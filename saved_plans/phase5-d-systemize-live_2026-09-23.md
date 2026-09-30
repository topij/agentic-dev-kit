# Phase 5 D — PHASE5-D-SYSTEMIZE-LIVE-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** This packet
turns the D-SYSTEMIZE-LIVE row of the [D proposal](phase5-d-proposal_2026-09-21.md)
("Subsequent D packages and evidence gates") into an executable scope. It follows the
form of [PHASE5-D-SYSTEMIZE-ENGINE-01](phase5-d-systemize-engine_2026-09-23.md). It
also carries the systemize half of the D-SERVICE notification row, as an exact-payload
item at the routing checkpoint. Topi owns scope changes, each payload approval and
every merge decision.

## Grounding reads

All reads below were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-23.
The protected head was `63f169de6135838ad94b363623954848b251a930`.

- `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha` at 13:47Z printed
  `63f169d…`. `gh run view 35868592468` (the push run for that sha) printed
  `completed` / `success`.
- The configured engine set (`fetch_merged_prs.py`, `digest_merged_prs.py`,
  `heartbeat_cli.py`) is present at that sha, from #769 (`cf83f20`). File presence
  therefore selects engine-backed mode. Each engine's `--help` printed the CLI that the
  shared workflow's *Engine interface* declares.
- The merged config comes from `kitconfig.load_config()`, including the gitignored
  overlay. Its declared values are:
  - `systemize`: `lookback_days: 7`, `backfill_days: 28`, `pattern_threshold: 2`,
    `tracker_severity: high`, `batch_size: 25`, `single_pass_max_prs: 60`,
    `max_findings_prs_per_run: 75`, `operator_logins: []`, `pr_draft: false`;
  - `review.bots: [coderabbit]`, with aliases `coderabbitai` and `coderabbitai[bot]`;
  - `notify.backend: slack`, with `notify.user_key: U082VD4SR2N` from the gitignored
    `config/dev-model.local.yaml`;
  - `vcs.systemize_branch_pattern: chore/systemize-{date}`.
- **Trusted-source discovery.** This is not the run's fetch. The command was
  `gh pr list --state merged --search "merged:2026-08-26..2026-09-22" --limit 300 --json number,mergedAt,reviews,title`.
  It returned fewer rows than its limit. The merged PRs in that window with a
  `coderabbitai` review object are:
  #599, #637, #648, #653, #684, #686, #688, #689, #690, #704, #716, #718, #724, #725,
  #726, #727, #733, #734, #742.
  Of those, only #742 merged inside the 7-day window ending 2026-09-22.
- **The fallback panel's findings are invisible to this workflow.** On #769, the
  panel's round reports and dispositions are PR issue comments posted by `topij`. Two
  things exclude them:
  - The shared workflow treats discussion comments as "context, not findings".
  - `systemize.operator_logins` is empty, so no `topij` review object counts either.

  Every PR where CodeRabbit skipped review and only the panel reviewed is therefore
  finding-free to systemize. That covers most PRs since #742. Whether this gap needs a
  tracker item is a separate decision; see *Preparation observations*.

## Proposed approval: PHASE5-D-SYSTEMIZE-LIVE-01

**Purpose:** one real, engine-backed, `live`-mode `post-merge-systemize` run over a
complete configured window, in a new isolated kit checkout. It proposes every route the
evidence supports, as exact payloads, then stops. Each routed write executes only after
Topi approves that exact payload. No recurrence, rule or issue may be invented to
exercise a route.

### Decisions bound by this approval

