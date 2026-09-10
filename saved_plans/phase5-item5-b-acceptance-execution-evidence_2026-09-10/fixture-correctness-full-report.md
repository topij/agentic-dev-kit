Reviewed repository: `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/handed-tree` — `topij/adk-item5-b-field-20260909`, PR #1. Actual placed HEAD from `git rev-parse HEAD`: `f770f183bf6691f1f706c676b740cf2ef5ceb766`. Reviewed SHA: `f770f183bf6691f1f706c676b740cf2ef5ceb766`. `git diff --stat 8533c334637e8776ca7a4fe3a9fd8c6c64e35707...f770f183bf6691f1f706c676b740cf2ef5ceb766` established a nonempty diff: **106 files changed, 83,335 insertions**. The full pinned diff is retained in [initial-4.log](initial-4.log), and the diffstat in [initial-3.log](initial-3.log).

**Right revision:** `git remote -v` identified the expected GitHub repository. `git ls-remote origin HEAD refs/heads/main refs/heads/chore/item5-b-field-exit` returned `8533c334637e8776ca7a4fe3a9fd8c6c64e35707` for remote HEAD and main, and `f770f183bf6691f1f706c676b740cf2ef5ceb766` for the PR branch. This established that the supplied base was current during this review; local ancestry was not used as a substitute. [Raw remote output](remote-refs.log).

Private clone: `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo`, created with `git clone --no-hardlinks /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/handed-tree /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo` at a fresh lens-and-revision namespace. The default sandbox allowed the clone and local reads. It blocked the initial remote query with DNS failure, and the required verification wrapper with a PermissionError opening `review-state/verification.lock`. Expanded-permission retries succeeded; there was no automatic approval-review rejection. [Routes](routes.json), [clone output](clone.log), [initial failed wrapper attempt](baseline.log).

**Attestation:** final `git --no-optional-locks status --short` output is empty for both the handed tree and private clone. Both HEADs remain the reviewed SHA; `git diff --exit-code f770f183bf6691f1f706c676b740cf2ef5ceb766 --` is empty and exits 0 in both. [Final command output and assertions](final-attestation.json). No handed-tree edit, checkout, detach, reset, or fetch was performed. Empty status establishes absence of visible working-tree changes and untracked scratch; it does not independently establish that a checkout was never repointed.

**Finding — P3 / low: qualify the byte-identity claim. Classification: imprecision.**

`docs/agentic-dev-kit/workflows/upgrade.md:159` defines `kit-current` as “byte-identical to the current rendered form.” `scripts/devkit/lib/runtime_adapters.py:364` reads the adopter file with `Path.read_text()`, which normalizes CRLF to LF before the equality at line 370. The executed CRLF probe generated 16 adapters using the reviewed renderer, wrote CRLF adopter copies, and received **16 `kit-current` classifications with 16 unequal byte comparisons**. The claim overstates what this diagnostic establishes. Describe newline-normalized text equality, or enforce byte equality if that is the intended contract; pin the selected behavior with a line-ending case. This is documentation imprecision, with no behavioral regression demonstrated: the probe preserves the Markdown instruction text. Evidence: [probe output](adapter-newlines.json), [executed probe and mutation harness](mutation_cases.py), [terminal wrapper output](mutation-wrapper.log). No higher-severity finding was established in the examined surface.

**Execute, don't only read — terminal verification results.** Every behavioral/test command ran through the required serial wrapper, with private-clone cwd and isolated caches/state, on **2026-09-10**, at the reviewed SHA except the two explicitly recorded mutants. The exact wrapper prefix was:

```sh
python3 -B /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/review-state/serial-verify.py /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness --
```

The supplied installed-suite child command was:

```sh
uv run --with pytest --with pyyaml python -B scripts/devkit/run_installed_tests.py --root /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo
```

Result: **2,129 passed, 128 skipped**, exit **0**, 498.78 seconds. [Raw baseline output](baseline-escalated.log). The 128 skips include 50 checks for the absent source-kit `.github/workflows/test.yml`, 49 complete-source-tree marker checks, 16 source-only assertions, and 13 other source/fixture checks. These skipped tests were not verified as passing.

