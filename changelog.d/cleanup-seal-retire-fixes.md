## session_cleanup.py: apply works again after retire-evidence; a malformed seal no longer breaks `list`

CHANGED (gate semantics): after `retire-evidence` deleted items from an inventory's
seal, every later `apply` of that inventory refused with `session has a different
persisted approval`, and the only way out was hand-editing `session.json`. The
`apply` and `apply --round` approval tokens now leave out the `retired` tombstones
that `retire-evidence` adds to items. A token for a seal with no tombstones is
unchanged. An inventory `apply` also accepts a persisted approval that binds the
tombstones as they stand now, which an inventory completed by its round applies
could have persisted before this change, and replaces it with the current token. If
one of your inventories is stuck this way, run `preview` again and apply with the
token it gives; no `session.json` edit is needed. One case stays stuck, as it already
was before this change: an inventory whose approval was persisted over tombstones and
which then had more items retired by a later `retire-evidence`. Its `apply` still
refuses. Such an inventory is already complete and needs no further apply:
`retire-evidence` does not depend on one, so leave it as it is.

CHANGED: a seal, inventory or round, that is neither null nor an object, or whose
`retained` is missing or not a list of objects, is now refused when the inventory loads, with an `error:`
naming that seal. `list` reports that inventory as `unavailable` and keeps listing
the rest; before, a seal that was not an object aborted `list` for every inventory.
`preview`, `apply`, `retire-evidence` and `reconcile` exit 2 on it. Deeper malformed
fields (an item missing `sha256`, say) are not checked by name: commands still exit 2
on them, with the underlying error.
