"""Controlled triage policy shipped with the installed tests."""

from __future__ import annotations


def triage_config_text() -> str:
    # Ordinary fixtures own their policy and require no optional init snapshots.
    # Keep adopter configuration confined to the explicit portability cases.
    return '''paths:
  engines: scripts
  friction_log: docs/kit-friction-log.md
  friction_log_archive: docs/kit-friction-log-archive.md
vcs:
  forge: github
  protected_branch: main
  triage_branch_pattern: "chore/triage-{date}-{session}"
  systemize_branch_pattern: "chore/systemize-{date}"
triage:
  analysis_tier: default
  state_path: "state/triage/triage-pipeline-state_{mode}.json"
  gate_path: "state/triage/triage-pipeline-gate_{mode}.lock"
  recovery_bundle_pattern: "state/triage/recovery-bundle_{mode}_{gate_digest}.json"
  frozen_inbox_pattern: "state/triage/frozen-inbox_{mode}_{date}_{session}.json"
  report_root: reports
  report_pattern: "reports/triage_{mode}_{date}_{session}.md"
  draft_engine: triage_friction_log.py
  finalize_engine: finalize_triage.py
  commit_subject: "docs(triage): graduate friction-log entries"
  pr_draft: false
tracker:
  backend: github-issues
  project_name: "topij/agentic-dev-kit"
  url: "https://github.com/topij/agentic-dev-kit/issues"
  linear:
    team_id: ""
    project_id: ""
    label_name: ""
review:
  bots: [coderabbit]
  bot_author_aliases:
    coderabbit: [coderabbitai, "coderabbitai[bot]"]
  bot_pending_grace_minutes: 15
notify:
  backend: slack
  user_key: ""
models:
  tiers:
    default: standard
state:
  dirname: state
  test_guard_exclude: []
'''
