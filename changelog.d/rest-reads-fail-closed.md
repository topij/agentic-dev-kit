## pr-watch: REST reads are judged complete from GitHub's own counts

CHANGED (report shape): on the REST backend, `truncated_reads` now also lists a read
that came back short of a count GitHub sent, not only one stopped by the page
ceiling: a check-runs or combined-status read with fewer rows than its
`total_count`, an issue-comment or inline-comment read with fewer items than the
PR's `comments` / `review_comments`, or a review read whose last page was full and
carried no next link. `pr_watch` itself still gates nothing on it (#94 stays open
for that), but its consumers do: triage's terminal `pr-watch` receipt needs the list
empty, and session-start reports review findings unavailable when it is not. A
review list that is an exact multiple of 100 long now lists its URL there, and so
does a comment deleted between the two reads; either leaves that receipt unsettled
until a later poll reads clean.

CHANGED (engine CLI surface): a REST body that lacks `total_count`, `comments` or
`review_comments`, carries a non-boolean `draft`, or holds a non-object list element
on a read the report needs now makes the poll exit 2 instead of reading as smaller
than it was. The per-check identity read (`commits/<sha>/statuses`) keeps degrading
as before. GitHub always sends these fields; a test that fakes GitHub REST bodies
must now include them.
