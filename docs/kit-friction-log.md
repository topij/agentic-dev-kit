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

## 2026-07-27 — Backlog migrated to GitHub Issues (#70–#77)

The inbox was swept by the `triage-friction-log` workflow. Thirteen entries in,
thirteen accounted for: **twelve graduated** into eight issues, **one** recorded a
measurement with *"No change proposed"*.

Four issues each merge **two** entries recorded on separate days, because the repeat is
the evidence — splitting them would lose the occurrence count that made them
issue-shaped:

- [#70](https://github.com/topij/agentic-dev-kit/issues/70) — a mutation harness that
  restores outside `finally` leaves the repo mutated; the tree must be checked *after*
  the harness exits, not only after a successful run.
- [#71](https://github.com/topij/agentic-dev-kit/issues/71) — build the
  closing-keyword guard: every match, every surface, no stripping, and the squash
  message checked at merge time. *Three occurrences across two sessions.*
- [#72](https://github.com/topij/agentic-dev-kit/issues/72) — `pr-watch` should warn at
  push time when a bot review no longer covers head, not only at receipt time.
- [#73](https://github.com/topij/agentic-dev-kit/issues/73) — the archive sweep must
  warn on relative cross-references in **both** directions. *Two occurrences; the second
  broke a reference the first sweep had written.*
- [#74](https://github.com/topij/agentic-dev-kit/issues/74) — the doc-budget remedy is a
  no-op at the default `--keep` (it measures lines, the sweep keeps blocks). *Three
  occurrences, two in this repo.*
- [#75](https://github.com/topij/agentic-dev-kit/issues/75) — invert contract item 7:
  assume the isolated worktree points at the wrong ref. *Nine of nine across two
  sessions.*
- [#76](https://github.com/topij/agentic-dev-kit/issues/76) — `--record-review` cannot
  record honest partial coverage, so the honest choice erases the trail.
- [#77](https://github.com/topij/agentic-dev-kit/issues/77) — nothing constrains the
  cockpit from editing the shared tree while a panel reviews it.

The thirteenth entry — the panel-disjointness measurement — carried *"No change
proposed"*: it is a second, stronger data point for the disjointness argument in
`fallback-review-panel.md`, which currently rests on one.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).
