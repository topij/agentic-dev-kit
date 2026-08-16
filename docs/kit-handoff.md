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

Last updated: 2026-08-16 — the merge gate's receipt hole closed; the quota posture measured.

## Latest session — 2026-08-16 (the receipt hole closed, and a posture whose two halves compete for one unit)

**Theme —** `#485` shipped (`#488`, squash `5449947`) — the hole the previous block called
the sharpest of its new tickets. Worth carrying: why direction 2 beat direction 1, what the
panel found underneath the fix, and a `#372` measurement that refuted its own first reading
within the hour.

- **`#485` ruled direction 2, and shipped.** `build_report` raises its own
  `merge_blockers` entry from the configured bot's latest review state at the head
  (`objecting_bot_coverage`); no receipt satisfies it. **Direction 1 — refuse inside
  `record_review` — was declined on ordering**, and that is the transferable half: a
  record-time refusal catches only the objection-first sequence, while the realistic one is
  a receipt taken *while the bot is rate-limited*, then the bot recovering and objecting at
  that same head, by which point `record_review` has returned. Merge-time evaluation catches
  both and the no-receipt case besides. No override flag — the head binding is the release
  valve. `#486` folded in, because that PR writes a **second copy** of the
  `covers_head is True` clause pair and a pinned copy beside an unpinned one is how `#447`
  spreads.
- **Filed from the panel:** `#489` (an unparseable `submittedAt` outranks every real
  timestamp — disarms the new blocker *and* forges `#350`'s evidence route; pre-existing,
  verified byte-identical to `main`), `#490` (a no-op commit clears a standing objection),
  `#491` (`unavailable_markers` conflates an outage with a bot configured not to review this
  head, and prescribes the panel for both). `#485` and `#486` closed by hand.
- **`#372` now has the measurement it was held open for**, on the ticket rather than
  restated here — including which direction the reading changed under.
- **Correcting the block below, which lists `#465` as a standing operator ruling:** its
  work shipped the day before that block was written (`#478`). `#465` and `#350` are both
  shipped-and-still-open — no closing keyword was written, by the discipline, and nothing
  retired them. Left open here rather than closed on my own judgement: I verified the
  shipping commit for each, not their acceptance criteria.

**Learned**

- **The `#372` correction is the decision-grade part.** My first comment framed the gap as
  "`pr_watch.py` has no request path", implying a mechanism closes it. I then performed the
  request by hand and the quota refused it. `auto_review` at open and the Converged
  re-request **compete for the same hourly unit**, so automating the request changes *when*
  the refusal arrives, not *whether*. The correction sits beneath the claim on the issue.
- **`#490` is a composition, not a defect in either half.** The head binding is what makes
  the blocker unwedgeable; the receipt is self-reported by design. Each is justified alone;
  together they leave a no-op commit as a clearance path. Neither ticket that argued for
  its half could have found it.
- **The panel's attestation earned its keep separately from its findings.** The correctness
  lens *executed* the REST-vs-`gh` transport claim I had written from reading — it held —
  and both lenses excluded `driftcheck` from their mutation runs, the false-kill trap this
  kit documents.
- **My own prose overclaimed twice, both caught before anyone else read them.** A test
  docstring claimed to pin an *ordering* that `build_report` cannot observe, since it reads
  final state; and the `#372` comment above. `#422`'s subject, twice in one session.

▶ Next: rule on `#372` — it now carries the measurement it was held open for, and the
reading changed mid-session. `#491`'s direction depends on which way it goes, and `#490`'s
only complete fix is blocked on it. `#460` is the other standing operator ruling.

______________________________________________________________________

## Session — 2026-08-16 (the two held rulings, and a fail-open the panel found in the fix for one of them)

**Theme —** the operator ruled on `#372` and `#350`, the two decisions the previous
block named as owned by nobody, and both shipped the same session. The parts worth
carrying are what the ruling on `#372` turned out to rest on, and what the panel found
inside the fix for `#350`.

- **`#372` ruled: reconfigure the trigger** (`#483`, squash `6484c1c`). The decision
  turned on a fact none of the five recorded occurrences had established: **this repo
  has never had a `.coderabbit.yaml`**, in the tree or anywhere in git history. Every
  occurrence was measured against stock defaults, one of which re-reviews on every push
  against a workflow that pushes a new head per fix round. `.coderabbit.yaml` is
  repo-local — absent from `KIT_OWNED`, so it reaches no adopter; verified at the
  destination rather than by reading the allowlist. The transferable half is a new
  `fallback-review-panel.md` section: the kit had extensive machinery for *detecting* an
  unavailable reviewer and none for asking whether it was configured to be available.
  `#372` **stays open** — the improvement is a prediction until a batch measures it.
