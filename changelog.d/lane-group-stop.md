## Lane launcher stops its child's process group through the shared runner

CHANGED (gate semantics, #1508). Refresh `launch_lane.py`, `lib/subprocess_runner.py`
and `tests/test_lane_launcher.py` together: the launcher now imports the runner's
process-group functions, and the tests no longer find `_process_group_exists`,
`_wait_for_process_group_exit` or `_ForkedChild.poll`/`wait`.

The launcher holds the child unreaped until the last signal or probe names its group,
then reaps it. This supersedes `killpg-eperm.md`'s account of the launcher: on EPERM
it no longer reaps the child and asks again. It waits up to the grace for the child to
exit, then asks whether a live member is left. Two refusals change:

- A group answered with `EPERM` whose only other members are zombies is now stopped,
  not refused with `cannot signal the child process group`. A live member the
  launcher may not signal is still refused.
- When the group's members cannot be listed (no `/proc` on Linux, or `/bin/ps`
  failing on macOS, which every clean exit there now asks), the launch fails. The
  receipt's error starts with `cannot observe the child process group: …`, followed
  by the stop's own refusal. Both signals are still sent. Because the stop cannot
  list the group either, it then refuses with `child process group survived forced
  termination`, leaves the child unreaped, and the receipt's `returncode` is null.
