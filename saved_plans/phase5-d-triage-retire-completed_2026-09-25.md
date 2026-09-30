# Phase 5 D — PHASE5-D-TRIAGE-RETIRE-01 approval packet (completed-state retirement)

**Prepared for approval. Nothing below has been approved or executed.** This packet
fixes the defect [PHASE5-D-TRIAGE-RESIDUAL-01](phase5-d-triage-residual_2026-09-25.md)
found and Stage T observed (its `RESULTS.md`, T7): **a completed triage session
permanently ends its mode.** The live half of D-TRIAGE-RESIDUAL waits on this fix. The
occurrence is recorded on #425
(https://github.com/topij/agentic-dev-kit/issues/425#issuecomment-5829524297), and #425
stays open until the operator decides otherwise.

Topi owns the scope, the merge, and the acceptance decision.

## The defect, and what is not a defect

All citations are to `281730c0b3d258d0f4c80c2d03ae02a7d9ac43f0`.

- **Defect.** A valid `completed` state blocks every new session in its mode:
  - `new` refuses over any valid state (`engine.py:1702-1712`);
  - no argument, `resume` and `test` replay "preserve the completed receipt"
    (`engine.py:1717-1730`, pinned by `test_triage_engine.py:138-141`);
  - `recover` refuses valid state (`engine.py:1669-1670`);
  - nothing removes the file.

  The workflow's outcome table allows the completing run to remove it ("Write a
  durable completed receipt before optionally removing active state",
  `triage-friction-log.md:622`). But its input matrix has no `completed` row, so
  `completed` falls into "No argument, valid active state → Resume" and "`new`, active
  live state → Refuse". Stage T's T7 observed the block on the real inbox. #425's
  2026-09-17 adopter occurrence records the scheduled form of the same failure: a job
  that exits `0` and never drafts again.
- **By design, not a defect.** An invalid state that carries external evidence becomes a
  terminal `state-present-held` envelope, and the gate stays in place
  (`recovery.py:397-416`, `engine.py:1656-1659`). The bundle's path is derived from the
  gate's digest (`triage.recovery_bundle_pattern`), so the gate has to stay for the
  bundle to remain discoverable. The workflow says so: "keep the recovery bundle and
  active state operator-held" (`triage-friction-log.md:843-847`). The #425 comment left
  this open as a question. This packet answers it: the behaviour is intended.
- **Declared but not implemented.** The workflow's reconstruction route, in which a
  reconstructed state replaces an invalid one "on exact operator approval of its
  recovery-bundle digest" (`triage-friction-log.md:840-844`), has no code in
  `scripts/lib/triage/recovery.py`. This packet does not implement it. It matters only
  if Stage 0 finds the 2026-09-06 state invalid.

## Stage 0 — classify the 2026-09-06 state

The fix below covers a **valid** completed state. Whether the kit's own 2026-09-06 live
state is valid is still unknown. RESIDUAL-01 did not parse it, because the proposal
forbids reading production state outside its gate. The answer decides whether this
package clears the live half or only the general case.

### Decision K

| Option | What it is | Trade-off |
|---|---|---|
| **K1 (recommended)** | A bounded exception. Copy the state file's bytes into a scratch state root, confirm the copy's SHA-256 equals `5f4872c6…60a6`, and run the engine's own `canonical_state` and `_validate_frozen_artifact` on the copy, with the frozen snapshot it names also copied. Hash the production file before and after. No gate is taken on production state, and nothing in `state/triage/` is written | Reading a copy cannot race or mutate the production file. What it gives up is the proposal's literal "no read outside the gate" rule. The payoff is knowing before implementation whether the fix clears the kit's own blocker |
| K2 | No classification. Implement the fix, and let Stage L's first live invocation classify under the gate | Keeps the rule literally. If the state is invalid, Stage L's first live call runs into the terminal held path RESIDUAL-01 point 7 describes |

**K1 outcomes:**

