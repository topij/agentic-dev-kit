---
name: parallel
description: Plan, launch, inspect, reconcile, and remove isolated development lanes backed by Git worktrees and per-lane state sandboxes. Use when work can be split into disjoint file footprints, when the user requests parallel development, or when inspecting existing agent lanes.
---

# Parallel Development

1. Work from the repository root.
2. Read `config/dev-model.yaml` and `docs/agentic-dev-kit/workflows/parallel.md` completely.
3. Follow the requested action. With no action, show the read-only lane board.
4. Resolve engine paths from the repository root; support both `scripts/dev_session.sh` and a namespaced adopted path such as `scripts/devkit/dev_session.sh`.
5. Use the current runtime's supported parallel-task mechanism. Do not assume peer messaging, model selection, background execution, or automatic terminal launch unless the runtime exposes it.
6. Preserve the cockpit/lane ownership boundary and require disjoint source-file footprints before launch.
7. For behavioral changes to lane safety, read and apply `docs/agentic-dev-kit/safety-critical-changes.md`.
