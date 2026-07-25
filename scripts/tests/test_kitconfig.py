"""Tests for the stdlib-only config reader (scripts/lib/kitconfig.py).

Two things are pinned here:

1. **Parity with PyYAML** on the config the kit actually ships. The reader exists
   so engines can drop the PyYAML dependency; the moment it disagrees with a real
   YAML parser on a construct the kit uses, that trade stops being safe. Skipped
   (not failed) when PyYAML is absent, so the suite still runs in a bare env —
   which is the whole point of the reader.
2. **The supported subset**, construct by construct, so a future edit that breaks
   inline lists or comment-stripping fails here rather than in an engine.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import kitconfig  # noqa: E402


SHIPPED_CONFIG = REPO_ROOT / "config" / "dev-model.yaml"


def test_matches_pyyaml_on_the_shipped_config():
    yaml = pytest.importorskip("yaml", reason="PyYAML absent — parity check skipped")
    text = SHIPPED_CONFIG.read_text(encoding="utf-8")
    assert kitconfig.loads(text) == yaml.safe_load(text)


def test_loads_the_shipped_config_without_pyyaml():
    config = kitconfig.load_config(SHIPPED_CONFIG)
    assert kitconfig.get(config, "vcs.protected_branch") == "main"
    assert kitconfig.get(config, "kit.version") == 2


def test_nested_mappings_and_scalar_types():
    parsed = kitconfig.loads(
        """
top:
  text: hello
  quoted: "a: b"
  number: 42
  yes_flag: true
  no_flag: false
  empty:
  nested:
    deeper:
      leaf: found
"""
    )
    assert parsed["top"]["text"] == "hello"
    assert parsed["top"]["quoted"] == "a: b"
    assert parsed["top"]["number"] == 42
    assert parsed["top"]["yes_flag"] is True
    assert parsed["top"]["no_flag"] is False
    assert parsed["top"]["empty"] is None
    assert parsed["top"]["nested"]["deeper"]["leaf"] == "found"


def test_inline_and_block_lists():
    parsed = kitconfig.loads(
        """
review:
  bots: [coderabbit, bugbot]
  none: []
  markers:
    - "first marker"
    - second
"""
    )
    assert parsed["review"]["bots"] == ["coderabbit", "bugbot"]
    assert parsed["review"]["none"] == []
    assert parsed["review"]["markers"] == ["first marker", "second"]


def test_block_list_of_mappings():
    parsed = kitconfig.loads(
        """
doc_budgets:
  - path: docs/handoff.md
    budget: 400
    archive: docs/handoff-history.md
  - path: docs/friction-log.md
    budget: 150
    archive: docs/friction-log-archive.md
after: sentinel
"""
    )
    assert parsed["doc_budgets"] == [
        {"path": "docs/handoff.md", "budget": 400, "archive": "docs/handoff-history.md"},
        {
            "path": "docs/friction-log.md",
            "budget": 150,
            "archive": "docs/friction-log-archive.md",
        },
    ]
    # The list must close cleanly — a following top-level key is not swallowed.
    assert parsed["after"] == "sentinel"


@pytest.mark.parametrize(
    ("style", "text"),
    [
        # Indented under the key — the style the kit's own config uses.
        ("indented", "a:\n  - k: 1\n    j: 2\n  - k: 3\nb: 9\n"),
        # At the SAME indent as the key. Equally valid YAML, and what most
        # formatters emit. This used to parse to {'a': None, 'j': 2, 'b': 9} —
        # the list dropped and its nested keys leaked into the parent mapping,
        # silently, with no error. Worst possible failure for a config reader.
        ("flush", "a:\n- k: 1\n  j: 2\n- k: 3\nb: 9\n"),
        # Flush list nested inside a mapping, with a sibling key after it.
        ("flush-nested", "top:\n  a:\n  - k: 1\n    j: 2\n  b: 9\nz: 1\n"),
    ],
)
def test_block_list_indent_styles(style, text):
    parsed = kitconfig.loads(text)
    owner = parsed["top"] if style == "flush-nested" else parsed
    assert owner["a"] == [{"k": 1, "j": 2}, {"k": 3}] or owner["a"] == [{"k": 1, "j": 2}]
    assert owner["b"] == 9
    if style == "flush-nested":
        assert parsed["z"] == 1
        assert "j" not in parsed and "j" not in owner  # no key leakage


def test_flush_list_of_scalars():
    parsed = kitconfig.loads("markers:\n- first\n- second\nafter: 1\n")
    assert parsed["markers"] == ["first", "second"]
    assert parsed["after"] == 1


def test_comments_are_stripped_but_not_inside_values():
    parsed = kitconfig.loads(
        """
vcs:
  branch: main         # never committed to directly
  pattern: "chore/triage-{date}#1"
  url: https://example.test/board#section
