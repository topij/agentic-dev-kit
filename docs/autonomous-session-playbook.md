# Autonomous session operating contract

> **Scope — operator-gated.** This contract applies **only when the operator explicitly
> requests an autonomous session** (e.g. "run an autonomous session on X", "work this
> autonomously", "autonomous chore sprint"). It does **not** govern normal interactive
> sessions, where the operator drives PR review and merge.
>
> Your always-loaded agent guide's branching and PR-follow-through rules are the
> always-on baseline; the generated root [`AGENTS.md`](../AGENTS.md) carries the
> cross-runtime version, is rendered from the shipped
> [`AGENTS.md` template](templates/AGENTS.md.tmpl), and Claude imports the generated
> root file through `@AGENTS.md`.
> [`CLAUDE-sections.md`](CLAUDE-sections.md) is ready-to-paste material for an existing
> guide. This contract is the autonomous **superset**. It drives work through
> review to an authorized merge, or preserves the exact head for an operator
> decision when merge authority is absent. Self-merge requires project policy
> and current-request authority; the autonomous request alone is not that grant.
> The always-on guardrails still hold — pause before security-sensitive changes, and
> respect whatever data-handling / PII confirmation rules your project's agent guide
> defines; a broad-but-sensitive config file (a customer/contact roster, a secrets
> manifest, anything similar) is never for unsupervised bulk migration by an autonomous
> pass.

Follow this top to bottom, per ticket.

## PR lifecycle / merge model — merge with authority or hold the exact head

### Branch hygiene

- Fetch the protected branch and reuse the task's assigned linked worktree, or
  create one from the fetched base. Keep edits, verification and commits in that
  worktree. Use `git branch --show-current` before committing to confirm the task branch.

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

### Validate → open ready

- **Risk gate, before opening the pull request:**
  - Low-risk display / derivation change → straight to ready (self-merge path).
  - A change to a cache shape, a data fetcher, or anything that touches shared/production
    state → **live-validate against the real target first**: write a throwaway harness
    that exercises the changed function directly against production-shaped input before
    trusting it. Do **not** commit regenerated artifacts produced only for validation.
- Push `-u` and open the completed pull request **ready for review**: `gh pr create`
  without `--draft`.
- Immediately run `uv run <engine-dir>/pr_watch.py <PR#> --assert-ready` before the
  watch-and-fix loop so a silently drifted draft bit cannot starve review.
- Take the bounded draft exception from
  [`pr-watch`](agentic-dev-kit/workflows/pr-watch.md#ready-and-draft-policy) only when a
  material unfinished-work window must already be on the remote pull request — for
  example, required forge-hosted validation that cannot run before the pull request
  exists. That run creates with `--draft`, confirms `--assert-draft`, and owns the
  `gh pr ready` plus `--assert-ready` transition as soon as the work and body are
  complete. Risk, operator-held merge authority, and a desire for human review are not
  draft reasons by themselves.

### Watch-and-fix loop (do NOT yield until green + clean)

1. Poll the exact PR and read failing checks, new findings and any read gaps.
   A lane's cockpit uses `dev_session.sh pr-watch <scope>` so the poll and receipt
   use that lane's state. Serialize operations on that state file.
2. Push repairs and post replies to findings you dispute. Once each finding
   from the last poll has been handled on the PR, acknowledge that round with
   `--mark-seen` and poll the current head again. Pending checks and
   unsettled rollups need another poll on the workflow's documented cadence.
3. At convergence, follow `review_owed` and inspect `review_evidence` for the
   reported head. Run any fallback review required by `review_class`. Record
   what actually ran, its head and the typed dispositions. If a disposition
   promises a repair, use the workflow's pending-repair receipt before pushing it.
4. Read `merge_blockers` and `mergeable`. If the review budget is spent with
   findings still to act on, deliver the decision packet and hold the head for
   the operator. The [PR-watch workflow](agentic-dev-kit/workflows/pr-watch.md)
   owns polling, review requests, receipts and stop conditions.

### Merge + close out

- Merge only once checks are green, the PR is mergeable, and every finding has been fixed
  or explicitly addressed. A lane created by `dev_session.sh` must honor its persisted
  merge class at act time. Where project and request authority permit self-merge,
  the cockpit merges a `self` lane through
  `<engine-dir>/dev_session.sh merge <scope>` (which re-polls `pr-watch`); missing,
  unknown, or `operator` metadata refuses autonomous merge and requires operator
  sign-off, and so does a `self` lane whose PR `pr_watch` does not class `standard`. A non-lane PR with no project merge policy defaults to the operator
  route and needs authorization for the exact PR; an autonomous-session request
  alone does not grant that merge. Consult the project's configured handoff for
  any operator hold on lane merges. When authorized,
  merge the authorized head and confirm the result on the forge. For an
  authorized non-lane PR, pin the observed head in the GitHub merge command:
  ```sh
  gh pr merge <PR#> --squash --match-head-commit <reviewed-sha>
  ```
- **Tracker auto-linking:** if your tracker backend (`tracker.backend` in
  `config/dev-model.yaml`) auto-links or auto-completes issues by branch name or commit
  trailer, know its rule before you merge — a partial umbrella ticket may need reopening
  and its checklist updated by hand after merge, rather than trusting the auto-close to be
  correct. Pass whatever project/board identifier your tracker requires
  (`tracker.project_name` / `tracker.linear.*`) so items land in the right place.
