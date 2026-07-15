# Safety-critical decision logic — review doctrine

These files gate customer-facing sends, destructive operations, or process
kill/recovery paths. Four rules apply to any behavioral change here — each one earned
by a real shipped failure that CI-green + full unit tests did not catch (an
approval-matcher inversion; a send-gate with holes found only in review; a destructive
operation whose "safety" fix reintroduced the hazard; a kill-path that passed unit
tests but was broken in integration). See Principle #6 in `PRINCIPLES.md` for the
full doctrine this rule operationalizes. Agent-specific adapters should bind this
shared doctrine through `.claude/rules/`, `AGENTS.md`, or a triggered repository
skill; do not fork the doctrine into runtime-specific copies.

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
   light.

1. **Adversarial review to convergence, not one pass.** Re-review after every fix
   round until a full pass finds nothing new. Fix rounds on gate logic routinely
   introduce their own regressions — treat "the last round found nothing" as
   provisional, not proof of safety.

1. **Kill/recovery paths need an integration test.** Unit tests on the handler are
   insufficient — a kill-path can pass unit tests while the wrapper-level behavior is
   broken. Exercise the real signal/timeout/retry path (or a faithful harness of it)
   before marking the change done.

Merge class: changes governed by this rule are **operator-merge** — never self-merge
them from an autonomous or lane session, even when green and clean.
