# Autonomous session operating contract

> **Scope — operator-gated.** This contract applies **only when the operator explicitly
> requests an autonomous session** (e.g. "run an autonomous session on X", "work this
> autonomously", "autonomous chore sprint"). It does **not** govern normal interactive
> sessions, where the operator drives PR review and merge.
>
> Your CLAUDE.md's Branching + PR-follow-through rules (see
> [`CLAUDE-sections.md`](CLAUDE-sections.md)) are the always-on baseline; this is the
> autonomous **superset**. Its distinguishing behaviors are **self-merging low-risk work**
> and **not yielding the turn until the work is merged**. The always-on guardrails still
> hold — pause before security-sensitive changes, and respect whatever data-handling /
> PII confirmation rules your project's CLAUDE.md defines; a broad-but-sensitive config
> file (a customer/contact roster, a secrets manifest, anything similar) is never for
> unsupervised bulk migration by an autonomous pass.

Follow this top to bottom, per ticket.

## PR lifecycle / merge model — don't yield the turn until merged

### Branch hygiene

- Branch from fresh `<config vcs.protected_branch>` (typically `main`):
  `git checkout <protected_branch> && git pull --ff-only`, then
  `git checkout -b <user>/<ticket>-<slug>` (or `chore/<slug>`). **NEVER commit directly to
  the protected branch.**
- **ALWAYS check `git branch --show-current` before any commit.** A stray edit made on the
  protected branch carries onto the next branch via `checkout -b` — verify every time.

### Sequencing — coupled vs independent

- **File-coupled tickets go SEQUENTIALLY** — each fully merged before the next branches off
  the updated protected branch. Tickets that share the same module, schema, or shared-state
  file race each other if stacked; a squash-merge makes a new commit on the protected branch
  and orphans the source branch a child PR targeted, so a dependent PR opened against an
  unmerged sibling silently never lands.
- Genuinely-independent work (disjoint files) may run in parallel.

### Local gate (before every push)

- Run your project's local gate (lint + typecheck + tests) on every changed file before
  pushing — replace this line with your project's actual command(s). If your gate has a
  known footgun (a stale build artifact, a cache that needs a forced reinstall, a test
  runner that needs a specific virtualenv), document the workaround here once you hit it,
  so the next autonomous session doesn't rediscover it the hard way.
- If a package/module has its own stricter gate (a typecheck pass, an integration-test
  suite), run that too whenever you touch it.

### Open → validate → ready

- Push `-u`, open a **draft**: `gh pr create --draft`.
- **Risk gate:**
  - Low-risk display / derivation change → straight to ready (self-merge path).
  - A change to a cache shape, a data fetcher, or anything that touches shared/production
    state → **live-validate against the real target first**: write a throwaway harness
    that exercises the changed function directly against production-shaped input before
    trusting it. Do **not** commit regenerated artifacts produced only for validation.
- Then `gh pr ready <PR#>`.

### Watch-and-fix loop (do NOT yield until green + clean)

- Seed the seen-set for whatever review-tracking tool your kit provides (e.g. the
  `/pr-watch` skill's `--mark-seen` flag), so you only react to *new* signal on later polls.
- Poll in a **background** loop and wait on task notifications so the turn stays alive
  instead of blocking on a foreground sleep. Break on: done (checks green + `merge_state`
  clean + no unresolved findings) | any check failing | (nothing pending and a new comment
  landed); poll on a bounded cadence (tens of seconds, not minutes).
- Your configured review bots (`review.bots` in `config/dev-model.yaml`) may not reliably
  re-review every incremental push — after fixing, confirm your fix-commit lands after the
  bot's last review rather than waiting indefinitely for a re-review that may not come.
  Fix real findings (commit + push → re-watch); reply-with-reason to nitpicks you keep. If
  every configured bot is unavailable (rate-limited, no credits, skipped the PR), run
  the current runtime's `review.fallback_commands` value as the substitute independent pass — a blocked bot is not a
  waiver on review.

### Merge + close out

- Merge only once checks are green, the PR is mergeable, and every finding has been fixed
  or explicitly addressed:
  ```sh
  gh pr merge <PR#> --squash --delete-branch
  git checkout <protected_branch> && git pull --ff-only origin <protected_branch>
  ```
- **Tracker auto-linking:** if your tracker backend (`tracker.backend` in
  `config/dev-model.yaml`) auto-links or auto-completes issues by branch name or commit
  trailer, know its rule before you merge — a partial umbrella ticket may need reopening
  and its checklist updated by hand after merge, rather than trusting the auto-close to be
  correct. Pass whatever project/board identifier your tracker requires
  (`tracker.project_name` / `tracker.linear.*`) so items land in the right place.
