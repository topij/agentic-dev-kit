"""Durable triage orchestration; all side effects pass through persisted state."""

from __future__ import annotations

import difflib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .approval import ApprovalContext, approval_record, parse_commands
from .canonical import (
    CanonicalError,
    decode_bytes,
    digest,
    digest_bytes,
    dumps,
    encode_bytes,
    loads_exact,
)
from .finalize import render_sweep, sweep_ids, validate_reviewed_head
from .gate import GateLease, acquire, validate_record
from .inbox import Candidate, parse, snapshot_content
from .model import (
    CAPABILITIES,
    OID_RE,
    SHA256_RE,
    Settings,
    TriageError,
    canonical_state,
    load_settings,
    new_run_identity,
    repository_identity,
    state_base,
    terminal_pr_watch_receipt,
    today_string,
    validate_state,
)
from .providers import ForgeProvider, NotificationProvider, ProviderObservation, TrackerProvider
from .recovery import (
    capture_state_present,
    gate_only_plan,
    persist_test_gate_held,
    prepare_gate_only,
    prepare_state_action,
    resume_gate_only,
    resume_state_action,
    state_action_plan,
    test_gate_state_plan,
)
from .storage import (
    ArtifactStore,
    Observation,
    atomic_replace,
    exclusive_create,
    observe,
    preflight_artifacts,
    quarantine_inode,
)


def _capabilities() -> dict[str, dict[str, str]]:
    return {name: {"status": "not-triggered", "mechanism": "not triggered"} for name in CAPABILITIES}


def _request_shape_error(request: dict[str, Any]) -> str | None:
    allowed = {
        "operator_identity", "source", "proposals", "approval",
        "recovery_approval", "finalize", "worktree",
    }
    unexpected = sorted(set(request) - allowed)
    if unexpected:
        return f"request contains unsupported policy fields: {', '.join(unexpected)}"
    proposals = request.get("proposals")
    if proposals is not None:
        if not isinstance(proposals, list) or any(not isinstance(item, dict) for item in proposals):
            return "request proposals must be an array of objects"
        for item in proposals:
            if "labels" in item and (not isinstance(item["labels"], list) or any(not isinstance(label, str) for label in item["labels"])):
                return "request proposal labels must be an array of strings"
    approval = request.get("approval")
    if approval is not None and not isinstance(approval, dict):
        return "request approval must be an object"
    recovery = request.get("recovery_approval")
    if recovery is not None and not isinstance(recovery, dict):
        return "request recovery_approval must be an object"
    if "finalize" in request and not isinstance(request["finalize"], bool):
        return "request finalize must be a boolean"
    if "worktree" in request and not isinstance(request["worktree"], str):
        return "request worktree must be a string"
    for name in ("operator_identity", "source"):
        if name in request and not isinstance(request[name], str):
            return f"request {name} must be a string"
    return None


def _result(
    capabilities: dict[str, dict[str, str]],
    outcome: str,
    *,
    mode: str,
    engine_mode: str | None,
    report: str | None,
    frozen: str | None,
    resume_action: str,
    detail: str,
    identifiers: list[str] | None = None,
    recovery_plan: dict[str, Any] | None = None,
    candidate_index: list[dict[str, Any]] | None = None,
    pull_request_url: str | None = None,
    observed_pr_head: str | None = None,
    reviewed_head: str | None = None,
    observed_protected_head: str | None = None,
) -> dict[str, Any]:
    return {
        "capabilities": capabilities,
        "outcome": outcome,
        "execution_mode": mode,
        "engine_mode": engine_mode,
        "report": report,
        "frozen_snapshot": frozen,
        "verified_tracker_identifiers": identifiers or [],
        "resume_action": resume_action,
        "detail": detail,
        "recovery_plan": recovery_plan,
        "candidate_index": candidate_index or [],
        "pull_request_url": pull_request_url,
        "observed_pr_head": observed_pr_head,
        "reviewed_head": reviewed_head,
        "observed_protected_head": observed_protected_head,
    }


def _pr_result_fields(state: dict[str, Any]) -> dict[str, str | None]:
    url = None
    observed = None
    reviewed = None
    for operation in state.get("finalization_operations", []):
        read_back = operation.get("read_back")
        intent = operation.get("intent")
        if not isinstance(read_back, dict) or not isinstance(intent, dict):
            continue
        if operation.get("kind") == "pull-request" and operation.get("status") == "verified":
            if read_back.get("baseRefName") == intent.get("base_branch") and read_back.get("headRefOid") == intent.get("head"):
                url = read_back.get("url") if isinstance(read_back.get("url"), str) else None
                observed = read_back.get("headRefOid") if isinstance(read_back.get("headRefOid"), str) else None
        elif (
            operation.get("kind") == "pr-watch"
            and read_back.get("url") == intent.get("pr")
            and read_back.get("baseRefName") == intent.get("base_branch")
            and read_back.get("headRefOid") == intent.get("head")
        ):
            url = read_back.get("url") if isinstance(read_back.get("url"), str) else url
            observed = read_back.get("headRefOid") if isinstance(read_back.get("headRefOid"), str) else observed
            if operation.get("status") == "verified" and read_back.get("reviewed_head") == observed and read_back.get("receipt"):
                reviewed = observed
    return {"pull_request_url": url, "observed_pr_head": observed, "reviewed_head": reviewed}


def _notification_read_back_exact(
    operation: dict[str, Any], read_back: Any, session: str
) -> bool:
    return (
        isinstance(read_back, dict)
        and isinstance(read_back.get("thread_reference"), str)
        and bool(read_back["thread_reference"])
        and read_back.get("marker") == session
        and read_back.get("target") == operation["target"]
        and read_back.get("rendered_payload") == operation["rendered_payload"]
        and read_back.get("rendered_payload_digest") == operation["rendered_payload_digest"]
        and read_back.get("match_count") == 1
    )


def _observe_protected_head(
    settings: Settings,
    state: dict[str, Any],
    authority: ForgeProvider | None,
) -> str:
    if authority is None:
        raise TriageError("protected branch refresh authority is unavailable")
    draft_head = state["run_identity"]["protected_branch_head"]
    observed = authority.authority("protected-head", {
        "repository_identity": state["run_identity"]["repository_identity"],
        "protected_branch": settings.protected_branch,
        "draft_head": draft_head,
    })
    if (
        not isinstance(observed, dict)
        or set(observed) != {"draft_head", "observed_head", "descends_from_draft"}
        or observed.get("draft_head") != draft_head
        or not isinstance(observed.get("observed_head"), str)
        or not OID_RE.fullmatch(observed["observed_head"])
        or observed.get("descends_from_draft") is not True
    ):
        raise TriageError("protected branch refresh is missing, divergent, or unverifiable")
    return observed["observed_head"]


def _recovery_approval(request: dict[str, Any], context: ApprovalContext | None, core_digest: str) -> dict[str, Any] | None:
    supplied = request.get("recovery_approval")
    if supplied is None:
        return None
    if context is None or context.source != "current-session" or not context.operator_identity:
        raise TriageError("recovery approval requires the trusted current-session operator", outcome="operator-held")
    expected = {
        "decision": "approve",
        "source": "current-session",
        "approver_identity": context.operator_identity,
        "core_digest": core_digest,
    }
    if supplied != expected:
        raise TriageError("recovery approval does not bind the prepared core", outcome="operator-held")
    read_back = context.source_read_back
    if not isinstance(read_back, dict) or read_back.get("decision") != "approve" or read_back.get("core_digest") != core_digest or read_back.get("approver_identity") != context.operator_identity:
        raise TriageError("recovery approval source read-back mismatch", outcome="operator-held")
    return expected


def _gate_only_state_value(store: ArtifactStore, state_raw: bytes | None) -> dict[str, Any] | None:
    if state_raw is None:
        return None
    try:
        value = loads_exact(state_raw)
    except Exception:
        return None
    if not isinstance(value, dict) or not isinstance(value.get("kind"), str) or value.get("kind") not in {
        "gate-only-recovery-intent", "test-gate-recovery-intent", "gate-only-operator-held"
    }:
        return None
    intent_keys = {
        "kind", "schema_version", "prepared_core_digest", "old_gate_digest",
        "configured_bundle_path", "repository_identity", "mode", "replacement_gate_run_identity",
    }
    receipt_keys = {
        "kind", "schema_version", "mode", "prepared_core_digest", "old_gate_digest",
        "configured_bundle_path", "repository_identity", "quarantine_observations",
        "replacement_quarantine_observations", "recovery_gate_owner_token", "recovery_gate_record",
    }
    expected_keys = receipt_keys if value.get("kind") == "gate-only-operator-held" else intent_keys
    if set(value) != expected_keys or value.get("schema_version") != 1:
        raise TriageError("gate-only state evidence has the wrong shape", outcome="operator-held")
    if value.get("mode") != store.mode or value.get("repository_identity") != repository_identity(store.settings):
        raise TriageError("gate-only state evidence is foreign", outcome="operator-held")
    old_gate_digest = value.get("old_gate_digest")
    if not isinstance(old_gate_digest, str) or value.get("configured_bundle_path") != str(store.recovery_path(old_gate_digest)):
        raise TriageError("gate-only state bundle binding is invalid", outcome="operator-held")
    return value


def _prepared_gate_only_bundle(store: ArtifactStore, state_value: dict[str, Any]) -> dict[str, Any]:
    bundle_path = Path(state_value["configured_bundle_path"])
    _, bundle_raw = observe(bundle_path)
    if bundle_raw is None:
        raise TriageError("recorded gate-only prepared bundle is missing", outcome="operator-held")
    try:
        bundle = loads_exact(bundle_raw)
    except Exception as exc:
        raise TriageError("recorded gate-only prepared bundle is malformed", outcome="operator-held") from exc
    envelope_keys = {
        "kind", "schema_version", "prepared_core", "prepared_core_digest", "approval",
        "intended_intent", "intended_intent_digest",
    }
    expected_kind = "test-gate-only-prepared" if store.mode == "test" else "gate-only-prepared"
    if not isinstance(bundle, dict) or set(bundle) != envelope_keys or bundle.get("kind") != expected_kind or bundle.get("schema_version") != 1:
        raise TriageError("recorded gate-only prepared bundle has the wrong shape", outcome="operator-held")
    if digest(bundle.get("prepared_core")) != bundle.get("prepared_core_digest") or digest(bundle.get("intended_intent")) != bundle.get("intended_intent_digest"):
        raise TriageError("recorded gate-only prepared bundle digest mismatch", outcome="operator-held")
    if bundle.get("prepared_core_digest") != state_value.get("prepared_core_digest"):
        raise TriageError("gate-only state does not bind its prepared core", outcome="operator-held")
    if state_value["kind"] != "gate-only-operator-held" and bundle.get("intended_intent") != state_value:
        raise TriageError("gate-only intent does not match its prepared bundle", outcome="operator-held")
    if state_value["kind"] == "gate-only-operator-held":
        intended = bundle["intended_intent"]
        record = state_value["recovery_gate_record"]
        validate_record(
            record,
            repository_identity=repository_identity(store.settings),
            config_fingerprint=store.settings.fingerprint,
        )
        if (
            record.get("owner_token") != state_value["recovery_gate_owner_token"]
            or record.get("owner_run_identity") != intended.get("replacement_gate_run_identity")
            or state_value["old_gate_digest"] != intended.get("old_gate_digest")
        ):
            raise TriageError("gate-only held receipt owner binding mismatch", outcome="operator-held")
        for item in [*state_value["quarantine_observations"], *state_value["replacement_quarantine_observations"]]:
            if not isinstance(item, dict):
                raise TriageError("gate-only held receipt observation is malformed", outcome="operator-held")
            approved = Observation(**item)
            observed, raw = observe(Path(approved.path), allow_links=True)
            if raw is None or observed != approved:
                raise TriageError("gate-only held receipt quarantine changed", outcome="operator-held")
        _, gate_raw = observe(store.gate_path, allow_links=True)
        if gate_raw is not None and gate_raw != dumps(record):
            raise TriageError("gate-only held receipt replacement gate changed", outcome="operator-held")
    return bundle


