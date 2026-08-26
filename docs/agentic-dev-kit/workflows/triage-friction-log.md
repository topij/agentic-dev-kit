# Triage friction log

Graduate the friction-log inbox into tracker tickets without weakening the frozen-
inbox, payload-approval, tracker-write, or archive-sweep boundaries. A draft run freezes
the inbox and proposes exact tracker payloads. A later approval/finalize run records
exact operator decisions, verifies every approved tracker write, and opens a reviewable
archive-sweep pull request. The shared declaration below owns policy; Claude and Codex
adapters translate only invocation and available mechanisms.

## Resolve and validate configuration

Resolve the repository root, then read the merged configuration with
`kitconfig.load_config()` so `config/dev-model.local.yaml` overrides the tracked file
per leaf. Do not fall back to the tracked file alone. In this workflow:

- `<friction-log>`, `<friction-log-archive>`, and `<engine-dir>` mean
  `paths.friction_log`, `paths.friction_log_archive`, and `paths.engines`.
- `<protected-branch>` and `<triage-branch>` mean `vcs.protected_branch` and
  `vcs.triage_branch_pattern` after documented date substitution.
- `<tracker>`, `<notify>`, and `<state-dir>` mean the configured `tracker`, `notify`,
  and `state.dirname` sections.
- `<triage>` means the complete `triage` section: `triage.analysis_tier`,
  `triage.state_path`, `triage.frozen_inbox_pattern`, `triage.report_root`,
  `triage.report_pattern`, `triage.draft_engine`, `triage.finalize_engine`,
  `triage.commit_subject`, and `triage.pr_draft`.
- A workflow invocation means `/triage-friction-log` in Claude Code or
  `$triage-friction-log` in Codex.

Validate every named key before reading or writing an artifact. Missing keys are a hard
stop that tells the operator to refresh `init.sh` and rerun `./init.sh --no-clobber`.
Never substitute a shipped default in memory: the merged config is the effective
contract.

`triage.analysis_tier` must name a key under `models.tiers`. Apply a runtime mapping
only when the current runtime mechanically exposes that control; otherwise label it
instructed guidance. `triage.pr_draft` is a boolean. Engine names and the commit subject
are non-empty strings. Each engine name is a relative path fragment with no `..`
component. Resolve it beneath the canonical `<engine-dir>` and require any existing
target to remain canonically contained there, including through symlinks, and to be a
regular file. An absolute, traversing, escaping, or non-regular engine target hard-stops
before engine-mode selection. Artifact patterns are non-empty repository-relative paths.
`triage.state_path` contains `{mode}`; the frozen-inbox and report patterns contain
`{mode}`, `{date}`, and `{session}`. Live and test state must resolve to different
paths. The state and frozen snapshot are logical `state.dirname` paths; the report is a
child of `triage.report_root`, which is neither empty nor the repository root.

Resolve state reads and writes through `<engine-dir>/lib/state_paths`. State and frozen
snapshots are own-session evidence, not the shared cache surface: resolve every read
and non-creating preflight with `resolve_write_path(fragment, mkdir=False)`, and resolve
every write with `resolve_write_path(fragment)`. Never use `resolve_read_path` for
either artifact; its newer-of sandbox/production cascade can import another session's
approval authority. Require
`state.dirname` to match that resolver's declared `STATE_DIRNAME`; a mismatch hard-stops
because the resolver does not take the directory from config. Require the matching
lexical prefix on `triage.state_path` and `triage.frozen_inbox_pattern`, remove it, then
pass only the remaining fragment to the resolver. Honor `DEVKIT_STATE_ROOT` and
`.devkit_state_root`; never write logical state paths directly beneath the worktree.
Preflight with non-creating resolution. Reject absolute fragments,
`..` traversal, path collisions, tracked artifact targets, control-input targets,
non-regular existing targets, escaping symlinks, and existing targets whose link count
is not exactly one. Compare existing targets by device/inode with one another and with
the merged config and source documents. Create parents only after every path check
passes, and publish frozen snapshot, report, and state by atomic replacement.

Generate a fresh opaque `session` id for a new run. Canonicalize the complete effective
configuration as RFC 8785 JSON and hash its UTF-8 bytes with SHA-256 as
`config_fingerprint`. Reject non-string mapping keys, non-JSON scalars, and non-finite
numbers rather than coercing them. Construct a run identity binding repository identity,
`<friction-log>`, protected-branch head, execution mode, session id, and config
fingerprint. Hash the exact frozen inbox bytes separately. State, report, and snapshot
metadata carry the run identity and frozen digest. A resumed run must match every
immutable identity field. The recorded protected-branch head is immutable draft
provenance, not a requirement that the moving protected ref remain equal forever.
Refresh the remote ref read-only on resume: the recorded head must remain an ancestor of
the current protected head. Record the observed current head separately. A non-ancestor,
missing, or unverifiable transition hard-stops before tracker or repository writes.

