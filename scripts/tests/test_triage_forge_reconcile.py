"""#1302: the sweep commit runs no adopter hook, and an ambiguous local-only
commit has an approval-bound way out.

The real git provider runs against a local bare origin. Every `git` call it
makes is rewritten to that origin through `url.<bare>.insteadOf`, and `gh` and
`uv run pr_watch.py` are answered by a small fake, so nothing leaves the
temporary directory.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, triage_config_text  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from test_finalize_triage import (  # noqa: E402
    approval,
    finalize_branch,
    native_watch_receipt,
    proposal_request,
)
from triage.approval import ApprovalContext  # noqa: E402
from triage.canonical import (  # noqa: E402
    decode_bytes,
    digest,
    digest_bytes,
    dumps,
    encode_bytes,
    loads_exact,
)
from triage.engine import run  # noqa: E402
from triage.model import (  # noqa: E402
    TriageError,
    canonical_state,
    discard_completed,
    legacy_fingerprint,
    load_settings,
    local_commit_discard_approval,
    local_commit_discard_refusal,
)
from triage.outcome import session_waiting_on  # noqa: E402
from triage.providers import GitHubForge  # noqa: E402

GITHUB_URL = "https://github.com/topij/agentic-dev-kit.git"
REPOSITORY = "topij/agentic-dev-kit"
PATHS = ["docs/kit-friction-log-archive.md", "docs/kit-friction-log.md"]
HOOK_MARK = b"<!-- rewritten by an adopter hook -->"

# A formatting pre-commit hook like the adopter's mdformat step: it rewrites
# every staged Markdown file and stages the result again.
PRE_COMMIT = f"""#!/bin/sh
for f in $(git diff --cached --name-only -- '*.md'); do
  printf '\\n{HOOK_MARK.decode()}\\n' >> "$f"
  git add -- "$f"
done
"""
MESSAGE_HOOK = """#!/bin/sh
printf 'subject rewritten by an adopter hook\\n' > "$1"
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


