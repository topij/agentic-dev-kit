#!/usr/bin/env python3
"""Resume a triage session through accounting and exact finalization."""

from __future__ import annotations

import sys

from triage_friction_log import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if not arguments or arguments[0].startswith("-"):
        arguments = ["resume", *arguments]
    raise SystemExit(main(arguments))
