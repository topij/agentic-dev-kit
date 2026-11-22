"""Run a command with a timeout and translate failures for engine CLI callers.

``run_stdout`` returns text stdout and raises for a non-zero exit. ``run_result``
(text) and ``run_bytes`` (bytes) return the exit code with the output instead, for
a caller whose answer is the exit code or whose content is bytes.

Every failure is a ``CommandError`` (a ``RuntimeError``), so a caller that only
needs "it did not work" catches one type. A caller that must treat the cases
differently catches the subclass: ``CommandTimedOut``, ``CommandUnavailable``
(the process could not start) or ``CommandFailed`` (it ran and exited non-zero;
raised by ``run_stdout`` only). Text is UTF-8: stderr is decoded with replacement, and
text-mode stdout that is not UTF-8 raises the base ``CommandError``.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class CommandError(RuntimeError):
    """A command did not produce its output."""


class CommandTimedOut(CommandError):
    """The command ran past its timeout and was killed."""


class CommandUnavailable(CommandError):
    """The command could not be started."""


class CommandFailed(CommandError):
    """The command ran and exited non-zero."""

    def __init__(self, message: str, *, returncode: int, stderr: str) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


def without_git_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return ``environ`` (default: this process's) with every ``GIT_*`` variable dropped.

    A ``GIT_DIR``, ``GIT_WORK_TREE``, ``GIT_INDEX_FILE`` or ``GIT_OBJECT_DIRECTORY``
    inherited from a hook or a calling Git would point ``git -C <path>`` at another
    repository than the one named, so a caller that names its repository by path
    runs Git without them.
    """
    source = os.environ if environ is None else environ
    return {key: value for key, value in source.items() if not key.startswith("GIT_")}


@dataclass(frozen=True)
class Completed:
    """A command that ran to its exit, whatever its exit code.

    ``stdout`` is ``str`` from ``run_result`` and ``bytes`` from ``run_bytes``;
    ``stderr`` is always text, decoded as UTF-8 with replacement. ``returncode`` is
    negative when a signal ended the command (``-9`` for ``SIGKILL``), so a caller
    whose answer is the exit code compares it with the codes it expects rather than
    treating every value but one as the other answer.
    """

    returncode: int
    stdout: str | bytes
    stderr: str


def _run(argv: list[str], *, cwd: Path | None, timeout: int, stdin: bytes | None,
         env: Mapping[str, str] | None) -> subprocess.CompletedProcess:
    """One bytes-mode ``subprocess.run`` call; a timeout or a failure to start becomes a CommandError.

    On a timeout ``subprocess.run`` kills the direct child and waits for it, as
    before. A process that child started keeps running, in the same process group
    or another; this runner does not reach it.
    """
    command = " ".join(argv)
    try:
        return subprocess.run(  # noqa: S603
            argv, cwd=None if cwd is None else str(cwd), timeout=timeout, input=stdin,
            env=None if env is None else dict(env), capture_output=True, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(f"{command} timed out after {timeout}s") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise CommandUnavailable(f"{command} could not run: {exc}") from exc


def _text(data: bytes, errors: str) -> str:
    # The same decoding and newline translation ``subprocess.run(text=True)`` applies
    # (``Popen._translate_newlines``), with UTF-8 named instead of the locale's.
    return data.decode("utf-8", errors).replace("\r\n", "\n").replace("\r", "\n")


def _stdout_text(argv: list[str], result: subprocess.CompletedProcess) -> str:
    try:
        return _text(result.stdout, "strict")
    except UnicodeDecodeError as exc:
        raise CommandError(f"{' '.join(argv)} wrote stdout that is not UTF-8 (exit {result.returncode}); "
                           "read it with run_bytes") from exc


def run_result(argv: list[str], *, cwd: Path | None, timeout: int, stdin_text: str | None = None,
               env: Mapping[str, str] | None = None) -> Completed:
    """Run a command with text in and out, and return its exit code, stdout and stderr.

    For a caller whose answer is the exit code (``git merge-base --is-ancestor``,
    ``git ls-files --error-unmatch``). A non-zero exit is returned, not raised. Only a
    timeout (``CommandTimedOut``), a command that cannot start (``CommandUnavailable``)
    or stdout that is not UTF-8 (``CommandError``) raises; stderr that is not UTF-8 is
    decoded with replacement, so it never costs the exit code. ``cwd`` and ``env`` are
    as for ``run_stdout``.
    """
    result = _run(argv, cwd=cwd, timeout=timeout,
                  stdin=None if stdin_text is None else stdin_text.encode("utf-8"), env=env)
    return Completed(result.returncode, _stdout_text(argv, result), _text(result.stderr, "replace"))


def run_bytes(argv: list[str], *, cwd: Path | None, timeout: int, stdin_bytes: bytes | None = None,
              env: Mapping[str, str] | None = None) -> Completed:
    """Run a command with bytes in and out, and return its exit code and output.

    For a caller that reads or writes content Git stores as bytes (``git show``,
    ``git cat-file blob``, ``git hash-object --stdin``). Exit codes and errors are as
    for ``run_result``; ``stdout`` is the raw bytes and ``stderr`` is decoded as UTF-8
    with replacement, for messages only.
    """
    result = _run(argv, cwd=cwd, timeout=timeout, stdin=stdin_bytes, env=env)
    return Completed(result.returncode, result.stdout, _text(result.stderr, "replace"))


def run_stdout(argv: list[str], *, cwd: Path | None, timeout: int, stdin_text: str | None = None,
               env: Mapping[str, str] | None = None) -> str:
    """Return stdout verbatim, or raise a CommandError naming the command and cause.

    A non-zero exit, including one a signal caused, raises ``CommandFailed`` before
    stdout is read. ``cwd=None`` runs in the current directory; ``env=None`` inherits
    this process's environment.
    """
    result = _run(argv, cwd=cwd, timeout=timeout,
                  stdin=None if stdin_text is None else stdin_text.encode("utf-8"), env=env)
    if result.returncode != 0:
        stderr = _text(result.stderr, "replace").strip()
        raise CommandFailed(f"{' '.join(argv)} failed (exit {result.returncode}): {stderr}",
                            returncode=result.returncode, stderr=stderr)
    return _stdout_text(argv, result)
