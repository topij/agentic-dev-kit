"""What pins the `kit_repo_only` skip mechanism (`conftest.py`).

The mechanism exists because several test modules assert against files the kit
ships but an adopter need not vendor — `init.sh`, `docs/templates/*.tmpl`, the
panel doctrine. Before it, a sized-down adopter's first run of the suite the kit
tells them to run as post-install verification was 90 red, which trains an
adopter to ignore the suite and hides the failures that would be real (#134
cause 2).

These tests run pytest in a **subprocess against a synthetic tree**, not against
this repo. Asserting the mechanism from inside the repo where every path happens
to exist would only ever exercise the not-skipped branch — and "the marker fires
when a path is absent" is the whole behaviour.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root

TESTS_DIR = Path(__file__).resolve().parent
ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)


def _tree(tmp_path: Path, body: str) -> Path:
    """A minimal vendored tree: a `.git` marker, the real conftest, one module.

    The engines land at `scripts/devkit/` deliberately — the layout `/adopt`
    defaults to and the one that broke `parents[2]` — so this also covers the
    conftest resolving its own root by walk-up rather than by counting.
    """
    root = tmp_path / "adopter"
    vendored = root / "scripts" / "devkit" / "tests"
    vendored.mkdir(parents=True)
    (root / ".git").mkdir()
    for name in ("conftest.py", "_repo_layout.py"):
        shutil.copy(TESTS_DIR / name, vendored / name)
    (vendored / "test_probe.py").write_text(body, encoding="utf-8")
    return root


def _run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        # `-rs` renders skip REASONS. Without it the reason is computed and
        # discarded, so an assertion on it would pass vacuously against output
        # that never contained one.
        [sys.executable, "-m", "pytest", "scripts/devkit/tests", "-q", "--no-header", "-rs"],
        cwd=root,
        capture_output=True,
        text=True,
    )


PROBE = """
import pytest


@pytest.mark.kit_repo_only({paths})
def test_probe():
    assert True
