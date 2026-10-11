# PR watch

Watch a pull request until it is **green and clean** — CI fully passing and every
review-bot / human review finding fixed or replied-to — then report. This is the loop
your project's "PR follow-through" policy mandates after opening or pushing to a PR;
run it without being asked.

It is for interactive sessions only: a scheduled job that opens its own PRs should be
excluded from this loop by your cron/CI runner's env signal (any of `DEVKIT_CI_ENV_VARS`,
default `JOB_NAME,CI,GITHUB_ACTIONS,GITLAB_CI,BUILDKITE`), so an automated open
never silently enters an unattended watch loop.

**Input:** an optional PR number. With none, the current branch's open PR is used.

## Reference files

This workflow is split so that each of its files fits in a single read. The files below
are part of the workflow and are as normative as this one; a section cited here by name,
or as *above* or *below*, may sit in any of them. **Read every one of them completely,
not in part, before the first action of any run**, whatever its entry, mode or phase.

- [`pr-watch/report-fields.md`](pr-watch/report-fields.md) — *Seen state and comment
  filtering*, *Review-bot status*, *Evidence findings*, *The REST backend*, *Review
  configuration*, *Review evidence and merge blockers*, *The review request at
  convergence*, *Round counting* and *The all-comments view*.

## Ready and draft policy

Open pull requests **ready for review by default**. Ready status invites review; it
does not grant merge authority. A workflow that reserves merge for the operator still
opens its completed work ready. Immediately after ready creation, run `--assert-ready`
before the watch-and-fix loop; it corrects a silently drifted draft bit before review
bots are expected to start.

Draft is the bounded exception for a **material unfinished-work window** that must
exist on the remote pull request before the work can be completed — for example, when a
required forge-hosted validation cannot run until the pull request exists. If the branch
can be completed and validated locally first, finish it and open ready. Do not use draft
merely to signal risk, broad scope, human review, or operator-held merge authority.

The run that takes the exception owns both ends of it: create with `--draft`, run
`--assert-draft`, finish and push the material work, complete the body, then run
`gh pr ready` and `--assert-ready` before starting the watch-and-fix loop. A scheduled
or unattended run may take that route only when the same run can perform the ready
transition; a hook that deliberately skips unattended execution is not a substitute.

Read `config/dev-model.yaml` first. Resolve `<engine-dir>` from `paths.engines`.
When a configured review bot is unavailable, the substitute pass is the
**panel** in `review.fallback_panel` — read
[`../fallback-review-panel.md`](../fallback-review-panel.md) before running it.
`review.fallback_commands` is the degraded one-lens mode for a runtime that
cannot isolate a reviewer.

**Tune the review settings for your own bot mix in `config/dev-model.yaml`, never in
the engine.** Editing the literals inside `<engine-dir>/pr_watch.py` forks the engine and turns every
later kit update into a merge conflict. Custom bots must list differing author logins
explicitly under `review.bot_author_aliases`. Leave `review.require_ci` `true` unless
the repo genuinely has no CI — with no checks and `require_ci: true`, `converged` can
never flip and `dev_session.sh merge` will always refuse. Setting it `false` leaves
current-head independent-review evidence as the only quality gate, so set it
deliberately.
*Review configuration*, in `report-fields.md`, says what each key does.

If the diff affects a customer-facing gate, destructive operation, recovery path,
or other configured high-risk file, read and apply
`docs/agentic-dev-kit/safety-critical-changes.md`. Green CI alone is not merge
approval for that class.

Engine: `<engine-dir>/pr_watch.py` (deterministic — check rollup + comment union across
issue/review/inline surfaces, noise-filtered, diffed against a per-PR seen-set). You
drive the loop + apply the judgment.

