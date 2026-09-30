# Phase 5 Stage A — reconciliation and fixture continuation approval

Stage A prepares a bounded continuation; it authorizes no execution. Read this with
the [completion plan](phase5-completion-plan_2026-09-18.md) and
[requirement/route ledger](phase5-stage-a-routes_2026-09-18.md).
**Proposed decision ID: PHASE5-B-UPDATE-REVIEW-01.** The separately selectable
**PHASE5-B-MERGE-01** is specific to the private fixture PR and candidate below.
Neither decision has been granted. Stage C/D/E and their acceptance amendments
remain separate.

**Read-only reconciliation.** The commands captured in
[initial reconciliation](phase5-stage-a-evidence_2026-09-18/reconciliation-initial.json),
[forge assessment](phase5-stage-a-evidence_2026-09-18/forge-assessment.json),
[direct binding/runtime validation](phase5-stage-a-evidence_2026-09-18/evidence-validation.json)
and [runtime comparison reconciliation](phase5-stage-a-evidence_2026-09-18/runtime-comparison-reconciliation.json)
ran from `/Users/topi/Coding/agentic-dev-kit` at
`5024a90dc7810b7cdfea138f2923512aae831065` on 2026-09-18.
They establish the following endpoint observations, with their full raw results:

The new repository API response omits its temporary clone credential; its original
response digest and exact redacted field are recorded in
[credential-redaction.json](phase5-stage-a-evidence_2026-09-18/credential-redaction.json).
This affects no review body or identity comparison and changes no historical evidence.

