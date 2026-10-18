## Scheduled triage caller enforcement and review retirement

Upgrade scheduled triage launchers together with the CLI and `lib/triage/caller.py`.
Use its run/attempt allocation, process-status recording and final run check as
documented in `workflows/triage-friction-log/engine-cli.md`. Unattended calls and
calls carrying scheduled markers now require a fresh caller-owned attempt as well
as receipt transport; direct unbound calls stop before engine dispatch. Preserve
the trusted launcher/runtime boundary described there before claiming coverage.
Interactive calls without scheduled markers keep their existing interface.

Refresh `sweep_scratch.py` before retiring managed review rounds. Retirement now
refreshes worktree, object-store and configured-root dependencies immediately
before removal and keeps a round when a new dependency becomes visible. Retain
the no-concurrent-writers contract and existing refusal handling.
