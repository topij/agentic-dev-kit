## session_cleanup.py: apply works again after retire-evidence; a malformed seal no longer breaks `list`

FIXED: after `retire-evidence` deleted items from an inventory's seal, every later
`apply` of that inventory refused with `session has a different persisted approval`,
and the only way out was hand-editing `session.json`. The `apply` and `apply --round`
approval tokens now leave out the `retired` tombstones that `retire-evidence` adds to
items. A token for a seal with no tombstones is unchanged, so approvals already
persisted still match. If one of your inventories is stuck this way, run `preview`
again and apply with the token it gives. No `session.json` edit is needed.

CHANGED: an inventory whose seal, or one of whose round seals, is not an object
holding a list of retained-item objects is now refused when it loads. `list` reports
that inventory as `unavailable` and keeps listing the rest. Before, `list` aborted
for every inventory. `preview`, `apply` and `retire-evidence` exit 2 with an
`error:` line naming the seal, where some of these cases used to crash with a traceback.
