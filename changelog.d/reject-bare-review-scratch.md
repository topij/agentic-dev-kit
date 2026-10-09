## Panel review scratch must name a checked-out worktree root

`panel_prompt.py --scratch` refuses bare repositories and Git metadata
directories even when their HEAD is detached at the requested commit. Pass the
root of a checked-out working tree created with `git worktree add --detach`.

A subdirectory is refused. The root must lie outside its own Git metadata
directory, even when `core.worktree` points inside that directory. Relative root
paths and symlink aliases remain accepted.
