from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402
from _triage_fixture import triage_config_text  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.model import TriageError, load_settings  # noqa: E402
from triage.storage import ArtifactStore  # noqa: E402


def configured_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "config/dev-model.yaml").write_text(triage_config_text(), encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/triage_friction_log.py").write_text("# draft\n", encoding="utf-8")
    (root / "scripts/finalize_triage.py").write_text("# finalize\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "init", "-b", "main"], check=True, capture_output=True)
    return root


def test_controlled_fixture_config_needs_no_optional_init_snapshot(tmp_path):
    # A selective installation can omit init's recorded fixture while keeping
    # triage tests. Exercise the installed helper in that layout.
    shutil.copy2(Path(__file__).parent / "_triage_fixture.py", tmp_path / "_triage_fixture.py")
    result = subprocess.run(
        [sys.executable, "-I", "-c",
         "import sys; sys.path.insert(0, '.'); from _triage_fixture import triage_config_text; print(triage_config_text(), end='')"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert result.stdout == triage_config_text()
    assert not (tmp_path / "fixtures").exists()


def test_partial_engine_set_is_rejected(tmp_path: Path) -> None:
    root = configured_repo(tmp_path)
    (root / "scripts/finalize_triage.py").unlink()
    with pytest.raises(TriageError, match="partial"):
        load_settings(root)


def test_live_and_test_artifact_paths_are_distinct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = configured_repo(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    settings = load_settings(root)
    live = ArtifactStore(settings, "live")
    test = ArtifactStore(settings, "test")
    assert live.state_path != test.state_path
    assert live.gate_path != test.gate_path


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda text: text.replace("  engines: scripts\n", "  engines: ../outside\n"), "contained relative"),
        (lambda text: text.replace('  gate_path: "state/triage/triage-pipeline-gate_{mode}.lock"', '  gate_path: "state/triage/triage-pipeline-state_{mode}.json"'), "paths collide"),
        (lambda text: text.replace("  report_root: reports\n", "  report_root: ../reports\n"), "contained relative"),
        (lambda text: text[: text.index("tracker:\n")] + "tracker: []\n" + text[text.index("notify:\n") :], "must be mappings"),
        (lambda text: text.replace("  protected_branch: main", "  protected_branch: 7"), "non-empty string"),
        (
            lambda text: text.replace('triage_branch_pattern: "chore/triage-{date}-{session}"', 'triage_branch_pattern: "chore/triage-{session}"'),
            "exactly once",
        ),
        (
            lambda text: text.replace('triage_branch_pattern: "chore/triage-{date}-{session}"', 'triage_branch_pattern: "chore/triage-{date}-{date}"'),
            "exactly once",
        ),
        (
            lambda text: text.replace('triage_branch_pattern: "chore/triage-{date}-{session}"', 'triage_branch_pattern: "chore/triage-{date}-{session}-{session}"'),
            "at most once",
        ),
        (
            lambda text: text.replace('triage_branch_pattern: "chore/triage-{date}-{session}"', 'triage_branch_pattern: "chore/triage-{date}{session}"'),
            "must separate",
        ),
        (
            lambda text: text.replace('triage_branch_pattern: "chore/triage-{date}-{session}"', 'triage_branch_pattern: "chore/triage-{session}{date}"'),
            "must separate",
        ),
    ],
)
def test_malformed_or_colliding_config_stops_before_artifact_resolution(
    tmp_path: Path, mutate, message: str
) -> None:
    root = configured_repo(tmp_path)
    config_path = root / "config/dev-model.yaml"
    value = config_path.read_text(encoding="utf-8")
    changed = mutate(value)
    assert changed != value, "configuration fault injection did not land"
    config_path.write_text(changed, encoding="utf-8")
    with pytest.raises(TriageError, match=message):
        load_settings(root)


def test_symlinked_engine_root_is_rejected(tmp_path: Path) -> None:
    root = configured_repo(tmp_path)
    shutil.rmtree(root / "scripts")
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "scripts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(TriageError, match="contained directory"):
        load_settings(root)


@pytest.mark.parametrize("module_name, builder", [
    ("test_triage_config", "configured_repo"),
    ("test_triage_engine", "repository"),
    ("test_triage_inputs", "repo"),
    ("test_triage_state", "_triage_repository"),
    ("test_finalize_triage", "repository"),
])
def test_ordinary_fixtures_ignore_adopter_policy(tmp_path, monkeypatch, module_name, builder):
    # Some adopters decline the finalize test module while installing the engines.
    if not (Path(__file__).parent / f"{module_name}.py").is_file():
        pytest.skip("fixture test module not installed")
    module = importlib.import_module(module_name)
    host = tmp_path / "adopter"
    (host / "config").mkdir(parents=True)
    (host / "config/dev-model.yaml").write_text(
        'paths:\n  engines: scripts/devkit\n  friction_log: docs/friction-log.md\n'
        '  friction_log_archive: docs/friction-log-archive.md\n'
        'vcs:\n  protected_branch: trunk\n  triage_branch_pattern: "chore/triage-{date}"\n'
        'tracker:\n  backend: linear\n  project_name: "Foreign adopter"\n'
        '  linear:\n    label_name: "cs-toolkit:triage"\n'
        'review:\n  bots: [foreign-bot]\n', encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", host)
    repo = getattr(module, builder)(tmp_path)
    settings = load_settings(repo)
    assert settings.paths.friction_log == repo / "docs/kit-friction-log.md"
    assert settings.paths.archive == repo / "docs/kit-friction-log-archive.md"
    assert settings.paths.engine_dir == repo / "scripts"
    assert settings.protected_branch == "main"
    assert settings.triage_branch_pattern == "chore/triage-{date}-{session}"
    assert settings.tracker["backend"] == "github-issues"
    assert settings.tracker["project_name"] == "topij/agentic-dev-kit"
    assert settings.config["review"]["bots"] == ["coderabbit"]


@pytest.mark.parametrize("layout", ["docs", "engines", "branch", "linear", "combined"])
def test_supported_adopter_layout_creates_frozen_state(tmp_path, monkeypatch, layout):
    from test_triage_engine import git, repository
    from triage.canonical import loads_exact
    from triage.engine import _branch_date, run
    from triage.model import tracker_destination
    from triage.providers import FakeTracker

    repo = repository(tmp_path)
    config = repo / "config/dev-model.yaml"
    text = config.read_text(encoding="utf-8")
    if layout in {"docs", "combined"}:
        for old, new in (("kit-friction-log.md", "friction-log.md"),
                         ("kit-friction-log-archive.md", "friction-log-archive.md")):
            assert old in text
            text = text.replace(old, new)
            (repo / "docs" / old).rename(repo / "docs" / new)
    if layout in {"engines", "combined"}:
        old = "  engines: scripts\n"
        assert old in text
        text = text.replace(old, "  engines: scripts/devkit\n")
        (repo / "scripts/devkit").mkdir()
        for name in ("triage_friction_log.py", "finalize_triage.py"):
            (repo / "scripts" / name).rename(repo / "scripts/devkit" / name)
    if layout in {"branch", "combined"}:
        old = 'triage_branch_pattern: "chore/triage-{date}-{session}"'
        assert old in text
        text = text.replace(old, 'triage_branch_pattern: "chore/triage-{date}"')
    if layout in {"linear", "combined"}:
        for old, new in (
            ("backend: github-issues", "backend: linear"),
            ('project_name: "topij/agentic-dev-kit"', 'project_name: "Synthetic adopter"'),
            ('url: "https://github.com/topij/agentic-dev-kit/issues"', 'url: "https://linear.app/synthetic/project/test"'),
            ('team_id: ""', 'team_id: "synthetic-team"'),
            ('project_id: ""', 'project_id: "synthetic-project"'),
            ('label_name: ""', 'label_name: "cs-toolkit:triage"'),
        ):
            assert old in text
            text = text.replace(old, new, 1)
    assert text != config.read_text(encoding="utf-8")
    config.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "synthetic adopter layout")
    settings = load_settings(repo)
    from triage.inbox import parse
    candidate = parse(settings.paths.friction_log.read_bytes())[0]
    supplied = {
        "operator_identity": "operator",
        "proposals": [{"candidate_id": candidate.candidate_id, "source_block_digest": candidate.digest,
                       "title": "Active defect", "body_without_marker": "Observed details.",
                       "project": settings.tracker["project_name"], "labels": ["bug"]}],
    }
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    tracker = FakeTracker()
    before = settings.paths.friction_log.read_bytes(), settings.paths.archive.read_bytes()
    result = run("new", context="interactive", request=supplied, start=repo, tracker=tracker)
    assert result["outcome"] == "operator-held"
    state = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert state["proposal_payloads"][0]["payload"]["project"] == settings.tracker["project_name"]
    assert Path(result["frozen_snapshot"]).is_relative_to(state_root)
    assert Path(result["frozen_snapshot"]).is_file()
    assert settings.paths.engine_dir == repo / ("scripts/devkit" if layout in {"engines", "combined"} else "scripts")
    assert settings.engine_mode == "engine-backed"
    assert tracker.calls == []
    assert (settings.paths.friction_log.read_bytes(), settings.paths.archive.read_bytes()) == before
    if layout in {"branch", "combined"}:
        assert _branch_date(settings, "chore/triage-2026-01-02", state["run_identity"]["session"]) == "2026-01-02"
    if layout in {"linear", "combined"}:
        assert tracker_destination(settings.tracker) == {
            "backend": "linear", "host": "linear.app", "repository": "Synthetic adopter",
            "project": "Synthetic adopter", "team_id": "synthetic-team",
            "project_id": "synthetic-project", "label_name": "cs-toolkit:triage",
        }
