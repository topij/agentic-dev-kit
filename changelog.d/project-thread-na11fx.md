## Ticket-creation instructions are pinned by region snapshots

CHANGED (test inputs): `scripts/tests/test_portability.py` now reads snapshots
under `scripts/tests/fixtures/ticket-creation-regions/`. When refreshing the
portability tests, copy those files with it; without them the new tests fail on
a missing shipped input. Each snapshot pins the reviewed ticket-creation instructions
of `triage-friction-log`, `post-merge-systemize` or `wrap-up`, from the
execution-environment metadata instruction to the text that follows its payload
binding. If you edit one of those regions in your copy of a workflow, update the
matching snapshot in the same change, after independent review.

The snapshots compare text inside each region only. They do not detect a contradiction
written elsewhere in a workflow, and they do not test an agent's classification or a
tracker write. `wrap-up` also gains a declared-field check: environment metadata is
prepared before a proposed ticket is presented, and it is part of the exact payload
the operator approves.
