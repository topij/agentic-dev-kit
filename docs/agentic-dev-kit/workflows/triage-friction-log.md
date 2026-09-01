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
| No argument, valid active state | Resume the recorded phase and mode. |
| `resume`, neither valid active state nor gate-only receipt | Hard-stop without an external write. |
| `resume`, valid active state | Resume the recorded phase and mode; never replace the active session. |
| `new`, neither active state nor gate-only receipt | Start a new live draft. |
| `new`, active live state | Refuse; never overwrite an approval-bound session. |
| Interactive `recover`, active live state and no blocking gate | Under the single-writer gate, capture raw bytes and filesystem observations before parsing the captured copy; valid state then refuses and directs to `resume`, while invalid state enters recovery. Recovery never authorizes a tracker, source, or forge write. |
| Interactive `recover`, blocking gate without a gate-only receipt | Capture the complete published gate and its filesystem observations; prove owner termination and require exact operator approval before quarantining the unchanged gate, whether or not active state exists. When state is absent, publish a blocking `gate-only-recovery-intent` before gate quarantine; never infer safe restart. |
| Interactive `recover`, blocking gate with a valid matching `gate-only-prepared` bundle and captured state absent | Revalidate the unchanged old gate and repeated state absence, then exclusively publish the bundle's exact approved intent payload; never reconstruct another payload. |
| Interactive `recover`, blocking gate with a valid matching `state-present-capture` or `state-present-prepared` bundle | Resume only the declared state-present recovery transition from the exact captured bytes and observations; require the recorded action-specific approval before its disputed mutation. |
| Interactive `recover`, blocking gate with a valid ordinary non-held, malformed, foreign, or digest-mismatched current-gate recovery bundle | After proving owner termination, preserve bundle, gate, and state byte-identically; report operator-held without an ordinary state parse or treating the bundle as resume authority. |
| Interactive `recover`, `gate-only-recovery-intent` present | Resume only the recorded bundle and digest-checked gate-only transition; never restart or reconstruct the draft. |
| Interactive `recover`, no active live state, gate, or gate-only receipt | Hard-stop without creating a recovery bundle or performing an external write. |
| Non-recover live invocation with a gate-only intent | Preserve the intent and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Any live invocation with a gate-only held receipt | Preserve the receipt, quarantined gate, and bundle; report operator-held and never start, resume, or reconstruct a draft automatically. |
| Scheduled or unattended `recover` | Report operator-held without acquiring the single-writer gate, capturing state, or changing an artifact. |
| `test`, no test state, test gate, or test recovery receipt | Start a test draft with test identity and test state; never read, replace, or resume live state. |
| `test`, valid test state and no blocking test gate | Resume only that test state; never read, replace, or resume live state. |
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
| Missing, malformed, or identity-mismatched live frozen snapshot/state outside `recover` | Hard-stop before tracker writes; name `recover` as the safe interactive transition; after an attempted or verified write, preserve operator-held evidence and never whole-sweep. Test-state remediation stays on the isolated `test` entry. |
| Tracker or finalization write fails or is ambiguous | Read back before retry; unresolved state is operator-held. |
| Test mode | Permit declared local artifacts and optional `[TEST]` notification only; prohibit tracker, source-document, and forge writes. |

### Gate-only input precedence

Resolve this table before ordinary live-state rows. The cases are disjoint by execution
context, entry, live-state artifact, and live recovery-bundle artifact. `unobserved`
means the row is selected without resolving or reading that live artifact.

| Case id | Context | Entry | Live-state artifact | Live bundle artifact | Required result |
|---|---|---|---|---|---|
| `intent-interactive-recover` | interactive | `recover` | `gate-only-recovery-intent` | matching `gate-only-prepared` | Resume only the exact recorded gate-only transition, whether the old or replacement gate is present. |
| `prepared-interactive-recover` | interactive | `recover` | absent | matching `gate-only-prepared` | Resume only the exact approved prepared transition from intent publication while the old gate and state absence still match. |
| `unattended-recover` | scheduled or unattended | `recover` | unobserved | unobserved | Report operator-held without acquiring the gate or reading or changing an artifact. |
| `intent-other-live-entry` | any live context | no argument, `new`, or `resume` | `gate-only-recovery-intent` | matching `gate-only-prepared` | Report operator-held; preserve intent and bundle. |
| `held-any-live-entry` | any live context | no argument, `new`, `resume`, or `recover` | `gate-only-operator-held` | matching `gate-only-prepared` | Report operator-held; preserve receipt, quarantined gate, and bundle. |
| `test-isolated-from-live-recovery` | any context | `test` | unobserved | unobserved | Select only the test-state rows without reading or changing a live recovery artifact. |

### Test input precedence

Apply this table before the ordinary test-state rows. After owner termination is proven,
the current-gate bundle is evaluated before state. Artifact kinds are exclusive parser
results: `absent`, `valid-state`, `invalid-state`, `safe-restart-receipt`, or
`test-gate-recovery-intent`. `valid-non-held` means an ordinary recovery bundle that
matches the current gate but carries neither a prepared nor state-present held-evidence kind.

