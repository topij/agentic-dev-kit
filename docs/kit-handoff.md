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

Last updated: 2026-09-24 — RECOVERY's post-dispatch rerun waits for #786, and
PHASE5-D-FRESH-CONTEXT-01 ran to completion. Phase 5 delivery item 5 remains incomplete;
item 6's replay remains complete.

## Latest session — 2026-09-24 (RECOVERY decision and Phase 5 D-FRESH-CONTEXT run, in Claude Code)

**Decisions, taken interactively.**

- **RECOVERY's post-dispatch cutpoint: fix the gap first, rerun later.**
  - The record is
    `state/review-evidence/phase5-d-systemize-recovery-01/DECISION-post-dispatch-20260924.md`.
  - The cutpoint stays an open Phase 5 E residual. The exit criteria allow no required
    row to be "covered only by a proposed deferral", so at E it needs evidence or an
    approved amendment.
  - The systemize workflow declares no idempotency key and no pre-dispatch attempted
    record for a tracker create or notification. #786 was filed for that, and the
    rerun waits for its fix.
- **PHASE5-D-FRESH-CONTEXT-01 approved** with A1 (ignore the Codex user config), B1
  (untrusted), C1 (`gpt-5.6-sol` at medium) and D1 (an extended fake forge, network off).
  Amendment 1 permitted Codex's automatic trust entry for the run's clone, followed by
  guarded removal. `APPROVAL.md` and `AMENDMENT-1.md` are in
  `state/review-evidence/phase5-d-fresh-context-01/`.
- **The Phase 5 packets stay local.** Whether to commit the whole untracked
  `saved_plans/phase5-*` set is a decision for the Phase 5 E audit.

**The packet.** `saved_plans/phase5-d-fresh-context_2026-09-24.md` is local and not
committed, like the other D packets. Fresh subagents checked successive drafts
read-only, and their corrections are listed in its *Preparation check*. The approved
bytes are also in the evidence directory as `packet.md`.

**The run.** `RESULTS.md` in `state/review-evidence/phase5-d-fresh-context-01/`
(gitignored) owns the outcomes.

- **Setup:** one `codex exec`, given only `$post-merge-systemize test`. It ran in a
  neutral clone at `1cc86cd` plus one disclosed config commit (`lookback_days: 10`),
  against a fake forge with the network off.
- **Observed:**
  - it found the adapter (by injection) and the shared workflow;
  - it read the config, overlay included, and passed `--window-days 10`;
  - it chose engine-backed mode;
  - its routes matched the sealed prediction, and containment was clean.
- **Not matched:** it made no merged-PR preflight read of its own before heartbeat
  `start`, and it ran `--verify` late. Both are parked in the friction log.
- **Scope of the result:** one sample. Whether it discharges the row is the E audit's
  call.

**The Codex trust entries.** `codex exec` wrote `trust_level = "trusted"` entries into
`~/.codex/config.toml` for its working directories, despite `--ignore-user-config
--ephemeral`, sometimes late. That stopped the gate at S3, before the run. After the run,
a guarded edit removed the three `/private/tmp` entries, and the file's SHA-256 matched
its value before this session's first probe. The finding is parked in the friction log.

**Filed this session, each on the operator's approval of the exact payload:**

- #786: systemize has no idempotency key or pre-dispatch attempted record;
- #787: the workflows' "merged per leaf" overlay wording omits the one-leaf allowlist;
- #788: the systemize tests' `FAKE_GH` over-answers and crashes on unknown forms.

**Retained:** `/private/tmp/w-83c93ce1`, the run's namespace, as the packet specifies.

**Still open from earlier sessions:** the #748 and #7 judgments, and #722's owed record
edits.

▶ Next: `/session-start`, then choose between #786's fix, which unblocks RECOVERY's
post-dispatch rerun, and drafting the D-TRIAGE-RESIDUAL packet from
`saved_plans/phase5-d-proposal_2026-09-21.md` (local).

______________________________________________________________________

## Session — 2026-09-24 (Phase 5 D-SYSTEMIZE-RECOVERY run, in Claude Code)

