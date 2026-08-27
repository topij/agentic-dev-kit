# Capability-tier calibration — live record — 2026-08-27

Companion to
[`capability-tier-calibration-design_2026-08-27.md`](capability-tier-calibration-design_2026-08-27.md),
which declares the matrix these observations fill. Every claim below is an
observation at the stamped clients on 2026-08-27, from a Claude Code session on
`main` at `16b07d64cddd085c1075ba4cd6a1570961ea80d0`, against a scratch fixture
under the session scratchpad (a fresh `git init` directory with one empty commit,
outside every repository). It is not a guarantee for other client versions, other
models, or other accounts.

`claude --version` printed `2.1.247 (Claude Code)`. `codex --version` printed
`codex-cli 0.149.1`. The user-level Claude settings on this machine carry
`model: opus` and `effortLevel: xhigh`; the user-level Codex config carries
`model = "gpt-5.6-sol"` and `model_reasoning_effort = "high"`. Both matter below
because "inherit" resolves to them or does not, depending on the trust route.

## Observers

Nothing here is read from a prompt, a child's prose, or the value the caller passed.

- **Claude, model and effort.** The runtime's own session transcript under
  `~/.claude/projects/<encoded-cwd>/<session_id>.jsonl` carries, on each
  `assistant` entry, `message.model` (the resolved model id) and a top-level
  `effort` field. Subagent transcripts sit beside it under
  `<session_id>/subagents/agent-<id>.jsonl` with the same fields and
  `isSidechain: true`. The `--output-format json` result's `modelUsage` keys name
  every model the session touched, which is weaker: `claude-haiku-4-5-20251001`
  appeared in every run's `modelUsage`, including runs whose transcript shows only
  one other model, so `modelUsage` cannot attribute a model to a subagent. The
  `--debug-file` log names each API request's source (`source=agent:custom:<name>`)
  and the model it dispatched to, but carries no effort field even under `-d api`.
  The stream-json `system/init` event carries `model` and the loaded `agents` list,
  and no effort field.
- **Codex, model and effort.** The runtime's rollout under
  `~/.codex/sessions/<date>/rollout-*-<thread_id>.jsonl` carries a `turn_context`
  entry whose payload names `model` and `effort` (and `approval_policy`,
  `sandbox_policy`). The `--json` event stream carries `thread.started` with the
  thread id and nothing about model or effort. `--ephemeral` writes no rollout, so
  the observer is unavailable for an ephemeral lens.

The observer was validated before it was trusted: with `--effort low` passed, the
transcript read `low`; with no effort passed, it read the default; with the
runtime's warned-and-ignored `--effort bogus`, it read the default and not `bogus`.

## Claude probes

Each command ran in the fixture directory with the prompt on stdin unless shown as
an argument. `<S>` is the session scratchpad.

### C1 — alias resolution (`--model`)

`claude -p --output-format json --model <alias> --setting-sources "" "reply with the
single word ok"`, one run per alias. Transcript `(model, effort)` per run:

| alias | transcript |
| --- | --- |
| `haiku` | `('claude-haiku-4-5-20251001', None)` |
| `sonnet` | `('claude-sonnet-5', 'high')` |
| `opus` | `('claude-opus-5', 'high')` |
| `fable` | `('claude-fable-5', 'high')` |

Every alias resolved; `is_error` was `False` on each. Haiku 4.5 carries no effort
field — effort is a per-model capability, which is why the C3 control below had to
run on a model that has one.

`claude -p --output-format json --setting-sources "" --model no-such-model-zzz`
(C10) exited 1 with `[claude-code:unrecognized_model]` on stderr and
`is_error: true`, `modelUsage []`. A bogus model is refused loudly.

### C2 — session effort (`--effort`)

- `--effort bogus`: exit **0**; stderr printed `Warning: Unknown --effort value
  'bogus' — ignoring it and using the default effort. Valid values: low, medium,
  high, xhigh, max.`; the transcript read `('claude-opus-5', 'high')`. **An invalid
  session effort is warned and ignored, not refused** — a launcher that passes
  `--effort` must validate the spelling itself and read stderr.
