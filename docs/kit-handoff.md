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

Last updated: 2026-08-06 — **The first parallel batch ran; Phase 1 is half done.** `#285`
shipped in PR `#317`, `#292` in PR `#315`. The kit-side starter `#304` did not ship: its
named repair carries an adopter-side regression, and it now folds into `#297`.

## Latest session — 2026-08-06 (the first parallel batch, and a fix that should not be built)

**Theme —** Three isolated lanes off one cockpit. Two landed. The third produced a finding
instead of a commit, which is the outcome worth recording: the repair `#304` names for
itself would have made an adopter's `AGENTS.md` permanently re-seedable.

- **`#292` shipped in PR `#315`.** `make test` and `mutation-test` now run CI's lint and
  shell-syntax gates before pytest. `#292` stays open — nothing pins that the targets
  actually depend on the new gates, so a symmetric revert still passes; the residual is on
  the issue and in the Makefile.
- **`#285` shipped in PR `#317`.** `kit_doctor`'s Usage block writes `<engine-dir>`, with a
  test pinning the invariant across `KIT_OWNED`.
- **`#304` did not ship, deliberately.** Its "smallest fix" — `seed_doc` re-emitting
  `KIT_OWN_MARKER` — is unconditional, so in the adopter tree `#297`'s body describes it
  leaves the seeded file permanently seedable instead of protected after one overwrite. The
  trace is on `#304`; a pointer is on `#297`. Both safe variants need a kit-repo detector
  that does not exist.
- **Filed this session:** `#316`, `#318` (from the `#285` lane), `#319`, `#320`. Occurrence
  comments on `#305`, `#304`, `#297`.
- **Batch reconciled** with `scripts/reconcile_sessions.sh fix-292-make-test-parity
  fix-285-kit-doctor-paths fix-304-seed-marker`, run in
  `/Users/topi/Coding/agentic-dev-kit`: `launched 3, merged 2, parked 1`. The parked lane is
  `fix-304-seed-marker` (`EMPTY — 0 commits, never started`).

**Learned**

- **A ticket's own proposed repair can carry the defect class the ticket cites.** `#304` was
  written after `#294`, names `#294`'s lessons, and its named repair has `#294`'s shape. What
  caught it was tracing the repair into an adopter tree before writing code — not review, and
  not the ticket's own reasoning.
- **Building the mechanical guard is what finds the bug elsewhere.** The `#285` lane's
  regression test surfaced the same hardcoded-path shape in seven further kit-owned engines,
  filed as `#316`. The prediction being borne out is **`#285`'s own** — its body argues for a
  mechanical fix over a careful edit because "the pattern reproduces itself on contact" — and
  the test established that rather than the argument. (`#316` records the seven; it does not
  contain that phrase, and an earlier draft of this line implied it did.)
- **A contract in the prompt is still prose.** A lane given the `prompt_preamble` verbatim
  idle-stalled against its first two clauses; its sibling, given the identical bytes, did
  not. `#320`, with the direction: the cockpit already owns a check that classifies this.
- **A panel that finds something cannot leave two-lens coverage at head.** Both merged PRs
  carry a single-lens `fallback:delta` receipt, because fixing a finding moves the head off
  the reviewed sha. `#305`, reframed there from a stopping rule to a coverage question.

**Decided this session (operator)**

- **Hybrid lane launch.** `parallel-headless.md` forbids an env-incapable launcher for a
  state-writing lane, and no in-session mechanism here can replace a spawned process's
  environment. So the two standard lanes ran as sub-agents with the sandbox carried by the
  on-disk marker and the refuse-flag reduced to a prompt instruction; the high-stakes lane
  stayed attended, where `activate` sets it mechanically.
- **Fold `#304` into `#297` rather than ship the smaller repair.** The lane produces a
  finding, not a commit.

**Open, and owned by nothing yet**

- **`#297` now carries `#304`'s work** as well as its own, and is Phase 2 of the convergence
  plan's critical path.
- **Phase 1 is half done** — `#285` landed, `#286` remains, and its body leaves three
  questions open that want an operator rather than a spec.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#283`, `#287`, `#286`, `#292`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#286` — the remaining half of Phase 1.** Read its body first: it leaves three
