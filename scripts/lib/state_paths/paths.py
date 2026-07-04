"""Path safety helpers — prevent directory traversal when joining paths read from YAML/JSON."""

from __future__ import annotations

from pathlib import Path


class PathTraversalError(ValueError):
    """Raised when a user-supplied path would resolve outside the allowed base directory."""


def safe_join(base: Path, *parts: str) -> Path:
    """Resolve `parts` against `base` and assert the result is contained inside `base`.

    Use this any time a file path is pulled from frontmatter, config, or another
    caller-controlled source before reading or attaching it. Rejects absolute
    paths and any `..` traversal that escapes `base`.

    Args:
        base: Directory the resolved path must stay inside. Resolved before comparison.
        *parts: Path fragments to join onto `base`. Empty strings are rejected.

    Returns:
        The resolved absolute path, guaranteed to be inside `base`.

    Raises:
        PathTraversalError: If any fragment is absolute, empty, or the resolved
            path is not contained inside `base`.
    """
    base_resolved = base.resolve()
    if not parts:
        raise PathTraversalError("safe_join requires at least one path fragment")
    candidate = base_resolved
    for part in parts:
        if not part:
            raise PathTraversalError("empty path fragment")
        fragment = Path(part)
        if fragment.is_absolute():
            raise PathTraversalError(f"absolute path not allowed: {part!r}")
        candidate = candidate / fragment
    resolved = candidate.resolve()
    if resolved != base_resolved and not resolved.is_relative_to(base_resolved):
        raise PathTraversalError(f"path {resolved} resolves outside base {base_resolved}")
    return resolved
