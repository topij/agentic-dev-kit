# Capability-tier calibration design — 2026-08-27

## Slice boundary

This design calibrates the runtime-neutral tiers (`models.tiers`) for Claude Code and
Codex from observed client behaviour, and declares, beside every config key that
selects compute, whether that key is **mechanical** or **advisory** on each runtime
(`#605`, `#255`). It retires the "Claude's delegation tool takes NO per-agent effort
parameter" sentences wherever the live record refutes them, and leaves them wherever
it does not.

It does not build `#621`'s durable evidence-bundle mechanism, run the first real
headless task on the generalised launcher, change lane identity, environment
replacement, transports, approval policy, or the receipt chain established by `#609`,
`#611`, and `#614`, decide Claude's shipped permissions as repository policy (`#606`),
or generate adapters. `scripts/launch_lane.py` is under
`docs/agentic-dev-kit/safety-critical-changes.md`; this slice changes it only if a
matrix row below is accepted that requires it, and the current plan is that none does:
the launcher keeps inheriting the runtime's own compute, and the calibration records
what "inherit" resolves to under each trust route.

Parity here means equivalent **tier outcomes** and **honest control semantics**, not
identical model names or CLI shapes.

## Vocabulary

A key's status on a runtime is one of:

- **mechanical-observed** — the value is passed to a client control by a launcher or
  by the cockpit's tool call, the client accepts it, and an observer independent of the
  prompt reads the applied value back.
- **mechanical-accepted** — the client accepts and validates the value (an invalid
  spelling is refused), but no independent observer reads the applied value back. The
  control is real; its effect is not separately evidenced.
- **advisory** — the value is rendered into a prompt or a document and a person or an
  agent may apply it. Nothing enforces it.
- **unavailable** — the surface exposes no such control.

A value *rendered into a prompt* (`panel_prompt.py`'s `Run at:` line, the hook's
`Run each lens at …` clause) is advisory on every runtime by construction. A value
*passed as argv or as a tool parameter* is mechanical only once the probe shows the
client honours it. The two are never conflated in a receipt or a doc.

## Product surface inventory

Quoted from each client's `--help` on 2026-08-27. `claude --version` printed
`2.1.247 (Claude Code)`; `codex --version` printed `codex-cli 0.149.1`. The help text
supplies candidate controls; only the probes below supply behaviour.

