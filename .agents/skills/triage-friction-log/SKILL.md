---
name: triage-friction-log
description: Triage the friction-log inbox into tracker tickets — draft tracker-issue payloads from un-graduated entries, get operator approval via DM, then file approved tickets and open a PR sweeping them into the archive. Use to graduate accumulated friction-log entries into the tracker.
---

# Triage Friction Log

1. Work from the repository root.
2. Read `config/dev-model.yaml` and resolve configured paths from it.
3. Read `docs/agentic-dev-kit/workflows/triage-friction-log.md` completely.
4. Follow that workflow, treating any argument as the entry point — one of `resume`, `new`, or `test`; with none, auto-detect from the state file.
5. Session A never writes to the tracker or the friction log. Every write happens in Session B, after the operator's DM reply.
6. Use the current runtime's tracker and notify mechanisms; require user authorization for external mutations not already requested.