def _blocking_recovery(
    settings: Settings,
    store: ArtifactStore,
    request: dict[str, Any],
    context: ApprovalContext | None,
) -> tuple[str, str, dict[str, Any] | None]:
    gate_observation, gate_raw = observe(store.gate_path, allow_links=True)
    if gate_raw is None:
        raise TriageError("blocking gate disappeared", outcome="operator-held")
    _, state_raw = observe(store.state_path)
    gate_only_state = _gate_only_state_value(store, state_raw)
    if gate_only_state is not None:
        if gate_only_state["kind"] == "gate-only-operator-held":
            _prepared_gate_only_bundle(store, gate_only_state)
            return "operator-held", "gate-only-operator-held", None
        bundle = _prepared_gate_only_bundle(store, gate_only_state)
        receipt = resume_gate_only(store, settings, bundle)
        return "operator-held", receipt["kind"], None
    bundle_path = store.recovery_path(digest_bytes(gate_raw))
    _, bundle_raw = observe(bundle_path)
    if bundle_raw is not None:
        try:
            bundle = loads_exact(bundle_raw)
        except Exception as exc:
            raise TriageError("current-gate recovery bundle is malformed", outcome="operator-held") from exc
        kind = bundle.get("kind") if isinstance(bundle, dict) else None
        if kind in {"gate-only-prepared", "test-gate-only-prepared"}:
            receipt = resume_gate_only(store, settings, bundle)
            return "operator-held", receipt["kind"], None
        if kind == "state-present-capture":
            plan = state_action_plan(store, settings, bundle)
            if plan.get("held") is not None:
                held = prepare_state_action(store, settings, bundle, approval={}, operator="")
                return "operator-held", held["terminal_classification"], plan
            approval = _recovery_approval(request, context, plan["action_core_digest"])
            if approval is None:
                return "operator-held", "state-present recovery action awaits exact approval", plan
            prepared = prepare_state_action(store, settings, bundle, approval=approval, operator=context.operator_identity)
            result = resume_state_action(store, prepared)
            return "operator-held", str(result.get("result", result.get("kind"))), None
        if kind == "state-present-prepared":
            result = resume_state_action(store, bundle)
            return "operator-held", str(result.get("result", result.get("kind"))), None
        return "operator-held", f"recovery evidence retained: {kind}", None
    if state_raw is None:
        plan = gate_only_plan(store, settings)
        approval = _recovery_approval(request, context, plan["prepared_core_digest"])
        if approval is None:
            return "operator-held", "gate-only recovery capture awaits exact approval", plan
        envelope = prepare_gate_only(store, settings, approval=approval, operator=context.operator_identity)
        receipt = resume_gate_only(store, settings, envelope)
        return "operator-held", receipt["kind"], None
    if store.mode == "test":
        plan = test_gate_state_plan(store, settings)
        approval = _recovery_approval(request, context, plan["capture_core_digest"])
        if approval is None:
            return "operator-held", "blocking test gate state capture awaits exact held-evidence approval", plan
        held = persist_test_gate_held(store, settings, plan, approval=approval, operator=context.operator_identity)
        return "operator-held", held["terminal_classification"], None
    bundle = capture_state_present(store, settings)
    plan = state_action_plan(store, settings, bundle)
    if plan.get("held") is not None:
        held = prepare_state_action(store, settings, bundle, approval={}, operator="")
        return "operator-held", held["terminal_classification"], plan
    approval = _recovery_approval(request, context, plan["action_core_digest"])
    if approval is None:
        return "operator-held", "state-present recovery action awaits exact approval", plan
    prepared = prepare_state_action(store, settings, bundle, approval=approval, operator=context.operator_identity)
    result = resume_state_action(store, prepared)
    return "operator-held", str(result.get("result", result.get("kind"))), None


def _restart_receipt(store: ArtifactStore, raw: bytes) -> tuple[dict[str, Any], bytes, bytes] | None:
    try:
        receipt = loads_exact(raw)
    except Exception:
        return None
    expected_kind = "test-recovered-safe-to-restart" if store.mode == "test" else "recovered-safe-to-restart"
    if not isinstance(receipt, dict) or receipt.get("kind") != expected_kind:
        return None
    required = {"kind", "schema_version", "mode", "old_gate_digest", "configured_bundle_path", "capture_core_digest", "quarantine_path", "prepared_envelope_digest", "quarantine_observation"}
    if set(receipt) != required or receipt.get("schema_version") != 1 or receipt.get("mode") != store.mode:
        raise TriageError("safe-restart receipt has the wrong shape", outcome="operator-held")
    if (
        any(
            not isinstance(receipt.get(name), str)
            or not SHA256_RE.fullmatch(receipt[name])
            for name in ("old_gate_digest", "capture_core_digest", "prepared_envelope_digest")
        )
        or not isinstance(receipt.get("configured_bundle_path"), str)
        or not isinstance(receipt.get("quarantine_path"), str)
        or not isinstance(receipt.get("quarantine_observation"), dict)
    ):
        raise TriageError("safe-restart receipt has malformed fields", outcome="operator-held")
    expected_path = store.recovery_path(receipt["old_gate_digest"])
    if receipt["configured_bundle_path"] != str(expected_path):
        raise TriageError("safe-restart bundle path mismatch", outcome="operator-held")
    _, envelope_raw = observe(expected_path)
    if envelope_raw is None or digest_bytes(envelope_raw) != receipt["prepared_envelope_digest"]:
        raise TriageError("safe-restart prepared envelope is missing or changed", outcome="operator-held")
    try:
        envelope = loads_exact(envelope_raw)
    except Exception as exc:
        raise TriageError("safe-restart prepared envelope is malformed", outcome="operator-held") from exc
    envelope_keys = {
        "kind",
        "schema_version",
        "capture_core",
        "capture_core_digest",
        "action_core",
        "action_core_digest",
        "approval",
    }
    if (
        not isinstance(envelope, dict)
        or set(envelope) != envelope_keys
        or envelope.get("kind") != "state-present-prepared"
        or envelope.get("schema_version") != 1
        or not isinstance(envelope.get("capture_core"), dict)
        or not isinstance(envelope.get("action_core"), dict)
        or envelope.get("capture_core_digest") != receipt["capture_core_digest"]
        or digest(envelope.get("capture_core")) != receipt["capture_core_digest"]
    ):
        raise TriageError("safe-restart prepared envelope binding mismatch", outcome="operator-held")
    receipt_core = envelope["action_core"].get("receipt_core")
    if (
        not isinstance(receipt_core, dict)
        or digest(envelope["action_core"]) != envelope.get("action_core_digest")
        or receipt_core.get("configured_bundle_path") != str(expected_path)
    ):
        raise TriageError("safe-restart action binding mismatch", outcome="operator-held")
    try:
        approved_quarantine = Observation(**receipt["quarantine_observation"])
    except (TypeError, ValueError) as exc:
        raise TriageError("safe-restart quarantine observation is malformed", outcome="operator-held") from exc
    if approved_quarantine.path != receipt["quarantine_path"]:
        raise TriageError("safe-restart quarantine path mismatch", outcome="operator-held")
    observed_quarantine, quarantined_raw = observe(
        Path(receipt["quarantine_path"]), allow_links=True
    )
    try:
        captured_raw = decode_bytes(envelope["capture_core"]["state_bytes"])
    except (KeyError, TypeError, ValueError, CanonicalError) as exc:
        raise TriageError("safe-restart captured state bytes are malformed", outcome="operator-held") from exc
    if observed_quarantine != approved_quarantine or quarantined_raw != captured_raw:
        raise TriageError("safe-restart quarantine evidence changed", outcome="operator-held")
    return receipt, raw, envelope_raw


def _initial_claim(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "reason": "initial-reservation",
        "previous_gate_binding": None,
        "current_gate_binding": binding,
        "captured_state_digest": None,
        "recovery_bundle_digest": None,
        "approval_digest": None,
    }


def _persist(
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    *,
    previous_digest: str,
) -> str:
    lease.verify()
    if state["gate_owner_token"] != lease.owner_token or state["gate_binding"] != lease.binding:
        raise TriageError("state is not bound to the held gate", outcome="operator-held")
    validate_state(state, settings=store.settings, mode=store.mode)
    return atomic_replace(store.state_path, dumps(state), expected_digest=previous_digest)


def _rebind(
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    raw: bytes,
) -> tuple[dict[str, Any], str]:
    previous_binding = state["gate_binding"]
    rebound = deepcopy(state)
    rebound["gate_owner_token"] = lease.owner_token
    rebound["gate_binding"] = lease.binding
    rebound["state_claim"] = {
        "reason": "normal-resume",
        "previous_gate_binding": previous_binding,
        "current_gate_binding": lease.binding,
        "captured_state_digest": digest_bytes(raw),
        "recovery_bundle_digest": None,
        "approval_digest": None,
    }
    new_digest = atomic_replace(store.state_path, dumps(rebound), expected_digest=digest_bytes(raw))
    return rebound, new_digest


def _marker(session: str, candidate_id: str, core_digest: str) -> str:
    return f"<!-- triage-payload:{session}:{candidate_id}:{core_digest} -->"


