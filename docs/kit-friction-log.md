# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **What lands here is what is not yet issue-shaped.** A finding that already carries a
> reproduction, a named mechanism and a proposed fix is filed straight to the tracker by
> `wrap-up`'s friction-routing step, on the operator's go-ahead, rather than parked here
> — and parks here anyway when that route is unavailable — which is the routing Principle #2 prescribes,
> not a neglected inbox. What stays is the remainder: findings still missing one of those
> three, and single instances of a shape that only matters if it recurs.
>
> **Position alone does not tell you what is un-graduated, and this file does not
> pretend otherwise** ([`#224`](https://github.com/topij/agentic-dev-kit/issues/224)).
> New entries are appended at the *top*, so the dated sections above the most recent
> `## … — Backlog migrated` marker are un-graduated. But a sweep does not archive
> everything it passes over: an entry added *between* a triage run's draft and its
> finalize is recognised as new and deliberately **kept in this file, below the new
> marker**, ready for the next pass rather than archived unfiled. So the un-graduated
> set is everything above the newest marker **plus anything kept below it**, and a
> dated section below a marker is that safety mechanism working — not a straggler.
> Each marker's own block records what it swept.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-09-26 — Backlog migrated by triage session 61ed6f6076da48678d921e9dec6fa7e4

Engine mode: `engine-backed`.

Filed: [#814](https://github.com/topij/agentic-dev-kit/issues/814), [#815](https://github.com/topij/agentic-dev-kit/issues/815), [#816](https://github.com/topij/agentic-dev-kit/issues/816).

Approval command: `approve TRI-01 TRI-02 TRI-04`. Approver: `topij`.

## 2026-09-25 — Backlog migrated by triage session 68e767ab2a9a400798b79cf780b3070e

Engine-backed (`engine-verified`) sweep, merged as #805. The engine writes no record
under its marker (#806), so this block was written in the session's wrap-up.

**Archived without filing,** on the operator's in-session command `archive TRI-05 TRI-06
TRI-12 TRI-13 TRI-14 TRI-15 TRI-16 TRI-18 TRI-19 TRI-20 TRI-21 TRI-22 TRI-23 TRI-24
TRI-25 TRI-28`. Each swept entry already had a home:

- on the tracker: #783, #776, #574, #719, #720, #578 (two entries), #721, #393, #561,
  #712 (two entries), #713;
- the bash 3.2 heredoc entry and the `#666` ordering entry were recorded knowledge, with
  no fix owed;
- the eight-panel-rounds entry had already graduated to `AGENTS.md`'s *Prose that goes
  false*.

**Kept active below:** every other entry, parked by default. That includes the
2026-08-27 `claude -p --output-format json` and `panel_prompt.py` entries, whose source
bytes are unchanged since the 2026-09-06 park.

**Degraded:** the notification thread. Approval was in the current session, which the
interactive route permits.

## 2026-09-25 — Backlog migrated by triage session a382ee5c31814a2390cce79eeee5a903

Engine-backed (`engine-verified`) sweep, merged as #803. This session's marker was
deleted by the next sweep's empty-section removal (#806), so the wrap-up restored it
with this record.

**Graduated:** [#802](https://github.com/topij/agentic-dev-kit/issues/802), from the
2026-09-24 `codex exec` trust-entry entry, on the operator's in-session command
`approve TRI-05`. The create's first read-back came back empty because the issue list
lagged (#808). A resume then verified #802 by its exact marker, with no duplicate.

**Before this session,** the 2026-09-06 LLM-only session's state was retired through
`recover`'s `retire-terminal-invalid-state` (#801), on the operator's approval of the
exact action digest. Its bytes are kept under `state/triage/`.

## 2026-09-24

- **The first two fallback-panel rounds on #790 each found another unpinned fail-closed
  clause.** #790 added normative prose to `post-merge-systemize.md` and pinned part of it
  in `_assert_post_merge_semantics`. The adversarial lens at `2b9dae8` and again at
  `ae54d68` proved, by a surviving mutant, that another guarding clause was not pinned.
  Only at `d873b68`, after every fail-closed clause in the section was pinned with an
  inverting mutation, did a round find no unpinned clause.
  - **Why it is parked:** it is one instance, and the point is whether it recurs. If it
    does, a candidate rule is that a change adding normative workflow prose pins every
    fail-closed clause in the first commit, not only the ones the author considers
    central.
  - **Not established:** whether the partial first pinning was an authoring slip or
    something the panel doctrine could prompt.
  - **Severity:** L. Each round cost a full panel, and no defect shipped.

## 2026-09-13

- **The panel path test overstates which declaration it protects.** The independent
  correctness review at fixture `12d7d4b41abe75451ed74d7cbc068bc6b8be2db7` on
  2026-09-12 UTC classified this as **L / P3 coverage-claim imprecision**, not a
  demonstrated production regression. `test_the_declared_path_matches_the_doctrine_path`
  compares `DOCTRINE` to another literal, without observing the `require_kit_paths`
  argument in `doctrine_text()`. Changing that argument to a missing path left the
  assertion passing while dependent tests skipped in the selected panel/marker modules.
  The [execution record](../saved_plans/phase5-item5-b-pr02-execution_2026-09-13.md)
  binds the full local report and mutation/restoration evidence; complete-mutant-suite
  survival was not established. Proposed remedy: observe the actual declaration, or
  narrow the claim if that protection is deliberately out of scope.
  `gh search issues '"test_panel_prompt" "require_kit_paths"' --repo topij/agentic-dev-kit --limit 30 --json number,title,url,state`
  in `/Users/topi/Coding/agentic-dev-kit` at
  `083bccbfa4c4b066d82e7625ddf1efe70716dd2d` on 2026-09-13 local date returned
  `[]`; this bounded search does not prove no duplicate exists. Pending an exact
  scope decision: the approved continuation excludes additional fixture fixes and
  tracker payloads, and the operator requested autonomous finalization before sleep.
  No fix, tracker write or waiver is established by this entry; the sweep stays parked.

## 2026-09-11

- **Case-insensitive report paths overwrote a completed review report.** During
  PR #733's final adversarial review on 2026-09-11, the reviewer wrote `REPORT.md`
  while the launcher used `codex exec -o report.md` in the same scratch directory.
  Those names aliased on the filesystem, so the launcher's final-summary write
  replaced the full report. **L** — the complete reviewer-authored text remained
  in a completed command in `events.jsonl`; shell-token and Python-AST literal
  parsing recovered it without executing the command. The
  [complete receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5639699233)
  preserves that recovery before merge. Proposed remedy: give the reviewer report
  and launcher summary distinct basenames and check their destination identities
  before launching. This was session review orchestration, not an established kit
  engine defect. `gh search issues --repo topij/agentic-dev-kit` with queries
  `"case-insensitive" "report"` and `"REPORT.md"`, including PRs, at
  `fc46efa0570f866f19cccf11834f909d5f37cf69` on 2026-09-11 in
  `/Users/topi/Coding/agentic-dev-kit` returned no match for the combined query and
  PR matches for the filename query; no collision issue was identified by
  that bounded search. Parked because the operator excludes tracker payloads from
  this work. No tracker write or friction sweep is authorized by this entry.

- **The review runtime stopped before delivering required adversarial coverage.**
  PR #733's [receipt at `88c5b044d5a42e33d2c4b0158be0957b4014678a`](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633065607)
  and [receipt at `207683b073f4d34cf22c5d9e1635f1c23239b6d4`](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633204702)
  preserve the actual `codex exec` argv, private review directories, compute readback
  and terminal cybersecurity-content flags on 2026-09-11. **M** — required review
  could not reach a final report. The runtime supplied no classifier diagnosis;
  no kit mechanism or repair is established. Parked for runtime-access diagnosis,
  with the unfinished commands distinguished from completed verification. No
  tracker payload or sweep is authorized by this record, and incomplete coverage
  is not merge clearance.

## 2026-09-09

- **ITEM5-B exposed a drift-check applicability mismatch after #705.** The
  [approved execution](../saved_plans/phase5-item5-b-execution_2026-09-09.md) retains
  the installed runner's complete command, fixture/source SHAs, output and failure
  excerpts. **M** — `test_the_drift_test_actually_executes` requires its child never
  to skip, while #705 added `require_kit_source()` to that child so an adopter's
  recorded baseline intentionally skips it. Proposed repair: align the parent's
  applicability with the child and prove the liveness check still detects an improper
  skip in a kit source tree. The same execution retains config/adapter assumptions
  already represented on #534; neither class is #393. Searched the exact parent test
  name with `gh search issues` and read #534's body and comments on 2026-09-09 at
  `edc199f42bc65b1850172ea79b791ef358577ae1`; the search returned no matching item,
  while #534 supplies the cross-test and kit-only-invariant scope. Parked for an exact
  occurrence-payload decision because the operator went to sleep; no tracker write.

- **A review suite encountered undecodable process-list output.** PR #725's
  [initial receipt](https://github.com/topij/agentic-dev-kit/pull/725#issuecomment-5607994984)
  retains the adversarial lens's `make test` result and targeted retry at
  `edc199f42bc65b1850172ea79b791ef358577ae1` on 2026-09-09 in its independent scratch
  clone. **L** — the launcher raised `UnicodeDecodeError` while reading process-list
  output; the targeted retry passed, and the raw offending process bytes were not
  captured. Parked for accumulation rather than asserting a reproducible repair.
  Keep this environment-dependent observation separate from #393 and ITEM5-B's
  installed-test failures.

- **A following shell line committed after staged validation failed.** During this
  wrap-up, `git diff --cached --check` rejected trailing whitespace in a copied
  pytest log, but the following `git commit` still ran because the shell command
  did not stop on the Python validator's failure. **L** — the unpublished record
  was corrected; the log now declares its whitespace-only transformation. Keep
  dependent commit work in a later tool call after reading validation, as the
  wrap-up workflow already prescribes. Parked for accumulation; no tracker write.
  **Recurred during ITEM5-B on 2026-09-09:** the combined validation/commit command
  again continued after `git diff --cached --check` flagged raw transcript whitespace,
  producing `38af832b8d044a12866dcdfb0ab3346558b392a2`. Those raw bytes were retained;
  an explicit raw-log exclusion and separate authored-file check were read afterward.
  Subsequent commit work moved to a separate tool call. No new tracker write.

## 2026-09-06 — Backlog migrated to GitHub Issues (#693)

Swept in **LLM-only mode** because the configured draft and finalize engines are absent,
which is what selects it; every result here is **agent-executed**, not engine-verified.

**Graduated:** [#693](https://github.com/topij/agentic-dev-kit/issues/693), from the
2026-09-06 adopt-continuation entry, searched by its exact idempotency marker before
creation and re-read afterward for its approved title, body, project, labels, marker and
payload digest. The pre-create search returned nothing for this session's marker while
returning prior markers for a `triage-payload` control term, so the empty result was
meaningful rather than a search that never matches.

**Archived without filing:** the 2026-09-01 entry and its 2026-09-02 recurrence, on the
operator's explicit `archive` decision. The 2026-09-02 recurrence is recorded with its
mechanism as an occurrence comment on
[#393](https://github.com/topij/agentic-dev-kit/issues/393), which stays open. The
2026-09-01 entry is not separately on the tracker — that comment refers to it only as
the hypothesis the recurrence did not survive — so its verbatim copy in
`kit-friction-log-archive.md` is the only record of its own revision and run. The
2026-09-03 sweep kept both pending exactly this decision.

**Kept active below this marker:** the `claude -p --output-format json` and
`panel_prompt.py` entries (2026-08-27) and the eight-panel-rounds entry (2026-08-22),
parked for accumulation. **Still reserved:** the `#608` and `#255` dispositions, carried
here from the swept 2026-09-06 entry's own trailer.

**Candidate ids are not the 2026-09-03 run's.** This run's `TRI-04`, `TRI-05` and
`TRI-06` are that run's `TRI-03`, `TRI-04` and `TRI-05`, each pair confirmed by an
identical source-block digest.

**Approval.** The exact payloads were presented in the current Claude Code session; the
DM path was not exercised, which the interactive route permits. The operator replied on
2026-09-06 — `approve TRI-01, archive TRI-02 TRI-03, park TRI-04 TRI-05 TRI-06` —
superseding an earlier `approve all`. This block is the committed approval record
[#128](https://github.com/topij/agentic-dev-kit/issues/128) asks the interactive path to
carry, since `state/` and `reports/` are gitignored.

**Frozen inbox.** `shasum -a 256
state/triage/frozen-inbox_live_2026-09-06_triage-548121b9fa18444808d6b2482aac91d3.json` in
`/Users/topi/Coding/agentic-dev-kit` at `4989efd4cbc09c0a81f8d5e3259f0430ff69484b` on 2026-09-06
printed `5dfbd96911df6e92a7272a6b4977853ea548eb81c2b51de4df2566fc1084b297`. Finalization
re-read the active inbox and admitted only the byte-identical frozen blocks for
`TRI-01`, `TRI-02` and `TRI-03`.

## 2026-09-03 — Backlog migrated to GitHub Issues (#671–#672)

Swept in **LLM-only mode** because the configured draft and finalize engines are absent;
the results are **agent-executed**, not engine-verified. Graduated:
[#671](https://github.com/topij/agentic-dev-kit/issues/671) and
[#672](https://github.com/topij/agentic-dev-kit/issues/672). Each issue was searched by
its exact idempotency marker before creation and re-read afterward for its approved
title, body, project, labels, marker, and payload digest.

**Kept active below this marker:** `TRI-03`, `TRI-04`, and `TRI-05`, exactly as the
operator decided. The 2026-09-01 entry and its recurrence are already recorded on
[#393](https://github.com/topij/agentic-dev-kit/issues/393); they were excluded from the
proposal set and remain byte-identical below rather than being swept without an explicit
archive decision. Content added after the frozen draft also remains active verbatim.

**Approval.** The exact payloads were presented in the current Codex session. The
operator replied on 2026-09-03: `approve TRI-01 TRI-02` and `park TRI-03 TRI-04 TRI-05`.

**Frozen inbox.** `shasum -a 256
state/triage/frozen-inbox_live_2026-09-03_triage-1565b7bfdf11475f9a92f06002f463d4.json`
at `e78c215c9bd1bd3e007a7d3c9753b2013e5a8221` on 2026-09-03 printed
`03de6ef926e190a5800b939ee652c7c9607be58f3e95362ece4365ac3bc6ebef`. Finalization
re-read the active inbox and admitted only the byte-identical frozen blocks for
`TRI-01` and `TRI-02` to this sweep.

## 2026-08-29 — Backlog migrated to GitHub Issues (#641–#645)

Swept in **LLM-only mode**: both engines named by `triage.draft_engine` and
`triage.finalize_engine` are absent, which is what selects it, and vendoring them is
[#6](https://github.com/topij/agentic-dev-kit/issues/6). Every result here is **agent-executed**, not engine-verified.

**Every block present at draft time is accounted for.** Graduated: [#641](https://github.com/topij/agentic-dev-kit/issues/641),
[#642](https://github.com/topij/agentic-dev-kit/issues/642), [#643](https://github.com/topij/agentic-dev-kit/issues/643) (the cause behind [#570](https://github.com/topij/agentic-dev-kit/issues/570)'s symptom),
[#644](https://github.com/topij/agentic-dev-kit/issues/644), [#645](https://github.com/topij/agentic-dev-kit/issues/645). Archived without filing: the `#428`-guard entry dated
2026-08-27, whose own text records the occurrence on [#467](https://github.com/topij/agentic-dev-kit/issues/467). Each create was re-read
from the tracker after landing per `#138` — state, title, body **and labels** — against its
approved payload digest and its idempotency marker.

**Kept active below this marker, deliberately not swept:** the `claude -p --output-format
json` multi-value entry and the `panel_prompt.py` empty-render entry (both 2026-08-27, single
instances, no mechanism identified), and the eight-panel-rounds entry (2026-08-22, parked on
both park conditions). This is [#575](https://github.com/topij/agentic-dev-kit/issues/575)'s *skipped* versus *parked* distinction, and
why [#224](https://github.com/topij/agentic-dev-kit/issues/224) says position alone does not tell you what is un-graduated: each waits
for a recurrence an archived entry never reaches.

**Approval.** The numbered proposal list went to the operator **in-session, not by DM** (the
notification path degraded to the current session, which the interactive route permits); the
decision came back the same session on 2026-08-29: `approve TRI-01 TRI-02 TRI-03 TRI-04
TRI-05`, `archive TRI-07`, `park TRI-06 TRI-08 TRI-09`. This block is the committed approval
record [#128](https://github.com/topij/agentic-dev-kit/issues/128) asks the interactive path to carry, since `state/` and `reports/` are
gitignored.

**Frozen inbox:** sha256 `e6e8ca7ba2ca523b2372dce9dfa6e52af845ffec4f9ec1cf5ec332f21081ce92`, from
`shasum -a 256 docs/kit-friction-log.md` at `9c7e130` on 2026-08-29; re-read at finalize and
required to match before the rewrite, every swept block byte-identical to its frozen block.
Swept entries are verbatim in the archive under `Graduated 2026-08-29`.

## 2026-08-27

- **`claude -p --output-format json` printed more than one JSON value on stdout in
  three of five cockpit probe invocations at 2.1.247, and one value on a repeat of the
  same invocation.** The wrapper terminalizes that shape `failed` (a single result is
  what the digest binds), so the outcome was fail-closed each time; the record in
  `saved_plans/claude-writing-lane-live-validation_2026-08-27.md` carries the
  occurrences. **L** — no mechanism identified, and the cockpit could not make it
  recur on demand; parked for accumulation. If it recurs, keep the raw stdout bytes
  and the stderr beside them before re-running.

- **`panel_prompt.py` produced an empty prompt file and hung until the tool timeout,
  then rendered in about a second on an identical re-run.** In a shell `for` loop that
  created a detached lens worktree and immediately rendered the lens prompt into it
  (`git worktree add --detach … && uv run scripts/panel_prompt.py --lens … > prompt.md`),
  the first render wrote nothing and did not return within the tool's timeout; the
  same invocation re-run alone with a bounded subprocess timeout returned in about one
  second with a complete prompt. A full `make test` was running in the background at
  the time. **L** — no mechanism identified (contention on the shared `.git` from the
  concurrent suite and the fresh worktree is a guess, not an observation), single
  instance; parked for accumulation. If it recurs, capture `panel_prompt.py`'s stderr
  and the worktree lock state before re-running.

## 2026-08-22 — Backlog migrated to GitHub Issues (#566–#571)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Twelve
entries in, twelve accounted for:** six new issues
([#566](https://github.com/topij/agentic-dev-kit/issues/566)–[#571](https://github.com/topij/agentic-dev-kit/issues/571)),
five entries folded into occurrence comments on already-open issues carrying the same
mechanism — [#509](https://github.com/topij/agentic-dev-kit/issues/509),
[#514](https://github.com/topij/agentic-dev-kit/issues/514) (two entries in one
comment: the original delegate stall and its same-day recurrence with the fix applied
verbatim), [#511](https://github.com/topij/agentic-dev-kit/issues/511) and
[#246](https://github.com/topij/agentic-dev-kit/issues/246) (one entry split across
two, since its second half is a `gh`-cwd-resolution finding rather than a two-tree
one), and [#510](https://github.com/topij/agentic-dev-kit/issues/510) — and **one
entry deliberately kept in the active file**, below (the disposition question that
raises is [#575](https://github.com/topij/agentic-dev-kit/issues/575)). All six creates and all five
comments were re-read from the tracker after landing per `#138` — state, title, body and
**labels**. The first re-read checked everything but labels and so missed that the six
issues had been filed with none; a panel lens caught it against the previous sweep.
`gh api repos/topij/agentic-dev-kit/issues/{566..571}/timeline` on 2026-08-22 shows each
created with no label and labelled in one later batch, both before this marker's commit.

**One entry was kept rather than swept, which diverges from the engine's spec.**
`triage-friction-log.md` Step 5 sweeps every block present at draft time, *including
LLM-skipped ones*, so a vendored `finalize_triage.py` would have archived the
2026-08-22 entry. It is kept here on the operator's approval because its own text
parks it for **accumulation** — "if it recurs with a mechanism attached it is worth a
rule" — and an archived entry reaches no future triage pass, which is the one thing
that entry is waiting for. Skipped and parked are different dispositions and the spec
has one bucket for both; worth resolving before the engine lands, since the engine
will not reproduce this choice.

**Approval.** The numbered proposal list went to the operator **in-session, not by
DM**: the Slack MCP was unauthorized for this session and `scripts/` carries no notify
engine, so the workflow's load-bearing DM surface was unavailable. The two-session
draft→approve→finalize split exists because a *scheduled* run has no operator to ask;
one was present here, so the list was put directly in front of them and approval came
back in the same session at 2026-08-22 — "approve all" — the grammar's bulk approve.
Nothing was declined. This block is the committed approval record `#128` asks the
interactive path to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 14,451 bytes, sha256
`9d42521dfa8b287a49f60f33aca13ce9f185774a1562ad33c95161db2296b59b`, reproducing from
`git show 8efdc9d:docs/kit-friction-log.md | tail -n +28 | shasum -a 256`. Draft and
finalize ran in one session with no window between them, so no window-added entry
could exist; the digest was recomputed from the file being swept immediately before
the rewrite and matched.

Swept entries are verbatim in the archive under `Graduated 2026-08-22`.
