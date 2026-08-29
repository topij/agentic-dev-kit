---
paths:
  - "scripts/dev_session.sh"
  - "scripts/devkit/dev_session.sh"
  - "scripts/launch_lane.py"
  - "scripts/devkit/launch_lane.py"
  # This is the shipped `parallel.claude_settings_profile`. If that key names a
  # different path, replace this entry with the configured path: rule frontmatter
  # cannot resolve values from config/dev-model.yaml.
  - "config/claude-lane-settings.json"
  # pr_watch.py COMPUTES the merge gate (`mergeable` / the legacy `done` alias)
  # that dev_session.sh merely re-checks. It was left out while `done` looked
  # like a watch-loop verdict — but a change here can authorize a merge on an
  # unreviewed PR just as directly, and the rule has to match the file where the
  # decision is made, not only the one that acts on it.
  - "scripts/pr_watch.py"
  - "scripts/devkit/pr_watch.py"
# Add your own send-path / gate / kill-path files or globs here. This rule is useful
# only after its paths match the files that gate sends or destructive/recovery work.
---

Read `docs/agentic-dev-kit/safety-critical-changes.md` completely and apply that
doctrine to every behavioral change in the matched files.
