## session_cleanup.py: named identity refusals and `reconcile`

- A refused inventory's message still starts with `session repository identity or
  cleanup policy changed`, now followed by `: ` and each bound field that differs, with
  stored and current values: `device (stored <n>, current <m>)`, `inode (…)`,
  `schema (…)`, `id (…)` or `policy <key> (stored <json>, current <json>)`. When only
  the device differs it ends with a pointer to `reconcile`. A check that matched the
  whole message exactly must match the prefix instead.
- `allocation root identity changed` now carries `(stored [..], current [..])`.
- New subcommand `reconcile <session> [--approve <token>]`: previews, and with an
  approval applies, rebinding an inventory whose only changed binding is the device
  number (macOS renumbers it across reboots) and whose recorded rounds and worktrees
  are all absent. It deletes nothing. To recover inventories that became unavailable
  after a reboot, run `list`, preview each, and apply under operator authorization.
