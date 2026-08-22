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

Last updated: 2026-08-22 — the overnight batch landed, the friction inbox graduated, and a panel that kept finding the narration wrong.

## Latest session — 2026-08-22 · overnight and morning (the batch landed, and a panel that kept finding the narration wrong)

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

- **Round 2 caught round 1's fix breaking a rule that had merged hours earlier.** The
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
  `#243`'s slice had no field test until now. Two deviations, both deliberate and disclosed
  in the marker: approval came in-session because the Slack MCP was unauthorized and no
  notify engine exists (`#573` asks whether that route should be sanctioned or the gate held
  absolute), and one entry was kept rather than swept because it parks for accumulation
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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

