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
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"evidence_complete": True, "retain": [
        {"source": str(path), "kind": "report", "requires": []}]}))
    result = subprocess.run([sys.executable, cleanup.__file__, "--config",
        str(registry.repo / "cleanup.yaml"), "seal", record["id"], str(manifest)],
        cwd=registry.repo, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert ("symlink aliases" if kind == "symlink" else "unaliased regular file") in result.stderr
    assert registry.load(record["id"])["seal"] is None


@pytest.mark.parametrize("change", ["root", "round", "round-without-marker", "marker", "config"])
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
        if change == "round":
            # Preserve the receipt bytes so this case isolates directory
            # replacement rather than the separate missing-marker refusal.
            shutil.copyfile(path.with_name(path.name + "-saved") / cleanup.sweep.ROUND_MARKER,
                            path / cleanup.sweep.ROUND_MARKER)
    sentinel = path / "must-remain"
    sentinel.write_text("replacement data")
    message = {"root": "root identity changed", "round": "round was replaced", "round-without-marker": "round was replaced", "marker": "round marker missing"}[change]
    with pytest.raises(cleanup.sweep.ConfigError, match=message):
        apply(registry, record)
    assert sentinel.read_text() == "replacement data"
    assert registry.load(record["id"])["approval"] is None


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
@pytest.mark.skipif(shutil.which("lsof") is None, reason="successful open-file observation requires lsof")
def test_real_open_file_observation_preserves_path_names(session, monkeypatch, name):
    _, _, root = session
    path = root / name
    path.mkdir()
    monkeypatch.undo()
    with (path / "file").open("w") as stream:
        stream.write("open handle")
        found = cleanup.active_users([str(path)], [])
    assert any(f"process {os.getpid()} uses {path}/file" == item for item in found), found


def test_incomplete_open_file_probe_blocks(session, monkeypatch):
    _, _, root = session
    monkeypatch.undo()
    monkeypatch.setattr(cleanup.subprocess, "run", lambda *a, **k:
        subprocess.CompletedProcess(a, 0, stderr=b"partial observation"))
    assert "incomplete" in cleanup.active_users([str(root)], [])[0]


def task_tree(registry, root):
    task = root / "task"
    cleanup.git(registry.repo, "worktree", "add", "--detach", str(task), "HEAD")
    return task


def commit(repo):
    cleanup.git(repo, "add", ".gitignore")
    cleanup.git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "-qm", "fixture ignore")


@pytest.mark.parametrize("runtime", ["git", "codex"])
def test_ignored_data_requires_preservation_before_retirement(session, runtime):
    registry, record, root = session
    (registry.repo / ".gitignore").write_text(".env\n")
    commit(registry.repo)
    task = task_tree(registry, root)
    secret = task / ".env"
    secret.write_text("unique input")
    registry.track_worktree(record, task, runtime)
    registry.seal(record, {"evidence_complete": True, "retain": [
        {"source": str(secret), "kind": "source", "requires": []}]})
    result = apply(registry, record)
    assert not result["complete"]
    assert "ignored content" in result["paths"][0]["reason"]
    assert secret.read_text() == "unique input"
    retained = Path(record["seal"]["retained"][0]["retained"])
    assert retained.read_text() == "unique input"
    secret.unlink()  # explicit fixture preservation completed above
    result = apply(registry, record)
    assert result["paths"][0]["action"] == ("removed" if runtime == "git" else "archive-with-runtime")


@pytest.mark.parametrize("local_ref", [None, "refs/bisect/good", "refs/worktree/keep", "refs/rewritten/keep"])
def test_unreferenced_detached_commit_preserved(session, local_ref):
    registry, record, root = session
    task = task_tree(registry, root)
    (task / ".gitignore").write_text("cache/\n")
    commit(task)
    head = cleanup.git(task, "rev-parse", "HEAD")
    if local_ref:
        cleanup.git(task, "update-ref", local_ref, head)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    result = apply(registry, record)
    assert "no containing shared branch" in result["paths"][0]["reason"]
    assert cleanup.git(task, "rev-parse", "HEAD") == head
    cleanup.git(registry.repo, "branch", "retained", head)
    assert apply(registry, record)["complete"]
    assert cleanup.git(registry.repo, "rev-parse", "retained") == head


