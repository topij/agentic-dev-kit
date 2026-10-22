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

## Session — 2026-10-22 (owned review rounds retire fixture git dirs; workstream tracker pass)

- **Scratch retention:** [#1186](https://github.com/topij/agentic-dev-kit/pull/1186)
  merged as `0b5d226e`. `--finish-review-round` on a verified round no longer keeps it
  for a bare repository, a `--separate-git-dir` target whose `.git` pointer is in the
  round, or a `.git` file that does not start with `gitdir:`. A dependency recorded
  outside the round stays kept; the engine docstring lists the limits, among them a
  decoy in-round pointer (#1189). The age sweep is unchanged.
- **Decided:** the operator chose #997's option A (receipt-owned rounds) and filed option
  B (unowned entries) as #1185. A follow-up ticket was chosen over widening #1186 for
  the sweep suite's own deliberately unprovable fixtures (#1188). The round-2 LOW
  findings were ticketed as #1189 rather than taking a third review round.
- **Review:** a full panel at `82a867e8`, then a dual-lens delta at `49dc15d8`. The PR's
  dispositions record both. `make test` at `49dc15d8`, in
  `.claude/worktrees/owned-round`, on 2026-10-22 printed `5492 passed, 1 skipped` and
  exited 0.
- **Not established:** that a round whose lens ran `test_sweep_scratch.py` can be
  retired. #1186's own round-1 allocation `review-72a279dd…` is still on disk, kept by
  those fixtures (#1188).
- **Tracker pass:** #1079 and #1102 were marked completed and #507 not planned
  (superseded by changelog fragments), each with an evidence comment; #1026 and #1120
  were already complete on 2026-10-21. Filed #1185, #1188 and #1189; added an
  occurrence to #1144.
- Retired workstreams, on the operator's decision because each one's issue is
  complete: Changelog fragments, Record-prose report limits, Panel prompt test
  fixtures, Headless lane manifest refresh.

______________________________________________________________________

## Session — 2026-10-22 (reviewer measurement and verifier compute, in a Claude Code cloud session)

- **Reviewer measurement:**
  [#1168](https://github.com/topij/agentic-dev-kit/pull/1168) (`e0b6a7b`) has
  `post-merge-systemize` read fallback-panel dispositions as findings and tally
  reviewer precision (#772, #1157).
  [#1169](https://github.com/topij/agentic-dev-kit/pull/1169) (`e68871b`) and
  [#1179](https://github.com/topij/agentic-dev-kit/pull/1179) (`a00eeed`) shipped
  `scripts/review_eval.py` and its case set (#1156).
  [#1181](https://github.com/topij/agentic-dev-kit/pull/1181) (`a72034b`) scores a
  verifier stage over reused lens reports.
  [#1183](https://github.com/topij/agentic-dev-kit/pull/1183) (`901daad`) declares
  `review.fallback_panel.verifier_compute` for #1155.
- **Decided:** the operator chose the cheap tier for the verifier and kept the key
  optional until measured. The verifier comparison on #1156 found no run that refuted
  a hit; the case set is too small to rank tiers. The operator ran the Codex verifier
  locally, because a cloud session has no Codex.
- **Review proportionality:**
  [#1167](https://github.com/topij/agentic-dev-kit/pull/1167) (`4248942`) refuses a
  `--last-reviewed` sha that is not on the branch past its fork point (#1166).
- Each PR body names its `make test` run; failures known to come from the cloud sandbox
  were left to CI. This session filed #1180, #1182
  and #1184 for review findings it left open. Its workstream assignment was not
  confirmed by the operator.

______________________________________________________________________

## Session — 2026-10-21 (changelog lookup and record-prose report limits)

- **Changelog fragments:** [#1147](https://github.com/topij/agentic-dev-kit/pull/1147)
  merged as `f98cc100a9527fcc0f908e89683d11ec5556ca0a`. It pins the lookup's baseline
  range and pathspec and aligns fragment naming guidance with the malformed-path warning.
- **Record-prose report limits:** [#1146](https://github.com/topij/agentic-dev-kit/pull/1146)
  merged as `f1999dfb56db0bd38624feb72bd5f228adc3c401`. The report prints the declared
  move bounds; the existing boundary tests assert the emitted wording.
  This workstream assignment was not confirmed by the operator.
- The PR bodies retain the `make test` commands, revisions, directories, dates and
  terminal output; their review dispositions retain the independent checks and limits.
  Headless-lane verification was interrupted; the cockpit took over at the unchanged heads.
- Tracker disposition and workstream closure remain operator decisions. The friction
  inbox records the recurring verification timeout; no tracker write was made.

______________________________________________________________________

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
- Evidence availability: `test -e` at `0b6db571544eca5ecda299cc5c821aefad62e5ec`,
  in `/private/tmp/agentic-dev-kit-triage-20261020-7858b019`, on 2026-10-20 found
  `/private/tmp/devkit-overnight-20261014-01a13bcb/` absent, including its
  `reviews/review-1108-ownership.log` and `reviews/review-1108-ownership-amended.log`.
  The dated 2026-10-15 TRI-11 source is archived verbatim and included in
  [#1137](https://github.com/topij/agentic-dev-kit/issues/1137); its location wording
  is historical. That ticket's acceptance audit needs another retained source or an
  explicit unavailable-input result. The
  [availability correction](https://github.com/topij/agentic-dev-kit/pull/1141#issuecomment-6289423693)
  records the distinction without changing the approved source or payload.
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
#1167 (`4248942`) refuses a `--last-reviewed` sha outside the branch (#1166).
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
#1034 (`79d33fb9`) preserves unquoted alternate path whitespace and filesystem bytes (#1032). #996 holds the unpinned
guards, wording, and the `.git`-gone exit 2, including the CLI-help follow-up from
#1122. #1122 (`dd089388`) shipped #900: allocated review rounds, prompt enforcement,
explicit retirement and disk/scratch reporting. Retirement retains Git-dependency
protections; #1130 (`d2f40206`) delivered #1127's dependency refresh at retirement time.
#1134 (`b739bc46`) delivered empty-marker handling. #1186 (`0b5d226e`) retires
fixture git dirs in a receipt-owned round (#997, narrowed to rounds); unowned entries
still keep them (#1185). #1189 holds #1186's residual LOWs.
`state/review-evidence/` retention remains scoped to #861.
**Owner:** [#900](https://github.com/topij/agentic-dev-kit/issues/900),
[#997](https://github.com/topij/agentic-dev-kit/issues/997),
[#1185](https://github.com/topij/agentic-dev-kit/issues/1185),
[#1188](https://github.com/topij/agentic-dev-kit/issues/1188),
[#1189](https://github.com/topij/agentic-dev-kit/issues/1189),
[#996](https://github.com/topij/agentic-dev-kit/issues/996),
[#861](https://github.com/topij/agentic-dev-kit/issues/861),
[#895](https://github.com/topij/agentic-dev-kit/issues/895).

▶ Next: #1188 — make `scripts/tests/test_sweep_scratch.py` remove each test's
temporary tree at teardown, so a round whose only pins are that module's fixtures
retires. That does not clear the fixtures already in the kept round `review-72a279dd…`
(receipt in the main checkout's ignored `state/review-rounds/`); removing that round is
the operator's call. #1185 carries the unowned-entry case.

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

### Reviewer measurement

**Status:** #1168 (`e0b6a7b`) tallies reviewer precision from fallback-panel
dispositions. #1169 (`e68871b`), #1179 (`a00eeed`) and #1181 (`a72034b`) ship
`scripts/review_eval.py`, which scores lens and verifier changes against known-bug and
clean cases. #1183 (`901daad`) declares the optional verifier compute key. The
comparison runs are recorded on #1156; making the lens panel the primary reviewer
is #1159. **Owner:** [#1156](https://github.com/topij/agentic-dev-kit/issues/1156),
[#1159](https://github.com/topij/agentic-dev-kit/issues/1159); follow-ups
[#1180](https://github.com/topij/agentic-dev-kit/issues/1180),
[#1182](https://github.com/topij/agentic-dev-kit/issues/1182),
[#1184](https://github.com/topij/agentic-dev-kit/issues/1184).

▶ Next: #1156 — judge the clean-case findings every verifier confirmed (real defect
or false alarm) and grow the case set before ranking verifier tiers.

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
