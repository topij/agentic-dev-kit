# Phase 5 D — PHASE5-D-SYSTEMIZE-RECOVERY-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** This packet
turns the D-SYSTEMIZE-RECOVERY row of the [D proposal](phase5-d-proposal_2026-09-21.md)
into an executable scope. It follows the form of
[PHASE5-D-SYSTEMIZE-BOUNDARIES-01](phase5-d-systemize-boundaries_2026-09-23.md). It covers
the Stage A row "Systemize process crash/restart"
([route ledger](phase5-stage-a-routes_2026-09-18.md)).

The D row names four cutpoints:

- durable raw;
- durable digest;
- pre-approval proposal;
- post-dispatch/pre-receipt.

The first two are engine cutpoints. The last two sit inside the agent, because in
systemize the agent makes every route write, not an engine. So the packet has **two
stages with separate approvals**:

- **Stage 1** covers the engine cutpoints. It is fully specified and can be approved as
  written.
- **Stage 2** covers the agent cutpoints. It first needs the open design decision in
  *Stage 2 — decisions owed*.

Everything this packet produces is **synthetic evidence, labelled as synthetic**. Topi
owns scope changes and the acceptance decision.

## Grounding reads

All reads were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-23.

- **Protected head.** `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha`
  printed `66a8a101bfd8254c82b020508dabc4e45e1e3937`. Its push run, `35914495178`, read
  `completed success` in `gh run list --branch main --event push --limit 1`.
- **The engines match what BOUNDARIES exercised.**
  `git diff --stat a6b281a5f6f0a4eafeb789f36bb405d5c62d5aca 66a8a101bfd8254c82b020508dabc4e45e1e3937`
  lists only `docs/kit-handoff.md` and `docs/kit-handoff-history.md`.
- **Config.** `systemize.config.load_settings()` printed fingerprint
  `sha256:f208ba0d506e02a448082773eafb127316992304ae41bd43b08238bf5545890d` and mode
  `engine-backed`. `shasum -a 256 config/dev-model.local.yaml` printed `ae10ac8d…a74d8`.
  The declared values this packet relies on are:
  - the `systemize` patterns `cache_pattern`, `digest_cache_pattern`, `heartbeat_pattern`
    and `report_pattern`;
  - `tracker.backend: github-issues`, with `project_name: topij/agentic-dev-kit`;
  - `notify.backend: slack`;
  - `systemize.analysis_tier: expensive`, which Claude maps to `fable`.

**Engine behaviour this packet depends on**, read from the code at that sha:

- **Fetch** reads the repository and the protected head, then takes its per-target
  lock. The merged-PR population read happens under that lock. Fetch then publishes by
  temp write, `fsync` and `os.replace`, and only then releases the lock
  (`scripts/lib/systemize/fetch.py:106-132`, `artifacts.py:178-232`).
  `test_a_held_artifact_lock_refuses_a_concurrent_fetch` pins this split. A fetch
  refused by a held lock has therefore already made the `repo view` and branch-head
  calls, and has made no merged-PR read.
  - The lock file holds the writer's PID.
  - A held lock refuses the next writer and names the remedy: "confirm no systemize
    process is running, then remove the lock".
  - A `SIGKILL` skips both `finally` cleanups, so it leaves the lock and any temp file
    behind.
- **Digest** never takes the raw bundle's lock. It reads the raw through the resolver.
  - It takes `forge_repo` and `protected_branch_head` from the bundle, by design: the
    `load_raw` docstring says they "cannot be re-derived without a second forge read".
  - `--verify` writes nothing and takes no lock (`digest.py:17-76`).
  - The digest has no time-dependent field, so rebuilding it from the same raw is
    expected to give identical bytes. The raw bundle carries `fetched_at`
    (`fetch.py:120`).
- **Heartbeat `start`** replaces any same-identity state and increments `restarts`. It
  does not check `status` (`heartbeat.py:72-90`).
  - `test_a_same_identity_restart_counts_and_resets` covers a restart of a *running*
    heartbeat.
  - Nothing tests `start` after `complete`. The workflow's *Engine interface* lists "a
    write after completion" as a hard stop.
  - **A unit-level probe shows `start` reopening a completed run.** The probe used the
    kit's own test helpers (`make_repo`, `fake_env`, `run_engine`) in a temp repo, with
    the control checkout at `66a8a10`, on 2026-09-23. It ran `heartbeat_cli.py start`,
    then `complete --reason complete`, then `start`. All three exited `0`, and the final
    state read `status: running`, `restarts: 1`, `exit_reason: null`. The probe and its
    output are in `…-prep-20260923/heartbeat-start-after-complete/`.
  - Case HB below repeats the probe through the entry point after a kill.
