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
- When the group's members cannot be listed (no `/proc` on Linux, `/bin/ps`
  failing on macOS, which every clean exit there now asks, or the listing raising
  an OS error such as `EMFILE`), the launch fails. The receipt's error starts with
  `cannot observe the child process group: …`. A stop that still cannot list the
  group refuses too, leaves the child unreaped, and the receipt's `returncode` is
  null. On Linux the stop sends both signals and adds `child process group
  survived forced termination`. On macOS the exited child's group answers EPERM,
  so the stop adds the same `cannot observe …` text again and sends no SIGKILL,
  which would meet the same EPERM.
- `subprocess_runner.wait_group_empty` and `stop_group` count a listing that raises
  an OS error as a group that still has a live member, as they already counted
  `GroupObserverUnavailable`, rather than raise it. A wait then runs out its
  timeout, so the launcher's stop still waits the grace before SIGKILL. A caller
  that caught `OSError` from either gets `False` or `GroupStop(stopped=False)`
  instead.
- When the child's exit cannot be observed (an OS error from `waitid` or
  `kqueue`), the launch fails with `cannot observe the child's exit: …`.
- An OS error raised by a stop on the failure path is added to the receipt's
  error, rather than raised past the receipt, which left none.

On Linux with `/proc` mounted `hidepid`, a group member owned by another user is
not seen, so a clean exit can pass with that member running. The launcher used to
catch it through its signal-0 probe after reaping the child; with the child held,
that probe succeeds on the child itself and cannot. #1520 tracks it.
