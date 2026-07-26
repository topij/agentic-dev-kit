# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most friction is filed directly as
> issues rather than parked here — which is the routing Principle #2 prescribes, not a
> neglected inbox. Anything that appears below a graduation marker is un-graduated: not yet
> issue-shaped, or waiting for the next `triage-friction-log` sweep.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-07-26 — Backlog migrated to GitHub Issues (#54–#56)

The inbox was swept by the `triage-friction-log` workflow. Three entries graduated:

- [#54](https://github.com/topij/agentic-dev-kit/issues/54) — every verification claim
  must name the command that establishes it (supersedes the narrower "wrap-up should
  fact-check the handoff" proposal).
- [#55](https://github.com/topij/agentic-dev-kit/issues/55) — `safety-critical-changes.md`
  rule 1 should name a tightening threshold.
- [#56](https://github.com/topij/agentic-dev-kit/issues/56) — removing a mechanism
  requires enumerating what it was rejecting.

Three further entries needed no ticket: their proposed fixes had **already shipped** in
PR #31 — the panel contract now requires lenses to execute and mutation-test (contract
items 4–5), rule 3 carries the blast-radius stopping criterion, and contract item 7
mandates isolated worktrees.

The remaining five: four were already tagged with an issue id (#10, #18, #19, #33), and one
recorded a guard working correctly with *"No change proposed"*. Eleven entries in, eleven
accounted for.

Everything above now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

## 2026-07-26

- **The doc-budget remedy does not fire at the default `--keep`.** `check_doc_budget`
  measures **lines**; `archive_plan_sessions` keeps **blocks**. This handoff hit
  448/400 lines with 5 blocks, so the remedy the warning names printed *"nothing to
  move: 5 session block(s) <= --keep 6"* and the file stayed over budget. The agent has
  to guess a `--keep` and re-run until the line count drops — which is exactly the
  manual fiddling the deterministic engine exists to remove. **M** — proposed fix: give
  `archive_plan_sessions` a `--target-lines` mode (sweep oldest-first until under
  budget), or have `check_doc_budget`'s remedy string compute and name the `--keep` that
  would work. Reproduced twice this session (kit and cs-toolkit).
- **A runtime's isolated worktree points at the session's base ref, not the PR head.**
  All **four** review-lens launches this session (2 lenses × 2 rounds) landed on `main`
  with an empty `git diff main...HEAD`. Every one detected it and cloned the real target
  — because the launch prompt required them to *report the path and diff stat they saw*.
  `fallback-review-panel.md` contract item 7 says to verify; what actually surfaced it
  was making the report **mandatory output**. **H** — proposed fix: promote "state the
  path reviewed and the diff stat" from advice to a required field of the lens report in
  contract item 8, and say plainly that a lens which cannot show a non-empty diff has not
  reviewed anything. A clean pass over an empty diff is indistinguishable from a real one.
- **`--record-review` has no way to record honest partial coverage.** It correctly
  refuses a receipt bound to a stale head (`PR head changed during review`), but the only
  alternative is a receipt claiming the current head — which the panel did not review. So
  the honest choice is **no receipt at all**, and the audit trail then loses the fact that
  a two-lens panel ran at all. **M** — proposed fix: allow recording against the reviewed
  sha with the head-gap represented rather than rejected (the existing `bots_behind_head`
  field is the precedent). Related: #32.
- **Negating a GitHub closing keyword still arms it.** A PR body was edited before merge
  to retract a closure claim; the retraction read *"Does NOT close #60"*. GitHub matched
  `close #60`, and merging closed an issue documenting an **unfixed** bug. Caught after
  the fact and reopened. **M** — proposed fix: one line in the wrap-up / pr-watch
  doctrine — never write a closing keyword adjacent to an issue number you do not intend
  to close, even negated; write "#60 stays open". cs-toolkit's `CLAUDE.md` already carries
  the Linear-side twin of this hazard.
- **The cockpit edited the shared tree while lenses were reviewing it.** A lens reported
  the shared checkout changing mid-run (5 files, mtimes inside its window) and correctly
  noted it was not the author. Its own review was unaffected — it worked from an isolated
  clone — but it had to spend output distinguishing "concurrent editor" from "corruption".
  Contract item 7 constrains the **lenses**; nothing constrains the **cockpit**. **M** —
  proposed fix: add a cockpit-side clause — do not mutate the shared tree between
  launching a panel and reading its findings.
- **The archive sweep breaks *relative* cross-references, and its docstring says it
  doesn't.** `archive_plan_sessions.py:20` claims *"It only ever moves content — every
  cross-reference (ticket ids, PR links, commit shas, …) is preserved."* Every kind it
  enumerates is **absolute**. A relative one is not preserved: this session's sweep moved
  the Phase 3a block into the history file while Phase 3b stayed live, orphaning
  *"see the Phase 3b block above"* — the target is now in a different file. Caught by
  CodeRabbit on the wrap-up PR, not by the sweep, which reported success. **M** —
  proposed fix: have the sweep scan moved blocks for `(above|below)`-style references
  and warn (not rewrite — rewriting is the class of surgery `init.sh`'s deleted marker
  migration proved dangerous). Same family as #53, which is about the pointer the sweep
  *writes*; this is about the references it *carries*.
