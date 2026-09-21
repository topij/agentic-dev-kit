"""Contained own-session artifact storage and filesystem observations."""

from __future__ import annotations

import os
import stat
import subprocess
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from state_paths import resolve_write_path
from state_paths.resolver import STATE_DIRNAME

from .canonical import digest_bytes, dumps
from .model import Settings, TriageError


@dataclass(frozen=True)
class Observation:
    path: str
    exists: bool
    device: int | None
    inode: int | None
    mode: int | None
    links: int | None
    size: int | None
    mtime_ns: str | None
    digest: str | None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def observe(path: Path, *, read: bool = True, allow_links: bool = False) -> tuple[Observation, bytes | None]:
    try:
        descriptors, identities, components = _open_parent_chain(path)
    except FileNotFoundError:
        return Observation(str(path), False, None, None, None, None, None, None, None), None
    try:
        _revalidate_parent_chain(descriptors, identities, components)
        result = _observe_at(descriptors[-1], path.name, path, read=read, allow_links=allow_links)
        _revalidate_parent_chain(descriptors, identities, components)
        return result
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def preflight_artifacts(
    artifacts: list[Path], *, controls: list[Path], repo: Path
) -> None:
    lexical = [Path(os.path.abspath(path)) for path in artifacts]
    if len(lexical) != len(set(lexical)):
        raise TriageError("artifact publication paths collide", outcome="hard-stop")
    control_paths = {Path(os.path.abspath(path)) for path in controls}
    artifact_identities: set[tuple[int, int]] = set()
    control_identities: set[tuple[int, int]] = set()
    for control in control_paths:
        observation, _ = observe(control, read=False)
        if observation.exists:
            control_identities.add((observation.device, observation.inode))
    for artifact in lexical:
        if artifact in control_paths:
            raise TriageError("artifact target is a workflow control input", outcome="hard-stop")
        observation, _ = observe(artifact, read=False)
        if observation.exists:
            identity = (observation.device, observation.inode)
            if identity in artifact_identities or identity in control_identities:
                raise TriageError("artifact target aliases another artifact or control input", outcome="hard-stop")
            artifact_identities.add(identity)
        if artifact.is_relative_to(repo):
            relative = str(artifact.relative_to(repo))
            tracked = subprocess.run(
                ["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", relative],
                check=False,
                capture_output=True,
                text=True,
            )
            if tracked.returncode == 0:
                raise TriageError("artifact target is tracked by the repository", outcome="hard-stop")


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _open_parent_chain(path: Path) -> tuple[list[int], list[tuple[int, int]], list[str]]:
    absolute = Path(os.path.abspath(path.parent))
    descriptors = [os.open("/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))]
    identities = [(os.fstat(descriptors[0]).st_dev, os.fstat(descriptors[0]).st_ino)]
    components = list(absolute.parts[1:])
    try:
        for component in components:
            descriptor = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptors[-1],
            )
            descriptors.append(descriptor)
            info = os.fstat(descriptor)
            identities.append((info.st_dev, info.st_ino))
    except Exception:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    return descriptors, identities, components


def _revalidate_parent_chain(
    descriptors: list[int], identities: list[tuple[int, int]], components: list[str]
) -> None:
    for descriptor, expected in zip(descriptors, identities, strict=True):
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) != expected:
            raise TriageError("held artifact ancestor changed", outcome="operator-held")
    probe = os.open("/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        root_info = os.fstat(probe)
        if (root_info.st_dev, root_info.st_ino) != identities[0]:
            raise TriageError("artifact ancestor chain retargeted", outcome="operator-held")
        for component, expected in zip(components, identities[1:], strict=True):
            following = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=probe,
            )
            os.close(probe)
            probe = following
            info = os.fstat(probe)
            if (info.st_dev, info.st_ino) != expected:
                raise TriageError("artifact ancestor chain retargeted", outcome="operator-held")
    finally:
        os.close(probe)


def _observe_at(
    parent_descriptor: int,
    name: str,
    display_path: Path,
    *,
    read: bool = True,
    allow_links: bool = False,
) -> tuple[Observation, bytes | None]:
    try:
        info = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return Observation(str(display_path), False, None, None, None, None, None, None, None), None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or (not allow_links and info.st_nlink != 1):
        raise TriageError(f"unsafe artifact at held parent: {display_path}", outcome="operator-held")
    descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_descriptor)
    try:
        captured = os.fstat(descriptor)
        if (captured.st_dev, captured.st_ino) != (info.st_dev, info.st_ino):
            raise TriageError(f"artifact name changed before held capture: {display_path}", outcome="operator-held")
        if read:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
        else:
            raw = None
    finally:
        os.close(descriptor)
    after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    signature = (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns)
    after_signature = (after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size, after.st_mtime_ns)
    if signature != after_signature:
        raise TriageError(f"artifact changed while held: {display_path}", outcome="operator-held")
    return Observation(
        str(display_path), True, info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
        info.st_size, str(info.st_mtime_ns), digest_bytes(raw) if raw is not None else None,
    ), raw


