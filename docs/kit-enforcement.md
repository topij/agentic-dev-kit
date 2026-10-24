# Enforcement table

Each row pairs a standing rule in this repository with what enforces it. `post-merge-systemize`'s
shared-rule route reads this table before it proposes a rule and adds or updates a row in the
same patch (`systemize.enforcement_table` in `config/dev-model.yaml` names this file). A repeat
of a rule marked `judgement, unenforced` is a candidate for a check.

| Rule | Where it is written | Enforced by |
|---|---|---|
| Commit `kit-manifest.json` regenerated after editing a kit-owned file | `CONTRIBUTING.md` | `scripts/hooks/pre-push` (stale-manifest guard) and the `driftcheck` test in `make test` |
| No wrap-up narrative file pushed from a `dev/*` branch | `AGENTS.md` *Ground rules* | `scripts/hooks/pre-push` (dev/* narrative-file guard) |
| A shipped kit-owned file names an engine as `<engine-dir>/…`, not a bare `scripts/` path | `docs/agentic-dev-kit/` doctrine | `test_no_shipped_kit_owned_file_hardcodes_a_bare_engine_path` in `scripts/tests/test_kit_doctor.py` |
| Numbers in prose carry a command, revision and date stamp | `AGENTS.md` *Numbers in prose* | `scripts/check_record_prose.py` for the configured narrative paths; judgement, unenforced elsewhere |
| No closing keyword next to an issue the change does not close | `AGENTS.md` *Ground rules* | `scripts/check_record_prose.py` for the configured narrative paths; judgement, unenforced elsewhere |
| An observable change adds its own `changelog.d/` fragment | `AGENTS.md` *Ground rules* | judgement, unenforced |
| An instruction file stays within its line budget | `config/dev-model.yaml` `doc_budgets` | `scripts/check_doc_budget.py`, warn-only |
