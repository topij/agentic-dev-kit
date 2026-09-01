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

Last updated: 2026-09-02 — PR `#659` (squash `4e63fd8`) retained the independently
recomputable Codex parallel-batch evidence and completed the Phase 4 exit.

## Latest session — 2026-09-02 (retained Codex parallel-batch evidence, in a Codex session)

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
  correctness rechecks reproduced the hostile cases and compatibility controls; no
  general dataflow mechanism or new schema was added. PR `#659` carries the resulting
  `fallback:panel` receipt at `d0eac77185d808ef822ba7fefe3247de902927da`.

- **Verified:** `make test` in a quiet fresh clone at
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

## Session — 2026-08-29 (safety-critical profile binding, in a Codex session)

**Theme —** In a Codex session, PR `#649` (squash `1976923`) made the answer to `#633`
explicit and checkable: changing the policy profile can change unattended authority while
`launch_lane.py` remains byte-identical, so a behavioral profile change takes the shared
safety-critical review and operator-merge route.

- **Codex and Claude bind the same doctrine through runtime-native mechanisms.** The root
  `AGENTS.md` names the profile resolved by `parallel.claude_settings_profile`; Claude's
  path-scoped rule names the shipped path and tells adopters to move that entry when they
  relocate the profile. The shared workflow carries the decision and its boundary rather
  than either adapter restating the doctrine.

- **The boundary is the dedicated policy file, not every configuration leaf.**
  `config/dev-model.yaml` stays outside Claude's file-path trigger because that trigger
  cannot select authority-bearing `parallel.*` keys without sweeping unrelated config.
  `#346` still owns the workflow-document gap, `#434` still owns the test-side merge guard,
  and `#621` and `#631` stay open. No lane grant from `#631` was built here.

- **The CHANGELOG entry is intentional adopter guidance.** The change alters when the
  operator-merge authorization gate applies, while `init.sh --no-clobber` preserves the
  adopter-owned Codex and Claude bindings that need a manual update.

- **Review turned the check from vocabulary matching into a semantic guard.** Negated
  runtime instructions, inverted relocation remedies and a config-only profile move all
  survived earlier substring checks. The merged test sentence-scopes the positive runtime,
  workflow, Claude-comment and CHANGELOG obligations; a supported relocation updates the
  config, Codex binding and Claude path while keeping shipped-default prose unchanged.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `9926741668117bec53eb9e08534c0bcd83f5cbe3` on 2026-08-29 ended at `#393`'s known
  `test_a_payload_too_deep_for_json_load_still_exits_zero` intermittent; that exact node
  passed when `uv run --python 3.12 --with pytest --with pyyaml python -m pytest
  scripts/tests/test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero
  -q` ran in the same directory at the same revision and date. `gh pr checks 649`, run in
  the same directory at that revision and date, reported the `toolkit` check successful.
  `scripts/pr_watch.py 649 --json --no-persist`, run in the same directory at that revision
  and date, reported it mergeable before the authorized squash merge.

▶ Next: `session-start` — re-read `#621`, `#631`, `#346` and `#434` with live repository
and tracker state before choosing the next slice.

______________________________________________________________________

## Session — 2026-08-29 (friction-log triage, in a Claude Code session)

**Theme —** In a Claude Code session, `triage-friction-log` ran end to end in LLM-only mode —
both configured engines are absent, which is the state that selects that mode, so every result
is `agent-executed` and `#6` still tracks vendoring them.

- **Filed from the inbox:** `#641` (`launch_lane.py`'s `Bash(:*)` refusal — parked last
  session, and filed here as its own issue rather than the `#631` comment that block offered,
  on the operator's approval of the triage payload), `#642` (a lens asserting a base-currency relationship its own command did not
  establish), `#643` (`panel_prompt.py` renders to a file while a Claude Code lens launch needs
  inline text), `#644` (a second intermittent test, beside `#109`), `#645` (the scope of the
  two-tree `cd` rule). The `#428`-guard entry was archived unfiled, because its own text records
  that occurrence on `#467`.

- **Three entries were kept active rather than swept, and the new marker says so in prose.**
  Each parks itself for accumulation, and an archived entry reaches no later triage pass — the
  distinction `#575` raises. Position alone cannot carry it, which is `#224`.

- **The run ended `operator-held`, not complete, and that is this session's real finding.**
  CodeRabbit reviewed `cf33e5e` cleanly, but its verdict arrived as an issue comment, so
  `qualifying_bot_coverage` could not see it (`#44`) and `pr_watch` never bound a review
  receipt. The operator merged on their own authority, which the workflow explicitly permits —
  but completion requires the merged head to equal a retained `reviewed_head`, and no
  completion route is reachable without one. The state was left valid, correct and
  uncompletable, and a later resume would have hit the same wall. Filed as `#647`.

