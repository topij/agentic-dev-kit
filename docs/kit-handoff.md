# agentic-dev-kit — Living Plan (Handoff)

> **Forward-looking handoff (Principle #1).** Read this at the start of every session
> (`/session-start`); update it at the end (`/wrap-up`). This file — not an agent's
> memory, not a scratch note — is the single source of truth for what's done, in
> progress, and next.
>
> **Why `kit-*.md` and not `handoff.md`:** `docs/handoff.md` is the *skeleton shipped to
> adopters*, rendered from `docs/templates/` by `init.sh`. If this repo pointed its own
> plan at that file, every session block here would ship into adopters' repos and the
> unrendered marker would be gone. An adopter's config uses the plain names; only the
> template repo needs this indirection.
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-08-20 — two merges across two repos, `main`'s own protection found to be convention, and a session whose claims were what review kept catching.

## Latest session — 2026-08-20 (the enforcement under the gate, and an author who was the unreliable narrator)

**Theme —** cross-repo. `#525` shipped here (`#95`'s forgery route at `#521`'s site, squash `6201af6`); `ci-gate`
shipped in the cs-toolkit adopter (`4e743dc3`). Both PRs' review rounds found real defects and
**every one was in the record prose, not the mechanism** — the diffs came through clean and the
narration did not.

- **`#524`: this repo's `main` is protected by convention only.** No classic protection
  (404), `rules/branches/main` empty, the sole ruleset `dont-delete-main` left
  `enforcement: disabled` since it was created. `scripts/hooks/pre-push` guards only
  `dev/*` pushes touching the narrative files, so a direct push to `main` reaches its
  `exit 0`. The kit ships the rule it does not enforce on itself. An enable script is
  with the operator; **not applied** — the finding stands until it is.

- **The adopter is better protected than the kit.** cs-toolkit's ruleset requires a PR
  (0 approvals) but carries no `required_status_checks`. Closing that meant a `ci-gate`
  aggregate job rather than a protection edit, because most of its checks are
  matrix-generated and requiring those names wedges every PR the moment a package moves.
  Tracked adopter-side; `CUS-1307` (nothing enforces `ci-gate.needs` stays complete) and
  `CUS-1308` (`always()` vs `!cancelled()` on a gate job) came out of its review.

- **`#372`: `#525` was reviewed, and this session's first account of it was wrong.** The
  request at the converged head *completed* — as a comment-only clean review naming its
  range (`6905aac` → `89939c0`) and reporting zero units remaining. The bot corrected the
  record on the ticket before this block was written. What made it look like silence: the
  acknowledgement comment was **mutated in place** into the review, and a poll that counts
  comments cannot see an update — `#509`'s mutable-surface hazard, paid. `#525` is therefore
  `#44`'s comment-only shape (a detection problem), and the adopter's `#2044` is the quota
  one; they are not one cause. `#498`'s convergence-only ruling **did** take effect: the one
  unit was spent on the merging head, which is what it was for.

- **`#518` got its field evidence and the line works.** `⚠ review owed` fired unprompted at
  `#525`'s converged head and was acted on rather than merged past. `#522` reproduced in the
  same output — the `✅ DONE — green, reviewed` banner sits four lines above it.

- **Filed this session: `#524`; `CUS-1307`, `CUS-1308`. Occurrence comments on `#372`,
  and the cs-toolkit routing audit on `CUS-1306`.** That audit's finding: the `paths:` glob
  binding the operator-merge rule exists only in `.claude/rules/`, so the runtime entering
  through `AGENTS.md` gets the doctrine with no file list at all — `#243`/`#273`'s failure,
  live in an adopter. Bidirectional drift, so it needs a merge and not a copy.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on the `#525` branch,
  and `make check-root` at `/Users/topi/Coding/in-parallel/cs-toolkit` — both passed, exit 0.
  Counts deliberately not restated: the commands own them, and each PR's own record carries
  the figure at the sha it was taken from.

**Learned**

- **A measurement taken from a still-running workflow read as a finished one.** A CI-cost
  figure was gathered with a `.jobs[] | select(.conclusion != null)` filter while the run was
  in flight; the filter silently dropped the unfinished jobs, including the long pole, and the
  partial set was reported as the total — into a commit message and a PR body, off by
  roughly fourfold. This is `settle_grace_minutes`' own failure mode committed by hand, one
  layer up: a count cannot tell you it is incomplete. Assert the run is `completed` before
  reading any figure off it.

- **The correction was wrong too, in the opposite direction.** The `if: always()` claim was
  repaired once and still false — GitHub documents `always()` as running "even when
  canceled", which is why its docs recommend `!cancelled()`. The delta pass caught it against
  primary sources. The third version asserts only what holds either way. `fallback-review-panel.md`'s
  "shorten, don't correct" is the rule that would have skipped two rounds.

- **Both lenses found the same structural gap from opposite directions**, and neither found
  it in the diff — the adversarial lens hunting a bypass, the correctness lens checking claims
  against the tree, both landing on `ci-gate.needs` having no enforcement. Disjoint lenses
  converging is the panel doctrine's claim; this is an instance of it.

- **A delegated implementer left its work uncommitted on `main` and stalled awaiting a
  notification that was never coming.** Nothing was pushed, so nothing was violated — the only
  thing preventing a commit to `main` was the agent not getting that far, which is `#524`
  demonstrating itself the same hour it was filed.

- **A CHANGELOG placeholder cannot survive this repo's own suite.**
  `test_real_changelog_headings_match_the_extraction_pattern` runs against the real file, so a
  `#TBD` heading fails `make test` by construction. Any split where an implementer pushes and
  the cockpit opens the PR hits this; the number has to be substituted before the suite can pass.
  Related to `#507`.

▶ Next: `#524` is the session's own unfinished business — the enable script is drafted and
unapplied, and until it runs every ground rule about `main` here rests on agents obeying it.
Behind it: `#44`/`#509` are where `#372`'s remaining weight sits now that the review turned
out to have happened and the gate could not see it, and `#310` is still the operator decision
nobody has made.

______________________________________________________________________

## Session — 2026-08-19 (a gate predicate used to answer a report's question, and a review the gate could see)

**Theme —** `#518` shipped (`#520`, squash `ab2bdad`): the converged head now names each
configured reviewer that has not looked at it. The line's first cut was wrong, and wrong
again in a second way after the first fix; the panel caught both before they reached
`main`. `#518` stays open — nothing verified its acceptance criteria in the field.

- **What shipped.** `⚠ review owed` at convergence, per configured bot, gated on the
  reviewer read having succeeded. `pr-watch.md`'s converged step settles that request
  *before* reading `mergeable` and says an already-true `mergeable` does not discharge it —
  which is the exit ramp `#516` took out of the loop. Reported only: the gate is untouched
  and a `fallback:panel` receipt still authorizes while the line still prints.

- **The defect worth carrying past this PR: a merge-gate predicate is not a report
  predicate.** The line read `qualifying_bot_coverage`, which under-reports *by design*
  because it feeds a gate, where under-reporting refuses a merge and is harmless. In a
  report the same bias asserts nobody reviewed the diff — false both where a bot had
  objected on the head and where the check read had failed, each reproduced before
  acting. Both lenses found it independently. In the friction log as
  a doctrine candidate; deliberately not a ticket — the instance is already handled in `#520`, and the
  general shape is the part worth keeping.

- **`#95`'s forgery, one namespace over.** The suppression trusted `_match_bot` over a check
  **name** — a substring match — so a same-repo workflow holding `checks: write` could
  silence "nobody has reviewed this" on its own PR. `review_bots.pending` now carries
  `identity`/`trusted`, and `blocking` deliberately does not read them so the gate stays
  fail-closed.

- **Filed this session: `#521` (the same forgery against the pre-existing coverage warning,
  which `#520` deliberately did not widen into), `#522` (the `DONE` banner says "reviewed"
  four lines above `review owed`).** Occurrence comments on `#506` and `#372`.

- **Verified:** `make test` at the repo root on merged `ab2bdad` — 1304 passed, exit 0.

**Learned**

- **`#372`: the request at the converged head produced a review the gate could see.**
  `@coderabbitai full review` at `#520`'s converged head produced a real review object and
  satisfied the `bot-coverage` route with no receipt needed. Read it against the runs
  already on that ticket rather than on its own: `#501`, where the request produced
  nothing, and `#519`, where it produced a genuine review that no detection route could
  see. What separates this run from those is unclassified, and the caution that ticket already
  carries about the detection routes is untouched by a run that happened to be detected.
  It did find a real defect the panel had missed, which is evidence against treating the
  panel as a standing replacement for the reviewer — one of the three postures `#372` is
  held open to decide.

- **`#506`'s shape recurred in a variant its own remedy does not catch.** Separate terms of
  one `if` were pinned by nothing, each found only by mutation and none by reading — by
  either lens, or by the author. The sharpest: an assertion placed in the neighbouring
  sibling test, whose fixtures carry an unacked comment and therefore never converge, so it
  passed while asserting nothing about a state it could not construct. "Extend the sibling's
  test" is *how it got there*. The occurrence on `#506` proposes the sharpening — a new term
  needs a case where that term alone decides the outcome.

- **The panel and the bot found disjoint defects, in both directions.** The lenses found the
  gate-predicate inversion and the forgery route; the bot then found a `CHANGELOG` sentence
  that was true when written and made false by a later bullet in the same entry, which the
  panel had read past. Neither substitutes for the other, which is what the panel
  doctrine claims and what this session observed rather than assumed.

▶ Next: `#518` and `#372` both want field evidence, and the next PR against this `main` is
the cheapest source of it — open with `session-start` and let the poll speak. Specifically:
does `⚠ review owed` fire at convergence and get acted on without prompting, and does a
second explicit request at the converged head deliver a review object the way `#520`'s did
and `#501`'s did not. Behind those: `#521` is a clean self-contained build, and `#310` is
still the operator decision nobody has made.

______________________________________________________________________

## Session — 2026-08-18 (a triage sweep, an overclaim the wrap-up's own panel caught, and `#372`'s data point at last)

**Theme —** ran `triage-friction-log` on the inbox that had rebuilt since `#470`'s
2026-08-14 sweep, filed the batch, and ran `pr-watch` on the resulting PR. CodeRabbit
never reviewed `#516` — the same `reviews: []`, no-request shape `#499` and `#500`
already showed the day `#498` landed, not a first occurrence as this block's own
first draft claimed (caught by this PR's own fallback panel before it reached
`main`).

- **Triaged the friction log: filed `#506`–`#515` and occurrence comments on `#372`,
  `#467`, `#435`, merged `#516`** (squash `3f25620`). Engine still not vendored
  (`#6`); run by hand against the workflow's prose. Approval was a Slack "lgtm"
  bulk-approve.
- **The fallback panel (adversarial + correctness) found two real things and disposed
  of both without touching `#516`'s diff.** `#508`'s body had dropped its source
  entry's safety caveat when condensed from the friction log — fixed directly via
  `gh issue edit` (a tracker-side edit costs no review round). The marker's own
  "fifteen accounted for" arithmetic reads as off-by-one on a literal skim (it is
  correct: 11 entries via issues + 4 via three comments) — logged rather than fixed,
  filed as `#517`.
- **`#516` merged with no CodeRabbit review object at all** (`gh pr view 516 --json
  reviews` → `[]`). The check-surface-unavailable rule fired on the very first poll —
  `auto_review.enabled: false` posts the skip notice at PR-open now, every time — and
  the panel satisfied `mergeable` before convergence, so the Converged step's own
  "request a review" bullet was never revisited. Filed as `#518`: that bullet is
  unconditional on `review_bots.coverage`, but reads, once a panel receipt already
  exists, like something already handled.
- **A hand-splice mistake in the archive sweep** (consumed the previous sweep's own
  section heading, orphaning its intro paragraph) was caught only by diffing the
  archive's pre-existing content against `origin/main` before committing — no damage
  landed. Occurrence recorded on `#6`.

**Learned**

- **All 15 friction-log entries this round were already issue-shaped — zero needed
  the inbox's waiting-room function.** Fresh evidence for `#310`'s claim (open since
  `08-05`) that `wrap-up` step 5 parks what the routing doctrine already says to file.
  The operator asked about this live; no new ticket needed, `#310` already names the
  fix — undecided whether to implement it or just add the occurrence.
- **`#516`'s non-attempt is at least the third instance, not the first.** This
  block's own first draft claimed `#516` was the first live PR since `#498`'s ruling 2
  to go unreviewed — wrong, caught by this PR's own fallback panel: `#499` and `#500`
  (2026-08-17, same day as `#498`) already merged with `reviews: []` and no request
  ever posted. `#501`, later that same day, is the only prior PR to have actually
  attempted the explicit request — twice, both empty, cause unclassified — and its
  ticket comment says a later PR is needed before ruling further.
- **`#372` has a data point, and it is stranger than "the request works."** An
  explicit `@coderabbitai full review` on `#519` produced a genuine completed review
  — clean verdict, full walkthrough, "0 remain after this review". First read
  against `review_bots.comment_verdicts` showed it picked up; re-checked live before
  this line was written, and it does not — the one comment carrying that verdict is
  the *same* comment CodeRabbit posted at PR-open with the "review skipped, auto
  reviews disabled" notice, edited in place to append the walkthrough **without
  removing the skip text**, so the comment now matches an `unavailable_markers` entry
  and disqualifies itself. Structurally, right now: `reviews: []` and
  `comment_verdicts: []` both — this PR currently has no detectable independent
  review at all, despite CodeRabbit having genuinely produced one. The mutable-comment
  problem this file already named on `2026-08-17` just defeated its own documented
  workaround, live, in this PR.

▶ Next: `#372` needs this written up properly — the explicit request *can* produce a
real review, but neither of this repo's two detection routes (`reviews[]`,
`comment_verdicts`) reliably see it once the vendor's in-place edit adds the skip
notice back onto the same comment. Whether that argues for a third detection route,
a different bot config, or accepting the fallback panel as the standing reviewer is
the operator's call — not pre-empted here. `#518` still stands separately: the loop
needs to actually reach the request step before any of this happens automatically.
Behind it: whether to act on `#310` (occurrence comment vs. implementing its
routing fix — operator hasn't
decided).

