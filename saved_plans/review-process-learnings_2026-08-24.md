# Review-process learnings — 2026-08-24

Status: evidence record from the Codex–Claude parity work in PR `#595`, PR `#596`, PR
`#599`, and PR `#609`. This is not shared gate doctrine. Promote a lesson to
`docs/agentic-dev-kit/` only after a later change defines and tests the reusable
contract.

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
