"""Strict configuration, identity, state, and operation models."""

from __future__ import annotations

import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from kitconfig import get, load_config, repo_root

from .canonical import CanonicalError, decode_bytes, digest, digest_bytes, loads_exact

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
PHASES = {
    "reserved",
    "propose",
    "notification-delivery",
    "awaiting-approval",
    "tracker-write",
    "forge-finalize",
    "archive-sweep",
    "completed",
}
CAPABILITIES = (
    "repository-config-read",
    "shared-state-resolver",
    "single-writer-state-gate",
    "frozen-inbox-state",
    "draft-finalize-engine-set",
    "notification-thread",
    "tracker-write-readback",
    "forge-pr-write-readback",
    "pr-watch",
    "runtime-compute-selection",
)


class TriageError(RuntimeError):
    def __init__(self, message: str, *, outcome: str = "hard-stop") -> None:
        super().__init__(message)
        self.outcome = outcome


@dataclass(frozen=True)
class Paths:
    repo: Path
    friction_log: Path
    archive: Path
    engine_dir: Path
    state_fragment: str
    gate_fragment: str
    recovery_pattern: str
    frozen_pattern: str
    report_root: Path
    report_pattern: str


@dataclass(frozen=True)
class Settings:
    config: dict[str, Any]
    fingerprint: str
    paths: Paths
    protected_branch: str
    triage_branch_pattern: str
    analysis_tier: str
    draft_engine: Path
    finalize_engine: Path
    engine_mode: str
    commit_subject: str
    tracker: dict[str, Any]
    notify: dict[str, Any]


def _required(config: dict[str, Any], name: str) -> Any:
    try:
        return get(config, name)
    except (KeyError, TypeError) as exc:
        raise TriageError(
            f"missing configuration key {name}; refresh init.sh and rerun ./init.sh --no-clobber"
        ) from exc


def _fragment(value: Any, name: str, placeholders: tuple[str, ...] = ()) -> str:
    if not isinstance(value, str) or not value:
        raise TriageError(f"{name} must be a non-empty string")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise TriageError(f"{name} must be a contained relative path")
    for placeholder in placeholders:
        if "{" + placeholder + "}" not in value:
            raise TriageError(f"{name} must contain {{{placeholder}}}")
    return value


def _engine_path(engine_dir: Path, value: Any, name: str) -> Path:
    fragment = _fragment(value, name)
    candidate = engine_dir / fragment
    resolved_parent = candidate.parent.resolve()
    engine_root = engine_dir.resolve()
    if not resolved_parent.is_relative_to(engine_root):
        raise TriageError(f"{name} escapes paths.engines")
    if candidate.exists() and (candidate.is_symlink() or not candidate.is_file()):
        raise TriageError(f"{name} is not a contained regular file")
    if candidate.exists() and not candidate.resolve().is_relative_to(engine_root):
        raise TriageError(f"{name} resolves outside paths.engines")
    return candidate


def _repo_path(root: Path, value: Any, name: str) -> Path:
    fragment = _fragment(value, name)
    candidate = root / fragment
    resolved_parent = candidate.parent.resolve()
    if not resolved_parent.is_relative_to(root):
        raise TriageError(f"{name} escapes the repository")
    if candidate.exists() and (candidate.is_symlink() or not candidate.is_file()):
        raise TriageError(f"{name} is not a contained regular file")
    if candidate.exists() and not candidate.resolve().is_relative_to(root):
        raise TriageError(f"{name} resolves outside the repository")
    return candidate


