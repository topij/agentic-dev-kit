# ITEM5-B-UPDATE-02 — current review triage

**Source-scope decision pending; retained execution remains unapproved.** The
prepared source remains `e6d6e77d118454349f8e8bb046e99ef3009c5f5c`. Do not edit its
frozen payload copies to satisfy a review or obtain UPDATE-02 approval while the
source findings below lack an operator disposition. This record proposes a separate
kit-only repair; it does not approve that repair, a deferral or a new retained source.

## Receipt and verification

The complete [CodeRabbit review](https://github.com/topij/agentic-dev-kit/pull/733#pullrequestreview-5178085353)
of `cf373efd3a4d00b36987f73574d567eef004594a` was read with paginated `gh api`
review, inline-comment and issue-comment requests from
`/Users/topi/Coding/agentic-dev-kit` on 2026-09-11. The
[raw receipt and source comparison](phase5-item5-b-update02-evidence_2026-09-11/coderabbit-current-review.json.gz)
preserve complete bodies, including the combined inline findings and top-level
nitpick, before any following fix. The bot excluded compressed evidence; its review
is not a claim that it inspected those archives.

`git show` and `git diff 60fe0dc7ad68922d064c0cf401cff2c4c6d607ac e6d6e77d118454349f8e8bb046e99ef3009c5f5c -- <source-path>`
in that directory at `cf373efd3a4d00b36987f73574d567eef004594a` on 2026-09-11
established that the supplied workflow, conftest and state-guard test payloads equal
the selected source and cockpit files. The cited workflow sections and session-finish
hook predate #731; these findings are not newly introduced #731 regressions.
The evidence retains each payload digest, source blob and actual source diff.

The documented config-check command, run from the cockpit root and then its `docs`
subdirectory at that same revision/date, found the root config but printed
`NO CONFIG` from `docs`. An isolated invocation of the extracted session-finish
hook, with a synthetic leak snapshot and session, replaced interruption and
internal-error statuses with the test-failure status. That is a bounded hook probe,
not a nested pytest session or retained-fixture test. No generic upgrade mutation,
symlink reproduction, initialization or retained writes ran during this triage.

## Findings and proposed disposition

| Review finding | Assessment and boundary |
|---|---|
| [Template contract](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648287) | Valid inherited contradiction: the opening and later free-refresh instruction conflict with `not_installed`. A source repair must preserve recorded template declines. |
| [Config path](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648291) | Reproduced inherited working-directory error. Resolve the intended repo before the config probe and use its absolute path. |
| [Manifest preflight](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648298) | Valid inherited ordering problem: init is overwritten before the manifest refusal. Preserve the distinction the bot's generated prompt conflates: corrupt/dangling manifests stop before mutation and initialization; a valid partial record skips template refresh but retains its existing initialization route. |
| [Destination aliases and failed mutations](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648306) | The combined comment identifies inherited destination-validation and unchecked-command gaps in generic upgrade. Static source inspection supports them; this triage did not reproduce writes through aliases. The local UPDATE-02 procedure does not execute generic upgrade or init and already requires destination checks. Repairing the shipped workflow is separate scope. |
| [Verification command status](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648314) | Valid inherited shell-block gap: later successful commands can mask earlier failures. The source workflow must stop on an unsuccessful required check. UPDATE-02 separately records each command's result. |
| [Pytest exit status](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648316) | The bounded hook probe confirms the inherited overwrite. A source repair must retain non-OK statuses and preserve the leak message; nested-session coverage is required before delivery. |
| [Validator Git environment](https://github.com/topij/agentic-dev-kit/pull/733#discussion_r3988648327) | Disputed: refusal before Git is the declared safety contract, not an accidental availability failure. The audit refuses inherited controls before Git reads; `check=True` prevents the revision command after refusal. The parent environment is unchanged between that check and the revision read. Silently sanitizing only validation would cease checking the environment later commands use. Keep refusal and require the operator to correct the invoking environment explicitly. |
| [Nested pytest timeout](https://github.com/topij/agentic-dev-kit/pull/733#pullrequestreview-5178085353) | Valid inherited harness limitation: `_run_pytest` lacks a timeout. A bounded source follow-up can report timeout with captured output. This does not extend the accepted state-root special-file detection scope. |

The [existing environment proof](phase5-item5-b-update02-evidence_2026-09-11/runtime-guard-proof.json.gz)
records actual refusal and mutation/restoration evidence. It is preserved historical
evidence; no security probe or failed reviewer was rerun to answer the bot.

These source findings remain open pending a scope decision. Recording them here
is not operator acceptance or a tracker deferral. No tracker payload is authorized.
The [incomplete adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/733#issuecomment-5633204702)
also remains incomplete. CodeRabbit's delivered review does not retrospectively
complete that lens or review compressed evidence it excluded.

## Proposed bounded kit-only follow-up

After explicit approval, repair the active kit source in a separate branch/ready PR:

- `docs/agentic-dev-kit/workflows/upgrade.md`: correct the template contract and
  initial config-root lookup; perform read-only scope and destination validation
  before mutation; stop on failed writes or required verification. Preserve absent,
  partial, corrupt/dangling and recorded-decline distinctions.
- `scripts/conftest.py`: preserve incoming non-OK pytest exit status when reporting
  a leak; retain the ordinary successful-session-to-failure transition and message.
- `scripts/tests/test_init_sh.py`, `scripts/tests/test_portability.py` and
  `scripts/tests/test_state_guard.py`: use the existing workflow/hook harnesses for
  the changed paths; cover preflight-before-write, command failure, declared scope,
  alias refusal, config lookup from a subdirectory and interrupted/internal-error
  nested sessions. Bound the nested child pytest helper and retain timeout output.
- `CHANGELOG.md` and the generated source `kit-manifest.json`: record the observable
  contract changes and publish matching source hashes through the existing process.
- Scoped kit execution/handoff/sprint records: retain full review receipts before
  fixes, full `make test` output, separate #561 shell parses, and #393 disclosure.
  Finish required independent review and pr-watch before the kit repair's merge.

This does not authorize editing UPDATE-02's frozen source or payloads in place.
After the separate repair is delivered, prepare a new exact source selection,
payload hashes, destination ledger, predicted baseline, verification and approval
question against fresh read-only retained checkpoints. Preserve the old packet,
questions, ledgers and evidence. The source revision for that replacement is not
known before delivery and must not be invented now.

**Scope question:** Do you approve this separate kit-only follow-up for the source
findings above, including its listed tests, release metadata and scoped kit records,
with a ready PR, required review and merge when clean, followed by preparation of a
revised retained-update packet, while retained fixture/source writes and all existing
fixture/client/settings/tracker exclusions remain prohibited?

This question approves no retained execution. The original exact UPDATE-02
[approval question](phase5-item5-b-update02-decision_2026-09-11.md#exact-decision-and-next-session)
remains preserved and unanswered. Source-scope disposition and required kit review
must precede asking it or its replacement.

**Next session:** obtain the source-scope decision above, then follow that decision;
resolve required-review availability without bypassing the recorded restriction.
Phase 5 item 5 remains incomplete. Item 6 and its replay remain complete, #723's
approved deferral and #585's earlier placement remain, and #724 delivered the #722
batch. The friction sweep stays parked; no exercise is repeated or re-credited.
