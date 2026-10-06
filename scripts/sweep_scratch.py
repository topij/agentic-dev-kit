#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Report, and on request remove, stale scratch under the configured artifact roots.

Session scratchpads and review-lens copies accumulate until the disk fills
(#900). This engine is the one boundary for clearing them: an allowlistable
command in place of ad-hoc ``rm -rf``.

The roots and the grace window are read from ``config/dev-model.yaml`` under
``scratch:``; nothing about where scratch lives is hardcoded here. Each direct
child of a root is one **entry**, and every entry gets exactly one owner class:

``live-worktree``
    The entry is, contains or sits inside a worktree registered with one of the
    ``scratch.worktree_repos`` (``git worktree list --porcelain``), or it holds a
    ``.git`` file pointing at a git dir that still exists outside the entry — a
    linked worktree of some repository this config does not name.
``in-grace``
    Something anywhere inside the entry was modified within
    ``scratch.grace_window``. The newest mtime over the whole tree decides, not the
    top directory's.
``stale``
    Neither of the above, and fully scanned.
``unclassified``
    Anything the engine could not fully classify: a symlink entry, an entry that
    is neither a file nor a directory, an unreadable path inside it, an entry that
    is or holds a mount point, or an entry that is or holds another configured
    root. Always kept.

Report mode (the default) changes nothing. ``--apply --older-than <age>`` removes
``stale`` entries whose newest mtime is at least ``<age>`` old, and nothing else.
Immediately before each removal it re-reads the worktree registrations and
re-scans the entry, and it removes only if the entry is still ``stale``, still old
enough, and is the same inode it classified.

A root is refused, and none of its entries touched, when it is not absolute after
placeholder expansion, is ``/``, contains ``..``, is itself a symlink, has a
symlink anywhere in its path, or is not a directory. A root that does not exist
is reported as absent. The root itself is never removed.

Usage (``<engine-dir>`` is ``paths.engines``):

    uv run <engine-dir>/sweep_scratch.py                          # report
    uv run <engine-dir>/sweep_scratch.py --json                   # machine-readable report
    uv run <engine-dir>/sweep_scratch.py --apply --older-than 7d  # remove stale entries

Ages are ``<n>s``, ``<n>m``, ``<n>h`` or ``<n>d``.

Exit codes:
    0 — report printed, or every eligible entry removed.
    1 — a configured root was refused, or an eligible entry could not be removed.
    2 — usage or config error, or the worktree registrations could not be read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
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
        return raw.format_map(values)
    except (KeyError, ValueError, IndexError) as exc:
        raise ValueError(f"unknown or malformed placeholder in {raw!r} ({exc})") from exc


def validate_root(path: str) -> tuple[str, str | None]:
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
    return "ok", None


# --------------------------------------------------------------------------- #
# worktree registrations
# --------------------------------------------------------------------------- #


def registered_worktrees(repos: list[Path]) -> list[str]:
    """Real paths of every worktree each repo registers. Any failure raises ConfigError."""
    found: list[str] = []
    for repo in repos:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise ConfigError(f"cannot run git for {repo}: {exc}") from exc
        if result.returncode != 0:
            raise ConfigError(
                f"git worktree list failed for {repo}: {result.stderr.strip() or result.returncode}"
            )
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                found.append(os.path.realpath(line[len("worktree "):]))
    if not found:
        raise ConfigError("no worktree registrations read; refusing to classify without them")
    return found


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


def configured_root_reason(path: str, roots: list[str]) -> str | None:
    # One direction only: an entry that IS or CONTAINS another root. Every entry of
    # a root nested inside this one sits under that root, and is not refused for it.
    for other in roots:
        if path == other or other.startswith(path + os.sep):
            return f"holds the configured root {other}"
    return None


def grace_reason(age: float, grace_seconds: int) -> str | None:
    if age < grace_seconds:
        return f"modified {format_age(age)} ago, inside the {format_age(grace_seconds)} grace window"
    return None


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
    target = os.path.realpath(target)
    if target.startswith(entry + os.sep):
        return None  # a submodule whose git dir lives inside the same entry
    if os.path.exists(target):
        return f"linked worktree {os.path.dirname(git_file)} of an unconfigured repository ({target})"
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
            if name == ".git" and stat.S_ISREG(st.st_mode) and result.linked is None:
                result.linked = _linked_gitdir_reason(child, entry)
    return result


def classify(
    entry: str,
    *,
    device: int,
    worktrees: list[str],
    roots: list[str],
    grace_seconds: int,
    now: float,
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
    reason = live_worktree_reason(entry, worktrees)
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
    expanded: list[tuple[str, str, str | None]] = []
    for raw in settings.roots:
        try:
            path = expand_root(raw, root=root)
        except ValueError as exc:
            expanded.append((raw, "refused", str(exc)))
            continue
        path = path.rstrip("/") or "/"
        status, reason = validate_root(path)
        expanded.append((path, status, reason))
    usable = [path for path, status, _ in expanded if status == "ok"]
    worktrees = registered_worktrees(settings.repos)
    reports: list[RootReport] = []
    for path, status, reason in expanded:
        report = RootReport(path, status, reason)
        reports.append(report)
        if status != "ok":
            continue
        others = [r for r in usable if r != path]
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
    usable = [r.root for r in reports if r.status == "ok"]
    outcomes: list[Outcome] = []
    for report in reports:
        if report.status != "ok" or report.device is None:
            continue
        others = [r for r in usable if r != report.root]
        for entry in report.entries:
            if entry.owner != STALE or entry.age_seconds is None or entry.age_seconds < older_than:
                continue
            # Re-read everything the decision rests on, as close to the removal as
            # possible: a lane may have registered a worktree or written a file since
            # the report was taken.
            try:
                worktrees = registered_worktrees(settings.repos)
            except ConfigError as exc:
                outcomes.append(Outcome(entry.path, "kept", str(exc)))
                continue
            fresh = classify(
                entry.path,
                device=report.device,
                worktrees=worktrees,
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
