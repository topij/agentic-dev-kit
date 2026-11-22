"""lane_usage.py: rank lanes by recorded usage, from receipts and subagent transcripts."""

from __future__ import annotations

import json
import os
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


def _subagent(
    projects: Path,
    session_id: str,
    agent: str,
    messages: list[dict],
    meta=None,
    *,
    torn: bool = False,
):
    directory = projects / "-home-user-repo" / session_id / "subagents"
    directory.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"type": "assistant", "message": m}) for m in messages]
    if torn:
        lines.insert(1, "{not json")
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
    # A resume round with no figures leaves both sums a lower bound, so neither is
    # published as the lane's figure.
    assert (result["tokens_complete"], result["cost_complete"]) == (False, False)
    assert "resume-2 not counted" in result["reason"]
    assert (row["tokens"], row["cost_usd"], row["subagent_tokens"]) == (None, None, None)


def test_every_round_reporting_gives_complete_totals(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(
        sessions,
        "lane-a",
        usage=_usage(10, 20, 5, cost=0.5),
        resumes=[{"round": 1, "session_id": SID_A, "usage": _usage(1, 2, cost=0.25)}],
    )
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    assert (row["result"]["tokens_complete"], row["result"]["cost_complete"]) == (True, True)
    assert "reason" not in row["result"]
    assert (row["tokens"], row["cost_usd"]) == (38, pytest.approx(0.75))


def test_mixed_token_only_and_cost_only_rounds_publish_neither_total(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "mixed", usage=_usage(100, 100), session_id=None,
          resumes=[{"round": 1, "usage": {"usage": None, "total_cost_usd": 0.5}}])
    _lane(sessions, "whole", usage=_usage(5, 5, cost=0.1), session_id=None)
    report = lane_usage.build_report(sessions, projects)
    rows = {r["scope"]: r for r in report["lanes"]}
    mixed = rows["mixed"]
    assert mixed["result"]["total_tokens"] == 200
    assert mixed["result"]["total_cost_usd"] == 0.5
    assert (mixed["tokens"], mixed["cost_usd"]) == (None, None)
    assert "no token figures in resume-1" in mixed["result"]["reason"]
    assert "no cost in launch" in mixed["result"]["reason"]
    assert report["lanes_without_usage"] == ["mixed"]
    # The larger but partial sums do not outrank complete ones, by tokens or cost.
    assert [r["scope"] for r in report["lanes"]] == ["whole", "mixed"]
    by_cost = lane_usage.build_report(sessions, projects, rank_by="cost")
    assert [r["scope"] for r in by_cost["lanes"]] == ["whole", "mixed"]
    text = lane_usage.render_text(report)
    assert ">=200 part" in text and ">=0.5000" in text
    common = ["--sessions-dir", str(sessions), "--projects-root", str(projects)]
    (sessions / "whole" / "launch-receipt-d1.json").unlink()
    assert _run(*common, "--strict").returncode == 1


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
    # The boolean `output_tokens` is not a count: the valid figures are kept, and
    # the sum is marked partial.
    assert sub["complete"] is False
    assert "agent-1: 1 response(s) with malformed token fields" in sub["reason"]
    assert row["subagent_tokens"] is None
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


def _run(*args: str, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
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


def test_strict_does_not_accept_an_incomplete_transcript_sum(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=None)
    directory = projects / "-p" / SID_A / "subagents"
    directory.mkdir(parents=True)
    (directory / "bad.jsonl").write_bytes(b"\xff\xfe")
    common = ["--sessions-dir", str(sessions), "--projects-root", str(projects)]
    strict = _run(*common, "--strict", "--json")
    assert strict.returncode == 1, strict.stdout
    assert json.loads(strict.stdout)["lanes_without_usage"] == ["lane-a"]


def test_a_cost_only_result_has_a_cost_but_no_token_total(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage={"usage": None, "total_cost_usd": 0.5}, session_id=None)
    report = lane_usage.build_report(sessions, projects)
    row = report["lanes"][0]
    assert row["result"]["available"] is True
    assert row["result"]["total_tokens"] is None and row["result"]["tokens"] is None
    assert (row["tokens"], row["cost_usd"]) == (None, 0.5)
    assert report["lanes_without_usage"] == []


def test_a_missing_session_alone_ranks_and_renders_as_partial(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(
        sessions,
        "partial",
        usage=None,
        resumes=[{"round": 1, "session_id": SID_B, "usage": None}],
    )
    _subagent(projects, SID_A, "agent-1", [{"usage": {"output_tokens": 9000}}])
    _lane(sessions, "whole", usage=None, session_id=SID_B.replace("2", "3"))
    _subagent(projects, SID_B.replace("2", "3"), "agent-2", [{"usage": {"output_tokens": 5}}])
    report = lane_usage.build_report(sessions, projects, rank_by="subagent-tokens")
    rows = {r["scope"]: r for r in report["lanes"]}
    assert rows["partial"]["subagents"]["complete"] is False
    assert SID_B in rows["partial"]["subagents"]["reason"]
    assert "unreadable" not in rows["partial"]["subagents"]["reason"]
    # The larger but partial sum does not outrank a complete one.
    assert [r["scope"] for r in report["lanes"]] == ["whole", "partial"]
    assert ">=9,000 part" in lane_usage.render_text(report)


def test_a_torn_transcript_line_keeps_the_rest_but_marks_the_sum_partial(
    tmp_path: Path,
) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=None)
    _subagent(
        projects,
        SID_A,
        "agent-1",
        [{"usage": {"output_tokens": 4}}, {"usage": {"output_tokens": 6}}],
        torn=True,
    )
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    sub = row["subagents"]
    assert sub["total_tokens"] == 10
    assert sub["complete"] is False
    assert "agent-1: 1 unparseable line(s)" in sub["reason"]
    assert row["subagent_tokens"] is None


def test_a_clean_transcript_is_a_complete_sum(tmp_path: Path) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=None)
    _subagent(projects, SID_A, "agent-1", [{"usage": {"output_tokens": 4}}])
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    assert row["subagents"]["complete"] is True
    assert row["subagent_tokens"] == 4


def test_a_listing_failure_makes_the_sum_partial(tmp_path: Path, monkeypatch) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=None)
    _subagent(projects, SID_A, "agent-1", [{"usage": {"output_tokens": 4}}])
    real_iterdir = Path.iterdir

    def failing_iterdir(self: Path):
        if self.name == "subagents":
            raise PermissionError(13, "Permission denied")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", failing_iterdir)
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    sub = row["subagents"]
    assert sub["available"] is True and sub["complete"] is False
    assert "cannot list" in sub["reason"] and "Permission denied" in sub["reason"]
    assert row["subagent_tokens"] is None
    assert row["scope"] in lane_usage.build_report(sessions, projects)["lanes_without_usage"]


