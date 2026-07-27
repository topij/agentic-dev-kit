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
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

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
    The fix (#67) reads the probe list from kit-manifest.json (role == engine) —
    the generated projection of KIT_OWNED, kit_doctor's probe source since #59,
    and the one form of it sh can read — which this fixture supplies; before it,
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


# --------------------------------------------------------------------------- #
# prompt re-stamping — the #62 write path
# --------------------------------------------------------------------------- #


def _shipped_with_name(name_value: str) -> str:
    needle = "  name: my-project\n"
    assert needle in SHIPPED_CONFIG, "shipped config's project.name moved — update the needle"
    return SHIPPED_CONFIG.replace(needle, f"  name: {name_value}\n")


def test_rerun_on_shipped_config_preserves_every_value_and_is_stable(tmp_path: Path) -> None:
    """A non-interactive re-run over the shipped config must change no value,
    and a further re-run must be byte-identical (the documented upgrade path)."""
    repo = _fixture(tmp_path, config=SHIPPED_CONFIG)

    _run_init(repo)
    once = _config(repo)
    assert yaml.safe_load(once) == yaml.safe_load(SHIPPED_CONFIG)

    _run_init(repo)
    assert _config(repo) == once


def test_rerun_preserves_quoted_name_with_colon(tmp_path: Path) -> None:
    """Prompted values are stamped quoted (#62) — the unquoted re-stamp turned a
    legal quoted name containing a colon into invalid YAML on a plain re-run."""
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

# The Makefile's install-hooks target established this pattern: extract one
# function straight out of init.sh, so the test always drives current logic.
_SET_FIELD_DRIVER = """CONFIG_FILE="config/dev-model.yaml"
eval "$(sed -n '/^set_field() {/,/^}/p' init.sh)"
set_field "tracker:" "" "^  url:" "$1"
"""


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