| Test case id | Context | Gate | Artifact | Current-gate bundle | Owner/capture authority | Required result |
|---|---|---|---|---|---|---|
| `gated-unattended` | scheduled or unattended | blocking | unobserved | unobserved | not evaluated | Preserve everything and report operator-held without reading an artifact. |
| `held-evidence` | interactive | blocking | any | `held-evidence` | proven dead | Preserve bundle, gate, and artifact; report operator-held with no mutation. |
| `prepared-absent-interactive` | interactive | blocking | `absent` | `test-gate-only-prepared` | proven dead with exact approval recorded | Revalidate gate and absence, then publish only the prepared intent payload. |
| `prepared-mismatch-interactive` | interactive | blocking | `valid-state`, `invalid-state`, or `safe-restart-receipt` | `test-gate-only-prepared` | proven dead with exact approval recorded | Preserve bundle, gate, and artifact; report operator-held without artifact mutation. |
| `bundle-evidence-held` | interactive | blocking | any | `valid-non-held`, malformed, foreign, or digest-mismatched | proven dead | Preserve bundle, gate, and artifact; report operator-held without an ordinary state parse or artifact mutation. |
| `intent-interactive` | interactive | any | `test-gate-recovery-intent` | absent or matching `test-gate-only-prepared` | already recorded | Resume only the recorded absent-state gate transition. |
| `intent-unattended` | scheduled or unattended | any | `test-gate-recovery-intent` | absent | already recorded | Preserve everything and report operator-held. |
| `gated-owner-unready-interactive` | interactive | blocking | unobserved | unobserved | active or uncertain | Preserve gate and artifact; report operator-held without writing a bundle or intent. |
| `gated-owner-unapproved-interactive` | interactive | blocking | `absent`, `valid-state`, `invalid-state`, or `safe-restart-receipt` | absent | proven dead but approval pending, refused, or unavailable | Preserve gate and artifact; report operator-held without writing a bundle or intent. |
| `gated-artifact-approved` | interactive | blocking | `valid-state`, `invalid-state`, or `safe-restart-receipt` | absent | proven dead and exactly approved | Capture one state-present held bundle; report operator-held without gate or artifact mutation. |
| `gated-absent-approved` | interactive | blocking | `absent` | absent | proven dead and exactly approved | Publish the absent-state intent before any gate quarantine. |
| `ungated-valid` | any | absent | `valid-state` | absent | not applicable | Resume only the valid test state. |
| `ungated-safe-restart` | any | absent | `safe-restart-receipt` | absent | not applicable | Execute only the receipt-to-reserved-state route. |
| `ungated-invalid-interactive` | interactive | absent | `invalid-state` | absent | not applicable | Execute only isolated invalid test-state recovery. |
| `ungated-invalid-unattended` | scheduled or unattended | absent | `invalid-state` | absent | not applicable | Preserve everything and report operator-held. |
| `ungated-absent` | any | absent | `absent` | absent | not applicable | Start a new isolated test draft. |

### State-present held-evidence procedure

Only `gated-artifact-approved` may exclusively create and flush the held bundle at
`triage.recovery_bundle_pattern` expanded with test mode and the SHA-256 digest of the
exact complete test gate. The bundle binds that gate digest,
repository identity, test mode, exact artifact bytes and observations, and exact
approval. Once it is durable, a fresh invocation derives the same path from the
still-blocking gate and routing immediately becomes `held-evidence`; no directory scan or
state pointer is required. A `held-evidence` invocation performs no pre-selection or
post-selection write. Every step is report-only:
preserve the bundle, gate, and artifact byte-identically. No later prose may authorize
quarantine, acquire, replace, resume, restart, reconstruct, delete, rename, link, unlink,
create, publish, write, edit, comment, push, or merge for this route.

## Authoritative integration declaration

The capability, authority, artifact, input, gate-only input precedence, test input precedence,
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
| `state-present-recovery` | `capture-before-parse-prepare-before-mutation-resume-exact-cutpoint` |
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

An ordinary active state is canonical JSON with `kind: triage-run-state`,
`schema_version: 1`, and a `phase` selected from:

- `reserved`
- `propose`
- `notification-delivery`
- `awaiting-approval`
- `tracker-write`
- `forge-finalize`
- `archive-sweep`
- `completed`

