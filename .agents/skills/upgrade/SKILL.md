---
name: upgrade
description: Upgrade an already-adopted agentic-dev-kit installation to the current kit — migrate the config schema, refresh kit-owned engines, and diff anything that drifted. The counterpart to adopt (first install) and to re-running ./init.sh (config only). Use when pulling a kit update into a repo that already has the kit.
---

# Upgrade

1. Work from the repository root of the repo being upgraded.
2. Read `config/dev-model.yaml` and resolve configured paths from it. If there is none,
   the workflow's Step 0 says to stop and adopt instead — follow that rather than guessing
   a config into existence.
3. Read `docs/agentic-dev-kit/workflows/upgrade.md` completely.
4. Follow that workflow in order. Steps 0 and 1 are read-only; everything from Step 2
   mutates the repo and must happen on a branch.
5. Do not batch-replace kit-owned files because most of them are `unchanged` — the
   `differs` entries are where the risk is, and each is a decision the workflow specifies.
6. Use the current runtime's review and commit mechanisms; require user authorization for
   external mutations not already requested.
