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

# Each lite doc, the full doc whose marked clauses it must carry, and the ids both
# must mark. The ids are pinned here, not read from the docs, so removing a marker
# pair from both files fails rather than quietly shrinking what is guarded.
PAIRS = {
    "lite-session-start.md": ("session-start.md", {"source-failure", "dont-invent-work"}),
    "lite-wrap-up.md": (
        "wrap-up.md",
        {
            "handoff-content",
            "record-prose",
            "park-conditions",
            "stage-by-name",
            "completion-inference",
            "no-working-detail",
        },
    ),
}
LITE_DOCS = ("lite-session-start.md", "lite-wrap-up.md", "lite-review.md")

MARKER = re.compile(r"<!-- lite:(begin|end) ([a-z0-9-]+) -->")
# Every link-shaped target in a lite doc, found in the raw text with no attempt to
# tell code from prose: an allowlist that is fail-closed. A link-shaped string that
# is only an example in code is still refused, which costs a rewording and never a
# missed link. Inline and reference-style Markdown links, at any indent, and
# `href=` / `src=` attributes, quoted or not.
LINK_TARGET = re.compile(
    r"\]\(\s*<?([^)>\s]+)"
    r"|^[ \t]*\[[^\]]+\]:[ \t]*<?([^\s>]+)"
    r"""|\b(?:href|src)\s*=\s*["']?([^"'\s>]+)""",
    re.I | re.M,
)
URI_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
LITE_DOC_NAME = re.compile(r"lite-[a-z0-9-]+\.md")
# What a lite repository does not have, matched case-insensitively against text whose
# whitespace runs are collapsed, so a name wrapped across a line is still found: the
# engines and their runner, the config loader, the full kit's test command, and the
# full-kit workflows and engines a reader might be sent to by name.
ENGINE_NEEDLES = (
    "<engine-dir>",
    "uv run",
    "kitconfig",
    "load_config",
    "scripts/",
    "make test",
    "pr_watch",
    "pr-watch",
    "check_record_prose",
    "session_cleanup",
    "panel_prompt",
    "kit_doctor",
    "dev_session",
    "launch_lane",
    "sweep_scratch",
)


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


def _compare(full_path: Path, lite_path: Path, expected: set[str]) -> None:
    """Fail unless both docs mark exactly `expected` and every marked clause matches."""
    full = _blocks(full_path)
    lite = _blocks(lite_path)
    assert set(full) == expected, f"{full_path.name} marks {sorted(full)}, expected {sorted(expected)}"
    assert set(lite) == expected, f"{lite_path.name} marks {sorted(lite)}, expected {sorted(expected)}"
    for block_id in sorted(expected):
        assert _normalise(lite[block_id]) == _normalise(full[block_id]), (
            f"{lite_path.name}: clause {block_id!r} differs from {full_path.name}"
        )


def _link_targets(text: str) -> list[str]:
    return [next(group for group in m.groups() if group) for m in LINK_TARGET.finditer(text)]


def _check_links(doc: Path, lite_dir: Path) -> None:
    """Fail unless every link-shaped target in `doc` is an anchor, a URL, or a lite doc in `lite_dir`."""
    for target in _link_targets(doc.read_text(encoding="utf-8")):
        if target.startswith("#") or URI_SCHEME.match(target):
            continue  # an in-page anchor, or a URL / mailto: neither is a file in the install
        name = target.split("#", 1)[0]
        assert LITE_DOC_NAME.fullmatch(name), f"{doc.name}: link {target!r} leaves the lite docs"
        assert (lite_dir / name).is_file(), f"{doc.name}: link {target!r} resolves to nothing"


def _engine_mentions(text: str) -> list[str]:
    flat = " ".join(text.split()).lower()
    return [needle for needle in ENGINE_NEEDLES if needle in flat]


@pytest.mark.parametrize("lite_name", sorted(PAIRS))
def test_lite_doc_carries_every_marked_full_clause_unchanged(lite_name: str) -> None:
    full_name, expected = PAIRS[lite_name]
    _compare(WORKFLOWS / full_name, LITE / lite_name, expected)


def test_lite_review_carries_the_configured_correctness_focus() -> None:
    config = yaml.safe_load((REPO_ROOT / "config/dev-model.yaml").read_text(encoding="utf-8"))
    lenses = config["review"]["fallback_panel"]["lenses"]
    (focus,) = [lens["focus"] for lens in lenses if lens["name"] == "correctness"]
    assert set(_blocks(LITE / "lite-review.md")) == {"correctness-focus"}
    assert _normalise(_blocks(LITE / "lite-review.md")["correctness-focus"]) == _normalise(focus)


