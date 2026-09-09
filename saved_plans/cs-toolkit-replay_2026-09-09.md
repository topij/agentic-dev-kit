# cs-toolkit replay — 2026-09-09

Phase 5 delivery item 6 was executed under [REPLAY-01 and its exact approval](cs-toolkit-replay-evidence_2026-09-09/approval.md). The replay verification at the bound refs succeeded with the disclosed original-checkout failure and operator-accepted #723 limitation. This does not complete Phase 5: item 5's later approved fixture and remaining verification are recorded in [ITEM5-B](phase5-item5-b-execution_2026-09-09.md). The initial #2222/#2223 pass is not credited again. REPLAY-01 initially held merges for the operator; the later authorization and delivery are recorded below.

## Bound upgrade and separate reconciliation

- Canonical adopter origin: `https://github.com/in-parallel-oy/cs-toolkit.git`.
- Adopter protected input: `bdeaf04f1ceed92570ddcd22281b659d5eb5cc80`.
- Prior kit baseline: `bde4c234eaa9005e90b987007101aba98281ce88`.
- Kit source and protected head: `e698ec47d6284ccd31af5ba9d8bc5657fe992310`.
- [Adopter PR #2255](https://github.com/in-parallel-oy/cs-toolkit/pull/2255), base `main`, head branch `chore/kit-upgrade-replay-20260909`, head `21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351`.

The PR refreshed the approved source files, ran `init.sh --no-clobber`, and recorded the install. The effective tracked config retained its typed mapping; initialization normalized quoting in `systemize.operator_logins`. The explicit declines in REPLAY-01 remain declined. Root forks, local doctrine, bindings and runtime registrations retain their approved ownership.

The [no-change stage](cs-toolkit-replay-evidence_2026-09-09/reconciliation.json) and its [invocation receipt](cs-toolkit-replay-evidence_2026-09-09/reconciliation-receipt.json) retain exact argv, output, input/output SHA, tree equality, clean status and preceding-upgrade linkage. No reconciliation PR was manufactured. An independent correctness assessment reviewed the fork diff and the shared/local instruction chain and concluded that no reconciliation hunk was required.

## Adopter condition and limits

The [verification result](cs-toolkit-replay-evidence_2026-09-09/verification-result.json) and [command receipt](cs-toolkit-replay-evidence_2026-09-09/verification-receipt.json) bind the destination checks and retained terminal test evidence to the immutable resulting head. [Test results](cs-toolkit-replay-evidence_2026-09-09/test-results.json) retain commands, directories, revisions, dates, actual summary lines and stdout digests.

At `21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351` on 2026-09-09 in `/Users/topi/Coding/in-parallel/cs-toolkit`:

- Upgrade Step 5's installed doctor, installed-test runner and document-budget command exited successfully. The [source doctor](cs-toolkit-replay-evidence_2026-09-09/source-doctor.json) confirms the exact kit baseline and declared unchanged/declined scope. The budget command reported the existing friction-inbox warning.
- `make check-root` printed `6090 passed in 452.39s (0:07:32)` after root lint. Scoped pre-commit checks exited successfully and destination status remained empty.
- `make test` exited with status 2 in support-docs, printing `2 failed, 859 passed in 44.95s`. Its Intercom inventory assertions scan ignored local artifacts. The [baseline-source probe](cs-toolkit-replay-evidence_2026-09-09/inventory-probe.json) reproduces those assertions from the unchanged original test source against the same artifact population. This is not kit #393. Raw output containing private artifact paths stays local.

Independent clone verification at the same SHA on 2026-09-09 completed `make test`, `make check-root` and `make test-devkit` successfully. The retained correctness-clone receipts name `/private/tmp/adopter-correctness-21fe33bb-UhJZNe/repo`; the separate adversarial pass reached the same command outcomes. These passing runs establish committed-source behavior, while the original checkout's artifact-dependent failure remains part of the record.

CodeRabbit found a non-object JSON defect in the imported `is_install_baseline` helper that the panel probes missed. The operator approved the exact [#723](https://github.com/topij/agentic-dev-kit/issues/723) payload and deferral on 2026-09-09. The declared installed test modules do not call that helper; the imported bytes remain unchanged. The [review record](cs-toolkit-replay-evidence_2026-09-09/review-record.md) also preserves the separate coverage limit: the installed suite survives suppression of the new unset diagnostic because doctor tests are declined. External behavioral probes killed that mutation; they are not installed-suite coverage.

## Reconciliation evidence matrix

The upstream endpoint diff is `git -C /private/tmp/agentic-dev-kit diff --exit-code bde4c234eaa9005e90b987007101aba98281ce88 e698ec47d6284ccd31af5ba9d8bc5657fe992310 -- scripts/dev_session.sh scripts/reconcile_sessions.sh`. The local-scope diff and destination hashes are in the no-change record. Each produced empty diff output on 2026-09-09. The independent assessment's N/A dispositions below refer to that empty hunk set; they do not invent coverage for code that changed elsewhere.

Exact passing nodes and the full test invocation are retained in [fork-test-nodes.json](cs-toolkit-replay-evidence_2026-09-09/fork-test-nodes.json), from `make test-root` with the recorded `PYTEST_ARGS` at the resulting head on 2026-09-09 in the original adopter checkout.

| Surface | Reviewed disposition and evidence |
|---|---|
| Upstream `dev_session.sh` | N/A: the pinned diff is empty. Existing descriptor and operator policy are exercised by `tests/test_dev_session_headless.py::test_headless_descriptor_carries_prompt_preamble_and_refuse_env` and `::test_self_merge_class_refuses_before_creating_a_session`. |
| Upstream `reconcile_sessions.sh` | N/A: the pinned diff is empty. `tests/test_reconcile_sessions.py::TestClassification::test_merge_ready_operator_pr_is_held_for_exit_4` and `::test_non_ready_operator_pr_remains_open_for_exit_3` exercise the retained local outcomes. |
| Adopter forks and runtime-neutral local policy | N/A: the replay scope changes neither fork nor local-policy file. `tests/test_review_receipt_integrity.py::test_merge_always_parks_before_invoking_gh_or_review_engine[operator]` and `::test_scope_adapter_forwards_shared_state_root_and_repo_identity` exercise operator authority and shared review state. |
| Refreshed headless declaration | N/A to the fork protocol: the shared declaration flows through the existing instruction chain. Local policy retains the legacy descriptor, declines the generic launcher, requires complete replacement of both root namespaces, and does not certify a Codex headless route. The declaration does not authorize a new launcher. |
| Claude/Codex bindings | The [adapter report](cs-toolkit-replay-evidence_2026-09-09/adapter-report.json) enumerates `kit-current` entries and no required binding missing. `tests/test_review_receipt_integrity.py::test_parallel_runtime_adapters_reach_the_shared_merge_override` and `::test_shared_parallel_policy_requires_descriptor_env_replacement` exercise their local-policy route. This is structural evidence, not a live runtime-load claim. |
| Hook-message and terminal-review doctrine | N/A to the fork engines: the upgrade imports the shared declarations. Hook presentation stays advisory; no fork protocol or merge authority is introduced. |

## Stable exit read-back

[Snapshot before verification](cs-toolkit-replay-evidence_2026-09-09/tuple-before.json) and [snapshot after verification](cs-toolkit-replay-evidence_2026-09-09/tuple-after.json) contain the authoritative origin, kit/adopter protected refs, resulting head, PR identity/base/head, ancestry and complete no-change stage. Their [capture receipts](cs-toolkit-replay-evidence_2026-09-09/tuple-before-receipt.json) and [exit read-back receipt](cs-toolkit-replay-evidence_2026-09-09/tuple-after-receipt.json) place verification between the reads.

`cmp -s` over those original snapshot files exited successfully on 2026-09-09 at the bound kit/adopter SHAs. The [comparison receipt](cs-toolkit-replay-evidence_2026-09-09/snapshot-comparison.json) records their byte identity and SHA256 `99c78b8409ce5b70aa23ff10cfc6c4ee93605d7d9934c7d911b6858658fa5918`. The capture rejects origin mismatch, source/protected mismatch, changed bound refs, PR retargeting, dirty trees and broken ancestry. The validator is agent-executed evidence, not a new automatic workflow gate.
Its executed source bytes and the capture/reconciliation probes are retained with
`.py.txt` suffixes as archival text; the invocation receipts name the original scratch scripts.

`uv run scripts/devkit/pr_watch.py 2255 --json` in the original adopter at `21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351` on 2026-09-09 reported `converged: true`, `mergeable: true` and `done: true`; the [poll](cs-toolkit-replay-evidence_2026-09-09/adopter-pr-watch.json) and [receipt](cs-toolkit-replay-evidence_2026-09-09/adopter-pr-watch-receipt.json) retain the observation. That observation preceded the operator’s subsequent merge authorization.

This kit wrap-up publishes the snapshots and stamped result before merge. Its own commit is not the replay source. Later ref movement is a separate event; it does not rewrite this observation or authorize a later merge without fresh checks.

## Subsequent delivery — 2026-09-09

After the exit read-back, the operator instructed `merge when clean`. A fresh
`uv run scripts/devkit/pr_watch.py 2255 --json --no-persist` in the original adopter
at `21fe33bb040e7fdcc8f7d3d7c4402e768b1ff351` on 2026-09-09 reported the exact head
mergeable. `gh pr merge` used `--squash` and pinned that exact SHA with
`--match-head-commit`;
`gh pr view 2255` read back `MERGED` with merge commit
`c4119f85e07f2a089ab8d5decc94cf2cd1635d14` at `2026-09-09T18:40:30Z`.
The [delivery event](cs-toolkit-replay-evidence_2026-09-09/delivery-events.json)
retains the authoritative response and the later authorization. The local adopter was
fast-forwarded to the merged main; its manifest bytes still match the reviewed head.

[Kit PR #724](https://github.com/topij/agentic-dev-kit/pull/724) publishes this ordinary
wrap-up and the replay snapshots. `gh pr view 724 --repo topij/agentic-dev-kit`
read back its merge as `8418118e40728c667c32a28a182697139bc7a5ef` on 2026-09-09.
This later delivery event leaves the replay snapshots unchanged.
The [initial kit panel receipt](https://github.com/topij/agentic-dev-kit/pull/724#issuecomment-5607067732)
was recorded at `9b63bc921533b2db19b05313ff2600ee9f1ffc52` before this later-event update.

## Operational limits and next action

A kit wrap-up branch-creation command used an explicit tool working directory but omitted the required pre-write `pwd` assertion. Read-back confirmed `chore/kit-replay-handoff-20260909` at `e698ec47d6284ccd31af5ba9d8bc5657fe992310`; subsequent record writes asserted the directory first and verified destination hashes. This lapse is recorded rather than claiming perfect procedure compliance.

The [fixture absence check](cs-toolkit-replay-evidence_2026-09-09/fixture-absence.json) retains the original missing paths; do not reconstruct them. The later [ITEM5-B execution](phase5-item5-b-execution_2026-09-09.md) supersedes this record's request to prepare an item 5 decision and owns the next action. #585's earlier placement is settled; its implementation is separate. #723 remains the accepted upstream follow-up.
