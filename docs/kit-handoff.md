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

## Session — 2026-10-05 (cs-toolkit recovery repair delivery, in Codex)

**Shipped upstream.** Historical gate compatibility merged through #952
(`70d74130374c010d7070e1de6742ef0aaf189959`), bounded provenance cleanup through
#955 (`6071c791729b381551989bfaf153a8cbb8176651`), captured-operator retry and
owned-child cleanup through #957 (`e3e75f8fbd3d2289b4d0edf12a2481427e0389a3`),
and detached-helper uncertainty through #959
(`7b9d3cdf34c39090bf57f6404d30b2572a045c4f`). Their PRs retain verification
and independent review dispositions. LOW follow-ups were filed as #953, #954,
#956, #958 and #960; #960's exact payload was approved and read back identical.

**Read-error and decoding repairs delivered.** [#961](https://github.com/topij/agentic-dev-kit/pull/961)
merged as `425c13f56792c1528e1721441bae62308e5dee53` and
[#962](https://github.com/topij/agentic-dev-kit/pull/962) as
`66a8044865e5ef43d633270c2ce224827de3aa35`. The latter merged tree matched
reviewed `45b42bf49d30191c35896bb618df9047be7d2b0a` exactly. `make test` at
`45b42bf49d30191c35896bb618df9047be7d2b0a` on 2026-10-05, in
`/private/tmp/mut-adversarial-45b42bf-sol61-v8q2pC9T`, printed
`4336 passed, 1 skipped in 864.38s`. Actual app rollouts retain the approved
session-only reviewer compute separately from failed CLI attempts. The MED
ordinary-wrapper limitation remains documented in #963; #964 records the LOW
test selection/deadline regression. Neither is claimed as a fixed mechanism.
Installation [#2535](https://github.com/in-parallel-oy/cs-toolkit/pull/2535)
merged as `33816d5f9558024796fe08552e41164440ace88d`, with its tree matched
to reviewed candidate `308e15a9700654b98025709ff92d3bc01178a2f0` before delivery
to the primary checkout. It incorporates refreshed cs-toolkit main
`42db0d0ec6fd0531d70834f07dfbd883bfbff31a` and pins the verified source merge.
`make check-root` at `308e15a9700654b98025709ff92d3bc01178a2f0` on 2026-10-05, in
`/private/tmp/mut-adversarial-308e15a9-app-sol61.JSrnIW/repo`, exited successfully;
its pytest summary printed `7642 passed, 4 skipped in 481.02s`.
Destination hashes, protected files and declines were checked after delivery.
The citation LOW reuses #954; the duplicate-key fixture LOW is filed as #966.

**Review learning.** Build the process ownership and failure matrix before review,
including read and decode errors beside timeout/cleanup transitions. The existing
shared doctrine already requires that matrix; no new general rule was added.
Keep provider failures as failures, reconcile any still-running owned command,
and observe compute through the actual launch route. The concrete reviewer-route
follow-up was filed as #965 under the operator’s instruction to create needed
devkit tickets; exact payload and readback remain in the retained evidence.

**Authority and evidence.** Installation and clean merges were authorized. The
session-local `invoke_installed.py recover` at `33816d5f9558024796fe08552e41164440ace88d` on 2026-10-05,
in `/Users/topi/Coding/in-parallel/cs-toolkit`, captured the preserved gate and
reservation and returned an action awaiting exact approval. Its core digest is
`1217af39a6eedcd2a4697bb34952a8941014bedd801de29bd46bfc3199094f2d`.
The complete display, owner facts, original bytes and receipts remain under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/`.
No quarantine, replacement live freeze or Linear write occurred. TEST decisions
remain TEST-only; root legacy artifacts, host automation and credentials were preserved.
The kit's separate budget triage froze session `469bcd5829244adeb17443d1a45a6c01`;
its archive/park decision remains pending, with every inbox block preserved.

______________________________________________________________________

## Session — 2026-10-05 (cs-toolkit test completion and historical gate recovery)

**Decided.** The operator established that the recorded host was this Mac and its
triage process had stopped, approved TRI-27 for the retained test session only,
parked every other test candidate, and approved the upstream compatibility repair
plan. Those decisions did not approve a live recovery mutation or Linear payload.

**Applied in test.** On 2026-10-04 the operator's test-only decisions were applied
to retained session `5d68cdbff45c4ecbb561dfc6832d0f11` in cs-toolkit. The local
evidence directory below retains `test-completed-state.json`,
`test-completion-receipt.json`, `test-completed-report.md` and `test-proposed.diff`.

**Developed.** [#952](https://github.com/topij/agentic-dev-kit/pull/952) carries the
approved historical-gate compatibility repair. Recovery keeps the original bytes,
requires owner evidence before state observation, and separates capture from exact
action approval. Local approval, capture, test-completion, verification and review
receipts are retained under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/`.
On 2026-10-04 this preparation retained the historical reservation bytes in
`held-live-state.raw` and `read-only-live-state-capture.json` in that directory
for a separately approved recovery action. No recovery mutation,
live frozen run, approved Linear payload or Linear write was performed during this
preparation. Adopter engine/configuration, root legacy
artifacts, host automation and credentials were preserved.

______________________________________________________________________

## Session — 2026-10-04 (cs-toolkit acceptance preparation, in Codex)

**Prepared.** The retained test session `5d68cdbff45c4ecbb561dfc6832d0f11`
advanced to `awaiting-approval` through the installed test entry. Its complete payload
set consists of explicit test-only fixtures; live semantic triage remains outstanding.
The exact report, proposal-set binding, client observations, installation checks and
recovery prerequisites are retained under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/resume-01a1085e/`.

**Held.** No test decision was invented, so decision accounting and diff rendering
remain pending. The live gate matched the preserved capture; its older format fails
the installed canonical and record-shape checks. Host identity and owner termination
remain unestablished. The prepared recovery plan grants no mutation authority.
No live frozen run or approved Linear payload was produced.

**Authority.** The operator requested autonomous continuation before going to sleep.
The plan's separate recovery and exact-payload approval boundaries were retained.
Legacy artifacts, host automations, credentials and installed engines were preserved.
Publication of the prepared acceptance update on #6 awaits its exact-payload decision.

______________________________________________________________________

## Session — 2026-10-04 (cs-toolkit Linear acceptance attempt, in Codex)

**Recorded.** [The acceptance attempt on #6](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-5983052800)
retains the installation checks, destination and credential plan, client observations,
native rollout reference, test freeze and held live preflight. The comment was read back
identical. Local artifacts are in `state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/`.

**Held.** The live preflight returned `single-writer gate is already held`; no live
frozen run or payload reached approval. No Linear write or recovery mutation occurred.
The operator's legacy-artifact, host-automation and credential boundaries were preserved.
The test run reached its freeze stage, not proposal/decision/render completion.

**Plan retained.** Use the installed kit pin and merged Linear destination, with the
existing secure credential loader. No cs-toolkit configuration or engine change was needed
for this attempt. The operator named this workstream and requested replacing its stale
starter; #946's merge and #919's closure were read back before the update.

______________________________________________________________________

## Session — 2026-10-04 (#919 capability-matrix row audit)

**Opened in that session.** [#946](https://github.com/topij/agentic-dev-kit/pull/946) delivers
#919's narrowed scope. `saved_plans/capability-matrix-row-audit_2026-10-04.md` maps each
matrix row's repository-side clauses to tests, separates declaration consistency from
behavioural and runtime-observed evidence, and names what stays unestablished. It also:

- corrects the *Capability tiers*, *Adapter upgrade* and *Lifecycle validation boundary*
  claims that were false or overstated;
- adds tests where a bounded repository test establishes a clause;
- records each added test's negative control.

The PR changes `config/dev-model.yaml`'s comment, so it is safety-critical and
operator-merge. **Subsequent disposition — 2026-10-04:** #946 merged as
`785c012414c94bdc335c84bf95f6747813ba1337`, and #919 was closed. This discharges
the earlier sessions' #919 open-status instructions.

**Review.** CodeRabbit skipped. Full two-lens fallback passes at `02642f54` and
`4497e8c` preceded the LOW repairs. The first LOW repair extended a control-flag scan,
and the adversarial lens disputed its containment, so no receipt was recorded for it. The
final repair `12b11e6` pins the shipped headless commands exactly instead. Its two-lens
`fallback:delta` receipt composes on the `4497e8c` panel. Dispositions and verdict lines
are on #946, which `pr_watch` reported converged and mergeable at `12b11e6`.

**Verified.** `env -u FORCE_COLOR DEVKIT_STATE_ROOT=<session scratchpad> make test` at
`12b11e6222b09798944ff6618be8873160182dc1` on 2026-10-04, in
`/Users/topi/Coding/agentic-dev-kit`, printed `4254 passed, 1 skipped in 651.24s
(0:10:51)`. CI's `Test` passed at that head.

**Filed** on the operator's approval of each exact text, each read back identical: #947,
holding the audit's remaining bounded-test gaps; occurrence comments on #120 and #720.

**Not established.** Client behaviour, agent-executed workflow steps, and a Codex
cockpit applying `lens_compute`; the record lists them. No live Linear payload or frozen
run was executed, and cs-toolkit was not touched.

______________________________________________________________________

## Session — 2026-10-04 (cs-toolkit repair delivery and adoption)

**Shipped.** [#943](https://github.com/topij/agentic-dev-kit/pull/943) merged as
`60b9727f65ee1bb7ffb5418f85e23d814cd4f1bd`, delivering #941 and #942.
cs-toolkit adopted that pin in [#2528](https://github.com/in-parallel-oy/cs-toolkit/pull/2528),
merged as `162b4601a39a68145e4c6b5b985e5430d9474058`. Configuration and decline decisions
were preserved. This delivery supersedes the earlier sessions' held-upgrade status.

**Adopter evidence.** `make check-root` and `make test-devkit` at
`9572a35feba59337f7a7392a7f11783185e0645d` on 2026-10-04, in
`/Users/topi/Coding/in-parallel/cs-toolkit`, passed as recorded on #2528. Their local
verification receipt retains the output hashes; #943 retains the final kit and
disposable-install receipts and independent review disposition.

**Limits and planning.** No live Linear payload or frozen run was executed. #919's
runtime audit and #6's live acceptance remain separate; #944 tracks the LOW CLI-help
reference. The briefing recommended #585, beginning with #921's classification-verdict
check; the operator has not selected that work. Other workstream starters are retained.

______________________________________________________________________

## Session — 2026-10-04 (cs-toolkit triage upgrade blockers)

**Implemented.** [#943](https://github.com/topij/agentic-dev-kit/pull/943) addresses
#941 and #942: controlled installed triage fixtures, asserted fault injections,
separate adopter-layout controls, and standalone triage entry-point metadata.
The generated manifest tracks the shared test helper; the CHANGELOG gives its refresh instructions.

**Verified.** `env -u FORCE_COLOR DEVKIT_STATE_ROOT=/private/tmp/devkit-triage-upgrade-20261004-GwSfUv/kit-sandbox make test`
at `273db1ed7fea679228551c5594e5d9d4e2e9b9fe` on 2026-10-04, in
`/Users/topi/Coding/agentic-dev-kit`, printed `4242 passed, 1 skipped in 654.36s (0:10:54)`.
Final-candidate kit and disposable declared-install receipts, CI and independent
review belong on #943. The reviewer found an optional-fixture dependency; the repair
keeps controlled policy in the helper those test modules already require.

**Authority and limits.** Merge and the next adopter pin remain operator decisions.
The operator supplied cs-toolkit checkpoint `f4047447cbafa7549e866f37db9ff7f88a5156b6`;
this session did not change it, its installed pin, legacy artifacts or host automation.
No live tracker write or frozen run was approved or attempted. #919 stays open for
its broader runtime audit. The operator assigned these repairs to the existing
cs-toolkit Codex validation and Linear installation workstream.

______________________________________________________________________

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
`ac7203341f50b5e39f5fe6f7f758b8f7e439cdf5`, as supplied by the operator; its local upgrade
work was held pending these upstream fixes. This session changed only the kit.
The new workstream assignment was not explicitly confirmed; it does not replace another workstream's starter.
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

**Status:** cs-toolkit installation [#2535](https://github.com/in-parallel-oy/cs-toolkit/pull/2535)
merged as `33816d5f9558024796fe08552e41164440ace88d` and was delivered with
kit pin `66a8044865e5ef43d633270c2ce224827de3aa35`. The retained TEST route
completed. Installed recovery captured the historical live reservation and
presented exact action digest
`1217af39a6eedcd2a4697bb34952a8941014bedd801de29bd46bfc3199094f2d`;
its decision remains pending. The operator established the owner facts and approved
installation/recovery/payload scope and clean merges. Actual action and live payload
bindings remain separate. **Owner:** [#6](https://github.com/topij/agentic-dev-kit/issues/6).

▶ Next: Resume installed recovery from the exact displayed action and the operator's
bound decision in the retained evidence; preserve quarantine bytes and read back the
safe-restart receipt. Then freeze a fresh live run, present its complete Linear payload
and immutable identity for exact approval, and read back approved writes. Preserve root
legacy artifacts, host automation and credentials; append acceptance evidence to #6.
