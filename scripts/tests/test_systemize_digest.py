"""Severity, addressed state, citation, ranking, cap and derived digest fields."""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import replace
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


@pytest.mark.parametrize("field", [
    "id", "source", "path", "line", "source_severity", "severity", "severity_mapped",
    "addressed", "stance", "reviewed_head", "guideline_citation", "url",
])
def test_verify_rejects_altered_or_missing_finding_evidence(settings, field) -> None:
    expected = normalize.build(_raw([_pr(1, ("🔴 Critical", False))], settings), settings, [])
    for remove in (False, True):
        candidate = deepcopy(expected)
        finding = candidate["prs"][0]["findings"][0]
        if remove:
            del finding[field]
        else:
            finding[field] = "altered"
        with pytest.raises(SystemizeError, match="finding evidence"):
            normalize.verify(candidate, expected, "candidate")


@pytest.mark.parametrize("mutation", ["delete", "add", "count", "unaddressed", "max", "refs", "extra"])
def test_verify_rejects_changed_population_and_pr_evidence(settings, mutation) -> None:
    expected = normalize.build(_raw([_pr(1, ("🔴 Critical", False))], settings), settings, [])
    candidate = deepcopy(expected)
    pr = candidate["prs"][0]
    if mutation == "delete":
        pr["findings"] = []
    elif mutation == "add":
        pr["findings"].append(deepcopy(pr["findings"][0]))
    else:
        key = {"count": "finding_count", "unaddressed": "unaddressed_count", "max": "max_severity",
               "refs": "tracker_refs", "extra": "invented"}[mutation]
        pr[key] = "altered"
    with pytest.raises(SystemizeError, match="finding evidence"):
        normalize.verify(candidate, expected, "candidate")


def test_verify_allows_only_typed_text_cleaning_latitude(settings) -> None:
    expected = normalize.build(_raw([_pr(1, ("x", False))], settings), settings, [])
    candidate = deepcopy(expected)
    finding = candidate["prs"][0]["findings"][0]
    finding.update(text="Agent cleaned text", text_truncated=True)
    normalize.verify(candidate, expected, "candidate")
    for field, value in (("text", None), ("text_truncated", "true")):
        broken = deepcopy(candidate)
        broken["prs"][0]["findings"][0][field] = value
        with pytest.raises(SystemizeError, match="finding evidence"):
            normalize.verify(broken, expected, "candidate")


def test_verify_rejects_boolean_counts_and_line_numbers(settings) -> None:
    expected = normalize.build(_raw([_pr(1, ("x", False))], settings), settings, [])
    for field in ("finding_count", "unaddressed_count", "number"):
        candidate = deepcopy(expected)
        candidate["prs"][0][field] = True
        with pytest.raises(SystemizeError):
            normalize.verify(candidate, expected, "candidate")
    candidate = deepcopy(expected)
    candidate["findings_pr_count"] = True
    with pytest.raises(SystemizeError):
        normalize.verify(candidate, expected, "candidate")


# --- fallback-panel dispositions (#772) and the reviewer tally (#1157) -----------

SHA = "b" * 40
LATER = "c" * 40


def _disposition(head: str, prose: str, *, lenses: str = "adversarial, correctness",
                 source: str = "fallback:panel") -> str:
    """The comment `pr_watch.py --record-review --disposition` posts."""
    return (f"<!-- pr-watch:disposition head={head} -->\n## Review disposition — {head[:7]}\n\n"
            f"- reviewed head: `{head}`\n- review source: `{source}`\n- lenses: {lenses}\n\n"
            f"{prose.strip()}\n")


def _operator_settings(tmp_path: Path, **keys):
    def edit(text: str) -> str:
        text = text.replace("operator_logins: []", "operator_logins: [Operator]")
        for key, value in keys.items():
            text = text.replace("  pr_draft: false\n", f"  pr_draft: false\n  {key}: {value}\n")
        return text
    return load_settings(make_repo(tmp_path, config_edit=edit))


def _panel_pr(number: int, *comments: tuple[int, str, str]) -> dict:
    return {"number": number, "review_threads": [], "reviews": [], "issue_comments": [
        {"id": cid, "author": author, "body": body, "url": f"https://x/c/{cid}"}
        for cid, author, body in comments]}


def test_the_parsed_header_is_the_one_pr_watch_writes() -> None:
    """The header grammar is pinned to the engine that writes it, not restated."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("pr_watch_for_systemize", engine_dir(Path(__file__)) / "pr_watch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    body = module.disposition_body(
        {"head": SHA, "source": "fallback:panel", "lenses": ["adversarial", "correctness"]},
        "adversarial F1 HIGH: accept — fixed in 1234567")
    header = normalize.disposition_header(body)
    assert header is not None
    assert (header["head"], header["review_source"], header["lenses"]) == (
        SHA, "fallback:panel", ["adversarial", "correctness"])


def test_panel_dispositions_are_findings_with_lens_severity_stance_and_addressed_state(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    prose = """Round 1.

