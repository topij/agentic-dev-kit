# Triage friction log — recovery and test routes

Read this file completely, together with
[`triage-friction-log.md`](../triage-friction-log.md) and its other reference files,
before the first action of any run. It is part of that workflow and as normative as it;
a section cited by name, or as *above* or *below*, may sit in that file or another of
its reference files.

Whether a state is invalid or abandonable is decided by *Validity and abandonability* in
[`state-schema.md`](state-schema.md), against the shapes its *Ordinary active state* declares.

## Contents

- Completed-state retirement
- Gate-only input precedence
- Test input precedence
- State-present held-evidence procedure
- Invalid-state recovery: gate-only, state-present and isolated test-state transitions

### Completed-state retirement

A valid `completed` state holds no pending approval, attempt, sweep, or merge, so it does
not end its mode. A session-starting entry — no argument or `new` in live mode, `test` in
test mode, in any execution context — that acquires the gate and captures a valid
`completed` state, after complete state and frozen-snapshot validation, renames the
unchanged state bytes to `<state path>.completed-<first 16 hex of completed_receipt_digest>`
beside it, then claims a new draft. The rename reuses the declared quarantine
publication: the captured identity and bytes must still match, a target that already
exists with other bytes stops operator-held with both files preserved, and the retained
file is read back. The workflow never deletes a retained file. The rename and the claim
both run under the held gate. A claim that fails with a `TriageError` after the rename
releases that gate over the absent state path, and the next run starts fresh. A killed
process never does, and neither does an exception other than `TriageError` raised by the
rename or the claim (an `OSError`, for example): either leaves the gate held. Once that
process has exited, the gate's owner is dead, and every later session-starting entry of
that mode stops operator-held. In live mode, no argument, `new` and `resume` report
`single-writer gate is already held`, and unattended `recover` reports its own refusal.
Where the gate stays held, what interactive `recover` can do depends on where retirement
stopped. In live mode:

- **Before the rename's link.** The state is intact. Interactive `recover` releases the
  old gate through `preserve-valid-state-and-quarantine-old-gate`, and the next
  session-starting entry retires the state again.
- **Between the rename's link and its unlink.** The state path and the retired name are
  one inode, and every read refuses a state with a second link (`unsafe artifact at held
  parent`), `recover` included. No engine route clears it, so the operator does, by hand:
  - First confirm that the gate's owner has exited. The gate record is the file at
    `triage.gate_path` with `{mode}` resolved to `live`; no process with its
    `process_id` may be running on its `host`. If that id now belongs to another
    process, neither this check nor `recover` can prove the owner dead until that
    process exits too, and the run stays held until then.
  - Then confirm that the state path and the retired name,
    `<state path>.completed-<first 16 hex of completed_receipt_digest>`, are the same
    inode, and that each shows a link count of 2. A file an earlier run retired carries
    another digest in its name and shows a link count of 1.
  - Then remove the retired name, and only that name, never the state path.

  This is an operator action outside the workflow, which itself never deletes a retained
  file, and it deletes no bytes: the same bytes stay at the state path. It is not the
  manual deletion *Invalid-state recovery* forbids, because `new` still waits for an
  approved `recover`. The run is now in the first case above. Interactive `recover`
  releases the old gate, and the next session-starting entry retires the state again.
  `test_a_kill_during_completed_state_retirement_holds_rather_than_starting_fresh[after-link]`
  pins that outcome: once it removes the retired name, `recover` releases the gate and
  `new` retires the state again.
- **After the unlink, before the claim.** The state path is absent and only the retired
  file remains. Interactive `recover` takes the gate-only route, which ends in the
  terminal `gate-only-operator-held` receipt, not in a fresh start.

In test mode the same cutpoints leave a blocking test gate, and interactive `test`
follows the blocking-gate rows of *Test input precedence*. Each of those rows ends held,
so unlike live mode's first cutpoint, no test-mode cutpoint leads back to a retirement.

