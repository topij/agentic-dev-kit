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

Last updated: 2026-08-01 — `#189` settled `#174`, which is now closed: both truncating writes stay,
documented at each site. The result that outlives it is `#190`, a merge-gate fail-open the review
found by executing a claim I had verified by reading.

## Latest session — 2026-08-01 (a documentation PR, and the defect it found in the merge gate)

**Theme —** `#189` merged (`13afb19`) and settled `#174`: `kit_doctor.main`'s `--generate-manifest`
branch and `pr_watch.save_state` keep `Path.write_text`, each with a short comment pointing at the
issue. **No behavioural delta at either site** — the scope independently corroborated by lens
token-stream and AST comparison, and deliberately narrower than the wider claim an earlier draft
made, which a lens disputed and I upheld against myself: the regenerated `kit-manifest.json` is
consumed by a build-failing drift gate. Every review round found a defect in some version of the
argument kept at the call sites, and some rounds' findings were regressions introduced by the round
before. Per-round dispositions are on `#189`; this block points at them rather than recounting them.

- **`#190` filed, and it is the durable result.** A receipt recorded against a lost false-settle
  baseline makes `mergeable` true while checks are still registering. Pre-existing on `main` and
  **not closed by converting the write**, which is why `#174` settled as *leave both* despite the
  discovery. The mechanism, the measurement and the suggested direction are on `#190`.
- **The decision's stated basis changed completely; the decision did not.** `#174`'s own reasoning
  was wrong in three places, and the superseding comment there carries what survived. The site
  comments point at it rather than restating it — which is only honest because that comment was
  written; an earlier draft pointed at a thread still carrying refuted claims.
- **Merged with an explicit squash body**, because the repo squashes with `COMMIT_MESSAGES` and the
  default would have published the withdrawn safety claim onto `main` as this change's recorded
  rationale. Found by a lens reading commit messages as a reviewed surface — it appears in no diff.

**Learned**

- **Delegation is only honest if the target is current.** Shortening the site comments to "the
  argument lives on `#174`" left the deciding reason existing nowhere, because that issue still
  carried claims the review had already refuted. A pointer inherits the accuracy of what it points
  at.
- **Deleting beats correcting — but not blindly.** Cutting the comments in half repaired most of one
  round's findings and simultaneously threw away a *correct* repair, putting the `#164` criterion
  wrong again. Deletion is a scalpel, and the load-bearing sentence is the one most easily cut with
  the verbose ones.
- **A guard sequenced before an action is not chained to it, and I proved `#180` on myself.** The
  closing-keyword scan printed a violation and the comment posted anyway, because the scan ran
  before the `gh` call rather than gating it. Rewired to gate on exit status it began refusing
  publishes, including on this block. Nothing was closed. **No such scanner exists in `scripts/`** —
  `#71` is the ask to build one, and each of these was an ad-hoc command. Occurrence data for `#180`
  and `#71` is in the inbox, un-graduated, not on those issues.
- **Two of my own checks reported success without examining their subject.** A CI-wait loop printed
  its exit condition and then crashed in its reporting line; a scripted comment edit matched its
  patterns and produced mangled text in both files. Both caught by reading output rather than an
  exit code — `#179`'s shape, in the session that merged a PR about unverified claims.

**Open, and owned by nothing yet**

- **`#190` is unowned and is the sharpest thing on the board**, and the `▶ Next` below sends the
  next session at it. Its ask is on the issue.
- **`#189` merged with a single-lens receipt (`fallback:delta`, correctness) and a one-commit
  unreviewed tail**, both disclosed on the PR before merge. The tail is `#27`'s gap; the one-lens
  receipt is `#76`'s. Chosen rather than missed, and the engine's own warnings are in the record
  command's output.
- **`#187` is now live rather than theoretical**: `check_doc_budget.py` warns that the friction log
  is over budget. Both the graduation marker and the inbox contribute, and `#187`'s own measurement
  is that a sweep lands the file back just under budget — so the warning clears, narrowly, and
  returns. Read `#187` before assuming either half is sufficient on its own.
