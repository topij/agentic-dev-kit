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


def test_graduation_marker_section_is_never_removed_as_empty_even_at_eof() -> None:
    """#806: the empty-section removal used to delete a bare marker heading —
    exactly the shape a prior sweep's own marker takes — because it has no
    entries of its own. It must reuse `parse`'s own recognizer, not a second
    one, and must not touch it even when it is the file's last section."""
    raw = (
        b"# Log\n\n"
        b"## 2026-01-01 \xe2\x80\x94 Backlog migrated by triage session retained\n\n"
        b"## 2026-01-02\n\n"
        b"- **Only entry.** gets swept\n"
    )
    candidates = parse(raw)
    assert len(candidates) == 1
    active, archive = exact_sweep(raw, candidates, {candidates[0].candidate_id})
    assert b"Backlog migrated by triage session retained" in active
    assert not active.endswith(b"\n\n"), "emptied trailing section left a blank line at EOF"
    assert active == (
        b"# Log\n\n## 2026-01-01 \xe2\x80\x94 Backlog migrated by triage session retained\n"
    )


def test_exact_sweep_trims_the_separating_blank_line_when_the_last_section_empties() -> None:
    """#806: removing an empty dated section deleted from its `## ` heading to
    the next section or EOF, but never the blank line that separated it from
    whatever precedes it — which is harmless mid-file (a single blank line
    still separates the surviving neighbours) but becomes a trailing blank
    line when the emptied section was the file's last."""
    raw = (
        b"# Log\n\n## 2026-09-20\n\n- **Kept.** still open\n\n"
        b"## 2026-09-10\n\n- **Sole entry.** gets swept\n"
    )
    candidates = parse(raw)
    sole = next(candidate for candidate in candidates if b"Sole entry" in candidate.raw)
    active, archive = exact_sweep(raw, candidates, {sole.candidate_id})
    assert active == b"# Log\n\n## 2026-09-20\n\n- **Kept.** still open\n"
    assert archive == b"## 2026-09-10\n\n- **Sole entry.** gets swept\n"


def _render_sweep_state(*, filed: list[tuple[str, str]] | None = None, archived: list[str] | None = None, approval: tuple[str, str] | None = None, engine_mode: str | None = "engine-backed") -> dict:
    operations = []
    decisions = []
    for candidate_id, identifier in filed or []:
        operations.append({
            "candidate_id": candidate_id,
            "decision": "file",
            "status": "verified",
            "returned_identifier": identifier,
            "destination": {
                "backend": "github-issues",
                "host": "github.com",
                "repository": "topij/agentic-dev-kit",
                "project": "topij/agentic-dev-kit",
            },
        })
        decisions.append({"candidate_id": candidate_id, "decision": "file"})
    for candidate_id in archived or []:
        decisions.append({"candidate_id": candidate_id, "decision": "archive"})
    state: dict = {"operations": operations, "decisions": decisions}
    if engine_mode is not None:
        state["engine_mode"] = engine_mode
    if approval is not None:
        command, approver = approval
        state["approval"] = {"approver_identity": approver, "source_read_back": {"text": command}}
    return state


def test_render_sweep_writes_a_record_block_under_the_marker() -> None:
    raw = b"# Log\n\n## 2026-09-20\n\n- **Filed one.** body\n\n- **Archived one.** body\n"
    candidates = parse(raw)
    filed_id, archived_id = candidates[0].candidate_id, candidates[1].candidate_id
    state = _render_sweep_state(
        filed=[(filed_id, "793")],
        archived=[archived_id],
        approval=(f"approve {filed_id}", "topi"),
    )
    marker = "## 2026-09-26 — Backlog migrated by triage session abc123\n\n".encode()
    active, archive = render_sweep(raw, b"# Archive\n", candidates, state, marker)
    assert b"Engine mode: engine-backed." in active
    assert b"Filed: [#793](https://github.com/topij/agentic-dev-kit/issues/793)." in active
    assert f"Archived without filing: {archived_id}.".encode() in active
    assert f"Approval command: `approve {filed_id}`. Approver: `topi`.".encode() in active
    # Marker was inserted at absolute EOF (the sole section emptied and was
    # removed), so the record's own trailing blank line must not survive either.
    assert not active.endswith(b"\n\n")


def test_render_sweep_record_block_omits_lines_it_has_no_data_for() -> None:
    raw = b"# Log\n\n## 2026-09-20\n\n- **Archived one.** body\n"
    candidates = parse(raw)
    state = _render_sweep_state(archived=[candidates[0].candidate_id], engine_mode=None)
    marker = "## 2026-09-26 — Backlog migrated by triage session abc123\n\n".encode()
    active, _archive = render_sweep(raw, b"# Archive\n", candidates, state, marker)
    assert b"Engine mode:" not in active
    assert b"Filed:" not in active
    assert b"Archived without filing:" in active
    assert b"Approval command:" not in active


def test_render_sweep_second_sweep_same_day_keeps_the_first_markers_record() -> None:
    """#806's own reproduction: a second engine-backed sweep the same day must
    not delete the first sweep's marker or the record now recorded under it."""
    raw = (
        b"# Log\n\n## 2026-09-20\n\n- **First.** body\n\n"
        b"## 2026-09-10\n\n- **Older.** still open\n"
    )
    candidates_a = parse(raw)
    state_a = _render_sweep_state(archived=[candidates_a[0].candidate_id], approval=("archive TRI-01", "topi"))
    marker_a = "## 2026-09-26 — Backlog migrated by triage session AAA\n\n".encode()
    active_a, archive_a = render_sweep(raw, b"# Archive\n", candidates_a, state_a, marker_a)

    candidates_b = parse(active_a)
    assert len(candidates_b) == 1  # only "Older." remains, freshly numbered TRI-01
    state_b = _render_sweep_state(
        filed=[(candidates_b[0].candidate_id, "900")],
        approval=(f"approve {candidates_b[0].candidate_id}", "topi"),
    )
    marker_b = "## 2026-09-26 — Backlog migrated by triage session BBB\n\n".encode()
    active_b, archive_b = render_sweep(active_a, archive_a, candidates_b, state_b, marker_b)

    assert b"session AAA" in active_b
    assert b"Archived without filing: TRI-01." in active_b
    assert b"session BBB" in active_b
    assert b"Filed: [#900](https://github.com/topij/agentic-dev-kit/issues/900)." in active_b
    # The second marker sits above the first: newest at the top, per the
    # friction log's own "appended at the top" convention.
    assert active_b.index(b"session BBB") < active_b.index(b"session AAA")


def test_render_sweep_adds_a_blank_line_before_the_appended_archive_heading() -> None:
    raw = b"# Log\n\n## 2026-09-20\n\n- **Archived one.** body\n"
    candidates = parse(raw)
    state = _render_sweep_state(archived=[candidates[0].candidate_id], approval=("archive TRI-01", "topi"))
    marker = "## 2026-09-26 — Backlog migrated by triage session abc123\n\n".encode()
    _active, archive = render_sweep(raw, b"# Archive\n\nprior content\n", candidates, state, marker)
    assert archive == b"# Archive\n\nprior content\n\n## 2026-09-20\n\n- **Archived one.** body\n"
