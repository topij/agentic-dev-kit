## Lanes: a linked cockpit worktree can issue a headless lane; `dev_session.sh <subcommand> --help`

CHANGED (gate semantics): `scripts/launch_lane.py` holds a lane to its repository by
Git common directory instead of by checkout path. A descriptor issued by
`dev_session.sh new --headless` from a linked worktree used to be refused with
`child observation disagrees on repo_root`. It now launches, and a lane worktree that
belongs to any other repository is still refused, now as
`child observation disagrees on git_common_dir`. The descriptor is unchanged, so this
needs only `scripts/launch_lane.py`. A lane issued from a linked worktree gets that
worktree as `DEVKIT_ROOT`, so its read-only prod-state fallback is the cockpit
worktree's `state/`, as an interactive lane created from a linked worktree already had.

CHANGED (report / return shape): the launch receipt's `expected` and `observed` maps
carry `git_common_dir`, and `observed` no longer carries `repo_root`. `expected.repo_root`
is unchanged. If you read the receipt's `observed.repo_root`, read
`observed.git_common_dir` instead: it is the lane worktree's Git common directory,
which is the primary checkout's `.git` directory, not a checkout.

CHANGED (CLI surface): `dev_session.sh <subcommand> --help` (or `-h`) as the first
argument prints that subcommand's usage line and exits 0 without creating anything.
For most subcommands it used to exit 1 with `unknown flag: --help`, or a slug error.
`print-contract --help` used to print the whole lane contract and exit 0; it now prints
the usage line, so call `print-contract` with no arguments to get the contract. Later
in the line `--help` keeps its old meaning. `dev_session.sh help` now prints the whole
header comment, which adds the paragraph on where sessions live.

A configured `parallel.<runtime>_headless_command` the launcher cannot resolve is still
refused. For a bare command name the message now names the trusted directories and the
remedy: for a user-local runtime install, link the binary into one of those directories
on the host (`parallel-headless.md`). For an absolute command, which is used as written
and never looked up, it names the file. The local overlay still does not accept these
keys.
