"""Behavioural pin for the #428 state guard in ``<engine-dir>/conftest.py``.

WHY THIS FILE EXISTS (#447). The guard's own docstring calls it "load-bearing,
not decorative" — and nothing in the suite would have noticed if it stopped
working. Measured by both lenses of #444's fallback panel, independently:
mutate the hook into a pure no-op (an early ``return`` before all its logic) and
the full `make test` run is bit-for-bit identical to the correct
implementation's. Nothing the shipped suite runs ever writes into the real
``state/`` — that is ``_hermetic_state_root``'s whole job — so the guard's
failure path was never exercised and the mutation survived silently.

WHY A SUBPROCESS AND NOT ``pytester``. The guard is a *session*-level property:
a baseline taken at conftest import, compared once at ``pytest_sessionfinish``.
Observing it needs a whole pytest session that is allowed to fail, nested inside
a passing one. ``pytester`` is the usual instrument and is unavailable here:
enabling it requires ``pytest_plugins = ["pytester"]``, and pytest has made that
an ERROR in any non-rootdir conftest since 4.0 — the kit's conftests are
non-rootdir by construction, because they travel into adopter trees and are
collected against the adopter's rootdir (#33/#112). ``-p pytester`` on the
command line would work but pushes the requirement onto every caller, including
`make test` and the adopter invocations `adopt.md`/`upgrade.md` prescribe. A
subprocess needs no plugin registration, no shipped-surface change, and
exercises the real file rather than a re-registration of it.

WHAT EACH SHAPE PINS. The parametrisation is not repetition for its own sake:
each entry is one of the invocation shapes #448 is about, and the
``state_paths``-only row is the one that was actually unguarded on `09a4c6b`
(measured: ``63 passed``, exit 0, the write sitting in the live
``state/pr-watch/``).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
ENGINE_CONFTEST = ENGINE_DIR / "conftest.py"

# The banner text the guard writes. Asserted as a substring rather than
# reconstructed, so a reworded banner fails here instead of silently passing a
# test that matches nothing.
_BANNER = "REAL state/ WAS WRITTEN (#428)"
_SUMMARY = "REGRESSION (#428)"

pytestmark = pytest.mark.skipif(
    not ENGINE_CONFTEST.exists(),
    reason=f"the engine-root conftest carrying the #428 guard is not vendored here: {ENGINE_CONFTEST}",
)

# The engine directory's position, keyed by id. `flat` is the kit's own layout;
# `nested` is the `paths.engines: scripts/devkit` shape `adopt.md` defaults to and
# cs-toolkit actually uses. Both are claimed as measured in the guard's docstring,
# so both are exercised here rather than only asserted there.
_LAYOUTS = {"flat": "scripts", "nested": "scripts/devkit"}


def _shapes(engine_rel: str) -> dict[str, list[str]]:
    """Every sanctioned invocation shape, as arguments relative to the repo root.

    Keyed by id rather than positional because the case tables below select from
    it: an index would let a reordering silently change which shape each case
    exercises, with every test still passing.
    """
    return {
        "both-dirs": [f"{engine_rel}/lib/state_paths/tests", f"{engine_rel}/tests"],
        "tests-only": [f"{engine_rel}/tests"],
        "state-paths-only": [f"{engine_rel}/lib/state_paths/tests"],
        "repo-root": ["."],
    }


_SHAPES = _shapes(_LAYOUTS["flat"])

# What the planted test does to the real `state/`. Both are leaks the guard
# claims to catch, and they exercise DIFFERENT branches of `_real_state_snapshot`:
# `file` is caught by the file-hash entries, `dir` only by the trailing-slash
# directory entries. The directory branch is the one that catches the next engine
# to acquire #428's bug, since `pr_watch.py`'s first act on that path is
# `STATE_DIR.mkdir(parents=True, exist_ok=True)` — an engine that creates its
# directory and writes no file in the same run is invisible to a files-only
# snapshot. Measured: with the snapshot reduced to files only, every file-leak
# case here still passes and only the `dir` cases fail.
_LEAK_KINDS = ("file", "dir")


def _build_tree(
    root: Path, *, leak_in: str | None, leak_kind: str = "file", engine_rel: str = "scripts"
) -> None:
    """A throwaway repo mirroring the kit's engine layout.

    ``leak_in`` names the test directory whose planted test writes into the real
    ``<root>/state/``; ``None`` plants only inert tests, which is the negative
    control. ``leak_kind`` selects whether that write is a file or a bare
    directory. ``engine_rel`` positions the engine directory, flat or nested.
    """
    # A `.git` marker so the copied conftest's walk-up resolves to `root`
    # deterministically, rather than to whatever happens to sit above tmp_path.
    (root / ".git").mkdir(parents=True)
    engine = root / engine_rel
    tests = engine / "tests"
    state_paths_tests = engine / "lib" / "state_paths" / "tests"
    tests.mkdir(parents=True)
    state_paths_tests.mkdir(parents=True)
    (engine / "conftest.py").write_bytes(ENGINE_CONFTEST.read_bytes())

    if leak_kind == "file":
        leak_stmt = (
            f"    d = Path({str(root)!r}) / 'state' / 'pr-watch'\n"
            "    d.mkdir(parents=True, exist_ok=True)\n"
            "    (d / '9999.json').write_text('{}')\n"
        )
    else:
        # No file written at all — exactly `pr_watch.py`'s import-time mkdir.
        leak_stmt = (
            f"    d = Path({str(root)!r}) / 'state' / 'brand-new-engine'\n"
            "    d.mkdir(parents=True, exist_ok=True)\n"
        )
    leak_body = "from pathlib import Path\ndef test_writes_into_real_state():\n" + leak_stmt
    inert_body = "def test_inert():\n    assert True\n"

    for name, directory in (("tests", tests), ("state_paths", state_paths_tests)):
        body = leak_body if leak_in == name else inert_body
        (directory / f"test_{name}_probe.py").write_text(body)


def _leaked_path(root: Path, leak_kind: str) -> Path:
    return (
        root / "state" / "pr-watch" / "9999.json"
        if leak_kind == "file"
        else root / "state" / "brand-new-engine"
    )


def _run_pytest(
    root: Path, args: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a nested pytest session and capture its verdict.

    ``cwd`` defaults to ``root``; pass the engine directory to exercise the
    invocation an adopter makes from inside their vendored engines. ``DEVKIT_*``
    is stripped from the child's environment so the nested run cannot inherit
    this test's own ``_hermetic_state_root`` sandbox. The guard does not read
    those variables — that independence is the point of its own root resolution
    — but a harness that quietly depended on them would be testing something
    other than what ships.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("DEVKIT_")}
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider"],
        cwd=cwd or root,
        env=env,
        capture_output=True,
        text=True,
    )


def _assert_guard_fired(
    result: subprocess.CompletedProcess[str], leaked: Path, names: str
) -> None:
    if not leaked.exists():
        pytest.fail(
            f"the planted test did not write {leaked}, so this run proves nothing "
            f"about the guard.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    assert result.returncode != 0, (
        f"the guard did not fail the run after a write into {leaked}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert names in combined, f"the guard fired but did not name the changed path:\n{combined}"


# (shape, which directory leaks). Written out rather than crossed with `_SHAPES`,
# because a leak only proves something in a shape that COLLECTS it: `pytest
# scripts/tests` never runs a test planted under `state_paths`, so that pairing
# would assert the guard stayed silent about a write that never happened — a
# passing test measuring nothing.
_LEAK_CASES = [
    ("both-dirs", "tests"),
    ("both-dirs", "state_paths"),
    ("tests-only", "tests"),
    ("state-paths-only", "state_paths"),
    ("repo-root", "tests"),
    ("repo-root", "state_paths"),
]


@pytest.mark.parametrize("leak_kind", _LEAK_KINDS)
@pytest.mark.parametrize(
    ("shape", "leak_in"), _LEAK_CASES, ids=[f"{s}-leak-in-{d}" for s, d in _LEAK_CASES]
)
def test_guard_catches_a_write_into_real_state(
    tmp_path: Path, shape: str, leak_in: str, leak_kind: str
) -> None:
    """A leak anywhere in the collected set turns the run red, in every shape.

    ``state-paths-only`` is #448 exactly: before the guard moved to the engine
    root, that row exited 0 with the write sitting on disk. The ``dir`` kind is
    the branch that catches an engine which creates its state directory and
    writes no file — see ``_LEAK_KINDS``.
    """
    _build_tree(tmp_path, leak_in=leak_in, leak_kind=leak_kind)
    result = _run_pytest(tmp_path, _SHAPES[shape])
    _assert_guard_fired(
        result,
        _leaked_path(tmp_path, leak_kind),
        "9999.json" if leak_kind == "file" else "brand-new-engine/",
    )


@pytest.mark.parametrize("layout", list(_LAYOUTS), ids=list(_LAYOUTS))
@pytest.mark.parametrize("invoked_from", ["repo-root", "engine-dir"])
def test_guard_reaches_every_layout_and_working_directory(
    tmp_path: Path, layout: str, invoked_from: str
) -> None:
    """The docstring's MEASURED REACH claim, pinned rather than only asserted.

    ``<engine-dir>/conftest.py`` states it fires in the kit's flat layout and in
    a nested ``scripts/devkit/`` adopter layout, invoked from the repo root or
    from inside the engine directory. Both lenses of #453's panel confirmed the
    claim is true and observed that nothing in the suite would notice if one of
    those four cells broke. This is that pin.

    ``state_paths`` is the leaking directory throughout: it is the one #448 was
    found in, and the one whose conftest coverage the placement depends on.
    """
    engine_rel = _LAYOUTS[layout]
    _build_tree(tmp_path, leak_in="state_paths", engine_rel=engine_rel)

    if invoked_from == "repo-root":
        args, cwd = _shapes(engine_rel)["state-paths-only"], None
    else:
        # Relative to the engine directory, which is what an adopter standing in
        # their vendored engines actually types.
        args, cwd = ["lib/state_paths/tests"], tmp_path / engine_rel

    result = _run_pytest(tmp_path, args, cwd=cwd)
    _assert_guard_fired(result, _leaked_path(tmp_path, "file"), "9999.json")


@pytest.mark.parametrize("shape", list(_SHAPES), ids=list(_SHAPES))
def test_guard_is_silent_when_nothing_writes(tmp_path: Path, shape: str) -> None:
    """The negative control: no leak, no banner, exit 0.

    Without this, a guard that failed EVERY run would satisfy the tests above
    while making the suite useless — the failure mode a positive-only pin
    cannot see.
    """
    _build_tree(tmp_path, leak_in=None)
    result = _run_pytest(tmp_path, _SHAPES[shape])

    combined = result.stdout + result.stderr
    assert result.returncode == 0, f"a clean run was failed by the guard:\n{combined}"
    assert _BANNER not in combined, f"the guard fired on a run that wrote nothing:\n{combined}"
    assert _SUMMARY not in combined, f"the guard's summary leaked into a clean run:\n{combined}"


def test_the_guards_own_root_resolution_agrees_with_the_test_suites() -> None:
    """The deliberate duplication must stay a duplication, not a divergence.

    ``<engine-dir>/conftest.py`` carries its own ``_find_repo_root`` instead of
    importing ``_repo_layout`` — it has to work in a tree that vendors engines
    without tests, and it must not borrow an ENGINE's root resolution, since an
    engine resolving its state path wrongly is the bug it exists to catch. That
    is a defensible copy and an undefensible place for the two to disagree, so
    this pins them equal on the tree we are running in. #203 tracks the wider
    four-helper consolidation; this keeps these two from drifting meanwhile.
    """
    namespace: dict[str, object] = {}
    source = ENGINE_CONFTEST.read_text()
    # Execute only the helper, not the module: importing the conftest here would
    # take a second baseline snapshot and register a duplicate session hook.
    start = source.index("def _find_repo_root")
    end = source.index("REPO_ROOT = _find_repo_root")
    exec(compile(source[start:end], str(ENGINE_CONFTEST), "exec"), namespace)  # noqa: S102
    guard_resolver = namespace["_find_repo_root"]

    assert guard_resolver(ENGINE_DIR) == find_repo_root(ENGINE_DIR)
