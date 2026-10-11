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
  `vcs.triage_branch_pattern` after documented substitution: `{date}` for today's
  ISO date, and, when the pattern carries it, `{session}` for the first 8
  characters of the run's own `run_identity.session`. `{session}` may appear at
  most once and never directly against `{date}`. A pattern without `{session}`
  keeps the same-day collision risk two sessions can hit.
- `<tracker>`, `<notify>`, and `<state-dir>` mean the configured `tracker`, `notify`,
  and `state.dirname` sections.
- `<triage>` means the complete `triage` section: `triage.analysis_tier`,
  `triage.state_path`, `triage.gate_path`, `triage.recovery_bundle_pattern`,
  `triage.frozen_inbox_pattern`, `triage.report_root`, `triage.report_pattern`,
  `triage.draft_engine`, `triage.finalize_engine`, `triage.commit_subject`, and
  `triage.pr_draft`.
- A workflow invocation means `/triage-friction-log` in Claude Code or
  `$triage-friction-log` in Codex.

Validate every named key before reading or writing an artifact. Missing keys are a hard
stop that tells the operator to refresh `init.sh` and rerun `./init.sh --no-clobber`.
Never substitute a shipped default in memory: the merged config is the effective
contract.

`triage.analysis_tier` must name a key under `models.tiers`. Apply a runtime mapping
only when the current runtime mechanically exposes that control; otherwise label it
instructed guidance. `triage.pr_draft` must be `false`: this workflow completes the
proposed patch before pull-request creation, so it has no material unfinished-work
window that must already exist remotely. A `true` value hard-stops before any artifact
or forge write instead of manufacturing a draft window. Engine names and the commit
subject are non-empty strings. Each engine name is a relative path fragment with no `..`
component. Resolve it beneath the canonical `<engine-dir>` and require any existing
target to remain canonically contained there, including through symlinks, and to be a
regular file. An absolute, traversing, escaping, or non-regular engine target hard-stops
before engine-mode selection. Artifact patterns are non-empty repository-relative paths.
`triage.state_path` and `triage.gate_path` contain `{mode}`;
`triage.recovery_bundle_pattern` contains
`{mode}` and `{gate_digest}`; the frozen-inbox and report patterns contain
`{mode}`, `{date}`, and `{session}`. `gate_digest` is the lowercase SHA-256 digest of
the exact complete gate bytes. Live and test state, gates, and recovery bundles must
resolve to different paths. The state, gate, recovery bundle, and frozen snapshot are
logical
`state.dirname` paths; the report is a child of `triage.report_root`, which is neither
empty nor the repository root.

Resolve state reads and writes through `<engine-dir>/lib/state_paths`. State and frozen
snapshots are own-session evidence, not the shared cache surface: resolve every read
and non-creating preflight with `resolve_write_path(fragment, mkdir=False)`, and resolve
every write with `resolve_write_path(fragment)`. Never use `resolve_read_path` for
either artifact; its newer-of sandbox/production cascade can import another session's
approval authority. Require
`state.dirname` to match that resolver's declared `STATE_DIRNAME`; a mismatch hard-stops
because the resolver does not take the directory from config. Require the matching
lexical prefix on `triage.state_path`, `triage.gate_path`,
`triage.recovery_bundle_pattern`, and `triage.frozen_inbox_pattern`, remove it, then pass
only the remaining fragment to the resolver. Honor `DEVKIT_STATE_ROOT` and
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