**Approval.** The operator approved PHASE5-D-SYSTEMIZE-RECOVERY-01: Stage 1, and Stage 2
with options A1 and B1. The operator also directed the merges of #780, #781 and #782.
`state/review-evidence/phase5-d-systemize-recovery-01/APPROVAL.md` records those
decisions, a Stage 2 amendment and the Stage 2 stop. `RESULTS.md` in the same directory
owns the outcomes.

**Stage 1: engine and orchestrator kills, synthetic.**

- **Setup:** it ran in a fresh clone at `66a8a10` under
  `/private/tmp/adk-phase5-d-systemize-recovery-01/`, against the kit's fake forge. Its
  predictions were sealed before the first kill.
- **Result:** `python3 -B compare.py` in the evidence directory, on 2026-09-24, printed
  `all fields match` for every case: PRE-1, PRE-2, RAW-1a, RAW-1b, RAW-2a, RAW-2b, DIG-1a,
  DIG-1b, DIG-2a, DIG-2b, PRE-3, HM and HB.
- **Containment:** `harness.py containment` printed `CONTAINMENT OK`.
- **Filed on the operator's direction:**
  - #783: heartbeat `start` reopens a completed run, now seen through the entry point
    after a kill;
  - #784: a kill after the temp write leaves a complete hidden copy that nothing removes.

**Stage 2: agent cutpoints, stopped after run P.**

- **Setup probes:** the first attempt failed, because git's credential helper came from
  the Command Line Tools system config. The operator amended the environment with
  `GIT_CONFIG_NOSYSTEM=1`, and every probe then passed.
- **Run P** was a headless `claude -p --model fable`, isolated by `--strict-mcp-config`
  and `--setting-sources ""`. It stopped at the tracker approval gate with the exact
  payload, made no tracker write, and was killed there.
- **The stop.** P wrote scratch files to literal `/tmp` paths, which is a packet stop, and
  it had read the fake `gh` source and the harness's environment variables. The operator
  stopped Stage 2 and kept P as partial evidence.
- **Not established:** the post-dispatch/pre-receipt cutpoint, and a restarted run
  presenting the payload again. Both go to the Phase 5 E audit as open residuals.
- **What a rerun needs:** an agent that can neither read the harness nor write outside
  its roots.

**Merged on the operator's direction:**

- #780 as `c8497c6295bdf21c073faa5470fb20e1337f5d7c`;
- #781 as `902dbf64bc5a3301ab5817b1cbc78c3effa29f1d`;
- #782 as `3644dc527b375b425ce61a6ae06de1ed832c3c49`.

**Still open:** the #748 and #7 judgments, which are in the next block, and #722's owed
record edits.

▶ Next: `/session-start`, then take two decisions:

- whether RECOVERY's post-dispatch cutpoint gets a sandboxed rerun or stays a Phase 5 E
  residual;
- the next D packet to draft: D-FRESH-CONTEXT, from
  `saved_plans/phase5-d-proposal_2026-09-21.md` (local).

The next session took both decisions; the 2026-09-24 block on the RECOVERY decision and
D-FRESH-CONTEXT owns them.

______________________________________________________________________

## Session — 2026-09-23 (Phase 5 D-SYSTEMIZE-RECOVERY packet, unattended, in Claude Code)

**Mode.** The operator asked for an autonomous session on the plan and then left. No
operator decision was taken while the session ran unattended. The operator's decisions
on its return are under *Operator decisions* at the end of this block.

**The packet.** `saved_plans/phase5-d-systemize-recovery_2026-09-23.md` (local, not
committed) splits the D-SYSTEMIZE-RECOVERY row into a Stage 1 and a Stage 2, each
approved separately:

- **Stage 1** kills the real engines, or the process driving them, at and just before
  the raw and digest cutpoints, then restarts fresh processes from durable files alone.
  It uses a fake forge in a new clone at `66a8a10`, and it is approvable as written.
- **Stage 2** covers the pre-approval and post-dispatch cutpoints, which sit inside the
  agent. It needs operator decisions on which agent process to use (A) and on what
  the post-dispatch cutpoint may touch (B).
  - The packet recommends A1: a headless `claude -p`, isolated by
    `--strict-mcp-config` and `--setting-sources ""`.
  - It recommends B1: a fake tracker only.
