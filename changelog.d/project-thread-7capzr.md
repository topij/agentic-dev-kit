## Session cleanup runs Git through the shared subprocess runner

CHANGED (engine CLI, #1219). Refresh `session_cleanup.py` and
`lib/subprocess_runner.py` together: the cleanup engine now imports the runner, so
an older runner beside it fails at import. `lib/subprocess_runner.py` adds the
`CommandError` family (`CommandTimedOut`, `CommandUnavailable`, `CommandFailed`),
all `RuntimeError` subclasses with unchanged messages, plus optional `env` and
`cwd=None` arguments. A caller that catches `RuntimeError` needs no change.
`session_cleanup.py`'s exit codes and per-item outcomes are unchanged. The reason
text for a Git timeout, or a Git that cannot start, now comes from the runner
(`git -C <path> … timed out after 30s`, `… could not run: <cause>`), so a script
matching Python's own `TimeoutExpired` wording there needs updating.
