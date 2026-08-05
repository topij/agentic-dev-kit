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

Last updated: 2026-08-05 — **A predicate you cannot decide is deleted, not guarded.**
Twice more this session, on the same function. The shape now has a name and four
instances; `#297` is still the unbuilt half of the last one.

## Latest session — 2026-08-05 (the runtime hook, and two predicates deleted)

**Theme —** Both runtimes now fire the PR follow-through hook, and neither registration is
written by the kit. The work that took the time was not the wiring: it was discovering, on
one function, the shape `#297` was filed about, twice over — a predicate about
somebody else's filesystem or config, restated where nothing can execute the restatement.

- **`#301` — closed** (PR `#303`). `pr_followup_hook.py` takes `--runtime`; it had hardcoded
  `review.fallback_commands.claude` and `lens_compute.claude`, which are runtime-keyed with
  different values, so registering it on Codex unchanged would have told that session to run
  Claude's review command at Claude's model. `.codex/hooks.json` added, `.claude/settings.json`
  updated, `init.sh` **prints both registrations whenever the engine is present, and writes neither**.
- **`#302` — closed** (PR `#306`). The trigger matched its phrase anywhere in a command, so
  anything quoting it mandated a non-terminating watch loop for a PR that did not exist.
  `tool_response` is now the discriminator; the command only selects candidates.
- **Filed this session:** `#304`, `#305`. A further occurrence on `#270`.

**Learned**

- **Delete the predicate; a guard round finds the shape the last guard missed.** `init.sh`
  first *seeded* `.codex/hooks.json`, then merely *read* it to decide whether to print. Each
  was retired only after its guards had been beaten — the seed by a dangling symlink at the
  leaf, where `[ -e ]` is false and `cat >` follows the link out of the directory; the read
  by a substring that cannot distinguish a `PostToolUse` entry from a mention under any other
  event. The same shape, on `/adopt`, is what `#294` and `#297` are about.
- **Verifying the output and guessing the input is the same error wearing a coat.** `#306`
  established `gh`'s stdout/stderr formats from `gh`'s source, exactly as the ticket demanded
  — and then read that evidence out of a `tool_response` whose shape it had guessed. Codex's
  schema types that field as `true`: any value. A review lens found the resulting silent miss.
- **A negated closing keyword in a heading closes the issue listed under it.** `#303`'s squash
  message said `## Filed, not fixed` above a list naming `#302`; GitHub paired them across the
  blank line and list marker, and the same message said in prose that it stays open. Found by
  going to work on `#302` and finding it closed. The contract in `AGENTS.md` already covers
  this ("in any form, even negated") — what failed was the check, which looked for a keyword
  and a reference on one line.
- **The panel's own output is the next round's input.** Rounds repeatedly found defects in the
  tests written to close the previous round's findings. That is what a fix round is, and it is
  why `#305` exists.
- **`panel_prompt.py` rendered every lens prompt this session** — the friction entry proposing
  it is now validated by use rather than by argument, including `--carry-forward` for the
  round-to-round aim that had been hand-written prose.

**Decided this session (operator)**

- **Record rather than repair, below a severity floor.** Applied once where it cost something:
  `#306` ships a doubled word in a comment, because repairing it would move the head off the
  sha both lenses reviewed. Stated in the squash message rather than hidden. `#305` argues the
  general case and is deliberately not self-answered — a stopping rule authored mid-loop by
  the party who wants the loop to end has the worst possible provenance.

**Open, and owned by nothing yet**

- **`#297` is still the unbuilt half of `#105`** — it was this session's inherited starter
  and was displaced, not dropped.
- **The closing-keyword check that works is a scratchpad script, not something this repo
  runs** — `#308`, with the draft's evidence. `#309` and `#310` were routed the same way:
  straight to the tracker rather than parked, because each already had a reproduction, a
  mechanism and a fix. `#310` is why they were parked in the first place.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#304` — `./init.sh` in this repo overwrites its own `AGENTS.md`/`CLAUDE.md`**,
destroying the kit-own marker one-way and reporting it as `seeded`. Read its body: it
reproduces the defect, records that `make test` then fails on this checkout, and notes that
`README.md` documents re-running `init.sh` as the upgrade step. It also names the smaller of
two fixes — `seed_doc` re-emitting the marker — which needs none of the kit-repo detection
`#291` wants. `#297` remains the larger inherited item.

______________________________________________________________________

## Session — 2026-08-04 (the guard that could not live in a document)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

