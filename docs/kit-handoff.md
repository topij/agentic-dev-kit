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

Last updated: 2026-08-14 — `#470` merged; filed `#463`–`#469`.

## Latest session — 2026-08-14 (the approved sweep, executed)

**Theme —** the friction-log graduation the previous block's `▶ Next:` named, run in
the workflow's LLM-only mode on the operator's bulk approval — "Slack proposals
reviewed. lgtm". Filed `#463`–`#469`, posted an occurrence comment on `#450`, swept the inbox
byte-exact against the frozen digest, and merged the sweep on `#470` (`b7f8d4f`) with
CodeRabbit's own clean review. The friction log is under its budget again, so the session-start
tripwire quiets.

- **`#463` is the batch's center of mass** — the disposition-carrying gap, filed with
  its occurrences enumerated, including `#459` round 5's live demonstration that a
  restated disposition is framing plus a second copy going stale.
- **`#251` recurred inside the batch's own writes:** a double-quoted comment body let
  the shell execute every backticked fragment, corrupting the `#450` comment — exit 0,
  caught only by reading the posted body back. Repaired in place (`-F body=@file`, per
  `#122`), re-verified fragment by fragment, occurrence recorded on `#251`.
- The morning's merge (`#470`) and the prior night's (`#462`) both landed on the
  bot's own clean review with no recordable receipt — `#350`'s vocabulary gap, its
  occurrence already on that issue.

▶ Next: several threads, none blocking — open with `session-start`. The operator-held
decisions are `#372` (review-quota posture, now carrying `#459`'s six-panel data
point) and `#460` (the bracket question); `#455` is the clean self-contained build.

______________________________________________________________________

## Session — 2026-08-13 (the #457 ruling: two instants kept, six rounds to hold one guard)

**Theme —** `#457` ruled and shipped (`#459`, squash `7ef068c`): the `#428` guard keeps
comparing two instants, because `state/` is a live store `pr_watch.py` writes between
and during sessions — only a change across the session is evidence, and what persists
at session end is all the merge gate can ever read. Within that design the traversal
became total (a symlink records by target as a value at its own path, the root's own
presence records, `<special>` covers the rest); the comparison's blind spots are now
stated as classes in the module docstring instead of an enumeration that kept growing.
`make test` at the kit root on the merged tip `7ef068c` is green.

- **Merged with a `fallback:panel` receipt at `417d3a1`, both lenses, after six full
  dual-lens rounds** — CodeRabbit was rate-limited on every head, again. Round records
  and every disposition are comments on `#459`; the loop ended in the doctrine's second
  terminal state, a round whose one finding was disposed without a commit. Occurrence
  recorded on `#372`, which this keeps costing.
- **The round that mattered: a lens broke my fix's own mechanism.** The `@`-suffix
  symlink key was a design choice I weighed and dismissed as unlikely to collide;
  round 3's adversarial lens demonstrated a real file named `<name>@` masking a
  brand-new symlink, end-to-end with a control. The kind marker moved into the value
  (`symlink -> <target>`), where no legal filename can collide. "Unlikely" is not a
  property of a mechanism.
- **Filed:** `#460` (an `atexit` callback writes after the second instant with a green
  run — the bracket's mechanism decision), `#461` (an unreadable file under `state/`
  crashes conftest import — fail-closed, undocumented). `#455` stays open: the cwd
  reach gap is in the threat model, and its fix is a second registration point on a
  load-bearing guard — its own PR, never a fix-round patch.
- Occurrences recorded on `#416` (a lens fetched inside its handed linked worktree
  again, self-disclosed; the `ls-remote` route is noted on the issue) and `#457` (the
  "stale by four" repair itself went stale — logged, then swept along with the two
  surviving `5 of 32` copies the round-5 adversarial lens found).

**Learned**

- **I published a commit sha before the commit existed.** A round comment named the
  fix commit by a sha no command had produced; the real sha differed. Corrected on the
  one surface it reached, with the correction left visible rather than silent —
  `#422`'s subject arriving inside a review record.
