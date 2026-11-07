## Lite wrap-up: `vcs.protected_branch` is read from every copy, and a key outside the lite schema stops it

BREAKING (gate semantics): the lite `wrap-up` now reads `vcs.protected_branch` from
the committed config (`HEAD`, or the index on a branch with no commit yet), the staged
copy and the working tree (#1377), and reads the staged copy again just before it
commits. Before, it read only the working tree, so an unstaged edit that deleted the key
committed straight to the branch the key protects. The protected branch is the one any
copy names, and copies naming different branches are a hard stop. A committed config
that Git cannot show was already a hard stop through the risk tier's read.

BREAKING (gate semantics): a key outside the lite config schema at any level, or a key
given twice at one level, in any copy, is now a hard stop for the lite `wrap-up`. The
schema is `profile`, `kit.version`, `paths.handoff`, `paths.friction_log`,
`friction.down_route`, `review.safety_critical_paths` and `vcs.protected_branch`.
`paths` is a mapping, and `kit`, `friction`, `review` and `vcs` are each a mapping or
null, so a bare `vcs:` still reads as absent. A misspelled, misplaced or repeated key,
such as `protected-branch`, `vsc:`, a `protected_branch` dedented out of `vcs`, or a
second `vcs:`, used to read as absent, which committed to the branch checked out.

CHANGED (gate semantics): a `vcs.protected_branch` value holding a character other than
ASCII letters, digits, `.`, `_`, `/` and `-`, or one `git check-ref-format --branch`
rejects, is unusable and stops the wrap-up. A branch now counts as present when it
exists locally or on any remote, not only on `origin`.

CHANGED: the way out of these stops, and of the risk tier's unreadable-config stop in
`lite-review.md`, commits the corrected config on a new branch with a pull request,
unless the operator says the branch checked out takes direct commits. It used to be a
plain commit on the branch checked out. `adopt.md`'s lite re-run now judges an existing
config by these stops and commits the correction with the install.

What to do: on a lite repository, before the next wrap-up, make every copy of
`config/dev-model.yaml` match the schema above, and commit it:

- delete each key the schema does not list, or move its value to a file of the
  repository's own when something there reads it;
- remove a repeated key;
- replace a `kit`, `friction`, `review` or `vcs` that is neither a mapping nor null (for
  example `vcs: main`) with a mapping (`vcs:` then `  protected_branch: main`) or with
  null;
- give `vcs.protected_branch` a plain branch name that exists locally or on a remote.

The lite `session-start` reports each of these as a 🔴 Now item.
