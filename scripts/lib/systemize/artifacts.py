"""Derived-artifact target resolution, safety checks and atomic publication.

The workflow's rule is that a configured output label does not make its
destination safe. Every target is resolved against an *allowed root* — the
shared state-path resolver's root for state artifacts, ``report_root`` inside
the repository for the report — and refused on any of: an escaping parent or
target symlink, a collision, a non-regular or multiply-linked target, an inode
alias of another artifact or a control input, a tracked path, or an existing
file that is not this run's own artifact. Parents are created only after every
check passes; publication is by atomic rename.
"""

from __future__ import annotations

import os
import stat
import subprocess
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from state_paths import repo_state_root, resolve_read_path, resolve_write_path
from state_paths.paths import PathTraversalError
from state_paths.resolver import StateRootError, state_root

from .config import Settings
from .errors import SystemizeError
from .identity import require_same_run


@dataclass(frozen=True)
class Target:
    label: str
    path: Path
    allowed_root: Path


def render(pattern: str, *, date: str, window_days: int, mode: str) -> str:
    return pattern.replace("{date}", date).replace("{window}", f"{window_days}d").replace("{mode}", mode)


def _state_relative(settings: Settings, logical: str) -> str:
    prefix = settings.state_dirname + "/"
    if not logical.startswith(prefix):
        raise SystemizeError(f"{logical}: state artifact must begin with {prefix}")
    return logical[len(prefix):]


def state_write_target(settings: Settings, label: str, logical: str) -> Target:
    rel = _state_relative(settings, logical)
    try:
        # The resolver is the authority on containment and sandbox selection, but
        # it returns a symlink-resolved path. Keep the lexical path beside it so a
        # symlinked target is seen by lstat rather than silently followed.
        resolve_write_path(rel, mkdir=False)
        root = Path(os.path.abspath(state_root()))
    except (PathTraversalError, StateRootError, ValueError) as exc:
        raise SystemizeError(f"{label}: state path {logical!r} rejected by the resolver: {exc}") from exc
    return Target(label, Path(os.path.abspath(root / rel)), root)


def state_read_path(settings: Settings, logical: str) -> Path:
    """The lexical path of the copy the resolver's newer-of-two cascade selects."""
    rel = _state_relative(settings, logical)
    try:
        chosen = resolve_read_path(rel)
        candidates = [Path(os.path.abspath(state_root() / rel))]
        with suppress(StateRootError):
            candidates.append(Path(os.path.abspath(repo_state_root() / rel)))
    except (PathTraversalError, StateRootError, ValueError) as exc:
        raise SystemizeError(f"state path {logical!r} rejected by the resolver: {exc}") from exc
    for candidate in candidates:
        if Path(os.path.realpath(candidate)) == Path(os.path.realpath(chosen)):
            return candidate
    raise SystemizeError(f"state path {logical!r}: resolver selected {chosen}, outside both state roots")


def report_target(settings: Settings, logical: str) -> Target:
    root = Path(os.path.abspath(settings.root / settings.report_root))
    path = Path(os.path.abspath(settings.root / logical))
    return Target("report", path, root)


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        info = os.stat(path)
    except OSError:
        return None
    return (info.st_dev, info.st_ino)


def _within(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def _is_tracked(repo: Path, path: Path) -> bool:
    if not _within(path, repo):
        return False
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", str(path.relative_to(repo))],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_targets(settings: Settings, targets: list[Target]) -> None:
    """Refuse every unsafe target before anything is created or written."""
    lexical = [t.path for t in targets]
    if len(lexical) != len(set(lexical)):
        raise SystemizeError("canonical artifact paths collide; select distinct configured patterns")
    real_paths = [Path(os.path.realpath(t.path)) for t in targets]
    if len(real_paths) != len(set(real_paths)):
        raise SystemizeError("canonical artifact paths collide through a link; inspect the state root")

    controls = set(settings.control_inputs)
    controls |= {Path(os.path.realpath(p)) for p in settings.control_inputs}
    control_ids = {i for i in (_identity(p) for p in settings.control_inputs) if i is not None}
    seen_ids: set[tuple[int, int]] = set()
    for target in targets:
        path, root = target.path, target.allowed_root
        if not _within(path, root) or path == root:
            raise SystemizeError(f"{target.label}: {path} is outside its allowed root {root}")
        real_root = Path(os.path.realpath(root))
        if not _within(Path(os.path.realpath(path.parent)), real_root):
            raise SystemizeError(f"{target.label}: a parent of {path} is a symlink escaping {root}")
        if target.label == "report" and not _within(Path(os.path.realpath(path)), settings.root):
            raise SystemizeError(f"report: {path} resolves outside the repository")
        if path in controls or Path(os.path.realpath(path)) in controls:
            raise SystemizeError(f"{target.label}: {path} is a repository control input")
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            info = None
        if info is not None:
            if not stat.S_ISREG(info.st_mode):
                raise SystemizeError(f"{target.label}: existing target {path} is not a regular file")
            if info.st_nlink != 1:
                raise SystemizeError(f"{target.label}: existing target {path} has {info.st_nlink} links")
            ident = (info.st_dev, info.st_ino)
            if ident in control_ids or ident in seen_ids:
                raise SystemizeError(f"{target.label}: existing target {path} aliases another artifact or control input")
            seen_ids.add(ident)
        if _is_tracked(settings.root, path):
            raise SystemizeError(f"{target.label}: {path} is tracked by Git")


def read_regular(path: Path, label: str) -> bytes:
    """Read without following a final symlink; refuse non-regular or linked files."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise SystemizeError(f"{label}: cannot read {path}: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise SystemizeError(f"{label}: {path} is not a singly-linked regular file")
        chunks = []
        while chunk := os.read(descriptor, 1 << 20):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def require_replaceable(target: Target, *, kind: str, identity: dict) -> None:
    if os.path.lexists(target.path):
        require_same_run(read_regular(target.path, target.label), kind=kind, identity=identity, path=str(target.path))


def publish(target: Target, data: bytes) -> None:
    """Atomically replace ``target`` with ``data``; call only after the checks."""
    parent = target.path.parent
    parent.mkdir(parents=True, exist_ok=True)
    real_root = Path(os.path.realpath(target.allowed_root))
    temporary = parent / f".{target.path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Re-check containment after the write, so a parent retargeted between
        # the preflight and now cannot receive the rename.
        if not _within(Path(os.path.realpath(parent)), real_root):
            raise SystemizeError(f"{target.label}: parent of {target.path} was retargeted outside {target.allowed_root}")
        os.replace(temporary, target.path)
        with suppress(OSError):
            directory = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
