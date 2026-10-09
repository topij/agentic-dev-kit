from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.approval import ApprovalContext, approval_record, parse_commands  # noqa: E402
from triage.model import TriageError  # noqa: E402

PROPOSALS = {"TRI-01": "a" * 64, "TRI-02": "b" * 64}


def test_one_exact_verb_and_unmentioned_default_to_park() -> None:
    assert parse_commands("approve TRI-01", PROPOSALS) == [
        {"candidate_id": "TRI-01", "decision": "file", "proposal_digest": "a" * 64},
        {"candidate_id": "TRI-02", "decision": "park", "proposal_digest": "b" * 64},
    ]


@pytest.mark.parametrize(
    "command",
    [
        "approve TRI-01, archive TRI-02",
        "approve TRI-01 archive TRI-02",
        "approve TRI-01,",
        "archive all",
        " approve TRI-01",
        "approve TRI-01 ",
    ],
)
def test_mixed_or_inexact_commands_are_rejected(command: str) -> None:
    with pytest.raises(TriageError):
        parse_commands(command, PROPOSALS)


@pytest.mark.parametrize("command", ["approve TRI-01,TRI-02", "approve TRI-01, TRI-02", "archive TRI-01,TRI-02"])
def test_a_comma_separated_id_list_is_refused_naming_the_separator(command: str) -> None:
    # #1016: the operator sent the comma form the cockpit suggested and got only
    # "mixed or malformed"; the refusal now says what to send instead.
    with pytest.raises(TriageError, match="ids are space-separated; a comma is not a separator"):
        parse_commands(command, PROPOSALS)
    assert [item["decision"] for item in parse_commands(command.replace(",", " ").replace("  ", " "), PROPOSALS)] == ["file" if command.startswith("approve") else "archive"] * 2


def test_modify_body_preserves_commas_and_requires_later_approval() -> None:
    decisions = parse_commands("modify TRI-01: replacement, with comma", PROPOSALS)
    assert decisions[0]["replacement_body"] == "replacement, with comma"
    assert decisions[0]["decision"] == "modify"


def test_approval_requires_exact_operator_and_readback() -> None:
    decisions = parse_commands("approve all", PROPOSALS)
    record = approval_record(
        decisions,
        context=ApprovalContext("current-session", "operator", {"approver_identity": "operator", "text": "approve all"}),
        proposal_set_digest="c" * 64,
        command_text="approve all",
    )
    assert record["approver_identity"] == "operator"
    with pytest.raises(TriageError, match="does not match"):
        approval_record(
            decisions,
            context=ApprovalContext("current-session", "", {"approver_identity": ""}),
            proposal_set_digest="c" * 64,
            command_text="approve all",
        )


THREE = {"TRI-01": "a" * 64, "TRI-02": "b" * 64, "TRI-03": "c" * 64}


def test_one_reply_carries_approve_and_archive_and_unmentioned_parks() -> None:
    # #820: the operator sent both verbs at once and the engine could take only one.
    assert parse_commands("archive TRI-02\napprove TRI-01", THREE) == [
        {"candidate_id": "TRI-01", "decision": "file", "proposal_digest": "a" * 64},
        {"candidate_id": "TRI-02", "decision": "archive", "proposal_digest": "b" * 64},
        {"candidate_id": "TRI-03", "decision": "park", "proposal_digest": "c" * 64},
    ]


def test_the_same_verb_may_span_lines() -> None:
    decisions = parse_commands("approve TRI-01\napprove TRI-03\npark TRI-02", THREE)
    assert [item["decision"] for item in decisions] == ["file", "park", "file"]


@pytest.mark.parametrize(
    ("command", "message"),
    [
        ("approve TRI-01\narchive TRI-01", "duplicate"),
        ("approve TRI-01\napprove TRI-01", "duplicate"),
        ("approve TRI-01\n\narchive TRI-02", "non-empty"),
        ("approve TRI-01\n archive TRI-02", "exact"),
        ("approve TRI-01\r\narchive TRI-02", "exact"),
        ("approve TRI-01\napprove all", "alone"),
        ("approve all\narchive TRI-02", "alone"),
        ("approve TRI-01\ncancel", "unknown or mixed"),
        ("approve TRI-01\nmodify TRI-02: body", "unknown or mixed"),
        ("approve TRI-01\narchive TRI-09", "unknown"),
        ("approve TRI-01\narchive TRI-02 approve TRI-03", "mixed"),
    ],
)
def test_a_multi_command_reply_is_rejected_whole_on_any_bad_line(command: str, message: str) -> None:
    with pytest.raises(TriageError, match=message):
        parse_commands(command, THREE)


@pytest.mark.parametrize("trailing", ["approve TRI-02", "archive TRI-02 TRI-03", "approve all", "cancel"])
def test_a_command_after_a_modify_is_not_swallowed_into_its_body(trailing: str) -> None:
    with pytest.raises(TriageError, match="modify must be sent alone"):
        parse_commands(f"modify TRI-01: replacement\n{trailing}", THREE)


def test_a_modify_body_may_still_span_lines_and_use_command_words() -> None:
    body = "First line.\napprove the change once reviewed\narchive TRI-09 is not in this batch"
    decisions = parse_commands(f"modify TRI-01: {body}", THREE)
    assert decisions[0] == {"candidate_id": "TRI-01", "decision": "modify", "replacement_body": body, "proposal_digest": "a" * 64}


@pytest.mark.parametrize("line", ["archive all", "park all", "approve TRI-01 TRI-09"])
def test_a_modify_body_line_that_is_no_valid_command_for_this_batch_is_body_text(line: str) -> None:
    decisions = parse_commands(f"modify TRI-01: First line.\n{line}", THREE)
    assert decisions[0]["replacement_body"] == f"First line.\n{line}"
