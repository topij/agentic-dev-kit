## Triage `recover`: a stale gate over a completed state no longer holds it after a config change

CHANGED (gate semantics): `recover` behind a gate whose owner is proven dead now
preserves a `completed` state that is valid except that it was written under an earlier
configuration, and quarantines the gate (`preserve-valid-state-and-quarantine-old-gate`).
The next session-starting entry then retires the state. Before, the action plan
captured that state as a terminal `state-present-held` bundle with no way out.

Nothing to change in your configuration. After a successful preserve, a completed
state's result now reports `start-new-session` instead of `resume`, and `recover`'s
`captured state is valid; recovery refused` names a session-starting entry for a completed
state. `resume` never retires a completed state, so run triage with no entry or with
`new`. If you match on the old `resume` detail for this case, expect the new value.

A `state-present-held` bundle captured before this change is not re-planned. While the
gate it is keyed to is present, `recover` reports the retained evidence and every
session-starting entry refuses on the gate; the engine offers no route out yet (#1282).
If that gate is already gone, as after an earlier quarantine, the bundle blocks nothing,
and a session-starting entry retires the completed state.
