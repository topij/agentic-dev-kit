# Triage friction log — engine CLI

Read this file completely, together with
[`triage-friction-log.md`](../triage-friction-log.md) and its other reference files,
before the first action of any run. It is part of that workflow and as normative as it;
a section cited by name, or as *above* or *below*, may sit in that file or another of
its reference files.

## Contents

- Entry points, inputs and outputs of both engines
- Dispositions, and running from a linked worktree
- Invocation outcome receipts and caller-owned freshness
- Scheduled caller enforcement and launcher integration

## Engine CLI

The configured entry points are `<engine-dir>/triage_friction_log.py` for draft,
approval, accounting, recovery and continuation, and `<engine-dir>/finalize_triage.py`
for a `resume`-defaulting finalization invocation; `paths.engines` and the two
`triage.*_engine` fragments select their installed locations. Both accept canonical RFC 8785
JSON through `--request`. A request file and an `--approval-context` file must be
single-link regular files. The approval-context file is a runtime-attested boundary:
an embedding runtime supplies the current operator or independently read notification
thread there. Proposal or approval JSON cannot establish that identity by repeating a
name. A person who invokes the CLI directly and creates that file is explicitly
attesting the current-session identity and read-back; the engine cannot authenticate a
freestanding local file as a service observation.

Invoke one recognized entry and an explicit context, for example:

```console
uv run <engine-dir>/triage_friction_log.py new --context interactive --request /absolute/path/freeze-request.json
uv run <engine-dir>/triage_friction_log.py resume --context interactive --request /absolute/path/analysis-request.json
uv run <engine-dir>/triage_friction_log.py resume --context interactive --request /absolute/path/approval-request.json --approval-context /absolute/path/runtime-approval-context.json
uv run <engine-dir>/triage_friction_log.py recover --context interactive --request /absolute/path/recovery-request.json --approval-context /absolute/path/runtime-recovery-context.json
uv run <engine-dir>/triage_friction_log.py test --context interactive --request /absolute/path/test-request.json --approval-context /absolute/path/runtime-test-context.json
uv run <engine-dir>/finalize_triage.py --context interactive --request /absolute/path/finalize-request.json --enable-github-forge
```

The freeze request is `{}`. It returns the durable frozen path and candidate index while
the state remains `reserved`. The later analysis request has `proposals`, an ordered
array whose objects contain `candidate_id`, `source_block_digest`, `title`,
`body_without_marker`, `project`, and string-array `labels`; it carries no approval.
The later approval request is
`{"approval":{"command":"approve all","proposal_set_digest":"<digest>"}}`.
Its trusted context is `{"source":"current-session","operator_identity":"<operator>",
"source_read_back":{"approver_identity":"<operator>","text":"approve all",
"proposal_set_digest":"<digest>","payload_digests":["<ordered-digest>"]}}`.
Recovery first returns `recovery_plan` without mutating a gate-only capture. A later
request contains `recovery_approval` with `decision`, `source`, `approver_identity`, and
`core_digest`; the trusted current-session read-back binds those same values.
Every finalization continuation carries `finalize: true`, not only the first: without
it a session in `forge-finalize` or `archive-sweep` does nothing and returns
`operator-held` with `resume_action` `resume with {"finalize": true}`. The first
continuation additionally carries an absolute isolated `worktree`. That path must lie
outside the repository checkout and must not exist yet. The first continuation holds a path inside the checkout, such as a
`.claude/worktrees/` directory, or one containing it, operator-held before the branch or
worktree is created.

External adapters are disabled unless selected explicitly. `--enable-tracker` selects
`github-issues` or `linear` from the merged `tracker.backend`; unsupported backends stop.
`--enable-github-tracker` remains a GitHub-only compatibility flag; the flags are mutually
exclusive. Selection enables only exactly approved payload transitions.

For Linear, set `tracker.project_name` to the project's exact name, `tracker.url` to its
`https://linear.app/...` URL, and `tracker.linear.team_id` and `project_id` to the model
UUIDs. A nonempty `tracker.linear.label_name` must appear in each approved payload's
labels; the adapter never adds labels to an approved payload. Label names resolve to
unique non-group labels in the configured team or workspace. Missing or ambiguous labels
hold the transition. Export a personal API key as `LINEAR_API_KEY` in the invoking
environment; do not put it in tracked config or request JSON. Both Codex and Claude invoke
the same engine beneath `paths.engines`, for example:

```sh
uv run <engine-dir>/triage_friction_log.py resume --enable-tracker --request <canonical-request.json> --approval-context <attested-context.json>
```

