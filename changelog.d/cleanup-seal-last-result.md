## session_cleanup.py: read the seal from the record, not from `last_result.evidence`; a discard-only seal is now size-checked

CHANGED (stored record shape): `apply` and `apply --round` still return and print
their full result, `evidence` (the seal) included, but the `last_result` they store in
`session.json` (on the inventory, or on the round's entry for `--round`) no longer
has an `evidence` key. `list` prints the stored record, so its `last_result` lacks the
key too. If you read `last_result.evidence`, read the seal beside it instead: the
inventory's `seal`, or the round entry's `seal`. A `last_result` stored before this
change keeps its `evidence` until the next apply of that inventory or round replaces
it, so tolerate both shapes until then. This replaces what the
`session-cleanup-seal-size` fragment says about a seal copy in `last_result`.

CHANGED (gate semantics): `seal` and `seal --round` now check every seal against the
`session.json` bound, one with an empty `retain` included. The projection is the
record with the new seal in place and a `retired` tombstone on every retained item
(those earlier seals hold included); it no longer adds a copy of the seal. So a seal
that retains items now needs less room than before, and a discard-only seal that would
use the room earlier seals reserved for their tombstones now refuses, before anything
is written, with `sealing this would leave no room to retire its evidence`. If you
hit it, shorten the discard list or retain fewer items, or seal them in a new
inventory. The refusal's text after that phrase changed: it no longer mentions `the
copy of it an apply records`, and its advice now names the discard list.

The projection still does not reserve what an apply records besides the seal (path
outcomes, the evidence summary, approvals and statuses) or later receipts, so a write
over the bound can still refuse afterwards, as before.
