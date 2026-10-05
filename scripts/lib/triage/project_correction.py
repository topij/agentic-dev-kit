"""Narrow correction authority for an attested Linear pre-create rejection.

An absent marker is not no-write proof. The invoking runtime must independently
attest the actual installed adapter and terminal invocation, outside request JSON.
Only the retained project guard of the declared adapter contract is accepted;
unknown adapters and transport/create failures remain in flight.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import PurePath
from typing import Any

from .approval import ApprovalContext
from .canonical import CanonicalError, decode_bytes, digest, digest_bytes, loads_exact
from .model import (
    CAPABILITIES,
    SHA256_RE,
    Settings,
    TriageError,
    canonical_state,
    tracker_destination,
    validate_state,
)

# This is a security contract identifier, not an installation/version reading.
# The declared adapter rejects a differing project before its create mutation.
# A runtime attestation cannot substitute an unknown provider implementation.
PROJECT_GUARD_PROVIDER_SHA256 = "ec0643678ea7b93d0f881079d745a0dddffea16d38f03f206b58c01cf359ba9c"
PROJECT_GUARD_DETAIL = "approved Linear project differs from configured destination"


def _held(message: str) -> None:
    raise TriageError(message, outcome="operator-held")


def rejection_proof(
    state: dict[str, Any], raw: bytes, settings: Settings,
    context: ApprovalContext | None,
) -> dict[str, Any]:
    """Validate a trusted observer's bound legacy guard evidence, without I/O."""
    if (
        state.get("mode") != "live" or state.get("phase") != "tracker-write"
        or "proposal_correction" in state
        or state.get("verified_tracker_identifiers") != []
        or state.get("repository_evidence") != []
        or state.get("pull_request_evidence") != []
        or state.get("notification_operations") != []
        or state.get("notification_thread_reference") is not None
        or not isinstance(state.get("approval"), dict)
    ):
        _held("project correction requires an untouched interactive tracker batch")
    filed = [item for item in state["decisions"] if item["decision"] == "file"]
    if len(filed) != 1 or any(item["decision"] not in {"file", "park"} for item in state["decisions"]):
        _held("project correction requires a single rejected filing and parked remainder")
    operations = state["operations"]
    if len(operations) != 1 or state["attempts"] != operations:
        _held("project correction cannot settle an earlier or reconciled attempt")
    operation = operations[0]
    if (
        operation["status"] != "attempting" or operation["response"] is not None
        or operation["returned_identifier"] is not None or operation["read_back"] is not None
        or operation["verified_route"] is not None or operation["search_read_back"] != []
    ):
        _held("project correction cannot settle an uncertain or observed create")
    destination = tracker_destination(settings.tracker)
    proposal = next(item for item in state["proposal_payloads"] if item["candidate_id"] == operation["candidate_id"])
    if destination["backend"] != "linear" or proposal["payload"]["project"] == destination["project"]:
        _held("project correction lacks the deterministic project rejection")
    if (
        context is None or context.source != "current-session"
        or context.operator_identity != state["approval"]["approver_identity"]
        or not isinstance(context.source_read_back, dict)
    ):
        _held("project correction requires a trusted runtime rejection observer")
    proof = context.source_read_back
    if set(proof) != {"state_digest", "report_digest", "provider_source_sha256", "route", "invocation", "stdout_raw"}:
        _held("project rejection observer has the wrong shape")
    if (
        proof["state_digest"] != digest_bytes(raw)
        or not isinstance(proof["report_digest"], str) or SHA256_RE.fullmatch(proof["report_digest"]) is None
        or proof["provider_source_sha256"] != PROJECT_GUARD_PROVIDER_SHA256
        or proof["route"] != "observed-unmodified-installed-linear-adapter"
    ):
        _held("project rejection observer does not bind the retained adapter and state")
    invocation = proof["invocation"]
    if not isinstance(invocation, dict):
        _held("project rejection invocation is missing")
    command = invocation.get("command")
    if (
        invocation.get("revision") != state["run_identity"]["protected_branch_head"]
        or invocation.get("directory") != str(settings.paths.repo)
        or isinstance(invocation.get("exit_code"), bool) or invocation.get("exit_code") != 0
        or not isinstance(invocation.get("date"), str) or not invocation["date"]
        or not isinstance(command, list) or any(not isinstance(item, str) for item in command)
        or "resume" not in command or "--enable-tracker" not in command
        or "--enable-github-forge" in command
    ):
        _held("project rejection invocation is outside the retained installed route")
    try:
        stdout = decode_bytes(proof["stdout_raw"])
        response = loads_exact(stdout.removesuffix(b"\n"))
    except (CanonicalError, TypeError, ValueError) as exc:
        raise TriageError("project rejection terminal output is invalid", outcome="operator-held") from exc
    if (
        invocation.get("stdout_sha256") != digest_bytes(stdout)
        or not isinstance(response, dict) or response.get("outcome") != "operator-held"
        or response.get("execution_mode") != "live" or response.get("detail") != PROJECT_GUARD_DETAIL
        or response.get("verified_tracker_identifiers") != []
        or response.get("report") != proposal["report_binding"]["path"]
        or not isinstance(response.get("frozen_snapshot"), str)
        or not PurePath(response["frozen_snapshot"]).is_absolute()
        or PurePath(response["frozen_snapshot"]).parts[-len(PurePath(state["frozen_snapshot"]["path"]).parts[1:]):] != PurePath(state["frozen_snapshot"]["path"]).parts[1:]
        or response.get("candidate_index") != state["frozen_snapshot"]["content"]["candidate_index"]
    ):
        _held("terminal invocation does not establish the declared pre-create guard")
    return {"source": context.source, "operator_identity": context.operator_identity, "source_read_back": proof}


