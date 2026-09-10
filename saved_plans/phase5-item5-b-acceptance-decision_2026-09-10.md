# ITEM5-B preserved-file acceptance and field-exit decision

**Prepared, not approved.** `ITEM5-B-ACCEPT-01` and `ITEM5-B-PR-01` below are
separate operator decisions. Preparation and this kit record are authorized;
neither decision is inferred from ITEM5-B-UPDATE-01, whose approval is consumed.
The recommendation is to accept the named preservation outcomes, then take the
bounded fixture PR route if the operator wants to finish the adoption lifecycle.
Neither decision completes Phase 5 item 5 or the untested systemize routes.

## Bound evidence and delivery

```sh
COCKPIT=/Users/topi/Coding/agentic-dev-kit
REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture
KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source
```

The fixture input is `413132b01d14c735d94753231bf325904135285f` on
`chore/item5-b-update-60fe0dc`. The source remains detached at
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`. The required fixture baseline hash is
`9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126`.

The [forge readback](phase5-item5-b-acceptance-evidence_2026-09-10/forge-readback.json)
records `gh pr view 728 --repo topij/agentic-dev-kit` and the exact comment API
read in `$COCKPIT` at `b80fe9905c0f8dc303aae38c77aa822129e1760d` on 2026-09-10.
It confirms merge `b80fe9905c0f8dc303aae38c77aa822129e1760d` and reviewed head
`a14322d3358b07a7477550b7a7c2bb16caef27d5`. The complete
[final review receipt](https://github.com/topij/agentic-dev-kit/pull/728#issuecomment-5618460675)
is retained [verbatim as JSON](phase5-item5-b-acceptance-evidence_2026-09-10/pr728-final-receipt.json).
It reports the independent adversarial/correctness panel and its source-suite failures,
evidence audits, behavioral probes, restoration checks and limitations. It does not
report a new installed-suite run, client exercise, executed rollback or completed adoption.
The audit below also compares the merge and reviewed Git tree objects for equality.

`python3 -B /Users/topi/Coding/agentic-dev-kit/saved_plans/phase5-item5-b-acceptance-audit_2026-09-10.py.txt`
ran in `$COCKPIT` at `32ba74b74e2b1b59e5e4510246a9d02f310633c3`, with the
optimization-refusal fix in the working tree, on 2026-09-10. The
[result](phase5-item5-b-acceptance-audit_2026-09-10.json) reports equality to the
update's **FINAL** evidence. The earlier observation at
`b80fe9905c0f8dc303aae38c77aa822129e1760d` remains byte-preserved as the
[initial result](phase5-item5-b-acceptance-evidence_2026-09-10/initial-audit-result.json)
and [initial program](phase5-item5-b-acceptance-evidence_2026-09-10/initial-audit-program.py.txt);
that archived program is historical evidence, not the current check.

The [review receipt](https://github.com/topij/agentic-dev-kit/pull/729#issuecomment-5619355511)
was recorded before the fix. Its adversarial P2 demonstrated that `PYTHONOPTIMIZE`
could suppress the audit's assertions. The current program unconditionally refuses
optimized execution before inspecting inputs. [Exact refusal checks](phase5-item5-b-acceptance-evidence_2026-09-10/optimization-refusal-checks.json)
retain the command, revision, program hash, date, status and output for environment
and CLI optimization routes. The [synthetic behavioral check](phase5-item5-b-acceptance-evidence_2026-09-10/optimization-behavioral-probe.json)
uses the review-authored harness with synthetic roots: normal equality succeeds,
changed inputs refuse, and optimized runs refuse. Removing the new refusal in a
scratch copy reproduces the unauthorized-file acceptance; the retained diff and
restoration check bind that observation. This new audit defect is separate from #393
and from the retained update's verification. The audit checks:

- Full non-Git inventories, including file hashes, directories, symlink targets and
  `stat.S_IMODE` permission bits, before and after its reads.
- Branch/detached identity, HEAD bytes, refs, status, remotes, index/config hashes and
  independent `.git` directories against the final Git records.
- Each preserved destination's bytes, mode and regular-file/single-link shape; complete
  tracked and merged configuration through the installed reader, retaining scalar types.
- Setup, repair and update evidence ledgers, the external update artifacts including
  byte archives/Git bundles, baseline bytes and recorded item 6 replay evidence.

This is checkpoint evidence, not proof against transient writes between observations,
every Git administrative mutation, or runtime behavior. The audit does not execute the
historical update/pre-update drivers. Their original-revision assertions are expected
to refuse after the update and must not be used as current checks.

The same audit checked existence and dangling-symlink presence at these original paths
and found them absent; neither was reconstructed:

- `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`
- `/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source`

## ITEM5-B-ACCEPT-01 — exact ownership decisions

Approve the following interpretations of the bytes in the audit's `preserved_files`
map. That map supplies the complete absolute destinations, hashes and modes; approval
is bound to it, not to whichever bytes a future checkout happens to contain. Acceptance
means the operator wants to keep this fixture behavior and ownership. It does not
transfer ownership to the kit or assert that a client exercised the file.

| Fixture path | Recorded handling and proposed acceptance |
|---|---|
| `AGENTS.md` | The initializer left the fixture policy in use. Accept its markerless fixture-specific policy; do not replace it with the kit's policy or restore the removed ownership marker. It is intentionally minimal and supplies no additional safety doctrine by itself. |
| `CLAUDE.md` | Left in use. Accept its `@AGENTS.md` import as the common policy route. Import text is not evidence of a new Claude client loading it. |
| `ROADMAP.md` | Left in use. Accept the existing fixture roadmap at `paths.handoff`; it is a preservation fixture, not a populated project plan. |
| `notes/history.md` | Left in use. Accept the existing fixture history at `paths.handoff_history`; do not overwrite it with the source narrative. |
| `notes/friction.md` | Seeded by the approved initializer. Accept its configured ownership and location, but its example entry is not an adoption-friction record. PR-01 below separately proposes replacing that example with the exact supplied record. |
| `notes/friction-archive.md` | Seeded. Accept the archive skeleton and configured link destination; no archival workflow has been exercised. |
| `config/dev-model.yaml` | Accept the full tracked mapping: fixture name, `scripts/devkit`, fixture narrative paths, Codex default, disabled tracker/notification backends, configured review/lane policy and budgets. No migration or key change is proposed. In particular `review.require_ci` remains `true`. |
| `config/dev-model.local.yaml` | Accept the ignored differing `notify.user_key` override. The installed reader establishes its merged value and type. `notify.backend: none` means this value does not establish a working notification route. Keep it local and out of the PR. |
| `config/claude-lane-settings.json` | Seeded, thereafter adopter-owned safety-critical policy. Accept the enumerated task-scoping grants and merge/force-push denials as this fixture's policy. Do not claim hostile-code containment or change it during a client test. |
| `.claude/agents/adversarial.md` | Seeded. Accept the generated definition and its mechanical compute carrier as rendered bytes, with local ownership after seeding. The doctor comparison does not prove a client loaded it. |
| `.claude/agents/correctness.md` | Same ownership decision, independently bound to its own hash and renderer result. |
| `.agents/skills/wrap-up/SKILL.md` | Preserve the authored collision fixture. Its complete body says `Preserve this adapter.` It is deliberately not a usable implementation of the shared wrap-up workflow. Accept ownership preservation only; do not credit wrap-up functionality or invoke it expecting the shared workflow. Any functional replacement needs a separate exact payload decision. |
| `.codex/hooks.json` | Accept the applied REG-01 SessionStart and PostToolUse registrations resolving under `scripts/devkit`; no Codex memory-hook registration is added. Canonical structure and resolution do not establish discovery, trust or execution in this new fixture. |
| `.codex/config.toml` | Accept the local `features.hooks = true` declaration. It does not establish the effective stack, a fresh client's trust decision, or defaults in other clients. |
| `.claude/settings.json` | Accept the applied REG-01 registrations and listed cockpit permission grants. This is adopter configuration, not a kit-owned byte-refresh target or an observation of applied client permissions. |
| `.gitignore` | Accept the initializer's ignored overlay, state, reports, lane-worktree and temporary-file paths. Preserve exact bytes; no broad ignore expansion. |
| `.git/hooks/pre-push` | Accept the executable installed shim targeting `scripts/devkit/hooks/pre-push`. It is local Git metadata and will not travel through a PR; the remote clone's hook installation is not established. |
| `init.sh` | Preserve the executable staged installer, whose ownership differs from the adopter policy it seeds. Accept its current bytes as the retained installer; this does not authorize running it again. |

The remaining generated Claude/Codex bindings retain the classifications enumerated in
the [adapter report](phase5-item5-b-update-evidence_2026-09-10/source-adapter-report.stdout.log).
Kit engines, tests, helpers, controlled test inputs, workflow documents and registration
references remain upstream-managed in their installed locations. The whole FINAL
inventory binds them; there is no mass refresh. The install baseline's `adopter_owned`
list is a recorder classification, not a complete enumeration of every local policy
file. Repo-only omissions remain as recorded; `not_installed: []` does not claim a
complete kit-source checkout because repo-only paths are outside that installation set.

**Acceptance writes:** only append the operator's exact decision and audit binding to
this kit decision record, update the maintained sprint/handoff accordingly, and complete
the scoped kit PR lifecycle. Fixture/source payloads, their Git state and baseline have
no writes under ACCEPT-01. If any row is declined, retain the existing bytes and prepare
the replacement diff before seeking its decision; acceptance does not imply deletion.

## What existing verification establishes

The [update execution](phase5-item5-b-update-execution_2026-09-10.md) owns the
commands and complete logs, with [argv/cwd/environment records](phase5-item5-b-update-evidence_2026-09-10/verification-commands.json).
The observations below are from 2026-09-10, fixture `$REPO` at
`413132b01d14c735d94753231bf325904135285f` and source `$KIT` at
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`:

| Command; directory | Actual result and boundary |
|---|---|
| `python3 -B "$REPO/scripts/devkit/kit_doctor.py" --root "$REPO" --manifest "$KIT/kit-manifest.json" --json`; `$REPO` | Exit `0`: independent source-manifest comparison, declared scope, baseline pin, dependencies, canonical registration paths and expected lens bytes. It does not accept retained prose or prove client behavior. |
| `python3 -B "$KIT/scripts/kit_doctor.py" --root "$REPO" --adapter-report --adapter-source "$KIT" --json`; `$REPO` | Exit `0`: generated bindings compared with the pinned renderer; the custom Codex wrap-up reports `adopter-owned`. Ownership classification does not certify that custom adapter's function. |
| `python3 -B "$REPO/scripts/devkit/check_doc_budget.py"`; `$REPO` | Exit `0`: the configured documents were checked. Budgets do not validate prose or prove an archive operation. |
| `uv run --with pytest --with pyyaml python -B "$REPO/scripts/devkit/run_installed_tests.py" --root "$REPO"`; `$REPO` | `2129 passed, 128 skipped in 898.84s (0:14:58)`, exit `0`. This is the complete manifest-selected installed run at the updated fixture revision, not a filtered substitute or a source-suite pass. |
| `make test`; `$KIT` | `1 failed, 2497 passed, 1 skipped in 472.05s (0:07:52)`, exit `2`. The traceback is `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`, the disclosed #393 observation. It is separate from the repaired installed-config/adapter assumptions and the #705 drift-liveness applicability regression; no new causal explanation or resolution is claimed. |
| Separate `bash -n` calls for `$KIT/scripts/dev_session.sh`, `$KIT/scripts/reconcile_sessions.sh`, `$KIT/scripts/lib/repo_root.sh`, `$KIT/scripts/hooks/pre-push`; `sh -n "$KIT/init.sh"`; `$KIT` | Each exited `0`. These explicitly parse the paths missed by #561's multi-filename recipe. They do not execute shell behavior or repair that recipe. |