Every phase has an exact base shape. It retains `mode`, the complete structured
`run_identity`, `gate_owner_token`, `gate_binding`, `state_claim`,
`config_fingerprint`, `frozen_inbox_digest`, `frozen_snapshot`,
`engine_mode`, and array-valued `attempts`, `verified_tracker_identifiers`,
`repository_evidence`, and `pull_request_evidence`. `mode` is `live` or `test` and
equals `run_identity.mode`; `engine_mode` is `engine-backed` or `llm-only`.
`run_identity` has exactly `repository_identity`, `friction_log`,
`protected_branch_head`, `mode`, `session`, and `config_fingerprint`; its repository,
friction-log path, mode, protected head, and config fingerprint equal the frozen run
identity. `gate_owner_token` matches the gate that last claimed this state and the
declared owner-token grammar. `gate_binding` has exactly the configured gate path,
owner token, owner run identity, and digest of the immutable nonrecursive gate-claim
core; it binds the current gate and repeats `gate_owner_token` exactly. Its owner run
identity equals the immutable gate core's value: either the exact state `run_identity`
when allocated before acquisition, or JSON null when the gate was necessarily acquired
before an existing state's identity could be observed. A null gate owner identity never
weakens the binding because the same core also binds repository/config identity, owner
token, host, process identifier, and process-start observation, and its digest is
recomputed from the actual current gate bytes before any phase action. `state_claim` has
exactly `reason`, `previous_gate_binding`,
`current_gate_binding`, `captured_state_digest`, `recovery_bundle_digest`, and
`approval_digest`. Its current binding equals `gate_binding`. An initial exclusive
state create uses `initial-reservation` and JSON null for the previous binding and all
digests. A normal resume first validates the captured prior state independently, then
digest-checks and atomically replaces only its claim and gate binding with the newly
acquired gate; `normal-resume` records the complete prior binding and SHA-256 digest of
the exact captured bytes, with null recovery/approval digests. `approved-recovery`
additionally requires both exact recovery-bundle and approval digests. Its canonical
approval record has exactly the approving decision, source, approver identity, and the
recomputed digest of the exact recovery-bundle bytes; the named bundle digest must equal
`recovery_bundle_digest` before the approval record is hashed as `approval_digest`.
Before accepting either digest, parse the bundle as the complete canonical prepared
recovery envelope and require its kind, run identity, captured state and digest,
previous gate binding, recovery action core, and action-core digest to match the state
being rebound. The approver identity must equal the operator identity established by
the current-session approval source; a non-empty foreign identity is not authority. The old persisted
token is never required to equal the new gate before that transition. A `reserved`
replacement of an exact safe-restart receipt instead uses `live-receipt-restart` or
`test-receipt-restart`. It has JSON-null previous binding, binds the exact receipt bytes
through `captured_state_digest`, binds the exact prepared bundle/envelope and approval
through the other two digests, and binds the newly acquired current gate. The reason
fixes the mode and `receipt-to-reserved` cutpoint; no other phase may carry it. A crash
before replacement leaves the receipt authoritative, while a crash after replacement
resumes the reserved state. No ordinary phase
action is allowed until current gate bytes match the persisted binding.
`config_fingerprint` equals `run_identity.config_fingerprint`.
`config_fingerprint` and `frozen_inbox_digest` are lowercase SHA-256 strings, and
`protected_branch_head` is a lowercase full commit identifier. Reject a missing, extra,
mistyped, non-canonical, foreign, or cross-binding-mismatched base field.
`frozen_snapshot` carries the exact expanded `triage.frozen_inbox_pattern` path,
canonical frozen content plus the exact base64-encoded canonical raw bytes, and a
recomputed digest over those decoded bytes equal to `frozen_inbox_digest`. Strictly
decode and re-encode the bytes, parse the content from them, and require it to equal the
retained structured content before deriving the ordered unique candidate/block index;
the index is never supplied by proposal state. Proposal source authority must match that
independent parsed index.

Each phase has the exact additional keys and validation below; keys owned by a later
phase are forbidden earlier.

- `reserved`: no additional keys; every evidence array is empty.
- `propose`: `proposal_payloads` and `proposal_payload_digests`; payloads are non-empty
  canonical records with exactly `candidate_id`, `payload_core`,
  `payload_core_digest`, `marker`, `payload`, `payload_digest`, `source_block_digest`,
  `source_block`, and `report_binding`. Recompute `source_block_digest` from the exact
  frozen source-block bytes retained in `source_block`. `report_binding` has the exact
  configured report path, canonical report core, and recomputed digest for the shared
  report that displays the complete ordered proposal set. The core binds run and frozen
  identity plus the ordered candidate id, source-block digest, and final payload digest
  for every proposal. Every proposal carries the same batch-level binding, which remains
  part of approval and later sweep authority. The payload core is exactly
  `{title, body_without_marker, project, labels}`; the final payload is exactly
  `{title, body, project, labels}`. Recompute the core digest, derive the
  session/candidate marker from it, append that exact marker to form the final body, and
  recompute the final digest. The digest array is ordered one-for-one with those final
  payload digests. The ordered proposal `(candidate_id, source_block)` sequence equals
  the independently parsed frozen candidate/block index one-for-one; omission,
  reordering, or an extra candidate is invalid even when the report and remaining
  proposals are self-consistent.
- `notification-delivery`: all proposal keys plus `notification_operations`. Before
  every scheduled send or reminder, append and atomically persist an exact operation
  bound to notification target, proposal-set digest, canonical rendered payload digest,
  and an idempotency key derived from run/session plus operation kind. Each logical
  operation owns an append-only `attempts` array; the operation's status, response, and
  read-back repeat its last attempt exactly. A retry appends a new `attempting` attempt
  without discarding the preceding attempt and is permitted only after authoritative
  no-match proved the preceding attempt had no effect. Its status is
  `attempting`, `verified`, `failed`, or `ambiguous`; retain the exact response and
  authoritative thread read-back. Reference absence alone never permits retry.
  `verified` requires one exact visible thread message and returned thread reference;
  authoritative no-match is `failed`; uncertain, non-exact, or multiple matches remain
  `ambiguous` and operator-held. Reminder operations use the same schema and authority.
- `awaiting-approval`: all proposal keys plus `approval`,
  `notification_thread_reference`, `notification_operations`, and `decisions`; before a decision, approval is JSON
  null and decisions are empty, while the optional non-empty thread reference records
  where proposals were presented. A non-null reference must come from the exact verified
  initial notification operation; every retained notification operation is independently
  valid and no failed, ambiguous, or attempting send may be silently retried. Once
  decisions exist, transition atomically to the
  selected write or archive phase. That next phase's approval has exact source,
  approver identity, normalized command records, and proposal-set digest; its ordered
  commands equal the ordered decisions one-for-one, and each binds the same candidate id
  and proposal digest. Approval also retains an authoritative source read-back. A
  current-session approval names the present operator identity; a notification-thread
  approval names that same operator identity and exact verified thread. A merely
  non-empty or foreign approver identity is invalid.
