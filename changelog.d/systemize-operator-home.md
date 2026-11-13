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
overlay wins over it. A checkout without the overlay, such as a fresh clone or a lane
worktree, sees only the tracked value. If that is empty and `review.bots` is empty
too, `post-merge-systemize` refuses there. No other `systemize` key is overlayable.
