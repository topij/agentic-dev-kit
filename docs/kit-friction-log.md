# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most of this session's friction was
> filed directly as issues rather than parked here — which is the routing Principle #2
> prescribes, not a neglected inbox. Entries below are the ones that are *not* yet
> issue-shaped.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-07-25 — Backlog migrated to GitHub Issues

Two H-severity entries were **removed from this file** and filed as
[#26](https://github.com/topij/agentic-dev-kit/issues/26) (fallback review needs to be a
*panel*) and [#27](https://github.com/topij/agentic-dev-kit/issues/27) (a receipt
survives a redesign its reviewer never saw). #27's cheap half shipped in PR #29; the
issue stays open for the shape-change half.

Also closed this session, so their inbox entries below are **done**, kept only for the
trail: **#19** (premature receipt — closed by PR #25) and **#10** (lane-worktree gate
failure — closed by PR #28).

## 2026-07-25 — inbox

- **The `cp -r` quickstart can't distinguish kit-owned from adopter-owned files (severity: M).**
  Any file the kit tracks lands in an adopter's repo, which is why this repo's own narrative
  docs had to be renamed `kit-*.md` rather than simply filled in. `kit-manifest.json` now
  encodes the ownership boundary (`adopter_owned`), so a manifest-aware installer could copy
  correctly and the rename would become unnecessary. Filed as issue #18.

- **`--record-review` accepts a receipt while the primary bot is still queued (severity: M).**
  Recorded a fallback receipt on #16 when CodeRabbit's check read `PENDING — Review queued`;
  its four valid findings landed after the merge. The doctrine distinguishes *unavailable*
  from *slow*, but nothing mechanically does. Candidate: treat a configured bot's own
  `PENDING` check as a merge blocker while no receipt exists — but that inverts the
  informational-check exclusion in the one case where the exclusion is load-bearing (it is
  what stops the loop wedging on a bot that never reports), so it needs care. Filed as #19.

- **A lane's local gate fails for reasons unrelated to its diff (severity: H).**
  All three lanes this session hit the same two `state_paths` test failures, caused purely by
  running from inside a marker-carrying worktree. A gate that goes red for environmental
  reasons teaches agents to ignore a red gate. Already filed as issue #10 — raising severity
  here because three independent occurrences in one session makes it a pattern, not an
  incident.

- **A fix round on gate logic is where the next bug comes from — every time (severity: M, pattern).**
  Seven review rounds on PR #25. Every one found something real, and **rounds 3 through 7
  each found a defect introduced by the previous round's fix**: an incomplete poison-clock
  fix that still wedged on a *parseable* future date (R3); a section-scoping fix applied
  to 1 of 3 guards in the same function (R4); a replacement warning message that walked
  inline-list adopters into the corruption the deleted mechanism used to cause (R5); a
  style detection that missed a real flow spelling (R6); and a list spelling promoted to
  "supported" that the kit's own reader cannot parse (R7). Session-wide: **13 rounds
  across three PRs, all 13 with findings, 7 of them self-inflicted by the prior fix.**
  `safety-critical-changes.md` rule 3 **already** says "Re-review after every fix round
  until a full pass finds nothing new" and that "fix rounds on gate logic routinely
  introduce their own regressions" — so the floor is written and was followed. What this
  session adds is different, and is what should graduate: (a) a *base rate* — 13/13 rounds
  with findings means "until a pass finds nothing new" may never terminate, so the rule
  needs a stopping criterion it currently lacks; and (b) the criterion that actually got
  used, which is **blast radius, not round count** — a merge gate and a
  reported-never-gating display field cannot share a stopping point.

- **Reading the code is not the same as running it, and the gap is not small (severity: M).**
  Three defects this session were invisible to careful reading and obvious on execution:
  CodeRabbit's pending check reports `startedAt: 0001-01-01T00:00:00Z`, so an
  "unmeasurable age fails open" branch was not an edge case but the *only* path that bot
  ever took (the #19 guard was dead code for its own target); making `append_to_section`
  return non-zero looked plainly correct and aborted `init.sh` under `set -eu` on any
  config missing an optional section; and `kitconfig` silently resolves a next-line flow
  list to `{}`. **Candidate graduation:** the review-panel prompt (#26) should require
  the lens to *execute* the changed paths and to mutation-test new branches — mutation
  is what proved **five** properties across the session were unpinned despite tests that
  named them (on #29: anchored author matching, newest-review-per-bot, the `bots=`
  threading; on #25: the `init.sh` list-style branch and `grep -qi`'s
  case-insensitivity). Three of those five are #29's.

- **Narrative surfaces drift from the diff, and nobody re-reads them (severity: M).**
  #25's PR body needed three corrections (a stale test count, and two descriptions of a
  design the diff had replaced); #29's asserted an anchored-match property no test pinned;
  and **this very wrap-up** was fact-checked and came back with 13 issues, three of them
  HIGH — including a number that a review round on #25 had *explicitly corrected*
  ("four ways to corrupt" → three) and which I reintroduced while writing up the lesson
  that PR bodies keep drifting. Every instance was caught by a review pass, never by the
  author. **Proposed fix:** `wrap-up` should fact-check the handoff against `git log` /
  `gh` before committing — the handoff is read at the start of every future session, so a
  wrong number there propagates further than a wrong PR body. Filing this at M rather
  than L because the failure recurred *inside the document describing it*.

- **The cockpit bundled wrap-up narrative edits into a lane branch, and only the hook caught it (severity: L, but the guard worked).**
  While waiting on CI for PR #29 I updated `kit-handoff.md` and `kit-friction-log.md`, then
  `git add -A` swept them into the lane commit. `pre-push` refused, named both files, and
  said where the lane's handoff belongs instead. Recording it because it is the **positive**
  case this log rarely captures: a fail-closed guard firing on its author, with a message
  that made the fix obvious. Worth keeping in mind when weighing whether a guard is worth
  its friction — this one cost ten seconds and prevented a narrative-file conflict with the
  wrap-up PR. No change proposed.
