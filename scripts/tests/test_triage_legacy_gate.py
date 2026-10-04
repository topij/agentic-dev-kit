"""Historical captures never become leases or live approval authority."""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from test_triage_engine import ENGINE_DIR, git, repository
from triage import engine
from triage.approval import ApprovalContext
from triage.canonical import digest as canonical_digest
from triage.canonical import digest_bytes, dumps, loads_exact
from triage.model import load_settings
from triage.storage import ArtifactStore


def historical_fixture(tmp_path, monkeypatch, *, active=False):
    root = repository(tmp_path)
    # Exercise the installed CLI and read-only remote provenance with a real local
    # bare remote. No network, operator repository or tracker is involved.
    for name in ("triage_friction_log.py", "finalize_triage.py"):
        shutil.copy2(ENGINE_DIR / name, root / "scripts" / name)
    shutil.copytree(ENGINE_DIR / "lib", root / "scripts/lib", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    git(root, "add", "scripts")
    git(root, "commit", "-m", "installed engines")
    remote = tmp_path / "origin.git"
    git(root, "clone", "--bare", str(root), str(remote))
    git(root, "remote", "set-url", "origin", str(remote))
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)" if active else "pass"])
    if not active:
        process.wait(timeout=10)
    settings = load_settings(root)
    store = ArtifactStore(settings, "live")
    identity = {
        "repository_identity": str(remote) + "#" + git(root, "rev-parse", "HEAD"),
        "protected_branch_head": git(root, "rev-parse", "HEAD"),
        "friction_log": "docs/kit-friction-log.md", "mode": "live",
        "session": "historical-session", "config_fingerprint": "a" * 64,
    }
    gate = {"created_at": 1790939543.119891, "host": "historical-host.example",
            "owner_token": "historical-owner", "pid": process.pid,
            "process_start_observation": 1790939543.11989, "run_identity": identity}
    binding = {"gate_path": settings.paths.gate_fragment.replace("{mode}", "live"),
               "owner_token": gate["owner_token"], "owner_run_identity": identity,
               "gate_claim_core_digest": "b" * 64}
    state = {"kind": "triage-run-state", "schema_version": 1, "phase": "reserved",
             "mode": "live", "engine_mode": "llm-only", "run_identity": identity,
             "config_fingerprint": identity["config_fingerprint"],
             "gate_owner_token": gate["owner_token"], "gate_binding": binding,
             "state_claim": {"reason": "initial-reservation", "previous_gate_binding": None,
                             "current_gate_binding": binding, "captured_state_digest": None,
                             "recovery_bundle_digest": None, "approval_digest": None},
             "frozen_snapshot": None, "frozen_inbox_digest": None, "attempts": [],
             "verified_tracker_identifiers": [], "repository_evidence": [], "pull_request_evidence": []}
    gate_raw = (json.dumps(gate, sort_keys=True) + "\n").encode()
    state_raw = (json.dumps(state, sort_keys=True) + "\n").encode()
    store.gate_path.parent.mkdir(parents=True, exist_ok=True)
    store.gate_path.write_bytes(gate_raw)
    store.state_path.write_bytes(state_raw)
    owner = {"source": "current-session", "operator_identity": "operator",
             "source_read_back": {"approver_identity": "operator", "text": "This was this machine and its owner stopped",
                                  "legacy_gate_owner": {"gate_digest": digest_bytes(gate_raw), "recorded_host": gate["host"],
                                                        "recorded_pid": process.pid, "local_host": socket.gethostname(),
                                                        "same_machine": True, "owner_terminated": True}}}
    owner_path = tmp_path / "owner.json"
    owner_path.write_bytes(dumps(owner))
    return root, store, gate_raw, state_raw, owner_path, process


def invoke(root, owner, *, request=None, approval=None, extra=()):
    argv = [sys.executable, str(root / "scripts/triage_friction_log.py"), "recover", "--legacy-gate-context", str(owner)]
    if request is not None:
        argv += ["--request", str(request), "--approval-context", str(approval)]
    completed = subprocess.run(argv + list(extra), cwd=root, capture_output=True, text=True, timeout=20)
    return loads_exact(completed.stdout.strip().encode())


