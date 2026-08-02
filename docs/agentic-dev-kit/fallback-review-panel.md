# The fallback review panel

What to run when your configured review bot can't. Read this whenever
`pr_watch` reports a reviewer as unavailable, and before recording any
`fallback:` receipt.

This file is **what executes**: the contract, the procedure, the receipt
commands. The measurements behind each rule, and the designs that were tried and
found holed, live in
[`fallback-review-panel-evidence.md`](fallback-review-panel-evidence.md).
Nothing there executes; it exists so a rule is not re-litigated and a buried
design is not re-proposed. You do not need it to run a panel.

**Contract items are named, not numbered.** Cite them by name; the numbers below
are for reading order only and may change (`#167`). Every citation on the kit's
*shipped* surfaces was swept to names when this file was split. This repo's own
narrative logs still carry older numeric citations — records, not instructions —
and some of them no longer resolve to the item they name.

## Why a panel and not a command

`review.fallback_commands.<runtime>` runs the runtime's own review command — in
the cockpit's context. When the cockpit *authored* the diff, that is the author
re-reading their own work. It finds things; it does not find the things the
author is blind to, which are exactly the ones that survive to production.

`safety-critical-changes.md` rule 2 already says a single-lens verdict "is an
incomplete review, not a green light". A single command cannot satisfy a rule
that asks for two disjoint lenses, so the mechanism was violating the doctrine
it was meant to serve.

**The evidence is disjointness, not volume** — the companion has the measured
case.

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

## What compute a lens gets

`review.fallback_panel.lens_compute.<runtime>` sets it, with two independent and
individually optional keys: `model` and `effort`. Set either, both, or neither —
a runtime exposing only one control carries only that key, and omitting a runtime
entirely means its lenses inherit the cockpit session's own compute. That
inheritance is the behaviour that predates the key, so an adopter who never sets
it sees no change.

**Each runtime reaches its own key by its own path**, and the key is inert until
that path exists — so if you add a runtime here, give it one.

- **Claude Code** — `scripts/hooks/pr_followup_hook.py` reads
  `lens_compute.claude` and renders it into the reminder it fires when a PR is
  opened or readied. It reads *only* that key: a value written for another
  runtime must never leak into this one's instruction.
- **Codex** — `.agents/skills/pr-watch/SKILL.md` step 5 names
  `lens_compute.codex`, the same way it names `review.fallback_commands`. No
  Python or shell reads either; the adapter is the consumer.

Do not go looking in the hook for why a non-Claude key had no effect — by design
it will never mention one.

**The two keys do not reach equally far, and the difference is per-runtime.** On
Claude Code today the delegation tool takes a `model` parameter but no per-agent
effort parameter — so `model` is a real control, and `effort` arrives as an
instruction in the lens's prompt, which the lens may or may not act on. Under a
runtime that exposes effort per delegated task it maps directly. Set it either
way; it is honest intent, and it becomes mechanical when the runtime catches up.
Do not record a receipt that implies an effort level was enforced.

**Upgrading an existing install does not add this key.** `init.sh` writes the
whole `fallback_panel` block only when the block is absent, so a repo that
configured a panel before `lens_compute` existed keeps its current block and
silently keeps inheriting the cockpit's compute. That is the safe direction — no
migration rewrites a config you tuned — but it means you add `lens_compute` by
hand. Fresh installs get it.

**A lens does not need the judgment tier.** The measurement, and two cautions
before you copy its numbers, are in the companion.

## The contract every lens gets

These are why the panel works. Drop any of them and it degrades toward the
author re-reading their own diff. **Cite them by name, never by number.**

1. **Fresh context.** A lens that watched the change being written inherits the
   author's model of it, including the wrong parts.
2. **No framing.** Give the raw diff. Do not tell the lens what the change is
   *for*, what you already fixed, or what you think is risky. That is the
   anchoring the panel exists to escape.
3. **Not the author.** Say it did not write the code. Cheap, and it measurably
   changes what a lens is willing to call wrong.
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
   killed while nothing behavioural caught anything — the companion has the
   measured case.

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

   **Regenerating the manifest instead is not the recommended route.** Both
   routes end in a green run for a surviving mutant; only deselection leaves on
   screen which tests that green was made of (`#112`). The companion has the
   full argument.

   **The rule none of this depends on: a kill is only a kill if a test that
   asserts behaviour is the thing that failed.** Check *which* test failed, not
   how many — a test comparing stored text is no more evidence than a test
   comparing stored hashes.
