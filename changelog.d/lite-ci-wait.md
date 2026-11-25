## Lite wrap-up reports the pull request's checks

CHANGED: when the lite `wrap-up` opens or updates a pull request (a repository that sets
`vcs.protected_branch`), it now reads that pull request's checks once before it reports,
with `gh pr checks <pull-request>` on GitHub, and reports them as failed, pending,
passed, none reported or not established. It does not wait for the checks or repair a
failed one. Merging is still the operator's.

Nothing to do beyond taking the new `lite-wrap-up.md` through `kit_doctor.py
--upgrade-lite`. A repository without `vcs.protected_branch` is unaffected.
