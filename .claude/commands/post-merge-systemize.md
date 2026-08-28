---
description: Find recurring root causes across merged-PR review findings and route them to shared rules, the friction log, or an operator-approved tracker write. Use for scheduled post-merge retros, not ad hoc single-PR review.
argument-hint: "[backfill] [test]"
---

Read `docs/agentic-dev-kit/workflows/post-merge-systemize.md` completely and follow it.

Treat `$ARGUMENTS` as entry-point keywords. Resolve configured paths from the repository
root and merged configuration defined by the shared workflow. This runtime's
repository-instruction layer is `CLAUDE.md` and `.claude/rules/`. Translate the
configured analysis tier only when the current launcher exposes that control; otherwise
treat it as guidance and do not claim that the model or effort changed.
