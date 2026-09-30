# Phase 5 D — PHASE5-D-TRIAGE-RECOVERY-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** This packet
turns the D-TRIAGE-RECOVERY row of the [D proposal](phase5-d-proposal_2026-09-21.md)
into an executable scope. It follows the form of
[PHASE5-D-SYSTEMIZE-RECOVERY-01](phase5-d-systemize-recovery_2026-09-23.md). Topi owns
scope changes, every exact payload, and the acceptance decision.

The row asks the package to exercise:

- an absent-state stale gate;
- valid and invalid state under a stale gate;
- invalid state without a gate;
- interruption of the prepared envelope, the intent, a quarantine and the replacement
  gate;
- an active or uncertain owner;
- the scheduled refusal;
- test-mode held evidence.

Its acceptance evidence is:

- gate ownership evidence;
- a complete capture before parsing;
- a deterministic approved intent;
- a restart on the same core, with preservation;
- state-present test-gate recovery that stays terminally held;
- no gate-only receipt ever acting as restart permission;
- ambiguous tracker writes that stay held, with no whole-sweep fallback.

**This package differs from the systemize one in one structural way.** In systemize the
agent made every route write, so the pre-approval and post-dispatch cutpoints needed a
headless agent. In triage
every recovery transition is inside the engine, behind the `recover` and `test` CLI
entries, and approval enters through the `--approval-context` file. So **no agent run is
needed**. A harness drives the real entry points, kills or stops them at chosen storage
calls, and restarts fresh processes.

**Preparation found F-1 and F-2, and a probe confirmed both. The preparation check
found F-3, a reporting defect.** Each is under *Findings from preparation*:

- **F-1:** state-present recovery quarantines only the primary gate name, so a leftover
  same-inode gate temporary wedges the mode.
- **F-2:** a state-present capture or prepared bundle is acted on without proving its
  gate owner dead.
- **F-3 (reporting only):** a released gate-only receipt is reported as "replacement
  gate changed".

So there is one decision owed, **Decision A**: whether to run the matrix now and fix
afterwards, or fix first.

Everything this package produces is **synthetic evidence, labelled as synthetic**.

## Grounding reads

All reads were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-29.

- **Protected head.** `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha`
  printed `197a2429af2ca253e4e1ee005bd39d4d21adfe27`. `gh run list --branch main --event
  push --limit 1` read run `36553523177`, `completed` / `success`, for that sha. The
  control checkout's `HEAD` and `origin/main` read the same sha.
