---
description: Upgrade an already-adopted agentic-dev-kit installation to the current kit — migrate the config schema, refresh kit-owned engines, and diff anything that drifted. The counterpart to /adopt (first install) and to re-running ./init.sh (config only). Use when pulling a kit update into a repo that already has the kit.
---

Read `docs/agentic-dev-kit/workflows/upgrade.md` completely and follow it.

**Its Step 0 clones the kit. Re-read the workflow from that clone before Step 2, and
follow the clone's copy for the rest of the run.** The workflow's own early steps execute
from whatever copy is on disk here, and it is replaced only in Step 4 — so an installed
copy that is behind the kit drives the entire upgrade before anything refreshes it, and
the paragraph telling you to check for that is inside the copy you do not have yet. That
is why the instruction is here instead: this adapter is the one surface read before any
of it. A workflow doc is kit-owned, so a local edit to it is a kit bug to report rather
than a patch to carry forward.

Treat `$ARGUMENTS` as additional upgrade context. Resolve all configured paths from the
repository root and `config/dev-model.yaml`.
