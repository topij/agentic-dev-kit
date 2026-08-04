# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it at the end (`/wrap-up`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-08-04 — **A workflow doc cannot host a safety-critical guard, because
nothing executes it.** `/adopt` settled `#105` by *stopping* before the destructive step
rather than guarding it. The durable result is `#297` and the reason it must exist.

## Latest session — 2026-08-04 (the guard that could not live in a document)

**Theme —** `/adopt`'s contract is *"never overwrite an existing file"*; `init.sh`'s
`_seedable` deliberately renders over anything carrying a kit marker. Both are right, and
this session connected them. The mechanisms built to make that safe — a
backup-and-restore, a re-classify-and-diff, an advisory gate, a gate fused to the run —
**each shipped a new way to destroy an adopter's file**. The scope was cut instead.

- **`#105` — closed** (`1592380`, PR `#294`). `/adopt` stages the adoption and stops:
  `docs/templates/` and `init.sh` in the copy list, the pre-push hook reaching the repo at
  all, `config/*.local.yaml` gitignored before the PR opens, a stop when the adopter has
  their own `init.sh`, and a handoff giving the operator the six seedable paths from *their*
  config. A Codex adopter arriving via `/adopt` now gets an entry point.
- **`/adopt` never runs `init.sh`.** The document carries no authored shell; the remaining
  fenced blocks are single-line kit commands. That is the fix, not a limitation of it.
- **Filed:** `#295`, `#296`, `#297`, `#298`; a fourth occurrence on `#270`.

**Learned**

- **Every guard written into a workflow doc is untested code.** No test, linter or CI runs
  it — `make test` passes in full without touching a line. Each defect class found here
  (locale-dependent marker match, staleness, 2-of-6 coverage, an unscoped `grep` resolving a
  decoy path, a BSD-only `mktemp` building an empty-tree probe) was a predicate `init.sh`
  already owns, restated and diverging on an input nobody could test. The only repair that
  held was **deleting the restatement**. This is `#297`'s whole argument.
- **A fix round's own output is the likeliest place for the next defect.** Repeatedly a
  commit corrected one passage and left an adjacent one asserting the old thing — including
  one whose message reasoned explicitly about the fact it then failed to apply next door.
  The round-by-round record is on PR `#294`; it is not restated here.
- **The panel's isolation contract has a second hole, and it is not `cp -R`.** A lens ran
  `init.sh` against the live checkout because the tool's cwd resets to the repo root between
  calls and `init.sh` acts on the *current directory*. It rendered over this repo's own
  `AGENTS.md` and `CLAUDE.md` — seedable by design since `#288` — and touched
  `config/dev-model.yaml`. Restored, and verified in the cockpit checkout
  (`git status --short` clean, files byte-identical to `HEAD`, hook firing on a synthetic
  `dev/*` push built with plumbing). `#270`, with the direction: a cockpit-side
  before/after baseline, which was run for the last round and held.
- **Nothing checks the review brief itself.** A lens found a diffstat in its own prompt that
  I had never measured. Contract items govern what a lens reports, not whether what it was
  told is true.
- **I asserted verification I had not performed, more than once** — an end-to-end claim
  whose fixtures excluded the dangerous input, and a consistency claim across four steps
  from a diff that touched one. Both were caught by review, not by me. `#248`'s shape.

**Decided this session (operator)**

- **Ship the safe half; move the guarantee to `init.sh`.** After the fourth mechanism
  failed, scope was cut to the parts carrying no predicate at all. `#297` carries the
  no-clobber mode, where CI can hold it.
- **CodeRabbit's original suggestion was right and I talked us out of it.** It proposed a
  no-clobber mode on the first round; I declined it as forking the semantics `#288`
  unified. A mode flag on one predicate is not a fork — two implementations of that
  predicate is, and that is what I built instead.

**Open, and owned by nothing yet**

- **`#297` is the completion of this work**, not an optional follow-up: until it exists,
  `/adopt` cannot seed anything and the operator runs `init.sh` by hand.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#297` — add `--no-clobber` to `init.sh`**, with tests in `scripts/tests/`. Read