## Semantic input matrix

Evaluate the input before capability-dependent work.
Here, `valid active state` means an ordinary live-run state, never a gate-only recovery
intent or held receipt.

| Input or state | Required result |
|---|---|
| Unknown or combined entry keyword | Hard-stop before capability probing or writes. |
| No argument, neither active state nor gate-only receipt | Start a new live draft. |
| No argument, valid active state | Resume the recorded phase and mode. |
| `resume`, neither valid active state nor gate-only receipt | Hard-stop without an external write. |
| `resume`, valid active state | Resume the recorded phase and mode; never replace the active session. |
| `new`, neither active state nor gate-only receipt | Start a new live draft. |
| `new`, active live state | Refuse; never overwrite an approval-bound session. |
| Interactive `recover`, active live state and no blocking gate | Under the single-writer gate, capture raw bytes and filesystem observations before parsing the captured copy; valid state then refuses and directs to `resume`, while invalid state enters recovery. Recovery never authorizes a tracker, source, or forge write. |
| Interactive `recover`, blocking gate without a gate-only receipt | Capture the complete published gate and its filesystem observations; prove owner termination and require exact operator approval before quarantining the unchanged gate, whether or not active state exists. When state is absent, publish a blocking `gate-only-recovery-intent` before gate quarantine; never infer safe restart. |
| Interactive `recover`, `gate-only-recovery-intent` present | Resume only the recorded bundle and digest-checked gate-only transition; never restart or reconstruct the draft. |
| Interactive `recover`, no active live state, gate, or gate-only receipt | Hard-stop without creating a recovery bundle or performing an external write. |
| Non-recover live invocation with a gate-only intent | Preserve the intent and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Any live invocation with a gate-only held receipt | Preserve the receipt, quarantined gate, and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Scheduled or unattended `recover` | Report operator-held without acquiring the single-writer gate, capturing state, or changing an artifact. |
| `test`, no test state, test gate, or test recovery receipt | Start a test draft with test identity and test state; never read, replace, or resume live state. |
| `test`, valid test state and no blocking test gate | Resume only that test state; never read, replace, or resume live state. |
| `test`, `test-recovered-safe-to-restart` receipt and no blocking test gate | Under the test gate, verify the receipt and bundle, parse the current inbox, then digest-check and replace only that receipt with the reserved new test state. Preserve the receipt if parsing or replacement fails. |
| Interactive `test`, blocking test gate without test state or intent | Capture the complete test gate, prove owner termination, require exact approval, and publish `test-gate-recovery-intent` before quarantining the unchanged gate. |
| Interactive `test`, `test-gate-recovery-intent` present | Resume only the recorded test-gate transition and finish `test-recovered-safe-to-restart`; never select a live path. |
| Interactive `test`, blocking test gate with valid test state | Capture the complete gate plus exact state bytes and observations in a durable state-present test-gate held bundle, then report operator-held. Never quarantine the gate, acquire a replacement, or resume or replace state. |
| Interactive `test`, blocking test gate with invalid test state | Capture the complete gate plus exact invalid-state bytes and observations in the same held-bundle shape, then report operator-held. Never quarantine the gate or state and never publish a restart receipt. |
| Interactive `test`, blocking test gate with `test-recovered-safe-to-restart` receipt | Capture the complete gate plus exact receipt bytes and observations in the same held-bundle shape, then report operator-held. Never quarantine the gate or replace the receipt. |
| Any `test` with a state-present test-gate held bundle | Preserve the bundle, gate, and test artifact byte-identically and report operator-held. The bundle is terminal evidence, not resumable mutation authority, and never selects a live path. |
| Interactive `test`, invalid test state and no blocking test gate | Under the test gate, capture and preserve the exact test-state evidence, require exact operator approval of its digest, revalidate before quarantine, and write `test-recovered-safe-to-restart`; prohibit live-state and external writes. |
| Scheduled or unattended `test`, invalid test state | Report operator-held without changing test or live artifacts. |
| Scheduled or unattended `test`, blocking test gate or test-gate intent | Report operator-held without changing test or live artifacts. |
| Scheduled or unattended non-recovery invocation with active state | Resume or report operator-held; never start another draft. |
| Both configured engines present | Select engine-backed mode and persist it. |
| Both configured engines absent | Select LLM-only mode and label its work agent-executed. |
| Only one configured engine present | Hard-stop before artifact or external write. |
| Interactive invocation with notification unavailable | Present exact payloads in-session and persist exact decisions; record degradation. |
| Scheduled or unattended invocation with notification unavailable | Hard-stop before creating a new approval session; preserve an existing session as operator-held. |
| Missing, malformed, or identity-mismatched live frozen snapshot/state outside `recover` | Hard-stop before tracker writes; name `recover` as the safe interactive transition; after an attempted or verified write, preserve operator-held evidence and never whole-sweep. Test-state remediation stays on the isolated `test` entry. |
| Tracker or finalization write fails or is ambiguous | Read back before retry; unresolved state is operator-held. |
| Test mode | Permit declared local artifacts and optional `[TEST]` notification only; prohibit tracker, source-document, and forge writes. |

