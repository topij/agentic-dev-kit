"""Per-worktree state sandbox — ``DEVKIT_STATE_ROOT`` path resolution.

A single env var redirects **all** ``state/`` writes (``cache/``,
``automation-progress/``, ``history/``, …) under a per-worktree sandbox so
parallel agents never clobber each other's ``state/cache/``. **Default
(unset) = repo-root ``state/`` — zero behavior change in production.**

Resolution follows an env-override -> derived -> fail-open shape:

    state_root():
        $DEVKIT_STATE_ROOT      (must be absolute — raise if relative; a
                                  relative root would resolve against the
                                  caller's cwd, which is the wrong directory
                                  for any non-interactive caller)
        -> .devkit_state_root    (marker file walked up from cwd to the first
                                  .git ceiling; absolute path inside -> use;
                                  relative -> raise; unreadable/garbage -> log
                                  + fall through. Consulted only when the env
                                  var is unset.)
        -> <$DEVKIT_ROOT>/state
        -> <repo-root>/state    (walk-up marker discovery from cwd)

The marker file is the headless-lane mechanism: a background agent's Bash
tool calls don't share a shell, so an exported ``DEVKIT_STATE_ROOT`` doesn't
survive across calls. A launcher that spins up a headless/background lane can
instead write the sandbox path to ``<worktree>/.devkit_state_root`` and this
resolver reads it from disk — the only thing a stateless sequence of Bash
calls can reliably observe. A cron/CI job writes no marker and its worktrees
contain none, so it falls straight through to the repo-root default — byte-
identical, unchanged.

**Writes always go to the sandbox** (:func:`resolve_write_path`). When no
sandbox is active, :func:`resolve_write_path` additionally warns (or, opt-in
via ``DEVKIT_REFUSE_UNSANDBOXED_STATE``, refuses) if it detects an
*unsandboxed parallel/background lane* writing production ``state/`` — a
no-op on cron/CI and normal interactive paths.

**Reads of the shared surface (``state/cache/``) take the NEWER of the
sandbox copy vs the repo-root copy by mtime** (:func:`resolve_read_path`) —
*not* sandbox-first. Sandbox-first would let a worktree read its own
stale/empty cache and silently skip work; the newer-of cascade means a fresh
prod cache is preferred over a stale sandbox one, while a sandbox the
worktree just wrote wins over an older prod copy. Own-dir state
(``automation-progress/``, ``history/``) is write-then-read-own and does
*not* need the cascade — read those back via
``resolve_write_path(rel, mkdir=False)``.

A relative ``DEVKIT_ROOT: "."`` resolving against a cron/CI worktree's cwd is
a known footgun class: the root then points at whatever directory the runner
happened to be in, not the repo. This module therefore never returns a
*relative* path and rejects a relative ``DEVKIT_STATE_ROOT`` outright rather
than silently resolving it against cwd.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .paths import safe_join
from .repo_root import walk_up_for_marker

log = logging.getLogger("state_paths.resolver")

STATE_ROOT_ENV = "DEVKIT_STATE_ROOT"
ROOT_ENV = "DEVKIT_ROOT"
STATE_DIRNAME = "state"
# Sticky on-disk marker written by a headless-lane launcher at the worktree
# root, holding the absolute sandbox path. Walked up from cwd when
# DEVKIT_STATE_ROOT is unset — see :func:`_marker_state_root`.
STATE_ROOT_MARKER = ".devkit_state_root"
# Your cron/CI runner's job-name env var — exported for every scheduled /
# automated invocation. Its presence marks a legitimate no-sandbox repo-root
# ``state/`` writer, so the unsandboxed-lane guard skips it.
JOB_NAME_ENV = "JOB_NAME"
# Opt-in: make the unsandboxed-lane guard a hard error instead of a warning
# (teeth for an autonomous-batch launcher). Default = warn only, so cron/CI
# and normal-interactive paths stay byte-identical.
REFUSE_UNSANDBOXED_ENV = "DEVKIT_REFUSE_UNSANDBOXED_STATE"

# Warn-once dedupe for the unsandboxed-lane guard (per process). Never gates
# the refuse path — an opted-in hard error must fire on every offending write.
_unsandboxed_warned = False


class StateRootError(ValueError):
    """Raised when the state root cannot be resolved to an absolute path.

    Two cases: an explicitly-configured ``DEVKIT_STATE_ROOT`` that is
    relative, or discovery exhausted — no ``DEVKIT_ROOT`` and no repo marker
    walking up from cwd. The latter fails loud rather than silently writing
    real data to an arbitrary cwd directory — a silent fallback here would be
    invisible to anything that expects state files to live in a known place.
    """


def repo_state_root() -> Path:
    """The canonical *production* ``state/`` directory — the sandbox's prod twin.

    Resolution: ``<$DEVKIT_ROOT>/state`` -> ``<repo-root>/state`` (walk-up
    marker discovery). Deliberately ignores ``$DEVKIT_STATE_ROOT`` — this is
    the prod side of the read cascade. Always absolute.

    Raises :class:`StateRootError` when neither ``DEVKIT_ROOT`` is set nor a
    repo marker is found walking up from cwd: state files hold real data, so a
    lost root must fail loud, not silently land in an arbitrary directory.
    """
    root = os.environ.get(ROOT_ENV)
    if root:
        # Honor the established DEVKIT_ROOT convention but guarantee an
        # absolute result (a relative root is a cwd-dependent footgun).
        base = Path(root)
        if not base.is_absolute():
            base = base.resolve()
        return base / STATE_DIRNAME
    repo = walk_up_for_marker(Path.cwd())
    if repo is not None:
        return repo / STATE_DIRNAME
    raise StateRootError(
        f"cannot resolve the state root: ${ROOT_ENV} is unset and no .git "
        f"marker was found walking up from {Path.cwd()}. Set ${ROOT_ENV} "
        f"(or ${STATE_ROOT_ENV}) to an absolute path."
    )


def _marker_state_root(start: Path | None = None) -> Path | None:
    """Sandbox root from a ``.devkit_state_root`` marker, walked up from cwd.

    The headless-lane mechanism: a launcher that spins up a headless /
    background worktree writes the marker at the worktree root holding the
    absolute sandbox path, so a background agent's stateless Bash calls (no
    shared shell, no surviving ``export``) resolve the sandbox from disk.

    Discovery walks up from ``start`` (default :func:`Path.cwd` — **not**
    ``DEVKIT_ROOT``, which points at the *main* checkout for the read cascade;
    the marker lives in the *worktree*). The walk is ceilinged at the first
    directory carrying a ``.git`` entry — the worktree root, where the marker
    lives as a sibling (a ``.git`` *file* in a linked worktree, a dir in a
    regular checkout). The marker is checked at that level *before* the
    ceiling stops the walk, so it is found; the ceiling only prevents climbing
    into an unintended ancestor.

    Returns the absolute path inside the marker, or ``None`` when no marker is
    found (fall through to the default). Raises :class:`StateRootError` for a
    *relative* path inside the marker — mirroring the env-var rule. An
    unreadable / empty / non-path marker is logged and treated as absent: it
    falls through to the default, never a silent redirect.
    """
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        marker = candidate / STATE_ROOT_MARKER
        if marker.is_file():
            try:
                raw = marker.read_text(encoding="utf-8").strip()
            except OSError as exc:
                log.warning("state_paths: could not read marker %s (%s); ignoring", marker, exc)
                return None
            if not raw:
                log.warning("state_paths: marker %s is empty; ignoring", marker)
                return None
            path = Path(raw)
            if not path.is_absolute():
                raise StateRootError(
                    f"{STATE_ROOT_MARKER} at {marker} must contain an absolute path, got {raw!r} "
                    "(a relative state root resolves against the caller's cwd)."
                )
            return path
        # Ceiling: stop once we've checked the worktree root (the .git level) so
        # the walk can't climb into an unintended ancestor (a stray marker there
        # would otherwise redirect this checkout). Checked AFTER the marker so a
        # marker sitting beside .git is still found.
        if (candidate / ".git").exists():
            break
    return None


def state_root() -> Path:
    """Absolute sandbox root that **writes** land under.

    ``$DEVKIT_STATE_ROOT`` (must be absolute — raises :class:`StateRootError`
    if relative) -> :func:`_marker_state_root` (consulted only when the env
    var is unset) -> :func:`repo_state_root`. Never returns a relative path.
    """
    explicit = os.environ.get(STATE_ROOT_ENV)
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            raise StateRootError(
                f"${STATE_ROOT_ENV} must be an absolute path, got {explicit!r} "
                "(a relative state root resolves against the caller's cwd)."
            )
        return candidate
    marker = _marker_state_root()
    if marker is not None:
        return marker
    return repo_state_root()


class UnsandboxedStateWriteError(RuntimeError):
    """Raised by the unsandboxed-lane guard when an unsandboxed parallel /
    background lane is about to write repo-root ``state/`` and
    ``DEVKIT_REFUSE_UNSANDBOXED_STATE`` opted into hard-fail. Default
    behavior is a warning, not this error."""


def _is_truthy_env(name: str) -> bool:
    """True iff env var ``name`` is set to a non-blank value."""
    val = os.environ.get(name)
    return bool(val and val.strip())


def _guard_unsandboxed_write() -> None:
    """Warn (or, opt-in, refuse) when a ``state/`` write would land in
    repo-root ``state/`` from an **unsandboxed parallel/background lane**.

    A parallel or background-agent lane that writes ``state/cache/`` must run
    sandboxed (``DEVKIT_STATE_ROOT`` or the marker file) so it can't clobber
    production state. The hard part is that **cron/CI** also writes repo-root
    ``state/`` with no sandbox and that is correct — so the guard fires only
    on the combination that is unique to a parallel/background lane and is
    neither cron/CI nor normal interactive dev. All must hold:

    - **no sandbox** — ``DEVKIT_STATE_ROOT`` unset/blank AND no
      ``.devkit_state_root`` marker walking up from cwd; **and**
    - **not cron/CI** — ``JOB_NAME`` unset/blank (your cron/CI runner's
      job-name env var, exported for every scheduled invocation); **and**
    - **a linked worktree** — the discovered repo root's ``.git`` is a *file*
      (``git worktree add`` writes a gitdir pointer file), which the main
      checkout (a ``.git`` directory) is not.

    Warn-only by default (logged **once** per process via
    ``_unsandboxed_warned``); set :data:`REFUSE_UNSANDBOXED_ENV` to raise
    :class:`UnsandboxedStateWriteError` instead. Fail-open throughout: any
    ambiguity (no discoverable repo root, a relative/garbage marker that
    signals a sandbox *was* intended) stays silent, so this never turns a
    cron/CI or normal-dev write into a false alarm.
    """
    global _unsandboxed_warned
    # Cheapest exits first so cron/sandboxed paths never touch the filesystem.
    # Mirror state_root()'s RAW truthiness for the sandbox var (``if explicit:``)
    # rather than _is_truthy_env's stripped form: a whitespace-only value is "set"
    # to state_root() (it raises StateRootError on the relative path), so the write
    # never reaches prod — the guard must treat it as a configured sandbox too, not
    # warn about an unsandboxed write that won't happen.
    if os.environ.get(STATE_ROOT_ENV):
        return  # explicit sandbox configured (state_root resolves/validates it)
    if _is_truthy_env(JOB_NAME_ENV):
        return  # cron/CI — a legitimate no-sandbox writer
    try:
        if _marker_state_root() is not None:
            return  # marker sandbox active
    except StateRootError:
        return  # a relative/garbage marker means a sandbox WAS intended — not our case
    repo = walk_up_for_marker(Path.cwd())
    if repo is None or not (repo / ".git").is_file():
        return  # main checkout (.git dir) or no marker → normal dev, not a lane
    msg = (
        f"writing repo-root state/ from an unsandboxed parallel lane — no "
        f"${STATE_ROOT_ENV}, no {STATE_ROOT_MARKER} marker, ${JOB_NAME_ENV} unset, "
        f"in a linked worktree ({repo}). A parallel or background-agent lane that "
        f"writes state/cache/ should run sandboxed so it can't clobber production "
        f"state: launch it via a sandboxed worktree launcher, or export "
        f"${STATE_ROOT_ENV} to an absolute sandbox path. "
        f"(Set ${REFUSE_UNSANDBOXED_ENV}=1 to make this a hard error.)"
    )
    if _is_truthy_env(REFUSE_UNSANDBOXED_ENV):
        raise UnsandboxedStateWriteError(f"✗ Refusing: {msg}")
    if not _unsandboxed_warned:
        log.warning("state_paths: ⚠ %s", msg)
        _unsandboxed_warned = True


def resolve_write_path(rel: str, *, mkdir: bool = True) -> Path:
    """Absolute path a state file is **written** to: always under :func:`state_root`.

    ``rel`` is the path relative to ``state/`` (e.g. ``"cache/report_2026-05-24.json"``).
    Absolute fragments and ``..`` traversal that escapes the sandbox are
    rejected (:class:`PathTraversalError`).

    When ``mkdir`` is True (default) the parent directory is created.
    Fail-open: if ``mkdir`` raises ``OSError`` the error is logged and the
    sandbox path is still returned (the caller's own write then fails open).
    The path is **never** redirected to repo-root ``state/`` on failure —
    silently writing to prod would defeat the very isolation the sandbox
    exists to provide. Pass ``mkdir=False`` to read back a file the caller
    wrote earlier (own-dir state) without touching the fs.

    Before resolving, :func:`_guard_unsandboxed_write` warns (or, opt-in,
    refuses) if this is an unsandboxed parallel/background lane about to
    write production ``state/`` — a no-op on cron/CI and normal interactive
    paths.

    Raises :class:`UnsandboxedStateWriteError` when
    ``DEVKIT_REFUSE_UNSANDBOXED_STATE`` is truthy and this call would write
    repo-root ``state/`` from an unsandboxed parallel/background lane. (Also
    raises :class:`StateRootError` if an explicit ``DEVKIT_STATE_ROOT`` is
    relative — see :func:`state_root`.)
    """
    _guard_unsandboxed_write()
    target = safe_join(state_root(), rel)
    if mkdir:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            log.warning("state_paths: could not create %s (%s); returning the path anyway", target.parent, exc)
    return target


def _safe_mtime(path: Path) -> float | None:
    """``path``'s mtime, or ``None`` if it does not exist / cannot be stat'd (fail-open)."""
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def resolve_read_path(rel: str) -> Path:
    """Absolute path a shared-surface (``cache/``) state file is **read** from.

    Returns the **newer** (by mtime) of the sandbox copy and the repo-root copy
    — never sandbox-first, so a fresh prod cache is never shadowed by a stale
    sandbox one. Falls back to whichever exists when only one does; to the
    sandbox path when neither does (so the caller's "missing -> fetch" branch
    fires against the sandbox and the fetched file lands in the sandbox).

    On equal mtime the sandbox wins (it is the worktree's own write target).

    Tie-break is file mtime, not a ``fetched_at`` field some cache files
    carry — mtime needs no parse and works for any state file. A
    ``fetched_at``-aware refinement is possible later if ``git checkout``
    perturbing mtimes proves to matter in practice.

    If the prod twin can't be resolved (an explicit ``$DEVKIT_STATE_ROOT``
    with no discoverable repo root), the sandbox is the only source — read
    from it rather than propagating the discovery error.
    """
    sandbox = safe_join(state_root(), rel)
    try:
        prod = safe_join(repo_state_root(), rel)
    except StateRootError:
        return sandbox
    if sandbox == prod:
        # No sandbox configured (or it coincides with prod) — single source.
        return sandbox
    sandbox_mtime = _safe_mtime(sandbox)
    prod_mtime = _safe_mtime(prod)
    if sandbox_mtime is None and prod_mtime is None:
        return sandbox
    if sandbox_mtime is None:
        return prod
    if prod_mtime is None:
        return sandbox
    return sandbox if sandbox_mtime >= prod_mtime else prod


def glob_state(subdir: str, pattern: str) -> list[Path]:
    """All ``state/<subdir>/`` files matching ``pattern``, unioned across the prod
    and sandbox state roots, sorted by filename.

    The general-purpose companion to :func:`resolve_read_path`. Works for any
    ``state/`` subtree — ``cache/``, ``history/<subsystem>/``, etc. On a
    filename collision the **newer** copy (by mtime) wins — never
    sandbox-first, matching the read cascade so a stale sandbox copy can't
    shadow a fresher prod file. When no ``DEVKIT_STATE_ROOT`` sandbox is
    configured the two roots coincide and this is exactly the prior
    single-dir glob (byte-identical result), so production behavior is
    unchanged.

    Callers anchor ``DEVKIT_ROOT`` (``os.environ.setdefault(...)``) so the prod
    twin resolves cwd-independently. Fail-open per side: if the prod twin
    can't be resolved (an explicit ``$DEVKIT_STATE_ROOT`` with no
    discoverable repo root) only the sandbox is scanned, mirroring
    :func:`resolve_read_path`.
    """
    sandbox = state_root()
    try:
        prod: Path | None = repo_state_root()
    except StateRootError:
        prod = None
    # Iterate the sandbox LAST so it wins an mtime tie (the worktree's own write
    # target); skip the redundant pass when no sandbox is configured (roots equal).
    roots: list[Path] = []
    if prod is not None:
        roots.append(prod)
    if sandbox not in roots:
        roots.append(sandbox)

    by_name: dict[str, Path] = {}
    for root in roots:
        directory = safe_join(root, subdir)
        if not directory.is_dir():
            continue
        for path in directory.glob(pattern):
            current = by_name.get(path.name)
            if current is None:
                by_name[path.name] = path
                continue
            # Keep the newer copy. Fail-open per side: an unstatable candidate
            # never displaces a good incumbent; an unstatable incumbent yields to
            # a statable candidate; both-unstatable keeps the incumbent.
            new_m, cur_m = _safe_mtime(path), _safe_mtime(current)
            if new_m is not None and (cur_m is None or new_m >= cur_m):
                by_name[path.name] = path
    return sorted(by_name.values(), key=lambda p: p.name)


def glob_state_cache(pattern: str) -> list[Path]:
    """All ``state/cache/`` files matching ``pattern``, unioned across the prod
    and sandbox state roots, sorted by filename.

    Thin delegate to :func:`glob_state` scoped to the ``cache/`` subtree. See
    that function for the full semantics (newer-by-mtime collision resolution,
    fail-open when the prod root is unresolvable, byte-identical result with
    ``DEVKIT_STATE_ROOT`` unset).
    """
    return glob_state("cache", pattern)
