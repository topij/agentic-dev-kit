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

import os
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
    config = kitconfig.load_config(SHIPPED_CONFIG, overlay=False)
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
    [
        "handoff.md.tmpl",
        "handoff-history.md.tmpl",
        "friction-log.md.tmpl",
        "friction-log-archive.md.tmpl",
        "AGENTS.md.tmpl",
    ],
)
def test_narrative_templates_ship(name):
    """init.sh renders these; a missing one silently degrades adoption to an
    unrendered skeleton, which is the bug the templates were added to fix."""
    assert (REPO_ROOT / "docs" / "templates" / name).is_file()


def _production_first_line(doc):
    """The first line exactly as the two production consumers see it.

    read_BYTES, not read_text: read_text applies universal-newline translation,
    so a lone CR would end the line here but not for `head -n 1` — the same
    \r hazard kit_doctor.py was fixed for in panel round 3. Reading text and
    splitting on "\n" left the negative assertion below able to pass while
    ./init.sh would seed over the kit's own living plan (panel round 4).
    splitlines() is wrong for the same reason and eight more: it also breaks on
    \x0b \x0c \x1c \x1d \x1e \x85 U+2028 U+2029. Mirrors kit_doctor.py's
    predicate verbatim — if that changes, change this with it.
    """
    return doc.read_bytes().decode("utf-8", "replace").split("\n", 1)[0]


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
    # Pinned to LINE 1 specifically: init.sh's seed guard reads only the first
    # line, so a skeleton carrying the marker lower down is invisible to it and
    # the #8 failure returns silently — a green suite with every adopter back on
    # a `my-project` header. Proven reachable: moving this marker to line 3 left
    # the whole suite passing while init.sh reported the skeleton "already in
    # use" (panel round 2, correctness lens).
    assert "devkit-template: unrendered" in _production_first_line(doc), (
        f"{doc}: the marker must be on line 1 — init.sh's guard reads no further"
    )


def test_kits_own_plan_is_real_not_a_skeleton():
    """The flip side: this repo must actually practise Principle #1. A kit whose
    own living plan is an unrendered template is not dogfooding it.

    Checked on line 1, matching init.sh's guard and kit_doctor's: these records
    narrate the marker mechanism, and a plan that merely QUOTES the marker in
    prose is still a real plan, not a skeleton."""
    config = kitconfig.load_config(SHIPPED_CONFIG, overlay=False)
    for key in ("paths.handoff", "paths.friction_log"):
        doc = REPO_ROOT / kitconfig.get(config, key)
        assert "devkit-template: unrendered" not in _production_first_line(doc), doc
        assert "YYYY-MM-DD" not in doc.read_text(encoding="utf-8"), (
            f"{doc} still has placeholder dates"
        )


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
    config = kitconfig.load_config(SHIPPED_CONFIG, overlay=False)
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


# ── repo_root(): the marker walk, and its fallback ──────────────────────────
#
# `repo_root` had NO coverage at all before issue #60, which is how its
# docstring and its code came to disagree in plain sight: the docstring says
# walking up for a marker "rather than counting `parents[N]`" is what lets the
# kit be vendored at any depth and names `scripts/devkit/lib/` as the case —
# and the fallback then counted `parents[2]`, which is right only for the kit's
# OWN `scripts/lib/` depth. From `scripts/devkit/lib/` it returned
# `<repo>/scripts`, and `load_config` reported a missing config at a path that
# never existed.
#
# The layouts below are the two the kit prescribes (`scripts/lib/` for itself,
# `scripts/devkit/lib/` for /adopt) plus one deeper than either, so a future edit
# that reintroduces depth-arithmetic fails here rather than in an adopter.
#
# NOTE the `git=True, config=False` in the .git test. Planting BOTH markers makes
# the .git probe unobservable — the config fallback returns the same root, so
# deleting the .git probe outright leaves the test green. It did, and this test
# claimed to pin "at any depth" while pinning nothing.

