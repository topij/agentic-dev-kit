# CLAUDE.md — agentic-dev-kit

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

- `main` is protected: never commit to it directly. Branch (`dev/<scope>` for cockpit
  lanes) and open a PR — and opening the PR is not done; watch it to green and
  review-clean (`pr-watch`).
- All configuration lives in `config/dev-model.yaml`; skills and engines read it from
  there. Never hardcode a value that belongs in it.
- The living plan is `docs/kit-handoff.md` — read at session start, updated at wrap-up.
  New friction is recorded in `docs/kit-friction-log.md`.
- Never write a GitHub closing keyword (`close` / `fix` / `resolve` and their forms)
  adjacent to an issue number you do not intend to close — on any surface (PR body,
  commit message, squash message), in any form, even negated or inside code spans.
  Write "#N stays open" instead.
