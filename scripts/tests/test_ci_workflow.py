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


def _concurrency() -> dict:
    """The `concurrency:` block, which is a top-level key rather than a trigger."""
    doc = yaml.safe_load((REPO_ROOT / WORKFLOW).read_text(encoding="utf-8"))
    block = doc.get("concurrency")
    assert isinstance(block, dict), (
        f"{WORKFLOW} has no parseable `concurrency:` block — got {block!r}"
    )
    return block


def test_ci_concurrency_group_isolates_each_protected_branch_run() -> None:
    """Kills: keying the concurrency group on the branch name.

    `cancel-in-progress: false` protects a run that is already EXECUTING. It does
    NOT protect a QUEUED one — GitHub cancels any pending run in the same group
    when a newer one arrives, whatever `cancel-in-progress` says. So a
    branch-keyed group put every push to the protected branch in one group, and
    two pushes landing while the first was still waiting for a runner cancelled
    the first. `CANCELLED` is in `pr_watch.summarize_checks`'s `bad` set, so that
    renders as a failing check on the protected branch — the exact
    cancelled-reads-as-failed confusion this workflow exists to remove.

    Established by a review lens live-firing the original stanza against a
    throwaway repo, not by reading the docs. The fix is at the KEY: `push` falls
    back to `github.run_id`, unique per run, so a protected-branch run is alone
    in its group and nothing can cancel it in either state.

    Both mutations this kills survived the entire suite before it existed."""
    group = _concurrency()["group"]

    assert "github.run_id" in group, (
        f"the concurrency group must fall back to `github.run_id` so a push run is "
        f"alone in its group and cannot be cancelled while queued — got {group!r}"
    )
    assert "github.head_ref" not in group, (
        f"`head_ref` keys the group on a BRANCH NAME, which shares a group across "
        f"every push to the protected branch (queued-run cancellation) and across "
        f"two PRs with the same branch name on a public repo — got {group!r}"
    )


def test_ci_concurrency_groups_a_pull_request_by_number_not_branch_name() -> None:
    """Kills: grouping PR runs by branch name.

    Superseding a PR's own older run is the point of the block, so PR runs must
    still share a group. Keying that on `head_ref` rather than the PR number
    means two PRs whose head branches happen to share a name — `patch-1` from two
    different forks, and this repo is public — land in one group and cancel each
    other. Nothing before this block could do that, so it is exposure the block
    introduced."""
    group = _concurrency()["group"]

    assert "github.event.pull_request.number" in group, (
        f"a pull_request run must be grouped by PR number, not by branch name — "
        f"got {group!r}"
    )


def test_ci_concurrency_never_cancels_in_progress_on_a_push() -> None:
    """Kills: `cancel-in-progress: true`.

    Redundant now that a push run is alone in its group, and kept because it is
    the one property that must not regress: a hardcoded `true` would cancel
    running protected-branch jobs if the group key ever widened again. A literal
    `True` and an expression are different YAML types, which is what this
    distinguishes."""
    cancel = _concurrency()["cancel-in-progress"]

    assert cancel is not True, (
        "cancel-in-progress must not be unconditionally true — that cancels runs "
        "on the protected branch, which this workflow exists to prevent"
    )
    assert isinstance(cancel, str) and "pull_request" in cancel, (
        f"cancel-in-progress must be conditioned on the pull_request event — got {cancel!r}"
    )