def _proposal_records(
    candidates: list[Candidate],
    supplied: Any,
    *,
    run_identity: dict[str, Any],
    frozen_digest: str,
    report_path: Path,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    if not isinstance(supplied, list):
        raise TriageError("runtime proposal analysis is required", outcome="operator-held")
    by_id = {item.get("candidate_id"): item for item in supplied if isinstance(item, dict)}
    if set(by_id) != {candidate.candidate_id for candidate in candidates} or len(by_id) != len(supplied):
        raise TriageError("proposal analysis must cover the frozen candidate index exactly", outcome="operator-held")
    intermediate: list[dict[str, Any]] = []
    for candidate in candidates:
        item = by_id[candidate.candidate_id]
        expected = {"candidate_id", "source_block_digest", "title", "body_without_marker", "project", "labels"}
        if set(item) != expected or item["source_block_digest"] != candidate.digest:
            raise TriageError("proposal source authority mismatch", outcome="operator-held")
        if not isinstance(item["title"], str) or not item["title"] or not isinstance(item["body_without_marker"], str):
            raise TriageError("proposal title/body is invalid", outcome="operator-held")
        if (
            not isinstance(item["project"], str)
            or not isinstance(item["labels"], list)
            or any(not isinstance(label, str) or not label for label in item["labels"])
            or len(item["labels"]) != len(set(item["labels"]))
        ):
            raise TriageError("proposal project/labels are invalid", outcome="operator-held")
        labels = sorted(item["labels"])
        core = {
            "title": item["title"],
            "body_without_marker": item["body_without_marker"],
            "project": item["project"],
            "labels": labels,
        }
        core_digest = digest(core)
        marker = _marker(run_identity["session"], candidate.candidate_id, core_digest)
        body = item["body_without_marker"].rstrip() + "\n\n" + marker
        payload = {"title": item["title"], "body": body, "project": item["project"], "labels": labels}
        intermediate.append({
            "candidate_id": candidate.candidate_id,
            "payload_core": core,
            "payload_core_digest": core_digest,
            "marker": marker,
            "payload": payload,
            "payload_digest": digest(payload),
            "source_block_digest": candidate.digest,
            "source_block": candidate.record(),
        })
    report_core = {
        "run_identity": run_identity,
        "frozen_inbox_digest": frozen_digest,
        "proposals": [
            {"candidate_id": record["candidate_id"], "source_block_digest": record["source_block_digest"], "payload_digest": record["payload_digest"]}
            for record in intermediate
        ],
    }
    binding = {"path": str(report_path), "report_core": report_core, "report_core_digest": digest(report_core)}
    records = [{**record, "report_binding": binding} for record in intermediate]
    return records, [record["payload_digest"] for record in records], binding


def _source_literal(raw: bytes) -> tuple[str, str, str]:
    """Return an honest readable rendering and a content-safe Markdown fence."""
    try:
        rendered = raw.decode("utf-8")
    except UnicodeDecodeError:
        rendered = ascii(raw)
        description = (
            "Python bytes literal; escapes are part of this unambiguous rendering and "
            "the exact authoritative bytes are retained in state"
        )
    else:
        if all(character.isprintable() or character in "\n\t" for character in rendered):
            description = (
                "printable UTF-8 text with LF/TAB whitespace; the exact authoritative "
                "bytes are retained in state"
            )
        else:
            rendered = ascii(raw)
            description = (
                "Python bytes literal; escapes are part of this unambiguous rendering and "
                "the exact authoritative bytes are retained in state"
            )
    runs = {
        marker: max((len(match.group()) for match in re.finditer(re.escape(marker) + "+", rendered)), default=0)
        for marker in ("`", "~")
    }
    marker = min(runs, key=runs.get)
    fence = marker * max(3, runs[marker] + 1)
    return rendered, fence, description


def _literal_block(label: str, raw: bytes, *, info: str = "") -> list[str]:
    """Return captioned literal-block lines; ``info`` applies only to verbatim text."""
    rendered, fence, description = _source_literal(raw)
    try:
        verbatim = rendered == raw.decode("utf-8")
    except UnicodeDecodeError:
        verbatim = False
    return [f"{label} ({description}):", "", fence + info if verbatim else fence, rendered, fence]


def _inline_literal(value: Any) -> str:
    """Return a one-line code span that no backtick run in the value can close.

    Only non-empty printable text without edge whitespace is shown verbatim. Anything
    else is shown as its escaped Python string literal, labelled outside the span so
    the escape cannot be mistaken for the value itself.
    """
    text = value if isinstance(value, str) else str(value)
    verbatim = bool(text) and text == text.strip() and text.isprintable()
    shown = text if verbatim else ascii(text)
    longest = max((len(match.group()) for match in re.finditer("`+", shown)), default=0)
    delimiter = "`" * (longest + 1)
    padding = " " if shown.startswith("`") or shown.endswith("`") else ""
    span = f"{delimiter}{padding}{shown}{padding}{delimiter}"
    return span if verbatim else span + " (escaped Python string literal)"


def _report_text(state: dict[str, Any], capabilities: dict[str, dict[str, str]], outcome: str) -> bytes:
    # Every value taken from state, configuration or a service enters the report
    # through _inline_literal or _literal_block and in no other way. The report's
    # Markdown structure is the engine's own; no inbox, proposal-analysis or
    # read-back text is ever rendered as report Markdown.
    lines = [
        "# Triage friction log report", "", f"Outcome: {_inline_literal(outcome)}",
        f"Mode: {_inline_literal(state['mode'])}",
        f"Engine mode: {_inline_literal(state['engine_mode'])}",
        f"Run identity: {_inline_literal(dumps(state['run_identity']).decode())}",
        f"Frozen inbox digest: {_inline_literal(state['frozen_inbox_digest'])}",
        "", "## Capabilities", "",
    ]
    for name in CAPABILITIES:
        entry = capabilities[name]
        lines.append(
            f"- {_inline_literal(name)}: {_inline_literal(entry['status'])}"
            f" — {_inline_literal(entry['mechanism'])}"
        )
    proposals = state.get("proposal_payloads", [])
    if proposals:
        lines.extend(["", "## Exact proposal payloads", ""])
        for proposal in proposals:
            payload = proposal["payload"]
            source_raw = decode_bytes(proposal["source_block"]["source_block"])
            lines.extend([
                f"### {_inline_literal(proposal['candidate_id'])}", "",
                f"Source-block digest: {_inline_literal(proposal['source_block_digest'])}", "",
                *_literal_block("Original source", source_raw), "",
                f"Payload digest: {_inline_literal(proposal['payload_digest'])}", "",
                f"Title: {_inline_literal(payload['title'])}", "",
                *_literal_block("Body", payload["body"].encode("utf-8")), "",
                f"Project: {_inline_literal(payload['project'])}", "",
                "Labels: " + ", ".join(_inline_literal(label) for label in payload["labels"]), "",
            ])
        lines.extend([
            "Historical annotations are evidence for review, not executable accounting instructions.",
            "Use `archive <ids>` for already handled entries without filing, and use `park <ids>` or leave an entry unmentioned to retain it.",
            "`approve all` files every displayed payload, including historically annotated entries; it does not archive already handled entries.",
        ])
    if state.get("operations"):
        lines.extend(["", "## Tracker operations", ""])
        for operation in state["operations"]:
            lines.append(
                f"- {_inline_literal(operation['candidate_id'])}: {_inline_literal(operation['status'])}"
                f" — {_inline_literal(operation.get('returned_identifier'))}"
            )
    if state.get("finalization_operations"):
        lines.extend(["", "## Finalization operations", ""])
        for operation in state["finalization_operations"]:
            lines.append(f"- {_inline_literal(operation['kind'])}: {_inline_literal(operation['status'])}")
        pr_fields = _pr_result_fields(state)
        lines.extend([
            "",
            f"Pull request: {_inline_literal(pr_fields['pull_request_url'])}",
            f"Observed PR head: {_inline_literal(pr_fields['observed_pr_head'])}",
            f"Reviewed head: {_inline_literal(pr_fields['reviewed_head'])}",
        ])
    completion = state.get("completion")
    if isinstance(completion, dict):
        proposed_diff = completion.get("receipt_core", {}).get("proposed_diff")
        if isinstance(proposed_diff, str):
            lines.extend([
                "", "## Proposed source diff", "",
                *_literal_block("Proposed source diff", proposed_diff.rstrip().encode("utf-8"), info="diff"),
                "",
            ])
    return ("\n".join(lines).rstrip() + "\n").encode()


def _write_report(path: Path, state: dict[str, Any], capabilities: dict[str, dict[str, str]], outcome: str) -> None:
    atomic_replace(path, _report_text(state, capabilities, outcome))


def _new_draft(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    capabilities: dict[str, dict[str, str]],
    request: dict[str, Any],
    *,
    context: str,
    notification: NotificationProvider | None,
    restart_receipt: tuple[dict[str, Any], bytes, bytes] | None = None,
) -> tuple[dict[str, Any], str, Path, Path, list[Candidate], str | None]:
    inbox_observation, inbox_raw = observe(settings.paths.friction_log)
    if inbox_raw is None:
        raise TriageError("configured friction log is missing")
    candidates = parse(inbox_raw)
    if context == "unattended" and candidates:
        target = settings.notify.get("user_key")
        if notification is None:
            raise TriageError("scheduled draft requires a notification provider before reservation")
        if not isinstance(target, str) or not target:
            raise TriageError("scheduled draft requires a configured notification target before reservation")
    identity = new_run_identity(settings, store.mode)
    day = today_string()
    frozen_path = store.frozen_path(session=identity["session"], day=day)
    report_path = store.report_path(session=identity["session"], day=day)
    preflight_artifacts(
        [store.state_path, store.gate_path, frozen_path, report_path],
        controls=[
            settings.paths.repo / "config/dev-model.yaml",
            settings.paths.repo / "config/dev-model.local.yaml",
            settings.paths.friction_log,
            settings.paths.archive,
            settings.draft_engine,
            settings.finalize_engine,
        ],
        repo=settings.paths.repo,
    )
    frozen_path = store.frozen_path(session=identity["session"], day=day, mkdir=True)
    content = snapshot_content(inbox_raw, candidates)
    frozen_snapshot = {
        "path": settings.paths.frozen_pattern.replace("{mode}", store.mode).replace("{date}", day).replace("{session}", identity["session"]),
        "content": content,
        "raw_encoding": "base64",
        "raw": encode_bytes(inbox_raw),
    }
    frozen_digest = digest_bytes(inbox_raw)
    frozen_artifact = {
        "kind": "triage-frozen-inbox",
        "schema_version": 1,
        "run_identity": identity,
        "frozen_inbox_digest": frozen_digest,
        "frozen_snapshot": frozen_snapshot,
    }
    exclusive_create(frozen_path, dumps(frozen_artifact))
    claim = _initial_claim(lease.binding)
    if restart_receipt is not None:
        receipt, receipt_raw, envelope_raw = restart_receipt
        envelope = loads_exact(envelope_raw)
        claim = {
            "reason": "test-receipt-restart" if store.mode == "test" else "live-receipt-restart",
            "previous_gate_binding": None,
            "current_gate_binding": lease.binding,
            "captured_state_digest": digest_bytes(receipt_raw),
            "recovery_bundle_digest": digest_bytes(envelope_raw),
            "approval_digest": digest(envelope["approval"]),
        }
    base = state_base(identity, lease.binding, claim, frozen_digest, frozen_snapshot, settings.engine_mode)
    if restart_receipt is None:
        state_digest = exclusive_create(store.state_path, dumps(base))
    else:
        state_digest = atomic_replace(store.state_path, dumps(base), expected_digest=digest_bytes(restart_receipt[1]))
    capabilities["frozen-inbox-state"] = {"status": "ready", "mechanism": "atomic exact-byte snapshot and canonical state"}
    if not candidates:
        completed = deepcopy(base)
        completed["phase"] = "completed"
        receipt_core = {"route": "no-op", "outcome": "successful-completion", "run_identity": identity, "frozen_inbox_digest": frozen_digest, "candidate_index": []}
        completed["completion"] = {"route": "no-op", "outcome": "successful-completion", "receipt_core": receipt_core, "completed_receipt_digest": digest(receipt_core)}
        state_digest = _persist(store, lease, completed, previous_digest=state_digest)
        _write_report(report_path, completed, capabilities, "successful-completion")
        return completed, state_digest, report_path, frozen_path, candidates, "successful-completion"
    if request.get("proposals") is None:
        _write_report(report_path, base, capabilities, "operator-held")
        return base, state_digest, report_path, frozen_path, candidates, None
    proposals, proposal_digests, _ = _proposal_records(candidates, request.get("proposals"), run_identity=identity, frozen_digest=frozen_digest, report_path=report_path)
    proposed = {**base, "phase": "propose", "proposal_payloads": proposals, "proposal_payload_digests": proposal_digests}
    state_digest = _persist(store, lease, proposed, previous_digest=state_digest)
    _write_report(report_path, proposed, capabilities, "operator-held")
    if context == "unattended":
        if notification is None:
            capabilities["notification-thread"] = {"status": "stop", "mechanism": "scheduled draft requires send and thread read-back"}
            return proposed, state_digest, report_path, frozen_path, candidates, "operator-held"
        # Persist the attempt before dispatch. The notification provider performs
        # its own destination read-back and returns that observation.
        target = settings.notify.get("user_key")
        if not isinstance(target, str) or not target:
            capabilities["notification-thread"] = {"status": "stop", "mechanism": "configured notification target is absent"}
            return proposed, state_digest, report_path, frozen_path, candidates, "operator-held"
        rendered = _report_text(proposed, capabilities, "operator-held").decode()
        initial_attempt = {"kind": "initial", "target": target, "proposal_set_digest": digest(proposal_digests), "rendered_payload": rendered, "rendered_payload_digest": digest(rendered), "idempotency_key": digest({"session": identity["session"], "kind": "initial"}), "status": "attempting", "response": None, "read_back": None}
        operation = {**initial_attempt, "attempts": [initial_attempt]}
        delivering = {**proposed, "phase": "notification-delivery", "notification_operations": [operation]}
        state_digest = _persist(store, lease, delivering, previous_digest=state_digest)
        observation = notification.send_and_read_back(target, rendered, identity["session"])
        if observation.status == "verified" and not _notification_read_back_exact(
            operation, observation.read_back, identity["session"]
        ):
            observation = ProviderObservation("ambiguous", observation.response, observation.read_back)
        attempt = {**{name: item for name, item in operation.items() if name != "attempts"}, "status": observation.status, "response": observation.response, "read_back": observation.read_back}
        operation = {**attempt, "attempts": [initial_attempt, attempt]}
        verified_notification = observation.status == "verified" and _notification_read_back_exact(
            operation, observation.read_back, identity["session"]
        )
        if not verified_notification:
            held = {**delivering, "notification_operations": [operation]}
            state_digest = _persist(store, lease, held, previous_digest=state_digest)
            capabilities["notification-thread"] = {"status": "operator-held", "mechanism": "notification was not authoritatively verified"}
            return held, state_digest, report_path, frozen_path, candidates, "operator-held"
        awaiting = {**proposed, "phase": "awaiting-approval", "approval": None, "notification_thread_reference": observation.read_back.get("thread_reference"), "notification_operations": [operation], "decisions": []}
        state_digest = _persist(store, lease, awaiting, previous_digest=state_digest)
        capabilities["notification-thread"] = {"status": "ready", "mechanism": "exact message independently read back"}
        return awaiting, state_digest, report_path, frozen_path, candidates, None
    capabilities["notification-thread"] = {"status": "degraded", "mechanism": "interactive current-session presentation"}
    awaiting = {**proposed, "phase": "awaiting-approval", "approval": None, "notification_thread_reference": None, "notification_operations": [], "decisions": []}
    state_digest = _persist(store, lease, awaiting, previous_digest=state_digest)
    _write_report(report_path, awaiting, capabilities, "operator-held")
    return awaiting, state_digest, report_path, frozen_path, candidates, None


def _resume_reserved(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    request: dict[str, Any],
    capabilities: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], str, Path]:
    frozen_raw = decode_bytes(state["frozen_snapshot"]["raw"])
    candidates = parse(frozen_raw)
    report_path = store.report_path(session=state["run_identity"]["session"], day=today_string())
    proposals, proposal_digests, _ = _proposal_records(
        candidates,
        request.get("proposals"),
        run_identity=state["run_identity"],
        frozen_digest=state["frozen_inbox_digest"],
        report_path=report_path,
    )
    proposed = {**state, "phase": "propose", "proposal_payloads": proposals, "proposal_payload_digests": proposal_digests}
    state_digest = _persist(store, lease, proposed, previous_digest=state_digest)
    capabilities["notification-thread"] = {"status": "degraded", "mechanism": "interactive current-session presentation"}
    awaiting = {**proposed, "phase": "awaiting-approval", "approval": None, "notification_thread_reference": None, "notification_operations": [], "decisions": []}
    state_digest = _persist(store, lease, awaiting, previous_digest=state_digest)
    _write_report(report_path, awaiting, capabilities, "operator-held")
    return awaiting, state_digest, report_path


