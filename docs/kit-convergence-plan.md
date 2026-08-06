# Convergence plan — one kit, two runtimes, one adopter

> **This is input to a planning session, not the plan.** It records what was
> verified on 2026-08-05/06, what blocks, and the questions a planning session
> has to settle. The phase shapes below are a proposal to argue with. Anything
> here stated as fact names how it was established; anything stated as a guess
> says so.
>
> The living plan remains `kit-handoff.md`. This document exists because the work
> spans several sessions and the handoff is a handoff, not a roadmap.

## The goal

**cs-toolkit uses the devkit rather than its own modified or historical copy of
it**, and **Codex is a first-class runtime rather than a partially-wired one.**

Those are separate goals that share a critical path: you cannot converge an
adopter you cannot measure, and you cannot measure with instruments that are
themselves wrong about a vendored, sized-down install — which is exactly
cs-toolkit's shape.

## Verified state

Established by running the named commands on 2026-08-05/06, not from memory.
Re-derive anything load-bearing before acting on it — some of it will have moved.

### cs-toolkit's install

`python3 scripts/devkit/kit_doctor.py --manifest <kit>/kit-manifest.json`, run in
`/Users/topi/Coding/in-parallel/cs-toolkit`:

- A **sized-down adoption**: `kit_doctor.py` and `lib/kitconfig.py` are vendored;
  the rest of the engines, the hooks and the templates are not.
- Baseline recorded from kit `d3faafb`. Two files report **stale, byte-identical
  to what was installed** — replacing them loses nothing local.
- `⚠ pre-push hook: NOT installed`.
- `.devkit-install.json` absent, so there is no install record beyond the manifest.

### The fork that matters

`.claude/settings.json` there registers `scripts/hooks/pr_followup_hook.py` —
**not** the configured engines path, `scripts/devkit/hooks/`. Consequences,
established by reading the file and grepping the manifest:

- It is **absent from cs-toolkit's manifest**, so the drift check cannot see it.
  It will never be reported stale however far the kit moves.
- It has no `--runtime`, so a Codex session there would be handed Claude's review
  command at Claude's model — the defect `#301` was about.
- It has no `tool_response` gate, so it is the pre-`#302` behaviour that mandates
  a watch loop for PRs that do not exist.

**This is the clearest case of the fork the goal is about, and the cheapest to
un-fork.** It is also the only divergence currently invisible to tooling.

### Runtime parity, in the kit itself

Read off the filesystem, `docs/agentic-dev-kit/workflows/` against
`.claude/commands/` and `.agents/skills/`:

- **Both runtimes:** `session-start`, `pr-watch`, `parallel`, `wrap-up`.
- **Claude only, and with no shared definition to bind:** `adopt`, `upgrade`,
  `post-merge-systemize`, `triage-friction-log`. These are the *lifecycle*
  workflows — Codex can use the kit but cannot adopt, upgrade or maintain it.
- **`parallel-headless`** has a shared definition and no binding on either side.
- **SessionStart hooks** (`check_doc_budget.py`, `check_memory_budget.py`) fire on
  Claude only. Principle #1's budget mechanism reaches one runtime.
- The **safety-critical doctrine is shared** (`docs/agentic-dev-kit/`), but its
  path-scoped trigger lives in `.claude/rules/` and is Claude-only. The rule
  exists as prose on Codex with nothing surfacing it when it matters — the kit's
  own Principle #8, unmet. That is `#273`.
- The PR follow-through hook reaches both as of `#301`, with the caveat that Codex
  needs the operator to trust it via `/hooks` and `init.sh` only prints the
  registration.

### What blocks measurement

Open issues that bite **cs-toolkit's exact configuration**, not hypothetical ones:

- `#286` — a sized-down adoption reports N missing forever, so an intact install
  and a broken one are indistinguishable. cs-toolkit reports missing engines today
  *by design*, and nothing separates that from damage.
- `#285` — `kit_doctor`'s Usage block hardcodes `scripts/`, so every command it
  prints is wrong in a vendored adopter. cs-toolkit vendors to `scripts/devkit`.
- `#290` — no state for "exists but is not usable".
- `#287` — the shared workflows assume engine *capabilities*, not just paths.
- `#283` — `/upgrade` step 4 and the copied release manifest.
- `#297` — `init.sh` has no no-clobber mode, which is why `/adopt` stages and
  stops rather than running it.

