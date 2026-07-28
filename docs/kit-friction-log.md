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

## 2026-07-27 — Backlog migrated to GitHub Issues (#70–#77)

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

## 2026-07-27

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

## 2026-07-27 (third session of the day)

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

## 2026-07-27 (fourth session of the day)

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

## 2026-07-28

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
