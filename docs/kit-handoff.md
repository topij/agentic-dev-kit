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

Last updated: 2026-08-31 — PR `#651` (squash `8e81293`) merged the durable
live-validation evidence verifier and its retained Codex writing-lane bundle.

## Latest session — 2026-08-31 (durable live-validation evidence, in a Codex session)

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

## Session — 2026-08-29 (cockpit settings policy, in a Claude Code session)

**Theme —** In a Claude Code session, PR `#637` (squash `83b959e`) took Phase 5's
remaining `#606` slice, on `.claude/settings.json`. Its three questions were answered
separately, and most of the change's value came from the review rather than the first
draft.

- **The engine path is templated, and `init.sh` prints it rather than writing it.** The
  allow rule baked in `scripts` and no permissions advisory existed at all, so an
  adopter vendoring under `scripts/devkit/` had no route to a correct rule. The advisory
  follows `#303`'s print-never-write doctrine, and the reason is sharper here than for
  hooks: an allow-list is policy about what may run unattended.

- **The `SessionStart` matcher was ours, not the runtime's.** `"startup"` was read as a
  limit until it was measured; a resumed session had been starting with both budget
  tripwires silent. Both runtimes now omit the matcher. The runs, the fixture hash and
  what was *not* exercised are in
  [`claude-sessionstart-matcher-live-validation_2026-08-29.md`](../saved_plans/claude-sessionstart-matcher-live-validation_2026-08-29.md).

- **The grant check was wrong in each direction available to it, always toward false
  reassurance.** It counted an exact-form rule that pre-approves one argument-less
  invocation; it counted any rule merely *naming* the engine — `cat`, `ruff check`,
  `rm`; and it missed `Bash(uv run:*)`, which covers every poll. It now asks whether a
  rule's tokens open the command the workflow issues. Rounds 5 and 6 each finding a
  defect in the same function was the signal its predicate was wrong rather than its
  cases incomplete.

- **CI caught a defect no local run could.** `Path.resolve()` reports a symlink
  loop as `RuntimeError` on Python 3.12 and returns the path unresolved on 3.14, and
  `make test` pins no interpreter — so three independent local suites passed and CI went
  red. The panel's redundancy is across reviewers, not across environments.

- **Filed this session:** occurrence comments on `#393` (a second test resting on
  `json.load` raising `RecursionError`, and the first observed failure of that shape,
  which falsifies that issue's "latent" framing), `#292` (the interpreter axis of its
  local-gate-weaker-than-CI thesis), and `#606` (the residual measurement task below).
  Review lessons are in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **Left deliberately open:** `_bash_allow_prefixes` asserts that `Bash`, `Bash(*)` and
  `Bash(:*)` each grant every command, and that assertion carries no stamp while every
  other behavioural claim in the change does. A cockpit deny-side probe and a lens
  allow-side probe disagree on two of the three. The check is advisory and the kit never
  emits `Bash(:*)`, so this was disclosed on the PR and on `#606` rather than fixed
  under a stopping rule the operator set at one review round on the rewrite.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `52d25e5b95e2e7d8cb188c7bbeced43fbfcaffc7` on 2026-08-29 reported one failure, in
  `test_pr_followup_hook.py` — the intermittent test recorded on `#393`, untouched by
  this change — and the full suite at that revision printed `2081 passed` under both
  `--python 3.12` and `--python 3.14`. At the tree that merged,
  `5c5527ce58637d8165fefa1054e109dd9c84389c`, `uv run --python 3.12 … pytest` printed
  `2091 passed` on 2026-08-29, and CI was green on the squash `83b959e`. **Read any one
  of those counts as a reading of a suite with known intermittency, not as a property
  of it:** review lenses reproducing the same commands in their own clones hit a
  *different* intermittent failure at both revisions and under both interpreters, and
  CI's own run of the merged head reported three skips where the local runs reported
  none.
  Both review lenses reproduced the suite independently in their own clones.

▶ Next: measure the allow side of `Bash`, `Bash(*)` and `Bash(:*)` under a configuration
that gates on `allow`, then drop or stamp the unmeasured entries in
`_bash_allow_prefixes` and move `test_a_whole_tool_bash_grant_covers_every_engine` with
the result — `#606` carries the task. `#621`, `#631` and `#633` stay open; use `#243`
for the remaining runtime-specific workflow field exercises.

______________________________________________________________________

## Session — 2026-08-29 (runtime-adapter refresh, in a Codex session)

**Theme —** In a Codex session, PR `#635` (squash `2f2561f`) took Phase 5's `#236`
adapter/verification slice and narrowed `#243`. Upgrade now classifies generated Claude
and Codex bindings from their slug, description and shared workflow path; generated
bindings refresh, adopter-authored bindings are reported and preserved, and unsafe
filesystem shapes fail closed.

- **The stale premise was measured in a real adopter before design.** The measurement,
  premise correction and resulting scope are recorded on `#236`; design started from
  that record rather than the issue's original diagnosis.

- **Step 5 now follows the adopter's manifest.** `scripts/run_installed_tests.py`
  selects declared installed tests, applies engine remapping, refuses missing or unsafe
  paths, propagates pytest's status, and makes an empty declaration an explicit skip.
  The workflow no longer treats a directory-shaped pytest invocation as proof of what
  upgrade delivered.