def test_a_project_that_cannot_be_checked_makes_the_sum_partial(
    tmp_path: Path, monkeypatch
) -> None:
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane-a", usage=None)
    _subagent(projects, SID_A, "agent-1", [{"usage": {"output_tokens": 4}}])
    (projects / "-other").mkdir()
    real_stat = Path.stat

    def failing_stat(self: Path, *args, **kwargs):
        if self.parent.name == "-other":
            raise PermissionError(13, "Permission denied")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", failing_stat)
    sub = lane_usage.build_report(sessions, projects)["lanes"][0]["subagents"]
    assert sub["complete"] is False
    assert "cannot check" in sub["reason"]


@pytest.mark.parametrize("damaged", [
    b"{torn", b"\xff", b'{"type":"assistant","message":{}}',
    b'{"message":{"usage":{"input_tokens":-1}}}', b'{"message":{"usage":{}}}',
])
def test_damaged_transcript_keeps_usable_records_as_partial(tmp_path, damaged):
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane", usage=None)
    _subagent(projects, SID_A, "agent", [{"usage": {"output_tokens": 8}}])
    path = projects / "-home-user-repo" / SID_A / "subagents" / "agent.jsonl"
    with path.open("ab") as handle:
        handle.write(damaged + b"\n")
    run = _run("--sessions-dir", str(sessions), "--projects-root", str(projects), "--strict", "--json")
    row = json.loads(run.stdout)["lanes"][0]
    assert run.returncode == 1 and row["subagent_tokens"] is None
    assert row["subagents"]["total_tokens"] == 8
    assert "agent" in row["subagents"]["reason"]


def test_missing_launch_identity_leaves_known_resume_transcripts_partial(tmp_path):
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane", usage=None, session_id=None,
          resumes=[{"round": 1, "session_id": SID_B}])
    _subagent(projects, SID_B, "agent", [{"usage": {"output_tokens": 8}}])
    row = lane_usage.build_report(sessions, projects)["lanes"][0]
    assert row["subagent_tokens"] is None and row["subagents"]["total_tokens"] == 8
    assert "no Claude session id" in row["subagents"]["reason"]


@pytest.mark.parametrize("resumes", [[None], "malformed"])
def test_malformed_resume_metadata_cannot_complete_a_total(resumes):
    result = lane_usage.result_usage({"usage": _usage(1, 2, cost=0.1), "resumes": resumes})
    assert result["total_tokens"] == 3
    assert result["tokens_complete"] is False and result["cost_complete"] is False
    assert "not counted" in result["reason"]


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize(
    ("extra_usage", "expected_sum", "gap"),
    [
        ({"output_tokens": 5, "input_tokens": 9}, 14, None),
        ({"output_tokens": 4, "input_tokens": -1}, 5, "malformed token fields"),
        ({"output_tokens": 4, "cache_read_input_tokens": 7}, 12, None),
    ],
)
def test_repeated_response_records_preserve_fields_and_gaps(
    tmp_path, reverse, extra_usage, expected_sum, gap
):
    sessions, projects = tmp_path / "sessions", tmp_path / "projects"
    _lane(sessions, "lane", usage=None)
    messages = [
        {"id": "msg", "usage": {"output_tokens": 5}},
        {"id": "msg", "usage": extra_usage},
    ]
    _subagent(projects, SID_A, "agent", messages[::-1] if reverse else messages)
    run = _run("--sessions-dir", str(sessions), "--projects-root", str(projects), "--strict", "--json")
    row = json.loads(run.stdout)["lanes"][0]
    assert row["subagents"]["total_tokens"] == expected_sum
    assert row["subagents"]["agents"][0]["assistant_messages"] == 1
    if gap is None:
        assert run.returncode == 0 and row["subagent_tokens"] == expected_sum
    else:
        assert run.returncode == 1 and row["subagent_tokens"] is None
        assert gap in row["subagents"]["reason"]


