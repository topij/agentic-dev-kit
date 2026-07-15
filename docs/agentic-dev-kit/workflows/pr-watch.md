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

Repeat until the report says **done**:

1. **Poll.** `uv run <engine-dir>/pr_watch.py <PR#> --json` (omit `<PR#>` for the current
   branch). Read `done`, `checks` (`all_green`, `failing[]`, `pending`),
   `merge_blockers[]`, `review_evidence`, and `new_comments[]`.

1. **If `done` (checks all green + nothing new + PR open/ready/mergeable with no
   requested changes + independent review evidence bound to the current head):**
   stop the loop and report — PR #, the green check count, review source, and "no
   outstanding review findings." You're finished.

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

- **Done** — `done: true` (green + clean + current-head independent review evidence).
  Report and finish. This is the goal.
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
  deliberately *not* noise: they surface and block `done`; acknowledging one still
  leaves the current-head review-evidence blocker until the configured fallback runs
  and records its receipt. Edit the marker lists in `<engine-dir>/pr_watch.py` for
  your own bot mix.
- This is interactive-only. A scheduled job that opens its own PRs should be excluded
  from this loop by your cron/CI runner's job-name signal, so an automated open never
  silently enters an unattended watch loop.