def approval_files(tmp_path, core_digest):
    approved = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    request = tmp_path / "request.json"
    context = tmp_path / "approval.json"
    request.write_bytes(dumps({"recovery_approval": approved}))
    context.write_bytes(dumps({"source": "current-session", "operator_identity": "operator", "source_read_back": approved}))
    return request, context


def test_installed_historical_recovery_requires_action_approval_and_preserves_bytes(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    planned = invoke(root, owner)
    assert planned["outcome"] == "operator-held"
    plan = planned["recovery_plan"]
    assert plan["action_core"]["action"] == "retire-historical-prefreeze-reservation"
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    # A machine/termination attestation alone never approves a mutation.
    assert invoke(root, owner)["recovery_plan"] == plan
    request, context = approval_files(tmp_path, "f" * 64)
    refused = invoke(root, owner, request=request, approval=context)
    assert "does not bind" in refused["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    recovered = invoke(root, owner, request=request, approval=context)
    assert recovered["detail"] == "recovered-safe-to-restart"
    assert not store.gate_path.exists()
    assert Path(plan["action_core"]["quarantine_path"]).read_bytes() == state_raw
    assert store.gate_path.with_name(store.gate_path.name + ".quarantine-" + digest_bytes(gate_raw)[:16]).read_bytes() == gate_raw
    receipt = loads_exact(store.state_path.read_bytes())
    assert receipt["kind"] == "recovered-safe-to-restart"
    # Recovery does not restart; a later ordinary entry creates a fresh immutable
    # run without importing historical approval, session or configuration.
    started = engine.run("new", context="interactive", request={}, start=root)
    assert started["frozen_snapshot"]
    state = loads_exact(store.state_path.read_bytes())
    assert state["run_identity"]["session"] != "historical-session"
    assert state["config_fingerprint"] != "a" * 64
    assert not state.get("approval_record") and state["attempts"] == []


def test_active_historical_owner_is_held_before_state_observation(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, process = historical_fixture(tmp_path, monkeypatch, active=True)
    original = engine.observe
    def guarded(path, **kwargs):
        assert path != store.state_path, "active owner must be rejected before state observation"
        return original(path, **kwargs)
    monkeypatch.setattr(engine, "observe", guarded)
    try:
        context = ApprovalContext(**loads_exact(owner.read_bytes()))
        result = engine.run("recover", context="interactive", request={}, start=root, legacy_gate_context=context)
        assert result["outcome"] == "operator-held" and "active or reused" in result["detail"]
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.parametrize("change", ["host", "digest", "foreign", "source", "pid", "timestamp", "duplicate"])
def test_historical_owner_evidence_refuses_uncertain_or_foreign_capture(tmp_path, monkeypatch, change):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    context = loads_exact(owner.read_bytes())
    record = json.loads(gate_raw)
    if change == "host":
        context["source_read_back"]["legacy_gate_owner"]["same_machine"] = False
    elif change == "digest":
        context["source_read_back"]["legacy_gate_owner"]["gate_digest"] = "f" * 64
    elif change == "source":
        context["source"] = "document"
    elif change == "foreign":
        record["run_identity"]["repository_identity"] = "foreign#" + record["run_identity"]["protected_branch_head"]
    elif change == "pid":
        record["pid"] = True
    elif change == "timestamp":
        record["created_at"] = float("nan")
    if change in {"foreign", "pid", "timestamp"}:
        gate_raw = (json.dumps(record) + "\n").encode()
        context["source_read_back"]["legacy_gate_owner"]["gate_digest"] = digest_bytes(gate_raw)
    if change == "duplicate":
        gate_raw = gate_raw.replace(b'{', b'{"pid":1,', 1)
    store.gate_path.write_bytes(gate_raw)
    owner.write_bytes(dumps(context))
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held" and result["recovery_plan"] is None
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not store.recovery_path(digest_bytes(gate_raw)).exists()


@pytest.mark.parametrize("field,value", [("frozen_snapshot", {}), ("attempts", [{"status": "ambiguous"}]),
                                        ("approval_record", {"decision": "approve"}), ("phase", "completed"),
                                        ("phase", "unknown"),
                                        ("engine_mode", "engine-backed")])
def test_historical_prefreeze_action_refuses_unrecognized_or_external_evidence(tmp_path, monkeypatch, field, value):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    state = json.loads(state_raw)
    state[field] = value
    state_raw = (json.dumps(state) + "\n").encode()
    store.state_path.write_bytes(state_raw)
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held"
    assert result["recovery_plan"].get("held") is not None
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw


def test_historical_gate_context_cannot_enable_writes_or_unattended_execution(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    for extra in (("--enable-tracker",), ("--enable-github-forge",), ("--context", "unattended")):
        assert invoke(root, owner, extra=extra)["outcome"] == "hard-stop"
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw


def test_historical_capture_is_opt_in_and_owner_context_cannot_start_a_run(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    result = engine.run("recover", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held" and result["recovery_plan"] is None
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    store.gate_path.unlink()
    result = invoke(root, owner)
    assert result["detail"] == "historical owner evidence requires a blocking historical gate"
    assert store.state_path.read_bytes() == state_raw and not store.gate_path.exists()
    assert not store.recovery_path(digest_bytes(gate_raw)).exists()


def test_historical_safe_restart_rechecks_action_specific_approval(tmp_path, monkeypatch):
    root, store, _, _, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    assert invoke(root, owner, request=request, approval=context)["detail"] == "recovered-safe-to-restart"
    receipt_raw = store.state_path.read_bytes()
    receipt = loads_exact(receipt_raw)
    bundle_path = Path(receipt["configured_bundle_path"])
    envelope = loads_exact(bundle_path.read_bytes())
    # Recomputing outer hashes does not turn a refused decision into approval.
    envelope["approval"]["decision"] = "reject"
    bundle_path.write_bytes(dumps(envelope))
    receipt["prepared_envelope_digest"] = digest_bytes(dumps(envelope))
    store.state_path.write_bytes(dumps(receipt))
    rejected_raw = store.state_path.read_bytes()
    result = engine.run("new", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held" and "not bound" in result["detail"]
    assert store.state_path.read_bytes() == rejected_raw


def test_historical_action_cannot_omit_owner_evidence_with_rehashed_envelope(tmp_path, monkeypatch):
    from triage.recovery import validate_historical_prepared

    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    bundle = loads_exact(store.recovery_path(digest_bytes(gate_raw)).read_bytes())
    del bundle["capture_core"]["legacy_gate_owner_evidence"]
    bundle["capture_core_digest"] = canonical_digest(bundle["capture_core"])
    prepared = {**bundle, **plan, "approval": {"decision": "approve", "source": "current-session",
                                              "approver_identity": "operator", "core_digest": plan["action_core_digest"]}}
    with pytest.raises(Exception, match="owner evidence is missing"):
        validate_historical_prepared(store, prepared)
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw


def test_historical_quarantine_interruption_resumes_exact_approved_transition(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    planned = invoke(root, owner)
    request, context = approval_files(tmp_path, planned["recovery_plan"]["action_core_digest"])
    # A distinct process exits immediately after the state move. A later invocation
    # must finish the same prepared envelope rather than asking for new authority.
    child = r'''
import os, sys
from pathlib import Path
import triage.recovery as recovery
from triage_friction_log import main
original = recovery._quarantine
def stop_after_state(path, *args, **kwargs):
    result = original(path, *args, **kwargs)
    if path.name.endswith("state_live.json"):
        os._exit(73)
    return result
recovery._quarantine = stop_after_state
main(sys.argv[1:])
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "scripts/lib") + os.pathsep + str(root / "scripts")
    stopped = subprocess.run([sys.executable, "-c", child, "recover", "--legacy-gate-context", str(owner),
                              "--request", str(request), "--approval-context", str(context)], cwd=root, env=env, timeout=20)
    assert stopped.returncode == 73 and not store.state_path.exists()
    assert store.gate_path.read_bytes() == gate_raw
    resumed = invoke(root, owner)
    assert resumed["detail"] == "recovered-safe-to-restart"
    assert Path(planned["recovery_plan"]["action_core"]["quarantine_path"]).read_bytes() == state_raw
    assert not store.gate_path.exists()
