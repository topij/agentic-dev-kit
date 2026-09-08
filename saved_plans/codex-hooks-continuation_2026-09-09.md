# Codex hooks continuation — 2026-09-09

This continues the [parked batch](codex-hooks-batch_2026-09-07.md) after the
doctor correction landed. The operator authorized the remaining live checks;
the earlier discovery and tracker dispositions were not repeated as new work.

## Observation bindings

The commands retained in
[capture provenance](codex-hooks-continuation-evidence_2026-09-09/capture-provenance.json)
ran from kit revision `144bc7f55ac7d98988acb4c4691f017ccbbb43f8` on
2026-09-08 UTC, with the desktop task finishing on 2026-09-09 in Europe/Helsinki.
The kit cwd was `/Users/topi/Coding/agentic-dev-kit`; individual invocation
records identify the disposable cwd where it differed.

The fixture input was `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` plus the
[post-REG-01 payloads](adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json).
The comparison source was `ab0a6d62308b298478b2f85fc961f14348f35365`, against
[its retained baseline](codex-adopt-ver02-evidence_2026-09-06/source-input-inventory.json).
[Setup](codex-hooks-continuation-evidence_2026-09-09/setup.json) and
[restoration audits](codex-hooks-continuation-evidence_2026-09-09/final-audit.json)
retain the comparisons. Neither original was rebuilt or used for instrumentation.

## Live client observations

The CLI launches used `script -q <capture> env CODEX_HOME=<private-state>
TERM=xterm-256color codex --cd <disposable-fixture> --no-alt-screen`.
The private user configuration omitted hooks feature settings; the unset fixture
omitted `.codex/config.toml`, and the disabled fixture set `[features].hooks = false`.
`/debug-config` identified the private layers and reported no requirements.
Its project-layer listing alone does not establish that an absent file exists.

| Case and live surface | Observation at the bound run | Evidence |
|---|---|---|
| CLI unset, `/hooks`, then trust | PostToolUse and SessionStart changed from Installed 1 / Active 0 / Review 1 to Installed 1 / Active 1. | [Exact terminal excerpts](codex-hooks-continuation-evidence_2026-09-09/cli-hooks-excerpts.txt) |
| CLI unset, fresh launch and `pwd` after trust | `/hooks` retained active definitions; entry logging reached the installed document-budget and PR-follow-up engines. | [Engine entries](codex-hooks-continuation-evidence_2026-09-09/engine-entries.jsonl), [command events](codex-hooks-continuation-evidence_2026-09-09/cli-command-events.json) |
| CLI explicit false, `/hooks` and `pwd` | Both event rows displayed Installed 0 / Active 0; the turn completed without a disabled-copy engine entry. | [Terminal excerpts](codex-hooks-continuation-evidence_2026-09-09/cli-hooks-excerpts.txt), [command events](codex-hooks-continuation-evidence_2026-09-09/cli-command-events.json) |
| Desktop unset, Settings → Hooks, trust, then a fresh local `pwd` task | The operator's view showed the disposable PostToolUse and SessionStart switches on with Trust prompts absent. The task reached both installed engines. | [Operator capture](codex-hooks-continuation-evidence_2026-09-09/desktop-fixture-after-trust.png), [execution record](codex-hooks-continuation-evidence_2026-09-09/desktop-execution.json), [command events](codex-hooks-continuation-evidence_2026-09-09/desktop-command-events.json) |

The desktop execution record binds the task to the disposable cwd and records
`originator: Codex Desktop`, runtime `0.153.4`, and the installed app's
`com.openai.codex` identity, version `26.901.51231`, build `8109`, from the
recorded rollout/`plistlib` inspection at the kit revision and observation time
above. The database's `source: vscode` is retained verbatim; it is not evidence
that this task ran in the VS Code UI.

Settings → Hooks was the observed desktop surface. The desktop composer did
not offer the CLI's `/hooks` command. This desktop observation agrees with the
CLI's unset behavior for the fixture; it does not establish a default shared by
every Codex client. The explicit-false observation is CLI-only.

