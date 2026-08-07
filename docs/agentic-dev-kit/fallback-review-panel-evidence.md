# The fallback review panel — evidence and buried designs

The companion to [`fallback-review-panel.md`](fallback-review-panel.md).

**Nothing here executes.** Every rule an agent follows lives in that file; this
one holds the measurements behind those rules, and the designs that were
proposed, adopted, and found holed. You do not need this file to run a panel.

It exists for two readers: someone deciding whether a rule still earns its place,
and someone about to re-propose a design that has already been buried. The
sections mirror the order of the executing file.

Figures here were counted by hand from session transcripts unless stated
otherwise, and several are recorded as approximate on their tracker issues. Treat
them as the shape of an effect, not as numbers to reproduce.

## Why a panel and not a command

**The evidence is disjointness, not volume.** Run as two fresh-context lenses
over one merge-gate change, the panel found a stale outage comment that
reintroduced the exact bug the PR existed to fix; a future-dated clock that
wedged the gate for 30 days *after* the fix for that class shipped; and a
section-scoping fix applied to one of three guards in the same function. The two
lenses overlapped on almost nothing, and the author's own passes had found none
of it.

## What compute a lens gets

**A lens does not need the judgment tier.** Measured on this repo, 2026-08-01,
over two real Sonnet panels — a docs PR (~196k output tokens) and a code PR
(~167k). Both produced findings the cockpit had missed: a stale verified-output
claim presented as literal command output, and a root-container run the cockpit
had declared impossible. Lens work is bounded and adversarial rather than
open-ended, so `effort` carries more of the weight than model tier does.

Two cautions before you copy the numbers. Cost tracked **claim density**, not code
complexity — the *docs* PR was the expensive one, because verifying prose meant
re-reading five issues, two comments and a chat thread. And a panel that finds
nothing has not necessarily been cheap or thorough; read what it *executed*, which
is why the contract demands attestation rather than a verdict.

## Mutation-test new branches

### The false-kill measurement

One lens's first pass here reported 17/17 killed; re-run with the drift test
excluded, 7 had survived — attested by that lens, not independently measured,
since the 17 are enumerated nowhere. Quoted for the shape of the effect, not as a
figure to reproduce.

### Why regenerating the manifest is not the recommended route

It does yield a truthful result, but it is per-mutant bookkeeping that fails
silently in the confident direction — forget it once and the mutant reads as
killed. The deeper problem is that it hides its own irrelevance: the drift check
goes from failing to *passing*, so it looks like a test that was consulted and had
nothing to say. Deselection reaches the same verdict while leaving the evidence on
screen — a `deselected` count says plainly that this check did not participate.
Both routes end in a green run for a surviving mutant; only one of them tells you
which tests that green was made of (`#112`).

## No writes in the tree you were given

Discovered the hard way on the PR that added the executing file: one lens's
mutations appeared to the other as an external process corrupting the repo, and
it "restored" them mid-run — so one lens's results were unreliable and the other
nearly destroyed live work.

## Right revision

`#75` and `#163` hold the occurrence data for lenses placed at the wrong ref.
Read it there rather than restating a figure here. Their own comments record that
the tallies were counted by hand, that different ones count different
populations, and that two of them do not reconcile.

## Recording the receipt — why `--lenses` is not verified

Four rounds of the PR that added the receipt tried to verify the lens roster from
the engine — matching the source, then the lens names, then a required roster,
then a counted one — and each was defeated, the last by a single extra character
in the source, after which the render cheerfully affirmed the forgery.
`safety-critical-changes.md` rule 1 calls that a stopgap, not a fix. `#32` holds
the four attempts in full, and the shape that would actually work: a receipt each
lens records from its own context.

## Re-running, and when to stop

### The base rate behind "the termination condition may never arrive"

Across one session of 13 rounds on three PRs, **every round found something**, and
seven of those findings were defects introduced by the *previous round's fix*.

A second measurement reproduced it closer to the limiting case. On a **test-only**
diff (404 insertions across 5 files), seven full panel rounds produced **zero**
findings in the code under repair — the two function bodies under repair were
byte-identical from the first commit to the merge, independently verified by a
round-6 lens diffing the code region across all six shas. Every finding was an
unpinned property or a claim outrunning what was verified, and rounds 3 through 6
each found a defect in the previous round's remediation. `#209` and `#120` hold
the round-by-round split.

### Why severity alone is the wrong discriminator

The executing file's "**Severity alone is the wrong discriminator**" paragraph had
its own first review round prove it: **no HIGH, and four of its MEDs said the
paragraph loosened a control it claimed to tighten.**

### Why the gate must not go into the lens prompts

The change that added `safety-critical-changes.md` rule 3's fix-round paragraph
was docs-only and drew **two HIGH findings**, both real and both acted on. A lens told to calibrate down for
"it's only docs" would have downgraded precisely those two.