`resume` reports the completed receipt and `recover` refuses valid state, as
before; neither retires. Retirement applies only to valid state: an invalid state,
however terminal its recorded phase, stays on *Invalid-state recovery*. A configuration
change made after the run completed does not make its state invalid for retirement: the
session-starting entry accepts a `completed` state whose recorded config fingerprint
differs from the current one, provided its two recorded fingerprints are SHA-256
digests that agree with each other. Every other validation still applies, and every other phase and entry stays bound
to the current configuration.

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
| `ungated-valid` | any | absent | `valid-state` | absent | not applicable | Resume only the valid test state, unless its phase is `completed`: then retire it and start a new isolated test draft. |
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
validate only the captured bytes, never the still-live path. In state validation the
one live read is a completed state's frozen artifact, as the classification paragraph
below says; proving a sweep reads git live, as its own paragraphs say. Record the parse
result and current and recorded identities in a candidate `action_core`. The prepared
envelope embeds the complete immutable capture core and digest, the action core and
digest, and the exact decision plus approver identity bound to `action_core_digest`.
Only the three declared actions are valid: `preserve-valid-state-and-quarantine-old-gate`,
`abandon-invalid-state`, and `retire-terminal-invalid-state`. An absent, empty, or unknown action or approving decision is
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
`recover` judges a completed state with the predicate a session-starting entry applies
before retiring it: state validation, then the published frozen snapshot artifact, then
the forge-prefix checks on its forge operations. A completed state that is valid but for
a configuration change made after it finished passes it, so it is refused as valid
(`captured state is valid; recovery refused`) and left for *Completed-state retirement*
rather than captured as invalid. A completed state that fails only the artifact or forge
checks, including an artifact it cannot read, fails it. It is captured and offered
`retire-terminal-invalid-state` only when git proves its sweep, as below; otherwise
`recover` writes nothing and refuses it (`state fails the session-starting checks and no
retirement is proven; recovery refused`), so restoring the artifact or landing the sweep
still leaves a route out, and the action plan preserves it as before when it passes
state validation under the current configuration (one that fails that is classified as
any invalid state). The refusal's resume action names the check that failed: an
artifact failure says to restore the published frozen snapshot artifact or land the
run's sweep, and a forge-prefix failure, whose artifact is present, says to reconcile the
state's recorded forge operations with the forge or land the run's sweep. A state in any
other phase is judged by state validation alone, so an in-flight run whose artifact is
missing is refused as valid and resumes once the artifact is restored. The `test` entry's
own recovery branch judges a test state the same way and refuses an unproven completed
one unwritten (`test state fails the session-starting checks and no retirement is
proven; recovery refused`); unattended, it preserves the state as any invalid test
state. A test run completes by `test-render` or `decision-only`, neither of which proves a
retirement, so for such a state the route out is restoring its artifact, after which
`test` retires it. A test completion records no finalization operations, so the
forge-prefix checks, and the resume action that names them, never apply to it. For a completed state the
action plan reads the live frozen artifact at plan time: the capture holds only the
state and gate bytes.
The one other invalid state that leaves the held route is a **finished** run, in either
layout. Both need phase `completed`, completion route `archive-sweep`, every tracker and
notification operation `verified`, every forge operation `verified` (a `pr-watch`
observation may also be `unsettled`, since it writes nothing), and a verified
`merge-read-back` as the last forge operation. In each attempt log, top-level or nested,
every entry is settled in the same way, except that an `attempting` entry, which the
engine writes before each external call, is settled when the very next entry carries the
same `intent_digest` with a settled status. The layout an LLM-only session records adds a
`completion.merge_read_back` of `merged: true` whose `final_head` equals the top-level
`reviewed_head` and which must name the `merge_commit`; one that does not stays held.
The engine's layout keeps the reviewed head under `archive_sweep`, and its last forge
operation's read-back must be `merged: true` at that head. That read-back names no merge
commit, so the engine looks for one (below). Those bytes are claims, not proof; neither a
reachable commit (any merged commit is one) nor the working tree (uncommitted edits can
say anything) proves the sweep, so the engine reads the evidence from git. For a state in
the engine's layout, which names no merge commit, the engine walks the protected branch's
remote-tracking ref first-parent from the run's own `protected_branch_head`, which must be
its ancestor, over commits that change `<friction-log>`. It takes a commit only when the
commit moves every block the run decided to file or archive out of `<friction-log>` and
into `<friction-log-archive>`, and only when exactly one commit does; otherwise the state
stays held. The merge commit, recorded or found, must be a full object id (40 to 64
lowercase hex) reachable from that ref, and it must be the sweep
itself: every frozen block the run decided to file or archive is in `<friction-log>` at
its parent, absent from `<friction-log>` and present in `<friction-log-archive>` at that
commit, and absent from `<friction-log>` at the protected ref. That shows this run's
blocks left the inbox, so a new session cannot re-file them. Nothing
such a run recorded is in flight, so it may offer `retire-terminal-invalid-state` under the same quarantine,
receipt, and approval sequence as abandonment; its action core additionally binds a
`terminal_evidence` summary of the session, verified tracker identifiers, pull request,
merge commit and whether it was `recorded` or `found-in-git`, the ref it was found on,
the swept candidate ids, and final head, so the approved digest names the finished writes. The
bytes are retained at the quarantine path, never rewritten. Any other or unreadable
value keeps the state held.
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
| `prepare-invalid-abandonment` | Abandonable or finished invalid state unchanged; record exact action approval, quarantine target, and receipt payload by digest-checked bundle replacement. |
| `quarantine-invalid-state` | Prepared invalid action present; revalidate and rename only the unchanged state to the prepared target. |
| `publish-restart-receipt` | Prepared quarantine target present and state absent; exclusively create and flush the exact prepared receipt. |
| `release-restart-receipt` | Exact prepared receipt present; release the matching owned gate or quarantine only every unchanged proven-stale gate name. |

If any external attempt or verified identifier is present, or absence of either cannot
be proved from readable evidence, abandonment is prohibited, and only the finished-run
retirement above may move the state. Digest-check and atomically
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
