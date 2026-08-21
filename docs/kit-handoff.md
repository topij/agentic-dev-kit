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

Last updated: 2026-08-21 — the adopter's three issues worked to merge, and a review loop that kept finding its own guards rather than the change.

## Latest session — 2026-08-21 (the adopter's findings, and a loop that reviewed its own guards)

**Theme —** cs-toolkit's `/upgrade` findings worked end to end. `#535`'s regression, `#536`'s
items and `#534`'s cause 3 all merged (`#538`, `#544`, `#545`); every one of those issues
stays open, since nothing verified their acceptance criteria in the field.

- **`#535` was upstream of where the issue pointed.** `#521`'s deference was correct; the
  FETCH under it was not — identity resolved only for rows that could cancel a pending
  block, so a healthy mid-review row never had one and `trusted` was never true. The
  precondition now covers both consumers. Fixed in the field on its own PR: `coverage: []`,
  a comment-surface entry with no trust field beside a trusted check entry, and `review
  owed` correctly silent via the check.

- **The panel found the defect the fix introduced, not the one it fixed.** `accounted`
  read `.get("trusted", True)`, and a comment-surface entry carries no such key — so one
  stale acknowledged outage comment would have silenced `review owed` for a PR's whole
  life. `summarize_review_bots`' own docstring forbids exactly that ("a comment is a
  statement about the past"), one layer below where I broke it.

- **After each PR's first round, no finding was in shipped behaviour.** Established by
  diffing each branch's first commit against its head over the files adopters receive:
  no prescribed `upgrade.md` command and no `ENGINE_DIR` substitution changed. Every
  later commit touched a test file and the manifest. All the HIGHs were in guards, several
  in the previous round's guard. Stopping was by blast radius, per the doctrine — not
  because a round came back clean.

- **The reason that was possible is now closed on both.** Each guard was pinned only to
  the real tree, which holds none of the shapes it exists to catch, so the suite could not
  tell a fixed guard from a broken one — lenses proved it by reintroducing earlier bugs
  and watching the suite stay green. Both are pinned on synthetic fixtures now, and
  `#544`'s fixture records which shapes discriminate and which are defence-in-depth,
  rather than implying a clean sweep.

