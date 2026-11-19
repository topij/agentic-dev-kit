## Watcher errors when GitHub CLI cannot start

Refresh `pr_watch.py` and `lib/subprocess_runner.py` together. If `gh` cannot
start after backend selection, commands that require its output report the
failure on stderr and exit with status 2. Optional check-identity lookups keep
their empty result. Include the runner alongside the watcher in your
`review.safety_critical_paths` and runtime review bindings.
