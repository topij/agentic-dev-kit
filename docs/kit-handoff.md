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

Last updated: 2026-09-07 — both Phase 5 blockers are closed out: registration applied on
both runtimes, and the installed suite assessed and recorded on #534. Phase 5 exit is now
the live decision and was not taken.

## Latest session — 2026-09-07 (installed-suite assessment, in Claude Code)

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

## Session — 2026-09-06 (approved FIX-01 application, in Claude Code)

**Theme —** Apply the retained ownership/lens diff to the original adoption fixture.

- The [FIX-01 record](../saved_plans/adopt-fix01-ownership-lenses_2026-09-06.md) retains
  the approved scope, precondition read, applied patch, doctor result and write
  boundary. `AGENTS.md` loses its kit-own marker and keeps its policy body; both lens
  definitions take the installed engine path. The fixture was not committed and no
  initializer ran.
- Before applying, the diff was shown current against the kit — the landed VER-03
  repair changed the panel test, not the renderer — and complete against the fixture:
  patching scratch copies reproduced the installed renderer's output byte-for-byte.
- `python3 <fixture>/scripts/devkit/kit_doctor.py --root <fixture> --manifest
  <comparison-source>/kit-manifest.json`, cwd the fixture, on 2026-09-06 UTC returned
  exit zero, reading `AGENTS.md: in use` and both lens definitions as matching the
  running doctor's expected output. The retained report read an ownership warning and a
  staleness warning per lens.
- The doctor's own remedy for that ownership warning is `run ./init.sh`, which in
  default mode renders the template over a marked-but-edited file; `#338` already names
  deleting line 1 as the operator resolution, and that is what was applied.
- **The fixture continuity baseline is superseded** by approved change. Compare against
  `fixture-inventory-after-fix01.json` in the FIX-01 evidence, not the VER-02/VER-03
  inventory; a mismatch against the older one is not drift.
- Filed on the operator's approval of the exact payload: #692, for the doctor remedy
  above. #338 stays open and covers the initializer side of the same ambiguity.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md) retains
  Phase 5 in progress and Phase 6 not started. Runtime registration, verification
  follow-up, new initialization, adoption completion, fixture PR, Phase 5 exit and
  cs-toolkit replay keep separate exact decisions. TRI-03/TRI-04/TRI-05, #608/#255 and
  the parked initializer proposal remain reserved.

▶ Next: In Claude, `/session-start` — then take one of the two open Phase 5 blockers
and prepare an exact decision for it: the fixture's runtime-registration scope (Codex
project hooks, Claude cockpit settings, or both) with both exact payloads drafted, or a
bounded assessment of the installed suite's initializer, launcher-policy and portability
failures in PR #686's retained terminal log. Read #534's comments and not only its body:
its 2026-09-06 occurrence places layout-assumption failures inside the issue's scope,
including one in a file the body does not name, so a root miscalculation belongs there
as an occurrence rather than as a new issue. One is already identifiable —
`test_lane_launcher.py:2234` takes `root = ENGINE_DIR.parent` where `conftest.py:48`
already offers `REPO_ROOT = find_repo_root(ENGINE_DIR)`, which is the defect VER-03
repaired in `test_panel_prompt.py` and the same trace the fixture log shows. Recheck
continuity against
`saved_plans/adopt-fix01-evidence_2026-09-06/fixture-inventory-after-fix01.json` — the
VER-02/VER-03 inventory is superseded and a mismatch against it is not drift. Draft
registration payloads in Claude but do not state whether Codex loaded them: `/hooks` in
a Codex session is the only authority on that, so park that confirmation and anything
resting on live Codex behaviour for one batched Codex session. Do not repeat credited
probes or exercises, or advance initialization, adoption completion, fixture PR, Phase 5
exit, cs-toolkit replay or reserved tracker dispositions without their own decisions.

______________________________________________________________________

## Session — 2026-09-06 (approved VER-03 repair, in Codex)

