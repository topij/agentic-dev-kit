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

## Session — 2026-09-27 (triage resume completion and create read-back lag, in Claude Code)

**Shipped.** [#828](https://github.com/topij/agentic-dev-kit/pull/828) merged as `76ef6be`: a resumed triage run completes a
merge read-back it had already verified (#826), and sweep cleanup believes only a
`verified` provider answer and builds its fallback from `SWEEP_CLEANUP_ARTIFACTS` (#827).
[#829](https://github.com/topij/agentic-dev-kit/pull/829) merged as `563e694`: after a successful GitHub tracker create, the
adapter waits, bounded, for the issue list to show the created issue before judging the
marker matches (#808). Both merged on the operator's "merge when clean". #828 also
carried the record fixes naming #826, #827 and the #256 comment.

**Review.** CodeRabbit skipped both PRs; the fallback panel reviewed each, and the
disposition comments on the PRs own the findings. On #829 the first approach, reading the
created issue directly when the list was empty, dropped the list's duplicate check under
lag, and was replaced by the wait.

**Verification.** `make test` on 2026-09-27, each in its PR's worktree under
`.claude/worktrees/`: at `f783e18a8be6fd689718f726a25910798b1d5633` it printed
`3624 passed, 1 skipped`, and at `a447d2041fc0bfb4e8abaebe56c78c80df528cda`
`3634 passed, 1 skipped`. In the main checkout it stops at conftest import on #461's
unreadable `state/` file.

**Left open:** #829 keeps the retry schedule as a class constant in `GitHubIssues` rather
than a `config/dev-model.yaml` key; its PR body raises the question.

**Not established:** the #826 resume against a real crash, and #829's wait against the
live GitHub API, including whether its bounded wait covers GitHub's actual lag. Both rest
on tests with scripted providers.

______________________________________________________________________

## Session — 2026-09-26 (triage sweep branches, #807, in Claude Code)

**Shipped.** [#824](https://github.com/topij/agentic-dev-kit/pull/824) merged as `2c2844e`
on the operator's direction in this session ("Merge when clean"); #807 closed with it. The
default `vcs.triage_branch_pattern` is now `chore/triage-{date}-{session}`, and after a
verified merge read-back the engine retires its own worktree, local branch and remote
branch, recording each result in `completion.sweep_cleanup`. The CHANGELOG entry says
what an adopter must do.

**Review.** CodeRabbit skipped. The fallback panel ran full rounds at `782532a`,
`ee209ed`, `5c9ec35` and `fbce09c`; the PR's disposition comments own the findings. The
second and third rounds each found a way for a custom provider's cleanup record to pass
the write and fail every later read. The fix that ended it was structural: the engine
now runs the completion validator itself (`validate_sweep_cleanup`) instead of keeping
its own copy of the rules.

**Verification.** `make test` at `fbce09c46c100c721deec254cb81762d5b3450b6` on
2026-09-26, in the PR's worktree under `.claude/worktrees/`, printed
`3619 passed, 1 skipped`. The same command's results at the earlier heads are on the PR.

**Not established:** a real same-day pair of triage runs, and retirement against the
real forge; both are covered only by tests with real git in temporary directories. The
stale `chore/triage-*` branches from before this change were not deleted.

______________________________________________________________________

## Session — 2026-09-26 (handoff workstreams, in Claude Code)

**Shipped.** [#822](https://github.com/topij/agentic-dev-kit/pull/822) merged as `76b883c`
on the operator's direction. Each open line of work now keeps its `▶ Next:` in the
standing `## Workstreams` section, and session entries record what happened. `wrap-up`
updates only its own workstream's entry and leaves closing to the operator;
`session-start` offers every workstream's next step and follows the operator's choice.
This file was migrated by hand in the same PR.

**Beyond the design comment**, each set out in #822's body: `Last updated:` is removed,
not only demoted; session headings no longer say `Latest`; the top of the session log is
a shared conflict point, with its resolution stated; the first-run migration lists older
`▶ Next:` lines nothing took up; and the archive sweep's footer is reworded, with the
old one still recognised.

**Review.** CodeRabbit skipped. The fallback panel ran at `3d2cc9e` and a correctness
delta at `113a97b`, for a Minor `CHANGELOG.md` imprecision; the PR's disposition comments
own the findings.

**Verification.** `make test` at `3d2cc9e2f369c326c7b1b85280d457e1b0873a33` on 2026-09-26,
in a detached worktree under this session's scratchpad, printed `3586 passed, 1 skipped`.
It did not run in the main checkout, because of #461. CI's `Test` run at `113a97b`
passed, and a PR comment carries its figures.

**Not established by the suite:** a Codex wrap-up under the contract, two workstreams
wrapping up in either order, a resumed older workstream, and an unrelated chosen task.
This wrap-up is the layout's first live use, in Claude Code.

Closed workstream Handoff workstreams: the layout shipped and this wrap-up used it; the
scenarios above are left to ordinary use, on the operator's decision.

______________________________________________________________________

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

**Status:** same-day sweep branches and post-merge retirement shipped in #824; its
follow-ups #826 and #827 shipped in #828, and the GitHub tracker's lagging post-create
read-back (#808) in #829. **Owner:**
[#818](https://github.com/topij/agentic-dev-kit/issues/818),
[#820](https://github.com/topij/agentic-dev-kit/issues/820).

▶ Next: before the next sweep, delete the pre-#824 `chore/triage-*` branches by hand;
the new engine retires only its own. Then fix #818 or #820.
