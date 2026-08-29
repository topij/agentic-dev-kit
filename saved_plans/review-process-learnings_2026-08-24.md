# Review-process learnings — 2026-08-24

Status: evidence record from the Codex–Claude parity work in PR `#595`, PR `#596`, PR
`#599`, PR `#609`, PR `#611`, PR `#614`, and PR `#620`. This is not shared gate
doctrine. Promote a lesson to `docs/agentic-dev-kit/` only after a later change defines
and tests the reusable contract.

## What paid off

Fresh adversarial and correctness contexts found concrete failure modes in portability,
artifact isolation, state-sandbox resolution, caller-checkout safety, trusted review
identity, resumability, approval routing, and installer YAML handling. Accepted
findings included executable probes or mutations that demonstrated an incorrect or
unsafe outcome.

The strongest fixes replaced ambiguous prose with structures that a test can parse:

- a capability table distinguishing required, optional, and conditional integrations;
- an authoritative safety declaration with explicit fail-closed outcomes;
- a canonical fingerprint encoding for cross-runtime resumability;
- installer fixtures covering the supported configuration shape and rejected shapes.

## Diminishing-return signal

The review moved from defects in the extracted workflow's core semantics to edge cases
introduced by the preceding mitigation. That shift is useful while a finding still
demonstrates corruption, an unauthorized write, evidence contamination, or a false
success. It is also the signal to stop broad exploration after the current exact head
receives clean configured fresh-context lenses.

A hypothetical wording conflict is not by itself a reason to edit. Require the reviewer
to show the operative outcome, identify the authority that resolves conflicting text,
and classify the result as a regression, imprecision, or pre-existing limitation.

## Review stopping rule

For work using the fallback panel:

1. Run the repository's required verification on the committed exact head.
2. Obtain the configured independent lenses against that same head and current base.
3. Fix a finding only when it demonstrates a concrete correctness, safety, contract, or
   adopter-upgrade failure in scope.
4. Re-review a behavioral fix. Dispose speculative, stylistic, duplicate, or
   already-authoritatively-resolved observations with a written reason.
5. When the exact-head lenses have no undisposed concrete finding and the deterministic
   gate has settled, record only the evidence that ran and merge. Do not launch a new
   exploratory panel merely to seek a different mutation.

## Design guidance for future review surfaces

- Define structured policy and precedence before writing explanatory prose.
- Before the first panel for a structured workflow contract, build a semantic matrix
  from the declarations. For each capability, record applicability, trigger point,
  unavailable result, authority, durable evidence, resume route, and overall outcome.
  Make terminal outcomes total and mutually exclusive before turning the matrix into
  prose. Test the outcome cross-product too: an optional degradation followed by a
  required downstream failure, and an authorized external write that fails or returns
  ambiguously, must each resolve to one declared terminal outcome.
- Build hostile mutations from that matrix, including a required capability becoming
  optional, an unavailable result becoming success, a fixed live source being skipped,
  a conditional being claimed ready before its trigger, an interrupted integration with
  no resumable outcome, duplicate or wrong-width declaration rows, and a thin adapter
  changing `follow` to `ignore` or appending a contradictory executable instruction. Run
  those mutations before asking a panel to rediscover them serially.
- Connect each required declaration to its later operational prose: mutate a pre-edit
  guard to run after the edit, replace a required gather with an exit-zero empty result,
  and remove the second-layer read behind any source whose classification promises more
  than list metadata exposes.
- Negate the complete normative-precedence sentence, not just one keyword, and mutate a
  declared source to promise evidence its recommended helper cannot actually return.
- Cross product external writes with an otherwise empty repository result: a verified
  tracker write is not a no-op, an ambiguous merge that read-back verifies is not
  incomplete, and acknowledgement state is not proof that a review finding was resolved.
- Cross product each abstract external-write capability with the repository's existing
  safety wrappers: authority to merge does not authorize bypassing mandatory paired
  review/merge wrappers or their shared state sandbox, so test authority class × write
  mechanism × state root as well as the terminal outcome.
- Exercise parser and installer changes with valid alternate syntax, comments, missing
  values, partial configuration, and upgrade/idempotency paths before opening the PR.
- Ask each lens for a novel failure hypothesis tied to an observable outcome. A new
  phrasing of an already-resolved policy conflict is not a novel hypothesis.
