## Lanes: a linked cockpit worktree can issue a headless lane; `dev_session.sh <subcommand> --help`

CHANGED (gate semantics): `scripts/launch_lane.py` holds a lane to its repository by
Git common directory instead of by checkout path. A descriptor issued by
`dev_session.sh new --headless` from a linked worktree used to be refused with
`child observation disagrees on repo_root`. It now launches, and a lane worktree that
belongs to any other repository is still refused, now as
`child observation disagrees on git_common_dir`. The descriptor is unchanged, so this
needs only `scripts/launch_lane.py`.

CHANGED (report / return shape): the launch receipt's `expected` and `observed` maps
carry `git_common_dir`, and `observed` no longer carries `repo_root`. `expected.repo_root`
is unchanged. If you read the receipt's `observed.repo_root`, read
`observed.git_common_dir` instead: it is that checkout's `.git` directory, not the
checkout.

CHANGED (CLI surface): `dev_session.sh <subcommand> --help` (or `-h`) as the first
argument prints that subcommand's usage line and exits 0 without creating anything.
It used to exit 1 with `unknown flag: --help`, or a slug error. Later in the line
`--help` keeps its old meaning.

A configured `parallel.<runtime>_headless_command` the launcher cannot resolve is still
refused, and the message now names the trusted directories and the remedy. For a
user-local runtime install, link the binary into one of those directories on the host
(`parallel-headless.md`). The local overlay still does not accept these keys.
