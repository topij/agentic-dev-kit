"""Severity, addressed state, citation, ranking, cap and derived digest fields."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))
from systemize import identity, normalize  # noqa: E402
from systemize.config import load_settings  # noqa: E402
from systemize.errors import SystemizeError  # noqa: E402
from test_systemize_support import HEAD, make_repo  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path):
    return load_settings(make_repo(tmp_path))


@pytest.mark.parametrize(
    "label, expected",
    [
        ("low", "low"), ("Minor", "low"), (" info ", "low"), ("INFORMATIONAL", "low"),
        ("medium", "normal"), ("moderate", "normal"), ("normal", "normal"), ("Warning", "normal"),
        ("high", "high"), ("Major", "high"),
        ("critical", "critical"), ("BLOCKER", "critical"),
        (None, "normal"),
    ],
)
def test_the_canonical_severity_table(label, expected) -> None:
    assert normalize.normalize_severity(label) == (expected, True)


@pytest.mark.parametrize("label", ["P1", "nitpick", "3", "severe"])
def test_custom_and_numeric_labels_are_normal_and_flagged(label) -> None:
    assert normalize.normalize_severity(label) == ("normal", False)


@pytest.mark.parametrize(
    "body, label",
    [
        ("_⚠️ Potential issue_ | _🟠 Major_\n\ntext", "Major"),
        ("🔴 **Critical**: bad", "Critical"),
        ("**High Severity**\n\nx", "High"),
        ("Severity: low\n", "low"),
        ("> **severity:** Blocker", "Blocker"),
        ("![P1 Badge](https://x/badge)", "P1"),
        ("no label at all, mentions P1 in prose", None),
        # The earliest label in the body wins.
        ("**Low Severity** then 🔴 Critical", "Low"),
    ],
)
def test_only_the_source_label_text_is_extracted(body, label) -> None:
    assert normalize.source_label(body) == label


@pytest.mark.parametrize(
    "thread, state",
    [
        ({"is_resolved": True, "is_outdated": True}, "addressed"),
        ({"is_resolved": True, "is_outdated": False}, "addressed"),
        ({"is_resolved": False, "is_outdated": True}, "outdated"),
        ({"is_resolved": False, "is_outdated": False}, "unaddressed"),
        ({}, "unaddressed"),
    ],
)
def test_addressed_state_is_forge_thread_resolution(thread, state) -> None:
    assert normalize.thread_addressed(thread) == state


def test_reply_text_does_not_mark_a_thread_addressed(settings) -> None:
    pr = {"number": 1, "review_threads": [{
        "is_resolved": False, "is_outdated": False, "path": "a.py", "line": 1,
        "comments": [{"id": 1, "author": "coderabbitai", "body": "bug"},
                     {"id": 2, "author": "someone", "body": "✅ Fixed in abc1234"}],
    }], "reviews": []}
    [finding] = normalize.pr_findings(pr, settings, [])
    assert finding["addressed"] == "unaddressed"


def test_guideline_citation_records_its_evidence() -> None:
    paths = ["AGENTS.md", "docs/agentic-dev-kit/workflows/wrap-up.md"]
    cited = normalize.guideline_citation("As per coding guidelines in AGENTS.md, …", paths)
    assert cited == {"state": "cited", "evidence": ["AGENTS.md", "as per coding guidelines"]}
    assert normalize.guideline_citation("plain", paths) == {"state": "none", "evidence": []}


def test_clean_text_drops_markup_but_keeps_collapsed_findings() -> None:
    body = "<!-- hidden -->Top\n\n\n\n<details>\n<summary>🧹 Nitpick comments (1)</summary>\n\nreal nit\n</details>"
    text, truncated = normalize.clean_text(body)
    assert text == "Top\n\n🧹 Nitpick comments (1)\n\nreal nit"
    assert not truncated
    long_text, long_truncated = normalize.clean_text("x" * (normalize.TEXT_LIMIT + 5))
    assert len(long_text) == normalize.TEXT_LIMIT and long_truncated


def test_only_trusted_thread_roots_and_review_bodies_are_findings(settings) -> None:
    pr = {"number": 1, "review_threads": [
        {"comments": [{"id": 1, "author": "CodeRabbitAI", "body": "x"}, {"id": 2, "author": "coderabbitai", "body": "reply"}]},
        {"comments": [{"id": 3, "author": "coderabbitai-shim", "body": "lookalike"}]},
        {"comments": []},
    ], "reviews": [
        {"id": 4, "author": "coderabbitai[bot]", "body": "summary"},
        {"id": 5, "author": "coderabbitai", "body": "   "},
    ]}
    assert [f["id"] for f in normalize.pr_findings(pr, settings, [])] == ["thread:1", "review:4"]


def _raw(prs, settings) -> dict:
    run_id = identity.run_identity(forge_repo="o/r", window_days=7, head=HEAD,
                                   fingerprint=settings.fingerprint, mode="test")
    return {**identity.header(identity.RAW_KIND, run_id), "window": {"start": "s", "end": "e"}, "prs": prs}


def _pr(number: int, *findings: tuple[str, bool]) -> dict:
    threads = [{"is_resolved": resolved, "is_outdated": False, "comments": [
        {"id": number * 100 + i, "author": "coderabbitai", "body": label}]}
        for i, (label, resolved) in enumerate(findings)]
    return {"number": number, "review_threads": threads, "reviews": []}


def test_ranking_uses_severity_then_unaddressed_then_total_then_number(settings) -> None:
    prs = [
        _pr(1, ("_🟡 Minor_", False)),
        _pr(2, ("**High Severity**", True)),                                  # high, 0 unaddressed
        _pr(3, ("**High Severity**", False)),                                 # high, 1 unaddressed
        _pr(4, ("**High Severity**", False), ("_🟡 Minor_", True)),            # high, 1 unaddressed, 2 total
        _pr(5, ("**High Severity**", False), ("_🟡 Minor_", True)),            # tie with 4 → number
        _pr(6, ("🔴 Critical", True)),
        {"number": 7, "review_threads": [], "reviews": []},                   # no findings: excluded
    ]
    digest = normalize.build(_raw(prs, settings), settings, [])
    assert [p["number"] for p in digest["prs"]] == [6, 4, 5, 3, 2, 1]


@pytest.mark.parametrize(
    "count, single_pass, batches",
    [(0, True, 0), (1, True, 1), (25, True, 1), (26, True, 2), (60, True, 3), (61, False, 3), (75, False, 3)],
)
def test_derived_fields(settings, count, single_pass, batches) -> None:
    assert normalize.derived(count, settings) == {
        "findings_pr_count": count, "single_pass_recommended": single_pass, "n_batches": batches}


def test_the_cap_keeps_the_top_ranked_and_discloses_the_rest(settings) -> None:
    cap = settings.max_findings_prs_per_run
    prs = [_pr(n, ("🔴 Critical" if n <= 3 else "_🟡 Minor_", False)) for n in range(1, cap + 6)]
    digest = normalize.build(_raw(prs, settings), settings, [])
    assert [p["number"] for p in digest["prs"]][:3] == [1, 2, 3]
    assert digest["findings_pr_count"] == cap
    assert digest["input_cap"] == {
        "applied": True, "uncapped_findings_pr_count": cap + 5, "omitted_prs": list(range(cap + 1, cap + 6))}


def test_zero_merged_prs_is_an_empty_valid_digest(settings) -> None:
    digest = normalize.build(_raw([], settings), settings, [])
    assert digest["prs"] == [] and digest["n_batches"] == 0
    assert digest["input_cap"] == {"applied": False, "uncapped_findings_pr_count": 0, "omitted_prs": []}
    normalize.verify(digest, digest, "same")


def test_verify_rejects_a_foreign_or_altered_header(settings) -> None:
    digest = normalize.build(_raw([_pr(1, ("x", False))], settings), settings, [])
    for mutated in ({**digest, "artifact_kind": "other"}, {**digest, "run_identity_digest": "sha256:" + "0" * 64}):
        with pytest.raises(SystemizeError):
            normalize.verify(mutated, digest, "candidate")
    with pytest.raises(SystemizeError, match="prs\\[\\]"):
        normalize.verify({**digest, "prs": "not a list"}, digest, "candidate")
