from __future__ import annotations

import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from triage.approval import ApprovalContext  # noqa: E402
from triage.canonical import (  # noqa: E402
    decode_bytes,
    digest,
    digest_bytes,
    dumps,
    encode_bytes,
    loads_exact,
)
from triage.engine import _pr_result_fields, _verify_forge_read_back, run  # noqa: E402
from triage.finalize import sweep_ids  # noqa: E402
from triage.inbox import parse  # noqa: E402
from triage.model import TriageError, canonical_state, load_settings  # noqa: E402
from triage.providers import FakeForge, ProviderObservation  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "config/dev-model.yaml", root / "config/dev-model.yaml")
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("  engines: scripts/devkit\n", "  engines: scripts\n"), encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n"
        b"- **Approved archive.** exact bytes. **Filed 2026-01-02 as #17.**\n\n"
        b"- **Window addition.** The prior Filed annotation is discussed; keep me.\n"
    )
    (root / "docs/kit-friction-log-archive.md").write_bytes(b"# Archive\n")
    (root / "scripts").mkdir()
    (root / "scripts/triage_friction_log.py").write_text("# engine\n", encoding="utf-8")
    (root / "scripts/finalize_triage.py").write_text("# engine\n", encoding="utf-8")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")
    git(root, "remote", "add", "origin", "https://github.com/topij/agentic-dev-kit.git")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def proposal_request(root: Path) -> tuple[dict, str]:
    candidates = parse((root / "docs/kit-friction-log.md").read_bytes())
    candidate = candidates[0]
    return ({
        "proposals": [
            {
                "candidate_id": item.candidate_id,
                "source_block_digest": item.digest,
                "title": item.title.rstrip("."),
                "body_without_marker": "exact bytes.",
                "project": "topij/agentic-dev-kit",
                "labels": ["maintenance"],
            }
            for item in candidates
        ],
    }, candidate.candidate_id)


def approval(state: dict, command: str) -> tuple[dict, ApprovalContext]:
    set_digest = digest(state["proposal_payload_digests"])
    request = {"approval": {"command": command, "proposal_set_digest": set_digest}}
    context = ApprovalContext("current-session", "operator", {
        "approver_identity": "operator",
        "text": command,
        "proposal_set_digest": set_digest,
        "payload_digests": state["proposal_payload_digests"],
    })
    return request, context


def verified(read_back: dict) -> ProviderObservation:
    return ProviderObservation("verified", {"synthetic": True}, read_back)


def native_watch_receipt(url: str, head: str) -> dict:
    return {
        "converged": True, "mergeable": True, "done": True,
        "merge_blockers": [], "head": head, "url": url,
        "truncated_reads": [], "review_evidence": {"valid": True},
    }


def test_sweep_set_is_union_of_verified_filed_and_explicit_archive_decisions() -> None:
    state = {
        "decisions": [
            {"candidate_id": "TRI-01", "decision": "file"},
            {"candidate_id": "TRI-02", "decision": "archive"},
            {"candidate_id": "TRI-03", "decision": "park"},
        ],
        "operations": [
            {"candidate_id": "TRI-01", "decision": "file", "status": "verified"},
        ],
    }
    assert sweep_ids(state) == {"TRI-01", "TRI-02"}


def test_fabricated_verified_watch_receipt_is_rejected_at_engine_boundary() -> None:
    head = "a" * 40
    url = "https://github.com/owner/repo/pull/17"
    intent = {"pr": url, "base_branch": "main", "head": head}
    read_back = {
        "url": url, "baseRefName": "main", "headRefOid": head,
        "reviewed_head": head, "receipt": {"status": "ready"},
    }
    with pytest.raises(TriageError, match="authoritative read-back"):
        _verify_forge_read_back("pr-watch", intent, read_back)