### Gate-only input precedence

Resolve this table before ordinary live-state rows. The cases are disjoint by execution
context, entry, and recovery-artifact kind.

| Case id | Context | Entry | Required result |
|---|---|---|---|
| `intent-interactive-recover` | interactive | `recover` | Resume only the exact recorded gate-only transition, whether the old or replacement gate is present. |
| `intent-unattended-recover` | scheduled or unattended | `recover` | Report operator-held without changing an artifact. |
| `intent-other-live-entry` | any live context | no argument, `new`, or `resume` | Report operator-held; preserve intent and bundle. |
| `held-any-live-entry` | any live context | no argument, `new`, `resume`, or `recover` | Report operator-held; preserve receipt, quarantined gate, and bundle. |
| `test-isolated-from-live-recovery` | any context | `test` | Select only the test-state rows without reading or changing a live recovery artifact. |

## Authoritative integration declaration

The capability, authority, artifact, input, gate-only input precedence,
recovery-transition, and completion rows in this document are
normative. They take precedence over later explanatory prose and runtime adapters. If a
runtime-specific instruction conflicts, stop before the disputed action, record
`workflow safety contradiction` when a safe report already exists, and perform no
disputed write.

### Capability contract

Report every capability as `ready`, `degraded`, `stop`, `not-triggered`, or
`operator-held`, with its runtime-native mechanism or actionable reason. Do not claim a
conditional capability ready before its trigger.

| Capability id | Class | Preflight and unavailable behavior |
|---|---|---|
| `repository-config-read` | required | Prove the repository root; read the merged config, protected branch, `<friction-log>`, and `<friction-log-archive>`; and establish caller branch/status. Missing, unreadable, or unsafe input hard-stops before artifact creation. |
| `shared-state-resolver` | required | Resolve `<engine-dir>/lib/state_paths`; prove own-session reads and preflights use `resolve_write_path(fragment, mkdir=False)`, writes use `resolve_write_path(fragment)`, and neither state nor frozen snapshots use the shared-cache `resolve_read_path`; honor the lane sandbox. Unavailability hard-stops before state, snapshot, or report writes. |
| `single-writer-state-gate` | required | Resolve a mode-specific sibling lock file under the same state root. Acquire it by atomically publishing a complete pre-populated owner record at an absent path before observing or changing active state; hold the owner token across every state transition and external-write/read-back sequence; require the expected state digest at act time. An existing, lost, or mismatched lock is operator-held and never permits overwrite, retry, or automatic stale-lock removal. |
| `frozen-inbox-state` | required | Create and later verify atomic state, report, and exact-byte frozen snapshot artifacts bound to one run identity. Missing, malformed, foreign, aliased, or mismatched evidence hard-stops before tracker writes; after a verified write it becomes operator-held and forbids a whole-inbox fallback. |
| `draft-finalize-engine-set` | optional, atomic | Resolve both configured engines under `<engine-dir>`. All present selects engine-backed mode; all absent selects LLM-only mode; a partial pair hard-stops. Persist the selected mode and never switch it during resume. |
| `notification-thread` | conditional by execution context | A scheduled or unattended draft requires notification send and thread read; missing backend, target, credential, or either operation hard-stops before the approval session. Interactive use may degrade to the current session. An existing unattended session whose notification path later fails is operator-held with state intact. |
| `tracker-write-readback` | conditional and payload-approval-gated | Trigger only for approved payloads. Require configured tracker/project access, exact-payload approval, create, and authoritative response or read-back. Unavailable, failed, or unresolved ambiguous writes preserve approval and become operator-held; availability alone never authorizes a write. |
| `forge-pr-write-readback` | conditional | Trigger only after every approved tracker payload is authoritatively accounted for and at least one frozen block is approved for sweep. Create the isolated branch/commit/push/PR and read back exact repository, base, head, draft bit, and staged paths. Failure or unresolved ambiguity is operator-held with state and exact repository evidence intact. |
| `pr-watch` | conditional | Trigger after the sweep PR exists. Run the shared workflow through any required lane wrapper. Unavailability or an unsettled exact head leaves the PR operator-held; it never waives review or authorizes merge. |
| `runtime-compute-selection` | optional enhancement | Apply `models.runtime_mappings` only when the runtime mechanically exposes the control; otherwise retain `triage.analysis_tier` as instructed guidance. |