- Keep core extraction review separate from integration hardening when their risk
  surfaces do not need the same atomic parity argument.
- Treat review-cycle cost as evidence too: when accepted findings cluster around the
  mitigation rather than the goal, improve the test/declaration shape instead of adding
  more prose guards.

## Lifecycle-design additions from PR `#599`

- Build an external-action matrix before implementation: action × crash cutpoint ×
  durable evidence × authoritative observer.
- Self-consistent digests and schemas are not authority; compare them with independently
  observed source or external state.
- Pre-action intent must not contain identifiers produced by the pending action.
- Chain every action's consumed identifiers to the preceding verified read-back.
- Derive semantic-test paths and other declaration-owned values from configuration
  instead of plausible hardcoded fixtures.
- Ensure duplicated persisted evidence structures are independent objects and prove the
  boundary using one-sided mutation.
- Use one batch-level report binding for an ordered proposal set rather than
  independently invented candidate bindings.
- Review the complete lifecycle and external-side-effect matrix early instead of
  discovering one missing transition per review round.
- Treat late repeated review cycles as evidence that the design artifact was incomplete;
  pause for a fresh-session handoff when another substantive lifecycle gap appears after
  the agreed decision review.

## Faster fix-round execution

- Freeze the lifecycle matrix before expanding prose, then give every action row an
  executable positive cutpoint and an authority oracle. A reviewer can challenge the
  table directly instead of inferring the design from scattered paragraphs.
- Require an accepted finding to add both a positive construction and a locally
  recomputed hostile mutation. The pair turns a review discovery into a standing
  boundary and prevents the next panel from rediscovering its adjacent transition.
- End the design pass with a contradiction sweep across normative tables, recovery
  prose, terminal precedence, and the semantic oracle. Treat disagreement between those
  surfaces as a design defect before launching another panel.
- Keep the reviewed tree fixed during infrastructure recovery. Bind fallback evidence
  to the exact content, refresh only the exact-head delta after a content-free forge
  recovery commit, and never turn an unavailable required check into synthetic success.
- Run the configured reviewer after the local semantic and mutation matrices, and reserve
  the authoritative full suite for the exact candidate head. Any later content change
  invalidates that candidate and starts the exact-head verification boundary again.

## Launcher additions from PR `#609`

`gh pr view 609 --json comments --jq '[.comments[].body | scan("### Review round:")] |
length'` at `5843440c88342bd1abf75feb9831b37dec1aca01` on 2026-08-27 printed `5`.
The enumerated panel-disposition comment is the baseline for comparing later launcher
slices; the count is not reconstructed from memory or from fix commits.

- Treat every inherited `GIT_*` key and executable lookup through caller `PATH` as
  repository authority. Replacement means constructing the child's allowed environment,
  not deleting a familiar subset from the caller's environment.
- Close descriptors that are independently enumerated as live. A range derived from a
  mutable soft limit can leave a hostile descriptor open above that limit; inability to
  enumerate the descriptor table is a fail-closed launch outcome.
- Process-group ownership is insufficient when a child can detach. Bind a private launch
  nonce into the child environment and audit nonce-bearing lineage across session changes.
- A start fingerprint sampled earlier does not make a later signal safe. Immediately
  before every signal, re-observe the nonce-bearing process and fingerprint so PID reuse
  becomes a no-signal outcome.
- Keep the local descriptor seal's trust boundary explicit: it detects corruption and
  descriptor-only rewriting, but it is not a privilege boundary against compromise of the
  same operating-system account.
- Test newest-first changelog selection and adopter migration text from the same contract
  that registers a new kit-owned safety-critical engine.
- Preserve the accepted-finding rule: add both a positive construction and a locally
  recomputed hostile mutation. A copied hostile evidence object can share aliases with the
  positive object and silently stop proving an independent boundary.

## Per-runtime launcher additions from PR `#611`

`gh pr view 611 --json comments --jq '[.comments[].body | scan("## Fallback panel — round")] |
length'` at `e0ef08157fa091b3d022bec2787603dd4298547f` on 2026-08-27 printed `3`; the
`#609` baseline command re-read the same day printed `5`. Each reading uses its own
PR's disposition heading, so compare them as the number of dispositions posted,
not as fix rounds; neither is reconstructed from memory.

