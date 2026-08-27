---
workflow_contract:
  - name: session-start
    status: aligned
    shared: docs/agentic-dev-kit/workflows/session-start.md
    claude: .claude/commands/session-start.md
    codex: .agents/skills/session-start/SKILL.md
  - name: wrap-up
    status: aligned
    shared: docs/agentic-dev-kit/workflows/wrap-up.md
    claude: .claude/commands/wrap-up.md
    codex: .agents/skills/wrap-up/SKILL.md
  - name: pr-watch
    status: aligned
    shared: docs/agentic-dev-kit/workflows/pr-watch.md
    claude: .claude/commands/pr-watch.md
    codex: .agents/skills/pr-watch/SKILL.md
  - name: parallel
    status: aligned
    shared: docs/agentic-dev-kit/workflows/parallel.md
    claude: .claude/commands/parallel.md
    codex: .agents/skills/parallel/SKILL.md
  - name: adopt
    status: aligned
    shared: docs/agentic-dev-kit/workflows/adopt.md
    claude: .claude/commands/adopt.md
    codex: .agents/skills/adopt/SKILL.md
  - name: upgrade
    status: aligned
    shared: docs/agentic-dev-kit/workflows/upgrade.md
    claude: .claude/commands/upgrade.md
    codex: .agents/skills/upgrade/SKILL.md
  - name: triage-friction-log
    status: aligned
    shared: docs/agentic-dev-kit/workflows/triage-friction-log.md
    claude: .claude/commands/triage-friction-log.md
    codex: .agents/skills/triage-friction-log/SKILL.md
  - name: post-merge-systemize
    status: aligned
    shared: docs/agentic-dev-kit/workflows/post-merge-systemize.md
    claude: .claude/commands/post-merge-systemize.md
    codex: .agents/skills/post-merge-systemize/SKILL.md
  - name: parallel-headless
    status: companion
    shared: docs/agentic-dev-kit/workflows/parallel-headless.md
    claude: null
    codex: null
    loaded_by: parallel
---

# Runtime parity contract

This is the current contract for Claude Code and Codex support in
agentic-dev-kit. The front matter is the machine-readable workflow inventory;
repository tests derive their expected shared definitions and runtime bindings from
it. Add or change a workflow there in the same change that moves its implementation.

## What parity means

Parity means equivalent outcomes and safety guarantees:

- the same workflow is discoverable and reaches the same shared definition;
- the same project contract and safety doctrine bind before relevant work;
- lifecycle hooks fire at the equivalent point and invoke the correct engine;
- review evidence describes the same reviewed revision and lenses;
- isolated lanes preserve the same source ownership, state sandbox, and merge authority;
- adoption and upgrade can install, inspect, and refresh each runtime without clobbering
  adopter-owned configuration.

Parity does not mean copying one runtime's configuration shape into the other. Claude
commands and Codex skills are adapters over the shared workflow. Claude settings and
Codex project configuration remain runtime-native surfaces.

## Workflow status vocabulary

- `aligned` — shared definition and both runtime bindings ship.
- `gap` — a user-facing workflow is missing a shared definition or runtime binding.
- `companion` — shared material is loaded by the workflow named in `loaded_by` and
  deliberately has no direct runtime command or skill.

The machine-readable declaration is authoritative for file coverage. The matrix below
records broader capability parity that cannot be expressed as an adapter path.

## Capability matrix

