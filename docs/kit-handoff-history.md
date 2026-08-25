# Handoff History — agentic-dev-kit

Archived session narratives from [`kit-handoff.md`](kit-handoff.md). Keep active direction
and the next step there; this file is append-only history.

## Session log

## Session — 2026-08-22 · afternoon (a field report acted on, and a remedy moved out of the document it was about)

**Theme —** `#577`, a cs-toolkit field report that is explicitly not a defect report, read
and acted on rather than triaged. Its headline item shipped as `#580`; the rest went to the
tracker. Squash on `main`: `#580`. The one correction this session made to the report ran
in the kit's favour, and only running it in this tree could establish that — which is the
report's own thesis, demonstrated on the report.

- **A remedy written inside the document it is about cannot reach the reader who needs
  it.** `upgrade.md` Step 1 told an operator to diff `$KIT`'s copy of that file against
  theirs; a reader whose copy is out of date is reading the out-of-date copy. `#580`
  moves it to surfaces a stale reader can reach and leaves the paragraph in place saying
  it cannot be the one that saves anyone, so a later pass does not tidy the others away
  as duplicates.

- **The report proposed the adapter or the engine, and neither closes the class alone.**
  A runtime adapter is adopter-owned and Step 4 keeps the adopter's version, so a kit fix
  there never reaches an already-adopted repo; `kit_doctor` reaches every adopter, but
  only from their *next* upgrade, because the copy running Step 1 today is the one
  installed last time. They fail in opposite directions. `#580` ships them and states the
  gap each leaves.

- **`#560` shaped what the new engine block may not say.** It prescribes *reading* the
  fetched copy — safe in every state it fires on — and leaves keep-or-replace to the drift
  list, rather than repeating the blanket "take the kit's copy" that is wrong for a
  `LOCALLY EDITED` one. `test_the_block_does_not_prescribe_replacing_the_file` fails if a
  prescriptive form returns. `#560` stays open; the paragraph it is about is unchanged.

- **A brief's inherited claim reached a commit message as fact, and the report inherited
  it too.** `#558` hardened `_resolve_lane_pr` and the merge gate. The adopter's fork has
  the scrub at the merge gate and not at `_resolve_lane_pr`; the kit's own copy has it at
  each — checked here before relaying it. `#582` is the general form.

- **The configured reviewer answered by editing its earlier skip comment in place.**
  `#509`'s shape. The doctrine's read-the-body-not-the-count rule caught it, and
  `pr_watch`'s `ⓘ review reported:` line named the reviewed sha without being asked. The
  verdict was clean and the merge still rested on the panel receipt, which is the split
  `#350` and `#44` describe working as intended.

- **Filed this session:** `#581`, `#582`, `#583`. Occurrence comments on `#576`, `#507`,
  `#578`. `#577` closed.

- **Verified:** `make test` in `/Users/topi/Coding/agentic-dev-kit` on merged `main` at
  `fabf554` printed `1362 passed`, and `kit_doctor` at the same sha in the same directory
  printed `56 unchanged, 0 differ, 0 missing, 0 unknown`. Before the commit, the new
  render block was mutation-checked with `upgrade_doc` forced to `None` — the mutation
  asserted applied by hash change and marker presence, tests failed, file restored to its
  pre-mutation hash — and each review lens repeated that independently in its own clone
  with the `driftcheck` self-check deselected.

**Learned**

- **Inlining the rendered panel prompt into the lens's own prompt is what made the
  operational parameters bind.** `#578` says a parameter binds where the agent's
  instructions live, not where the prompt points from. This panel passed
  `panel_prompt.py`'s output as the agent prompt itself rather than as a file to go read,
  with the timeout and the no-subagents rule at the top; the `adversarial` and
  `correctness` lenses each ran `make test` to completion, and no lens stalled. Recorded on `#578` as the predicted remedy holding.

- **A field report that says which item matters most is worth taking at its word.** `#577`
  named its own headline and ranked the rest, and that ranking survived contact — the
  headline was the one with a structural fix, and the others were each a defect a careful
  reader eventually catches. The ranking came from the reporter having run the thing.

▶ Next: `#576` item 1 — Step 0's clone is not re-runnable, and the invocations that name
the kit path hardcode it instead of using the `KIT` that Step 0 binds. Re-derive where
those sit; the line numbers in the issue body predate this session's squash. `#580` raised
this item's value rather than touching it — the clone is now also the source of the
*workflow the operator is told to follow*, so a reaped or stale clone mis-sources
instructions and not only files.

## Session — 2026-08-22 · overnight and morning (the batch landed, and a panel that kept finding the narration wrong)

**Theme —** An autonomous overnight batch of isolated lanes, all merged the next
morning; then the friction inbox graduated and swept. Squashes on `main`: `#559`, `#558`,
`#557`. The sweep is `#572`, open and merge-ready at session end. Every defect the review
panel found across the session was in a claim *about* the work rather than in the work —
again, and this time inside the PR that ships the rule against it.

- **The batch shape worked; `merge-gate-scrub` and `upgrade-paths` stalled the same way.**
  Lanes were launched `new --headless` with per-lane merge classes decided at plan time —
  `upgrade-paths` self, the others operator. Both ended their turn awaiting review lenses
  they had spawned themselves, with
  the prohibition verbatim in their injected contract. Distinct from the earlier
  timeout-shaped stalls on `#514`: the explicit `timeout: 600000` in every brief held, and no lane
  stalled on `make test`. Filed as `#564`.

- **The cockpit's obvious way to verify a lane is wrong by default, and the wrong answer
  looks like a lying lane.** A cockpit-side `pr_watch` poll reads the cockpit's state root,
  so a lane's receipt and seen-set are invisible and its finished PR reports as unreviewed
  and unsettled. A correction was drafted on that basis before the lane's own sandbox was
  read; the lane had been right. Principle #3 working, with a failure mode shaped exactly
  like the thing it is not. `#563`.

- **Following `pr-watch`'s Converged step un-converges the PR.** It prescribes posting an
  on-demand review request at the converged head; that comment then blocks `converged`, and
  `reconcile_sessions.sh` reports the lane `open` rather than `held` — so a closeable batch
  reads as not closeable on the surface used to decide. `#562`. The same write also blocked
  a self-merge lane overnight when `--mark-seen` was refused by the permission classifier,
  unattended; `#565`.

- **The panel found a HIGH the author's own verification step should have caught.** Every
  issue the sweep filed carried no labels, against a taxonomy every prior sweep's issues
  use. The `#138` post-landing re-read had run and checked state and title — the mechanism
  that exists for this, too shallow to catch it. The marker now names which fields it
  covered.

- **Round 2 caught round 1's fix breaking a rule that had merged earlier the same morning.** The
  repair for a count ambiguity added counts to prose, which `AGENTS.md`'s `Numbers in prose`
  forbids. The rule shipped as `df32eb2`, which is the very commit round 1 reviewed
  against, so it governed every line round 1 looked at. An earlier phrasing called
  `df32eb2` the *parent* of round 1's base; it **is** that base, and `#579`'s lenses
  split on the ambiguity — one could not trace it, one resolved it to the wrong commit and
  confirmed.

- **Both delta lenses disputed an author draw, and the adversarial one checked the claim
  behind it.** The kept-entry divergence had been tied to `#6` by assertion; `#6` is about
  vendoring the engine and says nothing about disposition semantics, so nobody scoping it
  would have found the question. Now `#575`, which argues the real risk: `finalize_triage.py`
  cannot see *why* a block was not filed, so the first vendored run archives every parked
  entry and silently ends the accumulation it exists for.

- **`triage-friction-log` ran end-to-end for the first time since `#553` rewrote it** —
  `#243`'s slice had no field test until now. The deviations were deliberate and disclosed
  in the marker: approval came in-session because the Slack MCP was unauthorized and no
  notify engine exists (`#573` asks whether that route should be sanctioned or the gate held
  absolute), and an entry was kept rather than swept because it parks for accumulation
  (`#575`).

- **Filed this session:** `#562`, `#563`, `#564`, `#565`, `#566`, `#567`, `#568`, `#569`,
  `#570`, `#571`, `#573`, `#574`, `#575`, `#578`. Occurrence comments on `#509`, `#514`,
  `#511`, `#246`, `#510`, `#534`, `#546`, `#128`.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on merged `main` at
  `df32eb2` printed `1355 passed`, and again on `chore/triage-2026-08-22` at `64fd2b2`.
  `kit_doctor` on merged `main` at `df32eb2`: `56 unchanged, 0 differ, 0 missing, 0 unknown`.
  `#537`'s pins were watched to fail against a reverted wrapper in a throwaway worktree at
  `9de2daa`, with the mutation asserted applied — a non-empty diff against `HEAD`, and the
  scrub markers gone from the wrapper — before the run.

**Learned**

- **A parameter binds where the agent's instructions live, not where the prompt points from.**
  `#514`'s fix — name the timeout, do not plead — worked for every lane, whose briefs
  *are* their instruction set. It failed for every lens on `#572`'s panel, whose wrapper
  points at a `panel_prompt.py`-rendered file they are told to follow exactly. Same words,
  outranked by the document they were attached to; `#578` enumerates them.

- **Knowing a failure does not prevent it when the wrong answer is well-formed.** The
  cs-toolkit brief's own closing warning is about classifying adopter files by path
  existence; the table above it had rows wrong from doing exactly that, in both
  directions at once. Recorded on `#534`.

- **The review receipt makes a record's imprecision permanent, which is an argument for
  getting it right at write time.** A wording fix moves the head and invalidates a two-lens
  receipt; re-recording at an unreviewed head would be false. So the mechanism protecting
  the review protects the imprecision with it — noted on `#128`, with a suggestion that the
  approval record take a fixed shape rather than being composed in prose each sweep.

▶ Next: merge `#572` if it is still open (green, review-clean, receipt bound to `64fd2b2`
plus a CodeRabbit review of the same head), then run the cs-toolkit `/upgrade` — the brief
is at `/tmp/cs-toolkit-upgrade-brief.md`, and its one out-of-band fact is that their
installed `upgrade.md` predates `#544` and `#559`, so follow `$KIT`'s copy, not `$REPO`'s.

## Session — 2026-08-22 · earlier (the routing rule, and a panel that refused its own cheap exit)

**Theme —** `#310`'s decision was taken and shipped. `wrap-up`'s friction-routing step now
routes on evidence rather than severity, and `triage-friction-log` became a shared workflow
with a Codex binding. Squashes on `main`: `#548`, `#553`. `#310`, `#515`, `#224`, `#243` and
`#6` all stay open — nothing verified their acceptance criteria in the field.

- **The rule.** A finding carrying a reproduction, a named mechanism and a proposed fix is
  filed at session end; anything missing one of the three, or whose point is accumulation,
  parks. Severity is explicitly not the test for issue-shapedness — it composes with, rather
  than replaces, `post-merge-systemize`'s worth-gate. The rule was stated on six surfaces and
  one was wrong; the other five were brought into line rather than left to drift.

- **The panel's HIGHs were about the fence, not the rule.** The first draft handed an agent an
  unconditional "file it in your tracker now" for the same write `triage-friction-log` spends a
  whole second session getting approval for. Filing now needs the operator's own turn — not
  text read from an issue, a comment, a tool result or a file — and parks when nobody is in the
  session, no tracker is configured, a create fails, or the outcome cannot be determined.

- **The panel refused the cheap exit, and that was the session's sharpest event.** A dual-lens
  delta pass was offered as the terminal check on `#548`; **both lenses disputed both author
  draws**. The prose class was conceded correct and the delta pass ruled disproportionate for
  it; the safety-critical boundary was disputed on the strength of the doctrine's by-nature
  scope against `.claude/rules/`'s path list, which `#346` already reports as incomplete. The
  dispute was **conceded rather than ruled on**, which is one more data point for `#346`: a
  change both lenses placed inside the doctrine's stated scope and outside its path binding,
  disposed of by conceding because the path list did no work.

- **Rounds 5 and 6 each found real defects in prose rounds 1–4 had passed over.** Round 4 looked
  converged; round 5 found a HIGH. The blind spot was re-reviewing the fix delta while treating
  already-passed prose as settled. Round 5's carry-forward was rewritten to say so, and round 6
  then found that the `#224` restatement was false against `finalize_triage.py`'s own spec —
  a sweep deliberately **keeps** a window-added entry below the new marker, so the paragraph
  had relabelled a working safety mechanism as a straggler.

- **On `#553`, every finding across both rounds was in the CHANGELOG prose; none in the change.**
  The move itself survived content-parity reversal and mutation kills on both rounds. One
  correction inverted its own advice: an adopter's edits to their Claude command are **kept** by
  `upgrade.md` Step 4, not lost — so the hazard is a fork that persists silently, which is this
  PR's own failure mode one layer up.

