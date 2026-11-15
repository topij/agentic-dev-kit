## Lane usage report: rank lanes by recorded tokens and cost

ADDED (engine CLI surface): `<engine-dir>/lane_usage.py`, a read-only report over the
lane sessions directory (`--sessions-dir`, default `$DEVKIT_SESSIONS_DIR` or the one
`dev_session.sh` uses). For each `launch-receipt-*.json` it sums the runtime-reported
`terminal.usage` over the launch round and every `terminal.resumes[].usage`, and,
separately, the subagent transcripts under `--projects-root` (default
`$CLAUDE_PROJECTS_DIR` or `~/.claude/projects`) for the session ids the receipt names.
Options: `--since <date>`, `--rank-by result-tokens|subagent-tokens|cost`, `--json`,
`--strict` (exit 1 when no lane had a complete figure from either source). A bad `--since` or an
unresolvable sessions directory exits 2. Each `--json` lane row carries flat `tokens`,
`cost_usd` and `subagent_tokens`, each None when its source has no figures and also
None when its sum is only a lower bound. For `tokens` and `cost_usd` that means a round
of the lane (the launch or a resume) did not report that metric; the result object
says which in `tokens_complete`, `cost_complete` and `reason`. For `subagent_tokens` it
means a session, a directory listing, a transcript, a line or a token field the lane
had could not be read; the subagent object carries `complete: false` and `reason`. A
partial figure ranks as unavailable, does not satisfy `--strict`, and shows in the
text report as `>=N part` (tokens) or `>=N` (cost). `tokens` is None for a cost-only
result. A missing or non-directory `--sessions-dir` exits 2.

Nothing to change to keep working: no receipt shape, config key or gate changes. Run
`init.sh` (or `/upgrade`) to install the engine and its test. The report never adds the
two sources together, and a lane with no figures is listed with a reason rather than as
zero; a per-lane budget (`#1174` stays open for it) is not part of this.
