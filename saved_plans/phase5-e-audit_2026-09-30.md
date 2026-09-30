# Phase 5 E — exit audit packet (PHASE5-E-AUDIT-01)

This is **milestone E** of the [completion plan](phase5-completion-plan_2026-09-18.md).
It does three things:

- audits the Phase 5 evidence against the agreed contract;
- names what is still owed;
- prepares the exact record and tracker changes an exit would need.

**It approves nothing and declares nothing.** Topi owns every acceptance, every scope
amendment, every tracker write and the exit declaration.

The completion plan's own wording governs every recommendation below:

- "if the acceptance contract changes, the final declaration must name that change.
  Never present reduced coverage as completion of the original full scope."
- "For each route, either produce the required evidence or obtain an explicit
  rationale, owner and placement for a changed scope."

The supporting evidence is in `state/review-evidence/phase5-e-audit-20260930/`
(gitignored): the grounding reads, custody checks, acceptance search, and the script
that took them. `collect.sh` there reruns everything, and writes only into that
directory. Each file below that is named without a path is in that directory.

## What is already decided

These are the operator acceptances and accepted limits on record.

**D-TRIAGE-RECOVERY, accepted as labelled synthetic.**

- Topi, in the Claude Code session of 2026-09-30: "I accept the Stage 1 and Stage 2
  RESULTS.md files."
- `ACCEPTANCE.md`, beside each `RESULTS.md` in
  `state/review-evidence/phase5-d-triage-recovery-01/` and `-02/`, records it.
- That record says each run's *Not established* list goes to this audit.

**Systemize live friction and tracker routes: acceptance amendment.**
`phase5-d-systemize-boundaries-01/APPROVAL.md` §1 (2026-09-23) records the answer
"Accept no-write (Recommended)". It sets three things:

- the live reconcile → propose → decline path is these routes' Phase 5 evidence;
- "the first genuine positive systemize friction or tracker write" is a residual,
  "carried to the scheduled run under #747. It is not a Phase 5 exit gate";
- the E audit "must cite it as such, not as exercised positive-write coverage."

**Systemize cap, batching, competing caches and hostile targets: accepted as labelled
synthetic.** The same file's §3 records the answer "Yes", "read as acceptance". It says
the E audit "must cite this as an acceptance of labelled synthetic coverage, not as
live-window coverage."

**RECOVERY-01's pre-approval cutpoint.** `phase5-d-systemize-recovery-01/APPROVAL.md`
§4 (2026-09-24) records "Stop; keep P as partial (Recommended)". The option's text was:
"Record P as the pre-approval cutpoint's evidence, with the /tmp deviation disclosed."

**Milestone B's accepted limits.** These accept named risks inside B's scope. None of
them accepts B as a whole.

- **The source-only acceptance of #744**, in
  `phase5-b-source-lifecycle-01-97801e82/approval.json` (2026-09-18): "I approve
  PHASE5-B-SOURCE-LIFECYCLE-01 under the recorded proposal seal, including its explicit
  source-only evidence limitations and conditional source merge."
- **The hosted runtime gap and branch metadata baseline**, in
  `phase5-b-fixture-delivery-01-4ecc2bdd/resume-execution/approval.json` (2026-09-18).
  Its `accepted_scope` reads: "Exact hosted runtime gap, observed branch metadata
  baseline, amended receipt and unchanged remaining native review/trust/conditional
  lifecycle only."
- **The repeated-interruption risk**, in
  `phase5-b-archive-repeat-interrupt-disposition-01/approval.json` (2026-09-19). Its
  scope reads "including the additional repeated-interruption risk", and the answer was
  "Yes, I approve the scope."
- **The metadata reconciliation**, in
  `phase5-b-archive-recovery-retention-01/administration-reconciliation-approval.json`
  (2026-09-20): "Accept only the exact enumerated .git/config and FETCH_HEAD changes".

**Credited before Stage A:** ITEM5-B-ACCEPT-01's ownership acceptance (2026-09-10).

**How the search was done.** Every other decision record for B, C and D holds approvals
to run, amend, file or merge.

- `collect.sh` listed the decision-bearing files under `state/review-evidence/phase5-*`
  in `decision-files.txt`.
  - It matched on name: `*accept*`, `*approval*`, `*decision*`, `*authoriz*`, `*amend*`,
    `AUTHORITY*` and `LIMITATIONS*`.
  - It looked to depth 3, at files under 1 MB, outside `runs/`, `cases/`, `fake/`,
    `handed/` and mutation trees.
- It wrote up to 20 `accept` lines per file to `acceptance-lines.txt`. The run was at
  `553ca5f` on 2026-09-30.
- Three read-only subagents searched the packets, the handoff and its history on the
  same day.
- A second check named four decision files the first search pattern missed. It read
  each and found no acceptance. The widened pattern above lists all four.

## Grounding reads

`collect.sh` ran from `/Users/topi/Coding/agentic-dev-kit` at
`553ca5f852e3276fffc95afd614fa90e16d93e0c` on 2026-09-30. The readings in this section
are from that run.

`collect.sh` ran again later that day, after #871 merged as `3bcb3a3`, to refresh the
packet's hash. #871 changed only `docs/kit-handoff.md` and
`docs/kit-handoff-history.md`. So `grounding.txt` now holds that rerun's readings,
which name `3bcb3a3`.

- **Protected branch.** `HEAD`, `origin/main` and the forge's `main` all read
  `553ca5f`. Push run `36666570597` for it read `completed` / `success`.
  `gh pr list --state open` listed no open kit pull request.
- **Fixture repository** `topij/adk-item5-b-field-20260909` (`fixture-prs.txt`):
  - PR #1 is `MERGED`: head `34ee83e5db84ff2664d888854781d61b2d1645f7`, merge
    `2b63a262d86e4352c5c92ddeb6fc99671fe5fac3`, at 2026-09-21T11:16:37Z, by `topij`.
  - PR #2 is `MERGED`: head `498e0cfb70ba7b6527bede5a6030cf76bbe75817`, merge
    `7b35c6543a27c918a6057afaf0d3e014fef9ab77`, at 2026-09-21T13:02:13Z, by `topij`.
  - Issue #3 is `OPEN`.
- **Kit pull requests** (`kit-prs.txt`), each `MERGED`: #765 `b808061`, #769 `cf83f20`,
  #771 `5165a3c`, #781 `902dbf6`, #790 `4c69ab2`, #865 `b13abb3`.
- **Kit issues** (`issue-states.txt`) are those listed in `collect.sh`. #255, #722,
  #786, #826, #862, #863 and #864 read `CLOSED`, and the rest `OPEN`.

## The contract

The exit is judged against these documents. The hashes were taken with
`shasum -a 256` at `553ca5f` on 2026-09-30.

| Document | SHA-256 |
|---|---|
| [Completion plan](phase5-completion-plan_2026-09-18.md), *E — Completion criteria* | `ac7501e4f6b716e6465ebf81b5746105e9ffef9b0ac0def39f000e9759d8597d` |
| [Stage A route ledger](phase5-stage-a-routes_2026-09-18.md), rows at lines 23–53 | `4330b4735cbada1854db62fd86585ddaba8eb920483b1a7ecceb3d541baf6fbf` |
| [D proposal](phase5-d-proposal_2026-09-21.md), its package table | `391673b612269fcb7496e2129433fa297dfdc5d95f7e82c8f0b9ff35d111518a` |
| [Acceptance matrix](phase5-item5-b-acceptance-decision_2026-09-10.md), *Remaining field-exit matrix* (line 281) | `ef9ad72f37e37cb059ea03534035c49e82ab0a45c7369279d70a8f6c853d9acf` |

The committed Phase 5 section of
[`codex-parity-plan_2026-08-23.md`](codex-parity-plan_2026-08-23.md) is also part of the
contract. That means its sprint-status delivery items 5 and 6 and its *Done when*.