- `tracker-write`: all approval keys plus `operations`; live operations are non-empty,
  summarize the last durable attempt record for each attempted filed decision, bind a proposal
  digest, frozen payload marker, exact
  tracker destination, returned identifier, and authoritative read-back, and use only
  `attempting`, `verified`, `failed`, or `ambiguous`. A `verified` read-back repeats the
  operation's identifier, payload digest, marker, and destination exactly. Its exact
  `verified_route` is `created-and-read-back`, `pre-existing-exact-match`,
  `failed-response-then-exact-read-back`, or
  `ambiguous-response-then-exact-read-back`; the retained response must match that route
  and no route may fabricate a successful create. The read-back carries the observed
  canonical `{title, body, project, labels}` plus its independently recomputed digest;
  exact verification requires that payload, digest, marker, destination, and identifier
  to match the approved operation. The complete decision plan plus its exact attempted
  operation prefix accounts for every approved tracker payload without cross-payload or duplicate
  identifier reuse. The
  `verified_tracker_identifiers` array equals the ordered returned identifiers of
  `verified` operations after authoritative read-back. An `attempting`, `failed`, or
  `ambiguous` operation may honestly retain JSON null for both returned identifier and
  read-back only when that is the exact observation; never fabricate either. A failed
  operation instead preserves an authoritative negative read-back. An ambiguous
  operation preserves the exact response, any returned identifier, and the non-exact or
  multiple-match read-back. Every ambiguous match has exact identifier, observed
  canonical payload, independently recomputed observed digest, marker, destination, and
  derived exact-payload verdict; the observed payload has exactly `title`, `body`,
  `project`, and `labels`, and its body carries the claimed marker exactly once.
  Identifiers are unique and every field binds the operation. Ambiguity requires
  multiple matches or a non-exact match; one
  exact match selects the matching verified route. This phase contains tracker-create operations only, and each
  operation's decision is exactly `file`; candidate ids, payload digests, decisions,
  and non-null returned identifiers are unique. Decisions retain the complete ordered
  filed plan, while operations are its exact ordered attempted prefix. A later operation
  is absent—not a fabricated attempt—until its predecessor verifies. Before every
  create, append that next operation as `attempting` and persist it; after the complete
  prefix verifies, operations and filed decisions are ordered bijectively.
  `attempts` is a separate append-only persisted array of complete tracker-attempt
  records, grouped in decision order. Each operation equals the last attempt for its
  decision; only an authoritative no-match `failed` attempt may precede a retry, so
  one-sided mutation of either structure invalidates the state without erasing history.
  Every live attempt also retains `search_read_back`, the complete authoritative
  pre-action marker match set with independently observed payloads and recomputed
  exact-payload verdicts. Create authority requires that set to be empty; the
  `pre-existing-exact-match` route requires that complete set to contain exactly the one
  selected exact match. A second, non-exact, incomplete, or foreign match invalidates
  both routes. Operations form a verified prefix: no later decision may have an attempt
  until the preceding operation is verified.
  Forge evidence begins in `forge-finalize`. In `test` mode the same phase uses
  `would-create` operations with JSON-null response, returned identifier, and read-back;
  verified identifiers and repository/PR evidence stay empty. Operations are empty when
  no test decision is `file`.
- `forge-finalize`: all tracker-write keys plus `finalization_operations`. Before each
  branch, commit, push, pull-request, review, or merge-read-back action, append and
  atomically persist its canonical intent and digest with `attempting`; after the action,
  persist the exact response and authoritative read-back as `verified`, `failed`,
  `ambiguous`, or, for `pr-watch` and merge read-back, `unsettled`. Each logical
  finalization operation owns an append-only `attempts` array and repeats its last
  attempt's status, response, and read-back. A failed action may append a retry only
  after authoritative no-effect; `pr-watch` may append after an unsettled observation;
  merge read-back may append after an authoritative `merged: false` observation.
  Ambiguous attempts remain operator-held. The ordered logical-operation log is a prefix of
  `branch-create`, `commit`, `push`, `pull-request`, `pr-watch`, and
  `merge-read-back`; every earlier logical operation is verified and at most the last is not.
  Each operation consumes only identifiers established by the preceding verified
  read-back: push intent and remote read-back use the commit operation's independently
  observed commit and tree; pull-request intent and read-back use that verified pushed
  remote head and tree; `pr-watch` intent and evidence use the exact PR identity, head,
  and tree independently read back after creation; and merge read-back intent uses the
  exact reviewed PR, head, and receipt. Every intent retains the immutable draft
  protected head separately from `finalize_base_head`, which is the independently
  observed current protected head proven to descend from the draft head before branch
  creation and is then inherited only from verified read-backs. An identifier returned by the pending operation
  is forbidden from its own intent. A foreign or future commit, tree, PR identity, head,
  or receipt introduced between stages invalidates the complete chain even when every
  individual operation's intent, digest, response, and read-back are locally
  self-consistent.
  Before the commit action, independently read back the staged tree and exact staged
  paths into `authority_read_back`; commit intent takes its tree and paths only from
  that observation. `authority_read_back` is JSON null for other finalization operations.
  Commit intent also binds the exact merged-config `triage.commit_subject`, and commit
  read-back observes that subject. Pull-request intent binds `triage.pr_draft` directly;
  neither value may be supplied by the candidate record or inferred from its response.
  Repository and PR evidence are the independently persisted verified records for their
  respective operations. A PR response without exact read-back, an unsettled/failed
  review, or an ambiguous merge read-back stays in this phase and operator-held.
