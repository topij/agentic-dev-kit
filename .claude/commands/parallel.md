---
description: Plan, launch, inspect, reconcile, and remove isolated development lanes backed by Git worktrees and per-lane state sandboxes. Use when work can be split into disjoint file footprints, when the user requests parallel development, or when inspecting existing agent lanes.
argument-hint: "[list|plan|new|pr-watch|merge|rm|path] [args...]"
---

Read `docs/agentic-dev-kit/workflows/parallel.md` completely and follow it.

Treat `$ARGUMENTS` as the requested parallel-development action and arguments.
Resolve the engine path from the repository root.
