from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.inbox import exact_sweep, parse  # noqa: E402
from triage.model import TriageError  # noqa: E402


def test_mixed_section_keeps_unaccounted_entry() -> None:
    raw = b"# Log\n\n## 2026-01-02\n\n- **Already done.** details\n  **Filed 2026-01-02 as #1.**\n\n- **Still active.** parked.\n"
    candidates = parse(raw)
    assert [candidate.raw for candidate in candidates] == [b"- **Still active.** parked.\n"]


def test_accounting_words_inside_an_entry_are_not_substring_authority() -> None:
    raw = b'# Log\n\n## 2026-01-02\n\n- **Parser bug.** The quoted example says "**Filed someday**" but no filing happened.\n'
    assert len(parse(raw)) == 1


def test_exact_sweep_uses_parsed_boundaries_and_preserves_same_date_addition() -> None:
    frozen_raw = b"# Log\n\n## 2026-01-02\n\n- **First.** body\n"
    frozen = parse(frozen_raw)
    current = b"# Log\n\n## 2026-01-02\n\n- **First.** body\n- **New.** later\n"
    active, archive = exact_sweep(current, frozen, {"TRI-01"})
    assert b"- **New.** later" in active
    assert b"- **First.** body" not in active
    assert archive == b"## 2026-01-02\n\n- **First.** body\n"


def test_matching_excerpt_inside_changed_block_is_not_a_sweep_match() -> None:
    frozen = parse(b"# Log\n\n## 2026-01-02\n\n- **First.** body\n")
    current = b"# Log\n\n## 2026-01-02\n\n- **Changed.** quote follows:\n  - **First.** body\n"
    with pytest.raises(TriageError, match="changed or is ambiguous"):
        exact_sweep(current, frozen, {"TRI-01"})
