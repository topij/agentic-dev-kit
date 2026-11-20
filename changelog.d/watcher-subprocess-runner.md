## Watcher errors when GitHub CLI cannot start

CHANGED (engine CLI, #414). Refresh `pr_watch.py` and
`lib/subprocess_runner.py` together. If `gh` cannot start after backend
selection, commands that require its output report the failure on stderr and
exit with status 2. Optional check-identity lookups keep their empty result.

CHANGED (gate semantics, #414). Include `lib/subprocess_runner.py` alongside
the watcher in `review.safety_critical_paths` and your runtime review bindings
so edits to its subprocess handling receive the same review.
