---
name: pr-watch
description: Drive a pull request through the deterministic poll, fix, acknowledge, and re-poll loop until CI is green and review findings are resolved. Use after opening or updating a pull request, when asked to watch CI or reviews, or when a task must continue until its PR is green and clean.
---

# PR Watch

1. Work from the repository root.
2. Read `config/dev-model.yaml` and `docs/agentic-dev-kit/workflows/pr-watch.md` completely.
3. Follow the workflow for the PR number in the user's request, or the current branch's PR when none is supplied.
4. Resolve the engine path from the repository root; support both `scripts/pr_watch.py` and a namespaced adopted path such as `scripts/devkit/pr_watch.py`.
5. Use `review.fallback_commands` for the current runtime when configured. Never treat an unavailable review bot as a review waiver.
6. For safety-critical changes, also read and apply `docs/agentic-dev-kit/safety-critical-changes.md` before recommending merge.
