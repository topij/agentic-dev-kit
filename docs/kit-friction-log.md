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

## 2026-09-03

- **A review lens that backgrounds a long verification loses its entire report, and the
  failure presents as silence.** A panel lens on PR `#668` started `make test` in the
  background and its turn ended while waiting; it returned no report at all, twice in a
  row, each time saying only that it was waiting. To the cockpit reading agent output,
  no-report is indistinguishable from a clean pass — the same shape as a bot outage read
  as an approval. It was recovered by resuming the agent with an explicit prohibition on
  blocking, after which it reported normally and disclosed the suite run as incomplete.
  **M** — reproduction and mechanism are both clear, and the remedy is one line in the
  lens prompt (`panel_prompt.py` could carry it, since every lens gets that contract),
  so this is issue-shaped rather than inbox-shaped. Parked here only because it arose in
  an unattended session with no route to exact-payload approval; it should be filed
  rather than accumulated.

- **A mutation that silently fails to apply reads as a clean kill.** While pinning
  `#667`'s stdin branch, the cockpit's first mutation anchored on text that a comment
  block interrupted, so the edit never landed and the suite reported `304 passed` against
  unmutated code. Taken at face value that is a survivor read as a kill, in the direction
  that matters. Caught by asserting the byte actually changed before trusting the run,
  which is the practice `#33` and `#112` already argue for from the false-kill side.
  **S** — a known class seen from a new angle (the mutation not applying, rather than the
  drift check over-killing); recorded as an occurrence rather than as a new defect.

## 2026-09-01

- **Two fallback-panel lenses each running the full suite concurrently produced a
  failure neither reproduces alone.** Both lenses' `make test` runs at
  `da142620a02d16d31e3231249d627b8fd194daa9` on 2026-09-01 failed
  `scripts/tests/test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`,
  a file outside the reviewed diff, and both saw it pass standalone; the adversarial
  lens saw the same failure at the base revision. The cockpit's own quiet-tree run at
  the same head printed `2374 passed in 514.92s (0:08:34)` with nothing failing. One
  lens reported `pytest-of-topi` tmp-dir cleanup races and two concurrent `make test`
  process chains in the same window. **M** — the correlation with concurrency is
  strong, but no mechanism is identified and a shared tmp-dir root is a guess rather
  than an observation. Parked for accumulation: this is `#623`'s quiet-tree class seen
  from the lens side rather than the cockpit's, and it recurs whenever a panel asks
  both lenses to verify. If it recurs, keep both lenses' full pytest output and their
  tmp-dir paths before re-running.

- **Recurrence 2026-09-02 — the concurrency hypothesis above did not survive it.** The
  same test failed twice in a row in
  `/Users/topi/Coding/agentic-dev-kit` at
  `679b197efc24e31a66e94f6d52b6b3e5f2a47855`, on a quiet tree with nothing running
  alongside either run, and passed standalone after each. The second run retained full
  output: the assertion that fails is `out == ""`, not the exit code, so the hook
  emitted its lifecycle warning because `json.load` **succeeded** inside the suite.
  Probed in the suite's own interpreter (Python 3.14.7), `json.loads` on the test's
  exact input raises `RecursionError: Stack overflow (used 8144 kB)` — the precondition
  holds in isolation and not in the suite, which is `#393`'s shape rather than a
  tmp-dir race. `test_init_sh.py:5100` already names `#393` and measures its own
  precondition for this reason; this sibling asserts it instead. The `pytest-of-topi`
  `garbage-*` cleanup warnings appear in both runs and are unrelated to the assertion
  that fails. **This is now issue-shaped** — reproduction, mechanism and a named sibling
  guard — and belongs on the tracker rather than here.

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

## 2026-08-22

- **Across eight panel rounds on two docs-only PRs, every finding was in a claim *about* the
  work rather than in the work.** Severity **M**. `#548` ran six rounds and `#553` two; the
  code, the 500-line doc move and the new guards came back clean under mutation every time a
  lens tried them — content parity re-derived twice by reverse-substituting placeholders, both
  registration guards killed by real set-equality assertions, four live `kit_doctor` scenarios.
  What kept being wrong was the prose beside them: a checkpoint that claimed to be the same as
  `triage-friction-log`'s and was weaker, a `kit_doctor` state named `missing` that is
  `new-upstream`, a refresh forecast inverted against `upgrade.md:613`, a positional invariant
  that `finalize_triage.py`'s keep-window breaks, an up-route attributed to a pass with no
  recurrence step. **Parked rather than filed, deliberately, on both park conditions:** there is
  no named mechanism — "authors overstate" is a description, not a cause — and the point is
  accumulation. One session cannot tell whether this is a property of docs-heavy PRs, of this
  author, or of a panel that has more purchase on prose than on tested code. If it recurs with
  a mechanism attached it is worth a rule; the shape to watch is whether a claim verified
  against a *command* ever failed, versus one verified against nothing.
