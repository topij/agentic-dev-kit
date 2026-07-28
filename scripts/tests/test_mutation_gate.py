"""The mutation-testing exclusion is a mechanism, so it gets pinned like one.

`docs/agentic-dev-kit/fallback-review-panel.md` contract item 5 tells a reviewer
to trust `-m 'not driftcheck'` when deciding whether a mutant died. Ways that
instruction can rot silently — all of which produce a confident wrong answer
rather than an error:

- **the marker spreads.** Marking anything beyond the byte-comparison test
  shrinks the mutation suite without saying so — every excluded test stops being
  able to kill anything, and the run still prints a reassuring pass count.
- **the exclusion moves to the wrong target.** `-m 'not driftcheck'` on the
  `test:` recipe disables the drift gate for *normal* runs, where it is the only
  thing standing between a stale manifest and a green local suite.
- **the mutation run quietly narrows.** A recipe that names fewer suites than
  `test:` reports on less than the reviewer believes they ran.
- **the drift test stops running at all** (a stacked `skip`), which collection
  cannot see: `--collect-only` lists skipped tests exactly like live ones.
- **the marker is renamed or dropped** while the doctrine, the Makefile target
  and the failure message keep naming the old spelling.

The first review of this file found its assertions were satisfiable by parking
the expected literal in a comment, so the Makefile checks below parse the
*recipe* for a target with comments stripped, and the failure-message check
triggers the real assertion instead of grepping the file it lives in.
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
SUITES = ("scripts/lib/state_paths/tests", "scripts/tests")

# The one test that is allowed to carry the marker. A bare node id, because the
# point is to pin WHICH test, not how many.
DRIFTCHECK_NODE = "scripts/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean"

MUTATION_INVOCATION = "-m 'not driftcheck'"

# Several assertions below read the kit's OWN repo layout (its Makefile, its
# doctrine file). Those files are not vendored into an adopter's tree, so in a
# `scripts/devkit/` layout the checks are not failing — they are inapplicable.
# Skipping is honest; asserting would report a defect that is not one. Making
# the marker assertions themselves portable is a real gap, filed separately.
_KIT_LAYOUT = (REPO_ROOT / "Makefile").is_file() and (
    REPO_ROOT / "docs" / "agentic-dev-kit" / "fallback-review-panel.md"
).is_file()
kit_repo_only = pytest.mark.skipif(
    not _KIT_LAYOUT, reason="asserts on the kit's own Makefile/doctrine, which adopters do not vendor"
)


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


def _recipe(target: str) -> list[str]:
    """The command lines of a Makefile target, comments and blanks stripped.

    Whole-file substring checks were the first version of this and are worth
    nothing: `# was: -m 'not driftcheck'` above a gutted recipe satisfied them.
    """
    lines = (REPO_ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    recipe: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith(f"{target}:"):
            collecting = True
            continue
        if collecting:
            if line.startswith("\t"):
                body = line.split("#", 1)[0].strip()
                if body:
                    recipe.append(body)
            elif line.strip():
                break
    assert recipe, f"no recipe found for Makefile target `{target}`"
    return recipe


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

    Asserts EXECUTION, deliberately not a pass. An earlier version of this test
    required `1 passed`, which made it fail for any behaviour-only mutation to a
    kit-owned file — reintroducing #33 inside the very run that exists to escape
    it, and caught here only by mutation-testing this file. Whether the drift
    test passes is `test_kit_repo_self_check_is_clean`'s own business; this one
    only cares that it is not silently inert.
    """
    proc = _pytest(DRIFTCHECK_NODE, "-q", "--no-header")
    assert "skipped" not in proc.stdout, (
        "the drift test is skipped, so it guards nothing:\n" + proc.stdout
    )
    assert "1 passed" in proc.stdout or "1 failed" in proc.stdout, (
        "the drift test must RUN, not merely be collected; got:\n" + proc.stdout
    )