things undecided (what happens when the kit adds a file, whether declaring is opt-in, and
where the declared set lives), so this wants live steering rather than a delegated spec.
`#297` — now carrying `#304` — is the Phase 2 follow-on, and the Codex `SessionStart` budget
hooks plus cs-toolkit's Phase 0 still run in parallel per `docs/kit-convergence-plan.md`.

______________________________________________________________________

## Session — 2026-08-06 (the planning session the convergence doc asked for)

**Theme —** Planning only; no engine, hook or workflow changed. The convergence plan's
questions are settled — 1, 2, 4 and 5 by operator decision, 3 by verification — and its
phase shape is now an agreed sequence. `docs/kit-convergence-plan.md` is the record:
the decisions with their evidence, the sequence with its done-whens, and the
re-verification notes all live there, not here.

- **Question 3 verified: Codex exposes `SessionStart`.** The sources and the remaining
  fire-it-and-see obligation are in the convergence doc's settled-questions list.
- **Re-derived live before deciding**, per the doc's own instruction: `kit_doctor
  --manifest` run in cs-toolkit, the forked hook measured against the kit's current one,
  `#285` / `#286` / `#297` re-read against the plan's claims. The claims held; the
  deltas are recorded in the doc's verified-state section.
- **One dependency the doc had missed is now in the sequence:** cs-toolkit's nightly
  fixer still reads `done`, which gates the engine swap — cs-toolkit's own config phased
  its adoption around exactly this, and the constraint had not reached the kit's plan.

**Open, and owned by nothing yet**

- **`#297` and `#304`** are now placed in the agreed sequence rather than free-floating;
  `#304` is the chosen kit-side starter.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#304`** — its body names the smaller repair (`seed_doc` re-emitting the
kit-own marker). The sequence's other immediate items — the Codex SessionStart budget
hooks (kit-side) and Phase 0, un-forking cs-toolkit's hook (a cs-toolkit session) —
run in parallel with it, per `docs/kit-convergence-plan.md`.

______________________________________________________________________

## Session — 2026-08-05 (the runtime hook, and two predicates deleted)

**Theme —** Both runtimes now fire the PR follow-through hook, and neither registration is
written by the kit. The work that took the time was not the wiring: it was discovering, on
one function, the shape `#297` was filed about, twice over — a predicate about
somebody else's filesystem or config, restated where nothing can execute the restatement.

- **`#301`** — settled in PR `#303`. `pr_followup_hook.py` takes `--runtime`; it had hardcoded
  `review.fallback_commands.claude` and `lens_compute.claude`, which are runtime-keyed with
  different values, so registering it on Codex unchanged would have told that session to run
  Claude's review command at Claude's model. `.codex/hooks.json` added, `.claude/settings.json`
  updated, `init.sh` **prints both registrations whenever the engine is present, and writes neither**.
- **`#302`** — settled in PR `#306`. The trigger matched its phrase anywhere in a command, so
  anything quoting it mandated a non-terminating watch loop for a PR that did not exist.
  `tool_response` is now the discriminator; the command only selects candidates.
- **Filed this session:** `#304`, `#305`, `#310` — written straight to the tracker; and
  `#308`, `#309` — routed out of the wrap-up inbox rather than left parked there.
  A further occurrence on `#270`.

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
  runs** — `#308`, with the draft's evidence. It and `#309` came out of the inbox, because
  each already had a reproduction, a mechanism and a proposed repair. `#310` is the write-up
  of why they were parked at all, and was never an inbox entry itself.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **a planning session on `docs/kit-convergence-plan.md`.** The goal is cs-toolkit
using the kit rather than its own copy, and Codex as a first-class runtime rather than a
partially-wired one. That document records what was verified about both, what blocks, and
five questions it deliberately does not answer — the first two branch the whole plan. Read
it before proposing an order.

Ready to start immediately if that planning lands on it: **`#304` — `./init.sh` in this
repo overwrites its own `AGENTS.md`/`CLAUDE.md`**,
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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

