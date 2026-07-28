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
Fourteen entries in, fourteen accounted for: **seven graduated** into six new issues
([#138](https://github.com/topij/agentic-dev-kit/issues/138)–[#143](https://github.com/topij/agentic-dev-kit/issues/143)),
and **seven** routed as occurrence comments. `7 + 7 = 14`.

The seven routed entries became **five** comments, on the five issues they are evidence for:
`#45` and `#113` each carry two entries, `#75`, `#73` and `#120` one each. Stated here rather
than left to a reader to reconcile, because "seven routed" against five enumerated targets is the
shape the previous sweep's record got wrong.

Seven entries became **six** issues because two of them — the `pr_watch` 403 diagnosis from the
second session and the *"still discards the 403 body, needs a ticket"* follow-up from the fourth —
are the same defect observed twice, and graduated together into
[#139](https://github.com/topij/agentic-dev-kit/issues/139).

`#23` is named as a routing target by the swept text and received nothing **from this sweep**: it
is closed, and its occurrence data is consolidated on `#45`. It is not un-commented, though — it
carries the *previous* sweep's occurrence comment, posted `2026-07-28T13:46:17Z`, four minutes
before `#126` merged, after a fallback panel caught that it had been omitted. The failure `#138`
records is therefore narrower than "a comment that was never posted": what claimed the comment
was the comment posted to `#45`, and the omission was real for as long as it took a panel to
catch it.

*(This paragraph is a review fix. Its first version asserted that the previous sweep's record
claimed a `#23` comment that was never posted. Both halves were false — that record's routing
list is `(#42, #45 ×3, #54, #74 ×2, #75, #76, #118)`, which does not name `#23`, and the comment
exists. Rated HIGH by the correctness lens. The verification below missed it because its filter
matched the string `` `triage-friction-log` sweep `` while the earlier comment reads "the
2026-07-28 triage sweep" — a substring test standing in for an author-and-time test, which is the
weakness `#138` is about.)*

### Approval record — in-session operator, no DM

This run was **interactive**, so the operator substituted for the DM review surface rather than
the stop being bypassed. [#128](https://github.com/topij/agentic-dev-kit/issues/128) argues that
an interactive operator is a valid substitute *only if the approval record lands somewhere
committed*, since `state/` and `reports/` are both gitignored. This block is that record.

Approval was given up front and unconditionally — *"I approve all suggestions"* — so every
proposal below carries the same decision, and the explicit-opt-in default was never exercised.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-28.json` (gitignored),
`sha256 b3a168a8ba8c18dc7d254fe76d1621b6ae5afff6d757540f1316c398643a6db7` over the inbox text
captured **before** any write — **14,341 bytes** (14,235 characters; 54 of them non-ASCII). The
digest is over the bytes, so the byte figure is the one to reproduce it with. The sweep below
moves exactly that text.

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

### Routing and sweep verified after the writes — six checks

The check [#138](https://github.com/topij/agentic-dev-kit/issues/138) proposes, applied to the
sweep that filed it. **This block is the review panel's second version.** The first ran three
commands under the heading "every claim re-read from GitHub", and the panel showed that was a
larger claim than the commands supported: no issue titles asserted, no author or timestamp bound
to any comment, `#23`'s closed state never checked, and a substring filter standing in for all of
it — which is how the false `#23` sentence above passed its own verification.

**None of it needs the gitignored snapshot.** The snapshot is a copy of a committed blob: the
inbox at `06490a1` *is* the frozen text, so every check below reproduces from `git` and `gh`
alone, in any session. The first version said otherwise, which had the effect of telling an
auditor not to try.

The script that produces the output below is reproduced in full in PR
[#144](https://github.com/topij/agentic-dev-kit/pull/144)'s body. It is deliberately **not
committed** — a one-off checker for one sweep is what `#138` exists to replace with something the
next sweep inherits, and adding an untested engine mid-fix-round is the shape
`safety-critical-changes.md` rule 3 prohibits. Output verbatim:

```
== 1. the frozen snapshot is reconstructible from git, no local state needed ==
  sha256 of 06490a12's inbox = b3a168a8ba8c18dc…  expected b3a168a8ba8c18dc…  OK
  14235 characters / 14341 bytes  (the digest is over the bytes)

== 2. sweep integrity: moved, not deleted; and not vacuously 'present' ==
  OK  ## 2026-07-28 — Backlog migrated to GitHub Issues (#   in_new=True in_old=False exactly_once=True
  OK  ## 2026-07-28 (second session of the day)              in_new=True in_old=False exactly_once=True
  OK  ## 2026-07-28 (fourth session of the day)              in_new=True in_old=False exactly_once=True
  entry bullets: 14 before -> 0 after  OK
  archive is old + new only: OK  (old body preserved verbatim: True)

== 3. every claimed issue exists, is OPEN, and has the expected title ==
  #138..#143 OK  [OPEN/topij]  titles match the record's one-line descriptions

== 4. every claimed comment exists on the issue it claims — matched by TIME, not text ==
  #45  OK  1 comment from this run at 2026-07-28T20:17:49Z  (carrying 2 routed entries)
  #113 OK  1 comment from this run at 2026-07-28T20:17:50Z  (carrying 2 routed entries)
  #75  OK  1 comment from this run at 2026-07-28T20:17:52Z  (carrying 1 routed entry)
  #73  OK  1 comment from this run at 2026-07-28T20:17:53Z  (carrying 1 routed entry)
  #120 OK  1 comment from this run at 2026-07-28T20:17:54Z  (carrying 1 routed entry)

== 5. the issue this sweep deliberately did NOT write to ==
  #23 OK  state=CLOSED, 0 comments from this run, 2 from topij overall (latest 2026-07-28T13:46:17Z)

== 6. arithmetic ==
  7 graduated + 7 routed + 0 discharged = 14 vs 14 entry bullets — OK
  7 graduated entries -> 6 issues; 7 routed entries -> 5 comments
```

Check 2 is the one [#127](https://github.com/topij/agentic-dev-kit/issues/127) says nothing
automated covers, and it is deliberately three assertions rather than one: a block must be in the
new archive, **absent from the old one** (or an already-archived block satisfies it vacuously),
and present **exactly once**. Plus: zero entry bullets left in the active file, and the previous
archive body preserved verbatim.

Still not covered by any of this: that the *approval* happened as described, and that the
proposals shown were the proposals drafted. Those are what the DM thread would have carried, and
in an in-session run nothing outside this record attests to them.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).
