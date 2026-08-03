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

Last updated: 2026-08-03 — **The first forked adapter is a pointer, and it earned its keep
immediately.** cs-toolkit's `/session-start` now reads the kit's shared workflow
(`in-parallel-oy/cs-toolkit@b33f2e90`), and its reviewer found a defect in *the kit's* text
that was fixed once, upstream, and returned byte-identical. That loop is what the shared
workflow exists for and could not happen while the adapter was a fork.

## Latest session — 2026-08-03 (the conversion proved itself, and the record kept outrunning the work)

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

## Earlier session — 2026-08-01 (the eighth sweep, configurable lens compute, and a panel that kept finding my own overclaims)

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

______________________________________________________________________

> Older session entries (below the live blocks above) live in [`kit-handoff-history.md`](kit-handoff-history.md).
> Active open items from them are folded into the "Open for next session" lists above.

______________________________________________________________________

