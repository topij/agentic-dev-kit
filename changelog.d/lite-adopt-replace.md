## Lite profile: pull-request repositories, repository sources, adopt's replace option

ADDED: the optional lite config key `vcs.protected_branch`, the branch that takes
changes only through pull requests. With it set, the lite `wrap-up` commits on a session
branch when that branch is checked out, then pushes and opens or updates the pull
request. An absent key now means the repository takes direct commits: the lite
`wrap-up` commits to the branch checked out and no longer asks each run. A key that is
present but null, blank, a `<placeholder>`, or no branch here stops the lite `wrap-up`.
A lite repository whose branch takes changes only through pull requests must set the
key; `adopt.md`'s *Lite profile* L1 now asks for it.

ADDED: repository sources. A lite repository lists the reads it adds to
`session-start` or `wrap-up` in its `AGENTS.md` section, under the workflow's name;
both lite docs read them as sources, with the source-failure rule. Move reads kept
elsewhere for the lite workflows (a local command, a note) into that section.

ADDED: `adopt.md`'s *Lite profile* L1 offers **replace** beside **keep** for a
`session-start`, `wrap-up` or `review` the repository already has. Replace gives each
of its extra items a home (usually a repository source in `AGENTS.md`); the operator
removes the repository's binding, a command file or a whole skill directory, and the
workflow stages a tracked one's removal with the install. The workflow deletes nothing
of the repository's itself.

CHANGED: the L3 copy block skips a Claude skill while `.claude/commands/<slug>.md`
exists, printing `collision: <path>`, where it installed the skill beside the command
and shadowed it. It strips every trailing slash from `REPO`: a `REPO` given with one,
for a repository reached through a symlinked ancestor, had every target skipped. A
lite repository installed before this change that has a command shadowed by a kit skill of the same name chooses
keep or replace for it now.

CHANGED: `session-start`, full and lite, puts high-severity friction entries in 🟡
Soon, and an entry that says it blocks work in 🔴 Now. Neither said where a high
entry went before.