- `claude --help`: `--model <model>` ("Model for the current session. Provide an alias
  for the latest model (e.g. 'fable', 'opus', or 'sonnet') …"); `--effort <level>`
  ("Effort level for the current session (low, medium, high, xhigh, max)");
  `--agents <json>` ("JSON object defining custom agents"); `--agent <agent>`;
  `--debug-file <path>`; `--output-format json|stream-json`; `--verbose`;
  `--setting-sources`, `--settings`, `--bare`.
- Claude Code's in-session delegation tool (`Agent`), as presented to this session:
  a `model` parameter with the enumeration `sonnet`, `opus`, `haiku`, `fable`, and no
  `effort` parameter. Its description states that a named agent type's "model,
  reasoning effort, and tools come from its definition (`.claude/agents/*.md`
  frontmatter or SDK `agents`)". That sentence is the claim the Claude probes test.
- `codex --help` / `codex exec --help`: `-m, --model <MODEL>`; `-c, --config
  <key=value>` (dotted config override); `-p, --profile`; `--json` (JSONL events);
  `--ephemeral` (no rollout on disk); `--ignore-user-config`; no reasoning-effort flag
  is listed. `~/.codex/config.toml` on this machine carries `model` and
  `model_reasoning_effort` keys, so the effort control candidate is the config key
  passed through `-c model_reasoning_effort=<level>`.
- `codex exec review --help`: the same `-m` and `-c` surface for a review run.

## Config-key inventory

Every key below selects compute or names a tier. Consumers are enumerated, never
counted; the grep that established each list is
`grep -rn <key> scripts/ init.sh config/ docs/ .claude .agents` at `16b07d6`.

| Key | Shipped value | Consumers that read it | What the consumer does with it |
| --- | --- | --- | --- |
| `models.tiers.{cheap,default,expensive}` | `mechanical` / `standard` / `judgment` | shared workflows (`session-start`, `parallel`, `triage-friction-log`, `post-merge-systemize`) | a vocabulary for planning tags; no engine reads it |
| `models.runtime_mappings.claude.*` | `haiku` / `sonnet` / `opus` | `init.sh` (migration write), `test_portability.py` (migration pin); no engine | none — the cockpit applies it by hand |
| `models.runtime_mappings.codex.*` | `low` / `medium` / `high` | same | none — the operator applies it by hand |
| `review.fallback_panel.lens_compute.claude.model` | `sonnet` | `scripts/panel_prompt.py` (renders `Run at:`), `scripts/hooks/pr_followup_hook.py` (renders the reminder clause), `kit_doctor.py` (tracks the hook) | rendered into text; the cockpit passes it to the `Agent` tool's `model` parameter by hand |
| `review.fallback_panel.lens_compute.claude.effort` | `high` | same | rendered into text only |
| `review.fallback_panel.lens_compute.codex.effort` | `high` | same, keyed `codex` | rendered into text; a Codex cockpit runs `codex exec` with whatever it chooses |
| `review.fallback_panel.lens_compute.codex.model` | absent | same | — |
| `systemize.analysis_tier`, `triage.analysis_tier` | tier names | their workflows | instructed guidance by declaration already |
| `parallel.<runtime>_headless_command` | `[claude, -p]` / `[codex, exec]` | `scripts/launch_lane.py` | argv prefix; carries no model or effort |

## Design matrix

Config key × runtime × launch surface × model control × effort control ×
mechanical/advisory status × authoritative observer × durable evidence × unavailable
or false-success outcome. "Observed" cells are filled by the live record; this table
declares what each cell must contain and how it fails.

| Key | Runtime | Launch surface | Model control | Effort control | Status to declare | Authoritative observer | Durable evidence | Unavailable / false-success outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lens_compute.claude.model` | Claude | cockpit → `Agent` tool (inline subagent per lens) | `model` parameter | none on the tool | mechanical-observed if the subagent's turns report the selected model id; else mechanical-accepted | stream-json assistant events carrying `parent_tool_use_id` and `message.model`; `result.modelUsage` keys | the probe transcript with the sha and date | tool refuses an unknown alias → lens not launched; a resolved id differing from the alias's documented target is recorded as `substituted`, never as applied |
| `lens_compute.claude.effort` | Claude | cockpit → `Agent` tool | — | none on the tool | advisory on this surface whatever the frontmatter probe shows | — | — | a receipt must not imply enforcement on this surface |
| `lens_compute.claude.{model,effort}` | Claude | cockpit → `Agent` tool with `subagent_type` naming a `.claude/agents/<lens>.md` whose frontmatter carries `model` and `effort` | frontmatter `model` | frontmatter `effort` | mechanical-observed for each key only if an independent observer reads the applied value back; mechanical-accepted if the client validates the field but nothing reads it back; advisory if the field is ignored | debug log of the API request (`--debug-file`) or stream-json init/assistant fields, whichever carries the field | the probe transcript | a definition added after session start not being loaded → `unavailable` for the running session, not a failure of the key; an invalid `effort` spelling accepted silently → `ignored`, and the key stays advisory |
| `lens_compute.claude.{model,effort}` | Claude | `claude -p --model <m> --effort <e>` (a separate headless session per lens) | `--model` | `--effort` | mechanical-observed / mechanical-accepted by the same rule | `result.modelUsage`; debug log for effort | the probe transcript | `--effort bogus` refused → the control validates; accepted-but-unobservable → mechanical-accepted |
| `lens_compute.codex.effort` (and an absent `model`) | Codex | cockpit → `codex exec -m <m> -c model_reasoning_effort=<e> -` (a separate session per lens) | `-m` | `-c model_reasoning_effort=` | mechanical-observed if the rollout's `turn_context` (or the `--json` stream) carries `model` and `effort` equal to the argv; mechanical-accepted if the client validates but nothing reads back | the runtime's own rollout under `~/.codex/sessions/` (never `--ephemeral`, which writes none); the `--json` event stream | the probe transcript with rollout excerpts | a misspelled `-c` key accepted silently and the observer showing the config default → `ignored` (the false-success row; the hostile control) ; an invalid effort value refused → validates |
| `lens_compute.codex.*` | Codex | `codex exec review` | `-m` | `-c` | same rule as `codex exec` | same | same | same |
| `runtime_mappings.claude.*` | Claude | operator or cockpit applying a tier: `--model`/`--effort` at launch, `/model` in session, `Agent` `model` parameter for a delegate | alias names | effort levels | advisory (no engine consumer); the *values* must name controls the client accepts, verified live | `result.modelUsage` for each alias | the probe transcript | an alias the client does not resolve is removed from the shipped mapping; the mapping never names a value the client refuses |
| `runtime_mappings.codex.*` | Codex | operator applying a tier: `codex -m`/`-c model_reasoning_effort=` at launch | inherited from `config.toml` unless `-m` | effort levels | advisory (no engine consumer); values verified live as accepted effort spellings | rollout `turn_context.effort` | the probe transcript | a level the client refuses is removed from the mapping |
| `parallel.claude_headless_command` (lane) | Claude | `launch_lane.py` → `claude -p --setting-sources "" --settings <profile> …` | none carried | none carried | inherited by design (unchanged); the record states what "inherit" resolves to under the trust route | `result.modelUsage` of a lane-shaped invocation | the probe transcript | the trust route dropping the user's `model` setting means the lane runs the product default, which the record names rather than assumes |
| `parallel.codex_headless_command` (lane) | Codex | `launch_lane.py` → `codex exec --sandbox … --cd … -` | none carried | none carried | inherited by design (unchanged); `#620` observed user `config.toml` reaching untrusted lanes, so the lane's model/effort are the user's | rollout `turn_context` | `#620`'s record (historical) | unchanged |
| any prompt-rendered value (`Run at:`, hook clause) | both | prompt text | — | — | advisory by construction | — | — | never written into a receipt as enforced |

## Terminal outcomes (total)

For any (key, runtime, surface) cell the live record assigns exactly one of these:

| Outcome | Condition | What the config comment and the parity row say |
| --- | --- | --- |
| `applied` | control accepted; observer reads back the configured value | mechanical-observed |
| `substituted` | control accepted; observer reads back a different concrete id than the alias names (an alias resolving to a dated model id is `applied`, not this) | mechanical-observed, with the substitution named |
| `accepted-unobserved` | control accepted and validated (an invalid spelling is refused); no independent observer exists for the applied value | mechanical-accepted |
| `ignored` | control accepted without error; observer shows the inherited value | the key stays advisory on that surface; the false-success row |
| `refused` | client refuses the value | the shipped value is changed or the surface is marked unavailable for that value |
| `inherited` | surface carries no such control; observer names what the session actually ran | unavailable on that surface; the inherited value is recorded, not the config value |
| `instructed` | value reaches the agent only as prompt text | advisory |
| `unobservable` | the probe could not run or the observer field is absent | the cell keeps its previous status; nothing is promoted |

No cell is left blank, and no cell is promoted from `instructed` or `unobservable` on
the strength of documentation alone.

## Probe plan

Each probe is run from this Claude Code session at `2.1.247` / `codex-cli 0.149.1`
on 2026-08-27, in a fresh fixture directory under the session scratchpad, with the
command and its raw output captured. The live record quotes the commands and the
observer fields; it does not paraphrase them.

### Claude

- **C1 — alias resolution.** `claude -p --output-format json --model <alias> "reply
  ok"` for `haiku`, `sonnet`, `opus`, `fable`. Observer: `result.modelUsage` keys.
  Decides which aliases the shipped `runtime_mappings.claude` may name.
- **C2 — session effort validation.** `claude -p --effort bogus` must refuse;
  `--effort low` must run. Observer for the applied level: `--debug-file` contents
  searched for the effort field, and the stream-json init event. If neither carries
  it, the outcome is `accepted-unobserved`.
- **C3 — agent-definition frontmatter.** A fixture project with
  `.claude/agents/probe.md` carrying `model: haiku` and `effort: low` (and a control
  agent with neither), driven by `claude -p --output-format stream-json --verbose` with
  a prompt that spawns each agent. Observer: assistant events with
  `parent_tool_use_id` and their `message.model`; the debug log for effort. Decides
  whether kit-owned agent definitions make `lens_compute.claude` mechanical.
- **C4 — in-session `Agent` tool.** From this session, spawn a subagent with
  `model: haiku` and have it return `claude --version`-independent evidence it cannot
  fabricate: nothing. So C4 is observed through the same stream-json route as C3 by
  running the parent headlessly; the in-session tool is the same surface.
- **C5 — lane trust route inheritance.** `claude -p --setting-sources "" --settings
  config/claude-lane-settings.json --output-format json "reply ok"` with the user
  settings carrying a `model`. Observer: `result.modelUsage`. Records what a lane
  actually runs.

### Codex

- **X1 — model and effort argv.** `codex exec -m <model> -c
  model_reasoning_effort=<level> --json --skip-git-repo-check -` in the fixture, for
  each level in `runtime_mappings.codex` plus `xhigh` and `minimal`. Observer: the
  rollout file's `turn_context` entry (`model`, `effort`) and the `--json` stream.
- **X2 — hostile control.** The same with `-c model_reasoning_effrot=low` (misspelled
  key). The observer must show the config-default effort, not `low`; if the client
  refuses the unknown key, that is recorded instead.
- **X3 — invalid value.** `-c model_reasoning_effort=bogus`. Expected: refused.
- **X4 — `codex exec review`.** One run with `-m` and `-c` to confirm the review
  surface takes the same controls.

### What each probe cannot establish

- A Codex cockpit spawning `codex exec` as a nested child under its own sandbox is not
  probed here; this session is Claude Code, and the Codex cockpit path stays declared
  as unobserved.
- Effort's *effect* (that the model reasoned more or less) is not an observation any
  probe here makes; only the applied parameter is.

## Calibration rules

- A shipped `runtime_mappings` value must be a spelling the client accepted in the
  probe. `expensive` on Claude points at the top alias the client resolves at the
  stamped version; if `fable` resolves, `expensive: fable`, else it stays `opus`.
- `lens_compute.claude` keeps `sonnet`/`high` (the `#219` measurement stands; this
  slice re-measures nothing about cost). Its status line changes only as the probes
  dictate.
- `lens_compute.codex` gains a `model` key only if the probe shows `-m` is applied and
  the record can name a model the adopter's account is likely to have; otherwise it
  stays effort-only and inherits the user's model, which is what `#620` observed.
- If C3 shows agent-definition `effort` is applied, the kit ships one
  `.claude/agents/<lens>.md` per configured lens, generated from
  `lens_compute.claude`, with a test that refuses drift between the two. If C3 shows
  it is accepted but unobservable, the same files ship with the comment saying so. If
  C3 shows it is ignored, no agent files ship and the "no per-agent effort" sentence is
  rewritten to name the surface it is true on rather than deleted.
- Every config comment, the panel doc, and the parity rows state the declared status
  per key per runtime using the vocabulary above, stamped with the client version and
  date of the probe that established it.

## Ownership boundary

- `#605` — this slice.
- `#255` — the per-key per-runtime declaration is made here; a `kit_doctor` check that
  the declaration is present is proposed there, not built here.
- `#621` — durable evidence bundles; this record's raw probe output is kept under
  `saved_plans/` as excerpts and is not promoted beyond what the excerpts show.
- The first real headless task — the next slice, no tracker item.
