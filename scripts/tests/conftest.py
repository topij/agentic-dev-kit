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


def pytest_configure(config) -> None:
    """Register `driftcheck` so `-m 'not driftcheck'` is a supported invocation.

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
