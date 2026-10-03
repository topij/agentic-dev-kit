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

## Session — 2026-10-04 (cs-toolkit Codex validation and Linear installation)

**Shipped.** Fixture portability in [#937](https://github.com/topij/agentic-dev-kit/pull/937),
`163af2d82491f77dd4daeef916e3ec31522e76b7`: controlled configuration, verified mutations,
quoted adopter bots plus an operator, and operator-only configuration. Validation fixes
in [#938](https://github.com/topij/agentic-dev-kit/pull/938),
`bcfe07b578bf59fb510e105ad91a5c6fae071f32`: bounded fail-closed subprocess reads,
complete typed finding-evidence verification, and standalone script metadata.

**Linear.** Installation support in [#939](https://github.com/topij/agentic-dev-kit/pull/939),
`410108fb115a0bf063f737d9961b5ec4f68d641d`: configured-backend opt-in, exact approval,
frozen-input/idempotency preservation, paginated read-back and bounded retries.
Read-back verifies label identity and inherited team scope; the transport refuses redirects.
No additional design decision blocks implementation. Live destination configuration,
credentials, exact payload approval and acceptance remain adopter work.

**Decided.** The operator authorized merging this session's PRs when clean. CodeRabbit
skipped review; the configured independent fallback supplied the adversarial fixture
review and the validation panel with its composed LOW delta. Native rollout records
confirmed the configured reviewer model and effort. Public disposition comments that
initially contained local filenames were corrected and read back.

**Verified.** `env -u FORCE_COLOR make test` at
`626bf01f2408d0d53ca6139bd3aa5419bbdeb866` on 2026-10-04, in
`/private/tmp/devkit-linear-triage`, printed `4195 passed, 1 skipped in 616.02s
(0:10:16)`. The contained LOW redirect repair at
`6f1b3022aca1dd138edc9477387ca5086087dc9e` ran
`uv run --with pytest --with pyyaml pytest -q scripts/tests/test_triage_providers.py
scripts/tests/test_triage_engine.py
scripts/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean` on 2026-10-04, in
the same directory, and printed `327 passed in 46.61s`. Its fresh adversarial delta
posted the named verdicts before composition on the retained full-review parent.
The exact-head watch receipt and authorized merge are recorded on #939.

**Not established.** No live Linear write or cs-toolkit runtime validation was performed.
cs-toolkit remains on `chore/kit-upgrade-2026-10-03` at
`ac7203341f50b5e39f5fe6f7f758b8f7e439cdf5`, as supplied by the operator; its upgrade PR
was held. This session changed only the kit. The new workstream assignment was not
explicitly confirmed; it does not replace another workstream's starter.
Workflow mistakes were recorded for accumulation in the friction inbox; no tracker write
was made. Implementation follows the destination and approval decisions already recorded in #6;
destination configuration, API credentials and exact live payload approval remain adopter actions.

______________________________________________________________________

## Session — 2026-10-03 (Delta-pass named draws, #921, in Claude Code)

**Shipped.** PR #934, squash `41beacb8`: `panel_prompt.py` takes a delta pass's two draws
as `--draw-prose-class` and `--draw-safety-critical`, refuses one without the other, and
names the verdict line each must begin with. The LOW rule's repair boundary goes to
`--repair-boundary`, and `--delta-draws` is refused with a pointer to the three flags.
The CHANGELOG entry is under #934. #921 stays open for its other half: a cockpit-side
check that each lens's verdict lines carry both names.

**Decided by the operator.** Start #921 from the session-start pick, merge #934, and
merge this wrap-up when clean.

**Review.** CodeRabbit skipped #934, so the fallback review ran: one adversarial lens as
the full pass at `53b4569`, then one correctness lens as a LOW delta pass over the repair
`e9d1c4b`. The delta prompt was the first rendered with the new flags, and its lens
returned both named verdict lines. Each round's disposition and the delta's verdict lines
are posted on #934.

**Verified.** `env -u FORCE_COLOR make test` at `53b4569d86e4eca043cc1e95382673796c47df2f`
on 2026-10-03, in `/Users/topi/Coding/agentic-dev-kit`, printed `4068 passed, 1 skipped in
611.11s (0:10:11)`. The repair `e9d1c4b` had focused runs only, recorded in #934's body.
`git diff --stat e9d1c4b 41beacb8` printed nothing, and `gh run list --commit
41beacb8fa54e290c83a04c7617fcf7a0d07c490` showed the `Test` workflow completed `success`.

**Not established.** The repair's focused runs ran on the uncommitted tree, so #934's
body stamps no revision for them, and `pr_watch` reported `verification_stamp_behind_head`
at `e9d1c4b`.

**Answered, not acted on.** The operator asked when to run the final Codex validation and
when to upgrade cs-toolkit. The answer given: upgrade cs-toolkit soon, because its pin
`e698ec47` predates #740 and #914 stops authorized work there; settle cs-toolkit's
`review.safety_critical_paths` first (#930); and run the upgrade in a Codex session so it
doubles as the Codex validation. No workstream records this yet.

______________________________________________________________________

## Session — 2026-10-03 (Review proportionality, #585, in Claude Code)

**Shipped.** PR #927, squash `8ea91add`: a fallback review's lens count follows the PR's
declared class. `review.safety_critical_paths` in `config/dev-model.yaml` declares the
safety-critical files, `pr_watch` classes a PR from Git against that list as committed at
the PR's base, and `fallback:lens` records a standard PR's one isolated lens. The doctrine
is *How many lenses* in `fallback-review-panel.md`.

**Decided by the operator** in this session, and recorded in #927's description:

- Workflow documents take one lens. Keeping two on them until #370 measured them was
  declined.
- A standard PR's one lens is correctness when every changed path is a handoff or
  friction-log file, and adversarial otherwise.
- A PR that changes `config/dev-model.yaml` is safety-critical.
- The class being computed by the PR's own checkout, and a template adopter inheriting
  the kit's list, are documented in #927 and ticketed rather than fixed there.

The operator also authorized merging #927 and this wrap-up.

**Filed on the operator's approval of each exact text:** #928, #929, #930, #931 and #932;
a scope comment on #928; occurrence comments on #838, #149 and #643.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed #927: full
panels at `3fd97b9`, `8bc4d39`, `c894a0b`, `9abb619` and `e86bcf1`, then dual-lens LOW delta
passes at `48594a2` and `1603de6`. Each round's disposition and both delta passes' verdict
lines are posted on #927.

**Verified.** `env -u FORCE_COLOR make test` at `1603de695fd233c9acdd05b722001658cd44499b`
on 2026-10-03, in `/Users/topi/Coding/agentic-dev-kit`, printed `4057 passed, 1 skipped in
615.42s (0:10:15)`. `git diff --stat 1603de6 8ea91add` printed nothing, so the squash
commit's tree is that head's.

**Not established.** Whether `baseRefOid` trails the base branch on an open PR: #929 rests
on the lens's reading of merged PRs, and nothing in this session exercised it live.

______________________________________________________________________

## Session — 2026-10-03 (Phase 6 item 10, #919, and the #585 decision, in Claude Code)

**Shipped.** PR #923, squash `3246e72`: Phase 6 item 10.

- `runtime-parity.md`'s front matter declares `capability_matrix` and
  `lane_isolation_records`; `scripts/tests/test_runtime_parity_matrix.py` holds each
  table to its declaration and resolves the file's links in the forms it parses.
- `saved_plans/phase6-exit-check_2026-10-02.md` records the re-run and the declaration.
  `saved_plans/codex-parity-plan_2026-08-23.md` is a pointer.
- #919 stays open for the row audit the exit left open.

**Decided by the operator.**

- Declare the Phase 6 exit under a recorded amendment rather than hold it (2026-10-02).
  #923's correctness lens then found the offered wording overstated, and the operator
  declared under the narrowed amendment the exit record states (2026-10-03).
- #585: the lens count follows a change's class, and only the safety-critical class
  inherits `safety-critical-changes.md` rule 2's two-lens floor; code outside the
  safety-critical paths takes one lens. Posted on #585 on approval of its exact text, as
  [this comment](https://github.com/topij/agentic-dev-kit/issues/585#issuecomment-5960721970),
  and read back identical.
- Authorized merging #923 and this wrap-up when clean, and running the rest unattended.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed #923: the
full panel at `9f23607`, then dual-lens delta passes at `0fb420d` and `f60b530`. Each
round's disposition and the delta passes' verdict lines are posted on #923. The loop
stopped under the LOW delta-or-ticket rule; its residual findings are parked below.

**Verified.** `env -u FORCE_COLOR make test` at
`f60b530acdd5ca38afaae042e26103fd85a15e1a` on 2026-10-02 (UTC), in
`/Users/topi/Coding/agentic-dev-kit`, printed `3992 passed, 1 skipped in 674.78s
(0:11:14)`. The exit-check record carries the mutation runs, each with its command and
revision.

**Not established.** Which matrix rows' claims are true; #919 carries that. Read on
2026-10-03, its tracker body did not yet say so; the comment below now does.

**Parked, not filed**, because no operator was present to approve a payload: the
2026-10-03 entries in `docs/kit-friction-log.md`. Once the operator was back, two were
filed on approval of their exact text, and each read back identical to that text: the matrix guard's
residue as #925, and a comment on #919 scoping the row audit.

Closed workstream *Phase 6 — gate parity and roll it out*: the operator declared its
exit, and closed it on 2026-10-03. Its residue is on #919, #925, #905, #915, #916 and #917.

______________________________________________________________________

## Session — 2026-10-02 (Phase 6 item 9, #880, in Claude Code)

**Shipped.** PR #920, squash `d9f757d`: Phase 6 item 9.

- `docs/kit-convergence-plan.md` is now a pointer;
  `git show 09fcbe8:docs/kit-convergence-plan.md` prints the archived text.
- `saved_plans/phase6-exit-check_2026-10-02.md` records the Phase 6 exit check at
  `7040d28`, with the command and revision behind each verdict.
- #880 closed on merge.

**Decided by the operator.**

- Hold the Phase 6 exit, rather than declare it under an amendment that narrows "the
  parity matrix" to the front-matter declaration.
- Add item 10, #919, filed on approval of its exact text. It adds a check over the
  capability table, then re-runs the exit check.
- Merge #920 when clean.

**Review.** CodeRabbit's auto-review stayed off, so the fallback panel reviewed #920.

- The full dual-lens panel ran at `89ddbe0`.
- A dual-lens delta pass covered the repair commit `92bad59`. It was dual because the
  correctness lens marked one finding LOW-MEDIUM. Its receipt composes on the panel's.
- Each round's disposition and the delta's verdict lines are posted on #920.

**Verified.**

- `env -u FORCE_COLOR make test` at `89ddbe0d3f8116c85b69cd16ed1a8a6de5d5c2d3` on
  2026-10-02, in `/Users/topi/Coding/agentic-dev-kit`, printed `3969 passed, 1 skipped
  in 662.86s (0:11:02)`.
- The repair commit changed only record prose. A link check covered it, as recorded on
  #920.
- `gh run list --commit d9f757da193bcf91c5cc4c0c2d211dcf71085023` showed the `Test`
  workflow completed `success` on `main`.

**Not established.** The record does not audit which table rows have their repository
side pinned by other tests; #919 carries that. The record's mutation clones were not
kept.

**Filed**, each on the operator's approval of its exact text, and read back identical:

- #919;
- #921, from the delta pass: a lens skipped the two classification verdicts;
- an occurrence comment on #578: the suite now outlasts the lens timeout that issue
  suggests.

______________________________________________________________________

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Review proportionality

**Status:** the lens-count half of #585's 2026-10-02 decision shipped in #927
(`8ea91add`): the class is computed from `review.safety_critical_paths`, and a standard PR
takes one isolated lens. #934 (`41beacb8`) gave a delta pass's two draws their own named
flags; #921 stays open for the cockpit-side check of the verdict-line names. The
record-prose row of #585's decision is not built: its deterministic checks, and a lens
told which spans stay executed. **Owner:**
[#585](https://github.com/topij/agentic-dev-kit/issues/585); related #921, #403, #666, and
the class's documented limits #928, #929, #930 and #931.

▶ Next: #585's record-prose row — its deterministic checks, and a lens told which spans
stay executed.

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

### cs-toolkit Codex validation and Linear installation

**Status:** fixture and validation fixes shipped in #937 and #938. Linear installation support shipped in #939
at `410108fb115a0bf063f737d9961b5ec4f68d641d`; live acceptance remains adopter work.
The upstream validation record remains #919; the Linear acceptance record remains #6.
**Owner:** [#919](https://github.com/topij/agentic-dev-kit/issues/919),
[#6](https://github.com/topij/agentic-dev-kit/issues/6).

▶ Next: In cs-toolkit, refresh the kit from `410108fb115a0bf063f737d9961b5ec4f68d641d`, reconcile its
retirement helper with the completed-state contract, run `make check-root` and
`make test-devkit`, then open the held upgrade PR and finish the remaining Codex runtime
validation. Install the declined triage engines with the Linear configuration and exact
operator-approved tracker payloads described in #939.
