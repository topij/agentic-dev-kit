## Take `scripts/lib/merge_predicate.py` with `dev_session.sh`, `reconcile_sessions.sh` and `lib/triage/model.py`; a `self` lane can now reconcile `held`

BREAKING (upgrade procedure): `dev_session.sh merge`, `reconcile_sessions.sh` and
`lib/triage/model.py` now read the `pr_watch.py --json` report through one new file,
`scripts/lib/merge_predicate.py` (stdlib only, run with a bare `python3`). Refresh all
four together. With the module absent, `dev_session.sh merge` refuses every merge with
`could not evaluate the pr-watch report`, `reconcile_sessions.sh` reports every probed
lane `open` under its `could not evaluate for 'held'` note, and the triage engine fails
at import.

CHANGED (gate semantics): the three callers now require the same thing of a report,
which is everything any one of them required before. A report is merge-ready only when
`mergeable`, `converged` and `done` are each `true`, `merge_blockers` and
`truncated_reads` are each an empty list, and `review_evidence.valid` is `true`, for the
exact pull request and head the caller holds. `pr_watch.py` writes all of these, so a
report from the current engine reads as before. A `mergeable` report that lists a
truncated read is now refused by `dev_session.sh merge` and is not `held`; the current
engine never emits one (only the REST backend records truncated reads, and a REST report
is never `mergeable`), so this changes only a stubbed or hand-built report.

- `dev_session.sh merge` newly requires `converged`, `done`, the empty `merge_blockers`
  and `truncated_reads`, and valid `review_evidence`. If you stub the report in a test,
  add those fields.
- `reconcile_sessions.sh` newly requires `done`, the empty `truncated_reads` and valid
  `review_evidence` before it reports a lane `held`.
- `terminal_pr_watch_receipt` newly requires `head` and `url` to be non-empty strings.

A `pr_watch.py` from before 2026-07-27 writes no `truncated_reads`, so its report fails
that check whatever else it says (one from before 2026-07-25 also writes no `mergeable`
or `converged`). `dev_session.sh merge` then refuses with `run pr-watch to convergence
first`, which in that case means: upgrade `pr_watch.py` together with the other four
files.

CHANGED (config keys): the shipped `review.safety_critical_paths` adds
`scripts/lib/merge_predicate.py` and `scripts/devkit/lib/merge_predicate.py`, because
`dev_session.sh merge` authorizes on its verdict. When upgrading an existing
installation, add the installed path (`<engine-dir>/lib/merge_predicate.py`) to your own
`review.safety_critical_paths` and to your runtime safety-critical bindings (the
`paths:` list of `.claude/rules/safety-critical-changes.md`, if you keep one), or a pull
request that changes the merge gate is classed standard: a `self` lane may merge it
itself, and a fallback review of it takes one lens instead of two.

CHANGED (gate semantics): `dev_session.sh merge` reads `review_class` more strictly
(#1371). A `review_class` lacking any of `class`, `matched_paths`, `changes_config` or
`unclassified` is refused as having no review class; `{"class": "standard"}` alone used
to merge. `changes_config` counts as a config change for any value other than `false`,
and a `matched_paths` that is not a list is not standard whatever its value. The
refusal for a report with no usable `review_class` now ends `: <what is absent>; upgrade
pr_watch.py together with dev_session.sh, then retry`.

CHANGED (gate semantics): `reconcile_sessions.sh` reports a `self` lane `held` when its
open pull request is merge-ready and its whole, classified `review_class` is not
standard, which is the pull request `dev_session.sh merge` refuses as operator-merge
(#1370). Such a batch can now exit 4 where it exited 3. A `self` lane's open pull
request is therefore polled with `pr_watch.py --json --no-persist`, as an `operator`
lane's already was. A merge-ready `self` lane whose `review_class` is absent, partial,
unclassified or carries a value `pr_watch.py` never writes stays `open` and is listed
under the `could not evaluate for 'held'` note. If you match the reconciler's
exit status or `held` rows per lane class, expect `held` and 4 for these lanes.
