## Lanes: an exited lane's process group is no longer refused on macOS

CHANGED (gate semantics): on macOS, `killpg` answers EPERM, not ESRCH, when a process
group's only member is the lane's leader that the wrapper has not reaped yet. The lane
launcher used to record that as a refusal (`cannot signal the child process group`, or
`cannot force-stop the child process group`), so an interrupted lane whose process had
already exited could be recorded `failed`, or a resume round could keep
`round did not finish`. `scripts/launch_lane.py` now waits up to
`parallel.termination_grace_seconds` for an exited or exiting leader to become
reapable, reaps it, and asks again: a group that is then gone is not refused. A group
that still answers EPERM after the reap, or one whose leader is still running when the
grace ends, is refused as before. Take `scripts/launch_lane.py`
together with `scripts/tests/test_lane_launcher.py`, which pins the interrupted resume
round's `error` to `launcher interrupted` again.
