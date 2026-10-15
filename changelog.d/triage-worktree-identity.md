## Triage engine: linked worktrees share a session; results carry a disposition

CHANGED (report / return shape): a triage run identity's `repository_identity.root` is
now the repository's main worktree for every linked worktree of it, not the invoking
checkout (#1103). A session drafted in one worktree continues from the primary checkout
or a later linked worktree that resolves the same state directory. Identities are
compared by exact equality and never rewritten: a primary-checkout session matches
unchanged. A session a linked worktree recorded before this change names that
worktree, so it no longer matches and holds with `refusal_code` `repository-identity`;
retire it with interactive `recover` (none existed in the kit, cs-toolkit or
OpenKitchen state roots on 2026-10-15). An independent clone of the same remote, a
changed origin, invalid state and an active session's configuration mismatch still
hold. A linked worktree whose main worktree is not a checkout of the same common dir (a
bare repository's, or one whose primary used `--separate-git-dir`), or one on a Git
older than 2.36, still names itself.

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
`origin`, or not a Git worktree) now stops with `hard-stop` and `refusal_code`
`repository-identity` before the gate is tried, where a missing `origin` used to read as a held gate (`operator-held`, exit 0).

CHANGED (gate semantics): every triage run that writes the report now checks that the
report directory below the identity's root is writable first (a draft before it
reserves a session, a resume before it rebinds or advances one) and stops with
`hard-stop`, gate released, otherwise. Keep the primary checkout's report root writable
by every account that runs triage, scheduled jobs in temporary worktrees included.

What an adopter must do: refresh the triage engines together, including the new
`lib/triage/outcome.py` that `engine.py` imports (`/upgrade` takes it from
`kit-manifest.json`), and the new kit-owned test
`scripts/tests/test_triage_worktree_identity.py`.
