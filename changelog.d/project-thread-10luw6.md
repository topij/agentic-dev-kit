## LOW review findings: a first occurrence is recorded on the pull request, not ticketed

CHANGED (gate semantics): under *LOW findings: delta review or ticket* in
`fallback-review-panel.md`, a deferred LOW finding's first occurrence takes a new
**record** route: its typed disposition line, or its thread reply for a bot or human
finding, says `recorded:` with the location and what a fix would change, and nothing
is filed in the tracker. A LOW is still ticketed when it recurs, when its recurrence
check (open tickets and earlier `recorded` lines) did not complete, when it is on a
safety-critical pull request, when its repair needs a redesign or its containment is
disputed, or when it is pre-existing. If you want every LOW ticketed as before, keep
your local copy of that section. If you take the record route, search your
pull-request comments for earlier `recorded` lines before recording a LOW (record only
when both that search and the open-ticket search completed: on GitHub, every page
read, `incomplete_results` false on each and `total_count` at most 1000; otherwise
ticket the LOW), and run
`post-merge-systemize backfill` at least every two weeks. Beside each run, the
session searches the window's pull-request comments for `recorded` itself, because
systemize does not read a recording made in a thread reply, and tickets each LOW
recorded on two or more pull requests, as well as the recurring clusters systemize
reports.