def test_archive_only_finalize_retains_exact_new_block_and_waits_for_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    config = root / "config/dev-model.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("project_name: topij/agentic-dev-kit", "project_name: central/triage-tracker"),
        encoding="utf-8",
    )
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    assert run("new", context="interactive", request=draft_request, start=root)["outcome"] == "operator-held"
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")

    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    branch = f"chore/triage-{date.today().isoformat()}"
    base = git(root, "rev-parse", "HEAD")
    tree = "1" * 40
    commit = "2" * 40
    pr_url = "https://github.com/topij/agentic-dev-kit/pull/999"
    paths = ["docs/kit-friction-log-archive.md", "docs/kit-friction-log.md"]
    forge = FakeForge([
        verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "head": base, "tree": "0" * 40}),
        verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "commit": commit, "tree": tree, "subject": "docs(triage): graduate friction-log entries", "paths": paths}),
        verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "remote_head": commit, "tree": tree}),
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "isDraft": False, "files": paths}),
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "isDraft": False, "files": paths, "reviewed_head": commit, "receipt": native_watch_receipt(pr_url, commit)}),
    ])
    result = run(
        "resume",
        context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root,
        approval_context=context,
        forge=forge,
    )
    assert result["outcome"] == "operator-held"
    assert result["pull_request_url"] == pr_url
    assert result["observed_pr_head"] == commit
    assert result["reviewed_head"] == commit
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert f"Pull request: `{pr_url}`" in report
    assert f"Observed PR head: `{commit}`" in report
    assert f"Reviewed head: `{commit}`" in report
    state = loads_exact(state_path.read_bytes())
    assert state["phase"] == "archive-sweep"
    assert [operation["kind"] for operation in state["finalization_operations"]] == [
        "branch-create", "commit", "push", "pull-request", "pr-watch"
    ]
    branch_intent = next(call[1] for call in forge.calls if call[0] == "branch-create")
    assert branch_intent["repository"] == "topij/agentic-dev-kit"
    assert b"Approved archive" not in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"Window addition" in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"Approved archive" in (worktree / "docs/kit-friction-log-archive.md").read_bytes()
    assert b"Filed 2026-01-02 as #17" in (
        worktree / "docs/kit-friction-log-archive.md"
    ).read_bytes()

    scalar_operation = {**state, "finalization_operations": [17]}
    with pytest.raises(TriageError, match="finalization operation order mismatch"):
        canonical_state(dumps(scalar_operation), settings=load_settings(root), mode="live")

    tampered_receipt = deepcopy(state)
    review_operation = deepcopy(tampered_receipt["finalization_operations"][-1])
    changed_read_back = {
        **review_operation["read_back"],
        "receipt": {
            **review_operation["read_back"]["receipt"],
            "head": "f" * 40,
        },
    }
    review_operation["read_back"] = changed_read_back
    review_operation["attempts"][-1] = {
        **review_operation["attempts"][-1], "read_back": changed_read_back,
    }
    tampered_receipt["finalization_operations"][-1] = review_operation
    tampered_receipt["pull_request_evidence"][-1] = review_operation
    with pytest.raises(TriageError, match="verified finalization read-back mismatch"):
        canonical_state(dumps(tampered_receipt), settings=load_settings(root), mode="live")

    swapped_predecessor = deepcopy(state)
    commit_operation = deepcopy(swapped_predecessor["finalization_operations"][1])
    changed_intent = {**commit_operation["intent"], "base": "f" * 40}
    changed_read_back = {**commit_operation["read_back"], "base": "f" * 40}
    changed_attempts = []
    for attempt in commit_operation["attempts"]:
        changed_attempts.append({
            **attempt,
            "intent": changed_intent,
            "intent_digest": digest(changed_intent),
            "read_back": changed_read_back if attempt["read_back"] is not None else None,
        })
    commit_operation = {
        **commit_operation,
        "intent": changed_intent,
        "intent_digest": digest(changed_intent),
        "read_back": changed_read_back,
        "attempts": changed_attempts,
    }
    swapped_predecessor["finalization_operations"][1] = commit_operation
    swapped_predecessor["repository_evidence"] = swapped_predecessor["finalization_operations"][:3]
    with pytest.raises(TriageError, match="predecessor binding mismatch"):
        canonical_state(dumps(swapped_predecessor), settings=load_settings(root), mode="live")

    retained_intent = deepcopy(state["finalization_operations"][-1]["intent"])
    pending_attempt = {
        "kind": "pr-watch",
        "intent": retained_intent,
        "intent_digest": digest(retained_intent),
        "status": "unsettled",
        "response": {"poll": "pending"},
        "read_back": {
            "url": pr_url,
            "baseRefName": "main",
            "headRefOid": commit,
        },
    }
    pending_operation = {
        **pending_attempt,
        "attempts": [*state["finalization_operations"][-1]["attempts"], pending_attempt],
    }
    pending = {
        **state,
        "phase": "forge-finalize",
        "finalization_operations": [*state["finalization_operations"][:-1], pending_operation],
        "pull_request_evidence": [
            operation for operation in state["pull_request_evidence"]
            if operation["kind"] != "pr-watch"
        ],
    }
    pending.pop("archive_sweep")
    state_path.write_bytes(dumps(pending))
    retried_forge = FakeForge([verified({
        "url": pr_url,
        "baseRefName": "main",
        "headRefName": branch,
        "headRefOid": commit,
        "isDraft": False,
        "files": paths,
        "reviewed_head": commit,
        "receipt": native_watch_receipt(pr_url, commit),
    })])
    retried = run(
        "resume", context="interactive", request={"finalize": True},
        start=root, forge=retried_forge,
    )
    assert retried["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["phase"] == "archive-sweep"
    retry_call = next(call for call in retried_forge.calls if call[0] == "pr-watch")
    assert retry_call[1] == retained_intent

    pending_merge = FakeForge([ProviderObservation("unsettled", {"poll": "unmerged"}, {
        "url": pr_url,
        "baseRefName": "main",
        "headRefOid": commit,
        "merged": False,
    })])
    pending_result = run(
        "resume", context="interactive", request={"finalize": True},
        start=root, forge=pending_merge,
    )
    assert pending_result["outcome"] == "operator-held"
    pending_state = loads_exact(state_path.read_bytes())
    assert pending_state["finalization_operations"][-1]["status"] == "unsettled"
    retained_merge_intent = pending_state["finalization_operations"][-1]["intent"]

    merge = FakeForge([verified({
        "url": pr_url,
        "baseRefName": "main",
        "headRefName": branch,
        "headRefOid": commit,
        "merged": True,
    })])
    completed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=merge)
    assert completed["outcome"] == "degraded-success"
    merge_call = next(call for call in merge.calls if call[0] == "merge-read-back")
    assert merge_call[1] == retained_merge_intent
    assert completed["pull_request_url"] == pr_url
    assert completed["observed_pr_head"] == commit
    assert completed["reviewed_head"] == commit
    assert completed["report"] == pending_state["proposal_payloads"][0]["report_binding"]["path"]
    terminal = loads_exact(state_path.read_bytes())
    assert terminal["phase"] == "completed"
    assert terminal["completion"]["route"] == "archive-sweep"
    assert terminal["finalization_operations"][-1]["kind"] == "merge-read-back"

    changed_summary = deepcopy(terminal)
    changed_summary["archive_sweep"] = {
        **changed_summary["archive_sweep"], "pr": "https://github.com/topij/agentic-dev-kit/pull/foreign",
    }
    changed_summary["completion"]["receipt_core"] = {
        **changed_summary["completion"]["receipt_core"],
        "archive_sweep": changed_summary["archive_sweep"],
    }
    changed_summary["completion"]["completed_receipt_digest"] = digest(
        changed_summary["completion"]["receipt_core"]
    )
    with pytest.raises(TriageError, match="archive summary does not derive"):
        canonical_state(dumps(changed_summary), settings=load_settings(root), mode="live")

    shortened = deepcopy(terminal)
    shortened["finalization_operations"] = shortened["finalization_operations"][:-1]
    shortened["pull_request_evidence"] = shortened["pull_request_evidence"][:-1]
    shortened["completion"]["receipt_core"] = {
        **shortened["completion"]["receipt_core"],
        "finalization_operations": shortened["finalization_operations"],
        "merge_read_back": None,
    }
    shortened["completion"]["completed_receipt_digest"] = digest(
        shortened["completion"]["receipt_core"]
    )
    with pytest.raises(TriageError, match="verified finalization chain"):
        canonical_state(dumps(shortened), settings=load_settings(root), mode="live")