`#297`'s body first: it enumerates the nine findings that argue for it and records that a
mode flag on `_seedable` is not the fork I mistook it for. `/adopt` passes it always;
`init.sh` bare and `/upgrade` keep today's behaviour, where re-rendering a marker is
correct. `#273` direction 1 was this session's inherited starter and is still undone — it
was displaced deliberately, not dropped.

______________________________________________________________________

## Earlier session — 2026-08-04 (the kit's own entry points, and a claim class that outlived the code)

**Theme —** `seed_doc` had two categories, a shipped skeleton and a file the adopter is using,
and the kit's own entry points are a third. Both halves of `#288` followed: `CLAUDE.md` rode
the `cp -r` quickstart into every adopter with nothing rendering, removing or reporting it, so
their Claude sessions loaded *the kit's* contract; and `AGENTS.md` was reached by file
**absence**, so the kit could not ship one and a Codex session working in the kit had no entry
point at all. `#274`'s class, on the two files whose whole job is to be read in the reading
repo.

- **`#288` — the third category** (`af004b9`, PR `#289`). `KIT_OWN_MARKER` on the kit's own
  root `AGENTS.md` and `CLAUDE.md`; an adopter's `init.sh` renders over both; a file carrying
  neither marker is still never touched. `AGENTS.md` holds the contract, `CLAUDE.md` imports
  it with `@AGENTS.md`, so one file states it and both runtimes load it in full.
- **`kit_doctor` now checks both entry points**, through a predicate that must agree with
  `_seedable`. Both sides pin `LC_ALL=C`: `[[:space:]]` is locale-dependent and they matched
  different characters under any real locale.
- **Filed:** `#290`, `#291`, `#292`. **Occurrences:** `#211`, `#120`, `#248`, `#209`, `#274`,
  and `#270`.

**Learned**

- **Each repair to the seed guard introduced the next defect**, all in one predicate. The two
  that destroyed a real file with no backup were both found by *running* `init.sh` against a
  hand-built fixture, never by reading it. `#211`'s thesis; the enumeration is on `#211`.
- **"What checks this new check" was answered wrong three times running** — a guard clause
  added to prevent silent overwrites was itself unpinned; the check added to catch an
  incomplete adoption was itself unchecked; the test added to pin a locale fix was itself
  locale-dependent and would have passed with the fix removed. Each found by mutation, none by
  reading. On `#211`.
- **The claims that survived review longest were the ones whose *form* looked rigorous** — a
  stated `grep` method whose scope was one file while the stale site sat in another, and a
  comment citing "the C locale" in a script that pinned no locale. A cited mechanism reads as
  verification and is not. Enumerated on `#248` as a sub-shape it did not name.
- **The code converged before the prose did, and the gap was most of the review.** The
  destructive findings stopped early; the rounds after them returned record and coverage
  findings almost exclusively. Evidence for `#120` over `#211` — on `#120`.
- **A lens wrote into the live checkout through the isolation route the doctrine prescribes.**
  `cp -R` of a *linked worktree* copies its `gitdir:` pointer, so the copy is not independent
  and `init.sh` in it rewrote the real repo's `.git/hooks/`. Invisible to the contract's own
  attestation, which reports on the handed tree. `#270`.
- **The local gate is weaker than CI.** An apostrophe in an `awk` comment closed the
  single-quoted program; `make test` reported a mass of unrelated pytest failures while CI's
  `sh -n init.sh` names the line. `#292`.

**Decided this session (operator)**

- **Codex as an equal-enough development environment, as soon as possible.** This is a
  standing goal and it lives on no ticket. It moved `#243` back off the backlog — but
  **sliced**: `adopt` + `upgrade` first, since the daily loop already works on Codex and the
  four missing workflows are lifecycle and maintenance.