**The acceptance matrix uses the Stage A rows.** Each of its rows maps to Stage A:

| Acceptance matrix row | Stage A line(s) |
|---|---|
| Preserved-file acceptance | 28 |
| Adoption friction and ready fixture PR | 30 |
| New fixture client loading/trust | 32 |
| Systemize live routing | 36–38 |
| Systemize engines | 39–41 |
| Systemize notifications | 42 |
| Systemize restart/recovery | 43 |
| Other systemize branches | 44–48 |
| Triage residual routes | 50–52 |
| Phase 5 item 5 exit | 53 |

So the ledger below uses Stage A's row names.

`packet-sha256.txt` hashes every local `saved_plans/phase5-*` packet at the latest
`collect.sh` run.

**The E criteria, in short:**

- B's adoption verification and PR lifecycle are complete at the recorded candidate,
  with local policy and custom-file functionality dispositioned.
- The required client behaviour is shown at named identities.
- Every applicable field-route row has adequate evidence **or an approved amendment**,
  and none is "unknown, failed, blocked or covered only by a proposed deferral".
- The item 6 replay stays bound to its original tuple.
- Exact handoff, sprint-status and tracker payloads exist, and Topi authorizes the exit
  and the external writes.

**The *Done when* clauses, and what carries each one:**

| Clause | Carried by |
|---|---|
| "an existing Codex adopter can upgrade without retaining stale runtime behavior or losing local policy" | The item 6 replay (credited), plus milestone B (E-1a) |
| "the remaining `#243` field exercises are complete" | This ledger, under the amendments E-7 names |
| "`#631` and `#608` carry their declarations" | Credited: the Phase 5 checklist's `[x]` items |
| "`#255`'s general mechanism is delivered" | Credited: the checklist records its delivery by #680, and #255 read `CLOSED` |
| The final adopter replay tuple | Item 6, bound to its original refs |

## Exit ledger

**Verdict classes.**

- **Credited** — Stage A credited it. This audit preserves it and asks nothing.
- **Accepted** — an operator acceptance or acceptance amendment is on record.
- **Decided** — the row waited for an operator decision, and that decision is on record.
- **Awaiting acceptance** — evidence exists but no acceptance is recorded.
  - Where the evidence falls short of the row's text, the gap is named.
  - **Accepting a row across a gap is itself an acceptance amendment**, and the
    declaration must name it (E-1).
- **Scope decision owed** — no evidence covers the row as written. It needs an approved
  amendment or new evidence (E-2).

Row names are Stage A's. The number is the row's line in
`phase5-stage-a-routes_2026-09-18.md`.

### Credited rows (no action)

| Row | Line | Evidence Stage A credits |
|---|---|---|
| Permissions and runtime declarations | 23 | Checklist deliveries #632, #635, #637, #639, #649, #655, #670, #667, #676, #680 |
| Initial cs-toolkit pilot, upgrade and reconciliation | 24 | cs-toolkit #2222, #2223 and #2255, as the checklist records them |
| Item 6 replay | 25 | [Replay record](cs-toolkit-replay_2026-09-09.md), its original tuple and accepted limits; #723's approved deferral |
| Parallel field batch | 26 | [Codex batch](codex-parallel-batch-live-validation_2026-09-01.md), #659 |
| Adoption inspection, staging, initialization and repair history | 27 | #682, #686 and the records the checklist links |
| Preserved-file ownership | 28 | ACCEPT-01 and its [execution](phase5-item5-b-acceptance-execution_2026-09-10.md) |
| #742 source repair and lifecycle | 29 | Sealed completion, merge `063b4f11` |
| Earlier Codex CLI/desktop hooks | 31 | [Batch](codex-hooks-batch_2026-09-07.md), [continuation](codex-hooks-continuation_2026-09-09.md) |
| Systemize test analysis/checkpoints | 35 | [Retained exercise](codex-systemize-test-field-exercise_2026-09-06.md) |
| Triage interactive LLM-only graduation | 49 | #673 and the committed graduation marker |

`git ls-files` at `553ca5f` on 2026-09-30 listed every committed record named here.
Later kit movement does not reopen the item 6 replay.

### Milestone B — retained fixture installation and PR (line 30): awaiting acceptance, with gaps

**Approval.** "I approve the bundled continuation. work autonomously based on the plan"
(`phase5-b-continuation-20260920/execution-approval.json`, 2026-09-21). The proposal it
approved includes conditional merges after verification and review.

- Each earlier B package has its own `approval.json` in its `phase5-b-*` directory.
- The memory-scope extension and the Sol / medium reviewer choice have no verbatim
  quote. Only two records carry them: flags in `memory-sol-continuation/authority.json`,
  and a summary in `execution/PROGRESS.md`.

**Delivery.**

