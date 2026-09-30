from __future__ import annotations

import os
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
from triage.engine import (  # noqa: E402
    _branch_date,
    _frozen_candidates,
    _pr_result_fields,
    _sweep_cleanup,
    _sweep_cleanup_kept,
    _validate_commit_updates,
    _verify_forge_read_back,
    run,
)
from triage.finalize import render_sweep, sweep_ids  # noqa: E402
from triage.inbox import parse  # noqa: E402
from triage.model import (  # noqa: E402
    SWEEP_CLEANUP_ARTIFACTS,
    Paths,
    Settings,
    TriageError,
    canonical_state,
    load_settings,
    validate_sweep_cleanup,
)
from triage.providers import FakeForge, ProviderObservation  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def repository(tmp_path: Path, *, prior_marker: bool = False) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "config/dev-model.yaml", root / "config/dev-model.yaml")
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("  engines: scripts/devkit\n", "  engines: scripts\n"), encoding="utf-8")
    (root / "docs").mkdir()
    # `prior_marker` adds an earlier sweep's graduation marker, which a current
    # sweep moves to the archive and a pre-#187 one left in place.
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n"
        + ("## 2026-01-01 — Backlog migrated by triage session earlier\n\nEngine mode: `engine-backed`.\n\n".encode() if prior_marker else b"")
        + b"## 2026-01-02\n\n"
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


def finalize_branch(state: dict) -> str:
    """The branch `_advance_finalize` computes under the shipped default
    pattern, `chore/triage-{date}-{session}`: today's date bound to this run's
    own session prefix (#807)."""
    return f"chore/triage-{date.today().isoformat()}-{state['run_identity']['session'][:8]}"


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
    branch = finalize_branch(presented)
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
    assert b"- **Approved archive.**" not in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"Window addition" in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"- **Approved archive.**" in (worktree / "docs/kit-friction-log-archive.md").read_bytes()
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
    branch = finalize_branch(presented)

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
    assert b"- **Approved archive.**" not in (worktree / "docs/kit-friction-log.md").read_bytes()
    assert b"- **Approved archive.**" in (worktree / "docs/kit-friction-log-archive.md").read_bytes()


@pytest.mark.parametrize("mutation", ["derived-content", "foreign-path", "legacy-rendering", "pre-818-rendering", "pre-187-rendering"])
def test_fresh_process_refuses_mutated_retained_commit_updates_before_rebind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path, prior_marker=mutation == "pre-187-rendering")
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
    branch = finalize_branch(presented)
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
    elif mutation in {"legacy-rendering", "pre-818-rendering", "pre-187-rendering"}:
        # A commit an engine before #812 rendered (bare marker, no record), one
        # before #818 rendered (no source entries, archive heading repeated), or one
        # before #187 rendered (earlier marker left in the inbox) must still
        # validate, so the restart gets past the content check instead of holding
        # on it.
        updates = {update["path"]: update for update in intent["updates"]}
        inbox, archive = updates["docs/kit-friction-log.md"], updates["docs/kit-friction-log-archive.md"]
        legacy = render_sweep(
            decode_bytes(inbox["previous_content"]), decode_bytes(archive["previous_content"]),
            _frozen_candidates(state), state, intent["migration_marker"].encode(),
            rendering={"legacy-rendering": "pre-812", "pre-818-rendering": "pre-818", "pre-187-rendering": "pre-187"}[mutation],
        )
        assert legacy != (decode_bytes(inbox["content"]), decode_bytes(archive["content"]))
        for update, raw in zip((inbox, archive), legacy, strict=True):
            update["content"] = encode_bytes(raw)
            update["content_digest"] = digest_bytes(raw)
        expected_detail = None
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
    if expected_detail is None:
        # Past the content check, the restart stops at the next step this
        # subprocess cannot perform: it has no forge to refresh the protected
        # branch through.
        assert (result["outcome"], result["detail"]) == ("hard-stop", "protected branch refresh authority is unavailable")
    else:
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


@pytest.mark.parametrize("placement", ["inside", "containing"])
def test_conflicting_worktree_is_refused_before_branch_authority_or_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, placement: str
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
    worktree = root / "nested" if placement == "inside" else root.parent
    result = run(
        "resume",
        context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root,
        approval_context=context,
        forge=forge,
    )
    assert result["outcome"] == "operator-held"
    assert result["detail"] == (
        "finalization worktree must lie outside the repository checkout, neither inside it nor containing it"
    )
    assert [call[0] for call in forge.calls] == ["authority:protected-head"]
    assert not (root / "nested").exists()


def _skip_unless_case_insensitive(directory: Path) -> None:
    probe = directory / "case-probe"
    probe.write_bytes(b"")
    folded = (directory / "CASE-PROBE").exists()
    probe.unlink()
    if not folded:
        pytest.skip("filesystem is case-sensitive; a case-variant path names a different directory")


def _case_variant(root: Path, placement: str) -> Path:
    """A differently cased spelling of the checkout, of a path inside it, or of its parent (#856)."""
    variant = root.with_name(root.name.swapcase())
    if placement == "same":
        return variant
    if placement == "inside":
        return variant / "nested"
    return root.parent.with_name(root.parent.name.swapcase())


