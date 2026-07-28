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
and **seven** routed as occurrence comments on the five issues they are evidence for
(#45, #73, #75, #113, #120). `7 + 7 = 14`.

Seven entries became **six** issues because two of them — the `pr_watch` 403 diagnosis from the
second session and the *"still discards the 403 body, needs a ticket"* follow-up from the fourth —
are the same defect observed twice, and graduated together into
[#139](https://github.com/topij/agentic-dev-kit/issues/139).

`#23` is named as a routing target by the inbox text and **received nothing**: it is closed, and
its occurrence data is consolidated on `#45`. That is stated here rather than left implicit
because the previous sweep's record claimed a comment on `#23` that was never posted — the defect
now filed as [#138](https://github.com/topij/agentic-dev-kit/issues/138).

### Approval record — in-session operator, no DM

This run was **interactive**, so the operator substituted for the DM review surface rather than
the stop being bypassed. [#128](https://github.com/topij/agentic-dev-kit/issues/128) argues that
an interactive operator is a valid substitute *only if the approval record lands somewhere
committed*, since `state/` and `reports/` are both gitignored. This block is that record.

Approval was given up front and unconditionally — *"I approve all suggestions"* — so every
proposal below carries the same decision, and the explicit-opt-in default was never exercised.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-28.json` (gitignored),
`sha256 b3a168a8ba8c18dc7d254fe76d1621b6ae5afff6d757540f1316c398643a6db7` over the 14,235 bytes of
inbox text captured **before** any write. The sweep below moves exactly that text.

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

### Routing verified against the live tracker, after the writes

The check [#138](https://github.com/topij/agentic-dev-kit/issues/138) proposes, applied to the
sweep that filed it. Every claim in the record above was re-read from GitHub rather than asserted:

```
$ for n in 45 113 75 73 120; do printf '%s ' "$(gh issue view $n --json comments \
    -q '[.comments[] | select(.body | contains("triage-friction-log` sweep"))] | length')"; done
1 1 1 1 1

$ gh issue view 23 --json comments \
    -q '[.comments[] | select(.body | contains("triage-friction-log` sweep"))] | length'
0                      # claimed to have received nothing, and did

$ for n in 138 139 140 141 142 143; do printf '%s ' "$(gh issue view $n --json state -q .state)"; done
OPEN OPEN OPEN OPEN OPEN OPEN
```

Sweep integrity and arithmetic, from the frozen snapshot rather than from this record. No
automated gate covers either ([#127](https://github.com/topij/agentic-dev-kit/issues/127)), and
the snapshot is gitignored, so this is reproducible only in the session that ran the sweep:

```
$ python3 - <<'PY'
import json, re, pathlib
frozen = json.load(open("state/triage/frozen-inbox_2026-07-28.json"))["inbox_text"]
arc = pathlib.Path("docs/kit-friction-log-archive.md").read_text()
blocks = re.split(r"\n(?=## )", frozen.strip())
demote = lambda b: "".join(("#" + l if re.match(r"^#{2,5} ", l) else l) for l in b.splitlines(keepends=True))
print(sum(demote(b).strip() in arc for b in blocks), "of", len(blocks), "swept blocks byte-identical in the archive")
print(len(re.findall(r"(?m)^- \*\*", frozen)), "entry bullets in the frozen inbox")
PY
3 of 3 swept blocks byte-identical in the archive
14 entry bullets in the frozen inbox
```

`7 graduated + 7 routed + 0 discharged = 14`, against those 14 bullets.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).
