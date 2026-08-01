"""Tests for the layout resolver the other test modules import (#134).

**Why this file exists, stated plainly because its absence was a review
finding.** The change that added `_repo_layout.py` repaired a real defect and
pinned it with nothing. Both fallback-panel lenses reverted `find_repo_root`'s
walk-up to the pre-#134 arithmetic — `return start.parent`, unconditionally —
and `make mutation-test` reported `614 passed, 1 deselected`. A third run by the
author reproduced it. The mutant survives for a reason no future edit will
remove: in the kit's OWN layout the engines sit one level below the root, which
is exactly where `start.parent` lands, so the correct answer and the bug agree
here and disagree only in the vendored layout the fix is about.

Neither `make test` nor `.github/workflows/test.yml` can reach that layout —
both collect `scripts/tests` from an ordinary checkout. So the disagreement has
to be built rather than waited for, which is what the synthetic trees below do:
each is a `tmp_path` skeleton with a `.git` marker placed where an adopter's
would be, and no dependence on where this file is actually running from.

`engine_dir` already had a safety net — off-by-one there fails collection
outright with `ModuleNotFoundError` — but it is pinned here anyway, because
"caught by an unrelated import blowing up" is not a property anything states.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root


def _tree(root: Path, engines: str, *, git: bool = True) -> Path:
    """An adopter skeleton; returns the path a test module would occupy."""
    tests = root / engines / "tests"
    tests.mkdir(parents=True)
    if git:
        (root / ".git").mkdir()
    return tests / "test_something.py"


def _require_no_ancestor_marker(start: Path) -> None:
    """Fail legibly when the environment defeats a no-marker test.

    The two fallback tests below need `find_repo_root` to walk all the way out
    without matching, which assumes `tmp_path` is not itself inside a checkout.
    That holds for pytest's default temp root here and in CI, and stops holding
    under `--basetemp` pointed inside a repository — where the walk finds THAT
    repo's marker and the assertion fails while naming neither the cause nor
    `--basetemp`.

    Raised by the review bot, whose framing was that the tests would silently
    not reach their assertion. They do reach it and they fail, so this is
    legibility rather than a false pass — which is why the remedy is a named
    precondition and not the suggested `monkeypatch.setattr(Path, "exists",
    ...)`. Stubbing `Path.exists` globally disables it for every other caller
    in the process, including `_tree`'s own `mkdir` bookkeeping and anything a
    later test in the same module touches; a fixture that lies to the whole
    interpreter to make one assertion reachable buys legibility with a much
    larger surface.
    """
    offenders = [p for p in (start, *start.parents) if (p / ".git").exists()]
    assert not offenders, (
        f"this test needs a temp dir outside any git checkout, but {offenders[0]} "
        "carries a .git marker — rerun without --basetemp inside a repository"
    )


# The two prescribed layouts, and a third nobody prescribes — `paths.engines` is
# a free-form string, so depth is not one of two values. `parents[2]` is right
# for exactly the first; `start.parent` from the engine dir for exactly the
# first as well, which is why the kit's own suite could not tell them apart.
# Depth ZERO — the marker at the engine dir itself — is not reachable by
# parametrizing this, so it has its own test below.
@pytest.mark.parametrize("engines", ["scripts", "scripts/devkit", "tools/vendor/devkit"])
def test_repo_root_is_found_at_any_engine_depth(tmp_path: Path, engines: str) -> None:
    module = _tree(tmp_path, engines)

    assert find_repo_root(engine_dir(module)) == tmp_path


def test_a_marker_at_the_engine_dir_itself_is_found(tmp_path: Path) -> None:
    """`start` is among the candidates at all — MEMBERSHIP, not its position.

    Position is the next test's; keeping the two claims apart is the point,
    because an earlier version of this docstring asserted both and pinned only
    this one, which is what the round-3 lens caught.

    `for candidate in (start, *start.parents)` mirrors `kitconfig.repo_root`'s
    identical construction. Dropping the `start` term — `for candidate in
    start.parents` — left the whole suite green (`622 passed, 1 deselected`)
    until this test existed: every other case here puts the marker at least one
    level above the engine dir, so none of them can tell the two loops apart.

    Found by the adversarial panel lens, whose point was that
    `test_repo_root_is_found_at_any_engine_depth` claims more generality in its
    name than its parameters reach. Reaching depth zero needs a differently
    shaped tree, not another parameter — `engines` there is a path segment, and
    there is no segment meaning "no directory at all".
    """
    engines = tmp_path / "repo"
    tests = engines / "tests"
    tests.mkdir(parents=True)
    (engines / ".git").mkdir()

    assert find_repo_root(engine_dir(tests / "test_something.py")) == engines


def test_start_is_examined_before_its_parents_not_merely_included(tmp_path: Path) -> None:
    """Ordering, pinned — the test above pins membership and not sequence.

    Round 3's adversarial lens made exactly the complaint the test above makes
    of its own sibling: the docstring claimed the leading position was
    load-bearing, while the only mutant killed was dropping `start` entirely.
    Reordering to `(*start.parents, start)` — `start` still examined, just last
    — survived at `623 passed, 1 deselected`. The same untested leading term is
    in five other marker walks, two of them in `pr_watch.py`; that is `#204`,
    and this test covers only the copy below it.

    Membership and sequence only diverge when TWO markers are in scope, so that
    is what this builds: a marker at the engine dir itself and another above it.
    The nearer must win, which is the same property
    `test_the_nearest_git_marker_wins` asserts one level up the tree and cannot
    reach here, because neither of its markers sits at `start`.

    Not hypothetical: a vendored tree carrying its own `.git`, checked out
    inside an outer repository, is this shape — and resolving to the outer one
    would point every path built from it at the wrong project.
    """
    outer = tmp_path / "outer"
    (outer / ".git").mkdir(parents=True)
    engines = outer / "vendored" / "scripts" / "devkit"
    tests = engines / "tests"
    tests.mkdir(parents=True)
    (engines / ".git").mkdir()

    assert find_repo_root(engine_dir(tests / "test_something.py")) == engines


def test_engine_dir_is_the_directory_holding_the_tests_directory(tmp_path: Path) -> None:
    module = _tree(tmp_path, "scripts/devkit")

    assert engine_dir(module) == tmp_path / "scripts" / "devkit"


def test_the_nearest_git_marker_wins(tmp_path: Path) -> None:
    """A checkout inside another checkout resolves to the inner one.

    Not hypothetical: the panel that reviewed #134's repair ran in detached
    worktrees under a scratch root, and a vendored tree built for a test sits
    inside this repo's own during development.
    """
    outer = tmp_path / "outer"
    (outer / ".git").mkdir(parents=True)
    inner = outer / "vendored"
    module = _tree(inner, "scripts/devkit")

    assert find_repo_root(engine_dir(module)) == inner


def test_a_git_file_counts_as_a_marker(tmp_path: Path) -> None:
    """A linked worktree's `.git` is a FILE, not a directory.

    `git worktree add` writes `gitdir: …` into a regular file, so a resolver
    testing `.is_dir()` finds no root in exactly the trees the review panel
    runs in. `.exists()` is the load-bearing choice here, and this pins it.
    """
    root = tmp_path / "linked"
    module = _tree(root, "scripts/devkit", git=False)
    (root / ".git").write_text("gitdir: /elsewhere/.git/worktrees/x\n", encoding="utf-8")

    assert find_repo_root(engine_dir(module)) == root


def test_without_a_git_marker_it_falls_back_instead_of_raising(tmp_path: Path) -> None:
    """The documented fallback, pinned as the deliberate choice it is.

    Raising here — which `test_portability.py`'s private copy does — turns a
    `.git`-less export into a COLLECTION error at import time, which is the
    failure #134's repair exists to remove. So the fallback is load-bearing and
    a future edit that "tightens" it to raise must fail this test and read the
    reasoning in `_repo_layout`'s docstring first.
    """
    module = _tree(tmp_path / "nogit", "scripts", git=False)
    _require_no_ancestor_marker(engine_dir(module))

    # Nothing is found anywhere above, so the
    # fallback answers. It returns the engine dir's parent — correct for this
    # layout, and byte-identical to the `parents[2]` this replaced.
    assert find_repo_root(engine_dir(module)) == tmp_path / "nogit"


def test_the_fallback_is_wrong_in_a_nested_layout_and_that_is_known(tmp_path: Path) -> None:
    """The residual gap, pinned so it cannot be mistaken for a repaired case.

    With no `.git` anywhere, a nested engines dir resolves ONE SHORT — the exact
    #134 defect, still live on this path. It is not repaired here because the
    fallback deliberately mirrors `kitconfig.repo_root`, whose own depth
    problem is #60, still open. Pinning it makes the limit a stated property
    rather than something a reader has to infer from a docstring, and this test
    is the thing that fails if #60's resolution lands without updating here.
    """
    module = _tree(tmp_path / "nogit", "scripts/devkit", git=False)
    root = tmp_path / "nogit"
    _require_no_ancestor_marker(engine_dir(module))

    resolved = find_repo_root(engine_dir(module))

    assert resolved == root / "scripts", "the fallback's known depth limit moved"
    assert resolved != root, "if this now passes, #60 is settled — update this test"
