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

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _repo_layout import engine_dir

TESTS_DIR = Path(__file__).resolve().parent
ENGINE_DIR = engine_dir(Path(__file__))


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


def test_a_directory_counts_as_present(tmp_path):
    """`docs/templates` is named as a directory by `test_kitconfig.py`, so the
    check has to be `exists()` rather than `is_file()`."""
    root = _tree(tmp_path, PROBE.format(paths='"docs/templates"'))
    (root / "docs" / "templates").mkdir(parents=True)
    out = _run(root)
    assert "1 passed" in out.stdout, out.stdout


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
    for module in sorted(TESTS_DIR.glob("test_*.py")):
        for call in re.finditer(r"kit_repo_only\(([^)]*)\)", module.read_text(encoding="utf-8")):
            found.update(re.findall(r'"([^"]+)"', call.group(1)))
    return found


def test_the_marker_scan_finds_something():
    """A non-vacuity control on `_marked_paths`. If the regex stopped matching —
    a marker written with single quotes, a rename — the check below would pass
    over an empty set and assert nothing, silently."""
    found = _marked_paths()
    assert "init.sh" in found, found
    assert len(found) >= 4, found


@pytest.mark.parametrize("path", sorted(_marked_paths()))
def test_every_path_this_repo_marks_actually_exists_here(path):
    """The kit's own repo must have every path its markers name, or those tests
    go quiet rather than red.

    This is a positive control on the marker set, not on the mechanism: it fails
    if someone marks a test with a path that never existed (a typo, a renamed
    file), which would skip that test in EVERY tree including this one — the
    failure mode the mechanism makes possible and nothing else would catch.

    It does not, and cannot, catch a kit file being deleted: the marker would
    then correctly report it absent, and this test would fail for the same
    reason the deletion caused. That is the stated limit in `conftest.py`.
    """
    assert (ENGINE_DIR.parent / path).exists(), (
        f"a kit_repo_only marker names {path!r}, which does not exist in the "
        "kit's own repo — every test carrying it will skip everywhere"
    )
