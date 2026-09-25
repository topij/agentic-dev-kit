from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.canonical import digest  # noqa: E402
from triage.model import TriageError  # noqa: E402
from triage.providers import GitHubForge, GitHubIssues  # noqa: E402

DESTINATION = {"backend": "github-issues", "host": "github.com", "repository": "owner/repo", "project": "owner/repo"}
MARKER = "<!-- triage-payload:session:TRI-01:" + "a" * 64 + " -->"


class Runner:
    def __init__(self, responses: list[tuple[int, object]]) -> None:
        self.responses = list(responses)
        self.argv: list[list[str]] = []

    def __call__(self, argv: list[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        self.argv.append(argv)
        code, body = self.responses.pop(0)
        stdout = body if isinstance(body, str) else json.dumps(body)
        return subprocess.CompletedProcess(argv, code, stdout=stdout, stderr="failure" if code else "")


def issue(number: int, payload: dict, *, pull_request: bool = False) -> dict:
    value = {
        "number": number,
        "title": payload["title"],
        "body": payload["body"],
        "labels": [{"name": label} for label in payload["labels"]],
        "repository_url": "https://api.github.com/repos/owner/repo",
    }
    if pull_request:
        value["pull_request"] = {"url": "example"}
    return value


def test_search_paginates_full_issue_listing_and_filters_pull_requests() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    first_page = [{"number": number, "body": "unrelated"} for number in range(100)]
    second_page = [{"number": 101, "body": payload["body"]}, {"number": 102, "body": payload["body"], "pull_request": {}}]
    runner = Runner([(0, first_page), (0, second_page), (0, issue(101, payload))])
    observed = GitHubIssues(runner).search(DESTINATION, MARKER)
    assert observed == [{"identifier": "101", "payload": payload, "payload_digest": digest(payload), "marker": MARKER, "destination": DESTINATION}]
    assert "page=1" in runner.argv[0][-1]
    assert "page=2" in runner.argv[1][-1]


def test_create_refuses_success_identifier_that_differs_from_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (0, {"number": 99}),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    observed = GitHubIssues(runner).create(DESTINATION, payload)
    assert observed.status == "ambiguous"


def test_failed_response_can_verify_only_through_exact_independent_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (1, "gateway failed"),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    observed = GitHubIssues(runner).create(DESTINATION, payload)
    assert observed.status == "verified"
    assert observed.verified_route == "failed-response-then-exact-read-back"


def test_destination_is_derived_from_authoritative_issue_repository() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": []}
    foreign = issue(101, payload)
    foreign["repository_url"] = "https://api.github.com/repos/other/repo"
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, foreign)])
    with pytest.raises(TriageError, match="destination"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_destination_host_is_bound_to_authoritative_issue_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": []}
    foreign = issue(101, payload)
    foreign["repository_url"] = "https://github.example.invalid/repos/owner/repo"
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, foreign)])
    with pytest.raises(TriageError, match="destination"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_duplicate_marker_is_ambiguous_not_authoritative_absence() -> None:
    runner = Runner([(0, [{"number": 101, "body": MARKER + "\n" + MARKER}])])
    with pytest.raises(TriageError, match="multiplicity"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_malformed_list_item_invalidates_absence_readback() -> None:
    runner = Runner([(0, [None])])
    with pytest.raises(TriageError, match="malformed"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_unsorted_authoritative_labels_reconcile_to_canonical_payload_order() -> None:
    payload = {
        "title": "title",
        "body": "body\n" + MARKER,
        "project": "owner/repo",
        "labels": ["alpha", "zeta"],
    }
    read_back = issue(101, payload)
    read_back["labels"] = [{"name": "zeta"}, {"name": "alpha"}]
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, read_back)])
    observed = GitHubIssues(runner).search(DESTINATION, MARKER)
    assert observed[0]["payload"] == payload
    assert observed[0]["payload_digest"] == digest(payload)