- The design matrix preceded the code, and no round found a defect in engine behaviour.
  What the rounds found instead was an overstated sentence of executed prose, the
  coverage gaps a mutant exposed (`is_error` absent, the hardlink clause), and a
  test-name imprecision — the shape the
  stopping rule predicts when the mitigation is designed before the panel rather than
  inside it.
- A test-only fix round can take the dual-lens delta pass with the author's draws
  stated (`--delta-draws`): the delta is test code, the branch is under the doctrine
  by path, the mutants were recomputed. Both lenses rebuilt the mutants independently
  and confirmed the draws; the pass cost one round and no engine change.
- "Logged, not fixed" for a record-prose imprecision works as written when the tracker
  artifact is asked for in the same breath as the disposition: the occurrence landed on
  the issue owning the class, the PR reply pointed at it, and the receipt stood.
- A live record produced by the runtime under test surfaces facts a fake cannot: the
  untrusted-workspace behaviour that decides the next slice came from Claude's own
  stderr, not from the wrapper's tests. Produce each runtime's record from that runtime.
- A lens interrupted by the host sleeping reports nothing and must be re-run from
  scratch; its worktree survives untouched, so the cost is the round, not the evidence.

## Writing-lane policy additions from PR `#614`

`gh pr view 614 --json comments --jq '[.comments[].body | scan("## Fallback panel — round")] |
length'` at `d2e1090865769685a46307d7e6a99b15b6f49eb5` on 2026-08-27 printed `15`. Same
heading as `#611`'s reading, so the two compare as dispositions posted; neither is
reconstructed from memory.