@pytest.mark.parametrize("runtime", ["git", "codex"])
@pytest.mark.parametrize("flag", ["assume-unchanged", "skip-worktree"])
def test_hidden_tracked_changes_preserved(session, runtime, flag):
    registry, record, root = session
    (registry.repo / ".gitignore").write_text("cache\n")
    commit(registry.repo)
    task = task_tree(registry, root)
    registry.track_worktree(record, task, runtime)
    cleanup.git(task, "update-index", "--" + flag, ".gitignore")
    (task / ".gitignore").write_text("unique modification\n")
    assert cleanup.git(task, "status", "--porcelain") == ""
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    result = apply(registry, record)
    assert "index hides changes" in result["paths"][0]["reason"]
    assert (task / ".gitignore").read_text() == "unique modification\n"
    cleanup.git(task, "update-index", "--no-" + flag, ".gitignore")
    assert "uncommitted" in apply(registry, record)["paths"][0]["reason"]
    # Restore only the fixture change after proving it survived both refusals.
    (task / ".gitignore").write_text("cache\n")
    assert apply(registry, record)["paths"][0]["action"] == ("removed" if runtime == "git" else "archive-with-runtime")


@pytest.mark.parametrize("runtime", ["git", "codex"])
def test_shared_store_inside_worktree_is_protected(session, runtime):
    registry, record, root = session
    (registry.repo / ".gitignore").write_text("cache/\n")
    commit(registry.repo)
    task = task_tree(registry, root)
    cleanup.git(root, "clone", "--bare", str(registry.repo), str(task / "cache"))
    consumer = root / "consumer"
    cleanup.git(root, "clone", "--shared", str(task / "cache"), str(consumer))
    config = registry.repo / "cleanup.yaml"
    config.write_text(config.read_text() + f"    - {consumer}\n")
    registry = cleanup.Registry(registry.repo, config)
    record = registry.start()
    registry.track_worktree(record, task, runtime)
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    result = apply(registry, record)
    assert "git dir or object store" in result["paths"][0]["reason"]
    assert cleanup.git(consumer, "cat-file", "-e", "HEAD") == ""
    cleanup.git(consumer, "repack", "-a", "-d")
    (consumer / ".git/objects/info/alternates").unlink()
    shutil.rmtree(task / "cache")  # consumer now owns its objects
    result = apply(registry, record)
    assert result["paths"][0]["action"] == ("removed" if runtime == "git" else "archive-with-runtime")
    assert cleanup.git(consumer, "cat-file", "-e", "HEAD") == ""


@pytest.mark.parametrize("change", ["ignored", "dirty", "head", "store", "active"])
def test_worktree_act_time_recheck(session, monkeypatch, change):
    registry, record, root = session
    (registry.repo / ".gitignore").write_text("cache\n")
    commit(registry.repo)
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    preview = registry.preview

    def late_change(current):
        result = preview(current)
        if change == "ignored":
            (task / "cache").write_text("late data")
        elif change == "dirty":
            (task / "data").write_text("late data")
        elif change == "head":
            (task / ".gitignore").write_text("changed\n")
            commit(task)
        elif change == "store":
            cleanup.git(root, "init", "--bare", str(task / "cache"))
            (registry.common / "objects/info/alternates").write_text(str(task / "cache/objects") + "\n")
        else:
            monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: ["late writer"])
        return result

    token = preview(record)["approval_token"]
    monkeypatch.setattr(registry, "preview", late_change)
    result = registry.apply(record, token, True)
    assert result["paths"][0]["action"] == "kept"
    expected = {"ignored": "ignored content", "dirty": "uncommitted", "head": "head changed",
                "store": "git dir or object store", "active": "active user"}[change]
    assert expected in result["paths"][0]["reason"]
    assert task.is_dir()


