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

## Session — 2026-09-30 (Phase 6 planned; #857 and #874 shipped from a headless lane, in Claude Code)

**Shipped.**

- PR #882, squash `12629ab`, from the headless Claude lane `triage-857-874` (merge class
  operator). It pins finalize's commit-step worktree re-check with a test (#857), and
  corrects the *Completed-state retirement* doctrine, with kill-cutpoint tests (#874).
  #883 carries the doctrine points the review rounds left open. #857 and #874 closed on
  merge.
- PR #881, squash `7290e31`: the parity plan's *Phase 6* section, ordered with an owner
  for each item, and the Phase 6 workstream.

**Filed.** Each was filed on the operator's approval of its exact text and read back
identical:

- #875, #876, #877, #878, #879 and #880: owners for Phase 6 items;
- #883: residual precision points from #882's panel;
- #884: the suite fails under `FORCE_COLOR`;
- #885: a lane's Read tool is denied outside its worktree.

Occurrence comments went on #628 (a lane's inline `gh pr create --body` was denied) and
on #852 (the receipt workaround below).

**Review.** CodeRabbit's auto-review is off, so the fallback panel reviewed both PRs.
Round 1's receipt was recorded at its reviewed head, with its findings in the
disposition, before the fix round was pushed. Each fix round then composed a delta
receipt on the one before it. #882 took the dual form throughout, because it changes
recovery doctrine. Its residual LOW findings went to #883 under the blast-radius
stopping rule.

**Lane.** The lane's work completed, but its receipt terminalized `failed` on permission
denials the work did not need. The receipt listed them, until `dev_session.sh rm`
removed its session directory:

- a Read of a gitignored file outside its worktree, which the cockpit's brief had pointed
  it at;
- a Write outside the worktree;
- an inline `gh pr create --body`, after which it fell back to `--body-file`.

`dev_session.sh rm triage-857-874` removed the lane after the merge.

**Verified.** `env -u FORCE_COLOR make test` at each PR's merged head, on 2026-09-30:

- #881 at `adb6324`, in `/Users/topi/Coding/agentic-dev-kit`: `3739 passed, 1 skipped,
  3 warnings in 679.30s`;
- #882 at `425dbfe`, in the lane worktree `/Users/topi/Coding/dev-model-sessions/triage-857-874/wt`:
  `3745 passed, 1 skipped, 3 warnings in 578.74s`.

The `env -u` form is because the shell began exporting `FORCE_COLOR=3` partway through
the session (#884).

**Held for the operator:** whether the retirement doctrine should prescribe removing the
retired name by hand to leave the two-link state.

______________________________________________________________________

## Session — 2026-09-30 (Phase 5 exit declared, in Claude Code)

**Declared.** Topi declared Phase 5 complete under PHASE5-E-AUDIT-01
(`saved_plans/phase5-e-audit_2026-09-30.md`) by answering "Declare, approve all
(Recommended)" to a question that quoted the packet's declaration wording, which that
answer adopts:

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

The declaration names its acceptance amendments; the packet's residual register owns
each residual's carrier. Topi took E-1 to E-6 as the packet recommends. Each answer is
recorded verbatim in `state/review-evidence/phase5-e-audit-20260930/DECISIONS.md`
(gitignored).

**Recorded.** The parity plan's Phase 5 items are checked (payload P-1), and the
`saved_plans/phase5-*` packet markdowns are committed (E-5 option A). Tracker, each
read back identical to its payload:

- P-2 on #243, which stays open:
  [issuecomment-5906532047](https://github.com/topij/agentic-dev-kit/issues/243#issuecomment-5906532047);
- P-3a on #7, then set completed:
  [issuecomment-5906532328](https://github.com/topij/agentic-dev-kit/issues/7#issuecomment-5906532328);
- P-3b on #748, then set completed:
  [issuecomment-5906532589](https://github.com/topij/agentic-dev-kit/issues/748#issuecomment-5906532589);
- P-6 filed as [#872](https://github.com/topij/agentic-dev-kit/issues/872).

**Not established:** a third full check of the packet against its evidence records.
Before the decisions, the packet's SHA-256, P-1's anchors, the facts P-3a and P-3b
state and the named issues' states were re-read from the repository root at `3bcb3a3`,
and matched.

Closed workstream Phase 5 exit: the exit is declared.

______________________________________________________________________

## Session — 2026-09-30 (Phase 5 E audit packet, in Claude Code)

**Accepted.** The operator accepted D-TRIAGE-RECOVERY: "I accept the Stage 1 and Stage 2
RESULTS.md files." `ACCEPTANCE.md` beside each run's `RESULTS.md` records it. Each run's
*Not established* list goes to the E audit.

**Packet.** `saved_plans/phase5-e-audit_2026-09-30.md` is local and not committed, like
the D packets. It is milestone E's audit, and it approves nothing. It contains:

- an exit ledger over every Stage A row and every D package;
- a custody check of the D evidence;
- the operator's decisions E-1 to E-7, each with a recommendation;
- exact payloads for the parity plan and the tracker.

Its grounding reads and `collect.sh` are in
`state/review-evidence/phase5-e-audit-20260930/` (gitignored). Fresh subagents
checked successive drafts against the records, and the packet's *Preparation check*
lists what each round changed.

**What the audit found.** The packet owns the detail.

- **Acceptances on record.** Besides D-TRIAGE-RECOVERY, the acceptances are:
  - the 2026-09-23 decisions in `phase5-d-systemize-boundaries-01/APPROVAL.md`: the
    systemize friction and tracker no-write amendment, and the cap, batching,
    competing-cache and hostile-target rows as synthetic;
  - RECOVERY-01's run P as the pre-approval cutpoint's evidence;
  - milestone B's accepted limits.

  No acceptance covers B or C as a whole, or the other D rows. The packet asks for
  those under E-1, and each gap it names is an amendment the declaration names.
- **Scope decisions.** The packet's searches found no recorded decision on additional
  client coverage. Also open as scope decisions (E-2):
  - notification approval provenance (#198) and the triage notification route;
  - scheduling and worktree runners, beside #747;
  - real-service crash ambiguity (#794) and concurrent systemize runs (#792);
  - engine installation in an adopter.
- **Missing sealed fixtures.** The `fixtures/` files that the manifests in
  `phase5-d-systemize-recovery-01/` and `phase5-d-systemize-boundaries-01/` bind are
  gone. Both directories' modification times fall in the window of the 2026-09-29
  cleanup that #861 describes. That the cleanup removed them is an inference from those
  times (E-3).
- **A wrong earlier judgment.** The judgment on #7 in the history's 2026-09-23
  D-SYSTEMIZE-RECOVERY packet block is wrong. #769 shipped #7's fetch/digest pair
  behind systemize's own forge boundary, not #6's. The threshold and operator-login
  keys predate #769, which added `heartbeat_job` and `heartbeat_pattern`.
  `nightly_digest.py` was not shipped. E-4 carries the corrected facts.

**Filed this session**, on the operator's approval of the exact revised text: an
occurrence comment on #861
([issuecomment-5905162617](https://github.com/topij/agentic-dev-kit/issues/861#issuecomment-5905162617)),
for the missing fixtures. It was read back identical.

**Not established:**

- a custody re-verification of the B and C namespaces' binding JSONs;
- whether that cleanup removed any other manifest-bound file, or removed these at all.

______________________________________________________________________

## Session — 2026-09-29 (Phase 5 D-TRIAGE-RECOVERY Stage 2, run autonomously, in Claude Code)

**Mandate.** The operator went to sleep and asked for the session to run autonomously
"based on the plan". Later they said "You can file the tickets as needed". The run's
`APPROVAL.md` quotes both messages and says how they were read. Nothing was merged.

**Packet.** `saved_plans/phase5-d-triage-recovery-02_2026-09-29.md` is local and not
committed, like the other D packets. It reruns the whole Stage 1 matrix at `b13abb3`;
`7a75f71` changes no engine or config file. The packet:

- names the cases that #865's changes reach, and reruns O-ACTIVE, O-UNCERTAIN, T-HELD
  and I-HELD as controls;
- extends O-CAPTURE;
- adds G-ALIAS-MID, V-ALIAS-MID and I-ALIAS for the cutpoints #865 created.

**Preparation check.** A fresh subagent checked the draft, dry-ran it at `b13abb3` and
counter-ran it at `197a242`. Its report is
`state/review-evidence/phase5-d-triage-recovery-02-prep-20260929/prepcheck/REPORT.md`.
The correction that would have broken the run concerned the fake origin:

- The harness's bare clone copied every local branch, so the control checkout's merged
  work branches reached the fake origin and failed K-U's `origin_refs`.
- The origin is now cloned single-branch.

**Stage 2 (synthetic).** The evidence is in
`state/review-evidence/phase5-d-triage-recovery-02/` (gitignored), and its `RESULTS.md`
owns the outcomes. The runs below were in that directory, over the engine at `b13abb3`
plus fixture commit `fa61085`, on 2026-09-29.

- `python3 verify_summaries.py` printed `cases 32 steps 215 problems []`.
- `harness.py containment` printed `true` for `git_status`, `state_listing` and
  `state_triage_lstat`.
- In that run, F-1, F-2 and F-3 passed through the CLI, in V-ALIAS, O-CAPTURE, and G0,
  G-ALIAS and T-GATE.
- The preparation check counter-ran the same predictions at `197a242`. It failed the
  changed and added rows' distinguishing steps and K-U's environmental `origin_refs`,
  and no other row. Its report quotes the `verify_summaries.py` line.

**Filed this session**, under the operator's go-ahead:

- #869: `recover` reports a held or other current-gate recovery bundle without proving
  the gate owner dead. It was reproduced with a stopped owner. It fits *Triage engine
  hardening*, whose entry this session left alone.
- An occurrence comment on #861: the harness's containment listing of all of `state/`
  grows with `state/`.

**Not established:** Stage 1's list, except the recovery evidence at the fixed engine
that it left to Stage 2, which this run supplies. Also not established:

- a `state-present-prepared` bundle whose owner is alive, which the CLI cannot reach;
- a real hostname change (#867);
- a `.tmp` gate name left by an earlier recovery.

**Left for the operator:**

- the row's acceptance;
- removing `/private/tmp/adk-phase5-d-triage-recovery-02` and its `-prepcheck-b13` and
  `-prepcheck-197a` siblings, which this session did not attempt;
- deleting the control checkout's local branches of the merged #865 and #868,
  `fix/triage-recovery-owner-alias` and `chore/update-handoff-2026-09-29-triage-recovery`.

______________________________________________________________________

## Session — 2026-09-29 (Phase 5 D-TRIAGE-RECOVERY packet and Stage 1, recovery fixes, in Claude Code)

**Packet.** `saved_plans/phase5-d-triage-recovery_2026-09-29.md` is local and not committed, like the other D packets. It scopes the D-TRIAGE-RECOVERY row as engine-level cases, driven through the real `recover` and `test` CLI, with no agent run.

- A fresh subagent checked the draft against the code, and its corrections are folded in.
- Preparation found F-1, F-2 and F-3. They were filed as #862, #863 and #864 on the operator's approval of the exact payloads.
- The operator chose Decision A1: run Stage 1 at `197a242`, fix, then rerun the affected cases as Stage 2.

**Stage 1 (synthetic).** It ran in a disposable workspace under `/private/tmp`. The harness, the fixture's setup and the fake `gh` are with the evidence in `state/review-evidence/phase5-d-triage-recovery-01/` (gitignored). `RESULTS.md` owns the outcomes, and `APPROVAL.md` holds the approval and the run's disclosures. `python3 verify_summaries.py` there, over the engine at `197a242` plus fixture commit `f4f261f`, printed `problems []` on 2026-09-29. So every predicted step matched, including the predicted F-1, F-2 and F-3 divergences.

**Shipped.** [#865](https://github.com/topij/agentic-dev-kit/pull/865) merged as `b13abb3`, a squash of its reviewed head `a904080` with the same tree. #862, #863 and #864 are closed. Recovery now:

- acts on a state-present bundle only once its gate owner is proven dead, by liveness alone;
- quarantines every same-inode gate name, aliases first, in the gate-only route too;
- reports a released gate-only receipt as itself.

An ungated plan followed by an approval must now run as separate processes, as the CLI does.

**Decided.** The action core gets no gate-disposition field. The owner is bound through `old_gate_digest`, and ownership is proven at act time; #865's body gives the reasoning.

**Review.** CodeRabbit skipped #865, so the fallback panel ran two full rounds. Round 1 found a regression: the owner check re-validated the current config fingerprint, which held an approved resume after any config change. It was fixed in the PR, and #865's disposition comments own the findings.

**Filed this session:**

- #862, #863 and #864;
- #867: `owner_status` reads a changed hostname as `uncertain`. `hostname` changed during this session.

Occurrence comments went on #643 and #835.

**Verification.** In `/Users/topi/Coding/agentic-dev-kit`, `make test` at `a9040803f84c198a14ee101c115a2a0d027a2c72` (#865's reviewed head) on 2026-09-29 printed `3739 passed, 1 skipped in 571.40s`.

**Not established:**

- recovery evidence at the fixed engine, which is Stage 2;
- real-service ambiguity from a crash;
- concurrent recovery races.

______________________________________________________________________

## Session — 2026-09-29 (triage finalize worktree, recover for engine-written runs, in Claude Code)

**Shipped.** [#855](https://github.com/topij/agentic-dev-kit/pull/855) merged as `e265c36`; #841 is closed. Finalize's refusal now says the `worktree` must lie outside the repository checkout, and the triage workflow adds that it must not exist yet.
[#858](https://github.com/topij/agentic-dev-kit/pull/858) merged as `369e9ee`; #833 is closed. `recover` reads the engine's finished layout. Its merge read-back names no merge commit, so `recover` takes the one first-parent commit on the protected ref, after the run's `protected_branch_head`, that moves every swept block into the archive, and holds otherwise. `recover` also refuses a config-drifted completed state as valid. #858 was reviewed as a safety-critical recovery path and merged on the operator's word.

**Decided.** An LLM-only state that names no merge commit stays held; the git lookup is the engine layout's route only (#858's round 1). The dead end filed as #859 was ticketed rather than fixed in #858, because the fix is a new mechanism on a recovery path. On the operator's word, both PRs merged and this session's work is recorded under *Triage engine hardening*.

**Filed this session:** #856 (the worktree guard compares paths by case), #857 (the commit-step re-check has no test), #859 (`recover` calls a state valid that `new` then hard-stops on). Occurrence comments on #852 (record the round's receipt before pushing its fix; chained deltas composed) and #643 (lenses launched by naming the rendered prompt file).

**Review.** CodeRabbit skipped both PRs; the fallback panel carried each, and the disposition comments on the PRs own the findings.

**Verification.** In `/Users/topi/Coding/agentic-dev-kit` on 2026-09-29, `make test` at `11b2d7f0e76034e22da0a5097763036f98b6b6dc` (#855's head) printed `3702 passed, 1 skipped in 547.40s`, and at `b540930b3adb3a52290822f3761977975f8da5b3` (#858's head) printed `3728 passed, 1 skipped in 585.33s`.

______________________________________________________________________

## Session — 2026-09-28 (make lint scope, state-guard exclusion, in Claude Code)

**Shipped.** [#850](https://github.com/topij/agentic-dev-kit/pull/850) merged as `6a21e59`; #848 is closed. `make lint` hands ruff only the Python files git tracks, and `scripts/tests/test_make_lint.py` runs the recipe against a stub `uvx`.
[#851](https://github.com/topij/agentic-dev-kit/pull/851) merged as `6e87d25`. The #428 state guard read every file under `state/` in each pytest process, so this checkout's `state/review-evidence/` made the local suite far slower than CI's. New `state.test_guard_exclude`, shipped as `[]` and settable in the local overlay: a listed top-level directory is recorded as present and not walked. A list naming `pr-watch`, a directory a configured `state/...` path points into, or any invalid entry excludes nothing.

**Decided.** The exclusion is set in this checkout's gitignored `config/dev-model.local.yaml` (`review-evidence`), not the tracked config, which is also `init.sh`'s template. On the operator's word, this session's work takes no workstream. Raised and not settled: whether `models.runtime_mappings.claude` should name Opus 5.5 for a tier.

**Filed this session:** #852 (a fix round cannot compose a delta receipt without a receipt at its parent), #853 (a repo-only test file fails CI twice).

**Review.** CodeRabbit skipped both PRs, so the fallback panel carried each; the disposition comments on the PRs own the findings. #851's round-1 adversarial lens built a fabricated `pr-watch` receipt that passed the guard when `pr-watch` was listed; the refusal of engine directories came from that.

**Verification.** In `/Users/topi/Coding/agentic-dev-kit` on 2026-09-28, `make test` at `37830b8349665d2c0218b696f67808add988d9b9` printed `3701 passed, 1 skipped in 494.89s`; the same command at `5a58e1a0081494f2d9c2ce75a5e9a27c3c9526e1`, #850's first commit and so without #851 or #850's own test, printed `3688 passed, 1 skipped in 3375.64s`. #461 stays open: an unreadable file anywhere the guard still walks stops the conftest import.

______________________________________________________________________

## Session — 2026-09-28 (sweep moves earlier graduation markers, friction sweep, in Claude Code)

**Shipped.** [#843](https://github.com/topij/agentic-dev-kit/pull/843) merged as `5ac1293`; #187 is closed. A sweep moves every earlier graduation-marker section to the archive and keeps only its own; a marker-titled section holding an entry line stays. The previous layout validates as the `pre-187` rendering.
[#847](https://github.com/topij/agentic-dev-kit/pull/847) merged as `261cc83`: the first sweep under #843, triage session `3058c6ec`. It filed #844, #845 and #846, and archived TRI-04 and TRI-05 (the 2026-08-27 `claude -p` and `panel_prompt.py` entries). Both merged on the operator's word.

**Decided.** #847's record named the approver `topi`: the cockpit wrote that into the approval context, while earlier records and the GitHub login use `topij`. On the operator's word, #847 merged as produced and this commit corrects the line, since editing the engine-rendered sweep would have broken its forge chain.

**Filed this session:** #848 (`make test` stops at lint on untracked Python files). #461 carries an occurrence: unreadable leftover fixtures under `state/review-evidence/` stopped the conftest import; the cockpit restored owner read permission on them and deleted nothing.

**Review.** CodeRabbit skipped both PRs, so the fallback panel carried each; the disposition comments on the PRs own the findings. #843's round 1 found that a dated entry whose heading merely mentions "Backlog migrated" would have been archived unannotated.

**Verification.** In `/Users/topi/Coding/agentic-dev-kit` on 2026-09-28, `uvx ruff@0.16.0 check --no-fix --extend-exclude saved_plans`, `make check-syntax` and `uv run --with pytest --with pyyaml python -m pytest scripts/lib/state_paths/tests scripts/tests -q` passed at `f59e46aac0f7fcef772587a77c4e49793e1ec9d7`, pytest printing `3689 passed`. Plain `make test` was not usable there: #848.

______________________________________________________________________

## Session — 2026-09-27 (mixed triage approval, sweep rendering, retirement across config, in Claude Code)

**Shipped.** [#831](https://github.com/topij/agentic-dev-kit/pull/831) merged as `96d7632`: one triage approval carries `approve`, `archive` and `park` commands, one per line (#820).
[#832](https://github.com/topij/agentic-dev-kit/pull/832) merged as `318173c`: the sweep record names each source entry, the archive gains no trailing blank line, and a same-date group joins the archive's existing section. `render_sweep` keeps a `pre-818` rendering, so the 2026-09-26 sweep still validates (#818).
[#834](https://github.com/topij/agentic-dev-kit/pull/834) merged as `11599e6`: a session-starting entry retires a completed state written under an earlier config. The first sweep attempt held on `configuration identity mismatch`, because #824 had changed the config after the 2026-09-26 sweep completed.
[#840](https://github.com/topij/agentic-dev-kit/pull/840) merged as `c842931`: the sweep of triage session `7110f64d`, approved in one mixed reply. It filed #835, #836, #837, #838 and #839, and archived TRI-01, TRI-03, TRI-05 and TRI-06, each already carried elsewhere. The 2026-09-11 runtime entry, the 2026-09-09 process-list entry, and the 2026-08-27 `claude -p` and `panel_prompt.py` entries stay parked.
Each merged on the operator's "merge when clean". The pre-#824 `chore/triage-*` branches were deleted by hand on 2026-09-27, before this session.

**Decided.** The operator chose fixing the engine over `recover` or a hand rename. `recover` would have written a terminal `state-present-held` bundle, because its finished-run check knows only the LLM-only layout (#833).

**Filed or reopened this session:** #833, #841, and #187 reopened with the marker-accumulation recurrence. #835 carries this session's lens-fetch occurrences.

**Review.** CodeRabbit skipped every PR, and the fallback panel carried each one; the disposition comments on the PRs own the findings. The #834 round-1 delta lens found that a doc-row edit pushed without a test run broke a pinned `test_portability.py` string.

**Verification.** `make test`, each in its PR's worktree under `.claude/worktrees/` on 2026-09-27: `3658 passed, 1 skipped` at `1c4c6ede786e0c06c9954dc3dea0dba168c8838b` (#831), `3668 passed, 1 skipped` at `a0978fe6670c3f1221cb43dfec84a0b5a7d4b69c` (#832), and `3680 passed, 1 skipped` at `2daf1d835306a8eff43c26aaeef00e304a0a3551` (#834). The final LOW-repair heads of #832 and #834 got focused suites and the delta lenses' own runs, not a cockpit `make test`.

**Not established:** `check_doc_budget.py` at `c842931` on 2026-09-27 still warned on `docs/kit-friction-log.md` after the sweep; #187 owns why.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Phase 6 — gate parity and roll it out

**Status:** ordered, with an owner for each item, on 2026-09-30, in the *Phase 6*
section of `saved_plans/codex-parity-plan_2026-08-23.md`. That section owns the order,
the dependencies and the exit. **Owner:**
[#875](https://github.com/topij/agentic-dev-kit/issues/875),
[#876](https://github.com/topij/agentic-dev-kit/issues/876),
[#877](https://github.com/topij/agentic-dev-kit/issues/877),
[#663](https://github.com/topij/agentic-dev-kit/issues/663),
[#243](https://github.com/topij/agentic-dev-kit/issues/243),
[#878](https://github.com/topij/agentic-dev-kit/issues/878),
[#879](https://github.com/topij/agentic-dev-kit/issues/879),
[#880](https://github.com/topij/agentic-dev-kit/issues/880).

▶ Next: [#875](https://github.com/topij/agentic-dev-kit/issues/875) — measure the suite
with `--durations`, mark its evidence-walking tests, and add `make test-fast`. Items 2 to
4 can run beside it; the plan's *Phase 6* section has the dependencies.

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
#882. #883 carries its residual points. The finalize worktree guard decides containment by
filesystem identity (#856, in #889); #891 carries the same gap in `GitHubForge`'s
sweep-cleanup guard. The doctrine prescribes the operator's manual way out of the
two-link state (#894), and an engine-owned rollback waits for a recurrence (#892).
**Owner:**
[#859](https://github.com/topij/agentic-dev-kit/issues/859),
[#883](https://github.com/topij/agentic-dev-kit/issues/883),
[#891](https://github.com/topij/agentic-dev-kit/issues/891),
[#892](https://github.com/topij/agentic-dev-kit/issues/892).

▶ Next: chosen at the next wrap-up. #891, the same gap #856 closed, and #859 are the
candidates.
