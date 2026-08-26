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

Last updated: 2026-08-26 — PR `#599` merged and closed the structural Phase 3 exit; the
session preserved the environment-capable Codex launcher as the next sprint boundary.

## Latest session — 2026-08-26 (triage forge provenance closes Phase 3)

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

## Session — 2026-08-24 (Codex lifecycle enforcement bounded by exact strings)

**Theme —** PR `#590` merged the trusted-client lifecycle evidence and installer wiring,
while `kit_doctor` now makes only the deterministic claim the repository can support:
the configured object either matches the installer-emitted canonical form or it does not.

- **The architecture was narrowed in place.** The earlier shell-equivalence parser remains
  visible in branch history, but the live checker no longer approximates general shell
  semantics. Exact repository-owned command strings receive structural lifecycle checks;
  altered strings retain only the generic path-resolution result. Unsupported keys around
  an exact command report `unverifiable`.

- **The evidence boundary stayed explicit.** The controlled record preserves trusted
  `SessionStart` and `PostToolUse` execution, additive project-source behavior, definition
  trust behavior, and the observed output channels. Repository inspection does not claim
  project trust, current-definition trust, live execution, or interactive-TUI
  `systemMessage` visibility.

- **The hostile probes became durable behavioral tests.** The corpus rejects the
  accumulated command mutations without specifying a shell grammar. The fresh fallback
  panel then exposed alias-precedence, inert-comment, accepted-matcher, and exit-contract
  regressions; the fix rounds validate each present feature alias, remove noncanonical
  shell recognition, distinguish supported match-all structures from the printed form,
  and align the exit documentation.

- **The exact-string panel tightened the remaining surfaces.** Its findings scoped feature
  validation to repositories with an exactly identified lifecycle command, corrected the
  README's stale fail-closed claim for altered shell text, and aligned the exit-gate
  rationale with unsupported lifecycle object keys. The follow-up correctness lens then
  exposed the bare-Python TOML import and contradictory feature-alias precedence; the fix
  reports an unavailable TOML parser explicitly and mirrors canonical-key precedence. The
  next adversarial pass corrected the changelog's breaking-change axis and the README's
  unconditional bare-Python claim.

- **The runtime contract remains shared.** Installer guidance, `CHANGELOG.md`, and the
  live evidence record preserve the lifecycle boundary. The parity matrix now distinguishes
  structural safety-doctrine routing from the pending trusted Codex load evidence. The
  doctrine remains one runtime-neutral document, and its merge class makes this PR
  operator-merge.

- **The sprint plan now reflects the delivery boundary.** The parity declaration is
  delivered, while the safety and lifecycle phase remains active. Hook execution has
  trusted-client evidence; the shared safety-doctrine routing has structural coverage but
  no trusted Codex load evidence yet. `post-merge-systemize` remains queued behind that
  exit condition.

**Learned**

- **A positive result needs a syntax the repository owns.** Exact canonical objects have a
  stable mutation surface; purportedly equivalent shell spellings do not. Unverifiable is
  reserved for unsupported structure around an exact command; declining to classify an
  altered command is the honest shell-semantics boundary.

- **Alias type validation and value precedence are separate.** Every present spelling must
  be boolean, while canonical `hooks` wins when it appears beside deprecated
  `codex_hooks`; only the effective value establishes whether lifecycle hooks are disabled.

▶ Next: close the Phase 2 evidence gap in
`saved_plans/codex-parity-plan_2026-08-23.md` — live-validate that Codex work affecting
the merge-authority engines loads the shared safety-critical doctrine, and preserve the
repository-structural versus trusted-client boundary in the resulting record.

______________________________________________________________________

## Session — 2026-08-23 (the Codex parity baseline and its implementation roadmap shipped)

**Theme —** Codex support moved from scattered compatibility surfaces to an explicit,
tested parity contract. PR `#588` merged the assessed roadmap and its recommended starting
slice without declaring the remaining client-dependent behavior aligned.

- **The live contract is now the authoritative inventory.**
  [`runtime-parity.md`](agentic-dev-kit/runtime-parity.md) declares shared workflow paths,
  Claude and Codex adapters, intentional gaps, and companion ownership. Repository tests
  derive coverage from that declaration, preserve adopter-recorded omissions, and require a
  companion's declared owner to reference it.

- **The clearest incorrect Codex lifecycle behavior is gone.** Codex no longer invokes the
  Claude-specific `MEMORY.md` budget checker. The portable document-budget hook remains,
  and installer guidance pins its match-all shape, `/hooks` review-and-trust step, and the
  silent-skip diagnostic. The matrix leaves live trusted-session validation as a gap.

- **The roadmap is durable.**
  [`saved_plans/codex-parity-plan_2026-08-23.md`](../saved_plans/codex-parity-plan_2026-08-23.md)
  records the pre-implementation assessment and delivery plan. README,
  upgrade notes, `kit_doctor` ownership, and the release manifest carry the new contract to
  adopters.

- **Fallback review changed the shipped guards.** The panel's accepted findings led to
  adapter validation for incomplete declarations, exact path uniqueness, trusted decline
  handling, a non-empty gap rule, Codex-only gap coverage, explicit companion ownership,
  and retention of the silent trust-skip diagnostic. The final receipt is bound to
  `d03bcf3d84abce3a623ac7408d4cc04423f740fb` on PR `#588`.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `d03bcf3d84abce3a623ac7408d4cc04423f740fb` on 2026-08-23 printed
  `1367 passed, 3 warnings in 166.51s`; the warnings were pytest temporary-directory
  cleanup warnings. GitHub Actions run `32607084576` for that PR head completed
  successfully on 2026-08-23, observed with `gh run watch 32607084576 --exit-status`.

**Learned**

- **A parity label needs an independent relationship when it promises one.** A shared-only
  path could satisfy either `gap` or `companion`; declaring `loaded_by` and checking the
  owner's reference made the companion claim enforceable without duplicating the inventory.

- **Pending live validation belongs in the matrix, not in optimistic wording.** Repository
  structure establishes what ships, while trusted-client behavior remains a separate exit
  condition. Keeping that boundary explicit prevented the Codex SessionStart row from
  overstating the evidence.

▶ Next: implement the next slice in `saved_plans/codex-parity-plan_2026-08-23.md` —
live-validate Codex SessionStart and PostToolUse matcher, trust, timeout, and output behavior,
then use the evidence to close lifecycle gaps and design the enforceable shared
safety-doctrine binding.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
