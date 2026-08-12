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
import shlex
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


def template_marker() -> str:
    """`init.sh`'s TEMPLATE_MARKER literal, derived at call time for the reasons
    `kit_own_marker` gives above. Older tests in this module spell this one as a
    literal; those are not rewritten here (out of this change's footprint), but
    new callers should prefer this."""
    text = (REPO_ROOT / "init.sh").read_text(encoding="utf-8")
    match = re.search(r'^TEMPLATE_MARKER="([^"]+)"', text, re.MULTILINE)
    assert match, "TEMPLATE_MARKER is not assigned in init.sh — was it renamed?"
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


def _run_init(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    # stdin explicitly closed so ask() keeps defaults even when the test runner
    # itself is attached to a terminal.
    #
    # `check=False` is for the arguments init.sh must REFUSE — an unknown flag
    # exits non-zero by design, and check=True would report that as an error in
    # the test rather than as the behaviour under test.
    return subprocess.run(
        ["sh", "init.sh", *args],
        cwd=repo,
        check=check,
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


_GET_FIELD_DRIVER = '''CONFIG_FILE="config/dev-model.yaml"
eval "$(sed -n "/^AWK_COMMENT_IDX=/,/^'/p" init.sh)"
eval "$(sed -n '/^get_field() {/,/^}/p' init.sh)"
get_field "tracker:" "" "^  url:"
'''

# `\\"` inside a double-quoted YAML scalar is an escaped quote, so this value is
# one scalar containing a `#`, and PyYAML reads it as such. The scanner used to
# close the scalar at the ESCAPED quote and then treat that `#` as opening a
# trailing comment (#383).
ESCAPED_QUOTE_CONFIG = 'tracker:\n  url: "a \\" b # c"\n'


def test_get_field_does_not_read_a_hash_inside_an_escaped_quote_as_a_comment(
    tmp_path: Path,
) -> None:
    """The read half of #383. On the old scanner this returned `"a \\" b` —
    truncated mid-scalar, and with an unbalanced quote left on the front."""
    repo = _fixture(tmp_path, config=ESCAPED_QUOTE_CONFIG)

    result = subprocess.run(
        ["sh", "-c", _GET_FIELD_DRIVER],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_env(repo.parent),
    )

    assert result.stdout.strip() == r'a \" b # c'


def test_set_field_does_not_reattach_part_of_the_old_value_as_a_comment(
    tmp_path: Path,
) -> None:
    """The write half, and the one that costs something: `set_field` preserves
    a trailing comment by design, so a scan that finds one INSIDE the old value
    re-attaches that fragment to the new value. Measured on the pre-fix
    installer, stamping `new-value` over this config produced

        url: "new-value"  # c"

    — a fragment of the old value, plus a dangling quote, written into the
    adopter's `config/dev-model.yaml` with nothing to report it."""
    repo = _fixture(tmp_path, config=ESCAPED_QUOTE_CONFIG)

    subprocess.run(
        ["sh", "-c", _SET_FIELD_DRIVER, "_", '"new-value"'],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_env(repo.parent),
    )

    assert _config(repo) == 'tracker:\n  url: "new-value"\n'


@pytest.mark.parametrize(
    "config,expected",
    [
        # A REAL trailing comment on a double-quoted scalar must still be found —
        # the fix must not make the scanner comment-blind.
        ('tracker:\n  url: "plain" # a real comment\n', "plain"),
        # A doubled backslash is one literal backslash, so the quote AFTER it is
        # the closing quote and the comment beyond it is real. This is why the
        # escape skips two characters rather than one.
        ('tracker:\n  url: "trailing \\\\" # a real comment\n', "trailing \\\\"),
        # The single-quote arm is unchanged: no backslash escaping there, and its
        # own doubled-apostrophe escape still holds a `#` inside the scalar.
        ("tracker:\n  url: 'O''Brien # x'\n", "'O''Brien # x'"),
        # The SCOPING of the new rule, which the case above only asserted in
        # prose. A single-quoted YAML scalar has no backslash escape — PyYAML
        # reads this value as `trailing \` with the comment stripped — so a
        # trailing backslash must NOT swallow the closing quote here. Broadening
        # the guard to both quote kinds (the two forms differ by one condition
        # and look almost identical) left the whole file green while making this
        # input return `'trailing \' # comment`: a real comment absorbed into the
        # value, which is the very bug #383 fixes on the other arm. Panel,
        # correctness lens, mutation-verified.
        ("tracker:\n  url: 'trailing \\' # a real comment\n", "'trailing \\'"),
    ],
)
def test_the_comment_scan_still_finds_the_comments_it_should(
    tmp_path: Path, config: str, expected: str
) -> None:
    repo = _fixture(tmp_path, config=config)

    result = subprocess.run(
        ["sh", "-c", _GET_FIELD_DRIVER],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_env(repo.parent),
    )

    assert result.stdout.strip() == expected


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


# --------------------------------------------------------------------------- #
# --no-clobber (#297)
# --------------------------------------------------------------------------- #
# The mode exists because `/adopt`'s contract ("never overwrite an existing
# file") and `_seedable`'s ("a marker means the kit may render over this") are
# both right and jointly destructive: an adopter who took the pre-#288 `cp -r`
# quickstart and then EDITED what landed owns a file that still carries a marker.
# PR #294 tried four times to make that safe from a workflow document and shipped
# a new way to destroy a file each time; #297 records the nine findings. These
# tests are the reason to move it here — a markdown snippet is executed by
# nothing, and `make test` passed in full while every one of those defects shipped.


def _marked_but_mine(marker: str) -> str:
    """A file in the state the flag exists for: a real kit marker on line 1, and
    the adopter's own content below it. Indistinguishable from a pristine
    skeleton by anything init.sh can read, which is why the answer is to refuse
    rather than to classify harder."""
    return f"<!-- {marker} -->\n# my own doctrine\n\nparagraphs I would lose\n"


@pytest.mark.kit_repo_only("docs/templates")
@pytest.mark.parametrize("marker", [kit_own_marker, template_marker])
def test_no_clobber_leaves_a_marked_file_byte_identical(tmp_path: Path, marker) -> None:
    """The core claim, with the bare run as its positive control IN THE SAME
    TEST.

    Asserting only "the file survived --no-clobber" passes vacuously against a
    fixture that lost its marker — and "left untouched" is also the outcome for
    an unmarked file, so nothing about the assertion would look wrong. Running
    the identical bytes both ways proves the marker is live and that the FLAG is
    what changed the outcome.

    BOTH markers, because `_seedable` reaches its MARKED verdict from two
    separate arms and this test originally exercised one. Mutating the other arm
    to the pre-change `return 0` left this test green — it was caught only
    incidentally, by the summary test, which happened to use the other literal.
    A defence that depends on which literal an unrelated test picked is not one.

    The parameters are the FUNCTIONS, not their values: these helpers read
    init.sh at call time, and calling them at module scope would run during
    collection, where a raise takes the whole session down (#226/#233)."""
    original = _marked_but_mine(marker())

    clobbered = _fixture(tmp_path / "bare", config=shipped_config(), templates=True)
    (clobbered / "AGENTS.md").write_text(original, encoding="utf-8")
    bare = _run_init(clobbered)
    assert (clobbered / "AGENTS.md").read_text(encoding="utf-8") != original, (
        "positive control failed: the bare run did NOT render over this fixture, "
        "so it is not in the MARKED state and the --no-clobber assertion below "
        "would pass for the wrong reason"
    )
    assert "seeded AGENTS.md" in bare.stdout

    protected = _fixture(tmp_path / "flagged", config=shipped_config(), templates=True)
    (protected / "AGENTS.md").write_text(original, encoding="utf-8")

    result = _run_init(protected, "--no-clobber")

    assert (protected / "AGENTS.md").read_text(encoding="utf-8") == original
    assert "left untouched (--no-clobber): AGENTS.md" in result.stdout
    assert "seeded AGENTS.md" not in result.stdout


@pytest.mark.kit_repo_only("docs/templates")
def test_no_clobber_preserves_a_link_whose_target_is_marked(tmp_path: Path) -> None:
    """The link case, which is the one place the two modes differ in what they
    DESTROY rather than in what they write.

    A working symlink resolves as a regular file, so a link whose TARGET opens
    with a marker is MARKED. A bare run replaces the link with the rendered file
    — `test_seeding_through_a_symlink_replaces_the_link_not_its_target` pins
    that, and it is disclosed rather than fixed: the target keeps its bytes and
    only the link relationship is lost. `--no-clobber` declines it like any
    other MARKED target, so the relationship survives too.

    Pinned because `docs/agentic-dev-kit/workflows/adopt.md` now states this in prose, and a
    claim about behaviour that nothing executes is how the guard this whole
    change exists to replace went wrong nine times (#294, #297). Raised by
    CodeRabbit on PR #328."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.md"
    marked = f"<!-- {kit_own_marker()} — the link target -->\n# canonical, shared\n"
    victim.write_text(marked, encoding="utf-8")
    (repo / "AGENTS.md").symlink_to(victim)
    assert (repo / "AGENTS.md").is_symlink()  # positive control on the fixture

    result = _run_init(repo, "--no-clobber")

    assert (repo / "AGENTS.md").is_symlink(), (
        "the link was replaced — --no-clobber must decline a MARKED target "
        "whatever kind of directory entry reaches it"
    )
    assert (repo / "AGENTS.md").resolve() == victim.resolve()
    assert victim.read_text(encoding="utf-8") == marked
    assert "left untouched (--no-clobber): AGENTS.md" in result.stdout


@pytest.mark.kit_repo_only("docs/templates")
def test_no_clobber_still_seeds_a_genuinely_absent_target(tmp_path: Path) -> None:
    """The flag narrows seeding to ABSENT targets; it does not switch seeding
    off. Every assertion in this section's other tests is about a file NOT being
    written, so all of them pass against an init.sh that writes nothing at all —
    this is the one that fails."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    absent = repo / "docs" / "kit-handoff.md"
    assert not absent.exists()  # positive control on the fixture

    result = _run_init(repo, "--no-clobber")

    assert f"seeded {absent.relative_to(repo)}" in result.stdout
    rendered = absent.read_text(encoding="utf-8")
    assert "{{" not in rendered, "an absent target was seeded but left unrendered"


@pytest.mark.kit_repo_only("docs/templates")
def test_no_clobber_keeps_the_in_use_wording_for_an_unmarked_file(tmp_path: Path) -> None:
    """The two skip reasons must stay distinguishable in the output. An unmarked
    file was never seedable in either mode, and reporting it under the
    --no-clobber banner would put it in the end-of-run list of files the
    operator is told to go open and act on — busywork over files the kit was
    never going to touch."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    original = "# CLAUDE.md — mine, no marker anywhere\n"
    (repo / "CLAUDE.md").write_text(original, encoding="utf-8")

    result = _run_init(repo, "--no-clobber")

    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == original
    assert "CLAUDE.md already in use — left untouched" in result.stdout
    assert "left untouched (--no-clobber): CLAUDE.md" not in result.stdout


@pytest.mark.kit_repo_only("docs/templates")
def test_no_clobber_summarizes_every_file_it_declined(tmp_path: Path) -> None:
    """The per-file line is printed where the decision happens, hundreds of
    lines of output before the run ends. The operator has to ACT on each one, so
    the run repeats them at the end.

    Both call sites are covered on purpose: `seed_doc` is called once for the
    four narrative docs at their CONFIGURED paths and once for the two root
    entry points, and a summary fed from only one of those loops would still
    look right in a single-file test."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    (repo / "docs").mkdir(parents=True, exist_ok=True)
    declined = ("AGENTS.md", "docs/kit-friction-log.md")
    for path in declined:
        (repo / path).write_text(_marked_but_mine(template_marker()), encoding="utf-8")

    result = _run_init(repo, "--no-clobber")

    tail = result.stdout.split("--no-clobber left these existing files untouched:")
    assert len(tail) == 2, "the end-of-run summary was not printed"
    for path in declined:
        assert f"\n  {path}\n" in tail[1], f"{path} missing from the summary"
        assert (repo / path).read_text(encoding="utf-8") == _marked_but_mine(template_marker())


@pytest.mark.kit_repo_only("docs/templates")
def test_no_summary_when_nothing_was_declined(tmp_path: Path) -> None:
    """A summary printed over an empty list tells the operator to go open files
    that do not exist, and trains them to ignore the block that matters."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)

    result = _run_init(repo, "--no-clobber")

    assert "--no-clobber left these existing files untouched:" not in result.stdout


# The `--no-clobber` summary under `set -eu` (#397)
#
# Driven as an extracted FRAGMENT rather than through `_run_init`, and that is
# the whole reason these tests kill anything. The defect is unreachable
# end-to-end: `seed_doc` returns early on an empty `_target`, so no empty entry
# can enter `NO_CLOBBER_SKIPPED` today, and the trailing newline from the append
# does not produce an empty final iteration either (`read` hits EOF instead). A
# test that ran the whole installer would therefore pass with the fix REVERTED —
# a test that names a property and pins nothing, which is the shape the
# 2026-08-09 friction entry is about. Feeding the block directly is what makes
# the mutation kill.
_NO_CLOBBER_SUMMARY_DRIVER = r"""set -eu
NO_CLOBBER_SKIPPED="$1"
eval "$(sed -n '/^if \[ -n "\$NO_CLOBBER_SKIPPED" \]; then/,/^fi$/p' init.sh)"
echo "SUMMARY-BLOCK-COMPLETED"
"""

_CLOSING_GUIDANCE = "Each carries a kit marker on line 1"


@pytest.mark.parametrize(
    ("skipped", "label"),
    [
        ("AGENTS.md\nCLAUDE.md\n", "no empty entry"),
        ("AGENTS.md\n\n", "empty FINAL entry"),
        ("\nAGENTS.md\n", "empty leading entry"),
        ("AGENTS.md\n\n\n", "two trailing empty entries"),
    ],
    ids=["normal", "empty-final", "empty-leading", "two-empty-trailing"],
)
def test_the_no_clobber_summary_always_reaches_its_closing_guidance(
    tmp_path: Path, skipped: str, label: str
) -> None:
    """#397 acceptance 1: the summary reaches its closing guidance whatever the
    list contains.

    A `while` loop's exit status is its last iteration's. With the body ending
    in `[ -n "$_skipped" ] && echo …`, an empty final entry makes that chain
    false, the loop exits non-zero, the PIPELINE it terminates exits non-zero,
    and `set -eu` aborts the script between the file list and the four echoes
    explaining what to do about it — printing the problem and swallowing the
    instruction.

    The pipeline matters and is why the sibling shapes in `dev_session.sh` and
    `reconcile_sessions.sh` are not this bug: a STANDALONE `while` whose last
    body statement is a falsy `&&` chain exits 0 under `set -e` (the AND-OR
    list exemption), while the same loop at the end of a pipeline exits 1.
    Verified both directions before narrowing this test to the pipeline form.
    """
    (tmp_path / "init.sh").write_bytes((REPO_ROOT / "init.sh").read_bytes())

    proc = subprocess.run(
        ["sh", "-c", _NO_CLOBBER_SUMMARY_DRIVER, "_", skipped],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"the summary block aborted under `set -eu` with {label} "
        f"(rc={proc.returncode}); stderr={proc.stderr!r}"
    )
    assert "AGENTS.md" in proc.stdout, "the file list was not printed"
    assert _CLOSING_GUIDANCE in proc.stdout, (
        f"the block printed the file list and then died before its closing "
        f"guidance ({label}) — this is the #397 abort"
    )
    assert "SUMMARY-BLOCK-COMPLETED" in proc.stdout, (
        "control never left the summary block, so the run's own tail "
        "(`Upgrading later: …`) is lost too"
    )


def test_the_no_clobber_summary_skips_an_empty_entry_rather_than_listing_it(
    tmp_path: Path,
) -> None:
    """#397 acceptance 2: an empty entry is skipped SILENTLY.

    `|| continue` must not be traded for something that keeps the run alive by
    printing a blank bullet — the operator would be told to go open a file with
    no name. Pins the skip, not just the survival.
    """
    (tmp_path / "init.sh").write_bytes((REPO_ROOT / "init.sh").read_bytes())

    proc = subprocess.run(
        ["sh", "-c", _NO_CLOBBER_SUMMARY_DRIVER, "_", "AGENTS.md\n\nCLAUDE.md\n"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    bullets = [
        line for line in proc.stdout.splitlines() if line.startswith("  ")
    ]
    assert bullets == ["  AGENTS.md", "  CLAUDE.md"], (
        f"expected exactly the two named files as bullets, got {bullets!r}"
    )


@pytest.mark.kit_repo_only("docs/templates")
def test_an_unknown_flag_is_refused_before_anything_is_written(tmp_path: Path) -> None:
    """A mistyped safety flag must not degrade to the destructive default.
    `--no-clobbler` under the old parse loop was silently ignored: init.sh
    rendered over the adopter's files and exited 0, having declined the
    guarantee its caller asked for without saying so."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    original = _marked_but_mine(kit_own_marker())
    (repo / "AGENTS.md").write_text(original, encoding="utf-8")

    result = _run_init(repo, "--no-clobbler", check=False)

    # The exact status, not merely non-zero: usage() documents exit 2, and 1 is
    # what init.sh's own pre-existing error paths return, so `!= 0` would pass
    # against a run that failed for an unrelated reason. (CodeRabbit, PR #328.)
    assert result.returncode == 2, result.stderr
    assert "unknown argument '--no-clobbler'" in result.stderr
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == original


def test_help_documents_the_flag(tmp_path: Path) -> None:
    """A safety mode nothing advertises is one an operator does not reach for.
    `--help` is the only surface init.sh has for that."""
    repo = _fixture(tmp_path, config=shipped_config())

    result = _run_init(repo, "--help")

    assert "--no-clobber" in result.stdout
    assert "Usage: ./init.sh [--no-clobber] [--help]" in result.stdout


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
        # Anchored for the same reason `/reports/` is: the kit's state root is
        # always <repo-root>/state, and unanchored it reached a `src/state/`
        # created after the install, which no tracked-file guard can see (#385,
        # panel round 2).
        "/state/",
        ".devkit_state_root",
        ".claude/worktrees/",
        # Anchored (#385). Unanchored it matched a `reports` directory at any
        # depth, which is the whole defect — an adopter's committed
        # `domains/*/reports/` artifacts silently stopped being stageable.
        "/reports/",
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
# .gitignore: policy entries vs hygiene entries (#385)
# --------------------------------------------------------------------------- #


def _commit(repo: Path, *paths: str) -> None:
    """Track `paths` in the fixture repo. Identity is passed per-invocation
    because `_env` nulls the global git config, so there is no user.name to
    inherit — a plain `git commit` there fails with a message about identity
    and would read as a defect in the code under test."""
    run = lambda *argv: subprocess.run(  # noqa: E731 - local to this helper
        argv, cwd=repo, check=True, capture_output=True, env=_env(repo.parent)
    )
    run("git", "add", "--", *paths)
    run(
        "git",
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=fixture",
        "commit",
        "-qm",
        "fixture",
    )


def _write(repo: Path, rel: str, body: str = "x\n") -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_the_adopters_nested_reports_stay_stageable(tmp_path: Path) -> None:
    """#385, stated as the adopter's own observable rather than as a line count.

    cs-toolkit commits dated artifacts under `domains/*/reports/` behind a scheme
    of `**/reports/**` + `!**/reports/*_latest.*` negations. The unanchored
    `reports/` this seeded excluded the PARENT directory, and git does not
    descend into an excluded directory — so every negation went inert and the
    crons silently stopped committing new artifacts. Asked of `git check-ignore`,
    not of the .gitignore text: the defect was about matching semantics, and a
    text assertion would have passed straight through it."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_text(
        "**/reports/**\n!**/reports/*_latest.*\n", encoding="utf-8"
    )
    _write(repo, "domains/cv/reports/cv_latest.json", "{}\n")
    _commit(repo, ".gitignore", "domains/cv/reports/cv_latest.json")
    # A NEW artifact, untracked — the only kind git's ignore rules can reach, and
    # so the only kind the defect could break.
    _write(repo, "domains/cv/reports/other_latest.json", "{}\n")

    _run_init(repo)

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "domains/cv/reports/other_latest.json"],
        cwd=repo,
        env=_env(repo.parent),
        capture_output=True,
    )
    assert ignored.returncode == 1, (
        "init.sh made a committed-by-design report artifact un-stageable:\n"
        + (repo / ".gitignore").read_text(encoding="utf-8")
    )


def test_the_seeded_reports_line_cannot_reach_a_nested_reports_directory(
    tmp_path: Path,
) -> None:
    """The anchoring itself, with NOTHING pre-seeded — which is what makes this
    the regression test the one above only looked like.

    `test_the_adopters_nested_reports_stay_stageable` pre-seeds `**/reports/**`,
    so the already-rules guard fires and `add_policy_ignore_line` returns before
    the entry's anchoring is ever exercised: reverting `/reports/` to the pre-fix
    `reports/` left that test GREEN (panel, adversarial lens, mutation-verified).
    Here the kit's line is the only rule in the file, so the mutation has nowhere
    to hide — and the assertion is still `git check-ignore`, because the defect
    was about matching semantics."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    _write(repo, "domains/cv/reports/cv_latest.json", "{}\n")
    _write(repo, "reports/kit_scratch.md", "# derived\n")

    _run_init(repo)

    def ignored(rel: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", rel],
                cwd=repo,
                env=_env(repo.parent),
                capture_output=True,
            ).returncode
            == 0
        )

    assert ignored("reports/kit_scratch.md"), "the kit's own root reports/ is not ignored"
    assert not ignored("domains/cv/reports/cv_latest.json"), (
        "the seeded line reached a nested reports directory:\n"
        + (repo / ".gitignore").read_text(encoding="utf-8")
    )


def test_a_negation_only_rule_still_counts_as_the_adopters_policy(
    tmp_path: Path,
) -> None:
    """The prefix branch of the rule check, which the exact-match branch would
    otherwise mask: dropping it left the whole suite green, because every other
    fixture pairs its negations with a plain `**/reports/**` line that matches
    exactly (panel, correctness lens, mutation-verified).

    A repo whose only reports rules are negations has a policy too — it is
    mid-migration, or it un-ignores from a rule that lives elsewhere — and the
    kit's line would still go last and win."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_text("!**/reports/*_latest.*\n", encoding="utf-8")

    result = _run_init(repo)

    assert "/reports/" not in (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "already rules on '/reports/'" in result.stdout


def test_a_crlf_gitignore_line_is_still_recognised_as_a_rule(tmp_path: Path) -> None:
    """A Windows-authored `.gitignore` ends its lines with `\\r`. Git trims it
    and honours the rule; the scan did not, so a bare pattern normalised to
    neither an exact match nor a prefix and the kit appended a redundant line
    (panel, adversarial lens)."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_bytes(b"reports\r\n")

    _run_init(repo)

    assert "/reports/" not in (repo / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_a_policy_entry_is_skipped_when_the_repo_already_rules_on_it(
    tmp_path: Path,
) -> None:
    """An adopter with rules for a path has a policy. The kit's line would be
    appended AFTER it and later rules win, so an imposed line is unappealable —
    no ordering or negation downstream can defend against it."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_text("**/reports/**\n", encoding="utf-8")

    result = _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/reports/" not in lines
    assert "reports/" not in lines
    assert "already rules on '/reports/'" in result.stdout


def test_a_policy_entry_is_skipped_when_tracked_files_would_be_hidden(
    tmp_path: Path,
) -> None:
    """The second disagreement: no rule, but the repo already tracks files the
    entry would ignore. `state/` rather than reports/ on purpose — the class is
    not about one path — and at the ROOT, because that is what the anchored
    entry can still reach: an adopter whose own `state/` directory holds
    committed fixtures."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    _write(repo, "state/fixtures.json", "{}\n")
    _commit(repo, "state/fixtures.json")

    result = _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/state/" not in lines
    assert "tracks files that '/state/' would ignore" in result.stdout
    # The skip is per-entry, not a bail-out: everything the repo does not
    # disagree with is still seeded.
    assert "/reports/" in lines


def test_the_seeded_state_line_cannot_reach_a_nested_state_directory(
    tmp_path: Path,
) -> None:
    """The half the tracked-files guard cannot cover, and the reason `state/`
    is anchored too (panel, adversarial lens, demonstrated live).

    That guard only sees what is ALREADY committed. A JS repo that creates
    `src/state/` AFTER running `init.sh` was silently caught by the unanchored
    line — and `git add -A` skips an ignored path with no output at all, so the
    file simply stops appearing in `git status`. The kit's own state root is
    always `<repo-root>/state`, so the anchor gives up nothing."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)

    _run_init(repo)

    # Created after the installer ran — the case the guard structurally cannot see.
    _write(repo, "src/state/index.ts", "export const x = 1\n")
    _write(repo, "state/sandbox.json", "{}\n")

    def ignored(rel: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", rel],
                cwd=repo,
                env=_env(repo.parent),
                capture_output=True,
            ).returncode
            == 0
        )

    assert ignored("state/sandbox.json"), "the kit's own state sandbox is not ignored"
    assert not ignored("src/state/index.ts"), (
        "the seeded line reached a nested state directory:\n"
        + (repo / ".gitignore").read_text(encoding="utf-8")
    )


def test_an_indented_legacy_line_is_reported_as_the_kits_own_not_as_a_policy(
    tmp_path: Path,
) -> None:
    """`.gitignore` is hand-edited, and an indented line is ordinary. The
    debris check matched exactly while the rule check trimmed blanks, so an
    indented `reports/` was reported as the adopter's own policy — the two
    messages swapped (panel, adversarial lens)."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_text("  reports/\n", encoding="utf-8")

    result = _run_init(repo)

    assert "seeded by an older" in result.stdout
    assert "already rules on '/reports/'" not in result.stdout


def test_hygiene_entries_are_seeded_even_when_the_repo_disagrees(
    tmp_path: Path,
) -> None:
    """The other side of the split. `config/*.local.yaml` is the only thing
    keeping an adopter's operator id out of git, so a repo that already tracks
    such a file must still get the rule — an always-wins append is the RIGHT
    shape for hygiene and the wrong one for policy."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    _write(repo, "config/dev-model.local.yaml", "notify:\n  operator_id: someone\n")
    _commit(repo, "config/dev-model.local.yaml")

    _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "config/*.local.yaml" in lines


def test_an_older_unanchored_reports_line_is_reported_not_rewritten(
    tmp_path: Path,
) -> None:
    """A repo seeded before #385 carries the unanchored line, and the guards
    cannot help — the entry is already there. `.gitignore` is adopter-owned, so
    the kit says what the line does and edits nothing."""
    repo = _fixture(tmp_path, config=shipped_config(), git=True)
    (repo / ".gitignore").write_text("reports/\n", encoding="utf-8")

    result = _run_init(repo)

    assert "unanchored 'reports/' line" in result.stdout
    assert (repo / ".gitignore").read_text(encoding="utf-8").splitlines()[0] == "reports/"


def test_policy_seeding_survives_a_tree_that_is_not_a_git_repo(tmp_path: Path) -> None:
    """The tracked-file probe asks git a question, and `init.sh` is documented as
    runnable before `git init`. No repo means nothing is tracked, so every policy
    entry is seeded — the pre-#385 behaviour, which is what an empty tree wants."""
    repo = _fixture(tmp_path, config=shipped_config())

    _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in ("/state/", ".devkit_state_root", ".claude/worktrees/", "/reports/"):
        assert entry in lines


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
    assert "/state/" in lines
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

    The drift check does not cover this. `init.sh` IS tracked in
    `kit-manifest.json` since #362 — this docstring said the opposite, which was
    true when written and is the same stale claim #382 found in two workflow
    documents — but that check compares the installer's BYTES against the kit's,
    which says nothing about whether the values it stamps agree with
    `config/dev-model.yaml`. Two files can each match their own manifest entry
    and still disagree with each other, so this test is what holds them
    together, and a new adopter would otherwise get different panel compute than
    this repo runs. (Found by the panel's correctness lens, which flagged it as
    out of scope for the change it was reviewing; corrected here because the
    change was in this file and the claim is the class the same session was
    sweeping.)
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


def _snapshot(path: Path) -> tuple:
    """Everything about `path` that a write could change, for any file type.

    Deliberately not `read_text()`: these fixtures point it at a symlink, an
    unreadable directory and a plain file, and the shape under test is the one
    thing that must not decide how thoroughly it is checked.

    Recursive, and that is load-bearing. The first version recorded a
    directory's child NAMES only, so deleting `.codex/hooks.json` and writing a
    regular file back under the same name left the snapshot identical — a
    round-6 lens did exactly that and all four parametrizations passed. Each
    child now carries its own type and content or link target.

    Symlinks are tested before existence: a dangling one is `exists() == False`
    and must still be recorded as the symlink it is, since replacing it with a
    real file is precisely the regression above.
    """
    if path.is_symlink():
        return ("symlink", str(path.readlink()))
    if not path.exists():
        return ("absent",)
    if path.is_dir():
        try:
            children = sorted(path.iterdir(), key=lambda c: c.name)
        except PermissionError:
            # mode 000 — unreadable is itself the state being preserved
            return ("dir", "unreadable", oct(path.stat().st_mode))
        return ("dir", *((c.name, _snapshot(c)) for c in children))
    try:
        return ("file", path.read_text(encoding="utf-8"))
    except (PermissionError, UnicodeDecodeError) as exc:
        return ("file", type(exc).__name__)


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
    """`register_pr_hook` reads neither config path, and this is the shape that
    proves it rather than asserting it.

    A FIFO is the one entry that does not fail fast: anything opening it for
    reading blocks until a writer appears, which here is never. So a run that
    completes over a FIFO at these paths cannot have read them — where a run
    that merely errors could have.

    This began as a guard test. A round-4 lens mutated the `-f` in
    `[ -f .codex/hooks.json ]` to `-e`, the whole suite stayed green, and the
    real `init.sh` hung until killed. The guard was then deleted along with the
    check it protected, so the test now pins the stronger property: a future
    edit that reintroduces any read of these paths fails here.

    The timeout is the assertion — a regression raises TimeoutExpired instead
    of hanging CI.
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
    # BOTH, including the runtime whose own path is the FIFO. Checking only the
    # other one let a round-6 lens gate the Codex block behind `[ ! -e ... ]` —
    # an existence test that never opens the file, so it cannot hang, and the
    # instructions vanish for an adopter who has an unusable config there. That
    # is the suppression bug this design deleted the read to prevent.
    assert "--runtime codex" in result.stdout
    assert "--runtime claude" in result.stdout


def test_register_pr_hook_reports_both_runtimes_and_writes_neither(tmp_path: Path) -> None:
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    assert "--runtime codex" in result.stdout
    assert "--runtime claude" in result.stdout
    # the whole point of the redesign: no write, so no filesystem shape to guard
    assert not (repo / ".codex").exists()
    assert not (repo / ".claude" / "settings.json").exists()


@pytest.mark.parametrize("shape", ["directory", "dangling_symlink"])
def test_no_advisory_when_the_engine_path_is_not_a_file(tmp_path: Path, shape: str) -> None:
    """Kills: `[ ! -f "$_hook_src" ]` weakened to `-e`.

    `-e` is true for a directory and false for a dangling symlink, so both
    shapes are needed to pin the guard from each side. A directory at the
    engine path under `-e` would print a registration naming something that
    cannot be executed — instructions that fail for the adopter with no clue
    why. A round-5 lens mutated this and the suite stayed green.
    """
    repo = _fixture(tmp_path, config=V1_CONFIG, git=True)
    hook = repo / "scripts" / "hooks" / "pr_followup_hook.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    if shape == "directory":
        hook.mkdir()
    else:
        hook.symlink_to(repo / "no-such-engine")

    result = _run_init(repo)

    assert "bootstrapped" in result.stdout
    assert "--runtime codex" not in result.stdout
    assert "--runtime claude" not in result.stdout


def test_the_printed_commands_are_pasteable_verbatim(tmp_path: Path) -> None:
    """The advisory is text an adopter copies into a JSON file, so the two
    variable idioms in it must survive to their stdout UNEXPANDED.

    Both are one backslash away from breaking silently. Drop it from
    `\\$(git rev-parse --show-toplevel)` and `init.sh` runs the substitution
    itself at print time, baking the absolute path of whatever machine ran the
    bootstrap into a snippet meant to be portable. The adopter pastes it, it
    works on their machine, and it is wrong for every other checkout — no
    error anywhere.

    A round-5 lens made exactly that edit and the whole suite stayed green,
    because every other assertion here matches loose substrings. These two
    are exact, which is the point: substring assertions cannot see expansion.

    **The Codex line now carries three `$` idioms rather than one** (`#359`): the
    substitution plus two `$root` reads. All three must survive unexpanded — and
    `$root` is the more fragile of the two kinds, because a missing backslash
    there expands to the EMPTY string at print time rather than to a visible
    absolute path, so the pasted snippet silently loses its own guard and
    reproduces `#359` in the adopter's config. That failure is invisible to any
    substring assertion, which is why this one stays exact.
    """
    repo = _with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    assert (
        '        root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        '[ -n "$root" ] || exit 0; exec python3 "$root/scripts/hooks/'
        'pr_followup_hook.py" --runtime codex' in result.stdout
    )
    assert (
        '        python3 "$CLAUDE_PROJECT_DIR/scripts/hooks/'
        'pr_followup_hook.py" --runtime claude' in result.stdout
    )
    # the matcher an adopter must reproduce exactly, quotes and anchors included
    assert 'matcher "^Bash$"' in result.stdout
    assert 'with if: "Bash(gh pr *)"' in result.stdout
    # nothing expanded: no absolute path from THIS machine leaked into the paste
    assert str(repo) not in result.stdout.split("note: the PR follow-through")[-1]


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

    # per line, not "somewhere in stdout": a round-6 lens hardcoded ONLY the
    # Codex line and the whole suite stayed green, because the Claude line's
    # correct interpolation satisfied the single substring check for both
    codex_line = next(ln for ln in result.stdout.splitlines() if "--runtime codex" in ln)
    claude_line = next(ln for ln in result.stdout.splitlines() if "--runtime claude" in ln)
    assert "scripts/devkit/hooks/pr_followup_hook.py" in codex_line
    assert "scripts/devkit/hooks/pr_followup_hook.py" in claude_line
    # The Claude line may not fall back to the default this fixture avoids. The
    # symmetrical check on the Codex line was VACUOUS and is gone: its template
    # always puts `)/` before the interpolation, so a leading-quote needle could
    # never match whether the value was right or wrong. The positive assertion
    # above already catches a Codex-side fallback — verified by mutation.
    assert "/scripts/hooks/pr_followup_hook.py\"" not in claude_line


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

    before = _snapshot(codex)

    try:
        result = _run_init(repo)  # check=True — a non-zero exit fails the test
        assert "bootstrapped" in result.stdout
        # Two assertions, each covering what the other cannot. `escaped.json`
        # is only reachable by the two symlink shapes, so it proved nothing for
        # the other two — a round-5 lens added `printf PWNED > .codex` and every
        # parametrization still passed. The snapshot closes that, but not the
        # symlink-escape shape: for a DIRECTORY it records entry names only, so
        # a write THROUGH a child symlink to an external target leaves it
        # unchanged. A round-6 lens established that by writing through the link
        # and watching the snapshot assertion pass while `escaped.exists()`
        # caught it. Neither line is redundant; do not drop either.
        assert _snapshot(codex) == before, f"init.sh modified .codex ({shape})"
        assert not escaped.exists(), "init.sh wrote through a symlink, outside .codex"
    finally:
        if shape == "unusable_dir":
            codex.chmod(0o755)


def test_the_advisory_matches_the_registrations_it_describes(tmp_path: Path) -> None:
    """The printed instructions and the two shipped files are the same claim in
    two places, and nothing tied them together.

    A round-5 lens mutated the printed matcher, the printed `if:`, the printed
    env-var idiom, and the shipped `.claude/settings.json`'s own matcher and
    `if` — four edits, each leaving the whole suite green. Static prose
    describing a file that nothing compares it against drifts silently, and
    this advisory is the ONLY route by which the hook reaches a new adopter.

    So every expected value here is READ FROM the shipped file rather than
    written down again. Editing either side alone fails this.
    """
    codex_cfg = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    claude_cfg = json.loads(
        (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    # both sides selected by content, not position: `[0]` is correct today
    # only because .codex/hooks.json has exactly one PostToolUse entry, and a
    # second unrelated hook would silently move this onto the wrong one
    codex_entry = next(
        e
        for e in codex_cfg["hooks"]["PostToolUse"]
        if any("pr_followup_hook" in h.get("command", "") for h in e["hooks"])
    )
    claude_entry = next(
        e
        for e in claude_cfg["hooks"]["PostToolUse"]
        if any("pr_followup_hook" in h.get("command", "") for h in e["hooks"])
    )
    claude_hook = next(
        h for h in claude_entry["hooks"] if "pr_followup_hook" in h.get("command", "")
    )
    codex_hook = next(
        h for h in codex_entry["hooks"] if "pr_followup_hook" in h.get("command", "")
    )

    result = _run_init(_with_pr_hook(_fixture(tmp_path, config=V1_CONFIG, git=True)))

    # the two command strings, verbatim — unexpanded, as an adopter pastes them
    assert codex_hook["command"] in result.stdout
    assert claude_hook["command"] in result.stdout
    # and the narrowing each runtime applies, from the file rather than restated
    assert f'matcher "{codex_entry["matcher"]}"' in result.stdout
    assert f'matcher "{claude_entry["matcher"]}"' in result.stdout
    assert f'if: "{claude_hook["if"]}"' in result.stdout
    # `if` lives on the hook entry beside `command`, not next to `matcher`, and
    # the advisory has to say so — an adopter who nests it wrong gets no error
    assert "if" not in claude_entry, "shipped file moved `if`; the advisory now lies"
    assert "beside `command`" in result.stdout


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
    # by content, like the two selections in the sibling test. This was the
    # THIRD instance of the same positional read; the first two were fixed in
    # 483fa3e and 3a67c45, and 3a67c45's message claimed "both levels filter by
    # content now, on both runtimes" while this one sat a test below, untouched.
    codex_pr_entry = next(
        e
        for e in parsed["hooks"]["PostToolUse"]
        if any("pr_followup_hook" in h.get("command", "") for h in e["hooks"])
    )
    assert codex_pr_entry["matcher"] == "^Bash$"


# ── register_budget_hooks — the SessionStart tripwires on Codex (#380) ───────


def _with_budget_engines(repo: Path) -> Path:
    """`register_budget_hooks` returns early when both engines are absent."""
    for name in ("check_doc_budget.py", "check_memory_budget.py"):
        engine = repo / "scripts" / name
        engine.parent.mkdir(parents=True, exist_ok=True)
        engine.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    return repo


def _codex_session_start_commands() -> list[str]:
    """The SessionStart command strings, read OUT OF the shipped file.

    Selected by CONTENT, never by position — the sibling helper's docstring
    records three separate defects from positional reads of this same file, the
    third of which sat one test below a commit message claiming both levels
    filtered by content.
    """
    parsed = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    return [
        hook["command"]
        for entry in parsed["hooks"]["SessionStart"]
        for hook in entry["hooks"]
        if "budget" in hook.get("command", "")
    ]


def test_the_shipped_codex_session_start_carries_no_matcher() -> None:
    """Kills: adding `"matcher": "startup"` to the Codex SessionStart entry.

    MEASURED on `codex-cli 0.147.0`, not read off documentation — the
    convergence plan assumed Claude's `startup`/`resume`/`clear` matcher shape
    transferred, and it does not. The one real SessionStart registration on the
    machine this was measured on (a shipping third-party integration) carries no
    `matcher` key.

    This is the load-bearing direction: a Codex registration carrying Claude's
    matcher is ACCEPTED and simply never fires, so the failure is silent and
    looks exactly like a hook that was never trusted. Nothing else in the suite
    would notice — `kit-manifest.json` does not track this file.
    """
    parsed = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    entries = [
        entry
        for entry in parsed["hooks"]["SessionStart"]
        if any("budget" in hook.get("command", "") for hook in entry["hooks"])
    ]
    assert entries, "no SessionStart budget registration in the shipped file"
    for entry in entries:
        assert "matcher" not in entry, (
            "the Codex SessionStart entry grew a `matcher` key. Codex accepts it "
            "and the hook then never fires — measured, not inferred."
        )
    assert len(_codex_session_start_commands()) == 2, (
        "both budget tripwires must be registered; Principle #1's mechanism "
        "reaching one runtime is what #380 is about"
    )


def test_the_budget_advisory_prints_the_shipped_codex_commands_verbatim(
    tmp_path: Path,
) -> None:
    """The advisory is text an adopter pastes into JSON, and the shipped file is
    what this repo actually runs. If they drift, one of the two is a lie and
    nothing else reports it.

    Read from the file rather than restated here, for the reason the sibling
    helper gives: comparing a copy against a copy makes a shared defect
    invisible.
    """
    repo = _with_budget_engines(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    # Whole line, for the reason the Claude sibling's comment gives: substring
    # matching misses a guard stripped from the FRONT of the shipped command.
    printed = {line.strip() for line in result.stdout.splitlines()}
    for command in _codex_session_start_commands():
        assert command in printed, (
            "the printed advisory has drifted from the shipped registration:\n"
            f"  shipped: {command}"
        )


def _claude_session_start_commands() -> list[str]:
    """The Claude SessionStart budget commands, read OUT OF the shipped file."""
    parsed = json.loads(
        (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    return [
        hook["command"]
        for entry in parsed["hooks"]["SessionStart"]
        for hook in entry["hooks"]
        if "budget" in hook.get("command", "")
    ]


def test_the_budget_advisory_prints_the_shipped_claude_commands_verbatim(
    tmp_path: Path,
) -> None:
    """The Claude half of the same advisory, drift-tested like the Codex half.

    Added because a review lens found the coverage ASYMMETRIC rather than
    absent: the Codex commands were compared byte-for-byte against
    `.codex/hooks.json` and the Claude ones against nothing, so a future edit to
    either surface would be caught on one runtime and silently not the other.

    Nothing was wrong when this was written — the two matched by hand — which is
    exactly when the asymmetry is worth closing, and `kit-manifest.json` tracks
    neither settings file, so no drift check covers it either.
    """
    repo = _with_budget_engines(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    shipped = _claude_session_start_commands()
    assert len(shipped) == 2, (
        "both budget tripwires must be registered on Claude too; found "
        f"{len(shipped)}"
    )
    # WHOLE LINE, not `in result.stdout`, and the difference is load-bearing.
    # Substring matching is directional: strip a guard from the FRONT of the
    # shipped command and what remains is a contiguous tail of the printed line,
    # so `command in stdout` still holds and the drift goes unseen. Measured —
    # with the substring form, removing `[ -z "$JOB_NAME" ] && ` from
    # .claude/settings.json left the whole suite green.
    printed = {line.strip() for line in result.stdout.splitlines()}
    for command in shipped:
        assert command in printed, (
            "the printed advisory has drifted from .claude/settings.json:\n"
            f"  shipped: {command}"
        )


def test_the_budget_advisory_says_an_untrusted_hook_is_skipped_silently(
    tmp_path: Path,
) -> None:
    """#380's acceptance names this sentence specifically, and it is the one an
    adopter cannot derive.

    Codex skips an untrusted hook with NO diagnostic: the session starts
    normally and reports nothing. Verified by controlled comparison on
    `codex-cli 0.147.0` — same repo, same `workspace-write` sandbox, the only
    difference `--dangerously-bypass-hook-trust`; with it the hook fired, without
    it nothing ran and nothing was said. Project trust (`trust_level =
    "trusted"`) is NOT hook trust and does not substitute for it.

    So the observable for "I forgot `/hooks`" is identical to the observable for
    "the hook is broken". An advisory that omits this sends the adopter to debug
    the command string.
    """
    repo = _with_budget_engines(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    assert "/hooks" in result.stdout
    lowered = result.stdout.lower()
    assert "silently" in lowered, (
        "the advisory must state that an untrusted hook is skipped SILENTLY"
    )
    assert "indistinguishable" in lowered, (
        "the advisory must say a skipped hook cannot be told from a broken one — "
        "that is the part an adopter cannot work out for themselves"
    )


def test_the_codex_session_start_takes_no_matcher_per_the_advisory(
    tmp_path: Path,
) -> None:
    """The advisory must SAY the matcher rule, not merely omit the key.

    An adopter hand-writing the entry from Claude's example will add
    `"matcher": "startup"` unless told otherwise, and Codex will accept it.
    """
    repo = _with_budget_engines(_fixture(tmp_path, config=V1_CONFIG, git=True))

    result = _run_init(repo)

    assert 'NO "matcher" key' in result.stdout
    assert "never fires" in result.stdout


@pytest.mark.parametrize("which", [0, 1], ids=["doc-budget", "memory-budget"])
def test_the_codex_budget_registrations_survive_a_git_less_tree(
    tmp_path: Path, which: int
) -> None:
    """`#359`'s guard, on the new commands — a LEVEL-2 test that EXECUTES them.

    `$(git rev-parse --show-toplevel)` is the empty string outside a worktree, so
    an unguarded form resolves to a path rooted at `/` and the interpreter exits
    non-zero on every session start. Both registrations are parametrized rather
    than looped, so a failure names which one broke.

    Text-level assertions cannot catch this: when the command string is wrong,
    the advisory and the shipped file are wrong identically.
    """
    command = _codex_session_start_commands()[which]

    outside = subprocess.run(
        ["sh", "-c", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=_env(tmp_path),
    )

    assert outside.returncode == 0, (
        "the Codex budget registration failed in a tree with no .git — #359. "
        f"exit={outside.returncode}\nstderr: {outside.stderr}"
    )
    assert not outside.stdout.strip(), f"unexpected output: {outside.stdout!r}"
    assert outside.stderr == "", (
        "the registration leaked git's error to stderr in a tree with no .git; "
        f"stderr: {outside.stderr!r}"
    )


@pytest.mark.parametrize(
    ("present", "absent"),
    [("check_doc_budget.py", "check_memory_budget.py"),
     ("check_memory_budget.py", "check_doc_budget.py")],
    ids=["only-doc-budget", "only-memory-budget"],
)
def test_the_budget_advisory_names_only_engines_that_exist(
    tmp_path: Path, present: str, absent: str
) -> None:
    """Kills: gating the advisory on the PAIR instead of on each engine.

    The early return covers "both absent". With exactly one present the advisory
    printed both commands anyway, and the absent one then fails at every session
    start with `|| true` hiding it — the same "instructions that fail with no clue
    why" the early return exists to prevent, one granularity down.

    Reachable rather than hypothetical: an adopter who declined one engine records
    it in `not_installed`, which is the state #398 is about. Found by the review
    bot on PR #401.
    """
    repo = _fixture(tmp_path, config=V1_CONFIG, git=True)
    engine = repo / "scripts" / present
    engine.parent.mkdir(parents=True, exist_ok=True)
    engine.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    result = _run_init(repo)

    assert "SessionStart budget tripwires" in result.stdout, (
        "one engine is present, so the advisory must still be printed"
    )
    assert present in result.stdout
    assert absent not in result.stdout, (
        f"the advisory named {absent}, which this repo does not have — the "
        "registration would fail at every session start with `|| true` hiding it"
    )


def test_no_budget_advisory_when_both_engines_are_absent(tmp_path: Path) -> None:
    """Kills: dropping the early return. An advisory naming engines the repo
    does not have is instructions that fail with no clue why — the same defect
    `test_no_advisory_when_the_engine_path_is_not_a_file` pins for the PR hook.
    """
    repo = _fixture(tmp_path, config=V1_CONFIG, git=True)

    result = _run_init(repo)

    assert "bootstrapped" in result.stdout
    assert "SessionStart budget tripwires" not in result.stdout


def _codex_registration_command() -> str:
    """The Codex registration's command string, read OUT OF the shipped file.

    Never a literal copied into this module: the defect below shipped because
    every existing assertion compared the registration's text against another
    copy of the same text, and a shared defect is invisible to a consistency
    check.
    """
    parsed = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    entry = next(
        e
        for e in parsed["hooks"]["PostToolUse"]
        if any("pr_followup_hook" in h.get("command", "") for h in e["hooks"])
    )
    hook = next(h for h in entry["hooks"] if "pr_followup_hook" in h.get("command", ""))
    return hook["command"]


def test_the_codex_registration_survives_a_git_less_tree(tmp_path: Path) -> None:
    """`#359`: the registration must not run `python3` against a path built from
    an empty string.

    `$(git rev-parse --show-toplevel)` yields the EMPTY STRING outside a
    worktree, so the bare form collapsed to `/…/pr_followup_hook.py` — an
    absolute path rooted at `/` — and `python3` exited 2. Because a `PostToolUse`
    failure does not halt a session, what an operator observes is a hook that
    silently stopped firing: the exact outcome the hook exists to prevent,
    reached by a different route than a moved file.

    **This is a LEVEL-2 test and that is the whole point (`#363`).** The kit
    already had level-1 coverage — `test_the_advisory_matches_the_registrations_it_describes`
    reads both shipped files and asserts `init.sh`'s printed advisory matches them
    verbatim, and the sibling above checks `--runtime`. Neither could catch this,
    because both compare *text*: when the command string itself is wrong, the
    advisory and the shipped file are wrong identically and every equality holds.
    So the command is EXECUTED here, through `sh -c`, exercising the shell
    expansion rather than a Python-side substitution of the placeholder.

    Two cwds, because one alone proves the wrong thing. A no-op that never
    resolved anything would pass the git-less case on its own.
    """
    command = _codex_registration_command()

    # Outside any worktree: must exit 0 and stay silent, having bailed BEFORE
    # invoking the interpreter.
    outside = subprocess.run(
        ["sh", "-c", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=_env(tmp_path),
    )
    assert outside.returncode == 0, (
        "the Codex registration failed in a tree with no .git — #359. "
        f"exit={outside.returncode}\nstderr: {outside.stderr}"
    )
    assert "No such file or directory" not in outside.stderr, (
        "the registration reached the interpreter with an unresolved root — the "
        f"#359 signature. stderr: {outside.stderr}"
    )
    assert not outside.stdout.strip(), f"unexpected output: {outside.stdout!r}"
    # Pins `2>/dev/null`. Without it git prints `fatal: not a git repository` on
    # EVERY Bash tool call in such a tree — the hook fires per tool use, so the
    # noise is per-call, not once. Mutation-checked: dropping the redirect
    # survived every other assertion here.
    assert outside.stderr == "", (
        "the registration leaked git's error to stderr in a tree with no .git; "
        f"a PostToolUse hook fires on every Bash call, so this is per-call noise. "
        f"stderr: {outside.stderr!r}"
    )

    # Positive control: inside a real worktree the same string must REACH the
    # hook rather than bail. Asserted through a variant naming a script that does
    # not exist, so a non-zero exit proves `exec` ran — the shipped hook exits 0
    # on an irrelevant tool call, which is indistinguishable from bailing out.
    probe = command.replace("pr_followup_hook.py", "no_such_hook_9f2a.py")
    assert probe != command, "probe substitution failed — did the script name change?"
    inside = subprocess.run(
        ["sh", "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    assert inside.returncode != 0, (
        "inside a worktree the registration bailed out instead of running the "
        "hook, so the guard added for #359 is too aggressive and the hook would "
        "never fire anywhere."
    )
    # The #359 check proper: the interpreter must be reached with the root
    # RESOLVED, not with a path rooted at `/`. Asserting the full expected path
    # rather than the basename is what makes this the actual check — an earlier
    # version tried `not inside.stderr.startswith("/no_such_hook")`, which can
    # never fail, because python3 prefixes its own program name
    # (`python3: can't open file '/no_such_hook…'`). The review bot caught that
    # vacuity; the basename-only assertion it replaced was true either way.
    assert f"{REPO_ROOT}/scripts/hooks/no_such_hook_9f2a.py" in inside.stderr, (
        "the interpreter was reached with a path rooted at `/` rather than at the "
        f"resolved worktree root — #359. stderr: {inside.stderr}"
    )


def test_the_codex_registration_execs_rather_than_forking_the_interpreter(
    tmp_path: Path,
) -> None:
    """`exec` must replace the shell, not spawn a child.

    Added because a correctness lens falsified the reason originally given for
    `exec` — that it "keeps the hook's own exit status". It does not: in `a; b; c`
    the status is `c`'s either way (`sh -c 'true; false'` and
    `sh -c 'true; exec false'` both exit 1, checked). The status behaviour was
    correct; the stated mechanism was fiction, and **nothing behavioural pinned
    `exec` at all** — only an incidental literal match in
    `test_the_printed_commands_are_pasteable_verbatim`, whose actual subject is
    backslash-escaping. So a future edit "cleaning up" the false rationale could
    drop `exec`, keep that text assertion in sync, and pass the whole suite.

    What `exec` really buys is process replacement, and this registration carries
    `"timeout": 10`. A timeout enforced by signalling the PID the runtime spawned
    reaches the interpreter directly rather than a wrapper shell that may not
    forward it — the difference between a timed-out hook dying and leaking an
    orphan.

    That is observable without Codex: with `exec`, the interpreter reports the
    shell's own PID; without it, a different one. Both directions are asserted, so
    the test cannot pass by being unable to tell them apart.
    """
    probe = tmp_path / "pid_probe.py"
    probe.write_text("import os\nprint(f'py_pid={os.getpid()}')\n", encoding="utf-8")

    command = _codex_registration_command()
    target = '"$root/scripts/hooks/pr_followup_hook.py"'
    assert target in command, f"registration shape changed; cannot build probe from {command!r}"
    probed = command.replace(target, f'"{probe}"')

    def pids(cmd: str) -> tuple[int, int]:
        out = subprocess.run(
            ["sh", "-c", f'echo "shell_pid=$$"; {cmd}'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        ).stdout
        found = dict(
            line.split("=", 1) for line in out.splitlines() if "=" in line and "_pid" in line
        )
        assert {"shell_pid", "py_pid"} <= found.keys(), f"probe produced no pids: {out!r}"
        return int(found["shell_pid"]), int(found["py_pid"])

    shell_pid, py_pid = pids(probed)
    assert shell_pid == py_pid, (
        "the registration forked the interpreter instead of exec'ing it, so the "
        "hook runs as a CHILD of the process the runtime spawned. Its "
        '`"timeout": 10` then signals a wrapper shell, which may not forward it. '
        f"shell={shell_pid} python={py_pid}"
    )

    # Control: the test must be able to see the difference it claims to check.
    #
    # `; :` is not decoration. Many shells replace themselves with the LAST
    # command of a `-c` list as an implicit tail-call, so a control that merely
    # drops `exec` can still report identical PIDs on such a shell — and this
    # test would then fail for a reason that has nothing to do with the
    # registration. A trailing no-op keeps the interpreter off the final position,
    # so a fork is guaranteed on every shell. Raised by the review bot, which
    # measured it across several `sh`/`bash` builds; the local shell happens to
    # fork either way, which is exactly why this needed catching by someone else.
    forked_shell, forked_py = pids(probed.replace("exec python3", "python3") + "; :")
    assert forked_shell != forked_py, (
        "the control did not fork, so this test cannot distinguish exec from "
        "no-exec and its assertion above proves nothing"
    )


def _with_stub_uv(tmp_path: Path) -> tuple[dict[str, str], Path]:
    """A `uv` on PATH that records having been called, and does nothing else.

    Lets the SessionStart registrations be executed for real while observing only
    whether they reached the interpreter. The alternative — running the actual
    budget script and looking for its output — cannot see the guard under test,
    because `--quiet` prints nothing on a repo that is under budget and the
    absence of output would then satisfy both arms.
    """
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir(parents=True, exist_ok=True)
    witness = tmp_path / "uv-was-called"
    stub = stub_dir / "uv"
    stub.write_text(f'#!/bin/sh\n: > "{witness}"\nexit 0\n', encoding="utf-8")
    stub.chmod(0o755)
    env = _env(tmp_path)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env.pop("JOB_NAME", None)
    return env, witness


@pytest.mark.parametrize("which", [0, 1], ids=["doc-budget", "memory-budget"])
def test_the_codex_budget_registration_skips_a_cron_run(
    tmp_path: Path, which: int
) -> None:
    """The `JOB_NAME` guard, EXECUTED — the level-2 test this guard did not have.

    Mutation-checked, and the result is why this exists: dropping
    `[ -z "${JOB_NAME:-}" ] || exit 0` from both shipped commands killed exactly
    one test, `..._prints_the_shipped_codex_commands_verbatim`, which compares the
    advisory against the shipped file. That is a DRIFT check — it fails only
    because one surface moved. Change both surfaces consistently and the guard is
    gone with the suite green, which is the level-1/level-2 distinction the
    git-less sibling's docstring draws.

    Both arms are asserted. Without the positive control, a registration that had
    stopped invoking anything at all would satisfy the cron arm and pass.
    """
    command = _codex_session_start_commands()[which]
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    env, witness = _with_stub_uv(tmp_path)

    interactive = subprocess.run(
        ["sh", "-c", command], cwd=repo, capture_output=True, text=True, env=env
    )
    assert interactive.returncode == 0, interactive.stderr
    assert witness.exists(), (
        "the registration never reached `uv` even outside a cron run, so the "
        "cron assertion below would hold for the wrong reason"
    )

    witness.unlink()
    cron = subprocess.run(
        ["sh", "-c", command],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**env, "JOB_NAME": "nightly"},
    )

    assert cron.returncode == 0, cron.stderr
    assert not witness.exists(), (
        "the budget tripwire ran under JOB_NAME — a scheduled/CI session gets a "
        "housekeeping nudge no human will read, and the guard that stops it is "
        "pinned by nothing but a drift check"
    )


@pytest.mark.parametrize("which", [0, 1], ids=["doc-budget", "memory-budget"])
def test_the_claude_budget_registration_skips_a_cron_run(
    tmp_path: Path, which: int
) -> None:
    """The Claude registration's `JOB_NAME` guard, EXECUTED — the half that had
    no protection of any kind.

    Found by mutation, not by reading: stripping `[ -z "$JOB_NAME" ] && ` from
    both commands in `.claude/settings.json` left the FULL suite green
    (1106/1106, driftcheck included). Neither `.claude/settings.json` nor
    `.codex/hooks.json` is tracked by `kit-manifest.json`, so the drift check
    cannot see either file, and the sibling Codex guard had an executed test
    while this one had nothing.

    The drift test alone is not enough here and that is measured too: the
    shipped command is a contiguous TAIL of the printed advisory line, so a
    substring comparison passes with the guard removed. This executes the real
    command string instead.
    """
    command = _claude_session_start_commands()[which]
    project = tmp_path / "project"
    project.mkdir()
    (project / "scripts").mkdir()
    env, witness = _with_stub_uv(tmp_path)
    env["CLAUDE_PROJECT_DIR"] = str(project)

    interactive = subprocess.run(
        ["sh", "-c", command], cwd=tmp_path, capture_output=True, text=True, env=env
    )
    assert interactive.returncode == 0, interactive.stderr
    assert witness.exists(), (
        "the registration never reached `uv` even outside a cron run, so the "
        "cron assertion below would hold for the wrong reason"
    )

    witness.unlink()
    cron = subprocess.run(
        ["sh", "-c", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**env, "JOB_NAME": "nightly"},
    )

    assert cron.returncode == 0, cron.stderr
    assert not witness.exists(), (
        "the Claude budget tripwire ran under JOB_NAME — a scheduled/CI session "
        "gets a housekeeping nudge no human will read"
    )


def _with_stub_git(tmp_path: Path, body: str) -> tuple[dict[str, str], Path]:
    """`_env` with a stub `git` first on PATH. `body` is its script body.

    The guard chain in the Codex registration has three clauses and real `git`
    exercises only one of them, so the other two are only reachable with a `git`
    that behaves in a way the installed one never does. That is the point rather
    than a contrivance: each stub below corresponds to a documented git behaviour
    (a bare repo, a wrapper on an adopter's PATH) that the shipped command must
    survive.

    **The witness file is what makes the stub tests non-vacuous, and it exists
    because they were vacuous.** An adversarial lens disabled the `PATH` prepend
    below — leaving the shipped guards intact — and both callers still passed.
    Outside a repo, real `git rev-parse --show-toplevel` exits 128 with EMPTY
    stdout, which at the shell level is indistinguishable from both stub
    behaviours: "succeeds printing nothing" is what real git's failure already
    looks like on stdout, and "fails printing a path" stops printing a path when
    the stub never runs. So each caller's assertions held for the wrong reason and
    nothing noticed the stub was never invoked.

    The stub now creates `witness` on every call and each caller asserts it
    exists, so a harness edit that breaks the `PATH` override — a typo, a wrong
    dict key, an ordering change — fails loudly instead of silently testing
    nothing.

    Returns `(env, witness)`. `tmp_path` is per-test, so no name needs to be
    unique beyond it; an earlier version derived the directory name from
    `hash(body)`, which added a collision surface for no isolation gain.
    """
    stub_dir = tmp_path / "stubbin"
    stub_dir.mkdir()
    witness = tmp_path / "stub-git-was-invoked"
    stub = stub_dir / "git"
    # `: >` rather than `touch`: one less external binary than the code under
    # test already depends on.
    stub.write_text(f'#!/bin/sh\n: > "{witness}"\n{body}\n', encoding="utf-8")
    stub.chmod(0o755)
    env = _env(tmp_path)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    return env, witness


def test_the_codex_registration_guards_a_git_that_fails_while_printing_a_path(
    tmp_path: Path,
) -> None:
    """Pins the FIRST `|| exit 0` — the clause an adversarial lens showed nothing
    covered.

    Its finding was that this clause is behaviourally redundant with
    `[ -n "$root" ]`, because real `git rev-parse --show-toplevel` prints nothing
    to stdout when it fails (`exit=128, stdout=[]`, checked), so the empty-string
    guard already catches that path. Removing the first clause was caught only by
    an unrelated hardcoded-literal test.

    Redundant against the *installed* git is not redundant against every git. The
    one case where this clause alone acts is a `git` that **exits non-zero while
    writing a path to stdout** — a wrapper on an adopter's PATH, a shim, a
    misconfigured alias. Then `$root` is non-empty and plausible, `[ -n "$root" ]`
    passes, and without the first clause the hook would run against a path git
    itself reported as an error.

    Deleting the clause was considered and rejected: it fails CLOSED, and
    `safety-critical-changes.md` rule 3 warns specifically against trading a
    fail-closed limitation for a fail-open one. Pinning it costs one test.
    """
    env, witness = _with_stub_git(tmp_path, "echo /nonexistent/wrong/root\nexit 1")

    result = subprocess.run(
        ["sh", "-c", _codex_registration_command()],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
    )

    # Before any conclusion: the stub must actually have been the `git` that ran.
    # Real git's failure outside a repo is indistinguishable from this stub's
    # behaviour at the shell level, so without this the assertions below hold
    # whether or not the PATH override worked. See `_with_stub_git`.
    assert witness.exists(), (
        "the stub git was never invoked, so this test proves nothing about the "
        "clause it names — the PATH override in `_with_stub_git` is broken."
    )
    assert result.returncode == 0, (
        "git failed but printed a path, and the registration used it anyway — "
        "the first `|| exit 0` is what refuses a root git itself reported as an "
        f"error. exit={result.returncode}\nstderr: {result.stderr}"
    )
    assert "No such file or directory" not in result.stderr, (
        "the interpreter was reached with a root git reported as failed; "
        f"stderr: {result.stderr}"
    )


def test_the_codex_registration_guards_an_empty_root_that_git_reports_as_success(
    tmp_path: Path,
) -> None:
    """Pins `[ -n "$root" ] || exit 0` specifically — the clause the sibling test
    above does NOT cover.

    Established by mutation rather than assumed: deleting that clause leaves the
    sibling test passing, because real `git rev-parse` *exits non-zero* outside a
    worktree and `|| exit 0` already catches that path. So the empty-string guard
    only earns its place against a `git` that succeeds and prints nothing — and
    nothing in this suite produced one.

    This test produces one, with a stub `git` first on `PATH` that exits 0 with
    empty stdout. That is not a contrived shape: `--show-toplevel` is documented
    to fail in a bare repository, `GIT_DIR`/`GIT_WORK_TREE` can point somewhere
    that resolves oddly, and a wrapper `git` on an adopter's PATH is common. If
    the guard is ever deleted as redundant, this fails and says why.
    """
    # Succeeds, prints nothing — the one case `|| exit 0` cannot see.
    env, witness = _with_stub_git(tmp_path, "exit 0")

    result = subprocess.run(
        ["sh", "-c", _codex_registration_command()],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
    )

    # See the sibling test and `_with_stub_git`: without this, real git's ordinary
    # failure satisfies the assertions below and the stub is never needed.
    assert witness.exists(), (
        "the stub git was never invoked, so this test proves nothing about the "
        "clause it names — the PATH override in `_with_stub_git` is broken."
    )
    assert result.returncode == 0, (
        "with a git that succeeds and prints nothing, the registration ran "
        "python3 against a path built from an empty string — #359's mechanism, "
        f"reached without git failing. exit={result.returncode}\n{result.stderr}"
    )
    assert "No such file or directory" not in result.stderr, (
        "the interpreter was reached with an empty root: the command built "
        f"'/…' from an empty $root. stderr: {result.stderr}"
    )


# --------------------------------------------------------------------------- #
# The upgrade workflow's own `init.sh` invocation (#330)
# --------------------------------------------------------------------------- #
# These two run the command OUT OF THE DOCUMENT rather than a literal copied
# from it, because the defect #330 reports is precisely a document drifting
# from the behaviour it promises: `upgrade.md` ran `init.sh` bare while its own
# opening line claimed it "never replaces a file without knowing it is safe to
# replace". A test asserting `"--no-clobber" in text` would pass on a doc that
# had moved the flag to a code block nothing tells you to run.
#
# This is also the friction log's 2026-08-04 entry (severity H) applied to one
# case: the kit ships prose containing executable payloads and had no way to
# execute them, so every defect in one was found by a human running it by hand.


def _step2_refresh_block() -> str:
    """upgrade.md's Step 2 refresh block, as text.

    Anchored on the `cp` of `init.sh` that opens it, so a code block elsewhere in
    the document cannot be picked up instead. The anchor tolerates both the bare
    `/tmp/agentic-dev-kit` form and the `$KIT`-anchored one (#399) — pinning the
    literal path here would make the cross-tree rewrite look like a missing block.
    """
    doc = (
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows" / "upgrade.md"
    ).read_text(encoding="utf-8")
    blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", doc, re.DOTALL)
    matching = [b for b in blocks if re.search(r"cp \"?(\$KIT|/tmp/agentic-dev-kit)", b)]
    assert len(matching) == 1, f"expected one Step 2 refresh block, found {len(matching)}"
    return matching[0]


def _upgrade_init_argv() -> list[str]:
    """The `init.sh …` line from upgrade.md Step 2, as argv beyond the script."""
    matching = _step2_refresh_block()
    lines = [
        ln.strip()
        for ln in matching.splitlines()
        if re.match(r'^\s*(\./|"\$REPO/)init\.sh\b', ln)
    ]
    assert len(lines) == 1, f"expected one init.sh invocation, found {lines!r}"
    argv = shlex.split(lines[0].split("#")[0])
    assert argv[0].endswith("init.sh"), argv
    return argv[1:]


@pytest.mark.kit_repo_only("docs/templates", "docs/agentic-dev-kit/workflows/upgrade.md")
def test_upgrade_workflows_init_invocation_does_not_destroy_a_marked_but_edited_file(
    tmp_path: Path,
) -> None:
    """Kills: dropping `--no-clobber` from upgrade.md Step 2.

    The exposed party is a long-running adopter, not a new one: `README.md`
    documents re-running `init.sh` as the supported upgrade path, and a repo
    that took the pre-#288 `cp -r` quickstart carries marked skeletons whose
    line 1 nobody removed while filling the body with their own doctrine.

    Bare, this run reports `seeded AGENTS.md` and the content is gone with no
    backup — which is the whole of #330."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    mine = f"<!-- {template_marker()} -->\n\n# my own doctrine, months of it\n"
    (repo / "AGENTS.md").write_text(mine, encoding="utf-8")

    result = _run_init(repo, *_upgrade_init_argv())

    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == mine
    # and the decline is reported rather than silent — the property that makes
    # the pristine-skeleton regression acceptable (see the workflow's table).
    assert "left untouched" in result.stdout


@pytest.mark.kit_repo_only("docs/templates", "docs/agentic-dev-kit/workflows/upgrade.md")
def test_upgrade_workflows_init_invocation_still_seeds_a_genuinely_absent_file(
    tmp_path: Path,
) -> None:
    """Kills: narrowing Step 2's invocation until it stops seeding at all.

    #330 argues against `--no-clobber` here on the grounds that it would stop a
    partially-adopted repo receiving `AGENTS.md`. It does not — the flag narrows
    seeding to ABSENT targets, and absent is this case — but nothing pinned that,
    and upgrade.md depends on it in the paragraph beginning "The templates have to
    land **before** `init.sh` runs": that is the path by which an existing adopter
    first receives either root entry point at all.

    Cited by its opening words rather than by line number, which is the review
    finding that produced this wording: the first draft said `upgrade.md:152-158`
    and was already two lines stale in the same commit that wrote it."""
    repo = _fixture(tmp_path, config=shipped_config(), templates=True)
    assert not (repo / "AGENTS.md").exists()  # positive control on the fixture

    _run_init(repo, *_upgrade_init_argv())

    assert (repo / "AGENTS.md").exists()
    assert template_marker() not in (repo / "AGENTS.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# upgrade.md Step 2's template copy is gated on the declared install set (#398)
#
# Executed, not read. A prose assertion (`"not_installed" in text`) would pass on
# a document that mentions the gate in a paragraph while the code block above it
# still copies unconditionally — which is exactly the failure mode the sibling
# section's banner describes for `--no-clobber`.


def _upgrade_template_copy_block() -> str:
    """The Step 2 refresh block from upgrade.md, minus the two lines that need a
    real kit checkout and a real installer.

    Anchored on the `cp` of `init.sh` like `_upgrade_init_argv`, so a future code
    block elsewhere in the document cannot be picked up instead.
    """
    # The `init.sh` INVOCATION is kept and stubbed by `_run_template_copy`, not
    # stripped. Stripping it is how a HIGH went uncaught: the gate's refusal used
    # `break`, which leaves the `for` loop while the next line runs the installer
    # anyway — "Copied nothing" followed by the workflow proceeding past its own
    # hard stop. No test could see it while the interaction was cut out of the
    # extract (review panel, adversarial lens).
    #
    # `cd` still goes, and for the opposite reason: keeping it would make
    # `..._writes_into_repo_even_when_the_shell_sits_in_the_kit_clone` vacuous,
    # since the block would put itself in the right tree before writing. Its
    # presence in the SHIPPED block is asserted separately below.
    kept = [
        line
        for line in _step2_refresh_block().splitlines()
        # `cd "$REPO"` specifically, not any `cd `. An over-broad strip is how
        # the round-2 HIGH stayed invisible: whatever the extract removes, no
        # test can see. If Step 2 ever gains a second `cd`, this must fail
        # loudly rather than quietly review a block that is not what ships.
        if not re.match(r'^\s*(cd "\$REPO"|cp "\$KIT/init\.sh"|chmod \+x)', line)
    ]
    body = "\n".join(kept)
    # Asserted against the SHIPPED block, not the stripped one, and that is the
    # point. The `cd` has to be stripped for the extracted body to run against a
    # fixture, which left it pinned by nothing: delete `cd "$REPO"` from
    # upgrade.md and every test in this section still passes, while `init.sh`
    # resolves the config and `docs/templates/*.tmpl` against the KIT clone —
    # #399's exact failure, one line over from the one being guarded. Found by
    # the review bot on PR #401.
    assert re.search(r'^\s*cd "\$REPO"', _step2_refresh_block(), re.M), (
        "Step 2 no longer cds into $REPO before running init.sh — the installer "
        "resolves config and templates against the working directory (#399)"
    )
    assert "not_installed" in body, (
        "the Step 2 code block no longer consults `not_installed` — the gate moved "
        "into prose, or was removed (#398)"
    )
    return body


def _fake_kit_templates(tmp_path: Path) -> Path:
    """A stand-in for /tmp/agentic-dev-kit/docs/templates, since the block's
    source path is hardcoded (that hardcoding is #343, not this test's subject)."""
    src = tmp_path / "kit" / "docs" / "templates"
    src.mkdir(parents=True)
    for name in ("handoff.md.tmpl", "friction-log.md.tmpl", "AGENTS.md.tmpl"):
        (src / name).write_text(f"# {name}\n", encoding="utf-8")
    return src


def _run_template_copy(
    repo: Path, src: Path, *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run the extracted block with `$KIT`/`$REPO` bound as Step 0 binds them.

    `cwd` defaults to the repo but is overridable on purpose: #399's whole subject
    is a working directory that is not where the writes belong, and a block that
    only works when cwd already happens to be right has not been tested for it.
    """
    # Substitute the real installer with a witness writer: the block's LAST act
    # is running `init.sh`, and whether it runs is exactly what the gate's
    # refusal has to control. Running the real one here would rebuild config in
    # a fixture and tell us nothing about the guard.
    block = _upgrade_template_copy_block()
    stubbed = re.sub(
        r'^(\s*)"\$REPO/init\.sh" --no-clobber\s*$',
        r'\1: > "$REPO/INIT_SH_RAN"',
        block,
        flags=re.M,
    )
    assert stubbed != block, (
        "the init.sh invocation was not found in the extracted block, so the "
        "stub did not apply and the gate/installer interaction is untested"
    )
    return subprocess.run(
        ["sh", "-c", stubbed],
        cwd=cwd or repo,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=check,
        env={**os.environ, "REPO": str(repo), "KIT": str(src.parent.parent)},
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2s_branch_step_fails_loudly_when_the_cd_fails() -> None:
    """Kills: reverting the branch step to `cd "$REPO" && git checkout -b …`.

    Text-level on purpose, and weaker than the sibling tests here, which execute
    what they check. Nothing in the kit executes this particular block — it
    creates a branch — and #374 tracks the general gap that fenced shell ships
    unchecked. Added because the mutation round found the `|| exit 1` fix pinned
    by nothing at all, which is worse than pinned weakly: with the `&&` form the
    `cd` can fail, the branch is never created, only the cd error is reported,
    and Step 2 then writes into whatever tree the shell was in — #399 reached
    through the one instruction that is supposed to establish the branch
    guarantee.
    """
    doc = (
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows" / "upgrade.md"
    ).read_text(encoding="utf-8")
    blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", doc, re.DOTALL)
    matching = [b for b in blocks if "git checkout -b" in b]
    assert len(matching) == 1, f"expected one branch block, found {len(matching)}"

    assert re.search(r'^cd "\$REPO" \|\| exit 1$', matching[0], re.M), (
        "the branch step must fail loudly when the cd fails; found:\n" + matching[0]
    )
    assert '&& git checkout' not in matching[0], (
        "the branch step is chained to the cd with `&&` — a failed cd then reports "
        "only the cd error and never creates the branch"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_does_not_copy_a_template_the_repo_declared_declined(
    tmp_path: Path,
) -> None:
    """#398: a path in `not_installed` is a DECISION, and copying it in reverses
    it silently — `cp` says nothing, the `missing` count goes DOWN (which reads as
    an improvement), and Step 4's `--record-install` then derives the installed set
    from disk and writes the reversal in as fact.

    An adopter caught this before acting and declined the instruction; nothing in
    the kit would have caught it after.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(
        json.dumps(
            {
                "kit_commit": "deadbeef",
                "files": {},
                "not_installed": [
                    "docs/templates/handoff.md.tmpl",
                    "docs/templates/friction-log.md.tmpl",
                ],
            }
        ),
        encoding="utf-8",
    )

    result = _run_template_copy(repo, src)

    installed = sorted(p.name for p in (repo / "docs" / "templates").glob("*.tmpl"))
    assert installed == ["AGENTS.md.tmpl"], (
        "a declined template was copied in, converting a recorded decision into "
        f"an install (#398). present: {installed}"
    )
    # and the skip is REPORTED — a silent skip is the other half of the same
    # defect, one direction over: the operator cannot see what was withheld.
    assert "declined" in result.stdout
    assert "handoff.md.tmpl" in result.stdout


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_copies_every_template_when_nothing_was_declared(
    tmp_path: Path,
) -> None:
    """The gate must not become a blanket refusal.

    A repo with no baseline at all has declared no scope, so every template is
    copied — the pre-#398 behaviour, which was correct for this shape and is what
    the `missing`-count rationale in `adopt.md` is really about. Without this,
    narrowing the gate until it copies nothing would pass the sibling test.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)

    _run_template_copy(repo, src)

    installed = sorted(p.name for p in (repo / "docs" / "templates").glob("*.tmpl"))
    assert installed == ["AGENTS.md.tmpl", "friction-log.md.tmpl", "handoff.md.tmpl"]


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_refuses_rather_than_guesses_on_an_unreadable_manifest(
    tmp_path: Path,
) -> None:
    """Present-but-corrupt is not the same state as absent, and only absent is
    safe to read as "no declared scope".

    A corrupt manifest may hold declines nobody can now read; copying over them
    is #398's reversal reached by another route. So this refuses and copies
    nothing rather than falling through to the permissive default.

    The earlier form let `json.JSONDecodeError` escape: a Python traceback per
    template file, and then the copy happened anyway. Found by the review
    panel's adversarial lens, which fed it `{not valid json!!!`.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text("{not valid json!!!", encoding="utf-8")

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, "{not valid json!!!")


def _assert_gate_refused(
    repo: Path, result: subprocess.CompletedProcess[str], shape: str
) -> None:
    installed = sorted(
        p.name for p in (repo / "docs" / "templates").glob("*.tmpl")
    ) if (repo / "docs" / "templates").exists() else []
    assert installed == [], (
        f"templates were copied over an unreadable declared set ({shape!r}): {installed}"
    )
    assert "STOP" in result.stdout + result.stderr, (
        f"the refusal must be loud for {shape!r} — a silent skip is "
        "indistinguishable from 'nothing needed copying'"
    )
    assert "Traceback" not in result.stderr, (
        f"the manifest read raises instead of refusing for {shape!r}:\n{result.stderr}"
    )
    # The refusal must stop the WORKFLOW, not just the loop. `break` leaves the
    # `for` and the next line runs the installer anyway — the HIGH a panel lens
    # found, invisible while the extract cut this line out.
    assert not (repo / "INIT_SH_RAN").exists(), (
        f"init.sh ran after the gate refused ({shape!r}) — the STOP message "
        "printed and the workflow carried on past its own hard stop"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
@pytest.mark.parametrize(
    "shape",
    ["null", "42", "true", '"a string"', "[1, 2, 3]"],
    ids=["null", "number", "bool", "string", "array"],
)
def test_step_2_refuses_a_manifest_that_parses_but_is_not_an_object(
    tmp_path: Path, shape: str
) -> None:
    """Valid JSON is not the same as a manifest, and the two failure shapes here
    are not even the same as each other — which is why all five are parametrized.

    `null`, `42` and `true` raise `TypeError` on `"kit_commit" in d`, exit 1, and
    the shell's `case` copies anyway — the same crash-then-copy the syntax-error
    fix was written to remove. `[…]` and `"…"` are quieter and worse: membership
    against them is simply `False`, so there is no error at all and the copy
    proceeds looking entirely normal.

    Both were measured before this guard existed. `#279` is the same class one
    engine over — a manifest load with no non-dict guard beside three siblings
    that have one.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(shape, encoding="utf-8")

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, shape)


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
@pytest.mark.parametrize(
    "declared",
    [5, True, 3.14, "docs/templates/handoff.md.tmpl", {"a": 1}, None],
    ids=["int", "bool", "float", "string", "object", "null"],
)
def test_step_2_refuses_a_baseline_whose_declared_scope_is_not_a_list(
    tmp_path: Path, declared: object
) -> None:
    """A well-formed manifest object is not the same as a readable scope, and the
    top-level `isinstance` check does not reach one field down.

    Three of these raise `TypeError` on the membership test and exit 1, so the
    shell copies — the crash-then-copy class again, two rounds after it was
    supposedly closed. The `string` case is the sharpest and is why it is
    parametrized with a path that WOULD be declined: `in` on a string is a
    SUBSTRING test, so a comma-joined value answers *true* for a path nobody
    declined, and the gate then reports a decline that was never recorded. That
    is the one direction none of the earlier shapes could produce.

    `kit_doctor.py`'s `_declared_scope` already rejects exactly this — a
    `not_installed` that is not a list, and a `files` that is not a dict — with
    its own parametrized regression test. This mirrors it, failing closed where
    that one returns `None`.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(
        json.dumps({"kit_commit": "deadbeef", "files": {}, "not_installed": declared}),
        encoding="utf-8",
    )

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, f"not_installed={declared!r}")


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_refuses_a_baseline_whose_files_half_is_unreadable(
    tmp_path: Path,
) -> None:
    """`_declared_scope`'s companion check, for its stated reason: a scope claim
    needs BOTH halves of the record, and a valid `not_installed` beside a
    malformed `files` is half a record. CodeRabbit found that one on PR #322 in
    the engine; the same reasoning applies to a gate that acts on the answer.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(
        json.dumps(
            {
                "kit_commit": "deadbeef",
                "files": ["not", "a", "dict"],
                "not_installed": ["docs/templates/handoff.md.tmpl"],
            }
        ),
        encoding="utf-8",
    )

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, "files=list")


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_refuses_a_dangling_symlink_at_the_manifest_path(
    tmp_path: Path,
) -> None:
    """`FileNotFoundError` alone does not mean absent.

    A dangling symlink raises it exactly as a missing file does, so the one
    branch the taxonomy treats as safe to copy on was also catching a
    present-but-unreadable manifest. `is_symlink()` separates them because it
    does not follow the link — it stays true precisely where `exists()` has gone
    false, verified directly.

    `#303` is the same shape one file over: a dangling symlink at
    `.codex/hooks.json` survived three rounds of guards there, where `[ -e ]` was
    false and the redirect wrote through the link anyway.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").symlink_to(tmp_path / "no-such-manifest.json")
    assert not (repo / "kit-manifest.json").exists()  # positive control
    assert (repo / "kit-manifest.json").is_symlink()

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, "dangling symlink")


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_refuses_on_an_exception_outside_the_old_enumerated_set(
    tmp_path: Path,
) -> None:
    """The refusal must cover ANY read/parse failure, not an enumerated set.

    Two enumerations have now had the same hole: the first let
    `JSONDecodeError` escape, and its fix caught `(OSError, ValueError)` and left
    `RecursionError` — a `RuntimeError`, reachable from a deeply-nested array —
    falling through to the copy branch with a traceback per template.

    **This test measures its own precondition rather than assuming it**, which is
    `#393`'s lesson: a sibling test elsewhere in this repo depends on
    `json.loads` raising `RecursionError` and that stops being true on newer
    CPython. If this input does not raise outside the old tuple on the running
    interpreter, the test cannot demonstrate anything and says so, instead of
    passing vacuously.
    """
    depth = 200_000
    payload = "[" * depth + "]" * depth

    # Probed in the SAME interpreter the gate will use, not in pytest's.
    # The gate runs in a subprocess that resolves a bare `python3` off PATH;
    # probing in-process only agrees with that because `uv run` puts its managed
    # venv first and `_run_template_copy` passes the environment through. Nothing
    # asserted that, so a different invocation could silently desync the
    # precondition from the thing under test and degrade this to an unconditional
    # skip with nothing failing anywhere — the vacuous pass this test exists to
    # avoid, reintroduced one layer up (review panel, adversarial lens).
    probe = subprocess.run(
        [
            "python3",
            "-c",
            "import json,sys\n"
            "try: json.loads(sys.stdin.read())\n"
            "except (OSError, ValueError): sys.exit(10)\n"
            "except Exception: sys.exit(11)\n"
            "sys.exit(12)",
        ],
        input=payload,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    if probe.returncode == 10:
        pytest.skip(
            "the gate's own python3 raises an (OSError, ValueError) here, so this "
            "input cannot exercise an exception outside the old enumerated set"
        )
    if probe.returncode == 12:
        pytest.skip(
            f"the gate's own python3 parses {depth} nested arrays without raising, "
            "so this input cannot exercise the escape this test is about"
        )
    assert probe.returncode == 11, (
        "the precondition probe itself failed to run, so a skip or pass here "
        f"would mean nothing: rc={probe.returncode} stderr={probe.stderr!r}"
    )

    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(payload, encoding="utf-8")

    result = _run_template_copy(repo, src, check=False)

    _assert_gate_refused(repo, result, "deeply nested array")


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_copies_against_a_manifest_carrying_neither_key(tmp_path: Path) -> None:
    """Pins the ORDER of the gate's two absence checks, which is load-bearing and
    was pinned by nothing.

    `kit_commit` absent is tested (untrusted manifest → copy) and
    `not_installed` absent is tested (partial record → skip). Neither reaches
    the case where BOTH are absent, so swapping the two `if` blocks survived the
    whole suite — found by mutation, not by reading.

    That shape is not hypothetical: it is **the kit's own shipped
    `kit-manifest.json`**, whose top-level keys are `adopter_owned`, `files` and
    `kit_version`. Every fresh `/adopt` and every kit checkout carries it before
    any `--record-install` has run. Under the swapped order it would skip every
    template and print a `#388` PARTIAL-record note about a file that was never a
    baseline — a misattributed cause on the commonest manifest there is.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    # the shipped shape: no kit_commit, no not_installed
    (repo / "kit-manifest.json").write_text(
        json.dumps({"kit_version": 2, "files": {}, "adopter_owned": []}),
        encoding="utf-8",
    )

    result = _run_template_copy(repo, src)

    installed = sorted(p.name for p in (repo / "docs" / "templates").glob("*.tmpl"))
    assert installed == ["AGENTS.md.tmpl", "friction-log.md.tmpl", "handoff.md.tmpl"], (
        "a manifest that is not a --record-install baseline declares no scope, so "
        f"every template copies; got {installed}"
    )
    assert (repo / "INIT_SH_RAN").exists()
    assert "#388" not in result.stderr, (
        "a manifest with no kit_commit was reported as a PARTIAL record — the "
        "two absence checks have swapped order, so the cause is misattributed"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_treats_a_partial_record_as_partial_not_broken(tmp_path: Path) -> None:
    """An absent `not_installed` is a PARTIAL record, and blocking on it aborts a
    routine upgrade.

    `kit_doctor.py`'s `record_install_manifest` omits the key entirely — not
    `[]` — whenever any kit-owned path is `unverified`, writes the baseline
    anyway, and exits 1 to say so. `upgrade.md` Step 5 calls a deliberately-kept
    local patch "the usual way in". So this shape is produced by the kit's own
    instructed command, in a state the kit treats as first class.

    An earlier version refused it AND suppressed `init.sh`, blocking the whole
    config migration for anyone carrying one patch — and its STOP message
    suggested a remedy that did not address the cause, whose obvious workaround
    (delete the manifest) reopens #398.

    Both halves are asserted, because the fix is precisely that they are
    separable: skip the copies, because the declines genuinely cannot be read;
    run `init.sh`, because template declines have nothing to do with the config
    migration.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    # exactly what record_install_manifest writes for a partial record
    (repo / "kit-manifest.json").write_text(
        json.dumps({"kit_commit": "deadbeef", "files": {"init.sh": {"sha256": "x"}}}),
        encoding="utf-8",
    )

    result = _run_template_copy(repo, src)

    installed = sorted(
        p.name for p in (repo / "docs" / "templates").glob("*.tmpl")
    ) if (repo / "docs" / "templates").exists() else []
    assert installed == [], (
        f"templates were copied against a baseline declaring no scope: {installed}"
    )
    assert (repo / "INIT_SH_RAN").exists(), (
        "init.sh was suppressed by a PARTIAL record — that blocks the config "
        "migration for any adopter carrying a deliberate local patch"
    )
    assert "STOP" not in result.stdout + result.stderr, (
        "a partial record is not a broken manifest and must not be reported as one"
    )
    assert "#388" in result.stderr, (
        "the note must name the cause; without it the operator has no route from "
        "the symptom to Step 5's remedy"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_runs_init_sh_when_the_gate_is_satisfied(tmp_path: Path) -> None:
    """The positive control for the refusal tests above.

    Without it, a block that had stopped running `init.sh` under ALL conditions
    would satisfy every `not INIT_SH_RAN` assertion and the gate would look
    perfect while the workflow no longer did its job.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)

    _run_template_copy(repo, src)

    assert (repo / "INIT_SH_RAN").exists(), (
        "init.sh did not run on a repo with no manifest at all — the gate is "
        "refusing something it should wave through"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_writes_into_repo_even_when_the_shell_sits_in_the_kit_clone(
    tmp_path: Path,
) -> None:
    """#399, as an executable pin rather than a paragraph.

    The failure this reproduces: a `cd` into the fetched kit — to inspect it, to
    read one file — outlives the command that made it, and every relative path
    afterwards resolves in the clone. It happened twice on 2026-08-09, in two
    repos, and neither session recognised it as a wrong directory; one read it as
    filesystem corruption and spent ten minutes on a suspected sandbox overlay.

    So the block is run with the shell parked in `$KIT`, which is the state that
    produced both occurrences. `$REPO`-anchored writes land correctly from any
    cwd; the pre-#399 relative form wrote the templates into the kit clone and
    left the repo untouched, with `cp` reporting nothing either way.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    kit_root = src.parent.parent

    _run_template_copy(repo, src, cwd=kit_root)

    installed = sorted(p.name for p in (repo / "docs" / "templates").glob("*.tmpl"))
    assert installed == ["AGENTS.md.tmpl", "friction-log.md.tmpl", "handoff.md.tmpl"], (
        "the copy did not land in $REPO when the shell was parked in $KIT — a "
        f"persisted `cd` still redirects Step 2's writes (#399). present: {installed}"
    )
    # and nothing was written into the kit clone, which is the other half: the
    # first occurrence's damage was writes landing in the throwaway tree.
    assert not (kit_root / "docs" / "templates" / "docs").exists(), (
        "Step 2 wrote a nested docs/templates inside the kit clone"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_step_2_ignores_a_not_installed_key_on_an_untrusted_manifest(
    tmp_path: Path,
) -> None:
    """The `kit_commit` test is what separates a real baseline from the kit's own
    shipped manifest sitting at the same path.

    Step 1 of the workflow draws that distinction for the drift report; the gate
    has to draw it too. A shipped manifest carries no `not_installed`, but a
    hand-rolled or partial one might — and honouring it would withhold templates
    from a repo that never declared a scope. Kills: dropping the `kit_commit`
    condition.
    """
    repo = tmp_path / "adopter"
    repo.mkdir()
    src = _fake_kit_templates(tmp_path)
    (repo / "kit-manifest.json").write_text(
        json.dumps({"files": {}, "not_installed": ["docs/templates/handoff.md.tmpl"]}),
        encoding="utf-8",
    )

    _run_template_copy(repo, src)

    installed = sorted(p.name for p in (repo / "docs" / "templates").glob("*.tmpl"))
    assert "handoff.md.tmpl" in installed, (
        "a manifest with no `kit_commit` is not a --record-install baseline, so "
        "its `not_installed` must not gate the copy"
    )


# --------------------------------------------------------------------------- #
# The installer does not rewrite itself (#360)


@pytest.mark.parametrize(
    ("label", "config", "argv", "proof"),
    [
        ("current schema", None, (), "seeded "),
        # NOT "seeded ": that is what the current-schema case above proves, so it
        # would pass on a run that skipped migration entirely and merely seeded
        # files. This string is emitted only when the schema is actually migrated
        # forward — the shipped config is already v2, so it never appears there.
        ("v1 migration", V1_CONFIG, (), "stamped kit.version=2"),
        # `proof` is what makes this case non-vacuous, and it was added because it
        # was vacuous. See the docstring's "reaching the branch" paragraph.
        ("no-clobber", None, ("--no-clobber",), "left untouched (--no-clobber): "),
    ],
    # Explicit ids: without them pytest builds each id from the parameter VALUES,
    # so the v1 case's whole YAML document lands in the test name and a failure
    # line runs to ~2000 characters of embedded config. Seen in a real mutation
    # run before this was added.
    ids=["current-schema", "v1-migration", "no-clobber"],
)
def test_running_the_installer_does_not_modify_the_installer(
    tmp_path: Path, label: str, config: str | None, argv: tuple[str, ...], proof: str
) -> None:
    """`init.sh` must leave its own bytes untouched — the premise #360's tracking
    model rests on.

    Tracking `init.sh` in `KIT_OWNED` is only correct if an adopter's copy is NOT
    expected to diverge, because that is what puts a behind-the-kit copy in
    `stale` (clears when updated) rather than `locally-edited` (permanently red on
    a file nobody edited — the failure #286 was closed to fix). Established for
    the real adopter by hashing: cs-toolkit's copy is byte-identical to kit commit
    7485512b, so its 852-line delta is version drift with no local rendering.

    **This replaces a regex over init.sh's source, and the replacement is the
    point.** That version looked for `> $0`, `sed -i … init.sh` and similar; an
    adversarial lens defeated it with a self-overwrite it structurally could not
    see — `SELF_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"` followed
    by a plain `cp`. `sh -n` accepted it and the guard passed. Two more reasons
    the textual instrument was wrong: the write verb is open-ended
    (`cp`/`mv`/`install`/`dd`/a downloader), and init.sh contains 14 `$0`
    occurrences that are all AWK's current-record variable, so anchoring on `$0`
    begins with 14 false positives.

    Comparing the file's own bytes across a real run needs no list of verbs and
    catches every mechanism, including ones nobody has thought of.

    Parametrized over three code paths rather than one, because a self-write
    could live on any of them: a fresh run on the current schema, a v1 config
    migration (the branch that rewrites config in place, the most plausible place
    for a self-rewrite to be added), and `--no-clobber`.

    **Reaching the branch is not the same as passing the flag, and round 2 caught
    this test failing that distinction.** `--no-clobber` only *does* anything on a
    target `_seedable` returns MARKED (2) for — an existing file whose line 1
    carries a kit marker. `_fixture(templates=True)` copies template SOURCES and
    never the rendered TARGETS, so every target was ABSENT (0) and the
    no-clobber-specific arm at `init.sh:1076-1080` never executed. An adversarial
    lens proved it by planting a self-write *inside* that arm: all three
    parametrizations passed. So this case exercised the flag and not its branch.

    Fixed two ways, and the second is what stops it regressing: the fixture now
    pre-seeds a marker-carrying target so MARKED is reached, and each case asserts
    a `proof` string in stdout showing the path it claims to cover actually ran.
    A guard that cannot go vacuous silently is worth more than one that happens to
    be non-vacuous today.

    **Each `proof` must also DISCRIMINATE its own path, which is a second mistake
    made here and caught by the review bot.** The v1 case first shipped with
    `"seeded "` — the same string the current-schema case uses — so a run that
    skipped migration entirely and merely seeded files would have satisfied it.
    Its proof is now `stamped kit.version=2`, emitted only when the schema is
    really migrated forward. A positive control shared with another case proves
    the union of the two paths, not the one it is attached to.
    """
    repo = _fixture(
        tmp_path,
        config=shipped_config() if config is None else config,
        templates=True,
        git=True,
    )
    if argv == ("--no-clobber",):
        # An existing target carrying the shipped skeleton's marker on line 1 —
        # the ONLY shape that makes _seedable return MARKED, and so the only way
        # the --no-clobber decline arm is reachable at all.
        marked = repo / "AGENTS.md"
        marked.write_text(
            f"<!-- {template_marker()} — pre-seeded so MARKED is reachable -->\n"
            "\n# placeholder\n",
            encoding="utf-8",
        )
    before = (repo / "init.sh").read_bytes()

    result = _run_init(repo, *argv)

    after = (repo / "init.sh").read_bytes()
    assert after == before, (
        f"init.sh rewrote itself during a `{label}` run "
        f"({len(before)} bytes -> {len(after)}). If that is deliberate, the "
        "KIT_OWNED entry for init.sh needs revisiting: an adopter's copy would "
        "then be expected to diverge, and `stale` would become `locally-edited` "
        "for every adopter. Re-open the #360 design question before shipping it."
    )
    # Positive control. Without it a run that did nothing at all — an early exit,
    # a fixture that made every branch a no-op — proves the bytes unchanged for
    # the wrong reason and reports it as coverage.
    assert proof in result.stdout, (
        f"the `{label}` run never reached the path this case exists to cover: "
        f"{proof!r} absent from stdout, so the unchanged-bytes assertion above "
        f"passed vacuously.\nstdout:\n{result.stdout}"
    )


# --------------------------------------------------------------------------- #
# The upgrade workflow's changelog-lookup block (#430)
# --------------------------------------------------------------------------- #
# Same reasoning as the Step 2 block above, and the same defect class (#330):
# this is executable payload shipped as prose. It is extracted and RUN rather
# than pattern-matched, because every assertion worth making here is about what
# the shell does, not about which words the document contains.
#
# The property under test is the guard's fail-CLOSED direction. Its two inputs
# fail differently and both must land on the degraded path: an empty baseline
# interpolates to `..HEAD`, which git reads as `HEAD..HEAD` and prints nothing
# (silent, and the worse of the two); a non-empty baseline this checkout cannot
# resolve exits 128 from `merge-base --is-ancestor` (loud, but still not the
# degraded path unless something routes it there). A panel lens hardwired this
# guard to its fail-open branch and the whole suite still passed, which is why
# the test exists.


def _changelog_lookup_block() -> str:
    """upgrade.md's Step 1 changelog-lookup block, as text.

    Anchored on the `merge-base --is-ancestor` guard rather than on a path or a
    heading: the guard IS the behaviour under test, so an edit that removes it
    must fail here as a missing block rather than pass against some other
    fenced block in the document.
    """
    doc = (
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows" / "upgrade.md"
    ).read_text(encoding="utf-8")
    blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", doc, re.DOTALL)
    matching = [b for b in blocks if "merge-base --is-ancestor" in b]
    assert len(matching) == 1, (
        f"expected one changelog-lookup block in upgrade.md, found {len(matching)}"
    )
    return matching[0]


def _run_lookup(tmp_path: Path, baseline: str, kit: Path) -> subprocess.CompletedProcess:
    """Run the document's own block with $BASELINE pre-set and $KIT bound.

    The `BASELINE=` assignment in the document shells out to `kit_doctor.py`,
    which needs an installed repo to report on. That resolution is not what this
    test covers, so the line is replaced by the value under test and everything
    after it — the guard and the extraction — runs verbatim from the document.
    """
    block = _changelog_lookup_block()
    body = re.sub(
        r'BASELINE="\$\(.*?\)"\n', "", block, count=1, flags=re.DOTALL
    )
    assert "merge-base --is-ancestor" in body, body
    script = f'set -u\nKIT={shlex.quote(str(kit))}\nBASELINE={shlex.quote(baseline)}\n{body}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, cwd=tmp_path
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
@pytest.mark.parametrize(
    "baseline, label",
    [
        ("", "empty baseline"),
        ("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "unresolvable baseline"),
    ],
)
def test_upgrade_changelog_lookup_degrades_when_the_baseline_is_unusable(
    tmp_path: Path, baseline: str, label: str
) -> None:
    """Neither unusable baseline may reach the range query (#430).

    Both must print the degraded-path notice. Asserting on that string rather
    than on the absence of output is deliberate: silence is what the empty
    baseline produced BEFORE the guard, so an assertion that accepted silence
    would pass against the defect.
    """
    kit = tmp_path / "kit"
    subprocess.run(["git", "init", "-q", str(kit)], check=True)
    subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty",
                    "-m", "seed (#1)"], check=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"})
    (kit / "CHANGELOG.md").write_text("## #1 — leaked\n\nmust not appear\n", encoding="utf-8")

    result = _run_lookup(tmp_path, baseline, kit)

    assert "degraded path" in result.stdout, (
        f"the {label} did not reach the degraded path — the guard let it through.\n"
        f"exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "leaked" not in result.stdout, (
        f"the {label} reached the changelog extraction, which is the fail-OPEN "
        f"direction this guard exists to close.\nstdout:\n{result.stdout}"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_upgrade_changelog_lookup_counts_commits_not_subject_text(
    tmp_path: Path,
) -> None:
    """A range of blank-subject commits is not an empty range (#430).

    `git log --format=%s` over such a range emits only newlines, and `$(...)`
    strips them — so a `-n "$SUBJECTS"` test reads a populated range as empty
    and claims "up to date". That is worse than the silence it replaced: a
    wrong positive rather than an ambiguous absence. The condition has to count
    commits.
    """
    kit = tmp_path / "kit"
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"}
    subprocess.run(["git", "init", "-q", str(kit)], check=True)
    subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty",
                    "-m", "base (#1)"], check=True, env=env)
    baseline = subprocess.run(["git", "-C", str(kit), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    for _ in range(2):
        subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty",
                        "--allow-empty-message", "-m", ""], check=True, env=env)
    (kit / "CHANGELOG.md").write_text("## #1 — dated\n\nirrelevant\n", encoding="utf-8")

    result = _run_lookup(tmp_path, baseline, kit)

    assert "up to date" not in result.stdout, (
        "two commits past the baseline were reported as no commits, because "
        f"their subjects are blank.\nstdout:\n{result.stdout}"
    )
    assert "2 commit(s) in range carry no trailing" in result.stdout, (
        "both blank-subject commits should count as unindexed — counting "
        "lines of `git log --format=%s` collapses them to one or zero.\n"
        f"stdout:\n{result.stdout}"
    )


@pytest.mark.kit_repo_only(
    "docs/agentic-dev-kit/workflows/upgrade.md", "CHANGELOG.md"
)
def test_real_changelog_headings_match_the_extraction_pattern() -> None:
    """The shipped CHANGELOG must satisfy the awk the workflow runs on it (#430).

    Every other test here builds a synthetic CHANGELOG under tmp_path, so the
    real file's heading format was coupled to the extraction by nothing. A
    malformed heading yields empty output, which is indistinguishable from "no
    observable change" — the exact ambiguity this section exists to remove.
    """
    changelog = REPO_ROOT / "CHANGELOG.md"
    headings = [
        ln for ln in changelog.read_text(encoding="utf-8").splitlines()
        if ln.startswith("## ")
    ]
    assert headings, "CHANGELOG.md has no `## ` entry headings to check"

    for heading in headings:
        fields = heading.split()
        assert re.fullmatch(r"#\d+", fields[1]), (
            f"heading {heading!r} puts {fields[1]!r} where the workflow's "
            "`awk -v pr` compares `$2` against `\"#\" pr` — this entry can "
            "never be extracted, and the lookup would render it as 'nothing "
            "changed'"
        )
        pr = fields[1][1:]
        extracted = subprocess.run(
            ["awk", "-v", f"pr={pr}", '/^## /{p = ($2 == "#" pr)} p', str(changelog)],
            capture_output=True, text=True, check=True,
        ).stdout
        assert heading in extracted, f"awk could not extract {heading!r}"
        others = [h for h in headings if h != heading]
        assert not any(h in extracted for h in others), (
            f"extracting {heading!r} leaked another entry's section"
        )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_upgrade_changelog_lookup_says_so_when_the_range_is_empty(
    tmp_path: Path,
) -> None:
    """An up-to-date baseline must say it is, not print nothing (#430).

    Every other outcome in this section emits a sentence — both degraded
    branches and the unindexed-commit warning. This one printed only the
    `baseline=` echo, so "nothing to report" and "the procedure broke" looked
    identical, which is the confusion the whole section exists to remove.
    """
    kit = tmp_path / "kit"
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"}
    subprocess.run(["git", "init", "-q", str(kit)], check=True)
    subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty",
                    "-m", "only commit (#1)"], check=True, env=env)
    (kit / "CHANGELOG.md").write_text("## #1 — dated\n\nmust not appear\n", encoding="utf-8")
    head = subprocess.run(["git", "-C", str(kit), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()

    result = _run_lookup(tmp_path, head, kit)

    assert "up to date" in result.stdout, (
        "an empty range printed no verdict, so silence stands in for both "
        f"'nothing to report' and 'this broke'.\nstdout:\n{result.stdout}"
    )
    assert "must not appear" not in result.stdout, (
        f"an empty range still reached the extraction.\nstdout:\n{result.stdout}"
    )
    assert "degraded path" not in result.stdout, (
        "a resolvable, current baseline was wrongly routed to the degraded "
        f"path — the fail-CLOSED direction over-firing.\nstdout:\n{result.stdout}"
    )


@pytest.mark.kit_repo_only("docs/agentic-dev-kit/workflows/upgrade.md")
def test_upgrade_changelog_lookup_reports_commits_it_could_not_index(
    tmp_path: Path,
) -> None:
    """A commit with no trailing `(#NNN)` is skipped — say so (#430).

    The positive control matters more than the warning: without an entry that
    DOES get emitted, a test asserting only the warning would pass on a block
    that emitted nothing at all.
    """
    kit = tmp_path / "kit"
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"}
    subprocess.run(["git", "init", "-q", str(kit)], check=True)
    for subject in ("base (#1)", "indexed change (#42)", "Merge pull request #7 from x"):
        subprocess.run(["git", "-C", str(kit), "commit", "-q", "--allow-empty",
                        "-m", subject], check=True, env=env)
    (kit / "CHANGELOG.md").write_text(
        "## #42 — dated\n\nBREAKING: the indexed one\n\n## #99 — dated\n\nunrelated\n",
        encoding="utf-8",
    )
    baseline = subprocess.run(
        ["git", "-C", str(kit), "rev-list", "--max-parents=0", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    result = _run_lookup(tmp_path, baseline, kit)

    assert "BREAKING: the indexed one" in result.stdout, (
        "the conforming commit's entry was not emitted, so the warning assertion "
        f"below would pass vacuously.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "unrelated" not in result.stdout, (
        f"extraction leaked past its own section into #99.\nstdout:\n{result.stdout}"
    )
    assert "1 commit(s) in range carry no trailing" in result.stdout, (
        "the `Merge pull request` subject yields no PR number and was skipped "
        f"silently — the failure this warning exists to make visible.\n"
        f"stdout:\n{result.stdout}"
    )