- **The `#243` residue is runtime translation, not duplicated workflow doctrine.** The
  generated comparison covers the shipped adapters. The issue comment names the
  remaining native context, lane/delegation, compute/isolation, bootstrap and
  instruction-layer carriers. This session followed `session-start` and `upgrade`
  through their shared documents without a Codex workaround; upgrade's cloned-workflow
  re-read remained load-bearing.

- **The fallback panel changed the implementation at the boundaries it challenged.**
  It found unsafe link shapes, a selector that was not actually manifest-owned,
  historical fixtures coupled to current metadata, CLI branches whose exit semantics
  were unpinned, doctor-first import ordering, mixed-mode fail-open behavior, and
  preservation assertions that could not distinguish unchanged bytes from a replaced
  path. The exact-head dispositions and independent mutation evidence are on PR `#635`;
  the reusable lessons are in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `3032a2f47c2be34e49ea4148c0c5635ca99a83fd` on 2026-08-29 printed `2034 passed, 3
  warnings in 352.43s`; the merged squash is `2f2561f`.

▶ Next: take Phase 5's `#606` `.claude/settings.json` half: engine-path templating, the
startup-only `SessionStart` matcher, and the missing `kit_doctor` check for the
permissions block. Keep `#621`, `#631`, and `#633` open; use `#243` for the remaining
runtime-specific workflow field exercises.

______________________________________________________________________

## Session — 2026-08-28 (Claude's shipped lane permissions as repository policy)

**Theme —** PR `#632` (squash `e04e8ff`) took Phase 5's first slice: `#606`, decided as
three separate questions about `config/claude-lane-settings.json` rather than one bundle.
The record is
[`lane-permission-policy_2026-08-28.md`](../saved_plans/lane-permission-policy_2026-08-28.md)
with a committed evidence bundle beside it, every probe run under the lane's own trust
route against the pinned client.

- **The two grantable questions were granted, and the third is not grantable.** A lane
  gets `Bash(make test:*)` — `AGENTS.md` makes that the verification command and a lane
  was structurally refused it, so its first verification was always CI — and
  `kit_doctor.py` in both engine spellings, without which a lane editing any kit-owned
  file cannot refresh the manifest and its PR is deterministically red. `#627`'s
  `.claude/` guard is the client's own and no allow-list entry reaches it, so the
  decision is what the kit *says*: a lane doing kit-owned Claude-adapter work is not a
  supported case, and a parity change is split — lane for the runtime-neutral half and
  the Codex adapter, cockpit for `.claude/`.

- **Measuring the objection to the first grant is what reframed the slice.** `make` runs
  what the worktree's `Makefile` says and `Edit(**)` lets a lane write it — so the grant
  looked like unrestricted execution. It is, and so is what already shipped: under the
  shipped bytes with nothing added, a lane rewrote `scripts/pr_watch.py` and ran it,
  writing outside the worktree with an empty denial list. `Edit(**)` bounds file edits,
  not a process. The profile is now documented as task-scoping — fail-closed for a
  *confused* lane — rather than a security boundary, with the mechanism filed as `#631`
  rather than built here.

- **The mirror to Codex is the doctrine, not the grants.** `--sandbox` has no per-command
  list to receive one, and bounds the process rather than the command name — narrower
  exactly where the prefix list is weakest. `runtime-parity.md`'s "Command permissions"
  row carries that, and that the `.claude/` asymmetry is permanent rather than a gap to
  close.

- **The panel found a false claim of ours in each round, both times in prose beside
  correct work.** Round 1 killed "the grant is bounded to the one target" by running
  `make test mutation-test`; the delta pass then showed the *replacement* wording still
  invited a substring reading, the real bound being argv tokens. It also caught readings
  stated without their client and date in the document that argues for stamping them.
  One HIGH was declined by measuring the case the lens's own evidence could not supply.
  Dispositions are on the PR and the lessons in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **Filed this session:** `#631` (the profile grants execution it cannot bound),
  `#633` (is the profile a safety-critical file — the two lenses split on it).
  Occurrences added to `#510` (a wrapper reported exit 0 for a `make test` that failed,
  the pipeline's status being `tail`'s) and `#628` (the lane contract should carry this
  slice's two outcomes alongside that issue's own item, as one change to a
  safety-critical engine).

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `7a5ffe2eb8681ec78057d6bb6f74b1b9a682622e` on 2026-08-28 printed `2007 passed, 3
  warnings in 358.77s` on a quiet tree; the merged squash is `e04e8ff`. A delta-pass
  correctness lens reproduced that run independently in its own clone.

▶ Next: Phase 5 continues with `#236` and the `#243` narrowing — `#243`'s extraction has
landed (every workflow has a shared doc, adapters are thin on both runtimes), so what
remains is its residual and the rendered-adapter comparison `#236`'s adapter half needs.
`#606` stays open for its `.claude/settings.json` half: engine-path templating, the
`SessionStart` matcher, and the missing `kit_doctor` check for the permissions block.
`#621` stays open.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
