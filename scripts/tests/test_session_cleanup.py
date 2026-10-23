"""Session lifecycle probes use only synthetic repositories inside tmp_path."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import session_cleanup as cleanup  # noqa: E402


@pytest.fixture
def session(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    repo = root / "repo"
    repo.mkdir()
    cleanup.git(repo, "init", "-q")
    cleanup.git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "--allow-empty", "-qm", "fixture")
    config = repo / "cleanup.yaml"
    config.write_text(f"scratch:\n  session_registry: cleanup-sessions\n  roots:\n    - {root}/scratch/{{repo_slug}}\n  grace_window: 24h\n  worktree_repos:\n    - .\n")
    registry = cleanup.Registry(repo, config)
    with registry.lock():
        record = registry.start()
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [])
    yield registry, record, root
    monkeypatch.undo()
    # Tests intentionally leave dependency refusals behind. Their whole fixture
    # sandbox, including all Git metadata, is owned by this fixture alone.
    shutil.rmtree(root)


def allocate(registry, record):
    root = cleanup.sweep.expand_root(registry.settings.roots[0], root=registry.repo)
    Path(root).mkdir(parents=True, exist_ok=True)
    return registry.allocate(record, root, cleanup.git(registry.repo, "rev-parse", "HEAD"))


def seal(registry, record, receipt):
    path = Path(receipt["path"])
    evidence = path / "result.md"
    evidence.write_text("terminal report\n")
    screenshot = path / "capture.bin"
    screenshot.write_bytes(b"authoritative bytes\x00\xff")
    logs = path / "verbose.log"
    logs.write_text("redundant diagnostics\n")
    return registry.seal(record, {"evidence_complete": True, "retain": [
        {"source": str(evidence), "kind": "report", "requires": [str(screenshot)]},
        {"source": str(screenshot), "kind": "asset", "requires": []},
    ], "retire": [{"source": str(logs), "reason": "terminal report replaces diagnostics",
                   "replaced_by": [str(evidence)]}]})


def apply(registry, record):
    return registry.apply(record, registry.preview(record)["approval_token"], True)


def test_removed_task_namespace_discovery_and_idempotent_retirement(session):
    primary, _, root = session
    task = root / "task"
    cleanup.git(primary.repo, "worktree", "add", "--detach", str(task), "HEAD")
    task_registry = cleanup.Registry(task, primary.repo / "cleanup.yaml")
    record = task_registry.start()
    earlier = allocate(task_registry, record)
    later = allocate(task_registry, record)
    seal(task_registry, record, later)
    cleanup.git(primary.repo, "worktree", "remove", str(task))
    resumed = primary.load(record["id"])
    # Ownership authorizes the old expansion only, not an arbitrary receipt.
    assert primary.preview(resumed)["paths"][0]["action"] == "eligible"
    result = apply(primary, resumed)
    assert result["complete"]
    assert not Path(earlier["path"]).exists()
    assert not Path(later["path"]).exists()
    assert apply(primary, primary.load(record["id"]))["complete"]
    for item in record["seal"]["retained"]:
        assert cleanup.hash_file(Path(item["retained"])) == (item["sha256"], item["size"])


def test_explicit_scope_and_evidence_required(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    unrelated = Path(receipt["root"]) / "unrelated"
    unrelated.mkdir()
    with pytest.raises(cleanup.sweep.ConfigError, match="seal"):
        registry.preview(record)
    seal(registry, record, receipt)
    with pytest.raises(cleanup.sweep.ConfigError, match="approval"):
        registry.apply(record, "wrong", True)
    with pytest.raises(cleanup.sweep.ConfigError, match="writers"):
        registry.apply(record, registry.preview(record)["approval_token"], False)
    assert apply(registry, record)["complete"]
    assert unrelated.is_dir()
    assert (root / "repo").is_dir()


def test_missing_required_evidence_and_corruption_refuse(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    report = Path(receipt["path"]) / "report"
    report.write_text("report")
    with pytest.raises(cleanup.sweep.ConfigError, match="dependency"):
        registry.seal(record, {"evidence_complete": True, "retain": [
            {"source": str(report), "kind": "report", "requires": ["missing"]}]})
    seal(registry, record, receipt)
    Path(record["seal"]["retained"][0]["retained"]).write_text("corrupted")
    with pytest.raises(cleanup.sweep.ConfigError, match="changed"):
        apply(registry, record)
    assert report.exists()


@pytest.mark.parametrize("kind", ["symlink", "fifo", "hardlink"])
def test_evidence_special_files_refused_without_blocking(session, kind):
    registry, record, root = session
    receipt = allocate(registry, record)
    path = Path(receipt["path"]) / "special"
    original = root / "original"
    original.write_text("evidence")
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "symlink":
        path.symlink_to(original)
    else:
        os.link(original, path)
    with pytest.raises(cleanup.sweep.ConfigError):
        registry.seal(record, {"evidence_complete": True, "retain": [
            {"source": str(path), "kind": "report", "requires": []}]})


@pytest.mark.parametrize("change", ["root", "round", "marker", "config"])
def test_identity_policy_or_marker_change_refused(session, change):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    if change == "config":
        registry.policy["registry"] = "other"
        with pytest.raises(cleanup.sweep.ConfigError, match="policy"):
            registry.load(record["id"])
        return
    path = Path(receipt["root"] if change == "root" else receipt["path"])
    if change == "marker":
        (path / cleanup.sweep.ROUND_MARKER).unlink()
    else:
        path.rename(path.with_name(path.name + "-saved"))
        path.mkdir()
    with pytest.raises((cleanup.sweep.ConfigError, OSError, cleanup.sweep.Refused)):
        apply(registry, record)
    assert path.exists()


def test_live_worktree_and_alternate_protect_round_and_do_not_journal(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    path = Path(receipt["path"])
    child = path / "registered"
    cleanup.git(registry.repo, "worktree", "add", "--detach", str(child), "HEAD")
    seal(registry, record, receipt)
    assert not apply(registry, record)["complete"]
    assert record["rounds"][0]["status"] == "allocated"
    cleanup.git(registry.repo, "worktree", "remove", str(child))
    store = path / "objects.git"
    cleanup.git(root, "init", "--bare", str(store))
    alternates = registry.common / "objects/info/alternates"
    alternates.write_text(str(store / "objects") + "\n")
    assert not apply(registry, record)["complete"]
    assert record["rounds"][0]["status"] == "allocated"
    alternates.unlink()
    assert apply(registry, record)["complete"]


def test_worktree_retirement_uses_git_and_codex_requires_native_archive(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    ordinary, managed = root / "ordinary", root / "managed"
    for path, runtime in [(ordinary, "git"), (managed, "codex")]:
        cleanup.git(registry.repo, "worktree", "add", "--detach", str(path), "HEAD")
        registry.track_worktree(record, path, runtime)
    seal(registry, record, receipt)
    result = apply(registry, record)
    assert not result["complete"]
    assert not ordinary.exists()
    assert managed.exists()
    assert result["paths"][1]["action"] == "archive-with-runtime"
    cleanup.git(registry.repo, "worktree", "remove", str(managed))
    assert apply(registry, record)["complete"]


def test_dirty_worktree_kept_and_primary_refused(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    with pytest.raises(cleanup.sweep.ConfigError, match="primary"):
        registry.track_worktree(record, registry.repo, "git")
    task = root / "task"
    cleanup.git(registry.repo, "worktree", "add", "--detach", str(task), "HEAD")
    registry.track_worktree(record, task, "git")
    (task / "user-work").write_text("keep")
    seal(registry, record, receipt)
    assert not apply(registry, record)["complete"]
    assert (task / "user-work").read_text() == "keep"


def test_process_blocker_preserves_approved_inventory(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    registry.track_process(record, os.getpid())
    seal(registry, record, receipt)
    monkeypatch.undo()
    result = apply(registry, record)
    assert not result["complete"]
    assert any(str(os.getpid()) in reason for reason in result["active_users"])
    assert Path(receipt["path"]).exists()


def test_killed_removal_resumes_after_marker_was_unlinked(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    # Kill the real CLI process after the durable journal, mid removal. The
    # next process must reconstruct authority exclusively from persisted state.
    code = '''
import os, signal, sys
sys.path.insert(0, sys.argv[1])
import session_cleanup as c
c.active_users = lambda paths, pids: []
def interrupted(path, root, identity):
    os.unlink(os.path.join(path, c.sweep.ROUND_MARKER))
    os.kill(os.getpid(), signal.SIGKILL)
c.sweep.remove_entry = interrupted
raise SystemExit(c.main(sys.argv[2:]))
'''
    token = registry.preview(record)["approval_token"]
    result = subprocess.run([sys.executable, "-c", code, str(Path(cleanup.__file__).parent),
        "--config", str(registry.repo / "cleanup.yaml"), "apply", record["id"],
        "--approve", token, "--processes-finished"], cwd=registry.repo,
        capture_output=True, timeout=30)
    assert result.returncode == -signal.SIGKILL, result.stderr.decode()
    resumed = registry.load(record["id"])
    assert resumed["rounds"][0]["status"] == "removing"
    assert not (Path(receipt["path"]) / cleanup.sweep.ROUND_MARKER).exists()
    assert registry.apply(resumed, token, True)["complete"]


def test_unknown_root_never_becomes_inventory_authority(session):
    registry, record, root = session
    foreign = root / "foreign"
    foreign.mkdir()
    with pytest.raises(cleanup.sweep.ConfigError):
        registry.allocate(record, str(foreign), cleanup.git(registry.repo, "rev-parse", "HEAD"))
    assert not registry.load(record["id"])["rounds"]


def test_cli_discovers_shared_registry_from_primary(session):
    registry, record, _ = session
    result = subprocess.run([sys.executable, cleanup.__file__, "--config",
        str(registry.repo / "cleanup.yaml"), "list"], cwd=registry.repo,
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["id"] == record["id"]


@pytest.mark.parametrize("name", ["space and 'quote'", "unicode-é"])
def test_real_open_file_observation_preserves_path_names(session, monkeypatch, name):
    _, _, root = session
    path = root / name
    path.mkdir()
    monkeypatch.undo()
    with (path / "file").open("w") as stream:
        stream.write("open handle")
        found = cleanup.active_users([str(path)], [])
    # Platforms unable to inspect open files fail closed rather than claiming
    # no users. A working probe must actually identify this process's handle.
    assert any("unavailable" in item or f"process {os.getpid()} uses " in item for item in found)


def test_incomplete_open_file_probe_blocks(session, monkeypatch):
    _, _, root = session
    monkeypatch.undo()
    monkeypatch.setattr(cleanup.subprocess, "run", lambda *a, **k:
        subprocess.CompletedProcess(a, 0, stderr=b"partial observation"))
    assert "incomplete" in cleanup.active_users([str(root)], [])[0]