- **No `--record-review` receipt was written, deliberately.** The receipt vocabulary names
  fallback passes only and no fallback panel ran, so recording one would assert a review that
  did not happen. `reviewed_head` was not inferred from the merged and reviewed heads being the
  same commit; that inference is the thing the receipt exists to prevent.

- **The uncompletable state was quarantined on the operator's go-ahead** to
  `state/triage/quarantined-uncompletable_live_2026-08-29_281cfd4f574f3256_issue-647.json`,
  preserved as `#647`'s evidence rather than deleted, so a later run starts a clean draft.

- **Occurrence comments filed:** on `#491` (the poll prescribed the fallback panel for a bot
  configured off rather than down — one `@coderabbitai review` got a real review of the merging
  head) and on `#187`, closed 2026-08-09, whose mechanism recurred: the marker's first draft
  left the inbox *longer* than before the sweep, and `triage-friction-log.md`'s finalize step
  never mentions the budget.

- **Verified:** the sweep was checked against the merged tree rather than the worktree that
  wrote it — `git show ded3933:docs/kit-friction-log.md` and the archive, run in
  `/Users/topi/Coding/agentic-dev-kit`, showed every swept block verbatim in the archive and
  absent from the inbox, and every parked block still in the inbox and unarchived. `make test`
  was not run: the change is two markdown documents, and `#646`'s `toolkit` check ran the suite.

▶ Next: `session-start` — `#647` is new and unowned, `#606`, `#621`, `#631` and `#633` are
untouched, and the parked inbox entries are waiting on recurrence rather than on a pass.

______________________________________________________________________

## Session — 2026-08-29 (whole-tool Bash allow grants, in a Claude Code session)

**Theme —** In a Claude Code session, PR `#639` (squash `56c0eb3`) took `#606`'s
residual: `_bash_allow_prefixes` asserted that `Bash`, `Bash(*)` and `Bash(:*)` each
grant every command, the one behavioural claim in `#637` that shipped without a stamp.

- **The hard part was the configuration, not the spellings.** Headless `-p` does not
  gate on the absence of an `allow` rule, so the earlier cockpit probe could only ever
  reach the deny matcher. `--restricted` ignores the user, project and local settings
  files, which makes the rule under test the only rule in play; `--tools Bash` leaves
  the model no non-Bash route to the observable.

- **The control is what makes the readings mean anything.** An empty allow list refused
  the probe command and the client recorded a `permission_denials` entry for it, so the
  configuration is *shown* to gate on `allow` rather than assumed to. Two dead ends are
  worth knowing: redirecting `CLAUDE_CONFIG_DIR` for isolation removes the credentials
  with the settings, and `Not logged in` scored as a refusal until the harness learned
  to report it separately.

- **`Bash(:*)` grants nothing, and needed no compensating branch.** It still matches the
  rule regex, contributes the empty prefix, lexes to no words, and `_grants_invocation`
  rejects an empty word list. The exact-vs-prefix pair was re-measured on the allow side
  at the same time, so that claim no longer rests on `allow` and `deny` sharing a
  grammar. Runs, harness and its hash are in
  [`claude-bash-allow-grants-live-validation_2026-08-29.md`](../saved_plans/claude-bash-allow-grants-live-validation_2026-08-29.md).

- **The panel found the defect in the fix, not in the change.** CodeRabbit skipped, so
  the fallback panel carried the review across three rounds. Round 1's adversarial lens
  re-ran the committed harness against the live client and matched every documented row.
  Round 2 found that the test *added in round 1* had a docstring naming the wrong
  mutation — it claimed to pin the match-anything repair, which a sibling test catches,
  when what it pins is short-circuit resistance. Prose beside a passing test is the
  shape this repo's own rules are about, and it survived a round.

- **Nothing was filed to the tracker this session.** Both lenses independently reached
  `scripts/launch_lane.py`'s own `Bash(:*)` classifier, which refuses the rule from a
  lane profile on its *shape*; this measurement says the client grants nothing under it,
  so the refusal is more conservative than it needs to be. Neither lens proposed a fix
  and both called it out of scope, so it is parked in the friction log rather than
  filed — an occurrence comment on `#631` is available on the operator's go-ahead.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `061a85c89ae3e97b8b7a3fea033c6794dcc74144` on 2026-08-29 reported one failure,
  `test_pr_followup_hook.py::test_a_payload_too_deep_for_json_load_still_exits_zero` —
  `#393`'s intermittent, in a file this change does not touch — which passed on an
  isolated re-run at that revision. `uv run --python 3.12 … pytest` at the same revision
  printed `2091 passed`. Both round-1 lenses independently ran the full suite in their
  own clones at `d272a5a` and each reported `1 failed, 2089 passed, 1 skipped` with the
  same test failing — unlike `#637`, where the cockpit and the lenses hit *different*
  intermittents at the same revision.

▶ Next: `session-start` — `#606` remains open on its own scope, `#621`, `#631` and
`#633` are untouched, and the friction-log inbox is over its budget with entries from
today, so the next session has several threads rather than one.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
