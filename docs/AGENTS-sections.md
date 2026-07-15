# AGENTS.md sections

Copy and adapt this section into an adopting repository's `AGENTS.md`. Keep project
status in the configured handoff, not in `AGENTS.md`.

## Agentic development workflow

- Read `config/dev-model.yaml` before running a kit workflow; paths and runtime
  mappings are configuration, not prompt literals.
- At the start of a development session, use the repository's `session-start` skill
  to read the handoff, friction log, pull requests, CI, and tracker before choosing
  work.
- After opening or updating a pull request, use `pr-watch` and continue until CI is
  green and every review finding is fixed or explicitly answered.
- Use `parallel` only for lanes with disjoint source-file footprints. The cockpit
  owns the configured handoff and friction log; lanes report through their PR bodies.
- At the end of every meaningful session, use `wrap-up` to update the configured
  handoff, capture workflow friction, and leave one clear next step.
- For customer-facing gates, destructive operations, recovery paths, security work,
  and changes to the lane-safety engines, read and apply
  `docs/agentic-dev-kit/safety-critical-changes.md`. Green CI is necessary but not
  sufficient; require independent review and operator sign-off.
