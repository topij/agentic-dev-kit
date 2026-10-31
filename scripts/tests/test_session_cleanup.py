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

EXCEPTION = {"task": "synthetic unfinished task", "next_action": "read the report",
             "delete_when": "the task merges"}


@pytest.fixture
def session(tmp_path, monkeypatch):
    yield from make_session(tmp_path, monkeypatch)


@pytest.fixture
def device_session(tmp_path, monkeypatch):
    """A session bound to the "device" identity kind, as on Linux or without a volume UUID."""
    monkeypatch.setattr(cleanup.sweep, "_volume_uuid", lambda path: None)
    yield from make_session(tmp_path, monkeypatch)


def make_session(tmp_path, monkeypatch):
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


def allocate(registry, record, keep_previous=None):
    root = cleanup.sweep.expand_root(registry.settings.roots[0], root=registry.repo)
    Path(root).mkdir(parents=True, exist_ok=True)
    return registry.allocate(record, root, cleanup.git(registry.repo, "rev-parse", "HEAD"),
                             keep_previous)


def seal(registry, record, receipt, scope=None):
    path = Path(receipt["path"])
    evidence = path / "result.md"
    evidence.write_text("terminal report\n")
    screenshot = path / "capture.bin"
    screenshot.write_bytes(b"authoritative bytes\x00\xff")
    logs = path / "verbose.log"
    logs.write_text("redundant diagnostics\n")
    sealing = registry.seal if scope is None else (lambda r, m: registry.seal_round(r, scope, m))
    return sealing(record, {"evidence_complete": True, "retain": [
        {"source": str(evidence), "kind": "report", "requires": [str(screenshot)], "exception": EXCEPTION},
        {"source": str(screenshot), "kind": "asset", "requires": [], "exception": EXCEPTION},
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
    later = allocate(task_registry, record, keep_previous="retired with the inventory")
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
            {"source": str(report), "kind": "report", "requires": [str(report.parent / "missing")],
             "exception": EXCEPTION}]})
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
        {"source": str(path), "kind": "report", "requires": [], "exception": EXCEPTION}]}))
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
    message = {"root": r"root identity changed \(stored \[", "round": "round was replaced", "round-without-marker": "round was replaced", "marker": "round marker missing"}[change]
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
        {"source": str(secret), "kind": "source", "requires": [], "exception": EXCEPTION}]})
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
    item = {"source": str(source), "kind": "source", "requires": [], "exception": EXCEPTION}
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


@pytest.mark.parametrize("options,expected", [({}, 30), ({"timeout": 300}, 300)])
def test_git_forwards_timeout_to_subprocess(tmp_path, monkeypatch, options, expected):
    observed = []

    def run(argv, **kwargs):
        observed.append((argv, kwargs["timeout"]))
        return subprocess.CompletedProcess(argv, 0, stdout="observed\n", stderr="")

    monkeypatch.setattr(cleanup.subprocess, "run", run)
    assert cleanup.git(tmp_path, "status", **options) == "observed"
    assert observed == [(["git", "-C", str(tmp_path), "status"], expected)]


@pytest.mark.parametrize("phase", ["preview", "recheck", "remove"])
def test_git_timeout_is_per_item_and_retryable(session, monkeypatch, phase):
    registry, record, root = session
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    original = cleanup.git
    calls = 0

    def timed(repo, *args, **kwargs):
        nonlocal calls
        if Path(repo) == task and args == ("rev-parse", "HEAD"):
            calls += 1
            if (phase == "preview" and calls == 1) or (phase == "recheck" and calls == 2):
                raise subprocess.TimeoutExpired(["git", *args], 30)
        if args[:2] == ("worktree", "remove"):
            assert kwargs["timeout"] == 300
            if phase == "remove":
                raise subprocess.TimeoutExpired(["git", *args], kwargs["timeout"])
        return original(repo, *args, **kwargs)

    token = registry.preview(record)["approval_token"]
    monkeypatch.setattr(cleanup, "git", timed)
    result = registry.apply(record, token, True)
    assert not result["complete"]
    assert result["paths"][0]["action"] == "kept"
    assert "timed out" in result["paths"][0]["reason"]
    assert task.is_dir()
    assert not Path(receipt["path"]).exists()
    assert registry.load(record["id"])["last_result"] == result
    registry.verify_evidence(record)
    monkeypatch.setattr(cleanup, "git", original)
    assert registry.apply(registry.load(record["id"]), token, True)["complete"]
    assert not task.exists()


