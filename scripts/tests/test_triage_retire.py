"""A completed triage session is retired by the next session-starting entry (#425).

Before this route, a valid ``completed`` state ended its mode: ``new`` refused it,
every other entry replayed its receipt, and nothing removed it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_triage_engine import approval_context, approval_for, repository, request
from triage import engine
from triage.canonical import loads_exact
from triage.engine import run
from triage.model import TriageError

LIVE = "triage/triage-pipeline-state_live.json"


def completed_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, bytes, Path]:
    """Drive a live session to a decision-only completion; return root, state, bytes, retired path."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / LIVE
    presented = loads_exact(state_path.read_bytes())
    completed = run(
        "resume", context="interactive",
        request={"approval": approval_for(presented, "park TRI-01")}, start=root,
        approval_context=approval_context(presented, "park TRI-01"),
    )
    assert completed["outcome"] == "degraded-success"
    raw = state_path.read_bytes()
    receipt = loads_exact(raw)["completion"]["completed_receipt_digest"]
    return root, state_path, raw, state_path.with_name(f"{state_path.name}.completed-{receipt[:16]}")


@pytest.mark.parametrize("entry", [None, "new"])
def test_session_starting_entry_retires_completed_live_state_and_drafts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str | None
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    previous_session = loads_exact(completed_raw)["run_identity"]["session"]
    result = run(entry, context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"].startswith(f"retired completed state to {retired} ")
    assert retired.read_bytes() == completed_raw
    fresh = loads_exact(state_path.read_bytes())
    assert fresh["phase"] == "reserved"
    assert fresh["run_identity"]["session"] != previous_session


@pytest.mark.parametrize(
    ("entry", "detail"),
    [("resume", "completed/decision-only"), ("recover", "captured state is valid; recovery refused")],
)
def test_resume_and_recover_leave_completed_state_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str, detail: str
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    result = run(entry, context="interactive", request={}, start=root)
    assert result["detail"] == detail
    assert state_path.read_bytes() == completed_raw
    assert not retired.exists()


def test_non_completed_state_is_never_retired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / LIVE
    awaiting = state_path.read_bytes()
    assert loads_exact(awaiting)["phase"] == "awaiting-approval"
    refused = run("new", context="interactive", request={}, start=root)
    assert refused["detail"] == "new refuses to overwrite active state"
    resumed = run(None, context="interactive", request={}, start=root)
    assert resumed["detail"] == "active session resumed"
    assert loads_exact(state_path.read_bytes())["phase"] == "awaiting-approval"
    assert [path.name for path in state_path.parent.iterdir() if ".completed-" in path.name] == []


def test_foreign_bytes_at_retired_path_hold_without_changing_either_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    retired.write_bytes(b"foreign\n")
    result = run(None, context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert state_path.read_bytes() == completed_raw
    assert retired.read_bytes() == b"foreign\n"


def test_interrupted_claim_after_retirement_starts_fresh_on_the_next_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    original = engine._new_draft

    def interrupted(*args, **kwargs):
        raise TriageError("simulated interruption after retirement")

    monkeypatch.setattr(engine, "_new_draft", interrupted)
    failed = run(None, context="interactive", request={}, start=root)
    assert failed["outcome"] == "hard-stop"
    assert not state_path.exists()
    assert retired.read_bytes() == completed_raw
    monkeypatch.setattr(engine, "_new_draft", original)
    fresh = run(None, context="interactive", request={}, start=root)
    assert fresh["detail"] == "durable triage state retained"
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"
    assert retired.read_bytes() == completed_raw


def test_unattended_retirement_then_holds_for_notification_like_a_fresh_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    result = run(None, context="unattended", request={}, start=root)
    assert retired.read_bytes() == completed_raw
    assert not state_path.exists()
    fresh_root = repository(tmp_path / "fresh")
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "fresh-state-root"))
    baseline = run(None, context="unattended", request={}, start=fresh_root)
    assert (result["outcome"], result["detail"]) == (baseline["outcome"], baseline["detail"])
