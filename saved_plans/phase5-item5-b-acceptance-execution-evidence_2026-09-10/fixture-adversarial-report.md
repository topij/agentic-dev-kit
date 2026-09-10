Reviewed `topij/adk-item5-b-field-20260909` PR #1 in the [handed tree](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/adversarial/handed-tree). Actual placed HEAD and reviewed SHA were both `f770f183bf6691f1f706c676b740cf2ef5ceb766`. The pinned diff contains **106 changed files, 83,335 insertions**. `git ls-remote` confirmed remote `main` remained at base `8533c334637e8776ca7a4fe3a9fd8c6c64e35707`.

Verification used a fresh [private clone](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/adversarial/mut-adversarial-f770f183-p3r4tuqp/repo), created with `git clone --no-hardlinks`. Initial sandbox DNS and verification-lock refusals were resolved by approved retries. Final `git status --short` was empty in both trees; all 114 tracked handed-tree file hashes were unchanged. I did not edit or repoint the handed tree. Status alone does not prove absence of repointing.

**P2 — The state-write guard misses creation of a regular file at the state root. Regression: no; inherited upstream gap.**

[scripts/devkit/conftest.py:234](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/adversarial/handed-tree/scripts/devkit/conftest.py:234) treats every non-directory `state` path as absent. Using unchanged reviewed guard bytes, a test that creates a regular file named `state` reports **1 passed, exit 0**, without the guard banner. The reviewed `pr_watch.save_state()` then raises `NotADirectoryError`. The directory-creation control correctly triggers the guard and exits 1.

Record the root’s kind/content and add a behavioral test for this case. The guard is byte-identical to pinned upstream `60fe0dc7…`; this demonstrates an inherited standalone-detector gap. The hosted workflow additionally checks Git cleanliness.

Verification on **2026-09-10 UTC**, through the required serial wrapper:

- Required `uv run --with pytest --with pyyaml python -B scripts/devkit/run_installed_tests.py --root <private-clone>`: **2,129 passed, 128 skipped; exit 0**.
- Source-manifest doctor, adapter comparison, document budgets, and separate shell syntax checks: **exit 0**.
- Focused controls before mutation and after restoration: **54 passed, 1 deselected; exit 0**.

| Deliberate mutation | Behavioral result |
|---|---|
| Symlink rejection condition → `False` | 2 failed, 5 passed; exit 1 |
| Missing-module rejection condition → `False` | 1 failed, 6 passed; exit 1 |
| State-content hash → constant | 6 overwrite-detection cases failed, 41 passed; exit 1 |

Every mutation run explicitly deselected the drift test and reported **1 deselected**. All three mutations were behaviorally killed. Their intended diffs were re-read before testing; original bytes and SHA-256 equality were verified after every restoration.

I did not write this code, apply fixes, spawn agents, or perform external writes. All verification processes terminated. The 128 skips remain verification limits; no local source-suite or live-client pass is claimed.

The [complete terminal report](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/adversarial/mut-adversarial-f770f183-p3r4tuqp/evidence/review-report.md) contains exact commands, cwd/revision/date records, raw results, mutation diffs, restoration hashes, and contract attestations.