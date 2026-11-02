## session_cleanup.py: a seal refuses when `session.json` could not take its retirement tombstones

CHANGED (gate semantics): `seal` and `seal --round` now refuse, before copying any
evidence, when the inventory's `session.json`, with the new seal in place and a
`retired` tombstone reserved on every retained item (those already sealed in the
inventory included), would exceed its 1 MiB bound. Until now such a seal could
succeed and leave `retire-evidence` unable to write its tombstones, so the evidence
could not be retired. The refusal reads `sealing this would leave no room to retire
its evidence`. If you hit it, retain fewer items, or seal them in a new inventory.
An inventory that is already over the projected size keeps working as before
until its next seal.

`reconcile`'s `rounds_without_seal` is unchanged, but is now documented as rounds
that recorded no disposition for their evidence. A round sealed with an empty
`retain` and a `discard` list also retains nothing, and is not listed in it.
