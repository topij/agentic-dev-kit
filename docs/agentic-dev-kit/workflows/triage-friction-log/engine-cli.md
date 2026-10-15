# Triage friction log — engine CLI

Read this file completely, together with
[`triage-friction-log.md`](../triage-friction-log.md) and its other reference files,
before the first action of any run. It is part of that workflow and as normative as it;
a section cited by name, or as *above* or *below*, may sit in that file or another of
its reference files.

## Contents

- Entry points, inputs and outputs of both engines
- Dispositions, and the outcome receipt a scheduled caller checks

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

## Dispositions and outcome receipts

`operator-held` names both a legitimate wait for the operator and a refusal, and the
CLI exits 0 for both, so neither the outcome nor the exit status tells a scheduled
caller whether the run progressed. Every result therefore also carries:

| Key | Values |
|---|---|
| `disposition` | `completed` for `successful-completion` or `degraded-success`; `waiting` when the run left durable state that a later invocation or an operator decision continues; `refused` for every other result, including a hard stop. |
| `waiting_on` | for `waiting` only, else null: `analysis` (an interactive resume supplies proposals), `notification-delivery` (a resume reads back the retained notification attempt), `approval`, `tracker-write` (a resume with the tracker adapter selected), `finalize` (a resume carrying `finalize: true`), `recovery-approval`, or `rerun` (an applied recovery transition left state the next ordinary run continues from). |
| `refusal_code` | for `refused` only, else null: `repository-identity`, `configuration-identity`, `single-writer-gate` (another invocation holds the gate, or its owner is not proven dead), `active-state` (`new` against an active session), `invalid-invocation`, or `unclassified`. |

The disposition is derived from the outcome, and an `operator-held` result is `waiting`
only where the engine names what it waits on; any other is `refused`. A session resting
in `propose` (an unattended draft that had no notification provider) has no
continuation, so a result reporting it is `refused`. Classify on these keys, never on
`detail`.

A caller whose own exit status does not come from the CLI, such as a scheduled agent
run that invokes the CLI itself, asks for an invocation-bound receipt. Choose a fresh
invocation id per scheduled run (`[A-Za-z0-9][A-Za-z0-9_-]{0,127}`) and an absolute
receipt path with no symlinked ancestor, and pass both, as flags or exported:

```console
uv run <engine-dir>/triage_friction_log.py --outcome-receipt /abs/receipts/triage.json --invocation-id run-2026-10-16 --context unattended
DEVKIT_TRIAGE_OUTCOME_RECEIPT=/abs/receipts/triage.json DEVKIT_TRIAGE_INVOCATION_ID=run-2026-10-16 <agent command that runs the CLI>
```

A flag wins over its variable. Each CLI call atomically replaces the receipt with
`kind: triage-invocation-outcome`, the invocation id, `sequence` (the count of calls
under that id), entry, context, mode, outcome, disposition, `waiting_on`,
`refusal_code`, the complete result and its digest. The last call's receipt is the
invocation's outcome. A path given without an id, or an id without a path, a relative
path, or a malformed id is refused before the engine runs, and no receipt is written.
A receipt that cannot be published leaves the printed result in place and makes the
exit status 2.

After the run, check the receipt against the id you chose:

```console
uv run <engine-dir>/triage_friction_log.py --check-outcome-receipt /abs/receipts/triage.json --invocation-id run-2026-10-16 --expect-context unattended --expect-mode live
```

It prints a canonical JSON `verdict` and exits 0 for `completed` and `waiting`, 1 for
`refused`, and 2 for `evidence-missing` (no receipt), `evidence-stale` (a receipt for
another invocation id: an earlier run left it and this one wrote none),
`evidence-wrong-invocation` (the right id, but another context or mode than
`--expect-context` or `--expect-mode`), `evidence-malformed` (shape, digest or field
consistency fails), or a usage error. Treat every exit other than 0 as a failed run,
and read `verdict` and `waiting_on` to tell a pending approval from a completed no-op.

Repository identity is the main worktree's root for every worktree of one repository
(*Repository identity* in [`triage-friction-log.md`](../triage-friction-log.md)), so a scheduled
run in a temporary linked worktree continues the session a primary-checkout run
started, provided both resolve one state root (`DEVKIT_STATE_ROOT` or
`.devkit_state_root`). An independent clone of the same remote is refused with
`repository-identity`, however it shares the state root.
