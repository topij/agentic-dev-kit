## PR watch state in linked cockpit worktrees

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

Include the package’s `resolver.py` and `repo_root.py` in
`review.safety_critical_paths` for your engine layout. These files select the
source of a merge-authorizing review receipt.
