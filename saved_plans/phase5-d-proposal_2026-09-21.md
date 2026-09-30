# Phase 5 D — engine, service and recovery proposal

**Prepared for approval; no D execution or acceptance amendment is approved.**
Recommended next decision: **PHASE5-D-TRIAGE-ENGINE-01**, the isolated triage
engine implementation scope below. Preserve the existing Phase 5 contract, deliver
review candidates for its missing engine prerequisites, then prepare the exact field
payloads after separately authorized delivery and installation. Installing
the donor scripts unchanged would not implement the kit's declared workflows.

## Authority and preserved evidence

This proposal follows the [completion plan](phase5-completion-plan_2026-09-18.md)
and [Stage A route ledger](phase5-stage-a-routes_2026-09-18.md). The later
[Phase 5 C execution record](../state/review-evidence/phase5-c-wrap-up-20260921/coordinator/EXECUTION.md)
owns C's delivery and limitations: private fixture PR #2 merged as
`7b35c6543a27c918a6057afaf0d3e014fef9ab77`, from reviewed candidate
`498e0cfb70ba7b6527bede5a6030cf76bbe75817`. Its native probe was an uncommitted
probe over the recorded fixture base, not that committed candidate. It established
local Codex wrap-up functionality with an incomplete-resumable publication outcome;
it did not establish external-service or Claude coverage.

Keep Phase 5 B's completed fixture/source lifecycles, C's original terminal/review
records, private issue #3's adapter coverage disposition, failed nested native
attempts, local/hosted verification distinctions and skips intact. C's disclosed
retained-fixture fetch metadata change and incomplete global-config restoration
remain limitations. No claim of pristine retained Git administration follows here.
Neither earlier packet wording nor the older handoff's next-step instructions
restart work completed by those execution records.

Also retain the credited interactive LLM-only triage graduation, the
[systemize test record](codex-systemize-test-field-exercise_2026-09-06.md), its
missing original raw-cache continuity, item 6's completed replay, #723's approved
deferral, #585's prior placement and #243's separate Phase 6 residue. Historical
checkpoint refusals remain refusal evidence; they are not process-crash recovery.
The parked source-block/digest mapping in Stage A remains authoritative history;
new candidate labels confer no approval.

## Discovery and provenance

Local observations below are from `python3 -B
/Users/topi/Coding/agentic-dev-kit/state/review-evidence/phase5-d-preparation-20260921/collect.py local`,
in `/Users/topi/Coding/agentic-dev-kit` at
`db1e84ec069b545ada7c722184a3d62f52a5ac1f` on 2026-09-21.
[Local discovery](../state/review-evidence/phase5-d-preparation-20260921/local-discovery.json)
retains the merged configuration, configured path existence, source hashes and
selected donor-file status. These are capability observations, not workflow runs.

| Route | Configured kit path | Discovery result and required adaptation |
|---|---|---|
| Systemize fetch | `scripts/fetch_merged_prs.py` | Absent at the stamped read. Donor reads a separate pipeline config and has deployment-specific tracker references. Adapt complete pagination, exact trusted author identities, current merged config and raw run envelope. |
| Systemize digest | `scripts/digest_merged_prs.py` | Absent. Donor returns its own `digest_version` shape, permits a disabled cap and uses fallback batching. Implement the declared strict values, canonical severity/ranking, omitted identities, run identity and independent raw-to-digest validation. |
| Systemize heartbeat | `scripts/heartbeat_cli.py` | Absent. Donor loads `libs/pipeline-engine/src/pipeline_engine/heartbeat.py`. Adapt a kit-owned, state-resolver-aware implementation and specify its configured invocation/state contract; no customer pipeline or scheduler installation. |
| Triage draft | `scripts/triage_friction_log.py` | Absent. Donor includes Anthropic proposal generation, Linear integration and deployment paths. Reuse suitable parsing logic only after conformance review; kit analysis must honor the selected Codex runtime and approval boundary. |
| Triage finalize | `scripts/finalize_triage.py` | Absent. Donor uses CUS graduation metadata and actively performs `git checkout -B` in its caller. Replace this with exact accounted-block transformation, operation accounting and isolated-worktree publication. |