- `archive-sweep`: all forge-finalize keys plus `archive_sweep`; the finalization log
  reaches verified `pr-watch` but not merge read-back. The record has exact
  repository, base, branch, commit, PR, observed head, reviewed head, and PR-watch receipt.
  Derive every archive-sweep field from the verified forge chain: repository and branch
  from the verified repository operations, commit from the verified pushed remote head,
  and base, PR identity, observed head, reviewed head, and receipt from the verified
  `pr-watch` read-back. Repository and PR evidence contain the independently persisted
  operation records, and every predecessor, head, tree, identity, and receipt binding
  matches. Every filed operation is verified. Operations may be empty only when no
  decision is `file`, so an archive-only batch remains constructible without inventing a
  tracker write.
- `completed`: a route-discriminated terminal shape with `completion`, which contains
  `route`, selected terminal outcome, and exact durable completed-receipt digest.
  Recompute the digest from a canonical nonrecursive route receipt core. Every core binds
  route, outcome, run identity, frozen digest, and the route's complete retained
  authority: candidate index for `no-op`; proposals, approval, decisions, tracker
  operations and attempt history for `decision-only` and `test-render`; and tracker,
  finalization, archive, PR-watch, and merge read-back evidence for `archive-sweep`. The
  `archive-sweep` route retains the complete archive-sweep shape, appends a verified
  `merge-read-back` operation, and stores its authoritative `merged: true`, final head,
  PR identity, and receipt binding in `completion`; the final head must equal the
  retained reviewed head. The `no-op` route is
  the exact base plus completion, requires `successful-completion`, an independently
  parsed empty candidate index in the frozen snapshot, empty evidence arrays, and a
  completed-receipt digest recomputed from the exact no-op receipt core containing the
  route, outcome, run identity, frozen digest, and empty candidate index. It never
  invents tracker or PR evidence. The `decision-only` route retains
  proposal, approval, and ordered parked decisions with empty operations and repository/PR
  evidence. The `test-render` route retains proposal, approval, decisions, and
  `would-create` operations while forbidding returned identifiers, read-back, and
  repository/PR evidence; those operations are empty when every test decision is
  `archive` or `park`. Evidence-retaining `decision-only` and `test-render` routes may
  record `degraded-success` when an optional interactive notification degraded after the
  decisions became durable.

Validate the exact base and the complete phase-owned shape before treating a captured
state as valid. A recognized phase with incomplete or invalid phase-owned fields is
uncertain, not abandonable. An unrecognized phase is invalid, but it is abandonable
only when the readable object contains exactly the valid complete base shape and that
shape independently proves empty `attempts`, `verified_tracker_identifiers`,
`repository_evidence`, and `pull_request_evidence`. A malformed base, extra key, or
unreadable field cannot prove absence.

Before an external write, atomically persist `attempting` with the exact operation and
payload digest. After response/read-back, atomically persist `verified`, `failed`, or
`ambiguous`. A retry must inspect that state and the destination. Process termination or
a missing final chat summary never authorizes repeating a write.

Every live or test mode has one single-writer gate file beside its active state path.
Keep the configured logical fragment separate from the resolver-returned absolute path;
only the contained absolute path is filesystem authority. Prepare a complete owner
record in a same-directory temporary file whose basename is
`.<gate-basename>.<owner-token>.tmp`: an opaque owner token matching the ASCII grammar
`[A-Za-z0-9][A-Za-z0-9_-]{0,127}`, run identity or JSON null before one is allocated,
host, process identifier, process-start
observation, and creation time. Canonicalize those immutable nonrecursive fields as the
gate-claim core and store its SHA-256 digest; the core never contains a state digest or
state binding. Flush the file, then acquire the absent gate with an
atomic hard-link publication of that inode; a pre-existing destination loses without
replacement. The
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
bundle remains present. These receipts come only from state-present invalid-state
recovery; gate-only recovery remains operator-held. Every safe-restart receipt carries its mode, originating
old-gate digest, exact configured bundle path, capture-core digest, quarantine path, and
prepared-envelope digest. Resolve that exact recorded bundle path without a directory
scan or a path derived from the newly acquired gate; verify the envelope digest and its
embedded core before replacing the receipt. Every later
transition reads the current bytes under the gate and records their digest, then
immediately before atomic replacement requires the same digest, run identity, and gate
owner token. A mismatch stops operator-held without replacing either version.
When a normal invocation acquires a fresh gate over valid ordinary state, validate the
captured old-bound state first, then perform the declared digest-checked state-claim
rebind as the sole permitted transition before any phase action. Preserve every field
other than `gate_owner_token`, `gate_binding`, and `state_claim` byte-for-byte. A crash
before replacement leaves the old binding under the new gate and may resume only this
claim transition; a crash after replacement resumes the phase under the current binding.
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

## Invalid-state recovery

