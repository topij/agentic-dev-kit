# Friction Log Archive — agentic-dev-kit

Graduated friction entries live here after they have been routed to the tracker
(GitHub Issues on this repo) or promoted into a repeated-pattern rule.

## Graduated 2026-07-27 — GitHub Issues (#70–#77)

Swept by the `triage-friction-log` workflow. Thirteen entries, fully accounted for:
**twelve graduated** into eight issues ([#70](https://github.com/topij/agentic-dev-kit/issues/70)–[#77](https://github.com/topij/agentic-dev-kit/issues/77)),
four of which each merge two entries recorded on separate days; **one** recorded a
measurement with *"No change proposed"*. All thirteen are kept below for the trail,
along with the prior graduation marker.

### 2026-07-26 — Backlog migrated to GitHub Issues (#54–#56)

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

### 2026-07-27

- **A mutation harness that restores outside `finally` leaves the repo mutated.** My
  restore line was unreachable when the script died parsing pytest output (a bare
  `python3` with no pytest returned no stdout, and `splitlines()[-1]` raised). The
  working tree kept a live mutant until `git status` caught it. Neither existing warning
  covers it: `#50` is about stale `.pyc`, and `fallback-review-panel.md` contract item 5
  warns only about **false kills** from a checksum/drift test (it does not mention
  `.pyc` at all). Both frame the hazard as "the result may be wrong"; neither says the
  repo may be left broken. **H** —
  proposed fix: contract item 5 should say the restore belongs in a `finally` (or a
  git-clean check) and that any harness must verify the tree is clean *after* it exits,
  not only after a successful run.
- **The closing-keyword trap fired again, because I weakened a correct rule on the
  strength of an experiment that did not test what I thought.** `#61` was closed by the
  squash-merge of `#68` and reopened by hand.

  **What is actually measured** — three data points, with their confounds stated,
  because two earlier write-ups of this stated more than the data supports:

  | artifact | form | outcome |
  | --- | --- | --- |
  | `#68` body | `Closes #61` inside a **fenced block** | inert (`closingIssuesReferences: []`) |
  | `9c6ab3a` commit message | `Closes #61` in an **inline** span | **fired** — closed `#61` |
  | `#63` body | `Does NOT close #60` **and** a plain `fix #60` | fired; which one is **not isolated** |

  **What is NOT measured, though I twice wrote as if it were:** whether an *inline* span
  is inert in a PR body. The two backtick data points differ in **two** variables at once
  — fenced-vs-inline *and* body-vs-commit — so "GitHub excludes inline code spans" and
  "fenced blocks are inert everywhere, inline spans fire everywhere" fit the evidence
  equally well. Under the second reading, the fix I proposed last round (strip inline
  code from a PR body before checking) reopens the exact hole that closed `#61`.

  Likewise the *negation* hypothesis: `#63`'s body carries a plain, non-negated `fix #60`
  alongside the negated mention, so a check that only flags keywords **near a negation**
  would have passed that body clean.

  **H** — **stop deriving a mechanism; take the conservative rule.** Three attempts to
  state this precisely have each been wrong, which is rule 1's threshold. The original
  2026-07-26 rule below — never write a closing keyword adjacent to an issue number you
  do not intend to close, in any form, on any surface — would have prevented all three
  incidents; the measurement talked me *out* of a correct rule. It stands as written, and
  the proposed check follows it rather than any theory of markdown:

  - flag **every** match on **every** surface — PR body, every commit message, and the
    squash message — with **no stripping** of code spans or fenced blocks;
  - cover the forms the naive regex misses and GitHub honours: `owner/repo#61`, a full
    issue URL, and `Closes: #61` (a colon, not whitespace);
  - check the **squash message at merge time** specifically. It is composed *after* the
    PR body was reviewed, and nothing reviews it — verified: `9c6ab3a`'s message matches
    neither `#68`'s title, its body, nor any of its three branch commits, and no hook in
    `scripts/` inspects commit messages at all;
  - the operator confirms each match. Over-firing is the acceptable failure here.

  Occurrence count, corrected: **three occurrences across two sessions** (`#63` and `#64`
  were the same session; `9c6ab3a` is this one).
- **A review bot with an incremental model keeps a stale review across a rewrite.**
  CodeRabbit reviewed the pre-split head, then declined `@coderabbitai review`
  ("does not re-review already reviewed commits") and hit its Fair Usage limit on
  `@coderabbitai full review`. The PR was force-pushed and then substantially rewritten,
  so the only bot review covered code that no longer existed. `pr_watch`'s
  `bots_behind_head` recorded it correctly — the friction is that **nothing warns at
  push time**, when re-requesting is still cheap. **M** — proposed fix: have `pr-watch`
  surface `covers_head: false` as a distinct, louder line right after a push that
  changes the diff shape, rather than only at receipt time. Related: `#27`, `#44`.
- **The panel's worth is disjointness, and this run measured it.** Round 1: the
  adversarial lens found the enclosing-repo and `GIT_DIR` regressions; the correctness
  lens independently found the `~`-expansion disagreement between `init.sh` and the new
  detector. Almost no overlap. Round 2's correctness lens then found the *misattributed
  defect* — a false sentence in the commit message written to describe round 1's own
  outcome, which could not have existed when round 1 ran. **No change proposed** —
  recording it because `fallback-review-panel.md` argues disjointness from one prior
  data point, and this is a second, stronger one worth citing there. Note the honest
  framing of what the panel beat: the four regressions were missed by CI, by the suite
  **as it then stood**, and by the mutation run **at that head** — not by the 372-test
  suite quoted elsewhere, which only exists *because* those findings were fixed.
- **The archive sweep broke a cross-reference again — and this time it broke one the
  PREVIOUS sweep had written.** The 2026-07-26 entry below reports the sweep orphaning
  *"see the Phase 3b block above"*. Today's sweep moved Phase 3b itself into the history
  file, so the surviving text — *"see the Phase 3b block, still live in
  kit-handoff.md"* — became false in a second way: the target is now in the very file
  the sentence sits in. Fixed by hand in this commit. **M** — the entry below proposes
  warning on `(above|below)`-style references in *moved* blocks; this instance shows the
  warning must also cover references **into** a moved block from anywhere in either
  document, since the block that moved was the reference's *target*, not its location.
  Same family as `#53`.
- **The doc-budget remedy no-op reproduced a third time** (see the 2026-07-26 entry
  below). `check_doc_budget` reported 421/400; the remedy it names printed *"nothing to
  move: 5 session block(s) <= --keep 6"*; `--keep 4` was needed and found by guessing.
  **No new fix proposed** — recording the third occurrence. The entry below already
  records two; this makes it three, two of them in *this* repo, which is a pattern
  rather than a run of bad luck.
- **A review lens's isolated worktree pointed at the wrong ref again — 5 of 5 this
  session, 9 of 9 across two.** (Last session's entry below records 4 of 4; this session
  ran 2 lenses × 2 rounds on `#65` plus 1 on `#68`.) Every lens detected it and cloned
  the target itself, because the prompt required reporting the path and diff stat.
  **H** — proposed fix: this is no longer a
  caveat, it is the default behaviour. Contract item 7 should stop saying "verify" and
  start saying "assume the worktree is wrong; clone the target yourself first", with the
  path/diff-stat report as a required field of the lens output (the existing 2026-07-26
  entry proposed the report; this one is about inverting the default).

### 2026-07-26

- **The doc-budget remedy does not fire at the default `--keep`.** `check_doc_budget`
  measures **lines**; `archive_plan_sessions` keeps **blocks**. This handoff hit
  448/400 lines with 5 blocks, so the remedy the warning names printed *"nothing to
  move: 5 session block(s) <= --keep 6"* and the file stayed over budget. The agent has
  to guess a `--keep` and re-run until the line count drops — which is exactly the
  manual fiddling the deterministic engine exists to remove. **M** — proposed fix: give
  `archive_plan_sessions` a `--target-lines` mode (sweep oldest-first until under
  budget), or have `check_doc_budget`'s remedy string compute and name the `--keep` that
  would work. Reproduced twice this session (kit and cs-toolkit).
- **A runtime's isolated worktree points at the session's base ref, not the PR head.**
  All **four** review-lens launches this session (2 lenses × 2 rounds) landed on `main`
  with an empty `git diff main...HEAD`. Every one detected it and cloned the real target
  — because the launch prompt required them to *report the path and diff stat they saw*.
  `fallback-review-panel.md` contract item 7 says to verify; what actually surfaced it
  was making the report **mandatory output**. **H** — proposed fix: promote "state the
  path reviewed and the diff stat" from advice to a required field of the lens report in
  contract item 8, and say plainly that a lens which cannot show a non-empty diff has not
  reviewed anything. A clean pass over an empty diff is indistinguishable from a real one.
- **`--record-review` has no way to record honest partial coverage.** It correctly
  refuses a receipt bound to a stale head (`PR head changed during review`), but the only
  alternative is a receipt claiming the current head — which the panel did not review. So
  the honest choice is **no receipt at all**, and the audit trail then loses the fact that
  a two-lens panel ran at all. **M** — proposed fix: allow recording against the reviewed
  sha with the head-gap represented rather than rejected (the existing `bots_behind_head`
  field is the precedent). Related: #32.
- **Negating a GitHub closing keyword still arms it.** A PR body was edited before merge
  to retract a closure claim; the retraction read *"Does NOT close #60"*. GitHub matched
  `close #60`, and merging closed an issue documenting an **unfixed** bug. Caught after
  the fact and reopened. **M** — proposed fix: one line in the wrap-up / pr-watch
  doctrine — never write a closing keyword adjacent to an issue number you do not intend
  to close, even negated; write "#60 stays open". cs-toolkit's `CLAUDE.md` already carries
  the Linear-side twin of this hazard.
- **The cockpit edited the shared tree while lenses were reviewing it.** A lens reported
  the shared checkout changing mid-run (5 files, mtimes inside its window) and correctly
  noted it was not the author. Its own review was unaffected — it worked from an isolated
  clone — but it had to spend output distinguishing "concurrent editor" from "corruption".
  Contract item 7 constrains the **lenses**; nothing constrains the **cockpit**. **M** —
  proposed fix: add a cockpit-side clause — do not mutate the shared tree between
  launching a panel and reading its findings.
- **The archive sweep breaks *relative* cross-references, and its docstring says it
  doesn't.** `archive_plan_sessions.py:20` claims *"It only ever moves content — every
  cross-reference (ticket ids, PR links, commit shas, …) is preserved."* Every kind it
  enumerates is **absolute**. A relative one is not preserved: this session's sweep moved
  the Phase 3a block into the history file while Phase 3b stayed live, orphaning
  *"see the Phase 3b block above"* — the target is now in a different file. Caught by
  CodeRabbit on the wrap-up PR, not by the sweep, which reported success. **M** —
  proposed fix: have the sweep scan moved blocks for `(above|below)`-style references
  and warn (not rewrite — rewriting is the class of surgery `init.sh`'s deleted marker
  migration proved dangerous). Same family as #53, which is about the pointer the sweep
  *writes*; this is about the references it *carries*.

## Graduated 2026-07-26 — GitHub Issues (#54–#56)

Swept by the `triage-friction-log` workflow. Eleven entries, fully accounted for:

- **3 graduated** to issues [#54](https://github.com/topij/agentic-dev-kit/issues/54),
  [#55](https://github.com/topij/agentic-dev-kit/issues/55) and
  [#56](https://github.com/topij/agentic-dev-kit/issues/56).
- **3 needed no ticket** — their proposed fixes had already shipped in PR #31.
- **4 were already tagged** with an issue id (#10, #18, #19, #33).
- **1 recorded a guard working correctly**, with *"No change proposed"*.

All eleven are kept below for the trail.

### 2026-07-25 — Backlog migrated to GitHub Issues

Two H-severity entries were **removed from this file** and filed as
[#26](https://github.com/topij/agentic-dev-kit/issues/26) (fallback review needs to be a
*panel*) and [#27](https://github.com/topij/agentic-dev-kit/issues/27) (a receipt
survives a redesign its reviewer never saw). #27's cheap half shipped in PR #29; the
issue stays open for the shape-change half.

Also closed this session, so their inbox entries below are **done**, kept only for the
trail: **#19** (premature receipt — closed by PR #25) and **#10** (lane-worktree gate
failure — closed by PR #28).

### 2026-07-25 — inbox

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

### 2026-07-26 — inbox

> **At the 150-line budget.** A `triage-friction-log` sweep is required before the
> next entry — the two H entries below are issue-shaped and #33 is already filed.

- **Mutation testing this repo reports false kills — filed as [#33](https://github.com/topij/agentic-dev-kit/issues/33) (severity: H).**
  `kit_doctor`'s self-check rehashes every kit-owned file, so any byte change to an
  engine fails it and every mutant looks killed. The **mechanism** is trivially
  reproducible (change one comment in an engine; only the manifest test fails). The
  **figure** — a lens reporting 17/17 killed on #31, and 7 survivors once that test
  was excluded — is attested rather than independently measured; the 17 are enumerated
  nowhere. Those 7 were closed inside #31. Filed at H because it is **retroactive**:
  mutation evidence cited across #25, #28, #29 and #31 may be worthless wherever the
  reviewer did not exclude that test, and "N mutants died" was used as a reason to stop
  reviewing. A false-negative testing tool is worse than none, because it is used to
  justify confidence. #33's mechanical fix (a `driftcheck` marker) is not built; only
  the panel doc's prose warning ships.

- **Concurrent review lenses in one working tree destroy each other's work (severity: H).**
  On #31 the adversarial lens mutated `pr_watch.py` to test it; the correctness lens,
  running at the same time, saw those mutations as an external process corrupting the
  repo and ran `git checkout --` to "restore" it. They fought for ~10 minutes. One
  lens's results were unreliable; when I stopped the other it left a live mutant behind
  (`if False and _PANEL_LENS_NAMES:`) that **silently disabled a guard in my working
  tree**, and I caught it only because a test failed citing an error string that should
  no longer have existed. Already fixed as contract item 7 (isolated worktrees) and
  `.gitignore`/`init.sh` entries, so this is recorded for the pattern rather than as an
  open item: **any doctrine that says "run N reviewers concurrently" owes them
  isolation**, and mine did not until it bit.

- **Deleting a check reintroduced the bug it was masking (severity: M).**
  The roster check removed from #31 was the only thing catching `,` as punctuation in
  `--lenses` — so `"adversarial, focused on the merge gate"` (an honest way to record
  ONE lens) rendered as two, suppressing the one-lens warning that was the field's
  entire remaining value. The commit that deleted it quoted that exact input as an
  example of what it still blocked. **Fixed inside #31** — recorded for the pattern. **Lesson worth generalising:** when removing a
  mechanism as unfit, enumerate what it was rejecting and confirm each case is either
  still rejected elsewhere or deliberately allowed — the deletion commit did neither.

- **Four rounds of tightening a matcher is the signal to delete it, and the rule
  already says so (severity: M, pattern).**
  `safety-critical-changes.md` rule 1: *"Treat 'we tightened the matcher' as a stopgap,
  not a fix."* On #31 I tightened it four times before accepting that. The adversarial
  panel told me by round 3 that the artifact was unverifiable from the engine — same
  actor, same invocation, nothing bound to what ran — and I built two more epicycles
  before acting on it. **Proposed fix:** rule 1 could name a threshold ("a second
  tightening of the same matcher is a design signal, not a bug fix") so the decision
  point is written down rather than requiring the author to notice it.
