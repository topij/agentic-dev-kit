# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it at the end (`/wrap-up`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-09-23 — Phase 5 D-SYSTEMIZE-LIVE run completed; its rule PR merged.
Phase 5 delivery item 5 remains incomplete; item 6's replay remains complete.

## Latest session — 2026-09-23 (Phase 5 D-SYSTEMIZE-LIVE run, in Claude Code)

**Approval.**
- The operator approved PHASE5-D-SYSTEMIZE-LIVE-01 Stage 1 as written in its packet,
  then each Stage 2 payload individually.
- The packet is `saved_plans/phase5-d-systemize-live_2026-09-23.md` (local, not
  committed).
- The approval records, logs, raw bundle, digest, final report and checksums are under
  `state/review-evidence/phase5-d-systemize-live-01/`.

**The run.**
- A live, engine-backed `post-merge-systemize backfill` with run date 2026-09-22, so
  the window was 2026-08-26..2026-09-22.
- It ran in a fresh clone at `63f169d` under
  `/private/tmp/adk-phase5-d-systemize-live-20260923/`.
- Fetch, digest, `--verify` and every heartbeat step exited `0`, and the heartbeat
  completed.
- The window did not trigger the cap or batching branches, so those stay with
  D-SYSTEMIZE-BOUNDARIES.

