<!-- devkit-source: kit-own — this is the KIT's own entry point, not a rendered one. ./init.sh replaces it with yours; delete this line to claim the file. -->

@AGENTS.md

# Claude Code

The contract above is imported from `AGENTS.md` and is the same one Codex reads —
Claude Code loads an `@path` import into context at session start, so it arrives
in full. Anything below this line is Claude-only; anything that must reach both
runtimes belongs in `AGENTS.md`, not here.

- Path-scoped rules in `.claude/rules/` bind **this runtime only**. Put nothing
  there that a Codex session also needs.
