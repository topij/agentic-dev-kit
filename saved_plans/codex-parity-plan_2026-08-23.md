# Codex parity plan — 2026-08-23

## Goal

Make Codex a first-class agentic-dev-kit runtime with the same workflow outcomes,
safety guarantees, review evidence, lane isolation, and upgrade behavior as Claude
Code. Runtime-specific files may differ in shape; their observable contract should
not.

## Sprint status — reconciled 2026-09-01

The machine-readable inventory and current capability judgments live in
[`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md); this plan supplies
their delivery order and exit conditions. This maintained status section reconciles
merged repository state; the stamped pre-implementation baseline below remains the
historical observation it was and is not silently refreshed.

- [x] **Phase 1 — Declare the parity contract.** PR `#588` merged on 2026-08-23 with
  the maintained capability matrix, shared-workflow inventory, explicit exceptions,
  and declaration-derived structural checks.
- [x] **Phase 2 — Correct safety and lifecycle hooks.** PR `#588` removed the
  Claude-only memory checker from Codex. PR `#590` routed shared safety doctrine and
  merged on 2026-08-24 with trusted-client hook evidence, canonical installer wiring,
  and exact-string lifecycle enforcement in `kit_doctor`. The controlled record in
  [`codex-safety-doctrine-live-validation_2026-08-24.md`](codex-safety-doctrine-live-validation_2026-08-24.md)
  then established, for the stamped trusted client observation, that Codex supplied
  the root route and read and applied the shared doctrine for affected merge-authority
  work. It does not generalize one client observation. Interactive-TUI
  `systemMessage` presentation remains an explicit live-client gap.
- [x] **Phase 3 — Complete workflow and integration coverage.** PR `#595` merged the
  bounded `post-merge-systemize` extraction with a shared definition, thin runtime
  bindings, config-owned policy, equivalent durable artifacts, and explicit capability
  preflights. PR `#596` merged the same structured contract for `session-start` and
  `wrap-up`. PR `#599` merged the config-owned draft/approve/finalize matrix and the
  independently observed forge-provenance chain for `triage-friction-log`, closing the
  remaining structural exit.
- [ ] **Phase 4 — Make delegation and parallel lanes equivalent.** PR `#598` delivered
  the kit-owned engine boundary; PR `#609` delivered the Codex wrapper, its live record,
  and the declared Claude gap; PR `#611` generalised the wrapper to Claude
  (`claude -p`) with a Claude-produced live record and moved the parity row's Claude
  cell to the observed mechanism; PR `#614` added the config-owned approval policy per
  runtime and the Claude trust route with a Claude-produced writing-lane record; PR
  `#620` added the Codex-authored writing-lane record without changing the launcher;
  PR `#623` calibrated the capability tiers per runtime from live probes and declared
  every compute key mechanical or advisory per runtime. Delivery order and current
  disposition:
  1. Done in PR `#611` (Claude through `claude -p`, config-declared transports, Codex
     pinned unchanged). The record observed no write or approval transition and found
     that a fresh lane worktree is an untrusted workspace to Claude — the shape of the
     next item.
  2. Done in PR `#614` for Claude: `parallel.<runtime>_approval_policy` and
     `parallel.claude_settings_profile`, the trust route (`--setting-sources ""` plus
     the cockpit-owned profile), the structural profile validator, denial read-back,
     and a writing-lane record — a lane that performed a scoped write and landed a PR
     through its own `pr-watch`. That slice did not observe the Codex value.
  3. Done in PR `#620`: the Codex-authored record observed the scoped write, exact
     per-command approval transitions, network-disabled and network-enabled outcomes,
     ready pull request, and cockpit `dev_session.sh pr-watch` receipt. It also found
     that action denials described in final prose do not reach
     `terminal.permission_denials` through `last-message-file`, and that user config
     reached the untrusted lanes while project config did not. The raw receipts,
     rollouts, and captures were removed with the fixture, so the parity cell records
     the historical observation without promoting it as durable capability evidence;
     `#621` owns the durable evidence-bundle follow-up.
  4. Done in PR `#623` (squash `92a3c15`): tiers calibrated from live probes of the
     pinned clients (Claude Code 2.1.247, codex-cli 0.149.1, 2026-08-27) —
     `runtime_mappings` advisory on both runtimes with values each client accepted
     (`claude.expensive: fable`, `codex.expensive: xhigh`); `lens_compute.claude`
     mechanical through the kit-owned `.claude/agents/<lens>.md` rendered by
     `panel_prompt.py --agent-definition` (the delegation tool itself has no effort
     parameter, so a plain subagent stays at the cockpit's effort); `lens_compute.codex`
     mechanical on the `codex exec` argv and read back from the rollout. The blanket
     "no per-agent effort" sentence is retired on the surface it was false on and kept
     on the one it was true on. Design and record:
     [`capability-tier-calibration-design_2026-08-27.md`](capability-tier-calibration-design_2026-08-27.md),
     [`capability-tier-calibration-live-validation_2026-08-27.md`](capability-tier-calibration-live-validation_2026-08-27.md).
     PR `#655` later delivered the adopter-side `kit_doctor` check for stale lens
     definitions. The already-running doctor owns expected rendering while the
     existing file report owns installed-engine drift.
  5. Done, as a fail-closed run: the first real headless task on the generalised
     launcher (no tracker item; `#602` was the task the lane performed, not the slice).
     The lane ran on this repository with the launcher and every shipped configuration
     value byte-identical, and terminalized `failed` on a non-empty denial list. That
     establishes for Claude what the Codex record could not — structured denial
     read-back with real denials in it — and found two boundaries no synthetic lane
     could reach: a lane cannot write under `.claude/`, which `Edit(**)` does not lift
     and which the same lane's successful `.agents/` and `scripts/tests/` edits rule out
     as a glob effect; and the read-only Bash class is a property of command shape, so a
     loop or a `;`-chained compound of otherwise-accepted commands is denied. The lane
     opened no pull request; the cockpit pushed its branch and opened `#625` only after
     writing the file the lane was refused, so what stays unobserved is a *lane* driving
     CI or earning a `pr-watch` receipt on a real repository — not CI on that branch.
     Design and record:
     [`first-real-headless-lane-design_2026-08-28.md`](first-real-headless-lane-design_2026-08-28.md),
     [`first-real-headless-lane-live-validation_2026-08-28.md`](first-real-headless-lane-live-validation_2026-08-28.md).
     Not built: a model or effort control on the wrapper, which the run gave no reason
     to add — the lane resolved to the product default and the task did not need
     another tier.
     Adopt now, mechanise later: the final verification stamp is a PR comment at the
     merged head, and a panel that ran leaves a disposition comment (`#603`, `#604`).
     Phase 5 owns `#236`, the `#243` narrowing (adapter generation), and `#631`; Phase 6
     takes `#607` as the adopter pilot and `#608`.
  6. Carried by PR `#651`: the repository-owned redacted evidence contract, hostile
     missing/altered/wrong-revision/claim-relabel mutations, and tracked positive
     control now refuse promotion when the retained bytes, complete claim-to-artifact
     map, independently expected applied compute for a claim that depends on it,
     review provenance, or binding are absent. A persistent Codex
     writing lane at source revision
     `bdfd6ee702a630f0575f0c186f51b3bbbcd1810a` produced descriptor-scoped worktree and
     state output, an open non-draft private pull request with GitHub `CLEAN` state,
     and an exact-head cockpit review
     receipt; the promotion retains the exact upstream and fixture source bytes those
     claims depend on and is bound to synthetic fixture revision
     `83d3b623305a691dd874df44ca92270daa62ade9`, repository, and head
     `5c4006d18e65e0443dc7b22f48c099ad07ce1da9`. The copied runtime attestation does not
     correlate its session to the launcher invocation, so its model, effort, and cwd
     remain historical and outside the promoted claim map. The 2026-08-27 record also
     stays historical and unpromoted. The retained record is
     [`codex-writing-lane-live-validation_2026-08-30.md`](codex-writing-lane-live-validation_2026-08-30.md).
     This implements `#621`'s durable-evidence contract for the bounded writing-lane
     claims. It does not establish the Phase 4 exit: the retained run is a writing
     lane, not the parallel batch the exit condition requires. The remaining exit is a
     retained, independently recomputable Codex parallel-batch run that demonstrates
     disjoint worktree and state-root identities, exact-head review evidence, and
     operator merge authority without merging.
- [ ] **Phase 5 — Align permissions, installation, and upgrades.** Merged deliveries
  now include PR `#632` for the measured Claude lane policy and permanent adapter-write
  asymmetry; PR `#635` for generated adapter refresh plus manifest-selected installed
  tests; PR `#637` for the templated cockpit grant advisory, open-ended SessionStart,
  and informational permission inspection; PR `#639` for the allow-side whole-tool
  rule measurement; and PR `#649` for the safety-critical classification of the
  configured lane profile; and PR `#655` for adopter-side stale lens-definition
  inspection. The exit is not yet established. `#236` retains the engine/doctrine
  same-function-different-path survey, `#243` retains field exercises for `adopt`,
  `parallel`, `triage-friction-log`, and `post-merge-systemize`, and `#631` retains the
  lane execution-boundary decision. The 2026-09-01 tracker reconciliation closed
  `#606`; PR `#655` delivered `#255`'s implementation, leaving tracker disposition
  rather than additional implementation.
- [ ] **Phase 6 — Gate parity and roll it out.** Adoption fixtures, trusted smoke
  coverage, maintained parity reporting, the `#607` downstream adopter work, and the
  `#608` interactive-TUI gap remain planned.

This plan records the pre-implementation baseline. Its repository observations were
collected with `rg --files`, targeted `rg`, and
`uv run scripts/kit_doctor.py --json` at
`9c4969687f9adbec1eca55cbfb47955d85025026` on 2026-08-23. They intentionally describe
that revision; the delivery slices below are expected to change them.

## Phase 3 integration inventory — 2026-08-25

### `session-start`

- **Shared semantics:** gather the handoff, friction inbox, tracker, pull requests,
  repository state, CI/cron health, and project drift; classify traceable candidates;
  remediate false `Now` promotions; render one briefing and recommendation.
- **Runtime translation:** Claude passes `$ARGUMENTS`; Codex passes the user's request.
  Each runtime selects its own read mechanisms and may apply the configured model or
  effort mapping only when its launcher actually exposes that control.
- **Capabilities:** repository/config and repository-state reads are required. Forge,
  CI/cron, and tracker reads are always attempted and degrade visibly; forge readiness
  uses unfiltered review evidence, labels resolution the forge cannot prove, and
  represents detached HEAD explicitly.
  Configured drift reads degrade visibly when applicable. Archive and resolved-
  tracker reads are conditional before a `Now` promotion. Runtime compute selection is
  an optional enhancement.
- **Authority and artifacts:** the workflow is read-only and creates no durable state.
  The returned briefing is load-bearing; live sources, not an earlier response, are
  retry evidence. Non-interactive use renders once and exits.
- **Stops and mismatch:** required-source failure is a hard stop; optional-source gaps
  produce degraded success without false empty/clean claims. The Codex adapter repeated
  read-only and compute policy that belongs in the shared definition; this slice removed
  that duplicate.

### `wrap-up`

- **Shared semantics:** author and validate the living record, route session friction,
  preserve a next starter, enforce document budgets, stage named paths, and carry the
  record pull request through shared review follow-through.
- **Runtime translation:** Claude and Codex select native repository, forge, review, and
  tracker mechanisms. Invocation itself remains runtime-specific; capability policy and
  approval semantics do not.
- **Capabilities:** repository/config read and handoff write are required. The document-
  budget checker is required; the archive helper is conditional on its result. Forge PR
  write and `pr-watch` are conditional on any changed repository artifact. Tracker
  search/write is
  conditional and payload-approval-gated for an issue-shaped finding; an existing
  project-status artifact is an optional enhancement. Merge authority is conditional
  after the exact head becomes mergeable.
- **Authority and artifacts:** invocation authorizes the scoped repository record and its
  branch/PR path, not a merge. Tracker creates, modifications, and occurrence comments
  require the exact payload to be confirmed by the operator in the current interactive
  session. An interactive issue-shaped finding is searched and presented for that
  decision before parking. Durable evidence is every changed repository artifact,
  including an existing project-status artifact, its reviewed merge
  or exact operator-held head when changed, a parked friction entry, or an identifier
  actually returned and read back from the tracker.
- **Stops and mismatch:** a required failure preserves the record and stops before a
  false completion. Tracker unavailability, decline, silence, or ambiguity degrades to
  the friction inbox; incomplete and accumulating findings also take that route. Missing
  or insufficient merge authority holds a mergeable pull request for the operator; a
  policy-less non-lane pull request takes the operator default. Conditional capabilities
  classify at their trigger rather than before the record edit; unavailable forge or
  unsettled review paths preserve exact resume evidence as incomplete. First-match
  terminal precedence also keeps a degraded integration from masking an incomplete
  repository path or a failed or still-ambiguous authorized merge; a tracker-only write
  is successful completion, not a no-op, and isolated review plus self-merge stay on
  the cockpit's paired lane wrappers and shared state sandbox. The
  Codex adapter's generic external-mutation wording was weaker than the shared payload-
  specific gate; this slice removed that duplicate.

### `triage-friction-log`

- **Shared semantics:** draft proposals from a frozen inbox, obtain exact operator
  decisions, persist an approval session, file approved tracker payloads, and finalize a
  no-data-loss archive sweep on a reviewable branch.
- **Runtime translation:** Claude accepts `$ARGUMENTS`; Codex accepts the skill argument.
  Each runtime needs native tracker and notification clients, but neither adapter should
  choose their policy.
- **Capabilities:** repository/config, sandbox-aware state resolution, and an exact
  frozen inbox are required. Tracker write/read-back is conditional after exact-payload
  approval. Scheduled approval collection requires notification send/thread read, while
  interactive notification failure degrades to the current session. The configured
  draft/finalize pair is atomic; both absent selects an honest agent-executed LLM-only
  mode and a partial pair stops.
- **Authority and artifacts:** the frozen inbox, proposal report, approval-bound state,
  returned tracker identifiers, source/archive diff, and PR are resume evidence. Tracker
  writes require exact-payload approval; a standing workflow request is not approval.
  Commit, push, pull-request creation, `pr-watch`, archive sweep, and merge read-back
  consume the exact identity established by the preceding independently verified
  read-back rather than a locally self-consistent lifecycle record.
- **Stops and mismatch:** active approval state cannot be overwritten; missing frozen
  evidence never falls back to a whole-inbox sweep; changed approved payloads require a
  new decision; failed or ambiguous tracker/forge writes require destination read-back;
  partial tracker success holds before finalization; and test mode cannot write tracker,
  source documents, or forge state. Shared precedence distinguishes hard-stop,
  operator-held, degraded success, and successful completion. Both adapters now carry
  invocation/mechanism translation only.

### Slice boundary and next starter

PR `#596` merged the shared contract for `session-start` and `wrap-up`, whose
integration surface can use existing config, runtime-native mechanisms, and the shipped
helpers named by each definition without adding a dedicated pipeline configuration. It
did not add a partial triage config, pretend the missing engines are ready, or duplicate
approval policy in an adapter.

PR `#598` advances the shared lane primitive without claiming the Phase 3 exit. Its
read-only comparison of cs-toolkit commit
`4cf1ca914361b9912cd6bb1389e985d6e97ab3a0` (`#2086`) and its parent separated reusable
engine behavior from cs-toolkit policy/translation and unrelated application code. The
kit receives absolute headless roots, the descriptor environment replacement contract, durable
lane/base/class identity, exact repository/PR/base/head/fork binding, fail-closed forge
reads, operator-held evidence, resume-aware branch-tip checks, semantic/mutation
matrices, and adopter upgrade coverage. It does not receive cs-toolkit's operator-only
merge policy or `CS_TOOLKIT_*` namespace. The downstream checkout remains unchanged;
its repo-owned engines require a later explicit reconciliation PR rather than a normal
kit upgrade.

PR `#599` delivered the Phase 3 starter and closed the declared structural exit.
Preserve the next sprint starter:

```text
Create feat/codex-environment-capable-launcher from current origin/main. Inventory the
supported Codex launch surfaces against the existing absolute descriptor and environment
replacement contract, choose one mechanism that can apply worktree plus environment
without weakening lane identity, and add live isolation evidence before changing the
shared parallel launcher guidance. Keep model/effort calibration and downstream
cs-toolkit adaptation in separate later slices.
```

## Pre-implementation assessment

### Aligned foundation

- `session-start`, `wrap-up`, `pr-watch`, `parallel`, `adopt`, `upgrade`, and
  `triage-friction-log` have runtime-neutral definitions under
  `docs/agentic-dev-kit/workflows/` and thin bindings under both
  `.claude/commands/` and `.agents/skills/`.
- `AGENTS.md` is the shared repository contract, and `CLAUDE.md` imports it rather
  than maintaining a second copy.
- The document-budget and PR-follow-through mechanisms have registrations for both
  runtimes.
- Review configuration already has runtime-specific fallback commands and compute
  mappings.

### Gaps to close

- `post-merge-systemize` remains a Claude-only command with no shared workflow or
  Codex skill.
- Claude has a path-scoped safety-doctrine binding under `.claude/rules/`; Codex
  relies on broader `AGENTS.md` prose and has no equivalent triggered binding in
  this repository.
- Codex SessionStart invokes `check_memory_budget.py`, although that engine explicitly
  targets Claude Code's external `MEMORY.md` and states that the artifact has no Codex
  equivalent.
- `init.sh` carries Codex hook guidance derived from an older measured client whose
  matcher and trust behavior did not match the documented surface reviewed for this
  baseline.
- Codex capability tiers vary reasoning effort but do not select a model, despite
  the documented subagent support for both controls reviewed for this baseline.
- The headless-lane contract requires worktree and environment replacement, while
  native Codex subagent dispatch does not itself provide that launch contract.
- Claude repository permissions are shipped in `.claude/settings.json`; the kit has
  no corresponding policy for trusted project `.codex/config.toml` or
  `.codex/rules/`.
- Tracker and notification workflows assume suitable CLI or MCP integrations, but
  Codex skill metadata declares no tool dependencies or preflight contract.
- `/upgrade` refreshes shared workflow definitions but keeps existing runtime
  adapters, so Codex metadata and adapter-specific fixes do not reliably reach
  adopters.
- Adapter coverage is maintained through a hardcoded test list rather than derived
  from the repository's declared runtime-parity contract.
- The repository has static coverage for Codex shapes but no trusted, end-to-end
  Codex smoke test covering instructions, skills, hooks, review, and isolated lanes.
- `docs/kit-convergence-plan.md` preserves historical status that is easy to misread
  as the live parity inventory, and README hook descriptions have drifted from
  the shipped Codex registration.

## Delivery plan

### Phase 1 — Declare the parity contract

- Add a maintained runtime-capability matrix covering workflows, persistent
  instructions, safety activation, hooks, permissions, model controls, subagents,
  external integrations, adoption, upgrade, and drift detection.
- Define parity as equivalent outcomes and safety guarantees rather than identical
  runtime configuration files.
- Declare every intentional exception in the matrix so absence cannot masquerade as
  support.
- Derive structural parity checks from that declaration instead of restating the
  expected adapter set in tests.

Done when every shipped workflow and enforcement mechanism has a declared Claude
path, Codex path, or explicit exception.

### Phase 2 — Correct safety and lifecycle hooks

- Stop registering the Claude memory-budget checker on Codex.
- Decide separately whether Codex needs an instruction-chain budget checker for
  `AGENTS.md`; do not relabel the Claude engine as portable.
- Revalidate Codex SessionStart, PostToolUse, matcher, timeout, output, and trust
  behavior against the supported client.
- Update installer guidance, hook comments, documentation, and tests from that live
  measurement.
- Bind safety-critical doctrine through concise shared `AGENTS.md` routing and nested
  instruction files where directory scoping is useful.
- Extend `kit_doctor` from path resolution to semantic registration checks.

Done when a clean trusted Codex checkout runs only the intended lifecycle hooks and
loads the safety doctrine for affected work.

### Phase 3 — Complete workflow and integration coverage

- [x] Extract `post-merge-systemize` into a shared workflow.
- [x] Replace the Claude implementation with a thin binding and add a Codex skill with
  UI metadata.
- [x] Define the workflow's capability contracts for forge, tracker, reviewer, and
  notification access.
- [x] Add explicit preflight behavior for unavailable tools and credentials.
- [x] Keep runtime tool selection in the adapters and capability preflight. Codex UI
  metadata uses the repository's supported `interface` shape; it does not claim a
  connector dependency that the client cannot mechanically require.
- [x] Apply the capability-contract pattern to `session-start` and `wrap-up` without
  moving their policy into adapters.
- [x] Apply the capability-contract pattern to `triage-friction-log` without moving its
  policy into adapters.

The bounded workflow slice is done when either runtime can execute the retro workflow
and produce the same durable artifacts. The phase is structurally complete:
`session-start`, `wrap-up`, and `triage-friction-log` carry explicit required,
degraded, held, resume, authority, and completion paths under shared definitions.

### Phase 4 — Make delegation and parallel lanes equivalent

- [x] Select a Codex lane launcher that sets worktree and complete lane environment,
  removes inherited identity, and binds child-observed identity plus final text to a
  one-shot receipt. The bounded launcher does not calibrate model, reasoning effort,
  or project permission mode.
- [x] Keep native subagents unsupported for headless state-writing lanes because their
  dispatch surface cannot apply the descriptor environment and observer/receipt chain;
  use the selected wrapper or remain attended.
- [x] Add a synthetic live check for lane worktree, repository, branch/base, state root,
  process, inherited-variable removal, and final-text binding at the stamped client.
- [x] Generalise the same wrapper contract to Claude through `claude -p`, with the
  runtime-under-test producing the live record (`#466`; PR `#611`).
- [x] Add config-owned approval/sandbox policy per runtime and the Claude trust route,
  with a Claude writing-lane live record (`#601`; PR `#614`).
- [x] Produce the Codex writing-lane live record from a Codex session before model or
  effort calibration (`#601`; PR `#620`). That 2026-08-27 record remains unpromoted
  because its raw fixture evidence was removed at cleanup; its historical observations
  stay bounded to that client and revision.
- [x] Rerun the Codex writing lane through the durable redacted bundle contract
  (`#621`; PR `#651`). The retained promotion binds the source revision, reviewed
  synthetic repository and head, client, persistent session carrier, independent
  redaction reviewer, authoritative observers, exact source bytes and their retained
  Git commit/tree membership proofs, destination digests, and exact-head review
  receipt. The uncorrelated model, effort, cwd, and session attestation remains a
  historical observation outside the promoted claim map. The receipt promotes only
  the complete independently expected claim objects and refuses absent, altered,
  ephemeral, wrong-revision, relabeled, or evidence-thinned carriers.
- [x] Calibrate both runtimes' neutral tiers and mechanically pass supported model/effort
  keys to fallback-review lenses (`#605`, `#255`).
- [x] Use the generalised launcher for the first real headless task only after those slices
  land (untracked; not `#602`).

Done when a Codex parallel batch preserves the same state isolation, review evidence,
and merge authority as Claude usage. The persistent 2026-08-30 writing-lane rerun does
not establish that exit. It retains source revision
`bdfd6ee702a630f0575f0c186f51b3bbbcd1810a`, reviewed synthetic head
`5c4006d18e65e0443dc7b22f48c099ad07ce1da9`, descriptor state, exact-head review
evidence, and operator merge class without merging, but contains no parallel-batch or
inter-lane observation. The remaining exit is the retained parallel-batch run described
above.

### Phase 5 — Align permissions, installation, and upgrades

- [x] Decide the shipped Claude lane allowances as repository policy and bind the Codex
  side by equivalent safety doctrine rather than copied command syntax (PR `#632`).
  The profile is task-scoping rather than a hostile-code boundary; `#631` owns the
  executable-boundary mechanism.
- [x] Make generated Claude and Codex adapters refreshable while preserving
  adopter-authored variants, and make upgrade verification select the manifest-declared
  installed tests (PR `#635`). `#236` keeps the engine/doctrine survey where path or
  slug cannot identify equivalent function.
- [x] Template the cockpit permission advisory on `paths.engines`, remove the narrow
  SessionStart matcher on both runtimes, inspect cockpit grant coverage without failing
  healthy adopters, and replace the unmeasured whole-tool rule with allow-side evidence
  (PRs `#637` and `#639`). The 2026-09-01 tracker reconciliation closed `#606`.
- [x] Treat the configured Claude lane profile as safety-critical adopter-owned policy
  through the Codex root binding and Claude path-scoped binding (PR `#649`). `#346` and
  `#434` remain separate workflow/test binding-coverage decisions.
- [ ] Exercise the remaining runtime-specific adapter translations through `adopt`,
  `parallel`, `triage-friction-log`, and `post-merge-systemize` (`#243`).
- [x] Inspect adopter-side generated lens definitions against their configured
  mechanical compute carrier without duplicating installed-engine drift (PR `#655`;
  `#255` retains tracker disposition only).
- [ ] Settle `#631` from executable positive and hostile-negative evidence without
  treating the Claude prefix list and Codex sandbox syntax as interchangeable.

Done when an existing Codex adopter can upgrade without retaining stale runtime
behavior or losing local policy. That exit remains open on the unchecked items above
and on `#236`'s engine/doctrine survey; merged delivery slices are not used as a
reassuring substitute for the exit.

### Phase 6 — Gate parity and roll it out

- Add fresh-repository fixtures for Codex-only, Claude-only, and dual-runtime
  adoption.
- Add trusted Codex smoke tests for instruction discovery, skill discovery,
  SessionStart, PostToolUse, `/review`, fallback panels, and parallel lanes.
- Keep Claude integration smoke tests beside them where automation credentials permit.
- Replace the historical convergence status with the maintained parity matrix and
  move historical analysis to an archive.
- Pilot the completed path in a real adopter before declaring Codex first-class.

Done when the parity matrix is enforced by deterministic checks and confirmed by an
adopter run.

## Completed review and shared-integration slices

PR `#593` delivered the review-evidence composition workstream separately from the
trusted-client validation: the shared engine now preserves a full-panel parent plus an
exact-head delta, validates ancestry, paths, heads, lenses, and pass caveats, and keeps
legacy receipts compatible. The shared fallback doctrine and prompt builder already
carry the full-versus-delta routing rules; Claude and Codex consume those same semantics.

Do not add a generic path or prose classifier as the next slice. The remaining review
gap is a deterministic artifact that can prove record-only semantics and independently
bind posted delta-draw verdicts; Git paths and author-supplied labels cannot establish
either fact. Until such an artifact exists, uncertain classification continues to take
the full-panel route and issue `#32` remains the provenance boundary.

PR `#596` then merged the shared integration contract for the lifecycle bookends. PR
`#599` completed that phase with config migration, frozen approval state, exact
external-write authority and read-back, cross-operation forge provenance, total
outcomes, thin adapters, and declaration-derived hostile mutations.

PR `#598` then moved the reusable lane-identity and forge-safety behavior exposed by
cs-toolkit `#2086` into kit-owned engines and shared workflows. It deliberately leaves
runtime launcher mechanics and downstream repo-owned engine adaptation outside the
slice. The environment-capable launcher workstream then selected the kit-owned stable
`codex exec` wrapper, added descriptor/receipt authority and synthetic live isolation
evidence, and left compute calibration plus downstream adaptation outside its boundary.

Keep the trusted-client record as an observation at its stamped client and revision; do
not turn it into a general instruction-loading guarantee.
