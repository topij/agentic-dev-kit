"""Linked-worktree repository identity and invocation outcomes (#1103).

Every fixture is a temporary repository, its linked worktrees or clones, and one
temporary state root they share through `DEVKIT_STATE_ROOT`.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from test_triage_engine import (  # noqa: E402
    LIVE_STATE,
    approval_context,
    approval_for,
    change_config,
    completed_live,
    git,
    repository,
    request,
)
from triage.canonical import digest, dumps, loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402
from triage.model import (  # noqa: E402
    load_settings,
    repository_identity,
    repository_identity_matches,
)
from triage.outcome import check_receipt, disposition_fields  # noqa: E402
from triage.providers import FakeForge, FakeTracker, ProviderObservation  # noqa: E402


def linked(root: Path, name: str) -> Path:
    path = root.parent / name
    git(root, "worktree", "add", "--detach", str(path), "HEAD")
    return path


def shared_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    return state_root


def draft_awaiting_approval(root: Path, state_root: Path) -> tuple[dict, bytes]:
    drafted = run("new", context="interactive", request=request(root), start=root)
    assert (drafted["disposition"], drafted["waiting_on"]) == ("waiting", "approval")
    raw = (state_root / LIVE_STATE).read_bytes()
    return loads_exact(raw), raw


DESTINATION = {"backend": "github-issues", "host": "github.com", "repository": "topij/agentic-dev-kit", "project": "topij/agentic-dev-kit"}


def verified_tracker(presented: dict | None = None) -> FakeTracker:
    """A tracker whose create reads back the presented payload exactly."""
    observed: dict = {"number": 40}
    if presented is not None:
        proposal = presented["proposal_payloads"][0]
        observed = {"identifier": "40", "payload": proposal["payload"], "payload_digest": proposal["payload_digest"],
                    "marker": proposal["marker"], "destination": DESTINATION}
    return FakeTracker([], ProviderObservation("verified", {"number": 40}, observed, "created-and-read-back"))


# --- identity -----------------------------------------------------------------


def test_every_worktree_of_one_repository_names_the_primary_checkout(tmp_path: Path) -> None:
    root = repository(tmp_path)
    first = linked(root, "cron-worktree")
    second = linked(root, "later-worktree")
    primary = repository_identity(load_settings(root))
    assert primary["root"] == str(root.resolve())
    assert repository_identity(load_settings(first)) == primary
    assert repository_identity(load_settings(second)) == primary


def test_a_primary_checkout_session_continues_from_a_linked_worktree_through_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The approval binding survives: the operator approves the primary's draft
    from a linked worktree, and the tracker write it authorizes happens."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    presented, _ = draft_awaiting_approval(root, state_root)
    worktree = linked(root, "cron-worktree")
    tracker = verified_tracker(presented)
    result = run(
        "resume", context="interactive", request={"approval": approval_for(presented)}, start=worktree,
        approval_context=approval_context(presented), tracker=tracker, head_authority=FakeForge([]),
    )
    assert result["disposition"] != "refused", result["detail"]
    assert result["verified_tracker_identifiers"] == ["40"]
    assert [call for call, _ in tracker.calls] == ["search", "create"]
    state = loads_exact((state_root / LIVE_STATE).read_bytes())
    assert state["run_identity"] == presented["run_identity"]
    assert state["proposal_payload_digests"] == presented["proposal_payload_digests"]


def test_a_linked_worktree_session_continues_from_a_later_linked_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scheduled case: each run gets a fresh temporary worktree, and the one
    that drafted is gone before the next run resumes."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    first = linked(root, "cron-1")
    presented, raw = draft_awaiting_approval(first, state_root)
    git(root, "worktree", "remove", "--force", str(first))
    second = linked(root, "cron-2")
    result = run(None, context="interactive", request={}, start=second)
    assert (result["disposition"], result["waiting_on"]) == ("waiting", "approval"), result["detail"]
    assert loads_exact((state_root / LIVE_STATE).read_bytes())["run_identity"] == presented["run_identity"]


@pytest.mark.parametrize("drift", [False, True])
def test_a_completed_session_retires_from_a_linked_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift: bool
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    if drift:
        change_config(worktree)
        assert load_settings(worktree).fingerprint != load_settings(root).fingerprint
    result = run(None, context="interactive", request={}, start=worktree)
    assert result["detail"].startswith(f"retired completed state to {retired} ")
    assert (result["disposition"], result["waiting_on"]) == ("waiting", "analysis")
    assert retired.read_bytes() == completed_raw
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"


def test_an_active_session_from_a_linked_worktree_stays_bound_to_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    _, awaiting = draft_awaiting_approval(root, state_root)
    worktree = linked(root, "cron-worktree")
    change_config(worktree)
    tracker = verified_tracker()
    for entry in (None, "resume"):
        held = run(entry, context="unattended", request={}, start=worktree, tracker=tracker)
        assert (held["outcome"], held["disposition"], held["refusal_code"]) == (
            "operator-held", "refused", "configuration-identity"
        )
    assert (state_root / LIVE_STATE).read_bytes() == awaiting
    assert tracker.calls == []


def clone_sharing_remote(root: Path, name: str) -> Path:
    clone = root.parent / name
    git(root.parent, "clone", "--quiet", str(root), str(clone))
    git(clone, "remote", "set-url", "origin", "https://github.com/example/project.git")
    git(clone, "config", "user.email", "test@example.invalid")
    git(clone, "config", "user.name", "Test")
    return clone


@pytest.mark.parametrize("foreign", ["unrelated-clone", "changed-remote"])
def test_a_foreign_checkout_sharing_the_state_root_is_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, foreign: str
) -> None:
    """An equal origin URL and a shared state directory do not make two clones
    one repository; a changed remote is not the same repository either."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    presented, awaiting = draft_awaiting_approval(root, state_root)
    if foreign == "unrelated-clone":
        other = clone_sharing_remote(root, "independent-clone")
        assert repository_identity(load_settings(other))["remote"] == presented["run_identity"]["repository_identity"]["remote"]
    else:
        other = linked(root, "cron-worktree")
        git(root, "remote", "set-url", "origin", "https://github.com/example/renamed.git")
    tracker = verified_tracker()
    for entry in (None, "resume"):
        held = run(
            entry, context="interactive", request={"approval": approval_for(presented)}, start=other,
            approval_context=approval_context(presented), tracker=tracker, head_authority=FakeForge([]),
        )
        assert (held["outcome"], held["disposition"], held["refusal_code"]) == (
            "operator-held", "refused", "repository-identity"
        ), held["detail"]
    assert (state_root / LIVE_STATE).read_bytes() == awaiting
    assert tracker.calls == []
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()


