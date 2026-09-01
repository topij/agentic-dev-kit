This is a synthetic Phase 4 evidence lane sourced from
`saved_plans/codex-parallel-batch-design_2026-09-01.md`; it has no tracker ticket.

Work only on branch `dev/parallel-alpha` in the worktree the launcher selected.
Before committing, run `git branch --show-current` and refuse if it is not that branch.

Create only `notes/parallel-alpha.md` with these exact bytes:

```text
# Parallel alpha

Scope: parallel-alpha
Expected peer: parallel-beta
Evidence role: disjoint-worktree-and-state-root identity
```

Do not edit `notes/parallel-beta.md`, `docs/kit-handoff.md`, or
`docs/kit-friction-log.md`. Run `git diff --check`, commit with subject
`test fixture: add parallel alpha evidence note`, and push only
`dev/parallel-alpha` to `origin`.

Open a ready pull request against `main` titled
`test fixture: add parallel alpha evidence note`. Its body must say this is a
synthetic retained-evidence lane, name the changed path, state that the merge class
is operator, and say the pull request must remain open and unmerged. Resolve the pull
request identity from GitHub, confirm repository, base, head, and ready state, then run
the repository's ready assertion and one JSON `pr_watch` poll. No CI workflow is
installed in this fixture. Do not record your own review receipt and do not merge;
the cockpit owns independent review and the operator-authority observation.

In final text report the branch, commit, pull-request URL and number, changed path,
ready assertion result, JSON poll result, and any permission denial or escalation.
