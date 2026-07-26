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

Last updated: 2026-07-26 — a second adopter adopted, and the kit's own fixes for
what that found regressed twice before being deleted.

## Latest session — 2026-07-26 (cs-toolkit Phase 1; kit lint; #60 attempted and reverted)

**Theme —** Adopted the kit into cs-toolkit (its ancestor), then fixed upstream what
the adoption found. **Everything the review panel caught had already passed my own
review and a green suite** — including two of my own fixes and two of my own tests.

- **cs-toolkit Phase 1 shipped** (`#1791`, merged, main green). Config surface +
  `init.sh` + manifest + `kit_doctor` + `kitconfig`, additive and inert. First reading:
  2 unchanged, 0 differ, 22 missing, 0 unknown. `#1792` open with the handoff memo.
- **Kit `#63` merged, closing `#58`.** `ruff.toml` + a CI lint step. On its **first run**
  it found a live crash the whole suite had missed: `yaml.YAMLError` in an `except`
  tuple with no `yaml` import (`F821`), so every config-resolution failure raised
  `NameError` from inside the handler written to report it cleanly.
- **Five issues filed from one adoption** — `#58`–`#62`. Two fixed; `#59`, `#61`, `#62`
  open.

**Decided**

- **Engines must be excludable as a DIRECTORY, and the kit must say so.** Adopters
  cannot be made lint-clean: cs-toolkit runs `line-length 120`, another runs 88, and no
  formatting satisfies both. `adopting-into-a-linted-repo.md` is the durable half of
  `#58`; the lint config is the smaller half.
- **Two failed tightenings ⇒ delete the mechanism** (rule 1, applied to my own work).
  `#60`'s fix probed upward for a config marker and escaped into a parent project —
  unbounded, then bounded and *still* escaping one level up in the shallowest layout.
  Removed rather than tightened a third time. **`#60` stays open** with both attempts,
  why a depth bound cannot work, and the `paths.engines`-validation shape that could.
- **Convergence beats formatting.** cs-toolkit is the ancestor and is AHEAD in places,
  so "adopt the kit's engine" is a regression there. A capability the adopter has and
  the kit lacks goes **upstream first**.

**Learned**

- **The panel's isolation pointed at the wrong repo, again — in both lenses, both
  rounds.** Each was placed on `main` with an empty diff. All four detected it because
  the prompt required reporting the path and diff stat; without that, four confident
  all-clears over nothing. Contract item 7 is load-bearing and its warning is not
  hypothetical.
- **A test can be precise about the wrong value.** My `#60` escape tests padded the
  fixture with a spare directory level, pushing the foreign config exactly one index
  past the bound — so they passed while the real case escaped. Mutation testing showed
  the bound was pinned *exactly*; it pinned exactly the wrong number.
- **Two of my tests pinned nothing.** One planted both markers, so the probe it named
  was never load-bearing — deleting it left the suite green. Both were in the block
  whose stated job was preventing that.
- **Regex guards catch the spelling you thought of.** The `datetime.UTC` guard missed
  `import datetime as dt` and a parenthesised multi-line import. CodeRabbit and the
  adversarial lens found it independently; a 340-test run did not.
- **Negating a closing keyword still arms it.** The PR body was edited to retract a
  closure claim and read "Does NOT close #60" — GitHub matched `close #60` and closed
  it on merge. Caught post-merge and reopened.

**Open, and owned by nothing yet**

- **`#60`** — reopened, unfixed, with the analysis. Three resolvers, not one.
- **`#59`, `#61`, `#62`** — `kit_doctor` cannot see itself; `kit.version: "2"` crashes
  it; `init.sh` stamps YAML unquoted.
- **`#47`** still the highest-leverage unbuilt thing; `#50` still casts doubt backwards.
- **`#63`'s last two commits merged unreviewed** — the panel covered `f40070e`, the head
  moved twice after. `--record-review` correctly refused a stale head, so no receipt
  claims otherwise. Recorded on the PR as an accepted risk, not a clean bill.

