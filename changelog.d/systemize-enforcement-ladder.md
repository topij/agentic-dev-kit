## Systemize: try a check before writing a rule, and keep an enforcement table

CHANGED (report / return shape): `post-merge-systemize`'s shared-rule route now chooses a
fix level in order (a structural change, then a check whose failure names the fix, then
a prose rule for judgement calls only). Each proposal names its level and why each
higher level does not work, and a proposed check carries proof that it fails on the code
of a pull request in the cluster. The run report adds each proposal's level, its proof,
and whether the enforcement table was configured. `triage-friction-log` proposes
tickets for recurring mistakes in the same order.

ADDED (config keys): optional `systemize.enforcement_table`, the path of a Markdown table
pairing each standing rule with what enforces it. The shared-rule route reads it before
proposing a prose rule and updates its row in the same patch. A config without the key
keeps working, and the run reports the table as unconfigured. `./init.sh` adds the key
(`docs/enforcement.md`) only when it writes a new `systemize:` block, so to use the
table in an existing config, add the line under `systemize:` yourself. The value must be a
`.md` path outside `report_root`, `state.dirname` and `.git` that is not one of the
run's control inputs (`AGENTS.md`, `CLAUDE.md`, the `post-merge-systemize` workflow,
`paths.friction_log`, `paths.handoff`); any other value is a hard stop (exit 1).
