"""The three systemize engines, run as real subprocesses against a fake forge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))
from test_systemize_support import (  # noqa: E402
    DATE,
    ENGINES,
    HEAD,
    comment,
    fake_env,
    make_repo,
    pr,
    run_args,
    run_engine,
    thread,
)

BOT = "coderabbitai"


def window_prs() -> list[dict]:
    return [
        pr(10, "2026-09-20T12:00:00Z", threads=[
            thread("T10a", [comment(101, BOT, "_🟠 Major_\n\nBug here."), comment(102, "someone", "fixed")], resolved=True),
            thread("T10b", [comment(103, BOT, "**Critical Severity**\n\nWorse."),
                            comment(104, BOT, "follow-up"), comment(105, BOT, "more"), comment(106, BOT, "and more")]),
        ], reviews=[comment(107, BOT, "**Actionable comments posted: 2**")], body="Refs #42"),
        pr(11, "2026-09-21T12:00:00Z", threads=[
            thread("T11a", [comment(111, "stranger", "_🔴 Critical_ untrusted")]),
        ]),
        pr(12, "2026-09-22T12:00:00Z", threads=[
            thread("T12a", [comment(121, BOT, "Severity: nitpick\n\nstyle")], outdated=True),
        ]),
        # Merged before the window but updated inside it: scanned, not collected.
        pr(9, "2026-09-10T12:00:00Z", updated="2026-09-22T00:00:00Z",
           threads=[thread("T9", [comment(91, BOT, "_🔴 Critical_ old")])]),
        pr(8, "2026-09-01T12:00:00Z"),
        pr(7, "2026-08-30T12:00:00Z"),
    ]


@pytest.fixture
def env_for(tmp_path: Path):
    def build(fixture: dict | None = None, **repo_kwargs):
        root = make_repo(tmp_path, **repo_kwargs)
        state = tmp_path / "sandbox"
        return root, state, fake_env(tmp_path, {"prs": window_prs(), **(fixture or {})}, root, state)
    return build


def _ok(result) -> dict:
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_fetch_digest_verify_and_heartbeat_run_end_to_end(env_for, tmp_path: Path) -> None:
    root, state, env = env_for()
    started = _ok(run_engine(root, "heartbeat_cli.py", ["start", *run_args()], env))
    assert started["status"] == "running"

    fetched = _ok(run_engine(root, "fetch_merged_prs.py", run_args(), env))
    raw = json.loads(Path(fetched["cache_path"]).read_text())
    assert Path(fetched["cache_path"]).is_relative_to(state)
    assert [p["number"] for p in raw["prs"]] == [10, 11, 12]
    assert raw["window"] == {"days": 7, "date": DATE, "start": "2026-09-17T00:00:00Z", "end": "2026-09-24T00:00:00Z"}
    assert raw["run_identity"]["protected_branch_head"] == HEAD
    assert raw["run_identity"]["execution_mode"] == "test"
    assert raw["prs"][0]["tracker_refs"] == [{"number": 42, "repo": "o/r", "source": "body-mention"}]
    # The embedded thread page held two comments; the rest came from ThreadComments.
    assert len(raw["prs"][0]["review_threads"][1]["comments"]) == 4

    built = _ok(run_engine(root, "digest_merged_prs.py", run_args(), env))
    digest = json.loads(Path(built["digest_path"]).read_text())
    assert [p["number"] for p in digest["prs"]] == [10, 12]  # 11 has only an untrusted finding
    ten = digest["prs"][0]
    assert ten["max_severity"] == "critical"
    assert {f["id"]: f["addressed"] for f in ten["findings"]} == {
        "thread:101": "addressed", "thread:103": "unaddressed", "review:107": "unevidenced"}
    assert digest["prs"][1]["findings"][0]["addressed"] == "outdated"
    assert digest["severity_limitations"] == [{"finding": "thread:121", "pr": 12, "source_severity": "nitpick"}]
    assert (digest["findings_pr_count"], digest["single_pass_recommended"], digest["n_batches"]) == (2, True, 1)
    assert built["run_identity_digest"] == fetched["run_identity_digest"]

    _ok(run_engine(root, "digest_merged_prs.py", [*run_args(), "--verify", built["digest_path"]], env))
    _ok(run_engine(root, "heartbeat_cli.py",
                   ["tick", *run_args(), "--step", "digest", "--run-identity-digest", fetched["run_identity_digest"]], env))
    _ok(run_engine(root, "heartbeat_cli.py", ["tick", *run_args(), "--step", "cluster", "--slice", "1/1"], env))
    done = _ok(run_engine(root, "heartbeat_cli.py", ["complete", *run_args(), "--reason", "complete"], env))
    assert done["status"] == "complete"


@pytest.mark.parametrize(
    "field, value",
    [
        ("prs", "reorder"),
        ("input_cap", {"applied": True, "omitted_prs": [99], "uncapped_findings_pr_count": 3}),
        ("findings_pr_count", 1),
        ("single_pass_recommended", False),
        ("n_batches", 2),
        ("batching", {"batch_size": 1, "single_pass_max_prs": 1, "max_findings_prs_per_run": 1}),
    ],
)
def test_verify_rejects_a_digest_that_selects_its_own_evidence(env_for, tmp_path: Path, field, value) -> None:
    root, _, env = env_for()
    _ok(run_engine(root, "fetch_merged_prs.py", run_args(), env))
    built = _ok(run_engine(root, "digest_merged_prs.py", run_args(), env))
    digest = json.loads(Path(built["digest_path"]).read_text())
    digest[field] = list(reversed(digest["prs"])) if value == "reorder" else value
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(digest))
    result = run_engine(root, "digest_merged_prs.py", [*run_args(), "--verify", str(tampered)], env)
    assert result.returncode == 1
    assert "disagrees with its raw bundle" in result.stderr


@pytest.mark.parametrize(
    "op, kind",
    [
        ("MergedPRs", "no_cursor"),
        ("MergedPRs", "error"),
        ("PR_reviewThreads", "no_pageinfo"),
        ("embedded", "no_cursor"),  # a thread's first comment page, inside PR_reviewThreads
        ("ThreadComments", "error"),
        ("PR_reviews", "error"),
        ("branch", "error"),
    ],
)
def test_a_failed_or_truncated_page_stops_without_writing(env_for, op, kind) -> None:
    root, state, env = env_for({"fault": {"op": op, "kind": kind}})
    result = run_engine(root, "fetch_merged_prs.py", run_args(), env)
    assert result.returncode == 1, result.stdout
    assert result.stderr.startswith("systemize: hard stop:")
    assert not state.exists() or not any(state.rglob("*.json"))


@pytest.mark.parametrize("missing", ENGINES)
def test_every_entry_point_refuses_a_partial_engine_set(env_for, missing) -> None:
    root, _, env = env_for(engines=tuple(e for e in ENGINES if e != missing))
    for name in ENGINES:
        if name == missing:
            continue
        args = ["start", *run_args()] if name == "heartbeat_cli.py" else run_args()
        result = run_engine(root, name, args, env)
        assert result.returncode == 1
        assert "partial" in result.stderr


@pytest.mark.parametrize(
    "args, code",
    [
        (["--mode", "prod", "--window-days", "7", "--date", DATE], 2),
        (["--mode", "test", "--window-days", "0", "--date", DATE], 2),
        (["--mode", "test", "--window-days", "7", "--date", "2026-9-23"], 2),
        (["--mode", "test", "--window-days", "7", "--date", "2026-02-30"], 2),
        (["--mode", "test", "--window-days", "7", "--date", DATE, "--bogus"], 2),
        (["--mode", "test", "--window-days", "9", "--date", DATE], 1),
    ],
)
def test_invocation_refusals(env_for, args, code) -> None:
    root, state, env = env_for()
    result = run_engine(root, "fetch_merged_prs.py", args, env)
    assert result.returncode == code, result.stderr
    assert not state.exists()
    assert not (Path(env["FAKE_GH_LOG"]).exists()), "the forge was contacted before the refusal"


def test_backfill_window_is_accepted_and_separate(env_for) -> None:
    root, _, env = env_for()
    normal = _ok(run_engine(root, "fetch_merged_prs.py", run_args(window=7), env))
    backfill = _ok(run_engine(root, "fetch_merged_prs.py", run_args(window=28), env))
    assert normal["cache_path"] != backfill["cache_path"]
    assert backfill["merged_in_window"] == 6


def test_digest_refuses_a_raw_bundle_from_another_mode_or_config(env_for) -> None:
    root, state, env = env_for()
    fetched = _ok(run_engine(root, "fetch_merged_prs.py", run_args(mode="test"), env))
    live_path = Path(fetched["cache_path"].replace("_test_", "_live_"))
    live_path.write_bytes(Path(fetched["cache_path"]).read_bytes())
    result = run_engine(root, "digest_merged_prs.py", run_args(mode="live"), env)
    assert result.returncode == 1
    assert "execution_mode" in result.stderr


def test_an_existing_foreign_artifact_is_preserved(env_for) -> None:
    root, state, env = env_for()
    target = state / "cache" / f"merged-prs_7d_test_{DATE}.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"artifact_kind": "something-else"}')
    result = run_engine(root, "fetch_merged_prs.py", run_args(), env)
    assert result.returncode == 1
    assert "foreign artifact kind" in result.stderr
    assert target.read_text() == '{"artifact_kind": "something-else"}'


def test_a_malformed_raw_bundle_is_a_one_line_hard_stop(env_for) -> None:
    root, _, env = env_for()
    fetched = _ok(run_engine(root, "fetch_merged_prs.py", run_args(), env))
    raw_path = Path(fetched["cache_path"])
    raw = json.loads(raw_path.read_text())
    raw["prs"] = [{"review_threads": "not a list"}]
    raw_path.write_text(json.dumps(raw))
    result = run_engine(root, "digest_merged_prs.py", run_args(), env)
    assert result.returncode == 1
    assert result.stderr.startswith("systemize: hard stop:")
    assert len(result.stderr.strip().splitlines()) == 1
