"""Exact-byte friction inbox parsing and block transformation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .canonical import digest_bytes, encode_bytes
from .model import TriageError

SECTION_RE = re.compile(rb"(?m)^## (?P<title>[^\n]+)\n")
DATED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:\s|$)")
ENTRY_RE = re.compile(rb"(?m)^- \*\*")

# The literal a graduation-marker heading carries, e.g. "## 2026-09-25 — Backlog
# migrated by triage session <id>". `parse` excludes a marker section from the
# active candidate set on this substring; `exact_sweep`'s empty-section removal
# reuses the same recognizer so it never deletes a marker that carries no entry
# of its own (#806) — one recognizer, not two independently-maintained checks.
MIGRATION_MARKER_TITLE = "Backlog migrated"


def is_migration_marker(title: str) -> bool:
    return MIGRATION_MARKER_TITLE in title


def _inline_literal(value: Any) -> str:
    """Return a one-line code span that no backtick run in the value can close.

    Only non-empty printable text without edge whitespace is shown verbatim. Anything
    else is shown as its escaped Python string literal, labelled outside the span so
    the escape cannot be mistaken for the value itself. Shared by the engine's report
    renderer and the friction-log record block: both embed state-derived text (an
    operator identity, a verbatim command) into a Markdown document neither of them
    controls the shape of, so both need the same guarantee that the embedded value
    cannot open a new heading or entry line.
    """
    text = value if isinstance(value, str) else str(value)
    verbatim = bool(text) and text == text.strip() and text.isprintable()
    shown = text if verbatim else ascii(text)
    longest = max((len(match.group()) for match in re.finditer("`+", shown)), default=0)
    delimiter = "`" * (longest + 1)
    padding = " " if shown.startswith("`") or shown.endswith("`") else ""
    span = f"{delimiter}{padding}{shown}{padding}{delimiter}"
    return span if verbatim else span + " (escaped Python string literal)"


def _markdown_mask(raw: bytes) -> bytes:
    """Blank fenced and inline code while preserving byte offsets and newlines."""
    masked = bytearray(raw)
    offset = 0
    fence: tuple[int, int] | None = None
    for line in raw.splitlines(keepends=True):
        content = line.rstrip(b"\r\n")
        indent = len(content) - len(content.lstrip(b" "))
        tail = content[indent:] if indent <= 3 else b""
        opening: tuple[int, int] | None = None
        if tail:
            marker = tail[0]
            if marker in (ord("`"), ord("~")):
                length = len(tail) - len(tail.lstrip(bytes([marker])))
                remainder = tail[length:]
                if length >= 3 and (marker != ord("`") or b"`" not in remainder):
                    opening = (marker, length)
        blank = fence is not None or opening is not None
        if fence is not None and tail:
            marker, minimum = fence
            length = len(tail) - len(tail.lstrip(bytes([marker])))
            if length >= minimum and not tail[length:].strip(b" \t"):
                fence = None
        elif opening is not None:
            fence = opening
        if blank:
            for index in range(offset, offset + len(line)):
                if masked[index] not in (10, 13):
                    masked[index] = 32
        offset += len(line)
    cursor = 0
    while cursor < len(masked):
        start = masked.find(b"`", cursor)
        if start < 0:
            break
        length = len(masked[start:]) - len(masked[start:].lstrip(b"`"))
        remainder = masked[start + length :]
        boundaries = [
            match.start()
            for pattern in (rb"\r?\n[ \t]*\r?\n", rb"(?m)^(?:## |- \*\*)")
            if (match := re.search(pattern, remainder)) is not None
        ]
        limit = len(masked) if not boundaries else start + length + min(boundaries)
        search = start + length
        closing = -1
        while search < limit:
            candidate = masked.find(b"`", search, limit)
            if candidate < 0:
                break
            candidate_length = len(masked[candidate:]) - len(masked[candidate:].lstrip(b"`"))
            if candidate_length == length:
                closing = candidate
                break
            search = candidate + candidate_length
        if closing < 0:
            cursor = start + length
            continue
        for index in range(start, closing + length):
            if masked[index] not in (10, 13):
                masked[index] = 32
        cursor = closing + length
    return bytes(masked)


def _title(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TriageError("friction-log heading is not UTF-8") from exc


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    title: str
    raw: bytes
    digest: str
    start: int
    end: int

    def record(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "source_block_encoding": "base64",
            "source_block": encode_bytes(self.raw),
            "source_block_digest": self.digest,
        }


def parse(raw: bytes) -> list[Candidate]:
    visible = _markdown_mask(raw)
    matches = list(SECTION_RE.finditer(visible))
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        title = _title(match.group("title"))
        if not DATED_RE.match(title) or is_migration_marker(title):
            continue
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        entries = list(ENTRY_RE.finditer(visible, match.end(), section_end))
        for entry_index, entry in enumerate(entries):
            end = entries[entry_index + 1].start() if entry_index + 1 < len(entries) else section_end
            block = raw[entry.start():end]
            block_digest = digest_bytes(block)
            if block_digest in seen:
                raise TriageError("duplicate active source block")
            seen.add(block_digest)
            candidate_id = f"TRI-{len(candidates) + 1:02d}"
            candidates.append(Candidate(candidate_id, title, block, block_digest, entry.start(), end))
    return candidates


def snapshot_content(raw: bytes, candidates: list[Candidate]) -> dict[str, Any]:
    return {
        "raw_encoding": "base64",
        "raw": encode_bytes(raw),
        "candidate_index": [candidate.record() for candidate in candidates],
    }


def exact_sweep(current: bytes, frozen: list[Candidate], sweep_ids: set[str]) -> tuple[bytes, bytes]:
    selected = [candidate for candidate in frozen if candidate.candidate_id in sweep_ids]
    unknown = sweep_ids - {candidate.candidate_id for candidate in frozen}
    if unknown:
        raise TriageError(f"unknown sweep candidate: {sorted(unknown)!r}", outcome="operator-held")
    current_blocks: list[tuple[int, int, bytes, str]] = []
    visible = _markdown_mask(current)
    sections = list(SECTION_RE.finditer(visible))
    for index, section in enumerate(sections):
        title = _title(section.group("title"))
        if not DATED_RE.match(title):
            continue
        section_end = sections[index + 1].start() if index + 1 < len(sections) else len(current)
        entries = list(ENTRY_RE.finditer(visible, section.end(), section_end))
        for entry_index, entry in enumerate(entries):
            end = entries[entry_index + 1].start() if entry_index + 1 < len(entries) else section_end
            current_blocks.append((entry.start(), end, current[entry.start():end], title))
    removals: list[tuple[int, int]] = []
    archived_by_title: dict[str, list[bytes]] = {}
    for candidate in selected:
        matches = [block for block in current_blocks if block[2] == candidate.raw and block[3] == candidate.title]
        if len(matches) != 1:
            raise TriageError(
                f"frozen source block changed or is ambiguous: {candidate.candidate_id}",
                outcome="operator-held",
            )
        start, end, block, title = matches[0]
        removals.append((start, end))
        archived_by_title.setdefault(title, []).append(block)
    active = current
    for start, end in sorted(removals, reverse=True):
        active = active[:start] + active[end:]
    # A date heading remains when another entry, including a newly added one,
    # still occupies its section. Remove only now-empty dated sections.
    visible_active = _markdown_mask(active)
    sections = list(SECTION_RE.finditer(visible_active))
    empty_sections: list[tuple[int, int]] = []
    for index, section in enumerate(sections):
        title = _title(section.group("title"))
        end = sections[index + 1].start() if index + 1 < len(sections) else len(active)
        if (
            DATED_RE.match(title)
            and not is_migration_marker(title)
            and not ENTRY_RE.search(visible_active, section.end(), end)
            and not active[section.end():end].strip()
        ):
            empty_sections.append((section.start(), end))
    for start, end in reversed(empty_sections):
        if end >= len(active):
            # The removed section was the file's last, so the blank line that
            # separated it from whatever now precedes it would otherwise become
            # a trailing blank line at EOF (#806). Collapse to a single newline,
            # or to nothing when no content precedes it.
            active = active[:start].rstrip(b"\n")
            if active:
                active += b"\n"
        else:
            active = active[:start] + active[end:]
    archived = bytearray()
    for title, blocks in archived_by_title.items():
        archived.extend(f"## {title}\n\n".encode())
        for block in blocks:
            archived.extend(block)
            if not archived.endswith(b"\n"):
                archived.extend(b"\n")
    return active, bytes(archived)