**Theme —** Repair the kit comparison's root and pin its behavior after relocation.

- The [VER-03 record](../saved_plans/codex-adopt-ver03-repair_2026-09-06.md) retains
  the approved scope, input continuity, focused regression, landed old-root mutation
  and restoration. The kit test uses its existing root helper; its manifest digest
  was refreshed. Synthetic layouts exercise the real comparison and renderer.
- The focused command in that record ran in `/Users/topi/Coding/agentic-dev-kit`
  at `188cd97198dbee34919369cfa75a9379d9ddc6eb` plus the test/manifest edits on
  2026-09-06 UTC and passed. The old-root mutation in the recorded disposable cwd
  failed in the nested-layout case; definition mutations reached the equality
  assertion. These are synthetic-layout results, not original-fixture completion.
- `python3 /private/tmp/adk-ver03-7m5h8wtr/check_continuity.py` in the kit checkout
  at `12a67be290989165e0e7f714942c3d59e38696fc` on 2026-09-06 UTC matched the
  original source/fixture inventories, Git state and legacy hashes after the trial.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md)
  retains Phase 5 in progress and Phase 6 not started. Ownership/lenses, runtime
  registration, verification follow-up, new initialization, adoption completion,
  fixture PR, Phase 5 exit and cs-toolkit replay keep separate exact decisions.
  TRI-03/TRI-04/TRI-05, #608/#255 and the parked initializer proposal remain reserved.

▶ Next: In Claude, `/session-start` — follow `docs/kit-handoff.md` and read
`saved_plans/codex-adopt-ver03-repair_2026-09-06.md`. Review the retained VER-03
result and the continuation review's ownership/lens diff, then prepare an exact
fixture decision. Keep registration and verification follow-up separately scoped;
recheck continuity before approved execution. Do not repeat credited probes or
exercises, or advance initialization, adoption completion, fixture PR, Phase 5 exit,
cs-toolkit replay or reserved tracker dispositions without their own decisions.

______________________________________________________________________

## Session — 2026-09-06 (approved VER-02 trial, in Codex)

**Theme —** Execute the approved disposable-copy diagnostic and preserve its limits.

- The [VER-02 record](../saved_plans/codex-adopt-ver02-trial_2026-09-06.md) retains
  exact commands, revisions, terminal results, input/destination inventories,
  setup refusals, mutation and restoration. Its verification stamps bind the
  source-control pass, fixture adversarial-lens mismatch and assertion rejection.
- `python3 /private/tmp/adk-adopt-ver02-ja4w9bd0/resume_trial.py` ran in
  `/Users/topi/Coding/agentic-dev-kit`
  at `cd39158df81457feafa4bd281d928f8fec7d9faf` on 2026-09-06 UTC and matched the
  original source/fixture inventories, Git state and retained snapshot. The trial
  changed only disposable copies; its approval is consumed.
- VER-03 proposes the permanent test-root repair and layout regression for a fresh
  operator decision. The fixture test stopped at the adversarial lens; it did not
  establish a correctness-lens pass or successful adoption verification.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md)
  retains Phase 5 in progress and Phase 6 not started. Initialization, fixture
  ownership/lenses/registration, verification follow-up, adoption completion,
  fixture PR, Phase 5 exit and cs-toolkit replay remain separately scoped.
- TRI-03/TRI-04/TRI-05, #608/#255 and the parked initializer issue proposal remain
  reserved. No tracker graduation was performed. The trial record contains the
  requested Claude-ready starter for reviewing Codex's evidence next.

▶ Next: In Claude, `/session-start` — follow `docs/kit-handoff.md` and read
`saved_plans/codex-adopt-ver02-trial_2026-09-06.md`. Review the retained outcomes
without repeating credited probes; present VER-03 for a fresh exact decision.
Recheck continuity before separately approved execution and preserve all fixture,
initialization, verification, completion, PR, exit, replay and tracker decisions.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

