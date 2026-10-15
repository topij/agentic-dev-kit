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
- **Review claimed post-restoration verification despite overlap.** Severity M, kept for accumulation.
  At `5635a764884ef61b0a690234c10bc68e1ec628b2`, the reviewer mutated its private copy
  while its suite ran, then described that run as after restoration. The cockpit withheld
  a receipt and required corrected evidence. Original and amended review logs are under
  `/private/tmp/devkit-overnight-20261014-01a13bcb/reviews/`: `review-1108-ownership.log` and `review-1108-ownership-amended.log`.

## 2026-10-14

- **Headless lanes used a denied manifest-refresh spelling during the 2026-10-13 batch.**
  Severity M. This entry records the original incident and its later correction.
  - **Repro:** in the 2026-10-13 overnight batch, the #1075, #1070 and #1079 lanes
    edited files that `kit-manifest.json` hashes, and could not refresh it.
    At that revision, `CONTRIBUTING.md` named `python3 scripts/kit_doctor.py --generate-manifest`. The
    lane profile (`config/claude-lane-settings.json`) allows only
    `Bash(uv run scripts/kit_doctor.py:*)`, and the lanes did not reach for that
    spelling.
  - **Effect:** each of those lanes' `make test` failed on
    `test_kit_repo_self_check_is_clean`, and the #1070 lane's push was refused by the
    pre-push hook. Each stopped without a PR.
  - **Correction — 2026-10-15:** [#1106](https://github.com/topij/agentic-dev-kit/pull/1106)
    documented `uv run scripts/kit_doctor.py --generate-manifest`. Routine polling and
    cleanup denials are recorded on [#1011](https://github.com/topij/agentic-dev-kit/issues/1011#issuecomment-6185414536).
- **`make test` outruns a headless lane's Bash time limit.** Severity M. Kept for
  accumulation, because the remedy is not established.
  - In the same batch, the first `make test` of the #1089, #1070 and #1079 lanes was
    killed at the background time limit, as each lane reported. The durations of the
    full runs are in each PR's `make test` stamp comment (#1096, #1097, #1099, #1100).
  - The #1089 lane then ended on a denied call before committing.
  - Whether the lane contract should prescribe a longer foreground timeout, or the lanes
    should stop before the stamp and leave it to the cockpit, was not decided.
- **The #1080 repair-chain shape recurred on LOW-only test-helper repairs.** Severity L,
  kept for accumulation.
  - On #1099 and #1100, each delta repair of a wording or pinning LOW drew a new LOW of
    the same size from the next delta lens.
  - #1100 converged once the claim was shortened to what the regex does.
  - #1099's third pair went to its ticket instead of a third round.
- **The archive sweep's moved-pairing case recurred, as in the 2026-10-12 entry below.**
  Severity L, kept for accumulation. This wrap-up's sweep joined the 2026-10-11 and
  2026-10-10 history blocks. The preflight then paired a GitHub keyword in the moved
  text with the next issue reference, at `docs/kit-handoff-history.md:72`. The text
  stays as exact bytes, per the 2026-10-12 decision.

## 2026-10-12

- **A handoff archive sweep still trips the record-prose preflight after #1088.** Severity
  L, kept for accumulation. The move exemption needs every line of a pairing moved
  unchanged. `archive_plan_sessions.py` rewrites each moved `## Session — …` heading to
  `### …` and drops the separator line, so a pre-existing pairing that spans a session
  boundary stays reported. It happened on this wrap-up: the last sentence of the 2026-10-09
  block in `docs/kit-handoff-history.md` pairs with the first reference of the 2026-10-08
  block below it. That history text is left unchanged.

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