@pytest.mark.parametrize("placement", ["same", "inside", "containing"])
def test_case_variant_worktree_is_refused_before_branch_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, placement: str
) -> None:
    """`resolve()` keeps the spelling it was given, so the guard decides by filesystem identity (#856)."""
    _skip_unless_case_insensitive(tmp_path)
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    approved, context = approval(loads_exact(state_path.read_bytes()), f"archive {candidate_id}")
    worktree = _case_variant(root, placement)
    assert worktree != root and not worktree.is_relative_to(root) and not root.is_relative_to(worktree)
    forge = _BaseAuthority([], git(root, "rev-parse", "HEAD"))
    result = run(
        "resume",
        context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root,
        approval_context=context,
        forge=forge,
    )
    assert result["outcome"] == "operator-held"
    assert result["detail"] == (
        "finalization worktree must lie outside the repository checkout, neither inside it nor containing it"
    )
    assert [call[0] for call in forge.calls] == ["authority:protected-head"]
    assert not (root / "nested").exists()


class _BaseAuthority(FakeForge):
    """A fake forge whose branch-create authority does not depend on an observation."""

    def __init__(self, observations, base: str) -> None:
        super().__init__(observations)
        self.base = base

    def authority(self, action, request):
        if action == "branch-create":
            self.calls.append(("authority:branch-create", request))
            return {"finalize_base_head": self.base, "descends_from_draft": True}
        if action == "worktree-clean":
            return {"clean": True}
        if action == "commit":
            raise TriageError("stop after branch-create", outcome="operator-held")
        return super().authority(action, request)


def _failed_branch_create(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Drive a live archive session to a single failed branch-create, as a same-day branch collision leaves it."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    approved, context = approval(loads_exact(state_path.read_bytes()), f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    base = git(root, "rev-parse", "HEAD")
    failing = _BaseAuthority([ProviderObservation(
        "failed", {"stderr": "fatal: a branch named 'chore/triage-x' already exists\n"}, {"effect": "unverified"},
    )], base)
    held = run(
        "resume", context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=failing,
    )
    assert held["outcome"] == "operator-held"
    retained = loads_exact(state_path.read_bytes())
    assert [(op["kind"], op["status"]) for op in retained["finalization_operations"]] == [("branch-create", "failed")]
    return root, state_path, worktree, base, retained


def test_failed_branch_create_is_retried_with_its_intent_once_read_back_shows_nothing_was_left(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, worktree, base, failed = _failed_branch_create(tmp_path, monkeypatch)
    intent = failed["finalization_operations"][0]["intent"]
    shutil.copytree(root, worktree)  # what the real branch-create produces
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    retry = _BaseAuthority([verified({
        "repository": "topij/agentic-dev-kit", "base": base, "branch": intent["branch"],
        "worktree": str(worktree), "head": base, "tree": "0" * 40,
    })], base)
    result = run("resume", context="interactive", request={"finalize": True}, start=root, forge=retry)
    assert result["detail"] == "stop after branch-create"
    assert ("authority:branch-create-absent", {"branch": intent["branch"], "worktree": intent["worktree"]}) in retry.calls
    assert [call for call in retry.calls if call[0] == "branch-create"] == [("branch-create", intent)]
    operation = loads_exact(state_path.read_bytes())["finalization_operations"][0]
    assert (operation["kind"], operation["status"], operation["intent"]) == ("branch-create", "verified", intent)
    assert [attempt["status"] for attempt in operation["attempts"]] == ["attempting", "failed", "attempting", "verified"]


_MISSING = object()


@pytest.mark.parametrize("left", ["local_branch_absent", "worktree_absent", "remote_branch_absent"])
@pytest.mark.parametrize("answer", [False, None, "yes", 1, _MISSING], ids=["false", "none", "truthy-str", "one", "missing"])
def test_failed_branch_create_stays_held_while_anything_it_could_have_left_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, left: str, answer: object
) -> None:
    """Only a literal True from the provider counts as absent; anything else holds."""
    root, state_path, worktree, base, failed = _failed_branch_create(tmp_path, monkeypatch)
    before = failed["finalization_operations"]
    retry = _BaseAuthority([], base)
    if answer is _MISSING:
        del retry.branch_create_absence[left]
    else:
        retry.branch_create_absence[left] = answer
    result = run("resume", context="interactive", request={"finalize": True}, start=root, forge=retry)
    assert result["outcome"] == "operator-held"
    assert result["capabilities"]["forge-pr-write-readback"]["mechanism"] == (
        "failed branch-create left an artifact read-back cannot rule out"
    )
    assert not [call for call in retry.calls if call[0] == "branch-create"]
    # A resume rebinds the gate claim, so compare the operation record, not the bytes.
    assert loads_exact(state_path.read_bytes())["finalization_operations"] == before


@pytest.mark.parametrize("placement", ["inside", "containing"])
def test_commit_step_refuses_a_recorded_worktree_that_conflicts_with_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, placement: str
) -> None:
    """The commit step re-checks the worktree the branch-create read-back recorded,
    not the one the request named (#857). Every other route reaches it with a
    worktree the branch-create guard already passed, so this rewrites the retained
    read-back, through the state validator, to one inside or containing the checkout."""
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
    first = run(
        "resume", context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context,
        forge=_BaseAuthority([verified({
            "repository": "topij/agentic-dev-kit", "base": base, "branch": finalize_branch(presented),
            "worktree": str(worktree), "head": base, "tree": "0" * 40,
        })], base),
    )
    assert first["detail"] == "stop after branch-create"
    state = loads_exact(state_path.read_bytes())
    operation = state["finalization_operations"][0]
    assert (operation["kind"], operation["status"]) == ("branch-create", "verified")
    assert state["repository_evidence"] == [operation]
    recorded = str(root / "nested" if placement == "inside" else root.parent)
    intent = {**operation["intent"], "worktree": recorded}
    read_back = {**operation["read_back"], "worktree": recorded}
    attempts = [
        {**attempt, "intent": intent, "intent_digest": digest(intent), "read_back": read_back if attempt["read_back"] is not None else None}
        for attempt in operation["attempts"]
    ]
    operation = {**operation, "intent": intent, "intent_digest": digest(intent), "read_back": read_back, "attempts": attempts}
    state = {**state, "finalization_operations": [operation], "repository_evidence": [operation]}
    canonical_state(dumps(state), settings=load_settings(root), mode="live")
    state_path.write_bytes(dumps(state))
    inbox_before = (root / "docs/kit-friction-log.md").read_bytes()
    archive_before = (root / "docs/kit-friction-log-archive.md").read_bytes()
    forge = FakeForge([])
    result = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == (
        "finalization worktree must lie outside the repository checkout, neither inside it nor containing it"
    )
    # Held before the worktree-clean authority, and before any commit was attempted.
    assert [call[0] for call in forge.calls] == ["authority:protected-head"]
    assert loads_exact(state_path.read_bytes())["finalization_operations"] == [operation]
    assert (root / "docs/kit-friction-log.md").read_bytes() == inbox_before
    assert (root / "docs/kit-friction-log-archive.md").read_bytes() == archive_before
    assert not (root / "nested").exists()


