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

## Session — 2026-10-10 (record-prose preflight and executed-span review, in Codex)

- **Review proportionality:** [#1039](https://github.com/topij/agentic-dev-kit/pull/1039)
  merged as `fa905cd09c950b96fe926ceb21d69ff7c00dea7c` on the operator's request.
  It shipped #585's Git-snapshot record-prose preflight and shared executed-span
  guidance. #403's shortening-versus-logging precedence question was outside the change.
- **Decision:** the operator chose to file the accepted **P2 — Regression** about
  the `uv run` no-network assurance and merge the reviewed candidate. Filed and
  read back as [#1041](https://github.com/topij/agentic-dev-kit/issues/1041), with
  `cloud` execution requirements. The [review disposition](https://github.com/topij/agentic-dev-kit/pull/1039#issuecomment-6101160726)
  preserves the independent review and the unresolved deferral.
- **Verification:** `make test` at `c02e4c67ffc2229e779009518b8c116d2a31abd8`
  on 2026-10-10, in `/Users/topi/Coding/agentic-dev-kit`, passed.
  The preflight itself does not establish command execution or numerical truth.
- **Not established:** an offline dependency-bootstrap remedy or an adopter rollout.
  The operator confirmed the workstream assignment.

______________________________________________________________________

## Session — 2026-10-10 (ticket execution environments, in Codex)

- **Ticket execution environments:** [#1038](https://github.com/topij/agentic-dev-kit/pull/1038)
  merged as `4271cbd7e6b8177554105205ee8f467e8b33e6ed` on the operator's request.
  The shared ticket contract and workflow bindings carry execution requirements
  into ticket drafting, session briefings and parallel planning.
- **Decision:** the operator chose to file the remaining MEDIUM non-regression
  coverage gaps and merge. [#1040](https://github.com/topij/agentic-dev-kit/issues/1040)
  carries the approved follow-up and its `unknown` execution classification.
  The [review disposition](https://github.com/topij/agentic-dev-kit/pull/1038#issuecomment-6100291789)
  preserves the independent panel and the deferral.
- **Verification:** `make test` at `30ad19f9df9af5e3d5df81ebb5039a21768118ca`
  on 2026-10-10, in
  `/private/tmp/claude-502/-Users-topi-Coding-agentic-dev-kit/codex-ticket-environment-4k5vbe5u/verify-30ad19f`,
  passed. The portability checks inspect declarations and reviewed Markdown;
  they do not execute an agent choosing work or creating tickets.
- **Not established:** live cloud selection and the intended cloud setup's
  verification capabilities. The operator confirmed the workstream name below.

______________________________________________________________________

## Session — 2026-10-09 (scratch alternate paths, in Codex)

- **Scratch retention:** [#1034](https://github.com/topij/agentic-dev-kit/pull/1034)
  merged as `79d33fb9eaca1d4da6dca0b1ca703fc384ffc657` on the operator's request,
  addressing #1032. Unquoted alternate paths preserve whitespace and filesystem bytes.
- **Verification:** `make test` at `fbc91bdcfa01b6fda7bb30f04dddfe8a403233f1` on 2026-10-09,
  in `/private/tmp/claude-502/-Users-topi-Coding-agentic-dev-kit/codex-01a121d7-1032-4xh1wqvu/verify-fbc91bdc`,
  printed `4538 passed, 1 skipped`. `gh run view 37976770841` from
  `/Users/topi/Coding/agentic-dev-kit` on 2026-10-09 reported `Test` at
  `79d33fb9eaca1d4da6dca0b1ca703fc384ffc657` completed with `success`.
- **Review:** CodeRabbit skipped. The [independent adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/1034#issuecomment-6087015179)
  records focused tests and deliberate trimming, line-splitting and replacement-decoding mutations.
- **Limits:** No production scratch sweep or adopter rollout ran in this session.

______________________________________________________________________

## Session — 2026-10-09 (workstreams named by subject, in Claude Code)

- **#1028 merged as `50145a23`, by the operator.** `wrap-up.md` now names a workstream for its subject, never a date, a run mode or a session. A session with unrelated pull requests files each one under its subject's workstream. An unattended guess is marked `assignment unconfirmed`, and an interactive wrap-up offers the operator folds for misnamed and unconfirmed entries. `session-start.md`, `parallel.md` and the handoff template follow suit. `make test` at `45819297` on 2026-10-09 in `/Users/topi/Coding/agentic-dev-kit` → `4497 passed, 1 skipped`.
- **Review.** CodeRabbit skipped the PR. The adversarial lens ran full passes at `dae754b8` and `2fe2ce11`. A delta pass at `4cce8edb` disputed containment and spent the round budget. The operator authorized one further round (option A of the decision packet on the PR). The delta pass at `45819297` found every repair contained, and its `fallback:delta` receipt is composed on `2fe2ce11`. The remaining LOW findings were filed, on the operator's approval of the exact text, as #1030, read back identical.
- **cs-toolkit.** On the operator's approval of each fold, in-parallel-oy/cs-toolkit#2609 merged as `3d7a6b95`. It re-filed that repository's batch-named workstreams by subject. Two LOW wording findings from its delta pass were left, on the operator's choice, for cs-toolkit's next wrap-up. They are recorded only in #2609's disposition comment.
- An occurrence was added to #852 on the operator's approval, and reads back identical: the round-1 receipt was not recorded before the repair was pushed.
- Not established: whether an unattended batch wrap-up files its pull requests by subject under the new rules. None has run under them yet.

______________________________________________________________________

## Session — 2026-10-09 (tickets closed after the lane batch, in Claude Code)

- On the operator's word, closed each ticket with a comment naming its merge commit: #1008, #1009, #1012, #1013, #1014, #1016, #1018. This supersedes, for those tickets, the previous entry's "still open" and "waits for the operator" lines. It also supersedes that entry's "not ticketed": #1017 now carries the gap.
- #1017 stays open with a comment. #1023 covered the `forge-finalize` and `archive-sweep` phases; a finished `tracker-write` session's resume hint is the open design decision.

______________________________________________________________________

## Session — 2026-10-09 (changelog fragments and the lane batch merged, in Claude Code)

- **#1020 merged as `f9146c5f`.** The operator authorized a fourth fix round. It made `upgrade.md`'s fragment lookup read fragments written only by a merge commit (`diff-tree -c`) and type-changed fragments (`--diff-filter=AMT`), and set the fragment naming rule. Its review at `36a69208` found no fail-open in the lookup but left test gaps. The operator chose to merge and ticket them: filed and read back as #1026. `make test` at `36a69208` on 2026-10-09 in `/Users/topi/Coding/agentic-dev-kit` → `4477 passed, 1 skipped`.
- **On the operator's word, #1023 merged as `a95e9983` through `dev_session.sh merge`, and #1022 merged as `54655d9d` pinned to its reviewed head `6d5343ac`.** #1023's `tracker-write` resume-hint gap shipped as is, and is not ticketed.
- `reconcile_sessions.sh pr-watch-trio triage-trio skip-shape-doctrine` reported every lane merged. The three lane sessions and branches were removed with `dev_session.sh rm --force`, which discarded only each lane's uncommitted `.pr-body.md`.
- The tickets the merged PRs addressed are still open: #1008, #1009, #1012, #1013, #1014, #1016, #1017, #1018. Closing them waits for the operator.

______________________________________________________________________

## Session — 2026-10-08 (changelog fragments, then a three-lane batch run overnight, in Claude Code)

- **#1009 designed and built as PR #1020, held for the operator.** On the operator's choice, once #1020 merges each PR would add `changelog.d/<branch-slug>.md`, with `CHANGELOG.md` frozen behind a BREAKING cutover entry and `upgrade.md` Step 1 printing each fragment version a commit in range wrote. Until then `main`'s rule is unchanged. A `git merge-tree` replay of #1004–#1006 showed only `CHANGELOG.md` conflicting; `kit-manifest.json` auto-merged, so it is unchanged. The adversarial lens reviewed `c254fd90`, `751bedee` and `44ada17e`, which spent the round budget, and the last review left a Low-Medium finding (a fragment written only by a merge commit prints nothing). The decision packet is on #1020. `make test` at `44ada17e` in the main checkout on 2026-10-08 → `4476 passed, 1 skipped`.
- **Lanes launched headless from `main` at `fad8597b`.** The operator first chose interactive lanes, then asked for autonomous work overnight, so each lane ran through `launch_lane.py`. Each prompt carried its ticket text, because the lane profile has no `gh issue view`.
  - `skip-shape-doctrine` (#1012) → #1021, merged as `43cb89ef` through `dev_session.sh merge`. It had a full lens pass at `ac635d8d` and two LOW delta repairs.
  - `pr-watch-trio` (#1008, #1013, #1014) → #1022, held for the operator: it is safety-critical. Its panel receipt is at `6d5343ac`, and the disposition lists the open LOWs.
  - `triage-trio` (#1016, #1017, #1018) → #1023, consciously parked by the cockpit, unmerged. It has a lens receipt at `6713c8a4`. Its #1017 fix leaves a Low-Medium gap for the `tracker-write` phase, and the right hint there is a design decision.
- **#1022 and #1023 both ship `changelog.d/` fragments, so merge #1020 first.** Before #1020, nothing reads them.
- `reconcile_sessions.sh pr-watch-trio triage-trio skip-shape-doctrine` reported `merged` for #1021, `held` for #1022 and `open` for #1023, which is parked as above. All three lane worktrees are kept, #1021's included, until the batch's open PRs settle.
- Workstream assignment was not confirmed with the operator: this session added a new **Changelog fragments** entry and left every existing entry alone. #1008 is named in *Review proportionality*, and #1022 now carries it.

______________________________________________________________________

## Session — 2026-10-08 (friction-log triage after the overnight batch, in Claude Code)

- **Triage session `469bcd58` superseded.** Its `resume` returned operator-held with "configuration identity mismatch": `config/dev-model.yaml` changed after it froze, in #993, #986 and #1006. On the operator's decision its isolated state root was left untouched as evidence, and a fresh live draft was started instead.
- **Triage run `7f662678` completed** (engine-backed, `degraded-success` because it used the session in place of a notification). The operator approved filing TRI-01, 02, 05, 08, 11 and 20, and archiving the rest.
  - Filed and read back: #1009, #1010, #1011, #1012, #1013, #1014.
  - The archive sweep #1015 merged as `770092ab` at its reviewed head, `3207eb04`. Its review was the correctness lens (CodeRabbit skipped). The engine read back the merge and removed the sweep's worktree and branch.
- **This wrap-up** moved the 2026-10-03 intro paragraph the sweep left behind into the archive. The lens on #1015 had found it.
- Filed at wrap-up, on the operator's approval of each payload: #1016, #1017, #1018.
- **Scratch:** the operator removed the probe directory that pinned session `2d56cdd2`'s scratchpad. The removal reset that entry's modified time, so `uv run scripts/sweep_scratch.py --apply --older-than 1d` cannot reclaim it before about 2026-10-09 14:50 UTC.

Closed workstream Kit friction-log triage: its step, deciding `469bcd58`, was superseded by run `7f662678`, which completed through #1015.

______________________________________________________________________

## Session — 2026-10-08 (overnight batch of headless lanes, in Claude Code)

The operator asked for an overnight autonomous session with parallel lanes and authorized merging every PR
"when clean", operator-class lanes included. It also approved filing #1002 and removing the merged
`dev/scratch-sweep` lane. Headless Claude lanes ran under `launch_lane.py`, one per PR below. The cockpit ran every
review and fix round, merged `main` into each later lane to clear `CHANGELOG.md` conflicts, and stamped
`make test` at each merging head. `reconcile_sessions.sh` at wrap-up reconciled each lane as merged or held, as listed.

- **#1003** (#999) merged as `695d35d0`, through `dev_session.sh merge` (self class).
  - `panel_prompt.py --scratch` now refuses unless the tree is detached at `--head`.
  - Review: one adversarial lens, then a delta pass.
  - `make test` at `0319a8ff` on 2026-10-08, in its lane worktree, printed `4434 passed, 1 skipped`.
- **#1004** (#1001, #1002) merged as `18bacdc2`.
  - A recovery refusal names the check that failed.
  - `test` judges a completed state as `recover` does.
  - The panel showed no engine-written state reaches the `test` entry's forge-prefix refusal, so the claim was narrowed rather than tested.
  - `make test` at `87d06984` on 2026-10-08, in its lane worktree, printed `4438 passed, 1 skipped`.
- **#1005** (#1000) merged as `f508d220`.
  - The scratch sweep judges root and entry containment by filesystem identity as well as by string.
  - The engine classes it standard; the cockpit ran both lenses because it deletes files.
  - `make test` at `b4645e26` on 2026-10-08, in its lane worktree, printed `4456 passed, 1 skipped`.
- **#1006** (#991, #994) is **held for the operator** at `fd2dd68974a8cd0bf317c1e90985aa790bd80473`.
  - Safety-critical paths match case-folded; `--record-round --head` takes only a hex sha.
  - Every reviewed head has a two-lens receipt, and no round found anything above LOW.
  - The round budget is spent with two LOWs open. Filing their ticket needs the operator, so the cockpit did not merge.
  - The decision packet on the PR has both options.
  - *(Correction: one more fix round followed, at `044f5ec6`. #1006 merged at that head as `f917d946`, and the one LOW that round left was filed as #1008.)*
  - `make test` at `fd2dd689` on 2026-10-08, in its lane worktree, printed `4467 passed, 1 skipped`.

Decided (cockpit): the operator's "merge when clean" was read as not covering a merge-gate PR with a LOW
still open past a spent round budget.

Not established: whether `sweep_scratch.py`'s per-component `stat` cost matters on a large root. A lens
measured a large slowdown on a synthetic layout; nothing measured it on a real one.

Filed this session: #1002. Lenses' mutation copies remain under this session's scratchpad, inside
`scratch.roots`.

______________________________________________________________________

## Session — 2026-10-07 (scratch sweep engine merged, in Claude Code)

[#986](https://github.com/topij/agentic-dev-kit/pull/986) merged as
`dff111ae86ff0101358183c07ca8874d17bff46e`, on the operator's authorization, after
fallback-panel rounds 6–9 in this session. `scripts/sweep_scratch.py` reports and,
with `--apply --older-than`, removes stale direct children of `scratch.roots`. Each
round's findings and dispositions are in its disposition comment on the PR.

Decided (operator, 2026-10-07):
- The global `rm -rf *` deny stays, so this engine is the only scratch-cleanup route.
- Round-5 finding 1 is fixed within a bound rather than documented. An entry holding a bare
  or separated git dir is kept, and so is one that holds a configured repository's git dir or
  object store, including stores reached through `alternates`.
- Round 6 also took the lens scratch-placement rule: *Scratch namespace* in
  `fallback-review-panel.md` puts a lens's copies beside its handed tree, never
  directly under the system temp dir.
- Bare fixture repos in pytest basetemps pin their whole session entry. That is
  documented and ticketed (#997) rather than loosened.
- Round 8's `.git`-gone skip was reverted in round 9, because it dropped a bare
  configured repo's object store (fail-open). That shape exits 2 again.

Not established: how much space the sweep reclaims on this machine. A report-mode run
during round 7 kept the largest session entries for the bare-fixture rule. `--apply`
was never run against a real directory.

Verification: `make test` at `258fee841388fb16c215dd37d0b5f79dfcc3f3c4` on 2026-10-07,
in `/Users/topi/Coding/dev-model-sessions/scratch-sweep/wt`, printed `4426 passed, 1
skipped`. CI's `Test` run on `main` passed at `dff111ae`.

The lane worktree `/Users/topi/Coding/dev-model-sessions/scratch-sweep/wt`
(`dev/scratch-sweep`) was left in place at this wrap-up.

Filed this session: #996, #997.

______________________________________________________________________

## Session — 2026-10-07 (review round budget, in Claude Code)

[#993](https://github.com/topij/agentic-dev-kit/pull/993) merged as
`2d40c96024f642fa60b656b03d53d34a93349fdc`. A pull request's review now gets the
opening review plus `review.round_budget` fix rounds. Past that, the watch loop posts
a decision packet and stops for the operator instead of pushing another fix round.
`pr_watch.py` counts distinct reviewed heads from configured bots' submitted reviews,
`--record-review`, and the new `--record-round`, and reports them as `review_rounds`.
It gates nothing. `pr-watch.md` carries the *Round budget* stop condition beside the
generic loop bound, and the panel doctrine, safety-critical rule 3 and the
follow-through hook say the same. The CHANGELOG entry tells adopters what to refresh.

Decided: the operator set the default at the opening review plus 2 fix rounds. The
motive is cost in adopting repositories: review tokens, and GitHub Actions minutes,
which this public repository does not pay. The budget is report-only rather than a
gate, so that a count the author partly self-reports cannot open or close a merge.
Not built: routing a non-regression MEDIUM in a fix round like a LOW, which needs its
own operator decision.

Not established: whether the budget shortens review in practice; nothing has measured
it yet. The count also misses rounds that go unrecorded, and `pr-watch.md` names those
cases.

Verification: `make test` at `59eeee935113e4f6fa015b6e97ff5cd1abc91107` on 2026-10-07,
in `/Users/topi/Coding/agentic-dev-kit-round-budget`, printed `4332 passed, 1 skipped`.
CI's `toolkit` run passed at that head.

Review: two-lens panel rounds at `6db144ca`, `753e6099` and `59eeee93`. Each round's
disposition comment on the PR holds its findings. The round at `59eeee93` found
nothing above LOW, and the PR's own budget was spent there, so its LOW findings went
to a ticket rather than a further round.

Filed this session: #994.

______________________________________________________________________

## Session — 2026-10-07 (overnight autonomous parallel lanes, in Claude Code)

The operator asked for an overnight autonomous session in separate worktrees, and authorized merging every PR "when clean". Three headless lanes ran under `launch_lane.py`, and the cockpit ran each PR's review and fix rounds.

- **#984** (for #884 and #944) merged as `4e27661e075dba8d2569bc086c9effdf9c757b2b`.
  - The suite now neutralises colour at `scripts/conftest.py` import.
  - The `--carry-forward` help names the live draw flags.
  - `FORCE_COLOR=3 make test` at `4b0e7d4e063e19a9384635596faba0c2eee2c36f` on 2026-10-06, in the lane worktree, printed `4293 passed, 1 skipped`. The one later commit changed a comment and its manifest hash, with CI's run only.
- **#985** (for #859) merged as `6ccc1744291f887ffbee8c9fe31c16d731617831`.
  - `recover` retires a completed state that fails only the frozen-artifact or forge-prefix checks, when git proves its sweep.
  - It refuses one with no proven retirement and writes nothing.
  - In-flight states keep the old judgement.
  - The panel rejected the earlier designs as HIGH regressions into a terminal hold; the PR's comments hold every round.
  - `make test` at `d9e951a3a421c8b959675d9e3daa0d0b4608a06a` on 2026-10-07, in the lane worktree, printed `4297 passed, 1 skipped`. Later commits are tests, docstrings, the CHANGELOG entry, the triage workflow doc and the manifest, reviewed by delta passes.
- **#986** (#900's scratch sweep engine) is **open and held for the operator** at `d9a1fd571daf8181b434e362de48d055abce4dd6`. *(Correction: it merged later the same day as `dff111ae`; see the session entry above.)*
  - Every full two-lens pass found new fail-open edge cases in what the engine judges removable, so the cockpit stopped the loop rather than merge a file-deleting engine.
  - The round-5 disposition comment on the PR lists the open findings.
  - `make test` at that head on 2026-10-07, in `/Users/topi/Coding/dev-model-sessions/scratch-sweep/wt`, printed `4367 passed, 1 skipped`.
  - `--apply` was never run against a real directory.

Decided: #986 was held, not merged. The operator's "merge when clean" did not cover a destructive engine with open low-to-medium fail-open findings.

Not established: the `test` entry's own recovery branch still judges by `canonical_state` alone, which is the #859 class in test mode. It is parked in the friction log, untracked. *(Correction: it was filed as #1002 the same day and fixed by #1004; see the 2026-10-08 entry above.)*

Lanes ran with no operator present, so no tracker write was made. This session's friction is parked in the friction log. *(Correction: the 2026-10-08 triage filed or archived these entries; see that entry above.)*

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Review proportionality

**Status:** #927 (`8ea91add`) shipped the computed review class; #934 (`41beacb8`)
added named delta draws; #993 (`2d40c960`) shipped the review round budget.
#1039 (`fa905cd09c950b96fe926ceb21d69ff7c00dea7c`) shipped #585's record-prose
preflight and executed-span guidance on 2026-10-10. The operator deferred the
accepted P2 regression to #1041; #403's precedence question was outside the change.
#921 owns the cockpit check of verdict-line names.
**Owner:** [#585](https://github.com/topij/agentic-dev-kit/issues/585),
[#1041](https://github.com/topij/agentic-dev-kit/issues/1041); related #921, #403,
#666, #305, and the class's documented limits #928, #929, #930 and #931.

▶ Next: Implement #1041 — qualify the dependency-bootstrap assurance in
`docs/agentic-dev-kit/fallback-review-panel.md` and verify cold-cache failure as
unavailable coverage, using the ticket's declared prerequisites.

### Scratch retention

**Status:** `scripts/sweep_scratch.py` and the `scratch:` config block shipped in
#986 (`dff111ae`). Its documented limits are in the engine docstring. #1005 (`f508d220`)
judges root and entry containment by filesystem identity as well as by path string (#1000).
#1034 (`79d33fb9`) preserves unquoted alternate path whitespace and filesystem bytes (#1032). #997 owns
reclaiming session entries that bare fixture repos pin. #996 holds the unpinned
guards, wording, and the `.git`-gone exit 2. #900 stays open for the round-end
cockpit sweep, the wrap-up and session-start integrations, and listing the engine
in `review.safety_critical_paths`. `state/review-evidence/` waits on #861.
**Owner:** [#900](https://github.com/topij/agentic-dev-kit/issues/900),
[#997](https://github.com/topij/agentic-dev-kit/issues/997),
[#996](https://github.com/topij/agentic-dev-kit/issues/996),
[#861](https://github.com/topij/agentic-dev-kit/issues/861),
[#895](https://github.com/topij/agentic-dev-kit/issues/895).

▶ Next: #997 — choose how a session entry whose only git dirs are test fixtures
becomes sweepable without reopening the outside-dependent fail-open (an operator
design decision), then build it.

### Reviewer profiles

**Status:** on 2026-09-25 the operator asked the reviewer's developer to post a GitHub
check run, which would let the merge gate's existing check-based path see it; #797 can
wait for that answer. **Owner:** [#796](https://github.com/topij/agentic-dev-kit/issues/796),
[#797](https://github.com/topij/agentic-dev-kit/issues/797); the adopter-specific notes are
in `saved_plans/fabro-review-tool-assessment_2026-09-25.md` (local, not committed).

▶ Next: implement #796 — adopter-defined reviewer profiles and a configured
review-request method.

### Triage engine hardening

**Status:** finalize's commit-step worktree re-check is pinned by a test (#857), and the
*Completed-state retirement* doctrine names each live-mode kill cutpoint (#874), both in
#882. #883 carries its residual points. The engine's worktree guards decide containment by
filesystem identity (#856, in #889). PR #907 applied the shared predicate to
`GitHubForge`’s sweep-cleanup guard (#891), merged on 2026-10-02 as `cb92fd5`. #985
(`6ccc1744`) made `recover` judge a completed state with the session-starting checks
(#859). #1004 (`18bacdc2`) names the failed check in a recovery refusal (#1001) and judges a
completed `test` state as `recover` does (#1002).
The doctrine prescribes the operator’s manual way out of the two-link state (#894),
and an engine-owned rollback waits for a recurrence (#892).
**Owner:**
[#883](https://github.com/topij/agentic-dev-kit/issues/883),
[#892](https://github.com/topij/agentic-dev-kit/issues/892).

▶ Next: #883 — the *Completed-state retirement* doctrine's residual precision points.

### Triage one-run cleanup

**Status:** #978 and its cs-toolkit installation removed the one-run recovery paths. A
shape check in `model.py` stays until cs-toolkit's completed LIVE state, which carries a
`proposal_correction` receipt, retires. **Owner:**
[#979](https://github.com/topij/agentic-dev-kit/issues/979).

▶ Next: once cs-toolkit's scheduled triage draft has retired its completed LIVE state,
confirm no state root holds a `proposal_correction`, then remove the shim (#979).

### Changelog fragments

**Status:** changelog entries are `changelog.d/` fragments since #1020 (`f9146c5f`), and #1022 and #1023 shipped the first two. #1026 holds the lookup's test gaps and naming wording; #1022's fragment `dev-pr-watch-trio.md` already departs from that rule, which gives `pr-watch-trio.md`. #507's heading check has no new entries to check.
**Owner:** [#1026](https://github.com/topij/agentic-dev-kit/issues/1026); the closed [#1009](https://github.com/topij/agentic-dev-kit/issues/1009) states the problem, and #1020 (`f9146c5f`) holds the design.

▶ Next: #1026 — pin the lookup's baseline range and pathspec with tests, and state one fragment naming rule.

### Handoff workstream naming

**Status:** #1028 (`50145a23`) names workstreams by subject and files a batch per pull request; cs-toolkit's batch-named entries were folded by in-parallel-oy/cs-toolkit#2609. #1030 holds the residual single-workstream wording, the half-pinned clauses, the run-mode carve-out, and a kept entry that cannot be named.
**Owner:** [#1030](https://github.com/topij/agentic-dev-kit/issues/1030).

▶ Next: #1030 — cover every workstream a session worked on in the "Update only that workstream's entry" bullet, pin the half-pinned clauses, give creating and detecting entries one run-mode carve-out, and define what happens to a kept entry that cannot be named and to references after a rename.

### Ticket execution environments

**Status:** the shared contract and workflow bindings shipped in #1038
(`4271cbd7e6b8177554105205ee8f467e8b33e6ed`). The operator deferred the
instruction-check coverage gaps to #1040; live cloud selection was not exercised.
**Owner:** [#1040](https://github.com/topij/agentic-dev-kit/issues/1040).

▶ Next: session-start cloud — assess #1040's inputs and verification prerequisites,
then work on its instruction-check coverage gaps only if eligible.
