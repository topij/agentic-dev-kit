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

## Session — 2026-09-27 (triage resume completion and create read-back lag, in Claude Code)

**Shipped.** [#828](https://github.com/topij/agentic-dev-kit/pull/828) merged as `76ef6be`: a resumed triage run completes a
merge read-back it had already verified (#826), and sweep cleanup believes only a
`verified` provider answer and builds its fallback from `SWEEP_CLEANUP_ARTIFACTS` (#827).
[#829](https://github.com/topij/agentic-dev-kit/pull/829) merged as `563e694`: after a successful GitHub tracker create, the
adapter waits, bounded, for the issue list to show the created issue before judging the
marker matches (#808). Both merged on the operator's "merge when clean". #828 also
carried the record fixes naming #826, #827 and the #256 comment.

**Review.** CodeRabbit skipped both PRs; the fallback panel reviewed each, and the
disposition comments on the PRs own the findings. On #829 the first approach, reading the
created issue directly when the list was empty, dropped the list's duplicate check under
lag, and was replaced by the wait.

**Verification.** `make test` on 2026-09-27, each in its PR's worktree under
`.claude/worktrees/`: at `f783e18a8be6fd689718f726a25910798b1d5633` it printed
`3624 passed, 1 skipped`, and at `a447d2041fc0bfb4e8abaebe56c78c80df528cda`
`3634 passed, 1 skipped`. In the main checkout it stops at conftest import on #461's
unreadable `state/` file.

**Left open:** #829 keeps the retry schedule as a class constant in `GitHubIssues` rather
than a `config/dev-model.yaml` key; its PR body raises the question.

**Not established:** the #826 resume against a real crash, and #829's wait against the
live GitHub API, including whether its bounded wait covers GitHub's actual lag. Both rest
on tests with scripted providers.

______________________________________________________________________

## Session — 2026-09-26 (triage sweep branches, #807, in Claude Code)

**Shipped.** [#824](https://github.com/topij/agentic-dev-kit/pull/824) merged as `2c2844e`
on the operator's direction in this session ("Merge when clean"); #807 closed with it. The
default `vcs.triage_branch_pattern` is now `chore/triage-{date}-{session}`, and after a
verified merge read-back the engine retires its own worktree, local branch and remote
branch, recording each result in `completion.sweep_cleanup`. The CHANGELOG entry says
what an adopter must do.

**Review.** CodeRabbit skipped. The fallback panel ran full rounds at `782532a`,
`ee209ed`, `5c9ec35` and `fbce09c`; the PR's disposition comments own the findings. The
second and third rounds each found a way for a custom provider's cleanup record to pass
the write and fail every later read. The fix that ended it was structural: the engine
now runs the completion validator itself (`validate_sweep_cleanup`) instead of keeping
its own copy of the rules.

**Verification.** `make test` at `fbce09c46c100c721deec254cb81762d5b3450b6` on
2026-09-26, in the PR's worktree under `.claude/worktrees/`, printed
`3619 passed, 1 skipped`. The same command's results at the earlier heads are on the PR.

**Not established:** a real same-day pair of triage runs, and retirement against the
real forge; both are covered only by tests with real git in temporary directories. The
stale `chore/triage-*` branches from before this change were not deleted.

______________________________________________________________________

## Session — 2026-09-26 (handoff workstreams, in Claude Code)

**Shipped.** [#822](https://github.com/topij/agentic-dev-kit/pull/822) merged as `76b883c`
on the operator's direction. Each open line of work now keeps its `▶ Next:` in the
standing `## Workstreams` section, and session entries record what happened. `wrap-up`
updates only its own workstream's entry and leaves closing to the operator;
`session-start` offers every workstream's next step and follows the operator's choice.
This file was migrated by hand in the same PR.

**Beyond the design comment**, each set out in #822's body: `Last updated:` is removed,
not only demoted; session headings no longer say `Latest`; the top of the session log is
a shared conflict point, with its resolution stated; the first-run migration lists older
`▶ Next:` lines nothing took up; and the archive sweep's footer is reworded, with the
old one still recognised.

**Review.** CodeRabbit skipped. The fallback panel ran at `3d2cc9e` and a correctness
delta at `113a97b`, for a Minor `CHANGELOG.md` imprecision; the PR's disposition comments
own the findings.

**Verification.** `make test` at `3d2cc9e2f369c326c7b1b85280d457e1b0873a33` on 2026-09-26,
in a detached worktree under this session's scratchpad, printed `3586 passed, 1 skipped`.
It did not run in the main checkout, because of #461. CI's `Test` run at `113a97b`
passed, and a PR comment carries its figures.

**Not established by the suite:** a Codex wrap-up under the contract, two workstreams
wrapping up in either order, a resumed older workstream, and an unrelated chosen task.
This wrap-up is the layout's first live use, in Claude Code.

Closed workstream Handoff workstreams: the layout shipped and this wrap-up used it; the
scenarios above are left to ordinary use, on the operator's decision.

______________________________________________________________________

## Session — 2026-09-26 (triage engine fixes, friction sweeps, #762 design, in Claude Code)

**Shipped, each with a fallback panel because CodeRabbit's automatic review is off:**

- [#812](https://github.com/topij/agentic-dev-kit/pull/812) merged as `cee1f6f`. Engine
  sweeps write a record block under their marker, a later sweep keeps the marker, and
  neither the EOF nor the archive heading spacing is mangled. It resolves #806, which
  was closed by hand. A delta lens caught that the first repair commit had spliced an
  existing test into a new one; `4ac95bb` restored it before merge.
- [#813](https://github.com/topij/agentic-dev-kit/pull/813) merged as `c8b9be5`. It fixes
  forward a regression #812 introduced: commit validation re-rendered retained sweeps
  with the new renderer, so the 2026-09-25 `completed` state could not be retired and
  triage refused to start. Validation now also accepts the pre-#812 rendering. Its PR
  body carries the `make test` stamp and the offline replay against that state.
- [#817](https://github.com/topij/agentic-dev-kit/pull/817) (`d027c66`) and
  [#819](https://github.com/topij/agentic-dev-kit/pull/819) (`fe93d98`) are engine-backed
  triage sweeps, both merged on the operator's direction. The run behind #817 filed
  [#814](https://github.com/topij/agentic-dev-kit/issues/814),
  [#815](https://github.com/topij/agentic-dev-kit/issues/815) and
  [#816](https://github.com/topij/agentic-dev-kit/issues/816). #819 archived three
  entries whose fixes had already shipped. The run needed two sweeps because one
  approval carries one command ([#820](https://github.com/topij/agentic-dev-kit/issues/820)).

**Filed at wrap-up, on the operator's approval of the exact payloads:** #820, and an
occurrence comment on #808 (every create in the #817 run read back `ambiguous` and was
verified on resume). [#818](https://github.com/topij/agentic-dev-kit/issues/818) was
filed earlier as the ticket disposition for the #817 panel's low-severity rendering
findings.

**#762 design decided.** Continuations move into a standing `## Workstreams` section.
Session blocks become an event log. The design, the defaults for workstream naming and
closing, and the migration are in the
[design comment](https://github.com/topij/agentic-dev-kit/issues/762#issuecomment-5845903370).
The operator scheduled #762 ahead of the next cs-toolkit upgrade, and asked for it to
run in a fresh session at higher effort.

**Not established:** where the next cs-toolkit upgrade sits in the sprint plan. Neither
`saved_plans/phase5-completion-plan_2026-09-18.md` (local, not committed) nor Phase 6 in
`saved_plans/codex-parity-plan_2026-08-23.md` names one.

______________________________________________________________________

## Session — 2026-09-26 (documentation refresh, in Codex)

**Shipped.** [#810](https://github.com/topij/agentic-dev-kit/pull/810) merged as
`09fcbe874249ea773e25acd7a591487170acd07d` on the operator's direction. The new
developer guide gives task-oriented routes; the architecture guide illustrates
components, PR flow, lane state, and friction routing with Mermaid. Entry guides and
the shared parallel workflow now agree with the supported upgrade, activation,
merge-authority, and model-tier behavior.

**Review.** CodeRabbit reported that automatic review was skipped. The PR carries
the fallback panel and composed delta review evidence; its comments own the findings
and dispositions.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Continuations are not kept in them: each workstream's next step lives in its entry under "Workstreams".

______________________________________________________________________

## Workstreams

### Phase 5 exit

**Status:** D-TRIAGE-RECOVERY ran in stages:

- Stage 1 at `197a242` found F-1, F-2 and F-3, which #865 (`b13abb3`) fixed.
- Stage 2 ran at `b13abb3` on 2026-09-29; its `RESULTS.md` owns the outcome.

The row awaits the operator's acceptance. The D runs' open residuals go to the E audit,
which also decides whether to commit the local `saved_plans/phase5-*` packets.

#748 and #7 were both open on 2026-09-29, awaiting the operator's judgment of whether
#769 discharges them. The 2026-09-23 D-SYSTEMIZE-RECOVERY packet block in
[`kit-handoff-history.md`](kit-handoff-history.md) sets out the options.

**Owner:** these files, all local and not committed:

- `saved_plans/phase5-completion-plan_2026-09-18.md`;
- `saved_plans/phase5-d-triage-recovery_2026-09-29.md`;
- `saved_plans/phase5-d-triage-recovery-02_2026-09-29.md`.

▶ Next: the operator accepts or rejects D-TRIAGE-RECOVERY from the Stage 1 and Stage 2
`RESULTS.md` files. Then prepare the Phase 5 E audit packet (milestone E of the
completion plan), which reconciles each D row's evidence and open residuals against the
Phase 5 contract.

- **Its first question** is whether any D row is still owed. Leads to re-check include
  the triage side of D-SERVICE, named as not established in the 2026-09-23
  D-SYSTEMIZE-LIVE history entry, and notification-thread approval, named in the
  2026-09-25 D-TRIAGE-RESIDUAL entry with #198.
- **Also open for the audit to weigh:** #794's workflow fix, which is residual R1 of the
  D-SYSTEMIZE-RECOVERY-02 run.

### Reviewer profiles

**Status:** on 2026-09-25 the operator asked the reviewer's developer to post a GitHub
check run, which would let the merge gate's existing check-based path see it; #797 can
wait for that answer. **Owner:** [#796](https://github.com/topij/agentic-dev-kit/issues/796),
[#797](https://github.com/topij/agentic-dev-kit/issues/797); the adopter-specific notes are
in `saved_plans/fabro-review-tool-assessment_2026-09-25.md` (local, not committed).

▶ Next: implement #796 — adopter-defined reviewer profiles and a configured
review-request method.

### Triage engine hardening

**Status:** `recover` retires an engine-written finished run by finding its sweep in git
(#858); finalize names where its `worktree` must lie (#855). **Owner:**
[#856](https://github.com/topij/agentic-dev-kit/issues/856),
[#857](https://github.com/topij/agentic-dev-kit/issues/857),
[#859](https://github.com/topij/agentic-dev-kit/issues/859).

▶ Next: #857 — pin finalize's commit-step worktree re-check with a test that reaches the
commit step with a recorded worktree inside, then containing, the checkout.