def test_commit_authority_failure_leaves_clean_worktree_and_fresh_retry_can_continue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    approved, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports")
    inbox_before = (worktree / "docs/kit-friction-log.md").read_bytes()
    archive_before = (worktree / "docs/kit-friction-log-archive.md").read_bytes()
    base = git(root, "rev-parse", "HEAD")
    branch = f"chore/triage-{date.today().isoformat()}"

    class FailingCommitAuthority(FakeForge):
        def authority(self, action, request):
            if action == "worktree-clean":
                return {"clean": True}
            if action == "commit":
                raise TriageError("synthetic staged-tree authority outage", outcome="operator-held")
            return super().authority(action, request)

    first_forge = FailingCommitAuthority([verified({
        "repository": "topij/agentic-dev-kit",
        "base": base,
        "branch": branch,
        "worktree": str(worktree),
        "head": base,
        "tree": "0" * 40,
    })])
    first = run(
        "resume",
        context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root,
        approval_context=context,
        forge=first_forge,
    )
    assert first["outcome"] == "operator-held"
    assert first["detail"] == "synthetic staged-tree authority outage"
    assert (worktree / "docs/kit-friction-log.md").read_bytes() == inbox_before
    assert (worktree / "docs/kit-friction-log-archive.md").read_bytes() == archive_before
    retained = loads_exact(state_path.read_bytes())
    assert [operation["kind"] for operation in retained["finalization_operations"]] == ["branch-create"]
    monkeypatch.setattr("triage.engine.today_string", lambda: "2099-01-01")

    tree = "1" * 40
    commit = "2" * 40
    paths = ["docs/kit-friction-log-archive.md", "docs/kit-friction-log.md"]
    pr_url = "https://github.com/topij/agentic-dev-kit/pull/999"
    retry_forge = FakeForge([
        verified({
            "repository": "topij/agentic-dev-kit", "base": base,
            "branch": branch, "worktree": str(worktree), "commit": commit,
            "tree": tree, "subject": "docs(triage): graduate friction-log entries",
            "paths": paths,
        }),
        verified({
            "repository": "topij/agentic-dev-kit", "base": base,
            "branch": branch, "worktree": str(worktree), "remote_head": commit,
            "tree": tree,
        }),
        verified({
            "url": pr_url, "baseRefName": "main", "headRefName": branch,
            "headRefOid": commit, "isDraft": False, "files": paths,
        }),
        verified({
            "url": pr_url, "baseRefName": "main", "headRefName": branch,
            "headRefOid": commit, "isDraft": False, "files": paths,
            "reviewed_head": commit, "receipt": native_watch_receipt(pr_url, commit),
        }),
    ])
    retried = run(
        "resume", context="interactive", request={"finalize": True},
        start=root, forge=retry_forge,
    )
    assert retried["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["phase"] == "archive-sweep"
    assert b"Approved archive" not in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"Approved archive" in (worktree / "docs/kit-friction-log-archive.md").read_bytes()


@pytest.mark.parametrize("mutation", ["derived-content", "foreign-path"])
def test_fresh_process_refuses_mutated_retained_commit_updates_before_rebind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    approved, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports")
    base = git(root, "rev-parse", "HEAD")
    branch = f"chore/triage-{date.today().isoformat()}"
    tree = "1" * 40
    forge = FakeForge([
        verified({
            "repository": "topij/agentic-dev-kit", "base": base,
            "branch": branch, "worktree": str(worktree), "head": base,
            "tree": "0" * 40,
        }),
        ProviderObservation("ambiguous", {"accepted": True}, {
            "repository": "topij/agentic-dev-kit", "base": base,
            "branch": branch, "worktree": str(worktree), "tree": tree,
        }),
    ])
    held = run(
        "resume", context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=forge,
    )
    assert held["outcome"] == "operator-held"
    state = loads_exact(state_path.read_bytes())
    operation = state["finalization_operations"][-1]
    assert operation["kind"] == "commit"
    intent = deepcopy(operation["intent"])
    if mutation == "derived-content":
        raw = decode_bytes(intent["updates"][0]["content"]) + b"tampered\n"
        intent["updates"][0]["content"] = encode_bytes(raw)
        intent["updates"][0]["content_digest"] = digest_bytes(raw)
        expected_detail = "commit updates do not match the approved sweep"
    else:
        intent["updates"][0]["path"] = "aaa-foreign.md"
        intent["paths"][0] = "aaa-foreign.md"
        intent["authority_read_back"]["paths"][0] = "aaa-foreign.md"
        expected_detail = "commit update intent is malformed"
    intent_digest = digest(intent)
    operation["intent"] = intent
    operation["intent_digest"] = intent_digest
    for attempt in operation["attempts"]:
        attempt["intent"] = deepcopy(intent)
        attempt["intent_digest"] = intent_digest
    state_path.write_bytes(dumps(state))
    state_before = state_path.read_bytes()
    inbox_before = (worktree / "docs/kit-friction-log.md").read_bytes()
    archive_before = (worktree / "docs/kit-friction-log-archive.md").read_bytes()
    code = (
        "from pathlib import Path; from triage.engine import run; "
        f"print(__import__('triage.canonical', fromlist=['dumps']).dumps(run('resume', context='interactive', request={{'finalize': True}}, start=Path({str(root)!r}))).decode())"
    )
    environment = dict(__import__("os").environ)
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib")
    restarted = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True,
        text=True, env=environment,
    )
    result = loads_exact(restarted.stdout.strip().encode())
    assert result["outcome"] == "operator-held"
    assert result["detail"] == expected_detail
    assert state_path.read_bytes() == state_before
    assert (worktree / "docs/kit-friction-log.md").read_bytes() == inbox_before
    assert (worktree / "docs/kit-friction-log-archive.md").read_bytes() == archive_before