"""


def test_a_marker_naming_an_absent_path_skips(tmp_path):
    root = _tree(tmp_path, PROBE.format(paths='"init.sh"'))
    out = _run(root)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1 skipped" in out.stdout, out.stdout
    # The reason names the path, so a reader of a skipped run can tell an
    # intentional omission from a broken install without reading this file.
    assert "init.sh" in out.stdout, out.stdout


def test_a_marker_naming_a_present_path_runs(tmp_path):
    """The other branch, and the one that matters for the kit's own repo: if the
    marker skipped unconditionally it would silently delete coverage here while
    every suite still reported green."""
    root = _tree(tmp_path, PROBE.format(paths='"init.sh"'))
    (root / "init.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    out = _run(root)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1 passed" in out.stdout, out.stdout
    assert "skipped" not in out.stdout, out.stdout


def test_one_absent_path_among_several_is_enough_to_skip(tmp_path):
    root = _tree(tmp_path, PROBE.format(paths='"init.sh", "Makefile"'))
    (root / "init.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    out = _run(root)
    assert "1 skipped" in out.stdout, out.stdout
    reason = next(ln for ln in out.stdout.splitlines() if "not vendored" in ln)
    assert "Makefile" in reason, reason
    # Only the genuinely missing one is named — a reason listing a file the tree
    # has would send an adopter looking for a problem they do not have.
    assert "init.sh" not in reason, reason


def test_a_function_marker_adds_to_a_module_marker_rather_than_replacing_it(tmp_path):
    """`get_closest_marker` returns only the nearest, so a function-level marker
    silently dropped the module's requirement — `test_init_sh.py`'s six seeding
    tests need `docs/templates` on top of the module's `init.sh`, and with the
    closest-marker form they ran in a tree with no `init.sh`.

    Fixed in round 1 by unioning `iter_markers`, and pinned here in round 2:
    reverting to `get_closest_marker` left the whole suite green, because the
    only real instance has both paths present in the kit's own repo either way.
    Adversarial lens, PR #232 round 2.
    """
    body = (
        "import pytest\n\n"
        'pytestmark = pytest.mark.kit_repo_only("init.sh")\n\n\n'
        '@pytest.mark.kit_repo_only("docs/templates")\n'
        "def test_probe():\n    assert True\n"
    )
    root = _tree(tmp_path, body)
    # The FUNCTION's path is present and the MODULE's is not: under
    # `get_closest_marker` this runs, under the union it skips.
    (root / "docs" / "templates").mkdir(parents=True)
    out = _run(root)
    assert "1 skipped" in out.stdout, out.stdout
    reason = next(ln for ln in out.stdout.splitlines() if "not vendored" in ln)
    assert "init.sh" in reason, reason


def test_a_directory_counts_as_present(tmp_path):
    """`docs/templates` is named as a directory by `test_kitconfig.py`, so the
    check has to be `exists()` rather than `is_file()`."""
    root = _tree(tmp_path, PROBE.format(paths='"docs/templates"'))
    (root / "docs" / "templates").mkdir(parents=True)
    out = _run(root)
    assert "1 passed" in out.stdout, out.stdout


def test_an_unresolved_root_says_so_rather_than_claiming_certainty(tmp_path):
    """With no `.git` the root is a guess, and the skip must not pretend
    otherwise. Three rounds of guessing at it were withdrawn (see `conftest.py`);
    what ships states what was searched and points at #233.

    The reason text is the whole behaviour here — a skip that reads identically
    to a resolved-root one is the confident false claim the withdrawals were
    about.
    """
    root = tmp_path / "adopter"
    vendored = root / "scripts" / "tests"
    vendored.mkdir(parents=True)
    for name in ("conftest.py", "_repo_layout.py"):
        shutil.copy(TESTS_DIR / name, vendored / name)
    (vendored / "test_probe.py").write_text(PROBE.format(paths='"init.sh"'), encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "scripts/tests", "-q", "--no-header", "-rs"],
        cwd=root, capture_output=True, text=True,
    )
    assert "1 skipped" in out.stdout, out.stdout
    reason = next(ln for ln in out.stdout.splitlines() if "not vendored" in ln)
    assert "repo root unresolved" in reason, reason
    assert "#233" in reason, reason


def test_a_resolved_root_does_not_carry_the_unresolved_note(tmp_path):
    """The other side: with `.git` present the root is known, so the caveat must
    be absent — a caveat on every skip would be noise that stops being read."""
    root = _tree(tmp_path, PROBE.format(paths='"init.sh"'))
    out = _run(root)
    reason = next(ln for ln in out.stdout.splitlines() if "not vendored" in ln)
    assert "repo root unresolved" not in reason, reason


def test_the_completeness_guard_rejects_a_tree_missing_an_untracked_kit_file(tmp_path):
    """`kit-manifest.json` tracks the root `Makefile` in no version, so
    manifest-completeness alone said True for a tree missing one — and the
    positive control then ran and FAILED over a legitimately absent file, which
    is round 1's HIGH narrowed rather than closed. Adversarial lens, round 2.

    `init.sh` USED to be the second such file and is named that way in this
    test's history; it has been manifest-tracked since #360, so completeness
    alone would now catch it. The guard still checks it explicitly and this test
    still passes, because the synthetic manifest below lists neither — which is
    the point: the guard must not depend on a given file being in the manifest.
    Do not "simplify" it back to a manifest-only check on the strength of #360.
    """
    root = tmp_path / "kitish"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "engine.py").write_text("x = 1\n", encoding="utf-8")
    (root / "kit-manifest.json").write_text(
        json.dumps({"files": {"scripts/engine.py": {"sha256": "0" * 64}}}), encoding="utf-8"
    )
    (root / "Makefile").write_text("test:\n", encoding="utf-8")
    assert _is_complete_kit_tree(root) is False, "manifest-complete but no init.sh"
    (root / "init.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    assert _is_complete_kit_tree(root) is True


@pytest.mark.parametrize(
    "body",
    [
        "[1, 2, 3]",
        '"a string"',
        "null",
        "{garbage not json",
        '{"files": []}',
        # Truthy but not a dict — the only shape that reaches, and therefore
        # pins, the `isinstance(files, dict)` guard. Without it `for rel in
        # files` iterates the LIST's elements as manifest keys, and real path
        # strings there would yield a confident wrong verdict rather than a
        # rejection. Adversarial lens, PR #232 round 3.
        '{"files": ["init.sh", "Makefile"]}',
    ],
)
def test_a_manifest_of_any_shape_degrades_rather_than_aborting(tmp_path, body):
    """This predicate feeds a `skipif`, so it runs at MODULE scope — anything it
    raises aborts collection and runs zero tests, which is exactly #226. Every
    malformed shape must return False, never raise."""
    root = tmp_path / "tree"
    root.mkdir()
    (root / "kit-manifest.json").write_text(body, encoding="utf-8")
    assert _is_complete_kit_tree(root) is False


def test_an_unmarked_test_is_untouched(tmp_path):
    root = _tree(tmp_path, "def test_probe():\n    assert True\n")
    out = _run(root)
    assert "1 passed" in out.stdout, out.stdout
    assert "skipped" not in out.stdout, out.stdout


def test_the_marker_is_registered_so_m_expressions_do_not_warn(tmp_path):
    """An unregistered mark still *matches* under `-m`, so the selection would
    work — it would just warn on every run. A warning attached to a command a
    reviewer is told to trust is what gets the command dropped."""
    root = _tree(tmp_path, PROBE.format(paths='"init.sh"'))
    out = _run(root)
    assert "PytestUnknownMarkWarning" not in out.stdout + out.stderr


def _marked_paths() -> set[str]:
    """Every path named by a `kit_repo_only` marker anywhere in this suite.

    DERIVED by scanning the modules rather than restated as a list, for the same
    reason `kit_doctor._derive_engine_names` is derived: a hand-kept copy goes
    stale exactly when someone adds a marker, which is the moment the check
    below needed to know about it.
    """
    found: set[str] = set()
    pattern = re.compile(r"(?:kit_repo_only|require_kit_paths)\(([^)]*)\)")
    for module in sorted(TESTS_DIR.glob("test_*.py")):
        for call in pattern.finditer(module.read_text(encoding="utf-8")):
            found.update(re.findall(r'"([^"]+)"', call.group(1)))
    return found


def _is_complete_kit_tree(root: Path = None) -> bool:
    """Whether this tree holds every file `kit-manifest.json` says the kit ships.

    The scope guard the check below needs, and DERIVED rather than a judgement
    about "is this the kit's own repo" — which would be a bound the author sets.
    True in the kit's checkout and in a full vendor that kept `scripts/`; false
    in any sized-down tree, where a marked path being absent is the mechanism
    working rather than a defect.
    """
    root = REPO_ROOT if root is None else root
    manifest = root / "kit-manifest.json"
    if not manifest.is_file():
        return False
    try:
        parsed = json.loads(manifest.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        # ValueError, not JSONDecodeError: invalid UTF-8 bytes raise
        # UnicodeDecodeError, which is a ValueError and was NOT caught — so a
        # manifest with one stray byte aborted collection at module scope, since
        # this feeds a `skipif`. #226's failure class inside the fix for #226,
        # and the round-2 claim that every malformed form was pinned was false:
        # `write_text` on a `str` can only ever emit valid UTF-8, so the
        # parametrized cases structurally could not reach it. Adversarial lens,
        # PR #232 round 3.
        return False
    # `[1, 2, 3]` is valid JSON. Calling `.get` on it raised `AttributeError`
    # here — at MODULE scope, since this feeds a `skipif` — so collection
    # aborted and the whole session ran zero tests. That is #226's failure class
    # reproduced inside the fix for it. Correctness lens, PR #232 round 2.
    if not isinstance(parsed, dict):
        return False
    files = parsed.get("files")
    if not isinstance(files, dict):
        return False
    if not files or not all((root / rel).exists() for rel in files):
        return False
    # The manifest tracks neither of these, so a manifest-complete tree could
    # still be missing one — and then the control below would run and FAIL over
    # a legitimately absent file, which is the round-1 defect narrowed rather
    # than closed. Adversarial lens, PR #232 round 2.
    return all((root / rel).exists() for rel in ("init.sh", "Makefile"))


def test_the_marker_scan_finds_something():
    """A non-vacuity control on `_marked_paths`. If the regex stopped matching —
    a marker written with single quotes, a rename — the check below would pass
    over an empty set and assert nothing, silently."""
    found = _marked_paths()
    assert "init.sh" in found, found
    assert len(found) >= 4, found


@pytest.mark.skipif(
    not _is_complete_kit_tree(),
    reason="not a complete kit tree — a marked path being absent here is the "
    "mechanism working, not a defect",
)
@pytest.mark.parametrize("path", sorted(_marked_paths()))
def test_every_path_a_marker_names_exists_in_a_complete_kit_tree(path):
    """A positive control on the marker SET, not on the mechanism.

    It fails if a marker names a path that is not there — a typo, a renamed
    file — which would otherwise skip that test in every tree, silently.

    **The scope guard is the point, and its absence was a HIGH finding.** With
    no guard this ran in every vendored tree and failed wherever a marked path
    was legitimately absent — which is the normal, designed state of a
    sized-down adoption. It turned the `/adopt` tree this PR exists to make
    clean into 4 failures. Adversarial lens, PR #232 round 1.

    It catches a DELETION too, loudly, contradicting an earlier version of this
    docstring that claimed it could not: the assertion does not know why a path
    is missing and fires either way. What it cannot do is tell the two apart.
    """
    assert (REPO_ROOT / path).exists(), (
        f"a kit_repo_only marker names {path!r}, which is absent from a tree "
        "that is otherwise a complete kit — every test carrying it will skip"
    )
