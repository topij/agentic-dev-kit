---
name: session-start
description: Build a concise start-of-session briefing from the living handoff, friction log, repository state, open pull requests, CI, and configured tracker. Use at the beginning of a development session, when resuming work after a gap, or when asked what the repository should do next.
---

# Session Start

Read `docs/agentic-dev-kit/workflows/session-start.md` completely and follow it.

Treat the user's request as additional session context. Resolve all configured paths
from the repository root and `config/dev-model.yaml`; translate only runtime-native
invocation and available mechanisms.