The installed log names its skips: kit-source contracts, absent source-layout paths,
the omitted repository CI/changelog/live-validation corpus and the absent mutation-test
target. They remain visible limitations. The synthetic repair results belong to their
earlier pins; the final repair review's focused probes are not a full installed run at
the final merge. The later retained-fixture update is the full installed observation.
The fixture has no project Makefile; no fixture `make test` is claimed or proposed.
Audit equality carries the identity of this historical evidence forward, not a fresh run.

The kit-record verification is separate: `make test` in `$COCKPIT` at
`22734da7d3aebdf31f846b7e288e50eb99ca7156` on 2026-09-10 printed
`1 failed, 2497 passed, 1 skipped in 429.74s (0:07:09)`, exit `2`.
The [complete log](phase5-item5-b-acceptance-evidence_2026-09-10/kit-make-test.log)
and [command/environment record](phase5-item5-b-acceptance-evidence_2026-09-10/kit-verification.json)
retain the same #393 deep-JSON traceback. This observation verifies neither the
proposed hosted workflow nor a new fixture run.

## ITEM5-B-PR-01 — proposed next adoption-lifecycle execution

This decision depends on ACCEPT-01, including explicit acceptance of the custom
wrap-up as an ownership fixture. The operator selected this proposal destination on
2026-09-10: **new private `topij/adk-item5-b-field-20260909` on GitHub**
([selection record](phase5-item5-b-acceptance-evidence_2026-09-10/destination-selection.json)).
That selection is not execution approval. It must be absent; an
existing repository, ambiguous absence or unavailable authentication stops before
creation. This proposal includes GitHub Actions usage and publication of the fixture's
tracked history to that private repository. It does not include a fixture merge,
ruleset/settings changes beyond the declared private repository/default branch, public
visibility, collaborators, secrets, tracker payloads or user-profile changes.

