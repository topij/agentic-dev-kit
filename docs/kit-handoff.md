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

Last updated: 2026-08-03 — **Prose that is correct where it is written and false where it is
read.** Three adapters converted across two repos. Five separate defects this session were the
same shape, and it is not `#248`'s: not a restatement drifting from its owner, but a sentence
true in the repo that authored it and false in the repo that installs it. Docs that ship into
other repositories have a failure mode single-repo prose does not.

## Latest session — 2026-08-03 (three conversions, and a defect class that only exists in shipped docs)

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

______________________________________________________________________

## Earlier session — 2026-08-03 (the tracker gather, and a failure mode `#248` had not named)

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

______________________________________________________________________

## Earlier session — 2026-08-03 (the conversion proved itself, and the record kept outrunning the work)

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

______________________________________________________________________

## Earlier session — 2026-08-02 (Phase 2's blockers closed, and withdrawal beating repair)

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

