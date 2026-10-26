## Session cleanup: per-worktree Git timeout outcomes

Read each path outcome and `complete` after applying a cleanup session. A Git
inspection or removal timeout now keeps that worktree with its error and lets
unrelated eligible paths proceed. Worktree removal has a bounded 300-second
wait; identity probes retain their 30-second bound. A kept outcome still needs
inspection and an explicit retry. Existing ownership and evidence checks apply.
