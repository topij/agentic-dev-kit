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

Established by running the named commands on 2026-08-05/08, not from memory.
Re-derive anything load-bearing before acting on it — some of it will have moved.

> **2026-08-08 — the critical path has cleared and this section is now partly
> historical.** cs-toolkit's Phase 0 merged as `2ab63d255`
> (`in-parallel-oy/cs-toolkit#1869`) and its fixer predicate as `bfafe13b7`
> (`#1866`); kit `#285`, `#286` and `#297` are closed. What each subsection below
> still gets right and wrong is marked inline — read the markers, because two
> paragraphs here were load-bearing arguments that the Phase 0 run falsified.
> The adopter's own account is
> [`adopter-forcing-function-memo_2026-08-07.md`](adopter-forcing-function-memo_2026-08-07.md).

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
un-fork.**

> **2026-08-08 — this paragraph used to end "It is also the only divergence
> currently invisible to tooling," and that was false.** `init.sh` is the
> counterexample: it is in neither `kit_doctor.KIT_OWNED` nor
> `kit-manifest.json`, so the file that *performs* the install is the one file
> the doctor structurally cannot report drift on. cs-toolkit's copy measures 852
> differing lines against kit `3761bec` while its doctor reports `13 unchanged,
> 0 differ, 0 missing` and exit 0 — every statement in that report true, and the
> drift entirely outside what it ranges over. Verified in this repo 2026-08-08 by
> parsing the `KIT_OWNED` tuple (35 entries, no `init.sh`) and searching the
> manifest. That is [`#360`](https://github.com/topij/agentic-dev-kit/issues/360).
>
> The correction is kept rather than quietly deleted because the sentence was
> **load-bearing twice**: it was the argument for why Phase 0 was the cheapest
> un-fork, and it implied the invisible surface had been enumerated. Only the
> first half survives. Phase 0 was still the cheapest un-fork; the enumeration
> was never done, and one adopter upgrade found the file that most needed it.

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
`.claude/commands/` and `.agents/skills/`. **Re-read 2026-08-08 — the first two
bullets had moved, and in the direction that removes work from this plan.**

- **Both runtimes:** `session-start`, `pr-watch`, `parallel`, `wrap-up`, and — as
  of `#330` — **`adopt` and `upgrade`**.
- **Claude only, and with no shared definition to bind:** `post-merge-systemize`,
  `triage-friction-log`. Codex can now adopt and upgrade the kit; what it still
  cannot do is run the two retro workflows.

  > **2026-08-08 correction.** This bullet used to name `adopt` and `upgrade`
  > here too, and Phase 4 below still asks for their shared definitions as
  > though unbuilt. They exist: `docs/agentic-dev-kit/workflows/adopt.md` (409
  > lines) and `upgrade.md` (386), with thin bindings on both runtimes — a
  > 9-line `.claude/commands/adopt.md` and an `.agents/skills/adopt/SKILL.md`.
  > `#330` did this, and `KIT_OWNED` has tracked both since.
  >
  > This matters beyond bookkeeping: the adopter memo read this section, took
  > the gap at face value, and recommended promoting the extraction to a **hard
  > Phase 3 gate** — an `L`-sized kit build that is already done. A stale plan
  > did not merely misinform a reader; it nearly bought a sprint. The real
  > residue is much smaller and belongs to the adopter: cs-toolkit's manifest
  > lists both workflow docs in `not_installed`, so **Phase 3 installs them**
  > (see that phase below).
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

Open issues that bite **cs-toolkit's exact configuration**, not hypothetical ones.
**States re-checked 2026-08-08 with `gh issue view` per number:**

- ~~`#286`~~ — **closed.** A sized-down adoption used to report N missing forever;
  `not_installed` now separates deliberately-sized-down from broken.
- ~~`#285`~~ — **closed.** `kit_doctor`'s Usage block no longer hardcodes
  `scripts/`, so its printed commands work in a vendored adopter.
- ~~`#297`~~ — **closed.** `init.sh` has a no-clobber mode.
- `#290` — no state for "exists but is not usable". **Still open.**
- `#287` — the shared workflows assume engine *capabilities*, not just paths.
  **Still open.**
- `#283` — `/upgrade` step 4 and the copied release manifest. **Still open.**
- **`#360` — new, and the one this section was missing entirely:** `init.sh` is in
  neither `KIT_OWNED` nor the manifest, so the installer is outside the
  measurement. See the correction under *The fork that matters*. This is now the
  blocker in front of Phase 3 — the reasoning is under that phase below.

**The prediction at the foot of this document was checked, and it held.** That
section says most of the issues in this list "read as though they were found by
*reasoning* about adopters rather than by upgrading one," and asked for the
forcing function to validate or refute them. One Phase-0-sized change in one
adopter produced `#358`, `#359` and `#360` — and `#360` contradicts a stated
premise of this plan rather than adding to a list.

## Agreed sequence — settled 2026-08-06

Dependencies are the point; the ordering follows from them. Three items start
immediately and in parallel; the critical path runs through the kit's
instrument work to the upgrade session; one kit track runs beside it.

> **Progress, 2026-08-08.** Phases 0, 1 and 2 and the fixer predicate are **done**
> — so every gate this sequence named for Phase 3 has cleared, and Phase 3 is
> unblocked *as written*. It should still not start first: the Phase 0 run
> surfaced `#360`, and Phase 3 **is** the upgrade while `init.sh` is what performs
> it. Running a converge-the-install session against an installer that no
> instrument can measure is the wrong order. The revised order is under *The
> critical path*.

### Immediately, in parallel

**Phase 0 — make divergence visible** — **DONE**, merged in cs-toolkit as
`2ab63d255` (`in-parallel-oy/cs-toolkit#1869`), 2026-08-07T21:06Z. Its done-when
was met on the terms below: the hook fires on both runtimes from the new path,
established by running it rather than by reading the config. The description that
follows is kept as the record of what the phase was, and because its two
**Nothing will repair that automatically** and **The move is not a file move**
paragraphs generalise past it — both are live constraints on Phase 3.

*What it was:* a cs-toolkit PR, through its own review, independent of everything
else. Move the hook into the tracked engines
path so drift is reportable at all; take the current engine version with it —
its import closure is already satisfied at that destination, measured under
*The fork that matters* above, so there is nothing further to carry; **create
`.codex/hooks.json` there with `--runtime codex`** (question 2's decision —
before this phase no hook of any kind fired for a Codex session in cs-toolkit);
replace the two stale files; re-record the install baseline.

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

> **What the phase produced beyond its own done-when**, and the reason the
> *Nothing will repair that automatically* paragraph above is now doubly load
> bearing: the registration cs-toolkit copied from the kit carries
> `$(git rev-parse --show-toplevel)`, which yields the **empty string** in a
> `.git`-less tree — so the command becomes an absolute path rooted at `/` and
> `python3` exits 2, and because a `PostToolUse` failure does not halt a session,
> the hook silently stops firing. That is the *exact* failure mode this phase's
> own paragraph describes for a moved hook, arriving by a different route.
> [`#359`](https://github.com/topij/agentic-dev-kit/issues/359).
>
> **The adopter deliberately carried the defect rather than fix it downstream**,
> because hardening its copy would have re-forked the registration Phase 0 had
> just un-forked. That is the right call under this plan's goal, and it makes
> `#359` a kit debt with an adopter waiting on it — fix it here before Phase 3
> re-prints the registrations, so the operator is told the right thing once
> instead of the current thing and corrected later.

**`#304`, in the kit** — the ready starter, small and adjacent to the `init.sh`
work below; its body names the smaller of two repairs (`seed_doc` re-emitting
the kit-own marker).

> **2026-08-08, settled: `#304` is NOT coupled to `#360` and stays open.** An
> earlier revision of this paragraph — written before `#360` was worked — said
> "now coupled to `#360` … treat the two as one piece of work", following the
> adopter memo's recommendation. That was reversed on evidence a few hours later
> and the reversal is under *Before Phase 3* item 1: `#304` needs a line-1
> `devkit-source: kit-own` marker to act on, and cs-toolkit's `AGENTS.md` and
> `CLAUDE.md` open with `# CS-Toolkit` and carry none, so `_seedable` leaves both
> untouched there and **`#304` blocks nothing in Phase 3.**
>
> The old wording is corrected here rather than only in the newer section because
> an adversarial review lens found the two passages contradicting each other and
> named the consequence precisely: a session following this document's own
> `▶ Next:` pointer reaches "coupled to `#360`" *before* it reaches "deliberately
> not bundled", and could reasonably conclude `#304` was resolved when `#360`
> closed. It was not.

**The SessionStart budget hooks on Codex, in the kit.** Question 3 is settled:
the event exists (see below), so this is the cheapest parity win available.
Registration printed, never written, per the `#303` doctrine. **Done when** the
hooks fire in a real Codex session — verified by running one, the same standard
as Phase 0.

### The critical path

**Phase 1 — make the instrument honest** — **DONE.** `#285` and `#286` both
closed. `kit_doctor` in cs-toolkit now distinguishes *deliberately sized down*
from *broken* (`✓ intact for this adoption — 22 file(s) declined`) and prints
commands that work at a vendored engines path.

**Phase 2 — make re-rendering safe** — **DONE.** `#297` closed; `init.sh` has a
no-clobber mode. `#304` is still open and is **not** part of `#360`'s work — see
the note under *`#304`, in the kit* above for why that grouping was reversed.

**The fixer predicate, in cs-toolkit** — **DONE**, merged as `bfafe13b7`
(`in-parallel-oy/cs-toolkit#1866`). It landed *after* this plan's 2026-08-06
snapshot, which is why earlier revisions listed it as outstanding. Its nightly
fixer read `done` from its own `pr_watch.py` while the kit's `done` means
MERGEABLE, so swapping engines without swapping the predicate to `converged`
would have been a silent infinite poll. Verified 2026-08-07 by `git log -S` on
that repo's `.claude/commands/nightly-fixer.md` and `pr-watch.md`, plus a
repo-wide grep confirming no consumer still reads the `done` key.

**Before Phase 3 — the kit work the forcing function found.** This is new as of
2026-08-08 and sits *between* the cleared gates and Phase 3, because Phase 3 is
the upgrade and `init.sh` is what performs it.

> **Status, end of 2026-08-08: items 1 and 2 are DONE, item 3 remains.** `#360`
> closed (PR `#362`) and `#359` closed (PR `#366`); `#358` is the only one left,
> and the coverage half of it is narrower than its issue proposes — the
> measurement is a comment on that ticket. `#304` was **removed** from this list
> rather than completed; the reasoning is under item 1.
>
> One consequence to carry into Phase 3, learned while doing item 1: `KIT_OWNED`
> lives in the **engine**, not the manifest, so passing `--manifest` alone does
> not backport a newly tracked path. cs-toolkit's vendored `kit_doctor.py` must be
> refreshed before its own doctor can see `init.sh` at all.

1. **`#360`** — **DONE** (PR `#362`). Track `init.sh`. Its issue frames the
   tracking model as a design
   call between three options, on the premise that an adopter's copy is
   *expected* to diverge because it "encodes answers to the adoption prompts" —
   so a plain `KIT_OWNED` entry would report every adopter permanently
   `locally-edited`, trading an invisible problem for a permanently-red one and
   re-creating the failure `#286` was just closed to fix.

   **That premise is false, checked 2026-08-08, and the design question dissolves
   with it.** cs-toolkit's `init.sh` is **byte-identical to kit commit
   `7485512b`** (2026-07-26) — found by hashing its copy and scanning every
   `init.sh` blob in this repo's history for a match. So all 852 differing lines
   are version drift and **none** are local rendering. Two supports: `init.sh`
   never writes to itself (it writes `config/dev-model.yaml` and renders
   `docs/templates/`), and nothing in the kit tells an adopter to edit it.

   Consequences for the fix, read off `_drift_state`: a tracked, unedited,
   behind-the-kit copy reports **`stale`** ("installed X, kit ships Y"), which is
   both true and actionable, and it clears to `unchanged` when the adopter
   updates the file. Not permanent, and not `locally-edited`. So **no new role and
   no file split** — a plain `KIT_OWNED` + manifest entry is correct. One
   migration note that is not a defect: a copy present locally but absent from an
   older recorded baseline reports `differs` ("not in baseline") until the adopter
   re-records, because `new-upstream` only covers files that are *absent*.

   **Acceptance:** `kit_doctor` in cs-toolkit can say something true about its
   installer, and the `_still_a_skeleton`-vs-seed-guard question a review bot
   raised on the Phase 0 PR becomes *answerable* — with the installer untracked
   there is currently no way to tell a doctor defect from installer drift.

   **`#304` is deliberately NOT bundled here**, against the memo's
   recommendation. It shares the file, but it fires only when `init.sh` runs in
   **the kit's own repo**: it needs a line-1 `devkit-source: kit-own` marker to
   act on, and cs-toolkit's `AGENTS.md`/`CLAUDE.md` open with `# CS-Toolkit` and
   carry no marker (checked 2026-08-08), so `_seedable` leaves both untouched
   there. It therefore blocks nothing in Phase 3. Its own issue's smaller repair
   — `seed_doc` re-emitting the marker — makes the damage *recoverable* without
   preventing it, since the kit's contract is still replaced by the adopter
   template on the first run; the repair that actually prevents it needs the
   kit-repo detector `#291` also wants and `#289` declined to add inside a fix
   round. That is an operator design call, not an overnight one.
2. **`#359`** — **DONE** (PR `#366`), before Phase 3 re-prints the registrations.
   The registration now bails cleanly instead of running `python3` against a path
   built from an empty string, and every clause of it is pinned by a test that
   executes it. `#363` — no test *executed* a registration, which is why `#359`
   shipped — stays open: this closed the gap for one registration, not the class.
3. **`#358`** — **remaining.** Two prose paths, plus the coverage question its
   issue raises. That question is answered on the ticket and the answer is "not as
   proposed": a position-independent match over the closed `KIT_OWNED` set flags
   two legitimate lines in `adopt.md` alongside the two real ones, because the
   distinguishing feature is line position — which is what the existing anchored
   regex already uses. Doctrine-scoped it is clean. The wider form needs a
   judgment call about `adopt.md:142` first.

**Phase 3 — converge the install.** After the three items above: an agent session
working **in cs-toolkit** (question 5's decision)
performs the upgrade and lands it as a normal PR through cs-toolkit's own
review; kit defects it surfaces route upstream as kit issues, not into the
adopter's PR. Engines per cs-toolkit's declared Phase 2, the declared install
set recorded, SessionStart wiring on both runtimes there. **Done when**
`kit_doctor --manifest <kit>/kit-manifest.json` reports no unexplained
divergence.

**Phase 3 also installs `adopt.md` and `upgrade.md` there**, which is the residue
of the correction under *Runtime parity* above. cs-toolkit's manifest lists both
in `not_installed`, so a Phase 3 session in that repo has **no installed workflow
document to follow** — it would improvise the very procedure the kit exists to
standardise. The shared definitions and both runtime bindings already exist
kit-side, so this is an install step in the adopter's own PR, not kit work.

### The kit track beside it

**Phase 4 — runtime parity in the kit, sliced** (questions 2 and 4). `#273`
first — its failure mode is the silent one. ~~Then shared definitions for `adopt`
and `upgrade`, the slice the standing `#243` decision named — ideally before
Phase 3 so the upgrade session can follow the shared definition, though not a
hard gate.~~ **That half is done** (`#330`); see the correction under *Runtime
parity, in the kit itself*. What remains of the `#243` slice is
`post-merge-systemize` and `triage-friction-log`, already in the deferred tail
below. So Phase 4 is now `#273` alone.

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
   **2026-08-08: this decision has been carried out** for its named slice —
   `#330` extracted both and bound them on both runtimes.
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

### Checked, 2026-08-08 — validated

**Phase 0 alone, one adopter, one file moved: three kit issues.** `#358`, `#359`,
`#360`. The prediction asked to be checked and this is the check, so the score is
worth stating precisely rather than favourably:

- **`#360` did more than add to the list — it falsified a stated premise** of this
  document (*The fork that matters*). A prediction that new issues would appear is
  weaker than what happened, which is that an argument the plan relied on was
  wrong.
- **The count is a floor, not a total.** Phase 0 was scoped to one file's
  relocation and two stale replacements. Phases 1–3 touch the engines, the
  manifest and both runtimes' wiring.
- **One item the adopter deliberately did not file**, and it is the most
  interesting: during the Phase 0 session a live Claude session kept invoking the
  *pre-move* hook path at a moment when that string existed in no file on disk.
  The observable is certain; the mechanism (stale snapshot vs. both registrations
  active) is not established. Plausibly runtime behaviour rather than a kit
  defect — but it bears directly on how `#303`'s hand-maintained registrations
  behave in practice, so it is filed now for a kit session to settle rather than
  left in a memo.

**A second, unpredicted finding: the forcing function also audits this document.**
Two of the corrections above (`init.sh` invisible to tooling; `adopt`/`upgrade`
unextracted) were plan text that a reader acted on. The second one nearly cost a
sprint — the adopter memo recommended promoting already-finished work to a hard
gate. So the cost of a stale plan is not only a misinformed reader; it is
*confidently scoped work that does not need doing.* Re-derive load-bearing facts
before acting on them, which is what the header of *Verified state* asks for and
what neither of those two readings did.