@kit_repo_only
def test_the_exclusion_is_on_the_mutation_target_and_only_there():
    """The flag belongs to `mutation-test`, never to `test`.

    On `test:` it is actively harmful: `make test` is what CLAUDE.md names as
    this repo's verification command, and with the drift test deselected there a
    genuinely stale manifest passes the local gate silently.
    """
    mutation_recipe = " ".join(_recipe("mutation-test"))
    test_recipe = " ".join(_recipe("test"))

    assert MUTATION_INVOCATION in mutation_recipe, (
        f"`make mutation-test` must pass {MUTATION_INVOCATION}; recipe is: {mutation_recipe}"
    )
    assert "driftcheck" not in test_recipe, (
        "`make test` must NOT exclude the drift check — that is the gate that "
        f"catches a stale manifest locally. Recipe is: {test_recipe}"
    )


@kit_repo_only
def test_the_mutation_run_covers_the_same_suites_as_the_normal_run():
    """A narrowed suite list is the same lie as a spread marker.

    Rewriting the recipe to name one module leaves every marker assertion above
    green, while the mutation run silently reports on a fraction of the suite.

    Known limit, measured: a narrowing severe enough to drop THIS file from the
    mutation target cannot be killed under `make mutation-test`, because the
    assertion is no longer collected. `make test` and CI both still run the
    whole suite unfiltered and do kill it. A guard cannot police a filter that
    can exclude the guard.
    """
    mutation_recipe = " ".join(_recipe("mutation-test"))
    test_recipe = " ".join(_recipe("test"))

    # Exact equality, not "contains each suite". A substring check passes when
    # the suite list is REPLACED by a path underneath it — `scripts/tests` is a
    # substring of `scripts/tests/test_kit_doctor.py` — which is how the first
    # version of this assertion let a one-module mutation run survive.
    assert mutation_recipe == f"{test_recipe} {MUTATION_INVOCATION}", (
        "`make mutation-test` must be exactly `make test` plus "
        f"{MUTATION_INVOCATION}, so the two can never cover different suites.\n"
        f"  test:          {test_recipe}\n"
        f"  mutation-test: {mutation_recipe}"
    )
    for suite in SUITES:
        assert suite in test_recipe, f"`make test` no longer runs {suite}"


def test_the_drift_failure_message_names_the_escape_hatch(monkeypatch):
    """Trigger the real assertion and read the real message.

    The first version of this test grepped `test_kit_doctor.py` for the literal,
    which a copy of the string in an unrelated comment satisfied while the
    message itself said nothing. The message is the only one of these surfaces a
    reviewer is guaranteed to read, because it appears at the moment they hit
    the trap — so it is checked by being raised.
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


def test_marker_is_registered_by_the_conftest_beside_the_tests():
    """Registration must come from the conftest, not an adopter's rootdir ini.

    An unregistered mark still matches under `-m`, so the exclusion would work
    either way — it would just warn on the one command a reviewer is told to
    trust, which is how the command gets dropped and the folklore comes back.
    """
    proc = _pytest(*SUITES, "--markers")
    assert proc.returncode == 0, f"`pytest --markers` failed:\n{proc.stdout}\n{proc.stderr}"
    assert "driftcheck" in proc.stdout, (
        "`driftcheck` is not registered — scripts/tests/conftest.py must declare "
        "it so it travels with the vendored tests"
    )
    assert (ENGINE_DIR / "tests" / "conftest.py").is_file(), (
        "the registration must live in a conftest beside the tests, so it moves "
        "with them when they are vendored"
    )


@kit_repo_only
def test_the_doctrine_names_the_live_spelling():
    """The folklore guard: #33's complaint was that the exclusion lived in
    reviewers' heads. Writing it down helps only while what is written is true.

    Note what this does and does not cover: renaming the marker in the decorator
    and the conftest is caught by the two collection tests above, not here. This
    catches the opposite drift — code keeps the marker, prose stops naming it.
    """
    doctrine = (REPO_ROOT / "docs/agentic-dev-kit/fallback-review-panel.md").read_text(
        encoding="utf-8"
    )
    assert MUTATION_INVOCATION in doctrine, (
        f"fallback-review-panel.md must name {MUTATION_INVOCATION} — it is the "
        "surface that ships to adopters"
    )
    assert "deselected" in doctrine, (
        "the doctrine must tell the reader to confirm the exclusion actually "
        "deselected something; an `-m` naming an unapplied marker is silent"
    )
