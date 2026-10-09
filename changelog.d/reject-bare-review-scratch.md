## Panel review scratch must contain a working tree

`panel_prompt.py --scratch` now refuses bare repositories and Git metadata
directories even when their HEAD is detached at the requested commit. Pass a
checked-out working tree created with `git worktree add --detach` instead.
