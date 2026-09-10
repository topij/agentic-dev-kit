# Phase 5 item 5 — approved kit test repair

Repair PR: [#726](https://github.com/topij/agentic-dev-kit/pull/726).

On 2026-09-10 the operator approved the kit-only slice proposed in the
[ITEM5-B execution record](phase5-item5-b-execution_2026-09-09.md). The standing
`merge when clean` instruction applies to this repair. It does not authorize an
update to the retained ITEM5-B fixture.

The repair separates initializer inputs from adopter-owned config and policy,
builds an explicit generated adapter corpus, and limits source-contract assertions
and their drift-liveness parent to kit source trees. Hostile config edits must change
the controlled input before the rejection test runs. Nested tests exercise improper
source skips, valid adopter skips, a stray baseline key and a declined renderer.
The real kit adapters and controlled inputs retain independent source assertions.
No production hook, review gate, adapter renderer or installation-baseline classifier
was changed. #534 stays open; typed decline reasons and #723 remain outside this slice.

## Verification

The [evidence](phase5-item5-kit534-repair-evidence_2026-09-10/verification.json) binds
commands, directories, immutable source/fixture revisions and output hashes on
2026-09-10. Full suites ran serially with separate external state directories.
The synthetic install uses `scripts/devkit/`, customized configuration, authored policy
and a custom Codex wrap-up adapter. Its setup driver is retained as historical evidence,
not a resume command. The setup result and `roots.json` retain the original captured
bytes, including the empty stdout from `--record-install`; its status text goes to
stderr. No retained field fixture was used as a write destination.
Suite logs retain terminal whitespace; their bytes are checked with the hash ledger
and excluded from authored-text whitespace checks.

- `make test` in `/Users/topi/Coding/agentic-dev-kit` at
  `85205bb491ce7ad09b7b3e3ab1e6c3027b19c363` printed
  `1 failed, 2493 passed, 1 skipped in 449.64s (0:07:29)`; the failure is the known
  #393 deep-JSON node, separate from the repaired test assumptions.
- `uv run --with pytest --with pyyaml python -B <fixture>/scripts/devkit/run_installed_tests.py --root <fixture>`
  in `/private/tmp/kit534-repair-20260910-3pWV3M/installed` at
  `0e04147a7dbeed332f8e589ac0dd0c7ea5b20bc9`, using source
  `85205bb491ce7ad09b7b3e3ab1e6c3027b19c363`, printed
  `2125 passed, 128 skipped in 428.71s (0:07:08)`.
- The subsequent renderer-dependency refinement is source
  `919a10b4f2ef45879011c9be5e4572e979623864`. At synthetic install
  `af217e63906d0c398474828ddf75770c9b8ba7db` in the same directory,
  `uv run --with pytest --with pyyaml python -B -m pytest scripts/devkit/tests/test_kit_repo_only.py -q`
  printed `19 passed, 49 skipped in 5.28s`. This is a focused refinement check;
  the complete installed run above belongs to its earlier pin.
- `make test` in `/private/tmp/kit534-repair-20260910-3pWV3M/source-919a10b`
  at `919a10b4f2ef45879011c9be5e4572e979623864` printed
  `1 failed, 2495 passed, 1 skipped in 419.85s (0:06:59)`, again the known #393 node.

These observations establish behavior in the named synthetic layouts. They do not
establish successful verification of retained ITEM5-B, client discovery/trust, fixture
PR lifecycle, or the untested systemize routes. Source-contract skips remain visible
in the complete installed result; no exclusion rerun is used as a full-suite pass.

## Maintained sprint and next action

Phase 5 item 5 remains incomplete. Item 6's cs-toolkit replay retains its recorded
completion and refs; #2222/#2223/#2255 are not repeated or re-credited. #585 remains
earlier, outside Phase 6. The accepted #723 deferral and delivered #722 batch in kit
#724 are unchanged. The [maintained sprint status](codex-parity-plan_2026-08-23.md#sprint-status--reconciled-2026-09-10)
remains the delivery authority.

**Next session:** prepare an exact ITEM5-B update decision packet against the merged
repair pin, including source/destination paths, proposed file writes and verification.
Recheck the retained inventory first. Do not update the fixture before that decision,
repeat its consumed setup, or reconstruct either original missing path.