class LocalForge:
    """A runner for `GitHubForge`: git against the local bare origin, and a fake
    `gh` and `pr_watch.py` that read their answers from that origin."""

    def __init__(self, bare: Path, *, pull_requests: list | None = None) -> None:
        self.bare = bare
        self.pull_requests = pull_requests if pull_requests is not None else []
        self.created: dict[str, str] = {}
        self.merged = False
        self.calls: list[list[str]] = []

    def _done(self, argv: list[str], stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, returncode, stdout, "")

    def _branch_head(self, branch: str) -> str:
        return git(self.bare, "rev-parse", f"refs/heads/{branch}")

    def __call__(self, argv: list[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[0] == "git":
            rewritten = ["git", "-c", f"url.{self.bare}.insteadOf={GITHUB_URL}", *argv[1:]]
            return subprocess.run(rewritten, cwd=cwd, check=False, capture_output=True, text=True)
        if argv[:3] == ["gh", "pr", "list"]:
            # The read-back must ask for pull requests in every state: a closed or
            # merged one still means the commit left the machine.
            assert argv[argv.index("--state") + 1] == "all", argv
            return self._done(argv, json.dumps(self.pull_requests))
        if argv[:3] == ["gh", "pr", "create"]:
            branch = argv[argv.index("--head") + 1]
            url = f"https://github.com/{REPOSITORY}/pull/{len(self.created) + 1}"
            self.created[url] = branch
            return self._done(argv, url + "\n")
        if argv[:3] == ["gh", "pr", "view"]:
            url = argv[3] if argv[3] in self.created else next(key for key, value in self.created.items() if value == argv[3])
            branch = self.created[url]
            head = self._branch_head(branch)
            base = git(self.bare, "merge-base", "refs/heads/main", head)
            files = git(self.bare, "diff", "--name-only", base, head).splitlines()
            return self._done(argv, json.dumps({
                "url": url, "baseRefName": "main", "headRefName": branch, "headRefOid": head,
                "isDraft": False, "mergedAt": "2026-11-08T00:00:00Z" if self.merged else None,
                "files": [{"path": path} for path in files],
            }))
        if argv[:2] == ["uv", "run"] and argv[-1] == "--assert-ready":
            return self._done(argv)
        if argv[:2] == ["uv", "run"] and argv[-1] == "--json":
            url = f"https://github.com/{REPOSITORY}/pull/{argv[3]}"
            return self._done(argv, json.dumps(native_watch_receipt(url, self._branch_head(self.created[url]))))
        raise AssertionError(f"unexpected forge call {argv}")


class HookedForge(GitHubForge):
    """The commit every engine before #1302 made: through the adopter's hooks."""

    COMMIT_ARGV = ("git", "commit", "-m")


def sweep_repository(tmp_path: Path) -> tuple[Path, Path]:
    """A checkout whose `origin` names GitHub while its objects live in a local
    bare repository, with the fixture config and inbox at `main`."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "config/dev-model.yaml").write_text(triage_config_text(), encoding="utf-8")
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
    (root / ".gitignore").write_text("reports/\n", encoding="utf-8")
    git(root.parent, "init", "-q", "-b", "main", str(root))
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    git(root, "remote", "add", "origin", GITHUB_URL)
    git(root, "push", "-q", str(bare), "HEAD:refs/heads/main")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root, bare


def install_hook(root: Path, name: str, body: str, *, hooks_path: bool = False) -> None:
    directory = root / ".githooks" if hooks_path else root / ".git/hooks"
    directory.mkdir(parents=True, exist_ok=True)
    hook = directory / name
    hook.write_text(body, encoding="utf-8")
    hook.chmod(0o755)
    if hooks_path:
        git(root, "config", "core.hooksPath", str(directory))


def _commit_request(root: Path, worktree: Path, branch: str, base: str) -> dict:
    updates = []
    for path in PATHS:
        previous = (worktree / path).read_bytes()
        content = previous + b"\n- **Swept.** by the engine.\n"
        updates.append({
            "path": path, "previous_content": encode_bytes(previous), "previous_digest": digest_bytes(previous),
            "content": encode_bytes(content), "content_digest": digest_bytes(content),
        })
    return {
        "host": "github.com", "repository": REPOSITORY, "base": base, "branch": branch,
        "worktree": str(worktree), "subject": "docs(triage): graduate friction-log entries",
        "paths": PATHS, "updates": updates,
    }


def _commit_once(forge: GitHubForge, root: Path, tmp_path: Path, branch: str) -> tuple[dict, object, Path]:
    """branch-create then commit, as the engine drives them, returning the commit
    intent and its observation."""
    base = git(root, "rev-parse", "HEAD")
    worktree = tmp_path / f"sweep-{branch.replace('/', '-')}"
    created = forge.perform("branch-create", {"repository": REPOSITORY, "branch": branch, "worktree": str(worktree), "finalize_base_head": base})
    assert created.status == "verified"
    request = _commit_request(root, worktree, branch, base)
    authority = forge.authority("commit", request)
    for update in request["updates"]:
        (worktree / update["path"]).write_bytes(decode_bytes(update["content"]))
    intent = {**request, "authority_read_back": authority}
    return intent, forge.perform("commit", intent), worktree


HOOKS = [
    ("pre-commit", PRE_COMMIT, False),
    ("pre-commit", PRE_COMMIT, True),
    ("prepare-commit-msg", MESSAGE_HOOK, False),
    ("commit-msg", MESSAGE_HOOK, False),
]


@pytest.mark.parametrize(("hook", "body", "hooks_path"), HOOKS, ids=["pre-commit", "pre-commit-core-hooksPath", "prepare-commit-msg", "commit-msg"])
def test_the_sweep_commit_lands_the_attested_tree_and_subject_whatever_hook_the_adopter_runs(
    tmp_path: Path, hook: str, body: str, hooks_path: bool
) -> None:
    root, bare = sweep_repository(tmp_path)
    install_hook(root, hook, body, hooks_path=hooks_path)
    runner = LocalForge(bare)
    # Control: the hook is live. The commit every earlier engine made goes
    # through it, so its tree or subject differs from what was attested.
    hooked_intent, hooked, _ = _commit_once(HookedForge(root, runner), root, tmp_path, "chore/triage-hooked")
    assert hooked.status == "verified"
    assert (hooked.read_back["tree"], hooked.read_back["subject"]) != (
        hooked_intent["authority_read_back"]["staged_tree"], hooked_intent["subject"]
    )
    intent, observed, worktree = _commit_once(GitHubForge(root, runner), root, tmp_path, "chore/triage-2099-01-01")
    assert observed.status == "verified"
    assert observed.read_back["tree"] == intent["authority_read_back"]["staged_tree"]
    assert observed.read_back["subject"] == intent["subject"]
    assert HOOK_MARK not in subprocess.run(
        ["git", "-C", str(worktree), "show", "HEAD:docs/kit-friction-log.md"], check=True, capture_output=True
    ).stdout


def _ambiguous_local_commit(tmp_path: Path, runner_kwargs: dict | None = None) -> tuple[Path, Path, LocalForge, list, dict]:
    """The adopter's shape: branch-create verified, then a hooked commit whose
    tree differs from the attested one, recorded as the engine records it."""
    root, bare = sweep_repository(tmp_path)
    install_hook(root, "pre-commit", PRE_COMMIT)
    runner = LocalForge(bare, **(runner_kwargs or {}))
    forge = HookedForge(root, runner)
    branch = "chore/triage-2099-01-01"
    base = git(root, "rev-parse", "HEAD")
    worktree = tmp_path / "sweep"
    created = forge.perform("branch-create", {"repository": REPOSITORY, "branch": branch, "worktree": str(worktree), "finalize_base_head": base})
    request = _commit_request(root, worktree, branch, base)
    authority = forge.authority("commit", request)
    for update in request["updates"]:
        (worktree / update["path"]).write_bytes(decode_bytes(update["content"]))
    intent = {**request, "authority_read_back": authority}
    committed = forge.perform("commit", intent)
    assert committed.read_back["tree"] != authority["staged_tree"]
    operations = [
        {"kind": "branch-create", "status": "verified", "intent": {}, "read_back": created.read_back},
        {"kind": "commit", "status": "ambiguous", "intent": intent, "read_back": committed.read_back},
    ]
    request_core = {"host": "github.com", "repository": REPOSITORY, "branch": branch, "base": base, "worktree": str(worktree), "paths": PATHS}
    return root, worktree, runner, operations, request_core


def _leave(root: Path, worktree: Path, runner: LocalForge, leftover: str, request_core: dict) -> None:
    branch = request_core["branch"]
    if leftover == "worktree-gone":
        shutil.rmtree(worktree)
    elif leftover == "worktree-gone-and-pruned":
        shutil.rmtree(worktree)
        git(root, "worktree", "prune")
    elif leftover == "remote-branch":
        git(worktree, "push", "-q", str(runner.bare), f"HEAD:refs/heads/{branch}")
    elif leftover == "pull-request":
        runner.pull_requests.append({"number": 7, "url": f"https://github.com/{REPOSITORY}/pull/7", "state": "CLOSED"})
    elif leftover == "second-commit":
        git(worktree, "-c", "core.hooksPath=/dev/null", "commit", "-q", "--allow-empty", "-m", "another")
    elif leftover == "foreign-path":
        (worktree / "config/dev-model.yaml").write_text("changed\n", encoding="utf-8")
        git(worktree, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-a", "--amend", "--no-edit")
    elif leftover == "dirty-worktree":
        (worktree / "docs/kit-friction-log.md").write_bytes(b"edited\n")
    elif leftover == "amended":
        # Still one commit on the base, touching only the two paths, but not the
        # commit the ambiguous attempt read back.
        git(worktree, "-c", "core.hooksPath=/dev/null", "commit", "-q", "--amend", "-m", "amended")
    elif leftover == "other-checkout":
        shutil.rmtree(worktree)
        git(root, "worktree", "prune")
        git(root, "worktree", "add", "-q", str(worktree.parent / "elsewhere"), branch)


ELIGIBLE = ["as-left", "worktree-gone", "worktree-gone-and-pruned"]
REFUSED = {
    "remote-branch": "a remote branch of that name exists",
    "pull-request": "a pull request from that branch exists",
    "second-commit": "not exactly one commit on the recorded base",
    "foreign-path": "touches a path other than the two recorded ones",
    "dirty-worktree": "not a clean checkout of that branch",
    "other-checkout": "checked out in another worktree",
    "amended": "not the commit the ambiguous attempt read back",
}


@pytest.mark.parametrize("statuses", [["verified", "verified"], ["verified", "failed"], ["verified", "attempting"], ["failed", "ambiguous"]])
def test_only_a_verified_branch_create_then_an_ambiguous_commit_can_be_discarded(tmp_path: Path, statuses: list) -> None:
    root, worktree, runner, operations, request_core = _ambiguous_local_commit(tmp_path)
    read_back = GitHubForge(root, runner).authority("commit-discard-read-back", request_core)
    assert local_commit_discard_refusal(read_back, operations) is None
    changed = [{**operation, "status": status} for operation, status in zip(operations, statuses, strict=True)]
    assert local_commit_discard_refusal(read_back, changed) == "only a verified branch-create followed by an ambiguous commit can be discarded"


@pytest.mark.parametrize("leftover", ELIGIBLE + list(REFUSED))
def test_the_discard_read_back_admits_only_a_commit_that_never_left_the_machine(tmp_path: Path, leftover: str) -> None:
    root, worktree, runner, operations, request_core = _ambiguous_local_commit(tmp_path)
    _leave(root, worktree, runner, leftover, request_core)
    forge = GitHubForge(root, runner)
    read_back = forge.authority("commit-discard-read-back", request_core)
    refusal = local_commit_discard_refusal(read_back, operations)
    if leftover in ELIGIBLE:
        assert refusal is None, read_back
    else:
        assert refusal is not None and REFUSED[leftover] in refusal, (refusal, read_back)


@pytest.mark.parametrize("leftover", ["as-left", "worktree-gone", "remote-branch", "pull-request", "dirty-worktree", "moved-branch"])
def test_the_discard_removes_only_a_local_only_branch_and_its_worktree(tmp_path: Path, leftover: str) -> None:
    root, worktree, runner, operations, request_core = _ambiguous_local_commit(tmp_path)
    if leftover != "moved-branch":
        _leave(root, worktree, runner, leftover, request_core)
    forge = GitHubForge(root, runner)
    expected = operations[1]["read_back"]["commit"]
    if leftover == "moved-branch":
        # The approved head is not the branch's head: nothing is removed.
        observed = forge.perform("commit-discard", {**request_core, "expected_local_head": request_core["base"]})
        assert observed.status == "ambiguous"
        assert worktree.exists()
        assert git(root, "rev-parse", f"refs/heads/{request_core['branch']}") == expected
        return
    observed = forge.perform("commit-discard", {**request_core, "expected_local_head": expected})
    local = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"refs/heads/{request_core['branch']}"], capture_output=True, text=True)
    if leftover in {"as-left", "worktree-gone"}:
        assert observed.status == "verified"
        assert local.returncode == 1
        assert not worktree.exists()
        assert str(worktree) not in git(root, "worktree", "list", "--porcelain")
    elif leftover == "dirty-worktree":
        # The worktree is removed without --force, so a dirty one stays, edits and all.
        assert observed.status == "failed"
        assert (worktree / "docs/kit-friction-log.md").read_bytes() == b"edited\n"
        assert local.stdout.strip() == expected
    else:
        assert observed.status == "ambiguous"
        assert local.stdout.strip() == expected
    if leftover == "as-left":
        again = forge.perform("commit-discard", {**request_core, "expected_local_head": expected})
        assert again.status == "verified"


# ---------------------------------------------------------------------------
# The adopter's session, end to end.


def _settings_fingerprint_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Record fingerprints as every engine before #1303 did."""
    monkeypatch.setattr("triage.model.scoped_fingerprint", legacy_fingerprint)


def _context(decision: str, name: str, value: str) -> ApprovalContext:
    return ApprovalContext("current-session", "operator", {"decision": decision, name: value, "approver_identity": "operator"})


@pytest.mark.evidence
def test_the_held_adopter_session_finishes_through_engine_routes_after_an_upgrade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """cs-toolkit's session 72885a30, replayed: drafted and approved under the
    whole-config fingerprint, its sweep commit ambiguous because a formatting
    hook rewrote the staged files, its worktree gone, and the config changed
    since in keys the engine never reads. After the upgrade, the config rebind
    and the local-commit discard finish it without editing or deleting state."""
    root, bare = sweep_repository(tmp_path)
    install_hook(root, "pre-commit", PRE_COMMIT)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    draft_head = git(root, "rev-parse", "HEAD")
    runner = LocalForge(bare)
    old_worktree = tmp_path / "scratchpad/sweep-wt"

    # Before the upgrade: draft, approve and finalize as the old engine did.
    with monkeypatch.context() as old_engine:
        _settings_fingerprint_legacy(old_engine)
        draft_request, candidate_id = proposal_request(root)
        run("new", context="interactive", request=draft_request, start=root)
        presented = loads_exact(state_path.read_bytes())
        assert presented["config_fingerprint"] == legacy_fingerprint(load_settings(root).config)
        approved, approved_context = approval(presented, f"archive {candidate_id}")
        hooked = HookedForge(root, runner)
        held = run(
            "resume", context="interactive", request={**approved, "finalize": True, "worktree": str(old_worktree)},
            start=root, approval_context=approved_context, forge=hooked, head_authority=hooked,
        )
    assert held["outcome"] == "operator-held"
    stranded = loads_exact(state_path.read_bytes())
    chain = stranded["finalization_operations"]
    assert [(item["kind"], item["status"]) for item in chain] == [("branch-create", "verified"), ("commit", "ambiguous")]
    assert chain[1]["read_back"]["tree"] != chain[1]["intent"]["authority_read_back"]["staged_tree"]
    ambiguous_commit = chain[1]["read_back"]["commit"]
    # The session scratchpad that held the worktree is gone; the branch is not.
    shutil.rmtree(old_worktree)
    # Since then: an unrelated config PR, and newer inbox sections on main.
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("bot_pending_grace_minutes: 15", "bot_pending_grace_minutes: 30"), encoding="utf-8")
    inbox = root / "docs/kit-friction-log.md"
    inbox.write_bytes(inbox.read_bytes().replace(b"# Log\n\n", b"# Log\n\n## 2026-02-01\n\n- **Newer entry.** added on main later.\n\n", 1))
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-am", "later main")
    git(root, "push", "-q", str(bare), "HEAD:refs/heads/main")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    forge = GitHubForge(root, runner)

    # After the upgrade: the legacy fingerprint is refused, not silently taken.
    refused = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)
    assert refused["refusal_code"] == "configuration-identity"
    assert state_path.read_bytes() == dumps(stranded)

    # Config rebind: plan from the draft-time config bytes, then approve.
    legacy_config = tmp_path / "legacy-dev-model.yaml"
    legacy_config.write_bytes(subprocess.run(["git", "-C", str(root), "show", f"{draft_head}:config/dev-model.yaml"], check=True, capture_output=True).stdout)
    spec = {"legacy_config": str(legacy_config), "legacy_local_config": None}
    planned = run("resume", context="interactive", request={"config_rebind": spec}, start=root)
    assert planned["waiting_on"] == "recovery-approval", planned
    core_digest = planned["recovery_plan"]["core_digest"]
    assert planned["recovery_plan"]["core"]["legacy_fingerprint"] == stranded["config_fingerprint"]
    assert state_path.read_bytes() == dumps(stranded)
    rebind_approval = {"decision": "rebind-config", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    rebound = run(
        "resume", context="interactive", request={"config_rebind": {**spec, "approval": rebind_approval}},
        start=root, approval_context=_context("rebind-config", "core_digest", core_digest),
    )
    assert rebound["refusal_code"] is None, rebound
    assert rebound["recovery_plan"] is None
    after_rebind = loads_exact(state_path.read_bytes())
    assert after_rebind["config_rebind"]["core"]["scoped_fingerprint"] == load_settings(root).fingerprint
    assert after_rebind["run_identity"] == stranded["run_identity"]

    # Commit reconciliation: plan, then approve the discard with a new worktree.
    plan = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)
    assert plan["waiting_on"] == "recovery-approval", plan
    assert plan["recovery_plan"]["eligible"] is True
    plan_digest = plan["recovery_plan"]["plan_digest"]
    assert plan["recovery_plan"]["plan"]["read_back"]["local_head"] == ambiguous_commit
    new_worktree = tmp_path / "sweep-after-upgrade"
    finished = run(
        "resume", context="interactive",
        request={"finalize": True, "worktree": str(new_worktree), "commit_reconciliation": local_commit_discard_approval(plan_digest, "operator")},
        start=root, approval_context=_context("discard-local-commit", "plan_digest", plan_digest), forge=forge, head_authority=forge,
    )
    assert finished["outcome"] == "operator-held", finished
    assert finished["recovery_plan"] is None
    swept = loads_exact(state_path.read_bytes())
    assert swept["phase"] == "archive-sweep", finished
    record = swept["finalization_reconciliations"][0]
    assert record["status"] == "discarded"
    assert record["superseded_operations"] == chain
    new_chain = swept["finalization_operations"]
    assert new_chain[0]["read_back"]["base"] == git(root, "rev-parse", "HEAD")
    assert new_chain[1]["read_back"]["tree"] == new_chain[1]["intent"]["authority_read_back"]["staged_tree"]
    pushed = new_chain[2]["read_back"]["remote_head"]
    assert git(bare, "rev-parse", f"refs/heads/{finalize_branch(swept)}") == pushed
    committed_inbox = subprocess.run(["git", "-C", str(bare), "show", f"{pushed}:docs/kit-friction-log.md"], check=True, capture_output=True).stdout
    assert HOOK_MARK not in committed_inbox
    assert b"Newer entry." in committed_inbox and b"- **Approved archive.**" not in committed_inbox
    assert subprocess.run(["git", "-C", str(root), "branch", "--contains", ambiguous_commit], capture_output=True, text=True).stdout == ""

    # The operator merges; the merge read-back completes the run.
    runner.merged = True
    completed = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)
    assert completed["disposition"] == "completed", completed
    final = loads_exact(state_path.read_bytes())
    assert final["phase"] == "completed"
    assert final["finalization_reconciliations"] == swept["finalization_reconciliations"]
    canonical_state(state_path.read_bytes(), settings=load_settings(root), mode="live")