def test_conflicting_input_counts_produce_a_lower_bound(tmp_path):
    _subagent(tmp_path, SID_A, "agent", [
        {"id": "same", "usage": {"input_tokens": 17, "output_tokens": 1}},
        {"id": "same", "usage": {"input_tokens": 12, "output_tokens": 2}},
    ])
    source = lane_usage.subagent_usage(tmp_path, [SID_A])
    assert source["total_tokens"] == 14 and not source["complete"]
    assert "conflicting response counts for input_tokens" in source["reason"]


@pytest.mark.parametrize(("role", "complete"), [("assistant", False), ("user", True)])
def test_nested_role_identifies_untyped_records_without_usage(tmp_path, role, complete):
    _subagent(tmp_path, SID_A, "agent", [{"id": "first", "usage": {"output_tokens": 4}}])
    path = tmp_path / "-home-user-repo" / SID_A / "subagents" / "agent.jsonl"
    with path.open("a") as handle:
        handle.write(json.dumps({"message": {"role": role, "content": []}}) + "\n")
    source = lane_usage.subagent_usage(tmp_path, [SID_A])
    assert source["complete"] is complete and source["total_tokens"] == 4


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd, env=_no_git_env(), capture_output=True, check=True,
    )


def _no_git_env(**extra: str) -> dict:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.pop("DEVKIT_SESSIONS_DIR", None)
    return {**env, **extra}


def _primary_with_linked(tmp_path: Path) -> tuple[Path, Path]:
    primary, linked = tmp_path / "a" / "primary", tmp_path / "b" / "linked"
    primary.mkdir(parents=True)
    _git("init", "-q", str(primary), cwd=tmp_path)
    _git("commit", "-q", "--allow-empty", "-m", "c", cwd=primary)
    _git("worktree", "add", "-q", str(linked), cwd=primary)
    return primary, linked


def _resolved_sessions_dir(cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return _run("--projects-root", str(cwd / "no-projects"), "--json", env=env, cwd=cwd)


def test_default_sessions_dir_is_beside_the_primary_from_a_linked_worktree(tmp_path: Path) -> None:
    primary, linked = _primary_with_linked(tmp_path)
    (primary.parent / "dev-model-sessions").mkdir()
    result = _resolved_sessions_dir(linked, _no_git_env())
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["sessions_dir"] == str((primary.parent / "dev-model-sessions").resolve())


@pytest.mark.parametrize("variable", ["GIT_DIR", "GIT_COMMON_DIR"])
def test_an_inherited_git_variable_does_not_choose_another_repository(tmp_path: Path, variable: str) -> None:
    """Before, `git worktree list` honoured the variable and listed the other repository."""
    primary, linked = _primary_with_linked(tmp_path)
    (primary.parent / "dev-model-sessions").mkdir()
    other = tmp_path / "c" / "other"
    other.mkdir(parents=True)
    _git("init", "-q", str(other), cwd=tmp_path)
    _git("commit", "-q", "--allow-empty", "-m", "c", cwd=other)
    (other.parent / "dev-model-sessions").mkdir()
    result = _resolved_sessions_dir(linked, _no_git_env(**{variable: str(other / ".git")}))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["sessions_dir"] == str((primary.parent / "dev-model-sessions").resolve())


def test_a_bare_primary_keeps_the_invoking_checkout(tmp_path: Path) -> None:
    """As `devkit_default_sessions_dir` does: a bare repository has no checkout to sit beside."""
    source, bare, linked = tmp_path / "src", tmp_path / "a" / "bare.git", tmp_path / "b" / "linked"
    source.mkdir()
    _git("init", "-q", str(source), cwd=tmp_path)
    _git("commit", "-q", "--allow-empty", "-m", "c", cwd=source)
    _git("clone", "-q", "--bare", str(source), str(bare), cwd=tmp_path)
    _git("worktree", "add", "-q", str(linked), cwd=bare)
    (linked.parent / "dev-model-sessions").mkdir()
    result = _resolved_sessions_dir(linked, _no_git_env())
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["sessions_dir"] == str((linked.parent / "dev-model-sessions").resolve())


def test_outside_any_checkout_the_default_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "plain"
    outside.mkdir()
    if any((d / ".git").exists() for d in (outside, *outside.parents)):
        pytest.skip("the test's temporary directory sits inside a checkout")
    result = _resolved_sessions_dir(outside, _no_git_env())
    assert result.returncode == 2
    assert "cannot resolve the sessions directory" in result.stderr
