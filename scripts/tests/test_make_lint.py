"""What `make lint` hands ruff, and what `make check-syntax` and CI's "Check shell
syntax" step catch — observed by running them, not by reading them.

`lint` must lint the Python files git tracks and nothing else (#848): CI lints a
fresh checkout, so an untracked local script deciding whether `make test` can
reach pytest is a local-only failure CI never sees. Nothing else in the suite
executes the recipe, so reverting it to a bare `ruff check` left the whole suite
green (PR #850's panel measured that).

Each `lint` case runs the repo's real Makefile in a throwaway git repo with a
stub `uvx` first on PATH that records its argv, so no ruff is fetched and the
assertion is on what make actually invoked. The `check-syntax` cases (#561) are
described at their own section below.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
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


# --- check-syntax ------------------------------------------------------------
#
# `make check-syntax` and CI's "Check shell syntax" step must run `bash -n` once
# per listed script (#561): `bash -n a.sh b.sh` parses only `a.sh` and hands
# `b.sh` to it as a positional parameter, so a single call over the list exits 0
# with every file after the first broken. Both surfaces are executed here in a
# throwaway tree holding copies of the scripts they list, with the LAST listed
# script broken, so the single-call form passes and fails these tests. The
# lists are read out of the Makefile (through `make -n`) and the workflow
# (through PyYAML), not copied here, so the tests follow the files.

WORKFLOW = ".github/workflows/test.yml"
CI_STEP = "Check shell syntax"


def _listed(text: str, where: str) -> list[str]:
    """The scripts `text` checks with `bash -n`: every repo file it names but init.sh.

    Read off the names rather than off the loop's shape, so a revert to the single
    `bash -n a b c d` call still yields its list and the behavioural tests, not
    this parser, are what fail it. init.sh is left out because its own `sh -n`
    line checks it, so it is never the file a single `bash -n` call would skip.
    """
    names: list[str] = []
    for token in re.split(r"[\s;]+", text.replace("\\\n", " ")):
        token = token.strip("\"'")
        if token and token != "init.sh" and token not in names and (REPO_ROOT / token).is_file():
            names.append(token)
    assert len(names) > 1, f"{where} names fewer than two scripts: {names}\n{text}"
    return names


def _make_recipe() -> str:
    require_kit_source()
    if not (REPO_ROOT / "Makefile").is_file() or not shutil.which("make"):
        pytest.skip("needs the kit's Makefile and make")
    done = subprocess.run(
        ["make", "-n", "check-syntax"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout


def _ci_run() -> str:
    doc = yaml.safe_load((REPO_ROOT / WORKFLOW).read_text(encoding="utf-8"))
    steps = [
        step
        for job in (doc.get("jobs") or {}).values()
        for step in (job.get("steps") or [])
        if step.get("name") == CI_STEP
    ]
    assert len(steps) == 1, f"expected one {CI_STEP!r} step in {WORKFLOW}, got {len(steps)}"
    assert "shell" not in steps[0], "the step sets its own shell; update _run_ci_step"
    return steps[0]["run"]


def _tree(tmp_path: Path, scripts: list[str], break_last: bool) -> Path:
    tree = tmp_path / "tree"
    for name in [*scripts, "init.sh"]:
        dest = tree / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / name, dest)  # keeps the mode, so init.sh stays +x
    if break_last:
        (tree / scripts[-1]).write_text("if then fi (\n", encoding="utf-8")
    return tree


def _run_make(tmp_path: Path, break_last: bool):
    scripts = _listed(_make_recipe(), "the Makefile's check-syntax recipe")
    tree = _tree(tmp_path, scripts, break_last)
    shutil.copy(REPO_ROOT / "Makefile", tree / "Makefile")
    return scripts, subprocess.run(
        ["make", "check-syntax"], cwd=tree, capture_output=True, text=True, check=False
    )


def _run_ci_step(tmp_path: Path, break_last: bool):
    run = _ci_run()
    scripts = _listed(run, f"{WORKFLOW}'s {CI_STEP!r} step")
    tree = _tree(tmp_path, scripts, break_last)
    step = tmp_path / "step.sh"
    step.write_text(run, encoding="utf-8")
    # GitHub runs a `run:` with no `shell:` on Linux as `bash -e {0}`.
    return scripts, subprocess.run(
        ["bash", "-e", str(step)], cwd=tree, capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize(
    "runner",
    [
        pytest.param(_run_make, id="makefile"),
        pytest.param(_run_ci_step, id="ci", marks=pytest.mark.kit_repo_only(WORKFLOW)),
    ],
)
def test_check_syntax_fails_on_a_broken_script_after_the_first(tmp_path, runner):
    scripts, proc = runner(tmp_path, break_last=True)
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, f"a broken {scripts[-1]} passed:\n{out}"
    assert scripts[-1] in out, f"the failure does not name {scripts[-1]}:\n{out}"


@pytest.mark.parametrize(
    "runner",
    [
        pytest.param(_run_make, id="makefile"),
        pytest.param(_run_ci_step, id="ci", marks=pytest.mark.kit_repo_only(WORKFLOW)),
    ],
)
def test_check_syntax_passes_when_nothing_is_broken(tmp_path, runner):
    _, proc = runner(tmp_path, break_last=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.kit_repo_only(WORKFLOW)
def test_ci_and_the_makefile_check_the_same_scripts():
    make_list = _listed(_make_recipe(), "the Makefile's check-syntax recipe")
    ci_list = _listed(_ci_run(), f"{WORKFLOW}'s {CI_STEP!r} step")
    assert ci_list == make_list
