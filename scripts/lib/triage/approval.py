"""Complete approval command parsing and exact payload binding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .model import TriageError

COMMAND_RE = re.compile(r"^(approve|archive|park)\s+(.+)$")
MODIFY_RE = re.compile(r"^modify\s+([A-Za-z0-9_-]+):\s+(.+)$", re.DOTALL)


@dataclass(frozen=True)
class ApprovalContext:
    """Identity/read-back attested by the invoking runtime, outside request JSON."""

    source: str
    operator_identity: str
    source_read_back: dict[str, Any]


def parse_commands(text: str, proposal_digests: dict[str, str]) -> list[dict[str, Any]]:
    if text != text.strip() or not text:
        raise TriageError("approval command must be exact", outcome="operator-held")
    if text == "cancel":
        return [{"candidate_id": candidate_id, "decision": "park", "proposal_digest": proposal_digests[candidate_id]} for candidate_id in proposal_digests]
    decisions: dict[str, dict[str, Any]] = {}
    modify = MODIFY_RE.fullmatch(text)
    if modify:
        candidate_id, body = modify.groups()
        if candidate_id not in proposal_digests:
            raise TriageError("unknown modify candidate", outcome="operator-held")
        decisions[candidate_id] = {"candidate_id": candidate_id, "decision": "modify", "replacement_body": body, "proposal_digest": proposal_digests[candidate_id]}
    else:
        match = COMMAND_RE.fullmatch(text)
        if not match:
            raise TriageError("unknown or mixed approval command", outcome="operator-held")
        verb, ids_text = match.groups()
        if "," in ids_text or re.search(r"\b(?:approve|archive|park|modify|cancel)\b", ids_text):
            raise TriageError("mixed or malformed approval command", outcome="operator-held")
        if ids_text == "all":
            if verb != "approve":
                raise TriageError("only approve all is supported", outcome="operator-held")
            ids = list(proposal_digests)
        else:
            ids = ids_text.split(" ")
            if any(not candidate_id for candidate_id in ids):
                raise TriageError("malformed candidate list", outcome="operator-held")
        decision = "file" if verb == "approve" else verb
        for candidate_id in ids:
            if candidate_id not in proposal_digests or candidate_id in decisions:
                raise TriageError("unknown or duplicate approval candidate", outcome="operator-held")
            decisions[candidate_id] = {"candidate_id": candidate_id, "decision": decision, "proposal_digest": proposal_digests[candidate_id]}
    for candidate_id, proposal_digest in proposal_digests.items():
        decisions.setdefault(candidate_id, {"candidate_id": candidate_id, "decision": "park", "proposal_digest": proposal_digest})
    return [decisions[candidate_id] for candidate_id in proposal_digests]


def approval_record(
    decisions: list[dict[str, Any]],
    *,
    context: ApprovalContext,
    proposal_set_digest: str,
    command_text: str,
) -> dict[str, Any]:
    if not isinstance(context.source, str) or context.source not in {"current-session", "notification-thread"}:
        raise TriageError("untrusted approval source", outcome="operator-held")
    if not isinstance(context.operator_identity, str) or not context.operator_identity:
        raise TriageError("approval identity does not match the operator", outcome="operator-held")
    if (
        not isinstance(command_text, str)
        or not isinstance(context.source_read_back, dict)
        or context.source_read_back.get("approver_identity") != context.operator_identity
        or context.source_read_back.get("text") != command_text
    ):
        raise TriageError("approval source read-back is not authoritative", outcome="operator-held")
    return {
        "source": context.source,
        "approver_identity": context.operator_identity,
        "commands": decisions,
        "proposal_set_digest": proposal_set_digest,
        "source_read_back": context.source_read_back,
    }
