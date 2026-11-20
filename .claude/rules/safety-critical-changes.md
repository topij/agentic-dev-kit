---
# Keep this list equal to `review.safety_critical_paths` in config/dev-model.yaml.
# That key is what sets a fallback review's lens count, and this frontmatter
# cannot read it.
paths:
  - "scripts/dev_session.sh"
  - "scripts/devkit/dev_session.sh"
  - "scripts/panel_prompt.py"
  - "scripts/devkit/panel_prompt.py"
  - "scripts/launch_lane.py"
  - "scripts/isolated_lane.py"
  - "scripts/devkit/isolated_lane.py"
  - "scripts/lib/isolated_guest.py"
  - "scripts/devkit/lib/isolated_guest.py"
  - "scripts/devkit/launch_lane.py"
  # This is the shipped `parallel.claude_settings_profile`. If that key names a
  # different path, replace this entry with the configured path: rule frontmatter
  # cannot resolve values from config/dev-model.yaml.
  - "config/claude-lane-settings.json"
  # pr_watch.py COMPUTES the verdicts (`mergeable` / the legacy `done` alias,
  # `review_class`) that dev_session.sh merge authorizes on through
  # lib/merge_predicate.py, which reads them and derives none. It was left
  # out while `done` looked like a watch-loop verdict — but a change here can authorize a merge on an
  # unreviewed PR just as directly, and the rule has to match the file where the
  # decision is made, not only the one that acts on it.
  - "scripts/pr_watch.py"
  - "scripts/devkit/pr_watch.py"
  - "scripts/lib/subprocess_runner.py"
  - "scripts/devkit/lib/subprocess_runner.py"
  # These select the local review receipt the watcher reads.
  - "scripts/lib/state_paths/repo_root.py"
  - "scripts/lib/state_paths/resolver.py"
  - "scripts/devkit/lib/state_paths/repo_root.py"
  - "scripts/devkit/lib/state_paths/resolver.py"
  # The merge gate itself: `dev_session.sh merge` authorizes on its verdict, so a
  # change here weakens every self-merge as directly as one to the wrapper.
  - "scripts/lib/merge_predicate.py"
  - "scripts/devkit/lib/merge_predicate.py"
  - "scripts/sweep_scratch.py"
  - "scripts/devkit/sweep_scratch.py"
  - "scripts/session_cleanup.py"
  - "scripts/devkit/session_cleanup.py"
  # Some files that can switch a check off without touching an engine (#1150):
  # CI, the hook scripts, and both runtimes' hook registrations. The kit's
  # shipped config comment names some of what this leaves out.
  - ".github/workflows/*"
  - "scripts/hooks/*"
  - "scripts/devkit/hooks/*"
  - ".claude/settings.json"
  - ".codex/hooks.json"
# Add your own send-path / gate / kill-path files or globs here. This rule is useful
# only after its paths match the files that gate sends or destructive/recovery work.
---

Read `docs/agentic-dev-kit/safety-critical-changes.md` completely and apply that
doctrine to every behavioral change in the matched files.