- **The engine has moved since the last triage field run.** Stage L of
  D-TRIAGE-RESIDUAL ran on 2026-09-25 against `94bd9dc` (#801) and later heads. `git log
  --oneline 94bd9dc..197a242 -- scripts/lib/triage scripts/triage_friction_log.py
  scripts/finalize_triage.py docs/agentic-dev-kit/workflows/triage-friction-log.md` lists
  commits through `369e9ee` (#858). Every code reading and the probe below are at
  `197a242`.
- **Config.** Read with `kitconfig.load_config()`, merged, at `197a242`:
  - `tracker.backend: github-issues`, `project_name: topij/agentic-dev-kit`,
    `url: https://github.com/topij/agentic-dev-kit/issues`;
  - `triage.state_path: state/triage/triage-pipeline-state_{mode}.json`;
  - `triage.gate_path: state/triage/triage-pipeline-gate_{mode}.lock`;
  - `triage.recovery_bundle_pattern:
    state/triage/recovery-bundle_{mode}_{gate_digest}.json`.
  - The gitignored overlay sets `notify.user_key` and `state.test_guard_exclude`. A clone
    has no overlay, which the design below relies on.
- **Tools.**
  - `uv --version` printed `uv 0.12.3`.
  - `uv run --with pyyaml python3` reported Python `3.14.7`.
  - `gh --version` printed `2.97.0`.
  - `git --version` printed `2.50.1 (Apple Git-155)`.
- **The control checkout's triage state directory.** `ls -la state/triage/` listed
  `triage-pipeline-state_live.json` (modified 2026-09-28), retired `.completed-*` files, a
  gate quarantine name and a 2026-09-25 recovery bundle; `ls state/triage/ | grep -c
  'lock$'` printed `0`. Nothing there was opened. **This package must not read, write or
  rename anything there**; its containment check lists that directory by `lstat` only.

### What the engine code establishes

All points are read at `197a242`.

1. **The recovery routes are all in the engine.**
   - `run()` sends an interactive `recover` or `test` whose gate acquisition fails to
     `_blocking_recovery` (`engine.py:1738-1740`).
   - Any other entry over a held gate reports `operator-held`, with resume action "use
     interactive recover for a proven-dead owner".
   - An unattended `recover` returns before loading settings (`engine.py:1724-1725`).
2. **The gate is a complete owner record published by exclusive hard link.** It binds
   host, PID and process start (`gate.py:177-213`). `owner_status` returns:
   - `terminated` only when `os.kill(pid, 0)` raises `ProcessLookupError`;
   - `uncertain` for a foreign host, a malformed PID or process start, a
     `PermissionError`, or a current process start that is unavailable or differs;
   - `active` otherwise (`gate.py:216-234`, the `uncertain` branches at `:219-233`).
3. **Every storage write is a named call on a basename relative to a held directory
   descriptor.** That makes a deterministic cutpoint a matter of matching the basename
   (`storage.py:185-383`):
   - `exclusive_create` writes a temporary, calls `os.link(temp, name)`, then
     `os.unlink(temp)`;
   - `atomic_replace` calls `os.replace(temp, name)`;
   - `quarantine_inode` calls `os.link(source, target)`, then `os.unlink(source)`.
4. **A quarantine killed between its link and its unlink holds for good.** After the
   link the source's link count is 2 where the capture recorded 1. How the restart
   refuses depends on which name was being moved:
   - **A gate.** `quarantine_inode` compares the source's current observation, link count
     included, with the approved one, and raises "approved artifact changed before
     quarantine" (`storage.py:193-195`).
   - **The state.** `_blocking_recovery` reads the state path without `allow_links`
     (`engine.py:312`), and the read itself refuses a link count other than one: "unsafe
     artifact at held parent: <state path>" (`storage.py:155-156`). No quarantine is
     attempted.
   - Both are workflow-conformant holds. The workflow rejects a state path whose "link
     count [is] other than one" (`triage-friction-log.md:751-753`), and says "every
     mismatch is operator-held without another mutation" (`:885-887`).
   - The hold rests on that workflow text, not on the code's own intent.
     `quarantine_inode`'s branch for an already-linked target (`storage.py:196-207`)
     cannot be reached by a kill between link and unlink, because the link-count check
     fires first.
5. **The gate-only route handles same-inode gate names.** `_gate_capture` records a
   `.<gate>.<token>.tmp` alias of the gate's inode (`recovery.py:44-62`), and the
   gate-only route quarantines every recorded name (`recovery.py:223`, `:244`).
   **The state-present routes quarantine only the primary name** (`recovery.py:738`,
   `:763`). That is F-1.
6. **Only some of the stale-gate routes prove the owner dead.**
   - These capture routes pass `require_terminated=True` (`recovery.py:42`):
     `gate_only_plan`, `test_gate_state_plan`, and the stale-gate `capture_state_present`.
   - These routes check no owner status at all: `_blocking_recovery`'s
     `state-present-capture` and `state-present-prepared` bundle routes
     (`engine.py:332-345`), and `resume_state_action`.
   - A capture published by an ungated `recover` binds that invocation's own gate, and
     that invocation leaves the gate on disk (`lease.held = False`, `engine.py:1793-1801`).
   - The workflow accepts that gate only after "exact termination proof", and stops
     otherwise (`triage-friction-log.md:767-771`). That is F-2.
7. **Invalid state is abandonable only when it proves nothing was attempted.**
   - It must be a base-key-exact `triage-run-state` whose phase is none of the declared
     phases, with every evidence array empty (`recovery.py:673-685`).
   - Anything else is retired as a finished run or held as
     `external-attempt-absence-unproven` (`recovery.py:686-702`).
   - The engine never writes such a state, so the invalid-state cases need a
     **synthetic invalidation** of an engine-written state.
8. **The tracker adapter shells out to `gh api --hostname <host>`**
   (`providers.py:90-195`), in these forms: a paged `issues?state=all` listing, a
   single-issue read, and a `POST` create. After a `POST` that returns, `create` searches
   again, retrying on a short bounded backoff until the listing shows the returned issue
   (`providers.py:162-181`). No K case reaches that retry, because its `POST` never
   returns.
   - The engine persists an `attempting` operation before the create
     (`engine.py:1003-1007`).
   - A resume reconciles an unsettled operation by marker read-back. Exactly one exact
     match is `verified`; **anything else, zero matches included, is `ambiguous` and
     operator-held** (`engine.py:959-985`). The workflow lets "no match" prove no landing
     "only when the tracker read is complete and authoritative"
     (`triage-friction-log.md:1076-1077`). The engine never treats a zero-match listing
     as authoritative, and #808's lagging list is the reason it should not.
   - Finalization refuses an unaccounted batch before any forge action:
     `sweep_ids` raises "approved tracker batch is not authoritatively accounted"
     (`finalize.py:185-186`, called at `engine.py:1543`).
9. **The protected-head check uses `git ls-remote origin`** (`providers.py:350-367`). So
   a clone whose `origin` is a local bare repository makes no network call there.
   Finalization past `sweep_ids` would hard-stop on such an origin, in
   `_forge_destination` (`engine.py:1484-1495`, reached at `:1596`). K-U stops at
   `sweep_ids` (`:1543`), before that point. **No case may extend past it.**

### Preparation probe

The probe was `probe_recovery.py`, run with `uv run --with pyyaml python3` from the
session scratchpad on 2026-09-29. It imported the engine library from the control
checkout at `197a242` and built temp repositories the way `scripts/tests/test_triage_engine.py`
does. It called the engine's `run()` rather than the CLI. The probe, its output and
`SHA256SUMS` are retained in
`state/review-evidence/phase5-d-triage-recovery-prep-20260929/`. It made no kit, network
or control-state write.

- **P1 (F-1):**
  - **The kill.** A `resume` child sent itself `SIGKILL` just before unlinking its gate
    temporary. It was reaped at `-9`.
  - **After the kill:** the gate and `.triage-pipeline-gate_live.lock.<token>.tmp`, one
    inode, `links 2`.
  - **The approved recovery:** `recover` offered `preserve-valid-state-and-quarantine-old-gate`,
    and the approved `recover` returned `resume`.
  - **What it left:** the alias and the new quarantine name, still one inode at `links 2`.
  - **The wedge.** The next `resume` returned `operator-held` / "orphaned gate temporary
    identity is ambiguous", and `recover` returned "blocking gate disappeared". No engine
    route remains.
- **P2 (F-2):**
  - **The owner.** A `recover` child over an ungated, synthetically invalidated state
    published its capture bundle. A monkeypatch of `engine.state_action_plan` then made
    it send itself `SIGSTOP`; this was not a storage-call cut. `ps -o stat=` read `T`,
    and the gate's `process_id` was that child's PID.
  - **The second and third calls.** They ran inside the probe's own process, not as
    separate children. The second `recover` printed the `abandon-invalid-state` plan,
    and the third, approved, returned `recovered-safe-to-restart`.
  - **The preparation check reproduced it with a storage-call cut** and a separate
    process per step (*Preparation check*).
  - **What it did to the live owner:** quarantined the stopped owner's gate and the state,
    and published the restart receipt. The owner still read `T` afterwards.
  - **The owner's resumed output.** On `SIGCONT` the owner printed "operator-held invalid
    state captured before parse" and exited `0`. That report was stale.

## Stage 1 — the recovery matrix, synthetic

**Purpose:** drive every row-named route through the real CLI entry points, in a new
isolated clone. Kill or stop owned processes at chosen storage calls, restart fresh
processes from durable files alone, and compare each outcome with a prediction sealed in
advance.

Stage 1 makes no write to the kit, the control checkout's `state/triage/`, config, the
real forge or tracker, the friction log, or notifications.

### Decisions bound by Stage 1

1. **Workspace.** Bind these roots:
   - `D=/private/tmp/adk-phase5-d-triage-recovery-01`;
   - `O="$D/origin.git"`, a `git clone --bare --no-hardlinks
     /Users/topi/Coding/agentic-dev-kit "$O"`. It is a local clone, so there is no network
     call and no dependence on where GitHub's `main` has moved. `git -C "$O" cat-file -e
     197a2429af2ca253e4e1ee005bd39d4d21adfe27^{commit}` must succeed;
   - `S="$D/stage"`, a clone of `$O`, detached at `197a242`;
   - `K="$D/kit"`, a clone of `$O` made after the fixture commit (decision 2), so
     `origin` is the local bare repository;
   - `F="$D/fake"`, holding the executing copy of the fake `gh` at `$F/bin/gh`, its
     per-case stores and its call log. The fake is written and sealed at `$E/fake/gh`, then
     copied to `$F/bin/gh`; both are hashed, and the hashes must match;
   - `R="$D/r"`: each case's `DEVKIT_STATE_ROOT` is `$R/<case>`;
   - `E=/Users/topi/Coding/agentic-dev-kit/state/review-evidence/phase5-d-triage-recovery-01`.

   Refuse if `$D` or `$E` already exists, and never reset or remove either. Use absolute
   write paths, and assert `pwd` before each write sequence.
2. **Fixture commit.** One commit on `197a242`, made in `$S` with a synthetic author, is
   pushed to `$O` as `main`. It changes two files:
   - `docs/kit-friction-log.md` gains a `## 2026-05-20` section with two bullet entries,
     each titled `SYNTHETIC — PHASE5-D-TRIAGE-RECOVERY-01 …`, in the form
     `scripts/tests/test_triage_engine.py` uses. The engine's freeze prints the candidate
     index, and that output is the only count this package uses.
   - `config/dev-model.yaml` sets `tracker.project_name: synthetic_adk/d-triage-recovery`
     and a matching `tracker.url`. The underscore is deliberate: GitHub account names
     cannot contain one, so even a leaked real call cannot name a real repository.

   The push is `git -C "$S" push "$O" +HEAD:refs/heads/main`. Record the fixture commit's
   sha, both files' SHA-256, and `$K`'s `origin/main`, which must equal the fixture sha.
3. **Containment.** Every engine process runs with:
   - `PATH="$F/bin:$PATH"`;
   - `GH_CONFIG_DIR="$D/gh-empty"`, with `GH_TOKEN` and `GITHUB_TOKEN` unset;
   - `GIT_CONFIG_GLOBAL="$D/gitconfig-empty"`, `GIT_CONFIG_NOSYSTEM=1` and
     `GIT_TERMINAL_PROMPT=0`. The Command Line Tools credential helper is what stopped
     SYSTEMIZE-RECOVERY Stage 2's first probe;
   - `TMPDIR="$D/tmp"`, cwd `$K`, `DEVKIT_STATE_ROOT="$R/<case>"`, and `DEVKIT_ROOT`
     unset.

   **Setup probes:**
   - `command -v gh` prints `$F/bin/gh`;
   - the real `gh`, by absolute path, reports not logged in;
   - `git -C "$K" remote get-url origin` prints `$O`.

   The fake answers only the adapter's forms listed in point 8, for the fixture's
   repository. Any other form exits `2` and is logged. The harness may add one read-only
   form and rerun that step once, and must disclose it. Anything beyond that stops the
   package.
4. **Process model.** The harness runs under `uv run --with pyyaml python3` and launches
   each engine with its own `sys.executable`, `start_new_session=True`, and a
   per-invocation timeout. A hang is a stop. A cut is one of two kinds:
   - **Interposed** (the H12 form from BOUNDARIES and SYSTEMIZE-RECOVERY Stage 1).
     `$E/interpose.py --op link|unlink|replace --match <basename glob> --when before|after
     --nth <n> --signal KILL|STOP -- <entry point> <args>`.
     - It wraps `os.link`, `os.unlink` and `os.replace`, matching the destination
       basename for `link`/`replace` and the path basename for `unlink`.
     - On the `n`th match it signals itself before or after the real call. "After" fires
       once the call completes, whether it returned or raised: `atomic_replace` always
       unlinks its temporary in a `finally`, and that call raises `FileNotFoundError` after
       a successful replace.
     - It then runs the unmodified entry point through `runpy`.
   - **Fake-tracker** (family K). The fake `gh` writes a flag file and blocks. The harness
     then sends `SIGKILL` to the engine's process group.

   For each `KILL`, retain:
   - PID, PGID and the reaped status, which must be `-9`;
   - `ps -g <pgid>`, which must be the header line only. `ps` exits `1` for an empty
     group, and that counts as empty;
   - the gate record's `process_id`, and `os.kill(pid, 0)` raising `ProcessLookupError`.

   For each `STOP`, retain `ps -o stat=` output beginning with `T` before any other
   process runs. Under `start_new_session=True` it reads `Ts`, so the check is a prefix
   match. A `finally` in the harness sends `SIGCONT` and then `SIGKILL` to any owned
   process still stopped when a case ends, or when the harness fails partway through one.
5. **Synthetic inputs, each labelled and hashed in `$E`.**
   - **Invalidation.** Taking an engine-written state, the harness keeps only the base
     keys and sets `phase: "synthetic-unknown-phase"`, which is the abandonable shape. For
     the held cases it instead adds one unknown top-level key to a state that holds an
     `attempting` operation.
   - **Uncertain owner.** The harness rewrites a stale gate's `host` to
     `synthetic-foreign-host.invalid` in both the top-level field and `gate_claim_core`,
     recomputes `gate_claim_core_digest`, and writes canonical bytes with the engine's own
     `dumps`. Anything less reads as "blocking gate is malformed" (`recovery.py:37-40`,
     `gate.py:43`).
   - **Analysis requests.** They are synthetic proposals whose `project` is the fixture's
     `project_name`.
   - **Approvals.**
     - Every approval-context file carries `operator_identity: "SYNTHETIC-TEST-OPERATOR"`,
       never `topij`. #815 records the defect of a synthetic approval under the
       operator's real name.
     - Recovery approvals have the shape `{"recovery_approval":{"decision":"approve",
       "source":"current-session","approver_identity":…,"core_digest":…}}`, with a
       matching `source_read_back` (`engine.py:203-220`).
     - The tracker approval is `approve TRI-01`, so TRI-02 parks.
     - A note in `$E` records that the harness wrote and attests every context file.
     - These approvals authorize nothing outside `$R`.
6. **Restart rule.**
   - Every restart is a fresh process that reads only durable files. The killed process's
     output never decides anything.
   - **An approval digest always comes from a plan printed by an invocation that
     completed.** Where a case plans twice, the two digests must be equal: that is the
     same-core evidence.
7. **Write containment, and how it is checked.** These are the surfaces checked; a
   difference on any of them is the whole-package stop.
   - Before setup and after the last case:
     - the control checkout's `git status --porcelain`;
     - an `lstat`-only listing of the control checkout's `state/triage/` (name, inode,
       link count, size, mtime), with no file opened;
     - a listing of the control checkout's `state/` excluding `$E`.
   - After each case, `$K`'s `git status --porcelain`, which must be empty. `/reports/`
     and `__pycache__/` are gitignored at `197a242` (`.gitignore:30`, `:2`).
   - The shared `uv` cache is the one declared outside write. It holds package caches, not
     outputs of this package.

