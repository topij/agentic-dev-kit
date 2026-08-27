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

Last updated: 2026-08-27 — PR `#614` merged the config-owned lane approval policy per
runtime and the Claude trust route, with a Claude-produced writing-lane record; the
Codex writing-lane record is the next slice, then calibration.

## Latest session — 2026-08-27 (writing-lane approval policy and the Claude trust route)

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
  approval: `#615`, `#616`, `#617`, `#618`, and an occurrence on `#574`.

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

## Session — 2026-08-26 (triage forge provenance closes Phase 3)

**Theme —** PR `#599` changed the friction-triage forge path so its lifecycle operations
consume identifiers from preceding independently verified read-backs. The change
targeted locally self-consistent records that exchanged repository, commit,
pull-request, review, archive, or merge identities.

- **The PR added an enumerated provenance spine.** It connected commit read-back's
  observed commit and tree to push; verified remote-head read-back to pull-request
  creation; pull-request read-back's PR and head to `pr-watch`; the reviewed PR,
  observed head, reviewed head, and receipt to archive-sweep evidence; and that reviewed
  identity to merge intent and read-back. It also added pre-write rejection routes for
  foreign and future identifiers.

- **The review retained independent authority boundaries.** PR `#599` kept proposal
  content bound to its frozen authoritative source, derived semantic paths from merged
  configuration, kept tracker attempts as separate persisted objects, constructed
  duplicated evidence structures independently, and bound the ordered proposal set to
  a batch report. It did not permit pre-action records to contain identifiers produced
  by the pending action.

- **The fix-round evidence exercised transitions rather than isolated records.** Its
  positive cutpoints constructed action chains from durable predecessors. Its hostile
  mutations recomputed locally valid records while changing lifecycle identities. PR
  `#599` added semantic-oracle assertions for those mutations and added no workflow
  policy to a runtime adapter.

- **The merge satisfied the declared structural Phase 3 exit.** The delivered set was
  shared workflow definitions, thin runtime bindings, config-owned policy, explicit
  capability preflights, durable resume evidence, and cross-operation authority for
  `post-merge-systemize`, `session-start`, `wrap-up`, and `triage-friction-log`. The PR
  did not add a launcher, model/effort calibration, lane reconciliation, or downstream
  cs-toolkit adaptation.

▶ Next: create `feat/codex-environment-capable-launcher` from current `origin/main`.
Inventory supported Codex launch surfaces against the absolute descriptor/environment-
replacement contract, select an environment-capable mechanism, and obtain live lane-
isolation evidence before changing shared launcher guidance. Keep model/effort
calibration and downstream adapter reconciliation in later slices.

______________________________________________________________________

## Session — 2026-08-25 (triage integration preflights complete the shared phase)

**Theme —** The friction-triage pipeline now has config-owned, runtime-neutral input,
authority, artifact, resume, and outcome contracts, while the optional deterministic
engines remain honestly absent and runtime adapters remain thin.

- **Configuration and migration lead the contract.** `triage` owns its analysis tier,
  mode-separated active state, session-unique frozen/report patterns, optional engine
  names, commit subject, and PR draft policy. Refreshed `init.sh` adds the whole block or
  missing flat keys without replacing adopter values and refuses ambiguous YAML before
  writing. Shared `paths`, tracker, notification, state, branch, and model sections stay
  authoritative.

- **Approval and resume evidence are act-time gates.** Merged config, sandbox-aware
  atomic state, and the exact frozen inbox are required. The configured engine pair is
  atomic; both absent selects agent-executed LLM-only behavior and a partial pair stops.
  Scheduled approval requires notification send/thread read; an interactive run can
  degrade to the current session. Exact canonical payload digests bind approval,
  attempts persist before writes, and failed or ambiguous tracker/forge responses take
  destination read-back before any retry.

- **Partial success cannot lose the inbox.** Finalization waits until every approved
  tracker payload is verified, then sweeps only explicitly accounted blocks that remain
  byte-identical to the frozen snapshot. Parked, unmentioned, failed, ambiguous, edited,
  and window-added entries remain active. Test mode cannot write tracker, friction/archive,
  branch, commit, push, or PR state.

- **Parity is structural without pretending engine availability.** The Claude and Codex
  bindings translate invocation and mechanisms only. Runtime parity, README/getting-
  started, adoption/upgrade guidance, the changelog, installer fixtures, declaration-
  derived semantic tests, and hostile mutations carry the same contract. No Phase 4
  launcher, model/effort calibration, lane reconciliation, or downstream cs-toolkit
  adaptation is included.

▶ Next: create `feat/codex-environment-capable-launcher` from current `origin/main`.
Inventory supported Codex launch surfaces against the absolute descriptor/environment-
replacement contract, select an environment-capable mechanism, and obtain live lane-
isolation evidence before changing shared launcher guidance. Keep model/effort
calibration and downstream adapter reconciliation in later slices.

______________________________________________________________________

## Session — 2026-08-25 (parallel lane ownership returns to the kit)

