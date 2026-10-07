#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Report, and on request remove, stale scratch under the configured artifact roots.

Session scratchpads accumulate until the disk fills (#900); review-lens clones
under the system temp dir and killed pytest basetemps do too, but no root here
covers them. This engine is the one boundary for clearing a configured root: an allowlistable
command in place of ad-hoc ``rm -rf``.

The roots and the grace window are read from ``config/dev-model.yaml`` under
``scratch:``; nothing about where scratch lives is hardcoded here. Each direct
child of a root is one **entry**, and every entry gets exactly one owner class:

``live-worktree``
    The entry is, contains or sits inside a worktree registered with one of the
    ``scratch.worktree_repos`` (``git worktree list --porcelain``); or it holds a
    ``.git`` file pointing at a git dir that still exists outside the entry — a
    linked worktree of some repository this config does not name; or it holds a
    ``.git`` directory whose ``worktrees/*/gitdir`` names a worktree that still
    exists outside the entry, which removing the entry would orphan; or it holds
    any other git dir (a bare repository or a ``--separate-git-dir`` target, which
    records nothing about who uses it) outside a ``.git`` directory; or it is,
    holds or sits inside the git dir of a configured repository or an object
    store one borrows from through ``objects/info/alternates``, followed
    transitively. A ``.git`` file or ``worktrees`` record the engine cannot read
    or parse also lands here, with that as its reason: kept, as if live; an
    unreadable or quoted ``alternates`` file is an exit 2.
``in-grace``
    Something anywhere inside the entry was modified within
    ``scratch.grace_window``. The newest mtime over the whole tree decides, not the
    top directory's.
``stale``
    Neither of the above, and fully scanned.
``unclassified``
    Anything the engine could not fully classify: a symlink entry, an entry that
    is neither a file nor a directory, an unreadable path inside it, an entry that
    is or holds a mount point on another device (a same-device bind mount shares
    ``st_dev`` and is not detected), or an entry that is or holds another
    configured root. Always kept.

Age is the newest **mtime** in the entry. A tree extracted or copied with its
original timestamps (``cp -a``, ``rsync -a``, an archive) looks as old as its
source, so add a root only where every child is disposable whatever its age.

Report mode (the default) changes nothing. ``--apply --older-than <age>`` removes
``stale`` entries whose newest mtime is at least ``<age>`` old, and nothing else.
Immediately before each removal it re-reads the worktree registrations and
re-scans the entry, and it removes only if the entry is still ``stale``, still old
enough, and is the same inode it classified.

A root is refused, and none of its entries touched, when it is not absolute after
placeholder expansion, is ``/``, contains ``..``, is itself a symlink, has a
symlink anywhere in its path, is not a directory, or is or contains the user's
home directory or one of the ``scratch.worktree_repos``. A root that does not
exist is reported as absent. The root itself is never removed.

Known limits, each one a reason to configure only a root whose every child is
disposable:

- An ordinary clone inside an entry that a repository the config does not name
  borrows objects from (a ``--shared`` or ``--reference`` clone elsewhere, whose
  ``objects/info/alternates`` points in) is not detected, and the entry can be
  ``stale``: the borrowed-from clone records nothing, and only the configured
  repositories' alternates are read. The same holds for a ``--separate-git-dir``
  target that is itself named ``.git``.
- The other direction costs reclaimed space: any bare-looking git dir keeps its
  whole entry, so a session scratchpad holding a pytest basetemp with fixture
  repositories (an ``origin.git``, say) is never swept. The reason names the git
  dir that kept it.
- A root over some other directory of repositories is refused only when it holds
  the home directory or a configured worktree repo. An idle sibling repository
  with no linked worktree is otherwise judged by age like anything else.
- A ``.git`` file whose git dir sits on an unmounted volume reads as an orphaned
  worktree, and the entry can be ``stale``.
- ``git worktree list -z`` needs git 2.36 or later. An older git fails the
  registration read, which exits 2 and touches nothing.

Usage (``<engine-dir>`` is ``paths.engines``):

    uv run <engine-dir>/sweep_scratch.py                          # report
    uv run <engine-dir>/sweep_scratch.py --json                   # machine-readable report
    uv run <engine-dir>/sweep_scratch.py --apply --older-than 7d  # remove stale entries

Ages are ``<n>s``, ``<n>m``, ``<n>h`` or ``<n>d``.

Exit codes:
    0 — report printed, and no root refused and no removal failed. An entry kept
        because its re-check no longer judged it removable, including a worktree
        re-read that failed mid-apply, is reported as ``kept`` and is not a
        failure.
    1 — a configured root was refused, or a removal was attempted and failed.
    2 — usage or config error, or the worktree registrations could not be read.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pwd
import re
import shutil
import stat
import string
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

LIVE = "live-worktree"
GRACE = "in-grace"
STALE = "stale"
UNCLASSIFIED = "unclassified"

_AGE_RE = re.compile(r"^(\d+)([smhd])$")
_AGE_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
# Read cap for a `.git` file. A real one is a single `gitdir:` line; anything
# larger is not one, and is treated as unparseable rather than read whole.
_GIT_FILE_MAX = 4096


class ConfigError(Exception):
    """A config or usage problem; the CLI exits 2."""


class Refused(Exception):
    """The removal primitive declined a path; the reason is the message."""


def parse_age(text: object, what: str) -> int:
    """``"36h"`` -> 129600. Bare numbers are refused: a unit-less age is ambiguous."""
    match = _AGE_RE.match(str(text).strip()) if isinstance(text, str) else None
    if not match:
        raise ConfigError(f"{what} must look like 30m, 36h or 7d (got {text!r})")
    return int(match.group(1)) * _AGE_UNITS[match.group(2)]


def repo_slug(root: Path) -> str:
    """Claude Code's project-dir naming: every non-alphanumeric char becomes ``-``."""
    return re.sub(r"[^a-zA-Z0-9]", "-", str(root))


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #


@dataclass
class Settings:
    roots: list[str]
    grace_seconds: int
    repos: list[Path]


def load_settings(config_path: str | Path, *, root: Path | None = None) -> Settings:
    """Read ``scratch.*``. Every key is required: an absent key is a refusal, not a default."""
    root = root or repo_root()
    try:
        config = load_config(config_path)
    except (OSError, ValueError) as exc:
        raise ConfigError(str(exc)) from exc
    try:
        roots = get(config, "scratch.roots")
        grace = get(config, "scratch.grace_window")
        repos = get(config, "scratch.worktree_repos")
    except KeyError as exc:
        raise ConfigError(f"{exc.args[0]} — see the scratch: block in config/dev-model.yaml") from exc
    if not isinstance(roots, list) or not all(isinstance(r, str) and r for r in roots):
        raise ConfigError("scratch.roots must be a list of path strings")
    if not isinstance(repos, list) or not all(isinstance(r, str) and r for r in repos):
        raise ConfigError("scratch.worktree_repos must be a list of path strings")
    if not repos:
        raise ConfigError("scratch.worktree_repos is empty; it must name at least this repo")
    repo_paths = [Path(r) if Path(r).is_absolute() else root / r for r in repos]
    return Settings(
        roots=list(roots),
        grace_seconds=parse_age(grace, "scratch.grace_window"),
        repos=repo_paths,
    )


def expand_root(raw: str, *, root: Path) -> str:
    """Substitute ``{uid}`` and ``{repo_slug}``. Any other placeholder is an error."""
    values = {"uid": str(os.getuid()), "repo_slug": repo_slug(root)}
    try:
        fields = list(string.Formatter().parse(raw))
    except ValueError as exc:
        raise ValueError(f"malformed placeholder in {raw!r} ({exc})") from exc
    for _literal, name, spec, conversion in fields:
        if name is None:
            continue
        if name not in values or spec or conversion:
            raise ValueError(f"unknown or malformed placeholder {{{name}}} in {raw!r}")
    return raw.format_map(values)


def guarded_paths(repos: list[Path]) -> list[str]:
    """Real paths no root may equal or contain: the user's home and each worktree repo.

    A root that holds one of these is a code or home directory, not scratch, and its
    other children are judged by age alone. Only these paths are knowable; a root
    over some other directory of repositories is not detected (see ``scratch:``).
    """
    homes: set[str] = set()
    env_home = os.environ.get("HOME")
    if env_home and os.path.isabs(env_home):
        homes.add(os.path.realpath(env_home))
    with contextlib.suppress(KeyError):  # no passwd entry for this uid
        homes.add(os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir))
    return sorted(homes) + [os.path.realpath(r) for r in repos]


def validate_root(path: str, guarded: list[str] | None = None) -> tuple[str, str | None]:
    """``(status, reason)`` where status is ``ok``, ``absent`` or ``refused``."""
    if not os.path.isabs(path):
        return "refused", "not an absolute path"
    trimmed = path.rstrip("/") or "/"
    if trimmed == "/":
        return "refused", "the filesystem root"
    if ".." in trimmed.split("/") or os.path.normpath(trimmed) != trimmed:
        return "refused", "not a normalised path"
    if not os.path.lexists(trimmed):
        return "absent", None
    if os.path.islink(trimmed):
        return "refused", "the root is itself a symlink"
    real = os.path.realpath(trimmed)
    if real != trimmed:
        return "refused", f"a symlink in its path; configure {real} if that is meant"
    if not os.path.isdir(trimmed):
        return "refused", "not a directory"
    for held in guarded or []:
        if held == trimmed or held.startswith(trimmed + os.sep):
            return "refused", f"holds {held}, a home or worktree repository"
    return "ok", None


# --------------------------------------------------------------------------- #
# worktree registrations
# --------------------------------------------------------------------------- #


def registered_worktrees(repos: list[Path]) -> list[str]:
    """Real paths of every worktree each repo registers. Any failure raises ConfigError."""
    found: list[str] = []
    # Run from a git hook, an inherited GIT_DIR or GIT_WORK_TREE would point
    # `git -C` at another repository's registrations.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    for repo in repos:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "worktree", "list", "--porcelain", "-z"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        except OSError as exc:
            raise ConfigError(f"cannot run git for {repo}: {exc}") from exc
        if result.returncode != 0:
            raise ConfigError(
                f"git worktree list failed for {repo}: {result.stderr.strip() or result.returncode}"
            )
        # -z: NUL-terminated fields, so a path holding a newline stays whole.
        for line in result.stdout.split("\0"):
            if line.startswith("worktree "):
                found.append(os.path.realpath(line[len("worktree "):]))
    if not found:
        raise ConfigError("no worktree registrations read; refusing to classify without them")
    return found


# Hops followed along an alternates chain before the read gives up (and refuses).
_ALTERNATES_MAX = 16


def _git_common_dir(worktree: str, env: dict[str, str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", worktree, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except OSError as exc:
        raise ConfigError(f"cannot run git for {worktree}: {exc}") from exc
    path = result.stdout.strip()
    if result.returncode != 0 or not os.path.isabs(path):
        raise ConfigError(
            f"cannot read the git dir of {worktree}: {result.stderr.strip() or result.returncode}"
        )
    return os.path.realpath(path)


def _alternates(objects: str) -> list[str]:
    """Object directories ``objects/info/alternates`` borrows from; an unreadable one raises."""
    path = os.path.join(objects, "info", "alternates")
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc.strerror}") from exc
    if not stat.S_ISREG(st.st_mode):
        raise ConfigError(f"{path} is not a regular file")
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc.strerror}") from exc
    found: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith('"'):
            # A C-quoted path; not parsed here, so nothing is classified past it.
            raise ConfigError(f"quoted path in {path}; refusing to classify without it")
        if not os.path.isabs(line):
            line = os.path.join(objects, line)
        found.append(os.path.realpath(line))
    return found


def repository_stores(worktrees: list[str]) -> list[str]:
    """Git dirs and borrowed object stores the configured repositories depend on.

    For every registered worktree: its common git dir, and every object directory
    reached through ``objects/info/alternates``, followed transitively. An entry
    holding any of these is kept, because removing it breaks a configured
    repository. A repository the config does not name is not read (see the limits
    in the module docstring). Any failure raises ConfigError.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    stores: list[str] = []
    pending: list[tuple[str, int]] = []
    for worktree in worktrees:
        state = _target_state(worktree)
        if state == "gone":
            # A prunable registration: its directory was deleted. Its common git
            # dir is the one every other worktree of that repository reports.
            continue
        if state == "unknown":
            raise ConfigError(f"cannot stat the registered worktree {worktree}")
        common = _git_common_dir(worktree, env)
        if common not in stores:
            stores.append(common)
            pending.append((os.path.join(common, "objects"), 0))
    seen: set[str] = set()
    while pending:
        objects, depth = pending.pop()
        if objects in seen:
            continue
        seen.add(objects)
        for borrowed in _alternates(objects):
            if depth + 1 > _ALTERNATES_MAX:
                raise ConfigError(f"alternates chain from {objects} is deeper than {_ALTERNATES_MAX}")
            if borrowed not in stores:
                stores.append(borrowed)
            pending.append((borrowed, depth + 1))
    return stores


# --------------------------------------------------------------------------- #
# classification
# --------------------------------------------------------------------------- #


@dataclass
class Entry:
    path: str
    owner: str
    size_bytes: int = 0
    age_seconds: int | None = None
    reason: str | None = None
    identity: tuple[int, int] | None = field(default=None, repr=False)


def _overlaps(a: str, b: str) -> bool:
    return a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep)


def live_worktree_reason(path: str, worktrees: list[str]) -> str | None:
    for wt in worktrees:
        if _overlaps(path, wt):
            return f"registered worktree {wt}"
    return None


def repository_store_reason(path: str, stores: list[str]) -> str | None:
    for store in stores:
        if _overlaps(path, store):
            return f"git dir or object store {store} of a configured repository"
    return None


def configured_root_reason(path: str, roots: list[str]) -> str | None:
    # One direction only: an entry that IS or CONTAINS another root. Every entry of
    # a root nested inside this one sits under that root, and is not refused for it.
    for other in roots:
        if path == other or other.startswith(path + os.sep):
            return f"holds the configured root {other}"
    return None


def grace_reason(age: float, grace_seconds: int) -> str | None:
    if age < grace_seconds:
        return f"modified {format_age(max(0.0, age))} ago, inside the {format_age(grace_seconds)} grace window"
    return None


def _target_state(path: str) -> str:
    """``present``, ``gone`` or ``unknown``. Only a missing path is ``gone``.

    ``os.path.exists`` answers False on a permission error too, which would read
    an unreachable live worktree as an abandoned one.
    """
    try:
        os.stat(path)
    except FileNotFoundError:
        return "gone"
    except (OSError, ValueError):
        return "unknown"
    return "present"


def _linked_gitdir_reason(git_file: str, entry: str) -> str | None:
    """A ``.git`` file whose git dir exists outside the entry is someone's live worktree."""
    try:
        with open(git_file, encoding="utf-8", errors="replace") as handle:
            text = handle.read(_GIT_FILE_MAX + 1)
    except OSError as exc:
        return f"unreadable .git file {git_file}: {exc.strerror}"
    lines = text.strip().splitlines()
    if len(text) > _GIT_FILE_MAX or len(lines) != 1 or not lines[0].startswith("gitdir:"):
        return f"unparseable .git file {git_file}"
    target = lines[0][len("gitdir:"):].strip()
    if not os.path.isabs(target):
        target = os.path.join(os.path.dirname(git_file), target)
    try:
        target = os.path.realpath(target)
    except (OSError, ValueError):
        return f"unparseable .git file {git_file}"
    if target.startswith(entry + os.sep):
        return None  # a submodule whose git dir lives inside the same entry
    state = _target_state(target)
    if state == "unknown":
        return f"cannot stat the git dir {target} named by {git_file}"
    if state == "present":
        return f"linked worktree {os.path.dirname(git_file)} of an unconfigured repository ({target})"
    return None


def _looks_like_git_dir(path: str) -> bool:
    """A git dir by git's own layout test: a ``HEAD`` file, ``objects`` and ``refs``, never followed."""
    try:
        head = os.lstat(os.path.join(path, "HEAD"))
        objects = os.lstat(os.path.join(path, "objects"))
        refs = os.lstat(os.path.join(path, "refs"))
    except OSError:
        return False
    return stat.S_ISREG(head.st_mode) and stat.S_ISDIR(objects.st_mode) and stat.S_ISDIR(refs.st_mode)


def _detached_git_dir(path: str) -> str:
    return (
        f"{path} is a git dir not beside its own work tree (a bare repository or a "
        "--separate-git-dir target), which a repository outside this entry may depend on"
    )


def _main_repo_reason(git_dir: str, entry: str) -> str | None:
    """A ``.git`` directory whose linked worktrees live outside the entry.

    Removing the entry deletes the git dir those worktrees point back at, so they
    stop being repositories. Reads ``<git_dir>/worktrees/*/gitdir``, each the path
    of one worktree's ``.git`` file.
    """
    records = os.path.join(git_dir, "worktrees")
    try:
        names = sorted(os.listdir(records))
    except FileNotFoundError:
        return None
    except OSError as exc:
        return f"unreadable worktree records {records}: {exc.strerror}"
    for name in names:
        gitdir_file = os.path.join(records, name, "gitdir")
        try:
            st = os.lstat(gitdir_file)
        except FileNotFoundError:
            continue  # a half-pruned record names no worktree
        except OSError as exc:
            return f"unreadable worktree record {gitdir_file}: {exc.strerror}"
        if not stat.S_ISREG(st.st_mode):
            # Never open a FIFO or device: the read would block the sweep.
            return f"unparseable worktree record {gitdir_file}"
        try:
            with open(gitdir_file, encoding="utf-8", errors="replace") as handle:
                text = handle.read(_GIT_FILE_MAX + 1)
        except OSError as exc:
            return f"unreadable worktree record {gitdir_file}: {exc.strerror}"
        lines = text.strip().splitlines()
        if len(text) > _GIT_FILE_MAX or len(lines) != 1:
            return f"unparseable worktree record {gitdir_file}"
        target = lines[0].strip()
        if not os.path.isabs(target):
            target = os.path.join(os.path.dirname(gitdir_file), target)
        try:
            worktree = os.path.dirname(os.path.realpath(target))
        except (OSError, ValueError):
            return f"unparseable worktree record {gitdir_file}"
        if worktree == entry or worktree.startswith(entry + os.sep):
            continue
        state = _target_state(target)
        if state == "unknown":
            return f"cannot stat the worktree {worktree} named by {gitdir_file}"
        if state == "present":
            return f"repository whose worktree {worktree} lives outside this entry"
    return None


@dataclass
class _Scan:
    size: int = 0
    newest: float = 0.0
    problems: list[str] = field(default_factory=list)
    linked: str | None = None


def _usage(st: os.stat_result) -> int:
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def scan(entry: str, top: os.stat_result) -> _Scan:
    """Size and newest mtime over the whole tree, never following a symlink."""
    result = _Scan(size=_usage(top), newest=top.st_mtime)
    if not stat.S_ISDIR(top.st_mode):
        return result
    if _looks_like_git_dir(entry):
        result.linked = _detached_git_dir(entry)  # the entry is itself a git dir

    def onerror(exc: OSError) -> None:
        result.problems.append(f"unreadable {exc.filename}: {exc.strerror}")

    for dirpath, dirnames, filenames in os.walk(entry, onerror=onerror, followlinks=False):
        for name in list(dirnames) + filenames:
            child = os.path.join(dirpath, name)
            try:
                st = os.lstat(child)
            except OSError as exc:
                result.problems.append(f"unreadable {child}: {exc.strerror}")
                continue
            result.size += _usage(st)
            result.newest = max(result.newest, st.st_mtime)
            if st.st_dev != top.st_dev:
                result.problems.append(f"{child} is on another filesystem")
                if name in dirnames:
                    dirnames.remove(name)
            if result.linked is None:
                if name == ".git" and stat.S_ISREG(st.st_mode):
                    result.linked = _linked_gitdir_reason(child, entry)
                elif stat.S_ISDIR(st.st_mode) and name == ".git":
                    # An ordinary clone's git dir may hold worktree records naming
                    # trees elsewhere.
                    result.linked = _main_repo_reason(child, entry)
                elif (
                    stat.S_ISDIR(st.st_mode)
                    and ".git" not in os.path.relpath(child, entry).split(os.sep)
                    and _looks_like_git_dir(child)
                ):
                    # Any other git dir records nothing about who uses it: the main
                    # worktree of a --separate-git-dir repository holds the only
                    # pointer, outside. A git dir inside a `.git` (a submodule's,
                    # under modules/) belongs to the clone around it.
                    result.linked = _detached_git_dir(child)
    return result


def classify(
    entry: str,
    *,
    device: int,
    worktrees: list[str],
    roots: list[str],
    grace_seconds: int,
    now: float,
    stores: list[str],
) -> Entry:
    """One owner class for one direct child of a root. Fails closed to ``unclassified``.

    ``device`` is the root's ``st_dev``: an entry on another one is a mount point.
    """
    try:
        top = os.lstat(entry)
    except OSError as exc:
        return Entry(entry, UNCLASSIFIED, reason=f"cannot stat: {exc.strerror}")
    identity = (top.st_dev, top.st_ino)
    if stat.S_ISLNK(top.st_mode):
        return Entry(entry, UNCLASSIFIED, reason="a symlink; never followed", identity=identity)
    if not (stat.S_ISDIR(top.st_mode) or stat.S_ISREG(top.st_mode)):
        return Entry(entry, UNCLASSIFIED, reason="neither a file nor a directory", identity=identity)
    if top.st_dev != device:
        return Entry(entry, UNCLASSIFIED, reason="a mount point", identity=identity)
    found = scan(entry, top)
    age = max(0, int(now - found.newest))
    reason = configured_root_reason(entry, roots)
    if reason:
        return Entry(entry, UNCLASSIFIED, found.size, age, reason, identity)
    reason = live_worktree_reason(entry, worktrees) or repository_store_reason(entry, stores)
    if reason:
        return Entry(entry, LIVE, found.size, age, reason, identity)
    if found.problems:
        shown = "; ".join(found.problems[:3])
        more = f" (+{len(found.problems) - 3} more)" if len(found.problems) > 3 else ""
        return Entry(entry, UNCLASSIFIED, found.size, age, shown + more, identity)
    if found.linked:
        return Entry(entry, LIVE, found.size, age, found.linked, identity)
    reason = grace_reason(now - found.newest, grace_seconds)
    if reason:
        return Entry(entry, GRACE, found.size, age, reason, identity)
    return Entry(entry, STALE, found.size, age, None, identity)


# --------------------------------------------------------------------------- #
# removal — the last gate, checked against the filesystem rather than the report
# --------------------------------------------------------------------------- #


def remove_entry(entry: str, root: str, identity: tuple[int, int] | None) -> None:
    """Remove one entry directly under ``root``, or raise ``Refused``."""
    name = os.path.basename(entry)
    if entry == root or name in ("", ".", "..") or os.path.dirname(entry) != root:
        raise Refused("not a direct child of its root")
    if os.path.realpath(root) != root or os.path.realpath(os.path.dirname(entry)) != root:
        raise Refused("the root no longer resolves to itself")
    try:
        st = os.lstat(entry)
    except OSError as exc:
        raise Refused(f"cannot stat: {exc.strerror}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise Refused("a symlink; never followed")
    if identity is None or (st.st_dev, st.st_ino) != identity:
        raise Refused("changed since it was classified")
    if stat.S_ISDIR(st.st_mode):
        if not shutil.rmtree.avoids_symlink_attacks:
            raise Refused("this platform's rmtree is not symlink-attack safe")
        shutil.rmtree(entry)
    elif stat.S_ISREG(st.st_mode):
        os.unlink(entry)
    else:
        raise Refused("neither a file nor a directory")


# --------------------------------------------------------------------------- #
# report + apply
# --------------------------------------------------------------------------- #


@dataclass
class RootReport:
    root: str
    status: str
    reason: str | None = None
    entries: list[Entry] = field(default_factory=list)
    device: int | None = field(default=None, repr=False)


def survey(settings: Settings, *, root: Path, now: float) -> list[RootReport]:
    guarded = guarded_paths(settings.repos)
    expanded: list[tuple[str, str, str | None]] = []
    for raw in settings.roots:
        try:
            path = expand_root(raw, root=root)
        except ValueError as exc:
            expanded.append((raw, "refused", str(exc)))
            continue
        path = path.rstrip("/") or "/"
        status, reason = validate_root(path, guarded)
        expanded.append((path, status, reason))
    # Every configured root is protected as an entry, refused ones included.
    protected = [path for path, _, _ in expanded if os.path.isabs(path)]
    worktrees = registered_worktrees(settings.repos)
    stores = repository_stores(worktrees)
    reports: list[RootReport] = []
    for path, status, reason in expanded:
        report = RootReport(path, status, reason)
        reports.append(report)
        if status != "ok":
            continue
        others = [r for r in protected if r != path]
        try:
            report.device = os.stat(path).st_dev
            names = sorted(os.listdir(path))
        except OSError as exc:
            report.status, report.reason = "refused", f"cannot list: {exc.strerror}"
            continue
        for name in names:
            report.entries.append(
                classify(
                    os.path.join(path, name),
                    device=report.device,
                    worktrees=worktrees,
                    stores=stores,
                    roots=others,
                    grace_seconds=settings.grace_seconds,
                    now=now,
                )
            )
    return reports


@dataclass
class Outcome:
    path: str
    action: str  # removed | kept | failed
    reason: str | None = None


def apply(
    reports: list[RootReport], settings: Settings, *, older_than: int, now_fn=time.time
) -> list[Outcome]:
    protected = [r.root for r in reports if os.path.isabs(r.root)]
    outcomes: list[Outcome] = []
    for report in reports:
        if report.status != "ok" or report.device is None:
            continue
        others = [r for r in protected if r != report.root]
        for entry in report.entries:
            if entry.owner != STALE or entry.age_seconds is None or entry.age_seconds < older_than:
                continue
            # Re-read everything the decision rests on, as close to the removal as
            # possible: a lane may have registered a worktree or written a file since
            # the report was taken.
            try:
                worktrees = registered_worktrees(settings.repos)
                stores = repository_stores(worktrees)
            except ConfigError as exc:
                outcomes.append(Outcome(entry.path, "kept", str(exc)))
                continue
            fresh = classify(
                entry.path,
                device=report.device,
                worktrees=worktrees,
                stores=stores,
                roots=others,
                grace_seconds=settings.grace_seconds,
                now=now_fn(),
            )
            if fresh.owner != STALE or fresh.age_seconds is None or fresh.age_seconds < older_than:
                outcomes.append(Outcome(entry.path, "kept", f"now {fresh.owner}: {fresh.reason}"))
                continue
            if fresh.identity != entry.identity:
                outcomes.append(Outcome(entry.path, "kept", "replaced since it was classified"))
                continue
            try:
                remove_entry(entry.path, report.root, fresh.identity)
            except Refused as exc:
                outcomes.append(Outcome(entry.path, "failed", f"refused: {exc}"))
            except OSError as exc:
                outcomes.append(Outcome(entry.path, "failed", f"{exc.filename}: {exc.strerror}"))
            else:
                outcomes.append(Outcome(entry.path, "removed"))
    return outcomes


def format_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GiB"  # pragma: no cover


def format_age(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    s = int(seconds)
    days, rest = divmod(s, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d{hours:02d}h"
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"


def render(reports: list[RootReport], outcomes: list[Outcome] | None) -> str:
    lines: list[str] = []
    for report in reports:
        if report.status != "ok":
            suffix = f": {report.reason}" if report.reason else ""
            lines.append(f"root {report.root} — {report.status}{suffix}")
            continue
        stale = sum(e.size_bytes for e in report.entries if e.owner == STALE)
        lines.append(f"root {report.root} — stale total {format_size(stale)}")
        for e in report.entries:
            note = f"  ({e.reason})" if e.reason else ""
            lines.append(
                f"  {e.owner:<13} {format_size(e.size_bytes):>10} {format_age(e.age_seconds):>7}"
                f"  {os.path.basename(e.path)}{note}"
            )
    for outcome in outcomes or []:
        note = f"  ({outcome.reason})" if outcome.reason else ""
        lines.append(f"{outcome.action} {outcome.path}{note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", default="config/dev-model.yaml", help="config file to read")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--apply", action="store_true", help="remove stale entries")
    parser.add_argument("--older-than", help="with --apply: minimum age of a removed entry")
    args = parser.parse_args(argv)
    if args.apply != (args.older_than is not None):
        parser.error("--apply and --older-than go together")

    root = repo_root()
    try:
        older_than = parse_age(args.older_than, "--older-than") if args.apply else None
        settings = load_settings(args.config, root=root)
        reports = survey(settings, root=root, now=time.time())
        outcomes = (
            apply(reports, settings, older_than=older_than) if older_than is not None else None
        )
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload: dict[str, object] = {
            "roots": [
                {
                    "root": r.root,
                    "status": r.status,
                    "reason": r.reason,
                    "entries": [
                        {k: v for k, v in asdict(e).items() if k != "identity"} for e in r.entries
                    ],
                }
                for r in reports
            ]
        }
        if outcomes is not None:
            payload["outcomes"] = [asdict(o) for o in outcomes]
        print(json.dumps(payload, indent=2))
    else:
        print(render(reports, outcomes))

    refused = any(r.status == "refused" for r in reports)
    failed = any(o.action == "failed" for o in outcomes or [])
    return 1 if refused or failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
