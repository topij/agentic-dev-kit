# ITEM5-B kit review repair decision

**Prepared, not approved.** `ITEM5-B-KIT-REVIEW-01` is new scope. ACCEPT-01
accepted the preserved-file ownership outcomes. PR-01 applied its exact fixture
payloads and created the private ready PR; its handoff is paused at review findings.
Neither earlier approval authorizes this repair, a retained-tree update or fixture merge.

## Findings and recorded review

The fixture review at `f770f183bf6691f1f706c676b740cf2ef5ceb766` completed with
independent adversarial and correctness lenses on 2026-09-10. Actual compute was
`gpt-6-astra`, effort `high`, as retained in the execution evidence.
The complete reports were posted and read back before preparing the candidate:

- [Adversarial receipt](https://github.com/topij/adk-item5-b-field-20260909/pull/1#issuecomment-5622780057):
  P2, inherited gap, not a regression. The unchanged state guard misses a test
  creating a regular file at the repository's `state` path. The test process exits
  successfully, while the reviewed state-saving path then raises `NotADirectoryError`.
  The report does not claim a bypass of the entire hosted workflow.
- [Correctness receipt](https://github.com/topij/adk-item5-b-field-20260909/pull/1#issuecomment-5622712808):
  P3, imprecision, no demonstrated behavioral regression. `kit-current` is described
  as byte-identical, although the comparator normalizes line endings.

These findings are separate from the disclosed #393 deep-JSON source-suite failure
and #561's syntax-check coverage gap. The [acceptance execution](phase5-item5-b-acceptance-execution_2026-09-10.md)
retains the actual local and hosted results and the unchanged retained-tree checkpoint.
A passing hosted check does not dispose of independent findings. No clean-review
receipt is claimed for the fixture head.

## ITEM5-B-KIT-REVIEW-01 — exact proposed kit-only work

The [write ledger](phase5-item5-b-review-repair-proposal_2026-09-10/write-ledger.json)
binds complete payload files, destination modes and before/after SHA-256 values.
The [reviewable patch](phase5-item5-b-review-repair-proposal_2026-09-10/proposed-repair.patch.txt)
has SHA-256 `14ff9579cde9166445e22b0ba2d898e8bb3330b34a38bf1ea84a2028b6593afd`.
The proposed production destinations are exclusively in the kit cockpit:

| Destination | Proposed change |
|---|---|
| `/Users/topi/Coding/agentic-dev-kit/scripts/conftest.py` | Hash a regular file at the `state` root into its root snapshot entry before the existing directory check. Detect creation and content changes. Keep the documented root-symlink and observation-window limits; add no new traversal or recovery mechanism. |
| `/Users/topi/Coding/agentic-dev-kit/scripts/tests/test_state_guard.py` | Add nested-pytest behavioral cases for new, unchanged and modified regular root files in the declared flat/nested layouts. An unchanged baseline must remain accepted. |
| `/Users/topi/Coding/agentic-dev-kit/docs/agentic-dev-kit/workflows/upgrade.md` | Describe `kit-current` as equality of rendered text after newline normalization. Comparator behavior remains as implemented. |
| `/Users/topi/Coding/agentic-dev-kit/CHANGELOG.md` | Insert the supplied entry template before the first existing PR entry. Substitute only the authoritatively returned repair PR number and UTC execution date; retain the template hash, substituted values and resulting file hash. Never predict a PR number. |

The changelog [entry template](phase5-item5-b-review-repair-proposal_2026-09-10/changelog-entry.template.md)
has SHA-256 `928b5492070da41d523f77195ea60436c738c6b3575493b0bd4efaeca45dacdd`.
Its variables are declared in the ledger because the repair PR does not exist yet.
The before hash of every destination must still match immediately before applying
this proposal; a mismatch needs an amended packet, not a silent rebase of payload bytes.

This decision would also authorize the necessary kit branch, commits, push, ready
repair PR, verification, independent review and scoped execution/handoff records.
Use a fresh `chore/item5-b-review-repair-20260910` branch from the read-back protected
head after the current record delivery. Preserve any intervening operator work.
A new repair execution evidence directory may hold before bytes/hashes, command
logs, isolated verification/reviewer identities, actual results and forge receipts;
use new owned scratch/cache/state locations, never historical UPDATE/replay roots.

Treat the detector repair as operator-merge because it protects verification state.
The [safety-critical doctrine](../docs/agentic-dev-kit/safety-critical-changes.md)
says: “Merge class: changes governed by this rule are **operator-merge**”. This
proposal authorizes the ready repair PR and review handoff; hold its exact reviewed
head for an operator merge decision. The current record-only PR keeps its existing
standing merge-when-clean authority.

**Excluded:** retained fixture or retained source writes, any baseline refresh,
initialization, adapter refresh, client/trust/profile changes, tracker payloads,
fixture repository/settings changes, fixture PR closure or merge. A delivered kit
repair would need its own later exact retained-update decision before it can alter
fixture PR #1. Do not repeat consumed UPDATE-01 to carry it there.

## Preparation evidence and required verification

Preparation used `/private/tmp/item5-b-review-proposal-srbdj7uq/repo`, detached at
`914c2e4ef06a33d88ae7c94a823d3262a9526278`, with the candidate bytes recorded in
[verification.json](phase5-item5-b-review-repair-proposal_2026-09-10/verification.json).
Commands ran on 2026-09-10 with isolated cache/state paths and Python optimization
unset. Production kit files and retained fixture/source files were not changed.

| Command in that proposal clone | Actual result |
|---|---|
| `uv run --with pytest --with pyyaml python -B -m pytest scripts/tests/test_state_guard.py::test_guard_observes_regular_file_at_state_root -q`, with the original guard and proposed tests | `4 failed, 2 passed in 2.10s`, exit `1`. The failure output shows the inner pytest processes leaving root-file writes while exiting successfully. |
| `uv run --with pytest --with pyyaml python -B -m pytest scripts/tests/test_state_guard.py -q`, with proposed guard/tests | `53 passed in 16.59s`, exit `0`. |
| `uvx ruff@0.16.0 check --no-fix scripts/conftest.py scripts/tests/test_state_guard.py` | Exit `0`. |

These focused preparation runs do not substitute for the repair's full `make test`.
After approval, bind absolute cockpit/fixture/source roots, assert the owning `pwd`
before writes, verify destination hashes/modes and serialize checkout/test/staging
operations. Read the staged diff before a separate commit. Render the changelog with
the returned repair PR identity before final review; no placeholder ships.

Run `make test` at the repair revision and let it finish; read its actual summary.
Run separate `bash -n` calls for `scripts/dev_session.sh`,
`scripts/reconcile_sessions.sh`, `scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`
and `sh -n init.sh` for #561's omitted parses. Keep #393's exact traceback separate;
any different failure, missing terminal summary or unexpected write stops for
assessment. Capture mutation/restoration evidence for the new guard branch. Complete
the independent adversarial/correctness panel and hosted CI at the repair's exact
head, recording review receipts before fixes. Never substitute the earlier fixture
panel for review of a new repair head.

Before applying the kit repair, save each destination's original bytes and hash.
For local undo, require the affected files still equal the proposed/recorded attempt
and restore only those destinations; retain the attempt commit/branch and evidence.
Intervening work stops undo. No broad reset/clean, historical rollback, remote deletion,
PR closure or fixture/source restoration is authorized by this proposal.

## Exact approval question

**Approve ITEM5-B-KIT-REVIEW-01 as scoped: apply the hash-bound kit-only guard,
regression-test and wording payloads, add the supplied changelog entry, run required
verification and complete the ready repair PR through independent review, holding
its reviewed head for an operator merge decision and leaving retained trees,
baseline, fixture PR merge, clients and trackers untouched?**

Approval of this proposal would not complete Phase 5 item 5. Preserve item 6's
completed replay and the acceptance packet's remaining systemize field-exit matrix.
