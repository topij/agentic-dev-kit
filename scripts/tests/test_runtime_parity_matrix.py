"""The capability matrix in `runtime-parity.md` is held to its declaration (#919).

Phase 6 item 10. The file's front matter declares the *Capability matrix* rows with
their statuses (`capability_matrix`) and the records the *Headless lane isolation per
runtime* sub-table links (`lane_isolation_records`). These tests hold each table to
its declaration, so deleting the table, deleting or renaming a row, or giving a row a
status in one place and not the other fails the suite. They also resolve every relative
link and in-file anchor in the file, the sub-table's anchor among them.

What this does not establish: that a row's claim is true. The rows' repository sides
are pinned, where they are, by the tests of the files they describe, and their live
sides by the records the *Live promotion boundary* governs.

Kit source only: the sub-table links records under `saved_plans/`, which an adopter
does not receive.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from _repo_layout import engine_dir, find_repo_root
from conftest import require_kit_source

REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))
PARITY_DOC = REPO_ROOT / "docs" / "agentic-dev-kit" / "runtime-parity.md"

pytestmark = pytest.mark.kit_repo_only("docs/agentic-dev-kit/runtime-parity.md")

# The *Status / exit* vocabulary, in the order the file lists it. A cell names its
# owning issue where the term says it must.
VOCABULARY = ("aligned", "decided", "intentional difference", "not load-bearing", "gap")
NEEDS_ISSUE = {"decided", "not load-bearing", "gap"}

MATRIX_HEADING = "## Capability matrix"
MATRIX_HEADER = ["Capability", "Shared contract", "Claude Code", "Codex", "Status / exit"]
LANE_HEADING = "### Headless lane isolation per runtime"
LANE_HEADER = ["Runtime", "Record", "Promoted", "Not promoted"]
LANE_RUNTIMES = {"Claude Code", "Codex"}

# An inline link's target, with or without a title, and a reference definition's.
LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REFERENCE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
ISSUE = re.compile(r"#\d+")


def _split(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), "runtime-parity.md has no front matter"
    _, frontmatter, body = text.split("---", 2)
    return yaml.safe_load(frontmatter), body


def _section(body: str, heading: str) -> list[str]:
    """The lines under `heading`, up to the next heading of any level."""
    lines = body.splitlines()
    starts = [i for i, line in enumerate(lines) if line.rstrip() == heading]
    assert len(starts) == 1, f"runtime-parity.md has {len(starts)} {heading!r} headings, not one"
    section = []
    for line in lines[starts[0] + 1 :]:
        marks = len(line) - len(line.lstrip("#"))
        if marks and line[marks:].startswith(" "):
            break
        section.append(line)
    return section


def _table(section: list[str], heading: str) -> tuple[list[str], list[list[str]]]:
    """A section's one table: its header cells and its rows' cells.

    One, because a row the parse does not reach is a row nothing checks: a second
    table, or rows below a blank line, could restate a capability with another status.
    """
    block: list[str] = []
    ended = False
    for line in section:
        if line.lstrip().startswith("|"):
            assert not ended, f"{heading!r} holds a second table, or rows outside its table"
            block.append(line)
        elif block:
            ended = True
    assert len(block) >= 2, f"{heading!r} holds no table"
    header, separator, *rows = (
        [cell.strip() for cell in line.strip().strip("|").split("|")] for line in block
    )
    assert all(set(cell) <= set("-: ") for cell in separator), f"{heading!r} table has no separator row"
    return header, rows


def _opens_with(cell: str, term: str) -> bool:
    if not cell.startswith(term):
        return False
    rest = cell[len(term) :]
    return not rest or not (rest[0].isalnum() or rest[0] in "-_")


def _slugs(text: str) -> set[str]:
    """GitHub's heading anchors for a Markdown file, outside fenced code."""
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        match = re.match(r"(#{1,6}) +(.*?) *#* *$", line)
        if fenced or not match:
            continue
        slug = re.sub(r"[^\w\- ]", "", match.group(2).lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        slugs.add(slug if count == 0 else f"{slug}-{count}")
    return slugs


def _assert_matrix_matches_declaration(text: str) -> None:
    declaration, body = _split(text)

    # The vocabulary the file states is the one this test enforces.
    matrix = _section(body, MATRIX_HEADING)
    stated = tuple(
        match.group(1)
        for line in matrix
        if (match := re.match(r"- `([^`]+)` — ", line))
    )
    assert stated == VOCABULARY, f"the file states the status vocabulary {stated}, not {VOCABULARY}"

    declared = declaration.get("capability_matrix")
    assert isinstance(declared, list) and declared, "the front matter declares no capability_matrix"
    for entry in declared:
        assert isinstance(entry, dict) and set(entry) == {"capability", "status"}, (
            f"capability_matrix entry {entry!r} is not exactly a capability and a status"
        )
        assert entry["status"] in VOCABULARY, (
            f"capability_matrix gives {entry['capability']!r} the status {entry['status']!r}, "
            f"outside {VOCABULARY}"
        )
    names = [entry["capability"] for entry in declared]
    assert len(names) == len(set(names)), "capability_matrix declares a capability twice"

    header, rows = _table(matrix, MATRIX_HEADING)
    assert header == MATRIX_HEADER, f"the capability matrix's columns are {header}"
    assert all(len(row) == len(MATRIX_HEADER) for row in rows), "a capability row has the wrong cell count"
    table_names = [row[0] for row in rows]
    assert table_names == names, (
        "the capability matrix's rows differ from capability_matrix: "
        f"table only {sorted(set(table_names) - set(names))}, "
        f"declaration only {sorted(set(names) - set(table_names))}, "
        "or the same rows in another order"
    )
    for row, entry in zip(rows, declared, strict=True):
        name, status = entry["capability"], entry["status"]
        assert all(row), f"the {name!r} row has an empty cell"
        assert _opens_with(row[-1], status), (
            f"the {name!r} row's status cell does not open with its declared status {status!r}: "
            f"{row[-1][:60]!r}"
        )
        if status in NEEDS_ISSUE:
            assert ISSUE.search(row[-1]), f"the {name!r} row is {status!r} but names no issue"

    records = declaration.get("lane_isolation_records")
    assert isinstance(records, list) and records, "the front matter declares no lane_isolation_records"
    for entry in records:
        assert isinstance(entry, dict) and set(entry) == {"runtime", "record"}, (
            f"lane_isolation_records entry {entry!r} is not exactly a runtime and a record"
        )
        assert entry["runtime"] in LANE_RUNTIMES, f"lane record for unknown runtime {entry['runtime']!r}"
    header, rows = _table(_section(body, LANE_HEADING), LANE_HEADING)
    assert header == LANE_HEADER, f"the per-runtime lane table's columns are {header}"
    assert len(rows) == len(records), (
        f"the per-runtime lane table has {len(rows)} rows and lane_isolation_records "
        f"declares {len(records)}"
    )
    for row, entry in zip(rows, records, strict=True):
        assert len(row) == len(LANE_HEADER) and all(row), f"lane row {row[:2]} is short or has an empty cell"
        assert row[0] == entry["runtime"], f"lane row for {row[0]!r} is declared as {entry['runtime']!r}"
        links = LINK.findall(row[1])
        assert links, f"lane row {row[0]!r} links no record"
        target = (PARITY_DOC.parent / links[0].split("#")[0]).resolve()
        assert target == (REPO_ROOT / entry["record"]).resolve(), (
            f"lane row {row[0]!r} links {links[0]!r}, not the declared {entry['record']!r}"
        )

    # Every relative link and anchor resolves, the sub-table's among them.
    own = _slugs(body)
    for target in LINK.findall(body) + REFERENCE.findall(body):
        if re.match(r"[a-z][a-z0-9+.-]*:", target):
            continue
        path, _, anchor = target.partition("#")
        if path:
            resolved = (PARITY_DOC.parent / path).resolve()
            assert resolved.exists(), f"runtime-parity.md links {target!r}, which does not exist"
            assert resolved.is_relative_to(REPO_ROOT), f"runtime-parity.md links {target!r}, outside the repository"
        if anchor:
            if path:
                assert resolved.is_file(), f"runtime-parity.md links {target!r}, an anchor into a non-file"
            slugs = own if not path else _slugs(resolved.read_text(encoding="utf-8"))
            assert anchor in slugs, f"runtime-parity.md links {target!r}, whose anchor does not exist"


def _text() -> str:
    return PARITY_DOC.read_text(encoding="utf-8")


def test_the_capability_matrix_matches_its_declaration() -> None:
    require_kit_source()
    _assert_matrix_matches_declaration(_text())


# Each mutation below must fail the check above: the acceptance half of #919.


def _mutated(old: str, new: str) -> str:
    text = _text()
    assert text.count(old) == 1, f"mutation anchor {old[:60]!r} is not unique"
    return text.replace(old, new)


def _row(capability: str) -> str:
    return next(line for line in _text().splitlines() if line.startswith(f"| {capability} |"))


def _fails(text: str, match: str) -> None:
    with pytest.raises(AssertionError, match=match):
        _assert_matrix_matches_declaration(text)


def test_deleting_the_tables_fails() -> None:
    require_kit_source()
    text = _text()
    start = text.index(MATRIX_HEADING)
    end = text.index("## Live promotion boundary")
    _fails(text[:start] + text[end:], "Capability matrix")


def test_deleting_or_renaming_a_row_fails() -> None:
    require_kit_source()
    row = _row("Runtime memory tripwire")
    _fails(_mutated(row + "\n", ""), "rows differ")
    _fails(_mutated(row, row.replace("Runtime memory tripwire", "Memory tripwire", 1)), "rows differ")


def test_deleting_or_renaming_a_declared_capability_fails() -> None:
    require_kit_source()
    entry = "  - capability: Runtime memory tripwire\n    status: intentional difference\n"
    _fails(_mutated(entry, ""), "rows differ")
    _fails(_mutated(entry, entry.replace("Runtime memory", "Memory")), "rows differ")


def test_reordering_rows_fails() -> None:
    require_kit_source()
    first, second = _row("Repository instructions"), _row("Workflow adapters")
    _fails(_mutated(f"{first}\n{second}\n", f"{second}\n{first}\n"), "another order")


def test_a_status_contradicted_on_either_side_fails() -> None:
    require_kit_source()
    row = _row("Adapter upgrade")
    assert "| aligned: " in row
    _fails(_mutated(row, row.replace("| aligned: ", "| gap: ", 1)), "does not open with")
    entry = "  - capability: Adapter upgrade\n    status: aligned\n"
    _fails(_mutated(entry, entry.replace("aligned", "decided")), "does not open with")


def test_a_status_outside_the_vocabulary_fails() -> None:
    require_kit_source()
    entry = "  - capability: Adapter upgrade\n    status: aligned\n"
    _fails(_mutated(entry, entry.replace("aligned", "mostly aligned")), "outside")


def test_a_status_that_owes_an_issue_and_names_none_fails() -> None:
    require_kit_source()
    row = _row("Interactive hook-message presentation")
    assert "not load-bearing (#608):" in row
    _fails(_mutated(row, re.sub(r"#\d+", "an issue", row)), "names no issue")


def test_a_stated_vocabulary_that_drifts_from_the_test_fails() -> None:
    require_kit_source()
    _fails(
        _mutated("- `gap` — a required parity outcome", "- `open` — a required parity outcome"),
        "status vocabulary",
    )


def test_deleting_a_lane_record_on_either_side_fails() -> None:
    require_kit_source()
    row = next(
        line
        for line in _text().splitlines()
        if line.startswith("| Codex |") and "parallel-batch-live-validation" in line
    )
    _fails(_mutated(row + "\n", ""), "lane table has")
    entry = (
        "  - runtime: Codex\n"
        "    record: saved_plans/codex-parallel-batch-live-validation_2026-09-01.md\n"
    )
    _fails(_mutated(entry, ""), "lane table has")


def test_a_lane_row_linking_another_record_fails() -> None:
    require_kit_source()
    entry = "    record: saved_plans/codex-writing-lane-live-validation_2026-08-30.md\n"
    _fails(
        _mutated(entry, entry.replace("2026-08-30", "2026-08-27")),
        "not the declared",
    )


def test_breaking_the_sub_table_anchor_fails() -> None:
    require_kit_source()
    _fails(
        _mutated(f"{LANE_HEADING}\n", "### Headless lanes per runtime\n"),
        "Headless lane isolation per runtime",
    )
    text = _text()
    assert text.count("(#headless-lane-isolation-per-runtime)") >= 1
    _fails(
        text.replace("(#headless-lane-isolation-per-runtime)", "(#headless-lane-isolation)", 1),
        "anchor does not exist",
    )


def test_a_broken_relative_link_fails() -> None:
    require_kit_source()
    _fails(
        _mutated(
            "(../../saved_plans/claude-writing-lane-live-validation_2026-08-27.md)",
            "(../../saved_plans/claude-writing-lane-live-validation_2026-08-26.md)",
        ),
        "does not exist|not the declared",
    )
    _fails(
        _mutated("(#adoption-footprint)", "(#adoption-surfaces)"),
        "anchor does not exist",
    )


def test_a_broken_or_escaping_link_outside_the_lane_table_fails() -> None:
    require_kit_source()
    link = "(../../saved_plans/claude-sessionstart-matcher-live-validation_2026-08-29.md)"
    _fails(_mutated(link, link.replace("2026-08-29", "2026-08-28")), "which does not exist")
    # The repository's parent directory exists, so only the containment check can fire.
    _fails(_mutated(link, "(../../..)"), "outside the repository")


def test_links_in_other_markdown_forms_are_checked() -> None:
    require_kit_source()
    text = _text() + '\nSee [a titled link](../../saved_plans/absent.md "title").\n'
    _fails(text, "which does not exist")
    _fails(_text() + "\n[ref]: ../../saved_plans/absent.md\n", "which does not exist")
    _fails(_text() + "\nSee [a directory](../../saved_plans/#section).\n", "an anchor into a non-file")


def test_rows_outside_the_one_table_fail() -> None:
    require_kit_source()
    last = _row("Drift inspection")
    rogue = "| Adapter upgrade | a | b | c | gap (#919): restated with another status |"
    _fails(_mutated(last + "\n", f"{last}\n\n{rogue}\n"), "second table")
    _fails(
        _mutated(f"{LANE_HEADING}\n", f"{LANE_HEADING}\n\n| A | B |\n|---|---|\n| c | d |\n"),
        "second table",
    )


def test_a_status_term_that_only_starts_the_cell_word_fails() -> None:
    require_kit_source()
    row = _row("Adapter upgrade")
    _fails(_mutated(row, row.replace("| aligned: ", "| alignedish: ", 1)), "does not open with")


def test_a_malformed_row_or_header_fails() -> None:
    require_kit_source()
    row = _row("Adapter upgrade")
    cells = row.split(" | ")
    _fails(_mutated(row, row.replace(cells[1], "", 1)), "empty cell")
    _fails(_mutated(row, row + " extra |"), "wrong cell count")
    _fails(
        _mutated("| Codex | Status / exit |", "| Codex | Status |"),
        "capability matrix's columns",
    )
    _fails(
        _mutated("| Promoted | Not promoted |", "| Promoted | Withheld |"),
        "lane table's columns",
    )


def test_a_malformed_declaration_entry_fails() -> None:
    require_kit_source()
    entry = "  - capability: Adapter upgrade\n    status: aligned\n"
    _fails(_mutated(entry, entry + "    note: extra\n"), "is not exactly a capability and a status")
    lane = "  - runtime: Codex\n    record: saved_plans/codex-parallel-batch-live-validation_2026-09-01.md\n"
    _fails(_mutated(lane, lane.replace("Codex", "Gemini")), "unknown runtime")


def test_a_lane_row_under_another_runtime_fails() -> None:
    require_kit_source()
    row = next(
        line
        for line in _text().splitlines()
        if line.startswith("| Codex |") and "parallel-batch-live-validation" in line
    )
    _fails(_mutated(row, row.replace("| Codex |", "| Claude Code |", 1)), "is declared as")
