"""Explicit recovery of the historical flat gate and pre-freeze reservation.

Historical timestamps are observations, never OS process-start identities. An
operator's machine attestation and a negative process probe are separate evidence.
Nothing here constructs a modern lease or imports historical approval authority.
"""

from __future__ import annotations

import json
import math
import os
import socket
import subprocess
from typing import Any

from .approval import ApprovalContext
from .canonical import digest_bytes, dumps
from .model import (
    BASE_KEYS,
    OID_RE,
    SHA256_RE,
    TOKEN_RE,
    TriageError,
    git_output,
    repository_identity,
)


def _held(detail: str) -> TriageError:
    return TriageError(detail, outcome="operator-held")


def historical_json(raw: bytes) -> dict[str, Any]:
    """Decode historical JSON without normalizing its retained source bytes."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
        dumps(value)  # Reject non-finite, non-interoperable and malformed scalars.
    except (ValueError, UnicodeError) as exc:
        raise _held("historical gate/state JSON is malformed") from exc
    if not isinstance(value, dict):
        raise _held("historical gate/state root is not an object")
    return value


def read_gate(store: Any, raw: bytes, context: ApprovalContext, *, check_owner: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    record = historical_json(raw)
    expected = {"created_at", "host", "owner_token", "pid", "process_start_observation", "run_identity"}
    if set(record) != expected:
        raise _held("unsupported historical gate shape")
    if not isinstance(record["owner_token"], str) or not TOKEN_RE.fullmatch(record["owner_token"]):
        raise _held("historical gate token is malformed")
    pid = record["pid"]
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise _held("historical gate PID is malformed")
    if not isinstance(record["host"], str) or not record["host"]:
        raise _held("historical gate host is malformed")
    for key in ("created_at", "process_start_observation"):
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise _held("historical gate timestamp is malformed")
    identity = record["run_identity"]
    identity_keys = {"repository_identity", "friction_log", "protected_branch_head", "mode", "session", "config_fingerprint"}
    if not isinstance(identity, dict) or set(identity) != identity_keys:
        raise _held("historical gate run identity is malformed")
    head = identity["protected_branch_head"]
    if not isinstance(head, str) or not OID_RE.fullmatch(head):
        raise _held("historical gate draft head is malformed")
    repo = repository_identity(store.settings)
    if identity["repository_identity"] != repo["remote"] + "#" + head or identity["mode"] != store.mode:
        raise _held("historical gate belongs to another repository or mode")
    if identity["friction_log"] != str(store.settings.paths.friction_log.relative_to(store.settings.paths.repo)):
        raise _held("historical gate friction-log identity is foreign")
    if not isinstance(identity["session"], str) or not TOKEN_RE.fullmatch(identity["session"]):
        raise _held("historical gate session is malformed")
    if not isinstance(identity["config_fingerprint"], str) or not SHA256_RE.fullmatch(identity["config_fingerprint"]):
        raise _held("historical gate configuration identity is malformed")
    readback = context.source_read_back if isinstance(context, ApprovalContext) else None
    if (
        not isinstance(context, ApprovalContext)
        or context.source != "current-session"
        or not isinstance(context.operator_identity, str) or not context.operator_identity
        or not isinstance(readback, dict)
        or readback.get("approver_identity") != context.operator_identity
        or not isinstance(readback.get("text"), str) or not readback["text"]
    ):
        raise _held("historical gate needs trusted current-session owner evidence")
    attestation = readback.get("legacy_gate_owner")
    expected_attestation = {
        "gate_digest": digest_bytes(raw), "recorded_host": record["host"],
        "recorded_pid": pid, "local_host": socket.gethostname(),
        "same_machine": True, "owner_terminated": True,
    }
    if (
        attestation != expected_attestation or not isinstance(attestation, dict)
        or attestation.get("same_machine") is not True or attestation.get("owner_terminated") is not True
        or type(attestation.get("recorded_pid")) is not int
    ):
        raise _held("historical gate machine attestation is missing or does not bind the capture")
    if check_owner:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except (PermissionError, OSError) as exc:
            raise _held("historical gate process observation is uncertain") from exc
        else:
            raise _held("historical gate PID is active or reused")
    ref = f"refs/heads/{store.settings.protected_branch}"
    try:
        remote_line = git_output(store.settings.paths.repo, "ls-remote", "--exit-code", "origin", ref)
        parts = remote_line.split("\t")
        if len(parts) != 2 or parts[1] != ref or not OID_RE.fullmatch(parts[0]):
            raise _held("historical gate protected head is unverifiable")
        observed_head = parts[0]
        local_head = git_output(store.settings.paths.repo, "rev-parse", f"refs/remotes/origin/{store.settings.protected_branch}")
        if local_head != observed_head:
            raise _held("refresh the protected ref before historical gate recovery")
        ancestor = subprocess.run(
            ["git", "-C", str(store.settings.paths.repo), "merge-base", "--is-ancestor", head, observed_head],
            capture_output=True, check=False,
        )
        if ancestor.returncode:
            raise _held("historical gate draft head is not a verified protected ancestor")
    except TriageError as exc:
        raise _held(str(exc)) from exc
    evidence = {
        "source": context.source, "operator_identity": context.operator_identity,
        "source_read_back": readback, "gate_digest": digest_bytes(raw),
        "observed_protected_head": observed_head,
        "original_config_fingerprint": identity["config_fingerprint"],
        "current_config_fingerprint": store.settings.fingerprint,
        "process_probe": "os.kill(pid, 0): ProcessLookupError",
    }
    return record, evidence


def prefreeze_reservation(store: Any, raw: bytes, gate: dict[str, Any]) -> bool:
    """Recognize only the exact historical reservation before frozen input existed.

The old gate binding digest is retained as a claim, never used as modern lease
authority. The complete capture and this classification must be approved separately.
"""
    try:
        state = historical_json(raw)
    except TriageError:
        return False
    if (
        set(state) != BASE_KEYS or state.get("kind") != "triage-run-state"
        or isinstance(state.get("schema_version"), bool) or state.get("schema_version") != 1
        or state.get("phase") != "reserved" or state.get("engine_mode") != "llm-only"
        or state.get("mode") != store.mode or state.get("run_identity") != gate["run_identity"]
        or state.get("config_fingerprint") != gate["run_identity"]["config_fingerprint"]
        or state.get("gate_owner_token") != gate["owner_token"]
        or state.get("frozen_snapshot") is not None or state.get("frozen_inbox_digest") is not None
        or any(state.get(name) != [] for name in ("attempts", "verified_tracker_identifiers", "repository_evidence", "pull_request_evidence"))
    ):
        return False
    binding = state.get("gate_binding")
    if (
        not isinstance(binding, dict)
        or set(binding) != {"gate_path", "owner_token", "owner_run_identity", "gate_claim_core_digest"}
        or binding.get("gate_path") != store.settings.paths.gate_fragment.replace("{mode}", store.mode)
        or binding.get("owner_token") != gate["owner_token"]
        or binding.get("owner_run_identity") != gate["run_identity"]
        or not isinstance(binding.get("gate_claim_core_digest"), str)
        or not SHA256_RE.fullmatch(binding["gate_claim_core_digest"])
    ):
        return False
    return state.get("state_claim") == {
        "reason": "initial-reservation", "previous_gate_binding": None,
        "current_gate_binding": binding, "captured_state_digest": None,
        "recovery_bundle_digest": None, "approval_digest": None,
    }
