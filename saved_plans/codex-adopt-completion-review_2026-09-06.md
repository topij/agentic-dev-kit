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
`e3c7b14ffb26e7ffac37e0be62ac02618d819c58` on 2026-09-06 UTC and completed
successfully after correcting the inspection program's expectation that the
initializer had preserved `.gitignore`. The initializer's recorded ignore additions
are expected; that file is outside the pre-initialization input-equality assertion.
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
| Installed verification | The report enumerates the failed nodes from PR #686's retained terminal log and binds that log by digest. | The diagnostic proposal below precedes any test repair or completion disposition. |

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

Initializer failures also appear in the retained inventory; they remain outside this
selected diagnostic scope. The existing occurrence on #534 already records the
vendored-suite finding. This assessment adds no new run or tracker occurrence.

## Selected next action: VER-01 — same-source diagnostic control

**Proposed, awaiting an exact operator decision.** Authorize a diagnostic run only:

- Recheck the bound fixture, source SHA, retained post-init config, baseline and
  preserved inputs. If continuity differs, stop and present the difference.
- Create fresh disposable copies under a unique `/private/tmp/adk-adopt-control-*`
  directory: a flat kit checkout at the bound installed-source SHA, and a copy of
  the initialized fixture including its staged files and synthetic local overlay.
  Give the fixture copy its own Git metadata rooted at the bound baseline. Keep
  each copy free of an origin remote; retain a file-digest comparison to its input.
- Use the same explicitly resolved Python interpreter and dependency environment
  for each run. Record its version, argv, cwd, source/baseline SHA, input digests,
  isolated `DEVKIT_STATE_ROOT`, separate pytest `--basetemp`, timeout, terminal
  output and exit status. Run sequentially with `PYTHONDONTWRITEBYTECODE=1`.
- Run the exact nodes listed in the assessment table, using `scripts/tests/` in
  the flat control and `scripts/devkit/tests/` in the fixture copy. Do not deselect
  a failed node, insert replacement config/adapters/skeletons, or repair a test.
- Compare each observed outcome and trace. A setup refusal or skipped node is an
  unestablished control. Record unresolved explanations rather than interpreting
  every difference as a layout defect. Verify the original fixture remains unchanged.

This proposal authorizes neither initialization nor fixture ownership/registration/
lens writes. It does not authorize changes to kit tests or engines, adoption
completion, a fixture remote or PR, final Phase 5 exit, cs-toolkit replay, tracker
dispositions or archive graduation. Even a successful flat control is evidence only
for its named nodes; successful adoption verification remains a separate obligation.

## Preserved decisions and sprint boundary

Initialization is credited only to PR #686's exact approved fixture execution; any
new run needs its own decision. Keep adoption completion, fixture PR, final Phase 5
exit and cs-toolkit replay separate. The maintained parity plan owns the final replay's
immutable tuple and exit assertions; this assessment changes none of them.

TRI-03/TRI-04/TRI-05, #608/#255 dispositions and the
[parked initializer issue proposal](codex-adopt-initialization-evidence_2026-09-06/init-compatibility-issue.md)
remain reserved. No tracker payload or friction graduation was executed. Phase 5 remains
in progress; Phase 6 remains not started. The next decision is VER-01, followed by
an evidence-based choice of test repair scope and the separately approved fixture
ownership/registration/lens handling.

## Kit verification and wrap-up

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
