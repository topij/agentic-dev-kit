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


# --------------------------------------------------------------------------- #
# review.require_ci — convergence on a repo with no CI
# --------------------------------------------------------------------------- #


def test_zero_check_pr_can_never_be_green_while_require_ci_holds() -> None:
    """The safe default: no real check ran, so nothing may report green — this is
    what stops an autonomous merge on a PR whose CI never started."""
    pr_watch = _load_pr_watch()

    assert pr_watch.summarize_checks([], require_ci=True)["all_green"] is False
    # An informational-only rollup has no *blocking* check either.
    informational_only = pr_watch.summarize_checks(
        [{"context": "CodeRabbit", "state": "PENDING"}], require_ci=True
    )
    assert informational_only["all_green"] is False
    assert informational_only["informational"] == 1


def test_zero_check_pr_is_green_when_require_ci_is_false() -> None:
    """A repo with no CI at all: without this, `blocking_total > 0` makes `done`
    unreachable forever — the watch loop never terminates and merge always refuses."""
    pr_watch = _load_pr_watch()

    assert pr_watch.summarize_checks([], require_ci=False)["all_green"] is True
    assert (
        pr_watch.summarize_checks(
            [{"context": "CodeRabbit", "state": "PENDING"}], require_ci=False
        )["all_green"]
        is True
    )


def test_require_ci_defaults_to_the_configured_value() -> None:
    pr_watch = _load_pr_watch()

    assert pr_watch._REQUIRE_CI is True  # this repo's config
    assert pr_watch.summarize_checks([])["all_green"] is False


@pytest.mark.parametrize("require_ci", [True, False])
def test_real_checks_are_classified_identically_under_both_settings(
    require_ci: bool,
) -> None:
    """`require_ci` may ONLY change the zero-blocking-check verdict. With real
    checks present, every tally and verdict is byte-identical to today."""
    pr_watch = _load_pr_watch()
    green = [{"name": "tests", "conclusion": "SUCCESS"}]
    pending = [{"name": "tests", "conclusion": None, "status": "IN_PROGRESS"}]
    failing = [{"name": "tests", "conclusion": "FAILURE"}]
    mixed = [
        {"name": "tests", "conclusion": "SUCCESS"},
        {"name": "lint", "conclusion": "ERROR"},
        {"context": "CodeRabbit", "state": "PENDING"},
    ]

    assert pr_watch.summarize_checks(green, require_ci=require_ci) == {
        "total": 1,
        "success": 1,
        "pending": 0,
        "informational": 0,
        "informational_non_green": 0,
        "failing": [],
        "all_green": True,
    }
    assert pr_watch.summarize_checks(pending, require_ci=require_ci)["all_green"] is False
    assert pr_watch.summarize_checks(failing, require_ci=require_ci)["all_green"] is False
    mixed_summary = pr_watch.summarize_checks(mixed, require_ci=require_ci)
    assert mixed_summary["all_green"] is False
    assert mixed_summary["failing"] == [{"name": "lint", "status": "ERROR"}]
    assert mixed_summary["informational"] == 1
    assert mixed_summary["informational_non_green"] == 1


def test_zero_check_pr_still_needs_current_head_review_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`require_ci: false` is not a merge waiver — the receipt becomes THE gate."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REQUIRE_CI", False)
    view = _green_view(statusCheckRollup=[])

    without_receipt = pr_watch.build_report(view, [], set())
    stale_receipt = pr_watch.build_report(
        view, [], set(), review_receipt={"head": "older", "source": "fallback:codex"}
    )
    with_receipt = pr_watch.build_report(
        view, [], set(), review_receipt={"head": "abc123", "source": "fallback:codex"}
    )

    assert without_receipt["checks"]["all_green"] is True
    assert without_receipt["done"] is False
    assert (
        "independent review evidence is missing for current head"
        in without_receipt["merge_blockers"]
    )
    assert stale_receipt["done"] is False
    assert with_receipt["done"] is True


def test_zero_check_pr_never_settles_done_while_require_ci_holds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REQUIRE_CI", True)

    report = pr_watch.build_report(
        _green_view(statusCheckRollup=[]),
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
    )

    assert report["checks"]["all_green"] is False
    assert report["done"] is False


# --------------------------------------------------------------------------- #
# review-bot knowledge comes from config, not from engine literals
# --------------------------------------------------------------------------- #


ADOPTER_CONFIG = """review:
  noise_markers:
    - "<!-- Generated by OtherBot -->"
    - "NOTHING TO REPORT"
  unavailable_markers:
    - "OtherBot Is Out Of Credits"
  informational_checks: [OtherBot, " Advisory "]
  require_ci: false
"""