- `--effort low --model sonnet` (two runs, one `--output-format json` with `-d api
  --debug-file`, one `stream-json --verbose --debug-file`): the transcript read
  `('claude-sonnet-5', 'low')` in both. The debug file (`-d api`) had no line
  matching `effort|thinking|budget|reasoning`; the init event's keys were
  `agents, analytics_disabled, apiKeySource, capabilities, claude_code_version, cwd,
  fast_mode_disabled_reason, fast_mode_state, mcp_servers, memory_paths,
  messaging_socket_path, model, output_style, permissionMode, plugins,
  product_feedback_disabled, session_id, skills, slash_commands, subtype,
  terminal_slash_commands, tools, type, uuid` — `model = claude-sonnet-5`, no
  effort. The result's `usage.output_tokens_details.thinking_tokens` was `0` on a
  one-word reply, which is not an effort observation.

### C3 — agent-definition frontmatter

Fixture `.claude/agents/` carried these definitions (each with `tools: Bash` and a
one-line body):

| file | frontmatter |
| --- | --- |
| `probe.md` | `model: haiku`, `effort: low` |
| `control.md` | neither |
| `probe-sonnet-low.md` | `model: sonnet`, `effort: low` |
| `probe-sonnet-noeffort.md` | `model: sonnet` |
| `probe-nomodel-low.md` | `effort: low` |
| `probe-sonnet-max.md` | `model: sonnet`, `effort: max` |
| `probe-bogus.md` | `model: sonnet`, `effort: bogus` |

Parent: `claude -p --output-format stream-json --verbose --model sonnet
--permission-mode dontAsk --allowedTools Agent --debug-file <S>/out/c3*.debug` with
the prompt on stdin ("Use the Agent tool … run the agent named '<name>' with the
prompt: reply with the single word ok …"). Project settings sources were loaded
(no `--setting-sources` flag), so the init event's `agents` list read
`['claude', 'control', 'Explore', 'general-purpose', 'Plan', 'probe',
'statusline-setup']` in the first run.

Subagent transcripts, `(model, effort)`:

| agent | parent effort | subagent transcript |
| --- | --- | --- |
| `probe` (haiku, low) | `xhigh` | `('claude-haiku-4-5-20251001', None)` |
| `control` (neither) | `xhigh` | `('claude-sonnet-5', 'xhigh')` |
| `probe-sonnet-low` | `xhigh` | `('claude-sonnet-5', 'low')` |
| `probe-sonnet-noeffort` | `xhigh` | `('claude-sonnet-5', 'xhigh')` |
| `probe-nomodel-low` | `xhigh` | `('claude-sonnet-5', 'low')` |
| `probe-sonnet-max` | `xhigh` | `('claude-sonnet-5', 'max')` |
| `probe-bogus` (C9; parent `--effort medium`) | `medium` | `('claude-sonnet-5', 'medium')` |

The parent's `xhigh` in the first runs is the user setting `effortLevel: xhigh`
reaching a session whose settings sources were loaded; under `--effort medium` it
read `medium`. **Frontmatter `model` and `effort` are applied.** An absent key
inherits the parent's value. For `probe-bogus`, the debug log carried `Agent file
…/probe-bogus.md has invalid effort 'bogus'. Valid options: lo…` and the agent ran at
the parent's `medium` with nothing on stderr and exit 0 — **an invalid frontmatter
effort is silently inherited** unless someone reads a debug log.

`agent_completion` lines in the debug log named each `agentType`, and each API
request line named `source=agent:custom:<name>`, which is how a subagent transcript
was matched to its definition.

### C11 — quoted frontmatter values

Run after the panel's adversarial lens showed that a `model` value carrying `:`
rendered bare breaks the frontmatter. Two definitions with JSON-quoted values,
`model: "haiku"` / `effort: "low"` and `model: "sonnet"` / `effort: "low"`, launched
from a parent at `--model sonnet --effort medium`:

| agent | subagent transcript |
| --- | --- |
| `probe-quoted` | `('claude-haiku-4-5-20251001', None)` |
| `probe-quoted-sonnet` | `('claude-sonnet-5', 'low')` |

The runtime applies a quoted frontmatter value, so the generator renders `model` as
a quoted YAML string.

### C6 — the delegation tool's `model` parameter

Parent `--model sonnet --effort medium`, project sources loaded, prompt asking for
three `Agent` calls. Tool-call inputs read from the stream:

| call | `subagent_type` | `model` parameter | subagent transcript |
| --- | --- | --- | --- |
| 1 | `general-purpose` | `haiku` | `('claude-haiku-4-5-20251001', None)` |
| 2 | `probe-sonnet-low` | `haiku` | `('claude-haiku-4-5-20251001', None)` |
| 3 | `general-purpose` | none | `('claude-sonnet-5', 'medium')` |

The tool's `model` parameter is applied and **overrides a definition's `model`**;
the tool has no `effort` parameter, and a plain subagent inherits the parent's model
and effort.

### C7 — `--agents` JSON under the lane trust route

`claude -p … --setting-sources "" --settings <repo>/config/claude-lane-settings.json
--permission-mode dontAsk --allowedTools Agent --agents '{"jprobe":{"description":…,
"prompt":…,"model":"sonnet","effort":"low","tools":["Bash"]}}'`: the init event's
`agents` read `['claude', 'Explore', 'general-purpose', 'jprobe', 'Plan',
'statusline-setup']` — the fixture's `.claude/agents/` definitions were **not**
loaded under `--setting-sources ""` (C2b's init event, under the same flag, listed
only the built-ins), while the JSON agent was. Its subagent transcript read
`('claude-sonnet-5', 'low')`; the parent read `('claude-sonnet-5', 'high')`.

