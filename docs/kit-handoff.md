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

Last updated: 2026-09-07 — `#698`'s doctor correction and `#706`'s push gate merged.
Phase 5 exit remains the live question and retains its own exact decision.

## Latest session — 2026-09-07 (#698 doctor correction and #706 push gate, in Claude Code)

**Theme —** Take the two delegate-shaped items and `#534`'s panel follow-ups, and let the
fallback panel do its work on a gate.

- [PR #708](https://github.com/topij/agentic-dev-kit/pull/708) merged as `ec75075`.
  `kit_doctor` grades `[features].hooks` whenever a Codex registration exists rather than
  only when `.codex/config.toml` does — this repo was itself the affected population. The
  new `unset` state reports at `·` and does not reach the exit code, which was the
  operator's calibration decision: the approved observation recorded a client discovering
  registrations with the switch unset, so failing the run would assert what that probe did
  not establish. An explicit `false` still exits 1.
- [PR #709](https://github.com/topij/agentic-dev-kit/pull/709) merged as `6f2cc24`.
  `scripts/hooks/pre-push` refuses a push whose commit carries a stale
  `kit-manifest.json`. Checked against the real remote from `main` at `6f2cc24` by
  committing an edit to `scripts/kit_doctor.py` without regenerating and attempting the
  push, which was refused naming that file; the probe branch was then deleted. Re-run it
  that way rather than trusting this sentence. An adopter's `--record-install` baseline is
  exempt.
- **Four panel rounds on `#709` produced four HIGH findings, every one the same shape:
  the guard reporting a clean check while not having checked.** Valid-but-non-object JSON
  crashed it into silence; an entry with no `sha256` was dropped silently; the
  adopter-baseline skip warned on every adopter push forever, contradicting the CHANGELOG
  written in the same commit; and a newline in a manifest key desynchronised the
  positional `git cat-file --batch` reader, **laundering a genuinely tampered file past
  the guard with exit 0 and an empty stderr**. The last was found by building the attack,
  not by reading. Round 4 confirmed the repair closes the class rather than the instance.
- [PR #710](https://github.com/topij/agentic-dev-kit/pull/710) carries `#534`'s two
  panel follow-ups from PR #705's disposition — `is_install_baseline`'s untested except
  arm, now pinned, and the `_shipped()` body duplicated across two test modules, now one
  accessor in `conftest.py`. It merged as `dc6a74e`, so `#534` needs no fresh start on
  either — only the typed decline reasons it always kept out of scope.
- The recurring shape is now unmissable and is in `docs/kit-friction-log.md`: across every
  round this session, each finding was in a claim the author made rather than in a
  mechanism. The 2026-08-22 entry parked exactly that pattern for accumulation on two
  docs-only PRs; it has now recurred on code, repeatedly. **Deciding whether it graduates
  to a rule is the clearest open judgement call.**
- **`#561` is worse than its title.** A genuinely unparseable `pre-push` passed `make
  test`: `check-syntax` hands four filenames to one `bash -n` and `pre-push` is last, so
  it is never parsed. `bash -n good.sh bad.sh` exits 0 with a broken second file. The hole
  for that one file is now shut by `#709`; the general fix is still `#561`'s.
- **A `make test` failure reproduces on clean `main` and CI cannot see it.** Recorded with
  its stamps in the friction log; local `uv run` resolves 3.14.7 against CI's pinned 3.12,
  and `#393` names the mechanism family but a different test. Non-deterministic, so the
  interpreter split is a candidate contributor rather than an established cause.
- `#698`, `#706`, `#534`, `#561` and `#393` all stay open.

**Both operator decisions this block asked for were given, and one is done.**

- **Filing: done.** The issue-shaped friction went to the tracker — [`#712`](https://github.com/topij/agentic-dev-kit/issues/712)
  (lens isolation, both occurrences), [`#713`](https://github.com/topij/agentic-dev-kit/issues/713)
  (`panel_prompt.py` resolving its base at assembly time), and occurrence comments on
  `#561` and `#393`. The rest stayed in the log, and each routed entry now records where
  it went, so triage reconciles rather than re-files.
- **Graduation: decided yes, not yet written.** That is the next piece of work.

▶ Next: **In Codex, run the parked hooks batch — it is unblocked and its inputs are
perishable.** It was held for one live run after `#698`'s fix existed; that fix merged as
`ec75075`. `/hooks` is the only authority for what it must clear — hook execution after
trust, the explicitly-disabled case, and other clients' defaults — and static doctor
output is not. Verifying `#698`'s correction in the field is the same run.

**Recheck continuity first** against
`saved_plans/adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json`
(the post-REG-01 baseline; disagreement with FIX-01 is not drift), work in a disposable
copy, and **stop rather than rebuild** if either original temporary tree is missing:

    fixture: /private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture
    source:  /private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source

Both were present on 2026-09-08 and both live under `/private/tmp`, so a reboot ends this
route. That is why it goes first.

Then, in Claude, **write the prose-claims rule.** The 2026-08-22 friction entry parked
*"every finding was in a claim about the work rather than in the work"* pending a
recurrence with a mechanism; the operator approved graduating it.

**Scope it narrowly, and read this before writing:** the broad reading — *"panel findings
land in claims rather than mechanisms"* — is **contradicted by this session's own
evidence.** `#709`'s four HIGH findings were real defects in mechanisms, including a
working bypass of its guard. Do not write that rule. What recurred, and what has a
mechanism, is narrower: **an author editing text adjacent to a fact they are
simultaneously changing does not re-read that text.** Both instances on PR #711 were in
the same paragraph as the edit, and both were introduced by the fix for the previous
finding. Bind prose surfaces; leave code alone. Placement is itself a judgement call —
the rule binds authors rather than lenses, which argues for `AGENTS.md` over the panel
doctrine, but that is not settled here.

Then: `docs/kit-friction-log.md` is past its budget and the operator holds the triage —
run `python3 scripts/check_doc_budget.py` for where it stands, and `triage-friction-log`
is the route. Phase 5 exit is still the live question and still needs its own exact
decision, as do the cs-toolkit replay, new initialization, adoption completion and the
fixture PR.

______________________________________________________________________

## Session — 2026-09-07 (#534 residual repairs, in Claude Code)

**Theme —** Repair what `#534` still carried, and field-verify the item that merged
without ever being checked in an adopter.

- [PR #705](https://github.com/topij/agentic-dev-kit/pull/705) merged as `7cb0868`.
  Item 1 (`_repo_layout` engine-dir resolution) was **not** re-done: it merged in
  PR #545, and `kit-handoff-history.md`'s 2026-08-21 block records the residual — those
  issues stayed open because nothing verified their acceptance criteria in the field.
  That verification is what this session did.
- **The proposed kit-repo-only marker cannot carry cause 1, and the reason generalises.**
  It skips on a *missing path*, and the question these tests need answered is whether the
  file at that path is the kit's copy. `conftest.py` gains the predicate it cannot
  express, derived from `kit_commit` being written only by `--record-install`.
  `test_shipped_manifest_covers_every_kit_owned_file` is restated rather than skipped, so
  an adopter gains coverage where they had a permanent red.
- **`.codex/hooks.json` and `.claude/settings.json` are the sharp case** — the kit prints
  both and writes neither (`#303`), so in an adopter those paths hold hand-written
  registrations and a path check accepts them. Reference copies now ship, engine-relative
  and `KIT_OWNED`, with a drift guard pinning reference to live.
- **Field-verified in disposable copies of the adopter fixture**, the original asserted
  equal to `fixture-inventory-after-reg01.json` before and unchanged after each run.
  Item 1 resolves there; a cause-1 test went from failing to passing, and others from
  failing to skipping. The silent false pass was proven fixed **by mutation, not by a passing run** —
  a pass is what that defect looks like — and that mutation is what caught a read site an
  edit had missed.
- **What the panel found is where the risk sat.** Its rounds are enumerated with their
  heads and fixes in the [disposition](https://github.com/topij/agentic-dev-kit/pull/705#issuecomment-5574151329).
  Every finding was in a claim the author made — a predicate said to be safe, an accessor
  said to decline gracefully, a test said to guard a fix, a docstring describing a step
  its function does not perform — and none was in a mechanism. Rounds whose CI was green
  still carried them.
- **`#534` stays open.** The typed decline reasons are deliberately out of scope; the
  disposition also carries the follow-up candidates the panel raised and this PR did not
  take.
- An occurrence on [`#393`](https://github.com/topij/agentic-dev-kit/issues/393#issuecomment-5573705268)
  records that the interpreter `uv run` resolves locally and the version
  `.github/workflows/test.yml` pins are not the same, so a suite failure reproducible on
  `main` is invisible to CI. That issue stays open.

- **Session friction routed at close-out.** [`#706`](https://github.com/topij/agentic-dev-kit/issues/706)
  files the manifest going stale between `--generate-manifest` and the commit, caught only
  by the full suite. The guard is not broken — it caught every instance — so the finding is
  about when it reports, and the proposed fix moves that to `scripts/hooks/pre-push`.

▶ Next: In Claude, `/session-start` — Phase 5 exit is the live question and now has no
`#534` repair standing in front of it; it still needs its own exact decision. New
initialization, adoption completion, fixture PR and cs-toolkit replay keep theirs.

______________________________________________________________________

## Session — 2026-09-07 (live Codex hooks batch)

**Theme —** Complete the parked Codex observations and preserve their scope.

- The [batch record](../saved_plans/codex-hooks-batch_2026-09-07.md) retains the live
  `/hooks` excerpts, configuration stack, continuity audits and tracker receipts.
  It distinguishes project trust from trust of the current hook definitions and
  discovery from execution.
- The fixture's registration appeared in `/hooks`; the disposable unset case also
  exposed its registrations. See the command/date/revision-bound record for the
  observations and their limits. The original fixture was not used for the unset case.
- The operator approved and posted the reserved `#608`/`#255` dispositions and closed
  those issues as completed. The credited PR #680 probe was not repeated.
- The approved [observation on #698](https://github.com/topij/agentic-dev-kit/issues/698#issuecomment-5569204436)
  scopes the remaining installer/doctor correction. It does not establish hook execution
  after trust or a default shared by every Codex client.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) carries
  those decisions without advancing Phase 5 exit. New initialization, adoption completion,
  fixture PR and cs-toolkit replay retain their own exact decisions. The `#534` repairs
  were outside this Codex batch.

▶ Next: In Claude, `/session-start` — follow `docs/kit-handoff.md`, read
`saved_plans/codex-hooks-batch_2026-09-07.md` and
`saved_plans/adopt-suite-assessment_2026-09-07.md`, and prepare the bounded `#534`
repair work and its exact decisions. Before approved fixture execution, recheck
`fixture-inventory-after-reg01.json`; stop if either original temporary tree is missing.
Do not repeat credited exercises or advance Phase 5 exit, adoption completion, fixture PR,
new initialization or cs-toolkit replay without their own exact decisions.

______________________________________________________________________

## Session — 2026-09-07 (installed-suite assessment, in Claude Code)

**Theme —** Assess PR #686's retained installed-suite log; close the second Phase 5 blocker.

- The [assessment record](../saved_plans/adopt-suite-assessment_2026-09-07.md) retains the
  classification, the re-measurement and the boundary. It changed no fixture, ran no
  initializer, and filed no new ticket. Most of what it found is in `#534`'s stated scope
  and is [recorded there](https://github.com/topij/agentic-dev-kit/issues/534#issuecomment-5565697869),
  with a [correction](https://github.com/topij/agentic-dev-kit/issues/534#issuecomment-5565966166)
  appended; one failure belongs to `#690` instead, already repaired.
- Most of the retained log's failures fit a cause `#534` already names. The largest
  single mechanism is the fixture's deliberately preserved wrap-up adapter, which
  accounts for every `test_portability.py` failure and most of `test_kit_doctor.py`'s —
  established from the tracebacks, after a first pass attributed the portability ones
  from their test names and got the mechanism wrong. `test_lane_launcher.py`'s was already recorded during
  PR #691's panel and was **not** re-filed. **`test_panel_prompt.py`'s is not a `#534`
  item at all:** `585483b` (#690) already repaired that test's root, and the fixture's
  installed copy predates the fix.
- **REG-01 invalidated part of that log.** Sixteen of its failure blocks were
  `FileNotFoundError` on the two registration files that were absent then and exist now,
  so the log is stale as a description of the fixture.
- Re-measured in a disposable copy on 2026-09-07 UTC: the selector picks 18 items,
  11 passing and 7 failing — **and neither outcome is better than the failure it
  replaced.** The passes assert against the *adopter's* registrations and
  report nothing about the kit's, which is `#534`'s silent-false-pass family as a family
  rather than a single instance; they were loudly red until the adopter completed a step the
  installer told them to complete, and completing it is what silenced them. The failures
  cross an expectation built from `init.sh` in a sandbox that takes the default
  `paths.engines: scripts` against a real registration carrying `scripts/devkit`, so the
  text accuses the kit of drift when the cause is the adopter's layout.
- **The first pass overstated two things and PR #701's correctness lens caught both** —
  a completeness claim covering files it had not examined, and a re-measurement that
  reached one file while the sixteenth test lived in another. Both are corrected on the
  record and in an appended `#534` correction; the substantive finding is unchanged.
- That last point is what the occurrence adds to `#534`'s suggested scope: item 1's
  `_repo_layout` fix reaches none of it, because nothing here reads `REPO_ROOT /
  "scripts"`. Whether the answer is a kit-repo-only marker or an installed reference copy
  is a decision that issue now carries.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) retains
  Phase 5 in progress and Phase 6 not started. **Both blockers named in the 2026-09-06
  handoff are now closed out** — registration by approved application, the suite by this
  assessment — but the failures are classified and recorded, not repaired, and Phase 5
  exit is its own exact decision that was not taken.

- **Session friction routed at close-out.** `#702` files the pattern behind two of this
  session's own defects: a failure's cause read off its test name rather than its
  traceback, the second instance landing inside the commit written to fix the first. An
  occurrence on `#510` records the other half — the task wrapper reporting `exit code 0`
  for a run `make` exited `2`, and a memory-killed run whose only tell was an absent pytest
  summary line. `#666` carries the receipt-ordering trap as **two walk-ins** and nothing
  else — the successful application, recording the parent receipt before the fix round, is
  on PR #701's own disposition, in the same PR as the second walk-in.

▶ Next: In Claude, `/session-start` — Phase 5 exit is now the live question and needs its
own exact decision; the repairs `#534` carries are the work standing between here and it.
Recheck continuity against `fixture-inventory-after-reg01.json` before any approved
execution. Keep every Codex-only confirmation — `/hooks` loading, `#698`'s open question,
the reserved `#608`/`#255` dispositions — for one batched Codex session, and keep new
initialization, adoption completion, fixture PR and cs-toolkit replay on their own exact
decisions.

______________________________________________________________________

## Session — 2026-09-07 (REG-01 applied, in Claude Code)

**Theme —** Execute the approved runtime registration on both runtimes.

- The [application record](../saved_plans/adopt-reg01-application_2026-09-07.md) retains
  the approval, precondition read, write boundary, doctor result and the new continuity
  baseline. The operator approved **both runtimes** on 2026-09-07; that execution
  approval is consumed.
- Continuity was rechecked immediately before the write — in
  `/Users/topi/Coding/agentic-dev-kit` at
  `810b2911abb1598b4662a5b96a6bcc5823588751` on 2026-09-07 UTC, exit zero — not earlier
  in the session.
- Paths added are exactly `.codex`, `.codex/hooks.json`, `.codex/config.toml` and
  `.claude/settings.json`. No path was removed and **no existing path changed**; the
  fixture's `HEAD`, branch, absent remote and index are untouched and the additions are
  untracked. No initializer ran and nothing was committed inside the fixture.
- The fixture's own doctor returned exit zero on 2026-09-07 UTC with **no advisory line
  left**: every engine path on both runtimes resolves and both Codex lifecycle forms
  verify. The two `· not present` lines are gone.
- **The disposable-copy trial predicted that report byte-for-byte**, once each run's own
  fixture root is normalised. Verifying in a copy first was accurate here, not merely
  safe.
- **The continuity baseline moved again.** Compare against
  `fixture-inventory-after-reg01.json`; a mismatch against the FIX-01 inventory is not
  drift. The comparison-source baseline is unchanged.
- **Nothing states what either runtime loaded**, and nothing here could — `/hooks` is
  the only authority. Parked for one batched Codex session with #698's open question
  (which this fixture no longer exercises, since it now sets `[features].hooks` to true)
  and the reserved `#608`/`#255` dispositions.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) retains
  Phase 5 in progress and Phase 6 not started. A warning-free doctor is not adoption
  completion. The installed-suite blocker is still untouched, and its
  `test_lane_launcher.py` root-helper defect still belongs to that assessment as a
  `#534` occurrence rather than a filing from outside it.

▶ Next: In Claude, `/session-start` — the remaining Phase 5 blocker is the bounded
assessment of the initializer, launcher-policy and portability failures in PR #686's
retained terminal log, adding occurrences to `#534` rather than re-filing. Recheck
continuity against `fixture-inventory-after-reg01.json` before any approved execution.
Keep every Codex-only confirmation for the batched Codex session, and keep new
initialization, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay on
their own exact decisions.

______________________________________________________________________

## Session — 2026-09-06 (REG-01 registration payloads, in Claude Code)

**Theme —** Take the runtime-registration blocker and prepare its exact decision.

- The [REG-01 record](../saved_plans/adopt-reg01-runtime-registration_2026-09-06.md)
  retains the drafted payloads with their digests, the per-scope doctor reports,
  both sets of negative controls and the write boundary. **Scope is recommended, not decided:**
  both runtimes. The original fixture was not written to, no initializer ran, and
  nothing here states what either runtime loaded.
- Continuity was rechecked first, against the FIX-01 baseline that supersedes the
  VER-02/VER-03 inventory. `uv run python <scratch>/recheck_continuity_fix01.py` in
  `/Users/topi/Coding/agentic-dev-kit` at
  `a4419dcd541f25162971615444aa995bc0dfb474` on 2026-09-06 UTC exited zero. Its one
  status divergence is expected and explained in the record: the lens files were
  already untracked before FIX-01, so only `AGENTS.md` gains a line.
- Each scope was read by the fixture copy's **own** installed doctor, in disposable
  copies. Every scope exits zero including the do-nothing baseline, so the exit code is
  not what separates them — the report body is, and the two runtimes' checks are
  disjoint: only Codex gets a lifecycle verdict, only Claude gets `#606`'s grant check.
- The green lines were falsified before being relied on. A wrong timeout exits 1; the
  kit's own `scripts/` allow entry in this `scripts/devkit` adopter fires `#606`; an
  altered command string silently loses its lifecycle verdict at exit 0.
- Filed on that last control and on a related blind spot: **#698**, where `kit_doctor`
  grades `[features].hooks` only when `.codex/config.toml` exists, so a fully verified
  `hooks.json` reports green with the switch never set. The silent-verdict half went to
  **#392** as an occurrence rather than a new issue, because that issue's option 3 is
  the fix for both axes.
- **Everything resting on live Codex behaviour is parked for one batched Codex
  session:** whether the payloads load and are trusted via `/hooks`, #698's open
  question, and the reserved `#608`/`#255` dispositions.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) retains
  Phase 5 in progress and Phase 6 not started. The second blocker — the installed
  suite's failures in PR #686's log, with its `test_lane_launcher.py` root-helper defect
  belonging there as a `#534` occurrence — is untouched by design. New initialization,
  adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay keep separate
  exact decisions.

▶ Next: In Claude, `/session-start` — then either give REG-01 its exact scope decision
(the record recommends both runtimes; approving it authorizes a real `permissions.allow`
grant in the fixture tree, not only a file a diagnostic reads) and apply the drafted
payloads after a fresh continuity recheck, or take the remaining Phase 5 blocker: the
bounded assessment of the initializer, launcher-policy and portability failures in PR
#686's retained terminal log, adding occurrences to `#534` rather than re-filing. Keep
every Codex-only confirmation for the batched Codex session.

______________________________________________________________________

## Session — 2026-09-06 (friction-log triage, in Claude Code)

**Theme —** Graduate the friction-log inbox on exact operator decisions.

- The operator decided in-session: `approve TRI-01, archive TRI-02 TRI-03, park TRI-04
  TRI-05 TRI-06`, superseding an earlier `approve all`. Filed: #693, the initializer's
  refusal of an indentless `doc_budgets` list that `kitconfig` accepts — the entry the
  2026-09-06 adopt-continuation block left reserved. Archived without filing: the
  2026-09-01 entry and its recurrence. Parked and byte-identical in place: the
  `claude -p` and `panel_prompt.py` entries (2026-08-27) and the eight-panel-rounds
  entry (2026-08-22).
- **Candidate ids shifted.** This run's `TRI-04`/`TRI-05`/`TRI-06` are the 2026-09-03
  run's `TRI-03`/`TRI-04`/`TRI-05`. The 2026-09-06 graduation marker records the mapping
  and how it was established; read it before quoting a reserved id from an older block.
  `#608`/`#255` remain reserved.
- Swept by PR #694, merged on 2026-09-06 as `991ad16e7a2237e5440695c78573592f1b87964e`;
  its graduation marker is the committed approval record.
  Review was the fallback panel — CodeRabbit's auto reviews are disabled, treated as an
  outage rather than a waiver. Its adversarial lens found that the marker overstated
  `#393` as recording both the 2026-09-01 entry and its recurrence when only the
  recurrence is on the tracker; that was fixed before merge, and the disposition of
  every finding is on the pull request.
- **The run had to be unblocked first, and that is now on the tracker.** A terminal
  `completed` record from the 2026-09-03 run occupied the live state path and no row
  authorizes a later run to clear it, so drafting could not start until the operator
  approved removing it. Recorded as an occurrence on
  [#425](https://github.com/topij/agentic-dev-kit/issues/425), whose own direction 1
  predicted the inverse case. Also filed: #695, the `forge-finalize` log having no slot
  for the review-fix round this session actually needed; #696, a graduation marker
  asserting tracker state it never verified.
- **What the sweep could not reach.** The parked entries are a deliberate decision, and
  the graduation markers accumulate in the same file. `triage-friction-log` can reduce
  neither, so another sweep is not the remedy; whether marker blocks belong in this file
  at all is `#224`'s territory and needs a decision. PR #694's review disposition
  carries this session's stamped figures.

▶ Next: In Claude, `/session-start` — the adopt-continuation thread below is unchanged
and still the live work; this session touched only the friction log. Note that #693 now
covers the initializer/`kitconfig` grammar split that the block below left reserved, so
it is a filed ticket rather than an open decision.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

