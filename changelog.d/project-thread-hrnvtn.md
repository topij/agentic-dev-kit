## CI workflows and hooks join the safety-critical list

CHANGED (config keys): the shipped `review.safety_critical_paths` adds
`.github/workflows/*`, `scripts/hooks/*`, `scripts/devkit/hooks/*`,
`.claude/settings.json` and `.codex/hooks.json` (#1150). If your repository
inherited the kit's list, a pull request touching one of these now takes the
two-lens fallback review. Keep the entries, or remove any that do not exist in your
repository; if you keep a Claude Code copy of the list in
`.claude/rules/safety-critical-changes.md`, make it match.