def test_unapproved_interrupted_journal_is_not_authority(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    record["rounds"][0]["status"] = "removing"
    registry.save(record)
    with pytest.raises(cleanup.sweep.ConfigError, match="durable approval"):
        registry.load(record["id"])
    assert Path(receipt["path"]).is_dir()


def test_reappeared_path_prevents_complete_result(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    original = cleanup.sweep.finish_review_round

    def reappears(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get("apply"):
            Path(receipt["path"]).mkdir()
            (Path(receipt["path"]) / "new-data").write_text("must survive")
        return result

    monkeypatch.setattr(cleanup.sweep, "finish_review_round", reappears)
    result = apply(registry, record)
    assert not result["complete"]
    assert result["paths"][0]["action"] == "kept"
    assert "exists after retirement" in result["paths"][0]["reason"]
    assert (Path(receipt["path"]) / "new-data").read_text() == "must survive"


def test_round_act_time_active_user_refusal(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    original = registry.preview

    def late_user(current):
        result = original(current)
        monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: ["late writer"])
        return result

    token = original(record)["approval_token"]
    monkeypatch.setattr(registry, "preview", late_user)
    result = registry.apply(record, token, True)
    assert not result["complete"]
    assert "active user" in result["paths"][0]["reason"]
    assert registry.load(record["id"])["rounds"][0]["status"] == "allocated"
    assert Path(receipt["path"]).is_dir()


def test_configured_root_inside_retiring_worktree_is_preserved(session):
    registry, record, root = session
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    # An absent configured root still protects its future owner. No ignored,
    # dirty or nested worktree refusal can stand in for this boundary.
    from dataclasses import replace
    registry.settings = replace(registry.settings, roots=[*registry.settings.roots, str(task / "future-scratch")])
    result = apply(registry, record)
    assert result["paths"][0]["action"] == "kept"
    assert "configured root" in result["paths"][0]["reason"]
    assert task.exists()


def test_absent_registered_worktree_requires_reconciliation(session):
    registry, record, root = session
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    task.rename(root / "moved-task")
    result = apply(registry, record)
    assert not result["complete"]
    assert result["paths"][0]["action"] == "kept"
    assert "still registered" in result["paths"][0]["reason"]
    assert (root / "moved-task").is_dir()


def apply_round(registry, record, receipt):
    token = registry.preview_round(record, receipt["id"])["approval_token"]
    return registry.apply_round(record, receipt["id"], token, True)


def test_allocate_refuses_while_an_earlier_round_is_unretired(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    original = (registry.location(record["id"]) / "session.json").read_bytes()
    before = sorted(Path(receipt["root"]).iterdir())
    for reason in (None, "", "   "):
        with pytest.raises(cleanup.sweep.ConfigError, match=f"{receipt['id']} is not retired"):
            allocate(registry, record, keep_previous=reason)
    # Refused before allocation: no new round directory and no record change.
    assert sorted(Path(receipt["root"]).iterdir()) == before
    assert (registry.location(record["id"]) / "session.json").read_bytes() == original


def test_round_retirement_keeps_the_inventory_open(session):
    registry, record, _ = session
    first = allocate(registry, record)
    sealed = seal(registry, record, first, scope=first["id"])
    result = apply_round(registry, record, first)
    assert result["complete"] and result["paths"][0]["action"] == "removed"
    assert not Path(first["path"]).exists()
    record = registry.load(record["id"])
    assert record["seal"] is None and record["approval"] is None
    assert record["rounds"][0]["status"] == "removed" and record["complete"]
    for item in sealed["retained"]:
        assert cleanup.hash_file(Path(item["retained"])) == (item["sha256"], item["size"])
    second = allocate(registry, record)
    assert Path(second["path"]).is_dir()
    assert not registry.load(record["id"])["complete"]
    # Retiring again is idempotent; the inventory still retires as a whole.
    assert apply_round(registry, record, first)["complete"]
    seal(registry, record, second)
    assert apply(registry, record)["complete"]
    assert not Path(second["path"]).exists()


def test_kept_round_is_recorded_and_retires_with_the_inventory(session):
    registry, record, _ = session
    first = allocate(registry, record)
    second = allocate(registry, record, keep_previous="lens worktree reused next round")
    assert registry.load(record["id"])["rounds"][0]["kept"] == "lens worktree reused next round"
    # A kept round no longer blocks; the round allocated after it still does.
    with pytest.raises(cleanup.sweep.ConfigError, match=f"{second['id']} is not retired"):
        allocate(registry, record)
    seal(registry, record, second)
    assert apply(registry, record)["complete"]
    assert not Path(first["path"]).exists()


def test_interrupted_round_retirement_refuses_allocation_until_resumed(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    token = registry.preview_round(record, receipt["id"])["approval_token"]

    def interrupted(path, root, identity):
        os.unlink(os.path.join(path, cleanup.sweep.ROUND_MARKER))
        raise OSError("killed mid removal")

    monkeypatch.setattr(cleanup.sweep, "remove_entry", interrupted)
    assert not registry.apply_round(record, receipt["id"], token, True)["complete"]
    monkeypatch.undo()
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [])
    # The round's own approval is the durable authority for its journal.
    resumed = registry.load(record["id"])
    assert resumed["rounds"][0]["status"] == "removing" and resumed["approval"] is None
    with pytest.raises(cleanup.sweep.ConfigError, match="interrupted"):
        allocate(registry, resumed, keep_previous="any reason")
    assert registry.apply_round(resumed, receipt["id"], token, True)["complete"]
    assert Path(allocate(registry, registry.load(record["id"]))["path"]).is_dir()


def test_round_scope_guards(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    with pytest.raises(cleanup.sweep.ConfigError, match="receipt id"):
        registry.preview_round(record, "0" * 32)
    with pytest.raises(cleanup.sweep.ConfigError, match="seal"):
        registry.preview_round(record, receipt["id"])
    seal(registry, record, receipt, scope=receipt["id"])
    with pytest.raises(cleanup.sweep.ConfigError, match="already sealed"):
        seal(registry, record, receipt, scope=receipt["id"])
    with pytest.raises(cleanup.sweep.ConfigError, match="approval"):
        registry.apply_round(record, receipt["id"], "wrong", True)
    token = registry.preview_round(record, receipt["id"])["approval_token"]
    with pytest.raises(cleanup.sweep.ConfigError, match="writers"):
        registry.apply_round(record, receipt["id"], token, False)
    record["rounds"][0].update(status="removing", approval="previous round")
    with pytest.raises(cleanup.sweep.ConfigError, match="different persisted approval"):
        registry.apply_round(record, receipt["id"], token, True)
    assert Path(receipt["path"]).is_dir()


def test_round_retirement_respects_active_users(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: ["writer"])
    result = apply_round(registry, record, receipt)
    assert not result["complete"] and result["active_users"] == ["writer"]
    assert registry.load(record["id"])["rounds"][0]["status"] == "allocated"
    assert Path(receipt["path"]).is_dir()


def test_cli_round_lifecycle(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    report = Path(receipt["path"]) / "report.md"
    report.write_text("terminal report\n")
    manifest = root / "round-manifest.json"
    manifest.write_text(json.dumps({"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}]}))

    def cli(*args):
        return subprocess.run([sys.executable, cleanup.__file__, "--config",
            str(registry.repo / "cleanup.yaml"), *args], cwd=registry.repo,
            capture_output=True, text=True, timeout=30)

    refused = cli("allocate", record["id"], "--root", receipt["root"], "--head", receipt["head"])
    assert refused.returncode == 2 and "--keep-previous" in refused.stderr
    assert cli("seal", record["id"], str(manifest), "--round", receipt["id"]).returncode == 0
    preview = cli("preview", record["id"], "--round", receipt["id"])
    token = json.loads(preview.stdout)["approval_token"]
    # The real lsof probe runs in this subprocess; tolerate only its blocker.
    applied = cli("apply", record["id"], "--round", receipt["id"], "--approve", token,
                  "--processes-finished")
    if applied.returncode == 1 and any("open-file observation unavailable" in user
                                       for user in json.loads(applied.stdout)["active_users"]):
        pytest.skip("open-file probe unavailable in this environment")
    assert applied.returncode == 0, applied.stderr
    assert not Path(receipt["path"]).exists()
    assert cli("allocate", record["id"], "--root", receipt["root"], "--head", receipt["head"]).returncode == 0


def test_kept_round_does_not_block_once_later_rounds_retire(session):
    registry, record, _ = session
    first = allocate(registry, record)
    second = allocate(registry, record, keep_previous="kept for comparison")
    seal(registry, record, second, scope=second["id"])
    assert apply_round(registry, record, second)["complete"]
    third = allocate(registry, record)
    assert Path(first["path"]).is_dir() and Path(third["path"]).is_dir()
    assert not registry.load(record["id"])["complete"]


def test_round_token_binds_its_evidence_seal(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    token = registry.preview_round(record, receipt["id"])["approval_token"]
    record["rounds"][0]["seal"]["retired"] = []
    with pytest.raises(cleanup.sweep.ConfigError, match="approval"):
        registry.apply_round(record, receipt["id"], token, True)
    assert Path(receipt["path"]).is_dir()


def test_cli_empty_round_is_refused_not_widened(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    report = Path(receipt["path"]) / "report.md"
    report.write_text("terminal report\n")
    manifest = root / "round-manifest.json"
    manifest.write_text(json.dumps({"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}]}))
    base = [sys.executable, cleanup.__file__, "--config", str(registry.repo / "cleanup.yaml")]
    for args in (["seal", record["id"], str(manifest), "--round", ""],
                 ["preview", record["id"], "--round", ""],
                 ["apply", record["id"], "--round", "", "--approve", "x", "--processes-finished"]):
        result = subprocess.run(base + args, cwd=registry.repo, capture_output=True, text=True, timeout=30)
        assert result.returncode == 2 and "receipt id" in result.stderr, args
    assert registry.load(record["id"])["seal"] is None


def test_interrupted_kept_round_still_refuses_allocation(session):
    registry, record, _ = session
    first = allocate(registry, record)
    second = allocate(registry, record, keep_previous="kept for comparison")
    seal(registry, record, second, scope=second["id"])
    assert apply_round(registry, record, second)["complete"]
    record["rounds"][0].update(status="removing", approval="approved")
    with pytest.raises(cleanup.sweep.ConfigError, match="interrupted"):
        allocate(registry, record, keep_previous="any reason")
    assert Path(first["path"]).is_dir()


def test_writers_freeze_only_while_a_round_is_removing(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    token = registry.preview_round(record, receipt["id"])["approval_token"]

    def interrupted(path, root, identity):
        os.unlink(os.path.join(path, cleanup.sweep.ROUND_MARKER))
        raise OSError("killed mid removal")

    monkeypatch.setattr(cleanup.sweep, "remove_entry", interrupted)
    assert not registry.apply_round(record, receipt["id"], token, True)["complete"]
    monkeypatch.undo()
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [])
    record = registry.load(record["id"])
    assert record["rounds"][0]["approval"] == token
    with pytest.raises(cleanup.sweep.ConfigError, match="interrupted retirement"):
        registry.track_process(record, os.getpid())
    # The journalled approval still completes the round, after which writers register.
    assert registry.apply_round(record, receipt["id"], token, True)["complete"]
    registry.track_process(record, os.getpid())
    assert registry.load(record["id"])["pids"] == [os.getpid()]


@pytest.mark.parametrize("stop", ["active", "refused"])
def test_a_stopped_round_apply_persists_no_approval_and_freezes_nothing(session, monkeypatch, stop):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    token = registry.preview_round(record, receipt["id"])["approval_token"]
    if stop == "active":
        monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: ["writer"])
    else:
        def refused(*args, **kwargs):
            if kwargs.get("apply"):
                raise cleanup.sweep.Refused("guard says no")
            return original(*args, **kwargs)
        original = cleanup.sweep.finish_review_round
        monkeypatch.setattr(cleanup.sweep, "finish_review_round", refused)
    assert not registry.apply_round(record, receipt["id"], token, True)["complete"]
    monkeypatch.undo()
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [])
    record = registry.load(record["id"])
    assert record["rounds"][0]["status"] == "allocated" and "approval" not in record["rounds"][0]
    # A kept round blocks neither writer registration nor a kept allocation.
    registry.track_process(record, os.getpid())
    later = allocate(registry, record, keep_previous="earlier round refused")
    assert Path(later["path"]).is_dir()
    # The stale token no longer matches; a fresh preview retires the round.
    with pytest.raises(cleanup.sweep.ConfigError, match="approval does not match"):
        registry.apply_round(record, receipt["id"], token, True)
    assert apply_round(registry, record, receipt)["complete"]


def test_round_result_is_persisted_on_the_round(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: ["writer"])
    apply_round(registry, record, receipt)
    stored = registry.load(record["id"])["rounds"][0]["last_result"]
    assert stored["complete"] is False and stored["active_users"] == ["writer"]
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [])
    apply_round(registry, record, receipt)
    stored = registry.load(record["id"])["rounds"][0]["last_result"]
    assert stored["complete"] and stored["paths"][0]["action"] == "removed"


def test_a_vanished_round_is_recorded_removed_and_unblocks_allocation(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    shutil.rmtree(receipt["path"])
    result = apply_round(registry, record, receipt)
    assert result["complete"] and result["paths"][0]["action"] == "absent"
    assert registry.load(record["id"])["rounds"][0]["status"] == "removed"
    assert Path(allocate(registry, record)["path"]).is_dir()


def test_complete_requires_every_round_removed_and_no_worktree(session):
    registry, record, root = session
    first = allocate(registry, record)
    second = allocate(registry, record, keep_previous="kept for comparison")
    seal(registry, record, second, scope=second["id"])
    assert apply_round(registry, record, second)["complete"]
    assert not registry.load(record["id"])["complete"]
    seal(registry, record, first, scope=first["id"])
    assert apply_round(registry, record, first)["complete"]
    assert registry.load(record["id"])["complete"]
    registry.track_worktree(record, task_tree(registry, root), "git")
    assert not registry.load(record["id"])["complete"]


def test_round_seal_refuses_a_retiring_round_and_foreign_diagnostics(session):
    registry, record, _ = session
    first = allocate(registry, record)
    second = allocate(registry, record, keep_previous="kept for comparison")
    foreign = Path(first["path"]) / "verbose.log"
    foreign.write_text("diagnostics of another round\n")
    report = Path(second["path"]) / "report.md"
    report.write_text("terminal report\n")
    with pytest.raises(cleanup.sweep.ConfigError, match="owned round"):
        registry.seal_round(record, second["id"], {"evidence_complete": True, "retain": [
            {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}], "retire": [
            {"source": str(foreign), "reason": "superseded", "replaced_by": [str(report)]}]})
    record["rounds"][1]["status"] = "removing"
    with pytest.raises(cleanup.sweep.ConfigError, match="already sealed or retiring"):
        seal(registry, record, second, scope=second["id"])


def test_round_token_binds_registered_writers(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    token = registry.preview_round(record, receipt["id"])["approval_token"]
    registry.track_process(record, os.getpid())
    with pytest.raises(cleanup.sweep.ConfigError, match="approval"):
        registry.apply_round(record, receipt["id"], token, True)
    assert Path(receipt["path"]).is_dir()


def test_a_tracked_worktree_keeps_a_round_only_retirement_incomplete(session):
    registry, record, root = session
    registry.track_worktree(record, task_tree(registry, root), "git")
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    assert apply_round(registry, record, receipt)["complete"]
    assert not registry.load(record["id"])["complete"]


def test_preview_round_requires_the_rounds_own_seal(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    with pytest.raises(cleanup.sweep.ConfigError, match="seal required evidence"):
        registry.preview_round(record, receipt["id"])


def test_inventory_apply_records_a_vanished_round_removed(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    shutil.rmtree(receipt["path"])
    result = apply(registry, record)
    assert result["complete"] and result["paths"][0]["action"] == "absent"
    assert registry.load(record["id"])["rounds"][0]["status"] == "removed"


def renumber(monkeypatch, *, inode=0):
    """Simulate a volume whose device number changed (a macOS reboot), every path at once."""
    original = cleanup.sweep._identity

    def shifted(path):
        device, number = original(path)
        return (device + 1, number + inode)
    monkeypatch.setattr(cleanup.sweep, "_identity", shifted)


def stored(registry, record):
    return json.loads((registry.location(record["id"]) / "session.json").read_text())


def vanished_round(registry, record):
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    shutil.rmtree(receipt["path"])
    return receipt


def test_device_renumber_names_the_field_and_points_to_reconcile(device_session, monkeypatch):
    registry, record, _ = device_session
    _kind, device, _inode = record["common_identity"]
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError) as refused:
        registry.load(record["id"])
    message = str(refused.value)
    assert message.startswith("session repository identity or cleanup policy changed: ")
    assert f"device (stored {device}, current {device + 1})" in message
    assert "inode (" not in message and "; policy " not in message
    assert f"reconcile {record['id']}" in message
    listed = {item["id"]: item for item in registry.inventories()}
    assert f"device (stored {device}" in listed[record["id"]]["unavailable"]


@pytest.mark.parametrize("change", ["inode", "policy", "schema"])
def test_other_bound_changes_are_named_without_a_reconcile_hint(device_session, monkeypatch, change):
    registry, record, _ = device_session
    if change == "inode":
        renumber(monkeypatch, inode=1)
        expected = "inode (stored"
    elif change == "policy":
        registry.policy["registry"] = "other"
        expected = 'policy registry (stored "cleanup-sessions", current "other")'
    else:
        record["schema"] = "devkit-cleanup-session/0"
        registry.save(record)
        expected = "schema (stored 'devkit-cleanup-session/0'"
    with pytest.raises(cleanup.sweep.ConfigError, match="identity or cleanup policy changed") as refused:
        registry.load(record["id"])
    assert expected in str(refused.value)
    assert "reconcile" not in str(refused.value)
    with pytest.raises(cleanup.sweep.ConfigError, match="only a changed device number"):
        registry.reconcile_plan(record["id"])


def test_reconcile_rebinds_an_absent_inventory_after_approval(device_session, monkeypatch):
    registry, record, _ = device_session
    receipt = vanished_round(registry, record)
    retained = record["rounds"][0]["seal"]["retained"]
    before = stored(registry, record)
    renumber(monkeypatch)
    plan = registry.reconcile_plan(record["id"])[1]
    assert plan["rounds_marked_removed"] == [receipt["id"]]
    assert stored(registry, record) == before  # preview writes nothing
    with pytest.raises(cleanup.sweep.ConfigError, match="approval does not match"):
        registry.reconcile(record["id"], "wrong")
    assert stored(registry, record) == before
    registry.reconcile(record["id"], plan["approval_token"])
    current = registry.load(record["id"])
    assert current["common_identity"] == plan["common_identity"]["current"]
    assert current["rounds"][0]["status"] == "removed" and current["complete"]
    assert current["reconciled"][0]["common_identity"]["stored"] == before["common_identity"]
    for item in retained:  # reconcile retires no evidence
        assert cleanup.hash_file(Path(item["retained"])) == (item["sha256"], item["size"])
    # An open inventory keeps accepting work after reconcile. (Allocation is not
    # used here: the sweeper validates rounds through lstat, outside this seam.)
    registry.track_process(current, os.getpid())
    assert registry.load(record["id"])["pids"] == [os.getpid()]


def test_reconcile_refuses_a_present_round_and_writes_nothing(device_session, monkeypatch):
    registry, record, _ = device_session
    receipt = allocate(registry, record)
    before = stored(registry, record)
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError, match="still present: " + receipt["path"]):
        registry.reconcile_plan(record["id"])
    assert stored(registry, record) == before
    assert Path(receipt["path"]).is_dir()


def test_reconcile_refuses_an_absent_but_registered_worktree(device_session, monkeypatch):
    registry, record, root = device_session
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    task.rename(root / "moved-task")
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError, match="still present: " + str(task)):
        registry.reconcile_plan(record["id"])


def test_reconcile_refuses_an_uninspectable_path_and_writes_nothing(device_session, monkeypatch):
    registry, record, _ = device_session
    receipt = vanished_round(registry, record)
    before = stored(registry, record)
    original = os.lstat

    def unreadable(path, *args, **kwargs):
        if str(path) == receipt["path"]:
            raise PermissionError(13, "Permission denied", str(path))
        return original(path, *args, **kwargs)
    renumber(monkeypatch)
    monkeypatch.setattr(cleanup.os, "lstat", unreadable)
    with pytest.raises(PermissionError):
        registry.reconcile_plan(record["id"])
    with pytest.raises(PermissionError):
        registry.reconcile(record["id"], "any")
    assert stored(registry, record) == before


def test_reconcile_refuses_an_unchanged_inventory(device_session):
    registry, record, _ = device_session
    with pytest.raises(cleanup.sweep.ConfigError, match="nothing to reconcile"):
        registry.reconcile_plan(record["id"])


def test_reconcile_token_binds_the_stored_record(device_session, monkeypatch):
    registry, record, _ = device_session
    vanished_round(registry, record)
    renumber(monkeypatch)
    token = registry.reconcile_plan(record["id"])[1]["approval_token"]
    changed = stored(registry, record)
    changed["pids"] = [os.getpid()]
    registry.save(changed)
    with pytest.raises(cleanup.sweep.ConfigError, match="approval does not match"):
        registry.reconcile(record["id"], token)


def test_cli_reconcile_previews_then_applies(session, monkeypatch):
    registry, record, _ = session
    vanished_round(registry, record)
    # The CLI runs in a child process, outside the identity seam, so store a
    # schema 1 record whose device differs from the current one.
    changed = stored(registry, record)
    common = os.stat(registry.common)
    changed.update(schema=cleanup.LEGACY_SCHEMA, common_identity=[common.st_dev + 1, common.st_ino])
    registry.save(changed)
    command = [sys.executable, cleanup.__file__, "--config", str(registry.repo / "cleanup.yaml"),
               "reconcile", record["id"]]
    preview = subprocess.run(command, cwd=registry.repo, capture_output=True, text=True, timeout=30)
    assert preview.returncode == 0, preview.stderr
    token = json.loads(preview.stdout)["approval_token"]
    assert stored(registry, record) == changed
    applied = subprocess.run([*command, "--approve", token], cwd=registry.repo,
                             capture_output=True, text=True, timeout=30)
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["applied"] is True
    assert registry.load(record["id"])["complete"]
    again = subprocess.run(command, cwd=registry.repo, capture_output=True, text=True, timeout=30)
    assert again.returncode == 2 and "nothing to reconcile" in again.stderr


def age_stored_device(registry, record):
    """Rewrite the stored device numbers as a pre-reboot record would hold them."""
    old = stored(registry, record)
    old["common_identity"][1] -= 1
    for entry in old["rounds"]:
        entry["receipt"]["root_identity"][1] -= 1
    registry.save(old)
    return old


def test_reconciled_inventory_previews_and_applies_inventory_wide(device_session, tmp_path):
    registry, record, root = device_session
    vanished_round(registry, record)
    age_stored_device(registry, record)
    registry.reconcile(record["id"], registry.reconcile_plan(record["id"])[1]["approval_token"])
    current = registry.load(record["id"])
    report = root / "inventory-report.md"
    report.write_text("final report\n")
    registry.seal(current, {"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}]})
    assert [p["action"] for p in registry.preview(current)["paths"]] == ["absent"]
    assert apply(registry, current)["complete"]


def test_unremoved_absent_round_still_checks_its_root(device_session):
    registry, record, _ = device_session
    receipt = vanished_round(registry, record)
    old = stored(registry, record)
    old["rounds"][0]["receipt"]["root_identity"][1] -= 1
    registry.save(old)
    with pytest.raises(cleanup.sweep.ConfigError,
                       match=r"allocation root identity changed \(stored \[.*current \["):
        registry.preview_round(registry.load(record["id"]), receipt["id"])


def test_plan_filters_removed_rounds_and_names_unsealed_ones(device_session, monkeypatch):
    registry, record, _ = device_session
    retired = allocate(registry, record)
    seal(registry, record, retired, scope=retired["id"])
    apply_round(registry, record, retired)
    unsealed = allocate(registry, record)
    shutil.rmtree(unsealed["path"])
    renumber(monkeypatch)
    plan = registry.reconcile_plan(record["id"])[1]
    assert plan["rounds_marked_removed"] == [unsealed["id"]]
    assert plan["rounds_without_seal"] == [unsealed["id"]]
    registry.reconcile(record["id"], plan["approval_token"])
    rounds = registry.load(record["id"])["rounds"]
    assert "reconciled" not in rounds[0]
    assert rounds[1]["reconciled"] == plan["approval_token"]


def test_reconcile_history_appends(device_session, monkeypatch):
    registry, record, _ = device_session
    vanished_round(registry, record)
    for _ in range(2):
        renumber(monkeypatch)
        registry.reconcile(record["id"], registry.reconcile_plan(record["id"])[1]["approval_token"])
    history = registry.load(record["id"])["reconciled"]
    assert len(history) == 2
    assert history[0]["common_identity"]["current"] == history[1]["common_identity"]["stored"]


def test_reconcile_token_binds_the_current_identity(device_session, monkeypatch):
    registry, record, _ = device_session
    vanished_round(registry, record)
    renumber(monkeypatch)
    token = registry.reconcile_plan(record["id"])[1]["approval_token"]
    before = stored(registry, record)
    renumber(monkeypatch)  # the device moves again between preview and apply
    with pytest.raises(cleanup.sweep.ConfigError, match="approval does not match"):
        registry.reconcile(record["id"], token)
    assert stored(registry, record) == before


def test_reconcile_refuses_an_unapproved_interrupted_journal(device_session, monkeypatch):
    registry, record, _ = device_session
    vanished_round(registry, record)
    record["rounds"][0]["status"] = "removing"
    registry.save(record)
    before = stored(registry, record)
    # Unchanged device: the journal refusal is reported, not "nothing to reconcile".
    with pytest.raises(cleanup.sweep.ConfigError, match="lacks its durable approval"):
        registry.reconcile_plan(record["id"])
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError, match="lacks its durable approval"):
        registry.reconcile_plan(record["id"])
    with pytest.raises(cleanup.sweep.ConfigError, match="lacks its durable approval"):
        registry.reconcile(record["id"], "any")
    assert stored(registry, record) == before


@pytest.mark.parametrize("change", ["id", "one-sided-policy-key"])
def test_id_and_one_sided_policy_differences_are_named(device_session, change):
    registry, record, _ = device_session
    if change == "id":
        path = registry.location(record["id"]) / "session.json"
        data = json.loads(path.read_text())
        data["id"] = "0" * 32
        path.write_text(json.dumps(data))
        expected = f"id (stored '{'0' * 32}', current '{record['id']}')"
    else:
        registry.policy["extra"] = "x"
        expected = 'policy extra (stored absent, current "x")'
    with pytest.raises(cleanup.sweep.ConfigError) as refused:
        registry.load(record["id"])
    assert expected in str(refused.value)


def test_rounds_without_seal_needs_every_condition(device_session, monkeypatch):
    registry, record, _ = device_session
    removed = allocate(registry, record)
    seal(registry, record, removed, scope=removed["id"])
    apply_round(registry, record, removed)
    sealed = vanished_round(registry, record)
    unsealed = allocate(registry, record, keep_previous="probe")
    shutil.rmtree(unsealed["path"])
    edited = stored(registry, record)
    edited["rounds"][0]["seal"] = None  # removed, and without its own seal
    registry.save(edited)
    renumber(monkeypatch)
    plan = registry.reconcile_plan(record["id"])[1]
    assert plan["rounds_marked_removed"] == [sealed["id"], unsealed["id"]]
    assert plan["rounds_without_seal"] == [unsealed["id"]]


def test_an_inventory_seal_covers_every_round(device_session, monkeypatch):
    registry, record, _ = device_session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    shutil.rmtree(receipt["path"])
    renumber(monkeypatch)
    plan = registry.reconcile_plan(record["id"])[1]
    assert plan["rounds_marked_removed"] == [receipt["id"]]
    assert plan["rounds_without_seal"] == []


def test_removing_absent_round_still_checks_its_root(device_session):
    registry, record, _ = device_session
    vanished_round(registry, record)
    edited = stored(registry, record)
    edited["rounds"][0].update(status="removing", approval="persisted")
    edited["rounds"][0]["receipt"]["root_identity"][1] -= 1
    registry.save(edited)
    with pytest.raises(cleanup.sweep.ConfigError, match="allocation root identity changed"):
        registry.round_outcome(registry.load(record["id"])["rounds"][0])


def test_removed_round_whose_path_reappeared_keeps_its_checks(device_session):
    registry, record, _ = device_session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    apply_round(registry, record, receipt)
    Path(receipt["path"]).mkdir()
    sentinel = Path(receipt["path"]) / "must-remain"
    sentinel.write_text("replacement data")
    # Either refusal shows the checks ran: APFS gives the new directory a new
    # inode ("replaced"), while ext4 may reuse it, and the missing marker refuses.
    with pytest.raises(cleanup.sweep.ConfigError, match="round was replaced|round marker missing"):
        registry.round_outcome(registry.load(record["id"])["rounds"][0])
    assert sentinel.read_text() == "replacement data"


@pytest.mark.parametrize(("field", "value", "expected"), [
    ("common_identity", [True, 5], "common identity (stored [True, 5], current ["),
    ("common_identity", "16777232", "common identity (stored '16777232', current ["),
    ("policy", ["roots"], "policy (stored value is not a mapping)"),
])
def test_malformed_bindings_are_named(session, field, value, expected):
    registry, record, _ = session
    record[field] = value
    registry.save(record)
    with pytest.raises(cleanup.sweep.ConfigError) as refused:
        registry.load(record["id"])
    assert expected in str(refused.value)


# --------------------------------------------------------------------------- #
# boot-stable identity and the schema 1 migration (#1253)
# --------------------------------------------------------------------------- #

UUID_A = "AC62930A-94C1-4C33-BEB6-1E9E9C72714E"
UUID_B = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def volume_session(tmp_path, monkeypatch):
    """A session bound to a fixed volume UUID, on any platform."""
    monkeypatch.setattr(cleanup.sweep, "_volume_uuid", lambda path: UUID_A)
    yield from make_session(tmp_path, monkeypatch)


def test_new_records_bind_the_volume_and_survive_a_renumber(volume_session, monkeypatch):
    registry, record, root = volume_session
    assert record["schema"] == cleanup.SCHEMA == "devkit-cleanup-session/2"
    assert record["common_identity"] == ["volume", UUID_A, os.stat(registry.common).st_ino]
    task = task_tree(registry, root)
    registry.track_worktree(record, task, "git")
    renumber(monkeypatch)
    current = registry.load(record["id"])
    assert current["worktrees"][0]["identity"][:2] == ["volume", UUID_A]
    assert registry.worktree_reason(current["worktrees"][0]) != "worktree identity changed"
    with pytest.raises(cleanup.sweep.ConfigError, match="nothing to reconcile"):
        registry.reconcile_plan(record["id"])


@pytest.mark.parametrize(("earlier", "later", "expected"), [
    (UUID_A, UUID_B, f"volume (stored {UUID_A}, current {UUID_B})"),
    (UUID_A, None, "identity kind (stored 'volume', current 'device')"),
    (None, UUID_A, "identity kind (stored 'device', current 'volume')"),
])
def test_another_volume_or_kind_is_refused_and_not_reconcilable(tmp_path, monkeypatch, earlier, later, expected):
    monkeypatch.setattr(cleanup.sweep, "_volume_uuid", lambda path: earlier)
    registry, record, _ = next(make_session(tmp_path, monkeypatch))
    monkeypatch.setattr(cleanup.sweep, "_volume_uuid", lambda path: later)
    with pytest.raises(cleanup.sweep.ConfigError) as refused:
        registry.load(record["id"])
    assert expected in str(refused.value) and "reconcile" not in str(refused.value)
    with pytest.raises(cleanup.sweep.ConfigError, match="other bound fields differ"):
        registry.reconcile_plan(record["id"])


def as_schema_1(registry, record):
    """Rewrite the stored record as one written before #1253: (st_dev, st_ino) bindings."""
    old = stored(registry, record)
    old["schema"] = cleanup.LEGACY_SCHEMA
    common = os.stat(registry.common)
    old["common_identity"] = [common.st_dev, common.st_ino]
    for worktree in old["worktrees"]:
        found = os.stat(worktree["path"])
        worktree["identity"] = [found.st_dev, found.st_ino]
    for entry in old["rounds"]:  # version 1 receipts, with their markers where present
        receipt = entry["receipt"]
        root = os.stat(receipt["root"])
        path = Path(receipt["path"])
        found = os.stat(path) if path.exists() else None
        receipt.update(version=1, root_identity=[root.st_dev, root.st_ino],
                       identity=[found.st_dev, found.st_ino] if found else [root.st_dev, receipt["identity"][-1]])
        if found:
            (path / cleanup.sweep.ROUND_MARKER).write_text(json.dumps(receipt, sort_keys=True))
    registry.save(old)
    return old


def test_schema_1_record_keeps_loading_on_its_pair(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    before = as_schema_1(registry, record)
    current = registry.load(record["id"])
    assert current["schema"] == cleanup.LEGACY_SCHEMA and current["common_identity"] == before["common_identity"]
    assert current["rounds"][0]["receipt"]["version"] == 1
    with pytest.raises(cleanup.sweep.ConfigError, match="nothing to reconcile"):
        registry.reconcile_plan(record["id"])
    # Work recorded into it from now on binds the new identity.
    task = task_tree(registry, root)
    registry.track_worktree(current, task, "git")
    assert registry.load(record["id"])["worktrees"][0]["identity"] == cleanup.sweep.stable_identity(str(task))
    assert registry.round_outcome(current["rounds"][0])["action"] == "eligible"
    assert Path(receipt["path"]).is_dir()


def test_renumbered_schema_1_record_names_the_device_and_points_to_reconcile(session, monkeypatch):
    registry, record, _ = session
    as_schema_1(registry, record)
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError) as refused:
        registry.load(record["id"])
    assert "device (stored " in str(refused.value) and "schema (" not in str(refused.value)
    assert f"only the device number differs, which a reboot or remount can renumber: " \
           f"preview `session_cleanup.py reconcile {record['id']}`" in str(refused.value)


def test_apply_round_leaves_incomplete_a_reconciled_round_whose_path_reappeared(device_session, monkeypatch):
    registry, record, root = device_session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    away = root / "unmounted-round"
    Path(receipt["path"]).rename(away)
    original = cleanup.sweep._identity

    def common_renumbered(path):
        device, number = original(path)
        return (device + 1, number) if path == str(registry.common) else (device, number)
    monkeypatch.setattr(cleanup.sweep, "_identity", common_renumbered)
    registry.reconcile(record["id"], registry.reconcile_plan(record["id"])[1]["approval_token"])
    away.rename(receipt["path"])
    result = apply_round(registry, registry.load(record["id"]), receipt)
    assert result["paths"][0]["action"] == "kept" and not result["complete"]
    assert registry.load(record["id"])["complete"] is False
    assert Path(receipt["path"]).is_dir()


def test_schema_1_record_is_not_accepted_on_inode_and_path_alone(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    as_schema_1(registry, record)
    renumber(monkeypatch)
    with pytest.raises(cleanup.sweep.ConfigError, match="still present: " + receipt["path"]):
        registry.reconcile_plan(record["id"])
    renumber(monkeypatch, inode=1)
    with pytest.raises(cleanup.sweep.ConfigError, match="other bound fields differ: .*inode"):
        registry.reconcile_plan(record["id"])


def test_renumbered_schema_1_record_reconciles_to_the_new_shape(session, monkeypatch):
    registry, record, _ = session
    receipt = vanished_round(registry, record)
    as_schema_1(registry, record)
    renumber(monkeypatch)
    plan = registry.reconcile_plan(record["id"])[1]
    assert plan["rounds_marked_removed"] == [receipt["id"]]
    assert plan["schema"] == {"stored": cleanup.LEGACY_SCHEMA, "current": cleanup.SCHEMA}
    registry.reconcile(record["id"], plan["approval_token"])
    current = registry.load(record["id"])
    assert current["schema"] == cleanup.SCHEMA and current["complete"]
    assert current["reconciled"][0]["schema"] == plan["schema"]
    assert current["common_identity"] == cleanup.sweep.stable_identity(str(registry.common))


def test_reconcile_names_a_shape_broken_record_instead_of_crashing(session):
    registry, record, _ = session
    broken = stored(registry, record)
    broken["schema"] = 0
    del broken["rounds"]
    registry.save(broken)
    with pytest.raises(cleanup.sweep.ConfigError, match=r"other bound fields differ: schema \(stored 0"):
        registry.reconcile_plan(record["id"])


def test_reconciled_round_whose_path_reappears_is_kept_not_removed(device_session, monkeypatch):
    """The repository's volume renumbered while a separate scratch volume was unmounted.

    The scratch volume comes back intact on its own unchanged device, so the
    round's receipt matches again; reconcile already marked it removed.
    """
    registry, record, root = device_session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    away = root / "unmounted-round"
    Path(receipt["path"]).rename(away)
    original = cleanup.sweep._identity

    def common_renumbered(path):
        device, number = original(path)
        return (device + 1, number) if path == str(registry.common) else (device, number)
    monkeypatch.setattr(cleanup.sweep, "_identity", common_renumbered)
    registry.reconcile(record["id"], registry.reconcile_plan(record["id"])[1]["approval_token"])
    away.rename(receipt["path"])  # same inode, marker intact: its receipt matches again
    sentinel = Path(receipt["path"]) / "result.md"
    current = registry.load(record["id"])
    outcome = registry.preview_round(current, receipt["id"])["paths"][0]
    assert outcome["action"] == "kept" and "marked removed by reconcile" in outcome["reason"]
    report = root / "inventory-report.md"
    report.write_text("final report\n")
    registry.seal(current, {"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}]})
    result = apply(registry, current)
    assert not result["complete"] and result["paths"][0]["action"] == "kept"
    assert sentinel.read_text() == "terminal report\n"


# Default discard and evidence retirement (#1256, #1315).

def discard_round(registry, record, receipt):
    report = Path(receipt["path"]) / "result.md"
    report.write_text("terminal report\n")
    return registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [],
        "discard": [{"source": receipt["path"], "reason": "findings recorded on PR #1"}]})


def test_discard_is_the_normal_completion_path(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    sealed = discard_round(registry, record, receipt)
    assert sealed["retained"] == [] and sealed["bytes"] == {"retained": 0, "copied": 0}
    assert sealed["discarded"][0]["reason"] == "findings recorded on PR #1"
    assert not (registry.location(record["id"]) / "evidence").exists() or not any(
        (registry.location(record["id"]) / "evidence").iterdir())
    assert apply_round(registry, record, receipt)["complete"]
    assert not Path(receipt["path"]).exists()
    assert registry.load(record["id"])["complete"]


@pytest.mark.parametrize("bad", ["empty", "no-exception", "partial-exception", "blank-reason",
                                 "both", "extra-key", "missing-key", "non-string", "normalised-overlap"])
def test_seal_refuses_undeclared_retention_and_bare_discard(session, bad):
    registry, record, root = session
    receipt = allocate(registry, record)
    source = Path(receipt["path"]) / "report.md"
    source.write_text("report")
    item = {"source": str(source), "kind": "report", "requires": []}
    manifest = {"evidence_complete": True, "retain": [item]}
    expected = "exception"
    if bad == "empty":
        manifest["retain"] = []
        expected = "discard entry"
    elif bad == "partial-exception":
        item["exception"] = {"task": "t", "next_action": "n", "delete_when": " "}
    elif bad == "blank-reason":
        manifest["retain"] = []
        manifest["discard"] = [{"source": str(source), "reason": " "}]
        expected = "reason"
    elif bad == "both":
        item["exception"] = EXCEPTION
        manifest["discard"] = [{"source": str(source), "reason": "in the PR"}]
        expected = "both retained and discarded"
    elif bad == "normalised-overlap":
        item["exception"] = EXCEPTION
        manifest["discard"] = [{"source": str(source.parent) + "/./" + source.name + "/",
                                "reason": "in the PR"}]
        expected = "both retained and discarded"
    elif bad == "extra-key":
        item["exception"] = {**EXCEPTION, "owner": "x"}
    elif bad == "missing-key":
        item["exception"] = {k: v for k, v in EXCEPTION.items() if k != "task"}
    elif bad == "non-string":
        item["exception"] = {**EXCEPTION, "next_action": 1}
    with pytest.raises(cleanup.sweep.ConfigError, match=expected):
        registry.seal_round(record, receipt["id"], manifest)
    assert registry.load(record["id"])["rounds"][0].get("seal") is None


def test_seal_reports_retained_and_copied_bytes(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    one, two = Path(receipt["path"]) / "a", Path(receipt["path"]) / "b"
    one.write_bytes(b"x" * 10)
    two.write_bytes(b"x" * 10)  # same bytes: one copy
    sealed = registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(p), "kind": "report", "requires": [], "exception": EXCEPTION} for p in (one, two)]})
    assert sealed["bytes"] == {"retained": 20, "copied": 10}


def retired_inventory(registry, record, receipt, legacy=True):
    """A complete inventory whose round sealed the helper's two items."""
    seal(registry, record, receipt, scope=receipt["id"])
    if legacy:  # sealed before exceptions existed
        for item in record["rounds"][0]["seal"]["retained"]:
            item.pop("exception")
        registry.save(record)
    assert apply_round(registry, record, receipt)["complete"]
    return registry.load(record["id"])


def test_completed_evidence_retires_by_default_and_leaves_a_tombstone(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    _, plan = registry.retirement_plan(record["id"], [])
    assert {v["kind"] for v in plan["retire"]} == {"report", "asset"} and not plan["kept"]
    size = sum(v["size"] for v in plan["retire"])
    assert plan["bytes"] == {"present_before": size, "removed": size, "present_after": 0,
                             "net_change": -size}
    with pytest.raises(cleanup.sweep.ConfigError, match="approval"):
        registry.retire_evidence(record["id"], "wrong", [])
    result = registry.retire_evidence(record["id"], plan["approval_token"], [])
    assert result["evidence_summary"]["retired"] == {"items": 2, "bytes": size}
    after = registry.load(record["id"])
    for item in after["rounds"][0]["seal"]["retained"]:
        assert not Path(item["retained"]).exists()
        assert item["retired"]["approval"] == plan["approval_token"] and item["sha256"]
    assert registry.preview_round(after, receipt["id"])["evidence_summary"]["present"]["items"] == 0
    assert registry.retirement_plan(record["id"], [])[1]["retire"] == []


def test_missing_evidence_is_not_reported_as_retired(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    gone = record["rounds"][0]["seal"]["retained"][1]
    os.unlink(gone["retained"])  # outside the engine: no tombstone
    summary = registry.evidence_summary(record)
    assert summary["missing"]["items"] == 1 and summary["retired"]["items"] == 0
    _, plan = registry.retirement_plan(record["id"], [])
    assert [v["sha256"] for v in plan["missing"]] == [gone["sha256"]]
    assert gone["sha256"] not in {v["sha256"] for v in plan["retire"]}
    assert plan["evidence_summary"]["missing"]["items"] == 1
    with pytest.raises(cleanup.sweep.ConfigError, match="missing and has no retirement tombstone"):
        registry.preview_round(record, receipt["id"])


def test_retention_exception_and_legacy_source_stay_until_included(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    draft = Path(receipt["path"]) / "draft.md"
    draft.write_text("unique authored draft\n")
    report = Path(receipt["path"]) / "report.md"
    report.write_text("report\n")
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(draft), "kind": "source", "requires": [], "exception": EXCEPTION},
        {"source": str(report), "kind": "report", "requires": [], "exception": EXCEPTION}]})
    for item in record["rounds"][0]["seal"]["retained"]:
        item.pop("exception", None) if item["kind"] == "source" else None
    registry.save(record)
    assert apply_round(registry, record, receipt)["complete"]
    _, plan = registry.retirement_plan(record["id"], [])
    reasons = {v["kind"]: v["reason"] for v in plan["kept"]}
    assert plan["retire"] == [] and "only copy" in reasons["source"]
    assert reasons["report"] == "retention exception until: the task merges"
    with pytest.raises(cleanup.sweep.ConfigError, match="names no retained item"):
        registry.retirement_plan(record["id"], ["0" * 64])
    sha = next(v["sha256"] for v in plan["kept"] if v["kind"] == "report")
    _, plan = registry.retirement_plan(record["id"], [sha])
    assert [v["kind"] for v in plan["retire"]] == ["report"]
    registry.retire_evidence(record["id"], plan["approval_token"], [sha])
    kept = next(i for i in registry.load(record["id"])["rounds"][0]["seal"]["retained"]
                if i["kind"] == "source")
    assert Path(kept["retained"]).read_text() == "unique authored draft\n"


def test_an_unretired_round_keeps_its_evidence(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt, scope=receipt["id"])
    for item in record["rounds"][0]["seal"]["retained"]:
        item.pop("exception")
    registry.save(record)
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == [] and {v["reason"] for v in plan["kept"]} == {"its round is not retired"}


def test_an_incomplete_inventory_keeps_its_own_seal(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    for item in record["seal"]["retained"]:
        item.pop("exception")
    registry.save(record)
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == [] and {v["reason"] for v in plan["kept"]} == {
        "inventory is not complete; retire its paths first"}


def test_shared_bytes_stay_while_a_kept_item_needs_them(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    one, two = Path(receipt["path"]) / "a", Path(receipt["path"]) / "b"
    one.write_bytes(b"shared")
    two.write_bytes(b"shared")
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(p), "kind": "report", "requires": [], "exception": EXCEPTION} for p in (one, two)]})
    record["rounds"][0]["seal"]["retained"][1].pop("exception")  # the second is default discard
    registry.save(record)
    assert apply_round(registry, record, receipt)["complete"]
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == [] and plan["bytes"]["removed"] == 0
    assert sorted(v["reason"].split(":")[0] for v in plan["kept"]) == [
        "retention exception until", "shares retained bytes with a kept item"]


def test_retiring_one_inventory_leaves_another_copy_intact(session):
    registry, first, _ = session
    receipt = allocate(registry, first)
    first = retired_inventory(registry, first, receipt)
    second = registry.start()
    other = allocate(registry, second)
    second = retired_inventory(registry, second, other)
    shared = {i["sha256"] for i in first["rounds"][0]["seal"]["retained"]}
    assert shared == {i["sha256"] for i in second["rounds"][0]["seal"]["retained"]}
    _, plan = registry.retirement_plan(first["id"], [])
    registry.retire_evidence(first["id"], plan["approval_token"], [])
    registry.verify_seal(second, second["rounds"][0]["seal"])
    assert registry.evidence_summary(second)["present"]["items"] == 2


def test_active_user_blocks_evidence_retirement(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    monkeypatch.setattr(cleanup, "active_users", lambda paths, pids: [f"process 1 uses {paths[0]}"])
    _, plan = registry.retirement_plan(record["id"], [])
    with pytest.raises(cleanup.sweep.ConfigError, match="active user"):
        registry.retire_evidence(record["id"], plan["approval_token"], [])
    assert registry.evidence_summary(registry.load(record["id"]))["present"]["items"] == 2


def test_escaped_evidence_path_refuses(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    outside = root / "outside"
    outside.write_text("not registry data")
    record["rounds"][0]["seal"]["retained"][0]["retained"] = str(outside)
    registry.save(record)
    with pytest.raises(cleanup.sweep.ConfigError, match="escaped"):
        registry.retirement_plan(record["id"], [])
    assert outside.exists()


def test_interrupted_evidence_retirement_reads_retiring_and_resumes(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    _, plan = registry.retirement_plan(record["id"], [])

    def interrupted(path, *args, **kwargs):
        raise KeyboardInterrupt

    with monkeypatch.context() as patch:
        patch.setattr(cleanup.os, "unlink", interrupted)
        with pytest.raises(KeyboardInterrupt):
            registry.retire_evidence(record["id"], plan["approval_token"], [])
    current = registry.load(record["id"])
    assert registry.evidence_summary(current)["retiring"]["items"] == 2
    registry.preview_round(current, receipt["id"])  # present tombstoned bytes still verify
    _, resumed = registry.retirement_plan(record["id"], [])
    assert len(resumed["retire"]) == 2
    registry.retire_evidence(record["id"], resumed["approval_token"], [])
    assert registry.evidence_summary(registry.load(record["id"]))["retired"]["items"] == 2


def test_cli_retire_evidence_preview_then_apply(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import session_cleanup as c; "
            "c.active_users=lambda paths,pids: []; raise SystemExit(c.main(sys.argv[2:]))")
    base = [sys.executable, "-c", code, str(Path(cleanup.__file__).parent),
            "--config", str(registry.repo / "cleanup.yaml"), "retire-evidence", record["id"]]
    preview = subprocess.run(base, cwd=registry.repo, capture_output=True, text=True, timeout=30)
    assert preview.returncode == 0, preview.stderr
    token = json.loads(preview.stdout)["approval_token"]
    assert registry.evidence_summary(registry.load(record["id"]))["present"]["items"] == 2
    applied = subprocess.run(base + ["--approve", token], cwd=registry.repo,
                             capture_output=True, text=True, timeout=30)
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["evidence_summary"]["retired"]["items"] == 2


def test_a_tombstoned_item_whose_bytes_remain_is_still_hash_checked(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    item = record["rounds"][0]["seal"]["retained"][0]
    item["retired"] = {"approval": "interrupted"}
    registry.save(record)
    Path(item["retained"]).write_text("a replacement")
    with pytest.raises(cleanup.sweep.ConfigError, match="changed"):
        registry.preview_round(registry.load(record["id"]), receipt["id"])


def test_a_manifest_cannot_forge_a_tombstone(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    draft = Path(receipt["path"]) / "draft.md"
    draft.write_text("unique draft\n")
    sealed = registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(draft), "kind": "source", "requires": [], "exception": EXCEPTION,
         "retired": {"approval": "forged"}, "sha256": "0" * 64}]})
    assert set(sealed["retained"][0]) == {"source", "kind", "requires", "exception", "sha256",
                                          "size", "retained"}
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == [] and plan["kept"][0]["reason"] == "its round is not retired"


def test_a_refused_seal_copies_nothing(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    good, bad = Path(receipt["path"]) / "good", Path(receipt["path"]) / "bad"
    good.write_text("good")
    bad.write_text("bad")
    with pytest.raises(cleanup.sweep.ConfigError, match="exception"):
        registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
            {"source": str(good), "kind": "report", "requires": [], "exception": EXCEPTION},
            {"source": str(bad), "kind": "report", "requires": []}]})
    evidence = registry.location(record["id"]) / "evidence"
    assert not evidence.exists() or not any(evidence.iterdir())


def test_an_item_a_kept_item_requires_stays(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    report, capture = Path(receipt["path"]) / "report", Path(receipt["path"]) / "capture"
    report.write_text("report")
    capture.write_text("capture")
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [str(capture)], "exception": EXCEPTION},
        {"source": str(capture), "kind": "asset", "requires": [], "exception": EXCEPTION}]})
    assert apply_round(registry, record, receipt)["complete"]
    sha = next(i["sha256"] for i in record["rounds"][0]["seal"]["retained"] if i["kind"] == "asset")
    _, plan = registry.retirement_plan(record["id"], [sha])
    assert plan["retire"] == []
    assert {v["kind"]: v["reason"] for v in plan["kept"]}["asset"] == "required by a kept item"


def test_shared_bytes_are_counted_once(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    one, two = Path(receipt["path"]) / "a", Path(receipt["path"]) / "b"
    one.write_bytes(b"x" * 10)
    two.write_bytes(b"x" * 10)
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(p), "kind": "report", "requires": [], "exception": EXCEPTION} for p in (one, two)]})
    for item in record["rounds"][0]["seal"]["retained"]:
        item.pop("exception")
    registry.save(record)
    assert apply_round(registry, record, receipt)["complete"]
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["evidence_summary"]["present"] == {"items": 2, "bytes": 10}
    assert plan["bytes"] == {"present_before": 10, "removed": 10, "present_after": 0, "net_change": -10}
    after = registry.retire_evidence(record["id"], plan["approval_token"], [])
    assert after["evidence_summary"]["retired"] == {"items": 2, "bytes": 10}
    assert not any((registry.location(record["id"]) / "evidence").iterdir())


def test_summaries_on_list_and_preview(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    seal(registry, record, receipt)
    expected = registry.evidence_summary(record)
    assert expected["present"]["items"] == 2 and expected["exceptions"] == 2
    listed = next(i for i in registry.inventories() if i["id"] == record["id"])
    assert listed["evidence_summary"] == expected
    assert registry.preview(record)["evidence_summary"] == expected


def test_a_retired_item_is_not_listed_missing(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    _, plan = registry.retirement_plan(record["id"], [])
    registry.retire_evidence(record["id"], plan["approval_token"], [])
    _, again = registry.retirement_plan(record["id"], [])
    assert again["retire"] == again["kept"] == again["missing"] == []
    assert again["evidence_summary"]["missing"]["items"] == 0


def test_an_interrupted_included_retirement_resumes_without_include(session, monkeypatch):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt, legacy=False)
    shas = [i["sha256"] for i in record["rounds"][0]["seal"]["retained"]]
    _, plan = registry.retirement_plan(record["id"], shas)
    assert len(plan["retire"]) == 2

    def interrupted(path, *args, **kwargs):
        raise KeyboardInterrupt

    with monkeypatch.context() as patch:
        patch.setattr(cleanup.os, "unlink", interrupted)
        with pytest.raises(KeyboardInterrupt):
            registry.retire_evidence(record["id"], plan["approval_token"], shas)
    _, resumed = registry.retirement_plan(record["id"], [])
    assert len(resumed["retire"]) == 2 and resumed["kept"] == []


def test_changed_retained_bytes_are_kept(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    target = Path(record["rounds"][0]["seal"]["retained"][0]["retained"])
    with open(target, "ab") as stream:
        stream.write(b"grown")
    _, plan = registry.retirement_plan(record["id"], [])
    assert any(v["reason"].startswith("retained bytes changed") for v in plan["kept"])
    assert target.exists()


def test_an_interrupted_round_retirement_refuses_evidence_retirement(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    record["rounds"][0]["status"] = "removing"
    record["rounds"][0]["approval"] = "persisted"
    registry.save(record)
    with pytest.raises(cleanup.sweep.ConfigError, match="interrupted"):
        registry.retirement_plan(record["id"], [])


def test_an_empty_plan_writes_nothing(session):
    registry, record, _ = session
    before = (registry.location(record["id"]) / "session.json").read_bytes()
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == []
    result = registry.retire_evidence(record["id"], plan["approval_token"], [])
    assert result["applied"]
    assert (registry.location(record["id"]) / "session.json").read_bytes() == before
    assert not (registry.location(record["id"]) / "evidence").exists()


def test_cli_include_reaches_the_plan(session):
    registry, record, root = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt, legacy=False)
    sha = record["rounds"][0]["seal"]["retained"][0]["sha256"]  # the report; its capture stays required
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import session_cleanup as c; "
            "c.active_users=lambda paths,pids: []; raise SystemExit(c.main(sys.argv[2:]))")
    base = [sys.executable, "-c", code, str(Path(cleanup.__file__).parent),
            "--config", str(registry.repo / "cleanup.yaml"), "retire-evidence", record["id"]]
    plain = json.loads(subprocess.run(base, cwd=registry.repo, capture_output=True, text=True,
                                      timeout=30, check=True).stdout)
    included = json.loads(subprocess.run(base + ["--include", sha], cwd=registry.repo,
                                         capture_output=True, text=True, timeout=30, check=True).stdout)
    assert plain["retire"] == [] and [v["sha256"] for v in included["retire"]] == [sha]


def test_an_unreadable_later_source_copies_nothing(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    good = Path(receipt["path"]) / "good"
    good.write_text("good")
    absent = Path(receipt["path"]) / "absent"
    with pytest.raises((OSError, cleanup.sweep.ConfigError)):
        registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
            {"source": str(p), "kind": "report", "requires": [], "exception": EXCEPTION}
            for p in (good, absent)]})
    evidence = registry.location(record["id"]) / "evidence"
    assert not evidence.exists() or not any(evidence.iterdir())


def test_a_shared_file_under_a_tombstone_is_counted_once(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    one, two = Path(receipt["path"]) / "a", Path(receipt["path"]) / "b"
    one.write_bytes(b"y" * 7)
    two.write_bytes(b"y" * 7)
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(p), "kind": "report", "requires": [], "exception": EXCEPTION} for p in (one, two)]})
    record["rounds"][0]["seal"]["retained"][0]["retired"] = {"approval": "interrupted"}
    registry.save(record)
    summary = registry.evidence_summary(record)
    assert summary["present"] == {"items": 1, "bytes": 7}
    assert summary["retiring"] == {"items": 1, "bytes": 0}


