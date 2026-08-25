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

Last updated: 2026-08-25 — PR `#598` delivers the kit-owned parallel identity boundary;
the triage pipeline remains the following Phase 3 slice.

## Latest session — 2026-08-25 (parallel lane ownership returns to the kit)

**Theme —** Reusable lane identity, forge safety, and resume behavior now live in the
kit-owned engines and shared workflows, while runtime adapters remain thin and
cs-toolkit's repo-owned translation remains downstream work.

- **PR `#598` is the bounded shared-engine slice.** The read-only inventory compared
  cs-toolkit commit `4cf1ca914361b9912cd6bb1389e985d6e97ab3a0` (`#2086`) with its
  parent and classified reusable engine behavior separately from cs-toolkit policy and
  translation and unrelated application code. The downstream checkout was not edited.

- **The identity chain is durable and exact.** Headless activation, markers, and
  descriptors use canonical absolute roots; descriptor environment keys replace
  inherited lane roots. Scope review and self-merge use the persisted branch/base/class
  and exact repository, PR, base, head, owner, and fork identity. A head change refuses
  before the forge write. Reconciliation stops on failed or malformed forge reads,
  requires the exact act-time report before classifying an operator lane as held, and
  keeps newer surviving branch work open rather than letting an older PR terminalize it.

- **The upgrade boundary is explicit.** The engines, shared workflow definitions, and
  regression surfaces move as a coupled kit-owned bundle in `kit-manifest.json`.
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

## Session — 2026-08-22 · evening (the review process assessed, and a session that kept reproducing the defect class it was assessing)

**Theme —** A planning session on why PR review costs what it does. The assessment found a
gap nothing on the tracker held and filed it. Then, writing up the finding, this session
produced the same defect three times — a claim generalised from one observation — and each
was refuted by something cheap that no panel had to run.

- **The proportionality machinery all governs re-runs; the opening pass has none.**
  Blast-radius classes, the executed/record discriminator, the delta pass, logged
  dispositions — every one is scoped to what a *fix round* owes.
  `fallback-review-panel.md` then closes the other door explicitly: a PR's initial review
  takes the full panel, never a delta pass. So a wrap-up PR of pure record prose opens with
  the pass a merge-gate change opens with. Filed as `#585`, with the three holes it has to
  survive named rather than waved at. Distinct from `#209` (within a PR's re-run chain) and
  `#420` (across sibling PRs), both of which are about a pass after the first.

- **The reviewer selection is not a choice anyone is making badly.** The bot reviews when it
  can, the panel runs when it cannot, and `fallback_commands` is degraded mode for a runtime
  that cannot isolate a lens — which Claude Code can, so it never runs here. Combined with
  `#372`'s quota shape, the session's *second* PR reliably gets the panel, and a session's
  second PR is reliably its wrap-up. The most expensive review a normal session buys is the
  one on the content with the least to break.

- **Doctrine carries to adopters; the economics do not.** `fallback-review-panel.md`,
  `safety-critical-changes.md`, `pr-watch.md` and `wrap-up.md` are byte-identical between
  this repo and cs-toolkit's install, so a fix to `#585` arrives there on its next
  `/upgrade` with no separate assessment. Whether the gap *costs* anything there is a
  per-repo fact and is unmeasured.

- **A paid reviewer tier is still metered, and past the allowance the behaviour is a
  console setting.** `#372` now carries the readings: a stated allowance per hour, and an
  over-limit path that bills, pauses, or stops depending on the usage-based add-on's mode,
  with any mode refusing once the spending cap is reached. That narrows what option 3 *is*
  without choosing it — paying makes the refusal a setting rather than removing it.

- **`#491` showed up live three times in one session**, in three different contexts: a
  configured incremental skip reported identically to an outage on a PR that had just
  configured the skip; the same on a later head; and once alongside *valid* coverage, where
  it was harmless. Followed literally the first time, it prescribes a two-lens panel over a
  YAML config file. Recorded there — the failure is not fail-open, it is fail-expensive.

- **Executed prose has no deterministic checker at all.** `make lint` is `ruff` and nothing
  else; there is no prose tool anywhere in the tree. So the surface where findings actually
  concentrate is checked only by a stochastic reviewer. Filed as `#586`, scoped to executed
  prose and explicitly *not* to record accuracy — `#120`'s territory, which no lint can
  reach, because those are truth defects rather than clarity ones.

- **In cs-toolkit:** `#2076` merged (`c5a6897f`) adding that repo's first
  `.coderabbit.yaml`; `#2078` carries its handoff update. Following `wrap-up.md` there hit
  `#505`'s mechanism with a second file pair — the workflow names `check_doc_budget.py`
  unconditionally, that adopter declines it deliberately and says so, and a *downstream*
  instruction depending on its output was silently skipped while the wrap-up reported
  success. Recorded there, with a third direction that issue lacked: the workflow could
  consult the `remedy:` field it already reads.

- **Filed this session:** `#585`, `#586`. Occurrence comments on `#491` and `#505`, and on
  `#372` — where an earlier comment of this session's was corrected in place rather than
  answered with a second one.

- **Verified:** no kit code changed this session, so nothing here rests on the suite —
  though `make test` in `/Users/topi/Coding/agentic-dev-kit` on this branch at `0a06365`
  printed `1362 passed`, which says the tree was green at handoff and nothing more. The
  claims above were established by reading rather than by running. The byte-identity of the
  four doctrine files was checked with `shasum -a 256` over both trees from
  `/Users/topi/Coding/agentic-dev-kit`; the absence of a prose linter by reading the `lint:`
  target and grepping the Makefile, `.github/workflows/` and `scripts/` at `fabf554`; the
  engine defaults behind three "absent" adopter config keys by reading `pr_watch.py`'s
  module constants, which is what retracted them as findings.

**Learned**

- **Three claims this session were generalisations from one observation, and each was
  refuted by something cheaper than a review round.** No refusals in a PR sweep read as
  "there is no quota" — refuted by an allowance line already in the reviewer's own output.
  One `Charged:` receipt read as "it bills rather than refusing" — refuted by a vendor docs
  page. And an adopter's absent config keys read as gaps — retracted by the engine's own
  defaults. Each reading was accurate; the error each time was treating one reading of a
  *configurable* system as a property of it.

- **What caught them is the argument for `#585` and `#586` both.** An allowance line, a
  docs page, and a module constant — none of them a panel. The expensive reviewer is not
  the only thing capable of finding this class, and the cheap things that found it were
  already present and unread.

▶ Next: `#372` — take the posture decision. It gates how much `#585` and `#586` are worth:
if the reviewer covers every head, the opening-pass gap is latent rather than live. It now
carries the metered-tier readings, the over-limit mode table, and the adopter comparison it
was missing, and a further occurrence has nothing left to teach it.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________