@pytest.mark.parametrize("placement", ["same", "inside", "containing"])
def test_commit_step_refuses_a_recorded_case_variant_of_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, placement: str
) -> None:
    """The commit-step re-check decides by filesystem identity too (#856): the
    retained branch-create read-back is rewritten, through the state validator, to
    a differently cased spelling of the checkout, of a path inside it, or of its parent."""
    _skip_unless_case_insensitive(tmp_path)
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
    first = run(
        "resume", context="interactive",
        request={**approved, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context,
        forge=_BaseAuthority([verified({
            "repository": "topij/agentic-dev-kit", "base": base, "branch": finalize_branch(presented),
            "worktree": str(worktree), "head": base, "tree": "0" * 40,
        })], base),
    )
    assert first["detail"] == "stop after branch-create"
    state = loads_exact(state_path.read_bytes())
    operation = state["finalization_operations"][0]
    recorded = _case_variant(root, placement)
    assert recorded != root and not recorded.is_relative_to(root) and not root.is_relative_to(recorded)
    intent = {**operation["intent"], "worktree": str(recorded)}
    read_back = {**operation["read_back"], "worktree": str(recorded)}
    attempts = [
        {**attempt, "intent": intent, "intent_digest": digest(intent), "read_back": read_back if attempt["read_back"] is not None else None}
        for attempt in operation["attempts"]
    ]
    operation = {**operation, "intent": intent, "intent_digest": digest(intent), "read_back": read_back, "attempts": attempts}
    state = {**state, "finalization_operations": [operation], "repository_evidence": [operation]}
    canonical_state(dumps(state), settings=load_settings(root), mode="live")
    state_path.write_bytes(dumps(state))
    inbox_before = (root / "docs/kit-friction-log.md").read_bytes()
    archive_before = (root / "docs/kit-friction-log-archive.md").read_bytes()
    forge = _BaseAuthority([], base)
    result = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == (
        "finalization worktree must lie outside the repository checkout, neither inside it nor containing it"
    )
    assert [call[0] for call in forge.calls] == ["authority:protected-head"]
    assert loads_exact(state_path.read_bytes())["finalization_operations"] == [operation]
    assert (root / "docs/kit-friction-log.md").read_bytes() == inbox_before
    assert (root / "docs/kit-friction-log-archive.md").read_bytes() == archive_before


def _branch_date_settings(tmp_path: Path, pattern: str) -> Settings:
    paths = Paths(
        tmp_path, tmp_path / "inbox", tmp_path / "archive", tmp_path / "scripts",
        "state/triage/state_{mode}.json", "state/triage/gate_{mode}.lock",
        "state/triage/recovery_{mode}_{gate_digest}.json",
        "state/triage/frozen_{mode}_{date}_{session}.json", tmp_path / "reports",
        "reports/triage_{mode}_{date}_{session}.md",
    )
    return Settings({}, "0" * 64, paths, "main", pattern, "default", tmp_path / "draft", tmp_path / "finalize", "engine-backed", "subject", {}, {})


def test_branch_date_binds_the_session_prefix_and_rejects_another_sessions_branch(tmp_path: Path) -> None:
    """#807 point 2a: a branch produced under the new pattern binds both the
    date and the state's own session prefix; a branch carrying a different
    session's prefix is rejected."""
    settings = _branch_date_settings(tmp_path, "chore/triage-{date}-{session}")
    session = "a" * 32
    branch = f"chore/triage-2026-09-26-{session[:8]}"
    assert _branch_date(settings, branch, session) == "2026-09-26"
    other_session = "b" * 32
    with pytest.raises(TriageError, match="session prefix"):
        _branch_date(settings, branch, other_session)


def test_branch_date_rejects_a_branch_that_does_not_match_the_pattern_at_all(tmp_path: Path) -> None:
    settings = _branch_date_settings(tmp_path, "chore/triage-{date}-{session}")
    session = "a" * 32
    with pytest.raises(TriageError, match="branch date is not bound"):
        _branch_date(settings, "some/other-branch-2026-09-26", session)


def test_branch_date_without_session_placeholder_never_checks_a_session(tmp_path: Path) -> None:
    """A pattern that never adopted `{session}` keeps its collision risk, but
    still parses the date, and binds no session — matching either run's."""
    settings = _branch_date_settings(tmp_path, "chore/triage-{date}")
    branch = "chore/triage-2026-09-26"
    assert _branch_date(settings, branch, "a" * 32) == "2026-09-26"
    assert _branch_date(settings, branch, "b" * 32) == "2026-09-26"


def test_legacy_no_session_branch_still_parses_under_the_new_default_pattern(tmp_path: Path) -> None:
    """#807 point 2b: a branch a previous engine wrote under the old default
    (`chore/triage-{date}`, no `{session}`) still parses once this repo's
    config carries the new default (`chore/triage-{date}-{session}`)."""
    settings = _branch_date_settings(tmp_path, "chore/triage-{date}-{session}")
    legacy_branch = "chore/triage-2026-01-02"
    assert _branch_date(settings, legacy_branch, "c" * 32) == "2026-01-02"


@pytest.mark.parametrize(
    ("pattern", "legacy_branch"),
    [
        ("chore/triage-{date}__{session}", "chore/triage-2026-01-02"),
        ("chore/triage-{date}/-{session}", "chore/triage-2026-01-02"),
        ("chore/triage-{session}--{date}", "chore/triage-2026-01-02"),
        ("chore/{session}-triage-{date}", "chore/triage-2026-01-02"),
    ],
)
def test_legacy_fallback_drops_the_whole_separator_beside_session(
    tmp_path: Path, pattern: str, legacy_branch: str
) -> None:
    settings = _branch_date_settings(tmp_path, pattern)
    assert _branch_date(settings, legacy_branch, "c" * 32) == "2026-01-02"


def test_retained_old_pattern_finalization_state_replays_cleanly_under_the_new_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#807 point 2b, at the shape the previous engine actually wrote: a
    verified branch-create whose branch has no `{session}` segment, replayed
    through the current engine's own commit-validation function against this
    repo's shipped config, which now defaults `vcs.triage_branch_pattern` to
    `chore/triage-{date}-{session}`."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    base = git(root, "rev-parse", "HEAD")
    # What a previous engine (no {session}) wrote: a branch of exactly that shape.
    legacy_branch = f"chore/triage-{date.today().isoformat()}"
    forge = FakeForge([verified({
        "repository": "topij/agentic-dev-kit", "base": base, "branch": legacy_branch,
        "worktree": str(worktree), "head": base, "tree": "0" * 40,
    })])
    result = run(
        "resume", context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=forge,
    )
    assert result["outcome"] == "operator-held"
    state = loads_exact(state_path.read_bytes())
    assert state["finalization_operations"][0]["read_back"]["branch"] == legacy_branch

    settings = load_settings(root)
    assert settings.triage_branch_pattern == "chore/triage-{date}-{session}"
    inbox_rel = "docs/kit-friction-log.md"
    archive_rel = "docs/kit-friction-log-archive.md"
    current = (worktree / inbox_rel).read_bytes()
    archive_bytes = (worktree / archive_rel).read_bytes()
    branch_date = date.today().isoformat()
    marker = f"## {branch_date} — Backlog migrated by triage session {state['run_identity']['session']}\n\n".encode()
    new_inbox, new_archive = render_sweep(current, archive_bytes, _frozen_candidates(state), state, marker)
    paths = sorted([inbox_rel, archive_rel])
    updates = sorted([
        {
            "path": inbox_rel, "previous_content": encode_bytes(current),
            "previous_digest": digest_bytes(current), "content": encode_bytes(new_inbox),
            "content_digest": digest_bytes(new_inbox),
        },
        {
            "path": archive_rel, "previous_content": encode_bytes(archive_bytes),
            "previous_digest": digest_bytes(archive_bytes), "content": encode_bytes(new_archive),
            "content_digest": digest_bytes(new_archive),
        },
    ], key=lambda item: item["path"])
    intent = {
        "host": "github.com", "repository": "topij/agentic-dev-kit", "base": base,
        "branch": legacy_branch, "worktree": str(worktree), "subject": settings.commit_subject,
        "paths": paths, "migration_marker": marker.decode(), "updates": updates,
        "authority_read_back": {"paths": paths, "staged_tree": "f" * 40},
    }
    _validate_commit_updates(state, settings, intent)  # must not raise


def test_verified_merge_read_back_retires_the_sweeps_own_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#807 point 3: a verified merge read-back retires this sweep's own
    worktree, local branch, and remote branch before writing completion. The
    result lands in `completion.sweep_cleanup`, outside `receipt_core`, so
    the completed-receipt digest is unaffected, and a completed state
    written before this field existed still validates without it."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    branch = finalize_branch(presented)
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
    swept = run(
        "resume", context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=forge,
    )
    assert swept["outcome"] == "operator-held"

    cleanup_result = {
        "worktree": {"result": "removed", "reason": None},
        "local_branch": {"result": "removed", "reason": None},
        "remote_branch": {"result": "kept", "reason": "remote branch head moved since this run pushed it"},
    }
    merge_forge = FakeForge([
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "merged": True}),
        ProviderObservation("verified", None, cleanup_result),
    ])
    completed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=merge_forge)
    assert completed["outcome"] == "degraded-success"
    assert [call[0] for call in merge_forge.calls][-2:] == ["merge-read-back", "sweep-cleanup"]
    terminal = loads_exact(state_path.read_bytes())
    assert terminal["completion"]["sweep_cleanup"] == cleanup_result
    receipt_core = terminal["completion"]["receipt_core"]
    assert "sweep_cleanup" not in receipt_core
    assert terminal["completion"]["completed_receipt_digest"] == digest(receipt_core)
    canonical_state(dumps(terminal), settings=load_settings(root), mode="live")  # revalidates with the field present

    # A completed state written before this field existed (no `sweep_cleanup`
    # key at all) must still validate and retire.
    legacy_completed = deepcopy(terminal)
    del legacy_completed["completion"]["sweep_cleanup"]
    canonical_state(dumps(legacy_completed), settings=load_settings(root), mode="live")

    # The recorded field is validated, not only tolerated: a reason accompanies
    # `kept` and nothing else. The route restriction is covered from a
    # decision-only completion in test_triage_engine.py.
    for mutate, message in (
        (lambda completion: completion["sweep_cleanup"]["remote_branch"].update(reason=None), "kept entry lacks a reason"),
        (lambda completion: completion["sweep_cleanup"]["remote_branch"].update(reason=""), "kept entry lacks a reason"),
        (lambda completion: completion["sweep_cleanup"]["worktree"].update(reason="invented"), "fabricates a reason"),
        (lambda completion: completion["sweep_cleanup"].pop("local_branch"), "wrong shape"),
    ):
        tampered = deepcopy(terminal)
        mutate(tampered["completion"])
        with pytest.raises(TriageError, match=message):
            canonical_state(dumps(tampered), settings=load_settings(root), mode="live")


