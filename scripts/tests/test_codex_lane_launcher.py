from __future__ import annotations

import contextlib
import copy
import datetime as dt
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _load_launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "launch_codex_lane", ENGINE_DIR / "launch_codex_lane.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _fake_codex(
    path: Path,
    *,
    sleep: bool = False,
    write_final: bool = True,
    corrupt_receipt: bool = False,
    ignore_sigterm: bool = False,
    spawn_descendant: bool = False,
) -> None:
    sleep_line = "time.sleep(60)" if sleep else ""
    ignore_line = "signal.signal(signal.SIGTERM, signal.SIG_IGN)" if ignore_sigterm else ""
    corrupt_line = (
        "[p.write_text('{}\\n', encoding='utf-8') for p in Path.cwd().parent.glob('launch-receipt-*.json')]"
        if corrupt_receipt
        else ""
    )
    final_line = (
        "Path(output).write_text(json.dumps(result, sort_keys=True), encoding='utf-8')"
        if write_final
        else "pass"
    )
    descendant_line = (
        "child = subprocess.Popen([sys.executable, '-c', "
        "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)']); "
        "Path.cwd().parent.joinpath('descendant.pid').write_text(str(child.pid), encoding='utf-8')"
        if spawn_descendant
        else ""
    )
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, signal, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "output = args[args.index('--output-last-message') + 1]\n"
        "prompt = sys.stdin.read()\n"
        "result = {\n"
        "  'cwd': str(Path.cwd().resolve()),\n"
        "  'branch': subprocess.run(['git','branch','--show-current'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'push_url': subprocess.run(['git','remote','get-url','--push','origin'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'env': {k: v for k, v in os.environ.items() if k.startswith('DEVKIT_')},\n"
        "  'gh_repo_present': 'GH_REPO' in os.environ,\n"
        "  'git_work_tree_present': 'GIT_WORK_TREE' in os.environ,\n"
        "  'git_config_present': any(k == 'GIT_CONFIG' or k.startswith('GIT_CONFIG_') for k in os.environ),\n"
        "  'contract_first': prompt.startswith('LANE CONTRACT (binding):'),\n"
        "  'pid': os.getpid(),\n"
        "}\n"
        f"{ignore_line}\n"
        f"{descendant_line}\n"
        f"{corrupt_line}\n"
        f"{final_line}\n"
        f"{sleep_line}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _install_repo(
    tmp_path: Path,
    *,
    sleep: bool = False,
    write_final: bool = True,
    corrupt_receipt: bool = False,
    ignore_sigterm: bool = False,
    spawn_descendant: bool = False,
):
    remote = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )
    repo = tmp_path / "project"
    repo.mkdir()
    _git(repo, "init", "-b", "trunk")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    (repo / ".gitignore").write_text(
        "state/\n.devkit_state_root\nconfig/*.local.yaml\n", encoding="utf-8"
    )
    _git(repo, "add", "README.md", ".gitignore")
    _git(repo, "commit", "-m", "seed")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "trunk")
    engine_dir = repo / "scripts" / "devkit"
    shutil.copytree(ENGINE_DIR, engine_dir)
    fake_codex = tmp_path / "fake-codex"
    _fake_codex(
        fake_codex,
        sleep=sleep,
        write_final=write_final,
        corrupt_receipt=corrupt_receipt,
        ignore_sigterm=ignore_sigterm,
        spawn_descendant=spawn_descendant,
    )
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text(
        "paths:\n"
        "  handoff: handoff.md\n"
        "  friction_log: friction-log.md\n"
        "runtime:\n"
        "  default: codex\n"
        "  launchers:\n"
        "    codex: codex\n"
        "parallel:\n"
        f"  codex_headless_command: [{json.dumps(str(fake_codex))}]\n"
        "  descriptor_ttl_seconds: 900\n"
        "  observation_timeout_seconds: 5\n"
        "  termination_grace_seconds: 1\n"
        "vcs:\n"
        "  protected_branch: trunk\n"
        "  dev_branch_prefix: lane\n",
        encoding="utf-8",
    )
    sessions = tmp_path / "sessions"
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    created = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "new",
            "probe",
            "--headless",
            "--runtime",
            "codex",
        ],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    descriptor = json.loads(created.stdout)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Inspect the lane and return the requested identity.\n", encoding="utf-8")
    return repo, engine_dir, sessions, descriptor, prompt, env