▶ Next: **`#59` then `#61`** — both are `kit_doctor` telling an adopter something false
on the first screen they see (`✗ contains no kit engine` while running from that very
directory; a traceback from a read-only diagnostic). Small, self-contained, and they
fix the tool every future adoption leans on. `#60` needs a design pass, not a patch.

______________________________________________________________________

## Earlier session — 2026-07-26 (adopter upgrades)

**Theme —** Ran the OpenKitchen upgrade end to end. **It worked**, and the doing of
it produced 17 issues — most of them not about the upgrade but about the kit's own
quality mechanisms disagreeing with each other.

- **5 PRs merged.** OpenKitchen `#256` (pre-v2 install → schema v2: config migrated
  with no value changed, pre-push hook finally *installed*, all 10 `differs` files
  refreshed), `#257` (`review.bots: []`), `#258` (doc sync). Kit `#43` (panel
  isolation doctrine) and `#49` (test suite detached from ambient config, closing
  `#48`).
- **`#48` blocked a one-value adopter config change**, and inverted the founding
  invariant: `pr_watch` resolves config at *import* time, so ~32 kit tests silently
  required the ambient repo to configure a review bot. Setting the truthful
  `review.bots: []` turned them red on assertions about *engine* behaviour. Fixed
  upstream, never patched in the adopter.
- **OpenKitchen has no reviewer at all.** CodeRabbit is installed but on the Free
  plan: 25/25 recent PRs have one walkthrough and **zero reviews**. So the fallback
  panel is that repo's **primary** reviewer, not a substitute for a bot that is down
  — and `review.bots` now says so.

**Decided**

- **A defect in a byte-identical kit file goes upstream, never into the adopter.**
  Applied 9 times on `#256` alone. An edited engine can never be replaced by a kit
  update, which is the whole property the upgrade exists to preserve.
- **The founding invariant is symmetric.** "Engines kit-owned, config adopter-owned"
  also means *a legitimate adopter config value must never break a kit-owned test*.
  That half was silently false.
- **Blast radius, not round count** — applied explicitly on `#49` (test
  infrastructure ⇒ stop at 2 panel rounds) and **stated in the PR**, including what
  stopping does *not* cover.

**Learned**

- **The kit's quality mechanisms cover different subsets and nothing checks they
  agree.** `KIT_OWNED` tracks 24 of 37 shipped files; the manifest tracks 0 test
  files; the suite covers 0 lines of `pre-push`. Every gap between them is where a
  file can be shipped, depended on, linked to, and invisible to all three — the root
  cause of `#36`, `#40`, `#41`, `#51`, and how a dangling doc link shipped. `#47` is
  the single check that closes the class.
- **Mutation testing can be silently poisoned.** A mutation preserving source
  *length* leaves stale bytecode that Python treats as valid, so a `git`-clean
  restore does not restore. The suite ran mutant code for minutes; grep found nothing
  because comments do not survive compilation (`#50`). **This invalidates mutation
  evidence gathered earlier in the session, including on the already-merged `#256`.**
- **My own claims were the most common defect.** Five-plus instances of
  claim-vs-artifact drift — two wrong numbers in a PR body, a bug report asserting a
  test did not exist when two do, an undercount of 3-vs-13, an invented "7 tests
  fail", and a false "untouched" claim that survived a round of corrections because I
  fixed the commit message and not the body. **Every one was caught by a reviewer,
  none by me.**
- **A fix round on the fix is still where the next bug comes from.** `#49` round 2
  found a MED/HIGH inside round 1's fix: a guard that *failed open by skipping*,
  because its skip predicate was computed with the function under test.
- **A review lens handed the wrong repo reports all-clear.** Both lenses on `#256`
  got a worktree of the *kit* while reviewing the *adopter*; both noticed and cloned
  the target themselves. Fixed as doctrine in `#43` — isolation must be **of the repo
  under review**, verified not assumed.

**Open, and owned by nothing yet**

- **`#46` — `pre-push` is all-or-nothing, and it BLOCKS cs-toolkit.** That repo's hook
  carries two guards the kit's does not (`auto/daily` protection, detect-secrets), and
  no config key can express either.
