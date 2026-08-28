from __future__ import annotations

import contextlib
import copy
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import select
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _load_launcher(engine_dir: Path = ENGINE_DIR) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "launch_lane", engine_dir / "launch_lane.py"
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
    spawn_detached_descendant: bool = False,
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
    detached_descendant_line = (
        "child = subprocess.Popen([sys.executable, '-c', "
        "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'], "
        "start_new_session=True); "
        "Path.cwd().parent.joinpath('detached-descendant.pid').write_text(str(child.pid), encoding='utf-8')"
        if spawn_detached_descendant
        else ""
    )
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, signal, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "output = args[args.index('--output-last-message') + 1]\n"
        "prompt = sys.stdin.read()\n"
        "inherited_fd = os.environ.get('TEST_INHERITED_FD')\n"
        "try:\n"
        "  os.fstat(int(inherited_fd))\n"
        "  inherited_fd_open = True\n"
        "except (OSError, TypeError, ValueError):\n"
        "  inherited_fd_open = False\n"
        "result = {\n"
        "  'cwd': str(Path.cwd().resolve()),\n"
        "  'branch': subprocess.run(['git','branch','--show-current'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'push_url': subprocess.run(['git','remote','get-url','--push','origin'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'env': {k: v for k, v in os.environ.items() if k.startswith('DEVKIT_')},\n"
        "  'gh_repo_present': 'GH_REPO' in os.environ,\n"
        "  'git_work_tree_present': 'GIT_WORK_TREE' in os.environ,\n"
        "  'git_config_present': any(k == 'GIT_CONFIG' or k.startswith('GIT_CONFIG_') for k in os.environ),\n"
        "  'git_environment_present': sorted(k for k in os.environ if k.startswith('GIT_')),\n"
        "  'inherited_fd_open': inherited_fd_open,\n"
        "  'contract_first': prompt.startswith('LANE CONTRACT (binding):'),\n"
        "  'pid': os.getpid(),\n"
        "  'argv': args,\n"
        "}\n"
        f"{ignore_line}\n"
        f"{descendant_line}\n"
        f"{detached_descendant_line}\n"
        f"{corrupt_line}\n"
        f"{final_line}\n"
        f"{sleep_line}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


CLAUDE_OUTPUT_MODES = (
    "valid",
    "malformed",
    "duplicated",
    "foreign",
    "error",
    "empty-result",
    "array",
    "text",
    "none",
    "denied",
    "no-denial-list",
)


def _fake_claude(
    path: Path,
    *,
    output: str = "valid",
    sleep: bool = False,
    corrupt_receipt: bool = False,
    ignore_stdin: bool = False,
) -> None:
    """A stand-in for `claude -p --output-format json`: prompt on stdin, one JSON
    result object on stdout. `output` selects a hostile stdout shape."""
    sleep_line = "time.sleep(60)" if sleep else ""
    corrupt_line = (
        "[p.write_text('{}\\n', encoding='utf-8') for p in Path.cwd().parent.glob('launch-receipt-*.json')]"
        if corrupt_receipt
        else ""
    )
    prompt_line = "prompt = ''" if ignore_stdin else "prompt = sys.stdin.read()"
    emit = {
        "valid": "sys.stdout.write(json.dumps(good) + '\\n')",
        "malformed": "sys.stdout.write(json.dumps(good)[:-7])",
        "duplicated": "sys.stdout.write(json.dumps(good) + '\\n' + json.dumps(good) + '\\n')",
        "foreign": "sys.stdout.write(json.dumps({'type': 'system', 'subtype': 'init', 'result': 'x'}) + '\\n')",
        "error": "sys.stdout.write(json.dumps({**good, 'is_error': True, 'subtype': 'error_during_execution'}) + '\\n')",
        "empty-result": "sys.stdout.write(json.dumps({**good, 'result': ''}) + '\\n')",
        "array": "sys.stdout.write(json.dumps([good]) + '\\n')",
        "text": "sys.stdout.write('plain text, not JSON\\n')",
        "none": "pass",
        # What Claude 2.1.247 actually prints when a tool call is refused: a
        # `success` envelope whose only trace of the refusal is this list.
        "denied": "sys.stdout.write(json.dumps({**good, 'permission_denials': [{'tool_name': 'Write', 'tool_use_id': 'toolu_x', 'tool_input': {'file_path': 'x.txt'}}]}) + '\\n')",
        "no-denial-list": "sys.stdout.write(json.dumps({k: v for k, v in good.items() if k != 'permission_denials'}) + '\\n')",
    }[output]
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, signal, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        f"{prompt_line}\n"
        "result = {\n"
        "  'cwd': str(Path.cwd().resolve()),\n"
        "  'branch': subprocess.run(['git','branch','--show-current'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'push_url': subprocess.run(['git','remote','get-url','--push','origin'], check=True, capture_output=True, text=True).stdout.strip(),\n"
        "  'env': {k: v for k, v in os.environ.items() if k.startswith('DEVKIT_')},\n"
        "  'gh_repo_present': 'GH_REPO' in os.environ,\n"
        "  'git_environment_present': sorted(k for k in os.environ if k.startswith('GIT_')),\n"
        "  'contract_first': prompt.startswith('LANE CONTRACT (binding):'),\n"
        "  'pid': os.getpid(),\n"
        "  'argv': args,\n"
        "}\n"
        "good = {'type': 'result', 'subtype': 'success', 'is_error': False, "
        "'result': json.dumps(result, sort_keys=True), 'session_id': 'fake', 'permission_denials': []}\n"
        f"{corrupt_line}\n"
        f"{emit}\n"
        "sys.stdout.flush()\n"
        f"{sleep_line}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


# The shape the kit seeds: a bounded allow-list and no defaultMode.
LANE_PROFILE: dict[str, object] = {
    "permissions": {
        "allow": ["Bash(git status:*)", "Bash(git commit:*)", "Bash(gh pr create:*)"],
        "deny": ["Bash(gh pr merge:*)"],
    }
}


def _install_repo(
    tmp_path: Path,
    *,
    runtime: str = "codex",
    claude_output: str = "valid",
    claude_ignore_stdin: bool = False,
    sleep: bool = False,
    write_final: bool = True,
    corrupt_receipt: bool = False,
    ignore_sigterm: bool = False,
    spawn_descendant: bool = False,
    spawn_detached_descendant: bool = False,
    codex_policy: str | None = "read-only",
    claude_policy: str | None = "accept-edits",
    profile: dict[str, object] | bytes | None = None,
    profile_key: str | None = "config/claude-lane-settings.json",
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
        spawn_detached_descendant=spawn_detached_descendant,
    )
    fake_claude = tmp_path / "fake-claude"
    _fake_claude(
        fake_claude,
        output=claude_output,
        sleep=sleep,
        corrupt_receipt=corrupt_receipt,
        ignore_stdin=claude_ignore_stdin,
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
        "    claude: claude\n"
        "parallel:\n"
        f"  codex_headless_command: [{json.dumps(str(fake_codex))}]\n"
        "  codex_worktree_transport: cd-flag\n"
        "  codex_prompt_transport: stdin-dash\n"
        "  codex_final_text_transport: last-message-file\n"
        f"  claude_headless_command: [{json.dumps(str(fake_claude))}]\n"
        "  claude_worktree_transport: process-cwd\n"
        "  claude_prompt_transport: stdin\n"
        "  claude_final_text_transport: json-stdout\n"
        + (f"  codex_approval_policy: {codex_policy}\n" if codex_policy is not None else "")
        + (f"  claude_approval_policy: {claude_policy}\n" if claude_policy is not None else "")
        + (f"  claude_settings_profile: {profile_key}\n" if profile_key is not None else "")
        + "  descriptor_ttl_seconds: 900\n"
        "  observation_timeout_seconds: 5\n"
        "  termination_grace_seconds: 1\n"
        "vcs:\n"
        "  protected_branch: trunk\n"
        "  dev_branch_prefix: lane\n",
        encoding="utf-8",
    )
    profile_path = repo / "config" / "claude-lane-settings.json"
    if profile is None:
        profile = LANE_PROFILE
    if isinstance(profile, bytes):
        profile_path.write_bytes(profile)
    else:
        profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
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
            runtime,
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
            str(engine_dir / "launch_lane.py"),
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
    fake_bin = tmp_path / "hostile-bin"
    fake_bin.mkdir()
    fake_git_marker = tmp_path / "fake-git-ran"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        f"#!/bin/sh\nprintf ran > {fake_git_marker}\nexit 97\n", encoding="utf-8"
    )
    fake_git.chmod(0o755)
    fake_bash_marker = tmp_path / "fake-bash-ran"
    fake_bash = fake_bin / "bash"
    fake_bash.write_text(
        f"#!/bin/sh\nprintf ran > {fake_bash_marker}\nexit 98\n", encoding="utf-8"
    )
    fake_bash.chmod(0o755)
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
        "GIT_OBJECT_DIRECTORY": str(tmp_path / "foreign-objects"),
        "GIT_SSH_COMMAND": str(tmp_path / "hostile-ssh"),
        "GIT_PROXY_COMMAND": str(tmp_path / "hostile-proxy"),
        "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
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
    assert final["git_environment_present"] == []
    assert final["push_url"] == descriptor["origin_push_url"]
    assert final["contract_first"] is True
    assert not fake_git_marker.exists()
    assert not fake_bash_marker.exists()
    assert receipt["terminal"]["final_message_sha256"]