- **Repeating `complete` with the same reason** is idempotent and writes nothing
  (`heartbeat.py:133-136`, `test_an_identical_completion_is_idempotent`).

**What the workflow says about recovery** (`docs/agentic-dev-kit/workflows/post-merge-systemize.md`):

- "Never repeat an external write merely because the previous process ended before its
  final summary; verify the pull request, notification, and tracker destination first."
- The report is written "before any external route" and updated "after each attempt".
- **It declares no idempotency key for a tracker item or a notification.** Only the rule
  route has deterministic identities: the branch pattern and the provenance marker.
  - A resuming agent therefore has no declared key for searching the tracker or the
    notification channel.
  - Nothing requires an "attempted" record *before* dispatch. The triage workflow
    requires one; this workflow does not.
  - Stage 2 tests whether the gap matters. It is a prediction, not a finding.

**Headless-agent probes.** These ground Stage 2's options. They used `claude` 2.1.281
in the session scratchpad, with the kit at `66a8a10`, on 2026-09-23. Outputs are
retained in `state/review-evidence/phase5-d-systemize-recovery-prep-20260923/`.

| Probe | Command (abridged) | Observed |
|---|---|---|
| Control | `claude -p --tools "" --output-format stream-json --verbose "Reply with the single word OK."` | init event listed 253 tools and 12 MCP servers, including `claude.ai Slack` (`connected`) — `control.jsonl` |
| Isolated | the same, plus `--strict-mcp-config --mcp-config empty-mcp.json` | init event: `tools []`, `mcp_servers []` — `strict.jsonl` |
| Model | plus `--model fable` | init event `model: claude-fable-5-1` — `hook.jsonl` |
| Stop hook | plus `--settings hook-settings.json` (a `Stop` command hook) | the hook ran and wrote `stop-hook-fired.json` — `hook.jsonl`, `stop-hook-fired.json` |
| Forge credentials | `GH_CONFIG_DIR=<empty dir> gh auth status`, then `gh api repos/topij/agentic-dev-kit` (gh 2.97.0, no token variables set) | exit `1` "You are not logged into any GitHub hosts"; exit `4` — `gh-credentials-with-exit.txt` |
| What else loaded | the `system` events and init fields of the isolated run | the user-level `SessionStart` hook still ran, and the synced plugin `cowork-plugin-management` was loaded — `strict.jsonl` |

So **a headless agent can be cut off from every account connector mechanically**, while
a run with no isolation loads Slack. Connector isolation alone does not keep out user
settings or plugins; Stage 2 therefore adds `--setting-sources ""` and a probe gate for
those.

This session's Agent tool offers no equivalent control:
- `general-purpose` subagents are declared with all tools.
- A restricted agent would need a new definition under `.claude/agents/`, which this
  packet does not propose.
- `TaskStop` can stop a background agent, but not at a deterministic point.

## Stage 1 — engine cutpoints (approvable as written)

**Purpose:** kill the real engine processes, or the process driving them, at the raw
and digest cutpoints and just before them. Then restart a fresh process from the durable
files alone and compare each outcome with a prediction written in advance. Nothing is
written to the kit, config, forge, tracker, friction log or notifications.

### Decisions bound by Stage 1

1. **Workspace.** Bind these roots:
   - `D=/private/tmp/adk-phase5-d-systemize-recovery-01`
   - `K="$D/kit"`, a fresh `git clone https://github.com/topij/agentic-dev-kit`,
     detached at `66a8a101bfd8254c82b020508dabc4e45e1e3937`
   - `F="$D/forge"`, holding the fake `gh`, the wrappers, fixtures and call logs
   - `R="$D/r"`: each case's `DEVKIT_STATE_ROOT` is `$R/<case>/state`
   - `E=/Users/topi/Coding/agentic-dev-kit/state/review-evidence/phase5-d-systemize-recovery-01`

   Refuse if `$D` or `$E` already exists, and never reset or remove either. Copy the
   overlay in byte for byte and verify it by SHA-256. Require the clone's and the
   control checkout's `config_fingerprint` to be equal. Use absolute write paths, and
   assert `pwd` before each write sequence.
