from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
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
    assert uv_calls[1].endswith("8 --json")
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
    for name in ("session-start", "wrap-up", "pr-watch", "parallel"):
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
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
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
def test_migration_is_idempotent(tmp_path: Path, shape: str) -> None:
    """Re-running `./init.sh` is the documented upgrade path, so a second run
    must be a no-op — not a second copy of every key it added."""
    path, _ = _run_init(tmp_path, shape, _MIGRATION_SHAPES[shape])
    once = path.read_text(encoding="utf-8")

    subprocess.run(
        ["sh", "init.sh"], cwd=path.parent.parent, check=True, capture_output=True, text=True
    )

    assert path.read_text(encoding="utf-8") == once


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
def test_the_instruction_stays_quiet_when_there_is_nothing_to_add(
    tmp_path: Path, case: str, config: str
) -> None:
    _, proc = _run_init(tmp_path, f"quiet_{case}", config)

    assert "ACTION NEEDED" not in proc.stderr


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


def test_a_failed_write_prints_no_past_tense_success_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """stdout must not claim the move happened when the write failed.

    The report used to be printed BEFORE the write, so a read-only handoff
    emitted `moved 2 block(s) ... (46 -> 33 plan lines)` and then an error — and
    `wrap-up.md` tells the operator to report the line count it sees. That is a
    figure for a file that was never touched.
    """
    archive = _load_module("archive_failed_write", ENGINE_DIR / "archive_plan_sessions.py")
    plan_dir = tmp_path / "live"
    plan_dir.mkdir()
    plan = plan_dir / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_text(encoding="utf-8")
    # The DIRECTORY, not the file: `atomic_write` replaces via a sibling temp, and
    # rename honours the directory's permissions rather than the target file's.
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


