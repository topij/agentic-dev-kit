## LOW review findings: a first occurrence is recorded on the pull request, not ticketed

CHANGED (gate semantics): under *LOW findings: delta review or ticket* in
`fallback-review-panel.md`, a deferred LOW finding's first occurrence takes a new
**record** route: its typed disposition line, or its thread reply for a bot or human
finding, says `recorded:` with the location and what a fix would change, and nothing
is filed in the tracker. A LOW is still ticketed when it recurs, when it is on a
safety-critical pull request, when its repair needs a redesign or its containment is
disputed, or when it is pre-existing. If you want every LOW ticketed as before, keep
your local copy of that section. If you take the record route, run
`post-merge-systemize backfill` at least every two weeks and ticket the recurring
clusters of recorded findings it reports.
