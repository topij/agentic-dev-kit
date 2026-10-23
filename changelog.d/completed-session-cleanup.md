## Completed-session cleanup

ADDED: Add `scratch.session_registry: cleanup-sessions` to opt into
`session_cleanup.py`. Follow `docs/agentic-dev-kit/session-cleanup.md` to register
review allocations, retain required evidence and preview an exact cleanup scope
that remains discoverable after the task checkout disappears. Approve those paths
before applying. Use native archive for Codex-managed worktrees and retry from the
primary checkout; protected or active leftovers remain incomplete cleanup.

Add the installed `session_cleanup.py` path to `review.safety_critical_paths`
and your runtime safety-critical bindings when upgrading an existing installation.
Fresh bindings and the kit configuration include it.
