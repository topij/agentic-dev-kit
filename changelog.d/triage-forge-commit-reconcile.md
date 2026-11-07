## triage: hook-free sweep commit, scoped config fingerprint, and two approval-bound routes for held sessions

CHANGED (gate semantics): the triage finalize engine commits the archive sweep with every
git hook disabled (`git -c core.hooksPath=/dev/null commit --no-verify`). An adopter
commit hook no longer runs on that commit, so one that reformats or re-stages Markdown no
longer makes every sweep commit `ambiguous`. The pull request's CI still checks the
committed bytes. If you relied on a commit hook running on the sweep commit, run that
check in CI instead.

CHANGED (report / return shape): a new triage session's `config_fingerprint` covers only
the configuration the triage engines read: `paths.engines`, `paths.friction_log`,
`paths.friction_log_archive`, `state.dirname`, the `triage` keys,
`vcs.protected_branch`, `vcs.triage_branch_pattern`, and the whole `tracker` and
`notify` sections. Changing any other key, such as `review.*`, no longer holds an
in-flight session with `configuration-identity`. A test or tool that recomputed the
fingerprint as the digest of the whole merged config must use
`triage.model.scoped_fingerprint` instead. A dead owner's gate that an earlier engine
left under the same configuration stays recoverable with `recover`.

ADDED (engine CLI surface): `resume` accepts a `config_rebind` request for a session an
earlier engine recorded under the whole-config fingerprint. After this upgrade, such a
session is held with `configuration-identity` until you rebind it. Pass the drafted
`config/dev-model.yaml` (usually `git show <protected_branch_head>:config/dev-model.yaml`)
as `legacy_config`, then approve the returned `core_digest`. The steps are in the triage
workflow's `recovery.md`, *Configuration rebind*. A completed state still retires across
a configuration change without a rebind.

ADDED (engine CLI surface): a finalization resume over a verified `branch-create`
followed by an `ambiguous` `commit` returns a `commit-reconciliation` plan. When the
read-back proves the commit never left the machine (no remote branch, no pull request,
one commit on the base touching only the two sweep paths), approving its `plan_digest`
with `commit_reconciliation` and a new `worktree` discards the local branch and worktree
and restarts finalization from the current protected head. The steps are in the triage
workflow's `finalize.md`, *Local commit reconciliation*.

ADDED (report / return shape): triage state may carry two optional keys,
`config_rebind` and `finalization_reconciliations`. A tool that rejects any state key
it does not know must accept both.
