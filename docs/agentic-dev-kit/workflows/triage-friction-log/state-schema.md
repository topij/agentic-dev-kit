# Triage friction log — state schema and gate mechanics

Read this file completely, together with
[`triage-friction-log.md`](../triage-friction-log.md) and its other reference files,
before the first action of any run. It is part of that workflow and as normative as it;
a section cited by name, or as *above* or *below*, may sit in that file or another of
its reference files.

## Contents

- Ordinary active state: base shape and the phase-owned keys
- Validity and abandonability
- The single-writer gate file

## Ordinary active state

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
A `proposal_correction` receipt, written only by the removed `correct-project` route,
is accepted on a `completed` LIVE state alone, and only its shape is checked: exactly
`action_core`, `action_core_digest` and `approval`, with `action_core.kind`
`linear-project-correction`. A session-starting entry then retires that state like any
other; nothing continues from the receipt. No other extra state fields are accepted.
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
  operation's identifier, marker, and destination exactly. Its exact
  `verified_route` is `created-and-read-back`, `pre-existing-exact-match`,
  `failed-response-then-exact-read-back`, or
  `ambiguous-response-then-exact-read-back`; the retained response must match that route
  and no route may fabricate a successful create. The read-back carries the observed
  canonical `{title, body, project, labels}` as the tracker returned it, plus its
  independently recomputed digest. Verification requires the marker, destination, and
  identifier to match the operation, and the observed payload to equal the approved one
  except in how each unordered-list marker outside a fenced code block is spelled:
  Linear's editor returns every bullet as `*`, so `-`, `*` and `+` compare equal there.
  A fence counts only when opened within three spaces of the margin, so a marker in
  indented or list-nested code is relaxed as well. That is what an *exact* tracker
  match means throughout this workflow; any other difference leaves the attempt
  ambiguous. The complete decision plan plus its exact attempted
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
  retained reviewed head. Its `completion` also carries an optional `sweep_cleanup`,
  outside the receipt core the digest binds, recording this sweep's own worktree,
  local branch, and remote branch retirement (below); its absence is valid — a state
  a previous engine completed before that field existed. The `no-op` route is
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

## Validity and abandonability

Validate the exact base and the complete phase-owned shape before treating a captured
state as valid. A recognized phase with incomplete or invalid phase-owned fields is
uncertain, not abandonable. An unrecognized phase is invalid, but it is abandonable
only when the readable object contains exactly the valid complete base shape and that
shape independently proves empty `attempts`, `verified_tracker_identifiers`,
`repository_evidence`, and `pull_request_evidence`. A malformed base, extra key, or
unreadable field cannot prove absence.

## The single-writer gate file

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