The adapter checks project/team membership, pages issue and label connections to
completion, includes archived issues in marker searches, and reads matched issues back
individually. Applied label IDs, group state and team/workspace scope must match the
paginated allowed label catalog, including archived labels. Ambiguous name resolution
holds the transition. Every payload field and destination must match. Network errors, partial
GraphQL data and unusable cursors hold the transition. Read retries and post-create
visibility retries are bounded; the create mutation is never automatically retried.
An uncertain create remains retained for marker reconciliation on resume. An empty
search after an uncertain create is not permission to create again. Authentication and
API conventions follow [Linear's API guide](https://linear.app/developers/graphql).

Because GitHub's issue list lags a fresh
create, that adapter re-reads the list on a short bounded backoff after a successful
create until the list shows the issue the response names, then judges the marker
matches exactly as before; a list that never shows it leaves the create ambiguous.
`--enable-github-forge` permits the
configured isolated-worktree, push, ready pull-request and read-back transitions; the
adapter has no merge action. The CLI has no notification-service flag. A nonempty
unattended new draft therefore hard-stops before creating session artifacts unless an
embedding runtime supplies a notification provider and configured target. An existing
unattended session remains operator-held if that provider later becomes unavailable.
Arbitrary response or receipt JSON in `--request` is transport data and never
substitutes for a provider read-back.

Conventional `--help` prints argparse help and exits. Every execution attempt otherwise
prints a canonical JSON result and returns success for a completed, degraded, or
operator-held transition. A hard stop returns a nonzero status. The result
always reports the capability map, outcome, disposition (below), execution mode, verified tracker
identifiers, recovery plan when present, safe
resume action and detail, observed protected head when a write preflight ran, and the
retained pull-request URL and observed/reviewed heads when authoritative evidence exists.
It reports the configured engine mode after configuration has loaded, the frozen
snapshot path after active-state validation, and the report path when that state carries
an exact report binding; those fields are null before their respective authority exists.

## Dispositions

`operator-held` names both a legitimate wait for the operator and a refusal, and the
CLI exits 0 for both, so neither the outcome nor the exit status tells a scheduled
caller whether the run progressed. Every result therefore also carries:

| Key | Values |
|---|---|
| `disposition` | `completed` for `successful-completion` or `degraded-success`; `waiting` when the run left an active session at a phase a later invocation or an operator decision continues, judged by that phase and its last retained write (an unresolved tracker write or an unverified forge write reads `waiting` on `reconciliation`, with the capability map saying why); `refused` for every other result, including a hard stop. |
| `waiting_on` | for `waiting` only, else null: `analysis` (an interactive resume supplies proposals), `notification-delivery` (a resume reads back the retained notification attempt; one whose read-back stays unresolved may need the operator), `approval`, `tracker-write` (a resume with the tracker adapter selected), `finalize` (a resume carrying `finalize: true`, with `--enable-github-forge`), `recovery-approval`, `rerun` (an applied state-present recovery left state the next ordinary run continues from), or `reconciliation` (the last retained write is unverified. A tracker write is read back on each rerun and advances once the tracker shows exactly the recorded write, which may need the operator, such as removing a duplicate. A forge write other than an unsettled `pr-watch` or `merge-read-back` is not read back again, so no rerun advances it and it needs the operator; the exception is a failed `branch-create`, which a rerun retries once read-back shows it left nothing. A scheduled caller should alert on `reconciliation` rather than wait). A gate-only or test-gate recovery ends in its terminal held receipt, which reads `refused` until the operator acts on it. |
| `refusal_code` | for `refused` only, else null: `repository-identity`, `configuration-identity`, `single-writer-gate` (the gate could not be acquired: another invocation holds it, its owner is not proven dead, or its record cannot be read or validated), `active-state` (`new` against an active session), `invalid-invocation`, or `unclassified`. |

The disposition is derived from the outcome, and an `operator-held` result is `waiting`
only where the engine names what it waits on; any other is `refused`. A session resting
in `propose` (an unattended draft that had no notification provider) has no
continuation, so a result reporting it is `refused`. Classify on these keys, never on
`detail`.

A scheduled caller can read a durable invocation outcome receipt instead of parsing
an agent's summary. The caller-owned freshness contract below binds each receipt to
a particular engine CLI call; it does not attest an entire agent conversation.

Repository identity is the main worktree's root for every worktree of one repository
whose main worktree is a checkout (a bare repository's linked worktree, one whose
primary used `--separate-git-dir`, any linked worktree on a Git older than 2.36, and
every checkout on a Git older than 2.31 name themselves; *Repository identity* in
[`triage-friction-log.md`](../triage-friction-log.md)), so a scheduled
run in a temporary linked worktree continues the session a primary-checkout run
started, provided both resolve the same state directory: a shared absolute
`DEVKIT_STATE_ROOT`, a `.devkit_state_root` marker, or a worktree `state/` that is a
symlink to the primary checkout's. An independent clone of the same remote is refused
with `repository-identity`, however it shares the state directory. A draft started in a
linked worktree writes its report below the primary checkout's `triage.report_root`, so
the scheduled run must be able to write there. Every run that writes the report checks
that directory is writable first: a draft before it reserves a session, and a resume
before it rebinds or advances the session. Otherwise it stops with `hard-stop` and the
gate released. A completed session that a session-starting entry retires first stays
retired (its bytes kept, as *Completed-state retirement* describes), and the next run
starts fresh.


## Invocation outcome receipts

The caller allocates a fresh invocation id and a fresh absolute receipt path **before
every engine CLI call**, including retries and continuations. Keep that expectation
outside agent-authored output. Use a random UUID for the id and a new private directory
for the call's artifacts, beneath a caller-owned job artifact root. Resolve that
parent's path before passing it: the storage reader refuses symlink ancestors, including
an unresolved system temporary-directory alias. The parent must already exist.
Scheduled callers use the allocation API under *Scheduled caller enforcement* below;
receipt flags alone are insufficient for scheduled execution. Interactive calls may
continue without receipts.

Pass `--outcome-receipt <absolute-path> --invocation-id <fresh-id>`, or set
`DEVKIT_TRIAGE_OUTCOME_RECEIPT` and `DEVKIT_TRIAGE_INVOCATION_ID` in that call's
environment. An explicit flag overrides its environment value. Both the path and id
are required when either is supplied. The id must match
`[A-Za-z0-9][A-Za-z0-9_-]{0,127}`. These are transport inputs, not configuration keys.
Neither the engine nor the checker generates the caller's expected identity.

The CLI refuses an occupied destination before invoking the engine. It publishes a
canonical JSON receipt with exclusive creation after the engine returns, preserving
any file another writer placed there in the meantime. It never deletes or overwrites a
receipt. Publication failure makes the CLI exit nonzero while preserving the printed
engine result: the engine may already have acted. Inspect retained workflow state
before deciding how to continue; absence of evidence is not evidence of no side effect.

A malformed command line, `--help`, a failed receipt preflight, an unhandled exception,
or a killed process may leave no receipt. Fresh identity, not removal of previous
files, prevents an earlier result being accepted for that call. **Never reuse an id or
path, even after failure.** The checker cannot detect reuse of the same expected id
against an earlier valid receipt. An unwritable destination does not authorize the CLI
to clear an old artifact, and it cannot guarantee removal from such a destination.

After the process has exited, check using the expectation retained before dispatch:

```console
uv run <engine-dir>/triage_friction_log.py --check-outcome-receipt <absolute-path> --invocation-id <fresh-id> --expect-entry resume --expect-context unattended --expect-mode live
```

`--expect-entry` is `auto` when the draft CLI's positional entry was omitted, otherwise
it names that entry. The finalize CLI defaults the execution entry to `resume`; its
receipt checks do not inject that default. `--expect-context` and `--expect-mode` are
required alongside `--expect-entry`. A refusal before mode discovery records `unknown`
and stays refused; a waiting or completed receipt with unknown mode is malformed.
The checker ignores publishing and caller environment variables and accepts no
execution flags. A valid checker invocation and `--help` perform no writes. Malformed
CLI arguments in a caller run retain a rejection in that run, without changing receipts.

| Check verdict | Exit | Caller interpretation |
|---|---|---|
| `completed` | `0` | The engine returned successful or degraded completion; inspect its result for the scope and limitations. |
| `waiting` | `0` | A classified continuation is pending, not a completed job; use `waiting_on`. Alert on `reconciliation`. |
| `refused` | `1` | The engine refused the transition; use `refusal_code`. |
| `evidence-missing` | `2` | No outcome exists at the expected path. |
| `evidence-stale` | `2` | The receipt belongs to another invocation id. |
| `evidence-wrong-invocation` | `2` | Entry, context or known mode differs from the expected call. |
| `evidence-malformed` | `2` | Unsafe file, invalid canonical JSON, unsupported schema, digest mismatch or inconsistent result. |

Invalid checker arguments also exit `2`. Require both the invoked process's successful
exit and an acceptable checked verdict; a receipt published before a later process
failure does not override that failure. The ordinary execution CLI preserves its
existing exit convention, so its exit `0` alone still cannot distinguish refusal from
waiting. The receipt contains `kind`, `schema_version`, `invocation_id`, `entry`,
`context`, the full `result`, and `result_digest`. The digest checks internal integrity;
it does not authenticate an agent or process with access to the private directory.

For an agent-driven scheduled job, route **every** engine call through the caller's
per-call launcher so it records a new expectation before dispatch and checks that
call's result afterwards. Do not export a shared id once around an agent run that may
make repeated engine calls. The outer wrapper must retain the call results, reject
failed or missing calls and apply its job-specific policy to the final checked
result. An agent run that never invoked the engine has no outcome evidence. Retrying
with a new id does not retroactively turn a failed scheduled job into success.
Adopting these flags alone does not instrument an existing scheduler; deploy the
enforcement integration below and failure propagation together. Refresh the CLI,
finalize entry, `lib/triage/outcome.py`, `lib/triage/caller.py`, and this workflow
reference from the same kit revision.

## Scheduled caller enforcement

Both CLI entry points require a caller attempt before engine dispatch when context is
`unattended`, or when any of `JOB_NAME`, `AUTOMATION_RUN_ID`,
`DEVKIT_TRIAGE_CALLER_RUN` or `DEVKIT_TRIAGE_CALLER_ATTEMPT` is present (even empty).
An explicit `--context interactive` does not override scheduled markers. These are
transport markers, not job-name configuration. Other schedulers must inject
`DEVKIT_TRIAGE_CALLER_RUN`; the CLI cannot discover an unmarked scheduled process.

Integrate the Python API in `<engine-dir>/lib/triage/caller.py` into the trusted caller:

1. Before launching the agent, call `create_run(root)` with a fresh absolute path
   beneath an existing caller-owned artifact directory. Resolve system temporary
   aliases first. The run directory must not exist; keep other wrapper artifacts
   outside it. Inject `DEVKIT_TRIAGE_CALLER_RUN=str(root)` into **every** agent/tool
   subprocess, including direct CLI calls. Do not set a run-wide attempt or receipt id.
2. Before each engine process, call `prepare_attempt(root, entry=entry, mode=mode)`.
   It returns the absolute attempt path and allocates a fresh id and receipt path.
   Use `read_attempt(root, attempt)` to obtain `invocation_id` and `outcome_receipt`.
   `entry` is `None` for omitted draft entry and `resume` for omitted finalize entry;
   select `live` or `test` as the expected mode. Retain dispatch order in the caller.
3. Pass the expected id and receipt using the existing flags and pass
   `--caller-attempt <attempt-path>` (or `DEVKIT_TRIAGE_CALLER_ATTEMPT` for that child
   only), with `--context unattended`. The caller controls these inputs: its launcher
   must reject agent-supplied overrides. Resolve the configured engine location from
   merged `paths.engines` and `triage.draft_engine` / `triage.finalize_engine`.
4. After the process exits, call `record_exit(root, attempt, returncode)` with its
   actual status, or `None` if launch/timeout handling could not establish a terminal
   status. Do not infer status from stdout or an agent summary. A missing status is
   also failure. Retain evidence; do not remove a failed attempt before retrying.
5. After the agent and all tool processes have ended, call `check_run(root)` and
   fail the job on **any exception**. It checks every allocated attempt, its exclusive
   claim, process status and outcome receipt; a rejected direct call or incomplete
   attempt prevents acceptance even after a valid call. An empty run fails. Returned
   checks prove invocation coverage inside this contract, not job completion, and
   are not dispatch ordered. Also require the agent's successful exit and apply the
   existing final-result policy using caller-retained dispatch order: approval waits
   remain pending, reconciliation requires attention, and unfinished phases are not
   completed jobs. Keep finalization's resume-only and frozen-inbox protections.

The CLI claims an attempt by exclusive creation before reading requests or invoking
the engine. It matches run identity, attempt location, entry, unattended context,
invocation id and receipt destination. Reuse, foreign attempts, missing transport or
an occupied destination return a hard stop before transition side effects. Rejected
direct calls are recorded in the run. A malformed or inaccessible run cannot authorize
dispatch. The final caller must treat unreadable evidence as failure. Read-only receipt
checks and help do not consume attempts. Engine failures, receipt publication failures,
process interruption and mode mismatch remain failures under the final check.

**Trusted boundary:** this protocol enforces dispatch through the installed CLI under
a trusted launcher and filesystem. It is not authentication or a security sandbox.
An unrestricted shell can unset markers, forge or delete evidence, import `engine.run`
directly, or replace engine bytes. Environment detection alone cannot prevent that.
To claim coverage against such a caller, the runtime must mediate tool/process launch,
preserve the run marker, protect caller evidence and engine code, and prevent execution
outside the guarded CLI (for example through a broker with separate authority). The
launcher owns allocation and process-status writes; agent tool calls request dispatch
through it. Prompt instructions and a child-only environment variable do not establish
this boundary. If the runtime cannot provide it, report coverage as trusted/cooperative
only and do not claim enforcement against arbitrary shell bypass. These requirements
do not grant tracker, approval, notification, recovery or workflow-state authority.
