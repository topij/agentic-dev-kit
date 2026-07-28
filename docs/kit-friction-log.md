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
committed blob*: the inbox at `06490a1` is that text, so the digest and every check below
reproduce from `git` and `gh` alone, in any session.

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
this run, matched by **author and timestamp**. `#23` is CLOSED with none. `7 + 7 = 14` against 14
parsed bullets.

**Not established, and worth naming.** The comment checks assert existence, not *content* — a
correct comment posted to the wrong issue would pass. The block-presence check is a substring
test over the whole archive; an adversarial lens showed it passes against an archive whose
visible text is destroyed while the real bytes hide in an HTML comment, so it rules out "archived
nothing", not "archived the wrong bytes". Nothing verifies that the approval happened as
described, or that the proposals shown were the proposals drafted — that is what the DM thread
would have carried. And no automated gate covers any of it
([#127](https://github.com/topij/agentic-dev-kit/issues/127)): a lens deleted a whole swept block
from the archive and `make mutation-test`, `check_doc_budget` and `kit_doctor` all stayed green.

The swept entries now live in [`kit-friction-log-archive.md`](kit-friction-log-archive.md), under
`Graduated 2026-07-28 (second sweep)`. *(Named, not linked: a relative link here becomes a
self-reference the moment the next sweep moves this marker into that file — the
[#73](https://github.com/topij/agentic-dev-kit/issues/73) hazard, which the previous version of
this line reproduced.)*
