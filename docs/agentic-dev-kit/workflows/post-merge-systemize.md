# Post-merge systemize

Scheduled pattern-finding across merged pull requests. Read each pull request's review
findings and originating tracker references, cluster findings by root cause, and ask:

> What recurring shape would a shared repository instruction, shared workflow, or
> configuration change have prevented?

This is the up-route of the friction flywheel. A cluster spanning at least
`systemize.pattern_threshold` distinct pull requests may become a rule proposal. A
single incident routes down to the configured friction log, or to a tracker proposal
when its severity reaches `systemize.tracker_severity`.

The cardinal discipline is no retro-policing. A run with no qualifying pattern is a
normal result. Do not turn one incident into standing doctrine, and do not add a second
runtime-specific copy of shared policy. When uncertain whether findings share a root
cause, keep them separate and route down.

## Resolve configuration

Read `config/dev-model.yaml` first, merged per leaf with the gitignored local overlay.
Every value used below comes from that merged configuration:

- `<handoff>`, `<friction-log>`, and `<engine-dir>` mean `paths.handoff`,
  `paths.friction_log`, and `paths.engines`.
- `<protected-branch>` and `<systemize-branch>` mean `vcs.protected_branch` and
  `vcs.systemize_branch_pattern`, with its documented date substitution applied.
- `<tracker>` and `<notify>` mean the configured `tracker` and `notify` sections.
- `<systemize>` means the complete `systemize` section:
  `systemize.analysis_tier`, `systemize.lookback_days`,
  `systemize.backfill_days`, `systemize.pattern_threshold`,
  `systemize.tracker_severity`, `systemize.batch_size`,
  `systemize.single_pass_max_prs`, `systemize.max_findings_prs_per_run`,
  `systemize.cache_pattern`, `systemize.digest_cache_pattern`,
  `systemize.report_root`, `systemize.report_pattern`, `systemize.fetch_engine`,
  `systemize.digest_engine`, `systemize.heartbeat_engine`,
  `systemize.commit_subject`, and `systemize.pr_draft`. Their values are not
  restated here.
- A workflow invocation means the current runtime's native adapter: `/name` in Claude
  Code or `$name` in Codex.

Validate every required `<systemize>` key before fetching anything. A missing key is a
hard stop that names the key and tells the operator to rerun `./init.sh` or add the
documented value. Do not silently substitute the shipped default: doing so would make
the tracked config stop being the effective contract.

Validate values as well as presence:

- `lookback_days`, `backfill_days`, `pattern_threshold`, `batch_size`,
  `single_pass_max_prs`, and `max_findings_prs_per_run` are positive integers, not
  booleans; `pattern_threshold` is at least `2` so a single incident cannot become
  standing doctrine.
- `backfill_days` is at least `lookback_days`; `batch_size` is no greater than
  `single_pass_max_prs`, which is no greater than `max_findings_prs_per_run`; and
  `pattern_threshold` is no greater than `max_findings_prs_per_run`.
- `tracker_severity` is one of the canonical severities defined in Step 1.
- cache, digest, and report patterns are non-empty repository-relative paths;
  `report_root` is a non-empty repository-relative directory other than the repository
  root; configured engine names and `commit_subject` are non-empty strings; and
  `pr_draft` is a boolean.

Before any derived write, substitute the selected date. Treat the configured cache and
digest patterns as logical `state.dirname` paths. Require `state.dirname` to match the
shared state resolver's declared `STATE_DIRNAME`; a mismatch is a hard stop because the
resolver does not take that directory from config. Require the matching lexical prefix,
remove it, then call the shared `scripts/lib/state_paths` write resolver with
`mkdir=False` during preflight. That resolver must honor `DEVKIT_STATE_ROOT` and
`.devkit_state_root`; its returned state root is the allowed cache/digest root even when
the sandbox is outside the checkout. Do not write those logical paths directly beneath
the worktree. Resolve an existing cache or digest through the shared state read resolver
so its newer sandbox-or-production selection remains authoritative, and record the
actual resolved paths. Resolve the report beneath `systemize.report_root` inside the
repository.

Against each resolved allowed root, reject an absolute configured fragment, `..`
traversal, a parent or target symlink that escapes its resolved allowed root, a report
path outside the repository, a collision among the canonical artifact paths, an existing
non-regular target, or a target already tracked by Git. For every existing artifact
target, require a link count of exactly one and compare its device/inode identity with
the other artifact targets plus tracked and control inputs; reject any alias. Also reject
a target matching a repository control input such as the merged config or an active
instruction/workflow, whether tracked or not. Create parents only after every target
passes this preflight, then publish derived files by atomic replacement. A configured
output label does not make its destination safe.

