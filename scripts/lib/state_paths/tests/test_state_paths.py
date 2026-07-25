"""Unit tests for the per-worktree state sandbox (``state_paths.resolver``).

These tests sign off the cascade semantics: writes always go to the sandbox;
reads of the shared surface take the *newer* of sandbox vs prod; a relative
``DEVKIT_STATE_ROOT`` raises; everything fails open.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

import state_paths.resolver as _sp
from state_paths.paths import PathTraversalError
from state_paths.resolver import (
    CI_ENV_VARS_ENV,
    DEFAULT_CI_ENV_VARS,
    JOB_NAME_ENV,
    REFUSE_UNSANDBOXED_ENV,
    ROOT_ENV,
    STATE_ROOT_ENV,
    STATE_ROOT_MARKER,
    StateRootError,
    UnsandboxedStateWriteError,
    _marker_state_root,
    ci_env_vars,
    glob_state,
    glob_state_cache,
    repo_state_root,
    resolve_read_path,
    resolve_write_path,
    state_root,
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Start each test with every sandbox signal neutral — env AND cwd.

    Every cron/CI marker var must be cleared, not just ``JOB_NAME``: this suite
    runs *in* GitHub Actions, which exports ``CI`` / ``GITHUB_ACTIONS``, so a
    leaked value would silently exempt every guard test from the very guard it
    asserts on.

    The **cwd** matters for exactly the same reason and was the half this
    fixture used to miss (issue #10). ``_marker_state_root`` discovers a sandbox
    by walking up from ``Path.cwd()``, so a ``.devkit_state_root`` marker
    anywhere at or above the invocation directory redirects the resolver and the
    "no sandbox configured" assertions fail — while every env var is dutifully
    unset. It stayed hidden because CI runs from a marker-free checkout; it
    surfaces the moment the suite runs from inside a headless lane worktree,
    which is precisely what a lane agent does before pushing. A gate that goes
    red for reasons unrelated to the diff teaches agents to ignore a red gate.

    Chdir'ing to a fresh ``tmp_path`` makes "no marker above me" the explicit
    starting state instead of an accident of where pytest was invoked. Tests
    that care about cwd still ``monkeypatch.chdir`` themselves afterwards, which
    overrides this — so the fixture makes the default safe without taking the
    control away from the tests that use it. Only two tests were ever
    cwd-sensitive without setting their own (the two that failed); the change is
    also strictly *stricter*, since three others used to pass by accidentally
    discovering the real repo root.

    Not hermetic, and deliberately so: ``tmp_path`` is marker-free because of
    where ``TMPDIR`` points, so pointing ``TMPDIR`` inside a marker-carrying
    worktree still fails. Closing that would need a ``.git`` ceiling sentinel
    inside ``tmp_path``, which the "no ``.git`` anywhere up → raise" tests
    require the *absence* of. The lane case this fixes is the one that actually
    happens.
    """
    monkeypatch.delenv(STATE_ROOT_ENV, raising=False)
    monkeypatch.delenv(ROOT_ENV, raising=False)
    monkeypatch.delenv(REFUSE_UNSANDBOXED_ENV, raising=False)
    monkeypatch.delenv(CI_ENV_VARS_ENV, raising=False)
    for name in DEFAULT_CI_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    _sp._unsandboxed_warned = False


