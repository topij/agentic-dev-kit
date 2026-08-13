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

Last updated: 2026-08-13 — first unattended multi-lane batch. `#441`, `#442`, `#443`
merged; `#444` and `#445` are green and held for the operator. Filed this session:
`#446`, `#447`, `#448`, `#449`, `#450`.

## Latest session — 2026-08-13 (five lanes overnight, and the reviewer catching the author each time)

**Theme —** the first autonomous batch run through `parallel-headless.md`. The mechanism
held; what the review found in the lanes' own work, and what the launch could not honour,
are the parts worth carrying.

- **Merged, each self-merge class via `dev_session.sh merge <scope>`:** `#441` (the two
  `#439` gaps in the changelog test helper), `#442` (`#429`'s path arithmetic, resolved
  through `_repo_layout.find_repo_root`), `#443` (`#435`'s receipt exception in
  `wrap-up.md` step 8). `make test` at the kit root is green on the merged tip `4d7e573`.
- **Held for the operator, both green with a current-head `fallback:panel` receipt:**
  `#444` (`#433`'s state guard, moved onto `pytest_sessionfinish`) and `#445` (the
  author's draws given their own `--delta-draws` channel). Persisted class `operator` on
  both; the merge wrapper refuses them by design.
- **`#444` did not take `#433`'s prescribed direction, and the deviation is the finding.**
  The ticket directs the baseline to `pytest_sessionstart`; that hook is never delivered
  when a bare `pytest` at the repo root loads the conftest lazily, so the baseline sits at
  conftest import. Found by mutating it back and watching a false alarm name three
  untouched files — not by reading. The operator rules on the shipped shape.
- **The launch could not honour `parallel-headless.md`'s mandatory `env` map.** Claude
  Code's delegation tool takes no environment, so `DEVKIT_REFUSE_UNSANDBOXED_STATE=1`
  never reached a lane. Isolation itself held on the on-disk marker — the cockpit exports
  no `DEVKIT_*`, so nothing could be inherited to collapse the lanes into one sandbox.
  Ran on the marker plus a prompt-level cwd guard, at the operator's decision. Friction
  entry filed; the contract's own alternative needs `--dangerously-skip-permissions`.
- **Filed:** `#446` (the workflow docs never say to fetch before branching off the
  protected branch), `#447` (the `#428` guard is unpinned — a no-op mutation of it passes
  the suite bit-identically), `#448` (that guard is absent entirely when a run does not
  collect `scripts/tests`), `#449` (`panel_prompt.py` interpolates free-text flag values
  naively), `#450` (`panel_prompt.py` cannot tell a full panel from a delta pass).

**Learned**

- **The panel caught the author on every lane that ran one, including on prose.** `#443`'s
  first wording said "branch first" without naming which tip, which would have let an
  agent cut from the already-reviewed feature-branch tip and carry those commits into the
  new PR — defeating the fix the PR existed to make. A MED regression in two paragraphs,
  in a change whose entire deliverable was the wording. `#445` round 1 found an overclaim
  reading as a structural guarantee; round 2 falsified a byte-identity claim in its own
  `CHANGELOG` entry.
- **A claim crossed from a ticket body into a commit message unchallenged.** `#442`'s
  commit message overstated when the duplicated `sys.path.insert` bites, inherited
  near-verbatim from `#429`'s own body; both lenses found it independently. `#54`'s
  subject one hop further out than it is usually seen — the ticket is not a source.
- **An operator-class lane has no terminal state.** `reconcile_sessions.sh` resolves
  merged / parked / open, and a lane that is finished, green and waiting on a human
  reports **open** — indistinguishable from one still working. So a batch holding any
  operator lane can never reconcile closed, which is the state every well-run autonomous
  batch ends in.
- **`#416` recurred twice in one night**, each time self-disclosed by the lens that did
  it — a `git fetch` inside the handed linked worktree writing the shared
  `refs/remotes/origin/main`. Verified additive-only from the kit root with
  `git reflog show refs/remotes/origin/main`: fast-forward on every entry, nothing
  rewound. The disclosure works; the structural cause is untouched.
- **`#439`'s fixes shipped on `#441` and the issue is still open**, because the lane
  correctly wrote no closing keyword and nothing else retires an issue. The discipline
  that prevents a wrong auto-close also prevents a right one.

**Open, and owned by nothing yet**

- **`#444`, `#445`** — green, reviewed, awaiting the operator's merge. `#444` carries one
  LOW docstring imprecision left unpatched on purpose, with the exact correction on the
  PR: a new head would bind the receipt to a head no lens reviewed, which is `#435`'s
  subject applied the same night it landed.
- **`#429` and `#435` stayed open deliberately** — `#429` for the nested-layout CI smoke
  (it touches `.github/workflows`, operator-merge territory), `#435` for direction 2.
  **`#439` needs closing or a note.**
- **`#447`** is the sharpest of the new set: the guard protecting the receipt store ships
  with no failing case behind it, which is `#417`'s pattern one level up.
- **`#450`** is a decision, not a build: whether `panel_prompt.py` should gate
  `--delta-draws` behind a self-reported pass kind — `#32`'s family.
- `#431`, `#434`, `#438` untouched; `#434` still needs `#273` accounted for.
- Nothing in the blocks below moved this session.

▶ Next: **rule on `#444` and `#445`** — both are green with dual-lens receipts and cannot
merge without you. Read `#444`'s deviation from `#433`'s prescribed direction first; it is
the one judgement the batch could not make for itself.

______________________________________________________________________

## Session — 2026-08-12 (the changelog an adopter reads, and a loop that kept finding my own fixes)

**Theme —** `#430`: `/upgrade` said *which* file to take and nothing said what taking it
would change. Shipped on `#437`. The mechanism is small; what the review found inside my
own work, round after round, is the part worth carrying.

- **`#430` closed** (`#437`, `9833e95`). Split deliberately, and the split is the design
  decision: `CHANGELOG.md` at the root records **observable**
  changes only; the *reading* half went into `upgrade.md` Step 1, where
  `baseline_kit_commit` is already in hand; the *authoring* half went into `AGENTS.md`,
  because only kit authors write entries and that rule must not ship to adopters.
- **`CHANGELOG.md` is deliberately outside `KIT_OWNED` and the manifest.** Adopters read
  the kit's copy in the clone Step 0 already makes; installing one would create another
  file that drifts and reports `differs` forever. Entries are keyed by the **PR that made
  the change**, not by the commit an adopter happened to land on — `#430`'s own sketch
  keyed the backfill to a wrap-up commit that changed no code.
- **`#432` landed**, closing the thread the previous block left waiting on an operator
  merge.
- **Filed:** `#438` (nothing enforces the new rule; every cheap proxy for "is this
  observable" fails in the expensive direction — a signature check misses `#190`/`#39`,
  whose signature never changed), `#439` (the unreachable test-helper gaps, whose
  filing is what ended the review loop). Occurrence comment on `#243`.

**Learned**

- **"Verified against the code" covered the behaviour and not the symbols.** I stated it
  on the PR; a lens then found the entry named a function that exists nowhere, and another
  quoted a `merge_blockers` value that is only ever a prefix. The behaviour claims were
  right, which is what made the rest look established. `#54`'s own subject, recorded there.
- **Each fix round carried the next defect, including into a test written to close the
  previous round's finding.** One round's correction introduced a false claim about the
  lines it was correcting; a later round's coverage fix hardcoded a copy of the thing
  under test, so mutating the document left the test green. `safety-critical-changes.md`
  rule 3's subject, with the loop's own transcript on `#437` as the evidence.
- **A claim repaired twice was deleted rather than corrected a third time.** The quoted
  git error text was wrong for every real input — `baseline_kit_commit` is a full sha and
  git words that case differently from an abbreviated one. The exit codes are what the
  guard keys on, so the quotation went. `fallback-review-panel.md`'s "keep the record
  small", applied rather than cited.
- **The lenses split on a finding and agreed on every fact beneath it** — one called a
  looser check a regression, the other tried to construct a false pass, could not, and
  reported clean. Fixed rather than adjudicated, because the repair removed the *reason*
  the looser form existed.
- **The stopping rule was stated on the PR before the last round's results were read.**
  Every bound on that loop is settable by the author of the change under review, so
  pre-committing is the only defence against choosing the cheaper answer afterwards. The
  loop ended on blast radius, not on findings running out.
- **The bot reviewed the first head and was rate-limited on every one after**, again, and
  the panel carried the rest. `#372` is the posture decision this keeps costing, and this
  session is the sharpest evidence for it and for `#420`.

**Open, and owned by nothing yet**

- **`#429`, `#431`** — the remainder of the cs-toolkit upstream set, untouched. The
  previous block called `#430` the one the others are downstream of; neither issue body
  records that dependency, so treat the ordering as a judgement to re-make rather than a
  blocker that has now cleared.
- **`#438`, `#439`** as filed. `#438` is the enforcement half `#437` deliberately left out.
- **`#433`, `#434`** untouched; `#434` still needs `#273` accounted for or it is half a fix.
- Nothing in the blocks below moved this session.

▶ Next: **`#429`** — `#134`'s defect surviving in `test_pr_watch.py`, the one file `#40`
certifies as portable. Read its body for the downstream fix already applied and offered
upstream, rather than starting from the title.

______________________________________________________________________

## Session — 2026-08-12 (the adopter refresh's first upstream fix, and a boundary I drew wrong)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

