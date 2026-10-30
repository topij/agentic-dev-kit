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
before you refresh. Refresh `scripts/lib/triage/` and its tests together. If you assert
that a completed state with the receipt retires, expect the refusal instead.

If you refreshed first, no engine entry retires such a state: delete the file with the
operator's approval. Do not run `recover` on it. For most such states `recover` ends in
an `external-attempt-absence-unproven` hold that leaves the single-writer gate lock and
a recovery bundle behind, after which every entry stops on the held gate. If that has
already happened, deleting the state no longer clears the hold: the gate lock and the
bundle have to go too, again with the operator's approval.