- **`--carry-forward` leaks framing, measured from the receiving end.** Round 5's
  prompt restated dispositions and a risk label; the lens flagged both under
  No framing, declined to defer, and re-derived the restated figure independently —
  finding it staler than the prompt claimed. Coverage-only carry-forward from round 6
  on; the friction entry carries the shape.
- **Severity fell monotonically and the loop's terminal states were reachable as
  written** — the last three rounds found nothing in the mechanism itself, and the
  close-out was a filed issue, not another fix round.

▶ Next: run the `triage-friction-log` workflow — the inbox has been over budget since
session start (the tripwire fires on it) and gained an entry this session.

______________________________________________________________________

## Session — 2026-08-13 (one guard, and the reviewer finding my own claims)

**Theme —** `#453`: the `#428` state guard, which keeps fabricated review receipts out of
`state/pr-watch/`. `#447` (nothing pinned it) and `#448` (it was absent when a run
collected only `lib/state_paths/tests`) were one mechanism's two symptoms and shipped
together. Merged as `175bda0`; `make test` at the kit root on the merged tip is green.

- **The placement `#448` did not consider.** That ticket weighed a repo-root conftest
  (reaches no adopter) against a second conftest beside `state_paths` (a copy to drift)
  and called neither right. The **engine root** has neither objection: pytest loads
  conftests from rootdir down, so one file there covers every test directory under it,
  and it sits inside what an adopter vendors. Only the detection half moved —
  `_hermetic_state_root` stays beside the tests because `lib/state_paths/tests` drives
  `$DEVKIT_STATE_ROOT` as its subject and asserts on the unset case.
- **The review kept finding defects in my own work, and the ones that mattered were
  claims I had written and defended.** I argued in the PR body that manifest-tracking the
  new file would cascade through `kit_doctor`, as the reason to defer it;
  measured, it was clean, and the file had been invisible to `/upgrade` — `#422`'s shape,
  committed by me. I documented the `cd`-into-tests residual as the no-argument form when
  the boundary is the working directory. I quoted `make test` as running
  `pytest lib/state_paths/tests tests`, having dropped both `scripts/` prefixes while
  moving text that claims to quote the command.
- **CodeRabbit's quota returned mid-PR and it found things the panel had not** — one
  with a better fix than mine (`_require_no_ancestor_marker`, already this
  repo's convention). Its outage is why the panel ran at all; `#372` is still the open
  question about that posture.
- **Filed:** `#455` (the guard is lost for any run whose cwd is a test directory),
  `#456` (a dangling symlink is invisible to the snapshot), `#457` (further routes past it,
  plus `session.shouldfail` unpinned). Occurrences recorded on `#40` and `#416`.

**Learned**

- **`#457`'s routes share one root, which is worth more than the tickets.** The
  guard observes **two instants** — disk at conftest import, disk at session end — and
  not the interval between them, so anything netting to zero across those instants is
  permanently outside what it can see. A resolution that keeps the two-instant design
  should say so instead of enumerating; one that watches the interval closes every route
  that nets to zero across them.
- **Every count I wrote about my own work was wrong or went stale, including in this
  block.** Its first draft tallied rounds run, defects found, lens runs, and open routes
  on a ticket still growing; `wrap-up.md`'s own rule caught them before the commit. An
  earlier attempt to illustrate the same lesson was itself inaccurate — I claimed a
  "TWO THINGS THIS TRAVERSAL CANNOT SEE" count had gone stale, when the later finding was
  a blind spot in the *comparison of two instants*, not in the traversal's enumeration, so
  that count still stands. `fallback-review-panel.md` teaches this as enumerate-never-count;
  what this session adds is that the reflex extends to the sentence explaining the reflex.
- **The panel's own attestation cannot catch a shared-`.git` write.** A lens fetched into
  the linked worktree it was handed; `git status` was clean before and after, because a
  ref write touches no working-tree byte. Self-reporting was the only detection route,
  and that is not a mechanism (`#416`).

▶ Next: **`#457`** — decide whether the `#428` guard should keep observing two instants
or watch the interval. That one choice disposes of every route that nets to zero across
the two instants, and tells you what `#455` and `#456` are worth; taking them as separate
tickets is the more expensive reading.

______________________________________________________________________

## Session — 2026-08-13 (five lanes overnight, and the reviewer catching the author each time)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

