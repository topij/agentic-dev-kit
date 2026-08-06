"""What pins `.github/workflows/test.yml`'s TRIGGERS against the config (#329).

Narrow on purpose. This does not police the workflow's steps — `test_mutation_gate.py`
explains at length why grepping a workflow's text is a guarantee that a reviewer
walks through every round with a spelling the last one did not use, and records that
a bare `assert suite in .github/workflows/test.yml` anchor was deleted here as inert.

These assertions are a different shape: both sides are **parsed**, and the comparison
is between two structured values that must agree. A spelling variation cannot slip
past a list equality the way it slips past a substring search.

Two invariants, and the second is the one that fails open:

1. `push.branches` names exactly `vcs.protected_branch`. The literal exists because a
   workflow file cannot read `config/dev-model.yaml` and GitHub forbids `${{ }}` in
   `on:` triggers, so nothing in the file itself can resolve it — this test is the
   only thing standing between the two values and a silent divergence the day the
   protected branch is renamed. The failure it prevents is quiet: CI simply stops
   running on the protected branch, and nothing says so.

2. `pull_request` survives as a trigger at all. Scoping `push` without it leaves
   **every PR with no CI**, which is strictly worse than #329's duplicate runs — a
   red PR is loud, an unrun one is not, and `review.require_ci` would then refuse
   every merge. This is the fail-open direction, so it gets its own assertion rather
   than riding on the one above.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from _repo_layout import engine_dir, find_repo_root

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)

WORKFLOW = ".github/workflows/test.yml"

# Not kit-owned — there is no `.github/` entry in kit-manifest.json, so an adopter
# never receives this file and has no reason to have one at this path.
pytestmark = pytest.mark.kit_repo_only(WORKFLOW, "config/dev-model.yaml")


def _workflow() -> dict:
    """Parse the workflow, resolving YAML 1.1's `on` problem.

    PyYAML implements YAML 1.1, where the bare key `on` is a BOOLEAN — so the
    trigger block arrives under the key `True`, not `"on"`. A test reading
    `doc["on"]` raises KeyError against a perfectly valid workflow, and one using
    `doc.get("on", {})` silently sees an EMPTY trigger block and passes every
    assertion below vacuously. The second is why this is a helper with a comment
    rather than an inline `.get`.
    """
    doc = yaml.safe_load((REPO_ROOT / WORKFLOW).read_text(encoding="utf-8"))
    triggers = doc.get("on", doc.get(True))
    assert isinstance(triggers, dict), (
        f"{WORKFLOW} has no parseable `on:` block — got {triggers!r}. If this is a "
        f"YAML 1.1 truthy-key change, fix the helper, not the assertion"
    )
    return triggers


def _protected_branch() -> str:
    config = yaml.safe_load((REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8"))
    branch = ((config or {}).get("vcs") or {}).get("protected_branch")
    assert branch, "vcs.protected_branch is unset in config/dev-model.yaml"
    return branch


def test_ci_push_trigger_matches_the_configured_protected_branch() -> None:
    triggers = _workflow()
    branch = _protected_branch()

    push = triggers.get("push")
    assert isinstance(push, dict) and "branches" in push, (
        "`push:` must be scoped to the protected branch (#329). Unscoped, it fires "
        "alongside `pull_request:` for every push to a PR branch, so one push starts "
        "two identical runs that compete for a runner — and a starved job renders as "
        "`toolkit fail 15m1s`, indistinguishable from a real failure"
    )
    assert push["branches"] == [branch], (
        f"{WORKFLOW} runs `push` on {push['branches']} but "
        f"config/dev-model.yaml sets vcs.protected_branch = {branch!r}. A workflow "
        f"cannot read the config and GitHub forbids expressions in `on:`, so these "
        f"two literals can only be kept in step by this test. If the protected "
        f"branch was renamed, update the workflow"
    )


def test_pull_request_remains_a_trigger() -> None:
    """The fail-open half. Scoping `push` while dropping `pull_request` leaves every
    PR with no CI at all — quieter than the problem #329 fixed, and `review.require_ci`
    would then block every merge instead."""
    triggers = _workflow()
    assert "pull_request" in triggers, (
        "`pull_request:` is gone — with `push:` scoped to the protected branch, no "
        "PR would run CI at all"
    )