- **A claim about what the runtime does is verified live before it is written, or it
  is not written.** The rounds' Critical and HIGH findings were sentences asserted by
  inspection — a `-v` flag called read-only, an allow list called the whole boundary —
  and a Low had the same shape (`cat` attributed to one policy's class); each was
  refuted by one probe against the pinned client. The record now states what the runtime accepts on its own beside what the
  profile grants, because the runtime's own classifier is part of the boundary.
- **Least privilege answered every widening finding; a blocklist answered none.** A
  remote grant narrowed to `get-url`, an edit grant narrowed to `Edit(**)`, a
  permissions object closed to its three rule lists. The one enumeration the panel found
  (`Bash(**)` missed by a spelling list) was replaced by a structural rule, and the
  closed set is the same move one level up.
- **"A fix round addresses only what the review found" held across the rounds.** No
  mechanism was added; the ones a finding prompted — a lane-side push gate, inline
  validated profile bytes, a post-exit origin re-read — were kept out of the fix and
  filed as their own items (`#615`, `#617`, `#618`).
  The doctrine's warning that a MED-prompted mechanism becomes the next HIGH was the
  reason, and the rounds stayed one finding wide.
- **A live probe from the cockpit reproduces a lens's finding before the fix is
  written.** Each accepted runtime-behaviour finding was reproduced with the same
  client before the disposition named it fixed, and the reproduction is what the record
  cites — a lens report is testimony, the cockpit's probe is the observation.
- **An interrupted host pauses the round, not the evidence.** With the operator away,
  the panel was not launched: a lens killed by sleep reports nothing, and a fix commit
  that lands while nobody can authorize the next round only moves the head. The pause
  cost nothing the worktrees did not keep.

## Codex writing-lane record additions from PR `#620`

`gh pr view 620 --json comments --jq '[.comments[].body | scan("## Fallback panel — round")] |
length'` at `37ad8eab0286c45aaf1ab1098e42e1da04561549` on 2026-08-27 printed `2`.

- **A digest is not durable evidence when the named bytes are deliberately removed.**
  The first adversarial panel found that fixture cleanup would delete the receipts,
  rollouts, and raw captures while the record retained their hashes. The fix retracted
  the capability promotion; it did not add an evidence-retention mechanism inside a
  record-only slice.
- **Runtime narration and wrapper evidence are different authorities.** Codex reported
  denied operations in final prose and returned success, while the bound
  `last-message-file` receipt carried `terminal.permission_denials: null`. The record
  treats that mismatch as the matrix result instead of reconstructing a denial object
  from prose.
- **Live config reach is part of the boundary.** The controlled user marker and values
  reached both untrusted lanes; the conflicting project marker and values did not. A
  launcher argv that selects `--sandbox` does not by itself isolate native user config.
- **Cleanup is a reviewed completion condition.** The correctness panel found that the
  fixture, including its auth symlink, still existed. The fix removed the exact fixture
  and verified its absence before the record could describe cleanup as complete.
- **The record-prose carve-out preserved the reviewed head.** The terminal correctness
  lens found a Low design-versus-record imprecision, not a regression. It was logged as
  an occurrence on `#120`, and no corrective commit invalidated the exact-head receipt.

## Capability-tier calibration additions from PR `#623`

`gh pr view 623 --json comments --jq '[.comments[].body | scan("## Fallback panel — round")] |
length'` at `92a3c15d13be50ae0a02ba0c40ac78e80a1e56e0` on 2026-08-27 printed `4`.

- **A blanket capability claim is refuted one surface at a time, and the true half
  stays.** "The delegation tool takes NO per-agent effort parameter" was true of the
  tool's parameters and false of the runtime: the agent definition's frontmatter is
  applied, and so is `--agents` JSON under the trust route. The retirement kept the
  sentence that survived (the tool has no effort parameter; a plain subagent inherits)
  beside the surface where the claim was wrong, and the test that had pinned the
  blanket claim now pins the per-surface declaration.
- **The runtime's own artifact is the observer, never the argv or the child's prose.**
  Claude's session and subagent transcripts carry `model` and `effort`; Codex's rollout
  carries `turn_context`. Each was validated against a known input before it was
  trusted, and each caught a false success the exit code did not: `--effort bogus`
  warned and ran at exit 0; a misspelled `-c model_reasoning_effrot` ran at the config
  default at exit 0; an invalid frontmatter effort ran at the parent's level with a
  debug-only log. The generator validates the level because the runtime does not
  where anyone looks.
- **Mechanical, advisory, and unavailable are per key, per runtime, per surface** —
  the same key was mechanical on one surface (frontmatter) and advisory on another
  (the tool call) of the same runtime. A declaration that names the surface is the one
  that survives the next probe.
- **A claim verified in the same session was still overturned by the session.** "The
  roster is fixed at session start" came from one probe in the turn that wrote the
  file; the shipped definitions then appeared in the roster some turns later. The
  correction landed in the fix round on every surface the claim had reached, and the
  record now says what was observed and what was not pinned (the refresh timing).
- **The panel's HIGH was in the new code's own guarantee, found by the lens executing
  the generator against a realistic input** (a Bedrock-shaped model id with `:`) — the
  fix was the escaping the sibling field already had, plus a live probe that the
  runtime applies a quoted value before the fix was written.
- **A verification stamp needs a quiet tree.** Two `make test` runs at the first
  candidate were invalidated by the cockpit itself — a concurrent `pr_watch.py` poll
  tripped the `#428` state guard, and uncommitted correction edits tripped the drift
  check. The stamp that counts was taken at the fix-round head with nothing else
  writing.
- **Rounds 2 through 4 ran under the mechanism the PR adds.** Once this session's
  roster listed the kit-owned `adversarial` and `correctness` agents, the lenses were
  launched as them, and the cockpit's subagent transcripts read `('claude-sonnet-5',
  'high')` for every lens in those rounds against `('claude-sonnet-5', 'xhigh')` for
  round 1's plain subagents — the frontmatter carried the compute, the prompt only
  restated it. The reading went into the live record, which the round-3 adversarial
  lens then correctly marked as something a lens cannot verify from its seat.
- **What each round found, and what it says about where defects live.** Round 1's
  HIGH and round 3's Medium were both in *new* code's own guarantee (an unquoted
  frontmatter value; a `sed` replacement with an unescaped path), each found by a lens
  executing the new path against an input the author's tests had not tried. Round 2's
  findings were the author's *rationale* for a correct fix being wrong (YAML breaks on
  colon-space, not on a colon), and an enumeration that went short again as the PR's
  own tests joined it — the same imprecision class the earlier round had flagged. The
  remedy that held for the enumeration was to name kinds, not files.
- **A mutant claimed killed before its recomputation ran is a claim, and it was
  caught.** The round-3 disposition asserted both new guards' mutants killed; the
  script for the second had aborted on a heredoc-terminator slip before applying the
  mutation. The recomputation was run and stamped on the PR before the next round, and
  the disposition's comment says which reading backs it.
- **The `#574` shape recurred lens by lens under the same contract text:** across the
  four rounds, some lenses fetched in the handed tree and disclosed it while others
  used `ls-remote`. The occurrences went to that issue; no wording change was made in
  the PR.

