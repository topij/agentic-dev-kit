"""Run a text-mode command and translate failures for engine CLI callers.

Every failure is a ``CommandError`` (a ``RuntimeError``), so a caller that only
needs "it did not work" catches one type. A caller that must treat the cases
differently catches the subclass: ``CommandTimedOut``, ``CommandUnavailable``
(the process could not start) or ``CommandFailed`` (it ran and exited non-zero).
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
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


def run_stdout(argv: list[str], *, cwd: Path | None, timeout: int, stdin_text: str | None = None,
               env: Mapping[str, str] | None = None) -> str:
    """Return stdout verbatim, or raise a CommandError naming the command and cause.

    ``cwd=None`` runs in the current directory; ``env=None`` inherits this process's
    environment.
    """
    command = " ".join(argv)
    try:
        result = subprocess.run(  # noqa: S603
            argv, cwd=None if cwd is None else str(cwd), timeout=timeout, input=stdin_text,
            env=None if env is None else dict(env), capture_output=True, text=True, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(f"{command} timed out after {timeout}s") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise CommandUnavailable(f"{command} could not run: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise CommandFailed(f"{command} failed (exit {result.returncode}): {stderr}",
                            returncode=result.returncode, stderr=stderr)
    return result.stdout