def test_a_removed_round_whose_path_reappeared_keeps_its_evidence(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    record = retired_inventory(registry, record, receipt)
    Path(receipt["path"]).mkdir()
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == [] and {v["reason"] for v in plan["kept"]} == {"its round is not retired"}


def test_a_two_hop_requires_chain_is_kept_whatever_its_order(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    leaf, middle, root = (Path(receipt["path"]) / n for n in ("leaf", "middle", "root"))
    for path in (leaf, middle, root):
        path.write_text(path.name)
    registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(leaf), "kind": "report", "requires": [], "exception": EXCEPTION},
        {"source": str(middle), "kind": "report", "requires": [str(leaf)], "exception": EXCEPTION},
        {"source": str(root), "kind": "report", "requires": [str(middle)], "exception": EXCEPTION}]})
    for item in record["rounds"][0]["seal"]["retained"]:
        if not item["source"].endswith("/root"):
            item.pop("exception")  # leaf and middle are default discard; root keeps them
    registry.save(record)
    assert apply_round(registry, record, receipt)["complete"]
    _, plan = registry.retirement_plan(record["id"], [])
    assert plan["retire"] == []
    assert sorted(v["reason"] for v in plan["kept"]) == [
        "required by a kept item", "required by a kept item", "retention exception until: the task merges"]


def test_requires_and_replaced_by_compare_after_normalisation(session):
    registry, record, _ = session
    receipt = allocate(registry, record)
    report, capture, log = (Path(receipt["path"]) / n for n in ("report", "capture", "log"))
    for path in (report, capture, log):
        path.write_text(path.name)
    odd = lambda path: str(path.parent) + "/./" + path.name  # noqa: E731
    sealed = registry.seal_round(record, receipt["id"], {"evidence_complete": True, "retain": [
        {"source": str(report), "kind": "report", "requires": [odd(capture)], "exception": EXCEPTION},
        {"source": str(capture), "kind": "asset", "requires": [], "exception": EXCEPTION}],
        "retire": [{"source": str(log), "reason": "report replaces it", "replaced_by": [odd(report)]}]})
    assert sealed["retained"][0]["requires"] == [str(capture)]
