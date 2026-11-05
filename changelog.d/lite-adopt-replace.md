## Lite adopt: replace an existing command with the kit's skill

ADDED: `adopt.md`'s *Lite profile* L1 offers **replace** beside **keep** for a
`session-start`, `wrap-up` or `review` the repository already has. Replace lists what
the repository's file does beyond the lite doc, gives each item a home (usually a
repository source in `AGENTS.md`), and removes the file in the install commit.

CHANGED: the L3 copy block skips a Claude skill while `.claude/commands/<slug>.md`
exists, printing `collision: <path>`, where it installed the skill beside the command.
It strips a trailing slash from `REPO`, so a repository reached through a symlinked
ancestor is no longer skipped whole. A repository already installed needs nothing; one
that kept a command next to a kit-installed skill of the same name chooses keep or
replace now.
