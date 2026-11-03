## Installed tests no longer assert the kit's template values against your config; `upgrade.md` Step 0 runs under zsh

CHANGED: four installed tests read `config/dev-model.yaml` at your repository root and
asserted the values the kit's template ships. In your repository that file is your own
config, so a correct configuration failed Step 5 of `upgrade.md`. They now skip in a tree
that carries a recorded install baseline (`kit_commit` in `kit-manifest.json`):

- `test_systemize_config.py::test_shipped_config_loads_engine_backed_once_an_operator_is_named`
  (an operator named in `systemize.operator_logins`);
- `test_pr_watch.py::test_the_shipped_list_classes_check_switches_as_safety_critical`
  (a `review.safety_critical_paths` for your own layout);
- `test_pr_followup_hook.py::test_shipped_config_pins_the_selected_reviewer_compute`
  (your own `review.fallback_panel.lens_compute`);
- the exact `systemize:` key set, which moved out of
  `test_portability.py::test_post_merge_systemize_is_shared_thin_and_config_owned` into
  `test_the_shipped_systemize_config_is_complete_and_named_by_the_workflow`. The
  adapter checks stay in the first test and still run in your repository.

What to do: if you kept a local patch of one of these tests, drop it at this upgrade and
take the kit's copy. If you added kit-only entries or keys to your config just to pass
them (the kit's `scripts/hooks/**` in a `scripts/devkit` layout, say, or the optional
`systemize.refuted_flag_*` and `systemize.enforcement_table` keys), you can remove them.

FIXED: `upgrade.md` Step 0's fetch now braces its variables. Under zsh,
`"$UPGRADE_BASE:refs/..."` read as the `:r` modifier and fetched
`refs/heads/mainefs/...`. A new installed test refuses an unbraced `$NAME:` followed by
a letter in any shell block under `docs/agentic-dev-kit/`.
