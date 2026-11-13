"""`lib/merge_predicate.py`: the one read of a `pr_watch.py --json` report that
decides whether a pull request may merge, or is held for the operator.

Three callers go through it: `dev_session.sh merge`, `reconcile_sessions.sh`'s
`_held_check` and `triage.model.terminal_pr_watch_receipt`. The reads are pinned
here once. That each caller really delegates, and spells no field check of its
own, is pinned where the caller is run: by swapping this module for a stub in
`test_portability.py` and `test_reconcile_sessions.py`, and by replacing
`readiness` in `test_finalize_triage.py`.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
MODULE = ENGINE_DIR / "lib" / "merge_predicate.py"
sys.path.insert(0, str(ENGINE_DIR / "lib"))

import merge_predicate  # noqa: E402

HEAD = "a" * 40
URL = "https://example.test/acme/widgets/pull/8"
STANDARD = {
    "class": "standard",
    "matched_paths": [],
    "changes_config": False,
    "unclassified": None,
}
CONTROL_CHARACTERS = [chr(code) for code in [*range(0x20), 0x7F]]


def ready_report(**changes: object) -> dict:
    report = {
        "pr": 8,
        "url": URL,
        "base": "trunk",
        "head": HEAD,
        "mergeable": True,
        "converged": True,
        "done": True,
        "merge_blockers": [],
        "truncated_reads": [],
        "review_evidence": {"valid": True},
        "review_class": dict(STANDARD),
    }
    report.update(changes)
    return report


def without(key: str) -> dict:
    report = ready_report()
    del report[key]
    return report


def test_the_module_imports_only_the_standard_library() -> None:
    """Engines run it with a bare `python3` from hooks and scheduled jobs, so an
    import of anything else is a merge gate that fails on those hosts. Read from
    the syntax tree, so a name in a comment or a string cannot satisfy or trip
    it."""
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "a relative import reaches outside the module"
            imported.add((node.module or "").split(".")[0])
    assert imported <= set(sys.stdlib_module_names), imported


# --------------------------------------------------------------------------- #
# readiness
# --------------------------------------------------------------------------- #


def test_a_complete_report_for_this_pull_request_is_ready() -> None:
    assert merge_predicate.readiness(ready_report(), pr="8", base="trunk", head=HEAD) == (
        "ready",
        "",
    )
    assert merge_predicate.readiness(ready_report(), url=URL, head=HEAD) == ("ready", "")


@pytest.mark.parametrize(
    "report",
    [
        ready_report(mergeable=False),
        ready_report(mergeable=1),
        ready_report(mergeable="true"),
        without("mergeable"),
        ready_report(converged=False),
        without("converged"),
        ready_report(done=False),
        without("done"),
        ready_report(merge_blockers=["pending review"]),
        ready_report(truncated_reads=["comments"]),
        ready_report(truncated_reads=None),
        without("truncated_reads"),
        ready_report(review_evidence={"valid": False}),
        ready_report(review_evidence={"valid": 1}),
        ready_report(review_evidence={}),
        ready_report(review_evidence=True),
        without("review_evidence"),
    ],
)
def test_every_verdict_field_is_required_and_fails_closed(report: dict) -> None:
    """Each of these was required by at least one of the three earlier copies.
    A value that is merely truthy is not `True`, and an absent key is not a
    yes."""
    verdict = merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD)
    assert verdict == ("not-mergeable", "")


@pytest.mark.parametrize(
    "report",
    [
        None,
        [],
        "ready",
        without("merge_blockers"),
        ready_report(merge_blockers=None),
        ready_report(merge_blockers="none"),
    ],
)
def test_a_report_that_cannot_be_read_is_malformed(report: object) -> None:
    assert merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD) == (
        "malformed",
        "",
    )


@pytest.mark.parametrize(
    ("changes", "verdict"),
    [
        ({"pr": 9}, ("wrong-pr", "9")),
        ({"pr": None}, ("wrong-pr", "")),
        ({"pr": True}, ("wrong-pr", "True")),
        ({"base": "other"}, ("wrong-base", "other")),
        ({"base": None}, ("wrong-base", "")),
        ({"head": ""}, ("no-head", "")),
        ({"head": None}, ("no-head", "")),
        ({"head": 7}, ("no-head", "")),
        ({"head": "b" * 40}, ("head-changed", "b" * 40)),
    ],
)
def test_the_report_must_name_exactly_this_pull_request(
    changes: dict, verdict: tuple[str, str]
) -> None:
    report = ready_report(**changes)
    assert merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD) == verdict


def test_the_url_is_checked_when_it_is_the_identity_given() -> None:
    report = ready_report(url="https://example.test/acme/widgets/pull/9")
    assert merge_predicate.readiness(report, url=URL, head=HEAD)[0] == "wrong-url"
    assert merge_predicate.readiness(without("url"), url=URL, head=HEAD)[0] == "wrong-url"


@pytest.mark.parametrize(
    "identity",
    [
        {"head": HEAD},
        {"head": HEAD, "pr": ""},
        {"head": HEAD, "pr": 8},
        {"head": HEAD, "url": ""},
        {"head": HEAD, "pr": "8", "base": ""},
        {"head": "", "pr": "8"},
        {"head": None, "pr": "8"},
    ],
)
def test_an_identity_the_caller_lost_never_matches(identity: dict) -> None:
    """A caller holding no pull request identity, or an empty one, must not be
    answered `ready` by a report that is equally empty there."""
    report = ready_report(pr="", url="", base="", head="")
    assert merge_predicate.readiness(report, **identity)[0] != "ready"
    assert merge_predicate.readiness(ready_report(), **identity)[0] != "ready"
    assert merge_predicate.readiness(ready_report(head=None), **identity)[0] != "ready"


@pytest.mark.parametrize("char", CONTROL_CHARACTERS)
def test_a_control_character_never_fuses_into_a_matching_identity(char: str) -> None:
    """The earlier wrapper scrubbed and then compared in the shell, where a
    deleted tab or NUL fused `tr<TAB>unk` into the recorded `trunk` (#537).
    Identity is now compared here on the raw value, and the reported value is
    scrubbed to a space only for printing."""
    report = ready_report(base=f"tr{char}unk")
    assert merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD) == (
        "wrong-base",
        "tr unk",
    )
    report = ready_report(pr=f"8{char}")
    assert merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD) == (
        "wrong-pr",
        "8 ",
    )
    report = ready_report(head=f"{HEAD}{char}")
    assert merge_predicate.readiness(report, pr="8", base="trunk", head=HEAD)[0] == (
        "head-changed"
    )


def test_scrub_leaves_printable_text_alone() -> None:
    assert merge_predicate.scrub("tr-unk é") == "tr-unk é"


# --------------------------------------------------------------------------- #
# review class
# --------------------------------------------------------------------------- #


def test_only_a_consistent_standard_class_reads_as_standard() -> None:
    assert merge_predicate.review_class(ready_report()) == ("standard", "")


@pytest.mark.parametrize(
    ("review_class", "why"),
    [
        (None, "the pr-watch report has no review_class"),
        ("standard", "the pr-watch report has no review_class"),
        (["standard"], "the pr-watch report has no review_class"),
        # #1371: a partial class is not a class. `rc.get("unclassified") is not
        # None` read this as classified, and then as standard.
        (
            {"class": "standard"},
            "the pr-watch report has no review_class that names "
            "matched_paths, changes_config, unclassified",
        ),
        (
            {"class": "standard", "matched_paths": [], "changes_config": False},
            "the pr-watch report has no review_class that names unclassified",
        ),
        (
            {"matched_paths": [], "changes_config": False, "unclassified": None},
            "the pr-watch report has no review_class that names class",
        ),
    ],
)
def test_an_absent_or_partial_review_class_is_missing(review_class: object, why: str) -> None:
    report = ready_report(review_class=review_class)
    if review_class is None:
        del report["review_class"]
    assert merge_predicate.review_class(report) == ("missing", why)


@pytest.mark.parametrize("reason", ["the base is unknown", "", 0, False, []])
def test_any_unclassified_value_but_none_is_unclassified(reason: object) -> None:
    report = ready_report(review_class={**STANDARD, "unclassified": reason})
    assert merge_predicate.review_class(report) == ("unclassified", str(reason))


@pytest.mark.parametrize(
    ("changes", "why"),
    [
        ({"class": "safety-critical"}, "class safety-critical"),
        ({"class": "Standard"}, "class Standard"),
        ({"class": None}, "class None"),
        (
            {"matched_paths": ["scripts/dev_session.sh"]},
            "class standard; matched: scripts/dev_session.sh",
        ),
        # #1371: `changes_config` is a config change for any value but `False`.
        # The earlier read counted only a literal `True`.
        ({"changes_config": True}, "class standard; matched: " + merge_predicate.CONFIG_CHANGE),
        ({"changes_config": 1}, "class standard; matched: " + merge_predicate.CONFIG_CHANGE),
        ({"changes_config": "true"}, "class standard; matched: " + merge_predicate.CONFIG_CHANGE),
        ({"changes_config": None}, "class standard; matched: " + merge_predicate.CONFIG_CHANGE),
        ({"changes_config": 0}, "class standard; matched: " + merge_predicate.CONFIG_CHANGE),
        # #1371: a `matched_paths` that is not a list. A truthy one was already
        # refused, by a branch no test reached; a falsy one read as no paths.
        ({"matched_paths": "scripts/pr_watch.py"}, "class standard; matched: scripts/pr_watch.py"),
        ({"matched_paths": ""}, "class standard; matched: "),
        ({"matched_paths": None}, "class standard; matched: None"),
        ({"matched_paths": 0}, "class standard; matched: 0"),
        ({"matched_paths": {}}, "class standard; matched: {}"),
    ],
)
def test_everything_else_is_not_standard(changes: dict, why: str) -> None:
    report = ready_report(review_class={**STANDARD, **changes})
    assert merge_predicate.review_class(report) == ("not-standard", why)


@pytest.mark.parametrize("char", CONTROL_CHARACTERS)
def test_the_printed_reason_is_scrubbed_of_every_control_character(char: str) -> None:
    """The reason is report text that reaches a refusal message and a
    tab-splitting shell `read`. A deleted character would be as wrong as a kept
    one, so each becomes exactly one space."""
    for changes, expected in (
        ({"unclassified": f"a{char}b"}, ("unclassified", "a b")),
        ({"class": f"a{char}b"}, ("not-standard", "class a b")),
        ({"matched_paths": [f"a{char}b"]}, ("not-standard", "class standard; matched: a b")),
    ):
        report = ready_report(review_class={**STANDARD, **changes})
        assert merge_predicate.review_class(report) == expected


# --------------------------------------------------------------------------- #
# the two decisions
# --------------------------------------------------------------------------- #


def test_the_merge_gate_needs_readiness_and_a_standard_class() -> None:
    gate = merge_predicate.merge_gate
    assert gate(ready_report(), pr="8", base="trunk", head=HEAD) == ("ready", "")
    assert gate(ready_report(done=False), pr="8", base="trunk", head=HEAD) == (
        "not-mergeable",
        "",
    )
    safety = ready_report(review_class={**STANDARD, "class": "safety-critical"})
    assert gate(safety, pr="8", base="trunk", head=HEAD) == (
        "class-not-standard",
        "class safety-critical",
    )
    assert gate(without("review_class"), pr="8", base="trunk", head=HEAD)[0] == "class-missing"
    unclassified = ready_report(review_class={**STANDARD, "unclassified": "why"})
    assert gate(unclassified, pr="8", base="trunk", head=HEAD) == ("class-unclassified", "why")
    # Readiness is reported first: a report for another head is refused as that,
    # whatever its class says.
    assert gate(safety, pr="8", base="trunk", head="b" * 40)[0] == "head-changed"
    assert gate(ready_report(pr="", base=""), pr="", base="trunk", head=HEAD)[0] == "wrong-pr"
    assert gate(ready_report(base=""), pr="8", base="", head=HEAD)[0] == "wrong-base"


SAFETY = {**STANDARD, "class": "safety-critical", "matched_paths": ["scripts/pr_watch.py"]}


@pytest.mark.parametrize(
    ("merge_class", "report", "answer"),
    [
        ("operator", ready_report(), "held"),
        # An operator lane is held on readiness alone; its class is not read.
        ("operator", without("review_class"), "held"),
        ("operator", ready_report(review_class=SAFETY), "held"),
        ("operator", ready_report(mergeable=False), "not-held"),
        ("operator", ready_report(head="b" * 40), "not-held"),
        ("operator", None, "unknown"),
        ("operator", without("merge_blockers"), "unknown"),
        # #1370: the merge wrapper refuses this lane, and the operator lands it.
        ("self", ready_report(review_class=SAFETY), "held"),
        ("self", ready_report(review_class={**STANDARD, "changes_config": True}), "held"),
        ("self", ready_report(), "not-held"),
        ("self", ready_report(review_class=SAFETY, mergeable=False), "not-held"),
        ("self", ready_report(review_class=SAFETY, head="b" * 40), "not-held"),
        ("self", ready_report(review_class=SAFETY, pr=9), "not-held"),
        ("self", ready_report(review_class=SAFETY, base="other"), "not-held"),
        ("self", without("review_class"), "unknown"),
        ("self", ready_report(review_class={"class": "safety-critical"}), "unknown"),
        ("self", ready_report(review_class={**SAFETY, "unclassified": "why"}), "unknown"),
        ("self", None, "unknown"),
        # Lane metadata that is not exactly one of the two classes holds nothing.
        ("", ready_report(review_class=SAFETY), "not-held"),
        ("Operator", ready_report(), "not-held"),
        ("operator\n", ready_report(), "not-held"),
        (None, ready_report(), "not-held"),
    ],
)
def test_held(merge_class: object, report: object, answer: str) -> None:
    held = merge_predicate.held(report, merge_class=merge_class, pr="8", base="trunk", head=HEAD)
    assert held == answer


def test_held_needs_the_pull_request_identity() -> None:
    report = ready_report(pr="", base="")
    for pr, base in (("", "trunk"), ("8", "")):
        answer = merge_predicate.held(report, merge_class="operator", pr=pr, base=base, head=HEAD)
        assert answer == "not-held"


# --------------------------------------------------------------------------- #
# the command the shell engines run
# --------------------------------------------------------------------------- #


def run_module(*args: str, stdin: str) -> subprocess.CompletedProcess[str]:
    # A bare interpreter with no environment: what a hook or a scheduled job has.
    return subprocess.run(
        [sys.executable, str(MODULE), *args],
        input=stdin,
        env={},
        capture_output=True,
        text=True,
        check=False,
    )


IDENTITY = ("--pr", "8", "--base", "trunk", "--head", HEAD)


def test_the_merge_command_prints_one_verdict_line_and_exits_zero_only_when_ready() -> None:
    ready = run_module("merge", *IDENTITY, stdin=json.dumps(ready_report()))
    assert (ready.returncode, ready.stdout) == (0, "ready\t\n")

    report = ready_report(review_class={**STANDARD, "unclassified": "a\tb\x00c\nd"})
    refused = run_module("merge", *IDENTITY, stdin=json.dumps(report))
    assert (refused.returncode, refused.stdout) == (1, "class-unclassified\ta b c d\n")

    for stdin in ("", "not json", "[]", "null"):
        malformed = run_module("merge", *IDENTITY, stdin=stdin)
        assert (malformed.returncode, malformed.stdout) == (1, "malformed\t\n"), stdin


def test_the_held_command_prints_its_answer_and_exits_to_match() -> None:
    safety = json.dumps(ready_report(review_class=SAFETY))
    cases = (
        (("--merge-class", "operator"), json.dumps(ready_report()), (0, "held\n")),
        (("--merge-class", "self"), safety, (0, "held\n")),
        (("--merge-class", "self"), json.dumps(ready_report()), (1, "not-held\n")),
        (("--merge-class", "bogus"), safety, (1, "not-held\n")),
        (("--merge-class", "self"), json.dumps(without("review_class")), (2, "unknown\n")),
        (("--merge-class", "operator"), "", (2, "unknown\n")),
        (("--merge-class", "operator"), "not json", (2, "unknown\n")),
    )
    for extra, stdin, expected in cases:
        result = run_module("held", *extra, *IDENTITY, stdin=stdin)
        assert (result.returncode, result.stdout) == expected, (extra, stdin)


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("merge",),
        ("merge", "--pr", "8", "--base", "trunk"),
        ("held", *IDENTITY),
        ("approve", *IDENTITY),
    ],
)
def test_a_usage_error_is_never_a_yes(args: tuple[str, ...]) -> None:
    """No verdict on stdout, and a status that is neither 0 nor 1."""
    result = run_module(*args, stdin=json.dumps(ready_report()))
    assert result.returncode == 2
    assert result.stdout == ""


def test_a_failure_inside_the_command_is_never_a_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(merge_predicate, "merge_gate", boom)
    monkeypatch.setattr(merge_predicate, "held", boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(ready_report())))
    assert merge_predicate.main(["merge", *IDENTITY]) == 2
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(ready_report())))
    assert merge_predicate.main(["held", "--merge-class", "operator", *IDENTITY]) == 2
