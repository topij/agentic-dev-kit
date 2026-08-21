---
description: Triage the friction-log inbox into tracker tickets — draft tracker-issue payloads from un-graduated entries, get operator approval via DM, then file approved tickets and open a PR sweeping them into the archive. Use to graduate accumulated friction-log entries into the tracker.
argument-hint: "[resume|new|test]"
---

Read `docs/agentic-dev-kit/workflows/triage-friction-log.md` completely and follow it.

Treat `$ARGUMENTS` as the entry point — one of `resume`, `new`, or `test`; with none,
auto-detect from the state file. Resolve all configured paths from the repository root
and `config/dev-model.yaml`.
