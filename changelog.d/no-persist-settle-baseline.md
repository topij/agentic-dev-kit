## pr-watch: gh `--no-persist` records the settle baseline

CHANGED (gate semantics, engine CLI surface): gh `pr_watch.py --no-persist` writes
the settle baseline to the per-PR state file — `head`, `max_total`,
`max_total_backend` and `settle_since` with its check count — computed exactly as a
plain poll computes it. In serialized use it preserves `seen`, `pending_seen`,
`bot_pending_since`, `review_receipt` and `review_rounds`, so
`--mark-seen` still acknowledges only what the last persisting poll reported.

A gh caller that only polls with `--no-persist`, such as a cockpit behind a Merge
button, now sees `check rollup has not settled for current head (no settle baseline
recorded)` clear once `review.settle_grace_minutes` has passed at an unchanged check
count, without a plain poll in between. Before this it never cleared.

What an adopter must do: serialize operations on the same per-PR state file,
including `--no-persist` polls. The existing unlocked, truncating writer can lose
concurrent updates or damage state on failure. A failed state re-read or write blocks
that poll's merge authorization; recheck stored state and review evidence before
retrying. A test that asserts a `--no-persist` poll leaves the state
file byte-for-byte unchanged, or creates no file, must allow those four keys on gh.
REST `--no-persist` continues to leave watch state unchanged, preventing its different
check count from wedging later gh polls. No baseline is reset on transport changes;
existing persisting REST polls retain their documented cross-backend limitation. The
poll does not overwrite a state file it cannot read as a JSON object, does not
rewrite an unchanged baseline, and records nothing for a report with no head.