def _stranded_engine_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, LocalForge, dict]:
    """A current-fingerprint session held at an ambiguous hooked commit."""
    root, bare = sweep_repository(tmp_path)
    install_hook(root, "pre-commit", PRE_COMMIT)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    runner = LocalForge(bare)
    draft_request, candidate_id = proposal_request(root)
    run("new", context="interactive", request=draft_request, start=root)
    approved, context = approval(loads_exact(state_path.read_bytes()), f"archive {candidate_id}")
    hooked = HookedForge(root, runner)
    run("resume", context="interactive", request={**approved, "finalize": True, "worktree": str(tmp_path / "sweep")},
        start=root, approval_context=context, forge=hooked, head_authority=hooked)
    stranded = loads_exact(state_path.read_bytes())
    assert [item["status"] for item in stranded["finalization_operations"]] == ["verified", "ambiguous"]
    return root, state_path, tmp_path / "sweep", runner, stranded


@pytest.mark.parametrize("leftover", ["remote-branch", "pull-request"])
def test_a_commit_that_may_have_left_the_machine_is_never_discarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, leftover: str
) -> None:
    root, state_path, worktree, runner, stranded = _stranded_engine_state(tmp_path, monkeypatch)
    branch = stranded["finalization_operations"][0]["read_back"]["branch"]
    _leave(root, worktree, runner, leftover, {"branch": branch})
    forge = GitHubForge(root, runner)
    plan = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)
    assert plan["recovery_plan"]["eligible"] is False
    assert plan["waiting_on"] == "reconciliation"
    # Even an approval of that exact plan digest does not discard it.
    plan_digest = plan["recovery_plan"]["plan_digest"]
    again = run(
        "resume", context="interactive",
        request={"finalize": True, "worktree": str(tmp_path / "new"), "commit_reconciliation": local_commit_discard_approval(plan_digest, "operator")},
        start=root, approval_context=_context("discard-local-commit", "plan_digest", plan_digest), forge=forge, head_authority=forge,
    )
    assert again["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["finalization_operations"] == stranded["finalization_operations"]
    assert "finalization_reconciliations" not in loads_exact(state_path.read_bytes())
    assert git(root, "rev-parse", f"refs/heads/{branch}") == stranded["finalization_operations"][1]["read_back"]["commit"]


@pytest.mark.parametrize("fault", ["no-context", "notification-source", "other-digest", "foreign-read-back", "no-worktree", "existing-worktree", "worktree-in-checkout"])
def test_a_discard_needs_the_exact_current_session_approval_of_the_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    root, state_path, worktree, runner, stranded = _stranded_engine_state(tmp_path, monkeypatch)
    forge = GitHubForge(root, runner)
    plan_digest = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)["recovery_plan"]["plan_digest"]
    supplied = local_commit_discard_approval("0" * 64 if fault == "other-digest" else plan_digest, "operator")
    context = None if fault == "no-context" else _context("discard-local-commit", "plan_digest", "f" * 64 if fault == "foreign-read-back" else plan_digest)
    if fault == "notification-source":
        context = ApprovalContext("notification-thread", context.operator_identity, context.source_read_back)
    request = {"finalize": True, "commit_reconciliation": supplied}
    if fault != "no-worktree":
        request["worktree"] = str(tmp_path / "new")
    if fault == "existing-worktree":
        (tmp_path / "new").mkdir()
    if fault == "worktree-in-checkout":
        request["worktree"] = str(root / "sweep-inside-the-checkout")
    result = run("resume", context="interactive", request=request, start=root, approval_context=context, forge=forge, head_authority=forge)
    assert result["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["finalization_operations"] == stranded["finalization_operations"]
    assert "finalization_reconciliations" not in loads_exact(state_path.read_bytes())
    assert git(root, "rev-parse", "--verify", f"refs/heads/{stranded['finalization_operations'][0]['read_back']['branch']}")


def test_a_discard_that_stopped_partway_resumes_without_a_second_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, worktree, runner, stranded = _stranded_engine_state(tmp_path, monkeypatch)
    forge = GitHubForge(root, runner)
    plan_digest = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)["recovery_plan"]["plan_digest"]

    class StopsAfterTheWorktree(GitHubForge):
        def perform(self, action, intent):
            if action == "commit-discard":
                subprocess.run(["git", "-C", str(root), "worktree", "remove", intent["worktree"]], check=True)
                raise TriageError("synthetic stop mid-discard", outcome="operator-held")
            return super().perform(action, intent)

    stopping = StopsAfterTheWorktree(root, runner)
    stopped = run(
        "resume", context="interactive",
        request={"finalize": True, "worktree": str(tmp_path / "new"), "commit_reconciliation": local_commit_discard_approval(plan_digest, "operator")},
        start=root, approval_context=_context("discard-local-commit", "plan_digest", plan_digest), forge=stopping, head_authority=stopping,
    )
    assert stopped["detail"] == "synthetic stop mid-discard"
    mid = loads_exact(state_path.read_bytes())
    assert mid["finalization_reconciliations"][-1]["status"] == "discarding"
    assert session_waiting_on(mid) == "finalize"
    assert mid["finalization_operations"] == stranded["finalization_operations"]
    resumed = run("resume", context="interactive", request={"finalize": True, "worktree": str(tmp_path / "new")}, start=root, forge=forge, head_authority=forge)
    assert loads_exact(state_path.read_bytes())["phase"] == "archive-sweep", resumed
    assert loads_exact(state_path.read_bytes())["finalization_reconciliations"][-1]["status"] == "discarded"