- **Merged without a dual-lens pass at the merging head.** The last panel ran three commits
  earlier; no receipt was recorded, because one would have claimed coverage that does not
  exist and the engine refuses it once the head moves. The merge gate was the operator's
  decision plus green CI plus a bot review of the parent — stated on `#289` rather than left
  to be inferred from a missing receipt.

**Open, and owned by nothing yet**

- **`#290` and `#291` are one complaint** — a single boolean cannot carry what `kit_doctor`'s
  narrative check now sees, so a directory named `AGENTS.md` reports `in use` and the kit's
  own repo warns about its own entry points forever.
- **Carried forward:** `#243`, `#273`, `#105`, `#285`, `#283`, `#287`, `#286`, `#248`, `#264`,
  `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`, `#190`,
  `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#273` direction 1** — one note on `safety-critical-changes.md` line 10 saying
`.claude/rules/` binds Claude only. It is the smallest step toward the Codex goal above and the
only one whose failure is *silent*: cs-toolkit follows that sentence today and its safety
doctrine reaches one of its two runtimes, so a Codex session touching a kill-path there is
unbound and nothing reports it. Then `#105` (a Codex adopter arriving via `/adopt` still gets
no entry point — this session fixed only the `init.sh` path). Read `#243`'s own scope note
before starting it: its line count is measured, stale, and growing.

______________________________________________________________________

## Earlier session — 2026-08-03 (the aim lever, and the bug the later rounds did not catch)

**Theme —** `#51`'s local half shipped, and the durable result is not the feature. What cost
more to learn than the code did is about *review*: an adopter upgrade found a defect that the
PR's later review rounds did not catch — and the cheapest explanation fails, because the round
pointed directly at the guards it lived in missed it too.

- **`#278` — `kit_commit` in the manifest, and `differs` split three ways** (`a042c82`).
  `STALE` / `LOCALLY EDITED` / `STALE and EDITED`, stated as fact rather than inferred from
  `kit.version`, which tracks the config schema and so never moved when kit files did.
- **`#280` — the fix that reopened the hole** (`d3faafb`). `#278`'s round-3 change replaced
  `.get("files") or {}` with an isinstance check and dropped the `None` handling; `None` is
  the sentinel for "no `--from-kit`", so verification silently switched off. Found by
  cs-toolkit's reviewer one commit after `#278` merged.
- **cs-toolkit upgraded** to the fixed kit, which was the first real use of `--record-install`
  and is where `#283` was found.

**Learned**

- **The design premise was wrong, and only measuring the adopter showed it.** `#51`'s comment
  said the local column "is already computed today". It is computed; the baseline it computes
  against was never written by any install path, so it had drifted nineteen days from the
  files beside it. Shipping the field alone would have relocated the false accusation rather
  than removing it.
- **Carry-forward can subtract attention — but it is not the whole story here.** No total is
  given, because every total I gave this was wrong and the enumeration is what holds. From the
  archived launch briefs: the bug entered in the fix for **round 3** (`accf8fa`), which round 4
  then reviewed; **round 4's brief aimed at those guards** ("whether each actually guards what
  it claims") and missed it;
  **rounds 5 and 6 named "the three isinstance degrade sites" as already covered**; **round 7
  reviewed a prose-only delta under a blanket "everything else is already covered"**. So a
  wrong coverage claim removed most of the chances and something else removed the one that was
  aimed. Recorded on `#211`, which the `#209` decision below recommends: a carry-forward
  asserting coverage should have to name the test or mutation that establishes it.

  **The briefs those figures come from are session scratch, not committed**, so a later reader
  cannot re-derive this from the repo. `#280`'s merged body and commit message state it
  differently again; treat this bullet as the account of record and that one as superseded.
- **Rounds 2 and 4 on `#278` returned disjoint lens sets**; the first convergence came at
  round 5. Direct evidence on the question `#209` turns on — recorded on `#278` itself, not on
  `#209`, which a review lens checked and found bare.
- **The configured bot reviewed a minority of heads while its check went green on all of
  them.** Its check surface carries no signal about whether a review happened — occurrence and
  the per-head table on `#45`.
