## session_cleanup.py: read the seal from the record, not from `last_result.evidence`; a retaining seal needs less room

CHANGED (stored record shape): `apply` and `apply --round` still return and print
their full result, `evidence` (the seal) included, but the `last_result` they store in
`session.json` (on the inventory, or on the round's entry for `--round`) no longer
has an `evidence` key. `list` prints the stored record, so its `last_result` lacks the
key too. If you read `last_result.evidence`, read the seal beside it instead: the
inventory's `seal`, or the round entry's `seal`. A `last_result` stored before this
change keeps its `evidence` until the next apply of that inventory or round replaces
it, so tolerate both shapes until then. This replaces what the
`session-cleanup-seal-size` fragment says about a seal copy in `last_result`.

CHANGED (gate semantics): `seal` and `seal --round` still check a seal that retains at
least one item against the `session.json` bound, but the projection no longer adds a
copy of the seal: it is the record with the new seal in place and a `retired`
tombstone on every retained item (those earlier seals hold included). So a retaining
seal that refused before for lack of room may now pass. A discard-only seal is still
not checked. The refusal's text no longer mentions `the copy of it an apply
records`; its start, `sealing this would leave no room to retire its evidence`, is
unchanged.

The projection still does not reserve a discard-only seal's discard list, what an
apply records besides the seal (path outcomes, the evidence summary, approvals and
statuses) or later receipts, so a write over the bound can still refuse afterwards,
as before.