@pytest.mark.parametrize("tamper", ["remote-present-in-plan", "superseded-chain-edited", "superseded-bytes-edited", "approval-digest", "discard-not-proven", "status-not-a-string", "plan-read-back-null"])
def test_a_reconciliation_record_that_does_not_bind_its_evidence_is_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    root, state_path, worktree, runner, stranded = _stranded_engine_state(tmp_path, monkeypatch)
    forge = GitHubForge(root, runner)
    plan_digest = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)["recovery_plan"]["plan_digest"]
    run(
        "resume", context="interactive",
        request={"finalize": True, "worktree": str(tmp_path / "new"), "commit_reconciliation": local_commit_discard_approval(plan_digest, "operator")},
        start=root, approval_context=_context("discard-local-commit", "plan_digest", plan_digest), forge=forge, head_authority=forge,
    )
    state = loads_exact(state_path.read_bytes())
    canonical_state(dumps(state), settings=load_settings(root), mode="live")
    record = state["finalization_reconciliations"][0]
    if tamper == "remote-present-in-plan":
        record["plan"]["read_back"]["remote_branch_absent"] = False
        record["plan_digest"] = digest(record["plan"])
        record["approval"]["plan_digest"] = record["plan_digest"]
    elif tamper == "superseded-chain-edited":
        record["superseded_operations"][1]["status"] = "verified"
    elif tamper == "superseded-bytes-edited":
        # Still an eligible chain; only the plan's digest of it can refuse the edit.
        record["superseded_operations"][1]["response"] = {"stdout": "rewritten history"}
    elif tamper == "approval-digest":
        record["approval"]["plan_digest"] = "0" * 64
    elif tamper == "status-not-a-string":
        record["status"] = ["discarded"]
    elif tamper == "plan-read-back-null":
        # Self-consistent digest and approval over a null read-back.
        record["plan"]["read_back"] = None
        record["plan_digest"] = digest(record["plan"])
        record["approval"]["plan_digest"] = record["plan_digest"]
    else:
        record["discard_read_back"]["local_head"] = record["plan"]["read_back"]["local_head"]
    with pytest.raises(TriageError):
        canonical_state(dumps(state), settings=load_settings(root), mode="live")


