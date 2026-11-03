## `upgrade.md` and `adopt.md` clone the kit into the checkout's git directory and name it only as `$KIT`

CHANGED: Step 0 of both workflows used to clone the kit to one shared path
`/tmp/agentic-dev-kit`. That clone failed whenever an earlier upgrade's or another
session's clone was already there. `upgrade.md` also named that path directly in Step 1's
`kit_doctor --manifest` and its fallback, Step 4's `--record-install --from-kit`, and
Step 5's `kit_doctor --manifest` and baseline `rev-parse`. So a clone made anywhere else
had to be substituted by hand into each of them, and a missed `--from-kit` recorded a
baseline from a different kit.

Step 0 now has a **kit block** that clones into the checkout's own git directory:
`upgrade.md` uses `<git dir>/agentic-dev-kit/<task branch>`, and `adopt.md` uses
`<git dir>/agentic-dev-kit`. The block clones only when nothing is there yet and refuses a
directory that is not a clone, so re-running it from any shell or session finds the same
clone again. Every later command that reads the kit, in a shell block or inline, names it
as `"${KIT:?KIT is not set — re-run the kit block in Step 0}"`. Removing an upgrade's task
worktree removes its clone too.

What to do, in the upgrade that installs this: you read this in Step 1, after Step 0 has
run from your installed `upgrade.md`, whose binding block sets `KIT=/tmp/agentic-dev-kit`.
Before Step 2, set `KIT` to the directory your clone is actually in, `/tmp/agentic-dev-kit`
if that is where the installed Step 0 put it. From Step 2 on, the adapter has you follow
the clone's `upgrade.md`, and its commands stop if `KIT` is unset. Its guards tell you to
re-run the kit block, which would make a second clone in your task's git directory: for
this one upgrade, set `KIT` again to your clone's path instead. If you read this before
starting, run the kit block from the new `upgrade.md` in place of the installed Step 0's
clone. Upgrades after this one run the kit block. Delete a clone outside a task worktree
once the upgrade has landed.
