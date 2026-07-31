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

Last updated: 2026-07-31 — the seventh friction-log sweep merged (`#185`). Reading the tracker
before drafting was the only step that caught anything, and what it caught was two entries asking
for work that had already landed.

## Latest session — 2026-07-31 (the seventh sweep, and the only step that caught anything)

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
  `#74` is no longer open and `--target-lines` ships at `archive_plan_sessions.py:442`, prescribed
  by `wrap-up.md:58`; the `finalize.pr_draft` entry had recorded its own resolution inline.
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
  same wording survives verbatim in two archived markers — correcting those would falsify the
  un-demote round-trip the sweep verifies — so **three consecutive markers carry the claim**.
  `#140`'s shape, and now its occurrence data.
- **`make test` is red under `uid 0` and green in CI.** Three tests `chmod 000` a doc and assert
  exit 2, which root bypasses. Established by running `make test` from the repository root twice,
  once with the session's edits stashed, and getting identical results both times. In the inbox
  below the marker, deliberately un-swept.

**Open, and owned by nothing yet**

- **A parallel session ran alongside this one and wraps up separately.** `#176` (`65c9ee4`) is
  its work, not this session's — it changed `fallback-review-panel.md`, `pr-watch.md`,
  `wrap-up.md` and `config/dev-model.yaml`, including the record-prose authoring rules this block
  was written under. Not a gap in the record and not summarised here; its own block will carry it.
  **Both sessions edit this file, so whichever wrap-up merges second will conflict on it** —
  resolve by keeping both session blocks rather than taking either side whole.
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
  reopening it. **`#174` is the successor**: `kit_doctor.py:637` and `pr_watch.py:2201` still
  truncate on write. `#164`'s scope note asked they be considered together; they were, and **neither
  was converted** (both write machine-regenerated artifacts, so the refuse-on-read-only/hardlink
  semantics add failure modes with no benefit). `#174` carries that reasoning *and the objection to
  it* — the decision lived in a PR body, so no review lens ever examined it, and `atomic_write` has
  one consumer, which makes those two sites the natural test of whether its refusals are
  proportionate.
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

## Earlier session — 2026-07-30 (two merges, eight rounds, and where every defect lived)

**Theme —** Both PRs landed after eight panel rounds: **18 lens runs launched, 16 completed**, two
stalled at the watchdog and re-run. Each figure published elsewhere is *lower* than 16 — they count
one PR each, or a subset of rounds — and only their sum, 18, exceeds it. None is wrong. The result
worth keeping is narrower than
this block first claimed, and a lens refuted the wider version: **no round ever disputed what the
tickets asked for** — flip a documented default, invert a contract item, diff the named sha — but
nearly every HIGH was in a justification or a guard added around those edits. Both are the
deliverable, so "the change was never contested" is false; what held was the *ask*, and what failed
was everything written to support it.

- **`#166` merged (`eeef647`).** `fallback-review-panel.md` contract item 7: `#75`'s inversion
  (*assume* the worktree points at the wrong ref, not *verify* it), `#163` Sink 1's recovery
  (diff the **named sha** — verified working from a wrong-ref worktree by four lenses, including
  against a `chmod -R a-w` source), and `#136`'s scratch-path isolation. `#75`'s second half had
  no home in the contract, so it is **item 10**, appended rather than renumbered.
