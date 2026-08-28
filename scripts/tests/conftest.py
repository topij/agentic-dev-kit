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
is only half of one. Test paths are kit-owned and `/upgrade` can deliver them now,
but each remains declinable: a sized-down adopter can install a test module without
this file. And in a copied tree with no `.git`, `_repo_layout.py` must fall back to
layout arithmetic that cannot identify an arbitrarily nested engine directory
(#233). Registration itself works when this conftest is present in a real vendored
checkout; the upgrade workflow enumerates the installed test modules rather than
assuming every test root was accepted.

`pyproject.toml` is doubly excluded: besides not travelling, a root
`pyproject.toml` makes `uv run --with pytest … python` fall into project mode
and materialise a `.venv/` and a stub `uv.lock` — see the header of `ruff.toml`,
where that was measured.

THE #428 GUARD'S TWO HALVES NOW LIVE IN DIFFERENT FILES, deliberately.
``_hermetic_state_root`` below is the PREVENTION and stays here, because it must
not reach ``lib/state_paths/tests`` — those tests drive ``$DEVKIT_STATE_ROOT``
themselves, and several assert on its ABSENCE, so an autouse fixture setting it
would rewrite the very condition under test. The DETECTION half — the baseline
snapshot and `pytest_sessionfinish` — moved up to ``<engine-dir>/conftest.py``,
which every test directory reaches (#448). Detection without prevention is the
correct arrangement for ``state_paths``: those tests should not be sandboxed,
and should still be caught if they write into the real ``state/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)

# Whether a `.git` marker was actually found. With none, `find_repo_root` falls
# back to `start.parent`, which is right for a flat layout and short by one or
# more levels for a nested one — and nothing here can tell those apart, because
# the only signal that would is exactly what is missing.
#
# THREE ATTEMPTS TO BE CLEVER ABOUT THIS WERE WITHDRAWN, one per review round,
# and the next one should not be made here:
#
#   round 1 — disable skipping entirely when no `.git` was found. Broke the FLAT
#             sized-down tarball case, which had been skipping correctly: an
#             accurate skip became a raw FileNotFoundError, #134's own harm class.
#   round 2 — search both `REPO_ROOT` and its parent. Still wrong at nesting
#             depth > 1 (`tools/internal/devkit/`), where it emitted a confident
#             `not vendored` about a file present at the true root; and in the
#             flat case the second candidate sits OUTSIDE the tree, so a
#             same-named file above it suppressed a skip that should have fired.
#   round 3 — this. No guess at all.
#
# The root is unknowable without `.git`, so the skip no longer pretends
# otherwise: it searches the one resolved root and SAYS the root was a guess.
# That is not a false claim — it states exactly what was checked — and it keeps
# the clean run a sized-down adopter is owed. #233 holds the resolution.
_ROOT_FOUND = any((c / ".git").exists() for c in (ENGINE_DIR, *ENGINE_DIR.parents))
_UNRESOLVED = (
    "" if _ROOT_FOUND else f" (repo root unresolved — no .git above {ENGINE_DIR}; see #233)"
)


# --------------------------------------------------------------------------- #
# hermetic state root (#428) — the PREVENTION half; detection is one level up
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _hermetic_state_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect every ``$DEVKIT_STATE_ROOT``-resolved write into a per-test dir.

    #428: `pr_watch.py` computes its persistence root as a MODULE-LEVEL
    constant, evaluated once at import time (``STATE_DIR = _STATE_ROOT /
    "pr-watch"``, resolving ``$DEVKIT_STATE_ROOT``, then a
    ``.devkit_state_root`` marker, then the real repo root). It is the only
    engine here that reaches ``state/`` at all, and it resolves at import
    rather than per call — which is why this fixture sets the env var, which
    a fresh module load will read, rather than patching an attribute on a
    module instance that does not outlive the test. A test that
    exercises the persistence path without individually remembering
    ``monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)`` therefore
    inherits the exact default the real CLI uses. Confirmed via `make test`
    on the unpatched suite: an ordinary run overwrote this repo's own
    ``state/pr-watch/1.json`` and ``4242.json`` with fixture data (a
    fabricated ``fallback:panel`` review receipt; a reset ``seen`` set) —
    the artifact the merge gate reads as proof a review happened.

    This sets the env var rather than patching ``STATE_DIR`` on an
    already-loaded module, because no such shared module exists to patch:
    `test_pr_watch.py`'s ``_load_pr_watch()`` (and similar helpers in other
    modules here) builds a FRESH module instance inside every test body via
    ``importlib.util.spec_from_file_location``. Each fresh exec reads
    ``os.environ`` again when it computes ``_STATE_ROOT``, so setting the
    var here — a normal autouse fixture, which pytest runs before the test
    body — reaches every one of them, in this module and any other
    collected under ``scripts/tests/``. It also means the module keeps
    doing its OWN real derivation; nothing here shortcuts or replaces it
    (see ``test_state_dir_is_the_pr_watch_subdir_of_the_resolved_root`` in
    ``test_pr_watch.py``, which pins that derivation directly and opts out
    of this fixture to do it).

    DELIBERATELY SCOPED TO THIS DIRECTORY, and not moved up beside the
    detection half. ``lib/state_paths/tests`` drives ``$DEVKIT_STATE_ROOT``
    as its subject — setting it, clearing it, and asserting on the
    unset case — so an autouse fixture setting it there would not sandbox
    those tests, it would rewrite what they are testing.

    The 6 tests that already ``monkeypatch.setattr(pr_watch, "STATE_DIR",
    tmp_path)`` by hand stay correct and are not redundant to remove: their
    explicit patch, applied after this fixture's env var already took
    effect, simply overrides it to their own literal path.

    ``monkeypatch.setenv`` restores whatever was ambient before the test
    (normally unset) once the test ends, so this cannot leak between tests
    or outlive the run.
    """
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state"))


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
    if not paths:
        return
    missing = [rel for rel in paths if not (REPO_ROOT / rel).exists()]
    if missing:
        pytest.skip(f"{prefix}: not vendored in this tree: {', '.join(missing)}{_UNRESOLVED}")


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
    # to a module-level one rather than replace it. `test_init_sh.py`'s six
    # seeding tests, which need `docs/templates` on top of the module's
    # `init.sh`, are exactly that case, and
    # with `get_closest_marker` the function marker silently dropped the
    # module's `init.sh` requirement. Correctness lens, PR #232 round 1.
    paths = sorted({rel for m in item.iter_markers("kit_repo_only") for rel in m.args})
    _skip_if_missing(paths, "needs")