| Capability | Shared contract | Claude Code | Codex | Status / exit |
|---|---|---|---|---|
| Repository instructions | `AGENTS.md` | `CLAUDE.md` imports it | reads `AGENTS.md` directly | aligned |
| Workflow adapters | `docs/agentic-dev-kit/workflows/` | `.claude/commands/` | `.agents/skills/` | declaration above is authoritative |
| Safety-critical doctrine | `docs/agentic-dev-kit/safety-critical-changes.md` | path-scoped `.claude/rules/` binding | precise root `AGENTS.md` routing for the merge-authority engines | aligned for the stamped supported-client observation: structure proves the route; prompt input and live events establish that the trusted run supplied it and read and applied the shared doctrine |
| Document-budget tripwire | `check_doc_budget.py` | `SessionStart` | open-ended match-all `SessionStart` with a bounded command timeout | aligned: repository semantics are deterministic and the supported trusted client ran the equivalent lifecycle shape |
| Runtime memory tripwire | runtime-specific artifact | `check_memory_budget.py` checks Claude's `MEMORY.md` | no corresponding repository artifact | intentional difference: never invoke the Claude engine on Codex |
| PR follow-through | `pr_followup_hook.py` | `PostToolUse` with Claude runtime mapping | `^Bash$` `PostToolUse` with Codex runtime mapping and a bounded command timeout | aligned; current hook definitions still require Codex review and trust |
| Review fallback | shared panel doctrine, prompt builder, and composed receipt schema | isolated reviewers where available | isolated reviewers where available | aligned runtime semantics: the shared engine validates parent/delta ancestry, exact heads, changed paths, and pass caveats; adapters translate launcher/model/effort capabilities only, with Claude per-lens effort still prompt-instructed where its launcher exposes no control. Record-only classification, lens provenance, and posted draw verdicts remain instructed or self-reported rather than mechanically enforced |
| Capability tiers | `config/dev-model.yaml` neutral tiers | model mapping | reasoning-effort mapping | gap: calibrate Codex model plus effort mappings |
| Headless lane isolation | one kit-owned per-runtime wrapper (`launch_lane.py`): canonical one-shot descriptor, exact identity chain, environment replacement, child observation, config-declared transports, and terminal receipt | the same wrapper around stable local `claude -p` (`process-cwd` / `stdin` / `json-stdout`) | the same wrapper around stable local `codex exec -C` (`cd-flag` / `stdin-dash` / `last-message-file`) | both local unattended paths aligned for their stamped supported-client observations: inherited `DEVKIT_*`, repository overrides, and caller `PATH` are removed, descriptor keys replace them, the child independently binds worktree/repository/origin/lane/state/branch/base/commit/process identity before `exec`, the request binds the runtime and its transports, and success waits for final-text evidence — for Claude, exactly one successful JSON result object. Approval/sandbox policy is config-declared per runtime (`parallel.<runtime>_approval_policy`) from an engine-owned bounded vocabulary, passed as argv, bound into the request and the observed argv, and read back from the runtime's own denial record where the transport exposes one. Claude's trust route is the wrapper's: `--setting-sources ""` plus the cockpit-owned `parallel.claude_settings_profile` through `--settings`, because a lane worktree is untrusted, its branch settings' allow-list is ignored while its hooks still run, and the operator's user settings would otherwise apply. The Claude writing-lane record observed a scoped write, commit, push, pull request, and cockpit `pr-watch` under that route with an empty denial list, plus a `dont-ask` lane's refused write terminalizing `failed`. Codex receives `--sandbox <policy>` validated the same way; its writing-lane behaviour is unobserved and unclaimed until the Codex record exists. Native agent dispatch on either runtime, desktop/app tasks, app-server, Claude remote sessions, and cloud tasks are not substitutes; model/effort calibration remains separate |
| Command permissions | repository policy | `.claude/settings.json` permissions | no shipped project rules | gap: decide and ship the Codex policy surface |
| Post-merge integrations | shared capability contract and `systemize` config | runtime-native forge, tracker, notify, and repository mechanisms | runtime-native forge, tracker, notify, and repository mechanisms | aligned for workflow outcomes: forge read and config are required; notification, tracker creation, reviewer access, and the atomic engine set have explicit degraded or fail-closed paths. The tracker remains payload-approval-gated and the unvendored engine set remains agent-executed in LLM-only mode |
| Session-start and wrap-up integrations | shared authoritative capability, authority, artifact, resumability, non-interactive, and completion declarations | runtime-native reads/writes behind thin commands | runtime-native reads/writes behind thin skills | aligned for repository structure: merged config and required failures stop; applicable optional sources must be attempted and have explicit degraded results; session-start PR readiness uses unfiltered review evidence, labels unverified resolution, and represents detached HEAD explicitly; conditionals classify at their trigger; interactive issue-shaped findings reach an exact-payload decision before parking; every changed repository artifact, including existing project status, takes the forge/review path; first-match terminal precedence prevents a degraded integration from masking an incomplete repository or merge path; tracker-only success cannot become a no-op; merge authority either permits and verifies the merge, routes isolated review and self-merge through the cockpit's paired lane wrappers and shared state sandbox, defaults a policy-less non-lane PR to operator authorization, or holds the exact reviewed head |
| Triage integrations | shared capability, authority, durable-artifact, semantic-input, and completion declarations plus the `triage` config block | runtime-native tracker/notify/repository mechanisms behind a thin command | runtime-native tracker/notify/repository mechanisms behind a thin skill | aligned for workflow outcomes: merged config and frozen state are required; the configured draft/finalize pair is atomic, with honest agent-executed LLM-only behavior when both are absent; unattended approval requires notification send/thread read while interactive use can degrade to the current session; exact-payload approval, pre-attempt state, destination read-back, and accounted byte-identical sweep sets prevent duplicate writes and partial-batch data loss; test mode cannot touch tracker or source/forge state; unresolved approval, tracker, repository, or review paths remain operator-held |
| Adapter upgrade | shared workflow refresh | existing adapter retained | existing adapter retained | gap: runtime-specific fixes can remain stale |
| Drift inspection | `kit_doctor` | registration paths resolved | merged project hook sources, project enablement, and structural lifecycle fields checked only for exact repository-owned command strings; altered strings retain generic path diagnostics | gap narrowed: runtime-adapter and general shell semantics remain |

