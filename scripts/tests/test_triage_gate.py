from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.canonical import digest, loads_exact  # noqa: E402
from triage.gate import acquire, owner_status, validate_record  # noqa: E402
from triage.model import Paths, Settings, TriageError, repository_identity  # noqa: E402
from triage.recovery import gate_only_plan, prepare_gate_only, resume_gate_only  # noqa: E402
from triage.storage import ArtifactStore  # noqa: E402


def settings(tmp_path: Path) -> Settings:
    paths = Paths(tmp_path, tmp_path / "inbox", tmp_path / "archive", tmp_path / "scripts", "state/triage/state_{mode}.json", "state/triage/gate_{mode}.lock", "state/triage/recovery_{mode}_{gate_digest}.json", "state/triage/frozen_{mode}_{date}_{session}.json", tmp_path / "reports", "reports/triage_{mode}_{date}_{session}.md")
    return Settings({}, "0" * 64, paths, "main", "chore/triage-{date}", "default", tmp_path / "draft", tmp_path / "finalize", "engine-backed", "subject", {}, {})


def test_gate_is_complete_at_first_publication_and_exclusive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    store = ArtifactStore(settings(tmp_path), "test")
    first = acquire(store, repository_identity={"root": str(tmp_path)}, config_fingerprint="0" * 64, run_identity=None)
    assert first.verify()
    assert not list(store.gate_path.parent.glob(f".{store.gate_path.name}.*.tmp"))
    with pytest.raises(TriageError, match="already held"):
        acquire(store, repository_identity={"root": str(tmp_path)}, config_fingerprint="0" * 64, run_identity=None)
    first.release()
    assert not store.gate_path.exists()


def test_release_refuses_replaced_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    store = ArtifactStore(settings(tmp_path), "live")
    lease = acquire(store, repository_identity={"root": str(tmp_path)}, config_fingerprint="0" * 64, run_identity=None)
    store.gate_path.write_bytes(b"foreign")
    with pytest.raises(TriageError, match="changed"):
        lease.release()


@pytest.mark.parametrize(("field", "value"), [("owner_token", 17), ("schema_version", True)])
def test_gate_record_rejects_values_that_only_compare_or_stringify_like_declared_types(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    store = ArtifactStore(settings(tmp_path), "test")
    lease = acquire(store, repository_identity={"root": str(tmp_path)}, config_fingerprint="0" * 64, run_identity=None)
    record = loads_exact(store.gate_path.read_bytes())
    if field == "schema_version":
        record[field] = value
    else:
        record[field] = value
        record["gate_claim_core"][field] = value
        record["gate_claim_core_digest"] = digest(record["gate_claim_core"])
    with pytest.raises(TriageError, match="wrong shape|identity"):
        validate_record(record)
    lease.release()


def test_gate_acquire_refuses_unavailable_process_identity_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    store = ArtifactStore(settings(tmp_path), "test")
    unrelated = tmp_path / "unrelated"
    unrelated.write_bytes(b"preserve")
    monkeypatch.setattr("triage.gate._process_start", lambda _pid: None)
    with pytest.raises(TriageError, match="start identity is unavailable"):
        acquire(store, repository_identity={"root": str(tmp_path)}, config_fingerprint="0" * 64, run_identity=None)
    assert not store.gate_path.exists()
    assert not list(store.gate_path.parent.glob(f".{store.gate_path.name}.*.tmp"))
    assert unrelated.read_bytes() == b"preserve"


@pytest.mark.parametrize("observed_start", [None, "ps-lstart:different-owner"])
def test_owner_status_is_uncertain_when_live_process_start_cannot_be_matched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    observed_start: str | None,
) -> None:
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "sandbox"))
    store = ArtifactStore(settings(tmp_path), "test")
    lease = acquire(
        store,
        repository_identity={"root": str(tmp_path)},
        config_fingerprint="0" * 64,
        run_identity=None,
    )
    monkeypatch.setattr("triage.gate._process_start", lambda _pid: observed_start)
    assert owner_status(lease.record) == "uncertain"
    lease.release()


@pytest.mark.parametrize("cutpoint", ["before-link", "after-link"])
def test_owned_process_kill_at_gate_publication_cutpoint_retains_declared_inode_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cutpoint: str
) -> None:
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    subprocess.run(["git", "-C", str(tmp_path), "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", "https://github.com/example/gate.git"], check=True)
    marker = tmp_path / "cutpoint"
    child = r'''
import os, sys, time
from pathlib import Path
from triage.gate import acquire
from triage.model import Paths, Settings
from triage.storage import ArtifactStore
root=Path(sys.argv[1]); marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
paths=Paths(root,root/'inbox',root/'archive',root/'scripts','state/triage/state_{mode}.json','state/triage/gate_{mode}.lock','state/triage/recovery_{mode}_{gate_digest}.json','state/triage/frozen_{mode}_{date}_{session}.json',root/'reports','reports/triage_{mode}_{date}_{session}.md')
settings=Settings({},'0'*64,paths,'main','chore/triage-{date}','default',root/'draft',root/'finalize','engine-backed','subject',{}, {})
store=ArtifactStore(settings,'test'); original=os.link
def controlled(source,destination,**kwargs):
    if cutpoint=='before-link': marker.write_text('ready'); time.sleep(300)
    result=original(source,destination,**kwargs)
    if cutpoint=='after-link': marker.write_text('ready'); time.sleep(300)
    return result
os.link=controlled
acquire(store,repository_identity={'root':str(root),'remote':'https://github.com/example/gate.git'},config_fingerprint='0'*64,run_identity=None)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib")
    process = subprocess.Popen([sys.executable, "-c", child, str(tmp_path), str(marker), cutpoint], env=environment)
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    gate = state_root / "triage/gate_test.lock"
    temporaries = list(gate.parent.glob(f".{gate.name}.*.tmp"))
    assert len(temporaries) == 1
    temporary_raw = temporaries[0].read_bytes()
    record = loads_exact(temporary_raw)
    assert record["kind"] == "triage-gate"
    assert temporaries[0].name == f".{gate.name}.{record['owner_token']}.tmp"
    configured = settings(tmp_path)
    store = ArtifactStore(configured, "test")
    if cutpoint == "before-link":
        assert not gate.exists()
        next_lease = acquire(store, repository_identity=repository_identity(configured), config_fingerprint="0" * 64, run_identity=None)
        next_lease.release()
        assert not temporaries[0].exists()
    else:
        assert gate.read_bytes() == temporary_raw
        assert (gate.stat().st_dev, gate.stat().st_ino) == (temporaries[0].stat().st_dev, temporaries[0].stat().st_ino)
        plan = gate_only_plan(store, configured)
        core_digest = plan["prepared_core_digest"]
        approval = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
        prepared = prepare_gate_only(store, configured, approval=approval, operator="operator")
        resume_gate_only(store, configured, prepared)
        assert not gate.exists() and not temporaries[0].exists()
