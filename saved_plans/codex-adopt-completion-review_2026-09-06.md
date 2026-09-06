# Adopt continuation review — 2026-09-06

This read-only assessment continues PR #686's initialization record under the
operator's request to review the remaining work and select a bounded next action.
The original fixture was not initialized again, edited, committed or registered
with a runtime. The credited parallel, triage, adopt staging and systemize test
exercises were not repeated.

## Inspection and ownership

`PYTHONDONTWRITEBYTECODE=1 python3
/private/tmp/adk-adopt-review-20260906-WJZrv7/inspect_fixture.py` ran in
`/Users/topi/Coding/agentic-dev-kit` at
`2f4275642d4d75598a7fad7d865608b488b4c726` plus review corrections on 2026-09-06
UTC and completed successfully. `.gitignore` is outside the pre-initialization
input-equality assertion because initialization added the recorded ignore entries.
The program, [report](codex-adopt-completion-review-evidence_2026-09-06/inspection.json)
and [proposed diff](codex-adopt-completion-review-evidence_2026-09-06/ownership-and-lenses.patch.json)
are retained together. The report verifies retained evidence hashes, installed
copy-ledger bytes, post-init config and baseline equality, retained policy inputs,
and fixture file equality before and after this inspection. It is a continuity
observation, not adoption verification.

The bound fixture is `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`,
on `chore/adopt-agentic-dev-kit` at Git baseline
`08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus the staged/initialized adoption.
Its source remains `ab0a6d62308b298478b2f85fc961f14348f35365`, with independent
comparison checkout `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`.

The installed doctor and lens-render commands in the report ran in that fixture,
at those bound revisions, on 2026-09-06 UTC. The doctor returned successfully while
reporting the retained ownership, registration and lens warnings. The render
commands completed successfully without applying their output.

| Decision | Evidence and proposed handling | Authority still needed |
|---|---|---|
| `AGENTS.md` ownership | The file contains fixture policy below the marker. The proposed diff removes the marker while retaining the policy verbatim. `CLAUDE.md` already imports it. | Exact approval to apply the diff, plus the operator's confirmation that retained content reads as intended. |
| Runtime registration | `.codex/config.toml`, `.codex/hooks.json` and `.claude/settings.json` were absent in the inspection. The source initializer deliberately prints registrations instead of installing them. | Choose the intended runtime registration scope before preparing and approving its exact payload. File inspection cannot establish loaded hooks or project trust. |
| Lens definitions | The installed renderer's diff changes the engine path to `scripts/devkit/panel_prompt.py` in `.claude/agents/adversarial.md` and `.claude/agents/correctness.md`; model and effort do not change. | Exact approval to apply the retained generated diff. This does not establish runtime discovery or applied compute. |
| Installed verification | The report binds PR #686's original terminal log by digest; use that log directly. | Review the independent probes below before deciding further diagnostic or test-repair scope. |

The ownership and lens diff is review material, not an executable instruction to
apply it. A bare initializer run is not the proposed ownership remedy. Registration
choices must also preserve the distinction between Codex's project hooks and Claude's
cockpit settings; neither follows from the retained Claude lens files being present.

## Verification assessment

The retained terminal traces and installed test source support these nominated
diagnoses. They do not classify every failed node or dispose of the installed suite:

| Test | Trace and source reading | What a fixture cleanup cannot establish |
|---|---|---|
| `test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders` | `root = ENGINE.parent.parent` resolves the vendored engine to `fixture/scripts`, followed by a missing `scripts/config/dev-model.yaml`. | Regenerating the lens files cannot repair this root calculation. |
| `test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes` | The comparison uses the adopter as its source kit; the preserved `.agents/skills/wrap-up/SKILL.md` is rejected as a source adapter. | Replacing fixture-owned policy to satisfy a source-kit assertion would invalidate the preservation exercise. |
| `test_kitconfig.py::test_shipped_skeletons_carry_the_unrendered_marker[handoff.md]` | The test reads literal `docs/handoff.md`, while the fixture's configured plan is `ROADMAP.md` and the shipped templates were installed separately. | Adding a redundant plan to satisfy this assertion would change the approved adoption. |

Initializer failures also appear in the retained terminal log; they remain outside this
selected diagnostic scope. The existing occurrence on #534 already records the
vendored-suite finding. No tracker occurrence was added.

The adversarial lens supplied diagnostic evidence during
[independent review](https://github.com/topij/agentic-dev-kit/pull/687#issuecomment-5558033584).
The retained [program](codex-adopt-completion-review-evidence_2026-09-06/probe_diagnoses.py)
and its [source-copy result](codex-adopt-completion-review-evidence_2026-09-06/source-copy-diagnoses.json)
and [fixture-copy result](codex-adopt-completion-review-evidence_2026-09-06/fixture-copy-diagnoses.json)
name the actual test commands and directories, run on 2026-09-06 UTC.
The source-copy command at
`ab0a6d62308b298478b2f85fc961f14348f35365` passed; the fixture-copy command at
baseline `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus copied initialization
failed in the named tests with the nominated path/ownership traces.

