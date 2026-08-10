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

## 2026-08-08 — Backlog migrated to GitHub Issues (#370–#374)

Tenth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Seven entries in, seven accounted for:** five new issues
([#370](https://github.com/topij/agentic-dev-kit/issues/370)–[#374](https://github.com/topij/agentic-dev-kit/issues/374)),
two occurrence comments (`#305`, `#115`), and one entry that routed nowhere new — the cockpit
mutation-harness post-mortem, whose occurrence *and* its "do not mutate the live tree" reframe
were already on `#326` before this sweep began. All seven writes were re-read from the tracker
after landing per `#138` — compared **by body**, with both commented issues confirmed still
open afterwards.

**Approval.** The operator replied `Lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1786168490.379319`) — a bulk approve of all seven, with nothing declined.

**Frozen inbox:** 16,602 bytes, `sha256 d8952f1c…`, reproducing from
`tail -n +14 docs/kit-friction-log.md | shasum -a 256` — run at draft time and again at
finalize, digest matched both times. The current inbox was byte-identical to the snapshot at
finalize, so every block swept and nothing was held back.

**Reading the tracker before drafting changed two routings.** The `panel_prompt.py` entry reads
as already handled — `#214` has landed, the engine ships, and `git grep panel_prompt` now hits
`fallback-review-panel.md` — but that hit is a `lens_compute` config aside, and "Running it"
step 2 still tells you to hand-author every lens prompt. The entry's wording had gone stale
while its substance stood, which is `#373`. The cockpit mutation-harness entry went the other
way: already fully represented on `#326`, so filing anything would have duplicated it. Swept
entries are verbatim in the archive under `Graduated 2026-08-08`.

## 2026-08-09 — un-graduated

### A test that names a property and pins nothing — five instances, one session

Every PR this session had at least one property stated in a comment or docstring and held by
no test, and each was found by a review lens **mutating the line and watching the suite stay
green** — never by reading:

- `#387` — `test_the_adopters_nested_reports_stay_stageable` was written to catch the
  anchoring defect and was masked by its own fixture, which pre-seeded a rule that made an
  earlier guard return first. Reverting the fix left it green.
- `#387` — the prefix branch of `_ignore_rule_exists_for` (negation-only rules).
- `#391` — the escape rule's scoping to double-quoted scalars. **Both lenses found this
  independently.** The PR's own comment calls the asymmetry "an oversight", which is exactly
  the reasoning that would delete the scope later.
- `#389` — "evidence order, not declaration order", the optional-overlay surface, and then
  the depth cap itself, whose test turned out to be measuring `json.loads` rather than the
  cap. That last one is the sharpest instance: the test was written *for* the cap, in
  direct response to a finding about the cap, and still measured something else.

A fifth, later: the same PR's own comment about which states reach the exit code went stale
one round after it was written, inside the same PR. And a sixth, in this very entry — its
heading said "four instances" over a body listing five, and the session's handoff block
carried two wrong counts and two claims that a PR had merged when it had not. A lens caught
all four. Then the rewrite that fixed them stated `#389`'s HIGH count three times, in three
different numbers, none of them right — one sentence after warning the reader that two
figures in that very block had been wrong when a lens counted them. **The pattern is not
about tests; it is about any claim nobody re-derives**, and the session that wrote an entry
about it produced five more instances while doing so, including one inside the caution.

One shape, not five: **a fixture that satisfies an earlier guard hides the later property**,
and the property then lives only in prose. Worth asking whether the mutation step belongs in
the authoring loop rather than only in review — the author wrote all of these believing they
were covered. Related to `#112`, which is about the drift test masking mutation results; this
is the same blindness one layer up.

### The panel is per-PR, and a batch of related PRs pays for it N times

Four PRs from one session's findings needed seventeen rounds — ten on one PR alone — and
upwards of twenty lens runs; count the `## Fallback panel — round N` headers per PR for
the exact figures, which is the point of the neighbouring entry. Each run rebuilds context
on the same repo, and several found the same class of defect independently. There is no
shape in `fallback-review-panel.md` for "these four PRs are one change split by risk class",
which is exactly what Principle #4 asks an author to do. The cost argues against splitting,
which is the wrong pressure to put on that principle.

### `AWK_COMMENT_IDX` cannot carry an apostrophe, and only breaking it tells you

`init.sh`'s shared awk scanner is a single-quoted shell string, so an apostrophe anywhere
inside it — including in a prose comment — ends the string and the next `eval` dies with a
shell syntax error pointing *inside the awk program*, not at the apostrophe. Hit twice in one
session, in two branches, the second time while writing the comment that documents the first.
Now documented above the assignment (`#391`); nothing prevents it.

### 2026-08-09 — a `gh` default limit silently produced a wrong backlog figure

`gh issue list --json number -q '.|length'` returns **30** on a repo with 202 open issues,
because `--limit` defaults to 30 and nothing in the output says so. That number was used in
a readiness assessment before anyone noticed, and it understated the backlog by 6.7×.

The general shape is worth more than the instance: **a paginated API's default limit is a
silent truncation**, and every count taken from one is a claim about the page, not the
population. `session-start`'s tracker step already has a related problem (`#143` — its tool
limit overflows at 68 open issues), so this is the second figure this repo has taken from a
truncated read.