## Proposed shape — argue with this

Dependencies are the point; the ordering follows from them.

**Phase 0 — make divergence visible.** Independent of everything else. Move the hook into the tracked engines path so
drift is reportable at all; take the current engine version with it; replace the
two stale files; record an install baseline.

**The move is not a file move.** cs-toolkit's `.claude/settings.json` invokes
`scripts/hooks/pr_followup_hook.py` by absolute path, and any `.codex/hooks.json`
it gains will too. Relocating the file without editing both registrations leaves
each runtime invoking a path that no longer exists. The interpreter does fail —
`python3` on a missing script writes to stderr and exits 2, checked — but a
`PostToolUse` hook failure does not halt the session, so what the operator
actually observes is a hook that stopped firing. Exactly HOW each runtime
surfaces hook stderr is not established here and is worth checking before
relying on the failure being noticed.

**Nothing will repair that automatically.** `init.sh` prints both registrations
and writes neither, deliberately (`#303`). That decision is right for safety and
it means a path change is now entirely manual, on every runtime, in every adopter.
Worth weighing when this phase is scheduled: the registrations must be edited in
the same change as the move, not after it.

**Done when** the hook FIRES on both runtimes from the new path — verified by
running it, not by reading the config — and `kit_doctor` reports it as a tracked
file whose state is a fact rather than an absence. A completion check that only
asserts the file is tracked would pass on a dead hook.

*(This paragraph exists because a review bot caught the original Phase 0 calling
the move "safe" while omitting the registrations. It was neither safe nor a move.)*

**Phase 1 — make the instrument honest.** `#285` and `#286` at minimum. **Done
when** `kit_doctor` in cs-toolkit distinguishes *deliberately sized down* from
*broken*, and prints commands that work there.

**Phase 2 — make re-rendering safe.** `#297`. **Done when** something can run
`init.sh` in an adopter without the operator having to reason about which files
it will overwrite. `#304` is adjacent and may share the fix.

**Phase 3 — converge the install.** Vendor the remaining engines and the Codex
bindings that exist. **Done when** `kit_doctor --manifest <kit>` reports no
unexplained divergence.

**Phase 4 — close the runtime gaps in the kit.** The SessionStart hooks, then
`#273`, then extracting shared definitions for the four Claude-only workflows.
This is the largest piece and the least urgent for cs-toolkit specifically.

Phases 0 and 1 can proceed in parallel. Phase 3 depends on 1 and 2. Phase 4 is
independent of all of them and could start any time.

## Questions the planning session must settle

These are genuinely open. Deciding them by default is how this goes wrong.

1. **Is cs-toolkit's sized-down adoption intentional and permanent, or an artifact
   of when it was installed?** The whole plan branches here. If sized-down is the
   destination, `#286` becomes the most important issue in the list and Phase 3
   shrinks to almost nothing. If full adoption is the destination, Phase 3 is the
   bulk of the work.
2. **Is Codex meant to be first-class in cs-toolkit, or is it a Claude repo that
   Codex occasionally visits?** Determines whether Phase 4 is on this critical
   path or a separate track.
3. **Does Codex expose a SessionStart event?** Not verified. If it does, the
   budget-hook gap is the cheapest parity win available and belongs early. If not,
   that gap needs a different answer entirely.
4. **Should the four lifecycle workflows get shared definitions, or is
   Claude-only correct for them?** There is a real argument that adoption and
   upgrade are operator-driven and single-runtime is acceptable. `AGENTS.md`'s
   parity rule suggests otherwise. This has not been argued either way.
5. **Who runs the upgrade, and does it get reviewed?** cs-toolkit is a live repo.
   An upgrade that lands a bad engine is a different risk class from a kit-side PR.

## What this work will probably surface

Stated as a prediction so it can be checked later, not as a claim.

Most of the issues in "What blocks measurement" read as though they were found by
*reasoning* about adopters rather than by upgrading one. cs-toolkit is the kit's
real adopter, so using it as the forcing function should validate or refute them
— and is likely to surface more. **Budget for that.** Treating the first upgrade
as a routine sync is the assumption most likely to be wrong.
