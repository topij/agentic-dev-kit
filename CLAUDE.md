<!-- devkit-source: kit-own — this is the KIT's own entry point, not a rendered one. ./init.sh replaces it with yours; delete this line to claim the file. -->

@AGENTS.md

# Claude Code

The contract above is imported from `AGENTS.md` and is the same one Codex reads —
Claude Code loads an `@path` import into context at session start, so it arrives
in full. Anything below this line is Claude-only; anything that must reach both
runtimes belongs in `AGENTS.md`, not here.

- Path-scoped rules in `.claude/rules/` bind **this runtime only**. Put nothing
  there that a Codex session also needs.

## Claude Code cloud sessions

A claude.ai/code cloud session works on a fresh clone in a container, so a few things a
local checkout already has must be set up first.

- **Run `make install-hooks` before the first push.** A fresh clone has no pre-push
  hook, and that hook is what refuses a stale `kit-manifest.json` or a wrap-up file
  pushed from a `dev/*` branch.
- **Git must support `--no-lazy-fetch` (2.44 or later).** `panel_prompt.py` and
  `check_record_prose.py` call it. Install a newer Git in the cloud environment's own
  setup script, not in `.claude/settings.json`: the kit ships that file to adopters, and
  cloud setup is the adopter's own hook
  ([runtime-parity: *Adopter-owned cloud setup hook*](docs/agentic-dev-kit/runtime-parity.md#adopter-owned-cloud-setup-hook)).
- **Some tests fail there for environment reasons, not code.** `make test` at `e659936`
  on 2026-10-12 in a cloud session failed exactly these, and passed the rest:
  - tests that make a path unreadable and expect a refusal, which root ignores:
    `test_kit_doctor.py::test_a_target_init_sh_will_not_touch_is_not_reported_as_unrendered[unreadable]`,
    `test_sweep_scratch.py::test_linked_worktree_whose_git_dir_cannot_be_statted_is_kept`;
  - tests of child-process and process-group cleanup, which the sandbox constrains:
    `test_lane_launcher.py::test_descendant_cannot_outlive_a_successful_child_leader`,
    `test_lane_launcher.py::test_detached_descendant_blocks_success_and_is_terminated`,
    `test_lane_launcher.py::test_interruption_terminates_detached_launch_lineage`,
    `test_runtime_smoke.py::test_a_child_that_outlives_its_timeout_is_stopped_with_what_it_started`,
    `test_runtime_smoke.py::test_what_a_client_leaves_in_its_group_goes_with_it`.

  Any other failure is real. For these, rely on CI or a local run, and say so in the
  verification claim rather than calling the run green.