### Cases and predictions

**Notation.**

- `KG` means: run the named entry under `interpose.py --op unlink --match
  '.triage-pipeline-gate_<mode>.lock.*.tmp' --when after --nth 1 --signal KILL`. That
  kills the process right after its gate is published, and leaves a stale gate with a
  dead owner.
- `KG-alias` is the same call with `--when before`. It leaves the gate plus its same-inode
  temporary.
- `AW` is the live setup: `new {}`, then `resume` with the analysis request. It leaves
  `awaiting-approval` state and no gate.
- `plan` is `recover {}`, or `test {}` in test mode. `approve` is the same entry with the
  plan's digest.
- Quoted strings are the result's `detail`. Every result's `outcome` is `operator-held`
  unless the case says otherwise.
- "Bytes kept" means every file in the case's state root is byte-identical, and has the
  same inode and link count, before and after that step.

**Family G — absent live state, stale gate (the gate-only route)**

| Case | Setup and cut | Predicted after the cut | Restart sequence → predicted |
|---|---|---|---|
| G0 | `new {}` under `KG` | gate only; no state, no frozen snapshot | `resume` → "single-writer gate is already held", bytes kept; `recover --context unattended` → "unattended recovery does not inspect or change artifacts", bytes kept; `plan` twice → "gate-only recovery capture awaits exact approval", equal `prepared_core_digest`, bytes kept; `approve` → "gate-only-operator-held": old gate at `.quarantine-<16>`, replacement released, receipt at the state path; `new {}`, `resume {}` and `recover {}` → "gate-only held receipt replacement gate changed", no frozen snapshot created, receipt bytes kept. The outcome is the workflow's (`triage-friction-log.md:169`), but the detail misnames the cause: see F-3 |
| G-PREP | G0 through `plan`; then `approve` cut at `unlink` `.recovery-bundle_live_*.tmp` after, n 1 | old gate; `gate-only-prepared` bundle; no state | `plan` → "gate-only-operator-held". The fresh process finishes the approved transition from the bundle alone. The same step publishes the intent and replaces it with the receipt, so the intent is not visible between snapshots; the receipt's `atomic_replace` succeeding under `expected_digest` equal to the intent's digest is the evidence that it matched (`recovery.py:270`, `storage.py:253-256`) |
| G-INTENT | same, cut at `unlink` `.triage-pipeline-state_live.json.*.tmp` after, n 1 | old gate; bundle; intent at the state path, whose bytes equal the canonical `intended_intent` in the bundle and hash to its `intended_intent_digest` | `resume` and `--context unattended` with no entry → "single-writer gate is already held", bytes kept; `plan` → "gate-only-operator-held" |
| G-QMID | same, cut at `link` `triage-pipeline-gate_live.lock.quarantine-*` after, n 1 | gate and its quarantine name, one inode, `links 2`; intent | `plan` → "approved artifact changed before quarantine", bytes kept; repeated → the same. **Terminal hold** (point 4) |
| G-QDONE | same, cut at `unlink` `triage-pipeline-gate_live.lock` after, n 1 | gate absent; quarantine name; intent | `resume` → "gate-only-recovery-intent", bytes kept; `plan` → "gate-only-operator-held", with `replacement_quarantine_observations` empty |
| G-REPL | same, cut at `unlink` `.triage-pipeline-gate_live.lock.*.tmp` after, n 1 | replacement gate with a dead owner; old gate quarantined; intent | `plan` → "gate-only-operator-held"; the replacement is quarantined to `.recovery-quarantine-<16>`, and `replacement_quarantine_observations` holds it |
| G-RCPT | same, cut at `replace` `triage-pipeline-state_live.json` after, n 1 | held receipt; replacement gate present with a dead owner | `plan` → "gate-only-operator-held", bytes kept; `new {}` → "single-writer gate is already held". The replacement gate stays: the receipt is terminal |
| G-ALIAS | `new {}` under `KG-alias` | gate plus alias, `links 2`; no state | `plan` → capture records the alias; `approve` → "gate-only-operator-held", with both names quarantined (`recovery.py:223`) |