An invalid value is a hard stop naming the failed invariant. Do not coerce a scalar or
repair relationships in memory: the operator must correct the shared configuration.

`systemize.analysis_tier` must name a key under `models.tiers`. Apply the current
runtime's `models.runtime_mappings` value only when its launcher exposes the relevant
model or effort control. Otherwise state that the tier is instructed guidance. Never
claim that a launcher switched model or effort merely because the config requested it.

## Entry points and execution context

The accepted keywords are `backfill` and `test`; they may be combined. Reject any
unknown argument before preflight.

- With no `backfill`, use `systemize.lookback_days`.
- With `backfill`, use `systemize.backfill_days`.
- With `test`, perform real read-only fetch and analysis, then render the proposed
  routes in the final output. Test mode may write only the derived cache, digest, and
  report plus an optional notification prefixed `[TEST]`; it must not write a branch,
  commit, pull request, friction-log entry, or tracker item. The notification is a real
  optional external write, not an approval or a simulated receipt.

Non-interactive runs never wait for operator input. If an action requires approval and
the invocation does not already carry that explicit approval, preserve the proposal in
the report and take the documented degraded route. Interactive runs may ask for tracker
approval after presenting the exact proposed tracker payload.

The workflow is single-session but resumable from its durable files. Before retrying a
failed run, inspect the report and configured cache/digest paths for the same window.
Reuse an input only when its recorded forge repository, window, protected-branch head,
and config fingerprint match the new run. Never repeat an external write merely because
the previous process ended before its final summary; verify the pull request,
notification, and tracker destination first.

## Capability contract and preflight

Report each capability as `ready`, `degraded`, or `stop`, with the discovered mechanism
or actionable reason. Capability names are runtime-neutral; use the current runtime's
available connector, API, or CLI without copying its tool name into this workflow.

| Capability | Class | Preflight and unavailable behavior |
|---|---|---|
| Repository/config read | required | Confirm the repository root, merged config, `<friction-log>`, and protected branch. Missing or unreadable input stops the run. |
| Forge merged-PR read | required | Prove authenticated access by reading the target repository and a bounded merged-PR page. Missing access or incomplete pagination stops the run. |
| Deterministic fetch/digest/heartbeat set | optional, atomic | Resolve every configured engine under `<engine-dir>`. All present selects engine-backed mode; all absent selects LLM-only mode; a partial set stops rather than mixing incompatible artifacts. |
| Forge/git PR write | conditional | Required only for a qualifying rule route. If unavailable, preserve the proposed patch and evidence in the report; make no partial branch or PR write. |
| `pr-watch` workflow | conditional | Required before calling a created rule PR complete. If unavailable, leave the PR unmerged, mark review follow-through owed, and report the gap. |
| Tracker create | optional and approval-gated | Missing access degrades to a flagged friction-log proposal. Available access still does not authorize a write. |
| Notification | optional | Missing backend or target degrades to the report plus final output. Notification is never the only durable result. |
| Configured reviewer | optional for this workflow | A ready PR may engage it. Unavailability follows `pr-watch`'s shared fallback policy; it never waives review or authorizes merge. |

The engine-backed set is an enhancement, not a prerequisite for runtime parity. The kit
does not vendor those engines yet; issue `#7` owns that integration. LLM-only mode must
produce the same normalized digest and report fields, but it must label clustering and
source classification as agent-executed rather than engine-verified.

Finish preflight before writing a heartbeat, cache, or report. On a hard stop, print the
failed capability and the exact remediation; do not create a failure notification when
notification itself was the failed capability.

## Durable artifacts

Every run may maintain the derived artifacts using the configured patterns. In test
mode they and the optional `[TEST]` notification are the only permitted writes:

- the fetched merged-PR bundle at `systemize.cache_pattern`;
- the normalized review-finding digest at `systemize.digest_cache_pattern`;
- the run report at `systemize.report_pattern`;

Outside test mode, routes may additionally produce:

- routed repository changes: a friction-log append or a proposed shared-rule branch and
  pull request;
- an optional notification that links or points to the report and routed artifacts;
- an optional tracker item only after explicit operator confirmation.

