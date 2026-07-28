"""What pins the mutation-testing exclusion — and, deliberately, what does not.

`docs/agentic-dev-kit/fallback-review-panel.md` contract item 5 tells a reviewer
to trust `-m 'not driftcheck'` when deciding whether a mutant died. The tests
here pin that the exclusion selects the right test, removes exactly it, and that
the test it removes is really running. Every assertion below reaches its verdict
by executing pytest and reading what pytest did.

**Three earlier tests were deleted rather than fixed, and the reason is worth
keeping.** They policed the `Makefile` recipes and the doctrine file by
inspecting their text, to stop the documented command silently rotting. Three
consecutive review rounds walked through them, each time by a spelling the
previous round had not used: a literal parked in a `#` comment; the first
`target:` block read while GNU make runs the last; `--deselect` and `-k` instead
of `-m`; `-k` with no space after it; `--ignore=`; narrowing both make targets
symmetrically; and dropping a target from `.PHONY:` so the loop never inspected
it. Each round's fix was the next round's finding, which is the pattern
`safety-critical-changes.md` rule 1 names — so they were removed instead of
tightened a fourth time.

The honest statement of what is left: **nothing here stops someone editing the
Makefile, the workflow, or the doctrine to disable the drift gate.** A text
search over a file cannot, because whoever edits it can read the search. What
this file does cover is the mechanism itself — the marker, its registration, and
the behaviour of the documented command — none of which is text-matched.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no repository root above {start}")


REPO_ROOT = _find_repo_root(ENGINE_DIR)

# Derived from where this file actually sits, not hardcoded to `scripts/`. An
# adopter vendors the engines under their own `paths.engines` (the /adopt
# default is `scripts/devkit/`), where a literal "scripts/tests" names nothing.
# CLAUDE.md's no-hardcoding rule points the same way.
_ENGINE_REL = ENGINE_DIR.relative_to(REPO_ROOT).as_posix()
SUITES = (f"{_ENGINE_REL}/lib/state_paths/tests", f"{_ENGINE_REL}/tests")

# The one test that is allowed to carry the marker.
DRIFTCHECK_NODE = f"{_ENGINE_REL}/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean"

MUTATION_INVOCATION = "-m 'not driftcheck'"


def _pytest(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _collect(*extra: str) -> list[str]:
    """Node ids pytest would collect, via a real subprocess run.

    Deliberately shells out to `pytest` rather than introspecting `pytestmark`
    attributes: the property under test is what the *documented command* does,
    and marker resolution is pytest's, not something a reimplementation in the
    test would faithfully model.
    """
    proc = _pytest(*SUITES, "--collect-only", "-q", "--no-header", *extra)
    assert proc.returncode in (0, 5), f"collection failed:\n{proc.stdout}\n{proc.stderr}"
    return [
        line.strip()
        for line in proc.stdout.splitlines()
        if "::" in line and not line.startswith(" ")
    ]


def test_driftcheck_marks_exactly_the_byte_comparison_test():
    """Exactly one test is excluded from mutation runs, and it is that one.

    A second marked test would leave a mutation run quietly reporting on a
    smaller suite than the reviewer believes they ran.
    """
    marked = _collect("-m", "driftcheck")
    assert marked == [DRIFTCHECK_NODE], (
        "the `driftcheck` marker must cover exactly the byte-comparison test; "
        f"collected {marked}. Anything else here is silently removed from "
        "every mutation-testing run."
    )


def test_mutation_invocation_deselects_only_that_test():
    """`-m 'not driftcheck'` removes one test and keeps the rest.

    Pins the complement as well as the selection: an `-m` expression that
    matched nothing would pass the test above and still leave the drift test
    running in mutation mode.
    """
    everything = _collect()
    mutation_run = _collect("-m", "not driftcheck")

    assert DRIFTCHECK_NODE in everything, "the drift test must still exist in a normal run"
    assert DRIFTCHECK_NODE not in mutation_run, (
        "the drift test is still collected under the documented mutation "
        "invocation — every mutant will read as killed (#33)"
    )
    assert set(everything) - set(mutation_run) == {DRIFTCHECK_NODE}
    assert len(mutation_run) == len(everything) - 1


def test_the_drift_test_actually_executes():
    """Collection is not execution, and the difference is a silent hole.

    A `skip` stacked above the marker leaves every assertion in this file green
    — `--collect-only` lists a skipped test exactly like a live one — while the
    drift gate stops guarding anything at all.

    Asserts EXECUTION, deliberately not a pass. An earlier version required
    `1 passed`, which made it fail for any behaviour-only mutation to a
    kit-owned file — reintroducing #33 inside the very run that exists to escape
    it. Whether the drift test passes is its own business; this one only cares
    that it is not silently inert.
    """
    proc = _pytest(DRIFTCHECK_NODE, "-q", "--no-header")
    assert "skipped" not in proc.stdout, (
        "the drift test is skipped, so it guards nothing:\n" + proc.stdout
    )
    assert "1 passed" in proc.stdout or "1 failed" in proc.stdout, (
        "the drift test must RUN, not merely be collected; got:\n" + proc.stdout
    )


def test_the_drift_failure_message_names_the_escape_hatch(monkeypatch):
    """Trigger the real assertion and read the real message.

    An earlier version grepped `test_kit_doctor.py` for the literal, which a
    copy of the string in an unrelated comment satisfied while the message
    itself said nothing. The message is the surface a reviewer is most likely to
    read, because it appears at the moment they hit the trap — so it is checked
    by being raised.

    Scope, stated because the mechanism invites over-reading: the drift is
    synthetic. This pins what the message SAYS when the check fires, not that
    the check still detects anything.
    """
    # Both imports need the engine and tests directories on the path. A
    # whole-directory collection puts them there as a side effect; running this
    # file on its own does not, and an ImportError here would look like a
    # failure of the property rather than of the harness.
    for extra in (ENGINE_DIR, ENGINE_DIR / "lib", ENGINE_DIR / "tests"):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))

    import kit_doctor
    import test_kit_doctor

    class _Drifted:
        path = "scripts/pr_watch.py"
        state = "differs"

    monkeypatch.setattr(
        kit_doctor,
        "inspect",
        lambda *a, **k: type("R", (), {"drifted": [_Drifted()]})(),
    )

    with pytest.raises(AssertionError) as excinfo:
        test_kit_doctor.test_kit_repo_self_check_is_clean()

    message = str(excinfo.value)
    assert MUTATION_INVOCATION in message, (
        f"the drift test's failure message must name the escape hatch; got: {message}"
    )
    assert "scripts/pr_watch.py" in message, "the message must name the drifted path"
    assert "not behaviour" in message or "not behavioural" in message, (
        "the message must say it compares bytes rather than behaviour"
    )


def test_the_marker_is_registered_somewhere_pytest_can_see_it():
    """An unregistered mark still matches under `-m`; it just warns on the one
    command a reviewer is told to trust, which is how the command gets dropped
    and the folklore comes back.

    Named for what it checks. It does NOT establish that the registration comes
    from the conftest beside the tests rather than from a rootdir ini — gutting
    `pytest_configure` and adding a root `pytest.ini` passes this, and a review
    demonstrated it. That distinction matters for adopters (a rootdir
    registration would not travel with the vendored tests, which is the whole
    reason the conftest exists) and it is not pinned here. The conftest's
    presence is asserted separately below, which is weaker than causation and is
    all this can honestly offer.
    """
    proc = _pytest(*SUITES, "--markers")
    assert proc.returncode == 0, f"`pytest --markers` failed:\n{proc.stdout}\n{proc.stderr}"
    assert "driftcheck" in proc.stdout, "`driftcheck` is not registered with pytest"
    assert (ENGINE_DIR / "tests" / "conftest.py").is_file(), (
        "the registration should live in a conftest beside the tests so it moves "
        "with them when they are vendored"
    )
