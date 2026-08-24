---
name: post-merge-systemize
description: Find recurring root causes across merged-PR review findings and route them to shared rules, the friction log, or an operator-approved tracker write. Use for scheduled post-merge retros, not ad hoc single-PR review.
---

# Post-Merge Systemize

1. Work from the repository root.
2. Read `config/dev-model.yaml` and resolve configured paths and capabilities from it.
3. Read `docs/agentic-dev-kit/workflows/post-merge-systemize.md` completely.
4. Follow that workflow, treating invocation arguments as the `backfill` and `test` entry-point keywords.
5. Use the current runtime's forge, tracker, notification, and repository mechanisms. Do not substitute a tool named by another runtime.
6. Treat the configured analysis tier as guidance unless this client can mechanically apply its model or effort mapping; never claim a compute change that did not occur.
7. Never create or modify a tracker item without explicit operator confirmation.
