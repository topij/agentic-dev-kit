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

## Session — 2026-10-09 (tickets closed after the lane batch, in Claude Code)

- On the operator's word, closed each ticket with a comment naming its merge commit: #1008, #1009, #1012, #1013, #1014, #1016, #1018. This supersedes the previous entry's "still open" line.
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

## Session — 2026-10-06 (merge gate ignores a bot's empty thread-reply review, in Claude Code)

[#982](https://github.com/topij/agentic-dev-kit/pull/982) merged as
`54a65a4893b90d03ba15f3acdfdb52eb7ce5104e`, which closed #981. `pr_watch.py`'s
coverage reduction now skips a configured bot's `COMMENTED` review with an empty
body. GitHub creates that object for a bot's reply on an inline thread, and the
merge gate had been accepting it as the bot's review of the head. The skip also
keeps the wrapper from displacing the bot's earlier real review. `APPROVED` and the
objection read are unchanged. The CHANGELOG entry tells adopters what to refresh.

Decided: #981's suggested "or an inline comment at that `commit_id`" branch was not
built. A thread reply is itself an inline comment, so the signal does not separate
the cases. The cost is a fail-closed bound, written beside the skip: a bot that posts
inline-only findings under an empty review body needs a receipt for that head.

Verification: `make test` at `7f62cf6192f2d45bd3c7ad52c89fd9852427504d` on 2026-10-06,
in `/Users/topi/Coding/agentic-dev-kit`, printed `4290 passed, 1 skipped`. The three
later commits changed comments and docstrings only, so they got no full-suite run;
CI's `Test` run passed on the PR's final head `35141002d5212d328e0c0b2435d86e33ac57ff68`.

Review: the two-lens panel at `7f62cf6`, then three LOW delta passes. On the
operator's choice each time, LOW wording findings were fixed rather than ticketed,
until a pass found nothing. The PR's comments hold each pass's record. Occurrences
were added, on the operator's approval of each exact text and read back identical,
to #643 (lenses launched from the rendered prompt file) and #666 (successive
prose-only LOW rounds).

Closed workstream Merge-gate review evidence: the operator closed it in this session,
once #981 was fixed with nothing outstanding.

______________________________________________________________________

## Session — 2026-10-06 (one-run triage recovery paths removed, in Claude Code)

[#978](https://github.com/topij/agentic-dev-kit/pull/978) removed #969's `correct-project`
route and #952's historical flat-gate recovery. It merged as
`7c0f6de429f0a7e1a627d0b20e8eb952a46ac395`. The removal took their CLI flags, tests,
`KIT_OWNED` entries and workflow sections with it. `recovery.py` matches its pre-#952
revision except for the `isinstance(operator, str)` hardening in `_approval`. Installation
[in-parallel-oy/cs-toolkit#2558](https://github.com/in-parallel-oy/cs-toolkit/pull/2558)
merged as `31dde6c28f4a15f6c9063ae3e500fb5fa26d2e75`. #975 is closed.

Decided: `model.py` keeps a shape check that lets a completed LIVE state carrying a
`proposal_correction` receipt parse. cs-toolkit's completed state carries one, and only a
session-starting entry retires a completed state. That entry also freezes the inbox and
starts a new run, so retiring the state early would have pre-empted cs-toolkit's scheduled
Friday draft. The check lets that draft retire the state under either engine.
`test_a_completed_state_with_a_project_correction_receipt_still_retires` pins it.
The check's removal is #979.

Also checked, on 2026-10-06: no adopter state root on this machine held a live historical flat gate.
cs-toolkit's recovery bundles are left as history.

Not established: the retirement itself. Read-only validation of cs-toolkit's real state passed
under both the kit and the installed code on 2026-10-06 (the commands are in #978's and
#2558's bodies). Neither ran the retirement.

cs-toolkit's main checkout was not pulled and still sat on its pre-install commit at
wrap-up. Its scheduled jobs run from that checkout, so the removal is live there only once
it is updated.

Review: #978 had one adversarial lens. Its LOW on the shim's unpinned conditions went to
#979; its LOW on this handoff's stale #975 wording is answered by #975's closure above.
#2558 merged on CodeRabbit's comment-verdict of its head. The two-lens panel did not run
there, because the reviewer was available and the copied code was byte-identical to
#978's reviewed code.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Review proportionality

**Status:** the lens-count half of #585's 2026-10-02 decision shipped in #927
(`8ea91add`): the class is computed from `review.safety_critical_paths`, and a standard PR
takes one isolated lens. #934 (`41beacb8`) gave a delta pass's two draws their own named
flags; #921 stays open for the cockpit-side check of the verdict-line names. The
record-prose row of #585's decision is not built: its deterministic checks, and a lens
told which spans stay executed. #993 (`2d40c960`) added the review round budget: the
opening review plus `review.round_budget` fix rounds, then an operator decision packet.
#1006 (`f917d946`) matches the class case-folded (#991) and closed #994's follow-ups; its
last LOW, #1008, was fixed by #1022 (`54655d9d`).
**Owner:**
[#585](https://github.com/topij/agentic-dev-kit/issues/585); round-budget follow-ups
[#994](https://github.com/topij/agentic-dev-kit/issues/994); related #921, #403, #666,
#305, and the class's documented limits #928, #929, #930 and #931.

▶ Next: #585's record-prose row — its deterministic checks, and a lens told which spans
stay executed.

### Scratch retention

**Status:** `scripts/sweep_scratch.py` and the `scratch:` config block shipped in
#986 (`dff111ae`). Its documented limits are in the engine docstring. #1005 (`f508d220`)
judges root and entry containment by filesystem identity as well as by path string (#1000). #997 owns
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
**Owner:** [#1009](https://github.com/topij/agentic-dev-kit/issues/1009), [#1026](https://github.com/topij/agentic-dev-kit/issues/1026).

▶ Next: #1026 — pin the lookup's baseline range and pathspec with tests, and state one fragment naming rule.