1. **Window: the configured `backfill` entry point, closed at 2026-09-22.**
   - The engine arguments are `--mode live --window-days 28 --date 2026-09-22`. That
     covers `2026-08-26T00:00:00Z` through `2026-09-22T23:59:59Z`: the whole UTC days
     ending on that date.
   - **Why backfill:** the 7-day window holds one trusted-source PR (#742). The
     `pattern` route needs `pattern_threshold` distinct PRs, so a 7-day run cannot
     reach the rule route at all.
   - The backfill window is a configured entry point, not a handpicked list. It also
     contains the #739–#742 set that Stage A suggested, which the D proposal permits
     only in this form.
   - **Why a closed date:** a window ending today would still be gaining merged PRs
     while the fetch runs. A closed window gives a population that no later merge can
     change.
   - **Alternative:** the normal 7-day window with the same date. The rule route could
     not qualify, and the run would record that as a structural no-rule result rather
     than a finding.
2. **Workspace.** Bind `D=/private/tmp/adk-phase5-d-systemize-live-20260923` and
   `K="$D/kit"`.
   - Refuse if `$D` already exists. Never reset or remove it.
   - Make a fresh `git clone https://github.com/topij/agentic-dev-kit "$K"` and detach
     it at `63f169de6135838ad94b363623954848b251a930`.
   - Copy `config/dev-model.local.yaml` in byte for byte, and verify it by SHA-256 at
     the destination.
   - Require the clone's and the control checkout's `config_fingerprint`s (computed by
     the engines' own config module) to be equal before the fetch.
   - Use absolute paths for every write, and assert `pwd` before each write sequence.
     No write goes to the control checkout except the evidence namespace below.
3. **State root.** The run uses the clone's own `state/` through production resolution.
   `DEVKIT_STATE_ROOT` is unset, and `$K/.devkit_state_root` must not exist. The live
   run therefore exercises the production resolver path, and it stays isolated because
   the whole checkout is.
4. **Head binding.** The fetch envelope's `protected_branch_head` must be `63f169d…`.
   If `main` has moved by execution time, stop and present the new head and its diff as
   a re-binding amendment. Do not run on a moved head without that approval.
5. **An approval overlay on top of the workflow.** The run is interactive and `live`,
   and every route write is held for exact-payload approval.
   - This is stricter than the workflow in one disclosed respect. Unattended, the
     workflow appends friction incidents without approval. Here, a declined block is
     recorded in the report as `declined by operator` and is not written.
   - The routing table itself is applied unchanged: every cluster still gets exactly
     one route.
6. **Reconcile before drafting.** Search each incident's mechanism in three places:
   - `docs/kit-friction-log.md`;
   - a scoped search of `docs/kit-friction-log-archive.md`, using a fixed literal
     subject;
   - the tracker, in all states.

   An incident that is already recorded is proposed as `already recorded: <pointer>`
   beside its table route, and Topi decides whether to write anything. This applies the
   Stage A friction row's reconciliation requirement.
7. **Carrying friction entries to `main`.** The workflow's friction route appends in
   the run's checkout and does not commit, so the clone holds the only copy.
   - Approved blocks are appended in the clone and read back there by SHA-256.
   - They are then carried byte for byte into this session's wrap-up branch
     (`chore/…`), which is this repository's normal carrier for friction entries. The
     block hash is verified again there.
   - Merging the wrap-up PR stays Topi's decision.
8. **Compute.** `systemize.analysis_tier` is `expensive`, which maps to `fable` on
   Claude. This session runs Opus 5.5 and cannot switch its own model, so the tier is
   guidance only and no switch is claimed. Clustering is agent-executed in both engine
   modes; the engines verify fetch and digest only.

### Stage 1 — executed on this approval, ending at the routing checkpoint

1. **Workspace:** set up as in decision 2. Record `git -C "$K" rev-parse HEAD`, the
   overlay hash and both fingerprints.
2. **Preflight:** run the workflow's capability table and record each row as `ready`,
   `degraded` or `stop`, with the mechanism used. This includes the trusted-source union
   and the non-creating path resolution for the cache, digest, report and heartbeat.
3. From `$K`, run each engine with `python3 -B "$K/scripts/<engine>"` and the arguments
   from decision 1, in this order:
   - `heartbeat_cli.py start`
   - `fetch_merged_prs.py` → check the head binding (decision 4)
   - `digest_merged_prs.py`
   - `digest_merged_prs.py --verify <digest path>`, which must exit `0`
   - `heartbeat_cli.py tick --step digest --run-identity-digest <digest>`

   For every call, retain the exit status, the stdout envelope and the stderr.
4. **Cluster** from the digest only. Use one pass if `single_pass_recommended` is true.
   Otherwise use `n_batches` slices, with a `tick --step cluster --slice i/n` after
   each.
5. **Route:** apply decision 6, then the routing table. Draft each payload exactly:
   - friction blocks as bytes;
   - tracker title, body, labels and an idempotency marker;
   - the rule patch as a diff, plus the PR title and body;
   - the Slack DM text.
6. **Write the report** at `$K/reports/post-merge-systemize_28d_live_2026-09-22.md`
   before any external route. It includes the capability preflight, cap disclosure, the
   addressed tri-state per finding, every cluster with its route, and every proposed
   payload in full.
7. **Retain evidence** under
   `state/review-evidence/phase5-d-systemize-live-01/` in the control checkout, with
   SHA-256 values: the raw bundle, the digest, the `--verify` result, the heartbeat
   state, the report and the terminal logs.
8. **Routing checkpoint: stop.** Present the report and the payload list. The heartbeat
   stays open across the pause; the engine has no staleness expiry.

### Stage 2 — each item executes only on its own exact-payload approval

- **Friction:** append the approved blocks in `$K/docs/kit-friction-log.md`, read them
  back by hash, then carry them as in decision 7.
- **Tracker:** search before creating, using the idempotency marker and key terms, in
  all states. Then run `gh issue create` in `topij/agentic-dev-kit` with the approved
  payload, and read it back with `gh issue view`. An ambiguous result is held and not
  retried.
- **Rule** (only if a real pattern qualifies):
  - Create a fresh isolated worktree from `origin/main`, on branch
    `chore/systemize-2026-09-22`.
  - Stage exactly the intended paths. Commit with `systemize.commit_subject` and push.
  - Open a ready PR, then run `pr-watch --assert-ready`.
  - Follow `pr-watch` to green and review-clean, including `make test` in that worktree
    and the fallback panel. **No merge.**
- **Notification:** save the exact DM text and a marker to the report before sending.
  Send to `U082VD4SR2N` through the Slack send tool. Keep the returned channel and
  message identifiers and the sender identity. Read the message back independently.
- After each attempt, update the report. Then run
  `heartbeat_cli.py complete --reason complete`, or `error` after a genuine hard stop.
  A failed completion marks the run incomplete.

### What counts as a result

- **A live no-pattern result is a result.** If no cluster reaches
  `pattern_threshold`, the report records a live no-rule outcome. Topi then decides
  whether positive rule-route coverage is still required (Stage A's rule row). If no
  incident reaches `tracker_severity`, the tracker route likewise gets an explicit scope
  disposition rather than an invented issue.
- **Cap and batching are not expected to trigger live.** The discovery list above is
  shorter than `single_pass_max_prs`, so both branches stay with
  D-SYSTEMIZE-BOUNDARIES' labelled synthetic route.

### Excluded

- Scheduler wiring and #747.
- Installation into any field checkout.
- Merging any PR.
- D-SYSTEMIZE-RECOVERY cutpoints, D-SYSTEMIZE-BOUNDARIES corpora and D-FRESH-CONTEXT.
- All triage work.
- Any config change, including `operator_logins`.
- Closing or editing an existing issue.
- Writes to the control checkout outside the evidence namespace and the wrap-up
  carry.

### Stops

Keep the checkpoint and propose a bounded amendment on any of these:

- `$D` already exists;
- the head binding or the overlay hash fails, or the fingerprints differ;
- a partial engine set;
- a non-zero exit from any engine;
- a `--verify` disagreement;
- a required capability reports `stop`;
- a dirty destination on the rule route;
- an ambiguous external result, which is held and not retried;
- a needed action outside this scope.

**Approval wording:** "I approve PHASE5-D-SYSTEMIZE-LIVE-01 Stage 1 as scoped: a live,
engine-backed backfill run over 2026-08-26..2026-09-22 in a new isolated clone at
63f169d, stopping at the routing checkpoint with every proposed write shown exactly; no
external or friction write without per-payload approval."

## Preparation observations (not part of the approval)

- **The fallback panel is invisible to systemize** (see the grounding reads). The run
  will measure only CodeRabbit evidence, while most recent review in this repository
  happened through the panel. This looks issue-shaped: the mechanism is named, and the
  fix is a design choice. The choices include structured review objects from the
  panel, or panel-report parsing as a trusted source. Filing it is a separate tracker
  write for Topi to decide, before or after the run.
- **#748:** the run's report will show the addressed tri-state on live threads. That is
  evidence for the pending judgment on whether #769 discharges #748.
- **#7:** #769 delivered fetch, digest and heartbeat. The issue body also names the
  donor's `nightly_digest.py`. Whether #7 closes is a separate decision.