Recovery is a state-preservation transition, not approval to discard a session or repeat
an external write. Acquire the mode's single-writer gate before ordinary state capture.
If a complete existing gate blocks acquisition, capture its owner record, every
same-inode temporary name, and filesystem observations, then prove owner termination
before using the bounded stale-gate classifier defined above. This route remains
available when active state is absent. Never remove the gate first. When active state is
absent, the immutable capture also records repeated non-creating resolution and
filesystem observations proving that absence. After obtaining exact operator approval
of the canonical `prepared_core` digest, atomically and exclusively create and flush a
`gate-only-prepared` bundle envelope. Build the core and envelope exactly as declared by
the semantic classifier: derive the one intent payload by adding the core digest, hash
that payload, and include both plus the core-bound approval in the envelope. Hashing the
full envelope is permitted for artifact read-back, but that digest is never an input to
its core or intended intent. Before old-gate quarantine, require the captured primary
path to equal the resolved mode gate path, require the envelope kind to match the mode,
recompute the old-gate digest from the captured gate bytes, match every captured gate
name and filesystem observation to the independently observed blocking inode, and
derive the exact configured bundle path from that digest. After quarantine, never
derive evidence by transforming that capture: resolve every recorded source and
quarantine target non-creatingly, require every source absent, and independently read
and stat every target as the exact recorded bytes, digest, device, inode, mode, link
count, size, and modification time. Open and retain no-follow descriptors for the state
root and every source and target parent. Immediately before each rename, independently
re-walk the configured parent chains from the state root and require every named
directory to retain the held device/inode identity; perform the rename and source
absence check relative to those held parents, revalidate the chains afterward, then
independently reacquire the configured target chain for read-back. A renamed, replaced,
or symlinked parent stops operator-held even when a detached descriptor can still read
the approved inode. Immediately before mutation, read and stat the held source and
require its exact approved bytes, digest, device, inode, mode, link count, size, and
modification time. Keep that approved source descriptor open through publication and
bind both names back to its device/inode identity before unlinking either. Publish the
quarantine name without replacement by exclusively hard-linking that inode, flush the
target directory, unlink the held source name, and
flush its directory; an existing target leaves both artifacts untouched and stops
operator-held. Any replacement gate is captured separately at the
same resolved mode gate path with its complete owner record and matching owner token.
Finalization validates those observations and the exact canonical held receipt before
releasing the replacement gate. Receipt validity is passive evidence; finalization and
release separately require the current invocation's owner token and run identity to
match the replacement gate. A later process observing the prior replacement owner can
hold the receipt but never release that gate as its own. A self-consistent foreign
envelope or reconstructed
quarantine record is evidence, not resume authority. Then claim the absent state path
by exclusive creation of
that exact `gate-only-recovery-intent`, which binds the prepared-core digest, old gate
owner record, old gate digest, exact configured bundle path, approved capture, absence
observations, and repository identity. Flush that intent and
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
| `capture-old-gate` | Old gate present, active state absent; persist the immutable `gate-only-prepared` bundle, exact approval, and intended intent payload. |
| `publish-recovery-intent` | Old gate still present; exclusively create and flush `gate-only-recovery-intent`. |
| `quarantine-old-gate` | Intent present; revalidate and quarantine every unchanged old-gate name. |
| `acquire-recovery-gate` | Intent present; atomically acquire a new complete recovery gate. |
| `finalize-held-receipt` | New gate present; digest-check and atomically replace intent with `gate-only-operator-held`. |
| `release-recovery-gate` | Held receipt durable; release only the matching new recovery gate. |

Otherwise, locate active state in its own sandbox with
`resolve_write_path(fragment, mkdir=False)` and inspect the path itself without parsing
its content. Reject a symlink, non-regular file, or link count other than one. Before
validity classification, rename, or repair, atomically and exclusively create a
`state-present-capture` bundle at `triage.recovery_bundle_pattern` expanded with the mode
and digest of the exact complete held gate. Its immutable capture core contains the
exact raw state bytes as canonical base64 with an explicit `base64` encoding label,
their SHA-256 digest computed over the decoded bytes, the active path, repository identity, the
exact configured bundle path, and the complete held-gate bytes, owner record, digest,
and filesystem observations. It also contains the path's device, inode, mode, link
count, size, and modification time observed around
the read; changed observations abort the capture and leave the active file untouched.
Canonical means decoding with strict validation and re-encoding must reproduce the
stored base64 text byte-for-byte; alternate pad bits are not equivalent capture bytes.
A process stop after publication is resumable only by interactive `recover`: rederive
the exact bundle from the unchanged blocking gate, validate its capture digest, and
continue from the captured bytes. This route accepts the exact gate still owned by the
current recovery invocation, or that same owner only after exact termination proof
changes its status to owned-now-proven-stale, as well as an independently proven-stale
foreign or prior owner. Missing or mismatched current ownership or termination evidence
stops operator-held. Other entries and unattended execution preserve it operator-held.

Decode the lossless capture and require its raw-byte digest before parsing. Parse and
validate only the captured bytes, never the still-live path. Record the parse
result and current and recorded identities in a candidate `action_core`. The prepared
envelope embeds the complete immutable capture core and digest, the action core and
digest, and the exact decision plus approver identity bound to `action_core_digest`.
Only the two declared actions are valid: `preserve-valid-state-and-quarantine-old-gate`
and `abandon-invalid-state`. An absent, empty, or unknown action or approving decision is
not recovery authority and stops operator-held.
Before selecting either transition, require the exact `state-present-capture` or
`state-present-prepared` kind, recompute the embedded old-gate digest, require its
primary path to equal the resolved mode gate path, and rederive the configured bundle
path. While that gate exists, match the complete embedded capture to the independently
observed gate. After quarantining a proven-stale gate, require resolved-path absence and
independent read-back of every recorded quarantine target. After normally releasing a
gate owned by this recovery invocation, require resolved-path absence plus the exact
durable receipt and bundle whose capture-core binding records that gate path, digest,
and owner token; no quarantine evidence exists or is required for this route. Missing,
foreign, reconstructed, or cross-gate evidence stops operator-held.
For each report or frozen-snapshot path obtained from validated captured
fields, apply the same path, alias, and atomic-read checks before recording exact paths,
bytes/digests, and filesystem observations. Never follow an unvalidated path from
malformed state; unresolved artifacts are named as unresolved. A valid captured state
under a gate still owned by the current invocation leaves the state byte-identical,
releases only that matching gate by normal teardown, and directs the operator to
`resume`. A valid capture reached through a proven-stale gate may select only
`preserve-valid-state-and-quarantine-old-gate`. Require exact approval of that action
core digest, then digest-check and atomically replace the capture bundle with the
prepared envelope before changing the old gate. A fresh invocation can resume the same
prepared action. Revalidate the unchanged state and every old-gate name, then quarantine
only the proven-stale gate. Once the old gate is absent, the byte-identical valid state
is again selected by ordinary `resume`; the recovery invocation does not parse it a
second time or start work under an unowned gate.

