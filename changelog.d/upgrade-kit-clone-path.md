## `upgrade.md` and `adopt.md` clone the kit into a fresh directory and name it only as `$KIT`

CHANGED: Step 0 of both workflows used to clone the kit to one shared path
`/tmp/agentic-dev-kit`. That clone failed whenever an earlier upgrade's or another
session's clone was already there, and several later commands, among them Step 4's
`--record-install --from-kit`, named that path directly. So a clone made anywhere else
had to be substituted by hand into each of them, and a missed one recorded a baseline
from a different kit. Step 0 now runs:

```bash
KIT="$(mktemp -d "${TMPDIR:-/tmp}/agentic-dev-kit.XXXXXX")" || exit 1
git clone --depth 1 https://github.com/topij/agentic-dev-kit "$KIT" || exit 1
```

Every later command names the kit as `"${KIT:?KIT is not set — re-run Step 0}"`, so a
command run without `KIT` set stops instead of reading another tree.

What to do: your next upgrade starts from the `upgrade.md` you have installed now, whose
Step 0 still clones to `/tmp/agentic-dev-kit`. Use the block above for that clone
instead, and set `KIT` to the path it prints. From Step 2 on, the adapter has you
follow the new clone's copy, which uses `$KIT` throughout. Delete the clone once the
upgrade has landed.
