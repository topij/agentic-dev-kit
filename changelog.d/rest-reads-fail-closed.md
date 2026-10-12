## pr-watch: REST reads are judged complete from GitHub's own counts

CHANGED (report shape): on the REST backend, `truncated_reads` now also lists a read
that came back short of a count GitHub sent, not only one stopped by the page
ceiling: a check-runs or combined-status read with fewer rows than its
`total_count`, or an issue-comment or inline-comment read with fewer items than
the PR's `comments` / `review_comments`. `pr_watch` itself still gates nothing on it
(#94 stays open for that), but session-start reports review findings unavailable
when the list is not empty. A comment deleted between the PR read and the comment
read now lists that URL there for that one poll.

CHANGED (engine CLI surface): a REST body that lacks `total_count`, `comments` or
`review_comments`, carries a non-boolean `draft`, or holds a non-object list element
on a read the report needs now makes the poll exit 2 instead of reading as smaller
than it was. A malformed body on the per-check identity read
(`commits/<sha>/statuses`) still degrades that read only, as before. GitHub always
sends these fields; a test that fakes GitHub REST bodies must now include them.
