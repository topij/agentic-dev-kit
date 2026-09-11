# ITEM5-B source-review repair

The operator approved the [bounded kit-only scope](phase5-item5-b-source-review-repair-evidence_2026-09-11/approved-scope.md)
on 2026-09-11: “I approve that repair, its tests and release metadata, review and
merge when clean, then preparation of a revised retained-update packet”. The
[approval record](phase5-item5-b-source-review-repair-evidence_2026-09-11/approval.json)
binds the scope bytes. This authorization covers the separate source repair,
its tests/release metadata, required review and merge when clean, followed by
preparation. It grants no retained fixture/source write or retained execution.

The [complete original review](phase5-item5-b-source-review-repair-evidence_2026-09-11/original-review.json.gz)
was preserved and read before source fixes. It retains the complete CodeRabbit
review at `cf373efd3a4d00b36987f73574d567eef004594a` and the prior source comparison.
The approved changes repair inherited upgrade and test-harness behavior; they do
not change #731's delivered history or the original UPDATE-02 payloads and ledgers.

The source branch starts at `bc0c33a3af93d78545050612649f49fa72107a40`, the #732
merge read back from `origin/main` with `git fetch --no-tags origin main` and
`git rev-parse origin/main` in `/Users/topi/Coding/agentic-dev-kit` on 2026-09-11.
Kit #731 remains the earlier repair at `e6d6e77d118454349f8e8bb046e99ef3009c5f5c`.
PR #733 retains the unapproved packet and its incomplete independent-review receipts.
The new source review cannot retrospectively complete those receipts.

The implementation moves manifest/scope decisions and refresh-destination checks
before the first copy, preserves recorded template declines and partial-record
handling, anchors the initial config probe, and stops on failed required commands.
Refresh preflight rejects existing destination aliases and unexpected file kinds;
its stated operating condition forbids concurrent writes between check and copy.
The pytest leak hook retains non-OK exit statuses, and the nested helper reports
timeouts with captured output. The inherited special-file-root detector limitation
remains accepted and unextended; ownership acceptance does not verify functionality
or field exit.

[PR #734](https://github.com/topij/agentic-dev-kit/pull/734) carries this source repair.
The [author verification record](phase5-item5-b-source-review-repair-evidence_2026-09-11/author-verification.json.gz)
retains complete argv, working directory, revision, date, status and output.
`make test` in `/Users/topi/Coding/agentic-dev-kit` at
`bcd497bf9e565b7f96ebc856d245a3d0c47b680d` on 2026-09-11 printed
`2 failed, 2528 passed, 1 skipped in 390.50s (0:06:30)`. The failures were the
known #393 deep-JSON case and the temporary changelog heading awaiting the forge's
PR identifier. After creation assigned #734, the exact changelog extraction test
named in the record printed `1 passed in 6.61s` at that revision/date/directory
with the assigned heading in the working tree. This targeted correction does not
turn the earlier full run into a passing one. The focused workflow/hook run and
individual shell parses covering #561 are retained alongside it.

The [delivery checkpoint](https://github.com/topij/agentic-dev-kit/pull/734#issuecomment-5637494093)
retains the completed independent reports, CodeRabbit disposition and exact-head
watch/merge. `gh pr view 734 --repo topij/agentic-dev-kit` with the JSON fields in
that checkpoint, from `/Users/topi/Coding/agentic-dev-kit` at
`7224547da0c766a4fd9ee5791e53ddb3f7db6cdf` on 2026-09-11, read back merge `7e0232ed871b37a315c5509c97b83d3b00b1a3fd`.
The source repair preserves #393 and #561 as separate limitations; their
implementations are unchanged. No source coverage is inferred from retained-fixture
results or historically incomplete reviewers.

**Next decision:** the [UPDATE-03 packet](phase5-item5-b-update03-decision_2026-09-11.md)
selects the delivered immutable source with fresh checkpoint evidence, bound payloads,
ledger/baseline prediction, preservation/verification/rollback and an exact question.
UPDATE-01 remains consumed and historical UPDATE-02 records remain unchanged.
No retained update follows without its separate exact approval.

Phase 5 item 5 remains incomplete; item 6 and replay evidence remain complete.
Do not repeat or re-credit cs-toolkit #2222/#2223/#2255. #723 remains the approved
upstream deferral; #585 remains earlier outside Phase 6; #724 delivered #722's batch.
The friction sweep stays parked pending its exact operator decision.
