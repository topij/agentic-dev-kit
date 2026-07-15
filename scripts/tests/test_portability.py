from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_nested_shell_engines(repo: Path) -> Path:
    engine_dir = repo / "scripts" / "devkit"
    (engine_dir / "lib").mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / "scripts" / "dev_session.sh", engine_dir / "dev_session.sh"
    )
    shutil.copy2(
        REPO_ROOT / "scripts" / "reconcile_sessions.sh",
        engine_dir / "reconcile_sessions.sh",
    )
    shutil.copy2(
        REPO_ROOT / "scripts" / "lib" / "repo_root.sh",
        engine_dir / "lib" / "repo_root.sh",
    )
    (repo / ".git").mkdir()
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text(
        """paths:
  handoff: handoff.md
  friction_log: friction-log.md
runtime:
  default: codex
  launchers:
    claude: claude
    codex: codex
vcs:
  protected_branch: trunk
""",
        encoding="utf-8",
    )
    return engine_dir


def test_nested_shell_engines_find_the_repository_root(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)

    result = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "list"],
        check=True,
        capture_output=True,
        text=True,
    )

    expected_sessions = repo.parent / "dev-model-sessions"
    assert f"no sessions — {expected_sessions} does not exist yet" in result.stdout


def test_nested_launcher_resolves_runtime_mapping(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)
    script = engine_dir / "dev_session.sh"

    result = subprocess.run(
        ["bash", "-c", 'source "$1"; _resolve_launcher "" ""', "bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == "codex\tcodex\n"


def test_nested_lane_contract_uses_configured_paths(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)
    script = engine_dir / "dev_session.sh"

    result = subprocess.run(
        ["bash", "-c", 'source "$1"; _lane_contract', "bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "scripts/devkit/pr_watch.py" in result.stdout
    assert "Never edit handoff.md or friction-log.md" in result.stdout
    assert "never trunk" in result.stdout


def test_archive_defaults_follow_configured_paths(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    config_path = repo / "config" / "dev-model.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """paths:
  handoff: handoff.md
  handoff_history: saved/handoff-history.md
""",
        encoding="utf-8",
    )
    archive = _load_module(
        "archive_plan_sessions", REPO_ROOT / "scripts" / "archive_plan_sessions.py"
    )

    plan, history = archive.configured_paths(root=repo, config_path=config_path)

    assert plan == repo / "handoff.md"
    assert history == repo / "saved" / "handoff-history.md"


def test_python_engine_root_walk_supports_namespacing(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    nested_script = repo / "scripts" / "devkit" / "pr_watch.py"
    nested_script.parent.mkdir(parents=True)
    (repo / ".git").mkdir()
    pr_watch = _load_module("pr_watch", REPO_ROOT / "scripts" / "pr_watch.py")

    assert pr_watch._find_repo_root(nested_script) == repo


def test_codex_skill_adapters_are_valid_and_share_workflows() -> None:
    for name in ("session-start", "wrap-up", "pr-watch", "parallel"):
        skill_dir = REPO_ROOT / ".agents" / "skills" / name
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert skill_text.startswith("---\n")
        _, frontmatter, body = skill_text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert set(metadata) == {"name", "description"}
        assert metadata["name"] == name
        assert "TODO" not in skill_text
        assert f"docs/agentic-dev-kit/workflows/{name}.md" in body

        interface = yaml.safe_load(
            (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
        )["interface"]
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${name}" in interface["default_prompt"]

        claude_adapter = (REPO_ROOT / ".claude" / "commands" / f"{name}.md").read_text(
            encoding="utf-8"
        )
        assert f"docs/agentic-dev-kit/workflows/{name}.md" in claude_adapter


def test_shared_lane_contract_has_no_runtime_specific_peer_api() -> None:
    script = (REPO_ROOT / "scripts" / "dev_session.sh").read_text(encoding="utf-8")

    assert "SendMessage" not in script
    assert "&& claude" not in script
