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


## 2026-08-19

- **A merge-gate predicate was used to answer a reportorial question, and the bias
  inverted.** Severity **H**. `#520`'s new `⚠ review owed` line read
  `qualifying_bot_coverage` to decide whether anyone had reviewed the head. That function
  under-reports *deliberately* — its own docstring keeps the bias in the safe direction —
  because it feeds a **gate**, where under-reporting refuses a merge and is harmless. Used
  in a **report**, the same bias asserts that nobody reviewed the diff. Both panel lenses
  found it independently, in distinct reachable states (a bot's `CHANGES_REQUESTED` on
  the head; a failed check read alongside a real `APPROVED` review). Proposed fix: a rule
  that a gate predicate and a report predicate are different functions even when they read
  the same field — the gate answers "may I merge on this", the report answers "what is
  true" — and that reusing one for the other inverts its safe direction. Candidate for
  doctrine rather than a ticket: the instance is already handled in `#520`, and the shape is what
  is worth keeping.

- **The panel ran from hand-written prompts after its first round, losing
  `panel_prompt.py`'s guarantees — including a diffstat it computes correctly.** Severity
  **M**. `panel_prompt.py` assembled the opening round; every round after it was hand-written, to carry
  round-specific framing (delta boundary, the author's stated draws) that the engine has
  flags for but that were easier to write inline. One consequence surfaced immediately: the
  round-2 prompt quoted a diffstat computed over the wrong range — the previous round's
  delta, labelled as the full base diff — which the adversarial lens recomputed, caught,
  and reported rather than trusting. Nothing was harmed, because **Right revision** exists
  for exactly this. But the failure is silent when the lens does not check, and the engine
  would not have made it. Proposed fix: either use `--carry-forward` / `--delta-draws`
  (which exist for the delta pass) rather than hand-writing, or have `panel_prompt.py`
  refuse to accept a diffstat it did not compute.

- **`gh pr checks --json state` reports `IN_PROGRESS`, never `PENDING`.** Severity **L**. A
  watch loop breaking on `[ "$s" != "PENDING" ]` exits on its first poll and reads as
  "CI finished" — the plain `gh pr checks` text output says `pending`, so the JSON field's
  vocabulary is not the one the human-facing surface trains you to expect. Cost here was
  one wasted loop, caught because the printed check row contradicted the loop's own
  conclusion. Terminal states observed: `SUCCESS`, `FAILURE`, `ERROR`, `CANCELLED`.
  Proposed fix: worth a line wherever the kit documents polling `gh` directly, since
  `pr_watch.py` insulates you from it and therefore never teaches it.

## 2026-08-18 — Backlog migrated to GitHub Issues (#506–#515)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Fifteen
entries in, fifteen accounted for:** ten new issues
([#506](https://github.com/topij/agentic-dev-kit/issues/506)–[#515](https://github.com/topij/agentic-dev-kit/issues/515)),
one pair merged at filing (the `make test | tail` entry and the same-night zsh
`pipefail` correction, per the approved routing), and three occurrence comments on
already-open issues carrying the same mechanism —
[#372](https://github.com/topij/agentic-dev-kit/issues/372) (two data points),
[#467](https://github.com/topij/agentic-dev-kit/issues/467), and
[#435](https://github.com/topij/agentic-dev-kit/issues/435). All ten creates and all
three comments were re-read from the tracker after landing per `#138`.

**Approval.** The numbered proposal DM went to the operator in-session (channel
`D083840DP7B`, ts `1787045705.365309`, continued at `1787045712.981769`); the approval
arrived at 2026-08-18 13:17:40 EEST — "lgtm" — the grammar's bulk approve; nothing was
declined. This block is the committed approval record `#128` asks the interactive path
to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 17,439 bytes, sha256
`5912a487eb7bdbff28ae0b3df3c361fb7a3943aae5339d54ec13c927fc47032b`, reproducing from
`git show 5645899:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The working
tree was byte-identical to `5645899`'s copy at sweep time, verified by recomputing
this digest from the file being swept immediately before the rewrite, so every block
swept with nothing held back and no window-added entries existed.

Swept entries are verbatim in the archive under `Graduated 2026-08-18`.