def quarantine_inode(source: Path, target: Path, approved: Observation, approved_raw: bytes) -> Observation:
    source_descriptors, source_identities, source_components = _open_parent_chain(source)
    target_descriptors, target_identities, target_components = _open_parent_chain(target)
    source_parent = source_descriptors[-1]
    target_parent = target_descriptors[-1]
    try:
        _revalidate_parent_chain(source_descriptors, source_identities, source_components)
        _revalidate_parent_chain(target_descriptors, target_identities, target_components)
        current, current_raw = _observe_at(source_parent, source.name, source, allow_links=True)
        if current != approved or current_raw != approved_raw:
            raise TriageError("approved artifact changed before quarantine", outcome="operator-held")
        existing, existing_raw = _observe_at(target_parent, target.name, target, allow_links=True)
        if existing_raw is None:
            os.link(
                source.name,
                target.name,
                src_dir_fd=source_parent,
                dst_dir_fd=target_parent,
                follow_symlinks=False,
            )
            os.fsync(target_parent)
        elif existing_raw != approved_raw or (existing.device, existing.inode) != (approved.device, approved.inode):
            raise TriageError("prepared quarantine target already exists with foreign identity", outcome="operator-held")
        linked, linked_raw = _observe_at(target_parent, target.name, target, allow_links=True)
        source_before_unlink, source_raw = _observe_at(source_parent, source.name, source, allow_links=True)
        expected_links = approved.links + 1 if approved.links is not None else None
        if (
            linked_raw != approved_raw
            or source_raw != approved_raw
            or (linked.device, linked.inode) != (approved.device, approved.inode)
            or (source_before_unlink.device, source_before_unlink.inode) != (approved.device, approved.inode)
            or linked.links != expected_links
            or source_before_unlink.links != expected_links
        ):
            raise TriageError("quarantine publication identity mismatch", outcome="operator-held")
        _revalidate_parent_chain(source_descriptors, source_identities, source_components)
        _revalidate_parent_chain(target_descriptors, target_identities, target_components)
        os.unlink(source.name, dir_fd=source_parent)
        os.fsync(source_parent)
        _revalidate_parent_chain(source_descriptors, source_identities, source_components)
        _revalidate_parent_chain(target_descriptors, target_identities, target_components)
        final, final_raw = _observe_at(target_parent, target.name, target, allow_links=True)
        if final_raw != approved_raw or (final.device, final.inode) != (approved.device, approved.inode):
            raise TriageError("quarantine read-back mismatch", outcome="operator-held")
        return final
    finally:
        for descriptor in reversed(target_descriptors):
            os.close(descriptor)
        for descriptor in reversed(source_descriptors):
            os.close(descriptor)