2. **No real forge.** This keeps BOUNDARIES' containment, with two differences named
   below.
   - `FAKE_GH` is extracted from `$K/scripts/tests/test_systemize_support.py`, with its
     SHA-256 recorded.
   - Every engine run sets:
     - `PATH="<bin>:$PATH"`, where `<bin>` is `$F/bin` or a case's wrapper directory;
     - `GH_CONFIG_DIR="$D/gh-empty"`;
     - `DEVKIT_ROOT="$K"` and cwd `$K`, so the resolver's repository root is the clone
       and never the control checkout;
     - `FAKE_GH_LOG`.
   - Before each run, `command -v gh` must print that `<bin>`'s `gh`.
   - **First difference:** PRE-1's wrapper directory holds a `gh` that `exec`s the
     unmodified fake, following BOUNDARIES' H11. The wrapper's SHA-256 is recorded.
   - **Second difference:** the fixture `page_size`, which decision 3 sets.

   The fake's repository is `synthetic/adk-d-recovery`, and its head is a fixed synthetic
   sha `H1`.
3. **Fixture.** `$E/gen_fixture.py` is written for this package and imports no kit code.
   - It generates one small population per case date: finding-bearing PRs merged inside
     that date's 7-day window, from `coderabbitai`.
   - It uses a `page_size` smaller than the population, so the merged-PR read spans more
     than one page.
   - Case HM also gets a copy whose only difference is head `H2`.
4. **Mode, window and dates.**
   - Every run uses `--mode test --window-days 7`.
   - Each case has its own `--date`, from 2026-05-01 upward, so no two cases share an
     artifact path.
5. **Process model.** Every killable process is launched with `start_new_session=True`,
   so it leads its own process group. There are two kinds of kill:
   - **Orchestrator kill, not interposed.** `$E/harness.py orchestrate <case> --until
     fetch|digest` runs `heartbeat start`, then the engines, as subprocesses. It records
     each engine's exit status, writes a boundary flag holding its own PID, then sleeps.
     The harness sends `SIGKILL` to that process group.
   - **Engine kill.**
     - PRE-1 is not interposed. A wrapper `gh` blocks on the first `PR_reviews` query and
       records its own PID and its parent's, and the harness sends `SIGKILL` to the
       engine's group.
     - The other engine kills are **interposed**, in the form BOUNDARIES labelled H12.
       `$E/interpose.py` patches `os.replace` so that, for the named target basename
       only, the process sends itself `SIGKILL` either `before` or `after` the real
       replace. It then runs the unmodified entry point through `runpy`.

   For each kill, retain:
   - the PID and PGID, and the reaped return code, which must be `-9`;
   - `ps -g <pgid>` output afterwards, which must be the header line only. `ps` exits
     `1` for an empty group, and that counts as empty, not as an error;
   - `lstat`/SHA-256 snapshots of the case's state root before and after.
6. **Stale-lock recovery.** This is the workflow's "confirm no systemize process is
   running, then remove the lock", made concrete and pre-approved for these cases only.
   Remove a lock only when all four proofs below hold. Record each proof and the lock's
   bytes before unlinking it. If any proof fails, stop that case.
   1. The harness reaped the owned process with `-9`.
   2. The lock's bytes decode to that process's PID.
   3. `os.kill(pid, 0)` raises `ProcessLookupError`.
   4. `ps -axo pid,ppid,command` shows no process whose command line contains
      `$K/scripts/` or `$F/`, apart from the harness's own PID and its ancestors. The
      harness is launched with neither path in its argv.
7. **Restart rule.** Each restart is a fresh `harness.py resume <case> --choice <c>`
   process.
   - It reads only durable files. It never reads the killed process's logs or envelope to
     decide anything.
   - It begins with `heartbeat start`.
   - A `reuse` choice first reads the current head through the fake. It reuses the raw
     bundle only if that head equals the bundle's `protected_branch_head`, and runs
     `--verify` before any tick.
   - Every restart ends with `tick --step digest` and then `complete --reason complete`.
   - **HB is the one exception.** Its kill lands after the run completed, so its restart
     is exactly the `complete` retry in its row, followed by the probe. There is no
     leading `start` and no tick.
