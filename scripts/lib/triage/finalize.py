"""Exact sweep planning and forge-operation accounting."""

from __future__ import annotations

import re
from typing import Any

from .canonical import digest
from .inbox import Candidate, _markdown_mask, exact_sweep
from .model import TriageError


def sweep_ids(state: dict[str, Any]) -> set[str]:
    verified = {
        operation["candidate_id"]
        for operation in state.get("operations", [])
        if operation.get("status") == "verified" and operation.get("decision") == "file"
    }
    archived = {
        decision["candidate_id"]
        for decision in state.get("decisions", [])
        if decision.get("decision") == "archive"
    }
    filed = {decision["candidate_id"] for decision in state.get("decisions", []) if decision.get("decision") == "file"}
    if verified != filed:
        raise TriageError("approved tracker batch is not authoritatively accounted", outcome="operator-held")
    return verified | archived


def render_sweep(current: bytes, archive: bytes, candidates: list[Candidate], state: dict[str, Any], marker: bytes) -> tuple[bytes, bytes]:
    ids = sweep_ids(state)
    active, archived = exact_sweep(current, candidates, ids)
    if marker:
        marker_bytes = marker + (b"\n" if not marker.endswith(b"\n") else b"")
        first_section = re.search(rb"(?m)^## ", _markdown_mask(active))
        offset = first_section.start() if first_section else len(active)
        new_active = active[:offset] + marker_bytes + active[offset:]
    else:
        new_active = active
    separator = b"" if not archive or archive.endswith(b"\n") else b"\n"
    return new_active, archive + separator + archived


def next_forge_operation(state: dict[str, Any], kind: str, intent: dict[str, Any]) -> dict[str, Any]:
    order = ["branch-create", "commit", "push", "pull-request", "pr-watch", "merge-read-back"]
    operations = state.get("finalization_operations", [])
    expected = order[len(operations)] if len(operations) < len(order) else None
    if kind != expected:
        raise TriageError(f"forge operation order violation: expected {expected}", outcome="operator-held")
    if operations and operations[-1].get("status") != "verified":
        raise TriageError("previous forge operation is not verified", outcome="operator-held")
    return {
        "kind": kind,
        "intent": intent,
        "intent_digest": digest(intent),
        "status": "attempting",
        "response": None,
        "read_back": None,
        "authority_read_back": intent.get("authority_read_back") if kind == "commit" else None,
        "attempts": [],
    }


def validate_reviewed_head(state: dict[str, Any], read_back: dict[str, Any]) -> None:
    archive = state.get("archive_sweep", {})
    reviewed = archive.get("reviewed_head")
    if not reviewed or read_back.get("headRefOid") != reviewed:
        raise TriageError("pull request head moved after review", outcome="operator-held")
    if read_back.get("merged") is not True:
        raise TriageError("pull request is not merged", outcome="operator-held")
