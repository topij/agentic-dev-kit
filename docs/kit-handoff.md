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
> Older session blocks graduate to [`kit-handoff-history.md`](kit-handoff-history.md) once
> this file crosses its line budget (`scripts/check_doc_budget.py`).

Last updated: 2026-09-02 — the cs-toolkit adopter pilot's read-only pass ran, and a
parked friction entry recurred deterministically on a quiet tree.

## Latest session — 2026-09-02 (cs-toolkit adopter pilot, read-only pass, in a Claude Code session)

**Theme —** Phase 5's exit test, first half. `/upgrade` Steps 0 and 1 ran against the
cs-toolkit adopter from a pinned kit clone. Nothing was written to the adopter. The
verification run then reproduced a parked friction entry under conditions that
contradict its parked hypothesis.

- **Runtime —** Claude Code, model `claude-opus-5[1m]` as this session's own system
  prompt names it; effort not read.

- **The pilot's findings live in the record, not here.**
  [`cs-toolkit-adopter-pilot-readonly_2026-09-02.md`](../saved_plans/cs-toolkit-adopter-pilot-readonly_2026-09-02.md)
  carries every reading with its command, the two tree bindings, and the three
  revisions they were taken against. `#661` is confirmed with its line
  (`scripts/kit_doctor.py:2652` filters `required_by` on the dependent's presence
  rather than on the installed version's requirement), and the same root cause has a
  second occurrence: `kit_doctor`'s lens-definition remedy prescribes
  `scripts/devkit/panel_prompt.py`, which `find` locates nowhere in the adopter.

- **What the pilot found that the sprint review did not predict:** `/upgrade` Step 1
  sends you to the adopter's installed engine first, which reports `intact` and names
  no new file, while the kit's engine reports `NOT intact` about the same tree — and
  Step 1's documented remedy for that under-reporting is a write, so a read-only pass
  cannot reach the complete view by the route the step names. `#607` is confirmed and
  invisible to every instrument: the adopter's lane engines are forks outside
  `paths.engines` and absent from its manifest, so `#598`'s BREAKING exit-`64` contract
  drifted unreported. And the adopter has already invented the mechanism the kit lacks
  — a repo-local runtime-neutral appendix, applied to `wrap-up` alone — while
  `session-start`'s Claude appendix, including the `origin/main` rule the appendix says
  cost that repo a duplicate ticket on 2026-08-10, reaches no Codex session.

- **A parked friction entry recurred, and its hypothesis did not survive.** The
  2026-09-01 inbox entry parked
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero`
  on a concurrency correlation. It recurred here twice on a quiet tree with nothing
  running alongside, and passed standalone both times. The measured precondition
  (`json.loads` on the test's own input, in the suite's interpreter) raised
  `RecursionError: Stack overflow (used 8144 kB)`, so the assertion that fails is
  `out == ""` and not the exit code — the parse succeeded inside the suite where it
  raises in isolation. `test_init_sh.py:5100` already names this as `#393`'s shape and
  guards its own precondition by measuring it; the failing sibling does not.

- **`#510` fired on the session that was verifying.** The first run was
  `make test 2>&1 | tail -25`, so the harness reported exit `0` over an output ending
  `make: *** [test] Error 1`, and the `tail` discarded the traceback the friction
  entry's own recurrence instruction asks to keep. The second run retained full output
  and captured `make`'s status directly.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `679b197efc24e31a66e94f6d52b6b3e5f2a47855` on 2026-09-02 printed
  `1 failed, 2403 passed, 1 skipped, 3 warnings in 458.08s (0:07:38)` with `make`
  exiting `2`. **That stamp names the parent commit, not this PR's head** — the
  commits after it are this handoff block and the friction entry, and `make test`
  carries no gate over either file's content, so the run's scope is stated rather
  than extended. The failure is the pre-existing one above: that commit's footprint
  is one `saved_plans/` file, that path is absent from `kit-manifest.json`, and no
  test reads it. It is also platform-dependent, not merely intermittent: the GitHub
  Actions `toolkit` job for PR `#665` printed `2402 passed, 3 skipped in 229.89s`
  with the same test carrying no skip marker. Nothing was filed to the tracker.

▶ Next: `session-start` — then bring the pilot's write pass to the adopter operator
for approval, and decide whether the recurrence above graduates `#393` or opens its own
issue.

______________________________________________________________________

## Session — 2026-09-02 (parity sprint review, in a Claude Code session)

**Theme —** A review-only session: the Codex parity sprint was read against the tree, the
tracker, the merged pull requests and the cs-toolkit checkout, and the plan was
re-sequenced so the adopter pilot is the next slice rather than the last.

- **Runtime —** Claude Code, model `claude-fable-5-1` as the session's own system prompt
  names it; effort not read.

- **The review lives in the plan, not here.**
  [`codex-parity-plan_2026-08-23.md`](../saved_plans/codex-parity-plan_2026-08-23.md)
  gained a *Sprint review — 2026-09-02* section carrying the stamped readings, and its
  *Sprint status*, Phase 5 and Phase 6 lists and next starter were rewritten from it.
  No code changed; nothing was committed to `main`.

- **What the review found, each with its command in the plan:** the live-validation
  verifier and its test ship to adopters as manifest engine and test while nothing they
  verify ships; cs-toolkit is pinned at the 2026-08-22 kit and `kit_doctor` misreports it
  as broken because `required_by` is filtered on the dependent's presence rather than
  its installed version; review evidence for PR `#659` is recoverable only from
  gitignored state, the `#603` / `#604` shape recurring on the sprint's own exit
  evidence; pull-request data is fetched by hand in `session-start.md` and by engine in
  `pr_watch.py`; the same status facts are restated across the plan, the handoff and
  the parity matrix, with the matrix's headless-lane row a single table cell.

- **Re-sequencing decided in the plan:** the cs-toolkit adopter pilot moves from the end
  of Phase 6 to Phase 5's exit test, read-only pass first; withdrawing the verifier from
  the shipped manifest and putting review evidence on the pull request join Phase 5;
  `#631`, `#608` and `#255` are taken as declarations rather than mechanisms; the
  proportional opening pass (`#585`), suite marking and the learnings-memo distillation
  lead Phase 6.

- **Filed on the operator's approval of each exact payload, in this session:** `#661`
  (`kit_doctor`'s false "broken, not sized down" verdict), `#662` (the verifier ships
  with nothing to verify), `#663` (pull-request data fetched by hand and by engine), and
  occurrence comments on `#603`, `#604`, `#585` and `#243`. Each create and comment was
  read back from the tracker after landing — state, title, labels and body — against
  its approved payload. Nothing was parked; the friction inbox is unchanged and its
  graduation is still `triage-friction-log`'s sweep.

- **Verified:** `make test` was not run; the change is one `saved_plans/` document and
  this handoff. The plan's tables were checked for cell count and escaped pipes and the
  whole file for a closing keyword beside an issue number, by a script in the session
  scratchpad, in `/Users/topi/Coding/agentic-dev-kit` at
  `89dbb3e67497586254e913dc3f5fdf7f648746bd` on 2026-09-02.
  `uv run scripts/archive_plan_sessions.py --target-lines 400`, run in the same
  directory on the same date over that revision plus this session's uncommitted edits,
  moved the 2026-08-29 whole-tool Bash allow grants block into
  `kit-handoff-history.md`; `check_doc_budget.py` prints the live figures.

▶ Next: `session-start` — then the plan's next starter: the cs-toolkit adopter pilot,
read-only pass first, with `$REPO` and `$KIT` bound before anything else.

______________________________________________________________________

## Session — 2026-09-02 (retained Codex parallel-batch evidence, in a Codex session)

**Theme —** The Codex-only Phase 4 exit shipped as retained evidence: disjoint lanes,
exact-head reviews and operator-held merge authority can be recomputed from promoted bytes.

- **Runtime —** Codex desktop, assigned model `gpt-5.6-sol`, main reasoning effort `high`.

- **PR `#659` retained the parallel batch without merging its fixture work.** The
  bundle binds each lane's worktree and state root, Git head, launcher receipt,
  correctness and adversarial executions, forge readback, reconciliation refusal and
  complete claim-to-artifact map. Fixture PR `#1` and `#2` remain open in the private
  synthetic repository; the operator merge boundary is evidence, not exercised permission.

- **The promotion contract is independently recomputable.** The public verifier derives
  the retained source closure and semantic claims from Git-bound bytes, and the
  promotion receipt binds the resulting manifest. Review repairs made numeric values,
  formatted expressions and format specifications visible to the credential scanner,
  while preserving named runtime helpers and direct `Authorization` carriers. The
  review-lens regression guard also binds each retained prompt, worktree and launch argv
  to its declared lens.

- **The review stopped at the demonstrated boundary.** Exact-head adversarial and
  correctness rechecks reproduced the hostile cases and compatibility controls. The
  scanner repairs stayed at the demonstrated expression shapes instead of adding a
  general dataflow mechanism; the retained batch uses PR `#659`'s explicit plural
  reviewed-head evidence shape. PR `#659` carries the resulting `fallback:panel`
  receipt at `d0eac77185d808ef822ba7fefe3247de902927da`.

- **Verified:** `make test` in
  `/private/tmp/adk-codex-parallel-20260901.xlAufG/root-final-test-d0eac77` at
  `d0eac77185d808ef822ba7fefe3247de902927da` on 2026-09-02 printed
  `2405 passed in 367.84s (0:06:07)`; the merged squash is `4e63fd8`.

- **The session did not change tracker or friction state.** `#621`, `#631` and `#255`
  retain their live disposition questions; the overdue friction-log graduation still
  requires `triage-friction-log` and exact tracker-payload approval.

▶ Next: `session-start` — in a Claude Code session take `#243`'s field exercise of
`adopt`, `parallel`, `triage-friction-log` and `post-merge-systemize`; bind `$REPO` and
`$KIT` before `adopt` writes, and obtain the workflow-specific approvals before any
tracker or external write.

______________________________________________________________________

## Session — 2026-09-01 (runtime_mappings status declaration, in a Claude Code session)

**Theme —** `#255`'s disposition was settled against the tree rather than against the
plan's summary of it, and the one measured residue shipped. The session then found its
own disposition had been drawn too wide.

- **Runtime —** Claude Code 2.1.252, assigned model `claude-opus-5`, effort `xhigh`,
  read from this session's own transcript rather than from the prompt or argv.

- **PR `#657` (squash `b5bc17a`) closed the gap between `#255`'s proposal and its
  delivery.** `lens_compute` carried the per-runtime mechanical/advisory declaration on
  both install surfaces; `models.runtime_mappings` carried it on the reference config
  only, so a migrating adopter's config surface stated the values without their status.
  `init.sh` now emits it, and `_runtime_mappings_block` — written for that pin and
  wired to no assertion — became `_runtime_mappings_comment` behind a pin holding both
  surfaces. The emitted block moved to single quotes because the added comment text
  carries backticks.

- **`Makefile`'s mutation guidance was inverted for the files that PR touched.** It
  named `scripts/tests/` and `init.sh` as paths a mutation never trips the drift check
  on; both are in `kit-manifest.json`, so a mutation to either read as killed under
  plain `make test` with nothing behavioural catching it. Corrected to send a
  contributor to the manifest rather than to the comment's own list.

- **`#255` stays open, and the disposition comment that implied otherwise was too
  wide.** Both halves of its *Proposed* section are delivered for the two keys the
  issue's own comments name, but the Proposed states a general rule over every
  compute- or capability-selecting key. Enumerating those found two carrying no
  per-runtime status: `review.fallback_commands` (consumed by `pr_followup_hook.py`,
  agent-executed and so advisory — the issue's own "real consumer, zero mechanism"
  shape) and `runtime.launchers` (consumed by `dev_session.sh`). A correction comment
  is owed on the issue and was not posted this session.

- **The panel's convergence was not corroboration.** Both lenses filed no finding
  against the diff and both drew the same overstated conclusion from the same probe.
  Recorded with the enumeration lesson in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **The sprint boundary held.** This session did not start `#631` or the retained Codex
  parallel-batch Phase 4 run, and `saved_plans/claude-side-assessment_2026-08-26.md`
  stayed operator-owned and unstaged.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `da142620a02d16d31e3231249d627b8fd194daa9` on 2026-09-01 printed
  `2374 passed in 514.92s (0:08:34)` on a quiet tree; the merged squash is `b5bc17a`.

▶ Next: `session-start` — then take `#243`'s Claude-side field exercise of `adopt`,
`parallel`, `triage-friction-log` and `post-merge-systemize` as the opening slice, and
settle `#255`'s two remaining undeclared keys.

______________________________________________________________________

## Session — 2026-09-01 (parity reconciliation and lens diagnostics, in a Codex session)

**Theme —** The session reconciled the parity plan and tracker against live repository
state, then PR `#655` delivered `#255`'s adopter-side lens-definition diagnostic without
duplicating the existing engine-drift responsibility.

- **Runtime —** Codex desktop, assigned model `gpt-5.6-sol`, main reasoning effort
  `high`.

- **The tracker now follows delivered contracts.** The 2026-09-01 reconciliation
  closed `#365`, `#169`, `#466`, `#601`, `#605`, and `#606` after read-back of their
  merged repository evidence.

- **PR `#655` keeps the responsibilities separate.** The already-running doctor
  renders the expected adopter-owned Claude definition; the existing manifest-backed
  file report continues to own installed-engine drift. The regeneration remedy changes
  to the inspected root, creates the target directory, and quotes configured paths.
  The generator imports its sibling doctor before `lib`, and the manifest derives that
  dependency.

- **Review changed the design rather than merely adding guards.** The renderer-bundle
  authentication approach was removed when successive findings showed it duplicated
  engine drift. The surviving boundary, command-context fixtures, and DRY ownership
  lessons are recorded in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **The remaining parity boundary is explicit.** Phase 4 still needs the separately
  retained Codex parallel-batch evidence run; `#621` does not own it. Phase 5 retains
  `#236`, `#243`, and `#631`; `#255` needs tracker disposition rather than more
  implementation. Phase 6 retains adoption fixtures, trusted runtime smoke tests,
  maintained parity reporting, `#607`, and `#608`. This session did not start `#631`
  or the Phase 4 run.

▶ Next: `session-start` — verify PR `#655` and `#255` live, present the exact proposed
tracker disposition for `#255`, then recommend the next parity slice without starting
`#631` or the retained Phase 4 Codex parallel-batch run.

______________________________________________________________________

## Session — 2026-09-01 (draft-policy correction, in a Codex session)

**Theme —** PR `#653` made completed pull requests ready for review by default across
shared doctrine, adopter workflows, shipped baselines, runtime bindings, configured
workflows and automatic follow-through. Draft remains only for a bounded material
unfinished-work window that already needs a remote pull request; its creating run owns
the ready transition.

- **Runtime —** Codex desktop, assigned model `gpt-5.6-sol`, main reasoning effort
  `xhigh`.

- **The hook stops at an authority boundary.** Shell and response text select
  non-authoritative candidate guidance; they do not prove that a lifecycle event ran,
  identify its target, or authorize a mutation. After operation assessment,
  authoritative forge identity and live draft state decide the conditional route. A
  shell parser was deliberately abandoned in favour of harmless warning false
  positives and fail-closed follow-through.

- **The adopter contract moved with the policy.** Adopt stays local until its
  operator-run initialization is complete; upgrade names the required
  `triage.pr_draft: false` and `systemize.pr_draft: false` migration; the playbook,
  lane contract, baseline templates and shared workflows carry the same bounded draft
  exception.

- **The review evidence is attached to the change.** PR `#653` carries the exact-head
  Python 3.12 verification stamp, the superseded-head dispositions, and the final fresh
  adversarial/correctness fallback-panel receipt for
  `239de40fb09faae1bfb6e3b1c6af8464f8e67414`; squash
  `dd536eee3e562fd806a4b90c8377ec532ebf6925` is the merge event.

- **The sprint boundary was preserved.** This session did not start `#631` or the
  retained Codex parallel-batch Phase 4 exit. `#621` kept the operator-set boundary,
  and `saved_plans/claude-side-assessment_2026-08-26.md` remained operator-owned and
  unstaged.

- **The process lesson is durable.** The authority-boundary, hostile-corpus and
  mutation lessons from this review are recorded in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

▶ Next: `session-start` — re-read the live tracker and sprint boundary before choosing
a slice; do not infer issue closure from PR `#653`'s merge.

______________________________________________________________________

## Session — 2026-08-31 (durable live-validation evidence, in a Codex session)

**Theme —** PR `#651` settled the retained-bundle verifier around an explicit object:
a descriptor-rooted immutable byte snapshot whose digest and semantic checks derive
from the same captured bytes. It does not claim that a mutable multi-file directory has
an atomic state at process return.

- **Runtime —** Codex desktop, assigned model `gpt-5.6-sol`, reasoning effort `high`.
  `jq` over the root rollout's final `turn_context`, run in
  `/Users/topi/Coding/agentic-dev-kit` at `8e812936f8650589f6445a1761733a5f243a9cfb`
  on 2026-08-31, read back those values and that directory.

- **The race correction is descriptor-relative, not another path reread.** Validated
  directory identities and no-follow opens anchor a captured-byte guarantee rather
  than mutable on-disk state at return. The behavioral nodes
  `test_an_earlier_artifact_changed_while_a_later_artifact_is_captured_binds_the_snapshot`
  and `test_an_ancestor_swap_after_its_descriptor_opens_cannot_redirect_the_snapshot`
  pin its race boundary. Their child processes receive an explicit observer callback
  and install no Python startup module or `PYTHONPATH` override.

- **The retained claim remains bounded.** The writing-lane bundle promotes its scoped
  output, private open/non-draft/`CLEAN` pull request and exact-head review receipt.
  Its uncorrelated runtime attestation remains outside the claim map. The synthetic
  private repository `topij/adk-codex-writing-evidence-20260830` remains because the
  available credential did not carry deletion authority.

- **Phase 4 remains open.** The retained writing lane establishes `#621`'s bundle
  mechanism but is not the independently recomputable Codex parallel-batch run named
  by the phase exit. Under this sprint's operator-set boundary, `#621` remains open
  without owning that run; `#631` remains a safety-critical execution-boundary decision.

- **Review and merge evidence stays with PR `#651`.** Its
  [exact-head panel disposition](https://github.com/topij/agentic-dev-kit/pull/651#issuecomment-5471285211)
  carries the review commands and results; the merged PR binds that reviewed head to
  squash `8e812936f8650589f6445a1761733a5f243a9cfb` without duplicating recomputable
  command output here.

▶ Next: `session-start` — take the draft-policy documentation correction as a fresh
slice. Re-read `#365` and related `#169` against live repository and tracker state,
choose one coherent ready-by-default rule only if the current surfaces support it,
and do not start `#631` or the retained Codex parallel-batch Phase 4 exit.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

