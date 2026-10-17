"""Caller-owned freshness and write-once outcome evidence for scheduled triage."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402
from test_triage_engine import change_config, repository, request  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))
from triage.canonical import digest, dumps, loads_exact  # noqa: E402
from triage.model import TriageError  # noqa: E402
from triage.outcome import (  # noqa: E402
    check_receipt,
    disposition_fields,
    preflight_receipt,
    write_receipt,
)


@pytest.fixture
def cli(monkeypatch):
    for key in ("DEVKIT_TRIAGE_OUTCOME_RECEIPT", "DEVKIT_TRIAGE_INVOCATION_ID"):
        monkeypatch.delenv(key, raising=False)
    spec = importlib.util.spec_from_file_location("triage_receipt_cli", ENGINE_DIR / "triage_friction_log.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def result(outcome="successful-completion", *, waiting_on=None, refusal_code=None, mode="live"):
    return {"outcome": outcome, "execution_mode": mode,
            **disposition_fields(outcome, waiting_on=waiting_on, refusal_code=refusal_code)}


def publish(path, payload=None, **kwargs):
    write_receipt(path, result() if payload is None else payload,
                  **{"invocation_id": "call-a", "entry": "resume", "context": "unattended", **kwargs})


def check(path, **kwargs):
    return check_receipt(path, **{"invocation_id": "call-a", "entry": "resume", "context": "unattended", "mode": "live", **kwargs})


def check_args(path):
    return ["--check-outcome-receipt", str(path), "--invocation-id", "call-a",
            "--expect-entry", "resume", "--expect-context", "unattended", "--expect-mode", "live"]


@pytest.mark.parametrize("payload,verdict", [
    (result(), "completed"),
    (result("degraded-success"), "completed"),
    (result("operator-held", waiting_on="approval"), "waiting"),
    (result("operator-held", waiting_on="reconciliation"), "waiting"),
    (result("operator-held", refusal_code="configuration-identity"), "refused"),
    (result("hard-stop", refusal_code="repository-identity", mode="unknown"), "refused"),
])
def test_classifies_derived_results(tmp_path, cli, capsys, payload, verdict):
    path = tmp_path / "receipt.json"
    publish(path, payload)
    assert check(path)["verdict"] == verdict
    assert cli.main(check_args(path)) == (1 if verdict == "refused" else 0)
    assert loads_exact(capsys.readouterr().out.strip().encode())["verdict"] == verdict


def test_missing_stale_and_wrong_invocation_are_distinct(tmp_path):
    path = tmp_path / "receipt.json"
    assert check(path)["verdict"] == "evidence-missing"
    publish(path)
    assert check(path, invocation_id="next-call")["verdict"] == "evidence-stale"
    for expectation in ({"entry": "new"}, {"context": "interactive"}, {"mode": "test"}):
        assert check(path, **expectation)["verdict"] == "evidence-wrong-invocation"


@pytest.mark.parametrize("field,value", [
    ("kind", "foreign"), ("schema_version", True), ("schema_version", 2),
    ("invocation_id", ""), ("entry", "foreign"), ("context", None),
    ("result_digest", "wrong"), ("result", []),
])
def test_rejects_malformed_envelope(tmp_path, field, value):
    path = tmp_path / "receipt.json"
    publish(path)
    receipt = loads_exact(path.read_bytes())
    receipt[field] = value
    path.write_bytes(dumps(receipt))
    assert check(path)["verdict"] == "evidence-malformed"


@pytest.mark.parametrize("change", [
    {"outcome": "invented"}, {"disposition": "waiting"}, {"waiting_on": "approval"},
    {"refusal_code": "repository-identity"}, {"execution_mode": "unknown"},
    {"outcome": [], "disposition": {}}, {"execution_mode": []},
])
def test_digest_alone_does_not_authorize_inconsistent_result(tmp_path, change):
    path = tmp_path / "receipt.json"
    publish(path)
    receipt = loads_exact(path.read_bytes())
    receipt["result"].update(change)
    receipt["result_digest"] = digest(receipt["result"])
    path.write_bytes(dumps(receipt))
    assert check(path)["verdict"] == "evidence-malformed"


@pytest.mark.parametrize("raw", [b"not json", b"{}\n", b"[]", b'{"extra":true}'])
def test_unreadable_evidence_never_reports_success(tmp_path, raw):
    path = tmp_path / "receipt.json"
    path.write_bytes(raw)
    assert check(path)["verdict"] == "evidence-malformed"


@pytest.mark.parametrize("shape", ["file", "receipt", "symlink", "hardlink", "directory", "ancestor-symlink"])
def test_publication_and_preflight_preserve_occupied_or_aliased_targets(tmp_path, shape):
    victim = tmp_path / "victim"
    victim.write_bytes(b"preserve me")
    path = tmp_path / "receipt.json"
    if shape == "file":
        path.write_bytes(b"foreign")
    elif shape == "receipt":
        publish(path)
    elif shape == "symlink":
        path.symlink_to(victim)
    elif shape == "hardlink":
        os.link(victim, path)
    elif shape == "directory":
        path.mkdir()
    else:
        (tmp_path / "alias").symlink_to(tmp_path, target_is_directory=True)
        path = tmp_path / "alias/receipt.json"
    before = path.read_bytes() if path.is_file() else None
    for operation in (lambda: preflight_receipt(path, "new-call"), lambda: publish(path, invocation_id="new-call")):
        with pytest.raises((OSError, TriageError)):
            operation()
        assert victim.read_bytes() == b"preserve me"
        if before is not None:
            assert path.read_bytes() == before


def test_target_occupied_during_engine_call_is_not_overwritten(tmp_path, cli, monkeypatch, capsys):
    path = tmp_path / "receipt.json"
    def run(*args, **kwargs):
        path.write_bytes(b"another writer")
        return result()
    monkeypatch.setattr(cli, "run", run)
    assert cli.main(["resume", "--outcome-receipt", str(path), "--invocation-id", "call-a"]) == 2
    output = capsys.readouterr()
    assert loads_exact(output.out.strip().encode())["disposition"] == "completed"
    assert "outcome receipt not written" in output.err
    assert path.read_bytes() == b"another writer"


@pytest.mark.parametrize("arguments", [
    ["--help"], ["--invocation-id"], ["--outcome-receipt"],
    ["--check-outcome-receipt"], ["--check-outcome-receipt", "--unknown"],
    ["--expect-mode", "live"], ["--check-outcome-receipt", "missing", "--context", "unattended"],
])
def test_help_and_invalid_arguments_never_mutate_receipts(tmp_path, cli, monkeypatch, arguments):
    path = tmp_path / "receipt.json"
    publish(path)
    before = path.read_bytes()
    monkeypatch.setenv("DEVKIT_TRIAGE_OUTCOME_RECEIPT", str(path))
    monkeypatch.setenv("DEVKIT_TRIAGE_INVOCATION_ID", "call-a")
    monkeypatch.setattr(cli, "run", lambda *a, **kw: pytest.fail("must not invoke engine"))
    if arguments == ["--help"]:
        with pytest.raises(SystemExit) as exc:
            cli.main(arguments)
        assert exc.value.code == 0
    else:
        assert cli.main(arguments) == 2
    assert path.read_bytes() == before


@pytest.mark.parametrize("extra", [[], ["resume"], ["--context", "interactive"], ["--enable-tracker"],
                                    ["--enable-github-tracker"], ["--enable-github-forge"], ["--request", "missing"],
                                    ["--approval-context", "missing"], ["--outcome-receipt", "missing"]])
def test_checks_ignore_publishing_environment_and_reject_execution_flags(tmp_path, cli, monkeypatch, extra):
    path = tmp_path / "receipt.json"
    publish(path)
    before = path.read_bytes()
    target = tmp_path / "must-not-create"
    monkeypatch.setenv("DEVKIT_TRIAGE_OUTCOME_RECEIPT", str(target))
    monkeypatch.setattr(cli, "run", lambda *a, **kw: pytest.fail("check must not invoke engine"))
    assert cli.main([*check_args(path), *extra]) == (2 if extra else 0)
    assert path.read_bytes() == before
    assert not target.exists()


def test_environment_transport_and_explicit_override(tmp_path, cli, monkeypatch, capsys):
    env_path = tmp_path / "env.json"
    path = tmp_path / "flag.json"
    monkeypatch.setenv("DEVKIT_TRIAGE_OUTCOME_RECEIPT", str(env_path))
    monkeypatch.setenv("DEVKIT_TRIAGE_INVOCATION_ID", "env-id")
    monkeypatch.setattr(cli, "run", lambda *a, **kw: result())
    assert cli.main(["resume"]) == 0
    assert check(env_path, invocation_id="env-id", context="interactive")["verdict"] == "completed"
    assert cli.main(["resume", "--outcome-receipt", str(path), "--invocation-id", "call-a"]) == 0
    assert check(path, context="interactive")["verdict"] == "completed"


def test_request_refusal_is_recorded_but_parse_failure_leaves_no_new_receipt(tmp_path, cli, capsys):
    path = tmp_path / "receipt.json"
    assert cli.main(["resume", "--request", str(tmp_path / "missing"), "--outcome-receipt", str(path), "--invocation-id", "call-a"]) == 2
    assert check(path, context="interactive")["refusal_code"] == "invalid-invocation"
    old = path.read_bytes()
    # The next call's identity was chosen BEFORE dispatch. Keeping an old file
    # cannot turn a malformed invocation into successful evidence for that id.
    assert cli.main(["--outcome-receipt", str(path), "--invocation-id", "next-call", "--context"]) == 2
    assert path.read_bytes() == old
    assert check(path, invocation_id="next-call")["verdict"] == "evidence-stale"


def test_real_engine_wait_noop_and_configuration_refusal(tmp_path, cli, monkeypatch, capsys):
    root = repository(tmp_path)
    monkeypatch.setattr(cli, "__file__", str(root / "scripts/triage_friction_log.py"))
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state"))
    request_path = tmp_path / "request.json"
    request_path.write_bytes(dumps(request(root)))
    first = tmp_path / "first.json"
    assert cli.main(["new", "--request", str(request_path), "--outcome-receipt", str(first), "--invocation-id", "call-a"]) == 0
    assert check(first, entry="new", context="interactive")["waiting_on"] == "approval"
    change_config(root)
    second = tmp_path / "second.json"
    assert cli.main(["resume", "--outcome-receipt", str(second), "--invocation-id", "call-b"]) == 0
    assert check(second, invocation_id="call-b", context="interactive")["refusal_code"] == "configuration-identity"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "empty-state"))
    (root / "docs/kit-friction-log.md").write_text("# Empty inbox\n")
    third = tmp_path / "third.json"
    assert cli.main(["new", "--outcome-receipt", str(third), "--invocation-id", "call-c"]) == 0
    assert check(third, invocation_id="call-c", entry="new", context="interactive")["verdict"] == "completed"


def test_finalization_check_does_not_inject_resume(tmp_path):
    path = tmp_path / "receipt.json"
    publish(path)
    completed = subprocess.run([sys.executable, str(ENGINE_DIR / "finalize_triage.py"), *check_args(path)],
                               capture_output=True, text=True, timeout=15)
    assert completed.returncode == 0, completed.stderr
    assert loads_exact(completed.stdout.strip().encode())["verdict"] == "completed"


def test_killed_cli_cannot_reuse_an_earlier_calls_receipt(tmp_path):
    old = tmp_path / "old.json"
    publish(old)
    path = tmp_path / "new.json"
    # Exercise the process boundary: stop inside an engine invocation, after
    # parsing and receipt preflight but before it can return an outcome.
    bootstrap = '''
import importlib.util, sys, time
spec = importlib.util.spec_from_file_location("cli", sys.argv[1])
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
def waiting(*args, **kwargs):
    print("engine-entered", flush=True)
    time.sleep(60)
cli.run = waiting
raise SystemExit(cli.main(sys.argv[2:]))
'''
    child = subprocess.Popen([sys.executable, "-u", "-c", bootstrap, str(ENGINE_DIR / "triage_friction_log.py"),
                              "resume", "--outcome-receipt", str(path), "--invocation-id", "next-call"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        import select
        ready, _, _ = select.select([child.stdout], [], [], 15)
        assert ready, "child did not reach the engine"
        assert child.stdout.readline().strip() == "engine-entered"
        child.kill()
        child.communicate(timeout=15)
        assert child.returncode != 0
        assert check(path, invocation_id="next-call")["verdict"] == "evidence-missing"
        assert check(old, invocation_id="next-call")["verdict"] == "evidence-stale"
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=15)