- **`#47`** — derive `KIT_OWNED` from the shipped tree. Highest leverage of the 17.
- **`#50`** — casts doubt backwards on merged mutation evidence.
- **`#44`/`#45`** — the merge gate cannot see a clean CodeRabbit review (it arrives as
  a comment), and cannot tell a structurally-non-reviewing bot from a pending one.
- ✔ **The friction-log inbox was graduated** (`triage-friction-log`, run inline in
  LLM-only mode since its engine is unvendored — `#6`). Three entries became `#54`
  (every verification claim must name the command that establishes it), `#55` (rule 1
  needs a tightening threshold) and `#56` (removing a mechanism requires enumerating
  what it rejected); three more needed no ticket because their fixes had already
  shipped in `#31`. Inbox 150 → 32 lines.

▶ Next: **cs-toolkit Phase 1 only** — install `config/dev-model.yaml` + `init.sh` +
`kit-manifest.json` + `kitconfig.py` + `kit_doctor.py` (additive, zero behaviour
change) to get a real `kit_doctor` reading, then stop. Defer the `pr_watch` swap
(the nightly fixer is in active development this week) and the `pre-push` swap
(blocked on `#46`). **Correction to the runbook**: the `done` → `converged` change
is in `.claude/commands/pr-watch.md` lines 11/13/39, **not** `nightly-fixer.md`,
which only delegates — following it literally finds nothing and the failure is a
silent infinite poll.

______________________________________________________________________

## Earlier session — 2026-07-26 (#26, overnight)

**Theme —** Built `review.fallback_panel`, then spent four rounds trying to make the
receipt's coverage claim verifiable *by the engine*, then deleted all of it. The
deletion is the result, not the failure.

- **#31 merged, closing #26.** `review.fallback_panel` is the primary substitute when
  a bot can't review: one isolated, fresh-context reviewer per lens.
  `fallback_commands` stays as the explicitly degraded one-lens mode. The lens
  *contract* — fresh context, raw diff, no author framing, execute rather than only
  read, mutation-test, report-don't-fix — is the part worth having written down, and
  lives in the new kit-owned `docs/agentic-dev-kit/fallback-review-panel.md`.
- **`pr_followup_hook` now names the panel.** It fires on every `gh pr create`/`ready`,
  which made it the most-read statement of fallback policy in the kit — and it was
  advertising the degraded mode.
- **#32 filed** — the design that would actually verify coverage (each lens recording
  its own receipt from its own context), with all four defeats written up.
- **#33 filed, and it is the one to read first.** `kit_doctor`'s drift self-check
  rehashes every kit-owned file, so *any* byte change to an engine fails it — which
  makes a mutation-testing run report every mutant as killed while nothing behavioural
  caught anything. Its proposed fix (a `driftcheck` pytest marker) is **not built**;
  only a prose warning in the panel doc ships.

**Decided**

- **Four tightenings of a matcher is the signal to delete it.** `safety-critical-
  changes.md` rule 1 says treat "we tightened the matcher" as a stopgap. I tightened
  it four times — source equality, lens names, a required roster, a counted roster —
  and each was defeated by the next round, the last by one decorated character in a
  field the caller writes themselves. What ships records the claim and labels it a
  claim.
- **Report, never gate — now for a fourth field.** `--lenses` joins `signal`,
  `bot_signal` and `coverage`. All four make an omission legible; none blocks.

**Learned**

- **Mutation testing this repo reports FALSE KILLS.** `kit_doctor`'s self-check
  rehashes every kit-owned file, so any byte change fails it — a run can report 100%
  killed while nothing behavioural caught anything. **I verified the mechanism
  directly** — disabling a behaviour outright fails only the manifest test. The
  *figure* "17/17 reported, 7 survived when excluded" is a reviewing lens's report,
  restated: the 17 mutants are enumerated nowhere, so treat it as attested, not
  measured. **This invalidates mutation evidence cited in #25, #28, #29 and #31
  itself** wherever the reviewer did not exclude that test. Contract item 5 now warns
  about it; #33 tracks the mechanical fix. (Those 7 survivors were themselves closed
  inside #31 — 7/7 caught by named tests once real coverage was added — so nothing is
  known to be live on `main` because of this.)