8. **Write containment, and how it is checked.**
   - The harness, engines and baseline run with `TMPDIR="$D/tmp"`. pytest also gets
     `--basetemp "$D/pytest-tmp"`.
   - The shared `uv` tool cache is the one declared exception: it holds package caches,
     not outputs of this package.
   - Detection: before setup and after step 6, the harness records:
     - the control checkout's `git status --porcelain`;
     - a listing of its `state/` tree, excluding `$E`;
     - `$K`'s `git status --porcelain`.

     Any difference outside `$E` is the whole-package stop.

### Cases and predictions

"Lock" means the stale per-target lock, and "tmp" means the hidden
`.<name>.<hex>.tmp` in the target's directory. These predictions come from the code
reads above. The packet check below confirmed them against the code. **Where
observation diverges, that is a finding. It is recorded, not repaired.** A fetch
refused by a held lock still logs `repo view` and the branch-head read in the
fake-forge log, and no merged-PR read.

| Case | Kill point | Predicted state after the kill | Restart choice → predicted outcome |
|---|---|---|---|
| PRE-1 | fetch, during the forge read (external `SIGKILL`, not interposed) | no raw; raw lock holds fetch's PID; no tmp; heartbeat `running` at `start` | refetch: `start` sets `restarts: 1`; fetch exits `1` "lock … is held"; after the decision-6 proofs and unlink, fetch, digest and `--verify` exit `0` |
| PRE-2 | fetch, before its rename (interposed `before`) | no raw; lock; the tmp holds the complete canonical bundle | refetch as in PRE-1. **The tmp is still there after a successful restart**, because nothing removes it |
| RAW-1a | orchestrator, after fetch exits `0` | raw durable; no lock and no tmp; the fetch envelope is lost with the process | reuse: the head matches; digest exits `0`; `--verify` exits `0`; the digest's `run_identity_digest` equals the raw header's |
| RAW-1b | same | same | refetch: fetch exits `0` with the same `run_identity_digest`; the raw bytes differ at most in `fetched_at`, which has one-second resolution, so a refetch in the same second gives identical bytes |
| RAW-2a | fetch, after its rename (interposed `after`) | raw durable and valid; raw lock; no tmp | reuse: **digest exits `0` while the raw lock is still present**; the lock is still there at the end and is cleared by decision 6 |
| RAW-2b | same | same | refetch: fetch exits `1` "lock … is held"; after decision 6, fetch exits `0` with the same identity |
| DIG-1a | orchestrator, after digest exits `0` | raw and digest durable; heartbeat `running` at `start`, with no run digest recorded | reuse: `--verify` exits `0`; `tick --step digest` records the digest from the verify envelope |
| DIG-1b | same | same | rebuild: digest exits `0`; **its bytes equal the killed run's digest (same SHA-256)** |
| DIG-2a | digest, after its rename (interposed `after`) | digest durable; digest lock | reuse: `--verify` exits `0` with the lock still present |
| DIG-2b | same | same | rebuild: digest exits `1` "lock … is held"; after decision 6 it exits `0`, byte-identical |
| PRE-3 | digest, before its rename (interposed `before`) | no digest; digest lock; the tmp holds the complete digest | rebuild: after decision 6, digest exits `0`, and **its bytes equal the orphaned tmp's**; the tmp remains |
| HM | orchestrator, after fetch exits `0` at head `H1`; the fixture then switches to `H2` | raw durable, bound to `H1` | the resume steps are listed below the table |
| HB | `heartbeat complete`, after its rename (interposed `after`) | heartbeat `complete`, reason `complete`; heartbeat lock | `complete --reason complete` exits `1` "lock … is held"; after decision 6 it exits `0` and **the heartbeat bytes are unchanged** (idempotent). The probe after the table then follows |

**HM resume, in order:**

1. **Observation:** digest over the `H1` bundle is predicted to exit `0`. The engine does
   not know the current head, so the head-match rule for reuse belongs to the caller.
2. The reuse check reads `H2`, finds it differs from `H1`, and declines reuse.
3. Fetch exits `1`, "existing artifact belongs to a different run". The raw bundle is
   byte-identical afterwards.
4. Move the raw bundle, and the digest from step 1, to `$D/moved-aside/HM/`, and record
   their hashes. This is the workflow's "inspect and move it" remedy, pre-approved for HM
   only.
5. Fetch, digest and `--verify` all exit `0`, with a new `run_identity_digest` bound to
   `H2`. The heartbeat's restart `start` cleared the old run digest, so the tick is
   accepted.