def load_settings(start: Path | None = None) -> Settings:
    root = repo_root(start).resolve()
    config = load_config(root / "config/dev-model.yaml")
    fingerprint = digest(config)
    engine_dir = root / _fragment(_required(config, "paths.engines"), "paths.engines")
    if engine_dir.exists() and (engine_dir.is_symlink() or not engine_dir.is_dir()):
        raise TriageError("paths.engines must be a contained directory")
    if not engine_dir.resolve().is_relative_to(root):
        raise TriageError("paths.engines escapes the repository")
    friction = _repo_path(root, _required(config, "paths.friction_log"), "paths.friction_log")
    archive = _repo_path(root, _required(config, "paths.friction_log_archive"), "paths.friction_log_archive")
    if friction == archive:
        raise TriageError("friction log and archive paths collide")
    state_dir = _required(config, "state.dirname")
    if state_dir != "state":
        raise TriageError("state.dirname does not match state_paths.STATE_DIRNAME")
    state_path = _fragment(_required(config, "triage.state_path"), "triage.state_path", ("mode",))
    gate_path = _fragment(_required(config, "triage.gate_path"), "triage.gate_path", ("mode",))
    recovery = _fragment(
        _required(config, "triage.recovery_bundle_pattern"),
        "triage.recovery_bundle_pattern",
        ("mode", "gate_digest"),
    )
    frozen = _fragment(
        _required(config, "triage.frozen_inbox_pattern"),
        "triage.frozen_inbox_pattern",
        ("mode", "date", "session"),
    )
    for name, value in (("state", state_path), ("gate", gate_path), ("recovery", recovery), ("frozen", frozen)):
        if not value.startswith(state_dir + "/"):
            raise TriageError(f"triage {name} path must begin with state.dirname")
    rendered_artifacts: list[str] = []
    for mode in ("live", "test"):
        rendered_artifacts.extend([
            state_path.replace("{mode}", mode),
            gate_path.replace("{mode}", mode),
            recovery.replace("{mode}", mode).replace("{gate_digest}", "0" * 64),
            frozen.replace("{mode}", mode).replace("{date}", "2000-01-01").replace("{session}", "session"),
        ])
    if len(rendered_artifacts) != len(set(rendered_artifacts)):
        raise TriageError("configured triage artifact paths collide")
    report_root_rel = _fragment(_required(config, "triage.report_root"), "triage.report_root")
    report_root = (root / report_root_rel).resolve()
    if report_root == root or not report_root.is_relative_to(root):
        raise TriageError("triage.report_root must be a contained child")
    report_pattern = _fragment(
        _required(config, "triage.report_pattern"),
        "triage.report_pattern",
        ("mode", "date", "session"),
    )
    report_candidate = (root / report_pattern.replace("{mode}", "live").replace("{date}", "2000-01-01").replace("{session}", "x")).resolve()
    if not report_candidate.is_relative_to(report_root):
        raise TriageError("triage.report_pattern must resolve below triage.report_root")
    analysis = _required(config, "triage.analysis_tier")
    tiers = _required(config, "models.tiers")
    if not isinstance(analysis, str) or not isinstance(tiers, dict) or analysis not in tiers:
        raise TriageError("triage.analysis_tier must name models.tiers")
    if _required(config, "triage.pr_draft") is not False:
        raise TriageError("triage.pr_draft must be false")
    protected_branch = _required(config, "vcs.protected_branch")
    branch_pattern = _required(config, "vcs.triage_branch_pattern")
    if not isinstance(protected_branch, str) or not protected_branch:
        raise TriageError("vcs.protected_branch must be a non-empty string")
    if not isinstance(branch_pattern, str) or branch_pattern.count("{date}") != 1:
        raise TriageError("vcs.triage_branch_pattern must contain {date} exactly once")
    if branch_pattern.count("{session}") > 1:
        raise TriageError("vcs.triage_branch_pattern may contain {session} at most once")
    subject = _required(config, "triage.commit_subject")
    if not isinstance(subject, str) or not subject:
        raise TriageError("triage.commit_subject must be non-empty")
    draft = _engine_path(engine_dir, _required(config, "triage.draft_engine"), "triage.draft_engine")
    finalize = _engine_path(engine_dir, _required(config, "triage.finalize_engine"), "triage.finalize_engine")
    presence = (draft.is_file(), finalize.is_file())
    if presence == (True, True):
        engine_mode = "engine-backed"
    elif presence == (False, False):
        engine_mode = "llm-only"
    else:
        raise TriageError("configured triage engine set is partial")
    tracker = _required(config, "tracker")
    notify = _required(config, "notify")
    if not isinstance(tracker, dict) or not isinstance(notify, dict):
        raise TriageError("tracker and notify configuration must be mappings")
    paths = Paths(root, friction, archive, engine_dir, state_path, gate_path, recovery, frozen, report_root, report_pattern)
    return Settings(
        config,
        fingerprint,
        paths,
        protected_branch,
        branch_pattern,
        analysis,
        draft,
        finalize,
        engine_mode,
        subject,
        dict(tracker),
        dict(notify),
    )


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True)
    if result.returncode:
        raise TriageError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def repository_identity(settings: Settings) -> dict[str, Any]:
    return {
        "root": str(settings.paths.repo),
        "remote": git_output(settings.paths.repo, "remote", "get-url", "origin"),
    }


def new_run_identity(settings: Settings, mode: str, session: str | None = None) -> dict[str, Any]:
    if mode not in {"live", "test"}:
        raise TriageError("invalid triage mode")
    head = git_output(settings.paths.repo, "rev-parse", f"refs/remotes/origin/{settings.protected_branch}")
    if not OID_RE.fullmatch(head):
        raise TriageError("protected branch head is not a full lowercase object id")
    return {
        "repository_identity": repository_identity(settings),
        "friction_log": str(settings.paths.friction_log.relative_to(settings.paths.repo)),
        "protected_branch_head": head,
        "mode": mode,
        "session": session or uuid.uuid4().hex,
        "config_fingerprint": settings.fingerprint,
    }


def state_base(
    run_identity: dict[str, Any],
    gate_binding: dict[str, Any],
    state_claim: dict[str, Any],
    frozen_digest: str,
    frozen_snapshot: dict[str, Any],
    engine_mode: str,
) -> dict[str, Any]:
    return {
        "kind": "triage-run-state",
        "schema_version": 1,
        "phase": "reserved",
        "mode": run_identity["mode"],
        "run_identity": run_identity,
        "gate_owner_token": gate_binding["owner_token"],
        "gate_binding": gate_binding,
        "state_claim": state_claim,
        "config_fingerprint": run_identity["config_fingerprint"],
        "frozen_inbox_digest": frozen_digest,
        "frozen_snapshot": frozen_snapshot,
        "engine_mode": engine_mode,
        "attempts": [],
        "verified_tracker_identifiers": [],
        "repository_evidence": [],
        "pull_request_evidence": [],
    }


BASE_KEYS = set(state_base(
    {"mode": "live", "config_fingerprint": "x"},
    {"owner_token": "x"},
    {},
    "x",
    {},
    "engine-backed",
))


SWEEP_CLEANUP_ARTIFACTS = ("worktree", "local_branch", "remote_branch")


