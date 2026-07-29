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
by the run before it — without noticing it existed.

### Approval record — in-session operator, no DM

`config/dev-model.yaml → notify.user_key` is empty, so there is no DM surface to stop on; the
operator was present and substituted for it. That is the interactive path
[#128](https://github.com/topij/agentic-dev-kit/issues/128) asks for, and this block is the
committed artifact that issue requires, since `state/` and `reports/` are gitignored. Approval
was bulk and unconditional — *"lgtm"* — so every proposal carries the same decision and the
explicit-opt-in default for unmentioned proposals was never exercised. This is the **sixth**
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
claimed for it; `#155` is OPEN with the labels stated. Nothing here verifies that any posted
comment is *true* — the previous sweep's worst error was caught by a review lens, not by a
check, and no automated gate covers any of this
([#127](https://github.com/topij/agentic-dev-kit/issues/127)).

The swept entries are verbatim in the archive under `Graduated 2026-07-29 (second sweep)`.
