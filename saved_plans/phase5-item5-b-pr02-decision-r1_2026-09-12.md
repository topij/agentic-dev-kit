# ITEM5-B-PR-02 — fixture PR continuation decision

**Prepared, not approved.** The operator's “Let's proceed” selected preparation of
this exact decision. It does not authorize the retained changes or publication below.
UPDATE-03 was executed locally and its approval is consumed. UPDATE-01 remains
consumed; UPDATE-02 and earlier questions, ledgers and evidence remain historical.

## Delivery and read-only preconditions

[Kit PR #736](https://github.com/topij/agentic-dev-kit/pull/736) delivered the
[UPDATE-03 execution record](phase5-item5-b-update03-execution_2026-09-12.md) as
`2b272a939013538a740f68f3990a6cc961c9512f`, from reviewed head
`ae6f11c4646c1a666e7049fed20b30b88c73e850`. Its
[review disposition](https://github.com/topij/agentic-dev-kit/pull/736#issuecomment-5643887657)
retains the final panel and the stamped cockpit verification result. The new
[forge binding](phase5-item5-b-pr02-evidence_2026-09-12/forge-binding.json) records
explicit repository/PR/comment reads at that reviewed head on 2026-09-12 (UTC),
from `/Users/topi/Coding/agentic-dev-kit`, including the merge readback.

The [local audit](phase5-item5-b-pr02-audit_2026-09-12.py.txt) compares against
UPDATE-03's committed **retained-final.json**, whose SHA-256 is
`9802c72b448249462cb823dae5cd679ac863426e0f58b437ba099490fe75910b`.
It imports only the committed inventory/configuration-isolation helper definitions;
it never runs the historical UPDATE FINAL main or consumed UPDATE-03 proposal validator.
Both non-executing retained inventories and Git administration are checked before
retained Git identity or configuration-reader execution. Python optimization and
bytecode writes are refused. The full typed tracked and merged config is compared.

`env -u PYTHONOPTIMIZE python3 -B saved_plans/phase5-item5-b-pr02-audit_2026-09-12.py.txt --binding-sha256 d667a2dc82a247d63165792692bf0b5328ba688bc30c7a5a6ecce7d1b58f89c5`
in `/Users/topi/Coding/agentic-dev-kit` at `2b272a939013538a740f68f3990a6cc961c9512f`
with the hash-bound preparation files in its working tree, on 2026-09-12 (UTC),
returned `local-preconditions-verified; execution-unapproved`. The same program's
optimized and wrong-binding invocations refused before dependent work. Their exact
argv, directory, revision, dates, exit statuses and unmodified outputs are in
[preparation validation](phase5-item5-b-pr02-evidence_2026-09-12/preparation-validation.json.gz).
This local result does not establish forge preconditions or execution approval.

The separate `gh pr view 1 --repo topij/adk-item5-b-field-20260909` and fully paginated
fixture review/file reads in the forge binding matched the UPDATE-03 final PR tuple,
file list and original full review-body hashes. The later pause notice is also bound.
The historical hosted run names `f770f183bf6691f1f706c676b740cf2ef5ceb766`; it is
not verification of the local updated installation or the proposed CI payload.

## Bound inputs and proposed payloads

```sh
COCKPIT=/Users/topi/Coding/agentic-dev-kit
REPO=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture
KIT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source
OUT=/Users/topi/Coding/adk-field-exercises/item5-b-20260909/pr02-7e0232e-20260912
```

| Input | Required value |
|---|---|
| Retained fixture | `4ad91c875377d8607082cd0a125ba801218187ed`, branch `chore/item5-b-update-7e0232e` |
| Retained source | Detached `7e0232ed871b37a315c5509c97b83d3b00b1a3fd`; no remote |
| Install baseline SHA-256 | `e02fda03c4119b0deb9cba6fbf37818831f3244c9f3fc1e8b37fd79e9768291b` |
| Existing private destination | `topij/adk-item5-b-field-20260909`, repository id `1364586097`, node `R_kgDOUVXucQ`, origin `https://github.com/topij/adk-item5-b-field-20260909.git` |
| Existing fixture PR | [#1](https://github.com/topij/adk-item5-b-field-20260909/pull/1), open and ready; base `main` at `8533c334637e8776ca7a4fe3a9fd8c6c64e35707`; head `chore/item5-b-field-exit` at `f770f183bf6691f1f706c676b740cf2ef5ceb766` |
| New local attempt branch | `chore/item5-b-pr02-7e0232e`, absent before execution |
| New execution evidence root | `$OUT`, absent before execution; preserve all older evidence roots |

The [write ledger](phase5-item5-b-pr02-evidence_2026-09-12/proposed-writes.json)
SHA-256 is `24b7fc281197a0a79483c257a5884273e90c38aa3c74da4d2e52767e8884c5c2`.
The [prepared-input binding](phase5-item5-b-pr02-evidence_2026-09-12/prepared-input-binding.json)
SHA-256 is `d667a2dc82a247d63165792692bf0b5328ba688bc30c7a5a6ecce7d1b58f89c5`.
It binds the ledger, supplied payloads, readback records, audit, command runner and
committed inherited helpers/checkpoint archive. Recompute these hashes immediately
before execution; a mismatch requires a revised decision, never a silent rebind.

| Destination | Exact proposed write |
|---|---|
| `$REPO/.github/workflows/item5-b-installed.yml` | Replace with the [complete supplied workflow](phase5-item5-b-pr02-evidence_2026-09-12/proposed-item5-b-installed.yml.txt), preserving its mode. It updates the source checkout/assertion and baseline hash, unsets `PYTHONOPTIMIZE`, and puts fixture/source project environments under the declared temporary output root. Existing job, triggers, read-only permission, Python selection, verification order and shell parse commands remain as supplied. |
| `$REPO/.git` | Create the new local attempt branch from the fixture input; stage only the CI payload and commit. Preserve all existing local branch refs, including the old local `chore/item5-b-field-exit`. Record generated objects, index, HEAD, commit message, reflogs and transient lock files. After publication, observe the corresponding Git-generated remote-tracking ref change. No config or hook change. |
| Existing remote head | After local verification, fast-forward only `refs/heads/chore/item5-b-field-exit` to the resulting immutable candidate using an ordinary non-forced push. The candidate must descend from both the fixture input and the bound remote input. Do not push `main` or a new remote branch. |
| Existing PR #1 | Keep repository/base/head identity and ready status. Set title to `Continue ITEM5-B verification at kit 7e0232e` and replace the body with the [complete supplied text](phase5-item5-b-pr02-evidence_2026-09-12/proposed-fixture-pr-body.md). Preserve historical comments and reviews. No new fixture PR. |
| Fixture verification/review comments | Post scoped actual command/result stamps, historical-finding reconciliation and completed head-bound review dispositions through installed `pr_watch.py`. Full logs/reports stay local; published summaries contain findings, dispositions, evidence hashes and links. No tracker issue/occurrence payload or unrelated message. |
| GitHub Actions runner | The updated workflow permits ephemeral checkout, dependency acquisition, a pinned public kit clone and serial installed/source verification with read-only contents permission. Retain actual run/job identity, interpreter/tool versions, complete logs and statuses. No synthetic status or CI bypass. |
| `$OUT` | Exclusively create authority, copied approved packet/ledger/binding, before/attempt/final inventories, verified byte archive/Git bundle, config/baseline/ref reports, commands/environments/times/statuses/output, forge readbacks and hash index. Permit `source-verification/`, separately named independent review clones, role-specific state, pytest/tool caches, project environments and `tmp/`. |
| Scoped kit records | Record the later exact response and execution outcome in new records, maintain sprint/handoff, and finish the scoped ready kit-record PR through required verification, pr-watch and standing kit-record merge authority. Historical packet/evidence bytes remain preserved. |

The baseline, retained source (including its Git administration), fixture config,
policy, hooks, registrations, adapters/lenses, documents and pre-existing ignored/cache
bytes have **no proposed write**. The earlier friction entries remain dated history.
The workflow is outside the kit-owned baseline map; no `--record-install`, baseline
refresh, release-manifest copy or source checkout occurs in this continuation.

## Execution order and stop conditions

1. Obtain the exact decision below. Capture its verbatim response and the packet,
   ledger and binding digests outside the retained trees. Run the local audit directly,
   with optimization disabled. It must complete before dependent Git/config work.
   Re-read the full forge binding independently: canonical private repository, exact
   base/head refs, PR identity/state/title/body, file set and all review surfaces.
   Compare historical full comment bodies by digest. Missing reads, changed inputs,
   new actionable feedback, an existing attempt/output root or ambiguity stop before writes.
2. Enter each owning absolute root and assert `pwd -P` before its write sequence.
   Verify destination kind, single-link identity and parent paths; reject aliases.
   Use the [PR-02 command runner](phase5-item5-b-pr02-command_2026-09-12.py.txt)
   for declared dependent commands. It retains r4's Git global/system/config isolation
   and administrative checks, with this attempt's output roots. It supplies no approval
   or destination sandbox. Do not wrap the local audit in that runner: the audit must
   inspect the caller's original Git environment before installing its own read controls.
3. Before mutation, create and verify the fixture non-Git byte archive and Git bundle.
   Create the local attempt branch; write only the supplied CI bytes, verify destination
   hash/mode, inspect the complete non-Git delta, and stage only that file. Read staged
   validation before a separate commit command. Preserve every existing local ref.
4. Commit before suites. Run the doctor, source adapter report, document budget and
   complete installed test runner from `$REPO`. Use `$KIT` only as the pinned read-only
   comparison source. Create `$OUT/source-verification` independently with
   `git clone --no-hardlinks --no-checkout "$KIT" "$OUT/source-verification"`, then
   detach that clone at the declared source. Run source `make test` there and the
   separate `bash -n`/`sh -n` commands from the execution record. Route bytecode,
   state, pytest/tool caches, project environments and temporary files outside both
   retained trees; record every environment value. Run suites serially to terminal
   summaries; no arbitrary kill, selection narrowing or overlap with checkout writers.
5. Read all actual results and complete inventory/config/baseline/ref comparisons.
   Keep the recorded #393 source failure separate from a new regression; its recurrence
   may be reported as the known local limitation, never as a passing source suite.
   Any other failure, missing summary, changed skip interpretation or unexpected write
   stops before publication. Grouped skip-summary equality cannot identify skipped nodes.
6. Re-read remote identity, exact base/head and review state immediately before publication.
   Require ancestry and a non-forced fast-forward; do not rewrite remote history.
   Push only the observed candidate SHA as `candidate:refs/heads/chore/item5-b-field-exit`.
   Read back ambiguous results before retrying. Then edit only the declared PR title/body
   with explicit `--repo` and `--body-file`, and verify their complete bytes. Concurrent
   forge changes can race a readback; any unexpected result is a stop, not permission
   to force or overwrite it.
7. Run installed `pr_watch.py 1 --assert-ready` only after authoritative fixture PR
   identity/readiness checks and the approved publication operation. Watch the actual
   current-head hosted check to success. No red-CI exception or fabricated status is
   included. Run fresh independent adversarial and correctness review over the full
   resulting PR diff, with the configured effort and isolated Git administration.
   Preserve complete reports, terminal results and actual compute readback. Reconcile
   the older recorded findings using their delivered repair/acceptance evidence.
   Record completed receipts/dispositions before any further fix. A new fixture fix
   is outside this ledger and needs its own exact decision.
8. Capture the final read-only `pr_watch.py 1 --json --no-persist` report and the complete
   fixture forge tuple twice; require equality at that resulting head. Compare retained
   preservation and all local refs against declared changes. Report the fixture PR's
   reviewed, unmerged handoff separately from adoption/field-exit completion. Do not
   merge, close, delete, change visibility/settings or continue another fixture scope.

## Failure preservation and rollback

Preserve attempted state, logs and forge readbacks before choosing rollback. Recheck
hashes, index, refs and absence of intervening work. Before commit, this proposal permits
restoring only the attempted CI bytes from the verified before archive and its staged
entry from the fixture input; do not reset unrelated paths. Require an empty index and
worktree before switching. After commit, it permits switching back to unchanged
`chore/item5-b-update-7e0232e` while keeping the attempt branch and evidence.

Neither route undoes a remote push or PR edit. On publication ambiguity or failure,
leave the remote repository/PR/refs intact and report their exact state. Remote rollback,
closure, deletion or merge needs a separate decision. Never run broad reset/clean,
reconstruct the original missing paths, restore the earlier UPDATE-01 baseline, or
remove historical evidence. The rollback has not been exercised by packet preparation.

## Preserved limits and exact approval question

The accepted inherited **special-file-root limitation remains**: a FIFO state root can
escape the inherited snapshot and obstruct state persistence. Supplied root and `.git`
root modes/timestamps are omitted; checkpoint equality does not exclude transient writes.
Ownership acceptance of `Preserve this adapter.` is not custom wrap-up functionality,
client loading/trust/hook verification, adoption completion or field exit.

Phase 5 item 5 remains incomplete. Item 6/replay and cs-toolkit #2222/#2223/#2255 retain
exactly their credited scope. #723 remains the approved upstream deferral; #585 stays
earlier and outside Phase 6. #724 delivered #722; neither that batch nor the deleted
`/tmp` explanation is restored. The friction sweep stays parked. Client/trust/profile
exercises, settings changes, initialization, generic upgrade, tracker payloads and the
remaining systemize/triage field routes retain their separate decisions.

> Approve ITEM5-B-PR-02 as bound by ledger SHA-256 `24b7fc281197a0a79483c257a5884273e90c38aa3c74da4d2e52767e8884c5c2` and prepared-input binding SHA-256 `d667a2dc82a247d63165792692bf0b5328ba688bc30c7a5a6ecce7d1b58f89c5`: apply only the supplied CI payload on the new local attempt branch from fixture `4ad91c875377d8607082cd0a125ba801218187ed`, complete the declared verification, fast-forward the existing private fixture PR #1 head, publish the supplied title/body and scoped verification/review dispositions, obtain fresh independent review, and record the kit delivery—while excluding baseline/source refresh, additional fixture fixes, client/settings/tracker work, fixture closure or merge, and field-exit completion?

Reply `Approve ITEM5-B-PR-02 as scoped` to authorize that execution. Declining or
amending leaves the retained trees and existing fixture PR unchanged. No response is
not approval. Preparation and its kit-record delivery do not consume this decision.
