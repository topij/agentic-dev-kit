#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Sweep old session blocks out of the live handoff into its history document.

The living handoff doc keeps only the most-recent handful of session blocks —
whether written as ``## Latest session`` / ``## Earlier session``, as a bare
dated ``## June 5 Fri (cont.) — …`` heading, or as ``###`` entries below a
``## Recent sessions`` section; everything older belongs in the append-only
handoff history. Doing this by hand is
error-prone (an unswept handoff doc balloons over time, making every session
start more expensive), so this script makes it a **deterministic, idempotent**
operation: keep the newest ``--keep`` blocks live, move the rest verbatim into
the history file (demoting ``## Earlier session — X`` headings to ``### X`` to
match its convention), refresh the "older entries moved to history" pointer,
and trim the line-16 quick-scan megaline to roughly the kept blocks.

It only ever *moves* content — every cross-reference (ticket ids, PR links,
commit shas, …) is preserved. Standing sections (Security, Next up, Backlog,
…) below the session region are left untouched. Running it when there is
nothing to move is a clean no-op.

Usage:

    uv run scripts/archive_plan_sessions.py                  # keep 6, apply
    uv run scripts/archive_plan_sessions.py --keep 5
    uv run scripts/archive_plan_sessions.py --dry-run         # report only
    uv run scripts/archive_plan_sessions.py --plan docs/handoff.md --history docs/handoff-history.md

Exit codes:
    0 — applied (or nothing to do, or dry-run)
    2 — usage error / unparseable handoff-doc structure
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from devmodel_config import _repo_root, load_config, resolve_path  # noqa: E402

REPO_ROOT = _repo_root()
SEP = "______________________________________________________________________\n"
SESSION_PREFIXES = ("## Latest session", "## Earlier session", "## Session — ")
# Recent sessions may write *dated* headings (`## June 5 Fri (cont.) — …`) or a
# bare `## Session — June 12 Fri — …` rather than the canonical `## Latest/
# Earlier session — …` (the `## Session` prefix is in SESSION_PREFIXES above).
# Recognise all of these, else split_plan mistakes the first unrecognised
# heading for the start of the standing sections and the sweep silently moves
# nothing. Anchored on an *exact* month name (full or 3-letter abbrev) + day
# number so it never matches a standing section that merely starts with a
# month-like word (`## Marketing 5 …`, `## Backlog`, `## Sprint history`, …).
_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
    "|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)
_DATED_SESSION_RE = re.compile(rf"^## (?:{_MONTHS}) \d{{1,2}}\b")
DEFAULT_KEEP = 6
RECENT_SESSIONS_HEADING = "## Recent sessions"
HISTORY_SECTION_HEADINGS = ("## Session log", "## Recent sessions (archived)")

POINTER = [
    "> Older session entries (below the live blocks above) live in [`handoff-history.md`](handoff-history.md).\n",
    '> Active open items from them are folded into the "Open for next session" lists above.\n',
    "\n",
    SEP,
    "\n",
]


def configured_paths(
    root: Path = REPO_ROOT, config_path: Path | None = None
) -> tuple[Path, Path]:
    """Resolve the live handoff and history paths from ``dev-model.yaml``."""
    config = load_config(config_path or root / "config" / "dev-model.yaml")
    return (
        resolve_path(config, "paths.handoff", root=root),
        resolve_path(config, "paths.handoff_history", root=root),
    )


def _is_session_heading(line: str) -> bool:
    return line.startswith(SESSION_PREFIXES) or bool(_DATED_SESSION_RE.match(line))


