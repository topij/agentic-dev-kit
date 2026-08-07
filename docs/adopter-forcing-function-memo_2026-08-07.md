# Memo to the next devkit session — what cs-toolkit's Phase 0 established

> Written 2026-08-07 from inside cs-toolkit, immediately after Phase 0 merged
> there as `2ab63d255` (PR `in-parallel-oy/cs-toolkit#1869`). Everything stated
> as fact below names how it was established; anything inferred says so.
>
> **Scope discipline.** This memo is deliberately limited to *what the kit must
> do so cs-toolkit can proceed to Phase 3*. It is not a general improvement
> list. Items that would improve the kit but do not block the adopter are named
> as such and ordered last.

> ## Editorial note added 2026-08-08, on committing this to the kit
>
> **This memo is preserved as the adopter's account, not corrected into
> agreement with what the kit later found.** One of its recommendations is
> superseded, and it is left standing with this pointer because *why* it was
> made is the more useful record:
>
> - **§"What Phase 3 needs from the kit beyond bug fixes" and step 4 of
>   §"Suggested order" are SUPERSEDED.** They ask for `adopt` + `upgrade` shared
>   definitions to be promoted to a hard Phase 3 gate. That work was already
>   finished by `#330`: both shared definitions exist and both runtimes have
>   bindings. The memo's own §Receipts shows how the error entered — the claim
>   was taken from `kit-convergence-plan.md`'s Runtime-parity section, which had
>   been stale since `#330`, rather than from the filesystem. **The residue is
>   real but adopter-side:** cs-toolkit lists both docs in `not_installed`, so
>   Phase 3 installs them. Nothing is owed by the kit.
> - **§"First: settle `init.sh`" — its design question is settled, and by
>   dissolving rather than deciding.** The memo declines to pick between three
>   tracking models because an adopter's `init.sh` is "arguably *expected* to
>   diverge, since it encodes answers to the adoption prompts." That premise is
>   false: cs-toolkit's copy is **byte-identical to kit commit `7485512b`**
>   (2026-07-26), so all 852 differing lines are version drift and none are local
>   rendering. `init.sh` never writes to itself and nothing in the kit tells an
>   adopter to edit it. A tracked copy therefore reports `stale`, not
>   `locally-edited`, and clears when updated — so the permanently-red failure the
>   memo feared, and with it the case for a new role or a file split, does not
>   arise.
>
> Everything else in the memo stands and was independently re-verified kit-side.

## The headline: the kit is no longer waiting on cs-toolkit

`docs/kit-handoff.md` (last updated 2026-08-07) says Phase 3 "still waits on
cs-toolkit's Phase 0 and its fixer predicate, both that repo's PRs." **Both have
landed.** That sentence is now stale and is the first thing to correct.

