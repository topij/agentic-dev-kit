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

## Session — 2026-10-06 (one-run triage recovery paths removed, in Claude Code)

[#978](https://github.com/topij/agentic-dev-kit/pull/978) removed #969's `correct-project`
route and #952's historical flat-gate recovery. It merged as
`7c0f6de429f0a7e1a627d0b20e8eb952a46ac395`. The removal took their CLI flags, tests,
`KIT_OWNED` entries and workflow sections with it, and `recovery.py` is back to its #765
shape. Installation
[in-parallel-oy/cs-toolkit#2558](https://github.com/in-parallel-oy/cs-toolkit/pull/2558)
merged as `31dde6c28f4a15f6c9063ae3e500fb5fa26d2e75`. #975 is closed.

Decided: `model.py` keeps a shape check that lets a completed LIVE state carrying a
`proposal_correction` receipt parse. cs-toolkit's completed state carries one, and only a
session-starting entry retires a completed state. That entry also freezes the inbox and
starts a new run, so retiring the state early would have pre-empted cs-toolkit's scheduled
Friday draft. The check lets that draft retire the state under either engine.
`test_a_completed_state_with_a_project_correction_receipt_still_retires` pins it.
The check's removal is #979.

Also checked: no adopter state root on this machine holds a live historical flat gate.
cs-toolkit's recovery bundles are left as history.

Not established: the retirement itself. Read-only validation of cs-toolkit's real state passed
under both the kit and the installed code on 2026-10-06 (the commands are in #978's and
#2558's bodies). Neither ran the retirement.

cs-toolkit's main checkout was not pulled and still sat on its pre-install commit at
wrap-up. Its scheduled jobs run from that checkout, so the removal is live there only once
it is updated.

Review: #978 had one adversarial lens. Its LOW findings went to #979 and to this entry.
#2558 merged on CodeRabbit's comment-verdict of its head. The two-lens panel did not run
there, because the reviewer was available and the copied code was byte-identical to
#978's reviewed code.

______________________________________________________________________

## Session — 2026-10-06 (cs-toolkit LIVE acceptance completed, in Claude Code)

The operator judged the acceptance work over-built and chose the smallest fix for
the landed-Markdown hold. [#973](https://github.com/topij/agentic-dev-kit/pull/973)
compares tracker payloads with list markers outside fenced code spelled `-`. The
engine's existing resume reconciliation did the rest, with no new contract,
state shape or approval step. #973 merged as
`6aadec23ac4ac543b7381ca550cf03a5638602f1`. Installation
[in-parallel-oy/cs-toolkit#2551](https://github.com/in-parallel-oy/cs-toolkit/pull/2551)
merged as `fb0004704e2d43ccd1a3c21c4f85c0944b6811c6`, pinning it.

The installed `resume` verified TRI-01 as CUS-1670. Three finalize continuations
then archived TRI-01 through the engine's sweep
[in-parallel-oy/cs-toolkit#2552](https://github.com/in-parallel-oy/cs-toolkit/pull/2552),
which merged as `c84d76c6536cad8d0f0d131b8cb095463ad11a12`. The run completed.
[The acceptance record on #6](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-6012620438)
holds the commands, revisions, directories and results. #6 stays open. This
supersedes the earlier 2026-10-06 Codex entry's pending reconciliation design.

Filed on the operator's approval of each exact text, each read back identical:
- #974, the learning: classify a held state as a recurring defect or a one-off
  incident before building an engine mechanism.
- #975: remove the one-run triage recovery paths.
- #976, with a follow-up comment: LOW residue from #973's and #2551's reviews.

`project_correction.py`'s pin on the `providers.py` digest failed #973's first CI
run, although the project guard was untouched. The digest list is now append-only,
and #975 covers removing the pin along with its path.

Closed workstream cs-toolkit Codex validation and Linear installation: the
operator closed it once LIVE acceptance completed. Its follow-ups are #974, #975
and #976. The separate frozen kit-friction decision
(`469bcd5829244adeb17443d1a45a6c01`) remains pending and untouched; the new
*Kit friction-log triage* workstream carries it.

______________________________________________________________________

## Session — 2026-10-06 (cs-toolkit installed correction and landed Markdown hold, in Codex)

Source [#969](https://github.com/topij/agentic-dev-kit/pull/969) merged as
`01269cc80e05ecab1987ebaa97ee76bba306afee`; installation
[#2545](https://github.com/in-parallel-oy/cs-toolkit/pull/2545) merged and was
delivered as `cddb46c284d92b3261b0ec1977d82fa3a629cbcf`, pinning that source.
The operator authorized checked installation/archive/wrap-up merges and delegated
approval of the exact project-only action and complete corrected filing payload.
Concrete presentations retain that human text beside runtime-computed digests;
they do not invent a later human reply. Configured reviewers ran at
`gpt-5.6-sol` / `medium`; GitHub runner cancellations were retried at the same
reviewed head without a review waiver or permanent configuration change.

The installed correction applied action
`767e470416961a2aa43a0a0e422bd79d46ce47875b13bc2179139c0d8d9d82f9`,
retaining rejected evidence and clearing its approval. The approved corrected
create landed CUS-1670, but Linear changed Markdown bullets from `-` to `*`.
`libs/report-utils/.venv/bin/python live-62970e59-normalization-readback.py`
at `cddb46c284d92b3261b0ec1977d82fa3a629cbcf` on 2026-10-05 UTC, in
`/Users/topi/Coding/in-parallel/cs-toolkit`, recorded the ambiguous exact-payload
mismatch with mutation-prohibited marker searches, independent by-ID readback
and unchanged retained state/report/quarantine bytes. No duplicate create,
issue update, raw state edit, replacement freeze or TRI-01 archive followed.
[The acceptance record](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-6003071493)
retains the commands, actual results and digests. A bounded representation
reconciliation design awaits the operator before further engineering.
This entry supersedes the earlier project-name resume instruction; the separate
frozen kit-friction decision remains pending. Follow-ups #970 and #971 were
recorded without fixes claimed. Evidence remains under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/`.

______________________________________________________________________

## Session — 2026-10-05 (cs-toolkit LIVE recovery and project-name hold, in Codex)

The operator approved the installed recovery action
`1217af39a6eedcd2a4697bb34952a8941014bedd801de29bd46bfc3199094f2d`.
The installed invoker applied it and the retained verification helper read back
the exact quarantine bytes, original filesystem identities and safe-restart receipt.
Commands, directory, revision and date are retained in the recovery receipts under
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/`.
The primary adopter advanced to actual main
`bbcd3f167185518ff4860c6c80d523657452aef0`; its installed triage contract and
kit pin `66a8044865e5ef43d633270c2ce224827de3aa35` were preserved.

The replacement LIVE run froze session `62970e59c292424c8db6b8ae75f3e81e`.
The operator selected TRI-01 for preparation, parked the other candidates, then
approved its complete exact Linear payload. I incorrectly prepared the project
as `CS-ToolkitDev`; configuration and Linear use `CS-Toolkit Dev`. The adapter
rejected the payload before its create mutation, after the engine had persisted
an `attempting` record. The complete mutation-prohibited marker search found no
matching issue; its command, revision, date and directory are retained in
`live-62970e59-project-mismatch-marker-readback.json`. No identifier was returned.
Live acceptance remains incomplete, with the valid in-flight state preserved.
The installed workflow supplies no project correction for that phase; no raw
state edit, replacement freeze or source sweep was attempted. [#6](https://github.com/topij/agentic-dev-kit/issues/6#issuecomment-5995157879)
records the hold and correction. Resume from
`RESUME-LIVE-PROJECT-MISMATCH-62970e59.md` in the evidence directory.
The separate frozen kit-friction archive/park decision remains pending.

______________________________________________________________________

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

### Triage one-run cleanup

**Status:** #978 and its cs-toolkit installation removed the one-run recovery paths. A
shape check in `model.py` stays until cs-toolkit's completed LIVE state, which carries a
`proposal_correction` receipt, retires. **Owner:**
[#979](https://github.com/topij/agentic-dev-kit/issues/979).

▶ Next: once cs-toolkit's scheduled triage draft has retired its completed LIVE state,
confirm no state root holds a `proposal_correction`, then remove the shim (#979).

### Kit friction-log triage

**Status:** a kit budget triage froze inbox session `469bcd5829244adeb17443d1a45a6c01`
on 2026-10-05 and left it awaiting approval, with every inbox block preserved. Its
frozen inbox and pipeline state sit in an isolated state root,
`state/review-evidence/cs-toolkit-linear-acceptance_2026-10-04/finalize-decisions/kit-friction-budget-state/`;
the live `state/triage/` holds nothing for it. **Owner:** that retained state.

▶ Next: present session `469bcd58`'s retained proposals to the operator and obtain
their archive-or-park decisions before any other `triage-friction-log` sweep of the kit
inbox.
