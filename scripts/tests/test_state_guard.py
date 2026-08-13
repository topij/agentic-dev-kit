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
a passing one. ``pytester`` is the usual instrument, and enabling it requires
``pytest_plugins = ["pytester"]`` in a conftest — which pytest refuses with
*"Defining 'pytest_plugins' in a non-top-level conftest is no longer supported"*.

**The trigger is being a non-INITIAL conftest, not being outside the rootdir**,
and the distinction matters because it decides which invocations break. pytest's
`_check_non_top_pytest_plugins` fires when the conftest is loaded after the
config is already configured — so the *same* file is accepted under
`pytest <engine-dir>/tests`, which makes it an initial conftest, and rejected
under a bare `pytest .`, which does not. (Isolated on pytest 9.1.1 by placing an
identical file in both shapes; an earlier version of this paragraph said "an
ERROR in any non-rootdir conftest since 4.0", which overstates it.)

That leaves `pytester` usable for some sanctioned shapes and not others, and a
guard built to cover bare `pytest .` cannot depend on a plugin that bare
`pytest .` refuses to load. ``-p pytester`` on the command line sidesteps the
conftest rule but pushes the requirement onto every caller, including `make test`
and the adopter invocations `adopt.md`/`upgrade.md` prescribe. A subprocess needs
no plugin registration, no shipped-surface change, and exercises the real file
rather than a re-registration of it.

WHAT EACH SHAPE PINS. The parametrisation is not repetition for its own sake:
each entry is one of the invocation shapes #448 is about, and the
``state_paths``-only row is the one that was actually unguarded on `09a4c6b`
(measured: ``63 passed``, exit 0, the write sitting in the live
``state/pr-watch/``).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

# Reused rather than re-implemented. It is the repo's existing convention for
# "this case needs the walk to find no marker", and duplicating it here would
# give the suite a second copy to drift — see its own docstring for why the
# remedy is a named precondition and not a patched `Path.exists`.
from test_repo_layout import _require_no_ancestor_marker  # noqa: E402

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

# What the planted test does to the real `state/`. All five are leaks the guard
# claims to catch, and each is caught by a DIFFERENT property of
# `_real_state_snapshot`, so each pins a branch the others leave free:
#
#   file       a new path appears  → the file-hash entries
#   dir        a new directory appears and no file is written → the
#              trailing-slash directory entries. This is the branch that catches
#              the next engine to acquire #428's bug, since `pr_watch.py`'s first
#              act on that path is `STATE_DIR.mkdir(parents=True,
#              exist_ok=True)`. Measured: reduce the snapshot to files only and
#              exactly the `dir` cases fail.
#   overwrite  an EXISTING file's bytes change while its path stays → the
#              CONTENT-sensitivity of `_hash_file`. This is the shape #428
#              actually happened as: "an ordinary run overwrote this repo's own
#              state/pr-watch/1.json and 4242.json with fixture data". Replacing
#              `_hash_file(path)` with a constant fails exactly these cases and
#              no others, and survived the suite entirely before they existed.
#   symlink    a DANGLING link appears in a directory that already existed →
#              the `symlink -> <target>`-valued entries, tested before
#              `is_dir`/`is_file` because both FOLLOW a link and answer False
#              for a broken one, which is how this kind passed every snapshot
#              before #457 closed it (#456). The parent is seeded into the
#              baseline so the link is the run's ONLY change — otherwise these
#              cases would merely re-pin the `dir` branch.
#   bare-root  `state/` itself appears, childless → the `./` root entry.
#              `rglob("*")` yields descendants only, never the root it is
#              called on, so before #457 this compared `{}` against `{}`.
#
# Five branches pinned is not a partition of everything the guard could miss.
# Read `_real_state_snapshot`'s docstring for what the traversal still cannot
# see, and the module docstring's observation-window section for the classes no
# traversal fix reaches (a leak already in the baseline; a write undone before
# session end — both dispositioned on #457). Read the list as branches pinned,
# never as full coverage.
#
# Absolute pass counts are deliberately not recorded here: the figure was wrong
# twice in consecutive review rounds as tests were added beside it. Run
# `make mutation-test` and read which tests failed.
_LEAK_KINDS = ("file", "dir", "overwrite", "symlink", "bare-root")

# Seeded into the throwaway `state/` before pytest starts, so it is part of the
# baseline the guard takes at conftest import, and overwritten by the planted
# test. The two must differ in content while sharing a path — that difference is
# the whole of what the `overwrite` kind detects.
_SEEDED = '{"seeded": true}'
_OVERWRITTEN = '{"fixture": "overwrote the real receipt"}'


def _build_tree(
    root: Path,
    *,
    leak_in: str | None,
    leak_kind: str = "file",
    engine_rel: str = "scripts",
    git: bool = True,
) -> None:
    """A throwaway repo mirroring the kit's engine layout.

    ``leak_in`` names the test directory whose planted test writes into the real
    ``<root>/state/``; ``None`` plants only inert tests, which is the negative
    control. ``leak_kind`` selects whether that write is a file or a bare
    directory. ``engine_rel`` positions the engine directory, flat or nested.
    """
    # A `.git` marker so the copied conftest's walk-up resolves to `root`
    # deterministically, rather than to whatever happens to sit above tmp_path.
    # `git=False` builds the no-marker tree the fallback branch is reached from.
    root.mkdir(parents=True, exist_ok=True)
    if git:
        (root / ".git").mkdir()
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
    elif leak_kind == "dir":
        # No file written at all — exactly `pr_watch.py`'s import-time mkdir.
        leak_stmt = (
            f"    d = Path({str(root)!r}) / 'state' / 'brand-new-engine'\n"
            "    d.mkdir(parents=True, exist_ok=True)\n"
        )
    elif leak_kind == "symlink":
        # The parent is created BEFORE pytest starts so it sits in the
        # baseline and the dangling link is the run's only change — see
        # `_LEAK_KINDS` for why that seeding is load-bearing.
        (root / "state" / "pr-watch").mkdir(parents=True, exist_ok=True)
        leak_stmt = (
            "    import os\n"
            f"    d = Path({str(root)!r}) / 'state' / 'pr-watch'\n"
            "    os.symlink('/nonexistent/receipt/does/not/exist.json', d / '2222.json')\n"
        )
    elif leak_kind == "bare-root":
        # The one write `rglob` can never yield: the root itself, childless.
        leak_stmt = f"    (Path({str(root)!r}) / 'state').mkdir()\n"
    else:
        # Seeded BEFORE pytest starts, so the baseline holds its original hash;
        # the planted test then changes the bytes at a path that already existed.
        seeded = root / "state" / "pr-watch" / "1.json"
        seeded.parent.mkdir(parents=True, exist_ok=True)
        seeded.write_text(_SEEDED)
        leak_stmt = (
            f"    p = Path({str(seeded)!r})\n    p.write_text({_OVERWRITTEN!r})\n"
        )
    leak_body = "from pathlib import Path\ndef test_writes_into_real_state():\n" + leak_stmt
    inert_body = "def test_inert():\n    assert True\n"

    for name, directory in (("tests", tests), ("state_paths", state_paths_tests)):
        body = leak_body if leak_in == name else inert_body
        (directory / f"test_{name}_probe.py").write_text(body)


_LEAK_PATHS = {
    "file": ("state/pr-watch/9999.json", "9999.json"),
    "dir": ("state/brand-new-engine", "brand-new-engine/"),
    "overwrite": ("state/pr-watch/1.json", "pr-watch/1.json"),
    "symlink": ("state/pr-watch/2222.json", "pr-watch/2222.json"),
    # The whole rendered list, not a fragment: `./` alone is a substring of
    # too much other output to discriminate, and asserting the full list also
    # pins that the root entry is the run's ONLY change.
    "bare-root": ("state", "['./']"),
}


def _leaked_path(root: Path, leak_kind: str) -> Path:
    return root / _LEAK_PATHS[leak_kind][0]


def _leak_landed(root: Path, leak_kind: str) -> bool:
    """Whether the planted test's write actually happened.

    Existence is the test for the two add-shaped kinds and is NOT for
    ``overwrite``, whose path exists either way — there the question is whether
    the bytes changed. Getting this wrong would make the `overwrite` case pass
    against a guard that never fired, which is the failure this whole file
    exists to make impossible.
    """
    path = _leaked_path(root, leak_kind)
    if leak_kind == "overwrite":
        return path.is_file() and path.read_text() == _OVERWRITTEN
    if leak_kind == "symlink":
        # `exists()` FOLLOWS the link and answers False for the dangling one
        # planted here — the guard's own old blind spot restated as a harness
        # bug. `is_symlink()` answers for the link itself.
        return path.is_symlink()
    return path.exists()


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
    result: subprocess.CompletedProcess[str], root: Path, leak_kind: str
) -> None:
    leaked = _leaked_path(root, leak_kind)
    if not _leak_landed(root, leak_kind):
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
    named = _LEAK_PATHS[leak_kind][1]
    assert named in combined, f"the guard fired but did not name the changed path:\n{combined}"
    # The `!`-wrapped tail line is printed by the terminal reporter ONLY when
    # `session.shouldfail` is set — the guard's docstring claims that line, and
    # dropping the assignment used to survive all of this file (#457's
    # "surviving mutant"). Shape measured under `-q` on pytest 9.1.1:
    # `! REGRESSION (#428): the suite wrote into the real .../state !`.
    assert re.search(rf"^!+ {re.escape(_SUMMARY)}.*!+$", combined, re.MULTILINE), (
        "no `!`-wrapped tail banner — `session.shouldfail` is the only thing "
        f"that prints one, so the attribute is no longer being set:\n{combined}"
    )


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
    root, that row exited 0 with the write sitting on disk. Every kind in
    ``_LEAK_KINDS`` rides this same cross — ``file``, ``dir``, ``overwrite``,
    ``symlink``, ``bare-root`` — and what each one pins is that table's
    comment, not repeated here.
    """
    _build_tree(tmp_path, leak_in=leak_in, leak_kind=leak_kind)
    result = _run_pytest(tmp_path, _SHAPES[shape])
    _assert_guard_fired(result, tmp_path, leak_kind)


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
    _assert_guard_fired(result, tmp_path, "file")


def test_a_live_symlink_retarget_to_equal_bytes_is_caught(tmp_path: Path) -> None:
    """The branch ORDER is load-bearing, and only a LIVE link can pin it.

    Every other symlink case in this file uses a dangling target — and a
    dangling link lands in the `@` branch even if `is_symlink()` is tested
    LAST, because `is_dir()`/`is_file()` follow the link and answer False for
    a broken one. So reordering the checks — reintroducing exactly the
    historical bug `_real_state_snapshot`'s docstring describes, a live link
    recorded as its target's kind — survived every dangling-target test, as
    both lenses of #459's round-1 panel measured independently. This is the
    kill for that mutant: two real files with IDENTICAL bytes, a link moved
    from one to the other. Under the correct ordering the recorded
    `os.readlink` value changes; under the reordered mutant the link is
    hashed THROUGH, and identical bytes make the retarget invisible. Equal
    content is the essential ingredient — differing content would let the
    mutant pass on the hash difference alone.
    """
    _build_tree(tmp_path, leak_in=None)
    store = tmp_path / "state" / "pr-watch"
    store.mkdir(parents=True)
    (store / "a.json").write_text('{"receipt": "identical bytes"}')
    (store / "b.json").write_text('{"receipt": "identical bytes"}')
    link = store / "live.json"
    os.symlink(store / "a.json", link)
    (tmp_path / "scripts" / "tests" / "test_live_retarget_probe.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_retargets_a_live_state_symlink():\n"
        f"    link = Path({str(link)!r})\n"
        "    os.unlink(link)\n"
        f"    os.symlink({str(store / 'b.json')!r}, link)\n"
    )

    result = _run_pytest(tmp_path, _SHAPES["tests-only"])

    assert os.readlink(link) == str(store / "b.json"), (
        "the planted test did not retarget the link, so this run proves nothing"
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"a live-target retarget was not caught:\n{combined}"
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert "pr-watch/live.json" in combined, (
        f"the guard fired but did not name the retargeted link:\n{combined}"
    )


def test_a_special_file_appearing_is_caught(tmp_path: Path) -> None:
    """A fifo appearing under `state/` turns the run red — the `<special>` pin.

    The `else` branch recording non-link/dir/file entries had no test at all:
    both lenses of #459's round-1 panel mutated it to a silent skip — the
    pre-#459 behaviour — and the whole suite stayed green while the CHANGELOG
    promised the case. The parent is seeded into the baseline so the fifo is
    the run's only change. Appearance is what this pins; a special file
    REPLACED at a stable path compares `<special>` == `<special>` and is
    documented as outside the snapshot's sight, not covered here.
    """
    _build_tree(tmp_path, leak_in=None)
    (tmp_path / "state" / "pr-watch").mkdir(parents=True)
    (tmp_path / "scripts" / "tests" / "test_fifo_probe.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_writes_a_fifo_into_real_state():\n"
        f"    os.mkfifo(Path({str(tmp_path)!r}) / 'state' / 'pr-watch' / 'node')\n"
    )

    result = _run_pytest(tmp_path, _SHAPES["tests-only"])

    assert (tmp_path / "state" / "pr-watch" / "node").exists(), (
        "the planted test did not create the fifo, so this run proves nothing"
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"a fifo appearing was not caught:\n{combined}"
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert "pr-watch/node" in combined, (
        f"the guard fired but did not name the fifo:\n{combined}"
    )


def test_a_symlink_beside_an_at_suffixed_file_is_caught(tmp_path: Path) -> None:
    """A real file named `<name>@` must not mask a new symlink `<name>`.

    #459's round-3 adversarial lens demonstrated this live against the
    earlier key scheme, which recorded a link under `f"{relative}@"`: `@` is
    a legal filename character, so a baseline file literally named `leak@`
    occupied the link's key, sorted order put the file's hash over the
    link's entry, and a brand-new symlink `leak` compared equal — an
    invisible write into the real `state/`. The fix moved the kind marker
    into the VALUE (`symlink -> <target>`), leaving every entry keyed by its
    own path; this is the kill for any return to a kind-marking key suffix.
    """
    _build_tree(tmp_path, leak_in=None)
    store = tmp_path / "state" / "pr-watch"
    store.mkdir(parents=True)
    (store / "leak@").write_text('{"an ordinary file whose name ends in @": true}')
    (tmp_path / "scripts" / "tests" / "test_collision_probe.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_symlinks_beside_the_at_file():\n"
        f"    os.symlink('/nonexistent/target-a', Path({str(store / 'leak')!r}))\n"
    )

    result = _run_pytest(tmp_path, _SHAPES["tests-only"])

    assert (store / "leak").is_symlink(), (
        "the planted test did not create the link, so this run proves nothing"
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, (
        f"a new symlink beside a `<name>@` file was not caught:\n{combined}"
    )
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert "pr-watch/leak" in combined, (
        f"the guard fired but did not name the masked link:\n{combined}"
    )


def test_a_deleted_symlink_is_caught(tmp_path: Path) -> None:
    """A symlink DELETED from the baseline turns the run red.

    The CHANGELOG's #459 entry claims created, retargeted, *or deleted*; the
    sibling tests pin the first two, and deletion is genuinely new to #459 —
    before it a link had no snapshot entry, so there was nothing to
    disappear. What this pins is the comparison's SYMMETRIC direction: the
    changed-key walk unions baseline and after, so a key present only in the
    baseline is a change, and no other test exercises that direction. Raised
    by #459's round-2 adversarial lens as the one claim with no test behind
    it.
    """
    _build_tree(tmp_path, leak_in=None)
    store = tmp_path / "state" / "pr-watch"
    store.mkdir(parents=True)
    link = store / "receipt.json"
    os.symlink("/nonexistent/target-a", link)
    (tmp_path / "scripts" / "tests" / "test_unlink_probe.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_deletes_a_state_symlink():\n"
        f"    os.unlink(Path({str(link)!r}))\n"
    )

    result = _run_pytest(tmp_path, _SHAPES["tests-only"])

    assert not os.path.lexists(link), (
        "the planted test did not delete the link, so this run proves nothing"
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"a symlink deletion was not caught:\n{combined}"
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert "pr-watch/receipt.json" in combined, (
        f"the guard fired but did not name the deleted link:\n{combined}"
    )


def test_a_retargeted_symlink_is_caught(tmp_path: Path) -> None:
    """A symlink whose TARGET moves while its path stays is a change.

    The `symlink` rows in `_LEAK_KINDS` pin only that a link APPEARS. This
    pins the value half: the snapshot records `os.readlink`, so two states
    differing only in where an existing link points compare unequal. A
    `<symlink>` sentinel value would pass every appearance case and read a
    retarget as no change — the second blind spot #456 names, and the
    mutation this test exists to kill. Both targets here are dangling, so the
    branch-ORDER property is deliberately not this test's subject —
    `test_a_live_symlink_retarget_to_equal_bytes_is_caught` carries that one.
    """
    _build_tree(tmp_path, leak_in=None)
    link = tmp_path / "state" / "pr-watch" / "receipt.json"
    link.parent.mkdir(parents=True)
    os.symlink("/nonexistent/target-a", link)
    (tmp_path / "scripts" / "tests" / "test_retarget_probe.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_retargets_an_existing_state_symlink():\n"
        f"    link = Path({str(link)!r})\n"
        "    os.unlink(link)\n"
        "    os.symlink('/nonexistent/target-b', link)\n"
    )

    result = _run_pytest(tmp_path, _SHAPES["tests-only"])

    assert os.readlink(link) == "/nonexistent/target-b", (
        "the planted test did not retarget the link, so this run proves nothing"
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"a retarget was not caught:\n{combined}"
    assert _BANNER in combined, f"no #428 banner in output:\n{combined}"
    assert "pr-watch/receipt.json" in combined, (
        f"the guard fired but did not name the retargeted link:\n{combined}"
    )


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


def _guards_resolver():
    """The guard's own ``_find_repo_root``, extracted without importing it.

    Importing the conftest here would take a second baseline snapshot and
    register a duplicate session hook, so only the helper is compiled.
    """
    namespace: dict[str, object] = {}
    source = ENGINE_CONFTEST.read_text()
    start = source.index("def _find_repo_root")
    end = source.index("REPO_ROOT = _find_repo_root")
    # The slice omits the conftest's own `from __future__ import annotations`,
    # and the function's signature annotates `Path`, which `namespace` does not
    # hold. It works because `compile` defaults to `dont_inherit=False` and so
    # inherits THIS module's future flags — verified on 3.12 and 3.14. That makes
    # it dependent on the `from __future__ import annotations` at the top of this
    # file: remove that and this helper starts raising NameError.
    exec(compile(source[start:end], str(ENGINE_CONFTEST), "exec"), namespace)  # noqa: S102
    return namespace["_find_repo_root"]


def test_the_guards_own_root_resolution_agrees_with_the_test_suites(tmp_path: Path) -> None:
    """The deliberate duplication must stay a duplication, not a divergence.

    ``<engine-dir>/conftest.py`` carries its own ``_find_repo_root`` instead of
    importing ``_repo_layout`` — it has to work in a tree that vendors engines
    without tests, and it must not borrow an ENGINE's root resolution, since an
    engine resolving its state path wrongly is the bug it exists to catch. That
    is a defensible copy and an undefensible place for the two to disagree.
    #203 tracks the wider four-helper consolidation; this keeps these two from
    drifting meanwhile.

    Both branches, not just the marker-found one. Comparing the pair only at
    ``ENGINE_DIR`` — which always has a ``.git`` ancestor — left the no-marker
    fallback unpinned, and a mutation of it survived the whole suite. That
    fallback carries #60's known nested-layout defect, so a divergence there
    moves which ``state/`` the guard watches.

    Both assertions in the second case are UNCONDITIONAL, behind a named
    precondition. An earlier version gated the fallback-specific assertion on
    ``if not marker_above``, so on a machine whose temp directory sits inside a
    checkout the test would quietly exercise the marker branch twice and still
    pass. ``_require_no_ancestor_marker`` — the repo's existing convention for
    this, raised by the review bot on #453 — turns that environment into a
    legible failure naming ``--basetemp`` instead.
    """
    guard_resolver = _guards_resolver()

    # Branch 1 — a marker exists above.
    assert guard_resolver(ENGINE_DIR) == find_repo_root(ENGINE_DIR)

    # Branch 2 — the fallback.
    deep = tmp_path / "no-marker" / "engines"
    deep.mkdir(parents=True)
    _require_no_ancestor_marker(deep)
    assert guard_resolver(deep) == find_repo_root(deep)
    assert guard_resolver(deep) == deep.parent, (
        "the fallback branch did not run, so this case pinned nothing"
    )


def test_a_nested_layout_with_no_marker_watches_the_wrong_state_dir(tmp_path: Path) -> None:
    """#60's depth limit, reaching the guard — pinned, not repaired.

    With no ``.git`` anywhere, ``_find_repo_root`` falls back to
    ``start.parent``. For a nested ``<root>/scripts/devkit`` engine that is
    ``<root>/scripts``, one level short, so the guard snapshots
    ``<root>/scripts/state`` while the engines write to ``<root>/state``. A real
    leak in such a tree is therefore invisible to it.

    **Not repaired here, deliberately.** The fallback mirrors
    ``kitconfig.repo_root``, whose depth problem is #60 and still open, and
    ``_repo_layout``'s own docstring records three attempts to be cleverer that
    were each withdrawn: the root is genuinely unknowable without a marker, so
    any guess is wrong in some layout. Raised by the review bot on #453, which
    asked for the root to be derived without the one-level fallback — that is
    #60's job, and doing it here would fork the resolution the guard is pinned
    to agree with.

    What this test adds is the half that WAS missing: the harness always planted
    a ``.git``, so nothing exercised the guard in the layout where its root
    resolution is known to be wrong. It is the sibling of
    ``test_repo_layout.py::test_the_fallback_is_wrong_in_a_nested_layout_and_that_is_known``
    and fails the same way — loudly, when #60 lands.
    """
    engine_rel = _LAYOUTS["nested"]
    _build_tree(tmp_path, leak_in="tests", leak_kind="file", engine_rel=engine_rel, git=False)
    _require_no_ancestor_marker(tmp_path / engine_rel)

    result = _run_pytest(tmp_path, _shapes(engine_rel)["tests-only"])

    assert _leak_landed(tmp_path, "file"), "the planted test did not write; nothing is pinned"
    combined = result.stdout + result.stderr
    assert result.returncode == 0, (
        "the guard caught a leak in a no-marker nested tree. If #60's depth "
        f"resolution landed, this test and the docstrings citing it need updating.\n{combined}"
    )
    assert _BANNER not in combined, f"the guard fired where #60 says it cannot see:\n{combined}"


@pytest.mark.parametrize(
    ("leak_in", "cwd_rel"),
    [("tests", "scripts/tests"), ("state_paths", "scripts/lib/state_paths/tests")],
    ids=["tests", "state-paths"],
)
def test_the_documented_residual_still_behaves_as_documented(
    tmp_path: Path, leak_in: str, cwd_rel: str
) -> None:
    """Characterisation pin for the one shape the guard does NOT cover.

    ``<engine-dir>/conftest.py`` documents, as measured fact, that a run whose
    CWD is a test directory loses the guard whatever arguments it gets — pytest
    resolves rootdir, and with it confcutdir, from cwd and args together. Every
    other measured claim in that docstring has a pin; this one did not, which
    the round-4 correctness lens flagged as the PR's own pattern stopping one
    claim short.

    **This asserts a limitation, deliberately.** It is not a blessing of the
    gap: #455 tracks closing it, and this test is expected to FAIL when that
    lands — which is the point. Until then it catches the same behaviour
    drifting silently in either direction under a future pytest.
    """
    _build_tree(tmp_path, leak_in=leak_in, leak_kind="file")
    result = _run_pytest(tmp_path, [], cwd=tmp_path / cwd_rel)

    assert _leak_landed(tmp_path, "file"), "the planted test did not write; nothing is pinned"
    combined = result.stdout + result.stderr
    assert result.returncode == 0, (
        "the residual documented in <engine-dir>/conftest.py has changed — a run "
        "with CWD inside the test directory now DOES fail on a leak. If #455 "
        f"landed, delete this test and the docstring's residual section.\n{combined}"
    )
    assert _BANNER not in combined, f"the guard fired where it is documented not to:\n{combined}"
