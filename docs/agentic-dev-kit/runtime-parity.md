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
| Review fallback | shared panel doctrine, prompt builder, and composed receipt schema | isolated reviewers where available | isolated reviewers where available | aligned runtime semantics: the shared engine validates parent/delta ancestry, exact heads, changed paths, and pass caveats; adapters translate launcher/model/effort capabilities only: Claude per-lens `model` and `effort` are applied from the kit-owned agent definition `.claude/agents/<lens>.md` rendered by `panel_prompt.py --agent-definition` (the delegation tool itself has no effort parameter, so a plain subagent inherits the cockpit's effort), and Codex per-lens effort is applied from the `codex exec` argv `-c model_reasoning_effort=<level>` and read back from the rollout — both observed at the stamped clients in the calibration record. Record-only classification, lens provenance, and posted draw verdicts remain instructed or self-reported rather than mechanically enforced |
| Capability tiers | `config/dev-model.yaml` neutral tiers with a per-key, per-runtime mechanical/advisory declaration | `runtime_mappings.claude` names model aliases the client resolved (`haiku`, `sonnet`, `opus`, `fable`); applied by hand through the delegation tool's `model` parameter or `claude -p --model`/`--effort`; per-lens compute carried by `.claude/agents/<lens>.md` | `runtime_mappings.codex` names reasoning-effort levels the client applied (`low`, `medium`, `xhigh`; `max` and `none` also accepted, `minimal` refused by the API for the probed model); applied by hand through `codex -m`/`-c model_reasoning_effort=`; per-lens compute carried on the `codex exec` argv | aligned for tier outcomes and control semantics at the stamped clients (Claude Code 2.1.247, codex-cli 0.149.1, 2026-08-27): the mapping is advisory on both runtimes because no engine reads it, the values name real controls on both, and `lens_compute` is mechanical on both through different carriers. Deliberate difference: Claude's judgment tier moves the model and inherits effort; Codex's moves effort on the user's model. Not observed: a Codex cockpit spawning `codex exec` lenses under its own sandbox; effort's effect, as opposed to the applied parameter. Neither headless wrapper carries a control; a Claude lane under the trust route runs the product default model and effort |
| Headless lane isolation | one kit-owned per-runtime wrapper (`launch_lane.py`): canonical one-shot descriptor, exact identity chain, environment replacement, child observation, config-declared transports, and terminal receipt | the same wrapper around stable local `claude -p` (`process-cwd` / `stdin` / `json-stdout`) | the same wrapper around stable local `codex exec -C` (`cd-flag` / `stdin-dash` / `last-message-file`) | both local unattended paths aligned for their stamped supported-client observations: inherited `DEVKIT_*`, repository overrides, and caller `PATH` are removed, descriptor keys replace them, the child independently binds worktree/repository/origin/lane/state/branch/base/commit/process identity before `exec`, the request binds the runtime and its transports, and success waits for final-text evidence — for Claude, exactly one successful JSON result object. Approval/sandbox policy is config-declared per runtime (`parallel.<runtime>_approval_policy`) from an engine-owned bounded vocabulary, passed as argv, bound into the request and the observed argv, and read back from the runtime's own denial record where the transport exposes one. Claude's trust route is the wrapper's: `--setting-sources ""` plus the cockpit-owned `parallel.claude_settings_profile` through `--settings`, because a lane worktree is untrusted, its branch settings' allow-list is ignored while its hooks still run, and the operator's user settings would otherwise apply. The Claude writing-lane record observed, under the shipped `dont-ask` default with path-scoped edit tools, a scoped write, commit, push, pull request, and cockpit `pr-watch` with an empty denial list, a write beyond the worktree refused, and a lane with denied calls terminalizing `failed`; it also observed that `accept-edits` auto-accepts the runtime's own file-system Bash class regardless of the allow list, which is why it is not the default. Codex receives `--sandbox <policy>` validated the same way. The first lane run on **this repository** rather than a synthetic one (`first-real-headless-lane-live-validation_2026-08-28.md`, Claude Code 2.1.250, 2026-08-28) kept the launcher and every shipped configuration value byte-identical and terminalized `failed` on a non-empty denial list, which establishes for Claude what the Codex record could not: structured denial read-back with real denials in it, each naming its tool and target, retained under digests the receipt itself carries. It also found two boundaries no synthetic lane could reach. A lane cannot write under `.claude/` — `Edit` and `Write` on `.claude/commands/` were both refused while the same lane's `Edit` of `.agents/skills/` and of `scripts/tests/` succeeded, and a cockpit probe under the same trust route was refused on `.claude/commands/`, `.claude/rules/`, `.claude/agents/`, `.claude/settings.json` and a file directly under `.claude/` in one session that wrote `.agents/skills/`, `docs/` and `.github/workflows/` — so `Edit(**)` does not lift it, the glob is not the mechanism, and neither is dot-directories; a Claude lane therefore cannot complete a runtime-parity change on its own, where a Codex lane edits its own adapter directory freely. And the read-only Bash class the shipped profile relies on is a property of command **shape**, not command name: a `for … do cat … done` loop and a `;`-chained `grep`/`echo` compound were denied in the same session that accepted simple `grep` and `cat`. That lane opened no pull request — the cockpit pushed its branch and opened one only after writing the file the lane was refused — so nothing about a lane driving CI or earning a `pr-watch` receipt on a real repository is promoted here.  The 2026-08-27 Codex writing-lane record remains a historical observation: its temporary receipts, rollouts, and captures were removed at fixture cleanup, so none of its behavior is promoted. The [2026-08-30 rerun](../../saved_plans/codex-writing-lane-live-validation_2026-08-30.md) promotes only claims independently recomputable from its [retained redacted bundle](../../saved_plans/codex-writing-lane-evidence_2026-08-30/bundle.json), bound to source revision `bdfd6ee702a630f0575f0c186f51b3bbbcd1810a`, synthetic fixture revision `83d3b623305a691dd874df44ca92270daa62ade9`, and reviewed head `5c4006d18e65e0443dc7b22f48c099ad07ce1da9`: descriptor-scoped worktree/state output, a ready private pull request, and an exact-head cockpit review receipt. Its retained session attestation is not correlated to the launcher invocation, so the applied Codex model/effort/cwd stays historical. It also does not promote the earlier record’s exact per-command approval transitions, native config reach, structured denial read-back, or future-client behavior. Both records carry `terminal.permission_denials: null`, so neither establishes structured Codex denial read-back. Native agent dispatch on either runtime, desktop/app tasks, app-server, Claude remote sessions, and cloud tasks are not substitutes; model/effort calibration remains separate |
| Command permissions | repository policy, decided per surface: the cockpit's own settings and the lane profile are different files answering different questions | cockpit: `.claude/settings.json` permissions. Lane: the cockpit-owned `config/claude-lane-settings.json`, a command-prefix allow list passed with `--settings` under `--setting-sources ""` | cockpit: no shipped project rules. Lane: `--sandbox <policy>` from the engine-owned vocabulary, shipped `read-only`, with no per-command list to receive a grant | lane surface decided (`#606`, 2026-08-28): the profile is **task-scoping, not a security boundary** — measured, under the shipped profile with nothing added, a lane rewrote an engine the profile already grants and executed it outside the worktree with an empty `permission_denials`, so a prefix rule cannot constrain the contents of the file it names (`#631`). What it does deliver is fail-closed behaviour for a *confused* lane. On that basis the shipped Claude grants are decided on what each buys: `make test` (the `AGENTS.md` verification command, which a lane structurally could not run) and `kit_doctor.py` (without it a lane editing a kit-owned file cannot make its own PR green). **The mirror to Codex is the doctrine, not the grants** — `--sandbox` is a different *kind* of mechanism, bounding the process rather than the command name, so it is narrower exactly where the prefix list is weakest; when a Codex writing policy is chosen it inherits the reasoning above and not these entries. **One asymmetry is permanent and not a gap to close:** a Claude lane cannot write under `.claude/` at all (`#627`, measured in two repositories under two edit tools; no allow-list entry reaches the client's own guard) while a Codex lane edits its own adapter directory freely, so a runtime-parity change is not symmetrically delegable — split it, lane for the neutral half and the Codex adapter, cockpit for `.claude/`. **Cockpit surface now decided too (`#606`, 2026-08-29), on the same print-never-write doctrine as the hook registrations (`#303`):** `init.sh` prints the cockpit allow-list templated on the adopter's `paths.engines`, because the kit's own entry baked in `scripts` and an adopter vendoring under `scripts/devkit/` copied a rule that grants nothing. `kit_doctor` reports an installed engine that no `permissions.allow` rule reaches as `ungranted`, reading the grant from `.claude/settings.json` **and** the `.claude/settings.local.json` overlay — a grant in either covers the engine, so an adopter who keeps the overlay out of version control is not reported ungranted — informational, never failing, since approving each poll is a supported choice. The `SessionStart` matcher is dropped on **both** runtimes rather than only Codex: `"startup"` was read as Claude's limit until it was measured and turned out to be ours, a resumed session having silently skipped both budget tripwires ([evidence](../../saved_plans/claude-sessionstart-matcher-live-validation_2026-08-29.md)). Codex still has no per-command surface to receive the allow-list half |
| Post-merge integrations | shared capability contract and `systemize` config | runtime-native forge, tracker, notify, and repository mechanisms | runtime-native forge, tracker, notify, and repository mechanisms | aligned for workflow outcomes: forge read and config are required; notification, tracker creation, reviewer access, and the atomic engine set have explicit degraded or fail-closed paths. The tracker remains payload-approval-gated and the unvendored engine set remains agent-executed in LLM-only mode |
| Session-start and wrap-up integrations | shared authoritative capability, authority, artifact, resumability, non-interactive, and completion declarations | runtime-native reads/writes behind thin commands | runtime-native reads/writes behind thin skills | aligned for repository structure: merged config and required failures stop; applicable optional sources must be attempted and have explicit degraded results; session-start PR readiness uses unfiltered review evidence, labels unverified resolution, and represents detached HEAD explicitly; conditionals classify at their trigger; interactive issue-shaped findings reach an exact-payload decision before parking; every changed repository artifact, including existing project status, takes the forge/review path; first-match terminal precedence prevents a degraded integration from masking an incomplete repository or merge path; tracker-only success cannot become a no-op; merge authority either permits and verifies the merge, routes isolated review and self-merge through the cockpit's paired lane wrappers and shared state sandbox, defaults a policy-less non-lane PR to operator authorization, or holds the exact reviewed head |
| Triage integrations | shared capability, authority, durable-artifact, semantic-input, and completion declarations plus the `triage` config block | runtime-native tracker/notify/repository mechanisms behind a thin command | runtime-native tracker/notify/repository mechanisms behind a thin skill | aligned for workflow outcomes: merged config and frozen state are required; the configured draft/finalize pair is atomic, with honest agent-executed LLM-only behavior when both are absent; unattended approval requires notification send/thread read while interactive use can degrade to the current session; exact-payload approval, pre-attempt state, destination read-back, and accounted byte-identical sweep sets prevent duplicate writes and partial-batch data loss; test mode cannot touch tracker or source/forge state; unresolved approval, tracker, repository, or review paths remain operator-held |
| Adapter upgrade | shared workflow refresh plus the fetched kit's adapter renderer | rendered kit form refreshed; authored command preserved | rendered kit form refreshed; authored skill preserved | aligned: `/upgrade` classifies exact current and prior rendered forms separately from adopter-authored bytes, installs missing bindings, and never puts adapter ownership into the drift gate |
| Drift inspection | `kit_doctor` | registration paths resolved; cockpit `permissions.allow` coverage reported against the configured engine path | merged project hook sources, project enablement, and structural lifecycle fields checked only for exact repository-owned command strings; altered strings retain generic path diagnostics | gap narrowed: runtime-adapter and general shell semantics remain |

