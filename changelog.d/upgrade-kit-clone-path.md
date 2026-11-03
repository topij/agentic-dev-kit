## `upgrade.md` and `adopt.md` clone the kit into a fresh directory and name it only as `$KIT`

CHANGED: Step 0 of both workflows used to clone the kit to one shared path
`/tmp/agentic-dev-kit`. That clone failed whenever an earlier upgrade's or another
session's clone was already there. `upgrade.md` also named that path directly in Step 1's
`kit_doctor --manifest` and its fallback, Step 4's `--record-install --from-kit`, and
Step 5's `kit_doctor --manifest` and baseline `rev-parse`. So a clone made anywhere else
had to be substituted by hand into each of them, and a missed `--from-kit` recorded a
baseline from a different kit. Step 0 now runs:

```bash
KIT="$(mktemp -d "${TMPDIR:-/tmp}/agentic-dev-kit.XXXXXX")" || exit 1
case "$KIT" in /*) ;; *) echo "KIT is not an absolute path: $KIT" >&2; exit 1 ;; esac
git clone --depth 1 https://github.com/topij/agentic-dev-kit "$KIT" || exit 1
```

Every later command that reads the kit, in a shell block or inline, names it as
`"${KIT:?KIT is not set — set it to the path Step 0 printed; do not clone again}"`, so a command run without `KIT` set stops
instead of reading another tree.

What to do, in the upgrade that installs this: you read this in Step 1, after Step 0 has
run from your installed `upgrade.md`, whose binding block sets `KIT=/tmp/agentic-dev-kit`.
Before Step 2, set `KIT` to the directory your clone is actually in, `/tmp/agentic-dev-kit`
if that is where the installed Step 0 put it. From Step 2 on, the adapter has you follow
the clone's `upgrade.md`, and its commands stop if `KIT` is unset. If you read this before
starting, clone with the block above and use the path it prints wherever the installed
Steps 0 and 1 name `/tmp/agentic-dev-kit`. Upgrades after this one run the new Step 0.
Delete the clone once the upgrade has landed.
