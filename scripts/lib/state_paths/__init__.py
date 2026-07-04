"""Standalone per-worktree state sandbox primitive.

A single env var (``DEVKIT_STATE_ROOT``) redirects all ``state/`` writes under
a per-worktree sandbox so parallel/background lanes never clobber shared
production ``state/``. See :mod:`state_paths.resolver` for the full resolution
semantics.

Public surface re-exported here: :func:`resolve_write_path`,
:func:`resolve_read_path`, :func:`glob_state`, :func:`glob_state_cache`,
:func:`state_root`, :func:`repo_state_root`, :class:`StateRootError`,
:class:`UnsandboxedStateWriteError`.

Internals — the env-var name constants, the marker filename, and
``_marker_state_root`` — are not re-exported here; import them from
``state_paths.resolver`` directly (as the test suite does).
"""

from __future__ import annotations

from .resolver import (
    StateRootError,
    UnsandboxedStateWriteError,
    glob_state,
    glob_state_cache,
    repo_state_root,
    resolve_read_path,
    resolve_write_path,
    state_root,
)

__all__ = [
    "StateRootError",
    "UnsandboxedStateWriteError",
    "glob_state",
    "glob_state_cache",
    "repo_state_root",
    "resolve_read_path",
    "resolve_write_path",
    "state_root",
]