@pytest.mark.parametrize(
    "labels",
    [
        {"name": "bug"},
        [{"name": "bug"}, {"color": "red"}],
        [{"name": "bug"}, {"name": "bug"}],
    ],
)
def test_malformed_or_ambiguous_label_readback_is_held(labels: object) -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    read_back = issue(101, payload)
    read_back["labels"] = labels
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, read_back)])
    with pytest.raises(TriageError, match="label read-back"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


@pytest.mark.parametrize("backend", [None, "linear", "jira"])
def test_github_adapter_refuses_foreign_tracker_backend_before_provider_call(backend: str | None) -> None:
    runner = Runner([])
    with pytest.raises(TriageError, match="unsupported tracker backend"):
        GitHubIssues(runner).search({**DESTINATION, "backend": backend}, MARKER)
    assert runner.argv == []


def pr_view(head: str) -> dict:
    return {
        "url": "https://github.com/owner/repo/pull/17",
        "baseRefName": "main",
        "headRefName": "chore/triage",
        "headRefOid": head,
        "isDraft": False,
        "mergedAt": None,
        "files": [{"path": "docs/kit-friction-log.md"}],
    }


def watch_intent(head: str) -> dict:
    return {
        "host": "github.com",
        "repository": "owner/repo",
        "pr": "https://github.com/owner/repo/pull/17",
        "base_branch": "main",
        "head": head,
        "tree": "b" * 40,
    }


@pytest.mark.parametrize(
    "receipt",
    [
        {"converged": False, "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
        {"converged": True, "head": "c" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
        {"converged": True, "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": False}},
        {"converged": True, "mergeable": False, "done": False, "merge_blockers": ["review pending"], "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
    ],
)
def test_pr_watch_exit_zero_without_complete_exact_head_review_is_unsettled(tmp_path: Path, receipt: dict) -> None:
    head = "a" * 40
    runner = Runner([(0, ""), (0, receipt), (0, pr_view(head))])
    observed = GitHubForge(tmp_path, runner, pr_watch=tmp_path / "configured-pr-watch.py").perform("pr-watch", watch_intent(head))
    assert observed.status == "unsettled"
    assert str(tmp_path / "configured-pr-watch.py") in runner.argv[0]
    assert runner.argv[0][-2:] == ["17", "--assert-ready"]
    assert runner.argv[1][-2:] == ["17", "--json"]


def test_pr_watch_moved_head_is_ambiguous(tmp_path: Path) -> None:
    head = "a" * 40
    receipt = {"converged": True, "head": head, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}}
    runner = Runner([(0, ""), (0, receipt), (0, pr_view("c" * 40))])
    assert GitHubForge(tmp_path, runner).perform("pr-watch", watch_intent(head)).status == "ambiguous"


def test_pr_watch_terminal_native_receipt_verifies_exact_head(tmp_path: Path) -> None:
    head = "a" * 40
    receipt = {
        "converged": True,
        "mergeable": True,
        "done": True,
        "merge_blockers": [],
        "head": head,
        "url": "https://github.com/owner/repo/pull/17",
        "truncated_reads": [],
        "review_evidence": {"valid": True},
    }
    runner = Runner([(0, ""), (0, receipt), (0, pr_view(head))])
    observed = GitHubForge(tmp_path, runner).perform("pr-watch", watch_intent(head))
    assert observed.status == "verified"
    assert observed.read_back["reviewed_head"] == head


def test_pr_watch_transport_matches_numeric_shared_cli_contract(tmp_path: Path) -> None:
    parser_probe = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "pr_watch.py"), "https://github.com/owner/repo/pull/17", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert parser_probe.returncode == 2
    assert "invalid int value" in parser_probe.stderr

    with pytest.raises(TriageError, match="forge destination"):
        GitHubForge(tmp_path, Runner([])).perform(
            "pr-watch",
            {**watch_intent("a" * 40), "pr": "https://example.com/owner/repo/pull/17"},
        )


def test_malformed_successful_pull_request_json_is_a_canonical_provider_hold(tmp_path: Path) -> None:
    intent = {
        "host": "github.com",
        "repository": "owner/repo",
        "pr": "https://github.com/owner/repo/pull/17",
        "base": "main",
        "reviewed_head": "a" * 40,
    }
    with pytest.raises(TriageError, match="invalid JSON"):
        GitHubForge(tmp_path, Runner([(0, "not-json")])).perform("merge-read-back", intent)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize("leftover", [None, "local-branch", "worktree", "remote-branch"])
def test_branch_create_absence_reads_the_real_repository(tmp_path: Path, leftover: str | None) -> None:
    """Each thing a failed branch-create could have left is read from git and the filesystem."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    branch, worktree = "chore/triage-2099-01-01", tmp_path / "sweep"
    if leftover == "local-branch":
        _git(repo, "branch", branch)
    elif leftover == "worktree":
        worktree.mkdir()
    elif leftover == "remote-branch":
        _git(repo, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
    absence = GitHubForge(repo).authority("branch-create-absent", {"branch": branch, "worktree": str(worktree)})
    expected = {"local_branch_absent": True, "worktree_absent": True, "remote_branch_absent": True}
    if leftover is not None:
        expected[{"local-branch": "local_branch_absent", "worktree": "worktree_absent", "remote-branch": "remote_branch_absent"}[leftover]] = False
    assert absence == expected


def test_branch_create_absence_holds_when_the_remote_cannot_be_read(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "remote", "add", "origin", str(tmp_path / "missing.git"))
    with pytest.raises(TriageError, match="remote branch read-back failed"):
        GitHubForge(repo).authority("branch-create-absent", {"branch": "b", "worktree": str(tmp_path / "w")})


def test_branch_create_absence_holds_when_local_refs_cannot_be_read(tmp_path: Path) -> None:
    """An unreadable ref store is not proof the branch is absent."""
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "branch", "chore/triage-2099-01-01")
    _git(repo, "pack-refs", "--all")
    (repo / ".git/packed-refs").write_text("garbage that is not a packed ref\n", encoding="utf-8")
    with pytest.raises(TriageError, match="local branch read-back failed"):
        GitHubForge(repo).authority("branch-create-absent", {"branch": "chore/triage-2099-01-01", "worktree": str(tmp_path / "w")})
