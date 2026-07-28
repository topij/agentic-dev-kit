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

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

SHIPPED_CONFIG = (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")

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
        target = repo / "scripts" / "hooks" / "pre-push"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "scripts" / "hooks" / "pre-push", target)
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
    needle = "  name: my-project\n"
    assert needle in SHIPPED_CONFIG, "shipped config's project.name moved — update the needle"
    return SHIPPED_CONFIG.replace(needle, f"  name: {name_value}\n")


def test_rerun_on_shipped_config_preserves_every_value_and_is_stable(tmp_path: Path) -> None:
    """A non-interactive re-run over the shipped config must change no value,
    and a further re-run must be byte-identical (the documented upgrade path).
    The bots byte-assertion pins the quoted-item list serialization — value
    equality alone let a revert to unquoted items survive (panel, #87)."""
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG)

    _run_init(repo)
    once = _config(repo)
    assert yaml.safe_load(once) == yaml.safe_load(SHIPPED_CONFIG)
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
    config = SHIPPED_CONFIG.replace('  url: ""', r'  url: "x\py"')
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
    config = SHIPPED_CONFIG.replace("  bots: [coderabbit]", "  bots: ['coderabbit']")
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
    config = SHIPPED_CONFIG.replace('  bots: [coderabbit]', '  bots: ["a\\"b"]')
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


def test_seeds_narrative_docs_with_tokens_rendered(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, templates=True)

    _run_init(repo)

    # Token rendering is asserted for ALL four docs: {{HANDOFF}} appears only in
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
    assert "my-project" in seeded["docs/kit-handoff.md"]  # {{PROJECT_NAME}}
    assert "scripts/check_doc_budget.py" in seeded["docs/kit-handoff.md"]  # {{ENGINE_DIR}}
    assert "kit-handoff-history.md" in seeded["docs/kit-handoff.md"]  # {{HANDOFF_HISTORY}}
    assert "kit-handoff.md" in seeded["docs/kit-handoff-history.md"]  # {{HANDOFF}}
    assert "kit-friction-log-archive.md" in seeded["docs/kit-friction-log.md"]  # {{FRICTION_ARCHIVE}}
    assert "tracker.url" in seeded["docs/kit-friction-log.md"]  # {{TRACKER_URL}} fallback
    # AGENTS.md renders at the repo ROOT, so its handoff link is the repo-relative
    # configured path, not the sibling-relative form the narrative docs use.
    assert "docs/kit-handoff.md" in seeded["AGENTS.md"]  # {{HANDOFF_PATH}}


def test_render_preserves_backslashes_in_values(tmp_path: Path) -> None:
    """_render passes values to awk via ENVIRON: with `-v`, a backslash-n in a
    project name became a real newline in every seeded doc — this was the one
    #62 surface the suite left unpinned (panel, #87)."""
    repo = _fixture(tmp_path, config=_shipped_with_name(r"Acme\nCo"), templates=True)

    _run_init(repo)

    handoff = (repo / "docs" / "kit-handoff.md").read_text(encoding="utf-8")
    assert r"Acme\nCo" in handoff


def test_seeding_respects_in_use_docs_and_reclaims_marked_ones(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, templates=True)
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


def test_agents_md_renders_the_configured_protected_branch(tmp_path: Path) -> None:
    """{{PROTECTED_BRANCH}} pinned against a DISTINCTIVE value: the shipped config
    says `main`, which occurs in enough unrelated prose that asserting it would
    pass even with the substitution deleted (panel, adversarial lens M2)."""
    config = SHIPPED_CONFIG.replace("protected_branch: main", "protected_branch: trunk-9f2a")
    repo = _fixture(tmp_path, config=config, templates=True)

    _run_init(repo)

    assert "trunk-9f2a" in (repo / "AGENTS.md").read_text(encoding="utf-8")


