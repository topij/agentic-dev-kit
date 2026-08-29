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

Last updated: 2026-08-29 — PR `#637` delivered Phase 5's `#606` cockpit slice: the
permissions advisory is templated on `paths.engines`, both runtimes drop the
`SessionStart` matcher, and `kit_doctor` reports an engine no allow rule pre-approves.
`#606` stays open for one unmeasured assertion the review surfaced.

## Latest session — 2026-08-29 (cockpit settings policy, in a Claude Code session)

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
  `test_pr_followup_hook.py`, which is the intermittent test recorded on `#393` and is
  untouched by this change; the full suite at that same revision printed `2091 passed`
  under both `--python 3.12` and `--python 3.14`, and CI was green on the merged head.
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

## Session — 2026-08-28 (first real headless lane on this repository)

**Theme —** PR `#626` (squash `2de16ed`) recorded the first headless lane run on this
repository rather than a synthetic one, and PR `#625` (squash `6e7143c`) landed the
`#602` binding fix the lane was given. The launcher and every shipped configuration
value stayed byte-identical for the run. The design matrix in
[`first-real-headless-lane-design_2026-08-28.md`](../saved_plans/first-real-headless-lane-design_2026-08-28.md)
fixed the observers and a total terminal-outcome table before the launch; the record in
[`first-real-headless-lane-live-validation_2026-08-28.md`](../saved_plans/first-real-headless-lane-live-validation_2026-08-28.md)
carries what each row returned, beside a committed evidence bundle.

- **The lane terminalized `failed`, and that is the finding.** It established for Claude
  what the Codex record could not: structured denial read-back with real denials in it,
  each naming its tool and target. The identity chain held throughout — worktree,
  branch, base, state root, policy and profile digest all bound by the receipt, with the
  cockpit's own `state/` untouched and the runtime's transcript independently confirming
  the lane's cwd. Under the trust route the lane ran the product default,
  `claude-opus-5` at effort `high`, read from that transcript.

- **A Claude lane cannot complete kit-owned work here, for two separate reasons.** It
  cannot write under `.claude/` — measured across `commands/`, `rules/`, `agents/`,
  `settings.json` and the bare directory, in a session that wrote `.agents/`, `docs/`
  and `.github/workflows/`, so neither the `Edit(**)` glob nor dot-directories is the
  mechanism (`#627`). And it cannot run `kit_doctor.py --generate-manifest` — measured,
  after a review lens objected that asserting it from the allow list used the very
  inference this run refuted — so after editing any kit-owned file it cannot make its
  own PR green, a failure *after* the work rather than before it. `#625`'s
  `.claude/` commit came from the cockpit for the first reason, and its manifest
  commit for the second.

- **Two smaller boundaries.** The read-only Bash class the shipped profile leans on is a
  property of command **shape**: a `for … do cat … done` loop and a `;`-chained compound
  were denied in the session that accepted plain `grep` and `cat` (`#628`). And the
  shipped `claude_headless_command` cannot resolve a user-local install, with no overlay
  reaching `parallel.*` (`#629`) — cleared for this run by a host symlink onto the
  trusted path, so the kit stayed unchanged.

- **The panel found real defects in the record, twice.** A correctness lens caught a
  present-tense claim about branch state that had gone stale before its own commit
  landed; the fix repaired two sentences and a delta-pass adversarial lens found a third
  in a file that fix never touched. Another correctness lens caught the `.claude/` claim
  generalising past its evidence, which was answered by measuring the gap rather than
  hedging — and the measurement killed a competing explanation that narrowing would have
  left standing. One Low was declined with the measurement that refuted it. The
  dispositions are on both PRs and the lessons in
  [`review-process-learnings_2026-08-24.md`](../saved_plans/review-process-learnings_2026-08-24.md).

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `77341814a66c478f9890e4b87592341800af0668` on 2026-08-28 printed `2006 passed, 3
  warnings in 432.92s` on a quiet tree; the merged squashes are `2de16ed` and `6e7143c`.

▶ Next: Phase 5, starting with `#606` — decide Claude's shipped lane permissions as
repository policy. This slice hands it two inputs a grant can settle (the lane can run
neither `make test` nor `kit_doctor.py --generate-manifest`) and one it cannot (`#627`'s
`.claude/` guard, which no allow-list entry lifts). Then `#236` and the `#243`
narrowing. `#621` stays open: this record met its intent by copying evidence out before
the cleanup boundary, but did not build the bundle contract that issue asks for.

______________________________________________________________________

## Session — 2026-08-27 (capability-tier calibration)

**Theme —** PR `#623` (squash `92a3c15`) calibrated `models.runtime_mappings` and
`review.fallback_panel.lens_compute` for Claude Code and Codex from live probes of the
pinned clients (Claude Code 2.1.247, codex-cli 0.149.1) and declared, per key per
runtime, whether each is mechanical or advisory. The design matrix in
[`capability-tier-calibration-design_2026-08-27.md`](../saved_plans/capability-tier-calibration-design_2026-08-27.md)
preceded the code; the record in
[`capability-tier-calibration-live-validation_2026-08-27.md`](../saved_plans/capability-tier-calibration-live-validation_2026-08-27.md)
carries every probe command and the observer field it read.