def test_caller_inheritable_file_descriptor_is_closed_before_runtime_exec(
    tmp_path: Path,
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    leak_read, leak_write = os.pipe()
    high_leak_fd = fcntl.fcntl(leak_read, fcntl.F_DUPFD, 512)
    os.close(leak_read)
    os.set_inheritable(high_leak_fd, True)
    os.write(leak_write, b"CAPABILITY-LEAK")
    os.close(leak_write)
    inherited = {**env, "TEST_INHERITED_FD": str(high_leak_fd)}
    _soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)

    def lower_descriptor_limit() -> None:
        resource.setrlimit(resource.RLIMIT_NOFILE, (256, hard_limit))

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(engine_dir / "launch_lane.py"),
                "--descriptor",
                str(descriptor["descriptor_path"]),
                "--prompt-file",
                str(prompt),
            ],
            env=inherited,
            pass_fds=(high_leak_fd,),
            preexec_fn=lower_descriptor_limit,
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        os.close(high_leak_fd)

    assert result.returncode == 0, result.stderr
    receipt = json.loads(
        (
            sessions
            / "probe"
            / f"launch-receipt-{descriptor['descriptor_id']}.json"
        ).read_text(encoding="utf-8")
    )
    final = json.loads(Path(receipt["terminal"]["final_message_path"]).read_text())
    assert final["inherited_fd_open"] is False


