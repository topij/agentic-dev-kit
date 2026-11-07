"""#1303: `config_fingerprint` covers only the configuration the triage engines
read, and a session recorded under the old whole-config fingerprint has an
approval-bound way to rebind to it."""

from __future__ import annotations

import ast
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from kitconfig import get  # noqa: E402
from test_finalize_triage import proposal_request, repository  # noqa: E402
from triage.approval import ApprovalContext  # noqa: E402
from triage.canonical import digest, dumps, loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402
from triage.model import (  # noqa: E402
    FINGERPRINT_KEYS,
    VALIDATION_ONLY_KEYS,
    TriageError,
    canonical_state,
    config_rebind_approval,
    legacy_fingerprint,
    load_settings,
    scoped_fingerprint,
)


def test_the_fingerprint_scope_is_exactly_what_load_settings_reads() -> None:
    """Every key `load_settings` reads is fingerprinted or declared
    validation-only, and nothing else is: a key read later cannot be missed."""
    source = (ENGINE_DIR / "lib/triage/model.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    load_settings_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "load_settings")
    read = {
        call.args[1].value
        for call in ast.walk(load_settings_node)
        if isinstance(call, ast.Call) and getattr(call.func, "id", None) == "_required"
        and len(call.args) == 2 and isinstance(call.args[1], ast.Constant)
    }
    assert read, "no _required calls found in load_settings"
    assert read == set(FINGERPRINT_KEYS) | set(VALIDATION_ONLY_KEYS)
    assert not set(FINGERPRINT_KEYS) & set(VALIDATION_ONLY_KEYS)


def _config(tmp_path: Path) -> dict:
    return load_settings(repository(tmp_path)).config


def _set(config: dict, dotted: str, value: object) -> dict:
    changed = deepcopy(config)
    node = changed
    *parents, leaf = dotted.split(".")
    for name in parents:
        node = node[name]
    node[leaf] = value
    return changed


@pytest.mark.parametrize("key", FINGERPRINT_KEYS)
def test_every_read_key_moves_the_fingerprint(tmp_path: Path, key: str) -> None:
    config = _config(tmp_path)
    assert scoped_fingerprint(_set(config, key, ["changed", get(config, key)])) != scoped_fingerprint(config)


@pytest.mark.parametrize("key", ["review.bot_pending_grace_minutes", "review.bots", "vcs.systemize_branch_pattern", "vcs.forge", "models.tiers.default", "state.test_guard_exclude"])
def test_an_unread_key_leaves_the_fingerprint_unchanged(tmp_path: Path, key: str) -> None:
    config = _config(tmp_path)
    changed = _set(config, key, "changed")
    assert legacy_fingerprint(changed) != legacy_fingerprint(config)
    assert scoped_fingerprint(changed) == scoped_fingerprint(config)


def test_the_scoped_fingerprint_never_equals_the_whole_config_digest(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert scoped_fingerprint(config) != legacy_fingerprint(config)
    assert scoped_fingerprint(config) != digest({key: get(config, key) for key in FINGERPRINT_KEYS})


def _held_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, legacy: bool) -> tuple[Path, Path, bytes]:
    """A live session waiting for approval, drafted under the current or the
    legacy whole-config fingerprint."""
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_live.json"
    with monkeypatch.context() as engine:
        if legacy:
            engine.setattr("triage.model.scoped_fingerprint", legacy_fingerprint)
        draft_request, _ = proposal_request(root)
        run("new", context="interactive", request=draft_request, start=root)
    raw = state_path.read_bytes()
    assert loads_exact(raw)["phase"] == "awaiting-approval"
    return root, state_path, raw


def _edit(root: Path, before: str, after: str) -> None:
    config = root / "config/dev-model.yaml"
    text = config.read_text(encoding="utf-8")
    assert before in text
    config.write_text(text.replace(before, after), encoding="utf-8")


UNREAD = ("bot_pending_grace_minutes: 15", "bot_pending_grace_minutes: 30")
READ = ('commit_subject: "docs(triage): graduate friction-log entries"', 'commit_subject: "docs(triage): another subject"')


def test_a_held_session_resumes_after_an_unread_key_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=False)
    _edit(root, *UNREAD)
    result = run("resume", context="interactive", request={}, start=root)
    assert result["refusal_code"] is None, result
    assert result["waiting_on"] == "approval"
    canonical_state(state_path.read_bytes(), settings=load_settings(root), mode="live")


