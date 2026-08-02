"""Pytest configuration that travels with the kit's tests.

WHY A CONFTEST AND NOT A ROOT INI FILE (issues #33, #112). The `driftcheck`
marker below has to be registered wherever these tests are *collected*, and the
kit's tests are vendored into adopter repos under `paths.engines`, and `/adopt`
and `/upgrade` both tell adopters to run `<engine-dir>/tests` — collecting them
against THEIR rootdir and THEIR ini file. Registration in this repo's root would
therefore work here and silently do nothing for every adopter, which is the
failure mode the kit exists to avoid. A conftest beside the tests moves with
them.

Two caveats, stated because the paragraph above reads as a working guarantee and
is only half of one. That vendored invocation does not cleanly collect TODAY —
several test modules hardcode the repo root as `parents[2]` (#134). And nothing
delivers this file to an ALREADY-adopted repo: `/upgrade` copies only what
`kit_doctor` tracks, and no test file is in the manifest (#132). Registration
itself does work in a vendored layout; both lenses that reviewed this confirmed
it by building one.

`pyproject.toml` is doubly excluded: besides not travelling, a root
`pyproject.toml` makes `uv run --with pytest … python` fall into project mode
and materialise a `.venv/` and a stub `uv.lock` — see the header of `ruff.toml`,
where that was measured.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)

# Whether a `.git` marker was actually FOUND, as opposed to `find_repo_root`
# falling back to `start.parent`. The fallback is right only when the engines
# sit directly under the root, and is one level short in the `scripts/devkit/`
# layout `/adopt` defaults to (#60, pinned in `test_repo_layout.py`).
#
# It matters here and nowhere else in the suite: a wrong root used to surface as
# a loud `FileNotFoundError` from a test body, and the skip below would convert
# that into `not vendored in this tree` — a confident, wrong claim about a file
# that is present. So when the marker is absent the skip does not run at all,
# and the pre-existing loud failure is preserved. Adversarial and correctness
# lenses, PR #232 round 1.
ROOT_IS_RESOLVED = any((c / ".git").exists() for c in (ENGINE_DIR, *ENGINE_DIR.parents))


def require_kit_paths(*paths: str) -> None:
    """Skip the current test unless every path is present, from inside a fixture.

    The fixture-time counterpart of the `kit_repo_only` marker, and the same
    predicate. It exists because a dependency introduced by a FIXTURE cannot be
    declared on the tests that use it without repeating a marker on every one of
    them — and a marker repeated 38 times goes stale the first time someone adds
    a 39th test. Expressed at the fixture, a new user of that fixture inherits
    it. `test_kit_repo_only.py` scans for both spellings.
    """
    _skip_if_missing(paths, "a fixture this test uses needs")


def _skip_if_missing(paths, prefix: str) -> None:
    if not paths or not ROOT_IS_RESOLVED:
        return
    missing = [rel for rel in paths if not (REPO_ROOT / rel).exists()]
    if missing:
        pytest.skip(f"{prefix}: not vendored in this tree: {', '.join(missing)}")


def pytest_configure(config) -> None:
    """Register the marks, so `-m` expressions naming them are supported.

    Unregistered marks still *match* under `-m`, so the exclusion would work
    without this — it would just warn (`PytestUnknownMarkWarning`) on every run.
    A warning attached to the one command a reviewer is told to trust is exactly
    the kind of noise that gets the command dropped, so the mark is declared.
    """
    config.addinivalue_line(
        "markers",
        "driftcheck: compares bytes against kit-manifest.json rather than "
        "asserting behaviour. Excluded from mutation-testing runs "
        "(`-m 'not driftcheck'`) because ANY mutation fails it, which reads "
        "as a kill while nothing behavioural caught anything (#33/#112).",
    )
    config.addinivalue_line(
        "markers",
        "kit_repo_only(*paths): asserts against files the kit ships but an "
        "adopter need not vendor. Skipped when any named path is absent, so a "
        "sized-down adoption gets a clean run instead of inapplicable failures "
        "(#134 cause 2).",
    )


def pytest_runtest_setup(item) -> None:
    """Skip a `kit_repo_only` test whose required paths this tree does not have.

    **Why a skip and not a fix.** These tests are not path-portable-with-effort;
    they are *inapplicable*. `test_init_sh.py` asserts on `init.sh`'s behaviour,
    and an adopter who vendored engines and config has no `init.sh` to assert
    about. Repairing the paths would only convert a `FileNotFoundError` into a
    differently-worded failure — #134 says exactly that, and the repair of
    cause 1 in PR #202 demonstrated it: it turned a collection abort into 90
    legible failures rather than into a clean run.

    **Why the marker takes paths rather than probing for "the kit's own repo".**
    A test declares what it needs, and the answer is then a fact about the tree
    rather than a judgement about which repo this is. Any such judgement would
    be a bound the author sets — the shape `fallback-review-panel.md` records as
    having opened a hole three times — and no marker file distinguishes the
    kit's checkout from a full-vendor adoption anyway. A full vendor that keeps
    `scripts/` runs these tests, correctly, because it genuinely has the files.

    **The limit this leaves, corrected from a claim that was wrong.** An earlier
    version of this docstring said a deleted kit file would "go quiet rather
    than red". It does not: `test_kit_repo_only.py`'s positive control asserts
    every marked path exists in a complete kit tree, and it fires on a deletion
    exactly as readily as on a typo — measured by deleting each marked path in
    turn. Deleting `scripts/kit_doctor.py` is louder still, since
    `test_kit_doctor.py` imports it at module scope and collection aborts.

    What the control genuinely cannot do is tell a deletion from a typo, and it
    is scoped to trees that hold every file `kit-manifest.json` lists — so a
    marker naming `init.sh`, which the manifest does not track, is the one path
    whose typo could go unnoticed in a tree that is otherwise incomplete.
    """
    # `iter_markers`, not `get_closest_marker`: a function-level marker must ADD
    # to a module-level one rather than replace it. `test_portability.py`'s
    # init.sh tests that also need `docs/templates` are exactly that case, and
    # with `get_closest_marker` the function marker silently dropped the
    # module's `init.sh` requirement. Correctness lens, PR #232 round 1.
    paths = sorted({rel for m in item.iter_markers("kit_repo_only") for rel in m.args})
    _skip_if_missing(paths, "needs")