| Surface | Observation and disposition |
|---|---|
| Control checkout | Branch `chore/lifecycle-readonly-continuation`; the supplied completion plan was untracked before preparation. This task adds only its saved-plan package/evidence. No control commit, fetch, push, PR, handoff or friction edit is part of A. |
| Retained fixture | `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`, branch `chore/item5-b-update-f9db898`, head `cfb33e6d6788dd8aec64e52ca52de26121e76e51`. Non-Git member content/modes, indexed content and tracked/merged configuration equal PR04's retained endpoint. |
| Fixture administration discrepancy | `.git/FETCH_HEAD` changed from SHA-256 `3c45dd3312fbac5d01b938f9132a6d73e5ca05626c1406fc28a13bac63afeca1` to `2c7c0ee3abf1f7ffb44c55c048f0ac2ce9bc0aa8d9d11197abf1086a0189986e`; other compared administrative members matched. [Exact bytes](phase5-stage-a-evidence_2026-09-18/fetch-head-observation.json) name the expected head/base. The actor and cause are unestablished. Do not label this continuous custody or erase it. Execution is held unless the operator explicitly accepts this exact starting endpoint as part of the proposed bounded amendment; no future-fetch tolerance follows. |
| Retained historical source | `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source`, detached at `f9db89839dc8fae91ebcff3340e313c9e9d447e5`. Compared non-Git and administration inventories and index match PR04. Preserve this tree at that identity. |
| Proposed source | Canonical GitHub commit `063b4f110a60bc0b1a0bfe0cac7b1b8d29edc2d0`, parent `f9db89839dc8fae91ebcff3340e313c9e9d447e5`, tree `2892e042e5fa2187a7c8148ca07370cafabced66`. The read-back matches #742's sealed merge and the available reviewed source `0ae90261ad684088b3671e813370e4a45384760d`. Payloads come from that committed, tree-equal source, not a moving branch. The merge object was absent from the retained local review clone; no fetch was performed there. B creates its own pinned source clone. |
| Canonical fixture PR | [topij/adk-item5-b-field-20260909 #1](https://github.com/topij/adk-item5-b-field-20260909/pull/1), database ID `4498082993`, node `PR_kwDOUVXucc8AAAABDBtMsQ`, ready/open in the stamped read. Head branch `chore/item5-b-field-exit` at the retained fixture SHA; base `main` at `8533c334637e8776ca7a4fe3a9fd8c6c64e35707`. Current title/body match PR04. No retarget or new PR is proposed. |
| Review surfaces | REST review submissions, issue comments and inline comments paged to completion; GraphQL thread pagination exhausted. Comment bodies match retained PR01/PR02/PR03 surfaces plus the exact PR04 pending body. They are historical reports, not current-candidate approval. The assessment enumerates IDs/hashes; no unseen-content acknowledgement was made. |
| Protection | The captured fixture branch read reports `protected: false`. This is an explicit limitation, not permission to bypass review. Keep protection unchanged; use operator authority, canonical pre-reads, exact-head merge and post-read. They cannot atomically lock base/review state. |
| Sealed evidence | Fresh hashing matches the direct file edges of PR04 and terminal #742 seals, including linked historical validation artifacts. This is not represented as a fresh recursive traversal of every historical authority. B must revalidate the full transitive chain at act time with its recorded mutable-state semantics, in a new output namespace. Never blindly rerun an old validator that writes into sealed evidence. |
| Retained runtime inventory | The runtime roots named by #742's terminal custody were reread. The strict comparison reported missing `sha256_available: false` fields in the new collector's unreadable-file rows. The separate comparison proves those differences are precisely that omitted schema field with identical kind/mode/read-error; unreadable content remains unverified. Preserve both observations. No missing root was rebuilt. |
| Original missing trees | The original disposable adopt fixture and source remain absent in the recorded read. They must not be reconstructed or credited as continuously retained. |

`kit_doctor.py --root <fixture> --manifest <reviewed-source>/kit-manifest.json --json`,
in the control cwd/revision/date above, returned exit `1` and classified the source
files enumerated in the installation ledger as stale. The exact invocation and output
are in [doctor-command.json](phase5-stage-a-evidence_2026-09-18/doctor-command.json).
The source doctor's `--adapter-report` invocation, with that same stamp, returned exit
`0`; its [report](phase5-stage-a-evidence_2026-09-18/adapter-command.json) leaves the
Codex custom wrap-up adopter-owned. These diagnostics do not establish client loading
or functionality.

The session-start read is complete as a scoped briefing: effective config and local
state were read; the captured paginated kit PR read had no open entries; tracker
backlog and recent CI were available. CI metadata is discovery only, not a new source
verification claim. No configured host apply/verify mechanism was established, so
host drift is not claimed checked. No urgent candidate was promoted from a partial
archive lookup. The next work remains this operator-selected Stage A package; the
budget reminder remains housekeeping with no triage draft or sweep authority.

**Exact proposed candidate and payload.** [installation-ledger.json](phase5-stage-a-evidence_2026-09-18/installation-ledger.json)
names every absolute destination, before/after SHA-256, source and file mode. Review
the [complete patch](phase5-stage-a-evidence_2026-09-18/proposed-fixture.diff) and
[candidate derivation](phase5-stage-a-evidence_2026-09-18/candidate.json).
`prepare-payloads.py` computes Git blob/tree/commit identities without writing a Git
object or an installed tree. The proposed candidate is
`096bfb035dd36ea781c765aa1d09d44ec66b5465`, tree
`411913fa3af80bdafd844ff46bf29250a3ce34ba`, parent
`cfb33e6d6788dd8aec64e52ca52de26121e76e51`.
Its fixed author/committer identity, declared timestamp, exact message and raw commit
bytes are bound in the candidate record. Actual staged tree and committed SHA must
match before publication; a different object requires an amended package.

| Source change | Fixture destination | Decision |
|---|---|---|
| `scripts/archive_plan_sessions.py` | `scripts/devkit/archive_plan_sessions.py` | Install exact merged bytes and executable mode. |
| `scripts/lib/atomic_write.py` | `scripts/devkit/lib/atomic_write.py` | Install exact merged bytes/mode. |
| `scripts/pr_watch.py` | `scripts/devkit/pr_watch.py` | Install exact merged bytes and executable mode; preserve watcher state. |
| `scripts/tests/test_portability.py` | `scripts/devkit/tests/test_portability.py` | Install with archive/atomic repair. |
| `scripts/tests/test_pr_followup_hook.py` | `scripts/devkit/tests/test_pr_followup_hook.py` | Install source's precondition-aware test repair; no inference that historical #393 failures passed. |
| `scripts/tests/test_pr_watch.py` | `scripts/devkit/tests/test_pr_watch.py` | Install with watcher repair. |
| Source release manifest | No wholesale fixture copy | Keep independent for inspection. Generate fixture `kit-manifest.json` through installed `--record-install --from-kit`, requiring byte equality to the prepared predicted baseline. Its proposed SHA-256 is `01a67ee172b1c8ba44f8821cdc3442537cf5dc43f4bde855cfcda7ddf755dd6e`. |
| Source `CHANGELOG.md` | Read-only guidance | #742 requires engine/test refresh together and new native poll/inspection before acknowledgement; no legacy-seen migration. No fixture changelog replacement. |
| Package-authored CI | `.github/workflows/item5-b-installed.yml` | Exact payload pins the merge source and tree, binds the proposed baseline hash, runs complete installed verification, individual shell parses and JUnit retention. Removes the old source `make test` replay. Raw Actions logs remain required. |

All other fixture bytes/modes and local settings are preserved, including root
instructions, `ROADMAP.md`, notes, tracked/local config, runtime registrations,
Claude lane profile/lens definitions, generated adapters and the custom wrap-up.
The declared install set and `not_installed` decisions remain unchanged. No
`init.sh`, template, workflow, config or hook-installation rewrite is needed for this
delta. This is an explicit narrow continuation through Upgrade's per-file refresh,
baseline and destination-verification steps, **not a repeat of initialization**.
If fresh inspection shows a migration or dependency outside this ledger is needed,
stop and amend rather than run generic initialization.

The [upgrade workflow at the reviewed source](</private/tmp/adk-repair04-lifecycle01-01a0b082/repo/docs/agentic-dev-kit/workflows/upgrade.md>)
and its safety-critical doctrine were read for this proposal. After obtaining the new
clone at the approved merge, re-read its own upgrade binding and complete shared
workflow before any installation write. Require equality with the reviewed workflow
and keep the explicit narrow scope above. Safety-critical operator merge authority
is not replaced by a successful panel.

**Finding-to-evidence map.** Source evidence is reused at its original identity;
fresh installed evidence below is still required. Old findings are not acknowledged
by this table.

| Finding | Original classification | Transferred repair and new installed evidence |
|---|---|---|
| PR04-A1 | P1 / High regression | Archive preserves recent introduction and budgets it; require installed `test_recent_introduction_stays_before_live_sessions_across_sweeps` and `test_recent_introduction_counts_toward_budget_and_survives_nonwrites`. |
| PR04-A2 | P1 / High regression | Occurrence/content acknowledgement; require installed `test_edited_acknowledged_comment_resurfaces_and_blocks_gates`, `test_distinct_identical_occurrence_reopens_all_gates`, `test_unidentifiable_occurrence_cannot_be_silenced_by_acknowledgement`, and `test_identical_occurrence_arriving_between_poll_and_ack_stays_unhandled`, plus legacy-key and own-disposition cases in the changed module. |
| PR04-A3 | P2 / Medium regression | History separator; require installed `test_history_insertion_keeps_a_heading_boundary_across_sweeps`. |
| PR04-C1 | P1 / High regression | Confirm destination bytes before claiming recovery; require installed `test_archive_rollback_confirmation_through_subprocess`, history-confirmation and destination-alias subprocess cases. |
| PR04-C2 | P2 / Medium regression | Contain close exceptions; require installed `test_commit_contains_directory_close_exceptions_after_replace` and `test_archive_contains_postpublication_close_interrupt_in_subprocess`. No additional loss was established by the original probe. |
| Source review occurrence-identity finding | Functional Correctness / Major / Heavy lift | #742's completed source panel, hostile/mutation/restoration evidence and exact public disposition remain authoritative at their named source. Fresh installed review checks integration, not re-crediting that source lifecycle. |
| PR03/PR02/PR01 | Preserve original classifications individually | [Coordinator assessment](../state/review-evidence/item5-b-p3-pr04-execution-20260915-01a0a5ba/coordinator-review-assessment.json) retains trailing-quotation repair, source/adopter policy applicability, guide wording, declaration observing assertion, detector and newline comparator dispositions. Require fresh panel to assess applicability; retain `expected_failure_established: false`. |

**Proposed execution sequence after approval.** The exact command plan is in
[the runbook](phase5-stage-a-evidence_2026-09-18/RUNBOOK.md). Its variables name fixed
absolute roots and candidate constants, not substitute branches.

- Revalidate the preparation seal, retained endpoint and explicitly accepted
  `FETCH_HEAD` bytes, complete historical/transitive authority, live PR identity/base/head,
  review bodies and configuration. Stop on unexplained differences. Create only the
  new B namespace; record backups of ledger files, fixture administration and a Git
  bundle before writes. Preserve backups and every historical namespace.
- Create a fresh canonical source clone pinned to the merge SHA; require parent/tree,
  manifest hashes and workflow identity. Preserve the existing source tree unchanged.
  Create fixture branch `chore/item5-b-update-063b4f1` from the bound parent. Assert cwd
  before each write sequence, preflight regular unaliased destination paths and parents,
  copy only the ledger, hash destinations, and run native baseline recording. Any
  unexpected generated output or preserved-path change stops execution.
- Commit only the ledger paths using the bound metadata/message. Require actual SHA/tree
  equality to the candidate record and empty tracked/untracked status, with evidence
  and caches outside the fixture. Then run complete destination verification. Do not
  substitute selected nodes for the installed suite. The repair-specific nodes must
  execute their behavioral assertions; absence, failure or skip is a stop.
- Publish only this candidate to the existing PR branch using an ordinary fast-forward
  push. Replace title/body with the exact [title](phase5-stage-a-evidence_2026-09-18/payloads/pr-title.txt)
  and [body](phase5-stage-a-evidence_2026-09-18/payloads/pr-body.md), assert ready status,
  then inspect actual hosted logs/artifacts for the candidate. No force push or new PR.
- Obtain a fresh full-base-to-candidate adversarial/correctness panel. Each lens receives
  the raw pinned diff, target identity and shared contract with configured high effort,
  in a new independently made mutation copy. Approval of this bundle explicitly permits
  sending this private fixture's review inputs to OpenAI's Codex service. It grants no
  Stage C client/trust exercise. Retain actual runtime/rollout, complete suite output,
  behavioral mutations, drift-test exclusion, exact restoration and enabled restored
  checks. No historical reviewer or source suite is rerun. All owned processes must
  reach retained terminal reports. New findings stop this package before repair,
  deferral, disposition or acknowledgement.
- Only if the new evidence substantiates every conditional statement may the native
  watcher post the prepared [disposition input](phase5-stage-a-evidence_2026-09-18/payloads/disposition-input.md)
  using `--record-review fallback:panel --lenses adversarial,correctness` at the exact
  candidate. Native rendering is prepared separately as `payloads/disposition-comment.md`.
  No free-form addition, new finding response or new verification exception inherits
  approval. If these fixed words are insufficient or false, stop for a concrete amendment.
- Preserve the native fixture watcher state and native settle history. Inspect a saved
  persistent poll and its complete raw review surfaces; associate every proposed
  acknowledgement with the enumerated unchanged historical comment identity/body and
  actual handled disposition. `--mark-seen` may consume only that exact saved snapshot.
  Preserve occurrence/content tokens and compare actual state evolution. Never reset,
  seed, convert legacy keys or hand-edit state. Unknown comments require assessment
  and, if a new write is needed, an amended payload approval. Poll within the declared
  runbook bound; exhaustion checkpoints and stops, without resetting native clocks.
- Conditional merge is available **only if PHASE5-B-MERGE-01 is also explicitly
  approved**. Require actual current-head successful CI, substantiated fresh review,
  handled known findings, valid receipt, native converged/mergeable/settled state and
  canonical base/head/title/body/policy readbacks immediately before the exact-head
  squash invocation. A known historical-only verification-stamp warning must remain
  labelled historical and must be reconciled against freshly stamped local execution
  results; it is not permission to suppress a required test or an unexplained warning.
  Read back merge state, parent and complete candidate tree afterward. Preserve branch
  and evidence. No branch deletion or local protected-branch advance is included.

**Verification reuse and limits.** #742's source author/panel suites, original hosted
run and completed lifecycle stay in [its sealed RESULTS](../state/review-evidence/item5-b-p3-repair04-lifecycle01-continuation02-01a0b082/RESULTS.md)
and [exact public disposition](../state/review-evidence/item5-b-p3-repair04-lifecycle01-preparation-20260917-01a0b082/payloads/receipt-disposition.md).
The source tree-equality proof permits reuse of those source observations; no new
source result is asserted at the squash SHA. The PR04 fixture suites/reviews stay
credited at their old head and cannot verify the changed candidate.

Preserve the exact local skip for
`scripts/tests/test_init_sh.py::test_step_2_refuses_on_an_exception_outside_the_old_enumerated_set`:
`the gate's own python3 parses 200000 nested arrays without raising, so this input cannot exercise the escape this test is about`.
The path remains unexercised. Hosted acceptance stays confined to run `35221728160`,
job `105203274603`, checkout `983538335d9c39309c4e437e95dabbe52d2e7f69`;
skip attribution was inferred from collection order with original
node/reason/configuration/plugin/locale telemetry unavailable. The later source CI
run visible in discovery receives no transferred exception or additional acceptance.

PR04's separate #393 exception and applicability failure remain historical. New
candidate skips must be enumerated with actual reasons and classified against the
declared installed scope. No blanket skip allowance, failure waiver, or new exception
is proposed. A required assertion not exercised, an unexplained skip change, a
failed command or uncertain hosted result stops dependent lifecycle work. #561's
grouped Bash recipe is unchanged; independent shell parses provide only their named
coverage. Top-level JUnit does not instrument every shipped nested subprocess;
targeted mutation evidence is not exhaustive or agent-obedience coverage.

All complete historical records remain linked, including
[PR04 preserved limits](../state/review-evidence/item5-b-p3-pr04-execution-20260915-01a0a5ba/approved-preserved-limitations.json)
and [exceptions](../state/review-evidence/item5-b-p3-pr04-execution-20260915-01a0a5ba/approved-EVIDENCE-AND-EXCEPTIONS.md).
Do not downgrade or erase failures, refusals, corrected classifiers, interrupted
controls, malformed helper attempts, unavailable telemetry or historical reviewer
classifications. Preserve #742's failed strict post-merge comparison and the finding
that only GitHub `pull_requests` association arrays disappeared; its reconciliation
does not relabel that strict comparison successful.

**Allowed evolution and rollback boundary.** Only approved B payload files, the
new fixture branch/commit, ordinary publication ref/reflog updates, new B clones and
evidence/cache/runtime paths, and native watcher operations in the declared watcher
root may evolve. Existing watcher history is carried by native operations, not copied
into a newly seeded state. Old source/fixture snapshots, reviewer clones, runtime
trees, replay evidence, source PR #742, client profiles and tracker state remain held.
Host user config/credentials and launcher settings are not edited; owned process
outputs are captured outside retained trees. Root metadata exclusion, non-followed
symlinks, special/unreadable contents and actor/process uncertainty remain explicit.

Before publication, a separately recorded execution failure may use the approved
file backup to restore **only this package's replaced paths**, and only when current
bytes still equal the recorded package-written bytes; restore exact old modes, retain
both endpoints, and leave the attempt branch/evidence intact. Do not run `reset --hard`,
delete a branch, discard unexpected edits, restore whole Git administration, or erase
a failed candidate. After publication, no force push, revert, close, receipt deletion
or rollback is preapproved. Stop and present its exact effects. After a merge, a
failed post-read preserves the observation and requires reconciliation; no automatic
revert or retry follows.

**Approval choices.** A concrete approval can authorize the compatible sequence
without returning for each already specified action:

> Approve PHASE5-B-UPDATE-REVIEW-01 as scoped, including the exact FETCH_HEAD
> checkpoint amendment, bound payload/candidate, changed-candidate verification,
> ordinary fixture publication, private Codex panel, and conditional fixed
> disposition, native acknowledgement and settling. Approve PHASE5-B-MERGE-01
> for fixture PR #1 only at candidate 096bfb035dd36ea781c765aa1d09d44ec66b5465
> if every stated gate is met.

The merge sentence may be omitted; the rest then ends ready and reviewed with merge
held. Approval must bind this package's final
[approval-binding.json](phase5-stage-a-evidence_2026-09-18/approval-binding.json)
SHA-256, recorded in its
[sidecar](phase5-stage-a-evidence_2026-09-18/approval-binding.sha256).
Silence is not approval. Source changes, unknown payloads/new findings, new exceptions,
client/trust/profile work, field-route execution, tracker/notification writes, friction
graduation, cleanup, acceptance-scope amendments and Phase 5 exit remain excluded.

This confirmation boundary comes from the user's explicit instruction to prepare
Stage A before fixture/client/tracker/lifecycle writes and the completion plan's
Stage A/B boundary. It is not an additional permission step inferred from a skill.

The [preparation results](phase5-stage-a-evidence_2026-09-18/PREPARATION-RESULTS.md)
separate static package checks from the future installed verification and record the
final read-only endpoint comparison.
