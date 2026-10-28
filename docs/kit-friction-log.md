# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded when it is found. Single incidents route **down** to the tracker; a genuine
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

## 2026-10-28

- **Two sessions acted on #1277 at once, and neither knew.** Severity M, kept for accumulation. Steps: a cloud session held #1277's round-budget packet; the 2026-10-28 local session ran a panel on the operator's go-ahead and posted its disposition; the cloud session then pushed `274fa3bf`, and the local session's push of the same narrowing was refused as non-fast-forward. Nothing in `pr_watch` showed the overlap. Missing: a mechanism and a remedy.

## 2026-10-24 — Backlog migrated by triage session 34cfc9d2f69d4462a37af84ce5a975c7

Engine mode: `engine-backed`.

Filed [#1213](https://github.com/topij/agentic-dev-kit/issues/1213) from TRI-03, the `2026-10-21` entry `Headless verification hit the runtime limit again.`.

Filed [#1214](https://github.com/topij/agentic-dev-kit/issues/1214) from TRI-08, the `2026-10-15` entry ``A review lens ran a global `pkill -f "pytest scripts/tests"`.``.

Archived without filing: TRI-01, the `2026-10-23` entry ``A lens's own `.git` probes keep its review round.``.

Archived without filing: TRI-02, the `2026-10-22` entry ``An unidentified `pr_watch` write failed a `make test` stamp.``.

Archived without filing: TRI-05, the `2026-10-20` entry `A reviewer ran verification in its handed linked tree.`.

Archived without filing: TRI-12, the `2026-10-14` entry `` `make test` outruns a headless lane's Bash time limit. ``.

Archived without filing: TRI-13, the `2026-10-11` entry `Each #1063 lens pass found a LOW in the author's own claims about its tests.`.

Approval commands: `approve TRI-03 TRI-08`, `archive TRI-01 TRI-02 TRI-05 TRI-12 TRI-13`, `park TRI-04 TRI-06 TRI-07 TRI-09 TRI-10 TRI-11 TRI-14`. Approver: `topij`.

## 2026-10-25

- **Something writes `pr_watch` state into linked worktrees' `state/` (recurrence).**
  Severity M, recurrence of the 2026-10-22 entry ``An unidentified `pr_watch` write
  failed a `make test` stamp``. On 2026-10-25, `make test` at `80fb1177` in
  `.claude/worktrees/lane-terminal` ran every test green (`5833 passed, 1 skipped`) and
  still exited 2 on the real-state guard (#428). The guard named
  `state/pr-watch/1236.json`, born 02:41 and modified 12:08, with keys `head`,
  `max_total`, `max_total_backend` and `settle_since`. The cockpit made no `pr_watch`
  call during that run. Two worktrees with no suite running gained `1236.json` and
  `1237.json` between 12:07 and 12:20, while review lenses were running. A fresh
  `1237.json` appeared in `lane-terminal` at 12:54:27, while the cockpit ran only
  read-only commands there. At that point no `pr_watch` or `claude -p` process was
  listed. The project's hook processes (`pr_followup_hook.py`, `check_doc_budget.py`,
  `check_memory_budget.py`) write no file, but `pr_followup_hook.py`'s injected text
  tells the receiving agent to run `pr_watch.py`, so a cockpit or lens agent following
  it in a worktree is not excluded. A bisect of `test_lane_launcher.py` found that
  neither half writes on its own while the whole file does; that fits an external writer
  but does not exclude an order- or time-dependent test. `~/Library/LaunchAgents` holds
  no job for this repository, and no other local session for it was listed. Writer not
  identified. A `make test` stamp run in a standalone clone outside the worktree set
  avoided it. Recurred 2026-10-26: `make test` at `36b4db6d` in
  `.claude/worktrees/delta-draw-verdicts` failed only the guard, on
  `state/pr-watch/1248.json` (written 08:02:51, 08:03:48, 09:09:54, 09:12:55 UTC). Lens
  transcripts show no `pr_watch` call; per-file reruns, and a file planted in place of the
  `state` directory, caught no write. A standalone-clone stamp again avoided it.
- **A failed `dev_session.sh new` leaves a session neither `rm` nor `new` clears.**
  Severity L, kept for accumulation. On 2026-10-25, in a single-branch clone whose
  fetch refspec lacked `main`, `new live3 --headless` failed at `git worktree add`
  (`invalid reference: origin/main`) after creating `dev-model-sessions/live3/`.
  `rm live3 --force` then refused (`no session 'live3' at …/live3/wt`) and `new live3`
  refused (`session 'live3' already exists`), naming `--force` as the way out. The
  smoke run moved on under a new scope name; `new --force` was not tried.
- **Discarding a lane deletes its usage record.** Severity M, input to
  [#1174](https://github.com/topij/agentic-dev-kit/issues/1174). A smoke lane at
  `a2bb8a46` (`new smoke-tier --headless --runtime claude`, then `launch_lane.py
  --tier cheap`) wrote `terminal.usage` into
  `<session>/launch-receipt-<descriptor_id>.json`. `dev_session.sh rm smoke-tier` then
  removed the whole session directory, and the receipt with it; no other copy of
  those figures exists. #1174's ranking report reads "recent lanes" from recorded rows,
  so it needs a home for usage that outlives `rm`. Without one, it sees only the lanes
  that have not yet been cleaned up.
- **A fast lane did not show RUN `starting` in one smoke run.** Severity L, kept for
  accumulation. In the same smoke run, a one-second poll of `dev_session.sh list` showed
  `running` at its first sample, then `completed` about eight seconds later. `starting`
  is real but lasts under a poll interval here, so a board watch cannot be used to
  confirm it.

## 2026-10-21

- **Review fixtures initially escaped their allocated round through pytest defaults.**
  Severity L, kept for accumulation. The report-limit reviewer superseded those probes
  with contained runs; the changelog reviewer repeated the missing mutation evidence
  with `TMPDIR` and `--basetemp` inside its round. Their PR review dispositions retain
  the limits. No shared fixture-containment change was selected.

## 2026-10-20

- **A prose review treated instruction conditionals as program branches.** Severity L,
  kept for accumulation. The adversarial lens for #1136 mutated the worktree preference
  in `AGENTS.md` and started `make mutation-test`. The cockpit stopped the exploratory
  full-suite runs and required restoration and a terminal clarification. The reviewer
  withdrew its claim that those runs were required: the code suite could not establish
  whether an agent follows the instruction. The
  [review disposition](https://github.com/topij/agentic-dev-kit/pull/1136#issuecomment-6287957657)
  retains the limits. No workflow remedy was selected.

## 2026-10-16

- **A lens wrote generically named helper files into the shared session scratchpad.** Severity L, kept for accumulation.
  #1111's round-9 correctness lens reported writing `mutate.py`, `muts1.json`, `preflight.sh`, `probe1.py` and an `orig/`
  directory directly into the scratchpad other rounds and lenses share. It said it had not checked whether those names
  already existed, so it may have overwritten an earlier round's file. The *Scratch namespace* contract item names the
  copy directory by lens and revision, but not loose helper files beside it. Worth acting on only if it recurs.

## 2026-10-15

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
## 2026-10-08

- **An approval-pending triage session cannot survive a configuration change.** Severity L, kept for accumulation.
  Triage session `469bcd58` froze the kit inbox on 2026-10-05 and waited for decisions. Merges then changed
  `config/dev-model.yaml` (#993, #986, #1006), and on 2026-10-08 its `resume` returned operator-held with
  "configuration identity mismatch", so its proposals could not be approved. A fresh draft replaced it. The binding
  is by design: only a `completed` state is exempt (*Completed-state retirement*). The cost is that operator
  decisions deferred across ordinary config merges are lost. Worth acting on only if it recurs.
