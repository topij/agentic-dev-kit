## Lane launcher stops its child's process group through the shared runner

CHANGED (gate semantics, #1508). Refresh `launch_lane.py`, `lib/subprocess_runner.py`
and `tests/test_lane_launcher.py` together: the launcher now imports the runner's
process-group functions, and the tests no longer find `_process_group_exists`,
`_wait_for_process_group_exit` or `_ForkedChild.poll`/`wait`.

The launcher holds the child unreaped until the last signal or probe names its group,
then reaps it. Two refusals change:

- A group answered with `EPERM` whose only other members are zombies is now stopped,
  not refused with `cannot signal the child process group`. A live member the
  launcher may not signal is still refused.
- When the group's members cannot be listed (no `/proc` on Linux, or `/bin/ps` fails
  on macOS), the launch fails with `cannot observe the child process group: …` in its
  receipt, and the group is still stopped.