The [proposed write ledger](phase5-item5-b-acceptance-evidence_2026-09-10/proposed-writes.json)
is part of the decision. It binds the actual supplied payload bytes and destination
modes. Recompute it and re-audit the input immediately before any execution; mismatch
requires an amended packet. Bind the roots above plus this new, absent evidence root:

`OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910`

| Destination / action | Exact proposed scope |
|---|---|
| `$REPO/notes/friction.md` | Replace only the seeded example with [the supplied complete file](phase5-item5-b-acceptance-evidence_2026-09-10/proposed-fixture-friction.md). This supplies adopt Step 5's fixture record. It does not file an upstream issue/comment or change the existing kit inbox. |
| `$REPO/.github/workflows/item5-b-installed.yml` | Add [the supplied workflow](phase5-item5-b-acceptance-evidence_2026-09-10/proposed-item5-b-installed.yml.txt), creating only its missing parent directories. This is adopter-owned verification configuration, deliberately separate from application lint. It keeps `review.require_ci: true` and supplies the real `installed-kit` check; it does not import the kit's repo-only `.github/workflows/test.yml` or Makefile. |
| `$REPO/kit-manifest.json` | **No write or refresh.** Preserve the required baseline hash and pin. The proposed narrative and CI paths are outside its kit-owned file map. No release-manifest copy, config reserialization or `--record-install` command. |
| `$KIT`, including `$KIT/.git` | **No write.** Keep the detached repair pin and FINAL inventory. Source suite runs described below use a new independent verification clone under `$OUT`, not this retained source. |
| `$REPO/.git` | Create `chore/item5-b-field-exit` from the exact fixture input, stage only the ledger payloads and commit. Retain existing branches. Create `main` at seed `8533c334637e8776ca7a4fe3a9fd8c6c64e35707` only if absent. Add `origin` with exactly `https://github.com/topij/adk-item5-b-field-20260909.git` only after verified remote creation. Record object/index/ref/HEAD/reflog/config changes and transient lock files; do not guess their byte hashes. |
| GitHub repository | `gh repo create topij/adk-item5-b-field-20260909 --private`, without README/license/template/clone flags. Read back canonical identity and private visibility before any push. Bootstrap its base by pushing the already-existing seed commit as `refs/heads/main`; create no new commit on `main`. Set default branch to `main` and read it back. No force push or replacement of a pre-existing ref. |
| GitHub head and PR | Push only the resulting `chore/item5-b-field-exit` head after local verification. Create ready with base `main`, that exact head branch, title `Complete the ITEM5-B adoption fixture`, and [the supplied body](phase5-item5-b-acceptance-evidence_2026-09-10/proposed-fixture-pr-body.md). Read back repository, base, head, changed paths and draft bit. The diff includes the original installation and update through the new friction/CI payloads; it is not an update-only PR based on `07bacf5`. |
| Review evidence / GitHub comments | Run installed `pr_watch.py --assert-ready` immediately after creation, then its normal loop. `review.bots: []` leaves independent panel review required. Use the configured adversarial/correctness lenses, record receipts **before fixes**, and post command/result stamps and exact-head dispositions. Any fixture payload fix outside this ledger requires a new decision before a write. Do not satisfy a failing CI gate with a fabricated status or by changing `require_ci`. |
| `$OUT` | Exclusively create authority, before/final inventories, Git readbacks, verified fixture byte archive and Git bundle, copied payload ledger, baseline/config/preservation reports, argv/environment/time/status/output records, PR/CI/review readbacks, result and hash ledger. Allow `source-verification/`, separately named reviewer clones, `fixture-state/`, `source-state/`, `review-state/`, `uv-cache/`, `uv-tools/`, `ruff-cache/`, `fixture-pytest-cache/`, `source-pytest-cache/`, and `tmp/`. New reviewer mutation copies stay under their own fresh `$OUT` namespaces. Never reuse historical evidence roots. |
| GitHub Actions runner | The supplied workflow declares ephemeral checkout, tool installation, caches and a pinned independent kit clone under the runner's temporary directory. It runs selected installed verification and source `make test` serially, with explicit shell parses. The job has read-only content permission; it creates no commit, PR, tracker item or notification. Capture run/job identity, actual interpreter/tool versions, complete logs and statuses. |
| Kit records | Retain the approved authority and execution result under a new evidence directory beside this packet; update this packet's disposition, maintained sprint status and living handoff, then ready kit PR, pr-watch and scoped authorized merge. Never rewrite old update/replay evidence. |

