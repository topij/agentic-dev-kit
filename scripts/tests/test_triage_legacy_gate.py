"""Historical captures never become leases or live approval authority."""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_triage_engine import ENGINE_DIR, git, repository
from triage import engine, legacy_gate
from triage.approval import ApprovalContext
from triage.canonical import digest as canonical_digest
from triage.canonical import digest_bytes, dumps, loads_exact
from triage.model import TriageError, load_settings
from triage.storage import ArtifactStore


def historical_fixture(tmp_path, monkeypatch, *, active=False, mode="live"):
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
    store = ArtifactStore(settings, mode)
    identity = {
        "repository_identity": str(remote) + "#" + git(root, "rev-parse", "HEAD"),
        "protected_branch_head": git(root, "rev-parse", "HEAD"),
        "friction_log": "docs/kit-friction-log.md", "mode": mode,
        "session": "historical-session", "config_fingerprint": "a" * 64,
    }
    gate = {"created_at": 1790939543.119891, "host": "historical-host.example",
            "owner_token": "historical-owner", "pid": process.pid,
            "process_start_observation": 1790939543.11989, "run_identity": identity}
    binding = {"gate_path": settings.paths.gate_fragment.replace("{mode}", mode),
               "owner_token": gate["owner_token"], "owner_run_identity": identity,
               "gate_claim_core_digest": "b" * 64}
    state = {"kind": "triage-run-state", "schema_version": 1, "phase": "reserved",
             "mode": mode, "engine_mode": "llm-only", "run_identity": identity,
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


def invoke(root, owner, *, request=None, approval=None, extra=(), entry="recover"):
    argv = [sys.executable, str(root / "scripts/triage_friction_log.py"), entry, "--legacy-gate-context", str(owner)]
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


@pytest.mark.parametrize("change", ["host", "digest", "foreign", "source", "pid", "overflow-pid", "timestamp", "duplicate"])
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
    elif change == "overflow-pid":
        record["pid"] = 2 ** 40
        context["source_read_back"]["legacy_gate_owner"]["recorded_pid"] = record["pid"]
    elif change == "timestamp":
        record["created_at"] = float("nan")
    if change in {"foreign", "pid", "overflow-pid", "timestamp"}:
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


@pytest.mark.parametrize("field,value", [("frozen_snapshot", {}), ("frozen_inbox_digest", "f" * 64),
                                        ("attempts", [{"status": "ambiguous"}]),
                                        ("verified_tracker_identifiers", ["TRI-27"]),
                                        ("repository_evidence", [{"result": "recorded"}]),
                                        ("pull_request_evidence", [{"result": "recorded"}]),
                                        ("approval_record", {"decision": "approve"}), ("phase", "completed"),
                                        ("phase", "unknown"),
                                        ("engine_mode", "engine-backed"), ("schema_version", 1.0)])
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


@pytest.mark.parametrize("field", [
    "run_identity", "config_fingerprint", "gate_owner_token", "mode", "schema_version",
    "binding-shape", "binding-extra", "binding-gate_path", "binding-owner_token",
    "binding-owner_run_identity", "binding-gate_claim_core_digest",
    "claim-reason", "claim-previous_gate_binding", "claim-current_gate_binding",
    "claim-captured_state_digest", "claim-recovery_bundle_digest", "claim-approval_digest",
    "claim-extra",
])
def test_historical_prefreeze_action_refuses_inconsistent_identity_or_reservation_claims(tmp_path, monkeypatch, field):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    state = json.loads(state_raw)
    if field == "run_identity":
        state[field]["session"] = "unrelated-state-session"
    elif field == "config_fingerprint":
        state[field] = "f" * 64
    elif field == "gate_owner_token":
        state[field] = "unrelated-state-owner"
    elif field == "mode":
        state[field] = "test"
    elif field == "schema_version":
        state[field] = True
    elif field.startswith("binding-"):
        name = field.removeprefix("binding-")
        binding = state["gate_binding"]
        if name == "shape":
            state["gate_binding"] = "unsupported-binding"
        elif name == "owner_run_identity":
            binding[name]["session"] = "unrelated-binding-session"
        else:
            binding[name] = "unrelated-binding-value"
        # Keep the initial claim consistent with this changed binding so a
        # separate claim mismatch cannot falsely kill a missing binding guard.
        state["state_claim"]["current_gate_binding"] = state["gate_binding"]
    else:
        name = field.removeprefix("claim-")
        state["state_claim"][name] = "unsupported-initial-claim"
    state_raw = (json.dumps(state, sort_keys=True) + "\n").encode()
    store.state_path.write_bytes(state_raw)
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held" and result["recovery_plan"].get("held") is not None
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


@pytest.mark.parametrize("supplied", [{"proposals": []}, {"approval": {"command": "approve all", "proposal_set_digest": "f" * 64}}, {"finalize": True}])
def test_historical_owner_context_rejects_draft_analysis_approval_and_finalization(tmp_path, monkeypatch, supplied):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    context = ApprovalContext(**loads_exact(owner.read_bytes()))
    result = engine.run("recover", context="interactive", request=supplied, start=root, legacy_gate_context=context)
    assert result["outcome"] == "hard-stop"
    assert "cannot authorize draft, approval or external writes" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not store.recovery_path(digest_bytes(gate_raw)).exists()


def test_uncertain_historical_process_probe_holds_before_state_observation(tmp_path, monkeypatch):
    from triage import legacy_gate

    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    def uncertain(pid, signal):
        raise PermissionError("process is not observable")
    monkeypatch.setattr(legacy_gate.os, "kill", uncertain)
    original = engine.observe
    def guarded(path, **kwargs):
        assert path != store.state_path, "uncertain owner must be rejected before state observation"
        return original(path, **kwargs)
    monkeypatch.setattr(engine, "observe", guarded)
    result = engine.run("recover", context="interactive", request={}, start=root,
                        legacy_gate_context=ApprovalContext(**loads_exact(owner.read_bytes())))
    assert result["outcome"] == "operator-held" and "uncertain" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw


def test_historical_provenance_requires_fresh_protected_remote_observation(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    git(root, "commit", "--allow-empty", "-m", "remote advance")
    git(root, "push", "origin", "main")
    # Push updates the local tracking ref, so recreate the stale observation.
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD^")
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held" and "refresh the protected ref" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    assert invoke(root, owner)["recovery_plan"]["action_core"]["action"] == "retire-historical-prefreeze-reservation"


@pytest.mark.parametrize("field,value", [("decision", "reject"), ("core_digest", "f" * 64), ("approval", []),
                                       ("approver_identity", True), ("approver_identity", "different-operator")])
def test_historical_safe_restart_rechecks_action_specific_approval(tmp_path, monkeypatch, field, value):
    root, store, _, _, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    assert invoke(root, owner, request=request, approval=context)["detail"] == "recovered-safe-to-restart"
    receipt_raw = store.state_path.read_bytes()
    receipt = loads_exact(receipt_raw)
    bundle_path = Path(receipt["configured_bundle_path"])
    envelope = loads_exact(bundle_path.read_bytes())
    # Recomputing outer hashes does not turn a refused decision into approval.
    if field == "approval":
        envelope["approval"] = value
    else:
        envelope["approval"][field] = value
    bundle_path.write_bytes(dumps(envelope))
    receipt["prepared_envelope_digest"] = digest_bytes(dumps(envelope))
    store.state_path.write_bytes(dumps(receipt))
    rejected_raw = store.state_path.read_bytes()
    result = engine.run("new", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held" and "approval" in result["detail"]
    assert store.state_path.read_bytes() == rejected_raw


def test_historical_quarantine_requires_the_captured_operator_identity(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    approval_request = loads_exact(request.read_bytes())
    bundle_path = store.recovery_path(digest_bytes(gate_raw))
    captured_bundle = bundle_path.read_bytes()
    approval_request["recovery_approval"]["approver_identity"] = "different-operator"
    approval_context = loads_exact(context.read_bytes())
    approval_context["operator_identity"] = "different-operator"
    approval_context["source_read_back"] = approval_request["recovery_approval"]
    request.write_bytes(dumps(approval_request))
    context.write_bytes(dumps(approval_context))
    result = invoke(root, owner, request=request, approval=context)
    assert result["outcome"] == "operator-held" and "approval identity" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not Path(plan["action_core"]["quarantine_path"]).exists()
    assert bundle_path.read_bytes() == captured_bundle
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    retried = invoke(root, owner, request=request, approval=context)
    assert retried["detail"] == "recovered-safe-to-restart"
    assert Path(plan["action_core"]["quarantine_path"]).read_bytes() == state_raw



@pytest.mark.parametrize("mode, state_present", [("live", False), ("test", False), ("test", True)])
def test_historical_publication_rejects_foreign_operator_without_blocking_retry(tmp_path, monkeypatch, mode, state_present):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch, mode=mode)
    if not state_present:
        store.state_path.unlink()
    entry = "test" if mode == "test" else "recover"
    plan = invoke(root, owner, entry=entry)["recovery_plan"]
    core_key = "capture_core" if state_present else "prepared_core"
    core_digest = plan[core_key + "_digest"]
    bundle_path = Path(plan[core_key]["configured_bundle_path"])
    assert not bundle_path.exists()
    request, context = approval_files(tmp_path, core_digest)
    approval_request = loads_exact(request.read_bytes())
    approval_request["recovery_approval"]["approver_identity"] = "different-operator"
    approval_context = loads_exact(context.read_bytes())
    approval_context["operator_identity"] = "different-operator"
    approval_context["source_read_back"] = approval_request["recovery_approval"]
    request.write_bytes(dumps(approval_request))
    context.write_bytes(dumps(approval_context))
    refused = invoke(root, owner, entry=entry, request=request, approval=context)
    assert refused["outcome"] == "operator-held" and "approval identity" in refused["detail"]
    assert store.gate_path.read_bytes() == gate_raw
    assert (store.state_path.read_bytes() if store.state_path.exists() else None) == (state_raw if state_present else None)
    assert not bundle_path.exists()
    assert not list(store.gate_path.parent.glob("*.quarantine-*"))
    request, context = approval_files(tmp_path, core_digest)
    retried = invoke(root, owner, entry=entry, request=request, approval=context)
    evidence = loads_exact(bundle_path.read_bytes())
    assert evidence["approval"]["approver_identity"] == "operator"
    assert retried["detail"] == ("test-gate-state-present" if state_present else "gate-only-operator-held")
    if state_present:
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    else:
        assert store.gate_path.with_name(store.gate_path.name + ".quarantine-" + digest_bytes(gate_raw)[:16]).read_bytes() == gate_raw


@pytest.mark.parametrize("mode", ["live", "test"])
def test_historical_gate_only_resume_rechecks_captured_operator_before_intent(tmp_path, monkeypatch, mode):
    from triage.recovery import gate_only_plan, prepare_gate_only

    root, store, gate_raw, _, owner_path, _ = historical_fixture(tmp_path, monkeypatch, mode=mode)
    store.state_path.unlink()
    owner = ApprovalContext(**loads_exact(owner_path.read_bytes()))
    store = ArtifactStore(store.settings, mode, legacy_gate_context=owner)
    plan = gate_only_plan(store, store.settings)
    request, _ = approval_files(tmp_path, plan["prepared_core_digest"])
    envelope = prepare_gate_only(store, store.settings,
                                 approval=loads_exact(request.read_bytes())["recovery_approval"], operator="operator")
    envelope["approval"]["approver_identity"] = "different-operator"
    bundle_path = store.recovery_path(digest_bytes(gate_raw))
    rejected_bundle = dumps(envelope)
    bundle_path.write_bytes(rejected_bundle)
    result = invoke(root, owner_path, entry="test" if mode == "test" else "recover")
    assert result["outcome"] == "operator-held" and "approval identity" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and not store.state_path.exists()
    assert bundle_path.read_bytes() == rejected_bundle
    assert not list(store.gate_path.parent.glob("*.quarantine-*"))


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


@pytest.mark.parametrize("advance", [False, True])
def test_historical_quarantine_interruption_resumes_exact_approved_transition(tmp_path, monkeypatch, advance):
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
    if advance:
        git(root, "commit", "--allow-empty", "-m", "protected branch advances during interruption")
        git(root, "push", "origin", "main")
    resumed = invoke(root, owner)
    assert resumed["detail"] == "recovered-safe-to-restart"
    assert Path(planned["recovery_plan"]["action_core"]["quarantine_path"]).read_bytes() == state_raw
    assert not store.gate_path.exists()


@pytest.mark.parametrize("decision", ["reject", "approve"])
def test_rehashed_prepared_action_cannot_strip_historical_classification(tmp_path, monkeypatch, decision):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    bundle_path = store.recovery_path(digest_bytes(gate_raw))
    bundle = loads_exact(bundle_path.read_bytes())
    del bundle["capture_core"]["legacy_gate_owner_evidence"]
    bundle["capture_core_digest"] = canonical_digest(bundle["capture_core"])
    action = {**plan["action_core"], "action": "abandon-invalid-state",
              "capture_core_digest": bundle["capture_core_digest"]}
    action_digest = canonical_digest(action)
    prepared = {**bundle, "kind": "state-present-prepared", "action_core": action,
                "action_core_digest": action_digest,
                "approval": {"decision": decision, "source": "current-session",
                             "approver_identity": "operator", "core_digest": action_digest}}
    bundle_path.write_bytes(dumps(prepared))
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held"
    assert "approval" in result["detail"] if decision == "reject" else "owner evidence is missing" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not Path(action["quarantine_path"]).exists()


def test_completed_historical_recovery_survives_protected_branch_advance(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    request, context = approval_files(tmp_path, plan["action_core_digest"])
    assert invoke(root, owner, request=request, approval=context)["detail"] == "recovered-safe-to-restart"
    receipt = loads_exact(store.state_path.read_bytes())
    bundle_path = Path(receipt["configured_bundle_path"])
    prepared_raw = bundle_path.read_bytes()
    git(root, "commit", "--allow-empty", "-m", "protected branch advances before restart")
    git(root, "push", "origin", "main")
    result = engine.run("new", context="interactive", request={}, start=root)
    assert result["frozen_snapshot"]
    assert loads_exact(store.state_path.read_bytes())["run_identity"]["session"] != "historical-session"
    assert bundle_path.read_bytes() == prepared_raw
    assert Path(plan["action_core"]["quarantine_path"]).read_bytes() == state_raw
    assert store.gate_path.with_name(store.gate_path.name + ".quarantine-" + digest_bytes(gate_raw)[:16]).read_bytes() == gate_raw


def test_historical_draft_must_be_a_protected_ancestor_before_capture(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    git(root, "checkout", "--orphan", "unrelated-draft")
    git(root, "commit", "-m", "unrelated historical draft")
    unrelated_head = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "main")
    record = json.loads(gate_raw)
    identity = record["run_identity"]
    remote = git(root, "remote", "get-url", "origin")
    identity.update(repository_identity=remote + "#" + unrelated_head, protected_branch_head=unrelated_head)
    gate_raw = (json.dumps(record, sort_keys=True) + "\n").encode()
    state = json.loads(state_raw)
    state["run_identity"] = identity
    state["gate_binding"]["owner_run_identity"] = identity
    state["state_claim"]["current_gate_binding"] = state["gate_binding"]
    state_raw = (json.dumps(state, sort_keys=True) + "\n").encode()
    context = loads_exact(owner.read_bytes())
    context["source_read_back"]["legacy_gate_owner"]["gate_digest"] = digest_bytes(gate_raw)
    store.gate_path.write_bytes(gate_raw)
    store.state_path.write_bytes(state_raw)
    owner.write_bytes(dumps(context))
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held" and "not a verified protected ancestor" in result["detail"]
    assert result["recovery_plan"] is None
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not store.recovery_path(digest_bytes(gate_raw)).exists()


def test_installed_historical_test_gate_publishes_only_approved_held_evidence(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch, mode="test")
    live = ArtifactStore(store.settings, "live")
    before = {p: p.read_bytes() if p.exists() else None for p in (live.gate_path, live.state_path)}
    planned = invoke(root, owner, entry="test")
    assert planned["outcome"] == "operator-held"
    assert planned["detail"] == "blocking test gate state capture awaits exact held-evidence approval"
    plan = planned["recovery_plan"]
    assert plan["capture_core"]["mode"] == "test"
    assert "action_core" not in plan
    bundle_path = Path(plan["capture_core"]["configured_bundle_path"])
    assert not bundle_path.exists()
    request, context = approval_files(tmp_path, "f" * 64)
    refused = invoke(root, owner, entry="test", request=request, approval=context)
    assert refused["outcome"] == "operator-held" and "does not bind" in refused["detail"]
    assert not bundle_path.exists()
    request, context = approval_files(tmp_path, plan["capture_core_digest"])
    held = invoke(root, owner, entry="test", request=request, approval=context)
    assert held["outcome"] == "operator-held" and held["detail"] == "test-gate-state-present"
    raw_bundle = bundle_path.read_bytes()
    evidence = loads_exact(raw_bundle)
    assert evidence["kind"] == "state-present-test-gate-held"
    assert evidence["capture_core"] == plan["capture_core"]
    assert evidence["approval"]["core_digest"] == plan["capture_core_digest"]
    assert invoke(root, owner, entry="test")["outcome"] == "operator-held"
    assert bundle_path.read_bytes() == raw_bundle
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not list(store.state_path.parent.glob("*.quarantine-*"))
    assert not held["frozen_snapshot"] and held["report"] is None
    for path, raw in before.items():
        assert (path.read_bytes() if path.exists() else None) == raw


@pytest.mark.parametrize("operation, helper", [("remote", False), ("ls-remote", False), ("rev-parse", False), ("merge-base", False), ("ls-remote", True)])
def test_historical_provenance_timeout_holds_before_capture(tmp_path, monkeypatch, operation, helper):
    root, store, gate_raw, state_raw, owner_path, _ = historical_fixture(tmp_path, monkeypatch)
    owner = ApprovalContext(**loads_exact(owner_path.read_bytes()))
    original_popen = legacy_gate.Popen
    stalled = []
    helper_pids = []

    def helper_running(pid):
        status = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True, timeout=2)
        assert status.returncode in {0, 1} and not status.stderr.strip()
        # A killed orphan may briefly remain a zombie before the OS reaps it.
        return bool(status.stdout.strip()) and not status.stdout.strip().startswith("Z")

    def stall_selected(argv, **kwargs):
        if argv[3] == operation:
            program = "import time; time.sleep(60)"
            if helper:
                # Finite lifetime lets a surviving cleanup mutant terminate
                # without signaling a PID after its parent has been reaped.
                program = "import subprocess,sys,time; helper=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)']); print(helper.pid, flush=True); time.sleep(60)"
            child = original_popen([sys.executable, "-c", program], **kwargs)
            stalled.append(child)
            if helper:
                pid = int(child.stdout.readline().strip())
                helper_pids.append(pid)
                assert helper_running(pid), "helper must be running before the provenance deadline"
            return child
        return original_popen(argv, **kwargs)

    monkeypatch.setattr(legacy_gate, "Popen", stall_selected)
    monkeypatch.setattr(legacy_gate, "PROVENANCE_TIMEOUT_SECONDS", 0.05)
    try:
        began = time.monotonic()
        result = engine.run("recover", context="interactive", start=root, legacy_gate_context=owner)
        assert time.monotonic() - began < 5
        assert result["outcome"] == "operator-held"
        assert "provenance read timed out" in result["detail"]
        assert stalled and all(child.poll() is not None for child in stalled)
        assert bool(helper_pids) == helper
        assert all(not helper_running(pid) for pid in helper_pids), "provenance helper survived process-group cleanup"
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        for child in stalled:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
        deadline = time.monotonic() + 12
        while any(helper_running(pid) for pid in helper_pids) and time.monotonic() < deadline:
            time.sleep(0.025)
        assert all(not helper_running(pid) for pid in helper_pids), "owned test helper did not reach terminal state"



def test_historical_provenance_read_error_reaps_owned_child_before_capture(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner_path, _ = historical_fixture(tmp_path, monkeypatch)
    owner = ApprovalContext(**loads_exact(owner_path.read_bytes()))
    original_popen = legacy_gate.Popen
    children = []
    reads = []

    def fail_selected_read(argv, **kwargs):
        if argv[3] != "ls-remote":
            return original_popen(argv, **kwargs)
        child = original_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
        children.append(child)
        communicate = child.communicate

        def read_error(*, timeout):
            reads.append(timeout)
            if len(reads) == 1:
                assert child.poll() is None, "the owned child must be alive when its read fails"
                raise OSError("injected provenance pipe read failure")
            return communicate(timeout=timeout)

        child.communicate = read_error
        return child

    monkeypatch.setattr(legacy_gate, "Popen", fail_selected_read)
    started = time.monotonic()
    try:
        result = engine.run("recover", context="interactive", request={}, start=root, legacy_gate_context=owner)
        assert result["outcome"] == "operator-held"
        assert "historical gate provenance read is unavailable" in result["detail"]
        assert time.monotonic() - started < 5
        assert len(children) == 1
        child = children[0]
        assert child.poll() is not None, "the owned provenance child survived its read error"
        assert child.stdout.closed and child.stderr.closed
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()


def test_detached_provenance_helper_holds_cleanup_uncertainty_before_capture(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner_path, _ = historical_fixture(tmp_path, monkeypatch)
    owner = ApprovalContext(**loads_exact(owner_path.read_bytes()))
    original_popen = legacy_gate.Popen
    children, helper_pids = [], []

    def helper_running(pid):
        status = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True, timeout=2)
        assert status.returncode in {0, 1} and not status.stderr.strip()
        return bool(status.stdout.strip()) and not status.stdout.strip().startswith("Z")

    def detach_selected(argv, **kwargs):
        if argv[3] == "ls-remote":
            # The finite helper retains the pipes from a separate session. Its
            # PID is observed only; cleanup never signals an unowned helper.
            program = "import subprocess,sys,time; helper=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'], start_new_session=True); print(helper.pid, flush=True); time.sleep(60)"
            child = original_popen([sys.executable, "-c", program], **kwargs)
            children.append(child)
            helper_pid = int(child.stdout.readline().strip())
            helper_pids.append(helper_pid)
            assert helper_running(helper_pid)
            return child
        return original_popen(argv, **kwargs)

    monkeypatch.setattr(legacy_gate, "Popen", detach_selected)
    monkeypatch.setattr(legacy_gate, "PROVENANCE_TIMEOUT_SECONDS", 0.05)
    try:
        began = time.monotonic()
        result = engine.run("recover", context="interactive", start=root, legacy_gate_context=owner)
        assert time.monotonic() - began < 5
        assert result["outcome"] == "operator-held"
        assert "descendant cleanup uncertain" in result["detail"]
        assert children and all(child.poll() is not None for child in children)
        assert all(child.stdout.closed and child.stderr.closed for child in children)
        assert helper_pids and all(helper_running(pid) for pid in helper_pids)
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
        deadline = time.monotonic() + 15
        while any(helper_running(pid) for pid in helper_pids) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert all(not helper_running(pid) for pid in helper_pids), "finite detached helper did not terminate"


def test_denied_group_cleanup_reaps_owned_provenance_child(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner_path, _ = historical_fixture(tmp_path, monkeypatch)
    owner = ApprovalContext(**loads_exact(owner_path.read_bytes()))
    original_popen = legacy_gate.Popen
    children = []

    def stall_remote(argv, **kwargs):
        if argv[3] == "ls-remote":
            child = original_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
            children.append(child)
            return child
        return original_popen(argv, **kwargs)

    def deny_group(*args):
        raise PermissionError("group signaling denied")

    monkeypatch.setattr(legacy_gate, "Popen", stall_remote)
    monkeypatch.setattr(legacy_gate.os, "killpg", deny_group)
    monkeypatch.setattr(legacy_gate, "PROVENANCE_TIMEOUT_SECONDS", 0.05)
    try:
        began = time.monotonic()
        result = engine.run("recover", context="interactive", start=root, legacy_gate_context=owner)
        assert time.monotonic() - began < 5
        assert result["outcome"] == "operator-held"
        assert "descendant cleanup uncertain" in result["detail"]
        assert children and all(child.poll() is not None for child in children)
        assert all(child.stdout.closed and child.stderr.closed for child in children)
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)


def test_denied_child_cleanup_closes_pipes_and_holds_uncertainty(tmp_path, monkeypatch):
    import io

    class DeniedChild:
        pid = 123
        stdout = io.StringIO()
        stderr = io.StringIO()
        killed = False
        waited = False

        def communicate(self, *, timeout):
            raise subprocess.TimeoutExpired("git", timeout)

        def kill(self):
            self.killed = True
            raise PermissionError("child signaling denied")

        def wait(self, *, timeout):
            self.waited = True
            raise subprocess.TimeoutExpired("git", timeout)

    child = DeniedChild()

    def deny_group(*args):
        raise PermissionError("group signaling denied")

    monkeypatch.setattr(legacy_gate, "Popen", lambda *args, **kwargs: child)
    monkeypatch.setattr(legacy_gate.os, "killpg", deny_group)
    with pytest.raises(TriageError, match="owned child termination unconfirmed") as raised:
        legacy_gate._git_read(tmp_path, "remote", "get-url", "origin")
    assert raised.value.outcome == "operator-held"
    assert child.killed and child.waited and child.stdout.closed and child.stderr.closed


def test_rehashed_historical_action_with_owner_evidence_cannot_change(tmp_path, monkeypatch):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    plan = invoke(root, owner)["recovery_plan"]
    bundle_path = store.recovery_path(digest_bytes(gate_raw))
    bundle = loads_exact(bundle_path.read_bytes())
    assert bundle["capture_core"]["legacy_gate_owner_evidence"]
    action = {**plan["action_core"], "action": "abandon-invalid-state"}
    action_digest = canonical_digest(action)
    approved = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": action_digest}
    prepared = {**bundle, "kind": "state-present-prepared", "action_core": action,
                "action_core_digest": action_digest, "approval": approved}
    bundle_path.write_bytes(dumps(prepared))
    result = invoke(root, owner)
    assert result["outcome"] == "operator-held"
    assert "historical recovery action changed" in result["detail"]
    assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
    assert not Path(action["quarantine_path"]).exists()


@pytest.mark.parametrize("stream", [1, 2])
def test_historical_provenance_decoding_error_holds_before_capture(tmp_path, monkeypatch, stream):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    original = legacy_gate.Popen
    owned = []

    def malformed_remote(argv, **kwargs):
        if argv[3] != "ls-remote":
            return original(argv, **kwargs)
        child = original([sys.executable, "-c", f"import os; os.write({stream}, bytes([255]))"], **kwargs)
        owned.append(child)
        return child

    def unexpected_signal(*args):
        pytest.fail("decoding an already reaped child must not signal its PID")

    monkeypatch.setattr(legacy_gate, "Popen", malformed_remote)
    monkeypatch.setattr(legacy_gate.os, "killpg", unexpected_signal)
    try:
        result = engine.run("recover", context="interactive", start=root,
                            legacy_gate_context=ApprovalContext(**loads_exact(owner.read_bytes())))
        assert result["outcome"] == "operator-held"
        assert "provenance read is unavailable" in result["detail"]
        assert owned and all(child.returncode == 0 for child in owned)
        assert all(child.stdout.closed and child.stderr.closed for child in owned)
        assert store.gate_path.read_bytes() == gate_raw
        assert store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()


def test_historical_provenance_invalid_git_remote_bytes_hold(tmp_path):
    root = tmp_path / "malformed-remote"
    root.mkdir()
    git(root, "init")
    config = root / ".git/config"
    config.write_bytes(config.read_bytes() + b'\n[remote "origin"]\n\turl = https://example.invalid/\xff\n')
    with pytest.raises(TriageError, match="provenance read is unavailable"):
        legacy_gate._git_read(root, "remote", "get-url", "origin")


@pytest.mark.parametrize("initial", ["timeout", "read-error"])
@pytest.mark.parametrize("group_denied", [False, True])
def test_historical_cleanup_decoding_preserves_original_observations(tmp_path, monkeypatch, initial, group_denied):
    root, store, gate_raw, state_raw, owner, _ = historical_fixture(tmp_path, monkeypatch)
    original = legacy_gate.Popen
    owned = []
    ready = tmp_path / "child-ready"

    def invalid_live_child(argv, **kwargs):
        if argv[3] != "ls-remote":
            return original(argv, **kwargs)
        program = "import os,sys,time; from pathlib import Path; os.write(1,bytes([255])); Path(sys.argv[1]).write_text('ready'); time.sleep(60)"
        child = original([sys.executable, "-c", program, str(ready)], **kwargs)
        owned.append(child)
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert ready.exists() and child.poll() is None
        if initial == "read-error":
            communicate = child.communicate
            reads = []

            def read_error(*, timeout):
                reads.append(timeout)
                if len(reads) == 1:
                    raise OSError("injected initial pipe read error")
                return communicate(timeout=timeout)

            child.communicate = read_error
        return child

    def deny_owned_group(pid, sig):
        assert owned and pid == owned[-1].pid
        raise PermissionError("injected owned group denial")

    monkeypatch.setattr(legacy_gate, "Popen", invalid_live_child)
    if group_denied:
        monkeypatch.setattr(legacy_gate.os, "killpg", deny_owned_group)
    monkeypatch.setattr(legacy_gate, "PROVENANCE_TIMEOUT_SECONDS", .05)
    try:
        result = engine.run("recover", context="interactive", start=root,
                            legacy_gate_context=ApprovalContext(**loads_exact(owner.read_bytes())))
        assert result["outcome"] == "operator-held"
        assert owned and all(child.poll() is not None for child in owned)
        assert all(child.stdout.closed and child.stderr.closed for child in owned)
        assert store.gate_path.read_bytes() == gate_raw and store.state_path.read_bytes() == state_raw
        assert not store.recovery_path(digest_bytes(gate_raw)).exists()
        if group_denied:
            assert "process-group cleanup unavailable; descendant cleanup uncertain" in result["detail"]
        if initial == "timeout":
            assert "provenance read timed out" in result["detail"]
        else:
            assert "provenance read is unavailable" in result["detail"]
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()
