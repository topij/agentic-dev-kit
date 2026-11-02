## session_cleanup.py: a seal refuses when `session.json` could not take its own apply and retirement writes

CHANGED (gate semantics): `seal` and `seal --round` now refuse, before copying any
evidence, when the seal retains at least one item and the inventory's `session.json`
would exceed its 1 MiB bound with three things added: the new seal, the copy of it
that its own first `apply` stores in `last_result`, and a `retired` tombstone on every
retained item (those earlier seals hold included). Until now such a seal could succeed
and leave `apply` or `retire-evidence` unable to write, so that some or all of the
evidence could not be retired. The refusal reads `sealing this would leave no room to
retire its evidence` and counts the unretired items earlier seals hold. If you hit it,
retain fewer items, or seal them in a new inventory. A seal with an empty `retain` is
not checked. An inventory already over the projected size keeps working as before,
except that its next seal retaining an item refuses.

The reservation is partial. It does not cover the apply copies of other seals not yet
applied, a discard-only seal's discard list, the tombstones a re-apply after
`retire-evidence` copies, or an apply's other bookkeeping and later receipts. So a
write over the bound can still refuse afterwards, as before. Retained evidence
survives that refusal; an `apply` that meets it has already removed its paths and
leaves the inventory incomplete.
