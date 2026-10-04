"""Controlled triage policy shipped with the installed tests."""

from __future__ import annotations

import json
from pathlib import Path


def triage_config_text() -> str:
    # The recorded config fixture travels with the tests. Host paths, branch
    # spelling, tracker destination and reviewer policy do not own test setup.
    fixture = Path(__file__).parent / "fixtures/init-config.json"
    return "".join(json.loads(fixture.read_text(encoding="utf-8")))
