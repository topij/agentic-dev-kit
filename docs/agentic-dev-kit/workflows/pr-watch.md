# PR watch

Watch a pull request until it is **green and clean** — CI fully passing and every
review-bot / human review finding fixed or replied-to — then report. This is the loop
your project's "PR follow-through" policy mandates after opening or pushing to a PR;
run it without being asked.

**Input:** an optional PR number. With none, the current branch's open PR is used.

Read `config/dev-model.yaml` first. Resolve `<engine-dir>` from `paths.engines`.
When a configured review bot is unavailable, the substitute pass is the
**panel** in `review.fallback_panel` — read
[`../fallback-review-panel.md`](../fallback-review-panel.md) before running it.
`review.fallback_commands` is the degraded one-lens mode for a runtime that
cannot isolate a reviewer.

If the diff affects a customer-facing gate, destructive operation, recovery path,
or other configured high-risk file, read and apply
`docs/agentic-dev-kit/safety-critical-changes.md`. Green CI alone is not merge
approval for that class.

Engine: `<engine-dir>/pr_watch.py` (deterministic — check rollup + comment union across
issue/review/inline surfaces, noise-filtered, diffed against a per-PR seen-set). You
drive the loop + apply the judgment.

For a lane coordinated from the cockpit, invoke the same engine through
`<engine-dir>/dev_session.sh pr-watch <scope> ...`. That scope-aware wrapper pins the
repository and stores polls, acknowledgments, and review receipts in the lane sandbox
that `dev_session.sh merge <scope>` re-checks.

## Loop

Repeat until the report says **converged**:

1. **Poll.** `uv run <engine-dir>/pr_watch.py <PR#> --json` (omit `<PR#>` for the current
   branch). Read `converged`, `mergeable`, `checks` (`all_green`, `failing[]`, `pending`),
   `merge_blockers[]`, `review_evidence`, `review_bots`, and `new_comments[]`.

   The two predicates answer different questions and you need both:

   - **`converged`** — "is there more for me to fix?" Green, nothing new, not
     settling. This is what ends *this* loop.
   - **`mergeable`** — "is this authorized to merge?" `converged` **plus** no
     `merge_blockers[]` **plus** independent-review evidence bound to the current
     head. This is what `dev_session.sh merge` re-checks.

   **Independent-review evidence has two routes, and `review_evidence.route` says
   which one answered** (`#350`):

   - **`receipt`** — a `--record-review` receipt bound to this head. Self-reported:
     the agent writes both the source and the lens names, and nothing binds either
     to a review that happened, which is why the render labels it a claim.
   - **`bot-coverage`** — a configured review bot's *own* review of this exact head,
     read from review objects the forge attributes to that bot's identity, with
     `review_evidence.bots` naming which. Nothing is recorded and nothing needs to
     be: this route exists because the receipt vocabulary describes only fallback
     passes, so a bot-reviewed head used to have no honest receipt at all and the
     gate was unreachable exactly when review had gone well.

   The coverage route is deliberately narrow, and everything it cannot see falls
   back to the receipt requirement rather than opening the gate: a review whose
   commit SHA is unusable, a verdict that arrived only as a comment (`#44`), or a
   bot-state read that failed all yield no evidence. A *pending* bot still blocks on
   its own grace window, and an unacknowledged outage notice still blocks
   `converged`.

   A PR can be `converged` and not `mergeable` — most commonly because neither route
   is satisfied yet. That is the normal, expected state at the end of the loop, not a
   failure.

   The other routine reason is a `merge_blockers[]` entry reading
   **`check rollup has not settled for current head`**. The merge gate waits for
   the check rollup to stop changing size before believing it is complete,
   because a partial rollup and a finished one report the same thing — a count,
   with no indication of how many checks are still coming. **Poll again rather than
   working around it:** it clears on its own, with no intervention.

   It reports two wordings — `no settle baseline recorded` (no clock is running)
   and `stable Nm of Mm` (one is). They are states of the same clock, which runs
   only while the rollup stays **the same size it was on the previous poll**.
   A push, a check appearing, and a check *disappearing* all restart it — so
   either wording can follow the other, and **`no settle baseline recorded` can
   reappear** rather than showing once. The same wording covers a stored stamp
   that is unusable at all — unparseable, the zero time, or one meaningfully in
   the future (a state file copied between machines, or a clock corrected
   backwards) — which fails closed like everything else here.

   Neither wording is a deadline: the gate opens once that has been true for
   `review.settle_grace_minutes` continuously. A rollup that dips and returns to
   its old count does **not** get credited the time before the dip. It never
   blocks `converged`, so it cannot stall this loop — only the merge that
   follows it.

   A third routine blocker reads **`configured review bot requested changes on
   current head: <bot>`** (`#485`). The configured reviewer has an unresolved
   objection to *this exact commit*, and **no receipt disposes of it** — a receipt is
   self-reported by the agent seeking the merge, so it cannot answer for another
   reviewer. It never blocks `converged`, so the loop still ends normally.

   **Clear it the ordinary way: address the findings and push.** That moves the head,
   leaves the objection covering an older commit, and the blocker clears on the next
   poll — there is deliberately no override flag. A maintainer dismissing the review
   on the forge clears it too. It is bound to the head precisely so that fixing the
   thing the reviewer asked for is what resolves it.

   **A third route exists and is legitimate: the reviewer itself re-reviewing
   this same head and approving.** No push, no dismissal — the bot changed its
   mind, which is a reviewer withdrawing an objection rather than an author
   getting around one, and it leaves a forge audit trail like the other two.

   **What is now a property rather than a description** (`#494`) is that those
   three are the *only* routes. The objection is read from each bot's latest
   *verdict* — `APPROVED`, `CHANGES_REQUESTED`, `DISMISSED` — so the same bot
   posting a `COMMENTED` or `PENDING` review afterwards, at the same head, leaves
   it standing. It used to clear it: the read was taken from the bot's latest
   review of any kind, which meant an ordinary follow-up review erased the
   objection *and* then supplied the independent-review evidence, needing no
   commit, no dismissal, and no act by anyone. If you are wondering why your
   reviewer's own later comment did not unblock the merge, that is the reason,
   and it is deliberate.

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

