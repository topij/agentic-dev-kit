"""Run a text-mode command and translate failures for engine CLI callers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_stdout(argv: list[str], *, cwd: Path, timeout: int, stdin_text: str | None = None) -> str:
    """Return stdout verbatim, or raise RuntimeError with the command and cause."""
    try:
        result = subprocess.run(  # noqa: S603
            argv, cwd=str(cwd), timeout=timeout, input=stdin_text,
            capture_output=True, text=True, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{' '.join(argv)} timed out after {timeout}s") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"{' '.join(argv)} could not run: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout
