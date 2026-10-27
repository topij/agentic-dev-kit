## session_cleanup.py: named identity refusals and `reconcile`

- A refused inventory's message still starts with `session repository identity or
  cleanup policy changed`, now followed by `: ` and each bound field that differs, with
  stored and current values: `device (stored <n>, current <m>)`, `inode (…)`,
  `schema (…)`, `id (…)` or `policy <key> (stored <json>, current <json>)`, where a
  key on one side only shows `absent`. A malformed stored value reads
  `common identity (stored …, current …)` or `policy (stored value is not a mapping)`.
  When only the device differs it ends with a pointer to `reconcile`. A check that
  matched the whole message exactly must match the prefix instead.
- `allocation root identity changed` now carries `(stored [..], current [..])`.
- New subcommand `reconcile <session> [--approve <token>]`: previews, and with an
  approval applies, rebinding an inventory whose only changed binding is the device
  number (macOS renumbers it across reboots) and whose recorded rounds and worktrees
  are all absent. It deletes nothing. Its preview lists `rounds_marked_removed` and,
  of those, `rounds_without_seal`. To recover inventories that became unavailable
  after a reboot, run `list`, then `reconcile <session>` on each to preview it, and
  apply with `--approve <token>` under operator authorization.
- A round already recorded `removed` whose path is gone now previews as `absent`
  without its root being re-validated, so a removed round under a wiped or
  recreated temp root no longer blocks the inventory's `preview` and `apply`.