- **`#350` ruled: direction 1, and shipped** (`#484`, squash `da5158c`). `mergeable`
  now accepts a configured bot's own review of the current head as independent-review
  evidence, alongside the receipt. Direction 2 (a `bot:<name>` literal) was declined on
  the threat model: receipts are self-reported by the agent that wants the merge, so
  that literal would have put the fabricated-receipt path `#428` exists to catch onto
  the gate's critical path.
- **Filed:** `#485` (a receipt authorizes a merge over a bot's live
  `CHANGES_REQUESTED` — `record_review` refuses only on a pending check row, never on
  the submitted verdict; reproduced at `#484`'s base, so it predates that work),
  `#486` (the `covers_head is True` strictness is unpinned — truthiness passes the whole
  suite). Occurrence recorded on `#467`.

**Learned**

- **The panel found a fail-open in the merge gate that nothing else did.** `#484`'s
  first round showed the new route accepted *any* review object at the head, so
  `DISMISSED`, `PENDING` and `CHANGES_REQUESTED` all authorized merges. CI, the suite,
  a three-mutation harness of my own and CodeRabbit's one landed review had all passed it.
- **The docstring's stated reason for not checking something was itself the defect.**
  It gave "`CHANGES_REQUESTED` is its own blocker" as why that state needed no check;
  `reviewDecision` reports *required* reviewers and a bot is typically not one, so the
  blocker never fired. The correction was then itself overstated — it holds on `gh` and
  not on the REST fallback — and a later round caught that too.
- **Two verification habits failed before any code did.** `make test 2>&1 | tail` returns
  *tail's* status, so every "exit 0" this session claimed before the correction was
  reading the pass line, not the exit code. And a `cd` into a base-comparison clone
  outlived its command, so a later grep ran in the wrong tree and reported this work's
  own changes missing — `AGENTS.md` predicts that failure and says it mimics the tool
  misbehaving, which is exactly how it read.
- **A guard can be half-decorative.** `qualifying_bot_coverage` requires two clauses; only
  one had a failing case behind it, and a lens found the other survived the suite. `#447`'s
  shape, one clause over from where the neighbouring docstring warns about `#447`.

**Open, and owned by nothing yet**

- **`#350` needs closing or a note.** Its direction was ruled and the work merged, and no
  closing keyword was written, so nothing retired it — the same state `#439` was left in
  by the same discipline.
- **`#485`** is the sharpest of the new tickets: it is a merge-gate hole in the *receipt*
  path, found only because a lens was probing the new route's neighbour, and it predates
  everything shipped here.
- `#460` and `#465` are the operator-held rulings still standing.

▶ Next: measure `#372`'s prediction — the first PR opened against this `main` is the
first valid data point, since `#484` established that a `.coderabbit.yaml` does not govern
the PR introducing it.

______________________________________________________________________

## Session — 2026-08-15 (five lanes, and the reviewer breaking the fix's own mechanism in three of them)

**Theme —** the second autonomous batch through `parallel-headless.md`, and the first
to reconcile closed. Lanes were clustered on disjoint source footprints and every one
of them landed. What the panels found inside the lanes' own work, and where the
*tickets* were wrong, are the parts worth carrying.

- **Merged:** `#474` (`#399`'s residual — `adopt.md`'s second-tree Step 0), `#476`
  (`#469` — the fresh-path rule surfaced early in the lens prompt), `#477` (`#468` —
  the dead `noise_markers` entry retired), `#475` (`#464` — `kit_doctor`'s status line
  off stdout), `#478` (`#465` — a `held` terminal state, exit code `4`).
  `scripts/reconcile_sessions.sh` over the five launched scopes prints
  `launched 5, merged 5, parked 0` (exit 0); `make test` at the kit root on the merged
  tip `af26133` is green.
- **Lanes whose own fix was broken by their own reviewer, each by execution rather than
  reading:** `#475`'s move-to-stderr left `2>&1` reopening the splice
  unchanged; `#474`'s `cd "$REPO" || exit 1` did not guard its named threat, because
  `cd ""` exits 0 and the `|| exit 1` never fires; `#478`'s repo pin failed open to an
  ambient `$GH_REPO`, letting a lane report `held` off a probe against an unrelated
  repository.
- **Two tickets were wrong in the direction only implementation surfaces, and both
  lanes declined the prescribed route.** `#464`'s "refuse when stdout is not a tty"
  would have silenced the tool for an agent caller, whose stdio is never a tty with no
  redirect in sight — `(st_dev, st_ino)` aliasing shipped instead. `#468`'s implied
  repair — add the bot's current clean-verdict wording as a marker — would have
  silently discarded the operator's own review record on `#43`, because `is_noise()`
  matches bodies with no author check; the dead marker was retired instead.
- **Filed:** `#479` (the lane contract prescribes `dev_session.sh pr-watch <scope>`,
  which cannot run from inside a lane worktree — two lanes hit it independently and
  worked around it two different ways), `#480` (`upgrade.md`'s two-tree hardening is
  fail-open, and it is the file `AGENTS.md` holds up as the hardened one), `#481`
  (`kit-manifest.json` is a derived index, so two kit-touching lanes are never disjoint
  by `parallel.md`'s test).

**Learned**

- **My own filing overstated its subject and this batch disproved it within the hour.**
  `#481` claimed every PR after the first needs a rebase-and-regenerate; three
  consecutive manifest-touching merges landed clean, because the file is one path per
  line and disjoint entries auto-merge. A lane then measured a fresh derivation
  byte-identical to git's auto-merge. The correction sits beneath the claim rather than
  replacing it. The real serialization was `CHANGELOG.md`, which the plan *had* named.
- **An overclaim I relayed into a lane brief was caught downstream by that lane's own
  panel.** `#469`'s body says every round of `#459`'s panel hit an `rm -rf` refusal; the
  round records show one. I copied it from the ticket into the brief, and the
  correctness lens re-derived it and narrowed it everywhere it had propagated —
  including that lane's PR body. `#54`'s subject travelling ticket → cockpit → lane.
- **The lane contract's idle-stall rule did not bind.** A lane backgrounded a poller and
  yielded the turn, against a rule forbidding exactly that, prepended verbatim to its
  prompt. Putting the rule *in the prompt* is `parallel-headless.md`'s stated fix for
  this failure mode; here it was not sufficient.
- **Every merge in this batch rests on a fallback-panel receipt, not a bot review.**
  CodeRabbit was rate-limited on every lane. `#372` has no sharper evidence than a whole
  batch paying for it.
- **`#466` bit the launch again**: the runtime's delegation tool takes no environment, so
  `DEVKIT_REFUSE_UNSANDBOXED_STATE=1` reached no lane. Isolation held on the on-disk
  marker — verified at launch (cockpit exports no `DEVKIT_*`, five distinct sandbox
  roots) and after (no batch PR's state landed in the cockpit's `state/pr-watch/`).

▶ Next: rule on `#372` — the review-bot quota posture. Every lane in this batch paid a
full panel and the review loop dominated its cost; `#478`'s PR carries the round records
if you want the shape of the worst case. The decision is the operator's alone. `#465`'s
shipped exit-code shape and `#460` are the other open rulings.

______________________________________________________________________

## Session — 2026-08-15 (an external field report, read against the kit's own batch record)

**Theme —** an operator-supplied field report (Boris Cherny's dozen daily maintenance
routines — crash fuzzer, dup unifier, dead-code remover — producing mergeable PRs at
scale) assessed against what the kit already carries. Most of it exists here in some
form — the tuning loop as `post-merge-systemize`'s pattern threshold, watch-to-green
as `pr-watch`, autonomous PR production as `parallel-headless` — so the genuinely
missing layer was filed rather than built.

- **Filed: `#472`** — the kit has no workflow kind for a *standing mandate* (a narrow,
  recurring, self-terminating maintenance routine). The ticket carries the full phased
  plan: the contract doc first, a mutation-sentinel worked instance second (the
  `#447`/`#417` class), the scheduling binding deliberately last so the contract is
  hand-runnable before it recurs unattended. The admission rule is the load-bearing
  decision — only mechanically-verifiable, self-merge-class change classes qualify —
  and it is where the external report and the 2026-08-13 overnight batch agree from
  opposite ends.
- What was considered and deliberately not taken is recorded on the ticket, not here
  (per-incident tuning, chat as a reporting surface, app-shaped routines for a repo
  with no app).
- `#251`'s discipline applied to the filing: body posted via `--body-file`, read back
  with `gh issue view --json body`, and diffed against the draft at the kit root —
  the extraction's own trailing newline was the only difference.
- **The wrap-up's own validation caught a stale relay in the just-filed ticket:** its
  body claimed `#447` open, relayed from the 2026-08-13 batch block rather than the
  live tracker — `#447` closed that same day with the `#453` work. Repaired on `#472`
  (its edit history carries the correction) before this commit existed to record it.

▶ Next: `#472` Phase 1 — the contract doc
(`docs/agentic-dev-kit/workflows/routines.md`). The operator-held decisions `#372`
and `#460` still stand ahead of it if ruling is preferred over building.

______________________________________________________________________

## Session — 2026-08-14 (the approved sweep, executed)

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

