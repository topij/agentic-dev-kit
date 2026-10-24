## Lane sessions resolve from the primary checkout; the board gains RUN and OVERLAP

CHANGED (engine CLI surface): `dev_session.sh` and `reconcile_sessions.sh` default the
sessions directory to `dev-model-sessions/` beside the repository's **primary**
worktree, the first entry of `git worktree list`, instead of beside the checkout the
engine was invoked from (#479). `dev_session.sh pr-watch <scope>` now works from inside
a lane worktree. If you ran either engine from a linked worktree without
`DEVKIT_SESSIONS_DIR`, sessions it created sat beside that worktree; set
`DEVKIT_SESSIONS_DIR` to that directory to keep reaching them, or finish them first.
A bare primary keeps the old default.

CHANGED (report shape): `dev_session.sh list` and `list --watch` print two new columns,
`RUN` and `OVERLAP`, between `DIRTY` and `SANDBOX`. A script that parses the board by
column position must take the sandbox path from the eighth column instead of the
sixth. `list --watch` also marks a row when either new cell changes.

ADDED (engine CLI surface): `pr_watch.py` prints a warning on stderr when it reads the
repo-root `state/` while a lane session holds watch state for the same PR (#563). Its
report and exit code are unchanged.