def atomic_replace(path: Path, raw: bytes, *, expected_digest: str | None = None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptors, identities, components = _open_parent_chain(path)
    parent_descriptor = descriptors[-1]
    temporary = f".{path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
        dir_fd=parent_descriptor,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if expected_digest is not None:
            current_obs, _ = _observe_at(parent_descriptor, path.name, path)
            if current_obs.digest != expected_digest:
                raise TriageError("concurrent state transition", outcome="operator-held")
        _revalidate_parent_chain(descriptors, identities, components)
        os.replace(temporary, path.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
        _revalidate_parent_chain(descriptors, identities, components)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=parent_descriptor)
        for held in reversed(descriptors):
            os.close(held)
    return digest_bytes(raw)


def exclusive_create(
    path: Path,
    raw: bytes,
    *,
    mode: int = 0o600,
    temporary_name: str | None = None,
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptors, identities, components = _open_parent_chain(path)
    parent_descriptor = descriptors[-1]
    temporary = temporary_name or f".{path.name}.{digest_bytes(raw)}.tmp"
    if Path(temporary).name != temporary:
        for held in reversed(descriptors):
            os.close(held)
        raise TriageError("temporary artifact name must be a basename", outcome="operator-held")
    published_before, _ = _observe_at(
        parent_descriptor,
        path.name,
        path,
        read=False,
        allow_links=True,
    )
    if published_before.exists and published_before.links == 1:
        for held in reversed(descriptors):
            os.close(held)
        raise FileExistsError(path)
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            mode,
            dir_fd=parent_descriptor,
        )
    except FileExistsError:
        try:
            staged, staged_raw = _observe_at(
                parent_descriptor,
                temporary,
                path.with_name(temporary),
                allow_links=True,
            )
            published, published_raw = _observe_at(
                parent_descriptor,
                path.name,
                path,
                allow_links=True,
            )
            if staged_raw != raw:
                raise TriageError("staged exclusive artifact has foreign bytes", outcome="operator-held")
            if published_raw is None:
                _revalidate_parent_chain(descriptors, identities, components)
                os.link(
                    temporary,
                    path.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                os.fsync(parent_descriptor)
                published, published_raw = _observe_at(
                    parent_descriptor,
                    path.name,
                    path,
                    allow_links=True,
                )
            if (
                published_raw != raw
                or (published.device, published.inode) != (staged.device, staged.inode)
            ):
                raise TriageError("published exclusive artifact has foreign identity", outcome="operator-held")
            _revalidate_parent_chain(descriptors, identities, components)
            os.unlink(temporary, dir_fd=parent_descriptor)
            os.fsync(parent_descriptor)
            _revalidate_parent_chain(descriptors, identities, components)
        finally:
            for held in reversed(descriptors):
                os.close(held)
        return digest_bytes(raw)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _revalidate_parent_chain(descriptors, identities, components)
        os.link(temporary, path.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor, follow_symlinks=False)
        os.fsync(parent_descriptor)
        _revalidate_parent_chain(descriptors, identities, components)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=parent_descriptor)
        for held in reversed(descriptors):
            os.close(held)
    return digest_bytes(raw)


def unlink_inode(path: Path, approved: Observation, approved_raw: bytes, *, allow_links: bool = False) -> None:
    descriptors, identities, components = _open_parent_chain(path)
    parent_descriptor = descriptors[-1]
    try:
        _revalidate_parent_chain(descriptors, identities, components)
        current, current_raw = _observe_at(
            parent_descriptor,
            path.name,
            path,
            allow_links=allow_links,
        )
        if current != approved or current_raw != approved_raw:
            raise TriageError("approved artifact changed before unlink", outcome="operator-held")
        _revalidate_parent_chain(descriptors, identities, components)
        os.unlink(path.name, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
        _revalidate_parent_chain(descriptors, identities, components)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


class ArtifactStore:
    def __init__(self, settings: Settings, mode: str) -> None:
        self.settings = settings
        self.mode = mode
        if STATE_DIRNAME != "state":
            raise TriageError("state resolver dirname mismatch")

    @staticmethod
    def _strip_state(fragment: str) -> str:
        prefix = STATE_DIRNAME + "/"
        if not fragment.startswith(prefix):
            raise TriageError("logical state fragment has wrong prefix")
        return fragment[len(prefix):]

    def resolve(self, fragment: str, *, mkdir: bool = False) -> Path:
        expanded = fragment.replace("{mode}", self.mode)
        if "{" in expanded or "}" in expanded:
            raise TriageError("unexpanded state artifact placeholder")
        return resolve_write_path(self._strip_state(expanded), mkdir=mkdir)

    @property
    def state_path(self) -> Path:
        return self.resolve(self.settings.paths.state_fragment)

    @property
    def gate_path(self) -> Path:
        return self.resolve(self.settings.paths.gate_fragment)

    def recovery_path(self, gate_digest: str) -> Path:
        return self.resolve(self.settings.paths.recovery_pattern.replace("{gate_digest}", gate_digest))

    def frozen_path(self, *, session: str, day: str, mkdir: bool = False) -> Path:
        fragment = self.settings.paths.frozen_pattern.replace("{date}", day).replace("{session}", session)
        return self.resolve(fragment, mkdir=mkdir)

    def report_path(self, *, session: str, day: str) -> Path:
        relative = self.settings.paths.report_pattern.replace("{mode}", self.mode).replace("{date}", day).replace("{session}", session)
        path = (self.settings.paths.repo / relative).resolve()
        if not path.is_relative_to(self.settings.paths.report_root):
            raise TriageError("report path escaped report root")
        return path

    def read(self, path: Path, *, allow_links: bool = False) -> tuple[Observation, bytes | None]:
        return observe(path, allow_links=allow_links)

    def write_json(self, path: Path, value: Any, *, expected_digest: str | None = None, exclusive: bool = False) -> str:
        raw = dumps(value)
        return exclusive_create(path, raw) if exclusive else atomic_replace(path, raw, expected_digest=expected_digest)
