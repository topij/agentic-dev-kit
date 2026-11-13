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
`dev_session.sh` creates gets a copy of the primary checkout's overlay when the lane's
base ref ignores `config/dev-model.local.yaml`. If the value a checkout sees is empty
and `review.bots` is empty too, `post-merge-systemize` refuses there.
No other `systemize` key is overlayable.

## A tracked local config overlay fails the test suite

`test_kitconfig.py::test_no_local_config_overlay_is_tracked` fails when Git's index
holds any `config/*.local.yaml`, committed or staged, so a CI that runs the kit's tests
fails on a pull request that force-adds one. `load_config` itself still reads an
overlay whether or not Git tracks it. If you committed your overlay, run
`git rm --cached config/dev-model.local.yaml`, keep `config/*.local.yaml` in
`.gitignore`, and commit that removal.
