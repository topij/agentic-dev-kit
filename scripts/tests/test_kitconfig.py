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
    # A nested string parses to a non-empty string, and the schema stamp to an
    # int. Deliberately NOT `== "main"`: the branch name is adopter-owned, and
    # pinning it makes this test assert something about whoever's config is on
    # disk rather than about the reader. A repo whose trunk is `master` is a
    # supported configuration, not a test failure.
    protected = kitconfig.get(config, "vcs.protected_branch")
    assert isinstance(protected, str) and protected
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


# Every scalar form where "is this a float?" is a judgement call, plus the
# known-and-deliberate divergences. Kept as one list so the parity check below
# cannot quietly cover a smaller set than the type assertions do.
_FLOAT_EDGE_CASES = (
    "2.5", "15", "1.", "0.0", "-0.0",
    "-0.5", "+1.5",   # sign IS allowed on the digits.digits form
    ".5", "-.5", "+.5",  # …and is NOT allowed on the .digits form
    "1.0e+3",   # signed exponent — a float in YAML 1.1
    "1.0e3", "1.0E3", "1.5e3", "-.5e+3",  # UNSIGNED exponent — a string
    "1_0.5", "._5",  # `_` is a digit separator, but not in the leading position
    "nan", "inf", "1e5", "1.2.3",  # things a bare float() would swallow
)
_KNOWN_PYYAML_DIVERGENCES = {
    ".nan": "float nan in PyYAML; string here",
    ".inf": "float inf in PyYAML; string here",
    "-.inf": "float -inf in PyYAML; string here",
    "1:30.0": "90.0 in PyYAML (YAML 1.1 sexagesimal); string here",
}


def test_decimal_scalars_match_pyyaml_except_the_documented_forms():
    """Floats are resolved by YAML 1.1's rule, not by handing text to `float()`.

    `float()` accepts `nan`, `inf` and `1e5`, all of which PyYAML resolves as
    strings — so the loose version would trade one divergence from the parity
    invariant for three more.

    The sign rules are the subtle half, and they are asymmetric in a way no
    reasonable guess reproduces: the exponent's sign is REQUIRED (`1.0e+3` is a
    float, `1.0e3` a string), and a leading sign is allowed on `digits.digits`
    but not on `.digits` (`-0.5` is a float, `-.5` a string). That is why the
    pattern is transcribed from PyYAML's resolver rather than approximated —
    an earlier version hoisted the sign out of the alternation and silently
    diverged on all three of `+.5`, `-.5`, `-.5e+3`.

    Parity is asserted over the whole edge-case list rather than a couple of
    hand-picked values, and the known divergences are pinned as divergences — so
    closing one later fails this test instead of passing silently.
    """
    yaml = pytest.importorskip("yaml", reason="PyYAML absent — parity check skipped")

    for token in _FLOAT_EDGE_CASES:
        doc = f"v: {token}\n"
        assert kitconfig.loads(doc) == yaml.safe_load(doc), token

    for token, why in _KNOWN_PYYAML_DIVERGENCES.items():
        doc = f"v: {token}\n"
        assert kitconfig.loads(doc) != yaml.safe_load(doc), (
            f"{token} now agrees with PyYAML — good, but remove it from "
            f"_KNOWN_PYYAML_DIVERGENCES and from _coerce's docstring ({why})"
        )


# The resolved type of every edge case above. Duplicated deliberately: the
# parity test derives its expectation from PyYAML, this one states it outright,
# so a regression has to fool two independent descriptions of the same rule.
_EXPECTED_TYPES = {
    "2.5": float, "15": int, "1.": float, "0.0": float, "-0.0": float,
    "-0.5": float, "+1.5": float, ".5": float,
    "-.5": str, "+.5": str,          # sign not allowed on the .digits form
    "1.0e+3": float,                 # signed exponent
    "1.0e3": str, "1.0E3": str, "1.5e3": str, "-.5e+3": str,  # unsigned
    "1_0.5": float, "._5": str,      # `_` separates digits, cannot lead
    "nan": str, "inf": str, "1e5": str, "1.2.3": str,
    # The four forms where this reader deliberately departs from PyYAML — see
    # _KNOWN_PYYAML_DIVERGENCES. All stay strings here.
    ".nan": str, ".inf": str, "-.inf": str, "1:30.0": str,
}


def test_every_float_edge_case_has_a_declared_type():
    """The no-PyYAML assertions must cover every token the parity check does.

    The parity test walks TWO collections — the edge cases and the known
    divergences — so checking set-equality against only the first leaves the
    four divergent tokens with no coverage at all in a bare env. Those are the
    highest-risk ones: they are precisely where the implementation deliberately
    departs from PyYAML, so an accidental change there looks like a fix.
    """
    assert set(_EXPECTED_TYPES) == set(_FLOAT_EDGE_CASES) | set(
        _KNOWN_PYYAML_DIVERGENCES
    )


@pytest.mark.parametrize(
    "token", (*_FLOAT_EDGE_CASES, *_KNOWN_PYYAML_DIVERGENCES)
)
def test_decimal_scalars_keep_their_python_types_without_pyyaml(token: str):
    """The engines run with no PyYAML, so the parity test above skips in exactly
    the environment that matters most. This one never skips."""
    value = kitconfig.loads(f"v: {token}\n")["v"]

    assert isinstance(value, _EXPECTED_TYPES[token]), (token, value)
    assert not isinstance(value, bool)  # `15` must not arrive as True
    if token in _KNOWN_PYYAML_DIVERGENCES:
        # The divergent forms stay verbatim strings — assertable without PyYAML,
        # so it does not belong behind the parity test's importorskip.
        assert value == token


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

    # The disjointness property holds for ANY config and is the real subject.
    assert not (set(noise) & set(unavailable)), "markers must not appear in both lists"

    # Where a specific marker lives is adopter-owned. `_load_review_config`
    # documents `unavailable_markers: []` as supported, and `adopt.md` tells
    # adopters to run this suite against their own config — so assert this only
    # when the list is actually populated, rather than failing a legitimately
    # configured repo.
    if unavailable:
        assert "review skipped" in unavailable


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
