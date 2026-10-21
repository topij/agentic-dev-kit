## CI workflows and hooks join the safety-critical list

CHANGED (config keys): the shipped `review.safety_critical_paths` adds
`.github/workflows/*`, `scripts/hooks/*`, `scripts/devkit/hooks/*`,
`.claude/settings.json` and `.codex/hooks.json` (#1150). If your repository
inherited the kit's list, a pull request touching one of these now takes the
two-lens fallback review and the operator-merge route. Keep the entries, or remove
any that do not exist in your repository. Make
`.claude/rules/safety-critical-changes.md`'s path list match, and name the same files
in your adopter-owned `AGENTS.md` binding (the Codex side), as the shipped
`docs/templates/AGENTS.md.tmpl` and `docs/AGENTS-sections.md` now do.
