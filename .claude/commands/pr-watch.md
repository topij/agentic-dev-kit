---
description: Drive a pull request through the deterministic poll, fix, acknowledge, and re-poll loop until CI is green and review findings are resolved. Use after opening or updating a pull request, when asked to watch CI or reviews, or when a task must continue until its PR is green and clean.
argument-hint: "[pr-number]"
---

Read `docs/agentic-dev-kit/workflows/pr-watch.md` completely and follow it.

Treat `$ARGUMENTS` as the optional PR number or additional watch context. Resolve
the engine path from the repository root.

When the fallback review panel runs here, launch each lens as the agent named after
it (`.claude/agents/<lens>.md`, rendered from `review.fallback_panel.lens_compute.claude`
by `<engine-dir>/panel_prompt.py --lens <lens> --agent-definition`): its frontmatter is what
applies the configured `model` and `effort`, since the delegation tool itself has no
effort parameter. A definition added after this session started was not launchable in
the turn it was written and appeared in the roster later; count on it from the next
session.
