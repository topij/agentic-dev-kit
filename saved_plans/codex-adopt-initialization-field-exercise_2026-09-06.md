# Codex adopt initialization continuation — 2026-09-06

This continues PR #682's existing disposable fixture at Step 3c. It does not restage
that exercise or repeat PR #684's systemize test. PR #685 delivered #683's installed
config-reader comparison; it did not establish initializer compatibility.

## Authority and binding

The operator approved the retained [exact proposal](codex-adopt-initialization-evidence_2026-09-06/operator-decision.md)
with “approved” in this session. The [approval record](codex-adopt-initialization-evidence_2026-09-06/approval.json)
binds the proposal digest and the fixture-only executor override. Initialization and
Step 4 checks were authorized; adoption completion, a fixture remote or PR, Phase 5
exit, cs-toolkit replay, TRI-03/TRI-04/TRI-05 and #608/#255 dispositions were reserved.
The later request to audit the active sprint and include it in wrap-up authorizes this
record and the maintained plan/handoff updates.

- Fixture: `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`, branch
  `chore/adopt-agentic-dev-kit`, Git baseline
  `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus the uncommitted staged adoption.
- Installed source: `ab0a6d62308b298478b2f85fc961f14348f35365`; the independent
  comparison clone is `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`
  at that SHA. The continuation did not upgrade the fixture to the session checkout.
- Session checkout: `/Users/topi/Coding/agentic-dev-kit` at
  `d898660c5da63a91f1916fa6b5f84357b5622ee4` before this record's edits.

The proposal stamps the pre-write continuity command. Its
[program](codex-adopt-initialization-evidence_2026-09-06/check_continuity.py) checks
PR #682's retained inputs, copy ledger and baseline. It is a pre-initialization probe,
so its absent-file assertions must not be replayed against the initialized fixture.

## Execution and retained results

All fixture observations below were made on 2026-09-06 UTC in the fixture directory
above, at its stated Git baseline plus staged/initialized changes, using the bound
installed source. The evidence directory retains the exact invocations, terminal
outputs, compared mappings and configuration snapshots; its
[SHA-256 ledger](codex-adopt-initialization-evidence_2026-09-06/sha256.json) covers the retained files.
These are session observations, not a live-validation capability promotion.

`./init.sh --no-clobber` first refused the staged indentless `doc_budgets` sequence
before presenting prompts. The [refusal](codex-adopt-initialization-evidence_2026-09-06/init-initial-refusal.json)
records the terminal result. The source initializer's top-level preflight treats the
unindented sequence items as unsupported top-level syntax, although the installed
`kitconfig` reader accepts that serialization.

A fixture-only formatting correction indented the sequence and normalized the empty
prompted tracker strings to double-quoted empty strings. Complete tracked and merged
mapping comparisons preserved the approved values. The empty-string normalization
was preventive; this run did not reproduce a separate empty-default failure. No
initializer, parser or workflow code was changed. The
[before](codex-adopt-initialization-evidence_2026-09-06/config-before-init.yaml),
[compatible](codex-adopt-initialization-evidence_2026-09-06/config-before-init-compatible.yaml)
and [after](codex-adopt-initialization-evidence_2026-09-06/config-after-init.yaml)
configurations retain the representation change.

The retry used the exact approved prompt values and exited successfully. Its
[terminal transcript](codex-adopt-initialization-evidence_2026-09-06/init-terminal.json)
records seeding the absent friction documents and lane settings profile, adding state
ignore patterns and installing the pre-push hook. It preserved the fixture-owned
narrative inputs and wrap-up adapter. The
[post-init read-back](codex-adopt-initialization-evidence_2026-09-06/post-init-readback.json)
records complete tracked/merged mapping equality, baseline equality and preserved-file
comparisons. The marked `AGENTS.md` was deliberately left untouched by `--no-clobber`.

`uv run scripts/devkit/kit_doctor.py --manifest
/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source/kit-manifest.json`
returned successfully with the [report](codex-adopt-initialization-evidence_2026-09-06/kit-doctor.json):
installed file hashes matched the declared installation, but `AGENTS.md` remained
marked, runtime registrations were absent, and the Claude lens definitions differed
from the running doctor's rendering. These warnings prevent treating the command's
exit status as adoption completion. `uv run scripts/devkit/check_doc_budget.py`
also returned successfully; its [output](codex-adopt-initialization-evidence_2026-09-06/document-budget.json)
retains the fixture document readings.

`uv run --with pytest --with pyyaml python -m pytest
scripts/devkit/lib/state_paths/tests/ scripts/devkit/tests/ -q` printed
`79 failed, 2006 passed, 111 skipped in 388.78s (0:06:28)` and exited `1`.
The [runner](codex-adopt-initialization-evidence_2026-09-06/run_verification.py),
[invocation metadata](codex-adopt-initialization-evidence_2026-09-06/fixture-verification.json)
and [terminal log](codex-adopt-initialization-evidence_2026-09-06/fixture-verification-output.json)
retain the isolated state root, timing, environment and actual failures. No broad
rerun with exclusions was used to claim successful verification.

Representative traces show the panel-prompt test reading the absent
`fixture/scripts/config/dev-model.yaml`, skeleton tests expecting kit narrative
files in the adopter, and adapter-test setup rejecting the deliberately preserved
fixture-owned wrap-up adapter. The initializer tests also expect kit-specific config
and runtime registrations. These examples fit #534's kit-only/layout-assumption scope;
they do not classify every failure, and no same-source flat-layout control was run in
this continuation. The [occurrence proposal](codex-adopt-initialization-evidence_2026-09-06/vendored-suite-occurrence.md)
and [initializer issue proposal](codex-adopt-initialization-evidence_2026-09-06/init-compatibility-issue.md)
were presented for separate exact tracker decisions. The operator subsequently
approved the occurrence comment; its
[posted payload](https://github.com/topij/agentic-dev-kit/issues/534#issuecomment-5557692003)
was read back against the exact approved bytes. The evidence retains that separate
[decision](codex-adopt-initialization-evidence_2026-09-06/tracker-decision.json) and
[read-back](codex-adopt-initialization-evidence_2026-09-06/tracker-readback.json).
The initializer issue proposal remains parked pending its own exact decision.

## Maintained sprint reconciliation

The active [parity plan](codex-parity-plan_2026-08-23.md) retains the delivered Phase 1,
Phase 2, Phase 3 and Phase 4 milestones. Its maintained status now points to PR #680's
scoped TUI observation, PR #667's review evidence delivery and PR #659's retained
parallel-batch exit rather than leaving those deliveries as future work. The historical
sprint-review baseline is unchanged.

Phase 5 remains in progress: the adopt route now credits initialization and attempted
Step 4 verification, while adoption completion and untested systemize routes remain
pending. The initial cs-toolkit write pass stays credited; the final replay and its
immutable exit tuple remain unexecuted. Phase 6 remains not started. This record adds
no new initialization, adoption-completion, replay or tracker authority.

## Remaining boundary

Review the preserved-file choices with the operator, including `AGENTS.md` ownership,
runtime registrations and the lens definitions. Resolve the installed-verification
failures within separately approved scope before claiming adoption completion.
A fixture remote or PR needs its own decision. Preserve the existing parked triage
entries and #608/#255 dispositions; neither the budget reminder nor a test-mode
proposal grants archive or tracker authority.

## Kit checkout verification

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`d898660c5da63a91f1916fa6b5f84357b5622ee4` plus the initial record/plan/handoff
edits on 2026-09-06 UTC printed
`1 failed, 2436 passed, 1 skipped in 362.05s (0:06:02)`; make exited `2`.
The [metadata](codex-adopt-initialization-evidence_2026-09-06/kit-verification.json)
and [terminal output](codex-adopt-initialization-evidence_2026-09-06/kit-verification-output.json)
retain the extended timeout and the failure in
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
The same assertion is recorded in the preceding handoff; this continuation did not
change it. This kit run used the session checkout, not a same-source flat-layout
control for the older fixture installation. It preceded the final verification
paragraph and parked-friction entries. The wrap-up PR carries later CI and review
results at its reviewed head.
