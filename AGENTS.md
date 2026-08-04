<!-- devkit-source: kit-own — this is the KIT's own entry point, not a rendered one. ./init.sh replaces it with yours; delete this line to claim the file. -->

# AGENTS.md — agentic-dev-kit

The contract every session in this repo runs under, for **both** runtimes. Codex
and other agents that read `AGENTS.md` load this file directly; Claude Code reads
`CLAUDE.md`, which imports it. One file, two bindings — do not copy any of it
into a runtime-specific file.

## Verification

**`make test` is the verification command for this repo.** It runs the full suite
(`scripts/lib/state_paths/tests` + `scripts/tests`) in tens of seconds, supplying its
own dependencies via `uv run --with pytest --with pyyaml`.

The two probes an agent reaches for first both fail here in a way that reads as
"pytest is unavailable in this environment". Neither is evidence of that:

- `uv run pytest` → `error: Failed to spawn: pytest` (pytest is not a project dependency)
- `python3 -m pytest` → `No module named pytest` (the system Python has no pytest)

Do not conclude tests cannot run locally, and do not defer verification to CI, without
having run `make test`. When claiming something is verified, name the command that
established it and its actual result — #54 tracks making this a standing rule.

## Ground rules

- `main` is protected: never commit to it directly. Branch and open a PR — and opening
  the PR is not done; watch it to green and review-clean (`pr-watch`).
  **Cockpit work branches `chore/<slug>` or `feat/<slug>`, never `dev/<scope>`.**
  `dev/` is `vcs.dev_branch_prefix` — the prefix reserved for isolated lanes — and
  `scripts/hooks/pre-push` refuses any push from a `dev/*` branch that touches
  `docs/kit-handoff.md` or `docs/kit-friction-log.md`. A wrap-up commit on a `dev/*`
  branch is blocked by the repo's own hook.
- All configuration lives in `config/dev-model.yaml`; skills and engines read it from
  there. Never hardcode a value that belongs in it.
- The living plan is `docs/kit-handoff.md` — read at session start, updated at wrap-up.
  New friction is recorded in `docs/kit-friction-log.md`.
- Never write a GitHub closing keyword (`close` / `fix` / `resolve` and their forms)
  adjacent to an issue number you do not intend to close — on any surface (PR body,
  commit message, squash message), in any form, even negated or inside code spans.
  Write "#N stays open" instead.

## Runtime parity

This repo is the kit itself, so its own two-runtime setup is the worked example:

- The runtime-neutral workflow definitions live in `docs/agentic-dev-kit/workflows/`.
  `.claude/commands/` and `.agents/skills/` are thin bindings over them.
- **A workflow's behaviour is changed in the shared doc, never in one binding.**
  A change made in an adapter reaches one runtime and silently not the other,
  which is the failure `#243` and `#273` are filed about.
- Doctrine that must reach every runtime does not belong in `.claude/rules/` —
  Claude Code alone reads that directory.
