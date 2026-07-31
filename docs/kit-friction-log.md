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

## 2026-07-31 — Backlog migrated to GitHub Issues (#178–#183)

Swept by the `triage-friction-log` workflow in LLM-only mode (the engine tracked in
[#6](https://github.com/topij/agentic-dev-kit/issues/6) is still not vendored).
**Fourteen entries in, fourteen accounted for:** six new issues
([#178](https://github.com/topij/agentic-dev-kit/issues/178)–[#183](https://github.com/topij/agentic-dev-kit/issues/183)),
four occurrence comments (`#163`, `#54`, `#140`, `#75`), and two entries that needed no ticket
because the work they asked for had already landed — ten writes, each re-read from the tracker
after landing per `#138`.

The mapping is not one-per-entry in either direction, so neither count is a per-entry tally: two
entries of the 2026-07-30 post-merge-second section share `#179`; the `#163` comment carries two
entries, and the `#54` comment carries two, one of which is also the whole of the `#140` comment.

**Reading the tracker before drafting changed the routing twice, and both changes were
subtractions.** The doc-budget entry proposed occurrence data for `#74` — but `#74` is no longer
open (completed 2026-07-30), `scripts/archive_plan_sessions.py` now implements
`--target-lines`, and `docs/agentic-dev-kit/workflows/wrap-up.md` step 8 prescribes it by name.
(Both were cited by line number when this marker was written — `:442` and `:58`. `#176` landed
hours later and inserted above the second, making that citation false without touching it. The
line numbers are dropped rather than refreshed: the next commit would stale them again.) Both
halves of that entry had landed, including the half the entry itself said was still missing. The
`finalize.pr_draft` entry had already recorded its own resolution inline on 2026-07-30. A sweep
that drafted from the entries alone would have filed two tickets for work that was already done,
and the entries are the only surface that would have said otherwise.

Two proposals were filed as **new issues rather than as occurrence comments on `#150`**. That
issue's stated subject is a scripted text replacement that matches nothing; a check that ran in
the wrong directory (`#179`) and a guard that reported failure correctly and was then ignored
(`#180`) are neither. Stretching `#150` to cover them would have widened its acceptance criterion
past what it can test — three entries pointed at it, and only the `sed` half of one is literally
in scope. `#150` stays open and unchanged; both new issues link to it, so the backlinks are on it
either way.

### Approval record — in-session operator, no DM

`config/dev-model.yaml → notify.user_key` is empty and no `config/dev-model.local.yaml` exists, so
there is no DM surface to stop on; the operator was present in session and substituted for it.
**The documented stop is still unconditional** — `.claude/commands/triage-friction-log.md` states
it at lines 113 and 465 — so this run is in the same position as the run
[#128](https://github.com/topij/agentic-dev-kit/issues/128) was filed against, which the archive
records as having *violated* the stop rather than substituted for it. What `#128` asks for is an
interactive-operator exception that does not exist yet; what it calls the load-bearing half is
that any substitute leave a **committed** approval record, since `state/` and `reports/` are
gitignored (`.gitignore:9` and `:25`). This block is that record. It does not make the run
compliant with a rule the skill has not yet gained.

Approval was bulk and unconditional — *"lgtm"* — so every proposal carries the same decision and
the explicit-opt-in default for unmentioned proposals was never exercised. This is the **seventh**
sweep overall; the archive holds the six earlier markers.

**Frozen-inbox snapshot:** `state/triage/frozen-inbox_2026-07-31.txt` (gitignored),
`sha256 33ad2f7260690df2104e199bfa6f824b38d64df741eb93ee0be027ed31079d3f` over **23,145 bytes**.
Taken before any write, and over a *committed* blob — the inbox at `abbd62f` is that text, so
`git show abbd62f:docs/kit-friction-log.md | tail -n +14 | sha256sum` reproduces the digest in any
session that has **`git` and a SHA-256 utility**, with no reliance on the gitignored file
surviving. An earlier draft of this block said *"from `git` alone, in any session"*. The reviewer
on this PR refuted it by running the command: its environment had none of `sha256sum`, `shasum`,
`openssl`, `busybox` or `cksum`, so it could confirm the blob and its 23,145 bytes but not the
digest. That is an untested mechanism claim of exactly the shape
[#140](https://github.com/topij/agentic-dev-kit/issues/140) governs, written from intent about an
environment other than the one it ran in.

| # | proposal (abridged) | from entry | decision | outcome |
| - | ------------------- | ---------- | -------- | ------- |
| 1 | Hook fires on command *text*, not on a PR actually opening | 5 | approve | [#178](https://github.com/topij/agentic-dev-kit/issues/178) |
| 2 | A check that never reached its subject reports clean | 1 + 2 | approve | [#179](https://github.com/topij/agentic-dev-kit/issues/179) |
| 3 | A guard must be *chained* to the action it guards | 14 | approve | [#180](https://github.com/topij/agentic-dev-kit/issues/180) |
| 4 | `--subject` suppresses the automatic `(#N)` append | 6 | approve | [#181](https://github.com/topij/agentic-dev-kit/issues/181) |
| 5 | A stalled lens is indistinguishable from one that found nothing | 7 | approve | [#182](https://github.com/topij/agentic-dev-kit/issues/182) |
| 6 | A mutation kill that aborts the session names no test | 4 | approve | [#183](https://github.com/topij/agentic-dev-kit/issues/183) |
| 7 | The one-of-two-sites remedy is structural, not another guard | 3 + 12 | approve | comment on #163 |
| 8 | A count of your own effort is a verification claim like any other | 8 + 9 | approve | comment on #54 |
| 9 | An ordinal into someone else's list is a mechanism claim | 9 | approve | comment on #140 |
| 10 | Occurrence; recovery needed the object reachable locally | 13 | approve | comment on #75 |
| — | Doc-budget remedy is a no-op at the default `--keep` | 10 | approve | no ticket — already landed |
| — | `finalize.pr_draft` contradicts the operator's preference | 11 | approve | no ticket — already landed |

### What was verified

The commands and their output are on the PR. Read them there. In summary: the snapshot digest
reproduces from `abbd62f`; all six issues exist with the titles and labels this record claims,
re-read from the tracker after filing; each of the four comments was re-read **by body** on the
issue claimed for it, not merely by the URL the create call returned; `#74` is no longer open and
the `--target-lines` mode it asked for is present in `archive_plan_sessions.py`.

The sweep itself ran under five assertions that abort before any write — snapshot equality, fence
parity, no alteration inside a fenced block, an un-demote round-trip, and per-line survival. The
previous marker recorded the fence count as measured rather than gated, and this run promoted it
to a gate.

**That promotion established nothing, and the run reported so itself.** The script printed
`0 fences preserved`: this inbox contains no fenced blocks at all, so the fence-parity assertion
and the fenced-line comparison both passed over an empty set. They are gates that never reached
their subject — which is [#179](https://github.com/topij/agentic-dev-kit/issues/179), filed
earlier in this same sweep, occurring inside the sweep that filed it. The only reason it is
recorded rather than claimed as coverage is that the script prints the count it asserted on; had
it printed `ok` the vacuous pass would have read as a real one, and that is `#179`'s
negative-control ask in one line.

So the gates that actually bore weight here are snapshot equality, the un-demote round-trip, and
per-line survival — and the round-trip is self-inverting, so it would pass on a corrupted
demotion. Per-line survival is the one doing real work. The fence gates stay in the script
because the archive *does* contain fenced blocks and a future inbox will too; they are simply
unproven today.

**What these checks do not reach.** Two are carried over unchanged: nothing verifies that the
approval happened as described — which matters most precisely because the DM that normally carries
that evidence did not exist — and no automated gate covers any of this
([#127](https://github.com/topij/agentic-dev-kit/issues/127)). One is new and is a direct
consequence of how the issues were checked: the six were confirmed by **title and label**, not by
body, so a mangled body would have passed. The comments were checked more strictly than the issues
were, which is the asymmetry a reader should assume until it is closed.

Above all, nothing here verifies that any filed issue or posted comment is **true**. What this
sweep can say is narrower and worth saying plainly: reading the tracker first is the only step
that caught anything, and what it caught was two entries asking for work that already existed. The
entries were confidently wrong about the state of the repository, and no amount of care in drafting
from them would have surfaced it.

The swept entries are verbatim in the archive under `Graduated 2026-07-31`.

## 2026-07-31 (post-sweep)

- **`make test` fails three tests as root, and the failure reads as a regression rather than as an
  environment fact.** `test_an_unreadable_doc_is_a_documented_exit_2_not_a_traceback` and both
  `test_a_read_failure_names_the_document_that_failed` cases make a doc unreadable with `chmod 000`
  and assert exit 2. Under `uid 0` that permission is a no-op — root reads the file anyway — so the
  tool succeeds and the assertion sees `assert 0 == 2`. **M** — the hazard is the *reading*, not the
  failure: `make test` is the verification command this repo's `CLAUDE.md` names, and an agent that
  runs it in a root container sees three red tests with no signal that they are environmental. The
  honest options are to skip them under `os.geteuid() == 0` with a stated reason, or to make the
  file unreadable by a means root cannot bypass. Established by running `make test` twice from
  `/home/user/agentic-dev-kit` — once with this sweep's two doc edits and once with them stashed —
  and getting the identical three failures and `589 passed` both times; `id -u` reports `0`. Noted
  during the 2026-07-31 sweep and deliberately left below the marker, so the next pass proposes it.
