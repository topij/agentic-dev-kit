## The session archiver's recovery hint runs Git through the shared subprocess runner

CHANGED (engine CLI). Refresh `archive_plan_sessions.py` and `lib/subprocess_runner.py`
together, at or after the runner that added `without_git_environment` and the
`CommandError` family: the archiver now imports both at load time, so it fails at
import beside an older runner or without one.

The recovery hint is printed when a sweep's write fails. Its three Git reads now run
without inherited `GIT_*` variables. Before, a `GIT_DIR` or `GIT_INDEX_FILE` inherited
from a hook or a calling Git could make them answer for another repository, so the hint
fell back to "No committed Git version could be confirmed" for a handoff that was
committed. Exit codes and both messages are unchanged. A handoff path that does not
decode as text, or that holds a carriage return, now gets the fallback instead of a
`git show` command.
