# Adopt continuation: initialization and post-init verification

Continue the fixture staged by PR #682 at its operator handoff. This proposal
covers initialization and Step 4 checks. Adoption completion, a fixture remote or
PR, Phase 5 exit, cs-toolkit replay, TRI-03/TRI-04/TRI-05 and #608/#255 dispositions
remain separate operator decisions.

## Bound fixture and continuity observation

Fixture: `/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture`

Branch: `chore/adopt-agentic-dev-kit`

Fixture baseline: `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2`

Installed kit source: `ab0a6d62308b298478b2f85fc961f14348f35365`

`PYTHONDONTWRITEBYTECODE=1 python3
/private/tmp/adk-adopt-continuation-20260906-AFeElK/check_continuity.py`, run in
`/Users/topi/Coding/agentic-dev-kit` at
`d898660c5da63a91f1916fa6b5f84357b5622ee4` on 2026-09-06 UTC, returned successfully.
It compared copied files to PR #682's retained ledger, preserved inputs to their
retained originals, and config/baseline bytes to the retained corrected versions.
It also checked the installed initializer against the bound source. This is a
continuity check; initialization and post-init verification have not run.

The current shared workflow includes PR #685's Step 3a. The fixture remains bound
to its original installed source so this continuation does not restage or upgrade
the credited exercise. Post-init doctor verification must use an independent
manifest from that immutable source; comparing the old installation to the moving
kit checkout would test a different question.

## Proposed operator command

Run this interactively, keeping the prompt values listed below:

```sh
(
  REPO=/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture
  cd "${REPO:?}" || exit 1
  test "$(pwd -P)" = "$REPO" || exit 1
  "$REPO/init.sh" --no-clobber
)
```

| Prompt | Proposed answer |
|---|---|
| Project name | `adopt-context-fixture` |
| Agent runtime | `codex` |
| Operator forge logins | `none` |
| Tracker backend | `none` |
| Tracker project name | Empty; accept the displayed empty default |
| Tracker board URL | Empty; accept the displayed empty default |
| Protected branch | `main` |
| Notify user id | `tracked-fixture-recipient`, the synthetic tracked fixture value |
| Review bots | `none` |

Retain the synthetic local override `local-fixture-recipient` in its existing
gitignored file. The notification backend remains `none`. Preserve the configured
paths and the fixture-owned wrap-up adapter.

## Resolved narrative decisions

The continuity command above and the direct first-line read in the same directory,
at the same revision and date, observed these paths:

| Path under the fixture | Observed state | Proposed handling |
|---|---|---|
| `AGENTS.md` | MARKED, with fixture-owned policy below the marker | Leave it untouched during initialization; its ownership-marker decision stays pending |
| `CLAUDE.md` | IN_USE, imports `AGENTS.md` | Preserve |
| `ROADMAP.md` | IN_USE | Preserve |
| `notes/history.md` | IN_USE | Preserve |
| `notes/friction.md` | ABSENT | Let the initializer seed it |
| `notes/friction-archive.md` | ABSENT | Let the initializer seed it |

The full prescribed handoff is retained at
`/Users/topi/Coding/agentic-dev-kit/saved_plans/codex-adopt-field-evidence_2026-09-05/operator-handoff.md`.
Keep the initializer's terminal output for Step 4. Its skipped-target list must be
reviewed with the operator; a skipped marked file does not establish completed
adoption. The operator must also confirm that the retained files read as intended.

## Execution authority

The adopt skill at
`/Users/topi/Coding/agentic-dev-kit/.agents/skills/adopt/SKILL.md` delegates to the
shared workflow. Step 3c says: "`/adopt` does not run `init.sh`." Its prescribed
handoff asks the operator to run it personally and see each prompt.

The operator may run the command personally. Alternatively, an explicit instruction
to Codex to execute this exact fixture-only proposal overrides that executor rule
for this exercise. No initialization authority is inferred from prior staging
approval, the budget reminder, or the merged record PRs.

After initialization, inspect its actual output and retained-file decisions, run the
configured portability suites with isolated state, run the document-budget check,
and compare the installed doctor report to the bound source manifest. Record actual
results and limitations before requesting any adoption-completion decision.