## First real headless lane additions from PR `#626`

- **A failed run is a result, and the design has to say so before the run.** The design
  matrix fixed a *total* terminal-outcome table in advance — including `failed` with a
  non-empty denial list, and the instruction attached to it: read the denials, decide
  whether the profile is too narrow or the prompt out of scope, and **do not widen the
  profile to make the run pass**. The run landed on exactly that row. Having written the
  instruction before there was an outcome is what made "the lane failed" a finding
  rather than a setback to be engineered around, and the profile was not widened by
  either the lane or the cockpit.
- **The lane's own diagnosis was right and was still not evidence.** Its final text said
  "every write under `.claude/` is refused", which the receipt's denial list corroborated
  entry for entry. The claim only became evidence when the cockpit reproduced it in an
  unrelated repository under the same trust route, and when the lane's *successful*
  `.agents/` and `scripts/tests/` edits ruled out the glob reading. Testimony that turns
  out to be true is still testimony; what changed its status was a second observer.
- **The first probe confirmed the claim and hid its scope.** Both the lane's denials and
  that probe targeted `.claude/commands/`, and the record generalised to `.claude/` as a
  directory and then reasoned about `rules/` and `agents/`. A delta-pass correctness lens
  caught the extrapolation. The remedy that held was to **measure rather than hedge**: a
  second probe covering each `.claude/` subdirectory plus controls outside it, which both
  established the wider claim and killed a competing explanation nobody had excluded —
  `.github/workflows/` was written in the session that was refused five `.claude/` paths,
  so it is not a dot-directory effect. Narrowing the sentence would have left that
  alternative standing.
- **A stale-state sentence survives a fix that repairs its siblings.** A correctness lens
  found the record asserting "not pushed, and no pull request" as present-tense fact,
  false by the time the commit carrying it landed — it established this from commit
  timestamps against live forge state, not by re-reading prose. The fix repaired two
  sentences; a delta-pass adversarial lens then found a **third** instance in a file the
  fix commit never touched, and disputed the author's draw that the fix "fully
  discharges" the finding. The lesson is that this defect class is per-sentence, so the
  fix has to be a sweep across every file the claim reached, not an edit at the place it
  was reported.
- **Stating draws for the delta pass is what produced that dispute.** The disputed draw
  was the author's own claim of completeness. A delta pass with no draws to argue against
  would have had to rediscover the defect on its own; naming the claim gave the lens
  something falsifiable, and it falsified it.
- **Both PRs' guards were verified by execution against the real regression, not the
  synthetic catalogue.** Two independent lenses reverted the adapters to their pre-PR
  bodies — the actual `#602` defect — and confirmed the new pin fails on it. One went
  further and recovered the lane's specified body out of the final-message object by its
  recorded digest, then byte-diffed it against the committed file, which is what makes
  "the pin decided the file" a checked claim rather than an author's assurance.
- **The quiet-tree rule held again, and cost a rerun each time.** Every `make test` stamp
  in this slice was taken with no concurrent `pr_watch` poll and nothing uncommitted, and
  each fix round meant another full run rather than reusing an earlier one. Panel prompts
  were rendered only outside those runs, after the 2026-08-27 entry recording
  `panel_prompt.py` hanging under exactly that contention.
- **A persisted `cd` produced a false finding in a read sequence.** An evidence-copying
  command's `cd` survived into the next call, and a hook-existence check then reported
  this repository as shipping no pre-push hook — contradicting `AGENTS.md`. It was caught
  and discarded before reaching the record, and filed as an occurrence on `#511`. The
  tell was a second error in the same output (`init.sh: No such file or directory`) that
  was unmistakably wrong; the first result on its own looked like a finding.

## Lane-permission-policy additions from PR `#632`

