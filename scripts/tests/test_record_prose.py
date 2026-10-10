"""Exercise the narrative preflight against independent committed Git fixtures."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from _repo_layout import engine_dir
from conftest import require_kit_paths

ENGINE = engine_dir(Path(__file__)) / "check_record_prose.py"
LOCAL_REF = "#7"
FOREIGN_REF = "other/repo#7"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


def save(root: Path, path: str, text: str) -> None:
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def commit(root: Path, message: str = "narrative update") -> str:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@example.com")
    save(root, "config/dev-model.yaml", """paths:
  handoff: docs/plan.md
  handoff_history: docs/history.md
  friction_log: docs/inbox.md
  friction_log_archive: docs/archive.md
doc_budgets:
  - path: docs/plan.md
    budget: 20
"""
    )
    save(root, "docs/plan.md", "# Plan\n\nEarlier record.\n")
    save(root, "docs/history.md", "# History\n")
    save(root, "docs/target with space.md", "# Target\n")
    return root, commit(root, "baseline")


def run(repo: tuple[Path, str], head: str, *extra: str) -> tuple[int, dict]:
    require_kit_paths("scripts/check_record_prose.py")
    root, base = repo
    result = subprocess.run(
        ["uv", "run", str(ENGINE), "--root", str(root), "--base", base,
         "--head", head, "--json", *extra],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=90,
    )
    assert result.stdout, result.stderr
    return result.returncode, json.loads(result.stdout)


def test_committed_snapshot_ignores_dirty_files_and_has_no_write(repo):
    root, base = repo
    save(root, "docs/plan.md", f"# Plan\n\n`make test` at `{base}` on 2026-10-10 printed a result.\n\n"
         "[Target](<target with space.md>) and [external](https://example.com).\n\n"
         "`[example](missing.md)`\n")
    head = commit(root)
    save(root, "docs/plan.md", "dirty working copy\n" * 100)
    before = git(root, "status", "--porcelain=v1")
    code, report = run(repo, head)
    assert code == 0, report
    assert report["status"] == "passed"
    assert report["stamps"][0]["revision"] == base
    assert report["stamps"][0]["names_head"] is False
    assert report["limits"]
    assert git(root, "status", "--porcelain=v1") == before
    assert (root / "docs/plan.md").read_text() == "dirty working copy\n" * 100


@pytest.mark.parametrize("text,kind", [
    ("line\n" * 21, "budgets"),
    ("[Missing](missing.md)\n", "links"),
    (f"Not `fixes {LOCAL_REF}`.\n", "closing-keywords"),
    (f"fixes\n{LOCAL_REF}\n", "closing-keywords"),
    ("`make test` at `HEAD` on 2026-10-10 printed a result.\n", "stamps"),
    ("`make test` at `abcdef0` on 2026-02-30 printed a result.\n", "stamps"),
])
def test_each_check_rejects_its_own_hostile_input(repo, text, kind):
    root, _ = repo
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert kind in [item["check"] for item in report["findings"]]


def test_reference_definition_edit_rechecks_existing_link(repo):
    root, _ = repo
    save(root, "docs/plan.md", "[Link][destination]\n\n[destination]: <target with space.md>\n")
    base = commit(root)
    save(root, "docs/plan.md", "[Link][destination]\n\n[destination]: missing.md\n")
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"


def test_commit_message_closure_requires_exact_intent(repo):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    head = commit(root, f"fixes {LOCAL_REF}\n\nresolves {FOREIGN_REF}")
    code, report = run(repo, head, "--allow-close", "#7")
    assert code == 1, report
    assert report["findings"][0]["source"] == f"commit:{head}"
    assert "other/repo#7" in report["findings"][0]["detail"]
    code, report = run(repo, head, "--allow-close", "#7", "--allow-close", "other/repo#7")
    assert code == 0, report


@pytest.mark.parametrize("text", [
    "[Outside](../../outside.md)\n",
    "[Machine file](/private/tmp/file.md)\n",
    "`make test` at `abcdef0` on 2026-10-10 printed a result.\n",
])
def test_unavailable_inputs_do_not_become_passing_checks(repo, text):
    root, _ = repo
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 2, report
    assert report["status"] == "unavailable"
    assert report["unavailable"]


def test_multiline_stamp_with_directory_is_observed(repo):
    root, base = repo
    save(root, "docs/plan.md", f"`make test` at `{base}`, in `/project`,\non 2026-10-10 printed a result.\n")
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["stamps"][0]["revision"] == base


@pytest.mark.parametrize("extra", [("--root", ""), ("--base", "HEAD"), ("--allow-close", "")])
def test_invalid_cli_inputs_are_explicitly_unavailable(repo, extra):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    code, report = run(repo, commit(root), *extra)
    assert code == 2, report
    assert report["status"] == "unavailable"
    assert report["error"]


def test_mixed_changes_supply_no_narrative_preflight_claim(repo):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    save(root, "code.py", "pass\n")
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["status"] == "not-applicable"


def test_missing_budgeted_candidate_is_unavailable(repo):
    root, _ = repo
    (root / "docs/plan.md").unlink()
    code, report = run(repo, commit(root))
    assert code == 2, report
    assert "absent" in report["error"]


def test_local_destination_is_literal_not_a_git_pathspec(repo):
    root, _ = repo
    save(root, "docs/plan.md", "[Target](target*.md)\n")
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"
