## Lite wrap-up waits for the pull request's checks

CHANGED: when the lite `wrap-up` opens or updates a pull request (a repository that sets
`vcs.protected_branch`), it now waits for that pull request's checks before it reports,
reading `gh pr checks <pull-request>` on GitHub every few minutes for at most 30 minutes. A failed
check is repaired on the session branch, reviewed, pushed and waited on again, with at
most two repair pushes in a session and never by weakening the check. The report says
what the checks said: passed, failed, none reported, or not established. Merging is
still the operator's.

Nothing to do beyond taking the new `lite-wrap-up.md` through `kit_doctor.py
--upgrade-lite`. A repository without `vcs.protected_branch` is unaffected.
