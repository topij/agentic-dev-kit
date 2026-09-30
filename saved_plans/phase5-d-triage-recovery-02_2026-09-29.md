# Phase 5 D — PHASE5-D-TRIAGE-RECOVERY-02 (Stage 2) packet

**Stage 2 of the D-TRIAGE-RECOVERY row, under Decision A1.** Stage 1 is
[PHASE5-D-TRIAGE-RECOVERY-01](phase5-d-triage-recovery_2026-09-29.md) (SHA-256
`6f27d9c6a4fdc6ecbc9dcc8f7dffecd63286e8fc6905ca9e2200ad55b77f6e18`). It ran at `197a242`
and found F-1, F-2 and F-3, which were filed as #862, #863 and #864. [#865](https://github.com/topij/agentic-dev-kit/pull/865)
fixed all three and merged as `b13abb3`. This package reruns the recovery matrix at
`b13abb3`. Topi owns scope changes and the acceptance decision.

**How this package is approved.** Topi could not review it before it ran. On 2026-09-29
they replied to a session-start briefing that recommended "prepare the D-TRIAGE-RECOVERY
Stage 2 packet, then run it once you approve". Their reply was "Let's do it. I'm going
to sleep so run the session autonomously based on the plan." The run's `APPROVAL.md`
quotes that reply and says how the cockpit read it:

- It covers this packet as scoped: synthetic cases in a new isolated clone, under Stage
  1's exclusions.
- It covers nothing Stage 1's approval did not. There is no kit, config, real-forge,
  real-tracker, friction-log, notification or control-checkout triage-state write.
- It authorizes no engine fix and no cleanup of either workspace. A divergence is
  recorded and presented, as in Stage 1.
- Tracker filing came later, in Topi's next message of the same session: "You can file
  the tickets as needed". That covers issue-shaped findings from this session. Each is
  searched for first and read back after filing. It does not cover engine fixes, merges
  or cleanup.

Everything this package produces is **synthetic evidence, labelled as synthetic**.

## Why the whole matrix, not only A1's "affected cases"

Stage 1's sketch said Stage 2 would rerun V, I and U, O-CAPTURE, T-INVALID, K-L and K-U,
plus G0 and T-GATE if F-3 was fixed in the same PR. #865 reaches more than that sketch
assumed:

- F-3 was fixed in the same PR, so G0 and T-GATE rerun.
- F-1's fix also changed the order in which the **gate-only** route quarantines names
  (aliases first, `recovery.py:101-114`). So every G case's approval now passes through
  changed code, and G-ALIAS is the one whose result could differ.

That leaves four cases that no changed line reaches: O-ACTIVE, O-UNCERTAIN, T-HELD and
I-HELD (*Reach*, below). They add a few seconds to a run whose Stage 1 cases took about
a minute. Rerunning them as **controls** gives the whole row's evidence at one sha, and
shows that the harness and environment have not drifted. Their predictions are
unchanged from Stage 1.

Three cases are **added** for cutpoints #865 created, and O-CAPTURE is **extended**.
Both are disclosed below as additions to Stage 1's scope. They are the same kind of
synthetic case under the same containment.

## Grounding reads

All reads were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-29.

- **Protected head.** `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha`
  printed `7a75f7172568e1bf2831cc16fc121c1b444643d9` at 2026-09-29T19:30:54Z.
  `gh run list --branch main --event push --limit 2` read:
  - run `36618414407`, `completed` / `success`, for `7a75f71`;
  - run `36614101523`, `completed` / `success`, for `b13abb3`.

  The control checkout's `HEAD` and `origin/main` both read `7a75f71`.
