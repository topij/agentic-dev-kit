## Lite profile: pull-request repositories, repository sources, and a bucket for high-severity friction

ADDED: the optional lite config key `vcs.protected_branch`, the branch that takes
changes only through pull requests. With it set, the lite `wrap-up` commits on a session
branch when that branch is checked out, then pushes and opens or updates the pull
request. Without it, the lite `wrap-up` commits to the branch checked out and no longer
asks each run whether that branch takes pull requests. A lite repository that takes
changes through pull requests sets the key; `adopt.md`'s *Lite profile* L1 now asks.

ADDED: repository sources. A lite repository lists the reads it adds to
`session-start` or `wrap-up` in its `AGENTS.md` section, under the workflow's name;
both lite docs read them as sources, with the source-failure rule. Move reads kept
elsewhere for the lite workflows (a local command, a note) into that section.

CHANGED: `session-start`, full and lite, puts high-severity friction entries in 🟡
Soon, and an entry that says it blocks work in 🔴 Now. Neither said where a high
entry went before.
