# Codex parity plan — 2026-08-23

## Goal

Make Codex a first-class agentic-dev-kit runtime with the same workflow outcomes,
safety guarantees, review evidence, lane isolation, and upgrade behavior as Claude
Code. Runtime-specific files may differ in shape; their observable contract should
not.

This plan records the pre-implementation baseline. Its repository observations were
collected with `rg --files`, targeted `rg`, and
`uv run scripts/kit_doctor.py --json` at
`9c4969687f9adbec1eca55cbfb47955d85025026` on 2026-08-23. They intentionally describe
that revision; the delivery slices below are expected to change them.

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

- Extract `post-merge-systemize` into a shared workflow.
- Replace the Claude implementation with a thin binding and add a Codex skill with
  UI metadata.
- Define capability contracts for forge, tracker, reviewer, and notification access.
- Add explicit preflight behavior for unavailable tools and credentials.
- Declare stable Codex tool dependencies in `agents/openai.yaml`; keep optional
  backends as visible degraded paths.

Done when either runtime can execute the retro workflow and produce the same durable
artifacts.

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

## Recommended starting slice

Ship Phase 1 together with the narrow Phase 2 correction that removes the
Claude-specific memory checker from Codex. This creates the acceptance contract and
removes the clearest incorrect runtime behavior before broader porting begins.
