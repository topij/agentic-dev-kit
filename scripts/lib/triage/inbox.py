"""Exact-byte friction inbox parsing and accounted-block transformation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .canonical import digest_bytes, encode_bytes
from .model import TriageError

SECTION_RE = re.compile(rb"(?m)^## (?P<title>[^\n]+)\n")
DATED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:\s|$)")
ENTRY_RE = re.compile(rb"(?m)^- \*\*")
ACCOUNTED_RE = re.compile(rb"(?m)^\s*\*\*(?:Filed|Routed|Reconciled)\b")


def _markdown_mask(raw: bytes) -> bytes:
    """Blank fenced-code lines while preserving every byte offset and newline."""
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
        if not DATED_RE.match(title) or "Backlog migrated" in title:
            continue
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        entries = list(ENTRY_RE.finditer(visible, match.end(), section_end))
        for entry_index, entry in enumerate(entries):
            end = entries[entry_index + 1].start() if entry_index + 1 < len(entries) else section_end
            block = raw[entry.start():end]
            if ACCOUNTED_RE.search(visible[entry.start():end]):
                continue
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
        if DATED_RE.match(title) and not ENTRY_RE.search(visible_active, section.end(), end) and not active[section.end():end].strip():
            empty_sections.append((section.start(), end))
    for start, end in reversed(empty_sections):
        active = active[:start] + active[end:]
    archived = bytearray()
    for title, blocks in archived_by_title.items():
        archived.extend(f"## {title}\n\n".encode())
        for block in blocks:
            archived.extend(block)
            if not archived.endswith(b"\n"):
                archived.extend(b"\n")
    return active, bytes(archived)
