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
lens, a performance lens): two disjoint lenses is the floor, not the ceiling.

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

   **Beware false kills.** If your repo has a checksum/drift test over the files
   you are mutating (this kit has one: `kit_doctor`'s self-check), *every*
   mutation fails it regardless of behaviour, and a whole run can report 100%
   killed while nothing behavioural caught anything. One lens's first pass here
   reported 17/17 killed; re-run with that test excluded, 7 had survived —
   attested by that lens, not independently measured, since the 17 are
   enumerated nowhere. Quoted for the shape of the effect, not as a figure to
   reproduce.

   **So exclude your repo's drift test before believing a kill** — by node id, by
   marker, by whatever your suite supports. In *this kit's own* repo that test
   carries a `driftcheck` marker, so the invocation is:

   ```
   pytest -m 'not driftcheck'        # in this repo: make mutation-test
   ```

   That marker is this repo's implementation, not a property of your repo. If you
   vendored these tests, check before relying on it: the marker and the conftest
   that registers it live under the tests directory, which is **not** tracked by
   `kit-manifest.json`, so an `/upgrade` will hand you this page without them.

   **Check that the exclusion excluded something.** An `-m` expression naming a
   marker no test carries deselects nothing and warns about nothing — you get a
   normal-looking green run with the drift test still in it. Confirm the run
   reports a `deselected` count, or skip the marker and name the test outright
   with `--deselect <nodeid>`.

   **Regenerating the manifest instead is not the recommended route.** It does
   yield a truthful result, but it is per-mutant bookkeeping that fails silently
   in the confident direction — forget it once and the mutant reads as killed.
   The deeper problem is that it hides its own irrelevance: the drift check goes
   from failing to *passing*, so it looks like a test that was consulted and had
   nothing to say. Deselection reaches the same verdict while leaving the
   evidence on screen — a `deselected` count says plainly that this check did not
   participate. Both routes end in a green run for a surviving mutant; only one
   of them tells you which tests that green was made of (#112).

   **The rule none of this depends on: a kill is only a kill if a test that
   asserts behaviour is the thing that failed.** Check *which* test failed, not
   how many — a test comparing stored text is no more evidence than a test
   comparing stored hashes.
6. **Report, do not fix.** A lens that edits loses the disjointness: it starts
   defending its own changes on the next round.
7. **Mutate in an isolated copy of the repo under review, never the shared
   tree.** Mutation testing needs temporary writes, and lenses run concurrently.
   Discovered the hard way on the PR that added this file: one lens's mutations
   appeared to the other as an external process corrupting the repo, and it
   "restored" them mid-run — so one lens's results were unreliable and the other
   nearly destroyed live work. Give each lens a scratch copy or its own git
   worktree, and require it to leave the shared tree byte-identical.

   **Of the repo under review — check, don't assume.** A runtime's built-in
   isolation usually clones *the session's* repo, which is not the target when
   the cockpit is reviewing a different one (an adopter repo, a sibling
   checkout). On the OpenKitchen upgrade both lenses were handed a worktree of
   the *kit* while reviewing the *adopter*: `git diff <base>...HEAD` was empty in
   both. Both noticed and cloned the real target themselves — but a lens that
   did not would have reviewed an empty diff and reported all-clear, which is
   the worst failure available to a review mechanism.

   So: name the target repo explicitly in the launch prompt, tell the lens to
   **verify it is looking at the right thing before reviewing** (a non-empty diff
   with the expected head), and never state in the prompt that isolation has
   already been arranged unless you have confirmed it. The launch prompt on that
   run asserted "you are in an isolated worktree of that repo" and was wrong.
8. **State what was verified clean, and how.** Absence of findings is only
   evidence if you know what was actually checked.
9. **Give every finding a severity and say whether it is a regression.** The
   stopping section below disposes of findings by both, so a lens that reports
   neither leaves that gate with nothing to read and everything gets filed by
   default. *Regression* means the change is worse at something than what it
   replaced; *imprecision* means it is right but overstated, miscounted, or
   loosely worded. When you cannot tell, say regression — the reviewer is the
   only party here with no stake in the cheaper answer.

## Running it

1. Read the change: `git diff <base>...HEAD`.
2. Launch **one isolated reviewer per lens**, concurrently, each with the
   contract above and its lens focus. Use whatever isolation your runtime has
   (a subagent, a separate session, a second person). If it has none, see
   *Degraded mode*. State the **repo and branch under review** explicitly — see
   contract item 7 on why the runtime's own isolation may not point at it.
3. **Confirm each lens reviewed the right code** before you read its findings: a
   lens reporting a clean pass over an empty or wrong diff looks exactly like a
   lens reporting a clean pass. A finding count of zero is a result only once you
   know what was in front of it.
4. Triage every finding against the *current* code — some go stale across
   rounds.
5. Fix real findings, reply-with-reason to the rest.
6. **Re-run the panel after the fix round.** Not optional: see below.
7. Record the receipt with the lenses that actually ran:

   ```sh
   uv run <engine-dir>/pr_watch.py <PR#> \
     --record-review "<review.fallback_panel.receipt_source>" \
     --lenses <names of the lenses that actually ran> \
     --head <polled-sha>
   ```

   **`--lenses` is self-reported, and the engine does not verify it.** You write
   the source and the lens names in one invocation; nothing binds either to a
   review that happened. Four rounds of this PR tried to verify it from the
   engine — matching the source, then the lens names, then a required roster,
   then a counted one —
   and each was defeated, the last by a single extra character in the source,
   after which the render cheerfully affirmed the forgery.
   `safety-critical-changes.md` rule 1 calls that a stopgap, not a fix.

   So what you get is an **audit trail, not a gate**. The poll render states the
   claim, labelled as a claim, on every poll once a current-head receipt exists
   (no receipt, or one bound to an older head, prints nothing):

   ```text
   review evidence: fallback:codex — ⚠ ONE lens claimed (correctness) — not a dual-lens pass
   ```

   That is genuinely useful — a one-lens pass is visible at merge time instead of
   buried in the record command's stdout — and it is worth exactly what an honest
   operator puts into it. Verifying coverage needs each lens to record its own
   receipt from its own context: issue #32, not this.

## Re-running, and when to stop

`safety-critical-changes.md` rule 3 says to re-review after every fix round
"until a full pass finds nothing new". Take that literally *and* know its limit:
across one session of 13 rounds on three PRs, **every round found something**,
and seven of those findings were defects introduced by the *previous round's
fix*. The termination condition may never arrive.

So the stopping criterion is **blast radius first** — and, for the third class only, a
round count too, because blast radius alone gives a prose loop no way to terminate:

- A **gate, send path, destructive operation, or kill/recovery path** — keep going.
  Worst case is an unreviewed change landing, and the doctrine's operator-merge rule
  applies.
- Something **reported but never acted on** (a warning, a log line, a report
  field) — a round or two is proportionate. Worst case is a wrong message.
- A **record of work already done, that nothing acts on** — **one review round, then
  stop.** See the hard cap below; it is the one class where the round-count guidance
  above does not apply. Membership is functional, not a list of file types: a
  graduation marker, handoff block, friction entry, PR body or commit message qualifies
  *only* if none of these hold. It belongs in the class **above** when:
  - **something executes it.** A commit message, squash message or PR body can carry a
    closing keyword and mutate tracker state — not hypothetical, it is `CLAUDE.md`'s
    standing rule and it fired in the session that produced this cap.
  - **it stands in for a control.** When operator approval is substituted, or a
    receipt's coverage is stated only in prose, the record *is* the control's artifact
    rather than a description of one.
  - **it is the only durable evidence a control was satisfied.** If deleting it would
    leave no way to check the claim, review it like the control.

That same classification decides **which findings to act on before merging**, and it
**narrows step 5 rather than replacing it**. If a change does not clearly sit in one
class, it is the first one — *except* that a record is not promoted by the risk of its
**subject** alone. Reviewing the sweep is first-class work; reviewing the paragraph
describing the sweep is not. That exception is about the subject, and it does not
override the three tests above: a record that carries a control, or is the only
evidence of one, is promoted on its **own** function however dull its subject.

- **First class** — act on every finding. Reply-with-reason stays what step 5 makes
  it, an answer to a nitpick, not a disposal route for something a lens called real.
- **Second class** — act on HIGH, and at any severity on a finding contract item 9
  marks a *regression*. An imprecision — a miscount, a stale cross-reference — may
  instead be **filed**: replied to on the PR with the reason, as step 5 requires,
  *and* recorded where your project tracks deferred work, so it is a disposition
  with an artifact rather than a third option that loses it.

- **Third class** — act on HIGH and on anything a lens marks a *regression*, then
  **stop and file the rest**, whatever the severity distribution looks like.

Severity alone is the wrong discriminator, and this paragraph's own first review
round proved it: no HIGH, and four of its MEDs said the paragraph loosened a control
it claimed to tighten. Know the trade, too — a round that acts on nothing produces
no fix round, so step 6's re-run does not fire and that round stands alone. In the
**first two classes**, do not read the bullet above as licence to stop while severity
is still rising. In the third, rising severity is not a reason to continue — see next.

## The hard cap on reviewing a record

Step 6's re-run is not optional in the first two classes. **For a record it is capped
at one round**, and this section exists because the rule above, without the cap, was
read as licence to run four.

Measured on the session that added this: a friction-log graduation marker drew
**four panel rounds and eight lenses**; a docs audit drew three more; a wrap-up drew
two. Across those nine rounds and fifteen-plus lenses, **no HIGH was ever in executable
behaviour** — every one was in prose. Roughly four findings out of ~78 would have
mattered if shipped, and three of those four were in prose that ships to adopters, not
in the records. The records generated the rest of the work themselves.

Three things follow, and they are the whole content of the cap:

1. **Prose has unbounded surface area.** There is no "the test passes" for a
   paragraph — you can always find another imprecision. A loop pointed at prose does
   not terminate on its own, so it needs a count, not a quality bar.
2. **Rising severity in a record is evidence the loop is eating itself, not that the
   artifact is dangerous.** Each fix round *adds prose*, and added prose is where the
   next round's findings live. On that session, round 2 found the round-1 fix had
   shipped four defects of the same species it removed; round 3 found the same of
   round 2; round 4 found a round-3 fix that had silently matched nothing while its
   commit message reported it landed. Every round's HIGHs were in claims about a
   surface *that round had not re-read*.
3. **A record already carrying corrections should be deleted, not corrected again.**
   Under the cap a record cannot accrue two rounds, so this bites on one that arrives
   with them — inherited from an earlier session, or carried on a branch reviewed under
   the first two classes before it was reclassified. The session's fix was to delete an elaborate verification
   transcript rather than amend it again: the file went 141 → 93 lines and the defect
   surface went with it. Keep the record short, state what the checks do *not*
   establish, and put the detail in the PR — read once, not maintained.

**Shipped prose is not a record.** Docs and config an adopter reads and executes
against — a workflow file, a `# Requires:` header, a docstring, a README instruction —
are code with worse tooling, and they belong in the first or second class. On that same
session the panel's genuinely load-bearing catch was exactly there: a workflow table
described two PR-*mutating* flags as read-only checks, so following it would flip a
deliberately drafted PR to ready. That round earned its keep. The four rounds spent on
the marker describing a completed sweep did not.

**Do not push the gate into the lens prompts.** Severity has to come from a reviewer
who does not know what you consider low-stakes. The change that added rule 3's
fix-round paragraph was docs-only and drew **two HIGH findings**, both real and both
acted on; a lens told to calibrate down for "it's only docs" would have downgraded
precisely those two. It is also the anchoring contract item 2 forbids. Report at
full severity; gate at the point of action.

Say which one you applied **in the PR**, where a human reads it — the receipt
carries what the review did *not* cover (`override`, `bot_signal`,
`bots_behind_head`) and what it did (`lenses`) — not a prose rationale for
stopping. "The last round found
nothing" is not available as a reason if it never happened.

A further lever acts on what a round *contains* rather than on which of its findings
you act on, and it **replaces none of the above** — step 6's re-run stays
not-optional. A separate
session, whose rounds were classified by whether each change had been *asked for*,
found the damage concentrated in one place: across five rounds on one feature,
**three mechanisms were added that no reviewer asked for, and every one became a
HIGH finding in a later round**. The fixes actually asked for held. So make each
round *smaller*, not fewer: `safety-critical-changes.md` rule 3 ("a fix round
addresses only what the review found") — a new mechanism gets filed, however
squarely a finding prompted it.

## Degraded mode

If the runtime cannot run isolated reviewers, fall back to
`review.fallback_commands.<runtime>` — one lens, in the author's context. It is
better than nothing and it is **not** a panel:

- record it as `fallback:<runtime>`, never the panel's `receipt_source`. The
  engine will not stop you doing otherwise — it cannot tell what ran. The
  honesty is entirely yours, which is the reason to write it down
- pass `--lenses` naming what actually ran, so the audit trail shows one lens
- for anything under `safety-critical-changes.md`, say plainly in the PR that
  rule 2 was not satisfied

A receipt should never claim more coverage than the review it stands for.