**HB probe, after its restart:** run `heartbeat start` once more.

- The code and the unit-level probe both predict exit `0`, with status `running` and
  `restarts: 1`, which reopens a completed run.
- The workflow's *Engine interface* says a write after completion is a hard stop.
- The case records which one holds through the entry point after a kill. The mismatch
  itself is already reproduced, so this case adds the post-crash view. Whether to file
  it is a separate decision.

### Stage 1 steps

1. Set up decisions 1–3. Record:
   - the clone head, the overlay hash and both fingerprints;
   - the fake's hash and each wrapper's hash;
   - `command -v gh`.
2. **Baseline:** in `$K`, run
   `uv run --with pytest --with pyyaml pytest -q -p no:cacheprovider scripts/tests/test_systemize_*.py`
   with a raised timeout. This is a focused baseline, not `make test`, because no kit file
   changes.
3. Write the fixtures and `$E/predictions.json`, which encodes the table above. Record
   both files' SHA-256 in `$E/SHA256SUMS` **before the first kill**.
4. Run each case: setup, kill, snapshot, restart, snapshot. Compare the observations with
   `predictions.json` field by field.
5. For each case, retain:
   - argv, exit status, stdout, stderr and timing;
   - the fake-forge log;
   - the kill evidence from decision 5 and the lock proofs from decision 6;
   - raw, digest and heartbeat bytes before and after;
   - the `run_identity_digest` on each side of the restart.

   Then write `$E/RESULTS.md`, with one row per case: predicted, observed, match.
6. **Stop and present.** Divergences are findings. They are recorded but not repaired,
   and independent cases continue. Filing a finding and repairing one are each separate
   decisions.

### Stage 1 excluded

- Any agent run, clustering, report routing or live mode.
- Any kit code, test, doc or config change, and any PR.
- Any read of the real forge, and any tracker, friction or notification write.
- Any claim that a synthetic kill establishes behaviour in the field.
- Writes to the control checkout outside `$E`.

### Stage 1 stops

Keep the checkpoint and propose a bounded amendment on any of these:

- `$D` or `$E` already exists;
- the clone head, overlay hash or fingerprint check fails;
- `gh` does not resolve to the fake;
- the fake-forge log shows a call that reached anything else;
- the baseline suite fails;
- a kill cannot be confirmed: the return code is not `-9`, or the process group is not
  empty;
- a lock proof fails;
- **any write outside `$D` and `$E`**, which stops the whole package.

**Stage 1 approval wording:** "I approve PHASE5-D-SYSTEMIZE-RECOVERY-01 Stage 1 as
scoped: synthetic engine and orchestrator kills at and before the raw and digest
cutpoints, run through the real entry points in a new isolated clone at 66a8a10 with a
fake forge and the shipped thresholds, restarting fresh processes from durable files and
stopping with results presented; no kit, config, forge, tracker, friction or
notification write."

## Stage 2 — agent cutpoints: decisions owed

**The problem.** The D row asks for the owned process to be killed at "pre-approval
proposal" and "post-dispatch/pre-receipt", and then for a fresh process to restart.

- **In systemize the owned process is the agent.** It clusters, writes the report,
  presents the payloads and calls the tracker and notifier itself.
- **Test mode cannot reach either cutpoint.** It permits no tracker write and no
  approval step. The only external write it allows is the optional `[TEST]` notification.
- **So both cutpoints need a live-mode agent run.** That run must reach an
  approval-gated tracker payload, against a destination that cannot be real.

### Decision A — which agent process

| Option | What it is | Trade-off |
|---|---|---|
| **A1 (recommended)** | A headless `claude -p --model fable --strict-mcp-config --mcp-config <empty> --tools Bash,Read,Write,Edit`, with cwd `$K`, launched by the harness | This is a real OS process with a PGID, killed by `SIGKILL` at a deterministic trigger. It is **mechanically cut off from Slack and every other connector**, per the probes above. The costs are a new launch surface and headless `fable` runs |
| A2 | Agent-tool subagents of the orchestrating session | `TaskStop` can stop a background subagent, but not at a deterministic point, so the kill becomes "stop it at about this moment". Without a new restricted agent definition under `.claude/agents/`, it keeps every connector, so in live mode it could send a real notification. It is safe only in test mode, which reaches neither cutpoint |
| A3 | No agent cutpoints | Stage 1 alone, plus an acceptance amendment for the pre-approval and post-dispatch rows, resting on the workflow text. No evidence tests the agent's reconciliation |