No new client action is included. Do not run `init.sh`, open an interactive Codex or
Claude session in the retained fixture, invoke the custom wrap-up, accept trust dialogs,
edit user hooks/profile settings, install another hook, refresh adapters/lenses or run
live triage/systemize under PR-01. The ordinary kit-review clients are independent
reviewers of the kit record, not a fixture field exercise.

### Execution order, commands and refusal conditions

Before each write sequence, enter its owning absolute root and assert `pwd -P` equals
that root. Reject symlink, nonregular and multiply-linked destinations, including
parent aliases. Verify archive members/bytes/modes and Git bundle integrity before the
fixture mutation. Capture both trees' FINAL inventory comparison and the baseline hash.
Require empty fixture status/index, unchanged historical refs and absent proposed
branch/evidence/remote names. Preserve ignored local/cache bytes. Bind expected config
separately from the running reader; compare the full typed tracked/merged mappings.

Apply only the ledger, hash intended destinations and compare their modes. Require the
full non-Git delta to equal the declared files plus required parent directories; verify
all other preservation hashes, including the baseline. Read staged validation before a
separate commit command. Commit before local suites so every result names an immutable
head. Test/checkout/stage/commit/baseline writers must not overlap.

For local verification, route `PYTHONDONTWRITEBYTECODE=1`, `UV_CACHE_DIR`, `UV_TOOL_DIR`,
`RUFF_CACHE_DIR`, `TMPDIR`, `PYTEST_ADDOPTS` and a nonempty role-specific
`DEVKIT_STATE_ROOT` beneath `$OUT`; record the actual values. Set pytest cache paths and
use `-ra`. Do not set an arbitrary wall-clock kill around a suite; let it finish and
read its actual summary. Capture stdout/stderr separately without normalizing logs.

