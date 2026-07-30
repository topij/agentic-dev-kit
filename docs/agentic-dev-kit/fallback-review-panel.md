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

   **Never write to a tree you did not create yourself.** A runtime may hand a
   lens the live checkout, or a worktree holding somebody's in-progress work — on
   this repo `dev_session.sh` builds lanes with `git worktree add -b`, so "this is
   a linked worktree" does not mean "this is disposable". No git command answers
   *is this tree mine*; that is the launcher's knowledge, not yours. So do not
   re-point, detach, check out or edit whatever you were given. Extract the
   revision into scratch you created, and work there.

   Attest to it in your report: say that you wrote nothing outside your own
   scratch, and name that path (`#136`). Do not offer `git rev-parse HEAD` and
   `git status --short` as the evidence — a detach at the reviewed sha leaves both
   of them unchanged, so they cannot see the failure that matters.

   **Isolating the repo does not isolate the scratch path.** Two lenses with their
   own worktrees both put mutation copies under one shared scratch root, both
   reached for `mut/`, and one reported having deleted the other's (`#136`).
   Namespace by **lens and revision** — `mut-adversarial-<short-sha>/` — not by
   lens alone, or the panel's own re-run collides with your previous round's copy
   at a different head (`#75`). If a file changes underneath you, rule out a
   colliding lens, then treat it as a finding: `#136` exists *because* a lens
   reported it, and a change that writes into the tree looks identical.

   **Assume the worktree points at the wrong ref.** A lens that does not check
   would review an empty diff and report all-clear — the worst failure available to
   a review mechanism, and reason enough on its own. (`#75` and `#163` hold the
   occurrence data; read it there rather than restating a figure here. `#75`'s
   addendum records that its tallies were hand-counted, that some count launches
   which recovered *correctly* while others count launches that pointed *wrong*,
   and that the two do not reconcile.)

   So the launch prompt names the **repo, the branch and the head sha**, and never
   claims isolation has been arranged unless that was confirmed — one prompt
   asserted "you are in an isolated worktree of that repo" and was wrong. Diff
   against the named sha, not `HEAD`:

   ```sh
   git diff <base>...<sha>
   git show <sha>:<path>
   ```

   Both work from a wrong-ref worktree with no copy and no write access, because it
   shares the object database with the checkout it was made from. A branch name
   resolves there too; the reason to pin the **sha** is that a branch *moves*, so a
   stale copy of the right branch passes silently (`#75`).

   Three things the sha alone does not settle:

   - **A writable tree**, which mutation testing needs: extract into your own
     scratch and `git init` it standalone —
     `git archive <sha> | tar -x -C <your-scratch>`. If your sandbox refuses that
     too, report mutation testing as **not performed** rather than skipping it
     quietly; item 5 is then unmet and the cockpit needs to know.
   - **`<base>` can be stale too**, and then the diff is large, non-empty and
     wrong. Check it *without writing* — `git ls-remote <remote> <base>` against
     your local ref, and `git merge-base --is-ancestor`. A fetch would work too,
     but it moves refs in a tree that is not yours.
   - **An unreachable sha has two causes that look identical.** A shallow or
     partial clone of the *right* repo merely lacks the object: fetch it from
     `origin`, the correct remote there. A worktree of the *wrong* repo never had
     it — a runtime's isolation usually clones *the session's* repo, not the target
     when the cockpit reviews a different one (an adopter repo, a sibling
     checkout), as on the OpenKitchen upgrade where both lenses got the *kit* while
     reviewing the *adopter*. Fetch or clone that by **URL or path**, since
     `origin` is the wrong remote by construction. `git show` will not tell you
     which case you are in; `git rev-parse --is-shallow-repository` and the
     remote's URL will.

   Which of these a sandbox permits is **not** doctrine: it varies by runtime and
   has flipped between panels here. Establish what yours allows, and report it.
8. **State what was verified clean, and how.** Absence of findings is only
   evidence if you know what was actually checked.
9. **Give every finding a severity and say whether it is a regression.** The
   stopping section below disposes of findings by both, so a lens that reports
   neither leaves that gate with nothing to read and everything gets filed by
   default. *Regression* means the change is worse at something than what it
   replaced; *imprecision* means it is right but overstated, miscounted, or
   loosely worded. When you cannot tell, say regression — the reviewer is the
   only party here with no stake in the cheaper answer.
10. **State what you reviewed before you state any finding** — required, and not
    as a closing note. Four things: the repo path; the `HEAD` you were **actually
    placed at**, which is the only one of these that observes your environment,
    since the sha you were handed is already in your prompt and echoing it back
    proves nothing (the found HEAD is what produced every occurrence record on
    `#75` and `#163`); the sha you reviewed, with its diffstat; and which routes
    your sandbox allowed **and refused**, plus the scratch path you wrote to — the
    refusals being the half that otherwise never gets recorded anywhere. A lens
    that cannot show a non-empty diff at the named sha **has not reviewed
    anything**, and must say so rather than report a clean pass, because the two
    are otherwise indistinguishable. Non-empty is necessary and not sufficient: a
    diff against a stale base is large and wrong.

## Running it

1. Read the change and resolve the revision you will hand every lens:
   `git diff <base>...HEAD`, then `git rev-parse HEAD`. `HEAD` is right *here* —
   this is the cockpit's own checkout. Item 7 forbids it to a **lens**, whose HEAD
   was chosen by the runtime rather than by anyone who knows the target. Refresh
   `<base>` while you are at it: a stale base here miscalibrates step 3's
   plausibility check as well as every lens's diff.