Two rounds, both lenses each round. Round 1 produced one HIGH that was declined on a
measurement and one LOW that was right and became a real fix; the delta pass disputed
two of four draws, and both disputes were right. The learnings below are about *probe
design* — this slice's findings were reached by running the real client rather than by
reading a diff, and most of what went wrong went wrong in what a probe was taken to
establish.

### An accept-form probe cannot establish a permission boundary. Only the denied case can.

Round 1's adversarial lens reported that a granted prefix widens to arbitrary shell,
having run `make test; echo …` and seen it succeed. The run was real and the conclusion
did not follow: `echo` is accepted here on its own, so **both** segments were
independently allowed and the result is identical under the two competing explanations —
"the prefix carried the rest" and "both parts were fine anyway".

The case that separates them is a compound whose second segment is **denied** standalone.
It was run, and refused. So the boundary held and the finding did not.

The general form: **an observation that everything ran tells you nothing about which
rule allowed it.** To attribute an outcome to a specific grant, the probe needs a
component that the grant is the *only* possible source of permission for. A control that
succeeds is not a control.

This cost nothing to check and would have cost a HIGH's worth of doctrine had it been
accepted — and equally, hedging it ("chaining may widen the grant") would have shipped
the false explanation standing beside the true one, unfalsifiable and permanent.

### A correction can under-correct, and the fix round's wording needs its own falsification

Round 1 correctly killed "the grant is bounded to the one target" and replaced it with
"admits a command whose **text** begins with `make test`". That was better and still
wrong in a way nobody had tested: it invites a *substring* reading. The delta-pass lens
tested exactly that — `make test-exfil`, `make testing-foo`,
`make test-and-curl-example-com` are all refused — establishing the match is on **argv
tokens**, not raw text.

So a fix round's replacement wording is a new claim, and it inherits none of the
original's scrutiny. It is the least-reviewed sentence in the PR at the moment it is
written, and it is written under the pressure of having just been wrong. Two rounds
found two successive versions of the same sentence overstating, in different directions.

### A probe's self-report is not evidence of the probe's effect

`result-B.json` and `result-C.json` carry the probe's own narration — "step 2 ran",
"the file was written". A delta-pass lens pointed out that this cannot distinguish a
real worktree escape from a probe *reporting* one, under the claim the whole slice leans
on.

The fix is cheap and should be the default: **capture the effect from outside the
probe.** The escaped files were still on the host filesystem, so they were listed with
their mtimes, digested and printed into `escape-readback.txt`, beside the worktree path
they are outside of. An effect that leaves an artifact should always be read back by the
party that did not produce it.

The same lens checked something worth stealing: that every `result-*.json` in the bundle
carries a **distinct session id**. That is the check which catches an evidence bundle
assembled by copy-paste, and no amount of reading the prose finds it.

### When lenses split, the split is the finding — route it to doctrine, do not pick a side

On the safety-critical scoping draw, adversarial disputed and correctness confirmed, both
correctly reasoning from the same text: `AGENTS.md` names three engines, and the changed
file is data those engines load. Neither lens was wrong; the rule was ambiguous.

The temptation is to adopt the stricter lens's reading in the PR — here, to add the
profile to the named list. That is a doctrine change nobody asked for, arriving in a
commit about permissions, which is precisely
`safety-critical-changes.md` rule 3's trap. It was filed instead (`#633`), with the
document telling the next author to take the conservative reading until it is settled.
**A disagreement between lenses is evidence about the rule, not about the change.**

### Sweep sibling claims when a lens rejects an inference

The most useful thing this slice did happened before any review. The previous session's
record contained, one bullet apart, a claim a lens had forced to be *measured* and a
second claim of the identical shape — inferred from the same allow list — that nobody
re-examined. The second was re-measured here as the first act of the slice.

So: **when a review forces one claim from inference to measurement, the sibling claims
resting on that same inference do not inherit the fix.** They are the likeliest place
for the next defect, they are cheap to find (they sit near the corrected one), and they
carry the corrected claim's credibility without having earned it. Worth a deliberate
pass at the time of the original correction, not one session later.

## Runtime-adapter upgrade additions from PR `#635`