Classify invalid captured state conservatively. Only a readable state that proves it
never reached `attempting` and contains no verified tracker identifier or repository/PR
evidence may offer `abandon <action-core-digest>` to the present interactive operator.
The action core binds the capture-core digest, exact engine-derived quarantine target,
exact `recovered-safe-to-restart` receipt core, old-gate capture, repository identity,
and gate disposition. An owned disposition binds the current recovery invocation's
owner token and run identity. If that process later terminates, only a new exact
termination proof that records an independently observed process absence after a
live-owner control and matches the captured host, process identifier, process-start
observation, owner token, and run identity changes its observed status to
owned-now-proven-stale; a present process or a reused identifier with a different start
observation stops operator-held, and the gate does not become a
foreign-stale disposition. A proven-stale
disposition binds the captured foreign or prior owner and can never select normal owned
release. The
receipt core contains mode, old-gate digest, exact configured bundle path,
capture-core digest, and quarantine path, but no action-core or prepared-envelope
digest. Persist exact approval by digest-checking and atomically replacing
`state-present-capture` with `state-present-prepared` before the first disputed rename.
After that envelope is durable, hash its exact bytes and form the final receipt by
adding `prepared_envelope_digest` to the approved receipt core; neither the receipt core
nor action core contains that later digest, so the graph remains non-circular.
Immediately before quarantine, re-read and re-stat the active path and require its
digest, device, inode, mode, and link count to equal the captured observations.
Derive the only acceptable quarantine target and restart receipt from the approved
action core, then independently read and stat the resulting artifact; a closure-local
reconstruction or semantic match is not authority. Quarantining the current state and
publishing its receipt require either the exact currently owned gate or the unchanged
proven-stale gate at the resolved mode gate path. For a proven-stale gate, later absence
requires the independently observed quarantine read-back above. For an owned gate, make
the exact receipt durable and read it back while the matching owner token still occupies
that path, then unlink only that gate; a later invocation may accept resolved-path
absence from that exact receipt-and-bundle binding without inventing quarantine
evidence.
Move that exact source to an absent prepared quarantine path without replacement using
the same exclusive-link, flush, unlink, and held-parent revalidation sequence. Create the receipt
only after re-reading and re-statting the quarantine target. Its exact path, digest,
device, inode, mode, link count, size, and modification time must equal the prepared
target and immutable capture observations; a same-byte replacement or changed
filesystem identity stops operator-held. Then exclusively create and flush the exact
prepared receipt at the now-absent state path, revalidate, and
release the matching currently owned gate by normal teardown, or quarantine every
unchanged name only when that owner is proven stale. A crash with the prepared bundle plus the
unchanged state, the exact quarantine target with state absent, or the exact receipt is
resumed only at the next declared step; every mismatch is operator-held without another
mutation. A later new draft may replace only that receipt under its newly acquired gate.
The bundle, quarantined bytes, and receipt remain durable.

### State-present recovery transition

| State-present step | Required state transition |
|---|---|
| `capture-state` | Old gate and state present; exclusively publish `state-present-capture` before parsing. |
| `prepare-valid-gate-release` | Valid captured state under a proven-stale gate; record exact action approval by digest-checked bundle replacement. |
| `release-valid-state` | Prepared valid action present; revalidate state and quarantine only every unchanged proven-stale gate name. |
| `prepare-invalid-abandonment` | Abandonable invalid state unchanged; record exact action approval, quarantine target, and receipt payload by digest-checked bundle replacement. |
| `quarantine-invalid-state` | Prepared invalid action present; revalidate and rename only the unchanged state to the prepared target. |
| `publish-restart-receipt` | Prepared quarantine target present and state absent; exclusively create and flush the exact prepared receipt. |
| `release-restart-receipt` | Exact prepared receipt present; release the matching owned gate or quarantine only every unchanged proven-stale gate name. |

If any external attempt or verified identifier is present, or absence of either cannot
be proved from readable evidence, abandonment is prohibited. Digest-check and atomically
replace the capture bundle with a terminal `state-present-held` envelope without moving,
replacing, or deleting the active bytes or old gate. That envelope retains the complete
immutable capture core and digest plus the terminal classification. Reconcile
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
Do not follow an unvalidated captured path. Derive the same complete invalid-state action
core and receipt core as state-present recovery, then digest-check and atomically replace
the capture bundle with the complete canonical `state-present-prepared` envelope whose
exact in-session operator approval binds `action_core_digest`; approval of only the
capture or bundle digest is not mutation authority. Then immediately re-read and re-stat
the test state and require the captured digest, device, inode, mode, and link count. Atomically quarantine only
that unchanged test-state file and write `test-recovered-safe-to-restart` under the
same test gate. A later `test` invocation may digest-check and replace only that receipt
after successfully parsing the current inbox under the test gate; a parse or act-time
digest failure preserves the receipt. The transition never reads or writes live state,
notification approval, tracker, source documents, archive, branch, commit, push, PR,
or merge.
Unknown test-gate ownership remains operator-held under the same capture, owner-death,
and exact-approval rule, confined to test paths. Only an interactive `test` that proves
the owner dead and obtains exact approval of the capture may preserve the unchanged gate
and state or safe-restart receipt in a unique state-present test-gate held bundle at the
deterministic recovery-bundle path, then
stop operator-held. Without a crash-released exclusive recovery primitive, neither
engine-backed nor LLM-only execution may claim
that separate gate, state, and bundle files form one atomic transition. When that same
approved interactive recovery proves test state absent, create and flush a
`test-gate-only-prepared` bundle with the same non-circular prepared-core, core-bound
approval, and derived intended-payload fields, then exclusively create and flush
`test-gate-recovery-intent` while the old test gate still exists, then follow the
Gate-only recovery transition ordering with test-confined paths. Quarantine the old
test gate only after the intent is durable; finish by replacing the intent with
`gate-only-operator-held` under the replacement test gate. That receipt never authorizes
a new test draft or a receipt-to-reserved transition. A later interactive `test` resumes
only the recorded absent-state intent; gate-only and state-present held bundles remain
terminally operator-held. Scheduled or unattended `test` with invalid state, a blocking
gate, recovery intent, or held bundle preserves everything operator-held and performs
no recovery mutation.