2. Launch **one isolated reviewer per lens**, concurrently, each with the
   contract above and its lens focus. Use whatever isolation your runtime has
   (a subagent, a separate session, a second person). If it has none, see
   *Degraded mode*. State the **repo, branch and head sha under review**
   explicitly — see contract item 7 on why the runtime's own isolation may not
   point at them, and why the sha is the field that lets a lens recover on its
   own.
3. **Confirm each lens reviewed the right code** before you read its findings,
   against item 10's required fields: the **repo path** is the target repo, the sha
   reviewed is the sha you named, and the diffstat is non-empty *and* plausible for
   the change. Read the **found** HEAD too — it is the only field that reports what
   the runtime actually did, and a lens placed in your live checkout should say so
   there. Read the scratch attestation and the refused routes as well: the first is
   your only evidence the shared tree was left alone, and the second is how a
   sandbox limit reaches you instead of being silently absorbed — including a lens
   that could not obtain a writable tree, whose pass therefore did not satisfy item
   5. A lens reporting a clean pass over an empty or wrong diff looks exactly like
   a lens reporting a clean pass. A finding count of zero is a result only once you
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

So the stopping criterion is **blast radius, not round count**:

- A **gate, send path, destructive operation, or kill/recovery path** — keep going.
  Worst case is an unreviewed change landing, and the doctrine's operator-merge rule
  applies.
- Something **reported but never acted on** (a warning, a log line, a report
  field) — a round or two is proportionate. Worst case is a wrong message.

That same classification decides **which findings to act on before merging**, and it
**narrows step 5 rather than replacing it**. If a change does not clearly sit in one
class, it is the first one.

- **First class** — act on every finding. Reply-with-reason stays what step 5 makes
  it, an answer to a nitpick, not a disposal route for something a lens called real.
- **Second class** — act on HIGH, and at any severity on a finding contract item 9
  marks a *regression*. An imprecision — a miscount, a stale cross-reference — may
  instead be **filed**: replied to on the PR with the reason, as step 5 requires,
  *and* recorded where your project tracks deferred work, so it is a disposition
  with an artifact rather than a third option that loses it.

Severity alone is the wrong discriminator, and this paragraph's own first review
round proved it: no HIGH, and four of its MEDs said the paragraph loosened a control
it claimed to tighten. Know the trade, too — a round that acts on nothing produces
no fix round, so step 6's re-run does not fire and that round stands alone. Do not
read the bullet above it as licence to stop while severity is still rising.

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

## Keep the record small

A record's defect surface is proportional to its length, and every correction round adds
to it. Measured across nine rounds on three PRs in one session: **no HIGH was in
executable code.** One was in a commit message — a closing keyword adjacent to an issue
reference, which closed an issue documenting an unfixed defect before any round found
it, so prose is not the same as inert. Every other HIGH was in prose, and the rounds
that cost the most went to a verification transcript inside a graduation marker, where
each correction added text the next round then found defects in.

What ended that was **deleting** the transcript rather than amending it again: the file
went 141 → 93 lines and the defect surface went with it.

So, when writing a record — a graduation marker, a handoff block, a PR body, a commit
message:

- **State what was done, and what the checks do *not* establish.** Put the detail in the
  PR, where it is read once, rather than in the record, where it is maintained.
- **A record already carrying corrections should be shortened, not corrected again.** A
  claim that has needed repairing twice is doing more work than it can carry; cut it
  back to what you can stand behind.
- **Prose an adopter reads and executes against is not a record.** A workflow file, a
  `# Requires:` header, a docstring, a README instruction — these are code with worse
  tooling and sit in the first class. So does a commit or squash message, which can
  mutate tracker state, and so does any record standing in for a control: when the
  operator-approval step is substituted, the record *is* the control's artifact.

This is guidance on **writing** a record, not on reviewing one. It changes nothing about
which findings a round acts on, or when a loop stops.

**Three attempts to bound that have each opened a hole.** Named because the natural next
proposal is usually one of them:

- **A class for a record of work already done**, defined by file type — marker, handoff
  block, PR body, commit message, friction entry. It explicitly did *not* give docs a
  lighter pass: its own rule said shipped prose an adopter reads and executes against is
  code with worse tooling. It died on the class boundary, not on the idea.
- **The same class with functional tests** — which the handoff *qualified for*, while being
  the file the next session is told to act on.
- **A class-independent stop signal** — whose trigger the author sets by choosing how
  verbose the fix round is.

Their shared shape: each bound is settable by the author of the change under review. The
live two-class gate has that property too — the author picks the class — so it is a
weakness to design against, not a disqualifier on its own. What the shipped gate adds is
that the choice is stated in the PR, where a reviewer can dispute it.

Full accounts, with the evidence: the comment on issue `#120` dated 2026-07-29, and the PR
that added this section.

**A separate question, often confused with these: how many lenses.** None of the three
touched it. Lens count is not bounded by class at all — `safety-critical-changes.md`
rule 2 wants two disjoint lenses, and the only sanctioned single-lens pass is **Degraded
mode** below, which is conditioned on the runtime being unable to isolate reviewers rather
than on what the change contains. A proposal to run fewer lenses for a "smaller" change is
therefore an argument against that rule, not against these three.

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