def test_grace_change_preserves_token_and_cleanup_authority(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    token = registry.preview(record)["approval_token"]
    config = registry.repo / "cleanup.yaml"
    config.write_text(config.read_text().replace("24h", "48h"))
    resumed = cleanup.Registry(registry.repo, config)
    current = resumed.load(record["id"])
    assert resumed.preview(current)["approval_token"] == token
    assert resumed.apply(current, token, True)["complete"]


@pytest.mark.parametrize("malformed", ["json", "policy-shape", "deep-json"])
def test_list_isolates_invalid_inventory_without_granting_authority(session, malformed):
    registry, record, root = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    config = registry.repo / "cleanup.yaml"
    config.write_text(config.read_text().replace("24h", "48h").replace("scratch/{repo_slug}", "other/{repo_slug}"))
    resumed = cleanup.Registry(registry.repo, config)
    fresh = resumed.start()
    broken = resumed.start()
    if malformed == "json":
        (resumed.location(broken["id"]) / "session.json").write_text("not JSON")
    elif malformed == "deep-json":
        (resumed.location(broken["id"]) / "session.json").write_text('{"policy":' + '[' * 200000 + '0' + ']' * 200000 + '}')
    else:
        broken["policy"] = []
        resumed.save(broken)
    result = subprocess.run([sys.executable, cleanup.__file__, "--config", str(config), "list"],
        cwd=registry.repo, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    listed = {item["id"]: item for item in json.loads(result.stdout)}
    assert listed[fresh["id"]]["seal"] is None
    assert "policy changed" in listed[record["id"]]["unavailable"]
    assert "unavailable" in listed[broken["id"]]
    with pytest.raises(cleanup.sweep.ConfigError, match="policy changed"):
        resumed.load(record["id"])
    assert Path(receipt["path"]).exists()


@pytest.mark.parametrize("operation", ["allocate", "worktree", "process", "seal"])
def test_sealing_freezes_inventory(session, operation):
    registry, record, root = session
    task = task_tree(registry, root)
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    original = (registry.location(record["id"]) / "session.json").read_bytes()
    with pytest.raises(cleanup.sweep.ConfigError, match="inventory is sealed"):
        if operation == "allocate":
            allocate(registry, record)
        elif operation == "worktree":
            registry.track_worktree(record, task, "git")
        elif operation == "process":
            registry.track_process(record, os.getpid())
        else:
            registry.seal(record, {})
    assert (registry.location(record["id"]) / "session.json").read_bytes() == original


def test_persisted_approval_conflict_refused(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    record["approval"] = "previous inventory"
    registry.save(record)
    with pytest.raises(cleanup.sweep.ConfigError, match="different persisted approval"):
        apply(registry, registry.load(record["id"]))
    assert Path(receipt["path"]).exists()


def test_cwd_inside_worktree_keeps_data(session, monkeypatch):
    registry, record, root = session
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    monkeypatch.chdir(task)
    result = apply(registry, record)
    assert "outside the worktree" in result["paths"][0]["reason"]
    assert task.is_dir()
    monkeypatch.chdir(registry.repo)


@pytest.mark.parametrize("bad", ["closure", "duplicate", "retirement"])
def test_evidence_declaration_guards(session, bad):
    registry, record, root = session
    receipt = allocate(registry, record)
    source = root / "source"
    source.write_text("evidence")
    item = {"source": str(source), "kind": "source", "requires": []}
    manifest = {"evidence_complete": True, "retain": [item]}
    expected = "complete required evidence"
    if bad == "closure":
        manifest["evidence_complete"] = False
    elif bad == "duplicate":
        manifest["retain"].append(dict(item))
        expected = "unique"
    else:
        outside = root / "outside"
        outside.write_text("not owned")
        manifest["retire"] = [{"source": str(outside), "reason": "redundant", "replaced_by": [str(source)]}]
        expected = "owned round"
    with pytest.raises(cleanup.sweep.ConfigError, match=expected):
        registry.seal(record, manifest)
    assert registry.load(record["id"])["seal"] is None
    assert Path(receipt["path"]).exists()


@pytest.mark.parametrize("state,expected", [("complete", 0), ("native", 1), ("refused", 2)])
def test_cli_exit_status(session, state, expected):
    registry, record, root = session
    if state == "native":
        registry.track_worktree(record, task_tree(registry, root), "codex")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    token = registry.preview(record)["approval_token"] if state != "refused" else "invalid"
    code = "import sys; sys.path.insert(0, sys.argv[1]); import session_cleanup as c; c.active_users=lambda paths,pids: []; raise SystemExit(c.main(sys.argv[2:]))"
    result = subprocess.run([sys.executable, "-c", code, str(Path(cleanup.__file__).parent),
        "--config", str(registry.repo / "cleanup.yaml"), "apply", record["id"],
        "--approve", token, "--processes-finished"], cwd=registry.repo,
        capture_output=True, text=True, timeout=30)
    assert result.returncode == expected, result.stderr
    if state != "refused":
        assert json.loads(result.stdout)["complete"] == (state == "complete")
