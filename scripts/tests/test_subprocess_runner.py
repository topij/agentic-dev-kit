"""lib/subprocess_runner.py: the shared runner's three entry points and its errors.

`run_stdout` raises for a non-zero exit; `run_result` and `run_bytes` return the
exit code with the output. All three share one timeout and start-failure path; the
kill test below exercises the timeout with a real child process rather than a stub.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))

from subprocess_runner import (  # noqa: E402
    CommandError,
    CommandFailed,
    CommandTimedOut,
    CommandUnavailable,
    Completed,
    run_bytes,
    run_result,
    run_stdout,
    without_git_environment,
)

SH = "/bin/sh"


def test_run_stdout_returns_stdout_verbatim() -> None:
    assert run_stdout([SH, "-c", "printf ' a\\n\\n'"], cwd=None, timeout=10) == " a\n\n"


def test_run_stdout_raises_a_failure_with_its_exit_code_and_stripped_stderr() -> None:
    with pytest.raises(CommandFailed) as caught:
        run_stdout([SH, "-c", "echo ' boom ' >&2; exit 3"], cwd=None, timeout=10)
    assert caught.value.returncode == 3
    assert caught.value.stderr == "boom"
    assert str(caught.value) == f"{SH} -c echo ' boom ' >&2; exit 3 failed (exit 3): boom"


def test_run_result_returns_a_non_zero_exit_instead_of_raising() -> None:
    done = run_result([SH, "-c", "cat; echo err >&2; exit 1"], cwd=None, timeout=10, stdin_text="in")
    assert done == Completed(returncode=1, stdout="in", stderr="err\n")


def test_run_result_honours_cwd_and_env(tmp_path: Path) -> None:
    done = run_result([SH, "-c", 'pwd -P; printf %s "$PROBE"'], cwd=tmp_path, timeout=10,
                      env={"PATH": os.environ["PATH"], "PROBE": "set"})
    assert done.returncode == 0
    assert done.stdout == f"{tmp_path.resolve()}\nset"


def test_run_result_keeps_the_exit_code_when_stderr_is_not_utf8() -> None:
    done = run_result([SH, "-c", "printf 'bad \\377' >&2; exit 1"], cwd=None, timeout=10)
    assert done == Completed(returncode=1, stdout="", stderr="bad \ufffd")


@pytest.mark.parametrize("entry", [run_stdout, run_result], ids=["stdout", "result"])
def test_text_stdout_that_is_not_utf8_is_a_command_error(entry) -> None:
    with pytest.raises(CommandError, match=r"wrote stdout that is not UTF-8 \(exit 0\); read it with run_bytes$"):
        entry([SH, "-c", "printf '\\377'"], cwd=None, timeout=10)


def test_a_failed_run_stdout_is_reported_before_its_stdout_is_read() -> None:
    with pytest.raises(CommandFailed, match=r"\(exit 2\): oops$"):
        run_stdout([SH, "-c", "printf '\\377'; echo oops >&2; exit 2"], cwd=None, timeout=10)


def test_text_output_translates_newlines_as_text_mode_did() -> None:
    done = run_result([SH, "-c", "printf 'a\\r\\nb\\rc\\n'; printf 'e\\r\\n' >&2"], cwd=None, timeout=10)
    assert (done.stdout, done.stderr) == ("a\nb\nc\n", "e\n")


@pytest.mark.parametrize("entry", [run_result, run_bytes], ids=["result", "bytes"])
def test_a_signal_exit_is_returned_as_a_negative_code(entry) -> None:
    assert entry([SH, "-c", "kill -9 $$"], cwd=None, timeout=10).returncode == -9


def test_run_stdout_raises_for_a_signal_exit() -> None:
    with pytest.raises(CommandFailed) as caught:
        run_stdout([SH, "-c", "kill -9 $$"], cwd=None, timeout=10)
    assert caught.value.returncode == -9


def test_run_bytes_round_trips_bytes_that_are_not_utf8() -> None:
    payload = b"\xff\x00\xfe raw\n"
    done = run_bytes([SH, "-c", "cat; printf '\\377' >&2"], cwd=None, timeout=10, stdin_bytes=payload)
    assert done.returncode == 0
    assert done.stdout == payload
    assert done.stderr == "�"


def test_run_bytes_returns_a_non_zero_exit_instead_of_raising() -> None:
    done = run_bytes([SH, "-c", "exit 128"], cwd=None, timeout=10)
    assert (done.returncode, done.stdout, done.stderr) == (128, b"", "")


@pytest.mark.parametrize("entry", [run_stdout, run_result, run_bytes], ids=["stdout", "result", "bytes"])
def test_a_command_that_cannot_start_is_unavailable(entry, tmp_path: Path) -> None:
    missing = str(tmp_path / "no-such-binary")
    with pytest.raises(CommandUnavailable, match=r"no-such-binary could not run: "):
        entry([missing], cwd=None, timeout=10)


@pytest.mark.parametrize("entry", [run_stdout, run_result, run_bytes], ids=["stdout", "result", "bytes"])
def test_a_command_past_its_timeout_is_killed_and_reaped(entry, tmp_path: Path) -> None:
    """The kill path, against a real child: it must be gone when the error is raised."""
    pidfile = tmp_path / "pid"
    started = time.monotonic()
    with pytest.raises(CommandTimedOut, match=r"timed out after 3s$") as caught:
        entry([SH, "-c", f"echo $$ > '{pidfile}'; exec sleep 30"], cwd=None, timeout=3)
    assert isinstance(caught.value, CommandError)
    assert time.monotonic() - started < 15
    pid = int(pidfile.read_text().strip())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_without_git_environment_drops_every_git_variable_only() -> None:
    source = {"GIT_DIR": "x", "GIT_CONFIG_COUNT": "1", "GITHUB_TOKEN": "t", "PATH": "/bin"}
    assert without_git_environment(source) == {"GITHUB_TOKEN": "t", "PATH": "/bin"}
