## Adapter report: Codex invocation policy

CHANGED (report / return shape): accept Codex `agents/openai.yaml` rows for `adopt`,
`upgrade` and `triage-friction-log`, including the new `policy-stale` state. Run
`kit_doctor.py --adapter-report` through `uv run` to provide its declared PyYAML
dependency. Other doctor modes and adapter rendering retain their bare-Python route.

For these rows, `kit-current` confirms an unambiguous, explicit YAML boolean
`policy.allow_implicit_invocation: false`; it does not classify the other keys as
kit-owned. Take the kit's file for `missing`. For `policy-stale`, inspect and reconcile
the setting while preserving adopter edits, or take the kit's file when its other
keys are appropriate. Differing, duplicate, malformed and merge-inherited settings
are not confirmed. A quoted `"false"` is a string. Unsafe or unreadable files remain
`adopter-owned`; inspect them without overwriting them automatically.
