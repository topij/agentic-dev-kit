## pr_watch: `--disposition` refuses a path; a stamp may name its directory before the date

BREAKING (engine CLI surface): `pr_watch.py --record-review … --disposition <value>` now
exits 2 with a usage error, before anything is posted or recorded, when the value, with
surrounding whitespace stripped, names an existing file or directory (#1013). Such a value
was posted verbatim as the PR comment. `--disposition -` is unchanged and still reads stdin. If
you passed a report's path, pipe its contents instead:
`… --disposition - < report.md`. A literal one-line disposition that happens to match a path
in the working directory must also go through stdin.

CHANGED (report / return shape): the `verification_stamp_behind_head` finding now also
reads a stamp with one `in <dir>` clause between the sha and the date, such as
`` at `<sha>`, in `<dir>`, on <date> `` (#1014). A PR whose only stamp at its head used that
order was reported as stamped behind the head, and now is not. Nothing to do. A pinned
test that expects that order to go unread needs updating.
