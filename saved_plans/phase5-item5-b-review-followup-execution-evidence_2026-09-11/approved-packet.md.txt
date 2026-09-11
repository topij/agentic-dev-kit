# ITEM5-B kit review follow-up decision

**Prepared, not approved.** ITEM5-B-KIT-REVIEW-01 applied its exact production payloads
and opened [kit PR #731](https://github.com/topij/agentic-dev-kit/pull/731) ready. Its
review is paused at the findings below. Execution approval did not authorize changes
outside that payload ledger, acceptance of a newly discovered limitation, or merge.
The operator requested autonomous continuation while going to sleep; that request
supplied no additional scope decision. Production bytes from REVIEW-01 remain unchanged.

## Complete review receipts before preparation

The full independent panel reviewed `b018a0544c44028c21399ad073ce8a3dee3bfd45` against
`f408039dc3a9b0d2e0e8d246c126af892839cee8` on 2026-09-10. The actual Codex rollouts
record `gpt-6-astra`, effort `high`, in each isolated reviewer. Their complete reports
were posted and read back before preparing this proposal:

- [Adversarial receipt](https://github.com/topij/agentic-dev-kit/pull/731#issuecomment-5624451599):
  **P2, inherited FIFO-root detector gap; not a regression.** Creating a FIFO at
  `<repo>/state` escapes the regular-file branch and directory traversal. The probe
  pytest exits successfully without the banner; the reviewed `pr_watch.save_state()`
  then raises `NotADirectoryError`. The reviewer reproduced this with base and reviewed
  guard bytes in flat/nested layouts. It is a persistence obstruction, not proof of
  bypassing the full hosted workflow or merge gate.
- [Correctness receipt](https://github.com/topij/agentic-dev-kit/pull/731#issuecomment-5624454595):
  **P3, coverage gap; no demonstrated production regression.** Removing the root-file
  branch's symlink exclusion survives the focused guard tests. This is not a claimed
  full-suite mutation survival. A negative behavioral test should pin the preserved boundary.

The [review evidence](phase5-item5-b-review-followup-evidence_2026-09-10/sha256.json)
retains full reports, commands, actual results, mutation diffs and restoration records.
`make test` in each report's private clone at `b018a0544c44028c21399ad073ce8a3dee3bfd45` on
2026-09-10 reached pytest's terminal summary with the disclosed #393 failure. Separate
shell parses covered #561's omissions. The linked reports carry their exact directories
and actual summaries. Hosted run `34519875043`, toolkit job `103014822984`, succeeded
at that same head: `gh run view 34519875043 --repo topij/agentic-dev-kit --job 103014822984 --log`,
read from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-10, retained
`2502 passed, 3 skipped in 255.21s (0:04:15)` and the no-PyYAML result
`92 passed, 2 skipped in 2.48s`. Hosted success does not dispose of the findings.

## ITEM5-B-KIT-REVIEW-02 — proposed disposition and exact writes

This proposal asks the operator to **accept the documented inherited special-file-root
limitation for this regular-file repair**, without claiming it is fixed. A FIFO can
obstruct engine state persistence while remaining invisible to this guard. Special-file
descendants, root symlinks and the observation window are distinct cases. Any future
functional extension must be proposed separately and must not open special nodes.

The proposed implementation is the reviewer's bounded documentation remedy and missing
compatibility test. It adds no special-node detection, traversal, retry or recovery logic.
The [reviewable patch](phase5-item5-b-review-followup-proposal_2026-09-10/proposed.patch.txt)
has SHA-256 `c46f4ad0b142a26314d179b434764d98d2f8aee25cc2618d59476f1ae31b2c74`. The
[write ledger](phase5-item5-b-review-followup-proposal_2026-09-10/write-ledger.json)
binds complete payloads and destination modes:

| Destination under `/Users/topi/Coding/agentic-dev-kit` | Before SHA-256 | Proposed SHA-256 |
|---|---|---|
| `scripts/conftest.py` | `a0a82682c9431205f8c0db80176694b37800da7964e5b77ec3eba283fc7569c2` | `ecebbbc42cd6a8960e187abda41c5917e39aa1623b438ad932c7102cdf3ab03c` |
| `scripts/tests/test_state_guard.py` | `8e7a7082fa4e7fcaa0ccf1985be646c7b26bb86af4cc519349cc068861b6b291` | `9420de32bcba5232f13e9d8258de6f5c08ccb0a398513ff83e01cd731f377613` |
| `kit-manifest.json` | `4697b0e14dfa85ba86797aef85788d1ce2edb0a7001a9c6a1057109775cbad96` | `6c701b78f79f36b171d5df67a18317d04f9b734aff489bc6a00d70455f511160` |

- `scripts/conftest.py`: add the root-special-file limitation to the docstring.
  `python3 -B /private/tmp/item5-b-kit-repair-1kc2i4t2/record02.py`, run from the cockpit
  at `b018a0544c44028c21399ad073ce8a3dee3bfd45` on 2026-09-10, found identical ASTs
  after removing docstrings from the candidate and reviewed guard. This is not
  acceptance of the limitation.
- `scripts/tests/test_state_guard.py`: add nested-pytest cases for creation of a root
  symlink to a regular file and modification of an existing link's target, in the
  declared layouts. Assert actual link/target state, successful inner exit and absence
  of the guard banner. The existing regular-file detection tests remain.
- `kit-manifest.json`: apply the deterministically generated release hashes for those
  files. The retained fixture install baseline is excluded.

`CHANGELOG.md` retains the already-applied #731 entry and SHA-256
`206a09f89f48039008d5949c293bc058602ea0404ab9ae1d69fba4a4b2380ee1`. This proposal changes documentation and tests,
not adopter-visible guard behavior, so it adds no new changelog entry.

Approval would authorize these exact kit destinations, scoped records, commits and
pushes on the existing repair branch, continued ready PR #731 verification/review, and
the stated limitation acceptance. It would **not** authorize repair merge. Read back
the current branch/head and preserve intervening work; do not create a duplicate PR.
Revalidate each destination's before hash and mode immediately before writing.
Any mismatch or necessary payload change requires an amended packet.

**Excluded:** functional special-file detection, retained fixture/source writes,
baseline refresh, initialization, adapter refresh, client/trust/profile changes,
tracker payloads, fixture settings changes, fixture PR closure or merge. UPDATE-01
is consumed. A delivered repair still needs a new exact retained-update decision.

The excluded retained roots are `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/fixture`
and `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source`.
Revalidation must compare with the post-acceptance fixture checkpoint at
`f770f183bf6691f1f706c676b740cf2ef5ceb766`, detached source
`60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`, and baseline SHA-256
`9e2196df3b7239b599819abcfc20271b0389b70f78f22837a0709575145b9126`.
The historical UPDATE FINAL equality audit is not a current fixture check after PR-01.
Check the original temporary paths from the acceptance record without reconstructing them.

## Preparation verification and execution gate

Preparation ran in `/private/tmp/item5-b-kit-repair-1kc2i4t2/proposal02/repo`, detached
at `b018a0544c44028c21399ad073ce8a3dee3bfd45`, on 2026-09-10, with recorded candidate overlays,
optimization unset and new isolated cache/state paths. The [hash index](phase5-item5-b-review-followup-proposal_2026-09-10/sha256.json)
binds argv, timestamps, raw stdout/stderr, payloads and restoration:

- `uvx ruff@0.16.0 check --no-fix scripts/conftest.py scripts/tests/test_state_guard.py`
  exited successfully.
- `uv run --with pytest --with pyyaml python -B -m pytest scripts/tests/test_state_guard.py::test_guard_leaves_root_file_symlinks_outside_snapshot -q`
  printed `4 passed in 0.92s` with the candidate and `4 failed in 0.93s` after removing
  `not state_dir.is_symlink() and` from the regular-file branch. Failures were inner
  process-exit assertions after the actual link/target changes, not manifest drift.
  The landed mutation diff was retained and candidate bytes were restored and rehashed.
- `uv run --with pytest --with pyyaml python -B -m pytest scripts/tests/test_state_guard.py scripts/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean -q`
  printed `58 passed in 12.63s`. The manifest self-check was included without deselection.
- `uv run --with pyyaml python -B <absolute candidate>/scripts/kit_doctor.py --root <absolute candidate> --generate-manifest`
  generated the proposed manifest; its recorded repeat preserved identical bytes.

These focused preparation runs are not full candidate verification or independent
review of the proposal. After approval, bind absolute `KIT`, `REPO` and retained source
paths; assert the owning `pwd` before writes; save each original destination's bytes,
hash and mode; apply only the ledger; verify hashes at their intended destinations;
regenerate the release manifest and require the supplied bytes. Run the manifest
self-check without deselecting driftcheck and run `make test` to terminal completion
at the actual attempt revision. Read pytest's actual summary. Keep #393's exact failure
separate; a different failure, missing summary or unexpected write stops for assessment.
Run separate `bash -n` for `scripts/dev_session.sh`, `scripts/reconcile_sessions.sh`,
`scripts/lib/repo_root.sh`, `scripts/hooks/pre-push`, and `sh -n init.sh` for #561.
Serialize checkout/test/staging operations, inspect the named staged diff before a
separate commit, and complete a fresh full independent panel and hosted CI at the new
head. Record complete review receipts before fixes. Hold that reviewed head for an
operator merge decision; no existing receipt automatically covers the new head.

For local undo, first require every affected destination still equals the recorded
attempt, then restore only its saved original bytes/mode. Preserve branch, commits and
evidence. Intervening work stops undo. No broad reset/clean, historical rollback,
remote deletion or PR closure is authorized.

## Exact approval question

**Approve ITEM5-B-KIT-REVIEW-02 as scoped: accept and document the inherited
special-file-root limitation for this regular-file repair, apply the hash-bound
root-symlink compatibility tests and release manifest, run required verification and
complete ready PR #731 through independent review, holding its reviewed head for an
operator merge decision and leaving retained trees, baseline, clients, trackers and
fixture PR merge untouched?**

If that limitation is unacceptable, leave this proposal unapproved and request a
separate functional repair packet. Phase 5 item 5 remains incomplete under either
choice; item 6's completed replay and the systemize field-exit gaps are preserved.