6. **Report, don't fix.** A lens that edits loses the disjointness: it starts
   defending its own changes on the next round.
7. **No writes in the tree you were given.** Mutate in an isolated copy of the
   repo under review, never the shared tree. Mutation testing needs temporary
   writes, and lenses run concurrently — one lens's mutations can appear to
   another as an external process corrupting the repo, and the companion has the
   occasion this was discovered on, where one lens nearly destroyed live work.
   Give each lens a scratch copy or its own git worktree, and require it to leave
   the shared tree byte-identical.

   A runtime may hand a lens the live checkout, or a worktree holding somebody's
   in-progress work — on this repo `dev_session.sh` builds lanes with
   `git worktree add -b`, so "this is a linked worktree" does not mean "this is
   disposable". No git command answers *is this tree mine*; that is the
   launcher's knowledge, not yours. So do not re-point, detach, check out or edit
   what you were given — and do not put your scratch inside it either: a
   *relative* extract path lands in the repo root, where it sits untracked until
   some later `git add -A` commits it. Use an absolute path outside the given
   tree.
8. **Attestation.** Attest to the above in your report — name the scratch path
   you used, and give `git status --short` for the tree you were handed. Be
   precise about what that proves: it catches the untracked-scratch case above,
   and it does **not** catch a detach at the reviewed sha, which changes no byte
   and no HEAD. It is evidence for one of the two failures, not both (`#136`).
9. **Scratch namespace.** Isolating the repo does not isolate the scratch path.
   Two lenses with their own worktrees both put mutation copies under one shared
   scratch root, both reached for `mut/`, and one reported having deleted the
   other's (`#136`). Namespace by **lens and revision** —
   `mut-adversarial-<short-sha>/` — not by lens alone, or the panel's own re-run
   collides with your previous round's copy at a different head (`#75`). If a
   file changes underneath you, rule out a colliding lens, then treat it as a
   finding: `#136` exists *because* a lens reported it, and a change that writes
   into the tree looks identical.
10. **Right revision.** Assume the worktree points at the wrong ref. A lens that
    does not check would review an empty diff and report all-clear — the worst
    failure available to a review mechanism, and reason enough on its own.
    (`#75` and `#163` hold the occurrence data; read it there rather than
    restating a figure here. **Those tallies are approximate** — counted by hand,
    counting different populations, and two of them do not reconcile. The
    companion has that account.)

    So the launch prompt names the **repo, the branch and the head sha**, and
    never claims isolation has been arranged unless that was confirmed — one
    prompt asserted "you are in an isolated worktree of that repo" and was wrong.
    Diff against the named sha, not `HEAD`:

    ```sh
    git diff <base>...<sha>
    git show <sha>:<path>
    ```

    Both work from a wrong-ref worktree with no copy and no write access, because
    it shares the object database with the checkout it was made from. A branch
    name resolves there too; the reason to pin the **sha** is that a branch
    *moves*, so a stale copy of the right branch passes silently (`#75`).

    Three things the sha alone does not settle. Each says what has to be true
    rather than which command gets you there: what an invocation actually does
    here depends on how your runtime built the tree, so establish and report your
    own route.

    - **A writable tree**, which mutation testing needs, has to be a copy you
      made. Extracting an archive and cloning with `--no-hardlinks` both reach
      the revision from a source you cannot write to. If your sandbox refuses
      every route, report mutation testing as **not performed** rather than
      skipping it quietly: **Mutation-test new branches** is then unmet and the
      cockpit needs to know.
    - **`<base>` has to be current.** A stale base yields a large, non-empty,
      wrong diff that satisfies every other check here. Establish it against the
      *remote*, not against your local ref — and note that an ancestry test does
      not do this, since a stale base is still an ancestor. Say in your report how
      you established it.
    - **An unreachable sha does not tell you why it is unreachable.** A shallow or
      partial clone of the *right* repo merely lacks the object; a tree of the
      *wrong* repo never had it — the OpenKitchen case, where both lenses got the
      *kit* while reviewing the *adopter*, and both fetched the real target.
      Comparing your remote's URL against the target distinguishes them. Either
      way, bring the objects into a copy you made instead of fetching into the
      tree you were handed: a fetch writes refs, and that tree is not yours.

    Which of these a sandbox permits is **not** doctrine: it varies by runtime and
    has flipped between panels here. Establish what yours allows, and report it.
