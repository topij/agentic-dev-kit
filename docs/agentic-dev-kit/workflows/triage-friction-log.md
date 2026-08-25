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
are non-empty strings. Artifact patterns are non-empty repository-relative paths.
`triage.state_path` contains `{mode}`; the frozen-inbox and report patterns contain
`{mode}`, `{date}`, and `{session}`. Live and test state must resolve to different
paths. The state and frozen snapshot are logical children of `<state-dir>`; the report
is a child of `triage.report_root`, which is neither empty nor the repository root.

Resolve state reads and writes through `<engine-dir>/lib/state_paths`, including
`DEVKIT_STATE_ROOT` and `.devkit_state_root`; never write logical state paths directly
beneath the worktree. Preflight with non-creating resolution. Reject absolute fragments,
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
metadata carry the run identity and frozen digest. A resumed run must match them all.

## Semantic input matrix

Evaluate the input before capability-dependent work.

| Input or state | Required result |
|---|---|
| Unknown or combined entry keyword | Hard-stop before capability probing or writes. |
| No argument, no active state | Start a new live draft. |
| No argument, valid active state | Resume the recorded phase and mode. |
| `resume`, no valid active state | Hard-stop without an external write. |
| `new`, active live state | Refuse; never overwrite an approval-bound session. |
| `test` | Use test identity and test state; never replace or resume live state. |
| Scheduled or unattended invocation with active state | Resume or report operator-held; never start another draft. |
| Both configured engines present | Select engine-backed mode and persist it. |
| Both configured engines absent | Select LLM-only mode and label its work agent-executed. |
| Only one configured engine present | Hard-stop before artifact or external write. |
| Interactive invocation with notification unavailable | Present exact payloads in-session and persist exact decisions; record degradation. |
| Scheduled or unattended invocation with notification unavailable | Hard-stop before creating a new approval session; preserve an existing session as operator-held. |
| Missing, malformed, or identity-mismatched frozen snapshot/state | Hard-stop before tracker writes; after a verified write, preserve operator-held evidence and never whole-sweep. |
| Tracker or finalization write fails or is ambiguous | Read back before retry; unresolved state is operator-held. |
| Test mode | Permit declared local artifacts and optional `[TEST]` notification only; prohibit tracker and repository writes. |

## Authoritative integration declaration

The capability, authority, artifact, input, and completion rows in this document are
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
| `shared-state-resolver` | required | Resolve `<engine-dir>/lib/state_paths`, prove non-creating write resolution plus existing-artifact read resolution, and honor the lane sandbox. Unavailability hard-stops before state, snapshot, or report writes. |
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
| `state-or-frozen-identity-mismatch` | `stop-before-tracker-write-never-whole-sweep` |
| `partial-engine-set` | `stop-never-mix-engine-and-llm-artifacts` |
| `unattended-without-notification` | `stop-before-new-approval-session` |
| `tracker-without-exact-payload-approval` | `prohibit-create-update-comment` |
| `approved-payload-changed` | `require-new-exact-payload-approval` |
| `ambiguous-external-write` | `read-back-before-retry-or-operator-hold` |
| `partial-tracker-batch` | `hold-before-archive-sweep` |
| `test-mode-external-write` | `prohibit-tracker-friction-archive-branch-commit-push-pr` |
| `archive-sweep-boundary` | `sweep-only-approved-accounted-byte-identical-frozen-blocks` |
| `runtime-policy-override` | `shared-declaration-wins-and-stop` |

### Durable artifacts, resumability, and completion

The report is load-bearing and is written before any external attempt. The state is the
act-time gate. It records the run/config/frozen identities, selected engine mode, exact
canonical proposal payloads and digests, approval source and approver identity,
notification thread reference when used, normalized per-item decisions, attempt state,
verified tracker identifiers, and branch/commit/PR identity. Never record an external
identifier not returned authoritatively or verified by read-back.

Before an external write, atomically persist `attempting` with the exact operation and
payload digest. After response/read-back, atomically persist `verified`, `failed`, or
`ambiguous`. A retry must inspect that state and the destination. Process termination or
a missing final chat summary never authorizes repeating a write.

