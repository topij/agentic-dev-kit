## upgrade: the lite upgrade is one engine command, `kit_doctor.py --upgrade-lite`

ADDED: `kit_doctor.py --upgrade-lite --root <repo> --branch <branch>`, run from the kit
clone, reads a lite install's upgrade: each lite file's state against the **committed**
baseline and what happens to it, whether the record is owed, the kept skills, the
`AGENTS.md` lite section's bullets against `adopt.md` L3's, and the `changelog.d/`
fragments since the baseline. Add `--json` for a machine-readable plan. With `--apply
--kit-commit <sha>` it takes the kit's copies and records `kit-manifest.json`. You
answer only the rows that need your decision: `--take` or `--keep` for an edited file
(`--keep` for a skill only), and `--take` or `--leave-absent` for a removed file or a
kept skill gone from disk. Kept skills carry over from the committed baseline. Exit 0:
done. Exit 1: refused, with nothing written after the refusal. Exit 2: a flag it cannot
act on.

CHANGED: every call refuses a `--root` that is not the top of a checkout on `--branch`,
or a branch named by `vcs.protected_branch` in the committed, staged or working-tree
config. A config copy that does not parse, or a key that names no branch, refuses too.
The read refuses a kit clone that is not clean or whose HEAD is not its origin's. Delete
the clone and run Step 0's kit block again. `--apply` refuses a clone that is not at
`--kit-commit`. One refused target (a symlink, a directory, a path under a symlinked
directory, a hardlinked file, or a Claude skill a `.claude/commands/<slug>.md` would be
shadowed by) refuses the whole run, and nothing is copied. A record that cannot be
complete leaves the old baseline as it was.

CHANGED: `upgrade.md`'s *Lite profile* runs these commands in place of its shell
blocks. Its steps no longer bind `REPO`, `KIT`, `LITE_BRANCH`, `LITE_PROTECTED` or
`LITE_TAKE`; every input is on the command line. U4 now takes and records in one step,
and U5 re-reads before the commit. If you followed the old blocks, re-run U2 with the
new command. It reads the committed baseline, so a half-finished earlier attempt needs
no clean-up first.
