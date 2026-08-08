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

Last updated: 2026-08-08 — **the pre-Phase-3 work cs-toolkit's Phase 0 surfaced is nearly
done: `#360` and `#359` are closed, `#358` is what remains.** Every gate
`docs/kit-convergence-plan.md` named for Phase 3 had already cleared (Phase 0 `2ab63d255`,
the fixer predicate `bfafe13b7`, kit `#285` / `#286` / `#297`); the ordering that mattered
was the work the Phase 0 run itself found, because Phase 3 *is* the upgrade and `init.sh`
is what performs it. `#304` was dropped from that order on evidence — it needs a line-1
kit-own marker to act on and cs-toolkit's entry points carry none, so it blocks nothing
there.

## Latest session — 2026-08-08 (the adopter's memo, checked rather than executed)

**Theme —** cs-toolkit's Phase 0 handed the kit a memo of findings. Two of its
load-bearing claims did not survive being re-derived, and the work that followed was
smaller and better aimed than the memo proposed.

- **PR `#361` merged.** Three facts in `docs/kit-convergence-plan.md` and this file that a
  reader would have acted on: Phase 3 no longer waits on cs-toolkit; "the only divergence
  currently invisible to tooling" was false, `init.sh` being the counterexample; and
  `adopt`/`upgrade` already have shared definitions with bindings on both runtimes since
  `#330`. The adopter memo is committed beside the plan as
  `docs/adopter-forcing-function-memo_2026-08-07.md`, preserved as the adopter's account
  with its superseded recommendation marked rather than rewritten.
- **PR `#362` merged — `#360` closed.** `init.sh` is tracked in `KIT_OWNED` and the
  manifest, so the file that performs every install is inside the measurement. Verified
  with `make test` in `/Users/topi/Coding/agentic-dev-kit`, and end-to-end by running the
  new doctor with `--root` against `/Users/topi/Coding/in-parallel/cs-toolkit`.
- **PR `#366` merged — `#359` closed.** The Codex registration no longer runs `python3`
  against a path built from an empty string. Both surfaces changed together because
  `test_the_advisory_matches_the_registrations_it_describes` requires it.
- **Filed this session: `#363`, `#364`, `#365`, `#367`, `#368`.** Occurrence comment on
  `#350`; the measurement that refutes `#358`'s proposed remedy is a comment on `#358`.

**Learned**

- **The memo's two false claims failed in opposite directions, and both came from reading
  a document instead of the tree.** It reported the kit has no coverage of the hook
  registrations — it has two real tests, and the true gap is that they compare *text*,
  which is *why* `#359` shipped: when the command string itself is wrong, the advisory and
  the shipped file are wrong identically and every equality holds. And it recommended
  promoting `adopt`/`upgrade` extraction to a hard Phase 3 gate, which `#330` had
  finished — taken from this repo's own stale plan section. **A stale plan does not merely
  misinform; it produces confidently-scoped work that does not need doing.**
- **`#360`'s design question dissolved instead of being decided.** Its three-way choice
  rested on an adopter's `init.sh` being *expected* to diverge. cs-toolkit's copy is
  byte-identical to kit commit `7485512b`, so the delta is version drift with no local
  rendering — which makes a tracked copy report `stale`, not `locally-edited`. No new role,
  no file split.
- **`KIT_OWNED` lives in the engine, not the manifest**, so `--manifest` cannot backport a
  newly tracked path. Found by running the adopter's *own* vendored doctor first and
  getting a different file list than the kit's.
- **Every panel round found the previous round's fix weaker than it claimed** — a regex
  guard defeated by execution, a parametrization that exercised a flag without reaching its
  branch, a positive control that did not discriminate its own path, a stub whose harness
  could break silently, and an assertion that could never fail. The doctrine predicts this
  about fix rounds; it held every round.
- **A mutation harness can report kills that never happened.** Cloning a branch before
  committing the fix meant the revert step restored the *unfixed* file, so two reported
  kills were that state failing again — and they were hiding two genuine coverage gaps.
  `#367`.
- **A stale PR *description* is worse than a stale comment**, because a reviewer reads it
  top-down before the diff. `#366`'s body asserted a rationale the code had already
  retracted.
- **One finding was beyond anything this machine could run:** the `exec` control in a new
  test was shell-dependent, and `/bin/dash` — `/bin/sh` on most Linux runners — tail-call
  optimises where the local shell forks. It would have failed there and passed here.

**Open, and owned by nothing yet**

- **`#358` is the remaining pre-Phase-3 item** — two prose paths plus a coverage question
  whose proposed remedy is refuted on the ticket, with the viable narrower form identified.
- **The friction inbox still awaits `triage-friction-log`**; nothing was added to it this
  session, because everything issue-shaped was filed to the tracker instead.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#368`, `#367`, `#365`, `#364`, `#363`, `#358`, `#356`, `#350`,
  `#346`, `#304`, `#291`, `#290`, `#287`, `#283`, `#273`, `#243`, `#248`, `#264`, `#236`,
  `#231`, `#213`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`,
  `#169`, `#143`, `#46`, `#36`.

▶ Next: **`#358`, then Phase 3 in cs-toolkit.** `#358` is two lines in
`fallback-review-panel.md` plus the doctrine-scoped guard its comment thread already
measures. Then Phase 3, from a session rooted in `/Users/topi/Coding/in-parallel/cs-toolkit`
— read `docs/kit-convergence-plan.md`'s pre-Phase-3 section first. Two things that session
must do beyond the upgrade: install `docs/agentic-dev-kit/workflows/adopt.md` and
`upgrade.md` there (its manifest lists both as declined, so it has no installed workflow
doc to follow), and refresh its vendored `kit_doctor.py` — until that is replaced, its own
doctor cannot see `init.sh` however current the manifest is.

______________________________________________________________________

## Session — 2026-08-07 (`#353`, and a boundary its author could not settle)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