def validate_receipt(value: dict[str, Any], settings: Settings) -> None:
    """Keep original approval/attempt bytes and corrected-only intent checkable."""
    receipt = value["proposal_correction"]
    if value.get("mode") != "live" or value.get("phase") not in {"awaiting-approval", "tracker-write", "forge-finalize", "archive-sweep", "completed"}:
        _held("project correction receipt is outside its live presentation route")
    if not isinstance(receipt, dict) or set(receipt) != {"action_core", "action_core_digest", "approval"}:
        _held("project correction receipt has the wrong shape")
    core = receipt["action_core"]
    expected_keys = {
        "kind", "schema_version", "run_identity", "frozen_inbox_digest", "configuration",
        "captured_state_raw", "captured_state_digest", "captured_report_raw", "captured_report_digest",
        "destination", "rejection_observer", "original_marker_read_back", "corrected_marker_read_back",
        "corrected_proposal_payloads", "corrected_proposal_set_digest", "transition",
        "corrected_report_raw", "corrected_report_digest", "report_capabilities",
    }
    if (
        not isinstance(core, dict) or set(core) != expected_keys
        or core.get("kind") != "linear-project-correction" or type(core.get("schema_version")) is not int
        or core["schema_version"] != 1 or core["transition"] != "re-present-without-filing-approval"
        or receipt["action_core_digest"] != digest(core)
        or core["original_marker_read_back"] != [] or core["corrected_marker_read_back"] != []
        or not isinstance(core["corrected_proposal_payloads"], list)
        or any(not isinstance(item, dict) for item in core["corrected_proposal_payloads"])
    ):
        _held("project correction action core is invalid")
    try:
        old_raw = decode_bytes(core["captured_state_raw"])
        old_report = decode_bytes(core["captured_report_raw"])
        corrected_report = decode_bytes(core["corrected_report_raw"])
        old_value = loads_exact(old_raw)
    except (CanonicalError, TypeError, ValueError) as exc:
        raise TriageError("project correction retained bytes are invalid", outcome="operator-held") from exc
    if (
        digest_bytes(old_raw) != core["captured_state_digest"]
        or digest_bytes(old_report) != core["captured_report_digest"]
        or digest_bytes(corrected_report) != core["corrected_report_digest"]
    ):
        _held("project correction retained bytes changed")
    configuration = core["configuration"]
    if not isinstance(configuration, dict) or not isinstance(configuration.get("tracker"), dict):
        _held("project correction configuration evidence is invalid")
    old_settings = replace(settings, fingerprint=digest(configuration), tracker=configuration["tracker"])
    if not isinstance(old_value, dict) or "proposal_correction" in old_value:
        _held("project correction cannot contain another correction history")
    old = canonical_state(old_raw, settings=old_settings, mode="live")
    observer = core["rejection_observer"]
    if not isinstance(observer, dict) or set(observer) != {"source", "operator_identity", "source_read_back"}:
        _held("project correction retained observer is invalid")
    rejection_proof(old, old_raw, old_settings, ApprovalContext(**observer))
    if observer["source_read_back"]["report_digest"] != core["captured_report_digest"]:
        _held("project correction report differs from the observed original presentation")
    approval = receipt["approval"]
    if approval != {
        "decision": "approve", "source": "current-session",
        "approver_identity": observer["operator_identity"], "core_digest": receipt["action_core_digest"],
    }:
        _held("project correction lacks its exact action approval")
    if (
        core["run_identity"] != value["run_identity"] or old["run_identity"] != value["run_identity"]
        or core["frozen_inbox_digest"] != value["frozen_inbox_digest"]
        or old["frozen_snapshot"] != value["frozen_snapshot"]
        or core["destination"] != tracker_destination(old_settings.tracker)
        or core["corrected_proposal_set_digest"] != digest([item["payload_digest"] for item in core["corrected_proposal_payloads"]])
    ):
        _held("project correction changes immutable run authority")
    corrected = core["corrected_proposal_payloads"]
    if len(corrected) != len(old["proposal_payloads"]):
        _held("project correction changes candidate coverage")
    for before, after in zip(old["proposal_payloads"], corrected, strict=True):
        if (
            after.get("candidate_id") != before["candidate_id"]
            or after.get("source_block") != before["source_block"]
            or after.get("source_block_digest") != before["source_block_digest"]
            or after.get("payload_core") != {**before["payload_core"], "project": core["destination"]["project"]}
        ):
            _held("project correction contains a change beyond the configured project")
    initial_presentation = {
        **old, "phase": "awaiting-approval", "proposal_payloads": corrected,
        "proposal_payload_digests": [item.get("payload_digest") for item in corrected],
        "approval": None, "decisions": [], "attempts": [],
    }
    initial_presentation.pop("operations")
    validate_state(initial_presentation, settings=old_settings, mode="live")
    capabilities = core["report_capabilities"]
    if (
        not isinstance(capabilities, dict) or set(capabilities) != set(CAPABILITIES)
        or any(not isinstance(item, dict) or set(item) != {"status", "mechanism"}
               or any(not isinstance(field, str) for field in item.values()) for item in capabilities.values())
    ):
        _held("project correction report capabilities are invalid")
    from .engine import _report_text
    if corrected_report != _report_text(initial_presentation, capabilities, "operator-held"):
        _held("project correction report does not present its exact corrected proposals")
    if any(item.get("payload_core", {}).get("project") != core["destination"]["project"] for item in value.get("proposal_payloads", [])):
        _held("project correction current proposals changed the corrected destination")
    for before, after in zip(corrected, value["proposal_payloads"], strict=True):
        if after["payload_core"] != {**before["payload_core"], "body_without_marker": after["payload_core"]["body_without_marker"]}:
            _held("project correction current proposals changed beyond a normal body modification")
    # Later normal body modifications may change the current proposals, but a
    # project correction is only initially published without an approval. The
    # immutable correction core always preserves its exact initial presentation.
    if value.get("approval") is not None and value["approval"] == old["approval"]:
        _held("project correction reused the rejected filing approval")