def test_a_held_session_is_refused_after_a_read_key_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=False)
    _edit(root, *READ)
    result = run("resume", context="interactive", request={}, start=root)
    assert result["refusal_code"] == "configuration-identity"
    assert state_path.read_bytes() == raw


def _legacy_config_file(tmp_path: Path, root: Path) -> Path:
    path = tmp_path / "legacy-dev-model.yaml"
    path.write_bytes(subprocess.run(["git", "-C", str(root), "show", "HEAD:config/dev-model.yaml"], check=True, capture_output=True).stdout)
    return path


def _approve(core_digest: str, *, read_back_digest: str | None = None) -> tuple[dict, ApprovalContext]:
    return (
        config_rebind_approval(core_digest, "operator"),
        ApprovalContext("current-session", "operator", {"decision": "rebind-config", "core_digest": read_back_digest or core_digest, "approver_identity": "operator"}),
    )


def test_a_legacy_session_is_refused_until_rebound_then_resumes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=True)
    _edit(root, *UNREAD)
    assert run("resume", context="interactive", request={}, start=root)["refusal_code"] == "configuration-identity"
    spec = {"legacy_config": str(_legacy_config_file(tmp_path, root)), "legacy_local_config": None}
    planned = run("resume", context="interactive", request={"config_rebind": spec}, start=root)
    assert planned["waiting_on"] == "recovery-approval"
    assert state_path.read_bytes() == raw
    approval, context = _approve(planned["recovery_plan"]["core_digest"])
    rebound = run("resume", context="interactive", request={"config_rebind": {**spec, "approval": approval}}, start=root, approval_context=context)
    assert rebound["waiting_on"] == "approval", rebound
    state = loads_exact(state_path.read_bytes())
    assert {key: value for key, value in state.items() if key not in {"config_rebind", "gate_owner_token", "gate_binding", "state_claim"}} == {
        key: value for key, value in loads_exact(raw).items() if key not in {"gate_owner_token", "gate_binding", "state_claim"}
    }
    # Later resumes need nothing more; a second rebind is refused.
    assert run("resume", context="interactive", request={}, start=root)["waiting_on"] == "approval"
    again = run("resume", context="interactive", request={"config_rebind": spec}, start=root)
    assert again["refusal_code"] == "configuration-identity" and "already rebound" in again["detail"]
    # A read key changing after the rebind still refuses the session.
    _edit(root, *READ)
    assert run("resume", context="interactive", request={}, start=root)["refusal_code"] == "configuration-identity"


@pytest.mark.parametrize("fault", ["other-bytes", "read-key-changed", "local-overlay-missing"])
def test_a_rebind_requires_the_drafted_configuration_and_an_unchanged_read_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=True)
    legacy = _legacy_config_file(tmp_path, root)
    spec = {"legacy_config": str(legacy), "legacy_local_config": None}
    if fault == "other-bytes":
        # Bytes that are not the drafted configuration do not reproduce its digest.
        legacy.write_text(legacy.read_text(encoding="utf-8").replace("bot_pending_grace_minutes: 15", "bot_pending_grace_minutes: 16"), encoding="utf-8")
        expected = "does not reproduce the session's recorded fingerprint"
    elif fault == "read-key-changed":
        _edit(root, *READ)
        expected = "changed since the session was drafted: triage.commit_subject"
    else:
        overlay = tmp_path / "legacy-dev-model.local.yaml"
        overlay.write_text('notify:\n  user_key: "U123"\n', encoding="utf-8")
        spec["legacy_local_config"] = str(overlay)
        expected = "does not reproduce the session's recorded fingerprint"
    result = run("resume", context="interactive", request={"config_rebind": spec}, start=root)
    assert result["refusal_code"] == "configuration-identity", result
    assert expected in result["detail"]
    assert result["recovery_plan"] is None
    assert state_path.read_bytes() == raw