Validate only the syntactic entry keyword before capability probing: an unknown or
combined keyword hard-stops immediately. For a recognized live or test entry, resolve
the repository/config and shared-state prerequisites, then attempt to acquire and hold
the mode-specific single-writer gate before observing state or recovery-artifact
presence, reading either artifact, or resolving any state-bearing predicate in this
matrix. A successful acquisition keeps every such observation under that gate. Only an
interactive `recover` or `test` whose acquisition fails on a complete blocking gate may
use the bounded stale-gate classifier: capture the complete gate and its filesystem
observations, prove its owner terminated, compute `gate_digest` from those exact gate
bytes, then non-creatingly resolve and capture the exact mode-specific state path and
the one `triage.recovery_bundle_pattern` candidate for that mode and gate digest,
with filesystem observations for both. Parse the captured bundle candidate first. A
valid matching state-present test held bundle selects `held-evidence`. A valid matching
`gate-only-prepared` or `test-gate-only-prepared` bundle permits only a bounded
prepared-transition check on the captured state copy. The bundle is a canonical
envelope containing a `prepared_core`, its SHA-256 digest, exact approval bound to that
core digest, the deterministically derived intended intent payload, and that payload's
digest. The core contains the old-gate capture, configured bundle path, repository
identity, repeated absence observations, mode, and every intended-intent field except
`prepared_core_digest`; it contains no approval, intent payload, intent digest, or full
bundle digest. The intended intent adds only `prepared_core_digest` to those declared
intent fields and never contains or binds the full bundle digest. The approval record
must carry the exact approving decision, approval source, and approver identity, all
bound to `prepared_core_digest`; missing, refused, or altered approval is not authority.
Captured state must be
absent or byte-identical to that intended same-mode intent. Absence resumes at exclusive
intent publication after revalidation; a matching intent resumes its recorded
transition. A valid matching `state-present-capture` or `state-present-prepared` bundle
selects only the bounded state-present transition declared below; it never falls through
to an ordinary state parse. Every prepared or held state-present envelope carries the
complete immutable `capture_core` byte-for-byte plus `capture_core_digest`; a prepared
envelope also carries `action_core`, `action_core_digest`, and an exact approval record
whose approving decision, source, and approver identity bind that action-core digest.
The action core's capture-core digest and old-gate digest must equal the embedded
capture core's verified values. A missing, refused, altered, cross-core, or
digest-mismatched core or approval stops operator-held. Any other state stops
operator-held. A valid ordinary non-held recovery
bundle stops operator-held without an ordinary state parse because it is evidence, not
resume authority. A malformed, foreign, or digest-mismatched candidate also stops
operator-held without parsing state. Every held result preserves bundle, gate, and state
byte-identically. Only when the current-gate bundle candidate is absent, parse the captured
state copy to classify ordinary state, absence, or a mode-specific recovery intent or held receipt. A valid
mode-specific intent derives the configured bundle candidate from its recorded old-gate
digest and mode, not from a replacement gate; resolve only that exact candidate and
digest-check it against the intent. Test classification stays inside the test state root and never
reads a live state, receipt, intent, or bundle. An active or uncertain owner stops
operator-held before the state-path capture; the classifier never changes an artifact or
resolves unrelated capabilities. The
scheduled or unattended `recover` row is the other explicit exception: execution
context and the recognized keyword select it without acquiring the gate or observing
state. Resolve the remaining capability-dependent predicates only after the entry/state
row is selected. This matrix declares required outcomes; it never authorizes any other
pre-gate state observation.
Here, `valid active state` means an ordinary live-run state, never a gate-only recovery
intent or held receipt.

