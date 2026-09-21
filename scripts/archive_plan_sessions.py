#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
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

Fenced Markdown examples and HTML block comments are content, including their
literal headings and separators. Their openers must start at the beginning of a
line, outside lists and quotes, and close before the end of the document.
Unterminated literal blocks are refused before writes so they cannot absorb
existing history entries. Indented or container-prefixed literal markers
outside an existing literal block are unsupported and refused before writes.
Lines starting with raw HTML tags, declarations
or processing instructions outside those contexts are unsupported: enclose them
in a fenced code block before archiving. The sweep refuses them before writes.
Handoff and history must name distinct files; overlapping destinations are refused
before a sweep or dry-run can report success.

It only ever *moves* content — every cross-reference (ticket ids, PR links,
commit shas, …) is preserved. Standing sections (Security, Next up, Backlog,
…) below the session region are left untouched. Running it when there is
nothing to move is a clean no-op.

**One documented exception to "moves", and it is not byte-for-byte: the sweep
NORMALISES LINE ENDINGS.** Both documents are read and written as text with
universal newlines, so a CRLF or classic-Mac (lone CR) document comes back with
every line ending as ``\\n`` — the whole file, not only the blocks that moved
(issue #162). This is deliberate rather than an accident of the default
``newline`` argument — ``main()`` passes ``newline="\\n"`` explicitly, since
``newline=None`` writes ``os.linesep`` and would be LF here only because this is
POSIX. **A test pins the normalisation; nothing pins the explicitness**, because
the two are indistinguishable on a POSIX host, and that test says so in its own
docstring. The reasons for choosing to normalise:

* These are Markdown documents the kit itself writes — ``init.sh`` renders them
  from ``docs/templates/`` with ``\\n``, and every other kit tool reads them as
  text — so ``\\n`` is already the repo's convention rather than a choice made
  here.
* ``budget_line_count`` (below) requires already-translated text, so the *read*
  must stay universal-newline for this tool and ``check_doc_budget`` to measure
  a "line" identically. Strictly that settles the read side only — the counter
  never sees written bytes — but a tool that read translated and wrote raw could
  not round-trip its own document, so the write side follows from it.
* The diff noise a whole-file rewrite causes is bounded wherever a repo sets a
  ``.gitattributes eol=`` policy or ``core.autocrlf``, since the index then
  holds ``\\n`` either way. **Neither is configured in this repo** — checked, not
  assumed — so a CRLF handoff swept *here* would produce exactly that whole-file
  diff. The mitigation is available to an adopter; it is not in force by default,
  and this bullet previously implied it was.

What the sweep does **not** do is drop characters it does not recognise. A line
whose only content is an exotic character used to be discarded by the
trailing-blank strip, because a bare ``str.strip()`` removes much more than
layout whitespace — ``\\v \\f \\x1c \\x1d \\x1e \\x1f \\x85 \\xa0`` and the
U+2000-range spaces among them. So a lone file separator vanished out of a swept
block, and so did a non-breaking space, which is not a control character at all.
The two places that decide a line is blank *within a block* — the trailing strip
and ``_is_sep`` — now strip ``_LAYOUT_WS`` and nothing else.
``insert_into_history`` still uses a bare ``strip()``, deliberately: it only
advances a cursor to find an insertion point and drops nothing.

Usage:

    uv run scripts/archive_plan_sessions.py                  # keep 6, apply
    uv run scripts/archive_plan_sessions.py --keep 5
    uv run scripts/archive_plan_sessions.py --target-lines <budget>  # sweep to a line budget
    uv run scripts/archive_plan_sessions.py --dry-run         # report only
    uv run scripts/archive_plan_sessions.py --plan docs/handoff.md --history docs/handoff-history.md

``--keep`` and ``--target-lines`` are mutually exclusive. ``check_doc_budget.py``
measures the handoff doc in *lines*; this script's ``--keep`` counts *blocks* — so
a block-count remedy can be a no-op against a line budget (fewer blocks than the
``--keep`` floor, yet still over on lines). ``--target-lines`` closes that gap: it
sweeps oldest-first, one block at a time, until the doc is at or under the target,
and never sweeps the last remaining block. Its line count is
``budget_line_count`` — deliberately the same physical-line rule
``check_doc_budget`` uses. If it runs out of sweepable blocks while still
over the target, it fails loudly (exit **3**) rather than reporting success — a
step that did not accomplish what it was asked must say so.

Exit codes:
    0 — applied, or nothing to do, or a dry-run that would have succeeded.
        NOT every dry-run: ``--dry-run`` still reports 3 for an unreachable
        ``--target-lines``, because reachability is decided before the dry-run
        branch. That is the point — a dry-run exists to report what the real run
        would do.
    2 — every other failure: usage error, unresolvable configured paths, missing
        file, a file that cannot be read (unreadable or not valid UTF-8),
        unparseable handoff structure, history doc with no session-log section,
        a refused write, or a failed one.

        **A failed write reports the observed recovery state.**
        Neither document is ever opened for truncation: each is published by
        renaming a fully-written temporary file over it, and both are written
        before either is published (issue #164 — ``Path.write_text`` truncates
        first, and a 26,807-byte handoff was measured going to 0 bytes under
        ENOSPC while this tool printed "no changes applied").

        Restoration confirmation reads the staged handoff destination and checks
        that the argument still resolves there. If either check fails, the run
        warns instead of claiming restoration. It names the arguments, staged
        destinations and affected blocks' **titles** to guide recovery inspection.
        The warning does not establish that those blocks are absent from either
        document. Content allocation and writing finish during staging;
        publication and rollback renames can still fail for space or I/O errors.

        When a committed version is available, recovery guidance names its
        repository and complete relative path in a quoted read-only command.
        Otherwise it directs inspection of saved copies without promising Git
        recovery. Committed content does not include uncommitted edits.

        A *refused* write is different from a failed one and is worded
        differently: the sweep declines to publish over a read-only or
        hardlinked document, because replacement could bypass the write
        restriction while preserving mode bits, or silently orphan an alias. See
        ``lib/atomic_write.py`` for the full list and for why the exception is
        not an ``OSError``.

        **Two trades, both real costs, stated rather than discovered:**

        1. Publishing by rename needs room for the new content *beside* the old,
           where truncating first frees the old blocks. A sweep on a nearly-full
           disk can now fail where it once succeeded. Deliberate — a sweep that
           "succeeds" by destroying the archive it writes to is not a remedy —
           but an out-of-space handoff now needs space freed before the sweep
           that would shrink it can run.
        2. A rename needs a writable *directory*, where a write needed only a
           writable file. A document that is writable inside a read-only
           directory could be swept before and cannot now. There is no way to
           publish atomically without it.
    3 — ``--target-lines`` specifically: the target cannot be reached without
        sweeping the last remaining block, or there is no block to sweep at all.
        Distinct from 2 so a caller can tell this apart from the unrelated
        failures above without parsing the message; anything reading only
        "non-zero" would report all of them as an exhausted sweep.

    130 — interrupted (``KeyboardInterrupt``), the shell's usual 128+SIGINT.
        The publication handlers attempt recovery for interrupts they catch
        during the guarded commit calls, then re-raise. Their diagnostics
        describe the recovery state they could establish.

        These handlers do not cover every instruction boundary around
        publication. An interrupt outside their protected calls can escape
        without recovery guidance after the handoff was swept but before the
        history received its blocks. Surviving staged copies may be needed.

        **Exit 130 and an absent recovery message establish neither restoration
        nor an untouched document.** Preserve both documents and any surviving
        staged copies, read any diagnostic above the traceback, and inspect the
        content before retrying. Do not discard uncommitted edits with checkout.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shlex
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from atomic_write import AtomicWriteRefused, stage_text  # noqa: E402
from kitconfig import load_config, repo_root, resolve_path  # noqa: E402

REPO_ROOT = repo_root()


def budget_line_count(text: str) -> int:
    """Count lines the way ``check_doc_budget.py`` counts them.

    The two tools MUST agree: ``--target-lines`` is the first path to compare a
    count against ``check_doc_budget``'s number, so a disagreement means the sweep
    can refuse a target that is genuinely achievable.

    ``check_doc_budget`` counts by iterating an open text handle.
    ``str.splitlines()`` breaks
    on ``\\v \\f \\x1c \\x1d \\x1e \\x85 \\u2028 \\u2029`` as well, so a doc
    containing any of those measures LONGER under ``splitlines()`` than in the
    budget.

    **Precondition, and it is the caller's:** ``text`` must already have had
    universal-newline translation applied — i.e. come from ``read_text()`` /
    ``open()`` in text mode, which turns ``\\r`` and ``\\r\\n`` into ``\\n``. This
    function splits on ``\\n`` alone, so it does NOT reproduce a text handle's
    count for untranslated bytes: on raw ``a\\rb\\rc\\n`` a handle sees 3 lines and
    this sees 1. Reading with ``newline=""`` anywhere upstream breaks parity by
    one line per CR, and ``test_line_counters_agree_on_exotic_separators`` covers
    both classes so that change fails there rather than in the field.

    Pinned by that test, which also asserts the naive ``len(splitlines())`` form
    genuinely disagrees, so it cannot pass vacuously.
    """
    count = text.count("\n")
    # A trailing fragment with no final newline is still a line to both counters.
    return count if text.endswith("\n") or not text else count + 1


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
_RECENT_SESSION_RE = re.compile(r"^### \d{4}-\d{2}-\d{2}\b")


def history_pointer(link: str, label: str) -> list[str]:
    return [
        f"> Older session entries (below the live blocks above) live in [`{label}`]({link}).\n",
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


# Whitespace a Markdown document treats as layout, and the ONLY characters this
# module may strip when deciding a line is blank. `str.strip()` with no argument
# also removes \x1c \x1d \x1e \x85 \v \f — so `"\x1c".strip() == ""`, and the
# trailing-strip in `parse_blocks` silently dropped a lone file separator out of
# a swept block (issue #162). A sweep is an archival move; a character it does
# not recognise is content, not layout.
_LAYOUT_WS = " \t\r\n"


def _is_sep(line: str) -> bool:
    stripped = line.strip(_LAYOUT_WS)
    return len(stripped) >= 3 and set(stripped) in ({"_"}, {"-"})


def _outside_fences(lines: list[str]) -> list[bool]:
    """Identify structural physical lines outside fences and HTML block comments."""
    outside: list[bool] = []
    fence = ""
    comment = False
    for line in lines:
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            outside.append(False)
            if (
                match
                and match[1][0] == fence[0]
                and len(match[1]) >= len(fence)
                and not match[2].strip(" \t")
            ):
                fence = ""
        elif comment:
            outside.append(False)
            comment = "-->" not in line
        else:
            # Container termination needs a full Markdown parser. Refuse literal
            # openers with indentation or list/quote prefixes instead of letting
            # an indented closer hide the next standing section. Do this only
            # outside a top-level literal block: its examples remain content.
            content = line.lstrip(" \t")
            while prefix := re.match(r"(?:>[ \t]*|[-+*][ \t]+|[0-9]{1,9}[.)][ \t]+)", content):
                content = content[prefix.end():].lstrip(" \t")
            if content != line and re.match(r"(?:`{3,}|~{3,}|<!--)", content):
                raise ValueError(
                    "unsupported literal block opener; put fences and HTML block "
                    "comments at the start of a line outside lists and quotes "
                    "before archiving"
                )
            if line.startswith("<!--"):
                # Fence spellings inside an HTML block comment are literal, and
                # comment spellings inside a fence cannot outlive that fence.
                outside.append(False)
                comment = "-->" not in line
            elif re.match(r"^ {0,3}<(?:/?[A-Za-z][A-Za-z0-9-]*(?:[\s\ufeff/>]|$)|[!?])", line):
                # Renderer whitespace includes Unicode spaces and BOM; a tag
                # must not reveal fence spellings that its HTML block keeps literal. Refuse
                # unsupported input before it can hide standing content.
                raise ValueError(
                    "unsupported raw HTML tag line; wrap HTML in a fenced code block "
                    "before archiving"
                )
            elif match and (match[1][0] == "~" or "`" not in match[2]):
                fence = match[1]
                outside.append(False)
            else:
                outside.append(True)
    if fence or comment:
        # Prepending an unfinished literal would absorb existing history entries.
        # Closing it on the caller's behalf would change the moved content.
        raise ValueError("unterminated literal block; close fences and HTML block comments before archiving")
    return outside


def split_plan(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return ``(head, session_region, tail)``.

    ``head`` runs up to the first session heading; ``session_region`` covers the
    session blocks plus any inter-block separators and the existing pointer;
    ``tail`` is the first non-session ``##`` heading (standing sections) onward.
    """
    outside = _outside_fences(lines)
    sess_start = next(
        (i for i, ln in enumerate(lines) if outside[i] and _is_session_heading(ln)), None
    )
    if sess_start is not None:
        standing = next(
            (
                i
                for i, ln in enumerate(lines)
                if i > sess_start
                and outside[i]
                and ln.startswith("## ")
                and not _is_session_heading(ln)
            ),
            len(lines),
        )
        return lines[:sess_start], lines[sess_start:standing], lines[standing:]

    recent_start = next(
        (i for i, ln in enumerate(lines)
         if outside[i] and ln.rstrip("\n") == RECENT_SESSIONS_HEADING),
        None,
    )
    if recent_start is None:
        raise ValueError(
            "no session blocks or '## Recent sessions' section found in handoff doc"
        )
    standing = next(
        (i for i, ln in enumerate(lines)
         if i > recent_start and outside[i] and ln.startswith("## ")),
        len(lines),
    )
    # Introductory prose belongs to the live section, not to an archived entry.
    # Start parsing at the first dated heading so parse_blocks cannot discard it.
    sess_start = next(
        (i for i in range(recent_start + 1, standing)
         if outside[i] and _RECENT_SESSION_RE.match(lines[i])),
        standing,
    )
    return (
        lines[:sess_start],
        lines[sess_start:standing],
        lines[standing:],
    )


def parse_blocks(region: list[str]) -> list[list[str]]:
    """Split the session region into per-block line lists, newest first.

    Trailing layout blanks and separators are stripped from each block.
    Quotations are content; main removes only the exact generated footer
    at the end of a classic session region before calling this parser.
    "Blank" means ``_LAYOUT_WS`` only — a line whose sole content is an exotic
    control character is kept, because this is a move and that character is
    content (issue #162).
    """
    blocks: list[list[str]] = []
    outside = _outside_fences(region)
    uses_recent_sections = not any(
        visible and _is_session_heading(line)
        for line, visible in zip(region, outside, strict=True)
    )

    def is_block_heading(line: str) -> bool:
        if uses_recent_sections:
            return bool(_RECENT_SESSION_RE.match(line))
        return _is_session_heading(line)

    cur: list[str] | None = None
    for line, visible in zip(region, outside, strict=True):
        if visible and is_block_heading(line):
            if cur is not None:
                blocks.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        blocks.append(cur)
    for block in blocks:
        visible = _outside_fences(block)
        while block and visible[-1] and (
            block[-1].strip(_LAYOUT_WS) == ""
            or _is_sep(block[-1])
        ):
            block.pop()
            visible.pop()
    return blocks


def demote(block: list[str]) -> list[str]:
    """Convert a handoff session block to a history-doc ``### <date>`` entry.

    Handles ``## Latest session — <date>``, ``## Earlier session — <date>``,
    ``## Session — <date>`` and bare dated ``## June 5 Fri (cont.) — …`` headings.
    Only the block's heading line matches; body lines pass through unchanged.
    """
    out: list[str] = []
    for i, line in enumerate(block):
        if i == 0:
            for prefix in ("## Earlier session — ", "## Latest session — ", "## Session — "):
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
    outside = _outside_fences(head)
    for i, line in enumerate(out):
        if outside[i] and line.startswith("Last updated:"):
            segments = line.rstrip("\n").split(" | ")
            if len(segments) > keep:
                out[i] = " | ".join(segments[:keep]) + "\n"
            break
    return out


def rebuild_plan(
    head: list[str],
    keep_blocks: list[list[str]],
    tail: list[str],
    keep: int,
    *,
    history_link: str = "handoff-history.md",
    history_label: str = "handoff-history.md",
) -> list[str]:
    """Reassemble the handoff doc from the trimmed head, kept blocks, fresh pointer, and tail."""
    # The head includes any recent-section introduction. The retained session
    # heading, rather than the head's last line, identifies the layout.
    if keep_blocks and _RECENT_SESSION_RE.match(keep_blocks[0][0]):
        body: list[str] = []
        for block in keep_blocks:
            body += block + ["\n", "---\n", "\n"]
        return head + body + tail

    head = trim_megaline(head, keep)
    body: list[str] = []
    for block in keep_blocks:
        body += block + ["\n", SEP, "\n"]
    body += history_pointer(history_link, history_label)
    return head + body + tail


def insert_into_history(history: list[str], moved: list[list[str]]) -> list[str]:
    """Insert demoted blocks at the top of a recognized history session section."""
    outside = _outside_fences(history)
    try:
        sl = next(
            i
            for i, ln in enumerate(history)
            if outside[i] and ln.rstrip("\n") in HISTORY_SECTION_HEADINGS
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
    prefix = history[:insert_at]
    if prefix and not prefix[-1].endswith("\n"):
        prefix[-1] += "\n"
    return prefix + chunk + history[insert_at:]


def _recovery_matches(target: Path, expected: str) -> bool:
    """Confirm regular-file text without waiting for a replaced FIFO's writer.

    These observations do not lock the destination or bound filesystem I/O.
    They prevent a special-file replacement from turning recovery into a
    blocking stream read, and refuse a pathname replaced after acquisition.
    """
    flags = os.O_RDONLY
    for name in ("O_NONBLOCK", "O_NOFOLLOW"):
        flag = getattr(os, name, None)
        if flag is None:
            raise OSError("safe recovery readback is unavailable")
        flags |= flag
    if not stat.S_ISREG(target.lstat().st_mode):
        raise OSError("recovery destination is not a regular file")
    # The path can change after lstat: nonblocking acquisition and fstat are
    # both needed before reading the opened object.
    fd = os.open(target, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("opened recovery destination is not a regular file")
        with os.fdopen(fd, "r", encoding="utf-8", newline=None, closefd=False) as stream:
            matches = stream.read(len(expected) + 1) == expected
        current = target.lstat()
        return (
            matches
            and stat.S_ISREG(current.st_mode)
            and (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino)
        )
    finally:
        os.close(fd)


def _recovery_hint(target: Path) -> str:
    """Offer a read-only command only for a confirmed committed document."""
    fallback = (
        "No committed Git version could be confirmed for the staged handoff. "
        "Inspect the named documents and any saved copies before restoring content."
    )
    try:
        root_result = subprocess.run(
            ["git", "-C", str(target.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        root = Path(root_result.stdout.rstrip("\n")).resolve()
        relative = target.relative_to(root).as_posix()
        object_name = f"HEAD:{relative}"
        entry = subprocess.run(
            ["git", "--literal-pathspecs", "-C", str(root), "ls-tree", "-z",
             "HEAD", "--", relative],
            capture_output=True, check=True, timeout=5,
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        )
        metadata, path = entry.stdout.rstrip(b"\0").split(b"\t", 1)
        # Git stores symlink targets as blobs too. Only a regular-file tree
        # entry establishes that `git show` reads document bytes here.
        if metadata.split()[0] not in (b"100644", b"100755") or path != os.fsencode(relative):
            return fallback
        kind = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-t", object_name],
            capture_output=True, text=True, check=True, timeout=5,
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        )
        if kind.stdout.strip() != "blob":
            return fallback
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt):
        return fallback
    command = shlex.join(["git", "-C", str(root), "show", object_name])
    return (
        "Read the committed handoff version with:\n\n"
        f"    {command}\n\n"
        "This reads committed content only; preserve uncommitted edits separately."
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: keep the newest ``--keep`` session blocks, archive the rest.

    ``--target-lines`` is the mutually-exclusive alternative: sweep oldest-first
    until the plan doc is at or under N lines, rather than a fixed block count.

    Exit codes are documented once, in the module docstring. Do not restate them
    here: a second copy has drifted from the first in three separate rounds of
    review on this function.
    """
    # RawDescriptionHelpFormatter, because `wrap-up.md` cites `--help` as the
    # authoritative exit-code list and the default formatter re-wraps
    # `description`, collapsing the bullets into inline `*` markers mid-paragraph
    # and running the numbered exit codes together into one block of prose.
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=None,
        help=f"live blocks to keep (default {DEFAULT_KEEP}; mutually exclusive with "
        "--target-lines)",
    )
    parser.add_argument(
        "--target-lines",
        type=int,
        default=None,
        help="sweep oldest-first, one block at a time, until the live handoff doc is "
        "at or under N lines (mutually exclusive with --keep)",
    )
    parser.add_argument("--plan", type=Path, default=None, help="living handoff doc")
    parser.add_argument(
        "--history", type=Path, default=None, help="handoff history/archive doc"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report only, write nothing"
    )
    args = parser.parse_args(argv)

    if args.plan is None or args.history is None:
        try:
            default_plan, default_history = configured_paths()
        # No `yaml.YAMLError` here: `configured_paths` resolves through
        # `kitconfig`, which is a hand-rolled parser with no PyYAML import (the
        # CI job "Engines must work without PyYAML" pins that). The name was a
        # leftover from before that migration, and because Python evaluates an
        # `except` tuple only when an exception actually arrives, it turned
        # EVERY failure on this path into `NameError: name 'yaml' is not
        # defined` — masking the real error in the very handler written to
        # report it clearly. Found by the ruff pass added in this change (F821).
        except (
            FileNotFoundError,
            KeyError,
            OSError,
            TypeError,
            ValueError,
        ) as exc:
            print(
                f"error: could not resolve configured handoff paths ({exc})",
                file=sys.stderr,
            )
            return 2
        args.plan = args.plan or default_plan
        args.history = args.history or default_history

    args.plan = args.plan if args.plan.is_absolute() else Path.cwd() / args.plan
    args.history = (
        args.history if args.history.is_absolute() else Path.cwd() / args.history
    )

    if args.keep is not None and args.target_lines is not None:
        print("error: --keep and --target-lines are mutually exclusive", file=sys.stderr)
        return 2

    target_lines: int | None = args.target_lines
    keep: int | None = None
    if target_lines is not None:
        if target_lines < 1:
            print("error: --target-lines must be >= 1", file=sys.stderr)
            return 2
    else:
        keep = args.keep if args.keep is not None else DEFAULT_KEEP
        if keep < 1:
            print("error: --keep must be >= 1", file=sys.stderr)
            return 2

    for path in (args.plan, args.history):
        if not path.is_file():
            print(f"error: not found: {path}", file=sys.stderr)
            return 2

    try:
        if args.plan.samefile(args.history):
            print("error: handoff and history destinations overlap; no changes applied",
                  file=sys.stderr)
            return 2
    except OSError as exc:
        print(f"error: could not compare document destinations ({exc})", file=sys.stderr)
        return 2

    # A read that fails is a documented exit 2, not an uncaught traceback.
    # BOTH classes, deliberately: `is_file()` above passes for a file that exists
    # and cannot be opened, so `PermissionError` reaches these lines just as a
    # cp1252 em-dash reaches them as `UnicodeDecodeError`. Catching only the
    # decode error left exit 1 producible while the module's exit-code contract
    # says 0/2/3 and `wrap-up.md` branches on 2 and 3 alone.
    # `check_memory_budget.py` already catches this exact pair for the same
    # reason; keep them in agreement.
    #
    # Read one at a time so the message can name WHICH document failed:
    # UnicodeDecodeError carries no filename, and `wrap-up.md`'s exit-2 branch
    # tells the operator to read this text and act on it.
    texts: list[str] = []
    for path in (args.plan, args.history):
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: could not read {path}: {exc}", file=sys.stderr)
            return 2
    # read_text already normalized CR/CRLF. Unicode/control separators within
    # a physical line are content, not a new place where a fence can open.
    plan = io.StringIO(texts[0]).readlines()
    history = io.StringIO(texts[1]).readlines()

    history_link = os.path.relpath(args.history, start=args.plan.parent).replace(
        os.sep, "/"
    )

    try:
        head, region, tail = split_plan(plan)
        pointer = history_pointer(history_link, args.history.name)
        # The classic writer owns this exact footer at the region boundary.
        # A quotation elsewhere, an edited footer, or a footer naming another
        # history destination is content and must survive the archival move.
        if (
            any(visible and _is_session_heading(line)
                for line, visible in zip(region, _outside_fences(region), strict=True))
            and region[-len(pointer):] == pointer
            and all(_outside_fences(region)[-len(pointer):])
        ):
            region = region[:-len(pointer)]
        blocks = parse_blocks(region)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if target_lines is not None:
        plan_lines = budget_line_count("".join(plan))
        if plan_lines <= target_lines:
            print(f"nothing to move: {plan_lines} line(s) <= --target-lines {target_lines}.")
            return 0
        if len(blocks) <= 1:
            # Both the 0-block and 1-block cases land here, and they need
            # different wording: with 0 blocks there is no "last live block" to
            # decline to sweep, and claiming one describes a document that does
            # not exist.
            reason = (
                "there are no session blocks to sweep"
                if not blocks
                else "its 1 remaining session block is never swept"
            )
            print(
                f"error: cannot reach --target-lines {target_lines}: {reason}. "
                f"Nothing was written; the doc is unchanged at {plan_lines} lines.",
                file=sys.stderr,
            )
            return 3

        # Sweep oldest-first, one block at a time (never the last remaining block —
        # range stops at len(blocks) - 1), breaking at the FIRST count that reaches
        # the target, which is therefore the smallest sweep that suffices.
        new_plan = keep_blocks = moved = None
        for moved_count in range(1, len(blocks)):
            keep_blocks = blocks[: len(blocks) - moved_count]
            moved = blocks[len(blocks) - moved_count :]
            new_plan = rebuild_plan(
                head,
                keep_blocks,
                tail,
                len(keep_blocks),
                history_link=history_link,
                history_label=args.history.name,
            )
            if budget_line_count("".join(new_plan)) <= target_lines:
                break

        if budget_line_count("".join(new_plan)) > target_lines:
            # Past tense would be wrong here: nothing has been written, and the
            # figures below describe the *rejected* candidate, not the file.
            print(
                f"error: cannot reach --target-lines {target_lines}: even sweeping "
                f"down to {len(keep_blocks)} live block(s) — the floor, since the "
                f"last block is never swept — would leave "
                f"{budget_line_count(''.join(new_plan))} lines. Nothing was "
                f"written; the doc is unchanged at {plan_lines} lines.",
                file=sys.stderr,
            )
            return 3
    else:
        if len(blocks) <= keep:
            print(f"nothing to move: {len(blocks)} session block(s) <= --keep {keep}.")
            return 0

        keep_blocks, moved = blocks[:keep], blocks[keep:]
        new_plan = rebuild_plan(
            head,
            keep_blocks,
            tail,
            keep,
            history_link=history_link,
            history_label=args.history.name,
        )

    try:
        new_history = insert_into_history(history, moved)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    moved_titles = [b[0].rstrip("\n").split(" — ", 1)[-1] for b in moved]
    # Figures in budget_line_count's units, not len(): these are read against
    # check_doc_budget's budget, so they have to be the same measure. Pinned by
    # test_report_figures_use_the_budget_counter_not_splitlines, which uses a doc
    # containing separators the two counters disagree about.
    # The verb is interpolated HERE, not left as a `{verb}` field for a later
    # `str.format()`. That earlier shape called `.format()` on a string containing
    # the swept session TITLES, so a heading with a brace in it — `… substituting
    # {budget} in the remedy`, which is exactly what this branch's own commits are
    # titled — raised KeyError/IndexError/ValueError AFTER both files were written:
    # exit 1 (a code nothing documents), no report, the move already on disk, and a
    # retry reporting "nothing to move". Session titles are DATA, never a template.
    verb = "would move" if args.dry_run else "moved"
    report = "\n".join(
        [
            f"{verb} {len(moved)} block(s) to {args.history.name}, "
            f"keeping {len(keep_blocks)} live "
            f"({budget_line_count(''.join(plan))} -> "
            f"{budget_line_count(''.join(new_plan))} plan lines):"
        ]
        + [f"  - {title[:88]}" for title in moved_titles]
    )

    if args.dry_run:
        print(report)
        return 0

    # The report is printed only AFTER a successful write, and never before one.
    # It used to be printed first, so a failed write emitted
    # "moved 2 block(s) ... (46 -> 33 plan lines)" and *then* an error, leaving a
    # past-tense success line on stdout describing a file that was never touched.
    #
    # This is a *move* across two documents, so it has two hazards, and they are
    # closed by two different properties of `atomic_write`:
    #
    #   1. A failed write must not destroy the document it was writing. Neither
    #      document is opened for truncation at all; each is published by
    #      renaming a fully-written temp over it (issue #164).
    #   2. A partial *move* — handoff trimmed, history write fails — would drop
    #      the swept blocks. So BOTH documents are staged first, and only when
    #      both are safely on disk is either published. Content allocation and
    #      writing happen before publication; the later directory updates can
    #      still fail for space or I/O errors.
    #
    # The rollback is staged UP FRONT, for the same reason. The previous attempt
    # at this (reverted from #160) rebuilt the original handoff from memory
    # *after* the history write failed — needing more free space, on the disk
    # that had just refused a smaller write, than the write it was undoing.
    # Staging it here avoids another full-content write during recovery.
    # The rollback rename itself can still fail.
    #
    # The plan is published FIRST. The order is load-bearing, not incidental:
    # publishing history first and failing on the plan would leave the blocks in
    # *both* files, and a re-run would append them to history a second time.
    original_plan = "".join(plan)
    staged = []
    preserve_recovery_staging = False
    try:
        try:
            # `newline="\n"` states the normalisation the docstring documents
            # instead of inheriting it from the platform. `newline=None` writes
            # `os.linesep`, which is LF here only because this is POSIX — the
            # claim above would have been true by accident and false on Windows.
            # Reading is still universal-newline, so the text reaching this point
            # already holds `\n` alone; this pins how it lands on disk.
            staged_plan = stage_text(args.plan, "".join(new_plan), newline="\n")
            staged.append(staged_plan)
            staged_history = stage_text(args.history, "".join(new_history), newline="\n")
            staged.append(staged_history)
            if staged_plan.target.samefile(staged_history.target):
                raise AtomicWriteRefused("handoff and history destinations overlap")
            # Reuse the destination selected for the sweep. Resolving the
            # argument again could stage recovery for a retargeted alias.
            staged_rollback = stage_text(staged_plan.target, original_plan, newline="\n")
            staged.append(staged_rollback)
            if staged_rollback.target != staged_plan.target:
                raise AtomicWriteRefused(
                    "the handoff rollback destination changed during staging"
                )
        except AtomicWriteRefused as exc:
            # Not an OSError and not phrased as one: nothing was attempted and
            # failed, the tool declined to publish this way. See atomic_write.
            print(f"error: refusing to write ({exc}); no changes applied", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"error: write failed ({exc}); no changes applied", file=sys.stderr)
            return 2

        plan_location = f"{args.plan} (staged destination {staged_plan.target})"
        history_location = f"{args.history} (staged destination {staged_history.target})"

        # BOTH publishes catch `BaseException`, and both ask the FILESYSTEM
        # whether the rename happened rather than inferring it from where the
        # exception was raised. Two review rounds got this wrong in two
        # different ways:
        #
        #   - Catching `OSError` here and `BaseException` only below fixed one
        #     of the two call sites. An interrupt during the *handoff* publish
        #     escaped, the `finally` unlinked the staged rollback, and the blocks
        #     were lost with no message at all — the same defect the round
        #     before had just fixed one line further down.
        #   - Trusting the exception's position is wrong even so: an interrupt
        #     can land after `os.replace` has returned, so a handler that assumes
        #     "raised here ⇒ not published" rolls back a *completed* move and
        #     leaves the blocks in BOTH documents, which a re-run then appends to
        #     the history a second time.
        #
        # `publish_state()` reads the temp's absence, which is evidence.
        #
        # ONE recovery routine serves both sites. Three separate review findings
        # were "the guard/message/test exists at one site and not the other", so
        # the duplication was the defect generator rather than any single miss.
        def restore_handoff(*, cause: BaseException) -> bool:
            """Put the handoff back; confirm its content before reporting success."""
            nonlocal preserve_recovery_staging
            rollback_error: BaseException | None = None
            try:
                staged_rollback.commit()
            except BaseException as exc:
                rollback_error = exc
            # A rename can land before raising, or a removed temp can falsely
            # suggest publication. Confirm the destination in either case.
            # A readback interrupt must not hide the original failure and the
            # recovery warning; it establishes uncertainty, not restoration.
            try:
                restored = _recovery_matches(staged_plan.target, original_plan)
                if args.plan.resolve(strict=True) != staged_plan.target:
                    confirmation = "argument no longer resolves to the staged destination"
                elif restored:
                    preserve_recovery_staging = False
                    return True
                else:
                    confirmation = "destination differs from the original handoff"
            except BaseException as exc:
                confirmation = f"could not read back the destination ({exc})"
            # Failed or unconfirmed restoration must not discard the remaining
            # pre-publication copies. Their paths may have vanished or changed;
            # leave them untouched without claiming their contents are verified.
            print(
                f"error: publishing failed ({cause}), AND restoration of "
                f"{plan_location} could not be confirmed ({confirmation}; "
                f"rollback error: {rollback_error!r}). These blocks "
                f"may be in NEITHER document. Inspect {plan_location} and {history_location}:\n"
                + "\n".join(f"  - {title[:88]}" for title in moved_titles)
                + "\nRecovery staging paths left untouched; existence and contents "
                "are unconfirmed:\n"
                f"  - staged history: {staged_history.temp}\n"
                f"  - original handoff: {staged_rollback.temp}\n"
                + _recovery_hint(staged_plan.target)
                + "\ndo NOT `git checkout`, which discards this session's own "
                "edits.",
                file=sys.stderr,
            )
            return False

        # Arm retention before publication can remove content from the handoff.
        # An interrupt between protected calls must not let final cleanup erase
        # the remaining recovery copies. Release only on a safe terminal path.
        preserve_recovery_staging = True
        try:
            staged_plan.commit()
        except BaseException as exc:
            plan_state = staged_plan.publish_state()
            if plan_state == "pending":
                preserve_recovery_staging = False
            # "unknown" is treated as published, and that is safe *here*: the
            # rollback writes the original bytes over a document that either was
            # swept (so it needs them) or was never touched (so they are what is
            # already there). At the history site the same ambiguity is not
            # symmetric, and is handled differently. Recovery diagnostics do
            # not turn this temporary-file observation into proof of a sweep.
            if plan_state in ("published", "unknown") and not restore_handoff(
                cause=exc
            ):
                if isinstance(exc, OSError):
                    return 2
                raise
            if isinstance(exc, OSError):
                print(f"error: write failed ({exc}); no changes applied", file=sys.stderr)
                return 2
            raise

        try:
            staged_history.commit()
        except BaseException as history_exc:
            history_state = staged_history.publish_state()
            if history_state == "published":
                # The temp's absence is only EVIDENCE that the rename happened —
                # anything else that removes it reads the same way, and a review
                # lens measured exactly that: temp removed externally, rename
                # failed, and this branch reported the move complete while the
                # blocks were in neither document. Here the destination itself
                # can be consulted, which settles it outright, so do that rather
                # than trust the proxy. An unreadable destination is not a
                # confirmation either, and falls through to `unknown`.
                try:
                    # Confirm the staged destination, not a newly resolved
                    # alias. These path observations do not lock directories
                    # against replacement by another writer.
                    landed = (
                        _recovery_matches(staged_history.target, "".join(new_history))
                        and args.history.resolve(strict=True) == staged_history.target
                    )
                except BaseException:
                    # Interrupted confirmation establishes uncertainty, not
                    # publication. Continue through validated restoration and
                    # preserve the original publication error below.
                    landed = False
                if not landed:
                    history_state = "unknown"
            if history_state == "published":
                # The rename DID happen and something after it failed. The move
                # is complete in both documents — restoring the handoff now is
                # precisely the duplication the plan-first ordering exists to
                # prevent, so leave both alone and report.
                #
                # Reaching here means the destination was read back and matches
                # what this run intended to write, so the claim below is checked
                # rather than inferred.
                # Printed for an interrupt too, not only an OSError: this is the
                # one path the code has already established is COMPLETE, and
                # exiting 130 in silence over it reads as "cancelled, nothing
                # happened" when the sweep in fact succeeded.
                preserve_recovery_staging = False
                print(
                    f"error: {history_location} was published — its content was "
                    f"read back and matches — but the step after it failed "
                    f"({history_exc}). The move is complete in both documents "
                    "and nothing needs restoring.",
                    file=sys.stderr,
                )
                if isinstance(history_exc, OSError):
                    return 2
                raise
            if not restore_handoff(cause=history_exc):
                if isinstance(history_exc, OSError):
                    return 2
                raise history_exc
            if history_state == "unknown":
                # The handoff is back, and whether the history also received the
                # blocks could not be determined. Restoring is the right side to
                # err on — duplicates are visible and fixable, blocks in neither
                # document are gone — but the operator has to be told to look.
                print(
                    f"error: publishing {history_location} failed ({history_exc}), and "
                    f"this run could not determine whether it landed. {plan_location} "
                    f"has been restored, so the blocks are definitely there — but "
                    f"CHECK {history_location} for duplicates of:\n"
                    + "\n".join(f"  - {title[:88]}" for title in moved_titles),
                    file=sys.stderr,
                )
                if isinstance(history_exc, OSError):
                    return 2
                raise
            if isinstance(history_exc, OSError):
                print(
                    f"error: publishing {history_location} failed ({history_exc}); "
                    f"{plan_location} was restored and no changes were applied. "
                    "Neither document holds a partial write; the handoff's bytes "
                    "are the text this run read, which for a CRLF document is its "
                    "normalised form (see the module docstring).",
                    file=sys.stderr,
                )
                return 2
            # Not an OSError — an interrupt. The handoff is back; let it out.
            raise
        else:
            preserve_recovery_staging = False
    finally:
        for item in staged:
            if preserve_recovery_staging and (
                item is staged_history or item is staged_rollback
            ):
                continue
            item.abort()

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
