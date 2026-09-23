"""Shared argument handling and exit-status discipline for the three engines.

Exit ``0`` prints one JSON envelope to stdout; ``1`` is a hard stop with one
stderr line naming the failed check; ``2`` is a rejected invocation, raised
before any preflight. The workflow treats the exit status as authoritative.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from datetime import date as Date
from typing import Any

from .config import Settings, load_settings
from .errors import SystemizeError, UsageError


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: D102 - argparse hook
        raise UsageError(f"invalid arguments: {message}")


def _date(text: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text!r}")
    try:
        Date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a calendar date: {text!r}") from exc
    return text


def _window(text: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", text):
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text!r}")
    return int(text)


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", required=True, choices=("live", "test"))
    parser.add_argument("--window-days", required=True, type=_window)
    parser.add_argument("--date", required=True, type=_date, help="selected run date, YYYY-MM-DD (UTC)")


def main(parser: argparse.ArgumentParser, action: Callable[[argparse.Namespace, Settings], dict[str, Any]],
         argv: list[str] | None = None) -> int:
    try:
        args = parser.parse_args(argv)
        settings = load_settings()
        if settings.engine_mode != "engine-backed":
            raise SystemizeError("configured engine set is not installed; this entry point cannot run alone")
        envelope = action(args, settings)
    except SystemizeError as exc:
        print(f"systemize: {'usage' if exc.exit_code == 2 else 'hard stop'}: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - every other failure is still a one-line hard stop
        print(f"systemize: hard stop: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(envelope, sort_keys=True))
    return 0