1. **If `converged`:** stop the loop and report — PR #, the green check count, and
   "no outstanding review findings." Then record the independent review (see below)
   so the PR becomes `mergeable`; if `mergeable` is already true, say so.

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
     `review_bots.blockers` is empty: run the **fallback review panel** —
     `review.fallback_panel`, one isolated fresh-context reviewer per lens. Read
     [`../fallback-review-panel.md`](../fallback-review-panel.md) for the contract
     each lens gets; it is what makes the pass independent of you. A blocked bot
     is an action signal, never auto-noise or a review waiver. Acknowledge the
     notice only after every finding is handled, then bind the pass to the exact
     `head` from the poll you reviewed:

     ```sh
     uv run <engine-dir>/pr_watch.py <PR#> \
       --record-review "<review.fallback_panel.receipt_source>" \
       --lenses <names of the lenses that ran> --head <polled-sha>
     ```

     `--lenses` names what actually ran, so a degraded one-lens pass is
     distinguishable from a panel in the audit trail. It is **self-reported** —
     the engine records it and shows it at merge time, but cannot verify it. If your
     runtime cannot isolate a reviewer, run `review.fallback_commands` instead
     and record it as `fallback:<runtime>` with the single lens named. The
     other single-lens receipt is the record-prose **delta pass** (the panel
     doc's stopping section): an isolated lens over a fix round's delta,
     recorded as the literal `fallback:delta` with its one lens named — never
     `fallback:<runtime>`, which is reserved for the author-context degraded
     run. For a
     lane, use `<engine-dir>/dev_session.sh pr-watch <scope>` with the same flags.
     If current-head evidence is already valid, do not rerun the panel; keep the
     outage visible and acknowledge the notice as an already-covered round.
     If another reviewer is pending, leave the notice unacknowledged and re-poll;
     the blocker must clear before the panel runs or its receipt will be refused.

   - **Real finding** (a bug, a missing guard, a correctness/clarity issue): fix it in
     the code, commit, push. Re-running the local gate first.
   - **Nitpick you disagree with** (style preference, out-of-scope, already-correct):
     **reply with a brief reason** rather than changing code — `gh pr comment <PR#>
     --body "..."` for a top-level reply, summarizing what you addressed vs. skipped
     and why.
   - Verify each finding against the *current* code before acting — some go stale
     across rounds (a later commit already fixed it).

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
cannot be combined with `--mark-seen`, `--record-review`, `--assert-draft`, or
`--assert-ready`. A merge wrapper should use this mode for its last `mergeable`
check, after the normal watch-and-acknowledge loop has finished.

## The draft-bit flags — they CORRECT, they do not check

`--assert-draft` and `--assert-ready` are documented in `pr_watch.py`'s own docstring and
noted under the REST backend in the Notes section below, but nothing says **when** to reach for them,
and their names badly undersell what they do. Read this before using either.

**Both mutate the PR.** Despite "assert", neither is a read-only check. Each reads
`isDraft`, and if it does not match, issues the corrective `gh pr ready` (for
`--assert-ready`) or `gh pr ready --undo` (for `--assert-draft`), then re-reads to
confirm. So:

```sh
uv run <engine-dir>/pr_watch.py 916 --assert-draft   # right after `gh pr create --draft`
uv run <engine-dir>/pr_watch.py 916 --assert-ready   # right before `gh pr merge`
```

Running `--assert-ready` on a PR you *deliberately* left as a draft will **flip it to
ready for review**, at which point a review bot may pick it up. That is the opposite of
a safe read-only probe, so never use either as a way to "check" PR state.

They exist because `gh`'s draft bit is flaky in both directions (observed on gh 2.89.0):
a `--draft` create can silently land non-draft, and a ready PR can silently revert to
draft so a later `gh pr merge` fails with *"Pull Request is still a draft"*. Exit 0 means
the bit held **or was corrected**; exit 2 means the correction did not take.

Both **require `gh`** — they mutate, and the REST fallback refuses them with exit 2, as
it does `--record-review`.

The one remaining flag not used in the loop above is `--allow-pending-bot-review`, which
lets `--record-review` proceed while a configured bot's own check is still pending. Use
it only with evidence the queued verdict will never arrive; it is recorded on the receipt
as `override`, because it is exactly the scenario a premature receipt exists to prevent.

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

    **State the condition as coverage, not as configuration**, because two
    different causes land here and only the observable one catches both. A repo
    that has turned off incremental auto-review (to stop spending a bounded review
    budget on fix rounds — see
    [`../fallback-review-panel.md`](../fallback-review-panel.md), *Before you
    accept the outage as fixed*) has a reviewer that saw the head the PR opened at
    and nothing since. A bot that is merely *behind* reports a completed review
    bound to a stale head, which reads green at a glance. Coverage reports both;
    the config setting reports only the first.

    **How much rides on this request depends on a setting it deliberately does
    not read.** Where automatic review at PR-open is left on, this tops up a
    reviewer that has already seen the opening diff, and skipping it costs
    coverage of the delta. Where a repo has moved its whole review budget here —
    automatic review at open turned *off*, so the one review it can afford lands
    on the head that merges — this request **is** the PR's review, and skipping
    it leaves the diff unreviewed by anyone. Prefer the reviewer's
    *complete*-review command over its incremental one in that case: an
    incremental request is defined against a previous review, which is precisely
    what that configuration arranges not to have.

    **A refused request is an expected outcome, not an error.** The request is
    itself a review request and spends from the same bounded budget, so it can
    arrive to find nothing left. The refusal surfaces through the ordinary
    unavailable path above and routes to the fallback panel — the correct
    disposition, since it means the merging head has no independent review and
    something must supply one. Where the budget merely needs time to refill,
    waiting and re-requesting is the cheaper answer under the
    no-auto-review-at-open configuration, because no unit was spent at open and
    the PR is therefore still owed one. Neither is a licence to retry in a loop
    against a quota.

    Nothing in `pr_watch.py` performs the request — it observes only. And note
    what this bullet does **not** say: it does not tell you to `--record-review`
    the bot's own verdict. That receipt vocabulary describes fallback passes, and
    a bot-reviewed head needs no receipt — its coverage *is* the evidence
    (`#350`, resolved by the `bot-coverage` route above). Recording one there
    asserts a fallback pass that did not run. This is also not a change to
    `converged`, which stays green + clean and deliberately is not merge
    clearance.
- **Stuck / needs a decision** — a check fails for a reason you can't resolve (a
  flaky-infra failure that won't clear on re-run; an external dependency; a finding
  that needs an operator product/design call). Stop, report the specific blocker, and
  ask. Don't loop forever on something only the operator can unblock.