def test_sweep_cleanup_never_un_completes_a_verified_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cleanup provider that raises, or answers with a malformed result,
    never withholds completion (#807 point 3): the run still completes, with
    every artifact recorded `kept` and a reason naming what went wrong."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    branch = finalize_branch(presented)
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
    run(
        "resume", context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=forge,
    )

    class RaisingCleanupForge(FakeForge):
        def perform(self, action, intent):
            if action == "sweep-cleanup":
                self.calls.append((action, intent))
                raise RuntimeError("synthetic cleanup outage")
            return super().perform(action, intent)

    merge_forge = RaisingCleanupForge([
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "merged": True}),
    ])
    completed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=merge_forge)
    assert completed["outcome"] == "degraded-success"
    terminal = loads_exact(state_path.read_bytes())
    assert terminal["phase"] == "completed"
    sweep_cleanup = terminal["completion"]["sweep_cleanup"]
    assert all(entry["result"] == "kept" for entry in sweep_cleanup.values())
    assert all("synthetic cleanup outage" in entry["reason"] for entry in sweep_cleanup.values())


def _cleanup_inputs(root: Path, worktree: Path) -> tuple[Settings, dict, dict]:
    settings = load_settings(root)
    state = {"finalization_operations": [{"kind": "branch-create", "read_back": {"worktree": str(worktree)}}]}
    archive = {"repository": "topij/agentic-dev-kit", "branch": "chore/triage-2026-09-26-abcdef12", "base": "main", "commit": "2" * 40}
    return settings, state, archive


