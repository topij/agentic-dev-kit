## Workflows: a writing guide, and parallel's mutation matrix moves to its own file

CHANGED (report / return shape): `docs/agentic-dev-kit/workflows/parallel.md` no longer
holds the semantic mutation matrix. It points to the new
`docs/agentic-dev-kit/parallel-verification.md`. `post-merge-systemize.md` and
`triage-friction-log.md` now point to the new `docs/agentic-dev-kit/writing-for-agents.md`.
Both new files are `KIT_OWNED`, so `kit_doctor` lists them if you lack them. During
`/upgrade`, take them together with those three workflow files. A refreshed workflow
without them sends the agent to a file that is not there.
