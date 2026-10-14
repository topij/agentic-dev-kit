## pr-watch: a `--no-persist` poll records the settle baseline

CHANGED (gate semantics, engine CLI surface): `pr_watch.py --no-persist` now writes
the settle baseline to the per-PR state file — `head`, `max_total`,
`max_total_backend` and `settle_since` with its check count — computed exactly as a
plain poll computes it. It still writes nothing else: `seen`, `pending_seen`,
`bot_pending_since`, `review_receipt` and `review_rounds` are left as they are, so
`--mark-seen` still acknowledges only what the last persisting poll reported.

A caller that only polls with `--no-persist`, such as a cockpit behind a Merge
button, now sees `check rollup has not settled for current head (no settle baseline
recorded)` clear once `review.settle_grace_minutes` has passed at an unchanged check
count, without a plain poll in between. Before this it never cleared.

What an adopter must do: a test that asserts a `--no-persist` poll leaves the state
file byte-for-byte unchanged, or creates no file, must now allow those four keys. The
poll does not overwrite a state file it cannot read as a JSON object, does not
rewrite an unchanged baseline, and records nothing for a report with no head.