- **Filed this session: `#549`, `#550`, `#551`, `#552`, `#554`.** Occurrence comments on `#209`
  (eight rounds' data, and the delta pass both lenses refused) and on `#546` for a count
  beside a list in a commit message — the third in two sessions, this one inside the PR
  rewriting the surrounding doctrine.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on each branch head before
  its push, and again on merged `main` after both squashes. `kit_doctor` on merged `main`:
  56 unchanged, 0 differ, 0 missing, 0 unknown.

**Learned**

- **The defects clustered in claims about the work, not the work.** Across eight panel rounds on
  two docs-only PRs, the code, the move and the guards came back clean under mutation every
  time; what kept being wrong was what I said about them — an overclaimed checkpoint, a
  mislabelled `kit_doctor` state, an inverted refresh forecast, a positional invariant the
  mechanism breaks.

- **A lens that executes beats a lens that reads, and the gap was measurable.** The `kit_doctor`
  claims that survived were the ones a lens ran four scenarios against; the ones beside them
  that died were the ones I had verified against nothing.

- **Both merges went in without a review receipt, on operator instruction.** `#548`'s merge class
  was operator-merge by the conceded dispute. The gap is recorded on both PRs rather than
  papered over with a receipt — the next session should read the friction-routing step knowing
  its terminal delta had no lens on it.

▶ Next: the friction inbox is over budget and un-graduated, and `triage-friction-log` — the
workflow `#553` just rewrote — is the way to clear it. Running it end-to-end is also the first
field test of that rewrite, which is what `#243`'s slice still lacks.

## Session — 2026-08-21 (the adopter's findings, and a loop that reviewed its own guards)

**Theme —** cs-toolkit's `/upgrade` findings worked end to end. `#535`'s regression, `#536`'s
items and `#534`'s cause 3 all merged (`#538`, `#544`, `#545`); every one of those issues
stays open, since nothing verified their acceptance criteria in the field.

- **`#535` was upstream of where the issue pointed.** `#521`'s deference was correct; the
  FETCH under it was not — identity resolved only for rows that could cancel a pending
  block, so a healthy mid-review row never had one and `trusted` was never true. The
  precondition now covers both consumers. Fixed in the field on its own PR: `coverage: []`,
  a comment-surface entry with no trust field beside a trusted check entry, and `review
  owed` correctly silent via the check.

- **The panel found the defect the fix introduced, not the one it fixed.** `accounted`
  read `.get("trusted", True)`, and a comment-surface entry carries no such key — so one
  stale acknowledged outage comment would have silenced `review owed` for a PR's whole
  life. `summarize_review_bots`' own docstring forbids exactly that ("a comment is a
  statement about the past"), one layer below where I broke it.

- **On `#544` and `#545`, nothing executable changed after the first commit.** Diffed each
  branch's first commit against its head: test files and the manifest, plus one
  comment-only edit to `config/dev-model.yaml` (checked — no key or value moved). No
  prescribed `upgrade.md` command and no `ENGINE_DIR` substitution changed. So on those two
  the review turned inward — the HIGHs were in guards, several in the previous round's guard.
  `#538` is the counterexample and the claim does not reach it: its `accounted` fix
  (`d6e371d`, a later commit) changed an executable line. Stopping was by blast radius,
  per the doctrine — not because a round came back clean.

- **The reason that was possible is now closed on both.** Each guard was pinned only to
  the real tree, which holds none of the shapes it exists to catch, so the suite could not
  tell a fixed guard from a broken one — lenses proved it by reintroducing earlier bugs
  and watching the suite stay green. Both are pinned on synthetic fixtures now, and
  `#544`'s fixture records which shapes discriminate and which are defence-in-depth,
  rather than implying a clean sweep.

- **Filed this session: `#537`** (the adopter's declined `dev_session.sh` carries a
  merge-gate hardening the kit lacks — the kit's own test certifies the fork), **`#540`**,
  **`#541`**, **`#542`**, **`#543`**, **`#546`**. Occurrence comments on `#325` (panel
  isolation holds for writes and failed for reads; the cockpit's own launch note was the
  mechanism) and a scope comment on `#534`.

- **The operator's unfiled candidates were all filed, none rejected** — `#540`, `#541`,
  `#542`. `#541` went in despite being pre-existing because its consequence
  changed: under coverage alone a truncated reviews list only ever refused a merge; with
  `#488`'s objection blocker reading the same list it can now authorize one.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on each branch head
  before its push, and again on `#545`'s merge commit after taking `origin/main` in. Each
  PR's record carries its own result at the sha it was taken from.

**Learned**

- **Across both files I kept keying a guard on what text LOOKED like instead of asserting
  the required form** — a line wrap, quotes and `=`, a shell continuation, a
  fence tag, a `$ ` prompt; an operator, an attribute, a constructor, a wrapper on the
  other operand. That is `safety-critical-changes.md` rule 1 ("treat 'we tightened the
  matcher' as a stopgap") and I did not see the shape until a lens had refuted the fifth.

- **The completeness claim was the more reliable defect than the code.** Round after
  round I declared a class closed and a lens found another member. Asserting closure is
  worse than leaving a gap open, because the assertion gives the next reader a reason to
  stop looking — the draws that finally worked named my own worst track record and asked
  the lenses to attack it.

- **A rule that binds one surface does not bind the author writing another.** `wrap-up.md`
  forbids a count beside a list; I broke that in docstrings and commit messages all
  session, each time in the commit that grew the list. Filed as `#546` — it is `#243`'s
  shape applied to surfaces rather than runtimes, and it tensions with `#54`, which asks
  for a command's actual result.

- **A lens verifying a declared LIMITATION is worth more than one confirming a claim.**
  The round that added most was one that built the real defect in a real scanned file and
  watched the guard pass over it, and one that checked my stated gaps were honest rather
  than that my stated capabilities worked.

▶ Next: `#537` — the merge-gate scrub the adopter's fork carries and the kit lacks. It was
blocked on `#534` cause 3, which merged today, so the test that pins it can now be written
against the kit's own `dev_session.sh` rather than an adopter's.

## Session — 2026-08-20 · afternoon (the third ruling, and the panel that corrected its own transcription)

**Theme —** executed the morning briefing's plan end-to-end. `#524` applied; `#372` ruled
(third ruling: the panel is the standing reviewer, detection surface frozen — the ruling
and its same-day correction are on the ticket); the ruling's doctrine follow-up plus three
delegated fixes driven through the full panel loop to merge. Squashes on `main`: `#529`
(upgrade.md `${KIT:?}` guards, addresses `#496`), `#530` (`review_evidence.head` nulled on
the bot-coverage route, addresses `#495`), `#528` (pr-watch.md converged step carries the
ruling), `#527` (manifest tracks the kit's own test suite, addresses `#493`). All four
issues stay open — nothing verified their acceptance criteria in the field.

- **The gap `#524` names is shut at the forge: ruleset `protect-main` is `active`** — PR required
  (0 approvals), `toolkit` required and pinned to the GitHub Actions `integration_id`
  (`#95`'s identity rule applied to the forge gate), deletion + non-fast-forward kept, no
  bypass actors. Verified: `gh api repos/topij/agentic-dev-kit/rules/branches/main` lists
  all four rule types, run from this repo's root.
- **The session's sharpest event: `#528`'s adversarial lens executed
  `bot_comment_verdicts()` against the live history and refuted the ruling it was
  reviewing the transcription of.** The ruling's receipt-time-re-read item had conflated
  `#519`'s conjunction-disqualification with `#525`'s count-blind hand-rolled loop — the
  engine would have seen `#525` — and carried a figure that measured the blind loop, not
  the bot. Corrected on `#372`; the fix round shortened rather than corrected, and round 2
  found only lens-labeled cosmetic Lows on the shortened text.
- **The ruling was field-tested the same afternoon, on the ticket:** `#529`'s
  converged-head request delivered a comment-only clean review the `ⓘ review reported`
  line caught; `#530`'s, a minute later, hit the quota wall, reported on both surfaces;
  `⚠ review owed` fired at both convergences. Neither outcome was waited on; both merges
  stood on dual-lens `fallback:panel` receipts.
- **`#527` took three rounds** (finding → fix → merge-resolution). The round-3 re-run over
  a "mechanical" merge delta found a real Medium (`#532`) — evidence against inventing a
  cheaper carve-out for merge-resolution deltas.
- **Filed this session: `#531`** (an adopter's own `conftest.py` misjudged via the
  engine-role basename), **`#532`** (KIT_OWNED role labels pinned by nothing — the guards
  derive their universe from the tuple they guard). Occurrence comments: `#372` (ruling,
  correction, two request outcomes), `#480` (executed evidence: `cd ""` is a no-op success
  in bash/zsh/sh; the false prose claim beneath the patched block; the test-name
  overclaim), `#496` (behavioral-pin residual), `#506` (`#532`'s shape). Caps posted on
  `#44` and `#509` — records and occurrence landing places now, not build backlog.
- **The cs-toolkit upgrade boundary is reached (`#504`):** precondition 1 by the `#372`
  ruling, precondition 2 by `#529`/`#530`/`#527` shipping the `#497` fix set. `kit_doctor`
  now drift-checks vendored tests — the exact hazard `#493` measured on that repo.
- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on each PR's final
  branch head before its push — each PR's record carries its own summary line.

**Learned**

- **A ruling written from the trail's latest occurrence comment inherited the trail's
  uncorrected layer.** The refuting evidence route was execution, not reading — the same
  lesson the lens contract's "Execute, don't only read" already carries, arriving on the
  record-authoring side.
- **This morning's delegate-stall friction entry recurred with its proposed fix applied
  verbatim and not binding.** What bound was a follow-up naming a concrete 600000ms
  timeout for the verification command: the stall is timeout-shaped, not
  obedience-shaped — `#514`'s carrier-not-wording, again.
- **Two same-session converged-head requests competed for the hourly unit a minute
  apart** — the first delivered, the second walled. Under the panel-as-reviewer posture
  that budget is corroboration, not review capacity, so this costs nothing.

▶ Next: run `/upgrade` on cs-toolkit — `#504`'s preconditions are both met. At upgrade
time re-run the CHANGES_REQUESTED sweep (non-zero pulls `#499` ahead), and fold CUS-1293
(`panel_prompt.py`: copy it or document the decline) and CUS-1306 (merge the
operator-merge `paths:` glob into the shared doc) into the same pass. Behind it: `#532`
is a clean self-contained build; `#310` is still the operator decision nobody has made.

## Session — 2026-08-20 · morning (the enforcement under the gate, and an author who was the unreliable narrator)

**Theme —** cross-repo. `#525` shipped here (`#95`'s forgery route at `#521`'s site, squash `6201af6`); `ci-gate`
shipped in the cs-toolkit adopter (`4e743dc3`). Both PRs' review rounds found real defects and
**every one was in the record prose, not the mechanism** — the diffs came through clean and the
narration did not.

- **`#524`: this repo's `main` is protected by convention only.** No classic protection
  (404), `rules/branches/main` empty, the sole ruleset `dont-delete-main` left
  `enforcement: disabled` since it was created. `scripts/hooks/pre-push` guards only
  `dev/*` pushes touching the narrative files, so a direct push to `main` reaches its
  `exit 0`. The kit ships the rule it does not enforce on itself. An enable script is
  with the operator; **not applied** — the finding stands until it is.

- **The adopter is better protected than the kit.** cs-toolkit's ruleset requires a PR
  (0 approvals) but carries no `required_status_checks`. Closing that meant a `ci-gate`
  aggregate job rather than a protection edit, because most of its checks are
  matrix-generated and requiring those names wedges every PR the moment a package moves.
  Tracked adopter-side; `CUS-1307` (nothing enforces `ci-gate.needs` stays complete) and
  `CUS-1308` (`always()` vs `!cancelled()` on a gate job) came out of its review.

- **`#372`: `#525` was reviewed, and this session's first account of it was wrong.** The
  request at the converged head *completed* — as a comment-only clean review naming its
  range (`6905aac` → `89939c0`) and reporting zero units remaining. The bot corrected the
  record on the ticket before this block was written. What made it look like silence: the
  acknowledgement comment was **mutated in place** into the review, and a poll that counts
  comments cannot see an update — `#509`'s mutable-surface hazard, paid. `#525` is therefore
  `#44`'s comment-only shape (a detection problem), and the adopter's `#2044` is the quota
  one; they are not one cause. `#498`'s convergence-only ruling **did** take effect: the one
  unit was spent on the merging head, which is what it was for.

- **`#518` got its field evidence and the line works.** `⚠ review owed` fired unprompted at
  `#525`'s converged head and was acted on rather than merged past. `#522` reproduced in the
  same output — the `✅ DONE — green, reviewed` banner sits four lines above it.

- **Filed this session: `#524`; `CUS-1307`, `CUS-1308`. Occurrence comments on `#372`,
  and the cs-toolkit routing audit on `CUS-1306`.** That audit's finding: the `paths:` glob
  binding the operator-merge rule exists only in `.claude/rules/`, so the runtime entering
  through `AGENTS.md` gets the doctrine with no file list at all — `#243`/`#273`'s failure,
  live in an adopter. Bidirectional drift, so it needs a merge and not a copy.

- **Verified:** `make test` at `/Users/topi/Coding/agentic-dev-kit` on the `#525` branch,
  and `make check-root` at `/Users/topi/Coding/in-parallel/cs-toolkit` — both passed, exit 0.
  Counts deliberately not restated: the commands own them, and each PR's own record carries
  the figure at the sha it was taken from.

**Learned**

- **A measurement taken from a still-running workflow read as a finished one.** A CI-cost
  figure was gathered with a `.jobs[] | select(.conclusion != null)` filter while the run was
  in flight; the filter silently dropped the unfinished jobs, including the long pole, and the
  partial set was reported as the total — into a commit message and a PR body, off by
  roughly fourfold. This is `settle_grace_minutes`' own failure mode committed by hand, one
  layer up: a count cannot tell you it is incomplete. Assert the run is `completed` before
  reading any figure off it.

- **The correction was wrong too, in the opposite direction.** The `if: always()` claim was
  repaired once and still false — GitHub documents `always()` as running "even when
  canceled", which is why its docs recommend `!cancelled()`. The delta pass caught it against
  primary sources. The third version asserts only what holds either way. `fallback-review-panel.md`'s
  "shorten, don't correct" is the rule that would have skipped two rounds.

- **Both lenses found the same structural gap from opposite directions**, and neither found
  it in the diff — the adversarial lens hunting a bypass, the correctness lens checking claims
  against the tree, both landing on `ci-gate.needs` having no enforcement. Disjoint lenses
  converging is the panel doctrine's claim; this is an instance of it.

- **A delegated implementer left its work uncommitted on `main` and stalled awaiting a
  notification that was never coming.** Nothing was pushed, so nothing was violated — the only
  thing preventing a commit to `main` was the agent not getting that far, which is `#524`
  demonstrating itself the same hour it was filed.

- **A CHANGELOG placeholder cannot survive this repo's own suite.**
  `test_real_changelog_headings_match_the_extraction_pattern` runs against the real file, so a
  `#TBD` heading fails `make test` by construction. Any split where an implementer pushes and
  the cockpit opens the PR hits this; the number has to be substituted before the suite can pass.
  Related to `#507`.

▶ Next: `#524` is the session's own unfinished business — the enable script is drafted and
unapplied, and until it runs every ground rule about `main` here rests on agents obeying it.
Behind it: `#44`/`#509` are where `#372`'s remaining weight sits now that the review turned
out to have happened and the gate could not see it, and `#310` is still the operator decision
nobody has made.

## Session — 2026-08-19 (a gate predicate used to answer a report's question, and a review the gate could see)

**Theme —** `#518` shipped (`#520`, squash `ab2bdad`): the converged head now names each
configured reviewer that has not looked at it. The line's first cut was wrong, and wrong
again in a second way after the first fix; the panel caught both before they reached
`main`. `#518` stays open — nothing verified its acceptance criteria in the field.

- **What shipped.** `⚠ review owed` at convergence, per configured bot, gated on the
  reviewer read having succeeded. `pr-watch.md`'s converged step settles that request
  *before* reading `mergeable` and says an already-true `mergeable` does not discharge it —
  which is the exit ramp `#516` took out of the loop. Reported only: the gate is untouched
  and a `fallback:panel` receipt still authorizes while the line still prints.

- **The defect worth carrying past this PR: a merge-gate predicate is not a report
  predicate.** The line read `qualifying_bot_coverage`, which under-reports *by design*
  because it feeds a gate, where under-reporting refuses a merge and is harmless. In a
  report the same bias asserts nobody reviewed the diff — false both where a bot had
  objected on the head and where the check read had failed, each reproduced before
  acting. Both lenses found it independently. In the friction log as
  a doctrine candidate; deliberately not a ticket — the instance is already handled in `#520`, and the
  general shape is the part worth keeping.

- **`#95`'s forgery, one namespace over.** The suppression trusted `_match_bot` over a check
  **name** — a substring match — so a same-repo workflow holding `checks: write` could
  silence "nobody has reviewed this" on its own PR. `review_bots.pending` now carries
  `identity`/`trusted`, and `blocking` deliberately does not read them so the gate stays
  fail-closed.

- **Filed this session: `#521` (the same forgery against the pre-existing coverage warning,
  which `#520` deliberately did not widen into), `#522` (the `DONE` banner says "reviewed"
  four lines above `review owed`).** Occurrence comments on `#506` and `#372`.

- **Verified:** `make test` at the repo root on merged `ab2bdad` — 1304 passed, exit 0.

**Learned**

- **`#372`: the request at the converged head produced a review the gate could see.**
  `@coderabbitai full review` at `#520`'s converged head produced a real review object and
  satisfied the `bot-coverage` route with no receipt needed. Read it against the runs
  already on that ticket rather than on its own: `#501`, where the request produced
  nothing, and `#519`, where it produced a genuine review that no detection route could
  see. What separates this run from those is unclassified, and the caution that ticket already
  carries about the detection routes is untouched by a run that happened to be detected.
  It did find a real defect the panel had missed, which is evidence against treating the
  panel as a standing replacement for the reviewer — one of the three postures `#372` is
  held open to decide.

- **`#506`'s shape recurred in a variant its own remedy does not catch.** Separate terms of
  one `if` were pinned by nothing, each found only by mutation and none by reading — by
  either lens, or by the author. The sharpest: an assertion placed in the neighbouring
  sibling test, whose fixtures carry an unacked comment and therefore never converge, so it
  passed while asserting nothing about a state it could not construct. "Extend the sibling's
  test" is *how it got there*. The occurrence on `#506` proposes the sharpening — a new term
  needs a case where that term alone decides the outcome.

- **The panel and the bot found disjoint defects, in both directions.** The lenses found the
  gate-predicate inversion and the forgery route; the bot then found a `CHANGELOG` sentence
  that was true when written and made false by a later bullet in the same entry, which the
  panel had read past. Neither substitutes for the other, which is what the panel
  doctrine claims and what this session observed rather than assumed.

▶ Next: `#518` and `#372` both want field evidence, and the next PR against this `main` is
the cheapest source of it — open with `session-start` and let the poll speak. Specifically:
does `⚠ review owed` fire at convergence and get acted on without prompting, and does a
second explicit request at the converged head deliver a review object the way `#520`'s did
and `#501`'s did not. Behind those: `#521` is a clean self-contained build, and `#310` is
still the operator decision nobody has made.

## Session — 2026-08-18 (a triage sweep, an overclaim the wrap-up's own panel caught, and `#372`'s data point at last)

**Theme —** ran `triage-friction-log` on the inbox that had rebuilt since `#470`'s
2026-08-14 sweep, filed the batch, and ran `pr-watch` on the resulting PR. CodeRabbit
never reviewed `#516` — the same `reviews: []`, no-request shape `#499` and `#500`
already showed the day `#498` landed, not a first occurrence as this block's own
first draft claimed (caught by this PR's own fallback panel before it reached
`main`).

- **Triaged the friction log: filed `#506`–`#515` and occurrence comments on `#372`,
  `#467`, `#435`, merged `#516`** (squash `3f25620`). Engine still not vendored
  (`#6`); run by hand against the workflow's prose. Approval was a Slack "lgtm"
  bulk-approve.
- **The fallback panel (adversarial + correctness) found two real things and disposed
  of both without touching `#516`'s diff.** `#508`'s body had dropped its source
  entry's safety caveat when condensed from the friction log — fixed directly via
  `gh issue edit` (a tracker-side edit costs no review round). The marker's own
  "fifteen accounted for" arithmetic reads as off-by-one on a literal skim (it is
  correct: 11 entries via issues + 4 via three comments) — logged rather than fixed,
  filed as `#517`.
- **`#516` merged with no CodeRabbit review object at all** (`gh pr view 516 --json
  reviews` → `[]`). The check-surface-unavailable rule fired on the very first poll —
  `auto_review.enabled: false` posts the skip notice at PR-open now, every time — and
  the panel satisfied `mergeable` before convergence, so the Converged step's own
  "request a review" bullet was never revisited. Filed as `#518`: that bullet is
  unconditional on `review_bots.coverage`, but reads, once a panel receipt already
  exists, like something already handled.
- **A hand-splice mistake in the archive sweep** (consumed the previous sweep's own
  section heading, orphaning its intro paragraph) was caught only by diffing the
  archive's pre-existing content against `origin/main` before committing — no damage
  landed. Occurrence recorded on `#6`.

**Learned**

- **All 15 friction-log entries this round were already issue-shaped — zero needed
  the inbox's waiting-room function.** Fresh evidence for `#310`'s claim (open since
  `08-05`) that `wrap-up` step 5 parks what the routing doctrine already says to file.
  The operator asked about this live; no new ticket needed, `#310` already names the
  fix — undecided whether to implement it or just add the occurrence.
- **`#516`'s non-attempt is at least the third instance, not the first.** This
  block's own first draft claimed `#516` was the first live PR since `#498`'s ruling 2
  to go unreviewed — wrong, caught by this PR's own fallback panel: `#499` and `#500`
  (2026-08-17, same day as `#498`) already merged with `reviews: []` and no request
  ever posted. `#501`, later that same day, is the only prior PR to have actually
  attempted the explicit request — twice, both empty, cause unclassified — and its
  ticket comment says a later PR is needed before ruling further.
- **`#372` has a data point, and it is stranger than "the request works."** An
  explicit `@coderabbitai full review` on `#519` produced a genuine completed review
  — clean verdict, full walkthrough, "0 remain after this review". First read
  against `review_bots.comment_verdicts` showed it picked up; re-checked live before
  this line was written, and it does not — the one comment carrying that verdict is
  the *same* comment CodeRabbit posted at PR-open with the "review skipped, auto
  reviews disabled" notice, edited in place to append the walkthrough **without
  removing the skip text**, so the comment now matches an `unavailable_markers` entry
  and disqualifies itself. Structurally, right now: `reviews: []` and
  `comment_verdicts: []` both — this PR currently has no detectable independent
  review at all, despite CodeRabbit having genuinely produced one. The mutable-comment
  problem this file already named on `2026-08-17` just defeated its own documented
  workaround, live, in this PR.

▶ Next: `#372` needs this written up properly — the explicit request *can* produce a
real review, but neither of this repo's two detection routes (`reviews[]`,
`comment_verdicts`) reliably see it once the vendor's in-place edit adds the skip
notice back onto the same comment. Whether that argues for a third detection route,
a different bot config, or accepting the fallback panel as the standing reviewer is
the operator's call — not pre-empted here. `#518` still stands separately: the loop
needs to actually reach the request step before any of this happens automatically.
Behind it: whether to act on `#310` (occurrence comment vs. implementing its
routing fix — operator hasn't
decided).

## Session — 2026-08-17 (three rulings shipped, and the defect that would have reached an adopter was a heading)

**Theme —** the operator ruled on `#372` and on `#44`, and `#494` — the fail-open the
previous session's ticket sweep had just filed against `#488` — was closed between them.
Shipped: `#372` (`#498`, squash `9f912e5`), `#494` (`#499`, `fa8d490`), `#44` (`#500`,
`4276654`). All three issues stay open; no closing keyword was written and nothing
verified their acceptance criteria.

- **`#372` ruled: convergence-only — and the first PR that tested it failed.**
  `auto_review.enabled: false`, so the one hourly unit is spent at the head that merges
  rather than the head that opens. The measurement that decided it is on the ticket: on
  `#488` the auto pass at open and the Converged re-request **competed for the same
  unit**. Paying was declined by the operator on cost, which discharges the conditional
  deferral the 2026-08-15 ruling had left standing.

  **Do not read this as a working posture.** `#501` — this wrap-up's own PR, and the
  first the ruling actually governs — requested review at its converged head and
  **`gh pr view 501 --json reviews` stayed empty**: no review object, no coverage, no
  verdict. That puts ruling 2 in question on the one ground that matters: it moved the
  whole review budget onto a request path that then did not deliver. Ruling 1
  (`auto_incremental_review: false`) is untouched and still measured. The account and the
  options it leaves are on `#372`; the next PR against this `main` is the second data
  point.

  **The evidence is stated as the empty review list on purpose.** The bot's own status
  comments rewrite themselves in place, and successive readings of one comment on `#501`
  gave different accounts of what had happened — two of which reached this file or that
  ticket before being corrected. **How many times it was rewritten is not knowable**:
  `updated_at` exposes only the most recent edit, so any count is a floor, and the count
  I first wrote here was wrong before the commit landed. That is the point rather than an
  aside — a tally off that surface is a claim about when you looked. The absent review
  object is not.
- **`#44` ruled: report it, never gate on it.** `review_bots.comment_verdicts` surfaces a
  comment-borne clean verdict; no gate reads it. Direction (a) — parse it into `coverage`
  so the gate self-clears — was declined because the failure modes are not symmetric:
  keying the *gate* on a reviewer's prose lets an upstream wording change decide merges,
  while keying a *report* on it lets a line go missing. `bot_review_coverage`'s docstring
  was already the standing argument, and is cited rather than restated.
- **`#494`'s fail-open shipped a fix: the objection now has its own read** over verdict
  states only. Directions 2 and 3 were declined on the ticket. The two reductions are one
  parameterized walk, not two copies — `#447` (the record for that shape) is why.
  Worded this way deliberately: "`#494` closed by …" reads on a skim as the *ticket*
  being closed, which it is not.

**Learned**

- **Three rulings' worth of panel found no gate defect; the thing that would have reached
  an adopter was a CHANGELOG heading.** `#499`'s entry was headed with the *issue* number,
  and `upgrade.md` Step 3 extracts by *PR* number — so a `BREAKING (gate semantics)` entry
  would have been invisible to the documented upgrade path (`#430`'s failure, on the file
  written to prevent it). Found because a lens **ran** the extraction rather than reading
  the file. Nothing in CI checks this correspondence.
- **`#447`'s shape recurred three times in one session**, each time found by mutation and
  never by reading: a new field added beside pinned siblings inherits exactly the gaps the
  siblings had already closed (`#499`'s objections scoping; `#500`'s config key and its
  render line). Logged to the inbox as a candidate rule rather than a ticket, because the
  third occurrence is what makes it a pattern.
- **Every fix round in this session produced a prose imprecision the next round found.**
  That is the doctrine's own claim observed under its own procedure, and it is the
  argument for the log-don't-fix carve-out — the cost of a round is another round's worth
  of new prose to get wrong.
- **A trigger heuristic `#44` had relied on since 2026-07-27 is falsified:** an explicit
  review request does *not* reliably produce a review object. Recorded on the ticket with
  the observation, and it retires "just re-request it" as operational advice.

▶ Next: open the next PR and watch what its converged-head review request does — that is
`#372`'s second data point and it decides whether ruling 2 stands, gets reverted, or is
renamed to "the panel is the reviewer". Behind it: `#460` (the last standing operator
ruling, untouched today) and `#489` (an unparseable `submittedAt` still outranks every
real timestamp, so a standing objection cannot yet be fully relied on even after `#494`).

## Session — 2026-08-16 (the receipt route closed, an upstream bypass left open, and a posture whose halves compete for one unit)

**Theme —** `#485` shipped (`#488`, squash `5449947`) — the hole the previous block called
the sharpest of its new tickets. Worth carrying: why direction 2 beat direction 1, what the
panel found underneath the fix, and a `#372` measurement that refuted its own first reading
within the hour.

**What is and is not closed**, because the two are one function apart and the distinction
governs whether the gate can be relied on: `#485`'s **receipt route** is closed — no
receipt satisfies the new blocker. `#489` is a **separate, pre-existing bypass upstream of
it**: an unparseable `submittedAt` makes the coverage read pick the wrong review, so the
objection never becomes the latest state and the blocker never fires. Untouched by `#488`,
verified byte-identical to `main`, and open. Nothing here should be read as "a standing
objection can now always stop a merge."

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
- Nothing else in the 2026-08-10 block's open list moved this session (that block is
  now in [`kit-handoff-history.md`](kit-handoff-history.md); swept 2026-08-13).

▶ Next: **cs-toolkit kit refresh** — carried forward untouched from the 2026-08-10 block
(now in [`kit-handoff-history.md`](kit-handoff-history.md))
below; read its bullet there for the verified preconditions rather than trusting this line.

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

## Session — 2026-08-09 (the adopter's Phase 3 findings, worked back into the kit)

**Theme —** cs-toolkit's Phase 3 filed seven kit issues and left an adopter holding
`init.sh`. Six were worked and all four PRs merged; the seventh needs a runtime this host
cannot start. The panel found far more than the issues did, and the HIGHs clustered
entirely in the one feature that was new code rather than a correction.

- **`#387` merged (`ccbed71`) — `#385`, the blocking one.** `init.sh` no longer imposes a
  `reports/` ignore. The seeding splits into *hygiene* (unconditional, always-wins — a
  leak helps nobody) and *policy*, which declines to write when the repo disagrees: it
  already tracks files the entry would hide (asked of `git ls-files -i -c --exclude=`, so
  git's own matcher answers) or already carries a rule for that path. `state/` and
  `reports/` are anchored too.
- **`#389` merged (`dd2c001`) — `#379`, `#381`, `#386`'s `kit_doctor` half, `#383` item 2.** `kit_doctor` reports whether each hook registration
  RESOLVES, per surface, and only a dead path reaches the exit code. Not by hash: those
  files are the adopter's, which is why `init.sh` only prints them (`#303`), and hashing
  would report every adopter `locally-edited` forever — `#286`'s failure. A declined
  `pre-push` now reads `· declined (recorded in not_installed)`.
- **`#390` merged (`d2cd509`) — `#382`.** `adopt.md` and `upgrade.md` stopped telling
  operators the installer is manifest-untracked. The convergence plan records Phase 3 as
  merged and carries its two defects: a phase cs-toolkit does not declare, and SessionStart
  wiring assigned to both the kit and the adopter.
- **`#391` merged (`99ef579`) — `#383`, and the `init.sh` half of `#386`.** The installer's
  comment scanner no longer closes a double-quoted scalar at an escaped quote, which had
  `set_field` re-attaching a fragment of the adopter's own value as a comment.
- **Filed: `#388`** (no state for a kit-owned file installed but PINNED — `--record-install`
  refuses it and drops the whole `not_installed` declaration; reproduced against a clone of
  the adopter), **`#392`** (a registration built from an unknown shell variable is
  `unresolvable` and never reaches the exit code) and **`#393`** (a test that depends on
  `json.loads` raising `RecursionError`, which stops being true on 3.14). Occurrence
  comment on `#88`.
- **`#380` is blocked, not skipped.** `codex-cli 0.42.0` here cannot start a session
  (`400`, "requires a newer version of Codex"), so the fire-check is still owed. The
  `matcher` half is settled: the one real `SessionStart` registration on this machine
  carries **no `matcher` key at all**, against what the plan assumed from documentation.

**Learned**

- **A regression test can be masked by its own fixture.** `#387`'s flagship test was
  written to catch the anchoring defect and did not: its fixture pre-seeded a rule that
  made the guard return before anchoring was ever exercised, so reverting the fix left it
  green. Found by a lens mutating the line, not by reading. Three more of the same shape
  followed in one session — a property named in a comment and pinned by nothing — which is
  a pattern, not four accidents.
- **A liveness check that lies is worse than one that stays silent.** `#389`'s first
  version reported `✓ resolves` for `…/pr_followup_hook.py.disabled`, because the token
  stopped at the kit's filename and the real file exists. Renaming is the most ordinary way
  to disable a hook. Before the feature the doctor said nothing; with the bug it said
  something false, confidently — `#379`'s own failure mode, manufactured by `#379`'s fix.
- **Two rounds later the same guess failed at the other end**, and that is the more useful
  lesson: a hand-rolled scan of a shell command will keep disagreeing with the shell, in
  shapes nobody enumerates in advance. The fix that held was deleting the guess — `shlex`
  is the shell's own lexer and it is in the standard library. Patching the instance twice
  cost two rounds; replacing the mechanism cost one.
- **Volatile figures went stale three times in one session**, each caught by a lens: a
  tracked-file count, a grep count, and a doctor report that this session's own manifest
  bump falsified. Every one is now the command that produces it.
- **The adopter's review bot is not the only free audit.** CodeRabbit was rate-limited on
  every PR, so the panel was the gate throughout — more than a dozen rounds across the
  four. Count them from the `## Fallback panel — round N` headers on each PR rather than
  from a figure here; two figures in this very block were wrong when a lens counted them.
  The severity did not decay the way a fix-round sequence is supposed to: `#389`'s HIGHs
  kept arriving into its final rounds. Its round-10 comment carries the round-by-round
  table; read the count there rather than here, because three drafts of this sentence
  carried three different numbers and a lens had to recount from the PR to settle it.
  Every one of them came from a lens executing the changed path rather than reading it.

**Open, and owned by nothing yet**

- **`#395` is the open design question `#389` leaves behind**, and it is the one worth
  reading the PR comments for. Ten panel rounds; nine found something real, and six of
  those nine carried at least one HIGH — all of one class: the check disagreeing with a
  real shell about which file gets executed. Each is fixed and pinned. The residual is structural — the check
  judges any path-shaped word inside a hook command, so a path merely *mentioned* reads
  as invoked — and narrowing it to the shapes `init.sh` prints is a trade (it would lose
  the ability to judge a hand-written registration), which is why it is a ticket and not
  a fix round.
- **`#380` needs a host with a working `codex-cli`.** Nothing else unblocks it.
- **`#388` is the next adopter-facing gap**: cs-toolkit hand-maintains a manifest entry
  because of it, and re-running `--record-install` there silently undoes that.
- **`#358` remains untouched**, as it was last session.

### Later the same day — the July-cohort sweep

**94 issues re-derived against `main` at `40eef8b`, 17 closed (18%).** The sweep was run
because filing was outrunning closing about 5:1 and 94 issues were ≥8 days old in a repo
worked daily. Six read-only agents re-derived each premise with a command rather than
reading the issue text; every close carries that command in a comment.

- **Closed:** `#27` `#33` `#37` `#72` `#75` `#93` `#106` `#112` `#121` `#123` `#124`
  `#136` `#146` `#163` `#178` `#183` `#187`. `#72` is the instructive one — it was filed
  against behaviour that already shipped.
- **Routed as decisions, not defects:** `#4` (describes a service scaffold this repo does
  not have), `#167` (the split shipped; the rest is its own "what a repair needs to
  decide"), `#169` (draft-vs-ready default).
- **31 of the remaining 74 are labelled into five clusters** — `cluster:merge-gate` (3),
  `cluster:pre-push` (5), `cluster:suite-integrity` (7), `cluster:doctrine` (8),
  `cluster:review-signal` (9); `#36` carries two, so 32 assignments over 31 issues. Counted
  with `gh issue list --state open --label "cluster:<name>" --limit 300`, not estimated —
  a first draft of this line claimed all 74 and a lens counted it.
  **43 are deliberately unlabelled**: no evidence-backed cluster emerged for them during
  the sweep, and inventing one to reach a round number would make the labels worse than
  useless. So the labels are an index of what the sweep *found*, not of the backlog — a
  session picking a cluster gets a real work package; a session wanting the rest still has
  to read.

**The sweep's real finding is that the backlog is not stale.** An 18% close rate means the
pile is unworked rather than rotten, so triage is not the lever. Two pre-sweep claims were
wrong — **one projection and one truncated measurement**, and the distinction matters
because they fail differently. "Expect 40–50 closes" was a forecast drawn from a sample
chosen *because* it looked fixed. "Open issues: 30" was an observation, taken from a `gh`
call that silently hit its default limit; nothing about it was a guess, which is what made
it convincing.

**What the clusters say, ordered by what they threaten:**

- **`cluster:merge-gate` is the one that matters.** Three independent routes make
  `mergeable`/`converged` true when they should not: `#190` (losing or corrupting the
  state file disables the false-settle guard — and a *fresh clone* reaches that with no
  failed write), `#39` (the guard is one poll wide), `#95` (unanchored substring bot
  matching lets a PR forge a check that cancels its own reviewer's block). This is the
  kit's central promise, and cs-toolkit runs the engine.
- **`cluster:pre-push`** — five issues on one file, and `#36` was mutation-verified during
  the sweep: `exit 1` → `exit 0` and 1084 tests still pass. The kit's one mandatory
  protection is unpinned.
- **`cluster:suite-integrity`** — `#135` is quoted in `test_mutation_gate.py`'s own
  docstring as unresolved. While this cluster stands, every "fixed" verdict anywhere is
  softer than it reads.
- **`cluster:doctrine`** — `#141` and `#142` both build on `#56`, which was never
  implemented. Sequence `#56` first or they compound on nothing.

### Later still — Codex hooks settled, and the adopter's refresh merged

**`#380` is no longer blocked; it is ready to build.** The 0.42.0 that could not start a
session was a stale Homebrew *formula* shadowing the real CLI. On `codex-cli 0.147.0`, a
probe with both hooks registered in a throwaway repo's `.codex/hooks.json`:

- **A project-level `.codex/hooks.json` IS read.** That assumption had been carried
  unverified since Phase 0.
- **`SessionStart` fires with NO `matcher` key** — matching the shipping third-party
  registration and contradicting what the convergence plan assumed from documentation.
  Carrying Claude's matcher shape over would ship a hook that silently never fires.
- **`PostToolUse` with `matcher: "^Bash$"` fires, dispatched by Codex.** First time the
  kit's own Codex shape has been observed firing *by the runtime* rather than verified by
  running its command string through a shell — the caveat the Phase 3 memo left open.
- **The gate is hook TRUST, not support.** An untrusted hook is skipped silently; the first
  probe run looked like "not read" for that reason alone. `init.sh` already names the
  `/hooks` trust step, and that advisory should say a skipped hook is indistinguishable
  from a broken one.

Evidence is on `#380`. **One caution for whoever builds it:** the shape was proven with
`--dangerously-bypass-hook-trust`, a diagnostic no adopter will use. Acceptance must be
"fires in a *trusted* session", or it verifies a condition nobody reproduces.

**cs-toolkit's refresh merged** (`in-parallel-oy/cs-toolkit#1887`) — all four STALE files
taken, the `#385` hold retired, the 20 declines unchanged, and `#46`/Phase 2B still
deliberately declined. It sent two things back:

- **`#397`, new** — `init.sh` runs under `set -eu`, and the `--no-clobber` summary's loop
  can exit non-zero on its last iteration, aborting the script after listing the files that
  need action and before the four lines explaining the action. **Found by CodeRabbit
  reviewing the adopter's PR** — the "an adopter's review bot audits the kit" mechanism the
  Phase 3 memo named, firing a second time.
- **A correction to `#388`'s repro** — re-run against `40eef8b` it now exits **1**, where
  this repo recorded 0, and it **writes the downgraded manifest before failing**. The defect
  is unchanged; the stale exit code is the kind of detail that turns a workaround into false
  confidence. Their rule is the better one: when a tool's failure mode is "writes the wrong
  artifact", assert the artifact — exit codes are advisory.
- **`#398`, new** — `upgrade.md` Step 2 copies `docs/templates/*.tmpl` unconditionally. In a
  repo where those six are *declined*, that silently converts six deliberate decisions into
  installs, and `--record-install` then makes it permanent: 20 declines become 14, with
  nothing recording that anything was reversed. They spotted it before acting and declined
  the instruction.
- **`#399`, new, and it is a pattern not an incident** — a persisted `cd` sent writes into a
  verification clone. It happened **twice on 2026-08-09**, in two repos, to two sessions:
  theirs put `cp` and `./init.sh` in the clone (presenting as filesystem corruption — one
  inode for two paths, ten minutes lost to suspecting a sandbox overlay); this repo's
  session ran kit greps inside cs-toolkit and briefly "found" `CS_TOOLKIT_SESSIONS_DIR` in
  the kit's `dev_session.sh`. The panel contract has this rule for lenses; **no workflow has
  it**, and `upgrade.md` sends the operator to a second tree and then speaks in relative
  paths.

**And their sixth learning was about this session's own prompt.** Source: that session's
memo, delivered as a rendered artifact rather than committed anywhere — see the provenance
note below, which is the more useful half. It reports that the prompt's opening precondition
("on branch `codex/support-docs-launch-refresh` with uncommitted work") was false at run
time: the repo was on a clean `main`, and the branch held seven *committed* commits with no
worktree.

Both checkable halves hold, and here are the commands. The branch is seven commits ahead —
`git rev-list --count origin/main..origin/codex/support-docs-launch-refresh` → `7`. And the
precondition was true when written: the session that wrote the prompt measured
`git status --porcelain | wc -l` → `9` on that branch, minutes before. So nobody was wrong;
the state moved between the measurement and the reading. That is the point: **a precondition
in a brief is an observation with a timestamp**, the Phase 3 memo's rule about shas
generalised — and it bites hardest when the false precondition authorises a *protective*
manoeuvre, because the protection is what gets applied to a state that no longer exists.

**`#380` and `#397` are the same file**, which makes them one session — and `init.sh` work
is disjoint from `cluster:merge-gate`'s `pr_watch.py`, so the two can run in parallel lanes.

▶ Next: **`cluster:merge-gate`** — `#190` and `#39` together (one guard, one change), then
`#95` separately — **and `#380`+`#397` as a parallel lane, since `init.sh` and
`pr_watch.py` do not touch.** Superseding the pointer below: `#388` has no *current* consumer now that
cs-toolkit has unpinned `init.sh` — it remains the named **future** one, and will hit this
the next time it pins a file — while `#363` waits behind a gate that can currently be
defeated three ways.

______________________________________________________________________

▶ Superseded by the sweep above, kept for the reasoning: **`#388`, then `#363`.** `#388` has a named consumer — cs-toolkit will hit it the
next time it pins a file, and re-running `--record-install` there silently undoes the
hand-maintained entry it keeps because of this — and its shape is decided: a third state
beside `files` and `not_installed`, plus a refusal that does not take the declared scope
with it. `#363` is the Claude registration hardening the adopter carried rather than
forking, and `#389` has now shipped the instrument that would report it dead.

## Session — 2026-08-08 (the tenth triage sweep, and what re-derivation changed)

**Theme —** The friction inbox graduated to the tracker. The sweep's value was in the
routing rather than the volume: reading the tracker before drafting changed two of the
seven entries' destinations, in opposite directions.

- **PR `#375` merged (`453900e`).** The inbox is swept into
  `docs/kit-friction-log-archive.md` under `Graduated 2026-08-08`; the active file keeps
  its H1, intro and the new marker. Run in LLM-only mode — `#6`'s engine is still not
  vendored, so the parse, draft, sweep and PR were done against the workflow prose by hand.
- **Filed this session: `#370`, `#371`, `#372`, `#373`, `#374`, `#376`.** Occurrence
  comments on `#305` and `#115`. The cockpit mutation-harness entry needed no write —
  `#326` already carried both the occurrence and its "do not mutate the live tree" reframe.
- **The approval binds to what the operator saw.** Session A stored the drafted proposals;
  Session B replayed those against the DM reply rather than re-deriving them. Every write
  was re-read from the tracker after landing per `#138`, compared **by body**, with both
  commented issues confirmed still open.
- **The archived text round-trips byte-exact against the draft-time snapshot**, and that
  snapshot still matched the live inbox at finalize — checked in
  `/Users/topi/Coding/agentic-dev-kit` before the commit, so no entry was swept unfiled and
  nothing was added in the draft window.

**Learned**

- **An entry can read as already handled and not be, and grep is what gets it wrong.** The
  `panel_prompt.py` entry said the panel doctrine never names the engine. `git grep
  panel_prompt` now hits `fallback-review-panel.md`, so a grep-level check would have
  archived it as done. That hit is inside a `lens_compute` config aside; "Running it" step 2
  still tells you to hand-author every lens prompt. The claim's *wording* went stale while
  its substance stood — the opposite direction from a claim that is simply false, and only
  re-derivation separates them. `#373`.
- **The bot was available, and reproduced two of its own tickets while being so.** After
  four sessions of quota outages CodeRabbit reviewed this head clean, so no panel was
  warranted — treating a successful review as an outage is the inverse of Principle #5's
  error. Its clean verdict arrived as a comment rather than a review, leaving `coverage`
  empty (`#44`), and `mergeable` then demanded a receipt that no configured literal honestly
  describes (`#350`). Recorded `coderabbit`, per this repo's own receipt history, rather than
  asserting a `fallback:` pass that never ran.
- **Four entries were one story and did not want one ticket.** The quota cluster split by
  what each part actually routes to: the missing observability (`#370`), a false claim in
  `config/dev-model.yaml` about the panel being "the real substitute" (`#371`), and the
  operator decision itself (`#372`) — which four entries had deliberately declined to file,
  and which needed a home once its evidence moved to the archive.
- **A workflow that DMs through the operator's own token cannot tell its own messages from
  theirs.** Every message in the thread carried the operator's user id, including the
  skill's "still waiting" reminder — whose text contains a bare `skip`, which the skill's
  own grammar defines as bulk-cancel. An engine implementing that grammar literally would
  read its own reminder as the operator aborting the batch, and say so with a success
  message. `#376`.

**Open, and owned by nothing yet**

- **`#358` is the remaining pre-Phase-3 item** — untouched by this session.
- **The friction inbox holds no un-graduated entries**; this session's own finding was
  issue-shaped and went to the tracker as `#376` rather than to the inbox.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#376`, `#374`, `#373`, `#372`, `#371`, `#370`, `#368`, `#367`,
  `#365`, `#364`, `#363`, `#358`, `#356`, `#350`, `#346`, `#304`, `#291`, `#290`, `#287`,
  `#283`, `#273`, `#243`, `#248`, `#264`, `#236`, `#231`, `#213`, `#209`, `#211`, `#120`,
  `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`, `#46`, `#36`.

▶ Next: **`#358`, then Phase 3 in cs-toolkit** — unchanged by this session; the block below
carries the detail, including what that session must do beyond the upgrade.

## Session — 2026-08-08 (the adopter's memo, checked rather than executed)

**Theme —** cs-toolkit's Phase 0 handed the kit a memo of findings. Two of its
load-bearing claims did not survive being re-derived, and the work that followed was
smaller and better aimed than the memo proposed.

- **PR `#361` merged.** Facts in `docs/kit-convergence-plan.md` and this file that a
  reader would have acted on: Phase 3 no longer waits on cs-toolkit; "the only divergence
  currently invisible to tooling" was false, `init.sh` being the counterexample; and
  `adopt`/`upgrade` already have shared definitions with bindings on both runtimes since
  `#330`. The adopter memo is committed beside the plan as
  `docs/adopter-forcing-function-memo_2026-08-07.md`, preserved as the adopter's account
  with its superseded recommendation marked rather than rewritten.
- **PR `#362` merged — `#360` closed.** `init.sh` is tracked in `KIT_OWNED` and the
  manifest, so the file that performs every install is inside the measurement. Verified
  with `make test` in `/Users/topi/Coding/agentic-dev-kit`, and end-to-end by running the
  new doctor with `--root` against `/Users/topi/Coding/in-parallel/cs-toolkit`.
- **PR `#366` merged — `#359` closed.** The Codex registration no longer runs `python3`
  against a path built from an empty string. Both surfaces changed together because
  `test_the_advisory_matches_the_registrations_it_describes` requires it.
- **Filed this session: `#363`, `#364`, `#365`, `#367`, `#368`.** Occurrence comment on
  `#350`; the measurement that refutes `#358`'s proposed remedy is a comment on `#358`.

**Learned**

- **The memo's two false claims failed in opposite directions, and both came from reading
  a document instead of the tree.** It reported the kit has no coverage of the hook
  registrations — it has two real tests, and the true gap is that they compare *text*,
  which is *why* `#359` shipped: when the command string itself is wrong, the advisory and
  the shipped file are wrong identically and every equality holds. And it recommended
  promoting `adopt`/`upgrade` extraction to a hard Phase 3 gate, which `#330` had
  finished — taken from this repo's own stale plan section. **A stale plan does not merely
  misinform; it produces confidently-scoped work that does not need doing.**
- **`#360`'s design question dissolved instead of being decided.** Its three-way choice
  rested on an adopter's `init.sh` being *expected* to diverge. cs-toolkit's copy is
  byte-identical to kit commit `7485512b`, so the delta is version drift with no local
  rendering — which makes a tracked copy report `stale`, not `locally-edited`. No new role,
  no file split.
- **`KIT_OWNED` lives in the engine, not the manifest**, so `--manifest` cannot backport a
  newly tracked path. Found by running the adopter's *own* vendored doctor first and
  getting a different file list than the kit's.
- **Every panel round found the previous round's fix weaker than it claimed** — a regex
  guard defeated by execution, a parametrization that exercised a flag without reaching its
  branch, a positive control that did not discriminate its own path, a stub whose harness
  could break silently, and an assertion that could never fail. The doctrine predicts this
  about fix rounds; it held every round.
- **A mutation harness can report kills that never happened.** Cloning a branch before
  committing the fix meant the revert step restored the *unfixed* file, so two reported
  kills were that state failing again — and they were hiding two genuine coverage gaps.
  `#367`.
- **A stale PR *description* is worse than a stale comment**, because a reviewer reads it
  top-down before the diff. `#366`'s body asserted a rationale the code had already
  retracted.
- **One finding was beyond anything this machine could run:** the `exec` control in a new
  test was shell-dependent, and `/bin/dash` — `/bin/sh` on most Linux runners — tail-call
  optimises where the local shell forks. It would have failed there and passed here.

**Open, and owned by nothing yet**

- **`#358` is the remaining pre-Phase-3 item** — two prose paths plus a coverage question
  whose proposed remedy is refuted on the ticket, with the viable narrower form identified.
- ~~**The friction inbox still awaits `triage-friction-log`**~~ — **swept 2026-08-08**, see
  the block above; nothing was added to it this session, because everything issue-shaped
  was filed to the tracker instead.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#368`, `#367`, `#365`, `#364`, `#363`, `#358`, `#356`, `#350`,
  `#346`, `#304`, `#291`, `#290`, `#287`, `#283`, `#273`, `#243`, `#248`, `#264`, `#236`,
  `#231`, `#213`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`,
  `#169`, `#143`, `#46`, `#36`.

▶ Next: **`#358`, then Phase 3 in cs-toolkit.** `#358` is two lines in
`fallback-review-panel.md` plus the doctrine-scoped guard its comment thread already
measures. Then Phase 3, from a session rooted in `/Users/topi/Coding/in-parallel/cs-toolkit`
— read `docs/kit-convergence-plan.md`'s pre-Phase-3 section first. What that session
must do beyond the upgrade: install `docs/agentic-dev-kit/workflows/adopt.md` and
`upgrade.md` there (its manifest lists both as declined, so it has no installed workflow
doc to follow), and refresh its vendored `kit_doctor.py` — until that is replaced, its own
doctor cannot see `init.sh` however current the manifest is.

## Session — 2026-08-07 (`#353`, and a boundary its author could not settle)

**Theme —** A two-paragraph doc correction whose own review ran four rounds, found two
defects the branch had introduced, and ended on a classification the author was
disqualified from deciding.

- **PR `#353` merged (`63dd892`).** `docs/kit-convergence-plan.md` corrected on two
  facts a cs-toolkit session would have acted on: that repo registers the hook
  `$CLAUDE_PROJECT_DIR`-relative, not by absolute path as the plan said, and the hook's
  import closure is one module already vendored there byte-identical, so Phase 0 carries
  one file rather than a file plus dependencies. Verified with `make test` in
  `/Users/topi/Coding/agentic-dev-kit`, re-run at each committed head.
- **Its review found two regressions this branch introduced, and fixed both.** Round 1
  (full panel): the corrected measurement left the Agreed-sequence bullet contradicting
  it. Round 2 (full panel): the `Verified state` header's date range no longer covered a
  paragraph the branch had inserted under it.
- **A lens disputed the author's safety-critical draw; the operator upheld it.** Round 3
  was a single-lens record-prose delta pass, which confirmed the prose class and disputed
  the boundary. The operator's resolution is on the PR — required to be theirs, not a
  relayed account. Round 4 ran the dual form's second lens; both lenses confirmed both
  draws. Receipt `fallback:delta`, both lenses, bound to `2475dbd` — the head that
  merged, which the squash then rewrote.
- **CodeRabbit was rate-limited on both surfaces throughout and its coverage stayed
  empty**, so the panel carried this review end to end.
- **Filed this session: `#356`.** Occurrence comments on `#346` and `#120`.
- **`#352`, `#354` and `#355` landed on `main` during this session from elsewhere** —
  not this session's work; recorded so the trail has it.

**Learned**

- **The dual form leaks its own independence, through artifacts the doctrine mandates.**
  The second delta lens read the first's verdicts by running `gh pr view` to check
  whether the operator resolution artifact existed — an artifact the doctrine requires,
  on the surface the doctrine requires the verdicts to be posted to. It disclosed this
  unprompted, and nothing else would have caught it: the exposure leaves no trace in git,
  the receipt, or `pr_watch` state. So that receipt's draw-2 disjointness is self-attested
  rather than structural, which is said on the PR. `#356`.
- **One passage, four consecutive fix rounds, each introducing a fresh defect into the
  text it was repairing** — `45d7b05` → `a7ec719` → `9fed796` → `e623196`. The first two
  are pre-squash commits from the branch that landed as `274eed9`: real, reachable in the
  object DB, not ancestors of `main`. `#305`'s argument with better evidence than `#305`
  carries.
- **A planning document reached the safety-critical class by argument, never by
  binding.** The path list names four engines; it names neither this document nor the
  hook whose relocation the document instructs — and that hook cites the doctrine in its
  own docstring. `#346`.

**Open, and owned by nothing yet**

- **The critical path is unchanged and still leaves this repo**: Phase 3 needs
  cs-toolkit's Phase 0 and its fixer predicate. Both re-verified live this session — the
  fork is still 66 lines at `scripts/hooks/`, `.codex/hooks.json` is still absent, and
  that repo's `pr-watch.md` still reads `done`.
- **The friction inbox is over budget and its triage is overdue**; this session added a
  fourth consecutive occurrence to its bot-quota entry, which is the decision the sweep
  is waiting on.
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#356`, `#350`, `#346`, `#304`, `#291`, `#243`, `#273`, `#290`,
  `#283`, `#287`, `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`,
  `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: ~~**cs-toolkit's Phase 0**~~ — **done 2026-08-07**, merged there as `2ab63d255`.
The block above is left as written: it is an accurate record of what was true that day,
and its "still leaves this repo" reading was correct until Phase 0 merged that evening.
The live next step is in the 2026-08-08 trail at the top of this file — the three kit
items Phase 0 surfaced (`#360`+`#304`, `#359`, `#358`), then Phase 3.

## Session — 2026-08-07 (`#305`, and a vice removed at the pricing side)

**Theme —** The review sprint resumed where `#209`'s decision left it. The panel's
stopping rule was the picked hard item; the operator steered the design live and chose
its shape; the change merged the same session.

- **PR `#349` merged (`0e343c9`).** A record-prose-only fix-round delta on a change under
  `safety-critical-changes.md` now takes **both** configured lenses over the delta — the
  dual form — instead of a full panel at the new head, with rule 2 kept by composition
  and a stated precondition: a full-panel review must be standing, so a Degraded-mode
  initial review leaves nothing to compose with. The loop's three terminal states are
  named, and a deletion's prose class is set by what the deleted text was doing where it
  stood. The evidence companion buries the old categorical rule with the `#328` pricing,
  the rejected severity-floor alternative, and the deferred dual-everywhere question.
  Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`: 1006 passed, at both
  heads.
- **`#337` and `#334` merged before this session opened** (`fddbd31`, `b28df6b`), with no
  session block of their own; recorded here so the trail has it. On `#349` the scoped
  trigger produced one PR run and one `main` run, both green.
- **CodeRabbit reviewed both heads of `#349`** and went rate-limited only after coverage
  stood, so no panel was owed. Every finding is disposed on the PR's threads; the one not
  fixed is deferred to `#194` with the bot's agreement. Another data point for the
  friction inbox's bot-quota decision, still waiting on `triage-friction-log`.
- **Filed this session: `#350`.** Comments on `#305` (the disposition) and `#194` (the
  dual form sharpens its receipt-field ask).

**Learned**

- **The bot found the design's own missing precondition.** The dual form's composition
  argument silently assumed a full-panel initial review; the author had reviewed the
  argument and missed it. Principle #5 earning its keep on the doctrine that implements
  it.
- **Fix the price, not the duty.** The durable resolution of `#305`'s vice left
  never-log-regressions untouched and moved what acting on it costs. The rejected
  alternative — a severity floor on the duty — is in the companion so it is not
  re-proposed.
- **`mergeable` has no honest receipt for a bot-reviewed head** — all three literals
  describe fallback passes, so the loop's best case (bot quota present, full coverage)
  wedges the autonomous merge path. `#350`.

**Decided this session (operator, live)**

- **The dual-lens form**, over a severity floor and over record-only; **the ordinary
  class stays single-lens**, with `#268`'s disjointness evidence recorded on `#305` as
  the open question.
- **Merge `#349`** — operator-merge per the doctrine's own closing rule applied to
  itself.

**Open, and owned by nothing yet**

- **The critical path leaves this repo**: Phase 3 needs cs-toolkit's Phase 0 and its
  fixer predicate (`done` → `converged`), both that repo's PRs, per
  `docs/kit-convergence-plan.md`. Every kit-side gate is merged.
- **The friction inbox is over budget and its triage is overdue** by its own entries;
  graduating it needs tracker writes and operator approval (`triage-friction-log`).
- **Kit-side review-sprint continuation, in `#209`'s decided order: `#211`, then `#120`.**
- **Carried forward:** `#350`, `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **cs-toolkit's Phase 0 + fixer predicate** — that repo's PRs, per
`docs/kit-convergence-plan.md`'s agreed sequence; read its "The move is not a file move"
paragraph before starting. Kit-side in parallel: `#211` (populate `--carry-forward` for
fix rounds — the review sprint's named next move), and the overdue `triage-friction-log`
sweep.

## Session — 2026-08-06 (`#330`, and a ticket's own objection that did not survive being run)

**Theme —** The fix was one flag. The work was establishing that the flag was the right one,
against a ticket that argued it was not — and then discovering that moving a file with no
content change still regresses it.

- **PR `#337` is open, reviewed, and deliberately unmerged.** `/upgrade` Step 2 now runs
  `./init.sh --no-clobber`, so a marked-but-edited file is declined instead of rendered over
  with no backup. Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`, on that
  PR's branch — the figure is not restated here, and the branch has to be named because this
  record sits on a different one where the same command in the same directory prints a
  different number.
- **`adopt` and `upgrade` are now shared workflow definitions**, with thin bindings per runtime
  and `KIT_OWNED` entries; Codex gains `$adopt` and `$upgrade`, which it had not had. The move
  was required — `#330`'s fix lands in `upgrade.md` and would otherwise have reached one
  runtime — but the reason worth keeping is separate: `upgrade.md` Step 4 tells an adopter to
  keep their own copy of a runtime *adapter*, so while these two were adapters, no kit fix to
  the adopt or upgrade procedure could reach anyone running it.
- **Filed this session:** `#338`, `#339`, `#340`, `#341`, `#342`, `#343`. Occurrence comments
  on `#326` and `#323`, and a correction on `#330` recording that its objection to the chosen
  option was measurably wrong.

**Learned**

- **A ticket's stated regression can be an artefact of conflating two states.** `#330` argued
  `--no-clobber` would stop a partially-adopted repo receiving `AGENTS.md`. Two `git init`
  sandboxes showed the flag narrows seeding to *absent* targets, and absent is exactly that
  case — it still seeds. The real cost is one row narrower and is announced twice per run.
  The three-option choice the ticket declined to make was decided by running it, not by
  re-reading it.
- **A byte-identical move still regresses.** `adopt.md`'s link to
  `adopting-into-a-linted-repo.md` was correct from `.claude/commands/` and dangling from
  `docs/agentic-dev-kit/workflows/`. Round 1 of the panel verified the move by diffing
  extracted bodies and could not have caught it: correctness depended on the file's depth, and
  the bytes are identical in both places. `#340` is the missing check; `#216` is why one was
  built and reverted before.
- **A hardcoded list in a test narrows coverage without failing.**
  `test_codex_skill_adapters_are_valid_and_share_workflows` iterates a tuple that was the
  complete set until this PR added two skills to it. An unnamed skill is unchecked, not red.
  `#341`. A lens then mutation-tested it in both directions to show the gap was real.
- **The bot's own findings were mostly older than the PR.** Four of its six were pre-existing
  in a file that had simply never been read by a reviewer — as a `.claude/commands/` adapter it
  sat outside every check the repo runs *and* outside what `/upgrade` refreshes. `#342`, `#343`.
  A single bot pass over a long document is a lower bound, not an audit.

**Decided this session (operator-absent, by doctrine)**

- **Option 1 of `#330`'s three**, with the pristine-skeleton cost stated in the workflow rather
  than buried, and option 3 filed as `#338` with the versioning problem that stops it being a
  byte-compare.
- **File rather than fix**, for every finding verified pre-existing. `safety-critical-changes.md`
  rule 3 is explicit that a fix round addresses what the review found, and this PR gates a
  destructive operation.
- **Do not self-merge.** That same doctrine's closing line makes changes it governs
  operator-merge, "even when green and clean". This is why `#337` is held; the outage is a
  second, independent reason.

**Open, and owned by nothing yet**

- **`#337` and `#334` both need an operator merge and neither has CI.** Both branches have zero
  workflow runs. **They are not queued — the push events were dropped**, so Actions recovering
  will not create them: the incident open since 15:22Z later throttled webhooks to a fraction of
  deliveries, and runs on other branches completed well into that window, which is what makes
  "still queued" the wrong read. `#345` has the measurement and the recovery route, and the
  route matters: a new commit would re-trigger CI and **invalidate the review receipt bound to
  the reviewed sha**, while closing and reopening the PR re-fires `pull_request` without moving
  the head. The panel substituted for what CI would confirm — each lens ran the suite in its own
  isolated clone — which is evidence, not a green tick.
- **The friction inbox is over its budget** and this session widened it. Not swept here;
  graduating it needs tracker writes and operator approval, which is `triage-friction-log`'s job.
- **`#342` is the largest of the new ones**: three Major correctness gaps in `adopt.md`, now
  reachable and refreshable for the first time.
- **Carried forward:** `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`, `#292`, `#248`,
  `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`,
  `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **merge `#337`, then `#334`, once Actions is back** — both are operator calls, `#337`
by the safety doctrine rather than only by the outage. Read `#337`'s round-3 comment first: it
records what the panel substituted for CI and what the receipt does *not* cover. After that the
substance is unchanged from last session — **cs-toolkit's Phase 0 and its fixer predicate**
gate Phase 3, and are that repo's PRs.

## Session — 2026-08-06 (`#297`, and a diagnosis corrected within the hour)

**Theme —** Phase 2 shipped after a two-lens panel. The rest of the session went to a CI
failure that looked like this repo's and was not — the correction is the part worth reading.

- **`#297` shipped in PR `#328`** (merged `dc38c48`). `_seedable` returns a tri-state, so
  `seed_doc` can tell ABSENT from MARKED and the mode is read at that **one call site** —
  never inside the predicate, which is the fork `#297` exists to prevent. An unknown
  argument now exits 2 rather than being skipped past. `/adopt` Step 3c hands the operator
  `./init.sh --no-clobber` instead of asking them to inspect six line-1s. Verified with
  `make test` in `/Users/topi/Coding/agentic-dev-kit`: 952 passed.
- **`#329` is in PR `#334`, open and deliberately unmerged.** CI's `push:` trigger is scoped
  to the protected branch; `scripts/tests/test_ci_workflow.py` pins that literal against
  `vcs.protected_branch`, which is the only thing that can — a workflow cannot read the
  config and GitHub forbids expressions in `on:`. Verified with `make test` in the same
  checkout: 955 passed. **Held** because it cannot be validated while Actions is down: its
  own evidence is "one run, not two", and it currently produces zero, which is
  indistinguishable from having broken PR CI entirely.
- **Filed this session:** `#329`, `#330`, `#331`, `#332`, `#333`, `#335`. Occurrence
  comments on `#243` and `#305`.

**Learned**

- **Ask whether the provider is up before diagnosing the repo.** `#329` was filed
  attributing 15-minute job starvation to this repo's duplicate CI runs; githubstatus.com
  read `Actions: major_outage`, against an incident opened 15:22Z that predates every
  starved run. What disproved the local claim was a run
  with **no sibling to compete with** — PR `#328`'s merge to `main` produced zero check runs
  under the old unscoped trigger. Corrected on the issue rather than by editing it, and the
  workflow gap that permitted it is `#335`.
- **Re-running during an outage is what created the second defect.** The re-run made a check
  row vanish from the rollup instead of turning green, wedging `pr_watch`'s monotone
  false-settle guard permanently (`#333`, measured over eight polls at an unchanged head).
- **A test that names a property can cover half of it.** The byte-identical `--no-clobber`
  test exercised one of `_seedable`'s two marker arms; mutating the other left it green, and
  the kill came from an unrelated test that happened to use the other literal. Found by
  mutation testing, not by review.
- **The panel reviewed what shipped; the bot reviewed the design.** CodeRabbit went rate
  limited after reviewing `4576f40`, so the fixes for its own three findings were never
  bot-reviewed. `#305`'s shape, hit twice in one PR.

**Decided this session (operator)**

- **Record rather than repair**, again on a comment defect: PR `#328` ships a duplicated
  comment paragraph in `init.sh`. Repairing it moves the head off the sha both lenses
  reviewed, and `safety-critical-changes.md` gives that class no delta-pass exit — so three
  lines of comment would have cost a full panel. Stated on the PR, recorded on `#305`.
- **Run the panel** rather than wait out the bot's rate limit.
- **Hold `#334`** rather than merge a CI-trigger change on a green that cannot be obtained.

**Open, and owned by nothing yet**

- **The critical path leaves this repo.** Phase 3 needs cs-toolkit's Phase 0 and its fixer
  predicate (`done` → `converged`); its `pr_watch.py` still carries `decide_done`, and
  `.codex/hooks.json` is absent there. Both are cs-toolkit PRs.
- **`#330` does not block Phase 3.** Measured this session: all six of cs-toolkit's seedable
  paths classify IN_USE under `init.sh`'s own `_seedable`, spliced from the script rather
  than reimplemented. Re-run that before Phase 3 executes rather than trusting the snapshot.
- **`#331`, `#332`, `#333`, `#335` are all `pr-watch` loop defects** found by using it. They
  tax every future PR, and Phase 3 is the largest one in the plan.
- **Carried forward:** `#304`, `#291`, `#243`, `#273`, `#290`, `#283`, `#287`, `#292`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`pr-watch 334` once GitHub Actions recovers** — the check is one `toolkit` run on
that PR rather than two, and a run on `main` after it merges; if zero runs still appear, the
change broke PR CI and `test_pull_request_remains_a_trigger` is the thing to read. That is a
gate, not the substance: the substance is **cs-toolkit's Phase 0 and its fixer predicate**,
which gate Phase 3 and are that repo's PRs, per `docs/kit-convergence-plan.md`.

## Session — 2026-08-06 (`#286`, and a review that kept finding the same shape)

**Theme —** One inline lane, steered live because `#286`'s three open questions were
operator decisions. All three were answered before code was written; none changed under
review.

- **`#286` shipped in PR `#322`.** `--record-install` records `not_installed`, so an
  absence resolves to `declined` / `removed` / `new-upstream` instead of one permanent
  count. Verified with `make test` in `/Users/topi/Coding/agentic-dev-kit`: 943 passed.
- **Phase 1's done-when is still open.** It asks that `kit_doctor` distinguish sized down
  from broken *in cs-toolkit*, which needs a `--record-install` run there — adopter-side,
  so it belongs to Phase 3 rather than to this PR. `#286` is closed; the phase is not.
- **Operator decisions:** the declared set lives in the baseline (derived, not
  hand-declared); a file the kit adds later gets its own state rather than defaulting
  either way; declaring is opt-in via the key's presence, so an older baseline keeps its
  existing report.
- **Filed this session:** `#323`, `#324`, `#325`, `#326`.

**Learned**

- **A verdict line is a claim, and it drifted three times from the same blind spot.** Three
  separate review rounds found a headline reading as an all-clear over something actionable
  below it — for `removed`, then `unknown-version`, then `differs`. Each fix addressed the
  case in hand and missed its sibling one line away. What ended it was routing all four
  branches through one shared caveat rather than a fourth careful edit.
- **The panel found what my own mutation testing could not.** Several findings were gaps in
  the tests I had just written: I mutated the branches I was thinking about, and those were
  the ones already covered. A lens picks its own targets, which is the property being paid
  for.
- **`#324` is the limit of what this axis can assert.** A path in neither map cannot be
  told from a damaged record, because the baseline is the trust root and carries no
  integrity check. PR `#322` hedges the wording and does not claim more.

**Decided this session (operator)**

- **Run the panel to convergence rather than to a round count.** Severity rose at round 3
  (a HIGH after two Medium-only rounds), and the stopping rule is blast radius, not rounds.
  Round 4 converged and the receipt was recorded then.

**Open, and owned by nothing yet**

- **`#297` is now the whole of the critical path's next step** — Phase 2, carrying `#304`.
- **`#325` and `#326` are about the panel itself**, and the panel is now the review path
  whenever the bot is limited, so they cost every PR rather than only this one.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#283`, `#287`, `#292`, `#248`,
  `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`,
  `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#297` — Phase 2 of the convergence plan**, and now the critical path's only
open step on the kit side. Its done-when is that something can run `init.sh` in an adopter
without the operator reasoning about which files it will overwrite; `#304` is adjacent and
may share parts of the change. The Codex `SessionStart` budget hooks and cs-toolkit's Phase
0 still run in parallel per `docs/kit-convergence-plan.md`.

## Session — 2026-08-06 (the first parallel batch, and a fix that should not be built)

**Theme —** Three isolated lanes off one cockpit. Two landed. The third produced a finding
instead of a commit, which is the outcome worth recording: the repair `#304` names for
itself would have made an adopter's `AGENTS.md` permanently re-seedable.

- **`#292` shipped in PR `#315`.** `make test` and `mutation-test` now run CI's lint and
  shell-syntax gates before pytest. `#292` stays open — nothing pins that the targets
  actually depend on the new gates, so a symmetric revert still passes; the residual is on
  the issue and in the Makefile.
- **`#285` shipped in PR `#317`.** `kit_doctor`'s Usage block writes `<engine-dir>`, with a
  test pinning the invariant across `KIT_OWNED`.
- **`#304` did not ship, deliberately.** Its "smallest fix" — `seed_doc` re-emitting
  `KIT_OWN_MARKER` — is unconditional, so in the adopter tree `#297`'s body describes it
  leaves the seeded file permanently seedable instead of protected after one overwrite. The
  trace is on `#304`; a pointer is on `#297`. Both safe variants need a kit-repo detector
  that does not exist.
- **Filed this session:** `#316`, `#318` (from the `#285` lane), `#319`, `#320`. Occurrence
  comments on `#305`, `#304`, `#297`.
- **Batch reconciled** with `scripts/reconcile_sessions.sh fix-292-make-test-parity
  fix-285-kit-doctor-paths fix-304-seed-marker`, run in
  `/Users/topi/Coding/agentic-dev-kit`: `launched 3, merged 2, parked 1`. The parked lane is
  `fix-304-seed-marker` (`EMPTY — 0 commits, never started`).

**Learned**

- **A ticket's own proposed repair can carry the defect class the ticket cites.** `#304` was
  written after `#294`, names `#294`'s lessons, and its named repair has `#294`'s shape. What
  caught it was tracing the repair into an adopter tree before writing code — not review, and
  not the ticket's own reasoning.
- **Building the mechanical guard is what finds the bug elsewhere.** The `#285` lane's
  regression test surfaced the same hardcoded-path shape in seven further kit-owned engines,
  filed as `#316`. The prediction being borne out is **`#285`'s own** — its body argues for a
  mechanical fix over a careful edit because "the pattern reproduces itself on contact" — and
  the test established that rather than the argument. (`#316` records the seven; it does not
  contain that phrase, and an earlier draft of this line implied it did.)
- **A contract in the prompt is still prose.** A lane given the `prompt_preamble` verbatim
  idle-stalled against its first two clauses; its sibling, given the identical bytes, did
  not. `#320`, with the direction: the cockpit already owns a check that classifies this.
- **A panel that finds something cannot leave two-lens coverage at head.** Both merged PRs
  carry a single-lens `fallback:delta` receipt, because fixing a finding moves the head off
  the reviewed sha. `#305`, reframed there from a stopping rule to a coverage question.

**Decided this session (operator)**

- **Hybrid lane launch.** `parallel-headless.md` forbids an env-incapable launcher for a
  state-writing lane, and no in-session mechanism here can replace a spawned process's
  environment. So the two standard lanes ran as sub-agents with the sandbox carried by the
  on-disk marker and the refuse-flag reduced to a prompt instruction; the high-stakes lane
  stayed attended, where `activate` sets it mechanically.
- **Fold `#304` into `#297` rather than ship the smaller repair.** The lane produces a
  finding, not a commit.

**Open, and owned by nothing yet**

- **`#297` now carries `#304`'s work** as well as its own, and is Phase 2 of the convergence
  plan's critical path.
- **Phase 1 is half done** — `#285` landed, `#286` remains, and its body leaves three
  questions open that want an operator rather than a spec.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#283`, `#287`, `#286`, `#292`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#286` — the remaining half of Phase 1.** Read its body first: it leaves three
things undecided (what happens when the kit adds a file, whether declaring is opt-in, and
where the declared set lives), so this wants live steering rather than a delegated spec.
`#297` — now carrying `#304` — is the Phase 2 follow-on, and the Codex `SessionStart` budget
hooks plus cs-toolkit's Phase 0 still run in parallel per `docs/kit-convergence-plan.md`.

## Session — 2026-08-06 (the planning session the convergence doc asked for)

**Theme —** Planning only; no engine, hook or workflow changed. The convergence plan's
questions are settled — 1, 2, 4 and 5 by operator decision, 3 by verification — and its
phase shape is now an agreed sequence. `docs/kit-convergence-plan.md` is the record:
the decisions with their evidence, the sequence with its done-whens, and the
re-verification notes all live there, not here.

- **Question 3 verified: Codex exposes `SessionStart`.** The sources and the remaining
  fire-it-and-see obligation are in the convergence doc's settled-questions list.
- **Re-derived live before deciding**, per the doc's own instruction: `kit_doctor
  --manifest` run in cs-toolkit, the forked hook measured against the kit's current one,
  `#285` / `#286` / `#297` re-read against the plan's claims. The claims held; the
  deltas are recorded in the doc's verified-state section.
- **One dependency the doc had missed is now in the sequence:** cs-toolkit's nightly
  fixer still reads `done`, which gates the engine swap — cs-toolkit's own config phased
  its adoption around exactly this, and the constraint had not reached the kit's plan.

**Open, and owned by nothing yet**

- **`#297` and `#304`** are now placed in the agreed sequence rather than free-floating;
  `#304` is the chosen kit-side starter.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#304`** — its body names the smaller repair (`seed_doc` re-emitting the
kit-own marker). The sequence's other immediate items — the Codex SessionStart budget
hooks (kit-side) and Phase 0, un-forking cs-toolkit's hook (a cs-toolkit session) —
run in parallel with it, per `docs/kit-convergence-plan.md`.

## Session — 2026-08-05 (the runtime hook, and two predicates deleted)

**Theme —** Both runtimes now fire the PR follow-through hook, and neither registration is
written by the kit. The work that took the time was not the wiring: it was discovering, on
one function, the shape `#297` was filed about, twice over — a predicate about
somebody else's filesystem or config, restated where nothing can execute the restatement.

- **`#301`** — settled in PR `#303`. `pr_followup_hook.py` takes `--runtime`; it had hardcoded
  `review.fallback_commands.claude` and `lens_compute.claude`, which are runtime-keyed with
  different values, so registering it on Codex unchanged would have told that session to run
  Claude's review command at Claude's model. `.codex/hooks.json` added, `.claude/settings.json`
  updated, `init.sh` **prints both registrations whenever the engine is present, and writes neither**.
- **`#302`** — settled in PR `#306`. The trigger matched its phrase anywhere in a command, so
  anything quoting it mandated a non-terminating watch loop for a PR that did not exist.
  `tool_response` is now the discriminator; the command only selects candidates.
- **Filed this session:** `#304`, `#305`, `#310` — written straight to the tracker; and
  `#308`, `#309` — routed out of the wrap-up inbox rather than left parked there.
  A further occurrence on `#270`.

**Learned**

- **Delete the predicate; a guard round finds the shape the last guard missed.** `init.sh`
  first *seeded* `.codex/hooks.json`, then merely *read* it to decide whether to print. Each
  was retired only after its guards had been beaten — the seed by a dangling symlink at the
  leaf, where `[ -e ]` is false and `cat >` follows the link out of the directory; the read
  by a substring that cannot distinguish a `PostToolUse` entry from a mention under any other
  event. The same shape, on `/adopt`, is what `#294` and `#297` are about.
- **Verifying the output and guessing the input is the same error wearing a coat.** `#306`
  established `gh`'s stdout/stderr formats from `gh`'s source, exactly as the ticket demanded
  — and then read that evidence out of a `tool_response` whose shape it had guessed. Codex's
  schema types that field as `true`: any value. A review lens found the resulting silent miss.
- **A negated closing keyword in a heading closes the issue listed under it.** `#303`'s squash
  message said `## Filed, not fixed` above a list naming `#302`; GitHub paired them across the
  blank line and list marker, and the same message said in prose that it stays open. Found by
  going to work on `#302` and finding it closed. The contract in `AGENTS.md` already covers
  this ("in any form, even negated") — what failed was the check, which looked for a keyword
  and a reference on one line.
- **The panel's own output is the next round's input.** Rounds repeatedly found defects in the
  tests written to close the previous round's findings. That is what a fix round is, and it is
  why `#305` exists.
- **`panel_prompt.py` rendered every lens prompt this session** — the friction entry proposing
  it is now validated by use rather than by argument, including `--carry-forward` for the
  round-to-round aim that had been hand-written prose.

**Decided this session (operator)**

- **Record rather than repair, below a severity floor.** Applied once where it cost something:
  `#306` ships a doubled word in a comment, because repairing it would move the head off the
  sha both lenses reviewed. Stated in the squash message rather than hidden. `#305` argues the
  general case and is deliberately not self-answered — a stopping rule authored mid-loop by
  the party who wants the loop to end has the worst possible provenance.

**Open, and owned by nothing yet**

- **`#297` is still the unbuilt half of `#105`** — it was this session's inherited starter
  and was displaced, not dropped.
- **The closing-keyword check that works is a scratchpad script, not something this repo
  runs** — `#308`, with the draft's evidence. It and `#309` came out of the inbox, because
  each already had a reproduction, a mechanism and a proposed repair. `#310` is the write-up
  of why they were parked at all, and was never an inbox entry itself.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **a planning session on `docs/kit-convergence-plan.md`.** The goal is cs-toolkit
using the kit rather than its own copy, and Codex as a first-class runtime rather than a
partially-wired one. That document records what was verified about both, what blocks, and
five questions it deliberately does not answer — the first two branch the whole plan. Read
it before proposing an order.

Ready to start immediately if that planning lands on it: **`#304` — `./init.sh` in this
repo overwrites its own `AGENTS.md`/`CLAUDE.md`**,
destroying the kit-own marker one-way and reporting it as `seeded`. Read its body: it
reproduces the defect, records that `make test` then fails on this checkout, and notes that
`README.md` documents re-running `init.sh` as the upgrade step. It also names the smaller of
two fixes — `seed_doc` re-emitting the marker — which needs none of the kit-repo detection
`#291` wants. `#297` remains the larger inherited item.

## Session — 2026-08-04 (the guard that could not live in a document)

**Theme —** `/adopt`'s contract is *"never overwrite an existing file"*; `init.sh`'s
`_seedable` deliberately renders over anything carrying a kit marker. Both are right, and
this session connected them. The mechanisms built to make that safe — a
backup-and-restore, a re-classify-and-diff, an advisory gate, a gate fused to the run —
**each shipped a new way to destroy an adopter's file**. The scope was cut instead.

- **`#105` — closed** (`1592380`, PR `#294`). `/adopt` stages the adoption and stops:
  `docs/templates/` and `init.sh` in the copy list, the pre-push hook reaching the repo at
  all, `config/*.local.yaml` gitignored before the PR opens, a stop when the adopter has
  their own `init.sh`, and a handoff giving the operator the six seedable paths from *their*
  config. A Codex adopter arriving via `/adopt` now gets an entry point.
- **`/adopt` never runs `init.sh`.** The document carries no authored shell; the remaining
  fenced blocks are single-line kit commands. That is the fix, not a limitation of it.
- **Filed:** `#295`, `#296`, `#297`, `#298`; a fourth occurrence on `#270`.

**Learned**

- **Every guard written into a workflow doc is untested code.** No test, linter or CI runs
  it — `make test` passes in full without touching a line. Each defect class found here
  (locale-dependent marker match, staleness, 2-of-6 coverage, an unscoped `grep` resolving a
  decoy path, a BSD-only `mktemp` building an empty-tree probe) was a predicate `init.sh`
  already owns, restated and diverging on an input nobody could test. The only repair that
  held was **deleting the restatement**. This is `#297`'s whole argument.
- **A fix round's own output is the likeliest place for the next defect.** Repeatedly a
  commit corrected one passage and left an adjacent one asserting the old thing — including
  one whose message reasoned explicitly about the fact it then failed to apply next door.
  The round-by-round record is on PR `#294`; it is not restated here.
- **The panel's isolation contract has a second hole, and it is not `cp -R`.** A lens ran
  `init.sh` against the live checkout because the tool's cwd resets to the repo root between
  calls and `init.sh` acts on the *current directory*. It rendered over this repo's own
  `AGENTS.md` and `CLAUDE.md` — seedable by design since `#288` — and touched
  `config/dev-model.yaml`. Restored, and verified in the cockpit checkout
  (`git status --short` clean, files byte-identical to `HEAD`, hook firing on a synthetic
  `dev/*` push built with plumbing). `#270`, with the direction: a cockpit-side
  before/after baseline, which was run for the last round and held.
- **Nothing checks the review brief itself.** A lens found a diffstat in its own prompt that
  I had never measured. Contract items govern what a lens reports, not whether what it was
  told is true.
- **I asserted verification I had not performed, more than once** — an end-to-end claim
  whose fixtures excluded the dangerous input, and a consistency claim across four steps
  from a diff that touched one. Both were caught by review, not by me. `#248`'s shape.

**Decided this session (operator)**

- **Ship the safe half; move the guarantee to `init.sh`.** After the fourth mechanism
  failed, scope was cut to the parts carrying no predicate at all. `#297` carries the
  no-clobber mode, where CI can hold it.
- **CodeRabbit's original suggestion was right and I talked us out of it.** It proposed a
  no-clobber mode on the first round; I declined it as forking the semantics `#288`
  unified. A mode flag on one predicate is not a fork — two implementations of that
  predicate is, and that is what I built instead.

**Open, and owned by nothing yet**

- **`#297` is the completion of this work**, not an optional follow-up: until it exists,
  `/adopt` cannot seed anything and the operator runs `init.sh` by hand.
- **Carried forward:** `#243`, `#273`, `#291`, `#290`, `#285`, `#283`, `#287`, `#286`,
  `#292`, `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`,
  `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#297` — add `--no-clobber` to `init.sh`**, with tests in `scripts/tests/`. Read
`#297`'s body first: it enumerates the nine findings that argue for it and records that a
mode flag on `_seedable` is not the fork I mistook it for. `/adopt` passes it always;
`init.sh` bare and `/upgrade` keep today's behaviour, where re-rendering a marker is
correct. `#273` direction 1 was this session's inherited starter and is still undone — it
was displaced deliberately, not dropped.

### 2026-08-04 (the kit's own entry points, and a claim class that outlived the code)

**Theme —** `seed_doc` had two categories, a shipped skeleton and a file the adopter is using,
and the kit's own entry points are a third. Both halves of `#288` followed: `CLAUDE.md` rode
the `cp -r` quickstart into every adopter with nothing rendering, removing or reporting it, so
their Claude sessions loaded *the kit's* contract; and `AGENTS.md` was reached by file
**absence**, so the kit could not ship one and a Codex session working in the kit had no entry
point at all. `#274`'s class, on the two files whose whole job is to be read in the reading
repo.

- **`#288` — the third category** (`af004b9`, PR `#289`). `KIT_OWN_MARKER` on the kit's own
  root `AGENTS.md` and `CLAUDE.md`; an adopter's `init.sh` renders over both; a file carrying
  neither marker is still never touched. `AGENTS.md` holds the contract, `CLAUDE.md` imports
  it with `@AGENTS.md`, so one file states it and both runtimes load it in full.
- **`kit_doctor` now checks both entry points**, through a predicate that must agree with
  `_seedable`. Locale was the hazard: `[[:space:]]` is locale-dependent, and the two sides
  matched different characters under any real locale.
- **Filed:** `#290`, `#291`, `#292`. **Occurrences:** `#211`, `#120`, `#248`, `#209`, `#274`,
  and `#270`.

**Learned**

- **Each repair to the seed guard introduced the next defect**, all in one predicate. The two
  that destroyed a real file with no backup were both found by *running* `init.sh` against a
  hand-built fixture, never by reading it. `#211`'s thesis; the enumeration is on `#211`.
- **"What checks this new check" was answered wrong three times running** — a guard clause
  added to prevent silent overwrites was itself unpinned; the check added to catch an
  incomplete adoption was itself unchecked; the test added to pin a locale fix was itself
  locale-dependent and would have passed with the fix removed. Each found by mutation, none by
  reading. On `#211`.
- **The claims that survived review longest were the ones whose *form* looked rigorous** — a
  stated `grep` method whose scope was one file while the stale site sat in another, and a
  comment citing "the C locale" in a script that pinned no locale. A cited mechanism reads as
  verification and is not. Enumerated on `#248` as a sub-shape it did not name.
- **The code converged before the prose did, and the gap was most of the review.** The
  destructive findings stopped early; the rounds after them returned record and coverage
  findings almost exclusively. Evidence for `#120` over `#211` — on `#120`.
- **A lens wrote into the live checkout through the isolation route the doctrine prescribes.**
  `cp -R` of a *linked worktree* copies its `gitdir:` pointer, so the copy is not independent
  and `init.sh` in it rewrote the real repo's `.git/hooks/`. Invisible to the contract's own
  attestation, which reports on the handed tree. `#270`.
- **The local gate is weaker than CI.** An apostrophe in an `awk` comment closed the
  single-quoted program; `make test` reported a mass of unrelated pytest failures while CI's
  `sh -n init.sh` names the line. `#292`.

**Decided this session (operator)**

- **Codex as an equal-enough development environment, as soon as possible.** This is a
  standing goal and it lives on no ticket. It moved `#243` back off the backlog — but
  **sliced**: `adopt` + `upgrade` first, since the daily loop already works on Codex and the
  four missing workflows are lifecycle and maintenance.
- **Merged without a dual-lens pass at the merging head.** The last panel ran three commits
  earlier; no receipt was recorded, because one would have claimed coverage that does not
  exist and the engine refuses it once the head moves. The merge gate was the operator's
  decision plus green CI plus a bot review of the parent — stated on `#289` rather than left
  to be inferred from a missing receipt.

**Open, and owned by nothing yet**

- **`#290` and `#291` are one complaint** — a single boolean cannot carry what `kit_doctor`'s
  narrative check now sees, so a directory named `AGENTS.md` reports `in use` and the kit's
  own repo warns about its own entry points forever.
- **Carried forward:** `#243`, `#273`, `#105`, `#285`, `#283`, `#287`, `#286`, `#248`, `#264`,
  `#236`, `#231`, `#213`, `#167`, `#209`, `#211`, `#120`, `#216`, `#220`, `#203`, `#190`,
  `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#273` direction 1** — one note on `safety-critical-changes.md` line 10 saying
`.claude/rules/` binds Claude only. It is the smallest step toward the Codex goal above and the
only one whose failure is *silent*: cs-toolkit follows that sentence today and its safety
doctrine reaches one of its two runtimes, so a Codex session touching a kill-path there is
unbound and nothing reports it. Then `#105` (a Codex adopter arriving via `/adopt` still gets
no entry point — this session fixed only the `init.sh` path). Read `#243`'s own scope note
before starting it: its line count is measured, stale, and growing.

### 2026-08-03 (the aim lever, and the bug the later rounds did not catch)

**Theme —** `#51`'s local half shipped, and the durable result is not the feature. What cost
more to learn than the code did is about *review*: an adopter upgrade found a defect that the
PR's later review rounds did not catch — and the cheapest explanation fails, because the round
pointed directly at the guards it lived in missed it too.

- **`#278` — `kit_commit` in the manifest, and `differs` split three ways** (`a042c82`).
  `STALE` / `LOCALLY EDITED` / `STALE and EDITED`, stated as fact rather than inferred from
  `kit.version`, which tracks the config schema and so never moved when kit files did.
- **`#280` — the fix that reopened the hole** (`d3faafb`). `#278`'s round-3 change replaced
  `.get("files") or {}` with an isinstance check and dropped the `None` handling; `None` is
  the sentinel for "no `--from-kit`", so verification silently switched off. Found by
  cs-toolkit's reviewer one commit after `#278` merged.
- **cs-toolkit upgraded** to the fixed kit, which was the first real use of `--record-install`
  and is where `#283` was found.

**Learned**

- **The design premise was wrong, and only measuring the adopter showed it.** `#51`'s comment
  said the local column "is already computed today". It is computed; the baseline it computes
  against was never written by any install path, so it had drifted nineteen days from the
  files beside it. Shipping the field alone would have relocated the false accusation rather
  than removing it.
- **Carry-forward can subtract attention — but it is not the whole story here.** No total is
  given, because every total I gave this was wrong and the enumeration is what holds. From the
  archived launch briefs: the bug entered in the fix for **round 3** (`accf8fa`), which round 4
  then reviewed; **round 4's brief aimed at those guards** ("whether each actually guards what
  it claims") and missed it;
  **rounds 5 and 6 named "the three isinstance degrade sites" as already covered**; **round 7
  reviewed a prose-only delta under a blanket "everything else is already covered"**. So a
  wrong coverage claim removed most of the chances and something else removed the one that was
  aimed. Recorded on `#211`, which the `#209` decision below recommends: a carry-forward
  asserting coverage should have to name the test or mutation that establishes it.

  **The briefs those figures come from are session scratch, not committed**, so a later reader
  cannot re-derive this from the repo. `#280`'s merged body and commit message state it
  differently again; treat this bullet as the account of record and that one as superseded.
- **Rounds 2 and 4 on `#278` returned disjoint lens sets**; the first convergence came at
  round 5. Direct evidence on the question `#209` turns on — recorded on `#278` itself, not on
  `#209`, which a review lens checked and found bare.
- **The configured bot reviewed a minority of heads while its check went green on all of
  them.** Its check surface carries no signal about whether a review happened — occurrence and
  the per-head table on `#45`.
- **A guard resting on an incidental property is not a guard.** `#278`'s first
  release-manifest check needed a `required_by` edge to fire, which is an accident of the
  current import graph. A lens called it fragile; cs-toolkit's real manifest then turned out
  to have none, so the original guard would have missed the live case.

**Decided this session (operator)**

- **`#209` — no proportionality valve.** None of directions 1–4 adopted, each refuted by a
  counter-example from a different PR; the issue body's recommendation of direction 1 is
  struck so a reader of the body cannot act on it. Next moves are `#211` then `#120`, both
  aimed at the finding *population* rather than the pass size.
- **Kit findings surfaced in an adopter route upstream, not into the adopter's PR.** A local
  edit to a kit-owned file reports `LOCALLY EDITED` on every later upgrade, which is the
  signal the baseline exists to give.

**Filed this session:** `#279`, `#281`, `#282`, `#283`; occurrences on `#45`, `#211`, `#270`.

**Open, and owned by nothing yet**

- **`#243` is still the precondition** for the `triage-friction-log` and
  `post-merge-systemize` conversions — the two that remain of the adapter work.
- **cs-toolkit's friction inbox is over budget with un-graduated dated sections.** Needs
  tracker writes plus operator approval, so it is `triage-friction-log`'s job and not a
  wrap-up's.
- **Carried forward:** `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#120`, `#216`, `#220`,
  `#203`, `#190`, `#187`, `#124`, `#169`, `#143`.

▶ Next: **`#283`** — one paragraph in `/upgrade` Step 4 saying a copied release manifest must
be removed before `--record-install`, and that the mode exits 1 on a partial record. It is the
smallest of the four filed today, it is on the path every pre-`#51` adopter takes on their
next upgrade, and the fix is prose in a file that is already `/upgrade`-refreshed. `#281` is
the next-largest and is a real guard defect, but it needs a test over the near-miss keys
rather than a wording change.

### 2026-08-03 (three conversions, and a defect class that only exists in shipped docs)

**Theme —** `/session-start` was already converted; this session did the rest. `/parallel` and
`/wrap-up` now point at shared workflows, `/wrap-up` on **both** runtimes. The durable result is
not the conversions: it is that every conversion produced a defect where prose was **correct in
the repo that wrote it and false in the repo that reads it** — and that installing kit docs into
a repo with a fresh reviewer is the cheapest oracle found so far for finding them.

- **cs-toolkit `#1830` — install the shared workflows** (`bfcb4104`). Nine docs; `docs/agentic-dev-kit/`
  had held one. Sessions there had no panel doctrine when the bot went down. Its
  `session-start.md` was **content**-stale, not byte-stale as the previous handoff recorded —
  two commits behind, so the repo where the silent tracker truncation was hit was running the
  session-start without the fix for it.
- **kit `#268` — two rules recovered from the `/parallel` fork** (`8e57562`), and **cs-toolkit
  `#1831`** (`2ee66143`) converting it, 200 lines to 64.
- **kit `#272` — the validation step** (`c7eb7ea`), and **cs-toolkit `#1832`** converting
  `/wrap-up` on both runtimes, 197 lines to 62, renaming the Codex slug.
- **kit `#276` and cs-toolkit `#1833`** — the validation step demonstrated its own gap in the
  commit that introduced it, and the repair. See below.
- **Filed:** `#269`, `#270`, `#271`, `#273`, `#274` (the defect class above), plus an occurrence
  and a correction on `#61` and the fourth measurement on `#209`.

**Learned**

- **The defect class.** Five instances: the hook-install claim (true of cs-toolkit's `make`
  target, false of `init.sh`); the advice that followed from it; "no record of it **in this
  repo**", which inverts in an adopter because there *this repo* is the one holding the record;
  a `docs/plan/handoff/` path that never existed; and an archiver substitution that renamed the
  script but not its `--target-lines` flag. Each was written correctly and read wrongly. `#248`
  did not describe this and nothing else did either; filed as `#274`.
- **Installing kit docs into an adopter is a review oracle.** CodeRabbit found 12 findings on
  `#1830` against files it had reviewed long ago upstream — including a hardcoded prefix in a
  file that documents three ways that prefix can differ.
- **The `/wrap-up` fork inverted the pattern.** The other conversions found kit bugs the fork
  was hiding; this fork was running a remedy the kit lacked, and had open as `#119`. Its
  validation step had no upstream equivalent — seven distinctive phrases, zero hits.
- **The panel found a false claim by executing it**, in a paragraph written while citing `#248`
  for that exact failure. Verifying the cheap sub-claims is not verifying the claim.
- **Seeing an untracked file is not a control; staging by name is.** The validation step added
  in `#272` was defeated on its first live use, in the same commit: `git add -A` swept 228 lines
  of an adopter's uncommitted design note into a wrap-up PR, through review and merge. The
  pre-commit check **did** list the file. It was read for intent — "pre-existing, not mine" —
  rather than as a staging hazard, which is why "surface untracked files" would not have helped
  and is the fix that was **not** shipped. `#276` bans wildcard adds in the workflow instead;
  cs-toolkit `#1833` reverted the sweep, content verified byte-identical three ways.
- **The panel's own contract has a write channel it forbids.** Two live incidents: a scratch
  clone whose `origin` pointed at the handed tree took a pushed ref, and a lens deleted this
  repo's installed `pre-push` after inferring from an untracked path that it had created it.
  Both invisible to `git status --short`, which the contract names as its attestation. `#270`.
- **`paths.engines` carries two meanings** and cannot be right in an adopter with divergent
  originals. The obvious fix is foreclosed: relocating kit engines puts them under a formatter
  that rewrites them. Attempted and reverted. `#269`.
- **The kit tells adopters to bind doctrine through `.claude/rules/`**, listed first among three
  "equivalent" options, and that one binds a single runtime. cs-toolkit has 427 lines behind it,
  including its 66-line safety doctrine, reaching one of its two runtimes. `#273`.

**Decided this session (operator)**

- **Kit-owned docs are exempt from an adopter's formatters.** cs-toolkit's hook would have
  rewritten 8 of 9 installed docs, making every one read as a local edit permanently, with no
  adopter-side way to re-stamp the baseline. The exemption was verified in both directions and
  has since held twice while the same commits reformatted adapter files beside them.
- **`#209` is a decision to take, not a build to schedule** — and after the conversions, which
  is what happened. The build edits the doctrine it reforms, which `#213` measured at five
  rounds.
- **Two kit PRs merged on operator sign-off without a third panel**, both after their bot went
  rate-limited mid-PR. Recorded on each PR rather than left to be inferred from a missing
  receipt.

**Open, and owned by nothing yet**

- **cs-toolkit's own wrap-up is in flight**, run through the newly converted `/wrap-up` so the
  conversion gets an end-to-end exercise rather than only a review. Two things it cannot do:
  its friction inbox is over budget with four un-graduated dated sections, and graduating them
  needs tracker writes plus operator approval (`triage-friction-log`, a separate pass); and its
  `chore/update-plan-<date>` convention already collided with an earlier PR the same day, which
  is `#256` reproduced a third time.
- **Carried forward:** `#243` (still the precondition for the `triage-friction-log` and
  `post-merge-systemize` conversions — those two are what remain of the adapter work), `#209`,
  `#248`, `#264`, `#236`, `#231`, `#213`, `#167`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`,
  `#124`, `#169`, `#143`, `#93` (its content-recovery half is now discharged; its compatibility
  half was retired by operator decision).

▶ Next: **take the `#209` decision.** It is the operator's, it is cheap, and its input will not
get better — four measurements now, and this session added the one that bears on the direction
the issue currently recommends. Direction 1 would have reduced round 2 of `#268` to a single
lens, and that round's two lenses returned **disjoint** finding sets, so whichever ran alone
would have missed the other's entire set including the MEDIUM. Read the two comments on `#209`
before proposing anything: `#120`, `#211` and `#209` share one evidence body and the issue says
to weigh them together, which now covers five asks. Start from "none of directions 1–4 is
ready" rather than from picking one.

### 2026-08-03 (the tracker gather, and a failure mode `#248` had not named)

**Theme —** The shipped rule never changed after round one. Across **every** review round on
`#260` and `#263`, each finding was in a claim written *about* the fix — and the dominant shape
was not a drifted restatement but an inference presented as an observation, which `#248` does
not currently describe. Both loops ended by **deleting** the claim that kept breaking rather
than repairing it again.

- **`#260` — `session-start`'s tracker gather gets a row limit** (`601a225`). Its PR bullet was
  hardened in `e49ddf3`; the tracker bullet three lines below carried nothing, because
  "field-limited" governs *which fields*, never *how many rows*. Field selection and the row
  limit are separate controls, and the returned count is now suspect against **two** ceilings —
  yours and the backend's.
- **`#262` — the same gather in `parallel plan`** (`fd9506f`), by pointer rather than copy. A
  truncation there does not shorten a briefing, it narrows the input to a set of isolated lanes,
  and nothing downstream recovers the tickets past the cut.
- **`#263` — prefer the backend's own has-more signal** (`56b42bf`). Row-count arithmetic is the
  fallback, not the method. Evidence the previous PR could not have had: Linear at its schema
  maximum answered `hasNextPage: true` — `#260`'s ceiling-equals-count case, reported outright
  instead of inferred.
- **`#258` — the handoff stops restating derived state** (`7546bdd`). The rule **replaced**
  `wrap-up.md`'s "The invariant, not the figure" rather than joining it: that bullet is what
  permitted the defect, since the stale line followed it exactly. This block is the rule's first
  use.
- **Filed:** `#264` (Jira's `nextPageToken` is an input, `endCursor` the output; the doc presents
  them as symmetric with Linear's `cursor`), `#261` (filed and closed here), and **`CUS-1119`**
  on cs-toolkit's own tracker. Occurrences on `#42`, `#44` (where a later comment retracts a fix
  an earlier one proposed), `#143`, `#179`, `#248`.

**Learned**

- **The rule was never the defect.** Every finding was in the surrounding evidence — an untested
  mechanism, a measurement that broke its own stated method, a citation to the wrong issue. What
  ended both loops was removal: the byte-comparison row that drew defects in consecutive rounds
  was cut rather than repaired again.
- **`#248` may be named too narrowly.** Its framing is a restated fact drifting from its owner.
  The dominant failure here was an **inference presented as an observation** — "ask for 500 and
  you get 100" when both cited clients reject; "one field set across all three" when the template
  rendered four of six. A restatement has a source to diff against; an untested assertion has
  none, which is why nothing catches it. Both instances were found by a lens that **called the
  tool** rather than read its schema. Enumerated on `#248`.
- **The operator asking "is that actually true?" was the cheapest intervention available**, and
  it fired on claims inherited from this repo's own archive — including "no MCP server is
  configured in this checkout", which was false and was the premise of a whole paragraph.
- **A rate-limited bot's stub carries the same commit-range marker as a real review.** On one PR
  that marker sat beside a genuine clean review; on the next, beside "we couldn't start this
  review". Zero review objects in both. The discriminator is the actionable-comments marker —
  which `review.noise_markers` deliberately discards. `#44`.

**Decided this session (operator)**

- **Both `wrap-up` runtimes harmonize in one pass.** Nothing relies on cs-toolkit's Codex
  `session-wrap-up` skill, so `#93`'s *compatibility* half is retired and the slug becomes a plain
  rename. Its *content-recovery* half stands: those forked lines may hold knowledge the shared doc
  lacks, so map before deleting.
- **The "Filed this session" list stays.** An event is not a tally — the enumeration is
  recoverable only by a dated tracker query; a count beside it is what recounts keep finding
  wrong. Written into `wrap-up.md`'s rule.

**cs-toolkit pre-flight — this changes the next step**

Established by comparing `kit-manifest.json` against the live checkout, not assumed:

- **`parallel.md` is not installed there**, so the standing "convert the `/parallel` adapter"
  had no target to point at. Most of the manifest is likewise absent, including
  `fallback-review-panel.md` and `safety-critical-changes.md` — sessions there have no panel
  doctrine when a bot goes down.
- **Its `session-start.md` is content-identical to kit `6bf4443` but byte-different** — a
  markdown formatter reflowed tables and re-wrapped paragraphs. `kit_doctor` compares bytes, so
  a formatter in an adopter makes kit-owned docs read as drifted permanently. Bears on `#51`.
- **`CUS-1119`** — its `list_dev_backlog.py` caps at 40, does not page, and applies the cap
  *before* filtering, against a Linear project whose size is on that ticket. The kit fix does not
  reach it.

**Open, and owned by nothing yet**

- **Carried forward:** `#243` (still the precondition for the `triage-friction-log` /
  `post-merge-systemize` conversions, not for `/parallel`), `#256`, `#248`, `#264`, `#236`,
  `#231`, `#213`, `#167`, `#209`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`,
  `#93`, `#143`.

▶ Next: **cs-toolkit — install the shared workflows first, then convert `/parallel` and
`/wrap-up` together.** Install at current `main`, not at whatever the repo last saw. Then
`/parallel` (a ~200-line fork with its shared doc now present) and `/wrap-up` on **both**
runtimes in one pass — `.claude/commands/wrap-up.md` and `.agents/skills/session-wrap-up/`,
renaming that slug to `wrap-up`. Use the method `in-parallel-oy/cs-toolkit#1826` proved: map
every section before deleting any, and contribute anything generic upstream first. Every
conversion so far has found a kit bug the fork was hiding.

### 2026-08-03 (the conversion proved itself, and the record kept outrunning the work)

**Theme —** Three kit PRs merged, one closed unmerged, one adopter converted. The durable
result is not any of them: it is that **a claim written about work already done was wrong in
every review round of one paragraph**, and the thing that finally held was replacing the claim
with an enumeration a grep can check. `#248`.

- **`#238` — `session-start` gains a Remediation check** (`b5b9547`). The kit shipped an
  archival mechanism and a briefing where the briefing never read what the archiver swept:
  `paths.handoff_history` and `paths.friction_log_archive` were consumed by nothing.
- **`#237` — the PR limit and its lost caveat** (`e49ddf3`). The shipped `--limit 20` was
  *below* `gh`'s own default. Both halves came from diffing the four shared workflows against
  the cs-toolkit adapters they were generalized out of; that survey found nothing else, and
  its result is recorded on the PR.
- **The fail-closed rule** (`6bf4443`). A source that fails now reports unavailable rather
  than its empty value. Found by CodeRabbit reviewing **cs-toolkit's copy**, not this repo's.
- **`#244` closed unmerged**, under a bound declared before its second lens reported. Its
  provenance rule was disproven on its own example — `git check-ref-format` accepts `$()` in a
  branch name, and `git branch --show-current` is in this workflow's own gather. `#245`.
- **cs-toolkit `/session-start` converted** to pointer + appendix. Every section of the fork
  was mapped before anything was deleted; the one with no home was contributed upstream as
  `#238` first. The conversion was **run**, not only mapped — the mapping and the run are on
  that PR.
- **Ninth friction-log sweep** (`#257`, `e2e8719`). Fifteen entries routed: seven into new
  issues (`#250`–`#256`), six into five occurrence comments (two entries shared one comment on
  `#205`), two already tagged `#198`. Twelve writes, fifteen entries — not the same number.
  CodeRabbit was rate-limited, so the merge stands on a `fallback:panel` receipt.

**Learned**

- **The record outran the work in every round, on one paragraph.** Four consecutive scope
  sentences each claimed more than was implemented, including one caught by its author's own
  grep before push. That is not four typos: an enumeration restating a list from six
  paragraphs above will drift from it. `#248` carries the rounds and three candidate
  directions.
- **Provenance is not a safety test.** "Who authored this string" says nothing about what
  characters it contains, and the shell only cares about the latter. `#245`.
- **A verification harness earned its place by being rewritten until it discriminated.** Twice
  a check returned the same result whichever branch was live and would have been reported as a
  pass; both were caught by asking what the *other* branch returns.
- **`gh` resolves the repo from the working directory, and a forge write is not retractable
  the way a file write is.** A comment landed on an unrelated merged PR in another repo that
  happened to share the number, and the write reported success. `#246`.
- **Half the kit is not thin** — four workflows exist only as Claude adapters with their
  doctrine inline and no Codex equivalent, so Codex can run half the kit by omission. This is
  what makes `#236`'s adapter half intractable and is now its precondition. `#243`.
- **The record outran the work again, in the session that named it.** Two more position claims
  were wrong — "four" sections where three was right, and a marker called first that is third —
  both inside sentences citing `#224` *for the position problem*. The second survived because
  the author repaired the visibly-broken clause and left the one needing a `grep`. Occurrence
  data on `#248`, and evidence for its "stop restating the structure" direction over the other
  two.

**Decided this session (operator)**

- **Branch patterns must uniquify within a day** — a second same-day run is the expected case,
  not the edge one. All three patterns are `{date}`-only; `state/triage/frozen-inbox_2026-07-29-b.json`
  is a hand-applied workaround from when triage hit it. Reproduced live today:
  `gh pr view chore/update-handoff-2026-08-03` answers `#249 MERGED`, this morning's wrap-up.
  Broadened onto `#256`; this session's own branch carries the `{date}-{time}` shape.
- **The handoff stops restating derived state.** `session-start` already gathers the friction
  log and grades its entries, so a budget line here is a second copy that can only go stale —
  it did, on `#257`'s merge, and it was the only misleading line in this block. Rule: the
  handoff carries what cannot be recomputed; if a command prints it, it belongs to the command.
  `#258`.

**Open, and owned by nothing yet**

- **Filed this session:** `#243`, `#245`, `#246`, `#248`, `#250`–`#256`, `#258`, plus `#240`
  and `#241` (the three withdrawn search recipes and the constraints any fourth must meet).
- **Carried forward:** `#236` (now narrowed to engines/doctrine plus Step 5), `#231`, `#213`,
  `#167`, `#209`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`, `#124`, `#169`, `#93`.

▶ Next: **convert cs-toolkit's `/parallel` adapter** with the method
`in-parallel-oy/cs-toolkit#1826` proved — map every
section before deleting any, contribute anything generic upstream first, then run it. It is a
200-line fork with a shared workflow already in the kit and no Codex counterpart, so it is the
same single-runtime shape as the one just done. Each conversion so far has found a kit bug the
fork was hiding; that is the reason to keep going rather than to batch them. `wrap-up` is the
one to leave for later — it carries `#93`'s Codex slug mismatch, and
`triage-friction-log`/`post-merge-systemize` cannot be converted at all until `#243` gives them
shared workflows.

### 2026-08-02 (Phase 2's blockers closed, and withdrawal beating repair)

**Theme —** Two PRs merged and one closed unmerged. In all three, the expensive part was a
mechanism *added in response to a review finding* — the doctrine already says to file those rather
than build them, and not following that is what the rounds were spent on.

- **`#41` — the required/optional manifest axis** (`ee3371d`). `kit-manifest.json` gains
  `required_by`, derived from the Python import graph rather than declared, so `/upgrade` stops
  filing a hard dependency under "sized-down adoption, or incomplete". It is a **mapping, not a
  boolean**: "required" is a property of a pair, so `lib/kitconfig.py` breaks a repo that installed
  an engine and is a legitimate omission for one that installed none.
- **`#134` cause 2 and `#226`** (`3e34fe5`). A `kit_repo_only` marker in the conftest that travels
  with the tests, skipping on the paths a test actually needs. Before it, a by-the-book `/adopt`
  tree ran **zero** tests — `test_panel_prompt.py` read the doctrine at module scope and collection
  aborted. The per-tree figures and their vendored subsets are in that PR's commits; a count
  without its tree identifies nothing.
- **`#230` closed unmerged.** A recovery rule for the panel's filing rule, dropped under its own
  pre-declared threshold when round 1 returned HIGHs from both lenses and the bot. Refiled as
  `#231` with every finding and the design questions they exposed.
- **`/upgrade` dry-run against a throwaway copy of cs-toolkit**, kit at `3e34fe5`. It **succeeds** —
  `kit_doctor` reports 32 unchanged, 0 differ, 0 missing, hook installed — and that is the finding:
  cs-toolkit's six Claude adapters all diverge from the kit's, the four measured reference no shared
  workflow doc, Step 4 says to keep them, and no `.claude/` path is in `KIT_OWNED` so nothing can
  report it. Step 5's own
  verification then runs zero tests, because test files never reach an adopter. `#236`. Live
  occurrences also recorded on `#51` (an older kit reported as "likely LOCAL EDITS") and `#93` (the
  slug mismatch installs the kit's skill *beside* the fork rather than replacing it).

**Learned**

- **The doctrine has prevention but no recovery.** "A new mechanism gets filed, however squarely a
  finding prompted it" is already in `fallback-review-panel.md`, and each expensive PR this session
  broke it. What it lacks is what to do once the mechanism is already in the diff and drawing
  HIGHs, where the default — patch again — is what turns two rounds into five. `#231`.
- **Withdrawal is the cheapest round available.** A shell-`source` scanner (`#228`) and a
  no-`.git` root guess (`#233`) were each removed rather than repaired after successive rounds found
  a fresh HIGH in the previous round's fix, and the round that removed them came back clean. Removal
  deletes surface instead of adding more for the next round to find.
- **A pre-declared threshold must be calibrated, and is binding either way.** `#230`'s fired on one
  HIGH at round 1, before any fix existed — stricter than the rule it was protecting, and it cost
  that PR. Honouring it anyway is the only thing that makes the mechanism worth having.
- **Claiming a test pins a guard is not the same as it pinning one.** This recurred across both
  merged PRs, each time verified false by deleting the guard and watching the suite stay green.
  `#229` and `#234` carry the instances; the check is to delete the thing, and it was skipped
  exactly where confidence was highest.
- **A measurement can be blind to its own subject.** The vendored trees are built from
  `git ls-files`, so a run taken before the new test file was tracked omitted the file under test
  and reported a clean result that was not. Build the tree from committed state.

**Open, and owned by nothing yet**

- Nothing was added to the inbox this session: `#71` took the closing-keyword scan occurrence, and
  the rest went straight to the tracker. Sweeping it needs `triage-friction-log`, which needs
  tracker writes and operator approval. Note `#143`.
- **Filed this session:** `#227`, `#228`, `#229`, `#231`, `#233`, `#234`, plus an occurrence on
  `#71`. `#233` is worth reading before touching test-tree resolution — it records three withdrawn
  attempts at the same problem.
- **Carried forward:** `#213`, `#167`, `#209`, `#120`, `#216`, `#220`, `#203`, `#190`, `#187`,
  `#124`, `#169`, `#170`, `#33`/`#112`, `#181`, `#93`.

▶ Next: **`#236`** — decide the adapter policy before running the cs-toolkit upgrade for real. The
file-copy half is proven: the dry run installed all 32 files cleanly. What is unresolved is that the
upgrade leaves the executed surface — the six forked `.claude/commands/` adapters — untouched while
reporting success, so a green upgrade changes nothing about how sessions behave. `#93` is one
instance of the same thing on the Codex side. Neither is a kit bug to fix first; both are decisions
that shape the upgrade plan. `#231` (the withdraw-don't-patch rule) is real but gates `#6`'s
vendoring, not this upgrade — a file copy has no mechanism to invent.

### 2026-08-02 (the doctrine split, the assembler that reads it, and where review yield actually comes from)

**Theme —** `#213` and `#214` merged. Neither result is the durable one. Across both PRs the
review rounds found almost nothing in the shipped change and almost everything in the *previous
round's repair* and in *claims about it* — and the lever that moved that was what the launch
prompt aimed lenses at, not how large the pass was.

- **`#213` — `fallback-review-panel.md` split** (`30feeec`). What executes keeps the name, so no
  referrer moved; the measurements and the three buried designs went to
  `fallback-review-panel-evidence.md`, linked once. Contract items are now cited **by name**, which
  is `#167`'s renumbering half — its reference-resolution check is still open, with three
  requirements recorded on the issue. **`#213` stays open**: the split landed, its "short enough to
  read before every panel" goal did not, because most of that file is executed prose rather than
  rationale. `#214` is the remedy; this was its dependency.
- **`#214` — `scripts/panel_prompt.py`** (`dc33e55`). Renders a lens's prompt by **quoting** the
  contract out of the doctrine at run time, resolving the base from the remote, and refusing rather
  than emitting anything misleading. **Its own** review prompts were generated by it from its first
  round, and lenses verified their briefings byte-for-byte against the doctrine and config. `#213`'s
  prompts were hand-authored — the assembler did not exist yet.
- **`#220` filed** — sub-HIGH findings from `#219`'s terminal round, logged rather than fixed under
  a bound declared before that round ran. Several are one-line changes; that is why the bound
  mattered.

**Learned**

- **Aim beats size.** Pointing lenses at "what prior rounds have not covered" changed yield more
  than any pass-size question did — and that carry-forward had no home except an author
  remembering to type it, which is now a flag. Full measurement on `#209`; cross-referenced from
  `#214` and `#211`. Weigh those together, not independently.
- **A property named by a commit message is not a property pinned by a test.** This recurred
  through `#219` until the sweep stopped fixing instances and fixed the class. `#220` records the
  remaining instances.
- **A stopping criterion declared *after* seeing findings is worthless**, and one declared before
  is only worth holding. Both PRs declared each round's criterion in advance; `#219`'s final bound
  held against every finding of that round, all of them cheap — they are on `#220`. `#194` is why
  the artifact lives on the PR — the receipt cannot
  carry it.
- **A correction can carry its own error.** Counts in commit messages and PR bodies went stale
  repeatedly, including inside paragraphs written to correct exactly that. What ended it was
  generating figures by shell substitution at the head rather than typing them.
- **CodeRabbit was rate-limited across most of `#213`'s PR**, so the panel was the substitute
  rather than a supplement there; the receipt says so. On `#214`'s PR it reported, and four of that
  PR's final-round findings are its — recorded on `#220`.

**Open, and owned by nothing yet**

- Sweeping the inbox needs the `triage-friction-log` workflow, which needs tracker writes and
  operator approval, so it is not done inline. Note `#143`: the tracker is past the size where
  `session-start`'s tracker step overflows.
- **Carried forward, all still open:** `#41` and `#134` cause 2 (the remaining Phase 2 blockers),
  `#213`, `#167`, `#209`, `#216`, `#220`, `#190`, `#187`, `#124`, `#169`, `#170`, `#33`/`#112`,
  `#181`, `#93`.

▶ Next: **`#220`** — sub-HIGH fixes, each already reproduced and specified on the issue, none
larger than a few lines. Good standalone work that needs no design decision. If you would rather
take a design question, `#209` now has three measurements behind it and an argument that its own
recommended direction is aimed at the wrong variable — read it before proposing anything.

### 2026-08-01 (two blocker fixes merged, and a guard withdrawn on the evidence)

**Theme —** `#134` cause 1 and `#37`/`#146` merged (`8edb4b6`, `82ef651`). Neither shipped change
drew a single review finding. Every finding across both PRs was in a **guard or a claim** built
around them — and on `#207` that guard was ultimately **reverted by operator decision** and refiled
as `#216`, because four consecutive rounds each found a regression introduced by the round before.

- **`#134` cause 1 — the issue's own numbers were stale, and the real failure was worse.** Its
  `19 failed, 368 passed` is reachable only with `--continue-on-collection-errors`, which nothing in
  the kit passes: the plain invocation **aborts collection and runs nothing**. Further corrections to
  the issue's own text are in its comments.
  **Cause 2 stays open** with a measurement attached — and no count is repeated here, because it is a
  function of both the vendored subset and the head.
- **`#37`/`#146` — three shipped files were untracked, so an upgrade refreshed a doc's links and not
  their target while reporting `0 differ, 0 unknown`.** `kit_doctor.py`'s entry now states in place
  that tracking closes that one instance and **nothing more**; `#146`'s pairing is still unguarded.
- **A guard was withdrawn, and that is the durable result.** Hand-rolling CommonMark in regexes kept
  producing regressions in its own repairs. `#216` carries the design (rebuild on a real parser) and
  per-commit shas so the parity oracle and pinned properties are recoverable rather than rewritten.

**Learned**

- **Two lenses read one sentence oppositely, and weighing the reports would have picked the wrong
  one.** Settled by rendering the text through CommonMark. Two other confident HIGH findings were
  refuted the same way. `#212`.
- **A verification harness that fails into the reassuring answer is the expensive failure**, because
  its failure is indistinguishable from the result it reports. One reported a surviving mutant as
  *killed* and nearly buried a valid finding. Occurrences are enumerated on `#205`, which is open and
  still collecting them.
- **A correction can fail its own rule.** A commit fixing a stale count carried a stale count, because
  the figure is written before the last edit. No count now appears in a commit message here; the one
  authoritative figure is generated by shell substitution at the merging head. Occurrence on `#149`.
- **I asserted a disposition I had not performed** — a commit message cited occurrence data on `#211`
  that did not exist. Caught by a lens comparing the issue's comment count against my prose, not by
  re-reading. The occurrence is now posted.
- **The bot and the panel are separate queues and only one was being drained.** A CodeRabbit finding
  sat unactioned for two rounds until an independent lens re-found it. Inbox has it.

**Open, and owned by nothing yet**

- **Review-process work is the operator's chosen next sprint, before the rest of Phase 2**: `#213`
  (split what executes from what explains) then `#209` (no proportionality valve), with `#167`
  falling out of `#213`. `#210`, `#211`, `#212`, `#214` are deliberately deferred until after the
  restructure; `#205` is the standalone if there is room.
- **Carried forward, all still open:** `#41` and `#134` cause 2 (the remaining Phase 2 blockers),
  `#190`, `#187`, `#124`, `#167`, `#169`, `#170`, `#33`/`#112`, `#181`, `#93`.

▶ Next: **`#213`** — read `fallback-review-panel.md` end to end and produce the split inventory
(every section classified executes / explains, contract items enumerated) **before editing**. Decide
and state the review-cost call for that PR up front, since it is doctrine and therefore first-class
prose reviewed under the rule it reforms. **Read `#213`'s correction comment first.** That
issue's original body says the `#37`/`#146` hazard is guarded by link tests added in `#207`; those
tests were reverted before `#207` merged, which the correction comment records. So the split must add
the new companion to `KIT_OWNED` and the manifest by hand — nothing fails if it does not.

### 2026-08-01 (the eighth sweep, configurable lens compute, and a panel that kept finding my own overclaims)

**Theme —** Three merges: the eighth friction sweep (`#197`), the root-permission test change
(`#199`, which settled `#195`), and configurable panel lens compute (`#200`). The durable result is
none of those.
It is that **every review pass this session found a false claim in work already verified**, and the
claims shared one shape — a measurement or a correction, true when written, stale when published.

- **`#198` filed — the Slack approval loop cannot be mechanically parsed.** Under a self-DM the
  operator and the pipeline share one identity, so Session B's "replies from the bot itself" rule is
  unevaluable; and the grammar has no "approve the rest" form, so the natural phrasing files nothing
  while reporting success. Both halves, with separate acceptance criteria, are on `#198`.
- **Sonnet lens compute is config now, not a per-run decision.**
  `review.fallback_panel.lens_compute.<runtime>`, independent optional `model` / `effort`, consumed
  on the Claude path by `pr_followup_hook.py` and on the Codex path by
  `.agents/skills/pr-watch/SKILL.md`. **`effort` is advisory on Claude Code** — its delegation tool
  has no per-agent effort parameter — and that caveat sits at all three surfaces because review
  caught it missing from one. Existing installs do not gain the key on upgrade; the doctrine doc
  says so.
- **Reading the tracker before drafting changed two proposals again, both by subtraction** — third
  sweep running. `#195` collapsed from a design question to two missing decorators once the marker
  it asked for turned out to already exist, applied to four tests in the same file. Routing table
  is on `#197`.

**Learned**

- **A correction must reach every surface at once, and I proved `#149` on myself.** Retracting an
  `effort` overclaim in the reference config and the doctrine doc left `init.sh` — the one adopters
  install from — carrying the retracted wording. Found by a lens that ran `init.sh` over a fixture
  instead of reading the diff. Nothing would have caught it: `init.sh` is not in
  `kit-manifest.json`.
- **A test can name a property and pin nothing; the mutant is how you find out.** "This key is
  load-bearing" rested on an append no test covered — deleting it left the suite green. The test
  that now fails on that deletion exists only because a lens performed it. Per-finding dispositions
  are on `#200`.
- **A receipt can name a lens that never ran.** `--lenses` is a typed string the engine does not
  verify (`#32`), and the cockpit can type it prematurely as easily as anyone. Inbox has it.
- **Reverting a mutant with `git checkout --` discards uncommitted work in the same file.** The
  panel doctrine already says mutate in an isolated copy; this is that hazard one level in, inside
  the cockpit's own tree.

▶ Next: `#193` — make `--mark-seen` print an excerpt of every key it promotes. Small, self-contained,
and it demonstrated itself on every ack this session (each printed a bare count).

### 2026-08-01 (a documentation PR, and the defect it found in the merge gate)

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

### 2026-07-31 (the loop got its exits, reviewed under the rules it replaces)

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

### 2026-07-31 (the seventh sweep, and the only step that caught anything)

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

### 2026-07-30 (one bug, seven review rounds, and the same defect five times)

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

### 2026-07-30 (two merges, eight rounds, and where every defect lived)

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

### 2026-07-30 (one flag, six rounds, and a bug older than the PR)

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

### 2026-07-29 (the sixth sweep, and three rounds that all found the same thing)

**Theme —** Three PRs merged. The result worth keeping is narrower than it first looked: across
three review rounds on one change, **justification prose was wrong in every round** — a recurring
defect category the mechanism's own tests cannot catch. Mechanism defects were found in every round
too; the first draft of this block claimed otherwise and a lens refuted it from the commits.

- **`#156` merged (`3d503c2`).** Sixth `triage-friction-log` sweep. Five inbox entries in, five
  accounted for: `#155` filed (a remark attributed to the operator must be quoted at its original
  scope) plus seven occurrence comments. Friction log 179 → 133 lines.
- **`#157` merged (`e9773ba`).** `#121`'s two halves. A gitignored `config/dev-model.local.yaml`
  merged over the tracked config for **`notify.user_key` only**; `tracker.*` stamped in the tracked
  file with a guard so no adopter inherits it — a non-interactive `init.sh` refuses a
  `project_name` that does not match the checkout's origin remote. Three adopter-facing defects
  fixed on the way: `/adopt` never seeded the ignore rule and never runs `init.sh`; the rule
  covered one filename while the loader derives `<name>.local.<ext>` for any path; and
  `add_ignore_line` turned a `.gitignore` ending `.env` into `.envstate/` across six call sites.
- **`#158` merged (`e76dd2c`).** `fallback-review-panel.md` now names the three failed
  stopping-rule designs, in addition to pointing at the fuller accounts, and separates a question they do not answer:
  **lens count is not bounded by class**, and the only sanctioned single-lens pass is Degraded
  mode, conditioned on runtime capability rather than on what the change contains.

**Learned**

- **Justification prose was wrong in all three rounds.** `_deep_merge`'s docstring said "two
  shapes" while implementing six; the overlay allowlist said its keys are "read by no shell reader"
  while `init.sh` read exactly them; a list rule was motivated by a key the same file asserts can
  never be set. It is written from *intent*, and intent is the one thing a reviewer cannot check
  against the code — nor can a test, which is why it recurred while the mechanism's defects were
  each fixed once. Correcting it added surface the next round then found defects in; **deleting it
  ended the loop**. That is the claim, and it is narrower than "the mechanism was never wrong",
  which a lens refuted: every round also found real mechanism defects, including three
  adopter-facing ones this block lists above.
- **One of the two late bugs was a regression from the previous round's fix, not both.**
  `pr_watch` re-raising at module import came from round 2's change and killed `--help`. The
  valueless-key-wipes-a-list hazard did not: round 1's guard was map-only from the start, so that
  route predates round 1 and survived it. The first draft claimed both, on four surfaces.
- **Generality was the defect, not the merge logic.** A config overlay honoured by one of several
  readers diverges everywhere. Narrowing to one key closed five findings at once — and `tracker.*`
  had to be removed after it made `session-start` on this repo query a project named
  "My Project Dev".
- **A single lens is a real pass.** One correctness lens on an 18-line docs change found six
  substantive issues, including a gloss that was roughly the inverse of what it described.
  Recorded as `fallback:claude`, not `fallback:panel`; the engine's own warning that one lens is
  not a green light is on the receipt.

▶ Next: `session-start` — several threads are open (`#121` still wants the friction-log header read
from config; `#124` and the `finalize.pr_draft` default now contradict the stated preference that
PRs not sit as drafts) and none is obviously first.

### 2026-07-29 (three failed designs, and what shipped instead)

**Theme —** An attempt to stop the previous sessions' review spirals. It failed three times, and
the failures are the result worth keeping.

- **`#153` merged (`b46f794`).** `fallback-review-panel.md` gains one section of *authoring*
  guidance — keep the record short, put detail in the PR, shorten a record that has needed
  repairing twice, and treat adopter-executed prose, commit messages and any record standing in
  for a control as first class. It loosens no control and says so explicitly. It also gave
  `workflows/pr-watch.md` the panel's missing precondition — that criterion applies only when the
  review bot is unavailable — and separated the poll/fix loop bound from per-change review rounds.
- **Three designs died first**, each killed by a panel on a real hole: a class defined by file
  type inside a section organised by function; the same class with functional tests, which the
  handoff passed while being the file the next session is told to act on; and a class-independent
  stop signal that beat the first class and whose trigger the author sets by choosing how verbose
  the fix round is.
- **Global git identity corrected** — `user.email` was `topi.jarvinen@gmail..com` (double dot) and
  `user.name` lacked its umlaut. Five commits from 2026-07-05/15 carry it; nothing from these
  sessions does, because GitHub's squash attribution used the account identity. Not rewritten.

**Learned**

- **Any rule whose trigger the author sets is a control the author can opt out of.** All three
  designs were versions of that, and the third one self-immunised: the commit proposing it
  rewrote the section, which by its own test made every later finding "prose the last fix wrote".
- **The premise was wrong.** "The record rounds did not earn their keep" does not survive: they
  caught a falsely closed issue, a false claim published to two tracker surfaces, and a falsified
  operator-approval record. The waste came from records being *elaborate*, not from being
  reviewed — and deleting prose (141 → 93 lines) is the only intervention that provably worked.

**Open, and owned by nothing yet**

- **The inbox is 179/150** and a sweep is due — the **fourth** consecutive session ending over
  budget (196, 203, 179, 179 since `06490a1`, against a budget of 150 throughout).
- **`#120` now carries this session's findings** — it proposes the cheaper terminal check these
  three designs were attempts at, so the reasons they broke are recorded there rather than only
  in this block.
- `#149`, `#150`, `#145`, `#146`, `#138`, `#139`, `#140`, `#141`, `#142`, `#143` and the rest per
  `session-start`.

▶ Next: `triage-friction-log` — the inbox has been over budget for four sessions. **Caveat before
running it unattended:** `notify.user_key` is blank, so the workflow stops at Step 2 by design; the
in-session-operator path is open regression `#128`, and `#124` records that its default draft PR
goes to a reviewer that will never read it.

No friction entries were added this session on purpose, and only one of the two lessons is in
doctrine: the record-length one is in `fallback-review-panel.md`, while *"any rule whose trigger
the author sets is a control the author can opt out of"* is recorded on `#120` — the tracker, not
the inbox, because it is the constraint any future attempt at that ticket must satisfy.

### 2026-07-29 (the fifth sweep, and a claim that was wrong in both directions)

**Theme —** One merge, four panel rounds, seven isolated lenses (two rounds on `#151`, two on the
wrap-up PR that records it). The sweep itself was never contested by any lens. The durable result is a failure mode the previous session's measurement
predicted but did not name: **an operator's narrow remark, inflated into a stronger claim and
published as operator-confirmed.** The fix for it then over-corrected, and round 2 caught that.

- **`#151` merged (`494b9eb`).** Fifth `triage-friction-log` sweep overall, dated 2026-07-29.
  Seven entries in, seven out: one graduated into two issues (`#149`, `#150`), six routed as
  seven occurrence comments (`#120`, `#138`, `#127`, `#75`, `#71`, `#45`, `#113`). LLM-only mode
  again (`#6` still not vendored). Inbox 203 → 136 against a 150 budget.
- **Two tickets filed:** `#149` (when a claim is corrected, enumerate every surface it was
  published to *at that moment*), `#150` (a scripted text replacement that matches nothing must
  fail, not report success).
- **The HIGH, and the HIGH inside its fix.** The operator said CodeRabbit is *currently* not
  available here. That was published as *"not installed, never exercised, nothing rate-limited"* —
  and then used to file a **structurally-never-reviews** verdict onto `#45`, the issue whose
  entire subject is that such a verdict cannot be made from outside. Both lenses found it
  independently. `#45`'s own body records a **Pro Plus** plan; `Review limit reached` notices sit
  on `#89` and `#99`. The correction then asserted a review count that was really a count of bot
  comments, and round 2 found *that*. Two independent re-derivations of "how many PRs did it
  actually review" disagreed with each other, so **no count was published**.
- **The silent run is twelve PRs, not seven** — `#102`, `#103`, `#104`, `#111` and `#148` were
  never counted. Third consecutive undercount in that series (four → six → seven → twelve). And
  `#151` merged silent too, so it is **thirteen** by the same rule — a lens caught the tally going
  stale inside the sentence announcing it was stale.

**Learned**

- **An operator's remark has a scope, and widening it is the same defect as inventing it.**
  "Currently not available" is not "never installed". The wider version was published on five
  surfaces and read as operator-confirmed on all of them, which is what made it durable.
  `#140` already asks for the command behind *"X is not available here"*; it arguably needs
  widening to cover *"X **is** available here, this much"* — round 2's finding.
- **Correcting a wrong number with a right one is a trap when the number is not recoverable.**
  Reviewed vs. quota-refused vs. silent is not cleanly separable from the comment stream without
  deciding what counts, and each attempt decided differently. Withdrawing the count was the only
  stable move — and the irreducibility is *better* evidence for `#45` than any count.
- **Deleting beat correcting, again — and it is now two-for-two.** Five review rounds across two
  sweeps have gone to the marker's verification section, every one finding the prose claiming more
  than the checks did. This session cut it rather than correct it a third time.
- **A check that errors can report a pass.** A closing-keyword scan built on a `grep -E`
  alternation with an empty branch was rejected by `ugrep`, exited non-zero, and the `|| echo
  clean` branch fired — printing a clean result from a check that never ran, inside the step
  guarding `#71`. A second run scanned a zero-byte surface and also read clean.
- **`#75`: 4 of 4 lens launches again**, all self-corrected. No running total is claimed; the
  addendum posted this session declares the existing tallies approximate and unreconcilable.
- **The check harness was left unfixed on purpose.** Round 2 showed checks 4/5 have headings
  larger than their assertions and that checks 1+2 share no trust chain (a forged snapshot yields
  byte-identical output). Documented, not repaired — building a harness inside a fix round is the
  mechanism-creep the panel doctrine warns against, and `#138`/`#127` exist to ask for it.

**Open, and owned by nothing yet**

- **`#149` and `#150`** — this session's two. `#149`'s own six-surface list **omits PR comments**,
  found by a lens after a retracted claim survived on one; that gap is unrecorded on the issue.
- **`#121` should absorb the config-placeholder question** rather than have it re-filed. This
  session re-derived `#121` from scratch without noticing it, and the rewrite of that entry then
  made a *larger* false claim than the one it corrected. The live inbox entry now routes there.
- **`#138` and `#127` are still the pair that would make a sweep's claims mechanically checkable**,
  and both were reproduced *again* inside this session's pilot run of them.
- **`#73` gained a *new* instance from this session's own archive sweep**, in the other direction:
  `kit-handoff-history.md` now says *"the 287-line figure **above**"* while that figure stayed in the
  live handoff. A lens found it; an earlier draft of this bullet claimed the *predicted* instance
  instead, which was the previous session's. Recorded in no routing row.
- **`#33`, `#112`, `#132` housekeeping is unchanged** from the previous session; `#132` is closed,
  so cs-toolkit Phase 2 blockers remain `#41`/`#37`/`#134`.
- **The inbox is back over budget the same day it was swept** — 179/150. The sweep took it 203 →
  136; wrapping up added four more entries and took it to 179. Not swept inline, per the
  wrap-up contract: graduating needs tracker writes and operator approval. Worth noting that a
  sweep now buys roughly one session of headroom, which is an argument for `#6` (vendor the
  engine) becoming urgent rather than merely open.

▶ Next: `session-start` — the threads are genuinely diffuse (two fresh tickets, two observations
recorded nowhere but here, and unchanged housekeeping), and nothing in the inbox is urgent despite it
being over budget. Page the tracker at `perPage: 25` reading `number`/`title`/`labels`/`state`
only — `#143` records `session-start` overflowing its tool limit at 68 open issues, and there are
~82 now.

### 2026-07-29 (the second sweep, and a documentation audit)

**Theme —** Two merges and nine panel rounds. The deliverables are routine; the durable
result is a measurement: **across nine rounds and at least fifteen isolated lenses, no HIGH finding
was in executable code** — one was in a squash message, which closed an issue before any round
found it (see below), so prose is not the same as inert. Every one was in prose — some of them inside `.py`/`.sh`
files, so "prose" means wherever it lives — and the prose that kept failing was the prose
*about* the verification, not the verification.

- **`#144` merged (`cdeae7a`).** Second `triage-friction-log` sweep dated 2026-07-28.
  Fourteen entries in, fourteen out: seven graduated into six issues (`#138`–`#143`), seven
  routed as five occurrence comments. Run in LLM-only mode again (`#6` still not vendored).
  Per `#128`, the graduation marker carries the approval record the DM would have — proposals,
  decisions, snapshot digest — plus an explicit statement of what its checks do *not* establish.
  Inbox 196 → 101 against a 150 budget.
- **`#147` merged (`030f053`).** Every prose surface audited against the engines, config,
  manifest and Makefile. The one that would have bitten: `CLAUDE.md` told the cockpit to branch
  `dev/<scope>`, the exact prefix `pre-push` refuses for narrative-file edits. Also corrected:
  `README`'s pytest command, a lane-sessions dir that does not exist, `path <scope>` documented
  as printing the sandbox when it prints the worktree, two live hooks and the `.mcp.json` lane
  copy documented nowhere, and `--assert-draft`/`--assert-ready` described as read-only checks
  when they *mutate* the PR.
- **Eight tickets filed:** `#138` (routing claims unverified), `#139` (`pr_watch.py:687`
  discards the 403 body), `#140` (extend `#54` to mechanism claims), `#141` (removal
  enumeration must be per-item and executed), `#142` (counterfactual step when a round removes
  a guard), `#143` (`session-start` overflows at 68 issues), `#145` (three config keys read by
  no code), `#146` (`parallel-headless.md` linked but untracked).
- **`#145` was closed by accident and reopened.** `#147`'s squash message read *"Filed rather
  than fixed:"* followed directly by the reference; GitHub matched it and closed the issue
  (`events` shows
  `closed commit_id=030f053`). The sentence asserted the opposite. This is `CLAUDE.md`'s
  closing-keyword ground rule and `#71`, firing in a session that was scanning for it — the scan
  never ran on a squash message. Occurrence data on `#71`.

**Learned**

- **The record about a change is a bigger defect source than the change.** The sweep moved the
  right bytes on its first commit and no round found otherwise; three rounds went to the record.
  The audit's edits were nearly all correct; three rounds went to its evidence. **Three** HIGHs
  were in prose that *ships* — `pr-watch.md`'s flag table, `devmodel_config.py`'s docstring, and
  the prerequisite list, which was wrong on **two** surfaces (`init.sh`'s `# Requires:` header and
  `README.md`). That is the class worth separating from the rest.
- **Correction-by-surface is the failure mode.** The same false `#23` sentence was fixed in the
  friction log (R1), found still live on `#45`'s comment (R2), then still live in `#140`'s issue
  body (R3). R4 found a fix that had silently matched nothing while its commit message reported
  it as landed.
- **Deleting beat correcting.** Two rounds of correcting the verification transcript each added
  prose and each added defects. Removing it took the file 141 → 93 and the defect surface with it.
- **A check heading is a claim.** "Every claimed comment exists on the issue it claims" asserted
  existence, author and timestamp — never content, which is how the `#23` HIGH survived a round.
  The integrity check was an unanchored substring test; a lens passed it against an archive whose
  visible text was destroyed and whose real bytes hid in an HTML comment.
- **`#75` is unanimous.** *Every* lens launch this session landed on `main` with an empty diff and
  self-corrected, because the launch prompt made reporting path/sha/diffstat mandatory *before*
  reviewing. A running count is not worth recording — the lens that reviewed this claim reproduced
  it too, so any total is stale on arrival. **At least 15, no exceptions** is the durable form.
- **CodeRabbit: seven consecutive PRs with no check and no comment** (`#126`–`#147`).

**Open, and owned by nothing yet**

- **`#138`, `#139`, `#140`, `#141`, `#142`, `#143`, `#145`, `#146`** — this session's eight,
  enumerated rather than written as a range, because `#138`–`#146` spans `#144` (a PR, not a
  ticket) and hides any member's state from a `#N` sweep. That is how a closed `#145` sat published in this
  list for ~13 minutes (closed `22:09:27Z`, list pushed `22:15:26Z`, reopened `22:28:07Z`). `#138` and `#127` are the pair that would make a sweep's own claims
  mechanically checkable — `#138` filed here, `#127` two sessions back — and both were
  reproduced inside this session's pilot run of them.
- **The friction inbox is well back over budget** — 203/150, from this session's seven
  entries. Another `triage-friction-log` sweep is due, and `#113`'s hazard has a **latent** *state-path*
  instance: `state/triage/frozen-inbox_{date}.json` would collide on a same-day re-run, and does
  not today only because the engine that writes it is not vendored (`#6`).
- **`#132`–`#136` from the previous session** — `#132` is **closed** (shipped `2026-07-28`), so
  the cs-toolkit Phase 2 blockers are `#41`/`#37`/`#134`. `#133`, `#135`, `#136` remain open.
- **`#33` and `#112` are shipped but still open** — close them deliberately after confirming
  `#131` is what each asked for.

▶ Next: `triage-friction-log` — **discharged** (`#151`). The inbox was 196/150, the same tripwire that opened this
session, and its seven entries are the freshest evidence behind `#120`, `#138`, `#127` and `#71`.
Prefer it over `session-start` this time: `#143` (filed here) records that `session-start`'s
tracker step overflowed its tool limit at 68 open issues and that the remedy it prescribes cannot
be run on this backend — there are ~80 open now, so page at `perPage: 25` and read
`number`/`title`/`labels`/`state` only if you do run it.

### 2026-07-28 · 4 (the mutation gate shipped; four panel rounds)

**Theme —** Two merges and a review loop that would not converge. The mechanism is small;
the durable result is a measured account of how a guard test can be defeated four times
running, and of a general argument being applied to instances it did not cover.

- **`#130` merged (`e8e7789`).** The `pr_watch` 403 entry from `#126` had the diagnosis
  right and the remedy wrong: it treated the proxy's *"an org admin must connect the
  Claude GitHub App"* body as actionable. It is a canned string — this is a personal repo
  with no org admin, and GitHub access was enabled throughout. Established by running the
  commands: `GET /user` returns `topij` **with the sentinel and with no auth header at
  all**; `/repos/*` and the public `/octocat` both 403; `documentation_url` is
  `docs.anthropic.com`. A path allowlist, not a credential problem.
- **`#131` merged (`9fb4baa`).** `driftcheck` marker on the byte-comparison test,
  registered in a new `scripts/tests/conftest.py` so it travels with vendored tests;
  `make mutation-test`; `fallback-review-panel.md` item 5 rewritten repo-agnostic with the
  rule that does not depend on any of it — **a kill is only a kill if a test asserting
  behaviour is what failed**. `#112`'s item 1 satisfied by construction; item 2 declined
  with reasons on the issue.
- **Five tickets filed:** `#132` (`/upgrade` cannot deliver anything under
  `scripts/tests/`), `#133` (the converse marker guard, with live instances on `main`),
  `#134` (kit tests hardcode `parents[2]`, so they fail in the `scripts/devkit/` layout),
  `#135` (a conftest `collect_ignore` is the one narrowing vector CI cannot catch),
  `#136` (panel lenses collide in the shared scratchpad, and copying a worktree is not
  isolation).

**Learned**

- **A guard test over an unbounded space cannot be finished.** Four rounds, four sets of
  HIGHs: a literal parked in a `#` comment; the first `target:` block read while make runs
  the last; `--deselect`/`-k`/`-k` with no space/`--ignore=`; symmetric narrowing; a
  dropped `.PHONY:` token. Every round's fix was the next round's finding — `rule 1`'s
  pattern, and severity never fell below three HIGHs.
- **But the general argument was applied to instances it did not cover.** "A text search
  cannot be sound" is true, and two of the three tests deleted on that basis were built on
  `make -n` — an *execution* probe. Deleting them opened the one hole the change existed
  to close: with the flag silently dropped from the recipe, the full suite stays green and
  a behaviour-only mutation then reads as a **kill**. The adversarial lens proved it by
  restoring the deleted assertions into every bypass and watching them kill each one.
- **My commit messages were the dominant defect, again — fourth session running.** Two
  measured figures were real and their write-ups under-specified what produced them (a
  "single module" narrowing that was partial; a `.PHONY` mutant needing an unstated
  flag duplication). Also promoted an *attested* 17/17 figure to "measured" **in the same
  commit that demoted it elsewhere**.
- **CodeRabbit registered nothing on four consecutive PRs** (`#126`, `#129`, `#130`,
  `#131`). The fallback panel was the only independent pass on all of them.
- **`pr_watch` cannot arbitrate the merge gate in a web container at all** — the whole
  API host is path-blocked — so both merges were reconstructed from MCP calls.

**Open, and owned by nothing yet**

- **`#132`–`#136`** — that session's five. `#132` and `#134` both land on the `scripts/devkit/`
  layout. *(`#132` has since closed — see the latest session's open list.)*
- **`#113` gained a third occurrence** — `chore/update-handoff-2026-07-28` already existed
  on the remote again; avoided by hand, still no mechanism.
- **`#33` and `#112` are shipped but still open** — close them deliberately after
  confirming `#131` is what each asked for.

▶ Next: `session-start` — **discharged**; the following session ran `triage-friction-log` and a
documentation audit instead. The cs-toolkit Phase 2 blockers named here were
`#41`/`#37`/`#132`/`#134`; `#132` has since closed.

### 2026-07-28 (the inbox graduated; the panel audited the record)

**Theme —** One deliverable, and a review panel that spent almost all of its findings on
the record rather than the sweep. The graduation is the small half; the durable result is
that the sweep's own accounting did not survive an audit, and that no gate in the repo can
tell a sweep from a deletion.

- **`#126` merged (`2d99593`).** The 24 un-graduated entries swept into
  `kit-friction-log-archive.md` behind a graduation marker; inbox 287 → 28 against a 150
  budget it had been over for three sessions. Routing: **13 graduated** into `#112`–`#120`
  and `#122`–`#125`, **10** routed as occurrence comments on issues that already existed,
  **1** discharged (`make test` discoverability, answered by the root `CLAUDE.md`).
- **Run in LLM-only mode.** `triage_friction_log.py` and `finalize_triage.py` are not
  vendored (`#6`), and `notify.user_key` is blank, so parse/draft/sweep were done by hand
  and the approval loop ran in-session instead of over DM.
- **`#121` came from running the workflow, not from the inbox** — the `tracker:` block in
  `dev-model.yaml` is still `init.sh` placeholder pointing at Linear, which `#6`'s engine
  will read the moment it lands.
- **CodeRabbit never reviewed `#126`** — no check, no comment, past its grace window. The
  fallback panel was the only independent pass.

**Learned**

- **The sweep's accounting did not survive an audit, and both lenses found the same
  defect.** The occurrence list named `#33`, summing to eleven against a stated ten, so an
  auditor checking "24 in, 24 out" got 25 with one entry double-counted. `#33` had received
  a cross-reference to `#112` — a *graduated* entry already inside the thirteen. Rated HIGH
  by the correctness lens; found independently by the adversarial one.
- **No gate in this repo can distinguish a sweep from a deletion.** Wiping both narrative
  docs to 3-line stubs leaves `make test` at 495 passed, `kit_doctor` at 0 differ, and
  `check_doc_budget` **greener** than the real branch (3/150 vs 28/150). Both files are
  `ADOPTER_OWNED`, so the drift check never compares them. Filed as `#127`.
- **A documented unconditional stop was bypassed and defended with the wrong rule.** The
  skill's notify-channel stop is absolute; the justification written into the PR body
  belonged to the non-interactive execution-context rule instead. Because `state/` and
  `reports/` are gitignored, no artifact of the proposals or the approval exists. Filed as
  `#128`, self-reported.
- **Both panel worktrees pointed at the wrong ref — 2 of 2.** Both lenses detected and
  corrected it because the launch prompt required verify-before-review. First occurrence
  set in this repo where *every* launch was wrong rather than right, so it cannot be
  folded into the earlier "8 of 8 correct" figures.
- **Four of the panel's ten findings were defects in the PR body itself**, including a
  verification claim naming no command — in the PR that files the issue about exactly
  that. Third consecutive session where the prose, not the change, carried the errors
  (`#120`).

**Open, and owned by nothing yet**

- **`#112`–`#128`** — this session's sixteen. `#112` (the manifest-hash gate is not
  coverage) is the highest-leverage: it invalidates every mutation claim over a
  `KIT_OWNED` file. `#127` and `#128` are the panel's own.
  **Superseded remedy —** this line used to end "until the regenerate-first step is
  mandatory", which is `#112`'s own proposed item 1. A later session took the opposite
  route: the drift test carries a `driftcheck` marker and is deselected *inside
  `make mutation-test`*, so there is no manifest gate left to discharge there and
  regenerate-first is deliberately *not* recommended
  (`fallback-review-panel.md` item 5 says so). Corrected here because a living plan that
  points the next session at a rejected remedy is worse than one that says nothing.
- **`#113` gained a second occurrence** — this session was a same-date second session, so
  `chore/update-handoff-2026-07-28` already existed on the remote. Avoided by branching
  off fresh `main` under a different name rather than by any mechanism.
- **`#75` gained a 2-of-2 occurrence set**; `#73` gained an instance the archive now
  carries deliberately (a swept self-link, left byte-identical to preserve the verbatim
  property).
- `#6`, `#33`, `#45`, `#54`, `#74`, `#76`, `#77`, `#93`, `#95`, `#97`, `#98` and the rest
  per `session-start`.

▶ Next: `session-start` — the threads are diffuse (sixteen fresh tickets, no in-flight PR,
nothing blocking), so let it re-read the tracker and propose. If you want one now: `#112`,
because every future mutation-testing claim depends on it.

### 2026-07-28 (`#92` shipped; the record corrected; five panel rounds)

**Theme —** Two deliverables, and a five-round panel that spent most of its findings on
this branch's own claims rather than on the code. The `AGENTS.md` template is the small
half; the durable result is a data-loss bug caught before it shipped and a much sharper
picture of where self-review fails.

- **`#104` merged (`985dcd0`), closing `#92`.** `docs/templates/AGENTS.md.tmpl` — the
  Codex entry point — rendered by `init.sh` through the same seed guard as the narrative
  docs, with two new tokens (`{{PROTECTED_BRANCH}}`, `{{HANDOFF_PATH}}`, repo-relative).
  `KIT_OWNED` row in, manifest 25 → 26. The verification command is deliberately a
  fill-me placeholder, not a token: `init.sh` knows no such value, so rendering one would
  have meant guessing (`#110` tracks giving it a real config key).
- **Seven corrections to the permanent record**, each re-verified against its primary
  source before editing rather than taken from the review that prompted them.
- **The rule-citation count went six → nine → ten.** Nine was itself wrong; the miss was
  `scripts/kit_doctor.py:101`. Two isolated lenses reached ten independently.
- **A live data-loss bug, caught pre-merge.** `seed_doc` matched the unrendered marker
  *anywhere* in a file, so any in-use doc that merely quoted the marker in prose was
  silently overwritten — no backup, run still printed "seeded". Reproduced against the
  pre-fix script on both a hand-written `AGENTS.md` and a rendered `kit-handoff.md`. The
  marker now counts on line 1 only, in `init.sh`, in `kit_doctor`, and in the tests.

**Learned**

- **Three separate pieces of new behaviour shipped unpinned** — the seeding call, both
  token substitutions, and later the `kit_doctor` predicate. Each survived the full suite
  when deleted. The manifest-hash gate reads as coverage and is not: it is discharged by
  one documented regenerate command, after which the mutant is green.
- **A fix round introduced a regression while fixing that same class.** Aligning
  `kit_doctor` with `init.sh` via `Path.read_text()` swapped one divergence for another,
  because universal-newline translation ends a "first line" at a lone CR where `head -n 1`
  ends only at LF. Round 3 caught it; round 2 had asserted the two matched "exactly".
- **A test can certify destroyed data as fine.** The line-1 assertions used
  `splitlines()[0]`, which breaks on nine separators production does not. A `U+2028`
  before the marker passed the suite while `init.sh` would seed over the live plan.
- **Rounds 1–4 each found a false claim in the previous round's fix**, most of them mine:
  a fabricated rationale in a test docstring, a "harmless" characterisation of a bug that
  was destroying data, a verification claim whose setup step was omitted, a side-effect
  claim whose cited command was scoped narrowly enough to hide the difference, and four
  consecutive sweeps declared complete that were not. The pattern is specific: the errors
  cluster in prose *about* verification, not in the verification itself.
- **Two lenses beat one, twice.** Round 3's correctness lens explicitly cleared the CR
  case as "behaviourally equivalent for all realistic inputs" — it had tested CRLF but not
  CR-only, where the adversarial lens proved divergence by execution. A lens's "verified
  clean" is worth exactly the edge cases it ran.
- **Convergence is visible when it happens.** Round 5 came back clean on the code: 4000
  randomized byte documents and a 30-cell separator matrix driving the test helper, the
  `kit_doctor` predicate and the real `head -n 1 | grep -qF` over identical bytes, with
  zero disagreements. That, not round count, is what ended the loop.

**Open, and owned by nothing yet**

- **`#105`–`#110`** — this session's six: `/adopt` never seeds `AGENTS.md`; `kit_doctor`
  aborts on unreadable/directory/invalid-UTF-8 docs where `init.sh` fails safe; the marker
  predicate is duplicated between `kit_doctor` and its tests and kept in sync by a
  docstring; `AGENTS.md`'s config-derived links freeze at first render; the intermittent
  `test_portability.py` flake; and the template's fill-me placeholder.
- **`#77` reproduced** — I edited the shared tree while a lens was reviewing it. The lens
  caught it on its own initiative, not because the contract asks. Occurrence logged there.
- **`#47` gained a third instance** — `docs/AGENTS-sections.md` untracked, alongside `#37`
  and `#41`. Not fixed, because adding one more hand-maintained row is what `#47` exists
  to stop.
- **`#93`, `#95`, `#97`, `#98`** unchanged; `#54` is directly relevant after this session.
- `#50`, `#66`, `#71`, `#72`, `#75`, `#76`, `#86`, `#88` and the rest per `session-start`.

▶ Next: `triage-friction-log` — **discharged**, shipped as `#126` later the same day. The
inbox is now 28 lines; the 287-line figure above is that session's reading, kept as the
record of why the sweep was called for.

### 2026-07-28 (fix-round scope shipped; the severity gate it exposed)

**Theme —** Two doctrine changes, the second existing because the first cost far more
than it should have. `#101` took three panel rounds and six isolated reviewers for one
paragraph; `#102` is the rule that stops that recurring.

- **`#101` merged (`238de25`), closing `#100`.** Rule 3 gains *"a fix round addresses
  only what the review found"* — a new mechanism is an addition however squarely a
  finding prompted it, so it gets filed. Plus a paragraph in `fallback-review-panel.md`
  stating that lever replaces none of the stopping criterion.
- **One of `#101`'s two HIGHs came from my own fix rounds — not both.** Round 2's HIGH
  was a gap the rule inherited: it did not catch two of the three cases it is built on,
  and `205d0a4`'s own message records that `#100`'s proposed wording has it too — round
  1's carve-out licensed those cases outright but did not create the gap. Round 3's
  HIGH was mine: two fresh readers, given only the paragraph, both permitted the case,
  both quoting my carve-out clause.
- **`#102` merged (`87dfa83`).** The blast-radius classification now also decides which
  findings to act on. A gate, send path, destructive operation, or kill/recovery path —
  plus any change that does not clearly sit in one class — gets **every** finding acted
  on; only on the second, reported-but-never-acted-on class is the gate HIGH always,
  plus anything at any severity that says the change is a *regression* rather than
  merely imprecise. New contract item 9 makes lenses report both labels.
- **CodeRabbit reviewed neither PR's final state** — one clean pass on `#101`'s first
  head, then a plan quota that no waiting clears. The fallback panel was the independent
  pass throughout: five rounds, ten isolated lenses across the two PRs.

**Decided**

- **Two failed tightenings ⇒ delete, applied to my own clause.** `#101`'s carve-out was
  itself an unrequested mechanism added mid-fix-round in response to a MED — the shape
  the paragraph prohibits, reproduced inside it. Deleted rather than reworded a third
  time.
- **Severity level alone is the wrong gate.** `#102`'s own first round returned 0 HIGH /
  7 MED, four of which said the paragraph loosened a control it claimed to tighten. The
  discriminator that works is regression-vs-imprecision.
- **The gate belongs at the act-on stage, never in the lens prompts.** `#101` was
  docs-only and drew two real HIGHs; a lens told to calibrate down for "it's only docs"
  would have downgraded exactly those two. It is also the anchoring contract item 2
  forbids.

**Learned**

- **A gate that reads labels nothing produces is not a gate.** `#102`'s HIGH: "act on
  HIGH" and "says regression" are lens output, and no contract item or `focus` string
  ever asked for either. It read as working only because I supplied severity ad hoc in
  my own launch prompts — the drift the single-source rule exists to stop.
- **A three-space list continuation is correct CommonMark and broken Python-Markdown**,
  which silently renumbered rule 4 to rule 1 while the header still said "Four rules
  apply". Ten files outside the session records cite these rules by number (fourteen
  counting the records themselves). Caught by rendering in both engines,
  not by review — a genuine completed bot review of the head carrying it passed clean.
- **I shipped a false claim in a commit message** (`4ac203e`), retracted in the PR body
  before merge, so it never reached `main`.
- **`#76` reproduced twice**: neither PR's final head was lens-reviewed, and
  `--record-review --head` can only assert the exact head, so both merged with the
  coverage recorded as PR prose and no receipt.

**Open, and owned by nothing yet**

- **`#92`, `#93`** — untouched; `#92` was the planned follow-on and now lands under both
  new rules.
- **`#95`, `#97`, `#98`** — the three panel-found defects on `main`, unchanged.
- `#47`, `#54`, `#66`, `#71`, `#72`, `#75`, `#76`, `#77`, `#86`, `#88` and the rest per
  `session-start`.

▶ Next: `#92` — ship `docs/templates/AGENTS.md.tmpl` rendered by `init.sh`, added to
`KIT_OWNED` and the manifest so `kit_doctor` reports it. Read `#92` for the generic
spine to lift; note in the template that adopters are expected to extend it.

### 2026-07-27 · 4 (gh-less REST transport; `#91` closed, `#96` merged)

**Theme —** One feature, five review rounds, two PRs. The first attempt was closed
unmerged because *severity rose every round* — each round hardened one more boundary and
the next round found the next one. The second bounds the new transport structurally
instead, and merged.

- **`#96` merged (`fd75cd7`), closing `#90`.** `pr_watch` can poll without `gh` (REST
  over `urllib`, `GH_TOKEN`/`GITHUB_TOKEN`), and on that backend it **polls only**:
  `mergeable` is false by construction and `--record-review` / `--assert-draft` /
  `--assert-ready` refuse. Suite 418 → 488, and 488 again with `gh` off PATH.
- **`#91` closed unmerged** with its rationale on the PR. Three panel rounds found 2, 2,
  then ~7 HIGH — **three of them introduced by the previous round's own fixes**. Six of
  the seven were "some degraded response makes REST report `mergeable: true`".
- **The bound costs nothing**: `dev_session.sh cmd_merge` resolves through `gh repo view`
  + `gh pr list` *before* it reads `mergeable`, so a gh-less session never had a merge
  path. `#96` turns that accident into an enforced invariant.
- **Filed six issues** (`#92`–`#95`, `#97`, `#98`) — the Codex-adapter pair, the
  broadening bar, and three defects the panel found that predate this work. `#96` is the
  PR, not an issue.

**Decided**

- **A structural bound beats validating every boundary** (rule 1's "deterministic
  artifact"). Five rounds of per-boundary tightening never converged; one guard in one
  place ended the class. Kept to two functions so `#94`'s broadening is a deletion plus
  its 13-row bar, not a rewrite.
- **Two of my own mechanisms deleted under rule 1 rather than tightened**: a request
  ceiling that created a fail-open by starving the one caller that swallows its
  exception, and a settle-baseline reset that disabled the false-settle guard on the
  **default `gh` backend** for every existing PR.
- **A third lens earns its place when the first two keep finding the same shape.** Two
  general lenses each found one HIGH per round — in the tests on round 1, engine
  fail-opens after that; a lens briefed only on "enumerate every external input, trace
  it to a permissive verdict" found three the others never saw. Its 56-row input
  enumeration is distilled to the 13-row acceptance table now on `#94`.
- **Coverage recorded piecewise, again.** The final delta (a reviewer-requested doc line
  + a manifest hash) is unreviewed and says so, with `bots_behind_head` on the receipt.

**Learned**

- **My own fixes were the largest single source of HIGH findings** — three of the seven
  fail-opens across both PRs, one of them on the *default* `gh` backend, with a test
  that pinned its permissive outcome as correct. The reviewed, *requested* fixes held; the unrequested
  hardening I added alongside them is what broke.
- **My claims were the dominant defect four rounds running** — a comment naming a
  consumer that did neither thing claimed, "nothing branches on this" about a field that
  gates a merge, "read-only" surviving on the two surfaces operators read, a commit
  claiming a docstring fix it never applied. Also: the cs-toolkit reasoning backwards and
  the diff-size comparison wrong twice, both flattering, both corrected on the record.
- **I pushed a red tree** by chaining `make test` into commit-and-push and acting past a
  failure on screen.
- **The provided worktree was at the base ref on 5 of 5 panel launches**, and every lens
  detected it because the prompt required clone-verify-report. Posted to `#75`; no
  cumulative claimed — the earlier sessions' figures count a different thing.

**Open, and owned by nothing yet**

- **`#94`** — broadening REST to merge authorization, with the fail-open enumeration as a
  written bar. Needs a real consumer first; nothing can merge gh-lessly today.
- **`#95`** — a pre-existing fail-open on `main`: a PR can forge a check that cancels its
  own reviewer's pending block. **`#98`** — pre-existing too, but it *hides* blockers
  rather than opening the gate: `render` sanitises comment bodies and not the path/author
  beside them, so a filename can walk the cursor over them. **`#97`** — no guard stops a kit test hitting the network.
- **`#92`, `#93`** — the kit ships Codex skills but no `AGENTS.md`; cs-toolkit forked the
  wrap-up workflow into a 160-line skill. `#93` must recover upstream content *before*
  thinning it.
- **The cs-toolkit `pr_watch` swap is unblocked** and is the *fix* for that repo's two
  transport fail-opens, not the trigger (correction recorded on `#94`).
- `#47`, `#66`, `#54`, `#71`, `#72`, `#75`, `#77`, `#86`, `#88` and the rest per
  `session-start`.

▶ Next: `session-start` — several independent threads (`#92`/`#93` Codex adapter, the
cs-toolkit swap, `#47`, `#100`, and three panel-found defects on `main`), so let it
re-propose.

### 2026-07-27 · 3 (CLAUDE.md; init.sh harness + fixes; review loop worked)

**Theme —** Worked the review-round problem directly. Three PRs merged, each watched to
convergence with real independent review: two CodeRabbit passes obtained by re-triggering
after rate-limit windows, four fallback-panel rounds that caught two config-bricking
regressions **in my own fix** before they shipped.

- **`#83` merged (`63acfcf`).** Root `CLAUDE.md` naming `make test` as *the* verification
  command — the discoverability precondition for `#54`. CodeRabbit reviewed the exact
  head clean after a re-trigger (its rate window was 13s).
- **`#85` merged (`cde96e8`), closing `#84`.** init.sh fixture harness: 14 tests — 10 pins
  plus 4 strict-xfail reproductions of `#62`/`#67`. `#84` corrected the record first: init.sh
  was **not** at zero coverage — its migration path was well covered; the three open
  bugs lived in the uncovered paths — detection (`#67`), hostile-value stamping (`#62`),
  hooks (`#66`); seeding and `.gitignore` were uncovered but bug-free.
- **`#87` merged (`7c71385`), closing `#67` + `#62`.** Manifest-derived engines
  detection (top-level names only), lossless-only quoting (`yaml_scalar` /
  `quoted_scalar`), one shared YAML-correct comment scanner, ENVIRON value transport,
  quoted bots serialization. Suite 372 → 418 across the session.
- **The panel earned its cost on `#87`**: round 1 caught my always-quote change turning
  an interior `"` into an unloadable config and `\` into a reader split-brain — worse
  than the bug it fixed; round 2 caught the same class surviving on the five
  always-quoted fields, plus a bots single-quote regression. None were caught by the
  suite as it stood at those heads.
- **Stale `chore/update-handoff-2026-07-27` deleted** after verifying full supersession
  (its fixed text is on main/archive; the graduated issues quote the fixed numbers).
- **Filed `#86`** (.mcp.json sniff misses the kit's own documented credential shape) and
  **`#88`** (the three config readers disagree on where a value ends). **Corrected**
  `#67`'s Note (it miscited `#36`, the pre-push twin).

**Decided**

- **A rate-limited reviewer with a short recovery window gets re-triggered, not waived
  or substituted.** `@coderabbitai review` after the window produced real reviews of the
  exact head on `#83` and `#87`. Windows observed ranged from 13s to 48min — panel when
  long, re-trigger when short.
- **Piecewise review coverage is recorded piecewise.** `#87`'s final delta
  (reviewer-prescribed fixes only) merged without a bot pass of its own; the receipt's
  `bots_behind_head` annotation plus a PR comment state exactly what covered what.
- **Quote only when lossless.** Blanket-quoting stamped values is a corruption class,
  not a fix — values YAML would reinterpret (`"`, `\`, leading `'`) stamp raw as they
  always did.

**Learned**

- **The handoff's own claim was the defect again — fifth consecutive session.** "init.sh
  has no automated test coverage" was false (four migration tests run it); caught this
  time by grounding before filing rather than by a reviewer, and the corrected framing
  changed both the issue and the work.
- **Panel isolation went 8 for 8** when every launch prompt assumed the worktree was
  wrong and required clone-verify-report — the inversion `#75` proposes, working as
  predicted (contrast: 9 of 9 wrong across the prior two sessions). Occurrence data
  posted to `#75`.
- **`#44`'s shape depends on how the review was triggered**: clean reviews on `#83`/`#85`
  arrived as edited comments (no review object — coverage machinery blind, receipts
  recorded by hand); `#87`'s re-triggered pass submitted a real review object with a
  commit SHA, so `coverage` populated (`covers_head: true`). Posted to `#44`. The
  rate-limited check reporting **pass** recurred four more times (posted to `#45`).

**Open, and owned by nothing yet**

- **`#86`, `#88`** — this session's filings; both small and well-specified.
- **`#47`** — called the highest-leverage unbuilt thing in three recent sessions. A scope
  note is posted on the issue itself: `#87` left init.sh's fallback triple as a
  deliberate manifest-lost fallback, so `#47`'s tree-derivation should say whether that
  restatement is in or out of its scope.
- **`#66`** — still behind the `#61` design call. `#54`, `#71`, `#72`, `#75` (now with
  supporting data), `#77`, and the rest of the backlog per session-start.

▶ Next: `#47` — derive `KIT_OWNED` from the shipped tree and fail CI on divergence; its
own body names `#36`/`#37`/`#40`/`#41` as the gap class it closes.

### 2026-07-27 (friction-log inbox graduated; `reports/` contract settled)

**Theme —** Ran the triage sweep the doc-budget warning had been asking for. Thirteen
entries in, thirteen accounted for. Both PRs merged **without an independent review** —
CodeRabbit was rate-limited on its plan while its status check reported **pass**, twice.

- **`#78` merged (`8b1d6b2`).** 13 un-graduated entries → 8 issues (`#70`–`#77`) plus one
  no-ticket. Four of the eight each merge **two** entries recorded on separate days,
  because the occurrence count is the evidence (`#71` three occurrences, `#75` nine of
  nine). Friction log 190 → 50 lines, back under its 150 budget.
- **`#79` filed, `#80` merged (`4e9cad9`).** `reports/` carried two contradictory
  contracts — `post-merge-systemize` said never commit it, `triage-friction-log` said
  git-track it, and `.gitignore` matched neither, so the first rule was unenforced. Now
  ignored here and in `init.sh`, with both skill lines corrected.
- **The triage engine is still unvendored (`#6`)**, so the sweep ran in the skill's
  LLM-only mode: marker, archive sweep and finalize done by hand against the same
  contract, with a frozen-inbox snapshot for window safety.

**Decided**

- **A rate-limited reviewer is not a waiver, but the operator may waive it.** Both
  waivers were explicit and scoped — the second was re-asked rather than extended,
  because that diff touched `init.sh` and not only docs — and both are recorded on the
  PR and in the squash body. **No review receipt was written**: a receipt would flip
  `mergeable` and let automation merge unreviewed work.
- **Use closing keywords deliberately rather than avoiding them.** `#80` carried one
  intended `Closes #79`, linted before push and verified after opening. Across two squash
  merges: `#79` closed, `#70`–`#77` all still open. The rule forbids *unintended*
  adjacency, not the mechanism.

**Learned**

- **`make test` exists and runs the whole suite in 22s** (372 passed). I probed
  `uv run pytest` and `python3 -m pytest`, both failed, and wrote *"tests were not run
  locally — pytest is not installed"* into `#80`'s body. False; corrected on the PR.
  Nothing in the repo points at `make test`, and there is no root `CLAUDE.md`. Fourth
  consecutive session where a claim of mine was the defect.
- **The kit's own triage skill defaults to a draft PR, and CodeRabbit skips drafts
  outright.** The workflow's happy path produces a PR its configured reviewer will never
  read, and the skill says nothing about it.
- **A rate-limited CodeRabbit reports `pass`** — the `#23` surface, now with two fresh
  instances in merged PRs and a third in the history file.

**Open, and owned by nothing yet**

- **`#70`–`#77`** — this sweep's output, untouched. `#71` (closing-keyword guard) and
  `#75` (invert contract item 7, nine of nine) carry the strongest evidence.
- **`chore/update-handoff-2026-07-27` holds unmerged work and needs an operator call.**
  `f3d4e6e` ("fix eight claim errors a review lens found in this handoff") and `30ab573`
  ("fix a cross-reference this sweep broke") are **not ancestors of `main`** — an earlier
  session's branch that never landed, possibly superseded by `42873d8`. Left intact
  rather than cleaned up. It is also what `#81` was accidentally opened against.
- Everything open at the end of the **2026-07-27 `#59` + `#61.1`** session still stands:
  three `init.sh` defects with no coverage and nothing tracking that gap, `#61`, `#47`,
  `#50`, `#60`. (Named rather than "the block below" — an archive sweep moves blocks
  between files and orphans relative pointers; that is `#73`.)

▶ Next: **a root `CLAUDE.md` naming `make test`, then the `init.sh`-coverage issue** —
today's false "tests not run locally" claim on a merged PR is the second verification-claim
defect in as many sessions and the fix is one file; then pick up the carry from the
`#59` + `#61.1` session, where three `init.sh` bugs are open against a file with zero
coverage and no issue tracking that gap.

### 2026-07-27 (#59 + #61.1 shipped; #61.2 built and reverted)

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

### 2026-07-26 (cs-toolkit Phase 1; kit lint; #60 attempted and reverted)

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

### 2026-07-26 (adopter upgrades)

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

### 2026-07-26 (#26, overnight)

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

### 2026-07-25 (Phase 3b)

**Theme —** Fixed #19 + #23 together, and then spent most of the session discovering
that **the fix rounds were more dangerous than the original diff**. Seven review rounds
on #25 alone; every one found something real; five of them found a defect introduced by
the previous round's fix.

- **#25 merged — #19 and #23 closed.** `summarize_review_bots` resolves each configured
  bot to *unavailable* (outage announced on a comment body **or** a status-check
  description — the surface that was invisible) or *pending* (a verdict still coming).
  Pending blocks the merge gate until it ages past `review.bot_pending_grace_minutes`;
  unavailable never blocks and is the action signal. **Nothing reaches `converged`** —
  that is the whole design, and it is what let both be fixed at once.
- **#28 merged — #10 closed.** The state_paths suite failed from inside a lane worktree
  because its fixture cleared every sandbox *env* signal and not the *cwd* one. The
  issue predicted a per-test audit would be needed; it wasn't — every cwd-sensitive test
  already chdirs itself. A mutation pass showed the fix makes the suite *stricter*:
  three tests had been passing by accidentally discovering the real repo root.
- **#29 merged — half of #27.** `review_bots.coverage` reports which commit each bot's
  last review actually saw, and `--record-review` records it as `bots_behind_head`.
  Verified against the real #25, where it reproduces the gap I had had to work out by
  hand an hour earlier. #27 stays open for the shape-change half.
- **#26 and #27 filed** from the friction-log inbox, both with concrete sketches.

**Decided**

- The anti-wedge property lives in `converged` alone. Every new signal feeds the merge
  gate, which already needs an explicit receipt — so a gate can wait, but the poll/fix/ack
  loop can always finish.
- **Report, never gate.** All three new fields (`signal`, `bot_signal`/`override`,
  `coverage`) make an omission legible at merge time and block nothing. The faithful
  version of each risks wedging a repo whose bot is permanently unavailable.
- **Stop patching a mechanism that keeps corrupting.** The `init.sh` marker migration
  produced **three** distinct config corruptions across three rounds, each while its own
  post-conditions passed and it printed success (the fourth round's finding was about
  the *replacement message*, not the surgery). It was deleted rather than patched again;
  `init.sh` now detects the gap and prints what to add.

**Learned**

- **A fix round on gate logic is where the next bug comes from.** Session-wide:
  **13 review rounds across #25, #28 and #29 — all 13 found something.** Seven of those
  findings were defects introduced by the *previous round's fix* (five on #25, two on
  #29), twice at HIGH. **No round on any PR came back empty**; #29's fourth pass found
  no HIGH or MEDIUM but still found four LOW, including a stale comment and a dead-
  argument trap. `safety-critical-changes.md` rule 3 already says to treat "the last
  round found nothing" as provisional — this session never reached that state at all,
  so the practical question is not when the findings stop but what blast radius
  justifies stopping anyway.
- **Stopping has to be calibrated to the blast radius, not the round count.** #25 was a
  merge gate — worst case, an unreviewed PR lands. #29 is a reported-never-gating display
  field — worst case, a wrong warning. Same review doctrine, different stopping points,
  and saying which one applies is part of the merge decision. The `never gates` property
  is what made that judgment available, and it was *proved* rather than assumed — by a
  review pass sweeping report shapes ad hoc, and in-repo by
  `test_review_coverage_is_reported_and_never_gates` plus the 32-combination matrix in
  `test_done_keeps_its_original_merge_authorization_semantics`.
- **Reading is not running.** Three defects were invisible to careful reading and obvious
  on execution — most sharply, CodeRabbit's pending check reports the zero timestamp, so
  the "unmeasurable age fails open" branch was not an edge case but the *only* path that
  bot ever took. The #19 guard was dead code for its own target, and only polling the
  live PR showed it.
- **Mutation testing found what test names asserted and test bodies didn't.** Five
  properties across the session were named in tests or claimed in a PR body and pinned by
  nothing: on #29, anchored author matching, newest-review-per-bot, and the `bots=`
  threading; on #25, the `init.sh` list-style branch and `grep -qi`'s case-insensitivity.
  Each was found by breaking the code and watching the suite still pass.
- **Every whole-file `grep '^  key:'` in a config migration is a bug in two directions**
  — it misses the key at another indent *and* matches a same-named key under an unrelated
  section. This change shipped one of each.
- **Removing a dangerous mechanism does not make its replacement safe.** After deleting
  the list surgery, the replacement *message* still told inline-list adopters to add a
  block item — walking them into the same corruption by hand.

**Open, and owned by nothing yet**

- **#27's other half** — invalidating a receipt when the diff changes *shape*, not just
  when the head moves. The cheap half (visibility) shipped; the faithful half runs into
  the same wedge tension as #19/#23.
- **#26** — the fallback panel. Run manually ~10 times this session (5 rounds on #25,
  4 on #29, 1 on #28), two fresh-context lenses per round. CodeRabbit completed only 3
  reviews across 17 pushed heads, so the panel carried most — not all — of the load; one
  of its 3 was the round that caught the "ACTION NEEDED" bug. Highest-value unbuilt thing
  in the tracker.

▶ Next: **#26** (make the fallback a panel spec). CodeRabbit was rate-limited on nearly
every head all day (3 completed reviews across 17 heads), so the panel carried most of
the review load — and it is still two manual subagent launches per round, ~10 rounds this
session. Two things this session learned belong in its prompt:
require the lens to **execute** the changed paths (three defects were invisible to
reading and obvious on running), and to **mutation-test** new branches (that is what
proved five separate properties were named by tests and pinned by nothing).

### 2026-07-25 (Phase 3a)

**Theme —** Made the Phase 3 sequencing decision, and it changed under scrutiny — twice.
Both times the correction came from asking what a *stale reader* of the mechanism would do.

> **What "Phase 3" and "the cs-toolkit back-port" mean.** cs-toolkit
> (a separate private repo) is where this kit's
> mechanisms originated; the kit generalized them, and the back-port is returning the
> improved versions. Phase 3 is the review-receipt + merge-gate slice of that. The vocabulary
> has never been written down outside this handoff, which made the claim below unverifiable
> from inside this repo — recorded here so the next session doesn't have to reconstruct it.

- **The blocking problem was not the porting order.** `decide_done` conflated "is there
  more for me to fix?" with "is this authorized to merge?", because `cmd_merge` had no
  other hook — it re-polled `pr_watch --json` and gated on `done`. That conflation, not the
  sequence of ports, is what would have wedged cs-toolkit's nightly fixer — its per-lane
  review step (`.claude/commands/nightly-fixer.md` Step 6.2 in that repo) watches to
  green-and-clean and records no receipt. Fixing it removed a whole phase from the plan.
- **#22 merged.** `converged` (watch loop) and `mergeable` (merge gate) are now distinct;
  `dev_session.sh merge` gates on `mergeable`. Tests 196 → 202.
- **The first cut of #22 failed open, and my own adversarial re-read caught it — not
  CodeRabbit, whose pass on that commit raised only a `local`-declaration nit and a test
  nitpick.** It redefined `done` to
  mean watch-convergence. Because `/upgrade` refreshes engines **per file** (`missing` is a
  supported state — "a sized-down adoption omits engines deliberately (one surveyed repo
  installs 2 of 6 on purpose)"), a new
  `pr_watch.py` can run against an older `dev_session.sh` whose gate reads `done` — which
  would then have authorized merges on PRs with no review receipt at all.
- **So the schema only grows.** `done` stays an unchanged alias of `mergeable`, and both
  skew directions fail closed. Note what is pinned where: the *function* `decide_done` is
  held to the pre-split expression across all 32 boolean inputs, but the thing that actually
  protects an older `dev_session.sh` is the report **key**, and that is pinned by a matrix of
  report shapes rather than exhaustively. Worth keeping straight — the same function-vs-key
  confusion is the next bullet's finding.
- **CodeRabbit was rate-limited**, so the configured fallback pass ran instead. It found
  three further issues, including a docstring that claimed a compatibility guarantee the
  *function* doesn't provide — the report **key** does.

**Decided**

- Enforce at the merge point, never at `converged`. A watch loop asking "anything left to
  fix?" should never be answered "no" only once a review receipt exists.
- A field that a safety gate reads may be added to, never redefined.
- #19 and #23 get designed together — they are the same ambiguity on two surfaces, and
  both run into the informational-check exclusion being load-bearing against wedging.

**Learned**

- **Documentation does not reach a stale reader.** Redefining `done` was safe by every
  local reading of the new code and unsafe in fact, because the component that would have
  been wrong is the one that never sees the new docs. Version skew is not hypothetical
  here: per-file engine upgrades are a supported, documented workflow.
- **An unavailable reviewer can be indistinguishable from a clean one.** CodeRabbit's
  rate-limit arrived as a status-check *description* on a check classified informational,
  so nothing surfaced it (#23). The doctrine's "a blocked bot is an action signal" rule can
  only fire if the outage is detected.
- **#22 merged without satisfying review rules 2 or 3, and that should be recorded as a
  violation rather than a compromise.** The doctrine has no "floor" the author's own pass
  can meet: rule 2 says a single-lens verdict is "not a green light", and rule 3 wants
  re-review until a pass finds nothing new — but the fallback's approve was written in the
  same pass that produced `32f3e4f`, so no *independent* review ever covered the final
  commit — the fallback saw that code, but only as the author re-reading their own fixes.
  CodeRabbit's only review was bound to the first commit, before the redesign.
- **A cold-context subagent reviewer found what three self-review passes missed** — a stale
  comment on the merge gate itself (`dev_session.sh` `cmd_merge`), describing the design that
  was rejected. It shipped to `main` in #22 and was fixed in the wrap-up PR (#24), so the
  artifact is visible only in that diff. Authorship anchoring, not capability, is what
  self-review cannot escape.
- A second, adversarially-prompted subagent pass then found nine further issues in the
  wrap-up itself — including this handoff misattributing a test-coverage claim, and the PR
  description still carrying the "floor" framing the diff had already retracted. The two
  lenses overlapped on nothing, which is the doctrine's disjointness claim holding up.

**Open, and owned by nothing yet**

- **#22's merged design has still never had an independent review.** CodeRabbit's only pass
  covered the first commit; the request for a pass over the final design (posted on #22)
  was refused for rate limits again. Re-request it — this is a safety-critical merge gate
  running on a two-lens subagent panel and the author's own reads.
- The two H-severity entries in [`kit-friction-log.md`](kit-friction-log.md) (fallback
  independence; a receipt outliving the design it reviewed) are unfiled. Both now carry a
  proposed fix, so they are issue-shaped — `triage-friction-log` should graduate them rather
  than leaving them in the inbox.

✔ Done — shipped as PR #25 (see the Phase 3b block, swept into this file by the
2026-07-27 archive run). The design constraint held: neither surface's fix
touches `converged`.

### 2026-07-25

**Theme —** Assessed the kit against its own ten principles, then fixed what the
assessment found. Six PRs merged; tests 83 → 188. The recurring shape: **the kit had
written down rules it was itself violating.**

- **Adoption was broken at step one.** `init.sh` shipped mode `100644`, so the documented
  `./init.sh` failed for every adopter. Its narrative-doc seeding was dead code — the kit
  *ships* `docs/handoff.md`, so the "seed only if absent" guard was permanently false and
  everyone started with a `my-project` header and a `<tracker.url — stamped by init.sh>`
  line that `init.sh` never stamped. (#8)
- **An upgrade path now exists, and it was mostly already written.** `init.sh` already had
  `migrate_runtime_schema()`; it had never run anywhere, because `./init.sh` didn't work.
  Fixing the mode unblocked the mechanism. Added `kit.version`, template rendering keyed on
  an unrendered marker, hook installation as a shim (honoring `core.hooksPath`), and
  **probing** `paths.engines` rather than defaulting it. (#8)
- **Engines became kit-owned.** `scripts/lib/kitconfig.py` — a stdlib-only config reader,
  verified byte-equal to PyYAML on the shipped config and on two real adopter configs — let
  review-bot markers, CI policy, and the cron/CI exemption move *out* of the engines and
  into config. Every shipped engine is now dependency-free. That invariant is what makes an
  upgrade a file copy instead of a manual merge. (#8, #9, #16 — closed #5)
- **Four hardcoded-literal bugs fixed.** `pre-push` diffed against a hardcoded
  `origin/main`, so on any repo whose trunk isn't `main` the guard **silently never fired**;
  `pr-watch` could never converge on a repo with no CI; `JOB_NAME` was a Jenkins-ism that
  GitHub Actions never sets. (#9)
- **Claude-side wiring caught up with Codex-side.** All seven commands had no frontmatter,
  so their surfaced descriptions were raw first lines. Added `.claude/settings.json` with
  SessionStart budget hooks and a `PostToolUse` hook that mandates PR follow-through —
  ported from cs-toolkit, which had the better mechanism. (#13)
- **`kit_doctor` + `/upgrade`.** Per-file drift against a hashed manifest, plus the four
  installation checks nothing else performed. Run read-only against the real adopters it
  found `brain`'s live breakage (config `paths.engines` pointing at a directory with no
  engine in it) and `OpenKitchen`'s four drifted files. (#16, #17)

**Decided**

- Engines are kit-owned; config is adopter-owned. Everything else follows from it.
- `differs` never claims a *cause* — a hash mismatch can't distinguish "older version" from
  "hand-edited", and claiming the latter sends someone hunting for edits they never made.
- Re-running `./init.sh` is the supported config upgrade; `/upgrade` handles engines.

**Learned**

- **The kit predicted its own bugs and shipped them anyway.** `dev_session.sh` states "any
  doc that quotes [the lane contract] should quote it, not restate it" — and `parallel.md`'s
  kickoff prompt restated it and drifted from it.
- **I then resolved that drift toward the wrong source.** The kickoff said "mark ready when
  done", the lane contract said "leave it in draft", and I treated the contract as
  authoritative. It wasn't: `CLAUDE-sections.md` — the always-on baseline — says a finished
  PR must *never* sit in draft, because ready-for-review is what triggers the review bots.
  The lane contract was the outlier, and `pr_watch` proves it: `"PR is draft"` is a merge
  blocker, so a `self` merge-class lane obeying the contract could never satisfy
  `dev_session.sh merge`. The contract forbade the exact action its own merge class
  required. Corrected in #21: marking ready is the lane's, landing it is the cockpit's.
  **The lesson isn't "check for drift" — it's that finding two sources doesn't tell you
  which one is right, and I picked by proximity rather than by testing either against the
  baseline.**
- **A guard that fails open must be loud.** Three separate silent-no-op bugs this session
  (`origin/main`, the uninstalled hook, `paths.engines`). Silence is indistinguishable from
  "checked and clean".
- **Same bug class, both directions, one session.** `core.hooksPath` was fixed in `init.sh`
  (write side) and then reintroduced in `kit_doctor` (read side) hours later. See issue #15.
- **Queued ≠ unavailable.** A review receipt was recorded while CodeRabbit was merely
  queued, and its four valid findings landed after the merge. `decide_done` can't tell the
  two apart.

✔ Superseded by the Phase 3a session (PR #22). The proposed order (merge
gate → receipts behind a flag → wire the fixer → flip) was replaced: the flag existed to
defer a breakage caused by `done` conflating two predicates, so splitting them removed the
need for it.
