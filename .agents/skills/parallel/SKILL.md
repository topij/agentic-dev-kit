---
name: parallel
description: Plan, launch, inspect, reconcile, and remove isolated development lanes backed by Git worktrees and per-lane state sandboxes. Use when work can be split into disjoint file footprints, when the user requests parallel development, or when inspecting existing agent lanes.
---

# Parallel Development

Read `docs/agentic-dev-kit/workflows/parallel.md` completely and follow it.

Treat the user's request as the parallel-development action and context. Resolve the
configured engine path from the repository root; translate only runtime-native lane,
isolation, and delegation mechanisms.