- **Valid, phase `completed`:** the fix below clears the blocker. Proceed.
- **Valid, any other phase:** stop and present. The 2026-09-06 run would then be an
  unfinished engine-schema session, and resuming it is a different decision.
- **Invalid:** stop and present. The fix still ships for the general case, but the kit's
  live half then needs either the reconstruction route or a decision about the evidence
  in the 2026-09-06 state, as a separate package. Do not run `recover` on it.

## The fix

### Behaviour

**Retire a completed state under the gate, and then claim.** For an entry that would
start a session, if the gate is acquired and the captured state is valid with phase
`completed`:

1. Validate it completely: the existing `canonical_state` plus
   `_validate_frozen_artifact`. The completed-receipt digest is already recomputed by
   `validate_state`.
2. Rename the unchanged state bytes to a retained path (Decision R), using the existing
   `quarantine_inode` primitive. That primitive checks identity before the rename and
   reads back after it.
3. Exclusively create the new `reserved` state and continue as a new draft.

**Which entries retire (Decision X):**

- Recommended: **no argument**, `new`, and `test` in test mode.
- `resume` over completed keeps replaying the receipt, and `recover` over completed keeps
  refusing, because neither means "start a new session".

**Crash semantics.** Each step is atomic, and the ordering fails safe:

- a crash before the rename leaves the completed state, which the next run retires;
- a crash after the rename, before the claim, leaves the state absent, and the next run
  starts normally;
- the retained file is never deleted by the engine.

A retained file already present at the target, with other bytes, stops the run
operator-held, which is `quarantine_inode`'s existing refusal.

**Output.** The CLI result and the new report name the retired path and its SHA-256.
The state schema does not change: no new key, and no pointer to the predecessor.

### Decisions

| Id | Options | Recommendation and why |
|---|---|---|
| **W**: when to retire | W1: when the next run claims (above). W2: the completing run retires its own state at completion | **W1.** It also retires states that already exist: the 2026-09-06 file if it is valid, and adopters' states. It survives a completing run that crashes before retiring. And `resume` can still replay the receipt until someone starts a new session |
| **R**: retained path | R1: derived from the state path, as `<state_path>.completed-<completed_receipt_digest[:16]>`, following the existing `.quarantine-<digest>` convention (`recovery.py:418`). R2: a new config key, `triage.completed_state_pattern` | **R1.** It adds no config key, so `init.sh`, `test_init_sh.py`, `fixtures/init-config.json` and `test_portability.py` do not change, and adopters get no migration. The suffix is derived the way the quarantine suffix already is |
| **X**: entries | as above | as above |
| **U**: unattended | U1: scheduled and unattended runs retire too. U2: interactive only | **U1.** The scheduled case is #425's adopter failure. Retirement touches only a completed state, which holds no pending approval, attempt or merge |
| **I**: who implements | I1: this Claude Code session, inline. I2: a Codex lane at GPT-5.6 Sol / medium, as TRIAGE-ENGINE-01 did | **I1.** The change is one route in `run()` with focused tests. Steering it live matters more than the runtime |

### Workflow text (the shared doc, never an adapter)

These go in `docs/agentic-dev-kit/workflows/triage-friction-log.md`:

- **Semantic input matrix.** Add rows ahead of "No argument, valid active state" and
  "`new`, active live state":
  - no argument or `new`, valid `completed` live state: under the gate, retire the
    unchanged state to its derived retained path, then start a new live draft;
  - `resume`, valid `completed` state: report the completed receipt, with no mutation.
- **Test matrix.** The `ungated-valid` row splits into a completed case, which retires
  and then starts a new test draft, and a non-completed case, which resumes.
- **Outcome table.** "optionally removing active state" becomes a statement that the
  next session-starting run retires a completed state under the gate, and that the
  retained file is never deleted by the workflow.

### Allowlist

- `scripts/lib/triage/engine.py`, and `scripts/lib/triage/storage.py` only if a helper
  is needed;
