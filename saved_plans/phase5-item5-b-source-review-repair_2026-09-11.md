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

Validation and complete source-review/delivery receipts will be appended after the
actual commands finish. Preserve #393 as a separate known test failure and cover
#561's recipe gap with individual shell parses. Do not infer source coverage from
installed-fixture results or from an incomplete reviewer.

**Next:** finish source verification and required review, then merge under the
operator's scoped authority. Prepare a replacement retained-update packet against
the delivered immutable source with a fresh read-only checkpoint comparison, new
hash-bound payloads/ledger/baseline prediction, preservation/verification/rollback
and exact approval question. Preserve UPDATE-01's consumed decision and historical
UPDATE-02 records. No retained update follows without its separate exact approval.

Phase 5 item 5 remains incomplete; item 6 and replay evidence remain complete.
Do not repeat or re-credit cs-toolkit #2222/#2223/#2255. #723 remains the approved
upstream deferral; #585 remains earlier outside Phase 6; #724 delivered #722's batch.
The friction sweep stays parked pending its exact operator decision.