def test_the_branch_is_deleted_only_from_the_approved_head(tmp_path: Path) -> None:
    """The delete is a compare-and-delete: a branch that moves between the
    discard's read-back and its delete is kept."""
    root, worktree, runner, operations, request_core = _ambiguous_local_commit(tmp_path)
    expected = operations[1]["read_back"]["commit"]
    branch = request_core["branch"]

    class MovesTheBranchFirst(LocalForge):
        def __call__(self, argv, cwd):
            if argv[:3] == ["git", "update-ref", "-d"]:
                subprocess.run(["git", "-C", str(root), "update-ref", f"refs/heads/{branch}", request_core["base"]], check=True)
            return super().__call__(argv, cwd)

    observed = GitHubForge(root, MovesTheBranchFirst(runner.bare)).perform("commit-discard", {**request_core, "expected_local_head": expected})
    assert observed.status == "failed"
    assert git(root, "rev-parse", f"refs/heads/{branch}") == request_core["base"]


def test_a_discard_the_provider_cannot_prove_stays_discarding_and_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, worktree, runner, stranded = _stranded_engine_state(tmp_path, monkeypatch)
    forge = GitHubForge(root, runner)
    plan_digest = run("resume", context="interactive", request={"finalize": True}, start=root, forge=forge, head_authority=forge)["recovery_plan"]["plan_digest"]

    class Unproven(GitHubForge):
        def perform(self, action, intent):
            observed = super().perform(action, intent)
            if action == "commit-discard":
                return type(observed)("ambiguous", observed.response, {**observed.read_back, "remote_branch_absent": False})
            return observed

    unproven = Unproven(root, runner)
    held = run(
        "resume", context="interactive",
        request={"finalize": True, "worktree": str(tmp_path / "new"), "commit_reconciliation": local_commit_discard_approval(plan_digest, "operator")},
        start=root, approval_context=_context("discard-local-commit", "plan_digest", plan_digest), forge=unproven, head_authority=unproven,
    )
    assert held["outcome"] == "operator-held"
    assert held["capabilities"]["forge-pr-write-readback"]["mechanism"].startswith("local-commit discard did not complete (ambiguous)")
    assert held["waiting_on"] == "reconciliation"
    state = loads_exact(state_path.read_bytes())
    assert state["finalization_reconciliations"][-1]["status"] == "discarding"
    assert state["finalization_operations"] == stranded["finalization_operations"]