______________________________________________________________________

## Session — 2026-08-17 (three rulings shipped, and the defect that would have reached an adopter was a heading)

**Theme —** the operator ruled on `#372` and on `#44`, and `#494` — the fail-open the
previous session's ticket sweep had just filed against `#488` — was closed between them.
Shipped: `#372` (`#498`, squash `9f912e5`), `#494` (`#499`, `fa8d490`), `#44` (`#500`,
`4276654`). All three issues stay open; no closing keyword was written and nothing
verified their acceptance criteria.

- **`#372` ruled: convergence-only — and the first PR that tested it failed.**
  `auto_review.enabled: false`, so the one hourly unit is spent at the head that merges
  rather than the head that opens. The measurement that decided it is on the ticket: on
  `#488` the auto pass at open and the Converged re-request **competed for the same
  unit**. Paying was declined by the operator on cost, which discharges the conditional
  deferral the 2026-08-15 ruling had left standing.

  **Do not read this as a working posture.** `#501` — this wrap-up's own PR, and the
  first the ruling actually governs — requested review at its converged head and
  **`gh pr view 501 --json reviews` stayed empty**: no review object, no coverage, no
  verdict. That puts ruling 2 in question on the one ground that matters: it moved the
  whole review budget onto a request path that then did not deliver. Ruling 1
  (`auto_incremental_review: false`) is untouched and still measured. The account and the
  options it leaves are on `#372`; the next PR against this `main` is the second data
  point.

  **The evidence is stated as the empty review list on purpose.** The bot's own status
  comments rewrite themselves in place, and successive readings of one comment on `#501`
  gave different accounts of what had happened — two of which reached this file or that
  ticket before being corrected. **How many times it was rewritten is not knowable**:
  `updated_at` exposes only the most recent edit, so any count is a floor, and the count
  I first wrote here was wrong before the commit landed. That is the point rather than an
  aside — a tally off that surface is a claim about when you looked. The absent review
  object is not.
