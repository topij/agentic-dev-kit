## session_cleanup.py and sweep_scratch.py: boot-stable directory identity

CHANGED (record and receipt shape): inventories and review-round receipts now bind
each directory by a tagged identity, `["volume", <UUID>, <inode>]` on macOS or
`["device", <st_dev>, <inode>]` elsewhere and wherever no volume UUID is readable.
On macOS a reboot that renumbers the device number no longer makes new inventories
or receipts unavailable.

- New inventories are `schema: "devkit-cleanup-session/2"`, and their
  `common_identity` takes the tagged form, as does each worktree `identity` recorded
  from now on, in any inventory. New
  receipts from `sweep_scratch.py --create-review-round` and `session_cleanup.py
  allocate` are `version: 2`, with tagged `identity` and `root_identity`. A version 1
  receipt is still accepted, with its old `[st_dev, st_ino]` check. A tool that reads
  these fields as a two-integer pair must accept the three-element form.
- A schema 1 inventory keeps loading on its `[st_dev, st_ino]` pair, as before. After
  a reboot that renumbers the device, `reconcile <session>` (preview, then
  `--approve <token>` under operator authorization) rebinds it to the new identity
  and schema 2, under the existing preconditions. Its preview and the `reconciled`
  history now carry `schema` (`stored`/`current`).
- Refusals can name two new fields: `volume (stored <UUID>, current <UUID>)` and
  `identity kind (stored 'volume', current 'device')`. Neither is reconcilable, in
  either direction between the kinds. Nor is an inventory whose volume UUID changed,
  for example one restored onto another volume.
- `reconcile` now names a shape-broken record's differing field before it checks
  the removal journal, instead of failing with a bare `KeyError`.
- A round that reconcile marked removed and whose path reappears now previews and
  applies as `kept`, with a reason, instead of refusing the whole inventory with
  `allocation root identity changed`. No removal is attempted on it.
