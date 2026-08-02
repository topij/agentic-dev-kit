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

# Resolved once, the same way every test module resolves it — walk up for `.git`
# from the engines directory, itself derived from this file's own location
# rather than counted in `parents[N]` (#134 cause 1).
REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))


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

    **The limit this leaves, stated because it is real.** In the kit's own repo
    every path is present, so nothing skips and coverage is unchanged — but if a
    kit file were deleted here, its tests would go quiet rather than red.
    `test_kit_repo_only.py` catches a marker naming a path that never existed;
    it cannot catch a deletion, because the marker would then be telling the
    truth. `kit-manifest.json` covers every KIT_OWNED path; `init.sh` and the
    root `Makefile` are tracked by neither, so for those two the trade is a loud
    failure for a counted skip.
    """
    marker = item.get_closest_marker("kit_repo_only")
    if marker is None:
        return
    missing = [rel for rel in marker.args if not (REPO_ROOT / rel).exists()]
    if missing:
        pytest.skip(f"not vendored in this tree: {', '.join(missing)}")