`python3 -B /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/mutation_cases.py` was the second wrapped child. It ran targeted controls, the two mutations below, byte restoration, and the CRLF probe. The unmutated controls before and after reported **7 passed, 1 deselected**, exit 0. [Before](targeted-baseline.log), [after restoration](targeted-restored.log). Each test invocation explicitly selected seven installed-runner tests and `test_kit_repo_self_check_is_clean`, then applied `-m 'not driftcheck'`. Exactly the drift test was deselected. Fully expanded test argv, cwd, date, and revision are retained at the beginning of each log and in the command appendix below.

**Mutation-test new branches — applied diffs and behavioral kills.** Original target bytes were saved using `git show f770f183bf6691f1f706c676b740cf2ef5ceb766:scripts/devkit/run_installed_tests.py` to [run_installed_tests.original.py](run_installed_tests.original.py). Each edit was re-read, asserted equal to the intended mutated bytes and different from the original, and diffed before pytest ran.

```diff
--- scripts/devkit/run_installed_tests.py@f770f183bf6691f1f706c676b740cf2ef5ceb766
+++ scripts/devkit/run_installed_tests.py (mutant)
@@ -55,7 +55,7 @@
         current = root
         for part in installed_rel.parts:
             current /= part
-            if current.is_symlink():
+            if False and current.is_symlink():
                 raise ValueError(
                     f"declared test path crosses a symlink after engine remapping: {rel}"
                 )
```

Result: **2 failed, 5 passed, 1 deselected**, exit 1. The failing tests were `test_installed_test_targets_refuse_declared_symlink` and `test_installed_test_targets_refuse_declared_symlinked_ancestor`; both failed because the expected `ValueError` was absent. These are behavioral refusals, not checksum or stored-text comparisons. [Raw output](symlink-guard-disabled.log).

```diff
--- scripts/devkit/run_installed_tests.py@f770f183bf6691f1f706c676b740cf2ef5ceb766
+++ scripts/devkit/run_installed_tests.py (mutant)
@@ -60,6 +60,7 @@
                     f"declared test path crosses a symlink after engine remapping: {rel}"
                 )
         if not candidate.is_file():
+            continue
             raise ValueError(
                 f"declared test module is missing or not regular after engine remapping: {rel}"
             )
```

Result: **1 failed, 6 passed, 1 deselected**, exit 1. `test_installed_test_targets_and_main_refuse_a_declared_missing_module` failed because an absent declared module no longer raised `ValueError`. [Raw output](missing-module-silently-skipped.log).

After each case, the original bytes were restored, re-read and asserted equal before the next case. Both restoration records show identical original/restored SHA-256: `4385056907334efbd44d7f67db3e10a302cf68433a18c666166b6b4d60c05235`. [First restoration](symlink-guard-disabled-restoration.json), [second restoration](missing-module-silently-skipped-restoration.json). No manifest was regenerated. Both kills came from behavioral assertions with the drift check excluded. This is sampled branch coverage, not exhaustive mutation coverage of the added kit.

**Verified clean — additional measured scope.** The third wrapped child, `python3 -B /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/installed_checks.py`, executed the exact commands recorded below. All four child commands exited 0:

- Version probe: Python **3.14.7**, pytest **9.1.1**, PyYAML **6.0.3**. [Output](versions.log).
- Installed `kit_doctor.py --root ... --manifest <retained-source>/kit-manifest.json --json`: file states `{'unchanged': 67}`. Its other diagnostics include `hooks_installed: false`; this clone's successful hash report is not proof of live Git-hook installation. [Output](installed-doctor.log).
- Retained-source `kit_doctor.py --adapter-report --adapter-source ... --root ... --json`: `{'kit-current': 15, 'adopter-owned': 1}`. The fixture-owned Codex wrap-up skill was classified `adopter-owned`. [Output](adapter-report.log).
- `python3 -B scripts/devkit/check_doc_budget.py`: ROADMAP.md **2/400** lines; notes/friction.md **31/150**. [Output](doc-budget.log).

The retained source was read-only. `git -C /Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source rev-parse HEAD` returned `60fe0dc7ad68922d064c0cf401cff2c4c6d607ac`; its `git status --short` was empty.

