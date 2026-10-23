## The age sweep removes test-fixture git dirs

CHANGED (gate semantics): `sweep_scratch.py` now judges a git dir not beside its own
work tree the same way in every entry, not only in a review round retired by its
receipt (#1185). An entry it used to report as `live-worktree` for such a git dir is
now `stale`, and `--apply --older-than` removes it once it is old enough, when the git
dir has no `worktrees` record naming a tree outside the entry and is either:

- a bare repository, or
- a `--separate-git-dir` target that a `.git` file inside the entry names.

An entry is still kept for a separated git dir that no in-entry `.git` file names,
for a bare one with a linked worktree outside it, and for a git dir whose config cannot
be read as a regular file. A nonempty `.git` file that does not start with `gitdir:`
still keeps an unowned entry; only `--finish-review-round` exempts it.

What this newly leaves unprotected in an unowned entry: a bare repository driven as
`git --git-dir=<it> --work-tree=<elsewhere>`, named as an outside clone's remote, or
borrowed from through an unconfigured repository's `alternates`; a
`--separate-git-dir` target given `core.bare = true` by hand; a separated git dir whose
real work tree is outside but which a copied `.git` file inside the entry names; and a
git dir whose linked worktree outside was moved with plain `mv`, so its `worktrees`
record names a path that no longer exists. If a configured `scratch.roots` root can
hold any of these, remove it from `scratch.roots`.

Refresh `scripts/sweep_scratch.py` and its tests. The engine helper
`_owned_detached_reason` is now `_detached_reason`. If you assert that an age sweep
keeps an entry holding fixture repositories, it is now `stale`.
