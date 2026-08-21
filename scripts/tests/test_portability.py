from __future__ import annotations

import ast
import contextlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no repository root above {start}")


REPO_ROOT = _find_repo_root(ENGINE_DIR)


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_nested_shell_engines(repo: Path) -> Path:
    engine_dir = repo / "scripts" / "devkit"
    (engine_dir / "lib").mkdir(parents=True)
    shutil.copy2(ENGINE_DIR / "dev_session.sh", engine_dir / "dev_session.sh")
    shutil.copy2(
        ENGINE_DIR / "reconcile_sessions.sh",
        engine_dir / "reconcile_sessions.sh",
    )
    shutil.copy2(
        ENGINE_DIR / "lib" / "repo_root.sh",
        engine_dir / "lib" / "repo_root.sh",
    )
    (repo / ".git").mkdir()
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text(
        """paths:
  handoff: handoff.md
  friction_log: friction-log.md
runtime:
  default: codex
  launchers:
    claude: claude
    codex: codex
vcs:
  protected_branch: trunk
""",
        encoding="utf-8",
    )
    return engine_dir


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )


def _install_real_trunk_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
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
    (repo / ".gitignore").write_text("state/\n.devkit_state_root\n", encoding="utf-8")
    _git(repo, "add", "README.md", ".gitignore")
    _git(repo, "commit", "-m", "seed")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "trunk")

    engine_dir = repo / "scripts" / "devkit"
    shutil.copytree(ENGINE_DIR, engine_dir)
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text(
        """paths:
  handoff: handoff.md
  friction_log: friction-log.md
runtime:
  default: codex
  launchers:
    claude: claude
    codex: codex
vcs:
  protected_branch: trunk
  dev_branch_prefix: lane
""",
        encoding="utf-8",
    )
    sessions = tmp_path / "sessions"
    return repo, engine_dir, sessions


def test_nested_shell_engines_find_the_repository_root(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)

    result = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "list"],
        check=True,
        capture_output=True,
        text=True,
    )

    expected_sessions = repo.parent / "dev-model-sessions"
    assert f"no sessions — {expected_sessions} does not exist yet" in result.stdout


def test_nested_launcher_resolves_runtime_mapping(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)
    script = engine_dir / "dev_session.sh"

    result = subprocess.run(
        ["bash", "-c", 'source "$1"; _resolve_launcher "" ""', "bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == "codex\tcodex\n"


def test_nested_lane_contract_uses_configured_paths(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    engine_dir = _install_nested_shell_engines(repo)
    script = engine_dir / "dev_session.sh"

    result = subprocess.run(
        ["bash", "-c", 'source "$1"; _lane_contract', "bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "scripts/devkit/pr_watch.py" in result.stdout
    assert "Never edit handoff.md or friction-log.md" in result.stdout
    assert "never trunk" in result.stdout


def test_real_headless_lane_uses_configured_base_and_replaces_inherited_state(
    tmp_path: Path,
) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    inherited = tmp_path / "cockpit-state"
    env = {
        **os.environ,
        "DEVKIT_SESSIONS_DIR": str(sessions),
        "DEVKIT_STATE_ROOT": str(inherited),
    }

    result = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "new",
            "probe",
            "--headless",
            "--merge-class",
            "self",
        ],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    descriptor = json.loads(result.stdout)

    assert descriptor["base"] == "trunk"
    assert descriptor["branch"] == "lane/probe"
    assert descriptor["merge_class"] == "self"
    assert descriptor["env"]["DEVKIT_STATE_ROOT"] == descriptor["state_root"]
    assert descriptor["env"]["DEVKIT_STATE_ROOT"] != str(inherited)
    assert descriptor["env"]["DEVKIT_ROOT"] == str(repo)
    assert (
        Path(descriptor["worktree"], ".devkit_state_root").read_text().strip()
        == descriptor["state_root"]
    )
    assert (sessions / "probe" / "merge_class").read_text().strip() == "self"

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_gh = fake_bin / "gh"
    fake_gh.write_text("#!/bin/sh\nprintf '[]\\n'\n", encoding="utf-8")
    fake_gh.chmod(0o755)
    reconcile = subprocess.run(
        ["bash", str(engine_dir / "reconcile_sessions.sh"), "probe"],
        cwd=repo,
        env={**env, "PATH": f"{fake_bin}:{env['PATH']}"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert "EMPTY — 0 commits, never started" in reconcile.stdout

    subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "rm",
            "probe",
            "--keep-branch",
        ],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert not (sessions / "probe").exists()


def test_force_recreate_refuses_configured_protected_branch_before_mutation(
    tmp_path: Path,
) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "new", "probe", "--headless"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    refused = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "new",
            "probe",
            "--base",
            "main",
            "--branch",
            "trunk",
            "--force",
        ],
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert refused.returncode != 0
    assert "refusing to use protected branch 'trunk'" in refused.stderr
    assert _git(repo, "show-ref", "--verify", "refs/heads/trunk").returncode == 0
    assert (sessions / "probe" / "wt").is_dir()


def test_single_quoted_protected_branch_is_still_protected(tmp_path: Path) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "new", "probe", "--headless"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    config = repo / "config" / "dev-model.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "protected_branch: trunk", "protected_branch: 'trunk'"
        ),
        encoding="utf-8",
    )

    refused = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "new",
            "probe",
            "--base",
            "main",
            "--branch",
            "trunk",
            "--force",
        ],
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert refused.returncode != 0
    assert "refusing to use protected branch 'trunk'" in refused.stderr
    assert _git(repo, "show-ref", "--verify", "refs/heads/trunk").returncode == 0
    assert (sessions / "probe" / "wt").is_dir()


@pytest.mark.parametrize(
    "vcs_block,expected_error",
    [
        ("vcs:\n  dev_branch_prefix: lane\n", "must define vcs.protected_branch"),
        (
            "vcs:\n  protected_branch: 'not a branch'\n  dev_branch_prefix: lane\n",
            "invalid vcs.protected_branch",
        ),
    ],
)
def test_missing_or_invalid_protected_branch_fails_before_mutation(
    tmp_path: Path, vcs_block: str, expected_error: str
) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "new", "probe", "--headless"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    config = repo / "config" / "dev-model.yaml"
    before_vcs = "vcs:\n  protected_branch: trunk\n  dev_branch_prefix: lane\n"
    config.write_text(
        config.read_text(encoding="utf-8").replace(before_vcs, vcs_block),
        encoding="utf-8",
    )

    refused = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "new",
            "probe",
            "--base",
            "main",
            "--branch",
            "trunk",
            "--force",
        ],
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert refused.returncode != 0
    assert expected_error in refused.stderr
    assert _git(repo, "show-ref", "--verify", "refs/heads/trunk").returncode == 0
    assert (sessions / "probe" / "wt").is_dir()


def test_operator_merge_class_refuses_before_contacting_github(tmp_path: Path) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    env = {**os.environ, "DEVKIT_SESSIONS_DIR": str(sessions)}
    subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "new", "probe", "--headless"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "merge", "probe"],
        cwd=repo,
        env={**env, "PATH": "/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "operator-merge" in result.stderr


def _prepare_self_merge_session(sessions: Path) -> Path:
    session = sessions / "probe"
    (session / "state").mkdir(parents=True)
    (session / "merge_class").write_text("self\n", encoding="utf-8")
    (session / "branch").write_text("lane/probe\n", encoding="utf-8")
    (session / "base").write_text("trunk\n", encoding="utf-8")
    return session


def _install_fake_merge_tools(tmp_path: Path) -> tuple[Path, Path, Path]:
    fake_bin = tmp_path / "merge-bin"
    fake_bin.mkdir()
    call_log = tmp_path / "gh-calls.log"
    uv_log = tmp_path / "uv-calls.log"
    gh = fake_bin / "gh"
    gh.write_text(
        """#!/bin/sh
printf '%s|%s|%s\n' "$PWD" "${GH_REPO:-unset}" "$*" >> "$CALL_LOG"
if [ "$1 $2" = "repo view" ]; then
  printf '{"nameWithOwner":"%s"}\n' "${GH_REPO:-owner/project}"
elif [ "$1 $2" = "pr list" ]; then
  printf '%s\n' "$PR_JSON"
elif [ "$1 $2" = "pr merge" ]; then
  exit "${MERGE_EXIT:-0}"
else
  exit 91
fi
""",
        encoding="utf-8",
    )
    gh.chmod(0o755)
    uv = fake_bin / "uv"
    uv.write_text(
        """#!/bin/sh
printf '%s|%s|%s\n' "$DEVKIT_STATE_ROOT" "${GH_REPO:-unset}" "$*" >> "$UV_LOG"
printf '%s\n' "$REPORT_JSON"
""",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    return fake_bin, call_log, uv_log


def test_self_merge_refuses_wrong_base_and_binds_gh_to_repo(tmp_path: Path) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    _prepare_self_merge_session(sessions)
    fake_bin, call_log, uv_log = _install_fake_merge_tools(tmp_path)
    caller = tmp_path / "unrelated-caller"
    caller.mkdir()
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "DEVKIT_SESSIONS_DIR": str(sessions),
        "CALL_LOG": str(call_log),
        "UV_LOG": str(uv_log),
        "PR_JSON": json.dumps(
            [
                {
                    "number": 8,
                    "baseRefName": "wrong-base",
                    "headRefName": "lane/probe",
                    "headRefOid": "listed-head",
                    "headRepositoryOwner": {"login": "owner"},
                }
            ]
        ),
        "REPORT_JSON": "{}",
        "GH_REPO": "attacker/other",
    }

    result = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "merge", "probe"],
        cwd=caller,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "not recorded base 'trunk'" in result.stderr
    assert not uv_log.exists()
    assert all(
        line.startswith(f"{repo}|") for line in call_log.read_text().splitlines()
    )
    calls = call_log.read_text(encoding="utf-8")
    assert f"{repo}|unset|repo view" in calls
    assert f"{repo}|owner/project|pr list" in calls


def test_self_merge_refuses_a_report_that_is_done_but_not_mergeable(
    tmp_path: Path,
) -> None:
    """The gate reads `mergeable`, and fails CLOSED when it is false or absent.

    Two cases, deliberately pinned together:

    - **`mergeable: false` alongside `done: true`.** These are equal in any report
      the engine actually produces, so this input is intentionally inconsistent:
      it proves the gate reads `mergeable` and does not quietly fall back to
      `done` if the two ever diverge.
    - **`mergeable` absent entirely.** An OLDER or foreign ``pr_watch`` predating
      the field emits only ``done``. The gate must read that as "not authorized"
      rather than merging on an assumption about the missing key.

    A gate that failed open in either case would merge unreviewed work.
    """
    _, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    _prepare_self_merge_session(sessions)
    fake_bin, call_log, uv_log = _install_fake_merge_tools(tmp_path)
    pr_json = json.dumps(
        [
            {
                "number": 8,
                "baseRefName": "trunk",
                "headRefName": "lane/probe",
                "headRefOid": "reviewed-head",
                "headRepositoryOwner": {"login": "owner"},
            }
        ]
    )
    base_report = {"pr": 8, "base": "trunk", "head": "reviewed-head", "done": True}

    for label, report in (
        ("explicitly not mergeable", {**base_report, "mergeable": False}),
        ("pre-split engine, key absent", base_report),
    ):
        result = subprocess.run(
            ["bash", str(engine_dir / "dev_session.sh"), "merge", "probe"],
            cwd=tmp_path,
            env={
                **os.environ,
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "DEVKIT_SESSIONS_DIR": str(sessions),
                "CALL_LOG": str(call_log),
                "UV_LOG": str(uv_log),
                "PR_JSON": pr_json,
                "REPORT_JSON": json.dumps(report),
                "GH_REPO": "attacker/other",
            },
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, label
        assert "not green, review-clean, and merge-ready" in result.stderr, label
        assert "pr merge" not in call_log.read_text(encoding="utf-8"), label


def test_self_merge_pins_validated_head_so_push_race_is_refused(tmp_path: Path) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    session = _prepare_self_merge_session(sessions)
    fake_bin, call_log, uv_log = _install_fake_merge_tools(tmp_path)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "DEVKIT_SESSIONS_DIR": str(sessions),
        "CALL_LOG": str(call_log),
        "UV_LOG": str(uv_log),
        "PR_JSON": json.dumps(
            [
                {
                    "number": 8,
                    "baseRefName": "trunk",
                    "headRefName": "lane/probe",
                    "headRefOid": "listed-head",
                    "headRepositoryOwner": {"login": "owner"},
                }
            ]
        ),
        "REPORT_JSON": json.dumps(
            {
                "pr": 8,
                "base": "trunk",
                "head": "reviewed-head",
                "done": True,
                "mergeable": True,
            }
        ),
        # Simulate GitHub rejecting --match-head-commit because a new push won
        # the race after the act-time poll.
        "MERGE_EXIT": "17",
        "GH_REPO": "attacker/other",
    }

    result = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "merge", "probe"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "GitHub merge failed" in result.stderr
    calls = call_log.read_text(encoding="utf-8")
    assert f"{repo}|unset|repo view" in calls
    assert f"{repo}|owner/project|pr list" in calls
    assert f"{repo}|owner/project|pr merge" in calls
    assert (
        "pr merge --repo owner/project 8 --squash --delete-branch --match-head-commit reviewed-head"
        in calls
    )
    assert uv_log.read_text(encoding="utf-8").startswith(f"{session / 'state'}|")


