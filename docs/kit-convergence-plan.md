# Convergence plan — one kit, two runtimes, one adopter

> **The planning session ran on 2026-08-06 and this document now records its
> result: the questions are settled and the sequence below is agreed, no longer
> a proposal.** Anything here stated as fact names how it was established;
> anything stated as a guess says so.
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

Established by running the named commands on 2026-08-05/07, not from memory.
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

Re-run 2026-08-06, same command, same directory: unchanged in substance. The
baseline lives inside cs-toolkit's own `kit-manifest.json` (written by
`--record-install`), so "no record beyond the manifest" means the manifest *is*
the record. The stale pair is `scripts/devkit/kit_doctor.py` and
`docs/agentic-dev-kit/fallback-review-panel.md`.

**The sized-down shape is declared in writing.** cs-toolkit's
`config/dev-model.yaml` header (read 2026-08-06) states `ADOPTION STATUS:
PHASE 1 (additive install only)` of a deliberately phased adoption, and names
its own later phases with their blockers: Phase 2 (the kit's `pr_watch.py` +
`dev_session.sh`) blocked until cs-toolkit's nightly fixer stops reading `done`
— its `.claude/commands/pr-watch.md` still reads it, checked 2026-08-06 — and
Phase 3 (the kit's `pre-push`) blocked on kit `#46`, still open. Question 1
below was largely answered by this file; the session confirmed it as current
intent rather than an artifact.

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

Measured 2026-08-06 (`wc -l` and `diff` against this repo's
`scripts/hooks/pr_followup_hook.py`, run in cs-toolkit): the fork is a 66-line
ancestor dated 2026-06-04; the kit's current hook is 454 lines. Un-forking is a
replacement, not a reconciliation of variants.

**Its import closure is already satisfied at the destination, so it costs
nothing to carry.** Re-measured 2026-08-07: the hook's only non-stdlib import is
`kitconfig`, and it resolves that module itself —
`Path(__file__).resolve().parent.parent / "lib"`, at
`scripts/hooks/pr_followup_hook.py:163-166`. From the target path
`scripts/devkit/hooks/` that resolves to `scripts/devkit/lib/kitconfig.py`,
which cs-toolkit already vendors and which `diff` reports byte-identical to this
repo's `scripts/lib/kitconfig.py`. So the phase carries one file rather than a
file and its dependencies — but note the resolution is relative to *the hook*,
which is a second reason the destination directory is not free to vary: a `lib/`
sitting beside the hook's own directory is part of the contract, not an accident
of layout.

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

## Agreed sequence — settled 2026-08-06

Dependencies are the point; the ordering follows from them. Three items start
immediately and in parallel; the critical path runs through the kit's
instrument work to the upgrade session; one kit track runs beside it.

### Immediately, in parallel

**Phase 0 — make divergence visible** (a cs-toolkit PR, through its own
review). Independent of everything else. Move the hook into the tracked engines
path so drift is reportable at all; take the current engine version with it —
its import closure is already satisfied at that destination, measured under
*The fork that matters* above, so there is nothing further to carry; **create
`.codex/hooks.json` there with `--runtime codex`** (question 2's decision —
today no hook of any kind fires for a Codex session in cs-toolkit); replace the
two stale files; re-record the install baseline.

**The move is not a file move.** cs-toolkit's `.claude/settings.json` invokes
the hook as `python3 "$CLAUDE_PROJECT_DIR/scripts/hooks/pr_followup_hook.py"`
(read 2026-08-07; an earlier revision of this paragraph said "by absolute path",
which was wrong — the registration is project-dir-relative), and any
`.codex/hooks.json` it gains will carry a path of its own. **Neither form
survives the file moving**, which is what this paragraph is actually about:
relocating it without editing both registrations leaves each runtime invoking a
path that no longer exists. The interpreter does fail —
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

**`#304`, in the kit** — the ready starter, small and adjacent to the `init.sh`
work below; its body names the smaller of two repairs (`seed_doc` re-emitting
the kit-own marker).

**The SessionStart budget hooks on Codex, in the kit.** Question 3 is settled:
the event exists (see below), so this is the cheapest parity win available.
Registration printed, never written, per the `#303` doctrine. **Done when** the
hooks fire in a real Codex session — verified by running one, the same standard
as Phase 0.

### The critical path

**Phase 1 — make the instrument honest.** `#285` and `#286` at minimum. `#286`
is needed on every branch of question 1 — even at the staged destination,
templates stay out of cs-toolkit (its narrative docs already exist and are in
use), so a declared install set is what lets `kit_doctor` ever say "intact".
**Done when** `kit_doctor` in cs-toolkit distinguishes *deliberately sized
down* from *broken*, and prints commands that work there.

**Phase 2 — make re-rendering safe.** `#297`. **Done when** something can run
`init.sh` in an adopter without the operator having to reason about which files
it will overwrite. `#304` is adjacent and may share parts of the change.

**The fixer predicate, in cs-toolkit.** Its nightly fixer reads `done` from its
own `pr_watch.py`; the kit's `done` means MERGEABLE, so swapping engines
without swapping the predicate to `converged` is a silent infinite poll —
cs-toolkit's config says exactly this and phased its adoption around it. A
small cs-toolkit PR; it gates only the engine swap. This dependency was missing
from the first draft of this plan.

**Phase 3 — converge the install.** After Phases 1 and 2 and the fixer
predicate: an agent session working **in cs-toolkit** (question 5's decision)
performs the upgrade and lands it as a normal PR through cs-toolkit's own
review; kit defects it surfaces route upstream as kit issues, not into the
adopter's PR. Engines per cs-toolkit's declared Phase 2, the declared install
set recorded, SessionStart wiring on both runtimes there. **Done when**
`kit_doctor --manifest <kit>/kit-manifest.json` reports no unexplained
divergence.

### The kit track beside it

**Phase 4 — runtime parity in the kit, sliced** (questions 2 and 4). `#273`
first — its failure mode is the silent one. Then shared definitions for `adopt`
and `upgrade`, the slice the standing `#243` decision named — ideally before
Phase 3 so the upgrade session can follow the shared definition, though not a
hard gate.

### Deferred tail, deliberately

Kit `#46` and then cs-toolkit's `pre-push` (its declared Phase 3 — the one
piece of the staged destination with no schedule yet); shared definitions for
`post-merge-systemize` and `triage-friction-log`; a binding for
`parallel-headless`, which has a shared definition and no binding on either
side.

## The questions, settled — 2026-08-06

Questions 1, 2, 4 and 5 are operator decisions from the planning session;
question 3 was verified. The original phrasings are in this file's git history.

1. **Staged adoption, as cs-toolkit's config writes it.** The sized-down
   install is Phase 1 of cs-toolkit's own declared staging, and that staging is
   confirmed as the destination — the later phases get scheduled (above) rather
   than abandoned or collapsed into one push. Templates stay out permanently,
   which is why `#286` survives every branch of this question.
2. **Codex is first-class in both repos.** Matches the standing 2026-08-04
   decision ("equal-enough development environment, as soon as possible").
   Concretely: Phase 0 includes cs-toolkit's `.codex/hooks.json`, and Phase 4
   is on this plan rather than on a someday-track.
3. **Codex exposes SessionStart — verified.** Two sources, 2026-08-06: the
   installed `codex-cli 0.42.0`'s user-level `~/.codex/hooks.json` on this
   machine registers a `SessionStart` hook (written by a shipping third-party
   integration whose status display depends on it firing), and current Codex
   hooks documentation lists the event with `startup` / `resume` / `clear`
   matchers — the same shape cs-toolkit's Claude config already uses. A
   fire-it-and-see check is still owed by the implementing session; the
   budget-hook item's done-when demands it.
4. **The lifecycle workflows are extracted sliced: `adopt` + `upgrade` first.**
   The daily loop already works on Codex; the two retro workflows follow later.
   This re-affirms the `#243` slice rather than inventing a new scope.
5. **The upgrade is an agent session in cs-toolkit, reviewed as a normal PR
   there.** Kit findings route upstream as issues — the decision the `#278`
   upgrade already operated under, now stated for this one.

## What this work will probably surface

Stated as a prediction so it can be checked later, not as a claim.

Most of the issues in "What blocks measurement" read as though they were found by
*reasoning* about adopters rather than by upgrading one. cs-toolkit is the kit's
real adopter, so using it as the forcing function should validate or refute them
— and is likely to surface more. **Budget for that.** Treating the first upgrade
as a routine sync is the assumption most likely to be wrong.