def test_sweep_cleanup_never_hands_the_caller_checkout_to_the_provider(tmp_path: Path) -> None:
    """The engine's own caller-checkout guard (#807), independent of the one in
    `GitHubForge`: a recorded worktree that is, contains, or sits inside the
    caller's repository is kept without the provider ever being asked."""
    root = repository(tmp_path)
    for worktree in (root, root / "nested", tmp_path):
        settings, state, archive = _cleanup_inputs(root, worktree)
        forge = FakeForge([])
        result = _sweep_cleanup(settings, forge, state, archive)
        assert forge.calls == []
        assert {entry["result"] for entry in result.values()} == {"kept"}
        assert all("conflicts with the caller checkout" in entry["reason"] for entry in result.values())


@pytest.mark.parametrize("placement", ["same", "inside", "containing"])
def test_sweep_cleanup_keeps_a_case_variant_of_the_caller_checkout(tmp_path: Path, placement: str) -> None:
    """The cleanup guard decides by filesystem identity, not spelling (#856)."""
    _skip_unless_case_insensitive(tmp_path)
    root = repository(tmp_path)
    worktree = _case_variant(root, placement)
    assert worktree != root and not worktree.is_relative_to(root) and not root.is_relative_to(worktree)
    settings, state, archive = _cleanup_inputs(root, worktree)
    forge = FakeForge([])
    result = _sweep_cleanup(settings, forge, state, archive)
    assert forge.calls == []
    assert {entry["result"] for entry in result.values()} == {"kept"}
    assert all("conflicts with the caller checkout" in entry["reason"] for entry in result.values())