### Authority contract

| Policy id | Required outcome |
|---|---|
| `unknown-or-combined-argument` | `stop-before-capability-probe` |
| `new-over-active-state` | `refuse-preserve-active-session` |
| `concurrent-state-transition` | `exclusive-reservation-and-digest-checked-replacement` |
| `recover-over-valid-state` | `refuse-and-resume-valid-session` |
| `invalid-state-recovery` | `preserve-before-classify-never-abandon-uncertain-attempt` |
| `state-or-frozen-identity-mismatch` | `stop-before-tracker-write-never-whole-sweep` |
| `protected-branch-advance` | `allow-fast-forward-preserve-draft-identity-hold-divergence` |
| `gate-only-recovery` | `preserve-evidence-publish-intent-before-quarantine-remain-operator-held` |
| `test-state-recovery` | `preserve-test-evidence-never-touch-live-or-external-state` |
| `test-gate-recovery` | `hold-state-present-or-publish-absent-state-intent-before-quarantine-never-touch-live` |
| `partial-engine-set` | `stop-never-mix-engine-and-llm-artifacts` |
| `unattended-without-notification` | `stop-before-new-approval-session` |
| `tracker-without-exact-payload-approval` | `prohibit-create-update-comment` |
| `approved-payload-changed` | `require-new-exact-payload-approval` |
| `ambiguous-external-write` | `read-back-before-retry-or-operator-hold` |
| `partial-tracker-batch` | `hold-before-archive-sweep` |
| `test-mode-external-write` | `prohibit-tracker-friction-archive-branch-commit-push-pr` |
| `archive-sweep-boundary` | `sweep-only-approved-accounted-byte-identical-frozen-blocks` |
| `merged-pr-completion` | `require-merged-final-head-equals-reviewed-head-else-operator-held` |
| `reviewed-head-persistence` | `persist-terminal-exact-pr-watch-head-and-receipt-before-merge` |
| `runtime-policy-override` | `shared-declaration-wins-and-stop` |

### Durable artifacts, resumability, and completion

The report is load-bearing and is written before any external attempt. The state is the
act-time gate. It records the run/config/frozen identities, selected engine mode, exact
canonical proposal payloads and digests, approval source and approver identity,
notification thread reference when used, normalized per-item decisions, attempt state,
verified tracker identifiers and branch/commit/PR identity. Each authoritative PR
read-back may update `observed_pr_head`. Only terminal exact-head review evidence plus a
matching authoritative read-back sets `reviewed_head` and its PR-watch receipt. Never record an external
identifier not returned authoritatively or verified by read-back.

Before an external write, atomically persist `attempting` with the exact operation and
payload digest. After response/read-back, atomically persist `verified`, `failed`, or
`ambiguous`. A retry must inspect that state and the destination. Process termination or
a missing final chat summary never authorizes repeating a write.

Every live or test mode has one single-writer gate file beside its active state path.
Prepare a complete owner record in a unique same-directory temporary file: opaque owner
token, run identity when allocated, host, process identifier, process-start observation,
and creation time. Flush the file, then acquire the absent gate with an atomic hard-link
publication of that inode; a pre-existing destination loses without replacement. The
published gate therefore never exists without its complete owner record. Flush the
directory, then unlink the temporary name. Process loss before publication leaves no
gate; process loss after publication leaves a complete gate, even when its temporary
name is still linked. Recovery verifies and quarantines every name for that inode rather
than treating the transient extra link as unknown authority.

