from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


ENGINE_DIR = Path(__file__).resolve().parent.parent


def _load_pr_watch() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pr_watch_under_test", ENGINE_DIR / "pr_watch.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _green_view(**overrides):
    view = {
        "number": 7,
        "url": "https://example.test/pr/7",
        "state": "OPEN",
        "isDraft": False,
        "baseRefName": "trunk",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "headRefOid": "abc123",
        "statusCheckRollup": [
            {"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS"}
        ],
        "comments": [],
        "reviews": [],
    }
    view.update(overrides)
    return view


def test_changes_requested_and_blocked_merge_state_never_settle_done() -> None:
    pr_watch = _load_pr_watch()
    review = {
        "id": "review-1",
        "author": {"login": "reviewer"},
        "body": "Please fix the unsafe branch deletion.",
    }
    view = _green_view(
        mergeStateStatus="BLOCKED",
        reviewDecision="CHANGES_REQUESTED",
        reviews=[review],
    )
    comments = pr_watch.collect_comments(view, [])
    seen = {
        key for comment in comments for key in (comment["key"], comment["content_key"])
    }

    report = pr_watch.build_report(view, [], seen)

    assert report["new_comments"] == []
    assert report["done"] is False
    assert "merge state is BLOCKED" in report["merge_blockers"]
    assert "review decision is CHANGES_REQUESTED" in report["merge_blockers"]


def test_unknown_or_non_open_pr_state_never_settles_done() -> None:
    pr_watch = _load_pr_watch()

    unknown = pr_watch.build_report(_green_view(mergeStateStatus="UNKNOWN"), [], set())
    merged = pr_watch.build_report(
        _green_view(state="MERGED", mergeStateStatus="UNKNOWN"), [], set()
    )

    assert unknown["done"] is False
    assert "merge state is UNKNOWN" in unknown["merge_blockers"]
    assert merged["done"] is False
    assert "PR state is MERGED" in merged["merge_blockers"]


def test_unstable_is_allowed_only_when_remaining_check_is_informational() -> None:
    pr_watch = _load_pr_watch()
    receipt = {"head": "abc123", "source": "fallback:codex"}
    coderabbit_pending = {
        "context": "CodeRabbit",
        "state": "PENDING",
    }

    informational_only = pr_watch.build_report(
        _green_view(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {"name": "tests", "conclusion": "SUCCESS"},
                coderabbit_pending,
            ],
        ),
        [],
        set(),
        review_receipt=receipt,
    )
    unexplained_unstable = pr_watch.build_report(
        _green_view(mergeStateStatus="UNSTABLE"),
        [],
        set(),
        review_receipt=receipt,
    )
    successful_informational = pr_watch.build_report(
        _green_view(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {"name": "tests", "conclusion": "SUCCESS"},
                {"context": "CodeRabbit", "state": "SUCCESS"},
            ],
        ),
        [],
        set(),
        review_receipt=receipt,
    )

    assert informational_only["done"] is True
    assert "merge state is UNSTABLE" not in informational_only["merge_blockers"]
    assert unexplained_unstable["done"] is False
    assert "merge state is UNSTABLE" in unexplained_unstable["merge_blockers"]
    assert successful_informational["done"] is False
    assert "merge state is UNSTABLE" in successful_informational["merge_blockers"]


def test_review_unavailable_overrides_coderabbit_summary_noise() -> None:
    pr_watch = _load_pr_watch()
    body = """<!-- This is an auto-generated comment: summarize by coderabbit.ai -->
Review limit reached. We couldn't start this review.
"""
    view = _green_view(
        comments=[{"id": "notice-1", "author": {"login": "coderabbitai"}, "body": body}]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "coderabbit"},
    )

    assert report["done"] is False
    assert len(report["new_comments"]) == 1
    assert (
        report["new_comments"][0]["review_unavailable_reason"] == "review limit reached"
    )


def test_acknowledged_unavailable_notice_still_needs_review_evidence() -> None:
    pr_watch = _load_pr_watch()
    body = "Review limit reached. We couldn't start this review."
    view = _green_view(
        reviewDecision="",
        comments=[
            {"id": "notice-1", "author": {"login": "coderabbitai"}, "body": body}
        ],
    )
    comments = pr_watch.collect_comments(view, [])
    seen = {
        key for comment in comments for key in (comment["key"], comment["content_key"])
    }

    report = pr_watch.build_report(view, [], seen)

    assert report["new_comments"] == []
    assert report["done"] is False
    assert (
        "independent review evidence is missing for current head"
        in report["merge_blockers"]
    )


def test_review_receipt_must_match_current_head() -> None:
    pr_watch = _load_pr_watch()
    view = _green_view(reviewDecision="")

    missing = pr_watch.build_report(view, [], set())
    stale = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "older", "source": "fallback:codex"},
    )
    current = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
    )

    assert missing["done"] is False
    assert stale["done"] is False
    assert current["done"] is True
    assert current["review_evidence"] == {
        "valid": True,
        "source": "fallback:codex",
        "head": "abc123",
    }


def test_record_review_refuses_push_between_review_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda _args: {"number": 7, "headRefOid": "new-unreviewed-head"},
    )

    with pytest.raises(ValueError, match="head changed during review"):
        pr_watch.record_review(7, "fallback:codex", "reviewed-head")

    assert not (tmp_path / "7.json").exists()


def test_record_review_persists_only_expected_current_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda _args: {"number": 7, "headRefOid": "reviewed-head"},
    )

    report = pr_watch.record_review(7, "fallback:codex", "reviewed-head")

    assert report["review_receipt"]["head"] == "reviewed-head"
    assert pr_watch.load_state(7)["review_receipt"]["source"] == "fallback:codex"


def test_normal_coderabbit_walkthrough_remains_noise() -> None:
    pr_watch = _load_pr_watch()
    body = """<!-- This is an auto-generated comment: summarize by coderabbit.ai -->
<!-- walkthrough_start -->
Summary only.
"""
    view = _green_view(
        comments=[
            {"id": "summary-1", "author": {"login": "coderabbitai"}, "body": body}
        ]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "coderabbit"},
    )

    assert report["new_comments"] == []
    assert report["done"] is True