@pytest.mark.parametrize(
    "read_back",
    [
        None,
        {"worktree": {"result": "removed", "reason": None}, "local_branch": {"result": "removed", "reason": None}},
        {"worktree": {"result": "gone", "reason": None}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
        {"worktree": {"result": "kept", "reason": None}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
        {"worktree": {"result": "kept", "reason": ""}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
        {"worktree": {"result": "removed", "reason": None, "note": "extra"}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
        {"worktree": {"result": "removed"}, "local_branch": {"result": "absent"}, "remote_branch": {"result": "kept", "reason": "moved"}},
        {"worktree": {"result": "removed", "reason": None}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}, "extra": {"result": "removed", "reason": None}},
        {"worktree": {"result": "removed", "reason": "invented"}, "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
        {"worktree": "removed", "local_branch": {"result": "removed", "reason": None}, "remote_branch": {"result": "removed", "reason": None}},
    ],
)
def test_sweep_cleanup_records_a_malformed_provider_answer_as_kept(tmp_path: Path, read_back) -> None:
    """A provider that answers `sweep-cleanup` with anything but the three-entry
    shape is recorded as `kept` for every artifact, never passed through."""
    settings, state, archive = _cleanup_inputs(repository(tmp_path), tmp_path / "isolated-finalize")
    forge = FakeForge([ProviderObservation("verified", None, read_back)])
    result = _sweep_cleanup(settings, forge, state, archive)
    assert [call[0] for call in forge.calls] == ["sweep-cleanup"]
    assert result == {
        name: {"result": "kept", "reason": "sweep-cleanup provider returned a malformed result"}
        for name in ("worktree", "local_branch", "remote_branch")
    }
    # What the write accepts, every later read accepts too.
    validate_sweep_cleanup(result)


@pytest.mark.parametrize("status", ["failed", "ambiguous", "unsettled"])
def test_sweep_cleanup_records_a_non_verified_answer_as_kept(tmp_path: Path, status: str) -> None:
    """#827: a well-formed record that says `removed` is believed only under a
    `verified` status; any other answer keeps every artifact."""
    settings, state, archive = _cleanup_inputs(repository(tmp_path), tmp_path / "isolated-finalize")
    removed = {name: {"result": "removed", "reason": None} for name in SWEEP_CLEANUP_ARTIFACTS}
    forge = FakeForge([ProviderObservation(status, None, removed)])
    result = _sweep_cleanup(settings, forge, state, archive)
    assert [call[0] for call in forge.calls] == ["sweep-cleanup"]
    assert result == {
        name: {"result": "kept", "reason": f"sweep-cleanup provider answered {status}"}
        for name in SWEEP_CLEANUP_ARTIFACTS
    }
    validate_sweep_cleanup(result)


def test_sweep_cleanup_fallback_follows_the_artifact_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """#827: the `kept` fallback is built from `SWEEP_CLEANUP_ARTIFACTS`, so a
    change to the set cannot leave the fallback failing its own validator."""
    widened = (*SWEEP_CLEANUP_ARTIFACTS, "extra_artifact")
    monkeypatch.setattr("triage.model.SWEEP_CLEANUP_ARTIFACTS", widened)
    monkeypatch.setattr("triage.engine.SWEEP_CLEANUP_ARTIFACTS", widened)
    fallback = _sweep_cleanup_kept("synthetic reason")
    assert set(fallback) == set(widened)
    validate_sweep_cleanup(fallback)


def test_resume_completes_a_verified_merge_read_back_whose_completion_was_never_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#826: a run that dies after persisting its verified `merge-read-back`
    but before writing completion leaves every finalization operation verified
    in `forge-finalize`. A resume completes it from the recorded read-back,
    without a second merge read-back, and writes the same completion the live
    path would have."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    branch = finalize_branch(presented)
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
    swept = run(
        "resume", context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=forge,
    )
    assert swept["outcome"] == "operator-held"

    cleanup_result = {name: {"result": "removed", "reason": None} for name in SWEEP_CLEANUP_ARTIFACTS}
    live = run("resume", context="interactive", request={"finalize": True}, start=root, forge=FakeForge([
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "merged": True}),
        ProviderObservation("verified", None, cleanup_result),
    ]))
    assert live["outcome"] == "degraded-success"
    terminal = loads_exact(state_path.read_bytes())

    # What `_forge_attempt` persisted before the process died: the verified
    # merge read-back in `forge-finalize`, with no derived summary and no
    # completion. It is a valid retained state in its own right.
    interrupted = deepcopy(terminal)
    interrupted["phase"] = "forge-finalize"
    del interrupted["archive_sweep"]
    del interrupted["completion"]
    assert [(op["kind"], op["status"]) for op in interrupted["finalization_operations"]][-1] == ("merge-read-back", "verified")
    canonical_state(dumps(interrupted), settings=load_settings(root), mode="live")
    state_path.write_bytes(dumps(interrupted))

    resume_forge = FakeForge([ProviderObservation("verified", None, cleanup_result)])
    resumed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=resume_forge)
    assert resumed["outcome"] == "degraded-success"
    assert resumed["pull_request_url"] == pr_url
    assert resumed["reviewed_head"] == commit
    assert "merge-read-back" not in [call[0] for call in resume_forge.calls]
    assert [call[0] for call in resume_forge.calls][-1] == "sweep-cleanup"
    completed = loads_exact(state_path.read_bytes())
    assert completed["phase"] == "completed"
    assert completed["archive_sweep"] == terminal["archive_sweep"]
    assert completed["completion"] == terminal["completion"]
    canonical_state(dumps(completed), settings=load_settings(root), mode="live")


def _engine_completed_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, swept_before_draft: bool = False
) -> tuple[Path, Path, Path, dict]:
    """Drive a real engine run to a completed archive-sweep state (#833).

    Returns the repository, the live state path, the finalization worktree
    holding the rendered sweep, and the completed state. Nothing after the
    draft is committed to the repository's own history: each caller builds the
    history it needs. `swept_before_draft` first sweeps the entry the run will
    archive and puts it back, both before the run's draft head.
    """
    root = repository(tmp_path)
    if swept_before_draft:
        inbox, archive = root / "docs/kit-friction-log.md", root / "docs/kit-friction-log-archive.md"
        original = inbox.read_text(encoding="utf-8")
        block = "- **Approved archive.** exact bytes. **Filed 2026-01-02 as #17.**"
        inbox.write_text(original.replace(block + "\n\n", ""), encoding="utf-8")
        archive.write_text(archive.read_text(encoding="utf-8") + "\n" + block + "\n", encoding="utf-8")
        _commit_to_main(root, "an earlier sweep of the same entry")
        inbox.write_text(original, encoding="utf-8")
        _commit_to_main(root, "the entry is back in the inbox")
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    request, context = approval(presented, f"archive {candidate_id}")
    worktree = tmp_path / "isolated-finalize"
    shutil.copytree(root, worktree)
    shutil.rmtree(worktree / "reports", ignore_errors=True)
    branch = finalize_branch(presented)
    base = git(root, "rev-parse", "HEAD")
    tree, commit = "1" * 40, "2" * 40
    pr_url = "https://github.com/topij/agentic-dev-kit/pull/999"
    paths = ["docs/kit-friction-log-archive.md", "docs/kit-friction-log.md"]
    run(
        "resume", context="interactive",
        request={**request, "finalize": True, "worktree": str(worktree)},
        start=root, approval_context=context, forge=FakeForge([
            verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "head": base, "tree": "0" * 40}),
            verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "commit": commit, "tree": tree, "subject": "docs(triage): graduate friction-log entries", "paths": paths}),
            verified({"repository": "topij/agentic-dev-kit", "base": base, "branch": branch, "worktree": str(worktree), "remote_head": commit, "tree": tree}),
            verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "isDraft": False, "files": paths}),
            verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "isDraft": False, "files": paths, "reviewed_head": commit, "receipt": native_watch_receipt(pr_url, commit)}),
        ]),
    )
    cleanup_result = {name: {"result": "kept", "reason": "fixture"} for name in SWEEP_CLEANUP_ARTIFACTS}
    completed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=FakeForge([
        verified({"url": pr_url, "baseRefName": "main", "headRefName": branch, "headRefOid": commit, "merged": True}),
        ProviderObservation("verified", None, cleanup_result),
    ]))
    assert completed["outcome"] == "degraded-success"
    terminal = loads_exact(state_path.read_bytes())
    assert terminal["phase"] == "completed" and "merge_read_back" not in terminal["completion"]
    return root, state_path, worktree, terminal


