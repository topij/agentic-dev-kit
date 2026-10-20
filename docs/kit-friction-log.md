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

## 2026-10-20 — Backlog migrated by triage session 7858b0190c764ac3af1d3d1002463f7f

Engine mode: `engine-backed`.

Filed [#1137](https://github.com/topij/agentic-dev-kit/issues/1137) from TRI-01, the `2026-10-18` entry `Review mutation overlapped a full-suite run again.`.

Filed [#1138](https://github.com/topij/agentic-dev-kit/issues/1138) from TRI-05, the `2026-10-15` entry `A review lens rewrote the kit's shared pre-push hook from a copied worktree.`.

Filed [#1139](https://github.com/topij/agentic-dev-kit/issues/1139) from TRI-15, the `2026-10-14` entry `The archive sweep's moved-pairing case recurred, as in the 2026-10-12 entry below.`.

Filed [#1140](https://github.com/topij/agentic-dev-kit/issues/1140) from TRI-19, the `2026-10-09` entry `A field-limited backlog read still exceeded the tool output limit.`.

Archived without filing: TRI-02, the `2026-10-18` entry `The uv-cache retirement refusal recurred.`.

Archived without filing: TRI-03, the `2026-10-18` entry `Allocated review rounds retained uv-cache Git markers.`.

Archived without filing: TRI-07, the `2026-10-15` entry `Backgrounded lens suites failed SIGINT tests again.`.

Archived without filing: TRI-11, the `2026-10-15` entry `Review claimed post-restoration verification despite overlap.`.

Archived without filing: TRI-12, the `2026-10-14` entry `Headless lanes used a denied manifest-refresh spelling during the 2026-10-13 batch.`.

Archived without filing: TRI-14, the `2026-10-14` entry `The #1080 repair-chain shape recurred on LOW-only test-helper repairs.`.

Archived without filing: TRI-16, the `2026-10-12` entry `A handoff archive sweep still trips the record-prose preflight after #1088.`.

Archived without filing: TRI-18, the `2026-10-10` entry `Archival preservation met the new narrative preflight's conservative lexer.`.

Approval commands: `approve TRI-01 TRI-05 TRI-15 TRI-19`, `archive TRI-02 TRI-03 TRI-07 TRI-11 TRI-12 TRI-14 TRI-16 TRI-18`, `park TRI-04 TRI-06 TRI-08 TRI-09 TRI-10 TRI-13 TRI-17 TRI-20`. Approver: `topij`.

## 2026-10-16

- **A lens wrote generically named helper files into the shared session scratchpad.** Severity L, kept for accumulation.
  #1111's round-9 correctness lens reported writing `mutate.py`, `muts1.json`, `preflight.sh`, `probe1.py` and an `orig/`
  directory directly into the scratchpad other rounds and lenses share. It said it had not checked whether those names
  already existed, so it may have overwritten an earlier round's file. The *Scratch namespace* contract item names the
  copy directory by lens and revision, but not loose helper files beside it. Worth acting on only if it recurs.

## 2026-10-15

- **A review lens ran a global `pkill -f "pytest scripts/tests"`.** Severity L, kept for
  accumulation. The round-2 correctness lens on #1111 used it to stop its own stray run,
  and it could have killed another lens's suite in the same session. No collateral
  failure was observed.
- **Launcher shutdown verification hit its timing assertion.** Severity M, kept for accumulation.
  `make test` at `5635a764884ef61b0a690234c10bc68e1ec628b2` on 2026-10-15 in
  `/private/tmp/devkit-overnight-20261014-01a13bcb/sessions/oct14-policy-report-r2/wt`
  failed `test_sigterm_ignoring_child_is_forcibly_stopped_within_the_configured_bound`.
  The cause is unknown; no time-limit change was made. Evidence is under `/private/tmp/devkit-overnight-20261014-01a13bcb/`:
  `make-test-1108-ownership.log` and `make-test-1108-ownership-repeat.log`.
- **Review service stopped before a terminal report.** Severity M, kept for accumulation;
  the mechanism is unknown. The Codex review of `bb4e0de47de710886020b1eb247563f4c36f1c33`
  ended with a safety-screening response and supplied no approval receipt. Evidence: `/private/tmp/devkit-overnight-20261014-01a13bcb/reviews/review-1108-r1.log`, rollout
  `01a13c0b-b847-79e3-b271-5381b24bf55c`. Any remedy must preserve incomplete-review reporting.
- **Review began before author verification settled.** Severity M, kept for accumulation.
  The review of `f54cea61a7e1aaff26c3334140774e88ef27ab55` began while `make test` was
  running in the policy lane. The suite and reviewer found a renderer stand-in regression;
  its correction moved the head and required another review allowance. Finish author
  verification before dispatching a budget-limited review of the exact head.
## 2026-10-14

- **`make test` outruns a headless lane's Bash time limit.** Severity M. Kept for
  accumulation, because the remedy is not established.
  - In the same batch, the first `make test` of the #1089, #1070 and #1079 lanes was
    killed at the background time limit, as each lane reported. The durations of the
    full runs are in each PR's `make test` stamp comment (#1096, #1097, #1099, #1100).
  - The #1089 lane then ended on a denied call before committing.
  - Whether the lane contract should prescribe a longer foreground timeout, or the lanes
    should stop before the stamp and leave it to the cockpit, was not decided.
## 2026-10-11

- **Each #1063 lens pass found a LOW in the author's own claims about its tests.**
  Severity L, kept for accumulation. The
  full pass and the delta pass each found a changelog fragment or commit message saying
  the tests caught more than they did.
## 2026-10-08

- **An approval-pending triage session cannot survive a configuration change.** Severity L, kept for accumulation.
  Triage session `469bcd58` froze the kit inbox on 2026-10-05 and waited for decisions. Merges then changed
  `config/dev-model.yaml` (#993, #986, #1006), and on 2026-10-08 its `resume` returned operator-held with
  "configuration identity mismatch", so its proposals could not be approved. A fresh draft replaced it. The binding
  is by design: only a `completed` state is exempt (*Completed-state retirement*). The cost is that operator
  decisions deferred across ordinary config merges are lost. Worth acting on only if it recurs.