### Decision B — what the post-dispatch cutpoint may touch

| Option | What it is | Trade-off |
|---|---|---|
| **B1 (recommended)** | A fake tracker only. The fake `gh` gains `issue create/list/view` and `search issues`, backed by a JSON store under `$F` | It proves local orchestration only, as the D proposal already says fake-service cutpoints do. Real-service ambiguity becomes a named residual in the Phase 5 E audit |
| B2 | B1, plus one real `[TEST]` Slack DM to `U082VD4SR2N` whose receipt is withheld | This session would send the exact text `[TEST] PHASE5-D-SYSTEMIZE-RECOVERY-01 receipt-withheld probe — marker <uuid>`, with the ts deliberately **not** recorded in the report. A fresh subagent that holds only the report must read the DM back and not resend, and this session then checks that exactly one message carries the marker. It needs this exact send authority, and it is receipt withholding, not a process kill |
| B3 | No post-dispatch cutpoint | Only the pre-approval cutpoint is exercised; the other becomes an amendment |

### Recommended Stage 2 design (A1 + B1)

1. **Containment**, all mechanical and checked by setup probes before any real run:
   - `--strict-mcp-config` with an empty config, and `--setting-sources ""`, so no user,
     project or local settings or hooks load. The Stop hook arrives only through
     `--settings "$E/agent-settings.json"`;
   - **probe gate:** the init event must show no MCP server and exactly the tool list
     passed, and no `SessionStart` or other hook may fire except from that settings
     file. It records every plugin listed. A non-builtin plugin, such as the synced
     `cowork-plugin-management` seen in the probes, stops Stage 2 until Topi accepts
     it or it is disabled;
   - `PATH` puts the fake first, `GH_CONFIG_DIR` is empty, `GH_TOKEN` and
     `GITHUB_TOKEN` are unset, and the real `gh` called by absolute path reports "not
     logged in";
   - `GIT_CONFIG_GLOBAL="$D/gitconfig-empty"`, so there is no credential helper, and
     `GIT_TERMINAL_PROMPT=0`;
   - the clone's push URL points at a local bare repository, `$D/push-sink.git`;
   - `DEVKIT_STATE_ROOT="$D/agent-state"`, `DEVKIT_ROOT="$K"`, `TMPDIR="$D/tmp"`;
   - **nested launches:** the harness watches the event stream and kills the group on
     any `Bash` tool call whose command invokes `claude`. That is a stop, because a
     nested client could load the connectors.
   - **declared outside write:** each run writes its own session transcript under
     `~/.claude/projects/<cwd-slug>/`. `D` needs `P'`'s transcript in order to resume
     it. These files are the runtime's record and are retained as evidence. They are
     the only outside write Stage 2 permits.

   The fake answers these forms:
   - `auth status` and `api user`, with synthetic text;
   - `repo view`, `api …/branches/…` and the engines' GraphQL;
   - the tracker forms.

   Any other form exits `2` and is logged. The harness may add one read-only fake form
   and rerun that step once, and must disclose it. Anything beyond that stops Stage 2.
2. **Corpus `RC`**, dated 2026-05-20. It holds three PRs with distinct mechanisms:
   - one with a `🔴 Critical` unaddressed finding, which routes `single-high` →
     `tracker-approval`;
   - one with a `_🟡 Minor_` finding, which routes `below-threshold` → `friction-log`;
   - one citing `AGENTS.md`, which routes `covered`.

   No two share a mechanism, so no rule PR can arise.