- **Why `b13abb3` rather than `7a75f71`.** `git log --oneline b13abb3..7a75f71 --
  scripts config` printed nothing. `7a75f71` (#868) changed only
  `docs/kit-handoff.md` and `docs/kit-handoff-history.md`. So the engine, its CLI and the
  config are identical at the two shas. `b13abb3` is the fix's own merge, and the
  handoff names it.
- **What changed since Stage 1's sha.** `git diff --stat 197a242 b13abb3 -- config/
  scripts/lib/triage/ scripts/triage_friction_log.py scripts/finalize_triage.py
  scripts/lib/kitconfig.py scripts/lib/state_paths` lists only
  `scripts/lib/triage/engine.py` and `scripts/lib/triage/recovery.py`. So Stage 1's
  config reading holds unchanged: tracker backend `github-issues`, the three
  `triage.*` path patterns, and an overlay that a clone does not have.
- **Tools.** `uv --version` printed `uv 0.12.3`. `uv run --with pyyaml python3` reported
  Python `3.14.7`. `gh --version` printed `2.97.0`. `git --version` printed
  `2.50.1 (Apple Git-155)`. These are the versions Stage 1 recorded.
- **The control checkout's triage state directory.** A Python `os.scandir` over
  `state/triage/`, `stat(follow_symlinks=False)` only, listed no `.lock` name. It listed
  one gate quarantine name, one recovery bundle, the live state, retired `.completed-*`
  files and frozen snapshots, each with one link. Nothing there was opened. **This
  package must not read, write or rename anything there.**
- **Hostname.** `hostname` printed `Topis-MacBook-Pro.local`, and so did Python's
  `socket.gethostname()`. #867 records that `owner_status` reads a changed hostname as
  `uncertain`, and that `hostname` changed during Stage 1's session. Every step record in
  this run carries `socket.gethostname()`. So a hostname change mid-run would show as a
  cause, rather than as an unexplained hold.

## What #865 changed, read at `b13abb3`

1. **Owner proof for state-present bundles (F-2, #863).** `_blocking_recovery` calls
   `_require_terminated_owner(gate_raw)` for a `state-present-capture` or
   `state-present-prepared` bundle, before planning from it or acting on it
   (`engine.py:350-354`). That function validates the record's shape only
   (`validate_record(record)`, with no repository or config identity), and holds
   `blocking gate owner is active or uncertain` unless `owner_status` returns
   `terminated` (`engine.py:307-321`).
   - Other bundle kinds do not get the check: `state-present-held`,
     `state-present-test-gate-held`, and the gate-only kinds.
   - The check runs after the state read at `engine.py:333`. That read refuses a state
     with two links, so I-QMID's restarts never reach it.
2. **Every gate name is quarantined (F-1, #862).** `resume_state_action` calls
   `_quarantine_group(_old_gate_quarantine_items(store, core), gate_raw)` in both
   actions (`recovery.py:746`, `:769`). That quarantines each recorded alias, then the
   gate. The invalid-state route used to be guarded by `if store.gate_path.exists()`.
   Now `_quarantine_group` accepts a name whose source is gone only if its quarantine
   target holds the approved bytes and inode (`recovery.py:89-90`).
   - `resume_gate_only` uses the same item list (`recovery.py:227`). The order there
     changed from gate-first to aliases-first.
   - The docstring gives the reason (`recovery.py:102-110`): a stop between two moves
     then leaves the primary gate in place, so `recover` finds it and resumes.
   - `_quarantine_group` then checks that every quarantined name has exactly as many
     links as there were items (`recovery.py:96-97`).
   - Its inner call changed from `quarantine_inode(...)` to
     `Observation(**_quarantine(...))` (`recovery.py:82`). `_quarantine` is
     `quarantine_inode(...).as_dict()` (`:65-66`), so that is a round trip with no
     behavioural effect.
3. **A released gate-only receipt reports itself (F-3, #864).** `run()` passes its own
   lease's bytes, `own_gate_raw=lease.verify()`, to `_prepared_gate_only_bundle`
   (`engine.py:1781`). That function accepts those bytes at the gate path
   (`engine.py:300-303`). So `new`, `resume`, `recover` and `test` over a released
   `gate-only-operator-held` receipt reach the branch that answers `detail:
   gate-only-operator-held` and `resume_action: preserve the terminal gate-only evidence`
   (`engine.py:1782-1784`).
4. **Storage behaviour the new cases rely on:**
   - `quarantine_inode` compares the source's whole `Observation` with the approved one
     (`storage.py:193-195`). That covers path, device, inode, mode, links, size,
     `mtime_ns` and digest, but not `ctime` (`storage.py:21-31`, `:175-182`).
   - A link or unlink of another name changes the inode's link count, but not its
     `mtime`. So once an alias has moved, the gate's observation still equals the
     captured one exactly when its link count is back to the captured value.
   - `exclusive_create` raises `FileExistsError` before creating a temporary only when
     the published name has one link (`storage.py:291-294`). A gate with two links is
     different: a failed acquisition over it creates its temporary, fails the `link`, and
     unlinks the temporary in its `finally` (`storage.py:352-358`). That unlink matches
     `.triage-pipeline-gate_live.lock.*.tmp`. So neither new mid-quarantine cut
     (`KGQ-before`) matches on that glob; each matches on the primary gate's quarantine
     `link` instead. I-ALIAS's `KG-alias` cut is Stage 1's, taken over an absent gate,
     where no failed acquisition occurs.

## Reach

Each case is listed under every changed path its steps pass through.

| Changed path | Cases (steps) |
|---|---|
| (1) owner proof | V0 (plan2, approve), V-PREP (approve-cut, restart), V-QMID (approve-cut, restart1, restart2), V-QDONE (approve-cut), V-ALIAS (approve), V-ALIAS-MID (approve-cut, restart), I0 (plan2, approve), I-PREP (approve-cut, restart), I-QMID (approve-cut only), I-QDONE (approve-cut, restart), I-RCPT (approve-cut, restart), I-ALIAS (approve), U0 (plan, approve), U-HELD (approve), O-CAPTURE (second-recover, recover-after, approve-after), T-INVALID (approve), K-L (approve), K-U (approve) |
| (2) state-present quarantine group | every step above that runs `resume_state_action`, except I-QMID, whose cut lands before the group |
| (2) gate-only item order | G0 (approve), G-PREP (restart), G-INTENT (restart), G-QMID, G-QDONE (restart), G-REPL, G-RCPT (approve-cut, restart), G-ALIAS (approve), G-ALIAS-MID (approve-cut, restart), T-GATE (approve) |
| (3) own lease accepted | G0 (new-after, resume-after, recover-after), G-QDONE (resume and restart, where the intent branch leaves it unused), G-ALIAS (new-after), G-ALIAS-MID (new-after), T-GATE (test-after) |
| **none (controls)** | O-ACTIVE, O-UNCERTAIN, T-HELD, I-HELD |

## Decisions bound by Stage 2

Stage 1's decisions 1–7 apply with these substitutions, and with nothing else changed:

1. **Workspace.** `D=/private/tmp/adk-phase5-d-triage-recovery-02`, with `O`, `S`, `K`,
   `F` and `R` under it as in Stage 1, and
   `E=/Users/topi/Coding/agentic-dev-kit/state/review-evidence/phase5-d-triage-recovery-02`.
   - `$O` is a `git clone --bare --no-hardlinks --single-branch --branch main` of the
     control checkout. Stage 1 cloned every local branch. The control checkout now also
     carries the merged work branches of #865 and #868. Cloning them would put three
     refs in `$O`, and K-U's sealed `origin_refs` would then fail on the environment
     rather than on the engine. `git -C "$O" cat-file -e
     b13abb3d6de6edf0403f576a32fb8b3ff374bded^{commit}` must succeed.
   - `$S` is detached at `b13abb3`.
   - Stage 1's `$D` and `$E` are read-only inputs and are never written. `$D` of Stage 1
     is not used at all.
   - As in Stage 1, the cockpit creates `$E` to hold `APPROVAL.md` after checking that
     neither `$D` nor `$E` exists, and `harness.py setup` refuses an existing `$D`.
2. **Fixture commit.** It is Stage 1's two-file fixture, applied on `b13abb3` by the same
   harness code, with the tag `PHASE5-D-TRIAGE-RECOVERY-02` in the two entry titles and
   the commit message. The friction-log anchor `## 2026-09-28 — Backlog migrated`
   occurs once at `b13abb3` (`git show b13abb3:docs/kit-friction-log.md | grep -c`
   printed `1`). The two config lines the fixture replaces are at
   `config/dev-model.yaml:240-241` there.
3. **Containment, process model, synthetic inputs, restart rule, write containment:**
   as Stage 1 decisions 3–7. The harness's `control_surfaces()` excludes the new `$E`
   and still lists Stage 1's, which this package only reads. Stage 1's `$E` holds a
   `__pycache__/`, so nothing in this run imports from that directory.

### Harness changes from Stage 1

Stage 2's `harness.py`, `interpose.py`, `fake/gh` and `verify_summaries.py` are copies
of Stage 1's sealed files. `$E/REUSE-DIFF.txt` records `diff -u` of each against its
Stage 1 source. The only changes:

- **Constants:** `SHA`, `D`, `E` and `TAG`, and the module docstring's first line
  (`harness.py`); the tag string in `interpose.py`; and the tag in `fake/gh`'s
  docstring. The fake's behaviour is unchanged.
- **`setup()` clones `$O` single-branch**, for the reason in decision 1.
- **O-CAPTURE's script** follows the new table below.
- **The three new case scripts:** G-ALIAS-MID, V-ALIAS-MID and I-ALIAS, and the
  `KGQ_BEFORE` cut constant they share.
- **`resume_stopped` records a printed plan's digest**, as `engine()` already does, so
  that `plan_same_as` can name a continued owner's plan.
- **Every step record carries `hostname`**: `socket.gethostname()` taken when the step
  starts.
- **The results heading** reads Stage 2.

`verify_summaries.py` is byte-identical to Stage 1's. It reads `predictions.json` from
its own directory.

## Cases and predictions

Notation is Stage 1's. Additionally:

- `LALIASQ` is `.triage-pipeline-gate_live.lock.*.tmp.quarantine-*`, the alias's
  quarantine name.
- `KGQ-before` means an approval under `interpose.py --op link --match
  'triage-pipeline-gate_live.lock.quarantine-*' --when before --nth 1 --signal KILL`.
  That kills the approval after it has moved every alias and before it links the primary
  gate to its quarantine name.
- `GO_DONE+` means detail `gate-only-operator-held`, with the result's `resume_action`
  equal to `preserve the terminal gate-only evidence`.

**Unchanged from Stage 1, and predicted to match as Stage 1 did:**

- G-PREP, G-INTENT, G-QMID, G-QDONE, G-REPL and G-RCPT;
- V0, V-PREP, V-QMID and V-QDONE;
- I0, I-PREP, I-QMID, I-QDONE and I-RCPT;
- U0;
- O-ACTIVE and O-UNCERTAIN;
- T-HELD and T-INVALID;
- K-L and K-U.

I-HELD and U-HELD are unchanged except that their `invalidate` step's
`synthetic_invalidation` value is this package's tag.

**Changed predictions: the three fixed findings.** Stage 1's predicted divergences
become passes.

| Case | Steps changed | Stage 1 prediction | Stage 2 prediction |
|---|---|---|---|
| G0 | new-after, resume-after, recover-after | "gate-only held receipt replacement gate changed" (F-3) | `GO_DONE+`, bytes kept; new-after creates no frozen snapshot |
| G-ALIAS | new-after | same F-3 detail | `GO_DONE+`, bytes kept, no frozen snapshot |
| T-GATE | test-after | same F-3 detail | `GO_DONE+`, bytes kept, no test frozen snapshot |
| V-ALIAS | approve, resume-after, recover-after (and plan, whose added checks do not separate the engines) | approve left the alias beside the quarantine name; resume-after "orphaned gate temporary identity is ambiguous"; recover-after "blocking gate disappeared" (F-1) | **plan:** the capture bundle records one alias. **approve:** "resume"; no gate and no alias left; one `LGQ` and one `LALIASQ`, one inode, `links 2` each; bundle `state-present-prepared`. **resume-after:** "active session resumed", `awaiting-approval`, `normal-resume`, proposal digests unchanged. **recover-after:** "captured state is valid; recovery refused", bytes kept |
| O-CAPTURE | second-recover onward | second-recover planned from the stopped owner's capture; third-approve quarantined its gate while it read `Ts` (F-2) | See the table below |

**O-CAPTURE at `b13abb3`:** a live owner holds, and once that owner exits, the same
capture proceeds.

| Step | Predicted |
|---|---|
| aw-freeze, aw-analysis, invalidate, stop-cut | as Stage 1 |
| second-recover | "blocking gate owner is active or uncertain"; bytes kept; still one bundle; the stopped owner is alive and reads `T…` |
| continue | `SIGCONT`; the owner exits `0` with "invalid state captured before parse", action `abandon-invalid-state`; gate, state and bundle unchanged since stop-cut. The detail is no longer stale |
| recover-after | "state-present recovery action awaits exact approval", `abandon-invalid-state`, the same `action_core_digest` as the owner's printed plan; bytes kept; the gate's owner PID is dead |
| approve-after | "recovered-safe-to-restart"; gate gone; `LGQ` and `LSQ` present; the state quarantine's bytes equal the invalidated state's |
| new-after | "verified recovery receipt replaced by reserved new state", `reserved`, `live-receipt-restart` |

Only `second-recover` distinguishes `b13abb3` from `197a242`. The later steps show that
the same capture still completes once its owner is dead, which the old engine also did.

**Added cases, for the cutpoints #865 created**

| Case | Setup and cut | Predicted after the cut | Restart sequence → predicted |
|---|---|---|---|
| G-ALIAS-MID | `new {}` under `KG-alias`; `plan`; `approve` under `KGQ-before` | gate and `LALIASQ` sharing one inode, `links 2`; no alias; no `LGQ`; intent at the state path equal to the bundle's `intended_intent` | `recover {}` → `GO_DONE`: no gate and no alias left; one `LGQ` and one `LALIASQ`, one inode, `links 2`; the receipt's `quarantine_observations` holds two entries and binds the bundle; `new {}` → `GO_DONE+`, bytes kept, no frozen snapshot |
| V-ALIAS-MID | `AW`; `resume {}` under `KG-alias`; `plan`; `approve` under `KGQ-before` | gate and `LALIASQ` sharing one inode, `links 2`; no alias; no `LGQ`; bundle `state-present-prepared` | `recover {}` → "resume": no gate and no alias left; one `LGQ` and one `LALIASQ`, one inode, `links 2`; `resume {}` → "active session resumed", `normal-resume`, proposal digests unchanged |
| I-ALIAS | `AW`; abandonable invalidation; `resume {}` under `KG-alias`; `plan`; `approve` | (after the cut) gate plus alias, `links 2`; state unchanged since invalidation | `plan` → `abandon-invalid-state`, the capture records one alias; `approve` → "recovered-safe-to-restart": no gate and no alias left; one `LGQ` and one `LALIASQ`, one inode, `links 2`; the state quarantine's bytes equal the invalidated state's; `new {}` → "verified recovery receipt replaced by reserved new state", `live-receipt-restart` |

Why these three:

- **G-ALIAS-MID and V-ALIAS-MID** each test the aliases-first ordering's stated reason,
  in one route each. That reason is that a stop between moves leaves the primary gate,
  and `recover` resumes from there. Each rests on point 4: the gate's observation after
  the alias moved must equal the captured one.
  - The order itself is shown by `approve-cut`'s post-cut state: alias moved, gate not.
    "`recover` resumes a half-done group" is the pair `approve-cut` + `restart`.
  - G-ALIAS-MID's `restart` alone would pass on the old engine too. There, the
    gate-first order puts the kill before any move, so the restart quarantines both
    names from scratch. V-ALIAS-MID's `restart` does separate the engines, because the
    old state-present route leaves the alias.
- **I-ALIAS** exercises the invalid-state action's gate group with an alias. V-ALIAS
  covers only the valid-state action.

`predictions.json` encodes all these tables, with Stage 1's other rows copied
unchanged. **The sealing order differs from Stage 1's.** Stage 1 sealed its predictions
before any harness code existed. Here the draft harness existed first, and ran in the
preparation check's disposable workspaces, because running it was the check. The
predictions are sealed after this packet's last edit, before the checked files are
copied into `$E` and before `setup`. Nothing is edited in response to the real run.

## Stage 2 steps

1. Create `$E` and write `APPROVAL.md`, after checking that neither `$D` nor `$E`
   exists.
2. Write `gen_predictions.py`, then generate `predictions.json` and seal both in
   `SEAL-predictions.sha256`, together with this packet's hash and `APPROVAL.md`'s.
3. Copy the checked draft `harness.py`, `interpose.py`, `fake/gh` and
   `verify_summaries.py` from the prep directory into `$E`, and write `REUSE-DIFF.txt`
   against Stage 1's sealed sources.
4. Run `harness.py setup`:
   - the focused triage baseline in `$S` at `b13abb3`, before the fixture;
   - the fixture commit and `$K`;
   - the fake;
   - the containment probes.
5. Seal `interpose.py`, `harness.py`, `fake/gh`, `predictions.json`,
   `gen_predictions.py`, `APPROVAL.md` and `setup.json` in `SHA256SUMS`, before the
   first cut.
6. Run `harness.py run`, then `harness.py containment` and `harness.py results`, then
   `verify_summaries.py`.
7. Write `RESULTS.md` and seal `EVIDENCE-SHA256SUMS`. `RESULTS.md` quotes the
   containment verdict separately, because `verify_summaries.py` does not read it. If
   an owner-proof step holds unexpectedly, read the step record's `hostname` against
   the gate record's `host` before anything else (#867).
8. Stop and present. A divergence is a finding: it is recorded, not repaired, and
   independent cases continue.

Between `setup` and `containment`, nothing may create a file in the control checkout
outside `$E` and `state/`. `control_surfaces()` records `git status --porcelain`, so a
new untracked file there stops the package.

## Stage 2 stops

These are Stage 1's stops, with Stage 2's roots, plus one:

- a harness `KeyError` or unknown check on a step that Stage 1 ran identically. That
  would mean the copy drifted from its source, so the whole run stops for an amendment
  rather than continuing.

## Excluded

Stage 1's exclusions all apply. In addition:

- **A `state-present-prepared` bundle whose owner is alive.** Through the CLI, the only
  process that can write a prepared bundle over its own gate is an ungated `recover`
  (or, in test mode, `test`; `engine.py:1807-1828` and `:1831-1851`) that plans and
  approves in one invocation. Its approval would have to bind a capture
  digest that includes its own new gate, which no earlier invocation can print.
  #865's CHANGELOG entry describes the in-process form, which is held. This package
  does not construct it.
- **O-CAPTURE's test-mode twin.** `_blocking_recovery`'s owner check does not depend on
  the mode.

## Not established by this package

Everything Stage 1 lists, and:

- #867: a gate written under another hostname. O-UNCERTAIN's synthetic foreign host
  covers the refusal, not a real hostname change.
- Any `.tmp` gate name that an earlier recovery left behind. #865's CHANGELOG says the
  change does not move one.

## Preparation check

A fresh subagent that took no part in the drafting checked the first draft on
2026-09-29, against the code at `b13abb3`. Its report, with every command and quoted
output, is `state/review-evidence/phase5-d-triage-recovery-02-prep-20260929/prepcheck/REPORT.md`.
Its probe workspaces are `/private/tmp/adk-phase5-d-triage-recovery-02-prepcheck-b13`
and `-prepcheck-197a`.

**It confirmed:**

- every point under *What #865 changed* and its citations, apart from the nits below;
- the *Reach* table, including that the four controls reach no changed line;
- the *Excluded* claim;
- the grounding reads it could re-run locally;
- that the generator encodes the tables. Every unchanged row is identical to Stage 1's
  `predictions.json`, apart from the I-HELD and U-HELD tag;
- that the harness copies differ from Stage 1's sealed files only as listed.

**Its dry run of the draft at `b13abb3`** printed, from `verify_summaries.py`,
`cases 32 steps 215 problems [('K-U', ['mismatch'])]`. That mismatch was K-U
`finalize`'s `origin_refs`, from the environment (C1 below). Every other step matched,
every changed and added row included.

**Its counter-run of the same draft at `197a242`** mismatched only these:

- G0, G-ALIAS and T-GATE at their F-3 steps;
- V-ALIAS at approve, resume-after and recover-after;
- O-CAPTURE at second-recover;
- G-ALIAS-MID at approve-cut and new-after;
- V-ALIAS-MID at approve-cut, restart and resume-after;
- I-ALIAS at approve and new-after;
- the same environmental K-U row.

So the changed and added predictions separate the fixed engine from the old one, and no
unchanged row does.

**Its corrections, folded in above:**

- **C1 (a run-breaking fix).** `$O` is now cloned single-branch (decision 1 and
  *Harness changes*). The draft's full clone carried the control checkout's merged work
  branches into `$O`, and K-U's sealed `origin_refs` failed on them at both shas.
- **C2.** The packet hash goes into `gen_predictions.py` only after this packet's last
  edit, and then the predictions are regenerated and sealed.
- **C3 and C4.** The *Reach* table's steps for G-PREP, G-INTENT and G-QDONE.
- **C5.** The test-mode twin in *Excluded*.
- **C6.** Which new cut can match the gate-temporary glob.
- **C7.** Which steps actually separate the engines, in O-CAPTURE, V-ALIAS and *Why these
  three*.
- **C8 and C9.** Citation nits, and the complete lists of changes.

**Its note for Topi, outside this package.** The shared workflow's row for "a valid
ordinary non-held, malformed, foreign, or digest-mismatched current-gate recovery
bundle" says "After proving owner termination" (`triage-friction-log.md:165`). But
`_blocking_recovery`'s held-bundle and other-kind branches check no owner status
(`engine.py:355-357`, `:372`). Those branches mutate nothing, so the gap is in the
reported cause, not in safety. I-HELD, U-HELD and T-HELD pass through it. It is not a
Stage 2 defect, and it is recorded for the session's friction routing.