11. **Verified clean.** State what was verified clean, and how. Absence of
    findings is only evidence if you know what was actually checked.
12. **Severity and regression.** Give every finding a severity and say whether it
    is a regression. The stopping section below disposes of findings by both, so a
    lens that reports neither leaves that gate with nothing to read and everything
    gets filed by default. *Regression* means the change is worse at something than
    what it replaced; *imprecision* means it is right but overstated, miscounted, or
    loosely worded. When you cannot tell, say regression — the reviewer is the
    only party here with no stake in the cheaper answer.
13. **Report what you reviewed, first** — required, and not as a closing note.
    Give the repo path; the `HEAD` you were **actually placed at**, which is the
    only one of these that observes your environment, since the sha you were
    handed is already in your prompt and echoing it back proves nothing (the found
    HEAD is what produced every occurrence record on `#75` and `#163`); the sha you
    reviewed, with its diffstat; how you established that `<base>` is current;
    which routes your sandbox allowed **and refused**, the refusals being the half
    that otherwise goes unrecorded anywhere; and **Attestation**'s report — your
    scratch path, or that you wrote nothing. A lens that cannot show a non-empty
    diff at the named sha **has not reviewed anything**, and must say so rather
    than report a clean pass, because the two are otherwise indistinguishable.
    Non-empty is necessary and not sufficient: a diff against a stale base is
    large and wrong.

## Running it

1. Read the change and resolve the revision you will hand every lens:
   `git diff <base>...HEAD`, then `git rev-parse HEAD`. `HEAD` is right *here* —
   this is the cockpit's own checkout. **No writes in the tree you were given**
   forbids it to a **lens**, whose HEAD was chosen by the runtime rather than by
   anyone who knows the target. Refresh `<base>` while you are at it: a stale base
   here miscalibrates step 3's plausibility check as well as every lens's diff.
2. Launch **one isolated reviewer per lens**, concurrently, each with the
   contract above and its lens focus. Use whatever isolation your runtime has
   (a subagent, a separate session, a second person). If it has none, see
   *Degraded mode*. State the **repo, branch and head sha under review**
   explicitly — see **Right revision** on why the runtime's own isolation may not
   point at them, and why the sha is the field that lets a lens recover on its
   own.

   Build each lens's review tree yourself when the runtime lets you hand one
   over: a detached worktree at the named sha, outside the repo, namespaced by
   lens and revision —

   ```sh
   git worktree add --detach <scratch>/lens-<name>-<short-sha> <sha>
   ```

   — and name that path in the launch prompt (remove the worktrees when the
   round ends). The cockpit is the only party that knows the target;
   runtime-provided isolation routinely lands at the wrong ref (`#75` holds
   the occurrence data; read it there rather than a figure here, and note its
   own tallies say they are **approximate**). A cockpit-built tree turns that
   per-lens recovery burden
   into a confirmation. Nothing in **No writes in the tree you were given** or
   **Report what you reviewed, first** relaxes: the tree is still not one the lens
   created (its mutation copies stay its own), and it still reports the HEAD it
   actually found — the defence that remains for a sandbox that re-homes the lens
   anyway.
3. **Confirm each lens reviewed the right code** before you read its findings,
   against **Report what you reviewed, first**'s required fields: the sha reviewed
   is the sha you named, and the diffstat is non-empty *and* plausible for the
   change. Compare the reported **repo path against your own** — not merely against
   "is it the target repo", which your live checkout satisfies too, being the target
   repo. That comparison is the only thing that catches a lens placed in your working
   tree; the found HEAD cannot, because a correctly isolated worktree reports the same
   sha. Read the scratch attestation and the refused routes as well: the first is your
   evidence the tree was left alone, and the second is how a sandbox limit reaches you
   instead of being silently absorbed — including a lens that could not obtain a
   writable tree, whose pass therefore did not satisfy **Mutation-test new branches**.
   A lens reporting a clean pass over an empty or wrong diff looks exactly like a lens
   reporting a clean pass. A finding count of zero is a result only once you know what
   was in front of it.