The report is load-bearing. Write it before any external route and update it after each
attempt so a retry can distinguish proposed, attempted, and completed actions. Include:
the forge repository, window, protected-branch head, config fingerprint, execution mode,
capability preflight, cache/digest locations, capped-input status, candidate clusters,
route dispositions, external identifiers actually created, incomplete actions, and the
next safe resume step. Do not record a tracker identifier, notification receipt, review
receipt, or pull-request URL that was not actually returned by that integration.

Cache, digest, state, and report files are derived output. Do not add them to a rule PR.

## Step 1 — Fetch and normalize merged-PR evidence

In engine-backed mode, start the configured heartbeat before the fetch, invoke the
configured fetch engine for the selected window, then invoke the configured digest
engine. The process exit status is authoritative: a warning beside a successful status
is informational; a non-success status is a hard stop. Record the stderr summary and
the emitted artifact paths.

In LLM-only mode, use the proven forge-read capability to fetch every merged pull
request in the selected window with complete pagination. For each pull request collect:
identity and merge revision, review comments and review objects, configured-reviewer
findings, operator review findings, file paths, source text, source identity, severity
when the source supplies one, addressed state when evidenced, and originating tracker
references. Plain discussion without a review finding is not evidence for a cluster.

Normalize every source severity before ranking, capping, or routing. Preserve the
source label beside the normalized value. The canonical order is
`low < normal < high < critical`: `low`, `minor`, `info`, and `informational` map to
`low`; `medium`, `moderate`, `normal`, `warning`, an absent label, or an unrecognized
label map to `normal`; `high` and `major` map to `high`; and `critical` and `blocker`
map to `critical`. Match labels case-insensitively after trimming whitespace. Retain a
numeric or custom source label, normalize it to `normal`, and record the unmapped-scale
limitation in the report; do not invent a source-specific mapping. The threshold route
includes severities at or above `systemize.tracker_severity` in this order.

From the normalized evidence, form the finding-bearing pull-request candidates. Before
serializing or accepting a digest, rank them by maximum normalized severity descending,
then unaddressed finding count descending, then total finding count descending, with
pull-request identity ascending as the stable tie-breaker. Apply
`systemize.max_findings_prs_per_run` to that ordered list. The digest's `prs[]` is exactly
this capped finding-bearing set; preserve the full fetched population in the raw bundle
and record every omitted pull-request identity plus the uncapped finding-bearing count.

Write the full raw bundle, then normalize the capped digest to the shared shape needed
below:

- `window`, `forge_repo`, `protected_branch_head`, and `config_fingerprint`;
- `prs[]`, each with pull-request identity, tracker references, and `findings[]`;
- each finding's source, path, original severity, normalized severity, addressed state,
  guideline-citation state, and cleaned text;
- input-cap state and the configured batching values;
- `findings_pr_count = len(prs)` after the cap,
  `single_pass_recommended = (findings_pr_count <=
  systemize.single_pass_max_prs)`, and `n_batches =
  ceil(findings_pr_count / systemize.batch_size)` (zero when the count is zero).

Engine-backed and LLM-only digests obey this same normalized schema. After either path
produces a candidate digest, recompute the ordered capped identities from the raw bundle,
then recompute the count, recommendation, and batch count from the configured values.
Stop if the artifact's `prs[]`, cap disclosure, or derived fields disagree; a digest
cannot select its own evidence or working-set policy. A cap is a bounded analysis, not
permission to describe the whole window as reviewed.

If the fetched bundle contains no merged pull request, write a complete report saying
there was nothing to systemize, optionally notify, complete the configured heartbeat in
engine-backed mode, and exit successfully.

After the digest is durable, tick the configured heartbeat for clustering in
engine-backed mode.

## Step 2 — Cluster by root cause

Read the digest, never the larger raw bundle. A finding already addressed in its pull
request rarely needs a single-incident route, but it can still support a recurring root
cause. A guideline citation is evidence that an existing rule participated in review,
not evidence that a new rule is needed.

Use one analysis pass only when the validated `single_pass_recommended` value is true.
Otherwise process exactly `n_batches` slices of `systemize.batch_size`, record candidate
shapes from each slice, and reduce them into a single cluster set. In engine-backed
mode, tick the configured heartbeat after each slice. A slice boundary never changes
cluster membership; union distinct pull-request identities before comparing a cluster
with `systemize.pattern_threshold`.

Cluster by causal shape, not similar wording. For each cluster record:

- a root-cause sentence;
- the distinct pull-request identities carrying it;
- the review sources;
- a representative excerpt within source-quotation limits;
- whether an existing shared instruction or workflow already covers it;
- the proposed route and why it meets that route's configured threshold.

