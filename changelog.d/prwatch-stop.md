## pr-watch.md: the converged-head review request keys on `⚠ review owed`

CHANGED: the *Stop conditions* bullet used to tell you to request a review whenever `review_bots.coverage` showed the head uncovered, even during a trusted check-borne outage, where the engine deliberately prints `⚠ review unavailable` and no `⚠ review owed`. It now says to request a review when `⚠ review owed` is printed, and to take the fallback panel when only `⚠ review unavailable` is. No action is needed unless you copied the old bullet into your own workflow docs; the engine is unchanged.
