## session_cleanup.py: a remote-tracking ref no longer retains a worktree's commit

CHANGED: `preview` and `apply` used to accept a tracked Git worktree for removal
when a `refs/remotes/*` ref contained its head. They now count only local branches
(`refs/heads/*`) and tags (`refs/tags/*`) (#1312). `git fetch --prune` deletes a
remote-tracking ref under a fetch refspec's destination pattern when the remote has
no ref at the matching source. That covers a merged PR's deleted branch, and
`refs/remotes/origin/pr/<n>` fetched from `refs/pull/<n>/head`, which the default
refspec maps to a nonexistent `refs/heads/pr/<n>` while the pull ref still exists.
That made preview and apply disagree. If a fetch refspec of yours maps into
`refs/heads` or `refs/tags` (a mirror refspec, or `--prune-tags`), a prune can delete
a local branch or tag too, and this check does not detect that. A worktree whose head
only a remote-tracking ref contains is now kept with the reason `worktree head has no
containing local branch or tag; preserve the commit with one before retirement`. The
old reason `… no containing shared branch, tag or remote ref …` is gone. Preserve
such a commit with a local branch or a tag (for example `git tag pr-preserve/<n>
<sha>`), then preview again. A script or test that matches the old reason text needs
the new one.