- From `$REPO`, run the doctor, adapter-report, budget and complete installed-runner
  commands in the verification table above. The source used for comparison remains
  `$KIT`. Compare typed config, unchanged baseline and the declared inventory delta
  after each command.
- Create an independent clone at `$OUT/source-verification` using `git clone
  --no-hardlinks --no-checkout "$KIT" "$OUT/source-verification"`, then detach that
  new clone at the exact repair SHA. In that clone run `make test` and the separate
  `bash -n`/`sh -n` commands above, substituting the clone's absolute root. This
  exercises source verification without writing retained `$KIT` caches/metadata.
- Keep #393's disclosed traceback separate. A repeated source failure can be recorded
  as the known verification limitation; it is not a passing suite. Any different
  failure, missing summary, changed skip scope or unexpected write stops before remote
  publication for assessment. The hosted check must actually succeed; PR-01 includes
  no exception to red CI and no source repair.
- After the verified private repository exists, run explicit `git -C "$REPO" push
  origin 8533c334637e8776ca7a4fe3a9fd8c6c64e35707:refs/heads/main`, read the remote base,
  set/read default branch, then `git -C "$REPO" push -u origin
  chore/item5-b-field-exit`. Use the independently read resulting commit for head
  checks. With explicit `--repo`, create/read the ready PR from the declared title/body.
- Run `uv run "$REPO/scripts/devkit/pr_watch.py" <returned-PR-number> --assert-ready`
  and `--json` from `$REPO` with `$OUT/review-state`. The returned number is consumed
  from the authoritative creation readback, never predicted or borrowed from another
  repository. Preserve each poll, handled round and terminal receipt; use
  `--record-review fallback:panel --lenses adversarial,correctness --head <observed-sha>
  --disposition -` only for completed independent reviews. Capture actual compute.
- Capture before/after forge tuples binding repository, private visibility, base name
  and SHA, head name and SHA, changed file set, check conclusions and review receipt;
  require equality across the exit readback and an unchanged local fixture head.
  Leave the fixture PR unmerged. Report it as an operator handoff, not a merged adoption.

### Rollback and evidence preservation

ACCEPT-01 requires no fixture rollback. Declining acceptance leaves its bytes unchanged.
For PR-01, preserve failure logs and the attempted state before choosing rollback.
Recheck target hashes, staged paths, refs and remote identity; intervening work stops
rollback for a new decision. This approval would permit only the following local undo:

- Before commit, capture NUL-delimited staged names against input `413132b01d14c735d94753231bf325904135285f`;
  require each in this packet's payload ledger. Restore only the replaced friction
  bytes from verified before-archive; remove only the added workflow with the exact
  proposed hash, then remove its newly-created empty parents if still empty. Restore
  only the captured staged set from that input, including staged additions; skip the
  index command if the set is empty. Require empty staged/worktree diffs before switching.
- After commit, if no later work exists, switch back to unchanged
  `chore/item5-b-update-60fe0dc` at the input. Keep the attempt branch and evidence.
  Do not switch retained `$KIT`, revert the prior update, delete historical refs, or
  run broad `reset`, `clean`, recursive deletion or initialization.
- If `origin` was added by this attempt and still equals the approved URL with no
  intervening config change, remove only that remote and its attempt-created tracking
  metadata after retaining the remote readback. Keep any created local `main` ref as
  recorded bootstrap evidence. Git administrative history is not claimed unchanged.
- Remote creation/publication cannot be undone by restoring local files. On failure,
  leave the private repository, pushed refs and any PR intact and report their exact
  identities. Closing/deleting a fixture PR, deleting a branch/repository, changing
  visibility or merging needs a fresh exact operator decision. Read back an ambiguous
  remote response before any retry; do not infer absence from an error.
- Hash restored destinations and compare the whole non-Git inventory and Git input
  identity. Preserve pre-existing ignored/cache bytes. Any proven unexpected cache
  changes require a named restoration decision; do not silently clean unrelated paths.

