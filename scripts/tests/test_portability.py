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


def test_pr_watch_root_fallback_handles_the_vendored_layout(tmp_path: Path) -> None:
    """No `.git`: the old `start.parent.parent` returned `<repo>/scripts`."""
    repo = tmp_path / "project"
    nested = repo / "scripts" / "devkit" / "pr_watch.py"
    nested.parent.mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    pr_watch = _load_module("pr_watch_fb", ENGINE_DIR / "pr_watch.py")

    assert pr_watch._find_repo_root(nested) == repo


def test_pr_watch_root_fallback_does_not_escape_into_a_parent_project(
    tmp_path: Path,
) -> None:
    """REPO_ROOT feeds every `gh`/`git` subprocess `cwd=` and the state root.

    Escaping would point a merge-gate engine at a different repository, so the
    bound matters more here than anywhere else it is applied.
    """
    outer = tmp_path / "outer"
    (outer / "config").mkdir(parents=True)
    (outer / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    release = outer / "releases" / "proj-1.2.3"
    nested = release / "scripts" / "pr_watch.py"
    nested.parent.mkdir(parents=True)
    pr_watch = _load_module("pr_watch_esc", ENGINE_DIR / "pr_watch.py")

    resolved = pr_watch._find_repo_root(nested)
    assert resolved != outer, "escaped into the parent project"
    assert resolved == release


def test_devmodel_config_root_fallback_handles_the_vendored_layout(tmp_path: Path) -> None:
    """`_repo_root()` reads `__file__`, so the module must be copied into place."""
    repo = tmp_path / "project"
    lib = repo / "scripts" / "devkit" / "lib"
    lib.mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "config" / "dev-model.yaml").write_text("kit:\n  version: 2\n", encoding="utf-8")
    target = lib / "devmodel_config.py"
    target.write_bytes((ENGINE_DIR / "lib" / "devmodel_config.py").read_bytes())

    module = _load_module("devmodel_config_fb", target)
    assert module._repo_root() == repo


def test_engines_avoid_datetime_utc_alias() -> None:
    """`datetime.UTC` / `from datetime import UTC` need Python 3.11+.

    `ruff.toml` ignores UP017 so the autofixer cannot introduce this, but the
    ignore is a comment — nothing stopped it being typed by hand, and the
    regression it guards against was silent (an ImportError at module load, on
    an interpreter CI never exercises).

    Scope is ENGINES, not tests: tests only ever run under the pinned CI
    interpreter, while engines get invoked as a bare `python3 <engine>` by git
    hooks, cron and CI steps on whatever interpreter is present. The six
    modules under lib/ carry no PEP 723 header at all, so they inherit their
    caller's interpreter with nothing to negotiate a newer one.
    """
    offenders: list[str] = []
    for path in sorted(ENGINE_DIR.rglob("*.py")):
        rel = path.relative_to(ENGINE_DIR)
        if rel.parts[0] == "tests" or "tests" in rel.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            code = line.split("#", 1)[0]
            if re.search(r"\bdatetime\.UTC\b", code) or re.search(
                r"^\s*from\s+datetime\s+import\s+.*\bUTC\b", code
            ):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "use `timezone.utc` — `datetime.UTC` raises ImportError below 3.11:\n"
        + "\n".join(offenders)
    )