**The rule, stated narrowly enough to be right.** `--limit` is the control for the `gh`
list commands (`gh issue list`, `gh pr list`, `gh run list`); `gh api` pages with
`--paginate` instead, and other tools have their own. Passing a large `--limit` is
necessary and **not sufficient**: if the result count *equals* the limit you asked for, you
have learned nothing about how many more there were. This session demonstrated exactly that
and missed it — `--limit 200` returned exactly 200, which was treated as the population;
`--limit 1000` then returned 202. The check that actually works is to raise the bound until
the count stops moving, or to page explicitly.

### 2026-08-09 — a projection presented as an estimate, from a sample chosen for its answer

Before the July sweep ran, this session projected "roughly 40–50 closes" from a hand-checked
sample of ten. The sample was picked *because* those issues looked already-fixed, so it was
selected on the outcome being measured. The real rate was 18%.

The projection cost nothing here — the sweep ran anyway — but it was offered as a reason to
do the sweep, and a different reader might have declined on a projection of 5%. The rule the
kit already has (`#54`: name the command that establishes a claim) has no equivalent for a
claim about the *future*, where there is no command to name. "Unknown until measured" was
available and was not used.

### 2026-08-09 — a record cited a source no reader inside the repo can reach

The handoff recorded a finding from the adopter session's memo. That memo was delivered as a
**rendered artifact**, not committed to either repo, so its URL is the only pointer to it.

A review lens searched the adopter's PR body, every PR and inline comment, both repos'
`git log --all` and `git grep`, and the adopter's friction log — found nothing, and scored it
**HIGH** as a claim that "does not trace to any source I can find", while noting honestly it
could not rule out a source it had no access to. **It was right to.** From inside the repo
the claim was unverifiable, and an unverifiable claim in a narrative document is a defect
whether or not it happens to be true.

The fix was provenance, not deletion: carry the commands that re-derive the checkable parts
(`git rev-list --count …` → 7) and name the artifact so the next reader knows the rest lives
outside the tree. **The rule:** when evidence arrives from outside the repo — an artifact, a
transcript, a runtime observation with no command to re-run — the record must quote enough to
stand alone or name a command that re-derives it. A URL is a pointer for a human in the same
session; it is not provenance. This is why the Phase 3 work committed its memo *into* the repo.

## 2026-08-10 — un-graduated

### The panel loop terminated by exhausting the author's regressions, not the original defect

`#407` ran the panel to a clean round. Read the `## Fallback panel — round N` comments there
for what each found; the shape is the point rather than the tally. The original two defects
were fixed in the first commit and never re-opened. A later round found a **third original
defect** in the same guard — a fail-open crediting settle time across a rollup dip — and
after that, every finding was about **the fix rounds themselves**: the dip fix was a
permanent wedge, and the wedge fix hollowed test fixtures. The loop ended when that chain
ran out, not when the subject did. Severity: **M** — nothing shipped wrong, but the
doctrine has no reading for the state the loop was in.

`fallback-review-panel.md`'s stopping section says the criterion is blast radius, not round
count, and warns the termination condition may never arrive. Both held. But it offers no
reading for the situation this session was actually in: **every recent finding is about my
own remediation, and none is about the thing under review.** That is a distinguishable state,
and arguably a signal to stop patching and re-derive — which is what finally worked here, the
third anchor being a change of what the clock compares against rather than another edit to the
condition.

Proposed direction, not yet a ticket: give the stopping section a way to name that state.
Something like — when consecutive rounds find only defects introduced by this loop's own fix
rounds, the next move is to re-derive the mechanism rather than to fix the finding. Rule 3
already says a fix round addresses only what the review found; this is the complementary
observation about when the fixes themselves have become the subject. Related: `#410` (one
mechanism by which a remediation creates the next finding), `#209` (proportionality of
re-runs).

**Second occurrence, same day, on `#412`.** The shape recurred with one difference worth the
note: the loop *did* end on a clean full pass of the subject, so it reached
`fallback-review-panel.md`'s first terminal state rather than running out of chain. But
rounds 3, 4 and 5 found no defect in the previous round's fix *itself*, and what they did
find was about my remediation's **test coverage** rather than about the subject — round 4's
worst finding was that the new guard's tests were scaffolding, not that the guard was wrong.
So the state this entry names is reachable even on a loop that terminates correctly, which
argues the stopping section needs a way to *say* which of the two happened rather than only
a rule for when to stop. The proposed direction above still stands; this occurrence narrows
it. The distinguishable signal is "no finding this round was about the code under review".

### A test that mocks the unit under test — filed as `#417`

It recurred through one PR, each time hiding a real defect from a green suite, including a
CRITICAL. Recorded here only as the pointer; the instances and the proposed contract
amendment are on the ticket. Related: the "test that names a property and
pins nothing" entry above — same blindness, one layer down: that one is a property with no
test, this one is a test with no subject.
