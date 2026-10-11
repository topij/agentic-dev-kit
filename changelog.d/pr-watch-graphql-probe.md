## pr-watch: backend chosen by a GraphQL probe, and an unreadable commit status is named

CHANGED (gate semantics): `scripts/pr_watch.py` now uses the `gh` backend only when
`gh` is on PATH **and** a GraphQL call through it succeeds
(`gh api graphql -f query=query{rateLimit{limit}}`, once per process). Any probe
failure selects the REST backend, which polls only and never authorizes a merge. A
session whose `gh` cannot reach GraphQL, such as a Claude Code cloud session, now polls
over REST instead of failing on `gh pr view`. It needs `GH_TOKEN` or `GITHUB_TOKEN`
for that; with no token it exits 2 and says so. A local `gh` that is not logged in also
takes this path, and `--record-review`, `--record-round`, `--assert-draft` and
`--assert-ready` then refuse as they do without `gh`.

ADDED (report shape): the JSON report has a new `unavailable_reads` list of
`{surface, url, reason}`. On REST, a `403` from the combined-status endpoint
(`commits/<sha>/status`) no longer fails the poll. It adds a `commit-statuses` entry
and the merge blocker `commit-statuses could not be read — …`, and, when review bots
are configured, the review-bot block reads `signal: unavailable`. Any `403` there takes
this path, a transient rate-limit one included. `checks` then covers check runs only,
and `converged` is not held false. Any other HTTP error on any read the report needs
still exits 2; the per-check identity read keeps degrading as before.

A consumer that parses the report should read `unavailable_reads` beside
`truncated_reads`. A test that puts a fake `gh` on PATH now needs that fake to answer
`gh api graphql`, or the engine selects REST.