| Outcome | Condition | Required result |
|---|---|---|
| `hard-stop` | A required preflight, state/frozen safety check, engine atomicity check, or shared/runtime policy check fails before the disputed action. | Name the failed capability and remediation; preserve every pre-existing artifact and perform no disputed write. |
| `operator-held` | Approval is pending; a triggered tracker, repository, review, or unattended-notification capability is unavailable; or an attempted write remains failed or ambiguous after read-back. | Preserve exact state, report, payload digests, verified identifiers, and repository/PR evidence; name one safe resume action and do not sweep or delete state. |
| `degraded-success` | Every required and triggered write completed authoritatively, but an optional interactive notification or runtime-compute enhancement was unavailable. | Report completed durable artifacts and the degraded capability; never use degradation to mask an unresolved required write. |
| `successful-completion` | No candidates or no sweep/write was approved, or every approved payload and sweep reached an authoritative terminal state without degradation. | Report actual artifacts and identifiers. Write a durable completed receipt before optionally removing active state. |

### Overall outcome precedence

Select the first matching row and report exactly one overall outcome.

| Precedence id | Condition | Outcome |
|---|---|---|
| `required-or-safety-failure` | A required preflight/state/safety check failed before a disputed action, or shared/runtime policy conflicts. | `hard-stop` |
| `approval-or-triggered-write-not-terminal` | Approval is pending or a triggered notification, tracker, repository, or review path lacks an authoritative terminal state. | `operator-held` |
| `optional-degradation-after-terminal-work` | Required and triggered work is terminal, but an optional interactive notification or compute enhancement degraded. | `degraded-success` |
| `all-triggered-contracts-terminal` | No prior row matches and every triggered capability is terminal. | `successful-completion` |

## Entry points and context

Accept exactly one of `resume`, `new`, or `test`, or no argument. `test` starts a new
test draft or resumes the separate test state; it never selects live state. No argument
resumes valid live state when present and otherwise starts a live draft. `new` refuses
when live state exists. `resume` requires valid live state.

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

Each tracker body includes a non-rendering idempotency marker binding session id,
candidate id, and payload digest. Canonicalize `{title, body, project, labels}` and hash
it. The marker is part of the body and therefore part of the exact payload the operator
reviews. In engine-backed mode invoke `triage.draft_engine`; in LLM-only mode draft with
the configured analysis tier and record `agent-executed`.

If parsing fails, hard-stop without state. If there are no candidates, write the report
and complete without notification, state, tracker, or repository writes. Otherwise
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

Trigger tracker access only for approved items. Before each create, search for the exact
idempotency marker and record the complete pre-existing match set. Recompute the payload
digest, compare it with the approval record, and persist `attempting` before the create.
After a success response, read back the item and require exact project, title, body,
labels, marker, and returned identifier before recording `verified`.

If the create fails or returns ambiguously, read back by the exact marker before any
retry. One new exact match verifies the write. No match proves no landing only when the
tracker read is complete and authoritative; multiple or non-exact matches remain
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
documents there. Require a clean index, stage only `<friction-log>` and
`<friction-log-archive>`, and prove the staged path set equals that pair exactly. Commit
with `triage.commit_subject`, push, and create the pull request with
`triage.pr_draft`. Read back repository, base, branch, commit, head, draft bit, PR URL,
and changed paths. A failed or ambiguous response triggers read-back before retry and
otherwise remains operator-held.

Run `pr-watch` for the exact head. This workflow never merges the sweep pull request.
When review is unsettled or the operator still owns the merge decision, report
`operator-held` with the PR URL and exact head. On a later resume, verify the pull
request merged before marking the run complete. Write completion to the report and
state before optionally deleting active state; the completed report remains durable.

## Final output

List every capability with terminal status, then report exactly one overall outcome.
Name the report and frozen snapshot, execution and engine modes, approval source,
verified tracker identifiers, sweep branch/commit/PR and exact head when present,
degraded capabilities, and one safe resume action. Never describe an unavailable source
as empty, a proposed write as completed, an operator-held PR as merged, or an
agent-executed result as engine-verified.