These are independent review probes. They do not record operator approval or
establish adoption completion. The derived failed-node inventory was removed after
the panel demonstrated truncation inside parameter IDs; the original log retains
the complete failure text.

## VER-01 reconciliation — 2026-09-06

VER-01 remains an unapproved historical proposal. Its named comparison has
independent evidence already; lack of operator approval is not an evidence gap and
is not a reason to repeat it. PR #687 merged on 2026-09-06 as
`61776212a2694108c5dfd8c2640c8b8ef08a40f4`; its retained review reports are the
provenance for those probes, not an operator execution decision.

The commands, directories, revisions and date in the linked probe results above
establish the source pass and fixture failures for the named nodes. The retained
program runs them sequentially, requests the same Python through `UV_PYTHON`, uses
an offline seeded dependency cache, and separates `DEVKIT_STATE_ROOT` and pytest
`--basetemp`. The fixture traceback identifies the Python installation it used.
The result JSON does not independently read back the resolved interpreter and
package versions or retain the pre-run copy digests; the program does not construct
the copies. Credit the observed outcomes and the review's copy provenance without
claiming that every proposed VER-01 telemetry requirement was executed. Those
historical limits do not call for a ceremonial rerun.

The remaining verification gap is adoption-relevant coverage. The installed suite's
original terminal log remains authoritative; the named probes neither classify its
other failures nor demonstrate a corrected test reaching its intended assertion.
A missing path, preserved adapter, or absent source skeleton cannot be repaired by
replacing fixture-owned content merely to satisfy a source-kit test. Initializer,
launcher-policy and portability failures in that log still need their own source
and precondition assessment. No new derived failed-node inventory is maintained.

`python3 -` (the retained continuity audit program) in
`/Users/topi/Coding/agentic-dev-kit` at
`61776212a2694108c5dfd8c2640c8b8ef08a40f4` on 2026-09-06 UTC completed its
assertions. The [continuity result](codex-adopt-verification-reconciliation-evidence_2026-09-06/continuity.json)
binds the fixture snapshot to PR #687's inspection, source checkout, copy ledger,
preserved inputs, post-init config, install baseline and original terminal digest.
It records fixture file equality around the read. It runs no doctor, renderer,
pytest node or initializer, and does not establish loaded hooks or adoption success.
Recheck continuity immediately before any later approved execution; this observation
is not an enduring approval precondition.

## Exact proposed decision: VER-02 — panel-test root repair trial

**Prepared for operator decision; not executed.** This is a diagnostic patch in
private copies, not a landed kit repair. The question is whether correcting the
known root calculation reaches the lens-content assertion, and what that assertion
then reports about the initialized fixture.

**Inputs and write boundary.** Use the original fixture and comparison-source paths
bound above. Before writing, require their revisions, fixture branch/no-remote,
post-init config, synthetic overlay, preserved inputs, copy-ledger bytes and baseline
to match the retained continuity evidence. Stop and present any difference. Create
fresh flat-source and initialized-fixture copies beneath a unique
`/private/tmp/adk-adopt-ver02-*` directory. Preserve the fixture's staged files and
synthetic overlay, give each copy independent Git metadata at its bound input SHA,
and leave both without origin remotes. Bind absolute roots, assert the destination
`pwd` before each write sequence, and retain destination hashes including modes and
symlink identities. Compare each copy with its input before the trial patch.

**Exact trial edit.** In the source copy's `scripts/tests/test_panel_prompt.py` and
the fixture copy's `scripts/devkit/tests/test_panel_prompt.py`, change only the
assignment inside
`test_the_committed_lens_definitions_are_what_the_generator_renders`:

```diff
-    root = ENGINE.parent.parent
+    root = REPO_ROOT
```

`REPO_ROOT` is already obtained from `_repo_layout.find_repo_root` in that module.
Save original bytes, assert the named assignment exists in the named function,
and retain the applied diff. Keep the existing marker, configuration read and
lens equality assertion. Do not change the original fixture, kit working tree,
engines, manifest, runtime registrations, policy or config. Generated definitions
stay unchanged except for the source-copy mutation explicitly specified below.

**Commands.** Resolve a Python interpreter and pytest/PyYAML environment once;
record `sys.executable`, Python version and package versions from that environment
before using its absolute interpreter path for each invocation. Run sequentially:

```text
<PYTHON> -m pytest --basetemp <SOURCE_TEMP> -q scripts/tests/test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders
<PYTHON> -m pytest --basetemp <FIXTURE_TEMP> -q scripts/devkit/tests/test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders
```

The cwd is the corresponding private copy. Set `PYTHONDONTWRITEBYTECODE=1` and a
separate absolute `DEVKIT_STATE_ROOT` for each run. Set a timeout of 120 seconds
per invocation; retain argv, cwd, revisions, original and patched hashes, environment,
start/end times, complete terminal output and exit status, including timeout/setup
refusals. A skipped, uncollected or refused node does not establish the control.
Do not run the other VER-01 nodes or a broad suite for this diagnostic.

