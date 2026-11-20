## The scratch sweep runs Git through the shared subprocess runner, with a timeout

CHANGED (engine CLI). Refresh `sweep_scratch.py` and `lib/subprocess_runner.py`
together, at or after the runner that added `without_git_environment` and the
`CommandError` family: the sweep now imports both, so an older runner beside it
fails at import, and so do `session_cleanup.py` and `panel_prompt.py`, which import
the sweep.

Each Git call the sweep makes is now killed after 30 seconds instead of being waited
on indefinitely. A timeout is handled like any other Git failure there, so exit codes
are unchanged: a report or `--apply` run that cannot read worktree registrations or a
git dir exits 2, an act-time re-read keeps the entry, and a git dir that only its
`core.bare` setting could clear is kept. The error names the command and the bound
(`git -C <repo> worktree list --porcelain -z timed out after 30s`). The messages for
a Git that fails or cannot start are unchanged. One message changed: when Git exits 0
but prints no absolute path for `--git-common-dir`, the error now ends in `0` where it
used to quote Git's stderr, which the runner does not return on success.
