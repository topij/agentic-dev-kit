## `systemize.operator_logins` may be set in the local overlay

`config/dev-model.local.yaml` now accepts `systemize.operator_logins`, beside
`notify.user_key` and `state.test_guard_exclude`. Before this, an overlay that set it
stopped every config load with `systemize.operator_logins — not overlayable`.

To keep your operator logins out of git, move them from `config/dev-model.yaml` to the
overlay:

```yaml
# config/dev-model.local.yaml
systemize:
  operator_logins: [your-login]
```

Leave the tracked value `[]`, because `./init.sh` writes the tracked file and the
overlay wins over it. A checkout without the overlay, such as a fresh clone or a
worktree made by plain `git worktree add`, sees only the tracked value; a lane that
`dev_session.sh` creates gets a copy of the primary checkout's overlay. If the value
a checkout sees is empty and `review.bots` is empty too, `post-merge-systemize`
refuses there. No other `systemize` key is overlayable.

## A local config overlay that Git tracks is refused

`kitconfig.load_config()` now raises `ValueError` (`local config overlay is tracked by
Git`) when `config/dev-model.local.yaml` is in Git's index, committed or staged. If you
committed your overlay, remove it from the index with
`git rm --cached config/dev-model.local.yaml`, keep `config/*.local.yaml` in
`.gitignore`, and commit that removal.