### C5 — what a lane inherits

| invocation | transcript |
| --- | --- |
| `--setting-sources "" --settings <profile> --permission-mode dontAsk`, no model/effort | `('claude-opus-5', 'high')` |
| default sources, no model/effort | `('claude-opus-5', 'xhigh')` |
| trust route plus `--model sonnet --effort low` | `('claude-sonnet-5', 'low')` |

Under the wrapper's trust route the user's `effortLevel: xhigh` is not loaded (the
lane ran `high`), and argv still controls both. Whether the `opus` in the first row
is the product default or the user's `model: opus` leaking through cannot be told
apart from these two rows alone — both show `opus` — so this record says only that
the *effort* setting demonstrably did not load, and that a lane wanting a specific
model passes `--model`.

### The in-session probe

From this cockpit session, a definition written to the repository's
`.claude/agents/tier-hotreload-probe.md` and then launched with the `Agent` tool
returned `Agent type 'tier-hotreload-probe' not found. Available agents: claude,
claude-code-guide, Explore, general-purpose, Plan, statusline-setup`. The debug log
of the headless runs says the runtime is "Watching for changes in skill/command
directories: … .claude/agents", but a definition added after session start was not
launchable in the turn that wrote it. The file was removed afterwards.

The same session then refined that: after the shipped `.claude/agents/adversarial.md`
and `correctness.md` were committed at `55a843e`, the cockpit was told, some turns
later, that both agent types were now available, and a fresh headless session in the
repository at `4a574d4` listed `['adversarial', 'claude', 'correctness', 'Explore',
'general-purpose', 'Plan', 'statusline-setup']` in its init event. **The roster is
listed at session start and refreshed at some later point in a running session; the
refresh was not launchable in the turn that wrote the file, and this record does not
pin when it happens.** Count on a definition from the next session; treat an earlier
listing as a bonus.

## Codex probes

Each command: `printf 'reply with the single word ok' | codex exec --json --sandbox
read-only --cd <fixture> <flags> -`, with the rollout located by the `thread.started`
thread id.

### X0 / X1 — `-m` and `-c model_reasoning_effort=`