- **`#168` merged (`046e9ce`).** `#124`'s documented default flipped to `false` — and the key
  turned out to be in **no config file and read by no code**. The larger find:
  `post-merge-systemize.md` **hardcoded `gh pr create --draft`**, so the key it documents in its
  own table had no effect on the one place that workflow opens a PR (Principle #10).
- **Filed:** `#167` (item 7 now carries four requirements under one number; stable numbering
  blocks splitting it), `#169` (`/adopt`+`/upgrade` drafts, plus the shipped CLAUDE.md template's
  draft-first baseline with no scheduled-run carve-out), `#170` (draft-bit verification, with all
  three failed attempts recorded). Occurrence comments on `#44`, `#45`, `#116`, `#140`.

**Learned**

- **A lens cannot know whether a tree is its own.** `git switch --detach` was documented as the
  cheapest route to a writable tree; every lens run was placed in the **live checkout** instead,
  so literal compliance would have detached a real branch — invisibly, since detaching at the same
  sha changes no byte. The guard added next **failed open from any subdirectory** (`--git-dir`
  absolute, `--git-common-dir` relative-to-cwd) and asked the wrong question anyway, because
  `dev_session.sh` builds lanes as worktrees. No git command answers *is this tree mine*. The rule
  that survived needs no discrimination: never write inside a tree you did not create.
- **A command menu in doctrine is a defect generator.** Every menu item 7 carried had a measured
  defect — routes documented as "blocked outright" that all three worked, `--is-shallow-repository`
  returning false for a partial clone, `merge-base --is-ancestor` passing on a stale base,
  `ls-remote origin origin/main` returning empty. What a given invocation does depends on how the
  runtime built the tree, so the bullets now state what must be **true** and make each lens
  establish its own route.
- **Deleting beat correcting, now four-for-four.** The two rounds across both PRs that *shrank*
  the text are the two that produced no follow-on HIGH. Every round that added an explanation
  produced the next round's finding — including three attempts at one comparative claim, each
  narrowing the quantifier while keeping the class, and a "de-duplicate" commit that took the
  duplicate count from two to three.
- **A check heading is a claim, and a metric can be blind by construction.** The rendering check
  counted `<pre>` elements — but a correctly rendered fence *adds* one, so `0` reads identically
  for "no fence" and "mangled fence". A true measurement supporting a false conclusion, under a
  "Verified" heading. Withdrawn rather than repaired (`#116`).
- **The review bot was throttled, not absent.** CodeRabbit reviewed after 13+ silent PRs, then
  rate-limited, then returned clean — all on one PR. That settles `#45` for this repo, and the
  clean pass reproduced `#44` exactly: it created **no review object**, so `coverage` reported the
  bot three heads behind while its commit status said `Review completed` on head.

**Open, and owned by nothing yet**

- **`#124` stays open** — what shipped is prose only. For `triage-friction-log` nothing an adopter
  runs changed, because `#6`'s engine is unvendored and still hardcodes a draft.
- **`#33`/`#112` still want confirming against `#131`** before either is deliberately marked done —
  the block naming `#131` went to history in this session's sweep, taking the qualifier with it.
- **`eeef647` landed without its `(#166)` suffix**, and it is not alone: 15 of 75 commits on
  `main` have an associated PR and no `(#N)` — 8 of those predate the squash convention, so the
  comparable figure is **7 of 67**, among them `cdeae7a` (#144), `c48164c` (#154), `b46f794`
  (#153). `--subject` explains this session's instance and is **not** established as the cause of
  the others. Recurring, not a one-off, and not repairable in place.
- The inbox is **well over budget** and grew again — five entries added to a file already over.
  **This line deliberately carries no number:** `check_doc_budget.py` prints the current one, and
  the hand-written figure went stale three times (206 → 217 → 224), each time inside the commit
  correcting its predecessor. `#167`, `#169`, `#170` are this session's three tickets.

▶ Next: **`session-start`** — three fresh tickets, an inbox well over budget, and no single
obvious thread. **Page the tracker rather than dumping it** —
`gh issue list --state open --limit 25 --json number,title,labels,state` is the form that works
here. `#143` records `session-start` overflowing at 68 open issues and is still open; there are
**89** now. (That issue's own remedy names `perPage`, a GitHub-MCP parameter; no MCP server is
configured in this checkout, so the `gh` form above is the executable one.) `#170` is the sharpest of the three tickets (it blocks nothing but has a
complete spec and three recorded failures), `#164` remains unfixed and the wrap-up sweep touches
that code every session, and the cs-toolkit Phase 2 blockers (`#41`/`#37`/`#134`) are untouched.
`triage-friction-log` is the alternative, and the inbox is further over budget than when the
previous session chose it.

______________________________________________________________________

## Earlier session — 2026-07-30 (one flag, six rounds, and a bug older than the PR)

**Theme —** `#74` shipped. The durable results are two: the review found a **pre-existing
data-loss bug in the tool that owns this file**, and it measured where six rounds of its own
effort actually went.

- **`#160` merged (`85cdeb0`).** `archive_plan_sessions.py --target-lines N` sweeps oldest-first
  until the handoff is at or under a *line* budget, so the remedy `check_doc_budget` names can
  actually discharge it — `--keep` counts blocks and was a no-op at its default. `budget_line_count`
  makes both tools measure a line the same way; `check_doc_budget` substitutes `{budget}` so the
  number lives in one place. **28 new test functions / 31 cases** (`--collect-only`: 56 → 87).
  Verified in production at this wrap-up: 419 → 355 lines.
- **`#164` filed — the find of the session, and it is NOT fixed.** `Path.write_text` truncates
  before writing, so a failed write destroys the document and the handler still prints *"no changes
  applied"*. Measured on a real full filesystem: a **26,807-byte handoff went to 0 bytes** while the
  tool reported nothing had happened. Latent in the archive engine all along.
- **`atomic_write` was attempted for it and REVERTED** — four HIGH regressions, found independently
  by both lenses: `os.replace` replaces a symlinked doc rather than writing through it, file
  mode/ownership reset every sweep, a fixed temp name lets concurrent runs publish each other's
  bytes, and a pre-existing temp symlink becomes an arbitrary-file clobber. All silent, all at
  exit 0.
- **The mitigation that shipped instead was itself defective three times, which is the session's own
  thesis biting the session.** `02c70ac` — `--help` still promised a rollback the first write never
  gets, a sentence true only while `atomic_write` existed and left standing through the revert.
  `15c8651` — the check named `<handoff>`, but under ENOSPC the *history* fails and the handoff
  rolls back clean, so the instruction **green-lit the damage it was written to catch** (measured:
  an archive committed at 12 of 39 sessions). `37aebd9` — the recovery said
  `git checkout -- <handoff>`, which discards this session's own block.
- **Also filed:** `#161` (LOW imprecisions; **two mutants still survive** — the megaline trim and
  `--target-lines < 1`), `#162` (the sweep is not byte-preserving), `#163` (where the review cycles
  went).

**Learned**

- **A fix stops at the first site**, and it is not a prose problem. The sharpest was
  `(OSError, UnicodeDecodeError)` applied to one of two exception classes *on the same line*,
  leaving exit 1 producible against a contract admitting only 0/2/3 — with the correct fix already
  sitting in `check_memory_budget.py:192-197` under a comment giving the reason. `#163` enumerates
  five occurrences; the PR's 13 commits carry more, **twice inside a fix for this very pattern**.
  Counts on `#163` predate rounds 5–6 and were not refreshed — treat the issue as the record and
  this line as a pointer.
- **A fix round that adds a new mechanism is where the next HIGH comes from.** Three times across
  seven review passes: round 2's `.format()` template → round 3's crash; round 5's `atomic_write` →
  round 6's four HIGHs → reverted; round 6's mitigation paragraph → the confirmation pass. The
  doctrine already says a new mechanism gets filed however squarely a finding prompted it; this is
  the measured version of why.
- **A hypothesis was stated as falsifiable and refuted within one round.** Apparent lens
  specialisation (adversarial finds mechanism, correctness finds prose) was coincidence — round 5's
  correctness lens led with a mechanism defect. On `#163` rather than dropped, because doctrine
  built on it would have rested on nothing.
- **Execution found the bugs that mattered; reading found more of them.** The filled ramdisk,
  `RLIMIT_FSIZE` and a planted symlink produced `#164` and the `atomic_write` HIGHs — nothing else
  would have. But the one-of-two-sites class, which is most of the session's fixes, was found by
  reading. The fuzz harnesses lived in session scratch and are gone: those runs are attestations,
  not reproducible evidence.

**Open, and owned by nothing yet**

- **This handoff block was itself panel-reviewed, and both lenses found it flattering.** It
  originally described the fallback mitigation in one sentence while three commits fixed defects in
  it, carried a stale test count, and asserted `#163` figures that contradicted `#163`. Corrected
  here. **The merged tree of `#160` was never seen by a lens** — the final panel reviewed `84dc129`,
  three doc/test commits followed, and the PR's review record says so explicitly (`#27`).
- **`#42` reproduced at merge time** on `#160`: posting the review record un-converged it
  (`review_evidence.valid: true`, blockers empty, `mergeable: false`) and needed `--mark-seen`.
  Occurrence data on the issue, not the inbox.
- **`#73` gained a new instance from this session's sweep** — the moved block says *"see the latest
  session's open list"* about `#132`, which resolves to nothing inside the history file. Not
  repaired here; recorded so the count is honest.
- The inbox is **168/150** and unchanged: today's friction went to the tracker (`#161`–`#164`),
  the routing Principle #2 prescribes. The guard-chaining rule (`check && act`) is the one entry
  that lives only there.

▶ Next: **`#163` Sink 1 + `#75`** — every lens run this session (18 of 18) sat on the base commit
with an empty `origin/main...HEAD` diff and re-derived a workaround. But the cheap fix is not the
`git archive` recipe: worktrees share the object store, so `git diff origin/main...<sha>` and
`git show <sha>:<path>` work directly, and the archive recipe was *refused by the sandbox* for one
lens. So: teach the launch prompt to diff against the **named sha** rather than `HEAD` (`#163`
Sink 1), and invert contract item 7 as `#75` actually asks. Then `#124`.

**Then the cs-toolkit thread, and note the vocabulary:** Phase 2's blockers remain
`#41`/`#37`/`#134` as the live blocks below state — all three still open, nothing discharged them.
What this session added is the argument that `#47` is their common cause, and that a prerequisite
slice (`#112`, `#33`, `#133`, `#135`, `#107` — the mutation/drift gate) should land first so the
verification everything after it relies on is trustworthy. That slice is a proposal, not an
established gate; `#164` also remains unfixed and the wrap-up sweep touches that code every session.

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

