## The session archiver's recovery hint runs Git through the shared subprocess runner

CHANGED (engine CLI). Refresh `archive_plan_sessions.py` and `lib/subprocess_runner.py`
together, at or after the runner that added `without_git_environment` and the
`CommandError` family: the archiver now imports both at load time, so it fails at
import beside an older runner or without one.

The recovery hint is printed when a sweep's write fails. Its three Git reads now run
without inherited `GIT_*` variables. Before, a `GIT_DIR`, `GIT_WORK_TREE` or
`GIT_OBJECT_DIRECTORY` inherited from a hook or a calling Git made them answer for
another repository or tree, so the hint fell back to "No committed Git version could be
confirmed" for a handoff that was committed. Exit codes and both messages are unchanged. The reads are now text in the locale's
encoding, so a handoff path that holds a carriage return, or that a non-UTF-8 locale
reads differently from the filesystem path, now gets the fallback instead of a
`git show` command.
