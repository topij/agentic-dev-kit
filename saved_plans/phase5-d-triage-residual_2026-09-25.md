# Phase 5 D — PHASE5-D-TRIAGE-RESIDUAL-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** This packet
scopes the D-TRIAGE-RESIDUAL row of the
[Phase 5 D proposal](phase5-d-proposal_2026-09-21.md). That row asks for an engine-backed
**test** session and a separately approved **live** session of the triage engines that
#765 delivered as `b808061`. Topi owns scope changes, every exact payload, the merge, and
the acceptance decision.

**Preparation found that the live session is unreachable with the engine as it stands.**
The 2026-09-06 LLM-only state is still present, and every engine route past it either
refuses or makes the live mode worse (*What the engine code establishes*, points 2 and
7). This packet therefore proposes **Stage T now**. Stage L is **re-prepared after an
engine fix**, and is sketched below only so that its corrected mechanics are not lost.

The proposal row asks for:

- a new engine-backed test session, and a separately approved live session;
- no read or replacement of existing production triage state outside its gate;
- a freeze of the current source blocks that preserves the historical parks by bytes and
  digest;
- acceptance evidence covering:
  - draft/finalize engine evidence;
  - notification-thread approval identity and digest;
  - attempt and read-back accounting;
  - the exact eligible sweep;
  - the ready PR's review identity;
- a merge under its own authority, with completion only after a matching merge
  read-back;
- no replay of the credited LLM-only graduation.

**This package cannot close the row.** Stage T gives engine evidence for draft, parks
and test-render only. The proposal (`phase5-d-proposal_2026-09-21.md`, the paragraph
after the package table) says interactive degradation does not discharge the
notification service row. So the notification-thread item stays open for the E audit
under every option here.

## Grounding reads

All reads were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-25.

- **Protected head.** `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha`
  printed `281730c0b3d258d0f4c80c2d03ae02a7d9ac43f0`. `gh run list --branch main
  --limit 1` read `success` for that sha.