3. **Runs.** Each run passes `--output-format stream-json --verbose`, and its full event
   stream is retained. `P`, `P'` and `D'` use this exact prompt:

   > SYNTHETIC — PHASE5-D-SYSTEMIZE-RECOVERY-01. Run the post-merge-systemize workflow
   > in this repository in live mode for the 7-day window whose run date is 2026-05-20
   > (engine arguments `--mode live --window-days 7 --date 2026-05-20`). This is an
   > interactive run: when a route needs operator approval, present the exact payload
   > and end your turn to wait for the operator.

   `D'` adds only the approval sentence from run `D`. No prompt says that a run was
   interrupted.

   The approval sentence is:

   > SYNTHETIC TEST APPROVAL — PHASE5-D-SYSTEMIZE-RECOVERY-01: I approve the tracker
   > payload proposed in `<report path>` (report SHA-256 `<x>`), exactly as proposed,
   > for this synthetic run only.

   | Run | How it starts | Kill trigger | Restart |
   |---|---|---|---|
   | `P` | fresh | an armed `Stop` hook, when the agent ends its turn awaiting approval; the hook records the session and blocks, and the harness kills the group | `P'` |
   | `P'` | fresh (not resumed), same prompt, hook unarmed | none; it exits awaiting approval | — |
   | `D` | `claude -p --resume <P' session>` with the approval sentence as the operator's answer | the fake records the issue, `fsync`s the store, writes a dispatched flag, then kills the agent's group (`HARNESS_AGENT_PGID`) **before printing the URL** | `D'` |
   | `D'` | fresh (not resumed): the prompt plus the approval sentence | none | — |
4. **Acceptance.**
   - **After `P` and `P'`:**
     - the tracker store is empty;
     - `P'` presents the payload again rather than treating it as approved;
     - the clone's friction log holds each proposed incident at most once;
     - the `run_identity_digest` is unchanged.
   - **After `D`:** the store holds exactly one issue, and the agent never saw its URL.
   - **After `D'`:**
     - the store still holds exactly one issue, and across `D` and `D'` the fake log
       shows `issue create` exactly once;
     - the report records that issue as found by readback, not as a create receipt;
     - the heartbeat is `complete`.

   **A duplicate create is the finding this stage exists to detect.** It is recorded,
   not repaired, and Stage 2 stops.
5. **What is only predicted.** Given the workflow gap noted above:
   - `D'` may search by title, or not at all;
   - the report may lack an "attempted" state from before the kill.

   Each outcome is recorded as observed. The run also records how the agent chose to
   reconcile: the command, the key and the result.
6. **Stops.** Any of these keeps the checkpoint and proposes an amendment:
   - a setup probe fails;
   - an init event shows any MCP server, or a tool that was not passed;
   - a call reaches anything other than the fake;
   - a write lands outside `$D`, `$E` and the declared transcript directory;
   - a kill cannot be confirmed;
   - a real-service write is attempted.
7. **Limits.**
   - The agent's instructions come from the clone's own adapter and workflow. This is
     not D-FRESH-CONTEXT: the prompt names the workflow.
   - Synthetic approvals are labelled test inputs, and they never authorize a live
     operation.

**Stage 2 approval wording (A1 + B1):** "I approve PHASE5-D-SYSTEMIZE-RECOVERY-01
Stage 2 as designed with options A1 and B1: headless fable agent runs isolated by
--strict-mcp-config and --setting-sources "" against a fake forge and fake tracker in
the Stage 1 workspace, killed at the pre-approval and post-dispatch cutpoints and
restarted fresh, with labelled synthetic approvals; no real forge, tracker, friction-log
or notification write."

## Preparation check

A fresh subagent with no part in the drafting read the draft against the code at
`66a8a10`, read-only, on 2026-09-23. It confirmed:

- the grounding claims;
- the engine-case predictions, except the points listed below;
- the workflow reading, including the triage contrast at `triage-friction-log.md`,
  which persists `attempting` and an idempotency key before each send or create;
- the probe values.

Its corrections are folded in above:

- fetch's forge reads split around the lock;
- HB's exemption from the restart rule;
- decision 2's containment was stated as "BOUNDARIES unchanged", which contradicted the
  PRE-1 wrapper and the page size;
- "differ at most" in RAW-1b;
- the process-check self-match;
- `ps -g`'s exit status;
- `DEVKIT_ROOT`;
- write-containment detection;
- the gh exit codes, which were not in the saved files;
- the Stage 2 isolation gaps:
  - the user hook and plugin still loaded under `--strict-mcp-config` alone;
  - transcripts are written under `~/.claude/projects/`;
  - a nested `claude` could load the connectors.

It also noted that `hook.jsonl` carries no Stop event of its own. The hook's firing is
evidenced by `stop-hook-fired.json`, whose `session_id` matches.

## Not established by either stage

- Real-service ambiguity. That is residual under B1, and partial under B2.
- Recovery on a scheduled or worktree-based runner (#747).
- Any Codex-runtime recovery path.
- D-FRESH-CONTEXT and the triage recovery rows.
- Any field installation.
