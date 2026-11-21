"""`archive_plan_sessions._recovery_hint`'s Git reads, through the shared runner.

The hint offers a `git show` command only when Git confirms a committed regular
file. These tests pin the runner's part: each read is bounded, runs without an
inherited ``GIT_*`` variable, and any failure gives the fallback, which offers no
command.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import time
from pathlib import Path
from types import ModuleType

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent
FALLBACK = "No committed Git version could be confirmed"


def _load_archive() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "archive_recovery_runner", ENGINE_DIR / "archive_plan_sessions.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)


def _committed_repo(root: Path, relative: str, text: str) -> Path:
    root.mkdir()
    _git(root, "init", "-q")
    document = root / relative
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(text)
    _git(root, "add", "--", relative)
    _git(root, "-c", "user.name=Archive fixture", "-c", "user.email=archive@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "-qm", "Synthetic baseline")
    return document


def _printed_command(hint: str) -> str:
    commands = [line[4:] for line in hint.splitlines() if line.startswith("    git ")]
    assert len(commands) == 1, hint
    return commands[0]


@pytest.mark.parametrize("variable", ["GIT_DIR", "GIT_INDEX_FILE"])
def test_an_inherited_git_variable_does_not_redirect_the_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str,
) -> None:
    archive = _load_archive()
    document = _committed_repo(tmp_path / "target", "docs/handoff.md", "Committed handoff.\n")
    other = _committed_repo(tmp_path / "other", "unrelated.md", "Unrelated.\n")
    value = str(other / ".git") if variable == "GIT_DIR" else str(other / ".git" / "index")
    monkeypatch.setenv(variable, value)

    hint = archive._recovery_hint(document)

    command = _printed_command(hint)
    shown = subprocess.run(
        ["sh", "-c", command], cwd=tmp_path, capture_output=True, check=False,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert shown.returncode == 0, shown.stderr
    assert shown.stdout == b"Committed handoff.\n"


def _fake_git(tmp_path: Path, body: str) -> Path:
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text("#!/bin/sh\n" + body)
    git.chmod(0o755)
    return bin_dir


@pytest.mark.parametrize("behaviour", ["hung", "failing", "missing"])
def test_a_git_that_does_not_answer_gives_the_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, behaviour: str,
) -> None:
    archive = _load_archive()
    document = _committed_repo(tmp_path / "target", "docs/handoff.md", "Committed handoff.\n")
    if behaviour == "hung":
        bin_dir = _fake_git(tmp_path, "exec /bin/sleep 30\n")
    elif behaviour == "failing":
        bin_dir = _fake_git(tmp_path, "echo 'fatal: synthetic' >&2\nexit 128\n")
    else:
        bin_dir = tmp_path / "empty-bin"
        bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setattr(archive, "GIT_TIMEOUT", 1)

    started = time.monotonic()
    hint = archive._recovery_hint(document)

    assert time.monotonic() - started < 4
    assert FALLBACK in hint
    assert not any(line.startswith("    git ") for line in hint.splitlines())


def test_each_read_uses_the_module_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _load_archive()
    document = _committed_repo(tmp_path / "target", "docs/handoff.md", "Committed handoff.\n")
    seen: list[tuple[str, int, dict[str, str] | None]] = []
    real = archive.run_stdout

    def record(argv: list[str], **kwargs: object) -> str:
        env = kwargs.get("env")
        seen.append((" ".join(argv), kwargs["timeout"], None if env is None else dict(env)))
        return real(argv, **kwargs)

    monkeypatch.setattr(archive, "run_stdout", record)
    monkeypatch.setattr(archive, "GIT_TIMEOUT", 7)
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))

    _printed_command(archive._recovery_hint(document))

    assert [cmd.split(" -C ", 1)[0] for cmd, _, _ in seen] == [
        "git", "git --literal-pathspecs", "git"]
    for _, timeout, env in seen:
        assert timeout == 7
        assert env is not None and env.get("GIT_NO_LAZY_FETCH") == "1"
        assert not {k for k in env if k.startswith("GIT_")} - {"GIT_NO_LAZY_FETCH"}