| Input or state | Required result |
|---|---|
| Unknown or combined entry keyword | Hard-stop before capability probing or writes. |
| No argument, neither active state nor gate-only receipt | Start a new live draft. |
| No argument, valid `completed` live state | Under the held gate, retire the completed state (*Completed-state retirement*, in `recovery.md`), then start a new live draft. |
| No argument, valid active state in any other phase | Resume the recorded phase and mode. |
| `resume`, neither valid active state nor gate-only receipt | Hard-stop without an external write. |
| `resume`, valid active state | Resume the recorded phase and mode; never replace the active session. A `completed` state reports its completed receipt without mutation. |
| `new`, neither active state nor gate-only receipt | Start a new live draft. |
| `new`, valid `completed` live state | Under the held gate, retire the completed state (*Completed-state retirement*, in `recovery.md`), then start a new live draft. |
| `new`, active live state in any other phase | Refuse; never overwrite an approval-bound session. |
| Interactive `recover`, active live state and no blocking gate | Under the single-writer gate, capture raw bytes and filesystem observations before parsing the captured copy; valid state then refuses and directs to `resume`, while invalid state enters recovery. Recovery never authorizes a tracker, source, or forge write. |
| Interactive `recover`, blocking gate without a gate-only receipt | Capture the complete published gate and its filesystem observations; prove owner termination and require exact operator approval before quarantining the unchanged gate, whether or not active state exists. When state is absent, publish a blocking `gate-only-recovery-intent` before gate quarantine; never infer safe restart. |
| Interactive `recover`, blocking gate with a valid matching `gate-only-prepared` bundle and captured state absent | Revalidate the unchanged old gate and repeated state absence, then exclusively publish the bundle's exact approved intent payload; never reconstruct another payload. |
| Interactive `recover`, blocking gate with a valid matching `state-present-capture` or `state-present-prepared` bundle | After proving owner termination, resume only the declared state-present recovery transition from the exact captured bytes and observations; require the recorded action-specific approval before its disputed mutation. A live or uncertain owner stays operator-held with every artifact preserved. |
| Interactive `recover`, blocking gate with a valid ordinary non-held, malformed, foreign, or digest-mismatched current-gate recovery bundle | After proving owner termination, preserve bundle, gate, and state byte-identically; report operator-held without an ordinary state parse or treating the bundle as resume authority. |
| Interactive `recover`, `gate-only-recovery-intent` present | Resume only the recorded bundle and digest-checked gate-only transition; never restart or reconstruct the draft. |
| Interactive `recover`, no active live state, gate, or gate-only receipt | Hard-stop without creating a recovery bundle or performing an external write. |
| Non-recover live invocation with a gate-only intent | Preserve the intent and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Any live invocation with a gate-only held receipt | Preserve the receipt, quarantined gate, and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Scheduled or unattended `recover` | Report operator-held without acquiring the single-writer gate, capturing state, or changing an artifact. |
| `test`, no test state, test gate, or test recovery receipt | Start a test draft with test identity and test state; never read, replace, or resume live state. |
| `test`, valid `completed` test state and no blocking test gate | Under the held test gate, retire the completed test state (*Completed-state retirement*, in `recovery.md`), then start a new test draft; never read, replace, or resume live state. |
| `test`, valid test state in any other phase and no blocking test gate | Resume only that test state; never read, replace, or resume live state. |
| `test`, `test-recovered-safe-to-restart` receipt and no blocking test gate | Under the test gate, verify the receipt and bundle, parse the current inbox, then digest-check and replace only that receipt with the reserved new test state. Preserve the receipt if parsing or replacement fails. |
| Interactive `test`, blocking test gate, no held bundle, and owner active or uncertain | Preserve the gate and any test artifact byte-identically; report operator-held without writing a bundle or intent. |
| Interactive `test`, blocking test gate, no held bundle, proven-dead owner, and exact capture approval pending, refused, or unavailable | Preserve the gate and any test artifact byte-identically; report operator-held without writing a bundle or intent. |
| Interactive `test`, blocking test gate with no test state, safe-restart receipt, intent, or held bundle, plus proven-dead owner and exact capture approval | Publish `test-gate-recovery-intent` before quarantining the unchanged gate. |
| Interactive `test`, `test-gate-recovery-intent` present and no held bundle | Resume only the recorded test-gate transition and finish `gate-only-operator-held` with test-confined evidence; never select a live path or infer safe restart. |
| Interactive `test`, blocking test gate with valid test state, no held bundle, proven-dead owner, and exact capture approval | Write one durable state-present test-gate held bundle from the complete gate plus exact state bytes and observations, then report operator-held. Never quarantine the gate, acquire a replacement, or resume or replace state. |
| Interactive `test`, blocking test gate with invalid test state, no held bundle, proven-dead owner, and exact capture approval | Write the same held-bundle shape from the complete gate plus exact invalid-state bytes and observations, then report operator-held. Never quarantine the gate or state and never publish a restart receipt. |
| Interactive `test`, blocking test gate with `test-recovered-safe-to-restart` receipt, no held bundle, proven-dead owner, and exact capture approval | Write the same held-bundle shape from the complete gate plus exact receipt bytes and observations, then report operator-held. Never quarantine the gate or replace the receipt. |
| Any `test` with a state-present test-gate held bundle | Preserve the bundle, gate, and test artifact byte-identically and report operator-held. The bundle is terminal evidence, not resumable mutation authority, and never selects a live path. |
| Interactive `test`, invalid test state and no blocking test gate | Under the test gate, capture and preserve the exact test-state evidence, derive the invalid-state action core, persist its complete canonical prepared envelope with exact action-core-bound operator approval, revalidate before quarantine, and write `test-recovered-safe-to-restart`; prohibit live-state and external writes. |
| Scheduled or unattended `test`, invalid test state | Report operator-held without changing test or live artifacts. |
| Scheduled or unattended `test`, blocking test gate or test-gate intent | Report operator-held without changing test or live artifacts. |
| Scheduled or unattended non-recovery invocation with active state | Resume or report operator-held; never start another draft. |
| Both configured engines present | Select engine-backed mode and persist it. |
| Both configured engines absent | Select LLM-only mode and label its work agent-executed. |
| Only one configured engine present | Hard-stop before artifact or external write. |
| Interactive invocation with notification unavailable | Present exact payloads in-session and persist exact decisions; record degradation. |
| Scheduled or unattended invocation with notification unavailable | Hard-stop before creating a new approval session; preserve an existing session as operator-held. |
| Missing, malformed, or identity-mismatched live frozen snapshot/state outside `recover`, other than a `completed` state a session-starting entry retires across a configuration change (*Completed-state retirement*) | Hard-stop before tracker writes; name `recover` as the safe interactive transition; after an attempted or verified write, preserve operator-held evidence and never whole-sweep. Test-state remediation stays on the isolated `test` entry. |
| Tracker or finalization write fails or is ambiguous | Read back before retry; unresolved state is operator-held. |
| Test mode | Permit declared local artifacts and optional `[TEST]` notification only; prohibit tracker, source-document, and forge writes. |