**Routes.**
- **Rule:** [PR #771](https://github.com/topij/agentic-dev-kit/pull/771) merged as
  `5165a3c`, whose tree equals the reviewed head `347d323`.
  - It adds "Evidence outside a promotion bundle" to `live-validation-evidence.md`, and
    makes `upgrade.md`'s kit fetch and branch creation stop on failure.
  - Review: a fallback panel at `6b25617`, where both lenses reported the same LOW
    imprecision. The operator approved amended wording, and a LOW `fallback:delta`
    review followed at `347d323`.
- **Notification:** one Slack DM, read back as channel `D083840DP7B`, ts
  `1790183998.138169`. It lands in the operator's self-DM because the connector acts
  as the operator. An occurrence was added to #198.
- **Tracker and friction:** no write. Every single-PR cluster was already addressed or
  superseded, and the operator declined each proposed entry. No tracker payload was
  drafted. Whether these two routes still need a live positive write is an open
  operator decision under the Stage A rows.

**Filed this session, on the operator's direction:**
- #772: fallback-panel findings are invisible to systemize;
- #773: the digest's `TEXT_LIMIT` truncates CodeRabbit findings before their substance;
- #774: routing of an addressed single-PR cluster.

**Verification.** `make test` in `/private/tmp/adk-phase5-d-systemize-live-20260923/rule`
at `6b25617148ecd042d0ce20f5c3cbb2a734a305dc` on 2026-09-23 exited `0` and printed
`3494 passed, 1 skipped`. The wording repair `347d323` got focused `pytest` runs in the
same worktree, and CI passed at both heads.

**Not established:**
- installation into a field checkout;
- scheduler wiring (#747);
- D-SYSTEMIZE-RECOVERY, D-SYSTEMIZE-BOUNDARIES and D-FRESH-CONTEXT;
- the triage side of D-SERVICE;
- any live tracker or friction write from systemize.

Also still open: #748 and #7 await a judgment on whether #769 discharges them, and
#722's owed record edits were not taken in this wrap-up.

▶ Next: `/session-start` — then get the operator's decision on whether systemize's
tracker and friction routes still need a live positive write, and pick the next D
package (D-SYSTEMIZE-BOUNDARIES, D-SYSTEMIZE-RECOVERY or D-TRIAGE-RESIDUAL) from the
D proposal's table (`saved_plans/phase5-d-proposal_2026-09-21.md`, local).

______________________________________________________________________

## Session — 2026-09-23 (Phase 5 D systemize engines delivered, in Claude Code)

**What merged.** [PR #769](https://github.com/topij/agentic-dev-kit/pull/769) merged as
`cf83f2000f9745eb8e1428c467d890d26ae7f643`. Its tree matches the reviewed head
`d4c003c73ecfada2b0244a2396b5b0347578345b`. The PR delivers the configured
post-merge-systemize engine set:

- `scripts/fetch_merged_prs.py`;
- `scripts/digest_merged_prs.py`;
- `scripts/heartbeat_cli.py`;
- `scripts/lib/systemize/`.

With all three files present, this repository's own systemize runs are now
engine-backed. The PR also adds `systemize.heartbeat_job` and
`systemize.heartbeat_pattern`, which are required only in engine-backed mode. And the
shared workflow now takes addressed state from forge thread resolution, not reply
text. #748 stays open, so review can judge whether that definition discharges it.

**Approval.** The operator approved PHASE5-D-SYSTEMIZE-ENGINE-01 interactively, then
its inventory amendment for `scripts/kit_doctor.py` and `scripts/tests/test_kit_doctor.py`.
The operator then directed the merge. The packet is
`saved_plans/phase5-d-systemize-engine_2026-09-23.md`, which is local and not
committed, like the D proposal. The requirement ledger, approval records and
installed-check evidence are under `state/review-evidence/phase5-d-systemize-engine-01/`.

**Review.** CodeRabbit skipped the review because auto-review is disabled on this
repository. The fallback panel ran instead, and the PR comments carry each round's
disposition and the verification stamps. The receipt at the merged head is a
correctness delta composed on a full-panel receipt at
`69db4479f335bcae9306c5c4b1954271fd989c8f`.

**Not established by this delivery**, and each still needs its own approval:

- a live or test systemize run with routing;
- installation into any field checkout;
- scheduler wiring;
- tracker or notification writes.

**Local `make test` hazard.** On 2026-09-23, `make test` could not start in this
control checkout. A mode-000 file inside the gitignored
`state/review-evidence/item5-b-p3-update04-*` tree crashed `scripts/conftest.py`'s
state snapshot at import, which is #461's mechanism; an occurrence was added to #461.
This session verified every candidate in a clean clone instead.

The next session ran D-SYSTEMIZE-LIVE; the latest session block owns its outcome.

______________________________________________________________________

## Session — 2026-09-23 (Phase 5 D triage engines delivered, in Claude Code)

**Session switch and the gap in this handoff.** The operator moved Phase 5 D from Codex
to Claude Code during review of the report rendering. The Codex sessions of 2026-09-14
through 2026-09-22 did not update this handoff. Those sessions were Phase 5 Stage A,
the B/C archive work and the D proposal, and kit PRs merged during that span
(`git log --since=2026-09-14 origin/main`). Their records are:

- the `saved_plans/phase5-*` files, which are not committed at this wrap-up;
- the gitignored evidence under `state/review-evidence/`;
- those PRs.

**What merged.** [PR #765](https://github.com/topij/agentic-dev-kit/pull/765) merged as
`b808061ffd2b813e5dc11e67d118d9b7519fc085` from reviewed head
`20ef06b5a95a685367f1172266a8d909f82f0201`, and its tree matches that head. It delivers
the configured triage draft and finalize engines: `scripts/triage_friction_log.py`,
`scripts/finalize_triage.py` and `scripts/lib/triage/`. The approvals were
PHASE5-D-TRIAGE-ENGINE-01 plus its inventory, accounting, source-rendering and
report-boundary amendments.

**How the repair loop ended.** Earlier rounds had fixed one report field at a time. The
final repair renders every report value as literal content at one boundary. The ready PR
opened once that candidate was verified. The operator's delta disposition and both
Claude fallback lenses then ran on it, under a blast-radius stopping rule that the
operator chose. The PR's comments carry the head verification stamp and the panel disposition.
The local evidence index is
`state/review-evidence/phase5-d-triage-engine-01/CLAUDE-CONTINUATION-20260923.md` and
its addenda.

**Tracker activity this session.** The original platform-stopped Codex adversarial
request was not retried. Filed this session:

- #766: a LOW coverage gap in `_markdown_mask`;
- #767: this package's per-site repair loop, and the delta-review route it lacked
  without a PR.

An occurrence was also added to #416.

**Not established by this delivery**, and each still needs its own approval:

- live tracker or notification operation;
- engine installation into any field checkout;
- a production friction-log sweep.

The friction inbox therefore waits for `triage-friction-log` under separate
authorization.

The next session took D-SYSTEMIZE-ENGINE; the 2026-09-23 systemize-engines block owns its outcome.

______________________________________________________________________

## Session — 2026-09-13 (ITEM5-B PR continuation execution, in Codex)

The operator approved ITEM5-B-PR-02 as scoped, later approved sending its private
review inputs to OpenAI's Codex service for the remaining adversarial review, and
requested autonomous session finalization with merge-when-clean authority for the
scoped kit records. The [execution record](../saved_plans/phase5-item5-b-pr02-execution_2026-09-13.md)
owns the applied CI payload, publication, local/hosted verification, review outcomes,
retention pointers and final preservation checks. The historical packet remains intact.

The record separates the disclosed local source #393 failure from hosted success
and accounts for #561's syntax-check gap. The inherited special-file-root limitation
remains. Preserved-file ownership acceptance is not functional verification or field
exit. Item 6/replay, #723's approved deferral, #585's earlier placement and #724's
delivered #722 batch retain their existing scope. The friction sweep stays parked.

The latest session block owns the subsequent state and next decision.

______________________________________________________________________

## Session — 2026-09-12 (ITEM5-B fixture PR continuation packet, in Codex)

The operator selected preparation of the separate fixture PR continuation decision.
The [PR-02 packet](../saved_plans/phase5-item5-b-pr02-decision_2026-09-12.md)
binds the retained UPDATE-03 checkpoints, existing private fixture PR identity,
CI payload, replacement title/body, verification, publication, review and rollback.
The packet's stamped readbacks retain the local/forge comparisons and validation
limits. Preparation leaves the retained fixture/source and fixture PR unchanged.
The packet preserves the preparation-time question; the subsequent execution record
owns the later approval and execution outcome.

Kit [#736](https://github.com/topij/agentic-dev-kit/pull/736) delivered UPDATE-03's
execution record as `2b272a939013538a740f68f3990a6cc961c9512f`, from reviewed head
`ae6f11c4646c1a666e7049fed20b30b88c73e850`; its
[review disposition](https://github.com/topij/agentic-dev-kit/pull/736#issuecomment-5643887657)
retains the panel and verification limitations. UPDATE-03 and UPDATE-01 are consumed;
UPDATE-02 remains historical and unanswered. Source remains the approved pin
`7e0232ed871b37a315c5509c97b83d3b00b1a3fd`; the fixture input remains the local
attempt `4ad91c875377d8607082cd0a125ba801218187ed`.

The inherited special-file-root limitation and ownership-only custom wrap-up boundary
remain. Item 5/field exit is incomplete; item 6/replay, #723's approved deferral,
#585's earlier placement and #724's delivered #722 batch are preserved. The friction
sweep remains parked, and no credited exercise is repeated.

The latest session block owns the subsequent execution and next decision.

______________________________________________________________________

## Session — 2026-09-12 (ITEM5-B approved retained update, in Codex)

The operator approved ITEM5-B-UPDATE-03 as scoped in its packet. The
[execution record](../saved_plans/phase5-item5-b-update03-execution_2026-09-12.md)
retains exact authority, fresh r4/r5 preconditions, source advance, fixture payloads,
predicted baseline, complete suite output, final preservation checks and backups.
The retained source is pinned to `7e0232ed871b37a315c5509c97b83d3b00b1a3fd`;
the local fixture attempt is `4ad91c875377d8607082cd0a125ba801218187ed`.
No fixture push or PR continuation occurred. UPDATE-03 is consumed; UPDATE-01
remains consumed and UPDATE-02 remains historical and unanswered.

The record separates installed verification from the disclosed source #393 failure,
and retains separate shell parses for #561's recipe gap. The accepted inherited
special-file-root limitation remains. Ownership acceptance does not establish
custom wrap-up functionality, client verification or field exit. Item 6/replay,
#723's approved deferral, #585's earlier placement and #724's delivered #722 batch
are preserved. The friction sweep stays parked; no credited exercise is repeated.

The latest session block owns the subsequent continuation packet and next decision.

______________________________________________________________________

## Session — 2026-09-11 (ITEM5-B revised retained-update packet, in Codex)

The operator-approved source repair [#734](https://github.com/topij/agentic-dev-kit/pull/734)
merged as `7e0232ed871b37a315c5509c97b83d3b00b1a3fd`, from reviewed head `7224547da0c766a4fd9ee5791e53ddb3f7db6cdf`. Its
[delivery checkpoint](https://github.com/topij/agentic-dev-kit/pull/734#issuecomment-5637494093)
retains the exact-head watch/merge, complete panel receipts, CodeRabbit disposition
and local #393 versus hosted verification limits. Separate shell parses account for
#561's recipe gap. The source repair did not update the retained installation.

The [UPDATE-03 packet](../saved_plans/phase5-item5-b-update03-decision_2026-09-11.md)
selects that immutable source and binds payloads, write ledger, baseline prediction,
preservation, verification, limits, rollback and an exact approval question. Its
read-only audit and forge records retain post-acceptance checkpoint comparisons.
The packet retains complete review receipts before its audit-ordering correction,
with earlier UPDATE-03 questions/evidence preserved and the current `-r5` binding
explicit. The packet records unresolved generic-upgrade bootstrap findings outside
its proposed execution; no further source repair or approved deferral is claimed.
[PR #733](https://github.com/topij/agentic-dev-kit/pull/733) merged on 2026-09-11 as
`e6b8e182466046a820198fa28c8cc52dc06509d0`, from reviewed head
`fc46efa0570f866f19cccf11834f909d5f37cf69`. Its
[completion checkpoint](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5639767232)
retains review, verification, merge readback and the pending exact approval question.
UPDATE-01 is consumed; UPDATE-02 and its old questions, payloads, ledgers and
incomplete review receipts remain preserved.

Packet preparation did not approve retained execution. Ownership acceptance does not establish custom
wrap-up functionality, client verification or field exit. The accepted inherited
special-file-root limitation remains. Item 6/replay, #723's approved deferral,
#585's earlier placement and #724's delivered #722 batch are preserved. The friction
sweep stays parked; no credited exercise is repeated.

The latest session block owns subsequent execution and the next decision.

______________________________________________________________________

## Session — 2026-09-11 (ITEM5-B repair delivery, in Codex)

The operator approved ITEM5-B-KIT-REVIEW-02 and subsequently said “merge when ready.”
[PR #731](https://github.com/topij/agentic-dev-kit/pull/731) merged as
`e6d6e77d118454349f8e8bb046e99ef3009c5f5c`, from reviewed head
`1bd4e10b423b0b4b230fb1a481bbc477de784a61`. The
[merge checkpoint](https://github.com/topij/agentic-dev-kit/pull/731#issuecomment-5629015678)
retains the exact-head merge, forge readback and completed review disposition.
The [execution record](../saved_plans/phase5-item5-b-review-followup-execution_2026-09-11.md)
links the complete panel reports and distinguishes hosted success from the disclosed
local #393 failure. The accepted inherited special-file-root limitation remains;
separate shell parses covered #561's omitted checks without repairing its recipe.

The resume readback used `gh pr view 731` and `gh run list` with the kit repository
and merge SHA from `/Users/topi/Coding/agentic-dev-kit` at
`1bd4e10b423b0b4b230fb1a481bbc477de784a61` on 2026-09-11: merge confirmed and
[post-merge Test run](https://github.com/topij/agentic-dev-kit/actions/runs/34558574354) succeeded.
This record follow-up began from that protected-main merge.

Ownership acceptance does not establish functionality or field exit. The repair did
not update the retained installation. Item 6's replay, #723's deferral, #585's earlier
placement and #724's delivered #722 batch are preserved. The friction sweep stays parked.

The latest session block owns the revised packet and next decision.

______________________________________________________________________

## Session — 2026-09-10 (ITEM5-B acceptance execution, in Codex)

The operator approved ACCEPT-01 and PR-01 as scoped in the
[decision packet](../saved_plans/phase5-item5-b-acceptance-decision_2026-09-10.md).
The [execution record](../saved_plans/phase5-item5-b-acceptance-execution_2026-09-10.md)
retains the fresh UPDATE FINAL audit, PR #729 merge/review readback, exact authority,
applied friction/CI payloads and private fixture PR #1. PR-01 is paused at the recorded
P2 inherited state-root detector gap and P3 wording imprecision; fixture merge remains
excluded. The custom wrap-up acceptance is ownership only, with no client/function claim.

The execution record retains actual local and hosted commands, revisions, dates and
terminal summaries, with #393 separated from installed coverage.
The fixture baseline, retained source and historical update/replay evidence remain
bound to the execution checkpoints. Item 5 remains incomplete, item 6's replay remains
complete, and #723's approved upstream deferral and #585's earlier placement remain.
Kit #724 already delivered the #722 batch. The friction-log sweep stays parked.

The latest session block owns the subsequent repair and next action.

______________________________________________________________________

## Session — 2026-09-10 (ITEM5-B acceptance preparation, in Codex)

The [decision packet](../saved_plans/phase5-item5-b-acceptance-decision_2026-09-10.md)
binds preserved-file acceptance to the update's FINAL evidence, and separately proposes
the fixture friction/CI files, private publication, verification and ready-PR handoff.
It explains the custom wrap-up's ownership-only role and the remaining systemize routes.
Preparation itself did not approve execution; no fixture/source update or client exercise
ran in that pass.

The packet retains the readback of kit #728 and its final review receipt, the new
read-only audit, exact proposed payloads and rollback boundaries. The maintained sprint
status keeps item 5 incomplete and preserves item 6's completed replay. #723's approved
deferral, #585's earlier placement and the delivered #722 batch in #724 remain unchanged.
The budget reminder's bounded triage intake preserved prior state and parked decisions;
it started no new draft, recovery, tracker payload or archive sweep.

`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`22734da7d3aebdf31f846b7e288e50eb99ca7156` on 2026-09-10 finished with the
recorded #393 deep-JSON failure; the packet retains the actual summary and full log.
The operator selected the proposed private fixture destination without authorizing
creation or PR execution.
The [kit review receipt](https://github.com/topij/agentic-dev-kit/pull/729#issuecomment-5619355511)
preceded the audit optimization-refusal fix. The packet preserves the initial audit
bytes and the follow-up refusal/mutation evidence; this defect is separate from #393.

The latest session block owns the subsequent operator approval and execution.

______________________________________________________________________

## Session — 2026-09-10 (ITEM5-B update execution, in Codex)

The operator approved ITEM5-B-UPDATE-01. The [execution record](../saved_plans/phase5-item5-b-update-execution_2026-09-10.md)
retains the source advance, fixture attempt, recorded baseline, complete local suite
results and preservation evidence. Its byte archives and Git bundles preserve the
bounded rollback route. No retained-tree initialization or client exercise was repeated.

The [packet](../saved_plans/phase5-item5-b-update-decision_2026-09-10.md) records the
consumed approval. Preserved-file acceptance, fixture PR lifecycle, adoption completion
and the untested systemize routes retain their separate boundaries. Completed item 6,
its replay evidence, #723's accepted deferral and #585's earlier placement are preserved.
The friction-budget reminder's intake again preserved the existing triage state;
no new sweep or tracker payload was started.

The latest session block owns the subsequent acceptance packet and next action.

______________________________________________________________________

## Session — 2026-09-10 (kit test repair, in Codex)

The operator approved the kit-only #534 slice from the ITEM5-B execution record.
The [repair record](../saved_plans/phase5-item5-kit534-repair_2026-09-10.md) retains
source and synthetic installed verification, command/directory/revision stamps and
limits. Controlled initializer inputs and generated adapter fixtures replace assumptions
about adopter-owned files. The drift-liveness parent follows its child's applicability.
The retained ITEM5-B baseline and completed item 6 replay were not rewritten.

The latest session block owns the subsequent decision packet and next action.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