- The merged source `db1e84ec` (#759) was installed and committed as `34ee83e5`, tree
  `22e0e6b8`, and published to fixture PR #1.
- PR #1 merged as `2b63a262`, with parent `8533c334`. The record is
  `execution/memory-sol-continuation/delivery/completion.json`, and the forge read is
  above.

**Verification**, as `execution/PROGRESS.md` records it:

- `bash verify-installed.sh` at `34ee83e5` on 2026-09-21, cwd
  `/private/tmp/p5ms-0921/author/fixture`, printed
  `2710 passed, 129 skipped in 537.22s (0:08:57)`.
- Hosted run `35589748843` at the same revision printed
  `2707 passed, 132 skipped in 321.71s (0:05:21)`.
- Before pytest, `verify-installed.sh` runs these steps under `set -euo pipefail`:
  - the installed doctor, against the source kit's manifest;
  - the adapter report;
  - `check_doc_budget.py`;
  - the shell parses.
- The author's outputs from those steps went to
  `/private/tmp/p5ms-0921/author/installed-baseline`, which is gone.
- The reviewers ran the same script at the same head.
  `delivery/fixture-review-disposition.md` records that the reviewers' "enabled
  `kit_doctor.py` against the independent source manifest succeeded".

**Review at `34ee83e5`.** Adversarial and correctness contexts ran GPT-5.6 Sol / medium.

- Adversarial reported no production defect.
- Correctness reported a P3 / LOW trailing-whitespace regression in test data. It was
  deferred to #761 (`delivery/fixture-review-disposition.md`).
- Before the merge, the installed `pr_watch.py 1 --json --no-persist` read converged
  and mergeable.

**PR04 findings.** The Stage A package maps PR04-A1, -A2 and -C1 (P1 / High), and -A3
and -C2 (P2 / Medium), to named regression nodes.

- Those nodes are in the current required coverage at `34ee83e5`
  (`delivery/fixture-historical-comment-reconciliation.json`).
- The first preparation check searched the B records on 2026-09-30. It found no record
  that names the PR04 IDs as resolved: the link runs through test names alone.

**Gaps and limits on record:**

- No passing local source `make test` is claimed at the final source head `e01aebac`
  (`PROGRESS.md`).
- The full-base `git diff --check` failure is preserved.
- `phase5-b-archive-test-docstring-01/LIMITATIONS.md` holds the cumulative list. It
  includes #561, #393, the ownership-only custom wrap-up and the pre-push
  unreadable-batch limitation.
- `completion.json` records `"phase5_complete": false`, and that "Phase 5 C/D and field
  exit remain separate".
- Open follow-ups: #754, #756, #757, #760, #761.
- Some B directories' modification times fall in the 2026-09-29 cleanup window. See
  *Evidence custody*.

### Milestone C

**Codex client loading and workflow behaviour (line 32): awaiting acceptance, with
gaps.**

- **Approval.** "Continue Phase 5 C using the prepared proposal. I approve its repair,
  isolated verification, reviews and conditional delivery. …"
  (`phase5-c-wrap-up-20260921/coordinator/authorization.json`, 2026-09-21).
- **Client.** `codex-cli 0.153.4`, GPT-5.6 Sol / medium, on 2026-09-21, in
  `/private/tmp/adk-p5c-client-20260921/sol-agent/valid-probe`.
- **What ran**, per `coordinator/EXECUTION.md`, *Native functionality and review*:
  - The client read the adapter and the shared workflow.
  - It updated the configured handoff and friction documents.
  - `check_doc_budget.py` and `git diff HEAD --check` succeeded.
  - The outcome was `incomplete-resumable`, because the probe prohibited publication.

**Gaps against the row**, which asks for "workflow execution and restoration at B's
actual candidate":

- The probe ran on base `2b63a262` plus the exact prepared adapter and synthetic
  inputs, uncommitted. The record says: "It is not represented as a run against the
  committed candidate."
- It ran in a disposable clone, not at the retained fixture path.
- "original global configuration restoration is not claimed" (*Preservation and
  disclosed deviations*).
- An author `git fetch` changed the retained fixture's fetch metadata.

**Failed attempts**, retained and not credited (author `EXECUTION-SUMMARY.md`):

- an unsupported flag combination;
- a sandbox denial of the state database;
- a limited probe that hard-stopped.

**Additional client coverage (line 33): scope decision owed.**

- Stage A says: "Topi must confirm whether desktop loading is additionally required …
  Until resolved, the ledger cannot claim full client coverage."
- The first preparation check found no such decision. It searched on 2026-09-30 for
  "desktop", "additional client", "client coverage" and "Claude coverage" across the
  `phase5-*` packets, the B, C and D evidence and the handoff.
- The C records exclude Claude coverage without deciding it
  (`coordinator/EXECUTION.md`).
- Decision E-2a.

**Custom Codex wrap-up functionality (line 34): awaiting acceptance.** The repair route
was chosen (`next-phase-preparation/CODEX-WRAP-UP-PROPOSAL.md`), under the C
authorization above.

- **Delivery.** Fixture PR #2, reviewed head `498e0cfb`, merged as `7b35c654`.
- **Hosted verification.** Run `35598288228` at `498e0cfb` on 2026-09-21 printed
  `2707 passed, 132 skipped in 357.29s (0:05:57)`.
- **Review.**
  - Adversarial found no actionable defect.
  - Correctness found a LOW / P3 coverage gap, ticketed as private issue #3.
  - The reviewers' nested native control and mutant attempts failed before any model
    turn, so they earn no test credit.
- **Limits.** The functionality evidence is the local probe above, which "does not
  claim external-service or Claude acceptance."

### Milestone D — systemize rows

| Row (line) | Evidence | Verdict |
|---|---|---|
| Live shared-rule routing (36) | D-SYSTEMIZE-LIVE-01: rule [PR #771](https://github.com/topij/agentic-dev-kit/pull/771) merged as `5165a3c`, with a tree equal to reviewed head `347d323` (`logs/51-merge.txt`) | Awaiting acceptance (E-1c) |
| Live friction routing (37) | Same run: reconcile → propose → decline, with no write | **Accepted**, by acceptance amendment (BOUNDARIES `APPROVAL.md` §1) |
| Live tracker routing (38) | Same run: no payload qualified, and there was no write | **Accepted**, by the same amendment |
| Fetch engine (39) | #769 (`cf83f20`), run engine-backed in the LIVE window 2026-08-26..2026-09-22. `cat logs/*.exit`, read at `553ca5f` on 2026-09-30, printed only `0` (`live-exit-codes.txt`) | Awaiting acceptance (E-1c) |
| Digest engine (40) | Same | Awaiting acceptance (E-1c) |
| Heartbeat engine (41) | Same: heartbeat `start`, ticks and `complete` exited `0` in LIVE. #783 is open: `start` reopens a completed run. Not scheduled | Engine: awaiting acceptance (E-1c). Scheduling: scope decision owed (E-2c) |
| Notification service (42) | LIVE sent one Slack DM (detail below) | Send, identity and read-back: awaiting acceptance (E-1c). Full thread read and approval provenance: scope decision owed (E-2b) |
| Process crash/restart (43) | RECOVERY-01 and RECOVERY-02, synthetic (detail below) | Awaiting acceptance as labelled synthetic, which is an amendment (E-1d). Real-service ambiguity: scope decision owed (E-2d) |
| Cap-triggered omission (44) | D-SYSTEMIZE-BOUNDARIES-01 | **Accepted**, labelled synthetic |
| Batched analysis (45) | Same | **Accepted**, labelled synthetic |
| Competing cache mtimes (46) | Same | **Accepted**, labelled synthetic |
| Hostile artifact targets (47) | Same | **Accepted**, labelled synthetic |
| Fresh-client context discovery (48) | D-FRESH-CONTEXT-01 (detail below) | Awaiting acceptance, with gaps (E-1e) |

**The LIVE Slack DM (line 42).** From `logs/40-notification-attempt.txt`:

- the content hash was persisted before the send;
- the send returned channel `D083840DP7B`, ts `1790183998.138169`;
- the DM was read back through a channel read, not a thread read;
- sender and recipient are both `U082VD4SR2N`;
- it was not used as an approval channel.

**RECOVERY-01 and RECOVERY-02 (line 43).**

- RECOVERY-01 Stage 1: `compare.py` printed `all fields match` for every case
  (`RESULTS.md`).
- RECOVERY-01 Stage 2 stopped after run P.
- RECOVERY-02 measured Claude agents (`claude -p --model fable`), one synthetic sample
  per cutpoint. It found: "a second create after a lost receipt, did not occur in either
  chain" (`RESULTS.md`).

**FRESH-CONTEXT-01 (line 48).** A fresh Codex context was given only
`$post-merge-systemize test`.

- It found the adapter "by injection", and it found the shared workflow.
- It read the config, overlay included, and chose engine-backed mode.
- It deviated from the workflow in two ways, recorded as findings: it made no merged-PR
  read of its own before `start`, and it ran `--verify` late.
- "Which model served the run" is not established.
- The record ends: "Whether it discharges the row is the Phase 5 E audit's call"
  (`RESULTS.md`).
- #802 is open for the trust entry that `codex exec` wrote.

**How the D packages map to these rows:**

| D package | Stage A line(s) |
|---|---|
| PHASE5-D-SYSTEMIZE-ENGINE-01 (#769) | 39–41 |
| D-SYSTEMIZE-LIVE | 36–38; also 42, as the systemize half of D-SERVICE |
| D-SYSTEMIZE-RECOVERY-01 and -02 | 43 |
| D-SYSTEMIZE-BOUNDARIES | 44–47 |
| D-FRESH-CONTEXT | 48 |

**Approval records.** None of these is an acceptance, except where *What is already
decided* says so:

- `phase5-d-systemize-engine-01/approval.json`;
- LIVE's `APPROVAL.md` and `STAGE2-APPROVAL.md`;
- RECOVERY-01's `APPROVAL.md` and `DECISION-post-dispatch-20260924.md`;
- RECOVERY-02's `APPROVAL.md`;
- FRESH-CONTEXT's `APPROVAL.md` and `AMENDMENT-1.md`.

**Engine delivery limits.**

- #769's installed check ran in a disposable vendored install at `46288b0` on
  2026-09-23. It reported `3 failed, 3109 passed, 137 skipped`.
- #769's body says the same three tests fail in a baseline install at `92926ca`, and
  that none of them is a systemize test.
- The same install ran heartbeat `start`, fetch, digest and `complete` in test mode
  against a fake `gh`.

**Open systemize engine and workflow defects:**

- #772: panel-only PRs have no findings systemize can see.
- #773: finding text is truncated.
- #774: routing of an addressed single-PR cluster.
- #777: cleanup after a parent retarget.
- #778: a raw bundle from another run date is accepted.
- #783: `start` runs after completion.
- #784: a kill leaves a hidden temp copy.
- #787: the overlay wording.
- #788: `FAKE_GH` is loose.
- #791: the dispatch protocol is pinned only as prose.
- #792: concurrent LLM-only runs.
- #794: the marker search.

### Milestone D — triage rows

| Row (line) | Evidence | Verdict |
|---|---|---|
| Draft/finalize engines (50) | PHASE5-D-TRIAGE-ENGINE-01, D-TRIAGE-RESIDUAL and later sweeps (detail below) | Awaiting acceptance, with a gap (E-1f) |
| Notification service (51) | **None**. Stage T, Stage L and the 2026-09-06 graduation each record `notification-thread` as degraded. The CLI "has no notification-service flag" (`workflows/triage-friction-log.md`). Stage L's *Not established* names "Notification-thread approval (N1; the CLI has no notification provider; #198)" | Scope decision owed (E-2b) |
| Parked entries (52) | The Stage A parks waited for "fresh exact decisions" (detail below) | **Decided** |
| D-TRIAGE-RESIDUAL (proposal table) | As line 50. Its packet says "**This package cannot close the row.**", and sends the notification-thread item to E | Awaiting acceptance for the engine routes (E-1f) |
| D-TRIAGE-RECOVERY (proposal table) | Stage 1 at `197a242`, Stage 2 at `b13abb3`, synthetic | **Accepted** on 2026-09-30, as labelled synthetic |

**The triage engines (line 50).**

- #765 (`b808061`) delivered them, with a tree equal to reviewed head `20ef06b`.
- D-TRIAGE-RESIDUAL ran Stage T in test mode.
- Stage L ran live, engine-backed sessions A and B. Each completed as `completed` /
  `archive-sweep` / `degraded-success`, the degradation being the notification row
  (`phase5-d-triage-residual-01-stage-l/RESULTS.md`).
- Later engine-backed sweeps followed: #817, #819, #840 and #847, each merged on
  Topi's word.

**The triage half of D-SERVICE** has no package and no evidence directory. Line 51 is
its row.

**How Topi decided the Stage A parks (line 52):**

- **The 2026-08-22 panel-rounds entry** was archived by D-TRIAGE-RESIDUAL Stage L
  session B in #805 (`bb0ebed`), as its annotated fresh identity. The archive notes that
  it had already graduated to `AGENTS.md`'s *Prose that goes false*.
- **The two 2026-08-27 entries** were archived without filing by triage session
  `3058c6ec` in #847 (`261cc83`). That triage run was outside the Phase 5 packets. The
  first preparation check confirmed that their archived bytes hash to Stage A's digests
  `8c427cec…` and `d1dba827…`.
- `docs/kit-friction-log.md`, read at `553ca5f` on 2026-09-30, has no dated entry
  section. So no live inbox entry carries a Stage A park.

**The D-TRIAGE-RECOVERY *Not established* lists** go to E. Stage 2's list extends Stage
1's. Together they name:

- real-service ambiguity from a crash;
- concurrent recovery races;
- scheduled or worktree runners, and any Codex-runtime run;
- notification-thread approval;
- field installation;
- `retire-terminal-invalid-state`, which Stage L's L0 covers;
- a `state-present-prepared` bundle whose owner is alive;
- a real hostname change (#867);
- a `.tmp` gate name left by an earlier recovery.

**Other triage engine limits on record:**

- "a real same-day pair of triage runs, and retirement against the real forge"
  (handoff, 2026-09-26);
- the #826 resume against a real crash, and #829's wait against the live API
  (handoff, 2026-09-27).

**Open triage engine defects:** #856, #857, #859, #867, #869.

- The *Triage engine hardening* workstream's owner line names #856, #857 and #859.
- The 2026-09-29 session entry says #869 fits that workstream, and that entry left the
  workstream alone.

### Phase 5 exit and tracker/record updates (line 53): this packet

This packet is the audit this row calls for. The exit itself, the exact payloads and
Topi's authorization are decision E-7.

## Residual register

This lists every residual a D record routes to E, and every gap a row leaves, with a
proposed disposition.

**What "accepted limitation" means here.** Topi accepts the item as a limit of the
Phase 5 evidence. Topi is then its owner, and the exit declaration, which names it, is
its placement.

The column *Routed from* says where each residual comes from.

| Residual | Routed from | Proposed disposition | Owner / placement |
|---|---|---|---|
| Claude and dual-runtime coverage of an adopted fixture | Stage A line 33 | Amendment E-2a | Phase 6's recorded scope: "Add fresh-repository fixtures for Codex-only, Claude-only, and dual-runtime adoption"; "Keep Claude integration smoke tests beside them where automation credentials permit" |
| Claude fresh-context discovery | FRESH-CONTEXT `RESULTS.md` | Amendment E-2a | The same Phase 6 scope |
| Codex desktop loading of the fixture | Stage A line 33 | Amendment E-2a: accepted limitation. Phase 6 has no desktop item | Declaration |
| Notification approval provenance (both workflows) | Stage A lines 42, 51; D-TRIAGE-RESIDUAL packet; D-TRIAGE-RECOVERY lists | Amendment E-2b | #198, which records the one-identity defect this rests on |
| Systemize's full thread read | Stage A line 42 | Amendment E-2b: accepted limitation | Declaration |
| Triage notification service; scheduled triage runs, which hard-stop without a notification provider | Stage A line 51; D-TRIAGE-RESIDUAL packet | Amendment E-2b: accepted limitation. A provider is new implementation scope | Declaration; alternatively a new issue (E-2b) |
| Scheduler wiring; scheduled or worktree systemize runners | Stage A line 41; LIVE; RECOVERY-02 | Amendment E-2c: accepted limitation | Declaration. #747 is the related open issue that the 2026-09-23 amendment already uses for the scheduled run's first positive write; its title is report durability on a worktree cron |
| Worktree triage runners | D-TRIAGE-RECOVERY lists | Amendment E-2c: accepted limitation | Declaration |
| Real-tracker marker search (R1) | RECOVERY-02 | Amendment E-2d | #794 |
| Real-service lost-receipt ambiguity beyond the marker search, in both workflows | Stage A line 43; RECOVERY-01 packet; D-TRIAGE-RECOVERY lists | Amendment E-2d: accepted limitation. The synthetic chains and the triage engine's scripted-provider tests (the #826 and #829 records) cover the local protocol | Declaration |
| Concurrent systemize runs | RECOVERY-02 | Amendment E-2d | #792 |
| Concurrent triage recovery races | D-TRIAGE-RECOVERY lists | Amendment E-2d: accepted limitation. The owner gate is the designed exclusion, and no race was exercised | Declaration |
| Codex-runtime recovery runs, both workflows | RECOVERY-02; D-TRIAGE-RECOVERY lists | Accepted limitation. Systemize's agent cutpoints were measured with Claude agents only; triage recovery drove the CLI directly, with no agent | Declaration |
| Engine installation into an adopter's field checkout | ENGINE, LIVE, D-TRIAGE-ENGINE and D-TRIAGE-RECOVERY records; history, 2026-09-23 ("Field installation is Phase 5's own row") | Amendment E-2e | New issue P-6 (recommended), or the next cs-toolkit upgrade, which the 2026-09-26 (triage engine fixes) session entry, now in `kit-handoff-history.md`, records as having no sprint-plan placement |
| A real same-day pair of triage runs; retirement against the real forge; #829's wait against the live API; the #826 resume against a real crash | Handoff, 2026-09-26 and 2026-09-27 | Accepted limitation | Declaration |
| `state-present-prepared` bundle whose owner is alive | D-TRIAGE-RECOVERY Stage 2 | Accepted limitation: the CLI cannot reach it (packet, *Excluded*) | Declaration |
| A real hostname change | D-TRIAGE-RECOVERY Stage 2 | Carried | #867 |
| `.tmp` gate name left by an earlier recovery | D-TRIAGE-RECOVERY Stage 2 | Accepted limitation | Declaration |
| Kills at other points, including the report write; process-tree behaviour seen through `ps` observations alone | RECOVERY-01 `RESULTS.md` | Accepted limitation | Declaration |
| Behaviour against the real living docs under a kill | RECOVERY-02 (E1 removed the docs) | Accepted limitation. LIVE ran against the real living docs, without a kill | Declaration |
| One sample per cutpoint; a single fresh-context sample | RECOVERY-02; FRESH-CONTEXT | Accepted limitation | Declaration |
| Fresh context: adopter-profile and trusted-project behaviour, live mode, real forge, which model served, and discovery by an agent that cannot read the harness | FRESH-CONTEXT `RESULTS.md` | Accepted limitation | Declaration |
| Fresh context: the merged view of leaves other than `notify.user_key` | FRESH-CONTEXT `RESULTS.md` | Accepted limitation. #787 records that the overlay can set only that leaf | Declaration; #787 |
| B's source and whitespace gaps, and C's restoration and probe-identity gaps | Ledger, B and C | Named gaps of E-1a and E-1b | Declaration |
| Missing sealed fixtures, and the B directories in the cleanup window | This audit | E-3 | E-3 |

**Routed to E and since discharged** (no disposition needed):

- `retire-terminal-invalid-state`, discharged by Stage L's L0;
- RECOVERY-01's post-dispatch cutpoint, exercised synthetically by RECOVERY-02 (the
  `D`/`D2` and `N`/`N2` chains).

The second item is still subject to E-1d.

## Evidence custody

**What was checked.** `collect.sh` ran `shasum -a 256 -c` on every `SHA256SUMS*`,
`EVIDENCE-SHA256SUMS` and `*.sha256` file under the `phase5-d-*` directories.

- It searched at any depth outside `runs/`, `cases/` and `fake/`, and checked each
  manifest from its own directory.
- The run was at `553ca5f` on 2026-09-30. `custody-check.txt` holds every line that
  was not OK.
- It also listed the evidence directories whose modification time falls between 15:00
  and 15:20 local on 2026-09-29 (`cleanup-window-dirs.txt`).

**Sealed fixtures are missing from two D directories.**

- In `phase5-d-systemize-recovery-01/`:
  - `SHA256SUMS` and `EVIDENCE-SHA256SUMS` list `fixtures/cases.json` and the per-case
    fixtures that `custody-check.txt` names;
  - `stage2/SHA256SUMS-stage2` lists `../fixtures/RC.json`;
  - all of them are missing.
- In `phase5-d-systemize-boundaries-01/`, `SHA256SUMS` lists nine fixtures, all
  missing: `fixtures/B60.json`, `B61.json`, `B75.json`, `B76.json`, `CP.json`,
  `CQ.json`, `H.json`, `H2.json` and `M90.json`.
- The generators (`gen_fixture.py`, `gen_corpus.py`), predictions, expectations, logs
  and `RESULTS.md` files are all present.
- The first preparation check searched these directories' records on 2026-09-30 and
  found none that discloses the removal.

**When the fixtures went, and what that suggests.** The two directories were last
modified at 2026-09-29T15:07:55+0300 and 15:08:01+0300. Other directories changed in
the same minutes:

- `phase5-b-archive-source-publication-01-9aaac906`;
- `phase5-b-archive-source-review-01` to `-06`, and `-05a`;
- three 2026-09-13 ITEM5-B P3 directories: `lifecycle-readonly-01-20260913`,
  `item5-b-p3-kit01-execution-20260913` and `item5-b-p3-kit02-resume-20260913`.

  These are behind the credited rows, not milestone B.

#861 describes a cleanup of `state/review-evidence/` that day. Its table counts
"fixtures … not bound by any manifest or linked from any record" among the removed
rows.

**That cleanup is an inferred cause, not a recorded one.** The only link is the shared
minutes. And #861 describes its population as run directories "from
2026-09-13..2026-09-20", while these two D directories date from 2026-09-23 and
2026-09-24.

**Failures the directory's own record explains:**

- **Pre-run seals.** These manifests are pre-run seals, and `APPROVAL.md` changed after
  them:
  - `SHA256SUMS` in RECOVERY-01 and in D-TRIAGE-RECOVERY-01;
  - `SEAL-predictions.sha256` in D-TRIAGE-RECOVERY-01.

  The final `EVIDENCE-SHA256SUMS` binds the final file.
- **Self-listing.** RECOVERY-02's `EVIDENCE-SHA256SUMS` lists itself.
- **Attempt seals.** RECOVERY-02's `harness/logs/SHA256SUMS-attempt*` name files
  relative to `harness/`. They were rerun from there, at `553ca5f` on 2026-09-30
  (`recovery-02-attempt-seals-from-harness.txt`):
  - attempt 3 printed only a format warning;
  - attempts 1 and 2 show the post-seal changes that `logs/deviations.txt` discloses.
- **Format warnings.** Some manifests print a warning for a timestamp or blank line:
  - D-TRIAGE-RECOVERY-01's `SHA256SUMS` and `SEAL-predictions.sha256`;
  - all three D-TRIAGE-RECOVERY-02 manifests;
  - RECOVERY-02's `harness/SHA256SUMS`;
  - attempt 3's seal.

**Manifests whose paths do not resolve from their own directory.** These are recorded
without a finding.

- **`phase5-d-systemize-engine-01/packet.sha256`** names a repository-relative path. It
  was run from the repository root at `553ca5f` on 2026-09-30, and printed `OK`
  (`engine-packet-from-root.txt`).
- **`phase5-d-fresh-context-01/staging/seal/SHA256SUMS`** binds `/private/tmp` workspace
  files.
- **`phase5-d-triage-retire-01-stage0/prod-before.sha256`** binds the live triage state
  that Stage L later retired.
- **The `inbox.py.orig.sha256` of a lens under `phase5-d-triage-engine-01/`** names the
  repository-relative `scripts/lib/triage/inbox.py` as it stood at that review. That
  file has changed since.

**These manifests printed no failing line** apart from the format warnings above:

- `phase5-d-fresh-context-01` (`EVIDENCE-SHA256SUMS`) and its `-prep-20260924`;
- `phase5-d-preparation-20260921/proposal-binding.sha256`;
- `phase5-d-systemize-live-01`;
- `phase5-d-systemize-recovery-02-prep-20260924`;
- RECOVERY-02's `harness/SHA256SUMS`;
- `phase5-d-triage-recovery-01` (`EVIDENCE-SHA256SUMS`);
- all three manifests of `phase5-d-triage-recovery-02`;
- `phase5-d-triage-recovery-prep-20260929`;
- both `phase5-d-triage-residual-01` directories;
- `phase5-d-triage-retire-01-stage0` (`SHA256SUMS`).

**Not re-verified:**

- the B and C namespaces' binding JSONs;
- the D directories that have no manifest: `phase5-d-systemize-recovery-prep-20260923`,
  `phase5-d-triage-recovery-02-prep-20260929`, and `phase5-d-triage-engine-01` at its
  top level.

B's `verify-installed.sh` sub-outputs were written under `/private/tmp` by design, and
are gone.

## Decisions

Each is Topi's. The recommendation comes first.

### E-1 — Accept the rows awaiting acceptance

Accept one group at a time, at the limits and gaps the ledger names. Accepting a group
means three things:

- its evidence is accepted as adequate for Phase 5 at those limits;
- where the ledger names a gap against the row's text, the acceptance is an amendment,
  and the declaration names it;
- the group's residuals take the dispositions in the register.

| Group | Rows | What is accepted, and the gaps it amends |
|---|---|---|
| E-1a | B (line 30) | Fixture adoption and PR lifecycle at `34ee83e5` / merge `2b63a262`. **Gaps:** PR04 findings are linked through test names only; the author's doctor, adapter and budget outputs are gone (the reviewers' runs record the doctor's success); no passing local source `make test` at `e01aebac`; the full-base `git diff --check` failure. Open: #754, #756, #757, #760, #761 |
| E-1b | C (lines 32, 34) | Codex CLI loading and the repaired custom wrap-up. **Gaps:** the probe ran on uncommitted exact bytes over `2b63a262`, not at the committed candidate or the retained path; publication was prohibited; global-config restoration is not claimed. Open: private issue #3 |
| E-1c | Systemize lines 36, 39, 40, 41 (engine only), 42 (send, identity and read-back only) | The live rule route, the engine set run engine-backed in a live window, and the Slack service route. **Gap:** a channel read, not a thread read. Open: the systemize defects the ledger lists |
| E-1d | Systemize line 43 | Crash/restart **as labelled synthetic**: one sample per cutpoint, with P as the pre-approval evidence. This amends the row as BOUNDARIES §3 did its rows. The D proposal says "synthetically covered live routes are not completion of the original contract" |
| E-1e | Systemize line 48 | Fresh Codex context discovery, one sample under A1 / B1 isolation. **Gaps:** the serving model is not established, and the adapter was found by injection. Open: #802 |
| E-1f | Triage line 50, D-TRIAGE-RESIDUAL | Engine-backed draft, park, file, sweep and merge read-back, run interactively with notification degraded. **Gap:** no "notification-thread approval identity/digest" (D proposal's D-TRIAGE-RESIDUAL row). Open: #856, #857, #859, #867, #869 |

**Alternative:** reject any group and name the evidence still wanted. That row then
blocks the exit.

### E-2 — Scope amendments

Each changes the acceptance contract, and the declaration must name it.

**E-2a — Additional client coverage (line 33).**

- **Recommended:** Phase 5 requires no additional client. The reasons:
  - The fixture's declared runtime is Codex.
  - Claude and dual-runtime adoption fixtures, trusted Codex smoke tests and Claude
    integration smoke tests are already in Phase 6's recorded scope. The Claude smoke
    tests carry the condition "where automation credentials permit".
  - Codex desktop loading has no Phase 6 item, so it becomes an accepted limitation.
- **Alternative:** name the client and task, and run it before the exit.

**E-2b — Notification: approval provenance and the full thread read (line 42), and the
triage notification service (line 51).**

- **Recommended:** none of these is a Phase 5 gate. The reasons:
  - #198 records that the connector sends as the operator. A DM and its reply therefore
    share one identity, and neither workflow can prove approval provenance
    mechanically.
  - The triage CLI has no notification provider, so a scheduled triage run hard-stops
    by declaration. A provider is new implementation scope. It is an accepted
    limitation here, not work #198 describes.
  - The service route itself (send, returned identity, read-back) is shown by LIVE's DM.
- **Alternative (i):** a labelled `[TEST]` triage DM with a thread read-back. It proves
  only the service route LIVE showed, plus the thread read.
- **Alternative (ii):** file an issue for a triage notification provider as the carrier,
  instead of the accepted limitation.

**E-2c — Scheduling (line 41) and worktree runners.**

- **Recommended:** accept as a limitation. #747 stays the related open issue, as the
  2026-09-23 amendment already uses it.

**E-2d — Real-service crash ambiguity.** Stage A line 43 asks for "exact payload
authority and readback, not a synthetic success claim". The D proposal adds:
"real-service ambiguity needs its own exact payload/send authority." Accepting
synthetic evidence alone therefore changes the contract.

- **Recommended:** accept the change. The owners are those in the register: #794 for
  R1, #792 for concurrent systemize runs, and accepted limitations for the rest.
- **Alternative:** a real-tracker run under an exact payload approval, after #794's fix.

**E-2e — Engine installation into an adopter's field checkout.** This is treated as an
amendment for three reasons:

- Stage A's engine rows (39–41, 50) read "unavailable in observed kit/source/fixture".
- The D proposal ties field payloads to "separately authorized delivery and
  installation".
- The 2026-09-23 history judgment calls field installation "Phase 5's own row".

The engines ran engine-backed only in the kit's own checkouts. #769's disposable
installed check also ran them, in test mode.

- **Recommended:** accept the change, and file P-6 as the carrier.
- **Alternative:** leave it to the next cs-toolkit upgrade. The engines are listed in
  `kit-manifest.json`, so that upgrade installs them. The 2026-09-26 (triage engine
  fixes) session entry, now in `kit-handoff-history.md`, records that upgrade as having
  no sprint-plan placement.

### E-3 — Custody

**Recommended:**

- accept the missing fixtures as a custody limitation of RECOVERY-01 and BOUNDARIES-01.
  The BOUNDARIES rows were accepted on 2026-09-23, before the modification times above.
- P-4 is already posted: Topi approved its revised text in this session, and it went
  to #861 as
  [issuecomment-5905162617](https://github.com/topij/agentic-dev-kit/issues/861#issuecomment-5905162617)
  on 2026-09-30, read back identical;
- accept that the B and ITEM5-B P3 directories in the cleanup window are not
  re-verified.

**Alternative:**

- regenerate the fixtures from the retained generators, and compare them with the
  sealed hashes before E-1d;
- re-verify the B bindings, bounded, before E-1a.

### E-4 — #7 and #748

These are not exit gates. The handoff has carried them since 2026-09-23.

**#7.** The 2026-09-23 judgment in the history says "nothing in #7's list is outstanding
once item 4 merges". The first preparation check found that wrong. The facts below
replace it.

#7's work items, against what shipped:

1. **Vendor `heartbeat_cli.py`:** shipped by #769.
2. **Vendor fetch and digest "behind the same forge abstraction as #6":** shipped by
   #769, but behind systemize's own `scripts/lib/systemize/forge.py`, not #6's. #6 is
   still open.
3. **Config-drive the thresholds:**
   - `lookback_days`, `pattern_threshold`, `batch_size`, `single_pass_max_prs` and the
     operator logins were already config keys from #595 (`6e88ca4`).
   - `review_sources` is served by `review.bots` plus `systemize.operator_logins`
     (`workflows/post-merge-systemize.md:190-193` at `553ca5f`, the trusted
     review-source set).
   - #769 added `heartbeat_job` and `heartbeat_pattern`.
4. **Correct the skill banner and README:** #595 did the banner, and #781 README.

The body's `nightly_digest.py`, a "related digest path", was not shipped.

- **Recommended (A):** close #7 as completed with P-3a. The configured engine set is
  complete, and the comment names the two differences.
- **(B):** keep #7 open, narrowed to a forge abstraction shared with #6.

**#748.** Topi put it in #769's scope: `phase5-d-systemize-engine-01/approval.json`
records "issue_748_scope": "Yes, in this PR". What shipped:

- Forge thread resolution is now the evidence: `thread_addressed`,
  `scripts/lib/systemize/normalize.py:98-104`.
- Review-body findings map to `unevidenced` (`normalize.py:145-147`).
- The forge query always requests `isResolved` and `isOutdated` (`forge.py:46`).
- A failed forge read stops the run.

Two differences from the issue's suggestions:

- **Suggestion 2** wanted `outdated` distinct, with only unresolved-and-current threads
  worth attention. `outdated` is distinct in the digest. But the workflow counts every
  state except `addressed` toward the unaddressed finding count
  (`workflows/post-merge-systemize.md:348-353` at `553ca5f`), and calls `outdated`
  "inconclusive".
- **Suggestion 3** wanted an honest unknown. The inconclusive states `outdated` and
  `unevidenced` supply one. A thread that is neither resolved nor outdated, including
  one with a missing field, maps to `unaddressed`.

The 2026-09-23 history judgment rated suggestion 3 as "only partly met".

- **Recommended (A):** close #748 as completed with P-3b. P-3b states the counting
  choice.
- **(B):** keep #748 open, narrowed to whether `outdated` should count toward the
  unaddressed total.

### E-5 — Commit the local `saved_plans/phase5-*` packets?

The kit repository is public.

- `untracked-saved-plans.txt` lists the untracked Phase 5 files: the
  `saved_plans/phase5-*.md` packets, this one among them, and
  `saved_plans/phase5-stage-a-evidence_2026-09-18/`.
- **A `grep` scan of the other packet markdowns** was run in this session on 2026-09-30.
  It is not part of `collect.sh`, and it ran before this packet existed; this packet
  lists the patterns, so it would match itself.
  - It matched none of these patterns: `ghp_`, `github_pat_`, `xox[bpa]-`, `sk-ant`,
    `CF-Access`, `Bearer`, `password`, `secret=`.
  - It did match three things that committed files already carry: the Slack recipient
    and DM channel IDs, `/Users/topi` paths, and the private fixture repository's name.
- **The Stage A evidence directory** holds material that is not packet prose:
  - copies of fixture files and issue comments from the private repository;
  - a personal e-mail address;
  - Python files that `make lint` would start linting once tracked.
- The packets link into gitignored `state/` evidence. Those links do not resolve on the
  forge.

Options:

- **Recommended (A):** commit the packet markdowns in the exit record PR. Leave out the
  Stage A evidence directory, and leave out `fabro-review-tool-assessment_2026-09-25.md`,
  which is kept local on purpose. The parity plan then links to committed documents.
- **(B):** commit only the completion plan, the Stage A ledger, the D proposal and this
  packet.
- **(C):** commit nothing. The exit record cites the packets as local files, by
  SHA-256.

### E-6 — #243

The completion plan requires #243's disposition to "account for its adapter template,
hostile-appended-instruction and doctrine-citation residue in the recorded Phase 6
scope".

- **Recommended:** post P-2. #243 stays open for that residue.

### E-7 — The exit declaration

**If E-1 to E-6 are decided as recommended:**

- Every applicable row is credited, decided, accepted, or accepted under a named
  amendment.
- No row is then unknown, failed, blocked or covered only by a proposed deferral.
- The item 6 replay stays bound to its original tuple.

Topi may then:

- declare the exit with the wording below;
- approve P-1 and P-5 for an exit record PR;
- approve each tracker payload by its exact text.

Closing the *Phase 5 exit* workstream is Topi's call.

**If any E-1 group is rejected, or an E-2 amendment declined**, the exit waits for the
evidence that decision names.

**Declaration wording:**

> I declare Phase 5 complete under PHASE5-E-AUDIT-01, on these amendments to its
> acceptance contract:
>
> - the systemize friction and tracker no-write amendment of 2026-09-23;
> - the synthetic acceptances of 2026-09-23 (systemize boundaries) and 2026-09-30
>   (D-TRIAGE-RECOVERY);
> - E-1a to E-1f, each with the gaps its row names;
> - E-2a to E-2e;
> - E-3.
>
> The accepted limitations in its residual register are limits of this exit.

## Exact payloads

**These are written for the recommended options.** A different choice changes them, and
a changed payload is shown again before use.

- `<date>` stands for the declaration's date.
- Under E-5 (C), each link to `phase5-e-audit_2026-09-30.md` becomes plain text: "the
  local Phase 5 E audit packet (SHA-256 `<hash>`)".

### P-1 — `saved_plans/codex-parity-plan_2026-08-23.md`

**Six replacements, each to be applied exactly.**

- A Python script copied the file to a scratch path at `553ca5f` on 2026-09-30. For
  each replacement, `str.count` found the old block exactly once, and all six then
  applied.
- Replacements 1 to 4 edit *Sprint status — reconciled 2026-09-10*. That section calls
  itself "This maintained status section", and the completion plan's E criteria name
  the maintained sprint status among the records to update.
- Sections that record a dated event are left as written. *Field-exercise
  reconciliation — 2026-09-05* is one.

1. Sprint-status Phase 5 bullet, line 390. Old:

   ```text
   - [ ] **Phase 5 — Align permissions, installation, and upgrades.** Merged deliveries
   ```

   New:

   ```text
   - [x] **Phase 5 — Align permissions, installation, and upgrades.** Merged deliveries
   ```

2. Same bullet, line 397. Old:

   ```text
     inspection. The exit is not yet established. `#236` retains the engine/doctrine
   ```

   New:

   ```text
     inspection. Topi declared the exit on <date> under the acceptance amendments the
     [Phase 5 E audit](phase5-e-audit_2026-09-30.md) names. `#236` retains the engine/doctrine
   ```

3. Delivery item 5, line 419. Old:

   ```text
     5. [ ] **Blocked:** complete the remaining `#243` field exercises. The original
   ```

   New:

   ```text
     5. [x] Complete the remaining `#243` field exercises, under the acceptance amendments
        of Topi's exit declaration of <date>; the [Phase 5 E audit](phase5-e-audit_2026-09-30.md)
        owns the outcome and those amendments. The rest of this item is its record up to
        2026-09-13 and is not updated. The item was blocked at first: the original
   ```

4. The last sentence of delivery item 6, line 538. Old:

   ```text
   Item 5 remains blocked, so this does not complete Phase 5.
   ```

   New:

   ```text
   Item 5 was still blocked then, so this did not complete Phase 5.
   ```

5. The Phase 5 checklist, lines 851–852. Old:

   ```text
   - [ ] Complete the remaining runtime-specific field coverage for `#243`, using the
     reconciliation below rather than repeating the issue's older exercise list.
   ```

   New:

   ```text
   - [x] Complete the remaining runtime-specific field coverage for `#243`, using the
     reconciliation below rather than repeating the issue's older exercise list. The
     [Phase 5 E audit](phase5-e-audit_2026-09-30.md) reconciles the field rows under the
     acceptance amendments Topi's exit declaration of <date> names; `#243` stays open for
     its Phase 6 residue.
   ```

6. The Phase 5 checklist's replay item, line 923. Old:

   ```text
     The remaining fixture work is blocked as recorded in delivery item 5.
   ```

   New:

   ```text
     The remaining fixture work was then blocked, as delivery item 5 records.
   ```

**After applying P-1**, grep the file for `remains blocked`, `is blocked`,
`remains pending` and `not yet established`. That catches what else the change made
false (AGENTS.md, *Prose that goes false*).

On the scratch copy with P-1 applied, at `553ca5f` on 2026-09-30, that grep hit only
line 495. That line is inside item 5, which replacement 3's new sentence dates. The word
`exit` is left out of the grep: it hits contract text such as the *Done when* throughout
the section.

### P-2 — comment on #243

```markdown
**Phase 5 field rows — exit declared <date>.**

Phase 5's exit audit reconciles the runtime-specific field rows this issue's remaining
exercise list became: `adopt` through the retained fixture's adoption and PR lifecycle;
`post-merge-systemize` through its engines and a live window, with its recovery,
boundary and fresh-context rows; `triage-friction-log` through its engines and live
sweeps.

The exit rests on these operator-approved amendments to the acceptance contract, which
the declaration names: the systemize friction and tracker no-write amendment; labelled
synthetic coverage for the systemize boundary, systemize recovery and triage recovery
rows; the named gaps of the fixture, client, engine, fresh-context and triage-engine
rows; additional client coverage; notification approval provenance (#198) and the
triage notification service; scheduling; real-service crash ambiguity (#794, #792);
engine installation in an adopter; and the evidence-custody limitation.

This issue stays open. Its Phase 6 residue is unchanged: adapter bodies as per-runtime
templates, the appended-instruction mutation for `adopt`, `upgrade` and `pr-watch`, and
the stale doctrine citation.
```

### P-3a — comment on #7, then close it as completed

```markdown
Delivered, with two differences from the plan above.

- Item 1: #769 (`cf83f20`) shipped `heartbeat_cli.py`.
- Item 2: #769 shipped `fetch_merged_prs.py` and `digest_merged_prs.py` behind
  systemize's own forge boundary (`scripts/lib/systemize/forge.py`), not one shared
  with #6, which is still open.
- Item 3: `lookback_days`, `pattern_threshold`, `batch_size`, `single_pass_max_prs` and
  the operator logins were already config keys from #595; review sources come from
  `review.bots` plus `systemize.operator_logins`; #769 added
  `systemize.heartbeat_job` and `systemize.heartbeat_pattern`.
- Item 4: #595 corrected the skill banner, and #781 (`902dbf6`) README and the guides.

`nightly_digest.py` was not shipped; the configured engine set is fetch, digest and
heartbeat. The engines are in `kit-manifest.json`, so an adopter's next upgrade installs
them. Closing as completed.
```

### P-3b — comment on #748, then close it as completed

```markdown
Delivered by #769, with one deliberate difference.

Forge thread resolution is now the addressed-state evidence
(`scripts/lib/systemize/normalize.py`, `thread_addressed`): resolved is `addressed`,
unresolved-and-outdated is `outdated`, any other unresolved thread is `unaddressed`, and
a review-body finding, which has no thread, is `unevidenced`. The forge query always
requests `isResolved` and `isOutdated`, and a failed forge read stops the run.

The difference: `outdated` and `unevidenced` are kept distinct in the digest but, being
inconclusive, count toward the unaddressed finding count
(`docs/agentic-dev-kit/workflows/post-merge-systemize.md`). Suggestion 2 would have
excluded outdated threads from that count. Closing as completed; a separate issue can
take up the count if it matters in practice.
```

### P-4 — occurrence comment on #861 (posted 2026-09-30 on Topi's approval)

```markdown
**Occurrence, 2026-09-29: manifest-bound fixtures are missing.**

Two Phase 5 evidence directories, `phase5-d-systemize-recovery-01/` and
`phase5-d-systemize-boundaries-01/`, no longer hold the `fixtures/` files their own
manifests bind (`SHA256SUMS`, `EVIDENCE-SHA256SUMS`, and in the first a stage-2 seal).
`shasum -a 256 -c` there on 2026-09-30 reports each listed fixture missing, and nothing
records their removal.

Both directories were last modified at 2026-09-29T15:07–15:08 +0300, the same minutes
as several 2026-09-13..2026-09-20 run directories, which points at this issue's
cleanup. But the table above describes a population dated 2026-09-13..2026-09-20, and
these two directories date from 2026-09-23 and 2026-09-24, so the attribution is an
inference from the times alone.

If the cleanup did remove them, its "not bound by any manifest" test did not read
these manifest forms. The retention rule this issue proposes should treat any checksum
manifest in a run directory as binding, whatever its name, before anything is dropped.
```

### P-5 — the exit record's handoff change

Written for the recommended path. Apply it in the exit record PR, through the wrap-up
workflow.

1. A session entry at the top of `docs/kit-handoff.md`'s session log:

   ```markdown
   ## Session — <date> (Phase 5 exit declared, in <runtime>)

   **Declared.** Topi declared Phase 5 complete under PHASE5-E-AUDIT-01
   (`saved_plans/phase5-e-audit_2026-09-30.md`): "<the declaration's exact words>".
   The declaration names its acceptance amendments; the packet's residual register
   owns each residual's carrier.

   **Recorded.** The parity plan's Phase 5 items are checked (payload P-1). Tracker:
   <each posted payload, with its returned URL>.

   Closed workstream Phase 5 exit: the exit is declared.
   ```

2. The *Phase 5 exit* workstream entry is removed, and only if Topi closes it. The
   last line of the entry above records the closing.

### P-6 — new issue: the carrier for engine installation (E-2e)

Title:

```text
Run the shipped systemize and triage engines in an adopter's field checkout
```

Body:

```markdown
Phase 5 delivered the configured `post-merge-systemize` engines (#769) and
`triage-friction-log` engines (#765). Their engine-backed runs happened in this
repository's own checkouts; #769's installed check also ran the systemize engines in
test mode in a disposable vendored install. No adopter's own checkout has installed
them through an upgrade and run them there.

What to establish at an adopter's next upgrade: the upgrade installs the engines from
`kit-manifest.json`; the adopter's merged config selects engine-backed mode for both
workflows; and one engine-backed run of each completes there, with its report.

Severity: M. Not a defect; a coverage gap carried out of Phase 5's exit.
```

No labels. Repository: `topij/agentic-dev-kit`.

## Preserved through this audit

- #742's **Functional Correctness / Major / Heavy lift** classification, and its
  completed lifecycle.
- The docstring warning, which stays informational.
- The exact local skip of
  `scripts/tests/test_init_sh.py::test_step_2_refuses_on_an_exception_outside_the_old_enumerated_set`,
  with its stated reason.
- Hosted acceptance limited to run `35221728160`, job `105203274603`, checkout
  `983538335d9c39309c4e437e95dabbe52d2e7f69`.
- PR04's separate #393 acceptance, and `expected_failure_established: false`.
- The #561 limits, the mutation and nested-process limits, and the special-file and
  ownership limits.
- The failed post-merge association comparison, and its reconciliation.
- The endpoint-only custody limit, and the nontransactional merge-race limit.
- #723's approved deferral; cs-toolkit #2222, #2223 and #2255; and kit #724's record
  batch (#722 was closed as done on 2026-09-24).
- #585's placement outside Phase 6.

This audit summarizes those records and narrows none of them.

## Not established by this packet

- **A re-verification of the B and C namespaces' binding JSONs.**
- **Any rerun.** Every result above is read from its record. The only new runs are:
  - the reads `collect.sh` makes;
  - the grep scan in E-5;
  - the scratch-copy test of P-1.
- **Whether #861's cleanup removed any other manifest-bound file, and whether it removed
  these at all.**
- **The full contents of the control checkout's `state/triage/`.** A listing there on
  2026-09-30 showed one recovery bundle, `recovery-bundle_live_77bf165a…json`
  (`kind: state-present-prepared`), and its gate quarantine. Both date from 2026-09-25.
  The bundle's id appears in D-TRIAGE-RESIDUAL Stage L's
  `runs/L0-recover-plan/stdout.json`, so it is Stage L's L0 recovery record, not a
  second bundle. It stays as evidence for E-1f. The first preparation check's "second
  recovery bundle" was a misreading.

## Preparation check

Two fresh subagents checked this packet read-only against the records on 2026-09-30.

**The first round checked the first draft.** This version addresses what it found:

- **Acceptances:**
  - an acceptance inventory that missed B's accepted limits and RECOVERY-01 §4;
  - a #7 comment that repeated an unverified history judgment.
- **Payloads:**
  - a P-1 that left line 923 false, and named no amendment;
  - a P-3b that was incomplete;
  - a missing handoff payload.
- **Ledger:**
  - an "Awaiting acceptance" class that claimed rows met their text;
  - missing residual owners, and a mis-cited D proposal line;
  - missing engine defects;
  - a missing line 53, and an undefined class for line 52;
  - unmapped packages, and a contract without the acceptance matrix.
- **Custody:** a check of root-level manifests only, and a P-4 that overstated the
  cause.
- **Grounding:** two wrong contract hashes, an issue-state claim that did not cover
  every named issue, and a misassigned #869.
- **Prose:** unenumerated counts and unstamped verdicts.

**The second round checked the revised draft.** This version addresses what it found:

- **Payloads:**
  - a false after-grep claim for P-1;
  - a P-6 body that ignored #769's installed check;
  - P-2 and the declaration wording, which under-listed the amendments.
- **Residuals and E-1:**
  - residuals missing from the register, and stretched owners (#198, #747, #794);
  - E-1a and E-1f, which lost gaps the ledger names;
  - a runtime-neutral rationale that is wrong for systemize.
- **Issue facts:** an incomplete item 3 for #7, and an imprecise #748 account.
- **Custody:**
  - three 2026-09-13 directories that were attributed to B;
  - a verified-list that omitted results;
  - a timestamp-line claim that was not true of every manifest;
  - a P-4 without its counter-indication.
- **Search:** acceptance-search patterns too narrow.
- **Contract:** a *Done when* left unreconciled.
- **Prose:** misquoted source text, and further unstamped readings.

A third check was not run. Whether this version introduced errors of its own is not
established.