def test_scope_pr_watch_and_merge_share_lane_state_and_pinned_repo(
    tmp_path: Path,
) -> None:
    repo, engine_dir, sessions = _install_real_trunk_repo(tmp_path)
    session = _prepare_self_merge_session(sessions)
    fake_bin, call_log, uv_log = _install_fake_merge_tools(tmp_path)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "DEVKIT_SESSIONS_DIR": str(sessions),
        "CALL_LOG": str(call_log),
        "UV_LOG": str(uv_log),
        "PR_JSON": json.dumps(
            [
                {
                    "number": 8,
                    "baseRefName": "trunk",
                    "headRefName": "lane/probe",
                    "headRefOid": "reviewed-head",
                    "headRepositoryOwner": {"login": "owner"},
                }
            ]
        ),
        "REPORT_JSON": json.dumps(
            {
                "pr": 8,
                "base": "trunk",
                "head": "reviewed-head",
                "done": True,
                "mergeable": True,
            }
        ),
        "GH_REPO": "attacker/other",
    }

    record = subprocess.run(
        [
            "bash",
            str(engine_dir / "dev_session.sh"),
            "pr-watch",
            "probe",
            "--record-review",
            "fallback:codex",
            "--head",
            "reviewed-head",
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    merge = subprocess.run(
        ["bash", str(engine_dir / "dev_session.sh"), "merge", "probe"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert record.returncode == 0, record.stderr
    assert merge.returncode == 0, merge.stderr
    uv_calls = uv_log.read_text(encoding="utf-8").splitlines()
    expected_prefix = f"{session / 'state'}|owner/project|"
    assert len(uv_calls) == 2
    assert all(line.startswith(expected_prefix) for line in uv_calls)
    assert "--record-review fallback:codex --head reviewed-head" in uv_calls[0]
    assert uv_calls[1].endswith("8 --json --no-persist")
    gh_calls = call_log.read_text(encoding="utf-8")
    assert "|attacker/other|" not in gh_calls
    assert f"{repo}|unset|repo view" in gh_calls
    assert f"{repo}|owner/project|pr merge" in gh_calls


def test_archive_defaults_follow_configured_paths(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    config_path = repo / "config" / "dev-model.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """paths:
  handoff: handoff.md
  handoff_history: saved/handoff-history.md
""",
        encoding="utf-8",
    )
    archive = _load_module(
        "archive_plan_sessions", ENGINE_DIR / "archive_plan_sessions.py"
    )

    plan, history = archive.configured_paths(root=repo, config_path=config_path)

    assert plan == repo / "handoff.md"
    assert history == repo / "saved" / "handoff-history.md"


def test_archive_supports_recent_sessions_layout(tmp_path: Path) -> None:
    archive = _load_module(
        "archive_recent_sessions", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    plan.write_text(
        """# Handoff

## Last updated

Current state.

## Recent sessions

### 2026-07-03 — Newest

Newest body.

---

### 2026-07-02 — Middle

Middle body.

---

### 2026-07-01 — Oldest

Oldest body.

---

## Strategic direction

Standing content.
""",
        encoding="utf-8",
    )
    history.write_text(
        """# Handoff history

## Recent sessions (archived)

### 2026-06-30 — Existing

Existing body.
""",
        encoding="utf-8",
    )

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    updated_plan = plan.read_text(encoding="utf-8")
    updated_history = history.read_text(encoding="utf-8")
    assert "### 2026-07-03 — Newest" in updated_plan
    assert "### 2026-07-02 — Middle" in updated_plan
    assert "### 2026-07-01 — Oldest" not in updated_plan
    assert "## Strategic direction\n\nStanding content." in updated_plan
    assert updated_history.index("### 2026-07-01 — Oldest") < updated_history.index(
        "### 2026-06-30 — Existing"
    )


def test_recent_session_nested_h3_stays_inside_its_dated_block(tmp_path: Path) -> None:
    archive = _load_module(
        "archive_recent_nested_heading", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    plan.write_text(
        """# Handoff

## Recent sessions

### 2026-07-03 — Newest

Newest body.

### 2026-07-02 — Older

Older body.

### Validation

Validation belongs to the older session.

## Backlog
""",
        encoding="utf-8",
    )
    history.write_text(
        "# History\n\n## Recent sessions (archived)\n",
        encoding="utf-8",
    )

    assert (
        archive.main(["--keep", "1", "--plan", str(plan), "--history", str(history)])
        == 0
    )
    archived = history.read_text(encoding="utf-8")
    assert "### 2026-07-02 — Older" in archived
    assert "### Validation\n\nValidation belongs to the older session." in archived


def test_archive_explicit_paths_do_not_require_config(
    tmp_path: Path, monkeypatch
) -> None:
    archive = _load_module(
        "archive_explicit_paths", ENGINE_DIR / "archive_plan_sessions.py"
    )
    monkeypatch.setattr(
        archive,
        "configured_paths",
        lambda: (_ for _ in ()).throw(AssertionError("config must not be read")),
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    plan.write_text(
        "# Handoff\n\n## Latest session — One\n\nBody.\n",
        encoding="utf-8",
    )
    history.write_text("# History\n\n## Session log\n", encoding="utf-8")

    assert (
        archive.main(["--plan", str(plan), "--history", str(history), "--dry-run"]) == 0
    )
    with pytest.raises(SystemExit) as exc:
        archive.main(["--help"])
    assert exc.value.code == 0


def test_archive_pointer_follows_configured_history_location(tmp_path: Path) -> None:
    archive = _load_module(
        "archive_dynamic_pointer", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "saved" / "handoff-history.md"
    history.parent.mkdir()
    plan.write_text(
        """# Handoff

## Latest session — New

New.

## Earlier session — Old

Old.
""",
        encoding="utf-8",
    )
    history.write_text("# History\n\n## Session log\n", encoding="utf-8")

    assert (
        archive.main(["--keep", "1", "--plan", str(plan), "--history", str(history)])
        == 0
    )
    assert "](saved/handoff-history.md)" in plan.read_text(encoding="utf-8")


# `CAP_DAC_OVERRIDE` — root ignores the permission bits these tests deny with, so
# `chmod 0555` on a directory does not stop the staging write and
# `os.access(target, os.W_OK)` returns true for a `chmod 0444` file. The tests
# would then FAIL rather than pass vacuously, which is the better direction, but
# a red suite in an adopter's root container says nothing about the kit. GitHub
# Actions runs as `runner`, so this skips nothing in this repo's own CI.
_is_root = hasattr(os, "geteuid") and os.geteuid() == 0
_needs_permission_enforcement = pytest.mark.skipif(
    _is_root,
    reason="root bypasses the permission bits this test denies with (CAP_DAC_OVERRIDE)",
)


def _write_four_block_plan(plan: Path, history: Path) -> None:
    """A 4-block, 46-line handoff doc shared by the ``--target-lines`` tests below.

    Bodies are 8 lines each (except the newest, 3) so the candidate line counts
    are far enough apart to write exact-value assertions against. The candidates
    the sweep actually builds — ``moved_count`` 1..3, i.e. 3 / 2 / 1 live blocks —
    measure **46 / 33 / 20** lines, and the floor with no blocks left would be 12.
    (A keep-everything rebuild would be 59, but ``range(1, len(blocks))`` never
    constructs it.)

"""
    plan.write_text(
        "# Handoff\n"
        "\n"
        "Last updated: 2026-07-30 — testing\n"
        "\n"
        "## Latest session — New\n"
        "\n"
        "New body line 1.\n"
        "New body line 2.\n"
        "New body line 3.\n"
        "\n"
        "## Earlier session — Third\n"
        "\n"
        + "".join(f"Third body line {i}.\n" for i in range(1, 9))
        + "\n"
        "## Earlier session — Second\n"
        "\n"
        + "".join(f"Second body line {i}.\n" for i in range(1, 9))
        + "\n"
        "## Earlier session — First\n"
        "\n"
        + "".join(f"First body line {i}.\n" for i in range(1, 9))
        + "\n"
        "## Standing section\n"
        "\n"
        "Standing content.\n",
        encoding="utf-8",
    )
    history.write_text(
        "# History\n\n## Session log\n\n### existing entry\n\nexisting.\n",
        encoding="utf-8",
    )


def test_target_lines_sweeps_more_than_one_block_to_reach_the_target(
    tmp_path: Path,
) -> None:
    """``--target-lines`` sweeps oldest-first, one block at a time, until the doc fits.

    The fixture is 46 lines; sweeping just the oldest block ("First") leaves it
    at 46 lines — the 11 lines the block occupied are offset by the 5-line
    history pointer plus 6 lines of separator normalisation across the kept
    blocks, not by the pointer alone — so a target of 35 is unreachable after one
    block
    and requires sweeping two ("Second" then "First") to land at 33.
    """
    archive = _load_module(
        "archive_target_lines_sweep", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    result = archive.main(
        ["--target-lines", "35", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    updated_plan = plan.read_text(encoding="utf-8")
    updated_lines = updated_plan.splitlines()
    assert len(updated_lines) <= 35
    assert "## Latest session — New" in updated_plan
    assert "## Earlier session — Third" in updated_plan
    assert "## Earlier session — Second" not in updated_plan
    assert "## Earlier session — First" not in updated_plan
    assert "## Standing section\n\nStanding content." in updated_plan
    updated_history = history.read_text(encoding="utf-8")
    assert "### Second" in updated_history
    assert "### First" in updated_history
    assert updated_history.index("### Second") < updated_history.index("### First")
    assert updated_history.index("### First") < updated_history.index(
        "### existing entry"
    )


def test_target_lines_already_met_is_a_clean_noop(tmp_path: Path) -> None:
    """A doc already at or under the target is left untouched (like the ``--keep`` no-op)."""
    archive = _load_module(
        "archive_target_lines_noop", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    result = archive.main(
        ["--target-lines", "46", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    assert plan.read_text(encoding="utf-8") == original_plan
    assert history.read_text(encoding="utf-8") == original_history


def test_target_lines_unreachable_fails_loudly_instead_of_reporting_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #150's doctrine: a step that did not accomplish its ask must fail, not warn-and-0.

    Sweeping down to the floor (1 live block — the last block is never swept)
    still leaves this fixture at 20 lines, so a target of 5 can never be
    reached. That must be exit 3 with a message naming the target and the doc's
    UNCHANGED length — never an "achieved" count, because nothing is written.
    """
    archive = _load_module(
        "archive_target_lines_unreachable", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    result = archive.main(
        ["--target-lines", "5", "--plan", str(plan), "--history", str(history)]
    )

    # Exit 3, not 2: 2 covers six unrelated failures (bad flag value,
    # unresolvable configured paths, missing file, unparseable handoff, history
    # with no session-log section, failed write), and
    # `wrap-up.md` tells the operator to diagnose an exhausted sweep from this
    # exit. Sharing 2 made every one of those misreport as "ran out of blocks".
    assert result == 3
    err = capsys.readouterr().err
    assert "--target-lines 5" in err
    # The message must describe the FILE, not the rejected candidate. It says
    # "would leave 20 lines" (conditional) and "unchanged at 46 lines" (actual);
    # an earlier version said "swept to 1 live block(s) ... and still 20 lines",
    # which is past tense about work that never happened and names a line count
    # the file never had.
    assert "would leave" in err
    assert "unchanged at 46 lines" in err
    assert "swept to" not in err
    # Nothing is written: this path returns before any write is attempted, so
    # there is nothing to roll back — the files are simply untouched.
    assert plan.read_text(encoding="utf-8") == original_plan
    assert history.read_text(encoding="utf-8") == original_history


def test_target_lines_and_keep_are_mutually_exclusive(tmp_path: Path) -> None:
    archive = _load_module(
        "archive_target_lines_conflict", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")

    result = archive.main(
        [
            "--keep",
            "2",
            "--target-lines",
            "35",
            "--plan",
            str(plan),
            "--history",
            str(history),
        ]
    )

    # `== 2`, not `!= 0`: exit 3 means specifically 'target unreachable', and a
    # usage error is not that. Asserting only non-zero re-creates the very
    # conflation the distinct code exists to remove — and `return 2` mutated to
    # `return 3` passed the suite while it did.
    assert result == 2
    assert plan.read_text(encoding="utf-8") == original_plan


def test_keep_alone_is_unchanged_by_the_target_lines_addition(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Regression guard: plain ``--keep`` must behave exactly as it did before.

    Asserts the stdout report as well as the resulting state.
    """
    archive = _load_module(
        "archive_keep_alone_regression", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "moved 2 block(s) to handoff-history.md, keeping 2 live (46 -> 33 plan lines)" in out
    updated_plan = plan.read_text(encoding="utf-8")
    assert len(updated_plan.splitlines()) == 33
    assert "## Earlier session — Second" not in updated_plan
    assert "## Earlier session — First" not in updated_plan
    assert "## Earlier session — Third" in updated_plan
    updated_history = history.read_text(encoding="utf-8")
    assert updated_history.index("### Second") < updated_history.index("### First")


@pytest.mark.kit_repo_only("init.sh")
def test_init_migrates_the_previous_runtime_schema(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    (repo / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "init.sh", repo / "init.sh")
    (repo / "config" / "dev-model.yaml").write_text(
        """project:
  name: old-project
paths:
  handoff: docs/handoff.md
  handoff_history: docs/handoff-history.md
  friction_log: docs/friction-log.md
  friction_log_archive: docs/friction-log-archive.md
doc_budgets: []
vcs:
  protected_branch: trunk
tracker:
  backend: none
  project_name: "Old"
  linear:
    team_id: ""
    project_id: ""
review:
  bots: []
  fallback_command: "/code-review"
notify:
  user_key: ""
models:
  cheap: tiny
  default: normal
  expensive: large
state:
  dirname: state
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["sh", "init.sh"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    config = yaml.safe_load(
        (repo / "config" / "dev-model.yaml").read_text(encoding="utf-8")
    )

    assert config["paths"]["engines"] == "scripts"
    assert config["runtime"]["default"] == "claude"
    assert config["runtime"]["launchers"]["codex"] == "codex"
    assert config["review"]["fallback_commands"]["codex"] == "/review"
    # The panel is what the fallback actually IS now; deleting its whole
    # migration block from init.sh previously passed the entire suite.
    panel = config["review"]["fallback_panel"]
    assert panel["receipt_source"] == "fallback:panel"
    assert [lens["name"] for lens in panel["lenses"]] == ["adversarial", "correctness"]
    # The migrated focus text must match what a fresh install ships, or an
    # upgrading adopter runs a materially weaker lens prompt than a new one.
    shipped = yaml.safe_load(
        (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")
    )["review"]["fallback_panel"]
    assert panel["lenses"] == shipped["lenses"]
    assert config["models"]["runtime_mappings"]["claude"] == {
        "cheap": "tiny",
        "default": "normal",
        "expensive": "large",
    }


def test_python_engine_root_walk_supports_namespacing(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    nested_script = repo / "scripts" / "devkit" / "pr_watch.py"
    nested_script.parent.mkdir(parents=True)
    (repo / ".git").mkdir()
    pr_watch = _load_module("pr_watch", ENGINE_DIR / "pr_watch.py")

    assert pr_watch._find_repo_root(nested_script) == repo


def test_codex_skill_adapters_are_valid_and_share_workflows() -> None:
    # Extended for `adopt` and `upgrade` when #330 moved them to shared workflow
    # definitions. This tuple is the ONLY thing validating `.agents/skills/*`, and
    # it is a hardcoded restatement of "every dual-runtime skill" — so adding a
    # skill without adding it here drops coverage silently, which is exactly what
    # this change did until a review lens caught it. Deriving the set from the
    # filesystem instead is #341, filed rather than built here because a fix round
    # addresses the finding and not the mechanism around it
    # (safety-critical-changes.md rule 3).
    for name in ("session-start", "wrap-up", "pr-watch", "parallel", "adopt", "upgrade"):
        skill_dir = REPO_ROOT / ".agents" / "skills" / name
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert skill_text.startswith("---\n")
        _, frontmatter, body = skill_text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert set(metadata) == {"name", "description"}
        assert metadata["name"] == name
        assert "TODO" not in skill_text
        assert f"docs/agentic-dev-kit/workflows/{name}.md" in body

        interface = yaml.safe_load(
            (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
        )["interface"]
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${name}" in interface["default_prompt"]

        claude_adapter = (REPO_ROOT / ".claude" / "commands" / f"{name}.md").read_text(
            encoding="utf-8"
        )
        assert f"docs/agentic-dev-kit/workflows/{name}.md" in claude_adapter


def test_shared_lane_contract_has_no_runtime_specific_peer_api() -> None:
    script = (ENGINE_DIR / "dev_session.sh").read_text(encoding="utf-8")

    assert "SendMessage" not in script
    assert "&& claude" not in script


# --------------------------------------------------------------------------- #
# config migrations — the highest-blast-radius code in the kit
# --------------------------------------------------------------------------- #
#
# `init.sh` rewrites a file the ADOPTER owns, so a bug here corrupts their
# config rather than merely misbehaving. Three review rounds on one PR produced
# three distinct corruptions from list surgery alone (wrong indent orphaning
# every entry; a whole-file key anchor writing into a same-named list under
# another section; a multi-line item spliced in half), each of which passed the
# migration's own post-conditions and printed success. None was caught by a test
# because there were none. Table-driven over the shapes real configs actually
# take.

_MIGRATION_SHAPES = {
    # (name): (config text, what must still be true afterwards)
    "two_space": """review:
  bots: [bugbot]
  unavailable_markers:
    - "my in-house reviewer is offline"
""",
    "four_space": """review:
    bots: [bugbot]
    unavailable_markers:
        - "my in-house reviewer is offline"
""",
    "flush_indent": """review:
  bots: [bugbot]
  unavailable_markers:
  - "my in-house reviewer is offline"
""",
    "inline_flow": """review:
  bots: [bugbot]
  unavailable_markers: ["my in-house reviewer is offline"]
""",
    "decoy_section_first": """other:
  bots: [nope]
  unavailable_markers:
    - "decoy"
review:
  bots: [bugbot]
  unavailable_markers:
    - "my in-house reviewer is offline"
""",
    "header_trailing_space": """review: 
  bots: [bugbot]
  unavailable_markers:
    - "my in-house reviewer is offline"
""",
    "multiline_item": '''review:
  bots: [bugbot]
  unavailable_markers:
    - "the reviewer could not run because the
       account is out of credits"
''',
    "no_trailing_newline": """review:
  bots: [bugbot]
  unavailable_markers:
    - "my in-house reviewer is offline\"""",
}


def _run_init(tmp_path: Path, name: str, config_text: str):
    repo = tmp_path / name
    (repo / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "init.sh", repo / "init.sh")
    (repo / "config" / "dev-model.yaml").write_text(config_text, encoding="utf-8")
    proc = subprocess.run(
        ["sh", "init.sh"], cwd=repo, check=True, capture_output=True, text=True
    )
    return repo / "config" / "dev-model.yaml", proc


@pytest.mark.parametrize("shape", sorted(_MIGRATION_SHAPES))
@pytest.mark.kit_repo_only("init.sh")
def test_migration_never_corrupts_or_silently_drops_adopter_config(
    tmp_path: Path, shape: str
) -> None:
    """Whatever else it does, the migration must leave a config that still
    PARSES and still says what the adopter said.

    `review.bots: [bugbot]` is the canary: an adopter whose reviewer is not
    CodeRabbit. Every corruption found in review showed up here as either a
    parse failure or that value silently becoming `[coderabbit]`.
    """
    path, _ = _run_init(tmp_path, shape, _MIGRATION_SHAPES[shape])
    text = path.read_text(encoding="utf-8")

    parsed = yaml.safe_load(text)  # raises on the corruptions found in review
    assert parsed["review"]["bots"] == ["bugbot"], "adopter's reviewer was overwritten"
    markers = parsed["review"]["unavailable_markers"]
    assert markers, "adopter's marker list was emptied"
    assert any("in-house" in m or "could not run" in m for m in markers), (
        f"adopter's own marker was dropped: {markers}"
    )
    # kitconfig (what the engines actually use) must agree with PyYAML — the
    # reader exists so engines can drop the dependency, so a disagreement means
    # the migration produced a file the two halves of the kit read differently.
    # ENGINE_DIR, not `REPO_ROOT / "scripts"` (#534): this imports the reader
    # THIS repo actually ships, which under a vendored `paths.engines` is not
    # under `scripts/`.
    sys.path.insert(0, str(ENGINE_DIR / "lib"))
    import kitconfig  # noqa: PLC0415

    if shape == "multiline_item":
        # kitconfig has no multi-line-scalar support, so it reads a wrapped list
        # item as a truncated one. PRE-EXISTING and unrelated to migration: it
        # reads the input the same way. Asserted as a known divergence rather
        # than skipped, so closing it later fails here instead of passing quietly.
        assert kitconfig.loads(text) != parsed
        assert kitconfig.loads(_MIGRATION_SHAPES[shape]) != yaml.safe_load(
            _MIGRATION_SHAPES[shape]
        ), "the divergence is in the reader, not in what the migration wrote"
    else:
        assert kitconfig.loads(text) == parsed

    # A decoy section with the same key names must be left exactly as it was.
    if shape == "decoy_section_first":
        assert parsed["other"]["unavailable_markers"] == ["decoy"]
        assert parsed["other"]["bots"] == ["nope"]


@pytest.mark.parametrize("shape", sorted(_MIGRATION_SHAPES))
@pytest.mark.kit_repo_only("init.sh")
def test_migration_is_idempotent(tmp_path: Path, shape: str) -> None:
    """Re-running `./init.sh` is the documented upgrade path, so a second run
    must be a no-op — not a second copy of every key it added."""
    path, _ = _run_init(tmp_path, shape, _MIGRATION_SHAPES[shape])
    once = path.read_text(encoding="utf-8")

    subprocess.run(
        ["sh", "init.sh"], cwd=path.parent.parent, check=True, capture_output=True, text=True
    )

    assert path.read_text(encoding="utf-8") == once


@pytest.mark.kit_repo_only("init.sh")
def test_migration_adds_every_review_key_exactly_once(tmp_path: Path) -> None:
    """Per-key guards, not one guard over a block of five.

    A single `noise_markers` guard over a block defining five keys meant an
    adopter who had `unavailable_markers` but not `noise_markers` got a SECOND
    definition of it — and both readers resolve last-key-wins, so their list was
    silently replaced by the kit's defaults.
    """
    path, _ = _run_init(
        tmp_path,
        "partial",
        'review:\n  bots: [bugbot]\n  unavailable_markers:\n    - "mine"\n',
    )
    text = path.read_text(encoding="utf-8")

    for key in (
        "bots",
        "noise_markers",
        "unavailable_markers",
        "informational_checks",
        "require_ci",
        "bot_pending_grace_minutes",
    ):
        assert len(re.findall(rf"^\s+{key}:", text, re.MULTILINE)) == 1, key
    assert yaml.safe_load(text)["review"]["unavailable_markers"] == ["mine"]


@pytest.mark.parametrize(
    ("style", "config", "wanted", "unwanted"),
    [
        # Block list — a `- ` item is the right thing to add.
        (
            "block",
            'review:\n  unavailable_markers:\n    - "mine"\n',
            '- "review rate limited"',
            "brackets",
        ),
        # Inline flow list — telling them to add a `- ` item would hang a block
        # item off a flow scalar, i.e. walk them into corrupting their config.
        (
            "flow",
            'review:\n  unavailable_markers: ["mine"]\n',
            "brackets",
            '- "review rate limited"',
        ),
        # Flow list whose brackets do not close on the key line. Valid YAML, but
        # `kitconfig` parses it to {} / "[" — so the adopter's WHOLE list is
        # already inert, and "add it inside the brackets" would be confident,
        # useless advice. Say what's actually wrong instead.
        (
            "flow_next_line",
            'review:\n  unavailable_markers:\n    ["mine", "other"]\n',
            "cannot parse that",
            '- "review rate limited"',
        ),
        (
            "flow_multi_line",
            'review:\n  unavailable_markers: [\n    "mine",\n    "other"\n  ]\n',
            "cannot parse that",
            "add the string inside the brackets",
        ),
        # A marker containing a `#` must not be cut short by comment-stripping —
        # doing so asks for a marker the adopter already has.
        (
            "hash_in_value",
            'review:\n  unavailable_markers:\n    - "see #23 for why"\n',
            '- "review rate limited"',
            "brackets",
        ),
    ],
)
@pytest.mark.kit_repo_only("init.sh")
def test_the_instruction_matches_the_list_style(
    tmp_path: Path, style: str, config: str, wanted: str, unwanted: str
) -> None:
    """The advice must be correct for the shape the adopter actually has.

    Without a per-style assertion the whole branch is dead-codeable: hardwiring
    the style test to a constant still passes a suite that only ever checks the
    block-list direction.
    """
    _, proc = _run_init(tmp_path, f"instructs_{style}", config)

    assert "ACTION NEEDED" in proc.stderr
    assert wanted in proc.stderr
    assert unwanted not in proc.stderr


@pytest.mark.parametrize(
    ("case", "config"),
    [
        # Already present — nothing to ask for.
        ("block", 'review:\n  unavailable_markers:\n    - "mine"\n    - "review rate limited"\n'),
        ("flow", 'review:\n  unavailable_markers: ["mine", "review rate limited"]\n'),
        # Case-insensitively: an adopter may have written it capitalized.
        ("block_mixed_case", 'review:\n  unavailable_markers:\n    - "Review Rate Limited"\n'),
        # …and a marker whose text contains a `#` must still count as present.
        (
            "hash_in_value",
            'review:\n  unavailable_markers:\n    - "tracked in #23: review rate limited"\n',
        ),
        # A key with no value falls back to the engine defaults, which already
        # contain the marker — so asking for it would be noise.
        ("empty_key", "review:\n  unavailable_markers:\n"),
        # Absent entirely: `ensure_review_key` writes the full default list.
        ("absent", "review:\n  bots: [bugbot]\n"),
    ],
)
@pytest.mark.kit_repo_only("init.sh")
def test_the_instruction_stays_quiet_when_there_is_nothing_to_add(
    tmp_path: Path, case: str, config: str
) -> None:
    _, proc = _run_init(tmp_path, f"quiet_{case}", config)

    assert "ACTION NEEDED" not in proc.stderr


@pytest.mark.kit_repo_only("init.sh")
def test_a_marker_named_only_in_a_comment_does_not_count(tmp_path: Path) -> None:
    """The kit's own shipped config carries a trailing comment on that very
    line, so a raw-line grep is satisfied by a config whose LIST lacks it."""
    _, proc = _run_init(
        tmp_path,
        "comment_only",
        'review:\n  unavailable_markers:\n'
        '    - "mine"   # unlike review rate limited, this one is ours\n',
    )

    assert "ACTION NEEDED" in proc.stderr


# Fewer than this many state_paths tests running means the subprocess collected
# the wrong thing, not that the sandbox resolver got simpler. 62 at the time of
# writing; raise it deliberately, never lower it to make a run pass.
_STATE_PATHS_TEST_FLOOR = 62


def test_state_paths_suite_passes_from_inside_a_lane_worktree(tmp_path: Path) -> None:
    """The local gate must not go red for reasons unrelated to the diff.

    `_marker_state_root` discovers a sandbox by walking up from `Path.cwd()`, so
    a `.devkit_state_root` marker at or above the invocation directory redirects
    the resolver — and the state_paths suite's "no sandbox configured"
    assertions fail. Its autouse fixture cleared every env signal but not the
    cwd, so the failure looked environmental and unexplained.

    It cannot be caught by running that suite the ordinary way: CI checks out a
    marker-free tree and a developer runs from the main checkout. It appears
    only when the suite runs from inside a headless lane worktree — exactly what
    a lane agent does before pushing, and it happened to three lanes in one
    session (issue #10). So the regression guard has to be the invocation
    itself, from a directory that carries a marker.
    """
    lane = tmp_path / "worktree"
    lane.mkdir()
    (lane / ".devkit_state_root").write_text(
        str(tmp_path / "sandbox-state"), encoding="utf-8"
    )

    result = subprocess.run(
        # ENGINE_DIR, not REPO_ROOT/"scripts": `paths.engines` is configurable,
        # so a vendored layout (scripts/devkit/) keeps this pointing at the
        # engines that are actually installed.
        [
            sys.executable, "-m", "pytest",
            str(ENGINE_DIR / "lib" / "state_paths" / "tests"),
            "-q",
        ],
        cwd=lane,
        capture_output=True,
        text=True,
        timeout=300,
    )

    # stderr, not just stdout: pytest reports a bad path or a collection error
    # there, while stdout says only "no tests ran". Without it, a drift in this
    # path would turn the gate red with no reason given — which is the exact
    # unexplained-red-gate failure this test exists to prevent.
    detail = f"stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
    assert result.returncode == 0, detail
    # A wrong path exits non-zero (4 = not found, 5 = nothing collected), so this
    # cannot pass vacuously — but assert on the count anyway, so the test fails
    # loudly rather than thinning out if the suite is ever moved.
    #
    # A FLOOR, parsed, not a range pattern: the state_paths suite is expected to
    # grow, so an exact count is churn and a `6\d+` regex silently stops matching
    # at 70 while quietly accepting a drop to 60. The floor only ever needs
    # raising deliberately.
    passed = re.search(r"(\d+) passed", result.stdout)
    assert passed, detail
    assert int(passed.group(1)) >= _STATE_PATHS_TEST_FLOOR, detail


# ── the no-.git fallback in the OTHER two root resolvers (issue #60) ─────────
#
# `test_python_engine_root_walk_supports_namespacing` above plants a `.git`, so
# it only ever exercised the marker walk. The FALLBACK was uncovered in all
# three resolvers, which is how the same depth-arithmetic bug survived in
# `pr_watch._find_repo_root` and `devmodel_config._repo_root` after it was fixed
# in `kitconfig.repo_root` — one fix, three copies, and the docstring in
# pr_watch made the same `scripts/devkit/` claim the issue was filed about.


def test_pr_watch_root_fallback_is_arithmetic_and_stays_inside_the_tree(
    tmp_path: Path,
) -> None:
    """Known limitation (#60), asserted rather than left to be discovered.

    No `.git`: `start.parent.parent`. For `<root>/scripts/pr_watch.py` that is
    the root; vendored under `scripts/devkit/` it is `<root>/scripts` — wrong,
    but inside the tree.
    """
    repo = tmp_path / "project"
    nested = repo / "scripts" / "devkit" / "pr_watch.py"
    nested.parent.mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    pr_watch = _load_module("pr_watch_fb", ENGINE_DIR / "pr_watch.py")

    resolved = pr_watch._find_repo_root(nested)
    assert resolved == repo / "scripts"       # the limitation
    assert repo in resolved.parents           # ...but still inside the tree


def test_pr_watch_root_fallback_does_not_escape_into_a_parent_project(
    tmp_path: Path,
) -> None:
    """Foreign config as the IMMEDIATE parent — the shape the removed probe
    escaped on. No padding directory; the earlier version of this test had one,
    which is why it passed while the real case escaped.

    Matters most here: `REPO_ROOT` is the `cwd=` for every `gh`/`git` subprocess
    and the base for the state root, so escaping points a merge-gate engine at
    a different repository.
    """
    outer = tmp_path / "outer"
    (outer / "config").mkdir(parents=True)
    (outer / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    inner = outer / "inner"
    nested = inner / "scripts" / "pr_watch.py"
    nested.parent.mkdir(parents=True)
    pr_watch = _load_module("pr_watch_esc", ENGINE_DIR / "pr_watch.py")

    resolved = pr_watch._find_repo_root(nested)
    assert resolved != outer, "escaped into the parent project"
    assert resolved == inner


def test_devmodel_config_root_fallback_does_not_escape_into_a_parent_project(
    tmp_path: Path,
) -> None:
    """`devmodel_config` had NO escape test at all — its bound was copied from
    kitconfig and, when mutated to fully unbounded, the whole suite stayed
    green. Covering it here so all three resolvers are pinned in the direction
    that matters.

    `_repo_root()` reads `__file__`, so the module must be copied into place.
    """
    outer = tmp_path / "outer"
    (outer / "config").mkdir(parents=True)
    (outer / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    lib = outer / "inner" / "scripts" / "lib"
    lib.mkdir(parents=True)
    target = lib / "devmodel_config.py"
    target.write_bytes((ENGINE_DIR / "lib" / "devmodel_config.py").read_bytes())

    module = _load_module("devmodel_config_esc", target)
    resolved = module._repo_root()
    assert resolved != outer, "escaped into the parent project"
    assert resolved == outer / "inner"


def test_engines_avoid_datetime_utc_alias() -> None:
    """`datetime.UTC` / `from datetime import UTC` need Python 3.11+.

    `ruff.toml` ignores UP017 so the autofixer cannot introduce this, but the
    ignore is a comment — nothing stops it being typed by hand, and the failure
    is an ImportError at module load on an interpreter CI never exercises.

    AST, not a regex. The first version of this test matched the literal text
    `datetime.UTC` on a single line, and a review found two forms that walk
    straight past it: `import datetime as dt` … `dt.UTC`, and a parenthesised
    `from datetime import (\n    UTC,\n)`. Both are the same ImportError. A
    guard that only catches the spelling you happened to think of is the class
    of test this suite has been bitten by repeatedly.

    Scope is ENGINES, not tests: tests only run under the pinned CI interpreter,
    while engines are invoked as a bare `python3 <engine>` by git hooks, cron
    and CI. The six modules under lib/ carry no PEP 723 header at all, so they
    inherit their caller's interpreter with nothing to negotiate a newer one.
    """
    import ast

    offenders: list[str] = []
    for path in sorted(ENGINE_DIR.rglob("*.py")):
        rel = path.relative_to(ENGINE_DIR)
        if "tests" in rel.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_aliases = {"datetime"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "datetime" and alias.asname:
                        module_aliases.add(alias.asname)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "datetime":
                for alias in node.names:
                    if alias.name == "UTC":
                        offenders.append(f"{rel}:{node.lineno}: from datetime import UTC")
            elif (
                isinstance(node, ast.Attribute)
                and node.attr == "UTC"
                and isinstance(node.value, ast.Name)
                and node.value.id in module_aliases
            ):
                offenders.append(f"{rel}:{node.lineno}: {node.value.id}.UTC")
    assert not offenders, (
        "use `timezone.utc` — `datetime.UTC` raises ImportError below 3.11:\n"
        + "\n".join(offenders)
    )


def _load_dataclass_module(name: str, path: Path) -> ModuleType:
    """Like `_load_module`, but registers the module in `sys.modules` while exec'ing.

    `@dataclass` class creation reads `sys.modules[cls.__module__].__dict__`, so an
    engine holding a dataclass — `check_doc_budget.py`'s `DocStatus` — raises
    `AttributeError` under the unregistered `_load_module`. Registration is popped
    again afterwards: it is only needed during `exec_module`, and leaving it would
    leak a fake module name into every later test in the session.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module

def test_doc_budget_remedy_substitutes_the_budget_placeholder(tmp_path: Path) -> None:
    """`{budget}` in a remedy is filled from that entry's own `budget:`.

    The remedy has to name a concrete `--target-lines` value, and that value is
    the budget. Substitution is what lets the config state the number once.
    """
    repo = tmp_path / "project"
    config_path = repo / "config" / "dev-model.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """doc_budgets:
  - path: plan.md
    budget: 3
    archive: history.md
    remedy: "sweep it (archive_plan_sessions.py --target-lines {budget})"
""",
        encoding="utf-8",
    )
    (repo / "plan.md").write_text("a\nb\nc\nd\ne\n", encoding="utf-8")

    budget = _load_dataclass_module(
        "check_doc_budget_subst", ENGINE_DIR / "check_doc_budget.py"
    )
    statuses = budget.evaluate(repo, config_path)
    report = budget.render(statuses, quiet=True)

    assert "--target-lines 3" in report, report
    assert "{budget}" not in report, "placeholder leaked into the operator-facing warning"


def test_shipped_doc_budget_remedies_never_restate_the_budget_as_a_literal() -> None:
    """A remedy naming `--target-lines` must use `{budget}`, never a digit.

    This is the test that fails if someone writes `--target-lines 400` beside
    `budget: 400`: the two would then drift silently the moment the budget moves,
    and the warning would prescribe a sweep to the stale target.
    """
    budget = _load_dataclass_module(
        "check_doc_budget_literal", ENGINE_DIR / "check_doc_budget.py"
    )
    repo = _find_repo_root(Path(__file__).resolve())
    statuses = budget.evaluate(repo, repo / "config" / "dev-model.yaml")

    # `[=\s]`, not `\s`: `--target-lines=400` is a fully valid invocation and
    # reaches exactly the staleness this guard exists to prevent.
    offenders = [
        f"{s.path}: {s.remedy}"
        for s in statuses
        if re.search(r"--target-lines[=\s]+\d", s.remedy)
    ]
    assert not offenders, (
        "write `--target-lines {budget}`, not a literal — it goes stale when the "
        "budget moves:\n" + "\n".join(offenders)
    )
    # The positive half: naming the flag at all obliges the placeholder. Without
    # this, `--target-lines <handoff-budget>` passes the regex above while being
    # exactly as unusable as a stale literal.
    missing = [
        f"{s.path}: {s.remedy}"
        for s in statuses
        if "--target-lines" in s.remedy and "{budget}" not in s.remedy
    ]
    assert not missing, "a remedy naming --target-lines must use {budget}:\n" + "\n".join(missing)
    # And no configured remedy may render with a brace still in it — an
    # unsubstituted placeholder is at best confusing and, in the --target-lines
    # remedy specifically, a command that dies with `invalid int value`.
    unresolved = [f"{s.path}: {s.remedy_text}" for s in statuses if "{" in s.remedy_text]
    assert not unresolved, (
        "placeholder left unsubstituted in the rendered remedy:\n" + "\n".join(unresolved)
    )


def _write_n_block_plan(plan: Path, history: Path, n: int) -> None:
    """A handoff doc with exactly ``n`` session blocks (``n`` may be 0)."""
    body = "# Handoff\n\nLast updated: 2026-07-30 — testing\n\n"
    for i in range(n):
        heading = "## Latest session" if i == 0 else "## Earlier session"
        name = f"Block{i}"
        body += f"{heading} — {name}\n\n"
        body += "".join(f"{name} line {j}.\n" for j in range(1, 9)) + "\n"
    if n == 0:
        body += "## Recent sessions\n\n"
    body += "## Standing section\n\nStanding content.\n"
    plan.write_text(body, encoding="utf-8")
    history.write_text(
        "# History\n\n## Session log\n\n### existing entry\n\nexisting.\n",
        encoding="utf-8",
    )


def test_line_counters_agree_on_exotic_separators(tmp_path: Path) -> None:
    """`archive_plan_sessions` and `check_doc_budget` must measure the same "line".

    `check_doc_budget` counts by iterating a text handle.
    `archive_plan_sessions` parses structure with `str.splitlines()`, which
    ALSO breaks on \\v \\f \\x1c \\x1d \\x1e \\x85 \\u2028 \\u2029. `--target-lines`
    is the first path to compare a count against the budget, which makes the
    disagreement reachable — a doc over budget by one counter and under by the
    other, with the sweep refusing a target that is genuinely achievable.

    Fails if `budget_line_count` is swapped back to `len(text.splitlines())`.
    """
    archive = _load_module(
        "archive_counter_parity", ENGINE_DIR / "archive_plan_sessions.py"
    )
    budget = _load_dataclass_module(
        "budget_counter_parity", ENGINE_DIR / "check_doc_budget.py"
    )
    doc = tmp_path / "doc.md"
    text = (
        "plain line\n"
        "form feed here:\f and continuing\n"
        "vertical tab:\v and continuing\n"
        "line sep:  and continuing\n"
        "para sep:  and continuing\n"
        "next line:\x85 and continuing\n"
        "file sep:\x1c group:\x1d record:\x1e done\n"
        "final line with no newline"
    )
    doc.write_text(text, encoding="utf-8", newline="")

    assert archive.budget_line_count(doc.read_text(encoding="utf-8")) == budget._line_count(doc)
    # And the naive form really does disagree — otherwise this test is vacuous.
    assert len(text.splitlines()) != budget._line_count(doc)

    # The OTHER divergence class, which this test could not previously reach.
    # `_line_count` reads a text handle, so universal newlines turns \r and \r\n
    # into \n before it counts; `budget_line_count` splits on \n alone and is
    # therefore correct only for ALREADY-TRANSLATED text. Reading with
    # `newline=""` anywhere upstream silently breaks parity by one line per CR.
    # Asserted in both directions so that change fails here rather than in the field.
    for raw in ("a\rb\rc\n", "a\rb\r", "a\rb\nc\rd\n", "a\r\nb\r\nc\n", "a\nb\n"):
        crdoc = doc.parent / "cr.md"
        crdoc.write_text(raw, encoding="utf-8", newline="")
        translated = crdoc.read_text(encoding="utf-8")
        assert archive.budget_line_count(translated) == budget._line_count(crdoc), raw

    # Only a LONE \r diverges when left untranslated — \r\n already carries the
    # \n this counter splits on, which is why the precondition bites exactly on
    # classic-Mac endings and is invisible in a CRLF document.
    for lone_cr in ("a\rb\rc\n", "a\rb\r", "a\rb\nc\rd\n"):
        crdoc = doc.parent / "cr.md"
        crdoc.write_text(lone_cr, encoding="utf-8", newline="")
        assert archive.budget_line_count(lone_cr) != budget._line_count(crdoc), (
            "untranslated lone-CR text must NOT be passed to budget_line_count; "
            "if this stops holding, the precondition has changed"
        )


def test_no_flags_keeps_the_documented_default_of_six_blocks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The `--keep` fallback introduced by `--target-lines` had zero coverage.

    Moving argparse's `default=DEFAULT_KEEP` to `default=None` (needed for the
    mutual-exclusion check) put the default behind `args.keep if ... else
    DEFAULT_KEEP`. Mutating that fallback to `1` swept 7 of 8 blocks and passed
    the whole suite: the only other no-flag invocation uses a 1-block fixture,
    where keep=1 and keep=6 are indistinguishable. Three places document "6".
    """
    archive = _load_module("archive_default_keep", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_n_block_plan(plan, history, 8)

    result = archive.main(["--plan", str(plan), "--history", str(history)])

    assert result == 0
    assert "keeping 6 live" in capsys.readouterr().out
    assert plan.read_text(encoding="utf-8").count("## Latest session") == 1
    live = plan.read_text(encoding="utf-8")
    assert live.count("## Earlier session") == 5, "expected 6 live blocks total"


def test_target_lines_stops_at_the_first_candidate_that_reaches_the_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`<=`, not `<` — "at or under the target" mirrors `over = lines > budget`.

    The candidates the loop builds are 46 / 33 / 20 lines, for 3 / 2 / 1 live
    blocks (59 is the keep-everything rebuild, which `range(1, len(blocks))` never
    constructs, and 12 is the 0-block floor). A target of exactly 33
    must stop at 2 live blocks. Mutating the break condition to `<` sweeps one
    block further (33 -> 20), silently discarding a live session block, and
    survived the whole suite: the pre-loop no-op guard's `<=` was pinned, this
    one was not. In production it fires whenever a sweep lands exactly on 400.
    """
    archive = _load_module("archive_exact_target", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    result = archive.main(
        ["--target-lines", "33", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    assert "moved 2 block(s)" in capsys.readouterr().out
    updated = plan.read_text(encoding="utf-8")
    assert archive.budget_line_count(updated) == 33
    assert "## Earlier session — Third" in updated, "over-swept an extra live block"


def test_target_lines_on_a_one_block_doc_fails_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The `len(blocks) <= 1` short-circuit was pinned by nothing.

    Mutating it to `<= 0` survived the suite, and it is the only thing standing
    between a 1-block doc and `range(1, 1)` leaving `new_plan = None`, then
    `TypeError: can only join an iterable`. No test exercised a 1-block doc
    under `--target-lines` at all.
    """
    archive = _load_module("archive_one_block", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_n_block_plan(plan, history, 1)
    original = plan.read_text(encoding="utf-8")

    result = archive.main(
        ["--target-lines", "3", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 3
    err = capsys.readouterr().err
    assert "1 remaining session block is never swept" in err
    assert "unchanged at" in err
    assert plan.read_text(encoding="utf-8") == original


def test_target_lines_on_a_zero_block_doc_does_not_claim_a_last_block(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no session blocks there is no "last live block" to decline to sweep.

    The single `<= 1` branch serves both 0 and 1 blocks, and its message asserted
    a block that does not exist — describing a document the operator does not
    have. `--keep` on the same doc reports `0 session block(s)` and exits 0.
    """
    archive = _load_module("archive_zero_block", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_n_block_plan(plan, history, 0)

    result = archive.main(
        ["--target-lines", "3", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 3
    err = capsys.readouterr().err
    assert "no session blocks to sweep" in err
    assert "last live block" not in err
    assert "1 remaining session block" not in err


def test_target_lines_never_sweeps_the_last_remaining_block(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The floor invariant, which was asserted in four prose sites and no test.

    Mutating the loop bound `range(1, len(blocks))` -> `range(1, len(blocks) + 1)`
    let the sweep empty the handoff of every session block and report SUCCESS
    (`rc=0`, `keeping 0 live`). It survived the whole suite.

    The target has to sit between the 0-block candidate and the 1-block candidate
    to force the extra iteration. For this fixture the candidates are 46 / 33 / 20
    for 3 / 2 / 1 live blocks, and 12 with none — so 15 is reachable ONLY by
    sweeping the last block, and must be refused. An earlier test used
    `--target-lines 5`, which is below 12 and therefore exits 3 either way.
    """
    archive = _load_module("archive_floor", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")

    result = archive.main(
        ["--target-lines", "15", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 3, "a target reachable only by emptying the doc must be refused"
    out = capsys.readouterr()
    assert "keeping 0 live" not in out.out
    # The doc is untouched, and in particular still has a session block.
    assert plan.read_text(encoding="utf-8") == original
    assert "## Latest session — New" in plan.read_text(encoding="utf-8")


def test_report_figures_use_the_budget_counter_not_splitlines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The reported `(N -> M plan lines)` must be in the budget's units.

    Every other fixture is separator-free, where `len(splitlines())` and
    `budget_line_count` agree — so reverting the report to `len()` survived the
    suite. This fixture puts a form feed and a vertical tab in a body line, which
    `splitlines()` counts as extra lines and the budget does not. The operator
    reads these numbers against `check_doc_budget`'s budget, so an overstatement
    here is a number that does not exist anywhere else.
    """
    archive = _load_module("archive_report_units", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    body = "# Handoff\n\nLast updated: 2026-07-30 — testing\n\n"
    for i in range(3):
        heading = "## Latest session" if i == 0 else "## Earlier session"
        body += f"{heading} — Block{i}\n\n"
        # \f and \v are line breaks to splitlines() and not to the budget counter.
        body += f"Block{i} line with \f form feed and \v vertical tab.\n"
        body += "".join(f"Block{i} line {j}.\n" for j in range(1, 8)) + "\n"
    body += "## Standing section\n\nStanding content.\n"
    plan.write_text(body, encoding="utf-8")
    history.write_text(
        "# History\n\n## Session log\n\n### existing entry\n\nexisting.\n",
        encoding="utf-8",
    )
    real_lines = archive.budget_line_count(body)
    assert real_lines != len(body.splitlines()), "fixture must distinguish the counters"

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert f"({real_lines} -> " in out, out
    written = plan.read_text(encoding="utf-8")
    assert f"-> {archive.budget_line_count(written)} plan lines" in out, out


@_needs_permission_enforcement
def test_a_failed_write_prints_no_past_tense_success_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """stdout must not claim the move happened when the write failed.

    The report used to be printed BEFORE the write, so a read-only handoff
    emitted `moved 2 block(s) ... (46 -> 33 plan lines)` and then an error — and
    `wrap-up.md` tells the operator to report the line count it sees. That is a
    figure for a file that was never touched.

    Uses a genuine OS-level write failure rather than a monkeypatch: the handoff
    lives in a directory the process cannot create a file in, so the staging
    write fails inside the real code path.
    """
    archive = _load_module("archive_failed_write", ENGINE_DIR / "archive_plan_sessions.py")
    plan_dir = tmp_path / "live"
    plan_dir.mkdir()
    plan = plan_dir / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")
    plan_dir.chmod(0o555)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        plan_dir.chmod(0o755)

    assert result == 2
    captured = capsys.readouterr()
    assert "moved" not in captured.out, captured.out
    assert "plan lines" not in captured.out, captured.out
    assert "write failed" in captured.err
    assert plan.read_text(encoding="utf-8") == original


def test_a_brace_in_a_session_title_does_not_crash_the_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Session titles are DATA in the report, never a format string.

    The report was briefly rendered with `"\\n".join(report).format(verb=...)`,
    and the joined string contains the swept titles — so a heading carrying a
    brace raised `KeyError` (or `ValueError` for a lone brace) *after* both files
    had been written, exiting 1 with the move already on disk and no report line.
    Exit 1 is not in the documented set, so the workflow's "read the exit code"
    rule had no branch for it.

    Braces in headings are ordinary here: this very repo's recent sessions are
    about a `{budget}` placeholder.
    """
    archive = _load_module("archive_brace_title", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    text = plan.read_text(encoding="utf-8").replace(
        "## Earlier session — First",
        "## Earlier session — First (substituting {budget}, and a lone { brace)",
    )
    plan.write_text(text, encoding="utf-8")

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "{budget}" in out, "the title must be reported verbatim, not interpolated"
    assert "First (substituting" in out
    assert "{budget}" in history.read_text(encoding="utf-8")


@_needs_permission_enforcement
def test_a_failed_history_stage_never_touches_the_handoff(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failing HISTORY write must not cost the swept blocks (issue #164).

    Renamed from `..._rolls_the_handoff_back`: no rollback is entered here, as
    the paragraph below explains, and the name claimed coverage that lives in
    `test_a_failed_history_publish_restores_the_handoff_from_its_staged_copy`.


    The failed-write test above kills the *plan* write, so the second document is
    never reached and its `plan == original` assertion passes trivially. Killing
    the *history* write is what exercises the move's real hazard: handoff already
    swept, history not written, blocks recoverable from neither.

    Since #164 the handoff is not merely rolled back — it is never modified at
    all, because both documents are staged before either is published and this
    failure happens during staging. Asserted on the INODE as well as the bytes:
    an implementation that wrote the handoff and restored it byte-for-byte would
    pass a content-only check, and it is precisely the one that loses the file if
    the restore fails too.
    """
    archive = _load_module("archive_rollback", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history_dir = tmp_path / "archive"
    history_dir.mkdir()
    history = history_dir / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")
    plan_inode = plan.stat().st_ino
    history_dir.chmod(0o555)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        history_dir.chmod(0o755)

    assert result == 2
    captured = capsys.readouterr()
    assert "write failed" in captured.err
    assert "no changes applied" in captured.err
    assert "moved" not in captured.out
    # The whole point: the blocks that were about to move still exist somewhere.
    assert plan.read_text(encoding="utf-8") == original_plan
    assert "## Earlier session — First" in plan.read_text(encoding="utf-8")
    assert history.read_text(encoding="utf-8") == original_history
    assert plan.stat().st_ino == plan_inode, "the handoff was replaced and put back"


def test_keep_floor_refuses_to_empty_the_handoff(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--keep`'s floor is the same data-loss guard as `--target-lines`'.

    `--target-lines`' floor got pinned when a review found it unpinned; the
    symmetric guard on the older `--keep` path was left uncovered in the same
    commit that touched its line. Mutating `keep < 1` to `keep < 0` survived the
    suite, and `--keep 0` then swept every block: `rc=0`, `keeping 0 live`, a
    handoff with no session blocks at all.
    """
    archive = _load_module("archive_keep_floor", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")

    result = archive.main(
        ["--keep", "0", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2
    captured = capsys.readouterr()
    assert "--keep must be >= 1" in captured.err
    assert "keeping 0 live" not in captured.out
    assert plan.read_text(encoding="utf-8") == original
    assert "## Latest session — New" in plan.read_text(encoding="utf-8")


def test_target_lines_rejects_a_value_below_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--target-lines 0` is a usage error (exit 2), not an unreachable target (3).

    Mutating `target_lines < 1` to `< 0` survived: the flag's only input
    validation had no test, and losing it silently reroutes a bad value into the
    exit-3 refusal, which claims the document is too short to sweep rather than
    that the argument is nonsense.
    """
    archive = _load_module("archive_tl_floor", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    result = archive.main(
        ["--target-lines", "0", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2, "a nonsense argument is a usage error, not an unreachable target"
    assert "--target-lines must be >= 1" in capsys.readouterr().err


def test_dry_run_writes_nothing_and_says_would_move(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run` is "report only" — and nothing pinned that.

    Deleting the whole `if args.dry_run: print(report); return 0` branch passed
    all 552 tests: a dry run then wrote both files while printing "would move".
    The suite's only other `--dry-run` invocation uses a 1-block doc under the
    default `--keep 6`, so it returns at the `nothing to move` early exit and
    never reaches the report or the dry-run branch at all.
    """
    archive = _load_module("archive_dry_run", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    result = archive.main(
        ["--dry-run", "--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "would move 2 block(s)" in out, out
    assert "would move 2 block(s)" in out
    assert not re.search(r"(?<!would )moved 2 block\(s\)", out), (
        "a dry run must not report in the past tense"
    )
    assert plan.read_text(encoding="utf-8") == original_plan, "--dry-run wrote the plan"
    assert history.read_text(encoding="utf-8") == original_history, (
        "--dry-run wrote the history doc"
    )


def test_the_plan_is_written_before_the_history_doc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The write ORDER, not merely the end state.

    `test_a_failed_history_stage_never_touches_the_handoff` asserts the plan ends up
    unchanged — which passes trivially against a variant that writes history
    first and has no rollback at all, because then the plan is never written. That
    is the same "passes trivially" weakness it was written to replace, one axis
    over. Under that variant a failing plan write leaves the blocks in BOTH files
    and a re-run appends them to history twice.

    So record the order directly. Since #164 the ordering that matters is the
    order the documents are PUBLISHED in — each is renamed over its target, and
    the rename is the only moment a reader can observe a change — so the spy sits
    on `os.replace` rather than on the write.
    """
    archive = _load_module("archive_write_order", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    order: list[str] = []
    real_replace = os.replace

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if Path(str(dst)) == plan:
            order.append("plan")
        elif Path(str(dst)) == history:
            order.append("history")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    assert order == ["plan", "history"], (
        f"the plan must be published first so a history failure can roll it back; got {order}"
    )


def test_a_non_utf8_doc_is_a_documented_exit_2_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A stray non-UTF-8 byte used to raise straight out of `main()` and exit 1.

    Exit 1 is not in this module's exit-code contract, and `wrap-up.md` now tells
    the operator to branch on the exit code with cases only for 2 and 3 — so the
    crash put the caller outside its own decision table. Reachable from a cp1252
    round-trip of an em-dash, and these headings are full of ` — `.
    """
    archive = _load_module("archive_bad_utf8", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    raw = plan.read_bytes().replace(b"## Earlier session", b"## Earlier \xff session", 1)
    plan.write_bytes(raw)

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2, "must be the documented usage/IO failure code, not a traceback"
    assert "could not read" in capsys.readouterr().err


@_needs_permission_enforcement
def test_an_unreadable_doc_is_a_documented_exit_2_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`PermissionError` reaches the same two lines as `UnicodeDecodeError`.

    `path.is_file()` passes for a file that exists and cannot be opened, so a
    guard catching only the decode error left exit 1 producible — while the
    module's exit-code contract says 0/2/3 and `wrap-up.md` branches on 2 and 3
    alone. `check_memory_budget.py` already catches `(OSError, UnicodeDecodeError)`
    for exactly this reason.
    """
    archive = _load_module("archive_unreadable", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    plan.chmod(0o000)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        plan.chmod(0o644)

    assert result == 2, "an unreadable file must not traceback out of main()"
    assert "could not read" in capsys.readouterr().err


def test_the_keep_early_exit_message_is_asserted_somewhere(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`nothing to move: N session block(s) <= --keep M` was pinned by nothing.

    Two docstrings claimed another test covered it; neither did — every `--keep`
    test takes the successful-sweep path. Replacing the whole message with a
    literal survived the suite.
    """
    archive = _load_module("archive_keep_noop", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")

    result = archive.main(
        ["--keep", "6", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    assert "nothing to move: 4 session block(s) <= --keep 6." in capsys.readouterr().out
    assert plan.read_text(encoding="utf-8") == original


def test_a_failed_rollback_does_not_claim_no_changes_applied(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the rollback itself fails, say which document is in which state.

    The handler added for this was pinned by nothing: reverting it to the bare
    `write_text(original_plan); raise` survived the suite. "no changes applied"
    would then be printed while the blocks sit in neither file.

    Since #164 this is one of two branches that can still leave the sweep
    half-done — its handoff-side twin is covered separately —
    and it is far narrower than it was: everything that can fail for want of
    space now fails during staging, before anything is published. Reaching it
    takes two failing `os.replace` calls — the publish of the history, and the
    publish of the rollback that was staged for exactly this.
    """
    archive = _load_module("archive_bad_rollback", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_history = history.read_text(encoding="utf-8")

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if target == history:
            raise OSError(28, "No space left on device")
        if target == plan and seen.count(plan) == 2:  # the staged rollback
            raise OSError(28, "No space left on device")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2
    err = capsys.readouterr().err
    assert "no changes applied" not in err, "the handoff WAS swept — don't claim otherwise"
    # BOTH documents named, each with the state this branch can actually vouch
    # for: an operator told only about the handoff restores one and commits the
    # other.
    assert str(history) in err, err
    assert str(plan) in err, err
    assert "git show HEAD:" in err, "the recovery must not be a destructive checkout"
    assert "do NOT `git checkout`" in err, err
    # The history is published by rename or not at all, so "part-written" is a
    # state it can no longer be in and the message must not invent it.
    assert "part-written" not in err, err
    assert history.read_text(encoding="utf-8") == original_history
    # And the swept blocks are named, so the operator knows what to look for.
    assert "First" in err, err


def test_a_failed_history_publish_restores_the_handoff_from_its_staged_copy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rollback path's happy case: history publish fails, handoff comes back.

    Distinct from the staging-failure test above, which never publishes anything.
    Here the handoff HAS been replaced, and the recovery is the third staged
    write — the one written up front precisely so this step needs no allocation
    on a disk that has just refused one (#164). That the copy is staged up front
    rather than built here is pinned separately, by
    `test_the_rollback_is_staged_before_anything_is_published`; this test would
    pass against either, which is what let the late-staging shape survive.

    The message deliberately does NOT say "both documents are intact": a review
    lens measured a CRLF handoff coming back 49 bytes shorter than it went in,
    because the restored bytes are the normalised text this run read. The
    document is whole and holds every block; it is not byte-identical, and the
    wording now says which.
    """
    archive = _load_module("archive_rollback_ok", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    real_replace = os.replace

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if Path(str(dst)) == history:
            raise OSError(28, "No space left on device")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2
    err = capsys.readouterr().err
    assert "was restored and no changes were applied" in err, err
    assert "no partial write" in err or "Neither document holds a partial write" in err, err
    assert plan.read_text(encoding="utf-8") == original_plan
    assert history.read_text(encoding="utf-8") == original_history
    assert not list(tmp_path.glob("*.devkit-tmp")), "staged temps must be cleaned up"


def test_a_successful_sweep_leaves_no_staged_temp_behind(tmp_path: Path) -> None:
    """Debris lands beside the handoff, which is where wrap-up stages files.

    A temp left in `docs/` is a file the very next `git add` picks up. The
    `*.devkit-tmp` .gitignore rule exists for the SIGKILL case that no handler
    can cover; it is not a licence to leak one on the ordinary path.
    """
    archive = _load_module("archive_no_debris", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "handoff-history.md",
        "handoff.md",
    ]


def test_a_symlinked_handoff_is_written_through_not_replaced(tmp_path: Path) -> None:
    """`os.replace` replaces the LINK; the real document would keep every block.

    Finding 1 of the four HIGHs that reverted the first attempt at #164, and the
    worst shape available: exit 0, a success report, the swept blocks appended to
    history — and a handoff whose real file still holds them, so a re-run appends
    them again. The fix is to resolve the target before staging.
    """
    archive = _load_module("archive_symlink", ENGINE_DIR / "archive_plan_sessions.py")
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    real_plan = real_dir / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(real_plan, history)
    link = tmp_path / "handoff.md"
    link.symlink_to(real_plan)

    assert archive.main(["--keep", "2", "--plan", str(link), "--history", str(history)]) == 0

    assert link.is_symlink(), "the symlink itself was replaced by a regular file"
    assert "## Earlier session — First" not in real_plan.read_text(encoding="utf-8"), (
        "the real document kept the swept block"
    )
    assert "First" in history.read_text(encoding="utf-8")


@_needs_permission_enforcement
def test_a_read_only_handoff_is_refused_rather_than_replaced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`os.replace` needs the DIRECTORY writable, not the file.

    So a `chmod 0444` document is replaceable by rename — and the replacement
    carries the temp's mode, which deletes the read-only bit permanently after
    one run. Finding 2 of the four that reverted the first attempt. Refusing
    preserves exactly what `write_text` did: nothing written, exit 2.
    """
    archive = _load_module("archive_readonly", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")
    plan.chmod(0o444)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
        mode_after = stat.S_IMODE(plan.stat().st_mode)
    finally:
        plan.chmod(0o644)

    assert result == 2
    err = capsys.readouterr().err
    assert "refusing to write" in err, err
    assert "not writable" in err, err
    assert "no changes applied" in err, err
    assert plan.read_text(encoding="utf-8") == original
    assert mode_after == 0o444, "the read-only bit was deleted"


def test_a_hardlinked_handoff_is_refused_rather_than_orphaning_the_alias(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """After a rename the other name keeps the OLD content — silently.

    Finding 2's third limb. There is no way to publish atomically and keep the
    alias, so the operator is told rather than having one of the two chosen for
    them.
    """
    archive = _load_module("archive_hardlink", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")
    alias = tmp_path / "alias.md"
    os.link(plan, alias)

    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 2
    err = capsys.readouterr().err
    assert "refusing to write" in err, err
    assert "hard link" in err, err
    assert plan.read_text(encoding="utf-8") == original
    assert alias.read_text(encoding="utf-8") == original


def test_a_sweep_preserves_the_handoffs_permissions(tmp_path: Path) -> None:
    """Mode is carried onto the staged temp, so a 0600 doc is not widened.

    Finding 2 of the four: `mkstemp` creates 0600 and the replaced file inherits
    the TEMP's metadata, so without an explicit carry every sweep rewrites the
    document's permissions — in either direction, silently.
    """
    archive = _load_module("archive_mode", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    plan.chmod(0o640)
    history.chmod(0o640)

    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0

    assert stat.S_IMODE(plan.stat().st_mode) == 0o640
    assert stat.S_IMODE(history.stat().st_mode) == 0o640


def _atomic_write() -> ModuleType:
    return _load_module("atomic_write_lib", ENGINE_DIR / "lib" / "atomic_write.py")


def test_commit_cannot_raise_once_the_replace_has_succeeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The durability step must never turn a published write into a reported failure.

    Found by the correctness lens. `commit()` guarded `os.open` and suppressed
    `os.fsync`, but left `os.close(dir_fd)` in a bare `finally` — and `close(2)`
    returns EIO on NFS. Injecting it there reproduced #164's exact shape from one
    call later: the handoff swept, the history untouched, the staged rollback
    discarded by the caller's cleanup, and `no changes applied` on stderr.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    real_close = os.close

    def exploding_close(fd: int) -> None:
        real_close(fd)
        raise OSError(5, "Input/output error")

    staged = aw.stage_text(target, "published\n")
    monkeypatch.setattr(os, "close", exploding_close)
    staged.commit()  # must not raise
    monkeypatch.undo()

    assert target.read_text(encoding="utf-8") == "published\n"


def test_ownership_that_cannot_be_carried_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The module states this as a guarantee; deleting it cost no test.

    Mutation: replace the `raise AtomicWriteRefused` in the `os.fchown` handler
    with `pass`. Survived the full suite, while the docstring promises ownership
    "is refused, rather than silently reassigning the document to whoever ran the
    tool". Reached here by making `fchown` fail rather than by needing a
    differently-owned file, which no unprivileged test can create.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    real_stat = os.stat_result
    monkeypatch.setattr(
        os, "fchown", lambda *a: (_ for _ in ()).throw(PermissionError(1, "nope"))
    )
    # Make the carried ownership differ from ours so the fchown branch is taken.
    real_lstat = Path.lstat

    def foreign_owner(self: Path) -> object:
        st = real_lstat(self)
        fields = list(st)
        fields[4] = st.st_uid + 1  # st_uid
        return real_stat(fields)

    monkeypatch.setattr(Path, "lstat", foreign_owner)

    with pytest.raises(aw.AtomicWriteRefused, match="ownership"):
        aw.stage_text(target, "replacement\n")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert not list(tmp_path.glob("*.devkit-tmp")), "the refusal leaked a temp"


def test_a_failed_open_leaves_no_temp_and_reports_its_real_cause(
    tmp_path: Path,
) -> None:
    """`open(fd, ...)` closes the descriptor even when it FAILS.

    Found by the adversarial lens. `fd = -1` was set inside the `with` body, so
    a bad `newline`/`encoding` — which the module docstring explicitly invites a
    caller to pass — raised before the reassignment, and the cleanup handler then
    double-closed. That EBADF replaced the real `ValueError` and aborted the
    handler before `temp.unlink()`, leaking the temp the module promises to
    remove. Closing a stale descriptor number is also how an unrelated file gets
    closed.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    with pytest.raises(ValueError, match="newline"):
        aw.stage_text(target, "replacement\n", newline="not-a-valid-newline")

    assert not list(tmp_path.glob("*.devkit-tmp")), "the failed stage leaked a temp"
    assert target.read_text(encoding="utf-8") == "original\n"


def test_a_failed_open_does_not_close_a_descriptor_it_no_longer_owns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half of the double-close fix that the symptoms do not reveal.

    Suppressing the cleanup's `os.close` error already stops EBADF masking the
    real exception and aborting the unlink — so the sibling test above passes
    even if the descriptor is closed twice. What it cannot see is the actual
    hazard: by then the number may have been reused, and the second close lands
    on an unrelated file. Nothing recovers from that and no assertion about
    `stage_text`'s own outputs can detect it.

    So observe the call itself. Retiring `fd` unconditionally means the handler
    makes no `os.close` at all on this path.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    closed: list[int] = []
    real_close = os.close

    def recording_close(fd: int) -> None:
        closed.append(fd)
        real_close(fd)

    monkeypatch.setattr(os, "close", recording_close)
    with pytest.raises(ValueError, match="newline"):
        aw.stage_text(target, "replacement\n", newline="not-a-valid-newline")
    monkeypatch.undo()

    assert closed == [], (
        "`open` already closed the descriptor when it failed; closing it again "
        f"can close an unrelated file. Saw os.close{closed}"
    )


def test_abort_never_raises_out_of_the_callers_finally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`abort()` runs in a `finally`; raising there costs the caller its exit code.

    Narrowing its `suppress(OSError)` back to `FileNotFoundError` survived the
    suite, while a six-line comment justified the width. The engine's documented
    contract admits 0/2/3, and an escape here produces 1.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")
    staged = aw.stage_text(target, "replacement\n")

    monkeypatch.setattr(
        Path, "unlink", lambda *a, **k: (_ for _ in ()).throw(PermissionError(1, "nope"))
    )
    staged.abort()  # must not raise
    monkeypatch.undo()

    assert target.read_text(encoding="utf-8") == "original\n"


def test_an_interrupt_while_publishing_the_handoff_restores_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The SECOND call site — the one the first interrupt fix missed.

    Found by the adversarial lens on round 2. `staged_plan.commit()` was wrapped
    in `except OSError` while `staged_history.commit()` had already been widened
    to `BaseException`, so an interrupt landing during the handoff's publish
    escaped, the `finally` unlinked the staged rollback, and the swept blocks
    were lost — with no message at all, unlike the history path. A fix applied to
    one of two sites is this repo's signature defect.

    The interrupt is injected so that the rename **succeeds and then** the
    exception arrives — the state the handler must get right. `_fsync_parent` no
    longer lets one out (that was the same finding's other half), so the reachable
    window is between `os.replace` returning and any Python bookkeeping, which is
    exactly what makes `published` a filesystem question rather than a flag.
    """
    archive = _load_module("archive_sigint_plan", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    real_replace = os.replace

    def publish_then_interrupt(src: object, dst: object, **kwargs: object) -> None:
        real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
        if Path(str(dst)) == plan:
            raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", publish_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    assert plan.read_text(encoding="utf-8") == original_plan, (
        "the handoff was published and its rollback discarded"
    )
    assert history.read_text(encoding="utf-8") == original_history
    assert not list(tmp_path.glob("*.devkit-tmp"))


def test_a_failed_rollback_on_the_handoff_publish_is_reported_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The handoff-side rollback was unguarded while the history side was guarded.

    Found by the review bot, and it is the one-of-two-call-sites defect again —
    committed inside the fix for that very pattern. An `OSError` from this
    rollback replaced the original exception, escaped through the `finally`, and
    ended the run as a traceback: exit 1, outside the documented 0/2/3/130
    contract, with the handoff swept and no operator message at all.
    """
    archive = _load_module("archive_plan_rb_fail", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if target == plan and seen.count(plan) == 2:  # the rollback
            raise OSError(28, "No space left on device")
        real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
        if target == plan and seen.count(plan) == 1:
            raise OSError(5, "Input/output error")  # fails AFTER publishing

    monkeypatch.setattr(os, "replace", spy)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )
    monkeypatch.undo()

    assert result == 2, "must be the documented failure code, not a traceback"
    err = capsys.readouterr().err
    assert str(plan) in err and str(history) in err, err
    assert "NEITHER document" in err, err
    assert "First" in err, "the swept titles must be named"
    assert "moved" not in err, "no past-tense success line"


def test_publish_state_never_raises_out_of_a_failure_handler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Path.exists()` propagates EACCES; it does not swallow it.

    Found by the adversarial lens. The publish check is consulted from *inside*
    an `except` handler, so a raise there replaced the real exception, skipped
    the rollback entirely and let the cleanup delete it: blocks in neither
    document, no message, and two temps leaked beside the living handoff.
    Reachable when the parent directory becomes unsearchable mid-run.

    So the answer is a tri-state, and the indeterminate case is named rather
    than guessed.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")
    staged = aw.stage_text(target, "replacement\n")

    def denied(self: Path) -> bool:
        raise PermissionError(13, "Permission denied")

    # `monkeypatch.context()`, not bare `setattr`: if the call under test raises
    # — which is exactly the regression — the patch has to come off anyway, or
    # pytest's own teardown calls the poisoned `Path.exists` and the session
    # dies during cleanup instead of reporting a failed test.
    def cancelled(self: Path) -> bool:
        raise KeyboardInterrupt

    for injected in (denied, cancelled):
        # An INTERRUPT, not only an OSError: `Path.exists()` calls `os.stat`, a
        # blocking syscall, and every caller of this is a failure handler — so
        # an escape here skips the recovery it was about to run and the caller's
        # cleanup then deletes the copy staged for it. `except OSError` was not
        # enough, and nothing caught that until a review lens measured it.
        with monkeypatch.context() as m:
            m.setattr(Path, "exists", injected)
            try:
                state = staged.publish_state()
            except BaseException as exc:  # noqa: BLE001 — that is the regression
                # Caught and converted rather than allowed to propagate: pytest
                # aborts the whole session on a KeyboardInterrupt, so the mutant
                # this pins would kill the run instead of naming a failed test —
                # and "a kill is only a kill if you can see which test failed".
                pytest.fail(f"publish_state() must never raise; got {exc!r}")
        assert state == "unknown", injected.__name__

    assert staged.publish_state() == "pending"
    staged.commit()
    assert staged.publish_state() == "published"


def test_an_indeterminate_history_publish_restores_and_warns_of_duplicates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When it cannot tell whether the history landed, it must err toward keeping.

    Duplicated blocks are visible and fixable; blocks in neither document are
    gone. So the handoff is restored — and because that risks the history
    holding them too, the operator is told to check for duplicates by name
    rather than being given a clean "no changes applied".
    """
    archive = _load_module("archive_unknown", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")

    real_replace, real_exists = os.replace, Path.exists

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if Path(str(dst)) == history:
            raise OSError(5, "Input/output error")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    def flaky_exists(self: Path) -> bool:
        if self.name.endswith(".devkit-tmp") and history.name in self.name:
            raise PermissionError(13, "Permission denied")
        return real_exists(self)

    monkeypatch.setattr(os, "replace", spy)
    monkeypatch.setattr(Path, "exists", flaky_exists)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )
    monkeypatch.undo()

    assert result == 2
    err = capsys.readouterr().err
    assert "could not determine" in err, err
    assert "duplicates" in err, err
    assert "First" in err, "the titles to look for must be named"
    assert plan.read_text(encoding="utf-8") == original_plan, "the handoff was not restored"


def test_an_unconfirmed_handoff_publish_is_not_reported_as_a_sweep(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the run cannot tell, the damage message must not pick the confident side.

    Measured by a review lens with a real EACCES: the handoff publish and its
    rollback both failed for the same reason — an unsearchable parent, which is
    also the one condition that makes the publish state indeterminate, so the
    two are not independent. The operator was told the blocks were in NEITHER
    document and to restore from git, while the handoff sat byte-identical on
    disk still holding them.
    """
    archive = _load_module("archive_unconfirmed", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")

    real_exists = Path.exists

    def spy(src: object, dst: object, **kwargs: object) -> None:
        raise OSError(13, "Permission denied")  # nothing publishes, ever

    def indeterminate(self: Path) -> bool:
        if self.name.endswith(".devkit-tmp") and plan.name in self.name:
            raise PermissionError(13, "Permission denied")
        return real_exists(self)

    monkeypatch.setattr(os, "replace", spy)
    monkeypatch.setattr(Path, "exists", indeterminate)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )
    monkeypatch.undo()

    assert result == 2
    err = capsys.readouterr().err
    assert plan.read_text(encoding="utf-8") == original_plan, "fixture check: untouched"
    # It must reach the recovery at all (the "unknown" arm), and must not assert
    # a sweep it could not establish.
    assert "has been swept" not in err, f"asserted a sweep that never happened: {err!r}"
    assert "could not be confirmed either way" in err, err


def test_a_completed_move_interrupted_afterwards_still_says_so(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 130 in silence over a sweep that fully succeeded reads as "nothing happened".

    This is the one path the code has already established is COMPLETE — the
    history was read back and matches. Its `OSError` twin prints a careful
    message; the interrupt twin printed nothing at all, which is #164's false
    all-clear pointing the other way.
    """
    archive = _load_module("archive_done_interrupt", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace

    def spy(src: object, dst: object, **kwargs: object) -> None:
        real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
        if Path(str(dst)) == history:
            raise KeyboardInterrupt  # lands, then cancelled

    monkeypatch.setattr(os, "replace", spy)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    err = capsys.readouterr().err
    assert "move is complete" in err, f"a completed sweep exited silently: {err!r}"
    assert "First" in history.read_text(encoding="utf-8"), "fixture check: it did complete"


@pytest.mark.parametrize("fail_at", ["plan", "history"])
def test_a_rollback_that_landed_is_not_reported_as_damage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    fail_at: str,
) -> None:
    """The recovery must judge itself by evidence, exactly as the publishes do.

    Both review lenses found this independently. The forward publishes consult
    `publish_state()` precisely because "raised here ⇒ not published" is unsound
    — and both rollback handlers then made that same inference about themselves.
    An interrupt in the documented window, after the rollback's own `os.replace`
    returns, produced a full damage report over a handoff that was correctly
    restored, sending the operator to recover a file that already holds this
    session's uncommitted block.

    Parametrised over both publish sites: three separate findings this session
    were "the guard, message or test exists at one site and not the other".
    """
    archive = _load_module(f"archive_rb_landed_{fail_at}", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if fail_at == "plan" and target == plan and seen.count(plan) == 1:
            real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
            raise KeyboardInterrupt  # published, then cancelled
        if fail_at == "history" and target == history:
            raise OSError(28, "No space left on device")
        if target == plan and seen.count(plan) == 2:
            # The rollback lands, and only THEN is interrupted.
            real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
            raise KeyboardInterrupt
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    # How the run TERMINATES differs by site and is not the point: on the plan
    # site the interrupt is the only cause and propagates; on the history site
    # the interrupt arrives during recovery from an ENOSPC that recovery then
    # completed, so the ENOSPC is what gets reported. The invariant under test is
    # the same either way — a restored handoff is never called damage.
    with contextlib.suppress(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    assert plan.read_text(encoding="utf-8") == original_plan, "fixture check: it did land"
    err = capsys.readouterr().err
    assert "NEITHER document" not in err, (
        f"reported damage over a handoff that was restored: {err!r}"
    )
    assert "may be in NEITHER" not in err, err


def test_a_vanished_history_temp_is_not_mistaken_for_a_published_move(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp's absence is evidence; the destination's content is the fact.

    A review lens measured the proxy failing: with the staged temp removed by
    something other than the rename, and the rename then failing, this branch
    reported the move complete while the blocks were in neither document — the
    false all-clear #164 exists to eliminate, one branch over. Hedging the
    wording was the first fix; reading the destination back and comparing it to
    what the run intended to write settles it outright.
    """
    archive = _load_module("archive_readback", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    real_replace, real_exists = os.replace, Path.exists

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if Path(str(dst)).name == history.name:
            raise OSError(5, "Input/output error")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    def vanished(self: Path) -> bool:
        if self.name.endswith(".devkit-tmp") and history.name in self.name:
            return False  # something else removed it
        return real_exists(self)

    monkeypatch.setattr(os, "replace", spy)
    monkeypatch.setattr(Path, "exists", vanished)
    result = archive.main(
        ["--keep", "2", "--plan", str(plan), "--history", str(history)]
    )
    monkeypatch.undo()

    assert result == 2
    err = capsys.readouterr().err
    assert "move is complete" not in err, f"a false all-clear over lost blocks: {err!r}"
    assert plan.read_text(encoding="utf-8") == original_plan, "the handoff was not restored"
    assert history.read_text(encoding="utf-8") == original_history
    assert "## Earlier session — First" in plan.read_text(encoding="utf-8")


def test_a_second_interrupt_during_the_rollback_still_reports_the_damage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Ctrl-C during the recovery must not exit silently on a swept handoff.

    The rollback handlers caught `OSError`, so a second interrupt — landing
    while the first one is being recovered from — escaped uncaught: exit 130,
    blocks in neither document, nothing on stderr, and the exit-code contract's
    own paragraph promising that a 130 meant no damage.
    """
    archive = _load_module("archive_double_ki", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if target == history:
            raise KeyboardInterrupt
        if target == plan and seen.count(plan) == 2:
            raise KeyboardInterrupt  # again, during the recovery
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    err = capsys.readouterr().err
    assert "NEITHER document" in err, f"a cancelled run damaged both docs silently: {err!r}"
    assert "First" in err


def test_a_cancelled_run_still_terminates_as_cancelled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bare `raise` in the disaster handler re-raises the ROLLBACK's error.

    The handler catches the history publish's exception, tries the rollback, and
    on a double failure must surface the *original*. A bare `raise` inside
    `except OSError as rollback_exc` surfaces the rollback's `OSError` instead —
    so an interrupted run stops looking interrupted, and the documented 130
    becomes a traceback exit 1. Reported by a review lens as pinned by nothing,
    which it was.
    """
    archive = _load_module("archive_cancel_code", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if target == history:
            raise KeyboardInterrupt  # the operator cancels
        if target == plan and seen.count(plan) == 2:
            raise OSError(28, "No space left on device")  # and the rollback fails
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    # The damage report is still emitted — the operator needs it either way.
    assert "NEITHER document" in capsys.readouterr().err


def test_an_interrupt_after_the_history_lands_does_not_duplicate_the_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rolling back a COMPLETED move puts the blocks in both documents.

    The other half of the same finding. An interrupt can arrive after
    `os.replace` has already published the history, so a handler that infers
    "raised here ⇒ not published" restores the handoff over a finished move —
    blocks in both files, and a re-run appends them to the history a second time,
    which is exactly what the plan-first ordering exists to prevent.

    So the decision is read from the filesystem (`publish_state()`), not from
    the exception's position.
    """
    archive = _load_module("archive_sigint_after", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace

    def publish_then_interrupt(src: object, dst: object, **kwargs: object) -> None:
        real_replace(src, dst, **kwargs)  # type: ignore[arg-type]
        if Path(str(dst)) == history:
            raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", publish_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])
    monkeypatch.undo()

    live = plan.read_text(encoding="utf-8")
    archived = history.read_text(encoding="utf-8")
    assert "## Earlier session — First" not in live, "the completed move was rolled back"
    assert "First" in archived
    assert archived.count("First body line 1.") == 1, "the blocks landed in history twice"
    assert live.count("First body line 1.") == 0, "the blocks are in BOTH documents"


def test_the_temp_is_fsynced_before_the_rename_not_after(tmp_path: Path) -> None:
    """The module's central durability claim, and deleting it cost no test.

    "The bytes have to be on the medium before a directory entry points at
    them" — without the pre-rename fsync a crash can publish a name for content
    that was never written. Asserted as an ordering, which is what the claim is.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    events: list[str] = []
    real_fsync, real_replace = os.fsync, os.replace

    def spy_fsync(fd: int) -> None:
        events.append("fsync")
        return real_fsync(fd)

    def spy_replace(src: object, dst: object, **k: object) -> None:
        events.append("replace")
        return real_replace(src, dst, **k)  # type: ignore[arg-type]

    os.fsync, os.replace = spy_fsync, spy_replace  # type: ignore[assignment]
    try:
        aw.stage_text(target, "published\n").commit()
    finally:
        os.fsync, os.replace = real_fsync, real_replace  # type: ignore[assignment]

    assert "replace" in events, "fixture check: the publish happened"
    assert events.index("fsync") < events.index("replace"), (
        f"the temp must be fsynced before it is renamed into place; got {events}"
    )
    assert events[-1] == "fsync", f"the parent directory is fsynced after; got {events}"


def test_an_interrupt_during_staging_leaves_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`except BaseException` in the staging cleanup — narrowing it leaks a temp.

    The docstring promises temps are "removed on every path this module
    controls, including exceptions", and `except Exception` satisfies neither
    that sentence nor the reason for it: debris lands beside the living handoff,
    where the next wrap-up step stages files for commit.

    Injected at the staging `os.fsync`, which is inside the guarded block. A
    first version of this test raised from an f-string argument instead — which
    is evaluated at the *call site*, before `stage_text` runs, so it never
    entered the handler and the narrowing mutant survived it.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    def interrupting_fsync(fd: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "fsync", interrupting_fsync)
    with pytest.raises(KeyboardInterrupt):
        aw.stage_text(target, "replacement\n")
    monkeypatch.undo()

    assert not list(tmp_path.glob("*.devkit-tmp")), "an interrupt leaked a staged temp"
    assert target.read_text(encoding="utf-8") == "original\n"


def test_an_interrupt_in_the_durability_step_cannot_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """"Nothing here may raise. Ever." — and `except OSError` did not achieve it.

    `os.open`/`os.fsync` on a directory are blocking syscalls, so they are the
    realistic landing spot for an interactive Ctrl-C. An escape here reaches the
    caller's cleanup and unlinks the staged rollback, losing the swept blocks
    over a document that was in fact published.

    The sibling interrupt tests inject at `os.replace` and so cannot see this:
    narrowing the handler back to `OSError` survived all of them.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")
    staged = aw.stage_text(target, "published\n")

    real_open = os.open

    def interrupting_open(path: object, flags: int, *a: object, **k: object) -> int:
        if Path(str(path)) == tmp_path:
            raise KeyboardInterrupt
        return real_open(path, flags, *a, **k)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "open", interrupting_open)
    staged.commit()  # must not raise
    monkeypatch.undo()

    assert target.read_text(encoding="utf-8") == "published\n"


def test_commit_and_abort_are_idempotent_as_documented(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The class docstring tells callers to use `finally: abort()` after a commit.

    That shape is only safe because both are idempotent. Asserted on the CALLS,
    not only on the resulting bytes: after a commit the temp path no longer
    exists, so a missing guard just unlinks nothing and every content assertion
    still passes — which is how the `abort()` guard survived a first attempt at
    this test. What it would really cost is the temp name being reused by a
    concurrent run in between, at which point the no-op deletes someone else's
    staged file.
    """
    aw = _atomic_write()
    target = tmp_path / "doc.md"
    target.write_text("original\n", encoding="utf-8")

    staged = aw.stage_text(target, "published\n")
    staged.commit()

    replaces: list[object] = []
    unlinks: list[object] = []
    real_replace, real_unlink = os.replace, Path.unlink

    def spy_replace(src: object, dst: object, **k: object) -> None:
        replaces.append(dst)
        return real_replace(src, dst, **k)  # type: ignore[arg-type]

    def spy_unlink(self: Path, **k: object) -> None:
        unlinks.append(self)
        return real_unlink(self, **k)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy_replace)
    monkeypatch.setattr(Path, "unlink", spy_unlink)
    staged.commit()  # second commit: must not rename again
    staged.abort()  # the documented `finally: abort()` after a good commit
    monkeypatch.undo()

    assert replaces == [], "a settled write published a second time"
    assert unlinks == [], "abort() after commit() tried to delete the temp path"
    assert target.read_text(encoding="utf-8") == "published\n"

    other = aw.stage_text(target, "discarded\n")
    other.abort()
    other.commit()  # after an abort, commit must not resurrect anything
    assert target.read_text(encoding="utf-8") == "published\n"


def test_a_directory_target_is_named_as_one(tmp_path: Path) -> None:
    """A directory has nlink >= 2, so it was diagnosed as a hardlink problem.

    The refusal told the operator to "remove the extra link(s)" for something
    that is not a document at all. Unreachable from the sweep, which guards with
    `is_file()`; latent in the library.
    """
    aw = _atomic_write()
    with pytest.raises(aw.AtomicWriteRefused, match="is a directory"):
        aw.stage_text(tmp_path, "replacement\n")


def test_a_new_file_gets_the_mode_write_text_would_have_given_it(
    tmp_path: Path,
) -> None:
    """`_default_mode()` is the nonexistent-target branch, and it was unpinned.

    `mkstemp` creates `0600`, so without this the first write of a document would
    silently be private where `write_text` would have made it `0666 & ~umask`.
    Mutating it to a constant survived the suite.
    """
    aw = _atomic_write()
    reference = tmp_path / "reference.md"
    reference.write_text("x\n", encoding="utf-8")  # what write_text produces
    target = tmp_path / "new.md"

    aw.stage_text(target, "y\n").commit()

    assert stat.S_IMODE(target.stat().st_mode) == stat.S_IMODE(reference.stat().st_mode)


def test_a_lone_control_character_survives_the_sweep(tmp_path: Path) -> None:
    """`"\\x1c".strip() == ""`, so the trailing-blank strip ate it (issue #162).

    Measured on the real tool: a lone file separator on a swept block's last line
    did not reach the history document. Silent content loss in a tool whose
    contract is that it moves content — the worst shape for it, however exotic
    the character.
    """
    archive = _load_module("archive_control_char", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    # On the LAST line of the oldest block, which is where the trailing-blank
    # strip runs — planted anywhere else it survives regardless and the test is
    # vacuous.
    text = plan.read_text(encoding="utf-8").replace(
        "First body line 8.\n",
        "First body line 8.\n\x1c\n",
        1,
    )
    assert "\x1c" in text, "fixture check: the separator was actually planted"
    plan.write_text(text, encoding="utf-8")

    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0

    assert "\x1c" in history.read_text(encoding="utf-8"), (
        "the swept block lost a character the sweep promised to move"
    )
    assert "\x1c" not in plan.read_text(encoding="utf-8")


def test_a_separator_like_line_with_a_control_character_is_content(
    tmp_path: Path,
) -> None:
    """The OTHER half of the #162 fix, and mutation showed it was unpinned.

    The fix touched two deciders: `parse_blocks`' trailing strip and `_is_sep`.
    Only the first had a test — reverting `_is_sep` to a bare `str.strip()`
    survived the whole suite. It is not a no-op: `"\\x1c___\\x1c"` then reads as a
    separator and is popped off the end of a swept block, so the tool exits 0
    with a success report having silently dropped content. That is the #162
    failure exactly, in the sibling function of the one that got covered.
    """
    archive = _load_module("archive_is_sep", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    text = plan.read_text(encoding="utf-8").replace(
        "First body line 8.\n", "First body line 8.\n\x1c___\x1c\n", 1
    )
    assert "\x1c___\x1c" in text, "fixture check: the planted line is there"
    plan.write_text(text, encoding="utf-8")

    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0

    assert "\x1c___\x1c" in history.read_text(encoding="utf-8"), (
        "_is_sep treated a control character as separator whitespace and the "
        "line was dropped"
    )


def test_an_interrupt_between_the_two_publishes_restores_the_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl-C at the one unsafe instant must not cost the swept blocks.

    Found by the adversarial lens of the review panel. `main()`'s cleanup is
    `finally: abort()` over every staged write, and it ran on ANY exception — so
    a `KeyboardInterrupt` landing after the handoff was published and during the
    history publish unlinked the rollback copy staged precisely to recover it.
    Blocks in neither document, no message, exit 1.

    The measured contrast is what makes it a HIGH: a **SIGKILL** at the same
    instant is survivable, because no handler runs and the rollback temp is left
    on disk. The interactive interrupt — the likely one, since `wrap-up` is
    interactive — was the destructive case.
    """
    archive = _load_module("archive_sigint", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")

    real_replace = os.replace

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if Path(str(dst)) == history:
            raise KeyboardInterrupt
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    with pytest.raises(KeyboardInterrupt):
        archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)])

    assert plan.read_text(encoding="utf-8") == original_plan, (
        "the handoff was left swept and the rollback copy deleted"
    )
    assert history.read_text(encoding="utf-8") == original_history
    assert "## Earlier session — First" in plan.read_text(encoding="utf-8")
    assert not list(tmp_path.glob("*.devkit-tmp"))


def test_the_rollback_is_staged_before_anything_is_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The load-bearing property of the redesign, and it was pinned by nothing.

    Both docstrings justify the whole shape by it: the rollback copy is written
    UP FRONT so recovery costs an `os.replace` rather than a full-size write on
    the disk that just refused one — the failure that reverted the first attempt
    on #160. Moving that `stage_text` call into the failure handler, i.e. back to
    the reverted shape, passed the entire suite (571 passed, 1 deselected).

    Asserted on ordering directly: by the time the first publish happens, three
    temps exist. A late-staging implementation has two.
    """
    archive = _load_module("archive_stage_order", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace
    temps_at_first_publish: list[int] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        if not temps_at_first_publish:
            temps_at_first_publish.append(len(list(tmp_path.glob("*.devkit-tmp"))))
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0

    assert temps_at_first_publish == [3], (
        "expected the new handoff, the new history AND the rollback all staged "
        f"before the first publish; saw {temps_at_first_publish}"
    )


def test_the_disaster_message_carries_no_past_tense_success_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both review lenses found this independently, on stderr.

    The both-failed branch appended the whole `report`, whose header reads
    `moved N block(s) to <history>` — a past-tense success line inside the
    message saying the move did not happen, and the exact string the engine's own
    comment records as removed in #160. The standing guard only covered stdout,
    and the sibling test's `"First" in err` was satisfied by the offending line
    itself, so it pinned the contradiction in place.
    """
    archive = _load_module("archive_no_success_line", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_replace = os.replace
    seen: list[Path] = []

    def spy(src: object, dst: object, **kwargs: object) -> None:
        target = Path(str(dst))
        seen.append(target)
        if target == history or (target == plan and seen.count(plan) == 2):
            raise OSError(28, "No space left on device")
        return real_replace(src, dst, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", spy)
    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 2

    err = capsys.readouterr().err
    assert "moved" not in err, f"a past-tense success line survived on stderr: {err}"
    assert "plan lines" not in err, err
    # The titles themselves must still be there — that is what the branch is for.
    assert "First" in err and "Second" in err, err


def test_the_sweep_normalises_line_endings_deliberately(tmp_path: Path) -> None:
    """The other half of #162 — pinned as a decision, not left as a default.

    Reading and writing as text translates on the way in and normalises on the
    way out, so a CRLF handoff comes back all-LF: the whole file, not only the
    blocks that moved. That is the documented choice (these are Markdown
    documents the kit renders with `\\n`, and `budget_line_count`'s parity with
    `check_doc_budget` requires already-translated text) — but it was previously
    an accident of the default `newline` argument, which is what makes it worth
    a test either way. If the sweep is ever made byte-preserving, this test is
    the one that must be deliberately rewritten.

    **What this test cannot see, stated rather than left implied.** It runs on
    POSIX, where `os.linesep` is `\\n` — so it passes identically whether the
    sweep writes with `newline="\\n"` or inherits `newline=None`. The two differ
    only on Windows, where the inherited form emits CRLF and the docstring's
    claim would be false. The explicit `newline="\\n"` in `main()` is what makes
    the guarantee real; this test pins the POSIX half of it, and no more.
    """
    archive = _load_module("archive_eol", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    plan.write_bytes(plan.read_bytes().replace(b"\n", b"\r\n"))
    history.write_bytes(history.read_bytes().replace(b"\n", b"\r\n"))
    assert b"\r\n" in plan.read_bytes(), "fixture check"

    assert archive.main(["--keep", "2", "--plan", str(plan), "--history", str(history)]) == 0

    assert b"\r" not in plan.read_bytes(), "CRLF survived — the docstring says it does not"
    assert b"\r" not in history.read_bytes()
    assert "## Earlier session — First" not in plan.read_text(encoding="utf-8")
    assert "First" in history.read_text(encoding="utf-8")


@pytest.mark.parametrize("damaged", ["plan", "history"])
@pytest.mark.parametrize(
    "how",
    [
        # Only the chmod-000 axis is uid-sensitive; `non_utf8` damages the bytes
        # and must keep running as root. Marking the whole function would skip
        # both and silently halve this test's coverage in a root container.
        pytest.param("unreadable", marks=_needs_permission_enforcement),
        "non_utf8",
    ],
)
def test_a_read_failure_names_the_document_that_failed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], damaged: str, how: str
) -> None:
    """Exit 2 must name WHICH document could not be read.

    `UnicodeDecodeError` carries no filename, and `wrap-up.md`'s exit-2 branch
    tells the operator to read this message and act on it — with two documents in
    play, a message that names neither is not actionable.

    Parametrized over both documents on purpose: the earlier tests damaged only
    the plan, so collapsing the per-file reads back into one combined `try` (and
    losing the path entirely) survived the whole suite. Both axes, because
    "unreadable" and "non-UTF-8" arrive as different exception types.
    """
    archive = _load_module(
        f"archive_read_names_{damaged}_{how}", ENGINE_DIR / "archive_plan_sessions.py"
    )
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    target = plan if damaged == "plan" else history
    other = history if damaged == "plan" else plan

    if how == "unreadable":
        target.chmod(0o000)
    else:
        target.write_bytes(target.read_bytes().replace(b"##", b"#\xff", 1))

    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        target.chmod(0o644)

    assert result == 2
    err = capsys.readouterr().err
    assert str(target) in err, f"the failing document must be named: {err}"
    assert str(other) not in err, f"only the failing document should be named: {err}"


@_needs_permission_enforcement
def test_the_no_changes_applied_literal_wrap_up_quotes_is_pinned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`wrap-up.md` quotes "no changes applied" to the operator — pin the literal.

    Only a NEGATIVE assertion existed (`"no changes applied" not in err` on the
    rollback path), so rewording it to anything else survived the whole suite
    while the workflow kept quoting the old text at the operator.

    Renamed from `..._write_failure_message_...`: since #164 a `0444` handoff
    takes the **refusal** branch, not the write-failure one, and the old name
    said otherwise. It passes because both messages end in this literal, which is
    exactly the property being pinned — so both branches are asserted below
    rather than leaving the branch identity to the name.
    """
    archive = _load_module("archive_wf_literal", ENGINE_DIR / "archive_plan_sessions.py")
    plan_dir = tmp_path / "live"
    plan_dir.mkdir()
    plan = plan_dir / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    plan.chmod(0o444)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        plan.chmod(0o644)

    assert result == 2
    refused = capsys.readouterr().err
    assert "no changes applied" in refused
    assert "refusing to write" in refused, "a read-only doc is refused, not attempted"

    # And the same literal on the genuine write-failure branch, which is a
    # different code path reached a different way.
    plan_dir.chmod(0o555)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        plan_dir.chmod(0o755)

    assert result == 2
    failed = capsys.readouterr().err
    assert "no changes applied" in failed
    assert "write failed" in failed


def test_the_target_lines_noop_message_is_pinned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The `--target-lines` early-exit wording had no assertion anywhere.

    Its `--keep` twin is pinned; this one was reworded freely with the suite
    green. The branch and its exit code were already covered — only the text a
    human reads was not.
    """
    archive = _load_module("archive_tl_noop_msg", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    result = archive.main(
        ["--target-lines", "46", "--plan", str(plan), "--history", str(history)]
    )

    assert result == 0
    assert "nothing to move: 46 line(s) <= --target-lines 46." in capsys.readouterr().out


def _is_os_path_join(node: ast.AST) -> bool:
    """An `os.path.join` callee.

    Requires the `.path` qualifier rather than matching any `.join`: the bare
    form would also match `", ".join(...)`, and over-matching a method this
    common is noise rather than the loud-direction failure the other helpers
    accept.
    """
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "join"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "path"
    )


def _is_path_constructor(node: ast.AST) -> bool:
    """A `Path` callee — bare, or any qualification of it.

    Name-only, like :func:`_is_repo_root`: `pathlib.Path` and `p.Path` both
    match, and so would an unrelated `shutil.Path`. That over-matches in the
    LOUD direction — a false positive names a file and a line in the assertion
    message — which is the direction this whole guard is built to fail in.
    """
    if isinstance(node, ast.Name):
        return node.id == "Path"
    return isinstance(node, ast.Attribute) and node.attr == "Path"


def _is_scripts_segment(node: ast.AST) -> bool:
    """The literal ``"scripts"``, bare or wrapped in a single-argument `Path()`.

    The mirror of :func:`_is_repo_root`, and it exists for the same reason one
    round later: a lens closed the wrapped-ROOT forms and then found
    `REPO_ROOT / Path("scripts")` still open — the wrapper had simply moved to
    the other operand. Wrapping either side is a no-op on the resulting path, so
    both sides have to resolve through it.
    """
    if isinstance(node, ast.Constant):
        return node.value == "scripts"
    if isinstance(node, ast.Call) and _is_path_constructor(node.func):
        return len(node.args) == 1 and _is_scripts_segment(node.args[0])
    return False


def _is_repo_root(node: ast.AST) -> bool:
    """`REPO_ROOT`, however it is reached.

    Three ways, and the third is recursive:

    - a bare name, `REPO_ROOT`;
    - an attribute, `_repo_layout.REPO_ROOT` — the same constant one
      qualification away, which a name-only guard would treat as a different
      thing;
    - wrapped in a single-argument `Path(...)`, because `Path(REPO_ROOT)` IS
      `REPO_ROOT` — the constructor is a no-op on something already a Path, so
      `Path(REPO_ROOT) / "scripts"` is the defect wearing a hat.

    The recursion is what makes the third case general rather than one more
    spelling: it composes with both other forms and with itself, so
    `Path(pathlib.Path(mod.REPO_ROOT))` resolves too. A lens found the
    unwrapped case open AFTER a previous round had closed
    `Path(REPO_ROOT, "scripts")` and declared the class shut — the difference
    being one argument, which is exactly the kind of distinction an enumeration
    misses and a recursive definition does not.

    Single-argument only: `Path(REPO_ROOT, "scripts")` is not "the repo root",
    it is the repo root JOINED to something, and the scanner's Call branch
    handles it there.
    """
    if isinstance(node, ast.Name):
        return node.id == "REPO_ROOT"
    if isinstance(node, ast.Attribute):
        return node.attr == "REPO_ROOT"
    if isinstance(node, ast.Call) and _is_path_constructor(node.func):
        return len(node.args) == 1 and _is_repo_root(node.args[0])
    return False


def _repo_root_slash_scripts_nodes(source: str) -> list[int]:
    """Line numbers of live `REPO_ROOT / "scripts"` expressions in ``source``.

    AST, not grep, and that is the whole point: this file, `test_pr_watch.py`,
    `test_kit_doctor.py` and `test_kitconfig.py` all DISCUSS the bad idiom in
    comments and docstrings explaining why it was removed. A textual scan would
    have to be taught to ignore those, and the day it got that wrong the honest
    fix would be to delete the explanation. Parsing sees only what executes.
    (That list named `_repo_layout.py` until a lens checked it — that file
    discusses the *different*, already-fixed `parents[2]` idiom and never
    mentions this one. Re-derive with
    `grep -ln 'REPO_ROOT / "scripts"' scripts/tests/*.py`.)

    **What it recognizes, and a warning about this paragraph.** Recognized:
    `REPO_ROOT` reached as a bare name, as an attribute, or wrapped in a
    single-argument `Path(...)` — see :func:`_is_repo_root`, which resolves all
    three recursively — divided by `"scripts"`, or joined to it via
    `.joinpath("scripts", …)` or `Path(<root>, "scripts", …)`.

    THREE forms are NOT recognized, and all three are name-binding — which is
    the actual shape of the excluded class, dataflow being the consequence
    rather than the definition:

    - binding the constant (`root = REPO_ROOT; root / "scripts"`);
    - hoisting the segment (`SEG = "scripts"; REPO_ROOT / SEG`);
    - aliasing the constructor (`from pathlib import Path as PP;
      PP(REPO_ROOT, "scripts")`) — named here because a lens pointed out it
      rides under the same umbrella and the umbrella did not mention it.

    Closing any of them is out of proportion, and a naive attempt at the first
    immediately false-positives on a legitimate `root` fixture elsewhere in this
    suite.

    **Do not read the paragraph above as a proof of completeness.** Three
    consecutive review rounds each closed a no-dataflow gap here and each
    declared the class shut — `.joinpath`, then `Path(root, "scripts")`, then
    `Path(root) / "scripts"` — and the third was found by a lens that built the
    real defect in a real file and watched the scan pass over it. The intended
    line is "needs dataflow or not"; the demonstrated track record is that the
    line has been drawn wrong every time it has been drawn. `_GUARD_CASES`
    below is therefore the authority on what this recognizes, because it
    executes; this prose is a summary of it and has been the less reliable of
    the two. If you are about to add a spelling here, add a case there first
    and let it fail.

    `os.path.join(REPO_ROOT, "scripts")` is recognized too. It was previously
    excused on the argument that a stdlib join would be conspicuous in a
    pathlib-only suite — a social claim inside a mechanical guard, and `os` is
    already imported in this file for unrelated reasons. It costs the same
    one-hop inspection as the rest.

    The guard is
    deliberately anchored on `REPO_ROOT` rather than matching any `/ "scripts"`:
    `tmp_path / "scripts"` is correct and common here, because the synthetic
    trees these tests build stand in for an adopter on the kit's default layout.
    """
    found: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
            continue
        if _is_repo_root(node.left) and _is_scripts_segment(node.right):
            found.append(node.lineno)
    # Two Call forms, both path-identical to the operator form above and both
    # pathlib's own idiom, so a refactor reaches either without meaning to:
    #
    #   REPO_ROOT.joinpath("scripts", …)   — a method on the constant
    #   Path(REPO_ROOT, "scripts", …)      — the constructor's varargs
    #
    # Lenses found each of them slipping past a narrower version of this
    # function, one round apart. Neither needs dataflow, which is what
    # distinguishes them from the two genuinely-excluded spellings below.
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        args = node.args
        if isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath":
            if not _is_repo_root(node.func.value):
                continue
        elif _is_os_path_join(node.func):
            # Closed rather than excused. The previous version left this open on
            # the argument that a stdlib join would "be conspicuous" in a
            # pathlib-only suite — a social claim inside a mechanical guard, and
            # `os` is already imported here for unrelated reasons. It costs the
            # same one-hop inspection as the others.
            if not (args and _is_repo_root(args[0])):
                continue
            args = args[1:]
        elif _is_path_constructor(node.func):
            # `Path(REPO_ROOT, "scripts")` — the root is the FIRST argument, so
            # the segment to check is the second.
            if not (args and _is_repo_root(args[0])):
                continue
            args = args[1:]
        else:
            continue
        first = args[0] if args else None
        if first is not None and _is_scripts_segment(first):
            found.append(node.lineno)
    return sorted(found)


# (source, detected) — the guard's contract, pinned on synthetic input rather
# than on whatever happens to be on disk. Round 1 swept the real offenders out,
# so the scanning test below has nothing left to find and every widening added
# since has been mutation-provably dead: a lens disabled the attribute branch,
# then the joinpath loop, then the rglob, and the suite stayed green each time.
#
# The NEGATIVE cases are the half worth having. Two of them are the documented
# limitations, so if someone ever closes one, this fails and sends them to the
# docstring that claims it is open — a limit nobody can quietly outgrow.
_GUARD_CASES = [
    ('x = REPO_ROOT / "scripts" / "a.py"', True),
    ('x = mod.REPO_ROOT / "scripts" / "a.py"', True),
    ('x = REPO_ROOT.joinpath("scripts", "a.py")', True),
    ('x = Path(REPO_ROOT, "scripts", "a.py")', True),
    ('x = pathlib.Path(REPO_ROOT, "scripts")', True),
    # `Path(REPO_ROOT)` IS `REPO_ROOT`; a lens found these open after a previous
    # round had closed the two-argument form and called the class shut.
    ('x = Path(REPO_ROOT) / "scripts"', True),
    ('x = Path(REPO_ROOT).joinpath("scripts")', True),
    ('x = pathlib.Path(mod.REPO_ROOT) / "scripts"', True),
    # Correct and common here: these tests build synthetic trees standing in for
    # an adopter on the kit's default layout.
    ('x = tmp_path / "scripts" / "a.py"', False),
    ('x = REPO_ROOT / "state"', False),
    # Documented limitations. All three are name-binding.
    ('root = REPO_ROOT\nx = root / "scripts"', False),
    ('SEG = "scripts"\nx = REPO_ROOT / SEG', False),
    ('from pathlib import Path as PP\nx = PP(REPO_ROOT, "scripts")', False),
    ('x = os.path.join(REPO_ROOT, "scripts")', True),
    # The wrapper on the SEGMENT rather than the root — a lens found these open
    # one round after the wrapped-root forms were closed.
    ('x = REPO_ROOT / Path("scripts")', True),
    ('x = REPO_ROOT.joinpath(Path("scripts"), "a.py")', True),
    # `.join` without the `.path` qualifier is an ordinary string method.
    ('x = ", ".join(REPO_ROOT)', False),
    # Prose is inert under a parser — the reason this is AST and not grep.
    ('"""Do not write REPO_ROOT / \'scripts\' here."""', False),
]


@pytest.mark.parametrize(("source", "detected"), _GUARD_CASES)
def test_the_engine_dir_guard_recognises_exactly_what_it_claims(source, detected):
    """The guard's own behaviour, pinned independently of the tree it scans."""
    assert bool(_repo_root_slash_scripts_nodes(source)) is detected


def test_no_test_module_rebuilds_the_engine_dir_from_repo_root():
    """#534 cause 3, pinned — because nothing else in this repo can pin it.

    `ENGINE_DIR` and `REPO_ROOT / "scripts"` resolve to the SAME path in the
    kit's own layout, so no test running here can distinguish the correct form
    from the defective one by behaviour. A review lens on `#545` reverted all
    three fixes and the whole suite stayed green — structurally, not by
    accident. Until this test, the only thing that had ever caught this class
    was a real adopter running a real vendored install (`#40`, `#134`, `#534`,
    `#537`), which is a feedback loop measured in months.

    So this pins the SHAPE rather than the behaviour. That is a weaker
    guarantee and it is the one available: a test that cannot fail in the
    layout it runs in has to assert about the source text instead of the
    result.

    Engine paths in a test module must come from `ENGINE_DIR` — which every one
    of these modules already computes, either from `_repo_layout.engine_dir()`
    or from its own `Path(__file__).resolve().parent.parent`. `REPO_ROOT` stays
    correct for everything that is genuinely repo-relative and not engine-
    relative: `docs/`, `.claude/`, `.agents/`, `kit-manifest.json`.
    """
    # rglob, so `lib/state_paths/tests/` is covered too — AGENTS.md counts it as
    # part of the full suite, and a guard that stops at one test directory is a
    # guard with a documented blind spot.
    scanned = sorted(ENGINE_DIR.rglob("tests/*.py"))
    # Pins the rglob itself. A lens reverted it to `glob` and nothing failed,
    # because the directory it stops reaching holds no offender today — so the
    # widening was live coverage that no test could tell had gone.
    directories = {path.parent.relative_to(ENGINE_DIR).as_posix() for path in scanned}
    assert directories == {"tests", "lib/state_paths/tests"}, (
        f"the scan no longer covers both test directories: {sorted(directories)}"
    )

    offenders = {}
    for path in scanned:
        lines = _repo_root_slash_scripts_nodes(path.read_text(encoding="utf-8"))
        if lines:
            offenders[path.name] = lines
    assert offenders == {}, (
        "a test module builds an engine path as `REPO_ROOT / \"scripts\"`, which "
        "is only correct while `paths.engines` is `scripts`. Use ENGINE_DIR. "
        f"Offenders: {offenders}"
    )
