"""Where the engines are, and where the repo root is, resolved rather than counted.

**The defect this exists to remove (#134).** Test modules used to open with
``REPO_ROOT = Path(__file__).resolve().parents[2]``. From a file at
``scripts/tests/test_x.py`` that is the repo root — but only while the engines
live at ``scripts/``. An adopter who vendors under ``paths.engines:
scripts/devkit`` (the layout ``docs/agentic-dev-kit/workflows/adopt.md`` defaults to, and the
one cs-toolkit actually uses) gets ``<repo>/scripts``, one directory short, and
every path built from it names something that does not exist. Measured on a
tree built exactly that way: two modules failed to import at all, which under a
plain ``pytest`` invocation aborts collection and runs **nothing**.

``CLAUDE.md`` also says configuration belongs in ``config/dev-model.yaml`` and
must not be hardcoded. ``paths.engines`` is precisely such a value, and an array
index is a hardcoding of it that no config edit can correct.

**Why the fallback does not raise.** ``kitconfig.repo_root`` settled on
walk-up-for-``.git``-then-fixed-depth after two attempts to probe more cleverly
were implemented and removed under ``safety-critical-changes.md`` rule 1; its
docstring records that no depth bound can distinguish "the root" from "one above
the root" without already knowing the layout. This mirrors that resolution
deliberately. The fallback returns what ``parents[2]`` returned, so a tree with
no ``.git`` above it — a ``git archive`` export before ``git init`` — behaves
exactly as it did before this module existed. ``test_portability.py``'s
private copy raises there instead; raising at import time is what turns a
missing ``.git`` into a *collection* error, which is the failure mode being
removed here, so it is not the form to copy.

**The fallback does not repair #134, it preserves it**, and that is worth saying
outright rather than leaving to be inferred: with no marker anywhere, a nested
engines directory still resolves one level short — the original defect, on the
one path where nothing can tell the layouts apart. That limit is ``#60``'s, not
this module's, and it is *pinned* rather than merely described, by
``test_repo_layout.py::test_the_fallback_is_wrong_in_a_nested_layout_and_that_is_known``
— which fails if ``#60``'s resolution lands without updating here.

**Six modules still carry their own copy** — ``test_portability.py``,
``test_mutation_gate.py``, ``test_pr_followup_hook.py``, ``test_pr_watch.py``,
``test_check_memory_budget.py`` and ``test_reconcile_sessions.py``. This said
*three* until a review lens counted; it named four, and the grep says six. Do
not transcribe this list — re-derive it, which is one grep:
``grep -c 'ENGINE_DIR = Path(__file__).resolve().parent.parent' scripts/tests/*.py``.
They already derive
the engine directory from their own location, so they are not affected by
#134 and were left alone rather than swept into its fix; consolidating them, and
deciding whether the raising fallback should survive anywhere, is ``#203``. Do
not read their divergence as a second opinion about what is correct.
"""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """The repository root at or above ``start``.

    Walks up for a ``.git`` marker. With none anywhere above, falls back to
    ``start.parent`` — the kit's own layout, and byte-identical to the
    ``parents[2]`` this replaced when ``start`` is the engine directory.
    """
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start.parent


def engine_dir(test_file: Path) -> Path:
    """The engines directory holding the test module at ``test_file``.

    Derived from where the file actually sits (``<engine-dir>/tests/x.py``), so
    it is correct under any ``paths.engines`` without reading the config — which
    matters because two of the callers need this *before* they can put
    ``kitconfig`` on ``sys.path`` to read the config with.
    """
    return test_file.resolve().parent.parent