def test_invalid_state_read_from_a_linked_worktree_is_held_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    presented, _ = draft_awaiting_approval(root, state_root)
    corrupted = dumps({**presented, "frozen_inbox_digest": "0" * 64})
    (state_root / LIVE_STATE).write_bytes(corrupted)
    worktree = linked(root, "cron-worktree")
    held = run(None, context="unattended", request={}, start=worktree)
    assert held["disposition"] == "refused"
    assert (state_root / LIVE_STATE).read_bytes() == corrupted


# --- identities recorded before #1103 -------------------------------------------


def test_a_pre_1103_linked_worktree_identity_continues_while_that_worktree_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before #1103 a linked worktree recorded its own root. The stored identity is
    compared, never rewritten; it continues while membership can be proven, holds
    once the worktree is gone, and continues again when one is re-added there."""
    import triage.model as model

    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    old = linked(root, "old-cron-worktree")
    with monkeypatch.context() as before_1103:
        before_1103.setattr(model, "canonical_repository_root", lambda repo: str(repo))
        presented, legacy = draft_awaiting_approval(old, state_root)
    assert presented["run_identity"]["repository_identity"]["root"] == str(old.resolve())
    report = Path(presented["proposal_payloads"][0]["report_binding"]["path"])
    assert report.is_relative_to(old.resolve())

    continued = run(None, context="unattended", request={}, start=root)
    assert (continued["disposition"], continued["waiting_on"]) == ("waiting", "approval"), continued["detail"]
    assert loads_exact((state_root / LIVE_STATE).read_bytes())["run_identity"] == presented["run_identity"]

    git(root, "worktree", "remove", "--force", str(old))
    before = (state_root / LIVE_STATE).read_bytes()
    held = run(None, context="unattended", request={}, start=root)
    assert (held["disposition"], held["refusal_code"]) == ("refused", "repository-identity")
    assert (state_root / LIVE_STATE).read_bytes() == before
    assert not old.exists()

    git(root, "worktree", "add", "--detach", str(old), "HEAD")
    restored = run(None, context="unattended", request={}, start=root)
    assert (restored["disposition"], restored["waiting_on"]) == ("waiting", "approval"), restored["detail"]


def test_a_linked_worktree_draft_writes_its_report_in_the_primary_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A temporary worktree's report would vanish with it; the report lives
    below the root the run identity names."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    presented, _ = draft_awaiting_approval(worktree, state_root)
    report = Path(presented["proposal_payloads"][0]["report_binding"]["path"])
    assert report.is_relative_to(root.resolve() / "reports")
    assert report.exists()
    assert not (worktree / "reports").exists()


def current(root: Path) -> dict:
    return repository_identity(load_settings(root))


def test_membership_requires_an_absolute_worktree_top_level_of_this_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    worktree = linked(root, "member")
    identity = current(root)
    remote = identity["remote"]
    assert repository_identity_matches({"root": str(worktree), "remote": remote}, identity)
    # The primary under a different spelling: a symlink to it.
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    assert repository_identity_matches({"root": str(alias), "remote": remote}, identity)
    # Each of these shares the shape but is not this repository's worktree.
    nested = root / "nested"
    nested.mkdir()
    git(nested, "init", "-q", "-b", "main")
    bare = tmp_path / "bare.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    clone = clone_sharing_remote(root, "clone")
    for rejected in (
        {"root": str(root / "docs"), "remote": remote},           # subdirectory
        {"root": "repo", "remote": remote},                        # relative
        {"root": str(nested), "remote": remote},                   # nested repository
        {"root": str(bare), "remote": remote},                     # bare repository
        {"root": str(clone), "remote": remote},                    # unrelated clone
        {"root": str(tmp_path / "gone"), "remote": remote},        # removed path
        {"root": str(worktree), "remote": remote + ".other"},      # other remote
        {"root": str(worktree), "remote": remote, "extra": "x"},   # malformed
        str(worktree),                                             # malformed
    ):
        assert not repository_identity_matches(rejected, identity), rejected
    # Relative even where the current directory would resolve it to the root.
    monkeypatch.chdir(tmp_path)
    assert not repository_identity_matches({"root": "repo", "remote": remote}, identity)


def test_a_caller_git_dir_does_not_make_a_foreign_root_a_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hook exports GIT_DIR; with it inherited, `git -C <anything>` would report
    this repository and every recorded root would pass."""
    root = repository(tmp_path)
    identity = current(root)
    clone = clone_sharing_remote(root, "clone")
    # With both inherited, git reports the clone as a worktree of this repository.
    monkeypatch.setenv("GIT_DIR", str(root / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(clone))
    assert not repository_identity_matches({"root": str(clone), "remote": identity["remote"]}, identity)


def test_a_linked_worktree_whose_gitfile_is_broken_names_no_repository(tmp_path: Path) -> None:
    """Moving the primary moves the common dir the worktree's gitfile points
    into, so the worktree is no Git worktree at all."""
    from triage.model import TriageError, canonical_repository_root

    root = repository(tmp_path)
    worktree = linked(root, "member")
    shutil.move(str(root), str(tmp_path / "moved"))
    with pytest.raises(TriageError, match="not a Git worktree") as raised:
        canonical_repository_root(worktree)
    assert raised.value.code == "repository-identity"


def test_a_linked_worktree_of_a_bare_repository_names_itself(tmp_path: Path) -> None:
    root = repository(tmp_path)
    bare = tmp_path / "bare.git"
    git(tmp_path, "clone", "--quiet", "--bare", str(root), str(bare))
    git(bare, "remote", "set-url", "origin", "https://github.com/example/project.git")
    git(bare, "update-ref", "refs/remotes/origin/main", "HEAD")
    worktree = tmp_path / "bare-worktree"
    git(bare, "worktree", "add", "--detach", str(worktree), "HEAD")
    assert current(worktree)["root"] == str(worktree.resolve())


def test_a_separate_git_dir_primary_s_linked_worktree_names_itself_and_continues_by_membership(
    tmp_path: Path,
) -> None:
    """Git reports a `--separate-git-dir` primary's git dir as the main worktree.
    That is no checkout, so the linked worktree names itself, as before #1103,
    and still matches the primary's identity through membership."""
    root = repository(tmp_path)
    separate = tmp_path / "separate.git"
    shutil.move(str(root / ".git"), str(separate))
    (root / ".git").write_text(f"gitdir: {separate}\n", encoding="utf-8")
    primary = current(root)
    assert primary["root"] == str(root.resolve())
    worktree = linked(root, "member")
    assert current(worktree)["root"] == str(worktree.resolve())
    assert repository_identity_matches(primary, current(worktree))


# --- dispositions -----------------------------------------------------------------


@pytest.mark.parametrize("outcome, waiting_on, refusal_code, expected", [
    ("successful-completion", None, None, ("completed", None, None)),
    ("degraded-success", "approval", "active-state", ("completed", None, None)),
    ("operator-held", "approval", None, ("waiting", "approval", None)),
    ("operator-held", None, None, ("refused", None, "unclassified")),
    ("operator-held", "not-a-wait", None, ("refused", None, "unclassified")),
    ("operator-held", None, "repository-identity", ("refused", None, "repository-identity")),
    ("hard-stop", "approval", "not-a-code", ("refused", None, "unclassified")),
])
def test_dispositions_are_derived_and_refused_unless_a_wait_is_named(outcome, waiting_on, refusal_code, expected) -> None:
    fields = disposition_fields(outcome, waiting_on=waiting_on, refusal_code=refusal_code)
    assert (fields["disposition"], fields["waiting_on"], fields["refusal_code"]) == expected


def test_only_resumable_phases_are_waits() -> None:
    """`propose` (an unattended draft with no notification provider) has no
    continuation and `completed` is not a wait; every other phase names one."""
    from triage.model import PHASES
    from triage.outcome import PHASE_WAITING_ON

    assert PHASE_WAITING_ON == {
        "reserved": "analysis",
        "notification-delivery": "notification-delivery",
        "awaiting-approval": "approval",
        "tracker-write": "tracker-write",
        "forge-finalize": "finalize",
        "archive-sweep": "finalize",
    }
    assert set(PHASES) - set(PHASE_WAITING_ON) == {"propose", "completed"}


def test_an_empty_inbox_draft_is_a_completed_no_op(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(b"# Log\n")
    git(root, "commit", "-qam", "empty inbox")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    shared_state(tmp_path, monkeypatch)
    result = run(None, context="unattended", request={}, start=linked(root, "cron-worktree"))
    assert (result["outcome"], result["disposition"]) == ("successful-completion", "completed")


# --- invocation receipts through the CLI --------------------------------------------


def load_cli(monkeypatch: pytest.MonkeyPatch, start: Path):
    spec = importlib.util.spec_from_file_location("triage_cli_receipts", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    real_run = cli.run
    monkeypatch.setattr(cli, "run", lambda *args, **kwargs: real_run(*args, **{**kwargs, "start": start}))
    for name in (cli.RECEIPT_ENV, cli.INVOCATION_ENV):
        monkeypatch.delenv(name, raising=False)
    return cli


def check(cli, receipt: Path, invocation: str, *extra: str, capsys) -> tuple[int, dict]:
    capsys.readouterr()
    status = cli.main(["--check-outcome-receipt", str(receipt), "--invocation-id", invocation, *extra])
    return status, loads_exact(capsys.readouterr().out.strip().encode())


def test_receipts_separate_refusal_pending_approval_and_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    receipt = tmp_path / "receipts" / "triage.json"

    # Missing: nothing ran under this invocation.
    cli = load_cli(monkeypatch, worktree)
    status, verdict = check(cli, receipt, "run-1", capsys=capsys)
    assert (status, verdict["verdict"]) == (2, "evidence-missing")

    # Pending approval, set through the environment as a scheduled wrapper does.
    request_path = tmp_path / "request.json"
    request_path.write_bytes(dumps(request(root)))
    monkeypatch.setenv(cli.RECEIPT_ENV, str(receipt))
    monkeypatch.setenv(cli.INVOCATION_ENV, "run-1")
    assert cli.main(["new", "--context", "interactive", "--request", str(request_path)]) == 0
    monkeypatch.delenv(cli.RECEIPT_ENV)
    monkeypatch.delenv(cli.INVOCATION_ENV)
    status, verdict = check(cli, receipt, "run-1", "--expect-context", "interactive", "--expect-mode", "live", capsys=capsys)
    assert (status, verdict["verdict"], verdict["waiting_on"], verdict["sequence"]) == (0, "waiting", "approval", 1)

    # Stale: the next invocation finds the last one's receipt.
    status, verdict = check(cli, receipt, "run-2", capsys=capsys)
    assert (status, verdict["verdict"]) == (2, "evidence-stale")

    # Wrong invocation: right id, another context than the caller started.
    status, verdict = check(cli, receipt, "run-1", "--expect-context", "unattended", capsys=capsys)
    assert (status, verdict["verdict"]) == (2, "evidence-wrong-invocation")

    # Refused: an identity refusal exits 0 from the engine CLI but is a failure here.
    clone = clone_sharing_remote(root, "independent-clone")
    cli = load_cli(monkeypatch, clone)
    assert cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-2", "resume", "--context", "unattended"]) == 0
    status, verdict = check(cli, receipt, "run-2", "--expect-context", "unattended", capsys=capsys)
    assert (status, verdict["verdict"], verdict["refusal_code"], verdict["sequence"]) == (1, "refused", "repository-identity", 1)
    assert verdict["outcome"] == "operator-held"

    # A second call under one invocation replaces the receipt and counts it.
    assert cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-2", "resume", "--context", "unattended"]) == 0
    assert check(cli, receipt, "run-2", capsys=capsys)[1]["sequence"] == 2

    # Completed no-op: with no active state and an emptied inbox, a fresh draft finds
    # no candidates.
    state = state_root / LIVE_STATE
    state.unlink()
    (worktree / "docs/kit-friction-log.md").write_bytes(b"# Log\n")
    cli = load_cli(monkeypatch, worktree)
    assert cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-3", "--context", "unattended"]) == 0
    status, verdict = check(cli, receipt, "run-3", "--expect-context", "unattended", capsys=capsys)
    assert (status, verdict["verdict"], verdict["outcome"]) == (0, "completed", "successful-completion")


def test_a_call_that_dies_leaves_no_receipt_rather_than_the_last_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repository(tmp_path)
    shared_state(tmp_path, monkeypatch)
    receipt = tmp_path / "triage.json"
    cli = load_cli(monkeypatch, root)
    request_path = tmp_path / "request.json"
    request_path.write_bytes(dumps(request(root)))
    assert cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-1", "new", "--request", str(request_path)]) == 0
    assert check(cli, receipt, "run-1", capsys=capsys)[1]["verdict"] == "waiting"

    def crash(*args, **kwargs):
        raise RuntimeError("killed mid-run")

    monkeypatch.setattr(cli, "run", crash)
    with pytest.raises(RuntimeError):
        cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-1", "resume"])
    status, verdict = check(cli, receipt, "run-1", capsys=capsys)
    assert (status, verdict["verdict"]) == (2, "evidence-missing")


def test_a_receipt_path_holding_another_file_is_refused_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = []
    spec = importlib.util.spec_from_file_location("triage_cli_foreign", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(cli, "run", lambda *a, **k: calls.append(a))
    target = tmp_path / "notes.md"
    target.write_bytes(b"PRECIOUS\n")
    assert cli.main(["resume", "--outcome-receipt", str(target), "--invocation-id", "run-1"]) == 2
    printed = loads_exact(capsys.readouterr().out.strip().encode())
    assert "not a triage outcome receipt" in printed["detail"]
    assert target.read_bytes() == b"PRECIOUS\n"
    assert calls == []


@pytest.mark.parametrize("tamper", ["digest", "disposition", "shape", "not-json"])
def test_a_tampered_receipt_is_malformed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tamper: str
) -> None:
    root = repository(tmp_path)
    shared_state(tmp_path, monkeypatch)
    receipt = tmp_path / "triage.json"
    cli = load_cli(monkeypatch, root)
    assert cli.main(["--outcome-receipt", str(receipt), "--invocation-id", "run-1", "resume"]) == 2
    assert check(cli, receipt, "run-1", capsys=capsys)[1]["verdict"] == "refused"
    value = loads_exact(receipt.read_bytes())
    if tamper == "digest":
        value["result"]["detail"] = "rewritten"
    elif tamper == "disposition":
        value["disposition"] = value["result"]["disposition"] = "completed"
        value["result_digest"] = digest(value["result"])
    elif tamper == "shape":
        value["extra"] = True
    receipt.write_bytes(b"{" if tamper == "not-json" else dumps(value))
    status, verdict = check(cli, receipt, "run-1", capsys=capsys)
    assert (status, verdict["verdict"]) == (2, "evidence-malformed")


@pytest.mark.parametrize("arguments, reason", [
    (["--outcome-receipt", "relative.json", "--invocation-id", "run-1"], "absolute"),
    (["--invocation-id", "run-1"], "both"),
    (["--outcome-receipt", "/tmp/x.json", "--invocation-id", "bad id"], "invocation id"),
])
def test_a_receipt_that_cannot_be_bound_is_refused_before_the_engine_runs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], arguments: list[str], reason: str
) -> None:
    calls = []
    spec = importlib.util.spec_from_file_location("triage_cli_unbound", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(cli, "run", lambda *a, **k: calls.append(a))
    monkeypatch.delenv(cli.RECEIPT_ENV, raising=False)
    monkeypatch.delenv(cli.INVOCATION_ENV, raising=False)
    assert cli.main(["resume", *arguments]) == 2
    printed = loads_exact(capsys.readouterr().out.strip().encode())
    assert reason in printed["detail"]
    assert (printed["disposition"], printed["refusal_code"]) == ("refused", "invalid-invocation")
    assert calls == []


def test_check_receipt_refuses_an_invalid_expected_invocation_id(tmp_path: Path) -> None:
    from triage.model import TriageError

    with pytest.raises(TriageError):
        check_receipt(tmp_path / "x.json", invocation_id="bad id")
