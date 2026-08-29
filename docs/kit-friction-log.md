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

## 2026-08-29

- **`scripts/launch_lane.py` refuses `Bash(:*)` from a lane profile on the rule's
  shape, and the client grants nothing under that rule anyway.** Both `#639` lenses
  reached this independently. The lane classifier asks whether a pattern is bounded;
  `kit_doctor` now asks what the client actually grants, and the two answers point the
  same way here — so the refusal costs an adopter a rule that was never dangerous.
  **L** — no proposed fix, and both lenses called it out of scope. Parked for
  accumulation: what matters is whether a shape-based classifier and a
  measured-behaviour one drift apart somewhere it *does* matter. `#631` is the nearest
  open item.
- **A review lens asserted a base-currency relationship its own command did not
  establish.** In `#639` round 3 the correctness lens wrote that the supplied base "is
  the tip of `origin/main`" when it was the PR branch's prior head; its check
  (`git log <base>..origin/main` empty) is satisfied by any descendant of `origin/main`.
  The conclusion it drew — base is current for this round — was right, and the
  adversarial lens established the same thing by the right route, so nothing rested on
  it. **M** — the panel contract asks a lens to say *how* it established base currency
  precisely so a wrong route is visible, and here the wrong route reached a right
  answer, which is the case that would not be caught if the two lenses had agreed.
  Parked for accumulation.
- **`panel_prompt.py` renders a prompt to a FILE, but a Claude Code lens launch needs
  the text inline — so every round invites a hand transcription of the rendered
  values.** In one of five launches on `#637` the diffstat was retyped as `999
  insertions / 18 deletions` against the rendered `1000 / 16`. The correctness lens
  caught the mismatch and correctly declined to attribute it to a stale base or wrong
  sha. **M** — bounded, since both lenses verify base and sha independently, but the
  diffstat cross-check exists to flag a wrong diff and a mistyped baseline blunts it.
  No mechanism proposed: a launcher that reads the rendered file and a rendered form the
  launch consumes directly are different designs. Parked for accumulation.
- **A second intermittent test, found by a review lens rather than by the suite:
  `test_reconcile_sessions.py::test_portable_bounded_runner_reaps_on_startup_interrupt`.**
  Both PR `#638` lenses ran the pinned full suite in their own fresh clones and this
  test failed for one of them at `52d25e5` and at `5c5527c`, under `--python 3.12` and
  `--python 3.14` alike, while the cockpit's runs at the same revisions had it pass and
  four consecutive isolated runs of it passed here. **M** — no mechanism identified,
  and the environment split is the signal: not the interpreter, since it failed on
  both. Distinct from `#393`'s parser-recursion shape — a reaping test failing only in
  a fresh clone points at process timing or at something the clone does not carry.
  Parked for accumulation; what it already establishes is that the cockpit's count of
  this tree and a lens's count of the same tree disagreed about whether it was green.
- **A `cd` outlived its command twice in one session, both times in a throwaway probe
  rather than in two-tree work.** A symlink-behaviour probe and a permission-rule probe
  each left the shell in a scratch directory; the next edit using a repository-relative
  path failed with `FileNotFoundError`. **L** — failed loudly both times, no damage. `AGENTS.md`'s *Working across two
  trees* documents this for verification clones and adopter checkouts, neither of which
  is where these happened; what accumulates is whether the rule belongs on any
  `cd`-bearing command.

## 2026-08-27

- **`claude -p --output-format json` printed more than one JSON value on stdout in
  three of five cockpit probe invocations at 2.1.247, and one value on a repeat of the
  same invocation.** The wrapper terminalizes that shape `failed` (a single result is
  what the digest binds), so the outcome was fail-closed each time; the record in
  `saved_plans/claude-writing-lane-live-validation_2026-08-27.md` carries the
  occurrences. **L** — no mechanism identified, and the cockpit could not make it
  recur on demand; parked for accumulation. If it recurs, keep the raw stdout bytes
  and the stderr beside them before re-running.
- **`make test`'s `#428` state guard tripped on the cockpit's own concurrent
  `pr_watch.py 614 --json` poll**, which persisted `state/pr-watch/614.json` while the
  suite ran; `make` exited 2 (pytest's own status inside it is 1) with the regression
  banner printed above a summary line that still read `passed`, and a re-run with no
  poll passed. This is `#467`'s shape — a snapshotted descendant changed by a
  concurrent poll, with `--no-persist` as its documented avoidance — so the occurrence
  is recorded on `#467`, and nothing is parked here. **L**.
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