Before proposing a rule, search active repository instructions and shared workflows for
an existing rule that covers the shape. If one exists, do not duplicate it. Record a
rule-citation in the report. If the recurrence shows that the existing instruction is
unclear or incomplete, propose the smallest edit to that shared source and label it as a
tightening, not a new rule.

Uncertain or disputed clusters route down as separate incidents. This workflow does not
classify review-evidence deltas and must not infer record-only semantics from filenames,
paths, or prose. Any PR review needed for its own edits follows the shared `pr-watch` and
fallback-panel doctrine unchanged.

## Step 3 — Route findings

### Shared-rule route

A cluster meeting `systemize.pattern_threshold` may produce the smallest instruction,
shared-workflow, or config edit that would have prevented the root cause. Prefer the
narrowest shared repository source. Do not edit a Claude or Codex adapter unless the
finding is genuinely about that runtime's invocation or capability translation.

Add a provenance marker beside each proposed rule:

```text
<!-- systemize:YYYY-MM-DD pattern; PRs #a,#b -->
```

Never switch branches in the caller's checkout or use it as the rule PR's staging area.
Determine the intended destination paths first. If one is staged, modified, or untracked
in the caller checkout, stop the route and preserve the proposal in the report; do not
blend an operator's local edit into the systemize patch. Unrelated caller changes remain
untouched.

Fetch the configured protected branch, then create a fresh isolated Git worktree and
`<systemize-branch>` from its current origin ref. If the branch or worktree already
exists during a resume, verify its base identity, intended patch, and clean status rather
than recreating or overwriting it. If a clean isolated worktree cannot be established,
stop the PR route with the patch preserved; branch-switching the caller checkout is not
a degraded path.

Re-read the destination files in that isolated worktree and apply the proposal to the
fresh base. Before committing, require a clean index before staging, stage each intended
path by name, and prove the staged path set equals the intended destination set exactly.
Any pre-existing change, extra staged path, or missing intended path stops the route.
Commit with `systemize.commit_subject`; never commit derived output. Push and create the
pull request using `systemize.pr_draft`.

The pull-request body gives each pattern's shape, evidence pull requests, review sources,
and exact shared rule location. It makes no merge claim. After creation, invoke the
native `pr-watch` workflow. Its shared review semantics, prompt construction, receipt
schema, delta routing, and stop conditions remain authoritative. Do not merge this rule
PR from `post-merge-systemize`; the operator reviews and decides it.

If branch, push, or pull-request creation fails, preserve the patch and evidence in the
report, stop that route, and do not retry blindly.

### Friction-log route

Append a normal single incident under the most fitting existing heading in
`<friction-log>`, following that file's local format. Include the source pull request,
review source, severity, mechanism known so far, and proposed next diagnostic or fix.
Do not commit the friction-log from this workflow; the configured triage workflow owns
its tracker migration.

When tracker access is unavailable or approval is absent, a high-severity tracker
proposal uses this route with a `**Proposed tracker item:**` prefix and the complete
payload preserved in the report.

### Tracker route

Construct the proposed title, description, project, and labels from `<tracker>` and the
cluster evidence. Show that exact payload to the operator. Create or modify nothing
unless the operator explicitly confirms that payload. Configuration, a scheduler launch,
a prior approval for another payload, and tracker availability are not confirmation.

In a non-interactive run with no prior payload-specific approval, take the flagged
friction-log route and report `approval unavailable`; never pause. In an interactive run,
decline or silence takes the same route. If the tracker write is approved but fails,
preserve the payload and failure in the report and do not claim an identifier.

## Step 4 — Report, notify, and stop

Finalize the report with the actual routes and unresolved actions. If notification is
available, send a concise summary containing the window, evidence scope, cluster routes,
created identifiers, degraded capabilities, cap disclosure, and report location. Prefix
the notification and final output with `[TEST]` in test mode.

In engine-backed mode, the configured heartbeat completion is the final write before the
run summary. Use the successful completion reason for a zero-PR or no-pattern run. Use an
error reason only after a genuine hard stop. If heartbeat completion fails, mark the run
incomplete even when analysis and routes succeeded.

Stop successfully after a no-pattern, zero-PR, or fully recorded degraded run. Stop with
failure after an unavailable required capability, invalid config, incomplete optional
engine set, non-success fetch/digest, unreadable artifact, or failed load-bearing report
write. A route-specific external failure does not erase the report; it leaves that route
incomplete with a copy-pasteable resume action.

Output a concise summary naming the report, input scope, routes actually taken, external
identifiers actually returned, degraded capabilities, and the next safe step.
