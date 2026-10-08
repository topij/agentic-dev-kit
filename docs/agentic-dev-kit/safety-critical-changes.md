# Safety-critical decision logic — review doctrine

These files gate customer-facing sends, destructive operations, or process
kill/recovery paths. Four rules apply to any behavioral change here — each one earned
by a real shipped failure that CI-green + full unit tests did not catch (an
approval-matcher inversion; a send-gate with holes found only in review; a destructive
operation whose "safety" fix reintroduced the hazard; a kill-path that passed unit
tests but was broken in integration). See Principle #6 in `PRINCIPLES.md` for the
principle this rule operationalizes. Agent-specific adapters should bind this
shared doctrine through `.claude/rules/`, `AGENTS.md`, or a triggered repository
skill; do not fork the doctrine into runtime-specific copies.

`review.safety_critical_paths` in `config/dev-model.yaml` declares which files
these are. A fallback review takes rule 2's two lenses on a pull request that
changes one of them or that config file, and one isolated lens otherwise: see
*How many lenses* in [`fallback-review-panel.md`](fallback-review-panel.md).

1. **Deterministic gate > NLP/keyword matcher.** A matcher over free-text (approval
   keywords, cancel phrases) is inherently leaky — repeated review rounds on a
   leaky matcher each tend to find a *new* wrong-send, not close the class of bug.
   When the decision matters, the durable design is a deterministic artifact (a
   stamp, a state field, an explicit flag) written at decision time and verified at
   act time. Treat "we tightened the matcher" as a stopgap, not a fix.

1. **Dual-lens review for customer-facing gates.** One review pass — however strong —
   is not enough: an adversarial/bypass-focused pass and a general-correctness pass
   routinely find **disjoint** holes. A send/publish gate needs BOTH lenses before
   merge. A single-lens "converged" verdict is an incomplete review, not a green
   light. When your review bot is unavailable, the substitute that satisfies this
   rule is the panel in [`fallback-review-panel.md`](fallback-review-panel.md) —
   a single fallback command run in the author's own context does not.

1. **Adversarial review to convergence, not one pass.** Re-review after each fix
   round using the full-panel or delta route in `fallback-review-panel.md`.
   **LOW/P3 findings never restart the whole process:** use a contained delta
   review with adversarial and correctness lenses, or file a ticket. This applies
   to LOW regressions too. It does not waive higher-severity findings, initial
   review coverage or operator merge authority. Fix rounds on gate logic routinely
   introduce their own regressions — treat "the last round found nothing" as
   provisional, not proof of safety. Be aware that "finds nothing new" may never
   arrive: see [`fallback-review-panel.md`](fallback-review-panel.md) for the
   observed base rate and for the stopping criterion to use instead — blast
   radius, not round count. A spent `review.round_budget` hands the next round
   to the operator ([`workflows/pr-watch.md`](workflows/pr-watch.md), *Round
   budget*); it never ends review on its own.

    **A fix round addresses only what the review found** — and what it found is the
    finding, not a licence to build. The minimum that resolves it is the fix; a new
    mechanism is an *addition* however squarely a finding prompted it, so it gets
    filed and proposed on its own. That distinction is the rule: across the five
    rounds behind this paragraph, three mechanisms were added that no reviewer asked
    for and **every one became a HIGH finding in a later round** — two of them built
    in direct response to a real MED, which is the trap. The fixes actually asked
    for held. Your mechanism ships in a commit whose message is about the findings,
    so the next round sees the two merged and cannot weight them differently. A MED
    or LOW is often best answered by **documenting the limitation**; the harm is
    trading a fail-*closed* limitation for a fail-*open* mechanism. State in the PR
    which changes were requested and which were not.

    **Before adding a skip or exemption, list every input that shares the shape it
    keys on**, and say for each one whether it should be skipped. A skip is keyed on
    something observable, and the observable is broader than the case it was written
    for. On `#986` a fix tolerated a registration whose directory was deleted but not
    one where only its `.git` was gone; the next fix tolerated the missing `.git`, and
    also skipped a bare configured repository — which has no `.git` either — and so
    dropped its object store. The sweep failed open, the adversarial lens reproduced
    it, and the following round reviewed the revert: each fix round created the next
    round's finding. Write the list where the reviewer reads it, so the review checks
    the enumeration rather than rediscovering it. Related: `#419`, `#666`, `#305`.

1. **Kill/recovery paths need an integration test.** Unit tests on the handler are
   insufficient — a kill-path can pass unit tests while the wrapper-level behavior is
   broken. Exercise the real signal/timeout/retry path (or a faithful harness of it)
   before marking the change done.

Merge class: changes governed by this rule are **operator-merge** — never self-merge
them from an autonomous or lane session, even when green and clean.
