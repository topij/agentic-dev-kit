## dev_session.sh merge: refuses a PR that pr_watch does not class standard

CHANGED: `dev_session.sh merge <scope>` now reads `review_class` from the
`pr_watch.py --json` report it polls, and refuses unless `review_class.class` is
exactly `standard` with no `unclassified` reason. A `self` lane whose PR grew into
a path under `review.safety_critical_paths`, or into the config that declares
them, is refused with the matched paths and the instruction that the operator
lands it directly. A report without `review_class` (a `pr_watch` older than the
field) or with one that could not class the PR refuses too.

If you install `dev_session.sh` without the matching `pr_watch.py`, upgrade both
together, or every self-merge will refuse. A test or wrapper that stubs the
`pr_watch` report for a successful merge must add a `review_class` of
`{"class": "standard", "unclassified": null}`.
