"""Fixture harness for init.sh's uncovered paths (issue #84).

test_portability.py covers the config-MIGRATION path (corruption across real
config shapes, idempotency, per-key guards). This file covers the paths those
fixtures never reach:

- ``detect_engines_dir()`` layout detection — issue #67's home
- prompt re-stamping with hostile values — issue #62 part 1's home. No pty is
  needed: ``ask()`` keeps the current value when stdin is not a tty, and every
  kept value is re-stamped through ``set_field``, so a plain non-interactive
  re-run drives the whole write path over whatever the config already holds.
- ``set_field``'s awk value handling — issue #62 part 2's home, driven directly
  via the same sed-extraction the Makefile's install-hooks target uses
- narrative-doc seeding and the unrendered-marker guard
- ``.gitignore`` appends
- ``install_hooks()`` — default hooks dir, repo-local ``core.hooksPath``, and
  the not-a-kit-shim guard. #66's ``core.hooksPath = ~/…`` case is out of scope
  until the #61 design call settles the fix shape.

The #62/#67 defect reproductions landed as ``xfail(strict=True)`` and were
flipped to plain pins by the change that closed those issues — they now guard
against regression like any other test here.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from _repo_layout import engine_dir, find_repo_root

# Every test here asserts on `init.sh`'s behaviour, and an adopter who
# vendored engines and config has no `init.sh` to assert about. Repairing
# the paths would only turn FileNotFoundError into a differently-worded
# failure — #134 cause 2 says the honest handling is a skip, not a fix.
pytestmark = pytest.mark.kit_repo_only("init.sh")


ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

def locale_where_nbsp_is_blank() -> str | None:
    """An installed locale under which the SHELL's `[[:space:]]` matches U+00A0,
    or None if this machine has none.

    Not "a UTF-8 locale" and not a hardcoded `en_US.UTF-8`: an uninstalled
    locale name silently falls back to C, where `[[:space:]]` is ASCII-only —
    so the test below would pass with the pin it exists to check REMOVED, in
    exactly the minimal CI containers most likely to lack the locale. The probe
    asks the shell the actual question instead of assuming an answer from the
    locale's name.
    """
    try:
        installed = subprocess.run(
            ["locale", "-a"], capture_output=True, text=True, check=True
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return None
    for name in installed:
        if "utf" not in name.lower():
            continue
        probe = subprocess.run(
            ["sh", "-c", 'case "$1" in [[:space:]]*) exit 0 ;; esac; exit 1', "sh", " "],
            env=dict(os.environ, LC_ALL=name, LANG=name),
            capture_output=True,
        )
        if probe.returncode == 0:
            return name
    return None


def kit_own_marker() -> str:
    """`init.sh`'s KIT_OWN_MARKER literal, read at CALL time.

    Derived rather than restated: a copy here would keep passing after the
    literal was renamed in init.sh — assertion and code agreeing about a string
    nothing looks for any more. Derived, a rename fails the shipped files that
    still carry the old one, which is the failure that matters.

    Call time, not module scope, for the reason `shipped_config()` gives below:
    a read that raises during COLLECTION aborts the whole pytest session and
    takes unrelated modules down with it (#226/#233), long before
    `kit_repo_only` is consulted."""
    text = (REPO_ROOT / "init.sh").read_text(encoding="utf-8")
    match = re.search(r'^KIT_OWN_MARKER="([^"]+)"', text, re.MULTILINE)
    assert match, "KIT_OWN_MARKER is not assigned in init.sh — was it renamed?"
    return match.group(1)


def shipped_config() -> str:
    """The kit's own `config/dev-model.yaml`, read at CALL time.

    This was a module-scope `read_text()`. Wherever `REPO_ROOT` resolves wrong —
    a nested engines directory in a tree with no `.git`, which #233 records as
    not resolvable — it raised during COLLECTION, so pytest aborted the whole
    session and ran zero tests, taking unrelated modules down with it. That is
    #226's failure class in a second module, and the reason the `kit_repo_only`
    marker cannot help: the exception fires at import, long before any marker is
    consulted. Correctness lens, PR #232 round 3.
    """
    return (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")

# A v1-schema config with no `paths.engines`, so a run must call
# detect_engines_dir() to stamp it — the same shape test_portability.py migrates.
V1_CONFIG = """project:
  name: sized-down
paths:
  handoff: docs/handoff.md
  handoff_history: docs/handoff-history.md
  friction_log: docs/friction-log.md
  friction_log_archive: docs/friction-log-archive.md
doc_budgets: []
vcs:
  protected_branch: main
tracker:
  backend: none
  project_name: "X"
  linear:
    team_id: ""
    project_id: ""
review:
  bots: []
  fallback_command: "/code-review"
notify:
  user_key: ""
models:
  cheap: haiku
  default: sonnet
  expensive: opus
state:
  dirname: state
"""


def _env(ceiling: Path) -> dict[str, str]:
    # Isolate from the developer's own git context three ways (all found by the
    # adversarial review lens on this change):
    # - null the global/system config: a global core.hooksPath would redirect a
    #   fixture's hook install into their real hooks directory;
    # - a discovery ceiling, so a git=False fixture can never resolve a repo
    #   enclosing pytest's tmp dir. No current fixture pairs git=False with a
    #   hooks source, so this is prophylactic — but with one added by hand,
    #   install_hooks demonstrably wrote a shim into the enclosing repo's live
    #   .git/hooks;
    # - drop an inherited GIT_DIR/GIT_WORK_TREE, which an explicit ceiling does
    #   not override.
    env = dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_CEILING_DIRECTORIES=str(ceiling),
    )
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _fixture(
    tmp_path: Path,
    *,
    config: str,
    manifest: bool = False,
    templates: bool = False,
    git: bool = False,
    hooks: bool = False,
) -> Path:
    repo = tmp_path / "project"
    (repo / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "init.sh", repo / "init.sh")
    (repo / "config" / "dev-model.yaml").write_text(config, encoding="utf-8")
    if manifest:
        shutil.copy2(REPO_ROOT / "kit-manifest.json", repo / "kit-manifest.json")
    if templates:
        (repo / "docs" / "templates").mkdir(parents=True)
        for tmpl in (REPO_ROOT / "docs" / "templates").glob("*.tmpl"):
            shutil.copy2(tmpl, repo / "docs" / "templates" / tmpl.name)
    if hooks:
        # Place the hook where the config THIS fixture just wrote says the
        # engines are, not at a literal `scripts/` (#134). `install_hooks()`
        # resolves the same key, so a hardcoded destination builds a fake repo
        # that contradicts its own config: under a `scripts/devkit` config the
        # hook was written to `scripts/` and init.sh correctly found nothing,
        # failing three tests for a reason that had nothing to do with hooks.
        engines = (yaml.safe_load(config).get("paths") or {}).get("engines") or "scripts"
        target = repo / engines / "hooks" / "pre-push"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ENGINE_DIR / "hooks" / "pre-push", target)
    if git:
        subprocess.run(
            ["git", "init", "-q"], cwd=repo, check=True, env=_env(tmp_path), capture_output=True
        )
    return repo


def _run_init(repo: Path) -> subprocess.CompletedProcess[str]:
    # stdin explicitly closed so ask() keeps defaults even when the test runner
    # itself is attached to a terminal.
    return subprocess.run(
        ["sh", "init.sh"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=_env(repo.parent),
    )


def _config(repo: Path) -> str:
    return (repo / "config" / "dev-model.yaml").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# detect_engines_dir — layout detection (#67)
# --------------------------------------------------------------------------- #
# The no-engines-anywhere fallback (`engines: scripts`) is already pinned by
# test_portability.py's test_init_migrates_the_previous_runtime_schema.


def test_engines_detection_finds_namespaced_layout(tmp_path: Path) -> None:
    """A vendored scripts/devkit/ layout holding a primary engine is detected."""
    repo = _fixture(tmp_path, config=V1_CONFIG)
    engine = repo / "scripts" / "devkit" / "pr_watch.py"
    engine.parent.mkdir(parents=True)
    engine.write_text("# engine\n", encoding="utf-8")

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts/devkit"


def test_engines_detection_prefers_scripts_when_engines_live_there(tmp_path: Path) -> None:
    """Candidate order: with engines present in BOTH scripts/ and scripts/devkit/,
    the kit's own layout wins. (Both populated on purpose — with only one, any
    candidate order passes and the test pins nothing; found by both review
    lenses on this change.)"""
    repo = _fixture(tmp_path, config=V1_CONFIG, manifest=True)
    for candidate in ("scripts", "scripts/devkit"):
        engine = repo / candidate / "pr_watch.py"
        engine.parent.mkdir(parents=True, exist_ok=True)
        engine.write_text("# engine\n", encoding="utf-8")

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts"


def test_engines_detection_sized_down_install(tmp_path: Path) -> None:
    """A sized-down install (kit_doctor.py + lib/kitconfig.py only) is detected.
    The fix (#67) reads the probe list from kit-manifest.json (role == engine,
    filtered to top-level names) — the generated projection of KIT_OWNED,
    kit_doctor's probe source since #59, and the one form of it sh can read —
    which this fixture supplies; before it,
    a hardcoded probe triple fell through and stamped `engines: scripts`. The
    test pins the detection OUTCOME only: it cannot see where a probe list came
    from, so the single-source property itself is #47's to enforce."""
    repo = _fixture(tmp_path, config=V1_CONFIG, manifest=True)
    for rel in ("kit_doctor.py", "lib/kitconfig.py"):
        path = repo / "scripts" / "devkit" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# engine\n", encoding="utf-8")

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts/devkit"


