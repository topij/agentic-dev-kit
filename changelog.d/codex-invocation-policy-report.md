## Adapter report: the Codex invocation policy of the explicit-only skills

CHANGED (report / return shape): `kit_doctor.py --adapter-report` now adds a codex row
for `.agents/skills/<slug>/agents/openai.yaml` for each of `adopt`, `upgrade` and
`triage-friction-log`. The row checks one key, the top-level
`policy.allow_implicit_invocation: false` block. It does not judge the file's other
keys. The row is `kit-current` when the file sets that key, `missing` when there is no
file, and the new state `policy-stale` when the file exists but does not set it, so
Codex still loads the skill unasked. A file at an unsafe path or one that cannot be read
is `adopter-owned`, as for the other rows.

During `/upgrade`, take the kit's `openai.yaml` for a `missing` row. For a
`policy-stale` row, take the kit's file, or add the block below if the adopter edited
the other keys. Only the block form the kit ships is recognised, so a flow mapping or
a quoted `"false"` also reads as `policy-stale`. A consumer that switches on the report's
`state` must accept `policy-stale`.

```yaml
policy:
  allow_implicit_invocation: false
```
