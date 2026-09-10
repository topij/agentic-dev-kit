Reviewed `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/handed-tree`.

Actual placed HEAD and reviewed SHA both: `f770f183bf6691f1f706c676b740cf2ef5ceb766`. The pinned `git diff --stat 8533c334637e8776ca7a4fe3a9fd8c6c64e35707...f770f183bf6691f1f706c676b740cf2ef5ceb766` showed **106 files changed, 83,335 insertions**. `git ls-remote origin HEAD refs/heads/main refs/heads/chore/item5-b-field-exit` confirmed the supplied base remained remote `main`, and the branch matched the reviewed SHA.

Scratch clone: sibling `mut-correctness-f770f183-tpxjgm_w/repo`, created fresh with `git clone --no-hardlinks`. Sandboxed remote access and verification-lock access initially failed; expanded-permission retries succeeded. No automatic approval rejection occurred. Final `git status --short` and tracked diffs were empty in both trees; HEADs remained unchanged.

**One finding: P3 / low — “byte-identical” overstates the adapter comparison. Classification: imprecision.**

[upgrade.md:159](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/handed-tree/docs/agentic-dev-kit/workflows/upgrade.md:159) defines `kit-current` as byte-identical. The comparator uses `Path.read_text()`, which normalizes line endings before comparison. The wrapped `python3 -B …/mutation_cases.py` probe produced **16 `kit-current` classifications despite 16 unequal byte comparisons** using CRLF copies.

Qualify the claim as newline-normalized text equality, or enforce byte equality. No behavioral regression was demonstrated; the probe preserves the Markdown instructions.

**Verification completed on 2026-09-10**, using the required `serial-verify.py` wrapper and private-clone cwd:

| Command/check | Terminal result |
|---|---|
| Supplied `uv run --with pytest --with pyyaml python -B scripts/devkit/run_installed_tests.py --root <private-copy>` | **2,129 passed, 128 skipped**, exit 0 |
| Installed `kit_doctor.py --manifest <retained-source>/kit-manifest.json --json` | 67 unchanged files; exit 0 |
| Source `kit_doctor.py --adapter-report --adapter-source …` | 15 current, fixture wrap-up adopter-owned; exit 0 |
| `python3 -B scripts/devkit/check_doc_budget.py` | Within budgets; exit 0 |

The local tests used Python 3.14.7, pytest 9.1.1 and PyYAML 6.0.3. The skipped source-only checks and GitHub Actions were not verified as passing. The doctor reported Git hooks not installed in the private clone.

**Mutation-test new branches:** both mutations were applied, re-read and diffed against saved `git show <reviewed-sha>:scripts/devkit/run_installed_tests.py` bytes before testing:

```diff
-            if current.is_symlink():
+            if False and current.is_symlink():
```

The leaf-symlink and symlinked-ancestor refusal tests failed: **2 failed, 5 passed, 1 deselected**, exit 1.

```diff
         if not candidate.is_file():
+            continue
```

The declared-missing-module refusal test failed: **1 failed, 6 passed, 1 deselected**, exit 1.

Both used targeted `uv run … python -B -m pytest <explicit-nodeids> -q -m 'not driftcheck'`. Exactly one drift test was deselected. Original bytes were restored and equality asserted after **each** mutation; restored SHA-256 was `4385056907334efbd44d7f67db3e10a302cf68433a18c666166b6b4d60c05235`. Controls before and after passed **7 tests, 1 deselected**, exit 0.

For **Fresh context**, **Not the author**, **Report, don't fix**, and **No writes in the tree you were given**: I reviewed independently, started no agents, and changed only private mutation fixtures and evidence. Status alone does not prove absence of repointing; no checkout, detach, reset or fetch was performed. All verification processes terminated. Manual inspection and mutation sampling were not exhaustive.

[Complete report with exact commands, dates, mutation diffs, raw results and restoration evidence](/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/review-report.md).