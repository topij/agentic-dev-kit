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

## Session — 2026-10-13 (move-candidate bound, split-workflow link check, kit_doctor reference edge and panel_prompt fixture objects, from headless lanes, in Claude Code)

- **How it ran:** an autonomous overnight session. The operator approved the four lanes
  and self-merge for the `self`-class ones. Each lane ran as a headless `claude` lane
  (`dev_session.sh new --headless`, `launch_lane.py`). None of them opened its PR. Each
  stopped at one of two walls, both parked in the friction log:
  - the profile denied the `python3` spelling of the manifest regeneration;
  - `make test` outran the lane's Bash time limit.

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
  self_check_is_clean` at `1666e247` in `/Users/topi/Coding/agentic-dev-kit` passed,
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

## Session — 2026-10-12 (friction-log triage; record-prose preflight recognises moved pairings, in Claude Code)

- **Friction-log triage** (session `ae0b23b8`, engine-backed, approved in this session
  rather than over Slack): filed #1078, #1079, #1080, #1081, #1082 and #1083; archived
  TRI-04, TRI-08, TRI-09 and TRI-11; parked TRI-02, TRI-06, TRI-07 and TRI-14. Sweep PR
  [#1084](https://github.com/topij/agentic-dev-kit/pull/1084) merged as `e37b7bd9` at its
  reviewed head `427d2fa5`. The record-prose preflight failed on the moved keyword/reference
  pairings at archive lines 4279 and 4459; the operator accepted them as moved history.
- **Review proportionality:** [#1088](https://github.com/topij/agentic-dev-kit/pull/1088)
  merged as `2ca8ded9` on the operator's request. The preflight no longer reports a
  keyword/reference pairing whose lines were moved unchanged, in order, from lines the
  same change deletes from a narrative path. Copies, new adjacencies, pairings past
  `MAX_MOVED_SPAN` or `MAX_MOVE_CANDIDATES`, and commit messages are still reported.
  - Decided: archival preservation means exact bytes. This settles the parked TRI-06,
    which stays in the inbox until the next triage pass.
  - Review: CodeRabbit skipped. Adversarial `fallback:lens` full passes ran at `3922348b`
    and `042f36e2`, and `fallback:delta` passes at `40bef2ae` and `0463c18d`. The last
    delta's LOW finding is #1089, on the operator's decision.
  - Verification: `make test` at `042f36e2299c4e1a35913dc27fd6752140ec35a3` on
    2026-10-12, in `/Users/topi/Coding/agentic-dev-kit`, printed `4894 passed, 1 skipped`.
    The LOW repairs at `40bef2ae` and `0463c18d` had focused verification
    (`scripts/tests/test_record_prose.py`, `make lint`, the drift check) and current-head
    CI, as the LOW rule prescribes.
- **Filed this session:** #1078, #1079, #1080, #1081, #1082, #1083, #1089,
  [#1090](https://github.com/topij/agentic-dev-kit/issues/1090) and
  [#1091](https://github.com/topij/agentic-dev-kit/issues/1091); an occurrence comment
  on #1080.
- **Not established:** #1082 overlaps the open #677 (the state guard reporting a
  concurrent cockpit write as a suite leak). The two were not reconciled.

______________________________________________________________________

## Session — 2026-10-12 (workflow reference-file links tested; OpenKitchen upgraded to the skill bindings, in Claude Code)

- **Skills and instruction files:** [#1074](https://github.com/topij/agentic-dev-kit/pull/1074)
  merged as `55869a7e` on the operator's merge. It corrects `pr-watch/report-fields.md`'s
  link to `fallback-review-panel.md` and adds a test that every relative link in a
  workflow reference file points at an existing file.
  - Review: CodeRabbit skipped. An adversarial `fallback:lens` full pass ran at
    `5b9cc641`, and a `fallback:delta` pass at `8abd3b3d` reviewed the repair of its
    LOW findings. The delta pass's own LOW findings are #1075.
  - Verification: `make test` at `8abd3b3d599cf27ff052cc34a48aac288a323fda` on
    2026-10-12, in `/Users/topi/Coding/agentic-dev-kit`, printed `4882 passed, 1 skipped`.
- **OpenKitchen upgraded** from kit `c5da977` to `55869a7e` in topij/OpenKitchen#324,
  merged as `cb810b88` on the operator's request. The upgrade ran from a linked worktree
  off `origin/main`, because OpenKitchen's main checkout was on another session's branch
  with uncommitted edits.
  - The eight Claude commands were `kit-retired` and nothing in OpenKitchen read them,
    so they were deleted once the skills were installed.
  - Review: OpenKitchen configures no review bot, and the change is safety-critical
    there, so the two-lens panel ran at `4c35c81b`. Its LOW finding on links to the
    removed `.claude/commands/` is topij/OpenKitchen#325, on the operator's decision.
  - Verification: `run_installed_tests.py` with a temporary `DEVKIT_STATE_ROOT`, run on
    2026-10-12 in that worktree on the tree committed as `4c35c81b`, printed
    `3756 passed, 109 skipped`. The PR body carries the full stamp.
- **Filed this session:** [#1075](https://github.com/topij/agentic-dev-kit/issues/1075),
  topij/OpenKitchen#325; occurrence comments on
  [#61](https://github.com/topij/agentic-dev-kit/issues/61) (a hook missed in a linked
  worktree), [#990](https://github.com/topij/agentic-dev-kit/issues/990),
  [#992](https://github.com/topij/agentic-dev-kit/issues/992) and
  [#1055](https://github.com/topij/agentic-dev-kit/issues/1055).
- **Not established:** OpenKitchen's main checkout was not pulled. It stays on the other
  session's branch.

______________________________________________________________________

## Session — 2026-10-12 (workflow reference files required by kit_doctor; cs-toolkit upgraded to the skill bindings, in Claude Code)

- **Skills and instruction files:** [#1069](https://github.com/topij/agentic-dev-kit/pull/1069)
  merged as `6f543433`, on the operator's request. `kit_doctor` now marks a file under
  `workflows/<slug>/` `missing-required` when `<slug>.md` is installed at the kit's
  version. On the operator's word, the tracker marks #1057 done.
  - Review: CodeRabbit skipped. An adversarial `fallback:lens` full pass ran at
    `e3e4ed04`, and a `fallback:delta` pass at `02e2c21b` repaired its LOW findings. The
    delta pass's own LOW findings are #1070.
  - Verification: `make test` at `02e2c21b38e2f7479d6b1087d5f17376738c29b8` on
    2026-10-12, in `/Users/topi/Coding/agentic-dev-kit`, printed `4880 passed, 1 skipped`.
- **cs-toolkit upgraded** from kit `0b8166b8` to `6f543433` in in-parallel-oy/cs-toolkit#2632,
  merged as `4079572c`, on the operator's request. This was the first `/upgrade` under the
  skill bindings.
  - #1069 worked as intended there. Once the entries were refreshed, the five reference
    files reported `missing-required`.
  - **Decision (operator):** cs-toolkit keeps its seven `kit-retired` commands. Its own
    `check_skills.py --strict` (CI), its plan-hygiene guard and `skill-index.yaml` still
    read `.claude/commands/`. CUS-1692 migrates those, and #1071 asks `upgrade.md` to warn.
  - #1066's GraphQL probe broke cs-toolkit's adopter-owned `tests/test_pr_watch.py` under
    its live-path guard, and the PR pinned the probe there.
  - The #428 state guard tripped on live cron writes in cs-toolkit's main checkout. The
    stamped runs used a detached worktree, and the occurrence is on #467.
  - Review: CodeRabbit's verdict was clean but excluded `docs/**`, so the two-lens panel
    ran at `cbff90a1`. Its findings went to #1072 (a kit link) and CUS-1693 (cs-toolkit
    CI never runs `make test-devkit`).
- **Filed this session:** [#1070](https://github.com/topij/agentic-dev-kit/issues/1070),
  [#1071](https://github.com/topij/agentic-dev-kit/issues/1071),
  [#1072](https://github.com/topij/agentic-dev-kit/issues/1072), CUS-1692, CUS-1693; an
  occurrence comment on [#467](https://github.com/topij/agentic-dev-kit/issues/467).
- **Not established:** OpenKitchen is not upgraded. A stale kit clone at
  `/tmp/agentic-dev-kit` made this session clone under its scratchpad instead, because
  `rm -rf` is denied to the agent; the operator removed that clone at wrap-up.

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
[#921](https://github.com/topij/agentic-dev-kit/issues/921); related #403,
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
(#1070); both tickets stay open for the operator.
#1055 owns the Codex `openai.yaml` check, #1058 the triage split's remaining pin gaps,
#1098 the link check's remaining state-machine gaps.
**Owner:** `saved_plans/skills-and-instructions-assessment_2026-10-11.md`;
[#1055](https://github.com/topij/agentic-dev-kit/issues/1055),
[#1058](https://github.com/topij/agentic-dev-kit/issues/1058),
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

**Status:** #1099 (`1666e247`) makes the panel_prompt tampering tests reach fixture
objects through `_loose_object`, which names a packed or missing object as a setup
error, and turns auto-gc off in the fixtures. #1079 carries the residual LOWs from its
last delta and stays open. Assignment unconfirmed: no existing workstream owned #1079.
**Owner:** [#1079](https://github.com/topij/agentic-dev-kit/issues/1079).

▶ Next: #1079 — pin git's stderr in the missing-object test's match, and make
`_loose_object`'s wording claim existence rather than readability (the residual-LOW
comment on #1079 has the acceptance criteria).
