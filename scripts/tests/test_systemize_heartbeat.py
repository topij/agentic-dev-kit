"""Heartbeat transitions and their refusals."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))
from systemize.config import load_settings  # noqa: E402
from systemize.errors import SystemizeError  # noqa: E402
from systemize.heartbeat import Heartbeat, lock_path  # noqa: E402
from systemize.identity import identity_digest  # noqa: E402
from test_systemize_support import DATE, make_repo  # noqa: E402

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


@pytest.fixture
def make(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = make_repo(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    monkeypatch.setenv("DEVKIT_ROOT", str(root))
    settings = load_settings(root)

    def build(mode: str = "test", date: str = DATE) -> Heartbeat:
        return Heartbeat(settings, mode=mode, window_days=7, date=date)
    return build


def _state(hb: Heartbeat) -> dict:
    return json.loads(hb.target.path.read_text())


def test_start_tick_complete_records_the_run(make) -> None:
    hb = make()
    hb.start()
    hb.tick("digest", None, DIGEST_A)
    hb.tick("cluster", "1/3", None)
    hb.tick("cluster", "2/3", DIGEST_A)
    hb.complete("complete")
    state = _state(hb)
    assert hb.target.path.name == f"post-merge-systemize_7d_test_{DATE}.json"
    assert state["status"] == "complete" and state["exit_reason"] == "complete"
    assert state["systemize_run_identity_digest"] == DIGEST_A
    assert state["slice"] == {"index": 2, "total": 3}
    assert [s["step"] for s in state["steps"]] == ["start", "digest", "cluster", "cluster", "done"]
    assert state["run_identity"]["schema"] == "post-merge-systemize-heartbeat-v1"
    assert not lock_path(hb.target).exists()


@pytest.mark.parametrize(
    "prepare, action, message",
    [
        (lambda hb: None, lambda hb: hb.tick("digest", None, None), "no heartbeat started"),
        (lambda hb: None, lambda hb: hb.complete("complete"), "no heartbeat started"),
        (lambda hb: hb.tick("cluster", "2/3", None), lambda hb: hb.tick("cluster", "1/3", None), "regressed"),
        (lambda hb: hb.tick("cluster", "1/3", None), lambda hb: hb.tick("cluster", "2/4", None), "total changed"),
        (lambda hb: hb.tick("digest", None, DIGEST_A), lambda hb: hb.tick("digest", None, DIGEST_B), "differs"),
        (lambda hb: hb.complete("complete"), lambda hb: hb.tick("x", None, None), "already complete"),
        (lambda hb: hb.complete("complete"), lambda hb: hb.complete("error"), "already completed"),
        (lambda hb: None, lambda hb: hb.tick("bad step!", None, None), "invalid heartbeat step"),
        (lambda hb: None, lambda hb: hb.tick("cluster", "4/3", None), "invalid --slice"),
        (lambda hb: None, lambda hb: hb.tick("digest", None, "sha256:short"), "invalid --run-identity-digest"),
        (lambda hb: None, lambda hb: hb.complete("timeout"), "invalid completion reason"),
    ],
)
def test_out_of_order_transitions_stop_and_preserve_state(make, prepare, action, message) -> None:
    hb = make()
    started = message != "no heartbeat started"
    if started:
        hb.start()
        prepare(hb)
    before = hb.target.path.read_bytes() if started else None
    with pytest.raises(SystemizeError, match=message):
        action(hb)
    assert (hb.target.path.read_bytes() if started else hb.target.path.exists()) == (before if started else False)


def test_an_identical_completion_is_idempotent(make) -> None:
    hb = make()
    hb.start()
    hb.complete("error")
    before = hb.target.path.read_bytes()
    assert hb.complete("error")["status"] == "complete"
    assert hb.target.path.read_bytes() == before


def test_a_held_lock_refuses_a_concurrent_writer(make) -> None:
    hb = make()
    hb.start()
    before = hb.target.path.read_bytes()
    lock_path(hb.target).write_text("12345")
    with pytest.raises(SystemizeError, match="lock .* is held"):
        hb.tick("digest", None, None)
    assert hb.target.path.read_bytes() == before
    assert lock_path(hb.target).read_text() == "12345"


def test_a_same_identity_restart_counts_and_resets(make) -> None:
    hb = make()
    hb.start()
    hb.tick("cluster", "2/2", None)
    hb.start()
    state = _state(hb)
    assert state["restarts"] == 1 and state["slice"] is None and state["status"] == "running"


def test_a_foreign_heartbeat_at_the_target_is_preserved(make) -> None:
    hb = make()
    hb.start()
    foreign = _state(hb)
    foreign["run_identity"] = {**foreign["run_identity"], "job": "someone-else"}
    foreign["run_identity_digest"] = identity_digest(foreign["run_identity"])
    hb.target.path.write_text(json.dumps(foreign))
    with pytest.raises(SystemizeError, match="different run"):
        hb.start()
    assert json.loads(hb.target.path.read_text())["run_identity"]["job"] == "someone-else"


def test_live_and_test_heartbeats_are_separate(make) -> None:
    assert make("live").target.path != make("test").target.path