def test_seeding_leaves_a_doc_that_merely_quotes_the_marker_untouched(tmp_path: Path) -> None:
    """The marker counts only on line 1, where every shipped skeleton carries it.
    Matching it anywhere let a hand-written AGENTS.md that documented the marker
    convention in prose be silently overwritten — content loss, reported as
    "seeded" (panel, adversarial lens)."""
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, templates=True)
    mine = repo / "AGENTS.md"
    original = (
        "# AGENTS.md — hand written\n\n"
        "The kit's skeletons are marked `devkit-template: unrendered` on line 1;\n"
        "this file is not one of them.\n"
    )
    mine.write_text(original, encoding="utf-8")

    result = _run_init(repo)

    assert mine.read_text(encoding="utf-8") == original
    assert "AGENTS.md already in use — left untouched" in result.stdout


def test_kit_ships_no_root_agents_md(tmp_path: Path) -> None:
    """AGENTS.md is seeded by ABSENCE, not by a marker, so the guard holds only
    while the kit itself ships no root AGENTS.md — and ./init.sh run in a kit
    checkout creates one. Committing that would hand every `cp -r` adopter the
    kit's own rendered file with the guard permanently false and no diagnostic:
    the #37/#41 failure the marker exists to prevent, re-entering through the one
    target that has no marker (panel, adversarial lens)."""
    assert not (REPO_ROOT / "AGENTS.md").exists(), (
        "the kit tree must not ship a root AGENTS.md — if ./init.sh was run here, "
        "delete the generated AGENTS.md rather than committing it"
    )


# --------------------------------------------------------------------------- #
# .gitignore appends
# --------------------------------------------------------------------------- #


def test_gitignore_entries_added_exactly_once_across_reruns(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG)

    _run_init(repo)
    _run_init(repo)

    lines = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in ("state/", ".devkit_state_root", ".claude/worktrees/", "reports/"):
        assert lines.count(entry) == 1, f"{entry!r} appears {lines.count(entry)} times"


def test_gitignore_gains_mcp_json_only_for_literal_credentials(tmp_path: Path) -> None:
    """The .mcp.json credential sniff, for the key shapes its regex matches
    (upper-case underscore forms like CF_TOKEN): a literal value gets the file
    ignored, a ${ENV} reference leaves it tracked. The sniff itself misses the
    kit's own documented hyphenated shape (CF-Access-Client-Id) — #86 tracks
    that; this green pins the guard that exists, not sufficiency."""
    literal = _fixture(tmp_path / "literal", config=SHIPPED_CONFIG)
    (literal / ".mcp.json").write_text('{"CF_TOKEN": "abc123"}', encoding="utf-8")
    _run_init(literal)
    assert ".mcp.json" in (literal / ".gitignore").read_text(encoding="utf-8").splitlines()

    envref = _fixture(tmp_path / "envref", config=SHIPPED_CONFIG)
    (envref / ".mcp.json").write_text('{"CF_TOKEN": "${CF_TOKEN}"}', encoding="utf-8")
    _run_init(envref)
    assert ".mcp.json" not in (envref / ".gitignore").read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------- #
# install_hooks
# --------------------------------------------------------------------------- #


def test_installs_pre_push_shim_into_git_hooks(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, git=True, hooks=True)

    _run_init(repo)

    shim = repo / ".git" / "hooks" / "pre-push"
    assert shim.is_file()
    assert os.access(shim, os.X_OK)
    body = shim.read_text(encoding="utf-8")
    assert "devkit-hook-shim" in body
    assert "scripts/hooks/pre-push" in body


def test_hook_shim_honors_repo_local_hookspath(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, git=True, hooks=True)
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
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG, git=True, hooks=True)
    hookdir = repo / ".git" / "hooks"
    hookdir.mkdir(parents=True, exist_ok=True)
    own = "#!/bin/sh\n# the adopter's own hook\n"
    (hookdir / "pre-push").write_text(own, encoding="utf-8")

    proc = _run_init(repo)

    assert (hookdir / "pre-push").read_text(encoding="utf-8") == own
    assert "left untouched" in proc.stderr
