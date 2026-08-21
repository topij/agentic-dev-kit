# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most friction is filed directly as
> issues rather than parked here — which is the routing Principle #2 prescribes, not a
> neglected inbox. Anything that appears below a graduation marker is un-graduated: not yet
> issue-shaped, or waiting for the next `triage-friction-log` sweep.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues


## 2026-08-21

- **Two lenses launched together against one head can land against different heads, and
  the doctrine has no disposition for the stale one.** Severity **M**. Both lenses of a
  round were launched at the same sha; the adversarial one returned first, its finding was
  fixed and pushed, and the correctness lens then reported against the sha it had been
  given — by then the parent. Several of its findings were already closed. Nothing in
  `fallback-review-panel.md` says what a round means when its two reports describe
  different trees, so the cockpit decides ad hoc: I re-checked each finding against the
  current head and dispositioned per finding, which is right but is not written anywhere.
  Worse, the confirmations are the risky half — a lens can confirm a draw that a later
  commit has since falsified, and that reads as corroboration. Proposed fix: either hold
  every fix until a round's lenses have all reported (simple, costs latency), or require a
  delta report to state the head it reviewed and the cockpit to re-check each finding and
  each CONFIRMED draw against the current head before acting. The second is what happened
  here; the first is what the doctrine implies without saying.

## 2026-08-20

- **A figure was read off a workflow run that had not finished, and nothing in the reading
  said so.** Severity **H**. A CI-cost measurement used
  `gh api .../runs/<id>/jobs?per_page=100 --jq '.jobs[] | select(.conclusion != null) | ...'`
  while the run was still in flight. (The filter is inside the `.jobs[]` iteration — at the
  top level `.conclusion` is null on the wrapper object and `select` would emit nothing,
  which is a different and louder failure.) It silently dropped the three unfinished jobs —
  including the long pole —
  and the remaining subset was reported as the run's totals: job count, wall clock and
  runner-minutes all wrong, wall clock by roughly fourfold. It reached a commit message and
  a PR body before a review lens re-derived it. The shape is exactly what
  `settle_grace_minutes` exists for on the check rollup — a partial result is
  indistinguishable from a complete one by inspection — but nothing carries that lesson to
  the *runs* API, where the same agent hits it by hand. Proposed fix: a rule wherever the kit
  reads a run or a rollup — assert the container reports `completed` **before** reading any
  figure out of it, and treat a filter that drops rows as the thing that hides
  incompleteness rather than as tidying.

- **A delegated implementer stopped mid-task waiting for a background notification that no
  one had arranged.** Severity **M**. Told to run the verification command and report the
  result, the delegate backgrounded it, then ended its turn saying it would wait for a
  monitor notification before branching and committing — so the task notification arrived
  with no branch, no commit, and no verification, while its edits sat uncommitted on the
  protected branch. It completed correctly when told plainly to run the command in the
  foreground and not stop between steps. Proposed fix: delegation prompts for
  implement-and-push work should state that the agent owns its own verification synchronously
  and must not end its turn before the push, and should name branching as step one rather
  than a later step — the ordering is what left the edits on `main`.

- **A watch loop polled for a review by counting comments, so an acknowledgement that was
  edited into the review itself read as silence.** Severity **H**. A hand-rolled loop watched
  two PRs with `[.comments[]|select(.author.login=="coderabbitai")]|length`, breaking on a
  new review object or a *new* comment. On `#525` the bot posted an acknowledgement at
  `07:15:29Z` and then **updated that same comment in place** at `07:17:40Z` into a completed
  clean review naming its range and reporting zero units left. The count never changed, no
  review object was ever created, and the loop ran to its bound reporting nothing — so the
  session recorded "requested, acknowledged, never delivered" for a PR that had in fact been
  reviewed, and carried that into a wrap-up block and a ticket comment. The bot corrected it
  on `#372` before the block was committed; the correctness lens caught that the block had
  been written anyway. This is `#509`'s mutable-comment hazard with a specific new mechanism:
  **any freshness check keyed on comment count or on "is there a new comment" is blind to
  `updatedAt`.** Proposed fix: wherever the kit polls a bot's comment surface, compare
  `updatedAt` and not just presence or count — `pr_watch` reads bodies and so is insulated,
  which is precisely why a hand-rolled loop beside it is where this bites. Occurrence for
  `#509`; the detection consequence is `#44`'s.

