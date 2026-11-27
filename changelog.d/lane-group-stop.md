## Lane launcher stops its child's process group through the shared runner

CHANGED (gate semantics, #1508). Refresh `launch_lane.py`, `lib/subprocess_runner.py`,
`tests/test_lane_launcher.py` and `tests/test_process_group_stop.py` together: the
launcher now imports the runner's process-group functions, its tests no longer
find `_process_group_exists`, `_wait_for_process_group_exit` or
`_ForkedChild.poll`/`wait`, and `test_process_group_stop.py`'s guard now refuses an
`os.killpg` call in `launch_lane.py`.

The launcher holds the child unreaped until the last signal or probe names its group,
then reaps it. This supersedes `killpg-eperm.md`'s account of the launcher: on EPERM
it no longer reaps the child and asks again. It waits up to the grace for the child to
exit, then asks whether a live member is left. These refusals change:

- A group answered with `EPERM` whose only other members are zombies is now stopped,
  not refused with `cannot signal the child process group`. A live member the
  launcher may not signal is still refused.
- When the group's members cannot be listed (no `/proc` on Linux, or `/bin/ps`
  failing on macOS, which every clean exit there now asks), the launch fails. The
  receipt's error starts with `cannot observe the child process group: …`, and the
  stop that follows cannot list the group either, so it refuses too, leaves the
  child unreaped, and the receipt's `returncode` is null. On Linux the stop sends
  both signals and adds `child process group survived forced termination`. On
  macOS the exited child's group answers EPERM, so the stop adds the same `cannot
  observe …` text again and sends no SIGKILL, which would meet the same EPERM.
- An observer that fails with an OS error, of the group or of the child's exit,
  now fails the launch with `cannot observe the child process group: …` or `cannot
  observe the child's exit: …` and writes the receipt. An OS error raised by the
  stop on that path is added to the receipt's error rather than raised past it.

On Linux with `/proc` mounted `hidepid`, a group member owned by another user is
not seen, so a clean exit can pass with that member running. The launcher used to
catch it through its signal-0 probe after reaping the child; with the child held,
that probe succeeds on the child itself and cannot. #1520 tracks it.
