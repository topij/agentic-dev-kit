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

Last updated: 2026-09-06 — REG-01 drafted and verified the fixture's runtime-registration
payloads and recommends both runtimes; the scope decision itself is open, and the
installed-suite blocker is untouched.

## Latest session — 2026-09-06 (REG-01 registration payloads, in Claude Code)

**Theme —** Take the runtime-registration blocker and prepare its exact decision.

- The [REG-01 record](../saved_plans/adopt-reg01-runtime-registration_2026-09-06.md)
  retains the three drafted payloads with their digests, the per-scope doctor reports,
  three negative controls and the write boundary. **Scope is recommended, not decided:**
  both runtimes. The original fixture was not written to, no initializer ran, and
  nothing here states what either runtime loaded.
- Continuity was rechecked first, against the FIX-01 baseline that supersedes the
  VER-02/VER-03 inventory. `uv run python <scratch>/recheck_continuity_fix01.py` in
  `/Users/topi/Coding/agentic-dev-kit` at
  `a4419dcd541f25162971615444aa995bc0dfb474` on 2026-09-06 UTC exited zero. Its one
  status divergence is expected and explained in the record: the two lens files were
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

## Session — 2026-09-06 (adopt verification reconciliation, in Codex)

**Theme —** Credit the retained diagnostic outcomes and prepare the next bounded
decision without repeating the field exercises.

- The [continuation review](../saved_plans/codex-adopt-completion-review_2026-09-06.md#ver-01-reconciliation--2026-09-06)
  reconciles VER-01 with PR #687's independent source/fixture probes. It separates
  their demonstrated path/ownership failures from missing historical telemetry and
  the unresolved adoption-relevant verification obligation.
- The exact VER-02 proposal trials the panel test's existing repository-root helper
  in disposable copies and checks that the lens-content assertion is reached. The
  proposal remains unexecuted; it does not change the fixture or initialize it again.
- `python3 -` using the retained continuity audit program in
  `/Users/topi/Coding/agentic-dev-kit` at
  `61776212a2694108c5dfd8c2640c8b8ef08a40f4` on 2026-09-06 UTC completed its
  assertions against PR #687's fixture snapshot and the retained source/config/
  baseline evidence. The [result](../saved_plans/codex-adopt-verification-reconciliation-evidence_2026-09-06/continuity.json)
  records the read's boundaries; continuity must be rechecked before execution.
- Kit `make test` evidence and its verification limits are retained in the
  continuation review; subsequent checks and independent review belong to this
  wrap-up PR at its reviewed head.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md)
  retains Phase 5 in progress and Phase 6 not started. Ownership, registration,
  lens definitions, verification, adoption completion, fixture PR, Phase 5 exit
  and cs-toolkit replay retain separate exact decisions.
- TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the parked initializer issue
  proposal remain reserved. No tracker or friction-graduation action was taken.

▶ Next: `$session-start` — follow the maintained Phase 5 reconciliation and decide
VER-02 in `saved_plans/codex-adopt-completion-review_2026-09-06.md`. Before any approved
trial, recheck the bound source and original-fixture continuity. Preserve the separate
fixture, initialization, adoption-completion, PR, exit, replay and tracker decisions.

______________________________________________________________________

## Session — 2026-09-06 (adopt continuation review, in Codex)

**Theme —** Review PR #686's remaining fixture decisions and select a bounded
diagnostic without repeating credited exercises.

- The [review and VER-01 proposal](../saved_plans/codex-adopt-completion-review_2026-09-06.md)
  retain the stamped read-only inspection, original failure-log pointer and proposed
  ownership/lens diff. The original fixture was not changed or initialized again.
- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `e3c7b14ffb26e7ffac37e0be62ac02618d819c58` plus the review/plan/handoff edits
  on 2026-09-06 UTC failed in the recurring deep-payload hook assertion. The
  review record retains its terminal output and verification boundary.
- Independent review supplied the named source/fixture comparison and caught a
  lossy derived failure inventory, which was removed. Reconcile those retained
  probes with VER-01 before authorizing further verification; do not repeat them
  merely because the proposal remains unapproved. The installed suite is not disposed.
- Phase 5 remains in progress and Phase 6 not started in the maintained
  [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md). Preserve exact
  decisions for initialization, fixture ownership/registration/lenses, verification,
  adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay.
- TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the parked initializer issue
  proposal remain reserved. The review added no tracker occurrence or graduation.

▶ Next: `$session-start` — follow the maintained Phase 5 reconciliation and the
VER-01 proposal in `saved_plans/codex-adopt-completion-review_2026-09-06.md`.
Review the retained independent probes before an exact follow-up decision; preserve the separate fixture,
adoption-completion, replay and tracker decisions.

______________________________________________________________________

## Session — 2026-09-06 (adopt initialization and sprint audit, in Codex)