- **A guard resting on an incidental property is not a guard.** `#278`'s first
  release-manifest check needed a `required_by` edge to fire, which is an accident of the
  current import graph. A lens called it fragile; cs-toolkit's real manifest then turned out
  to have none, so the original guard would have missed the live case.

**Decided this session (operator)**

- **`#209` — no proportionality valve.** None of directions 1–4 adopted, each refuted by a
  counter-example from a different PR; the issue body's recommendation of direction 1 is
  struck so a reader of the body cannot act on it. Next moves are `#211` then `#120`, both
  aimed at the finding *population* rather than the pass size.
- **Kit findings surfaced in an adopter route upstream, not into the adopter's PR.** A local
  edit to a kit-owned file reports `LOCALLY EDITED` on every later upgrade, which is the
  signal the baseline exists to give.

**Filed this session:** `#279`, `#281`, `#282`, `#283`; occurrences on `#45`, `#211`, `#270`.

**Open, and owned by nothing yet**

- **`#243` is still the precondition** for the `triage-friction-log` and
  `post-merge-systemize` conversions — the two that remain of the adapter work.
- **cs-toolkit's friction inbox is over budget with un-graduated dated sections.** Needs
  tracker writes plus operator approval, so it is `triage-friction-log`'s job and not a
  wrap-up's.
- **Carried forward:** `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#283`** — one paragraph in `/upgrade` Step 4 saying a copied release manifest must
be removed before `--record-install`, and that the mode exits 1 on a partial record. It is the
smallest of the four filed today, it is on the path every pre-`#51` adopter takes on their
next upgrade, and the fix is prose in a file that is already `/upgrade`-refreshed. `#281` is
the next-largest and is a real guard defect, but it needs a test over the near-miss keys
rather than a wording change.

______________________________________________________________________

## Earlier session — 2026-08-03 (three conversions, and a defect class that only exists in shipped docs)

**Theme —** `/session-start` was already converted; this session did the rest. `/parallel` and
`/wrap-up` now point at shared workflows, `/wrap-up` on **both** runtimes. The durable result is
not the conversions: it is that every conversion produced a defect where prose was **correct in
the repo that wrote it and false in the repo that reads it** — and that installing kit docs into
a repo with a fresh reviewer is the cheapest oracle found so far for finding them.

- **cs-toolkit `#1830` — install the shared workflows** (`bfcb4104`). Nine docs; `docs/agentic-dev-kit/`
  had held one. Sessions there had no panel doctrine when the bot went down. Its
  `session-start.md` was **content**-stale, not byte-stale as the previous handoff recorded —
  two commits behind, so the repo where the silent tracker truncation was hit was running the
  session-start without the fix for it.
- **kit `#268` — two rules recovered from the `/parallel` fork** (`8e57562`), and **cs-toolkit
  `#1831`** (`2ee66143`) converting it, 200 lines to 64.
- **kit `#272` — the validation step** (`c7eb7ea`), and **cs-toolkit `#1832`** converting
  `/wrap-up` on both runtimes, 197 lines to 62, renaming the Codex slug.
- **kit `#276` and cs-toolkit `#1833`** — the validation step demonstrated its own gap in the
  commit that introduced it, and the repair. See below.
- **Filed:** `#269`, `#270`, `#271`, `#273`, `#274` (the defect class above), plus an occurrence
  and a correction on `#61` and the fourth measurement on `#209`.

**Learned**

- **The defect class.** Five instances: the hook-install claim (true of cs-toolkit's `make`
  target, false of `init.sh`); the advice that followed from it; "no record of it **in this
  repo**", which inverts in an adopter because there *this repo* is the one holding the record;
  a `docs/plan/handoff/` path that never existed; and an archiver substitution that renamed the
  script but not its `--target-lines` flag. Each was written correctly and read wrongly. `#248`
  did not describe this and nothing else did either; filed as `#274`.