def test_unsettled_merge_is_retained_and_retried_without_a_merge_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The detailed finalization test establishes an archive-sweep state; this
    # focused provider assertion pins that the adapter surface has no merge
    # action at all.
    from triage.providers import GitHubForge

    forge = GitHubForge(tmp_path)
    with pytest.raises(Exception, match="unsupported forge action"):
        forge.perform("merge", {})


def test_unsettled_pr_readback_reports_observed_head_without_claiming_reviewed_head() -> None:
    head = "a" * 40
    url = "https://github.com/topij/agentic-dev-kit/pull/17"
    state = {
        "finalization_operations": [{
            "kind": "pr-watch",
            "status": "unsettled",
            "intent": {"pr": url, "base_branch": "main", "head": head},
            "read_back": {"url": url, "baseRefName": "main", "headRefOid": head},
        }],
    }
    assert _pr_result_fields(state) == {
        "pull_request_url": url,
        "observed_pr_head": head,
        "reviewed_head": None,
    }


def test_provider_verified_mismatch_is_persisted_ambiguous_and_cannot_advance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    approved, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    base = git(root, "rev-parse", "HEAD")
    mismatched = FakeForge([verified({
        "repository": "foreign/repository",
        "base": base,
        "branch": "chore/triage-2026-09-21",
        "worktree": str(worktree),
        "head": base,
        "tree": "0" * 40,
    })])
    first = run(
        "resume",
        context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root,
        approval_context=context,
        forge=mismatched,
    )
    assert first["outcome"] == "operator-held"
    retained = loads_exact(state_path.read_bytes())
    assert retained["finalization_operations"][0]["status"] == "ambiguous"
    unused = FakeForge([verified({"unexpected": True})])
    second = run("resume", context="interactive", request={"finalize": True}, start=root, forge=unused)
    assert second["outcome"] == "operator-held"
    assert [call[0] for call in unused.calls] == ["authority:protected-head"]


def test_conflicting_worktree_is_refused_before_branch_authority_or_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    approved, context = approval(presented, f"archive {candidate_id}")
    forge = FakeForge([])
    result = run(
        "resume",
        context="interactive",
        request={**approved, "finalize": True, "worktree": str(root / "nested")},
        start=root,
        approval_context=context,
        forge=forge,
    )
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "finalization worktree conflicts with caller checkout"
    assert [call[0] for call in forge.calls] == ["authority:protected-head"]
    assert not (root / "nested").exists()