**Success criteria and stop.** The patched flat-source node must pass without a
skip. The fixture node must reach the actual configured lens comparison instead
of failing on `scripts/config/dev-model.yaml`. A mismatch is a diagnostic result,
not permission to regenerate a lens or call the fixture verified. Compare the
mismatch with the retained ownership/lens proposal and report any difference.
If the control passes, append `\nVER-02 mutation sentinel\n` to the source copy's
`.claude/agents/adversarial.md`, retain the landed mutation diff, and run only that same
source node to show the equality assertion rejects it. Restore and byte-check both
the definition and test patches before reporting. A failure before the equality
assertion is not a mutation kill. Recheck the untouched original fixture and
source checkout. Return the terminal evidence and a proposed permanent repair
scope; stop before implementing that repair or advancing adoption.

Re-running this node after the exact trial edit asks a new question about the
repaired path. It does not repeat VER-01 merely to obtain an approval-shaped result.
Approval of VER-02 authorizes only the copy creation, copied-test patch, named
invocations, source-copy mutation/restoration and evidence recording above.
It authorizes no initializer run, original-fixture change, permanent source repair,
fixture PR, adoption completion, Phase 5 exit, cs-toolkit replay or tracker write.

## Remaining fixture decisions

| Separate decision | Concrete material or prerequisite |
|---|---|
| New initialization | Fresh exact command, inputs and destination decision; the PR #686 approval was consumed. VER-02 runs no initializer. |
| Fixture ownership | Approve only the `AGENTS.md` hunk in the retained patch, removing the marker while preserving policy, and confirm the retained policy reads as intended. |
| Fixture lens definitions | Approve only the retained `adversarial.md` and `correctness.md` hunks after byte continuity; they update the engine path. Runtime discovery and applied compute need separate evidence. |
| Runtime registration | Choose Codex project hooks, Claude cockpit settings, or both before preparing exact file payloads. File absence and initializer advice do not establish loaded registrations, trust or permission grants. |
| Verification follow-up | VER-02 is the proposed next slice. Adapter source fixtures, narrative-skeleton applicability, initializer preconditions, launcher-policy and portability assertions remain outside it. A permanent test repair needs a fresh scope decision. |
| Adoption completion | Requires the agreed fixture changes, resolved verification applicability and successful adoption-relevant checks; a passing flat source or warning-only doctor exit cannot substitute. |
| Fixture PR | Needs its own remote/destination, change scope and review decision after fixture verification. This kit record PR does not create or authorize it. |
| Phase 5 exit | Remains subject to the maintained plan's field-coverage and adopter-condition evidence and its own exact decision. |
| cs-toolkit replay | Requires its own current-source, origin and ancestry-bound approval/evidence; preserve the plan's immutable tuple and read-back requirements. |

## Preserved decisions and sprint boundary

Initialization is credited only to PR #686's exact approved fixture execution; any
new run needs its own decision. Keep adoption completion, fixture PR, final Phase 5
exit and cs-toolkit replay separate. The maintained parity plan owns the final replay's
immutable tuple and exit assertions; this assessment changes none of them.

TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the
[parked initializer issue proposal](codex-adopt-initialization-evidence_2026-09-06/init-compatibility-issue.md)
remain reserved. No tracker payload or friction graduation was executed. Phase 5 remains
in progress; Phase 6 remains not started. The next decision is the exact VER-02 trial above; original-fixture
ownership, registration and lens handling remain independently scoped.

## Reconciliation verification and wrap-up

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`61776212a2694108c5dfd8c2640c8b8ef08a40f4` plus the reconciliation record edits
on 2026-09-06 UTC passed lint and failed in
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
The [metadata](codex-adopt-verification-reconciliation-evidence_2026-09-06/make-test.json),
[terminal output](codex-adopt-verification-reconciliation-evidence_2026-09-06/make-test-output.json)
and command source retain the run and extended timeout. This is the recurring
assertion recorded by the preceding sessions, outside the changed paths. The run
preceded this paragraph, evidence copy and final proposal wording edits. It is kit
record verification, not VER-02 or adoption verification. The wrap-up PR carries
subsequent checks and review at its own head. No new tracker occurrence was posted.

## Prior kit verification and wrap-up — PR #687

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`e3c7b14ffb26e7ffac37e0be62ac02618d819c58` plus the review, plan and handoff edits
on 2026-09-06 UTC failed in
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`.
The [run metadata](codex-adopt-completion-review-evidence_2026-09-06/kit-test.json),
[terminal output](codex-adopt-completion-review-evidence_2026-09-06/kit-test-output.json)
and runner retain the actual result and extended timeout. This is the assertion
recorded in the preceding handoff, outside the changed paths. The run preceded this
verification paragraph and the final evidence copy; it is not VER-01's same-source
control or successful adoption verification.

Wrap-up updated the maintained sprint status and used `archive_plan_sessions.py
--target-lines 400` to move the oldest handoff block into history. The friction
inbox and initializer proposal were preserved. The wrap-up PR carries subsequent
CI and review evidence at its own head, with merge left to the operator.
