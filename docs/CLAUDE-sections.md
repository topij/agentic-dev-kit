# Agent-guide sections (CLAUDE.md / AGENTS.md) — ready to paste

Paste these into your repo's agent guide — `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or
whatever file your agent loads every session — adjust to taste. (Below they say
"CLAUDE.md"; read that as *your always-loaded agent guide*.) Each section implements one or
more of the ten principles in [`PRINCIPLES.md`](../PRINCIPLES.md). Where a value is
project-specific, it's written as a `config/dev-model.yaml` key (see
[`../config/dev-model.yaml`](../config/dev-model.yaml)) rather than a literal, so you can
either replace the key reference with your actual value inline, or leave it pointing at
config and let your skills read it at runtime.

---

## Branching

All changes go through branches and pull requests — never commit directly to
`<vcs.protected_branch>` (typically `main`). Convention:

- Branch from `<vcs.protected_branch>` with a descriptive name (e.g. `feat/lifecycle-metrics`,
  `chore/update-dashboard`).
- **Open the PR as a draft on first push, and mark it ready (`gh pr ready`) the moment the
  branch is complete** — i.e. there's nothing more to commit or push. A finished PR must
  never sit in draft: ready-for-review is what triggers your review bots' (`review.bots`)
  full review pass, so leaving completed work in draft starves it of review. Keep a PR in
  draft *only* while you're still actively pushing commits to it; flip it to ready as soon
  as the work is done and the body is complete, then run the watch-and-fix loop. Re-draft
  (`gh pr ready --undo`) only if you discover the PR needs material follow-up commits
  before review.
- `<vcs.protected_branch>` is protected; direct pushes should be rejected by your forge
  (branch protection rules).
- PRs require an external reviewer before merge (a human, or the review-bot pass below).

### Stacking vs. one-PR-per-change

Because review is non-trivial, split PRs by **risk**, not by size:

- **Stack low-risk, iterative work into one PR.** Pure UI/CSS/JS tweaks, renaming,
  cosmetic copy changes, layout iterations — keep these on a shared local branch and push
  a single combined PR when the batch feels done. 3–5 logically-related changes is a
  reasonable cap. Use one commit per change so review-by-commit stays feasible.
- **Keep high-risk work in its own PR.** Data-shape changes, fetcher/ingest behavior,
  config semantics, security, anything that touches production or shared state. A
  reviewer's second pair of eyes is most valuable here; bundling these dilutes review
  quality and makes rollback harder.
- **Don't open stacked PRs against an unmerged parent branch — open one at a time.** A
  squash-merge creates a new commit on the protected branch distinct from anything on the
  source branch, leaving the original branch dead. A child PR targeting the dead parent
  will report "merged" into that dead branch while the changes never reach the protected
  branch. If a follow-up depends on a not-yet-merged PR: wait for the parent to merge,
  rebase onto the new protected-branch tip, then open the follow-up.
- When in doubt, err on the side of the focused PR — it's faster to open a second PR than
  to unwind a regression out of a bundle.

---

## PR follow-through (mandatory)

Opening or pushing to a PR is not "done" — **monitoring and fixing it is part of the same
task, not a separate request.** After you `gh pr create` / `gh pr ready`, or push a fix
commit to a PR branch, **run the watch-and-fix loop and don't yield the turn until the PR
is green and clean** — CI fully passing AND every configured review bot's (`review.bots`)
finding either fixed or replied-to with a reason. Stop early only for a genuine blocker
that needs an operator decision (a finding that's a product/design call, an unrecoverable
infra failure) — then report the specific blocker and ask.

**A review bot being unavailable is not a reason to skip review.** When a configured bot
can't review an otherwise-ready PR — rate-limited, out of credits, or it silently skipped
the PR — run `review.fallback_commands.claude` as the independent review pass and triage its
findings the same way (fix if confident and small, reply-with-reason otherwise). A blocked
review bot is **not** a waiver: the "clean" bar still requires one independent review
pass — bot *or* the fallback command.

---

## Execution Rules

- Proceed autonomously for file operations, scaffolding, testing, and lint fixes.
- Pause before: API design decisions, security-sensitive changes, CLAUDE.md restructuring.
- After completing a phase: commit, run your local gate (lint + typecheck + tests), report
  status, then continue.
- If the local gate fails: fix and retry up to 3 times, then pause and report.
- If a design question arises that isn't covered by the plan: pause and ask.
- Never bulk-edit a sensitive, broad-reader-surface config file (a customer/contact
  roster, a secrets manifest, anything similar) without explicit confirmation.
- If something goes sideways (unexpected errors, repeated test failures, scope creep):
  stop and re-plan instead of pushing through.
- If a fix feels hacky, pause and consider the elegant alternative before committing — but
  skip this for simple, obvious changes.
- Before marking a non-trivial change done: diff the behavior against
  `<vcs.protected_branch>` when relevant, and ask "would a senior engineer approve this?"

---

## Memory layout — CLAUDE.md vs. rules

CLAUDE.md holds repo-wide context that applies to **every** session. Topic- and
file-type-specific conventions live as path-scoped rules under `.claude/rules/`, each with
a `paths:` glob so it loads only when a matching file is in context. Keep CLAUDE.md lean:
when a convention only matters for *some* files, it belongs in a rule, not in CLAUDE.md.

Example rules layout (name and scope these to your own stack — the kit ships
[`safety-critical-changes.md`](../.claude/rules/safety-critical-changes.md), the rest are
illustrative):

- a language/runtime conventions rule (`paths: **/*.py` or equivalent) — idioms, lint /
  typecheck / test specifics, environment gotchas.
- a shared-library rule (`paths: libs/**` or equivalent) — cross-package invariants.
- a skills/commands rule (`paths: .claude/commands/**`) — prompt conventions, tool
  pre-flight, review-loop mechanics.
- a data/state rule (`paths: state/**`, cache code) — shared cache catalog, config
  loading, dependency pre-flight.
- `safety-critical-changes.md` (send-path / gate / kill-path scripts) — the review
  doctrine from Principle #6: deterministic gate over matcher, dual-lens review,
  adversarial-to-convergence, kill-path integration tests, operator-merge only.

List each active rule and its `paths:` scope in CLAUDE.md so a session can tell at a
glance which rules exist without opening every file.