Acquire the gate before testing state presence, reading state for a transition, or
parsing a new inbox. Parse under the held gate before creating the `reserved` state. If
parsing fails before reservation, prove the active state remains absent and that no run
artifact or external write occurred, then release only the matching gate and hard-stop
without state. After successful parsing, a new run claims the absent state path with
exclusive creation of a minimal `reserved` record while still holding the gate; it never
publishes its first state by replacement over an expected absence. The only non-absent
new-run claim is a digest-checked replacement of an exact
`recovered-safe-to-restart` or `test-recovered-safe-to-restart` receipt whose recovery
bundle remains present. Every later
transition reads the current bytes under the gate and records their digest, then
immediately before atomic replacement requires the same digest, run identity, and gate
owner token. A mismatch stops operator-held without replacing either version.
The gate-only intent has no live-run identity or new gate owner token. Its sole permitted
replacement is the digest-checked gate-only finalization below, which verifies the
bundle digest, repository identity, and newly acquired gate token before adding that
token to the held receipt.

Hold the gate across an external create and its authoritative read-back so a second
invocation cannot act on `attempting` concurrently. On normal or handled-failure
teardown, release only a gate whose owner token still matches and only after the terminal
or held state is durable, except for the proven pre-reservation parse-failure path above.
Process loss leaves the gate and state as operator-held. Never
delete or steal an unknown gate: interactive `recover` must first capture its exact
bytes and filesystem observations, prove the recorded owner is no longer executing,
obtain exact operator approval of that capture digest, and quarantine the unchanged gate
before acquiring a new recovery gate. Uncertain ownership remains operator-held.

| Outcome | Condition | Required result |
|---|---|---|
| `hard-stop` | A required preflight, state/frozen safety check, engine atomicity check, or shared/runtime policy check fails before the disputed action. | Name the failed capability and remediation; preserve every pre-existing artifact and perform no disputed write. |
| `operator-held` | Approval is pending; a triggered tracker, repository, review, or unattended-notification capability is unavailable; an attempted write remains failed or ambiguous after read-back; a merged PR's final head is missing or mismatched; or gate-only recovery cannot establish prior state. | Preserve exact state, report, recovery bundle, payload digests, verified identifiers, and repository/PR evidence; name the safe operator action and do not sweep or delete state. |
| `degraded-success` | Every required and triggered write completed authoritatively, but an optional interactive notification or runtime-compute enhancement was unavailable. | Report completed durable artifacts and the degraded capability; never use degradation to mask an unresolved required write. |
| `successful-completion` | No candidates or no sweep/write was approved, or every approved payload and sweep reached an authoritative terminal state without degradation. | Report actual artifacts and identifiers. Write a durable completed receipt before optionally removing active state. |

### Overall outcome precedence

Select the first matching row and report exactly one overall outcome.

| Precedence id | Condition | Outcome |
|---|---|---|
| `required-or-safety-failure` | A required preflight/state/safety check failed before a disputed action, or shared/runtime policy conflicts. | `hard-stop` |
| `gate-only-recovery-held` | A valid `gate-only-recovery-intent` or `gate-only-operator-held` receipt exists. | `operator-held` |
| `test-gate-recovery-held` | A valid `test-gate-recovery-intent` cannot be resumed interactively, or a state-present test-gate held bundle exists. | `operator-held` |
| `approval-or-triggered-write-not-terminal` | Approval is pending or a triggered notification, tracker, repository, or review path lacks an authoritative terminal state. | `operator-held` |
| `optional-degradation-after-terminal-work` | Required and triggered work is terminal, but an optional interactive notification or compute enhancement degraded. | `degraded-success` |
| `all-triggered-contracts-terminal` | No prior row matches and every triggered capability is terminal. | `successful-completion` |

## Entry points and context

Accept exactly one of `resume`, `new`, `recover`, or `test`, or no argument. `test` starts a new
test draft or resumes the separate test state; it never selects live state. No argument
resumes valid live state when present and otherwise starts a live draft. `new` refuses
when live state exists. `resume` requires valid live state. `recover` is interactive and
requires an active live-state file or a blocking live gate; it does not decide whether
state is valid until after raw capture. Scheduled or unattended recovery holds without
changing an artifact.

## Invalid-state recovery