def _touch(path: Path, *, mtime: float | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


# --------------------------------------------------------------------------- #
# state_root()
# --------------------------------------------------------------------------- #


def test_state_root_defaults_to_repo_root_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    assert state_root() == tmp_path / "state"


def test_state_root_explicit_absolute_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "wt" / "state-sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))  # ignored — explicit sandbox wins
    assert state_root() == sandbox


def test_state_root_relative_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(STATE_ROOT_ENV, "rel/state-sandbox")
    with pytest.raises(StateRootError):
        state_root()


def test_state_root_dot_relative_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # A relative-dot root resolving against cwd — the shape that silently
    # breaks if this rule isn't enforced.
    monkeypatch.setenv(STATE_ROOT_ENV, ".")
    with pytest.raises(StateRootError):
        state_root()


def test_state_root_unset_discovers_repo_marker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert state_root() == tmp_path.resolve() / "state"


def test_state_root_no_git_marker_anywhere_up_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # .git-only discovery: with no .git anywhere up the tree — even from a
    # nested cwd — an unrelated directory must never be mistaken for the repo
    # root. Discovery exhausts and raises rather than falsely adopting one.
    nested = tmp_path / "some" / "nested" / "dir"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    with pytest.raises(StateRootError):
        repo_state_root()


def test_repo_state_root_raises_when_exhausted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # No env roots, no marker anywhere up the tree → fail loud rather than
    # silently writing real data to an arbitrary cwd directory.
    monkeypatch.chdir(tmp_path)
    with pytest.raises(StateRootError):
        repo_state_root()


def test_state_root_returns_absolute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    assert state_root().is_absolute()


# --------------------------------------------------------------------------- #
# _marker_state_root() + state_root() marker fallback
# --------------------------------------------------------------------------- #


def _make_worktree(parent: Path) -> Path:
    """A worktree-like dir: a ``.git`` *file* (the linked-worktree shape) at its root."""
    wt = parent / "wt"
    wt.mkdir(parents=True)
    (wt / ".git").write_text("gitdir: /somewhere/.git/worktrees/wt\n", encoding="utf-8")
    return wt


def test_marker_found_walking_up(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # The headless-lane shape: marker at the worktree root, cwd a nested subdir.
    wt = _make_worktree(tmp_path)
    sandbox = tmp_path / "state-sandbox"
    (wt / STATE_ROOT_MARKER).write_text(str(sandbox), encoding="utf-8")
    nested = wt / "libs" / "some-package"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert _marker_state_root() == sandbox
    assert state_root() == sandbox


def test_marker_beside_git_is_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # cwd IS the worktree root: the marker (beside .git) is checked BEFORE the
    # ceiling break, so it's found — the .git level is inclusive.
    wt = _make_worktree(tmp_path)
    sandbox = tmp_path / "sandbox"
    (wt / STATE_ROOT_MARKER).write_text(str(sandbox), encoding="utf-8")
    monkeypatch.chdir(wt)
    assert _marker_state_root() == sandbox


def test_env_var_wins_over_marker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    wt = _make_worktree(tmp_path)
    (wt / STATE_ROOT_MARKER).write_text(str(tmp_path / "marker-sandbox"), encoding="utf-8")
    env_sandbox = tmp_path / "env-sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(env_sandbox))
    monkeypatch.chdir(wt)
    assert state_root() == env_sandbox  # env var wins; the marker is not consulted


def test_marker_relative_path_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Mirrors the env-var rule: a relative path resolves against cwd.
    wt = _make_worktree(tmp_path)
    (wt / STATE_ROOT_MARKER).write_text("rel/sandbox", encoding="utf-8")
    monkeypatch.chdir(wt)
    with pytest.raises(StateRootError):
        _marker_state_root()
    with pytest.raises(StateRootError):
        state_root()


def test_marker_empty_falls_through(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # An empty/whitespace marker is garbage — logged and ignored, falling through
    # to the repo-root default. Never a silent redirect.
    wt = _make_worktree(tmp_path)
    (wt / STATE_ROOT_MARKER).write_text("   \n", encoding="utf-8")
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    monkeypatch.chdir(wt)
    assert _marker_state_root() is None
    assert state_root() == tmp_path / "state"


def test_marker_directory_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # A marker that is a directory is not a file → skipped, falls through.
    wt = _make_worktree(tmp_path)
    (wt / STATE_ROOT_MARKER).mkdir()
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    monkeypatch.chdir(wt)
    assert _marker_state_root() is None
    assert state_root() == tmp_path / "state"


def test_marker_ceiling_stops_at_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # A marker ABOVE the .git ceiling must NOT be found — the walk stops at the
    # worktree root so a stray ancestor marker can't redirect this checkout.
    (tmp_path / STATE_ROOT_MARKER).write_text(str(tmp_path / "ancestor-sandbox"), encoding="utf-8")
    wt = _make_worktree(tmp_path)  # wt/.git is the ceiling; wt has no marker of its own
    monkeypatch.chdir(wt)
    assert _marker_state_root() is None  # ancestor marker never reached


def test_no_marker_byte_identical_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # The load-bearing invariant (cron/CI's shape): no env var AND no marker →
    # repo-root default, byte-identical to the no-sandbox default.
    wt = _make_worktree(tmp_path)  # has .git but NO marker
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    monkeypatch.chdir(wt)
    assert _marker_state_root() is None
    assert state_root() == tmp_path / "state"


# --------------------------------------------------------------------------- #
# repo_state_root() — the prod twin, ignores the sandbox var
# --------------------------------------------------------------------------- #


def test_repo_state_root_ignores_sandbox_var(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    prod = tmp_path / "prod"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(prod))
    assert state_root() == sandbox
    assert repo_state_root() == prod / "state"


def test_repo_state_root_relative_root_made_absolute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ROOT_ENV, "sub")
    result = repo_state_root()
    assert result.is_absolute()
    assert result == (tmp_path / "sub").resolve() / "state"


# --------------------------------------------------------------------------- #
# resolve_write_path() — always under the sandbox
# --------------------------------------------------------------------------- #


def test_resolve_write_path_under_sandbox_and_mkdirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(STATE_ROOT_ENV, str(tmp_path))
    target = resolve_write_path("cache/report_2026-05-24.json")
    assert target == tmp_path / "cache" / "report_2026-05-24.json"
    assert target.parent.is_dir()  # mkdir happened


def test_resolve_write_path_no_mkdir_leaves_fs_untouched(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(STATE_ROOT_ENV, str(tmp_path))
    target = resolve_write_path("automation-progress/job_latest.json", mkdir=False)
    assert target == tmp_path / "automation-progress" / "job_latest.json"
    assert not target.parent.exists()


def test_resolve_write_path_rejects_absolute_fragment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(STATE_ROOT_ENV, str(tmp_path))
    with pytest.raises(PathTraversalError):
        resolve_write_path("/etc/passwd")


def test_resolve_write_path_rejects_parent_traversal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(STATE_ROOT_ENV, str(tmp_path / "sandbox"))
    with pytest.raises(PathTraversalError):
        resolve_write_path("../escape.json")


def test_resolve_write_path_fail_open_returns_sandbox_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Sandbox root is a *file*, so mkdir of a child dir raises OSError. Fail-open
    # returns the sandbox path without crashing and does NOT redirect to prod —
    # redirecting would write into prod state/ and defeat isolation.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir", encoding="utf-8")
    prod = tmp_path / "prod"
    monkeypatch.setenv(STATE_ROOT_ENV, str(blocker))
    monkeypatch.setenv(ROOT_ENV, str(prod))
    target = resolve_write_path("cache/x.json")
    assert target == blocker / "cache" / "x.json"  # sandbox path, not prod
    assert not (prod / "state").exists()  # prod untouched


# --------------------------------------------------------------------------- #
# resolve_read_path() — newer-of cascade (cache surface)
# --------------------------------------------------------------------------- #


def test_resolve_read_path_single_source_when_no_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))  # no STATE_ROOT → sandbox == prod
    assert resolve_read_path("cache/x.json") == tmp_path / "state" / "cache" / "x.json"


def test_resolve_read_path_prefers_newer_prod(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    prod = tmp_path / "prod" / "state"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    _touch(sandbox / "cache" / "x.json", mtime=1000.0)
    _touch(prod / "cache" / "x.json", mtime=2000.0)
    assert resolve_read_path("cache/x.json") == prod / "cache" / "x.json"


def test_resolve_read_path_prefers_newer_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    prod = tmp_path / "prod" / "state"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    _touch(sandbox / "cache" / "x.json", mtime=3000.0)
    _touch(prod / "cache" / "x.json", mtime=2000.0)
    assert resolve_read_path("cache/x.json") == sandbox / "cache" / "x.json"


def test_resolve_read_path_equal_mtime_prefers_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    prod = tmp_path / "prod" / "state"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    _touch(sandbox / "cache" / "x.json", mtime=2000.0)
    _touch(prod / "cache" / "x.json", mtime=2000.0)
    assert resolve_read_path("cache/x.json") == sandbox / "cache" / "x.json"


def test_resolve_read_path_only_prod_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    prod = tmp_path / "prod" / "state"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    _touch(prod / "cache" / "x.json")
    assert resolve_read_path("cache/x.json") == prod / "cache" / "x.json"


def test_resolve_read_path_only_sandbox_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    _touch(sandbox / "cache" / "x.json")
    assert resolve_read_path("cache/x.json") == sandbox / "cache" / "x.json"


def test_resolve_read_path_neither_exists_returns_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(ROOT_ENV, str(tmp_path / "prod"))
    # Missing on both sides → sandbox path, so the caller's "missing → fetch"
    # branch writes the fetched file into the sandbox.
    assert resolve_read_path("cache/x.json") == sandbox / "cache" / "x.json"


def test_resolve_read_path_sandbox_only_when_prod_unresolvable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Explicit sandbox but no DEVKIT_ROOT and a marker-less cwd → the prod
    # twin can't be resolved; read from the sandbox rather than raising.
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.chdir(tmp_path)
    assert resolve_read_path("cache/x.json") == sandbox / "cache" / "x.json"


# --------------------------------------------------------------------------- #
# glob_state_cache() — union glob over the cache surface
# --------------------------------------------------------------------------- #

GLOB = "widget-metrics_*.json"


def test_glob_state_cache_no_sandbox_is_plain_prod_glob(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # No DEVKIT_STATE_ROOT → roots coincide → exactly a single-dir glob.
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    f = _touch(tmp_path / "state" / "cache" / "widget-metrics_2026-05-24.json")
    assert glob_state_cache(GLOB) == [f]


def test_glob_state_cache_unions_distinct_filenames(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    _touch(prod / "state" / "cache" / "widget-metrics_2026-05-20.json")
    _touch(sandbox / "cache" / "widget-metrics_2026-05-21.json")
    names = {p.name for p in glob_state_cache(GLOB)}
    assert names == {"widget-metrics_2026-05-20.json", "widget-metrics_2026-05-21.json"}


def test_glob_state_cache_collision_prefers_newer_prod(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    name = "widget-metrics_2026-05-22.json"
    _touch(sandbox / "cache" / name, mtime=1000.0)
    prod_file = _touch(prod / "state" / "cache" / name, mtime=2000.0)  # fresher
    result = glob_state_cache(GLOB)
    assert result == [prod_file]  # newer prod wins, never sandbox-first


def test_glob_state_cache_collision_prefers_newer_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    name = "widget-metrics_2026-05-22.json"
    _touch(prod / "state" / "cache" / name, mtime=1000.0)
    sandbox_file = _touch(sandbox / "cache" / name, mtime=2000.0)  # fresher
    result = glob_state_cache(GLOB)
    assert result == [sandbox_file]


def test_glob_state_cache_equal_mtime_prefers_sandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    name = "widget-metrics_2026-05-22.json"
    _touch(prod / "state" / "cache" / name, mtime=2000.0)
    sandbox_file = _touch(sandbox / "cache" / name, mtime=2000.0)
    assert glob_state_cache(GLOB) == [sandbox_file]  # tie → sandbox (iterated last)


def test_glob_state_cache_sandbox_only_when_prod_unresolvable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Explicit sandbox, no DEVKIT_ROOT, marker-less cwd → prod twin can't
    # resolve; scan the sandbox only rather than raising.
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.chdir(tmp_path)
    f = _touch(sandbox / "cache" / "widget-metrics_2026-05-24.json")
    assert glob_state_cache(GLOB) == [f]


def test_glob_state_cache_empty_when_no_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))  # no cache dir created
    assert glob_state_cache(GLOB) == []


# --------------------------------------------------------------------------- #
# glob_state() — union glob over an arbitrary state subtree
# --------------------------------------------------------------------------- #


def test_glob_state_cache_subdir_matches_glob_state_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``glob_state("cache", pattern)`` is byte-identical to ``glob_state_cache(pattern)``
    with DEVKIT_STATE_ROOT unset (single-dir case)."""
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    f = _touch(tmp_path / "state" / "cache" / "widget-metrics_2026-05-24.json")
    assert glob_state("cache", GLOB) == [f]
    assert glob_state("cache", GLOB) == glob_state_cache(GLOB)


def test_glob_state_non_cache_subdir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``glob_state`` reaches into a non-cache subtree (e.g. ``history/exports``)."""
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    f = _touch(tmp_path / "state" / "history" / "exports" / "export_2026-05-24.json")
    assert glob_state("history/exports", "export_*.json") == [f]


def test_glob_state_unions_distinct_filenames_non_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    _touch(prod / "state" / "history" / "exports" / "export_2026-05-20.json")
    _touch(sandbox / "history" / "exports" / "export_2026-05-21.json")
    # Assert the list (not a set) to verify the sorted-by-filename ordering guarantee.
    names = [p.name for p in glob_state("history/exports", "export_*.json")]
    assert names == ["export_2026-05-20.json", "export_2026-05-21.json"]


def test_glob_state_collision_newer_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prod, sandbox = tmp_path / "prod", tmp_path / "sandbox"
    monkeypatch.setenv(ROOT_ENV, str(prod))
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    name = "export_2026-05-22.json"
    _touch(sandbox / "history" / "exports" / name, mtime=1000.0)
    prod_file = _touch(prod / "state" / "history" / "exports" / name, mtime=2000.0)
    assert glob_state("history/exports", "export_*.json") == [prod_file]


def test_glob_state_empty_when_no_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ROOT_ENV, str(tmp_path))
    assert glob_state("history/exports", "export_*.json") == []


def test_glob_state_sandbox_only_when_prod_unresolvable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv(STATE_ROOT_ENV, str(sandbox))
    monkeypatch.chdir(tmp_path)
    f = _touch(sandbox / "history" / "exports" / "export_2026-05-24.json")
    assert glob_state("history/exports", "export_*.json") == [f]


# --------------------------------------------------------------------------- #
# resolve_write_path() unsandboxed-lane guard
# --------------------------------------------------------------------------- #

GUARD_LOGGER = "state_paths.resolver"


def _make_lane_worktree(parent: Path) -> Path:
    """A linked-worktree checkout: ``.git`` is a FILE (the gitdir pointer)."""
    wt = parent / "wt"
    wt.mkdir(parents=True)
    (wt / ".git").write_text("gitdir: /somewhere/.git/worktrees/wt\n", encoding="utf-8")
    return wt


def _make_main_checkout(parent: Path) -> Path:
    """A primary checkout: ``.git`` is a DIRECTORY."""
    co = parent / "checkout"
    (co / ".git").mkdir(parents=True)
    return co


def _guard_warned(caplog: pytest.LogCaptureFixture) -> bool:
    return any("unsandboxed parallel lane" in r.message for r in caplog.records)


def test_guard_warns_for_unsandboxed_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A linked worktree with no sandbox, no marker, and no JOB_NAME → warn, and
    the write still resolves to the worktree's repo-root state/ (warn, not block)."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        target = resolve_write_path("cache/x.json")
    assert _guard_warned(caplog)
    assert target == wt.resolve() / "state" / "cache" / "x.json"


def test_guard_silent_for_cron_job_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """JOB_NAME set → a legitimate cron/CI no-sandbox writer, even in a worktree → no warn."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(JOB_NAME_ENV, "nightly-report-job")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


@pytest.mark.parametrize("var", DEFAULT_CI_ENV_VARS)
def test_guard_silent_for_every_default_ci_signal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    var: str,
) -> None:
    """Any default cron/CI marker exempts the write. `CI` / `GITHUB_ACTIONS` are
    the ones that matter most: GitHub Actions exports those and no JOB_NAME, so
    with the old Jenkins-only check the guard misfired on every CI write."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(var, "true")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_guard_warns_for_blank_ci_signal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A whitespace-only marker is not "set" — the exemption needs a real value."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv("CI", "   ")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert _guard_warned(caplog)


def test_ci_env_vars_override_replaces_the_default_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """DEVKIT_CI_ENV_VARS replaces rather than extends, so it can also NARROW the
    exemption — a runner that must stay guarded despite exporting CI."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(CI_ENV_VARS_ENV, " MY_RUNNER , OTHER_RUNNER ")
    assert ci_env_vars() == ("MY_RUNNER", "OTHER_RUNNER")

    monkeypatch.setenv("CI", "true")  # no longer in the list
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert _guard_warned(caplog)

    _sp._unsandboxed_warned = False
    caplog.clear()
    monkeypatch.setenv("OTHER_RUNNER", "job-17")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/y.json")
    assert not _guard_warned(caplog)


def test_blank_ci_env_vars_override_keeps_the_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """`export DEVKIT_CI_ENV_VARS=` (or a list of only separators) must not
    silently drop the exemption — fail open to the documented defaults."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    for blank in ("", "   ", " , , "):
        monkeypatch.setenv(CI_ENV_VARS_ENV, blank)
        assert ci_env_vars() == DEFAULT_CI_ENV_VARS, repr(blank)

    monkeypatch.setenv(CI_ENV_VARS_ENV, "")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_ci_signal_does_not_defeat_the_opt_in_refusal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Precedence is unchanged: the CI exemption is checked BEFORE the refusal, so
    a genuine CI writer is exempt even with REFUSE set — and a lane with no CI
    signal still hard-fails."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(REFUSE_UNSANDBOXED_ENV, "1")

    with pytest.raises(UnsandboxedStateWriteError):
        resolve_write_path("cache/a.json")

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert resolve_write_path("cache/b.json") == wt.resolve() / "state" / "cache" / "b.json"


def test_guard_silent_for_env_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An explicit DEVKIT_STATE_ROOT sandbox → no warn (sandbox active)."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(STATE_ROOT_ENV, str(tmp_path / "sandbox"))
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_guard_silent_for_whitespace_env_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A whitespace-only DEVKIT_STATE_ROOT is 'configured' to state_root() (raw
    truthiness → it raises StateRootError on the relative path), so the write never
    reaches prod. The guard must mirror that and NOT warn about an unsandboxed write
    that won't happen — the StateRootError is what surfaces."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(STATE_ROOT_ENV, "   ")
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER), pytest.raises(StateRootError):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_guard_silent_for_marker_sandbox(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A .devkit_state_root marker → sandbox active → no warn."""
    wt = _make_lane_worktree(tmp_path)
    (wt / STATE_ROOT_MARKER).write_text(str(tmp_path / "sandbox"), encoding="utf-8")
    monkeypatch.chdir(wt)
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_guard_silent_for_main_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The primary checkout (.git is a DIR) is normal interactive dev, not a lane → no warn."""
    co = _make_main_checkout(tmp_path)
    monkeypatch.chdir(co)
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/x.json")
    assert not _guard_warned(caplog)


def test_guard_refuses_when_opted_in(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """DEVKIT_REFUSE_UNSANDBOXED_STATE=1 turns the warning into a hard error."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(REFUSE_UNSANDBOXED_ENV, "1")
    with pytest.raises(UnsandboxedStateWriteError):
        resolve_write_path("cache/x.json")


def test_guard_warns_once_per_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning is deduped — two writes from the same unsandboxed lane log once."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    with caplog.at_level(logging.WARNING, logger=GUARD_LOGGER):
        resolve_write_path("cache/a.json")
        resolve_write_path("cache/b.json")
    warnings = [r for r in caplog.records if "unsandboxed parallel lane" in r.message]
    assert len(warnings) == 1


def test_guard_refuse_fires_every_call(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Refuse mode is not gated by the warn-once dedupe — every offending write raises."""
    wt = _make_lane_worktree(tmp_path)
    monkeypatch.chdir(wt)
    monkeypatch.setenv(REFUSE_UNSANDBOXED_ENV, "1")
    with pytest.raises(UnsandboxedStateWriteError):
        resolve_write_path("cache/a.json")
    with pytest.raises(UnsandboxedStateWriteError):
        resolve_write_path("cache/b.json")