- **The retired claim was half right, and the half that was right stayed.** "Claude's
  delegation tool takes NO per-agent effort parameter" is true of the tool (it has
  `model`, no `effort`; a plain subagent inherits the cockpit's effort) and false of
  the runtime: the frontmatter `model` and `effort` of `.claude/agents/<name>.md` are
  applied and read back from the runtime's own subagent transcript, as is `--agents`
  JSON under the lane trust route. The kit now ships one definition per configured
  lens, rendered from `lens_compute.claude` by `panel_prompt.py --agent-definition`,
  seeded by `init.sh`, listed `ADOPTER_OWNED`, and pinned by tests to the generator's
  bytes. The generator refuses an effort level the runtime would drop with only a
  debug-mode log, quotes `model` (a `: ` or ` #` breaks or truncates bare YAML), and
  holds the lens name to a slug.

- **Codex's controls are on the argv and read back from the rollout.** `-m` and
  `-c model_reasoning_effort=<level>` reach `turn_context`; a misspelled `-c` key is
  accepted at exit 0 at the config default, an invalid level or model is refused by
  the API at exit 1, `--ephemeral` leaves no observer. `runtime_mappings` is advisory
  on both runtimes (no engine reads it) and its values now name what each client
  accepted: `claude.expensive: fable`, `codex.expensive: xhigh`.

- **The panel ran under the mechanism it reviewed.** Round 1's plain subagents ran at
  the cockpit's inherited `xhigh`; rounds 2–4, launched as the kit-owned lens agents,
  ran at the frontmatter's `high` — read from this session's subagent transcripts and
  recorded. Round 1 found a HIGH in the new generator (bare `model` broke the
  frontmatter), round 2 corrected the rationale for that fix and a consumer
  enumeration, round 3 found the seed's `sed` interpolation mangling `&` and `|`,
  round 4 found nothing by execution. Filed on their owning issues: `#574` (lenses
  fetching in the handed tree, one occurrence comment per round that showed it), `#255` (no adopter-side check for a
  stale lens definition — the doctor check that issue proposes).

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `d85e1bf35fdda9f71f14e787133e2ca2f0b90c20` on 2026-08-27 printed `2006 passed, 3
  warnings in 367.24s`; the merged squash is `92a3c15`.

▶ Next: run the first real headless task on the generalised launcher (no tracker item;
`#602` is the `post-merge-systemize` binding bug, not this). A Claude lane under the
trust route runs the product default model and effort unless the descriptor's argv
says otherwise — the wrapper still carries neither control, by design. Then Phase 5
(`#606`, `#236`, the `#243` narrowing).

______________________________________________________________________

## Session — 2026-08-27 (Codex writing-lane record)

**Theme —** PR `#620` (squash `58c5d7e`) recorded a Codex lane launched through
`scripts/launch_lane.py` with a fixture-only `workspace-write` declaration. The lane
performed the scoped write, committed after exact per-command approvals, pushed,
opened a ready pull request, and received a cockpit `dev_session.sh pr-watch` review
receipt. No launcher or shipped configuration changed; the shipped Codex approval
policy remains `read-only`.

- **The denial transport is not parity evidence.** The control lane observed an
  outside-worktree write denial, protected Git-metadata denials, and a network-blocked
  push, but Codex returned success and the `last-message-file` receipt terminalized
  `completed` with `terminal.permission_denials: null`. The record also observed that
  the exact state root was writable only when user config named it, user Codex config
  reached both untrusted lanes, and project Codex config did not.

- **The matrix moved only as far as durable evidence permits.** Cleanup removed the
  fixture receipts, rollouts, and raw captures named by the record's digests. The
  panel therefore required the capability promotion to be retracted. The record is a
  bounded historical account, not durable proof of Codex writing-lane parity.

- **Review disposition stayed scoped.** The retracted promotion received a full
  adversarial/correctness rerun. A later Low record-prose imprecision was logged as an
  occurrence on `#120`, without changing the reviewed head. The learnings document
  carries the stamped disposition reading. Filed this session on exact-payload
  approval: `#621` owns the missing durable-evidence handoff.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `37ad8eab0286c45aaf1ab1098e42e1da04561549` on 2026-08-27 printed `1960 passed, 3
  warnings in 365.20s`; the merged squash is `58c5d7e`.

- **Housekeeping done:** the operator deleted
  `topij/adk-writing-lane-synthetic-codex-20260827` from the GitHub UI after the
  session token proved to lack `delete_repo`; `gh repo view` no longer resolves it.

▶ Next: take calibration (`#605`, `#255`): calibrate both runtimes' neutral tiers,
declare mechanical versus advisory model/effort controls per runtime, and retire the
unsupported "no per-agent effort" claims. Keep the first real headless task on the
generalised launcher in the following slice; it has no tracker item, and `#602` is the
`post-merge-systemize` binding bug.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