- **A generated-artifact classifier needs fixtures independent of the renderer under
  test.** The initial legacy fixtures called the historical renderer, and that renderer
  still consumed current descriptions. At `dfd1976412ec530a1a7a6ec81f8028e7f4572a7a`
  on 2026-08-28, a correctness mutation changed the historical text while
  `UV_CACHE_DIR=/private/tmp/mut-correctness-dfd1976-F9FLJz/uv-cache
  UV_TOOL_DIR=/private/tmp/mut-correctness-dfd1976-F9FLJz/uv-tools uv run --with pytest
  --with pyyaml python -m pytest scripts/tests/test_kit_doctor.py -q -m 'not driftcheck'`
  printed `421 passed, 1 deselected`. The fix freezes historical metadata and compares
  it with independently checked-in digests of the prior rendered bytes.

- **Read-only is an identity claim, not a byte-equality claim.** A test that snapshots
  content misses unlink-and-recreate, symlink-target writes, and hardlink write-through.
  The accepted fix added assertions for link identity, inode relationships, targets and
  sentinels. The adversarial and correctness `make test` runs at
  `3032a2f47c2be34e49ea4148c0c5635ca99a83fd` on 2026-08-29 printed `2034 passed, 3
  warnings in 387.86s` and `2034 passed, 3 warnings in 385.43s`, respectively.

- **Test the gate at the process boundary where the workflow relies on it.** Helper-only
  tests left mutations alive in `main()` branches for unconditional skip, swallowed
  source-validation failure, missing declared tests and omitted state-path roots. The
  accepted fixes invoke the entry points and pin the returned status and pytest call,
  because a correct selector below a fail-open wrapper does not protect upgrade.

- **The applied-compute observer is part of review evidence.** The Codex carrier argv
  requested `high`, but only rollout `turn_context` established what ran. At
  `3032a2f47c2be34e49ea4148c0c5635ca99a83fd` on 2026-08-29, the following command read
  back `model=gpt-5.6-sol` and `effort=high` for the persistent adversarial and
  correctness audits:

  ```sh
  jq -c 'select(.type == "turn_context") | {file: input_filename, model: .payload.model, effort: .payload.effort, configured_effort: .payload.collaboration_mode.settings.reasoning_effort, cwd: .payload.cwd}' /Users/topi/.codex/sessions/2026/08/29/rollout-2026-08-29T01-11-19-01a04a6d-6a0f-73b0-bdef-70233fec1748.jsonl /Users/topi/.codex/sessions/2026/08/29/rollout-2026-08-29T01-11-28-01a04a6d-8d2d-7943-8173-848f222ded53.jsonl
  ```

  The final `--ephemeral` lens invocations intentionally retained no rollout to inspect.
  A review launcher that promises applied compute has to preserve that minimal observer
  or arrange an explicit readback before cleanup.

- **A scratch tree must satisfy the suite's repository assumptions.** The correctness
  delta lens initially used `git archive`, which cannot carry repository metadata. That
  attempt was kept as a non-verdict, and the lens restarted in a fresh no-hardlink clone.
  Scratch isolation and repository identity are separate properties; those properties
  must coexist when the suite checks its own checkout.

## Cockpit-settings-policy additions from PR `#637`

Seven dual-lens rounds plus one CodeRabbit review, on a change whose blast radius is a
single advisory report line. Rounds 3 and 4 were clean on both lenses and rounds 5, 6
and 7 each found something anyway, so this is also the clearest local instance of the
"termination condition may never arrive" warning in `fallback-review-panel.md`.

- **A local suite is evidence about the interpreter it ran on and nothing more.** At
  `254fdcf492d1be64fb9a2f086e73fb413a25100b` on 2026-08-29, `make test` passed in three
  independent checkouts — the cockpit's and both lenses' own clones — and CI failed on
  the one test written for the changed branch. `Path.resolve()` reports a symlink loop
  as `RuntimeError` on Python 3.12 and returns the path unresolved on 3.14.6; `make
  test` carries no `--python`, so `uv` selected 3.13 and later 3.14 within one session
  while `.github/workflows/test.yml` pins 3.12. **No number of additional lenses could
  have caught this**, which is the part worth keeping: the panel's redundancy is across
  reviewers, not across environments. Recorded on `#292`, whose thesis it extends.