- **`#44` ruled: report it, never gate on it.** `review_bots.comment_verdicts` surfaces a
  comment-borne clean verdict; no gate reads it. Direction (a) — parse it into `coverage`
  so the gate self-clears — was declined because the failure modes are not symmetric:
  keying the *gate* on a reviewer's prose lets an upstream wording change decide merges,
  while keying a *report* on it lets a line go missing. `bot_review_coverage`'s docstring
  was already the standing argument, and is cited rather than restated.
- **`#494`'s fail-open shipped a fix: the objection now has its own read** over verdict
  states only. Directions 2 and 3 were declined on the ticket. The two reductions are one
  parameterized walk, not two copies — `#447` (the record for that shape) is why.
  Worded this way deliberately: "`#494` closed by …" reads on a skim as the *ticket*
  being closed, which it is not.

**Learned**

- **Three rulings' worth of panel found no gate defect; the thing that would have reached
  an adopter was a CHANGELOG heading.** `#499`'s entry was headed with the *issue* number,
  and `upgrade.md` Step 3 extracts by *PR* number — so a `BREAKING (gate semantics)` entry
  would have been invisible to the documented upgrade path (`#430`'s failure, on the file
  written to prevent it). Found because a lens **ran** the extraction rather than reading
  the file. Nothing in CI checks this correspondence.
