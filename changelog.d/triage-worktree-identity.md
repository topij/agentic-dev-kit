## Triage engine: linked worktrees share a session; results carry a disposition; scheduled callers can check an outcome receipt

CHANGED (report / return shape): a triage run identity's `repository_identity.root` is
now the repository's main worktree for every linked worktree of it, not the invoking
checkout (#1103). A session drafted in one worktree continues from the primary checkout
or a later linked worktree that resolves the same state root. Identities already
recorded are compared, not rewritten: a primary-checkout session matches unchanged, and
one a linked worktree recorded before this change matches while that worktree still
exists. If it was removed, the session holds with `refusal_code`
`repository-identity`; re-add a linked worktree of the repository at the recorded path
to continue it, or finish or retire it from there first. An independent clone of the
same remote, a changed origin, invalid state and an active session's configuration
mismatch still hold. A linked worktree whose main worktree is not a checkout of the same
common dir (a bare repository's, or one whose primary used `--separate-git-dir`) still
names itself.

CHANGED (report / return shape): the triage report a run writes is bound below the root
the run identity names, so a draft started in a linked worktree writes its report under
the primary checkout's `triage.report_root`, not the worktree's. Keep that directory
ignored by Git in the primary checkout, as `/reports/` is in the kit.

ADDED (report / return shape): every triage result, and the CLI's own hard stops, carry
`disposition` (`completed`, `waiting` or `refused`), `waiting_on` and `refusal_code`.
`operator-held` is `waiting` only where the engine names what it waits on; every other
`operator-held` result is `refused`. A test that compares a whole result or a pinned
key set needs the three keys. A caller that treated every exit-0 `operator-held` as a
wait should read `disposition` instead.

CHANGED (report / return shape): a checkout whose identity cannot be established (no
`origin`, or not a Git worktree)
now stops with `hard-stop` and `refusal_code` `repository-identity` before the gate is
tried, where a missing `origin` used to read as a held gate (`operator-held`, exit 0).

ADDED (engine CLI surface): `triage_friction_log.py` takes `--outcome-receipt <abs path>`
and `--invocation-id <id>`, or `DEVKIT_TRIAGE_OUTCOME_RECEIPT` and
`DEVKIT_TRIAGE_INVOCATION_ID`, and publishes an invocation-bound receipt after each
call. It refuses a receipt path that holds a file other than a receipt, and clears an
earlier receipt before the engine runs, so a call that dies leaves none. `--check-outcome-receipt <abs path> --invocation-id <id> [--expect-context …]
[--expect-mode …]` classifies it and exits 0 for completed or waiting, 1 for refused and
2 for missing, stale, wrong-invocation or malformed evidence. A scheduled wrapper whose
exit status does not come from the CLI (a `claude -p` triage job, for one) should export
the two variables with a fresh id per run and gate on the check. Nothing changes for a
caller that passes neither.
