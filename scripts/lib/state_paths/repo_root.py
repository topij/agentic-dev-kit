"""Repo-root discovery — shared marker walk-up.

Callers need to find the project repo root from an arbitrary cwd. Counting
``Path(__file__).parents[N]`` silently breaks under any non-editable install
(a uv worktree env, an archive cache, a pip wheel) — the file's on-disk depth
isn't a stable proxy for "how many directories up is the repo root". The
reliable signal is a repo *marker*: a ``.git`` entry (a directory in a regular
checkout, a file in a linked worktree).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def has_repo_marker(candidate: Path) -> bool:
    """True iff ``candidate`` looks like the repo root — i.e. it has a ``.git`` entry.

    Accepts a ``.git`` entry whether it's a directory (a regular checkout) or a
    file (a linked worktree's gitdir pointer).
    """
    return (candidate / ".git").exists()


def walk_up_for_marker(start: Path) -> Path | None:
    """First ancestor of ``start`` (inclusive) carrying a repo marker, else ``None``."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if has_repo_marker(candidate):
            return candidate
    return None


def primary_worktree(repo_root: Path) -> Path:
    """The primary checkout, or the invoking checkout if Git lists no usable primary.

    Ignore inherited Git repository selectors so discovery stays anchored to
    the checkout that owns the engine. Bare and separate Git dirs have no
    usable primary working directory in the porcelain listing.
    """
    if not (repo_root / ".git").is_file():
        return repo_root
    try:
        listed = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "list", "--porcelain", "-z"],
            env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        listed = b""
    first: list[bytes] = []
    for field in listed.split(b"\0"):
        if not field:
            break
        first.append(field)
    if first and first[0].startswith(b"worktree ") and b"bare" not in first[1:]:
        candidate = Path(os.fsdecode(first[0][len(b"worktree "):]))
        if candidate.is_absolute() and candidate.is_dir() and (candidate / ".git").exists():
            return candidate
    return repo_root