The same configured filenames were absent beneath the retained fixture's
`scripts/devkit` in that read. Its `notify.backend` and `tracker.backend` resolve
to `none`; its trusted review-source union is empty. It cannot supply the live
service or systemize source routes without changing its accepted configuration.
**Use a new D checkout and state namespace; do not repurpose the B/C fixture.**

Candidate donor:
`/Users/topi/Coding/in-parallel/cs-toolkit`, observed revision
`53f2f17ab2aed9145bf0c612984669c821da4a90`. The discovery JSON binds the donor
entry scripts, `_triage_inbox.py` and heartbeat dependency by SHA-256 and retains
`git status --short -- <selected paths>`. Static source inspection used `rg` and
`sed` at that donor revision on 2026-09-21 from the kit cwd. It demonstrates the
specific incompatibilities above, not a complete donor audit or donor test result.
No donor engine was imported, executed, copied into the kit or installed.
Before copying donor implementation bytes into a publishable candidate, verify the
exact commit/path custody and relevant dependency closure, read license/notices,
establish reuse authority and record required attribution; otherwise use an independent
implementation of the kit contract and preserve the donor as read-only reference.

`collect.py forge` at the same kit revision/date/cwd retained authenticated `gh api`
responses in [forge discovery](../state/review-evidence/phase5-d-preparation-20260921/forge-discovery.json).
The protected kit head read back as `db1e84ec069b545ada7c722184a3d62f52a5ac1f`;
[#6](https://github.com/topij/agentic-dev-kit/issues/6) and
[#7](https://github.com/topij/agentic-dev-kit/issues/7) read back open. #6 scopes
triage extraction behind tracker adapters; #7 sequences systemize after #6.
Those issue descriptions predate the current shared contract, so their filenames,
draft-PR wording and historical implementation descriptions are not normative.
An initial sandboxed GitHub read failed to connect; the explicit read-only
network retry supplied the retained responses. Repository permission metadata is
not proof that an exact future write will succeed.

The merged kit config selects GitHub Issues at `topij/agentic-dev-kit` and Slack
recipient `U082VD4SR2N`. The Slack profile tool read on 2026-09-21 in this planning
task returned Topi; send and thread-read tools are callable. No send or approval
round trip was attempted. Tracker creation/readback is likewise unexercised here.
Private Linear credentials or an adopter deployment are not prerequisites for the
proposed kit/GitHub route.

## Proposed approval: PHASE5-D-TRIAGE-ENGINE-01

**Purpose:** implement the configured triage engine pair against the existing
shared declaration, with deterministic state, approval and recovery enforcement.
This is a prerequisite implementation slice, not approval to graduate the kit inbox.
Codex owns implementation and evidence; Topi owns scope changes, exact live payloads
and merge decisions. Request GPT-5.6 Sol / medium for implementation and independent
review contexts, retain launcher settings and actual runtime selection when exposed.
Do not rewrite `models.runtime_mappings` to make this task-local choice persistent.

**Source and workspace.** Start a fresh local clone at immutable kit source
`db1e84ec069b545ada7c722184a3d62f52a5ac1f`, with branch
`chore/phase5-d-triage-engine`, under
`/private/tmp/adk-phase5-d-20260921/triage-engine`. Refuse an existing destination;
do not reset or remove it. Put synthetic state, caches, temporary homes and logs
inside `/private/tmp/adk-phase5-d-20260921`; retain reviewable evidence under
`state/review-evidence/phase5-d-triage-engine-01` in the control repository.
Use absolute write paths, assert cwd before writes and verify at destinations.
Do not fetch, fast-forward, initialize or write the retained B/C fixture/source.

**Implementation footprint and acceptance.**

Before implementation writes, persist a requirement-to-file/test ledger in the new
evidence namespace. Map every normative triage input, capability, authority, artifact,
recovery and completion row, including its refusal branches, to implementation and
verification. Freeze intended paths within this allowlist: the configured entry
points; `scripts/lib/triage/`; triage-specific `scripts/tests/test_triage_*.py` and
`scripts/tests/test_finalize_triage.py`; the shared triage workflow for CLI invocation
documentation; `config/dev-model.yaml`; `init.sh`; `kit-manifest.json`; and
`CHANGELOG.md`. Config/installer/manifest edits are limited to necessary shipping
wiring. If existing schema or installation tests outside this list need changes,
present the exact additional paths and reason as an amendment before editing them.
No changes to `pr_watch.py`, `dev_session.sh`, `launch_lane.py`, lane settings,
runtime adapters or unrelated source are included.

- Add the configured `scripts/triage_friction_log.py` and
  `scripts/finalize_triage.py` entry points. Add narrowly scoped shared helpers
  beneath `scripts/lib/triage/` and focused tests beneath `scripts/tests/`.
  Prefer deterministic parsing/state machinery; proposal analysis remains an
  explicit runtime step using the selected model, without a hardcoded Anthropic call.
- Define and document engine CLI/input/output contracts against
  `docs/agentic-dev-kit/workflows/triage-friction-log.md`. Implement the complete
  applicable input, artifact, approval, accounting and recovery tables. A ready engine
  candidate must satisfy that complete traceability ledger. Do not install selectable
  entry points around incomplete behavior: file presence selects engine-backed mode.
  If implementation must split into a non-selectable foundation, stop and obtain an
  amendment; a refusal stub is not completion of a required successful transition.
  No weakening of the shared declaration and no runtime-only adapter behavior change.
- Resolve merged `config/dev-model.yaml`, exact source bytes, canonical RFC 8785
  identities and own-session state paths. Atomically acquire the complete owner gate
  before observing active state. Bind every transition to the expected state digest.
  Keep live/test identities separate and persist the selected engine mode on resume.
- Bind exact payload/core digests, source-block digests, operator identity and approval
  source. Persist attempted external operations before dispatch; require authoritative
  readback before retry. Implement GitHub Issues create/readback behind a provider
  boundary. Exercise adapters with fakes locally; real tracker calls remain excluded
  until an exact-payload field approval. Linear live coverage and a full extraction of
  #6's broader Linear scope are not claimed by this slice; #6 stays open.
- Finalize only the verified-filed or explicitly archived frozen blocks. Preserve
  parked, unmentioned, changed and newly added blocks. Stage only the configured inbox
  and archive in an isolated worktree; reject caller-path conflicts. Persist exact
  repository-operation identities and the reviewed head. The engine never merges.
- Implement the declared invalid-state, gate-only, state-present and test recovery
  transitions with capture-before-parse and prepared-action-bound approval. Preserve
  uncertain tracker attempts and terminal held evidence. No automatic stale-gate
  removal or approval inference. Synthetic recovery approvals must be labelled
  test inputs and must never authorize a live operation.
- Add focused fault/cutpoint tests for exclusive gate acquisition, concurrent state
  replacement, canonical/digest rejection, source drift, cross-mode reads, ambiguous
  service responses, partial batches, protected-head fast-forward/divergence, exact
  finalization, reviewed-head movement and recovery restart. Include control/mutant
  witnesses where the repository review doctrine requires behavioral evidence.
- Update config/schema/installation manifests or tests only where required to ship
  these engines and their declared CLI. Any new key belongs in `config/dev-model.yaml`.
  Document the adopter action in this implementation PR's numbered `CHANGELOG.md`
  entry. Do not migrate the retained fixture or expand into unrelated engine cleanup.

Recovery tests must explicitly cover normal-resume gate rebind before/after state
replacement; gate publication before/after hard-link publication and same-inode
temporary-name cleanup; gate-only prepared bundle, intent, old-gate quarantine,
replacement-gate acquisition, held receipt and release; state-present capture,
prepared action, quarantine, restart receipt and gate release; persisted external
attempt before dispatch and after ambiguous response. At each cutpoint retain exact
bytes/digests, inode/link observations, owner-token binding and the permitted next
invocation route. Use owned synthetic artifacts/services for this implementation
verification; these tests do not establish live field recovery.

**Verification and delivery.** Run the repository's required `make test` in the new
source checkout with an extended runtime allowance and retained terminal output.
Keep actual failures/skips and the #561 shell-parse limitation explicit; parse changed
shell files separately if any are necessary. Run installed-engine verification in a
new disposable installation when the install surface changes, without rerunning B/C.
Stamp results with command, cwd, exact candidate SHA and date. Obtain fresh independent
adversarial/correctness review under the applicable shared doctrine; supply the exact
candidate and raw diff. Publish a ready kit PR under the approved branch, run
`pr-watch --assert-ready`, and follow it to the configured verification/review gates.
The approval includes ordinary scoped ready-PR publication/review follow-through;
it excludes merge, live notification, tracker filing, inbox graduation and deployment.
Unexpected broader repairs require an amendment; preserve any blocked result.
The outcome is a reviewed candidate. Engine availability on the protected branch or
in the field checkout requires a separate authorized merge and exact installation/
readback; no later D package may infer that delivery from ready-PR status alone.

**Approval wording:** “I approve PHASE5-D-TRIAGE-ENGINE-01 as scoped, using
GPT-5.6 Sol / medium, through a ready, verified and reviewed kit PR, without merge
or live field writes.”

The [proposal binding](../state/review-evidence/phase5-d-preparation-20260921/proposal-binding.json)
and [digest sidecar](../state/review-evidence/phase5-d-preparation-20260921/proposal-binding.sha256)
identify the prepared document and supporting evidence. Verify them before consuming
approval; this proposal remains unapproved until the operator decides.

## Subsequent D packages and evidence gates

These rows retain required coverage. They are proposed follow-on scopes, not actions
included in PHASE5-D-TRIAGE-ENGINE-01 and not approved deferrals.

| Package / route | Concrete scope to bind before execution | Acceptance evidence |
|---|---|---|
| D-SYSTEMIZE-ENGINE | After the triage slice, adapt `fetch_merged_prs.py`, `digest_merged_prs.py` and `heartbeat_cli.py` plus minimal helpers/tests to the shared contract. Define heartbeat path/job/invocation config explicitly; do not substitute a Codex automation. | Atomic complete engine-set selection, real subprocess invocation and exit status, exact-source hashes, raw/digest/report identities, independent cap/rank validation, heartbeat start/tick/complete state and failure semantics; required source/installed tests and reviewed delivery. |
| D-SYSTEMIZE-LIVE | New isolated kit checkout; complete configured lookback window anchored to an exact UTC interval and protected SHA at preparation time. Retain all pages, review objects, inline comments, exact trusted author matches and file/source evidence. Include earlier suggested PRs only if they fall in that full window; never substitute a handpicked PR list for a window fetch. | Qualifying recurrence becomes an exact shared-rule patch; below-threshold incident becomes an exact friction block; a qualifying high-severity incident becomes an exact tracker proposal. Adequately covered causes become rule citations. No invented recurrence or unnecessary issue solely to produce a write. Bind each actual destination/payload for approval. |
| D-SERVICE | Slack DM to configured Topi `U082VD4SR2N`, through the actual send/thread-read tools; GitHub Issues in `topij/agentic-dev-kit` only for an approved genuine payload. Reconfirm recipient and backend at act time. | Persist exact content/marker before attempt, returned channel/message/issue identifiers, independent complete readback and sender identity for any approval. Tool presence is not delivery evidence. An isolated `[TEST]` DM proves only its service route, not live triage graduation. |
| D-SYSTEMIZE-RECOVERY | Isolated D process and state roots; terminate only the owned process at the durable raw, digest, pre-approval proposal and post-dispatch/pre-receipt cutpoints. Restart a fresh process from retained artifacts at each point. | Before/after bytes, process identity/termination, identical run identity, actual restart choice and external-destination readback. Never repeat a potentially completed external write solely because the local response was lost. Fake-service cutpoints prove only local orchestration; real-service ambiguity needs its own exact payload/send authority. |
| D-SYSTEMIZE-BOUNDARIES | Separately labelled synthetic corpus above the configured cap and batching threshold, adversarial target fixture and competing cache copies. Keep all copies under new D roots. | Severity/order/omitted-identity disclosure, exact batch slices and cross-batch distinct-PR reduction; sandbox/production mtime selection in both directions; refusal/preservation for symlink escape, hardlink aliases, nonregular, tracked/control targets, collisions and parent retargeting. Synthetic success is not a live-window route. |
| D-FRESH-CONTEXT | Fresh Sol/medium Codex context in the approved D checkout with only the native skill invocation and task scope. Bind client/version/cwd/config/instructions. No inherited analysis or prompt that supplies the expected route. | Observable discovery of adapter/shared workflow and merged config, chosen engine mode and actual behavior. If client trust changes are necessary, first bind their exact effect and guarded restoration; do not reuse C's leftover profile state as approval. |
| D-TRIAGE-RESIDUAL | New engine-backed test session and separately approved live session, without reading/replacing existing production triage state outside its gate. Freeze current source blocks, preserving historical parks by bytes/digest. | Engine draft/finalize evidence, notification-thread approval identity/digest, attempt/readback accounting, exact eligible sweep and ready-PR review identity. Actual merge requires its own authority; completion requires a later matching merge readback. The credited LLM-only graduation is not replayed. |
| D-TRIAGE-RECOVERY | Exercise absent-state stale gate; valid/invalid state with stale gate; invalid state without gate; prepared envelope/intent/quarantine/replacement interruption; active/uncertain owner; scheduled refusal; test held evidence. Use owned isolated artifacts and exact action-core approvals at required mutation points. | Gate ownership evidence, complete capture before parsing, deterministic approved intent, same-core restart and preservation. State-present test-gate recovery remains terminally held; a gate-only receipt is never restart permission. Ambiguous tracker writes remain held; no whole-sweep fallback. |

For boundary corpora, use the configured values from the bound run: generate a
finding-bearing population exceeding `max_findings_prs_per_run`, and a validated
capped digest exceeding `single_pass_max_prs`; partition with `batch_size`. Do not
silently lower production thresholds to manufacture coverage. If a natural live
window cannot exercise a required branch, present the labelled synthetic evidence
and an explicit acceptance decision; the route remains unexercised as live behavior.

The shared triage declaration makes scheduled notification send/read mandatory;
interactive degradation to the current session does not discharge that service row.
Tracker/notification recovery requires destination reconciliation before any retry.
If readback cannot distinguish absent from previously written, stop operator-held.

## Payload and state boundaries

No live finding payload exists yet: current complete-window collection and grounded
clustering belong to the later field package. Preparing a generic tracker title or
rule now would invent evidence. That package must present exact title/body/project/
labels or exact patch/friction bytes and hashes, not a blanket “approve D writes”.

A service-only payload can be prepared after its report and marker are bound. It must
name the actual report, scope and degraded capabilities. It must not ask the operator
to approve unknown future payloads. The field package must also name its exact
notification and tracker readback mechanisms and preserve returned identities.

Triage gates, recovery bundles and live state were not opened for discovery here.
The inbox-budget reminder is handled as a scope signal only: the completion plan says
“An inbox budget warning does not authorize a sweep, tracker payload or archive
change.” The [triage skill](../.agents/skills/triage-friction-log/SKILL.md) delegates
to the [shared workflow](../docs/agentic-dev-kit/workflows/triage-friction-log.md),
whose `tracker-without-exact-payload-approval` policy prohibits create/update/comment.
Preparation therefore stops at this concrete scope decision. Existing parked entries
are not silently included in the proposed implementation work.

## Stops, retention and exit

Stop the affected route on unexplained source/config/ref drift, partial engine sets,
invalid or foreign artifact identity, unexpected write destinations, missing required
capabilities, ambiguous external results, uncertain process ownership, new actionable
findings outside scope or failed required verification. Preserve the checkpoint and
propose a bounded amendment; continue independent authorized preparation only.

Rollback means stop and retain the isolated candidate/state/evidence. No deletion of
old evidence, cleanup of retained workspaces, force-push, issue closure, review dismissal,
profile overwrite or production-state reset is included. No global Codex configuration
change is authorized by this proposal. A necessary trust modification needs a concrete
amendment before launch.

Phase 5 E remains a separate evidence audit and operator exit decision. D's engines,
service routes and recovery rows must each have applicable evidence or an explicitly
approved acceptance amendment. Required-but-blocked, proposed or synthetically covered
live routes are not completion of the original contract.

This preparation changes only its new proposal/evidence namespace. A broad B artifact
scan failed on an unreadable historical test artifact before publishing its preservation
snapshot; the failure is retained in
[preparation limitations](../state/review-evidence/phase5-d-preparation-20260921/preparation-limitations.json).
`collect.py baseline` in the kit cwd at `db1e84ec069b545ada7c722184a3d62f52a5ac1f`
on 2026-09-21 found no changes to the sealed records and pre-existing saved plans
named by C's checkpoint. It also captured the durable C bundle for endpoint comparison.
This bounded check does not establish preservation of the full B artifact tree,
intervening actor attribution or transitive custody. No implementation or repository
test-suite result is claimed here.

The route-analysis delegation requested GPT-5.6 Sol / medium through the launcher.
No independent runtime model/effort attestation was exposed; the preparation record
does not represent the request as an attested rollout or claim a coordinator switch.
