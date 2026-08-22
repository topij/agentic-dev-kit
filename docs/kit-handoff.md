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

Last updated: 2026-08-22 — the review process assessed, and a session that kept reproducing the defect class it was assessing.

## Latest session — 2026-08-22 · evening (the review process assessed, and a session that kept reproducing the defect class it was assessing)

**Theme —** A planning session on why PR review costs what it does. The assessment found a
gap nothing on the tracker held and filed it. Then, writing up the finding, this session
produced the same defect three times — a claim generalised from one observation — and each
was refuted by something cheap that no panel had to run.

- **The proportionality machinery all governs re-runs; the opening pass has none.**
  Blast-radius classes, the executed/record discriminator, the delta pass, logged
  dispositions — every one is scoped to what a *fix round* owes.
  `fallback-review-panel.md` then closes the other door explicitly: a PR's initial review
  takes the full panel, never a delta pass. So a wrap-up PR of pure record prose opens with
  the pass a merge-gate change opens with. Filed as `#585`, with the three holes it has to
  survive named rather than waved at. Distinct from `#209` (within a PR's re-run chain) and
  `#420` (across sibling PRs), both of which are about a pass after the first.

- **The reviewer selection is not a choice anyone is making badly.** The bot reviews when it
  can, the panel runs when it cannot, and `fallback_commands` is degraded mode for a runtime
  that cannot isolate a lens — which Claude Code can, so it never runs here. Combined with
  `#372`'s quota shape, the session's *second* PR reliably gets the panel, and a session's
  second PR is reliably its wrap-up. The most expensive review a normal session buys is the
  one on the content with the least to break.

- **Doctrine carries to adopters; the economics do not.** `fallback-review-panel.md`,
  `safety-critical-changes.md`, `pr-watch.md` and `wrap-up.md` are byte-identical between
  this repo and cs-toolkit's install, so a fix to `#585` arrives there on its next
  `/upgrade` with no separate assessment. Whether the gap *costs* anything there is a
  per-repo fact and is unmeasured.

- **A paid reviewer tier is still metered, and past the allowance the behaviour is a
  console setting.** `#372` now carries the readings: a stated allowance per hour, and an
  over-limit path that bills, pauses, or stops depending on the usage-based add-on's mode,
  with any mode refusing once the spending cap is reached. That narrows what option 3 *is*
  without choosing it — paying makes the refusal a setting rather than removing it.

- **`#491` showed up live three times in one session**, in three different contexts: a
  configured incremental skip reported identically to an outage on a PR that had just
  configured the skip; the same on a later head; and once alongside *valid* coverage, where
  it was harmless. Followed literally the first time, it prescribes a two-lens panel over a
  YAML config file. Recorded there — the failure is not fail-open, it is fail-expensive.

- **Executed prose has no deterministic checker at all.** `make lint` is `ruff` and nothing
  else; there is no prose tool anywhere in the tree. So the surface where findings actually
  concentrate is checked only by a stochastic reviewer. Filed as `#586`, scoped to executed
  prose and explicitly *not* to record accuracy — `#120`'s territory, which no lint can
  reach, because those are truth defects rather than clarity ones.

- **In cs-toolkit:** `#2076` merged (`c5a6897f`) adding that repo's first
  `.coderabbit.yaml`; `#2078` carries its handoff update. Following `wrap-up.md` there hit
  `#505`'s mechanism with a second file pair — the workflow names `check_doc_budget.py`
  unconditionally, that adopter declines it deliberately and says so, and a *downstream*
  instruction depending on its output was silently skipped while the wrap-up reported
  success. Recorded there, with a third direction that issue lacked: the workflow could
  consult the `remedy:` field it already reads.

- **Filed this session:** `#585`, `#586`. Occurrence comments on `#491` and `#505`, and on
  `#372` — where an earlier comment of this session's was corrected in place rather than
  answered with a second one.

- **Verified:** no kit code changed this session, so nothing here rests on the suite —
  though `make test` in `/Users/topi/Coding/agentic-dev-kit` on this branch at `0a06365`
  printed `1362 passed`, which says the tree was green at handoff and nothing more. The
  claims above were established by reading rather than by running. The byte-identity of the
  four doctrine files was checked with `shasum -a 256` over both trees from
  `/Users/topi/Coding/agentic-dev-kit`; the absence of a prose linter by reading the `lint:`
  target and grepping the Makefile, `.github/workflows/` and `scripts/` at `fabf554`; the
  engine defaults behind three "absent" adopter config keys by reading `pr_watch.py`'s
  module constants, which is what retracted them as findings.

**Learned**

- **Three claims this session were generalisations from one observation, and each was
  refuted by something cheaper than a review round.** No refusals in a PR sweep read as
  "there is no quota" — refuted by an allowance line already in the reviewer's own output.
  One `Charged:` receipt read as "it bills rather than refusing" — refuted by a vendor docs
  page. And an adopter's absent config keys read as gaps — retracted by the engine's own
  defaults. Each reading was accurate; the error each time was treating one reading of a
  *configurable* system as a property of it.

- **What caught them is the argument for `#585` and `#586` both.** An allowance line, a
  docs page, and a module constant — none of them a panel. The expensive reviewer is not
  the only thing capable of finding this class, and the cheap things that found it were
  already present and unread.

▶ Next: `#372` — take the posture decision. It gates how much `#585` and `#586` are worth:
if the reviewer covers every head, the opening-pass gap is latent rather than live. It now
carries the metered-tier readings, the over-limit mode table, and the adopter comparison it
was missing, and a further occurrence has nothing left to teach it.

______________________________________________________________________

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

______________________________________________________________________

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

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