- **A persisted `cd` sent a later read to the wrong repo, and the two-tree rule's remedy is
  written for writes.** Severity **M**. A `cd` into the second repo persisted across
  subsequent tool calls, so a later poll ran in the adopter rather than the kit; caught only
  because `pwd` was asserted before the next write. `AGENTS.md`'s two-tree rule prescribes
  exactly that assertion, so the rule worked — but it is stated for *writes*, and this was a
  read whose output was about to be used as evidence of the wrong repo's state. Proposed fix:
  extend the rule's remedy to any command whose *output* is used as evidence, not only writes;
  `#511` already reports the read-sequence half and this is a second occurrence of it.
  **And `pwd` is not sufficient on its own for a forge read** — `gh` resolves the repository
  from the working directory, so a correct `pwd` still leaves the target implicit. Bind the
  identity too: `scripts/reconcile_sessions.sh` already resolves `REPO_NWO` and exports
  `GH_REPO` before collecting evidence, which is the pattern to generalise. Passing `--repo`
  explicitly at the call site gives the same guarantee. `#246` is the occurrence behind this —
  filed on a forge *write* reaching the wrong repository; the cwd-resolution mechanism it
  describes is read/write-agnostic, which is why extending it to reads is proposed here rather
  than claimed as already covered.

- **A ruling comment transcribed the evidence trail's latest occurrence layer, and that
  layer was wrong.** Severity **H**. `#372`'s third ruling stated a detection mechanism and
  a timing figure read off the trail's most recent occurrence comment; both were already
  refuted by a correction sitting on the same trail, and both reached a doctrine PR before
  `#528`'s adversarial lens executed `bot_comment_verdicts()` against the live history and
  refuted them again. Proposed fix: a ruling that cites occurrences is written from the
  trail's *corrections*, not its occurrences — or states mechanisms only from evidence the
  author executed. The lens contract's "Execute, don't only read" already carries this for
  reviewers; nothing carries it for the record's author.

- **This morning's delegate-stall entry recurred with its proposed fix applied verbatim,
  and the fix did not bind.** Severity **M**. Two of three delegates backgrounded
  `make test` — which outruns the default tool timeout — and ended their turn to wait,
  with "run in the FOREGROUND, do not background, do not end your turn" verbatim in their
  briefs. Both complied after a follow-up message named a concrete 600000ms timeout for
  the command. The stall is timeout-shaped, not obedience-shaped: the default timeout
  forces the backgrounding, and no instruction overrides a mechanism (`#514`). Proposed
  fix: delegation briefs for verification-owning work name the timeout value for the long
  command up front — a parameter, not a plea.

- **`#510`'s `make test | tail` pattern reproduced by the cockpit, in the session that
  knows the ticket.** Severity **L**. `make test 2>&1 | tail -1` ran inside a `set -e`
  chain ahead of a `git push`: `tail` exits 0 whatever the suite did, so the push proceeds
  regardless. No harm — the printed summary line was read and green — but the guard was
  the reader, not the shell. Occurrence for `#510`; its fix (pipefail, or read the exit
  before piping) stands unchanged.

## 2026-08-19

