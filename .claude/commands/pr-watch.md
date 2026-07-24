---
description: Drive a pull request through the deterministic poll, fix, acknowledge, and re-poll loop until CI is green and review findings are resolved. Use after opening or updating a pull request, when asked to watch CI or reviews, or when a task must continue until its PR is green and clean.
argument-hint: "[pr-number]"
---

Read `docs/agentic-dev-kit/workflows/pr-watch.md` completely and follow it.

Treat `$ARGUMENTS` as the optional PR number or additional watch context. Resolve
the engine path from the repository root.