def test_a_discard_is_complete_only_once_the_worktree_registration_is_gone() -> None:
    done = {
        "branch": "b", "base": "0" * 40, "worktree": "/w", "paths": PATHS,
        "local_head": None, "local_parents": None, "local_paths": None,
        "worktree_present": False, "worktree_registered": False,
        "worktree_branch": None, "worktree_head": None, "worktree_clean": None,
        "other_checkouts": [], "remote_branch_absent": True, "pull_requests": [],
    }
    assert discard_completed(done, done)
    assert not discard_completed({**done, "worktree_registered": True}, done)



def test_the_discard_never_removes_the_invoking_checkout(tmp_path: Path) -> None:
    root, worktree, runner, operations, request_core = _ambiguous_local_commit(tmp_path)
    observed = GitHubForge(worktree, runner).perform("commit-discard", {**request_core, "expected_local_head": operations[1]["read_back"]["commit"]})
    assert observed.status == "ambiguous"
    assert worktree.exists()


def test_the_read_back_finds_a_recorded_worktree_whose_path_holds_a_newline(tmp_path: Path) -> None:
    root, bare = sweep_repository(tmp_path)
    runner = LocalForge(bare)
    forge = GitHubForge(root, runner)
    base = git(root, "rev-parse", "HEAD")
    worktree = tmp_path / "sweep\nwith a newline"
    assert forge.perform("branch-create", {"repository": REPOSITORY, "branch": "chore/triage-2099-01-01", "worktree": str(worktree), "finalize_base_head": base}).status == "verified"
    read_back = forge.authority("commit-discard-read-back", {"host": "github.com", "repository": REPOSITORY, "branch": "chore/triage-2099-01-01", "base": base, "worktree": str(worktree), "paths": PATHS})
    assert read_back["worktree_registered"] is True
    assert read_back["other_checkouts"] == []
