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

from triage.canonical import loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "config/dev-model.yaml", root / "config/dev-model.yaml")
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("  engines: scripts/devkit\n", "  engines: scripts\n"), encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/kit-friction-log.md").write_text("# Log\n", encoding="utf-8")
    (root / "docs/kit-friction-log-archive.md").write_text("# Archive\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/triage_friction_log.py").write_text("# draft\n", encoding="utf-8")
    (root / "scripts/finalize_triage.py").write_text("# finalize\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", "https://github.com/example/project.git"], check=True)
    subprocess.run(["git", "-C", str(root), "update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
    return root


def test_unattended_recover_does_not_observe_or_change_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo(tmp_path)
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    gate = state_root / "triage/triage-pipeline-gate_live.lock"
    state = state_root / "triage/triage-pipeline-state_live.json"
    gate.parent.mkdir(parents=True)
    gate.write_bytes(b"opaque gate")
    state.write_bytes(b"opaque state")
    before = (gate.stat(), gate.read_bytes(), state.stat(), state.read_bytes())
    result = run("recover", context="unattended", start=root)
    after = (gate.stat(), gate.read_bytes(), state.stat(), state.read_bytes())
    assert result["outcome"] == "operator-held"
    assert result["capabilities"]["repository-config-read"]["status"] == "not-triggered"
    assert (before[0].st_ino, before[1], before[2].st_ino, before[3]) == (after[0].st_ino, after[1], after[2].st_ino, after[3])


def test_test_entry_isolated_from_live_recovery_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo(tmp_path)
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    live = state_root / "triage/triage-pipeline-state_live.json"
    live.parent.mkdir(parents=True)
    live.write_bytes(b"live opaque evidence")
    result = run("test", context="interactive", request={"proposals": []}, start=root)
    assert result["outcome"] == "successful-completion"
    assert live.read_bytes() == b"live opaque evidence"
    assert (state_root / "triage/triage-pipeline-state_test.json").exists()


def test_cli_rejects_symlink_request_before_engine(tmp_path: Path) -> None:
    target = tmp_path / "request.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "request-link.json"
    link.symlink_to(target)
    result = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "triage_friction_log.py"), "new", "--request", str(link)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "unsafe artifact at held parent" in result.stdout


@pytest.mark.parametrize("arguments", [["new", "resume"], ["--unknown-flag"]])
def test_cli_argument_errors_emit_complete_canonical_hard_stop(arguments: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "triage_friction_log.py"), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert result.stderr == ""
    envelope = loads_exact(result.stdout.strip().encode())
    assert envelope["outcome"] == "hard-stop"
    assert envelope["execution_mode"] == "unknown"
    assert set(envelope["capabilities"]) == {
        "repository-config-read", "shared-state-resolver", "single-writer-state-gate",
        "frozen-inbox-state", "draft-finalize-engine-set", "notification-thread",
        "tracker-write-readback", "forge-pr-write-readback", "pr-watch",
        "runtime-compute-selection",
    }


@pytest.mark.parametrize(
    "request_value",
    [
        [],
        {"proposals": ["not-an-object"]},
        {"proposals": [{"labels": "not-an-array"}]},
        {"approval": []},
        {"recovery_approval": "approve"},
        {"finalize": "yes"},
        {"worktree": []},
    ],
)
def test_malformed_request_containers_hard_stop_before_gate_or_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request_value
) -> None:
    root = repo(tmp_path)
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    result = run("new", context="interactive", request=request_value, start=root)
    assert result["outcome"] == "hard-stop"
    assert result["capabilities"]["repository-config-read"]["status"] == "not-triggered"
    assert not state_root.exists()


def test_runtime_policy_override_is_rejected_before_capability_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    result = run(
        "new", context="interactive",
        request={"analysis_tier": "cheaper-runtime", "pr_draft": True},
        start=root,
    )
    assert result["outcome"] == "hard-stop"
    assert result["capabilities"]["repository-config-read"]["status"] == "not-triggered"
    assert "unsupported policy fields" in result["detail"]
    assert not state_root.exists()


def test_pre_reservation_parse_failure_releases_gate_without_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(b"# Log\n\n## 2026-01-02 \xff\n\n- **Broken.**\n")
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    result = run("new", context="interactive", request={}, start=root)
    assert result["outcome"] == "hard-stop"
    assert "not UTF-8" in result["detail"]
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert not (state_root / "triage/triage-pipeline-state_live.json").exists()


@pytest.mark.parametrize("missing", ["provider", "target"])
def test_unattended_nonempty_new_without_notification_capability_creates_no_session_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    root = repo(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n- **Needs triage.** details.\n"
    )
    if missing == "provider":
        notification = None
    else:
        class Notification:
            @staticmethod
            def send_and_read_back(*_args):
                raise AssertionError("notification dispatch must not run")

        notification = Notification()
    state_root = tmp_path / "state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    result = run("new", context="unattended", request={}, start=root, notification=notification)
    assert result["outcome"] == "hard-stop"
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert not (state_root / "triage/triage-pipeline-state_live.json").exists()
    assert not list((state_root / "triage").glob("frozen-inbox_live_*.json"))
    assert not list((root / "reports").glob("triage_live_*.md"))


def test_no_argument_starts_absent_session_while_resume_absence_hard_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resume_root = repo(tmp_path / "resume")
    resume_state = tmp_path / "resume-state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(resume_state))
    absent = run("resume", context="interactive", request={}, start=resume_root)
    assert absent["outcome"] == "hard-stop"
    assert not (resume_state / "triage/triage-pipeline-state_live.json").exists()

    implicit_root = repo(tmp_path / "implicit")
    implicit_state = tmp_path / "implicit-state"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(implicit_state))
    started = run(None, context="interactive", request={}, start=implicit_root)
    assert started["outcome"] == "successful-completion"
    assert (implicit_state / "triage/triage-pipeline-state_live.json").exists()
