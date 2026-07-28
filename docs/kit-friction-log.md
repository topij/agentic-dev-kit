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

## 2026-07-28 (second sweep) — Backlog migrated to GitHub Issues (#138–#143)

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

### Approval record — in-session operator, no DM

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

### What was verified, and what was not

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

## 2026-07-29 (session spanning from 2026-07-28)

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
