from __future__ import annotations

import inspect
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from test_triage_engine import (
    ENGINE_DIR,
    approval_context,
    approval_for,
    git,
    repository,
    request,
)
from test_triage_providers import LinearIssues, LinearTransport
from triage import engine
from triage.approval import ApprovalContext
from triage.canonical import decode_bytes, digest, digest_bytes, dumps, encode_bytes, loads_exact
from triage.model import canonical_state, load_settings
from triage.project_correction import PROJECT_GUARD_PROVIDER_SHA256
from triage.providers import FakeForge


def linear_repo(tmp_path, *, installed=False):
    root = repository(tmp_path)
    path = root / "config/dev-model.yaml"
    text = path.read_text()
    for before, after in (
        ("backend: github-issues", "backend: linear"),
        ('project_name: "topij/agentic-dev-kit"', 'project_name: "Adopter"'),
        ('url: "https://github.com/topij/agentic-dev-kit/issues"', 'url: "https://linear.app"'),
        ('team_id: ""', 'team_id: "team"'),
        ('project_id: ""', 'project_id: "project"'),
        ('label_name: ""', 'label_name: "bug"'),
    ):
        assert before in text
        text = text.replace(before, after)
    path.write_text(text)
    if installed:
        shutil.copy2(ENGINE_DIR / "triage_friction_log.py", root / "scripts/triage_friction_log.py")
        shutil.copytree(ENGINE_DIR / "lib", root / "scripts/lib", ignore=shutil.ignore_patterns("__pycache__", "tests"))
        git(root, "add", ".")
        git(root, "commit", "-m", "installed Linear fixture")
        remote = tmp_path / "origin.git"
        git(root, "clone", "--bare", str(root), str(remote))
        git(root, "remote", "set-url", "origin", str(remote))
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def rejected_run(tmp_path, monkeypatch, *, installed=False):
    root = linear_repo(tmp_path, installed=installed)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    supplied = request(root)
    supplied["proposals"][0]["project"] = "Wrong project"
    # Reproduce the prior presentation contract, then exercise the real adapter
    # guard through persisted tracker-write orchestration. This does not bypass
    # the correction route under test.
    original = engine._proposal_records
    def legacy_records(*args, **kwargs):
        kwargs.pop("configured_project", None)
        return original(*args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(engine, "_proposal_records", legacy_records)
        draft = engine.run("new", context="interactive", start=root, request=supplied)
    path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(path.read_bytes())
    old_request = {"approval": approval_for(presented)}
    context = approval_context(presented)
    decisions, approval = engine._approval_authority(presented, old_request, context)
    writing = {**presented, "phase": "tracker-write", "decisions": decisions, "approval": approval, "operations": []}
    path.write_bytes(dumps(writing))
    transport = LinearTransport()
    tracker = LinearIssues(transport=transport, sleep=lambda _: None)
    result = engine.run("resume", context="interactive", start=root, tracker=tracker, head_authority=FakeForge([]))
    assert result["detail"] == "approved Linear project differs from configured destination"
    assert not any("mutation " in query for query, _ in transport.calls)
    raw = path.read_bytes()
    state = loads_exact(raw)
    stdout = dumps(result) + b"\n"
    observer = ApprovalContext("current-session", "operator", {
        "state_digest": digest_bytes(raw), "provider_source_sha256": digest_bytes(Path(inspect.getfile(LinearIssues)).read_bytes()),
        "report_digest": digest_bytes(Path(draft["report"]).read_bytes()),
        "route": "observed-unmodified-installed-linear-adapter",
        "invocation": {
            "command": [sys.executable, str(root / "scripts/triage_friction_log.py"), "resume",
                        "--context", "interactive", "--request", str(root / "approved-request.json"),
                        "--approval-context", str(root / "approved-context.json"), "--enable-tracker"],
            "revision": state["run_identity"]["protected_branch_head"], "directory": str(root),
            "date": "2026-10-05", "exit_code": 0, "stdout_sha256": digest_bytes(stdout),
        },
        "stdout_raw": encode_bytes(stdout),
    })
    assert observer.source_read_back["provider_source_sha256"] == PROJECT_GUARD_PROVIDER_SHA256
    return root, path, draft, tracker, transport, observer, raw, old_request, context


def plan_and_approval(root, tracker, observer):
    planned = engine.run("correct-project", context="interactive", start=root, tracker=tracker, rejection_context=observer)
    assert planned["detail"] == "project correction awaits exact action approval"
    core_digest = planned["recovery_plan"]["action_core_digest"]
    approval = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    return planned, {"recovery_approval": approval}, ApprovalContext("current-session", "operator", approval)


def test_correction_preserves_failed_bytes_requires_new_approval_and_creates_once(tmp_path, monkeypatch):
    root, path, draft, tracker, transport, observer, raw, old_request, old_context = rejected_run(tmp_path, monkeypatch)
    frozen = Path(draft["frozen_snapshot"]).read_bytes()
    report = Path(draft["report"]).read_bytes()
    inbox = (root / "docs/kit-friction-log.md").read_bytes()
    planned, approved_request, approved_context = plan_and_approval(root, tracker, observer)
    assert path.read_bytes() == raw
    applied = engine.run("correct-project", context="interactive", start=root, request=approved_request, tracker=tracker,
                         approval_context=approved_context, rejection_context=observer)
    assert applied["detail"] == "project correction applied; complete corrected filing approval is pending"
    corrected = canonical_state(path.read_bytes(), settings=load_settings(root), mode="live")
    assert corrected["phase"] == "awaiting-approval" and corrected["approval"] is None
    assert corrected["decisions"] == [] and corrected["attempts"] == []
    assert decode_bytes(corrected["proposal_correction"]["action_core"]["captured_state_raw"]) == raw
    assert decode_bytes(corrected["proposal_correction"]["action_core"]["captured_report_raw"]) == report
    assert corrected["run_identity"] == loads_exact(raw)["run_identity"]
    assert Path(draft["frozen_snapshot"]).read_bytes() == frozen
    assert (root / "docs/kit-friction-log.md").read_bytes() == inbox
    assert corrected["proposal_payload_digests"] != loads_exact(raw)["proposal_payload_digests"]
    assert not any("mutation " in query for query, _ in transport.calls)
    refused = engine.run("resume", context="interactive", start=root, request=old_request, tracker=tracker,
                         approval_context=old_context, head_authority=FakeForge([]))
    assert "displayed proposal set" in refused["detail"]
    assert not any("mutation " in query for query, _ in transport.calls)
    repeated = engine.run("correct-project", context="interactive", start=root, tracker=tracker)
    assert "already applied" in repeated["detail"]
    written = engine.run("resume", context="interactive", start=root, request={"approval": approval_for(corrected)},
                         approval_context=approval_context(corrected), tracker=tracker, head_authority=FakeForge([]))
    assert written["verified_tracker_identifiers"] == ["ADO-17"]
    assert sum("mutation " in query for query, _ in transport.calls) == 1
    engine.run("resume", context="interactive", start=root, tracker=tracker, head_authority=FakeForge([]))
    assert sum("mutation " in query for query, _ in transport.calls) == 1
    assert corrected["proposal_correction"]["action_core_digest"] == planned["recovery_plan"]["action_core_digest"]


@pytest.mark.parametrize("fault", ["no-observer", "unknown-adapter", "wrong-state", "wrong-route", "wrong-output", "wrong-report", "wrong-freeze", "wrong-index", "wrong-revision", "wrong-operator", "uncertain-attempt", "earlier-attempt", "unattended", "request-proof", "mixed-finalize"])
def test_correction_refuses_uncertainty_and_untrusted_authority(tmp_path, monkeypatch, fault):
    root, path, _, tracker, transport, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    proof = deepcopy(observer.source_read_back)
    request_data = {}
    context = "interactive"
    if fault == "no-observer":
        observer = None
    elif fault == "unknown-adapter":
        proof["provider_source_sha256"] = "a" * 64
    elif fault == "wrong-state":
        proof["state_digest"] = "a" * 64
    elif fault == "wrong-route":
        proof["route"] = "caller-says-no-write"
    elif fault in {"wrong-output", "wrong-report", "wrong-freeze", "wrong-index"}:
        output = loads_exact(decode_bytes(proof["stdout_raw"]).removesuffix(b"\n"))
        if fault == "wrong-output":
            output["detail"] = "create outcome unknown"
        elif fault == "wrong-report":
            output["report"] = "/another/run.md"
        elif fault == "wrong-freeze":
            output["frozen_snapshot"] = "/another/freeze.json"
        else:
            output["candidate_index"] = []
        changed = dumps(output) + b"\n"
        proof["stdout_raw"] = encode_bytes(changed)
        proof["invocation"]["stdout_sha256"] = digest_bytes(changed)
    elif fault == "wrong-revision":
        proof["invocation"]["revision"] = "a" * 40
    elif fault in {"uncertain-attempt", "earlier-attempt"}:
        state = loads_exact(raw)
        if fault == "uncertain-attempt":
            state["operations"][0]["response"] = {"error": "create outcome unknown"}
            state["attempts"][0]["response"] = state["operations"][0]["response"]
        else:
            state["attempts"].append(deepcopy(state["operations"][0]))
        path.write_bytes(dumps(state))
        raw = path.read_bytes()
        proof["state_digest"] = digest_bytes(raw)
    elif fault == "unattended":
        context = "unattended"
    elif fault == "request-proof":
        request_data = {"rejection_context": proof}
        observer = None
    elif fault == "mixed-finalize":
        request_data = {"finalize": True}
    if observer is not None:
        observer = ApprovalContext(observer.source, "other" if fault == "wrong-operator" else observer.operator_identity, proof)
    result = engine.run("correct-project", context=context, start=root, request=request_data, tracker=tracker, rejection_context=observer)
    assert result["outcome"] in {"operator-held", "hard-stop"}
    assert result["recovery_plan"] is None
    assert path.read_bytes() == raw
    assert not any("mutation " in query for query, _ in transport.calls)


def test_wrong_linear_project_never_publishes_or_enters_attempted_write(tmp_path, monkeypatch):
    root = linear_repo(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    supplied = request(root)
    supplied["proposals"][0]["project"] = "Wrong project"
    result = engine.run("new", context="interactive", start=root, request=supplied)
    assert result["detail"] == "proposal Linear project differs from configured destination"
    path = tmp_path / "state-root/triage/triage-pipeline-state_live.json"
    assert loads_exact(path.read_bytes())["phase"] == "reserved"
    assert not list((root / "reports").glob("*"))
    supplied["proposals"][0]["project"] = "Adopter"
    engine.run("resume", context="interactive", start=root, request=supplied)
    assert loads_exact(path.read_bytes())["phase"] == "awaiting-approval"


def test_wrong_preexisting_approval_stops_before_attempt(tmp_path, monkeypatch):
    root, path, _, tracker, transport, _, raw, old_request, old_context = rejected_run(tmp_path, monkeypatch)
    state = loads_exact(raw)
    state.update(phase="awaiting-approval", approval=None, decisions=[], attempts=[])
    state.pop("operations")
    path.write_bytes(dumps(state))
    transport.calls.clear()
    result = engine.run("resume", context="interactive", start=root, request=old_request, tracker=tracker,
                        approval_context=old_context, head_authority=FakeForge([]))
    assert "before tracker-write" in result["detail"]
    retained = loads_exact(path.read_bytes())
    assert retained["phase"] == "awaiting-approval" and retained["attempts"] == []
    assert transport.calls == []


@pytest.mark.parametrize("marker_kind", ["original", "corrected"])
def test_any_marker_landing_holds_correction_even_after_action_approval(tmp_path, monkeypatch, marker_kind):
    root, path, _, tracker, transport, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    plan, approved_request, approved_context = plan_and_approval(root, tracker, observer)
    if marker_kind == "original":
        proposal = loads_exact(raw)["proposal_payloads"][0]
    else:
        proposal = plan["recovery_plan"]["action_core"]["corrected_proposal_payloads"][0]
    transport.issues.append({
        "id": "foreign", "identifier": "ADO-99", "url": "https://linear.app/w/issue/ADO-99",
        "title": proposal["payload"]["title"], "description": proposal["payload"]["body"],
        "team": {"id": "team"}, "project": {"id": "project", "name": "Adopter"},
        "labels": [{"id": "label", "name": "bug"}],
    })
    result = engine.run("correct-project", context="interactive", start=root, request=approved_request,
                        tracker=tracker, rejection_context=observer, approval_context=approved_context)
    assert "marker reconciliation is not empty" in result["detail"]
    assert path.read_bytes() == raw
    assert not any("mutation " in query for query, _ in transport.calls)


@pytest.mark.parametrize("drift", ["frozen", "configuration", "pagination", "stale-approval", "report"])
def test_correction_revalidates_every_action_binding(tmp_path, monkeypatch, drift):
    root, path, draft, tracker, transport, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved_request, approved_context = plan_and_approval(root, tracker, observer)
    if drift == "frozen":
        Path(draft["frozen_snapshot"]).write_bytes(b"changed")
    elif drift == "configuration":
        config = root / "config/dev-model.yaml"
        config.write_text(config.read_text().replace('project_name: "Adopter"', 'project_name: "Changed"'))
    elif drift == "pagination":
        original = tracker.transport
        def incomplete(query, variables):
            if "TriageIssues(" in query:
                return {"data": {"issues": {"nodes": [], "pageInfo": {"hasNextPage": True, "endCursor": None}}}}
            return original(query, variables)
        tracker.transport = incomplete
    elif drift == "report":
        Path(draft["report"]).write_bytes(b"foreign evidence")
    else:
        approved_request["recovery_approval"]["core_digest"] = "a" * 64
    result = engine.run("correct-project", context="interactive", start=root, request=approved_request,
                        tracker=tracker, rejection_context=observer, approval_context=approved_context)
    assert result["outcome"] == ("hard-stop" if drift == "frozen" else "operator-held")
    assert "applied" not in result["detail"]
    assert path.read_bytes() == raw
    assert not any("mutation " in query for query, _ in transport.calls)


def test_prepared_correction_is_idempotent_after_handled_persist_failure(tmp_path, monkeypatch):
    from triage.model import TriageError

    root, path, _, tracker, transport, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    plan, approved_request, approved_context = plan_and_approval(root, tracker, observer)
    with monkeypatch.context() as patch:
        def refuse(*args, **kwargs):
            raise TriageError("injected persistence hold", outcome="operator-held")
        patch.setattr(engine, "_persist", refuse)
        result = engine.run("correct-project", context="interactive", start=root, request=approved_request,
                            tracker=tracker, rejection_context=observer, approval_context=approved_context)
    assert result["detail"] == "injected persistence hold"
    assert path.read_bytes() == raw
    prepared = path.parent / ("recovery-bundle_live_" + plan["recovery_plan"]["action_core_digest"] + ".json")
    retained = prepared.read_bytes()
    result = engine.run("correct-project", context="interactive", start=root, request=approved_request,
                        tracker=tracker, rejection_context=observer, approval_context=approved_context)
    assert result["detail"] == "project correction applied; complete corrected filing approval is pending"
    assert prepared.read_bytes() == retained
    assert not any("mutation " in query for query, _ in transport.calls)


def test_report_changed_after_state_commit_is_preserved_and_replay_holds(tmp_path, monkeypatch):
    root, path, draft, tracker, _, observer, _, _, _ = rejected_run(tmp_path, monkeypatch)
    plan, approved, context = plan_and_approval(root, tracker, observer)
    report = Path(draft["report"])
    competing = b"competing evidence must survive\n"
    persist = engine._persist
    with monkeypatch.context() as patch:
        def competing_report(*args, **kwargs):
            result = persist(*args, **kwargs)
            report.write_bytes(competing)
            return result
        patch.setattr(engine, "_persist", competing_report)
        result = engine.run("correct-project", context="interactive", start=root, request=approved,
                            tracker=tracker, rejection_context=observer, approval_context=context)
    assert "report changed" in result["detail"]
    retained = path.read_bytes()
    assert canonical_state(retained, settings=load_settings(root), mode="live")["phase"] == "awaiting-approval"
    assert report.read_bytes() == competing
    replay = engine.run("correct-project", context="interactive", start=root, tracker=tracker)
    assert "report changed" in replay["detail"]
    assert path.read_bytes() == retained and report.read_bytes() == competing
    assert decode_bytes(plan["recovery_plan"]["action_core"]["corrected_report_raw"]) != competing


@pytest.mark.parametrize("entry", [None, "resume"])
@pytest.mark.parametrize("approved_filing", [False, True])
def test_ordinary_resume_cannot_bypass_competing_report_hold(tmp_path, monkeypatch, entry, approved_filing):
    root, path, draft, tracker, transport, observer, _, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved, context = plan_and_approval(root, tracker, observer)
    report = Path(draft["report"])
    competing = b"competing evidence must survive\n"
    persist = engine._persist
    with monkeypatch.context() as patch:
        def competing_report(*args, **kwargs):
            result = persist(*args, **kwargs)
            report.write_bytes(competing)
            return result
        patch.setattr(engine, "_persist", competing_report)
        result = engine.run("correct-project", context="interactive", start=root, request=approved,
                            tracker=tracker, rejection_context=observer, approval_context=context)
    assert "report changed" in result["detail"]
    retained = path.read_bytes()
    state = loads_exact(retained)
    result = engine.run(entry, context="interactive", start=root, tracker=tracker, head_authority=FakeForge([]),
                        request={"approval": approval_for(state)} if approved_filing else {},
                        approval_context=approval_context(state) if approved_filing else None)
    assert report.read_bytes() == competing
    assert path.read_bytes() == retained
    assert "report changed" in result["detail"]
    assert not any("mutation " in query for query, _ in transport.calls)


@pytest.mark.parametrize("fault", ["missing", "changed"])
def test_ordinary_resume_checks_prepared_correction_before_filing(tmp_path, monkeypatch, fault):
    root, path, draft, tracker, transport, observer, _, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved, context = plan_and_approval(root, tracker, observer)
    engine.run("correct-project", context="interactive", start=root, request=approved,
               tracker=tracker, rejection_context=observer, approval_context=context)
    retained = path.read_bytes()
    state = loads_exact(retained)
    prepared = path.parent / ("recovery-bundle_live_" + state["proposal_correction"]["action_core_digest"] + ".json")
    if fault == "missing":
        prepared.unlink()
    else:
        prepared.write_bytes(b"changed")
    report = Path(draft["report"]).read_bytes()
    result = engine.run("resume", context="interactive", start=root, tracker=tracker, head_authority=FakeForge([]),
                        request={"approval": approval_for(state)}, approval_context=approval_context(state))
    assert "prepared receipt changed or is missing" in result["detail"]
    assert path.read_bytes() == retained and Path(draft["report"]).read_bytes() == report
    assert not any("mutation " in query for query, _ in transport.calls)


@pytest.mark.parametrize("fault", ["state-bytes", "report-bytes", "corrected-report", "observer", "project-and-rehash", "title-and-rehash", "approval-reuse"])
def test_receipt_revalidates_retained_history_and_intent(tmp_path, monkeypatch, fault):
    from triage.model import TriageError

    root, path, _, tracker, _, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved, context = plan_and_approval(root, tracker, observer)
    engine.run("correct-project", context="interactive", start=root, request=approved,
               tracker=tracker, rejection_context=observer, approval_context=context)
    state = loads_exact(path.read_bytes())
    receipt = state["proposal_correction"]
    core = receipt["action_core"]
    if fault in {"state-bytes", "report-bytes", "corrected-report"}:
        field = {"state-bytes": "captured_state_raw", "report-bytes": "captured_report_raw", "corrected-report": "corrected_report_raw"}[fault]
        core[field] = encode_bytes(b"forged")
    elif fault == "observer":
        core["rejection_observer"]["source_read_back"]["provider_source_sha256"] = "a" * 64
    elif fault in {"project-and-rehash", "title-and-rehash"}:
        core["corrected_proposal_payloads"][0]["payload_core"]["project" if fault.startswith("project") else "title"] = "Changed"
    else:
        state["approval"] = loads_exact(raw)["approval"]
    # Outer digest consistency cannot replace the original history/intents.
    receipt["action_core_digest"] = digest(core)
    receipt["approval"]["core_digest"] = digest(core)
    with pytest.raises(TriageError):
        canonical_state(dumps(state), settings=load_settings(root), mode="live")


def test_project_only_correction_refuses_body_modification_before_rebinding(tmp_path, monkeypatch):
    root, path, draft, tracker, _, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved, context = plan_and_approval(root, tracker, observer)
    engine.run("correct-project", context="interactive", start=root, request=approved,
               tracker=tracker, rejection_context=observer, approval_context=context)
    state = loads_exact(path.read_bytes())
    retained = path.read_bytes()
    report = Path(draft["report"]).read_bytes()
    changed = engine.run("resume", context="interactive", start=root,
                         request={"approval": {"command": "modify TRI-01: corrected details", "proposal_set_digest": digest(state["proposal_payload_digests"])}},
                         approval_context=approval_context(state, "modify TRI-01: corrected details"))
    assert changed["outcome"] == "operator-held"
    assert "modify is unavailable" in changed["detail"]
    assert path.read_bytes() == retained and Path(draft["report"]).read_bytes() == report
    assert decode_bytes(state["proposal_correction"]["action_core"]["captured_state_raw"]) == raw
    engine.run("correct-project", context="interactive", start=root, tracker=tracker)
    assert Path(draft["report"]).read_bytes() == report


@pytest.mark.parametrize("fault", ["unrelated-program", "unrelated-interpreter", "relative-interpreter", "contradictory-context", "duplicate-flag", "missing-context", "different-entry", "relative-request"])
def test_rejection_observer_binds_the_exact_normalized_installed_cli_route(tmp_path, monkeypatch, fault):
    root, path, draft, tracker, transport, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch)
    command = observer.source_read_back["invocation"]["command"]
    if fault == "unrelated-program":
        command[1] = str(root / "unrelated-program.py")
    elif fault == "unrelated-interpreter":
        command[0] = "/usr/bin/true"
    elif fault == "relative-interpreter":
        command[0] = "python"
    elif fault == "contradictory-context":
        command[4] = "unattended"
    elif fault == "duplicate-flag":
        command.append("--enable-tracker")
    elif fault == "missing-context":
        del command[3:5]
    elif fault == "different-entry":
        command[2] = "new"
    else:
        command[6] = "request.json"
    report = Path(draft["report"]).read_bytes()
    calls = list(transport.calls)
    result = engine.run("correct-project", context="interactive", start=root, tracker=tracker, rejection_context=observer)
    assert result["recovery_plan"] is None and "installed route" in result["detail"]
    assert path.read_bytes() == raw and Path(draft["report"]).read_bytes() == report
    assert transport.calls == calls


def test_corrected_report_remains_immutable_through_noop_and_filing(tmp_path, monkeypatch):
    root, path, draft, tracker, transport, observer, _, _, _ = rejected_run(tmp_path, monkeypatch)
    _, approved, context = plan_and_approval(root, tracker, observer)
    engine.run("correct-project", context="interactive", start=root, request=approved,
               tracker=tracker, rejection_context=observer, approval_context=context)
    report = Path(draft["report"])
    presentation = report.read_bytes()
    for _ in range(2):
        result = engine.run("resume", context="interactive", start=root, tracker=tracker)
        assert result["detail"] == "active session resumed" and report.read_bytes() == presentation
    state = loads_exact(path.read_bytes())
    result = engine.run("resume", context="interactive", start=root, tracker=tracker, head_authority=FakeForge([]),
                        request={"approval": approval_for(state)}, approval_context=approval_context(state))
    assert result["verified_tracker_identifiers"] == ["ADO-17"]
    assert report.read_bytes() == presentation
    report.write_bytes(b"independent evidence after filing\n")
    retained = path.read_bytes()
    calls = list(transport.calls)
    replay = engine.run("resume", context="interactive", start=root, tracker=tracker)
    assert "report changed" in replay["detail"]
    assert path.read_bytes() == retained and report.read_bytes() == b"independent evidence after filing\n"
    assert transport.calls == calls


def installed_cli(root, tmp_path, *, entry="correct-project", request_data=None, context=None, observer=None, cutpoint="none"):
    argv = [entry, "--context", "interactive"]
    for flag, value in (("--request", request_data), ("--approval-context", context), ("--rejection-context", observer)):
        if value is not None:
            path = tmp_path / (flag.removeprefix("--") + ".json")
            path.write_bytes(dumps(value))
            argv.extend([flag, str(path)])
    if entry == "correct-project":
        argv.append("--enable-tracker")
    # Run the installed CLI in a separate process. Its real engine, persistence,
    # owner record and recovery logic execute; only the service transport and
    # deliberate termination cutpoint are substituted.
    program = r'''
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "scripts"))
import triage_friction_log as cli
sys.path.insert(0, sys.argv[1])
from test_triage_providers import LinearTransport
from triage import engine
from triage.providers import LinearIssues
from triage.canonical import dumps
transport = LinearTransport()
def read_only(query, variables):
    with open(sys.argv[3], "ab") as stream:
        stream.write(dumps({"query": query}) + b"\n")
    assert "mutation " not in query, "correction must never mutate a tracker"
    return transport(query, variables)
cli.LinearIssues = lambda: LinearIssues(transport=read_only, sleep=lambda _: None)
persist = engine._persist
def terminated(*args, **kwargs):
    if args[2].get("proposal_correction"):
        if sys.argv[2] == "before-state":
            os._exit(73)
        result = persist(*args, **kwargs)
        if sys.argv[2] == "after-state":
            os._exit(73)
        return result
    return persist(*args, **kwargs)
engine._persist = terminated
raise SystemExit(cli.main(sys.argv[4:]))
'''
    return subprocess.run(
        [sys.executable, "-c", program, str(Path(__file__).parent), cutpoint, str(tmp_path / "transport-calls.jsonl"), *argv],
        cwd=root, env=os.environ.copy(), capture_output=True, text=True, timeout=30,
    )


@pytest.mark.parametrize("cutpoint", ["before-state", "after-state"])
def test_installed_cli_crash_requires_dead_owner_recovery_then_retries_exact_cutpoint(tmp_path, monkeypatch, cutpoint):
    root, path, draft, tracker, _, observer, raw, _, _ = rejected_run(tmp_path, monkeypatch, installed=True)
    plan, approved, context = plan_and_approval(root, tracker, observer)
    report = Path(draft["report"])
    original_report = report.read_bytes()
    observed = {"source": observer.source, "operator_identity": observer.operator_identity, "source_read_back": observer.source_read_back}
    action_context = {"source": context.source, "operator_identity": context.operator_identity, "source_read_back": context.source_read_back}
    killed = installed_cli(root, tmp_path, request_data=approved, context=action_context, observer=observed, cutpoint=cutpoint)
    assert killed.returncode == 73, killed.stderr
    gate = path.parent / "triage-pipeline-gate_live.lock"
    gate_raw = gate.read_bytes()
    committed = path.read_bytes()
    assert (committed == raw) == (cutpoint == "before-state")
    assert report.read_bytes() == original_report
    blocked = installed_cli(root, tmp_path, request_data=approved, context=action_context, observer=observed)
    assert "proven-dead owner" in loads_exact(blocked.stdout.strip().encode())["resume_action"]
    assert gate.read_bytes() == gate_raw and path.read_bytes() == committed
    recovery = installed_cli(root, tmp_path, entry="recover")
    recovery_plan = loads_exact(recovery.stdout.strip().encode())["recovery_plan"]
    assert recovery_plan["action_core"]["action"] == "preserve-valid-state-and-quarantine-old-gate"
    approval = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": recovery_plan["action_core_digest"]}
    recovered = installed_cli(root, tmp_path, entry="recover", request_data={"recovery_approval": approval},
                              context={"source": "current-session", "operator_identity": "operator", "source_read_back": approval})
    assert loads_exact(recovered.stdout.strip().encode())["detail"] == "resume"
    assert path.read_bytes() == committed and not gate.exists()
    assert gate.with_name(gate.name + ".quarantine-" + digest_bytes(gate_raw)[:16]).read_bytes() == gate_raw
    replay = installed_cli(root, tmp_path, request_data=approved, context=action_context, observer=observed)
    result = loads_exact(replay.stdout.strip().encode())
    assert ("applied;" if cutpoint == "before-state" else "already applied") in result["detail"]
    corrected = canonical_state(path.read_bytes(), settings=load_settings(root), mode="live")
    assert corrected["approval"] is None and corrected["phase"] == "awaiting-approval"
    core = corrected["proposal_correction"]["action_core"]
    assert core == plan["recovery_plan"]["action_core"]
    assert report.read_bytes() == decode_bytes(core["corrected_report_raw"])
    assert decode_bytes(core["captured_state_raw"]) == raw
    assert "mutation " not in (tmp_path / "transport-calls.jsonl").read_text()
