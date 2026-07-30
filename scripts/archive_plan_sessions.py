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

It only ever *moves* content — every cross-reference (ticket ids, PR links,
commit shas, …) is preserved. Standing sections (Security, Next up, Backlog,
…) below the session region are left untouched. Running it when there is
nothing to move is a clean no-op.

**One documented exception to "moves", and it is not byte-for-byte: the sweep
NORMALISES LINE ENDINGS.** Both documents are read and written as text with
universal newlines, so a CRLF or classic-Mac (lone CR) document comes back with
every line ending as ``\\n`` — the whole file, not only the blocks that moved
(issue #162). This is deliberate rather than an accident of the default
``newline`` argument, and it is pinned by a test:

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
``budget_line_count`` — deliberately the same rule ``check_doc_budget`` uses, not
this module's ``splitlines()``. If it runs out of sweepable blocks while still
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

        **A failed write leaves both documents intact, and the message says so.**
        Neither document is ever opened for truncation: each is published by
        renaming a fully-written temporary file over it, and both are written
        before either is published (issue #164 — ``Path.write_text`` truncates
        first, and a 26,807-byte handoff was measured going to 0 bytes under
        ENOSPC while this tool printed "no changes applied").

        Exactly one branch cannot promise it, and it names both documents with
        the states it can actually vouch for: the handoff published, the history
        untouched, and the swept blocks listed so they can be recovered by hand.
        It is reachable only if a second ``os.replace`` fails after the first
        succeeded — allocation is finished by then, so the ordinary out-of-space
        route does not lead here.

        A *refused* write is different from a failed one and is worded
        differently: the sweep declines to publish over a read-only or
        hardlinked document, because replacing one by rename would succeed while
        deleting the read-only bit or silently orphaning the alias. See
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
"""

from __future__ import annotations

import argparse
import os
import re
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
    ``str.splitlines()`` — which this module uses for structural parsing — breaks
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


def split_plan(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return ``(head, session_region, tail)``.

    ``head`` runs up to the first session heading; ``session_region`` covers the
    session blocks plus any inter-block separators and the existing pointer;
    ``tail`` is the first non-session ``##`` heading (standing sections) onward.
    """
    sess_start = next(
        (i for i, ln in enumerate(lines) if _is_session_heading(ln)), None
    )
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
        (i for i, ln in enumerate(lines) if ln.rstrip("\n") == RECENT_SESSIONS_HEADING),
        None,
    )
    if recent_start is None:
        raise ValueError(
            "no session blocks or '## Recent sessions' section found in handoff doc"
        )
    standing = next(
        (i for i, ln in enumerate(lines) if i > recent_start and ln.startswith("## ")),
        len(lines),
    )
    # Keep the section heading in the head; parse_blocks handles its ``###``
    # entries and rebuild_plan preserves this layout without adding a pointer.
    return (
        lines[: recent_start + 1],
        lines[recent_start + 1 : standing],
        lines[standing:],
    )


