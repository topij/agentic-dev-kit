"""A LIVE gate across a linked worktree whose `state/` is a symlink (#1269).

The adopter's scheduler runs triage from a temporary linked worktree whose
`state/` is a symlink to the primary checkout's. One LIVE run was refused with
`repository identity mismatch`, and the gate survived it. These tests take that
shape with no `DEVKIT_STATE_ROOT`, so the state root is found from the worktree
and runs through the symlink. The repository-identity refusal comes from a
completed state another checkout wrote to the same state root. In the adopter's
case the state came from a kit that predates #1111's shared root. Both reach the
same refusal after the gate is held.

The first test shows the refused `new` releases its gate. The second shows where
a surviving gate comes from: the interactive `recover` the run made next keeps
its own gate as part of the `state-present-held` evidence it captures. After that,
every later LIVE run is refused as `single-writer-gate`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from test_triage_engine import (  # noqa: E402
    LIVE_STATE,
    approval_context,
    approval_for,
    git,
    repository,
    request,
)
from triage.canonical import loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402

LIVE_GATE = "triage/triage-pipeline-gate_live.lock"


def symlinked_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """The primary's `state/` holding another checkout's completed LIVE state,
    and a linked worktree whose `state/` links to it, entered as the cwd with no
    state-root override. Returns the primary's state directory and the worktree."""
    root = repository(tmp_path)
    state = root / "state"
    state.mkdir()
    other = repository(tmp_path / "other")
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state))
    run("new", context="interactive", request=request(other), start=other)
    presented = loads_exact((state / LIVE_STATE).read_bytes())
    completed = run(
        "resume", context="interactive", request={"approval": approval_for(presented, "park TRI-01")},
        start=other, approval_context=approval_context(presented, "park TRI-01"),
    )
    assert completed["outcome"] == "degraded-success", completed["detail"]
    assert not (state / LIVE_GATE).exists()

    worktree = tmp_path / "cron-worktree"
    git(root, "worktree", "add", "--detach", str(worktree), "HEAD")
    (worktree / "state").symlink_to(state, target_is_directory=True)
    monkeypatch.delenv("DEVKIT_STATE_ROOT")
    monkeypatch.delenv("DEVKIT_ROOT", raising=False)
    monkeypatch.chdir(worktree)
    return state, worktree


def test_a_live_new_refused_after_the_gate_is_held_releases_it_through_a_symlinked_state_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, worktree = symlinked_worktree(tmp_path, monkeypatch)
    assert (worktree / "state").is_symlink()
    state_before = (state / LIVE_STATE).read_bytes()

    refused = run("new", context="unattended", request={}, start=worktree)

    # `ready` is recorded only once `acquire` returned, and the identity check
    # that refuses runs after it, in the session-state validation.
    assert refused["capabilities"]["single-writer-state-gate"]["status"] == "ready"
    assert (refused["refusal_code"], refused["detail"]) == ("repository-identity", "repository identity mismatch")
    assert not (state / LIVE_GATE).exists()
    assert (state / LIVE_STATE).read_bytes() == state_before

    # Nothing held: the next run is refused for the same reason, not as a held gate.
    again = run("new", context="unattended", request={}, start=worktree)
    assert again["refusal_code"] == "repository-identity", again["detail"]
    assert not (state / LIVE_GATE).exists()


def test_the_gate_that_outlives_the_refused_run_is_the_one_recover_keeps_as_held_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, worktree = symlinked_worktree(tmp_path, monkeypatch)
    refused = run("new", context="unattended", request={}, start=worktree)
    assert refused["refusal_code"] == "repository-identity"
    assert not (state / LIVE_GATE).exists()

    recovered = run("recover", context="interactive", request={}, start=worktree)

    assert (recovered["outcome"], recovered["detail"]) == ("operator-held", "external-attempt-absence-unproven")
    gate = loads_exact((state / LIVE_GATE).read_bytes())
    bundles = sorted((state / "triage").glob("recovery-bundle_live_*.json"))
    assert len(bundles) == 1
    captured = loads_exact(bundles[0].read_bytes())["capture_core"]
    assert captured["old_gate_record"] == gate
    later = run("new", context="unattended", request={}, start=worktree)
    assert (later["refusal_code"], later["detail"]) == ("single-writer-gate", "single-writer gate is already held")
