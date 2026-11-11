## upgrade: the lite upgrade's U5 runs adopt.md's L5 itself

CHANGED: a `kit_doctor.py --upgrade-lite` read with no `--apply` now runs `adopt.md`'s
*Lite profile* L5 checks itself once U4 has nothing left to do. That is when the
working tree holds U4's record for the kit, or when the committed baseline names the
kit and every row is settled. It prints two `verify (L5):` lines, for the install and
for the skill bindings. Each of these gives a `stop: verify (L5):` line and exit 1: a
lite file that is not intact, a kept skill not on disk, any other `declined` file that
is on disk, and a binding that is neither the kit's render nor a kept skill. A
`declined` file not on disk is named on the install line. Before that point an
unpinned read prints no `verify (L5):` line, and a read given `--kit-commit` (U5)
prints `stop: verify (L5): not run — <why>` and exits 1. Under `--json` the plan has a
`verify` object (`ran`, `lines`), and those stops are in `stops`. If your upgrade notes ran L5's two commands after U4,
read U5's `verify (L5):` lines instead: U4 no longer runs L5.

CHANGED: after a successful U4, U5 no longer prints the "uncommitted or abandoned
record" `note:`. The `record: recorded in the working tree` line says what that record
is. A working-tree record for another commit, or an incomplete one, still prints the
note.

CHANGED: `upgrade.md`'s *Lite profile* gives a default task branch,
`chore/kit-upgrade-<sha>`, and a default task-worktree path beside the checkout, for a
repository that names neither. It says where U1's kit clone lives, and that U6
deletes it by path after the merge, or after the commit when there is no pull request.
It also says what happens to the living plan, and that a kit-side fault is filed
upstream or put in the friction inbox, not both.
