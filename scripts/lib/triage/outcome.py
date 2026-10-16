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

from typing import Any

from .model import REFUSAL_CODES

COMPLETED_OUTCOMES = ("successful-completion", "degraded-success")
DISPOSITIONS = ("completed", "waiting", "refused")
# What a `waiting` result waits on. `analysis`: an interactive resume supplies
# proposals for the reserved snapshot. `notification-delivery`: a resume reads
# back the retained notification attempt. `approval`: the operator's exact
# approval. `tracker-write`: a resume with the tracker adapter selected.
# `finalize`: a resume carrying `finalize: true`. `recovery-approval`: the exact
# approval of a recorded recovery plan. `rerun`: an applied recovery transition
# left state that the next ordinary run resumes or restarts from.
# `reconciliation`: a retained tracker or forge write that read-back left
# unresolved; a rerun reads it back again, and advances only once the provider
# shows it resolved, which may need the operator (a duplicate removed, say).
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
