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

Last updated: 2026-08-08 — **cs-toolkit's Phase 0 landed, and the work it found is now
the thing in front of Phase 3.** Every gate `docs/kit-convergence-plan.md` named for
Phase 3 has cleared (Phase 0 `2ab63d255`, the fixer predicate `bfafe13b7`, kit `#285` /
`#286` / `#297` closed). Phase 3 is unblocked on paper and should still not start first:
the Phase 0 run surfaced `#360`, and Phase 3 *is* the upgrade while `init.sh` is what
performs it. Order is `#360`+`#304` → `#359` → `#358` → Phase 3.

## Latest session — 2026-08-07 (`#353`, and a boundary its author could not settle)

**Theme —** A two-paragraph doc correction whose own review ran four rounds, found two
defects the branch had introduced, and ended on a classification the author was
disqualified from deciding.

- **PR `#353` merged (`63dd892`).** `docs/kit-convergence-plan.md` corrected on two
  facts a cs-toolkit session would have acted on: that repo registers the hook
  `$CLAUDE_PROJECT_DIR`-relative, not by absolute path as the plan said, and the hook's
  import closure is one module already vendored there byte-identical, so Phase 0 carries
  one file rather than a file plus dependencies. Verified with `make test` in
  `/Users/topi/Coding/agentic-dev-kit`, re-run at each committed head.
- **Its review found two regressions this branch introduced, and fixed both.** Round 1
  (full panel): the corrected measurement left the Agreed-sequence bullet contradicting
  it. Round 2 (full panel): the `Verified state` header's date range no longer covered a
  paragraph the branch had inserted under it.
- **A lens disputed the author's safety-critical draw; the operator upheld it.** Round 3
  was a single-lens record-prose delta pass, which confirmed the prose class and disputed
  the boundary. The operator's resolution is on the PR — required to be theirs, not a
  relayed account. Round 4 ran the dual form's second lens; both lenses confirmed both
  draws. Receipt `fallback:delta`, both lenses, bound to `2475dbd` — the head that
  merged, which the squash then rewrote.
- **CodeRabbit was rate-limited on both surfaces throughout and its coverage stayed
  empty**, so the panel carried this review end to end.
- **Filed this session: `#356`.** Occurrence comments on `#346` and `#120`.
- **`#352`, `#354` and `#355` landed on `main` during this session from elsewhere** —
  not this session's work; recorded so the trail has it.

**Learned**

- **The dual form leaks its own independence, through artifacts the doctrine mandates.**
  The second delta lens read the first's verdicts by running `gh pr view` to check
  whether the operator resolution artifact existed — an artifact the doctrine requires,
  on the surface the doctrine requires the verdicts to be posted to. It disclosed this
  unprompted, and nothing else would have caught it: the exposure leaves no trace in git,
  the receipt, or `pr_watch` state. So that receipt's draw-2 disjointness is self-attested
  rather than structural, which is said on the PR. `#356`.
- **One passage, four consecutive fix rounds, each introducing a fresh defect into the
  text it was repairing** — `45d7b05` → `a7ec719` → `9fed796` → `e623196`. The first two
  are pre-squash commits from the branch that landed as `274eed9`: real, reachable in the
  object DB, not ancestors of `main`. `#305`'s argument with better evidence than `#305`
  carries.
- **A planning document reached the safety-critical class by argument, never by
  binding.** The path list names four engines; it names neither this document nor the
  hook whose relocation the document instructs — and that hook cites the doctrine in its
  own docstring. `#346`.

**Open, and owned by nothing yet**

- **The critical path is unchanged and still leaves this repo**: Phase 3 needs
  cs-toolkit's Phase 0 and its fixer predicate. Both re-verified live this session — the
  fork is still 66 lines at `scripts/hooks/`, `.codex/hooks.json` is still absent, and
  that repo's `pr-watch.md` still reads `done`.
- **The friction inbox is over budget and its triage is overdue**; this session added a
  fourth consecutive occurrence to its bot-quota entry, which is the decision the sweep
  is waiting on.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#356`, `#350`, `#346`, `#304`, `#291`, `#243`, `#273`, `#290`,
  `#283`, `#287`, `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`,
  `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: ~~**cs-toolkit's Phase 0**~~ — **done 2026-08-07**, merged there as `2ab63d255`.
The block above is left as written: it is an accurate record of what was true that day,
and its "still leaves this repo" reading was correct until Phase 0 merged that evening.
The live next step is in the 2026-08-08 trail at the top of this file — the three kit
items Phase 0 surfaced (`#360`+`#304`, `#359`, `#358`), then Phase 3.

______________________________________________________________________

## Session — 2026-08-07 (`#305`, and a vice removed at the pricing side)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

