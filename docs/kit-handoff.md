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

## Session — 2026-10-15 (triage linked-worktree identity and outcome receipts; shared-hook install from linked worktrees; consumer-upgrade assessment, in Claude Code)

- **Triage repository identity and outcome receipts:** [#1111](https://github.com/topij/agentic-dev-kit/pull/1111)
  (for #1103) is open and ready at `9ee0fd9b`, held for the operator.
  - What it does: linked worktrees name the main worktree; recorded identities are
    compared by verified Git membership, never rewritten; results carry
    `disposition` / `waiting_on` / `refusal_code`; the CLI can publish and check an
    invocation-bound outcome receipt.
  - Review: the two-lens panel ran three rounds (`342f0a9a`, `cc3eb05f`, `9ee0fd9b`),
    and the round budget is spent. The decision packet on the PR names the open
    findings. The receipt-clearing path drew a finding in every round, so the packet
    treats it as design feedback rather than proposing another patch.
  - Found by the author in round 1, then corrected: a `--separate-git-dir` primary's linked
    worktree would have hard-stopped.
  - Verification: `make test` at `9ee0fd9bd486e0e8860233cfaa02a62287a3562a` on
    2026-10-15, in `/Users/topi/Coding/agentic-dev-kit-wt/triage-worktree-identity`,
    printed `5069 passed, 1 skipped`.
- **Shared hook installation:** [#1112](https://github.com/topij/agentic-dev-kit/pull/1112)
  (for #990 item 2) is open and ready at `5fda739d`, held for the operator.
  - What it does: from a linked worktree, `init.sh` / `make install-hooks` report a
    shared hooks directory instead of writing it. A byte-identical, executable shim is
    `already current`; anything else is `deferred`, unless
    `DEVKIT_INSTALL_SHARED_HOOKS=1` is set.
  - Review: three panel rounds, and the round budget is spent. The decision packet's
    open findings are stale `init.sh --help` / `adopt.md` prose (MEDIUM) and five LOW
    findings.
  - Verification: `make test` at `5fda739deb899a75a959e7c2b1e2df0282e478e3` on
    2026-10-15, in `/Users/topi/Coding/agentic-dev-kit-wt/linked-worktree-hooks`,
    printed `5041 passed, 1 skipped`.
  - #990's items 1 (lens definitions rendered for the kit's config) and 3 (migration
    gaps) are untouched and remain on #990.
- **Consumer upgrades:** the assessment is `saved_plans/consumer-upgrade-assessment_2026-10-15.md`
  (local, not committed).
  - Read-only facts: cs-toolkit records kit `6f543433` and OpenKitchen `55869a7e`
    (their `kit-manifest.json` on `origin/main`).
  - cs-toolkit's retained triage state is a completed live session bound to its
    primary checkout. It matches exactly under #1111, and it still carries the #979
    receipt.
  - Its 2026-10-09 scheduled draft stopped on the identity mismatch in a `/tmp`
    worktree, and the finalize job logged a passed deliverable check anyway.
  - #989's items do not trigger for either consumer's install scope.
  - #1011 and #1109 matter only to OpenKitchen, which installs lanes; cs-toolkit
    declines them.
  - No consumer was upgraded and no tracker write was made, on the operator's
    instruction.
- **Assignment:** all three workstream entries below are new, and the operator did not
  confirm the assignment.

______________________________________________________________________

## Session — 2026-10-15 (Codex policy reporting, fixture diagnostics and lane manifest guidance)

- **Skills and instruction files:** [#1108](https://github.com/topij/agentic-dev-kit/pull/1108)
  merged as `f066b3ae3d4b902e7c8d30c8ea78eff25d9d7c95`. Added Codex invocation-policy reporting.
  Original scope `oct14-policy-report` is consciously parked; its replacement shipped.
- **Panel prompt test fixtures:** [#1107](https://github.com/topij/agentic-dev-kit/pull/1107)
  shipped git-stderr provenance coverage and missing-object wording on 2026-10-14.
  Original scope `oct14-fixture-stderr` is consciously parked; its replacement shipped.
- **Headless lane manifest refresh:** [#1106](https://github.com/topij/agentic-dev-kit/pull/1106)
  documented the allowed refresh command on 2026-10-14. Original scope
  `oct14-manifest-command` is consciously parked; its replacement shipped.
- **Decisions and evidence:** workstream assignments were confirmed. PR comments retain
  verification and review receipts. Failed launcher receipts were not treated as completion.
- **Filed with exact-payload approval:** [#1109](https://github.com/topij/agentic-dev-kit/issues/1109)
  and an [occurrence on #1011](https://github.com/topij/agentic-dev-kit/issues/1011#issuecomment-6185414536).
  Review-screening and verification-ordering incidents remain in the friction inbox.

______________________________________________________________________

## Session — 2026-10-13 (move-candidate bound, split-workflow link check, kit_doctor reference edge and panel_prompt fixture objects, from headless lanes, in Claude Code)

- **How it ran:** an autonomous overnight session. The operator approved the four lanes
  and self-merge for the `self`-class ones. Each lane ran as a headless `claude` lane
  (`dev_session.sh new --headless`, `launch_lane.py`). None of them opened its PR.
  The #1075, #1070 and #1079 lanes stopped because they could not regenerate
  `kit-manifest.json`. The #1089 lane ended earlier, on a denied call after its
  `make test` was killed at the Bash time limit. Both walls are parked in the friction
  log.

  The cockpit finished each lane: rebase, `uv run scripts/kit_doctor.py
  --generate-manifest`, the stamp, the review, and `dev_session.sh merge`.
  `reconcile_sessions.sh` reported all four scopes merged, and the lane sessions were
  removed.
- **Review:** CodeRabbit skipped every PR (automatic reviews are disabled). Each PR had
  an isolated adversarial `fallback:lens` full pass. LOW findings took
  `fallback:delta` repairs or tickets, with the dispositions and verbatim verdict lines
  on each PR. The cockpit applied every mutant a lane named, in a scratch clone.
- **Review proportionality:** [#1096](https://github.com/topij/agentic-dev-kit/pull/1096)
  merged as `8beee9a1`. A positional test now pins `MAX_MOVE_CANDIDATES`, so the values
  7, 9 and 1 each fail a behavioural case. The full pass had no findings.
- **Skills and instruction files:**
  - [#1097](https://github.com/topij/agentic-dev-kit/pull/1097) merged as `0f8e93f2`. A
    fence-like line inside an HTML block, or after a form feed, no longer hides later
    links from the split-workflow link check. A delta added four cases for the full
    pass's surviving mutants. The state-machine gaps that pass found are
    [#1098](https://github.com/topij/agentic-dev-kit/issues/1098).
  - [#1100](https://github.com/topij/agentic-dev-kit/pull/1100) merged as `5d29a75f`.
    It covers #1069's residual LOWs. Two deltas then narrowed the read-all pin and
    shortened its docstring to what the regex matches.
- **Panel prompt test fixtures:**
  [#1099](https://github.com/topij/agentic-dev-kit/pull/1099) merged as `1666e247`.
  Tampering tests reach fixture objects through `_loose_object`, which names a packed
  or missing object as a setup error. Two deltas followed. Their last pair of LOWs went
  to #1079 as a comment rather than a third repair round, because each round had
  produced a new wording-sized LOW (the #1080 shape).
- **Verification:** each PR carries its own `make test` stamp in a PR comment, run in
  that lane's worktree under `/Users/topi/Coding/dev-model-sessions/` on 2026-10-13.
  The LOW repairs had focused runs and current-head CI, as the LOW rule prescribes.
  After the last merge, `pytest scripts/tests/test_kit_doctor.py -k
  self_check_is_clean` at `1666e247` on 2026-10-14, in
  `/Users/topi/Coding/agentic-dev-kit`, passed,
  which shows the four separately regenerated manifest hunks merged consistently.
- **Filed this session:** #1098 and an occurrence comment on #1079. Both were written
  during the night under the operator's overnight grant. The wrap-up rule does not
  count that grant as approval for a tracker write, so the operator should confirm
  both.
- **Not established:** #1089, #1075, #1070 and #1079 are still open, for the operator to
  mark done; #1079 now also carries the residual LOWs. The workstream assignment
  of *Panel prompt test fixtures* is unconfirmed.

______________________________________________________________________

## Session — 2026-10-13 (kit-retired command deletion checks adopter references; REST reads judged against GitHub's counts, in a Claude Code cloud session)

- **Skills and instruction files:** [#1077](https://github.com/topij/agentic-dev-kit/pull/1077)
  merged as `8bac932` on the operator's go-ahead. `upgrade.md` Step 4 now searches the
  repository for references to `.claude/commands/` and to a `kit-retired` command's own
  path before deleting it, and keeps the command when adopter code or CI depends on it;
  Step 1 and the adapter-report hint say the same. Review: one adversarial
  `fallback:lens` pass and three `fallback:delta` passes, recorded in the PR's review comment. Receipts were not
  recorded, because `--record-review` refuses on the REST backend. #1071, which the PR
  answers, was open when this entry was written; closing it waits for the operator.
- **pr-watch REST backend:** [#1093](https://github.com/topij/agentic-dev-kit/pull/1093)
  merged as `4fae786f` on the operator's go-ahead, from the cloud session through the
  GitHub merge API. A REST read short of a count GitHub sends (check-runs and
  combined-status `total_count`, the PR's `comments` / `review_comments`) is listed in
  `truncated_reads`; a body missing those counts or a boolean `draft`, or holding a
  non-object list element, exits 2. It gates nothing in `pr_watch`.
  - Decided: only step 1 of the #94 plan (detection) was worth doing. Steps 2 and 3,
    which would let a cloud session record receipts and merge through `pr_watch`, were
    judged to cost more than they buy and are parked on #94.
  - Decided: a "full last page with no next link" check for reviews was built and
    dropped in review. A complete list an exact multiple of `per_page` long flagged
    every poll on a quiet PR.
  - Review: two-lens full panels at `7757f03`, `593ce38` and `ae4706c`, then a
    two-lens delta at `454ae79`; receipts listed in the PR body, not recorded.
  - Verification: `make test` at `454ae79be8ede08cf03556fc0472767ee9f35607` on
    2026-10-12, in `/home/user/rest-failclosed` (cloud), printed
    `8 failed, 4892 passed, 37 skipped`; the failures are the cloud-sandbox root and
    process-group tests. CI on `7ffa549f` passed.
- **Not established:** whether GitHub's `review_comments` count can permanently exceed
  the inline-comment list (pending or hidden comments). The lenses could only sample
  this repository, where every PR's inline count was zero. If it can, session-start
  would report that PR's review findings unavailable on every poll.
- **Residual LOWs from #1093's review, not filed:** no test reads a wrapped surface
  exactly one row short of `total_count`, and one sentence on triage's terminal receipt
  is loose in mechanism. Both are listed in the PR body.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Review proportionality

**Status:** #927 (`8ea91add`) shipped the computed review class; #934 (`41beacb8`)
added named delta draws; #993 (`2d40c960`) shipped the review round budget.
#1039 (`fa905cd09c950b96fe926ceb21d69ff7c00dea7c`) shipped #585's record-prose
preflight and executed-span guidance on 2026-10-10. The P2 regression the operator
deferred to #1041 shipped in #1044 (`8f41ea42`); #403's precedence question was outside the change.
#1088 (`2ca8ded9`) exempts pairings moved unchanged, not ones across a heading the
archive sweep rewrites (friction log). #1096 (`8beee9a1`) pins its candidate bound
with a positional test; #1089 stays open for the operator.
#921 owns the cockpit check of verdict-line names.
**Owner:** [#585](https://github.com/topij/agentic-dev-kit/issues/585),
[#921](https://github.com/topij/agentic-dev-kit/issues/921),
[#1089](https://github.com/topij/agentic-dev-kit/issues/1089); related #403,
#666, #305, and the class's documented limits #928, #929, #930 and #931.

▶ Next: #921 — make the cockpit check that a delta lens returned both the
`prose-class:` and `safety-critical:` verdict lines before a `fallback:delta` receipt
is recorded.

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

### Skills and instruction files

**Status:** #1052 (`f7d8749a`), #1053 (`78d623c3`) and #1054 (`ea4010db`) shipped on
2026-10-11, and #1061 (`367be931`) and #1063 (`ad65e539`) split pr-watch into an entry
and `pr-watch/report-fields.md`. #1069 (`6f543433`) makes an absent reference file
`missing-required`. cs-toolkit runs the skill bindings since in-parallel-oy/cs-toolkit#2632,
and OpenKitchen since topij/OpenKitchen#324 (`cb810b88`). #1074 (`55869a7e`) corrected
`pr-watch/report-fields.md`'s link and tests every relative link under `workflows/*/`.
#1077 (`8bac932`) makes `upgrade.md` Step 4 search for adopter references before
deleting a `kit-retired` command (#1071).
#1097 (`0f8e93f2`) keeps a fence-like line in an HTML block or after a form feed from
hiding later links (#1075), and #1100 (`5d29a75f`) covers #1069's residual LOWs
(#1070).
#1108 (`f066b3ae3d4b902e7c8d30c8ea78eff25d9d7c95`) added the Codex invocation-policy report for #1055.
#1058 owns the triage split's remaining pin gaps, and #1098 the link check's remaining
state-machine gaps.
**Owner:** `saved_plans/skills-and-instructions-assessment_2026-10-11.md`;
[#1055](https://github.com/topij/agentic-dev-kit/issues/1055),
[#1058](https://github.com/topij/agentic-dev-kit/issues/1058),
[#1070](https://github.com/topij/agentic-dev-kit/issues/1070),
[#1075](https://github.com/topij/agentic-dev-kit/issues/1075),
[#1098](https://github.com/topij/agentic-dev-kit/issues/1098).

▶ Next: #1058 — pin the triage split's section placement and full normative sentences
in the mutation test in `scripts/tests/test_portability.py`.

### pr-watch REST backend

**Status:** #1093 (`4fae786f`) judges REST reads complete against the counts GitHub
sends and rejects malformed bodies (step 1 of #94's plan). Reviews carry no count, so a
review read that loses its `Link` header still reads as complete (#94 re-audit rows 7
and 9). REST still cannot authorize a merge; letting a cloud session record receipts
and merge (#94 steps 2 and 3) is parked as not worth its cost. #951 owns the cloud
session's GraphQL block.
**Owner:** [#94](https://github.com/topij/agentic-dev-kit/issues/94),
[#951](https://github.com/topij/agentic-dev-kit/issues/951).

▶ Next: #94 — decide whether the REST review read gets a completeness signal (rows 7
and 9) or stays a documented gap, then say so on #94.

### Panel prompt test fixtures

**Status:** #1099 (`1666e247`) routed tampering tests through `_loose_object` and
turned fixture auto-gc off. #1107 (`fc35fbe8`) added git-stderr provenance coverage
and narrowed the missing-object wording. Workstream assignment confirmed.
**Owner:** [#1079](https://github.com/topij/agentic-dev-kit/issues/1079).

▶ Next: review #1079 against the delivered fixture changes and decide its tracker disposition.

### Headless lane manifest refresh

**Status:** #1106 (`2276c153`) documented `uv run scripts/kit_doctor.py --generate-manifest`
for the headless lane profile.
**Owner:** [#1102](https://github.com/topij/agentic-dev-kit/issues/1102).

▶ Next: review #1102 against the delivered lane guidance and decide its tracker disposition.

### Triage repository identity and outcome receipts

**Status:** [#1111](https://github.com/topij/agentic-dev-kit/pull/1111) is open at
`9ee0fd9b`, held for the operator with its round budget spent; the decision packet on the
PR recommends option A if the receipt surface is wanted now, otherwise C (ship identity
and dispositions, move the receipt surface to a follow-up). cs-toolkit's scheduled triage needs the identity half. Assignment
unconfirmed — may belong to Triage engine hardening.
**Owner:** [#1103](https://github.com/topij/agentic-dev-kit/issues/1103); PR #1111.

▶ Next: operator decides #1111's decision packet (A, B or C); then pr-watch 1111 for the chosen route.

### Shared hook installation

**Status:** [#1112](https://github.com/topij/agentic-dev-kit/pull/1112) is open at
`5fda739d`, held for the operator with its round budget spent; its open findings are one
docs MEDIUM and five LOW findings (decision packet on the PR). #990's lens
rendering and migration items are untouched. Assignment unconfirmed.
**Owner:** [#990](https://github.com/topij/agentic-dev-kit/issues/990); PR #1112.

▶ Next: operator decides #1112's decision packet (option A is the one further round the packet scopes).

### Consumer upgrades

**Status:** neither consumer was upgraded. The plan, the facts read from each consumer
and the issue-by-consumer impact are in
`saved_plans/consumer-upgrade-assessment_2026-10-15.md` (local). cs-toolkit's
scheduled triage is blocked until #1111's identity change is installed there. Assignment
unconfirmed.
**Owner:** `saved_plans/consumer-upgrade-assessment_2026-10-15.md`; #1103, #990, #1011,
#1109, #979.

▶ Next: after #1111 merges, `/upgrade` cs-toolkit from a fresh linked worktree of its `origin/main` (plan step 2 of the local `saved_plans/consumer-upgrade-assessment_2026-10-15.md`), with operator approval.