def test_a_failed_history_write_rolls_the_handoff_back(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The rollback branch itself — asserted in two docstrings, entered by no test.

    The existing failed-write test chmods the *plan*, so the FIRST write fails and
    the rollback is never reached; its `plan == original` assertion passes
    trivially. Making the *history* write fail is what exercises the branch that
    exists to stop a move from dropping the swept blocks: handoff already
    truncated, history write refused, blocks recoverable from neither.
    """
    archive = _load_module("archive_rollback", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    hist_dir = tmp_path / "hist"
    hist_dir.mkdir()
    history = hist_dir / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original_plan = plan.read_text(encoding="utf-8")
    original_history = history.read_text(encoding="utf-8")
    # NOTE: chmod on the FILE no longer blocks the write. `atomic_write` creates a
    # sibling temp and `os.replace`s it, and rename cares about the DIRECTORY's
    # permissions, not the target file's. That is a deliberate behaviour change
    # from this commit — the data-loss fix is worth it — so block the directory,
    # which is what genuinely fails now.
    hist_dir.chmod(0o555)
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        hist_dir.chmod(0o755)

    assert result == 2
    captured = capsys.readouterr()
    assert "write failed" in captured.err
    assert "moved" not in captured.out
    # The whole point: the handoff is back to its original content, so the blocks
    # that were about to move still exist somewhere.
    assert plan.read_text(encoding="utf-8") == original_plan
    assert "## Earlier session — First" in plan.read_text(encoding="utf-8")
    assert history.read_text(encoding="utf-8") == original_history


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


def _atomic_target(path: Path) -> str:
    """Map `.handoff.md.archive-tmp` back to `handoff.md`.

    `archive_plan_sessions.atomic_write` writes a sibling temp file and
    `os.replace`s it, so a `Path.write_text` spy sees the temp name, not the
    target. Tests that care about WHICH document is being written have to look
    through that.
    """
    name = path.name
    if name.startswith(".") and name.endswith(".archive-tmp"):
        return name[1:-len(".archive-tmp")]
    return name

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


def test_the_plan_is_written_before_the_history_doc(tmp_path: Path) -> None:
    """The write ORDER, not merely the end state.

    `test_a_failed_history_write_rolls_the_handoff_back` asserts the plan ends up
    unchanged — which passes trivially against a variant that writes history
    first and has no rollback at all, because then the plan is never written. That
    is the same "passes trivially" weakness it was written to replace, one axis
    over. Under that variant a failing plan write leaves the blocks in BOTH files
    and a re-run appends them to history twice.

    So record the order directly.
    """
    archive = _load_module("archive_write_order", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    order: list[str] = []
    real_write = Path.write_text

    def spy(self: Path, data: str, *args: object, **kwargs: object) -> int:
        target = _atomic_target(self)
        if target == plan.name:
            order.append("plan")
        elif target == history.name:
            order.append("history")
        return real_write(self, data, *args, **kwargs)

    Path.write_text = spy  # type: ignore[method-assign]
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        Path.write_text = real_write  # type: ignore[method-assign]

    assert result == 0
    assert order == ["plan", "history"], (
        f"the plan must be written first so a history failure can roll it back; got {order}"
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When the rollback itself fails, the plan IS truncated — say so.

    The handler added for this was pinned by nothing: reverting it to the bare
    `write_text(original_plan); raise` survived the suite. "no changes applied"
    would then be printed while the blocks sit in neither file.
    """
    archive = _load_module("archive_bad_rollback", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)

    real_write = Path.write_text
    calls: list[str] = []

    def spy(self: Path, data: str, *args: object, **kwargs: object) -> int:
        target = _atomic_target(self)
        calls.append(target)
        if target == history.name:
            raise OSError(28, "No space left on device")
        if target == plan.name and calls.count(plan.name) == 2:  # the rollback
            raise OSError(28, "No space left on device")
        return real_write(self, data, *args, **kwargs)

    Path.write_text = spy  # type: ignore[method-assign]
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        Path.write_text = real_write  # type: ignore[method-assign]

    assert result == 2
    err = capsys.readouterr().err
    assert "no changes applied" not in err, "the blocks are in neither doc — don't claim otherwise"
    assert "ALREADY SWEPT" in err
    assert "Restore it from git" in err
    # Both causes, not just the last one: a full disk fails twice, and the first
    # failure is usually what explains the second.
    assert err.count("No space left on device") == 2, err


def test_a_failed_write_leaves_the_handoff_byte_identical(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """"no changes applied" must be TRUE, not aspirational.

    `Path.write_text` opens mode 'w', which truncates before the first byte is
    written — so a failure between the open and the flush (ENOSPC, EIO, quota)
    left the handoff empty or half-written while the handler printed "no changes
    applied". Demonstrated on a real full filesystem: a 26,807-byte living
    handoff became 0 bytes and the tool reported that nothing had happened, at
    which point `wrap-up.md` routes the operator straight on to the commit step.

    `atomic_write` writes a sibling temp file and `os.replace`s it, so any
    failure before the replace leaves the original untouched.
    """
    archive = _load_module("archive_atomic", ENGINE_DIR / "archive_plan_sessions.py")
    plan = tmp_path / "handoff.md"
    history = tmp_path / "handoff-history.md"
    _write_four_block_plan(plan, history)
    original = plan.read_bytes()

    real_write = Path.write_text

    def spy(self: Path, data: str, *args: object, **kwargs: object) -> int:
        # Fail the way a full disk does: during the write, after the open.
        if self.name.startswith(".handoff.md"):
            real_write(self, data[: len(data) // 2], *args, **kwargs)
            raise OSError(28, "No space left on device")
        return real_write(self, data, *args, **kwargs)

    Path.write_text = spy  # type: ignore[method-assign]
    try:
        result = archive.main(
            ["--keep", "2", "--plan", str(plan), "--history", str(history)]
        )
    finally:
        Path.write_text = real_write  # type: ignore[method-assign]

    assert result == 2
    assert "no changes applied" in capsys.readouterr().err
    assert plan.read_bytes() == original, "the handoff was modified despite the failure"
    # And no debris left behind for the next run to trip over.
    assert not list(tmp_path.glob(".*archive-tmp")), "temp file survived the failure"
