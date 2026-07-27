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

Last updated: 2026-07-27 — two of three adopter-facing `kit_doctor` lies fixed; the
third was built, reviewed, and deleted.

## Latest session — 2026-07-27 (#59 + #61.1 shipped; #61.2 built and reverted)

**Theme —** Fixed what the cs-toolkit adoption found in `kit_doctor`. The review panel
ran twice; round 1 found **four regressions against `main`** — my change making things
*worse* than the code it replaced: `--root` on a non-repo answering from the *enclosing*
repository, an inherited `GIT_DIR` overriding it, an unreadable manifest version
degrading from a loud crash to a silent `✓`, and `version: 2.0` going from accepted to a
hard `--generate-manifest` failure. **None were caught** by CI, by the suite as it then
stood (355 tests), by my own mutation run at that head, or by CodeRabbit.

- **`#65` merged (`a18f085`), closing `#59`.** The engines probe derives from
  `KIT_OWNED` instead of naming three files; a quoted `kit.version` no longer crashes
  the report, an unreadable one says so instead of advising a migration, and it exits 2
  because CI gates on that code.
- **`#61`'s hook-detection half was deleted, not shipped.** Asking git resolved the
  false negatives and introduced worse: answering from an *enclosing* repository when
  `--root` was not one, and honoring an inherited `GIT_DIR`. `_hook_dirs`'s **body** is
  byte-identical to `main`; the only change is 25 docstring lines stating the gaps as
  known — including a false POSITIVE the revert does *not* fix (`.git/hooks` is appended
  unconditionally, so a hook there reports installed even when git reads elsewhere).
- **`#66`, `#67` filed** — both `init.sh`, both found by the panel while reviewing
  something else.

**Decided**

- **The detector must resolve the same way as the writer.** Probing settled a
  disagreement the kit shipped with: `rev-parse --git-path hooks` *does* honor
  `core.hooksPath` and tilde-expands it; `git config --get` does not. `init.sh`'s
  comment asserts the opposite, and it installs an **inert hook** for a `~`-form path.
- **Blast radius, not round count — and say which you applied, in the PR.** A read-only
  report's worst case is a wrong message, so two panel rounds with decaying severity is
  proportionate. What that does *not* cover was written down too.
- **Rule 1 applied to a half, not a PR.** Two failed shapes for hook detection ⇒ revert
  that half and ship the rest, rather than tightening a third time or holding #59.

**Learned**

- **My claims keep being the defect.** A commit message attributed a defect to the
  reverted half when it *ships*; a PR table misstated `main`'s behaviour; and the
  wrap-up's own handoff block then miscited `#36`, overstated a test count, and got a
  GitHub rule backwards — all caught by a review lens, none by me. This is the third
  consecutive session where claim-vs-artifact drift is the most common finding.
- **An under-determined measurement talked me out of a correct rule.** `#68`'s
  squash-merge closed `#61` (reopened by hand) because I had weakened the standing
  "never write a closing keyword next to an issue number, even negated" rule after
  measuring one PR body as inert. That experiment varied **two** things at once —
  fenced-vs-inline *and* body-vs-commit — so it never established the thing I concluded
  from it. Three attempts to state the rule precisely have each been wrong; the
  conservative original would have prevented all three incidents. Stop deriving the
  mechanism (rule 1).
- **Two of my tests pinned nothing**, including the one whose stated thesis is "don't
  restate the list": it re-derived its expectation from the real `KIT_OWNED` with the
  prefix filter left out, so deleting that filter left the suite green.
- **A mutation harness must restore in a `finally`.** Mine died parsing pytest output
  and left the file mutated — `#50`'s hazard by a route `#50` does not describe.
- **CodeRabbit is incremental**, so a force-pushed or substantially rewritten PR keeps a
  stale review and reports nothing new. Its pass covered the pre-split head only;
  `bots_behind_head` recorded that rather than waving it through.

**Open, and owned by nothing yet**

- **Three `init.sh` defects** — `#62` (unquoted YAML stamping), `#66` (inert `~` hook),
  `#67` (the same hardcoded triple `#59` just fixed, where it *writes* bad config).
  `init.sh` has no automated test coverage and **no issue tracks that** — `#36` is the
  `pre-push` twin, and `#67`'s body miscites it for `init.sh`; both need correcting.
- **`#61`** — open (closed in error by `#68`'s squash-merge, reopened by hand): the
  hook-detection half, with the panel's
  evidence, the shape a correct fix needs, and a table of 9 `git config` value forms of
  which the current scan misparses 5.
- **`#47`** still the highest-leverage unbuilt thing, and it subsumes `#67`.
- **`#50`, `#60`** unchanged.

▶ Next: **file the `init.sh`-coverage issue, then `#67` + `#62` behind it** — three
`init.sh` bugs are open, the file has zero coverage, and nothing tracks that gap, so the
harness is the unblocking step and it needs a ticket of its own first. `#66` needs the
`#61` design call and should follow.

______________________________________________________________________

## Earlier session — 2026-07-26 (cs-toolkit Phase 1; kit lint; #60 attempted and reverted)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