**Family V — valid live state, stale gate**

| Case | Setup and cut | Predicted after the cut | Restart sequence → predicted |
|---|---|---|---|
| V0 | `AW`, then `resume {}` under `KG` | state unchanged; stale gate | `plan` twice → "state-present recovery action awaits exact approval", action `preserve-valid-state-and-quarantine-old-gate`, equal `action_core_digest`; a `state-present-capture` bundle whose `state_digest` equals the pre-recovery state file's SHA-256; `approve` → "resume", gate at `.quarantine-<16>`; `resume {}` → "active session resumed", `awaiting-approval`, `state_claim.reason: normal-resume`, proposal digests unchanged |
| V-PREP | V0 through `plan`; `approve` cut at `replace` `recovery-bundle_live_*.json` after, n 1 | bundle `state-present-prepared`; gate still present | `plan` → "resume" without asking again; then `resume {}` as in V0 |
| V-QMID | same, cut at `link` `triage-pipeline-gate_live.lock.quarantine-*` after, n 1 | gate and quarantine name, `links 2` | `plan` → "approved artifact changed before quarantine", bytes kept. **Terminal hold** |
| V-QDONE | same, cut at `unlink` `triage-pipeline-gate_live.lock` after, n 1 | recovery complete; its output lost | `recover {}` → "captured state is valid; recovery refused"; `resume {}` as in V0 |
| V-ALIAS | `AW`, then `resume {}` under `KG-alias` | state; gate plus alias | `plan`; `approve` → "resume"; **predicted divergence (F-1):** `resume {}` → "orphaned gate temporary identity is ambiguous", and `recover {}` → "blocking gate disappeared". The alias and the quarantine name are left sharing one inode |

