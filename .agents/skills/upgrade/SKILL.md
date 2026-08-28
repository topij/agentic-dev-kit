---
name: upgrade
description: Upgrade an already-adopted agentic-dev-kit installation to the current kit — migrate the config schema, refresh kit-owned engines, and diff anything that drifted. The counterpart to adopt (first install) and to re-running ./init.sh (config only). Use when pulling a kit update into a repo that already has the kit.
---

# Upgrade

Read `docs/agentic-dev-kit/workflows/upgrade.md` completely and follow it.

The workflow's Step 0 clones the kit. Re-read the workflow from that clone before
Step 2, and follow the clone's copy for the rest of the run. Its early steps execute from
whatever copy is installed in the adopter and it is replaced only in Step 4, so this
bootstrap instruction must remain in the adapter that is read first. A local edit to the
shared workflow is a kit bug to report rather than a patch to carry forward.

Treat the user's request as additional upgrade context. Resolve configured paths from
the repository root and merged configuration; translate only runtime-native invocation
and available mechanisms.
