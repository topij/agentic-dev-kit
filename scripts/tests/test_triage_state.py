from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.canonical import dumps, loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402
from triage.inbox import parse  # noqa: E402
from triage.model import TriageError  # noqa: E402
from triage.providers import FakeTracker  # noqa: E402
from triage.storage import (  # noqa: E402
    atomic_replace,
    exclusive_create,
    observe,
    preflight_artifacts,
    quarantine_inode,
)


def _triage_repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    source_config = REPO_ROOT / "config/dev-model.yaml"
    shutil.copy2(source_config, repo / "config/dev-model.yaml")
    config = repo / "config/dev-model.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "  engines: scripts/devkit\n", "  engines: scripts\n"
        ),
        encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n"
        b"- **Handled.** details. **Filed 2026-01-02 as #17.**\n"
        b"- **Open.** details.\n"
    )
    (repo / "docs/kit-friction-log-archive.md").write_bytes(b"# Archive\n")
    (repo / "scripts").mkdir()
    (repo / "scripts/triage_friction_log.py").write_text("# engine\n", encoding="utf-8")
    (repo / "scripts/finalize_triage.py").write_text("# engine\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "fixture"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/example/project.git"], check=True)
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
    return repo


def test_saved_index_that_omits_historical_entry_is_refused_before_tracker_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _triage_repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    candidates = parse((repo / "docs/kit-friction-log.md").read_bytes())
    proposals = [
        {
            "candidate_id": candidate.candidate_id,
            "source_block_digest": candidate.digest,
            "title": candidate.title,
            "body_without_marker": "Observed details.",
            "project": "topij/agentic-dev-kit",
            "labels": ["bug"],
        }
        for candidate in candidates
    ]
    drafted = run("new", context="interactive", request={"proposals": proposals}, start=repo)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    state = loads_exact(state_path.read_bytes())
    old_open = {
        **state["frozen_snapshot"]["content"]["candidate_index"][1],
        "candidate_id": "TRI-01",
    }
    state["frozen_snapshot"]["content"]["candidate_index"] = [old_open]
    frozen_path = Path(drafted["frozen_snapshot"])
    frozen = loads_exact(frozen_path.read_bytes())
    frozen["frozen_snapshot"] = state["frozen_snapshot"]
    frozen_path.write_bytes(dumps(frozen))
    retained = dumps(state)
    state_path.write_bytes(retained)
    tracker = FakeTracker()
    result = run("resume", context="interactive", request={}, start=repo, tracker=tracker)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "frozen snapshot candidate index mismatch"
    assert tracker.calls == []
    assert state_path.read_bytes() == retained


