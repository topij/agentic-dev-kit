# Capability-matrix row audit — 2026-10-04

[#919](https://github.com/topij/agentic-dev-kit/issues/919)'s narrowed scope, as its
[2026-10-03 comment](https://github.com/topij/agentic-dev-kit/issues/919#issuecomment-5965698201)
states it: for each row of the
[capability matrix](../docs/agentic-dev-kit/runtime-parity.md#capability-matrix) that
cites no stamped live record, name the tests that pin its repository side, or record
that none does.

The tree was read at `7467c9b552b4eeb50dc9bab25ad69a5add89254d` (`main`) on 2026-10-04.
The tests and corrections this audit added are on the branch that carries this record,
and *Negative controls* below names the revision each was run against. A test is cited by
its node id, never a line number, so the citation survives an edit above it.

## What counts as evidence

The audit sorts every piece of evidence into one of three classes, and a row's claim is
only as established as the weakest class its clauses need.

- **Declaration consistency.** A test compares one text with another: a declaration with
  the files on disk, a workflow's declaration table with its expected ids, the shipped
  hook file with the doctor's literal. It establishes that two places agree. It does not
  establish that either describes behaviour.
- **Behavioural.** A test executes a shipped engine, script or installer and asserts an
  outcome. It establishes the engine's behaviour on the inputs the test supplies.
- **Runtime-observed.** A live record of a real client. No repository test can supply
  this. The on-demand smoke record
  ([`runtime-smoke_2026-10-02.md`](runtime-smoke_2026-10-02.md)) is an observation and not
  a promotion bundle, so it is cited as context only and promotes nothing.

`scripts/tests/test_runtime_parity_matrix.py` holds the table to its declaration: row
names, order, status terms and links. That is declaration consistency about the table
itself, and it establishes no row's claim; this audit does not count it as evidence for
any row.

Several rows describe workflows an agent executes from prose. For those, a test that
pins the prose establishes that the workflow document says it, not that an agent does it.
The audit names that limit wherever it applies rather than repeating it as a gap.

## Rows and their records

Two rows rest on stamped live records for their claims and are outside the narrowed
scope; they are named here so the scope is visible.

- *Safety-critical doctrine*: [`codex-safety-doctrine-live-validation_2026-08-24.md`](codex-safety-doctrine-live-validation_2026-08-24.md).
- *Headless lane isolation*: the records its
  [per-runtime sub-table](../docs/agentic-dev-kit/runtime-parity.md#headless-lane-isolation-per-runtime)
  links.

Five rows cite a stamped record for part of the claim and make repository-side claims
beside it. The audit covers their repository side:

- *Document-budget tripwire* and *PR follow-through*: the Codex lifecycle record
  [`codex-hooks-live-validation_2026-08-23.md`](codex-hooks-live-validation_2026-08-23.md).
- *Review fallback* and *Capability tiers*: the calibration record
  [`capability-tier-calibration-live-validation_2026-08-27.md`](capability-tier-calibration-live-validation_2026-08-27.md).
- *Command permissions*: the `#606`, `#627` and `#631` measurements and
  [`claude-sessionstart-matcher-live-validation_2026-08-29.md`](claude-sessionstart-matcher-live-validation_2026-08-29.md).

The remaining rows cite no record: *Repository instructions*, *Workflow adapters*,
*Fresh-install footprint*, *Runtime memory tripwire*, *Interactive hook-message
presentation*, *Post-merge integrations*, *Session-start and wrap-up integrations*,
*Triage integrations*, *Adapter upgrade* and *Drift inspection*.

## Findings that changed the matrix

Three claims were false or overstated at `7467c9b5`, and this change corrects them.

1. **Capability tiers: "advisory on both runtimes because no engine reads it".** False
   since `#913` (`947fca07`, 2026-10-02): `scripts/runtime_smoke.py` reads
   `models.runtime_mappings.codex.cheap` and `.claude.cheap` and applies them to its own
   probe sessions. `runtime_smoke.py` is repo-only in `KIT_OWNED`, so no engine an
   adopter receives reads the map, and the advisory status stands for adopters. The row,
   `workflows/parallel.md`, and the `models` comment in `config/dev-model.yaml` (with
   its fixture copy) now say "no shipped engine". `init.sh`'s emitted comment already said
   the kit carries the map through no engine, which holds for an adopter, and is unchanged.
   `test_init_sh.py::test_no_shipped_engine_reads_runtime_mappings` now holds the reader
   set.
2. **Adapter upgrade: "classifies exact current and prior rendered forms".** The renderer
   records one prior generation, template version 1. That generation reproduces every
   adapter the kit shipped at `2f2561f3^`, the parent of `#635`, which introduced the
   renderer: each declared adapter at that revision equals its version-1 render. Adapter
   text shipped before that revision does not match either render, so `/upgrade`
   classifies it `adopter-owned` and preserves it rather than refreshing it. That is the
   safe direction, but "prior rendered forms" overstated it, and the row now names the one
   generation. "Exact" was also dropped: `kit-current` compares after newline
   normalization, as `workflows/upgrade.md` already says.
3. ***Lifecycle validation boundary*: "objects printed by `init.sh`".** `init.sh` prints
   the command strings and states the event, matcher and timeout in prose. The handler
   `type` and the hook object's key set are held only by `kit_doctor`'s literal. The
   sentence now says the canonical objects are the doctor's, whose commands, event,
   matcher and timeout are the ones `init.sh` prints.

## Row by row

Each row lists the clause, the evidence, its class, and what stays unestablished.
"Added" marks a test this change contributes.

### Repository instructions

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| `AGENTS.md` is the shared contract and reaches every install | `test_adoption_fixtures.py::test_a_fresh_install_receives_the_declared_footprint`, with `test_removing_any_declared_file_fails` as its control | behavioural (`init.sh` in a temp repository) | Presence and rendering; content is pinned by the entry point's own tests. |
| `CLAUDE.md` imports it | The fresh-install fixture asserts the `@AGENTS.md` line; **added**: the same fixture asserts `init.sh`'s active-import predicate found a live import in the rendered file. **Added**: `test_init_sh.py::test_the_kits_own_claude_md_actively_imports_agents_md` for the kit's own root `CLAUDE.md`, which no test read beyond its marker line. `test_init_sh.py::test_an_inactive_agents_import_does_not_suppress_the_hint` and `test_an_active_agents_import_suppresses_the_hint` pin the predicate both ways | behavioural | That Claude Code loads the import is client behaviour. The 2026-10-02 smoke record observed it as context only. |
| Codex reads `AGENTS.md` directly | **Added**: the fresh-install fixture asserts no `AGENTS.override.md` anywhere in an install. `test_adoption_fixtures.py::test_an_undeclared_runtime_file_fails` already rejects an undeclared file under `.codex/` | behavioural (the repository ships nothing that would pre-empt the file) | That Codex reads it is client behaviour; the 2026-08-24 doctrine record observed the root item at its stamped client. Codex's handling of a large `AGENTS.md` is not established. |

### Workflow adapters

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| The declaration is authoritative | `test_portability.py::test_runtime_parity_contract_covers_workflows_and_adapters` (declared paths equal the globs, naming conventions, status vocabulary), with `test_runtime_parity_rejects_a_missing_or_stale_systemize_adapter` and `test_runtime_parity_rejects_missing_or_stale_bookend_adapter` as controls | declaration consistency | — |
| Each binding is the rendered thin adapter over its shared definition | `test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes`; `test_portability.py::test_adopt_upgrade_and_pr_watch_adapter_bodies_are_pinned_word_for_word`; the fresh-install fixture's rendered-adapter check | behavioural (renderer executed) and text pins | `runtime_adapters.WORKFLOW_SLUGS` is tied to the declaration only through both equalling the same globs. |
| The workflow is discoverable in each runtime | none in the repository | runtime only | Client behaviour; the smoke record's skill and command rows are context. |

### Fresh-install footprint

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| `other_runtime: installed`; every install receives both runtimes' declared adapters and surfaces, and nothing undeclared under `.claude/`, `.agents/`, `.codex/` | `test_adoption_fixtures.py::test_a_fresh_install_receives_the_declared_footprint` over Codex-only, Claude-only and dual-runtime adopters, with that module's negative controls | behavioural | The template route is simulated by copying `git ls-files`; only the non-interactive `init.sh` path runs; surfaces are compared with the kit's own copy, so a defect shared by both passes, as the fixture's docstring says. |
| `runtime.default` selects the session-start invocation | the fresh-install fixture's closing-line check | behavioural | The lane-launcher half of that sentence has no fixture assertion. |
| The other runtime's files are inert | none | runtime only | Definitional; not testable in the repository. |
| `/adopt` proposes both adapter sets and writes no hook registration | none beyond the workflow text | agent-executed prose | Unpinned. |

### Runtime memory tripwire

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| `check_memory_budget.py` checks Claude's `MEMORY.md` | `test_check_memory_budget.py` | behavioural | Claude's project-slug rule is assumed, not observed. |
| Never invoked on Codex | `test_init_sh.py::test_the_shipped_codex_session_start_carries_no_matcher` (SessionStart only); `test_kit_doctor.py::test_codex_rejects_the_claude_only_memory_tripwire` (exact canonical string only); **added**: `test_init_sh.py::test_no_shipped_codex_hook_names_the_claude_only_memory_engine`, every string in the shipped file under every event | declaration consistency over the shipped file | Before the added test, a `PostToolUse` handler naming the engine passed both existing tests. That a Codex client never runs it is client behaviour. |

### Interactive hook-message presentation

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| No required parity outcome depends on the display | **Added**: `test_pr_followup_hook.py::test_entrypoint_emits_scoped_read_only_policy_and_lifecycle_prerequisites` now asserts the hook's output has only `hookSpecificOutput`, holding only `hookEventName` and `additionalContext` | behavioural, for the one shipped JSON-emitting hook | The budget engines print plain stdout. The semantic claim, that no workflow outcome depends on what a client displays, is a decision on #608 and is not testable in the repository. |

### Document-budget tripwire (repository side)

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Codex: match-all `SessionStart`, bounded timeout | `test_init_sh.py::test_the_shipped_codex_session_start_carries_no_matcher`; `test_kit_doctor.py::test_codex_lifecycle_semantics_accept_the_shipped_contract`; `test_init_sh.py::test_the_budget_advisory_prints_the_shipped_codex_commands_verbatim` | declaration consistency, and the doctor executed on the shipped file | At `paths.engines: scripts` only, before this change. |
| The printed commands verify under a vendored engine directory | **Added**: `test_init_sh.py::test_the_codex_commands_printed_for_a_vendored_engine_dir_verify_in_the_doctor` runs `init.sh` with `paths.engines: scripts/devkit`, builds the hook file from what it printed, and requires the doctor to verify both lifecycle forms | behavioural | — |
| Repository semantics are deterministic | **Added**: `test_portability.py::test_doc_budget_cli_warns_without_blocking_and_blocks_only_under_strict` runs the engine as a hook does: exit 0 within and over budget, 1 only under `--strict`, 2 for a missing configured doc, silence under `--quiet` while within budget, and the `--json` shape. Previously only `render`, `evaluate` and the config-error exit were tested | behavioural | — |
| The supported trusted client ran the equivalent shape | the Codex lifecycle record | runtime-observed | That record's fixture commands differ from the shipped ones; no test ties its group shape to the shipped group. |

### PR follow-through (repository side)

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| The engine maps `--runtime` to that runtime's policy | `test_pr_followup_hook.py::test_entrypoint_emits_scoped_read_only_policy_and_lifecycle_prerequisites` and the module's `main`/config tests | behavioural | — |
| Claude `PostToolUse`, matcher `Bash`, `if: Bash(*)`; Codex `^Bash$`, bounded timeout | `test_init_sh.py` registration-shape tests over the shipped files; `test_kit_doctor.py::test_codex_lifecycle_semantics_accept_the_shipped_contract` | declaration consistency, and the doctor executed | The shipped Claude command is never executed with the real hook; the Codex command's execution tests swap the hook for a probe. |
| Hook definitions still require Codex review and trust | the Codex lifecycle record's trust sequence | runtime-observed | The advisory lines that tell an adopter so are unpinned. |

### Review fallback (repository side)

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| The engine validates parent/delta ancestry, exact heads, changed paths and pass caveats | `test_pr_watch.py::test_delta_paths_binds_real_git_ancestry_and_changed_paths`, `test_record_review_refuses_push_between_review_and_receipt`, `test_composition_refuses_a_parent_that_is_not_the_standing_receipt_head`, `test_composed_coverage_invalidates_when_recorded_paths_do_not_match_git`, `test_composed_coverage_preserves_and_renders_each_pass_caveat` | behavioural | — |
| Claude per-lens model and effort come from `.claude/agents/<lens>.md` rendered by `panel_prompt.py --agent-definition` | `test_panel_prompt.py::test_agent_definition_carries_the_configured_model_and_effort`, `test_the_committed_lens_definitions_are_what_the_generator_renders`; `test_kit_doctor.py` lens-definition inspection tests | behavioural | That the client applies them is the calibration record's. |
| Codex per-lens effort comes from the `codex exec` argv | the adapter text instructing it, pinned by `test_portability.py::test_adopt_upgrade_and_pr_watch_adapter_bodies_are_pinned_word_for_word` | declaration consistency over instructions | No shipped engine builds that argv; the cockpit does by hand. The repo-only smoke runner builds it, and its tests would not notice the effort flag dropped, because the fake client's default equals the configured level. |
| Classification, lens provenance and posted draw verdicts are instructed or self-reported | doctrine text; `test_pr_watch.py::test_the_poll_render_reports_the_receipt_as_a_CLAIM_not_a_verdict` | declaration | A claim that nothing enforces them; no test is owed. |

### Capability tiers (repository side)

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Per-key, per-runtime mechanical/advisory declarations | `test_init_sh.py::test_per_runtime_config_maps_declare_status_on_each_install_surface`, `test_both_runtime_mappings_comments_declare_the_status_per_runtime` | declaration consistency | Their docstrings say they check presence and vocabulary, not that a carrier applies a value. |
| Advisory because no shipped engine reads the map | **Added**: `test_init_sh.py::test_no_shipped_engine_reads_runtime_mappings` holds the reader set to `init.sh` (writer) and `scripts/runtime_smoke.py` (repo-only) | declaration consistency over engine sources | A name scan: a reader that builds the key from parts, or walks `models` without naming it, is not seen. |
| `lens_compute` is mechanical on both through different carriers | Claude: as in *Review fallback*. Codex: instructed argv | behavioural (Claude), instructed (Codex) | Codex's "mechanical" rests on the calibration record plus a cockpit following the adapter text. |
| Neither headless wrapper carries a control | `test_lane_launcher.py::test_each_declared_policy_reaches_the_child_argv_in_the_fixed_slot` (the launcher adds none, over fixture commands); **added**: `test_lane_launcher.py::test_shipped_headless_commands_carry_no_compute_control` over the shipped commands | behavioural, and declaration consistency over the shipped config | What a lane then runs at is client behaviour. |

### Command permissions (repository side)

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Claude lane profile under `--setting-sources ""`; Codex `--sandbox` from the engine vocabulary, shipped `read-only`; shipped Claude grants include `make test` and `kit_doctor.py` | `test_lane_launcher.py::test_shipped_config_declares_a_bounded_policy_and_the_shipped_profile_validates` and the policy-slot test | behavioural over the shipped config | That the client loads only that profile is the `#606`/`#627` measurements'. |
| `init.sh` prints the cockpit allow-list templated on `paths.engines` | `test_init_sh.py::test_the_permissions_advisory_names_the_configured_engine_dir`, `test_the_permissions_advisory_prints_the_shipped_allow_rules_verbatim` | behavioural | Print-never-write is not asserted for this block. |
| `kit_doctor` reports an unreached engine `ungranted`, reads both settings files, never fails on it | `test_kit_doctor.py::test_an_allow_rule_naming_the_wrong_engine_dir_is_reported_ungranted`, `test_a_grant_in_the_local_overlay_covers_the_tracked_settings`, `test_an_ungranted_permission_does_not_fail_the_run` | behavioural | The last asserts the inputs to the exit code, not the exit code. |
| `SessionStart` matcher dropped on both runtimes | `test_init_sh.py::test_the_shipped_claude_session_start_carries_no_matcher` and its Codex sibling | declaration consistency | The Codex advisory-prose test would also pass on an `omit matcher` that only the Claude line kept. |
| Codex cockpit: no shipped project rules | none | — | Unpinned; nothing ships under `.codex/` but `hooks.json`, which the fresh-install fixture's undeclared-file check would catch if that changed. |

### Post-merge integrations

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Forge read and config are required | `test_systemize_engines.py::test_a_failed_or_truncated_page_stops_without_writing`; `test_systemize_artifacts.py::test_forge_timeout_is_bound_and_fail_closed`; `test_systemize_config.py::test_a_missing_required_key_is_named`; `test_portability.py::test_post_merge_systemize_required_and_degraded_preflights_are_discriminating` | behavioural (engine-backed mode) and declaration | In LLM-only mode the read is agent-executed. |
| The engine set is atomic | `test_systemize_config.py::test_a_partial_engine_set_stops`; `test_systemize_engines.py::test_every_entry_point_refuses_a_partial_engine_set` | behavioural | — |
| Notification and tracker creation degrade or fail closed; the tracker is payload-approval-gated | `test_portability.py::test_post_merge_systemize_required_and_degraded_preflights_are_discriminating`, `test_post_merge_systemize_semantic_mutations_are_rejected` | declaration | No engine sends or files; agent-executed. |
| Reviewer access degrades or fails closed | none | — | The workflow's *Configured reviewer* row is pinned by no test. |
| LLM-only mode when the engine set is absent | `test_systemize_config.py::test_heartbeat_keys_are_required_only_engine_backed` (mode selection) | behavioural for selection | The run itself is agent-executed. |

### Session-start and wrap-up integrations

Almost every clause is pinned as declaration consistency only, by
`test_portability.py::test_bookend_integrations_are_shared_thin_declared_and_manifested`
and `test_bookend_integration_semantic_mutations_are_rejected`. Both workflows are
agent-executed. The behavioural coverage is the engines they call:

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| PR readiness uses unfiltered review evidence | `test_pr_watch.py::test_all_comments_reports_what_seen_noise_and_empty_bodies_hide`, `test_all_comments_through_main_is_read_only`, `test_truncation_is_reported_in_the_json_and_the_render` | behavioural (engine) | That the agent judges from it is prose. |
| Isolated review and self-merge go through the paired lane wrappers and shared state sandbox | `test_portability.py::test_scope_pr_watch_and_merge_share_lane_state_and_pinned_repo`, `test_operator_merge_class_refuses_before_contacting_github` | behavioural (wrapper) | `evidence`-marked, so `make test-fast` skips them. |
| Merge authority holds the exact reviewed head | `test_portability.py::test_self_merge_refuses_when_identity_read_and_review_poll_disagree_on_head`; **added**: the wrapper test now asserts the merge call carries `--match-head-commit` with the validated head | behavioural | Before the addition, the merge call was matched by substring, and dropping `--match-head-commit` from `dev_session.sh` passed. |
| Detached HEAD, unverified resolution labels, conditionals at their trigger, exact-payload decisions, forge path for every artifact, terminal precedence, tracker-only success, policy-less non-lane PRs | the declaration tests above | declaration | Agent-executed; no engine. |

### Triage integrations

Coverage is extensive and largely behavioural: `run()` in `scripts/lib/triage/engine.py`
executes against fake trackers and forges.

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Merged config and frozen state are required | `test_triage_config.py::test_malformed_or_colliding_config_stops_before_artifact_resolution`; `test_triage_engine.py::test_resume_refuses_invalid_published_frozen_artifact_before_tracker_write` | behavioural | No triage test sets a `dev-model.local.yaml` value and reads it back through `load_settings`. |
| The draft/finalize pair is atomic; LLM-only when both are absent | `test_triage_config.py::test_partial_engine_set_is_rejected` | behavioural, one direction | The draft-absent direction and LLM-only selection are untested. |
| Unattended approval requires notification send and thread read | `test_triage_inputs.py::test_unattended_nonempty_new_without_notification_capability_creates_no_session_artifacts`; `test_triage_engine.py::test_unattended_initial_and_single_reminder_require_provider_readback` | behavioural | — |
| Exact-payload approval, pre-attempt state, destination read-back | `test_triage_approval.py::test_approval_requires_exact_operator_and_readback`; `test_triage_engine.py::test_live_attempt_is_persisted_before_fake_create`, `test_tracker_dispatch_process_loss_recovers_gate_and_reconciles_without_duplicate_create`; `test_triage_providers.py` read-back tests | behavioural | — |
| Accounted, byte-identical sweep sets prevent partial-batch loss | `test_finalize_triage.py::test_sweep_set_is_union_of_verified_filed_and_explicit_archive_decisions`; **added**: `test_sweep_set_refuses_a_filed_decision_without_a_verified_operation` | behavioural | Before the addition only the accounted case ran, and deleting the refusal in `sweep_ids` passed. |
| Test mode cannot touch tracker or source/forge state | `test_triage_engine.py::test_test_mode_completes_without_external_provider`; **added**: `test_test_mode_writes_nothing_through_providers_it_is_handed`, with a creating tracker and a forge supplied and finalization requested | behavioural | — |
| Unresolved paths stay operator-held | `test_finalize_triage.py::test_unsettled_merge_is_retained_and_retried_without_a_merge_call`; `test_triage_recovery.py::test_state_with_unproven_attempts_becomes_terminal_held` | behavioural | — |

### Adapter upgrade

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| The current and the one recorded prior form classify separately from authored bytes | `test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes`, `test_authored_adapter_change_is_reported_and_preserved_for_each_runtime`, `test_previous_generated_codex_adapter_is_refreshable_not_adopter_owned` | behavioural (classifier) | The legacy-body hashes are checked against the bytes shipped at `2f2561f3^`. Older generated forms read as adopter-owned; see *Findings*. |
| `/upgrade` runs the fetched kit's classifier, installs missing bindings and refreshes stale ones | `test_kit_doctor.py::test_adapter_report_cli_is_read_only_and_does_not_require_adopter_config`, `test_adapter_report_refuses_a_source_adapter_the_renderer_does_not_own` | behavioural (report only) | The report never writes; the install/refresh/preserve mapping is agent-executed prose in `workflows/upgrade.md`, unpinned. |
| Adapter ownership never enters the drift gate | `test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes` (no `KIT_OWNED` path under `.claude/` or `.agents/`), `test_adapter_report_refuses_drift_and_write_options` | declaration consistency and CLI separation | No default-mode doctor run shows an adapter edit leaves the gate unchanged. |

### Drift inspection

| Clause | Evidence | Class | Limits and gaps |
|---|---|---|---|
| Claude registration paths resolved; `permissions.allow` coverage against the configured engine path | `test_kit_doctor.py` registration and permission-coverage tests (see *Command permissions*) | behavioural | — |
| Lens definitions compared with the running doctor's output; generator drift stays on the file axis | `test_kit_doctor.py::test_lens_definition_inspection_reports_missing_current_and_stale`, `test_a_configured_compute_change_makes_the_definition_stale`, `test_lens_inspection_does_not_execute_the_adopter_generator` | behavioural | Several are `evidence`-marked. |
| Codex: merged project hook sources, enablement aliases, structure for exact strings only | `test_kit_doctor.py` Codex lifecycle tests | behavioural | — |
| No adopter-owned generated lens surface on Codex | `test_panel_prompt.py::test_agent_definition_is_a_claude_surface_and_refuses_codex` | behavioural | — |

## Negative controls

Every mutation was applied twice, each time to a fresh `git clone --no-hardlinks` of
this repository: once detached at `b309bb8ae4aaa0729df569014032e16830cf1504`, the commit
that adds the tests, and once at `7467c9b552b4eeb50dc9bab25ad69a5add89254d`, before
them. A script applied each edit after asserting it matched exactly once, and
`git diff --stat` read it back. Both sides ran
`uv run --with pytest --with pyyaml pytest -q -p no:cacheprovider -m 'not driftcheck'`
with `DEVKIT_STATE_ROOT` and `--basetemp` under the session scratchpad, on 2026-10-04.
`not driftcheck` keeps the manifest self-check from failing on every byte change, as
`make mutation-test` does. The added test ran at `b309bb8`. At `7467c9b`, the run took
the whole test modules that exercise the mutated file, named in the last column, not
the whole suite.

| Mutation | Added test at `b309bb8` | Modules at `7467c9b` |
|---|---|---|
| `check_doc_budget.py` returns 1 whenever a doc is over budget, `--strict` or not | `test_doc_budget_cli_warns_without_blocking_and_blocks_only_under_strict`: `1 failed` | `test_portability.py`, `test_kitconfig.py`, `test_init_sh.py`, `test_check_memory_budget.py`: `1111 passed` |
| `check_doc_budget.py`'s `render` prints within-budget docs under `--quiet` | the same test: `1 failed` | the same modules: `1111 passed` |
| a `PostToolUse` handler running `check_memory_budget.py` added to `.codex/hooks.json` and its fixture copy | `test_no_shipped_codex_hook_names_the_claude_only_memory_engine`: `1 failed` | `test_init_sh.py`, `test_kit_doctor.py`: `887 passed, 1 deselected` |
| `pr_followup_hook.py` adds a `systemMessage` beside `hookSpecificOutput` | `test_entrypoint_emits_scoped_read_only_policy_and_lifecycle_prerequisites`: `20 failed` | `test_pr_followup_hook.py`, `test_init_sh.py`: `503 passed` |
| `parallel.claude_headless_command` gains `--model opus`, config and fixture alike | `test_shipped_headless_commands_carry_no_compute_control`: `1 failed` | `test_lane_launcher.py`, `test_init_sh.py`: `584 passed` |
| `kit_doctor.py` gains a `models.runtime_mappings` key read | `test_no_shipped_engine_reads_runtime_mappings`: `1 failed` | `test_init_sh.py`, `test_kit_doctor.py`: `887 passed, 1 deselected` |
| `dev_session.sh merge` drops `--match-head-commit "$validated_head"` | `test_scope_pr_watch_and_merge_share_lane_state_and_pinned_repo`: `1 failed` | `test_portability.py`, `test_lane_launcher.py`: `892 passed, 2 warnings` |
| `sweep_ids` loses its unaccounted-batch refusal | `test_sweep_set_refuses_a_filed_decision_without_a_verified_operation`: `3 failed` | `test_finalize_triage.py`, `test_triage_engine.py`, `test_triage_recovery.py`: `270 passed` |
| triage test mode renders only when no tracker is supplied | `test_test_mode_writes_nothing_through_providers_it_is_handed`: `1 failed` | `test_triage_engine.py`, `test_finalize_triage.py`, `test_triage_inputs.py`: `279 passed` |
| `docs/templates/CLAUDE.md.tmpl`'s comment closes below `@AGENTS.md` | `test_a_fresh_install_receives_the_declared_footprint`: `3 failed` | `test_adoption_fixtures.py`, `test_init_sh.py`: `373 passed` |
| the kit's root `CLAUDE.md` fences its `@AGENTS.md` | `test_the_kits_own_claude_md_actively_imports_agents_md`: `1 failed` | `test_init_sh.py`, `test_adoption_fixtures.py`: `373 passed` |
| a tracked root `AGENTS.override.md` | `test_a_fresh_install_receives_the_declared_footprint`: `3 failed` | `test_adoption_fixtures.py`, `test_kit_doctor.py`: `566 passed, 1 deselected` |
| `kit_doctor.py` hard-codes `scripts/` in the canonical doc-budget command | `test_the_codex_commands_printed_for_a_vendored_engine_dir_verify_in_the_doctor`: `1 failed` | `test_init_sh.py`, `test_kit_doctor.py`: `887 passed, 1 deselected` |

Each failure was the added test or the assertion this change added to an existing one.
No module run at `7467c9b` caught any of these mutations.

## What stays unestablished

No repository test can establish these; each is client behaviour or an agent following
prose:

- that either client loads its entry point, discovers its adapters, fires a hook, or
  honours a timeout, trust step or settings source — the cited records cover what they
  cover at their stamped clients, and the smoke record is context only;
- that an agent executing *session-start*, *wrap-up*, *post-merge-systemize*,
  *triage-friction-log*, `/adopt` or `/upgrade` does what the prose declares;
- that a Codex cockpit applies `lens_compute` through the `codex exec` argv;
- that no workflow outcome depends on what a client displays.

Gaps a bounded repository test could still close, left for follow-up rather than
widened into this change: the workflow's *Configured reviewer* row in
`post-merge-systemize.md`; the draft-absent direction and LLM-only selection of the
triage engine set; triage settings through the local overlay; the advisory lines that
tell an adopter Codex needs trust; print-never-write for the permissions block; the
smoke runner's effort carrier; a default-mode doctor run showing an adapter edit leaves
the drift gate unchanged.
