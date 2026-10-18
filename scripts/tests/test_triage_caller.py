"""Scheduled dispatch is bound to a retained caller attempt before it can act."""

from __future__ import annotations

import importlib.util
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_triage_outcome_receipts import ENGINE_DIR, result  # noqa: E402
from triage.caller import (  # noqa: E402
    ATTEMPT_ENV,
    RUN_ENV,
    SCHEDULED_ENV,
    check_run,
    create_run,
    prepare_attempt,
    read_attempt,
    record_exit,
)
from triage.canonical import dumps  # noqa: E402
from triage.model import TriageError  # noqa: E402


@pytest.fixture(autouse=True)
def caller_environment(monkeypatch):
    for key in (*SCHEDULED_ENV, "DEVKIT_TRIAGE_OUTCOME_RECEIPT", "DEVKIT_TRIAGE_INVOCATION_ID"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def cli():
    spec = importlib.util.spec_from_file_location("triage_caller_cli", ENGINE_DIR / "triage_friction_log.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def caller(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "caller"
    create_run(root)
    monkeypatch.setenv(RUN_ENV, str(root))
    return root


def arguments(root, attempt, *, entry="resume"):
    expected = read_attempt(root, attempt)
    return ([entry] if entry is not None else []) + [
        "--context", "unattended", "--caller-attempt", str(attempt),
        "--invocation-id", expected["invocation_id"], "--outcome-receipt", expected["outcome_receipt"],
    ]


@pytest.mark.parametrize("marker", ["JOB_NAME", "AUTOMATION_RUN_ID", RUN_ENV, ATTEMPT_ENV, "unattended"])
@pytest.mark.parametrize("default", [None, "resume"])
def test_scheduled_markers_require_caller_before_dispatch(cli, monkeypatch, marker, default):
    monkeypatch.setattr(cli, "run", lambda *a, **kw: pytest.fail("unbound transition"))
    argv = ["--context", "unattended"] if marker == "unattended" else []
    if marker != "unattended":
        monkeypatch.setenv(marker, "")  # presence, including malformed/empty, fails closed
    assert cli.main(argv, default_entry=default) == 2


def test_interactive_calls_remain_compatible(cli, monkeypatch):
    monkeypatch.setattr(cli, "run", lambda *a, **kw: result())
    assert cli.main(["resume"]) == 0


@pytest.mark.parametrize("entry", [None, "resume", "new", "test", "recover"])
def test_bound_call_and_environment_transport(caller, cli, monkeypatch, entry):
    attempt = prepare_attempt(caller, entry=entry)
    argv = arguments(caller, attempt, entry=entry)
    monkeypatch.setenv(ATTEMPT_ENV, str(attempt))
    offset = argv.index("--caller-attempt")
    del argv[offset:offset + 2]
    monkeypatch.setattr(cli, "run", lambda *a, **kw: result())
    status = cli.main(argv)
    record_exit(caller, attempt, status)
    assert status == 0
    assert check_run(caller)[0]["verdict"] == "completed"


@pytest.mark.parametrize("mutation", ["entry", "context", "id", "receipt", "foreign", "replay"])
def test_mismatched_or_replayed_attempt_cannot_dispatch(caller, tmp_path, cli, monkeypatch, mutation):
    attempt = prepare_attempt(caller, entry="resume")
    argv = arguments(caller, attempt)
    if mutation == "entry":
        argv[0] = "new"
    elif mutation == "context":
        argv[argv.index("--context") + 1] = "interactive"
    elif mutation == "id":
        argv[argv.index("--invocation-id") + 1] = "another-call"
    elif mutation == "receipt":
        argv[argv.index("--outcome-receipt") + 1] = str(tmp_path / "other.json")
    elif mutation == "foreign":
        other = tmp_path / "other"
        create_run(other)
        foreign = prepare_attempt(other, entry="resume")
        argv = arguments(other, foreign)
    else:
        # Claim without publishing, as if the original process died.
        from triage.caller import enforce_attempt
        expected = read_attempt(caller, attempt)
        enforce_attempt(attempt=attempt, receipt=Path(expected["outcome_receipt"]),
                        invocation_id=expected["invocation_id"], entry="resume", context="unattended")
    monkeypatch.setattr(cli, "run", lambda *a, **kw: pytest.fail("invalid attempt dispatched"))
    assert cli.main(argv) == 2
    with pytest.raises(TriageError):
        check_run(caller)


@pytest.mark.parametrize("failure", ["parse", "request", "engine", "receipt", "status", "missing-status", "mode"])
def test_failed_call_cannot_be_hidden_by_successful_retry(caller, cli, monkeypatch, failure):
    attempt = prepare_attempt(caller, entry="resume")
    argv = arguments(caller, attempt)
    if failure == "parse":
        argv.append("--not-a-flag")
    elif failure == "request":
        argv.extend(["--request", str(caller / "missing")])
    def transition(*args, **kwargs):
        if failure == "receipt":
            (attempt.parent / "outcome.json").write_bytes(b"occupied")
        return result("hard-stop", refusal_code="active-state") if failure == "engine" else result(mode="test" if failure == "mode" else "live")
    monkeypatch.setattr(cli, "run", transition)
    status = cli.main(argv)
    if failure != "missing-status":
        record_exit(caller, attempt, -9 if failure == "status" else status)
    retry = prepare_attempt(caller, entry="resume")
    monkeypatch.setattr(cli, "run", lambda *a, **kw: result())
    record_exit(caller, retry, cli.main(arguments(caller, retry)))
    with pytest.raises((TriageError, ValueError, OSError)):
        check_run(caller)


def test_wait_is_preserved_for_callers_job_policy(caller, cli, monkeypatch):
    attempt = prepare_attempt(caller, entry="resume")
    monkeypatch.setattr(cli, "run", lambda *a, **kw: result("operator-held", waiting_on="approval"))
    record_exit(caller, attempt, cli.main(arguments(caller, attempt)))
    checked = check_run(caller)[0]
    assert checked["verdict"] == "waiting"
    assert checked["waiting_on"] == "approval"


@pytest.mark.parametrize("shape", ["no-calls", "unclaimed", "symlink", "hardlink", "malformed", "foreign-run"])
def test_missing_or_unsafe_caller_evidence_refuses(caller, tmp_path, shape):
    if shape != "no-calls":
        attempt = prepare_attempt(caller, entry="resume")
        original = attempt.read_bytes()
        if shape in ("symlink", "hardlink"):
            target = tmp_path / "keep.json"
            target.write_bytes(original)
            attempt.unlink()
            if shape == "symlink":
                attempt.symlink_to(target)
            else:
                os.link(target, attempt)
        elif shape == "malformed":
            attempt.write_bytes(b"{}")
        elif shape == "foreign-run":
            expected = read_attempt(caller, attempt)
            expected["run_id"] = "another-run"
            attempt.write_bytes(dumps(expected))
    with pytest.raises((TriageError, OSError, ValueError)):
        check_run(caller)


# Exercise the actual entrypoint scripts in child processes. Only the engine
# transition is replaced; parser, caller guard and receipt publication are real.
BOOTSTRAP = '''
import runpy, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent / "lib"))
sys.path.insert(0, str(Path(sys.argv[1]).parent))
import triage.engine
behavior = sys.argv[2]
def transition(*args, **kwargs):
    print("engine-entered", file=sys.stderr, flush=True)
    if behavior == "wait":
        time.sleep(60)
    return {"outcome": "successful-completion", "execution_mode": "live",
            "disposition": "completed", "waiting_on": None, "refusal_code": None}
triage.engine.run = transition
engine = sys.argv[1]
sys.argv = [engine, *sys.argv[3:]]
runpy.run_path(engine, run_name="__main__")
'''


@pytest.mark.parametrize("engine", ["triage_friction_log.py", "finalize_triage.py"])
def test_direct_then_instrumented_sequence_fails_run(caller, engine):
    command = [sys.executable, "-c", BOOTSTRAP, str(ENGINE_DIR / engine), "return"]
    direct = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert direct.returncode == 2
    assert "engine-entered" not in direct.stderr
    attempt = prepare_attempt(caller, entry="resume")
    invoked = subprocess.run([*command, *arguments(caller, attempt)], capture_output=True, text=True, timeout=15)
    record_exit(caller, attempt, invoked.returncode)
    assert invoked.returncode == 0, invoked.stderr
    assert "engine-entered" in invoked.stderr
    with pytest.raises(TriageError, match="rejected"):
        check_run(caller)


@pytest.mark.parametrize("engine", ["triage_friction_log.py", "finalize_triage.py"])
def test_interrupted_bound_process_leaves_failed_attempt(caller, engine):
    attempt = prepare_attempt(caller, entry="resume")
    child = subprocess.Popen([sys.executable, "-u", "-c", BOOTSTRAP, str(ENGINE_DIR / engine),
                              "wait", *arguments(caller, attempt)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([child.stderr], [], [], 15)[0]
        assert child.stderr.readline().strip() == "engine-entered"
        child.kill()
        child.communicate(timeout=15)
        record_exit(caller, attempt, child.returncode)
        assert not (attempt.parent / "outcome.json").exists()
        with pytest.raises(TriageError, match="failed or was interrupted"):
            check_run(caller)
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=15)