- **A probe of your own module cannot establish what the runtime does.** An early
  cockpit probe printed `exact rule, no wildcard -> GRANTED` and was read as confirming
  Claude Code's permission semantics. It was reporting `kit_doctor`'s behaviour back.
  The real semantics, measured at Claude Code 2.1.251 under a deny rule of
  `Bash(git status)`, are that `git status` is refused and `git status --short` is not.
  Four panel rounds and a bot review passed over the resulting defect, because the
  output of a self-probe is shaped exactly like a finding about the client.

- **Ask what the guard is for, not whether its inputs appear.** The permission check
  asked whether any word in a rule resolved to the engine's path. That was wrong in
  both directions at once: `Bash(cat <engine>:*)`, `ruff check`, and `rm` all reported
  the engine granted, while `Bash(uv run:*)` — which pre-approves every poll — reported
  it ungranted. Rounds 5 and 6 each found one direction. The repair was not a further
  case but a different question: are the rule's tokens a prefix of the command the
  workflow issues. **Two consecutive rounds finding defects in one function is the
  signal that its predicate is wrong**, not that its cases are incomplete.

- **False mutation *survival* is the inverse hazard, and it reads as good news.** The
  documented trap is the false kill. Here a mutation reverting `init.sh`'s advisory to
  the narrower `SessionStart` matcher reported `7 passed` under `-k 'permission or
  matcher or session_start'` — a filter that never selected
  `test_the_claude_budget_advisory_does_not_tell_an_adopter_to_narrow_it`, the test that
  guards it. Re-run with `advisory` in the expression, it failed. **A `deselected` count
  does not detect this**: it confirms something was excluded, not that the guarding test
  was included.

- **A test that greps for a token is defeated by any other occurrence of it, including
  narration about the test.** `test_dead_registrations_docstring_accounts_for_every_
  state_it_omits` searches the docstring for each omitted state name. A self-referential
  paragraph added beside the real sentence — recording that the sentence had been
  missing for a round — contained the same word, so deleting the sentence still passed.
  Removing the narration, which "Keep the record small" already asks for, restored the
  kill.

- **A guard whose comment credits it with work another line does.** An explicit `$`
  check was added to reject a single-quoted `'$CLAUDE_PROJECT_DIR/…'` path, and its
  docstring said so. Mutation showed no test could distinguish the guard from its
  absence: switching the comparison to path equality had already subsumed it. Removed,
  and the comment corrected to name the comparison. The same class recurred one round
  later in the opposite direction — a docstring asserting a clause had "no demonstrated
  trigger" on the strength of one interpreter, which CI falsified within minutes.

- **A prompt assembled by a tool, retyped by hand, is a figure written from
  expectation.** `panel_prompt.py` renders a prompt to a file; a Claude Code launch
  needs the text inline. In one of five launches the diffstat was transcribed as
  `999 insertions / 18 deletions` against the rendered `1000 / 16`. The correctness lens
  caught the mismatch and correctly declined to attribute it to a stale base or wrong
  sha. Bounded — both lenses verify base and sha independently — but the diffstat check
  exists to flag a wrong diff, and a mistyped baseline blunts exactly that.

- **`bot-coverage` is a window in which recording a receipt is the error.** CodeRabbit's
  auto-review is disabled here, so the converged-head request is the review. It answered
  at `405c23b680f49b92a4500b64a3a61d4fa0865535` with `covers_head: true`, and
  `review_evidence.route` became `bot-coverage` — under which every `fallback:` literal
  would name a substitute pass that did not run. The next fix round moved the head,
  coverage went stale, the hourly budget was spent, and the panel receipt became the
  honest evidence again. Both transitions behaved as `pr-watch` documents; the failure
  available here is recording out of habit during the window.

- **The engine refused a premature receipt and was right.** `--record-review` was
  declined with `review bot coderabbit has not reported yet (pending 0.00m < 15m
  grace)`, because the review request had just put the bot into a pending state.
  Waiting rather than passing `--allow-pending-bot-review` — which is for evidence a
  verdict will never arrive — cost about three minutes and produced a real review.

- **A `cd` outlives its command in a one-off probe, not only in two-tree work.** Two
  occurrences this session: a symlink probe and a permission probe each left the shell
  in a scratch directory, and the next relative-path edit failed. `AGENTS.md` documents
  the hazard for verification clones and adopter checkouts; both instances here were
  throwaway probes, which is not where that rule tells you to expect it.
