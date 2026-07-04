#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Warn-only tripwire: nudge an archive sweep when a handoff doc grows too large.

The two cross-session handoff docs — ``docs/handoff.md`` (the living plan) and
``docs/friction-log.md`` (the friction inbox) — are meant to stay lean:
completed session logs belong in ``docs/handoff-history.md`` and
pre-graduation post-mortems in ``docs/friction-log-archive.md``. Left unswept
they balloon, which makes every session start more expensive and the handoff
harder to scan.

This check is **warn-only by design** — it always exits 0 (a SessionStart hook
or ``/wrap-up`` step should *nudge*, never block). Pass ``--strict`` to make it
exit 1 when over budget (e.g. if you ever want it as a soft CI signal).

The tracked docs + their budgets come from ``config/dev-model.yaml``'s
``doc_budgets`` list (``{path, budget, archive, remedy}``) — see
``scripts/lib/devmodel_config.py``. Adjust the budgets there, not here.

Usage:

    python3 scripts/check_doc_budget.py            # report every tracked doc
    python3 scripts/check_doc_budget.py --quiet     # print only when over budget
    python3 scripts/check_doc_budget.py --strict    # exit 1 when over budget
    python3 scripts/check_doc_budget.py --json       # machine-readable

Exit codes:
    0 — always (warn-only), unless ``--strict`` and at least one doc is over.
    2 — usage error (config missing/malformed, or a configured doc is missing).

~milliseconds so it is safe to run from a SessionStart hook.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from devmodel_config import _repo_root, get, load_config  # noqa: E402

# Discover the repo root by walking up for a `.git` marker (via devmodel_config)
# rather than assuming a fixed `scripts/<script>.py` depth — so this keeps working
# when the kit is vendored under a nested dir (e.g. scripts/devkit/).
REPO_ROOT = _repo_root()


@dataclass(frozen=True)
class DocStatus:
    path: str
    lines: int
    budget: int
    archive: str
    remedy: str

    @property
    def over(self) -> bool:
        return self.lines > self.budget


def _line_count(path: Path) -> int:
    """Count lines without slurping the whole file into one string."""
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _load_doc_budgets(config_path: Path) -> list[tuple[str, int, str, str]]:
    """Read ``doc_budgets`` from ``config/dev-model.yaml`` as (path, budget, archive, remedy) tuples."""
    config = load_config(config_path)
    budgets = get(config, "doc_budgets")
    if not isinstance(budgets, list) or not budgets:
        raise ValueError(f"'doc_budgets' in {config_path} must be a non-empty list")
    out: list[tuple[str, int, str, str]] = []
    for i, entry in enumerate(budgets):
        if not isinstance(entry, dict):
            raise ValueError(f"doc_budgets[{i}] must be a mapping, got {type(entry).__name__}")
        try:
            out.append((str(entry["path"]), int(entry["budget"]), str(entry["archive"]), str(entry["remedy"])))
        except KeyError as exc:
            raise ValueError(f"doc_budgets[{i}] missing required key {exc}") from exc
    return out


def evaluate(root: Path = REPO_ROOT, config_path: Path | None = None) -> list[DocStatus]:
    """Return a :class:`DocStatus` per configured doc. Raises if config or a doc is missing."""
    docs = _load_doc_budgets(config_path if config_path is not None else root / "config" / "dev-model.yaml")
    statuses: list[DocStatus] = []
    for rel, budget, archive, remedy in docs:
        target = root / rel
        if not target.is_file():
            raise FileNotFoundError(f"configured doc not found: {target}")
        statuses.append(DocStatus(rel, _line_count(target), budget, archive, remedy))
    return statuses


def render(statuses: list[DocStatus], *, quiet: bool) -> str:
    """Human-readable report. When ``quiet`` only over-budget docs are shown."""
    lines: list[str] = []
    for s in statuses:
        if s.over:
            lines.append(
                f"⚠ {s.path} is {s.lines} lines (budget ~{s.budget}) — an archive "
                f"sweep into {s.archive} is overdue: {s.remedy}."
            )
        elif not quiet:
            lines.append(f"✓ {s.path} {s.lines}/{s.budget} lines")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: report each handoff doc's line count against its budget.

    Returns 0 (warn-only), or 1 when ``--strict`` and a doc is over budget, or 2
    on a usage error (config missing/malformed, or a configured doc is missing).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print nothing when every doc is under budget (for the hook)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when at least one doc is over budget",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repo root (defaults to the script's repo)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="path to dev-model.yaml (defaults to <root>/config/dev-model.yaml)",
    )
    args = parser.parse_args(argv)

    try:
        statuses = evaluate(args.root, args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    any_over = any(s.over for s in statuses)

    if args.json:
        print(
            json.dumps(
                {
                    "any_over": any_over,
                    "docs": [
                        {
                            "path": s.path,
                            "lines": s.lines,
                            "budget": s.budget,
                            "over": s.over,
                        }
                        for s in statuses
                    ],
                }
            )
        )
    else:
        report = render(statuses, quiet=args.quiet)
        if report:
            print(report)

    return 1 if (args.strict and any_over) else 0


if __name__ == "__main__":
    raise SystemExit(main())
