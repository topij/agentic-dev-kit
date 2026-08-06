---
description: Upgrade an already-adopted agentic-dev-kit installation to the current kit — migrate the config schema, refresh kit-owned engines, and diff anything that drifted. The counterpart to /adopt (first install) and to re-running ./init.sh (config only). Use when pulling a kit update into a repo that already has the kit.
argument-hint: "[--dry-run]"
---

Read `docs/agentic-dev-kit/workflows/upgrade.md` completely and follow it.

Treat `$ARGUMENTS` as additional upgrade context. Resolve all configured paths from the
repository root and `config/dev-model.yaml`.