**Theme —** Reusable lane identity, forge safety, and resume behavior now live in the
kit-owned engines and shared workflows, while runtime adapters remain thin and
cs-toolkit's repo-owned translation remains downstream work.

- **PR `#598` is the bounded shared-engine slice.** The read-only inventory compared
  cs-toolkit commit `4cf1ca914361b9912cd6bb1389e985d6e97ab3a0` (`#2086`) with its
  parent and classified reusable engine behavior separately from cs-toolkit policy and
  translation and unrelated application code. The downstream checkout was not edited.

- **The identity chain is durable and exact.** Headless activation, markers, and
  descriptors use canonical absolute roots; the shared launcher contract requires
  descriptor environment keys to replace inherited lane roots. Scope review and self-merge use the persisted branch/base/class
  and exact repository, PR, base, head, owner, and fork identity. A head change refuses
  before the forge write. Reconciliation stops on failed or malformed forge reads,
  requires the exact act-time report before classifying an operator lane as held, and
  checks local, cached remote-tracking, and live origin tips before terminalizing a lane.
  Non-force cleanup repeats its dirty guard in the Git removal itself, and relative
  session containers are anchored before any worktree write.

- **The upgrade boundary is explicit.** The engines, shared workflow definitions, and
  regression surfaces are individually kit-owned entries in `kit-manifest.json`; the
  `#598` changelog entry names the coordinated refresh set explicitly.
  Existing config already owns the protected branch, lane prefix, and per-lane merge
  class, so no config or installer migration is needed. cs-toolkit's operator-only merge
  policy and `CS_TOOLKIT_*` namespace did not move; its repo-owned engines require a
  later explicit downstream reconciliation PR.

- **The Phase 4 boundary remains honest.** This establishes the shared engine primitive,
  not an environment-capable Codex launcher or live runtime-isolation proof. Model and
  effort calibration and launcher mechanics remain planned.

▶ Next: create `feat/triage-integration-preflights` from current `origin/main` and use
the preserved starter in
[`codex-parity-plan_2026-08-23.md`](../saved_plans/codex-parity-plan_2026-08-23.md).
Build the config-owned semantic input matrix and init/upgrade migration before changing
the shared triage workflow; keep both runtime adapters thin.

______________________________________________________________________

## Session — 2026-08-24 (Codex doctrine validation and composed review evidence merged)

**Theme —** Phase 2 closed on trusted-client evidence rather than inference, then the
separate review-evidence workstream replaced the single-current-head receipt limitation
without forking review semantics between Claude and Codex.

- **PR `#592` merged the bounded live validation.** The controlled fixture separated
  client-supplied instructions, repository search, prompt guessing, nested precedence,
  and project trust. The conclusion stays scoped to its stamped client and revisions;
  interactive-TUI `systemMessage` visibility remains unsupported evidence.

- **PR `#593` merged composed review receipts.** A standing full-panel parent can now be
  extended by an exact-head `fallback:delta` pass. The shared engine binds ancestry,
  parent and final heads, changed paths, recorded lenses, and per-pass review caveats;
  malformed coverage fails closed while legacy receipts retain their prior behavior.

- **The review cycle produced material returns, then stopped.** The terminal panel found
  that Git rename detection could omit a safety-relevant source path and that composition
  could erase earlier override, unreadable-bot, or behind-head caveats. The bounded fix
  records rename source and destination and preserves, validates, and renders per-pass
  caveats.

- **The routing inventory did not justify another classifier.** The shared fallback
  doctrine and `panel_prompt.py` already carry full re-review for behavior, executed prose,
  record-prose delta passes, safety-critical lens floors, dispute escalation, exact-head
  invalidation, finding labels, and behavioral-evidence expectations. Runtime adapters do
  not own any of those semantics.

- **The remaining gap is precise.** Git can establish the parent, head, ancestry, and path
  set, but it cannot establish that arbitrary prose is non-operative or that posted draw
  verdicts are honest. A generic filename or path allowlist cannot distinguish record prose
  from executed prose when one Markdown surface can contain either. Issue `#32` remains the
  provenance umbrella; no tracker write was made and no proposed CS-Toolkit policy was copied
  into the engine.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `a23147f44ab9c405c24dced125becbb34bee2b95` on 2026-08-24 printed
  `1525 passed, 3 warnings in 202.06s`. `make test` in the same directory at
  `77577274792ac2652a7c618362a7be5bb17df83a` on 2026-08-24 printed
  `1539 passed, 3 warnings in 191.34s`. The warnings in these runs were pytest
  temporary-directory cleanup warnings.

▶ Next: run
`git fetch origin && git switch -c feat/post-merge-systemize-shared origin/main`, then
extract the bounded shared workflow and add the thin Codex binding. If a future
review-routing PR starts instead, its first deliverable must be a deterministic artifact
that proves record-only semantics without inferring them from filenames or prose;
otherwise keep the current full-review fallback and do not change `pr_watch.py`.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
