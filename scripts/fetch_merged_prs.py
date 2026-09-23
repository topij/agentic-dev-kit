#!/usr/bin/env python3
"""Fetch every merged pull request in a systemize window into the raw bundle.

Invoked by the post-merge-systemize workflow in engine-backed mode, after the
heartbeat ``start``. Exit 0 prints a JSON envelope naming the written bundle;
exit 1 is a hard stop; exit 2 is a rejected invocation.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from systemize.cli import Parser, add_run_arguments, main  # noqa: E402
from systemize.fetch import run  # noqa: E402
from systemize.forge import GitHubReader  # noqa: E402


def parser() -> Parser:
    result = Parser(description=__doc__)
    add_run_arguments(result)
    return result


def action(args, settings):
    return run(
        settings, GitHubReader(settings.root), mode=args.mode, window_days=args.window_days, date=args.date
    )


if __name__ == "__main__":
    sys.exit(main(parser(), action))
