## Lanes: an exited lane's process group is no longer refused on macOS

CHANGED (gate semantics): on macOS, `killpg` answers EPERM, not ESRCH, when a process
group's only member is the lane's leader that the wrapper has not reaped yet. That
includes a leader still exiting. The lane launcher used to treat that as a refusal
(`cannot signal the child process group`, or `cannot force-stop the child process
group`). An interrupted lane was still recorded `interrupted`. But the launch round's
`returncode`, final text and denials went unrecorded, and a resume round kept
`error: round did not finish` instead of `launcher interrupted`.
`scripts/launch_lane.py` now waits up to `parallel.termination_grace_seconds` for an
exited or exiting leader to become reapable, reaps it, and asks again. A group that is
then gone is not refused. A group that still answers EPERM after the reap, or one whose
leader is still running when the grace ends, is refused as before.

`scripts/tests/test_lane_launcher.py` now requires the interrupted resume round's
`error` to be `launcher interrupted`. That assertion depends on timing. Forked
process-group tests and tests with a patched `killpg` cover the change
deterministically. Take both files together.
