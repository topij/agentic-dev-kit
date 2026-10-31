## session_cleanup retires a task worktree nested under the primary checkout

CHANGED: `session_cleanup.py preview` and `apply` no longer keep a tracked task worktree for the
reason `registered worktree <primary checkout>` when the worktree sits inside the primary
checkout, such as `<primary>/.claude/worktrees/<name>` (#1307). It now takes the same
identity, head, status, ignored-content, dependency and retention checks as a worktree
outside the repository. Two new kept reasons can appear:
`the primary checkout tracks content at the worktree's path`, and `cannot read what the
primary checkout tracks at the worktree's path: …`. If you have a test or a script that
expects such a worktree to stay `kept`, update it. A worktree under or holding another
registered worktree is still kept.