The earlier UPDATE-01 rollback remains historical: its verified archives and bundles
are still readable, but it would return to the **pre-update** fixture/source. It is
not the rollback for PR-01. Neither rollback route has been executed by this preparation.

## Remaining field-exit matrix

| Requirement / route | Decision and evidence still needed |
|---|---|
| Preserved-file acceptance | Exact operator acceptance of ACCEPT-01, including the deliberately nonfunctional custom wrap-up boundary. |
| Adoption friction and ready fixture PR | PR-01's exact destination/write decision, actual local and hosted verification, independent exact-head review, PR readback and operator handoff. Fixture merge remains a separate decision. |
| New fixture client loading/trust | Untested; no new client exercise is proposed here. A later packet must name client/version/task/cwd, effective configuration stack, trust changes, prompts, permitted writes and evidence, plus restoration of any approved changes. Earlier CLI/desktop hook observations retain their original scope; do not repeat them as missing history. |
| `post-merge-systemize` live rule, friction and tracker routing | The retained test exercise establishes test-mode analysis only. Select the live repository/window and exact rule/friction/issue payloads after trusted review-source and digest checks. The fixture's disabled tracker/notification backends are not a usable live route. No old test proposal is approval. |
| Systemize engine-backed operation | Untested and the configured engines were absent in the retained exercise. Requires an implementation/install decision and exact engine provenance before field execution; kit #7 owns extraction context. This packet neither installs nor pretends to test those engines. |
| Systemize notifications | Untested. Requires configured service/recipient, exact content, send and thread-read access, returned message identity and readback; no send or profile change proposed. |
| Systemize restart/recovery | Full process-crash recovery remains untested. Checkpoint refusal probes are not restarted workflows. Requires isolated state/cache/report paths, crash cutpoints, exact state identities, allowed recovery transitions and durable before/after evidence. |
| Other systemize branches | Cap-triggered omission, batched analysis, competing production/sandbox mtimes, hostile artifact targets and fresh-client context discovery remain untested as listed in the retained record. Select bounded probes or an explicit scope disposition; do not silently promote them. |
| Triage residual routes | The credited interactive LLM-only graduation is not repeated. Engine-backed and notification-service routes are untested; preserve TRI-03/TRI-04/TRI-05's recorded dispositions and exact approval boundaries. The budget reminder does not authorize payloads, recovery or a sweep. |
| Phase 5 item 5 exit | Reconcile the evidence above against #243's maintained field-exercise list and make an explicit exit decision. No checked item follows solely from this packet or a warning-free doctor. |

The [maintained sprint status](codex-parity-plan_2026-08-23.md#sprint-status--reconciled-2026-09-10)
owns order and completion. Phase 5 item 6 and its replay remain complete at their
recorded refs; cs-toolkit #2222, #2223 and #2255 are not repeated or re-credited.
Kit #723 remains the approved upstream deferral. #585 stays earlier, outside Phase 6.
Kit #724 delivered the #722 record batch; no replacement batch or deleted explanation
is introduced here.

## Operator response and next session

The [triage intake](phase5-item5-b-acceptance-evidence_2026-09-10/triage-intake.json)
records the budget reminder's bounded state read under a temporary owned gate at
`b80fe9905c0f8dc303aae38c77aa822129e1760d` on 2026-09-10 in `$COCKPIT`.
It preserved the recorded completed run byte-for-byte and claimed no full resume
validation. No new triage draft, recovery, tracker payload or sweep was performed.

`Approve ITEM5-B-ACCEPT-01 as scoped` accepts only the ownership/preservation rows
and their stated limits. `Approve ITEM5-B-PR-01 as scoped` additionally accepts the
declared fixture files, private destination, hosted/local verification, ready PR and
bounded local rollback; it requires ACCEPT-01 and does not authorize fixture merge.
Either may be declined or amended independently. No response is not approval.

**Next:** decide ACCEPT-01 and, if ready to proceed with adoption handoff, PR-01 from
this packet after revalidating the FINAL input. Keep the systemize field-exit decision
separate and preserve item 6's completed evidence.
