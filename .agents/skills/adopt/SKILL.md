---
name: adopt
description: Selectively adopt agentic-dev-kit into an existing repo — inspect what's already present, propose an install plan the operator confirms, then install only the missing pieces without clobbering existing files. Use when integrating the kit into a mature repository rather than a fresh one.
---

# Adopt

Read `docs/agentic-dev-kit/workflows/adopt.md` completely and follow it.

Treat the user's request as additional adoption context. Resolve configured paths from
the repository root and merged configuration when one exists; translate only
runtime-native invocation and available mechanisms.
