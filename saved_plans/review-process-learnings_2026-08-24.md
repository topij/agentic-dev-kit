# Review-process learnings — 2026-08-24

Status: evidence record from the Codex–Claude parity work in PR `#595`. This is not
shared gate doctrine. Promote a lesson to `docs/agentic-dev-kit/` only after a later
change defines and tests the reusable contract.

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
- Exercise parser and installer changes with valid alternate syntax, comments, missing
  values, partial configuration, and upgrade/idempotency paths before opening the PR.
- Ask each lens for a novel failure hypothesis tied to an observable outcome. A new
  phrasing of an already-resolved policy conflict is not a novel hypothesis.
- Keep core extraction review separate from integration hardening when their risk
  surfaces do not need the same atomic parity argument.
- Treat review-cycle cost as evidence too: when accepted findings cluster around the
  mitigation rather than the goal, improve the test/declaration shape instead of adding
  more prose guards.