def test_relative_runtime_command_uses_only_the_trusted_executable_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(tmp_path)
    trusted_bin = tmp_path / "trusted-bin"
    hostile_bin = tmp_path / "hostile-bin"
    trusted_bin.mkdir()
    hostile_bin.mkdir()
    trusted_runtime = trusted_bin / "lane-runtime"
    shutil.copy2(tmp_path / "fake-codex", trusted_runtime)
    hostile_marker = tmp_path / "hostile-runtime-ran"
    hostile_runtime = hostile_bin / "lane-runtime"
    hostile_runtime.write_text(
        f"#!/bin/sh\nprintf ran > {hostile_marker}\nexit 99\n", encoding="utf-8"
    )
    hostile_runtime.chmod(0o755)
    config_path = Path(descriptor["repo_root"]) / "config" / "dev-model.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace(
            f"codex_headless_command: [{json.dumps(str(tmp_path / 'fake-codex'))}]",
            'codex_headless_command: ["lane-runtime"]',
        ),
        encoding="utf-8",
    )
    launcher = _load_launcher(engine_dir)
    launcher.SAFE_EXECUTABLE_PATH = os.pathsep.join(
        (str(trusted_bin), launcher.SAFE_EXECUTABLE_PATH)
    )
    monkeypatch.setenv("PATH", f"{hostile_bin}{os.pathsep}{env['PATH']}")

    result = launcher.main(
        [
            "--descriptor",
            str(descriptor["descriptor_path"]),
            "--prompt-file",
            str(prompt),
        ]
    )

    assert result == 0
    receipt = json.loads(
        (
            sessions
            / "probe"
            / f"launch-receipt-{descriptor['descriptor_id']}.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt["request"]["configured_command"] == [str(trusted_runtime)]
    assert receipt["status"] == "completed"
    assert not hostile_marker.exists()


@pytest.mark.parametrize(
    ("key", "foreign"),
    (
        ("DEVKIT_STATE_ROOT", "/foreign-state"),
        ("DEVKIT_ROOT", "/foreign-repository"),
        ("DEVKIT_REFUSE_UNSANDBOXED_STATE", "0"),
    ),
)
def test_descriptor_environment_is_cross_bound_to_lane_identity(
    tmp_path: Path, key: str, foreign: str
) -> None:
    launcher = _load_launcher()
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(tmp_path)
    descriptor_path = Path(descriptor["descriptor_path"])
    mutated = copy.deepcopy(descriptor)
    mutated["env"][key] = foreign
    mutated_raw = launcher._canonical_json(mutated)
    descriptor_path.write_bytes(mutated_raw)
    authority_path = Path(descriptor["session_dir"]) / "launch-authority.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["descriptor_sha256"] = hashlib.sha256(mutated_raw).hexdigest()
    authority_path.chmod(0o600)
    authority_path.write_bytes(launcher._canonical_json(authority))

    result = _run_launcher(engine, mutated, prompt, env)

    assert result.returncode != 0
    assert "environment disagrees with lane identity" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_issuer_authority_rejects_id_and_window_rewrite_before_launch(
    tmp_path: Path,
) -> None:
    launcher = _load_launcher()
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(tmp_path)
    descriptor_path = Path(descriptor["descriptor_path"])
    mutated = copy.deepcopy(descriptor)
    mutated["descriptor_id"] = "11111111-1111-4111-8111-111111111111"
    for field in ("issued_at", "expires_at"):
        value = dt.datetime.fromisoformat(mutated[field].replace("Z", "+00:00"))
        mutated[field] = (value - dt.timedelta(seconds=1)).isoformat().replace(
            "+00:00", "Z"
        )
    descriptor_path.write_bytes(launcher._canonical_json(mutated))

    result = _run_launcher(engine, mutated, prompt, env)

    assert result.returncode != 0
    assert "issuer-created launch authority" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


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
            "argv": ["/bin/runtime", "--sandbox", "read-only"],
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
        expected_argv=["/bin/runtime", "--sandbox", "read-only"],
    )
    with pytest.raises(launcher.LaunchError, match="process identity"):
        launcher._validate_parent_binding(
            receipt,
            descriptor_id="descriptor",
            request=request,
            pid=41,
            process_nonce="reused-process-nonce",
            live_start_fingerprint=None,
            expected_argv=["/bin/runtime", "--sandbox", "read-only"],
        )


def test_reused_pid_without_launch_nonce_is_never_signalled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = _load_launcher()
    scans = iter(({4242: "ps:same-second"}, {}, {}, {}, {}))
    signalled: list[tuple[int, int]] = []
    monkeypatch.setattr(
        launcher,
        "_processes_with_launch_nonce",
        lambda _nonce: next(scans, {}),
    )
    monkeypatch.setattr(
        launcher, "_process_start_fingerprint", lambda _pid: "ps:same-second"
    )
    monkeypatch.setattr(
        launcher.os, "kill", lambda pid, signum: signalled.append((pid, signum))
    )

    launcher._terminate_launch_lineage("current-launch-nonce", 1)

    assert signalled == []


def test_descriptor_scrub_refuses_when_live_descriptors_cannot_be_enumerated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = _load_launcher()
    monkeypatch.setattr(launcher.Path, "is_dir", lambda _path: False)

    with pytest.raises(launcher.LaunchError, match="cannot enumerate inherited"):
        launcher._close_nonstandard_descriptors()


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
            str(engine / "launch_lane.py"),
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


def test_internal_child_mode_cannot_be_forged_by_a_caller(tmp_path: Path) -> None:
    launcher = _load_launcher()
    _repo, engine, _sessions, descriptor, _prompt, env = _install_repo(tmp_path)
    session_dir = Path(descriptor["session_dir"])
    descriptor_id = str(descriptor["descriptor_id"])
    descriptor_raw = Path(descriptor["descriptor_path"]).read_bytes()
    capability = b"x" * 32
    task = b"MALICIOUS PROMPT WITHOUT CONTRACT"
    request = {
        "descriptor_sha256": hashlib.sha256(descriptor_raw).hexdigest(),
        "task_sha256": hashlib.sha256(task).hexdigest(),
        "combined_prompt_sha256": hashlib.sha256(task).hexdigest(),
        "configured_command": [str(tmp_path / "fake-codex")],
        "process_nonce_sha256": hashlib.sha256(capability.hex().encode()).hexdigest(),
    }
    attempt_path = session_dir / "launch-attempt.json"
    attempt_path.write_bytes(
        launcher._canonical_json(
            {
                "schema_version": 1,
                "status": "starting",
                "descriptor_id": descriptor_id,
                "request": request,
                "parent_process": {
                    "pid": os.getpid(),
                    "start_fingerprint": launcher._process_start_fingerprint(os.getpid()),
                },
            }
        )
    )
    receipt_path = session_dir / f"launch-receipt-{descriptor_id}.json"
    final_path = session_dir / f"launch-final-{descriptor_id}.txt"
    authority_read, authority_write = os.pipe()
    ready_read, ready_write = os.pipe()
    ack_read, ack_write = os.pipe()
    command = [
        sys.executable,
        str(engine / "launch_lane.py"),
        "_child",
        "--descriptor",
        str(descriptor["descriptor_path"]),
        "--attempt",
        str(attempt_path),
        "--receipt",
        str(receipt_path),
        "--final-message",
        str(final_path),
        "--descriptor-id",
        descriptor_id,
        "--task-sha256",
        request["task_sha256"],
        "--combined-prompt-sha256",
        request["combined_prompt_sha256"],
        "--authority-fd",
        str(authority_read),
        "--ready-fd",
        str(ready_write),
        "--ack-fd",
        str(ack_read),
    ]
    process = subprocess.Popen(
        command,
        cwd=descriptor["worktree"],
        env=launcher._scrubbed_environment(descriptor),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pass_fds=(authority_read, ready_write, ack_read),
        start_new_session=True,
    )
    os.close(authority_read)
    os.close(ready_write)
    os.close(ack_read)
    os.write(authority_write, capability)
    os.close(authority_write)
    readable, _, _ = select.select([ready_read], [], [], 2)
    ready = os.read(ready_read, 64) if readable else b""
    os.close(ready_read)
    if ready == b"READY\n":
        os.write(ack_write, b"1")
    os.close(ack_write)
    stdout, stderr = process.communicate(input=task, timeout=5)

    assert process.returncode != 0, (stdout, stderr)
    assert ready != b"READY\n"
    assert not receipt_path.exists()
    assert not final_path.exists()


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
            str(engine / "launch_lane.py"),
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
            if (
                receipt.get("status") == "observed"
                and final_path.is_file()
                and final_path.stat().st_size > 0
            ):
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
    launcher = _load_launcher()
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(tmp_path)

    first = _run_launcher(engine, descriptor, prompt, env)
    mutated = copy.deepcopy(descriptor)
    mutated["descriptor_id"] = "22222222-2222-4222-8222-222222222222"
    for field in ("issued_at", "expires_at"):
        value = dt.datetime.fromisoformat(mutated[field].replace("Z", "+00:00"))
        mutated[field] = (value - dt.timedelta(seconds=1)).isoformat().replace(
            "+00:00", "Z"
        )
    descriptor_path = Path(descriptor["descriptor_path"])
    mutated_raw = launcher._canonical_json(mutated)
    descriptor_path.write_bytes(mutated_raw)
    authority_path = Path(descriptor["session_dir"]) / "launch-authority.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["descriptor_id"] = mutated["descriptor_id"]
    authority["descriptor_sha256"] = hashlib.sha256(mutated_raw).hexdigest()
    authority_path.chmod(0o600)
    authority_path.write_bytes(launcher._canonical_json(authority))
    second = _run_launcher(engine, mutated, prompt, env)

    assert first.returncode == 0, first.stderr
    assert second.returncode != 0
    assert "already has a launch attempt" in second.stderr


def test_partial_descriptor_without_rewrite_seal_cannot_launch(tmp_path: Path) -> None:
    _repo, engine, _sessions, descriptor, prompt, env = _install_repo(tmp_path)
    authority_path = Path(descriptor["session_dir"]) / "launch-authority.json"
    authority_path.unlink()

    result = _run_launcher(engine, descriptor, prompt, env)

    assert result.returncode != 0
    assert "launch-authority.json" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


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
    rewritten_raw = launcher._canonical_json(rewritten)
    descriptor_path.write_bytes(rewritten_raw)
    authority_path = Path(descriptor["session_dir"]) / "launch-authority.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["descriptor_sha256"] = hashlib.sha256(rewritten_raw).hexdigest()
    authority_path.chmod(0o600)
    authority_path.write_bytes(launcher._canonical_json(authority))

    result = _run_launcher(engine, descriptor, prompt, env)

    assert result.returncode != 0
    assert "canonical issuer" in result.stderr
    assert not sessions.joinpath("probe", "launch-attempt.json").exists()


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


def test_detached_descendant_blocks_success_and_is_terminated(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, spawn_detached_descendant=True
    )
    pid_path = sessions / "probe" / "detached-descendant.pid"
    detached_pid: int | None = None
    try:
        result = _run_launcher(engine, descriptor, prompt, env)
        assert result.returncode != 0
        detached_pid = int(pid_path.read_text(encoding="utf-8"))
        receipt = json.loads(
            (
                sessions
                / "probe"
                / f"launch-receipt-{descriptor['descriptor_id']}.json"
            ).read_text(encoding="utf-8")
        )
        assert receipt["status"] == "failed"
        assert "detached launch-lineage" in receipt["terminal"]["error"]
        with pytest.raises(ProcessLookupError):
            os.kill(detached_pid, 0)
    finally:
        if detached_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(detached_pid, signal.SIGKILL)


def test_interruption_terminates_detached_launch_lineage(tmp_path: Path) -> None:
    _repo, engine, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, sleep=True, spawn_detached_descendant=True
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(engine / "launch_lane.py"),
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
    pid_path = sessions / "probe" / "detached-descendant.pid"
    receipt_path = sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if pid_path.is_file() and receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("status") == "observed":
                break
        time.sleep(0.05)
    else:
        process.kill()
        pytest.fail("launcher never durably observed the detached-lineage fixture")
    detached_pid = int(pid_path.read_text(encoding="utf-8"))
    try:
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode != 0, (stdout, stderr)
        terminal = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert terminal["status"] == "interrupted"
        with pytest.raises(ProcessLookupError):
            os.kill(detached_pid, 0)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(detached_pid, signal.SIGKILL)


def test_exception_after_reaped_leader_still_cleans_up_descendant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repo, engine, sessions, descriptor, prompt, _env = _install_repo(
        tmp_path, spawn_descendant=True
    )
    launcher = _load_launcher(engine)
    original_group_exists = launcher._process_group_exists
    calls = 0

    def fail_first_group_check(process_group: int) -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected parent-side group observation failure")
        return original_group_exists(process_group)

    monkeypatch.setattr(launcher, "_process_group_exists", fail_first_group_check)
    pid_path = sessions / "probe" / "descendant.pid"
    descendant_pid: int | None = None
    try:
        result = launcher.main(
            [
                "--descriptor",
                str(descriptor["descriptor_path"]),
                "--prompt-file",
                str(prompt),
            ]
        )
        assert result != 0
        descendant_pid = int(pid_path.read_text(encoding="utf-8"))
        receipt = json.loads(
            (
                sessions
                / "probe"
                / f"launch-receipt-{descriptor['descriptor_id']}.json"
            ).read_text(encoding="utf-8")
        )
        assert receipt["status"] == "failed"
        assert "injected parent-side group observation failure" in receipt["terminal"]["error"]
        with pytest.raises(ProcessLookupError):
            os.kill(descendant_pid, 0)
    finally:
        if descendant_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(descendant_pid, signal.SIGKILL)


# ── Per-runtime generalisation: Claude through `claude -p`, Codex unchanged ──────


def _receipt(sessions: Path, descriptor: dict[str, object]) -> dict[str, object]:
    return json.loads(
        (sessions / "probe" / f"launch-receipt-{descriptor['descriptor_id']}.json").read_text(
            encoding="utf-8"
        )
    )


def test_claude_wrapper_replaces_inherited_identity_and_binds_json_final_text(
    tmp_path: Path,
) -> None:
    repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude"
    )
    fake_bin = tmp_path / "hostile-bin"
    fake_bin.mkdir()
    fake_git_marker = tmp_path / "fake-git-ran"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        f"#!/bin/sh\nprintf ran > {fake_git_marker}\nexit 97\n", encoding="utf-8"
    )
    fake_git.chmod(0o755)
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
        "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
    }

    result = _run_launcher(engine_dir, descriptor, prompt, inherited)

    assert result.returncode == 0, result.stderr
    assert descriptor["runtime"] == "claude"
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "completed"
    assert receipt["request"]["runtime"] == "claude"
    assert receipt["request"]["transports"] == {
        "worktree": "process-cwd",
        "prompt": "stdin",
        "final_text": "json-stdout",
    }
    raw = Path(receipt["terminal"]["final_message_path"]).read_bytes()
    envelope = json.loads(raw)
    assert envelope["type"] == "result" and envelope["is_error"] is False
    final = json.loads(envelope["result"])
    # Claude's argv carries no worktree flag and no prompt argument: cwd comes
    # from the process and the prompt from stdin. The approval contribution sits
    # between the command prefix and the final-text arguments.
    profile_path = str((repo / "config" / "claude-lane-settings.json").resolve())
    assert final["argv"] == [
        "--setting-sources",
        "",
        "--permission-mode",
        "acceptEdits",
        "--settings",
        profile_path,
        "--output-format",
        "json",
    ]
    assert receipt["request"]["approval_policy"] == {
        "declared": "accept-edits",
        "argv": final["argv"][:6],
        "settings_profile_path": profile_path,
        "settings_profile_sha256": hashlib.sha256(
            (repo / "config" / "claude-lane-settings.json").read_bytes()
        ).hexdigest(),
    }
    assert receipt["observed"]["argv"] == [
        *receipt["request"]["configured_command"],
        *final["argv"],
    ]
    assert receipt["terminal"]["permission_denials"] == []
    assert final["cwd"] == descriptor["worktree"]
    assert final["branch"] == descriptor["branch"]
    assert final["env"] == descriptor["env"]
    assert final["gh_repo_present"] is False
    assert final["git_environment_present"] == []
    assert final["push_url"] == descriptor["origin_push_url"]
    assert final["contract_first"] is True
    assert not fake_git_marker.exists()
    assert receipt["terminal"]["final_text_transport"] == "json-stdout"
    assert receipt["terminal"]["final_message_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (
        receipt["terminal"]["final_text_sha256"]
        == hashlib.sha256(envelope["result"].encode()).hexdigest()
    )
    assert receipt["terminal"]["final_text_sha256"] != receipt["terminal"]["final_message_sha256"]
    assert receipt["observed"]["repo_root"] == str(repo)


