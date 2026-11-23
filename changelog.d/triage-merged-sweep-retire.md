## Triage recover: retire a sweep whose fixed pull request merged

ADDED — report shape: Refresh `lib/triage/recovery.py`, `lib/triage/engine.py`,
`lib/triage/providers.py`, `scripts/tests/test_finalize_triage.py`, and the shared
`triage-friction-log/recovery.md` and `engine-cli.md`. Some sweep pull requests need a
fix commit before they can merge, for example when a required check fails on the bytes
the engine committed. That left the run's state in `forge-finalize`, waiting on
`reconciliation`, and no command could move it (#1474). After such a pull request merges,
run `recover` interactively with `--enable-github-forge`. If the forge reads the pull
request back as merged at the moved head, and git finds exactly one commit that swept
the run's blocks, the recovery plan offers a fourth action, `retire-merged-sweep-state`.
Its action core carries `merged_sweep_evidence`. Approve it as you approve the other
recovery actions, running `recover` with `--enable-github-forge` again. The state is
quarantined and the next session starts from the receipt. Retirement does not run the
post-merge cleanup that completing a run does, so remove the run's finalize worktree,
local branch and remote branch yourself.

A consumer that accepts only the three earlier action names must accept the new one.
`recover` on such a state (its last watch neither `verified` nor `unsettled`) now refuses,
until the merge is proven, with `sweep pull request watch cannot complete and its merged
sweep is not proven; recovery refused`, where it used to say `captured state is valid;
recovery refused` and name `resume`. An `unsettled` watch still gets the old refusal. A custom `ForgeProvider` must answer
the new `pull-request-read-back` authority action, with the `gh pr view` fields plus
`merged`, before it can use this route.