**Theme —** Continue the staged fixture at Step 3c on the exact operator approval,
then reconcile the active sprint without promoting adoption or Phase 5 completion.

- The [continuation record](../saved_plans/codex-adopt-initialization-field-exercise_2026-09-06.md)
  retains the approval, initializer refusal, value-preserving formatting correction,
  prompt transcript, config read-backs, doctor warnings and failed installed suites.
  The fixture stayed bound to PR #682's installed source; staging was not repeated.
- In `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`, at baseline
  `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus the staged/initialized adoption
  from `ab0a6d62308b298478b2f85fc961f14348f35365`, the installed pytest command
  retained in the record failed on 2026-09-06 UTC. Initialization's successful retry
  does not dispose of the doctor warnings or establish successful adoption verification.
- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `d898660c5da63a91f1916fa6b5f84357b5622ee4` plus initial record edits on
  2026-09-06 UTC failed in the recurring deep-payload hook assertion. The record
  retains terminal output and the approved #534 occurrence comment. The initializer
  issue proposal remains parked pending its own exact decision.
- The maintained [sprint status](../saved_plans/codex-parity-plan_2026-08-23.md)
  credits the delivered milestones, records Phase 5's in-progress adopt continuation,
  corrects stale TUI/review/batch scheduling statements and leaves Phase 6 not started.
- Initialization authority was exercised only for the exact fixture proposal.
  Adoption completion, fixture PR, final Phase 5 exit and cs-toolkit replay remain
  separate decisions. Preserve TRI-03/TRI-04/TRI-05 and #608/#255 dispositions.
  PR #684 remains test-mode systemize evidence; no live systemize route was attempted.

▶ Next: `$session-start` — follow the maintained Phase 5 reconciliation and this
adopt continuation's remaining boundary. Obtain exact decisions for the preserved
fixture ownership/registration/lens choices and verification follow-up before any
adoption completion; preserve the final replay and parked tracker decisions.

______________________________________________________________________

## Session — 2026-09-06 (adopt config compatibility, in Codex)

**Theme —** Implement #683 in the shared adopt workflow, before baseline recording
and the Step 3c operator handoff.

- Step 3a requires supported serialized representations and complete tracked and
  merged mapping comparisons through the installed destination reader. Runtime
  bindings and the parser are unchanged; this remains agent-executed verification.
- [PR #685 fixture evidence](https://github.com/topij/agentic-dev-kit/pull/685#issuecomment-5555450011)
  retains the disposable program and destination read-backs: default wrapping lost long focus/remedy tails; the corrected fixture
  preserved the complete mapping and a separate differing long local override.
  The fixture command `PYTHONDONTWRITEBYTECODE=1 uv run --with pyyaml python
  /private/tmp/adk683-6cfcvcic/verify_staging.py /Users/topi/Coding/agentic-dev-kit`
  in `/Users/topi/Coding/agentic-dev-kit` at
  `5588c36008cb376a34dc10fe3d0d54ab79332a73` on 2026-09-05 UTC succeeded.
- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `5588c36008cb376a34dc10fe3d0d54ab79332a73` on 2026-09-05 UTC printed
  `1 failed, 2436 passed, 1 skipped in 407.01s (0:06:47)` and make exited `2`.
  The quiet-tree run used an extended timeout with no watcher in flight. The
  failure was the recurring #393-shaped empty-output assertion in
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
  This run preceded the plan/handoff update; the PR carries later review evidence.
- The [full Codex panel disposition](https://github.com/topij/agentic-dev-kit/pull/685#issuecomment-5555538351)
  retains terminal reports, applied runtime read-backs, landed mutation diffs and
  byte-verified restoration at `e417f281f12938dc517701287d5d667c4937ce32`.
  The host CLI refused the configured model; the compatible installed runtime
  completed the lenses. CodeRabbit refused the requested review due to its rate limit.
  The correctness evidence-retention observation preceded the publication linked above.
  The retained commands in the named lens directories on 2026-09-05 UTC show the
  recurring hook failure, additional sandbox process-observation failures in the
  correctness suite, and setup refusals separately. Removing Step 3a was not caught
  behaviorally by the mutation runs; the workflow remains agent-executed prose.
- PR #684 retains test-mode systemize analysis, not live routing or Phase 5 exit.
  PR #682 retains approved adopt staging and the operator handoff, not adoption
  completion. This implementation repeated neither field exercise.
- Operator initialization, adoption completion, final Phase 5 exit, cs-toolkit replay
  and other field routes were not run. #243 stays open. Preserve TRI-03/TRI-04/TRI-05
  and the operator-held #608/#255 dispositions; no tracker or archive authority
  follows from the budget reminder or test-mode proposals.

▶ Next: `$session-start` — continue #243 from the maintained Phase 5 field-exercise
reconciliation; select the next bounded untested route and obtain any fresh exact
operator decisions it requires. Do not repeat credited exercises or treat #683 as
adoption completion or Phase 5 exit.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

