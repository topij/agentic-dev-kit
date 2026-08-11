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

Last updated: 2026-08-11 — the friction-log inbox is graduated (`#424`, `463dc26`). Filed this
session: `#419`, `#420`, `#421`, `#422`, `#423`, `#425`. The cs-toolkit refresh is still the
outstanding thread, unchanged from the block below it.

## Latest session — 2026-08-11 (the sweep, and a record claim that could not be repaired)

**Theme —** a routine graduation sweep. The routing went clean; every defect the review found
was in the record prose *about* it, including one that turned out to have no correct value.

- **Inbox graduated** (`#424`, `463dc26`). Eight entries, all accounted for: new issues
  `#419` (mutation in the authoring loop), `#420` (the panel is per-PR, so a split change
  pays N times), `#421` (init.sh's awk scanner and the apostrophe), `#422` (extend `#54` to
  predictive claims), `#423` (extend `#54` to out-of-repo evidence); occurrence comments on
  `#305` and `#313`; and one entry already filed as `#417`.
- **Reading the tracker before drafting moved two entries off the new-issue path**, the same
  step the 2026-08-08 sweep recorded as changing its own routings. `#305` already carried the
  panel-loop entry's proposal as its direction 3, and `#313` already reproduced the
  `gh --limit` defect. Each comment carries what the entry *added*; filing either fresh would
  have fragmented a family that already holds `#209`, `#305`, `#211`.
- **`#128`'s interactive path was exercised.** The operator was in-session, so the DM was not
  the only review surface — but `state/` and `reports/` are gitignored, so the approval record
  (proposals, decision, snapshot digest) went into the graduation marker, which is `#128`'s
  point 2 and the half that makes the exception honest.
- **Filed:** `#425` (this skill's Step 6 deletes the state file, that delete can be refused,
  and auto-detect keys on file *existence* — so a refused cleanup leaves a run that falsely
  auto-resumes, and can suppress every scheduled sweep after it).

**Learned**

- **A record claim can have no correct value, and the doctrine assumes one always exists.**
  CodeRabbit found the frozen-inbox digest command was working-tree-relative and did not
  re-derive its own digest. The repair then named the wrong answer a reader would get — false
  against the tree that shipped it, because the repair edited the paragraph being hashed. Both
  panel lenses found that independently. It could not be corrected: the sentence naming the
  digest sits inside the region the digest hashes, so every value written invalidates itself.
  Deleted the specific, kept the caveat. `#403` is open about the disposal gap this lands in
  and its framing assumes correcting is always available; the occurrence is recorded there.
- **Departing from a lens's label is legitimate; doing it silently is what failed before.**
  Both lenses marked that finding MEDIUM/imprecision, whose record-prose disposal is *logged,
  not fixed*. Logging would have shipped a permanently false claim, so I departed — and said
  so on the PR rather than relabelling the finding, which is the half the earlier instance on
  `#401` got wrong. Note the direction: the departure **cost** an extra review round rather
  than saving one.
- **The defects landed in the hand-written half, not the judgement half.** All three review
  findings were in record prose a deterministic finalize engine would generate; the routing,
  the two comment-not-issue decisions, and the verbatim archive sweep were re-derived by both
  lenses against live GitHub state with no findings. Recorded on `#6` as priority evidence —
  the parts that keep breaking are the derivable ones.
- **CodeRabbit reviewed the first head and was rate-limited on every one after**, again. The
  panel carried the rest and the receipt records that its last review covered `6ac50e2`, not
  the merging head. `#372` is the posture decision this keeps costing.

**Open, and owned by nothing yet**

- **`#425`** — the state-file gap above. Its directions (1) and (2) compose and need no engine,
  so it is actionable before `#6` lands.
- **`#403`, `#140`** each carry a new occurrence from this session's panel. `#403`'s is the
  substantive one: a claim that is false and *unrepairable* is outside its three proposed
  shapes, and it sharpens shape 1.
- **`#399`** gained a third occurrence, and it is single-repo — a scratchpad `cd` persisting
  into the next command, with no second tree in play. The rule's statement in `AGENTS.md`
  covers it; its heading ("Working across two trees") does not, so it reaches only readers who
  think they are doing two-tree work. Cheaper to fix than `#399`'s `adopt.md` half and
  separate from it.
- **`#378`** has a second miscount noted on it: the 2026-08-08 marker calls itself the tenth
  sweep where `#198` and the archive's own sections put it eleventh. The 2026-08-11 marker
  carries no ordinal, deliberately.
- Everything listed as open in the 2026-08-10 block below is unchanged by this session.

▶ Next: **cs-toolkit kit refresh** — carried forward untouched from the 2026-08-10 block
below; read its bullet there for the verified preconditions rather than trusting this line.

______________________________________________________________________

## Session — 2026-08-10 (the check-name trust boundary, and a fix worse than the bug)

**Theme —** `#95` shipped. The fix itself is small; what the panel found *inside my own
work* is the part worth carrying. Round 2 found a CRITICAL I had introduced that was
strictly worse than `#95`, and round 4 found that the new guard's own tests were
scaffolding.

- **`#95` closed** (`#412`, `247d2c8`), and with it `cluster:merge-gate`. A check's *name*
  is chosen by whoever created the check, so on a same-repo PR it is not a trust
  boundary; the **cancel** now requires the creator identity GitHub records (`app.slug`
  on a check run, `creator.login` on a status context), which a workflow cannot forge.
  The **report** deliberately does not, so the signal to run the panel never goes
  missing. New optional knob: `review.bot_app_slugs`, ordinarily absent.
