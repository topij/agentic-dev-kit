## Lite wrap-up: `vcs.protected_branch` is read as committed, and another key under `vcs` stops it

CHANGED (gate semantics): the lite `wrap-up` now reads `vcs.protected_branch` from the
committed config (`HEAD`, or the index on a branch with no commit yet) as well as from
the working tree (#1377). Before, it read only the working tree, so an unstaged edit
that deleted the key committed straight to the branch the key protects. When the two
copies differ, the wrap-up says so and treats the branch checked out as protected if
either copy names it. A committed config that Git cannot show was already a hard stop
through the risk tier's read.

CHANGED (gate semantics): a `vcs` key that is neither null nor a mapping, or a mapping
that holds any key other than `protected_branch`, in either copy, is now a hard stop for
the lite `wrap-up`. A bare `vcs:` still means no protected branch. A
misspelling such as `protected-branch` read as an absent key, which commits to the
branch checked out.

What to do: on a lite repository, remove every key under `vcs` except
`protected_branch`, and commit `config/dev-model.yaml` with the key you want before the
next wrap-up. The lite `session-start` reports another key under `vcs` as a 🔴 Now item.