**Family I — invalid live state, stale gate**

| Case | Setup and cut | Predicted after the cut | Restart sequence → predicted |
|---|---|---|---|
| I0 | `AW`, synthetic invalidation (abandonable), then `resume {}` under `KG` | invalid state; stale gate | `plan` twice → action `abandon-invalid-state`, equal digests; `approve` → "recovered-safe-to-restart": state bytes at `.quarantine-<16>` unchanged, a `recovered-safe-to-restart` receipt at the state path, gate quarantined; `new {}` → "verified recovery receipt replaced by reserved new state", with `state_claim.reason: live-receipt-restart` |
| I-PREP | I0 through `plan`; `approve` cut at `replace` `recovery-bundle_live_*.json` after, n 1 | prepared bundle; state and gate unchanged | `plan` → "recovered-safe-to-restart"; `new {}` as in I0 |
| I-QMID | same, cut at `link` `triage-pipeline-state_live.json.quarantine-*` after, n 1 | state and quarantine name, `links 2` | `plan` → "unsafe artifact at held parent: <absolute state path>", bytes kept; repeated → the same; `new {}` → "single-writer gate is already held". **Terminal hold** (point 4). `predictions.json` templates the path |
| I-QDONE | same, cut at `unlink` `triage-pipeline-state_live.json` after, n 1 | state absent; quarantine name; gate | `plan` → "recovered-safe-to-restart" (the bundle route, `engine.py:321-346`, runs before the absent-state route, `engine.py:347`) |
| I-RCPT | same, cut at `unlink` `.triage-pipeline-state_live.json.*.tmp` after, n 1 | receipt present; gate unquarantined | `plan` → "recovered-safe-to-restart"; receipt bytes unchanged; gate quarantined |
| I-HELD | K-U's setup and cut (family K) in its own root; then invalidation with an extra key | invalid state holding an `attempting` operation; stale gate | `plan` → "external-attempt-absence-unproven": the bundle becomes `state-present-held`, and state and gate are kept byte-identical; `plan` again → "recovery evidence retained: state-present-held"; `new {}` → "single-writer gate is already held". **Terminal hold; no abandon offered** |

**Family U — invalid live state, no gate**

| Case | Setup | Restart sequence → predicted |
|---|---|---|
| U0 | `AW`, then synthetic invalidation (abandonable) | `recover {}` → "invalid state captured before parse", action `abandon-invalid-state`; a capture bundle is published and its own gate is left on disk (point 6); `plan` → "state-present recovery action awaits exact approval", by the bundle route, with the same `action_core_digest`; `approve` → "recovered-safe-to-restart", gate quarantined; `new {}` as in I0 |
| U-HELD | K-U's chain through its approved recovery, which leaves valid state and no gate; then invalidation with an extra key | `recover {}` → "external-attempt-absence-unproven", with the gate left on disk; `new {}` → "single-writer gate is already held"; `recover {}` → "recovery evidence retained: state-present-held". **Terminal hold** |

**Family O — active or uncertain owner**

| Case | Setup and cut | Restart sequence → predicted |
|---|---|---|
| O-ACTIVE | `AW`, then `resume {}` under `KG` with `--signal STOP` | `recover {}` → "blocking gate owner is active or uncertain": no bundle, bytes kept; then `SIGCONT` → the owner exits `0` with "active session resumed" and releases its gate; `recover {}` → "captured state is valid; recovery refused" |
| O-UNCERTAIN | V0's setup and cut, then the synthetic foreign-host gate edit | `recover {}` → "blocking gate owner is active or uncertain", no bundle, bytes kept |
| O-CAPTURE | U0's setup; `recover {}` under `interpose --op unlink --match '.recovery-bundle_live_*.tmp' --when after --nth 1 --signal STOP` | **Predicted divergence (F-2)**, the probe's P2 through the CLI. A second `recover {}` → "state-present recovery action awaits exact approval", offering the abandon plan without any owner check; a third, approved → "recovered-safe-to-restart", with the live owner's gate and the state quarantined while `ps` reads `Ts`; on `SIGCONT` the owner prints its JSON result with the stale detail "invalid state captured before parse" and exits `0`. Every `_blocking_recovery` return is `operator-held`, so the outcome does not show the divergence. The divergence is that the engine offers, and on approval executes, a plan where the workflow requires a stop for missing termination proof (`triage-friction-log.md:767-771`) |