def test_codex_child_argv_is_pinned_with_the_policy_slot_and_evidence_route_unchanged(
    tmp_path: Path,
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(tmp_path)

    result = _run_launcher(engine_dir, descriptor, prompt, env)

    assert result.returncode == 0, result.stderr
    receipt = _receipt(sessions, descriptor)
    final_path = Path(receipt["terminal"]["final_message_path"])
    final = json.loads(final_path.read_text(encoding="utf-8"))
    # Pinned: the #609 argv, byte for byte and in the same order, with exactly one
    # addition — the declared sandbox policy in the slot after the command prefix.
    # Dropping or reordering `--cd`, the evidence file, or the stdin dash while the
    # policy is added is the regression this pin reports.
    assert final["argv"] == [
        "--sandbox",
        "read-only",
        "--cd",
        descriptor["worktree"],
        "--output-last-message",
        str(final_path),
        "-",
    ]
    assert receipt["request"]["approval_policy"] == {
        "declared": "read-only",
        "argv": ["--sandbox", "read-only"],
        "settings_profile_path": None,
        "settings_profile_sha256": None,
    }
    assert receipt["observed"]["argv"] == [
        receipt["request"]["configured_command"][0],
        *final["argv"],
    ]
    # `last-message-file` cannot observe the approval outcome: null, never [].
    assert receipt["terminal"]["permission_denials"] is None
    assert receipt["request"]["runtime"] == "codex"
    assert receipt["request"]["transports"] == {
        "worktree": "cd-flag",
        "prompt": "stdin-dash",
        "final_text": "last-message-file",
    }
    assert receipt["terminal"]["final_text_transport"] == "last-message-file"
    assert receipt["terminal"]["final_text_sha256"] == receipt["terminal"]["final_message_sha256"]
    assert receipt["terminal"]["final_message_sha256"] == hashlib.sha256(
        final_path.read_bytes()
    ).hexdigest()


@pytest.mark.parametrize(
    ("output", "fragment"),
    (
        ("malformed", "not one complete JSON object"),
        ("duplicated", "more than one JSON value"),
        ("foreign", "not a result object"),
        ("error", "unsuccessful result"),
        ("empty-result", "missing or empty"),
        ("array", "not an object"),
        ("text", "not one complete JSON object"),
        ("none", "no JSON result on stdout"),
    ),
)
def test_hostile_claude_stdout_is_a_failed_terminal_receipt(
    tmp_path: Path, output: str, fragment: str
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", claude_output=output
    )

    result = _run_launcher(engine_dir, descriptor, prompt, env)

    assert result.returncode == 70, result.stderr
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "failed"
    assert fragment in receipt["terminal"]["error"]
    assert receipt["terminal"]["final_text_sha256"] is None
    # The exclusive attempt stays: a hostile stdout does not free the descriptor.
    assert Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_claude_prompt_not_delivered_on_stdin_is_visible_in_the_final_text(
    tmp_path: Path,
) -> None:
    # Positive construction for the transport claim: a runtime that does not read
    # stdin cannot have seen the lane contract, and the bound final text says so.
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", claude_ignore_stdin=True
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 0, result.stderr
    receipt = _receipt(sessions, descriptor)
    envelope = json.loads(Path(receipt["terminal"]["final_message_path"]).read_bytes())
    assert json.loads(envelope["result"])["contract_first"] is False
    honest = _install_repo(tmp_path / "honest", runtime="claude")
    result = _run_launcher(honest[1], honest[3], honest[4], honest[5])
    assert result.returncode == 0, result.stderr
    envelope = json.loads(
        Path(_receipt(honest[2], honest[3])["terminal"]["final_message_path"]).read_bytes()
    )
    assert json.loads(envelope["result"])["contract_first"] is True


@pytest.mark.parametrize(
    ("runtime", "key", "declared"),
    (
        ("claude", "claude_prompt_transport", "stdin-dash"),
        ("claude", "claude_final_text_transport", "last-message-file"),
        ("claude", "claude_worktree_transport", "cd-flag"),
        ("codex", "codex_prompt_transport", "stdin"),
        ("codex", "codex_final_text_transport", "json-stdout"),
        ("codex", "codex_worktree_transport", "process-cwd"),
        ("claude", "claude_prompt_transport", "argument"),
    ),
)
def test_declared_transport_the_runtime_does_not_implement_is_refused(
    tmp_path: Path, runtime: str, key: str, declared: str
) -> None:
    _repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime=runtime
    )
    config_path = Path(descriptor["repo_root"]) / "config" / "dev-model.yaml"
    lines = config_path.read_text(encoding="utf-8").splitlines(keepends=True)
    rewritten = [
        f"  {key}: {declared}\n" if line.startswith(f"  {key}:") else line for line in lines
    ]
    assert rewritten != lines
    config_path.write_text("".join(rewritten), encoding="utf-8")

    result = _run_launcher(engine_dir, descriptor, prompt, env)

    assert result.returncode == 64
    assert f"config parallel.{key} must declare one of" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_descriptor_for_an_untemplated_runtime_is_refused(tmp_path: Path) -> None:
    launcher = _load_launcher()
    _repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude"
    )
    descriptor_path = Path(descriptor["descriptor_path"])
    authority_path = Path(descriptor["session_dir"]) / "launch-authority.json"

    foreign = copy.deepcopy(descriptor)
    foreign["runtime"] = "gemini"
    foreign_raw = launcher._canonical_json(foreign)
    descriptor_path.write_bytes(foreign_raw)
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["descriptor_sha256"] = hashlib.sha256(foreign_raw).hexdigest()
    authority_path.chmod(0o600)
    authority_path.write_bytes(launcher._canonical_json(authority))
    result = _run_launcher(engine_dir, foreign, prompt, env)
    assert result.returncode == 64
    assert "not a supported headless runtime" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()

    # A supported runtime name whose command the config does not template.
    descriptor_path.write_bytes(launcher._canonical_json(descriptor))
    authority["descriptor_sha256"] = hashlib.sha256(
        launcher._canonical_json(descriptor)
    ).hexdigest()
    authority_path.write_bytes(launcher._canonical_json(authority))
    config_path = Path(descriptor["repo_root"]) / "config" / "dev-model.yaml"
    config_path.write_text(
        "".join(
            line
            for line in config_path.read_text(encoding="utf-8").splitlines(keepends=True)
            if not line.startswith("  claude_headless_command:")
        ),
        encoding="utf-8",
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64
    assert "parallel.claude_headless_command must be a non-empty argv sequence" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_claude_final_text_is_not_accepted_before_the_observation_is_bound(
    tmp_path: Path,
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", corrupt_receipt=True
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode != 0
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "failed"
    assert "observed receipt changed" in receipt["terminal"]["error"]


def test_claude_descriptor_is_one_shot_after_a_successful_launch(tmp_path: Path) -> None:
    _repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude"
    )
    first = _run_launcher(engine_dir, descriptor, prompt, env)
    second = _run_launcher(engine_dir, descriptor, prompt, env)
    assert first.returncode == 0, first.stderr
    assert second.returncode != 0
    assert "already has a launch attempt" in second.stderr


def _approval(
    declared: str, argv: list[str], *, profile: str | None = None
) -> dict[str, object]:
    return {
        "declared": declared,
        "argv": argv,
        "settings_profile_path": profile,
        "settings_profile_sha256": "p" * 64 if profile else None,
    }


def test_request_binding_carries_runtime_and_transports() -> None:
    launcher = _load_launcher()
    codex = launcher.RuntimeProfile(
        "codex",
        ["/bin/codex", "exec"],
        {"worktree": "cd-flag", "prompt": "stdin-dash", "final_text": "last-message-file"},
        _approval("read-only", ["--sandbox", "read-only"]),
    )
    claude = launcher.RuntimeProfile(
        "claude",
        ["/bin/claude", "-p"],
        {"worktree": "process-cwd", "prompt": "stdin", "final_text": "json-stdout"},
        _approval(
            "accept-edits",
            ["--setting-sources", "", "--permission-mode", "acceptEdits", "--settings", "/profile.json"],
            profile="/profile.json",
        ),
    )
    bind = lambda profile: launcher._request_binding(  # noqa: E731
        b"descriptor",
        task_sha256="t",
        combined_prompt_sha256="c",
        profile=profile,
        process_nonce="n",
    )
    assert bind(codex) != bind(claude)
    assert bind(codex)["transports"] is not codex.transports
    assert bind(codex)["approval_policy"] is not codex.approval
    assert bind(codex)["approval_policy"]["argv"] is not codex.approval["argv"]
    assert bind(claude)["approval_policy"]["settings_profile_path"] == "/profile.json"
    assert codex.child_argv("/wt", "/final") == [
        "/bin/codex",
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
        "/wt",
        "--output-last-message",
        "/final",
        "-",
    ]
    assert claude.child_argv("/wt", "/final") == [
        "/bin/claude",
        "-p",
        "--setting-sources",
        "",
        "--permission-mode",
        "acceptEdits",
        "--settings",
        "/profile.json",
        "--output-format",
        "json",
    ]


@pytest.mark.parametrize(
    ("transport", "payload", "fragment"),
    (
        ("json-stdout", b"", "no JSON result"),
        ("json-stdout", b"\xff\xfe", "not UTF-8"),
        ("json-stdout", b'{"type": "result"', "not one complete JSON object"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":"a"}\n{}', "more than one"),
        ("json-stdout", b'[{"type":"result"}]', "not an object"),
        ("json-stdout", b'{"type":"assistant","result":"a"}', "not a result object"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":true,"result":"a"}', "unsuccessful"),
        # `is_error` must be the literal false: absent, null, 0, or "" is not a
        # success assertion, and a truthiness check would accept all four.
        ("json-stdout", b'{"type":"result","subtype":"success","result":"a"}', "unsuccessful"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":null,"result":"a"}', "unsuccessful"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":0,"result":"a"}', "unsuccessful"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":"","result":"a"}', "unsuccessful"),
        ("json-stdout", b'{"type":"result","subtype":"error_max_turns","is_error":false,"result":"a"}', "unsuccessful"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":""}', "missing or empty"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":7}', "missing or empty"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false}', "missing or empty"),
        # The approval outcome must be observable: a result with no list-valued
        # `permission_denials` is refused rather than read as "nothing denied".
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":"a"}', "no permission_denials list"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":"a","permission_denials":null}', "no permission_denials list"),
        ("json-stdout", b'{"type":"result","subtype":"success","is_error":false,"result":"a","permission_denials":{}}', "no permission_denials list"),
    ),
)
def test_final_text_extraction_refuses_every_non_result_shape(
    transport: str, payload: bytes, fragment: str
) -> None:
    launcher = _load_launcher()
    with pytest.raises(launcher.LaunchError, match=fragment):
        launcher._extract_final_text(transport, payload)


