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

Last updated: 2026-09-24 — RECOVERY's agent-cutpoint rerun ran as
PHASE5-D-SYSTEMIZE-RECOVERY-02. Phase 5 delivery item 5 remains incomplete; item 6's
replay remains complete.

## Latest session — 2026-09-24 (Phase 5 D-SYSTEMIZE-RECOVERY-02 rerun, in Claude Code)

**Approved and run.** The operator approved PHASE5-D-SYSTEMIZE-RECOVERY-02 with options
A1, B1, C1, R1 and E1. The packet is
`saved_plans/phase5-d-systemize-recovery-rerun_2026-09-24.md` (local, not committed, like
the other D packets). `APPROVAL.md`, `RESULTS.md`, the harness and
`EVIDENCE-SHA256SUMS` are in
`state/review-evidence/phase5-d-systemize-recovery-02/` (gitignored). `RESULTS.md` owns
the outcomes.

- **Design:**
  - headless `claude -p --model fable` runs, isolated by Claude Code's sandbox;
  - `denyRead` covered the harness, the control repository, `~/.claude` and the
    `/private/tmp` entries that existed at setup;
  - a socket-served fake forge and tracker, whose kills the server performs;
  - the clones were at `c1d513e` plus one commit resetting the living docs.
- **Outcome:** in both chains a fresh restart after a kill made **no second create**.
  The landed-before-receipt chain recorded `found-by-read-back`. The
  killed-before-landing chain made one create and recorded `created-and-read-back`.
- **Operator amendments during the run**, recorded in `APPROVAL.md`:
  - **§2:** a second fake-form gap, in `Q`'s preflight, did not stop the chain.
  - **§3:** the harness's process-group kill missed the Bash tool's own process groups,
    so the kill became a whole-tree kill and the `Q` chain was redone.
    `launch_lane.py` already covers this case with its lineage kill.
- **Scope of the result:** one synthetic sample per cutpoint. Whether it discharges the
  residuals is the E audit's call. The real tracker's marker search is still a residual
  (R1).

**Filed and closed, each on the operator's approval of the exact payload:**

- #794: the marker search defines neither the query nor the match set;
- #722 closed as done: every owed record edit was already in the tree.

**Parked in the friction log:** a restart that resumed the heartbeat without `start`; a
synthetic approval recorded under the operator's real name; and a confounded related
occurrence on the FRESH-CONTEXT preflight entry.

**Still open from earlier sessions:** the #748 and #7 judgments.

▶ Next: `/session-start`, then draft the D-TRIAGE-RESIDUAL packet from
`saved_plans/phase5-d-proposal_2026-09-21.md` (local). The alternative is #794's
workflow fix.

______________________________________________________________________

## Session — 2026-09-24 (systemize dispatch idempotency, #790, in Claude Code)

**Shipped.** [#790](https://github.com/topij/agentic-dev-kit/pull/790) merged as
`4c69ab2c7eb6c33f537d553e5c168566b297edee` on the operator's direction, and #786 was
closed on the operator's direction.

- `post-merge-systemize.md` gains *External dispatch records*: an idempotency marker and
  a report record for each tracker create and notification, `attempting` persisted
  before the write, and a marker search before any create.
- A new safety row, `unverified-external-dispatch`, makes the read-back normative.
- `CHANGELOG.md` carries the adopter entry.

**Review.** CodeRabbit skipped, because automatic reviews are disabled. The fallback panel
ran at `2b9dae8`, `ae54d68` and `d873b68`. The receipt is bound to `d873b68`, and the
PR's disposition comments own the findings.

**Filed on the operator's approval of the exact payloads:**

- #791: the dispatch protocol is tested only as pinned prose, so an added contradicting
  instruction passes;
- #792: two concurrent LLM-only runs can both pass the marker search and create.

**Verification.** `make test` at `d873b68dfc96e87b2787e886207dcc9feb48d3df` on
2026-09-24, in a detached worktree under this session's scratchpad, printed
`3500 passed, 1 skipped`. It did not run in the main checkout, because a mode-000 file
under the gitignored `state/review-evidence/` crashes the suite's state snapshot. That
is #461's mechanism, now live.

**Still open from earlier sessions:** the #748 and #7 judgments, and #722's owed record
edits.

▶ Next: `/session-start`, then draft the RECOVERY post-dispatch rerun packet against the
workflow at `4c69ab2`, from `saved_plans/phase5-d-systemize-recovery_2026-09-23.md`
(local). The alternative is the D-TRIAGE-RESIDUAL packet, from
`saved_plans/phase5-d-proposal_2026-09-21.md` (local).

The next session took the rerun, and closed #722 as done. The 2026-09-24 block on
D-SYSTEMIZE-RECOVERY-02 owns both.

______________________________________________________________________

## Session — 2026-09-24 (RECOVERY decision and Phase 5 D-FRESH-CONTEXT run, in Claude Code)

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

The next session took #786's fix; the 2026-09-24 block on systemize dispatch
idempotency owns it.

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
