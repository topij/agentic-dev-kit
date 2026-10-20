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

## Session — 2026-10-20 (worktree-first sessions)

- **Worktree-first sessions:** [#1136](https://github.com/topij/agentic-dev-kit/pull/1136)
  merged as `023a211bc7b7cd7689fd98ad49b1841efe43f77e` on the operator's request.
  The shared `AGENTS.md` carries the task-worktree preference.
- Verification: `make test` at `7438abb864b6aea3fe74c5995c5039d021318ce3`, in
  `/private/tmp/agentic-dev-kit-worktree-preference-20261020`, on 2026-10-20 passed.
  The [review disposition](https://github.com/topij/agentic-dev-kit/pull/1136#issuecomment-6287957657)
  retains the exploratory mutation limits; no agent-compliance harness was run.
- The operator-approved triage filed
  [#1137](https://github.com/topij/agentic-dev-kit/issues/1137),
  [#1138](https://github.com/topij/agentic-dev-kit/issues/1138),
  [#1139](https://github.com/topij/agentic-dev-kit/issues/1139) and
  [#1140](https://github.com/topij/agentic-dev-kit/issues/1140). The archive-sweep
  [#1141](https://github.com/topij/agentic-dev-kit/pull/1141) carries the exact
  approve/archive/park commands; parked source entries remain in the inbox.
- Workstream **Worktree-first sessions** finished on the operator's confirmation;
  no follow-up remains.

______________________________________________________________________

## Session — 2026-10-18 (cs-toolkit upgrade support)

- **Scratch retention:** [#1126](https://github.com/topij/agentic-dev-kit/pull/1126)
  merged as `bc1bd023`, annotating the deliberate system-temp refusal for Bandit
  (#1124). [#1130](https://github.com/topij/agentic-dev-kit/pull/1130) merged as
  `d2f40206`; retirement now refreshes Git dependencies before removal (#1127).
  The cosmetic Bandit-selector follow-up is #1128.
- **Triage outcome receipts:** #1130 also delivered scheduled caller enforcement
  (#1129). Its [review disposition](https://github.com/topij/agentic-dev-kit/pull/1130#issuecomment-6248253499)
  records the evidence and the corrected verification chronology from the
  correctness lens; its overlapping full-suite run was discarded as verification.
- **Consumer upgrades:** the operator will continue cs-toolkit's upgrade using
  kit `d2f40206d3b819b496398ad0d08eba97a9d7b9ca`. This session did not upgrade
  cs-toolkit. The later adopter evidence is in **Consumer upgrades** below;
  copying CLI files alone does not establish real scheduled-run behavior.
- Verification: `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `2fb0981c6e8cbc71b3fe5785714029a201685555` on 2026-10-18 passed. The merged
  `d2f40206` tree matches that candidate. Full output is retained in
  `/private/tmp/devkit-1127-1129-evidence-eTfHvO/make-test-2fb0981c.log`.
- The session recorded uv-cache dependency refusals and review mutation/verification
  overlap, preserving scratch guards. The later triage sweep is recorded in
  [#1141](https://github.com/topij/agentic-dev-kit/pull/1141).
- On 2026-10-20 the operator canceled the retained October 18 triage draft
  `749a3ff1c51d4fe1928d7f0d4553c2cc`, preserving its source entries and report at
  `reports/triage_live_2026-10-18_749a3ff1c51d4fe1928d7f0d4553c2cc.md`.
  Fresh session `7858b0190c764ac3af1d3d1002463f7f` took the operator's new decisions.

______________________________________________________________________

## Session — 2026-10-18 (caller-owned triage receipts; managed review scratch)

- **Triage outcome receipts:** [#1121](https://github.com/topij/agentic-dev-kit/pull/1121)
  merged as `d5129869`. The caller allocates freshness for each engine call;
  cs-toolkit later integrated the wrapper in its PR 2769.
- **Scratch retention:** [#1122](https://github.com/topij/agentic-dev-kit/pull/1122)
  merged as `dd089388`, completing #900. Reviews now allocate owned rounds and
  retire them after processes finish and evidence is retained. The dependency
  protections remain in force; this did not reclaim legacy unmanaged scratch.
  The [review disposition](https://github.com/topij/agentic-dev-kit/pull/1122#issuecomment-6242495091)
  retains the review evidence; the residual CLI-help finding was routed to #996.
- Verification: `make test` at `e080536159c0b16874f47ed8b36336e296d820a3`, in
  `/Users/topi/Coding/agentic-dev-kit`, on 2026-10-18 passed. This is the reviewed
  scratch-lifecycle candidate, before the squash merge.
- Retirement kept the opening and repair panel rounds because uv-cache `.git`
  markers triggered dependency protection. The friction archive records the paths
  after the #1141 sweep; the guards were not bypassed.
- Workstream assignment confirmed by the operator: **Triage outcome receipts**
  and **Scratch retention**.

______________________________________________________________________

## Session — 2026-10-16 (ticket-creation region snapshots; split-workflow placement and citation pins; REST review-read gap decision, in a Claude Code cloud session)

- **Ticket execution environments:** [#1114](https://github.com/topij/agentic-dev-kit/pull/1114)
  (`9a3473df`) pins the ticket-creation instructions of `triage-friction-log`,
  `post-merge-systemize` and `wrap-up` by region snapshots under
  `scripts/tests/fixtures/ticket-creation-regions/`, and checks that `wrap-up` declares
  environment metadata before a ticket is presented and inside the approved payload.
  Its changelog fragment is `changelog.d/project-thread-na11fx.md`. Not established: a
  contradiction written outside a region, or an agent's classification.
- **Skills and instruction files:** [#1115](https://github.com/topij/agentic-dev-kit/pull/1115)
  (`738d1b2e`) gives the split-workflow heading-placement and summary-citation
  assertions a mutation case each that only it rejects, and mutates every reference
  file's opening tail clause. #1058 stays open for the operator.
- **pr-watch REST backend:** the operator kept #94 rows 7 and 9 as a documented gap
  while REST cannot authorize a merge; the `&page=N` design for when cloud merge is
  revived is [on #94](https://github.com/topij/agentic-dev-kit/issues/94#issuecomment-6213171824).
- Both PRs were merged from the cloud session through the GitHub MCP on the operator's
  word. Their `--record-review fallback:panel` commands could not run there (#951) and
  are in each squash message for a local run.
- Verification: `make test` in `/home/user/agentic-dev-kit` (cloud, root) at
  `71d04d3efe6ceb15b34c41989e3f46d313c8e386` on 2026-10-16 printed
  `7 failed, 5004 passed, 38 skipped`; every failure is in the cloud-environment set
  `CLAUDE.md` names. CI `Test` was green on each merged head.
- The friction-log triage was not run: the skill is operator-invoked only, so a
  delegated session on the operator's device could not start it.
- Closed workstream Ticket execution environments: #1114 covers #1040, closed on the
  operator's word.
- Closed workstream pr-watch REST backend: nothing moves until cloud merge is revived;
  #94 and #951 hold the detail.

______________________________________________________________________

## Session — 2026-10-16 (triage repository identity redesigned and merged; shared-hook install merged; residual review findings filed, in Claude Code)

- **Triage outcome receipts** (renamed from *Triage repository identity and outcome
  receipts*): [#1111](https://github.com/topij/agentic-dev-kit/pull/1111) merged as
  `62e0ffaa` on the operator's request, pinned to the reviewed head `7a59669e`.
  - Shipped: linked worktrees name the main worktree. A recorded identity matches by
    string comparison only: it equals the current one, or equals it with the invoking
    checkout's own root, so a session a linked worktree recorded before #1111
    continues from that worktree's path. A checkout whose main worktree cannot be
    proven names itself, including every checkout on a Git older than 2.31; #1116
    names one `--separate-git-dir` layout whose linked worktrees name a phantom root
    instead. Results
    carry `disposition` / `waiting_on` / `refusal_code`. An unverified tracker or forge
    write waits on `reconciliation`, except an unsettled forge `pr-watch` or
    `merge-read-back`, which waits on `finalize`.
  - Decided: the invocation-bound outcome receipt is out of #1111 (operator's option C).
    Its code is on branch `feat/triage-outcome-receipts` at `fabed73e`, and #1103
    stays open for it. Membership probing of recorded roots was replaced by equality,
    on the operator's call, after its rounds kept finding edges in that probing.
  - Review: the two-lens round at `7a59669e` left no finding above LOW; each round's
    disposition is on #1111. Residual LOW findings: #1116.
  - Verification: `make test` at `7a59669e0e3d6c64387354e6825f791bfbe6bfac` on
    2026-10-16, in `/Users/topi/Coding/agentic-dev-kit-wt/triage-worktree-identity`,
    printed `5099 passed, 1 skipped`.
- **Shared hook installation:** [#1112](https://github.com/topij/agentic-dev-kit/pull/1112)
  merged as `aff05641`, pinned to `cf1a5402`, after a round with nothing above LOW.
  Residual LOW findings: #1117. `kit_doctor`'s hook advice from a linked worktree is
  noted on #61.
- **Consumer upgrades:** no consumer was upgraded. cs-toolkit's scheduled triage
  needs #1111 installed there.
- **Filed this session:** #1116, #1117; comments on #1103 (receipt branch) and #61.
- **Assignment:** confirmed by the operator. The three workstream entries drop their
  `assignment unconfirmed` markers, and the triage entry is renamed for what remains.

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
archive sweep rewrites (friction archive; #1139). #1096 (`8beee9a1`) pins its candidate bound
with a positional test.
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
guards, wording, and the `.git`-gone exit 2, including the CLI-help follow-up from
#1122. #1122 (`dd089388`) shipped #900: allocated review rounds, prompt enforcement,
explicit retirement and disk/scratch reporting. Retirement retains Git-dependency
protections; #1130 (`d2f40206`) delivered #1127's dependency refresh at retirement time.
#997 owns bare fixture retention; the friction archive records the uv-cache marker
case. #1134 (`b739bc46`) delivered empty-marker handling. Fixture dependencies remain protected.
`state/review-evidence/` retention remains scoped to #861.
**Owner:** [#900](https://github.com/topij/agentic-dev-kit/issues/900),
[#997](https://github.com/topij/agentic-dev-kit/issues/997),
[#996](https://github.com/topij/agentic-dev-kit/issues/996),
[#861](https://github.com/topij/agentic-dev-kit/issues/861),
[#895](https://github.com/topij/agentic-dev-kit/issues/895).

▶ Next: #997 — choose how a session entry whose only git dirs are test fixtures
becomes sweepable without reopening the outside-dependent fail-open (an operator
design decision). Keep empty-cache-marker handling separate from the fixture
dependency decision.

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
#1115 (`738d1b2e`) pins the triage split's section placement and summary citations
for #1058, which stays open for the operator. #1132
(`a5ec9c0f594142559bdb47ece083f6133a5efe6e`) delivered #1098's link-check follow-up.
**Owner:** `saved_plans/skills-and-instructions-assessment_2026-10-11.md`;
[#1055](https://github.com/topij/agentic-dev-kit/issues/1055),
[#1058](https://github.com/topij/agentic-dev-kit/issues/1058),
[#1070](https://github.com/topij/agentic-dev-kit/issues/1070),
[#1075](https://github.com/topij/agentic-dev-kit/issues/1075).

▶ Next: operator selection after #1132; the previous #1098 implementation step shipped.

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

### Triage outcome receipts

**Status:** #1111 (`62e0ffaa`) shipped linked-worktree identity and result
dispositions. #1121 merged as `d5129869` on 2026-10-18 (Europe/Helsinki), completing
#1103's receipt follow-up. The receipt contract makes the caller allocate a fresh id and
destination before each engine CLI call, publishes without replacement, and checks
without writing. #1130 (`d2f40206`) delivered #1129: scheduled calls claim a
caller-owned attempt before dispatch, and the final caller check retains direct-call refusals.
The preserved `fabed73e` implementation is design evidence; the
round-3 decision packet and round-4 findings on #1111 explain why receipt clearing
was removed. #1116 carries the identity follow-ups, including the cs-toolkit upgrade's
timeout and report-containment findings.
**Owner:** [#1103](https://github.com/topij/agentic-dev-kit/issues/1103);
[#1116](https://github.com/topij/agentic-dev-kit/issues/1116).

▶ Next: verify cs-toolkit's real scheduled-run receipts and the documented trusted
launcher boundary; installed wrapper code alone does not establish live invocation
coverage or completed-state retirement.

### Shared hook installation

**Status:** #1112 (`aff05641`) stopped `init.sh` run from a linked worktree from writing
the hooks every checkout shares. #1117 holds its residual LOW findings. #990's items 1
(lens definitions rendered for the kit's config) and 3 (migration gaps) are open.
**Owner:** [#990](https://github.com/topij/agentic-dev-kit/issues/990);
[#1117](https://github.com/topij/agentic-dev-kit/issues/1117).

▶ Next: #990 item 1 — render the lens agent definitions from the adopter's config rather than the kit's.

### Consumer upgrades

**Status:** cs-toolkit's
[in-parallel-oy/cs-toolkit#2769](https://github.com/in-parallel-oy/cs-toolkit/pull/2769)
integrated caller enforcement and managed review rounds after the #2762 upgrade.
`git show 5b49543928c4d4187598e18d17deececb9419a34:kit-manifest.json` in
`/Users/topi/Coding/in-parallel/cs-toolkit` on 2026-10-20 recorded kit
`b739bc46faa99764f3a10200dc2e02720e61a6de`. At that same adopter revision,
`git show` of `scripts/scheduled_triage.py` and `config/automations.yaml` showed
the per-call wrapper and its deliverable checks; `scripts/retire_triage_state.py`
was a read-only guard. No real scheduled job or live state retirement was run here.
The adopter handoff separates notification-provider integration from the installed
receipt contract. The earlier local assessment,
`saved_plans/consumer-upgrade-assessment_2026-10-15.md`, predates these upgrades.
**Owner:** #1116, #990, #1011, #1109, #979.

▶ Next: verify cs-toolkit's scheduled-run receipts and completed-state retirement
before removing the #979 shim; resolve unattended notification delivery as its own
adopter decision. Reassess OpenKitchen's installation and lane prerequisites before
an upgrade there.
