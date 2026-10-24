# Enforcement table

Each row pairs a standing rule in this repository with what enforces it. `post-merge-systemize`'s
shared-rule route reads this table before it proposes a rule and adds or updates a row in the
same patch (`systemize.enforcement_table` in `config/dev-model.yaml` names this file). A repeat
of a rule whose *Enforced by* cell is `judgement, unenforced` is a candidate for a check. A
review preflight, a pull request template checkbox or a warning does not stop a change, so a
row that relies on one says `judgement, unenforced` and names it under *Notes*.

| Rule | Where it is written | Enforced by |
|---|---|---|
| Commit `kit-manifest.json` regenerated after editing a kit-owned file | `CONTRIBUTING.md` | `scripts/hooks/pre-push` (stale-manifest guard) and the `driftcheck` test in `make test` |
| No wrap-up narrative file pushed from a `dev/*` branch | `AGENTS.md` *Ground rules* | `scripts/hooks/pre-push` (dev/* narrative-file guard) |
| A shipped kit-owned file names an engine as `<engine-dir>/…`, not a bare `scripts/` path | the test's own docstring | `test_no_shipped_kit_owned_file_hardcodes_a_bare_engine_path` in `scripts/tests/test_kit_doctor.py` |
| Numbers in prose carry a command, revision and date stamp | `AGENTS.md` *Numbers in prose* | judgement, unenforced |
| No closing keyword next to an issue the change does not close | `AGENTS.md` *Ground rules* | judgement, unenforced |
| An observable change adds its own `changelog.d/` fragment | `AGENTS.md` *Ground rules* | judgement, unenforced |
| `AGENTS.md` stays within its line budget | `config/dev-model.yaml` `doc_budgets` | judgement, unenforced |

## Notes

- The `pre-push` rows hold only in a checkout that ran `make install-hooks`, and both
  guards skip, fail-open, when the hook finds no `python3`. CI's `driftcheck` test gates
  the manifest rule everywhere else; the `dev/*` guard has no CI backstop.
- The engine-path test covers the files `kit-manifest.json` lists as kit-owned, and keeps an
  allowlist of known pre-existing paths.
- `scripts/check_record_prose.py` is a review preflight that the fallback panel runs on the
  narrative paths. It checks the commit and date of the stamps it recognises and flags
  closing keywords. It does not find a number that carries no stamp, and no hook or CI step
  runs it.
- The pull request template asks for the changelog fragment as a checkbox.
- `scripts/check_doc_budget.py` warns at session start and exits non-zero only under
  `--strict`. `CLAUDE.md` and `.claude/rules/` have no budget.