Recovery is a state-preservation transition, not approval to discard a session or repeat
an external write. Acquire the mode's single-writer gate before state capture. If an
existing gate blocks acquisition, capture its complete owner record, every same-inode
temporary name, and filesystem observations before following the stale-gate recovery
rule above; this route remains available when active state is absent. Never remove the
gate first. When active state is absent, the immutable capture also records repeated
non-creating resolution and filesystem observations proving that absence. After proving
owner termination and obtaining exact operator approval of the bundle digest,
atomically claim the absent state path by exclusive creation of a
`gate-only-recovery-intent` that binds the bundle digest, old gate owner record,
approved capture, absence observations, and repository identity. Flush that intent and
its directory before revalidating and quarantining every unchanged name for the old
gate. The durable intent is the blocking state if the process stops or another
invocation arrives after quarantine. Acquire a new recovery gate, re-prove state
absence apart from the exact intent, then digest-check and atomically replace the intent
with a `gate-only-operator-held` receipt that adds quarantine paths and the new gate
owner token. Release the new gate only after that receipt is durable. This terminal recovery result
does not create a restart receipt, make `new` available, or infer that no external
attempt occurred; every later invocation preserves it as operator-held. The gate-only
route does not enter the raw-state capture path below.

### Gate-only recovery transition

| Gate-only step | Required state transition |
|---|---|
| `capture-old-gate` | Old gate present, active state absent; persist the immutable evidence bundle and exact approval. |
| `publish-recovery-intent` | Old gate still present; exclusively create and flush `gate-only-recovery-intent`. |
| `quarantine-old-gate` | Intent present; revalidate and quarantine every unchanged old-gate name. |
| `acquire-recovery-gate` | Intent present; atomically acquire a new complete recovery gate. |
| `finalize-held-receipt` | New gate present; digest-check and atomically replace intent with `gate-only-operator-held`. |
| `release-recovery-gate` | Held receipt durable; release only the matching new recovery gate. |

Otherwise, locate active state in its own sandbox with
`resolve_write_path(fragment, mkdir=False)` and inspect the path itself without parsing
its content. Reject a symlink, non-regular file, or link count other than one. Before
validity classification, rename, or repair, atomically create a unique initial recovery
bundle under that same resolved state root. Its immutable capture contains the exact raw
state bytes, their SHA-256 digest, the active path, repository identity, and the path's
device, inode, mode, link count, size, and modification time observed around the read;
changed observations abort the capture and leave the active file untouched.

Parse and validate only the captured bytes, never the still-live path. Append the parse
result and current and recorded identities when readable to the recovery journal. For
each report or frozen-snapshot path obtained from validated captured fields, apply the
same path, alias, and atomic-read checks before appending exact paths, bytes/digests, and
filesystem observations. Never follow an unvalidated path from malformed state;
unresolved artifacts are named as unresolved. If the captured state is valid, record
that result, leave the active state byte-identical, refuse recovery, and direct the
operator to `resume`. Only an invalid captured state proceeds to recovery
classification.

Classify conservatively. Only a readable state that proves it never reached
`attempting` and contains no verified tracker identifier or repository/PR evidence may
offer `abandon <recovery-bundle-digest>` to the present interactive operator. Persist
that exact approval in the bundle. Immediately before quarantine, while holding the
same gate, re-read and re-stat the active path and require its digest, device, inode,
mode, and link count to equal the captured observations. Atomically rename that exact
source to a unique quarantine path, then leave a `recovered-safe-to-restart` receipt;
any mismatch is operator-held and creates no receipt. A later new draft may replace only
that receipt under the same gate. The bundle, quarantined bytes, and receipt remain
durable.

If any external attempt or verified identifier is present, or absence of either cannot
be proved from readable evidence, abandonment is prohibited. Persist an
`operator-held` recovery receipt without moving or deleting the active bytes. Reconcile
only with authoritative tracker/forge read-backs keyed by the preserved exact marker,
payload digest, returned identifier, repository, branch, and head evidence. A
reconstructed state must preserve all verified and ambiguous operations and requires
exact operator approval of its recovery-bundle digest before it can replace the invalid
active state. Recovery itself performs no tracker create, update, or comment, no source
edit, and no branch, commit, push, PR, or merge. When evidence cannot be reconciled,
keep the recovery bundle and active state operator-held and name the missing evidence;
never make `new` available by manual deletion.

### Isolated test-state recovery