- **Two review lenses in one working tree corrupt each other.** One mutates files to
  test them; the other reads that as external corruption and `git checkout --`s it.
  Stopping one left a live mutant behind that silently disabled a guard. Contract
  item 7: isolated worktrees.
- **Deleting a check can reintroduce a bug it was masking.** The roster check was the
  only thing catching comma-as-punctuation in `--lenses`; removing it brought back the
  exact forgery the commit before it claimed to block, plus an honest input
  misrendering. **Fixed inside #31** (`_countable_lenses` counts entries that look like
  lens names, not prose) — recorded for the pattern, not as a live defect.
- **A silent `str.replace()` no-op let me assert a fix that never landed** — twice.
  Every substitution in this session's later rounds reports MISS rather than passing
  quietly.

**Open, and owned by nothing yet**

- **#32** — verifying lens coverage rather than self-reporting it. The honest version
  of what #31 tried.
- **#33** — the drift self-check's false kills. H severity and retroactive; its
  mechanical fix (a `driftcheck` marker) is unbuilt.
- **The autonomous self-merge path never displays review coverage.** `dev_session.sh
  merge` gates on `mergeable` alone, so the `review evidence:` line — the whole
  remaining value of #31 — is invisible on exactly the path
  `autonomous-session-playbook.md` argues review independence matters most on. Known
  and documented in `workflows/pr-watch.md`, deliberately not fixed at the end of a
  seven-round review; #32 is the real answer.
- **Adopter upgrades are written but not run.** `~/Documents/openkitchen-devkit-upgrade.md`
  and `~/Documents/cs-toolkit-devkit-adoption.md`. Held at the operator's request until
  #31 landed — it has now landed, so both are unblocked.

▶ Next: **run the OpenKitchen upgrade** (`~/Documents/openkitchen-devkit-upgrade.md`).
It is a real adopter on a pre-#8 install that cannot migrate its own config until
`init.sh` and `kitconfig.py` are copied in, and its pre-push hook is not installed.
cs-toolkit is the larger job — an *adoption*, not an upgrade, plus a fixer change from
`done` to `converged` that will otherwise wedge an unattended nightly loop.

______________________________________________________________________

## Earlier session — 2026-07-25 (Phase 3b)

**Theme —** Fixed #19 + #23 together, and then spent most of the session discovering
that **the fix rounds were more dangerous than the original diff**. Seven review rounds
on #25 alone; every one found something real; five of them found a defect introduced by
the previous round's fix.

- **#25 merged — #19 and #23 closed.** `summarize_review_bots` resolves each configured
  bot to *unavailable* (outage announced on a comment body **or** a status-check
  description — the surface that was invisible) or *pending* (a verdict still coming).
  Pending blocks the merge gate until it ages past `review.bot_pending_grace_minutes`;
  unavailable never blocks and is the action signal. **Nothing reaches `converged`** —
  that is the whole design, and it is what let both be fixed at once.
- **#28 merged — #10 closed.** The state_paths suite failed from inside a lane worktree
  because its fixture cleared every sandbox *env* signal and not the *cwd* one. The
  issue predicted a per-test audit would be needed; it wasn't — every cwd-sensitive test
  already chdirs itself. A mutation pass showed the fix makes the suite *stricter*:
  three tests had been passing by accidentally discovering the real repo root.
- **#29 merged — half of #27.** `review_bots.coverage` reports which commit each bot's
  last review actually saw, and `--record-review` records it as `bots_behind_head`.
  Verified against the real #25, where it reproduces the gap I had had to work out by
  hand an hour earlier. #27 stays open for the shape-change half.
- **#26 and #27 filed** from the friction-log inbox, both with concrete sketches.

**Decided**

- The anti-wedge property lives in `converged` alone. Every new signal feeds the merge
  gate, which already needs an explicit receipt — so a gate can wait, but the poll/fix/ack
  loop can always finish.