**Family T — test mode.** Every T case must leave its root's live-mode files
byte-identical. T-HELD therefore runs in a root that also holds a stale live gate and live
state, made by V0's setup.

| Case | Setup and cut | Restart sequence → predicted |
|---|---|---|
| T-HELD | `test {}`, then `test` with the analysis request, then `test {}` under `KG` (test gate) | `plan` → "blocking test gate state capture awaits exact held-evidence approval"; `approve` (with `capture_core_digest`) → "test-gate-state-present", a `state-present-test-gate-held` bundle, with gate and test state kept byte-identical; `test {}` → "recovery evidence retained: state-present-test-gate-held"; `test --context unattended` → "single-writer gate is already held". **Terminal hold**; live files kept |
| T-GATE | `test {}` under `KG` in a fresh root | `plan` → "gate-only recovery capture awaits exact approval"; `approve` → "gate-only-operator-held" (test mode); `test {}` → "gate-only held receipt replacement gate changed", with no test draft created and the receipt kept (F-3) |
| T-INVALID | test `AW` equivalent, then synthetic invalidation | `test --context unattended` → "invalid test state preserved without unattended recovery", bytes kept; `test {}` → "invalid test state captured before parse"; `approve` → "test-recovered-safe-to-restart"; `test {}` → "verified recovery receipt replaced by reserved new state" |

**Family K — ambiguous tracker write, fake tracker.** Both cases run `AW`, then `resume`
with the approval request, the context, and `--enable-github-tracker`.

| Case | Cut | Predicted after the cut | Restart sequence → predicted |
|---|---|---|---|
| K-L | the fake stores the issue, `fsync`s, flags, and blocks before answering; the harness kills the group | state `tracker-write`, last operation `attempting`; stale gate; one issue in the store; one `POST` in the log | `resume --enable-github-tracker` → "single-writer gate is already held", with no fake call; `plan`, then `approve` → "resume"; `resume {} --enable-github-tracker` → operation `verified`, `verified_route: ambiguous-response-then-exact-read-back`, `verified_tracker_identifiers` naming the stored issue. **Still one issue and one `POST`** |
| K-U | the fake flags and blocks **before** storing; the harness kills the group | as K-L, but the store is empty | the same recovery; `resume {} --enable-github-tracker` → operation `ambiguous`, capability "retained tracker attempt is not authoritatively reconciled"; a second resume gives the same, **with no `POST`**; then `finalize_triage.py --request <file> --enable-github-forge`, the file holding `{"finalize":true,"worktree":"$D/wt-K-U"}`, → "approved tracker batch is not authoritatively accounted". **No `$D/wt-K-U`, no sweep branch, and `$O` refs unchanged.** |

K-U is the row's "ambiguous tracker writes remain held; no whole-sweep fallback". **Its
hold is by design, not a finding.**

- "Process termination or a missing final chat summary never authorizes repeating a
  write" (`triage-friction-log.md:588-589`).
- A partial batch never becomes an archive sweep (`:1078-1080`).
- A zero-match read proves no landing only when that read is authoritative (`:1076-1077`,
  point 8). GitHub's lagging list (#808) is why the engine never treats it as
  authoritative, and so never re-creates on its own.

### Stage 1 steps

1. Set up decisions 1–3, and record:
   - `$O`'s `197a242` check, the fixture sha and its file hashes, and `$K`'s
     `origin/main`;
   - the fake's hash and `command -v gh`;
   - the real `gh`'s not-logged-in output.
2. **Baseline:** in `$S` at `197a242`, before the fixture commit, run
   `uv run --with pytest --with pyyaml pytest -q -p no:cacheprovider
   scripts/tests/test_triage_*.py scripts/tests/test_finalize_triage.py` with
   `--basetemp "$D/pytest-tmp"` and a raised timeout. It runs before the fixture because
   the fixture changes the tracker project the tests read. It is a focused baseline, not
   `make test`, because no kit file changes.
3. Write `$E/interpose.py`, `$E/harness.py`, `$E/fake/gh` and `$E/predictions.json`, which
   encodes the tables above. Record their SHA-256 in `$E/SHA256SUMS` **before the first
   cut**.
4. For each case in table order, retain for every step:
   - argv, context, exit status, stdout, stderr and timing;
   - `lstat` and SHA-256 snapshots of the case root before and after the step;
   - the fake log, for family K;
   - the kill or stop evidence from decision 4.

   Compare each step with `predictions.json` field by field.
5. Write `$E/RESULTS.md`, with one row per case step: predicted, observed, match. Seal
   `$E/EVIDENCE-SHA256SUMS`.
6. **Stop and present.**
   - A divergence other than those predicted for F-1 and F-2 is a finding. It is recorded
     but not repaired, and independent cases continue.
   - Filing a finding and repairing one are each separate decisions.
   - Removing `$D` is a separate cleanup for Topi to authorize.

### Stage 1 excluded

- Any agent run, any real forge or tracker call, any notification, and any live mode
  outside `$R`.
- Any kit code, test, doc or config change, and any PR. The fixture commit exists only in
  `$O`.
- Finalization past the refusal in K-U: branch, commit, push, PR and merge.
- `retire-terminal-invalid-state`. Stage L's L0 exercised it live on 2026-09-25 against
  real LLM-only state, and #858's tests cover the engine layout.
