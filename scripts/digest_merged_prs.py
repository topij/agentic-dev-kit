#!/usr/bin/env python3
"""Normalize a systemize raw bundle into the capped review-finding digest.

With ``--verify PATH`` it writes nothing: it recomputes the ordered capped
evidence, cap disclosure and derived batching fields from the raw bundle and
exits 1 if the digest at PATH — engine-built or agent-built — disagrees.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from systemize.cli import Parser, add_run_arguments, main  # noqa: E402
from systemize.digest import run  # noqa: E402


def parser() -> Parser:
    result = Parser(description=__doc__)
    add_run_arguments(result)
    result.add_argument("--verify", type=Path, metavar="PATH", help="check an existing digest instead of writing one")
    return result


def action(args, settings):
    return run(
        settings, mode=args.mode, window_days=args.window_days, date=args.date, verify_path=args.verify
    )


if __name__ == "__main__":
    sys.exit(main(parser(), action))