def test_engines_detection_not_fooled_by_generic_lib_names(tmp_path: Path) -> None:
    """lib/ entries are excluded from the detection probe: their basenames are
    generic, so an adopter's own scripts/lib/repo_root.sh would otherwise make
    `scripts` shadow a kit vendored at scripts/devkit — a false positive the
    3-name probe never had (panel, #87)."""
    repo = _fixture(tmp_path, config=V1_CONFIG, manifest=True)
    adopters_own = repo / "scripts" / "lib" / "repo_root.sh"
    adopters_own.parent.mkdir(parents=True)
    adopters_own.write_text("# the adopter's own helper\n", encoding="utf-8")
    for rel in ("pr_watch.py", "kit_doctor.py"):
        engine = repo / "scripts" / "devkit" / rel
        engine.parent.mkdir(parents=True, exist_ok=True)
        engine.write_text("# engine\n", encoding="utf-8")

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts/devkit"


def test_degraded_manifest_warns_and_falls_back(tmp_path: Path) -> None:
    """A present-but-unparseable manifest must not silently resurrect the #67
    misdetection: the fallback triple still detects the layout it always could,
    and stderr says the manifest was unreadable (panel, #87)."""
    repo = _fixture(tmp_path, config=V1_CONFIG)
    (repo / "kit-manifest.json").write_text("", encoding="utf-8")
    engine = repo / "scripts" / "devkit" / "pr_watch.py"
    engine.parent.mkdir(parents=True)
    engine.write_text("# engine\n", encoding="utf-8")

    proc = _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts/devkit"
    assert "no engine entries could be read" in proc.stderr


# --------------------------------------------------------------------------- #
# prompt re-stamping — the #62 write path
# --------------------------------------------------------------------------- #


def _shipped_with_name(name_value: str) -> str:
    """Swap `project.name` in the shipped config, whatever it currently holds.

    This used to match the literal `  name: my-project\\n`. That coupled twelve
    tests to the config being *unstamped*: the moment a repo set its own project
    name — which every adopter does, and which this repo did — they all failed on
    a needle assertion rather than on anything they test. These tests ship to
    adopters, so the fixture has to be value-independent.
    """
    # The replacement is a FUNCTION, not a string: `re.sub` interprets backslash
    # escapes in a string replacement, so a hostile value like `Acme\nCo` — which
    # this fixture exists to feed through init.sh — would arrive as a real
    # newline and silently test the wrong thing. Caught by
    # test_render_preserves_backslashes_in_values.
    pattern = re.compile(r"^  name: .*$", re.M)
    # No `count=` cap: capping at 1 would make the assertion below unable to fire
    # on a duplicate, which is exactly what it claims to guard (panel, correctness).
    replaced, count = pattern.subn(lambda _m: f"  name: {name_value}", shipped_config())
    assert count == 1, (
        f"expected exactly one `  name:` line under project: in the shipped config, found {count}"
    )
    return replaced


def _shipped_with_tracker_url(url_value: str) -> str:
    """Swap `tracker.url`, whatever it currently holds — same reasoning as
    `_shipped_with_name`, and the same function-replacement rule for backslashes."""
    pattern = re.compile(r"^  url: .*$", re.M)
    # No `count=` cap: capping at 1 would make the assertion below unable to fire
    # on a duplicate, which is exactly what it claims to guard (panel, correctness).
    replaced, count = pattern.subn(lambda _m: f"  url: {url_value}", shipped_config())
    assert count == 1, (
        f"expected exactly one `  url:` line under tracker: in the shipped config, found {count}"
    )
    return replaced


def test_rerun_on_shipped_config_preserves_every_value_and_is_stable(tmp_path: Path) -> None:
    """A non-interactive re-run over the shipped config must change no value,
    and a further re-run must be byte-identical (the documented upgrade path).
    The bots byte-assertion pins the quoted-item list serialization — value
    equality alone let a revert to unquoted items survive (panel, #87)."""
    repo = _fixture(tmp_path, config=shipped_config())

    _run_init(repo)
    once = _config(repo)
    assert yaml.safe_load(once) == yaml.safe_load(shipped_config())
    assert 'bots: ["coderabbit"]' in once

    _run_init(repo)
    assert _config(repo) == once


def _rerun_and_reload(tmp_path: Path, name_value: str) -> tuple[Path, str, dict]:
    """Fixture + one non-interactive run over the shipped config with
    project.name set to `name_value`; returns (repo, config text, parsed)."""
    repo = _fixture(tmp_path, config=_shipped_with_name(name_value))
    _run_init(repo)
    text = _config(repo)
    return repo, text, yaml.safe_load(text)