## Trust, configuration and execution boundaries

Earlier GUI attempts did not establish the intended private-profile observation.
The operator then explicitly approved temporarily removing only `hooks = true`
from `/Users/topi/.codex/config.toml`, using the ordinary desktop window for a
fresh local disposable-fixture task, and restoring the setting afterward.
The [apply record](codex-hooks-continuation-evidence_2026-09-09/desktop-normal-config-apply.json),
[config inspection](codex-hooks-continuation-evidence_2026-09-09/desktop-normal-unset-preflight.json),
[pre-task observation](codex-hooks-continuation-evidence_2026-09-09/desktop-after-trust-pre-task.json)
and [restoration record](codex-hooks-continuation-evidence_2026-09-09/desktop-normal-config-restore.json)
retain that amendment and its application. Restoration preserved unrelated
concurrent edits, including the operator's trust changes. Existing user hooks
were present in this ordinary profile; the recorded engine entries identify the
disposable project paths.

The [CLI instrumentation](codex-hooks-continuation-evidence_2026-09-09/instrumentation.json)
and [desktop instrumentation](codex-hooks-continuation-evidence_2026-09-09/desktop-instrumentation.json)
inserted entry logging into the installed engines after their future imports.
Registration bytes, hook command strings, input handling and normal output were
retained. The loggers were not invoked manually. These observations establish
reaching the actual engine bodies after trust, not every downstream semantic
effect or successful completion of arbitrary hooks. An earlier PATH observer
produced no entry and is not used as evidence of nonexecution.

The [desktop cleanup record](codex-hooks-continuation-evidence_2026-09-09/desktop-cleanup.json)
retains engine restoration, original-tree continuity and private credential
cleanup. The disposable desktop project and its task remain available in the app;
they are not an adoption completion or a fixture PR.

## Doctor correction in the field

The current external inspector ran `python3 scripts/kit_doctor.py --root <copy>
--manifest <preserved-source>/kit-manifest.json` at the kit revision/date above;
the linked records retain absolute argv and cwd. It inspected the installed
fixture without upgrading its engines.

| Switch | Structured state and text | Exit | Invocation record |
|---|---|---|---|
| Unset | `unset`, advisory `·` | 0 | [Unset](codex-hooks-continuation-evidence_2026-09-09/doctor-unset.json) |
| Explicit false | `misconfigured`, disabled by project config | 1 | [Disabled](codex-hooks-continuation-evidence_2026-09-09/doctor-disabled.json) |
| Explicit true | No feature warning | 0 | [Enabled](codex-hooks-continuation-evidence_2026-09-09/doctor-enabled.json) |

The [structured registration observations](codex-hooks-continuation-evidence_2026-09-09/doctor-structured-registration-observations.json)
retain the separately invoked JSON results. These runs showed no divergence from
the requested correction on #698. Static doctor output supplies none of the
live-client conclusions above. No observation was reposted to #698, and the
earlier #608/#255 dispositions were not repeated.

## Verification and retained decisions

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`144bc7f55ac7d98988acb4c4691f017ccbbb43f8` on 2026-09-08 printed pytest's own
summary: `1 failed, 2484 passed, 1 skipped in 445.62s (0:07:25)`.
The [log](codex-hooks-continuation-evidence_2026-09-09/make-test-full.log) names
`test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`,
the pre-existing intermittent failure identified by the operator and #393.
The recording PR carries its own verification and independent-review receipts.

Phase 5 exit, the cs-toolkit replay, new initialization, adoption completion and
the fixture PR retain their own exact decisions. The prose-claims rule and
friction triage remain with Claude/the operator. Future fixture execution must
recheck the original trees and stop if either has expired; the retained
[stat observation](codex-hooks-continuation-evidence_2026-09-09/expiry-observation.json)
is scheduling evidence, not a promise that temporary children survive.
