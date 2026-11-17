"""Regression checks for the isolated launch's credential and protected-branch boundary."""

import contextlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = Path(__file__).resolve().parents[1]
host = load_module("isolated_lane", ENGINE / "isolated_lane.py")
guest = load_module("isolated_guest", ENGINE / "lib/isolated_guest.py")
REPO = "owner/project"


@pytest.mark.parametrize(
    "mutation", ["valid", "app", "extra", "always", "evaluate", "hidden", "deletable"]
)
def test_effective_update_rule_requires_only_operator_pr_bypass(monkeypatch, mutation):
    actor = {"actor_id": 9, "actor_type": "User", "bypass_mode": "pull_request"}
    actors = [actor]
    detail = {
        "enforcement": "active",
        "rules": [{"type": "update"}, {"type": "deletion"}],
        "bypass_actors": actors,
    }
    if mutation == "deletable":
        detail["rules"] = [{"type": "update"}]
    if mutation == "app":
        actor["actor_type"] = "Integration"
    if mutation == "extra":
        actors.append({**actor, "actor_id": 12})
    if mutation == "always":
        actor["bypass_mode"] = "always"
    if mutation == "evaluate":
        detail["enforcement"] = "evaluate"
    if mutation == "hidden":
        del detail["bypass_actors"]
    responses = {
        "user": {"id": 9},
        f"repos/{REPO}/rules/branches/main": [
            {
                "type": "update",
                "ruleset_source_type": "Repository",
                "ruleset_source": REPO,
                "ruleset_id": 4,
            }
        ],
        f"repos/{REPO}/rulesets/4": detail,
        f"repos/{REPO}/branches/main": {"commit": {"sha": "base"}},
    }
    monkeypatch.setattr(host, "gh", responses.__getitem__)
    if mutation == "valid":
        assert host.protected_head(REPO, "main") == "base"
    else:
        with pytest.raises(ValueError, match="operator-only"):
            host.protected_head(REPO, "main")


@pytest.mark.parametrize("case", ["guest_failure", "extra_repo", "extra_permission"])
def test_scoped_token_revoked_on_failed_validation_or_guest(monkeypatch, case):
    calls = []

    def api(method, path, token, data=None):
        calls.append((method, path))
        if path.endswith("/installation"):
            return {"app_id": 1, "id": 2, "app_slug": "fixture", "suspended_at": None}
        if path.endswith("/access_tokens"):
            assert data == {"repository_ids": [3], "permissions": host.PERMISSIONS}
            perms = dict(host.PERMISSIONS)
            if case == "extra_permission":
                perms["actions"] = "write"
            return {"token": "test-token", "permissions": perms}
        if method == "GET":
            return {"total_count": 2 if case == "extra_repo" else 1, "repositories": [{"id": 3}]}
        assert token == "test-token"

    monkeypatch.setattr(host, "api", api)
    monkeypatch.setattr(host, "gh", lambda path: {"id": 3})
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"test-signature")
    error = "guest failed" if case == "guest_failure" else "token scope"
    with pytest.raises(ValueError, match=error), host.installation_token(REPO, 1, Path("test-key")):
        assert case == "guest_failure"
        raise ValueError("guest failed")
    assert calls[-1] == ("DELETE", "installation/token")


def test_guest_uses_allowlist_before_first_child(monkeypatch, tmp_path):
    import io
    import sys

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GH_TOKEN", "operator")
    monkeypatch.setenv("GITHUB_TOKEN", "operator")
    monkeypatch.setenv("SSH_AUTH_SOCK", "operator")
    monkeypatch.setenv("UNRELATED_SECRET", "operator")
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"token": "fixture", "model_key": None}))
    )

    def inspect(args, *, env, **kwargs):
        assert args == ["gh", "auth", "setup-git", "--hostname", "github.com"]
        assert set(env) == {
            "HOME",
            "PATH",
            "LANG",
            "GH_TOKEN",
            "GH_PROMPT_DISABLED",
            "GIT_TERMINAL_PROMPT",
        }
        assert env["GH_TOKEN"] == "fixture"
        raise RuntimeError("inspected")

    monkeypatch.setattr(subprocess, "run", inspect)
    with pytest.raises(RuntimeError, match="inspected"):
        guest.main()


def test_shell_entry_forwards_termination_to_launcher(monkeypatch, tmp_path):
    """A SIGTERM to the public wrapper must reach the cleanup-owning process."""
    import os
    import shutil
    import signal
    import sys
    import time

    root = tmp_path / "repo"
    engines = root / "scripts"
    (engines / "lib").mkdir(parents=True)
    shutil.copy(ENGINE / "dev_session.sh", engines / "dev_session.sh")
    shutil.copy(ENGINE / "lib/repo_root.sh", engines / "lib/repo_root.sh")
    (root / "config").mkdir()
    (root / "config/dev-model.yaml").write_text("vcs:\n  protected_branch: main\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    events = tmp_path / "events"
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import os,signal,time\n"
        "from pathlib import Path\n"
        f"events=Path({str(events)!r})\n"
        "def terminate(signum,frame): raise SystemExit(128+signum)\n"
        "signal.signal(signal.SIGTERM,terminate)\n"
        "try:\n"
        "    events.write_text(str(os.getpid()))\n"
        "    while True: signal.pause()\n"
        "finally: events.write_text('cleanup')\n"
    )
    shimdir = tmp_path / "bin"
    shimdir.mkdir()
    shim = shimdir / "python3"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\n"
        f"args=[{str(probe)!r}] if sys.argv[1:2]==['-I'] else sys.argv[1:]\n"
        "os.execv(sys.executable,[sys.executable,*args])\n"
    )
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(shimdir) + os.pathsep + os.environ["PATH"])
    process = subprocess.Popen(
        [str(engines / "dev_session.sh"), "isolated", "fixture"],
        cwd=root,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not events.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert events.exists(), process.poll()
        assert int(events.read_text()) == process.pid
        process.send_signal(signal.SIGTERM)
        _, stderr = process.communicate(timeout=10)
        assert process.returncode == 143, stderr
        assert events.read_text() == "cleanup"
    finally:
        # Own the process group and finish every descendant even when the PID
        # equality regression fails before the termination assertion.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
