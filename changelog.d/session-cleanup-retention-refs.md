## session_cleanup.py: a remote-tracking ref no longer retains a worktree's commit

CHANGED: `preview` and `apply` used to accept a tracked Git worktree for removal
when a `refs/remotes/*` ref contained its head. They now count only local branches
(`refs/heads/*`) and tags (`refs/tags/*`) (#1312), because `git fetch --prune` can
delete a remote-tracking ref between preview and apply. Such a worktree is now kept
with the reason `worktree head has no containing local branch or tag; preserve the
commit with one before retirement`, replacing `… no containing shared branch, tag or
remote ref …`. Preserve the commit with a local branch or a tag (for example
`git tag pr-preserve/<n> <sha>`), then preview again, and update any script or test
that matches the old reason text. If a fetch refspec of yours maps into `refs/heads`
or `refs/tags` (a mirror refspec, or `--prune-tags`), a prune can delete that branch
or tag too, which this check does not detect: preserve with a ref no refspec maps.