The `test` entry resolves only the test state, test gate, and test artifacts; it never
reads or changes a live path. When interactive `test` finds invalid test state, acquire
the test gate and atomically capture its exact raw bytes, digest, path observations,
test identity, and resolved test artifacts in a test recovery bundle before parsing.
Do not follow an unvalidated captured path. Require exact in-session operator approval
of the bundle digest, then immediately re-read and re-stat the test state and require
the captured digest, device, inode, mode, and link count. Atomically quarantine only
that unchanged test-state file and write `test-recovered-safe-to-restart` under the
same test gate. A later `test` invocation may digest-check and replace only that receipt
after successfully parsing the current inbox under the test gate; a parse or act-time
digest failure preserves the receipt. The transition never reads or writes live state, notification
approval, tracker, source documents, archive, branch, commit, push, PR, or merge.
Unknown test-gate ownership remains operator-held under the same capture, owner-death,
and exact-approval rule, confined to test paths. When a proven-dead owner left test
state or a safe-restart receipt, capture the unchanged gate and artifact in a unique
state-present test-gate held bundle, then stop operator-held. Without a crash-released
exclusive recovery primitive, neither engine-backed nor LLM-only execution may claim
that separate gate, state, and bundle files form one atomic transition. The held bundle
is evidence only: it never authorizes quarantine, replacement, restart, or a live path.
When test state is absent, capture that absence in the test recovery bundle, exclusively create and flush
`test-gate-recovery-intent` while the old test gate still exists, then follow the
Gate-only recovery transition ordering with test-confined paths. Quarantine the old
test gate only after the intent is durable; finish by replacing the intent with
`test-recovered-safe-to-restart` under the replacement test gate. A later interactive
`test` resumes only the recorded absent-state intent; a state-present held bundle remains
terminally operator-held. Scheduled or unattended `test` with invalid state, a blocking
gate, recovery intent, or held bundle preserves everything operator-held and performs
no recovery mutation.

Classify execution as interactive or scheduled/unattended from the actual invocation,
not a branch name or worktree path. Non-interactive runs never wait for input. A
scheduled draft with an active session resumes the held cycle or sends the documented
reminder; it never overwrites state.

## Preflight and engine mode

Complete every required preflight before creating parents or artifacts. Resolve both
engine paths. On a new run, all present selects engine-backed mode and all absent selects
LLM-only mode. In LLM-only mode the runtime performs the same parse, frozen snapshot,
proposal, accounting, and finalization contract and labels each such result
`agent-executed`, never `engine-verified`. A partial set is a hard stop. On resume, the
persisted mode is authoritative; a run never changes modes merely because files appeared
or disappeared. Engine-backed resume requires the recorded engine set to remain usable.

Before draft, resolve notification according to context. Scheduled/unattended work needs
send and thread-read readiness plus the exact operator target from merged `notify`
configuration. Interactive notification is optional because the current session can
carry the decision; missing notification is recorded as degraded, not silently omitted.
Tracker readiness may remain `not-triggered` during drafting, but the report must say
that finalization has not been proven.

## Draft session

Parse every active inbox entry by presence, excluding only graduation markers and
already-accounted tracker entries. Freeze the exact inbox bytes before proposing. The
snapshot metadata contains the run identity and digest; the report contains every
candidate id, its exact source-block digest, and the proposed tracker payload.

Build the idempotency marker without a recursive digest. First canonicalize
`{title, body_without_marker, project, labels}` and hash it as `payload_core_digest`.
The non-rendering marker binds session id, candidate id, and that core digest. Append the
marker to the body, then canonicalize the final `{title, body, project, labels}` and hash
it separately as `payload_digest`. State and report store both digests; exact-payload
approval binds the final digest, and marker read-back uses the core digest before
requiring the complete final payload to match. The marker is therefore part of the exact
payload the operator reviews without attempting to hash a digest into itself. In
engine-backed mode invoke `triage.draft_engine`; in LLM-only mode draft with the
configured analysis tier and record `agent-executed`.

If parsing fails under the held gate before reservation, follow the proven
pre-reservation teardown and hard-stop without state. If there are no candidates, write the report
and complete without notification, approval state, tracker, source-document, or forge
writes. Otherwise
atomically write state in `awaiting-approval` before presenting proposals.

With notification, send the numbered exact-payload summary and persist the returned
channel/thread identifiers. Without notification in an interactive run, present the
same exact payloads in the current session. State, not the chat response or DM alone,
is resume evidence.

## Approval session

Accept decisions only from the configured operator identity or the present interactive
operator. Parse complete commands, never keyword substrings. Supported commands are:

- `approve <ids>` or the exact command `approve all` — approve the displayed payload
  digests;
- `archive <ids>` — archive those source blocks without filing tracker items;
- `park <ids>` — keep those source blocks active for a later triage pass;
- `modify <id>: <replacement body>` — create a new payload digest, re-present the full
  payload, and leave it unapproved until a later `approve <id>`;
- the exact command `cancel` — cancel the batch and keep every source block active.

