---
name: session-start
description: Build a concise start-of-session briefing from the living handoff, friction log, repository state, open pull requests, CI, and configured tracker. Use at the beginning of a development session, when resuming work after a gap, or when asked what the repository should do next.
---

# Session Start

1. Work from the repository root.
2. Read `config/dev-model.yaml` and resolve configured paths from it.
3. Read `docs/agentic-dev-kit/workflows/session-start.md` completely.
4. Follow that workflow using the user's request as additional session context.
5. Use the current runtime's available tools for independent reads and delegation. Treat configured model names as capability guidance; do not claim a model switch the runtime cannot perform.
6. Keep the briefing read-only unless the user explicitly asks to begin the recommended work.
