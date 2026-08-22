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
    status: gap
    shared: null
    claude: .claude/commands/post-merge-systemize.md
    codex: null
  - name: parallel-headless
    status: companion
    shared: docs/agentic-dev-kit/workflows/parallel-headless.md
    claude: null
    codex: null
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
- `companion` — shared material is loaded by another workflow and deliberately has no
  direct runtime command or skill.

The machine-readable declaration is authoritative for file coverage. The matrix below
records broader capability parity that cannot be expressed as an adapter path.

## Capability matrix

| Capability | Shared contract | Claude Code | Codex | Status / exit |
|---|---|---|---|---|
| Repository instructions | `AGENTS.md` | `CLAUDE.md` imports it | reads `AGENTS.md` directly | aligned |
| Workflow adapters | `docs/agentic-dev-kit/workflows/` | `.claude/commands/` | `.agents/skills/` | declaration above is authoritative |
| Safety-critical doctrine | `docs/agentic-dev-kit/safety-critical-changes.md` | path-scoped `.claude/rules/` binding | broad `AGENTS.md` routing only | gap: add an enforceable Codex binding without forking doctrine |
| Document-budget tripwire | `check_doc_budget.py` | `SessionStart` | `SessionStart` | aligned |
| Runtime memory tripwire | runtime-specific artifact | `check_memory_budget.py` checks Claude's `MEMORY.md` | no corresponding repository artifact | intentional difference: never invoke the Claude engine on Codex |
| PR follow-through | `pr_followup_hook.py` | `PostToolUse` with Claude runtime mapping | `PostToolUse` with Codex runtime mapping | aligned; trust remains a Codex operator step |
| Review fallback | shared panel doctrine and receipt | isolated reviewers where available | isolated reviewers where available | aligned outcome; compute controls remain runtime-specific |
| Capability tiers | `config/dev-model.yaml` neutral tiers | model mapping | reasoning-effort mapping | gap: calibrate Codex model plus effort mappings |
| Headless lane isolation | shared lane descriptor and contract | launcher-dependent | launcher-dependent | gap: Codex needs a launcher that can apply worktree and environment fields |
| Command permissions | repository policy | `.claude/settings.json` permissions | no shipped project rules | gap: decide and ship the Codex policy surface |
| Tracker and notification tools | backend names in config | runtime client or MCP | runtime client or MCP | gap: declare dependencies and preflight behavior |
| Adapter upgrade | shared workflow refresh | existing adapter retained | existing adapter retained | gap: runtime-specific fixes can remain stale |
| Drift inspection | `kit_doctor` | registration paths resolved | registration paths resolved | gap: semantic hook and adapter checks remain |

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
