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

# Several assertions below need the kit's own root `Makefile`, which is NOT
# vendored — an adopter gets the engines directory, not this file — so in a
# `scripts/devkit/` layout those checks are inapplicable rather than failing,
# and skipping is honest where asserting would report a defect that is not one.
#
# Note the doctrine file is a DIFFERENT case and the reason here used to say
# otherwise: `docs/agentic-dev-kit/fallback-review-panel.md` IS manifest-tracked,
# shipped by /adopt and refreshed by /upgrade, so adopters do have it. It is
# included in the predicate only because the one test that reads it also needs
# the kit layout to be meaningful. Making the marker assertions themselves
# portable is a real gap, filed separately.
_KIT_LAYOUT = (REPO_ROOT / "Makefile").is_file() and (
    REPO_ROOT / "docs" / "agentic-dev-kit" / "fallback-review-panel.md"
).is_file()
kit_repo_only = pytest.mark.skipif(
    not _KIT_LAYOUT, reason="needs the kit's own root Makefile, which adopters do not vendor"
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


def _make_would_run(target: str) -> str:
    """What `make` itself says it would execute for a target.

    Asks make rather than parsing the Makefile. Two earlier versions of this
    helper were text-based and both were defeated by text: a whole-file
    substring search was satisfied by `# was: -m 'not driftcheck'` sitting above
    a gutted recipe, and hand-parsing the first `target:` block read the WRONG
    recipe entirely — GNU make executes the LAST definition of a duplicated
    target, so appending a second block silently replaced what ran while the
    assertion kept reading the original.

    `make -n` has neither problem: comments never reach the output, and the
    command printed is the one that would actually run.
    """
    proc = subprocess.run(  # noqa: S603
        ["make", "-n", target],  # noqa: S607 — resolved via PATH, like every other make call here
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"`make -n {target}` failed:\n{proc.stdout}\n{proc.stderr}"
    lines = [
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip() and not line.startswith("make")
    ]
    assert lines, f"`make -n {target}` printed no command"
    return " ".join(lines)


def _phony_targets() -> list[str]:
    for line in (REPO_ROOT / "Makefile").read_text(encoding="utf-8").splitlines():
        if line.startswith(".PHONY:"):
            return line.split(":", 1)[1].split()
    raise AssertionError("no .PHONY line in the Makefile")


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

    "Only there" is checked against every `.PHONY` target rather than against
    `test:` alone, and covers `--deselect`/`-k` as well as the marker — the
    doctrine this repo ships names `--deselect <nodeid>` as a legitimate way to
    exclude the drift test, which makes it the spelling a reader is most likely
    to reach for on the wrong target.
    """
    mutation_cmd = _make_would_run("mutation-test")
    assert MUTATION_INVOCATION in mutation_cmd, (
        f"`make mutation-test` must pass {MUTATION_INVOCATION}; make would run: {mutation_cmd}"
    )

    for target in _phony_targets():
        if target == "mutation-test":
            continue
        cmd = _make_would_run(target)
        for spelling in ("driftcheck", "--deselect", "-k "):
            assert spelling not in cmd, (
                f"`make {target}` excludes the drift check via {spelling!r} — that "
                "is the gate catching a stale manifest locally, and only "
                f"`mutation-test` may drop it. make would run: {cmd}"
            )


@kit_repo_only
def test_the_mutation_run_covers_the_same_suites_as_the_normal_run():
    """A narrowed suite list is the same lie as a spread marker.

    Rewriting the recipe to name one module leaves every marker assertion above
    green, while the mutation run silently reports on a fraction of the suite.

    Known limit, measured: a narrowing severe enough to drop THIS file from the
    mutation target cannot be killed under `make mutation-test`, because the
    assertion is no longer collected. `make test` still runs the whole suite and
    does kill it. A guard cannot police a filter that can exclude the guard.
    """
    mutation_cmd = _make_would_run("mutation-test")
    test_cmd = _make_would_run("test")

    # Exact equality, not "contains each suite". A substring check passes when
    # the suite list is REPLACED by a path underneath it — `scripts/tests` is a
    # substring of `scripts/tests/test_kit_doctor.py` — which is how an earlier
    # version of this assertion let a one-module mutation run survive.
    assert mutation_cmd == f"{test_cmd} {MUTATION_INVOCATION}", (
        "`make mutation-test` must be exactly `make test` plus "
        f"{MUTATION_INVOCATION}, so the two can never cover different suites.\n"
        f"  test:          {test_cmd}\n"
        f"  mutation-test: {mutation_cmd}"
    )
    # Anchor the shared suite list against CI, which is the only definition of
    # "the whole suite" that neither target can edit. Equality above makes the
    # two targets agree with EACH OTHER; narrowing both symmetrically satisfies
    # it, and did, until this was added.
    ci = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    for suite in SUITES:
        assert f"{suite} " in f"{test_cmd} ", (
            f"`make test` no longer runs {suite} as a whole suite; "
            f"make would run: {test_cmd}"
        )
        assert suite in ci, (
            f"CI no longer runs {suite}, so this test's anchor is gone — fix the "
            "workflow or update SUITES deliberately"
        )


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
    """ACCIDENTAL-DRIFT DETECTOR ONLY. This is a text search, and it cannot
    survive anyone who reads it.

    Stated plainly because an earlier version of this test was presented as a
    guard and is not one: a review defeated it by replacing the whole of item 5
    with the folklore #33 exists to kill and parking both literals in an HTML
    comment, which passes. No text search over prose can do better, so the
    honest scope is small — it catches the marker being renamed or the paragraph
    deleted by someone who simply did not notice the other surface. It is worth
    keeping at that size and worth nothing beyond it.

    What actually protects the mechanism is the collection tests above, which
    exercise pytest rather than reading a file. Renaming the marker in the
    decorator and the conftest is caught there, not here.
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
