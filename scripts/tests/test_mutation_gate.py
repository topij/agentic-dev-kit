"""The mutation-testing exclusion is a mechanism, so it gets pinned like one.

`docs/agentic-dev-kit/fallback-review-panel.md` contract item 5 tells a reviewer
to trust `-m 'not driftcheck'` when deciding whether a mutant died. Two ways
that instruction can rot silently, both of which produce a confident wrong
answer rather than an error:

- **the marker spreads.** Marking anything beyond the byte-comparison test
  shrinks the mutation suite without saying so — every excluded test stops being
  able to kill anything, and the run still prints a reassuring pass count.
- **the marker is renamed or dropped** while the doctrine, the Makefile target
  and the failure message keep naming the old spelling. The command then
  deselects nothing, the drift test runs, and every mutant reads as killed —
  which is #33 exactly, restored by drift instead of by design.

So the assertions below are about the *set* the exclusion covers and about the
doc/code coupling, not about the drift test's own logic (that lives in
`test_kit_doctor.py`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITES = ("scripts/lib/state_paths/tests", "scripts/tests")

# The one test that is allowed to carry the marker. A bare node id, because the
# point is to pin WHICH test, not how many.
DRIFTCHECK_NODE = "scripts/tests/test_kit_doctor.py::test_kit_repo_self_check_is_clean"

MUTATION_INVOCATION = "-m 'not driftcheck'"


def _collect(*extra: str) -> list[str]:
    """Node ids pytest would collect, via a real subprocess run.

    Deliberately shells out to `pytest` rather than introspecting
    `pytestmark` attributes: the property under test is what the *documented
    command* does, and marker resolution (module-level marks, parametrisation,
    `-m` expression parsing) is pytest's, not something a reimplementation in
    the test would faithfully model.
    """
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", *SUITES, "--collect-only", "-q", "--no-header", *extra],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
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


def test_marker_is_registered_so_the_command_does_not_warn():
    """An unregistered mark still matches, but warns on the one command a
    reviewer is told to trust — and a warning there is how the command gets
    dropped and the folklore comes back."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", *SUITES, "--markers"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "driftcheck" in proc.stdout, (
        "`driftcheck` is not registered — scripts/tests/conftest.py must declare "
        "it so it travels with the vendored tests rather than depending on an "
        "adopter's rootdir ini file"
    )


def test_the_documented_command_matches_the_marker():
    """Doctrine, Makefile and failure message must all name the live spelling.

    This is the folklore guard: #33's complaint was that the exclusion lived in
    reviewers' heads. Writing it down only helps while what is written is still
    true, and a renamed marker is exactly the change that would not fail
    anything else here.
    """
    doctrine = (REPO_ROOT / "docs/agentic-dev-kit/fallback-review-panel.md").read_text(
        encoding="utf-8"
    )
    assert MUTATION_INVOCATION in doctrine, (
        f"fallback-review-panel.md must name {MUTATION_INVOCATION} — it is the "
        "surface that ships to adopters"
    )

    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "not driftcheck" in makefile, "make mutation-test must use the live marker"

    failure_message = (REPO_ROOT / "scripts/tests/test_kit_doctor.py").read_text(encoding="utf-8")
    assert MUTATION_INVOCATION in failure_message, (
        "the drift test's own failure message must name the escape hatch — it "
        "is the only one of these surfaces a reviewer is guaranteed to read, "
        "because it appears at the moment they hit the trap"
    )