| Gate | State | Evidence |
|---|---|---|
| cs-toolkit Phase 0 | **done** | merged `2ab63d255`, 2026-08-07T21:06Z |
| cs-toolkit fixer predicate (`done` → `converged`) | **done** | merged in `bfafe13b7` (PR #1866) — landed *after* the convergence plan's 2026-08-06 snapshot, which is why the plan still lists it as outstanding |
| Kit `#285`, `#286`, `#297` (plan's critical path) | **closed** | `gh issue view` on each |

So every gate the convergence plan named for Phase 3 has cleared. Phase 3 is
unblocked *on paper*. The rest of this memo is about why it should not start
tomorrow, and what to do first.

## What the forcing function produced

The convergence plan predicted this and asked for it to be checked:

> Most of the issues in "What blocks measurement" read as though they were found
> by *reasoning* about adopters rather than by upgrading one. […] using it as
> the forcing function should validate or refute them — and is likely to surface
> more. **Budget for that.**

**Validated.** One Phase-0-sized change in one adopter surfaced three kit issues,
one of which falsifies a stated premise of the plan.

- **[#360](https://github.com/topij/agentic-dev-kit/issues/360) — `init.sh` is in neither `KIT_OWNED` nor the manifest.** The file that *performs* the install is the one file `kit_doctor` structurally cannot report drift on. cs-toolkit's copy measures **852 differing lines** against kit `3761bec` while the doctor reports a clean bill of health. **This is the blocker.** Detail below.
- **[#359](https://github.com/topij/agentic-dev-kit/issues/359) — the `.codex/hooks.json` registration.** `$(git rev-parse --show-toplevel)` yields the empty string in a `.git`-less tree, so the command becomes an absolute path rooted at `/` and `python3` exits 2 — and a `PostToolUse` failure does not halt a session, so the hook silently stops firing. Reproduced directly. Narrow reachability (Codex only loads `.codex/` for a project it has already discovered), but the failure mode is the exact one the hook exists to prevent.
- **[#358](https://github.com/topij/agentic-dev-kit/issues/358) — kit-owned doctrine names engines by their kit-layout path in prose.** `fallback-review-panel.md` says `scripts/hooks/pr_followup_hook.py` at lines 61 and 68 while using `<engine-dir>` at line 331 of the same file. `test_no_shipped_kit_owned_file_hardcodes_a_bare_engine_path` scans this file and misses these lines because `_BARE_ENGINE_PATH_RE` anchors on `^\s*…scripts/` and both lines open with a markdown backtick or `**`. CodeRabbit independently found the same defect during cs-toolkit's review, from a different direction.

### The premise that was falsified

The plan says of the PR follow-through hook, under *The fork that matters*:

> It is also **the only divergence currently invisible to tooling.**

That is false, and `init.sh` is the counterexample. Worth correcting in the plan
rather than only in an issue, because the sentence is load-bearing: it is the
argument for why Phase 0 was the cheapest un-fork, and it implies the invisible
surface was fully enumerated. It was not.

## First: settle `init.sh` (#360 + #304) — before Phase 3, not during it

**Phase 3 *is* the upgrade, and `init.sh` is what performs it.** Running a
converge-the-install session against an 852-line-stale installer is the wrong
order on its own. It is worse than that, because
[#304](https://github.com/topij/agentic-dev-kit/issues/304) is open and directly
adjacent: *"init.sh destroys the kit's own AGENTS.md/CLAUDE.md markers, one-way,
and reports it as 'seeded'."* A known one-way destructive bug in the tool that
performs the upgrade, in the session whose whole purpose is to run that tool.

Treat #360 and #304 as one piece of work. They are the same file and the second
is a concrete instance of why the first matters: with `init.sh` untracked, an
adopter cannot tell whether its local copy has that bug or not.

### The design call this memo cannot make for you

Issue `#360` has a complication I deliberately did not resolve, because it looks
like a design decision rather than a fix. `init.sh` is unlike the other kit-owned
files: an adopter's copy is arguably *expected* to diverge, since it encodes
answers to the adoption prompts. So a plain `KIT_OWNED` entry would report every
adopter permanently `locally-edited` — trading an invisible problem for a
permanently-red one, which is the failure mode `#286` was just closed to fix.

Candidates, in the issue:

1. A role that expects local rendering, the way `adopter_owned` already carves out narrative docs.
2. Split the file — a tracked kit-owned engine plus an untracked rendered part.
3. Track it and document the expected-divergence state, so `differs` is reportable *and interpretable*.

**Recommendation: (2) or (3), and decide it before writing code.** (1) is
cheapest but it re-creates the `#286` ambiguity in a new place — `adopter_owned`
means "we will never tell you anything about this file," which for the installer
is the status quo with extra steps. What cs-toolkit needs is not "init.sh is
exempt" but "here is how far your installer has drifted, and whether that
matters."

### A concrete symptom to verify against

While reviewing cs-toolkit's Phase 0, CodeRabbit flagged an apparent mismatch
between `kit_doctor._still_a_skeleton` and "init.sh's seed guard." I did **not**
forward it as an issue, because it compared the doctor against *cs-toolkit's*
`init.sh` — 852 lines stale — and with the installer untracked there is no way
to distinguish a doctor defect from installer drift. **If #360 is fixed, this
becomes answerable.** It is a good acceptance test: after the fix, that question
should have a determinate answer.

## Second: #359, because Phase 3 will re-print the registrations

`init.sh` prints both hook registrations and writes neither (`#303`, deliberate).
That makes the printed text the operator's only instruction — so a Phase 3
session in cs-toolkit will surface whatever the kit's registration shape is at
that moment. Fixing #359 before Phase 3 means the adopter is told the right
thing once, rather than told the current thing and corrected later.

Note the constraint that kept cs-toolkit from fixing this locally: its
`.codex/hooks.json` was copied verbatim *because* matching the kit is the point.
Hardening it downstream would have re-forked the registration Phase 0 just
un-forked. **The adopter is deliberately carrying a known defect to stay
convergent.** That is the right call under the current goal, and it is also a
standing cost — it should not be left open indefinitely.

## Third: #358, cheap and worth doing in the same pass

Low severity — no broken command, since these are prose references. But
`fallback-review-panel.md` is the document an adopter reads *while reconciling a
fork*, which is exactly when a wrong path costs most. The fix is two lines
(`<engine-dir>/hooks/…`, `<engine-dir>/panel_prompt.py`).

The coverage question is the more interesting half: the existing guard cannot
catch this class without loosening an anchor whose docstring explicitly defends
its narrowness. The issue suggests matching the closed set of `KIT_OWNED` *file
paths* rather than the open-ended command shape — cheaper and more precise than
widening the regex.

## What Phase 3 needs from the kit beyond bug fixes

> **SUPERSEDED — see the editorial note at the top.** `#330` had already
> extracted `adopt` and `upgrade` and bound both runtimes; this section's
> recommendation asks for finished work. The install step it implies is
> adopter-side and is now recorded under Phase 3 in `kit-convergence-plan.md`.

**cs-toolkit declines `adopt.md` and `upgrade.md` today.** Verified in its
manifest's `not_installed` set. So a Phase 3 upgrade session working in
cs-toolkit has *no installed workflow document to follow* — it would be
improvising the very procedure the kit exists to standardise.

The plan already anticipates this under Phase 4 ("shared definitions for `adopt`
and `upgrade`, the slice the standing `#243` decision named — ideally before
Phase 3, though not a hard gate"). **Recommend promoting it to a hard gate.**
The reasoning that made it soft was sequencing convenience; the reasoning to
harden it is that Phase 3 is the first upgrade of the kit's only real adopter,
and doing it without a shared definition means the one run that would validate
the workflow does not exercise it.

## A verification pattern worth taking kit-side

Not a defect — a technique that worked, offered because the kit has no
equivalent and the hook is registered on two runtimes.

cs-toolkit's `tests/test_pr_followup_hook.py` resolves the hook path **from each
registration** and then executes it, rather than hardcoding a path. Two levels:

1. Parse `.claude/settings.json` / `.codex/hooks.json`, extract the path, assert it exists, sits under `paths.engines`, and carries the right `--runtime`.
2. Execute each registration's **command string verbatim** through `sh -c`, so the shell expansion itself is exercised — not a Python-side substitution of the placeholder.

Level 2 exists because level 1 alone passed while the expansion was broken;
CodeRabbit caught that. Mutation-verified: reverting either registration to the
old path turns 10 tests red, dropping `--runtime` turns 1 red, and an expansion
that yields empty turns 12 red.

**Why this matters to the kit specifically:** the property being defended is
`#303`'s consequence — registrations are hand-maintained forever, on every
runtime, in every adopter. A test that reads the registration is the only thing
that converts "someone edited one of two places" from a silent outage into a red
build. The kit ships the hook and prints both registrations but has no such
coverage of its own.

## What not to do

**Do not take adopter-local wins in cs-toolkit while this is pending.** The
tempting one is registering the SessionStart budget hooks in cs-toolkit's new
`.codex/hooks.json` — a few lines, closes the biggest remaining Codex parity gap
there. It is the wrong trade right now: cs-toolkit declined the kit's budget
engines and uses its own, so that change is pure adopter-local surface. Every
such patch is future drift against the stated goal ("cs-toolkit uses the devkit
rather than its own modified or historical copy of it"), and none of them touch
what actually blocks Phase 3.

If Codex SessionStart parity is worth doing, do it as the kit item the plan
already names, and let it reach cs-toolkit through the install.

## Suggested order

1. **#360 + #304 together** — decide the `init.sh` tracking model, then fix. Acceptance: the `_still_a_skeleton` question above becomes answerable, and `kit_doctor` in cs-toolkit can say something true about its installer.
2. **#359** — before Phase 3 re-prints registrations.
3. **#358** — same pass, two lines plus the coverage question.
4. ~~**`adopt` + `upgrade` shared definitions** (`#243` slice) — promote to a hard gate for Phase 3.~~ **SUPERSEDED — done under `#330`; see the editorial note at the top.** What remains is an adopter-side install, inside Phase 3 itself.
5. **Then Phase 3**, in cs-toolkit, as a normal PR through its review.

Items 1–3 are all "the forcing function found this"; item 4 is the plan's own
Phase 4 re-ordered on evidence.

## Receipts

Established by running the named command in the named repo, not carried from
chat:

- Phase 0 merge state and commit — `gh pr view 1869 --json state,mergedAt,mergeCommit`, in cs-toolkit.
- Fixer predicate — `git log -S` on `.claude/commands/nightly-fixer.md` and `pr-watch.md`, both landing in `bfafe13b7`; plus a repo-wide grep confirming no consumer reads the `done` key.
- Kit issue states (`#46`, `#273`, `#285`, `#286`, `#297`, `#303`, `#304`) — `gh issue view` per number.
- `init.sh` drift — `diff cs-toolkit/init.sh agentic-dev-kit/init.sh | grep -c '^[<>]'` → 852; absence from `KIT_OWNED` and from the kit manifest checked directly.
- cs-toolkit's declined set, including `adopt.md` / `upgrade.md` — its `kit-manifest.json` `not_installed` array.
- `#359`'s failure — the registration's exact command string run from a directory outside any git worktree.
- Doctor end state — `13 unchanged, 0 differ, 0 missing`, `✓ intact for this adoption — 22 file(s) declined`, exit 0.

One caveat on a claim I could not settle: during the Phase 0 session the *live*
Claude session kept invoking the pre-move hook path after the edit, at a moment
when that string existed in no file on disk. The observable is certain; the
mechanism (stale snapshot vs. both registrations active) is not established, and
I did not file it as a kit issue because it is plausibly runtime behaviour
rather than a kit defect. Flagged here in case a kit session can settle it —
it bears on how `#303`'s hand-maintained registrations behave in practice.
