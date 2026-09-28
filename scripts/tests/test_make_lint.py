"""What `make lint` hands ruff — observed by running it, not by reading it.

`lint` must lint the Python files git tracks and nothing else (#848): CI lints a
fresh checkout, so an untracked local script deciding whether `make test` can
reach pytest is a local-only failure CI never sees. Nothing else in the suite
executes the recipe, so reverting it to a bare `ruff check` left the whole suite
green (PR #850's panel measured that).

Each case runs the repo's real Makefile in a throwaway git repo with a stub
`uvx` first on PATH that records its argv, so no ruff is fetched and the
assertion is on what make actually invoked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root
from conftest import require_kit_source

REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))

STUB = """#!/bin/sh
for arg in "$@"; do printf '%s\\n' "$arg"; done >> "$UVX_LOG"
"""


def _lint(tmp_path: Path, tracked: list[str], untracked: list[str]):
    require_kit_source()
    makefile = REPO_ROOT / "Makefile"
    if not makefile.is_file() or not shutil.which("make") or not shutil.which("git"):
        pytest.skip("needs the kit's Makefile, make and git")

    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(makefile, repo / "Makefile")
    for name in tracked + untracked:
        (repo / name).write_text("x = 1\n", encoding="utf-8")

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    git = ["git", "-C", str(repo)]
    subprocess.run([*git, "init", "-q"], check=True, env=env)
    subprocess.run([*git, "add", "Makefile", *tracked], check=True, env=env)
    subprocess.run([*git, "commit", "-qm", "fixture"], check=True, env=env)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "uvx"
    stub.write_text(STUB, encoding="utf-8")
    stub.chmod(0o755)
    log = tmp_path / "uvx.log"
    env["UVX_LOG"] = str(log)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    proc = subprocess.run(
        ["make", "lint"], cwd=repo, env=env, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else None


def test_lint_passes_tracked_python_and_skips_untracked(tmp_path):
    argv = _lint(tmp_path, tracked=["kept.py"], untracked=["stray.py"])
    assert argv is not None, "make lint never invoked uvx"
    assert "kept.py" in argv, argv
    assert "stray.py" not in argv, f"an untracked file reached ruff: {argv}"
    # A bare `ruff check` with no paths walks the working tree, untracked
    # files included — the #848 behaviour. The tracked file being named is
    # what rules that form out; this rules out a `.` smuggled in beside it.
    assert "." not in argv, argv


def test_lint_with_no_tracked_python_does_not_run_ruff(tmp_path):
    # With no paths ruff defaults to `.`, so running it here would lint the
    # untracked file. BSD xargs already skips an empty input; GNU xargs does
    # not without `-r`, so on Linux this is what pins the flag.
    argv = _lint(tmp_path, tracked=[], untracked=["stray.py"])
    assert argv is None, f"ruff ran with no tracked Python files: {argv}"