| flags | exit | rollout `turn_context` |
| --- | --- | --- |
| none | 0 | `model gpt-5.6-sol, effort high` (the user config) |
| `-m gpt-5.6-sol -c model_reasoning_effort=minimal` | 1 | `effort minimal`; `turn.failed`: API `invalid_request_error` `unsupported_value` — "'minimal' is not supported with the 'gpt-5.6-sol-1p-codexswic-ev3' model. Supported values are: 'none', 'low', 'medium', 'high', 'xhigh', and 'max'." |
| `… =low` | 0 | `effort low` |
| `… =medium` | 0 | `effort medium` |
| `… =high` | 0 | `effort high` |
| `… =xhigh` | 0 | `effort xhigh` |
| `… =max` | 0 | `effort max` |
| `… =none` | 0 | `effort none` |

The client wrote the requested level into the rollout in every case, including the
one the API then refused; the applied level is therefore the rollout's value **and**
a completed turn.

### X2 — the hostile control (misspelled key)

`-m gpt-5.6-sol -c model_reasoning_effrot=low`: exit **0**, stderr empty, a completed
turn, rollout `effort high`. **A misspelled `-c` key is accepted silently and the
session runs at the config default.** The rollout is what catches it; nothing at the
argv or exit-code layer does.

### X3 / X5 — invalid value, bogus model

- `-c model_reasoning_effort=bogus`: exit 1, `turn.failed`, API
  `[ReasoningEffortParam] [reasoning.effort] [invalid_enum_value] Invalid value:
  'bogus'`; rollout `effort bogus` (the client passed it through).
- `-m no-such-model-zzz -c model_reasoning_effort=low`: exit 1, API "The
  'no-such-model-zzz' model is not supported when using Codex with a ChatGPT
  account."; rollout `model no-such-model-zzz, effort low`.

### X4 — `codex exec review`

`codex exec --json --cd <fixture> review --uncommitted -m gpt-5.6-sol -c
model_reasoning_effort=low` (with an uncommitted file present; `--cd` must precede
`review` — placed after it, the client exits 2 with `unexpected argument '--cd'`):
exit 0. The parent thread's rollout had no `turn_context`; a second rollout whose
`session_meta` reads `source: {'subagent': 'review'}` carried `turn_context`
`model gpt-5.6-sol, effort low, approval_policy never`. The review surface takes the
same controls, applied in the review subagent's thread.

### X6 — `--ephemeral`

`--ephemeral -m gpt-5.6-sol -c model_reasoning_effort=low`: exit 0, a completed turn,
and no rollout for the thread id. The observer is unavailable; an ephemeral lens
cannot have its compute read back.

### The panel's own lenses, read back

The fallback panel that reviewed this PR is the mechanism in use. Round 1 at
`4a574d4` launched both lenses as plain `general-purpose` subagents with `model:
sonnet` on the delegation tool, before this session's roster listed the shipped
definitions; round 2 at `e128cdc` launched them as the kit-owned `adversarial` and
`correctness` agents. The cockpit session's subagent transcripts (`(model, effort)`
per assistant entry, read on 2026-08-27):

| round | launch | adversarial | correctness |
| --- | --- | --- | --- |
| 1 | `general-purpose`, tool `model: sonnet` | `('claude-sonnet-5', 'xhigh')` | `('claude-sonnet-5', 'xhigh')` |
| 2 | kit-owned agent named after the lens | `('claude-sonnet-5', 'high')` | `('claude-sonnet-5', 'high')` |

Round 1 inherited the cockpit's `xhigh`; round 2 ran at the frontmatter's `high`.
That is `lens_compute.claude.effort` advisory on the tool surface and mechanical
through the definition, observed in a real panel rather than a fixture.

## Matrix results

Vocabulary from the design: `applied`, `substituted`, `accepted-unobserved`,
`ignored`, `refused`, `inherited`, `instructed`, `unobservable`.

