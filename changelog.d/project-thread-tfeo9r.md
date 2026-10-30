## A triage state carrying `proposal_correction` is held, no longer retired

BREAKING (gate semantics): the triage engine no longer accepts a `proposal_correction`
receipt on a completed LIVE state (#1305). The removed `correct-project` route (#975)
wrote that receipt, and the engine kept parsing it only so that such a state could still
be retired. A state that carries one now fails validation as any state with an extra
field does: `triage state has missing or extra phase fields`, outcome `operator-held`.
A session-starting entry holds it in place rather than retiring it.

Before you refresh `scripts/lib/triage/`, check that no triage state file under your
state root holds a `proposal_correction` field. If one does, let a session-starting run
of the engine you have now retire it, or delete the file with the operator's approval,
before you refresh. Do not run `recover` on such a state after refreshing: it ends in a
terminal `external-attempt-absence-unproven` hold that leaves the single-writer gate and
a recovery bundle behind, and every later entry then stops on the held gate. Refresh `scripts/lib/triage/` and its
tests together. If you assert that a completed state with the receipt retires, expect
the refusal instead.