def _commit_to_main(root: Path, message: str) -> str:
    git(root, "add", "docs/kit-friction-log.md", "docs/kit-friction-log-archive.md")
    git(root, "commit", "-q", "--allow-empty", "-m", message)
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return git(root, "rev-parse", "HEAD")


def _land_sweep(root: Path, worktree: Path) -> str:
    for rel in ("docs/kit-friction-log.md", "docs/kit-friction-log-archive.md"):
        shutil.copy2(worktree / rel, root / rel)
    return _commit_to_main(root, "docs(triage): graduate friction-log entries (#999)")


def _invalidate(state_path: Path, terminal: dict) -> bytes:
    """Make the completed state invalid in one field, the way an older or
    hand-edited state fails validation, and keep its finished evidence."""
    raw = dumps({**terminal, "schema_deviations": [{"id": "hand-recorded"}]})
    state_path.write_bytes(raw)
    return raw


def _recover_approval(core_digest: str) -> tuple[dict, ApprovalContext]:
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = ApprovalContext("current-session", "operator", {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest})
    return {"recovery_approval": supplied}, context


def test_recover_retires_an_invalid_engine_written_completed_sweep_found_in_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#833: the engine's finished layout names no merge commit, so `recover`
    finds this run's sweep on the protected ref and retires the run on exact
    approval instead of holding it for good."""
    root, state_path, worktree, terminal = _engine_completed_sweep(tmp_path, monkeypatch)
    sweep = _land_sweep(root, worktree)
    raw = _invalidate(state_path, terminal)
    with pytest.raises(TriageError):
        canonical_state(raw, settings=load_settings(root), mode="live", retiring=True)

    # Planned in its own process, as through the CLI: the capture's gate owner must be
    # proven dead before the approval acts on it (#863).
    child = (
        "import sys\nfrom pathlib import Path\nfrom triage.canonical import dumps\n"
        "from triage.engine import run\n"
        "print(dumps(run('recover', context='interactive', request={}, start=Path(sys.argv[1]))).decode(), flush=True)\n"
    )
    environment = {**os.environ, "PYTHONPATH": str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)}
    completed = subprocess.run([sys.executable, "-c", child, str(root)], check=True, capture_output=True, text=True, env=environment)
    planned = loads_exact(completed.stdout.strip().encode())
    plan = planned["recovery_plan"]
    assert plan["action_core"]["action"] == "retire-terminal-invalid-state"
    evidence = plan["action_core"]["terminal_evidence"]
    assert evidence["merge_commit"] == sweep
    assert evidence["merge_commit_source"] == "found-in-git"
    assert evidence["merge_commit_reachable_from"] == "refs/remotes/origin/main"
    assert evidence["final_head"] == terminal["archive_sweep"]["reviewed_head"]
    assert evidence["pull_request"] == "https://github.com/topij/agentic-dev-kit/pull/999"
    assert evidence["swept_candidates"] == [terminal["decisions"][0]["candidate_id"]]
    assert state_path.read_bytes() == raw

    request, context = _recover_approval(plan["action_core_digest"])
    recovered = run("recover", context="interactive", request=request, start=root, approval_context=context)
    assert recovered["detail"] == "recovered-safe-to-restart"
    assert loads_exact(state_path.read_bytes())["kind"] == "recovered-safe-to-restart"
    assert Path(plan["action_core"]["quarantine_path"]).read_bytes() == raw
    restarted = run("new", context="interactive", request={}, start=root)
    assert restarted["detail"] == "verified recovery receipt replaced by reserved new state"


@pytest.mark.parametrize("history", ["not-landed", "swept-twice", "block-back-in-inbox"])
def test_recover_holds_an_invalid_engine_written_completed_sweep_git_does_not_prove(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, history: str
) -> None:
    """No commit, or more than one, is this run's sweep, or the swept block is
    back in the protected ref's inbox: the run stays held, bytes untouched."""
    root, state_path, worktree, terminal = _engine_completed_sweep(tmp_path, monkeypatch)
    inbox = root / "docs/kit-friction-log.md"
    if history != "not-landed":
        _land_sweep(root, worktree)
        block = next(
            decode_bytes(record["source_block"]).decode("utf-8").rstrip("\n")
            for record in terminal["frozen_snapshot"]["content"]["candidate_index"]
            if record["candidate_id"] == terminal["decisions"][0]["candidate_id"]
        )
        swept_inbox = inbox.read_text(encoding="utf-8")
        inbox.write_text(swept_inbox + "\n" + block + "\n", encoding="utf-8")
        _commit_to_main(root, "block re-added to the inbox")
        if history == "swept-twice":
            inbox.write_text(swept_inbox, encoding="utf-8")
            _commit_to_main(root, "a second commit sweeps the same block")
    raw = _invalidate(state_path, terminal)
    held = run("recover", context="interactive", request={}, start=root)
    assert held["outcome"] == "operator-held"
    assert held["detail"] == "external-attempt-absence-unproven"
    assert state_path.read_bytes() == raw


