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

Last updated: 2026-08-28 — PRs `#626` and `#625` merged the first real headless task on
the generalised launcher. The lane ran on this repository, terminalized `failed` at a
capability boundary, and that is the result: a Claude lane cannot write under `.claude/`
and cannot refresh the kit manifest, so it cannot complete kit-owned work end to end.
Phase 4 is closed; Phase 5 (`#606`) is next, and this slice handed it two decidable
inputs and one constraint it cannot decide.

## Latest session — 2026-08-28 (first real headless lane on this repository)

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
  own PR green, a failure *after* the work rather than before it. `#625`'s `.claude/` commit came from the cockpit for the
  first reason, and its manifest commit for the second.

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

## Session — 2026-08-27 (writing-lane approval policy and the Claude trust route)

**Theme —** PR `#614` (squash `d6b39c9`) added `parallel.codex_approval_policy`,
`parallel.claude_approval_policy`, and `parallel.claude_settings_profile` beside the
headless commands, and `scripts/launch_lane.py` now passes the declared policy in a
fixed argv slot per runtime, validated like the transports. On Claude the trust route
is `--setting-sources ""` plus the cockpit-owned profile through `--settings`: the
untrusted lane worktree's own settings, hooks, `.mcp.json`, agents, and `CLAUDE.md`
are not loaded, and the profile is the one settings source. The design matrix in
[`claude-writing-lane-approval-policy-design_2026-08-27.md`](../saved_plans/claude-writing-lane-approval-policy-design_2026-08-27.md)
preceded the code.

- **The policy is a declaration the engine validates, and the profile is one too.**
  An unrestricted or missing spelling refuses before an attempt record exists. The
  profile validator is structural: the `permissions` object is closed to its three
  rule lists, a `Bash` allow needs a literal command prefix, an edit tool needs a
  worktree-relative pattern. The child re-reads the profile under the parent's digest,
  and a `permission_denials` entry in the runtime's result terminalizes the lane
  `failed` — a denied write is never a success. `test_lane_launcher.py` names each of
  these with a recomputed mutant behind it.

- **The Claude writing-lane record exists; the Codex one does not.** The record in
  [`claude-writing-lane-live-validation_2026-08-27.md`](../saved_plans/claude-writing-lane-live-validation_2026-08-27.md)
  observed a lane on a synthetic repository perform a scoped write, commit, push, open
  a PR, and see it reviewed through the lane's own `pr-watch`, with denials read back
  from the runtime. It also states what the runtime does on its own at 2.1.247 — a
  read-only Bash class accepted under `dont-ask`, a file-system class under
  `accept-edits`, project hooks not executed under the trust route, and a push rule
  that bounds nothing after `origin` — so the allow list is the boundary on what a
  lane can do, not on what it can see. The Codex value is validated and unobserved;
  `runtime-parity.md` says so and the Codex cell did not move.

- **What the panel's dispositions were made of.** The panel's findings were
  claims asserted by inspection that a live probe refuted — a `-v` flag called
  read-only, an allow list called the whole boundary, a runtime class attributed to
  the wrong policy — and one structural gap (`additionalDirectories` passed through).
  Each fix was least privilege or precise disclosure; no mechanism was added across
  the rounds; the ones a finding prompted were filed as their own items. The stamped
  round reading is in the learnings document beside `#609`'s and `#611`'s.

- **Merged under the doctrine's class.** The launcher is in the safety-critical path
  binding, so the PR was held mergeable at `d2e1090` and merged on the operator's
  explicit authorization in this session. Filed this session, each on exact-payload
  approval: `#615`, `#616`, `#617`, `#618`, an occurrence on `#467`, and occurrences on
  `#574` (from `#614` round 15 and from the wrap-up PR's own round 1).

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at `d2e1090` on
  2026-08-27 printed `1960 passed, 3 warnings in 397.20s`; the merged squash is
  `d6b39c9`.

- **Housekeeping done:** the synthetic repository
  `topij/adk-writing-lane-synthetic-20260827` was deleted by the operator from the
  GitHub UI on 2026-08-27, after the session's token proved to lack `delete_repo`;
  `gh repo view` no longer resolves it.

▶ Next: in a Codex session, produce the Codex writing-lane record on the generalised
launcher: declare `parallel.codex_approval_policy: workspace-write` for the lane only,
run a lane that performs a scoped write and lands a PR through
`dev_session.sh pr-watch`, observe the sandbox and approval transitions Codex reports
(what `--sandbox` denies and how a denial reaches the receipt), and move the Codex
cell in `runtime-parity.md` only from that record. Then take `#605` (calibration,
`#255`). The first real headless task on the launcher stays after both — it has no
tracker item; the plan's earlier `#602` citation for it was a mis-reference (`#602` is
the `post-merge-systemize` binding bug).

______________________________________________________________________

## Session — 2026-08-27 (per-runtime launcher: Claude through `claude -p`)

**Theme —** PR `#611` generalised the Codex wrapper into one kit-owned per-runtime
launcher, `scripts/launch_lane.py`, run from a Claude Code session so the runtime under
test produced its own live record. Codex's argv and evidence route are unchanged and
pinned; Claude runs `claude -p --output-format json` with cwd from the process, the
prompt on stdin, and its single JSON result bound by digest.

- **Transports are declarations the engine checks.** Config owns, per runtime,
  `parallel.<runtime>_headless_command` and its `*_transport` keys; the engine owns
  the vocabulary each runtime implements and refuses any other declaration before an
  attempt record exists. The attempt and receipt request bind the runtime and its
  transports, so parent and child cannot resolve different templates. Everything
  `#609` established — descriptor seal, environment replacement, trusted lookup,
  child observation, nonce lineage, one-shot attempts, terminal receipts — is
  byte-for-byte the same path.

