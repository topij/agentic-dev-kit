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


@pytest.mark.parametrize("case", ["success", "guest_failure", "extra_repo", "extra_permission"])
@pytest.mark.parametrize("revocation_failures", [0, 1, 2])
def test_scoped_token_revocation(monkeypatch, capsys, case, revocation_failures):
    calls = []
    revocations = []

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
        revocations.append(path)
        if len(revocations) <= revocation_failures:
            raise OSError("revocation unavailable")

    monkeypatch.setattr(host, "api", api)
    monkeypatch.setattr(host, "gh", lambda path: {"id": 3})
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"test-signature")
    expected = contextlib.nullcontext()
    if case != "success":
        error = "guest failed" if case == "guest_failure" else "token scope"
        expected = pytest.raises(ValueError, match=error)
    elif revocation_failures == 2:
        expected = pytest.raises(OSError, match="revocation unavailable")
    with expected, host.installation_token(REPO, 1, Path("test-key")):
        if case == "guest_failure":
            raise ValueError("guest failed")
    assert calls[-1] == ("DELETE", "installation/token")
    assert len(revocations) == min(revocation_failures + 1, 2)
    assert ("Suspend the App installation" in capsys.readouterr().err) == (revocation_failures == 2)


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


def test_host_resolves_repository_and_supplies_branch(monkeypatch, tmp_path):
    from types import SimpleNamespace

    engines = tmp_path / "scripts"
    (engines / "lib").mkdir(parents=True)
    (engines / "lib/isolated_guest.py").write_text("guest fixture")
    prompt = tmp_path / "prompt"
    prompt.write_text("task")
    work = tmp_path / "vm"
    work.mkdir()
    head = "a" * 40
    branch = "local-prefix/fixture"
    checked_repositories = []
    monkeypatch.setattr(host, "ENGINE", engines)
    monkeypatch.setattr(host, "repo_root", lambda path: tmp_path)
    monkeypatch.setattr(
        host,
        "load_config",
        lambda path: {
            "vcs": {"protected_branch": "main", "dev_branch_prefix": "local-prefix"},
            "parallel": {
                "isolated_image_url": "https://example.com/image",
                "isolated_image_sha512": "a" * 128,
            },
        },
    )
    monkeypatch.setattr(host.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(host.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(host.tempfile, "mkdtemp", lambda **kwargs: str(work))
    monkeypatch.setattr(
        host.subprocess, "check_output", lambda *a, **kw: "git@github.com:Owner/Project.git\n"
    )

    def protected(repo, base):
        assert base == "main"
        checked_repositories.append(repo)
        return "base"

    def gh(path):
        if path == "repos/Owner/Project":
            return {"full_name": REPO}
        if path == "repos/owner/project/git/matching-refs/heads/local-prefix%2Ffixture":
            return []
        assert (
            path
            == "repos/owner/project/pulls?state=open&base=main&head=owner%3Alocal-prefix%2Ffixture"
        )
        return [
            {
                "user": {"login": "fixture[bot]"},
                "draft": False,
                "html_url": "fixture",
                "head": {"sha": head, "repo": {"full_name": REPO}, "ref": branch},
                "base": {"repo": {"full_name": REPO}, "ref": "main"},
            }
        ]

    @contextlib.contextmanager
    def token(repo, app_id, key):
        assert repo == REPO
        yield "fixture", "fixture[bot]"

    def lima(args, **kwargs):
        if "shell" in args:
            payload = json.loads(kwargs["input"])
            assert payload["repo"] == REPO
            assert payload["branch"] == branch
            return subprocess.CompletedProcess(args, 0, stdout=head.encode())
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(host, "protected_head", protected)
    monkeypatch.setattr(host, "gh", gh)
    monkeypatch.setattr(host, "installation_token", token)
    monkeypatch.setattr(host.subprocess, "run", lima)
    host.run_isolated(
        SimpleNamespace(
            scope="fixture", prompt_file=prompt, provision=None, app_id=1, app_key=Path("fixture")
        )
    )
    assert checked_repositories == [REPO, REPO]
    assert not work.exists()


def test_guest_passes_host_branch_to_lane_creation(monkeypatch, tmp_path):
    import io
    import sys

    monkeypatch.setenv("HOME", str(tmp_path))
    payload = {
        "token": "fixture",
        "model_key": None,
        "bot": "fixture[bot]",
        "repo": REPO,
        "base": "main",
        "head": "base",
        "engines": "scripts",
        "scope": "fixture",
        "branch": "host-prefix/fixture",
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    def run(args, **kwargs):
        if "new" in args:
            assert args[args.index("--branch") + 1] == "host-prefix/fixture"
            raise RuntimeError("inspected branch")
        return subprocess.CompletedProcess(args, 0, stdout=b"base\n")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="inspected branch"):
        guest.main()


@pytest.mark.parametrize("signal_name", ["SIGTERM", "SIGHUP"])
def test_shell_entry_forwards_termination_to_launcher(monkeypatch, tmp_path, signal_name):
    """Signals to the public wrapper must unwind the real host token context."""
    import os
    import shutil
    import signal
    import sys
    import textwrap
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
        textwrap.dedent(f"""\
        import importlib.util
        import os
        import signal
        from pathlib import Path

        spec = importlib.util.spec_from_file_location('host', {str(ENGINE / "isolated_lane.py")!r})
        host = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(host)
        events = Path({str(events)!r})

        def record(value):
            with events.open('a') as stream:
                stream.write(str(value) + '\\n')

        def api(method, path, token, data=None):
            if path.endswith('/installation'):
                return {{'app_id': 1, 'id': 2, 'app_slug': 'fixture'}}
            if path.endswith('/access_tokens'):
                return {{'token': 'fixture', 'permissions': host.PERMISSIONS}}
            if method == 'GET':
                return {{'total_count': 1, 'repositories': [{{'id': 3}}]}}
            record('revoked')

        def run(args):
            try:
                with host.installation_token('owner/project', 1, Path('fixture')):
                    record(os.getpid())
                    while True:
                        signal.pause()
            finally:
                record('stopped')

        host.api = api
        host.gh = lambda path: {{'id': 3}}
        host.subprocess.check_output = lambda *args, **kwargs: b'signature'
        host.run_isolated = run
        raise SystemExit(host.main())
        """)
    )
    shimdir = tmp_path / "bin"
    shimdir.mkdir()
    shim = shimdir / "python3"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\n"
        f"args=[{str(probe)!r}, *sys.argv[3:]] if sys.argv[1:2]==['-I'] else sys.argv[1:]\n"
        "os.execv(sys.executable,[sys.executable,*args])\n"
    )
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(shimdir) + os.pathsep + os.environ["PATH"])
    process = subprocess.Popen(
        [
            str(engines / "dev_session.sh"),
            "isolated",
            "fixture",
            "--app-id",
            "1",
            "--app-key",
            "fixture",
            "--prompt-file",
            "fixture",
        ],
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
        sent_signal = getattr(signal, signal_name)
        process.send_signal(sent_signal)
        _, stderr = process.communicate(timeout=10)
        assert process.returncode == 128 + sent_signal, stderr
        assert events.read_text().splitlines() == [str(process.pid), "revoked", "stopped"]
    finally:
        # Own the process group and finish every descendant even when the PID
        # equality regression fails before the termination assertion.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
