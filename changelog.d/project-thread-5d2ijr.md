## Sessions delete what they created, with an optional standing grant

ADDED (workflow): `session-cleanup.md` gains *Clean up what this session created*. A
session deletes the paths it created and recorded (review rounds, lens and task
worktrees, throwaway clones, extracted archives, killed test runs, merged lanes) once
nothing needs them, and `wrap-up` now does that before its scratch report. Nothing the
session did not create, and nothing holding retained state, is deleted.

Without further action, sessions still ask you before each deletion, as before. To let
them delete their own recorded paths without asking, copy the new *Session cleanup*
section from `docs/AGENTS-sections.md` into your `AGENTS.md`. Engine previews,
attestations and guards still apply under that grant, and age sweeps still need your
approval. A freshly rendered `AGENTS.md` carries a bullet pointing at the rule; an
existing one does not change, so add the bullet yourself if you want it.
