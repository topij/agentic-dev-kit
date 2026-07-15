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

## Loop

Repeat until the report says **done**:

1. **Poll.** `uv run <engine-dir>/pr_watch.py <PR#> --json` (omit `<PR#>` for the current
   branch). Read `done`, `checks` (`all_green`, `failing[]`, `pending`), and
   `new_comments[]`.

1. **If `done` (checks all green + nothing new):** stop the loop and report — PR #,
   the green check count, and "no outstanding review findings." You're finished.

1. **If checks are still `pending` and there are no new comments:** nothing to do yet
   — wait and re-poll (see Pacing). CI can take 20–30 min; that's expected, keep
   going.

1. **If a check is `failing`:** investigate (`gh run view <run-id> --log-failed`, or
   `gh pr checks <PR#>`), fix the cause in the code, run your project's local gate
   (e.g. `make check`), commit, and `git push`. The push re-triggers CI — keep
   looping.

1. **If there are `new_comments`:** handle each with judgment —

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

1. **Pace the next poll** (see below), then go to step 1.

## Pacing

Self-pace on a bounded cadence — don't busy-wait:

- **Review bots** land their first pass ~2–5 min after a push. Poll ~every 180–270 s
  while waiting on them (stays inside the prompt-cache window).
- **CI** can run 20–30 min. While only checks are pending, a longer 300–600 s cadence
  is fine.
- After you push a fix, expect a fresh CI run + possibly a re-review — keep looping;
  don't declare done off a stale poll.

## Stop conditions

- **Done** — `done: true` (green + clean). Report and finish. This is the goal.
- **Stuck / needs a decision** — a check fails for a reason you can't resolve (a
  flaky-infra failure that won't clear on re-run; an external dependency; a finding
  that needs an operator product/design call). Stop, report the specific blocker, and
  ask. Don't loop forever on something only the operator can unblock.
- **Bound the loop** — if you've gone ~8–10 rounds without converging, stop and
  summarize where it stands rather than looping indefinitely.

## Notes

- The seen-set lives at `state/pr-watch/<PR#>.json` (gitignored). It's per-PR, so
  re-running on a different PR starts fresh.
- Known auto-noise from your review bots (billing/usage notices, walkthrough / "no
  actionable comments" summaries) is filtered out by the engine — edit the
  noise-marker list in `<engine-dir>/pr_watch.py` for your own bot mix; those never count
  as findings.
- This is interactive-only. A scheduled job that opens its own PRs should be excluded
  from this loop by your cron/CI runner's job-name signal, so an automated open never
  silently enters an unattended watch loop.
