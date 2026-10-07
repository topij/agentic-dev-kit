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
  - The panel showed the `test` entry's forge-prefix refusal is unreachable, so the claim was narrowed rather than tested.
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

Lanes ran with no operator present, so no tracker write was made. This session's friction is parked in the friction log.

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

## Session — 2026-10-06 (cs-toolkit LIVE acceptance completed, in Claude Code)

The operator judged the acceptance work over-built and chose the smallest fix for
the landed-Markdown hold. [#973](https://github.com/topij/agentic-dev-kit/pull/973)
compares tracker payloads with list markers outside fenced code spelled `-`. The
engine's existing resume reconciliation did the rest, with no new contract,
state shape or approval step. #973 merged as
`6aadec23ac4ac543b7381ca550cf03a5638602f1`. Installation
[in-parallel-oy/cs-toolkit#2551](https://github.com/in-parallel-oy/cs-toolkit/pull/2551)
merged as `fb0004704e2d43ccd1a3c21c4f85c0944b6811c6`, pinning it.

The installed `resume` verified TRI-01 as CUS-1670. Three finalize continuations
then archived TRI-01 through the engine's sweep
[in-parallel-oy/cs-toolkit#2552](https://github.com/in-parallel-oy/cs-toolkit/pull/2552),
which merged as `c84d76c6536cad8d0f0d131b8cb095463ad11a12`. The run completed.
[The acceptance record on #6](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-6012620438)
holds the commands, revisions, directories and results. #6 stays open. This
supersedes the earlier 2026-10-06 Codex entry's pending reconciliation design.

Filed on the operator's approval of each exact text, each read back identical:
- #974, the learning: classify a held state as a recurring defect or a one-off
  incident before building an engine mechanism.
- #975: remove the one-run triage recovery paths.
- #976, with a follow-up comment: LOW residue from #973's and #2551's reviews.

`project_correction.py`'s pin on the `providers.py` digest failed #973's first CI
run, although the project guard was untouched. The digest list is now append-only,
and #975 covers removing the pin along with its path.

Closed workstream cs-toolkit Codex validation and Linear installation: the
operator closed it once LIVE acceptance completed. Its follow-ups are #974, #975
and #976. The separate frozen kit-friction decision
(`469bcd5829244adeb17443d1a45a6c01`) remains pending and untouched; the new
*Kit friction-log triage* workstream carries it.

______________________________________________________________________

## Session — 2026-10-06 (cs-toolkit installed correction and landed Markdown hold, in Codex)

Source [#969](https://github.com/topij/agentic-dev-kit/pull/969) merged as
`01269cc80e05ecab1987ebaa97ee76bba306afee`; installation
[#2545](https://github.com/in-parallel-oy/cs-toolkit/pull/2545) merged and was
delivered as `cddb46c284d92b3261b0ec1977d82fa3a629cbcf`, pinning that source.
The operator authorized checked installation/archive/wrap-up merges and delegated
approval of the exact project-only action and complete corrected filing payload.
Concrete presentations retain that human text beside runtime-computed digests;
they do not invent a later human reply. Configured reviewers ran at
`gpt-5.6-sol` / `medium`; GitHub runner cancellations were retried at the same
reviewed head without a review waiver or permanent configuration change.

The installed correction applied action
`767e470416961a2aa43a0a0e422bd79d46ce47875b13bc2179139c0d8d9d82f9`,
retaining rejected evidence and clearing its approval. The approved corrected
create landed CUS-1670, but Linear changed Markdown bullets from `-` to `*`.
`libs/report-utils/.venv/bin/python live-62970e59-normalization-readback.py`
at `cddb46c284d92b3261b0ec1977d82fa3a629cbcf` on 2026-10-05 UTC, in
`/Users/topi/Coding/in-parallel/cs-toolkit`, recorded the ambiguous exact-payload
mismatch with mutation-prohibited marker searches, independent by-ID readback
and unchanged retained state/report/quarantine bytes. No duplicate create,
issue update, raw state edit, replacement freeze or TRI-01 archive followed.
[The acceptance record](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-6003071493)
retains the commands, actual results and digests. A bounded representation
reconciliation design awaits the operator before further engineering.
This entry supersedes the earlier project-name resume instruction; the separate
frozen kit-friction decision remains pending. Follow-ups #970 and #971 were
recorded without fixes claimed. Evidence remains under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/`.

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
#1006 (#991's case-folded class match and #994's follow-ups) is **held for the operator** at
`fd2dd68974a8cd0bf317c1e90985aa790bd80473`: its round budget is spent with two LOW findings open, and its
decision packet is on the PR.
**Owner:**
[#585](https://github.com/topij/agentic-dev-kit/issues/585); round-budget follow-ups
[#994](https://github.com/topij/agentic-dev-kit/issues/994); related #921, #403, #666,
#305, and the class's documented limits #928, #929, #930 and #931.

▶ Next: operator — decide #1006 from its decision packet (merge at `fd2dd689` and file the two
LOWs as one ticket, or authorize one more fix round); then #585's record-prose row.

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

### Kit friction-log triage

**Status:** a kit budget triage froze inbox session `469bcd5829244adeb17443d1a45a6c01`
on 2026-10-05 and left it awaiting approval, with every inbox block preserved. Its
frozen inbox and pipeline state sit in an isolated state root,
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/kit-friction-budget-state/`;
the live `state/triage/` holds nothing for it. **Owner:** that retained state.

▶ Next: present session `469bcd58`'s retained proposals to the operator and obtain
their archive-or-park decisions before any other `triage-friction-log` sweep of the kit
inbox.