## Lifecycle validation boundary

Repository checks establish that the shipped Codex JSON names the portable engine,
keeps the Claude-only memory engine out, and exactly matches the canonical event,
matcher, handler, command, and timeout objects printed by `init.sh`. They also inspect
additive inline project hooks and each present project hook feature-switch alias. An
altered command string is not assigned lifecycle semantics or accepted as
shell-equivalent; it retains the generic registration-path result. Repository
inspection does not establish that a client trusted or executed the definitions.
Each present project feature spelling must be boolean; canonical `hooks` supplies the
effective value when deprecated `codex_hooks` is also present.

The separate lifecycle trusted-client record is kept upstream at
[`saved_plans/codex-hooks-live-validation_2026-08-23.md`](https://github.com/topij/agentic-dev-kit/blob/main/saved_plans/codex-hooks-live-validation_2026-08-23.md).
It records the controlled repository, client, commands, revisions, and observed
`SessionStart` / `PostToolUse` behavior. Interactive `systemMessage` presentation
remains a gap; the noninteractive event stream and model-visible context were checked.

The safety-doctrine trusted-client record is kept upstream at
[`saved_plans/codex-safety-doctrine-live-validation_2026-08-24.md`](https://github.com/topij/agentic-dev-kit/blob/main/saved_plans/codex-safety-doctrine-live-validation_2026-08-24.md).
It uses the client-visible prompt-input list rather than a correct answer to establish
that the root route was supplied, then binds the doctrine read and applied result to a
clean trusted checkout and exact client. The fixture includes a search decoy, a
no-instruction guess control, nested precedence, and trusted/untrusted project controls.
Its conclusion is an observation at the stamped client and revision, not a guarantee
for future clients or other surfaces.

The environment-capable launcher records are kept in
[`saved_plans/codex-environment-capable-launcher-live-validation_2026-08-26.md`](../../saved_plans/codex-environment-capable-launcher-live-validation_2026-08-26.md)
and
[`saved_plans/claude-environment-capable-launcher-live-validation_2026-08-27.md`](../../saved_plans/claude-environment-capable-launcher-live-validation_2026-08-27.md),
each produced from a session of the runtime it observes. Each uses a synthetic
repository to avoid sending workspace metadata to the external client, verifies the
copied engine bytes against this checkout, injects hostile inherited lane/repository
variables, and binds the child observation and final text to the one-shot descriptor
receipt. Each supported claim is limited to the stamped local client and the selected
kit wrapper; neither observes a write or an approval transition. The Claude
writing-lane record is kept in
[`saved_plans/claude-writing-lane-live-validation_2026-08-27.md`](../../saved_plans/claude-writing-lane-live-validation_2026-08-27.md),
produced from a Claude Code session against a private synthetic GitHub repository:
it observes the config-declared policy and trust route in the child argv and receipt,
the lane's write, commit, push, and pull request, the cockpit's `dev_session.sh
pr-watch` read-back, the denial list the runtime reported, and a `dont-ask` control
lane whose refused write terminalized `failed`. Its route-selection probes are in
[`saved_plans/claude-writing-lane-approval-policy-design_2026-08-27.md`](../../saved_plans/claude-writing-lane-approval-policy-design_2026-08-27.md).
The Codex writing-lane record does not exist yet; the Codex policy argv is validated
and passed, and nothing about its behaviour is claimed.

## Product surfaces this contract relies on

The Codex bindings follow the supported repository skill layout and explicit `$skill`
invocation described in the
[Codex skills documentation](https://learn.chatgpt.com/docs/build-skills). Codex project
instructions use the root-to-working-directory `AGENTS.md` chain described in the
[Codex AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
Hook schema and project trust follow the
[Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

These links define the external product surface, not the kit's acceptance test. A
change based on new runtime behavior still needs a live trusted-session check before
the matrix moves to `aligned`.

## How to change the contract

1. Update the front-matter declaration and the implementation together.
2. Keep user-facing behavior in the shared workflow; keep only invocation and
   runtime-capability translation in the adapter.
3. Update the capability row when a gap is opened, narrowed, or closed.
4. Add deterministic structural coverage, then add a live runtime check when the claim
   depends on client behavior rather than repository files.
5. Update adoption, upgrade, `kit_doctor`, and README when the changed surface must
   reach existing adopters.