def test_last_message_file_without_bytes_is_missing_evidence() -> None:
    # The Codex route does no shape validation: any bytes are the final text, and
    # only their absence is refused.
    launcher = _load_launcher()
    with pytest.raises(launcher.LaunchError, match="final-message evidence"):
        launcher._extract_final_text("last-message-file", b"")
    assert launcher._extract_final_text("last-message-file", b"{not json") == b"{not json"


def test_final_text_extraction_accepts_one_result_object() -> None:
    launcher = _load_launcher()
    good = (
        b'\n {"type":"result","subtype":"success","is_error":false,'
        b'"result":"done \xc3\xa9","permission_denials":[]} \n'
    )
    assert launcher._extract_final_text("json-stdout", good) == "done é".encode()
    assert launcher._extract_final_result("json-stdout", good) == ("done é".encode(), [])
    denied = (
        b'{"type":"result","subtype":"success","is_error":false,"result":"done",'
        b'"permission_denials":[{"tool_name":"Write"}]}'
    )
    # Extraction reports the denial; refusing the lane is the launcher's decision.
    assert launcher._extract_final_result("json-stdout", denied) == (
        b"done",
        [{"tool_name": "Write"}],
    )
    assert launcher._extract_final_text("last-message-file", b"raw text") == b"raw text"
    assert launcher._extract_final_result("last-message-file", b"raw text") == (b"raw text", None)


def test_json_stdout_redirect_requires_the_reserved_empty_file(tmp_path: Path) -> None:
    launcher = _load_launcher()
    occupied = tmp_path / "occupied.txt"
    occupied.write_text("stale", encoding="utf-8")
    link_target = tmp_path / "target.txt"
    link_target.touch()
    link = tmp_path / "link.txt"
    link.symlink_to(link_target)
    missing = tmp_path / "missing.txt"
    # A reserved file that another path also names is not the parent's exclusive
    # reservation any more, even while it is still empty.
    hardlinked = tmp_path / "hardlinked.txt"
    hardlinked.touch()
    os.link(hardlinked, tmp_path / "hardlink-alias.txt")
    for path, fragment in (
        (occupied, "not an empty regular file"),
        (hardlinked, "not an empty regular file"),
        (link, "cannot open"),
        (missing, "cannot open"),
    ):
        with pytest.raises(launcher.LaunchError, match=fragment):
            launcher._redirect_stdout_to_reserved_final(path)
    # The redirect itself is exercised in a child so pytest's stdout stays intact.
    reserved = tmp_path / "reserved.txt"
    reserved.touch()
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util, sys, os\n"
            f"spec = importlib.util.spec_from_file_location('l', {str(ENGINE_DIR / 'launch_lane.py')!r})\n"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "from pathlib import Path\n"
            f"m._redirect_stdout_to_reserved_final(Path({str(reserved)!r}))\n"
            "os.write(1, b'RUNTIME-OUTPUT')\n",
        ],
        check=True,
        capture_output=True,
    )
    assert probe.stdout == b""
    assert reserved.read_bytes() == b"RUNTIME-OUTPUT"


# ── Approval/sandbox policy and the Claude trust route (#601) ────────────────────


def _rewrite_parallel_key(descriptor: dict[str, object], key: str, value: str | None) -> None:
    """Rewrite (or drop, when value is None) one flat `parallel` key in the fixture config."""
    config_path = Path(descriptor["repo_root"]) / "config" / "dev-model.yaml"
    lines = config_path.read_text(encoding="utf-8").splitlines(keepends=True)
    rewritten = [
        (f"  {key}: {value}\n" if value is not None else "")
        if line.startswith(f"  {key}:")
        else line
        for line in lines
    ]
    assert rewritten != lines
    config_path.write_text("".join(rewritten), encoding="utf-8")


@pytest.mark.parametrize(
    ("runtime", "declared", "mode_argv"),
    (
        ("claude", "dont-ask", ["--permission-mode", "dontAsk"]),
        ("claude", "accept-edits", ["--permission-mode", "acceptEdits"]),
        ("codex", "read-only", ["--sandbox", "read-only"]),
        ("codex", "workspace-write", ["--sandbox", "workspace-write"]),
    ),
)
def test_each_declared_policy_reaches_the_child_argv_in_the_fixed_slot(
    tmp_path: Path, runtime: str, declared: str, mode_argv: list[str]
) -> None:
    kwargs = {"claude_policy": declared} if runtime == "claude" else {"codex_policy": declared}
    repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime=runtime, **kwargs
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 0, result.stderr
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "completed"
    assert receipt["request"]["approval_policy"]["declared"] == declared
    final_path = Path(receipt["terminal"]["final_message_path"])
    if runtime == "claude":
        envelope = json.loads(final_path.read_bytes())
        argv = json.loads(envelope["result"])["argv"]
        profile_path = str((repo / "config" / "claude-lane-settings.json").resolve())
        assert argv[:6] == ["--setting-sources", "", *mode_argv, "--settings", profile_path]
        assert argv[6:] == ["--output-format", "json"]
    else:
        argv = json.loads(final_path.read_text(encoding="utf-8"))["argv"]
        assert argv[:2] == mode_argv
        assert argv[2:] == ["--cd", descriptor["worktree"], "--output-last-message", str(final_path), "-"]
    assert receipt["request"]["approval_policy"]["argv"] == argv[: len(receipt["request"]["approval_policy"]["argv"])]
    assert receipt["observed"]["argv"] == [*receipt["request"]["configured_command"], *argv]