| Key | Runtime | Surface | Outcome | Declared status |
| --- | --- | --- | --- | --- |
| `lens_compute.claude.model` | Claude | `Agent` tool `model` parameter | `applied` (C6) | mechanical-observed |
| `lens_compute.claude.model` | Claude | `.claude/agents/<lens>.md` frontmatter | `applied` (C3); overridden by the tool parameter when both are given (C6) | mechanical-observed |
| `lens_compute.claude.effort` | Claude | `Agent` tool, plain subagent | `inherited` (C6 call 3) | advisory on this surface — the tool has no effort parameter |
| `lens_compute.claude.effort` | Claude | `.claude/agents/<lens>.md` frontmatter | `applied` (C3b); an invalid level is `ignored` with a debug-only log (C9) | mechanical-observed; the generator validates the level |
| `lens_compute.claude.{model,effort}` | Claude | `--agents` JSON at launch | `applied`, also under `--setting-sources ""` (C7) | mechanical-observed |
| `lens_compute.claude.{model,effort}` | Claude | `claude -p --model/--effort` | `applied` (C1, C2, C5); an invalid `--effort` is `ignored` with a stderr warning at exit 0 (C2a); a bogus `--model` is `refused` at exit 1 (C10) | mechanical-observed |
| `lens_compute.claude.*` | Claude | a definition added after session start | `unavailable` in the turn that wrote it; listed later in the same session, timing unpinned | count on it from the next session |
| `lens_compute.codex.effort` | Codex | `codex exec -c model_reasoning_effort=` | `applied` for low, medium, high, xhigh, max, none (X1); `refused` by the API for minimal on this model and for `bogus` (X1, X3); a misspelled key is `ignored` at exit 0 (X2) | mechanical-observed |
| `lens_compute.codex.model` | Codex | `codex exec -m` | `applied` (X1); a bogus model `refused` at exit 1 (X5); absent → `inherited` from the user config (X0) | mechanical-observed when set |
| `lens_compute.codex.*` | Codex | `codex exec review` | `applied` in the review subagent thread (X4) | mechanical-observed |
| `lens_compute.codex.*` | Codex | `--ephemeral` | `unobservable` (X6) | do not use for a lens |
| `runtime_mappings.claude.*` | Claude | operator/cockpit-applied | values `applied` as aliases (C1) | advisory; no engine consumer |
| `runtime_mappings.codex.*` | Codex | operator-applied | values `applied` as levels (X1) | advisory; no engine consumer |
| `parallel.claude_headless_command` | Claude | wrapper trust route | `inherited`: `opus`/`high`, with the user's `effortLevel` demonstrably not loaded (C5) | unchanged; the wrapper carries no control |
| `parallel.codex_headless_command` | Codex | wrapper | `inherited` from the user config (X0 here; `#620`'s record) | unchanged |
| prompt `Run at:` line | both | prompt text | `instructed` | advisory by construction |

## What moved, and what did not

- The blanket sentence "Claude's delegation tool takes NO per-agent effort
  parameter" was **half right**: true for the tool's parameters (C6), false as a
  statement that per-agent effort is unavailable (C3b, C7). The config comments, the
  panel doctrine, `init.sh`, and the parity rows now say which surface each half is
  true on.
- `runtime_mappings.claude.expensive` moved `opus` → `fable` and
  `runtime_mappings.codex.expensive` moved `high` → `xhigh`, each to the top of what
  its client accepted on this date. Both remain advisory: no engine reads the map.
- `lens_compute` values did not move. Their status did: `claude.effort` from
  advisory to mechanical through the agent definition, `codex.effort` from
  instructed to mechanical on the argv.
- The kit now ships `.claude/agents/<lens>.md` per configured lens, generated by
  `panel_prompt.py --agent-definition`, seeded by `init.sh`, and pinned by tests to
  the generator's output. The Codex binding names the argv carrier.
- Not observed, and not claimed: a Codex cockpit spawning `codex exec` lenses under
  its own sandbox; effort's effect on reasoning as opposed to the applied parameter;
  whether the lane's `opus` under the trust route is the product default or a
  leaked user setting.

## Cleanup

The fixture and its `.claude/agents/` definitions live under the session scratchpad
and were not committed anywhere. The throwaway `.claude/agents/tier-hotreload-probe.md`
written into this repository for the in-session probe was removed before any commit;
`git status` at the first commit of this slice shows only the intended files. The
Codex rollouts and Claude transcripts the observers read remain in each runtime's own
session store on this machine; they are not part of the repository and this record
quotes them as excerpts (`#621` owns the durable-bundle mechanism).