- **`#447`'s shape recurred three times in one session**, each time found by mutation and
  never by reading: a new field added beside pinned siblings inherits exactly the gaps the
  siblings had already closed (`#499`'s objections scoping; `#500`'s config key and its
  render line). Logged to the inbox as a candidate rule rather than a ticket, because the
  third occurrence is what makes it a pattern.
- **Every fix round in this session produced a prose imprecision the next round found.**
  That is the doctrine's own claim observed under its own procedure, and it is the
  argument for the log-don't-fix carve-out — the cost of a round is another round's worth
  of new prose to get wrong.
- **A trigger heuristic `#44` had relied on since 2026-07-27 is falsified:** an explicit
  review request does *not* reliably produce a review object. Recorded on the ticket with
  the observation, and it retires "just re-request it" as operational advice.

▶ Next: open the next PR and watch what its converged-head review request does — that is
`#372`'s second data point and it decides whether ruling 2 stands, gets reverted, or is
renamed to "the panel is the reviewer". Behind it: `#460` (the last standing operator
ruling, untouched today) and `#489` (an unparseable `submittedAt` still outranks every
real timestamp, so a standing objection cannot yet be fully relied on even after `#494`).

______________________________________________________________________

## Session — 2026-08-16 (the receipt route closed, an upstream bypass left open, and a posture whose halves compete for one unit)

