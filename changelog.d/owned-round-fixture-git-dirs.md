## Review-round retirement removes test-fixture git dirs

CHANGED (gate semantics): `sweep_scratch.py --finish-review-round <receipt> --apply
--reviewers-finished` now removes a round whose only git dirs are test fixtures, where
it used to return `kept` with a `live-worktree` reason (#997). Inside a verified round,
two kinds of git dir no longer keep it:

- a bare repository, or a `--separate-git-dir` target whose `.git` pointer is also in
  the round, in either case with no `worktrees` record naming a tree outside it;
- a nonempty `.git` file that is not a `gitdir:` pointer.

A git dir that something outside the round depends on is still kept. So is a git dir
whose config cannot be read as a regular file. The age sweep (`--apply --older-than`)
is unchanged and still keeps all of them.

Refresh `scripts/sweep_scratch.py` and its tests. If you assert that a round holding a
pytest basetemp of fixture repositories is `kept`, it is now `removed`.
