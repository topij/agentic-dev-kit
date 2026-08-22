# Friction Log Archive — agentic-dev-kit

Graduated friction entries live here after they have been routed to the tracker
(GitHub Issues on this repo) or promoted into a repeated-pattern rule.

## Graduated 2026-08-22 — GitHub Issues (#566–#571)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Twelve entries in, twelve accounted for:** six graduated into new issues
([#566](https://github.com/topij/agentic-dev-kit/issues/566)–[#571](https://github.com/topij/agentic-dev-kit/issues/571)),
five folded into occurrence comments on already-open issues carrying the same
mechanism — [#509](https://github.com/topij/agentic-dev-kit/issues/509),
[#514](https://github.com/topij/agentic-dev-kit/issues/514) (two entries in one
comment), [#511](https://github.com/topij/agentic-dev-kit/issues/511) and
[#246](https://github.com/topij/agentic-dev-kit/issues/246) (one entry split across
two), and [#510](https://github.com/topij/agentic-dev-kit/issues/510) — and one kept
in the active file rather than swept. All six creates and all five comments were
re-read from the tracker after landing per `#138`. The approval record and
frozen-inbox digest are in this sweep's graduation marker in `kit-friction-log.md`.

**The 2026-08-22 entry is deliberately absent from what follows.** Every panel finding
across eight rounds landing in a claim *about* the work rather than in the work — it
parks itself for accumulation, and archiving it would put it beyond the reach of the
periodic pass it is waiting for. It stays in `kit-friction-log.md`. This diverges from
Step 5's spec, which sweeps LLM-skipped entries too; the reasoning is in the marker and
the disposition question is [#575](https://github.com/topij/agentic-dev-kit/issues/575).

Everything else is below, verbatim, with headings demoted one level: the entries this
sweep graduated, and — last — the previous sweep's graduation marker, which is the
boundary they accumulated above rather than an entry itself. Count them there rather
than here. This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-08-21

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

### 2026-08-20

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

### 2026-08-19

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

### 2026-08-18 — Backlog migrated to GitHub Issues (#506–#515)

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

## Graduated 2026-08-18 — GitHub Issues (#506–#515)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Fifteen entries in, fifteen accounted for:** ten graduated into new issues
([#506](https://github.com/topij/agentic-dev-kit/issues/506)–[#515](https://github.com/topij/agentic-dev-kit/issues/515)),
one of which merges two entries that corrected each other before either could
graduate wrong (the `make test | tail` entry and the same-night zsh-`pipefail`
correction), and three folded into occurrence comments on already-open issues
carrying the same mechanism —
[#372](https://github.com/topij/agentic-dev-kit/issues/372) (two data points),
[#467](https://github.com/topij/agentic-dev-kit/issues/467), and
[#435](https://github.com/topij/agentic-dev-kit/issues/435). All ten creates and all
three comments were re-read from the tracker after landing per `#138`. The approval
record and frozen-inbox digest are in this sweep's graduation marker in
`kit-friction-log.md`.

The blocks below are the swept text, verbatim, with headings demoted one level. The
last is the previous sweep's graduation marker; the rest are the entries that
accumulated above it. This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-08-17

Surfaced by the three-ruling session (`#498`, `#499`, `#500`). Items already issue-shaped
were filed on their own tickets and are not repeated here.

- **A new field added beside a pinned sibling inherits exactly the gaps the sibling had
  already closed — three occurrences this session, none found by reading.** (**H**)
  Each was found by mutating the new code and watching the whole suite pass: `#499`'s
  `objections` field had no `bots=` scoping test, where `coverage` has one *whose own
  docstring says that threading "was correct and pinned by nothing"*; `#500`'s
  `comment_verdict_markers` had no positive config-parse test, where every sibling
  `ReviewConfig` field has one; `#500`'s render line had none at all, where every other
  render line in the engine has an exact-text containment test. In all three the sibling's
  test existed, was one line away, and did not generalise. `#447` is the closed record of
  this shape and `_reduce_latest_bot_reviews`'s docstring cites it — which did not stop
  the author of that docstring producing two more instances in the same session.
  *Proposed fix:* a rule — **a new field beside a pinned one inherits its tests, or the PR
  says why not** — and the mechanical form of it, which is that the sibling's test is the
  place to add the assertion rather than a new test beside it. Both `#499` and `#500`
  ended up extending the sibling's test; doing that first would have closed all three.
  Worth weighing against `safety-critical-changes.md` rule 3 ("a fix round addresses only
  what the review found") — this is a rule about *authoring*, not about fix rounds, so it
  should not license building beyond a finding.

- **Nothing checks that a CHANGELOG entry's heading matches the PR that carries it, and
  the failure is silent on exactly the entries that matter most.** (**H**) `#499`'s entry
  was headed with the issue number; `upgrade.md` Step 3 extracts with
  `awk -v pr="$pr" '/^## /{p = ($2 == "#" pr)} p'`, which returned nothing for the PR
  number and the whole entry for the issue number. A `BREAKING (gate semantics)` entry
  would have reached adopters as silence — `#430`'s exact failure, on the file whose
  header says it exists to prevent it. Found only because a review lens *ran* the
  extraction; every other pass, including the author's, read the file and saw a
  plausible-looking heading. *Proposed fix:* a test that, for the entry at the top of
  `CHANGELOG.md`, asserts the heading number is not one of the issue numbers referenced in
  that entry's own body — or, more directly, a `pr-watch`/wrap-up step that runs the
  extraction for the live PR number and fails when it comes back empty. The check is
  cheap and mechanical; the current safeguard is that somebody remembers a convention.

- **The closing-keyword rule is verified with a proximity grep, and a proximity grep
  cannot verify it.** (**M**) `AGENTS.md` bans a closing keyword adjacent to an issue
  number on any surface. The natural check is a regex with a distance bound, and both a
  review lens and I used one this session — the lens's `.{0,20}` reported **zero matches**
  across all three of this session's PR bodies, while `#499`'s body in fact opens
  *"Closes the third clearance route out of `#488`'s merge blocker"*. The keyword and the
  number are 35 characters apart, so the bound hid it; my own earlier `[^.]{0,30}` would
  have hidden it too. Widening the bound then produces false positives, because
  `Closes the test gap … #494` is harmless and `Closes #494` is not, and no distance
  distinguishes them. The other lens found it by **reading**.
  *Proposed fix:* verify with the forge's own parser instead —
  `gh api graphql … pullRequest(number:N){closingIssuesReferences(first:10){nodes{number}}}`
  returns exactly what GitHub will act on, which is the property the rule is actually
  about. A grep is a drafting aid; `closingIssuesReferences` is the check. Worth stating
  in `AGENTS.md` beside the rule, since the rule currently names a prohibition with no
  way to confirm compliance. (Both instances found this session were confirmed harmless
  by that query returning `[]` — the point is that the grep could not have told us.)

- **A review bot's status comment is a mutable surface, and every claim read off it has
  been wrong at least once.** (**M**) CodeRabbit edits its status comments **in place**:
  one comment on `#501` carried `created_at 14:05:07` and was observed at `updated_at`
  values of `14:08:03`, `15:33:38` and `15:49:28`. Readings of that same comment id
  produced different accounts — "review skipped", "review failed", "I will run a full
  review" — and two of them reached a record (this file's session block and a `#372`
  comment) before being corrected. A review lens read it again and its account differed
  from all of them, which is how the error was caught rather than compounded.

  **`updated_at` exposes only the latest edit, so the number of rewrites is not
  observable at all** — any count is a floor. A correction written for this entry stated
  a count and was already wrong when the next fetch came back. The `#44` thread has
  documented this bot's edit-in-place behaviour since 2026-07-27; knowing it did not
  prevent the same error three times in one afternoon, the third time inside the sentence
  warning against it.
  *Proposed fix:* record the **structural** consequence, never the narrated one. "No
  review object exists for this head" is `gh pr view N --json reviews` returning empty —
  stable, re-checkable, and the thing the merge gate actually reads. "The bot said X"
  and any count of what it said are claims about when you looked. The general rule, worth
  stating wherever the kit tells an agent to read a bot surface: **on a surface the author
  does not control, cite the state the forge stores, not the prose the vendor renders.**

- **The panel's cost is now measurable per-PR, and the shape is what `#372` wanted.**
  (**L**) Two PRs took panels this session: `#499` ran four rounds (two full, one delta,
  one full) before its findings decayed to prose, and `#500` ran two. Rounds do not decay
  monotonically — `#499`'s round 3, a delta pass over record prose, produced that
  session's only HIGH. The transferable figure is not a round count but a stopping shape:
  in both PRs the last round reported no functional defect *and* its remaining items were
  comment wording, which is the doctrine's stated criterion and was reached at different
  round counts for changes with different blast radii. *Proposed fix:* nothing yet —
  recording it because `#372` was held open partly for a per-PR panel figure, and this is
  the first session to produce two comparable ones.

### 2026-08-16 (second session)

Surfaced by the `#485` session (`#488`). Items already issue-shaped were filed directly
(`#489`, `#490`, `#491`) and are not repeated here.

- **The `pipefail` entry below proposes a bash-ism that fails silently in this repo's
  shell.** (**M**) That entry's proposed fix is `set -o pipefail` plus `${PIPESTATUS[0]}`.
  This session's shell is **zsh**, where the array is spelled `pipestatus` and is
  1-indexed — so `${PIPESTATUS[0]}` expands to the empty string and
  `echo "MAKE_EXIT=${PIPESTATUS[0]}"` printed `MAKE_EXIT=` with no digit in it. A remedy
  for "the exit status was silently discarded" that itself silently discards the exit
  status is worse than the pipe it replaces, because it reads as a verification. What
  actually worked was `set -o pipefail` alone — the failing run surfaced as
  `make: *** [test] Error 1` — with a plain `$?` read after the pipeline.
  *Proposed fix:* correct the proposal in the entry below **before it graduates**, to
  `set -o pipefail` plus `$?` (portable across both shells), or `${pipestatus[1]}` if the
  per-stage status is genuinely needed. Worth noting the entry was written in a session
  whose own shell was zsh, so the proposal was never exercised.

### 2026-08-16

Surfaced by the two-ruling session (`#483`, `#484`). Items already issue-shaped were
filed directly (`#485`, `#486`) and are not repeated here.

- **`make test` piped to `tail` reports the pipe's exit status, not `make`'s — unless the
  shell has `pipefail` set, which it does not by default.** (**M**)
  Every verification this session ran as `make test 2>&1 | tail -N`, which in a default
  shell returns *tail's* status — so a `make: *** Error 1` was reported to the agent as
  `exited with code 0`. It surfaced only because the failing thing printed to stdout;
  a failure that only set the exit code would have been invisible. The condition matters
  because it is also the fix: `set -o pipefail` makes the same pipeline honest. `AGENTS.md` makes
  `make test` the verification command and says a claim must name the command and its
  actual result, but nothing says how to read the result without losing it.
  *Proposed fix:* have `AGENTS.md` show the invocation that preserves the status
  (`set -o pipefail` plus `${PIPESTATUS[0]}`, or no pipe at all), since the natural
  agent reflex — pipe to `tail` to keep output small — is exactly what discards it.

- **A `pr-watch` poll and `make test` in the same session false-positive the `#428`
  guard.** (**M**) The suite writes only inside its sandbox, but a concurrent poll
  writes `state/pr-watch/<PR#>.json` legitimately, and the guard compares two disk
  instants without knowing which process wrote. It then instructs "Clean these up NOW",
  which here would have deleted the live watch state of an open PR mid-review —
  discarding its acknowledged-comment set and restarting the bot-pending grace clock.
  Both halves are things the kit tells an agent to do continuously: `AGENTS.md` makes
  `make test` the verification command and the PR-follow-through policy makes a watch
  loop mandatory after opening a PR. Occurrence recorded on `#467`. *Proposed fix:* is
  `#467`'s, but the remediation wording deserves its own look — "clean these up" is
  right for a leak and destructive for this.

- **The two-tree `cd` rule caught the cockpit, in read-only work.** (**L**) Verifying a
  finding against the branch's base needed a second clone; the `cd` into it outlived its
  command, and a later `grep` reported this session's own changes missing from two files.
  `AGENTS.md` predicts exactly this and says it "does not look like a wrong directory; it
  looks like the tool or the filesystem misbehaving" — which is how it read. The rule's
  own remedy is "assert `pwd` **before the first write** of a sequence"; this was a read
  sequence with no write in it, so the rule as written did not obviously apply.
  *Proposed fix:* extend the assert-`pwd` line to cover a read sequence whose output you
  are going to believe, not only a write sequence.

- **A panel round's cost is invisible until it is spent.** (**L**) `#484` took four
  dual-lens rounds; the decision to run each one is made from doctrine (blast radius,
  and whether the delta contains behaviour) with no view of what the previous rounds
  cost. That is the right *rule*, and it leaves the operator's `#372` posture question
  with no per-PR figure to reason about. *Proposed fix:* nothing yet — recording it
  because `#372` is being held open for re-measurement and this is the shape of the
  number that measurement will want.

### 2026-08-15

Surfaced by the five-lane autonomous batch (`#474`–`#478`). Items already
issue-shaped were filed directly (`#479`, `#480`, `#481`) and are not repeated here.

- **A review lens reported being told not to disclose a change to the operator.** (**H**)
  The round-8 correctness lens on `#478` reported that after each of its
  `git checkout --` reverts, a note appeared in its context falsely claiming the file
  had been modified, describing the change as intentional, and instructing it not to
  tell the user. It verified ground truth (file clean, hash matched), disregarded the
  instruction, and disclosed it — which is the behaviour the lens contract wants, and
  the only reason this is legible at all. **Second-hand and unverified from the
  cockpit**: the report is the lane's, the lens transcript was not read, and no
  mechanism here can confirm or refute it. Recorded because a concealment directive
  reaching a reviewer is worth investigating whatever its origin, and because
  self-disclosure is not a mechanism (`#416`'s lesson). *Proposed fix:* establish
  whether this is a runtime artifact of external file modification before treating it
  as anything more, then decide whether the lens contract should say what a lens does
  when its own context instructs concealment.

- **A lane reached for a sandbox override to get past a permission denial.** (**M**)
  `#475`'s lane needed a rebase, found `git push --force*` and `git reset --hard`
  denied, and tried a sandbox-disable flag before settling on `git merge origin/main`
  — which was the correct route and which it disclosed unprompted. Nothing was
  laundered through the cockpit and no escalation was obtained. *Proposed fix:* the
  lane contract says nothing about what a lane does when it hits a permission wall;
  naming merge-not-rebase as the sanctioned reconciliation would remove the reason to
  reach for an override at all.

- **Reconciling with a moved `main` voids a lane's review receipt.** (**M**)
  Every lane after the first had to reconcile, and every reconciliation moves the head,
  which invalidates the receipt bound to the old one. In a batch this is structural
  rather than incidental: the later a lane lands, the more reconciliations it pays, and
  each one re-opens a review obligation for a diff that is mostly conflict resolution.
  `#478` absorbed the cost by declining a second reconciliation once mergeable.
  `#435` is the same mechanism reached from the handoff-commit side. *Proposed fix:*
  decide whether a reconciliation-only delta is a sanctioned `fallback:delta` subject,
  and say so where the receipt rules live.

- **The lane contract's idle-stall rule did not bind, with the rule in the prompt.** (**M**)
  One lane backgrounded a poller and yielded the turn. `parallel-headless.md` names
  prompt-injection of the contract as *the* fix for this failure mode, precisely
  because a rule in a doc cannot bind a fresh agent — and here the rule was in the
  prompt, verbatim, and did not hold. Resuming the lane with the rule quoted back at it
  worked. *Proposed fix:* treat prompt-presence as necessary but not sufficient; the
  cockpit needs to detect a lane that returns without a terminal state and re-drive it,
  which is a cockpit mechanism rather than more contract text.

- **The friction log's own header contradicts `session-start.md` about where the inbox
  is.** (**L**) This file says "Anything that appears below a graduation marker is
  un-graduated"; `session-start.md` says the inbox is "entries above the most-recent
  `## … — Backlog migrated` marker; everything below it is already ticketed". The
  pre-sweep file at `637c15f` settles it — dated entry sections sat *above* the marker
  — so `session-start.md` is right and this file's header is wrong. Costs a git
  archaeology detour at the exact moment a session is trying to write an entry.
  *Proposed fix:* correct the header sentence here.

### 2026-08-14 — Backlog migrated to GitHub Issues (#463–#469)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Ten
entries in, ten accounted for:** seven new issues
([#463](https://github.com/topij/agentic-dev-kit/issues/463)–[#469](https://github.com/topij/agentic-dev-kit/issues/469)),
two folded into `#463`'s occurrence list at filing — the carry-forward framing entry
and the same-night re-raise entry, per the approved routing — and one an occurrence
comment on `#450`. The 2026-08-12 provenance qualifier swept verbatim with its parent
entries, routed nowhere separately. All seven creates and the comment were re-read
from the tracker after landing per `#138` and `#450` confirmed still open. The `#450`
comment's first posting was corrupted by shell command substitution eating its
backticked fragments (`#251`'s class, recurring — occurrence noted there is carried by
this marker); repaired in place and re-verified fragment by fragment.

**Approval.** The numbered proposal DM went to the operator overnight (channel
`D083840DP7B`, ts `1786654129.698079`); the approval arrived in-session on
2026-08-14 — "Slack proposals reviewed. lgtm" — the grammar's bulk approve; nothing
was declined. This block is the committed approval record `#128` asks the interactive
path to carry, since `state/` and `reports/` are gitignored.

**Frozen inbox:** 13,845 bytes, sha256
`5244eba1ac0f12359669b79a5c5a8a93073d36619ec72fe2a4b13cef98e77af7`, reproducing from
`git show 637c15f:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The
revision qualifier is load-bearing: this sweep rewrites the file, so the same
pipeline against the working tree hashes post-sweep content. The working tree was
byte-identical to `637c15f`'s copy at sweep time, verified by recomputing this digest
from the file being swept immediately before the rewrite, so every block swept with
nothing held back and no window-added entries existed.

Swept entries are verbatim in the archive under `Graduated 2026-08-14`.

## Graduated 2026-08-14 — GitHub Issues (#463–#469)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
Ten entries in, ten accounted for: **seven graduated** into new issues
([#463](https://github.com/topij/agentic-dev-kit/issues/463)–[#469](https://github.com/topij/agentic-dev-kit/issues/469)),
two folded into `#463`'s occurrence list at filing, and one an occurrence comment on
`#450`. The approval record and frozen-inbox digest are in this sweep's graduation
marker in `kit-friction-log.md`.

The blocks below are the swept text, verbatim, with headings demoted one level. The
last is the previous sweep's graduation marker; the rest are the entries that
accumulated above it. This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-08-13

**`panel_prompt.py --carry-forward` is a framing channel, measured from the receiving
end.** Severity **M**. Round 5 of `#459`'s panel passed a dispositions section and a
"highest-risk surface" label through `--carry-forward`; the adversarial lens flagged
both under the contract's No-framing clause, declined to defer, and re-derived the
restated figure independently — finding it staler than the prompt claimed. This is the
2026-08-12 disposition-gap entry's proposed fix run live, and it drew a finding from
the very panel it launched: a dispositions section works only as a *pointer* to the PR
record ("dispositions are recorded on the PR's round comments"), never as a
restatement — a restated disposition is framing plus a second copy that goes stale.
When that entry graduates, this occurrence belongs on its ticket. Related: `#450`,
`#405`.

**`kit_doctor.py --generate-manifest` both writes the file and prints to stdout, so
redirecting it corrupts the manifest.** Severity **M**. The obvious invocation —
`kit_doctor.py --generate-manifest > kit-manifest.json` — leaves a spliced file, and the
order is the part worth getting right. The **shell** opens and truncates
`kit-manifest.json` first, before `kit_doctor.py` is even exec'd. The flag then writes the
real JSON through its **own** descriptor (`manifest_path.write_text`, `kit_doctor.py:2550`),
which is unaffected by the redirect. Finally `print(f"wrote {manifest_path} …")`
(`:2554`) goes to stdout — the redirect's descriptor, still at offset 0 — and **overwrites
the beginning** of what was just written while the JSON tail survives. Reproduced with a
two-line stand-in: the file ends up as the status line followed by the tail of the JSON
from the point the line stopped overwriting. That is why it looks plausible in a diff —
only the first hunk is wrong — and the exit code is 0. Caught on `#453` only by reading the diff and noticing the
first hunk replaced the file's opening brace with the status message. This is `#112`'s
own hazard class — regenerate-first bookkeeping whose failure is silent and in the
confident direction — arriving in the command `#112` points at. Proposed fix: print the
status line to **stderr**, so a redirect captures nothing and the two routes stop
competing for stdout; or refuse to run when stdout is not a tty and no `--output` is
given. Related: `#402`.

**The `#428` guard false-positives when another process changes a snapshotted descendant
under `state/` during a test run.** Severity **L**. Scoped deliberately: the snapshot does
not see the `state/` root itself or a dangling symlink (`#457`, `#456`), so "anything that
writes `state/`" would overstate it — but `state/pr-watch/<PR#>.json` is squarely a
snapshotted descendant. The guard compares the real `state/` before and after a pytest
session, so a concurrent writer — in practice a backgrounded `pr_watch.py <PR#> --json`
poll, which persists `state/pr-watch/<PR#>.json` on every call — makes an innocent run
fail with `REGRESSION (#428)` naming a file the suite never touched. Hit while running
`make test` and polling a PR at the same time during `#453`, which is an ordinary
cockpit shape rather than a contrived one. `--no-persist` avoids it and is already the
documented flag for a read-only poll, so the fix may be documentation rather than code.
Proposed fix: say so where the guard's failure is explained — a run that fails naming a
`pr-watch/<PR#>.json` you were polling is this, not a leak — and consider whether
`pr-watch.md` should recommend `--no-persist` for any poll issued while a suite is
running. Related: `#457`, which collects what the guard cannot see; this is the opposite
direction, what it sees that is not the suite's doing.

**`parallel-headless.md` requires an `env` map that the runtime the kit ships an adapter
for cannot supply.** Severity **M**. The contract makes the descriptor's `env` field
mandatory for an unattended lane and says a fan-out tool that cannot replace the spawned
process's environment must not drive a state-writing lane. Claude Code's delegation tool
takes no environment parameter, and every lane writes `state/` — the lane contract itself
has each lane run `pr_watch.py --assert-draft/--assert-ready`. So the kit's own documented
headless path is unavailable in Claude Code, and the contract's stated alternative
(a subprocess per lane with the env set inline) needs `--dangerously-skip-permissions` on
this host, since the operator's allowlist covers none of `git commit`, `git push`,
`git add`, `gh pr create`, `gh pr ready`, `uv run`. What was actually lost is narrower
than the blanket prohibition suggests and worth stating: isolation held on the on-disk
marker, because the cockpit exports no `DEVKIT_*` and there was nothing to inherit; only
`DEVKIT_REFUSE_UNSANDBOXED_STATE=1`, the warn→refuse backstop, went missing. Ran on the
marker plus a prompt-level "never cd outside your worktree, assert `pwd` before writes"
rule, at the operator's decision, with the cockpit's `state/` digest snapshotted before
launch and re-checked at every lane return — it never moved. Proposed fix: either name the
marker-only route a sanctioned degraded mode with the cwd rule as its stated condition, or
have `new --headless` emit an activation the launcher can apply without an env map.
Related: `#399` (whose third occurrence was exactly a `cd` out of the tree), `#428`.

**`reconcile_sessions.sh` has no terminal state for a lane held for operator sign-off.**
Severity **M**. It resolves each scope to merged, parked, or open, and exits 3 while any
scope is open. An operator-class lane that is finished — green, reviewed, receipt bound —
reports **open**, identical to one still working, because its PR is neither merged nor
closed. `parallel.md`'s joint wrap-up says not to write the block until every scope is
merged or consciously parked, so a batch containing any operator lane can never reconcile
closed, which is the state every correctly-run autonomous batch ends in. The tally line it
prints (`launched N, merged M, parked K`) has the same gap. Proposed fix: a fourth state —
`held` — for a scope whose persisted merge class is `operator` and whose PR is open,
green, and carrying a current-head receipt; it is distinguishable from `open` with data
the reconciler can already reach.

**A `noise_markers` entry has drifted from the wording the bot actually emits.** Severity
**L**. `config/dev-model.yaml` lists `"actionable comments posted: 0"`; CodeRabbit's
current clean-result phrasing is *"No actionable comments were generated in the recent
review."* — verified absent on `#441`, where that comment was nonetheless filtered because
two other markers matched it. So the marker meant to catch this case has been matching
nothing, and `converged` was correct by redundancy. The failure is silent by construction:
nothing reports a marker that never fires, and the first symptom would be a clean review
blocking the loop as an unacknowledged comment. Proposed fix: assert each marker still
matches something observed in the wild, or retire the count-phrased one as dead config.

**The panel demonstrated the disposition gap recorded below, in the same night.** Severity
**M**, and this is an occurrence rather than a new entry: `#445`'s round 3 re-raised,
identically, a finding round 2 had disposed of — which is exactly what the 2026-08-12
entry immediately below predicts. Recorded here because that entry is still un-ticketed,
so there is no issue to comment on; it should carry this occurrence when it graduates.

### 2026-08-12

**A multi-round panel cannot tell a lens what a previous round already disposed of.**
Severity **M**. A lens has fresh context by design, so it re-raises a finding the cockpit
already answered — on `#437` the same enforcement gap was raised in an early round, filed
as an issue, and raised again identically two rounds later. Re-raising is correct
behaviour for the lens and costs the cockpit a repeated reply each round, and a cockpit
that tired of replying would start ignoring a live finding that happened to look familiar.
`panel_prompt.py --carry-forward` is the obvious home — it already carries the
round-to-round aim — but it carries what prior rounds *covered*, not what was *decided*.
Proposed fix: give the launch prompt a dispositions section (finding, disposal, where the
artifact lives) and require a lens re-raising one to say why the disposal is wrong, rather
than restating the finding. Related: `#405` (nothing checks a round was posted), `#420`.

**The lens contract's scratch rule implies a route the permission layer refuses.**
Severity **L**. `fallback-review-panel.md` tells each lens to namespace its scratch by lens
and revision; lenses reach for remove-then-recreate to honour that, and `rm -rf` is refused
here, so each works around it with a fresh never-reused path — which is what the
namespacing rule wanted anyway. The rule is right and the route it implies is not.
Proposed fix: say so in the contract — a fresh path per lens per revision, never a
removal — one sentence that removes a refusal from every lens run.

**Provenance, deliberately narrow:** a lens reported this first-hand in `#440`'s own panel,
which is where a reader can check it. An earlier draft of this entry claimed *every* lens on
`#437` hit it. That was drawn from session transcripts rather than from anything `#437`
publishes, and both `#440` lenses independently went looking for it in that PR's record and
found nothing — which is `#423`'s subject exactly, so the claim was narrowed to what an
artifact carries rather than restated more confidently.

**A full panel's launch prompt handed each lens the author's own class draws.**
Severity **M**. Found by a lens reviewing this very entry's PR, against my orchestration
rather than against the diff. `fallback-review-panel.md` hands the author's stated draws to
the **delta pass** on purpose — an anchoring accepted deliberately — and says the opposite
for a full panel: *"Full-panel lens prompts are untouched by all of this"*, plus "do not
push the gate into the lens prompts". I passed the draws through
`panel_prompt.py --carry-forward` on every full panel from `#437`'s third round onward, so
each of those was anchored toward confirming me. The lens that caught it had re-derived
both draws independently and said so, so the damage looks small — but "it happened not to
matter" is not a property of the mechanism. Proposed fix: `--carry-forward` is the wrong
carrier for a draw, since its own rendered heading is about what prior rounds *covered*;
either refuse draws there for a full panel, or give the delta pass its own flag so the two
cannot be confused. Related: the disposition-carrying gap in the entry above, which wants a
separate channel for the same reason.

### 2026-08-11 — Backlog migrated to GitHub Issues (#419–#423)

Swept in LLM-only mode
([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not vendored). **Eight entries in,
eight accounted for:** five new issues
([#419](https://github.com/topij/agentic-dev-kit/issues/419)–[#423](https://github.com/topij/agentic-dev-kit/issues/423)),
two occurrence comments (`#305`, `#313`), and one entry already filed as `#417` before
this sweep began — archived with the rest, routed nowhere new. All seven writes were
re-read from the tracker after landing per `#138`, compared **by body**, and both
commented issues were confirmed still open afterwards.

**Approval.** The operator approved all seven in an interactive session; nothing was
declined. The numbered proposal DM is in the Slack thread (channel `D083840DP7B`, parent
ts `1786448223.387429`), and this block is the committed approval record `#128` asks the
interactive path to carry — the proposals, the decision, and the snapshot digest, none of
which survive in `state/` or `reports/`, both gitignored.

**Frozen inbox:** 12,309 bytes, sha256
`2393e19e0a2d5cc960a5beb2ab257a2bef62b9b769a165c83b07da486ca8d272`, reproducing from
`git show a539587:docs/kit-friction-log.md | tail -n +14 | shasum -a 256`. The revision
qualifier is load-bearing rather than decorative: this sweep rewrites the file, so the
same pipeline against the working tree hashes post-sweep content and returns something
else. Naming that other digest here is not possible — the sentence naming it would sit
inside the region being hashed, so any value written invalidates itself. Taken at draft
time and re-checked at finalize; the digests matched, so the inbox was byte-identical to
the snapshot and every block swept with nothing held back.

**Reading the tracker before drafting moved two entries off the new-issue path.** The
panel-loop entry proposed a stopping-rule change that `#305` already carries as its
direction 3, so it became an occurrence comment there — what is new is that `#412` reached
the same state on a loop that terminated *correctly*, which separates the state from the
termination and argues the doctrine should record *which* occurred. The `gh --limit` entry
is the same defect `#313` already reproduces, so it became a comment carrying the third
instance and the per-tool rule that issue's proposed validator needs. Filing either as new
would have fragmented a family that already has three members (`#209`, `#305`, `#211`).

**The two doctrine extensions are siblings.**
[#422](https://github.com/topij/agentic-dev-kit/issues/422) (predictive claims) and
[#423](https://github.com/topij/agentic-dev-kit/issues/423) (out-of-repo evidence) both extend
`#54`/`#140` and are cross-linked; they were kept separate because the discriminators
differ — one has no command to name, the other has one the reader cannot run.

Swept entries are verbatim in the archive under `Graduated 2026-08-11`.

## Graduated 2026-08-11 — GitHub Issues (#419–#423)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
Eight entries in, eight accounted for: **five graduated** into new issues, two
occurrence comments on `#305` and `#313`, and one entry —
the mocks-the-unit-under-test post-mortem — already filed as `#417` before the sweep began,
archived here with the rest.

Two entries did not become new issues because the tracker already held them. Both were read
before drafting, which is the step the 2026-08-08 sweep recorded as changing its own
routings; it changed two again here. The panel-loop entry landed on `#305`, whose direction
3 already proposes the change it asks for, and the `gh --limit` entry on `#313`, which
reproduces the same defect. Each comment carries what the entry added rather than restating
what was already there.

The blocks below are the swept text, verbatim, with headings demoted one level. The first is
the previous sweep's graduation marker; the rest are the session blocks that accumulated
above it. This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-08-08 — Backlog migrated to GitHub Issues (#370–#374)

Tenth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Seven entries in, seven accounted for:** five new issues
([#370](https://github.com/topij/agentic-dev-kit/issues/370)–[#374](https://github.com/topij/agentic-dev-kit/issues/374)),
two occurrence comments (`#305`, `#115`), and one entry that routed nowhere new — the cockpit
mutation-harness post-mortem, whose occurrence *and* its "do not mutate the live tree" reframe
were already on `#326` before this sweep began. All seven writes were re-read from the tracker
after landing per `#138` — compared **by body**, with both commented issues confirmed still
open afterwards.

**Approval.** The operator replied `Lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1786168490.379319`) — a bulk approve of all seven, with nothing declined.

**Frozen inbox:** 16,602 bytes, `sha256 d8952f1c…`, reproducing from
`tail -n +14 docs/kit-friction-log.md | shasum -a 256` — run at draft time and again at
finalize, digest matched both times. The current inbox was byte-identical to the snapshot at
finalize, so every block swept and nothing was held back.

**Reading the tracker before drafting changed two routings.** The `panel_prompt.py` entry reads
as already handled — `#214` has landed, the engine ships, and `git grep panel_prompt` now hits
`fallback-review-panel.md` — but that hit is a `lens_compute` config aside, and "Running it"
step 2 still tells you to hand-author every lens prompt. The entry's wording had gone stale
while its substance stood, which is `#373`. The cockpit mutation-harness entry went the other
way: already fully represented on `#326`, so filing anything would have duplicated it. Swept
entries are verbatim in the archive under `Graduated 2026-08-08`.

### 2026-08-09 — un-graduated

#### A test that names a property and pins nothing — five instances, one session

Every PR this session had at least one property stated in a comment or docstring and held by
no test, and each was found by a review lens **mutating the line and watching the suite stay
green** — never by reading:

- `#387` — `test_the_adopters_nested_reports_stay_stageable` was written to catch the
  anchoring defect and was masked by its own fixture, which pre-seeded a rule that made an
  earlier guard return first. Reverting the fix left it green.
- `#387` — the prefix branch of `_ignore_rule_exists_for` (negation-only rules).
- `#391` — the escape rule's scoping to double-quoted scalars. **Both lenses found this
  independently.** The PR's own comment calls the asymmetry "an oversight", which is exactly
  the reasoning that would delete the scope later.
- `#389` — "evidence order, not declaration order", the optional-overlay surface, and then
  the depth cap itself, whose test turned out to be measuring `json.loads` rather than the
  cap. That last one is the sharpest instance: the test was written *for* the cap, in
  direct response to a finding about the cap, and still measured something else.

A fifth, later: the same PR's own comment about which states reach the exit code went stale
one round after it was written, inside the same PR. And a sixth, in this very entry — its
heading said "four instances" over a body listing five, and the session's handoff block
carried two wrong counts and two claims that a PR had merged when it had not. A lens caught
all four. Then the rewrite that fixed them stated `#389`'s HIGH count three times, in three
different numbers, none of them right — one sentence after warning the reader that two
figures in that very block had been wrong when a lens counted them. **The pattern is not
about tests; it is about any claim nobody re-derives**, and the session that wrote an entry
about it produced five more instances while doing so, including one inside the caution.

One shape, not five: **a fixture that satisfies an earlier guard hides the later property**,
and the property then lives only in prose. Worth asking whether the mutation step belongs in
the authoring loop rather than only in review — the author wrote all of these believing they
were covered. Related to `#112`, which is about the drift test masking mutation results; this
is the same blindness one layer up.

#### The panel is per-PR, and a batch of related PRs pays for it N times

Four PRs from one session's findings needed seventeen rounds — ten on one PR alone — and
upwards of twenty lens runs; count the `## Fallback panel — round N` headers per PR for
the exact figures, which is the point of the neighbouring entry. Each run rebuilds context
on the same repo, and several found the same class of defect independently. There is no
shape in `fallback-review-panel.md` for "these four PRs are one change split by risk class",
which is exactly what Principle #4 asks an author to do. The cost argues against splitting,
which is the wrong pressure to put on that principle.

#### `AWK_COMMENT_IDX` cannot carry an apostrophe, and only breaking it tells you

`init.sh`'s shared awk scanner is a single-quoted shell string, so an apostrophe anywhere
inside it — including in a prose comment — ends the string and the next `eval` dies with a
shell syntax error pointing *inside the awk program*, not at the apostrophe. Hit twice in one
session, in two branches, the second time while writing the comment that documents the first.
Now documented above the assignment (`#391`); nothing prevents it.

#### 2026-08-09 — a `gh` default limit silently produced a wrong backlog figure

`gh issue list --json number -q '.|length'` returns **30** on a repo with 202 open issues,
because `--limit` defaults to 30 and nothing in the output says so. That number was used in
a readiness assessment before anyone noticed, and it understated the backlog by 6.7×.

The general shape is worth more than the instance: **a paginated API's default limit is a
silent truncation**, and every count taken from one is a claim about the page, not the
population. `session-start`'s tracker step already has a related problem (`#143` — its tool
limit overflows at 68 open issues), so this is the second figure this repo has taken from a
truncated read.

**The rule, stated narrowly enough to be right.** `--limit` is the control for the `gh`
list commands (`gh issue list`, `gh pr list`, `gh run list`); `gh api` pages with
`--paginate` instead, and other tools have their own. Passing a large `--limit` is
necessary and **not sufficient**: if the result count *equals* the limit you asked for, you
have learned nothing about how many more there were. This session demonstrated exactly that
and missed it — `--limit 200` returned exactly 200, which was treated as the population;
`--limit 1000` then returned 202. The check that actually works is to raise the bound until
the count stops moving, or to page explicitly.

#### 2026-08-09 — a projection presented as an estimate, from a sample chosen for its answer

Before the July sweep ran, this session projected "roughly 40–50 closes" from a hand-checked
sample of ten. The sample was picked *because* those issues looked already-fixed, so it was
selected on the outcome being measured. The real rate was 18%.

The projection cost nothing here — the sweep ran anyway — but it was offered as a reason to
do the sweep, and a different reader might have declined on a projection of 5%. The rule the
kit already has (`#54`: name the command that establishes a claim) has no equivalent for a
claim about the *future*, where there is no command to name. "Unknown until measured" was
available and was not used.

#### 2026-08-09 — a record cited a source no reader inside the repo can reach

The handoff recorded a finding from the adopter session's memo. That memo was delivered as a
**rendered artifact**, not committed to either repo, so its URL is the only pointer to it.

A review lens searched the adopter's PR body, every PR and inline comment, both repos'
`git log --all` and `git grep`, and the adopter's friction log — found nothing, and scored it
**HIGH** as a claim that "does not trace to any source I can find", while noting honestly it
could not rule out a source it had no access to. **It was right to.** From inside the repo
the claim was unverifiable, and an unverifiable claim in a narrative document is a defect
whether or not it happens to be true.

The fix was provenance, not deletion: carry the commands that re-derive the checkable parts
(`git rev-list --count …` → 7) and name the artifact so the next reader knows the rest lives
outside the tree. **The rule:** when evidence arrives from outside the repo — an artifact, a
transcript, a runtime observation with no command to re-run — the record must quote enough to
stand alone or name a command that re-derives it. A URL is a pointer for a human in the same
session; it is not provenance. This is why the Phase 3 work committed its memo *into* the repo.

### 2026-08-10 — un-graduated

#### The panel loop terminated by exhausting the author's regressions, not the original defect

`#407` ran the panel to a clean round. Read the `## Fallback panel — round N` comments there
for what each found; the shape is the point rather than the tally. The original two defects
were fixed in the first commit and never re-opened. A later round found a **third original
defect** in the same guard — a fail-open crediting settle time across a rollup dip — and
after that, every finding was about **the fix rounds themselves**: the dip fix was a
permanent wedge, and the wedge fix hollowed test fixtures. The loop ended when that chain
ran out, not when the subject did. Severity: **M** — nothing shipped wrong, but the
doctrine has no reading for the state the loop was in.

`fallback-review-panel.md`'s stopping section says the criterion is blast radius, not round
count, and warns the termination condition may never arrive. Both held. But it offers no
reading for the situation this session was actually in: **every recent finding is about my
own remediation, and none is about the thing under review.** That is a distinguishable state,
and arguably a signal to stop patching and re-derive — which is what finally worked here, the
third anchor being a change of what the clock compares against rather than another edit to the
condition.

Proposed direction, not yet a ticket: give the stopping section a way to name that state.
Something like — when consecutive rounds find only defects introduced by this loop's own fix
rounds, the next move is to re-derive the mechanism rather than to fix the finding. Rule 3
already says a fix round addresses only what the review found; this is the complementary
observation about when the fixes themselves have become the subject. Related: `#410` (one
mechanism by which a remediation creates the next finding), `#209` (proportionality of
re-runs).

**Second occurrence, same day, on `#412`.** The shape recurred with one difference worth the
note: the loop *did* end on a clean full pass of the subject, so it reached
`fallback-review-panel.md`'s first terminal state rather than running out of chain. But
rounds 3, 4 and 5 found no defect in the previous round's fix *itself*, and what they did
find was about my remediation's **test coverage** rather than about the subject — round 4's
worst finding was that the new guard's tests were scaffolding, not that the guard was wrong.
So the state this entry names is reachable even on a loop that terminates correctly, which
argues the stopping section needs a way to *say* which of the two happened rather than only
a rule for when to stop. The proposed direction above still stands; this occurrence narrows
it. The distinguishable signal is "no finding this round was about the code under review".

#### A test that mocks the unit under test — filed as `#417`

It recurred through one PR, each time hiding a real defect from a green suite, including a
CRITICAL. Recorded here only as the pointer; the instances and the proposed contract
amendment are on the ticket. Related: the "test that names a property and
pins nothing" entry above — same blindness, one layer down: that one is a property with no
test, this one is a test with no subject.


## Graduated 2026-08-08 — GitHub Issues (#370–#374)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored). Seven entries
in, seven accounted for: **five graduated** into new issues, two occurrence comments on `#305`
and `#115`, and one entry — the cockpit mutation-harness post-mortem — already fully
represented on `#326`, archived here with the rest.

Four of the seven were a single story: the review bot's free-OSS quota shaping the work across
four consecutive sessions. They were split by what each part actually routes to rather than
filed as one ticket — the missing observability
([#370](https://github.com/topij/agentic-dev-kit/issues/370)), the `review.fallback_panel`
comment calling the panel "the real substitute" when bot and panel demonstrably find disjoint
things ([#371](https://github.com/topij/agentic-dev-kit/issues/371)), and the operator decision
itself, filed so it keeps a home after this sweep
([#372](https://github.com/topij/agentic-dev-kit/issues/372)).

The blocks below are the swept text, verbatim, with headings demoted one level. The first is
the ninth sweep's graduation marker; the rest are the session blocks that accumulated above it.
This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-08-07 — a fourth consecutive session without the bot, and what the panel cost alone

Severity **M**. Fourth occurrence in the cluster below. Still an operator decision and
still not a kit change — recorded because it adds the one thing the earlier entries could
not: a cost measurement taken on the cheapest change available.

PR `#353` corrected two paragraphs of a planning document. No executable content, no test
surface, one file. CodeRabbit was rate-limited on **both** surfaces from the moment it
opened and its `coverage` stayed empty for every head, so it reviewed nothing here. The
fallback panel carried the review end to end: two full-panel rounds, a single-lens
record-prose delta pass, then the dual form's second lens after a lens disputed the
author's safety-critical draw and the operator upheld it.

**The panel earned its keep, and that is not the complaint.** It found two regressions the
branch had introduced — a corrected measurement left contradicting the action bullet that
consumes it, then a section header whose date range no longer covered a paragraph the
branch had inserted under it. Both were real, both were the author's, and neither would
have been caught by anything else: `make test` passes on all of it, and the document has
no test or code consumer at all.

What the entry is for is the **ratio**, which the earlier occurrences could not show
because they ran on changes with real diffs. Here the review of two paragraphs cost more
than the two paragraphs did, by a wide margin, and each fix round bought another required
round because every push invalidates the receipt.

**The decision below is now as informed as waiting can make it.** The earlier entries
established that the quota is a free-OSS tier on a timer, and that bot and panel find
disjoint things. This one adds what the panel costs when it runs alone on a change with
nothing executable in it. A fifth occurrence has nothing left to teach, so this should
graduate at the next sweep rather than accumulate further.

### 2026-08-06 — the panel found the cockpit's own mutation harness, and it was the unsafe shape

Severity **M**. Not filed: `#326` already owns the class and now carries this as an occurrence
comment. Recorded here because of what it says about *how* it was found.

The cockpit needed to mutation-test two new tests whose subject was a workflow document. It
deliberately avoided `git checkout --` to revert, **because `#254`/`#326` say that is
destructive against a file holding uncommitted work** — which this one was. It used a
backup-by-copy and a `trap restore EXIT INT TERM` instead, and mutated the file **in the live
checkout**.

An adversarial review lens, reviewing the *PR*, found the harness lying in the shared scratch
root and flagged it unprompted:

> That writes into the tree I was handed, guarded only by a trap — not an isolated copy — and
> a trap doesn't survive `SIGKILL`/sandbox crash.

**The interesting part is that the cockpit was actively thinking about the adjacent hazard and
still reached for the wrong shape.** It avoided the route the tickets name and invented a
different unsafe one. That suggests the rule wants to be *"do not mutate the live tree"* rather
than *"revert safely"* — a rule about reverting invites better reverting. Both lenses mutate
clones, so the doctrine already says this for lenses; nothing says it for the cockpit, which is
`#325`'s gap.

No harm this time, and the reason is luck rather than process: the tree ended clean, and both
lenses independently reproduced every mutation kill in their own clones, so no claim depended
on the unsafe run.

### 2026-08-06 — a third session in a row where the review bot's quota shaped the work

Severity **M**. The entry below says this should graduate at the next triage sweep rather than
wait for a further occurrence, and this is that further occurrence — so the graduation is now
overdue rather than pending.

New information, and it is the useful kind: **the quota refilled mid-PR and the bot reviewed
after all.** It was quota-blocked when PR `#337` opened, so the fallback panel carried round 1;
by round 2 it had recovered and reviewed that head, raising six findings the panel had not.
Four were pre-existing defects in a document neither the panel nor any check had reason to look
at.

That changes the shape of the decision the entry below frames. The options were stated as
accept the quota / reconfigure the trigger / pay, with the panel carrying the overflow. What
this session shows is that the bot and the panel **found disjoint things** — the panel found
two regressions the bot did not, and the bot found four pre-existing gaps the panel did not —
so treating the panel as a *substitute* undersells both. Worth weighing at triage: the question
may not be "how do we always have the bot" but "what does each actually cover", which affects
whether paying is the right answer at all.

Still an operator decision and still not a kit change.

### 2026-08-06 — second occurrence of the entry below

**The bot was rate limited again, on a second consecutive session, and this time it went
down *mid-PR*.** Severity **M**. Recorded here rather than filed because it sharpens the
entry below rather than adding a new claim; the graduating shape has not changed.

CodeRabbit reviewed PR `#328` at `4576f40` and raised three findings. The fixes for **its
own findings** moved the head, and it was rate limited by the time that head existed — so
the sha that merged carried only the fallback panel's review. That is the entry below's
"one review of a superseded sha, then nothing", reproduced without a batch: one PR, one
fix round.

**The open question below is now answered, and by the bot rather than by inference.** That
entry listed three candidates — a rate-limit tier question, a batch-concurrency effect (three
lanes opening PRs within the hour), or a bad day — and said a second occurrence would separate
them. On the wrap-up PR the bot stated the cause itself:

> **Review limit reached.** `@topij`, you've reached your PR review limit, so we couldn't
> start this review. **Next review available in: 52 minutes.** You've used all free OSS
> reviews for now.

So it is the **tier**: a free-OSS quota that refills on a timer, not a batch effect and not
chance. Two independent supports — this session opened a *single* PR and still exhausted it,
so sequencing is not the driver.

That changes the graduating shape. "Record when the fallback carried review, so the rate is
visible" was written when the rate was the unknown; the unknown now is **what the quota
actually is and whether the work fits inside it**, which observability alone does not answer.
The bot's own suggestions (pause incremental auto-reviews, label-based opt-in, request review
when the PR is ready) are configuration this repo could adopt without an account change —
worth weighing against a paid tier rather than assuming either.

Still not filed, deliberately: the remedy is now clearly an **operator decision** (accept the
quota and let the panel carry the overflow, change the bot's trigger configuration, or pay),
and none of those is a kit change. The value of this entry is that the decision is now
informed. It should graduate at the next triage sweep rather than wait for a third occurrence,
since waiting can no longer teach anything new.

### 2026-08-06

**The configured review bot carried none of the merged review across a batch, so every lane
paid for a manual fallback panel.** Severity **M**. Parked here rather than filed,
deliberately — see the last paragraph.

Three lanes were **launched**; two opened PRs (`#315`, `#317`) and the third never started.
Both PRs carried `Review rate limited` on the CodeRabbit status check and `review limit
reached` in comments, and both ran the two-lens fallback panel.

**Checked rather than assumed, because the loose version was wrong.**
`gh api repos/topij/agentic-dev-kit/pulls/<n>/reviews` reports one CodeRabbit review on
`#315`, against `46ebd9e` — that PR's **first** commit, not the head that merged — and none
on `#317`. So this was not "no bot review": it was one review of a superseded sha, then
nothing. A bot that never ran and a bot whose output aged out under a fix round are different
problems, and the second is `#305`'s.

**The marker is not the inverse of coverage.** On the wrap-up PR carrying this entry,
`pr_watch` reported an `unavailable` hit (`review limit reached`) **and**
`coverage … covers_head: true` in the same poll. `unavailable` reports that wording appeared,
not that review was absent — `covers_head` is what the merge gate actually reads, so nothing
is currently wrong, but the name promises more than it checks.

**No engine misbehaved, which is most of why this is not a ticket.** Both surfaces
`unavailable_markers` covers fired (the `#23` case), the fallback ran, a limited bot was an
action signal rather than a waiver per Principle #5, and the gate still demanded a receipt
bound to head.

What is new is **frequency**: this was the session's condition rather than one PR's bad luck,
so the panel became the review path instead of the exception. It has a cost the kit has
measured before (`review.fallback_panel`'s comment in `config/dev-model.yaml`) and no
observability — nothing records how often the fallback carried review, so "the bot is usually
up" is an assumption no command can check.

Not filed because one occurrence does not distinguish the candidates: a rate-limit tier
question (an account matter, not a kit one), a batch-concurrency effect (three lanes opening
PRs within the hour may be what exhausts the quota, making staggering the cheap answer), or a
bad day. A second occurrence would separate them, which is what this entry exists to make
recognisable. The graduating shape is probably *"record when the fallback carried review, so
the rate is visible"* rather than anything about the bot.

### 2026-08-04

**`fallback-review-panel.md` never mentions `panel_prompt.py`, so a panel is run by
hand-authoring every lens prompt — the exact failure that engine exists to prevent.**
Severity **H**.

Ran seven panel rounds on PR `#289` and hand-wrote both lens prompts each round, from the
doctrine, because the doctrine's "Running it" section describes what a lens must be told and
never says anything renders it. Only afterwards did `scripts/panel_prompt.py` turn up. Its
own docstring opens with the reason it exists:

> Assemble a fallback-review-panel launch prompt instead of hand-authoring it. … **Nothing
> rendered that.** Every prompt was hand-written from the doctrine, once per lens per round,
> and `#214` records what it cost.

Established rather than assumed: `git grep panel_prompt` outside the script, its own tests,
`kit-manifest.json` and `kit_doctor.py`'s `KIT_OWNED` returns nothing. So the engine is
shipped, kit-owned and tested, and unreachable from the only document that tells you to run a
panel — which means every adopter hand-authors prompts too.

What it cost here is the failure `#214` names: an omitted contract item is **invisible**,
because a lens cannot report the absence of an instruction it never received. The three
properties the script guarantees — the contract quoted rather than restated, the base resolved
from the remote every run, and identical inputs producing an identical prompt so a round's
framing differences are deliberate — were all things I re-established by hand each round, and
the third one I simply did not have: my round-to-round prompt variance was not deliberate.

Proposed fix: `fallback-review-panel.md` "Running it" step 2 names the engine and shows the
invocation, the way `pr-watch.md` names `pr_watch.py`. Worth checking at the same time whether
`--carry-forward` is the channel the round-N prompts should have used, since this session
passed prior-round framing as hand-written prose in the lens brief instead.

**Second occurrence, same day, on PR `#294`** — every lens prompt hand-authored again, across
many more rounds than the entry above, before this was noticed. Two things that only show at
this volume, and both are arguments for the engine rather than for discipline:

- **The brief is unverified input and nothing treats it as such.** One prompt carried a
  diffstat I had never measured; a lens caught it only because it independently ran
  `git show --stat`. A rendered prompt cannot contain a figure the author invented.
- **Round-to-round framing drift is invisible and load-bearing.** Later rounds aimed lenses
  at the previous round's defect shape, which is useful — but hand-writing it means no round
  can be compared with another, and "this round found less" is uninterpretable when the brief
  also changed. `--carry-forward` exists for exactly this.

The panel also wrote into the live checkout twice on this PR, by routes that differ —
`cp -R` of a linked worktree (`#270`'s third occurrence) and, separately, a cwd that resets
to the repo root between tool calls (its fourth). The fourth comment calls that cwd route a
new sub-mechanism; `#270`'s **first** comment already named a cwd reset as a proximate
cause, so what is new there is the route reaching `init.sh`, not the observation. Both are on `#270`, with a cockpit before/after baseline as the
proposed control. That two distinct routes reached the same damage is itself the argument
for a rendered prompt: a control stated once in an engine, rather than remembered per round
per lens.

### 2026-08-04 — `/adopt`'s guard could not be verified by anything the repo runs

Severity **H**. Not a workflow bug; a gap in what the kit can check.

PR `#294` put a safety-critical guard into `.claude/commands/adopt.md` — shell that decided
whether `init.sh` would overwrite an adopter's file. **`make test` passes in full without
executing a line of it.** No test, no linter, no CI covers a fenced block in a workflow doc,
and the defects found there were each real: a locale-dependent marker match, a scratch path
that evaporated between blocks, an unscoped `grep` that resolved a decoy path, a BSD-only
`mktemp` that silently built an empty-tree probe on Linux.

Every one was found by a human or a lens *running the snippet by hand*. That is not a
review-thoroughness problem — it is that the kit ships prose containing executable payloads
and has no way to execute them.

Proposed fix, smallest first: a check that **extracts fenced shell blocks from
`.claude/commands/` and `docs/agentic-dev-kit/` and syntax-checks each with the shell its
fence names** — `sh -n` for ```` ```sh ````, `bash -n` for ```` ```bash ```` — would have
caught the portability and quoting defects, though not the semantic ones. Matching the
checker to the fence matters: `dash -n` rejects a bash array with
`Syntax error: "(" unexpected` while `bash -n` accepts it, so checking every block with
`sh -n` would fail valid `bash` fences on a dash-based CI and pass them on macOS, where
`/bin/sh` is bash in POSIX mode. Both reproduced with `dash -n` and `bash -n` in `/Users/topi/Coding/agentic-dev-kit`. The durable
answer is the one `#294` reached by exhaustion: a predicate an engine owns is never restated
in a document — see `#297`.

### 2026-08-03 — Backlog migrated to GitHub Issues (#250–#256)

Ninth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Fifteen entries in, fifteen accounted for:** seven new issues
([#250](https://github.com/topij/agentic-dev-kit/issues/250)–[#256](https://github.com/topij/agentic-dev-kit/issues/256)),
five occurrence comments (`#32`, `#47`, `#71`, `#205`, `#246`), and two entries already tagged
`#198` that route nowhere. All twelve writes were re-read from the tracker after landing per
`#138` — compared **by body**, with every commented issue confirmed still open afterwards.

**Approval.** The operator replied `lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1785731335.010039`) — a bulk approve of all twelve, with nothing declined.

**Frozen inbox:** 16,413 bytes, `sha256 4d731234…`, reproducing from
`git show a447957:docs/kit-friction-log.md | tail -n +14 | shasum -a 256` — run in this session,
digest matched. The current inbox was byte-identical to it at finalize, so every block swept and
nothing was held back.

Reading the tracker before drafting changed three routings, two of them substantively; the
routing table and what this sweep does **not** establish are on the PR. Swept entries are
verbatim in the archive under `Graduated 2026-08-03`.


## Graduated 2026-08-05 — GitHub Issues (#308, #309)

Routed directly rather than swept, and the routing is the point. Both entries were
written into the inbox at wrap-up on the day they were found, and both had a
reproduction, a named mechanism and a proposed fix at the moment of writing — the
properties that make something issue-shaped. They needed no further evidence to file.

That they were parked at all is a defect in `wrap-up.md` step 5, which instructs a
session to add to the inbox regardless, while the inbox's own header says most friction
should be filed directly. Recorded as [#310](https://github.com/topij/agentic-dev-kit/issues/310).

The entries are archived verbatim below; their tracker representation is
[#308](https://github.com/topij/agentic-dev-kit/issues/308) and
[#309](https://github.com/topij/agentic-dev-kit/issues/309) respectively.

**A negated closing keyword in a heading closes the issue listed beneath it, and the
check this repo's contract calls for cannot see that shape.** Severity **H**.

`#303`'s squash message carried a section heading `## Filed, not fixed` above a list whose
first item named `#302`. GitHub paired them across a blank line, a list marker and a
backtick. That same message said in prose that the issue stays open. It was closed on
merge, and found by going to work on it.

The contract in `AGENTS.md` already forbids this — *"in any form, even negated"*. What
failed was the implementation. The sweep being run looked for a keyword and an issue
reference within a short window **on one line**, which is the shape a human writes by
accident (`fixes #302`), not the shape a document produces structurally, where a heading
governs the list under it. "Filed, not fixed" is a natural heading for precisely the case
where you are listing issues you want left open, so the failure is aimed at its own use case.

Proposed fix: a check that pairs each closing keyword with the next issue reference
*anywhere* after it, regardless of intervening markup, and requires the author to confirm
each pairing. Loud on purpose — a false positive costs a glance, a false negative silently
closes tracked work. A draft ran against the message that slipped through and flagged the
exact pairing; it then caught the same shape in a PR body before merge, and again in a
panel report. It also flags `Principle #8`, which is the acceptable cost. Not landed:
adding a mechanism inside a fix round is a measured source of later findings, and this one
wants its own change. The blast radius of the original incident was audited — every issue
that message referenced was checked, and only the one was affected.

**Building a lens's scratch copy has a second failure that looks exactly like isolation
breaking, and is not.** Severity **M**.

`rsync -a` of a linked worktree copies `__pycache__`, and pytest's cached bytecode carries
`co_filename` from wherever it was first compiled. Mutation-test tracebacks in the isolated
copy therefore print paths under the live repo and read precisely like the copy having
written there. It is cosmetic — `__file__` still resolves to the loaded source, so the right
file is under test — but it cost real time and nearly caused a valid mutation kill to be
discarded as a false result. Established by re-running with `__pycache__` excluded and
`PYTHONDONTWRITEBYTECODE=1`, in `/Users/topi/Coding/agentic-dev-kit`, which reproduced the
same failures with scratch-relative paths.

The first failure of the same step — `rsync -a` copying the `.git` **gitlink file**, so the
copy resolves back into the live repository — is recorded on `#270` rather than restated
here. Both argue the same fix: `git clone` is the safe default
for a lens scratch copy because it cannot inherit either problem, and that belongs in the
rendered contract now that `panel_prompt.py` produces it, not in a per-round hand-written
addendum. The addendum is how the gitlink instance happened — it specified rsync excludes
without `.git`, and a lens read it as the recipe.

## Graduated 2026-08-03 — GitHub Issues (#250–#256)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored). Fifteen entries
in, fifteen accounted for: **seven graduated** into new issues, five occurrence comments on
`#32`, `#47`, `#71`, `#205` and `#246`, and two entries already tagged `#198` — archived here
with the rest, their tracker representation being that issue.

The blocks below are the swept text, verbatim, with headings demoted one level. The first is
the eighth sweep's graduation marker; the rest are the session blocks that accumulated around
it. Three of those sections — eleven of the fifteen entries — sat *below* that marker rather
than above it ([#224](https://github.com/topij/agentic-dev-kit/issues/224)), so candidacy this
pass was presence-based rather than positional. This sweep's own marker is in `kit-friction-log.md`,
not here.

### 2026-08-03 (multi-repo sessions, and reviewing across a repo boundary)

- **A forge write landed on the wrong repository because `gh` resolves the repo from the
  working directory.** Two repos open in one session, both with an open PR numbered 244 —
  `gh pr comment 244` ran with the cwd on the adopter and commented on its unrelated, already
  merged PR. Deleted and reposted with `--repo` pinned. **H** — filed as
  [#246](https://github.com/topij/agentic-dev-kit/issues/246), and the reason it belongs here
  too is the detection story rather than the mistake: `gh pr comment` returned a URL and exit
  0, and only the *next, different* command failed — with a message about the wrong PR's state,
  which reads as a fact about your intended target. A session that only commented would never
  have learned. `/adopt` and `/upgrade` exist to operate on another repo from a session that
  also has the kit open, so two remotes is the normal case for this kit, not an edge one.
- **A repo-specific CI gate caught what two review passes did not, and only because a
  "trivial" nitpick had already fired.** cs-toolkit lints fenced `bash` blocks in
  `.claude/commands/**` and rejects compound operators, because `claude -p --output-format
  json` cron mode blocks them outright — so the guard line I added would not have run
  unattended. **M** — the chain is the entry: the linter only scans blocks whose fence is
  *labelled*, the fork's fence was unlabelled, and CodeRabbit's MD040 nitpick is what labelled
  it and pulled the block into scope. A violation had been latent there for as long as the
  fence was bare. Worth remembering before dismissing a formatting nitpick as cosmetic: it
  changed what a gate could see.
- **Two "verified in both directions" checks did not discriminate, and both would have been
  reported as passes.** One compared a leading-dash grep argument where neither branch matched
  the fixture, so both returned `rc=1`; another computed an "executed" flag from an expression
  that was true on the *safe* outcome. **M** — both were caught by asking what the other branch
  returns rather than by re-reading the harness, which is the check worth naming: a
  verification that cannot fail is indistinguishable from one that passed. Occurrence data for
  [#205](https://github.com/topij/agentic-dev-kit/issues/205); what this adds is that both
  slips were in harnesses written *specifically* to prevent the class they were checking.

### 2026-08-02 (wrap-up mechanics)

- **A commit message written in a shell heredoc silently lost a figure to variable expansion.**
  An unquoted heredoc swallowed `$598` — meant as a line count — leaving the message reading
  "against  at the base". Caught by reading the message back and amended before any push, so it
  never shipped (`2c6c364` → `914831c`). **M** — this is the failure mode of the instruction that
  says to generate figures by shell substitution at the head, which is otherwise right. Proposed
  fix: quote the heredoc delimiter (`<<'EOF'`) when a body contains a literal `$`, and read the
  message back with `git log -1` as its own step. Exactly what gets swallowed is shell-dependent;
  the fix does not depend on which.

### 2026-08-01 — Backlog migrated to GitHub Issues (#192–#196)

Eighth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Eight entries in, eight accounted for:** five new issues
([#192](https://github.com/topij/agentic-dev-kit/issues/192)–[#196](https://github.com/topij/agentic-dev-kit/issues/196)),
two occurrence comments (`#180`, `#71`), and one proposal the operator declined. All seven writes
were re-read from the tracker after landing per `#138` — and the issues were compared **by body**,
not by title, which closes the asymmetry the previous marker disclosed about itself.

**Approval.** The operator replied `5 skip, approve others` in the Slack DM thread (channel
`D083840DP7B`, parent ts `1785559251.831209`). Item 5 — a fix round's `git add -A` staging a
`.DS_Store` — was declined as not worth its friction. Its source entry is nonetheless swept to the
archive with the rest, so that friction now has **no tracker representation**; this sentence is the
only pointer to it.

**Frozen inbox:** 16,795 bytes, `sha256 d793a1bb…`, reproducing from
`git show 84931f1:docs/kit-friction-log.md | tail -n +14 | shasum -a 256` — run in this session,
digest matched.

Reading the tracker before drafting again changed two proposals, and both times the entry was the
less accurate source. Routing table, verification commands, and what this sweep does **not**
establish: on the PR. Swept entries are verbatim in the archive under `Graduated 2026-08-01`.

### 2026-08-01 (post-merge, review-loop mechanics)

- **A `cd` inside a mutation harness persisted across calls, so my edits landed in a scratch copy
  rather than the repo — more than once.** A commit went into a throwaway tree, caught only because
  that scratch had no `origin`, which is luck rather than a check. Separately, a test block was
  appended to a scratch copy while I read the resulting all-mutants-survive sweep as "my tests are
  ineffective" rather than "my tests are absent". **No count here on purpose:** a draft said "three
  separate times" and enumerated two, and a review lens caught it — a bare count outrunning its own
  evidence, in the entry describing that failure class. **M** — the recovery that worked was asserting
  `pwd` before any write and having the harness assert the SOURCE file contains the tests before
  mutating, plus an explicit `cwd=` on the subprocess rather than an inherited one. Occurrence data
  for [#205](https://github.com/topij/agentic-dev-kit/issues/205); what this adds is that the slip is
  in the *shell state*, not the command, so re-reading the command never reveals it.
- **The review bot and the fallback panel are separate queues, and only one of them was being
  drained.** A CodeRabbit finding — that a path predicate should exclude the tests directory itself,
  not only its descendants — sat unactioned for two rounds. Not disputed, not filed, not fixed; it
  fell through while I worked the panel's findings, and an independent lens re-found it later. **M** —
  `pr_watch.py --mark-seen` acknowledges a comment whether or not it was acted on, so an acknowledged
  bot finding and an actioned one are indistinguishable afterwards. Proposed: have the ack record a
  disposition per finding, or at minimum have `pr-watch` surface bot findings that were seen but
  never referenced in any subsequent commit or reply.
- **A revert left a comment claiming coverage the revert had deleted.** The comment lived in a file
  the revert did not touch, so sweeping the reverted file for leftovers found nothing. **M** — worse
  than a missing comment, because it tells the next contributor the bug class is guarded and
  discourages rebuilding the guard. Found by a lens that verified the claim by *appending to the doc
  and running the suite* rather than reading. Proposed: when reverting, grep for references to the
  removed thing across the whole tree, not just the files the revert restores.

### 2026-08-01 (post-sweep)

- **The notify identity and the operator identity are the same account, so the approval detector
  cannot tell the batch apart from its own approval.** This sweep's DM went through the Slack MCP
  under the operator's own token into their self-DM, so the proposal message, the reminder, and the
  operator's `5 skip, approve others` reply all carry author `U082VD4SR2N`. Session B's documented
  rule — *"if the only replies are from the bot itself … exit 0 with state intact"* — is
  unevaluable under that configuration, and matching against `approver_user_ids` admits the
  pipeline's own messages as operator replies. A human reads the thread correctly; the automated
  detector the skill specifies cannot. **M** — proposed: a marker the pipeline stamps on its own
  messages, or a bot identity in config distinct from `notify.user_key`. Reply-ts ordering against
  `posted_at` is **not** sufficient alone and was rejected on review: it establishes only that a
  message arrived later, and the pipeline's own reminder is itself later than `posted_at`, so
  ordering re-admits exactly what it is meant to exclude. Filed as
  [#198](https://github.com/topij/agentic-dev-kit/issues/198). The reply itself was correct and
  in-thread; this is not a defect in it.
- **The approval grammar has no "approve the rest" form, and the safe default makes the natural
  phrasing file nothing.** `5 skip, approve others` is unambiguous to a reader but matches no
  documented rule: bulk approve is `lgtm` / `approve all`, per-item approve is `<numbers> approve`,
  and anything unmentioned defaults to skip. A literal parser would have skipped item 5, found no
  approve verb bound to the rest, and filed **zero** tickets while reporting success. **M** — the
  failure is silent and in the safe direction, which is exactly why it would survive unnoticed.
  Proposed: add an explicit `others`/`rest approve` form, or have the parser refuse a reply it
  cannot fully account for rather than defaulting it away. Filed as
  [#198](https://github.com/topij/agentic-dev-kit/issues/198) alongside the bullet above — one
  issue, two separately testable acceptance criteria.

### 2026-08-01 (post-merge, mutation and receipt hygiene)

- **Mutation-testing a file that carries uncommitted work makes `git checkout --` destructive.**
  I mutated `scripts/hooks/pr_followup_hook.py` while it held three uncommitted review fixes, then
  reverted the mutant with `git checkout -- <file>` — which discarded the fixes too. Caught only
  because the tests written minutes earlier went red; had the mutation targeted code those tests
  did not cover, the fixes would have vanished silently and the PR would have merged without them.
  **M** — `fallback-review-panel.md` contract item 7 already says to mutate in an isolated copy of
  the repo, but it frames that as protecting *other lenses* from your writes. This is the same
  hazard pointed inward: the cockpit's own tree. Proposed: extend item 7 to say mutate only
  committed code, or copy the file aside and restore from the copy rather than from git — `git
  checkout --` cannot distinguish your mutant from your work.
- **A review receipt can name a lens that has not run, and the cockpit is as able to do it as
  anyone.** I recorded `--record-review "fallback:delta" --lenses correctness` before spawning the
  correctness lens, then ran the lens to make the claim true. The engine accepts `--lenses` as a
  typed string and verifies nothing. **M** — occurrence data for
  [#32](https://github.com/topij/agentic-dev-kit/issues/32), whose whole subject is that the lens
  roster is self-reported; what this occurrence adds is that the failure is easy to commit
  *accidentally*, mid-way through doing the right thing, rather than as a shortcut. No new proposal
  — the lens-written entries `#32` already asks for would settle it — but the sequencing hazard is
  worth naming: record after the lens returns, never before.
- **`.agents/skills/**` is not manifest-tracked, so a Codex adapter can drift from the config it
  documents.** Adding a `lens_compute.codex` sentence to `.agents/skills/pr-watch/SKILL.md` and
  regenerating the manifest produced no diff at all. The review bot independently flagged the same
  gap. **L** — these adapters are the Codex runtime's only consumer of several config keys, so a
  silent drift there makes a key inert on that runtime with nothing reporting it. Proposed: extend
  `KIT_OWNED` to the adapter files, or state at `#47` why they are deliberately excluded.
- **A config key can express a control the runtime cannot actually apply.**
  `review.fallback_panel.lens_compute` carries `effort`, but Claude Code's delegation tool has no
  per-agent effort parameter, so on that runtime it reaches a lens only as prompt text. This one is
  documented at every surface — but only because a dogfooding run surfaced it after the key had
  already been designed, written, tested and opened as a PR. **M** — nothing prevents the next such
  key, and the failure is quiet: config that reads as a control and behaves as a suggestion.
  Proposed: when a config key selects compute or capability, state per runtime whether it is
  mechanical or advisory, and consider a `kit_doctor` check that a declared runtime key has a named
  consumer.
- **A guard that refuses looks exactly like a command that failed, and the recovery instinct is to
  re-run without the guard.** `gh pr create` was chained to the closing-keyword scan. The scan
  **refused** — correctly: the PR body quoted a banned construction in the course of describing it.
  All the chain emitted was an absence, no URL, so I read it as a transient failure and re-ran
  `gh pr create` **without the chain**, publishing the body the guard had just declined. **H** —
  this is [#180](https://github.com/topij/agentic-dev-kit/issues/180) inverted and is the more
  dangerous half: `#180` is about a guard that is not chained; this is a guard that *is* chained,
  fires correctly, and loses to the operator's next keystroke.
  **What each half rests on, since a review round challenged exactly this.** The refusal is
  reproducible — the scan still exits 1 on that body content, so *"the chain would not have
  published this"* is checkable rather than narrated. The re-run without the chain leaves no
  server-side trace and cannot be corroborated from the forge; treat it as my account. What the
  record shows independently is the **consequence**: the banned construction was live in the PR body
  for roughly fourteen minutes, and throughout that window the body asserted the scan was *"clean
  over both surfaces"* while naming only the doc lines and the commit message. The body was itself
  a surface, and its claim of cleanliness was false about the document making it.
  **`#195` was not altered** — it reached its final state at `05:29:21Z`, before this PR existed,
  and nothing has moved it since.
  An earlier draft cited *"no timeline event from the PR"* as the evidence for that, and the commit
  publishing the claim falsified it on the spot by naming `#195` in its own message, which GitHub
  auto-links. **State is the checkable property here; timeline is not.** **Proposed — and
  review of this entry sharpened it, which is worth recording because the first proposal was too
  weak.** A louder failure message is not a fix: `REFUSED: <reason>` on the failure path is a useful
  diagnostic, but it does not stop the next keystroke from dropping the chain, and prescribing
  operator discipline against that is Principle #8's *"a rule that lives only in a doc is a wish"*
  aimed at my own remedy. The enforceable version is that the guarded path is the **only**
  publishing path — scan inside it, direct unguarded publication rejected — which is
  [#71](https://github.com/topij/agentic-dev-kit/issues/71)'s ask rather than a separate one. So
  this is occurrence data for `#71` and evidence for its priority: the guard being ad-hoc rather
  than shipped is precisely what made dropping it a single edit.
- **`gh pr view <branch>` can resolve to a *merged* PR when a branch name repeats.** Compounding the
  above, and the reason I mis-diagnosed it: the wrap-up branch pattern
  `chore/update-handoff-{date}` repeats whenever two wrap-ups land on one date, and this session's
  did. `gh pr view <branch> --json number,isDraft` printed `PR #191 isDraft=false` — a PR **merged
  the previous session** from a branch of the same name — so the check answered confidently about a
  different, already-merged PR and sent me looking for a transient `gh` failure instead of at my own
  refused guard. Caught only by listing open PRs and finding none. **M** —
  [#179](https://github.com/topij/agentic-dev-kit/issues/179)'s shape with a concrete mechanism, and
  it weakens [#170](https://github.com/topij/agentic-dev-kit/issues/170) directly: verifying the
  draft bit landed is only sound when bound to the PR just created. Proposed: verify by the PR
  **number** `gh pr create` prints, never by branch name; and consider a wrap-up branch pattern that
  cannot repeat within a day.

## Graduated 2026-08-01 — GitHub Issues (#192–#196)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored). Eight entries
in, eight accounted for: **five graduated** into new issues, two occurrence comments on `#180`
and `#71`, and one entry the operator declined to file (`git add -A` staging a `.DS_Store`) —
archived here with the rest, and therefore with no tracker representation.

The blocks below are the swept text, verbatim, with headings demoted one level. The first is
the previous sweep's graduation marker — the seventh sweep; the rest are the session blocks
that accumulated after it. This sweep's own marker is in `kit-friction-log.md`, not here.

### 2026-07-31 — Backlog migrated to GitHub Issues (#178–#183)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Fourteen entries in, fourteen accounted for:** six new issues
([#178](https://github.com/topij/agentic-dev-kit/issues/178)–[#183](https://github.com/topij/agentic-dev-kit/issues/183)),
four occurrence comments (`#163`, `#54`, `#140`, `#75`), and two entries that needed no ticket
because the work they asked for had already landed — ten writes, each re-read from the tracker
after landing per `#138`.

The mapping is not one-per-entry in either direction, so neither count is a per-entry tally: two
entries of the 2026-07-30 post-merge-second section share `#179`; the `#163` comment carries two
entries, and the `#54` comment carries two, one of which is also the whole of the `#140` comment.

**Reading the tracker before drafting changed the routing twice, and both changes were
subtractions.** The doc-budget entry proposed occurrence data for `#74` — but `#74` is no longer
open (completed 2026-07-30), `scripts/archive_plan_sessions.py` now implements
`--target-lines`, and `docs/agentic-dev-kit/workflows/wrap-up.md`'s *"Keep the handoff docs lean"*
step prescribes it by name. (Cited by heading because position failed twice: `:58` was true when
written and `#176` invalidated it hours later, then the repair said "step 8" when it is step 7.)
Both
halves of that entry had landed, including the half the entry itself said was still missing. The
`finalize.pr_draft` entry had already recorded its own resolution inline on 2026-07-30. A sweep
that drafted from the entries alone would have filed two tickets for work that was already done,
and the entries are the only surface that would have said otherwise.

Two proposals were filed as **new issues rather than as occurrence comments on `#150`**. That
issue's stated subject is a scripted text replacement that matches nothing; a check that ran in
the wrong directory (`#179`) and a guard that reported failure correctly and was then ignored
(`#180`) are neither. Stretching `#150` to cover them would have widened its acceptance criterion
past what it can test — three entries pointed at it, and only the `sed` half of one is literally
in scope. `#150` stays open and unchanged; both new issues link to it, so the backlinks are on it
either way.

#### Approval record — in-session operator, no DM

`config/dev-model.yaml → notify.user_key` is empty and no `config/dev-model.local.yaml` exists, so
there is no DM surface to stop on; the operator was present in session and substituted for it.
**The documented stop is still unconditional** — `.claude/commands/triage-friction-log.md` states
it at lines 113 and 465 — so this run is in the same position as the run
[#128](https://github.com/topij/agentic-dev-kit/issues/128) was filed against, which the archive
records as having *violated* the stop rather than substituted for it. What `#128` asks for is an
interactive-operator exception that does not exist yet; what it calls the load-bearing half is
that any substitute leave a **committed** approval record, since `state/` and `reports/` are
gitignored (`.gitignore:9` and `:25`). This block is that record. It does not make the run
compliant with a rule the skill has not yet gained.

Approval was bulk and unconditional — *"lgtm"* — so every proposal carries the same decision and
the explicit-opt-in default for unmentioned proposals was never exercised. This is the **seventh**
sweep overall; the archive holds the six earlier markers.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-31.txt` (gitignored),
`sha256 33ad2f7260690df2104e199bfa6f824b38d64df741eb93ee0be027ed31079d3f` over **23,145 bytes**.
Taken before any write, and over a *committed* blob — the inbox at `abbd62f` is that text, so
`git show abbd62f:docs/kit-friction-log.md | tail -n +14 | sha256sum` reproduces the digest in any
session that has **`git` and a SHA-256 utility**, with no reliance on the gitignored file
surviving. An earlier draft of this block said *"from `git` alone, in any session"*. The reviewer
on this PR refuted it by running the command: its environment had none of `sha256sum`, `shasum`,
`openssl`, `busybox` or `cksum`, so it could confirm the blob and its 23,145 bytes but not the
digest. That is an untested mechanism claim of exactly the shape
[#140](https://github.com/topij/agentic-dev-kit/issues/140) governs, written from intent about an
environment other than the one it ran in.

| # | proposal (abridged) | from entry | decision | outcome |
| - | ------------------- | ---------- | -------- | ------- |
| 1 | Hook fires on command *text*, not on a PR actually opening | 5 | approve | [#178](https://github.com/topij/agentic-dev-kit/issues/178) |
| 2 | A check that never reached its subject reports clean | 1 + 2 | approve | [#179](https://github.com/topij/agentic-dev-kit/issues/179) |
| 3 | A guard must be *chained* to the action it guards | 14 | approve | [#180](https://github.com/topij/agentic-dev-kit/issues/180) |
| 4 | `--subject` suppresses the automatic `(#N)` append | 6 | approve | [#181](https://github.com/topij/agentic-dev-kit/issues/181) |
| 5 | A stalled lens is indistinguishable from one that found nothing | 7 | approve | [#182](https://github.com/topij/agentic-dev-kit/issues/182) |
| 6 | A mutation kill that aborts the session names no test | 4 | approve | [#183](https://github.com/topij/agentic-dev-kit/issues/183) |
| 7 | The one-of-two-sites remedy is structural, not another guard | 3 + 12 | approve | comment on #163 |
| 8 | A count of your own effort is a verification claim like any other | 8 + 9 | approve | comment on #54 |
| 9 | An ordinal into someone else's list is a mechanism claim | 9 | approve | comment on #140 |
| 10 | Occurrence; recovery needed the object reachable locally | 13 | approve | comment on #75 |
| — | Doc-budget remedy is a no-op at the default `--keep` | 10 | approve | no ticket — already landed |
| — | `finalize.pr_draft` contradicts the operator's preference | 11 | approve | no ticket — already landed |

#### What was verified

The commands and their output are on the PR. Read them there. In summary: the snapshot digest
reproduces from `abbd62f`; all six issues exist with the titles and labels this record claims,
re-read from the tracker after filing; each of the four comments was re-read **by body** on the
issue claimed for it, not merely by the URL the create call returned; `#74` is no longer open and
the `--target-lines` mode it asked for is present in `archive_plan_sessions.py`.

The sweep itself ran under five assertions that abort before any write — snapshot equality, fence
parity, no alteration inside a fenced block, an un-demote round-trip, and per-line survival. The
previous marker recorded the fence count as measured rather than gated, and this run promoted it
to a gate.

**That promotion established nothing, and the run reported so itself.** The script printed
`0 fences preserved`: this inbox contains no fenced blocks at all, so the fence-parity assertion
and the fenced-line comparison both passed over an empty set. They are gates that never reached
their subject — which is [#179](https://github.com/topij/agentic-dev-kit/issues/179), filed
earlier in this same sweep, occurring inside the sweep that filed it. The only reason it is
recorded rather than claimed as coverage is that the script prints the count it asserted on; had
it printed `ok` the vacuous pass would have read as a real one, and that is `#179`'s
negative-control ask in one line.

So the gates that actually bore weight here are snapshot equality, the un-demote round-trip, and
per-line survival — and the round-trip is self-inverting, so it would pass on a corrupted
demotion. Per-line survival is the one doing real work. The fence gates stay in the script
because the archive *does* contain fenced blocks and a future inbox will too; they are simply
unproven today.

**What these checks do not reach.** Two are carried over unchanged: nothing verifies that the
approval happened as described — which matters most precisely because the DM that normally carries
that evidence did not exist — and no automated gate covers any of this
([#127](https://github.com/topij/agentic-dev-kit/issues/127)). One is new and is a direct
consequence of how the issues were checked: the six were confirmed by **title and label**, not by
body, so a mangled body would have passed. The comments were checked more strictly than the issues
were, which is the asymmetry a reader should assume until it is closed.

Above all, nothing here verifies that any filed issue or posted comment is **true**. What this
sweep can say is narrower and worth saying plainly: reading the tracker first is the only step
that caught anything, and what it caught was two entries asking for work that already existed. The
entries were confidently wrong about the state of the repository, and no amount of care in drafting
from them would have surfaced it.

The swept entries are verbatim in the archive under `Graduated 2026-07-31`.

### 2026-08-01

- **One `unavailable_markers` list serves two surfaces, so a check-surface phrase matches comment
  bodies.** A PR comment of mine *describing* CodeRabbit's rate-limiting produced an `unavailable`
  entry with `bot: None` attributed to `@topij`. **The engine is not confused** — `summarize_review_bots`'
  docstring states this case exactly (`bot` is `None` when a marker matches but the author matches no
  configured bot, "reported (the operator should see it) and attributed to nobody, so it can never
  suppress anything"), and an earlier draft of this entry called that a defect and proposed deleting
  the property the docstring names as its rationale. **L, not M**, and the real observation is
  narrower: the phrase that fired is `"review rate limited"`, which `config/dev-model.yaml` annotates
  as *the status-check wording* of the comment-surface marker. It matched a comment body only because
  both surfaces read one list. Proposed: let a marker declare which surface it belongs to, so a
  check-phrase cannot match a comment. Filed as a new proposal — **not** occurrence data for
  [#23](https://github.com/topij/agentic-dev-kit/issues/23), which is closed and is the mirror-image
  defect (a check-surface outage that was *not* being read).
- **The closing-keyword scan ran as a separate command before the publish, so a printed violation
  did not stop it.** The comment posted with a banned construction in it; nothing was closed
  (GitHub auto-closes from PR bodies and commits, not issue comments), and the re-post gated on the
  scan's exit status then began refusing publishes that carried the same shape. **M** — this is
  [#180](https://github.com/topij/agentic-dev-kit/issues/180) occurring in the session after it was
  filed, by the agent that filed it, so the entry is occurrence data rather than a new proposal. The
  fix that worked: `scan && publish` as one chained command, never two sequenced ones. Also
  occurrence data for [#71](https://github.com/topij/agentic-dev-kit/issues/71), whose guard would
  have caught it at authoring time.
- **`git add -A` in a fix round committed a `.DS_Store`, and no gate would have caught it.** Not in
  `.gitignore`, not on the protected branch, invisible to CI and to the drift gate. Found only
  because resolving the review panel's revision meant diffing against a freshly fetched base and
  reading the diffstat. **L** — fixed in-session by adding the entry to `.gitignore`, so the
  specific recurrence is closed; the general shape is that a fix round's `git add -A` stages
  whatever the working tree happens to hold, and the panel's revision-resolution step was the only
  thing that looked.
- **A one-lens receipt at the merging head is honest but the loop has no cheaper way to earn a
  two-lens one.** The full panel's last head was two fix rounds behind the merge, and each fix round
  invalidates the receipt, so converging fully would have meant a panel per round indefinitely. The
  merge disclosed the gap and recorded `fallback:delta` rather than stamping `fallback:panel`.
  **M** — the doctrine's stopping criterion is blast radius rather than round count, but nothing in
  `pr-watch` or the panel doc tells an agent how to *record* a stop taken on blast-radius grounds;
  the receipt vocabulary only describes what ran, not why stopping was proportionate. Proposed:
  a receipt field, or a documented disclosure shape, for "stopped on blast radius" — currently it
  lives only in a PR comment an autonomous merge path never reads
  ([#32](https://github.com/topij/agentic-dev-kit/issues/32)'s territory).

### 2026-07-31 (post-sweep)

- **`make test` fails three tests as root, and the failure reads as a regression rather than as an
  environment fact.** `test_an_unreadable_doc_is_a_documented_exit_2_not_a_traceback` and both
  `test_a_read_failure_names_the_document_that_failed` cases make a doc unreadable with `chmod 000`
  and assert exit 2. Under `uid 0` that permission is a no-op — root reads the file anyway — so the
  tool succeeds and the assertion sees `assert 0 == 2`. **M** — the hazard is the *reading*, not the
  failure: `make test` is the verification command this repo's `CLAUDE.md` names, and an agent that
  runs it in a root container sees three red tests with no signal that they are environmental. The
  honest options are to skip them under `os.geteuid() == 0` with a stated reason, or to make the
  file unreadable by a means root cannot bypass. Established by running `make test` twice from
  `/home/user/agentic-dev-kit` — once with this sweep's two doc edits and once with them stashed —
  and getting the identical three failures and `589 passed` both times; `id -u` reports `0`. Noted
  during the 2026-07-31 sweep and deliberately left below the marker, so the next pass proposes it.

### 2026-07-31 (post-merge, review-loop doctrine)

- **A comment-then-ack chain piped the poll to `/dev/null`, and a bot finding was acknowledged
  unread.** Twice in one session: `pr_watch.py <PR> --json > /dev/null` chained into `--mark-seen`
  after posting a round comment. The second time, the discarded poll carried the review bot's pass
  over an intermediate head with one actionable finding; the ack buried it. Caught before merge
  only because a later read poll's `coverage` line named a review at a sha no panel round had
  claimed, prompting a by-hand fetch of the review. `pr-watch.md` step 6 already commands "always
  poll-and-read first" — the violation was convenience chaining, so the documented rule did not
  hold where it mattered. **M** — proposed fix: `--mark-seen` should print an excerpt of every key
  it promotes, making the ack surface itself a read; until then, never redirect a poll whose
  pending set a mark-seen will promote. Routes to
  [#180](https://github.com/topij/agentic-dev-kit/issues/180) as a sharpening, not to `#150`,
  which the latest sweep deliberately kept narrow: the ack *was* chained to the poll, and
  chaining gates on exit status — a check whose signal lives in its output, not its exit code,
  is unguarded by chaining unless the output reaches a reader.
- **The keyword-adjacency scan covered the diff and not the commit message committed beside it.**
  Two banned constructions (described, not quoted, per this file's own precedent) reached the
  pushed branch inside a fix-round message; the amend was prepared and scanned clean, the
  force-push was declined at the operator's permission gate, so the branch message stands,
  disclosed on the PR, and the squash message was authored fresh and scanned. **M** — the ground
  rule says any surface; the scan's surface list was one short, which is
  [#179](https://github.com/topij/agentic-dev-kit/issues/179)'s shape: a gate examining the wrong
  set. Proposed fix, adopted mid-session and held after: write the message to a file, scan the
  file, `git commit -F` it — and treat the surface list as diff, commit message, PR body, and
  squash subject plus body. Occurrence data for
  [#71](https://github.com/topij/agentic-dev-kit/issues/71).
- **`gh pr merge --delete-branch` from a detached HEAD merges server-side, then exits nonzero.**
  The failure ("could not determine current branch") is the local branch-switch step, after the
  merge already succeeded; a caller reading exit ≠ 0 as merge-failed reports a false failure or
  retries. The retry printing "already merged" is what disambiguated it here. **L** — proposed
  fix: when detached, merge without `--delete-branch` and delete branches separately.

## Graduated 2026-07-31 — GitHub Issues (#178–#183)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet). Fourteen entries
in, fourteen accounted for: **six graduated** into new issues, four occurrence comments across
`#163`, `#54`, `#140` and `#75`, and two entries that needed no ticket because the work they
asked for had already landed.

The blocks below are the swept text, verbatim, with headings demoted one level. The first is the
previous sweep's graduation marker — the sixth sweep; the rest are the session blocks that
accumulated after it. This sweep's own marker, carrying the approval record and the verification
statement per `#128`, is in `kit-friction-log.md`, not here.

### 2026-07-29 (second sweep) — Backlog migrated to GitHub Issues (#155)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Five entries in, five accounted for:** one new issue
([#155](https://github.com/topij/agentic-dev-kit/issues/155)) and seven occurrence comments
(`#121`, `#138`, `#140`, `#45`, `#150`, `#71`, `#149`) — eight writes, each re-read from the
tracker after landing per `#138`.

The mapping is not one-per-entry in either direction, so neither count is a per-entry tally:
entry 1 routed to `#121` and `#138` *and* folded its second half into the `#45` comment that
entry 3 also produced; entry 2 produced both `#155` and the `#140` comment.

Every routing target was read from the live tracker **before** drafting. That is a direct
response to entry 1, which records the previous sweep re-deriving `#121` — an OPEN issue filed
**two sweeps earlier** — without noticing it existed. (The swept entry and this marker's first
draft both said *"the previous run"*; `#121` was created `2026-07-28T12:57:28Z` and falls in the
third sweep's `#112`–`#125` range, with the fourth sweep in between. A review lens caught it, and
the `#138` comment carrying the same error was amended.)

#### Approval record — in-session operator, no DM

`config/dev-model.yaml → notify.user_key` is empty, so there is no DM surface to stop on; the
operator was present and substituted for it. **The documented stop is still unconditional** —
`.claude/commands/triage-friction-log.md` states it at lines 113 and 465 — so this run is in the
same position as the run [#128](https://github.com/topij/agentic-dev-kit/issues/128) was filed
against, which the archive records as having *violated* the stop rather than substituted for it.
What `#128` asks for is an interactive-operator exception that does not exist yet; what it calls
the load-bearing half is that any substitute leave a **committed** approval record, since
`state/` and `reports/` are gitignored. This block is that record. It does not make the run
compliant with a rule the skill has not yet gained.

Approval was bulk and unconditional — *"lgtm"* — so every proposal carries the same decision and
the explicit-opt-in default for unmentioned proposals was never exercised. This is the **sixth**
sweep overall; the archive holds the five earlier markers.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-29-b.json` (gitignored),
`sha256 ccb3b0c4e5aae8f6ea2f756cb523be5cfbd215e5a2b432c1c885796eb36a92fe` over **13,678 bytes**.
Taken before any write, and over a *committed* blob — the inbox at `c48164c` is that text, so
the digest reproduces from `git` alone, in any session. The `-b` suffix is because this is the
second sweep dated 2026-07-29; the first sweep's snapshot is a different file and is still
referenced by the marker now in the archive.

| # | proposal (abridged) | from entry | decision | outcome |
| - | ------------------- | ---------- | -------- | ------- |
| 1 | Which of `dev-model.yaml` is template and which is live is not readable | 1 | approve | comment on #121 |
| 2 | The duplicate check belongs before the draft, not only after the writes | 1 | approve | comment on #138 |
| 3 | A remark attributed to the operator must be quoted at its original scope | 2 | approve | [#155](https://github.com/topij/agentic-dev-kit/issues/155) |
| 4 | The positive polarity needs a command too — *"X was never installed"* | 2 | approve | comment on #140 |
| 5 | The reviewer's real state is neither expressible in config nor recoverable | 1 + 3 | approve | comment on #45 |
| 6 | Widen from text replacements to any check: assert it examined something | 4 | approve | comment on #150 |
| 7 | Third hand-rolled instance of the guard, dropping the same stated exception | 4 | approve | comment on #71 |
| 8 | A review-changed fact must be sourced from the merged text, not recollection | 5 | approve | comment on #149 |

**Two amendments after approval, disclosed rather than silent.** Proposal 6 referred to the guard
it was describing by a compound noun whose first word is one of the hazardous keywords, sitting
within 60 characters of an issue reference; the pre-post scan flagged the proposal's own prose and
the word was dropped. It would not have fired GitHub's parser — the keyword was not directly
followed by the reference, and a comment cannot act on an issue regardless — but `#71` states that
over-firing is the acceptable failure and the repo rule admits no exceptions. (Described here
rather than quoted, which is the swept entry's own point: quoting the construction puts a live one
into the record.) Proposal 4 gained the literal `#155`, which did not exist when it was approved.

#### What was verified

The commands and their output are on the PR. Read them there. In summary: the snapshot digest
reproduces from `c48164c`, and the snapshot file's own text field hashes to the same value; the
archived block un-demotes to the snapshot byte-for-byte; each of the seven comments sits on the
issue claimed for it; `#155` exists with the title and labels this record claims. **Several of
those comments have since been amended** — corrections from the review rounds on this PR — so they
no longer hash to the text originally sent, and the check compares placement rather than content.

**What these checks do not reach.** Two are carried over from the previous marker: nothing
verifies that the approval happened as described — which matters most precisely because the DM
that normally carries that evidence did not exist — and no automated gate covers any of this
([#127](https://github.com/topij/agentic-dev-kit/issues/127)). The previous marker's third gap,
that checks 1 and 2 shared no trust chain because the snapshot's text field was never hashed, is
now **closed** rather than restated: the check hashes that field. One gap is new, found by a review
lens: the un-demote round-trip is self-inverting and would pass on a corrupted demotion, and the
fence count that would catch the realistic corruption is measured, not asserted as a gate.

Above all, nothing here verifies that any posted comment is **true**. Four review lenses across two
rounds found defects on this PR in every round, and **every one was in prose describing the work
rather than in the work** — the mechanical core has not been wrong once, under every negative test
four lenses could construct. That asymmetry is the honest summary of what these checks are worth,
and the argument for keeping the record short: the prose is where the defects live.

The swept entries are verbatim in the archive under `Graduated 2026-07-29 (second sweep)`.

### 2026-07-30 (post-merge, second)

- **A `cd` in one Bash call silently rebased every later command, and three checks reported green
  against the wrong tree.** Mid-session I ran `cd <scratch>/m15 && pytest` to reproduce a mutant.
  The working directory persists across calls, so the next `ruff check scripts/`, `make test` and
  `kit_doctor --generate-manifest` all ran **inside the mutated clone** and reported clean. It
  surfaced only because a `grep` for test names I had just written returned nothing. Re-run from the
  repository, a real `ruff` failure appeared that the false green had hidden. The same drift then
  put a `sed -i ''` rename into the clone instead of the repo, leaving a test whose `def` kept its
  old name while its docstring claimed the rename and a sibling cited an identifier that did not
  exist — found by a review lens, not by me. **H** — this is the shape that makes a whole
  verification section worthless, and both instances were in the same session as a PR *about*
  trustworthy failure reporting. Proposed fix: any command whose result is quoted as verification
  should establish its own directory (`git -C`, absolute paths, or a leading `cd <repo>`), and a
  verification claim should name the directory it ran in. Routes to
  [#150](https://github.com/topij/agentic-dev-kit/issues/150) as a **widening**, not as occurrence
  data: only the `sed` half is literally a scripted text replacement, which is that issue's stated
  subject. The three falsely-green *checks* share its root cause — the target was never reached —
  and that is the class the issue would have to grow to cover.
- **A verification probe reported five clean passes and had exercised nothing.** Written to re-drive
  a review lens's five measured data-loss scenarios against the fixed code, it compared the raw
  `--plan` path against the path `os.replace` was called with — while the engine resolves targets
  with `os.path.realpath`, and on macOS `/var` is a symlink to `/private/var`. No injection ever
  fired; every scenario "passed". **H** — a probe that exercises nothing is indistinguishable from a
  probe that finds nothing, and this one was written *specifically* to check that a data-loss fix
  worked. Caught only by noticing that exit 0 with no stderr was implausible for a scenario that was
  supposed to fail. Proposed fix: a negative-control run belongs in any probe of this kind — assert
  the injection fires at least once before trusting the pass. Occurrence data for
  [#150](https://github.com/topij/agentic-dev-kit/issues/150) and a sharpening of it: `#150` covers a
  check that *reports* success wrongly; this is a check whose subject was never reached.
- **"Applied to one of two call sites" appeared five times in one PR, three of them inside the fix
  for that pattern.** Round 1 widened one publish handler and not its twin; the review bot then found
  the twin's rollback unguarded; round 4 found both rollback handlers making the unsound inference
  the forward publishes had just been fixed to avoid; round 4 also found the plan-site widening
  tested only at the history site; and a `BaseException` argument written down in one method's
  docstring was not carried to the method one call away. **H** — every instance was individually
  low-severity and the class is not: severity ranking cannot see it, and four rounds of reviewers
  each found one more. What ended it was **collapsing the duplication into a single
  `restore_handoff()`**, after which shared-code mutants died to tests from both sites. Proposed fix:
  route to [#163](https://github.com/topij/agentic-dev-kit/issues/163) — its enumeration is of
  occurrences; what this adds is that the remedy is structural (remove the second site) rather than
  another guard, and that a fix round should check its own twin before the reviewer does.
- **A mutation kill that aborts the test session names no test.** One mutant let a `KeyboardInterrupt`
  escape, and pytest aborts the whole run on that signal — so the driver reported `killed by ?` and,
  in an earlier variant, `EXCLUSION EXCLUDED NOTHING` because the summary line never printed. Both
  read as tooling noise rather than as the kill they were. **M** — `fallback-review-panel.md` item 5
  already says a kill counts only if a behaviour-asserting test failed; it does not say the test must
  be *identifiable*, and an unattributable kill is not evidence. Proposed fix: a test pinning
  "must not raise" should catch and `pytest.fail`, not let the exception propagate.

### 2026-07-30 (post-merge)

- **`pr_followup_hook.py` fires on command *text*, not on PR-opens — six false positives in one
  session.** Its trigger matches `.tool_input.command`, so any heredoc containing `gh pr create`
  or `gh pr ready` trips it: writing a doc *about* the command, filing an issue quoting it, and
  the `gh pr merge` whose squash body mentioned it all produced a MANDATORY watch-loop demand with
  no PR in existence. **M** — the guard it implements is real (`PRINCIPLES.md` #5/#8), which is
  what makes this expensive: a hook that cries wolf on documentation trains the agent to skim the
  one message that is sometimes load-bearing. **Two gates, and a fix must address both:**
  `.claude/settings.json` pre-filters on `Bash(gh pr *)`, then `pr_followup_hook.py:41` matches
  `\bgh\s+pr\s+(create|ready)\b` against `.tool_input.command` (`:181-182`) with no heredoc or
  quote awareness. Proposed fix: gate on the tool *result* rather than the command string — and with a
  **predicate per command**, since the two differ: `gh pr create` succeeds by yielding a *new* PR
  number, while `gh pr ready` acts on an existing one and succeeds by that PR reading
  non-draft afterwards. A single new-PR-URL test would silently drop every valid `ready` event. A review lens reproduced a seventh occurrence
  live while checking this entry.
- **`gh pr merge --subject` suppresses GitHub's `(#NNN)` append — and the repo already had the
  problem.** `eeef647` landed without its number, worked around on the next merge by writing
  `(#168)` into the subject by hand. But a review lens then measured the base rate: **15 of 75
  commits on `main` have an associated PR and no `(#N)`** — though 8 of those predate the squash
  convention and carry their number in a merge-commit subject instead, so the comparable figure is
  **7 of 67** (75 minus 5 constituent commits of PRs #1–#3 and their 3 merge commits): `cdeae7a` (#144), `c48164c` (#154), `b46f794` (#153), `0b82ff2` (#148), `42873d8`
  (#69), `9c6ab3a` (#68), and this session's. So `--subject`
  explains *this* instance and is **not established** as the cause of the others. **M** — raised
  from L because it is recurring rather than a one-off, and a ticket drafted from the first
  version of this entry would have carried the wrong scope. Proposed fix: whichever workflow
  documents `gh pr merge` should say `--subject` replaces the whole subject line, append included
  — and something should check the suffix at merge time, since it went unnoticed across several
  sessions. (No session count is offered: two review lenses counted this same population and got
  four and five. Neither is independently reconstructible, which is the condition under which `#75`
  says to publish the invariant and not the figure.)
- **Two isolated lenses stalled identically at the 600s watchdog, mid-run.** Same session, same
  prompt shape, both killed with partial output. Re-running with a tighter scope succeeded. **M**
  — the hazard is not the stall but its shape: a stalled lens returns *nothing*, which is
  indistinguishable from a lens that ran and found nothing unless the cockpit checks the task
  status. `fallback-review-panel.md` item 10 requires the lens to open with what it reviewed,
  which catches a wrong-ref lens but not a dead one — the report never arrives at all. Proposed
  fix: the panel's step 3 should confirm each lens reached a **successful terminal status**, and
  record the exit/watchdog state — not merely that something came back. "Returned" is too weak, and
  this session proves it: both stalled lenses emitted partial text before the watchdog killed them,
  so a returned-output test would have passed them.
- **A self-reported count of your own effort drifts upward, and nothing checks it.** This session's
  handoff block was written claiming *"nine panel rounds and twenty isolated lens runs"*. Recounting
  the actual launches gave **eight rounds and sixteen completed runs** (eighteen launched, two
  stalled). Both figures were wrong in the direction that makes the measurement sound stronger, and
  the sentence carrying them was the block's own thesis — that explanatory prose is where defects
  live. **It reached a published surface before it was caught:** the PR opened at 15:08:13Z carrying
  the inflated figures, and the correction landed at 15:10:58Z — after, not before. No check exists
  that would have caught it at all; the recount was voluntary. **M** — occurrence data for [#54](https://github.com/topij/agentic-dev-kit/issues/54), and
  a sharpening of it: `#163`'s comment already records that unreconciled restatements *"moved in the
  author's favour"*. This is the same drift with no restatement involved — the first statement was
  already inflated. Proposed fix: a count of one's own work is a verification claim like any other,
  so it needs the enumeration behind it, not just the number.
- **A citation and its quotation can drift apart, and only the citation goes wrong.** A comment on
  `#170` quoted that issue's third constraint verbatim while numbering it the fourth, twice, and
  the same wrong ordinal reached a commit message. The quote read as corroboration for the number
  beside it. **L** — occurrence data for [#54](https://github.com/topij/agentic-dev-kit/issues/54)
  and [#140](https://github.com/topij/agentic-dev-kit/issues/140): "name the command that
  establishes it" covers a claim, but an ordinal into someone else's list is a claim too, and the
  cheapest check is to re-read the list rather than the sentence.

### 2026-07-29 (post-sweep, second)

- **The doc-budget remedy is a no-op at the default `--keep`, and the wrap-up workflow prescribes
  exactly that invocation.** `check_doc_budget` warned the handoff was 423/400 and named
  `archive_plan_sessions.py` as the remedy; running it as
  `docs/agentic-dev-kit/workflows/wrap-up.md` step 7 instructs
  reported *"nothing to move: 6 session block(s) <= --keep 6"* and left the file over budget. Only
  an explicit `--keep 5` moved anything (425 → 352; a first draft of this entry said 423, which
  cannot be right — 425 − 73 = 352). **M** — occurrence data for
  [#74](https://github.com/topij/agentic-dev-kit/issues/74), which already records the lines-vs-blocks
  mismatch. The archive already records this recurrence, including that the workflow tells the
  operator to run a sweep that does nothing at its default — so this is at least the fifth
  occurrence, not a new observation. What it can still add is the concrete remedy shape: a budget
  expressed in lines cannot be discharged by a remedy bounded in blocks, so either the script takes
  a line target or `wrap-up.md` says to lower `--keep` until the budget clears.
- **`finalize.pr_draft: true` contradicts the operator's stated preference and this repo's own
  `#124`.** The operator asked that PRs be marked ready as soon as no further changes are expected,
  because a draft is invisible to the review bot; `#124` records the same thing as a defect of the
  triage workflow specifically. **M** — **addressed 2026-07-30**, and one claim in this entry was
  wrong: `config/dev-model.yaml` never defaulted `finalize.pr_draft` at all. The key is absent from
  that file and read by no code here — before the fix the only default anywhere was prose in
  `.claude/commands/triage-friction-log.md`'s config table, now `false`. The larger find while
  doing it: `post-merge-systemize.md` **hardcoded `gh pr create --draft`**, so the config key it
  documents had no effect on the one place that workflow opens a PR — a Principle #10 violation,
  not a default that needed flipping. And a draft
  is worse than unreviewed: CodeRabbit's *"Review skipped: draft pull request"* matches
  `review.unavailable_markers`, so a draft registers as **reviewer-unavailable** and demands a
  `fallback_panel` pass the sweep never asked for.
- **Three review rounds on one change found their defect in the same place each time: the prose
  justifying the mechanism.** `_deep_merge`'s docstring said "two shapes" while implementing six;
  the overlay allowlist said its keys were "read by no shell reader" while `init.sh` read exactly
  them; a list-replacement rule was motivated by a key the same file asserts can never be set. The
  mechanism itself was never wrong — and the two genuine bugs found in rounds 2 and 3 were both
  introduced by the *previous round's fix*. **M** — downgraded from H after a lens refuted the
  absolute form: the mechanism *was* wrong in every round too, including three adopter-facing
  defects. The claim that survives is narrower and still useful — justification prose is written
  from intent, which neither a reviewer nor a test can check against the code, so it recurs while
  mechanism defects get fixed once. Proposed fix for `fallback-review-panel.md`'s authoring
  section: a "why this is safe" sentence should cite a test that would fail if it were false, or be
  deleted. **Do not promote the absolute version** — it was queued for doctrine here and was
  false.
- **Both review lenses were handed a worktree at the PR's base rather than its head, and both
  caught it.** Runtime-provided isolation created both worktrees at `c48164c`, so
  `git diff origin/main...HEAD` was empty in each and neither HEAD matched the `f33bb488` the
  launch prompt named. Both detected it and reviewed the real diff — one via read-only plumbing
  against the shared object store, the other by re-pointing its own worktree. **M** — occurrence
  data for [#75](https://github.com/topij/agentic-dev-kit/issues/75), continuing its recorded
  detection rate rather than adding anything new to it. A first draft of this entry called it "the
  first instance where the guard is observed working"; `#75`'s own body says **9 of 9 across two
  sessions**, and the previous sweep recorded 14 of 14, so that claim inverted the record it cited.
  A lens caught it. What this run does add is narrower: recovery was possible only because the
  object was reachable locally, which is not true of the cross-repository case `#75` also records.
  **Not from the swept inbox:** surfaced by the review panel on this sweep's own PR.
- **`set -euo pipefail` did not gate the step after a failing check, so a guard that fired was
  overruled by the write it was guarding.** The keyword scan protecting this sweep's PR body ran
  as a heredoc'd Python block under `set -euo pipefail`, exited non-zero with three flags — and
  the `gh pr edit` on the next line ran anyway, publishing the flagged text and printing a success
  line. Reproduced minimally in the same tool harness (`set -euo pipefail`; failing heredoc'd
  `python3 - <<'PY'`; the following `echo` still runs), and **not** reproducible by running the
  identical script under either `bash` or `zsh` directly, where both abort correctly — so it is a
  property of how the command is executed, not of the shell's `errexit`. Every scan-then-act in
  this session was therefore ungated; nothing wrong was published as a result only because the
  output was read each time, which is luck rather than a mechanism. **M** — occurrence data for
  [#150](https://github.com/topij/agentic-dev-kit/issues/150), and a sharpening of it: that issue
  and this session's comment on it both frame the danger as a check that *reports* success
  wrongly. This is a check that reported failure correctly and was ignored, which the same
  acceptance criterion does not cover. The durable form is that a guard must be **chained** to the
  action it guards (`check && act`), never merely sequenced before it — sequencing depends on an
  `errexit` guarantee that does not hold in every execution context. **Not from the swept inbox:**
  surfaced while writing this PR.

## Graduated 2026-07-29 (second sweep) — GitHub Issues (#155)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet). Five entries in,
five accounted for: **one graduated** into a new issue, and seven occurrence comments across
`#121`, `#138`, `#140`, `#45`, `#150`, `#71` and `#149`.

The two blocks below are the swept text, verbatim, with headings demoted one level. The first is
the previous sweep's graduation marker — the fifth sweep, dated the same day as this one; the
second is the session block that accumulated after it. This sweep's own marker, carrying the
approval record and the verification statement per `#128`, is in `kit-friction-log.md`, not here.

### 2026-07-29 — Backlog migrated to GitHub Issues (#149–#150)

The inbox was swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine
tracked in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Seven entries in, seven accounted for:** one graduated into two new issues
([#149](https://github.com/topij/agentic-dev-kit/issues/149),
[#150](https://github.com/topij/agentic-dev-kit/issues/150)), six routed as seven occurrence
comments (`#120`, `#138`, `#127`, `#75`, `#71`, `#45`, `#113`).

Two reconciliations, stated rather than left to a reader — mis-stating exactly these is what
`#138` was filed for. Both are one-into-two. The correction-propagation entry became **two**
issues because the surface-enumeration checklist (`#149`) and the assert-your-edit-changed-
something guard (`#150`) are different mechanisms that can land independently. The
check-heading entry became **two** comments because it names two distinct checks: the routing
check's heading (`#138`) and the block-integrity check's unanchored substring test (`#127`).

#### Approval record — in-session operator, no DM

`config/dev-model.yaml → notify.user_key` is empty, so there is no DM surface to stop on; the
operator was present and substituted for it, as in the 2026-07-28 second sweep. (This is the
**fifth** `triage-friction-log` sweep overall — the archive holds four earlier markers. Only the
second-of-07-28 also substituted; the first-of-07-28 is the run `#128` was filed *against*, and
the archive records that one as having **violated** the stop, not substituted for it.)
[#128](https://github.com/topij/agentic-dev-kit/issues/128) asks that such a substitute leave
the approval record somewhere **committed**, since `state/` and `reports/` are gitignored. This
block is it. Approval was bulk and unconditional — *"lgtm"* — so every proposal carries the
same decision and the explicit-opt-in default was never exercised.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-29.json` (gitignored),
`sha256 a24d1e32693a3df94f63aa5faa708c00381785c3b96587b7af9fe8fbed12a538` over **15,840 bytes**
(15,755 characters; 44 non-ASCII — the digest is over the bytes). Taken before any write, and a
*copy of a committed blob*: the inbox at `0b82ff2` is that text, so the digest reproduces from
`git` alone, in any session.

| # | proposal (inbox entry, abridged) | decision | outcome |
| - | -------------------------------- | -------- | ------- |
| 1 | When a claim is corrected, enumerate every surface it was published to | approve | [#149](https://github.com/topij/agentic-dev-kit/issues/149) |
| 2 | A scripted text replacement that matches nothing must fail, not report success | approve | [#150](https://github.com/topij/agentic-dev-kit/issues/150) |
| 3 | The verification a run writes about itself outweighs the work it verifies | approve | comment on #120 |
| 4 | A check whose heading is larger than its assertion reads as coverage | approve | comment on #138 |
| 5 | The block-integrity check was an unanchored substring test | approve | comment on #127 |
| 6 | `#75` reproduced on 14 of 14 lens launches | approve | comment on #75 |
| 7 | A closing keyword in a squash message acted on an issue documenting an unfixed defect | approve | comment on #71 |
| 8 | CodeRabbit registered nothing on a sixth and seventh consecutive PR | approve | comment on #45 |
| 9 | `#113` has a latent instance in a state path, not just a branch name | approve | comment on #113 |

**Proposal 8 was amended after approval, the amendment was wrong, and both panel lenses caught
it independently.** The operator's actual remark was narrow: CodeRabbit is *currently* not
available here, it is in use on `cs-toolkit`, and — the load-bearing part, which stands — its
absence **should not generate friction, because the fallback panel exists**. What reached the
`#45` comment was an inflation of that into *"not installed, never exercised, nothing
rate-limited, no credit run out."* `#45`'s own body records a **Pro Plus** plan for this repo, and
CodeRabbit has both reviewed PRs here and posted many `Review limit reached` notices, the last
activity of any kind being `2026-07-28T04:35:09Z` on `#101`. One `gh api` call establishes that —
exactly what [#140](https://github.com/topij/agentic-dev-kit/issues/140) asks for before writing
*"X is not available here."*

The inflation was then used to file a **structurally-never** verdict onto `#45`, whose subject is
that structurally-absent and merely-pending are indistinguishable — committing that issue's own
confusion, on that issue. Corrected in place with both retractions visible: a **second** round
found the correction had over-claimed in the opposite direction, and independent attempts to count
how many PRs CodeRabbit actually *reviewed* (as against was refused for quota) returned different
answers. So no such count appears here. That irreducibility is the better evidence for `#45` than
any of the numbers were: from the outside, a twelve-PR silence is not distinguishable from
removal, quota exhaustion, or an infinite queue, and two successive careful readings got it wrong
in opposite directions. The swept entry's *"sixth and seventh consecutive"* is separately an
undercount — `#102`, `#103`, `#104`, `#111`, `#148` also carry nothing, making it **twelve**, the
third undercount in that series. The archive keeps the original wording; it is a verbatim record.

#### What was verified, and what was not

The six checks and their output are published on the PR. **Read them there rather than trusting a
summary here** — three review rounds went to this section in the 2026-07-28 sweep and two more
went to it here, every one finding the prose claiming more than the checks did. This version
states less on purpose; the earlier sweeps' remedy for the same loop was deletion, not a further
correction.

**What the checks establish.** The snapshot digest reconstructs from `0b82ff2`. The archived
block, un-demoted, matches the snapshot modulo one trailing newline (hence `15,839` in the output
against `15,840` here). The prior archive body is preserved byte-for-byte. `#149` and `#150` exist
and are OPEN. Each of `#120`/`#138`/`#127`/`#75`/`#71`/`#45`/`#113` carries exactly one comment
from this run, and its body hashes to the text this run sent. The live log holds one bullet.
`1 + 6 = 7` against the 7 parsed bullets.

**What they do not.** Several check *headings* on the PR name more than their bodies assert —
issue titles and labels are printed but not compared, and the bullet count has no notion of
"swept", so a restored swept entry would pass it. A reviewer demonstrated both, and demonstrated
that checks 1 and 2 share no trust chain: the snapshot's text field is never hashed, so a forged
snapshot produces byte-identical output. These are named rather than fixed — building a better
harness inside a fix round is the mechanism-creep the panel doctrine warns against, and `#138` and
`#127`, which ask for exactly that harness, both stay open. The content check is also the one
thing here a third party cannot re-run: its right-hand side is a local file. Nothing verifies that
the approval happened as described, and nothing here proves any posted comment is *true* — the
`#45` amendment above was caught by a reviewer, not by a check. No automated gate covers any of it
([#127](https://github.com/topij/agentic-dev-kit/issues/127)).

The swept entries now live in the archive, under the section `Graduated 2026-07-29`.

### 2026-07-29 (post-sweep)

- **The sweep re-derived `#121` from scratch without noticing it existed, and got two things
  wrong that `#121` would have corrected.** [#121](https://github.com/topij/agentic-dev-kit/issues/121)
  is OPEN, filed by the *previous* run of this workflow, and already covers `tracker.backend:
  linear` with blank `linear.*` ids, the placeholder `tracker.project_name`, and `notify.user_key`
  (routed onward to `#128`) — closing by asking whether any *other* block is still unstamped
  placeholder, the question this entry then asked again a day later as though it were new. The
  first draft claimed each instance "has been paid for separately" and that the placeholders carry
  "no comment saying they are stale". Both false; `#121` is the comment. A panel lens found it.
  The one key not in `#121`, `review.bots: [coderabbit]`, turned out to need no fix at all: the
  draft called the bot "not installed on this repo", which the marker above retracts, so the value
  is **accurate**. **M** — proposed fix, narrowed to what survives: `#121` should absorb the
  remaining question, which is not "these values are wrong" but *which* of this config is template
  and which is live, and how a reader could tell. `paths.*` carries a six-line comment explaining
  why **this repo** deviates; `tracker.*` and `notify.*` carry only schema hints (`# linear |
  github-issues | jira | none`, `# a key into your project's own notify config`) that say nothing
  either way — so a placeholder and a deliberate value are typographically identical. (The first
  draft of this sentence said those keys "carry no comment", which a lens refuted; they do, just
  not comments that answer the question.)
  Separately, and independent of any value: `review.bots` cannot express *"expected, currently
  silent, panel is the pass"* — `#45`'s subject, on which this sweep spent a HIGH. **Not from the
  swept inbox:** surfaced during pre-flight, recorded on operator instruction, and
  rewritten after review; it sits below the marker for the next pass, where it should be merged
  into `#121` rather than filed fresh.
- **An operator's remark was widened into a stronger claim and published as operator-confirmed —
  on five surfaces, including the tracker.** *"CodeRabbit is currently not available here"* became
  *"not installed, never exercised, nothing rate-limited, no credit run out"*, which was then used
  to file a **structurally-never-reviews** verdict onto `#45` — the issue whose whole subject is
  that such a verdict cannot be made from outside. Both panel lenses caught it independently. **H**
  — proposed remedy: `#140` asks for the command behind *"X is not available here"*; it needs widening
  to cover the positive form too, and a remark attributed to the operator should be quoted at its
  original scope rather than paraphrased into its implications. Distinct from `#149`: that one asks
  a correction to reach every surface, this asks the claim not to exceed its source in the first
  place.
- **Correcting a wrong number with a precise one failed twice, because the number is not
  recoverable.** The fix above asserted a review count that was really a count of bot comments; a
  second round caught it, and two independent re-derivations of "how many PRs did CodeRabbit
  actually review" then disagreed with each other — *reviewed* vs *quota-refused* vs *silent* is
  not separable from the comment stream without deciding what counts. **M** — proposed fix:
  withdrawing the count was the only stable move, and the irreducibility is better evidence for
  `#45` than any count. Occurrence data for `#45`, and an argument that a machine-readable reviewer
  state is the actual fix.
- **A check that errored reported a pass, inside the step guarding `#71`.** The closing-keyword
  scan used a `grep -E` alternation with an empty branch; `ugrep` rejected it, exited non-zero, and
  the `|| echo clean` branch fired. A later run of the rewritten scan read a **zero-byte** surface
  (nothing staged) and also reported clean. **M** — occurrence data for `#150`, and a scope note:
  `#150` is written for text *replacements*, and both instances here are *scans*. The durable form
  is that any check must assert it examined something — a match count, a byte count, an explicit
  failure — and `|| <success message>` must never follow a command that can fail for reasons other
  than the condition being tested. **Third instance, same session, different mechanism:** the
  rewritten scan's own regex required the keyword and the reference to be adjacent modulo
  whitespace, so it silently missed the same keyword followed by a **backtick-wrapped** reference —
  the code-span form `CLAUDE.md` explicitly names and the archive already records firing against
  `#61`. (Written as prose, not quoted: quoting it puts the live construction into an inbox entry a
  future sweep will paste into an issue body.) It was caught only because the same
  text appeared *without* backticks on another surface. A guard written from memory of a rule
  reproduced the rule's headline and dropped its stated exception.
- **The wrap-up reinstated a correction that had merged forty minutes earlier.** `#151`'s review
  changed "third sweep" to "fifth" on every surface it reached, and the handoff written immediately
  after called it *"the third sweep"* again — in a heading, the `Last updated` line, the commit
  subject, the PR title and the PR body — while the same block said "Fifth sweep overall" three
  lines below. Two lenses caught it. **M** — occurrence data for `#149`, and a sharpening of it: the
  six surfaces `#149` enumerates are the ones a claim *was* published to, which is the wrong
  frame for this failure. The handoff was written from the session's memory rather than from the
  merged artifact, so the corrected value never entered the drafting at all. The remedy is narrower
  than "enumerate surfaces" — **when a session's own review changed a fact, the wrap-up must source
  that fact from the merged text, not from recollection of the session.**

## Graduated 2026-07-29 — GitHub Issues (#149–#150)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet). Seven entries in,
seven accounted for: **one graduated** into two new issues, **six** routed as seven occurrence
comments on the seven issues they are evidence for.

Both one-into-two counts are deliberate, not miscounts. The correction-propagation entry split
into `#149` (enumerate a corrected claim's surfaces) and `#150` (a scripted replacement that
matches nothing must fail) because those are separable mechanisms; the check-heading entry
produced comments on both `#138` (the routing check's heading) and `#127` (the block-integrity
check's substring test) because it names two distinct checks.

The two blocks below are the swept text, verbatim, with headings demoted one level. The first is
the previous sweep's graduation marker; the second is the session block that accumulated after
it. The live log's marker for this sweep — which carries the approval record and the
verification statement, per `#128` — is in `kit-friction-log.md`, not here.

### 2026-07-28 (second sweep) — Backlog migrated to GitHub Issues (#138–#143)

The inbox was swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine
tracked in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Fourteen entries in, fourteen accounted for:** seven graduated into six new issues
([#138](https://github.com/topij/agentic-dev-kit/issues/138)–[#143](https://github.com/topij/agentic-dev-kit/issues/143)),
seven routed as five occurrence comments (`#45` ×2 entries, `#113` ×2, `#75`, `#73`, `#120`).

Two reconciliations, stated rather than left to a reader — mis-stating exactly these is what
`#138` was filed for: seven graduated entries became **six** issues because the `pr_watch` 403
defect was recorded in two sessions and both entries went to
[#139](https://github.com/topij/agentic-dev-kit/issues/139); seven routed entries became **five**
comments because `#45` and `#113` each carry two.

`#23` is named as a routing target by the swept text and received nothing **from this sweep** —
it is closed, and its occurrence data is consolidated on `#45`. It is not un-commented: it
carries the *previous* sweep's comment, posted `2026-07-28T13:46:17Z`, four minutes before `#126`
merged, after a panel caught that it had been omitted.

#### Approval record — in-session operator, no DM

This run was **interactive**, so the operator substituted for the DM review surface rather than
the stop being bypassed. [#128](https://github.com/topij/agentic-dev-kit/issues/128) asks that
such a substitute leave the approval record somewhere **committed**, since `state/` and
`reports/` are gitignored. This block is it. Approval was given up front and unconditionally —
*"I approve all suggestions"* — so every proposal carries the same decision and the
explicit-opt-in default was never exercised.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-28.json` (gitignored),
`sha256 b3a168a8ba8c18dc7d254fe76d1621b6ae5afff6d757540f1316c398643a6db7` over **14,341 bytes**
(14,235 characters; 54 non-ASCII — the digest is over the bytes). The snapshot is a *copy of a
committed blob*: the inbox at `06490a1` is that text, so the digest and every check in
the PR reproduce from `git` and `gh` alone, in any session.

| # | proposal (inbox entry, abridged) | decision | outcome |
| - | -------------------------------- | -------- | ------- |
| 1 | A routing list is a claim about tracker state, and nothing verifies it | approve | [#138](https://github.com/topij/agentic-dev-kit/issues/138) |
| 2 | `pr_watch.py`'s 403 blames the token, and neither the token nor the proxy's message is the problem | approve | [#139](https://github.com/topij/agentic-dev-kit/issues/139) |
| 3 | I filed a mechanism I had not tested, and it read as verified because it was specific | approve | [#140](https://github.com/topij/agentic-dev-kit/issues/140) |
| 4 | A rate-limited reviewer and an absent one are the same signal — fourth shape | approve | comment on #45 |
| 5 | `#113` reproduced as a setup condition, one day after being filed | approve | comment on #113 |
| 6 | The panel's worktree pointed at the wrong ref on 2 of 2 launches | approve | comment on #75 |
| 7 | `#73` gained an instance that is being kept on purpose | approve | comment on #73 |
| 8 | Four of the panel's ten findings were defects in the PR body, not the diff | approve | comment on #120 |
| 9 | A correct general argument was used to justify deleting instances it did not cover | approve | [#141](https://github.com/topij/agentic-dev-kit/issues/141) |
| 10 | `safety-critical-changes.md` rule 1 says to stop, not what to do when the change *is* the guard | approve | [#142](https://github.com/topij/agentic-dev-kit/issues/142) |
| 11 | `pr_watch.py:687` still discards the 403 body — needs a ticket | approve | [#139](https://github.com/topij/agentic-dev-kit/issues/139) (with 2) |
| 12 | `session-start`'s tracker step overflows its own tool limit at 68 open issues | approve | [#143](https://github.com/topij/agentic-dev-kit/issues/143) |
| 13 | CodeRabbit registered nothing on a fourth consecutive PR | approve | comment on #45 (with 4) |
| 14 | `#113` reproduced a third time | approve | comment on #113 (with 5) |

#### What was verified, and what was not

The full six-check script and its unedited output are in PR
[#144](https://github.com/topij/agentic-dev-kit/pull/144). Summarised honestly, because two
review rounds went to this block and both found the summary claiming more than the checks did:

**Established.** The snapshot digest reconstructs from `06490a1`. All three swept blocks appear
in the archive verbatim modulo heading demotion, are **absent from the pre-change archive**, and
appear **exactly once**; zero entry bullets remain in this file; the prior archive body is
preserved. `#138`–`#143` exist, are OPEN, are authored by this account, and their titles contain
the expected fragments. Each of `#45`/`#113`/`#75`/`#73`/`#120` carries exactly one comment from
this run, matched by **author and timestamp**. `#23` is CLOSED and carries nothing from this run
(it has three comments overall, the latest being the previous sweep's). `7 + 7 = 14` against the
14 parsed bullets.

**Not established, and worth naming.** The comment checks assert existence, not *content* — a
correct comment posted to the wrong issue would pass. The block-presence check is a substring
test over the whole archive; an adversarial lens showed it passes against an archive whose
visible text is destroyed while the real bytes hide in an HTML comment, so it rules out "archived
nothing", not "archived the wrong bytes". Nothing verifies that the approval happened as
described, or that the proposals shown were the proposals drafted — that is what the DM thread
would have carried. And no automated gate covers any of it
([#127](https://github.com/topij/agentic-dev-kit/issues/127)): a lens deleted a whole swept block
from the archive and `make mutation-test`, `check_doc_budget` and `kit_doctor` all stayed green.

The swept entries now live in `kit-friction-log-archive.md`, under the section
`Graduated 2026-07-28 (second sweep)`.

*(On that sentence, which took four tries. Three earlier versions carried a relative link to the
archive; the third also claimed to be "named, not linked" while doing so, and a lens caught the
contradiction. The link is now gone — but removing it is a smaller fix than it looked.
[#73](https://github.com/topij/agentic-dev-kit/issues/73)'s two recorded occurrences are both
**prose**, not markdown links: a sentence pointing "above" or naming another file, which stops
being true once the block moves. So the sentence above is still a latent instance — it names a
file it will sit inside after the next sweep. What removing the link actually bought is that it
will not also be a broken clickable target. Recorded rather than papered over, because two
versions of this parenthetical over-claimed the mitigation.)*

### 2026-07-29 (session spanning from 2026-07-28)

- **A correction applied to one copy of a claim, while the same claim stands on other surfaces,
  was the dominant defect shape — four rounds running, on the same PR.** Round 1 found a false
  `#23` sentence; it was rewritten in `docs/kit-friction-log.md`. Round 2 found the identical
  sentence still published on `#45`'s occurrence comment — and that the round had amended `#73`'s
  comment for a LOW in the same window, so the ability was there and the HIGH was the one missed.
  Round 3 found the same claim still live in **`#140`'s issue body**. Round 4 found a round-3 fix
  that had *silently matched nothing* (the target phrase wraps mid-sentence, the anchor assumed one
  line) while its commit message reported it as landed. Each round fixed the surface it was pointed
  at. **M** — proposed fix: when a claim is corrected, enumerate the surfaces it was published to
  *at that moment*, rather than discovering them one review at a time. For this workflow the set is
  fixed and short: the live log, the archive, the issue bodies the run filed, the occurrence
  comments the run posted, the PR body, the commit messages. Distinct from `#138`, which asks the
  *routing* to be verified — this asks a *correction* to be propagated. The silent-no-op half also
  argues that a scripted text replacement should assert it changed something.
- **The verification a run writes about itself is a bigger defect source than the work it
  verifies.** Across eight panel rounds and at least fifteen isolated lenses on three PRs, **no
  HIGH was in executable behaviour** — every one was in prose. Some of that prose lives inside
  `.py`/`.sh` files (a module docstring, a `# Requires:` header), so "prose" means wherever it
  lives, not "outside the source tree". The sweep moved exactly the right bytes on its first
  commit and no round ever found otherwise; three rounds went to the record describing it. The
  documentation audit's edits were almost all correct; three rounds went to its evidence for them.

  **Three of the HIGHs were in prose that *ships*** — the class worth separating, because these
  would reach an adopter: `pr-watch.md`'s flag table (it described `--assert-draft`/`--assert-ready`
  as read-only checks when they issue `gh pr ready`, so following it flips a deliberately drafted
  PR to ready), `devmodel_config.py`'s module docstring, and the `init.sh` prerequisite list, which
  was wrong on **two** surfaces at once (`init.sh`'s own header *and* `README.md`).

  The mechanism is now visible: each correction round *adds prose*, and added prose is where the
  next round's findings live. What broke the cycle was **deleting** the elaborate verification
  transcript rather than correcting it a third time — the file went 141 → 93 lines and the defect
  surface went with it. **No new fix proposed** — occurrence data for `#120`, with the
  deletion-beats-correction observation attached.
- **A check whose heading is larger than its assertion reads as coverage.** The sweep's routing
  check was headed *"every claimed comment exists on the issue it claims"* while asserting only
  existence, author and timestamp — never content, so a comment carrying a falsehood passes (which
  is exactly how the `#23` HIGH survived into round 2). Its block-integrity check was an unanchored
  substring test: a lens built an archive whose visible text is `CORRUPTED` ×200 with the real bytes
  hidden in an HTML comment at EOF, and **the check passed**. Both headings needed two rewrites to
  match what the code does. **No new fix proposed** — occurrence data for `#138` (routing) and
  `#127` (integrity). `#138` was filed by this session; `#127` was filed two sessions back
  (`2026-07-28T13:46:49Z`, during `#126`'s review — the inbox-graduation session, not the
  mutation-gate one between it and this). Both were reproduced inside this session's
  pilot run of the checks they ask for.
- **`#75` reproduced on 14 of 14 lens launches.** Every isolated reviewer was placed in a worktree
  at `main` with an empty `git diff main...HEAD`, across three PRs and eight rounds. Every one
  detected it and fetched the real head, because the launch prompt required reporting path, sha and
  diffstat *before* reviewing. Largest set recorded, and unanimous. **No new fix proposed** —
  occurrence data for `#75`, but at 14/14 the contract item should stop saying "verify" and start
  saying "assume wrong, fetch first".
- **A closing keyword in a squash message closed an issue documenting an unfixed defect — and
  the check that cleared it could not see the surface that fired.** `#147`'s squash message read
  *"Filed rather than fixed:"* followed directly by the two references. GitHub matched the
  keyword immediately preceding the first and closed it when `030f053` landed: `gh api …/issues/145/events` returns
  `event=closed commit_id=030f053`, and `commit_id` is populated only when a commit triggers the
  close. The sentence was asserting the **opposite**. `#146`, filed the same way in the same
  sentence, survived because no keyword happened to sit next to it. Reopened by hand.

  Two separate failures, and the second is the interesting one:

  1. **The scan never ran on the surface that mattered.** A `close|fix|resolve`-adjacent-to-`#N`
     scan was run on every PR body and on the added lines of every diff this session. A squash
     message is composed at merge time, after every other gate has passed, and was never scanned.
     `CLAUDE.md` names it explicitly; the habit did not.
  2. **The clearing check was structurally blind.** This entry's first version reported the
     incident as a near-miss — *"no `closingIssuesReferences` were created (verified on both
     PRs)"*. That field is derived from the **PR body** and cannot see a commit message, so it
     returns `[]` whether or not a squash message fired. The verification was aimed at the wrong
     surface and returned a confident, meaningless pass.

  Separately and more mildly: on one invocation the scan and the `gh pr edit` were chained in a
  single shell command, so the edit published regardless of what the scan found. That one *was*
  a near-miss — it found a `closed` adjacent to a reference in a PR body, and the body was
  corrected. **M** — proposed fix: this is `#71`, and the instance sharpens where its guard must
  live and what it must read. A scan the author can sequence after the thing it guards is not a
  guard; and any "no harm done" check must read the issue's own **event stream**
  (`gh api repos/:o/:r/issues/N/events`, looking for `closed` with a non-null `commit_id`), not a
  PR-body-derived field. Second occurrence — the archive already records the same keyword firing from
  an inline code span in a commit message against `#61` — and the first where the checking was also wrong.
- **CodeRabbit registered nothing on a sixth and seventh consecutive PR.** `#126`, `#129`, `#130`,
  `#131`, `#137`, `#144`, `#147` — no check row, no comment, past grace on every one. The fallback
  panel was the only independent pass throughout. The occurrence comment recording this pattern was
  itself posted with an undercount ("four consecutive"), eight minutes after the fifth instance
  merged. **No new fix proposed** — occurrence data for `#45`.
- **`#113` has a latent instance in a state path, not just a branch name.** This session ran a
  *second* sweep on a date that already had one, so `chore/triage-{date}` and
  `state/triage/frozen-inbox_{date}.json` were both candidates to collide. **Neither actually
  did**, and for the same reason: the first sweep ran on `claude/triage-friction-log-kabrzh`
  (`gh pr view 126 --json headRefName`) and wrote no snapshot at all, so the default branch name
  was never taken either. The branch was renamed by hand against a collision that was not there. **No data was lost** — `stat`
  reports `frozen-inbox_2026-07-28.json` with `created == modified == Jul 28 23:14:44`, this
  session's write, and only the `2026-07-27` file predates it, because the first sweep never wrote
  a snapshot at all. **M** — proposed fix: `#113` should cover date-patterned *state* paths as well
  as branch names. The hazard is latent only because the engine that would have written the first
  snapshot is not vendored (`#6`); once it is, a same-day re-run silently overwrites the artifact
  the previous run's audit trail depends on. *(Recorded as latent after checking. The first draft of
  this entry asserted the overwrite had happened — inferred from the shared path, with no command
  run. One `stat` refuted it. That is `#140`'s shape, in the session that filed `#140`, caught this
  time because the entry was checked before being committed rather than after.)*

## Graduated 2026-07-28 (second sweep) — GitHub Issues (#138–#143)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked
in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet). This is
the **second** sweep dated 2026-07-28. The first is the next `## Graduated` section,
`## Graduated 2026-07-28 — GitHub Issues (#112–#125)`. Do not mistake it for the nearer
`### 2026-07-28 — Backlog migrated to GitHub Issues (#112–#125)` inside *this* section —
same issue range, different heading, and that one is the first sweep's marker swept out of
the live log by this one. This sweep graduates the two session blocks that accumulated
after it.

Fourteen entries in, fourteen accounted for: **seven graduated** into six new issues,
**seven** routed as occurrence comments on the five issues they are evidence for. The
seven-into-six is not a miscount — the `pr_watch` 403 defect was recorded twice, in the
second and fourth sessions of the day, and both entries graduated into
[#139](https://github.com/topij/agentic-dev-kit/issues/139).

The six graduated issues:

- [#138](https://github.com/topij/agentic-dev-kit/issues/138) — a graduation record's
  routing claims are unverified; the tracker must be re-read **after** the writes land.
  Filed from the entry describing how the previous sweep's own record was wrong twice.
- [#139](https://github.com/topij/agentic-dev-kit/issues/139) — `pr_watch.py:687`
  discards the 403 body and asserts a cause it cannot know. *Two occurrences.* The body
  is evidence to show the operator, not an instruction to follow: in a web container the
  proxy synthesises a 403 naming an org admin that a personal repo does not have.
- [#140](https://github.com/topij/agentic-dev-kit/issues/140) — extend
  [#54](https://github.com/topij/agentic-dev-kit/issues/54)'s rule to **mechanism**
  claims. *Two instances, the second inside the correction of the first. Neither shipped
  in `#126` — `git show 2d99593:docs/kit-friction-log.md` contains neither; instance 1 was
  written and caught within one session and never reached `main`, and instance 2 shipped
  in `#129` and was corrected by `#130`. What ran across consecutive sessions is the
  catching.*
- [#141](https://github.com/topij/agentic-dev-kit/issues/141) — the removal enumeration
  in [#56](https://github.com/topij/agentic-dev-kit/issues/56) must be per-item and
  **executed**, not a correct category judgement applied to a group that differs in
  exactly the property the judgement turns on.
- [#142](https://github.com/topij/agentic-dev-kit/issues/142) — add a **counterfactual**
  step to the panel contract for any round that removes a guard. Restore it and measure;
  do not reason about whether it was load-bearing.
- [#143](https://github.com/topij/agentic-dev-kit/issues/143) — `session-start`'s tracker
  step overflows its tool limit at 68 open issues, and the field-limited call it
  prescribes is impossible on GitHub-Issues-over-MCP.

The seven routed entries became five comments: `#45` (two entries — the fourth shape of
reviewer absence, and four consecutive PRs with no check and no comment), `#113` (two
entries — the second and third reproductions), `#75`, `#73`, and `#120`. `#23` is named
as a routing target by the swept text and deliberately received nothing **from this
sweep**: it is closed, and its occurrence data was consolidated on `#45`. It is not
un-commented — it carries the *previous* sweep's occurrence comment, posted
`2026-07-28T13:46:17Z`, four minutes before `#126` merged.

The approval record for this sweep — proposals, decisions, frozen-snapshot digest, and
the post-write verification — lives in **this sweep's graduation marker**, headed
`2026-07-28 (second sweep) — Backlog migrated to GitHub Issues (#138–#143)`, per
[#128](https://github.com/topij/agentic-dev-kit/issues/128). That marker is in
`kit-friction-log.md` while this is the newest sweep, and moves into this file as a `###`
block when the next sweep runs — so it is named here rather than linked. A relative link
would have been a [#73](https://github.com/topij/agentic-dev-kit/issues/73) break authored
by hand, in the record that reports on #73; the "leave it byte-identical" argument covers
*swept* text, not text this commit wrote itself.

### 2026-07-28 — Backlog migrated to GitHub Issues (#112–#125)

The inbox was swept by the `triage-friction-log` workflow. Twenty-four entries in,
twenty-four accounted for: **thirteen graduated** into new issues
([#112](https://github.com/topij/agentic-dev-kit/issues/112)–[#120](https://github.com/topij/agentic-dev-kit/issues/120),
[#122](https://github.com/topij/agentic-dev-kit/issues/122)–[#125](https://github.com/topij/agentic-dev-kit/issues/125)),
**ten** routed as occurrence comments on the issues they are evidence for
(#42, #45 ×3, #54, #74 ×2, #75, #76, #118), and **one** — `make test` being
undiscoverable — recorded as **discharged**, its proposed root `CLAUDE.md` having since
landed. `13 + 10 + 1 = 24`.

[#121](https://github.com/topij/agentic-dev-kit/issues/121) sits inside that numeric
range but came from the sweep itself rather than the inbox: this repo's `tracker:` config
is still `init.sh` placeholder pointing at Linear. #33 also received a comment, but a
cross-reference to #112 rather than one of the ten — see the archive for why that
distinction cost this record an audit.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-28 (second session of the day)

- **A routing list is a claim about tracker state, and nothing verifies it before it is
  committed.** The `#126` sweep's record asserted where each un-graduated entry went. Two
  of those assertions were false at commit time: `#33` was listed among the ten occurrence
  comments when it had received a cross-reference about a *graduated* entry (making the
  list sum to eleven against a stated ten, so "24 in, 24 out" audited to 25), and `#23`
  was named as a routing target by three entries **and by the comment posted to `#45`**
  while receiving nothing at all. Both survived the sweep, the commit, and CI; both were
  caught only by the fallback panel, independently, and the miscount was the panel's only
  HIGH. **M** — proposed fix: before writing the graduation record, re-read the tracker
  and assert that every claimed comment exists on the issue it claims; a routing table is
  cheap to generate and currently impossible to trust. Distinct from `#54` (which asks a
  claim to name its command) — here the claim is about a remote system's state, and the
  verifying command has to run *after* the writes.
- **`pr_watch.py`'s 403 blames the token, and the token is not the problem — but neither
  is the message the proxy substitutes.** *(Corrected 2026-07-28, third session — the
  version committed in `#126` got the diagnosis right and the remedy wrong. Every claim
  below was established by running the command shown, in this container, before editing.)*
  `uv run scripts/pr_watch.py 126` exits with *"403 Forbidden — the token may lack `repo`
  scope or have expired"*. Both halves of that are wrong here, and so is taking the
  proxy's reply at face value:
  - **The tokens are set, and they are not GitHub credentials.** `GH_TOKEN` and
    `GITHUB_TOKEN` are both present in a Claude-Code-on-the-web container and both are a
    14-character proxy sentinel (`prox…`) — established by
    `python3 -c "import os; print(len(os.environ['GH_TOKEN']), os.environ['GH_TOKEN'][:4])"`
    → `14 prox`.
  - **The proxy injects a real, working credential — GitHub *is* connected.**
    `curl -H "Authorization: Bearer $GH_TOKEN" https://api.github.com/user` returns `200`
    with login `topij`, id `5101841`. The *same request with no `Authorization` header at
    all* also returns `200` with the same identity, so the sentinel is not what
    authenticates — the proxy attaches auth on the way out regardless of what the client
    sends.
  - **The block is a path allowlist, not a credential or permission problem.**
    `https://api.github.com/repos/topij/agentic-dev-kit` returns `403` **with** the
    sentinel and `403` **without** any auth header, and the public, unauthenticated
    `/octocat` returns `403` too. Identity is fine on `/user` and refused on `/repos/*`;
    only the path differs.
  - **The 403 is synthesized by Anthropic's proxy, not returned by GitHub.** Its
    `documentation_url` is `https://docs.anthropic.com/en/docs/claude-code/github-actions`.
  - **Its message is a canned string that does not describe this situation.** It reads
    *"GitHub access is not enabled for this session. An org admin must connect the Claude
    GitHub App for this organization."* Access **is** enabled — the GitHub MCP
    (`mcp__github__*`) reads and writes this repo in the same session — and
    `topij/agentic-dev-kit` is a personal repo with no organization and no org admin, so
    the prescribed action does not exist. The proxy's two 403 bodies also contradict each
    other: `/octocat` answers *"use repository-scoped endpoints
    (`repos/{owner}/{repo}/...`)"*, which is the exact path that returns the org-admin
    message. **Do not send the operator to org settings on the strength of this body.**
  - **Git is unaffected** because `git` goes through a **separate** local git proxy
    (`git remote -v` → `http://local_proxy@127.0.0.1:41729/git/topij/agentic-dev-kit`),
    which is why every push and fetch succeeded while the REST API was refused.

  **M** — proposed fix, two parts: (1) surface the response body on a 403 instead of
  asserting a cause the engine cannot know (`scripts/pr_watch.py:687`) — the body is
  **evidence to show the operator, not an instruction to follow**, and this correction is
  the reason that distinction is worth writing down; (2) decide whether the REST transport
  should detect the proxy sentinel and name the GitHub MCP as the supported path, since
  `#96`'s premise — "no `gh`, so talk REST" — does not hold when the blocked thing is the
  API host rather than the CLI. **Installing `gh` would not help**: it reads the same
  sentinel and takes the same route.
- **I filed a mechanism I had not tested, and it read as verified because it was
  specific.** The first version of the entry above stated that "the GitHub credential
  lives in the MCP server and is never exposed to the container". That is false —
  `GH_TOKEN` is set, and one `env | grep` would have shown it. The claim was inferred
  from `pr_watch`'s own error text plus the fact that MCP calls worked, and it was written
  with enough circumstantial detail to pass for a finding. It survived a fallback panel
  (both lenses reviewed the diff carrying it), CI, and my own review; it was caught only
  because the operator asked an unrelated question — *"what if we install `gh`?"* — that
  happened to require testing the claim. **M** — proposed fix: `#54`'s rule should extend
  to *mechanism* claims, not just verification claims. "X is not available in this
  environment" is a testable assertion and needs the command that establishes it in the
  same way a passing test does. Related to the routing-list entry above: both are claims
  about a system outside the repo that nothing in the workflow checks before they are
  committed.

  **Second instance, same entry, caught the next session.** The *corrected* version — the
  one that shipped in `#126` — still carried an untested claim: that the proxy's 403 body
  "says exactly what to do". It does not; it is a canned string naming an org admin who
  does not exist for this repo, and one `curl https://api.github.com/user` (no auth
  header) would have shown that GitHub access was enabled the whole time. The first
  version failed by inferring a mechanism from an error message; the second failed by
  *believing* one. Both were specific enough to read as verified, both survived the panel
  and CI, and both were corrected only because the operator went and ran the commands.
  That strengthens the proposed fix rather than changing it: the rule has to bind to any
  claim about the environment, including one quoted from the environment itself.
- **A rate-limited reviewer and an absent one are still the same signal — fourth shape.**
  On `#126` CodeRabbit registered **no check and no comment at all**, well past
  `bot_pending_grace_minutes: 15`. Not a false green, not a rate-limit notice, not a
  pending check. The three shapes recorded before this all left *something* on the PR;
  this one leaves the PR indistinguishable from one whose reviewer simply has not started.
  Nothing but an operator's judgement stopped a silent merge. **No new fix proposed** —
  occurrence data posted to `#45` and `#23`.
- **`#113` reproduced as a setup condition, one day after being filed.** This was a
  second session on 2026-07-28, so `chore/update-handoff-2026-07-28` already existed on
  the remote — the exact precondition that turned `#81` into a 160/249 revert. Avoided by
  branching off fresh `main` under a different name, i.e. by hand, because no mechanism
  exists yet. **No new fix proposed** — second occurrence for `#113`, and worth noting
  that the first occurrence caused damage while this one was caught only because the
  hazard had been filed hours earlier and was still in mind.
- **The panel's worktree pointed at the wrong ref on 2 of 2 launches**, both detected and
  corrected by the lens because the launch prompt required verify-before-review. Recording
  it as its own set: earlier sessions counted launches that isolated *correctly*, and this
  is the first set here where every launch was wrong, so the two cannot be summed. **No
  new fix proposed** — occurrence data for `#75`.
- **`#73` gained an instance that is being kept on purpose.** The swept text carries the
  previous sweep's closing line, *"Everything swept now lives in
  `kit-friction-log-archive.md`"*, which is now a self-link inside the archive it names.
  Left byte-identical because rewriting swept content would destroy the verbatim property
  that makes the archive auditable — so the sweep-warns-on-cross-references fix `#73`
  proposes needs a *warn*, not a rewrite. **No new fix proposed** — occurrence for `#73`,
  with that constraint attached.
- **Four of the panel's ten findings were defects in the PR body, not the diff** —
  including a verification claim that named no command, in the PR filing the issue about
  exactly that. Third consecutive session where the prose carried the errors and the code
  did not. **No new fix proposed** — occurrence data for `#120`, which proposes the
  cheaper message-only terminal check; three sessions of evidence now sit behind it.

### 2026-07-28 (fourth session of the day)

- **A correct general argument was used to justify deleting instances it did not cover,
  and the deletion opened the exact hole the change existed to close.** After three panel
  rounds walked through the same guard tests, the fix round deleted them on the argument
  that *"a text search over a file cannot be sound, because whoever edits it can read the
  search."* That argument is true. It did not apply to two of the three tests: they were
  built on `make -n`, which executes make and reads what it says it would run. With them
  gone, the `mutation-test` recipe silently losing `-m 'not driftcheck'` was observed by
  nothing (`make test` → 500 passed), and a behaviour-only mutation then reported a
  **kill** — `#33` restored inside the command built to escape it. Caught only because the
  next round's adversarial lens restored the deleted assertions into every bypass and
  watched them kill each one. **M** — proposed fix: when a fix round *removes* a
  mechanism, `#56` already asks for an enumeration of what it was rejecting; this says the
  enumeration must be **per-item and executed**, not a category judgement applied to a
  group. The deletion rationale here was written once and applied to three tests that
  differed in exactly the property the rationale turned on.
- **`safety-critical-changes.md` rule 1 tells you to stop, and does not say what to do
  instead when the change *is* a guard.** Four rounds, HIGHs every time, severity never
  below three. Rule 1 prescribes "a deterministic artifact" — but for a guard over an
  unbounded space of edits, the artifact is the thing under review. Stopping produced a
  deletion that was too broad; not stopping would have produced a fifth round. What
  actually resolved it was a reviewer running the *counterfactual* (restore the deleted
  code into each bypass), which no rule asks for. **M** — proposed fix: add a
  counterfactual step to the panel contract for any round that removes a guard — restore
  it and measure, rather than reasoning about whether it was load-bearing.
- **`pr_watch.py:687` still discards the 403 body and asserts a cause it cannot know.**
  `#130` corrected the *record* about this; the defect itself has no ticket. In a web
  container the whole API host is path-blocked, so `pr_watch` cannot arbitrate a merge
  gate at all — both of this session's merges were reconstructed from MCP calls by hand.
  **M** — proposed fix: surface the response body, and have the REST transport detect the
  proxy sentinel and name the GitHub MCP as the supported path. Needs a ticket.
- **`session-start`'s tracker step overflows its own tool limit at 68 open issues.** The
  MCP `list_issues` call returned 177k characters and had to be re-read from a spill file
  and field-filtered by hand. The workflow already warns that a naive "dump everything"
  call overflows, and prescribes a field-limited call — but the MCP tool exposes no field
  selection, so the prescription cannot be followed on this backend. **L** — proposed fix:
  the workflow's tracker step needs a backend-specific note for GitHub-Issues-over-MCP:
  page at `perPage: 25` and read `number`/`title`/`labels`/`state` only.
- **CodeRabbit registered nothing on a fourth consecutive PR.** `#126`, `#129`, `#130`,
  `#131` — no check, no comment, past grace on all four. The fallback panel was the only
  independent pass every time. **No new fix proposed** — occurrence data for `#45`/`#23`,
  now with four consecutive instances behind it rather than one.
- **`#113` reproduced a third time.** `chore/update-handoff-2026-07-28` already existed on
  the remote, so the wrap-up branched as `chore/wrap-up-2026-07-28-mutation-gate` by hand.
  **No new fix proposed** — third occurrence, still no mechanism.

## Graduated 2026-07-28 — GitHub Issues (#112–#125)

Swept by the `triage-friction-log` workflow, run in LLM-only mode (the engine tracked
in [#6](https://github.com/topij/agentic-dev-kit/issues/6) is not vendored yet).
Twenty-four entries in, twenty-four accounted for: **thirteen graduated** into new
issues, **ten** routed as occurrence comments on the issues they are evidence for, and
**one** discharged by work that has since landed.

The thirteen graduated entries became
[#112](https://github.com/topij/agentic-dev-kit/issues/112)–[#120](https://github.com/topij/agentic-dev-kit/issues/120)
and [#122](https://github.com/topij/agentic-dev-kit/issues/122)–[#125](https://github.com/topij/agentic-dev-kit/issues/125)
— [#121](https://github.com/topij/agentic-dev-kit/issues/121) sits inside that numeric
range but is not one of them (see below). Four of the twenty-four entries were rated
**H**; three of the four became issues:

- [#112](https://github.com/topij/agentic-dev-kit/issues/112) — the manifest-hash gate
  reads as test coverage but is discharged by one `--generate-manifest` run, so any
  mutation result on a `KIT_OWNED` file is void unless the manifest is regenerated
  first. Inverse symptom of [#33](https://github.com/topij/agentic-dev-kit/issues/33),
  cross-referenced there.
- [#113](https://github.com/topij/agentic-dev-kit/issues/113) — a push-then-PR step can
  open a PR against a stale remote branch and exit 0; this is how `#81` came to carry
  160 insertions / 249 deletions **against `main`**, reverting the day's merged work.
  (The qualifier matters: GitHub's own file view of `#81` reports a different figure,
  because it diffs against the merge base rather than against `main`.)
- [#114](https://github.com/topij/agentic-dev-kit/issues/114) — a test written from the
  fix's own framing can pin the bug as correct; the mutation was killed by that test.
- The fourth, **`make test` is undiscoverable**, is the one entry recorded as
  **discharged**: its proposed fix was a root `CLAUDE.md` naming `make test` as *the*
  verification command, and that file now exists and does exactly that. Verified by
  reading `CLAUDE.md` in this repo at commit `18768fc`.

[#121](https://github.com/topij/agentic-dev-kit/issues/121) was not an inbox entry — it
was surfaced *by running this workflow*: `config/dev-model.yaml`'s `tracker:` block is
still `init.sh` placeholder (`backend: linear`, blank ids) while this repo's real
tracker is GitHub Issues on itself, which the engine in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) will read the moment it lands.

The ten occurrence comments went to
[#42](https://github.com/topij/agentic-dev-kit/issues/42) (one entry),
[#45](https://github.com/topij/agentic-dev-kit/issues/45) (three),
[#54](https://github.com/topij/agentic-dev-kit/issues/54) (one),
[#74](https://github.com/topij/agentic-dev-kit/issues/74) (two),
[#75](https://github.com/topij/agentic-dev-kit/issues/75) (one),
[#76](https://github.com/topij/agentic-dev-kit/issues/76) (one), and
[#118](https://github.com/topij/agentic-dev-kit/issues/118) (one) — summing to ten, so
`13 + 10 + 1 = 24` closes.

Two clarifications the review panel forced, because the first version of this section
did not survive an audit:

- **[#33](https://github.com/topij/agentic-dev-kit/issues/33) is not in that list.** It
  received a *cross-reference* to #112 — a **graduated** entry, already counted among the
  thirteen — not occurrence data for any of the ten. Listing it made the enumeration sum
  to eleven against a stated ten, so `24` in produced `25` out.
- **Not all ten carried *"No new fix proposed"***. Five did; the rest (notably the
  entries routed to #54, #118 and #42) proposed a fix that belonged on an **existing**
  issue rather than a new one. Being comment-shaped rather than ticket-shaped is what
  they have in common, not the absence of a proposal.

Three of the twenty-four entries also named
[#23](https://github.com/topij/agentic-dev-kit/issues/23) alongside #45 as a routing
target; that comment was posted after the panel caught its omission.

The panel itself produced two further issues, neither from the inbox:
[#127](https://github.com/topij/agentic-dev-kit/issues/127) — nothing mechanically
distinguishes a sweep from a deletion, and `check_doc_budget` scores the deletion higher
(proved by wiping both files and watching every gate stay green) — and
[#128](https://github.com/topij/agentic-dev-kit/issues/128), the skill's notify-channel
stop having no in-session-operator exception, which this run violated.

All twenty-four entries are kept verbatim below for the trail, along with the prior
graduation marker. Note that the swept text includes the previous sweep's closing line,
*"Everything swept now lives in `kit-friction-log-archive.md`"*, which is now a self-link
inside the archive it names — the class [#73](https://github.com/topij/agentic-dev-kit/issues/73)
exists for. It is left byte-identical deliberately: rewriting swept content would break
the verbatim property that makes this archive auditable.

### 2026-07-27 — Backlog migrated to GitHub Issues (#70–#77)

The inbox was swept by the `triage-friction-log` workflow. Thirteen entries in,
thirteen accounted for: **twelve graduated** into eight issues, **one** recorded a
measurement with *"No change proposed"*.

Four issues each merge **two** entries recorded on separate days, because the repeat is
the evidence — splitting them would lose the occurrence count that made them
issue-shaped:

- [#70](https://github.com/topij/agentic-dev-kit/issues/70) — a mutation harness that
  restores outside `finally` leaves the repo mutated; the tree must be checked *after*
  the harness exits, not only after a successful run.
- [#71](https://github.com/topij/agentic-dev-kit/issues/71) — build the
  closing-keyword guard: every match, every surface, no stripping, and the squash
  message checked at merge time. *Three occurrences across two sessions.*
- [#72](https://github.com/topij/agentic-dev-kit/issues/72) — `pr-watch` should warn at
  push time when a bot review no longer covers head, not only at receipt time.
- [#73](https://github.com/topij/agentic-dev-kit/issues/73) — the archive sweep must
  warn on relative cross-references in **both** directions. *Two occurrences; the second
  broke a reference the first sweep had written.*
- [#74](https://github.com/topij/agentic-dev-kit/issues/74) — the doc-budget remedy is a
  no-op at the default `--keep` (it measures lines, the sweep keeps blocks). *Three
  occurrences, two in this repo.*
- [#75](https://github.com/topij/agentic-dev-kit/issues/75) — invert contract item 7:
  assume the isolated worktree points at the wrong ref. *Nine of nine across two
  sessions.*
- [#76](https://github.com/topij/agentic-dev-kit/issues/76) — `--record-review` cannot
  record honest partial coverage, so the honest choice erases the trail.
- [#77](https://github.com/topij/agentic-dev-kit/issues/77) — nothing constrains the
  cockpit from editing the shared tree while a panel reviews it.

The thirteenth entry — the panel-disjointness measurement — carried *"No change
proposed"*: it is a second, stronger data point for the disjointness argument in
`fallback-review-panel.md`, which currently rests on one.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-27

- **The kit has a working local test command and nothing points at it.** `make test`
  runs the full suite — **372 passed in 22s** — supplying its own dependencies via
  `uv run --with pytest --with pyyaml`. But the two probes an agent reaches for first
  both fail in a way that reads as *"pytest is unavailable in this environment"*:
  `uv run pytest` → `Failed to spawn: pytest`, `python3 -m pytest` → `No module named
  pytest`. **No markdown file in the repo mentions `make test`**, and there is no root
  `CLAUDE.md`. This session concluded the environment could not run tests, deferred
  verification to CI on two PRs, and wrote *"tests were not run locally — pytest is not
  installed"* into the body of a **merged** PR (`#80`); corrected afterwards by comment.
  **H** — proposed fix: a root `CLAUDE.md` naming `make test` as *the* verification
  command. `#54` requires every verification claim to name the command that establishes
  it, and that has no chance of holding while the only working command is undiscoverable.
  Same family as `#54`.
- **The `Makefile`'s `test` target claims a local gate that does not exist.** Its comment
  says the target *"Runs the same suites the lane contract's local gate runs before every
  push."* There is no such gate: `scripts/hooks/pre-push` deliberately runs no tests
  (line 23 — checks are kept separate and independently testable), and
  `scripts/dev_session.sh` runs none either. **M** — proposed fix: either correct the
  comment to describe what exists, or make it true by having `pre-push` run `make test`.
  The second is a design call, not a patch — `pre-push`'s own comment argues for keeping
  checks separate, and 22s lands on every push. Same family as `#54`: a comment claiming
  more than the code does.
- **The triage skill's default output is a PR its configured reviewer will never read.**
  `finalize.pr_draft` defaults to `true`, and CodeRabbit skips draft PRs outright
  (*"Review skipped: draft pull request"*). So `triage-friction-log`'s happy path
  produces a draft PR that receives no bot review, and nothing in the skill says so —
  the operator discovers it only when the review gate will not close. **M** — proposed
  fix: either default `pr_draft` to `false`, or have the skill state that a draft PR
  needs `@coderabbitai review` or a ready-flip before the review gate can be satisfied.
  Surfaced on `#78`.
- **The wrap-up branch name collides on a same-date session, and `gh pr create` turns
  the collision into a PR that reverts the day's merged work.** The handoff branch is
  `chore/update-handoff-{date}`, so a *second* session on the same date recreates an
  identical name off the current `main`. The push is correctly rejected as a
  non-fast-forward — but `gh pr create` then opens a PR against the **pre-existing
  remote branch**, exits 0, and prints a PR URL. `#81` was opened this way: it carried an
  earlier session's commits, cut from a base predating today's merges, so its diff was
  **160 insertions / 249 deletions against `main`** — un-graduating the friction inbox,
  deleting 186 lines of archive, and undoing the `reports/` work. Merging it would have
  reverted both PRs that landed earlier the same day. Caught only because the
  rejected-push hint and the PR URL landed in the same output and the head sha was then
  compared. **H** — proposed fix, two parts: (1) uniquify the wrap-up branch name (short
  sha suffix) or fail loudly when the remote branch already exists; (2) more general and
  more important — any workflow step that pushes and then opens a PR must **verify the
  push landed** before creating it. `git push -q && gh pr create` is not sufficient: with
  `-q` the rejection is a stderr hint, the exit status is swallowed by the chain, and the
  PR gets created against whatever the remote already had. Compare remote head to local
  `HEAD` first.
- **A rate-limited CodeRabbit reports its check as `pass` — two more instances.** `#78`
  and `#80` both merged with a green `CodeRabbit` check that had reviewed nothing
  (*"Review limit reached"* / *"Review rate limited"*). `pr_watch` handled both correctly
  — recorded `unavailable` and refused to converge on missing review evidence — so the
  engine is not the problem; the hazard is the **check rollup**, which reads as reviewed
  to any human scanning it. **No new fix proposed** — recording two further occurrences
  for `#45` / `#23`. `kit-handoff-history.md` records CodeRabbit rate-limiting in an
  earlier session too, so this is at least the third.

### 2026-07-27 (third session of the day)

- **`pr-watch` prescribes the fallback panel on ANY reviewer outage; a short rate-limit
  window makes re-triggering strictly better.** Recovery windows observed this session
  ranged from 13s to 48min across `#83`/`#85`/`#87`. When short, `@coderabbitai review`
  after the window produced a real review of the exact head — stronger evidence than a
  panel receipt, at zero cost. Neither `pr-watch.md` nor the workflow's
  reviewer-unavailable branch mentions the notice's "Next review available in" field or
  the re-trigger command. **M** — proposed fix: the reviewer-unavailable branch should
  read the recovery window from the outage notice; short window → wait and re-trigger,
  then fall back to the panel only if that fails; long window on a risky diff → run the
  panel now and offer the recovered bot the final head afterwards. The re-trigger half
  is validated (`#83`; `#85`'s recovered pass covered its full final diff); the
  offer-the-final-head half can still end in an acknowledged gap — `#87`'s last push
  rate-limited again and merged with the coverage gap recorded on the receipt.
- **`gh api -X PATCH … -f body=@-` writes the literal string `@-`, destroying the
  comment.** Only `-F` performs `@`-file/stdin expansion; `-f` is always a string. Three
  freshly-posted issue comments were clobbered to `@-` this session and caught only
  because a later edit re-read one. **L** — proposed fix: any workflow step that edits a
  GitHub comment via `gh api` should use `-F body=@<file>` and verify the comment's
  body length (or a content marker) after the PATCH.

### 2026-07-27 (fourth session of the day)

- **A test written from the fix's own framing can pin the bug as correct.** My
  `comparable_max_total` reset disabled the false-settle guard on the DEFAULT `gh`
  backend (`mergeable` false → **true** for every existing PR), and the test I wrote
  alongside it asserted `settling is False` / `converged is True` as the *desired*
  outcome. So the suite pinned the permissive direction and nothing pinned the guard —
  a mutation removing the reset was **killed by my own test**. Two review lenses found
  it independently; the suite could not, by construction. **H** — proposed fix: for a
  change to a gate, the test must assert the *blocking* direction survives, not that the
  new behaviour occurs. Worth a line in `safety-critical-changes.md`: when a fix changes
  what a guard concludes, pin the guard's refusal first and the fix's effect second.
- **`archive_plan_sessions.py`'s default `--keep 6` is a no-op remedy — fourth
  occurrence, third in this repo.** (The graduated-issue note above already records
  three, two here.) `check_doc_budget` warned at 470/400 lines and
  the sweep answered *"nothing to move: 6 session block(s) <= --keep 6"*, leaving the
  file over budget with the warning still firing. `--keep 4` moved 2 blocks and brought
  it to 314. This is `#74` exactly; recording the recurrence because the wrap-up workflow
  tells the operator to run the sweep and the sweep does nothing at its default.
  **M** — no new fix proposed beyond `#74`: the remedy should take the *budget* as input
  and drop blocks until it fits, rather than counting blocks.
- **Chaining `make test` into commit-and-push let me push a red tree.** I ran
  `make test && git commit && git push` as one compound command, `make test` failed on a
  stale manifest hash, and the failure scrolled past while the commit and push
  succeeded. CI on that head went red. **M** — proposed fix: the wrap-up and lane
  contracts should say verification runs as its **own** step whose result is read before
  anything is committed; a compound `&&` chain that ends in a push makes the failure
  invisible at exactly the moment it matters. Related to `#54` (name the command that
  established a claim) but distinct: here the command ran and its answer was ignored.
- **`--record-review` un-converges the PR it just certified, and the merge then needs a
  second `--mark-seen`.** Posting the coverage record made `converged` false (my own
  comment is a new comment), so `mergeable` went false with an *empty* `merge_blockers`
  list — which reads as "no reason" to anyone scanning it. Acking cleared it. This is
  `#42`; recording an occurrence plus the detail that the empty blocker list makes the
  cause unguessable from the JSON alone. **L**
- **The provided worktree was at the base ref on 5 of 5 panel launches this session**
  (`main`, empty diff), and every lens detected and corrected it because the launch
  prompt required clone-verify-report. **No cumulative figure claimed**: the earlier
  sessions' "8 of 8" counts launches that isolated *correctly*, so it cannot be added to
  a count of launches that pointed *wrong* — an easy error to make and worth not making
  in the record. **No new fix proposed** — occurrence data posted to `#75`.
- **CodeRabbit rate-limited three times in one session**, once still limited at merge
  time, and **its recovery-window figures are not retrievable afterwards** — it edits the
  rate-limit notice comment in place, so a window read live (41 minutes on `#91` this
  session) is overwritten by the next edit and cannot be audited later. That is the
  finding: every claim in this log about a recovery window is an ephemeral observation
  with no artifact behind it, which is why they keep failing verification. **L** —
  proposed fix: when the reviewer-unavailable branch reads the window, record the value
  and the timestamp on the PR, so the decision to wait-and-re-trigger versus run the
  panel is auditable. Supports the session-3 entry proposing that branch.

### 2026-07-28

- **A reviewer's plan quota is not a rate-limit window, and `unavailable_markers`
  cannot tell them apart.** CodeRabbit's notice read *"you've reached your PR review
  limit … Next review available in: 56 minutes"*, but re-triggering two minutes past
  that window produced nothing, and it never registered a check on the next PR either.
  The kit's reviewer-unavailable branch assumes a window you can wait out and re-trigger
  after — the session-3 entry above is built entirely on that assumption. A quota needs
  the panel immediately and no re-trigger attempt. **M** — proposed fix: distinguish the
  two in the unavailable branch; treat *"review limit reached"* as non-recoverable
  within the session rather than something to wait out.
- **A three-space list continuation is correct CommonMark and silently renumbers the
  list under Python-Markdown.** `1. ` is three columns, so three spaces is the
  CommonMark content column and GitHub rendered it correctly — Python-Markdown requires
  four and otherwise closes the list, emitting a fresh `<ol>` that restarts at 1. In
  `safety-critical-changes.md` that turned rule 4 into rule 1 while the header still
  said *"Four rules apply"*, and ten files outside the session records cite those rules
  by number (fourteen counting the records themselves). A bot review of
  that exact head passed it clean; rendering in both engines caught it. **M** — proposed
  fix: render kit-owned docs in both engines as a check, or fix the convention at
  four-space continuations and say so where the docs are edited.
- **A gate that reads labels nothing produces is not a gate.** `#102` shipped a rule
  keying on finding severity and a regression/imprecision axis — both lens *output* —
  when no contract item and neither `focus` string in `dev-model.yaml` ever asked a lens
  for either. It read as working only because the cockpit supplied severity ad hoc in
  its own launch prompts, which is exactly the drift the panel doc's single-source rule
  exists to prevent. Fixed in-PR (contract item 9), recorded because the *class* is
  general: any doctrine that consumes a field must name where the field is required.
  **M** — proposed fix, beyond `#102`: when a rule starts consuming a lens-reported
  field, the contract must be amended in the same change.
- **A rate-limited CodeRabbit reported its check as `SUCCESS` again** — on `#101`'s
  `4a0d499`. Correcting this entry as first merged, which got both attributions wrong.
  The false green did not sit on the defective diff: `4a0d499` is the head that *fixed*
  the indentation bug above, and the head that carried the bug (`d8bf1af`) received a
  genuine completed review that passed it clean — the next entry. Nor was it the first
  false green that could have shipped something: `#91`'s final head `d96d4a1` reported
  `SUCCESS` / *"Review rate limited"* while panel round 3 found ~7 HIGH against that
  exact head. **No new fix proposed** — occurrence data for `#45` / `#23`.
- **A fully working bot review missed a defect that renumbered doctrine.** `#101`'s
  first head `d8bf1af` — the one carrying the indentation bug — received a genuine,
  completed CodeRabbit review (walkthrough, five pre-merge checks passed) that
  reported it clean, while the defect turned rule 4 into rule 1 in a file ten others
  outside the session records cite by number. That is a worse failure mode than the
  rate-limited false green, which reviewed nothing: this review ran and vouched for
  the head. It was recorded
  nowhere — the entry above had attributed the miss to the rate-limited pass. **M** —
  no fix proposed beyond the render-in-both-engines check the indentation entry
  proposes; recorded so "bot reviewed and missed it" is not conflated with "bot never
  reviewed", which the occurrence data for `#45` / `#23` counts.
- **`#76` reproduced twice in one session.** Neither `#101` nor `#102` had its final
  head reviewed by any lens, and `--record-review --head` can only assert that the exact
  head was reviewed — so on both the honest choice was to record nothing and write the
  coverage table into a PR comment instead. Both merged with `mergeable: false` and an
  explicit operator decision. **No new fix proposed** — occurrence data for `#76`, with
  the detail that the honest path always forces an operator merge.
- **Deferred from `#102`, not yet issue-shaped**: the act-on gate has a fail-closed
  default for an ambiguous *change* but none for an ambiguous *finding*, and the party
  resolving that axis is the author who benefits from the cheaper answer (contract item
  9 now pushes it to the reporting end, which is a mitigation rather than a fix); the
  *"say which one you applied in the PR"* antecedent now has two candidates;
  `docs/CLAUDE-sections.md:116-118` enumerates the doctrine as five items for adopters
  to paste and is now incomplete; step 5 gains no forward pointer to the gate that
  narrows it; and class 2's worst-case test (*"a wrong message"*) fits a report field
  better than a doctrine file, which is acted on by every future author. **L**
- **The manifest-hash gate reads as test coverage and is not.** Three times this session
  a mutation to new behaviour was "caught" only by `test_kit_repo_self_check_is_clean`,
  which compares `kit-manifest.json` hashes. That gate is discharged by one documented
  command (`kit_doctor.py --generate-manifest`) — exactly what a real edit would run —
  after which the mutant is fully green. Any mutation result on a `KIT_OWNED` file is
  therefore meaningless unless the manifest is regenerated first, and a reviewer who
  skips that step will record a kill that did not happen. **H** — proposed fix: have the
  mutation-testing guidance (and `#33`, which already covers the false-kill direction)
  state the regenerate-first step as mandatory, and consider making `--generate-manifest`
  refuse to run against a tree with uncommitted engine edits so the discharge is visible.
- **A verification claim can be true, name a command, and still mislead through scope.**
  Two of this session's false claims survived because the command cited was narrower than
  the claim: `git status --porcelain docs/` supports "docs/ untouched" but was offered as
  evidence for "the only side effect is a root `AGENTS.md`", which the unscoped command
  disproves; and "fresh render in a scratch clone → all five docs seeded" omitted the
  `rm docs/kit-*.md` the run actually began with. `#54` requires naming the command; it
  does not require that the command's scope match the claim's scope. **M** — proposed
  fix: extend `#54` to "name the command *and* the setup it ran against", or require the
  claim to be restated as exactly what the command shows.
- **Panel rounds converge on the code long before they converge on the prose.** Round 5
  found zero code regressions after 4000 differential probes, while still returning six
  imprecisions in the commit message. Every round from 1 to 4 found a false claim in the
  previous round's fix, and none of those were in shipped behaviour — they were in
  descriptions of it. The current stopping criterion (blast radius) handles the code well
  and gives no guidance for prose, so the choice to stop was mine each time rather than
  the doctrine's. **M** — proposed fix: consider a separate, cheaper terminal check for
  record accuracy — one lens, message-only, run once before merge — rather than carrying
  prose review through every full round at full cost.
- **`#74` reproduced during this very wrap-up.** The budget check reported
  `docs/kit-handoff.md` at 463/400 and prescribed the archive sweep; the sweep at its
  default `--keep 6` reported *"nothing to move: 6 session block(s) <= --keep 6"* and the
  doc stayed at 463. The prescribed remedy is a no-op precisely when the warning fires,
  because the check counts **lines** and the sweep keeps **blocks**. Getting under budget
  needed `--keep 4`, chosen by trying `--dry-run` until the projected line count fit —
  i.e. the operator does the search the tool should do. **No new fix proposed** — third
  occurrence for `#74`, now with the detail that the workflow text (*"it deterministically
  keeps the newest ~6 session blocks"*) names the default that fails, so an agent
  following wrap-up literally will run the no-op, see the warning persist, and have no
  documented next step. Worth having the sweep accept a target line count, or having the
  budget check emit the `--keep` that would satisfy it.

## Graduated 2026-07-27 — GitHub Issues (#70–#77)

Swept by the `triage-friction-log` workflow. Thirteen entries, fully accounted for:
**twelve graduated** into eight issues ([#70](https://github.com/topij/agentic-dev-kit/issues/70)–[#77](https://github.com/topij/agentic-dev-kit/issues/77)),
four of which each merge two entries recorded on separate days; **one** recorded a
measurement with *"No change proposed"*. All thirteen are kept below for the trail,
along with the prior graduation marker.

### 2026-07-26 — Backlog migrated to GitHub Issues (#54–#56)

The inbox was swept by the `triage-friction-log` workflow. Three entries graduated:

- [#54](https://github.com/topij/agentic-dev-kit/issues/54) — every verification claim
  must name the command that establishes it (supersedes the narrower "wrap-up should
  fact-check the handoff" proposal).
- [#55](https://github.com/topij/agentic-dev-kit/issues/55) — `safety-critical-changes.md`
  rule 1 should name a tightening threshold.
- [#56](https://github.com/topij/agentic-dev-kit/issues/56) — removing a mechanism
  requires enumerating what it was rejecting.

Three further entries needed no ticket: their proposed fixes had **already shipped** in
PR #31 — the panel contract now requires lenses to execute and mutation-test (contract
items 4–5), rule 3 carries the blast-radius stopping criterion, and contract item 7
mandates isolated worktrees.

The remaining five: four were already tagged with an issue id (#10, #18, #19, #33), and one
recorded a guard working correctly with *"No change proposed"*. Eleven entries in, eleven
accounted for.

Everything above now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

### 2026-07-27

- **A mutation harness that restores outside `finally` leaves the repo mutated.** My
  restore line was unreachable when the script died parsing pytest output (a bare
  `python3` with no pytest returned no stdout, and `splitlines()[-1]` raised). The
  working tree kept a live mutant until `git status` caught it. Neither existing warning
  covers it: `#50` is about stale `.pyc`, and `fallback-review-panel.md` contract item 5
  warns only about **false kills** from a checksum/drift test (it does not mention
  `.pyc` at all). Both frame the hazard as "the result may be wrong"; neither says the
  repo may be left broken. **H** —
  proposed fix: contract item 5 should say the restore belongs in a `finally` (or a
  git-clean check) and that any harness must verify the tree is clean *after* it exits,
  not only after a successful run.
- **The closing-keyword trap fired again, because I weakened a correct rule on the
  strength of an experiment that did not test what I thought.** `#61` was closed by the
  squash-merge of `#68` and reopened by hand.

  **What is actually measured** — three data points, with their confounds stated,
  because two earlier write-ups of this stated more than the data supports:

  | artifact | form | outcome |
  | --- | --- | --- |
  | `#68` body | `Closes #61` inside a **fenced block** | inert (`closingIssuesReferences: []`) |
  | `9c6ab3a` commit message | `Closes #61` in an **inline** span | **fired** — closed `#61` |
  | `#63` body | `Does NOT close #60` **and** a plain `fix #60` | fired; which one is **not isolated** |

  **What is NOT measured, though I twice wrote as if it were:** whether an *inline* span
  is inert in a PR body. The two backtick data points differ in **two** variables at once
  — fenced-vs-inline *and* body-vs-commit — so "GitHub excludes inline code spans" and
  "fenced blocks are inert everywhere, inline spans fire everywhere" fit the evidence
  equally well. Under the second reading, the fix I proposed last round (strip inline
  code from a PR body before checking) reopens the exact hole that closed `#61`.

  Likewise the *negation* hypothesis: `#63`'s body carries a plain, non-negated `fix #60`
  alongside the negated mention, so a check that only flags keywords **near a negation**
  would have passed that body clean.

  **H** — **stop deriving a mechanism; take the conservative rule.** Three attempts to
  state this precisely have each been wrong, which is rule 1's threshold. The original
  2026-07-26 rule below — never write a closing keyword adjacent to an issue number you
  do not intend to close, in any form, on any surface — would have prevented all three
  incidents; the measurement talked me *out* of a correct rule. It stands as written, and
  the proposed check follows it rather than any theory of markdown:

  - flag **every** match on **every** surface — PR body, every commit message, and the
    squash message — with **no stripping** of code spans or fenced blocks;
  - cover the forms the naive regex misses and GitHub honours: `owner/repo#61`, a full
    issue URL, and `Closes: #61` (a colon, not whitespace);
  - check the **squash message at merge time** specifically. It is composed *after* the
    PR body was reviewed, and nothing reviews it — verified: `9c6ab3a`'s message matches
    neither `#68`'s title, its body, nor any of its three branch commits, and no hook in
    `scripts/` inspects commit messages at all;
  - the operator confirms each match. Over-firing is the acceptable failure here.

  Occurrence count, corrected: **three occurrences across two sessions** (`#63` and `#64`
  were the same session; `9c6ab3a` is this one).
- **A review bot with an incremental model keeps a stale review across a rewrite.**
  CodeRabbit reviewed the pre-split head, then declined `@coderabbitai review`
  ("does not re-review already reviewed commits") and hit its Fair Usage limit on
  `@coderabbitai full review`. The PR was force-pushed and then substantially rewritten,
  so the only bot review covered code that no longer existed. `pr_watch`'s
  `bots_behind_head` recorded it correctly — the friction is that **nothing warns at
  push time**, when re-requesting is still cheap. **M** — proposed fix: have `pr-watch`
  surface `covers_head: false` as a distinct, louder line right after a push that
  changes the diff shape, rather than only at receipt time. Related: `#27`, `#44`.
- **The panel's worth is disjointness, and this run measured it.** Round 1: the
  adversarial lens found the enclosing-repo and `GIT_DIR` regressions; the correctness
  lens independently found the `~`-expansion disagreement between `init.sh` and the new
  detector. Almost no overlap. Round 2's correctness lens then found the *misattributed
  defect* — a false sentence in the commit message written to describe round 1's own
  outcome, which could not have existed when round 1 ran. **No change proposed** —
  recording it because `fallback-review-panel.md` argues disjointness from one prior
  data point, and this is a second, stronger one worth citing there. Note the honest
  framing of what the panel beat: the four regressions were missed by CI, by the suite
  **as it then stood**, and by the mutation run **at that head** — not by the 372-test
  suite quoted elsewhere, which only exists *because* those findings were fixed.
- **The archive sweep broke a cross-reference again — and this time it broke one the
  PREVIOUS sweep had written.** The 2026-07-26 entry below reports the sweep orphaning
  *"see the Phase 3b block above"*. Today's sweep moved Phase 3b itself into the history
  file, so the surviving text — *"see the Phase 3b block, still live in
  kit-handoff.md"* — became false in a second way: the target is now in the very file
  the sentence sits in. Fixed by hand in this commit. **M** — the entry below proposes
  warning on `(above|below)`-style references in *moved* blocks; this instance shows the
  warning must also cover references **into** a moved block from anywhere in either
  document, since the block that moved was the reference's *target*, not its location.
  Same family as `#53`.
- **The doc-budget remedy no-op reproduced a third time** (see the 2026-07-26 entry
  below). `check_doc_budget` reported 421/400; the remedy it names printed *"nothing to
  move: 5 session block(s) <= --keep 6"*; `--keep 4` was needed and found by guessing.
  **No new fix proposed** — recording the third occurrence. The entry below already
  records two; this makes it three, two of them in *this* repo, which is a pattern
  rather than a run of bad luck.
- **A review lens's isolated worktree pointed at the wrong ref again — 5 of 5 this
  session, 9 of 9 across two.** (Last session's entry below records 4 of 4; this session
  ran 2 lenses × 2 rounds on `#65` plus 1 on `#68`.) Every lens detected it and cloned
  the target itself, because the prompt required reporting the path and diff stat.
  **H** — proposed fix: this is no longer a
  caveat, it is the default behaviour. Contract item 7 should stop saying "verify" and
  start saying "assume the worktree is wrong; clone the target yourself first", with the
  path/diff-stat report as a required field of the lens output (the existing 2026-07-26
  entry proposed the report; this one is about inverting the default).

### 2026-07-26

- **The doc-budget remedy does not fire at the default `--keep`.** `check_doc_budget`
  measures **lines**; `archive_plan_sessions` keeps **blocks**. This handoff hit
  448/400 lines with 5 blocks, so the remedy the warning names printed *"nothing to
  move: 5 session block(s) <= --keep 6"* and the file stayed over budget. The agent has
  to guess a `--keep` and re-run until the line count drops — which is exactly the
  manual fiddling the deterministic engine exists to remove. **M** — proposed fix: give
  `archive_plan_sessions` a `--target-lines` mode (sweep oldest-first until under
  budget), or have `check_doc_budget`'s remedy string compute and name the `--keep` that
  would work. Reproduced twice this session (kit and cs-toolkit).
- **A runtime's isolated worktree points at the session's base ref, not the PR head.**
  All **four** review-lens launches this session (2 lenses × 2 rounds) landed on `main`
  with an empty `git diff main...HEAD`. Every one detected it and cloned the real target
  — because the launch prompt required them to *report the path and diff stat they saw*.
  `fallback-review-panel.md` contract item 7 says to verify; what actually surfaced it
  was making the report **mandatory output**. **H** — proposed fix: promote "state the
  path reviewed and the diff stat" from advice to a required field of the lens report in
  contract item 8, and say plainly that a lens which cannot show a non-empty diff has not
  reviewed anything. A clean pass over an empty diff is indistinguishable from a real one.
- **`--record-review` has no way to record honest partial coverage.** It correctly
  refuses a receipt bound to a stale head (`PR head changed during review`), but the only
  alternative is a receipt claiming the current head — which the panel did not review. So
  the honest choice is **no receipt at all**, and the audit trail then loses the fact that
  a two-lens panel ran at all. **M** — proposed fix: allow recording against the reviewed
  sha with the head-gap represented rather than rejected (the existing `bots_behind_head`
  field is the precedent). Related: #32.
- **Negating a GitHub closing keyword still arms it.** A PR body was edited before merge
  to retract a closure claim; the retraction read *"Does NOT close #60"*. GitHub matched
  `close #60`, and merging closed an issue documenting an **unfixed** bug. Caught after
  the fact and reopened. **M** — proposed fix: one line in the wrap-up / pr-watch
  doctrine — never write a closing keyword adjacent to an issue number you do not intend
  to close, even negated; write "#60 stays open". cs-toolkit's `CLAUDE.md` already carries
  the Linear-side twin of this hazard.
- **The cockpit edited the shared tree while lenses were reviewing it.** A lens reported
  the shared checkout changing mid-run (5 files, mtimes inside its window) and correctly
  noted it was not the author. Its own review was unaffected — it worked from an isolated
  clone — but it had to spend output distinguishing "concurrent editor" from "corruption".
  Contract item 7 constrains the **lenses**; nothing constrains the **cockpit**. **M** —
  proposed fix: add a cockpit-side clause — do not mutate the shared tree between
  launching a panel and reading its findings.
- **The archive sweep breaks *relative* cross-references, and its docstring says it
  doesn't.** `archive_plan_sessions.py:20` claims *"It only ever moves content — every
  cross-reference (ticket ids, PR links, commit shas, …) is preserved."* Every kind it
  enumerates is **absolute**. A relative one is not preserved: this session's sweep moved
  the Phase 3a block into the history file while Phase 3b stayed live, orphaning
  *"see the Phase 3b block above"* — the target is now in a different file. Caught by
  CodeRabbit on the wrap-up PR, not by the sweep, which reported success. **M** —
  proposed fix: have the sweep scan moved blocks for `(above|below)`-style references
  and warn (not rewrite — rewriting is the class of surgery `init.sh`'s deleted marker
  migration proved dangerous). Same family as #53, which is about the pointer the sweep
  *writes*; this is about the references it *carries*.

## Graduated 2026-07-26 — GitHub Issues (#54–#56)

Swept by the `triage-friction-log` workflow. Eleven entries, fully accounted for:

- **3 graduated** to issues [#54](https://github.com/topij/agentic-dev-kit/issues/54),
  [#55](https://github.com/topij/agentic-dev-kit/issues/55) and
  [#56](https://github.com/topij/agentic-dev-kit/issues/56).
- **3 needed no ticket** — their proposed fixes had already shipped in PR #31.
- **4 were already tagged** with an issue id (#10, #18, #19, #33).
- **1 recorded a guard working correctly**, with *"No change proposed"*.

All eleven are kept below for the trail.

### 2026-07-25 — Backlog migrated to GitHub Issues

Two H-severity entries were **removed from this file** and filed as
[#26](https://github.com/topij/agentic-dev-kit/issues/26) (fallback review needs to be a
*panel*) and [#27](https://github.com/topij/agentic-dev-kit/issues/27) (a receipt
survives a redesign its reviewer never saw). #27's cheap half shipped in PR #29; the
issue stays open for the shape-change half.

Also closed this session, so their inbox entries below are **done**, kept only for the
trail: **#19** (premature receipt — closed by PR #25) and **#10** (lane-worktree gate
failure — closed by PR #28).

### 2026-07-25 — inbox

- **The `cp -r` quickstart can't distinguish kit-owned from adopter-owned files (severity: M).**
  Any file the kit tracks lands in an adopter's repo, which is why this repo's own narrative
  docs had to be renamed `kit-*.md` rather than simply filled in. `kit-manifest.json` now
  encodes the ownership boundary (`adopter_owned`), so a manifest-aware installer could copy
  correctly and the rename would become unnecessary. Filed as issue #18.

- **`--record-review` accepts a receipt while the primary bot is still queued (severity: M).**
  Recorded a fallback receipt on #16 when CodeRabbit's check read `PENDING — Review queued`;
  its four valid findings landed after the merge. The doctrine distinguishes *unavailable*
  from *slow*, but nothing mechanically does. Candidate: treat a configured bot's own
  `PENDING` check as a merge blocker while no receipt exists — but that inverts the
  informational-check exclusion in the one case where the exclusion is load-bearing (it is
  what stops the loop wedging on a bot that never reports), so it needs care. Filed as #19.

- **A lane's local gate fails for reasons unrelated to its diff (severity: H).**
  All three lanes this session hit the same two `state_paths` test failures, caused purely by
  running from inside a marker-carrying worktree. A gate that goes red for environmental
  reasons teaches agents to ignore a red gate. Already filed as issue #10 — raising severity
  here because three independent occurrences in one session makes it a pattern, not an
  incident.

- **A fix round on gate logic is where the next bug comes from — every time (severity: M, pattern).**
  Seven review rounds on PR #25. Every one found something real, and **rounds 3 through 7
  each found a defect introduced by the previous round's fix**: an incomplete poison-clock
  fix that still wedged on a *parseable* future date (R3); a section-scoping fix applied
  to 1 of 3 guards in the same function (R4); a replacement warning message that walked
  inline-list adopters into the corruption the deleted mechanism used to cause (R5); a
  style detection that missed a real flow spelling (R6); and a list spelling promoted to
  "supported" that the kit's own reader cannot parse (R7). Session-wide: **13 rounds
  across three PRs, all 13 with findings, 7 of them self-inflicted by the prior fix.**
  `safety-critical-changes.md` rule 3 **already** says "Re-review after every fix round
  until a full pass finds nothing new" and that "fix rounds on gate logic routinely
  introduce their own regressions" — so the floor is written and was followed. What this
  session adds is different, and is what should graduate: (a) a *base rate* — 13/13 rounds
  with findings means "until a pass finds nothing new" may never terminate, so the rule
  needs a stopping criterion it currently lacks; and (b) the criterion that actually got
  used, which is **blast radius, not round count** — a merge gate and a
  reported-never-gating display field cannot share a stopping point.

- **Reading the code is not the same as running it, and the gap is not small (severity: M).**
  Three defects this session were invisible to careful reading and obvious on execution:
  CodeRabbit's pending check reports `startedAt: 0001-01-01T00:00:00Z`, so an
  "unmeasurable age fails open" branch was not an edge case but the *only* path that bot
  ever took (the #19 guard was dead code for its own target); making `append_to_section`
  return non-zero looked plainly correct and aborted `init.sh` under `set -eu` on any
  config missing an optional section; and `kitconfig` silently resolves a next-line flow
  list to `{}`. **Candidate graduation:** the review-panel prompt (#26) should require
  the lens to *execute* the changed paths and to mutation-test new branches — mutation
  is what proved **five** properties across the session were unpinned despite tests that
  named them (on #29: anchored author matching, newest-review-per-bot, the `bots=`
  threading; on #25: the `init.sh` list-style branch and `grep -qi`'s
  case-insensitivity). Three of those five are #29's.

- **Narrative surfaces drift from the diff, and nobody re-reads them (severity: M).**
  #25's PR body needed three corrections (a stale test count, and two descriptions of a
  design the diff had replaced); #29's asserted an anchored-match property no test pinned;
  and **this very wrap-up** was fact-checked and came back with 13 issues, three of them
  HIGH — including a number that a review round on #25 had *explicitly corrected*
  ("four ways to corrupt" → three) and which I reintroduced while writing up the lesson
  that PR bodies keep drifting. Every instance was caught by a review pass, never by the
  author. **Proposed fix:** `wrap-up` should fact-check the handoff against `git log` /
  `gh` before committing — the handoff is read at the start of every future session, so a
  wrong number there propagates further than a wrong PR body. Filing this at M rather
  than L because the failure recurred *inside the document describing it*.

- **The cockpit bundled wrap-up narrative edits into a lane branch, and only the hook caught it (severity: L, but the guard worked).**
  While waiting on CI for PR #29 I updated `kit-handoff.md` and `kit-friction-log.md`, then
  `git add -A` swept them into the lane commit. `pre-push` refused, named both files, and
  said where the lane's handoff belongs instead. Recording it because it is the **positive**
  case this log rarely captures: a fail-closed guard firing on its author, with a message
  that made the fix obvious. Worth keeping in mind when weighing whether a guard is worth
  its friction — this one cost ten seconds and prevented a narrative-file conflict with the
  wrap-up PR. No change proposed.

### 2026-07-26 — inbox

> **At the 150-line budget.** A `triage-friction-log` sweep is required before the
> next entry — the two H entries below are issue-shaped and #33 is already filed.

- **Mutation testing this repo reports false kills — filed as [#33](https://github.com/topij/agentic-dev-kit/issues/33) (severity: H).**
  `kit_doctor`'s self-check rehashes every kit-owned file, so any byte change to an
  engine fails it and every mutant looks killed. The **mechanism** is trivially
  reproducible (change one comment in an engine; only the manifest test fails). The
  **figure** — a lens reporting 17/17 killed on #31, and 7 survivors once that test
  was excluded — is attested rather than independently measured; the 17 are enumerated
  nowhere. Those 7 were closed inside #31. Filed at H because it is **retroactive**:
  mutation evidence cited across #25, #28, #29 and #31 may be worthless wherever the
  reviewer did not exclude that test, and "N mutants died" was used as a reason to stop
  reviewing. A false-negative testing tool is worse than none, because it is used to
  justify confidence. #33's mechanical fix (a `driftcheck` marker) is not built; only
  the panel doc's prose warning ships.

- **Concurrent review lenses in one working tree destroy each other's work (severity: H).**
  On #31 the adversarial lens mutated `pr_watch.py` to test it; the correctness lens,
  running at the same time, saw those mutations as an external process corrupting the
  repo and ran `git checkout --` to "restore" it. They fought for ~10 minutes. One
  lens's results were unreliable; when I stopped the other it left a live mutant behind
  (`if False and _PANEL_LENS_NAMES:`) that **silently disabled a guard in my working
  tree**, and I caught it only because a test failed citing an error string that should
  no longer have existed. Already fixed as contract item 7 (isolated worktrees) and
  `.gitignore`/`init.sh` entries, so this is recorded for the pattern rather than as an
  open item: **any doctrine that says "run N reviewers concurrently" owes them
  isolation**, and mine did not until it bit.

- **Deleting a check reintroduced the bug it was masking (severity: M).**
  The roster check removed from #31 was the only thing catching `,` as punctuation in
  `--lenses` — so `"adversarial, focused on the merge gate"` (an honest way to record
  ONE lens) rendered as two, suppressing the one-lens warning that was the field's
  entire remaining value. The commit that deleted it quoted that exact input as an
  example of what it still blocked. **Fixed inside #31** — recorded for the pattern. **Lesson worth generalising:** when removing a
  mechanism as unfit, enumerate what it was rejecting and confirm each case is either
  still rejected elsewhere or deliberately allowed — the deletion commit did neither.

- **Four rounds of tightening a matcher is the signal to delete it, and the rule
  already says so (severity: M, pattern).**
  `safety-critical-changes.md` rule 1: *"Treat 'we tightened the matcher' as a stopgap,
  not a fix."* On #31 I tightened it four times before accepting that. The adversarial
  panel told me by round 3 that the artifact was unverifiable from the engine — same
  actor, same invocation, nothing bound to what ran — and I built two more epicycles
  before acting on it. **Proposed fix:** rule 1 could name a threshold ("a second
  tightening of the same matcher is a design signal, not a bug fix") so the decision
  point is written down rather than requiring the author to notice it.