def _is_sep(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= 3 and set(stripped) in ({"_"}, {"-"})


def split_plan(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return ``(head, session_region, tail)``.

    ``head`` runs up to the first session heading; ``session_region`` covers the
    session blocks plus any inter-block separators and the existing pointer;
    ``tail`` is the first non-session ``##`` heading (standing sections) onward.
    """
    sess_start = next((i for i, ln in enumerate(lines) if _is_session_heading(ln)), None)
    if sess_start is not None:
        standing = next(
            (
                i
                for i, ln in enumerate(lines)
                if i > sess_start
                and ln.startswith("## ")
                and not _is_session_heading(ln)
            ),
            len(lines),
        )
        return lines[:sess_start], lines[sess_start:standing], lines[standing:]

    recent_start = next(
        (
            i
            for i, ln in enumerate(lines)
            if ln.rstrip("\n") == RECENT_SESSIONS_HEADING
        ),
        None,
    )
    if recent_start is None:
        raise ValueError(
            "no session blocks or '## Recent sessions' section found in handoff doc"
        )
    standing = next(
        (
            i
            for i, ln in enumerate(lines)
            if i > recent_start and ln.startswith("## ")
        ),
        len(lines),
    )
    # Keep the section heading in the head; parse_blocks handles its ``###``
    # entries and rebuild_plan preserves this layout without adding a pointer.
    return lines[: recent_start + 1], lines[recent_start + 1 : standing], lines[standing:]


def parse_blocks(region: list[str]) -> list[list[str]]:
    """Split the session region into per-block line lists, newest first.

    Trailing blank/separator/pointer (``>``) lines are stripped from each block,
    so the pointer the previous run wrote never gets absorbed into a block.
    """
    blocks: list[list[str]] = []
    uses_recent_sections = not any(_is_session_heading(line) for line in region)

    def is_block_heading(line: str) -> bool:
        if uses_recent_sections:
            return line.startswith("### ")
        return _is_session_heading(line)

    cur: list[str] | None = None
    for line in region:
        if is_block_heading(line):
            if cur is not None:
                blocks.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        blocks.append(cur)
    for block in blocks:
        while block and (block[-1].strip() == "" or _is_sep(block[-1]) or block[-1].startswith(">")):
            block.pop()
    return blocks


def demote(block: list[str]) -> list[str]:
    """Convert a handoff session block to a history-doc ``### <date>`` entry.

    Handles both the canonical ``## Latest/Earlier session — <date>`` form and a
    bare dated ``## June 5 Fri (cont.) — …`` heading; only the block's heading line
    matches, body lines pass through unchanged.
    """
    out: list[str] = []
    for i, line in enumerate(block):
        if i == 0:
            for prefix in ("## Earlier session — ", "## Latest session — "):
                if line.startswith(prefix):
                    line = "### " + line[len(prefix) :]
                    break
            else:
                if _DATED_SESSION_RE.match(line):
                    line = "### " + line[len("## ") :]
        out.append(line)
    return out


def trim_megaline(head: list[str], keep: int) -> list[str]:
    """Trim the ``Last updated:`` megaline to its first ``keep`` ``|``-segments."""
    out = list(head)
    for i, line in enumerate(out):
        if line.startswith("Last updated:"):
            segments = line.rstrip("\n").split(" | ")
            if len(segments) > keep:
                out[i] = " | ".join(segments[:keep]) + "\n"
            break
    return out


def rebuild_plan(head: list[str], keep_blocks: list[list[str]], tail: list[str], keep: int) -> list[str]:
    """Reassemble the handoff doc from the trimmed head, kept blocks, fresh pointer, and tail."""
    if head and head[-1].rstrip("\n") == RECENT_SESSIONS_HEADING:
        body: list[str] = ["\n"]
        for block in keep_blocks:
            body += block + ["\n", "---\n", "\n"]
        return head + body + tail

    head = trim_megaline(head, keep)
    body: list[str] = []
    for block in keep_blocks:
        body += block + ["\n", SEP, "\n"]
    body += POINTER
    return head + body + tail


def insert_into_history(history: list[str], moved: list[list[str]]) -> list[str]:
    """Insert demoted blocks at the top of a recognized history session section."""
    try:
        sl = next(
            i
            for i, ln in enumerate(history)
            if ln.rstrip("\n") in HISTORY_SECTION_HEADINGS
        )
    except StopIteration as exc:
        expected = "' or '".join(HISTORY_SECTION_HEADINGS)
        raise ValueError(f"history doc has no '{expected}' section") from exc
    # skip the blank line after the header, insert before the first entry
    insert_at = sl + 1
    while insert_at < len(history) and history[insert_at].strip() == "":
        insert_at += 1
    chunk: list[str] = []
    for block in moved:
        chunk += demote(block) + ["\n"]
    return history[:insert_at] + chunk + history[insert_at:]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: keep the newest ``--keep`` session blocks, archive the rest.

    Returns 0 on success / no-op / dry-run, 2 on usage error, unparseable handoff
    structure, or a failed write (the handoff doc is rolled back in that case).
    """
    default_plan, default_history = configured_paths()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="live blocks to keep")
    parser.add_argument("--plan", type=Path, default=default_plan, help="living handoff doc")
    parser.add_argument(
        "--history", type=Path, default=default_history, help="handoff history/archive doc"
    )
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args(argv)

    if args.keep < 1:
        print("error: --keep must be >= 1", file=sys.stderr)
        return 2
    for path in (args.plan, args.history):
        if not path.is_file():
            print(f"error: not found: {path}", file=sys.stderr)
            return 2

    plan = args.plan.read_text(encoding="utf-8").splitlines(keepends=True)
    history = args.history.read_text(encoding="utf-8").splitlines(keepends=True)

    try:
        head, region, tail = split_plan(plan)
        blocks = parse_blocks(region)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if len(blocks) <= args.keep:
        print(f"nothing to move: {len(blocks)} session block(s) <= --keep {args.keep}.")
        return 0

    keep_blocks, moved = blocks[: args.keep], blocks[args.keep :]
    new_plan = rebuild_plan(head, keep_blocks, tail, args.keep)
    try:
        new_history = insert_into_history(history, moved)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    moved_titles = [b[0].rstrip("\n").split(" — ", 1)[-1] for b in moved]
    verb = "would move" if args.dry_run else "moved"
    print(
        f"{verb} {len(moved)} block(s) to {args.history.name}, keeping {len(keep_blocks)} live "
        f"({len(plan)} -> {len(new_plan)} plan lines):"
    )
    for title in moved_titles:
        print(f"  - {title[:88]}")

    if not args.dry_run:
        # This is a *move*: a partial write (handoff doc trimmed but history write
        # fails) would drop the moved blocks. Write the handoff doc, then the
        # history doc; if the history write fails, roll the handoff doc back so
        # nothing is lost.
        original_plan = "".join(plan)
        try:
            args.plan.write_text("".join(new_plan), encoding="utf-8")
            try:
                args.history.write_text("".join(new_history), encoding="utf-8")
            except OSError:
                args.plan.write_text(original_plan, encoding="utf-8")
                raise
        except OSError as exc:
            print(f"error: write failed ({exc}); no changes applied", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
