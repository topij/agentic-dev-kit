#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Resume a triage session through accounting and exact finalization."""

from __future__ import annotations

import sys

from triage_friction_log import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], default_entry="resume"))
