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

## 2026-09-07

- **`make test` fails on `main` in a way CI cannot see, and not always on the same test.**
  `make test` at `4b56d3eec285781ac382e0b897d5d1da9c7fe40e` (clean `main`) on 2026-09-07
  printed `1 failed, 2445 passed, 1 skipped in 379.54s`, failing
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`. It
  passes in isolation every time. Four review lenses measured it independently across the
  session: one got a *different* single failure
  (`test_reconcile_sessions.py::test_portable_bounded_runner_reaps_on_startup_interrupt`)
  from base-content files under concurrent load, and another got no failure at all on a
  repeat run at an identical sha. `uv run python -c "import sys; print(sys.version)"` in
  `/Users/topi/Coding/agentic-dev-kit` on 2026-09-07 printed `3.14.7`, while
  `.github/workflows/test.yml` pins `python-version: "3.12"`. `#393` records that `json`'s
  `RecursionError` behaviour changes at 3.14 and names a *different* test. **M** — the
  interpreter split is a candidate contributor, not an established mechanism, and the
  non-determinism is unexplained. Route to `#393` as a second occurrence, or file
  separately if it is judged distinct. Worth recording either way: a red local suite that
  CI reports green trains a session to discount its own verification command.

- **A genuinely unparseable `scripts/hooks/pre-push` passed `make test`.** `check-syntax`
  hands four filenames to one `bash -n`, and `pre-push` is last on that line, so it is
  never parsed — locally or in CI. Measured on 2026-09-07: `bash -n good.sh bad.sh` exits
  0 with a syntactically broken `bad.sh`, while `bash -n bad.sh` alone exits 2. `#561`
  already names the mechanism; what this adds is the blast radius — the hook runs on every
  push here and in every adopter, so a broken one ships through a green suite. `#709`
  closes the hole for that one file with `test_the_hook_parses_on_its_own`. **M** —
  `#561` remains the general fix and is worth raising in priority on this evidence.

- **The parse failure itself: bash 3.2 mis-parses an apostrophe inside a quoted heredoc
  within `$( )`.** Reproduced minimally on `GNU bash, version 3.2.57(1)-release
  (arm64-apple-darwin25)` — macOS's default, and what `#!/usr/bin/env bash` selects there
  — where a `$(python3 - <<'PY' … PY )` block whose body contains one apostrophe in a
  *Python comment* fails with ``unexpected EOF while looking for matching `'``. The
  existing config-read block in the same file has always avoided apostrophes, which now
  reads as deliberate but was nowhere stated. **L** — single instance, mechanism
  identified and commented in place; recorded because the failure presents as a broken
  heredoc rather than as a quoting rule.

- **`cp -a` of a linked git worktree does not isolate it, and the panel contract does not
  say so.** A review lens built its mutation scratch that way; the copied `.git` is a
  *pointer file* naming the same per-worktree admin directory, so `git stash` and
  `git checkout` run in the "copy" wrote the given tree's index. File contents were never
  altered, the lens detected and repaired it, and the cockpit independently confirmed the
  tree clean, index empty, HEAD unmoved and both changed files hash-matching the manifest.
  **M** — proposed fix: *No writes in the tree you were given* should name the mechanism,
  because the rule as written ("use an absolute path outside the given tree") is satisfied
  by the very command that breaks it. Six later lens launches stated the hazard inline and
  none recurred, so the carrier is the gap rather than the wording — the same shape as
  `#469`.

- **Lenses end their turn on a progress update while a background `make test` runs.** Four
  occurrences on 2026-09-07 across three PRs, each needing a `SendMessage` resume to
  produce a terminal report, and one lens lost its run entirely by piping it through `tail`
  and stopping early. *Execute, don't only read* already says a progress update is not a
  report, and two of the four had that sentence quoted in their prompt. **M** — no
  mechanism identified beyond "the instruction is present and does not bind"; proposed
  direction is the same as `#469`'s, a carrier change rather than a wording one. Parked
  for accumulation; if it recurs, capture whether the lens had a foreground alternative.

- **`panel_prompt.py` rendered a stale base, and only the lens contract caught it.** The
  `#711` round was assembled after `#709` merged, and its prompts named
  `ec750753eff1a645c64163b61a2b511e3adf71d4` as the base — one commit behind
  `origin/main`, then at `6f2cc2470c62ca4aa16793e0e20252341ba48b24`. Diffing against it
  attributed `#709`'s already-merged hook, tests and manifest to `#711`, which is a large,
  non-empty, wrong diff — the exact shape *Right revision* warns satisfies every other
  check. Both lenses independently detected it against the remote, re-derived the correct
  three-file diff, and said so in their reports before reviewing. **M** — the contract
  worked and the mechanism did not. Proposed fix: `panel_prompt.py` should re-resolve the
  base at render time rather than at an earlier assembly step, or state the timestamp of
  the resolution it used so a stale one is visible in the prompt. Worth filing: the
  cockpit had no signal, and a lens that skipped the check would have reviewed the wrong
  diff and reported it clean.

- **`#666`'s ordering is enforced by the engine, and the recovery costs a full round.**
  Round 2 of `#708`'s panel was fixed before its receipt was recorded; the retroactive
  `pr_watch.py --record-review --head <round-2 sha>` then refused with `PR head changed
  during review … review the new head before recording evidence`. That is the guard
  working. **L** — no fix proposed and none obviously needed: the cost lands on the party
  that skipped the step. Recorded so the next session knows the receipt is not recoverable
  after the fact and plans the round accordingly.

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
