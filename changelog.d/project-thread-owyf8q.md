## Lane usage report: rank lanes by recorded tokens and cost

ADDED (engine CLI surface): `<engine-dir>/lane_usage.py`, a read-only report over the
lane sessions directory (`--sessions-dir`, default `$DEVKIT_SESSIONS_DIR` or the one
`dev_session.sh` uses). For each `launch-receipt-*.json` it sums the runtime-reported
`terminal.usage` over the launch round and every `terminal.resumes[].usage`, and,
separately, the subagent transcripts under `--projects-root` (default
`$CLAUDE_PROJECTS_DIR` or `~/.claude/projects`) for the session ids the receipt names.
Options: `--since <date>`, `--rank-by result-tokens|subagent-tokens|cost`, `--json`,
`--strict` (exit 1 when no lane had figures from either source). A bad `--since` or an
unresolvable sessions directory exits 2. Each `--json` lane row carries flat `tokens`,
`cost_usd` and `subagent_tokens`, each None when its source has no figures;
`subagent_tokens` is also None when a session or transcript the lane had could not be
read. A missing or non-directory `--sessions-dir` exits 2.

Nothing to change to keep working: no receipt shape, config key or gate changes. Run
`init.sh` (or `/upgrade`) to install the engine and its test. The report never adds the
two sources together, and a lane with no figures is listed with a reason rather than as
zero; a per-lane budget (`#1174` stays open for it) is not part of this.
