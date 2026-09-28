"""Exact sweep planning and forge-operation accounting."""

from __future__ import annotations

import re
from typing import Any

from .approval import COMMAND_RE
from .canonical import digest
from .inbox import (
    Candidate,
    _inline_literal,
    _markdown_mask,
    append_archive_groups,
    append_archive_sections,
    exact_sweep,
    sweep_groups,
    take_migration_markers,
)
from .model import TriageError

CANDIDATE_ID_RE = re.compile(r"TRI-(\d+)")
GITHUB_REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
GITHUB_HOST_RE = re.compile(r"[A-Za-z0-9.-]+")
NUMERIC_IDENTIFIER_RE = re.compile(r"[1-9][0-9]*")
RENDERINGS = ("current", "pre-187", "pre-818", "pre-812")


def _candidate_sort_key(candidate_id: Any) -> tuple[int, str]:
    text = candidate_id if isinstance(candidate_id, str) else ""
    match = CANDIDATE_ID_RE.fullmatch(text)
    return (int(match.group(1)), text) if match else (2**63, text)


def _issue_link(destination: Any, identifier: Any) -> str:
    """Render a filed identifier as a Markdown issue link when the destination and
    identifier are exactly the shape the GitHub adapter itself requires (mirrors
    `GitHubIssues._repository`'s validation); otherwise fall back to a safe inline
    literal rather than assembling a URL from unverified state."""
    identifier_text = identifier if isinstance(identifier, str) else str(identifier)
    if (
        isinstance(destination, dict)
        and destination.get("backend") == "github-issues"
        and isinstance(destination.get("host"), str)
        and GITHUB_HOST_RE.fullmatch(destination["host"])
        and isinstance(destination.get("repository"), str)
        and GITHUB_REPOSITORY_RE.fullmatch(destination["repository"])
        and NUMERIC_IDENTIFIER_RE.fullmatch(identifier_text)
    ):
        return f"[#{identifier_text}](https://{destination['host']}/{destination['repository']}/issues/{identifier_text})"
    return _inline_literal(identifier)


def _entry_lead(raw: bytes) -> str:
    """The bold lead an inbox entry opens with (`- **Lead.** …`), whitespace-collapsed
    because a long lead wraps across source lines; empty when there is none.

    The lead may itself contain bold (`- **Do **not** panic.** …`), so its end is the
    first `**` that closes rather than opens: a `**` preceded by whitespace and
    followed by a non-space opens a nested span, a `**` preceded by a non-space
    closes one, and each nested span's closer is skipped. A `**` with whitespace on
    both sides, or inside a code span, is text, not a delimiter. The lead never runs
    past a blank line."""
    if not raw.startswith(b"- **"):
        return ""
    text = raw[4:].split(b"\n\n", 1)[0]
    visible = _markdown_mask(text)
    depth = 0
    for match in re.finditer(rb"\*\*", visible):
        start, end = match.span()
        before, after = visible[start - 1:start], visible[end:end + 1]
        if after and not after.isspace() and (not before or before.isspace()):
            depth += 1
        elif not before or before.isspace():
            continue
        elif depth:
            depth -= 1
        else:
            return " ".join(text[:start].decode("utf-8", "replace").split())
    return ""


def _source_entry(candidate_id: Any, sources: dict[str, Candidate]) -> str:
    """Name the inbox entry a swept candidate came from (#818): its id, date heading
    and bold lead, the last two through `_inline_literal` because they are copied
    from operator-written text."""
    shown = candidate_id if isinstance(candidate_id, str) and CANDIDATE_ID_RE.fullmatch(candidate_id) else _inline_literal(candidate_id)
    candidate = sources.get(candidate_id) if isinstance(candidate_id, str) else None
    if candidate is None:
        return shown
    lead = _entry_lead(candidate.raw)
    entry = f"{shown}, the {_inline_literal(candidate.title)} entry"
    return f"{entry} {_inline_literal(lead)}" if lead else entry


