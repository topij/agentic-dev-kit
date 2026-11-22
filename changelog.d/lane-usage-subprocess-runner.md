## `lane_usage.py` finds the sessions directory through the shared primary-checkout resolver

CHANGED (engine CLI): without `--sessions-dir` or `DEVKIT_SESSIONS_DIR`,
`lane_usage.py` now finds the primary checkout with
`scripts/lib/state_paths/repo_root.py`'s `primary_worktree`, the resolver
`pr_watch.py` uses. An inherited `GIT_DIR` or `GIT_COMMON_DIR` no longer points
it at another repository's `dev-model-sessions/`.

What to do: refresh `scripts/lane_usage.py` together with the
`scripts/lib/state_paths/` package. `lane_usage.py` now imports it, and a copy
of the engine without it fails at start.
