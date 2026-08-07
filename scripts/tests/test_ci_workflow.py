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

import re
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
    `doc.get("on", {})` silently sees an EMPTY trigger block. The assertions in
    this module as written would still fail against that empty dict rather than
    pass vacuously — an earlier version of this docstring claimed otherwise, and
    a review lens checked it. The hazard is real but latent: it is the NEXT
    membership-style assertion added here that would pass over nothing, which is
    why the resolution lives in this helper rather than in each caller.
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


EXPECTED_GROUP = (
    "${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}"
)
EXPECTED_CANCEL = "${{ github.event_name == 'pull_request' }}"


# GitHub expression operators are FIXED multi-character tokens. There is no
# standalone `=` or `|` operator, so `= =` and `| |` are not spaced spellings of
# `==` and `||` — they are a different token stream.
_OPERATORS = ("||", "&&", "==", "!=", "<=", ">=")
_EXPR = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)


def _norm_expression(inner: str) -> str:
    """Canonicalise ONE `${{ … }}` body: one space around each operator token."""
    for op in _OPERATORS:
        inner = inner.replace(op, f" {op} ")
    return " ".join(inner.split())


def _norm(value: object) -> str:
    """Canonicalise a workflow value so only a MEANING change can fail a compare.

    Two earlier forms of this helper were each wrong in an opposite direction,
    and both were found by a review lens rather than by reasoning:

    1. Collapsing whitespace RUNS was asymmetric — it tolerated extra spacing but
       could not manufacture a separator, so `a||b` failed against `a || b`
       despite being the same expression to GitHub. A false failure on this
       repo's own merge gate.
    2. Stripping ALL whitespace fixed that and opened a HIGH hole: it made
       `a | | b` and `a = = b` compare EQUAL to `a || b` and `a == b`, so the
       guard stopped firing on a changed token stream. It also flattened
       whitespace OUTSIDE `${{ }}`, which is literal YAML content — `}} - ${{`
       and `}}-${{` produce different concurrency-group strings at runtime, and
       the stripping form called them identical.

    So this does neither. Text outside `${{ }}` is compared EXACTLY, because
    there it is content. Inside, each operator token is given one space on each
    side and whitespace runs are then collapsed — which makes spacing around an
    operator irrelevant while leaving a SPLIT operator (`| |`) as two tokens that
    cannot canonicalise to one."""
    s = str(value)
    out: list[str] = []
    pos = 0
    for m in _EXPR.finditer(s):
        out.append(s[pos : m.start()])
        out.append("${{ " + _norm_expression(m.group(1)) + " }}")
        pos = m.end()
    out.append(s[pos:])
    return "".join(out)


def test_ci_concurrency_group_is_exactly_the_expression_that_isolates_push_runs() -> None:
    """Kills: any change to the group key's meaning, including operand ORDER.

    Asserted as an exact string rather than by membership, because membership is
    what let two meaning-inverting mutations through the first version of this
    test. Both lenses of the review panel and the review bot found that
    independently, which is why this is exact now:

      - `github.run_id || github.event.pull_request.number` — operands swapped.
        `run_id` is present and truthy on EVERY run, so the PR-number arm becomes
        dead code and each push to a PR gets its own group. That silently removes
        the superseding this block exists to provide, reopening the runner
        contention of #329. The old assertion passed, because the PR-number
        substring was still present.
      - reverting to `github.head_ref || github.ref` — the original defect.

    WHY EACH HALF IS WHAT IT IS, so a future editor updating this constant to
    match a change knows what they are giving up:

      pull_request → the PR NUMBER. Runs for one PR share a group and supersede
                     each other; two PRs sharing a head branch name (`patch-1`
                     from two forks, and this repo is public) do not collide.
      push         → `github.run_id`, unique per run, so a protected-branch run
                     is ALONE in its group. That is what makes it uncancellable
                     while QUEUED — `cancel-in-progress` only governs a run that
                     is already executing, and a queued run in a shared group is
                     cancelled unconditionally."""
    group = _norm(_concurrency()["group"])

    assert group == _norm(EXPECTED_GROUP), (
        f"the concurrency group expression does not match, ignoring whitespace.\n"
        f"  expected: {EXPECTED_GROUP}\n"
        f"  found:    {_concurrency()['group']}\n"
        f"This says the two differ, not HOW — read this test's docstring for what each "
        f"half does before changing either side. Spacing is not the cause: it is stripped."
    )


def test_ci_concurrency_group_puts_the_pull_request_arm_first() -> None:
    """Kills: the operand swap, by a different shape than the exact match above.

    Deliberately redundant with the equality assertion, and the redundancy was
    DISPUTED and then measured rather than argued. A review lens held that this
    test can never fail while its neighbour passes — true, and provable, while
    `EXPECTED_GROUP` is a fixed literal in which the arms are already in order.

    That is not the case this test is for. It is for the editor who makes the
    exact-match test pass by updating the CONSTANT to whatever the workflow now
    says. Measured both ways, with `__pycache__` cleared between runs:

      swap the operands in the workflow only    → both tests fail
      swap them AND update the constant to match → ONLY this test fails

    So the independent kill is real; it just does not appear in a mutation that
    leaves the constant alone, which is the mutation the dispute used."""
    group = _norm(_concurrency()["group"])

    assert "github.event.pull_request.number" in group and "github.run_id" in group, (
        f"both arms must be present — got {group!r}"
    )
    assert group.index("github.event.pull_request.number") < group.index("github.run_id"), (
        f"`github.run_id` is truthy on every run, so it must be the FALLBACK arm, not "
        f"the first — leading with it makes the pull_request arm dead code and silently "
        f"stops PR runs superseding each other. Got {group!r}"
    )


def test_ci_concurrency_cancel_is_exactly_the_pull_request_only_condition() -> None:
    """Kills: `cancel-in-progress: true`, and the polarity inversion.

    `github.event_name != 'pull_request'` still contains the substring
    `pull_request` and is still not a literal `True`, so the first version of
    this test passed it — while it cancels EXECUTING runs on the protected
    branch (the failure this whole file exists to prevent) and simultaneously
    disables PR superseding. Exact match is the only form that catches a
    polarity flip."""
    cancel = _concurrency()["cancel-in-progress"]

    assert cancel is not True, (
        "cancel-in-progress must not be unconditionally true — that cancels runs on "
        "the protected branch, which this workflow exists to prevent"
    )
    assert _norm(cancel) == _norm(EXPECTED_CANCEL), (
        f"cancel-in-progress does not match, ignoring whitespace.\n"
        f"  expected: {EXPECTED_CANCEL}\n"
        f"  found:    {cancel}\n"
        f"A polarity flip (`==` to `!=`) is one way to reach this and not the only one — "
        f"compare the two above rather than assuming which."
    )