- adversarial F1 HIGH: accept — fixed in 1234567
- `correctness F1 LOW: dispute-evidence — scripts/x.py:12 already guards it`
- correctness F2 high: dispute-concern — we think it is fine
- adversarial F2 MEDIUM: dispute-concern — intentional
"""
    pr = _panel_pr(1, (10, "operator", _disposition(SHA, prose)))
    found = {f["id"]: f for f in normalize.pr_findings(pr, settings, [])}
    assert set(found) == {f"disposition:10:{k}" for k in (
        "adversarial:F1", "correctness:F1", "correctness:F2", "adversarial:F2")}
    first = found["disposition:10:adversarial:F1"]
    assert first["source"] == {"kind": "operator", "login": "operator", "lens": "adversarial",
                               "review_source": "fallback:panel"}
    assert (first["source_severity"], first["severity"], first["stance"], first["addressed"],
            first["reviewed_head"]) == ("HIGH", "high", "accept", "addressed", SHA)
    assert found["disposition:10:correctness:F1"]["addressed"] == "addressed"
    # A HIGH is never closed by dispute-concern; a MEDIUM is.
    assert found["disposition:10:correctness:F2"]["addressed"] == "unaddressed"
    assert found["disposition:10:adversarial:F2"]["addressed"] == "addressed"


@pytest.mark.parametrize("line, label, severity, addressed", [
    # Concern closes only a finding known to be below HIGH and not a regression.
    ("adversarial F1 MEDIUM regression: dispute-concern — x", "MEDIUM", "normal", "unaddressed"),
    ("adversarial F1 regression: dispute-concern — x", None, "normal", "unaddressed"),
    ("adversarial F1: dispute-concern — x", None, "normal", "unaddressed"),
    ("adversarial F1 HGH: dispute-concern — x", "HGH", "normal", "unaddressed"),
    ("adversarial F1 P1: dispute-concern — x", "P1", "normal", "unaddressed"),
    ("adversarial F1 MEDIUM: dispute-concern — x", "MEDIUM", "normal", "addressed"),
    # The other stances close it whatever the label.
    ("adversarial F1 HGH regression: dispute-evidence — a.py:1", "HGH", "normal", "addressed"),
    ("adversarial F1: accept — fixed", None, "normal", "addressed"),
])
def test_concern_closes_only_a_finding_known_to_be_closable(tmp_path, line, label, severity, addressed) -> None:
    settings = _operator_settings(tmp_path)
    [found] = normalize.pr_findings(_panel_pr(1, (10, "operator", _disposition(SHA, line))), settings, [])
    assert (found["source_severity"], found["severity"], found["addressed"]) == (label, severity, addressed)


@pytest.mark.parametrize("author, body", [
    # An untrusted author, however exact the comment.
    ("someone", _disposition(SHA, "adversarial F1 HIGH: accept — x")),
    # A trusted author's prose without the engine's header.
    ("operator", "adversarial F1 HIGH: accept — x"),
    # The marker alone, without the fixed header lines under it.
    ("operator", f"<!-- pr-watch:disposition head={SHA} -->\nadversarial F1 HIGH: accept — x"),
    # The header's two heads disagree.
    ("operator", _disposition(SHA, "adversarial F1 HIGH: accept — x").replace(
        f"reviewed head: `{SHA}`", f"reviewed head: `{LATER}`")),
    # A quoted line is a quotation, not this round's disposition.
    ("operator", _disposition(SHA, "> adversarial F1 HIGH: accept — x")),
    # So is a line inside a fenced block, either fence.
    ("operator", _disposition(SHA, "```text\nadversarial F1 HIGH: accept — x\n```")),
    ("operator", _disposition(SHA, "~~~\nadversarial F1 HIGH: accept — x\n~~~")),
    # An unclosed fence runs to the end of the comment.
    ("operator", _disposition(SHA, "```\nadversarial F1 HIGH: accept — x")),
    # A line with text after the fence characters does not close it.
    ("operator", _disposition(SHA, "```\n``` text\nadversarial F1 HIGH: accept — x\n```")),
    # A shorter run does not close a longer fence.
    ("operator", _disposition(SHA, "````\n```\nadversarial F1 HIGH: accept — x\n````")),
    # A fence opened behind a list marker.
    ("operator", _disposition(SHA, "- ```\n  adversarial F1 HIGH: accept — x\n  ```")),
    # An HTML comment is not rendered, so it is not a disposition either.
    ("operator", _disposition(SHA, "<!--\nadversarial F1 HIGH: accept — x\n-->")),
    # A lens the header does not list.
    ("operator", _disposition(SHA, "security F1 HIGH: accept — x")),
    # Not a typed stance.
    ("operator", _disposition(SHA, "adversarial F1 HIGH: fixed — x")),
])
def test_no_comment_is_panel_evidence_by_its_prose_alone(tmp_path, author, body) -> None:
    settings = _operator_settings(tmp_path)
    assert normalize.pr_findings(_panel_pr(1, (10, author, body)), settings, []) == []


def test_an_empty_operator_list_trusts_no_disposition(settings) -> None:
    pr = _panel_pr(1, (10, "operator", _disposition(SHA, "adversarial F1 HIGH: accept — x")))
    assert normalize.pr_findings(pr, settings, []) == []


def test_a_later_comment_at_the_same_head_corrects_an_earlier_one(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    pr = _panel_pr(
        1,
        (10, "operator", _disposition(SHA, "adversarial F1 HIGH: dispute-concern — no\nadversarial F2 LOW: accept — ok")),
        (11, "operator", _disposition(SHA, "adversarial F1 HIGH: accept — fixed after all")),
        (12, "operator", _disposition(LATER, "adversarial F1 LOW: accept — round two")),
    )
    found = {f["id"]: f["stance"] for f in normalize.pr_findings(pr, settings, [])}
    assert found == {"disposition:10:adversarial:F2": "accept",
                     "disposition:11:adversarial:F1": "accept",
                     "disposition:12:adversarial:F1": "accept"}
    assert normalize.panel_findings(pr, settings, [])[0] == [SHA, LATER]


def test_a_line_after_a_closed_fence_is_read(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    body = _disposition(SHA, "```\nexample F1 HIGH: accept — x\n```\nadversarial F1 HIGH: accept — fixed")
    findings = normalize.pr_findings(_panel_pr(1, (10, "operator", body)), settings, [])
    assert [f["id"] for f in findings] == ["disposition:10:adversarial:F1"]


def test_the_marker_and_stance_are_read_in_any_case(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    body = _disposition(SHA, "adversarial F1 MEDIUM Regression: Dispute-Concern — x")
    [found] = normalize.pr_findings(_panel_pr(1, (10, "operator", body)), settings, [])
    assert (found["stance"], found["addressed"]) == ("dispute-concern", "unaddressed")


def test_round_tags_keep_each_round_and_count_it(tmp_path) -> None:
    """One comment at the final head carries every round, and a lens restarts at F1."""
    settings = _operator_settings(tmp_path)
    prose = ("adversarial R1 F1 HIGH: accept — fixed in 1234567\n"
             "adversarial R2 F1 LOW: dispute-evidence — a.py:3\n"
             "adversarial R3 F1 LOW: accept — fixed")
    pr = _panel_pr(1, (10, "operator", _disposition(SHA, prose)))
    found = {f["id"]: f["review_round"] for f in normalize.pr_findings(pr, settings, [])}
    assert found == {"disposition:10:adversarial:R1:F1": 1, "disposition:10:adversarial:R2:F1": 2,
                     "disposition:10:adversarial:R3:F1": 3}
    digest = normalize.build(_raw([pr], settings), settings, [])
    assert digest["reviewer_tally"]["rounds"] == [{"pr": 1, "rounds": 3}]


def test_a_repeated_line_in_one_comment_counts_once(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    body = _disposition(SHA, "adversarial F1 HIGH: accept — fixed\nadversarial F1 LOW: dispute-concern — dup")
    findings = normalize.pr_findings(_panel_pr(1, (10, "operator", body)), settings, [])
    assert [(f["source_severity"], f["stance"]) for f in findings] == [("HIGH", "accept")]


def test_a_panel_only_pr_reaches_the_digest(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    digest = normalize.build(_raw([
        _panel_pr(1, (10, "operator", _disposition(SHA, "adversarial F1 HIGH: accept — fixed"))),
        _panel_pr(2, (20, "operator", _disposition(SHA, "No findings."))),
    ], settings), settings, [])
    assert [p["number"] for p in digest["prs"]] == [1]
    assert digest["prs"][0]["max_severity"] == "high"
    # A clean round still counts as a round.
    assert digest["reviewer_tally"]["rounds"] == [{"pr": 1, "rounds": 1}, {"pr": 2, "rounds": 1}]


def test_the_tally_counts_each_source_over_the_uncapped_window(tmp_path) -> None:
    settings = _operator_settings(tmp_path, refuted_flag_min_findings=2, refuted_flag_percent=50)
    noisy = "adversarial F1 LOW: dispute-evidence — a:1\nadversarial F2 LOW: dispute-evidence — a:2\n" \
            "correctness F1 HIGH: accept — fixed\ncorrectness F2 LOW: dispute-evidence — c:3"
    prs = [
        _panel_pr(1, (10, "operator", _disposition(SHA, noisy)),
                  (11, "operator", _disposition(LATER, "adversarial F1 LOW: accept — fixed"))),
        _pr(2, ("**High Severity**", True), ("_🟡 Minor_", False)),
    ]
    # One PR survives the cap; the tally still counts both.
    digest = normalize.build(_raw(prs, settings), replace(settings, max_findings_prs_per_run=1), [])
    assert len(digest["prs"]) == 1 and digest["input_cap"]["omitted_prs"]
    tally = digest["reviewer_tally"]
    by_source = {s["source"]: s for s in tally["sources"]}
    assert list(by_source) == ["configured-reviewer:coderabbitai", "lens:adversarial", "lens:correctness"]
    adversarial = by_source["lens:adversarial"]
    assert adversarial["findings"] == 3
    assert adversarial["by_stance"] == {"accept": 1, "dispute-evidence": 2, "dispute-concern": 0}
    assert adversarial["refuted"] == 2 and adversarial["refuted_flag"] is True
    correctness = by_source["lens:correctness"]
    assert correctness["refuted"] == 1 and correctness["refuted_flag"] is True  # 1 of 2 is 50%
    bot = by_source["configured-reviewer:coderabbitai"]
    assert bot["by_stance"] is None and bot["refuted"] is None and bot["refuted_flag"] is False
    assert bot["by_addressed"] == {"addressed": 1, "outdated": 0, "unaddressed": 1, "unevidenced": 0}
    assert tally["rounds"] == [{"pr": 1, "rounds": 2}]
    assert (tally["refuted_flag_min_findings"], tally["refuted_flag_percent"]) == (2, 50)


def test_the_flag_needs_its_percent(tmp_path) -> None:
    settings = _operator_settings(tmp_path, refuted_flag_min_findings=2, refuted_flag_percent=50)
    prose = "\n".join(f"adversarial F{n} LOW: {stance} — a:{n}" for n, stance in
                      enumerate(["dispute-evidence", "accept", "accept"], start=1))
    tally = normalize.build(_raw([_panel_pr(1, (10, "operator", _disposition(SHA, prose)))], settings),
                            settings, [])["reviewer_tally"]
    assert tally["sources"][0]["refuted"] == 1 and tally["sources"][0]["refuted_flag"] is False


def test_the_flag_needs_its_minimum_sample(tmp_path) -> None:
    settings = _operator_settings(tmp_path)  # the defaults: 5 findings, 50 percent
    prose = "adversarial F1 LOW: dispute-evidence — a:1"
    tally = normalize.build(_raw([_panel_pr(1, (10, "operator", _disposition(SHA, prose)))], settings),
                            settings, [])["reviewer_tally"]
    assert tally["sources"][0]["refuted"] == 1 and tally["sources"][0]["refuted_flag"] is False
    assert (tally["refuted_flag_min_findings"], tally["refuted_flag_percent"]) == (5, 50)


@pytest.mark.parametrize("key, value", [
    ("refuted_flag_percent", 101), ("refuted_flag_percent", 0), ("refuted_flag_min_findings", 0),
    ("refuted_flag_min_findings", "true"),
])
def test_the_flag_settings_are_validated(tmp_path, key, value) -> None:
    with pytest.raises(SystemizeError, match=key):
        _operator_settings(tmp_path, **{key: value})


def test_verify_recomputes_panel_findings_and_the_tally(tmp_path) -> None:
    settings = _operator_settings(tmp_path)
    expected = normalize.build(_raw([
        _panel_pr(1, (10, "operator", _disposition(SHA, "adversarial F1 HIGH: accept — fixed")))],
        settings), settings, [])
    normalize.verify(deepcopy(expected), expected, "same")
    dropped = deepcopy(expected)
    dropped["prs"] = []
    with pytest.raises(SystemizeError, match="finding evidence"):
        normalize.verify(dropped, expected, "candidate")
    for field in ("stance", "reviewed_head", "review_round"):
        altered = deepcopy(expected)
        altered["prs"][0]["findings"][0][field] = "altered"
        with pytest.raises(SystemizeError, match="finding evidence"):
            normalize.verify(altered, expected, "candidate")
    tallied = deepcopy(expected)
    tallied["reviewer_tally"]["sources"][0]["refuted"] = 1
    with pytest.raises(SystemizeError, match="reviewer_tally"):
        normalize.verify(tallied, expected, "candidate")