def _validate_sweep_cleanup(sweep_cleanup: Any) -> None:
    """Validate an optional `completion.sweep_cleanup` (#807): one guarded,
    idempotent result per retired artifact, `removed`/`absent` with no reason or
    `kept` with one. Absent entirely is valid — a state a previous engine
    completed before this field existed, or a run whose merge verified before the
    cleanup step existed."""
    if sweep_cleanup is None:
        return
    if not isinstance(sweep_cleanup, dict) or set(sweep_cleanup) != set(SWEEP_CLEANUP_ARTIFACTS):
        raise TriageError("sweep cleanup record has the wrong shape", outcome="operator-held")
    for entry in sweep_cleanup.values():
        if not isinstance(entry, dict) or set(entry) != {"result", "reason"} or entry.get("result") not in {"removed", "absent", "kept"}:
            raise TriageError("sweep cleanup entry has the wrong shape", outcome="operator-held")
        if entry["result"] == "kept":
            if not isinstance(entry.get("reason"), str) or not entry["reason"]:
                raise TriageError("sweep cleanup kept entry lacks a reason", outcome="operator-held")
        elif entry.get("reason") is not None:
            raise TriageError("sweep cleanup removed or absent entry fabricates a reason", outcome="operator-held")


def terminal_pr_watch_receipt(receipt: Any, *, head: str, url: str) -> bool:
    return (
        isinstance(receipt, dict)
        and receipt.get("converged") is True
        and receipt.get("mergeable") is True
        and receipt.get("done") is True
        and receipt.get("merge_blockers") == []
        and receipt.get("head") == head
        and receipt.get("url") == url
        and receipt.get("truncated_reads") == []
        and isinstance(receipt.get("review_evidence"), dict)
        and receipt["review_evidence"].get("valid") is True
    )


