"""Linked-worktree repository identity and invocation outcomes (#1103).

Every fixture is a temporary repository, its linked worktrees or clones, and one
temporary state root they share through `DEVKIT_STATE_ROOT`.
"""

from __future__ import annotations

import importlib.util
import os
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
from triage.canonical import dumps, loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402
from triage.model import (  # noqa: E402
    load_settings,
    repository_identity,
    repository_identity_matches,
)
from triage.outcome import disposition_fields  # noqa: E402
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


def test_a_pre_1103_linked_worktree_identity_is_held_for_recover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before #1103 a linked worktree recorded its own root. The recorded root is
    never probed: such an identity does not equal the main worktree's, so the
    session holds with `repository-identity`, its bytes unchanged, and the refusal
    names interactive `recover` as the way to retire it."""
    import triage.model as model

    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    old = linked(root, "old-cron-worktree")
    with monkeypatch.context() as before_1103:
        before_1103.setattr(model, "canonical_repository_root", lambda repo: str(repo))
        presented, legacy = draft_awaiting_approval(old, state_root)
    assert presented["run_identity"]["repository_identity"]["root"] == str(old.resolve())
    for start in (root, old):
        held = run(None, context="unattended", request={}, start=start)
        assert (held["disposition"], held["refusal_code"]) == ("refused", "repository-identity"), held["detail"]
        assert "retired with interactive recover" in held["resume_action"]
        assert (state_root / LIVE_STATE).read_bytes() == legacy
        assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()


def test_a_corrupted_recorded_root_is_refused_not_probed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A root with a NUL byte crashed the old membership probe with the gate held;
    with equality only, it is an ordinary identity refusal."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    presented, _ = draft_awaiting_approval(root, state_root)
    identity = {**presented["run_identity"]["repository_identity"], "root": "/tmp/a\u0000b"}
    corrupted = dumps({**presented, "run_identity": {**presented["run_identity"], "repository_identity": identity}})
    (state_root / LIVE_STATE).write_bytes(corrupted)
    held = run(None, context="unattended", request={}, start=root)
    assert (held["disposition"], held["refusal_code"]) == ("refused", "repository-identity")
    assert (state_root / LIVE_STATE).read_bytes() == corrupted
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()


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


def test_identities_match_by_equality_only(tmp_path: Path) -> None:
    root = repository(tmp_path)
    worktree = linked(root, "member")
    identity = current(root)
    assert repository_identity_matches(dict(identity), identity)
    for rejected in (
        {"root": str(worktree), "remote": identity["remote"]},          # another worktree's root
        {"root": str(root / "docs"), "remote": identity["remote"]},     # subdirectory
        {**identity, "remote": identity["remote"] + ".other"},          # other remote
        {**identity, "extra": "x"},                                     # malformed
        str(root),                                                      # malformed
    ):
        assert not repository_identity_matches(rejected, identity), rejected


def test_a_caller_git_dir_does_not_change_the_current_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hook exports GIT_DIR; with it inherited, the probes of a clone would
    describe this repository instead."""
    root = repository(tmp_path)
    clone = clone_sharing_remote(root, "clone")
    git(clone, "remote", "set-url", "origin", "https://github.com/example/clone.git")
    expected = current(clone)
    monkeypatch.setenv("GIT_DIR", str(root / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(root))
    assert current(clone) == expected


def test_configuration_variables_still_apply_to_the_recorded_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the variables that relocate a repository are dropped; a remote that
    git rewrites through `url.<base>.insteadOf` from the environment reads as git
    reports it, as it did when an identity was recorded."""
    root = repository(tmp_path)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url.git@github.com:.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "https://github.com/")
    assert current(root)["remote"] == git(root, "remote", "get-url", "origin")
    assert current(root)["remote"] == "git@github.com:example/project.git"


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


def test_a_separate_git_dir_primary_s_linked_worktree_names_itself(tmp_path: Path) -> None:
    """Git reports a `--separate-git-dir` primary's git dir as the main worktree.
    That is no checkout, so the linked worktree names itself, as before #1103,
    and does not continue the primary's sessions."""
    root = repository(tmp_path)
    separate = tmp_path / "separate.git"
    shutil.move(str(root / ".git"), str(separate))
    (root / ".git").write_text(f"gitdir: {separate}\n", encoding="utf-8")
    primary = current(root)
    assert primary["root"] == str(root.resolve())
    worktree = linked(root, "member")
    assert current(worktree)["root"] == str(worktree.resolve())
    assert not repository_identity_matches(primary, current(worktree))


def test_gate_and_gate_only_evidence_match_identities_by_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate record and gate-only state evidence compare repository identity
    by the same equality rule as the state, and refuse with codes."""
    from triage.canonical import dumps as canonical_dumps
    from triage.engine import _gate_only_state_value
    from triage.gate import acquire, validate_record
    from triage.model import TriageError
    from triage.storage import ArtifactStore

    root = repository(tmp_path)
    shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "old-cron-worktree")
    settings = load_settings(root)
    store = ArtifactStore(settings, "live")
    legacy = {"root": str(worktree.resolve()), "remote": current(root)["remote"]}
    lease = acquire(store, repository_identity=current(worktree), config_fingerprint=settings.fingerprint, run_identity=None)
    record = lease.record
    lease.release()
    assert validate_record(record, repository_identity=current(root), config_fingerprint=settings.fingerprint) == record
    clone = clone_sharing_remote(root, "independent-clone")
    for foreign_identity in (current(clone), legacy):
        with pytest.raises(TriageError) as foreign:
            validate_record(record, repository_identity=foreign_identity, config_fingerprint=settings.fingerprint)
        assert foreign.value.code == "repository-identity"
    with pytest.raises(TriageError) as drifted:
        validate_record(record, repository_identity=current(root), config_fingerprint="0" * 64)
    assert drifted.value.code == "configuration-identity"

    digest_text = "a" * 64
    intent = {
        "kind": "gate-only-recovery-intent",
        "schema_version": 1,
        "prepared_core_digest": "b" * 64,
        "old_gate_digest": digest_text,
        "configured_bundle_path": str(store.recovery_path(digest_text)),
        "repository_identity": current(worktree),
        "mode": "live",
        "replacement_gate_run_identity": {"kind": "gate-only-recovery", "mode": "live", "prepared_core_digest": "b" * 64},
    }
    assert _gate_only_state_value(store, canonical_dumps(intent)) == intent
    for foreign_identity in (current(clone), legacy):
        foreign_intent = {**intent, "repository_identity": foreign_identity}
        with pytest.raises(TriageError) as held:
            _gate_only_state_value(store, canonical_dumps(foreign_intent))
        assert held.value.code == "repository-identity"


def test_an_unattended_run_over_a_reserved_session_waits_on_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    shared_state(tmp_path, monkeypatch)
    run("new", context="interactive", request={}, start=root)
    waiting = run(None, context="unattended", request={}, start=linked(root, "cron-worktree"))
    assert (waiting["outcome"], waiting["disposition"], waiting["waiting_on"]) == ("operator-held", "waiting", "analysis")


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


def test_refusal_codes_name_a_missing_origin_an_active_state_and_an_unattended_recover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    shared_state(tmp_path, monkeypatch)
    unattended = run("recover", context="unattended", request={}, start=root)
    assert (unattended["disposition"], unattended["refusal_code"]) == ("refused", "invalid-invocation")
    run("new", context="interactive", request=request(root), start=root)
    again = run("new", context="interactive", request={}, start=root)
    assert (again["disposition"], again["refusal_code"]) == ("refused", "active-state")
    git(root, "remote", "remove", "origin")
    orphan = run(None, context="interactive", request={}, start=root)
    assert (orphan["outcome"], orphan["refusal_code"]) == ("hard-stop", "repository-identity")


def test_an_empty_inbox_draft_is_a_completed_no_op(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(b"# Log\n")
    git(root, "commit", "-qam", "empty inbox")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    shared_state(tmp_path, monkeypatch)
    result = run(None, context="unattended", request={}, start=linked(root, "cron-worktree"))
    assert (result["outcome"], result["disposition"]) == ("successful-completion", "completed")


# --- report root -------------------------------------------------------------------


# A root user writes through mode bits, so a permission refusal cannot be staged.
needs_unprivileged = pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores directory mode bits"
)


@needs_unprivileged
def test_an_unwritable_report_root_refuses_before_any_state_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The report is written in the primary checkout; an unwritable report root
    used to fail after the reservation and leave the gate held."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    reports = root / "reports"
    reports.mkdir()
    reports.chmod(0o555)
    try:
        refused = run("new", context="interactive", request=request(root), start=worktree)
        assert (refused["outcome"], refused["disposition"]) == ("hard-stop", "refused")
        assert "report directory is not writable" in refused["detail"]
        assert not (state_root / LIVE_STATE).exists()
        assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    finally:
        reports.chmod(0o755)
    drafted = run("new", context="interactive", request=request(root), start=worktree)
    assert (drafted["disposition"], drafted["waiting_on"]) == ("waiting", "approval")


@needs_unprivileged
def test_an_analysis_resume_checks_the_report_root_before_it_advances_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    frozen = run("new", context="interactive", request={}, start=worktree)
    assert frozen["waiting_on"] == "analysis"
    reserved = (state_root / LIVE_STATE).read_bytes()
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    reports.chmod(0o555)
    try:
        refused = run("resume", context="interactive", request=request(root), start=worktree)
        assert (refused["outcome"], refused["disposition"]) == ("hard-stop", "refused")
        assert "report directory is not writable" in refused["detail"]
        # Checked before the rebind: the state is byte-for-byte unchanged.
        assert (state_root / LIVE_STATE).read_bytes() == reserved
        assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    finally:
        reports.chmod(0o755)
    resumed = run("resume", context="interactive", request=request(root), start=worktree)
    assert (resumed["disposition"], resumed["waiting_on"]) == ("waiting", "approval")


@needs_unprivileged
def test_an_approval_resume_checks_the_report_root_before_it_advances_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later phase rewrites the bound report too; an unwritable root refuses
    cleanly before the session moves, rather than raising with the gate held."""
    root = repository(tmp_path)
    state_root = shared_state(tmp_path, monkeypatch)
    worktree = linked(root, "cron-worktree")
    presented, _ = draft_awaiting_approval(worktree, state_root)
    tracker = verified_tracker(presented)
    reports = root / "reports"
    reports.chmod(0o555)
    try:
        refused = run(
            "resume", context="interactive", request={"approval": approval_for(presented)}, start=worktree,
            approval_context=approval_context(presented), tracker=tracker, head_authority=FakeForge([]),
        )
        assert (refused["outcome"], refused["disposition"]) == ("hard-stop", "refused")
        assert "report directory is not writable" in refused["detail"]
        assert loads_exact((state_root / LIVE_STATE).read_bytes())["phase"] == "awaiting-approval"
        assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
        assert tracker.calls == []
    finally:
        reports.chmod(0o755)


def test_a_cli_hard_stop_carries_a_refusal_disposition(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("triage_cli_disposition", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.main(["resume", "--request", str(tmp_path / "missing.json")]) == 2
    printed = loads_exact(capsys.readouterr().out.strip().encode())
    assert (printed["outcome"], printed["disposition"], printed["refusal_code"]) == ("hard-stop", "refused", "invalid-invocation")
    assert printed["waiting_on"] is None
