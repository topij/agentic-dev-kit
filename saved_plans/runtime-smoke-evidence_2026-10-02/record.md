# Runtime smoke record — 2026-10-02

Written by `scripts/runtime_smoke.py` at kit revision `0c2c2009c8e84d3e016f303d9a9542cd1b5662b6`, run `adk-smoke-0cl1hxzt`, started 2026-10-02T14:17:23Z and finished 2026-10-02T14:22:57Z (UTC). Every row below is an observation at the clients and revision named here.

Invocation, as the runner's arguments, under `~/.cache/uv/environments-v2/runtime-smoke-106a2fd21d154242/bin/python3`:

```text
scripts/runtime_smoke.py --work-root '<work-root>' --out '<out>' --codex-bin /opt/homebrew/bin/codex --codex-version 0.153.4 --codex-home '<codex-home>' --claude-bin '~/.local/bin/claude' --claude-version 2.1.287 --claude-config-dir '<claude-config>' --allow-codex-project-trust --allow-codex-hook-trust-bypass
```

## Clients

| Runtime | Binary | Shell `--version` | Pin | Executing runtime, per row | Preflight |
|---|---|---|---|---|---|
| codex | `/opt/homebrew/Caskroom/codex/0.153.4/bin/codex` | `codex-cli 0.153.4` | `0.153.4` | `0.153.4` | ready |
| claude | `~/.local/share/claude/versions/2.1.287` | `2.1.287 (Claude Code)` | `2.1.287` | `2.1.287` | ready |

## Results

| Row | Check | Result | Evidence or reason |
|---|---|---|---|
| `codex.instructions` | AGENTS.md discovery | **passed** | the injected AGENTS.md block names the fixture and equals its AGENTS.md byte for byte |
| `codex.skills` | repository skill discovery | **passed** | every skill the parity declaration binds for Codex is listed in the injected skills block |
| `codex.session_start` | SessionStart hook | **passed** | the tripwire line naming this run's over-budget count reached the session |
| `codex.post_tool_use` | PostToolUse hook | **passed** | the follow-up hook's warning reached the session after the shell call that printed the nonce URL |
| `codex.review` | native review (`codex exec review`) | **passed** | the rollout recorded review mode and the review returned its output |
| `codex.panel` | configured fallback panel | **passed** | every configured lens ran at its configured compute and returned a report naming the review head |
| `codex.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |
| `claude.instructions` | CLAUDE.md and its AGENTS.md import | **passed** | the runtime loaded the fixture's CLAUDE.md, and AGENTS.md as its import |
| `claude.commands` | command and lens-agent discovery | **passed** | every declared command and every configured lens agent was loaded |
| `claude.session_start` | SessionStart hook | **passed** | the tripwire line naming this run's over-budget count was the SessionStart hook's output |
| `claude.post_tool_use` | PostToolUse hook | **passed** | a PostToolUse hook event after the shell call that printed the nonce URL carried the hook's warning |
| `claude.review` | configured review command | **passed** | the configured review command was invoked, by the transcript's record, and returned a non-error result |
| `claude.panel` | configured fallback panel | **passed** | each configured lens ran as its agent definition, on the rendered prompt, at its configured compute, and returned a report naming the review head |
| `claude.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |

## Fixture and observations

- Fixture: `d0c38c7c483743c5d0043f4596090beec9a08971` (the revision's tree plus the controls commit), review head `9a8cd3bb4bc85157d0b86449c486ea450d389fbf` on `smoke-review`.
- SessionStart control: `docs/kit-friction-log.md` committed at 162 lines against a budget of 150.
- Codex hook probe trust: project trust per-invocation override; definition trust per-invocation bypass.
- Trusted-project entries the run added to the isolated Codex home (#802): none.
- Hook-state entries the run added to the isolated Codex home: none.
- Instruction files above the fixture, which a client walking upward could also load: none.

`record.json` beside this file carries each row's evidence fields, the session fields read from the runtime's artifacts, and every invocation with its exit status and timeout.
