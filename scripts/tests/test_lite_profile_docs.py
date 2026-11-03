"""The lite profile's workflow docs keep their shared clauses identical to the full ones (#1320).

The lite docs under `docs/agentic-dev-kit/lite/` are separate files so a
lite adopter can read them without the full kit's machinery. The clauses both
profiles keep are wrapped in `<!-- lite:begin <id> -->` / `<!-- lite:end <id> -->`
markers in both files, and these tests fail when the two copies differ, so a change
to one cannot silently leave the other behind (the drift #243 and #273 describe).
Whitespace is collapsed before comparing, so indentation and line wrapping may
differ between the two files; the words may not.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))
WORKFLOWS = REPO_ROOT / "docs/agentic-dev-kit/workflows"
LITE = REPO_ROOT / "docs/agentic-dev-kit/lite"

# Each lite doc and the full doc whose marked clauses it must carry.
PAIRS = {
    "lite-session-start.md": "session-start.md",
    "lite-wrap-up.md": "wrap-up.md",
}
LITE_DOCS = ("lite-session-start.md", "lite-wrap-up.md", "lite-review.md")

MARKER = re.compile(r"<!-- lite:(begin|end) ([a-z0-9-]+) -->")


def _blocks(path: Path) -> dict[str, str]:
    """Return each marked block's text, refusing malformed, nested or repeated markers."""
    text = path.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    open_id: str | None = None
    start = 0
    for m in MARKER.finditer(text):
        kind, block_id = m.groups()
        if kind == "begin":
            assert open_id is None, f"{path}: {block_id!r} begins inside {open_id!r}"
            assert block_id not in blocks, f"{path}: {block_id!r} is marked twice"
            open_id, start = block_id, m.end()
        else:
            assert open_id == block_id, f"{path}: end {block_id!r} does not close {open_id!r}"
            blocks[block_id] = text[start : m.start()]
            open_id = None
    assert open_id is None, f"{path}: {open_id!r} is never closed"
    return blocks


def _normalise(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize("lite_name", sorted(PAIRS))
def test_lite_doc_carries_every_marked_full_clause_unchanged(lite_name: str) -> None:
    full = _blocks(WORKFLOWS / PAIRS[lite_name])
    lite = _blocks(LITE / lite_name)
    assert full, f"{PAIRS[lite_name]} marks no shared clause"
    assert sorted(lite) == sorted(full), (
        f"marked clauses differ: only in the full doc {sorted(set(full) - set(lite))}, "
        f"only in the lite doc {sorted(set(lite) - set(full))}"
    )
    for block_id, text in full.items():
        assert _normalise(lite[block_id]) == _normalise(text), (
            f"{lite_name}: clause {block_id!r} differs from {PAIRS[lite_name]}"
        )


def test_lite_review_carries_the_configured_correctness_focus() -> None:
    config = yaml.safe_load((REPO_ROOT / "config/dev-model.yaml").read_text(encoding="utf-8"))
    lenses = config["review"]["fallback_panel"]["lenses"]
    (focus,) = [lens["focus"] for lens in lenses if lens["name"] == "correctness"]
    assert _normalise(_blocks(LITE / "lite-review.md")["correctness-focus"]) == _normalise(focus)


@pytest.mark.parametrize("lite_name", LITE_DOCS)
def test_lite_doc_names_no_engine_or_loader(lite_name: str) -> None:
    # A lite repository has no engines directory and no config loader; a lite doc
    # that sends the reader to one gives an instruction that cannot be carried out.
    text = (LITE / lite_name).read_text(encoding="utf-8")
    for needle in ("<engine-dir>", "uv run", "kitconfig", "load_config"):
        assert needle not in text, f"{lite_name} names {needle!r}"


@pytest.mark.parametrize("lite_name", LITE_DOCS)
def test_lite_doc_links_stay_inside_the_lite_docs(lite_name: str) -> None:
    # A lite install carries the lite docs and none of the full workflows, so a
    # link out of this directory would break in the adopter.
    text = (LITE / lite_name).read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#\s]+)", text):
        if "://" in target:
            continue
        resolved = (LITE / target).resolve()
        assert resolved.is_file(), f"{lite_name}: link {target!r} resolves to nothing"
        assert resolved.parent == LITE, f"{lite_name}: link {target!r} leaves the lite docs"


def test_markers_reject_a_clause_that_differs(tmp_path: Path) -> None:
    # Positive control: the comparison above must be able to fail.
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("<!-- lite:begin x -->\nkeep this\n<!-- lite:end x -->\n", encoding="utf-8")
    b.write_text("<!-- lite:begin x -->\n  keep   that\n<!-- lite:end x -->\n", encoding="utf-8")
    assert _normalise(_blocks(a)["x"]) != _normalise(_blocks(b)["x"])
    b.write_text("<!-- lite:begin x -->\n  keep\n   this\n<!-- lite:end x -->\n", encoding="utf-8")
    assert _normalise(_blocks(a)["x"]) == _normalise(_blocks(b)["x"])


def test_markers_reject_an_unclosed_clause(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    a.write_text("<!-- lite:begin x -->\ntext\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="never closed"):
        _blocks(a)
