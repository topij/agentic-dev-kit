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
