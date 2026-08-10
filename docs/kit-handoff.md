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

Last updated: 2026-08-10 — **two-thirds of `cluster:merge-gate` is closed** (`#190`, `#39`,
via `#407`/`1de29b3`). `#95` is the remaining item and now carries its own re-derived
groundwork as a comment, because its filed premise had moved. New: `#408`, `#409`, `#410`;
occurrence on `#399`. `#333` stays open and is now pinned by name in a test.

## Latest session — 2026-08-10 (the merge gate, and the fix rounds that became the subject)

**Theme —** `#190` and `#39` were one guard seen from two directions and shipped as one
change. The original defects were fixed in the first commit and never re-opened; what the
review found about *my own fix rounds* after that is the part worth carrying forward.

- **`#190` + `#39` closed** (`#407`, `1de29b3`). Neither is closable by counting: the
  rollup never says how many checks are still coming, so 2-of-5 and 2-of-2 are the same
  number. The fix is a persisted, head-scoped baseline carrying **the count it stands
  for**, whose stamp survives only while the rollup is that same size. It gates
  `merge_blockers` and never `converged`, so the watch loop stays runnable, and `done`
  tightens rather than loosens. Knob: `review.settle_grace_minutes`.
- **Both defects were re-derived through `main` before any fix**, with their preconditions
  asserted rather than assumed — `#190`'s receipt *is* valid for the head, `#39`'s
  `settling` *has* already dropped.
- **The panel was the gate throughout** — CodeRabbit was rate-limited across most of the
  branch, and its one completed review was of an early head, which the engine's own
  `bot_review_coverage` reported rather than letting the check status pass for a review.
  Read the `## Fallback panel — round N` comments on `#407` for what each round found;
  every round but the last found something real.
- **Filed:** `#408` (mutation testing under concurrency yields both false kills and a
  false *clean pass*), `#409` (`render` names a cause it cannot know on the shrink path —
  flagged independently by both lenses, rounds apart), `#410` (a required-field addition
  silently hollows test fixtures). Occurrence comment on `#399`; groundwork comment on
  `#95`.

**Learned**

- **A fix round for a gate became the next round's subject.** Round 6 closed a fail-open
  that credited settle time across a rollup dip — that hole was original, not introduced.
  Its fix was a **permanent wedge**, found by round 7. That fix added a required field,
  which hollowed test fixtures — found first by the harness as survivors, then again by
  round 8 after my sweep missed more. Both regressions are now permanent harness mutations,
  so each is pinned as a thing that must fail. `safety-critical-changes.md` rule 3 names
  this pattern; the loop ending only once the chain ran out is the friction-log entry.
- **The anchor was the mistake, not the disjunct.** Both failures came from anchoring on
  `max_total`: growth past it let a stamp survive a dip, and `settling` inherited its
  one-way ratchet, so a check that disappears for good wedged the gate forever. Comparing
  against the **previous poll's count** has neither failure. What held changed what the
  clock compares against, not the condition that reads it.
- **A negative assertion is evidence only if the same fixture can produce the positive.**
  Three fixtures kept passing after `total` became required, one having stopped exercising
  its function entirely — none found by reading. The repaired tests lead with a positive
  control, and the control was itself verified by deleting it and watching the test pass
  vacuously. `#410`.
- **Three completeness claims of mine were wrong, all about sweeps.** One because the grep
  was case-sensitive against a differently-cased site. Naming the command is not the fix;
  pasting the residual output is.
- **A green mutation run is not evidence without reading which test failed.** The harness
  first scored a kill that was ruff failing at `lint` before pytest ran, and later reported
  three false kills under concurrency while a lens independently hit the opposite — a
  genuine mutation reporting a clean pass. `#408`.

**Open, and owned by nothing yet**

- **`#95`** — the remaining `cluster:merge-gate` item. Its issue body predates the current
  code; the groundwork comment carries what the transports actually expose and why the
  obvious discriminator is insufficient. Read that before the body.
- **`#333`** — its ratchet wedge predates this work, is untouched, and is now pinned by
  name in a test so nobody credits `#407` with it or "fixes" it by loosening the settle
  clock, which is the direction that reopens `#39`.
- **`#408`, `#409`, `#410`** as filed. `#410` proposes a panel-contract amendment.
- **`#399`'s `adopt.md` half**, plus a third occurrence recorded on it — this one in the
  cockpit's own session, from a `cd` into a *scratchpad* rather than a second tree, which
  is narrower than the rule as written covers.
- **`#402`, `#403`, `#404`, `#405`, `#395`, `#388`, `#358`** unchanged by this session.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**

▶ Next: **`#95`** — the check-name trust boundary, on its own branch and its own panel.
Start from the groundwork comment on the issue, not the issue body: `_match_bot` already
has the `anchored=` parameter the body asks for, so the thing to attack is the trust
argument at its check-name call site. `gh pr checks --json` exposes no app identity, and
the `workflow` field discriminates check *runs* only — a commit status posted via the
statuses API bypasses it — so the class fix needs REST `app.slug`/`creator.login` plumbed
through both transports.

