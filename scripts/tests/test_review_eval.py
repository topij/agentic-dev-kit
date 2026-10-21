"""The reviewer eval runner (#1156), driven by stub lenses so no model is called."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
ENGINE = ENGINE_DIR / "review_eval.py"
DOCTRINE = "docs/agentic-dev-kit/fallback-review-panel.md"
sys.path.insert(0, str(ENGINE_DIR))

import review_eval  # noqa: E402


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def _commit(root: Path, name: str, text: str) -> str:
    (root / name).write_text(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", name)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> dict:
    """A fixture repository: a bug commit, a clean commit, and the real doctrine."""
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "docs/agentic-dev-kit").mkdir(parents=True)
    (root / "scripts/lib").mkdir(parents=True)
    (root / "scripts/check_record_prose.py").write_text(
        '# /// script\n# requires-python = ">=3.12"\n# dependencies = []\n# ///\n')
    (root / "scripts/lib/kitconfig.py").write_text("# fixture parser\n")
    (root / DOCTRINE).write_text((REPO_ROOT / DOCTRINE).read_text(encoding="utf-8"))
    scratch = tmp_path / "scratch-root"
    scratch.mkdir()
    (root / "config/dev-model.yaml").write_text(
        f"scratch:\n  roots: [{str(scratch)!r}]\n  grace_window: 24h\n  worktree_repos: [{str(root)!r}]\n"
        "vcs:\n  protected_branch: main\n"
        "review:\n  fallback_panel:\n    lenses:\n"
        "      - name: adversarial\n        focus: prove it wrong\n"
        "      - name: correctness\n        focus: ask what it says\n"
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "remote.origin.url", "https://github.com/o/r.git")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    base = _git(root, "rev-parse", "HEAD")
    bug = _commit(root, "bug.py", "def f(x):\n    return x / 0\n    # unreachable\n")
    clean = _commit(root, "notes.md", "a note\n")
    cases = tmp_path / "cases.yaml"
    cases.write_text(
        "schema: review-eval-cases-v1\n"
        "bug_cases:\n"
        f"  - id: divide-by-zero\n    base: {base}\n    head: {bug}\n    source: \"#1\"\n"
        "    findings:\n      - path: bug.py\n        lines: [2, 2]\n        description: divides by zero\n"
        "    confirmed: \"fixture\"\n"
        f"  - id: unconfirmed-case\n    base: {base}\n    head: {bug}\n    source: \"#2\"\n"
        "    findings:\n      - path: bug.py\n        lines: [3, 3]\n        description: dead code\n"
        "    confirmed: \"\"\n"
        "clean_cases:\n"
        f"  - id: a-clean-note\n    base: {bug}\n    head: {clean}\n    source: \"#3\"\n    confirmed: \"\"\n"
    )
    return {"root": root, "cases": cases, "scratch": scratch, "base": base, "bug": bug, "clean": clean}


def _stub(tmp_path: Path, body: str, name: str = "lens.py") -> str:
    """A lens that records where it ran and what it was told, then prints ``body``."""
    path = tmp_path / name
    log = tmp_path / f"{name}.log"
    path.write_text(
        "import subprocess, sys\n"
        "prompt = sys.stdin.read()\n"
        "head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()\n"
        f"open({str(log)!r}, 'a').write(head + ' ' + str('## Your lens' in prompt or 'adversarial' in prompt) + '\\n')\n"
        f"sys.stdout.write({body!r})\n"
    )
    return f"{sys.executable} {path}"


def _run(repo: dict, command: str, *extra: str, out: Path | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(ENGINE), "--root", str(repo["root"]), "--cases", str(repo["cases"]),
            "--runtime", "claude", "--lens-command", command, "--scratch-root", str(repo["scratch"]), *extra]
    if out is not None:
        args += ["--out", str(out)]
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_a_cited_bug_is_a_hit_and_clean_findings_are_candidate_false_alarms(repo, tmp_path) -> None:
    command = _stub(tmp_path, "F1 HIGH: bug.py:2 divides by zero\nF2 LOW: notes.md:1 typo\n")
    out = tmp_path / "out"
    proc = _run(repo, command, "--lens", "adversarial", out=out)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert json.loads((out / "result.json").read_text()) == result
    assert result["schema"] == "review-eval-result-v1" and result["runtime"] == "claude"
    assert result["lens_command"] == command
    assert result["kit_revision"] == repo["clean"]
    by_case = {r["case"]: r for r in result["results"]}
    assert by_case["divide-by-zero"]["hit"] is True
    assert by_case["divide-by-zero"]["matched_citations"] == [{"finding": 0, "path": "bug.py", "lines": [2, 2]}]
    assert by_case["unconfirmed-case"]["hit"] is False
    assert by_case["a-clean-note"]["candidate_false_alarms"] == 2
    assert result["summary"] == {"adversarial": {
        "confirmed_bug_cases": 1, "confirmed_hits": 1, "unconfirmed_bug_cases": 1,
        "unconfirmed_hits": 0, "clean_cases": 1, "candidate_false_alarms": 2}}
    assert (out / "divide-by-zero-adversarial.md").read_text().startswith("F1 HIGH")
    # The lens ran in a tree at each case head, with the rendered prompt on stdin.
    log = (tmp_path / "lens.py.log").read_text().split("\n")
    assert [line.split()[0] for line in log if line] == [repo["bug"], repo["bug"], repo["clean"]]
    assert all(line.endswith("True") for line in log if line)


def test_every_round_is_retired_and_every_tree_removed(repo, tmp_path) -> None:
    proc = _run(repo, _stub(tmp_path, "nothing found\n"))
    assert proc.returncode == 0, proc.stderr
    assert list(repo["scratch"].iterdir()) == []
    assert _git(repo["root"], "worktree", "list").count("\n") == 0
    summary = json.loads(proc.stdout)["summary"]
    assert set(summary) == {"adversarial", "correctness"}
    assert summary["correctness"]["confirmed_hits"] == 0


def test_a_failing_lens_command_is_exit_1_and_still_cleans_up(repo, tmp_path) -> None:
    script = tmp_path / "fail.py"
    script.write_text("import sys\nsys.stdin.read()\nsys.exit(3)\n")
    proc = _run(repo, f"{sys.executable} {script}", "--case", "divide-by-zero", "--lens", "adversarial")
    assert proc.returncode == 1
    assert "exited 3" in proc.stderr
    assert list(repo["scratch"].iterdir()) == []
    assert _git(repo["root"], "worktree", "list").count("\n") == 0


@pytest.mark.parametrize("edit, message", [
    (lambda t, r: t.replace(r["bug"], r["bug"][:12], 1), "full 40-hex sha"),
    (lambda t, r: t.replace(r["bug"], "f" * 40, 1), "is not a commit"),
    (lambda t, r: t.replace("id: unconfirmed-case", "id: divide-by-zero"), "unique"),
    (lambda t, r: t.replace("lines: [2, 2]", "lines: [3, 2]"), "start <= end"),
    (lambda t, r: t.replace("review-eval-cases-v1", "v0"), "schema"),
])
def test_a_malformed_case_file_is_refused(repo, tmp_path, edit, message) -> None:
    repo["cases"].write_text(edit(repo["cases"].read_text(), repo))
    proc = _run(repo, _stub(tmp_path, ""))
    assert proc.returncode == 2 and message in proc.stderr
    assert list(repo["scratch"].iterdir()) == []


def test_unknown_lenses_and_cases_are_refused(repo, tmp_path) -> None:
    assert "security" in _run(repo, _stub(tmp_path, ""), "--lens", "security").stderr
    assert "no such case" in _run(repo, _stub(tmp_path, ""), "--case", "nope").stderr


@pytest.mark.parametrize("report, hit", [
    ("see bug.py:1-2", True),
    ("see src/bug.py:2", True),
    ("see bug.py:3", False),
    ("see other.py:2", False),
    ("bug.py line 2, no citation", False),
])
def test_a_hit_needs_an_overlapping_citation(report, hit) -> None:
    case = {"findings": [{"path": "bug.py", "lines": [2, 2]}]}
    assert review_eval.score_bug(report, case)["hit"] is hit


def test_the_shipped_case_set_names_the_issues_the_ticket_requires() -> None:
    """#1156's acceptance: at least #19, #23 and #95, each with a confirmation."""
    data = review_eval.load_config(REPO_ROOT / review_eval.CASES)
    sources = {case["source"]: case for case in data["bug_cases"]}
    for issue in ("#19", "#23", "#95"):
        assert issue in sources and sources[issue]["confirmed"].strip(), issue
        for finding in sources[issue]["findings"]:
            assert finding["path"] and finding["lines"][0] <= finding["lines"][1]