## Live promotion boundary

Client-dependent capability promotion follows
[`live-validation-evidence.md`](live-validation-evidence.md). A narrative, a digest
whose named bytes were cleaned up, or a carrier that cannot retain the authoritative
applied-compute observation stays historical. `verify_live_validation_bundle.py`
checks the closed bundle and promotion shapes, destination digests, independently
supplied source/review/redaction/runtime/applied-compute and complete claim-object
promotion expectations, artifact inventory, capture request/date stamps, bounded input
envelopes and trees, redaction backstops, and persistent minimal `turn_context`
attestation when a claim depends on model, effort, or cwd. For a fixture ledger, the
verifier also walks every retained source dependency at the fixture revision. The
tracked semantic control adds a path-to-digest trust root outside the bundle, fixes the
fixture identity, and asserts claim-specific observer relationships. The named
redaction reviewer and capability reviewer still own semantic minimization and whether
the retained observers establish the promoted claim; a structurally valid bundle is
not a substitute for that claim-specific recomputation.

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
The Codex writing-lane design and record are kept in
[`saved_plans/codex-writing-lane-design_2026-08-27.md`](../../saved_plans/codex-writing-lane-design_2026-08-27.md)
and
[`saved_plans/codex-writing-lane-live-validation_2026-08-27.md`](../../saved_plans/codex-writing-lane-live-validation_2026-08-27.md).
The durable rerun and its repository-owned evidence are kept in
[`saved_plans/codex-writing-lane-live-validation_2026-08-30.md`](../../saved_plans/codex-writing-lane-live-validation_2026-08-30.md)
and
[`saved_plans/codex-writing-lane-evidence_2026-08-30/`](../../saved_plans/codex-writing-lane-evidence_2026-08-30/).
The capability-tier calibration design and record are kept in
[`saved_plans/capability-tier-calibration-design_2026-08-27.md`](../../saved_plans/capability-tier-calibration-design_2026-08-27.md)
and
[`saved_plans/capability-tier-calibration-live-validation_2026-08-27.md`](../../saved_plans/capability-tier-calibration-live-validation_2026-08-27.md),
produced from a Claude Code session with controlled `claude -p` and `codex exec`
probes in a scratch fixture. The record's observers are each runtime's own artifacts —
Claude's session and subagent transcripts, Codex's rollout `turn_context` — never the
prompt or the child's prose; its raw outputs were session-scoped and are quoted as
excerpts, so the row above promotes only what the excerpts show.
The historical record narrates the fixture-only workspace-write lane, native config
reach, per-command approval transitions, network-disabled and network-enabled
outcomes, GitHub pull-request read-back, and the cockpit review receipt. Its raw
fixture evidence was temporary and removed under that run's cleanup contract, so the
narrative and its unresolvable digests remain historical. The durable rerun uses the
repository-owned verifier and a promotion receipt bound to the retained destination
bytes, exact upstream and fixture source files, source revision, synthetic fixture
revision, review repository, reviewed synthetic head, redaction reviewer, runtime,
client, and claim IDs. It promotes the scoped write/state, ready private PR, and
exact-head review-receipt claims enumerated in that receipt. The retained runtime
attestation is outside the promoted claim map because it does not correlate its session
to the launcher invocation. Both
runs preserve the transport gap: Codex described denial/approval behavior in final
prose while the completed last-message receipt carried
`terminal.permission_denials: null`. The shipped default remains read-only.

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