4. Triage every finding against the *current* code — some go stale across
   rounds.
5. Fix real findings, reply-with-reason to the rest.
6. **Re-run after the fix round.** Not optional — whether it is the full panel
   or one lens over the delta is decided below: first by whether the change
   sits under `safety-critical-changes.md`, which never takes the delta pass,
   then by what the fix round's delta contains.
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
   engine and each was defeated — the companion has the four attempts.
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
measured across one session, **every round found something**, and several of
those findings were defects introduced by the *previous round's fix*. **The
termination condition may never arrive.** The companion has both measurements —
the round counts, and a second one on a diff with no shipped behaviour at all.

So the stopping criterion is **blast radius, not round count**:

- A **gate, send path, destructive operation, or kill/recovery path** — keep going.
  Worst case is an unreviewed change landing, and the doctrine's operator-merge rule
  applies.
- Something **reported but never acted on** (a warning, a log line, a report
  field) — a round or two is proportionate. Worst case is a wrong message.

That same classification decides **which findings to act on before merging**, and it
**narrows step 5 rather than replacing it**. If a change does not clearly sit in one
class, it is the first one.

- **First class** — act on every finding, with the one carve-out defined below: a
  record-prose *imprecision below HIGH, as the lens marked it,* is logged
  rather than fixed. A
  HIGH is acted on in every class; for record prose the act is deletion or
  shortening. Reply-with-reason stays what step 5 makes it, an answer to a
  nitpick, not a disposal route for something a lens called real.
- **Second class** — act on HIGH, and at any severity on a finding the
  **Severity and regression** item marks a *regression*. An imprecision below HIGH — a
  miscount, a stale cross-reference — may
  instead be **filed**: replied to on the PR with the reason, as step 5 requires,
  *and* recorded where your project tracks deferred work, so it is a disposition
  with an artifact rather than a third option that loses it.

**Severity alone is the wrong discriminator**, and this paragraph's own first
review round proved it — the companion has that case. Know the trade, too — a
round that acts on nothing produces no fix round, so step 6's re-run does not fire
and that round stands alone. Do not read the bullet above it as licence to stop
while severity is still rising.

**A prose finding is then disposed of by what the text *is*, not only by the
change's class.** The discriminator — measured on `#163`, where a whole round's
findings were prose about the work — is: **does anything execute this text?**

- **Executed prose** — a workflow step an agent follows, an error message an
  operator acts on, an exit-code table a caller branches on, a config remedy
  string, a `▶ Next:` starter, a commit or squash message (it can mutate
  tracker state). Behaviour with worse tooling: the two classes above apply
  unchanged.
- **Record prose** — narration of work already done: why an earlier version was
  wrong, what a round found, a count of the author's own effort. Nothing
  executes it, in either class — a gate PR's record prose is still record. A
  *regression* here is repaired by **deleting or shortening** the claim, not by
  amending it ("Keep the record small" below has the measured base). An
  *imprecision* below HIGH — a miscount, a drifted ordinal — is **logged, not
  fixed**, and only under the label the reviewing lens gave it
  (**Severity and regression**): a
  lens-marked *regression* is never logged, and a HIGH imprecision is deleted
  or shortened like a regression, never logged. Logging means
  reply-with-reason on the PR,
  plus an occurrence comment on the tracker issue that owns the class — opened
  if none exists. That artifact is stricter than the second class's "where
  your project tracks deferred work": it must exist at disposition time, and
  it must live outside the repo tree. **A logged finding produces no commit** —
  that is the mechanism, not a convenience: no commit leaves the current-head
  receipt standing and gives step 6 no fix round to re-review, which is the
  only exit this loop has that does not cost a round. In a mixed round, other
  findings force a commit anyway and that mechanism lapses; the logged
  finding still stays out of the commit — there, "Keep the record small"
  carries the rule alone. The log lives on the PR
  and the tracker, never in a committed file: a committed log would invalidate
  the receipt it exists to preserve, and become one more budgeted record to
  keep true.