- **Safe on by default because the cancel only ACCELERATES the grace clock.** An
  unresolvable identity costs at most `bot_pending_grace_minutes`; a terminal outage row
  (`#23`'s own shape) costs nothing, having no pending entry to cancel. Fail-closed and
  bounded, never a wedge — which is why it needed no opt-in.
- **Two premises in the issue's groundwork were wrong**, and re-deriving them changed the
  design: the combined `/commits/{sha}/status` endpoint carries **no `creator`** (only the
  plural `/statuses` does), and a `workflow`-field discriminator would have looked like a
  fix while leaving the reviewer's actual surface open. Both re-derived against live
  payloads, not read off the issue.
- **Filed:** `#413` (kitconfig parses flow sequences but turns flow mappings into
  strings), `#414` (`_gh` translates only `TimeoutExpired`), `#415` (`_route_http`
  misroutes when one route fragment prefixes another), `#416` (the panel's cockpit-built
  worktree is *linked*, so a lens establishing base against the remote writes into the
  operator's `.git`), `#417` (a test that mocks the unit under test — the pattern below).

**Learned**

- **My fix was briefly worse than the bug.** The REST identity read called the plural
  statuses endpoint with the object-wrapped reader; it raised, and `fetch_check_details`
  degraded to `([], "unavailable")`, discarding **every** row and switching `#19`'s and
  `#23`'s guards off in exactly the outage case they exist for. `record_review` already
  names that state "the SILENT bypass, and the worse of the two". Found in round 2, on a
  supported backend, in the engine that decides a PR is safe to merge.
- **A test that mocks the unit under test cannot see that unit's defects.** It recurred
  through this PR: the reader whose shape assumption was wrong was itself the mock; then
  the helper the new guard depends on; then a path with no test at all. Each left a green
  suite. Once the shape was named it was cheap to hunt — the later ones were found by
  looking for it rather than by review. The move that works is hardwiring the *real*
  unit's body to a constant, which is strictly stronger than mutating the branch under
  review. `#417` enumerates the instances and proposes the amendment.
- **A mutation sweep's own restore step can invalidate it.** The harness restored the
  engine with `git checkout --` before applying each mutation, which reverted files
  copied in from the working tree — so mutations never applied and would have read as
  survivors. Caught only because the harness asserts its anchor is present before
  trusting a result. The fix is to commit the state under test in the throwaway clone
  first.
- **The panel's stopping rule worked here, and the loop ended on the subject.** Severity
  fell every round and round 5 was a clean pass from both lenses — the first of
  `fallback-review-panel.md`'s three terminal states, not "the findings got small". But
  rounds 3–5 found nothing wrong with the previous round's *fix*, and their findings were
  about my remediation's coverage rather than about `#95`. That is the second occurrence
  of the state the friction log's 2026-08-10 entry describes.
- **CodeRabbit reviewed the first head and was rate-limited on every one after**, so the
  panel carried rounds 2–5 and the receipt records that its last review covered
  `d3140f9`, not the merging head. `#372` is the posture decision this keeps costing.

**Open, and owned by nothing yet**

- **`#417`** proposes a panel-contract amendment; `#410` proposes another. Worth deciding
  together rather than separately.
- **`#416`** is mine to have caused: `fallback-review-panel.md` step 2 has the cockpit
  build a linked worktree while the contract asks the lens to establish base against the
  remote. Lenses in rounds 4 and 5 each disclosed hitting it independently; impact was
  verified nil from the cockpit (`git reflog show refs/remotes/origin/main`, kit root),
  cause is structural.
- **`#333`** — its ratchet wedge is untouched and still pinned by name in a test, so
  nobody credits `#412` with it or "fixes" it by loosening the settle clock.
- **`#413`, `#414`, `#415`** as filed. `#414` should also remove the now-redundant local
  guards `#412` added, rather than leaving two overlapping rules.
- **`#408`, `#409`, `#410`, `#399`'s `adopt.md` half, `#402`, `#403`, `#404`, `#405`,
  `#395`, `#388`, `#358`** unchanged by this session.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **cs-toolkit's refresh is unblocked** — it was waiting on this landing. Its kit-owned
  files are all byte-identical to what was installed (no local edits to merge), and its
  `paths.engines` is `scripts/devkit`. Drive `/upgrade` from **the kit's** copy of
  `upgrade.md`: the adopter's own copy predates the cross-tree hardening. Verified with
  `python3 scripts/kit_doctor.py --root <cs-toolkit> --manifest <kit manifest>` run from
  the kit root.

▶ Next: **cs-toolkit kit refresh** — `/upgrade` for `/Users/topi/Coding/in-parallel/cs-toolkit`,
driving from this repo's `docs/agentic-dev-kit/workflows/upgrade.md` rather than the
adopter's older copy. Bind `$REPO`/`$KIT` before the first write and verify at the
destination. Its own `tests/test_pr_watch.py` will not pin the refreshed engine's new
merge-gate behaviour — decide deliberately whether to vendor the kit's tests too.

______________________________________________________________________

## Session — 2026-08-10 (the merge gate, and the fix rounds that became the subject)

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

▶ Done in `#412`, kept for what the groundwork got wrong: **`#95`** — the check-name trust
boundary. The groundwork's reading of the transports was half right. `gh pr checks --json`
does expose no app identity, and the `workflow` field really does discriminate check *runs*
only. But it also said `/commits/{sha}/status` exposes `creator.login` per context, and that
endpoint carries **no `creator` at all** — only the plural `/statuses` does. Worth keeping
because the error was in a document written specifically to spare the next session the
probes, and only re-running them caught it.

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

