#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Warn-only tripwire: nudge a memory-index review when Claude Code's agent
memory grows too large.

Claude Code's own per-project auto-memory index (``MEMORY.md`` — one pointer
line per saved memory) is loaded into context at every session start. Past a
size limit the loader **truncates** it — the oldest/least-relevant index
lines silently fall out of context, so a real memory becomes unrecallable.
``docs/handoff.md`` and ``docs/friction-log.md`` get a line-count budget
tripwire from ``check_doc_budget.py`` (Principle #1 in ``PRINCIPLES.md``);
this is the analogous guard for the memory index — the Claude-runtime
counterpart, since this artifact is Claude Code-specific and has no Codex
equivalent.

Two signals, mirroring ``check_doc_budget.py``:

* **Total size** vs a byte budget set just under the observed SessionStart
  load limit, so the warning fires while there's still room to act rather
  than after lines have already been dropped.
* **Per-line length** — any index pointer over ~200 chars. The index is meant
  to be one terse "[Title](file.md) — hook" line each; an over-long line is a
  hook that should be tightened (or the memory pruned). These also
  disproportionately eat the byte budget.

**Warn-only by design** — always exits 0 (a SessionStart hook should *nudge*,
never block). ``--strict`` makes it exit 1 when over budget (soft CI signal).

Why this isn't driven by ``config/dev-model.yaml``'s ``doc_budgets`` list
(unlike ``check_doc_budget.py``): that list is iterated unconditionally by
``check_doc_budget.py`` — every entry's ``path`` is resolved relative to the
repo root and required to exist, with mandatory ``archive``/``remedy``
fields. The memory index lives *outside* the repo at a path keyed by this
machine's Claude Code config dir and this repo's absolute path (not portable
across clones/machines, and not swept to an in-repo archive file), so adding
it as a ``doc_budgets`` entry would make every ``check_doc_budget.py`` run
fail loudly with "configured doc not found" wherever no memory has been
saved yet — including the very SessionStart hook this check itself rides
alongside. The byte/line-length budgets below are therefore kept as
documented platform constants (overridable via ``--max-bytes`` /
``--max-line-chars``), the same way ``check_doc_budget.py`` keeps its own
`MAX_BYTES`-equivalent tuning out of adopter config. ``scripts/lib/kitconfig``
is still reused, for the one thing that *is* config-shaped here: portable
repo-root discovery (walking up for ``.git`` rather than assuming a fixed
``scripts/<script>.py`` depth), so the repo-slug this script derives stays
correct even when the kit is vendored under a nested `paths.engines` dir.

The memory dir lives **outside the repo**, at
``${CLAUDE_CONFIG_DIR:-~/.claude}/projects/<repo-slug>/memory/MEMORY.md``
where ``<repo-slug>`` is the repo's absolute path with every non-alphanumeric
char replaced by ``-`` (Claude Code's own project-dir naming).
``--memory-file`` overrides this (tests, other machines).

Usage:

    python3 scripts/check_memory_budget.py            # report
    python3 scripts/check_memory_budget.py --quiet     # print only when over budget (the hook)
    python3 scripts/check_memory_budget.py --strict    # exit 1 when over budget
    python3 scripts/check_memory_budget.py --json       # machine-readable

Exit codes:
    0 — always (warn-only), unless ``--strict`` and over budget.
    2 — usage error (MEMORY.md not found at the resolved path).

Stdlib-only and ~milliseconds so it is safe to run from a SessionStart hook.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import repo_root  # noqa: E402

# Discover the repo root by walking up for a `.git` marker (via kitconfig)
# rather than assuming a fixed `scripts/<script>.py` depth — so the derived
# repo-slug (below) stays correct when the kit is vendored under a nested
# dir (e.g. scripts/devkit/).
REPO_ROOT = repo_root()

# Budget sits just under the observed SessionStart load limit so the warning
# fires with headroom to act (≈10+ memories) before truncation, not after. A
# tuning constant for a dev-tool feature — documented here, not in config
# (see module docstring for why this isn't a `doc_budgets` entry).
MAX_BYTES = 24_000
# The index is one terse pointer line per memory; over ~200 chars means an
# over-long hook to tighten (or a memory to prune).
MAX_LINE_CHARS = 200


def default_memory_file() -> Path:
    """Resolve MEMORY.md from the repo slug (Claude Code's project-dir naming).

    ``<repo-slug>`` is the repo's absolute path with every non-alphanumeric char
    replaced by ``-`` — e.g. ``/home/u/agentic-dev-kit`` -> ``-home-u-agentic-dev-kit``.
    """
    config_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
    slug = re.sub(r"[^a-zA-Z0-9]", "-", str(REPO_ROOT))
    return config_dir / "projects" / slug / "memory" / "MEMORY.md"


@dataclass(frozen=True)
class MemoryStatus:
    path: str
    size_bytes: int
    line_count: int
    max_bytes: int
    max_line_chars: int
    long_lines: list[tuple[int, int]]  # (1-based line number, length) for over-long lines

    @property
    def over_size(self) -> bool:
        return self.size_bytes > self.max_bytes

    @property
    def over(self) -> bool:
        return self.over_size or bool(self.long_lines)


def evaluate(memory_file: Path, *, max_bytes: int = MAX_BYTES, max_line_chars: int = MAX_LINE_CHARS) -> MemoryStatus:
    """Measure MEMORY.md against the byte budget + per-line length budget.

    Raises ``FileNotFoundError`` if the index is missing at ``memory_file``.
    """
    if not memory_file.is_file():
        raise FileNotFoundError(f"memory index not found: {memory_file}")
    text = memory_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    long_lines = [(i, len(line)) for i, line in enumerate(lines, start=1) if len(line) > max_line_chars]
    return MemoryStatus(
        path=str(memory_file),
        size_bytes=len(text.encode("utf-8")),
        line_count=len(lines),
        max_bytes=max_bytes,
        max_line_chars=max_line_chars,
        long_lines=long_lines,
    )


def render(status: MemoryStatus, *, quiet: bool) -> str:
    """Human-readable report. When ``quiet`` only print if over budget."""
    if not status.over:
        return (
            ""
            if quiet
            else f"✓ MEMORY.md {status.size_bytes / 1000:.1f} KB / {status.line_count} lines (budget ~{status.max_bytes / 1000:.0f} KB)"
        )
    lines: list[str] = []
    if status.over_size:
        lines.append(
            f"⚠ MEMORY.md is {status.size_bytes / 1000:.1f} KB (budget ~{status.max_bytes / 1000:.0f} KB) — "
            f"approaching the SessionStart load limit; a review/prune pass over the oldest or "
            f"least-relevant memories is overdue."
        )
    if status.long_lines:
        shown = ", ".join(f"L{n} ({length}c)" for n, length in status.long_lines[:5])
        more = "" if len(status.long_lines) <= 5 else f" (+{len(status.long_lines) - 5} more)"
        lines.append(
            f"⚠ {len(status.long_lines)} index line(s) over {status.max_line_chars} chars: {shown}{more} — "
            f"tighten the hook (or prune the memory)."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 (warn-only), 1 (``--strict`` and over), or 2 (missing file)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-file", type=Path, default=None, help="MEMORY.md path (default: repo-slug-derived).")
    parser.add_argument("--quiet", action="store_true", help="print nothing when under budget (for the hook).")
    parser.add_argument("--strict", action="store_true", help="exit 1 when over budget.")
    parser.add_argument("--json", action="store_true", help="machine-readable output.")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES, help=f"byte budget (default {MAX_BYTES}).")
    parser.add_argument(
        "--max-line-chars", type=int, default=MAX_LINE_CHARS, help=f"per-line char budget (default {MAX_LINE_CHARS})."
    )
    args = parser.parse_args(argv)
    if args.max_bytes <= 0 or args.max_line_chars <= 0:
        parser.error("--max-bytes and --max-line-chars must be positive integers")

    memory_file = args.memory_file.resolve() if args.memory_file else default_memory_file()
    try:
        status = evaluate(memory_file, max_bytes=args.max_bytes, max_line_chars=args.max_line_chars)
    except (OSError, UnicodeDecodeError) as exc:
        # FileNotFoundError (missing index) is the common case, but a permission
        # or decode error must also exit 2 cleanly rather than traceback — this
        # runs from a SessionStart hook.
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "path": status.path,
                    "size_bytes": status.size_bytes,
                    "line_count": status.line_count,
                    "max_bytes": status.max_bytes,
                    "over_size": status.over_size,
                    "long_lines": status.long_lines,
                    "over": status.over,
                }
            )
        )
    else:
        report = render(status, quiet=args.quiet)
        if report:
            print(report)

    return 1 if (args.strict and status.over) else 0


if __name__ == "__main__":
    raise SystemExit(main())
