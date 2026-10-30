## A triage state carrying `proposal_correction` is held, no longer retired

CHANGED (gate semantics): the triage engine no longer accepts a `proposal_correction`
receipt on a completed LIVE state (#1305). The removed `correct-project` route (#975)
wrote that receipt, and the engine kept parsing it only so that such a state could still
be retired. A state that carries one now fails validation as any state with an extra
field does: `triage state has missing or extra phase fields`, outcome `operator-held`.
A session-starting entry holds it in place rather than retiring it.

Before you refresh `scripts/lib/triage/`, check that no triage state file under your
state root holds a `proposal_correction` field. If one does, let a session-starting run
of the current engine retire it first, or delete it with the operator's approval. Then
refresh `scripts/lib/triage/` and its tests. If you assert that a completed state with
the receipt retires, expect the refusal instead.