**Theme —** `#485` shipped (`#488`, squash `5449947`) — the hole the previous block called
the sharpest of its new tickets. Worth carrying: why direction 2 beat direction 1, what the
panel found underneath the fix, and a `#372` measurement that refuted its own first reading
within the hour.

**What is and is not closed**, because the two are one function apart and the distinction
governs whether the gate can be relied on: `#485`'s **receipt route** is closed — no
receipt satisfies the new blocker. `#489` is a **separate, pre-existing bypass upstream of
it**: an unparseable `submittedAt` makes the coverage read pick the wrong review, so the
objection never becomes the latest state and the blocker never fires. Untouched by `#488`,
verified byte-identical to `main`, and open. Nothing here should be read as "a standing
objection can now always stop a merge."

- **`#485` ruled direction 2, and shipped.** `build_report` raises its own
  `merge_blockers` entry from the configured bot's latest review state at the head
  (`objecting_bot_coverage`); no receipt satisfies it. **Direction 1 — refuse inside
  `record_review` — was declined on ordering**, and that is the transferable half: a
  record-time refusal catches only the objection-first sequence, while the realistic one is
  a receipt taken *while the bot is rate-limited*, then the bot recovering and objecting at
  that same head, by which point `record_review` has returned. Merge-time evaluation catches
  both and the no-receipt case besides. No override flag — the head binding is the release
  valve. `#486` folded in, because that PR writes a **second copy** of the
  `covers_head is True` clause pair and a pinned copy beside an unpinned one is how `#447`
  spreads.
- **Filed from the panel:** `#489` (an unparseable `submittedAt` outranks every real
  timestamp — disarms the new blocker *and* forges `#350`'s evidence route; pre-existing,
  verified byte-identical to `main`), `#490` (a no-op commit clears a standing objection),
  `#491` (`unavailable_markers` conflates an outage with a bot configured not to review this
  head, and prescribes the panel for both). `#485` and `#486` closed by hand.
- **`#372` now has the measurement it was held open for**, on the ticket rather than
  restated here — including which direction the reading changed under.
- **Correcting the block below, which lists `#465` as a standing operator ruling:** its
  work shipped the day before that block was written (`#478`). `#465` and `#350` are both
  shipped-and-still-open — no closing keyword was written, by the discipline, and nothing
  retired them. Left open here rather than closed on my own judgement: I verified the
  shipping commit for each, not their acceptance criteria.

**Learned**

- **The `#372` correction is the decision-grade part.** My first comment framed the gap as
  "`pr_watch.py` has no request path", implying a mechanism closes it. I then performed the
  request by hand and the quota refused it. `auto_review` at open and the Converged
  re-request **compete for the same hourly unit**, so automating the request changes *when*
  the refusal arrives, not *whether*. The correction sits beneath the claim on the issue.
- **`#490` is a composition, not a defect in either half.** The head binding is what makes
  the blocker unwedgeable; the receipt is self-reported by design. Each is justified alone;
  together they leave a no-op commit as a clearance path. Neither ticket that argued for
  its half could have found it.
- **The panel's attestation earned its keep separately from its findings.** The correctness
  lens *executed* the REST-vs-`gh` transport claim I had written from reading — it held —
  and both lenses excluded `driftcheck` from their mutation runs, the false-kill trap this
  kit documents.
- **My own prose overclaimed twice, both caught before anyone else read them.** A test
  docstring claimed to pin an *ordering* that `build_report` cannot observe, since it reads
  final state; and the `#372` comment above. `#422`'s subject, twice in one session.

▶ Next: rule on `#372` — it now carries the measurement it was held open for, and the
reading changed mid-session. `#491`'s direction depends on which way it goes, and `#490`'s
only complete fix is blocked on it. `#460` is the other standing operator ruling.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

