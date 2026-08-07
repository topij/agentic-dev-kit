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

Last updated: 2026-08-07 — **the kit-side critical path is clear.** `#337`, `#334` and
`#349` are merged; Phase 3 of `docs/kit-convergence-plan.md` now waits on cs-toolkit's
Phase 0 and its fixer predicate, both that repo's PRs.

## Latest session — 2026-08-07 (`#305`, and a vice removed at the pricing side)

**Theme —** The review sprint resumed where `#209`'s decision left it. The panel's
stopping rule was the picked hard item; the operator steered the design live and chose
its shape; the change merged the same session.

- **PR `#349` merged (`0e343c9`).** A record-prose-only fix-round delta on a change under
  `safety-critical-changes.md` now takes **both** configured lenses over the delta — the
  dual form — instead of a full panel at the new head, with rule 2 kept by composition
  and a stated precondition: a full-panel review must be standing, so a Degraded-mode
  initial review leaves nothing to compose with. The loop's three terminal states are
  named, and a deletion's prose class is set by what the deleted text was doing where it
  stood. The evidence companion buries the old categorical rule with the `#328` pricing,
  the rejected severity-floor alternative, and the deferred dual-everywhere question.
  Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`: 1006 passed, at both
  heads.
- **`#337` and `#334` merged before this session opened** (`fddbd31`, `b28df6b`), with no
  session block of their own; recorded here so the trail has it. On `#349` the scoped
  trigger produced one PR run and one `main` run, both green.
- **CodeRabbit reviewed both heads of `#349`** and went rate-limited only after coverage
  stood, so no panel was owed. Every finding is disposed on the PR's threads; the one not
  fixed is deferred to `#194` with the bot's agreement. Another data point for the
  friction inbox's bot-quota decision, still waiting on `triage-friction-log`.
- **Filed this session: `#350`.** Comments on `#305` (the disposition) and `#194` (the
  dual form sharpens its receipt-field ask).

**Learned**

- **The bot found the design's own missing precondition.** The dual form's composition
  argument silently assumed a full-panel initial review; the author had reviewed the
  argument and missed it. Principle #5 earning its keep on the doctrine that implements
  it.
- **Fix the price, not the duty.** The durable resolution of `#305`'s vice left
  never-log-regressions untouched and moved what acting on it costs. The rejected
  alternative — a severity floor on the duty — is in the companion so it is not
  re-proposed.
- **`mergeable` has no honest receipt for a bot-reviewed head** — all three literals
  describe fallback passes, so the loop's best case (bot quota present, full coverage)
  wedges the autonomous merge path. `#350`.

**Decided this session (operator, live)**

- **The dual-lens form**, over a severity floor and over record-only; **the ordinary
  class stays single-lens**, with `#268`'s disjointness evidence recorded on `#305` as
  the open question.
- **Merge `#349`** — operator-merge per the doctrine's own closing rule applied to
  itself.

**Open, and owned by nothing yet**

- **The critical path leaves this repo**: Phase 3 needs cs-toolkit's Phase 0 and its
  fixer predicate (`done` → `converged`), both that repo's PRs, per
  `docs/kit-convergence-plan.md`. Every kit-side gate is merged.