def _approval_authority(
    state: dict[str, Any],
    request: dict[str, Any],
    approval_context: ApprovalContext | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    supplied = request.get("approval")
    if not isinstance(supplied, dict):
        return None
    if approval_context is None:
        raise TriageError("approval requires a trusted runtime context", outcome="operator-held")
    displayed = state["proposal_payload_digests"]
    displayed_set_digest = digest(displayed)
    source_read_back = approval_context.source_read_back
    if supplied.get("proposal_set_digest") != displayed_set_digest:
        raise TriageError("approval is not bound to the displayed proposal set", outcome="operator-held")
    if not isinstance(source_read_back, dict) or source_read_back.get("proposal_set_digest") != displayed_set_digest or source_read_back.get("payload_digests") != displayed:
        raise TriageError("approval source did not read back the displayed payload digests", outcome="operator-held")
    command = supplied.get("command")
    if not isinstance(command, str):
        raise TriageError("approval command must be exact", outcome="operator-held")
    digests = {proposal["candidate_id"]: proposal["payload_digest"] for proposal in state["proposal_payloads"]}
    decisions = parse_commands(command, digests)
    approval = approval_record(
        decisions,
        context=approval_context,
        proposal_set_digest=displayed_set_digest,
        command_text=command,
    )
    return decisions, approval


def _apply_approval(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    request: dict[str, Any],
    capabilities: dict[str, dict[str, str]],
    tracker: TrackerProvider | None,
    approval_context: ApprovalContext | None,
) -> tuple[dict[str, Any], str, str]:
    authority = _approval_authority(state, request, approval_context)
    if authority is None:
        return state, state_digest, "operator-held"
    decisions, approval = authority
    if any(decision["decision"] == "modify" for decision in decisions):
        modified = deepcopy(state["proposal_payloads"])
        modification = next(decision for decision in decisions if decision["decision"] == "modify")
        for proposal in modified:
            if proposal["candidate_id"] != modification["candidate_id"]:
                continue
            core = {**proposal["payload_core"], "body_without_marker": modification["replacement_body"]}
            core_digest = digest(core)
            marker = _marker(state["run_identity"]["session"], proposal["candidate_id"], core_digest)
            payload = {**proposal["payload"], "body": modification["replacement_body"].rstrip() + "\n\n" + marker}
            proposal.update({"payload_core": core, "payload_core_digest": core_digest, "marker": marker, "payload": payload, "payload_digest": digest(payload)})
        proposal_digests = [proposal["payload_digest"] for proposal in modified]
        old_binding = modified[0]["report_binding"]
        report_core = {
            "run_identity": state["run_identity"],
            "frozen_inbox_digest": state["frozen_inbox_digest"],
            "proposals": [
                {"candidate_id": proposal["candidate_id"], "source_block_digest": proposal["source_block_digest"], "payload_digest": proposal["payload_digest"]}
                for proposal in modified
            ],
        }
        binding = {"path": old_binding["path"], "report_core": report_core, "report_core_digest": digest(report_core)}
        modified = [{**proposal, "report_binding": binding} for proposal in modified]
        represented = {**state, "proposal_payloads": modified, "proposal_payload_digests": proposal_digests, "approval": None, "decisions": []}
        state_digest = _persist(store, lease, represented, previous_digest=state_digest)
        capabilities["tracker-write-readback"] = {"status": "not-triggered", "mechanism": "modified payload requires re-presentation and later approval"}
        return represented, state_digest, "operator-held"
    filed = [decision for decision in decisions if decision["decision"] == "file"]
    archived_decisions = [decision for decision in decisions if decision["decision"] == "archive"]
    if not filed and not archived_decisions:
        completed = {**state, "phase": "completed", "approval": approval, "decisions": decisions}
        completed.pop("notification_thread_reference", None)
        completed.pop("notification_operations", None)
        receipt_core = {"route": "decision-only", "outcome": "degraded-success" if capabilities["notification-thread"]["status"] == "degraded" else "successful-completion", "run_identity": state["run_identity"], "frozen_inbox_digest": state["frozen_inbox_digest"], "proposal_payloads": state["proposal_payloads"], "approval": approval, "decisions": decisions, "operations": [], "attempts": []}
        completed["completion"] = {"route": "decision-only", "outcome": receipt_core["outcome"], "receipt_core": receipt_core, "completed_receipt_digest": digest(receipt_core)}
        # Completed routes have retained route authority, so validation is
        # performed by the completed-shape validator rather than awaiting keys.
        state_digest = atomic_replace(store.state_path, dumps(completed), expected_digest=state_digest)
        return completed, state_digest, receipt_core["outcome"]
    writing = {**state, "phase": "tracker-write", "approval": approval, "decisions": decisions, "operations": []}
    state_digest = _persist(store, lease, writing, previous_digest=state_digest)
    if store.mode == "test":
        operations = [{"candidate_id": decision["candidate_id"], "decision": "file", "proposal_digest": decision["proposal_digest"], "status": "would-create", "response": None, "returned_identifier": None, "read_back": None} for decision in filed]
        rendered = {**writing, "operations": operations}
        state_digest = _persist(store, lease, rendered, previous_digest=state_digest)
        receipt_core = {"route": "test-render", "outcome": "degraded-success" if capabilities["notification-thread"]["status"] == "degraded" else "successful-completion", "run_identity": state["run_identity"], "frozen_inbox_digest": state["frozen_inbox_digest"], "proposal_payloads": state["proposal_payloads"], "approval": approval, "decisions": decisions, "operations": operations, "attempts": [], "proposed_diff": _test_render_diff(settings, rendered)}
        completed = {**rendered, "phase": "completed", "completion": {"route": "test-render", "outcome": receipt_core["outcome"], "receipt_core": receipt_core, "completed_receipt_digest": digest(receipt_core)}}
        state_digest = atomic_replace(store.state_path, dumps(completed), expected_digest=state_digest)
        return completed, state_digest, receipt_core["outcome"]
    if tracker is None:
        capabilities["tracker-write-readback"] = _tracker_unavailable(decisions, "approved payload requires tracker provider")
        return writing, state_digest, "operator-held"
    return _advance_tracker_batch(settings, store, lease, writing, state_digest, capabilities, tracker)


def _tracker_unavailable(decisions: list[dict[str, Any]], held_mechanism: str) -> dict[str, str]:
    """Report a missing tracker as holding only when an approved decision files."""
    if not any(decision["decision"] == "file" for decision in decisions):
        return {"status": "not-triggered", "mechanism": "archive-only approval files no tracker payload; continue with finalize"}
    return {"status": "operator-held", "mechanism": held_mechanism}


def _advance_tracker_batch(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    writing: dict[str, Any],
    state_digest: str,
    capabilities: dict[str, dict[str, str]],
    tracker: TrackerProvider,
) -> tuple[dict[str, Any], str, str]:
    tracker_host = urlparse(str(settings.tracker.get("url", ""))).hostname
    destination = {"backend": settings.tracker.get("backend"), "host": tracker_host, "repository": settings.tracker.get("project_name"), "project": settings.tracker.get("project_name")}
    operations: list[dict[str, Any]] = deepcopy(writing.get("operations", []))
    proposals = {proposal["candidate_id"]: proposal for proposal in writing["proposal_payloads"]}
    filed = [decision for decision in writing["decisions"] if decision["decision"] == "file"]
    if operations and operations[-1].get("status") != "verified":
        pending = operations[-1]
        proposal = proposals[pending["candidate_id"]]
        matches = tracker.search(destination, proposal["marker"])
        exact = [match for match in matches if match.get("payload_digest") == proposal["payload_digest"]]
        reconciliation_route = (
            "failed-response-then-exact-read-back"
            if pending.get("status") == "failed"
            else "ambiguous-response-then-exact-read-back"
        )
        reconciliation = {
            **pending,
            "status": "verified" if len(matches) == 1 and len(exact) == 1 else "ambiguous",
            "response": pending.get("response"),
            "returned_identifier": exact[0]["identifier"] if len(matches) == 1 and len(exact) == 1 else None,
            "read_back": exact[0] if len(matches) == 1 and len(exact) == 1 else {"matches": matches},
            "verified_route": reconciliation_route if len(matches) == 1 and len(exact) == 1 else None,
            "search_read_back": matches,
        }
        operations[-1] = reconciliation
        attempts = [*writing.get("attempts", []), reconciliation]
        verified_ids = [item["returned_identifier"] for item in operations if item["status"] == "verified"]
        writing = {**writing, "operations": operations, "attempts": attempts, "verified_tracker_identifiers": verified_ids}
        state_digest = _persist(store, lease, writing, previous_digest=state_digest)
        if reconciliation["status"] != "verified":
            capabilities["tracker-write-readback"] = {"status": "operator-held", "mechanism": "retained tracker attempt is not authoritatively reconciled"}
            return writing, state_digest, "operator-held"
    for decision in filed[len(operations):]:
        proposal = proposals[decision["candidate_id"]]
        matches = tracker.search(destination, proposal["marker"])
        exact = [match for match in matches if match.get("payload_digest") == proposal["payload_digest"]]
        if len(matches) == 1 and len(exact) == 1:
            operation = {"candidate_id": decision["candidate_id"], "decision": "file", "proposal_digest": proposal["payload_digest"], "marker": proposal["marker"], "destination": destination, "status": "verified", "response": None, "returned_identifier": exact[0]["identifier"], "read_back": exact[0], "verified_route": "pre-existing-exact-match", "search_read_back": matches}
            operations.append(operation)
            writing = {**writing, "operations": operations, "verified_tracker_identifiers": [item["returned_identifier"] for item in operations]}
            state_digest = _persist(store, lease, writing, previous_digest=state_digest)
            continue
        if matches:
            operation = {"candidate_id": decision["candidate_id"], "decision": "file", "proposal_digest": proposal["payload_digest"], "marker": proposal["marker"], "destination": destination, "status": "ambiguous", "response": None, "returned_identifier": None, "read_back": {"matches": matches}, "verified_route": None, "search_read_back": matches}
            operations.append(operation)
            writing = {**writing, "operations": operations}
            state_digest = _persist(store, lease, writing, previous_digest=state_digest)
            capabilities["tracker-write-readback"] = {"status": "operator-held", "mechanism": "marker read-back is non-exact or multiple"}
            return writing, state_digest, "operator-held"
        attempting = {"candidate_id": decision["candidate_id"], "decision": "file", "proposal_digest": proposal["payload_digest"], "marker": proposal["marker"], "destination": destination, "status": "attempting", "response": None, "returned_identifier": None, "read_back": None, "verified_route": None, "search_read_back": []}
        operations.append(attempting)
        writing = {**writing, "operations": operations, "attempts": [*writing["attempts"], attempting]}
        state_digest = _persist(store, lease, writing, previous_digest=state_digest)
        observed = tracker.create(destination, proposal["payload"])
        read_back = observed.read_back
        identifier = read_back.get("identifier") if isinstance(read_back, dict) else None
        final = {**attempting, "status": observed.status, "response": observed.response, "returned_identifier": identifier, "read_back": read_back, "verified_route": observed.verified_route}
        operations[-1] = final
        attempts = [*writing["attempts"], final]
        verified_ids = [item["returned_identifier"] for item in operations if item["status"] == "verified"]
        writing = {**writing, "operations": operations, "attempts": attempts, "verified_tracker_identifiers": verified_ids}
        state_digest = _persist(store, lease, writing, previous_digest=state_digest)
        if observed.status != "verified":
            capabilities["tracker-write-readback"] = {"status": "operator-held", "mechanism": "tracker create is unresolved after authoritative read-back"}
            return writing, state_digest, "operator-held"
    capabilities["tracker-write-readback"] = {"status": "ready", "mechanism": "every approved payload authoritatively read back"}
    return writing, state_digest, "operator-held"


def _unattended_reminder(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    capabilities: dict[str, dict[str, str]],
    notification: NotificationProvider | None,
) -> tuple[dict[str, Any], str]:
    operations = state["notification_operations"]
    if any(operation.get("kind") == "reminder" for operation in operations):
        capabilities["notification-thread"] = {"status": "operator-held", "mechanism": "the single reminder attempt is already retained"}
        return state, state_digest
    target = settings.notify.get("user_key")
    if notification is None or not isinstance(target, str) or not target:
        capabilities["notification-thread"] = {"status": "operator-held", "mechanism": "unattended reminder provider or target is unavailable"}
        return state, state_digest
    rendered = _report_text(state, capabilities, "operator-held").decode()
    reminder_attempt = {
        "kind": "reminder",
        "target": target,
        "proposal_set_digest": digest(state["proposal_payload_digests"]),
        "rendered_payload": rendered,
        "rendered_payload_digest": digest(rendered),
        "idempotency_key": digest({"session": state["run_identity"]["session"], "kind": "reminder"}),
        "status": "attempting",
        "response": None,
        "read_back": None,
    }
    operation = {**reminder_attempt, "attempts": [reminder_attempt]}
    attempting = {**state, "notification_operations": [*operations, operation]}
    state_digest = _persist(store, lease, attempting, previous_digest=state_digest)
    observed = notification.send_and_read_back(target, rendered, state["run_identity"]["session"])
    if observed.status == "verified" and not _notification_read_back_exact(
        operation, observed.read_back, state["run_identity"]["session"]
    ):
        observed = ProviderObservation("ambiguous", observed.response, observed.read_back)
    attempt = {**{name: item for name, item in operation.items() if name != "attempts"}, "status": observed.status, "response": observed.response, "read_back": observed.read_back}
    retained = {**attempt, "attempts": [reminder_attempt, attempt]}
    updated = {**attempting, "notification_operations": [*operations, retained]}
    state_digest = _persist(store, lease, updated, previous_digest=state_digest)
    capabilities["notification-thread"] = {
        "status": "ready" if observed.status == "verified" else "operator-held",
        "mechanism": "reminder independently read back" if observed.status == "verified" else "reminder result is unresolved",
    }
    return updated, state_digest


def _resume_notification_delivery(
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    capabilities: dict[str, dict[str, str]],
    notification: NotificationProvider | None,
) -> tuple[dict[str, Any], str, str]:
    operations = state.get("notification_operations")
    if not isinstance(operations, list) or len(operations) != 1 or operations[0].get("kind") != "initial":
        raise TriageError("notification delivery evidence is malformed", outcome="operator-held")
    operation = operations[0]
    rendered = operation.get("rendered_payload")
    if not isinstance(rendered, str) or operation.get("rendered_payload_digest") != digest(rendered):
        raise TriageError("notification delivery payload binding mismatch", outcome="operator-held")
    reader = getattr(notification, "read_back", None) if notification is not None else None
    if not callable(reader):
        capabilities["notification-thread"] = {"status": "operator-held", "mechanism": "notification read-back provider is unavailable"}
        return state, state_digest, "operator-held"
    observed = reader(operation["target"], rendered, state["run_identity"]["session"])
    attempt = {**{name: item for name, item in operation.items() if name != "attempts"}, "status": observed.status, "response": observed.response, "read_back": observed.read_back}
    retained = {**attempt, "attempts": [*operation.get("attempts", []), attempt]}
    if observed.status != "verified" or not _notification_read_back_exact(
        operation, observed.read_back, state["run_identity"]["session"]
    ):
        held = {**state, "notification_operations": [retained]}
        state_digest = _persist(store, lease, held, previous_digest=state_digest)
        capabilities["notification-thread"] = {"status": "operator-held", "mechanism": "notification read-back remains unresolved"}
        return held, state_digest, "operator-held"
    awaiting = {
        **state,
        "phase": "awaiting-approval",
        "approval": None,
        "notification_thread_reference": observed.read_back["thread_reference"],
        "notification_operations": [retained],
        "decisions": [],
    }
    state_digest = _persist(store, lease, awaiting, previous_digest=state_digest)
    capabilities["notification-thread"] = {"status": "ready", "mechanism": "retained delivery independently read back"}
    return awaiting, state_digest, "operator-held"


def _frozen_candidates(state: dict[str, Any]) -> list[Candidate]:
    candidates = []
    for proposal in state["proposal_payloads"]:
        source = proposal["source_block"]
        raw = decode_bytes(source["source_block"])
        if digest_bytes(raw) != source["source_block_digest"]:
            raise TriageError("frozen proposal source bytes changed", outcome="operator-held")
        candidates.append(Candidate(source["candidate_id"], source["title"], raw, source["source_block_digest"], 0, 0))
    return candidates


def _validate_frozen_artifact(store: ArtifactStore, state: dict[str, Any]) -> Path:
    frozen_path = store.resolve(state["frozen_snapshot"]["path"])
    _, frozen_raw = observe(frozen_path)
    if frozen_raw is None:
        raise TriageError("published frozen snapshot artifact is missing")
    try:
        artifact = loads_exact(frozen_raw)
    except Exception as exc:
        raise TriageError("published frozen snapshot artifact is malformed") from exc
    if (
        not isinstance(artifact, dict)
        or set(artifact) != {
            "kind", "schema_version", "run_identity", "frozen_inbox_digest",
            "frozen_snapshot",
        }
        or artifact.get("kind") != "triage-frozen-inbox"
        or isinstance(artifact.get("schema_version"), bool)
        or artifact.get("schema_version") != 1
        or artifact.get("run_identity") != state["run_identity"]
        or artifact.get("frozen_inbox_digest") != state["frozen_inbox_digest"]
        or artifact.get("frozen_snapshot") != state["frozen_snapshot"]
    ):
        raise TriageError("published frozen snapshot artifact does not match active state")
    return frozen_path


def _test_render_diff(settings: Settings, state: dict[str, Any]) -> str:
    projection = deepcopy(state)
    projection["operations"] = [
        {**operation, "status": "verified"}
        for operation in projection["operations"]
    ]
    frozen_inbox = decode_bytes(state["frozen_snapshot"]["raw"])
    archive = settings.paths.archive.read_bytes()
    marker = f"## {today_string()} — Proposed triage archive sweep\n\n".encode()
    proposed_inbox, proposed_archive = render_sweep(
        frozen_inbox,
        archive,
        _frozen_candidates(state),
        projection,
        marker,
    )
    pieces = []
    for before, after, path in (
        (frozen_inbox, proposed_inbox, str(settings.paths.friction_log.relative_to(settings.paths.repo))),
        (archive, proposed_archive, str(settings.paths.archive.relative_to(settings.paths.repo))),
    ):
        pieces.extend(difflib.unified_diff(
            before.decode("utf-8").splitlines(),
            after.decode("utf-8").splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        ))
    return "\n".join(pieces) + "\n"


def _branch_date(settings: Settings, branch: Any) -> str:
    pattern_parts = settings.triage_branch_pattern.split("{date}")
    if (
        len(pattern_parts) != 2
        or not isinstance(branch, str)
        or not branch.startswith(pattern_parts[0])
        or not branch.endswith(pattern_parts[1])
    ):
        raise TriageError("commit update branch date is not bound", outcome="operator-held")
    end = len(branch) - len(pattern_parts[1]) if pattern_parts[1] else len(branch)
    branch_date = branch[len(pattern_parts[0]):end]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", branch_date):
        raise TriageError("commit update branch date is not bound", outcome="operator-held")
    return branch_date


def _validate_commit_updates(
    state: dict[str, Any], settings: Settings, intent: dict[str, Any]
) -> None:
    inbox_rel = str(settings.paths.friction_log.relative_to(settings.paths.repo))
    archive_rel = str(settings.paths.archive.relative_to(settings.paths.repo))
    expected_paths = sorted([inbox_rel, archive_rel])
    updates = intent.get("updates")
    if (
        intent.get("paths") != expected_paths
        or not isinstance(updates, list)
        or [update.get("path") for update in updates if isinstance(update, dict)] != expected_paths
        or any(
            not isinstance(update, dict)
            or set(update) != {
                "path", "previous_content", "previous_digest", "content", "content_digest",
            }
            for update in updates
        )
    ):
        raise TriageError("commit update path set is invalid", outcome="operator-held")
    decoded: dict[str, tuple[bytes, bytes]] = {}
    try:
        for update in updates:
            previous = decode_bytes(update["previous_content"])
            content = decode_bytes(update["content"])
            if (
                digest_bytes(previous) != update["previous_digest"]
                or digest_bytes(content) != update["content_digest"]
            ):
                raise TriageError("commit update digest mismatch", outcome="operator-held")
            decoded[update["path"]] = (previous, content)
    except (KeyError, TypeError, ValueError, CanonicalError) as exc:
        raise TriageError("commit update content is malformed", outcome="operator-held") from exc
    branch_date = _branch_date(settings, intent.get("branch"))
    marker_text = intent.get("migration_marker")
    expected_marker = (
        f"## {branch_date} — Backlog migrated by triage session "
        f"{state['run_identity']['session']}\n\n"
    )
    if marker_text != expected_marker:
        raise TriageError("commit migration marker is not bound to its branch", outcome="operator-held")
    marker = expected_marker.encode()
    expected_inbox, expected_archive = render_sweep(
        decoded[inbox_rel][0],
        decoded[archive_rel][0],
        _frozen_candidates(state),
        state,
        marker,
    )
    if decoded[inbox_rel][1] != expected_inbox or decoded[archive_rel][1] != expected_archive:
        raise TriageError("commit updates do not match the approved sweep", outcome="operator-held")
    authority = intent.get("authority_read_back")
    if (
        not isinstance(authority, dict)
        or authority.get("paths") != expected_paths
        or not isinstance(authority.get("staged_tree"), str)
    ):
        raise TriageError("commit updates lack staged-tree authority", outcome="operator-held")


def _forge_attempt(
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    forge: ForgeProvider,
    kind: str,
    intent: dict[str, Any],
) -> tuple[dict[str, Any], str, ProviderObservation]:
    operations = deepcopy(state.get("finalization_operations", []))
    retry = bool(operations and operations[-1].get("kind") == kind and operations[-1].get("status") == "unsettled")
    attempt = {"kind": kind, "intent": intent, "intent_digest": digest(intent), "status": "attempting", "response": None, "read_back": None}
    if retry:
        prior_attempts = operations[-1].get("attempts", [])
        operation = {**attempt, "attempts": [*prior_attempts, attempt]}
        operations[-1] = operation
    else:
        operation = {**attempt, "attempts": [attempt]}
        operations.append(operation)
    attempting = {**state, "phase": "forge-finalize", "finalization_operations": operations}
    state_digest = _persist(store, lease, attempting, previous_digest=state_digest)
    if kind == "commit":
        _validate_commit_updates(state, store.settings, intent)
        worktree = Path(intent["worktree"]).resolve()
        for update in intent.get("updates", []):
            relative = Path(update["path"])
            target = (worktree / relative).resolve()
            if relative.is_absolute() or not target.is_relative_to(worktree):
                raise TriageError("commit update path escapes the isolated worktree", outcome="operator-held")
            content = decode_bytes(update["content"])
            if digest_bytes(content) != update.get("content_digest"):
                raise TriageError("commit update content digest mismatch", outcome="operator-held")
            atomic_replace(target, content, expected_digest=update.get("previous_digest"))
    observed = forge.perform(kind, intent)
    if observed.status == "verified":
        if not isinstance(observed.read_back, dict):
            observed = ProviderObservation("ambiguous", observed.response, observed.read_back)
        else:
            try:
                _verify_forge_read_back(kind, intent, observed.read_back)
            except TriageError:
                observed = ProviderObservation("ambiguous", observed.response, observed.read_back)
    final_attempt = {**attempt, "status": observed.status, "response": observed.response, "read_back": observed.read_back}
    operations[-1] = {**final_attempt, "attempts": [*operation["attempts"], final_attempt]}
    repository_evidence = [*attempting["repository_evidence"]]
    pull_request_evidence = [*attempting["pull_request_evidence"]]
    if observed.status == "verified":
        if kind in {"branch-create", "commit", "push"}:
            repository_evidence.append(operations[-1])
        else:
            pull_request_evidence.append(operations[-1])
    updated = {**attempting, "finalization_operations": operations, "repository_evidence": repository_evidence, "pull_request_evidence": pull_request_evidence}
    state_digest = _persist(store, lease, updated, previous_digest=state_digest)
    return updated, state_digest, observed


def _archive_summary(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    operations = state["finalization_operations"]
    if len(operations) < 5 or [item.get("kind") for item in operations[:5]] != ["branch-create", "commit", "push", "pull-request", "pr-watch"]:
        raise TriageError("finalization evidence is not a complete reviewed prefix", outcome="operator-held")
    if any(item.get("status") != "verified" for item in operations[:5]):
        raise TriageError("finalization evidence is not verified", outcome="operator-held")
    branch, _commit, push, _pull_request, review = [item["read_back"] for item in operations[:5]]
    return {
        "repository": branch["repository"],
        "base": settings.protected_branch,
        "branch": branch["branch"],
        "commit": push["remote_head"],
        "pr": review["url"],
        "observed_head": review["headRefOid"],
        "reviewed_head": review["reviewed_head"],
        "pr_watch_receipt": review["receipt"],
    }


def _verify_forge_read_back(kind: str, intent: dict[str, Any], read_back: dict[str, Any]) -> None:
    if kind == "branch-create":
        required = (read_back.get("repository") == intent["repository"] and read_back.get("branch") == intent["branch"] and read_back.get("worktree") == intent["worktree"] and read_back.get("head") == read_back.get("base") == intent["finalize_base_head"])
    elif kind == "commit":
        required = (read_back.get("repository") == intent["repository"] and read_back.get("branch") == intent["branch"] and read_back.get("base") == intent["base"] and read_back.get("worktree") == intent["worktree"] and read_back.get("subject") == intent["subject"] and read_back.get("paths") == intent["paths"] and read_back.get("tree") == intent["authority_read_back"]["staged_tree"])
    elif kind == "push":
        required = (read_back.get("repository") == intent["repository"] and read_back.get("branch") == intent["branch"] and read_back.get("remote_head") == intent["commit"] and read_back.get("tree") == intent["tree"])
    elif kind == "pull-request":
        required = (read_back.get("baseRefName") == intent["base_branch"] and read_back.get("headRefName") == intent["branch"] and read_back.get("headRefOid") == intent["head"] and read_back.get("isDraft") is False and read_back.get("files") == intent["paths"])
    elif kind == "pr-watch":
        required = (
            read_back.get("url") == intent["pr"]
            and read_back.get("baseRefName") == intent["base_branch"]
            and read_back.get("headRefOid") == intent["head"]
            and read_back.get("reviewed_head") == intent["head"]
            and terminal_pr_watch_receipt(
                read_back.get("receipt"), head=intent["head"], url=intent["pr"]
            )
        )
    elif kind == "merge-read-back":
        required = (read_back.get("url") == intent["pr"] and read_back.get("baseRefName") == intent["base"] and read_back.get("headRefOid") == intent["reviewed_head"] and read_back.get("merged") is True)
    else:
        required = False
    if not required:
        raise TriageError(f"{kind} authoritative read-back does not match its intent", outcome="operator-held")


def _validate_forge_prefix(
    operations: list[dict[str, Any]], state: dict[str, Any], settings: Settings
) -> None:
    for operation in operations:
        if operation.get("kind") == "commit" and isinstance(operation.get("intent"), dict):
            _validate_commit_updates(state, settings, operation["intent"])
        if operation.get("status") == "verified":
            read_back = operation.get("read_back")
            if not isinstance(read_back, dict):
                raise TriageError("verified forge operation lacks read-back", outcome="operator-held")
            _verify_forge_read_back(operation["kind"], operation["intent"], read_back)
    for previous, current in zip(operations, operations[1:], strict=False):
        if previous.get("status") != "verified":
            break
        read_back = previous["read_back"]
        intent = current["intent"]
        if current["kind"] == "commit":
            bound = all(intent.get(name) == read_back.get(name) for name in ("repository", "branch", "worktree")) and intent.get("base") == read_back.get("head")
        elif current["kind"] == "push":
            bound = all(intent.get(name) == read_back.get(name) for name in ("repository", "branch", "worktree", "tree")) and intent.get("commit") == read_back.get("commit")
        elif current["kind"] == "pull-request":
            bound = intent.get("repository") == read_back.get("repository") and intent.get("branch") == read_back.get("branch") and intent.get("head") == read_back.get("remote_head")
        elif current["kind"] == "pr-watch":
            bound = intent.get("head") == read_back.get("headRefOid") and intent.get("pr") == read_back.get("url")
        elif current["kind"] == "merge-read-back":
            bound = intent.get("reviewed_head") == read_back.get("reviewed_head") and intent.get("pr") == read_back.get("url")
        else:
            bound = False
        if not bound:
            raise TriageError("forge predecessor binding mismatch", outcome="operator-held")


def _forge_destination(remote: str) -> tuple[str, str]:
    if remote.startswith("git@") and ":" in remote:
        host, repository = remote[4:].split(":", 1)
    else:
        parsed = urlparse(remote)
        host = parsed.hostname or ""
        repository = parsed.path.lstrip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]
    parts = repository.split("/")
    if not host or len(parts) != 2 or any(not part or not all(character.isalnum() or character in "._-" for character in part) for part in parts):
        raise TriageError("origin does not identify a supported forge repository", outcome="hard-stop")
    return host.lower(), repository


def _advance_finalize(
    settings: Settings,
    store: ArtifactStore,
    lease: GateLease,
    state: dict[str, Any],
    state_digest: str,
    request: dict[str, Any],
    capabilities: dict[str, dict[str, str]],
    forge: ForgeProvider | None,
) -> tuple[dict[str, Any], str, str]:
    if store.mode == "test":
        return state, state_digest, "operator-held"
    if forge is None or request.get("finalize") is not True:
        capabilities["forge-pr-write-readback"] = {"status": "operator-held", "mechanism": "exact finalization continuation/provider is required"}
        return state, state_digest, "operator-held"
    if state["phase"] == "tracker-write":
        sweep_ids(state)
        state = {**state, "phase": "forge-finalize", "finalization_operations": []}
        state_digest = _persist(store, lease, state, previous_digest=state_digest)
    if state["phase"] == "archive-sweep":
        resumed = {**state, "phase": "forge-finalize"}
        resumed.pop("archive_sweep")
        state_digest = _persist(store, lease, resumed, previous_digest=state_digest)
        state = resumed
    if state["phase"] != "forge-finalize":
        return state, state_digest, "operator-held"
    operations = state["finalization_operations"]
    _validate_forge_prefix(operations, state, settings)
    order = ["branch-create", "commit", "push", "pull-request", "pr-watch", "merge-read-back"]
    if operations and operations[-1].get("status") != "verified":
        if operations[-1].get("status") != "unsettled" or operations[-1].get("kind") not in {"pr-watch", "merge-read-back"}:
            return state, state_digest, "operator-held"
        next_kind = operations[-1]["kind"]
    else:
        next_kind = order[len(operations)] if len(operations) < len(order) else None
    if next_kind is None:
        return state, state_digest, "operator-held"
    retry_intent = (
        deepcopy(operations[-1]["intent"])
        if operations and operations[-1].get("status") == "unsettled"
        else None
    )
    previous = operations[-1]["read_back"] if operations else None
    forge_host, repository = _forge_destination(state["run_identity"]["repository_identity"]["remote"])
    branch = settings.triage_branch_pattern.replace("{date}", today_string())
    worktree = request.get("worktree")
    if retry_intent is not None:
        intent = retry_intent
    elif next_kind == "branch-create":
        if not isinstance(worktree, str) or not Path(worktree).is_absolute():
            raise TriageError("finalization worktree must be an explicit absolute path", outcome="operator-held")
        worktree_path = Path(worktree).resolve()
        if worktree_path == settings.paths.repo or settings.paths.repo.is_relative_to(worktree_path) or worktree_path.is_relative_to(settings.paths.repo):
            raise TriageError("finalization worktree conflicts with caller checkout", outcome="operator-held")
        request_core = {"host": forge_host, "repository": repository, "protected_branch": settings.protected_branch, "draft_head": state["run_identity"]["protected_branch_head"], "branch": branch, "worktree": worktree}
        authority = forge.authority("branch-create", request_core)
        if not isinstance(authority, dict) or authority.get("descends_from_draft") is not True or not isinstance(authority.get("finalize_base_head"), str):
            raise TriageError("protected branch ancestry is not authoritative", outcome="hard-stop")
        intent = {**request_core, "finalize_base_head": authority["finalize_base_head"], "authority_read_back": authority}
    elif next_kind == "commit":
        if not isinstance(previous, dict):
            raise TriageError("branch read-back is missing", outcome="operator-held")
        worktree_path = Path(previous["worktree"]).resolve()
        if worktree_path == settings.paths.repo or settings.paths.repo.is_relative_to(worktree_path) or worktree_path.is_relative_to(settings.paths.repo):
            raise TriageError("finalization worktree conflicts with caller checkout", outcome="operator-held")
        inbox_rel = str(settings.paths.friction_log.relative_to(settings.paths.repo))
        archive_rel = str(settings.paths.archive.relative_to(settings.paths.repo))
        clean = forge.authority("worktree-clean", {"repository": repository, "worktree": str(worktree_path)})
        if clean != {"clean": True}:
            raise TriageError("finalization worktree is not clean", outcome="operator-held")
        current = (worktree_path / inbox_rel).read_bytes()
        archive_bytes = (worktree_path / archive_rel).read_bytes()
        branch_date = _branch_date(settings, previous["branch"])
        marker = (
            f"## {branch_date} — Backlog migrated by triage session "
            f"{state['run_identity']['session']}\n\n"
        ).encode()
        new_inbox, new_archive = render_sweep(current, archive_bytes, _frozen_candidates(state), state, marker)
        paths = sorted([inbox_rel, archive_rel])
        updates = [
            {
                "path": inbox_rel,
                "previous_content": encode_bytes(current),
                "previous_digest": digest_bytes(current),
                "content": encode_bytes(new_inbox),
                "content_digest": digest_bytes(new_inbox),
            },
            {
                "path": archive_rel,
                "previous_content": encode_bytes(archive_bytes),
                "previous_digest": digest_bytes(archive_bytes),
                "content": encode_bytes(new_archive),
                "content_digest": digest_bytes(new_archive),
            },
        ]
        updates.sort(key=lambda item: item["path"])
        request_core = {"host": forge_host, "repository": repository, "base": previous["base"], "branch": previous["branch"], "worktree": previous["worktree"], "subject": settings.commit_subject, "paths": paths, "migration_marker": marker.decode(), "updates": updates}
        authority = forge.authority("commit", request_core)
        if not isinstance(authority, dict) or authority.get("paths") != paths or not isinstance(authority.get("staged_tree"), str):
            raise TriageError("commit staged-tree authority is incomplete", outcome="operator-held")
        intent = {**request_core, "authority_read_back": authority}
        _validate_commit_updates(state, settings, intent)
    elif next_kind == "push":
        intent = {"host": forge_host, "repository": repository, "base": previous["base"], "branch": previous["branch"], "worktree": previous["worktree"], "commit": previous["commit"], "tree": previous["tree"]}
    elif next_kind == "pull-request":
        paths = sorted([str(settings.paths.friction_log.relative_to(settings.paths.repo)), str(settings.paths.archive.relative_to(settings.paths.repo))])
        intent = {"host": forge_host, "repository": repository, "base_branch": settings.protected_branch, "branch": previous["branch"], "worktree": previous["worktree"], "head": previous["remote_head"], "tree": previous["tree"], "paths": paths, "draft": False, "title": settings.commit_subject, "body": "Archive only the exact approved and accounted friction blocks."}
    elif next_kind == "pr-watch":
        pr_identity = previous.get("url")
        intent = {"host": forge_host, "repository": repository, "pr": pr_identity, "base_branch": settings.protected_branch, "head": previous["headRefOid"], "tree": operations[-2]["read_back"]["tree"] if len(operations) >= 2 else None}
    else:
        archive = _archive_summary(state, settings)
        intent = {"host": forge_host, "repository": archive["repository"], "pr": archive["pr"], "base": archive["base"], "reviewed_head": archive["reviewed_head"], "receipt": archive["pr_watch_receipt"]}
    state, state_digest, observed = _forge_attempt(store, lease, state, state_digest, forge, next_kind, intent)
    if observed.status != "verified" or not isinstance(observed.read_back, dict):
        capabilities["forge-pr-write-readback"] = {"status": "operator-held", "mechanism": f"{next_kind} lacks authoritative verification"}
        return state, state_digest, "operator-held"
    _verify_forge_read_back(next_kind, intent, observed.read_back)
    if next_kind == "merge-read-back":
        archive = _archive_summary(state, settings)
        validate_reviewed_head({"archive_sweep": archive}, observed.read_back)
        outcome = (
            "degraded-success"
            if state.get("notification_thread_reference") is None
            and state.get("notification_operations") == []
            else "successful-completion"
        )
        receipt_core = {"route": "archive-sweep", "outcome": outcome, "run_identity": state["run_identity"], "frozen_inbox_digest": state["frozen_inbox_digest"], "tracker_operations": state["operations"], "finalization_operations": state["finalization_operations"], "archive_sweep": archive, "merge_read_back": observed.read_back}
        completed = {**state, "phase": "completed", "archive_sweep": archive, "completion": {"route": "archive-sweep", "outcome": outcome, "receipt_core": receipt_core, "completed_receipt_digest": digest(receipt_core)}}
        state_digest = atomic_replace(store.state_path, dumps(completed), expected_digest=state_digest)
        return completed, state_digest, outcome
    if next_kind == "pr-watch":
        read_back = observed.read_back
        if read_back.get("headRefOid") != read_back.get("reviewed_head") or not read_back.get("receipt"):
            raise TriageError("terminal review evidence does not bind the current head", outcome="operator-held")
        archive = _archive_summary(state, settings)
        swept = {**state, "phase": "archive-sweep", "archive_sweep": archive}
        state_digest = _persist(store, lease, swept, previous_digest=state_digest)
        capabilities["forge-pr-write-readback"] = {"status": "ready", "mechanism": "ready pull request and exact-head review read back"}
        capabilities["pr-watch"] = {"status": "ready", "mechanism": "terminal receipt persisted before merge"}
        return swept, state_digest, "operator-held"
    return _advance_finalize(settings, store, lease, state, state_digest, request, capabilities, forge)


def run(
    entry: str | None,
    *,
    context: str,
    request: dict[str, Any] | None = None,
    start: Path | None = None,
    tracker: TrackerProvider | None = None,
    notification: NotificationProvider | None = None,
    approval_context: ApprovalContext | None = None,
    forge: ForgeProvider | None = None,
    head_authority: ForgeProvider | None = None,
) -> dict[str, Any]:
    capabilities = _capabilities()
    if request is None:
        request = {}
    if not isinstance(request, dict):
        return _result(capabilities, "hard-stop", mode="unknown", engine_mode=None, report=None, frozen=None, resume_action="supply a canonical request object", detail="request root must be an object")
    shape_error = _request_shape_error(request)
    if shape_error is not None:
        return _result(capabilities, "hard-stop", mode="unknown", engine_mode=None, report=None, frozen=None, resume_action="supply a well-typed canonical request", detail=shape_error)
    if entry is not None and (not isinstance(entry, str) or entry not in {"resume", "new", "recover", "test"}):
        return _result(capabilities, "hard-stop", mode="unknown", engine_mode=None, report=None, frozen=None, resume_action="invoke with no argument, resume, new, recover, or test", detail="unknown or combined entry keyword")
    if not isinstance(context, str) or context not in {"interactive", "unattended"}:
        return _result(capabilities, "hard-stop", mode="unknown", engine_mode=None, report=None, frozen=None, resume_action="supply an explicit execution context", detail="invalid execution context")
    mode = "test" if entry == "test" else "live"
    observed_protected_head = None
    result_engine_mode: str | None = None
    result_report: str | None = None
    result_frozen: str | None = None
    result_state: dict[str, Any] | None = None
    if context == "unattended" and entry == "recover":
        return _result(capabilities, "operator-held", mode=mode, engine_mode=None, report=None, frozen=None, resume_action="rerun recover interactively", detail="unattended recovery does not inspect or change artifacts")
    try:
        settings = load_settings(start)
        result_engine_mode = settings.engine_mode
        capabilities["repository-config-read"] = {"status": "ready", "mechanism": "merged kitconfig and repository inputs validated"}
        capabilities["shared-state-resolver"] = {"status": "ready", "mechanism": "own-session resolve_write_path"}
        capabilities["draft-finalize-engine-set"] = {"status": "ready", "mechanism": settings.engine_mode}
        capabilities["runtime-compute-selection"] = {"status": "degraded", "mechanism": f"{settings.analysis_tier} is instructed guidance"}
        store = ArtifactStore(settings, mode)
        try:
            lease = acquire(store, repository_identity=repository_identity(settings), config_fingerprint=settings.fingerprint, run_identity=None)
        except TriageError as gate_error:
            capabilities["single-writer-state-gate"] = {"status": "operator-held", "mechanism": str(gate_error)}
            if context == "interactive" and entry in {"recover", "test"}:
                outcome, detail, plan = _blocking_recovery(settings, store, request, approval_context)
                return _result(capabilities, outcome, mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="review or resume the exact recorded recovery transition", detail=detail, recovery_plan=plan)
            return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="use interactive recover for a proven-dead owner", detail=str(gate_error))
        capabilities["single-writer-state-gate"] = {"status": "ready", "mechanism": "exclusive complete-record hard-link gate"}
        try:
            state_observation, state_raw = observe(store.state_path)
            if state_raw is None:
                if entry in {"resume", "recover"}:
                    lease.release()
                    return _result(capabilities, "hard-stop", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="start with new or no argument" if entry == "resume" else "no recovery is available", detail="required active state is absent")
                state, state_digest, report_path, frozen_path, candidates, terminal = _new_draft(settings, store, lease, capabilities, request, context=context, notification=notification)
                _write_report(report_path, state, capabilities, terminal or "operator-held")
                lease.release()
                return _result(capabilities, terminal or "operator-held", mode=mode, engine_mode=settings.engine_mode, report=str(report_path), frozen=str(frozen_path), resume_action="resume with analysis bound to the frozen candidate index" if state["phase"] == "reserved" else "rerun with the exact pending approval or provider action", detail="durable triage state retained", identifiers=state.get("verified_tracker_identifiers"), candidate_index=state["frozen_snapshot"]["content"]["candidate_index"])
            gate_only_state = _gate_only_state_value(store, state_raw)
            if gate_only_state is not None:
                bundle = _prepared_gate_only_bundle(store, gate_only_state)
                if gate_only_state["kind"] == "gate-only-operator-held":
                    lease.release()
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="preserve the terminal gate-only evidence", detail="gate-only-operator-held")
                permitted = context == "interactive" and ((mode == "live" and entry == "recover") or mode == "test")
                if not permitted:
                    lease.release()
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="resume the exact recorded recovery transition interactively", detail=gate_only_state["kind"])
                # The generic entry gate was acquired before state observation. It
                # is not the replacement gate declared by the durable intent, so
                # release it and let the digest-bound recovery transition acquire
                # its own identity. The intent continues to block ordinary work.
                lease.release()
                receipt = resume_gate_only(store, settings, bundle)
                return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="preserve the terminal gate-only evidence", detail=receipt["kind"])
            restart = _restart_receipt(store, state_raw)
            if restart is not None:
                if entry == "resume" or entry == "recover":
                    lease.release()
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="start a new run from the verified restart receipt", detail="safe-restart receipt is not an active session")
                state, state_digest, report_path, frozen_path, candidates, terminal = _new_draft(
                    settings, store, lease, capabilities, request, context=context, notification=notification, restart_receipt=restart
                )
                _write_report(report_path, state, capabilities, terminal or "operator-held")
                lease.release()
                return _result(capabilities, terminal or "operator-held", mode=mode, engine_mode=settings.engine_mode, report=str(report_path), frozen=str(frozen_path), resume_action="rerun with the exact pending approval or provider action", detail="verified recovery receipt replaced by reserved new state", identifiers=state.get("verified_tracker_identifiers"))
            if entry == "recover":
                captured = capture_state_present(store, settings, require_terminated=False, publish=False)
                try:
                    canonical_state(state_raw, settings=settings, mode=mode)
                except TriageError:
                    captured = capture_state_present(store, settings, require_terminated=False, publish=True)
                    plan = state_action_plan(store, settings, captured)
                    if plan.get("held") is not None:
                        held = prepare_state_action(store, settings, captured, approval={}, operator="")
                        lease.held = False
                        return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="inspect retained state-present held evidence", detail=held["terminal_classification"], recovery_plan=plan)
                    approval = _recovery_approval(request, approval_context, plan["action_core_digest"])
                    if approval is None:
                        lease.held = False
                        return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="approve the exact recorded recovery action", detail="invalid state captured before parse", recovery_plan=plan)
                    prepared = prepare_state_action(store, settings, captured, approval=approval, operator=approval_context.operator_identity)
                    receipt = resume_state_action(store, prepared)
                    lease.held = False
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="restart only from the exact recovery receipt", detail=str(receipt.get("kind")))
                lease.release()
                return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="resume", detail="captured state is valid; recovery refused")
            if entry == "test":
                try:
                    canonical_state(state_raw, settings=settings, mode=mode)
                except TriageError:
                    if context == "unattended":
                        lease.release()
                        return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="rerun test interactively to inspect exact recovery evidence", detail="invalid test state preserved without unattended recovery")
                    captured = capture_state_present(store, settings, require_terminated=False, publish=True)
                    plan = state_action_plan(store, settings, captured)
                    if plan.get("held") is not None:
                        held = prepare_state_action(store, settings, captured, approval={}, operator="")
                        lease.held = False
                        return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="inspect retained test state held evidence", detail=held["terminal_classification"], recovery_plan=plan)
                    approval = _recovery_approval(request, approval_context, plan["action_core_digest"])
                    if approval is None:
                        lease.held = False
                        return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="approve the exact recorded test recovery action", detail="invalid test state captured before parse", recovery_plan=plan)
                    prepared = prepare_state_action(store, settings, captured, approval=approval, operator=approval_context.operator_identity)
                    receipt = resume_state_action(store, prepared)
                    lease.held = False
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=settings.engine_mode, report=None, frozen=None, resume_action="restart test only from the exact recovery receipt", detail=str(receipt.get("kind")))
            state = canonical_state(state_raw, settings=settings, mode=mode)
            frozen_path = _validate_frozen_artifact(store, state)
            result_state = state
            result_frozen = str(frozen_path)
            if state.get("proposal_payloads"):
                result_report = state["proposal_payloads"][0]["report_binding"]["path"]
            if state.get("finalization_operations"):
                _validate_forge_prefix(
                    state["finalization_operations"], state, settings
                )
            if state["phase"] == "completed" and entry in {None, "new", "test"}:
                # A completed session holds no pending approval, attempt or merge,
                # so a session-starting entry retires it rather than letting it end
                # the mode (#425). The bytes are renamed, never deleted, under the
                # held gate and only after the full validation above; a crash
                # between the rename and the claim leaves the state absent, which
                # the next run treats as a fresh start.
                retired_path = Path(f"{store.state_path}.completed-{state['completion']['completed_receipt_digest'][:16]}")
                quarantine_inode(store.state_path, retired_path, state_observation, state_raw)
                retired = f"retired completed state to {retired_path} (sha256 {digest_bytes(state_raw)})"
                state, state_digest, report_path, frozen_path, candidates, terminal = _new_draft(settings, store, lease, capabilities, request, context=context, notification=notification)
                _write_report(report_path, state, capabilities, terminal or "operator-held")
                lease.release()
                return _result(capabilities, terminal or "operator-held", mode=mode, engine_mode=settings.engine_mode, report=str(report_path), frozen=str(frozen_path), resume_action="resume with analysis bound to the frozen candidate index" if state["phase"] == "reserved" else "rerun with the exact pending approval or provider action", detail=f"{retired}; durable triage state retained", identifiers=state.get("verified_tracker_identifiers"), candidate_index=state["frozen_snapshot"]["content"]["candidate_index"])
            if entry == "new":
                lease.release()
                return _result(
                    capabilities,
                    "operator-held",
                    mode=mode,
                    engine_mode=state["engine_mode"],
                    report=result_report,
                    frozen=result_frozen,
                    resume_action="resume",
                    detail="new refuses to overwrite active state",
                    identifiers=state.get("verified_tracker_identifiers"),
                    candidate_index=state["frozen_snapshot"]["content"]["candidate_index"],
                    **_pr_result_fields(state),
                )
            if state["phase"] == "completed":
                completion = state["completion"]
                lease.release()
                return _result(
                    capabilities,
                    completion["outcome"],
                    mode=mode,
                    engine_mode=state["engine_mode"],
                    report=result_report,
                    frozen=str(frozen_path),
                    resume_action="preserve the completed receipt",
                    detail=f"completed/{completion['route']}",
                    identifiers=state.get("verified_tracker_identifiers"),
                    candidate_index=state["frozen_snapshot"]["content"]["candidate_index"],
                    **_pr_result_fields(state),
                )
            if state["phase"] == "awaiting-approval" and isinstance(request.get("approval"), dict):
                _approval_authority(state, request, approval_context)
            state, state_digest = _rebind(store, lease, state, state_raw)
            tracker_transition = tracker is not None and (
                (state["phase"] == "awaiting-approval" and isinstance(request.get("approval"), dict))
                or state["phase"] == "tracker-write"
            )
            forge_transition = request.get("finalize") is True and state["phase"] in {
                "tracker-write", "forge-finalize", "archive-sweep"
            }
            if tracker_transition or forge_transition:
                pending_report = Path(state["proposal_payloads"][0]["report_binding"]["path"])
                _write_report(pending_report, state, capabilities, "operator-held")
                observed_protected_head = _observe_protected_head(
                    settings, state, head_authority or forge
                )
            report_path = Path(state["proposal_payloads"][0]["report_binding"]["path"]) if state.get("proposal_payloads") else None
            terminal = "operator-held"
            freshly_presented = False
            if state["phase"] == "notification-delivery":
                state, state_digest, terminal = _resume_notification_delivery(
                    store, lease, state, state_digest, capabilities, notification
                )
            if state["phase"] == "reserved":
                if context != "interactive":
                    lease.release()
                    return _result(capabilities, "operator-held", mode=mode, engine_mode=state["engine_mode"], report=None, frozen=str(frozen_path), resume_action="resume interactively with analysis bound to the frozen snapshot", detail="reserved analysis handoff cannot infer an unattended provider", candidate_index=state["frozen_snapshot"]["content"]["candidate_index"])
                state, state_digest, report_path = _resume_reserved(settings, store, lease, state, state_digest, request, capabilities)
                freshly_presented = True
            if state["phase"] == "awaiting-approval" and not freshly_presented:
                if state.get("notification_thread_reference") is None and state.get("notification_operations") == []:
                    capabilities["notification-thread"] = {"status": "degraded", "mechanism": "interactive current-session presentation"}
                if context == "unattended" and not isinstance(request.get("approval"), dict):
                    state, state_digest = _unattended_reminder(settings, store, lease, state, state_digest, capabilities, notification)
                else:
                    state, state_digest, terminal = _apply_approval(settings, store, lease, state, state_digest, request, capabilities, tracker, approval_context)
            if state["phase"] == "tracker-write" and not isinstance(request.get("approval"), dict):
                if tracker is None:
                    capabilities["tracker-write-readback"] = _tracker_unavailable(
                        state["decisions"], "retained tracker batch requires a read-back provider"
                    )
                else:
                    state, state_digest, terminal = _advance_tracker_batch(
                        settings, store, lease, state, state_digest, capabilities, tracker
                    )
            if state["phase"] in {"tracker-write", "forge-finalize", "archive-sweep"}:
                if request.get("finalize") is True and observed_protected_head is None:
                    if state.get("proposal_payloads"):
                        pending_report = Path(state["proposal_payloads"][0]["report_binding"]["path"])
                        _write_report(pending_report, state, capabilities, "operator-held")
                    observed_protected_head = _observe_protected_head(
                        settings, state, head_authority or forge
                    )
                state, state_digest, terminal = _advance_finalize(settings, store, lease, state, state_digest, request, capabilities, forge)
            if report_path is not None:
                _write_report(report_path, state, capabilities, terminal)
            lease.release()
            return _result(capabilities, terminal, mode=mode, engine_mode=state["engine_mode"], report=str(report_path) if report_path else None, frozen=str(frozen_path), resume_action="resume", detail="active session resumed", identifiers=state.get("verified_tracker_identifiers"), observed_protected_head=observed_protected_head, **_pr_result_fields(state))
        except TriageError:
            if lease.held:
                lease.release()
            raise
        except Exception:
            # Preserve the complete gate on an unexpected interruption path.
            # A handled TriageError is reported by the outer block, but the gate
            # remains when durable state may need recovery classification.
            raise
    except TriageError as exc:
        retained = result_state or {}
        return _result(
            capabilities,
            exc.outcome,
            mode=mode,
            engine_mode=result_engine_mode,
            report=result_report,
            frozen=result_frozen,
            resume_action="inspect retained evidence and follow the named recovery route",
            detail=str(exc),
            identifiers=retained.get("verified_tracker_identifiers"),
            candidate_index=retained.get("frozen_snapshot", {}).get("content", {}).get("candidate_index"),
            **_pr_result_fields(retained),
        )
