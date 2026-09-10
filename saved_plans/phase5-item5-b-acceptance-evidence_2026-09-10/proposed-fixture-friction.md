# Friction Log

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real
> use — a bug, an awkward workflow, a recurring annoyance — recorded the moment it's
> fresh, at session end.
>
> **What lands here is what is not yet issue-shaped.** A finding that already carries a
> reproduction, a named mechanism and a proposed fix is filed straight to the tracker at
> session end, by `wrap-up`'s friction-routing step and on the operator's go-ahead — a
> triage pass could add nothing to it but latency. When that route is unavailable (no
> operator, no tracker, a failed create) the finding parks here instead.
> This file holds the remainder: findings still missing one of those three, and single
> instances of a shape that only matters if it recurs. A periodic triage (`triage-friction-log`)
> graduates those — single incidents go **down** to the tracker; a genuine,
> multi-occurrence **pattern** goes **up** into a rule or skill change. Route down by
> default, up only on repetition — so the flywheel self-regulates instead of ratcheting
> every week.
>
> Each entry: the observed issue, the date surfaced, a rough severity (**H**igh / **M**edium
> / **L**ow), and a proposed fix or next step. Link related PRs, commits, or tracker items
> when available. Graduated entries are swept to
> [`friction-archive.md`](friction-archive.md) so this file stays just the current
> inbox plus the most-recent graduation marker.
>
> Tracker board: set `tracker.url` in `config/dev-model.yaml`

## 2026-09-09 — inbox

- **[kit] Installed tests assumed upstream configuration and generated adapters (severity: M).** The ITEM5-B setup on 2026-09-09 reached assertions against fixture-owned configuration and the preserved Codex wrap-up. The approved kit repair separates controlled test inputs from adopter policy; ITEM5-B-UPDATE-01 applied it from source `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`. The kit execution records retain the command, directory, revision, date, terminal results and skips. This entry records the adoption experience; it creates no upstream issue or comment.

- **[kit] Drift-liveness applicability differed between parent and child (severity: M).** The setup's installed run exercised a parent that required its source-only child never to skip. The approved repair aligned their applicability while retaining source liveness probes. Keep this introduced applicability defect separate from the older configuration assumptions and the independently disclosed deep-JSON source-suite failure. The update evidence retains the complete results; this entry does not claim client loading, a passing source suite, or completed field exit.