def _run_launcher(
    engine_dir: Path,
    descriptor: dict[str, object],
    prompt: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(engine_dir / "launch_codex_lane.py"),
            "--descriptor",
            str(descriptor["descriptor_path"]),
            "--prompt-file",
            str(prompt),
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_supported_launcher_replaces_inherited_identity_and_binds_observation(
    tmp_path: Path,
) -> None:
    repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    inherited = {
        **env,
        "DEVKIT_STATE_ROOT": str(tmp_path / "foreign-state"),
        "DEVKIT_ROOT": str(tmp_path / "foreign-repo"),
        "DEVKIT_FOREIGN_LANE": "must-be-removed",
        "GH_REPO": "foreign/project",
        "GIT_WORK_TREE": str(tmp_path / "foreign-worktree"),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "remote.origin.pushurl",
        "GIT_CONFIG_VALUE_0": str(tmp_path / "foreign-origin"),
    }

    result = _run_launcher(engine_dir, descriptor, prompt, inherited)

    assert result.returncode == 0, result.stderr
    receipt_path = sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    final_path = Path(receipt["terminal"]["final_message_path"])
    final = json.loads(final_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "completed"
    assert receipt["expected"] is not receipt["observed"]
    assert receipt["expected"]["environment"] == descriptor["env"]
    assert receipt["observed"]["environment"] == descriptor["env"]
    assert receipt["observed"]["worktree"] == descriptor["worktree"]
    assert receipt["observed"]["repo_root"] == str(repo)
    assert final["cwd"] == descriptor["worktree"]
    assert final["branch"] == descriptor["branch"]
    assert final["env"] == descriptor["env"]
    assert final["gh_repo_present"] is False
    assert final["git_work_tree_present"] is False
    assert final["git_config_present"] is False
    assert final["push_url"] == descriptor["origin_push_url"]
    assert final["contract_first"] is True
    assert receipt["terminal"]["final_message_sha256"]


def test_correct_descriptor_cannot_launch_in_a_wrong_worktree() -> None:
    launcher = _load_launcher()
    expected = {
        "scope": "lane",
        "worktree": "/sessions/lane/wt",
        "session_dir": "/sessions/lane",
        "state_root": "/sessions/lane/state",
        "repo_root": "/repo",
        "origin_url": "origin",
        "origin_push_url": "origin",
        "branch": "dev/lane",
        "base": "main",
        "base_oid": "a" * 40,
        "lane_oid": "b" * 40,
        "merge_class": "operator",
        "environment": {
            "DEVKIT_STATE_ROOT": "/sessions/lane/state",
            "DEVKIT_ROOT": "/repo",
            "DEVKIT_REFUSE_UNSANDBOXED_STATE": "1",
        },
    }
    observed = {
        **copy.deepcopy(expected),
        "git_top": expected["worktree"],
        "marker_state_root": expected["state_root"],
        "persisted_branch": expected["branch"],
        "pwd_environment": expected["worktree"],
        "repository_overrides_present": [],
    }
    launcher._validate_observation(expected, observed)
    wrong = copy.deepcopy(observed)
    wrong["worktree"] = wrong["git_top"] = wrong["pwd_environment"] = "/repo"
    with pytest.raises(launcher.LaunchError, match="worktree"):
        launcher._validate_observation(expected, wrong)


def test_caller_supplied_identity_without_independent_observation_is_rejected() -> None:
    launcher = _load_launcher()
    expected = {"worktree": "/lane", "state_root": "/state"}
    with pytest.raises(launcher.LaunchError):
        launcher._validate_observation(expected, dict(expected))


@pytest.mark.parametrize(
    ("field", "foreign"),
    (
        ("repo_root", "/foreign"),
        ("branch", "dev/foreign"),
        ("base", "foreign-base"),
        ("state_root", "/foreign-state"),
        ("origin_url", "/foreign-fetch"),
        ("origin_push_url", "/foreign-push"),
        ("base_oid", "c" * 40),
        ("lane_oid", "d" * 40),
    ),
)
def test_foreign_identity_mutations_are_rejected(field: str, foreign: str) -> None:
    launcher = _load_launcher()
    expected = {
        "scope": "lane",
        "worktree": "/sessions/lane/wt",
        "session_dir": "/sessions/lane",
        "state_root": "/sessions/lane/state",
        "repo_root": "/repo",
        "origin_url": "origin",
        "origin_push_url": "origin",
        "branch": "dev/lane",
        "base": "main",
        "base_oid": "a" * 40,
        "lane_oid": "b" * 40,
        "merge_class": "operator",
        "environment": {},
    }
    observed = {
        **copy.deepcopy(expected),
        "git_top": expected["worktree"],
        "marker_state_root": expected["state_root"],
        "persisted_branch": expected["branch"],
        "pwd_environment": expected["worktree"],
        "repository_overrides_present": [],
    }
    observed[field] = foreign
    with pytest.raises(launcher.LaunchError):
        launcher._validate_observation(expected, observed)


def test_stale_descriptor_is_rejected_after_canonical_rewrite(tmp_path: Path) -> None:
    launcher = _load_launcher()
    _repo, _engine, _sessions, descriptor, _prompt, _env = _install_repo(tmp_path)
    path = Path(descriptor["descriptor_path"])
    expired = copy.deepcopy(descriptor)
    expired["issued_at"] = "2026-01-01T00:00:00Z"
    expired["expires_at"] = "2026-01-01T00:15:00Z"
    path.write_bytes(launcher._canonical_json(expired))
    with pytest.raises(launcher.LaunchError, match="issue/expiry"):
        launcher._load_descriptor(
            path, now=dt.datetime(2026, 1, 1, 0, 15, 1, tzinfo=dt.timezone.utc)
        )


def test_process_reuse_cannot_satisfy_parent_binding() -> None:
    launcher = _load_launcher()
    request = {"descriptor_sha256": "a", "task_sha256": "b"}
    receipt = {
        "status": "observed",
        "descriptor_id": "descriptor",
        "request": copy.deepcopy(request),
        "observed": {
            "process": {
                "pid": 41,
                "capability_nonce": "old-nonce",
                "start_fingerprint": None,
            }
        },
    }
    launcher._validate_parent_binding(
        receipt,
        descriptor_id="descriptor",
        request=request,
        pid=41,
        process_nonce="old-nonce",
        live_start_fingerprint=None,
    )
    with pytest.raises(launcher.LaunchError, match="process identity"):
        launcher._validate_parent_binding(
            receipt,
            descriptor_id="descriptor",
            request=request,
            pid=41,
            process_nonce="reused-process-nonce",
            live_start_fingerprint=None,
        )


def test_success_without_final_message_evidence_is_failure(tmp_path: Path) -> None:
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, write_final=False
    )
    result = _run_launcher(engine, descriptor, prompt, env)
    assert result.returncode != 0
    receipt = json.loads(
        Path(
            descriptor["session_dir"],
            f"launch-receipt-{descriptor['descriptor_id']}.json",
        ).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "failed"
    assert "final-message evidence" in receipt["terminal"]["error"]


def test_receipt_evidence_objects_do_not_alias(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    result = _run_launcher(engine, descriptor, prompt, env)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(
        (sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    observed_before = copy.deepcopy(receipt["observed"])
    receipt["expected"]["branch"] = "dev/mutated"
    receipt["expected"]["environment"]["DEVKIT_ROOT"] = "/mutated"
    assert receipt["observed"] == observed_before


def test_forced_interruption_stops_child_and_records_terminal_outcome(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(tmp_path, sleep=True)
    process = subprocess.Popen(
        [
            sys.executable,
            str(engine / "launch_codex_lane.py"),
            "--descriptor",
            str(descriptor["descriptor_path"]),
            "--prompt-file",
            str(prompt),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    receipt_path = sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("status") == "observed":
                break
        time.sleep(0.05)
    else:
        process.kill()
        pytest.fail("launcher never durably bound the child observation")
    child_pid = receipt["observed"]["process"]["pid"]
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode != 0, (stdout, stderr)
    terminal = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert terminal["status"] == "interrupted"
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)


def test_internal_child_requires_a_parent_attempt(tmp_path: Path) -> None:
    _repo, engine, _sessions, descriptor, _prompt, env = _install_repo(tmp_path)
    session_dir = Path(descriptor["session_dir"])
    descriptor_id = str(descriptor["descriptor_id"])
    command = [
        sys.executable,
        str(engine / "launch_codex_lane.py"),
        "_child",
        "--descriptor",
        str(descriptor["descriptor_path"]),
        "--attempt",
        str(session_dir / f"launch-attempt-{descriptor_id}.json"),
        "--receipt",
        str(session_dir / f"launch-receipt-{descriptor_id}.json"),
        "--final-message",
        str(session_dir / f"launch-final-{descriptor_id}.txt"),
        "--descriptor-id",
        descriptor_id,
        "--task-sha256",
        "a" * 64,
        "--combined-prompt-sha256",
        "b" * 64,
        "--authority-fd",
        "0",
        "--ready-fd",
        "1",
        "--ack-fd",
        "0",
    ]

    first = subprocess.run(command, input=b"x" * 32, env=env, capture_output=True)
    second = subprocess.run(command, input=b"y" * 32, env=env, capture_output=True)

    assert first.returncode != 0
    assert second.returncode != 0
    assert not (session_dir / f"launch-attempt-{descriptor_id}.json").exists()
    assert not (session_dir / f"launch-final-{descriptor_id}.txt").exists()


def test_descriptor_id_cannot_escape_the_session_evidence_namespace(
    tmp_path: Path,
) -> None:
    launcher = _load_launcher()
    _repo, _engine, _sessions, descriptor, _prompt, _env = _install_repo(tmp_path)
    path = Path(descriptor["descriptor_path"])
    loaded, _raw = launcher._load_descriptor(path)
    assert loaded["descriptor_id"] == descriptor["descriptor_id"]

    escaped = copy.deepcopy(descriptor)
    escaped["descriptor_id"] = "x/../../foreign"
    path.write_bytes(launcher._canonical_json(escaped))

    with pytest.raises(launcher.LaunchError, match="canonical UUID4"):
        launcher._load_descriptor(path)


def test_corrupted_observation_cannot_be_terminalized_as_success(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, corrupt_receipt=True
    )

    result = _run_launcher(engine, descriptor, prompt, env)

    assert result.returncode != 0
    receipt = json.loads(
        (sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "failed"
    assert receipt["descriptor_id"] == descriptor["descriptor_id"]
    assert receipt["request"]["descriptor_sha256"]
    assert receipt["request"]["task_sha256"]
    assert "observed receipt changed" in receipt["terminal"]["error"]


def test_sigterm_ignoring_child_is_forcibly_stopped_within_the_configured_bound(
    tmp_path: Path,
) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, sleep=True, ignore_sigterm=True
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(engine / "launch_codex_lane.py"),
            "--descriptor",
            str(descriptor["descriptor_path"]),
            "--prompt-file",
            str(prompt),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    receipt_path = sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json"
    final_path = sessions / "probe" / f"launch-final-{descriptor['descriptor_id']}.txt"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("status") == "observed" and final_path.is_file():
                break
        time.sleep(0.05)
    else:
        process.kill()
        pytest.fail("launcher never durably bound the child observation")
    child_pid = receipt["observed"]["process"]["pid"]

    started = time.monotonic()
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=5)
    elapsed = time.monotonic() - started

    assert process.returncode != 0, (stdout, stderr)
    terminal = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert terminal["status"] == "interrupted"
    assert elapsed < 2.5
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)


def test_descriptor_is_one_shot_after_a_successful_launch(tmp_path: Path) -> None:
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(tmp_path)

    first = _run_launcher(engine, descriptor, prompt, env)
    second = _run_launcher(engine, descriptor, prompt, env)

    assert first.returncode == 0, first.stderr
    assert second.returncode != 0
    assert "already has a launch attempt" in second.stderr


def test_preexisting_final_message_path_blocks_launch(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    final_path = sessions / "probe" / f"launch-final-{descriptor['descriptor_id']}.txt"
    final_path.write_text("stale evidence", encoding="utf-8")

    result = _run_launcher(engine, descriptor, prompt, env)

    assert result.returncode != 0
    receipt = json.loads(
        (sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "failed"
    assert "reserve empty final-message evidence" in receipt["terminal"]["error"]
    assert final_path.read_text(encoding="utf-8") == "stale evidence"


def test_rewritten_prompt_contract_is_rejected_before_launch(tmp_path: Path) -> None:
    launcher = _load_launcher()
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    descriptor_path = Path(descriptor["descriptor_path"])
    rewritten = copy.deepcopy(descriptor)
    rewritten["prompt_preamble"] = "caller supplied identity"
    descriptor_path.write_bytes(launcher._canonical_json(rewritten))

    result = _run_launcher(engine, descriptor, prompt, env)

    assert result.returncode != 0
    assert "canonical issuer" in result.stderr
    assert not list(sessions.joinpath("probe").glob("launch-attempt-*.json"))


def test_descendant_cannot_outlive_a_successful_child_leader(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, spawn_descendant=True
    )
    pid_path = sessions / "probe" / "descendant.pid"
    descendant_pid: int | None = None
    try:
        result = _run_launcher(engine, descriptor, prompt, env)
        assert result.returncode != 0
        descendant_pid = int(pid_path.read_text(encoding="utf-8"))
        receipt = json.loads(
            (
                sessions
                / "probe"
                / f"launch-receipt-{descriptor['descriptor_id']}.json"
            ).read_text(encoding="utf-8")
        )
        assert receipt["status"] == "failed"
        assert "process group remained active" in receipt["terminal"]["error"]
        with pytest.raises(ProcessLookupError):
            os.kill(descendant_pid, 0)
    finally:
        if descendant_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(descendant_pid, signal.SIGKILL)
