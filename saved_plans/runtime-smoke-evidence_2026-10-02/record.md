# Runtime smoke record — 2026-10-02

Written by `scripts/runtime_smoke.py` at kit revision `64526e1d6c357735317b5d151a56feb80612c098`, run `adk-smoke-lpgam5d5`, started 2026-10-02T10:21:56Z and finished 2026-10-02T10:27:12Z (UTC). Every row below is an observation at the clients and revision named here.

Invocation:

```text
uv run scripts/runtime_smoke.py --work-root '<work-root>' --out '<out>' --codex-bin /opt/homebrew/bin/codex --codex-version 0.153.4 --codex-home '<codex-home>' --claude-bin '~/.local/bin/claude' --claude-version 2.1.287 --claude-config-dir '<claude-config>' --allow-codex-project-trust --allow-codex-hook-trust-bypass
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
| `codex.panel` | configured fallback panel | **passed** | every configured lens ran at its configured compute and reported on the review head |
| `codex.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |
| `claude.instructions` | CLAUDE.md and its AGENTS.md import | **passed** | the runtime loaded the fixture's CLAUDE.md and the AGENTS.md it imports |
| `claude.commands` | command and lens-agent discovery | **passed** | every declared command and every configured lens agent was loaded |
| `claude.session_start` | SessionStart hook | **passed** | the tripwire line naming this run's over-budget count was the SessionStart hook's output |
| `claude.post_tool_use` | PostToolUse hook | **passed** | the follow-up hook's warning was the PostToolUse output for the shell call that printed the nonce URL |
| `claude.review` | configured review command | **passed** | the configured review command ran and returned a review |
| `claude.panel` | configured fallback panel | **passed** | each configured lens ran as its agent definition, on the rendered prompt, at its configured compute, and reported on the review head |
| `claude.lane` | parallel lane through `launch_lane.py` | **passed** | the launcher completed the lane in its worktree and bound the final text |

## Fixture and observations

- Fixture: `24a1145af6f5441773e0840378ebb20d9cfb9b47` (the revision's tree plus the controls commit), review head `91d9d3f89a98866a6ee747d3a401ef5638777e37` on `smoke-review`.
- SessionStart control: `docs/kit-friction-log.md` committed at 182 lines against a budget of 150.
- Codex hook probe trust: project trust per-invocation override; definition trust per-invocation bypass.
- Trusted-project entries the run added to the isolated Codex home (#802): none.
- Hook-state entries the run added to the isolated Codex home: none.
- Instruction files above the fixture, which a client walking upward could also load: none.

`record.json` beside this file carries each row's evidence fields, the session fields read from the runtime's artifacts, and every invocation with its exit status and timeout.