Classify the **claim, not the file** — the handoff carries both kinds in
adjacent sentences: its `▶ Next:` line is executed by the next session; the
round count beside it is record. The first two buried designs in the companion — both
scoped by file — died on exactly that boundary. Whether anything reads a string is a fact about
the repo and its consumers, not a bound the author sets — which is the property
all three buried designs lacked. Establish it fail-closed: a repository search
finds consumers, but a missing match does not prove there are none (a runtime
workflow, a hosting integration, a generated artifact, an operator acting on
what they read) — **when in doubt, the text is executed prose**, the same
default the two classes above already use. The author still *applies* the
discriminator, so each logged disposition is stated in the PR, where a reviewer
can dispute the classification. Full-panel lens prompts are untouched by all
of this — the next paragraph stands. The one exception is the delta lens
below, handed the author's stated draws precisely in order to dispute them:
an anchoring accepted deliberately, like the delta boundary itself.

**Do not push the gate into the lens prompts.** Severity has to come from a reviewer
who does not know what you consider low-stakes. A docs-only change drew **two HIGH
findings**, both real and both acted on; a lens told to calibrate down for "it's only
docs" would have downgraded precisely those two — the companion names which change.
It is also the anchoring **No
framing** forbids. Report at full severity; gate at the point of action.

Say which one you applied **in the PR**, where a human reads it — the receipt
carries what the review did *not* cover (`override`, `bot_signal`,
`bots_behind_head`) and what it did (`lenses`) — not a prose rationale for
stopping. "The last round found
nothing" is not available as a reason if it never happened.

A further lever acts on what a round *contains* rather than on which of its findings
you act on, and it **replaces none of the above** — step 6's re-run stays
not-optional. Measured on a separate session, the damage was concentrated in one
place: **mechanisms added that no reviewer asked for became HIGH findings in a later
round**, while the fixes actually asked for held — the companion has the counts and
the trap inside them. So make each round *smaller*, not
fewer: `safety-critical-changes.md` rule 3 ("a fix round addresses only what the
review found") — a new mechanism gets filed, however squarely a finding prompted it.

**When that rule was not followed, withdraw rather than patch.** The filing rule
is prevention; this is its recovery, and it exists because the prevention was
measured failing. A mechanism a round-1 finding prompted was built rather than
filed, and every later round then found a HIGH *inside that mechanism* while the
rest of the change drew nothing — rounds 2–5 reviewed the fixes, not the work.
The signal is not a round count but **a fix that itself draws a HIGH, twice, in
the same mechanism**: patching further is evidence-free, each patch a fresh guess
at a problem the last guess misread. Take the mechanism out, file it with what
defeated it, and let the round that removes it be the last — removal is the
cheapest round there is, deleting surface rather than adding more for the next
round to find.

**Declare the withdrawal threshold before seeing a round's findings**, beside the
stopping criterion. Named in advance it is a decision; reached afterwards it is
indistinguishable from fatigue, and no reviewer can tell which it was.

**Batch the fix round into one commit and one push, and aim the re-run at the
delta.** Each push invalidates the current-head receipt, so each new head
costs another required review — a fix round landed as four pushes buys four
times the review its content needs. Land the round's accepted fixes together,
then hand the next round `git diff <last-reviewed-sha>...<head>` as its
highest-risk surface with the full diff still in scope. Naming that boundary
reveals what a prior round covered — anchoring of a kind, accepted
deliberately because the full diff stays in scope, and bounded by taking
`<last-reviewed-sha>` from the recorded receipt's `--head` rather than from
the author's memory. (Promoted to doctrine without the cost measurement `#163`
Sink 2 asked for — the companion records that gap.)

