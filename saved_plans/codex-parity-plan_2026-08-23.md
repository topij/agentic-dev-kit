# Codex parity plan — 2026-08-23

## Goal

Make Codex a first-class agentic-dev-kit runtime with the same workflow outcomes,
safety guarantees, review evidence, lane isolation, and upgrade behavior as Claude
Code. Runtime-specific files may differ in shape; their observable contract should
not.

## Sprint status — 2026-08-25

The machine-readable inventory and current capability judgments live in
[`runtime-parity.md`](../docs/agentic-dev-kit/runtime-parity.md); this plan supplies
their delivery order and exit conditions.

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
- [ ] **Phase 3 — Complete workflow and integration coverage.** PR `#595` merged the
  bounded `post-merge-systemize` extraction with a shared definition, thin runtime
  bindings, config-owned policy, equivalent durable artifacts, and explicit capability
  preflights. PR `#596` merged the same structured contract for `session-start` and
  `wrap-up`; `triage-friction-log` remains the Phase 3 exit.
- [ ] **Phase 4 — Make delegation and parallel lanes equivalent.** PR `#598` delivers
  the kit-owned engine boundary for absolute descriptor roots, exact lane/forge
  identity, fail-closed reconciliation, operator-held evidence, and adopter upgrade
  ownership. Codex model and effort calibration, an environment-capable launcher, and
  live runtime isolation checks remain planned.
- [ ] **Phase 5 — Align permissions, installation, and upgrades.** Codex project
  policy, adopter-owned merge surfaces, and adapter refresh behavior remain planned.
- [ ] **Phase 6 — Gate parity and roll it out.** Adoption fixtures, trusted smoke
  coverage, historical-status cleanup, and the adopter pilot remain planned.

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
- **Capabilities:** repository/config and inbox reads are required. Live Session B needs
  tracker write access after payload-specific approval. Scheduled approval collection
  needs notification thread read/write. Parser/finalizer availability must be treated as
  an atomic engine mode rather than assumed.
- **Authority and artifacts:** the frozen inbox, proposal report, approval-bound state,
  returned tracker identifiers, source/archive diff, and PR are resume evidence. Tracker
  writes require exact-payload approval; a standing workflow request is not approval.
- **Stops and mismatch:** the current shared workflow names a dedicated pipeline config
  that is absent from `config/dev-model.yaml`, assumes unvendored engines, and makes the
  notification channel an unconditional stop even when the operator is present in the
  interactive session. Its Codex adapter also states only a generic external-mutation
  gate. Resolving those together requires a config/installer migration and the semantic
  input matrix, so it is deliberately outside the bookend slice.

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
kit receives absolute headless roots, descriptor environment replacement, durable
lane/base/class identity, exact repository/PR/base/head/fork binding, fail-closed forge
reads, operator-held evidence, resume-aware branch-tip checks, semantic/mutation
matrices, and adopter upgrade coverage. It does not receive cs-toolkit's operator-only
merge policy or `CS_TOOLKIT_*` namespace. The downstream checkout remains unchanged;
its repo-owned engines require a later explicit reconciliation PR rather than a normal
kit upgrade.

Resume the Phase 3 exit with this preserved starter:

```text
Create feat/triage-integration-preflights from current origin/main. Build the semantic
input matrix for a config/dev-model.yaml-owned triage block and its init/upgrade
migration first. Then make triage-friction-log declare required repository and frozen-
state capabilities, atomic engine-backed versus honest LLM-only behavior, interactive
approval when notification is unavailable, scheduled notification requirements,
payload-specific tracker authority, durable resume evidence, test-mode write limits,
and hard-stop/degraded-success/completion outcomes. Keep the Claude and Codex adapters
thin; update runtime parity, README/getting-started, upgrade guidance, manifest, and
declaration-derived mutation tests in the same PR.
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
- [ ] Apply the capability-contract pattern to `triage-friction-log` without moving its
  policy into adapters.

The bounded workflow slice is done when either runtime can execute the retro workflow
and produce the same durable artifacts. The phase closes when `session-start`,
`wrap-up`, and `triage-friction-log` carry equally explicit required and degraded paths.

### Phase 4 — Make delegation and parallel lanes equivalent

- Calibrate Codex `{model, effort}` mappings for the neutral capability tiers.
- Pass configured Codex model and reasoning effort mechanically to fallback-review
  lenses.
- Provide or select a Codex lane launcher that can set worktree, environment, model,
  reasoning effort, and permission mode.
- Permit native subagents only when the state-isolation contract can be satisfied;
  otherwise use the environment-capable launcher or remain attended.
- Add live checks for reviewer isolation, reviewed revision, lane state root, and
  final-text handoff.

Done when a Codex parallel batch preserves the same state isolation, review evidence,
and merge authority as Claude usage.

### Phase 5 — Align permissions, installation, and upgrades

- Decide which Claude permission allowances are repository policy and express their
  Codex equivalents through trusted project config or command rules.
- Treat Codex hooks, config, and rules as adopter-owned merge surfaces rather than
  replacement targets.
- Derive runtime-adapter inventories from the filesystem and the parity declaration.
- Track adapter baselines, or make the adapters sufficiently generated and thin that
  runtime fixes can safely reach existing adopters.
- Extend adoption, upgrade, and `kit_doctor` to inspect and report Codex skills,
  metadata, configuration, hook semantics, and declared dependencies.

Done when an existing Codex adopter can upgrade without retaining stale runtime
behavior or losing local policy.

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

PR `#596` then merged the shared integration contract for the lifecycle bookends. The
remaining Phase 3 starter is the `feat/triage-integration-preflights` block under
“Slice boundary and next starter” above and is mirrored in the latest handoff; update
both together if its scope changes.

PR `#598` then moved the reusable lane-identity and forge-safety behavior exposed by
cs-toolkit `#2086` into kit-owned engines and shared workflows. It deliberately leaves
runtime launcher mechanics and downstream repo-owned engine adaptation outside the
slice. The Phase 3 starter remains `feat/triage-integration-preflights`; this Phase 4
slice neither replaces nor completes it.

Keep the trusted-client record as an observation at its stamped client and revision; do
not turn it into a general instruction-loading guarantee.