## Reference files

This workflow is split so that each of its files fits in a single read. The files below
are part of the workflow and are as normative as this one; a section cited here by name,
or as *above* or *below*, may sit in any of them. **Read every one of them completely,
not in part, before the first action of any run**, whatever its entry, mode or phase.

- [`triage-friction-log/recovery.md`](triage-friction-log/recovery.md) —
  *Completed-state retirement*, *Gate-only input precedence*, *Test input precedence*,
  *State-present held-evidence procedure* and *Invalid-state recovery*.
- [`triage-friction-log/state-schema.md`](triage-friction-log/state-schema.md) — the
  exact state, phase and single-writer gate shapes.
- [`triage-friction-log/finalize.md`](triage-friction-log/finalize.md) — *Tracker writes
  and accounting* and *Finalize and sweep*.
- [`triage-friction-log/engine-cli.md`](triage-friction-log/engine-cli.md) — the
  engines' invocations and outputs.

## Authoritative integration declaration

The capability, authority, artifact, input, gate-only input precedence, test input precedence,
recovery-transition, and completion rows in this workflow and its
reference files are normative. They take precedence over later explanatory prose and
runtime adapters. If a runtime-specific instruction conflicts, stop before the disputed action, record
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
| `state-present-recovery` | `capture-before-parse-prepare-before-mutation-resume-exact-cutpoint` |
| `test-state-recovery` | `preserve-test-evidence-never-touch-live-or-external-state` |
| `test-gate-recovery` | `hold-state-present-or-publish-absent-state-intent-before-quarantine-never-touch-live` |
| `partial-engine-set` | `stop-never-mix-engine-and-llm-artifacts` |
| `unattended-without-notification` | `stop-before-new-approval-session` |
| `tracker-without-exact-payload-approval` | `prohibit-create-update-comment` |
| `approved-payload-changed` | `require-new-exact-payload-approval` |
| `linear-project-mismatch` | `refuse-before-proposal-publication-or-attempt` |
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

The phase-by-phase state shape and the single-writer gate mechanics are in
[`triage-friction-log/state-schema.md`](triage-friction-log/state-schema.md).

Before an external write, atomically persist `attempting` with the exact operation and
payload digest. After response/read-back, atomically persist `verified`, `failed`, or
`ambiguous`. A retry must inspect that state and the destination. Process termination or
a missing final chat summary never authorizes repeating a write.

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
| `successful-completion` | No candidates or no sweep/write was approved, or every approved payload and sweep reached an authoritative terminal state without degradation. | Report actual artifacts and identifiers. Write a durable completed receipt; the next session-starting run retires the completed state. |

### Overall outcome precedence

Select the first matching row and report exactly one overall outcome.

| Precedence id | Condition | Outcome |
|---|---|---|
| `required-or-safety-failure` | A required preflight/state/safety check other than bounded recovery-evidence classification failed before a disputed action, or shared/runtime policy conflicts. | `hard-stop` |
| `gate-only-recovery-held` | A valid `gate-only-recovery-intent` or `gate-only-operator-held` receipt exists. | `operator-held` |
| `state-present-recovery-held` | A valid `state-present-capture` awaits action approval, a `state-present-held` bundle exists, or a prepared state-present transition does not match its exact declared cutpoint. | `operator-held` |
| `test-gate-recovery-held` | A valid `test-gate-recovery-intent` cannot be resumed interactively, or a state-present test-gate held bundle exists. | `operator-held` |
| `recovery-evidence-held` | A valid ordinary non-held, malformed, foreign, digest-mismatched, or prepared-bundle/state-mismatched current-gate recovery bundle exists after owner termination is proven. | `operator-held` |
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

