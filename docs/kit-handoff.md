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

Last updated: 2026-08-03 — **The fix was right in round one; everything that failed review was
the evidence written around it.** A silent tracker truncation the operator hit in cs-toolkit is
closed in both places it lived in the kit — and the durable result is what the review rounds
found instead: not drifted restatements, but mechanisms asserted without being tested, stated
beside verified claims at the same confidence.

## Latest session — 2026-08-03 (the tracker gather, and a failure mode `#248` had not named)

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

## Earlier session — 2026-08-02 (the doctrine split, the assembler that reads it, and where review yield actually comes from)

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

______________________________________________________________________

## Earlier session — 2026-08-01 (two blocker fixes merged, and a guard withdrawn on the evidence)

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

