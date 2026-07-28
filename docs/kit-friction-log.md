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

## 2026-07-28 — Backlog migrated to GitHub Issues (#112–#125)

The inbox was swept by the `triage-friction-log` workflow. Twenty-four entries in,
twenty-four accounted for: **thirteen graduated** into new issues
([#112](https://github.com/topij/agentic-dev-kit/issues/112)–[#120](https://github.com/topij/agentic-dev-kit/issues/120),
[#122](https://github.com/topij/agentic-dev-kit/issues/122)–[#125](https://github.com/topij/agentic-dev-kit/issues/125)),
**ten** routed as occurrence comments on the issues they are evidence for
(#42, #45 ×3, #54, #74 ×2, #75, #76, #118), and **one** — `make test` being
undiscoverable — recorded as **discharged**, its proposed root `CLAUDE.md` having since
landed. `13 + 10 + 1 = 24`.

[#121](https://github.com/topij/agentic-dev-kit/issues/121) sits inside that numeric
range but came from the sweep itself rather than the inbox: this repo's `tracker:` config
is still `init.sh` placeholder pointing at Linear. #33 also received a comment, but a
cross-reference to #112 rather than one of the ten — see the archive for why that
distinction cost this record an audit.

Everything swept now lives in [`kit-friction-log-archive.md`](kit-friction-log-archive.md).

## 2026-07-28 (second session of the day)

- **A routing list is a claim about tracker state, and nothing verifies it before it is
  committed.** The `#126` sweep's record asserted where each un-graduated entry went. Two
  of those assertions were false at commit time: `#33` was listed among the ten occurrence
  comments when it had received a cross-reference about a *graduated* entry (making the
  list sum to eleven against a stated ten, so "24 in, 24 out" audited to 25), and `#23`
  was named as a routing target by three entries **and by the comment posted to `#45`**
  while receiving nothing at all. Both survived the sweep, the commit, and CI; both were
  caught only by the fallback panel, independently, and the miscount was the panel's only
  HIGH. **M** — proposed fix: before writing the graduation record, re-read the tracker
  and assert that every claimed comment exists on the issue it claims; a routing table is
  cheap to generate and currently impossible to trust. Distinct from `#54` (which asks a
  claim to name its command) — here the claim is about a remote system's state, and the
  verifying command has to run *after* the writes.
- **`pr_watch.py` cannot authenticate in a web session, so the merge gate ran by hand.**
  `uv run scripts/pr_watch.py 126` exits with *"403 Forbidden — the token may lack `repo`
  scope or have expired"*. The gh-less REST transport merged as `#96` reads a token from
  the environment; in this runtime the GitHub credential lives in the MCP server and is
  never exposed to the container. So the one fully-wired engine that arbitrates
  `converged` / `mergeable` is unavailable exactly where `gh` is also absent — which is
  the environment `#96` was built for. Every merge-gate judgement on `#126` was
  reconstructed from MCP calls by hand. **M** — proposed fix: let the REST transport
  accept the runtime's GitHub MCP as a transport, or fail with a message that names the
  MCP fallback instead of implying an expired token.
- **A rate-limited reviewer and an absent one are still the same signal — fourth shape.**
  On `#126` CodeRabbit registered **no check and no comment at all**, well past
  `bot_pending_grace_minutes: 15`. Not a false green, not a rate-limit notice, not a
  pending check. The three shapes recorded before this all left *something* on the PR;
  this one leaves the PR indistinguishable from one whose reviewer simply has not started.
  Nothing but an operator's judgement stopped a silent merge. **No new fix proposed** —
  occurrence data posted to `#45` and `#23`.
- **`#113` reproduced as a setup condition, one day after being filed.** This was a
  second session on 2026-07-28, so `chore/update-handoff-2026-07-28` already existed on
  the remote — the exact precondition that turned `#81` into a 160/249 revert. Avoided by
  branching off fresh `main` under a different name, i.e. by hand, because no mechanism
  exists yet. **No new fix proposed** — second occurrence for `#113`, and worth noting
  that the first occurrence caused damage while this one was caught only because the
  hazard had been filed hours earlier and was still in mind.
- **The panel's worktree pointed at the wrong ref on 2 of 2 launches**, both detected and
  corrected by the lens because the launch prompt required verify-before-review. Recording
  it as its own set: earlier sessions counted launches that isolated *correctly*, and this
  is the first set here where every launch was wrong, so the two cannot be summed. **No
  new fix proposed** — occurrence data for `#75`.
- **`#73` gained an instance that is being kept on purpose.** The swept text carries the
  previous sweep's closing line, *"Everything swept now lives in
  `kit-friction-log-archive.md`"*, which is now a self-link inside the archive it names.
  Left byte-identical because rewriting swept content would destroy the verbatim property
  that makes the archive auditable — so the sweep-warns-on-cross-references fix `#73`
  proposes needs a *warn*, not a rewrite. **No new fix proposed** — occurrence for `#73`,
  with that constraint attached.
- **Four of the panel's ten findings were defects in the PR body, not the diff** —
  including a verification claim that named no command, in the PR filing the issue about
  exactly that. Third consecutive session where the prose carried the errors and the code
  did not. **No new fix proposed** — occurrence data for `#120`, which proposes the
  cheaper message-only terminal check; three sessions of evidence now sit behind it.
