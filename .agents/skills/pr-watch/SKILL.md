---
name: pr-watch
description: Drive a pull request through the deterministic poll, fix, acknowledge, and re-poll loop until CI is green and review findings are resolved. Use after opening or updating a pull request, when asked to watch CI or reviews, or when a task must continue until its PR is green and clean.
---

# PR Watch

1. Work from the repository root.
2. Read `config/dev-model.yaml` and `docs/agentic-dev-kit/workflows/pr-watch.md` completely.
3. Follow the workflow for the PR number in the user's request, or the current branch's PR when none is supplied.
4. Resolve the engine path from the repository root; support both `scripts/pr_watch.py` and a namespaced adopted path such as `scripts/devkit/pr_watch.py`.
5. When a bot is unavailable, run the `review.fallback_panel` pass — one isolated, fresh-context reviewer per lens, per `docs/agentic-dev-kit/fallback-review-panel.md`. Give each lens the compute in `review.fallback_panel.lens_compute.codex` (`model` and/or `effort`; either may be absent, and an absent runtime key means the lens inherits this session's own compute). Fall back to `review.fallback_commands` only if the runtime cannot isolate a reviewer, and record that as one lens, never as the configured `review.fallback_panel.receipt_source`. Never treat an unavailable review bot as a review waiver.
6. For safety-critical changes, also read and apply `docs/agentic-dev-kit/safety-critical-changes.md` before recommending merge.
