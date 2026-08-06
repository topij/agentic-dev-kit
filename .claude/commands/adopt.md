---
description: Selectively adopt agentic-dev-kit into an existing repo — inspect what's already present, propose an install plan the operator confirms, then install only the missing pieces without clobbering existing files. Use when integrating the kit into a mature repository rather than a fresh one.
---

Read `docs/agentic-dev-kit/workflows/adopt.md` completely and follow it.

Treat `$ARGUMENTS` as additional adoption context (for example, a target repo path or
constraints on what may be installed). Resolve all configured paths from the repository
root and `config/dev-model.yaml`.