- `scripts/tests/test_triage_engine.py`, plus a new `scripts/tests/test_triage_retire.py`
  if that is cleaner;
- `docs/agentic-dev-kit/workflows/triage-friction-log.md`;
- `CHANGELOG.md`.

Nothing else. `pr_watch.py`, `dev_session.sh`, `launch_lane.py`, the lane settings
profile, runtime adapters and config are out of scope. Needing any other path is an
amendment.

### Tests

Focused tests on synthetic roots, following the existing `run(…, start=root)` pattern:

- For each of no argument, `new`, and `test` over a completed state: retires to the
  derived path with the bytes unchanged and the hash verified, creates a new `reserved`
  state, and returns a fresh session identity.
- `resume` over completed: replays, with bytes unchanged. This keeps
  `test_triage_engine.py:138-141` true.
- `recover` over completed: refuses, as before.
- Each non-completed valid phase: `new` still refuses and no argument still resumes.
- Retained path already present with other bytes: operator-held, and both files
  unchanged.
- State changed between capture and rename: operator-held, via the existing
  identity check.
- Crash between the rename and the claim, simulated by making the claim fail: the next
  run starts normally, and the retained file is intact.
- An unattended no-argument run over completed: retires and then drafts, or holds for
  the notification provider exactly as a fresh unattended draft does now.
- **Control/mutant witnesses**, per the review doctrine:
  - reverting the retirement route makes the retirement tests fail;
  - retiring on a non-completed phase makes the phase test fail.

### Verification and delivery

- **`make test`** runs in a detached worktree of the candidate under this session's
  scratchpad, not in the main checkout. The main checkout's
  `state/review-evidence/` holds mode-000 files that crash the suite's state snapshot
  (#461). `find state -not -perm -u=r` in `/Users/topi/Coding/agentic-dev-kit` on
  2026-09-25 listed such files. The result is stamped with command, sha, directory and
  date.
- **Branch** `feat/triage-retire-completed-state`. Open the PR ready, run
  `pr-watch --assert-ready`, and watch it to green and review-clean. CodeRabbit's
  automatic reviews are off (`.coderabbit.yaml:76-79`), so the fallback panel carries
  the review.
- **CHANGELOG.md.** An entry headed with this PR's number. It is observable in two ways:
  gate semantics change (no argument and `new` over completed now start a session), and
  a new retained artifact appears. What the adopter does: nothing is required. An
  adopter who retires completed state with its own script (#425's 2026-09-17 occurrence)
  can remove that script after upgrading.
- **Merge** is Topi's decision, and is not part of this approval.

## After merge

Stage L of D-TRIAGE-RESIDUAL is re-prepared against the merged engine:

- If K1 found the 2026-09-06 state valid and completed, Stage L's first live call
  retires it under the gate and drafts.
- The single-verb constraint still holds (RESIDUAL-01 point 1). Stage T's analysis
  applies: file TRI-05, and archive the already-ticketed set. So Stage L is **two
  sequential live sessions**, one filing and one archiving, each with its own sweep PR.
  The fix is what makes the second session possible.
- TRI-05's undated `gh search` sentence is stamped or removed before filing.

## Not in scope

- The reconstruction route for invalid state with evidence.
- A notification provider for the CLI (RESIDUAL-01 point 3, #198).
- Any live triage session, tracker write or friction-log edit.
- Changing the held-gate design.

**Approval wording (K1 + W1 + R1 + U1 + I1):** "I approve PHASE5-D-TRIAGE-RETIRE-01 with
K1, W1, R1, U1 and I1: a read-only classification of a hash-verified copy of the
2026-09-06 live state, then, if it is valid and completed (or regardless, for the
general fix), an inline implementation in which no-argument, new and test runs retire a
valid completed state under the gate to <state_path>.completed-<digest16> before
claiming, with workflow text, focused tests, make test in a detached worktree, a
CHANGELOG entry and a ready reviewed PR on feat/triage-retire-completed-state. No merge,
no live triage session."