- **Report, never gate.** All three new fields (`signal`, `bot_signal`/`override`,
  `coverage`) make an omission legible at merge time and block nothing. The faithful
  version of each risks wedging a repo whose bot is permanently unavailable.
- **Stop patching a mechanism that keeps corrupting.** The `init.sh` marker migration
  produced **three** distinct config corruptions across three rounds, each while its own
  post-conditions passed and it printed success (the fourth round's finding was about
  the *replacement message*, not the surgery). It was deleted rather than patched again;
  `init.sh` now detects the gap and prints what to add.

**Learned**

- **A fix round on gate logic is where the next bug comes from.** Session-wide:
  **13 review rounds across #25, #28 and #29 — all 13 found something.** Seven of those
  findings were defects introduced by the *previous round's fix* (five on #25, two on
  #29), twice at HIGH. **No round on any PR came back empty**; #29's fourth pass found
  no HIGH or MEDIUM but still found four LOW, including a stale comment and a dead-
  argument trap. `safety-critical-changes.md` rule 3 already says to treat "the last
  round found nothing" as provisional — this session never reached that state at all,
  so the practical question is not when the findings stop but what blast radius
  justifies stopping anyway.
- **Stopping has to be calibrated to the blast radius, not the round count.** #25 was a
  merge gate — worst case, an unreviewed PR lands. #29 is a reported-never-gating display
  field — worst case, a wrong warning. Same review doctrine, different stopping points,
  and saying which one applies is part of the merge decision. The `never gates` property
  is what made that judgment available, and it was *proved* rather than assumed — by a
  review pass sweeping report shapes ad hoc, and in-repo by
  `test_review_coverage_is_reported_and_never_gates` plus the 32-combination matrix in
  `test_done_keeps_its_original_merge_authorization_semantics`.
- **Reading is not running.** Three defects were invisible to careful reading and obvious
  on execution — most sharply, CodeRabbit's pending check reports the zero timestamp, so
  the "unmeasurable age fails open" branch was not an edge case but the *only* path that
  bot ever took. The #19 guard was dead code for its own target, and only polling the
  live PR showed it.
- **Mutation testing found what test names asserted and test bodies didn't.** Five
  properties across the session were named in tests or claimed in a PR body and pinned by
  nothing: on #29, anchored author matching, newest-review-per-bot, and the `bots=`
  threading; on #25, the `init.sh` list-style branch and `grep -qi`'s case-insensitivity.
  Each was found by breaking the code and watching the suite still pass.
- **Every whole-file `grep '^  key:'` in a config migration is a bug in two directions**
  — it misses the key at another indent *and* matches a same-named key under an unrelated
  section. This change shipped one of each.
- **Removing a dangerous mechanism does not make its replacement safe.** After deleting
  the list surgery, the replacement *message* still told inline-list adopters to add a
  block item — walking them into the same corruption by hand.

**Open, and owned by nothing yet**

- **#27's other half** — invalidating a receipt when the diff changes *shape*, not just
  when the head moves. The cheap half (visibility) shipped; the faithful half runs into
  the same wedge tension as #19/#23.
- **#26** — the fallback panel. Run manually ~10 times this session (5 rounds on #25,
  4 on #29, 1 on #28), two fresh-context lenses per round. CodeRabbit completed only 3
  reviews across 17 pushed heads, so the panel carried most — not all — of the load; one
  of its 3 was the round that caught the "ACTION NEEDED" bug. Highest-value unbuilt thing
  in the tracker.

▶ Next: **#26** (make the fallback a panel spec). CodeRabbit was rate-limited on nearly
every head all day (3 completed reviews across 17 heads), so the panel carried most of
the review load — and it is still two manual subagent launches per round, ~10 rounds this
session. Two things this session learned belong in its prompt:
require the lens to **execute** the changed paths (three defects were invisible to
reading and obvious on running), and to **mutation-test** new branches (that is what
proved five separate properties were named by tests and pinned by nothing).

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

