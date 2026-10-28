# AGENTS.md sections

Copy and adapt these sections into an adopting repository's `AGENTS.md`. Keep project
status in the configured handoff, not in `AGENTS.md`.

## Agentic development workflow

- Read `config/dev-model.yaml` before running a kit workflow; paths and runtime
  mappings are configuration, not prompt literals.
- At the start of a development session, use the repository's `session-start` skill
  to read the handoff, friction log, pull requests, CI, and tracker before choosing
  work.
- When creating a tracker ticket, record its execution environment and required
  inputs before presenting the payload. Follow
  `docs/agentic-dev-kit/ticket-execution-environment.md`; `session-start` uses that
  contract to recommend work compatible with the current session.
- After opening or updating a pull request, use `pr-watch` and continue until CI is
  green and every review finding is fixed or explicitly answered.
- Open completed work ready for review by default. Draft is only for a bounded
  material unfinished-work window that must already exist on the remote pull request;
  the run that opens it owns the ready transition. Ready status invites review and does
  not grant merge authority. Run `pr-watch --assert-ready` after ready creation or
  transition, before review polling. Follow the shared policy in
  `docs/agentic-dev-kit/workflows/pr-watch.md`.
- Use `parallel` only for lanes with disjoint source-file footprints. The cockpit
  owns the configured handoff and friction log; lanes report through their PR bodies.
- Before every pull request goes to review, run `wrap-up`'s handoff test. It
  decides whether the work left anything its pull request, commits and tracker
  issues do not already record, and commits only that to the configured handoff on
  that pull request; most pull requests leave nothing and commit nothing. Route
  workflow friction when it is found. Run the full `wrap-up` when the operator asks,
  and offer it in one line when a session ends with half-finished state, a decision
  only in the conversation, or unrouted friction.
- Delete the files and directories the session created once nothing needs them,
  while working and before ending, following *Clean up what this session created*
  in `docs/agentic-dev-kit/session-cleanup.md`. Never delete what the session did
  not create or what holds retained state.
- For customer-facing gates, destructive operations, recovery paths, security work,
  and behavioral changes to the configured `<engine-dir>/pr_watch.py`,
  `<engine-dir>/dev_session.sh`, `<engine-dir>/launch_lane.py`,
  `<engine-dir>/sweep_scratch.py`, `<engine-dir>/session_cleanup.py`, or the profile named by `parallel.claude_settings_profile` (shipped as
  `config/claude-lane-settings.json`), the CI workflows, the hook scripts, or the runtime
  hook registrations (`.claude/settings.json`, `.codex/hooks.json`), read and apply
  `docs/agentic-dev-kit/safety-critical-changes.md`. Green CI is necessary but not
  sufficient; require independent review and operator sign-off.

## Session cleanup

Optional. Add it only if you, the operator, want sessions to delete what they created
without asking you for each path. It is the standing grant that
`docs/agentic-dev-kit/session-cleanup.md` refers to; leave it out and sessions ask.

- **Standing cleanup authorization.** The operator authorizes every session in this
  repository to delete, without asking first, the paths that session created and
  recorded, of the kinds listed in *Clean up what this session created* in
  `docs/agentic-dev-kit/session-cleanup.md`. Every engine preview, attestation and
  guard still applies, and an engine `kept` result stays kept. This does not cover
  an age sweep (`sweep_scratch.py --apply --older-than`) or any path another session
  or person created.
