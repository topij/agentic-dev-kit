# VER-03 — permanent panel-test root repair

The operator approved the exact VER-03 scope with “VER-03 approved” on 2026-09-06.
The scope is retained in the [VER-02 record](codex-adopt-ver02-trial_2026-09-06.md#proposed-exact-decision-ver-03--permanent-root-repair-and-layout-regression).
This session executed that kit test repair in Codex. Its execution approval is
consumed; merge and the remaining fixture decisions are separate.

## Repair and input continuity

Commit `12a67be290989165e0e7f714942c3d59e38696fc` changes the named lens comparison
to use its existing `REPO_ROOT`, preserving the marker, roster check and equality
assertion. The same module adds a subprocess regression with synthetic `scripts`
and `scripts/devkit` layouts. Each carries a Git root marker, explicit engine-path
config, copied real test/helper/renderer dependencies and generated definitions.
Only this test's digest changes in `kit-manifest.json`.

The [pre-edit audit](codex-adopt-ver03-evidence_2026-09-06/continuity-before.json)
was `python3 -` in `/Users/topi/Coding/agentic-dev-kit` at
`188cd97198dbee34919369cfa75a9379d9ddc6eb` on 2026-09-06 UTC. It matched the
retained source/fixture inventories, Git state, legacy fixture hashes and evidence
digests, and found no test/helper/renderer change from VER-02's source. This was a
read-only continuity check; it did not rerun a fixture test or renderer.

`python3 /private/tmp/adk-ver03-7m5h8wtr/check_continuity.py` in that kit checkout
at `12a67be290989165e0e7f714942c3d59e38696fc` on 2026-09-06 UTC matched those
original source/fixture inventories, Git state and legacy hashes after the focused
regression and mutation. The [result](codex-adopt-ver03-evidence_2026-09-06/continuity-after.json)
and retained program bind the read; continuity must be rechecked before a later
approved fixture action.

## Behavioral verification

The commands below ran on 2026-09-06 UTC under the retained
[supervisor](codex-adopt-ver03-evidence_2026-09-06/run_command.py.txt).
The source revision was `188cd97198dbee34919369cfa75a9379d9ddc6eb` plus the test
and manifest edits subsequently committed as `12a67be290989165e0e7f714942c3d59e38696fc`.
The metadata binds the test bytes, command, cwd, timeout, execution controls,
terminal streams and their digests. The child results and copied-file hashes are
linked through [layout bindings](codex-adopt-ver03-evidence_2026-09-06/layout-bindings.json).

```text
uv run --with pytest --with pyyaml python -m pytest --basetemp /private/tmp/adk-ver03-7m5h8wtr/focused-basetemp -q scripts/tests/test_panel_prompt.py::test_committed_lens_comparison_in_relocated_layout
uv run --with pytest --with pyyaml python -m pytest --basetemp /private/tmp/adk-ver03-7m5h8wtr/mutation-basetemp -q scripts/tests/test_panel_prompt.py::test_committed_lens_comparison_in_relocated_layout
```

- The [focused command](codex-adopt-ver03-evidence_2026-09-06/focused.json), cwd
  `/Users/topi/Coding/agentic-dev-kit`, passed the flat and nested cases without
  skips. Within each case the real named comparison passed, then rejected a
  deliberate adversarial definition change and a deliberate correctness definition
  change at the lens equality assertion. The test restored each definition in a
  `finally` block and checked its bytes.
- The [mutation command](codex-adopt-ver03-evidence_2026-09-06/old-root-mutation.json),
  cwd `/private/tmp/adk-ver03-7m5h8wtr/mut-root-old-188cd97`, used a disposable copy
  with the old root assignment restored. The flat case passed; the nested case
  failed when its positive comparison read `scripts/config/dev-model.yaml` and
  raised `FileNotFoundError`. This is the regression detecting the original root
  defect, not a claim that a definition mismatch reached equality in this mutant.
  The [landed diff](codex-adopt-ver03-evidence_2026-09-06/root-mutation.diff), copied
  input hashes, terminal result and [byte restoration](codex-adopt-ver03-evidence_2026-09-06/root-restoration.json)
  are retained. No drift/hash test ran in these focused commands.

The synthetic child commands, definition mutation diffs and restored definition
hashes are retained with the parent run. Historical supervisors and terminal
records are evidence of consumed execution, not instructions to repeat VER-01,
VER-02 or this mutation trial.

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`12a67be290989165e0e7f714942c3d59e38696fc` on 2026-09-06 UTC passed lint and
failed the recurring
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`
assertion. Its [terminal record](codex-adopt-ver03-evidence_2026-09-06/make-test.json)
printed `1 failed, 2438 passed, 1 skipped in 354.03s (0:05:54)`; the supervisor
returned status `2` without a timeout. The source test and manifest were committed
before the run; the narrative records were being prepared during it. This is a
verification limit, not a new scope to repair the hook or repeat an adoption probe.

`uv run scripts/check_doc_budget.py` in that kit checkout at the same revision
plus the maintained-record edits on 2026-09-06 UTC completed with the handoff within
its configured budget and the existing friction-log warning. No handoff archive
or friction graduation was performed in this wrap-up. The PR carries subsequent
record validation and independent review at its exact head.

## Remaining boundary and next session

This repairs a kit test and exercises synthetic layouts. It does not replace the
test in the original adoption fixture or resolve that fixture's retained
ownership, runtime-registration or lens-definition decisions. VER-02's original
fixture comparison stopped at the adversarial mismatch; these synthetic
correctness-lens checks do not fill that original-fixture verification gap.
The installed suite's other failures still need their own bounded assessment.

The maintained Phase 5 reconciliation continues to hold adoption completion,
fixture PR, Phase 5 exit and cs-toolkit replay separately. New initialization,
fixture changes and verification follow-up need fresh exact decisions.
TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the parked initializer issue
proposal remain reserved. The original adoption fixture and runtime registrations
were not changed; no initializer or tracker write was performed under VER-03.

```text
In Claude, /session-start — follow docs/kit-handoff.md and read
saved_plans/codex-adopt-ver03-repair_2026-09-06.md. Review the retained VER-03
result and the continuation review's ownership/lens diff, then prepare an exact
fixture decision. Keep registration and verification follow-up separately scoped;
recheck continuity before approved execution. Do not repeat credited probes or
exercises, or advance initialization, adoption completion, fixture PR, Phase 5 exit,
cs-toolkit replay or reserved tracker dispositions without their own decisions.
```