def _tree(root: Path, rel: str, *, git: bool, config: bool) -> Path:
    """Build a fake checkout and return the `start` path for `repo_root`."""
    start = root / rel
    start.parent.mkdir(parents=True, exist_ok=True)
    start.write_text("# stand-in for kitconfig.py\n", encoding="utf-8")
    if git:
        (root / ".git").mkdir(exist_ok=True)
    if config:
        (root / "config").mkdir(exist_ok=True)
        (root / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    return start


@pytest.mark.parametrize(
    "layout",
    [
        "scripts/lib/kitconfig.py",          # the kit's own layout
        "scripts/devkit/lib/kitconfig.py",   # vendored — what /adopt prescribes on a name collision
        "tools/vendor/devkit/lib/kitconfig.py",  # arbitrary depth, per the docstring's promise
    ],
)
def test_repo_root_finds_the_git_marker_at_any_depth(tmp_path: Path, layout: str) -> None:
    # config=False so ONLY the .git probe can produce this answer.
    start = _tree(tmp_path, layout, git=True, config=False)
    assert kitconfig.repo_root(start) == tmp_path


@pytest.mark.parametrize(
    "layout",
    [
        "scripts/lib/kitconfig.py",
        "scripts/devkit/lib/kitconfig.py",
        "tools/vendor/devkit/lib/kitconfig.py",
    ],
)
def test_repo_root_accepts_a_git_file_as_a_linked_worktree_marker(
    tmp_path: Path, layout: str
) -> None:
    """`.git` is a FILE in a linked worktree, which the docstring promises to
    handle. `.exists()` covers it and `.is_dir()` would not — and nothing pinned
    that, so the distinction survived only as prose."""
    start = _tree(tmp_path, layout, git=False, config=False)
    (tmp_path / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n", encoding="utf-8")
    assert kitconfig.repo_root(start) == tmp_path


@pytest.mark.parametrize(
    "layout, root_index",
    [
        ("scripts/lib/kitconfig.py", 2),         # the kit's own — arithmetic is right
        ("scripts/devkit/lib/kitconfig.py", 3),  # vendored — arithmetic is WRONG here
    ],
)
def test_repo_root_without_git_is_depth_arithmetic_and_stays_inside_the_tree(
    tmp_path: Path, layout: str, root_index: int
) -> None:
    """Pins the KNOWN LIMITATION of issue #60, not a fix for it.

    With no `.git`, resolution is `parents[2]`. For the kit's own layout that is
    the root; for the vendored layout it is `<root>/scripts` — wrong, and the
    caller then fails naming a path that does not exist. Asserted explicitly so
    the limitation is visible in the suite rather than discovered by an adopter.

    The property that must hold in BOTH cases is the one below: the answer stays
    inside the tree. A config-marker probe was tried twice to fix the vendored
    case and escaped into a parent project both times.
    """
    start = _tree(tmp_path, layout, git=False, config=True)
    resolved = kitconfig.repo_root(start)

    assert resolved == start.parents[2]
    assert resolved == tmp_path or tmp_path in resolved.parents

    if root_index != 2:  # the vendored case: wrong, and loud about it
        assert resolved != tmp_path
        with pytest.raises(FileNotFoundError):
            kitconfig.load_config(resolved / "config" / "dev-model.yaml")


def test_repo_root_never_escapes_into_a_parent_projects_config(tmp_path: Path) -> None:
    """The foreign config is the IMMEDIATE parent — no padding directory.

    This is the shape both removed probes escaped on. The first version walked
    to `/`; the second was bounded to the deepest prescribed layout, which still
    reaches one above the root in the shallowest one. The earlier test for this
    had a spare `releases/` level that pushed the foreign config just past the
    bound, so it passed while the real case escaped — the padding was the bug in
    the test.
    """
    outer = tmp_path / "outer"
    (outer / "config").mkdir(parents=True)
    (outer / "config" / "dev-model.yaml").write_text(
        "kit:\n  version: 2\npaths:\n  handoff: FOREIGN.md\n", encoding="utf-8"
    )
    inner = outer / "inner"
    start = _tree(inner, "scripts/lib/kitconfig.py", git=False, config=False)

    resolved = kitconfig.repo_root(start)
    assert resolved != outer, "escaped into the parent project's config"
    assert resolved == inner


def test_repo_root_resolves_a_nested_checkout_to_its_own_root(tmp_path: Path) -> None:
    """A checkout nested inside another project resolves to ITS root.

    An earlier version of this docstring claimed to pin the ORDER of two probes.
    There is only one probe now — the config-marker probe it referred to was
    removed — so the claim would have been describing a mechanism that no longer
    exists. It also never held: a review showed that swapping the two loops left
    the whole suite green, because this fixture's layout put the outer config
    outside the probe's reach, making the ordering unobservable in exactly the
    case chosen to demonstrate it.

    What it pins now is narrower and true: `.git` on the inner checkout wins over
    anything the outer project has, at a vendored depth.
    """
    outer = tmp_path / "outer"
    (outer / "config").mkdir(parents=True)
    (outer / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    inner = outer / "vendor" / "inner"
    start = _tree(inner, "scripts/devkit/lib/kitconfig.py", git=True, config=False)
    assert kitconfig.repo_root(start) == inner


def test_repo_root_last_resort_when_neither_marker_exists(tmp_path: Path) -> None:
    """Neither marker: nothing better is knowable, so the arithmetic stands."""
    start = _tree(tmp_path, "scripts/lib/kitconfig.py", git=False, config=False)
    assert kitconfig.repo_root(start) == tmp_path


def test_archive_plan_sessions_reports_a_missing_config_instead_of_crashing(tmp_path: Path) -> None:
    """The config-resolution handler must report, not raise.

    `archive_plan_sessions.py` listed `yaml.YAMLError` in this handler's `except`
    tuple with no `yaml` import. Python evaluates that tuple only when an
    exception actually arrives, so EVERY failure on this path raised
    `NameError: name 'yaml' is not defined` from inside the handler written to
    report the error cleanly — masking the real cause. Found by the ruff pass
    added alongside this test (F821); nothing in the suite covered it.

    Run from a copied tree with no `config/dev-model.yaml`: the script resolves
    its root at import time, so an in-place run would find the kit's own config
    and never reach the handler.
    """
    import subprocess

    (tmp_path / "scripts" / "lib").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    # Every module the engine imports at load time. `atomic_write` joined this
    # list with #164 — omit it and the copied tree tracebacks on the import
    # rather than reaching the handler under test, which is a false pass waiting
    # to become a false failure.
    for rel in (
        "scripts/archive_plan_sessions.py",
        "scripts/lib/kitconfig.py",
        "scripts/lib/atomic_write.py",
    ):
        (tmp_path / rel).write_bytes((REPO_ROOT / rel).read_bytes())

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(tmp_path / "scripts" / "archive_plan_sessions.py"), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert "NameError" not in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr
    assert result.returncode == 2, f"rc={result.returncode}\n{result.stderr}"
    assert "could not resolve configured handoff paths" in result.stderr


# ── Local config overlay ──────────────────────────────────────────────────────
#
# `load_config()` merges a gitignored `config/dev-model.local.yaml` over the
# tracked file, so a value that must not enter git (an operator's DM id, a
# tracker team id) can be supplied without committing it. These pin the merge
# semantics — the failure that matters is an overlay silently NOT applying, which
# reads exactly like a correctly-configured repo until a workflow targets the
# wrong person.


def _config_tree(tmp_path: Path, tracked: str, overlay: str | None = None) -> Path:
    """A minimal repo root holding a tracked config and optionally an overlay."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".git").mkdir()
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "dev-model.yaml").write_text(tracked, encoding="utf-8")
    if overlay is not None:
        (cfg_dir / "dev-model.local.yaml").write_text(overlay, encoding="utf-8")
    return cfg_dir / "dev-model.yaml"


def test_overlay_absent_is_silent_and_returns_the_tracked_file(tmp_path):
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n  backend: slack\n')
    config = kitconfig.load_config(path)
    assert kitconfig.get(config, "notify.user_key") == ""
    assert kitconfig.get(config, "notify.backend") == "slack"


def test_overlay_value_wins_over_the_tracked_blank(tmp_path):
    path = _config_tree(
        tmp_path,
        'notify:\n  user_key: ""\n  backend: slack\n',
        'notify:\n  user_key: "U0LOCAL123"\n',
    )
    config = kitconfig.load_config(path)
    assert kitconfig.get(config, "notify.user_key") == "U0LOCAL123"


def test_overlay_merges_per_leaf_and_does_not_drop_siblings(tmp_path):
    """The regression this guards: a shallow merge replaces the whole `notify`
    map, silently deleting `backend` because the overlay only mentioned one key."""
    path = _config_tree(
        tmp_path,
        'notify:\n  user_key: ""\n  backend: slack\n'
        'tracker:\n  backend: github-issues\n  linear:\n    team_id: ""\n',
        'notify:\n  user_key: "U0LOCAL123"\n',
    )
    config = kitconfig.load_config(path)
    assert kitconfig.get(config, "notify.backend") == "slack"
    assert kitconfig.get(config, "tracker.backend") == "github-issues"
    assert kitconfig.get(config, "tracker.linear.team_id") == ""


def test_overlay_merges_nested_maps_rather_than_replacing_them(tmp_path):
    path = _config_tree(
        tmp_path,
        'notify:\n  backend: slack\n  user_key: ""\n',
        'notify:\n  user_key: "U0LOCAL"\n',
    )
    config = kitconfig.load_config(path)
    assert kitconfig.get(config, "notify.user_key") == "U0LOCAL"
    assert kitconfig.get(config, "notify.backend") == "slack"


def test_deep_merge_replaces_a_list_rather_than_appending():
    """`_deep_merge` replaces lists so an overlay could express "none of these"
    rather than only ever adding.

    Pinned directly on `_deep_merge`, not through `load_config`: nothing in
    OVERLAYABLE_PREFIXES is a list, so no overlay can reach this today. The
    previous version of this test claimed `review.bots: []` as its motivation —
    a key the same file asserts can never be set (panel, correctness lens). Kept
    because the merge is general and the allowlist may widen."""
    problems: list[str] = []
    out = kitconfig._deep_merge({"a": [1, 2, 3]}, {"a": []}, "", problems)
    assert out["a"] == []
    assert problems == []


def test_missing_tracked_file_still_raises_even_with_an_overlay_present(tmp_path):
    """The overlay supplies values, never the schema — it must not stand in for
    an absent tracked config and let an engine run on a partial map."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "dev-model.local.yaml").write_text(
        'notify:\n  user_key: "U0LOCAL123"\n', encoding="utf-8"
    )
    with pytest.raises(FileNotFoundError):
        kitconfig.load_config(tmp_path / "config" / "dev-model.yaml")


def test_malformed_overlay_raises_rather_than_being_ignored(tmp_path):
    """Fail loud. A silently-skipped overlay is the failure mode this whole
    feature has to avoid: the workflow runs, targets the tracked blank, and
    nothing says the local value never applied."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', "- just\n- a list\n")
    with pytest.raises(ValueError, match="produced no keys"):
        kitconfig.load_config(path)


def test_comments_only_overlay_is_legitimately_empty(tmp_path):
    """The counterpart to the test above: an overlay a user has commented out is
    not malformed, and must not become a hard error on every engine start."""
    path = _config_tree(
        tmp_path,
        'notify:\n  user_key: "tracked"\n',
        "# notify:\n#   user_key: \"U0LOCAL123\"\n\n",
    )
    config = kitconfig.load_config(path)
    assert kitconfig.get(config, "notify.user_key") == "tracked"


def test_overlay_with_no_colon_produces_no_keys_and_fails_loudly(tmp_path):
    """A line with no colon parses to nothing at all. Renamed from
    ...indented_wrong...: a review lens showed the old name and docstring promised
    two scenarios (a lost top-level key, a wrong indent) that this input is
    neither of, and that BOTH were silent no-ops in the implementation. They are
    now covered by their own tests below."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', 'user_key "U0LOCAL123"\n')
    with pytest.raises(ValueError, match="produced no keys"):
        kitconfig.load_config(path)


# The cases below were all silent in the first version of this feature. Two were
# worse than silent: they DELETED tracked config. Found by both panel lenses.


def test_overlay_key_absent_from_the_tracked_config_is_an_error(tmp_path):
    """The overlay supplies values for keys the tracked file declares; it is not
    the schema. A key with no counterpart applies cleanly to nothing."""
    path = _config_tree(
        tmp_path, 'notify:\n  user_key: ""\n', 'notifiy:\n  user_key: "U0LOCAL123"\n'
    )
    with pytest.raises(ValueError, match="no such key"):
        kitconfig.load_config(path)


def test_overlay_typo_in_a_leaf_key_is_an_error(tmp_path):
    path = _config_tree(
        tmp_path, 'notify:\n  user_key: ""\n', 'notify:\n  usr_key: "U0LOCAL123"\n'
    )
    with pytest.raises(ValueError, match="notify.usr_key"):
        kitconfig.load_config(path)


def test_overlay_dotted_key_written_flat_is_an_error(tmp_path):
    """`notify.user_key: "…"` is a natural thing to write and parses as one
    top-level key with a dot in it — which matches nothing and silently did."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', 'notify.user_key: "U0LOCAL"\n')
    with pytest.raises(ValueError, match="no such key"):
        kitconfig.load_config(path)


def test_tab_indented_overlay_is_an_error_and_does_not_wipe_the_block(tmp_path):
    """Tabs do not indent YAML. The child parsed as a sibling, leaving the parent
    valueless — which then REPLACED the tracked block, deleting `notify.backend`.
    The docstring promised sibling preservation while this route silently broke
    it (panel, both lenses)."""
    path = _config_tree(
        tmp_path,
        'notify:\n  backend: slack\n  user_key: ""\n',
        'notify:\n\tuser_key: "U0LOCAL123"\n',
    )
    with pytest.raises(ValueError, match="cannot replace"):
        kitconfig.load_config(path)


def test_overlay_with_its_only_child_commented_out_is_an_error(tmp_path):
    """The operator comments out the leaf but leaves the parent — a valueless
    parent that would wipe the tracked block."""
    path = _config_tree(
        tmp_path,
        'notify:\n  backend: slack\n  user_key: ""\n',
        'notify:\n  # user_key: "U0LOCAL123"\n',
    )
    with pytest.raises(ValueError, match="cannot replace"):
        kitconfig.load_config(path)


def test_overlay_flow_mapping_is_an_error(tmp_path):
    """`notify: {user_key: "…"}` parses to a STRING under this reader, which
    would replace the whole tracked block with that string."""
    path = _config_tree(
        tmp_path,
        'notify:\n  backend: slack\n  user_key: ""\n',
        'notify: {user_key: "U0LOCAL123"}\n',
    )
    with pytest.raises(ValueError, match="cannot replace"):
        kitconfig.load_config(path)


def test_structural_only_overlay_is_legitimately_empty(tmp_path):
    """`---`, `{}` and `null` are valid ways to write an intentionally-empty
    overlay. The first version of the guard rejected all three (panel)."""
    for i, body in enumerate(("---\n", "{}\n", "null\n")):
        path = _config_tree(tmp_path / f"case{i}", 'notify:\n  user_key: "kept"\n', body)
        config = kitconfig.load_config(path)
        assert kitconfig.get(config, "notify.user_key") == "kept"


def test_unreadable_overlay_raises_rather_than_falling_back(tmp_path):
    """The docstring says an overlay that exists but cannot be applied raises. A
    surviving mutant showed that an `except OSError: return config` would let the
    feature regress to fail-open with a green suite (panel, adversarial)."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', 'notify:\n  user_key: "x"\n')
    overlay = path.with_name("dev-model.local.yaml")
    overlay.chmod(0o000)
    try:
        if os.access(overlay, os.R_OK):  # running as root — the chmod is a no-op
            pytest.skip("cannot make a file unreadable as this user")
        with pytest.raises(OSError):
            kitconfig.load_config(path)
    finally:
        overlay.chmod(0o644)


# ── The overlay allowlist ─────────────────────────────────────────────────────
#
# Round 2 of the panel found the general overlay produced divergence: only
# kitconfig merges it, while dev_session.sh, reconcile_sessions.sh and the
# pre-push hook read the tracked file directly. An overlay on a key THEY read
# applies in Python and silently does not in sh — the exact failure the overlay
# exists to prevent. These pin the narrowing.


def test_overlay_cannot_set_a_key_the_shell_readers_consume(tmp_path):
    """`vcs.dev_branch_prefix` is read by the pre-push hook's own snippet. An
    overlay on it left that guard matching a prefix nothing is named, so a hard
    stop CLAUDE.md relies on failed open."""
    path = _config_tree(
        tmp_path, "vcs:\n  dev_branch_prefix: dev\n", 'vcs:\n  dev_branch_prefix: "lane"\n'
    )
    with pytest.raises(ValueError, match="not overlayable"):
        kitconfig.load_config(path)


def test_overlay_cannot_wipe_a_tracked_list(tmp_path):
    """The regression this closes: `review:` with `bots:` left blank made
    `review.bots` None, and pr_watch then fell back to its built-in default with
    the tracked review gate silently narrowed. Now unreachable two ways over —
    review.* is not overlayable, and None never replaces a tracked value."""
    path = _config_tree(tmp_path, "review:\n  bots: [coderabbit]\n", "review:\n  bots:\n")
    with pytest.raises(ValueError, match="not overlayable"):
        kitconfig.load_config(path)


def test_none_never_replaces_a_tracked_value_even_on_an_overlayable_key(tmp_path):
    """The allowlist and the None-guard are independent; this pins the second one
    on a key the first one permits, so neither alone is load-bearing."""
    path = _config_tree(
        tmp_path, 'tracker:\n  labels: [bug]\n  url: "x"\n', "tracker:\n  labels:\n"
    )
    with pytest.raises(ValueError, match="cannot replace"):
        kitconfig.load_config(path)


def test_overlay_cannot_replace_a_plain_value_with_a_block(tmp_path):
    """The mirror of the block-over-value rule. Left unguarded, a workflow gets a
    dict where it expects a Slack id."""
    path = _config_tree(
        tmp_path, 'notify:\n  user_key: ""\n', 'notify:\n  user_key:\n    slack_id: "U0"\n'
    )
    with pytest.raises(ValueError, match="cannot replace a plain value"):
        kitconfig.load_config(path)


def test_overlay_false_reads_the_tracked_file_alone(tmp_path):
    """Tests asserting about the SHIPPED config need this: without it a
    developer's own gitignored overlay turns the suite red on their machine while
    CI stays green, against a repo whose CLAUDE.md names `make test` as *the*
    verification command."""
    path = _config_tree(
        tmp_path, 'notify:\n  user_key: "tracked"\n', 'notify:\n  user_key: "local"\n'
    )
    assert kitconfig.get(kitconfig.load_config(path), "notify.user_key") == "local"
    assert kitconfig.get(kitconfig.load_config(path, overlay=False), "notify.user_key") == "tracked"


def test_bare_notify_and_bare_tracker_both_reach_the_useful_guard(tmp_path):
    """The ancestor clause admits a parent of an overlayable key so the block/None
    guard can speak, instead of a bare "not overlayable".

    It was asymmetric: `"tracker".startswith("tracker.")` is False, so a bare
    `tracker:` got the unhelpful message while `notify:` got the useful one — and
    BOTH mutants of the clause survived the suite, so nothing pinned either
    direction (panel, adversarial lens)."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', "notify:\n")
    with pytest.raises(ValueError, match="cannot replace a value"):
        kitconfig.load_config(path)


def test_overlay_block_whose_children_did_not_parse_is_an_error(tmp_path):
    """A child that lost its colon leaves an empty block, which merged as a clean
    no-op — the overlay silently applied nothing (panel, adversarial lens)."""
    path = _config_tree(tmp_path, 'notify:\n  user_key: ""\n', 'notify:\n  user_key "U0LOCAL"\n')
    with pytest.raises(ValueError, match="sets nothing"):
        kitconfig.load_config(path)


def test_overlay_dangling_yaml_token_is_an_error(tmp_path):
    """A bare `|` or `>` lands verbatim as the value — worse than a no-op, since a
    workflow then acts on the literal token."""
    for token in ("|", ">"):
        path = _config_tree(
            tmp_path / f"t{ord(token)}", 'notify:\n  user_key: ""\n', f"notify:\n  user_key: {token}\n"
        )
        with pytest.raises(ValueError, match="bare YAML token"):
            kitconfig.load_config(path)


def test_tracker_is_not_overlayable(tmp_path):
    """`tracker.*` was overlayable and was removed. Eight agent-facing docs tell the
    agent to read `config/dev-model.yaml` directly, so hiding the values in the
    overlay made `session-start` on this repo query a project literally named
    "My Project Dev" (panel, adversarial lens). Also `tracker.backend` is a setting,
    not an identity — it failed the allowlist's own stated criterion."""
    path = _config_tree(
        tmp_path, 'tracker:\n  backend: linear\n', "tracker:\n  backend: github-issues\n"
    )
    with pytest.raises(ValueError, match="not overlayable"):
        kitconfig.load_config(path)
