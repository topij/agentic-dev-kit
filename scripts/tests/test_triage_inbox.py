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


def test_mixed_section_keeps_historically_annotated_and_open_entries() -> None:
    raw = b"# Log\n\n## 2026-01-02\n\n- **Already done.** details\n  **Filed 2026-01-02 as #1.**\n\n- **Still active.** parked.\n"
    candidates = parse(raw)
    assert [candidate.raw for candidate in candidates] == [
        b"- **Already done.** details\n  **Filed 2026-01-02 as #1.**\n\n",
        b"- **Still active.** parked.\n",
    ]


@pytest.mark.parametrize(
    "annotation",
    [
        b"**Filed 2026-01-02\n  as [#1](https://example.test/1), on approval.**",
        b"**Routed\n  2026-01-02 to\n  [#1](https://example.test/1) as an occurrence.**",
        b"**Reconciled 2026-01-02 under #1:** the prior filing accounts for it.",
    ],
)
@pytest.mark.parametrize("placement", [b"  {annotation}\n", b"Details complete.   {annotation}\n"])
def test_dated_accounting_annotations_remain_visible_across_hard_wrapping(
    annotation: bytes, placement: bytes
) -> None:
    raw = b"# Log\n\n## 2026-01-02\n\n- **Already done.** body\n" + placement.replace(
        b"{annotation}", annotation
    )
    assert [candidate.raw for candidate in parse(raw)] == [raw[raw.index(b"- **Already done."):]]


@pytest.mark.parametrize(
    "entry",
    [
        b"- **Parser bug.** The prior entry was handled. **Filed 2026-01-02 as #1** was its annotation, not ours.\n",
        b"- **Title.** Some text ends here. **Filed 2026-01-01 as** duplicate, but actually still open.\n",
        b"- **Parser bug.** We fixed it. **Filed 2026-01-02 as #1, on the operator go-ahead.**\n",
        b"- **Parser bug.** The phrase **Filed 2026-01-02 as #1** is discussed, not asserted.\n",
    ],
)
def test_submitted_accounting_regressions_remain_candidates(entry: bytes) -> None:
    other = b"- **Unrelated open entry.** Still needs triage.\n"
    raw = b"# Log\n\n## 2026-01-02\n\n" + entry + other
    assert [candidate.raw for candidate in parse(raw)] == [entry, other]


def test_accounting_words_inside_an_entry_are_not_substring_authority() -> None:
    raw = b'# Log\n\n## 2026-01-02\n\n- **Parser bug.** The quoted example says "**Filed someday**" but no filing happened.\n'
    assert len(parse(raw)) == 1


@pytest.mark.parametrize(
    "mention",
    [
        b'The quoted example says "**Filed 2026-01-02 as #1.**" but no filing happened.',
        b"The inline code says `Example. **Filed 2026-01-02 as #1.**` but records nothing.",
        b"The phrase **Reconciled 2026-01-02 under #1:** is discussed, not asserted.",
        b"The words Filed, Routed, and Reconciled are ordinary narrative.",
    ],
)
def test_accounting_words_and_inline_literals_are_not_annotation_authority(mention: bytes) -> None:
    raw = b"# Log\n\n## 2026-01-02\n\n- **Parser bug.** " + mention + b"\n"
    assert len(parse(raw)) == 1


def test_wrapped_inline_code_annotation_example_remains_active() -> None:
    raw = b'''# Log

## 2026-01-02

- **Parser bug.** The code says `Example.
  **Filed 2026-01-02 as #1.**` but records nothing.
'''
    assert len(parse(raw)) == 1


def test_inline_code_requires_equal_delimiters_and_ends_before_real_annotation() -> None:
    raw = b'''# Log

## 2026-01-02

- **Literal only.** The code says `prefix `` Example. **Filed 2026-01-02 as #1.**`.
- **Already done.** The code says `prefix `` Example. **Filed 2026-01-02 as #1.**`.
  Complete. **Routed 2026-01-02 to #1.**
'''
    candidates = parse(raw)
    assert [candidate.raw for candidate in candidates] == [
        b"- **Literal only.** The code says `prefix `` Example. **Filed 2026-01-02 as #1.**`.\n",
        b"- **Already done.** The code says `prefix `` Example. **Filed 2026-01-02 as #1.**`.\n  Complete. **Routed 2026-01-02 to #1.**\n",
    ]


def test_unclosed_inline_code_does_not_mask_the_next_entry() -> None:
    raw = b'''# Log

## 2026-01-02

- **First.** An unmatched `code span stays literal.
- **Second.** Its own `code` remains inside this active entry.
'''
    assert [candidate.raw for candidate in parse(raw)] == [
        b"- **First.** An unmatched `code span stays literal.\n",
        b"- **Second.** Its own `code` remains inside this active entry.\n",
    ]


def test_graduation_marker_section_remains_excluded() -> None:
    raw = (
        b"# Log\n\n"
        b"## 2026-01-01 \xe2\x80\x94 Backlog migrated by triage session retained\n\n"
        b"- **Graduated.** archive record.\n"
        b"## 2026-01-02\n\n"
        b"- **Inbox.** review me.\n"
    )
    assert [candidate.raw for candidate in parse(raw)] == [b"- **Inbox.** review me.\n"]


def test_duplicate_active_source_blocks_remain_refused() -> None:
    raw = (
        b"# Log\n\n## 2026-01-02\n\n"
        b"- **Repeated.** same bytes.\n"
        b"- **Repeated.** same bytes.\n"
    )
    with pytest.raises(TriageError, match="duplicate active source block"):
        parse(raw)


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