- **Installing kit docs into an adopter is a review oracle.** CodeRabbit found 12 findings on
  `#1830` against files it had reviewed long ago upstream — including a hardcoded prefix in a
  file that documents three ways that prefix can differ.
- **The `/wrap-up` fork inverted the pattern.** The other conversions found kit bugs the fork
  was hiding; this fork was running a remedy the kit lacked, and had open as `#119`. Its
  validation step had no upstream equivalent — seven distinctive phrases, zero hits.
- **The panel found a false claim by executing it**, in a paragraph written while citing `#248`
  for that exact failure. Verifying the cheap sub-claims is not verifying the claim.
- **Seeing an untracked file is not a control; staging by name is.** The validation step added
  in `#272` was defeated on its first live use, in the same commit: `git add -A` swept 228 lines
  of an adopter's uncommitted design note into a wrap-up PR, through review and merge. The
  pre-commit check **did** list the file. It was read for intent — "pre-existing, not mine" —
  rather than as a staging hazard, which is why "surface untracked files" would not have helped
  and is the fix that was **not** shipped. `#276` bans wildcard adds in the workflow instead;
  cs-toolkit `#1833` reverted the sweep, content verified byte-identical three ways.
- **The panel's own contract has a write channel it forbids.** Two live incidents: a scratch
  clone whose `origin` pointed at the handed tree took a pushed ref, and a lens deleted this
  repo's installed `pre-push` after inferring from an untracked path that it had created it.
  Both invisible to `git status --short`, which the contract names as its attestation. `#270`.
- **`paths.engines` carries two meanings** and cannot be right in an adopter with divergent
  originals. The obvious fix is foreclosed: relocating kit engines puts them under a formatter
  that rewrites them. Attempted and reverted. `#269`.
- **The kit tells adopters to bind doctrine through `.claude/rules/`**, listed first among three
  "equivalent" options, and that one binds a single runtime. cs-toolkit has 427 lines behind it,
  including its 66-line safety doctrine, reaching one of its two runtimes. `#273`.

**Decided this session (operator)**

- **Kit-owned docs are exempt from an adopter's formatters.** cs-toolkit's hook would have
  rewritten 8 of 9 installed docs, making every one read as a local edit permanently, with no
  adopter-side way to re-stamp the baseline. The exemption was verified in both directions and
  has since held twice while the same commits reformatted adapter files beside them.
- **`#209` is a decision to take, not a build to schedule** — and after the conversions, which
  is what happened. The build edits the doctrine it reforms, which `#213` measured at five
  rounds.
- **Two kit PRs merged on operator sign-off without a third panel**, both after their bot went
  rate-limited mid-PR. Recorded on each PR rather than left to be inferred from a missing
  receipt.

**Open, and owned by nothing yet**

- **cs-toolkit's own wrap-up is in flight**, run through the newly converted `/wrap-up` so the
  conversion gets an end-to-end exercise rather than only a review. Two things it cannot do:
  its friction inbox is over budget with four un-graduated dated sections, and graduating them
  needs tracker writes plus operator approval (`triage-friction-log`, a separate pass); and its
  `chore/update-plan-<date>` convention already collided with an earlier PR the same day, which
  is `#256` reproduced a third time.
- **Carried forward:** `#243` (still the precondition for the `triage-friction-log` and
  `post-merge-systemize` conversions — those two are what remain of the adapter work), `#209`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`,
  `#124`, `#169`, `#143`, `#93` (its content-recovery half is now discharged; its compatibility
  half was retired by operator decision).

▶ Next: **take the `#209` decision.** It is the operator's, it is cheap, and its input will not
get better — four measurements now, and this session added the one that bears on the direction
the issue currently recommends. Direction 1 would have reduced round 2 of `#268` to a single
lens, and that round's two lenses returned **disjoint** finding sets, so whichever ran alone
would have missed the other's entire set including the MEDIUM. Read the two comments on `#209`
before proposing anything: `#120`, `#211` and `#209` share one evidence body and the issue says
to weigh them together, which now covers five asks. Start from "none of directions 1–4 is
ready" rather than from picking one.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

