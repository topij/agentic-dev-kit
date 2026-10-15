"""Deterministic invocation outcomes for automated callers (#1103).

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

An outer wrapper whose own exit status does not come from the CLI (a scheduled
agent run, for one) asks the CLI for an invocation-bound receipt instead: the
wrapper picks a fresh invocation id, passes it with a receipt path, and checks
the receipt afterwards with `check_receipt`. Missing, stale, malformed and
wrong-invocation receipts each have their own verdict, and none of them reads as
success.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import CanonicalError, digest, dumps, loads_exact
from .model import REFUSAL_CODES, TOKEN_RE, TriageError
from .storage import atomic_replace, observe

COMPLETED_OUTCOMES = ("successful-completion", "degraded-success")
DISPOSITIONS = ("completed", "waiting", "refused")
# What a `waiting` result waits on. `analysis`: an interactive resume supplies
# proposals for the reserved snapshot. `notification-delivery`: a resume reads
# back the retained notification attempt. `approval`: the operator's exact
# approval. `tracker-write`: a resume with the tracker adapter selected.
# `finalize`: a resume carrying `finalize: true`. `recovery-approval`: the exact
# approval of a recorded recovery plan. `rerun`: an applied recovery transition
# left state that the next ordinary run resumes or restarts from.
WAITING_ON = (
    "analysis",
    "notification-delivery",
    "approval",
    "tracker-write",
    "finalize",
    "recovery-approval",
    "rerun",
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

RECEIPT_KIND = "triage-invocation-outcome"
RECEIPT_KEYS = {
    "kind", "schema_version", "invocation_id", "sequence", "entry", "context", "mode",
    "outcome", "disposition", "waiting_on", "refusal_code", "result", "result_digest",
}
# A receipt check's verdicts. The first three describe a valid receipt bound to
# the expected invocation; every `evidence-*` verdict means the caller has no
# outcome for its invocation and must treat the run as failed.
VERDICTS = (
    "completed",
    "waiting",
    "refused",
    "evidence-missing",
    "evidence-malformed",
    "evidence-stale",
    "evidence-wrong-invocation",
)


def disposition_fields(outcome: str, *, waiting_on: str | None = None, refusal_code: str | None = None) -> dict[str, Any]:
    """The three disposition keys for a result with this outcome."""
    if outcome in COMPLETED_OUTCOMES:
        return {"disposition": "completed", "waiting_on": None, "refusal_code": None}
    if outcome == "operator-held" and waiting_on in WAITING_ON:
        return {"disposition": "waiting", "waiting_on": waiting_on, "refusal_code": None}
    code = refusal_code if refusal_code in REFUSAL_CODES else "unclassified"
    return {"disposition": "refused", "waiting_on": None, "refusal_code": code}


def _consistent(fields: dict[str, Any], outcome: Any) -> bool:
    return isinstance(outcome, str) and fields == disposition_fields(
        outcome, waiting_on=fields.get("waiting_on"), refusal_code=fields.get("refusal_code")
    )


def _invocation_id_error(invocation_id: Any) -> str | None:
    if not isinstance(invocation_id, str) or not TOKEN_RE.fullmatch(invocation_id):
        return "invocation id must match [A-Za-z0-9][A-Za-z0-9_-]{0,127}"
    return None


def receipt_path_error(path: Path | None, invocation_id: str | None) -> str | None:
    """Why a receipt request cannot be honoured, or None. Both or neither."""
    if path is None and invocation_id is None:
        return None
    if path is None or invocation_id is None:
        return "an outcome receipt needs both a receipt path and an invocation id"
    if not path.is_absolute():
        return "outcome receipt path must be absolute"
    return _invocation_id_error(invocation_id)


def write_receipt(path: Path, result: dict[str, Any], *, invocation_id: str, entry: str | None, context: str | None) -> dict[str, Any]:
    """Publish the receipt for one CLI invocation, replacing any earlier one.

    An agent run may call the CLI more than once under one invocation id (a
    freeze, then an analysis resume), so the receipt is replaced rather than
    created exclusively, and `sequence` counts the calls under that id. The last
    call's receipt is the invocation's outcome."""
    _, previous_raw = observe(path)
    sequence = 1
    if previous_raw is not None:
        try:
            previous = loads_exact(previous_raw)
        except CanonicalError:
            previous = None
        if (
            isinstance(previous, dict)
            and previous.get("kind") == RECEIPT_KIND
            and previous.get("invocation_id") == invocation_id
            and isinstance(previous.get("sequence"), int)
            and not isinstance(previous.get("sequence"), bool)
            and previous["sequence"] >= 1
        ):
            sequence = previous["sequence"] + 1
    receipt = {
        "kind": RECEIPT_KIND,
        "schema_version": 1,
        "invocation_id": invocation_id,
        "sequence": sequence,
        "entry": entry,
        "context": context,
        "mode": result.get("execution_mode"),
        "outcome": result.get("outcome"),
        "disposition": result.get("disposition"),
        "waiting_on": result.get("waiting_on"),
        "refusal_code": result.get("refusal_code"),
        "result": result,
        "result_digest": digest(result),
    }
    atomic_replace(path, dumps(receipt))
    return receipt


def check_receipt(
    path: Path,
    *,
    invocation_id: str,
    context: str | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    """Classify the receipt at `path` for the invocation the caller started.

    `context` and `mode`, when given, are what the caller invoked; a receipt
    for the right invocation id that records another is `evidence-wrong-invocation`.
    A receipt for another invocation id is `evidence-stale`: an earlier run left
    it and this run wrote none."""
    def verdict(name: str, detail: str, receipt: dict[str, Any] | None = None) -> dict[str, Any]:
        bound = receipt if name in {"completed", "waiting", "refused"} else None
        return {
            "kind": "triage-invocation-outcome-check",
            "verdict": name,
            "invocation_id": invocation_id,
            "sequence": bound["sequence"] if bound else None,
            "outcome": bound["outcome"] if bound else None,
            "disposition": bound["disposition"] if bound else None,
            "waiting_on": bound["waiting_on"] if bound else None,
            "refusal_code": bound["refusal_code"] if bound else None,
            "detail": detail,
        }

    if _invocation_id_error(invocation_id) is not None:
        raise TriageError(_invocation_id_error(invocation_id) or "", code="invalid-invocation")
    try:
        _, raw = observe(path)
    except (OSError, TriageError) as exc:
        return verdict("evidence-malformed", f"receipt cannot be read safely: {exc}")
    if raw is None:
        return verdict("evidence-missing", "no receipt exists at the receipt path")
    try:
        receipt = loads_exact(raw)
    except CanonicalError as exc:
        return verdict("evidence-malformed", f"receipt is not canonical JSON: {exc}")
    if (
        not isinstance(receipt, dict)
        or set(receipt) != RECEIPT_KEYS
        or receipt.get("kind") != RECEIPT_KIND
        or receipt.get("schema_version") != 1
        or isinstance(receipt.get("schema_version"), bool)
        or not isinstance(receipt.get("result"), dict)
        or receipt.get("result_digest") != digest(receipt["result"])
        or isinstance(receipt.get("sequence"), bool)
        or not isinstance(receipt.get("sequence"), int)
        or receipt["sequence"] < 1
        or _invocation_id_error(receipt.get("invocation_id")) is not None
    ):
        return verdict("evidence-malformed", "receipt shape, kind or result digest is invalid")
    result = receipt["result"]
    fields = {name: receipt[name] for name in ("disposition", "waiting_on", "refusal_code")}
    if (
        any(result.get(name) != receipt[name] for name in ("outcome", "disposition", "waiting_on", "refusal_code"))
        or result.get("execution_mode") != receipt["mode"]
        or not _consistent(fields, receipt["outcome"])
    ):
        return verdict("evidence-malformed", "receipt fields disagree with its result or with each other")
    if receipt["invocation_id"] != invocation_id:
        return verdict("evidence-stale", "receipt belongs to another invocation")
    if (context is not None and receipt["context"] != context) or (mode is not None and receipt["mode"] != mode):
        return verdict("evidence-wrong-invocation", "receipt records another context or mode than the caller invoked")
    return verdict(receipt["disposition"], f"call {receipt['sequence']} under this invocation", receipt)