@pytest.mark.parametrize("lite_name", LITE_DOCS)
def test_lite_doc_names_no_engine_or_loader(lite_name: str) -> None:
    # A lite repository has no engines directory and no config loader; a lite doc
    # that sends the reader to one gives an instruction that cannot be carried out.
    assert _engine_mentions((LITE / lite_name).read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("lite_name", LITE_DOCS)
def test_lite_doc_links_stay_inside_the_lite_docs(lite_name: str) -> None:
    # A lite install carries the lite docs and none of the full workflows, so a
    # link out of this directory would break in the adopter.
    _check_links(LITE / lite_name, LITE)


# The guard's own branches, against fixtures, so each refusal is shown to fire.


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_compare_rejects_a_clause_that_differs(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep this\n<!-- lite:end x -->\n")
    lite = _write(tmp_path / "lite.md", "<!-- lite:begin x -->\n  keep   that\n<!-- lite:end x -->\n")
    with pytest.raises(AssertionError, match="clause 'x' differs"):
        _compare(full, lite, {"x"})
    _write(lite, "<!-- lite:begin x -->\n  keep\n   this\n<!-- lite:end x -->\n")
    _compare(full, lite, {"x"})


def test_compare_rejects_a_marker_pair_removed_from_both_docs(tmp_path: Path) -> None:
    both = "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n"
    full = _write(tmp_path / "full.md", both)
    lite = _write(tmp_path / "lite.md", both)
    with pytest.raises(AssertionError, match="expected"):
        _compare(full, lite, {"x", "y"})


def test_compare_rejects_a_clause_only_the_lite_doc_marks(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n")
    lite = _write(
        tmp_path / "lite.md",
        "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n<!-- lite:begin y -->\nmore\n<!-- lite:end y -->\n",
    )
    with pytest.raises(AssertionError, match="full.md marks"):
        _compare(full, lite, {"x", "y"})


def test_compare_rejects_a_clause_marked_in_one_doc_only(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n")
    lite = _write(tmp_path / "lite.md", "keep\n")
    with pytest.raises(AssertionError, match="lite.md marks"):
        _compare(full, lite, {"x"})


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("<!-- lite:begin x -->\ntext\n", "never closed"),
        ("<!-- lite:begin x -->\n<!-- lite:begin y -->\n", "begins inside"),
        ("<!-- lite:begin x -->\na\n<!-- lite:end x -->\n<!-- lite:begin x -->\nb\n<!-- lite:end x -->\n", "marked twice"),
        ("<!-- lite:begin x -->\ntext\n<!-- lite:end y -->\n", "does not close"),
        ("<!-- lite:end x -->\n", "does not close"),
    ],
)
def test_blocks_rejects_malformed_markers(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _blocks(_write(tmp_path / "a.md", text))


def test_engine_needles_are_pinned() -> None:
    # Pinned here so that dropping a needle fails, rather than dropping its test too.
    assert set(ENGINE_NEEDLES) == {
        "<engine-dir>", "uv run", "kitconfig", "load_config", "scripts/", "make test",
        "pr_watch", "pr-watch", "check_record_prose", "session_cleanup", "panel_prompt",
        "kit_doctor", "dev_session", "launch_lane", "sweep_scratch",
    }


@pytest.mark.parametrize("needle", ENGINE_NEEDLES)
def test_engine_mentions_catch_every_needle(needle: str) -> None:
    assert _engine_mentions(f"Run {needle} here.") == [needle]


@pytest.mark.parametrize("text", ["Run uv\nrun here.", "Use Pr-Watch.", "then MAKE  TEST"])
def test_engine_mentions_ignore_case_and_wrapping(text: str) -> None:
    assert _engine_mentions(text) != []


@pytest.fixture
def lite_dir(tmp_path: Path) -> Path:
    d = tmp_path / "lite"
    d.mkdir()
    _write(d / "lite-other.md", "# Other\n")
    _write(tmp_path / "outside.md", "# Outside\n")
    return d


@pytest.mark.parametrize(
    "line",
    [
        "[ok](lite-other.md)",
        "[ok](lite-other.md#a-section)",
        "[ok][r]\n\n[r]: lite-other.md",
        "[anchor](#report)",
        "[mail](mailto:a@example.com)",
        "[web](https://example.com/x.md)",
        '<a href="lite-other.md">x</a>',
        "No link here at all.",
    ],
)
def test_check_links_accepts_links_a_lite_install_resolves(lite_dir: Path, line: str) -> None:
    _check_links(_write(lite_dir / "lite-doc.md", line + "\n"), lite_dir)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("[x](lite-missing.md)", "resolves to nothing"),
        ("[x](../outside.md)", "leaves the lite docs"),
        ("[x](other.md)", "leaves the lite docs"),
        ("[x][r]\n\n[r]: ../outside.md", "leaves the lite docs"),
        ("- item\n\n     [r]: ../outside.md", "leaves the lite docs"),
        ('<a href="../outside.md">x</a>', "leaves the lite docs"),
        ("<a href=../outside.md>x</a>", "leaves the lite docs"),
        ('<img src="../outside.md">', "leaves the lite docs"),
        ("Code `[x](../outside.md)` is still refused.", "leaves the lite docs"),
        ("Use a ` tick\n\n[x](../outside.md)\n\n``code``", "leaves the lite docs"),
        ("~~~\n[x](../outside.md)\n~~~", "leaves the lite docs"),
    ],
)
def test_check_links_rejects_links_a_lite_install_cannot_resolve(lite_dir: Path, line: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_links(_write(lite_dir / "lite-doc.md", line + "\n"), lite_dir)