def test_permission_denials_fail_the_lane_before_any_success(tmp_path: Path) -> None:
    # Positive construction for the approval transition: Claude's envelope for a
    # refused write is `subtype=success`, `is_error=false`; the refusal lives only
    # in `permission_denials`. The wrapper must read it before acknowledging.
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", claude_output="denied"
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 70, result.stderr
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "failed"
    assert receipt["terminal"]["returncode"] == 0
    assert "permission denials under declared policy accept-edits" in receipt["terminal"]["error"]
    assert receipt["terminal"]["permission_denials"] == [
        {"tool_name": "Write", "tool_use_id": "toolu_x", "tool_input": {"file_path": "x.txt"}}
    ]
    # The envelope is still bound as evidence; the extracted text is not success.
    assert receipt["terminal"]["final_message_sha256"] is not None
    assert receipt["terminal"]["final_text_sha256"] is None
    assert Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_result_without_a_denial_list_is_not_success(tmp_path: Path) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", claude_output="no-denial-list"
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 70, result.stderr
    receipt = _receipt(sessions, descriptor)
    assert receipt["status"] == "failed"
    assert "no permission_denials list" in receipt["terminal"]["error"]
    assert receipt["terminal"]["permission_denials"] is None


@pytest.mark.parametrize(
    ("runtime", "key", "declared"),
    (
        ("claude", "claude_approval_policy", "bypassPermissions"),
        ("claude", "claude_approval_policy", "bypass"),
        ("claude", "claude_approval_policy", "dangerously-skip-permissions"),
        ("claude", "claude_approval_policy", "auto"),
        ("claude", "claude_approval_policy", "manual"),
        ("claude", "claude_approval_policy", "plan"),
        ("claude", "claude_approval_policy", "acceptEdits"),
        ("claude", "claude_approval_policy", "workspace-write"),
        ("claude", "claude_approval_policy", None),
        ("codex", "codex_approval_policy", "danger-full-access"),
        ("codex", "codex_approval_policy", "approve-for-me"),
        ("codex", "codex_approval_policy", "dangerously-bypass-approvals-and-sandbox"),
        ("codex", "codex_approval_policy", "accept-edits"),
        ("codex", "codex_approval_policy", None),
    ),
)
def test_undeclared_or_unrestricted_policy_is_refused_before_the_attempt(
    tmp_path: Path, runtime: str, key: str, declared: str | None
) -> None:
    _repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime=runtime
    )
    _rewrite_parallel_key(descriptor, key, declared)
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64
    assert f"config parallel.{key} must declare one of" in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


def test_no_declaration_can_make_the_engine_emit_an_unrestricted_flag() -> None:
    launcher = _load_launcher()
    # The vocabulary is exactly these members; a grown vocabulary is a failure
    # here before any argv is examined.
    assert {
        runtime: set(policies) for runtime, policies in launcher.RUNTIME_APPROVAL_POLICIES.items()
    } == {
        "codex": {"read-only", "workspace-write"},
        "claude": {"dont-ask", "accept-edits"},
    }
    forbidden = (
        "bypassPermissions",
        "--dangerously-skip-permissions",
        "--allow-dangerously-skip-permissions",
        "danger-full-access",
        "--dangerously-bypass-approvals-and-sandbox",
        "--dangerously-bypass-hook-trust",
        "--approve-for-me",
        "auto",
        "manual",
        "plan",
    )
    for policies in launcher.RUNTIME_APPROVAL_POLICIES.values():
        for argv in policies.values():
            assert not set(argv) & set(forbidden), argv
    assert launcher.CLAUDE_SETTING_SOURCES_ARGS == ("--setting-sources", "")


@pytest.mark.parametrize(
    ("entry", "widens"),
    (
        ("Bash", True),
        ("Bash()", True),
        ("Bash(*)", True),
        ("Bash(**)", True),
        ("Bash(?*)", True),
        ("Bash(:*)", True),
        ("Bash(*:*)", True),
        ("Bash( ** )", True),
        ("Bash(*git:*)", True),
        ("Bash(/*)", True),
        ("Bash(.*)", True),
        ("Bash(~*)", True),
        ("Bash(/**)", True),
        ("Bash(../*)", True),
        ("Bash(~/*)", True),
        ("Bash(/)", True),
        ("Bash(. rm*)", True),
        ("Bash(~ rm:*)", True),
        ("Bash( git:*)", True),
        ("Bash (git:*)", True),
        ("Bash:*", True),
        ("Bash*", True),
        ("Bash!", True),
        ("Bash{git:*}", True),
        ("Bash(git:*", True),
        ("  Bash(*)  ", True),
        ("Bash(git:*)", False),
        ("Bash(git status:*)", False),
        ("Bash(/usr/bin/git:*)", False),
        ("Bash(./run.sh:*)", False),
        ("Bash(~/bin/tool:*)", False),
        ("Bash(g*)", False),
        # A literal prefix that names a shell is the adopter's declaration; the
        # guard judges the shape of the prefix, not the command.
        ("Bash(sh:*)", False),
        ("Bash(/bin/sh -c:*)", False),
        ("Bashful", False),
        ("BashOutput", False),
        ("Read", False),
        ("WebFetch(domain:*)", False),
    ),
)
def test_whole_tool_bash_is_decided_by_structure_not_by_spelling(
    entry: str, widens: bool
) -> None:
    launcher = _load_launcher()
    assert launcher._bash_allow_has_no_literal_prefix(entry) is widens


@pytest.mark.parametrize(
    ("entry", "escapes"),
    (
        ("Write", True),
        ("Edit", True),
        ("MultiEdit", True),
        ("NotebookEdit", True),
        ("  Write  ", True),
        ("Write()", True),
        ("Write( )", True),
        ("Write:*", True),
        ("Write (**)", True),
        ("Write(//private/tmp/**)", True),
        ("Write(~/**)", True),
        ("Edit(../**)", True),
        ("Edit(..)", True),
        # A `..` segment anywhere is a declared escape (panel round 6); a single
        # leading `/` anchors at the worktree root and is inside.
        ("Write(sub/../../outside.txt)", True),
        ("Write(notes/**/../../x)", True),
        ("Edit(C:/Users/x/**)", True),
        ("Edit(C:\\Users\\x\\**)", True),
        ("Edit(c:/**)", True),
        ("Edit(\\\\server\\share\\**)", True),
        ("Write(\\x)", True),
        ("Edit(notes/C:/**)", False),
        ("Write(/notes/**)", False),
        ("Write(notes/..hidden/**)", False),
        ("Write(**)", False),
        ("Edit(./**)", False),
        ("MultiEdit(notes/**)", False),
        ("NotebookEdit(**)", False),
        ("Write(.env)", False),
        ("WriteFile", False),
        ("Read", False),
        ("Bash(git status:*)", False),
    ),
)
def test_edit_tool_allow_must_be_scoped_inside_the_worktree(entry: str, escapes: bool) -> None:
    launcher = _load_launcher()
    assert launcher._edit_allow_escapes_the_worktree(entry) is escapes


