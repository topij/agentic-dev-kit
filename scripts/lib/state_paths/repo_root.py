"""Repo-root discovery — shared marker walk-up.

Callers need to find the project repo root from an arbitrary cwd. Counting
``Path(__file__).parents[N]`` silently breaks under any non-editable install
(a uv worktree env, an archive cache, a pip wheel) — the file's on-disk depth
isn't a stable proxy for "how many directories up is the repo root". The
reliable signal is a repo *marker*: a ``.git`` entry (a directory in a regular
checkout, a file in a linked worktree).
"""

from __future__ import annotations

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