- Concurrent `recover` processes racing on one stale gate. The stale-gate routes mutate
  without holding a gate and rely on exclusive creation, which this package does not
  exercise.
- A mid-quarantine kill of the gate *after* the restart receipt in the invalid-state
  route. The receipt at the state path has one link, so it is V-QMID's mechanism
  (point 4).
- Any claim that a synthetic kill establishes behaviour in the field.

### Stage 1 stops

Keep the checkpoint and propose a bounded amendment on any of these:

- `$D` or `$E` already exists;
- `$O` lacks `197a242`, or a fixture or clone check fails;
- `gh` does not resolve to the fake, or the real `gh` is logged in;
- the fake log shows a form beyond the one permitted addition;
- the baseline suite fails;
- a kill or stop cannot be confirmed;
- a difference on any surface decision 7 checks, which stops the whole package.

**Stage 1 approval wording:** "I approve PHASE5-D-TRIAGE-RECOVERY-01 Stage 1 as scoped:
the G, V, I, U, O, T and K recovery cases, run through the real triage entry points in a
new isolated clone of 197a242 plus one synthetic fixture commit, with a local bare origin,
a fake gh tracker and labelled SYNTHETIC-TEST-OPERATOR approvals, cutting owned processes
at the named storage calls and restarting fresh processes from durable files, with
results presented. No kit, config, real forge, real tracker, friction-log, notification
or control-checkout triage-state write."

## Decision A — the order of the run and the fixes

| Option | What it is | Trade-off |
|---|---|---|
| **A1 (recommended)** | Run Stage 1 now at `197a242`. V-ALIAS and O-CAPTURE are predicted divergences, and G0 and T-GATE carry F-3's detail. File F-1, F-2 and F-3, plus anything else Stage 1 finds, and fix them in **one** engine PR. Then **Stage 2** reruns, at the fixed sha, the families that pass through the changed code | The matrix shakes out every divergence before any fix is written, so the fixes are batched and the rerun happens once. The cost is a second, smaller run |
| A2 | File and fix F-1, F-2 and F-3 first. Then run Stage 1 once, at the fixed sha, with the affected cases predicted to pass | All the evidence is at one sha. But any further defect Stage 1 finds needs another fix-and-rerun cycle |

## Stage 2 — sketch for re-preparation after the fix (A1 only)

Stage 2 is not proposed for approval here. It reuses Stage 1's harness, fake and fixture
at the fixed sha, and reruns the families whose code the fix touches. On the fix sketched
below, those are:

- **V, I and U**, through `resume_state_action`;
- **O-CAPTURE**, through `_blocking_recovery`'s bundle routes;
- **T-INVALID**, whose first `test {}` leaves its own gate on disk (`engine.py:1812-1821`)
  and whose approval runs through the same bundle route and `resume_state_action`;
- **K-L and K-U**, whose recovery runs through V's route.

V-ALIAS and O-CAPTURE are then predicted to pass. G, T-HELD and T-GATE do not change
unless the fix reaches `resume_gate_only`, `test_gate_state_plan` or
`persist_test_gate_held`. If F-3 is fixed in the same PR, G0 and T-GATE rerun too.

## Findings from preparation

These are for Topi to decide whether to file. Nothing has been filed. The draft payloads
below are for approval as written, or for editing.

**F-1: state-present recovery quarantines only the primary gate name.**

- **Mechanism.** `resume_state_action` calls `_quarantine` on `store.gate_path` alone
  (`recovery.py:738`, `:763`). Its gate-only counterpart quarantines every recorded
  same-inode name (`recovery.py:223`, `:244`). The workflow's `release-valid-state` and
  `release-restart-receipt` rows say "quarantine only every unchanged proven-stale gate
  name" (`triage-friction-log.md:897`, `:901`).
- **Consequence.** A process killed between the gate's `link` and its temporary's
  `unlink` leaves a same-inode alias. After an approved valid- or invalid-state recovery,
  that alias shares the quarantine name's inode, at `links 2`. Every later acquisition
  then refuses it (`gate.py:137`), and `recover` finds no gate.
- **Evidence.** The mode has no engine route out. P1 reproduces it.

Draft issue:

- **Title:** "Triage state-present recovery quarantines only the primary gate name, so a
  leftover same-inode gate temporary wedges the mode"
- **Labels:** `bug`, `robustness`, `P3`.
- **Body:** the mechanism, the consequence and P1's steps as above, and the fix direction:
  carry the capture's alias observations into the state-present quarantine, as the
  gate-only route does.

**F-2: a state-present capture or prepared bundle is acted on without proving its owner
dead.**

- **Mechanism.** `_blocking_recovery`'s bundle routes (`engine.py:332-345`) and
  `resume_state_action` check no owner status. A capture published by an ungated
  `recover` binds that invocation's own gate, and the gate stays on disk after it returns.
- **Consequence.** While that process is still alive, a second `recover` plans and, once
  approved, quarantines the live owner's gate and the state. The workflow requires "exact
  termination proof" for the owned-now-stale case, and stops otherwise
  (`triage-friction-log.md:767-771`).
- **Spec gap.** The action core also carries no gate disposition or owner binding, which
  the workflow lists among its fields (`triage-friction-log.md:846-848`).
- **Evidence.** P2 reproduces it with a `SIGSTOP`ped owner.

Draft issue:

- **Title:** "Triage recover acts on a state-present capture or prepared bundle without
  proving the gate owner dead"
- **Labels:** `bug`, `robustness`, `P2`.
- **Body:** the mechanism, the consequence and P2's steps as above, and the fix direction:
  require `owner_status == "terminated"` for the captured gate before planning from, or
  acting on, a state-present bundle.

**F-3 (candidate, found by the preparation check): the terminal gate-only receipt is
reported under the wrong cause.**

- **Mechanism.** Every entry `run()` sends past a successful gate acquisition first
  validates the gate-only receipt through `_prepared_gate_only_bundle`
  (`engine.py:1755`). That function compares whatever sits at the gate path with the
  receipt's `recovery_gate_record` (`engine.py:297-299`), and there it finds the caller's
  own, freshly acquired gate.
- **Consequence.** `new`, `resume`, `recover` and `test` over a released gate-only
  receipt report "gate-only held receipt replacement gate changed". The branch meant to
  report "gate-only-operator-held" (`engine.py:1756-1758`) is unreachable.
- **Why it is not a safety defect.** The outcome is still `operator-held`, the receipt is
  kept and no draft starts, so the workflow's row (`triage-friction-log.md:169`) holds.
  An operator reading the detail is sent looking for a gate change that did not happen.
- **Evidence.** The preparation check's probe, cases G0, G-ALIAS and T-GATE.

Draft issue:

- **Title:** "A released gate-only triage receipt reports 'replacement gate changed'
  because the entry's own gate is compared with the receipt's recorded gate"
- **Labels:** `bug`, `P3`.
- **Body:** the mechanism and consequence above, and the fix direction: skip the gate
  comparison when the gate at the path is the caller's own lease, or compare before
  acquiring.

**Related, not new:**

- #859 stays open. It covers `recover` judging a completed state valid on
  `canonical_state` alone. Whether other phases share that gap was not probed.
- #425 stays open.

## Already established elsewhere, and not repeated

- **Real-service ambiguity reconciled by read-back.** Stage L's Session A, on 2026-09-25,
  recorded #802's create as `ambiguous`, because the list lagged. A resume then reconciled
  it by marker read-back to `ambiguous-response-then-exact-read-back`, with no duplicate
  (#808).
  - That was a lagging list, not a crash. Family K does not replace it, and it does not
    replace family K.
- **`retire-terminal-invalid-state` on real state**: Stage L's L0.
- **Unit-level cutpoint coverage.** `scripts/tests/test_triage_engine.py` and
  `test_triage_recovery.py` drive fresh-process restarts at function-boundary cutpoints
  with injected providers. They end the owner with `terminate()`. This package adds:
  - the real CLI and approval-context channel;
  - the real GitHub adapter against a fake `gh`;
  - `SIGKILL` at individual storage calls;
  - owner proof by real PID and process start.

## Not established by this package

- Any real-service ambiguity from a crash. Under the fake tracker it stays residual, as it
  did for systemize.
- Concurrent recovery races.
- Scheduled or worktree-based runners, and any Codex-runtime run of these routes.
- Notification-thread approval. The CLI has no notification provider (#198).
- Any field installation.

## Preparation check

A fresh subagent with no part in the drafting read the first draft against the code at
`197a242`, read-only, on 2026-09-29.

**Its probe.** It ran `uv run --with pyyaml python3 probe.py` in a scratchpad directory.
Each step was a fresh child process calling the engine's `run()`, with the decision-4
storage-call cut wrapped around `os.link`, `os.unlink` and `os.replace`. Each case had:

- a local bare `origin`;
- the synthetic `tracker.project_name`;
- a fake `gh` first on `PATH`.

It covered every case in the tables. Its probe, child, fake `gh` and output are retained
under `state/review-evidence/phase5-d-triage-recovery-prep-20260929/prepcheck/`.

**It confirmed**, by that probe unless noted:

- the grounding reads it could re-run locally. It made no `gh` calls, so the protected-head
  and CI reads were not re-run;
- points 1–9 and their citations, apart from the corrections below;
- that P1 and P2 match `probe-output.json`, and that `SHA256SUMS` matches the files it
  lists;
- every case's detail, outcome and post-cut artifacts, apart from G0's and T-GATE's last
  step and I-QMID;
- that every cut spec lands where the tables say, with `nth 1` correct throughout. No
  earlier matching call happens in any of those processes, including `atomic_replace`'s
  cleanup unlink and the failed first gate acquisition;
- that a local-path origin works for `repository_identity`, `new_run_identity` and
  `_observe_protected_head`;
- that the underscore project name passes the adapter's check and still read-back
  matches, since K-L verified;
- K-U's finalize refusal, with no worktree and `$O` still holding only `main`;
- that F-1 and F-2 diverge from the workflow and are not intended behaviour;
- that the terminal holds are workflow-conformant.

**Its corrections, folded in above:**

- **G0 and T-GATE:** the last step's detail. That is F-3.
- **I-QMID:** the detail, and point 4's split between a gate and the state.
- **G-PREP:** the intent claim, which moved to G-INTENT.
- **The `STOP` check:** `Ts` rather than `T`, and the `SIGCONT`/`SIGKILL` cleanup.
- **Decision 7:**
  - `lstat`-only listing of `state/triage/`;
  - the empty `$K` status;
  - the named surfaces.
- **The origin:** cloned from the control checkout, with no network call and no dependence
  on GitHub's `main`, and pushed with `+HEAD:refs/heads/main`.
- **The fake `gh`:** a single sealed source, and its executing copy.
- **Stage 2:** T-INVALID added to the rerun set.
- **O-CAPTURE:** where the divergence actually shows, and the owner's JSON output.
- **Unstamped counts and outside-state phrasing.**
- **Citations:**
  - `owner_status`'s other `uncertain` branches;
  - `storage.py:193-195`;
  - `engine.py:1738-1740`;
  - `triage-friction-log.md:846-848`;
  - `create`'s post-`POST` retry.
- **O-UNCERTAIN:** the edit's canonical form.
- **P2's write-up:** it ran in-process and used a monkeypatch. The check reproduced F-2
  with a storage-call cut.
- **K-U:** the workflow citations for its hold.
- **Finalization:** no case may pass `sweep_ids` on a local-path origin.
