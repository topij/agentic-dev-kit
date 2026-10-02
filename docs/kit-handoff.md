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
> **Two parts.** Session entries are a log of what happened, newest first, and carry no
> next step. Each open line of work keeps its own `▶ Next:` in its entry under
> **Workstreams** at the end of this file, until the operator closes it
> ([#762](https://github.com/topij/agentic-dev-kit/issues/762)).
>
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`). The Workstreams
> section is never swept.

## Session — 2026-10-02 (Phase 6 items 7 and 8, #879, in Claude Code)

**Shipped.** PR #913, squash `947fca0`: `scripts/runtime_smoke.py`, a repo-only runner
started by hand rather than in pull-request CI. In a fixture built from a kit revision,
under isolated client homes, it drives a pinned Codex and a pinned Claude Code through
instruction and skill or command discovery, SessionStart and PostToolUse, native review,
the fallback panel and a lane through `scripts/launch_lane.py`. Each row records evidence
read from the runtime's own artifacts, or the reason it could not run. The first stamped
record, from a run at `0c2c200`, is `saved_plans/runtime-smoke-evidence_2026-10-02/`,
and `saved_plans/runtime-smoke_2026-10-02.md` is its narrative. #879 closed on merge.

**Decided.**

- Trust is granted per invocation, and only in isolated homes the operator created and
  logged in to. For the Codex hook probe alone, the operator authorized the hook-trust
  bypass and a `-c` project-trust override; the fixture's hook output reached a Codex
  session only with both (the narrative's observation 2).
- A smoke record is an observation, not a promotion bundle
  (`live-validation-evidence.md`, *On-demand smoke records*), so no parity-matrix row
  moved.

**Verified.** `env -u FORCE_COLOR make test` at
`ec06c3bd2ded880fabcf674e33d8947035d37b4d` on 2026-10-02 in
`/Users/topi/Coding/agentic-dev-kit` printed `3969 passed, 1 skipped in 645.24s
(0:10:45)`. The squash's tree is that revision's.

**Not established.** The narrative's own section names what the record does not show.
The runner's stops were exercised against fake clients only.

**Filed.** #915, from #913's review; #916 and #917, from the live runs. Observations
went to #802, #643 and #408 as comments.

______________________________________________________________________

## Session — 2026-10-02 (Phase 6 Codex validation)

**Shipped.** PR #911, squash `0298191`: #908's lifecycle record now names the
Capability tiers matrix row and identifies the writing-lane records as the ones
with accompanying designs. The manifest was regenerated.

**Observed.** The Codex session exercised skill discovery, session-start sources,
ready PR creation, PR follow-through hook delivery, and the fallback panel. Each
fresh `codex exec` lens's native `turn_context` confirmed the configured model and
effort. To avoid #802's trust side effect, the operator approved starting reviewers
in the already trusted checkout and directing them to separate review trees.
The panel's disposition is on #911; local observations and native excerpts are in
`state/review-evidence/codex-validation-20261002/` (gitignored).

**Verified.** `env -u FORCE_COLOR make test` at
`4985e4c1d99419ee39144682b576582ca8943038` on 2026-10-02 in
`/Users/topi/Coding/agentic-dev-kit` passed on a quiet tracked tree.

**Not established.** No SessionStart output reached this chat. The trusted hooks
were inspected in a separate CLI session; the desktop hook UI was unavailable.
Native `/review`, parallel lanes, Claude smoke tests and the on-demand runner were
not exercised. The #879 observation comment was drafted for operator approval;
this session makes no parity-matrix promotion.

**Corrected.** At the operator's request, the triage workstream records #907's
merge as `cb92fd5`, removes #891 from its owners, and continues with #859.

______________________________________________________________________

## Session — 2026-10-01 (Phase 6 item 6, #890 and #891, unattended in Claude Code)

**Shipped.**

- PR #904, squash `0c7669a`: Phase 6 item 6. `runtime-parity.md` gains an `adoption`
  front-matter block, scoped to the template route. Repo-only fixtures in
  `scripts/tests/test_adoption_fixtures.py` install the kit into fresh Codex-only,
  Claude-only and dual-runtime repositories and check each install against it. #878
  closed on merge.
- PR #906, squash `c6b663d`: each headless-lane record's claims now live once, in the
  per-runtime sub-table of `runtime-parity.md`. #890 closed on merge.

**Held for the operator.** PR #907 is the fix for #891: `GitHubForge`'s sweep-cleanup
guard now decides containment by filesystem identity, through #889's predicate moved to
`model.py`. It gates a destructive operation, so `safety-critical-changes.md` makes it
operator-merge, and this session did not merge it. Its full-panel receipt at `704bde3`
was recorded from the worktree #907 was built in, whose state file was then copied into
the main checkout's `state/`; the two-lens delta receipt at `fcff926` composed on it
there (#563's mechanism; occurrence noted there).

**Decided by the operator**, in this session, before it ran unattended:

- #878 step 3: a single-runtime adopter keeps receiving the other runtime's adapters,
  recorded as `other_runtime: installed`, and on #878.
- Scope: #878, then #890 and #891, then wrap-up. Pull requests merge when clean, and
  LOW review findings are filed.
- Issue-shaped friction at wrap-up is filed without per-payload approval. That departs
  from `wrap-up.md`'s exact-payload rule; #909 asks which should hold.

**Filed**, each read back: #905 and #908, the deferred LOW findings of #904 and #906;
#909. Occurrence comments on #563, #844 and #643.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed each
pull request. #904 had a full panel at `2581034` and again at `1f37c00`. #906 had a
full panel at `54c2f75`. #907 had a full panel at `704bde3` and a delta at `fcff926`.
Each round's disposition is posted on its pull request.

**Verified.** Each pull request's body carries its `env -u FORCE_COLOR make test`
stamp at the head that merged or is held, each run on 2026-10-01 with exit 0:

- at `1f37c00` (#904) and at `54c2f75` (#906), in `/Users/topi/Coding/agentic-dev-kit`;
- at `fcff926` (#907), in a `git worktree add` of it under the session scratchpad.

`gh run list --commit` showed the `Test` workflow `success` on `main` for `0c7669a` and
`c6b663d`.

**Not established.** #907's case-variant tests skip on a case-sensitive filesystem,
which is what CI runs; they ran on this machine's case-insensitive one.

______________________________________________________________________

## Session — 2026-10-01 (Phase 6 item 5, in Claude Code)

**Shipped.** PR #902, squash `65e9d2d`: Phase 6 item 5. #243 closed on merge.

- Each adapter's runtime-specific text moved from `_CURRENT_CONTEXTS` into
  `scripts/lib/adapter_templates/<runtime>/<slug>.md`, read from beside the renderer.
  The rendered adapters are byte-identical.
- `adopt`, `upgrade` and `pr-watch` gained word-for-word pins with appended-instruction
  mutations.
- `fallback-review-panel.md` no longer cites a "step 5" of the Codex `pr-watch` binding.

**Decided by the operator.**

- The templates sit beside the renderer, not under `docs/templates/` as #243's
  2026-09-02 comment proposed.
- #902 closes #243, and merges once clean.

**Filed**, on the operator's approval of its exact text and read back identical: an
occurrence comment on #644
([issuecomment-5937818741](https://github.com/topij/agentic-dev-kit/issues/644#issuecomment-5937818741)).
It reproduces that intermittent failure by launching the test as a shell `&` job,
which starts it with SIGINT ignored.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed #902:
the full dual-lens panel at `a459006`, then adversarial delta passes over the repair
commits. Delta passes 1 and 2 each disputed a draw, both about another test's handling
of the templates, so neither recorded a receipt. Delta pass 3 confirmed every draw,
and its receipt at `947bc22` composes on the full panel's. Each round's disposition is
posted on the PR.

**Verified.** `env -u FORCE_COLOR make test` at `a459006`, in
`/Users/topi/Coding/agentic-dev-kit` on 2026-10-01: `3792 passed, 1 skipped in
519.66s (0:08:39)`. The repair commits carry focused verification, recorded on the PR.
For the merged tree, `gh run list --commit 65e9d2d334de4277dd2bbb031667bd666c3da9ee`
showed the `Test` workflow completed `success` on `main`.

______________________________________________________________________

## Session — 2026-10-01 (Phase 6 item 4, and a scratch and branch cleanup, in Claude Code)

**Shipped.** PR #897, squash `6e4c439`: Phase 6 item 4 (#663).

- session-start reads each open pull request through `pr_watch.py <PR#> --json
  --no-persist --all-comments` instead of three `gh api` calls.
- The new `--all-comments` flag reports every comment and review submission,
  unfiltered by seen state, noise markers or an empty body.
- A REST poll reads `pulls/{n}`, `check-runs` and `status` once instead of twice.

**Decided by the operator.**

- Merge #897, which was held for them as operator-merge.
- Keep `state/review-evidence/` until a retention rule decides what each run keeps
  (#861).
- Build the sweep engine (#900) in its own session. It opens the *Scratch retention*
  workstream below.

**Left out on purpose:** passing `dev_session.sh`'s `headRefOid` down to `pr_watch.py`.
The reason is in the #663 comment, and #663 stays open for its residue.

**Filed**, each on the operator's approval of its exact text: #898, #899, #900.
Comments went on #663 and #838.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed #897:
the full dual-lens panel at `d29fa9a`, then dual-lens delta passes for its LOW repairs
at `be68303` and `a2acb9b`. The receipts compose into one chain. Each round's
disposition is posted on the PR, with both delta passes' verdict lines verbatim.

**Cleanup.**

- Every head branch on origin whose PR merged was deleted, after checking that its tip
  was the merged head. GitHub's delete-branch-on-merge setting is now on.
- `dev/pr-watch-rest-transport` is kept: its PR, #91, closed with commits not in
  `main`.
- The operator ran a generated script that removed stale session scratchpads and
  review-lens trees under `/private/tmp`, for this repo and for cs-toolkit. Apart from
  this session's own lens clones, it touched only entries not modified that day.

**Verified.** `env -u FORCE_COLOR make test` at `d29fa9a`, in
`/Users/topi/Coding/agentic-dev-kit` on 2026-10-01: `3773 passed, 1 skipped in
658.45s`. That run predates the two LOW-repair commits, `be68303` and `a2acb9b`, which
changed `scripts/pr_watch.py` and its tests before the merge. For the merged tree,
`gh run list --commit 6e4c439` showed the `Test` workflow completed `success` on
`main`.

______________________________________________________________________

## Session — 2026-10-01 (Phase 6 items 1 to 3, the triage guard, the two-link way out, in Claude Code)

This continues the *Phase 6 planned* session entry below, after its wrap-up.

**Shipped.**

- PR #887, squash `e559b5f`, from the headless lane `phase6-877`: Phase 6 item 3 (#877).
  The parity matrix's headless-lane cell is split per runtime, and the parity plan is cut
  to exits, owners and order.
- PR #888, squash `757a6c0`: item 2 (#876). The review-process learnings memo is distilled
  into `fallback-review-panel.md` and archived.
- PR #893, squash `25fde2c`: item 1 (#875). It adds an `evidence` marker and
  `make test-fast`, pinned by `make -n` to be `make test` plus `-m 'not evidence'`.
  `AGENTS.md` says it is never a verification claim and names the guard tests it skips.
- PR #889, squash `95822fb`, from the headless lane `triage-856`: the engine's worktree
  guards decide containment by filesystem identity (#856).
- PR #894, squash `2a81896`: the *Completed-state retirement* doctrine gives the operator
  a manual way out of the two-link state. The same PR rewrote the *Triage engine
  hardening* entry below.

#875, #876, #877 and #856 closed on merge.

**Decided by the operator.**

- Build #875 even though the premise check had put it on hold. The correction comment on
  #875 retracts the first estimate.
- Leave the two-link state to a documented manual step. This answers the question the
  entry below held for the operator. #892 carries the engine route, to be built only if
  the state recurs.
- *Triage engine hardening*'s next step is #891.

**Filed**, each on the operator's approval of its exact text: #890, #891, #892, #895.
Comments went on #880, #875 (two), #883, #892, #852 and #514.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed each PR.
#889 and #894 took the dual form throughout, as a gate guard and as recovery doctrine.
On #894, delta pass 1's receipt was refused because its repair was pushed first. That
is #852's trap on a later round, and its dispositions went in as a plain comment.

**Incidents.**

- The disk filled overnight (ENOSPC), and every tool call failed until the operator
  cleared pytest's temp directory. #895 names the mechanism: a killed run leaves a lock
  that pins its basetemp for three days.
- Review lenses stalled when the host slept. Their suite runs outlived them and were
  killed by hand.
- The `triage-856` lane returned mid-task, because the cockpit's brief told it to
  background `make test`. The cockpit finished the work (the #514 comment).

**Verified.** Each PR's body carries its `env -u FORCE_COLOR make test` stamp at a named
sha. On main on 2026-10-01, `gh run list --commit <sha>` showed the `Test` workflow
completed `success` on `95822fb`, `e559b5f`, `757a6c0`, `2a81896` and `25fde2c`.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Phase 6 — gate parity and roll it out

**Status:** items 1 to 3 shipped on 2026-10-01, in #893, #888 and #887; items 4 and 5
the same day, in #897 and #902; item 6 the same day, in #904, which also recorded
#878 step 3's answer; items 7 and 8 on 2026-10-02, in #913, with the first stamped
smoke record. #906 removed the duplication #887 left in `runtime-parity.md`.
The *Phase 6* section of `saved_plans/codex-parity-plan_2026-08-23.md` owns the order,
the dependencies and the exit. #663, item 4's owner, stays open for residue that is not
Phase 6 work; its 2026-10-01 comment names it. #905 carries deferred LOW findings
from #904, #915 a deferred LOW finding from #913's review, and #916 and #917 what
#913's live runs found. #911 clarified #906’s lifecycle references on 2026-10-02.
**Owner:**
[#880](https://github.com/topij/agentic-dev-kit/issues/880),
[#905](https://github.com/topij/agentic-dev-kit/issues/905),
[#915](https://github.com/topij/agentic-dev-kit/issues/915),
[#916](https://github.com/topij/agentic-dev-kit/issues/916),
[#917](https://github.com/topij/agentic-dev-kit/issues/917).

▶ Next: [#880](https://github.com/topij/agentic-dev-kit/issues/880) — Phase 6 item 9:
retire `docs/kit-convergence-plan.md` behind the maintained parity matrix, then check
the Phase 6 exit as the parity plan states it.

### Scratch retention

**Status:** filed on 2026-10-01 as #900. Review lenses' mutation clones, session
scratchpads and killed pytest basetemps pile up under `/private/tmp` with nothing to
sweep them. They filled the disk on 2026-09-29 and again overnight into 2026-10-01. A
manual cleanup on 2026-10-01 removed the stale ones. `state/review-evidence/` is kept
until #861 sets its retention rule. **Owner:** [#900](https://github.com/topij/agentic-dev-kit/issues/900),
[#861](https://github.com/topij/agentic-dev-kit/issues/861),
[#895](https://github.com/topij/agentic-dev-kit/issues/895).

▶ Next: #900 — build `scripts/sweep_scratch.py`, report mode first, then the guarded
`--apply`. It deletes files, so read `docs/agentic-dev-kit/safety-critical-changes.md`
first and hold the PR for the operator's merge.

### Reviewer profiles

**Status:** on 2026-09-25 the operator asked the reviewer's developer to post a GitHub
check run, which would let the merge gate's existing check-based path see it; #797 can
wait for that answer. **Owner:** [#796](https://github.com/topij/agentic-dev-kit/issues/796),
[#797](https://github.com/topij/agentic-dev-kit/issues/797); the adopter-specific notes are
in `saved_plans/fabro-review-tool-assessment_2026-09-25.md` (local, not committed).

▶ Next: implement #796 — adopter-defined reviewer profiles and a configured
review-request method.

### Triage engine hardening

**Status:** finalize's commit-step worktree re-check is pinned by a test (#857), and the
*Completed-state retirement* doctrine names each live-mode kill cutpoint (#874), both in
#882. #883 carries its residual points. The engine's worktree guards decide containment by
filesystem identity (#856, in #889). PR #907 applied the shared predicate to
`GitHubForge`’s sweep-cleanup guard (#891), merged on 2026-10-02 as `cb92fd5`.
The doctrine prescribes the operator’s manual way out of the two-link state (#894),
and an engine-owned rollback waits for a recurrence (#892).
**Owner:**
[#859](https://github.com/topij/agentic-dev-kit/issues/859),
[#883](https://github.com/topij/agentic-dev-kit/issues/883),
[#892](https://github.com/topij/agentic-dev-kit/issues/892).

▶ Next: #859 — triage recover calls a completed state valid on `canonical_state`
alone, so a missing frozen artifact dead-ends it.
