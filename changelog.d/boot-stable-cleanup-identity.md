## session_cleanup.py and sweep_scratch.py: boot-stable directory identity

CHANGED (record and receipt shape): inventories and review-round receipts now bind
each directory by a tagged identity, `["volume", <UUID>, <inode>]` on macOS or
`["device", <st_dev>, <inode>]` elsewhere and wherever no volume UUID is readable.
On macOS a reboot that renumbers the device number no longer makes new inventories
or receipts unavailable.

- New inventories are `schema: "devkit-cleanup-session/2"`, and their
  `common_identity` and each worktree's `identity` take the tagged form. New
  receipts from `sweep_scratch.py --create-review-round` and `session_cleanup.py
  allocate` are `version: 2`, with tagged `identity` and `root_identity`. A version 1
  receipt is still accepted, with its old `[st_dev, st_ino]` check. A tool that reads
  these fields as a two-integer pair must accept the three-element form.
- A schema 1 inventory no longer loads. `list` reports it unavailable with
  `schema (stored 'devkit-cleanup-session/1', current 'devkit-cleanup-session/2'; …)`
  and a pointer to `reconcile`. To upgrade one, preview `session_cleanup.py reconcile
  <session>` and apply `--approve <token>` under operator authorization. The preview
  now carries `mode` (`schema-upgrade` or `renumbered-device`), `schema`
  (`stored`/`current`) and `worktrees_rebound`. `schema-upgrade` mode needs the
  device and inode to still match, and no round that is not yet `removed` may be
  present; such a round whose path is absent is marked removed, deleting nothing.
  Worktrees may still be present. **Before taking this upgrade, retire every live
  round** (`seal`, `preview`, `apply --round`): this engine cannot load a schema 1
  inventory to retire one, so a present live round afterwards must be preserved and
  removed by hand before the upgrade applies. In `renumbered-device` mode, every
  recorded path must be absent, as before.
  Recover inventories that became unavailable after a reboot the same way.
- Refusals can name two new fields: `volume (stored <UUID>, current <UUID>)` and
  `identity kind (stored 'volume', current 'device')`. Neither is reconcilable, in
  either direction between the kinds. Nor is an inventory whose volume UUID changed,
  for example one restored onto another volume.
- `reconcile` now names a shape-broken record's differing field before it checks
  the removal journal, instead of failing with a bare `KeyError`.
- A round that reconcile marked removed and whose path reappears now previews and
  applies as `kept`, with a reason, instead of refusing the whole inventory with
  `allocation root identity changed`. No removal is attempted on it.