## Linear project guard

A proposal's Linear project must equal the exact merged `tracker.project_name` before
publication and again before approval enters `tracker-write`. A mismatch preserves the
reservation or displayed state without creating an attempted operation.

## Execution context

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

Parse every structurally recognized entry remaining in a dated inbox section,
excluding graduation-marker sections. Do not exclude an entry because its prose
contains a filing, routing or reconciliation annotation. Freeze the exact inbox
bytes before proposing. The snapshot metadata contains the run identity and digest;
the report contains every candidate id, its exact source-block digest, its original
source text presented as literal content, and the proposed tracker payload. Present
every value taken from the inbox, the proposal analysis, configuration or a service
read-back as literal content: multi-line text inside a fence that no line of that text
can close, single-line text inside a code span that no backtick run of that text can
close, and any value containing a non-printable character (other than LF or TAB in
multi-line text) as an escaped representation labelled as such. Never render such a
value as report Markdown. Historical
annotations are evidence for the operator to consider, not executable accounting
instructions. Present the archive and park choices alongside the filing choice.

Before computing proposal digests, classify each proposed ticket and include its
execution-environment section and configured label according to
[`ticket-execution-environment.md`](../ticket-execution-environment.md). Apply this
in engine-backed and LLM-only drafting; the author supplies the metadata, and the
engine's exact-payload binding preserves it without independently verifying the
classification. Never add it after approval or rewrite retained proposals on resume.

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
writes. Otherwise persist the complete `propose` state. An interactive current-session
presentation atomically advances to `awaiting-approval` before presentation. A
scheduled/unattended notification instead appends and persists the exact
`notification-delivery` `attempting` operation before sending; only authoritative exact
thread read-back advances it to `awaiting-approval` with that thread reference.

With notification, send the numbered exact-payload summary, preserve the exact response,
and independently read back the marker-bound message before persisting verified
channel/thread identifiers. A null reference, failed response, or ambiguous response
never authorizes another send without the declared authoritative read-back transition.
Without notification in an interactive run, present the
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

One reply may carry several `approve <ids>`, `archive <ids>` and `park <ids>` commands,
one per line, so a single decision can file some candidates and archive others. Each id
may appear in only one command, and each line is one complete command. `approve all`,
`modify` and `cancel` each cover the whole reply and must be sent alone.
Ids are space-separated, as in `approve TRI-01 TRI-02`; a comma is not a separator,
and a command containing one is refused with that reason.

For an entry already handled, review its retained annotation and referenced evidence
before choosing `archive <ids>`, which files no tracker item. If its disposition is
uncertain, use `park <ids>` or leave it unmentioned. `approve all` approves filing
payloads for every displayed candidate, including historically annotated entries;
it does not mean archive already-handled entries. The engine does not establish a
historical filing from prose alone. An archive decision remains subject to the exact
frozen-block and reviewed-sweep requirements below.

Reject unknown ids, an id named by more than one command, two verbs on one line, blank
or padded lines, substring matches, messages from other identities, or
an approval whose current payload digest differs from the displayed digest. Unmentioned
items default to `park`, never archive. Persist normalized decisions and exact approval
evidence atomically before any tracker capability is triggered.

In an unattended resume with no valid reply, append and persist one exact reminder
`attempting` operation before send, then apply the same response/read-back states as the
initial notification. A retained reminder operation prohibits a second reminder.
Preserve state and report `operator-held`. If the notification path is now unavailable, preserve
state and report the same outcome without pretending the reminder was sent.

## Tracker writes, finalize and sweep

Both are in [`triage-friction-log/finalize.md`](triage-friction-log/finalize.md), read
with the rest of the workflow before the first action.

## Engine CLI

The engines' invocations and outputs are in
[`triage-friction-log/engine-cli.md`](triage-friction-log/engine-cli.md).

## Final output

List every capability with terminal status, then report exactly one overall outcome.
Name the report and frozen snapshot, execution and engine modes, approval source,
verified tracker identifiers, sweep branch/commit/PR and exact head when present,
degraded capabilities, and one safe resume action. Never describe an unavailable source
as empty, a proposed write as completed, an operator-held PR as merged, or an
agent-executed result as engine-verified.