- **Carried forward from the block this session swept to history, because all are still open and
  the sweep would otherwise drop them:** `#124` (documented default flipped, prose only — nothing an
  adopter runs changed while `#6`'s engine is unvendored), `#167`, `#169`, `#170` from the draft-bit
  and contract-numbering thread, `#33`/`#112`, which still want confirming against `#131` before
  either is deliberately marked done, `#181` (a merge that lands without its `(#N)` suffix —
  recurring, and not repairable in place), and the cs-toolkit Phase 2 blockers `#41`/`#37`/`#134`,
  still untouched. **A first pass at this bullet folded only the issue-numbered items and dropped
  these**, which is the same invariant failing twice in one PR.
- Inbox length: `check_doc_budget.py` prints the live figure.

▶ Next: **`session-start`** — `#190` is the one clear thread and the rest is diffuse. **Page the
tracker rather than dumping it:** `#143` records `session-start` overflowing its tool limit above 68
open issues and is still open; `gh issue list --state open --limit 25 --json number,title,labels,state`
is the form that works here. That issue's own remedy names a GitHub-MCP parameter, and no MCP server
is configured in this checkout, so the `gh` form is the executable one.

______________________________________________________________________

## Earlier session — 2026-07-31 (the loop got its exits, reviewed under the rules it replaces)

**Theme —** `#176` merged (`65c9ee4`): a prose finding is disposed of by whether anything
**executes** the text; a record-prose imprecision below HIGH is **logged** — reply on the PR plus
a tracker artifact, no commit — instead of fixed; fix rounds batch into one push; re-runs aim at
the delta since the last receipt's `--head`; a record-prose-only delta takes **one lens**
(`fallback:delta`) instead of the panel. The review rounds that forged the guards are enumerated
on `#176` — one disposition comment per round, totals in the squash message — and **the PR could
never take its own exits**: every delta was executed prose, so every round was a full panel. That
measures what the exits are for — record-prose PRs like this handoff update, not doctrine PRs.

- **`#176` merged.** `fallback-review-panel.md` (discriminator, logged disposition, delta pass,
  batching, cockpit-built lens worktrees), `wrap-up.md` (the record-prose authoring checklist this
  block is written under), `pr-watch.md` and config comments (the three receipt literals). This
  line is a pointer, not a copy.
- **The final clause merged reviewed by no lens** — disclosed on the PR, on the operator's call:
  `#27`'s gap chosen rather than missed, the same choice the block below records for `e5bd82b`,
  twice in one day.
- **Cockpit-built lens trees inverted `#75`'s failure mode.** Every lens attestation on `#176`
  reports the named sha found in the provided tree; the recovery burden `#75` records never
  fired. Counter-occurrence comment posted on `#75`.
- **Filed:** `#177` (session records restate doctrine that later changes supersede — also the
  logged disposition's first artifact) and `#184` (the terminal rounds' below-HIGH remainder,
  including the message-only-delta gate note from the review bot's second pass).

**Learned**

- **The logged disposition's first live use also bent it, and the next round caught the bend.** A
  stale restatement in this file's 2026-07-29 block — lens-marked LOW imprecision, record prose —
  got a reply and `#177` and no commit of its own; but the artifact was first promised to this
  inbox, a committed file, exactly what the rule forbids, and the round after made the tracker
  artifact mandatory at disposition time. An honesty model working is indistinguishable from the
  author happening to be honest; the record of the bend is what makes the difference checkable.
- **Two of my own checks had the examined-nothing shape, inside the PR that documents that
  shape.** The keyword scan read the diff but not the commit message committed beside it — two
  banned adjacencies reached the pushed branch (rewrite declined at the permission gate;
  disclosed; squash written fresh and scanned). And two comment-then-ack batches piped the poll
  to `/dev/null` before `--mark-seen`, acknowledging a real bot finding unread — caught only
  because a later poll's coverage line named a review at a sha no panel round had claimed. Both
  in the inbox.
- **A permission denial is a design input, not an obstacle.** Declined force-push and reset left
  the branch label stranded on a superseded commit; committing detached and pushing
  `HEAD:<branch>` kept every later fix fast-forward, and the label was deleted after merge.

**Open, and owned by nothing yet**

- **The delta pass has never run.** This wrap-up's PR is its first natural candidate: a
  record-prose-only fix round here takes one configured lens and the `fallback:delta` receipt,
  per the doctrine now on `main`.
- `#177` and `#184` are occurrence collectors, open by design. The first PR to touch the panel
  doc's stopping section should sweep `#184`'s item on the two surviving absolutes.
- Inbox length: `check_doc_budget.py` prints the live figure; three entries added below the
  fresh graduation marker.

▶ Next: **`session-start`** — the block below's starter stands, minus what this session folded
in: `#176` and `#177` are now in this file, so the sharpest remaining are `#179`/`#180`'s
beside-or-inside-`#150` call and `#174`'s yes/no on the two truncating writes.

______________________________________________________________________

## Earlier session — 2026-07-31 (the seventh sweep, and the only step that caught anything)

**Theme —** `#185` merged (`e8b145f`), graduating the inbox. The result worth keeping is not the
sweep's accounting — that lives in the graduation marker — but **which step earned its keep**:
reading the live tracker *before* drafting was the only one that found anything, and what it found
was two entries asking for work already done. Both would have become tickets if drafted from the
entry text, which was the only surface claiming otherwise.

- **`#185` merged (`e8b145f`).** Seventh `triage-friction-log` sweep, LLM-only (`#6` unvendored).
  Filed `#178`–`#183`; occurrence comments on `#163`, `#54`, `#140`, `#75`. The per-entry routing
  table, the approval record, and the verification statement are in the marker in
  `docs/kit-friction-log.md`; this line is a pointer, not a copy.
- **Two entries needed no ticket, established against the repo rather than against the entry.**
  `#74` is no longer open, `archive_plan_sessions.py` implements `--target-lines`, and
  `wrap-up.md`'s *"Keep the handoff docs lean"* step prescribes it by name; the `finalize.pr_draft`
  entry had recorded its own resolution inline. **Cited by name, not by position** — the merged
  marker says `wrap-up.md:58`, which `#176` invalidated by inserting above it hours later, and the
  first repair of that said "step 8" when it is step 7. A position into a living document expires;
  a heading does not.
- **`#179` and `#180` were filed beside `#150`, not folded into it.** That issue's subject is a
  scripted text replacement that matches nothing; a check run in the wrong directory and a guard
  that reported failure and was then ignored are neither. `#150` is unchanged — a judgement call
  worth revisiting while the three are fresh.

**Learned**

- **A gate promoted in this sweep passed over an empty set.** Fence-parity went from measured to
  asserted, then printed `0 fences preserved` — this inbox has no fenced blocks, so the assertion
  and its companion never reached a subject. `#179`, occurring inside the sweep that filed it. It
  is visible only because the script prints the count it asserts on; had it printed `ok`, the
  vacuous pass would have read as a real one. That is `#179`'s negative-control ask in one line.
- **The review's one finding was record prose, refuted by execution.** The marker claimed the
  frozen-inbox digest reproduces *"from `git` alone"*; the command also needs a SHA-256 utility,
  and the reviewer established that by running it where none existed. Corrected in `e5bd82b`. The
  same wording still stands in **two archived markers** — correcting those would falsify the
  un-demote round-trip the sweep verifies — so three consecutive sweeps *made* the claim and two
  still carry it. `#140`'s shape, and now its occurrence data.
- **`make test` is red under `uid 0` and green in CI.** Three tests `chmod 000` a doc and assert
  exit 2, which root bypasses. Established by running `make test` from the repository root twice,
  once with the session's edits stashed, and getting identical results both times. In the inbox
  below the marker, deliberately un-swept.

**Open, and owned by nothing yet**

- **A parallel session ran alongside this one and wraps up after it.** `#176` (`65c9ee4`) is its
  work; its own block will carry it. That block lands on top of this one in this file.
- **The merge receipt covers `7d95da8`, not head.** `e5bd82b` — the correction the reviewer itself
  asked for — merged unreviewed, on the operator's explicit call after the bot rate-limited a
  third time. `#27`'s gap, live again, and this time chosen rather than missed.
- **The reviewer was rate-limited on two of three attempts**, holding the merge about an hour.
  Re-triggering after the stated window produced a real review — `#118`'s proposed behaviour,
  performed by hand. Occurrence data is on that issue.
- Inbox length: `check_doc_budget.py` prints the live figure. No number here.

▶ Next: **`session-start`** — six fresh tickets and no single obvious thread. The sharpest
candidates: `#179`/`#180` want the beside-vs-inside-`#150` call confirmed while the reasoning is
fresh; `#176` and `#177` want folding into the handoff; `#174` still wants a deliberate yes/no on
the two remaining truncating writes. `#178` is the most self-contained fix (gate the hook on the
tool result, with a predicate per command).

______________________________________________________________________

## Earlier session — 2026-07-30 (one bug, seven review rounds, and the same defect five times)

**Theme —** `#172` merged (`b82eba9`), repairing `#164` and settling `#162`. The bug was one *call*
— `Path.write_text` truncating before it writes — at three sites in the engine.
What the session actually measured is where the *fix* kept going wrong: **a fix, or its
written rationale, applied to one of two symmetric locations — five findings, three of them inside
the fix for that very pattern.** (Three are literally one-of-two *call sites*; the fourth is a test
covering one site only, the fifth a `BaseException` argument written in one method's docstring and
not carried to the method one call away. The wider class is the honest one.) Severity ranking missed
every instance, and what ended it was structural rather than another guard: the two hand-written
recovery paths were collapsed into one function used by both sites.

- **`#164` repaired.** `Path.write_text` truncates before writing, so a failed write destroyed the
  living handoff while the tool printed *"no changes applied"*. Measured with `RLIMIT_FSIZE`
  against the **real 28,518-byte handoff**: before, 28,518 → 1,024 bytes at exit 2 under that
  message; after, both documents byte-identical and the message true. New `scripts/lib/atomic_write.py`
  stages to a random sibling temp (`mkstemp`, `O_EXCL`), fsyncs, publishes with `os.replace` —
  and stages **both documents plus the rollback** before publishing either, which is what dissolves
  the objection that reverted the first attempt on `#160`: the rollback's cost is paid up front,
  while failing is still free. **Not total:** of five failure scenarios a lens measured as silent
  data loss, two now recover and three do not — those three force a publish *and* its rollback to
  fail together, so nothing is left to recover from. All five now print a message naming both
  documents, which is the part that was missing.
- **`#162` settled the other way, deliberately.** The `\x1c` half was genuine content loss and is
  repaired (a bare `str.strip()` eats `\v \f \x1c \x1d \x1e \x1f \x85 \xa0`). Line endings
  **normalise**, and a test pins it — including what that test *cannot* see on POSIX. The docstring
  still opens with "only ever moves content" and now **qualifies** it with the normalisation as a
  named exception; it was not replaced, and this line said "instead of" until a lens read the file.
- **Seven review rounds**: CodeRabbit ×3 (rate-limited on every head in between), fallback panel ×4.
  Tests 564 → 599, both counts reproduced by `make test`. The mutant total (25 across three batches,
  all reported killed by named behaviour tests) is **attested, not reproducible**: only round 1's ten
  are enumerated on the PR, the driver scripts lived in session scratch, and `Makefile` already warns
  that an unenumerated kill count is exactly the figure that does not survive scrutiny.

**Learned**

- **Ctrl-C was more destructive than SIGKILL.** At the same instant: SIGKILL runs no handler, so the
  staged rollback survived on disk and the data was recoverable; Ctrl-C ran the `finally`, which
  unlinked the copy staged for exactly that moment. On a tool whose caller is interactive. Nothing
  about severity or code review suggests looking there — only executing it did.
- **A proxy documented as "the fact".** The staged temp's absence is *evidence* the rename happened;
  anything else that removes it reads identically. Hedging the wording made the message honest
  without making the outcome better. What worked was **reading the destination back** and comparing
  it to what the run intended to write — a real check replacing an inference.
- **Three separate episodes of my own checks reporting success without examining anything.** A
  persisted `cd` into a scratch clone made `ruff`/`make test`/manifest all pass against the wrong
  tree (three checks, one episode); the same drift put a `sed` rename in the clone, leaving a test
  whose docstring claimed a rename that never happened; and a verification probe reported five clean
  passes because it compared an unresolved path against a `realpath`-resolved one. Only the `sed` one
  is literally `#150`'s subject (a scripted text replacement that matches nothing); the other two
  share its **root cause** — a check whose target was never reached — which is the widening the
  friction entries propose. All three were caught by reading output, not by an exit code.
- **A kill you cannot attribute is not evidence.** Four mutants needed a second attempt: one test
  raised from an f-string argument (evaluated before the function was entered), one guard was
  invisible to content assertions, one hazard had been fixed twice so the symptoms were gone either
  way, and one kill aborted the pytest session instead of naming a test.

**Open, and owned by nothing yet**

- **`#164` and `#162` are CLOSED**, both with the reasoning posted on them rather than a bare state
  change — `#162`'s records that the decision is *normalising* and exactly what would justify
  reopening it. **`#174` is settled by `#189`** (open at the time of writing): the writes in
  `kit_doctor.main`'s `--generate-manifest` branch and in `pr_watch.save_state` stay truncating, now
  documented at each site. Cited by function, not by line — `#189` moved both, which is how the
  stale `:637`/`:2201` this bullet used to carry were found. This bullet's own reason
  (*"both write machine-regenerated artifacts, so the refuse-on-read-only/hardlink semantics add
  failure modes with no benefit"*) was partly wrong: `write_text` already fails on a read-only
  target, so that was never an added refusal. **`#190`** is the larger result — a merge-gate
  fail-open where a receipt recorded against a lost state file makes `mergeable` true with CI still
  registering. It came out of `#189`'s panel, no choice of write can close it, and it is worth more
  than the PR that surfaced it.
- **The merged tree was reviewed by nothing, and the unreviewed tail is 5 commits, not 2.** Panel
  round 4 saw `e5cb29f` (7 commits back); CodeRabbit's last review was `342f437` (5 back). That tail
  is `+106/-12` and is **not** all test hygiene — `6d7eb28` touches both engine files. The first
  draft of this bullet said "last two commits", which was the PR receipt's error reproduced into the
  durable record. `#27`'s gap, live again.
- **`#75` again: 8 of 8 lens runs were placed at the base rather than the head.** All eight detected
  it and diffed the named sha, so the contract works — but a 100% harness failure rate is an open
  defect, not a rigor statistic, and belongs here rather than in the round-count bullet where the
  first draft put it. The 8/8 figure is **self-reported by the lenses** and unverifiable from outside
  (`#32`), like every `--lenses` claim on every receipt this repo records.
- **The wider one-of-two-symmetric-locations pattern belongs in doctrine, not just this block.**
  `#163` records occurrences; what this session adds is that it recurred *inside its own fix* and
  that the remedy is **structural** — remove the second site — where guards and severity ranking both
  failed. Caveat against the thesis: the de-duplication commit itself left a duplicated comment
  block, caught by the review bot, which is the same trap this repo's history already records.
- **`#127` and `#138` are still the pair that would make a sweep's claims mechanically checkable**,
  carried forward from the block this session archived. Both OPEN. Recorded here because the sweep
  that moved that block **dropped them** from the live handoff, which the file's own closing line
  promises does not happen — and `#127` is the ticket about a sweep being indistinguishable from a
  deletion. Found by a review lens, not by the sweep.
- The inbox was **283/150 at this wrap-up** — the largest in the recorded series
  (168 → 179 → 233 → 283). Stated as a measurement with its moment, not a running figure: the
  previous block dropped the number precisely because a hand-written one went stale three times,
  each time inside the commit correcting its predecessor. `check_doc_budget.py` prints the live one.

▶ Next: **`triage-friction-log`** — the inbox is near double budget and un-swept for
several sessions; four of this session's entries are ready to graduate, three of them one class
(`#150`: a check that reports success without having examined anything). Then `session-start` for
the rest: the five-finding one-of-two-symmetric-locations result wants routing — doctrine change vs.
a comment on `#163` — and `#174` wants a deliberate yes/no on the two remaining truncating writes.
Caveat before running the sweep unattended: `notify.user_key` is blank, so `triage-friction-log`
stops at Step 2 by design (`#128`).

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

