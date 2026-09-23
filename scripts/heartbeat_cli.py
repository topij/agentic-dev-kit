#!/usr/bin/env python3
"""Record the local heartbeat of an engine-backed systemize run.

``start`` before the fetch; ``tick --step NAME`` after the digest and after each
analysis slice (``--slice i/n``), passing ``--run-identity-digest`` once the
fetch has printed it; ``complete --reason complete|error`` as the final write.
A failed ``complete`` exits non-zero: the workflow then marks the run incomplete.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from systemize.cli import Parser, add_run_arguments, main  # noqa: E402
from systemize.heartbeat import REASONS, Heartbeat  # noqa: E402


def parser() -> Parser:
    result = Parser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True, parser_class=Parser)
    add_run_arguments(commands.add_parser("start"))
    tick = commands.add_parser("tick")
    add_run_arguments(tick)
    tick.add_argument("--step", required=True)
    tick.add_argument("--slice", dest="slice_text", metavar="I/N")
    tick.add_argument("--run-identity-digest")
    complete = commands.add_parser("complete")
    add_run_arguments(complete)
    complete.add_argument("--reason", required=True, choices=REASONS)
    return result


def action(args, settings):
    heartbeat = Heartbeat(settings, mode=args.mode, window_days=args.window_days, date=args.date)
    if args.command == "start":
        return heartbeat.start()
    if args.command == "tick":
        return heartbeat.tick(args.step, args.slice_text, args.run_identity_digest)
    return heartbeat.complete(args.reason)


if __name__ == "__main__":
    sys.exit(main(parser(), action))