Reject unknown ids, mixed verbs, substring matches, messages from other identities, or
an approval whose current payload digest differs from the displayed digest. Unmentioned
items default to `park`, never archive. Persist normalized decisions and exact approval
evidence atomically before any tracker capability is triggered.

In an unattended resume with no valid reply, send one reminder when possible, preserve
state, and report `operator-held`. If the notification path is now unavailable, preserve
state and report the same outcome without pretending the reminder was sent.

## Tracker writes and accounting

Trigger tracker access only for approved items. Recompute the payload digest and compare
it with the approval record before any tracker action. Search for the exact idempotency
marker and record the complete pre-existing match set. One authoritative pre-existing
exact payload match records `verified` with its read-back identifier without a create.
Any multiple or non-exact marker match is ambiguous and stops operator-held. Only an
authoritative empty match set permits persisting `attempting` and calling create. After a
success response, read back the item and require exact project, title, body, labels,
marker, and returned identifier before recording `verified`.

If the create fails or returns ambiguously, read back by the exact marker before any
retry. One exact payload match verifies the write. No match proves no landing only when
the tracker read is complete and authoritative; multiple or non-exact matches remain
ambiguous. Preserve state and stop operator-held. Continue to later creates only after
the current item is verified; never turn a partially attempted batch into an archive
sweep. Every approved proposal must be verified or the batch remains held.

Test mode performs the readiness and approval checks but never calls a tracker create,
update, or comment operation. It records `would-create` in test state and report; that
record is not live approval and cannot be resumed as live.

## Finalize and sweep

Finalize only after every approved tracker payload is verified. The sweep set is the
union of verified-filed items and items explicitly decided `archive`. Parked,
unmentioned, canceled, failed, ambiguous, and window-added items are never in that set.
Re-read the current inbox and require every proposed sweep block to be byte-identical to
its frozen block. An edited approved block is operator-held; do not archive a stale
snapshot or widen to the whole inbox. Window-added blocks stay active verbatim.

Test mode stops after rendering the proposed diff in the report. It does not edit
`<friction-log>` or `<friction-log-archive>` on disk and does not create a branch,
commit, push, or pull request.

In engine-backed mode invoke `triage.finalize_engine` only if it accepts the exact
accounted block set and implements this declaration; an older helper that whole-sweeps
the frozen snapshot is not ready. In LLM-only mode perform the same exact-content
transformation and label it `agent-executed`.

Never switch the caller checkout. Fetch the protected branch, create a fresh isolated
worktree and `<triage-branch>` from its current origin ref, and re-read the destination
documents there. Require the current origin ref to descend from the immutable draft
head, persist it as `finalize_base_head`, and never rewrite the draft run identity. A
permitted fast-forward advance still must pass the byte-identical frozen-block check;
otherwise remain operator-held. Require a clean index, stage only `<friction-log>` and
`<friction-log-archive>`, and prove the staged path set equals that pair exactly. Commit
with `triage.commit_subject`, push, and create the pull request with
`triage.pr_draft`. Read back repository, base, branch, commit, head, draft bit, PR URL,
and changed paths. A failed or ambiguous response triggers read-back before retry and
otherwise remains operator-held.

Run `pr-watch` for the exact head. This workflow never merges the sweep pull request.
When `pr-watch` reports terminal exact-head review evidence, authoritatively read back
the PR and require its current `headRefOid` to equal the head in that evidence. Before
allowing merge, atomically persist that head as
`reviewed_head` with the PR-watch receipt. Any later head movement invalidates the
receipt and requires a new exact-head PR-watch cycle before replacing `reviewed_head`.
When review is unsettled or the operator still owns the merge decision, report
`operator-held` with the PR URL and `observed_pr_head`; name `reviewed_head` only when a
retained terminal receipt establishes it. If terminal evidence exists but PR read-back
is unavailable or mismatched, remain operator-held without changing `reviewed_head`.
On a later resume,
authoritative PR read-back must prove both that the pull request merged and that its final `headRefOid`
equals `reviewed_head` recorded in state, and the retained terminal PR-watch receipt
must still bind that same head. A missing or mismatched final head or receipt is
operator-held; never mark an unreviewed replacement head complete. Only then write
completion to the report and state before optionally deleting active state; the
completed report remains durable.

## Final output

List every capability with terminal status, then report exactly one overall outcome.
Name the report and frozen snapshot, execution and engine modes, approval source,
verified tracker identifiers, sweep branch/commit/PR and exact head when present,
degraded capabilities, and one safe resume action. Never describe an unavailable source
as empty, a proposed write as completed, an operator-held PR as merged, or an
agent-executed result as engine-verified.
