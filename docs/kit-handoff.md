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
> **Two parts.** Session entries are a log of what happened, newest first, and carry no
> next step. Each open line of work keeps its own `▶ Next:` in its entry under
> **Workstreams** at the end of this file, until the operator closes it
> ([#762](https://github.com/topij/agentic-dev-kit/issues/762)).
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`). The Workstreams
> section is never swept.

## Session — 2026-09-26 (triage engine fixes, friction sweeps, #762 design, in Claude Code)

**Shipped, each with a fallback panel because CodeRabbit's automatic review is off:**

- [#812](https://github.com/topij/agentic-dev-kit/pull/812) merged as `cee1f6f`. Engine
  sweeps write a record block under their marker, a later sweep keeps the marker, and
  neither the EOF nor the archive heading spacing is mangled. It resolves #806, which
  was closed by hand. A delta lens caught that the first repair commit had spliced an
  existing test into a new one; `4ac95bb` restored it before merge.
- [#813](https://github.com/topij/agentic-dev-kit/pull/813) merged as `c8b9be5`. It fixes
  forward a regression #812 introduced: commit validation re-rendered retained sweeps
  with the new renderer, so the 2026-09-25 `completed` state could not be retired and
  triage refused to start. Validation now also accepts the pre-#812 rendering. Its PR
  body carries the `make test` stamp and the offline replay against that state.
- [#817](https://github.com/topij/agentic-dev-kit/pull/817) (`d027c66`) and
  [#819](https://github.com/topij/agentic-dev-kit/pull/819) (`fe93d98`) are engine-backed
  triage sweeps, both merged on the operator's direction. The run behind #817 filed
  [#814](https://github.com/topij/agentic-dev-kit/issues/814),
  [#815](https://github.com/topij/agentic-dev-kit/issues/815) and
  [#816](https://github.com/topij/agentic-dev-kit/issues/816). #819 archived three
  entries whose fixes had already shipped. The run needed two sweeps because one
  approval carries one command ([#820](https://github.com/topij/agentic-dev-kit/issues/820)).

**Filed at wrap-up, on the operator's approval of the exact payloads:** #820, and an
occurrence comment on #808 (every create in the #817 run read back `ambiguous` and was
verified on resume). [#818](https://github.com/topij/agentic-dev-kit/issues/818) was
filed earlier as the ticket disposition for the #817 panel's low-severity rendering
findings.

**#762 design decided.** Continuations move into a standing `## Workstreams` section.
Session blocks become an event log. The design, the defaults for workstream naming and
closing, and the migration are in the
[design comment](https://github.com/topij/agentic-dev-kit/issues/762#issuecomment-5845903370).
The operator scheduled #762 ahead of the next cs-toolkit upgrade, and asked for it to
run in a fresh session at higher effort.

**Not established:** where the next cs-toolkit upgrade sits in the sprint plan. Neither
`saved_plans/phase5-completion-plan_2026-09-18.md` (local, not committed) nor Phase 6 in
`saved_plans/codex-parity-plan_2026-08-23.md` names one.

______________________________________________________________________

## Session — 2026-09-26 (documentation refresh, in Codex)

**Shipped.** [#810](https://github.com/topij/agentic-dev-kit/pull/810) merged as
`09fcbe874249ea773e25acd7a591487170acd07d` on the operator's direction. The new
developer guide gives task-oriented routes; the architecture guide illustrates
components, PR flow, lane state, and friction routing with Mermaid. Entry guides and
the shared parallel workflow now agree with the supported upgrade, activation,
merge-authority, and model-tier behavior.

**Review.** CodeRabbit reported that automatic review was skipped. The PR carries
the fallback panel and composed delta review evidence; its comments own the findings
and dispositions.

______________________________________________________________________

## Session — 2026-09-25 (Phase 5 D-TRIAGE-RESIDUAL, in Claude Code)

The packets are `saved_plans/phase5-d-triage-residual_2026-09-25.md` and
`saved_plans/phase5-d-triage-retire-completed_2026-09-25.md`. They are local and not
committed, like the other D packets. The evidence is in `state/review-evidence/`
(gitignored):

- `phase5-d-triage-residual-01/`: Stage T;
- `phase5-d-triage-retire-01-stage0/`: the K1 classification;
- `phase5-d-triage-residual-01-stage-l/`: the live stage, and its `RESULTS.md` owns the
  outcomes.

**Stage T** (test mode, in a throwaway clone) worked, and showed that a completed session
ended its mode for good. **K1** (a read-only copy of the 2026-09-06 LLM-only state) found
it invalid but finished.

**Shipped, each on the operator's direction, with fallback panels:**

- #798: `new`, no argument and `test` retire a valid completed triage state.
- #799: a guard test compares `KIT_OWNED` with `git ls-files scripts`.
- #801: `recover` retires an invalid but finished run, proven from git.
- #804: a failed branch-create is retried once read-back shows it left nothing.

The operator also asked for #800 (another session's handoff) to be merged.

**Live triage.** The 2026-09-06 state was retired through #801. Session A filed TRI-05 as
#802 and swept it (#803). Session B archived the entries that already had a home (#805). Both
completed as `archive-sweep` / `degraded-success`. The markers' record blocks in
`docs/kit-friction-log.md` were restored by hand in this wrap-up.

**Filed, on the operator's approval of the exact payloads:** #806, #807, #808. An
occurrence comment went on #425.

**Not established:** notification-thread approval (the CLI has no notification provider;
#198), and D-TRIAGE-RECOVERY.

**Verification.** The bodies of #798, #799, #801 and #804 each stamp their own
`make test` run. All ran in linked worktrees under this session's scratchpad, because the main checkout's
`state/review-evidence/` holds unreadable files (#461).

______________________________________________________________________

## Session — 2026-09-25 (reviewer switching assessment, in Claude Code)

**Why.** An In Parallel adopter repository is replacing CodeRabbit with an internal PR
reviewer. The operator wants the kit to treat any reviewer as "just another review
bot" and to make switching between CodeRabbit and internal tooling a config choice.

**Decisions (operator):**

- The kit repo stays on CodeRabbit (free OSS tier).
- The kit ships **no** settings for the internal reviewer. The kit may be used by
  external repos, so the adopter defines its reviewer's profile itself. Kit code, docs
  and tests stay reviewer-neutral and use a made-up reviewer.
- How the internal reviewer behaves (trigger, label semantics, login, latency) is
  settled by watching it once it is live on the adopter. If the kit can't accommodate
  it, the fallback is asking the reviewer's developer for a change. On 2026-09-25
  the operator asked that developer to have the reviewer post a GitHub check run, which would make the kit's existing
  check-based pending path work unchanged.

**Filed on the operator's go-ahead:**

- #796: reviewer profiles, with adopter-defined profiles and a configured
  review-request method;
- #797: the merge gate can't see a reviewer whose only in-progress signal is a
  comment, and pending grace is one value for all reviewers.

The reviewer-specific notes and the checklist of things to observe once it is live are
in `saved_plans/fabro-review-tool-assessment_2026-09-25.md` (local, not committed). The
public issues leave those details out on purpose.

______________________________________________________________________

## Session — 2026-09-24 (Phase 5 D-SYSTEMIZE-RECOVERY-02 rerun, in Claude Code)

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Phase 5 exit

**Status:** the D runs' open residuals go to the E audit, which also decides whether to
commit the local `saved_plans/phase5-*` packets. #748 and #7 were both open on
2026-09-26, awaiting the operator's judgment of whether #769 discharges them; the
2026-09-23 D-SYSTEMIZE-RECOVERY packet block in
[`kit-handoff-history.md`](kit-handoff-history.md) sets out the options.
**Owner:** `saved_plans/phase5-completion-plan_2026-09-18.md` (local, not committed).

▶ Next: draft the D-TRIAGE-RECOVERY packet from
`saved_plans/phase5-d-proposal_2026-09-21.md` (local). The alternative is #794's
workflow fix: the real tracker's marker search is still residual R1 of the
D-SYSTEMIZE-RECOVERY-02 run.

### Reviewer profiles

**Status:** on 2026-09-25 the operator asked the reviewer's developer to post a GitHub
check run, which would let the merge gate's existing check-based path see it; #797 can
wait for that answer. **Owner:** [#796](https://github.com/topij/agentic-dev-kit/issues/796),
[#797](https://github.com/topij/agentic-dev-kit/issues/797); the adopter-specific notes are
in `saved_plans/fabro-review-tool-assessment_2026-09-25.md` (local, not committed).

▶ Next: implement #796 — adopter-defined reviewer profiles and a configured
review-request method.

### Triage engine hardening

**Status:** the sweep-marker defect (#806) is fixed by #812 and #813. **Owner:**
[#807](https://github.com/topij/agentic-dev-kit/issues/807),
[#808](https://github.com/topij/agentic-dev-kit/issues/808),
[#818](https://github.com/topij/agentic-dev-kit/issues/818),
[#820](https://github.com/topij/agentic-dev-kit/issues/820).

▶ Next: fix #807 — two triage sessions on one day collide on `chore/triage-{date}` —
before the next same-day engine-backed sweep.

### Handoff workstreams

**Status:** the layout this section belongs to is implemented by the pull request that
added it, from [#762's design comment](https://github.com/topij/agentic-dev-kit/issues/762#issuecomment-5845903370).
Its behaviour for wrap-ups in either order, a resumed older workstream, and an unrelated
chosen task is prose an agent executes, so it is exercised by use rather than by the
suite. **Owner:** [#762](https://github.com/topij/agentic-dev-kit/issues/762).

▶ Next: check the first wrap-ups under this layout, in both runtimes, against #762's
acceptance criteria, then ask the operator whether to close this workstream. The next
cs-toolkit upgrade carries this contract; where that upgrade sits in the sprint plan is
not established.