- **Filed this session: `#537`** (the adopter's declined `dev_session.sh` carries a
  merge-gate hardening the kit lacks — the kit's own test certifies the fork), **`#540`**,
  **`#541`**, **`#542`**, **`#543`**, **`#546`**. Occurrence comments on `#325` (panel
  isolation holds for writes and failed for reads; the cockpit's own launch note was the
  mechanism) and a scope comment on `#534`.

- **The operator's unfiled candidates were all filed, none rejected** — `#540`, `#541`,
  `#542`. `#541` went in despite being pre-existing because its consequence
  changed: under coverage alone a truncated reviews list only ever refused a merge; with
  `#488`'s objection blocker reading the same list it can now authorize one.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on each branch head
  before its push, and again on `#545`'s merge commit after taking `origin/main` in. Each
  PR's record carries its own result at the sha it was taken from.

**Learned**

- **Across both files I kept keying a guard on what text LOOKED like instead of asserting
  the required form** — a line wrap, quotes and `=`, a shell continuation, a
  fence tag, a `$ ` prompt; an operator, an attribute, a constructor, a wrapper on the
  other operand. That is `safety-critical-changes.md` rule 1 ("treat 'we tightened the
  matcher' as a stopgap") and I did not see the shape until a lens had refuted the fifth.

- **The completeness claim was the more reliable defect than the code.** Round after
  round I declared a class closed and a lens found another member. Asserting closure is
  worse than leaving a gap open, because the assertion gives the next reader a reason to
  stop looking — the draws that finally worked named my own worst track record and asked
  the lenses to attack it.

- **A rule that binds one surface does not bind the author writing another.** `wrap-up.md`
  forbids a count beside a list; I broke that in docstrings and commit messages all
  session, each time in the commit that grew the list. Filed as `#546` — it is `#243`'s
  shape applied to surfaces rather than runtimes, and it tensions with `#54`, which asks
  for a command's actual result.

- **A lens verifying a declared LIMITATION is worth more than one confirming a claim.**
  The round that added most was one that built the real defect in a real scanned file and
  watched the guard pass over it, and one that checked my stated gaps were honest rather
  than that my stated capabilities worked.

▶ Next: `#537` — the merge-gate scrub the adopter's fork carries and the kit lacks. It was
blocked on `#534` cause 3, which merged today, so the test that pins it can now be written
against the kit's own `dev_session.sh` rather than an adopter's.

______________________________________________________________________

## Session — 2026-08-20 · afternoon (the third ruling, and the panel that corrected its own transcription)

**Theme —** executed the morning briefing's plan end-to-end. `#524` applied; `#372` ruled
(third ruling: the panel is the standing reviewer, detection surface frozen — the ruling
and its same-day correction are on the ticket); the ruling's doctrine follow-up plus three
delegated fixes driven through the full panel loop to merge. Squashes on `main`: `#529`
(upgrade.md `${KIT:?}` guards, addresses `#496`), `#530` (`review_evidence.head` nulled on
the bot-coverage route, addresses `#495`), `#528` (pr-watch.md converged step carries the
ruling), `#527` (manifest tracks the kit's own test suite, addresses `#493`). All four
issues stay open — nothing verified their acceptance criteria in the field.

- **The gap `#524` names is shut at the forge: ruleset `protect-main` is `active`** — PR required
  (0 approvals), `toolkit` required and pinned to the GitHub Actions `integration_id`
  (`#95`'s identity rule applied to the forge gate), deletion + non-fast-forward kept, no
  bypass actors. Verified: `gh api repos/topij/agentic-dev-kit/rules/branches/main` lists
  all four rule types, run from this repo's root.
- **The session's sharpest event: `#528`'s adversarial lens executed
  `bot_comment_verdicts()` against the live history and refuted the ruling it was
  reviewing the transcription of.** The ruling's receipt-time-re-read item had conflated
  `#519`'s conjunction-disqualification with `#525`'s count-blind hand-rolled loop — the
  engine would have seen `#525` — and carried a figure that measured the blind loop, not
  the bot. Corrected on `#372`; the fix round shortened rather than corrected, and round 2
  found only lens-labeled cosmetic Lows on the shortened text.
- **The ruling was field-tested the same afternoon, on the ticket:** `#529`'s
  converged-head request delivered a comment-only clean review the `ⓘ review reported`
  line caught; `#530`'s, a minute later, hit the quota wall, reported on both surfaces;
  `⚠ review owed` fired at both convergences. Neither outcome was waited on; both merges
  stood on dual-lens `fallback:panel` receipts.
- **`#527` took three rounds** (finding → fix → merge-resolution). The round-3 re-run over
  a "mechanical" merge delta found a real Medium (`#532`) — evidence against inventing a
  cheaper carve-out for merge-resolution deltas.
- **Filed this session: `#531`** (an adopter's own `conftest.py` misjudged via the
  engine-role basename), **`#532`** (KIT_OWNED role labels pinned by nothing — the guards
  derive their universe from the tuple they guard). Occurrence comments: `#372` (ruling,
  correction, two request outcomes), `#480` (executed evidence: `cd ""` is a no-op success
  in bash/zsh/sh; the false prose claim beneath the patched block; the test-name
  overclaim), `#496` (behavioral-pin residual), `#506` (`#532`'s shape). Caps posted on
  `#44` and `#509` — records and occurrence landing places now, not build backlog.
- **The cs-toolkit upgrade boundary is reached (`#504`):** precondition 1 by the `#372`
  ruling, precondition 2 by `#529`/`#530`/`#527` shipping the `#497` fix set. `kit_doctor`
  now drift-checks vendored tests — the exact hazard `#493` measured on that repo.
- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on each PR's final
  branch head before its push — each PR's record carries its own summary line.

**Learned**

- **A ruling written from the trail's latest occurrence comment inherited the trail's
  uncorrected layer.** The refuting evidence route was execution, not reading — the same
  lesson the lens contract's "Execute, don't only read" already carries, arriving on the
  record-authoring side.
- **This morning's delegate-stall friction entry recurred with its proposed fix applied
  verbatim and not binding.** What bound was a follow-up naming a concrete 600000ms
  timeout for the verification command: the stall is timeout-shaped, not
  obedience-shaped — `#514`'s carrier-not-wording, again.
- **Two same-session converged-head requests competed for the hourly unit a minute
  apart** — the first delivered, the second walled. Under the panel-as-reviewer posture
  that budget is corroboration, not review capacity, so this costs nothing.

▶ Next: run `/upgrade` on cs-toolkit — `#504`'s preconditions are both met. At upgrade
time re-run the CHANGES_REQUESTED sweep (non-zero pulls `#499` ahead), and fold CUS-1293
(`panel_prompt.py`: copy it or document the decline) and CUS-1306 (merge the
operator-merge `paths:` glob into the shared doc) into the same pass. Behind it: `#532`
is a clean self-contained build; `#310` is still the operator decision nobody has made.

______________________________________________________________________

## Session — 2026-08-20 · morning (the enforcement under the gate, and an author who was the unreliable narrator)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

