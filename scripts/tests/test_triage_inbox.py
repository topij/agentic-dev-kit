from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.finalize import render_sweep  # noqa: E402
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


def test_fenced_headings_entries_and_accounting_markers_are_literal_examples() -> None:
    raw = b'''# Log

```markdown
## 2026-01-01

- **Quoted fake.** not active
```

## 2026-01-02

- **Real entry.** body

  ~~~~markdown
  - **Nested quoted entry.** example
  **Filed:** example only
  ~~~~
'''
    candidates = parse(raw)
    assert [candidate.title for candidate in candidates] == ["2026-01-02"]
    assert len(candidates) == 1
    assert b"Nested quoted entry" in candidates[0].raw


def test_exact_sweep_preserves_fenced_examples_without_splitting_them_into_archive() -> None:
    raw = b'''# Log

```markdown
## 2026-01-01
- **Quoted fake.** not active
```

## 2026-01-02

- **Real entry.** body
'''
    candidates = parse(raw)
    active, archive = exact_sweep(raw, candidates, {"TRI-01"})
    assert b"Quoted fake" in active
    assert b"Quoted fake" not in archive
    assert archive == b"## 2026-01-02\n\n- **Real entry.** body\n"


def test_render_sweep_places_migration_marker_before_first_real_section() -> None:
    raw = b'''# Log

```markdown
## quoted heading
```

## 2026-01-02

- **Real entry.** body
'''
    candidates = parse(raw)
    marker = "## 2026-01-02 — migrated\n\n".encode()
    active, archive = render_sweep(
        raw,
        b"# Archive\n",
        candidates,
        {
            "operations": [],
            "decisions": [{"candidate_id": "TRI-01", "decision": "archive"}],
        },
        marker,
    )
    assert active.index(b"```markdown") < active.index(marker)
    assert active.index(b"```\n") < active.index(marker)
    assert b"quoted heading" in active
    assert b"quoted heading" not in archive
