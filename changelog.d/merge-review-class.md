## dev_session.sh merge: refuses a PR that pr_watch does not class standard

BREAKING (gate semantics): `dev_session.sh merge <scope>` now reads `review_class`
from the `pr_watch.py --json` report it polls, and refuses unless
`review_class.class` is exactly `standard`, with no `unclassified` reason, no
`matched_paths` and no config change (#1357). A `self` lane whose PR grew into a
path under `review.safety_critical_paths`, or into the config that declares them,
is refused with the matched paths: the operator lands it directly.

What you must do:
- Upgrade `dev_session.sh` and `pr_watch.py` together. A report without
  `review_class` refuses every self-merge, and the refusal says to upgrade.
- Keep `review.safety_critical_paths` declared and non-empty at the PR's base.
  Where it is missing there, every PR is unclassified and every self-merge
  refuses; land that config change on the base directly, not through a lane.
- Have the PR's base and head commits in the local clone. `pr_watch` classes
  the PR from local git, so a commit the clone has not fetched leaves it
  unclassified; the refusal says to `git fetch origin <base>` and retry.
- A test or wrapper that stubs the `pr_watch` report for a successful merge must
  add `"review_class": {"class": "standard", "matched_paths": [],
  "changes_config": false, "unclassified": null}`.
