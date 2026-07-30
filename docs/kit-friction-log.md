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

## 2026-07-29 (second sweep) — Backlog migrated to GitHub Issues (#155)

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

### Approval record — in-session operator, no DM

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

### What was verified

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

## 2026-07-30 (post-merge)

- **`pr_followup_hook.py` fires on command *text*, not on PR-opens — six false positives in one
  session.** Its trigger matches `.tool_input.command`, so any heredoc containing `gh pr create`
  or `gh pr ready` trips it: writing a doc *about* the command, filing an issue quoting it, and
  the `gh pr merge` whose squash body mentioned it all produced a MANDATORY watch-loop demand with
  no PR in existence. **M** — the guard it implements is real (`PRINCIPLES.md` #5/#8), which is
  what makes this expensive: a hook that cries wolf on documentation trains the agent to skim the
  one message that is sometimes load-bearing. **Two gates, and a fix must address both:**
  `.claude/settings.json` pre-filters on `Bash(gh pr *)`, then `pr_followup_hook.py:41` matches
  `\bgh\s+pr\s+(create|ready)\b` against `.tool_input.command` (`:181-182`) with no heredoc or
  quote awareness. Proposed fix: gate on the tool *result* (a PR URL, or `gh pr view` confirming a
  new number) rather than on the command string. A review lens reproduced a seventh occurrence
  live while checking this entry.
- **`gh pr merge --subject` suppresses GitHub's `(#NNN)` append — and the repo already had the
  problem.** `eeef647` landed without its number, worked around on the next merge by writing
  `(#168)` into the subject by hand. But a review lens then measured the base rate: **15 of 75
  commits on `main` have an associated PR and no `(#N)`**, among them `cdeae7a` (#144), `c48164c`
  (#154), `b46f794` (#153), `0b82ff2` (#148), `42873d8` (#69), `9c6ab3a` (#68). So `--subject`
  explains *this* instance and is **not established** as the cause of the others. **M** — raised
  from L because it is recurring rather than a one-off, and a ticket drafted from the first
  version of this entry would have carried the wrong scope. Proposed fix: whichever workflow
  documents `gh pr merge` should say `--subject` replaces the whole subject line, append included
  — and something should check the suffix at merge time, since seven sessions did not notice.
- **Two isolated lenses stalled identically at the 600s watchdog, mid-run.** Same session, same
  prompt shape, both killed with partial output. Re-running with a tighter scope succeeded. **M**
  — the hazard is not the stall but its shape: a stalled lens returns *nothing*, which is
  indistinguishable from a lens that ran and found nothing unless the cockpit checks the task
  status. `fallback-review-panel.md` item 10 requires the lens to open with what it reviewed,
  which catches a wrong-ref lens but not a dead one — the report never arrives at all. Proposed
  fix: the panel's step 3 should confirm each lens *returned*, not only that what returned looks
  right.
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

## 2026-07-29 (post-sweep, second)

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