- **Triage engine, workflow and `pr_watch.py` unchanged since #765.** `git log --oneline
  b808061..281730c -- scripts/triage_friction_log.py scripts/finalize_triage.py
  scripts/lib/triage docs/agentic-dev-kit/workflows/triage-friction-log.md
  scripts/pr_watch.py` printed nothing. `config/dev-model.yaml` did change after
  `b808061` (in `cf83f20`, #769, which added systemize keys), so this read says nothing
  about the config.
- **Config** (`kitconfig.load_config()`, merged, `config/dev-model.yaml` at `281730c`):
  - `tracker.backend: github-issues`, `project_name: topij/agentic-dev-kit`;
  - `triage.analysis_tier: default`, which `models.runtime_mappings.claude` maps to
    `sonnet`;
  - `triage.pr_draft: false`;
  - `vcs.triage_branch_pattern: chore/triage-{date}`.
- **The inbox.** `shasum -a 256 docs/kit-friction-log.md` printed
  `8486505aebd1c4585ad2d6d4f5fcda1e1cc549628236eeea47efb9c3f27e5c8e`. `git grep -n
  "Backlog migrated" 281730c -- docs/kit-friction-log.md` names `## 2026-09-06 —
  Backlog migrated to GitHub Issues (#693)` as the first marker heading. The candidate
  set is **not** counted here. The engine's freeze prints the candidate index, and that
  output is the only count this package uses.
- **Existing live triage state.** `ls -la state/triage/` lists
  `triage-pipeline-state_live.json` and no `*.lock` file. `shasum -a 256` of the state
  file printed `5f4872c69894bed498ba6b3c6bc17f42667173324cd16dcee06a4d08319060a6`. **Its
  contents were not read or parsed.** The committed marker
  (`docs/kit-friction-log.md`, the 2026-09-06 section) records that its session filed
  #693 and finalized a sweep.
- **Client.** `claude --version` printed `2.1.282 (Claude Code)`.

### What the engine code establishes

Read at `281730c`, and confirmed independently (see *Preparation check*).

1. **One command per approval.** `approval.py:11-58` accepts exactly one of `approve
   <ids>`, `approve all`, `archive <ids>`, `park <ids>`, `modify <id>: …` or `cancel`,
   and rejects mixed verbs and commas. Every candidate the command does not mention
   defaults to `park`. So one session can file **or** archive, but not both.
2. **A completed session ends its mode.**
   - `engine.py:1702-1712` refuses `new` over any valid state.
   - `engine.py:1717-1730` answers every other entry over completed state with "preserve
     the completed receipt", and `test_triage_engine.py:138-141` pins that replay.
   - `recover` refuses valid state (`engine.py:1669-1670`).
   - No code in `scripts/lib/triage` deletes a completed state file. The workflow allows
     it ("Write a durable completed receipt before optionally removing active state",
     `triage-friction-log.md:622`), but the engine never takes that option.
   - This is the other side of open #425: the engine made completed state inert, and
     inert completed state now permanently blocks `new`.
3. **The CLI has no notification provider.** `NotificationProvider` is only a
   `Protocol` (`providers.py:32`), and `triage_friction_log.py:102` passes none. An
   interactive draft records `notification-thread: degraded` (`engine.py:815`, `:843`).
   *Engine CLI* says so itself: "The CLI has no notification-service flag".
4. **The live tracker search is a complete listing, not the search index.**
   `providers.py:76-107` pages `issues?state=all&per_page=100` until a short page, skips
   pull requests, and matches the marker as an exact substring. #794's question about
   index tokenization and latency does not arise here.
5. **Test mode makes no tracker call.** It records `would-create` and completes with
   route `test-render` when the command is `approve` or `archive`
   (`engine.py:936-944`). A `park` or `cancel` command ends the session as
   `decision-only` (`engine.py:927-934`).
6. **Finalization** runs only in a new, absolute, out-of-repo worktree
   (`engine.py:1464-1472`, `providers.py:390`), stages exactly the friction log and its
   archive, and runs `pr-watch --assert-ready` (`providers.py:440`). It has no merge
   action. Completion needs a merge read-back whose final head equals `reviewed_head`,
   which only a terminal `pr-watch` receipt supplies (`triage-friction-log.md:1055-1081`).
   #647 is the hazard: a merge before that receipt leaves the run uncompletable.
7. **Recovering the 2026-09-06 state would make the live mode worse.**
   - Invalid state is abandonable only if it records no attempts, verified identifiers,
     repository evidence or pull-request evidence (`recovery.py:397-416`). The 2026-09-06
     session filed #693, so an invalid file would almost certainly be classified
     `state-present-held` / `external-attempt-absence-unproven`.
   - On that path `recover` publishes the capture and replaces it with a terminal held
     envelope (`recovery.py:296-297`, `:361-365`). It then sets `lease.held = False`
     without releasing the lease (`engine.py:1656-1659`). **The live gate stays on
     disk.** Every later live entry fails to acquire the gate, and live mode goes from
     "state, no gate" to "gate, state and held envelope", with no engine route out.
   - Invalid state also blocks `new`, because `canonical_state` raises
     (`engine.py:1690`).
   - So whether the file is valid (point 2) or invalid (this point), no live session can
     start. **Running `recover` to find out makes irreversible writes under the gate,
     before any approval.**

## Decisions owed

### Decision C — the live half

| Option | What it is | Trade-off |
|---|---|---|
| **C1 (recommended)** | Run Stage T only now. File the engine gap (a new issue, or an addition to #425; Topi picks). A separate engine package defines how a completed or LLM-only prior state is retired **under the gate**, without manual deletion. Stage L is re-prepared against the fixed engine | Nothing live runs yet, and the production state is not touched. The fix can also allow an archive session after a filing session (point 1), which the proposal's "exact eligible sweep" benefits from |
| C2 | Run `recover` on the 2026-09-06 state and see what happens | By point 7, the likely outcome is a held envelope and a stuck live gate, with no route out. Rejected on the record |
| C3 | Move the 2026-09-06 state aside by hand | Contradicts the proposal's gate rule and the workflow's "never make `new` available by manual deletion" (`triage-friction-log.md:847`). Rejected on the record |

### Decision A — who writes the proposal analysis

The engine freezes the inbox and returns the candidate index. The analysis request (for
each candidate: `candidate_id`, `source_block_digest`, `title`, `body_without_marker`,
`project` and `labels`) is written by the runtime. The analysis must cover **every**
candidate, the historical parks included (`engine.py:510-511`).

| Option | What it is | Trade-off |
|---|---|---|
| **A1 (recommended)** | A `sonnet` subagent drafts the request from the frozen snapshot only. `sonnet` is what `default` maps to. The cockpit then checks every proposal against its source block and against existing tracker issues | Follows the configured tier as guidance. The engine reports `runtime-compute-selection: degraded` under either option (`engine.py:1601`) |
| A2 | The cockpit drafts it | One step fewer, and the tier guidance is not followed |

Proposals are keyed only by `candidate_id` and `source_block_digest`
(`engine.py:510-517`). So the Stage T request can be reused by the later Stage L if the
index and digests have not changed.

### Decision B — where the test session runs

| Option | What it is | Trade-off |
|---|---|---|
| **B1 (recommended)** | A disposable clone, with cwd inside it and the state-root variables unset (below) | Test state, frozen snapshot, reports and the completed test receipt all stay in the clone. The control checkout's `state/triage/` is untouched, so its test mode is not blocked by point 2 |
| B2 | The control checkout | Leaves a completed test state there permanently (point 2) |

### Decision D — the notification-thread item

| Option | What it is | Trade-off |
|---|---|---|
| **N1 (recommended)** | No notification in this package. The item goes to the E audit as open, citing point 3 and #198 | Honest: the CLI cannot send, so there is no engine-backed notification route to exercise |
| N2 | For Stage L later: the cockpit sends the exact-payload summary as a Slack DM to `U082VD4SR2N`, reads the thread back, and the approval context carries `source: "notification-thread"` | Exercises send and thread-read, but not the engine's `notification-delivery` operation. #198 defect 1 applies: the DM and the reply share author `U082VD4SR2N`, so the read-back tells them apart by order and text, not by identity |

## Stage T design (A1 + B1 + C1 + N1)

### Namespaces

- `$W=/private/tmp/adk-phase5-d-triage-residual-<h>` (`<h>` is 8 random hex
  characters). **Refuse if it exists.** It holds the test clone `$W/test-clone`.
- `$E=state/review-evidence/phase5-d-triage-residual-01/` in the control checkout. It
  holds `APPROVAL.md`, the analysis and approval requests, the approval-context files,
  each invocation's argv, cwd, stdout, stderr and exit code, the copied report,
  `RESULTS.md` and `EVIDENCE-SHA256SUMS`. A note in `$E` records that the cockpit wrote
  and attests every approval-context file.

Every write uses absolute paths, `pwd` is asserted before each write sequence, and
results are verified at the destination by hash.

### How the engine resolves its paths

Config, repository root and reports come from the engine's own file location. **State,
the gate, the frozen snapshot and recovery paths come from `state_paths`**. That
resolves from `$DEVKIT_STATE_ROOT`, then a `.devkit_state_root` marker walked up from the
**cwd**, then `$DEVKIT_ROOT`, then the cwd's repository (`storage.py:400-404`,
`state_paths/resolver.py:115-139`, `:196-222`). The run identity reads
`refs/remotes/origin/main` and `remote get-url origin` (`model.py:234-252`).

So every Stage T invocation is a single command of this form:

```
cd "$W/test-clone" && env -u DEVKIT_STATE_ROOT -u DEVKIT_ROOT \
  uv run --with pyyaml python3 "$W/test-clone/scripts/triage_friction_log.py" test \
  --context interactive --request <file> [--approval-context <file>]
```

`uv run --with pyyaml` is used because the engine imports `yaml`. Whether the system
Python has it was not probed for this packet.

### Steps

1. `git clone https://github.com/topij/agentic-dev-kit "$W/test-clone"` and check out
   `281730c` on a local branch, with `origin/main` at `281730c`. Confirm the inbox hash
   equals the grounding value. Record `ls -la state/triage/` in the control checkout.
2. **Freeze**: `test` with request `{}`. Record the frozen path, its SHA-256 and the
   printed candidate index. Check that
   `$W/test-clone/state/triage/triage-pipeline-state_test.json` exists, and that the
   control checkout's `state/triage/` listing is unchanged.
3. **Historical parks.** Find the three ledger blocks in the frozen snapshot (the
   2026-08-27 `claude -p --output-format json` entry, the 2026-08-27 `panel_prompt.py`
   entry, and the 2026-08-22 panel-rounds entry). Compare each `source_block_digest`
   with the route ledger's `8c427cec…98f7`, `d1dba827…782c` and `f76cd721…4b0`.
   - **Equal:** the park is preserved by digest.
   - **Changed:** the ledger's digests used the LLM-only run's block boundaries, and the
     engine uses its own (`inbox.py:114-119`). So also compare the engine block's bytes
     with the same block in
     `state/triage/frozen-inbox_live_2026-09-06_triage-548121b9fa18444808d6b2482aac91d3.json`,
     to tell a boundary difference from a content change. That file is a sealed past
     artifact, not active state. The panel-rounds entry was annotated after 2026-09-06,
     so a content change there is expected. Record it and present that block as a fresh
     source identity, with its old digest beside it.
4. **Analyse** per A1, then run `test` with the analysis request
   (`{"proposals":[…]}`). Expected: `awaiting-approval` and a rendered report. Copy the
   report to `$E`.
5. **Test approval.** Present the payloads in this session. Topi gives a single command
   labelled as a test. It must be `approve <ids>` or `archive <ids>`, never `approve
   all`, which would also file the historical parks.
   - The request is `{"approval":{"command":"<verbatim>","proposal_set_digest":"<d>"}}`.
   - The approval-context file has exactly the keys `source`, `operator_identity` and
     `source_read_back` (`triage_friction_log.py:89`). Its values are `"current-session"`,
     `"topij"`, and `{"approver_identity":"topij","text":"<verbatim>",
     "proposal_set_digest":"<d>","payload_digests":[…]}` (`engine.py:866-879`,
     `approval.py:72-78`).
6. `test` with the approval request and context. Expected: outcome `degraded-success`,
   with state `completion.route: test-render`, a `would-create` for each approved
   filing, and a proposed diff for the friction log and its archive. Hash both documents
   in the clone before and after; they must be unchanged.
7. **Observe the gap**: run `test` with `{}` again. Expected: detail
   `completed/test-render`, and the state bytes unchanged. That is point 2 on the real
   inbox.
8. Write `RESULTS.md`, and seal `EVIDENCE-SHA256SUMS`. Removing `$W` is a separate
   cleanup for Topi to authorize.

Stage T makes no tracker, notification, forge or source write, and no write to the
control checkout's `state/triage/`.

### Stops

Keep the checkpoint and present on any of these:

- `$W` exists;
- the inbox hash or protected head differs from the grounding values;
- the control checkout's `state/triage/` listing changes;
- an engine hard stop, or an outcome other than the expected one;
- a changed historical-park digest not yet presented.

## Stage L — sketch for re-preparation after the engine fix

Stage L is not proposed for approval here. These corrected mechanics carry forward:

- **Freeze**, then `resume` with the analysis request, which gives `awaiting-approval`.
  A freeze alone leaves the state `reserved` (`engine.py:771-773`).
- **Present** the exact payloads and `proposal_set_digest`. This is the exact-payload
  approval point.
- **Approve**, then `resume` with the approval request, the attested context (shape as
  in T5) and `--enable-github-tracker`. The engine searches, persists `attempting`,
  creates and reads back (`engine.py:975-1030`). An `ambiguous` or `failed` result stops
  the stage.
- **Finalize.** Every `finalize_triage.py` call passes `--request` containing
  `"finalize": true` and `--enable-github-forge` (`engine.py:1431-1433`). The first call
  also names an absolute `worktree` that must not exist yet (`providers.py:390-391`).
- **Review.** `pr-watch` and, since `.coderabbit.yaml:76-79` turns automatic reviews
  off, the fallback panel. **No merge before `reviewed_head` is persisted** (#647).
- **Merge** by Topi, separately, then a merge read-back resume.
- **Recovery approval shape**, if the fix still routes through `recover`: request
  `{"recovery_approval":{"decision":"approve","source":"current-session",
  "approver_identity":"topij","core_digest":"<action_core_digest>"}}`, with a read-back
  that carries `decision`, `core_digest` and `approver_identity`
  (`engine.py:200-217`).

## Findings from preparation

These are for Topi to decide whether to file. Nothing has been filed.

- **Completed or held triage state permanently blocks its mode** (points 2 and 7).
  - A completed state blocks `new`, and the engine never takes the workflow's option to
    remove it.
  - `recover` refuses valid state.
  - For invalid state with any external evidence, `recover` leaves a held envelope and
    the gate still held. There is then no engine route out.
  - Consequence: the kit's own next live triage cannot run through the engine. This
    relates to open #425.
- **The CLI cannot drive the scheduled notification route** (point 3). This is declared
  in *Engine CLI*, so it may be a limitation rather than a defect. It does leave the
  proposal's notification item with nothing to exercise. Relates to #198.

**Approval wording (C1 + A1 + B1 + N1):** "I approve PHASE5-D-TRIAGE-RESIDUAL-01 Stage T
as designed with C1, A1, B1 and N1: an engine-backed triage test session in a disposable
clone of 281730c, with its state root inside the clone, sonnet-drafted and cockpit-checked
proposals, and my labelled single-verb test approval (not approve all). No tracker,
notification, forge or source write, and no write to the control checkout's triage state.
The live half waits for an engine fix."

## Not established by this package

- Any live session: tracker attempt and read-back, the sweep, the ready-PR review, or the
  merge read-back.
- Notification-thread approval (point 3, #198).
- D-TRIAGE-RECOVERY's cutpoints.

## Preparation check

A fresh subagent with no part in the drafting read the first draft against `281730c`,
read-only, on 2026-09-25, and did not read the live state's contents. It confirmed:

- the grounding hashes, the config values and the ledger digests;
- points 1 to 6;
- the reuse of the analysis request;
- that `new` works after a restart receipt.

Its corrections are folded in above:

- Stage T's state would have resolved into the control checkout. The fix is cwd in the
  clone, the state-root variables unset, and a clone of the GitHub URL.
- The first draft's C1 (`recover` to classify) would have left a held envelope and a
  stuck live gate. That is point 7, and C was reshaped around it.
- Invalid state also blocks `new`.
- The missing analysis step, the exact approval-context and recovery shapes, and the
  finalize flags on every continuation.
- The `$W` stop contradicted the worktree reuse.
- `runtime-compute-selection` is `degraded` under either option of Decision A.
- The T6 outcome, and which verbs produce `test-render`.
- Citations, and the relation to #425.
- The digest-boundary caveat, and forbidding `approve all`.
- The row cannot close under N1.
- Unstamped readings.