def _write_config(tmp_path: Path, body: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "dev-model.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_review_knowledge_is_read_from_config_not_engine_literals(
    tmp_path: Path,
) -> None:
    pr_watch = _load_pr_watch()

    noise, unavailable, informational, require_ci = pr_watch._load_review_config(
        _write_config(tmp_path, ADOPTER_CONFIG)
    )

    # Lower-cased/stripped at load so every call site can keep matching
    # case-insensitively against a folded body / check name.
    assert noise == ("<!-- generated by otherbot -->", "nothing to report")
    assert unavailable == ("otherbot is out of credits",)
    assert informational == frozenset({"otherbot", "advisory"})
    assert require_ci is False
    # None of the kit's own default markers leak in — config replaces, not extends.
    assert "<!-- walkthrough_start -->" not in noise


def test_missing_config_falls_back_to_defaults_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A standalone engine run (no config at all) must behave exactly as before."""
    pr_watch = _load_pr_watch()

    resolved = pr_watch._load_review_config(tmp_path / "absent.yaml")

    assert resolved == (
        pr_watch._DEFAULT_NOISE_MARKERS,
        pr_watch._DEFAULT_REVIEW_UNAVAILABLE_MARKERS,
        frozenset(pr_watch._DEFAULT_INFORMATIONAL_CHECK_NAMES),
        True,
    )
    assert capsys.readouterr().err == ""


def test_unreadable_config_warns_and_falls_back_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A config that exists but can't be read must never wedge the watch loop —
    fall back to defaults, but say so, so an ignored config stays visible."""
    pr_watch = _load_pr_watch()
    path = _write_config(tmp_path, ADOPTER_CONFIG)
    path.chmod(0o000)
    if path.is_file():
        try:
            path.read_text(encoding="utf-8")
        except OSError:
            pass
        else:  # pragma: no cover - only when tests run as root
            pytest.skip("cannot make a file unreadable (running as root?)")

    resolved = pr_watch._load_review_config(path)

    assert resolved[3] is True  # NOT the config's require_ci: false
    assert resolved[0] == pr_watch._DEFAULT_NOISE_MARKERS
    assert "could not read review config" in capsys.readouterr().err


def test_explicit_empty_noise_list_is_honored_but_absent_key_is_not(
    tmp_path: Path,
) -> None:
    """`noise_markers: []` means "filter nothing" (an adopter with no bots);
    an absent key means "use the kit's defaults". The two must not collapse."""
    pr_watch = _load_pr_watch()

    empty = pr_watch._load_review_config(
        _write_config(tmp_path / "a", "review:\n  noise_markers: []\n")
    )
    absent = pr_watch._load_review_config(
        _write_config(tmp_path / "b", "review:\n  bots: [coderabbit]\n")
    )

    assert empty[0] == ()
    assert absent[0] == pr_watch._DEFAULT_NOISE_MARKERS


def test_non_boolean_require_ci_keeps_the_safe_default(tmp_path: Path) -> None:
    """Only a real boolean flips the CI requirement — a stray `yes` must not
    silently let a zero-check PR read as green."""
    pr_watch = _load_pr_watch()

    for value in ("yes", "0", '"false"'):
        _, _, _, require_ci = pr_watch._load_review_config(
            _write_config(tmp_path, f"review:\n  require_ci: {value}\n")
        )
        assert require_ci is True, value


def test_configured_unavailable_marker_still_beats_configured_noise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The "a down reviewer is never auto-noise" invariant is a property of the
    engine, not of which list a marker happens to sit on in config."""
    pr_watch = _load_pr_watch()
    noise, unavailable, _, _ = pr_watch._load_review_config(
        _write_config(
            tmp_path,
            'review:\n  noise_markers: ["OtherBot Is Out Of Credits"]\n'
            '  unavailable_markers: ["OtherBot Is Out Of Credits"]\n',
        )
    )
    monkeypatch.setattr(pr_watch, "_NOISE_MARKERS", noise)
    monkeypatch.setattr(pr_watch, "_REVIEW_UNAVAILABLE_MARKERS", unavailable)

    body = "OtherBot is out of credits for this repo."

    assert pr_watch.review_unavailable_reason(body) == "otherbot is out of credits"
    assert pr_watch.is_noise(body) is False


def test_shipped_config_preserves_the_engine_defaults_behavior() -> None:
    """This repo's own config/dev-model.yaml must classify exactly as the
    literals it replaced — the behavior-preservation argument for BUG 3."""
    pr_watch = _load_pr_watch()

    walkthrough = (
        "<!-- This is an auto-generated comment: summarize by coderabbit.ai -->\n"
        "<!-- walkthrough_start -->\nSummary only.\n"
    )
    assert pr_watch.is_noise(walkthrough) is True
    assert pr_watch.is_noise("Actionable comments posted: 0") is True
    # Unavailability notices: surfaced, never noise (either list, either case).
    for body in (
        "Bugbot needs on-demand usage enabled",
        "Review skipped",
        "Review limit reached",
        "No review credits",
    ):
        assert pr_watch.review_unavailable_reason(body) is not None, body
        assert pr_watch.is_noise(body) is False, body
    assert pr_watch._INFORMATIONAL_CHECK_NAMES == frozenset({"coderabbit"})
    assert pr_watch._REQUIRE_CI is True


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
