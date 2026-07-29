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

## 2026-07-29 (post-sweep, second)

- **The doc-budget remedy is a no-op at the default `--keep`, and the wrap-up workflow prescribes
  exactly that invocation.** `check_doc_budget` warned the handoff was 423/400 and named
  `archive_plan_sessions.py` as the remedy; running it as `workflows/wrap-up.md` step 8 instructs
  reported *"nothing to move: 6 session block(s) <= --keep 6"* and left the file over budget. Only
  an explicit `--keep 5` moved anything (423 → 352). **M** — occurrence data for
  [#74](https://github.com/topij/agentic-dev-kit/issues/74), which already records the lines-vs-blocks
  mismatch. What this adds is that the *workflow doc* hands an agent the invocation that cannot
  work: a budget expressed in lines cannot be discharged by a remedy bounded in blocks, so either
  the script should take a line target or `wrap-up.md` should say to lower `--keep` until the
  budget clears.
- **`finalize.pr_draft: true` contradicts the operator's stated preference and this repo's own
  `#124`.** The operator asked that PRs be marked ready as soon as no further changes are expected,
  because a draft is invisible to the review bot; `#124` records the same thing as a defect of the
  triage workflow specifically. But `config/dev-model.yaml` still defaults `finalize.pr_draft` to
  `true`, so every sweep opens a draft and relies on someone remembering to flip it. **M** —
  proposed fix: flip the default and let an adopter opt into drafts, or state in
  `triage-friction-log.md` that the PR must be readied before the run reports complete. Distinct
  from `#124`, which asks for the *reviewer* to see the PR; this is about a default that has to be
  worked around every time.
- **Three review rounds on one change found their defect in the same place each time: the prose
  justifying the mechanism.** `_deep_merge`'s docstring said "two shapes" while implementing six;
  the overlay allowlist said its keys were "read by no shell reader" while `init.sh` read exactly
  them; a list-replacement rule was motivated by a key the same file asserts can never be set. The
  mechanism itself was never wrong — and the two genuine bugs found in rounds 2 and 3 were both
  introduced by the *previous round's fix*. **H** — proposed fix: this belongs in
  `fallback-review-panel.md`'s authoring section next to "keep the record small", as a sharper
  claim than that one makes. Justification prose is written from intent; intent is the one thing a
  reviewer cannot check against the code, so a "why this is safe" sentence should either cite a
  test that would fail if it were false, or be deleted. Deleting it is what ended the loop here.
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