### Execution context

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

Reject unknown ids, mixed verbs, substring matches, messages from other identities, or
an approval whose current payload digest differs from the displayed digest. Unmentioned
items default to `park`, never archive. Persist normalized decisions and exact approval
evidence atomically before any tracker capability is triggered.

In an unattended resume with no valid reply, append and persist one exact reminder
`attempting` operation before send, then apply the same response/read-back states as the
initial notification. A retained reminder operation prohibits a second reminder.
Preserve state and report `operator-held`. If the notification path is now unavailable, preserve
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

Before each branch, commit, push, pull-request, `pr-watch`, or merge-read-back action,
append its exact intent and persist the `forge-finalize` operation and first attempt at
`attempting`; a permitted retry appends another attempt to that same logical operation;
never infer safety from a missing response. After each action, independently read back
the declared repository/PR facts and persist the status-specific evidence before
beginning the next operation. Build each next intent from that verified read-back, not
from the preceding response or from identifiers retained in memory: commit read-back
supplies push's commit and tree, push read-back supplies pull-request creation's remote
head and tree, pull-request read-back supplies `pr-watch`'s PR identity and observed
head, and verified `pr-watch` supplies archive-sweep and merge-read-back identity, head,
and receipt. Reject a locally valid later record when any consumed identifier differs
from its predecessor's verified observation. Never switch the caller checkout. Fetch the protected branch, create a fresh isolated
worktree and `<triage-branch>` from its current origin ref, and re-read the destination
documents there. Require the current origin ref to descend from the immutable draft
head, persist it as `finalize_base_head`, and never rewrite the draft run identity. A
permitted fast-forward advance still must pass the byte-identical frozen-block check;
otherwise remain operator-held. Require a clean index, stage only `<friction-log>` and
`<friction-log-archive>`, and prove the staged path set equals that pair exactly. Commit
with `triage.commit_subject`, push, and create the pull request ready for review by
binding the validated `false` `triage.pr_draft` directly. Immediately run the native
`pr-watch --assert-ready` correction, then read back repository, base, branch, commit,
head, draft bit, PR URL, and changed paths, and require the read-back draft bit to be
`false` before the normal `pr-watch` loop. A failed assertion or a failed, ambiguous, or
draft response triggers read-back before retry and otherwise remains operator-held.

Run `pr-watch` for the exact head and persist an `unsettled` review observation whenever
it has not reached terminal exact-head evidence. This workflow never merges the sweep pull request.
When `pr-watch` reports terminal exact-head review evidence, authoritatively read back
the PR and require its current base branch to remain the configured protected branch and
its current `headRefOid` to equal the head in that evidence. Before
allowing merge, atomically persist that head as
`reviewed_head` with the PR-watch receipt. Any later head movement invalidates the
receipt and remains terminally operator-held in this run; this schema never replaces
`reviewed_head` or invents a second review cycle from a later head.
When review is unsettled or the operator still owns the merge decision, report
`operator-held` with the PR URL and `observed_pr_head`; name `reviewed_head` only when a
retained terminal receipt establishes it. If terminal evidence exists but PR read-back
is unavailable or mismatched, remain operator-held without changing `reviewed_head`.
On a later resume, digest-check the `archive-sweep` state and atomically return to
`forge-finalize` by dropping only the derived `archive_sweep` summary while retaining
its complete verified tracker, repository, PR-creation, and PR-watch operation evidence.
Append `merge-read-back` there without issuing a merge. After verified read-back,
rederive the byte-identical archive summary for completion. The authoritative PR
read-back must prove that the pull request still names that same base, that it merged,
and that its final `headRefOid`
equals `reviewed_head` recorded in state, and the retained terminal PR-watch receipt
must still bind that same head. A missing or mismatched final head or receipt is
operator-held; an authoritative matching `merged: false` read-back is retained as an
unsettled attempt and permits a later read-back attempt without issuing a merge or
discarding the observation; never mark an unreviewed replacement head complete. Only then write
completion to the report and state before optionally deleting active state; the
completed report remains durable.

## Final output

List every capability with terminal status, then report exactly one overall outcome.
Name the report and frozen snapshot, execution and engine modes, approval source,
verified tracker identifiers, sweep branch/commit/PR and exact head when present,
degraded capabilities, and one safe resume action. Never describe an unavailable source
as empty, a proposed write as completed, an operator-held PR as merged, or an
agent-executed result as engine-verified.
