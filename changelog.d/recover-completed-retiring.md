## Triage `recover`: a stale gate over a completed state no longer holds it after a config change

CHANGED (gate semantics): `recover` behind a gate whose owner is proven dead now
preserves a `completed` state that is valid except that it was written under an earlier
configuration, and quarantines the gate (`preserve-valid-state-and-quarantine-old-gate`).
The next session-starting entry then retires the state. Before, the action plan
captured that state as a terminal `state-present-held` bundle with no way out.

Nothing to change in your configuration. A `state-present-held` bundle captured before
this change stays where it is. It blocks only while a gate with the digest it is keyed
to is present. Once that gate has been quarantined, a session-starting triage entry
retires the completed state.