def parse_blocks(region: list[str]) -> list[list[str]]:
    """Split the session region into per-block line lists, newest first.

    Trailing blank/separator/pointer (``>``) lines are stripped from each block,
    so the pointer the previous run wrote never gets absorbed into a block.
    "Blank" means ``_LAYOUT_WS`` only — a line whose sole content is an exotic
    control character is kept, because this is a move and that character is
    content (issue #162).
    """
    blocks: list[list[str]] = []
    uses_recent_sections = not any(_is_session_heading(line) for line in region)

    def is_block_heading(line: str) -> bool:
        if uses_recent_sections:
            return bool(_RECENT_SESSION_RE.match(line))
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
        while block and (
            block[-1].strip(_LAYOUT_WS) == ""
            or _is_sep(block[-1])
            or block[-1].startswith(">")
        ):
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
    if head and head[-1].rstrip("\n") == RECENT_SESSIONS_HEADING:
        body: list[str] = ["\n"]
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
    plan = texts[0].splitlines(keepends=True)
    history = texts[1].splitlines(keepends=True)

    try:
        head, region, tail = split_plan(plan)
        blocks = parse_blocks(region)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    history_link = os.path.relpath(args.history, start=args.plan.parent).replace(
        os.sep, "/"
    )

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
    #      both are safely on disk is either published. Everything that can fail
    #      for want of space or a bad sector now happens while nothing has been
    #      published and aborting costs nothing.
    #
    # The rollback is staged UP FRONT, for the same reason. The previous attempt
    # at this (reverted from #160) rebuilt the original handoff from memory
    # *after* the history write failed — needing more free space, on the disk
    # that had just refused a smaller write, than the write it was undoing.
    # Staging it here means the recovery path is an `os.replace` whose cost was
    # paid while failing was still free.
    #
    # The plan is published FIRST. The order is load-bearing, not incidental:
    # publishing history first and failing on the plan would leave the blocks in
    # *both* files, and a re-run would append them to history a second time.
    original_plan = "".join(plan)
    staged = []
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
            staged_rollback = stage_text(args.plan, original_plan, newline="\n")
            staged.append(staged_rollback)
        except AtomicWriteRefused as exc:
            # Not an OSError and not phrased as one: nothing was attempted and
            # failed, the tool declined to publish this way. See atomic_write.
            print(f"error: refusing to write ({exc}); no changes applied", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"error: write failed ({exc}); no changes applied", file=sys.stderr)
            return 2

        try:
            staged_plan.commit()
        except OSError as exc:
            print(f"error: write failed ({exc}); no changes applied", file=sys.stderr)
            return 2

        try:
            staged_history.commit()
        except BaseException as history_exc:
            # BaseException, not OSError. Between the two publishes the handoff
            # is swept and the history has not received the blocks, so ANY escape
            # here — `KeyboardInterrupt` above all, since `wrap-up` is
            # interactive — leaves them in neither document. Worse, the `finally`
            # below would then unlink the very copy staged to recover them: a
            # Ctrl-C destroyed data that a SIGKILL at the same instant survives,
            # because SIGKILL runs no handler. Restore first, re-raise after.
            try:
                staged_rollback.commit()
            except OSError as rollback_exc:
                # Never claim "no changes applied" when the rollback failed too.
                # Both remaining claims are ones this branch can actually make:
                # the history was published by rename or not at all, so it is
                # INTACT rather than part-written, and the handoff is the
                # already-swept document whose rollback did not land.
                #
                # The swept titles are listed bare. An earlier version appended
                # the whole `report`, whose header reads "moved N block(s) to
                # <history>" — a past-tense success line, inside the message
                # saying the move did not happen, and the exact string the
                # comment above records as removed in #160. Both lenses of the
                # review panel found it independently.
                print(
                    f"error: publishing {args.history} failed ({history_exc}), AND "
                    f"restoring {args.plan} failed ({rollback_exc}). "
                    f"{args.history} is unchanged and intact — it was never "
                    f"truncated — but {args.plan} has been swept, so these blocks "
                    f"are in NEITHER document:\n"
                    + "\n".join(f"  - {title[:88]}" for title in moved_titles)
                    + f"\nRestore {args.plan} from git before continuing.",
                    file=sys.stderr,
                )
                if isinstance(history_exc, OSError):
                    return 2
                raise
            if isinstance(history_exc, OSError):
                print(
                    f"error: publishing {args.history} failed ({history_exc}); "
                    f"{args.plan} was restored and no changes were applied. "
                    "Neither document holds a partial write; the handoff's bytes "
                    "are the text this run read, which for a CRLF document is its "
                    "normalised form (see the module docstring).",
                    file=sys.stderr,
                )
                return 2
            # Not an OSError — an interrupt. The handoff is back; let it out.
            raise
    finally:
        # `abort` on a committed write is a no-op, so this only ever removes
        # temps that were never published — including on the paths above that
        # return early, and on an unexpected exception. The rollback is committed
        # by the handler above BEFORE this runs, which is what stops it being
        # deleted at the one moment it is needed.
        for item in staged:
            item.abort()

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