def _record_lines(state: dict[str, Any], sources: dict[str, Candidate] | None = None) -> list[str]:
    """Build the record a marker's own block carries: what an engine-backed sweep
    filed, archived, and ran under, from data the engine already holds in `state` —
    never invented, and never state text placed where it could open a heading or
    entry line of its own (`_inline_literal` guarantees the latter).

    With `sources` (the frozen candidates by id) each filed and archived candidate
    gets its own line naming the entry it came from (#818). Without it the lines are
    the pre-#818 lists, kept so a sweep an older engine committed still validates."""
    lines: list[str] = []
    engine_mode = state.get("engine_mode")
    if isinstance(engine_mode, str) and engine_mode:
        lines.append(f"Engine mode: {_inline_literal(engine_mode)}.")
    operations = state.get("operations") or []
    filed = sorted(
        (
            operation
            for operation in operations
            if isinstance(operation, dict) and operation.get("status") == "verified" and operation.get("decision") == "file"
        ),
        key=lambda operation: _candidate_sort_key(operation.get("candidate_id")),
    )
    if filed and sources is None:
        links = [_issue_link(operation.get("destination"), operation.get("returned_identifier")) for operation in filed]
        lines.append("Filed: " + ", ".join(links) + ".")
    elif filed:
        for operation in filed:
            link = _issue_link(operation.get("destination"), operation.get("returned_identifier"))
            lines.append(f"Filed {link} from {_source_entry(operation.get('candidate_id'), sources)}.")
    decisions = state.get("decisions") or []
    archived = sorted(
        (
            decision["candidate_id"]
            for decision in decisions
            if isinstance(decision, dict) and decision.get("decision") == "archive" and isinstance(decision.get("candidate_id"), str)
        ),
        key=_candidate_sort_key,
    )
    if archived and sources is None:
        lines.append("Archived without filing: " + ", ".join(archived) + ".")
    elif archived:
        for candidate_id in archived:
            lines.append(f"Archived without filing: {_source_entry(candidate_id, sources)}.")
    approval = state.get("approval")
    if isinstance(approval, dict):
        source_read_back = approval.get("source_read_back")
        command = source_read_back.get("text") if isinstance(source_read_back, dict) else None
        approver = approval.get("approver_identity")
        if isinstance(command, str) and command and isinstance(approver, str) and approver:
            if "\n" in command and all(COMMAND_RE.fullmatch(line) for line in command.split("\n")):
                # A multi-command approval (#820) shows each command as its own span
                # rather than one escaped literal with its newlines spelled out. Any
                # other multi-line text — a `modify` body that spans lines — stays
                # one escaped literal, so its body lines never read as commands.
                shown = ", ".join(_inline_literal(line) for line in command.split("\n"))
                lines.append(f"Approval commands: {shown}. Approver: {_inline_literal(approver)}.")
            else:
                lines.append(f"Approval command: {_inline_literal(command)}. Approver: {_inline_literal(approver)}.")
    return lines


def _record_block(state: dict[str, Any], sources: dict[str, Candidate] | None = None) -> bytes:
    lines = _record_lines(state, sources)
    return ("\n\n".join(lines) + "\n").encode("utf-8") if lines else b""


def _blank_line_separator(before: bytes) -> bytes:
    """The bytes to insert so a `## ` heading appended right after `before` gets
    exactly one blank line ahead of it — nothing when `before` is empty (a leading
    heading needs no separator) or already ends in a blank line, one more newline
    when it ends in exactly one. Shared by the marker insertion and the archive
    append (#806: the archive append previously had no separator at all)."""
    if not before or before.endswith(b"\n\n"):
        return b""
    return b"\n" if before.endswith(b"\n") else b"\n\n"


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


def render_sweep(
    current: bytes,
    archive: bytes,
    candidates: list[Candidate],
    state: dict[str, Any],
    marker: bytes,
    *,
    rendering: str = "current",
) -> tuple[bytes, bytes]:
    """Render a sweep's new inbox and archive bytes from the approved `state`.

    `rendering` picks one of `RENDERINGS`. Only `current` renders a new sweep; the
    older ones reproduce, byte for byte, what an engine before #187, #818 or #812
    committed, so commit validation can still accept a sweep such an engine left.
    `current` differs from `pre-187` only in moving every earlier graduation-marker
    section to the archive, ahead of this sweep's groups, before writing its own.
    """
    if rendering not in RENDERINGS:
        raise ValueError(f"unknown sweep rendering: {rendering!r}")
    ids = sweep_ids(state)
    legacy = rendering == "pre-812"
    if legacy:
        active, archived = exact_sweep(current, candidates, ids, legacy=True)
        # The pre-#812 rendering, kept byte-for-byte: a bare marker with no record,
        # no separator management, and an archive append with no blank line before
        # its heading. Only commit validation asks for it (see `exact_sweep`).
        if marker:
            marker_bytes = marker + (b"\n" if not marker.endswith(b"\n") else b"")
            first_section = re.search(rb"(?m)^## ", _markdown_mask(active))
            offset = first_section.start() if first_section else len(active)
            active = active[:offset] + marker_bytes + active[offset:]
        separator = b"" if not archive or archive.endswith(b"\n") else b"\n"
        return active, archive + separator + archived
    if rendering == "pre-818":
        active, archived = exact_sweep(current, candidates, ids)
        new_archive = archive + _blank_line_separator(archive) + archived
        sources = None
    else:
        active, groups = sweep_groups(current, candidates, ids)
        if rendering == "current":
            active, markers = take_migration_markers(active)
            archive = append_archive_sections(archive, markers)
        new_archive = append_archive_groups(archive, groups)
        sources = {candidate.candidate_id: candidate for candidate in candidates}
    if marker:
        marker_bytes = marker + (b"\n" if not marker.endswith(b"\n") else b"")
        record_bytes = _record_block(state, sources)
        first_section = re.search(rb"(?m)^## ", _markdown_mask(active))
        offset = first_section.start() if first_section else len(active)
        prefix = active[:offset]
        tail = active[offset:]
        body = marker_bytes + record_bytes
        if tail:
            gap = _blank_line_separator(body)
        else:
            # Nothing follows the marker, so its own trailing blank line (from
            # `marker_bytes`, or the single newline `record_bytes` already ends
            # in) would otherwise become a trailing blank line at EOF (#806).
            body = body.rstrip(b"\n") + b"\n"
            gap = b""
        new_active = prefix + _blank_line_separator(prefix) + body + gap + tail
    else:
        new_active = active
    return new_active, new_archive


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
