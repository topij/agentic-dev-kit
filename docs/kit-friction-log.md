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

## 2026-10-12 — Backlog migrated by triage session ae0b23b828f945bd9228c7c591ff0530

Engine mode: `engine-backed`.

Filed [#1078](https://github.com/topij/agentic-dev-kit/issues/1078) from TRI-01, the `2026-10-12` entry `A review lens wrote into the tree it was handed, again.`.

Filed [#1079](https://github.com/topij/agentic-dev-kit/issues/1079) from TRI-03, the `2026-10-11` entry `A CI-only failure in the pinned-preflight test passed on rerun.`.

Filed [#1080](https://github.com/topij/agentic-dev-kit/issues/1080) from TRI-05, the `2026-10-10` entry `The repair-and-review chain shape recurred in the record-prose preflight.`.

Filed [#1081](https://github.com/topij/agentic-dev-kit/issues/1081) from TRI-10, the `2026-10-08` entry `The headless lane profile cannot read the lane's own ticket.`.

Filed [#1082](https://github.com/topij/agentic-dev-kit/issues/1082) from TRI-12, the `2026-10-08` entry ``A cockpit `pr_watch` call invalidated its own `make test` stamp again.``.

Filed [#1083](https://github.com/topij/agentic-dev-kit/issues/1083) from TRI-13, the `2026-10-08` entry ``A comment in `scripts/sweep_scratch.py` still describes the bare-repo skip by its object store.``.

Archived without filing: TRI-04, the `2026-10-11` entry `Pinning prose did not converge on #1054; a design change did.`.

Archived without filing: TRI-08, the `2026-10-09` entry `A review lens wrote refs into the tree it was handed.`.

Archived without filing: TRI-09, the `2026-10-09` entry `The review-chain shape in the 2026-10-08 entry below recurred on #1028.`.

Archived without filing: TRI-11, the `2026-10-08` entry `A full-pass review chain on an executed doc block found a new shape each round.`.

Approval commands: `approve TRI-01 TRI-03 TRI-05 TRI-10 TRI-12 TRI-13`, `archive TRI-04 TRI-08 TRI-09 TRI-11`, `park TRI-02 TRI-06 TRI-07 TRI-14`. Approver: `topij`.

## 2026-10-11

- **Each #1063 lens pass found a LOW in the author's own claims about its tests.**
  Severity L, kept for accumulation. The
  full pass and the delta pass each found a changelog fragment or commit message saying
  the tests caught more than they did.
## 2026-10-10

- **Archival preservation met the new narrative preflight's conservative lexer.**
  Severity L, parked because no workflow remedy was established. During this
  wrap-up, the budget helper moved the dated merge-gate review-evidence entry into
  history. The preflight then treated its historical ticket-state verbs as added
  keyword/reference pairings. The shared wrap-up workflow prescribes preserving
  earlier session entries, while the repository forbids unintended ticket-state
  directives. The moved entry retained its dated decisions with neutral wording;
  the archive helper itself was not changed. Whether preservation should mean
  exact bytes or historical meaning under this guard needs a scoped decision.

## 2026-10-09

- **A field-limited backlog read still exceeded the tool output limit.** Severity L, kept for accumulation. During this Codex session’s `session-start` read, `gh issue list --json number,title,labels,state,updatedAt,url --limit 500` returned label IDs, descriptions and colours, and the tool truncated the output. A rerun kept the complete query, checked its page ceiling, and rendered issue numbers, priority labels and titles compactly. This is related to #143’s payload-overflow shape; selecting fields alone did not keep the rendered payload within the tool limit.
## 2026-10-08

- **An approval-pending triage session cannot survive a configuration change.** Severity L, kept for accumulation.
  Triage session `469bcd58` froze the kit inbox on 2026-10-05 and waited for decisions. Merges then changed
  `config/dev-model.yaml` (#993, #986, #1006), and on 2026-10-08 its `resume` returned operator-held with
  "configuration identity mismatch", so its proposals could not be approved. A fresh draft replaced it. The binding
  is by design: only a `completed` state is exempt (*Completed-state retirement*). The cost is that operator
  decisions deferred across ordinary config merges are lost. Worth acting on only if it recurs.