@pytest.mark.parametrize("fault", ["no-context", "notification-source", "other-digest", "foreign-read-back", "not-resume"])
def test_a_rebind_needs_the_exact_current_session_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=True)
    spec = {"legacy_config": str(_legacy_config_file(tmp_path, root)), "legacy_local_config": None}
    core_digest = run("resume", context="interactive", request={"config_rebind": spec}, start=root)["recovery_plan"]["core_digest"]
    approval, context = _approve("0" * 64 if fault == "other-digest" else core_digest, read_back_digest="f" * 64 if fault == "foreign-read-back" else None)
    if fault == "notification-source":
        context = ApprovalContext("notification-thread", context.operator_identity, context.source_read_back)
    result = run(
        None if fault == "not-resume" else "resume", context="interactive",
        request={"config_rebind": {**spec, "approval": approval}}, start=root,
        approval_context=None if fault == "no-context" else context,
    )
    assert result["outcome"] in {"operator-held", "hard-stop"}
    assert result["disposition"] == "refused"
    assert state_path.read_bytes() == raw


def test_a_session_already_on_the_scoped_fingerprint_is_not_rebound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=False)
    spec = {"legacy_config": str(_legacy_config_file(tmp_path, root)), "legacy_local_config": None}
    result = run("resume", context="interactive", request={"config_rebind": spec}, start=root)
    assert result["refusal_code"] == "invalid-invocation"
    assert state_path.read_bytes() == raw


@pytest.mark.parametrize("tamper", ["scoped", "legacy", "session", "core-digest", "approval"])
def test_a_rebind_record_that_does_not_bind_the_session_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str) -> None:
    root, state_path, raw = _held_session(tmp_path, monkeypatch, legacy=True)
    spec = {"legacy_config": str(_legacy_config_file(tmp_path, root)), "legacy_local_config": None}
    core_digest = run("resume", context="interactive", request={"config_rebind": spec}, start=root)["recovery_plan"]["core_digest"]
    approval, context = _approve(core_digest)
    run("resume", context="interactive", request={"config_rebind": {**spec, "approval": approval}}, start=root, approval_context=context)
    state = loads_exact(state_path.read_bytes())
    canonical_state(dumps(state), settings=load_settings(root), mode="live")
    record = state["config_rebind"]
    if tamper == "approval":
        record["approval"]["core_digest"] = "0" * 64
    elif tamper == "core-digest":
        # The approval still binds the record's digest; only the recomputed
        # digest of the core can refuse it.
        record["core_digest"] = "0" * 64
        record["approval"]["core_digest"] = "0" * 64
    else:
        name = {"scoped": "scoped_fingerprint", "legacy": "legacy_fingerprint", "session": "session"}[tamper]
        record["core"][name] = "a" * 64 if name != "session" else "another-session"
        record["core_digest"] = digest(record["core"])
        record["approval"]["core_digest"] = record["core_digest"]
    with pytest.raises(TriageError) as refused:
        canonical_state(dumps(state), settings=load_settings(root), mode="live")
    assert refused.value.code == "configuration-identity"