**Scope and contract attestation.** For **Fresh context**, **No framing**, and **Not the author**, I reviewed independently, did not write the submitted code, read the pinned raw diff without author summaries, and started no other agent. Manual examination concentrated on the installed runner, adapter comparator, upgrade claims, CI workflow, registrations, and related tests/conftests. The full installed suite exercised the other installed test modules. Manual inspection and mutation sampling were not exhaustive. This local execution used Python 3.14.7; the workflow specifies Python 3.12. GitHub Actions, live clients, forge writes, and the source kit's separate `make test` were not executed by this lens.

**Report, don't fix**, **No writes in the tree you were given**, and **Scratch namespace** were honored: writes stayed in the fresh private clone and adjacent evidence, and the original bytes were restored. No scratch path was removed or recreated; no submitted policy, retained baseline, profile, historical evidence or hook trust was edited. **Severity and regression** is stated for the finding; **Report what you reviewed, first** is satisfied by the opening evidence. All my verification processes reached terminal results; none was killed or left running. The initial sandboxed wrapper failed before tests, and its output is retained rather than described as a test failure.

**Exact child commands.** The following commands all ran beneath the wrapper prefix above, cwd `/Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo`. The script harnesses and wrapper logs retain the nesting and isolated environment.

targeted-baseline, 2026-09-10T17:17:43.569254+00:00:

```sh
uv run --with pytest --with pyyaml python -B -m pytest scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_use_manifest_not_directory_contents scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_invokes_pytest_and_propagates_failure scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_reports_a_successful_empty_suite scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_and_main_refuse_a_declared_missing_module scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_skip_a_declined_missing_test_root scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlink scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlinked_ancestor scripts/devkit/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean -q -m 'not driftcheck'
```

symlink-guard-disabled, 2026-09-10T17:17:49.124161+00:00:

```sh
uv run --with pytest --with pyyaml python -B -m pytest scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_use_manifest_not_directory_contents scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_invokes_pytest_and_propagates_failure scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_reports_a_successful_empty_suite scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_and_main_refuse_a_declared_missing_module scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_skip_a_declined_missing_test_root scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlink scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlinked_ancestor scripts/devkit/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean -q -m 'not driftcheck'
```

missing-module-silently-skipped, 2026-09-10T17:17:49.752143+00:00:

```sh
uv run --with pytest --with pyyaml python -B -m pytest scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_use_manifest_not_directory_contents scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_invokes_pytest_and_propagates_failure scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_reports_a_successful_empty_suite scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_and_main_refuse_a_declared_missing_module scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_skip_a_declined_missing_test_root scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlink scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlinked_ancestor scripts/devkit/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean -q -m 'not driftcheck'
```

targeted-restored, 2026-09-10T17:17:50.335621+00:00:

```sh
uv run --with pytest --with pyyaml python -B -m pytest scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_use_manifest_not_directory_contents scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_invokes_pytest_and_propagates_failure scripts/devkit/tests/test_kit_doctor.py::test_installed_test_main_reports_a_successful_empty_suite scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_and_main_refuse_a_declared_missing_module scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_skip_a_declined_missing_test_root scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlink scripts/devkit/tests/test_kit_doctor.py::test_installed_test_targets_refuse_declared_symlinked_ancestor scripts/devkit/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean -q -m 'not driftcheck'
```

versions, 2026-09-10T17:17:50.896546+00:00:

```sh
uv run --with pytest --with pyyaml python -B -c 'import sys,pytest,yaml; print(sys.version); print("pytest",pytest.__version__); print("pyyaml",yaml.__version__)'
```

installed-doctor, 2026-09-10T17:17:51.153120+00:00:

```sh
python3 -B scripts/devkit/kit_doctor.py --root /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo --manifest /Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source/kit-manifest.json --json
```

adapter-report, 2026-09-10T17:17:51.234313+00:00:

```sh
python3 -B /Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source/scripts/kit_doctor.py --root /Users/topi/Coding/adk-field-exercises/item5-b-20260909/acceptance-pr-20260910/reviews/f770f183bf6691f1f706c676b740cf2ef5ceb766/correctness/mut-correctness-f770f183-tpxjgm_w/repo --adapter-report --adapter-source /Users/topi/Coding/adk-field-exercises/item5-b-20260909/kit-source --json
```

doc-budget, 2026-09-10T17:17:51.301144+00:00:

```sh
python3 -B scripts/devkit/check_doc_budget.py
```
