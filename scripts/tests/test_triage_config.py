from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.model import TriageError, load_settings  # noqa: E402
from triage.storage import ArtifactStore  # noqa: E402


def configured_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "config/dev-model.yaml", root / "config/dev-model.yaml")
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("  engines: scripts/devkit\n", "  engines: scripts\n"), encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/triage_friction_log.py").write_text("# draft\n", encoding="utf-8")
    (root / "scripts/finalize_triage.py").write_text("# finalize\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "init", "-b", "main"], check=True, capture_output=True)
    return root


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
    ],
)
def test_malformed_or_colliding_config_stops_before_artifact_resolution(
    tmp_path: Path, mutate, message: str
) -> None:
    root = configured_repo(tmp_path)
    config_path = root / "config/dev-model.yaml"
    value = config_path.read_text(encoding="utf-8")
    config_path.write_text(mutate(value), encoding="utf-8")
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