- **Bound the loop** — if you've gone ~8–10 rounds without converging, stop and
  summarize where it stands rather than looping indefinitely. This bounds *this* loop —
  poll, fix, acknowledge — and applies whatever the change is. It is **not** the fallback
  panel's stopping criterion, which is per-change, applies only when your review bot is
  unavailable, and lives in
  [`../fallback-review-panel.md`](../fallback-review-panel.md). Neither one is licence to
  stop polling a red PR.

## Notes

- The seen-set lives at `state/pr-watch/<PR#>.json` (gitignored). It's per-PR, so
  re-running on a different PR starts fresh.
- Known auto-noise from your review bots (walkthrough / "no actionable comments"
  summaries) is filtered out by the engine. Reviewer-unavailable notices are
  deliberately *not* noise: they surface as new comments and so block `converged`;
  acknowledging one clears `converged` but ordinarily still leaves the current-head
  review-evidence blocker on `mergeable` until the panel runs and records its
  receipt. Ordinarily, not always: an outage announced *after* the configured bot
  already reviewed this exact head leaves qualifying coverage behind it, so the
  evidence blocker is already satisfied and there is nothing for a panel to add.
  Read `review_evidence.route` rather than inferring from the outage.
- **A bot's outage is detected on both trusted surfaces, and a queued bot is not a
  finished one.** `review.unavailable_markers` are matched against comments
  authored by the exact normalized login of a configured `review.bots` entry
  (or an alias under `review.bot_author_aliases`) *and* against that bot's
  status-check description — the same rate limit is worded differently on the two
  surfaces, and matching only comments made detection depend on which one the bot
  happened to use. Author scoping matters because tracker mirrors and humans can
  quote outage text without the reviewer being unavailable. A legacy prefix-like
  author carrying an outage marker is surfaced as an **untrusted candidate** on
  its first unseen poll—it blocks convergence until handled, but never counts as
  reviewer evidence. Like every handled comment, it no longer reappears after
  `--mark-seen`; add the exact login to `bot_author_aliases` only after verifying
  it so future notices are authenticated. The report's
  `review_bots` block resolves each bot to:
  - **unavailable** — an outage announced on either surface. Rendered as
    `⚠ review unavailable …`. The status entry itself adds no
    `review_bots.blockers` item, but an unseen notice comment still blocks
    `converged`, and unavailability never satisfies the current-head review gate:
    `mergeable` stays blocked until the configured `review.fallback_panel` runs
    and records a receipt. The outage stays visible after you `--mark-seen` the
    notice comment, so the gap is still readable at merge time. Only a
    **check**-surface outage cancels the pending block below: a check describes
    the bot's state now, while comments are the whole PR history unscoped by
    head — and since rate limits are transient, an old outage comment would
    otherwise wave through every later queued review.
  - **pending** — the bot's own check is non-terminal and no outage was announced.
    A verdict is genuinely coming, so this **blocks `mergeable`** (and makes
    `--record-review` refuse) until the check ages past
    `review.bot_pending_grace_minutes` (default 15), after which the bot is treated
    as never going to report and stops blocking. Use
    `--allow-pending-bot-review` only with evidence the queued verdict will never
    arrive. CodeRabbit's pending check reports no usable timestamp
    (`0001-01-01T00:00:00Z`), so the grace clock falls back to when *this engine*
    first saw the bot pending — persisted per PR under `bot_pending_since`, scoped
    to the head, and reset by a push. A stored value the engine cannot read — or
    one dated in the future — is replaced rather than trusted, so the window stays
    bounded whatever wrote the state file.

  None of this reaches `converged`. That is deliberate and load-bearing: the watch
  loop must be able to finish while a bot that never reports sits pending forever.
  More precisely, none of the `review_bots` status or pending entries above reaches
  `converged`; an unseen outage notice still does through `new_comments`. Those
  status and pending signals feed the merge gate only.

  It also reports **`review_bots.coverage`** — the commit each bot's *last*
  review actually saw. A receipt binds to the head and a push invalidates it,
  which answers "was this exact code reviewed" but not "by whom, and how much of
  it did they see": a bot can review commit 1, go rate-limited through a
  material redesign, and the merge proceed on a fallback receipt taken at commit
  5. When a bot's last review is behind the head the render says so:

  ```
  ⚠ review coverage: coderabbit's last review was of 954b93f, not the current
    head — a receipt taken now would not stand for its review of this design;
    re-request it, or say so explicitly
  ```

  It defers to a bot that is *actively* pending — one mid-review of a just-pushed
  head is behind it by construction, and the pending line already says a verdict
  is coming. It does **not** defer once that check ages past the grace window or
  is cancelled by an announced outage: that is the engine saying the verdict is
  not coming, which is the reviewer-went-away case this exists for.

  `--record-review` records the same gap on the receipt as `bots_behind_head`,
  next to `override` and `bot_signal` — all three say what the receipt does *not*
  stand for. It is recorded even under `--allow-pending-bot-review`, since that
  override is itself the #22/#25 scenario. (Unlike the poll render, the receipt
  does not defer to a pending bot: recording a receipt is the moment the gap
  matters most.)

  Reported, never gating — deliberately the cheap half of the problem, because
  invalidating a receipt on a shape change risks wedging a repo whose bot is
  permanently unavailable.

  Once a current-head receipt exists, every poll also prints what that receipt
  **claims** to cover:

  ```
  review evidence: fallback:panel — 2 lenses claimed (adversarial, correctness)
  review evidence: fallback:codex — ⚠ ONE lens claimed (correctness) — not a dual-lens pass
  ```

  Self-reported: `--lenses` is written by whoever ran `--record-review`, and the
  engine records it without verifying it (issue #32). It is shown here so a
  one-lens pass is visible when a merge is considered rather than only in the
  record command's output. Entries that read as prose rather than a lens name
  are recorded but not counted.

  **Known gaps, so you don't mistake them for coverage:**
  - The `review evidence:` line prints on the **poll render**, which a human
    reads. `dev_session.sh merge` consumes the JSON and gates on `mergeable`
    alone — so on an autonomous self-merge path nobody sees it. That is the gap
    issue #32 exists to close properly; until then, an unattended lane's review
    coverage is only as good as what it recorded.
  - `coverage` reports only bots that have reviewed *and* whose review carried a
    commit SHA. A bot that has never reviewed at all produces no entry and no
    warning — that case is the pending/unavailable machinery's, not this one's.
  - The pending block only exists once the bot has *registered* a check. In the
    window between `gh pr ready` and the bot creating its check row, "the bot
    hasn't started yet" is indistinguishable from "this repo has no bot", so a
    receipt recorded in that window is still premature. Give a freshly-readied PR
    a poll or two before recording one.
  - `review_bots.signal` is `ok` / `skipped` (no bots configured) / `unavailable`
    (the check read failed — e.g. a `gh` too old for the requested `--json`
    fields, or a PR with no checks at all). On `unavailable` **both guards are
    off**; it's reported rather than blocking, because an environment problem
    shouldn't become a wedge — and a receipt recorded while the read was
    `unavailable` carries a `bot_signal` key so the audit trail shows the guard
    didn't run. (`skipped` is not flagged: nothing was unreadable.)
  - An *older* `pr_watch.py` polling the same PR drops the persisted grace clock,
    restarting the window. Merges wait longer; nothing fails open.
- **Without `gh`, the engine polls but cannot authorize a merge.** When the `gh`
  binary is absent it falls back to the GitHub REST API using
  `GH_TOKEN`/`GITHUB_TOKEN` (with neither, it exits 2 saying so). That fallback is
  deliberately **poll-only**:
  - `mergeable` is **false by construction**, with the merge blocker `the REST
    backend cannot authorize a merge — it polls only`. No response from GitHub can
    change that; it is not a judgement about the PR.
  - `--record-review`, `--assert-draft` and `--assert-ready` **refuse** with exit
    2. They write durable evidence or mutate the PR, so they need `gh`.
  - `converged` works normally, which is the point: you can run the watch-and-fix
    loop from a session without `gh` and hand the merge back to one that has it.
  - `report["backend"]` says which transport produced the poll (`gh` / `rest`).
  - Broadening this is tracked as an issue in this repo's tracker; it needs every
    external input to read fail-closed first, so do not lift it casually.
  - Known gaps on the REST path, stated rather than discovered: no GitHub
    Enterprise (`GH_HOST`), no `GH_REPO` (it reads `origin`), no **fork**
    checkouts (the branch lookup reuses the `origin` owner, so a fork queries the
    fork while the PR lives upstream — pass an explicit PR number there), and
    `dev_session.sh pr-watch <scope>` itself needs `gh`, so a gh-less session must
    invoke the engine directly.
- **`truncated_reads`** lists any paginated read that stopped at the page ceiling
  rather than at the end of the data. A truncated read means the poll did **not**
  see every check or comment, so `converged` may be premature — REST list
  endpoints return oldest-first, so what gets dropped is the newest. It gates
  nothing (blocking `converged` would wedge the loop) and is printed by the human
  render as well as carried in the JSON. Empty on the `gh` backend.
- **Tune this for your own bot mix in `config/dev-model.yaml`, never in the engine.**
  `review.bots`, `review.bot_author_aliases`, `review.noise_markers`,
  `review.unavailable_markers`, `review.informational_checks` and
  `review.bot_pending_grace_minutes` are read from config; the engine only carries
  them as fallbacks for a missing config.
  `review.bots` and `review.informational_checks` ship with the *same* value and
  different jobs: the latter is a blocking policy ("this check never blocks the
  watch loop"), the former an identity ("this check belongs to a reviewer whose
  state the merge gate cares about"). Bot names match case-insensitively as a
  **substring** of a check name (your own CI and bot config). Comment authors are
  stricter: only the exact bot key, its conventional `[bot]` form, or an exact
  login configured under `review.bot_author_aliases` is trusted. The shipped
  CodeRabbit aliases cover `coderabbitai` and `coderabbitai[bot]`; custom bots
  must list differing author logins explicitly. This replaces the legacy prefix
  rule—after upgrading, an unseen prefix-like outage comment gets one actionable
  untrusted-candidate warning instead of disappearing as noise. Editing the literals inside
  `<engine-dir>/pr_watch.py` forks the engine and turns every later kit update into
  a merge conflict. A key you omit keeps the kit default; an explicit empty list
  (`noise_markers: []`) means "filter nothing".
- `review.require_ci` (default `true`) is whether a PR must have at least one real,
  non-informational check before it can report green. Leave it `true` unless the repo
  genuinely has no CI — with no checks and `require_ci: true`, `converged` can never flip
  and `dev_session.sh merge` will always refuse. Setting it `false` does **not**
  weaken the review gate: `mergeable` still requires current-head
  independent-review **evidence** by either route above, which then becomes the only
  quality gate — so set it deliberately. Note how the two settings compose:
  `require_ci: false` on a repo with `review.bots: []` leaves the receipt as the single
  gate, since the coverage route needs a configured bot to exist.
- This is interactive-only. A scheduled job that opens its own PRs should be excluded
  from this loop by your cron/CI runner's env signal (any of `DEVKIT_CI_ENV_VARS`,
  default `JOB_NAME,CI,GITHUB_ACTIONS,GITLAB_CI,BUILDKITE`), so an automated open
  never silently enters an unattended watch loop.