### Why fix rounds must be smaller, not fewer

A separate session, whose rounds were classified by whether each change had been
*asked for*, found the damage concentrated in one place: across five rounds on one
feature, **three mechanisms were added that no reviewer asked for, and every one
became a HIGH finding in a later round** — two of them built in direct response to
a real MED, which is the trap. The fixes actually asked for held. (That last
clause is `safety-critical-changes.md` rule 3's own wording, quoted from the
sibling doctrine file rather than from a tracker issue — a review lens went
looking for it on the tracker and could not source it.)

### The cost measurement that does not exist

`#163` Sink 2 asked for a cost measurement before "aim the re-run at the delta"
became doctrine. None exists. It was promoted anyway, deliberately, with the
full-diff-in-scope clause carrying that risk. Trialed on `#160` from round 4.

### Why a lens-prescribed fix still takes the full panel

The direction "a fix the lens itself specified is self-validating and needs no
fresh adversarial pass" was declined with the `#209` decision (2026-08-03): on
`#202`, rounds 3 through 6 each found a defect **in the previous round's
remediation** — on that evidence the remediation is the loop's most
defect-dense surface, precisely because it is small, written to a
lens-supplied specification, and usually a new check that nothing else checks
(`#211` has the mechanism). Exempting that class is exempting the surface
where the defects are.

### The categorical no-delta-exit for safety-critical changes — narrowed 2026-08-07

Until 2026-08-07 the stopping section closed the delta pass entirely for a
change under `safety-critical-changes.md`: rule 2 wants both lenses before
merge, and under head-bound receipts that was read as "the pass standing at
the merging head is the panel, whatever the last delta contained".

What that priced, measured on PR `#328` (the occurrence is on `#305`): a full
two-lens panel found exactly one finding — Low severity, lens-marked
*regression*, a comment paragraph duplicated verbatim in `init.sh`. A
lens-marked regression is never logged, so the rule said fix; the categorical
rule said the fix's new head owed a full panel — ~250k output tokens, ~20
minutes on that PR's measurement — to review a three-line deletion. The
operator chose record-rather-than-repair, shipping the known defect, for the
second time in two days (2026-08-05 was the same call on the same defect
class). A rule that prices a trivial repair above shipping a defect does not
hold: it gets overridden ad hoc, the defect stays in, and the override is
legible only as prose (`#194`).

The narrowing keeps the class's floor and moves the price. A record-prose-only
delta on a safety-critical change now takes **both** configured lenses over
the delta instead of a full panel at the new head; two-lens coverage of the
merging head is composed — panel at the reviewed head, dual delta pass over
everything after it — rather than delivered by one pass. The dual form
presupposes a full-panel review standing at the reviewed head: after a
Degraded-mode initial review there is nothing to compose with, and rule 2
stays unmet, said plainly in the PR. The single-lens exit stays closed for
the class, any disputed verdict still owes the full panel, and
operator-merge is untouched.

Composition's assumption — a record-prose delta interacts with nothing — is an
author-drawn draw, the property every buried design above died on. Two things
answer it, short of a guarantee: both delta lenses dispute the draw
independently, first-duty, verdicts posted verbatim before any receipt; and
the executing file's deletion rule makes text that bounded executed prose
executed prose itself. That rule's measurement is PR `#218` (recorded in
`#209`'s 2026-08-01 comment): a caveat bounding the wrong-ref rule was dropped
at two of the three sites it appeared, leaving an instruction resting on
figures a reader would take as firm — and the round whose diff already
contained the loss walked past it once before the next round caught it. Two
lenses are rule 2's floor, not a proof.

Rejected on the way here, so it is not re-proposed: pricing the *duty*
instead — a severity floor under which a lens-marked regression may be logged
rather than fixed on a safety-critical PR. That legitimises shipping known
defects and weakens the one rule that forces repairing real damage, to solve
what the occurrences show is a pricing problem.

Deferred, recorded on `#305`: whether the ordinary class's single-lens delta
pass should also take two lenses — `#268` round 2 measured overlap-0
disjointness between lenses on a delta small enough that a single lens looks
sufficient, which argues the second lens is load-bearing even there; against
it, the cost roughly doubles on every PR with a fix round. Not decided here.

## Keep the record small

### The measurement

Measured across nine rounds on three PRs in one session: **no HIGH was in
executable code.** One was in a commit message — a closing keyword adjacent to an
issue reference, which closed an issue documenting an unfixed defect before any
round found it, so prose is not the same as inert. Every other HIGH was in prose,
and the rounds that cost the most went to a verification transcript inside a
graduation marker, where each correction added text the next round then found
defects in.

What ended that was **deleting** the transcript rather than amending it again: the
file went 141 → 93 lines and the defect surface went with it.

### Three attempts to bound that have each opened a hole

Named because the natural next proposal is usually one of them:

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
that added the "Keep the record small" section.