______________________________________________________________________

## Session — 2026-08-10 (the install-path lane, and a gate the panel kept breaking)

**Theme —** four install-path items shipped in one PR. The work was small; the review was
not, and what it found is the more useful half. The `#398` template gate drew a defect in
round after round, every one inside the previous round's remediation.

- **`#397` closed.** `init.sh`'s `--no-clobber` summary aborted under `set -eu` between
  the file list and the four echoes explaining the action. Swept `init.sh` for the shape:
  no other instance. The similar lines in `dev_session.sh` and `reconcile_sessions.sh` are
  a **different shape and not this bug** — a standalone `while` whose last body statement
  is a falsy `&&` chain exits 0 under `set -e`; only one ending a **pipeline** exits 1.
  Verified in both directions, which is what stopped a false ticket against those files.
- **`#380` closed, acceptance met.** `init.sh` prints a Codex SessionStart registration
  and the kit's own `.codex/hooks.json` carries it. The fire-check ran in a **trusted**
  session with no bypass flag; the issue carries the before/after. Settled there too:
  `SessionStart` takes **no** `matcher` key (Codex accepts Claude's shape and then never
  fires), a project-level `.codex/hooks.json` **is** read, and project trust is **not**
  hook trust — the probe repo had `trust_level = "trusted"` and the hook still did not run.
- **`#398` closed.** The template refresh is gated on the declared set, keyed on
  `kit_commit`. `adopt.md`'s bullet had the same shape via its rationale rather than its
  instruction.
- **`#399` partly.** The cross-tree rule is in `AGENTS.md` and `upgrade.md` is bound to it
  — `$REPO`/`$KIT` in Step 0, `$REPO`-anchored writes, a `cd` that fails the run.
  **`adopt.md` is not hardened** and the issue stays open for it.
- **Filed:** `#402` (`kit_doctor`'s four manifest reads catch two exception types; a deep
  JSON array crashes the diagnostic), `#403` (the record-prose carve-out has no disposal
  for a claim that is *false* but marked imprecision), `#404` (the panel's scratch
  namespace collides on a same-head re-run), `#405` (nothing checks a round was posted —
  two were not, while four commits cited them). Occurrence comments on `#77` and `#399`.

**Learned**

- **A predicate restated where nothing executes it does not converge by patching.** The
  `#398` gate reimplements manifest semantics in doc-embedded Python, next to
  `kit_doctor.py`, which owns that schema. Read the `## Fallback panel — round N` headers
  on `#401` for the sequence; each fix drew the next defect. `init.sh`'s own
  `register_pr_hook` comment already names this pattern and its only known ending —
  delete the predicate, do not guard it better — and it went unrecognised for most of the
  loop while each round's fix was treated as the last one needed.
  **The structural fix is Step 2 asking the engine instead of re-deriving**, which needs a
  `kit_doctor` surface that does not exist; it gets its own PR.
- **Two guards were the same class one type over.** The manifest read enumerated exception
  types twice and was holed twice — `JSONDecodeError` escaped, then `RecursionError`
  escaped `(OSError, ValueError)`. `except Exception` closed the class. `#402` is the same
  enumeration, unfixed, in the engine.
- **A fix round can over-apply a finding as easily as under-apply it.** Round 2 found that
  the gate's refusal did not stop the workflow; the fix made *every* refusal stop it, which
  blocked the config migration for any adopter carrying a deliberate local patch — a state
  `record_install_manifest` writes by design. The narrower reading was available and not
  taken.
- **A `trap … EXIT` bounds damage in time, not against a concurrent reader.** A background
  job held a temporarily-lowered doc budget while `git add -A` ran for an unrelated commit,
  and the bad value merged into the branch before being restored. The trap fired correctly;
  the window was simply open. Caught by `git status`, not by any test — the budget check is
  warn-only, so a nonsense budget fails nothing.
- **The panel's own doctrine bit back, correctly.** A record-prose finding marked
  *imprecision below HIGH* must be **logged, not fixed** — and the rule says "as the lens
  marked it" precisely so the author cannot relabel to justify the cheaper disposal. I
  relabelled; two lenses caught it independently. `#403` is the gap that made the choice
  genuinely hard: the claim was *false*, and logging a falsehood ships it.

**Open, and owned by nothing yet**

- **`#399`'s `adopt.md` half** — it clones to the same second tree in Step 0 and Step 1
  sends you to read inside it, with no `$REPO`/`$KIT` binding.
- **`#402`, `#403`, `#404`, `#405`** as filed. `#403` is the one worth a decision rather
  than a fix.
- **`#395`, `#388`, `#358`** unchanged by this session.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**

▶ Superseded by the block above, kept for the reasoning: **`cluster:merge-gate`** — `#190`
and `#39` together (one guard, one change), then `#95` separately. `#190` and `#39` are now
closed; `#95` remains and is the live `▶ Next:`. The reasoning worth keeping is why the
three were ever grouped: they are `pr_watch.py` defects that nothing in `#401` touched, and
the cluster was never gated on the install-path lane.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