- **The live record moved the parity cell, and found the next slice's shape.** The
  Claude-produced record in
  [`claude-environment-capable-launcher-live-validation_2026-08-27.md`](../saved_plans/claude-environment-capable-launcher-live-validation_2026-08-27.md)
  observed the client, as the exec'd observer, report the descriptor's worktree,
  repository, branch, head, marker, and environment from inside the lane under hostile
  inherited identity. It observed no write or approval transition, and it recorded
  that a freshly issued lane worktree is an untrusted workspace to Claude, whose
  committed `permissions.allow` entries it ignored. `parallel-headless.md` states that
  limitation; the occurrence is on `#601`.

- **Design before code held, and the panel record shows it.** The design matrix in
  [`claude-environment-capable-launcher-design_2026-08-27.md`](../saved_plans/claude-environment-capable-launcher-design_2026-08-27.md)
  preceded the engine change. The panel found no defect in engine behaviour: round 1
  corrected an overstated sentence and filed the permission trust boundary, round 2
  found coverage gaps (`is_error` absent, the hardlink clause) and a test-name
  imprecision (answered by test code only, mutants recomputed and killed), round 3 was
  a dual-lens delta pass with zero findings. The stamped round reading is in the learnings document beside `#609`'s.

- **Merged under the doctrine's class.** The launcher is in the safety-critical path
  binding, so the PR was held mergeable at `f7c0111` and merged on the operator's
  explicit authorization in this session. Filed this session, each on exact-payload
  approval: occurrences on `#601` and `#149`; earlier in the same session, `#601`–`#608`
  and occurrences on `#466`, `#243`, `#255`, `#346`, `#236`, with `#341` and `#550`
  closed as resolved.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at `f7c0111` on
  2026-08-27 printed `1799 passed, 3 warnings in 318.71s`; the merged squash is
  `e0ef081`.

▶ Next: create `feat/writing-lane-approval-policy` from current `origin/main` and take
`#601`: add a config-owned approval/sandbox policy per runtime beside
`parallel.<runtime>_headless_command`, pass it mechanically in `scripts/launch_lane.py`,
and on Claude add the trust-establishment step the live record exposed (pre-trust the
lane worktree, a trusted settings profile, or `--bare` with the contract re-injected).
Write the design matrix first — action × approval state × durable evidence ×
authoritative observer — then obtain a writing-lane live record on each runtime: a
lane that performs a scoped write and lands a PR through `dev_session.sh pr-watch`.
Keep calibration (`#605`, `#255`) and the first real headless task (`#602`) in the
slices after. Stamp the final `make test` as a PR comment at the merged head and
record the round reading with the same `gh` command the learnings document uses.

______________________________________________________________________

## Session — 2026-08-27 (Codex environment-capable launcher merged)

**Theme —** PR `#609` delivered the bounded Codex launcher slice: a kit-owned wrapper
now applies an absolute worktree and replacement lane environment, independently
observes the child, and binds the request, attempt, process lineage, observation, final
text, and terminal receipt before success.

- **The supported surface is explicit.** `new --headless` accepts the descriptor when
  the runtime resolves to Codex through `--runtime codex` or
  `DEVKIT_RUNTIME=codex`. Claude remains supported for attended lanes; its headless
  parity cell is a declared gap because no unattended state-writing path has live
  runtime evidence yet.

- **Repository authority stays with shared policy and kit-owned engines.** The launcher
  replaces inherited lane/state values, removes repository overrides, resolves the
  runtime through trusted paths, observes worktree/repository/lane/state/branch/base/
  forge/process identity in the child, and fails closed on stale or foreign evidence,
  interrupted or partial launches, reused process identity, detached descendants, and
  an unbound success. Runtime adapters remain translation-only.

- **The live record is intentionally bounded.** The Codex-produced record proves the
  read-only isolation and receipt chain at its stamped client and revision. It does not
  claim writing-lane approval behavior, Claude headless behavior, model/effort
  calibration, downstream adaptation, or a general launcher framework.

- **The adopter and review surfaces moved with the engine.** The launcher is tracked as
  safety-critical kit-owned content, the changelog names the adopter refresh path, and
  the configured fallback panel disposition records the accepted positive/hostile pairs
  after CodeRabbit reported automatic review unavailable.

▶ Next: create `feat/claude-environment-capable-launcher` from current `origin/main`
and run the slice from a Claude Code session, because the live record must be produced
by the runtime under test. Generalise `scripts/launch_codex_lane.py` into a per-runtime
wrapper: keep the descriptor, scrub, child observer, one-shot attempt, and receipt chain
unchanged; move the runtime check and child argv into a config-owned per-runtime template
(`parallel.<runtime>_headless_command` plus each runtime's final-text transport —
`claude -p` reads the prompt from stdin, takes cwd from the process, and returns final
text on stdout with `--output-format json`). Write the design matrix and semantic/
mutation rows before code, obtain a Claude-produced live isolation record matching
`saved_plans/codex-environment-capable-launcher-live-validation_2026-08-26.md`, then
move the headless parity row's Claude cell from gap to the observed mechanism. Keep
approval policy and the writing-lane record (`#601`), calibration (`#605`), and `#602`
in the slices that follow, in that order. Stamp final `make test` as a PR comment at the
merged head, post the panel disposition, and record the review-round count so PR `#609`
remains the comparison baseline.

______________________________________________________________________

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

