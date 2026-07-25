# The fallback review panel

What to run when your configured review bot can't. Read this whenever
`pr_watch` reports a reviewer as unavailable, and before recording any
`fallback:` receipt.

## Why a panel and not a command

`review.fallback_commands.<runtime>` runs the runtime's own review command — in
the cockpit's context. When the cockpit *authored* the diff, that is the author
re-reading their own work. It finds things; it does not find the things the
author is blind to, which are exactly the ones that survive to production.

`safety-critical-changes.md` rule 2 already says a single-lens verdict "is an
incomplete review, not a green light". A single command cannot satisfy a rule
that asks for two disjoint lenses, so the mechanism was violating the doctrine
it was meant to serve.

**The evidence is disjointness, not volume.** Run as two fresh-context lenses
over one merge-gate change, the panel found a stale outage comment that
reintroduced the exact bug the PR existed to fix; a future-dated clock that
wedged the gate for 30 days *after* the fix for that class shipped; and a
section-scoping fix applied to one of three guards in the same function. The two
lenses overlapped on almost nothing, and the author's own passes had found none
of it.

## The lenses

Configured in `review.fallback_panel.lenses` — **that is where each lens's
brief lives**, as its `focus`, and it is what you hand the reviewer. Restating
the briefs here would give the kit two copies to drift apart, so this section
describes only what the two shipped lenses are *for*:

- **adversarial** — starts from "this is wrong" and tries to prove it.
- **correctness** — starts from "this works" and asks what it *says*.

They are the two the doctrine names, and they are chosen to overlap as little
as possible. Add or replace lenses for your own risk profile (a data-migration
lens, a performance lens): two disjoint lenses is the floor, not the ceiling,
and `--record-review` counts roster lenses without forbidding extras.

## The contract every lens gets

These are why the panel works. Drop any of them and it degrades toward the
author re-reading their own diff.

1. **Fresh context.** A lens that watched the change being written inherits the
   author's model of it, including the wrong parts.
2. **The raw diff, no framing.** Do not tell the lens what the change is *for*,
   what you already fixed, or what you think is risky. That is the anchoring
   the panel exists to escape.
3. **Say it did not write the code.** Cheap, and it measurably changes what a
   lens is willing to call wrong.
4. **Execute, don't only read.** The highest-value findings came from *running*
   the changed paths against hostile input, not from reading them. A guard was
   dead code for the exact bot it was written for, because that bot reports a
   zero timestamp — no amount of re-reading surfaced it; one live poll did.
5. **Mutation-test new branches.** Break the new behaviour deliberately and
   confirm a test fails. Repeatedly, properties were *named* by a test and
   pinned by nothing — hardwiring a branch to a constant still passed the whole
   suite.
6. **Report, do not fix.** A lens that edits loses the disjointness: it starts
   defending its own changes on the next round.
7. **Mutate in an isolated copy, never the shared tree.** Mutation testing needs
   temporary writes, and lenses run concurrently. Discovered the hard way on the
   PR that added this file: one lens's mutations appeared to the other as an
   external process corrupting the repo, and it "restored" them mid-run — so one
   lens's results were unreliable and the other nearly destroyed live work. Give
   each lens a scratch copy or its own git worktree, and require it to leave the
   shared tree byte-identical.
7. **Mutate in an isolated copy, never the shared tree.** Mutation testing needs
   temporary writes, and lenses run concurrently. Discovered the hard way on the
   PR that added this file: one lens's mutations appeared to the other as an
   external process corrupting the repo, and it "restored" them mid-run — so one
   lens's results were unreliable and the other nearly destroyed live work. Give
   each lens a scratch copy or its own git worktree, and require it to leave the
   shared tree byte-identical.
8. **State what was verified clean, and how.** Absence of findings is only
   evidence if you know what was actually checked.

## Running it

1. Read the change: `git diff <base>...HEAD`.
2. Launch **one isolated reviewer per lens**, concurrently, each with the
   contract above and its lens focus. Use whatever isolation your runtime has
   (a subagent, a separate session, a second person). If it has none, see
   *Degraded mode*.
3. Triage every finding against the *current* code — some go stale across
   rounds.
4. Fix real findings, reply-with-reason to the rest.
5. **Re-run the panel after the fix round.** Not optional: see below.
6. Record the receipt with the lenses that actually ran:

   ```sh
   uv run <engine-dir>/pr_watch.py <PR#> \
     --record-review "<review.fallback_panel.receipt_source>" \
     --lenses <names of the lenses that actually ran> \
     --head <polled-sha>
   ```

   `--record-review` **refuses** a receipt whose source is the configured
   `receipt_source` (compared case-insensitively, after stripping) unless `--lenses` names two distinct lenses. Know
   what that is and is not: `source` is free text, so the check catches an
   accidental mislabel, not a determined one — `fallback:panel (2 lenses)` is
   just another string.

   The defence that does not depend on the label is the **poll render**, which
   states the recorded lens count on every poll once a current-head receipt
   exists (no receipt, or one bound to an older head, prints nothing):

   ```text
   review evidence: fallback:codex — ⚠ ONE lens (correctness) — not a dual-lens pass
   ```

   So a one-lens pass reads as one lens at merge time whatever it was called,
   and `--lenses` is what determines that — not the source string.

## Re-running, and when to stop

`safety-critical-changes.md` rule 3 says to re-review after every fix round
"until a full pass finds nothing new". Take that literally *and* know its limit:
across one session of 13 rounds on three PRs, **every round found something**,
and seven of those findings were defects introduced by the *previous round's
fix*. The termination condition may never arrive.

So the stopping criterion is **blast radius, not round count**:

- A **gate, send path, or destructive operation** — keep going. Worst case is an
  unreviewed change landing, and the doctrine's operator-merge rule applies.
- Something **reported but never acted on** (a warning, a log line, a report
  field) — a couple of rounds with the findings decaying in severity is
  proportionate. Worst case is a wrong message.

Say which one you applied **in the PR**, where a human reads it — the receipt
carries what the review did *not* cover (`override`, `bot_signal`,
`bots_behind_head`) and what it did (`lenses`) — not a prose rationale for
stopping. "The last round found
nothing" is not available as a reason if it never happened.

## Degraded mode

If the runtime cannot run isolated reviewers, fall back to
`review.fallback_commands.<runtime>` — one lens, in the author's context. It is
better than nothing and it is **not** a panel:

- record it as `fallback:<runtime>`, never the panel's `receipt_source`. The
  engine refuses a panel-sourced receipt naming fewer than two distinct lenses,
  so the shortest path through it is to record what actually ran — but it cannot
  tell whether a panel really ran, only what you named. The honesty is yours
- pass `--lenses` naming what actually ran, so the audit trail shows one lens
- for anything under `safety-critical-changes.md`, say plainly in the PR that
  rule 2 was not satisfied

A receipt should never claim more coverage than the review it stands for.
