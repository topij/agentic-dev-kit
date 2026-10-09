## Panel scratch checks report Git state, not checkout creation

Create and inspect a detached checkout before passing its root as `--scratch`.
The prompt reports assembly-time Git checks; it no longer claims that the
assembler established that a checkout was built. Contents and cleanliness are
not verified by this read-only assembler.

Bare repositories, Git metadata directories and nested paths are refused. The
root must lie outside its own Git metadata directory even when `core.worktree`
points inside it. Relative root paths and symlink aliases remain accepted.