- **A merge-gate predicate was used to answer a reportorial question, and the bias
  inverted.** Severity **H**. `#520`'s new `⚠ review owed` line read
  `qualifying_bot_coverage` to decide whether anyone had reviewed the head. That function
  under-reports *deliberately* — its own docstring keeps the bias in the safe direction —
  because it feeds a **gate**, where under-reporting refuses a merge and is harmless. Used
  in a **report**, the same bias asserts that nobody reviewed the diff. Both panel lenses
  found it independently, in distinct reachable states (a bot's `CHANGES_REQUESTED` on
  the head; a failed check read alongside a real `APPROVED` review). Proposed fix: a rule
  that a gate predicate and a report predicate are different functions even when they read
  the same field — the gate answers "may I merge on this", the report answers "what is
  true" — and that reusing one for the other inverts its safe direction. Candidate for
  doctrine rather than a ticket: the instance is already handled in `#520`, and the shape is what
  is worth keeping.

- **The panel ran from hand-written prompts after its first round, losing
  `panel_prompt.py`'s guarantees — including a diffstat it computes correctly.** Severity
  **M**. `panel_prompt.py` assembled the opening round; every round after it was hand-written, to carry
  round-specific framing (delta boundary, the author's stated draws) that the engine has
  flags for but that were easier to write inline. One consequence surfaced immediately: the
  round-2 prompt quoted a diffstat computed over the wrong range — the previous round's
  delta, labelled as the full base diff — which the adversarial lens recomputed, caught,
  and reported rather than trusting. Nothing was harmed, because **Right revision** exists
  for exactly this. But the failure is silent when the lens does not check, and the engine
  would not have made it. Proposed fix: use the flags that exist for this —
  `--carry-forward` for what prior rounds covered, and `--delta-draws`, delta-pass only,
  for the author's stated draws. They are not interchangeable: `panel_prompt.py --help`
  says carry-forward is "never the author's draws or risk assessment". Alternatively,
  have `panel_prompt.py` refuse a diffstat it did not compute itself.

- **`gh pr checks --json state` reports `IN_PROGRESS`, never `PENDING`.** Severity **L**. A
  watch loop breaking on `[ "$s" != "PENDING" ]` exits on its first poll and reads as
  "CI finished" — the plain `gh pr checks` text output says `pending`, so the JSON field's
  vocabulary is not the one the human-facing surface trains you to expect. Cost here was
  one wasted loop, caught because the printed check row contradicted the loop's own
  conclusion. Terminal states observed: `SUCCESS`, `FAILURE`, `ERROR`, `CANCELLED`.
  Proposed fix: worth a line wherever the kit documents polling `gh` directly, since
  `pr_watch.py` insulates you from it and therefore never teaches it.

## 2026-08-18 — Backlog migrated to GitHub Issues (#506–#515)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Fifteen
entries in, fifteen accounted for:** ten new issues
([#506](https://github.com/topij/agentic-dev-kit/issues/506)–[#515](https://github.com/topij/agentic-dev-kit/issues/515)),
one pair merged at filing (the `make test | tail` entry and the same-night zsh
`pipefail` correction, per the approved routing), and three occurrence comments on
already-open issues carrying the same mechanism —
[#372](https://github.com/topij/agentic-dev-kit/issues/372) (two data points),
[#467](https://github.com/topij/agentic-dev-kit/issues/467), and
[#435](https://github.com/topij/agentic-dev-kit/issues/435). All ten creates and all
three comments were re-read from the tracker after landing per `#138`.

**Approval.** The numbered proposal DM went to the operator in-session (channel
`D083840DP7B`, ts `1787045705.365309`, continued at `1787045712.981769`); the approval
arrived at 2026-08-18 13:17:40 EEST — "lgtm" — the grammar's bulk approve; nothing was
declined. This block is the committed approval record `#128` asks the interactive path
to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 17,439 bytes, sha256
`5912a487eb7bdbff28ae0b3df3c361fb7a3943aae5339d54ec13c927fc47032b`, reproducing from
`git show 5645899:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The working
tree was byte-identical to `5645899`'s copy at sweep time, verified by recomputing
this digest from the file being swept immediately before the rewrite, so every block
swept with nothing held back and no window-added entries existed.

Swept entries are verbatim in the archive under `Graduated 2026-08-18`.