**LOW/P3 findings take delta review or a ticket, never a full-process restart.**
Apply [LOW findings: delta review or ticket](../fallback-review-panel.md#low-findings-delta-review-or-ticket)
to bot, human and fallback findings alike. Batch contained repairs, verify their
affected behavior and preserve prior review evidence; otherwise file and link the
deferred work. A new LOW finding does not restart full suites, whole-PR panels,
delivery stages or approval rounds. Required CI, initial review coverage, formal
change requests and higher-severity blockers remain separate obligations.

For a lane coordinated from the cockpit, invoke the same engine through
`<engine-dir>/dev_session.sh pr-watch <scope> ...`. That scope-aware wrapper pins the
repository and stores polls, acknowledgments, and review receipts in the lane sandbox
that `dev_session.sh merge <scope>` re-checks.

**Without `gh`, the engine polls but cannot authorize a merge** (*The REST backend*, in
`report-fields.md`). `converged` works normally, which is the point: you can run the
watch-and-fix loop from a session without `gh` and hand the merge back to one that has
it. `dev_session.sh pr-watch <scope>` itself needs `gh`, so a gh-less session must
invoke the engine directly, and on a **fork** checkout pass an explicit PR number.

## Loop

Repeat until the report says **converged**:

1. **Poll.** `uv run <engine-dir>/pr_watch.py <PR#> --json` (omit `<PR#>` for the current
   branch). Read `converged`, `mergeable`, `checks` (`all_green`, `failing[]`, `pending`),
   `merge_blockers[]`, `review_evidence`, `review_bots`, `evidence_findings[]`,
   `review_rounds`, and `new_comments[]`.

   The two predicates answer different questions and you need both:

   - **`converged`** — "is there more for me to fix?" Green, nothing new, not
     settling. This is what ends *this* loop.
   - **`mergeable`** — "is this authorized to merge?" `converged` **plus** no
     `merge_blockers[]` **plus** independent-review evidence bound to the current
     head. This is what `dev_session.sh merge` re-checks.

   **Independent-review evidence has two routes, and `review_evidence.route` says
   which one answered** (`#350`): `receipt`, a `--record-review` receipt bound to
   this head, and `bot-coverage`, a configured review bot's own review of this exact
   head. *Review evidence and merge blockers*, in `report-fields.md`, says what each
   route accepts and how the unsettled-rollup and requested-changes blockers below
   behave.

   A PR can be `converged` and not `mergeable` — most commonly because neither route
   is satisfied yet. That is the normal, expected state at the end of the loop, not a
   failure.

   The other routine reason is a `merge_blockers[]` entry reading
   **`check rollup has not settled for current head`**. **Poll again rather than
   working around it:** it clears on its own, with no intervention. It never
   blocks `converged`, so it cannot stall this loop — only the merge that
   follows it.

   A third routine blocker reads **`configured review bot requested changes on
   current head: <bot>`** (`#485`), and **no receipt disposes of it**. It never
   blocks `converged`, so the loop still ends normally. **Clear it the ordinary
   way: address the findings and push.** A maintainer dismissing the review on the
   forge clears it too, and so does the reviewer itself re-reviewing this same head
   and approving. A later `COMMENTED` or `PENDING` review by the same bot leaves it
   standing.

   `done` also appears in the report. It is a **legacy alias for `mergeable`**, kept
   so that an older `dev_session.sh` still gates on merge authorization. Prefer
   `converged` / `mergeable`; never assume `done` means "the loop finished."

1. **If `review_bots.unavailable` contains an entry whose `surface` is `check` and
   `review_bots.blockers` is empty and the current head has no valid
   `review_evidence`:** run `review.fallback_panel` and record its receipt against
   the report's exact `head`, even when `new_comments[]` contains no outage notice.
   A check description can be the only trusted current outage surface; waiting for
   a comment in that case leaves `converged` true but `mergeable` permanently
   blocked. A historical comment-only outage is not sufficient for this branch —
   unseen comments follow the existing path below, while an acknowledged old
   comment must not preempt a live pending bot on a later head. When another
   configured reviewer is still pending, its blocker also defers the panel:
   `--record-review` would refuse, so running the panel early only repeats work.
   Re-poll until `review_bots.blockers` is empty. After recording, re-poll. If valid
   current-head evidence already exists, keep the outage visible but do not rerun
   the panel.

   **What this records is a substitute review, not a request** (`#518`). The
   receipt satisfies the merge gate and is meant to — the panel is the sanctioned
   stand-in for a reviewer that cannot answer. What it must not stand in for is
   having *asked*, which is owed at the converged head whether or not a receipt
   already exists. Running the panel here is therefore never the reason to skip the
   request below.

1. **If `converged`:** stop the loop and report — PR #, the green check count, and
   "no outstanding review findings." **Then, before anything else, settle the
   review request the Converged stop condition below owes.** The poll answers
   this for you: when it prints `⚠ review owed`, it names the configured
   reviewers that have not reviewed this head — request one from each, at this
   head, now. **Key off that line rather than re-deriving it from
   `review_bots.coverage` alone.** Coverage is one of the four things the engine
   weighs: it also suppresses the line for a reviewer that answered in a comment
   (`#44`), for one whose review is still in flight, and whenever the reviewer
   read itself failed — so a condition rebuilt from coverage by hand asks for
   reviews the engine already knows are unnecessary. Then record the independent
   review (see below) so the PR becomes `mergeable`.

   **A `mergeable` that is already true does not discharge that request** (`#518`).
   The panel branch above can fire on the *first* poll — a reviewer configured not
   to auto-review announces that at PR-open, so the check-surface condition is true
   before CI has even settled — and its receipt can therefore make `mergeable` true
   before the loop ever converges. The PR then reads as finished. On `#516` that is
   exactly what happened: `gh pr view 516 --json reviews` returned `[]`, the
   configured reviewer never saw the diff that merged, and every value in the report
   was correct throughout. Report that `mergeable` was already true; do not read it
   as the end of this step.

1. **If checks are still `pending` and there are no new comments:** nothing to do yet
   — wait and re-poll (see Pacing). CI can take 20–30 min; that's expected, keep
   going.

1. **If a check is `failing`:** investigate (`gh run view <run-id> --log-failed`, or
   `gh pr checks <PR#>`), fix the cause in the code, run your project's local gate
   (e.g. `make check`), commit, and `git push`. The push re-triggers CI — keep
   looping.

1. **If there are `new_comments`:** handle each with judgment —

   - **Reviewer unavailable** (`review_unavailable_reason` is set — rate limit,
     skipped review, no credits), current-head `review_evidence` is invalid, and
     `review_bots.blockers` is empty: run the **fallback review** the poll's
     `review_class` owes, one isolated fresh-context reviewer per lens. A
     safety-critical PR takes the panel, every lens in `review.fallback_panel`; a
     standard PR takes one lens, the one *How many lenses* in
     [`../fallback-review-panel.md`](../fallback-review-panel.md) names. Read that
     file for the contract each lens gets; it is what makes the pass independent
     of you. A blocked bot
     is an action signal, never auto-noise or a review waiver. Acknowledge the
     notice only after every finding is handled, then bind the pass to the exact
     `head` from the poll you reviewed:

     ```sh
     uv run <engine-dir>/pr_watch.py <PR#> \
       --record-review "<review.fallback_panel.receipt_source>" \
       --lenses <names of the lenses that ran> --head <polled-sha> \
       --disposition -   # findings and how each was disposed, on stdin
     ```

     A standard PR's one lens records `--record-review "fallback:lens"` with
     `--lenses` naming that lens; the engine refuses `fallback:lens` on a PR it
     classes safety-critical or cannot class.

     `--lenses` names what actually ran, so a degraded one-lens pass is
     distinguishable from a panel in the audit trail. It is **self-reported** —
     the engine records it and shows it at merge time, but cannot verify it. If your
     runtime cannot isolate a reviewer, run `review.fallback_commands` instead
     and record it as `fallback:<runtime>` with the single lens named. A further
     single-lens receipt is the **delta pass** for record prose or LOW repairs (the panel
     doc's stopping section): an isolated lens over a fix round's delta,
     recorded as the literal `fallback:delta` with its one lens named — never
     `fallback:<runtime>`, which is reserved for the author-context degraded
     run — plus `--compose-parent <last-reviewed-sha>`. That flag preserves the
     standing full-pass receipt, records the reviewed delta boundary and exact
     changed paths, and makes ancestry/path drift invalidate merge evidence. For a
     lane, use `<engine-dir>/dev_session.sh pr-watch <scope>` with the same flags.
     If current-head evidence is already valid, do not rerun the panel; keep the
     outage visible and acknowledge the notice as an already-covered round. An
     outage announced *after* the configured bot already reviewed this exact head
     leaves qualifying coverage behind it, so the evidence blocker is already
     satisfied and there is nothing for a panel to add. Read
     `review_evidence.route` rather than inferring from the outage.
     If another reviewer is pending, leave the notice unacknowledged and re-poll;
     the blocker must clear before the panel runs or its receipt will be refused.

   - **Untrusted outage candidate** (the entry carries
     `untrusted_review_unavailable_candidate`, rendered `[untrusted reviewer-outage
     candidate]`): a legacy prefix-like author carrying an outage marker, surfaced on
     its first unseen poll. It blocks convergence until handled, but never counts as
     reviewer evidence. Like every handled comment, it no longer reappears after
     `--mark-seen`; add the exact login to `review.bot_author_aliases` only after
     verifying it so future notices are authenticated.

   - **LOW/P3 finding:** use the delta-or-ticket rule above, including for a
     low-severity regression. Do not restart the full process.
   - **Real finding** above LOW (a bug, a missing guard, a correctness/clarity issue): fix it in
     the code, commit, push. Re-running the local gate first. **Before that push, take
     the step after this list**, *Count the round before you fix it*: record the
     round and check the budget.
   - **Nitpick you disagree with** (style preference, out-of-scope, already-correct):
     **reply with a brief reason** rather than changing code — `gh pr comment <PR#>
     --body "..."` for a top-level reply, summarizing what you addressed vs. skipped
     and why.
   - Verify each finding against the *current* code before acting — some go stale
     across rounds (a later commit already fixed it).

1. **Count the round before you fix it.** A review that leaves findings to fix
   records no receipt yet, so record the round itself, against the head that was
   reviewed:

   ```sh
   uv run <engine-dir>/pr_watch.py <PR#> --record-round --head <reviewed-sha> \
     --lenses <names of the lenses that ran>
   ```

   It writes no review evidence and gates nothing; it is what
   `review.round_budget` counts. It needs the `gh` backend, like `--record-review`.
   `--head` is the reviewed commit's hex sha, full or abbreviated, and may be the PR
   head or an ancestor of it. A ref such as `HEAD~1` or a branch name is refused,
   because it would resolve against your checkout, which can be stale.
   A configured bot's submitted review counts its own head, and `--record-review`
   counts the head it binds, so neither needs this, with one exception: a bot
   review whose findings are only inline comments under an empty body is not
   counted (`#981`), so record that round. Then read the poll's `review_rounds`:
   **if `spent` is true, do not push the fix round unless an operator go-ahead on
   the PR covers it** — go to *Round budget* under Stop conditions.

1. **Acknowledge the round:** once you've handled this round's findings, run `uv run
   <engine-dir>/pr_watch.py <PR#> --mark-seen` so they don't resurface. `--mark-seen` never
   re-polls `gh` — it promotes the exact set of comment keys that your last `--json`
   poll reported (persisted locally in the per-PR state file as a "pending" set) into
   the seen-set, then clears it. This makes the ack deterministic: a comment that
   lands on the PR *after* your read-poll and *before* `--mark-seen` was never part of
   that pending set, so it can't be acked by this call — it stays unseen and surfaces
   on your next poll instead of being silently buried. Calling `--mark-seen` without a
   prior poll (nothing pending) acks nothing and says so (`note` in the output) —
   always poll-and-read first.

1. **Record the independent pass — when there is one to record.** If
   `review_evidence.route` is already `bot-coverage`, the configured bot reviewed
   this exact head and **nothing should be recorded**: the gate is satisfied, and
   every available `<source>` literal names a fallback pass that did not run
   (`#350`). Recording one there is a false receipt, not a formality.

   Otherwise run `--record-review <source> --head <polled-sha>`
   only after the human or fallback reviewer has completed and all
   findings are resolved. `<polled-sha>` is the `head` field from the exact poll whose
   diff was reviewed. Recording fails if the PR head changed in the meantime. The
   receipt is persisted with that exact `headRefOid`; any later push invalidates it and
   requires another independent pass. A platform `APPROVED` state is still recorded
   explicitly so the engine never assumes that an approval predates no later push.
   Marking comments seen never creates review evidence.

   The pending block only exists once the bot has *registered* a check. In the
   window between `gh pr ready` and the bot creating its check row, "the bot
   hasn't started yet" is indistinguishable from "this repo has no bot", so a
   receipt recorded in that window is still premature. Give a freshly-readied PR
   a poll or two before recording one.

   `--allow-pending-bot-review` lets `--record-review` proceed while a configured
   bot's own check is still pending. Use it only with evidence the queued verdict
   will never arrive; it is recorded on the receipt as `override`, because it is
   exactly the scenario a premature receipt exists to prevent.

   **Pass `--disposition` with it, and pass what the review found.** The receipt
   records `source`, `lenses`, `head` and `recorded_at` — the reviewed revision
   and who looked, never the findings — and it is written into the per-PR state
   file, which is gitignored. Without a disposition on the pull request, the
   review evidence does not survive the merge (`#604`). The flag takes the text,
   or `-` to read it from stdin, and posts it as one comment bound to the
   recorded head, under a heading the engine fixes so the next poll can find it
   again, and acknowledges that comment in the same write so it does not come
   back as a finding to address. One comment per round is enough. A failed post
   refuses the whole command and records no receipt: re-run it. When the poll's
   `evidence_findings[]` carries `review_disposition_missing`, the remedy is
   `--record-review --disposition`; a hand-written comment under some other heading
   does not clear it, because the check reads the marker the engine writes rather
   than matching prose.

1. **Pace the next poll** (see below), then go to step 1.

## Read-only act-time poll

The normal poll persists the report's comment acknowledgment set, check-count
baseline, head, and bot-pending clock so the interactive loop can make progress.
That is intentional during the loop, but it is the wrong side effect for a final
authorization probe that must not silently acknowledge anything the operator has
not read. Use:

```sh
uv run <engine-dir>/pr_watch.py <PR#> --json --no-persist
```

`--no-persist` performs the same current-state reads and builds the same report,
but leaves the per-PR state file unchanged. It is valid only for a plain poll; it
cannot be combined with `--mark-seen`, `--record-review`, `--record-round`,
`--assert-draft`, or `--assert-ready`. A merge wrapper should use this mode for its last `mergeable`
check, after the normal watch-and-acknowledge loop has finished.

`--all-comments`, valid only with `--json` on a plain poll, adds `all_comments[]`
to the report; *The all-comments view*, in `report-fields.md`, describes it. The
watch loop does not need it, because `new_comments[]` is its view.

## The draft-bit flags — they CORRECT, they do not check

`--assert-draft` and `--assert-ready` are documented in `pr_watch.py`'s own docstring,
used by the ready/draft policy above, and noted under *The REST backend*, in
`report-fields.md`. Their names badly undersell what they do. Read this before using
either.

**Both mutate the PR.** Despite "assert", neither is a read-only check. Each reads
`isDraft`, and if it does not match, issues the corrective `gh pr ready` (for
`--assert-ready`) or `gh pr ready --undo` (for `--assert-draft`), then re-reads to
confirm. So:

```sh
uv run <engine-dir>/pr_watch.py 916 --assert-draft   # right after `gh pr create --draft`
uv run <engine-dir>/pr_watch.py 916 --assert-ready   # after ready creation/transition, and before merge
```

Running `--assert-ready` on a PR you *deliberately* left as a draft will **flip it to
ready for review**, at which point a review bot may pick it up. That is the opposite of
a safe read-only probe, so never use either as a way to "check" PR state.

They exist because `gh`'s draft bit is flaky in both directions (observed on gh 2.89.0):
a `--draft` create can silently land non-draft, and a ready PR can silently revert to
draft so a later `gh pr merge` fails with *"Pull Request is still a draft"*. Exit 0 means
the bit held **or was corrected**; exit 2 means the correction did not take.

Both **require `gh`** — they mutate, and the REST fallback refuses them with exit 2, as
it does `--record-review` and `--record-round`.

## Pacing

Self-pace on a bounded cadence — don't busy-wait:

- **Review bots** land their first pass ~2–5 min after a push. Poll ~every 180–270 s
  while waiting on them (stays inside the prompt-cache window).
- **CI** can run 20–30 min. While only checks are pending, a longer 300–600 s cadence
  is fine.
- After you push a fix, expect a fresh CI run + possibly a re-review — keep looping;
  don't declare done off a stale poll.
- A transient `merge state is UNKNOWN` blocker is expected immediately after GitHub
  receives new state; re-poll until it resolves. `BLOCKED`, `DIRTY`, `BEHIND`, a
  draft bit, or `CHANGES_REQUESTED` needs action rather than acknowledgment.
- `UNSTABLE` remains blocking unless every real check is green and its only remaining
  status contexts are names explicitly classified as informational by the engine. A
  current-head independent-review receipt is still required in that case.

## Stop conditions

- **Converged** — `converged: true` (green + clean). Report and finish. This is the
  goal of the loop. State `mergeable` too: convergence is not merge clearance.
  - **If the current head has no review coverage, request a review here.** Read
    `review_bots.coverage`: an entry whose `covers_head` is false — or no entry at
    all — means nothing has reviewed the diff that is about to merge. Convergence
    is the moment the merge head stops moving, so it is the moment to spend one
    review on it: request at the current head, then poll on.

    **Poll on means poll on: never wait on the request's outcome.** An
    acknowledgement is not evidence a review is coming. Where automatic review at
    PR-open is turned off, this request **is** the PR's review: prefer the
    reviewer's *complete*-review command over its incremental one.

    **A refused request is an expected outcome, not an error.** It surfaces through
    the ordinary unavailable path above and routes to the fallback panel. Where the
    budget merely needs time to refill, waiting and re-requesting is the cheaper
    answer under the no-auto-review-at-open configuration. Neither is a licence to
    retry in a loop against a quota.

    **A reviewer can answer clearly and still leave the gate unsatisfied.** When the
    poll prints `ⓘ review reported:` (`review_bots.comment_verdicts`), that is a
    report, not evidence: if that verdict is what you are merging on, record it as a
    receipt whose source says what it stands for — `<bot>:comment-verdict`, with
    **no `--lenses`**, since no fallback pass ran. If it is not, run the panel. What
    is not available is treating the missing coverage as a review waiver.

    **Before recording a converged-head `fallback:panel` receipt, re-read the
    bot's status comment once — the body, never the count** (`#372`). A genuinely
    delivered clean verdict of this head takes the `<bot>:comment-verdict` receipt;
    where the panel already carries the merge, note the bot's review on the PR
    rather than letting the record say it never happened.

    The engine makes no request itself; its `⚠ review owed` line says when one is
    owed and from whom. Do not `--record-review` the bot's own verdict: a
    bot-reviewed head needs no receipt, because its coverage is the evidence
    (`#350`). *The review request at convergence*, in `report-fields.md`, gives the
    reasons behind each rule in this bullet.
  - **A verification stamp behind the head.** When `evidence_findings[]` carries
    `verification_stamp_behind_head`, none of the pull request's verification stamps
    names the current head. Stamps are read from the body **and** from every comment,
    so a final stamp posted as a comment at the merged head clears it — that is the
    form to use.
- **Stuck / needs a decision** — a check fails for a reason you can't resolve (a
  flaky-infra failure that won't clear on re-run; an external dependency; a finding
  that needs an operator product/design call). Stop, report the specific blocker, and
  ask. Don't loop forever on something only the operator can unblock.
- **Round budget** — a pull request's review gets the opening review plus
  `review.round_budget` fix rounds. A round is a distinct head that a review covered,
  whoever reviewed it. The poll reports the count as `review_rounds`; once it reaches
  the limit, `review_rounds.spent` is true and the text render prints `⚠ round budget
  spent`. When reviewing the current head would itself go past the limit,
  `review_rounds.next_round_needs_operator` is true as well. Each round costs a review
  and a CI run, in every repository that runs this loop; `#305` and `#666` hold
  occurrences where fix rounds' own repairs carried the next finding.

  **When the budget is spent and the last review left findings to act on, stop.** Do
  not push another fix round. Post one comment on the PR, the **decision packet**:

  - each open finding, with the severity and regression label its reviewer gave it,
    and what fixing it would touch;
  - the LOW findings already routed to tickets, linked;
  - the options: merge with the remaining findings ticketed, authorize a stated
    number of further rounds, split the change, or withdraw the repair that grew.

  When the head moved without findings, such as a CI fix after the last review, the
  packet says what moved it and asks for the one review the new head needs.

  Then report the PR as held for the operator and end the loop. The operator's answer
  goes on the PR. A go-ahead names how many further rounds it covers, and the poll keeps
  printing the warning through them, because the count does not reset. A LOW finding
  needs no go-ahead to be ticketed; fixing it takes one, as below.

  *Round counting*, in `report-fields.md`, says when the count runs under or over
  the fix rounds taken.

  Past a spent budget, a LOW fix is a fix round like any other: pushing it, and the
  `fallback:delta` review its head then needs, takes the operator's go-ahead.
  Without one, the LOW finding takes the ticket.

  **What the budget does not do.** It moves neither `converged` nor `mergeable`, and it
  waives nothing. A finding above LOW that is still open is not merged past by an agent
  on budget grounds; that call is the operator's. The blast-radius rules in
  [`../fallback-review-panel.md`](../fallback-review-panel.md) still decide which
  findings a round acts on, and a safety-critical pull request stays operator-merge.
  If the last review covered the current head and left nothing to act on, the spent
  budget changes nothing: finish the loop as usual. A red check is not a review round, so fixing it needs no go-ahead.
  The head that fix produces is unreviewed, though, and once the budget is spent its
  review needs one like any other.
- **Bound the loop** — if you've gone ~8–10 polls of fixing without converging, for any
  reason (red checks included), stop and summarize where it stands rather than looping
  indefinitely. This bounds *this* loop — poll, fix, acknowledge — whatever the change
  is; the round budget above bounds only review rounds. Neither is licence to stop
  polling a red PR.
