## pr_watch: `--repair-pending` holds the merge gate until a review's repair is pushed

ADDED (engine CLI surface, gate semantics): `pr_watch.py --record-review` takes
`--repair-pending`. The receipt it records carries `"repair_pending": true`, and while
the pull request's head is still the reviewed head, every poll adds a merge blocker and
reports `mergeable` (and `done`) false. Pushing the repair moves the head and releases
it; recording again at the same head without the flag withdraws it. A receipt without
the field gates exactly as before.

To adopt it, take `scripts/pr_watch.py` with `docs/agentic-dev-kit/workflows/pr-watch.md`
and `docs/agentic-dev-kit/fallback-review-panel.md`, and pass the flag whenever a
receipt's disposition leaves a repair to commit. The hold is in the engine's report
only: GitHub's merge button and `gh pr merge` do not read it.
