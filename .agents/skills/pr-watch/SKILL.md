---
name: pr-watch
description: Drive a pull request through the deterministic poll, fix, acknowledge, and re-poll loop until CI is green and review findings are resolved. Use after opening or updating a pull request, when asked to watch CI or reviews, or when a task must continue until its PR is green and clean.
---

# PR Watch

Read `docs/agentic-dev-kit/workflows/pr-watch.md` completely and follow it.

Treat the user's request as the optional PR number or additional watch context. Resolve
the configured engine path from the repository root.

When the fallback panel runs, use one isolated fresh-context reviewer per configured
lens. Carry `review.fallback_panel.lens_compute.codex` on the `codex exec` argv as
`-c model_reasoning_effort=<effort>` and, when configured, `-m <model>`; read the
applied values back from the rollout. Translate only runtime-native reviewer isolation
and available mechanisms, and never treat an unavailable reviewer as a waiver.
