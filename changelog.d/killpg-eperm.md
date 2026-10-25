## Lanes: an exited lane's process group is no longer refused on macOS

CHANGED (gate semantics): on macOS, `killpg` answers EPERM, not ESRCH, when a process
group's only member is the lane's leader that the wrapper has not reaped yet. That
includes a leader still exiting. The lane launcher used to treat that as a refusal
(`cannot signal the child process group`, or `cannot force-stop the child process
group`). An interrupted lane was still recorded `interrupted`. But the launch round's
final text and denials went unrecorded, and so did its `returncode` when the leader was
still exiting (an already-exited leader is reaped while the refusal is recorded). A
resume round kept `error: round did not finish` instead of `launcher interrupted`.
`scripts/launch_lane.py` now waits up to `parallel.termination_grace_seconds` for an
exited or exiting leader to become reapable, reaps it, and asks again. A group that is
then gone is not refused. A group that still answers EPERM after the reap, or one whose
leader is still running when the grace ends, is refused as before. Each signal can now
spend up to one grace on that wait, so a termination that ends in a refusal can take up
to four graces where it took two.

`scripts/tests/test_lane_launcher.py` now requires the interrupted resume round's
`error` to be `launcher interrupted`. That assertion depends on timing. The tests with
a patched `killpg` discriminate the change on any platform. The forked test of a group
holding only the unreaped leader discriminates it on macOS only, because other
platforms do not answer EPERM there. Take both files together.
