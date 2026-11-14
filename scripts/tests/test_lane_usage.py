"""lane_usage.py: rank lanes by recorded usage, from receipts and subagent transcripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE = engine_dir(Path(__file__)) / "lane_usage.py"
sys.path.insert(0, str(ENGINE.parent))
import lane_usage  # noqa: E402

SID_A = "11111111-1111-4111-8111-111111111111"
SID_B = "22222222-2222-4222-8222-222222222222"


def _usage(inp: int, out: int, cache_read: int = 0, cost: float | None = None) -> dict:
    return {
        "source": "claude json result",
        "usage": {"input_tokens": inp, "output_tokens": out, "cache_read_input_tokens": cache_read},
        "total_cost_usd": cost,
        "models": {"claude-x": {"inputTokens": inp}},
        "num_turns": 1,
        "duration_ms": 10,
    }


def _lane(
    sessions: Path,
    scope: str,
    *,
    runtime: str = "claude",
    usage: dict | None = None,
    session_id: str | None = SID_A,
    resumes: list[dict] | None = None,
    finished_at: str = "2026-11-10T12:00:00Z",
    terminal: bool = True,
) -> Path:
    lane = sessions / scope
    lane.mkdir(parents=True)
    final = lane / "launch-final-d1.txt"
    if session_id is not None:
        final.write_text(json.dumps({"type": "result", "session_id": session_id}))
    receipt: dict = {
        "descriptor_id": f"{scope}-d1",
        "status": "completed",
        "request": {"runtime": runtime, "compute": {"tier": "standard", "model": "opus"}},
    }
    if terminal:
        receipt["terminal"] = {
            "final_message_path": str(final),
            "usage": usage,
            "lane_state": "pr-ready",
            "resumes": resumes or [],
            "finished_at": finished_at,
        }
    path = lane / "launch-receipt-d1.json"
    path.write_text(json.dumps(receipt))
    return path


def _subagent(projects: Path, session_id: str, agent: str, messages: list[dict], meta=None):
    directory = projects / "-home-user-repo" / session_id / "subagents"
    directory.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"type": "assistant", "message": m}) for m in messages]
    lines.insert(1, "{not json")  # a torn line must not discard the rest
    (directory / f"{agent}.jsonl").write_text("\n".join(lines) + "\n")
    if meta is not None:
        (directory / f"{agent}.meta.json").write_text(json.dumps(meta))


def test_result_usage_sums_launch_and_resume_rounds_and_names_gaps(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(
        sessions,
        "lane-a",
        usage=_usage(10, 20, 5, cost=0.5),
        resumes=[
            {"round": 1, "session_id": SID_A, "usage": _usage(1, 2, cost=0.25)},
            {"round": 2, "session_id": SID_A, "usage": None},
        ],
    )
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    result = row["result"]
    assert result["available"] is True
    assert result["tokens"] == {
        "input_tokens": 11,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 5,
        "output_tokens": 22,
    }
    assert result["total_tokens"] == 38
    assert result["total_cost_usd"] == pytest.approx(0.75)
    assert result["rounds_counted"] == ["launch", "resume-1"]
    assert result["rounds_without_usage"] == ["resume-2"]
    assert row["session_ids"] == [SID_A]
    assert (row["tokens"], row["cost_usd"]) == (38, pytest.approx(0.75))
    assert row["subagent_tokens"] is None


def test_a_lane_with_no_usage_is_reported_unavailable_never_zero(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "codex-lane", runtime="codex", usage=None, session_id=None)
    _lane(sessions, "running-lane", terminal=False)
    report = lane_usage.build_report(sessions, projects)
    rows = {r["scope"]: r for r in report["lanes"]}
    codex = rows["codex-lane"]
    assert codex["result"] == {
        "available": False,
        "reason": "codex's final-text transport carries no usage figures",
    }
    assert "total_tokens" not in codex["result"]
    assert (codex["tokens"], codex["cost_usd"], codex["subagent_tokens"]) == (None, None, None)
    assert rows["running-lane"]["tokens"] is None
    assert codex["subagents"]["available"] is False
    assert "no terminal record" in rows["running-lane"]["result"]["reason"]
    assert sorted(report["lanes_without_usage"]) == ["codex-lane", "running-lane"]


def test_subagent_transcripts_are_summed_per_session_and_kept_apart(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(
        sessions,
        "lane-a",
        usage=_usage(10, 20),
        resumes=[{"round": 1, "session_id": SID_B, "usage": None}],
    )
    _subagent(
        projects,
        SID_A,
        "agent-1",
        [
            {"model": "claude-h", "usage": {"input_tokens": 100, "output_tokens": 7}},
            {"model": "claude-h", "usage": {"cache_read_input_tokens": 1000, "output_tokens": True}},
            {"content": "no usage here"},
        ],
        meta={"description": "review lens"},
    )
    _subagent(projects, SID_B, "agent-2", [{"usage": {"output_tokens": 3}}])
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    sub = row["subagents"]
    assert row["session_ids"] == [SID_A, SID_B]
    assert sub["available"] is True
    assert sub["agent_count"] == 2
    assert sub["tokens"] == {
        "input_tokens": 100,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 1000,
        "output_tokens": 10,
    }
    assert sub["agents"][0]["description"] == "review lens"
    assert sub["agents"][0]["assistant_messages"] == 2
    # The two sources are reported side by side, never summed.
    assert row["result"]["total_tokens"] == 30


def test_a_session_without_a_transcript_directory_is_unavailable(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    projects.mkdir()
    _lane(sessions, "lane-a", usage=_usage(1, 1))
    sub = lane_usage.build_report(sessions, projects)["lanes"][0]["subagents"]
    assert sub["available"] is False
    assert "no transcript directory" in sub["reason"]


def test_a_located_session_that_dispatched_nothing_is_a_real_zero(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    (projects / "-p" / SID_A).mkdir(parents=True)
    _lane(sessions, "lane-a", usage=_usage(1, 1))
    sub = lane_usage.build_report(sessions, projects)["lanes"][0]["subagents"]
    assert sub == {
        "available": True,
        "complete": True,
        "agent_count": 0,
        "tokens": dict.fromkeys(lane_usage.TOKEN_FIELDS, 0),
        "total_tokens": 0,
        "agents": [],
    }


@pytest.mark.parametrize(
    "bad_id", ["../../etc", "11111111111141118111111111111111", "", None, 7]
)
def test_a_non_canonical_session_id_never_becomes_a_path(tmp_path: Path, bad_id) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    path = _lane(sessions, "lane-a", usage=_usage(1, 1), session_id=None)
    (path.parent / "launch-final-d1.txt").write_text(
        json.dumps({"type": "result", "session_id": bad_id})
    )
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    assert row["session_ids"] == []
    assert row["subagents"]["reason"] == "receipt names no Claude session id"


def test_ranking_window_and_unreadable_receipts(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "small", usage=_usage(1, 1, cost=0.9))
    _lane(sessions, "big", usage=_usage(100, 100, cost=0.1))
    _lane(sessions, "old", usage=_usage(1000, 1000), finished_at="2026-10-01T00:00:00Z")
    (sessions / "broken").mkdir()
    (sessions / "broken" / "launch-receipt-x.json").write_text("{torn")

    report = lane_usage.build_report(sessions, projects)
    assert [r["scope"] for r in report["lanes"]] == ["old", "big", "small", "broken"]
    assert report["lanes"][-1]["note"] == "receipt is unreadable or not a JSON object"

    by_cost = lane_usage.build_report(sessions, projects, rank_by="cost")
    assert [r["scope"] for r in by_cost["lanes"]][:2] == ["small", "big"]

    windowed = lane_usage.build_report(
        sessions, projects, since=lane_usage.dt.date(2026, 11, 1)
    )
    # The unreadable receipt has no finish instant, so it stays visible.
    assert [r["scope"] for r in windowed["lanes"]] == ["big", "small", "broken"]


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_json_text_and_strict_exit(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "codex-lane", runtime="codex", usage=None, session_id=None)
    common = ["--sessions-dir", str(sessions), "--projects-root", str(projects)]

    text = _run(*common)
    assert text.returncode == 0, text.stderr
    assert "codex-lane" in text.stdout
    assert "no usage recorded from either source" in text.stdout

    strict = _run(*common, "--strict", "--json")
    assert strict.returncode == 1
    assert json.loads(strict.stdout)["lanes_without_usage"] == ["codex-lane"]

    assert _run(*common, "--since", "not-a-date").returncode == 2


def test_cli_honours_devkit_sessions_dir(tmp_path: Path) -> None:
    import os

    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=_usage(2, 3))
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    result = _run("--projects-root", str(projects), "--json", env=env)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["sessions_dir"] == str(sessions.resolve())
    assert report["lanes"][0]["result"]["total_tokens"] == 5


def test_records_of_one_response_are_counted_once(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=_usage(1, 1))
    directory = projects / "-p" / SID_A / "subagents"
    directory.mkdir(parents=True)
    block = {"id": "msg_1", "usage": {"input_tokens": 100, "output_tokens": 10}}
    streamed = {"id": "msg_2", "usage": {"input_tokens": 5, "output_tokens": 1}}
    final = {"id": "msg_2", "usage": {"input_tokens": 5, "output_tokens": 9}}
    lines = [
        {"requestId": "req_1", "message": block},
        {"requestId": "req_1", "message": block},
        {"requestId": "req_2", "message": streamed},
        {"requestId": "req_2", "message": final},
    ]
    (directory / "a.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    agent = row["subagents"]["agents"][0]
    assert agent["assistant_messages"] == 2
    assert row["subagent_tokens"] == 110 + 14


@pytest.mark.parametrize(
    ("usage", "reason"),
    [
        ({"source": "claude json result", "usage": {}}, "no round recorded runtime usage"),
        (
            {"usage": {"input_tokens": -5, "output_tokens": 3}},
            "malformed figures in launch",
        ),
        ({"usage": {"input_tokens": 1}, "total_cost_usd": "free"}, "malformed figures"),
    ],
)
def test_empty_or_malformed_usage_is_not_a_measurement(
    tmp_path: Path, usage: dict, reason: str
) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=usage, session_id=None)
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    assert row["result"]["available"] is False
    assert reason in row["result"]["reason"]
    assert row["tokens"] is None


def test_an_explicit_zero_is_a_measurement(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage={"usage": {"output_tokens": 0}}, session_id=None)
    assert lane_usage.build_report(sessions, projects)["lanes"][0]["tokens"] == 0


def test_a_missing_session_or_unreadable_transcript_makes_the_sum_incomplete(
    tmp_path: Path,
) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(
        sessions,
        "lane-a",
        usage=_usage(1, 1),
        resumes=[{"round": 1, "session_id": SID_B, "usage": None}],
    )
    _subagent(projects, SID_A, "agent-1", [{"usage": {"output_tokens": 3}}])
    (projects / "-home-user-repo" / SID_A / "subagents" / "bad.jsonl").write_bytes(b"\xff\xfe")
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    sub = row["subagents"]
    assert sub["available"] is True and sub["complete"] is False
    assert SID_B in sub["reason"] and "unreadable transcript(s) bad" in sub["reason"]
    assert sub["total_tokens"] == 3
    assert row["subagent_tokens"] is None


def test_text_report_names_each_sources_gap(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    projects.mkdir()
    _lane(sessions, "lane-a", usage=_usage(1, 1))
    text = lane_usage.render_text(lane_usage.build_report(sessions, projects))
    assert "lane-a subagents: no transcript directory" in text


def test_a_missing_sessions_dir_exits_2(tmp_path: Path) -> None:
    result = _run("--sessions-dir", str(tmp_path / "nope"))
    assert result.returncode == 2
    assert "sessions directory not found" in result.stderr
