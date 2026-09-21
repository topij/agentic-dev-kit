from __future__ import annotations

import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.canonical import digest, dumps, loads_exact  # noqa: E402
from triage.model import Paths, Settings, TriageError, state_base  # noqa: E402
from triage.recovery import (  # noqa: E402
    capture_state_present,
    gate_only_plan,
    prepare_gate_only,
    prepare_state_action,
    resume_gate_only,
    resume_state_action,
    state_action_plan,
)
from triage.storage import ArtifactStore, observe  # noqa: E402


def settings(tmp_path: Path) -> Settings:
    if not (tmp_path / ".git").exists():
        subprocess.run(["git", "-C", str(tmp_path), "init", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", "https://github.com/example/recovery.git"], check=True)
    paths = Paths(tmp_path, tmp_path / "inbox", tmp_path / "archive", tmp_path / "scripts", "state/triage/state_{mode}.json", "state/triage/gate_{mode}.lock", "state/triage/recovery_{mode}_{gate_digest}.json", "state/triage/frozen_{mode}_{date}_{session}.json", tmp_path / "reports", "reports/triage_{mode}_{date}_{session}.md")
    return Settings({}, "0" * 64, paths, "main", "chore/triage-{date}", "default", tmp_path / "draft", tmp_path / "finalize", "engine-backed", "subject", {}, {})


CHILD = r'''
import os, sys, time
from pathlib import Path
from triage.gate import acquire
from triage.model import Paths, Settings
from triage.storage import ArtifactStore, exclusive_create
root=Path(sys.argv[1]); mode=sys.argv[2]; artifact=sys.argv[3]; alias=sys.argv[4]=='alias'
paths=Paths(root,root/'inbox',root/'archive',root/'scripts','state/triage/state_{mode}.json','state/triage/gate_{mode}.lock','state/triage/recovery_{mode}_{gate_digest}.json','state/triage/frozen_{mode}_{date}_{session}.json',root/'reports','reports/triage_{mode}_{date}_{session}.md')
settings=Settings({},'0'*64,paths,'main','chore/triage-{date}','default',root/'draft',root/'finalize','engine-backed','subject',{}, {})
store=ArtifactStore(settings,mode)
lease=acquire(store,repository_identity={'root':str(root),'remote':'https://github.com/example/recovery.git'},config_fingerprint='0'*64,run_identity=None)
if artifact != 'absent': exclusive_create(store.state_path, bytes.fromhex(artifact))
if alias: os.link(store.gate_path, store.gate_path.parent / ('.'+store.gate_path.name+'.'+lease.owner_token+'.tmp'))
print('ready',flush=True)
time.sleep(300)
'''


def dead_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, mode: str, artifact: bytes | None, alias: bool = False) -> tuple[ArtifactStore, subprocess.Popen[str]]:
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    store = ArtifactStore(settings(tmp_path), mode)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib")
    process = subprocess.Popen(
        [sys.executable, "-c", CHILD, str(tmp_path), mode, artifact.hex() if artifact is not None else "absent", "alias" if alias else "plain"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    return store, process


def approval(core_digest: str) -> dict[str, str]:
    return {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}


def unknown_phase_state(tmp_path: Path, *, attempts: list | None = None) -> bytes:
    identity = {
        "repository_identity": {"root": str(tmp_path), "remote": "https://github.com/example/recovery.git"},
        "friction_log": "inbox",
        "protected_branch_head": "1" * 40,
        "mode": "test",
        "session": "recovery-session",
        "config_fingerprint": "0" * 64,
    }
    binding = {"gate_path": "gate", "owner_token": "owner", "owner_run_identity": None, "gate_claim_core_digest": "2" * 64}
    state = state_base(identity, binding, {}, "3" * 64, {}, "engine-backed")
    state["phase"] = "unknown"
    state["attempts"] = attempts or []
    return dumps(state)


def test_gate_only_recovery_preserves_same_inode_names_and_finishes_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = dead_owner(tmp_path, monkeypatch, mode="live", artifact=None, alias=True)
    plan = gate_only_plan(store, settings(tmp_path))
    envelope = prepare_gate_only(store, settings(tmp_path), approval=approval(plan["prepared_core_digest"]), operator="operator")
    receipt = resume_gate_only(store, settings(tmp_path), envelope)
    assert receipt["kind"] == "gate-only-operator-held"
    assert not store.gate_path.exists()
    assert len(receipt["quarantine_observations"]) == 2
    assert {item["links"] for item in receipt["quarantine_observations"]} == {2}
    assert observe(store.state_path)[1] == dumps(receipt)


@pytest.mark.parametrize("mutation", ["malformed", "digest-mismatch", "foreign"])
def test_gate_only_prepared_bundle_refuses_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    store, _ = dead_owner(tmp_path, monkeypatch, mode="live", artifact=None)
    configured = settings(tmp_path)
    plan = gate_only_plan(store, configured)
    envelope = prepare_gate_only(
        store,
        configured,
        approval=approval(plan["prepared_core_digest"]),
        operator="operator",
    )
    candidate: object = deepcopy(envelope)
    if mutation == "malformed":
        candidate = []
    elif mutation == "digest-mismatch":
        candidate["intended_intent"]["old_gate_digest"] = "f" * 64
    else:
        foreign = {"root": "/foreign", "remote": "https://example.invalid/foreign"}
        candidate["prepared_core"]["repository_identity"] = foreign
        candidate["prepared_core_digest"] = digest(candidate["prepared_core"])
        candidate["intended_intent"]["repository_identity"] = foreign
        candidate["intended_intent"]["prepared_core_digest"] = candidate["prepared_core_digest"]
        candidate["intended_intent_digest"] = digest(candidate["intended_intent"])
    gate_before = store.gate_path.read_bytes()
    bundle_before = store.recovery_path(plan["prepared_core"]["old_gate_digest"]).read_bytes()
    with pytest.raises(TriageError):
        resume_gate_only(store, configured, candidate)
    assert store.gate_path.read_bytes() == gate_before
    assert store.recovery_path(plan["prepared_core"]["old_gate_digest"]).read_bytes() == bundle_before
    assert not store.state_path.exists()


def test_invalid_state_recovery_requires_action_bound_approval_and_restarts_by_cutpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = unknown_phase_state(tmp_path)
    store, _ = dead_owner(tmp_path, monkeypatch, mode="test", artifact=invalid)
    capture = capture_state_present(store, settings(tmp_path))
    plan = state_action_plan(store, settings(tmp_path), capture)
    prepared = prepare_state_action(store, settings(tmp_path), capture, approval=approval(plan["action_core_digest"]), operator="operator")
    receipt = resume_state_action(store, prepared)
    assert receipt["kind"] == "test-recovered-safe-to-restart"
    assert observe(Path(receipt["quarantine_path"]))[1] == invalid
    assert observe(store.state_path)[1] == dumps(receipt)
    assert resume_state_action(store, prepared) == receipt


def test_state_with_unproven_attempts_becomes_terminal_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = unknown_phase_state(tmp_path, attempts=[{"status": "attempting"}])
    store, _ = dead_owner(tmp_path, monkeypatch, mode="test", artifact=invalid)
    capture = capture_state_present(store, settings(tmp_path))
    plan = state_action_plan(store, settings(tmp_path), capture)
    assert plan["held"]["kind"] == "state-present-held"


def test_malformed_base_with_empty_evidence_is_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    malformed = dumps({"kind": "unknown", "attempts": [], "verified_tracker_identifiers": [], "repository_evidence": [], "pull_request_evidence": []})
    store, _ = dead_owner(tmp_path, monkeypatch, mode="test", artifact=malformed)
    capture = capture_state_present(store, settings(tmp_path))
    assert state_action_plan(store, settings(tmp_path), capture)["held"]["kind"] == "state-present-held"


def test_gate_capture_rejects_unaccounted_hardlink_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = dead_owner(tmp_path, monkeypatch, mode="live", artifact=None)
    os.link(store.gate_path, store.gate_path.parent / "unexpected-alias")
    with pytest.raises(Exception, match="unexpected same-inode"):
        gate_only_plan(store, settings(tmp_path))


def test_gate_capture_rejects_top_level_owner_mismatch_before_death_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = dead_owner(tmp_path, monkeypatch, mode="live", artifact=None)
    record = loads_exact(store.gate_path.read_bytes())
    record["process_id"] = 99999999
    store.gate_path.write_bytes(dumps(record))
    with pytest.raises(Exception, match="core binding mismatch"):
        gate_only_plan(store, settings(tmp_path))


def test_gate_capture_rejects_foreign_repository_even_with_self_consistent_core(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = dead_owner(tmp_path, monkeypatch, mode="live", artifact=None)
    record = loads_exact(store.gate_path.read_bytes())
    record["gate_claim_core"]["repository_identity"] = {"root": "/foreign", "remote": "https://example.invalid/foreign"}
    record["repository_identity"] = record["gate_claim_core"]["repository_identity"]
    record["gate_claim_core_digest"] = digest(record["gate_claim_core"])
    store.gate_path.write_bytes(dumps(record))
    with pytest.raises(Exception, match="repository identity is foreign"):
        gate_only_plan(store, settings(tmp_path))
