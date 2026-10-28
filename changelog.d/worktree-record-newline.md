## A worktree record whose path holds a newline no longer keeps its entry

CHANGED (gate semantics): `sweep_scratch.py` now reads a `worktrees/*/gitdir` record
whole, stripping only its trailing line ends, rather than refusing any record that is
not one line (#1265). Git writes a worktree's path verbatim, so a worktree named with a
newline (`test_panel_prompt.py`'s `newline-only` and `both` cases build one) left a
two-line record, and an entry or review round holding it was kept as
`live-worktree: unparseable worktree record`. Such a record is now judged by the path it
names:

- a worktree inside the entry no longer keeps it, so `--finish-review-round` retires a
  round a lens ran that suite in;
- a worktree outside the entry that exists still keeps it, now with the reason
  `repository whose worktree ... lives outside this entry`;
- a record holding a newline whose path does not exist, or cannot be statted, is still
  kept as `unparseable worktree record`.

A one-line record with a leading or trailing blank is now kept as `unparseable worktree
record`; it used to be read with the blanks stripped. Git writes no such record.

Refresh `scripts/sweep_scratch.py` and its tests. If you assert the old
`unparseable worktree record` reason for a two-line record naming an existing worktree,
expect the entry's real verdict instead.
