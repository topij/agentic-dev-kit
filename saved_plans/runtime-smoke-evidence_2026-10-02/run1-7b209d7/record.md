# Runtime smoke record — 2026-10-02

Written by `scripts/runtime_smoke.py` at kit revision `7b209d78e088c3a54a2d48f0d342d15580698408`, run `adk-smoke-76ih37g5`, started 2026-10-02T09:50:51Z and finished 2026-10-02T09:54:48Z (UTC). Every row below is an observation at the clients and revision named here.

Invocation:

```text
uv run scripts/runtime_smoke.py --work-root '<work-root>' --out '<out>' --codex-bin /opt/homebrew/bin/codex --codex-version 0.153.4 --codex-home '<codex-home>' --claude-bin '~/.local/bin/claude' --claude-version 2.1.287 --claude-config-dir '<claude-config>' --allow-codex-hook-trust-bypass
```

## Clients

| Runtime | Binary | Shell `--version` | Pin | Executing runtime, per row | Preflight |
|---|---|---|---|---|---|
| codex | `/opt/homebrew/Caskroom/codex/0.153.4/bin/codex` | `codex-cli 0.153.4` | `0.153.4` | `0.153.4` | ready |
| claude | `~/.local/share/claude/versions/2.1.287` | `2.1.287 (Claude Code)` | `2.1.287` | `2.1.287` | ready |

## Results

| Row | Check | Result | Evidence or reason |
|---|---|---|---|
| `codex.instructions` | AGENTS.md discovery | **failed** | no injected AGENTS.md block both named the fixture and equalled its AGENTS.md |
| `codex.skills` | repository skill discovery | **passed** | every skill the parity declaration binds for Codex is listed in the injected skills block |
| `codex.session_start` | SessionStart hook | **failed** | hooks ran under the bypass but the tripwire line never reached the session |
| `codex.post_tool_use` | PostToolUse hook | **failed** | the shell call ran but the hook's warning never reached the session |
| `codex.review` | native review (`codex exec review`) | **failed** | the rollout recorded no review-mode event |
| `codex.panel` | configured fallback panel | **passed** | every configured lens ran at its configured compute and reported on the review head |
| `codex.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |
| `claude.instructions` | CLAUDE.md and its AGENTS.md import | **passed** | the runtime loaded the fixture's CLAUDE.md and the AGENTS.md it imports |
| `claude.commands` | command and lens-agent discovery | **passed** | every declared command and every configured lens agent was loaded |
| `claude.session_start` | SessionStart hook | **passed** | the tripwire line naming this run's over-budget count was the SessionStart hook's output |
| `claude.post_tool_use` | PostToolUse hook | **passed** | the follow-up hook's warning was the PostToolUse output for the shell call that printed the nonce URL |
| `claude.review` | configured review command | **failed** | the configured review command was not listed, not invoked, or returned nothing |
| `claude.panel` | configured fallback panel | **failed** | adversarial: applied efforts ['medium'], configured 'high'; correctness: applied efforts ['medium'], configured 'high' |
| `claude.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |

## Fixture and observations

- Fixture: `d0d57784622db0e117f189a52ce91c651a554ed3` (the revision's tree plus the controls commit), review head `466fbb20ad0d8b5472f48bf22f64e01255e60d21` on `smoke-review`.
- SessionStart control: `docs/kit-friction-log.md` committed at 237 lines against a budget of 150.
- Codex hook-trust route: bypass.
- Trusted-project entries the run added to the isolated Codex home (#802): none.
- Hook-state entries the run added to the isolated Codex home: none.
- Instruction files above the fixture, which a client walking upward could also load: none.

`record.json` beside this file carries each row's evidence fields, the session fields read from the runtime's artifacts, and every invocation with its exit status and timeout.
