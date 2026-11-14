# Principles — a portable development model for AI-agent-driven codebases

These principles come from running interactive and unattended coding sessions with
a human operator who makes the final decisions about risk. The Full profile puts
them into practice with worktrees, pull requests, checks and independent review.
Lite uses the handoff, friction inbox and staged-change review in a smaller project.
See [the profile comparison](README.md#choose-an-install-profile) for the install
decision and [architecture](docs/architecture.md) for how the parts work together.

## 1. Living-plan handoff

**Statement.** Keep a forward-looking plan in the repository. Each open workstream
has a place where the next session can find its status, its owner and its next
action. A commit records what changed. The plan holds the context needed to
continue, such as a design decision that the commit and tracker leave unsaid.

**Failure it prevents.** A fresh session sees that an endpoint shipped, but only
the previous conversation says who must choose the rollout date. A handoff entry
that names the decision and its owner lets work resume without reconstructing the
conversation. Copying every merged change into the same file would bury that entry.

**Mechanism.** Read the plan at session start. On Full, run the handoff test before
each PR's opening review. Add a record on that branch when the work leaves
something to hand over. A lane sends its record to the cockpit. On Lite, include
needed plan edits in the staged change that wrap-up reviews. Both routes give
the next session a plan it can act on. [Full handoff](docs/agentic-dev-kit/workflows/wrap-up.md) · [Lite handoff](docs/agentic-dev-kit/lite/lite-wrap-up.md)

## 2. Friction flywheel

**Statement.** Capture friction while the evidence is available. Give a finding
a destination based on what the session knows and what the operator has approved.

**Failure it prevents.** A setup failure disappears with the terminal that showed
it. Or someone responds to the first occurrence by adding a permanent rule for
every subsequent session. Recording the failing step and what remains to be
learned gives the next attempt a starting point.

**Mechanism.** On Full, an issue-shaped finding has a reproduction, a named
mechanism and a proposed fix. Search the tracker for existing work and present the
exact filing for approval. Park a finding in the inbox when it needs diagnosis,
needs to recur, or cannot be filed. Triage freezes the inbox for decisions about
its entries. A separate workflow examines findings from *merged PR reviews* for
recurring causes. When a change is warranted, try to remove the cause, then look
for a check that catches it, and reserve prose for decisions requiring judgement.
Lite routes explained findings through the project's configured friction route.
[Full routing](docs/architecture.md#friction-flywheel) · [Lite wrap-up](docs/agentic-dev-kit/lite/lite-wrap-up.md)

## 3. Cockpit + isolated lanes

**Statement.** When multiple threads of work run at once — especially with
autonomous or semi-autonomous agents — each thread gets its own isolated
workspace (a separate checkout/worktree, its own branch, its own scratch state)
so parallel work can never clobber another thread's files or shared caches. One
coordinating session (the "cockpit") owns cross-cutting narrative artifacts (the
living plan, the friction inbox) and the terminal merge decision; individual
lanes never touch those shared files directly.

**Failure it prevents.** Two lanes writing to the same shared directory or the
same narrative file at the same time silently corrupt each other's output, or
collide at merge time in a way that's hard to disentangle. Worse, a lane that
edits the shared plan/inbox pollutes an otherwise-focused code review with
unrelated narrative changes, and two lanes' edits to the same narrative file are
a guaranteed merge conflict on files that were never the point of either PR.

**Mechanism.** A worktree-per-lane convention plus a sandboxed state directory
whose resolution precedence is explicit and overridable (an environment variable
for shells that persist, a fallback marker file for tool invocations that don't
share a shell). Before launching a batch of parallel lanes, map each candidate's
file footprint and only run truly disjoint work concurrently — the isolation
mechanism prevents *state* collisions, not *source-file* merge conflicts, so
footprint-mapping is a separate, deliberate step. Each lane's task prompt
explicitly forbids editing the shared narrative files and instead carries its
handoff (what shipped, what was learned, what's deferred) in its own pull
request's description — the one channel that's reviewed and visible across every
lane. The cockpit reconciles every launched lane to a terminal state (merged,
parked-with-reason, or still open) before writing anything to the shared plan —
an aggregate "everything's done" claim is not evidence a specific lane actually
shipped.

## 4. Risk-based PR splitting + merge classes

**Statement.** Decide how to bundle changes into pull requests by **risk**, not by
size or by feature boundary. Low-risk, easily-reversible, cosmetic changes can
stack together into one PR; anything touching shared state, external side
effects, security, or destructive operations gets its own tightly-scoped PR.
Identify the authorized actor at planning time. In a lane, the cockpit
coordinates the merge decision. The lane itself hands back a PR or explains why
it stopped.

**Failure it prevents.** Bundling a risky change alongside a pile of safe cosmetic
ones dilutes review attention (a reviewer skimming twenty small diffs is less
likely to catch the one dangerous one) and makes rollback harder if something
goes wrong. Conversely, splitting every trivial change into its own PR multiplies
review overhead for work that carries no real risk. Deciding merge authority
*after* the fact — mid-review, under time pressure — is how a risky change
quietly gets self-merged by an agent that was never supposed to have that
authority.

**Mechanism.** A stated policy: stack N logically-related low-risk changes into
one PR (one commit per change, so review-by-commit stays tractable); isolate
anything touching shared/production state, security, or irreversible operations
into its own PR. When planning a batch of work (especially parallel/autonomous
lanes), tag each item's merge class up front — "self-mergeable once green" versus
"requires operator sign-off" — as a required field in the plan. Check the final diff and
project policy before acting on that assignment. For work in the kit repository,
read the operator's [lane merge decision](docs/kit-handoff.md#whole-kit-plan).

## 5. PR follow-through to green-and-clean

**Statement.** Opening or pushing to a pull request is not the end of the task —
watching it through to a fully green, fully addressed state is part of the same
unit of work, not a separate favor to be asked for later. Every PR gets at least
one independent review pass before merge; a review tool being unavailable is not
a waiver on that requirement, it's a trigger to substitute a different
independent pass.

**Failure it prevents.** A PR opened and abandoned mid-CI, or left with unread
review comments, creates invisible unfinished work — nobody's watching it, so a
failing check or an unaddressed finding sits silently until someone happens to
look. "The review bot was down" quietly becoming "so we merged without review"
is exactly how a real defect slips through — a blocked reviewer is not evidence
the code is fine.

**Mechanism.** A standing loop, run by whoever opened or last pushed to the PR:
poll CI status and new review comments on a bounded cadence; fix real findings
and push; reply-with-reason to findings you disagree with; stop only once checks
are green and every finding has been fixed or explicitly addressed, or when a
genuine blocker needs a decision only a human can make. If the primary review
tool is unavailable, run a substitute independent review pass rather than
treating its absence as permission to skip review entirely.

## 6. Safety-critical doctrine

**Statement.** For any decision logic that gates a customer-facing send, an
irreversible or destructive operation, or a recovery/kill path: prefer a
deterministic gate (an explicit stamp, flag, or state field, checked at the
moment of action) over a natural-language or keyword-based matcher; require more
than one independently-reasoning review pass looking for different failure
classes before merging; re-review after every fix round rather than trusting a
single pass; and back kill/recovery-path changes with an integration test that
exercises the real failure path, not just a unit test of the handler in
isolation.

**Failure it prevents.** A matcher over free-text approval/cancellation language
is inherently leaky — there is always another phrasing that slips past it, and
each round of "tightening the matcher" just finds a new gap rather than closing
the class of bug. A single review pass, however thorough, has a blind spot; two
independently-reasoning passes (one adversarial/bypass-focused, one
correctness-focused) routinely find *disjoint* problems the other missed
entirely. A fix for one round's finding routinely introduces a fresh regression,
so "the last round found nothing" is not the same as "this is now safe." And
unit-testing a kill/recovery handler in isolation can pass green while the real
signal/timeout/retry path — the thing that actually matters in production —
remains broken.

**Mechanism.** Treat any change to a send-gate, destructive-operation guard, or
kill/recovery path as its own review-doctrine category: require a deterministic
artifact rather than a matcher wherever the decision has real consequences;
require two-plus review lenses (varying in what each is trying to break) before
merge; loop re-review until a full pass finds nothing new; and require an
integration-level test of the actual failure path before calling it done.
Changes in this category are never self-merged by an autonomous process,
however green the checks — they route to an explicit human sign-off.

## 7. Model/effort tiering by step difficulty

**Statement.** Match the computational/reasoning "tier" you spend to the
difficulty of the specific step, not to the session as a whole. Purely
mechanical, well-specified work (renames, sweeps, applying a known fix) gets the
cheapest capable tier. Self-contained work with a clear spec — even work that
must verify itself against a live system — gets the default, mid-cost tier. The
most expensive, highest-reasoning tier is reserved for the genuinely hard calls:
ambiguous scoping, security-sensitive judgment, calibration decisions, anything
where being wrong is expensive and hard to catch in review.

**Failure it prevents.** Running every step at the top tier burns budget (and, on
usage-metered plans, scarce quota) on work that didn't need it. Running
everything at the cheapest tier under-resources the few steps where reasoning
depth actually changes the outcome, producing worse decisions exactly where it
matters most. Tiering by *session* instead of by *step* gets this wrong in both
directions within the same piece of work.

**Mechanism.** A three-tier default (cheap-mechanical / default-standard /
expensive-judgment) with a short decision rule: does this step need cross-system
reasoning, an ambiguous judgment call, or a hard-to-reverse decision? If not, it
doesn't need the top tier. Default to the middle tier when unsure — a
regression-free baseline — and round up rather than down when a step's risk is
ambiguous. When work is delegated to a sub-agent or parallel lane, the tier
travels with the task as an explicit field, not an assumption the delegate has
to infer.

## 8. Mechanism over memory

**Statement.** Any rule that a fresh agent or a spawned sub-process "should have
known" does not actually bind unless it lives in something that agent is
guaranteed to read: the launch prompt itself, a pre-commit/pre-push hook, or a CI
check. A rule that lives only in a memory file, a prior conversation, or a
paragraph of prose in a document nobody re-reads is not a rule — it's a wish.

**Failure it prevents.** A freshly spawned agent (a new session, a sub-agent, a
background task) has no access to a previous session's memory or a document it
wasn't explicitly told to read. A recurring failure mode — an agent idling on a
"someone else is watching this" assumption, or skipping a safety check it was
never actually shown — repeats indefinitely if the fix is "we wrote it down
somewhere" rather than "the launcher injects it into every relevant prompt" or
"a hook refuses the action outright."

**Mechanism.** When a session-end retrospective identifies "the agent should have
known X," the fix is never "add a note reminding people of X" — it's one of:
inject X verbatim into the launch prompt/preamble every relevant process
receives; encode X as a pre-commit/pre-push/CI check that mechanically blocks
the violating action; or build X into the tool itself so the violating action is
simply not available. Prose and memory are for *humans* orienting themselves;
mechanisms are for binding automated or semi-automated agents.

## 9. Deterministic scaffolding around LLM-driven steps

**Statement.** When a process that includes an LLM-reasoning step needs to run
longer, handle more volume, or survive interruption than a single LLM call
comfortably allows, add deterministic (non-LLM) scaffolding around it rather than
just writing more instructions into the prompt: a script that pre-fetches and
slims the data the model will reason over, a heartbeat that records progress at
each step boundary, an idempotent way to resume after a partial failure, and a
hard cap on how much input any single reasoning pass is asked to process.

**Failure it prevents.** An LLM asked to reason over an unbounded or
ever-growing input (a full week's worth of activity, an entire raw data dump)
eventually times out or produces degraded reasoning as the input grows — and the
natural fix, "just tell it to be more careful/efficient in the prompt," doesn't
scale, because the underlying problem is architectural (too much ungrounded
context per call), not a prompting problem. A long-running process with no
progress markers gives no visibility into where it died when it does fail, and
one with no resume mechanism repeats a full, expensive run from scratch on every
retry.

**Mechanism.** Separate deterministic pre/post-processing (fetching, filtering,
slimming, batching, checkpointing) from the LLM reasoning step itself, as
distinct, testable, non-LLM code. Cap the input any single reasoning pass
receives, with a documented batching/map-reduce fallback for when the natural
input exceeds that cap. Emit a heartbeat or progress marker at each meaningful
step boundary so a failure is diagnosable from *where* it stopped rather than
just *that* it stopped. Make expensive intermediate results durable and reusable
so a partial failure costs a resume, not a full re-run.

## 10. No hardcoding

**Statement.** Every value that is specific to a particular environment or
deployment — the tracker's project identifier, a chat channel or notification
target, a URL or API endpoint, a file path that varies by machine, a threshold
or budget — lives in a config file the tooling reads, never hardcoded inline in
a script, a prompt, or a rule document.

**Failure it prevents.** Hardcoded environment-specific values are exactly what
makes a piece of tooling non-portable: copying a script or skill to a second
project (or even a second environment of the same project — staging vs.
production) requires hunting down and editing every place the old value was
baked in, and it's easy to miss one. It also means the same piece of logic can't
be tested or dry-run against a different target without editing the source.

**Mechanism.** A convention that every environment-specific value is a named key
in a config file (or an explicit environment-variable override for values that
must vary per-machine, like a local filesystem path), read at runtime — never a
literal string embedded in logic. When reviewing new tooling, treat a spotted
hardcoded environment value as something to flag and move to config, not
something to quietly let slide because "it works for now."