- A fresh subagent checked the draft against the code at `66a8a10`. Its corrections are
  folded in, and the packet's *Preparation check* lists them.

**Preparation evidence** is in
`state/review-evidence/phase5-d-systemize-recovery-prep-20260923/` (gitignored). Its
headless probes are what option A1 rests on:

- without isolation, a headless run loaded the claude.ai connectors, Slack included;
- with `--strict-mcp-config` and an empty MCP config it loaded none;
- the user `SessionStart` hook and a synced plugin loaded all the same.

**Found and parked:** `heartbeat_cli.py start` reopens a completed run, which contradicts
the workflow's *Engine interface*. The entry is in the friction log rather than the
tracker, because nobody was present to approve a payload.

**Pull requests opened ready for review:**

- [#780](https://github.com/topij/agentic-dev-kit/pull/780) fixes the handoff footer
  layout that #776 diagnosed. Reviewed head
  `20451840fec7ba74923134ef7c49fc776272bc00`.
- [#781](https://github.com/topij/agentic-dev-kit/pull/781) stops README,
  getting-started and runtime-parity from describing the shipped engines as absent. It
  is #7's fourth work item. Reviewed head `c32189c4acd76b4b150c1e744fe1dd5dbb5ec3d5`.

Each has a fallback panel receipt bound to its reviewed head, and each PR's
disposition comment records the lens results. Both were held for the operator, whose
merges are under *Operator decisions*.

**Judgments prepared, not taken.** Each is the operator's to make.

- **#748.** #769 delivered its first two suggestions: forge thread resolution is
  authoritative, and `outdated` is a state of its own.
  - The third, an honest "unknown", is only partly met. A failed forge read stops the
    run, but a thread with no resolution field digests as `unaddressed`
    (`normalize.thread_addressed`).
  - The options are to retire #748 as delivered, or to narrow it to that mapping.
- **#7.** #769 shipped its work items 1–3, and #781 carries item 4. Field installation
  is Phase 5's own row, not #7's, so nothing in #7's list is outstanding once item 4
  merges.

**Still open from earlier sessions:** #722's owed record edits.

**Sweep.** #780 is not merged at this block's base. So this wrap-up swept with the
repo's own helper, applying the footer restore and trim that the next block describes.
It also swept the same pre-sweep files a second time, as scratch copies, with #780's
helper at `2045184`. On 2026-09-24 the two gave different results:

| Helper | Input | Printed |
|---|---|---|
| repo's own, at `66a8a10` | with the blank line restored | `moved 3 block(s) … (463 -> 379 plan lines)` |
| #780's, at `2045184` | untouched | `moved 2 block(s) … (462 -> 400 plan lines)` |

The old helper counts the blank line it writes itself toward `--target-lines`. This
commit keeps the first result.

**Operator decisions, 2026-09-24.** The approval record is
`state/review-evidence/phase5-d-systemize-recovery-01/APPROVAL.md`, which binds the
approved packet by SHA-256.

- **PHASE5-D-SYSTEMIZE-RECOVERY-01:** Stage 1 is approved as scoped. Stage 2 is
  approved with options A1 and B1.
- **Merges:** the operator directed the merges.
  - #780 merged as `c8497c6295bdf21c073faa5470fb20e1337f5d7c`; on 2026-09-24 `git rev-parse
    <sha>^{tree}` matched its reviewed head's. The next block's footer restore is not needed.
  - #781 merged as `902dbf64bc5a3301ab5817b1cbc78c3effa29f1d`; on 2026-09-24 `git diff` from its
    reviewed head over the three docs it changed was empty.

▶ Next: execute PHASE5-D-SYSTEMIZE-RECOVERY-01 — Stage 1, then Stage 2 with A1 and B1 —
from `state/review-evidence/phase5-d-systemize-recovery-01/packet.md`. If that
directory already holds a `RESULTS.md`, resume from it rather than starting again.

The next session ran RECOVERY; the 2026-09-24 D-SYSTEMIZE-RECOVERY run block owns its
outcome.

______________________________________________________________________

## Session — 2026-09-23 (Phase 5 D-SYSTEMIZE-BOUNDARIES, in Claude Code)

**Operator decisions, taken interactively.** They are recorded in
`state/review-evidence/phase5-d-systemize-boundaries-01/APPROVAL.md`.

- **Systemize live friction and tracker routes.** D-SYSTEMIZE-LIVE ran reconcile →
  propose → decline, with no write. That path is accepted as these routes' Phase 5
  evidence, as an acceptance amendment.
  - The first genuine positive write is a residual carried to the scheduled run
    (#747), not an exit gate.
- **PHASE5-D-SYSTEMIZE-BOUNDARIES-01.** Stage 1 was approved as written; the packet is
  `saved_plans/phase5-d-systemize-boundaries_2026-09-23.md` (local).
- **Its evidence was accepted** for these Stage A rows: cap-triggered omission, batched
  analysis, competing cache mtimes and hostile artifact targets. The acceptance is for
  labelled synthetic coverage, not live coverage.

**The run.**

- **Setup:** the real engine entry points, driven against the kit's own `FAKE_GH` at
  the shipped thresholds. They ran in an isolated clone at `a6b281a` under
  `/private/tmp/adk-phase5-d-systemize-boundaries-20260923/`.
- **Exercised:**
  - synthetic corpora at and across the cap and single-pass thresholds;
  - blind subagent clustering of a batched corpus, scored against a key sealed before
    the agents ran;
  - competing sandbox and production caches;
  - planted hostile artifact targets.
- **Records:** `RESULTS.md` in the same evidence directory owns the outcomes,
  deviations and limits.
- **Writes:** nothing was written to the kit, config, forge, friction log or
  notifications.
- **Baseline:** `uv run --with pytest --with pyyaml pytest -q -p no:cacheprovider
  scripts/tests/test_systemize_*.py`, run in that clone at `a6b281a` on 2026-09-23,
  exited `0` and printed `169 passed`.

**Filed this session, on the operator's direction:**

- #777: after a mid-run parent retarget, cleanup by lexical path leaves a stale lock and
  a temp file behind;
- #778: the digest accepts a raw bundle fetched for another run date.

An occurrence was also added to #643, which is about prompts rendered to a file but
launched inline.

**Not established:**

- live cap or batching behaviour;
- D-SYSTEMIZE-RECOVERY, D-FRESH-CONTEXT and D-TRIAGE-RESIDUAL;
- installation into a field checkout;
- scheduler wiring (#747).

**Still open from earlier sessions:**

- #748 and #7 await a judgment on whether #769 discharges them;
- #722's owed record edits.

**Sweep caveat (#776).** This wrap-up did two things to the footer:

- before sweeping, it restored the trailing blank line so the archive helper would
  recognise the footer;
- after sweeping, it trimmed that line again so `git diff --check` passes.

Until #776 lands, the next sweep needs the same restore first.

▶ Next: `/session-start` — then draft the PHASE5-D-SYSTEMIZE-RECOVERY approval packet
from the D proposal's table (`saved_plans/phase5-d-proposal_2026-09-21.md`, local).

- **Reuse:** the BOUNDARIES harness and fake forge
  (`state/review-evidence/phase5-d-systemize-boundaries-01/harness.py`).
- **Open design point:** the post-dispatch, pre-receipt cutpoint needs an operator
  decision, because systemize's external writes are made by the agent, not an engine.

The next session drafted that packet; the 2026-09-23 D-SYSTEMIZE-RECOVERY packet block
owns it.

______________________________________________________________________

## Session — 2026-09-23 (Phase 5 D-SYSTEMIZE-LIVE run, in Claude Code)

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
  drafted. Whether these two routes still needed a live positive write was left as an
  operator decision under the Stage A rows; the next session's block records it.

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

The next session took the positive-write decision and ran D-SYSTEMIZE-BOUNDARIES; the
2026-09-23 D-SYSTEMIZE-BOUNDARIES block owns both outcomes.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
