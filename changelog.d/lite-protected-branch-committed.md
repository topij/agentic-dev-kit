## Lite wrap-up: `vcs.protected_branch` is read as committed, and a key outside the lite schema stops it

CHANGED (gate semantics): the lite `wrap-up` now reads `vcs.protected_branch` from the
committed config (`HEAD`, or the index on a branch with no commit yet) as well as from
the working tree (#1377). Before, it read only the working tree, so an unstaged edit
that deleted the key committed straight to the branch the key protects. The protected
branch is the one either copy names, and two copies naming different branches is a
hard stop. A committed config that Git cannot show was already a hard stop through the
risk tier's read.

CHANGED (gate semantics): a key outside the lite config schema, at any level and in
either copy, is now a hard stop for the lite `wrap-up`. The schema is `profile`,
`kit.version`, `paths.handoff`, `paths.friction_log`, `friction.down_route`,
`review.safety_critical_paths` and `vcs.protected_branch`, and a bare optional
section (`vcs:`) still reads as absent. A misspelled or misplaced key, such as
`protected-branch`, `vsc:` or a `protected_branch` dedented out of `vcs`, used to read
as absent, which committed to the branch checked out.

CHANGED: the way out of a config hard stop, in the lite `wrap-up` and the risk tier in
`lite-review.md`, commits the corrected config on a new branch with a pull request,
unless the operator says the branch checked out takes direct commits. It used to be a
plain commit on the branch checked out.

What to do: on a lite repository, remove every key the schema above does not list, and
commit `config/dev-model.yaml` with the values you want before the next wrap-up. The
lite `session-start` reports a key outside the schema as a 🔴 Now item.