- **The friction inbox is over budget and its triage is overdue** by its own entries;
  graduating it needs tracker writes and operator approval (`triage-friction-log`).
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#350`, `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **cs-toolkit's Phase 0 + fixer predicate** — that repo's PRs, per
`docs/kit-convergence-plan.md`'s agreed sequence; read its "The move is not a file move"
paragraph before starting. Kit-side in parallel: `#211` (populate `--carry-forward` for
fix rounds — the review sprint's named next move), and the overdue `triage-friction-log`
sweep.

______________________________________________________________________

## Session — 2026-08-06 (`#330`, and a ticket's own objection that did not survive being run)

**Theme —** The fix was one flag. The work was establishing that the flag was the right one,
against a ticket that argued it was not — and then discovering that moving a file with no
content change still regresses it.

- **PR `#337` is open, reviewed, and deliberately unmerged.** `/upgrade` Step 2 now runs
  `./init.sh --no-clobber`, so a marked-but-edited file is declined instead of rendered over
  with no backup. Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`, on that
  PR's branch — the figure is not restated here, and the branch has to be named because this
  record sits on a different one where the same command in the same directory prints a
  different number.
- **`adopt` and `upgrade` are now shared workflow definitions**, with thin bindings per runtime
  and `KIT_OWNED` entries; Codex gains `$adopt` and `$upgrade`, which it had not had. The move
  was required — `#330`'s fix lands in `upgrade.md` and would otherwise have reached one
  runtime — but the reason worth keeping is separate: `upgrade.md` Step 4 tells an adopter to
  keep their own copy of a runtime *adapter*, so while these two were adapters, no kit fix to
  the adopt or upgrade procedure could reach anyone running it.
- **Filed this session:** `#338`, `#339`, `#340`, `#341`, `#342`, `#343`. Occurrence comments
  on `#326` and `#323`, and a correction on `#330` recording that its objection to the chosen
  option was measurably wrong.

**Learned**

- **A ticket's stated regression can be an artefact of conflating two states.** `#330` argued
  `--no-clobber` would stop a partially-adopted repo receiving `AGENTS.md`. Two `git init`
  sandboxes showed the flag narrows seeding to *absent* targets, and absent is exactly that
  case — it still seeds. The real cost is one row narrower and is announced twice per run.
  The three-option choice the ticket declined to make was decided by running it, not by
  re-reading it.
- **A byte-identical move still regresses.** `adopt.md`'s link to
  `adopting-into-a-linted-repo.md` was correct from `.claude/commands/` and dangling from
  `docs/agentic-dev-kit/workflows/`. Round 1 of the panel verified the move by diffing
  extracted bodies and could not have caught it: correctness depended on the file's depth, and
  the bytes are identical in both places. `#340` is the missing check; `#216` is why one was
  built and reverted before.
- **A hardcoded list in a test narrows coverage without failing.**
  `test_codex_skill_adapters_are_valid_and_share_workflows` iterates a tuple that was the
  complete set until this PR added two skills to it. An unnamed skill is unchecked, not red.
  `#341`. A lens then mutation-tested it in both directions to show the gap was real.
- **The bot's own findings were mostly older than the PR.** Four of its six were pre-existing
  in a file that had simply never been read by a reviewer — as a `.claude/commands/` adapter it
  sat outside every check the repo runs *and* outside what `/upgrade` refreshes. `#342`, `#343`.
  A single bot pass over a long document is a lower bound, not an audit.

**Decided this session (operator-absent, by doctrine)**

- **Option 1 of `#330`'s three**, with the pristine-skeleton cost stated in the workflow rather
  than buried, and option 3 filed as `#338` with the versioning problem that stops it being a
  byte-compare.
- **File rather than fix**, for every finding verified pre-existing. `safety-critical-changes.md`
  rule 3 is explicit that a fix round addresses what the review found, and this PR gates a
  destructive operation.
- **Do not self-merge.** That same doctrine's closing line makes changes it governs
  operator-merge, "even when green and clean". This is why `#337` is held; the outage is a
  second, independent reason.

**Open, and owned by nothing yet**

- **`#337` and `#334` both need an operator merge and neither has CI.** Both branches have zero
  workflow runs. **They are not queued — the push events were dropped**, so Actions recovering
  will not create them: the incident open since 15:22Z later throttled webhooks to a fraction of
  deliveries, and runs on other branches completed well into that window, which is what makes
  "still queued" the wrong read. `#345` has the measurement and the recovery route, and the
  route matters: a new commit would re-trigger CI and **invalidate the review receipt bound to
  the reviewed sha**, while closing and reopening the PR re-fires `pull_request` without moving
  the head. The panel substituted for what CI would confirm — each lens ran the suite in its own
  isolated clone — which is evidence, not a green tick.
- **The friction inbox is over its budget** and this session widened it. Not swept here;
  graduating it needs tracker writes and operator approval, which is `triage-friction-log`'s job.
- **`#342` is the largest of the new ones**: three Major correctness gaps in `adopt.md`, now
  reachable and refreshable for the first time.
- **Carried forward:** `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`, `#292`, `#248`,
  `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`,
  `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **merge `#337`, then `#334`, once Actions is back** — both are operator calls, `#337`
by the safety doctrine rather than only by the outage. Read `#337`'s round-3 comment first: it
records what the panel substituted for CI and what the receipt does *not* cover. After that the
substance is unchanged from last session — **cs-toolkit's Phase 0 and its fixer predicate**
gate Phase 3, and are that repo's PRs.

______________________________________________________________________

## Session — 2026-08-06 (`#297`, and a diagnosis corrected within the hour)

**Theme —** Phase 2 shipped after a two-lens panel. The rest of the session went to a CI
failure that looked like this repo's and was not — the correction is the part worth reading.

- **`#297` shipped in PR `#328`** (merged `dc38c48`). `_seedable` returns a tri-state, so
  `seed_doc` can tell ABSENT from MARKED and the mode is read at that **one call site** —
  never inside the predicate, which is the fork `#297` exists to prevent. An unknown
  argument now exits 2 rather than being skipped past. `/adopt` Step 3c hands the operator
  `./init.sh --no-clobber` instead of asking them to inspect six line-1s. Verified with
  `make test` in `/Users/topi/Coding/agentic-dev-kit`: 952 passed.
- **`#329` is in PR `#334`, open and deliberately unmerged.** CI's `push:` trigger is scoped
  to the protected branch; `scripts/tests/test_ci_workflow.py` pins that literal against
  `vcs.protected_branch`, which is the only thing that can — a workflow cannot read the
  config and GitHub forbids expressions in `on:`. Verified with `make test` in the same
  checkout: 955 passed. **Held** because it cannot be validated while Actions is down: its
  own evidence is "one run, not two", and it currently produces zero, which is
  indistinguishable from having broken PR CI entirely.
- **Filed this session:** `#329`, `#330`, `#331`, `#332`, `#333`, `#335`. Occurrence
  comments on `#243` and `#305`.

**Learned**

- **Ask whether the provider is up before diagnosing the repo.** `#329` was filed
  attributing 15-minute job starvation to this repo's duplicate CI runs; githubstatus.com
  read `Actions: major_outage`, against an incident opened 15:22Z that predates every
  starved run. What disproved the local claim was a run
  with **no sibling to compete with** — PR `#328`'s merge to `main` produced zero check runs
  under the old unscoped trigger. Corrected on the issue rather than by editing it, and the
  workflow gap that permitted it is `#335`.
- **Re-running during an outage is what created the second defect.** The re-run made a check
  row vanish from the rollup instead of turning green, wedging `pr_watch`'s monotone
  false-settle guard permanently (`#333`, measured over eight polls at an unchanged head).
- **A test that names a property can cover half of it.** The byte-identical `--no-clobber`
  test exercised one of `_seedable`'s two marker arms; mutating the other left it green, and
  the kill came from an unrelated test that happened to use the other literal. Found by
  mutation testing, not by review.
- **The panel reviewed what shipped; the bot reviewed the design.** CodeRabbit went rate
  limited after reviewing `4576f40`, so the fixes for its own three findings were never
  bot-reviewed. `#305`'s shape, hit twice in one PR.

**Decided this session (operator)**

- **Record rather than repair**, again on a comment defect: PR `#328` ships a duplicated
  comment paragraph in `init.sh`. Repairing it moves the head off the sha both lenses
  reviewed, and `safety-critical-changes.md` gives that class no delta-pass exit — so three
  lines of comment would have cost a full panel. Stated on the PR, recorded on `#305`.
- **Run the panel** rather than wait out the bot's rate limit.
- **Hold `#334`** rather than merge a CI-trigger change on a green that cannot be obtained.

**Open, and owned by nothing yet**

- **The critical path leaves this repo.** Phase 3 needs cs-toolkit's Phase 0 and its fixer
  predicate (`done` → `converged`); its `pr_watch.py` still carries `decide_done`, and
  `.codex/hooks.json` is absent there. Both are cs-toolkit PRs.
- **`#330` does not block Phase 3.** Measured this session: all six of cs-toolkit's seedable
  paths classify IN_USE under `init.sh`'s own `_seedable`, spliced from the script rather
  than reimplemented. Re-run that before Phase 3 executes rather than trusting the snapshot.
- **`#331`, `#332`, `#333`, `#335` are all `pr-watch` loop defects** found by using it. They
  tax every future PR, and Phase 3 is the largest one in the plan.
- **Carried forward:** `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`, `#292`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`pr-watch 334` once GitHub Actions recovers** — the check is one `toolkit` run on
that PR rather than two, and a run on `main` after it merges; if zero runs still appear, the
change broke PR CI and `test_pull_request_remains_a_trigger` is the thing to read. That is a
gate, not the substance: the substance is **cs-toolkit's Phase 0 and its fixer predicate**,
which gate Phase 3 and are that repo's PRs, per `docs/kit-convergence-plan.md`.

______________________________________________________________________

## Session — 2026-08-06 (`#286`, and a review that kept finding the same shape)

**Theme —** One inline lane, steered live because `#286`'s three open questions were
operator decisions. All three were answered before code was written; none changed under
review.

- **`#286` shipped in PR `#322`.** `--record-install` records `not_installed`, so an
  absence resolves to `declined` / `removed` / `new-upstream` instead of one permanent
  count. Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`: 943 passed.
- **Phase 1's done-when is still open.** It asks that `kit_doctor` distinguish sized down
  from broken *in cs-toolkit*, which needs a `--record-install` run there — adopter-side,
  so it belongs to Phase 3 rather than to this PR. `#286` is closed; the phase is not.
- **Operator decisions:** the declared set lives in the baseline (derived, not
  hand-declared); a file the kit adds later gets its own state rather than defaulting
  either way; declaring is opt-in via the key's presence, so an older baseline keeps its
  existing report.
- **Filed this session:** `#323`, `#324`, `#325`, `#326`.

**Learned**

- **A verdict line is a claim, and it drifted three times from the same blind spot.** Three
  separate review rounds found a headline reading as an all-clear over something actionable
  below it — for `removed`, then `unknown-version`, then `differs`. Each fix addressed the
  case in hand and missed its sibling one line away. What ended it was routing all four
  branches through one shared caveat rather than a fourth careful edit.
- **The panel found what my own mutation testing could not.** Several findings were gaps in
  the tests I had just written: I mutated the branches I was thinking about, and those were
  the ones already covered. A lens picks its own targets, which is the property being paid
  for.
- **`#324` is the limit of what this axis can assert.** A path in neither map cannot be
  told from a damaged record, because the baseline is the trust root and carries no
  integrity check. PR `#322` hedges the wording and does not claim more.

**Decided this session (operator)**

- **Run the panel to convergence rather than to a round count.** Severity rose at round 3
  (a HIGH after two Medium-only rounds), and the stopping rule is blast radius, not rounds.
  Round 4 converged and the receipt was recorded then.

**Open, and owned by nothing yet**

- **`#297` is now the whole of the critical path's next step** — Phase 2, carrying `#304`.
- **`#325` and `#326` are about the panel itself**, and the panel is now the review path
  whenever the bot is limited, so they cost every PR rather than only this one.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#283`, `#287`, `#292`, `#248`,
  `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`,
  `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#297` — Phase 2 of the convergence plan**, and now the critical path's only
open step on the kit side. Its done-when is that something can run `init.sh` in an adopter
without the operator reasoning about which files it will overwrite; `#304` is adjacent and
may share parts of the change. The Codex `SessionStart` budget hooks and cs-toolkit's Phase
0 still run in parallel per `docs/kit-convergence-plan.md`.

______________________________________________________________________

## Session — 2026-08-06 (the first parallel batch, and a fix that should not be built)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