def test_a_completed_legacy_session_still_retires_after_an_unread_key_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#1272's allowance keeps working for a session recorded under the legacy
    fingerprint: a session-starting entry retires the completed state."""
    root, state_path, _ = _held_session(tmp_path, monkeypatch, legacy=True)
    from triage.approval import ApprovalContext as Context
    state = loads_exact(state_path.read_bytes())
    command = "cancel"
    set_digest = digest(state["proposal_payload_digests"])
    context = Context("current-session", "operator", {"approver_identity": "operator", "text": command, "proposal_set_digest": set_digest, "payload_digests": state["proposal_payload_digests"]})
    with monkeypatch.context() as engine:
        engine.setattr("triage.model.scoped_fingerprint", legacy_fingerprint)
        done = run("resume", context="interactive", request={"approval": {"command": command, "proposal_set_digest": set_digest}}, start=root, approval_context=context)
    assert loads_exact(state_path.read_bytes())["phase"] == "completed", done
    _edit(root, *UNREAD)
    fresh = run(None, context="interactive", request={}, start=root)
    assert fresh["detail"].startswith("retired completed state to "), fresh
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"


_DEAD_GATE_CHILD = r'''
import sys
from pathlib import Path
from triage.gate import acquire
from triage.model import legacy_fingerprint, load_settings, repository_identity
from triage.storage import ArtifactStore
settings = load_settings(Path(sys.argv[1]))
fingerprint = {"legacy-current": legacy_fingerprint(settings.config), "foreign": "f" * 64}[sys.argv[2]]
acquire(ArtifactStore(settings, "live"), repository_identity=repository_identity(settings), config_fingerprint=fingerprint, run_identity=None)
'''


@pytest.mark.parametrize("written", ["legacy-current", "foreign"])
def test_a_dead_gate_an_earlier_engine_left_stays_recoverable_under_the_same_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, written: str
) -> None:
    """A gate an engine before #1303 wrote carries the whole-config digest. When the
    current configuration reproduces it, the gate was written under exactly this
    configuration, so `recover` captures it as before; any other fingerprint is
    still foreign."""
    import os

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    environment = {**os.environ, "PYTHONPATH": str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)}
    subprocess.run([sys.executable, "-c", _DEAD_GATE_CHILD, str(root), written], check=True, env=environment)
    gate = state_root / "triage/triage-pipeline-gate_live.lock"
    assert gate.exists()
    planned = run("recover", context="interactive", request={}, start=root)
    if written == "legacy-current":
        assert planned["recovery_plan"] is not None, planned
        assert planned["waiting_on"] == "recovery-approval"
    else:
        assert planned["recovery_plan"] is None
        assert planned["detail"] == "gate configuration identity is foreign"


_ORPHAN_CHILD = _DEAD_GATE_CHILD + r'''
import json
store = ArtifactStore(settings, "live")
token = json.loads(store.gate_path.read_bytes())["owner_token"]
store.gate_path.rename(store.gate_path.with_name(f".{store.gate_path.name}.{token}.tmp"))
'''


@pytest.mark.parametrize("written", ["legacy-current", "foreign"])
def test_an_orphaned_gate_temporary_an_earlier_engine_left_is_cleaned_under_the_same_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, written: str
) -> None:
    """A process stopped between writing its gate temporary and linking it leaves
    the temporary behind; the next acquisition removes it once its owner is dead.
    One written by an engine before #1303 under this same configuration carries
    the whole-config digest and is cleaned as before; any other stays foreign."""
    import os

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    environment = {**os.environ, "PYTHONPATH": str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)}
    subprocess.run([sys.executable, "-c", _ORPHAN_CHILD, str(root), written], check=True, env=environment)
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert list((state_root / "triage").glob(".triage-pipeline-gate_live.lock.*.tmp"))
    draft_request, _ = proposal_request(root)
    result = run("new", context="interactive", request=draft_request, start=root)
    if written == "legacy-current":
        assert result["refusal_code"] is None, result
        assert not list((state_root / "triage").glob(".triage-pipeline-gate_live.lock.*.tmp"))
    else:
        assert result["refusal_code"] == "configuration-identity"
