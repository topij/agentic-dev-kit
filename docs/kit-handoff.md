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

Last updated: 2026-08-12 — the cs-toolkit refresh landed and `#428` is fixed on `#432`,
which is `mergeable` and waiting on an operator merge. Filed this session: `#433`, `#434`,
`#435`.

## Latest session — 2026-08-12 (the adopter refresh's first upstream fix, and a boundary I drew wrong)

**Theme —** `#428`, the sharpest of the four issues the cs-toolkit refresh filed against the
kit. The fix is small; what the review found in it, round after round, is the part worth
carrying.

- **The cs-toolkit refresh is done** — the thread this handoff carried as outstanding since
  2026-08-10. It went `40eef8b` → `0c73bdf` clean: `kit_doctor` 0 differ, config migration
  byte-identical, 6 of 6 declines preserved. Filed upstream: `#428`, `#429`, `#430`, `#431`,
  plus an occurrence comment on `#40`. **Its field report exists only as a chat artifact**,
  which is `#423`'s own shape — a URL is a pointer for one reader, not provenance. The
  findings above are the durable half.
- **`#428` fixed on `#432`** — the kit's own `make test` was overwriting `state/pr-watch/1.json`
  and `4242.json`, and `1.json` is a real PR's record slot. Two layers: an autouse fixture
  binding a per-test state root, and a session-scoped pin that fails the run if the real
  `state/` changes. Receipt `fallback:panel` at `752d9fe`, both lenses.
  **Not merged — operator-merge under the ruling below.**
- **Filed:** `#433` (the pin's snapshot is taken after the first test directory has already
  run — the conftest is directory-scoped and a session fixture instantiates lazily),
  `#434` (`safety-critical-changes.md`'s glob does not reach the guard, with the breadth
  decided as `scripts/tests/conftest.py` only), `#435` (wrap-up step 8 sends the handoff
  commit to the session branch, which voids that PR's review receipt — hit while wrapping
  up this session, worked around by branching off `main`). Occurrence comments on `#54`,
  `#182`, `#209`.

**Learned**

- **The isolation command I wrote failed open.** `DEVKIT_STATE_ROOT=$(mktemp -d) pytest …`
  sets the empty string when `mktemp` fails, and `_resolve_state_root` reads empty as *no
  override* — so it would have redirected the suite into live `state/` exactly when the
  isolation failed, which is worse than not having the line, because the command reads as
  protected. CodeRabbit found it. The two-step `tmp="$(mktemp -d)" && …` gates the run on
  the assignment.
- **I drew the safety-critical boundary wrong, and a lens overturned it.** My reasoning was
  that the globs name `dev_session.sh` and `pr_watch.py` and the diff touches neither —
  literally true. But the glob's own frontmatter says `pr_watch.py` was added because the
  rule must match where the decision is *made*; a fabricated receipt is indistinguishable
  from a real one by the time the gate reads it, so the defence has to be upstream. The
  operator upheld the dispute. **The resolution is the operator's own comment on `#432`**,
  because the doctrine excludes a relayed account from the party that drew the boundary —
  which was me.
- **Four of the defects the loop caught were introduced while fixing the previous round.**
  A deleted referent left a dangling pronoun; a corrected claim described an empty set as a
  population. That is `safety-critical-changes.md` rule 3's own subject, and it is why
  `#433` and `#434` were filed rather than built into a fix round.
- **A figure that crosses an agent boundary arrives with its provenance collapsed.** Two
  numbers I relayed from a delegated report into the PR body named commands that did not
  produce them — and naming a command is what made them look established. Recorded on `#54`;
  it sharpens that issue rather than restating it.
- **A lens returned a placeholder instead of a report** and would have counted as a passing
  lens to anything tallying rather than reading. Caught only because the output was visibly
  not a report. `#182`.

**Open, and owned by nothing yet**

- **`#432`** is `mergeable` and unmerged. Operator-merge; do not self-merge it.
- **`#429`, `#430`, `#431`** — the rest of the cs-toolkit refresh's upstream findings,
  untouched. `#430` is the one three of the others are downstream of.
- **`#433`, `#434`** as filed. `#434` needs `#273` accounted for or it is half a fix —
  `.claude/rules/` binds one runtime.
- Nothing in the 2026-08-11 block's open list below moved this session.

▶ Next: **merge `#432`** (operator-merge, receipt `fallback:panel` at `752d9fe`), then
`#430` — the adopter-facing signal for an upgrade that changes observable engine behaviour,
which `#429` and the `#431` decline-labour both trace back to.

______________________________________________________________________

## Session — 2026-08-11 (the sweep, and a record claim that could not be repaired)

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
- **`#399`** gained another occurrence this session; it is on the issue, alongside the
  2026-08-10 comment that already made the argument. Its `adopt.md` half is untouched.
- **`#378`** has a second miscount noted on it: the 2026-08-08 marker calls itself the tenth
  sweep where `#198` and the archive's own sections put it eleventh. The 2026-08-11 marker
  carries no ordinal, deliberately.
- Nothing else in the 2026-08-10 block's open list below moved this session.

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

