## `pr_watch.py --json` reports `review_owed`; pr-watch.md keys the converged-head review request on it

ADDED (report shape): a top-level `review_owed` field in the `pr_watch.py` report, present on every poll. It is a sorted list of the configured review bots owed a review of the current head, `[]` when nobody is owed (every configured bot accounted for, or none configured), or `null` when the review-bot read did not succeed (`review_bots.signal` is `unavailable`). It is the same predicate the text render prints as `⚠ review owed` at convergence, and like that line it gates nothing.

CHANGED (workflow): pr-watch.md's *Converged* stop condition used to tell you to request a review whenever `review_bots.coverage` showed the head uncovered. It now keys on `review_owed`: request from each named bot at the converged head; request nothing on `[]`; on `null`, re-poll once, and if the next poll at the same head is still `null`, run the fallback review the PR owes and say the reviewer's state could not be read.

What to do: take the new `scripts/pr_watch.py` and `docs/agentic-dev-kit/workflows/pr-watch.md` together. If your own automation decides whether to request a review from `review_bots` fields, key it on `review_owed` instead. A consumer that rejects unknown keys must allow the new field.