@pytest.mark.parametrize(
    ("profile", "fragment"),
    (
        (b"{not json", "not valid JSON"),
        (b"[]\n", "one JSON object"),
        ({}, "permissions object"),
        ({"permissions": []}, "permissions object"),
        ({"permissions": {"allow": [], "defaultMode": "bypassPermissions"}}, "defaultMode"),
        ({"permissions": {"allow": [], "defaultMode": "acceptEdits"}}, "defaultMode"),
        # The permissions object carries only the three rule lists. A profile
        # widening tool access through `additionalDirectories` (the settings form
        # of `--add-dir`) passed the validator with no rule in any list, with or
        # without an allow list beside it; any key outside the closed set is
        # refused rather than passed through (panel round 14, adversarial lens).
        (
            {"permissions": {"allow": ["Edit(**)"], "additionalDirectories": ["/etc", "/"]}},
            "permissions.additionalDirectories",
        ),
        ({"permissions": {"additionalDirectories": ["/"]}}, "permissions.additionalDirectories"),
        ({"permissions": {"allow": [], "additionalDirectories": []}}, "permissions.additionalDirectories"),
        (
            {"permissions": {"allow": [], "disableBypassPermissionsMode": "disable"}},
            "permissions.disableBypassPermissionsMode",
        ),
        ({"permissions": {"allow": [], "Allow": ["Bash"]}}, "permissions.Allow"),
        ({"permissions": {"allow": ["Bash"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(*:*)"]}}, "widens Bash"),
        ({"permissions": {"allow": [" Bash "]}}, "widens Bash"),
        # Whitespace inside the spelling and the empty-prefix form are the same
        # allowance (panel round 1, adversarial lens).
        ({"permissions": {"allow": ["Bash( * )"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(*: *)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash (*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(:*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash( : * )"]}}, "widens Bash"),
        # Any pattern with no literal command prefix, not a list of spellings:
        # `Bash(**)` was unrestricted live at 2.1.247 while an enumeration missed
        # it (panel round 2, adversarial lens).
        ({"permissions": {"allow": ["Bash(**)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(***)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash( ** )"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(?*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(*git:*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(-c:*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(git status:*)", "Bash(**)"]}}, "widens Bash"),
        # A lone path character in front of a wildcard is every absolute-path
        # command (panel round 3, adversarial lens).
        ({"permissions": {"allow": ["Bash(/*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(.*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(~*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(/**)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(../*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(/ *)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(/:*)"]}}, "widens Bash"),
        # Inside the parentheses a space is literal and ends the head, so a
        # word after it does not lend the head a letter (panel round 4).
        ({"permissions": {"allow": ["Bash(. rm*)"]}}, "widens Bash"),
        ({"permissions": {"allow": ["Bash(/ rm:*)"]}}, "widens Bash"),
        # An edit tool is bounded only by a path pattern relative to the worktree
        # root: a bare tool name wrote `../outside-probe.txt` live at 2.1.247.
        ({"permissions": {"allow": ["Write"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Edit"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["MultiEdit"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["NotebookEdit"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Write()"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Write(//private/tmp/**)"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Write(~/**)"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Edit(../**)"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Write(sub/../../outside.txt)"]}}, "beyond the worktree"),
        ({"permissions": {"allow": ["Write:*"]}}, "beyond the worktree"),
        ({"permissions": {"allow": "Bash(git:*)"}}, "list of strings"),
        ({"permissions": {"allow": [1]}}, "list of strings"),
    ),
)
def test_widening_or_malformed_settings_profile_is_a_refused_trust_step(
    tmp_path: Path, profile: dict[str, object] | bytes, fragment: str
) -> None:
    _repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", profile=profile
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64, result.stderr
    assert "lane settings profile" in result.stderr and fragment in result.stderr
    assert not Path(descriptor["session_dir"], "launch-attempt.json").exists()


@pytest.mark.parametrize(
    "profile",
    (
        # Only `allow` can widen: a whole-tool entry under `deny` narrows and one
        # under `ask` is a denial in an unattended `-p` lane, so both are accepted
        # (panel round 1, correctness lens). A prefixed allow is bounded.
        {"permissions": {"allow": [], "deny": ["Bash"]}},
        {"permissions": {"allow": [], "ask": ["Bash", "Bash(*)"]}},
        {"permissions": {"allow": ["Bash(git status:*)", "Bash(gh pr view:*)"]}},
        # A literal prefix may be an absolute or relative command path, and a
        # non-Bash rule is outside this guard's claim.
        {"permissions": {"allow": ["Bash(/opt/homebrew/bin/gh pr view:*)", "Bash(./scripts/run.sh:*)"]}},
        {"permissions": {"allow": ["Bash(git*)", "Read", "WebFetch(domain:example.com)"]}},
        # Path-scoped edit tools are bounded by the worktree root.
        {"permissions": {"allow": ["Write(**)", "Edit(**)", "MultiEdit(notes/**)", "NotebookEdit(**)"]}},
    ),
)
def test_bounded_or_narrowing_settings_profile_is_accepted(
    tmp_path: Path, profile: dict[str, object]
) -> None:
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", profile=profile
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 0, result.stderr
    assert _receipt(sessions, descriptor)["status"] == "completed"


def test_missing_symlinked_or_undeclared_settings_profile_is_refused(tmp_path: Path) -> None:
    repo, engine_dir, _sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude"
    )
    profile_path = repo / "config" / "claude-lane-settings.json"
    attempt = Path(descriptor["session_dir"], "launch-attempt.json")

    profile_path.unlink()
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64 and "not a regular file" in result.stderr
    assert not attempt.exists()

    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text(json.dumps(LANE_PROFILE), encoding="utf-8")
    profile_path.symlink_to(elsewhere)
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64 and "not a regular file" in result.stderr
    assert not attempt.exists()

    profile_path.unlink()
    profile_path.write_text(json.dumps(LANE_PROFILE), encoding="utf-8")
    _rewrite_parallel_key(descriptor, "claude_settings_profile", None)
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 64
    assert "config parallel.claude_settings_profile must name the lane settings profile" in result.stderr
    assert not attempt.exists()

    # Codex has no profile key and does not read one: a missing file is not a
    # Codex refusal.
    codex = _install_repo(tmp_path / "codex", runtime="codex", profile_key=None)
    (codex[0] / "config" / "claude-lane-settings.json").unlink()
    result = _run_launcher(codex[1], codex[3], codex[4], codex[5])
    assert result.returncode == 0, result.stderr


def test_absolute_profile_path_outside_the_repository_is_accepted_and_bound(
    tmp_path: Path,
) -> None:
    elsewhere = tmp_path / "operator-profile.json"
    elsewhere.write_text(json.dumps(LANE_PROFILE), encoding="utf-8")
    _repo, engine_dir, sessions, descriptor, prompt, env = _install_repo(
        tmp_path, runtime="claude", profile_key=str(elsewhere)
    )
    result = _run_launcher(engine_dir, descriptor, prompt, env)
    assert result.returncode == 0, result.stderr
    receipt = _receipt(sessions, descriptor)
    assert receipt["request"]["approval_policy"]["settings_profile_path"] == str(elsewhere.resolve())
    assert receipt["request"]["approval_policy"]["settings_profile_sha256"] == hashlib.sha256(
        elsewhere.read_bytes()
    ).hexdigest()
    assert "--settings" in receipt["observed"]["argv"]
    assert receipt["observed"]["argv"][receipt["observed"]["argv"].index("--settings") + 1] == str(
        elsewhere.resolve()
    )


def test_profile_rewritten_after_the_parent_read_is_refused_by_the_child(
    tmp_path: Path,
) -> None:
    # Locally recomputed hostile transition: the parent bound one profile digest
    # into the attempt; the child's own read resolves to different bytes. The
    # request bindings differ, so the child is not bound to the attempt.
    launcher = _load_launcher()
    transports = {"worktree": "process-cwd", "prompt": "stdin", "final_text": "json-stdout"}
    parent_profile = launcher.RuntimeProfile(
        "claude", ["/bin/claude", "-p"], transports, _approval(
            "accept-edits", ["--settings", "/p.json"], profile="/p.json"
        )
    )
    child_profile = launcher.RuntimeProfile(
        "claude", ["/bin/claude", "-p"], transports, {
            **_approval("accept-edits", ["--settings", "/p.json"], profile="/p.json"),
            "settings_profile_sha256": "q" * 64,
        }
    )
    session = tmp_path / "session"
    session.mkdir()
    descriptor_id = "0f2d8e2e-2a3d-4b3e-9d1f-1c2d3e4f5a6b"
    capability = b"c" * 32
    request = launcher._request_binding(
        b"descriptor",
        task_sha256="t",
        combined_prompt_sha256="c",
        profile=parent_profile,
        process_nonce=capability.hex(),
    )
    attempt = {
        "schema_version": launcher.SCHEMA_VERSION,
        "status": "starting",
        "descriptor_id": descriptor_id,
        "request": request,
        # The child compares against its parent's pid; this test is its own child.
        "parent_process": {"pid": os.getppid(), "start_fingerprint": None},
        "started_at": "2026-08-27T00:00:00Z",
    }
    launcher._write_atomic(session / "launch-attempt.json", attempt)
    descriptor = {"descriptor_id": descriptor_id, "session_dir": str(session)}

    def arguments() -> object:
        read_end, write_end = os.pipe()
        os.write(write_end, capability)
        os.close(write_end)
        return type(
            "Arguments",
            (),
            {
                "descriptor_id": descriptor_id,
                "attempt": str(session / "launch-attempt.json"),
                "receipt": str(session / f"launch-receipt-{descriptor_id}.json"),
                "final_message": str(session / f"launch-final-{descriptor_id}.txt"),
                "task_sha256": "t",
                "combined_prompt_sha256": "c",
                "authority_fd": read_end,
            },
        )()

    # The parent's own profile binds.
    assert launcher._validate_child_authority(
        arguments(), descriptor, b"descriptor", parent_profile
    ) == capability.hex()
    # A profile whose bytes changed does not, even though every other field matches.
    with pytest.raises(launcher.LaunchError, match="not bound to the exclusive parent launch attempt"):
        launcher._validate_child_authority(arguments(), descriptor, b"descriptor", child_profile)


@pytest.mark.parametrize(
    "dropped",
    (
        ("--settings", "/profile.json"),
        ("--setting-sources", ""),
        ("--permission-mode", "acceptEdits"),
        ("--sandbox", "read-only"),
    ),
)
def test_observed_argv_that_omits_the_policy_or_trust_step_fails_parent_validation(
    dropped: tuple[str, str],
) -> None:
    # The trust step skipped while the receipt claims it: `request` still carries
    # the profile digest, only the exec'd argv lost the flag. The parent compares
    # the argv the child recorded against its own expectation and refuses.
    launcher = _load_launcher()
    expected = [
        "/bin/runtime",
        "--setting-sources",
        "",
        "--permission-mode",
        "acceptEdits",
        "--settings",
        "/profile.json",
        "--sandbox",
        "read-only",
        "--output-format",
        "json",
    ]
    index = expected.index(dropped[0])
    assert expected[index : index + 2] == list(dropped)
    mutated = expected[:index] + expected[index + 2 :]
    request = {"approval_policy": {"settings_profile_sha256": "p" * 64}}

    def receipt(argv: list[str]) -> dict[str, object]:
        return {
            "status": "observed",
            "descriptor_id": "descriptor",
            "request": copy.deepcopy(request),
            "observed": {
                "argv": argv,
                "process": {"pid": 41, "capability_nonce": "nonce", "start_fingerprint": None},
            },
        }

    launcher._validate_parent_binding(
        receipt(list(expected)),
        descriptor_id="descriptor",
        request=request,
        pid=41,
        process_nonce="nonce",
        live_start_fingerprint=None,
        expected_argv=expected,
    )
    with pytest.raises(launcher.LaunchError, match="durable child observation"):
        launcher._validate_parent_binding(
            receipt(mutated),
            descriptor_id="descriptor",
            request=request,
            pid=41,
            process_nonce="nonce",
            live_start_fingerprint=None,
            expected_argv=expected,
        )
    # An observation with no argv at all is not "nothing to compare".
    with pytest.raises(launcher.LaunchError, match="durable child observation"):
        missing = receipt(list(expected))
        del missing["observed"]["argv"]
        launcher._validate_parent_binding(
            missing,
            descriptor_id="descriptor",
            request=request,
            pid=41,
            process_nonce="nonce",
            live_start_fingerprint=None,
            expected_argv=expected,
        )


@pytest.mark.kit_repo_only("config/dev-model.yaml", "config/claude-lane-settings.json")
def test_shipped_config_declares_a_bounded_policy_and_the_shipped_profile_validates() -> None:
    launcher = _load_launcher()
    root = ENGINE_DIR.parent
    config = launcher.load_config(root / "config" / "dev-model.yaml", overlay=False)
    codex = launcher._approval_for_runtime("codex", config, root)
    claude = launcher._approval_for_runtime("claude", config, root)
    assert codex == {
        "declared": "read-only",
        "argv": ["--sandbox", "read-only"],
        "settings_profile_path": None,
        "settings_profile_sha256": None,
    }
    profile = root / "config" / "claude-lane-settings.json"
    # The shipped bytes pass the validator directly, not only through the
    # resolution above (panel round 6, correctness lens).
    launcher._validate_settings_profile(profile.read_bytes(), profile)
    assert claude["declared"] == "dont-ask"
    assert claude["settings_profile_path"] == str(profile.resolve())
    assert claude["settings_profile_sha256"] == hashlib.sha256(profile.read_bytes()).hexdigest()
    assert claude["argv"] == [
        "--setting-sources",
        "",
        "--permission-mode",
        "dontAsk",
        "--settings",
        str(profile.resolve()),
    ]
    shipped = json.loads(profile.read_text(encoding="utf-8"))
    assert set(shipped) == {"permissions"}
    assert set(shipped["permissions"]) == {"allow", "deny"}
    assert set(shipped["permissions"]) <= set(launcher.PERMISSION_RULE_LISTS)
    # Landing is the cockpit's: the merge command and the flag spellings of a
    # force push are denied. A prefix rule cannot express "contains a forced
    # update", so `git push origin +HEAD:main` is NOT denied by this profile
    # (panel round 4, live-reproduced); history protection is the forge's branch
    # protection and the lane contract, and this test claims no more.
    assert "Bash(gh pr merge:*)" in shipped["permissions"]["deny"]
    # The push allow is the form the lane contract names and the narrowest a
    # token-boundary rule can express (panel round 8): the flag-first and no-`-u`
    # spellings do not match it; a hostile refspec after `origin` still does.
    assert "Bash(git push -u origin:*)" in shipped["permissions"]["allow"]
    assert "Bash(git push:*)" not in shipped["permissions"]["allow"]
    # `git remote` is granted as `get-url` only: a broad `git remote:*` let a lane
    # retarget `origin` and push elsewhere (panel round 11, live), and
    # `git remote -v:*` admitted `-v set-url` the same way (round 12, live).
    assert "Bash(git remote get-url:*)" in shipped["permissions"]["allow"]
    assert not any(
        entry.startswith("Bash(git remote") and entry != "Bash(git remote get-url:*)"
        for entry in shipped["permissions"]["allow"]
    )
    assert "Bash(git push --force:*)" in shipped["permissions"]["deny"]
    assert "Bash(git push -f:*)" in shipped["permissions"]["deny"]
    assert "Bash(gh pr merge:*)" not in shipped["permissions"]["allow"]
    # Under the shipped `dont-ask` the allow list bounds every call the runtime
    # does not accept on its own (a read-only Bash class is accepted regardless at
    # 2.1.247): the edit rule is `Edit(**)` and every Bash entry is a bounded
    # command prefix.
    # `Edit(**)` is the one rule that governs every file-editing tool at 2.1.247;
    # a `Write(...)` entry is inert there and is not shipped (panel round 7).
    assert "Edit(**)" in shipped["permissions"]["allow"]
    assert all(
        entry == "Edit(**)" or (entry.startswith("Bash(") and entry.endswith(":*)"))
        for entry in shipped["permissions"]["allow"]
    )
    # `#606` (2026-08-28, Claude Code 2.1.250) decided the three grants that were
    # open, on measurements in
    # `saved_plans/lane-permission-policy-evidence_2026-08-28/`. `make test` is the
    # `AGENTS.md` verification command and was refused under the profile as it
    # stood, so a lane's first verification was always CI; the grant is bounded to
    # the one target, because the runtime matches on token boundaries and
    # `make mutation-test` is refused by this entry (measured, not inferred).
    assert "Bash(make test:*)" in shipped["permissions"]["allow"]
    assert "Bash(make:*)" not in shipped["permissions"]["allow"]
    # `kit_doctor.py` is granted for BOTH engine layouts, exactly as `pr_watch.py`
    # is: `paths.engines` is the adopter's, and `scripts/devkit/` is the vendored
    # layout `.claude/rules/safety-critical-changes.md` supports. Without it a lane
    # that edits any kit-owned file cannot refresh the manifest, so its PR is
    # deterministically red and the cockpit must finish the work (`#625`).
    # Granted BARE rather than scoped to `--generate-manifest`, so that reading the
    # doctor's report before regenerating does not hit a denial — which under the
    # shipped `dont-ask` ends the whole run rather than costing a round trip.
    for engine_dir in ("scripts", "scripts/devkit"):
        assert f"Bash(uv run {engine_dir}/kit_doctor.py:*)" in shipped["permissions"]["allow"]
        assert f"Bash(uv run {engine_dir}/pr_watch.py:*)" in shipped["permissions"]["allow"]
    assert not any(
        entry.startswith("Bash(uv run") and "--generate-manifest" in entry
        for entry in shipped["permissions"]["allow"]
    )
    # What this profile does NOT claim, measured rather than reasoned (`#631`): a
    # `Bash(<interpreter> <worktree-path>)` entry names a file `Edit(**)` lets the
    # lane rewrite, so it composes into execution outside the worktree that no rule
    # in any list describes. Under the shipped bytes with nothing added, a lane
    # rewrote `scripts/pr_watch.py` and ran it, writing an absolute path outside the
    # worktree, and returned an empty `permission_denials`. The profile is
    # task-scoping — fail-closed for a CONFUSED lane — not a security boundary, and
    # no spelling of these entries changes that while the lane can write the file
    # each one names. This assertion pins the shape that carries the property, so a
    # future entry naming a worktree path is a deliberate choice and not a slip.
    assert [
        entry
        for entry in shipped["permissions"]["allow"]
        if entry.startswith("Bash(uv run")
    ] == [
        "Bash(uv run scripts/pr_watch.py:*)",
        "Bash(uv run scripts/devkit/pr_watch.py:*)",
        "Bash(uv run scripts/kit_doctor.py:*)",
        "Bash(uv run scripts/devkit/kit_doctor.py:*)",
    ]