"""
    )
    assert parsed["vcs"]["branch"] == "main"
    # A '#' not preceded by whitespace is part of the value, not a comment.
    assert parsed["vcs"]["pattern"] == "chore/triage-{date}#1"
    assert parsed["vcs"]["url"] == "https://example.test/board#section"


def test_get_is_fail_loud_without_a_default():
    config = {"a": {"b": 1}}
    assert kitconfig.get(config, "a.b") == 1
    assert kitconfig.get(config, "a.missing", "fallback") == "fallback"
    assert kitconfig.get(config, "nope.deep", None) is None
    with pytest.raises(KeyError, match=re.escape("a.missing")):
        kitconfig.get(config, "a.missing")


def test_get_str_list_tolerates_a_bare_scalar():
    config = kitconfig.loads(
        """
review:
  listed: [a, b]
  single: solo
"""
    )
    assert kitconfig.get_str_list(config, "review.listed", []) == ["a", "b"]
    # A hand-authored lone value must not iterate character-by-character.
    assert kitconfig.get_str_list(config, "review.single", []) == ["solo"]
    assert kitconfig.get_str_list(config, "review.absent", ["fallback"]) == ["fallback"]


def test_load_config_reports_a_missing_file_clearly():
    with pytest.raises(FileNotFoundError, match="dev-model config not found"):
        kitconfig.load_config(REPO_ROOT / "config" / "does-not-exist.yaml")


@pytest.mark.parametrize(
    "name",
    ["handoff.md.tmpl", "handoff-history.md.tmpl", "friction-log.md.tmpl", "friction-log-archive.md.tmpl"],
)
def test_narrative_templates_ship(name):
    """init.sh renders these; a missing one silently degrades adoption to an
    unrendered skeleton, which is the bug the templates were added to fix."""
    assert (REPO_ROOT / "docs" / "templates" / name).is_file()


@pytest.mark.parametrize(
    "skeleton",
    ["handoff.md", "handoff-history.md", "friction-log.md", "friction-log-archive.md"],
)
def test_shipped_skeletons_carry_the_unrendered_marker(skeleton):
    """The marker is what lets init.sh tell 'the file the kit shipped' from 'a
    handoff someone is using'. Without it the seed step can never fire on a
    copy-in, which is exactly how adopters ended up with `my-project` headers.

    Asserted on the LITERAL adopter-facing filenames, deliberately not via
    `paths.handoff`: this repo points its own config at `docs/kit-*.md` so its
    session blocks never ship to adopters, so reading the config here would check
    the kit's live plan (which must NOT carry the marker) instead of the skeleton."""
    doc = REPO_ROOT / "docs" / skeleton
    assert "devkit-template: unrendered" in doc.read_text(encoding="utf-8"), doc


def test_kits_own_plan_is_real_not_a_skeleton():
    """The flip side: this repo must actually practise Principle #1. A kit whose
    own living plan is an unrendered template is not dogfooding it."""
    config = kitconfig.load_config(SHIPPED_CONFIG)
    for key in ("paths.handoff", "paths.friction_log"):
        doc = REPO_ROOT / kitconfig.get(config, key)
        text = doc.read_text(encoding="utf-8")
        assert "devkit-template: unrendered" not in text, doc
        assert "YYYY-MM-DD" not in text, f"{doc} still has placeholder dates"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A scalar containing ':' is NOT a mapping — YAML requires the colon be
        # followed by whitespace or end-of-line. Testing for a bare ':' in the
        # body turned `- https://host/p` into {"https": "//host/p"}: a silent
        # guess, which this module's contract forbids in favour of skipping.
        ("a:\n  - https://example.com/path\n", ["https://example.com/path"]),
        ("a:\n  - http://h:8080/x\n", ["http://h:8080/x"]),
        ("a:\n  - 12:30 standup\n", ["12:30 standup"]),
        # A genuine `key: value` item still opens a mapping.
        ("a:\n  - k: v\n", [{"k": "v"}]),
    ],
)
def test_dash_item_colon_is_not_always_a_mapping(text, expected):
    assert kitconfig.loads(text)["a"] == expected


def test_review_skipped_lives_only_in_unavailable_markers():
    """`is_noise()` checks unavailability FIRST and returns False, so a marker in
    both lists is dead weight in `noise_markers` and reads as a precedence
    ambiguity. Keep it in exactly one place."""
    config = kitconfig.load_config(SHIPPED_CONFIG)
    noise = kitconfig.get_str_list(config, "review.noise_markers", [])
    unavailable = kitconfig.get_str_list(config, "review.unavailable_markers", [])
    assert "review skipped" in unavailable
    assert not (set(noise) & set(unavailable)), "markers must not appear in both lists"


def test_check_doc_budget_handles_a_config_without_doc_budgets(tmp_path):
    """The config reader is fail-loud by design (KeyError with no default), so
    every engine that calls it must catch that too — otherwise a config missing
    an optional-looking section crashes with a traceback instead of the intended
    one-line error and exit 2. Caught post-merge on #16; the gap predated the
    switch to kitconfig (devmodel_config.get was equally fail-loud)."""
    import subprocess

    cfg = tmp_path / "dev-model.yaml"
    cfg.write_text("kit:\n  version: 2\npaths:\n  handoff: docs/handoff.md\n", encoding="utf-8")
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(REPO_ROOT / "scripts" / "check_doc_budget.py"), "--config", str(cfg)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    assert "doc_budgets" in result.stderr
