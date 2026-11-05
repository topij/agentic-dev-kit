## `upgrade.md` Step 1 stops on an unset `REPO` or `KIT` and on a failed history fetch

CHANGED (upgrade procedure): Step 1's baseline block now stops when `REPO` or `KIT` is
unset, and its non-conforming-subject count now stops when `KIT` is unset. Before, the baseline block printed
`baseline=NONE` and sent you to the degraded path as if no baseline had been recorded,
and the count printed `0`. Step 1's history fetch now stops when both
`fetch --unshallow` and its `--depth=1000` fallback fail, rather than leave the clone
shallow and let the baseline guard route you to the degraded path.

What to do: take the new `docs/agentic-dev-kit/workflows/upgrade.md`. If the history
fetch stops, make the kit's `origin` reachable and re-run that block before resolving the
baseline. The Step 0 kit block's text in `upgrade.md` and `adopt.md` now also names the
changes its clean-clone check does not see: a pattern in the clone's `.git/info/exclude`,
a `--skip-worktree` entry, and a commit made in the clone. If you made any of them, delete
`$KIT` and re-run the kit block.