def test_preflight_rejects_tracked_and_control_artifact_targets(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    tracked = repo / "tracked-report.md"
    tracked.write_text("tracked", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked-report.md"], check=True)
    with pytest.raises(TriageError, match="tracked by the repository"):
        preflight_artifacts([tracked], controls=[], repo=repo)

    control = repo / "config.yaml"
    control.write_text("control", encoding="utf-8")
    with pytest.raises(TriageError, match="workflow control input"):
        preflight_artifacts([control], controls=[control], repo=repo)


def test_exclusive_create_publishes_only_a_complete_fsynced_inode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "state.json"
    raw = b"x" * 32768
    original = os.link
    observations: list[tuple[bool, bytes]] = []

    def inspect_link(source, destination, **kwargs):
        parent_fd = kwargs["src_dir_fd"]
        with open(source, "rb", opener=lambda name, flags: os.open(name, flags, dir_fd=parent_fd)) as stream:
            staged = stream.read()
        observations.append((target.exists(), staged))
        result = original(source, destination, **kwargs)
        observations.append((target.exists(), target.read_bytes()))
        return result

    monkeypatch.setattr(os, "link", inspect_link)
    exclusive_create(target, raw)
    assert observations == [(False, raw), (True, raw)]


def test_exclusive_create_never_replaces_existing_target(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    exclusive_create(target, b"first")
    with pytest.raises(FileExistsError):
        exclusive_create(target, b"second")
    assert target.read_bytes() == b"first"


@pytest.mark.parametrize("artifact_name", ["state.json", "frozen.json", "report.md"])
@pytest.mark.parametrize("cutpoint", ["before-publication", "after-publication"])
def test_owned_process_loss_around_non_gate_publication_restarts_safely(
    tmp_path: Path, artifact_name: str, cutpoint: str
) -> None:
    target = tmp_path / artifact_name
    marker = tmp_path / f"{artifact_name}.{cutpoint}.marker"
    raw = b"complete durable artifact\n"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib")
    child = r'''
import os,sys,time
from pathlib import Path
import triage.storage as storage
target=Path(sys.argv[1]); marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
original=os.link
def controlled(source,destination,**kwargs):
 if cutpoint=='before-publication': marker.write_text(cutpoint); time.sleep(300)
 result=original(source,destination,**kwargs)
 if cutpoint=='after-publication': marker.write_text(cutpoint); time.sleep(300)
 return result
os.link=controlled
storage.exclusive_create(target,bytes.fromhex(sys.argv[4]))
'''
    process = subprocess.Popen(
        [sys.executable, "-c", child, str(target), str(marker), cutpoint, raw.hex()],
        env=environment,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    if cutpoint == "before-publication":
        assert not target.exists()
    else:
        assert target.read_bytes() == raw
    restart = r'''
import sys
from pathlib import Path
from triage.storage import exclusive_create,observe
target=Path(sys.argv[1]); raw=bytes.fromhex(sys.argv[2])
try:
 exclusive_create(target,raw)
except FileExistsError:
 pass
print(observe(target)[1].hex(),flush=True)
'''
    restarted = subprocess.run(
        [sys.executable, "-c", restart, str(target), raw.hex()],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert bytes.fromhex(restarted.stdout.strip()) == raw


def test_expected_digest_is_rechecked_after_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")
    from triage.canonical import digest_bytes

    original_replace = os.replace

    def should_not_replace(*args, **kwargs):
        raise AssertionError("replacement reached despite digest mismatch")

    monkeypatch.setattr(os, "replace", should_not_replace)
    target.write_bytes(b"concurrent")
    with pytest.raises(TriageError, match="concurrent"):
        atomic_replace(target, b"new", expected_digest=digest_bytes(b"old"))
    monkeypatch.setattr(os, "replace", original_replace)


def test_atomic_replace_cleanup_uses_held_parent_after_parent_retarget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = tmp_path / "artifacts"
    parent.mkdir()
    target = parent / "state.json"
    target.write_bytes(b"old")
    moved = tmp_path / "original-parent"
    from triage import storage
    from triage.canonical import digest_bytes

    original_observe = storage._observe_at

    def retarget_after_capture(parent_descriptor, name, path):
        result = original_observe(parent_descriptor, name, path)
        parent.rename(moved)
        parent.mkdir()
        temporary = next(moved.glob(".state.json.*.tmp"))
        (parent / temporary.name).write_bytes(b"unrelated replacement-directory file")
        return result

    monkeypatch.setattr(storage, "_observe_at", retarget_after_capture)
    with pytest.raises(TriageError, match="ancestor chain retargeted"):
        atomic_replace(target, b"new", expected_digest=digest_bytes(b"old"))
    assert (moved / "state.json").read_bytes() == b"old"
    replacement_files = list(parent.iterdir())
    assert len(replacement_files) == 1
    assert replacement_files[0].read_bytes() == b"unrelated replacement-directory file"


def test_atomic_replace_revalidates_the_complete_ancestor_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ancestor = tmp_path / "outer"
    parent = ancestor / "artifacts"
    parent.mkdir(parents=True)
    target = parent / "state.json"
    target.write_bytes(b"old")
    moved = tmp_path / "original-outer"
    from triage import storage
    from triage.canonical import digest_bytes

    original_revalidate = storage._revalidate_parent_chain
    changed = False

    def retarget_ancestor(descriptors, identities, components):
        nonlocal changed
        if not changed:
            changed = True
            ancestor.rename(moved)
            parent.mkdir(parents=True)
            (parent / "state.json").write_bytes(b"unrelated")
        return original_revalidate(descriptors, identities, components)

    monkeypatch.setattr(storage, "_revalidate_parent_chain", retarget_ancestor)
    with pytest.raises(TriageError, match="ancestor chain retargeted"):
        atomic_replace(target, b"new", expected_digest=digest_bytes(b"old"))
    assert (moved / "artifacts/state.json").read_bytes() == b"old"
    assert (parent / "state.json").read_bytes() == b"unrelated"


def test_quarantine_refuses_to_unlink_a_replaced_source_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "gate.lock"
    target = tmp_path / "gate.lock.quarantine"
    approved_raw = b"approved gate"
    source.write_bytes(approved_raw)
    approved, _ = observe(source, allow_links=True)
    from triage import storage

    original_observe_at = storage._observe_at
    swapped = False

    def swap_after_target_readback(parent_descriptor, name, display_path, **kwargs):
        nonlocal swapped
        result = original_observe_at(parent_descriptor, name, display_path, **kwargs)
        if display_path == target and result[1] == approved_raw and not swapped:
            swapped = True
            source.unlink()
            source.write_bytes(b"unrelated replacement")
        return result

    monkeypatch.setattr(storage, "_observe_at", swap_after_target_readback)
    with pytest.raises(TriageError, match="quarantine publication identity mismatch"):
        quarantine_inode(source, target, approved, approved_raw)
    assert source.read_bytes() == b"unrelated replacement"
    assert target.read_bytes() == approved_raw
