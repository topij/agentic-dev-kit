# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it on a pull request (`/wrap-up`'s handoff test) when the
> work left something to hand over. This file — not an agent's memory, not a scratch note — is the single
> source of truth for what is in progress and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> **Workstreams only.** Each open line of work keeps its own entry under
> **Workstreams** at the end of this file — a status line, an owner pointer and its own
> `▶ Next:` — until the operator closes it
> ([#762](https://github.com/topij/agentic-dev-kit/issues/762)). What shipped is not
> restated here: merged pull requests, commits and tracker issues record it, and
> `session-start` reads them first-hand. `wrap-up` edits this file only for what none
> of them holds, and writes no session entry.
>
> The dated session entries above Workstreams are from the earlier layout. They graduate
> to [`kit-handoff-history.md`](kit-handoff-history.md) through the archive sweep
> (`scripts/archive_plan_sessions.py`); the Workstreams section is never swept.

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
`pr_watch.py --record-review fallback:delta` refuses a disposition missing a named
lens's `prose-class:` or `safety-critical:` verdict line (#921, in PR #1248).
#1167 (`4248942`) refuses a `--last-reviewed` sha outside the branch (#1166).
**Owner:** [#585](https://github.com/topij/agentic-dev-kit/issues/585); related #403,
#666, #305, and the class's documented limits #928, #929, #930 and #931.

▶ Next: choose the next step with the operator from #585 and the documented limits
#928, #929, #930 and #931.

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
fixture git dirs in a receipt-owned round (#997, narrowed to rounds), and #1185 has the
age sweep judge them the same way in unowned entries; a nonempty `.git` file that does
not start with `gitdir:` still keeps an unowned entry. #1193 (`043f61f2`) delivered #1186's residual LOWs (#1189),
and #1192 (`5b50b225`) has `test_sweep_scratch.py` remove each test's tree at
teardown (#1188). Not established: that a round in which a lens probes `.git` files can be
retired; triage archived that question without filing on 2026-10-24.
`sweep_scratch.py --disk --json` in the primary checkout at `ef8e4780` on 2026-10-27 listed none of the rounds kept
on 2026-10-22 and 2026-10-23 (`review-72a279dd…` among them).
#1258 (`ef8e4780`) retires each review round of an open session-cleanup inventory
(`--round`) and has `allocate` refuse while an earlier round is unretired (#1254); its
round-3 LOWs are #1259. #1261 (`87a5f18b`) names the differing bound field in an
unavailable inventory's refusal and adds an approved `reconcile` for a changed device
number, under the preconditions in `session-cleanup.md`. It deletes nothing. Retained evidence is discarded by default and retires through
`session_cleanup.py retire-evidence` once #1316 merges (#1256, #1315);
the cross-inventory shared store and a seal byte budget from those tickets were left out of it as secondary. #1261's review LOWs are #1263. Copies outside every managed root, such as Codex lens trees under
`~/.codex/worktrees`, are invisible to the report (#1255); retained-evidence policy is
#1256. `state/review-evidence/` retention remains scoped to #861. #1267 (`cfb708db`) shipped #1253's binding of inventories
and receipts to a boot-stable identity. On 2026-10-28, from the primary checkout and with the operator's approval,
every device-renumbered inventory in this repository was reconciled. Inventory `8cf42b14` stayed incomplete: it
holds round `01234b40` (round 3 of #1262's review), which `session_cleanup.py preview --round` kept on
2026-10-27 for a worktree record whose path holds a newline, written inside the round by a `test_panel_prompt.py`
fixture (#1265). #1277 (`e372ba36`) released that record's keep, and `configured.git` fixture dirs still keep the
round (#1279). #1277's review rounds `5ced121b` and `e388daaa` are also kept on disk, in inventory `a5b9c398`, by lens
probe leftovers: a `.git` file whose `gitdir:` pointer spans lines, which `_linked_gitdir_reason` keeps on purpose and
no open ticket covers yet, and a `configured.git` dir (#1279).
**Owner:** [#997](https://github.com/topij/agentic-dev-kit/issues/997),
[#996](https://github.com/topij/agentic-dev-kit/issues/996),
[#861](https://github.com/topij/agentic-dev-kit/issues/861),
[#895](https://github.com/topij/agentic-dev-kit/issues/895),
[#1255](https://github.com/topij/agentic-dev-kit/issues/1255),
[#1256](https://github.com/topij/agentic-dev-kit/issues/1256),
[#1259](https://github.com/topij/agentic-dev-kit/issues/1259),
[#1263](https://github.com/topij/agentic-dev-kit/issues/1263),
[#1279](https://github.com/topij/agentic-dev-kit/issues/1279),
[#1280](https://github.com/topij/agentic-dev-kit/issues/1280).

▶ Next: #1279 — clear `test_panel_prompt.py`'s `configured.git` keeper. Then preview rounds `01234b40`, `5ced121b`
and `e388daaa` with `session_cleanup.py preview --round`, and retire each one it reports eligible, with the operator's
approval. Round `5ced121b` stays kept for its multi-line `.git` pointer until a change, not yet ticketed, releases it.
Separately, once #1316 merges: decide with the operator whether #1256's seal byte budget and #1315's shared store are
still wanted, and take #1307, then #1312, one PR each: the operator set that order on 2026-10-31. #1278 is in the
pull request on branch `feat/absent-round-root`.

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

**Status:** #978 and its cs-toolkit installation removed the one-run recovery paths. The last
shape check in `model.py`, kept so that cs-toolkit's completed LIVE state with a
`proposal_correction` receipt could still retire, is removed by #1305's change. The
evidence that no state root holds the field is cs-toolkit's report of 2026-10-29, recorded
on #1305: the state retired and the retired file was deleted with the operator's
approval. It covers the operator's machine only. A state that still carries the field
is now held as `operator-held`.

**Owner:** [#979](https://github.com/topij/agentic-dev-kit/issues/979),
[#1305](https://github.com/topij/agentic-dev-kit/issues/1305).

▶ Next: once #1305's pull request merges, the operator decides whether this workstream ends.

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
[#1058](https://github.com/topij/agentic-dev-kit/issues/1058).

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
An adopter's real scheduled runs on 2026-10-23 each wrote a receipt that its wrapper re-checked against the expected
invocation, as read on 2026-10-27 (sources in `saved_plans/adopter-upgrade-prep_2026-10-27.md`). Neither run reached
completed-state retirement; see *Triage one-run cleanup*.
**Owner:** [#1116](https://github.com/topij/agentic-dev-kit/issues/1116).

▶ Next: verify the documented trusted launcher boundary for the adopter's scheduled calls.

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
[#1159](https://github.com/topij/agentic-dev-kit/issues/1159). #1191 (`433de2ab`)
delivered #1182.

▶ Next: #1156 — judge the clean-case findings every verifier confirmed (real defect
or false alarm) and grow the case set before ranking verifier tiers.

### Parallel lanes

**Status:** the 2026-10-24 review of the parallel-lane capabilities
(https://claude.ai/artifact/XqWRnuWfgwxTry4k8ZoXoL) ranked the proposals. #1235
(`c37e47b7`) made lane state visible and applied compute tiers; #1236 (`1213e980`) added
the `LANE-TERMINAL:` line and bounded resume; #1237 (`035c07c8`) prescribed file-based
lane messages, granted `git restore` and added `launch_lane.py --ticket`. Operator
decisions on 2026-10-25 that no single PR holds: a resume continues the bound launch
with no new descriptor; `parallel.max_resumes` ships as 1; the lane profile grants
neither `gh pr edit` nor `gh pr comment`; `--ticket` stays. Whether #514, #564, #1011,
#628 and #271 are done is the operator's call. Probed at Claude Code 2.1.310 with the
shipped profile under `dontAsk` (stamped in `parallel-headless.md`), compounds of profile-allowed
`git` commands ran and a chain with a refused part was denied whole; the runtime's
read-only class that #628's 2.1.250 denials concern was not re-probed. #1241 took
the first-launch blockers on routes the operator chose on 2026-10-25: a
lane is held to its repository by Git common directory, so a linked worktree can issue
one (#1109); a user-local runtime install is placed on the trusted path by the host,
and the overlay still refuses `parallel.<runtime>_headless_command` (#629);
`dev_session.sh <subcommand> --help` is side-effect free, which is only part of #454.
Proposals not yet taken: a
documented cloud-session lane route, and standing mandates (#472, which the review
sequences after a terminal state and a cost record). Still open from #1235: #1173's
default tier and a tier carried in the descriptor, and #1174's ranking report and
per-lane budget.
**Owner:** [#1239](https://github.com/topij/agentic-dev-kit/issues/1239),
[#1174](https://github.com/topij/agentic-dev-kit/issues/1174),
[#1173](https://github.com/topij/agentic-dev-kit/issues/1173),
[#1242](https://github.com/topij/agentic-dev-kit/issues/1242),
[#1243](https://github.com/topij/agentic-dev-kit/issues/1243),
[#454](https://github.com/topij/agentic-dev-kit/issues/454),
[#472](https://github.com/topij/agentic-dev-kit/issues/472); the review document above
(a claude.ai link, not in the repository).

▶ Next: choose the next proposal with the operator: the documented cloud-session lane
route, #472's standing mandates, or #454's remainder (capability negotiation in the
shared workflow for an adopter-retained engine, an extension contract for adopter
state environment and destructive-path guards, the partial-adopter fixture, and a
Codex launch through such an engine). Smaller follow-ups: #1239, and #1242 together
with #1243's items in one PR, so the safety-critical panel runs once.

### Consumer upgrades

**Status:** a read-only upgrade-prep pass for the private adopter, from its installed kit `cd41724b` to `2a8fbb96`,
ran on 2026-10-27. Its notes are local and untracked: `saved_plans/adopter-upgrade-prep_2026-10-27.md`. The
adopter-specific next steps are in its own tracker. cs-toolkit then installed kit `31b7c84f`
(in-parallel-oy/cs-toolkit#2981, 2026-10-27). The operator reported on 2026-10-28 that its cleanup inventories were
reconciled and that `recover` quarantined its stale LIVE triage gate on 2026-10-27. A read-only probe in cs-toolkit's
primary checkout on 2026-10-28, with its installed engine at kit `31b7c84f`, found no LIVE gate, and its completed
LIVE state failing `canonical_state` on its configuration fingerprint (not #1111's repository identity) but passing
`validate_session_state(..., retiring=True)`. That implies, without having been run, that a session-starting entry
there retires it. Its `state-present-held` bundle `6d1168cb…` is keyed to the quarantined gate's digest, so it blocks
nothing while no gate is present. The
scheduled-run findings are under *Triage one-run cleanup*. Separate
adopter decisions: unattended notification delivery, and OpenKitchen's installation and lane prerequisites, to
reassess before an upgrade there. The earlier local assessment, `saved_plans/consumer-upgrade-assessment_2026-10-15.md`, predates
these upgrades. cs-toolkit later installed kit `814b01da` (in-parallel-oy/cs-toolkit#3014, merged 2026-10-29), which
contains `dd51941b`, and dropped CodeRabbit as a configured reviewer (in-parallel-oy/cs-toolkit#3020, merged
2026-10-30). Its vendored PR follow-up hook still words the fallback review as conditional on a bot outage until it
installs #1301.
**Owner:** #1116, #990, #1011, #979, #1282.

▶ Next: cs-toolkit reported on 2026-10-29 that its completed LIVE state had retired (see *Triage one-run cleanup*), so removing the shim (#1305) owes cs-toolkit nothing more. Separately, upgrade cs-toolkit to a kit at or after `e68010213` (#1301: the hook's no-bot wording and the empty `review.bots` default; its config already names no bot, so the changelog's BREAKING entries need no config change there) following `upgrade.md`.
