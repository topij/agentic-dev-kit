## PR watch state in linked cockpit worktrees

BREAKING (gate semantics) — A linked cockpit now reads existing receipts from the
primary checkout by default. A receipt held only in the linked checkout needs
the explicit state root described below.

Install the watcher with its sibling `lib/state_paths/` package. Run the watch
loop for a PR from any linked cockpit worktree of the same repository. The
default receipt, acknowledgements and settle baseline live under
`state/pr-watch/` in the primary checkout. Serialize operations for each PR.

For an in-flight review whose only receipt is in the previous linked checkout,
finish its watch loop with `DEVKIT_STATE_ROOT` set to the absolute path of that
checkout’s `state/`. New reviews can use the shared default. Continue to use
the scoped cockpit wrapper for lanes. For a bare repository or a layout where
Git cannot identify a primary checkout, specify the same absolute state root
in each cockpit to share its watch state.

CHANGED (config keys) — Add the installed paths of
`<engine-dir>/lib/state_paths/resolver.py` and
`<engine-dir>/lib/state_paths/repo_root.py` to `review.safety_critical_paths`.
List both in the safety-critical section of your adopter-owned `AGENTS.md` and
in the `paths` list of your Claude rule at `.claude/rules/safety-critical-changes.md`.