def test_recover_refuses_a_completed_state_valid_but_for_a_later_config_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#833's second reproduction: a self-consistent completed state written
    under an earlier configuration is valid for retirement, so `recover` refuses
    it as valid rather than capturing it as invalid and holding it for good."""
    root, state_path, _worktree, _terminal = _engine_completed_sweep(tmp_path, monkeypatch)
    config = root / "config/dev-model.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("bot_pending_grace_minutes: 15", "bot_pending_grace_minutes: 16"),
        encoding="utf-8",
    )
    raw = state_path.read_bytes()
    with pytest.raises(TriageError, match="configuration identity mismatch"):
        canonical_state(raw, settings=load_settings(root), mode="live")
    result = run("recover", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "captured state is valid; recovery refused"
    assert state_path.read_bytes() == raw
    restarted = run("new", context="interactive", request={}, start=root)
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved", restarted


def test_recover_takes_the_first_parent_merge_commit_of_a_merge_landed_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sweep landed by a merge commit moves the block in both the branch
    commit and the merge; only the first-parent walk makes the merge the one
    candidate, so the run retires rather than being held as ambiguous."""
    root, state_path, worktree, terminal = _engine_completed_sweep(tmp_path, monkeypatch)
    git(root, "checkout", "-q", "-b", "sweep-branch")
    branch_commit = _land_sweep(root, worktree)
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-ff", "-m", "Merge the sweep", "sweep-branch")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    merge = git(root, "rev-parse", "HEAD")
    assert git(root, "rev-parse", f"{merge}^2") == branch_commit
    _invalidate(state_path, terminal)
    plan = run("recover", context="interactive", request={}, start=root)["recovery_plan"]
    assert plan["action_core"]["action"] == "retire-terminal-invalid-state"
    assert plan["action_core"]["terminal_evidence"]["merge_commit"] == merge


def test_recover_looks_for_the_sweep_only_after_the_runs_draft_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same entry was swept once and put back before this run drafted: that
    earlier commit is not this run's sweep, so only the one after the draft head
    counts and the run retires."""
    root, state_path, worktree, terminal = _engine_completed_sweep(tmp_path, monkeypatch, swept_before_draft=True)
    sweep = _land_sweep(root, worktree)
    _invalidate(state_path, terminal)
    plan = run("recover", context="interactive", request={}, start=root)["recovery_plan"]
    assert plan["action_core"]["action"] == "retire-terminal-invalid-state"
    assert plan["action_core"]["terminal_evidence"]["merge_commit"] == sweep


def test_recover_holds_when_the_runs_draft_head_is_not_on_the_protected_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recorded draft head the protected ref does not contain bounds nothing,
    so the state stays held even though a sweep is on the ref."""
    root, state_path, worktree, terminal = _engine_completed_sweep(tmp_path, monkeypatch)
    git(root, "checkout", "-q", "-b", "elsewhere")
    git(root, "commit", "-q", "--allow-empty", "-m", "never merged")
    foreign = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "-q", "main")
    _land_sweep(root, worktree)
    moved = deepcopy(terminal)
    moved["run_identity"]["protected_branch_head"] = foreign
    raw = _invalidate(state_path, moved)
    held = run("recover", context="interactive", request={}, start=root)
    assert held["detail"] == "external-attempt-absence-unproven"
    assert state_path.read_bytes() == raw
