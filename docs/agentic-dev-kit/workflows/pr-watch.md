# PR watch

Watch a pull request until it is **green and clean** — CI fully passing and every
review-bot / human review finding fixed or replied-to — then report. This is the loop
your project's "PR follow-through" policy mandates after opening or pushing to a PR;
run it without being asked.

**Input:** an optional PR number. With none, the current branch's open PR is used.

Read `config/dev-model.yaml` first. Resolve `<engine-dir>` from `paths.engines`,
and select the current runtime's independent fallback from
`review.fallback_commands` when needed.

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
   `merge_blockers[]`, `review_evidence`, and `new_comments[]`.

   The two predicates answer different questions and you need both:

   - **`converged`** — "is there more for me to fix?" Green, nothing new, not
     settling. This is what ends *this* loop.
   - **`mergeable`** — "is this authorized to merge?" `converged` **plus** no
     `merge_blockers[]` **plus** an independent-review receipt bound to the current
     head. This is what `dev_session.sh merge` re-checks.

   A PR can be `converged` and not `mergeable` — most commonly because no review
   receipt has been recorded yet. That is the normal, expected state at the end of
   the loop, not a failure.

   `done` also appears in the report. It is a **legacy alias for `mergeable`**, kept
   so that an older `dev_session.sh` still gates on merge authorization. Prefer
   `converged` / `mergeable`; never assume `done` means "the loop finished."

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
     skipped review, no credits): run the current runtime's configured
     `review.fallback_commands` pass. A blocked bot is an action signal, never
     auto-noise or a review waiver. Acknowledge the notice only after the fallback
     review has completed and every finding from it is handled. Then record the
     pass against the exact `head` from the poll you reviewed with `uv run
     <engine-dir>/pr_watch.py <PR#> --record-review "fallback:<runtime>" --head
     <polled-sha>`. For a lane, use `<engine-dir>/dev_session.sh pr-watch <scope>
     --record-review "fallback:<runtime>" --head <polled-sha>` instead.

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

1. **Record the independent pass:** run `--record-review <source> --head <polled-sha>`
   only after the configured bot, human, or fallback reviewer has completed and all
   findings are resolved. `<polled-sha>` is the `head` field from the exact poll whose
   diff was reviewed. Recording fails if the PR head changed in the meantime. The
   receipt is persisted with that exact `headRefOid`; any later push invalidates it and
   requires another independent pass. A platform `APPROVED` state is still recorded
   explicitly so the engine never assumes that an approval predates no later push.
   Marking comments seen never creates review evidence.

1. **Pace the next poll** (see below), then go to step 1.

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
- **Stuck / needs a decision** — a check fails for a reason you can't resolve (a
  flaky-infra failure that won't clear on re-run; an external dependency; a finding
  that needs an operator product/design call). Stop, report the specific blocker, and
  ask. Don't loop forever on something only the operator can unblock.
- **Bound the loop** — if you've gone ~8–10 rounds without converging, stop and
  summarize where it stands rather than looping indefinitely.

## Notes

- The seen-set lives at `state/pr-watch/<PR#>.json` (gitignored). It's per-PR, so
  re-running on a different PR starts fresh.
- Known auto-noise from your review bots (walkthrough / "no actionable comments"
  summaries) is filtered out by the engine. Reviewer-unavailable notices are
  deliberately *not* noise: they surface as new comments and so block `converged`;
  acknowledging one clears `converged` but still leaves the current-head
  review-evidence blocker on `mergeable` until the configured fallback runs and
  records its receipt.
- **A bot's outage is detected on both surfaces, and a queued bot is not a finished
  one.** `review.unavailable_markers` are matched against comment bodies *and*
  against the status-check description of any check belonging to a configured
  `review.bots` entry — the same rate limit is worded differently on the two
  surfaces, and matching only comments made detection depend on which one the bot
  happened to use. The report's `review_bots` block resolves each bot to:
  - **unavailable** — an outage announced on either surface. Rendered as
    `⚠ review unavailable …`, and it never blocks anything: it's the action signal
    to run `review.fallback_commands`. It stays visible after you `--mark-seen` the
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
  Every signal here feeds the merge gate only.

  It also reports **`review_bots.coverage`** — the commit each bot's *last*
  review actually saw. A receipt binds to the head and a push invalidates it,
  which answers "was this exact code reviewed" but not "by whom, and how much of
  it did they see": a bot can review commit 1, go rate-limited through a
  material redesign, and the merge proceed on a fallback receipt taken at commit
  5. When a bot's last review is behind the head the render says so:

  ```
  ⚠ review coverage: coderabbit's last review was of 954b93f, not the current
    head — a receipt taken now does not mean it saw this design
  ```

  Reported, never gating — deliberately the cheap half of the problem, because
  invalidating a receipt on a shape change risks wedging a repo whose bot is
  permanently unavailable. Treat it as the prompt to re-request a review, or to
  say plainly what the receipt does and does not cover.

  **Known gaps, so you don't mistake them for coverage:**
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
- **Tune this for your own bot mix in `config/dev-model.yaml`, never in the engine.**
  `review.bots`, `review.noise_markers`, `review.unavailable_markers`,
  `review.informational_checks` and `review.bot_pending_grace_minutes` are read from
  config; the engine only carries them as fallbacks for a missing config.
  `review.bots` and `review.informational_checks` ship with the *same* value and
  different jobs: the latter is a blocking policy ("this check never blocks the
  watch loop"), the former an identity ("this check belongs to a reviewer whose
  state the merge gate cares about"). Bot names match case-insensitively: as a
  **substring** of a check name (your own CI and bot config) and as a **prefix**
  of a comment author (anyone may comment on a public PR, so `xcoderabbit` must
  not be able to speak for the reviewer). `coderabbit` covers the check
  `CodeRabbit` and the author `coderabbitai` either way — keep entries specific
  enough not to collide with a CI job name. Editing the literals inside
  `<engine-dir>/pr_watch.py` forks the engine and turns every later kit update into
  a merge conflict. A key you omit keeps the kit default; an explicit empty list
  (`noise_markers: []`) means "filter nothing".
- `review.require_ci` (default `true`) is whether a PR must have at least one real,
  non-informational check before it can report green. Leave it `true` unless the repo
  genuinely has no CI — with no checks and `require_ci: true`, `converged` can never flip
  and `dev_session.sh merge` will always refuse. Setting it `false` does **not**
  weaken the review gate: `mergeable` still requires a current-head
  independent-review receipt, which then becomes the only quality gate — so set it
  deliberately.
- This is interactive-only. A scheduled job that opens its own PRs should be excluded
  from this loop by your cron/CI runner's env signal (any of `DEVKIT_CI_ENV_VARS`,
  default `JOB_NAME,CI,GITHUB_ACTIONS,GITLAB_CI,BUILDKITE`), so an automated open
  never silently enters an unattended watch loop.
