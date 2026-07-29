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
reproduces from `c48164c`; the archived block un-demotes to the snapshot byte-for-byte; each of
the seven comments was fetched back by id and hashes to the text that was sent, on the issue
claimed for it; `#155` exists with the title and labels this record claims.

**What these checks do not reach**, restated rather than dropped — the previous marker named
these about its own checks and they are still true here. The comment check's right-hand side is
a **local file**, so it is the one thing a third party cannot re-run. Nothing verifies that the
approval happened as described, which matters most precisely because the DM that normally carries
that evidence did not exist. The un-demote round-trip is self-inverting, so it would pass on a
corrupted demotion; the fence count that would catch the realistic corruption is *measured* and
reported, not asserted as a gate. And nothing here verifies that any posted comment is **true** —
this sweep's own `#45` comment opens by retracting a claim the previous sweep filed there, and
four of the errors corrected on this PR were found by a review lens rather than by any check. No
automated gate covers any of it
([#127](https://github.com/topij/agentic-dev-kit/issues/127)).

The swept entries are verbatim in the archive under `Graduated 2026-07-29 (second sweep)`.

## 2026-07-29 (post-sweep, second)

- **Both review lenses were handed a worktree at the wrong ref, and both caught it.** The panel
  run on the sweep's own PR launched two lenses with runtime-provided worktree isolation. Both
  worktrees were created at `c48164c` — the PR's *base* — so `git diff origin/main...HEAD` was
  **empty** in each, and neither HEAD matched the `f33bb488` the launch prompt named. This is
  [#75](https://github.com/topij/agentic-dev-kit/issues/75)'s subject reproducing exactly: the
  contract item that tells a lens to assume its worktree points at the wrong ref, and to verify a
  non-empty diff against an expected head before reviewing. **H** — occurrence data for `#75`,
  and the strongest available: it is the first instance where the guard is observed *working*
  rather than the failure being observed after the fact. Two independent lenses, 2/2, each
  detected it and each recovered differently — one reviewed via read-only plumbing against the
  shared object store, the other re-pointed its own worktree — so both reviewed the real diff and
  neither reported all-clear on an empty one. The launch prompt's wording matters and should be
  kept: it named the expected head and told each lens to stop rather than report clean. Note also
  that recovery was possible only because the object was reachable locally; a lens whose runtime
  gave it a worktree of a *different repository* (the OpenKitchen case `#75` records) has no such
  fallback. **Not from the swept inbox:** surfaced by the review panel on this sweep's own PR,
  recorded below the marker for the next pass.
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