**Step 6's full panel is for a delta that contains behaviour.** A fix round
that touched executable code or executed prose gets the full re-run,
unchanged — and a change under `safety-critical-changes.md` never takes this
exit at all: rule 2 requires both lenses **before merge**, and under
head-bound receipts that means the pass standing at the merging head is the
panel, whatever the last delta contained. Whether a change sits under that
file at all is itself an author-drawn boundary — state that draw in the PR
alongside the prose class. Elsewhere, a fix round whose delta is record
prose only — deletions, trims, messages that act on nothing — contains
nothing that acts, and the proportionate re-check is **one lens over that
delta**: isolated, fresh-context, drawn from the panel's configured lenses
(`review.fallback_panel.lenses`), not minted for the occasion, and recorded
honestly as a single-lens receipt — source the literal `fallback:delta`,
never Degraded mode's `fallback:<runtime>` (an author-context run the audit
trail must stay able to tell apart) and never
`review.fallback_panel.receipt_source` — with `--lenses` naming the one that
ran and `--head` the polled sha. Expect the poll render to flag any one-lens
receipt; for a sanctioned delta pass that flag is the audit trail speaking,
not an instruction to run the panel the pass replaced. **The delta is the
diff plus the commit messages that land it** (`git log
<last-reviewed-sha>..<head>` — a message appears in no diff). A message is
executed prose by class, so the test on it is what executing it does: the
pass requires messages that act on nothing — no closing keyword near a
reference, no instruction to a future reader, no claim a process consumes.
The delta lens reads both surfaces, and its first duty is to dispute both
stated draws — the prose class and the safety-critical boundary; "confirmed"
means both are confirmed, and either dispute forbids the receipt. The launch
prompt requires the lens to end its report with **one verdict line per
draw**. **Both lines are posted on the PR by the cockpit, verbatim, before
any `fallback:delta` receipt is recorded** — quoting both is what closes
selective quotation, and the posting is self-reported, like the receipt:
the verdict lines appear nowhere in git history, and the posted lines are
what make "no verdict yet" distinguishable from "confirmed" — so they get the same
outside-the-tree artifact rule the logged disposition carries. **A disputed
prose class is a behaviour-containing delta** — the full panel is owed. **A
disputed safety-critical boundary is stronger**: treat the change as sitting
under `safety-critical-changes.md` until the dispute is resolved — and the
resolution is an artifact the operator authors on the PR, existing before
any receipt or merge, never a relayed account by the party that drew the
boundary — with the
panel at the merging head, and operator-merge, never a self-merge over it. Know
also what the engine retains: it keeps one receipt per PR, so recording
`fallback:delta` replaces the panel receipt that evidenced the initial full
panel — the posted verdict and the PR record become the surviving evidence
that the floor was met. A logged disposition that produced no commit
needs less still: there is no new head, so there is nothing to re-review.
This is the second sanctioned single-lens pass, beside Degraded mode —
conditioned on what the delta contains, not on what the author considers
low-stakes. The delta pass moves no floor: a PR's initial review takes the
full panel — or Degraded mode, only where isolation is impossible — never a
delta pass. The author still draws the class, states it in the PR, and can
draw it wrong — the same design-against weakness the live two-class gate
above carries.

## Keep the record small

A record's defect surface is proportional to its length, and every correction
round adds to it. Measured across one session, **no HIGH was in executable
code** — the companion has the figures and the one case that shows prose is not
the same as inert. What ended the most expensive loop was **deleting** the
offending transcript rather than amending it again.

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

**Three attempts to bound that have each opened a hole**, and their shared shape:
**each bound is settable by the author of the change under review.** The
companion names all three, because the natural next proposal is usually one of
them. The live two-class gate has that property too — the author picks the class
— so it is a weakness to design against, not a disqualifier on its own. What the
shipped gate adds is that the choice is stated in the PR, where a reviewer can
dispute it.

**A separate question, often confused with these: how many lenses.** None of the three
touched it. Lens count is not bounded by class — `safety-critical-changes.md`
rule 2 wants two disjoint lenses **before merge**, and the two sanctioned
single-lens passes are this file's own refinements, not readings of that rule:
**Degraded mode** below, conditioned on the runtime being unable to isolate
reviewers, and the **record-prose delta pass** in the stopping section,
conditioned on what a fix round's delta contains — and excluded outright for a
change under `safety-critical-changes.md`, whose merging head needs both
lenses whatever the last delta contained. Each condition is a fact about the
environment or the repo, not about what the change is worth. A proposal to run
fewer lenses for a "smaller" change is still an argument against that rule,
not against these three.

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
