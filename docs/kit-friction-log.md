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

## 2026-10-08

- **The headless lane profile cannot read the lane's own ticket.** Severity M. Parked because no operator was present to approve a tracker write. `config/claude-lane-settings.json` allows no `gh issue view`, and under `dont-ask` a denied call ends the lane. `parallel.md` requires every lane brief to be grounded in the ticket body, so the cockpit put each ticket's full text into the task prompt. Lane `pr-watch-trio` also had a multi-line `git commit -m` message containing backticks refused, and fell back to repeated single-line `-m` flags. Both are the shape #1011 tracks: routine lane steps the profile denies. The fix is either a read-only `gh issue view` grant or a launcher step that embeds the ticket text. The profile is safety-critical.
- **A full-pass review chain on an executed doc block found a new shape each round.** Severity L, kept for accumulation. On #1020 the lens found a different input-shape gap in the fragment lookup at each of its three reviewed heads: quoted names, then reused names and symlinks, then merge-only and type-changed fragments. The budget ran out with a Low-Medium open. An operator-authorized fourth round, on 2026-10-09, again found new shapes, this time test gaps (#1026). This is the shape #1012 names for skips, here met by a lookup over git history: list every history shape (rename, merge, delete, type change, reuse) before the first review.
- **A cockpit `pr_watch` call invalidated its own `make test` stamp again.** Severity L, kept for accumulation. A `--record-round` call made while the stamp ran wrote `state/pr-watch/1020.json`, and the suite's real-state guard (#428) failed a run in which every test passed. The rerun on a quiet tree was the stamp.
- **A comment in `scripts/sweep_scratch.py` still describes the bare-repo skip by its object store.** Severity L. #1021 corrected the doctrine's version of this wording. The delta lens on #1021 found that the comment around `scripts/sweep_scratch.py:401` ("skipping it would drop its object store") overstates it the same way. It should say that the configured repository's git dir and alternates chain would go unrecorded.

- **An approval-pending triage session cannot survive a configuration change.** Severity L, kept for accumulation.
  Triage session `469bcd58` froze the kit inbox on 2026-10-05 and waited for decisions. Merges then changed
  `config/dev-model.yaml` (#993, #986, #1006), and on 2026-10-08 its `resume` returned operator-held with
  "configuration identity mismatch", so its proposals could not be approved. A fresh draft replaced it. The binding
  is by design: only a `completed` state is exempt (*Completed-state retirement*). The cost is that operator
  decisions deferred across ordinary config merges are lost. Worth acting on only if it recurs.

## 2026-10-08 — Backlog migrated by triage session 7f6626780abd4719b8a752a5ac8856ee

Engine mode: `engine-backed`.

Filed [#1009](https://github.com/topij/agentic-dev-kit/issues/1009) from TRI-01, the `2026-10-08` entry ``Parallel lanes collide on `CHANGELOG.md` and `kit-manifest.json`, and each collision costs a review round.``.

Filed [#1010](https://github.com/topij/agentic-dev-kit/issues/1010) from TRI-02, the `2026-10-08` entry `A composed delta receipt cannot gain a disposition comment afterwards.`.

Filed [#1011](https://github.com/topij/agentic-dev-kit/issues/1011) from TRI-05, the `2026-10-07` entry `A headless Claude lane cannot open a PR with a real body.`.

Filed [#1012](https://github.com/topij/agentic-dev-kit/issues/1012) from TRI-08, the `2026-10-07` entry `Fix rounds on #986 kept creating the next round's findings.`.

Filed [#1013](https://github.com/topij/agentic-dev-kit/issues/1013) from TRI-11, the `2026-10-05` entry `The disposition filename was supplied as literal text again.`.

Filed [#1014](https://github.com/topij/agentic-dev-kit/issues/1014) from TRI-20, the `2026-10-03` entry `` `pr_watch.py`'s verification-stamp parser and `wrap-up.md`'s stamp wording disagree. ``.

Archived without filing: TRI-03, the `2026-10-08` entry `Review lenses wrote into the tree they were handed, twice.`.

Archived without filing: TRI-04, the `2026-10-08` entry `A headless lane could not restore its own mutation-test edits.`.

Archived without filing: TRI-06, the `2026-10-07` entry ``The `test` entry's recovery branch still judges validity by `canonical_state` alone.``.

Archived without filing: TRI-07, the `2026-10-07` entry `The two-lens panel did not converge on a new destructive engine.`.

Archived without filing: TRI-09, the `2026-10-07` entry `A lens's report-mode run against the real shared scratch root was refused by the runtime's auto-mode classifier.`.

Archived without filing: TRI-10, the `2026-10-07` entry ``A cockpit `make test` was killed by SIGTERM mid-suite.``.

Archived without filing: TRI-12, the `2026-10-05` entry `An installation push preceded root verification's terminal result.`.

Archived without filing: TRI-13, the `2026-10-05` entry `A fallback review's full suite overlapped its scratch mutations.`.

Archived without filing: TRI-14, the `2026-10-04` entry `A PR poll initially put its receipt in the real state tree during synthetic validation.`.

Archived without filing: TRI-15, the `2026-10-04` entry `The cockpit changed verification state while claiming an isolated run.`.

Archived without filing: TRI-16, the `2026-10-04` entry `A public fallback disposition initially contained its local filename.`.

Archived without filing: TRI-17, the `2026-10-03` entry `The matrix guard's LOW residue from #923's last delta pass.`.

Archived without filing: TRI-18, the `2026-10-03` entry `#919's tracker body does not scope the row audit the records now assign to it.`.

Archived without filing: TRI-19, the `2026-10-03` entry `` `make lint` does not see an untracked file, so a lint failure surfaced only after a stamp run started. ``.

Archived without filing: TRI-21, the `2026-10-03` entry `A negative control anchored on a structural boundary stopped testing anything when an unrelated key moved that boundary.`.

Archived without filing: TRI-22, the `2026-10-03` entry `The option offered for an operator decision overstated its own premise.`.

Archived without filing: TRI-23, the `2026-10-03` entry `#923 is a further occurrence of the shape #838 tracks.`.

Approval commands: `approve TRI-01 TRI-02 TRI-05 TRI-08 TRI-11 TRI-20`, `archive TRI-03 TRI-04 TRI-06 TRI-07 TRI-09 TRI-10 TRI-12 TRI-13 TRI-14 TRI-15 TRI-16 TRI-17 TRI-18 TRI-19 TRI-21 TRI-22 TRI-23`. Approver: `topij`.