def test_rerun_preserves_name_with_interior_double_quote(tmp_path: Path) -> None:
    """A plain scalar containing double quotes is stamped RAW, exactly as main
    always did — blanket quoting turned it into unloadable YAML, taking every
    PyYAML consumer down (panel, #87). Lossless double-quoting of `"` would
    need escape support get_field does not have."""
    repo, text, parsed = _rerun_and_reload(tmp_path, 'he said "hi" ok')

    assert parsed["project"]["name"] == 'he said "hi" ok'
    assert '  name: he said "hi" ok\n' in text
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_preserves_name_with_backslashes_for_both_readers(tmp_path: Path) -> None:
    """A value containing backslashes is stamped RAW: double-quoting it makes
    YAML interpret the backslashes as escapes while kitconfig reads them
    literally — an unloadable config or a reader split-brain (panel, #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, r"C:\proj\new")

    assert parsed["project"]["name"] == r"C:\proj\new"
    import kitconfig  # noqa: PLC0415

    assert kitconfig.loads(text)["project"]["name"] == r"C:\proj\new"
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_preserves_single_quoted_name(tmp_path: Path) -> None:
    """A value already in single-quoted style is left in it (stamped raw) —
    re-wrapping it in double quotes corrupted the value to literal `'…'`
    (panel, #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, "'Acme Co'")

    assert parsed["project"]["name"] == "Acme Co"
    assert "  name: 'Acme Co'\n" in text
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_keeps_apostrophe_value_and_its_comment(tmp_path: Path) -> None:
    """A mid-scalar apostrophe is literal, not an opening quote: the earlier
    scan treated it as one, decided the trailing `#` was 'inside quotes', and
    absorbed the line's real comment into the value (panel, #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, "O'Brien kit  # keep this comment")

    assert parsed["project"]["name"] == "O'Brien kit"
    assert "  name: O'Brien kit  # keep this comment\n" in text
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_preserves_midword_hash(tmp_path: Path) -> None:
    """`a#b` is one plain-scalar token — YAML (and kitconfig) open a comment
    only after whitespace. The old blind index() truncated it (panel, #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, "a#b")

    assert parsed["project"]["name"] == "a#b"
    _run_init(repo)
    assert _config(repo) == text


# The Makefile's install-hooks target established this pattern: extract one
# function straight out of init.sh, so the test always drives current logic.
_YAML_SCALAR_DRIVER = """eval "$(sed -n '/^yaml_scalar() {/,/^}/p' init.sh)"
yaml_scalar "$1"
"""


def _yaml_scalar_extra_cases() -> list[tuple[str, str]]:
    # Reserved leading indicators where double-quoting is lossless and a raw
    # stamp is unloadable or type-flipped YAML (panel round 2 on #87).
    return [
        ("`my-proj`", '"`my-proj`"'),
        ("?x", '"?x"'),
        (",x", '",x"'),
        ("]x", '"]x"'),
        ("}x", '"}x"'),
    ]


@pytest.mark.parametrize(("value", "stamped"), _yaml_scalar_extra_cases())
def test_yaml_scalar_quotes_reserved_leading_indicators(
    tmp_path: Path, value: str, stamped: str
) -> None:
    (tmp_path / "init.sh").write_bytes((REPO_ROOT / "init.sh").read_bytes())
    proc = subprocess.run(
        ["sh", "-c", _YAML_SCALAR_DRIVER, "_", value],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout == stamped + "\n"


_QUOTED_SCALAR_DRIVER = """eval "$(sed -n '/^quoted_scalar() {/,/^}/p' init.sh)"
quoted_scalar "$1"
"""


@pytest.mark.parametrize(
    ("value", "stamped"),
    [
        ("My Project Dev", '"My Project Dev"'),
        ("", '""'),
        (r"x\py", r"x\py"),
        ('a"b', 'a"b'),
    ],
)
def test_quoted_scalar_prefers_quotes_but_degrades_losslessly(
    tmp_path: Path, value: str, stamped: str
) -> None:
    """The historically-always-quoted fields keep their quoted style, except
    where double-quoting cannot be lossless (`\\` or `\"` in the value) — the
    panel showed a valid `url: x\\py` re-stamping into unloadable YAML when
    quoted blindly (round 2, #87)."""
    (tmp_path / "init.sh").write_bytes((REPO_ROOT / "init.sh").read_bytes())
    proc = subprocess.run(
        ["sh", "-c", _QUOTED_SCALAR_DRIVER, "_", value],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout == stamped + "\n"


def test_rerun_preserves_tracker_url_with_backslash_for_both_readers(tmp_path: Path) -> None:
    """A backslash in an always-quoted field degrades to a raw stamp: quoted,
    PyYAML rejects the escape while kitconfig reads it literally (panel, #87)."""
    config = _shipped_with_tracker_url(r'"x\py"')
    assert r'  url: "x\py"' in config
    repo = _fixture(tmp_path, config=config)

    _run_init(repo)
    text = _config(repo)
    assert yaml.safe_load(text)["tracker"]["url"] == r"x\py"
    import kitconfig  # noqa: PLC0415

    assert kitconfig.loads(text)["tracker"]["url"] == r"x\py"
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_normalizes_single_quoted_bots_item(tmp_path: Path) -> None:
    """A hand-written `bots: ['coderabbit']` is valid YAML naming the reviewer
    `coderabbit` — the double-quote-only strip re-serialized it as the literal
    name `'coderabbit'`, which pr_watch silently fails to match (panel, #87)."""
    config = shipped_config().replace("  bots: [coderabbit]", "  bots: ['coderabbit']")
    assert "  bots: ['coderabbit']" in config
    repo = _fixture(tmp_path, config=config)

    _run_init(repo)
    text = _config(repo)
    assert yaml.safe_load(text)["review"]["bots"] == ["coderabbit"]
    assert 'bots: ["coderabbit"]' in text
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_handles_doubled_single_quote_escape(tmp_path: Path) -> None:
    """YAML's `''` escape inside a single-quoted scalar: the close-quote scan
    must skip it, or the interior `#` reads as a comment and the value is
    truncated with its remainder re-attached as a comment (CodeRabbit on #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, "'it''s #1' # note")

    assert parsed["project"]["name"] == "it's #1"
    once = text
    _run_init(repo)
    assert _config(repo) == once


def test_rerun_drops_yaml_significant_chars_from_bots_items(tmp_path: Path) -> None:
    """A quote or backslash inside a bots item would corrupt the whole flow
    list when re-wrapped; such characters cannot appear in a real bot handle
    and are dropped so the config stays loadable (CodeRabbit on #87)."""
    config = shipped_config().replace('  bots: [coderabbit]', '  bots: ["a\\"b"]')
    assert '  bots: ["a\\"b"]' in config
    repo = _fixture(tmp_path, config=config)

    _run_init(repo)
    text = _config(repo)
    assert yaml.safe_load(text)["review"]["bots"] == ["ab"]
    _run_init(repo)
    assert _config(repo) == text


def test_rerun_preserves_quote_ending_value_with_comment(tmp_path: Path) -> None:
    """`he said "hi"` followed by a real comment: the old independent-ends
    quote strip ate the value's closing quote; the matched-pair strip keeps it
    (panel round 2, #87)."""
    repo, text, parsed = _rerun_and_reload(tmp_path, 'he said "hi" # note')

    assert parsed["project"]["name"] == 'he said "hi"'
    assert '# note' in text.split("name:")[1].splitlines()[0]
    _run_init(repo)
    assert _config(repo) == text


@pytest.mark.parametrize(
    ("value", "stamped"),
    [
        ("plain", "plain"),
        ("Acme: Platform", '"Acme: Platform"'),
        ("Acme #1", '"Acme #1"'),
        ("a#b", '"a#b"'),
        ("[coderabbit]", '"[coderabbit]"'),
        ("-lead", '"-lead"'),
        ('he said "hi"', 'he said "hi"'),
        (r"C:\proj", r"C:\proj"),
        ("'quoted'", "'quoted'"),
        ("", '""'),
    ],
)
def test_yaml_scalar_stamping_policy(tmp_path: Path, value: str, stamped: str) -> None:
    """Quote only when needed AND lossless: `:`/`#`/leading-indicator values are
    double-quoted; values containing `"` or `\\` (YAML-significant in
    double-quoted style, and get_field does not unescape) or already
    single-quoted stay raw; empty stamps as an explicit empty string."""
    (tmp_path / "init.sh").write_bytes((REPO_ROOT / "init.sh").read_bytes())
    proc = subprocess.run(
        ["sh", "-c", _YAML_SCALAR_DRIVER, "_", value],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout == stamped + "\n"


def test_rerun_preserves_quoted_name_with_colon(tmp_path: Path) -> None:
    """Prompted values are stamped quoted when needed (#62) — the unquoted
    re-stamp turned a legal quoted name containing a colon into invalid YAML on
    a plain re-run. yaml_scalar's full policy is table-tested below."""
    repo = _fixture(tmp_path, config=_shipped_with_name('"Acme: Platform"'))

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["project"]["name"] == "Acme: Platform"


def test_rerun_preserves_quoted_name_with_hash(tmp_path: Path) -> None:
    """get_field's comment strip is quote-aware (#62) — a blind index() silently
    truncated a quoted name containing # and re-stamped the truncation. The
    second run pins set_field's comment scan too: a quote-blind one re-attached
    the tail of the old value as a growing pseudo-comment on every re-run."""
    repo = _fixture(tmp_path, config=_shipped_with_name('"Acme #1"'))

    _run_init(repo)
    once = _config(repo)
    assert yaml.safe_load(once)["project"]["name"] == "Acme #1"

    _run_init(repo)
    assert _config(repo) == once


# --------------------------------------------------------------------------- #
# set_field — awk value handling (#62 part 2)
# --------------------------------------------------------------------------- #

# The Makefile's install-hooks target established this pattern: extract the
# needed blocks straight out of init.sh, so the test always drives current
# logic. set_field splices the shared AWK_COMMENT_IDX scanner into its awk
# program, so the driver extracts that definition too.
_SET_FIELD_DRIVER = '''CONFIG_FILE="config/dev-model.yaml"
eval "$(sed -n "/^AWK_COMMENT_IDX=/,/^'/p" init.sh)"
eval "$(sed -n '/^set_field() {/,/^}/p' init.sh)"
set_field "tracker:" "" "^  url:" "$1"
'''


def test_set_field_writes_backslashes_literally(tmp_path: Path) -> None:
    """The value reaches awk via the environment (#62) — `awk -v` ran escape
    processing on the assignment, turning a backslash-n in a stamped value into
    a real newline before substitution."""
    repo = _fixture(tmp_path, config='tracker:\n  url: ""\n')
    value = '"' + r"https://x.example/a\nb\\c" + '"'

    subprocess.run(
        ["sh", "-c", _SET_FIELD_DRIVER, "_", value],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    assert r"a\nb\\c" in _config(repo)


# --------------------------------------------------------------------------- #
# narrative-doc seeding
# --------------------------------------------------------------------------- #


@pytest.mark.kit_repo_only("docs/templates")
def test_seeds_narrative_docs_with_tokens_rendered(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)

    _run_init(repo)

    # Token rendering is asserted for ALL five seeded docs: {{HANDOFF}} appears only in
    # the handoff-history template, and with the check on one doc a deleted
    # substitution survived the whole suite (adversarial lens, this change).
    seeded = {
        rel: (repo / rel).read_text(encoding="utf-8")
        for rel in (
            "docs/kit-handoff.md",
            "docs/kit-handoff-history.md",
            "docs/kit-friction-log.md",
            "docs/kit-friction-log-archive.md",
            "AGENTS.md",
        )
    }
    for rel, text in seeded.items():
        assert "{{" not in text, f"unrendered token left in {rel}"
    # Token ABSENCE alone lets a substitution that renders to the EMPTY string
    # pass — an uninitialized awk variable is silently "" (adversarial lens,
    # round 2) — so also pin one rendered VALUE per token family, per doc:
    # Pin that the token rendered to the CONFIGURED name, read from the config
    # under test — not to a literal. Asserting `my-project` coupled this to the
    # config being unstamped, so it failed the moment this repo (or any adopter)
    # set its own project name, which is not what this test is about.
    configured_name = yaml.safe_load(shipped_config())["project"]["name"]
    assert configured_name, "shipped config has no project.name to render"
    assert configured_name in seeded["docs/kit-handoff.md"]  # {{PROJECT_NAME}}
    # Read the engines dir from the config under test for the same reason
    # `configured_name` above is read rather than written literally (#134): a
    # bare "scripts/" pins this to one layout, and it failed under the
    # `scripts/devkit` layout `/adopt` defaults to — where the token renders
    # correctly and the assertion was simply wrong about what correct is.
    configured_engines = yaml.safe_load(shipped_config())["paths"]["engines"]
    assert (
        f"{configured_engines}/check_doc_budget.py" in seeded["docs/kit-handoff.md"]
    )  # {{ENGINE_DIR}}
    assert "kit-handoff-history.md" in seeded["docs/kit-handoff.md"]  # {{HANDOFF_HISTORY}}
    assert "kit-handoff.md" in seeded["docs/kit-handoff-history.md"]  # {{HANDOFF}}
    assert "kit-friction-log-archive.md" in seeded["docs/kit-friction-log.md"]  # {{FRICTION_ARCHIVE}}
    # {{TRACKER_URL}} has two branches (init.sh: a non-empty value renders as-is,
    # a blank one renders a "set `tracker.url`" instruction). Assert whichever
    # branch the config under test selects. The blank branch keeps its own test
    # below, so stamping a real URL here cannot silently delete that coverage —
    # which is exactly what happened when this assertion was a bare literal.
    configured_url = yaml.safe_load(shipped_config())["tracker"]["url"]
    assert (configured_url or "tracker.url") in seeded["docs/kit-friction-log.md"]
    # AGENTS.md renders at the repo ROOT, so its handoff link is the repo-relative
    # configured path, not the sibling-relative form the narrative docs use.
    assert "docs/kit-handoff.md" in seeded["AGENTS.md"]  # {{HANDOFF_PATH}}


@pytest.mark.kit_repo_only("docs/templates")
def test_blank_tracker_url_renders_the_set_it_instruction(tmp_path: Path) -> None:
    """The {{TRACKER_URL}} fallback branch, pinned independently of what the
    shipped config holds.

    Until this existed, the fallback was covered only incidentally — by the
    shipped config happening to leave `tracker.url` blank. Stamping a real URL
    silently removed that coverage, and nothing failed to say so.
    """
    repo = _fixture(tmp_path, config=_shipped_with_tracker_url('""'), templates=True)

    _run_init(repo)

    friction = (repo / "docs" / "kit-friction-log.md").read_text(encoding="utf-8")
    assert "tracker.url" in friction, "blank tracker.url should render the set-it instruction"
    assert "{{" not in friction


@pytest.mark.kit_repo_only("docs/templates")
def test_render_preserves_backslashes_in_values(tmp_path: Path) -> None:
    """_render passes values to awk via ENVIRON: with `-v`, a backslash-n in a
    project name became a real newline in every seeded doc — this was the one
    #62 surface the suite left unpinned (panel, #87)."""
    repo = _fixture(tmp_path, config=_shipped_with_name(r"Acme\nCo"), templates=True)

    _run_init(repo)

    handoff = (repo / "docs" / "kit-handoff.md").read_text(encoding="utf-8")
    assert r"Acme\nCo" in handoff


@pytest.mark.kit_repo_only("docs/templates")
def test_seeding_respects_in_use_docs_and_reclaims_marked_ones(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    (repo / "docs").mkdir(parents=True, exist_ok=True)
    in_use = repo / "docs" / "kit-handoff.md"
    in_use.write_text("# mine — hands off\n", encoding="utf-8")
    marked = repo / "docs" / "kit-friction-log.md"
    marked.write_text(
        "<!-- devkit-template: unrendered — pristine -->\nskeleton\n", encoding="utf-8"
    )

    _run_init(repo)

    assert in_use.read_text(encoding="utf-8") == "# mine — hands off\n"
    reseeded = marked.read_text(encoding="utf-8")
    assert "skeleton" not in reseeded
    assert "{{" not in reseeded


@pytest.mark.kit_repo_only("docs/templates")
def test_agents_md_renders_the_configured_protected_branch(tmp_path: Path) -> None:
    """{{PROTECTED_BRANCH}} pinned against a DISTINCTIVE value, because the token
    has a FALLBACK: `render_protected_branch` defaults to "main" when the config
    value is empty. Asserting the shipped `main` therefore cannot tell "the
    configured value was rendered" from "the config was never read and the
    fallback fired" — a distinctive value separates them. (Round 2's correctness
    lens disproved this docstring's first version, which claimed asserting `main`
    would pass with the substitution deleted: the template contains no literal
    `main`, so that assertion would have failed. The test is right; the reason
    given for it was not.)"""
    config = shipped_config().replace("protected_branch: main", "protected_branch: trunk-9f2a")
    repo = _fixture(tmp_path, config=config, templates=True)

    _run_init(repo)

    assert "trunk-9f2a" in (repo / "AGENTS.md").read_text(encoding="utf-8")


@pytest.mark.kit_repo_only("docs/templates")
@pytest.mark.parametrize("marker_line", [2, 3])
def test_seeding_leaves_a_doc_that_merely_quotes_the_marker_untouched(
    tmp_path: Path, marker_line: int
) -> None:
    """The marker counts only on line 1, where every shipped skeleton carries it.
    Matching it anywhere let a hand-written AGENTS.md that documented the marker
    convention in prose be silently overwritten — content loss, reported as
    "seeded" (panel, adversarial lens).

    LINE 2 is parametrized because this is the DESTRUCTIVE consumer: with the
    marker only on line 3, widening the guard to `head -n 2` left the whole suite
    green while init.sh overwrote a doc whose line 2 quotes the marker. The
    read-only reporter got this case first; the file-destroying one had it open
    two rounds longer (panel round 5)."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    mine = repo / "AGENTS.md"
    lines = ["# AGENTS.md — hand written", "", "still hand written", ""]
    lines[marker_line - 1] = "The kit marks skeletons `devkit-template: unrendered` on line 1."
    original = "\n".join(lines) + "\n"
    # Positive control: a fixture that lost the marker would pass vacuously,
    # since "left untouched" is also the no-marker outcome (panel round 5).
    assert "devkit-template: unrendered" in original.split("\n")[marker_line - 1]
    mine.write_text(original, encoding="utf-8")

    result = _run_init(repo)

    assert mine.read_text(encoding="utf-8") == original
    assert "AGENTS.md already in use — left untouched" in result.stdout


@pytest.mark.parametrize("entry_point", ["AGENTS.md", "CLAUDE.md"])
def test_kit_own_entry_points_carry_the_marker(entry_point: str) -> None:
    """Replaces `test_kit_ships_no_root_agents_md`, which pinned the OLD
    discriminator: AGENTS.md was seeded by ABSENCE, so the kit could not ship one
    without handing every `cp -r` adopter its own rendered file with the guard
    permanently false and no diagnostic.

    That constraint is gone — the kit now ships BOTH entry points, so a session
    working in the kit is bound by the kit's contract on either runtime — but the
    failure it named is not, and it is now reachable through CLAUDE.md too, which
    the kit shipped unmarked all along. The invariant that replaces it is the one
    that actually prevents the failure: a kit-own entry point must carry
    KIT_OWN_MARKER on LINE 1, which is what makes ./init.sh render over it in an
    adopter instead of calling it "already in use".

    Line 1 specifically, because that is all `_seedable` reads."""
    marker = kit_own_marker()
    path = REPO_ROOT / entry_point
    assert path.is_file(), f"the kit must ship its own {entry_point}"
    first_line = path.read_text(encoding="utf-8").split("\n", 1)[0]
    assert marker in first_line, (
        f"{entry_point} must carry '{marker}' on line 1 — without it "
        f"./init.sh reports it 'already in use' in every `cp -r` adopter and "
        f"leaves them the kit's contract, silently"
    )


def test_kit_own_marked_file_is_reseeded_over(tmp_path: Path) -> None:
    """The behaviour the marker buys, asserted end-to-end rather than by reading
    the predicate: a file carrying KIT_OWN_MARKER is REPLACED, and what lands is
    the adopter's values, not the kit's.

    DISTINCTIVE values, for the reason
    `test_agents_md_renders_the_configured_protected_branch` gives: the kit's own
    `shipped_config()` names the project `agentic-dev-kit` and its handoff
    `docs/kit-handoff.md`, so asserting those strings are absent cannot tell "the
    kit's file was replaced" from "the adopter's file rendered the same words".
    The first version of this test did exactly that and failed against correct
    code."""
    config = (
        shipped_config()
        .replace("name: agentic-dev-kit", "name: acme-q7")
        .replace("handoff: docs/kit-handoff.md", "handoff: docs/plan-q7.md")
    )
    assert "acme-q7" in config and "docs/plan-q7.md" in config, (
        "fixture config did not take the distinctive values — the substitutions "
        "above no longer match config/dev-model.yaml"
    )
    repo = _fixture(tmp_path, config=config, templates=True)
    kit_own_text = (
        f"<!-- {kit_own_marker()} -->\n# the kit's own entry point\n"
        "The living plan is `docs/kit-handoff.md`.\n"
    )
    for entry_point in ("AGENTS.md", "CLAUDE.md"):
        (repo / entry_point).write_text(kit_own_text, encoding="utf-8")

    result = _run_init(repo)

    for entry_point in ("AGENTS.md", "CLAUDE.md"):
        rendered = (repo / entry_point).read_text(encoding="utf-8")
        assert rendered != kit_own_text, (
            f"{entry_point} was left untouched — the kit-own marker did not "
            f"make it seedable"
        )
        assert kit_own_marker() not in rendered
        assert "docs/kit-handoff.md" not in rendered
        assert "acme-q7" in rendered, f"{entry_point} did not render this repo's values"
        assert "{{" not in rendered, f"unrendered token left in {entry_point}"
        assert f"{entry_point} already in use" not in result.stdout


def test_an_in_use_entry_point_is_still_never_touched(tmp_path: Path) -> None:
    """The widened predicate must not widen what it destroys. An adopter's own
    entry point carries NEITHER marker, and `seed_doc` takes no backup, so this
    is the destructive consumer of the change above."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    mine = repo / "CLAUDE.md"
    original = f"# CLAUDE.md — mine\n\nThe kit marks its own files `{kit_own_marker()}`.\n"
    # Positive control: a fixture that lost the quoted marker would pass
    # vacuously, since "left untouched" is also the no-marker outcome.
    assert kit_own_marker() in original.split("\n")[2]
    mine.write_text(original, encoding="utf-8")

    result = _run_init(repo)

    assert mine.read_text(encoding="utf-8") == original
    assert "CLAUDE.md already in use — left untouched" in result.stdout


@pytest.mark.parametrize("target", ["AGENTS.md", "CLAUDE.md", "docs/kit-friction-log.md"])
def test_a_marker_quoted_in_prose_on_line_1_is_not_seedable(
    tmp_path: Path, target: str
) -> None:
    """The destructive consumer of the anchor in `_seedable`, and the case the
    line-1 rule alone does NOT cover.

    `test_seeding_leaves_a_doc_that_merely_quotes_the_marker_untouched`
    parametrizes the quote onto lines 2 and 3 — never line 1, which is the one
    line the guard reads. A substring match there overwrote a real file with no
    backup, printing `seeded <path>`, indistinguishable from a first-time seed.
    Found by the panel's adversarial lens on PR #289 by running init.sh against
    a hand-built fixture, not by reading the predicate.

    Both markers, because both now flow through one predicate; and both entry
    points, because for those two it is a REGRESSION rather than an inherited
    risk — `AGENTS.md` used to be seeded by absence and `CLAUDE.md` not at all."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    for marker in (kit_own_marker(), "devkit-template: unrendered"):
        # Every shape that mentions a marker without BEING one. The HTML-comment
        # forms are the sharp ones: anchoring only the left side (`<!--`) left
        # them matching, which is how this guard destroyed a file for the second
        # time — panel round 2, reproduced end-to-end against a real fixture.
        for shape in (
            f"Note: the kit marks its own files `{marker}` on line 1.",
            f"<!-- see the kit's {marker} convention for why this file exists -->",
            f"<!-- migration note: we dropped the {marker} line when we forked -->",
            # Prefix-only: the marker is the first token but not a whole one.
            f"<!-- {marker}ership notes, ours -->",
        ):
            path = repo / target
            path.parent.mkdir(parents=True, exist_ok=True)
            original = f"{shape}\n\n# Ours, hand written, must survive ./init.sh\n"
            path.write_text(original, encoding="utf-8")

            result = _run_init(repo)

            assert path.read_text(encoding="utf-8") == original, (
                f"{target} was DESTROYED — line 1 was {shape!r}, which mentions "
                f"'{marker}' without being the kit's marker comment"
            )
            assert f"{target} already in use — left untouched" in result.stdout


@pytest.mark.parametrize("target", ["AGENTS.md", "CLAUDE.md"])
@pytest.mark.parametrize("shape", ["directory", "broken symlink"])
def test_a_non_regular_target_is_not_reported_as_seeded(
    tmp_path: Path, target: str, shape: str
) -> None:
    """`[ -f ]` alone conflated "missing" with "exists but is not a regular
    file", so a DIRECTORY named AGENTS.md read as missing: `mv` moved the
    rendered temp file inside it and the run reported `seeded AGENTS.md` having
    written nothing at that path. Panel round 3, adversarial, live fixture.

    BOTH shapes, because they are pinned by different halves of the guard and
    round 3 shipped only the first: `[ -e ]` catches the directory, `[ -L ]`
    catches the broken symlink — `-e` follows the link and is FALSE for a
    dangling one, so without the `-L` disjunct a broken symlink reads as missing
    and is silently replaced, reported `seeded`. Round 4's adversarial lens
    mutated `-L` away and the whole suite stayed green.

    BOTH targets, because the guard is claimed to define "in use" identically
    for every target while `CLAUDE.md` alone has target-specific logic nearby
    (the `@AGENTS.md` import hint), so a future special-case there would not be
    caught by an AGENTS.md-only fixture."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    path = repo / target
    if shape == "directory":
        path.mkdir()
    else:
        path.symlink_to("no-such-target-9f2a.md")
        assert path.is_symlink() and not path.exists()  # positive control: dangling

    result = _run_init(repo)

    assert f"seeded {target}" not in result.stdout
    assert f"{target} already in use — left untouched" in result.stdout
    if shape == "directory":
        assert path.is_dir()
        strays = list(path.iterdir())
        assert strays == [], f"render leaked a temp file into the directory: {strays}"
    else:
        assert path.is_symlink(), f"{target} was replaced — the broken symlink was overwritten"
        assert not path.exists()


def test_seeding_through_a_symlink_replaces_the_link_not_its_target(tmp_path: Path) -> None:
    """A symlink to a regular file resolves as one, so a link whose TARGET opens
    with a marker is seedable — and `mv` then replaces the link itself.

    Pins both halves of that, because only one of them is safe by luck: the link
    target must be byte-identical afterwards (`mv` rewrites a directory entry
    and does not follow), while the link is gone. Panel round 5, adversarial —
    reported as an undisclosed, untested edge rather than a data-loss path, and
    the behaviour is documented rather than changed."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.md"
    marked = f"<!-- {kit_own_marker()} — the link target -->\n# canonical, shared\n"
    victim.write_text(marked, encoding="utf-8")
    (repo / "AGENTS.md").symlink_to(victim)
    assert (repo / "AGENTS.md").is_symlink()  # positive control on the fixture

    _run_init(repo)

    assert victim.read_text(encoding="utf-8") == marked, (
        "the render followed the symlink and overwrote its target — mv must "
        "replace the directory entry, not dereference it"
    )
    assert not (repo / "AGENTS.md").is_symlink(), "the link survived — fixture never seeded"
    assert "canonical, shared" not in (repo / "AGENTS.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("blank", [" ", " ", "　"])
def test_a_unicode_blank_beside_the_marker_does_not_make_it_seedable(
    tmp_path: Path, blank: str
) -> None:
    """`[[:space:]]` is LOCALE-DEPENDENT, and nothing here pins the locale by
    default. Under the UTF-8 locale a developer machine actually runs, the shell
    matched these while `kit_doctor`'s `POSIX_BLANKS` did not — so a marker line
    whose space had been typo'd to NBSP was seedable to init.sh and "in use" to
    the doctor: init.sh would overwrite it and the doctor would say nothing.
    Panel round 7, adversarial, reproduced across four locales.

    Runs under a locale PROVED to classify U+00A0 as blank, not a hardcoded
    name: under LC_ALL=C — which is where an uninstalled locale name lands —
    this passes with the pin removed, so a hardcoded name would unpin the check
    silently on any machine lacking that locale."""
    locale_name = locale_where_nbsp_is_blank()
    if locale_name is None:
        pytest.skip(
            "no installed locale classifies U+00A0 as blank, so the shell's "
            "[[:space:]] cannot differ from C here and this pins nothing"
        )
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    original = f"<!--{blank}{kit_own_marker()} -->\n# ours, must survive\n"
    (repo / "CLAUDE.md").write_text(original, encoding="utf-8")

    env = _env(repo.parent)
    env["LC_ALL"] = locale_name
    env["LANG"] = locale_name
    result = subprocess.run(
        ["sh", "init.sh"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
    )

    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == original, (
        "a Unicode blank beside the marker made the file seedable under a UTF-8 "
        "locale — init.sh and kit_doctor then disagree about whether it is in use"
    )
    assert "CLAUDE.md already in use — left untouched" in result.stdout


@pytest.mark.parametrize("target", ["AGENTS.md", "CLAUDE.md"])
def test_the_real_marker_comment_is_still_seedable(tmp_path: Path, target: str) -> None:
    """The control for the test above. Without it, a `_seedable` that simply
    returned false would pass every negative case — and the kit's own entry
    points would then never be rendered over in an adopter, which is the whole
    mechanism. Uses the SHIPPED line 1 verbatim rather than a reconstruction."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    shipped_first_line = (REPO_ROOT / target).read_text(encoding="utf-8").split("\n", 1)[0]
    assert kit_own_marker() in shipped_first_line  # positive control on the fixture
    (repo / target).write_text(f"{shipped_first_line}\n# the kit's own\n", encoding="utf-8")

    result = _run_init(repo)

    assert f"seeded {target}" in result.stdout
    assert "the kit's own" not in (repo / target).read_text(encoding="utf-8")


def test_an_in_use_claude_md_without_the_import_is_reported(tmp_path: Path) -> None:
    """Leaving their file alone is correct and also leaves the two runtimes on
    different contracts, because Claude Code reads CLAUDE.md and not AGENTS.md.
    init.sh must say so rather than edit their file."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    (repo / "CLAUDE.md").write_text("# CLAUDE.md — mine\n", encoding="utf-8")

    result = _run_init(repo)

    assert "does not import AGENTS.md" in result.stdout
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == "# CLAUDE.md — mine\n"


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("code span", "# mine\n\nAdd `@AGENTS.md` near the top to import the contract.\n"),
        ("fenced block", "# mine\n\n```markdown\n@AGENTS.md\n```\n"),
        ("tilde fence", "# mine\n\n~~~\n@AGENTS.md\n~~~\n"),
        ("longer name", "# mine\n\n@AGENTS.mdx\n"),
        # A ```-run does not close a ````-opened fence (CommonMark: the closer
        # must be at least as long). Toggling on any three read the inner fence
        # as a close and scanned the rest as live prose — panel, adversarial
        # lens. The `@AGENTS.md` below is still inside the outer fence.
        ("mismatched fence length", "# mine\n\n````\ntext\n```\n@AGENTS.md\n````\n"),
        # A closing fence carries nothing but blanks after its run, so the
        # middle line here does not close the block and @AGENTS.md is still
        # inside it (panel round 2, LOW).
        ("run with trailing text is not a close", "# mine\n\n```\n``` still open\n@AGENTS.md\n```\n"),
        # Code spans are delimited by runs of EQUAL length, so this is ONE
        # double-backtick span, not two empty single ones. The single-backtick
        # regex this replaces stripped the delimiters and read the middle as
        # live prose (CodeRabbit, PR #289).
        ("double-backtick span", "# mine\n\n``@AGENTS.md``\n"),
        ("triple-backtick span inline", "# mine\n\nsee ```@AGENTS.md``` here\n"),
        # A span runs to its matching closer even across a newline.
        ("multiline span", "# mine\n\n`@AGENTS.md\nstill inside the span`\n"),
        # A run of a DIFFERENT length does not close the span.
        ("inner shorter run does not close", "# mine\n\n``a ` b @AGENTS.md``\n"),
        # Claude Code strips block-level HTML comments before injecting, so an
        # import inside one is not live — and this is a plausible thing to
        # write (panel round 6, adversarial).
        ("html comment", "# mine\n\n<!-- TODO: add the @AGENTS.md import -->\n"),
        ("multiline html comment", "# mine\n\n<!-- TODO:\n@AGENTS.md\n-->\n"),
    ],
)
def test_an_inactive_agents_import_does_not_suppress_the_hint(
    tmp_path: Path, label: str, body: str
) -> None:
    """Claude Code does not evaluate import syntax inside Markdown code spans or
    fenced code blocks, so an `@AGENTS.md` in either is NOT an import and the
    file does not load the shared contract.

    A substring match read all of these as importing and stayed silent — the
    TEMPLATE_MARKER "quotes it in prose" class, one function over, found by the
    review bot on this PR.

    No shipped file is one of these shapes; an earlier version of this docstring
    claimed `docs/templates/CLAUDE.md.tmpl` was, and its only `@AGENTS.md` is the
    live import. The case is an adopter's own CLAUDE.md — the code-span form is
    what prose about the mechanism reaches for, as `docs/getting-started.md:44`
    does, though that file never reaches the predicate."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    (repo / "CLAUDE.md").write_text(body, encoding="utf-8")

    result = _run_init(repo)

    assert "does not import AGENTS.md" in result.stdout, (
        f"an @AGENTS.md in a {label} was read as an active import"
    )


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("bare import, plus a code-span mention", "# mine\n\n@AGENTS.md\n\nSee `@AGENTS.md` above.\n"),
        # Four leading spaces is an INDENTED CODE BLOCK, not a fence. Treating
        # it as one opened a block that never closed and swallowed the real
        # import below it — the hint then fired on a file that does import
        # (CodeRabbit, PR #289).
        ("after a four-space-indented backtick line", "# mine\n\n    ```\n    example\n\n@AGENTS.md\n"),
        # A closed span must not leave the scanner inside one.
        ("after a closed multiline span", "# mine\n\n`a\nb`\n\n@AGENTS.md\n"),
        # A closed comment must not leave the scanner inside one — and the
        # SHIPPED template opens with an HTML comment header above its import,
        # so this is the shape that actually ships.
        ("after a closed html comment", "<!-- header -->\n\n@AGENTS.md\n"),
        ("after a closed multiline html comment", "<!-- a\nb -->\n\n@AGENTS.md\n"),
        # A `<!--` inside a code span is span content, not a comment opener.
        ("backticked comment opener", "# mine\n\n`<!--` then\n\n@AGENTS.md\n"),
    ],
)
def test_an_active_agents_import_suppresses_the_hint(
    tmp_path: Path, label: str, body: str
) -> None:
    """The other direction, so the inactive-shape cases above cannot pass by the
    hint always firing — which they would if `_imports_agents_md` simply
    returned false. Each case here contains a genuinely live import."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    (repo / "CLAUDE.md").write_text(body, encoding="utf-8")

    result = _run_init(repo)

    assert "does not import AGENTS.md" not in result.stdout, (
        f"a live import was missed: {label}"
    )


# --------------------------------------------------------------------------- #
# .gitignore appends
# --------------------------------------------------------------------------- #


def test_gitignore_entries_added_exactly_once_across_reruns(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config())

    _run_init(repo)
    _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in (
        "state/",
        ".devkit_state_root",
        ".claude/worktrees/",
        "reports/",
        # The overlay's ignore rule is the ONLY thing keeping an adopter's operator
        # id out of git, and `.gitignore` is adopter-owned so the kit never ships
        # one. Without this seeded here, docs/getting-started.md instructs adopters
        # to write an identity into a tracked path while asserting it is ignored
        # (panel, adversarial lens — a HIGH on the change that added the overlay).
        "config/*.local.yaml",
    ):
        assert lines.count(entry) == 1, f"{entry!r} appears {lines.count(entry)} times"


def test_gitignore_gains_mcp_json_only_for_literal_credentials(tmp_path: Path) -> None:
    """The .mcp.json credential sniff, for the key shapes its regex matches
    (upper-case underscore forms like CF_TOKEN): a literal value gets the file
    ignored, a ${ENV} reference leaves it tracked. The sniff itself misses the
    kit's own documented hyphenated shape (CF-Access-Client-Id) — #86 tracks
    that; this green pins the guard that exists, not sufficiency."""
    literal = _fixture(tmp_path / "literal", config=shipped_config())
    (literal / ".mcp.json").write_text('{"CF_TOKEN": "abc123"}', encoding="utf-8")
    _run_init(literal)
    assert ".mcp.json" in (literal / ".gitignore").read_text(encoding="utf-8").splitlines()

    envref = _fixture(tmp_path / "envref", config=shipped_config())
    (envref / ".mcp.json").write_text('{"CF_TOKEN": "${CF_TOKEN}"}', encoding="utf-8")
    _run_init(envref)
    assert ".mcp.json" not in (envref / ".gitignore").read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------- #
# install_hooks
# --------------------------------------------------------------------------- #


def test_installs_pre_push_shim_into_git_hooks(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config(), git=True, hooks=True)

    _run_init(repo)

    shim = repo / ".git" / "hooks" / "pre-push"
    assert shim.is_file()
    assert os.access(shim, os.X_OK)
    body = shim.read_text(encoding="utf-8")
    assert "devkit-hook-shim" in body
    # The shim must point at the hook under the CONFIGURED engines dir, not at
    # a literal `scripts/` (#134). Under `paths.engines: scripts/devkit` the
    # generated shim correctly reads `scripts/devkit/hooks/pre-push`, and the
    # literal form of this assertion failed on a shim that was right.
    configured_engines = yaml.safe_load(shipped_config())["paths"]["engines"]
    assert f"{configured_engines}/hooks/pre-push" in body


def test_hook_shim_honors_repo_local_hookspath(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config(), git=True, hooks=True)
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=repo,
        check=True,
        env=_env(repo.parent),
        capture_output=True,
    )

    _run_init(repo)

    assert (repo / ".githooks" / "pre-push").is_file()
    assert not (repo / ".git" / "hooks" / "pre-push").exists()


def test_existing_non_shim_hook_left_untouched(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=shipped_config(), git=True, hooks=True)
    hookdir = repo / ".git" / "hooks"
    hookdir.mkdir(parents=True, exist_ok=True)
    own = "#!/bin/sh\n# the adopter's own hook\n"
    (hookdir / "pre-push").write_text(own, encoding="utf-8")

    proc = _run_init(repo)

    assert (hookdir / "pre-push").read_text(encoding="utf-8") == own
    assert "left untouched" in proc.stderr


def test_gitignore_append_preserves_a_file_with_no_trailing_newline(tmp_path: Path) -> None:
    """`add_ignore_line` concatenated onto the last line when `.gitignore` did not
    end in a newline: a file ending `.env` became `.envstate/`, silently
    un-ignoring it. Six call sites share the helper, two of them secret hygiene.

    The fix shipped without a test and its mutant survived the whole suite
    (panel, adversarial lens) — this is that test."""
    repo = _fixture(tmp_path, config=shipped_config())
    (repo / ".gitignore").write_text("node_modules/\n.env", encoding="utf-8")

    _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lines, f".env was corrupted: {lines}"
    assert "state/" in lines
    assert not any(line.startswith(".env") and line != ".env" for line in lines), lines


def test_non_interactive_run_refuses_to_inherit_a_foreign_tracker(tmp_path: Path) -> None:
    """`ask()` keeps the committed value without prompting when stdin is not a tty,
    so a piped `./init.sh` would seed an adopter this repo's live, public board —
    which triage-friction-log then files real issues into.

    Fires only when an origin remote exists and disagrees, so the kit's own repo
    and every fixture here (no remote) are unaffected."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/acme/widgets.git"],
        cwd=repo, check=True, capture_output=True, env=_env(tmp_path),
    )

    result = subprocess.run(
        ["sh", "init.sh"], cwd=repo, capture_output=True, text=True,
        stdin=subprocess.DEVNULL, env=_env(repo.parent), check=False,
    )

    assert result.returncode == 1, result.stdout
    assert "does not match this repo's origin" in result.stderr, result.stderr


def test_non_interactive_run_is_unaffected_without_an_origin_remote(tmp_path: Path) -> None:
    """The guard must not fire for the kit's own repo or a fresh copy-in — both
    reach init.sh before any remote exists. Pins the guard's narrowness, which is
    what keeps it from wedging the documented install path."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)

    _run_init(repo)  # check=True — a non-zero exit fails here

    assert yaml.safe_load(_config(repo))["tracker"]["project_name"] == "topij/agentic-dev-kit"


def _lens_compute_block(text: str, *, unescape: bool = False) -> tuple[str, str]:
    """Return ``(comment, values)`` for the `lens_compute` block in `text`."""
    if unescape:
        text = text.replace("'\"'\"'", "'")
    start_values = text.index("    lens_compute:")
    start_comment = text.index("    # Compute for each panel lens")
    end_values = text.index("lenses:", start_values)
    return text[start_comment:start_values], text[start_values:end_values].strip()


def test_init_sh_ships_the_same_lens_compute_values_as_the_reference_config():
    """A fresh install must not diverge from the shipped config's actual settings.

    `init.sh` is NOT tracked in `kit-manifest.json`, so no drift check compares
    it against anything — the two can separate silently, and a new adopter would
    then get different panel compute than this repo runs.
    """
    init_comment, init_values = _lens_compute_block(
        (REPO_ROOT / "init.sh").read_text(encoding="utf-8"), unescape=True
    )
    cfg_comment, cfg_values = _lens_compute_block(
        (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")
    )

    assert init_values == cfg_values

    # The comments are deliberately NOT compared for equality: the reference
    # config carries the measurement rationale for the shipped values, which a
    # migration script has no reason to repeat. Asserting equality here would
    # be a check that fails for a reason nobody wants enforced.
    assert init_comment != "" and cfg_comment != ""


def test_both_lens_compute_comments_state_that_effort_is_not_enforced():
    """The honesty caveat must reach BOTH install paths, not just the reference.

    Regression pin for a real miss: the commit that retracted the "effort is a
    real control" overclaim fixed `config/dev-model.yaml` and the doctrine doc
    and left `init.sh` carrying the retracted wording — so every NEW adopter
    would have installed the version its author had already judged wrong. Caught
    by a review lens that ran `init.sh` over a fixture and read the output.

    This is #149's rule ("when a claim is corrected, enumerate every surface it
    was published to") applied to the one surface a manifest cannot watch.
    """
    caveat = "NO per-agent effort parameter"
    init_comment, _ = _lens_compute_block(
        (REPO_ROOT / "init.sh").read_text(encoding="utf-8"), unescape=True
    )
    cfg_comment, _ = _lens_compute_block(
        (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")
    )

    assert caveat in init_comment, "init.sh must not promise an effort guarantee"
    assert caveat in cfg_comment, "the reference config must not either"


# ── register_pr_hook (#301, #303) ────────────────────────────────────────────
# It REPORTS for both runtimes and writes neither. The seeding it used to do for
# .codex/hooks.json was removed after a review round found a dangling symlink at
# that path made `cat >` write outside .codex entirely — see the function's own
# comment. So these tests assert on what it PRINTS, and that it writes nothing.


def _with_pr_hook(repo: Path) -> Path:
    """`register_pr_hook` returns early when the engine is absent, so a fixture
    that wants to exercise it must ship the file."""
    hook = repo / "scripts" / "hooks" / "pr_followup_hook.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    return repo


@pytest.mark.parametrize("fifo_at", [".codex/hooks.json", ".claude/settings.json"])
def test_a_fifo_at_either_config_path_cannot_wedge_the_run(
    tmp_path: Path, fifo_at: str
) -> None:
    """The guards are `-f`, not `-e`, and that single token is load-bearing.

    `grep -q` on a FIFO blocks until someone opens the write end. Nothing ever
    does, so `-e` here is not a slower run — it is `init.sh` hanging forever
    with no output and no error, which is worse than any failure it could
    report. `-f` is false for a FIFO, so the guard short-circuits and grep is
    never reached.

    A FIFO cannot arrive by clone (git has no mode for one), so this is not a
    shape an adopter stumbles into. It is here because a round-4 review lens
    mutated `-f` to `-e` and the whole suite stayed green while the real
    `init.sh` hung until killed. The token had no defender.

    The timeout is the assertion: a regression fails by raising TimeoutExpired
    rather than by hanging CI.
    """
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))
    target = repo / fifo_at
    target.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(target)

    result = subprocess.run(
        ["sh", "init.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=_env(repo.parent),
        timeout=60,
    )

    assert result.returncode == 0
    assert "bootstrapped" in result.stdout
    # and it still said its piece about the runtime whose path is not a FIFO
    other = "claude" if fifo_at.startswith(".codex") else "codex"
    assert f"--runtime {other}" in result.stdout


def test_register_pr_hook_reports_both_runtimes_and_writes_neither(tmp_path: Path) -> None:
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    assert "--runtime codex" in result.stdout
    assert "--runtime claude" in result.stdout
    # the whole point of the redesign: no write, so no filesystem shape to guard
    assert not (repo / ".codex").exists()
    assert not (repo / ".claude" / "settings.json").exists()


def test_register_pr_hook_names_the_configured_engines_dir(tmp_path: Path) -> None:
    """Kills: `${engines_dir}` hardcoded to `scripts`.

    The previous version of this test used a config with no `paths.engines`, so
    the detected fallback was the literal string `scripts` — the same value a
    hardcoded version produces, which made the test unable to tell them apart.
    A review round mutated the interpolation away and the whole suite stayed
    green. This fixture puts the engines somewhere the fallback would never
    produce."""
    repo = _fixture(tmp_path, config=V1_CONFIG, git=True)
    hook = repo / "scripts" / "devkit" / "hooks" / "pr_followup_hook.py"
    hook.parent.mkdir(parents=True)
    hook.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (repo / "scripts" / "devkit" / "pr_watch.py").write_text("", encoding="utf-8")

    result = _run_init(repo)

    assert "scripts/devkit/hooks/pr_followup_hook.py" in result.stdout


def test_register_pr_hook_reports_a_mention_without_calling_it_a_registration(
    tmp_path: Path,
) -> None:
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))
    codex = repo / ".codex"
    codex.mkdir()
    (codex / "hooks.json").write_text(
        '{"hooks": {"PostToolUse": [{"hooks": [{"command": "pr_followup_hook.py"}]}]}}\n',
        encoding="utf-8",
    )

    result = _run_init(repo)

    # narrowed after CodeRabbit pointed out the substring proves a mention, not
    # a registration: the run reports what it saw and names /hooks as the judge
    assert ".codex/hooks.json mentions the PR follow-through hook" in result.stdout
    assert "not checked here" in result.stdout
    assert "no PR follow-through hook found for Codex" not in result.stdout


def test_a_mention_under_the_wrong_event_is_not_reported_as_registered(
    tmp_path: Path,
) -> None:
    """CodeRabbit's finding on `#303`, as a fixture.

    `pr_followup_hook` under `SessionStart` means Codex will never run this on
    a `Bash` call — the adopter is unprotected. The old wording said "already
    registers" and sent them away believing otherwise.

    The fix is not to parse the JSON and decide. It is to stop claiming a
    conclusion the check cannot reach: report the mention, name `/hooks` as
    the authority. This test pins that distinction, so a future edit that
    "helpfully" restores the stronger wording fails here.
    """
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))
    codex = repo / ".codex"
    codex.mkdir()
    (codex / "hooks.json").write_text(
        '{"hooks": {"SessionStart": [{"hooks": ['
        '{"command": "pr_followup_hook.py --runtime codex"}]}]}}\n',
        encoding="utf-8",
    )

    result = _run_init(repo)

    assert "mentions the PR follow-through hook" in result.stdout
    assert "/hooks in a Codex session" in result.stdout
    # the claim the adopter must not be given, in any of its historical forms
    for overclaim in ("already registers", "is registered", "will run"):
        assert overclaim not in result.stdout


@pytest.mark.parametrize("shape", ["plain_file", "dangling_symlink", "unusable_dir", "hooks_json_dangling"])
def test_no_codex_shape_can_make_the_run_write_or_abort(tmp_path: Path, shape: str) -> None:
    """Each of these broke the seeding version — the last one by following a
    symlink and writing the payload OUTSIDE .codex while reporting success.
    With nothing written, every shape is inert."""
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))
    codex = repo / ".codex"
    escaped = repo / "escaped.json"

    if shape == "plain_file":
        codex.write_text("not a directory\n", encoding="utf-8")
    elif shape == "dangling_symlink":
        codex.symlink_to(repo / "no-such-target")
    elif shape == "unusable_dir":
        codex.mkdir()
        codex.chmod(0o000)
    else:
        codex.mkdir()
        (codex / "hooks.json").symlink_to(escaped)

    try:
        result = _run_init(repo)  # check=True — a non-zero exit fails the test
        assert "bootstrapped" in result.stdout
        assert not escaped.exists(), "init.sh wrote through a symlink, outside .codex"
    finally:
        if shape == "unusable_dir":
            codex.chmod(0o755)


def test_both_shipped_registrations_name_their_own_runtime() -> None:
    """Kills: `--runtime claude` in .claude/settings.json flipped to codex.

    Nothing else covers those two files. `kit-manifest.json` does not track
    either, so the drift check cannot see a hand-edit, and `init.sh` no longer
    writes them — so these literals are only as correct as this assertion."""
    root = REPO_ROOT
    claude = (root / ".claude" / "settings.json").read_text(encoding="utf-8")
    codex = (root / ".codex" / "hooks.json").read_text(encoding="utf-8")

    assert "pr_followup_hook.py" in claude
    assert "--runtime claude" in claude
    assert "--runtime codex" not in claude

    assert "pr_followup_hook.py" in codex
    assert "--runtime codex" in codex
    assert "--runtime claude" not in codex

    # and the Codex registration must be valid JSON with the tool-name matcher,
    # since Codex has no config-level `if:` and this is the only narrowing
    parsed = json.loads(codex)
    assert parsed["hooks"]["PostToolUse"][0]["matcher"] == "^Bash$"
