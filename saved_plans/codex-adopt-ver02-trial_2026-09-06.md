# VER-02 — panel-test root repair trial

The operator approved the exact VER-02 proposal retained in
[the continuation review](codex-adopt-completion-review_2026-09-06.md#exact-proposed-decision-ver-02--panel-test-root-repair-trial)
after separately authorizing PR #688's merge. That approval was exercised for this
disposable-copy trial on 2026-09-06. It grants no later execution or permanent repair.

## Bound inputs and execution

The kit checkout was `/Users/topi/Coding/agentic-dev-kit` at
`cd39158df81457feafa4bd281d928f8fec7d9faf`. The retained
[preflight](codex-adopt-ver02-evidence_2026-09-06/preflight.json) binds:

- Original fixture: `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`,
  branch `chore/adopt-agentic-dev-kit`, baseline
  `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus initialized adoption.
- Installed comparison source:
  `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`, detached at
  `ab0a6d62308b298478b2f85fc961f14348f35365`.
- Disposable roots: `/private/tmp/adk-adopt-ver02-ja4w9bd0/source-copy` and
  `/private/tmp/adk-adopt-ver02-ja4w9bd0/fixture-copy`. Their retained input/copy
  inventories compare file hashes, modes and symlink identities; Git metadata is
  independent, with the bound revisions and indexes and no origin remotes.

`PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 python3 -`, using the
[retained preflight command](codex-adopt-ver02-evidence_2026-09-06/preflight-command.json),
in the kit checkout at the revision above on 2026-09-06 UTC matched the retained
fixture snapshot, copy ledger, preserved inputs, synthetic overlay, post-init config,
install baseline and original verification log digest before creating the copies.
The initial branch-telemetry command refused the source's detached HEAD; its
[refusal](codex-adopt-ver02-evidence_2026-09-06/preflight-initial-refusal.json) is
retained. The corrected telemetry reads detached HEAD without requiring a branch.

The trial changed only `root = ENGINE.parent.parent` to `root = REPO_ROOT` inside
`test_the_committed_lens_definitions_are_what_the_generator_renders` in each copied
test module. [Source](codex-adopt-ver02-evidence_2026-09-06/source-patch.json) and
[fixture](codex-adopt-ver02-evidence_2026-09-06/fixture-patch.json) records retain
the exact applied diffs and destination hashes.

The initial supervisor stopped before pytest because the interpreter path returned
by `uv run` did not remain available. It restored the copied patches and rechecked
the originals. The continuation created a persistent environment under the same
scratch root, resolved its executable and package versions, then used that
absolute interpreter for every test invocation. The
[environment readback](codex-adopt-ver02-evidence_2026-09-06/persistent-environment-readback.json)
is the authority for those readings. This setup repair did not repeat a test.

The historical supervisors are retained as
[run_trial.py.txt](codex-adopt-ver02-evidence_2026-09-06/run_trial.py.txt) and
[resume_trial.py.txt](codex-adopt-ver02-evidence_2026-09-06/resume_trial.py.txt).
They record this consumed execution, not a reusable tool or a command to rerun.
The [publication-minimization record](codex-adopt-ver02-evidence_2026-09-06/publication-minimization.json)
records omitted ambient `PATH`, `HOME` and `TMPDIR` values. The original metadata
remains outside the repository; argv, cwd, execution controls, resolved-interpreter
readbacks, terminal streams and historical runner text are retained.

## Demonstrated outcomes and limits

The commands below ran on 2026-09-06 UTC, sequentially, with the corresponding copy
as cwd, a separate absolute `DEVKIT_STATE_ROOT`, `PYTHONDONTWRITEBYTECODE=1` and
a supervising timeout of 120 seconds per invocation. The terminal records retain
complete emitted stdout/stderr, statuses, times, environment and revisions.

```text
/private/tmp/adk-adopt-ver02-ja4w9bd0/venv/bin/python -m pytest --basetemp /private/tmp/adk-adopt-ver02-ja4w9bd0/source-basetemp -q scripts/tests/test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders
/private/tmp/adk-adopt-ver02-ja4w9bd0/venv/bin/python -m pytest --basetemp /private/tmp/adk-adopt-ver02-ja4w9bd0/fixture-basetemp -q scripts/devkit/tests/test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders
```

- The [source command](codex-adopt-ver02-evidence_2026-09-06/source-trial.json),
  at `ab0a6d62308b298478b2f85fc961f14348f35365` plus the copied-test patch,
  passed without a skip.
- The [fixture command](codex-adopt-ver02-evidence_2026-09-06/fixture-trial.json),
  at `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus copied initialization and
  the test patch, reached the actual lens equality assertion. It failed on
  `.claude/agents/adversarial.md`, showing `scripts/panel_prompt.py` in the
  preserved file against `scripts/devkit/panel_prompt.py` in the generated value.
  The former missing-config failure was bypassed by the root repair.
- The source command was then repeated at its same bound revision/test patch
  with the approved `\nVER-02 mutation sentinel\n` appended to the source-copy
  adversarial definition. Its [terminal result](codex-adopt-ver02-evidence_2026-09-06/source-mutation.json)
  rejected the sentinel at the equality assertion. The
  [landed mutation](codex-adopt-ver02-evidence_2026-09-06/mutation.json) and
  [restoration](codex-adopt-ver02-evidence_2026-09-06/resumed-restoration.json)
  retain the changed bytes and equality checks after restoring the definition
  and copied test patches.

The fixture invocation stopped at the adversarial lens; it did not reach the
correctness lens. Pytest abbreviated the value diff in its emitted output. The
[mismatch comparison](codex-adopt-ver02-evidence_2026-09-06/mismatch-comparison.json)
compares preserved fixture bytes with PR #687's retained renderer output and finds
the same adversarial hunk as the retained ownership/lens proposal. It is not a fresh
capture of the full generated value and does not establish a correctness-lens pass.

`PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 python3
/private/tmp/adk-adopt-ver02-ja4w9bd0/resume_trial.py` in the kit checkout at
`cd39158df81457feafa4bd281d928f8fec7d9faf` on 2026-09-06 UTC completed its
restoration and [final continuity checks](codex-adopt-ver02-evidence_2026-09-06/continuity-after-resumed-trial.json).
The original source/fixture inventories, Git state and legacy snapshot matched.

This supports the root-repair mechanism and the continued effectiveness of the
lens equality assertion under this trial. It does not land the repair, validate
runtime discovery or compute, dispose of the installed suite's other failures, or
establish adoption completion. No initializer, original-fixture edit, other VER-01
node, fixture PR, Phase 5 exit, cs-toolkit replay or tracker write was performed.

## Proposed exact decision: VER-03 — permanent root repair and layout regression

**Prepared for a fresh operator decision; not implemented.** Review the retained
VER-02 evidence in the next session before deciding this scope. If the kit test or
helper has changed, present the current diff and revise the proposal before approval.

- In `scripts/tests/test_panel_prompt.py`, apply the trial's exact root assignment
  inside the named test. Preserve its marker, roster check and lens equality.
- In that same test module, add a regression exercising the real root discovery
  and renderer in isolated `scripts` and `scripts/devkit` layouts. Supply a Git
  root marker, configured engine path and generated synthetic definitions; require
  the named comparison to pass and to reject a deliberately changed definition
  at the equality assertion. The regression must exercise the nested layout, not
  merely assert that the module contains `REPO_ROOT`.
- In a disposable regression copy, restore the old root assignment and show that
  the nested-layout regression detects it. Retain the landed mutation, terminal
  failure and byte restoration. Also retain the definition-mutation evidence;
  drift/hash checks must not be credited as behavioral mutation kills.
- Refresh only the changed test's digest in `kit-manifest.json`. Run the focused
  regression and repository `make test` with extended timeouts and stamped evidence;
  preserve any unrelated failure as a verification limit. Do not rerun VER-01 or
  VER-02, and do not use the original adoption fixture for this repair's tests.
- Record the result in this maintained continuation and sprint/handoff artifacts,
  open a ready kit repair PR, and complete `pr-watch`. Hold merge for a separate
  exact operator decision.

This proposed scope permits no production-engine, workflow, adapter, config,
registration or original-fixture change. Any need to expand the footprint returns
to the operator before execution. Fixture ownership and lens hunks, registration
payloads, new initialization, further adoption verification, adoption completion,
fixture PR, Phase 5 exit and cs-toolkit replay retain separate exact decisions.
TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the parked initializer issue
proposal remain reserved; an incidental friction sweep cannot graduate them.

## Next-session starter — Claude

```text
/session-start — follow docs/kit-handoff.md and the maintained Phase 5 reconciliation for #243. Read saved_plans/codex-adopt-ver02-trial_2026-09-06.md and its retained evidence, alongside the continuation review and PR #688. Review Codex's VER-02 outcomes and limits without repeating credited probes or exercises. Present VER-03's exact permanent root-repair and layout-regression scope for a fresh operator decision before implementing it. Recheck source/fixture continuity before any separately approved execution. Preserve separate decisions for initialization, fixture ownership/lenses/registration, verification follow-up, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay, plus TRI-03/TRI-04/TRI-05, #608/#255 and the parked initializer proposal. Update the maintained sprint status and next-session starter during /wrap-up and complete required PR follow-through. This starter grants no execution or merge approval.
```

Claude is suggested to review Codex's evidence from the other runtime. That is a
workflow choice for this parity exercise, not a model-performance ranking.

## Kit record verification and wrap-up

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`cd39158df81457feafa4bd281d928f8fec7d9faf` plus the trial-record and maintained-doc
edits on 2026-09-06 UTC passed lint and failed the recurring
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`
assertion. The [metadata](codex-adopt-ver02-evidence_2026-09-06/make-test.json),
[terminal output](codex-adopt-ver02-evidence_2026-09-06/make-test-output.json) and
[runner](codex-adopt-ver02-evidence_2026-09-06/run_make.py.txt) retain the result and
extended timeout. This kit verification is separate from VER-02's named diagnostic;
it preceded this paragraph and the output copy. The record PR carries subsequent
validation and review at its own head.

`uv run scripts/check_doc_budget.py` in the same kit checkout at that revision plus
the record edits on 2026-09-06 UTC directed the handoff archive. The configured
`archive_plan_sessions.py --target-lines 400` moved the oldest session block into
`docs/kit-handoff-history.md`; the post-archive budget check completed with the
friction-log warning preserved. No friction graduation or tracker write was taken.
