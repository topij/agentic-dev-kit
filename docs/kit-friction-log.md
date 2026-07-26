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