def validate_state(value: Any, *, settings: Settings, mode: str) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or value.get("kind") != "triage-run-state"
        or isinstance(value.get("schema_version"), bool)
        or value.get("schema_version") != 1
    ):
        raise TriageError("invalid triage state", outcome="operator-held")
    phase = value.get("phase")
    if not isinstance(phase, str) or phase not in PHASES:
        raise TriageError("unrecognized triage state phase", outcome="operator-held")
    required = BASE_KEYS | {
        "propose": {"proposal_payloads", "proposal_payload_digests"},
        "notification-delivery": {"proposal_payloads", "proposal_payload_digests", "notification_operations"},
        "awaiting-approval": {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions"},
        "tracker-write": {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions", "operations"},
        "forge-finalize": {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions", "operations", "finalization_operations"},
        "archive-sweep": {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions", "operations", "finalization_operations", "archive_sweep"},
        "completed": {"completion"},
    }.get(phase, set())
    if phase == "completed" and isinstance(value.get("completion"), dict):
        route = value["completion"].get("route")
        if route == "decision-only":
            required = BASE_KEYS | {"proposal_payloads", "proposal_payload_digests", "approval", "decisions", "completion"}
        elif route == "test-render":
            required = BASE_KEYS | {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions", "operations", "completion"}
        elif route == "archive-sweep":
            required = BASE_KEYS | {"proposal_payloads", "proposal_payload_digests", "approval", "notification_thread_reference", "notification_operations", "decisions", "operations", "finalization_operations", "archive_sweep", "completion"}
    if set(value) != required:
        raise TriageError("triage state has missing or extra phase fields", outcome="operator-held")
    identity = value.get("run_identity")
    if not isinstance(identity, dict) or set(identity) != {"repository_identity", "friction_log", "protected_branch_head", "mode", "session", "config_fingerprint"}:
        raise TriageError("invalid run identity", outcome="operator-held")
    if identity["mode"] != mode or value.get("mode") != mode:
        raise TriageError("cross-mode state", outcome="operator-held")
    if identity["config_fingerprint"] != settings.fingerprint or value.get("config_fingerprint") != settings.fingerprint:
        raise TriageError("configuration identity mismatch", outcome="operator-held")
    if identity.get("repository_identity") != repository_identity(settings):
        raise TriageError("repository identity mismatch", outcome="operator-held")
    if identity.get("friction_log") != str(settings.paths.friction_log.relative_to(settings.paths.repo)):
        raise TriageError("friction-log identity mismatch", outcome="operator-held")
    if (
        not isinstance(identity.get("protected_branch_head"), str)
        or not OID_RE.fullmatch(identity["protected_branch_head"])
        or not isinstance(identity.get("session"), str)
        or not TOKEN_RE.fullmatch(identity["session"])
    ):
        raise TriageError("run identity has malformed immutable fields", outcome="operator-held")
    if not isinstance(value.get("engine_mode"), str) or value.get("engine_mode") not in {"engine-backed", "llm-only"}:
        raise TriageError("invalid persisted engine mode", outcome="operator-held")
    if not SHA256_RE.fullmatch(str(value.get("frozen_inbox_digest", ""))):
        raise TriageError("invalid frozen digest", outcome="operator-held")
    for name in ("attempts", "verified_tracker_identifiers", "repository_evidence", "pull_request_evidence"):
        if not isinstance(value.get(name), list):
            raise TriageError(f"{name} must be an array", outcome="operator-held")
    binding = value.get("gate_binding")
    if not isinstance(binding, dict) or set(binding) != {"gate_path", "owner_token", "owner_run_identity", "gate_claim_core_digest"}:
        raise TriageError("invalid gate binding", outcome="operator-held")
    expected_gate = settings.paths.gate_fragment.replace("{mode}", mode)
    if expected_gate.startswith("state/"):
        from state_paths import resolve_write_path

        expected_gate_path = str(resolve_write_path(expected_gate[len("state/"):]))
    else:
        raise TriageError("configured gate path is outside shared state", outcome="operator-held")
    if (
        binding.get("gate_path") != expected_gate_path
        or binding.get("owner_token") != value.get("gate_owner_token")
        or not isinstance(value.get("gate_owner_token"), str)
        or not TOKEN_RE.fullmatch(value["gate_owner_token"])
        or not isinstance(binding.get("gate_claim_core_digest"), str)
        or not SHA256_RE.fullmatch(binding["gate_claim_core_digest"])
    ):
        raise TriageError("gate binding identity mismatch", outcome="operator-held")
    claim = value.get("state_claim")
    if not isinstance(claim, dict) or set(claim) != {"reason", "previous_gate_binding", "current_gate_binding", "captured_state_digest", "recovery_bundle_digest", "approval_digest"} or claim.get("current_gate_binding") != binding:
        raise TriageError("invalid state claim", outcome="operator-held")
    if not isinstance(claim.get("reason"), str) or claim.get("reason") not in {"initial-reservation", "normal-resume", "approved-recovery", "live-receipt-restart", "test-receipt-restart"}:
        raise TriageError("invalid state-claim reason", outcome="operator-held")
    frozen = value.get("frozen_snapshot")
    if not isinstance(frozen, dict) or set(frozen) != {"path", "content", "raw_encoding", "raw"} or frozen.get("raw_encoding") != "base64":
        raise TriageError("invalid frozen snapshot", outcome="operator-held")
    try:
        frozen_raw = decode_bytes(frozen["raw"])
    except (CanonicalError, KeyError) as exc:
        raise TriageError("invalid frozen snapshot bytes", outcome="operator-held") from exc
    if digest_bytes(frozen_raw) != value["frozen_inbox_digest"]:
        raise TriageError("frozen snapshot digest mismatch", outcome="operator-held")
    from .inbox import parse, snapshot_content

    frozen_candidates = parse(frozen_raw)
    if frozen.get("content") != snapshot_content(frozen_raw, frozen_candidates):
        raise TriageError("frozen snapshot candidate index mismatch", outcome="operator-held")
    expected_frozen = settings.paths.frozen_pattern.replace("{mode}", mode).replace("{session}", identity["session"])
    if not isinstance(frozen.get("path"), str) or not re.fullmatch(re.escape(expected_frozen).replace(re.escape("{date}"), r"\d{4}-\d{2}-\d{2}"), frozen["path"]):
        raise TriageError("frozen snapshot path mismatch", outcome="operator-held")
    proposals = value.get("proposal_payloads")
    if proposals is not None:
        if not isinstance(proposals, list) or not proposals or value.get("proposal_payload_digests") != [item.get("payload_digest") for item in proposals if isinstance(item, dict)]:
            raise TriageError("proposal payload set mismatch", outcome="operator-held")
        index = {item.candidate_id: item for item in frozen_candidates}
        for proposal in proposals:
            keys = {"candidate_id", "payload_core", "payload_core_digest", "marker", "payload", "payload_digest", "source_block_digest", "source_block", "report_binding"}
            if not isinstance(proposal, dict) or set(proposal) != keys or proposal.get("candidate_id") not in index:
                raise TriageError("invalid proposal record", outcome="operator-held")
            candidate = index[proposal["candidate_id"]]
            core = proposal["payload_core"]
            payload = proposal["payload"]
            marker = proposal["marker"]
            expected_marker = f"<!-- triage-payload:{identity['session']}:{proposal['candidate_id']}:{proposal['payload_core_digest']} -->"
            if (
                proposal["source_block"] != candidate.record()
                or proposal["source_block_digest"] != candidate.digest
                or not isinstance(core, dict)
                or set(core) != {"title", "body_without_marker", "project", "labels"}
                or not isinstance(core.get("title"), str)
                or not isinstance(core.get("body_without_marker"), str)
                or not isinstance(core.get("project"), str)
                or not isinstance(core.get("labels"), list)
                or any(not isinstance(label, str) for label in core.get("labels", []))
                or digest(core) != proposal["payload_core_digest"]
                or marker != expected_marker
                or not isinstance(payload, dict)
                or set(payload) != {"title", "body", "project", "labels"}
                or payload != {
                    "title": core["title"],
                    "body": core["body_without_marker"].rstrip() + "\n\n" + marker,
                    "project": core["project"],
                    "labels": core["labels"],
                }
                or digest(payload) != proposal["payload_digest"]
            ):
                raise TriageError("proposal authority mismatch", outcome="operator-held")
            if not isinstance(marker, str) or proposal["payload"].get("body", "").count(marker) != 1:
                raise TriageError("proposal marker mismatch", outcome="operator-held")
        candidate_ids = [proposal["candidate_id"] for proposal in proposals]
        if (
            candidate_ids != [candidate.candidate_id for candidate in frozen_candidates]
            or len(candidate_ids) != len(set(candidate_ids))
            or len(value["proposal_payload_digests"]) != len(set(value["proposal_payload_digests"]))
        ):
            raise TriageError("proposal identifiers or digests are not unique", outcome="operator-held")
        report_core = {
            "run_identity": identity,
            "frozen_inbox_digest": value["frozen_inbox_digest"],
            "proposals": [
                {
                    "candidate_id": proposal["candidate_id"],
                    "source_block_digest": proposal["source_block_digest"],
                    "payload_digest": proposal["payload_digest"],
                }
                for proposal in proposals
            ],
        }
        binding = proposals[0]["report_binding"]
        expected_report = str(settings.paths.repo / settings.paths.report_pattern.replace("{mode}", mode).replace("{session}", identity["session"]))
        if (
            not isinstance(binding, dict)
            or set(binding) != {"path", "report_core", "report_core_digest"}
            or binding.get("report_core") != report_core
            or binding.get("report_core_digest") != digest(report_core)
            or not isinstance(binding.get("path"), str)
            or not re.fullmatch(re.escape(expected_report).replace(re.escape("{date}"), r"\d{4}-\d{2}-\d{2}"), binding["path"])
            or any(proposal["report_binding"] != binding for proposal in proposals)
        ):
            raise TriageError("proposal report binding mismatch", outcome="operator-held")
    approval = value.get("approval")
    decisions = value.get("decisions")
    if approval is not None:
        if not isinstance(approval, dict) or set(approval) != {"source", "approver_identity", "commands", "proposal_set_digest", "source_read_back"}:
            raise TriageError("approval record has the wrong shape", outcome="operator-held")
        if not isinstance(approval.get("source"), str) or approval.get("source") not in {"current-session", "notification-thread"} or not isinstance(approval.get("approver_identity"), str) or not approval["approver_identity"]:
            raise TriageError("approval identity is invalid", outcome="operator-held")
        if approval.get("proposal_set_digest") != digest(value.get("proposal_payload_digests")) or approval.get("commands") != decisions:
            raise TriageError("approval does not bind the decision plan", outcome="operator-held")
        read_back = approval.get("source_read_back")
        if not isinstance(read_back, dict) or read_back.get("approver_identity") != approval["approver_identity"] or read_back.get("proposal_set_digest") != approval["proposal_set_digest"] or read_back.get("payload_digests") != value["proposal_payload_digests"]:
            raise TriageError("approval source read-back mismatch", outcome="operator-held")
    if decisions is not None:
        if not isinstance(decisions, list) or any(not isinstance(item, dict) or set(item) - {"candidate_id", "decision", "proposal_digest", "replacement_body"} for item in decisions):
            raise TriageError("decision plan is malformed", outcome="operator-held")
        if decisions and proposals is not None and [(item.get("candidate_id"), item.get("proposal_digest")) for item in decisions] != [(item["candidate_id"], item["payload_digest"]) for item in proposals]:
            raise TriageError("decision plan does not cover proposals exactly", outcome="operator-held")
    notification_operations = value.get("notification_operations")
    if notification_operations is not None:
        if not isinstance(notification_operations, list) or len(notification_operations) > 2:
            raise TriageError("notification operations are malformed", outcome="operator-held")
        if [item.get("kind") for item in notification_operations if isinstance(item, dict)] != ["initial", "reminder"][:len(notification_operations)]:
            raise TriageError("notification operation order is malformed", outcome="operator-held")
        notification_keys = {
            "kind", "target", "proposal_set_digest", "rendered_payload",
            "rendered_payload_digest", "idempotency_key", "status", "response",
            "read_back", "attempts",
        }
        attempt_keys = notification_keys - {"attempts"}
        for operation in notification_operations:
            if not isinstance(operation, dict) or set(operation) != notification_keys:
                raise TriageError("notification operation has the wrong shape", outcome="operator-held")
            if not isinstance(operation["target"], str) or not operation["target"]:
                raise TriageError("notification target is malformed", outcome="operator-held")
            rendered = operation["rendered_payload"]
            if (
                not isinstance(rendered, str)
                or operation["rendered_payload_digest"] != digest(rendered)
                or operation["proposal_set_digest"] != digest(value.get("proposal_payload_digests"))
                or operation["idempotency_key"] != digest({"session": identity["session"], "kind": operation["kind"]})
            ):
                raise TriageError("notification operation binding mismatch", outcome="operator-held")
            if not isinstance(operation["status"], str) or operation["status"] not in {"attempting", "verified", "failed", "ambiguous"}:
                raise TriageError("notification operation status is invalid", outcome="operator-held")
            attempts = operation["attempts"]
            if not isinstance(attempts, list) or not attempts or any(not isinstance(item, dict) or set(item) != attempt_keys for item in attempts):
                raise TriageError("notification attempt history is malformed", outcome="operator-held")
            if attempts and any(
                any(item.get(name) != operation.get(name) for name in (
                    "kind", "target", "proposal_set_digest", "rendered_payload",
                    "rendered_payload_digest", "idempotency_key",
                ))
                for item in attempts
            ):
                raise TriageError("notification attempt history changes immutable intent", outcome="operator-held")
            if attempts and any(operation.get(name) != attempts[-1].get(name) for name in ("status", "response", "read_back")):
                raise TriageError("notification operation does not repeat its last attempt", outcome="operator-held")
            if operation["status"] == "verified":
                read_back = operation["read_back"]
                if (
                    not isinstance(read_back, dict)
                    or not isinstance(read_back.get("thread_reference"), str)
                    or not read_back["thread_reference"]
                    or read_back.get("marker") != identity["session"]
                    or read_back.get("target") != operation["target"]
                    or read_back.get("rendered_payload") != rendered
                    or read_back.get("rendered_payload_digest") != operation["rendered_payload_digest"]
                    or read_back.get("match_count") != 1
                ):
                    raise TriageError("verified notification read-back mismatch", outcome="operator-held")
    operations = value.get("operations")
    if operations is not None:
        if not isinstance(operations, list) or any(not isinstance(item, dict) for item in operations):
            raise TriageError("tracker operations must be an array", outcome="operator-held")
        filed = [item for item in decisions or [] if item.get("decision") == "file"]
        if [item.get("candidate_id") for item in operations] != [item.get("candidate_id") for item in filed[:len(operations)]]:
            raise TriageError("tracker operations are not the filed decision prefix", outcome="operator-held")
        identifiers = []
        proposal_by_candidate = {
            item["candidate_id"]: item for item in proposals or []
        }
        configured_destination = {
            "backend": settings.tracker.get("backend"),
            "host": urlparse(str(settings.tracker.get("url", ""))).hostname,
            "repository": settings.tracker.get("project_name"),
            "project": settings.tracker.get("project_name"),
        }
        for operation in operations:
            if not isinstance(operation, dict):
                raise TriageError("tracker operation has the wrong shape", outcome="operator-held")
            if not isinstance(operation.get("status"), str) or operation.get("status") not in {"attempting", "verified", "failed", "ambiguous", "would-create"}:
                raise TriageError("invalid tracker operation status", outcome="operator-held")
            proposal = proposal_by_candidate.get(operation.get("candidate_id"))
            if proposal is None or operation.get("decision") != "file" or operation.get("proposal_digest") != proposal["payload_digest"]:
                raise TriageError("tracker operation proposal binding mismatch", outcome="operator-held")
            if operation["status"] == "would-create":
                if set(operation) != {"candidate_id", "decision", "proposal_digest", "status", "response", "returned_identifier", "read_back"}:
                    raise TriageError("test tracker operation has the wrong shape", outcome="operator-held")
                continue
            expected_keys = {
                "candidate_id", "decision", "proposal_digest", "marker", "destination",
                "status", "response", "returned_identifier", "read_back",
                "verified_route", "search_read_back",
            }
            if set(operation) != expected_keys:
                raise TriageError("tracker operation has the wrong shape", outcome="operator-held")
            if operation["marker"] != proposal["marker"] or operation["destination"] != configured_destination or not isinstance(operation["search_read_back"], list):
                raise TriageError("tracker operation authority mismatch", outcome="operator-held")
            if operation.get("status") == "verified":
                read_back = operation.get("read_back")
                route = operation.get("verified_route")
                if not isinstance(route, str) or route not in {
                    "created-and-read-back", "pre-existing-exact-match",
                    "failed-response-then-exact-read-back",
                    "ambiguous-response-then-exact-read-back",
                }:
                    raise TriageError("verified tracker route is invalid", outcome="operator-held")
                if route == "pre-existing-exact-match" and operation.get("response") is not None:
                    raise TriageError("pre-existing tracker route fabricates a create response", outcome="operator-held")
                if route == "failed-response-then-exact-read-back" and operation.get("response") is None:
                    raise TriageError("failed-response tracker route lacks its response", outcome="operator-held")
                if (
                    not isinstance(read_back, dict)
                    or not isinstance(operation.get("returned_identifier"), str)
                    or read_back.get("identifier") != operation.get("returned_identifier")
                    or read_back.get("payload") != proposal["payload"]
                    or digest(read_back.get("payload")) != operation.get("proposal_digest")
                    or read_back.get("payload_digest") != operation.get("proposal_digest")
                    or read_back.get("marker") != operation.get("marker")
                    or read_back.get("destination") != operation.get("destination")
                ):
                    raise TriageError("verified tracker read-back mismatch", outcome="operator-held")
                identifiers.append(operation["returned_identifier"])
        if identifiers != value["verified_tracker_identifiers"] or len(identifiers) != len(set(identifiers)):
            raise TriageError("verified tracker identifier accounting mismatch", outcome="operator-held")
        for attempt in value["attempts"]:
            if not isinstance(attempt, dict) or set(attempt) != {
                "candidate_id", "decision", "proposal_digest", "marker", "destination",
                "status", "response", "returned_identifier", "read_back",
                "verified_route", "search_read_back",
            }:
                raise TriageError("tracker attempt history is malformed", outcome="operator-held")
            operation = next((item for item in operations if item.get("candidate_id") == attempt.get("candidate_id")), None)
            if operation is None or any(attempt.get(name) != operation.get(name) for name in ("candidate_id", "decision", "proposal_digest", "marker", "destination")):
                raise TriageError("tracker attempt history changes immutable intent", outcome="operator-held")
    finalization = value.get("finalization_operations")
    if finalization is not None:
        order = ["branch-create", "commit", "push", "pull-request", "pr-watch", "merge-read-back"]
        if (
            not isinstance(finalization, list)
            or any(not isinstance(item, dict) for item in finalization)
            or [item.get("kind") for item in finalization] != order[:len(finalization)]
        ):
            raise TriageError("finalization operation order mismatch", outcome="operator-held")
        for position, operation in enumerate(finalization):
            if (
                not isinstance(operation, dict)
                or set(operation) != {
                    "kind", "intent", "intent_digest", "status", "response",
                    "read_back", "attempts",
                }
                or not isinstance(operation.get("intent"), dict)
                or digest(operation.get("intent")) != operation.get("intent_digest")
                or not isinstance(operation.get("status"), str)
                or operation.get("status") not in {"attempting", "verified", "failed", "ambiguous", "unsettled"}
            ):
                raise TriageError("finalization operation is malformed", outcome="operator-held")
            if position < len(finalization) - 1 and operation.get("status") != "verified":
                raise TriageError("finalization operation prefix is not verified", outcome="operator-held")
            if operation.get("kind") == "commit":
                intent = operation["intent"]
                expected_paths = sorted([
                    str(settings.paths.friction_log.relative_to(settings.paths.repo)),
                    str(settings.paths.archive.relative_to(settings.paths.repo)),
                ])
                updates = intent.get("updates")
                authority = intent.get("authority_read_back")
                if (
                    intent.get("paths") != expected_paths
                    or not isinstance(updates, list)
                    or len(updates) != len(expected_paths)
                    or any(not isinstance(update, dict) for update in updates)
                    or [update.get("path") for update in updates] != expected_paths
                    or any(
                        set(update) != {
                            "path", "previous_content", "previous_digest",
                            "content", "content_digest",
                        }
                        for update in updates
                    )
                    or not isinstance(authority, dict)
                    or authority.get("paths") != expected_paths
                    or not isinstance(authority.get("staged_tree"), str)
                    or not isinstance(intent.get("migration_marker"), str)
                ):
                    raise TriageError("commit update intent is malformed", outcome="operator-held")
                try:
                    for update in updates:
                        previous = decode_bytes(update["previous_content"])
                        content = decode_bytes(update["content"])
                        if (
                            digest_bytes(previous) != update["previous_digest"]
                            or digest_bytes(content) != update["content_digest"]
                        ):
                            raise TriageError("commit update intent digest mismatch", outcome="operator-held")
                except (KeyError, TypeError, ValueError, CanonicalError) as exc:
                    raise TriageError("commit update intent is malformed", outcome="operator-held") from exc
            attempts = operation.get("attempts")
            if not isinstance(attempts, list) or not attempts:
                raise TriageError("finalization attempt history is missing", outcome="operator-held")
            last = attempts[-1]
            attempt_keys = {"kind", "intent", "intent_digest", "status", "response", "read_back"}
            if any(
                not isinstance(attempt, dict)
                or set(attempt) != attempt_keys
                or attempt.get("kind") != operation.get("kind")
                or attempt.get("intent") != operation.get("intent")
                or attempt.get("intent_digest") != operation.get("intent_digest")
                or digest(attempt.get("intent")) != attempt.get("intent_digest")
                for attempt in attempts
            ):
                raise TriageError("finalization attempt history changes immutable intent", outcome="operator-held")
            if any(operation.get(name) != last.get(name) for name in ("kind", "intent", "intent_digest", "status", "response", "read_back")):
                raise TriageError("finalization operation does not repeat its last attempt", outcome="operator-held")
            if operation["status"] == "verified" and not _forge_read_back_matches(
                operation["kind"], operation["intent"], operation["read_back"]
            ):
                raise TriageError("verified finalization read-back mismatch", outcome="operator-held")
        for previous, current in zip(finalization, finalization[1:], strict=False):
            if previous["status"] != "verified" or not _forge_predecessor_matches(
                previous["read_back"], current["kind"], current["intent"]
            ):
                raise TriageError("finalization predecessor binding mismatch", outcome="operator-held")
        expected_repository_evidence = [
            item for item in finalization
            if item.get("kind") in {"branch-create", "commit", "push"} and item.get("status") == "verified"
        ]
        expected_pull_request_evidence = [
            item for item in finalization
            if item.get("kind") in {"pull-request", "pr-watch", "merge-read-back"} and item.get("status") == "verified"
        ]
        if value["repository_evidence"] != expected_repository_evidence or value["pull_request_evidence"] != expected_pull_request_evidence:
            raise TriageError("finalization evidence accounting mismatch", outcome="operator-held")
    elif value["repository_evidence"] or value["pull_request_evidence"]:
        raise TriageError("forge evidence exists before finalization", outcome="operator-held")
    completion = value.get("completion")
    if completion is not None:
        # `sweep_cleanup` (#807) sits beside `receipt_core`, never inside it, so a
        # completed state written before it existed keeps its exact receipt digest
        # and still validates without the key.
        completion_keys = {"route", "outcome", "receipt_core", "completed_receipt_digest"}
        if isinstance(completion, dict) and "sweep_cleanup" in completion:
            completion_keys = completion_keys | {"sweep_cleanup"}
        if not isinstance(completion, dict) or set(completion) != completion_keys or digest(completion.get("receipt_core")) != completion.get("completed_receipt_digest"):
            raise TriageError("completed receipt digest mismatch", outcome="operator-held")
        if "sweep_cleanup" in completion and completion.get("route") != "archive-sweep":
            raise TriageError("sweep cleanup recorded outside an archive-sweep completion", outcome="operator-held")
        _validate_sweep_cleanup(completion.get("sweep_cleanup"))
        receipt = completion["receipt_core"]
        if not isinstance(receipt, dict) or receipt.get("route") != completion["route"] or receipt.get("outcome") != completion["outcome"] or receipt.get("run_identity") != identity or receipt.get("frozen_inbox_digest") != value["frozen_inbox_digest"]:
            raise TriageError("completed receipt authority mismatch", outcome="operator-held")
        route = completion["route"]
        if route == "no-op":
            if frozen["content"].get("candidate_index") != []:
                raise TriageError("no-op receipt contradicts the frozen candidate index", outcome="operator-held")
            expected = {
                "route": route, "outcome": "successful-completion",
                "run_identity": identity,
                "frozen_inbox_digest": value["frozen_inbox_digest"],
                "candidate_index": [],
            }
            if receipt != expected:
                raise TriageError("no-op receipt authority mismatch", outcome="operator-held")
        elif route == "decision-only":
            expected = {
                "route": route, "outcome": completion["outcome"],
                "run_identity": identity,
                "frozen_inbox_digest": value["frozen_inbox_digest"],
                "proposal_payloads": value["proposal_payloads"],
                "approval": value["approval"], "decisions": value["decisions"],
                "operations": [], "attempts": [],
            }
            if not isinstance(completion["outcome"], str) or completion["outcome"] not in {"degraded-success", "successful-completion"} or receipt != expected:
                raise TriageError("decision-only receipt authority mismatch", outcome="operator-held")
        elif route == "test-render":
            expected = {
                "route": route, "outcome": completion["outcome"],
                "run_identity": identity,
                "frozen_inbox_digest": value["frozen_inbox_digest"],
                "proposal_payloads": value["proposal_payloads"],
                "approval": value["approval"], "decisions": value["decisions"],
                "operations": value["operations"], "attempts": [],
                "proposed_diff": receipt.get("proposed_diff"),
            }
            if (
                not isinstance(completion["outcome"], str)
                or completion["outcome"] not in {"degraded-success", "successful-completion"}
                or not isinstance(receipt.get("proposed_diff"), str)
                or receipt != expected
            ):
                raise TriageError("test-render receipt authority mismatch", outcome="operator-held")
        elif route == "archive-sweep":
            final_order = ["branch-create", "commit", "push", "pull-request", "pr-watch", "merge-read-back"]
            if (
                not isinstance(finalization, list)
                or [item.get("kind") for item in finalization] != final_order
                or any(item.get("status") != "verified" for item in finalization)
            ):
                raise TriageError("archive completion lacks a verified finalization chain", outcome="operator-held")
            branch_read_back = finalization[0]["read_back"]
            push_read_back = finalization[2]["read_back"]
            review_read_back = finalization[4]["read_back"]
            expected_archive = {
                "repository": branch_read_back["repository"],
                "base": settings.protected_branch,
                "branch": branch_read_back["branch"],
                "commit": push_read_back["remote_head"],
                "pr": review_read_back["url"],
                "observed_head": review_read_back["headRefOid"],
                "reviewed_head": review_read_back["reviewed_head"],
                "pr_watch_receipt": review_read_back["receipt"],
            }
            if value.get("archive_sweep") != expected_archive:
                raise TriageError("archive summary does not derive from finalization evidence", outcome="operator-held")
            merge_read_back = finalization[-1].get("read_back") if finalization else None
            expected = {
                "route": route, "outcome": completion["outcome"],
                "run_identity": identity,
                "frozen_inbox_digest": value["frozen_inbox_digest"],
                "tracker_operations": value["operations"],
                "finalization_operations": value["finalization_operations"],
                "archive_sweep": value["archive_sweep"],
                "merge_read_back": merge_read_back,
            }
            expected_outcome = (
                "degraded-success"
                if value.get("notification_thread_reference") is None
                and value.get("notification_operations") == []
                else "successful-completion"
            )
            if completion["outcome"] != expected_outcome or receipt != expected:
                raise TriageError("archive completion receipt authority mismatch", outcome="operator-held")
        else:
            raise TriageError("completed receipt route is invalid", outcome="operator-held")
    return value


def _forge_read_back_matches(kind: str, intent: dict[str, Any], read_back: Any) -> bool:
    if not isinstance(read_back, dict):
        return False
    if kind == "branch-create":
        return (
            read_back.get("repository") == intent.get("repository")
            and read_back.get("branch") == intent.get("branch")
            and read_back.get("worktree") == intent.get("worktree")
            and read_back.get("head") == read_back.get("base") == intent.get("finalize_base_head")
        )
    if kind == "commit":
        authority = intent.get("authority_read_back")
        return (
            isinstance(authority, dict)
            and read_back.get("repository") == intent.get("repository")
            and read_back.get("branch") == intent.get("branch")
            and read_back.get("base") == intent.get("base")
            and read_back.get("worktree") == intent.get("worktree")
            and read_back.get("subject") == intent.get("subject")
            and read_back.get("paths") == intent.get("paths")
            and read_back.get("tree") == authority.get("staged_tree")
        )
    if kind == "push":
        return (
            read_back.get("repository") == intent.get("repository")
            and read_back.get("branch") == intent.get("branch")
            and read_back.get("remote_head") == intent.get("commit")
            and read_back.get("tree") == intent.get("tree")
        )
    if kind == "pull-request":
        return (
            read_back.get("baseRefName") == intent.get("base_branch")
            and read_back.get("headRefName") == intent.get("branch")
            and read_back.get("headRefOid") == intent.get("head")
            and read_back.get("isDraft") is False
            and read_back.get("files") == intent.get("paths")
        )
    if kind == "pr-watch":
        return (
            read_back.get("url") == intent.get("pr")
            and read_back.get("baseRefName") == intent.get("base_branch")
            and read_back.get("headRefOid") == intent.get("head")
            and read_back.get("reviewed_head") == intent.get("head")
            and terminal_pr_watch_receipt(
                read_back.get("receipt"), head=intent.get("head"), url=intent.get("pr")
            )
        )
    if kind == "merge-read-back":
        return (
            read_back.get("url") == intent.get("pr")
            and read_back.get("baseRefName") == intent.get("base")
            and read_back.get("headRefOid") == intent.get("reviewed_head")
            and read_back.get("merged") is True
        )
    return False


def _forge_predecessor_matches(
    read_back: Any, kind: str, intent: dict[str, Any]
) -> bool:
    if not isinstance(read_back, dict):
        return False
    if kind == "commit":
        return (
            all(intent.get(name) == read_back.get(name) for name in ("repository", "branch", "worktree"))
            and intent.get("base") == read_back.get("head")
        )
    if kind == "push":
        return (
            all(intent.get(name) == read_back.get(name) for name in ("repository", "branch", "worktree", "tree"))
            and intent.get("commit") == read_back.get("commit")
        )
    if kind == "pull-request":
        return (
            intent.get("repository") == read_back.get("repository")
            and intent.get("branch") == read_back.get("branch")
            and intent.get("head") == read_back.get("remote_head")
        )
    if kind == "pr-watch":
        return (
            intent.get("head") == read_back.get("headRefOid")
            and intent.get("pr") == read_back.get("url")
        )
    if kind == "merge-read-back":
        return (
            intent.get("reviewed_head") == read_back.get("reviewed_head")
            and intent.get("pr") == read_back.get("url")
        )
    return False


def canonical_state(raw: bytes, *, settings: Settings, mode: str) -> dict[str, Any]:
    try:
        value = loads_exact(raw)
    except CanonicalError as exc:
        raise TriageError(str(exc), outcome="operator-held") from exc
    return validate_state(value, settings=settings, mode=mode)


def today_string() -> str:
    return date.today().isoformat()
