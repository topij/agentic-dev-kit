## wrap-up: commit only what nothing else records, on the session's own pull request

CHANGED (gate semantics): `wrap-up` now starts with a handoff test. A session whose
pull requests, commits, changelog fragments and tracker issues already record what it
did ends as `successful-noop`, with no commit, no pull request and no review. When the
test leaves something (a decision, an abandoned approach, half-finished state, a next
step with no ticket), the record goes on the session's own pull request before its
opening review, and a separate wrap-up pull request is only for a session whose pull
requests are already reviewed or merged, or that had none. If you script or check for
a wrap-up pull request after every session, stop expecting one.

CHANGED (record shape): `wrap-up` writes no `## Session — <date>` entry. Decisions and
what was not established go in the entry of the workstream they bear on, pointing at
their record. The shipped `docs/templates/handoff.md.tmpl` seeds no session entry. Keep
an existing handoff's dated entries; the archive sweep still moves them to history
when the file crosses its budget. A wrap-up may now also correct a line in any
workstream entry that calls merged work open or names a closed issue, and still asks
before rewriting a `▶ Next:`.

CHANGED (report shape): `session-start` reads the protected branch's recent
first-parent log for what just shipped. Its briefing's `Last session:` line is now
`Recently merged:`, and it lists a workstream entry that names merged or closed work
as owed as a housekeeping item.
