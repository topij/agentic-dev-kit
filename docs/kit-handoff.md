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

Last updated: 2026-09-06 — approved FIX-01 applied fixture ownership and lens
definitions; registration and verification follow-up stay separate.

## Latest session — 2026-09-06 (approved FIX-01 application, in Claude Code)

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
failures in PR #686's retained terminal log. #534 is scoped to a `REPO_ROOT / "scripts"`
hardcoding in four named test files, so check each failure against that scope before
adding an occurrence there rather than filing it separately — `test_lane_launcher.py`
in particular fails on a different assumption. Recheck continuity against
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

## Session — 2026-09-06 (systemize test record, in Codex)

**Theme —** Retain the bounded test observation and update the field-exercise
reconciliation under the operator's separate record-and-wrap-up authorization.

- The [field record](../saved_plans/codex-systemize-test-field-exercise_2026-09-06.md)
  retains context, preflight, trusted source material, digest validation, artifact
  checkpoint probes and proposed routes. This credits test-mode analysis only.
- The maintained parity plan preserves the earlier parallel, triage and bounded
  adopt evidence. PR #682 ended at the Step 3c operator handoff; #683 owns its
  separately identified config-serialization gap.
- The exercise's `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `4c4ce47ce067309f3cb24733a939c40c76911a4a` on 2026-09-05 UTC failed in
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
  The field record retains the terminal output and verification limits.
- No test-mode routing or tracker disposition was executed. Preserve
  TRI-03/TRI-04/TRI-05 and the operator-held #608/#255 dispositions. Adoption
  completion, final Phase 5 exit and cs-toolkit replay remain separately scoped.

▶ Next: `$session-start` — implement #683 in the shared adopt workflow and verify
serialized config through the installed reader, including long scalars and the
local overlay. Keep the operator initialization boundary and later adoption
verification separate; follow the maintained plan before any final adopter replay.

______________________________________________________________________

## Session — 2026-09-05 (adopt context field exercise, in Codex)

**Theme —** Exercise adopt's context carrier through its shared workflow in a
local disposable fixture, with the operator's explicit staging approval.

- The [field record](../saved_plans/codex-adopt-field-exercise_2026-09-05.md)
  retains inputs, inspection, copy/baseline read-backs, the cache refusal, and
  the Step 3c operator handoff. `init.sh` and later adoption stages were not run.
- The maintained parity plan now reconciles the older `#243` follow-up list with
  retained parallel-batch evidence and the completed Codex triage route. It
  credits those bounded routes without repeating them or claiming Phase 5 exit.
- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `ab0a6d62308b298478b2f85fc961f14348f35365` on 2026-09-05 failed in
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
  The record retains the terminal output and quiet-tree verification limits.
- No tracker dispositions changed. Preserve TRI-03/TRI-04/TRI-05 and the
  operator decisions for `#608`/`#255`; no cs-toolkit replay was attempted.

▶ Next: `$session-start` — follow the maintained Phase 5 field-exercise
reconciliation. Take `post-merge-systemize` as a separate bounded field slice;
keep adoption completion and the final cs-toolkit replay explicitly scoped.

______________________________________________________________________

## Session — 2026-09-05 (runtime declarations, in Codex)

**Theme —** Deliver the joined Phase 5 declaration and config-test scope, then hand
the remaining field exercises to a fresh Codex session.

- [PR #680](https://github.com/topij/agentic-dev-kit/pull/680) merged on 2026-09-05
  as `3898204a00948ac5c73745dbb4bc551967b16e62`. It carries `#608`'s non-load-bearing
  matrix row and `#255`'s general declaration-presence test together.
- The first-hand Codex TUI observation is in that PR: `systemMessage` was displayed,
  so the row does not repeat the planned "not observed" claim. This scoped observation
  does not establish a general client guarantee. The config test covers the reference
  and newly emitted migration blocks; it does not establish carrier truth or backfill
  declarations into preserved existing blocks.
- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `bb27a58ae640a7541d34bc984333565e4a435166` on 2026-09-05 failed at
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
  The [review disposition](https://github.com/topij/agentic-dev-kit/pull/680#issuecomment-5553981033)
  retains the verification limits, accepted fixes, and the logged P3 prose imprecision
  on `#163`. Executed test-code fix rounds received full Codex panels.
- The final Phase 5 exit and adopter replay were not attempted. Reconcile the tracker
  dispositions for `#608` and `#255` with the landed work on the operator's decision.
  Preserve `TRI-03`, `TRI-04`, and `TRI-05`; graduation still needs fresh exact
  operator dispositions through `triage-friction-log`.

▶ Next: In a fresh Codex session, run `$session-start` and follow
`docs/kit-handoff.md`. Reconcile prior evidence against `#243`, then take a bounded
`adopt` field exercise through the shared workflow in an isolated fixture. Keep the
remaining field exercises and final adopter replay separate.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
