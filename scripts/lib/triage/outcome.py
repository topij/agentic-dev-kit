"""Deterministic result dispositions for automated callers (#1103).

`outcome` alone cannot drive a scheduled caller: `operator-held` is both the
legitimate wait for an operator's approval and a refusal such as a repository
identity mismatch, and the CLI exits 0 for both. Every result therefore also
carries:

- `disposition` — `completed`, `waiting` or `refused`;
- `waiting_on` — for `waiting` only, what continues the run;
- `refusal_code` — for `refused` only, a value from `REFUSAL_CODES`.

The disposition is derived, never chosen freely: a completed or degraded outcome
is `completed`, and `operator-held` is `waiting` only where the engine names
what it waits on. Every other result — a hard stop, or an `operator-held` no site
classified — is `refused`. A new return path is therefore a refusal until someone
decides otherwise.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .canonical import CanonicalError, digest, dumps, loads_exact
from .model import REFUSAL_CODES, TOKEN_RE, TriageError
from .storage import exclusive_create, observe

COMPLETED_OUTCOMES = ("successful-completion", "degraded-success")
DISPOSITIONS = ("completed", "waiting", "refused")
# What a `waiting` result waits on. `analysis`: an interactive resume supplies
# proposals for the reserved snapshot. `notification-delivery`: a resume reads
# back the retained notification attempt. `approval`: the operator's exact
# approval. `tracker-write`: a resume with the tracker adapter selected.
# `finalize`: a resume carrying `finalize: true`. `recovery-approval`: the exact
# approval of a recorded recovery plan. `rerun`: an applied recovery transition
# left state that the next ordinary run resumes or restarts from.
# `reconciliation`: the last retained tracker or forge write is unverified. A
# tracker write is read back on each rerun and advances once the tracker shows
# exactly the recorded write, which may need the operator (a duplicate removed,
# say). A forge write is not read back again, so no rerun advances it, except a
# failed branch-create that read-back proves left nothing.
WAITING_ON = (
    "analysis",
    "notification-delivery",
    "approval",
    "tracker-write",
    "finalize",
    "recovery-approval",
    "rerun",
    "reconciliation",
)
# The phase an active session rests in, mapped to what continues it. `propose`
# and `completed` are absent on purpose: a session resting in `propose` (an
# unattended draft with no notification provider) has no continuation, and a
# completed session is not waiting.
PHASE_WAITING_ON = {
    "reserved": "analysis",
    "notification-delivery": "notification-delivery",
    "awaiting-approval": "approval",
    "tracker-write": "tracker-write",
    "forge-finalize": "finalize",
    "archive-sweep": "finalize",
}
# Forge operations whose unsettled read-back the next finalize run polls again;
# any other unverified forge operation waits on reconciliation.
_FORGE_POLLED = ("pr-watch", "merge-read-back")


def session_waiting_on(state: dict[str, Any]) -> str | None:
    """What continues an active session: its phase's wait, unless the last
    retained tracker or forge write is unverified. The phase alone would report
    an ambiguous tracker create as `tracker-write` on every run, a wait no
    adapter selection ends."""
    phase = state.get("phase")
    if phase == "tracker-write":
        operations = state.get("operations") or []
        if operations and operations[-1].get("status") != "verified":
            return "reconciliation"
    if phase == "forge-finalize":
        operations = state.get("finalization_operations") or []
        if operations and operations[-1].get("status") != "verified" and not (
            operations[-1].get("status") == "unsettled" and operations[-1].get("kind") in _FORGE_POLLED
        ):
            return "reconciliation"
    return PHASE_WAITING_ON.get(phase)


def disposition_fields(outcome: str, *, waiting_on: str | None = None, refusal_code: str | None = None) -> dict[str, Any]:
    """The three disposition keys for a result with this outcome."""
    if outcome in COMPLETED_OUTCOMES:
        return {"disposition": "completed", "waiting_on": None, "refusal_code": None}
    if outcome == "operator-held" and waiting_on in WAITING_ON:
        return {"disposition": "waiting", "waiting_on": waiting_on, "refusal_code": None}
    code = refusal_code if refusal_code in REFUSAL_CODES else "unclassified"
    return {"disposition": "refused", "waiting_on": None, "refusal_code": code}


RECEIPT_KIND = "triage-invocation-outcome"
RECEIPT_KEYS = {"kind", "schema_version", "invocation_id", "entry", "context", "result", "result_digest"}
ENTRIES = (None, "resume", "new", "recover", "test")
CONTEXTS = ("interactive", "unattended")


def validate_receipt_target(path: Path, invocation_id: str) -> None:
    """Validate caller-supplied identity and an absolute, lexically normalized path."""
    if not path.is_absolute() or ".." in path.parts:
        raise TriageError("outcome receipt path must be absolute without '..'", code="invalid-invocation")
    if not isinstance(invocation_id, str) or not TOKEN_RE.fullmatch(invocation_id):
        raise TriageError("invocation id must match [A-Za-z0-9][A-Za-z0-9_-]{0,127}", code="invalid-invocation")


def preflight_receipt(path: Path, invocation_id: str) -> None:
    """Refuse an occupied destination before running the engine; never clear it.

    Freshness belongs to the caller: allocate a new id AND path for every CLI
    call, before launching it. No cleanup here can make reuse safe after a call
    that fails before parsing its flags or cannot write the destination.
    """
    validate_receipt_target(path, invocation_id)
    if observe(path, read=False)[0].exists:
        raise TriageError("outcome receipt destination already exists; allocate a fresh invocation", code="invalid-invocation")
    if not path.parent.is_dir():
        raise TriageError("outcome receipt parent must already exist", code="invalid-invocation")


def write_receipt(path: Path, result: dict[str, Any], *, invocation_id: str, entry: str | None, context: str) -> None:
    """Publish once without replacing any file, including a prior receipt.

    The random staging basename disables exclusive_create's deterministic
    interrupted-publication recovery: an invocation outcome is never resumed.
    """
    receipt = {
        "kind": RECEIPT_KIND,
        "schema_version": 1,
        "invocation_id": invocation_id,
        "entry": entry,
        "context": context,
        "result": result,
        "result_digest": digest(result),
    }
    exclusive_create(path, dumps(receipt), temporary_name=f".{path.name}.{uuid.uuid4().hex}.tmp")


def _valid_receipt(receipt: Any) -> bool:
    if (
        not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS
        or receipt["kind"] != RECEIPT_KIND or type(receipt["schema_version"]) is not int
        or receipt["schema_version"] != 1 or receipt["entry"] not in ENTRIES
        or receipt["context"] not in CONTEXTS or not isinstance(receipt["invocation_id"], str)
        or not TOKEN_RE.fullmatch(receipt["invocation_id"]) or not isinstance(receipt["result"], dict)
        or receipt["result_digest"] != digest(receipt["result"])
    ):
        return False
    result = receipt["result"]
    if not {"outcome", "execution_mode", "disposition", "waiting_on", "refusal_code"} <= result.keys():
        return False
    outcome = result.get("outcome")
    if outcome not in (*COMPLETED_OUTCOMES, "operator-held", "hard-stop"):
        return False
    fields = {key: result.get(key) for key in ("disposition", "waiting_on", "refusal_code")}
    if fields != disposition_fields(outcome, waiting_on=fields["waiting_on"], refusal_code=fields["refusal_code"]):
        return False
    # Only a refusal can precede mode discovery; completion or waiting with an
    # unknown mode is malformed, not an exemption from the caller's expectation.
    return result.get("execution_mode") in ("live", "test") or (
        fields["disposition"] == "refused" and result.get("execution_mode") == "unknown"
    )


def check_receipt(path: Path, *, invocation_id: str, entry: str | None, context: str, mode: str) -> dict[str, Any]:
    """Read-only evidence classification for a caller's fresh per-call identity.

    This is integrity and correlation, not authentication of a writer with the
    same filesystem access. The caller owns a private destination and retains
    its expected identity outside agent-authored output. It checks after the
    invoked process exits, and also requires that process to exit successfully.
    """
    validate_receipt_target(path, invocation_id)
    if entry not in ENTRIES or context not in CONTEXTS or mode not in ("live", "test"):
        raise TriageError("invalid expected invocation", code="invalid-invocation")

    def verdict(name: str, detail: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "kind": "triage-invocation-outcome-check", "verdict": name,
            "invocation_id": invocation_id, "detail": detail,
            **{key: result.get(key) if result else None for key in ("outcome", "disposition", "waiting_on", "refusal_code")},
        }

    try:
        _, raw = observe(path)
        if raw is None:
            return verdict("evidence-missing", "no receipt exists at the expected path")
        receipt = loads_exact(raw)
        if not _valid_receipt(receipt):
            return verdict("evidence-malformed", "receipt shape, digest or disposition is invalid")
    except (OSError, TriageError, CanonicalError, RecursionError) as exc:
        return verdict("evidence-malformed", f"receipt cannot be read safely: {exc}")
    if receipt["invocation_id"] != invocation_id:
        return verdict("evidence-stale", "receipt belongs to another invocation")
    result = receipt["result"]
    if receipt["entry"] != entry or receipt["context"] != context or (
        result["execution_mode"] != mode and result["execution_mode"] != "unknown"
    ):
        return verdict("evidence-wrong-invocation", "receipt records another entry, context or mode")
    return verdict(result["disposition"], "receipt matches the expected invocation", result)
