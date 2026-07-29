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

## 2026-07-29 — Backlog migrated to GitHub Issues (#149–#150)

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

### Approval record — in-session operator, no DM

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

### What was verified, and what was not

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

## 2026-07-29 (post-sweep)

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
