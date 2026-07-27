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

Defect reproductions are ``xfail(strict=True)`` pinned to their issue: the fix
PR flips each by deleting the marker, and a later regression fails loudly
instead of quietly returning to xfail.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
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


def _env() -> dict[str, str]:
    # Isolate from the developer's own git config: a global core.hooksPath would
    # otherwise redirect a fixture's hook install into their real hooks directory.
    return dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


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
            ["git", "init", "-q"], cwd=repo, check=True, env=_env(), capture_output=True
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
        env=_env(),
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
    """Candidate order: the kit's own layout wins when engines really are there."""
    repo = _fixture(tmp_path, config=V1_CONFIG, manifest=True)
    (repo / "scripts").mkdir()
    (repo / "scripts" / "pr_watch.py").write_text("# engine\n", encoding="utf-8")

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["paths"]["engines"] == "scripts"


@pytest.mark.xfail(
    strict=True,
    reason="issue #67: detect_engines_dir probes a hardcoded triple, so a sized-down "
    "install (kit_doctor.py + lib/kitconfig.py only) falls through and stamps "
    "`engines: scripts` for a tree whose engines live in scripts/devkit",
)
def test_engines_detection_sized_down_install(tmp_path: Path) -> None:
    """The probe list must come from kit-manifest.json (role == engine), the same
    single source kit_doctor derives its probe from since #59 — not a fourth
    hand-maintained restatement."""
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


@pytest.mark.xfail(
    strict=True,
    reason="issue #62: prompted values are re-stamped unquoted, so a legal quoted "
    "name containing a colon becomes invalid YAML on a plain re-run",
)
def test_rerun_preserves_quoted_name_with_colon(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=_shipped_with_name('"Acme: Platform"'))

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["project"]["name"] == "Acme: Platform"


@pytest.mark.xfail(
    strict=True,
    reason="issue #62: get_field's comment strip is not quote-aware, so a quoted "
    "name containing # is silently truncated and the truncation re-stamped",
)
def test_rerun_preserves_quoted_name_with_hash(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, config=_shipped_with_name('"Acme #1"'))

    _run_init(repo)

    assert yaml.safe_load(_config(repo))["project"]["name"] == "Acme #1"


# --------------------------------------------------------------------------- #
# set_field — awk value handling (#62 part 2)
# --------------------------------------------------------------------------- #

# The Makefile's install-hooks target established this pattern: extract one
# function straight out of init.sh, so the test always drives current logic.
_SET_FIELD_DRIVER = """CONFIG_FILE="config/dev-model.yaml"
eval "$(sed -n '/^set_field() {/,/^}/p' init.sh)"
set_field "tracker:" "" "^  url:" "$1"
"""


@pytest.mark.xfail(
    strict=True,
    reason="issue #62: awk -v runs escape processing on the assigned value, so a "
    "backslash sequence in a stamped value is transformed before substitution",
)
def test_set_field_writes_backslashes_literally(tmp_path: Path) -> None:
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

    handoff = (repo / "docs" / "kit-handoff.md").read_text(encoding="utf-8")
    assert "{{" not in handoff
    assert "my-project" in handoff
    for rel in (
        "docs/kit-handoff-history.md",
        "docs/kit-friction-log.md",
        "docs/kit-friction-log-archive.md",
    ):
        assert (repo / rel).is_file(), f"{rel} was not seeded"


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
        env=_env(),
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
