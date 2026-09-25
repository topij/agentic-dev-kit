"""Capture-before-parse recovery transitions for live and test state."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .canonical import decode_bytes, digest, digest_bytes, dumps, encode_bytes, loads_exact
from .gate import acquire, owner_status, validate_record
from .model import BASE_KEYS, OID_RE, Settings, TriageError, canonical_state, repository_identity
from .storage import (
    ArtifactStore,
    Observation,
    atomic_replace,
    exclusive_create,
    observe,
    quarantine_inode,
)


def _approval(core_digest: str, supplied: dict[str, Any], *, operator: str) -> dict[str, Any]:
    expected = {"decision", "source", "approver_identity", "core_digest"}
    if not isinstance(supplied, dict) or set(supplied) != expected:
        raise TriageError("recovery approval has the wrong shape", outcome="operator-held")
    if supplied["decision"] != "approve" or supplied["core_digest"] != core_digest:
        raise TriageError("recovery approval is not bound to the prepared core", outcome="operator-held")
    if supplied["source"] != "current-session" or supplied["approver_identity"] != operator or not operator:
        raise TriageError("recovery approval identity is not authoritative", outcome="operator-held")
    return supplied


def _gate_capture(store: ArtifactStore, *, require_terminated: bool = True) -> tuple[dict[str, Any], bytes, Observation, list[dict[str, Any]]]:
    observation, raw = observe(store.gate_path, allow_links=True)
    if raw is None:
        raise TriageError("blocking gate disappeared", outcome="operator-held")
    try:
        record = loads_exact(raw)
    except Exception as exc:
        raise TriageError("blocking gate is malformed", outcome="operator-held") from exc
    validate_record(record, repository_identity=repository_identity(store.settings), config_fingerprint=store.settings.fingerprint)
    if require_terminated and owner_status(record) != "terminated":
        raise TriageError("blocking gate owner is active or uncertain", outcome="operator-held")
    aliases: list[dict[str, Any]] = []
    expected_alias = f".{store.gate_path.name}.{record['owner_token']}.tmp"
    for candidate in store.gate_path.parent.iterdir():
        if candidate == store.gate_path:
            continue
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if (info.st_dev, info.st_ino) == (observation.device, observation.inode):
            if candidate.name != expected_alias:
                raise TriageError("blocking gate has an unexpected same-inode name", outcome="operator-held")
            alias_observation, alias_raw = observe(candidate, allow_links=True)
            if alias_raw != raw:
                raise TriageError("same-inode gate name changed bytes", outcome="operator-held")
            aliases.append(alias_observation.as_dict())
    if observation.links != 1 + len(aliases):
        raise TriageError("blocking gate has an unaccounted same-inode name", outcome="operator-held")
    return record, raw, observation, aliases


def _quarantine(path: Path, target: Path, approved: Observation, approved_raw: bytes) -> dict[str, Any]:
    return quarantine_inode(path, target, approved, approved_raw).as_dict()


def _quarantine_group(items: list[tuple[Path, Path, Observation]], approved_raw: bytes) -> list[dict[str, Any]]:
    if not items:
        raise TriageError("empty quarantine group", outcome="operator-held")
    expected_inode = (items[0][2].device, items[0][2].inode)
    if any((item[2].device, item[2].inode) != expected_inode for item in items):
        raise TriageError("gate quarantine group crosses inodes", outcome="operator-held")
    results: list[dict[str, Any]] = []
    for source, target, approved in items:
        source_observation, source_raw = observe(source, allow_links=True)
        target_observation, target_raw = observe(target, allow_links=True)
        if source_raw is not None:
            if source_raw != approved_raw or (source_observation.device, source_observation.inode) != expected_inode:
                raise TriageError("gate source changed before quarantine", outcome="operator-held")
            target_observation = quarantine_inode(source, target, approved, approved_raw)
            target_raw = approved_raw
            source_raw = None
            if target_raw != approved_raw or (target_observation.device, target_observation.inode) != expected_inode:
                raise TriageError("gate quarantine target mismatch", outcome="operator-held")
            if source_raw is not None:
                raise TriageError("gate quarantine source remained after publication", outcome="operator-held")
        elif target_raw != approved_raw or (target_observation.device, target_observation.inode) != expected_inode:
            raise TriageError("gate name lacks approved source or quarantine", outcome="operator-held")
    for _, target, _ in items:
        observation, raw = observe(target, allow_links=True)
        if raw != approved_raw or (observation.device, observation.inode) != expected_inode:
            raise TriageError("gate quarantine read-back mismatch", outcome="operator-held")
        results.append(observation.as_dict())
    if results[0]["links"] != len(items) or any(result["links"] != len(items) for result in results):
        raise TriageError("unaccounted same-inode gate name", outcome="operator-held")
    return results


def gate_only_plan(store: ArtifactStore, settings: Settings) -> dict[str, Any]:
    record, gate_raw, gate_observation, aliases = _gate_capture(store)
    state_observation, state_raw = observe(store.state_path)
    if state_raw is not None:
        raise TriageError("gate-only recovery requires absent state", outcome="operator-held")
    repeated, repeated_raw = observe(store.state_path)
    if repeated_raw is not None:
        raise TriageError("state appeared during gate-only capture", outcome="operator-held")
    gate_digest = digest_bytes(gate_raw)
    bundle_path = store.recovery_path(gate_digest)
    core = {
        "repository_identity": repository_identity(settings),
        "mode": store.mode,
        "configured_bundle_path": str(bundle_path),
        "old_gate_bytes_encoding": "base64",
        "old_gate_bytes": encode_bytes(gate_raw),
        "old_gate_digest": gate_digest,
        "old_gate_record": record,
        "old_gate_observation": gate_observation.as_dict(),
        "old_gate_alias_observations": aliases,
        "state_absence_observations": [state_observation.as_dict(), repeated.as_dict()],
        "intent_kind": "test-gate-recovery-intent" if store.mode == "test" else "gate-only-recovery-intent",
    }
    return {"prepared_core": core, "prepared_core_digest": digest(core)}


def prepare_gate_only(
    store: ArtifactStore,
    settings: Settings,
    *,
    approval: dict[str, Any],
    operator: str,
) -> dict[str, Any]:
    plan = gate_only_plan(store, settings)
    core = plan["prepared_core"]
    core_digest = plan["prepared_core_digest"]
    gate_digest = core["old_gate_digest"]
    bundle_path = Path(core["configured_bundle_path"])
    approved = _approval(core_digest, approval, operator=operator)
    replacement_run_identity = {
        "kind": "gate-only-recovery",
        "mode": store.mode,
        "prepared_core_digest": core_digest,
    }
    intent = {
        "kind": core["intent_kind"],
        "schema_version": 1,
        "prepared_core_digest": core_digest,
        "old_gate_digest": gate_digest,
        "configured_bundle_path": str(bundle_path),
        "repository_identity": core["repository_identity"],
        "mode": store.mode,
        "replacement_gate_run_identity": replacement_run_identity,
    }
    envelope = {
        "kind": "test-gate-only-prepared" if store.mode == "test" else "gate-only-prepared",
        "schema_version": 1,
        "prepared_core": core,
        "prepared_core_digest": core_digest,
        "approval": approved,
        "intended_intent": intent,
        "intended_intent_digest": digest(intent),
    }
    exclusive_create(bundle_path, dumps(envelope))
    return envelope


def resume_gate_only(store: ArtifactStore, settings: Settings, envelope: dict[str, Any]) -> dict[str, Any]:
    expected_envelope_keys = {
        "kind", "schema_version", "prepared_core", "prepared_core_digest", "approval",
        "intended_intent", "intended_intent_digest",
    }
    if not isinstance(envelope, dict) or set(envelope) != expected_envelope_keys:
        raise TriageError("prepared gate-only bundle has the wrong shape", outcome="operator-held")
    expected_kind = "test-gate-only-prepared" if store.mode == "test" else "gate-only-prepared"
    if envelope.get("kind") != expected_kind or envelope.get("schema_version") != 1:
        raise TriageError("prepared gate-only bundle has the wrong identity", outcome="operator-held")
    core = envelope["prepared_core"]
    intent = envelope["intended_intent"]
    if digest(core) != envelope.get("prepared_core_digest") or digest(intent) != envelope.get("intended_intent_digest"):
        raise TriageError("prepared gate-only bundle digest mismatch", outcome="operator-held")
    expected_bundle_path = store.recovery_path(core.get("old_gate_digest", ""))
    if (
        core.get("repository_identity") != repository_identity(settings)
        or core.get("mode") != store.mode
        or core.get("configured_bundle_path") != str(expected_bundle_path)
        or intent.get("prepared_core_digest") != envelope["prepared_core_digest"]
        or intent.get("old_gate_digest") != core.get("old_gate_digest")
        or intent.get("configured_bundle_path") != str(expected_bundle_path)
        or intent.get("repository_identity") != repository_identity(settings)
        or intent.get("mode") != store.mode
    ):
        raise TriageError("prepared gate-only bundle is foreign", outcome="operator-held")
    replacement_run_identity = intent.get("replacement_gate_run_identity")
    if replacement_run_identity != {
        "kind": "gate-only-recovery",
        "mode": store.mode,
        "prepared_core_digest": envelope["prepared_core_digest"],
    }:
        raise TriageError("replacement gate identity is not bound to the prepared core", outcome="operator-held")
    _approval(envelope["prepared_core_digest"], envelope["approval"], operator=envelope["approval"].get("approver_identity", ""))
    gate_raw = decode_bytes(core["old_gate_bytes"])
    if digest_bytes(gate_raw) != core["old_gate_digest"]:
        raise TriageError("prepared old gate bytes mismatch", outcome="operator-held")
    intent_raw = dumps(intent)
    _, state_raw = observe(store.state_path)
    if state_raw is None:
        exclusive_create(store.state_path, intent_raw)
    elif state_raw != intent_raw:
        raise TriageError("gate-only intent path contains foreign bytes", outcome="operator-held")
    gate_observation = Observation(**core["old_gate_observation"])
    sources = [(store.gate_path, gate_observation)]
    for alias in core["old_gate_alias_observations"]:
        sources.append((Path(alias["path"]), Observation(**alias)))
    quarantine_items = []
    for source, observation in sources:
        suffix = core["old_gate_digest"][:16]
        target = source.with_name(source.name + f".quarantine-{suffix}")
        quarantine_items.append((source, target, observation))
    current_gate_observation, current_gate_raw = observe(store.gate_path, allow_links=True)
    replacement_quarantine: list[dict[str, Any]] = []
    if current_gate_raw == gate_raw:
        quarantine_records = _quarantine_group(quarantine_items, gate_raw)
    else:
        if current_gate_raw is not None:
            try:
                replacement_record = loads_exact(current_gate_raw)
            except Exception as exc:
                raise TriageError("replacement gate is malformed", outcome="operator-held") from exc
            validate_record(
                replacement_record,
                repository_identity=repository_identity(settings),
                config_fingerprint=settings.fingerprint,
            )
            if replacement_record.get("owner_run_identity") != replacement_run_identity:
                raise TriageError("replacement gate is foreign to the prepared transition", outcome="operator-held")
            if owner_status(replacement_record) != "terminated":
                raise TriageError("replacement gate owner is active or uncertain", outcome="operator-held")
            replacement_digest = digest_bytes(current_gate_raw)
            target = store.gate_path.with_name(store.gate_path.name + f".recovery-quarantine-{replacement_digest[:16]}")
            replacement_quarantine.append(
                _quarantine(store.gate_path, target, current_gate_observation, current_gate_raw)
            )
        quarantine_records = _quarantine_group(quarantine_items, gate_raw)
    _, verified_intent_raw = observe(store.state_path)
    if verified_intent_raw != intent_raw:
        raise TriageError("gate-only intent changed before replacement gate acquisition", outcome="operator-held")
    lease = acquire(
        store,
        repository_identity=repository_identity(settings),
        config_fingerprint=settings.fingerprint,
        run_identity=replacement_run_identity,
    )
    _, verified_intent_raw = observe(store.state_path)
    if verified_intent_raw != intent_raw:
        raise TriageError("gate-only intent changed under replacement gate", outcome="operator-held")
    receipt = {
        "kind": "gate-only-operator-held",
        "schema_version": 1,
        "mode": store.mode,
        "prepared_core_digest": envelope["prepared_core_digest"],
        "old_gate_digest": core["old_gate_digest"],
        "configured_bundle_path": core["configured_bundle_path"],
        "repository_identity": core["repository_identity"],
        "quarantine_observations": quarantine_records,
        "replacement_quarantine_observations": replacement_quarantine,
        "recovery_gate_owner_token": lease.owner_token,
        "recovery_gate_record": lease.record,
    }
    atomic_replace(store.state_path, dumps(receipt), expected_digest=digest_bytes(intent_raw))
    lease.release()
    return receipt


def capture_state_present(store: ArtifactStore, settings: Settings, *, require_terminated: bool = True, publish: bool = True) -> dict[str, Any]:
    record, gate_raw, gate_observation, aliases = _gate_capture(store, require_terminated=require_terminated)
    state_observation, state_raw = observe(store.state_path)
    if state_raw is None:
        raise TriageError("state-present recovery requires state", outcome="operator-held")
    gate_digest = digest_bytes(gate_raw)
    core = {
        "repository_identity": repository_identity(settings),
        "mode": store.mode,
        "configured_bundle_path": str(store.recovery_path(gate_digest)),
        "old_gate_bytes_encoding": "base64",
        "old_gate_bytes": encode_bytes(gate_raw),
        "old_gate_digest": gate_digest,
        "old_gate_record": record,
        "old_gate_observation": gate_observation.as_dict(),
        "old_gate_alias_observations": aliases,
        "state_bytes_encoding": "base64",
        "state_bytes": encode_bytes(state_raw),
        "state_digest": digest_bytes(state_raw),
        "state_observation": state_observation.as_dict(),
    }
    bundle = {"kind": "state-present-capture", "schema_version": 1, "capture_core": core, "capture_core_digest": digest(core)}
    if publish:
        exclusive_create(store.recovery_path(gate_digest), dumps(bundle))
    return bundle


def test_gate_state_plan(store: ArtifactStore, settings: Settings) -> dict[str, Any]:
    if store.mode != "test":
        raise TriageError("test-gate held evidence is test-confined", outcome="operator-held")
    record, gate_raw, gate_observation, aliases = _gate_capture(store)
    state_observation, state_raw = observe(store.state_path)
    if state_raw is None:
        raise TriageError("test-gate state evidence is absent", outcome="operator-held")
    gate_digest = digest_bytes(gate_raw)
    core = {
        "repository_identity": repository_identity(settings),
        "mode": "test",
        "configured_bundle_path": str(store.recovery_path(gate_digest)),
        "old_gate_bytes_encoding": "base64",
        "old_gate_bytes": encode_bytes(gate_raw),
        "old_gate_digest": gate_digest,
        "old_gate_record": record,
        "old_gate_observation": gate_observation.as_dict(),
        "old_gate_alias_observations": aliases,
        "state_bytes_encoding": "base64",
        "state_bytes": encode_bytes(state_raw),
        "state_digest": digest_bytes(state_raw),
        "state_observation": state_observation.as_dict(),
    }
    return {"capture_core": core, "capture_core_digest": digest(core)}


def persist_test_gate_held(
    store: ArtifactStore,
    settings: Settings,
    plan: dict[str, Any],
    *,
    approval: dict[str, Any],
    operator: str,
) -> dict[str, Any]:
    expected = test_gate_state_plan(store, settings)
    if expected != plan:
        raise TriageError("test-gate capture changed before held publication", outcome="operator-held")
    approved = _approval(plan["capture_core_digest"], approval, operator=operator)
    core = plan["capture_core"]
    held = {
        "kind": "state-present-test-gate-held",
        "schema_version": 1,
        "capture_core": core,
        "capture_core_digest": plan["capture_core_digest"],
        "approval": approved,
        "terminal_classification": "test-gate-state-present",
    }
    exclusive_create(Path(core["configured_bundle_path"]), dumps(held))
    return held


def prepare_state_action(
    store: ArtifactStore,
    settings: Settings,
    bundle: dict[str, Any],
    *,
    approval: dict[str, Any],
    operator: str,
) -> dict[str, Any]:
    plan = state_action_plan(store, settings, bundle)
    if plan.get("held") is not None:
        held = plan["held"]
        core = bundle["capture_core"]
        atomic_replace(store.recovery_path(core["old_gate_digest"]), dumps(held), expected_digest=digest_bytes(dumps(bundle)))
        return held
    core = bundle["capture_core"]
    action_core = plan["action_core"]
    action_digest = plan["action_core_digest"]
    approved = _approval(action_digest, approval, operator=operator)
    prepared = {
        "kind": "state-present-prepared",
        "schema_version": 1,
        "capture_core": core,
        "capture_core_digest": bundle["capture_core_digest"],
        "action_core": action_core,
        "action_core_digest": action_digest,
        "approval": approved,
    }
    atomic_replace(store.recovery_path(core["old_gate_digest"]), dumps(prepared), expected_digest=digest_bytes(dumps(bundle)))
    return prepared


_SETTLED = {"verified"}
_FORGE_SETTLED = {"verified", "unsettled"}


def _terminal_evidence(parsed: Any) -> dict[str, Any] | None:
    """Summarise an invalid but finished run, or return None to keep it held.

    An invalid state that records external writes cannot be abandoned, because
    nothing proves none is still in flight. A run whose own bytes record every
    tracker and forge operation as verified, and a verified merge whose final
    head is the reviewed head, has nothing in flight: it can be retired to its
    quarantine path like an abandoned one, keeping every byte. `unsettled` is
    accepted only on a `pr-watch` observation, which writes nothing. Anything
    unrecognised keeps the state held.
    """
    if (
        not isinstance(parsed, dict)
        or parsed.get("kind") != "triage-run-state"
        or isinstance(parsed.get("schema_version"), bool)
        or parsed.get("schema_version") != 1
        or parsed.get("phase") != "completed"
    ):
        return None
    completion = parsed.get("completion")
    merge = completion.get("merge_read_back") if isinstance(completion, dict) else None
    reviewed_head = parsed.get("reviewed_head")
    identifiers = parsed.get("verified_tracker_identifiers")
    if (
        not isinstance(completion, dict)
        or completion.get("route") != "archive-sweep"
        or not isinstance(merge, dict)
        or merge.get("merged") is not True
        or not isinstance(reviewed_head, str)
        or merge.get("final_head") != reviewed_head
        or not isinstance(identifiers, list)
        or any(not isinstance(item, str) for item in identifiers)
    ):
        return None
    records: list[tuple[dict[str, Any], set[str]]] = []
    for name in ("operations", "attempts", "notification_operations"):
        entries = parsed.get(name, [])
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            return None
        records.extend((entry, _SETTLED) for entry in entries)
    forge = parsed.get("finalization_operations")
    if not isinstance(forge, list) or not forge or any(not isinstance(entry, dict) for entry in forge):
        return None
    for entry in forge:
        allowed = _FORGE_SETTLED if entry.get("kind") == "pr-watch" else _SETTLED
        records.append((entry, allowed))
        nested = entry.get("attempts", [])
        if not isinstance(nested, list) or any(not isinstance(attempt, dict) for attempt in nested):
            return None
        records.extend((attempt, allowed) for attempt in nested)
    if any(record.get("status") not in allowed for record, allowed in records):
        return None
    if forge[-1].get("kind") != "merge-read-back" or forge[-1].get("status") != "verified":
        return None
    run_identity = parsed.get("run_identity")
    return {
        "session": run_identity.get("session") if isinstance(run_identity, dict) else None,
        "verified_tracker_identifiers": identifiers,
        "pull_request": merge.get("pull_request"),
        "merge_commit": merge.get("merge_commit"),
        "final_head": reviewed_head,
    }


def _swept_blocks(parsed: dict[str, Any]) -> dict[str, str] | None:
    """The frozen source text of every block the run decided to file or archive."""
    snapshot = parsed.get("frozen_snapshot")
    content = snapshot.get("content") if isinstance(snapshot, dict) else None
    blocks = content.get("blocks") if isinstance(content, dict) else None
    decisions = parsed.get("decisions")
    if not isinstance(blocks, list) or not isinstance(decisions, list):
        return None
    texts: dict[str, str] = {}
    for block in blocks:
        if not isinstance(block, dict) or not isinstance(block.get("candidate_id"), str) or not isinstance(block.get("source_block"), str):
            return None
        texts[block["candidate_id"]] = block["source_block"]
    swept: dict[str, str] = {}
    for decision in decisions:
        if not isinstance(decision, dict) or not isinstance(decision.get("candidate_id"), str):
            return None
        if decision.get("decision") in {"file", "archive"}:
            text = texts.get(decision["candidate_id"])
            if not text or not text.strip():
                return None
            swept[decision["candidate_id"]] = text
    return swept or None


def _sweep_landed(settings: Settings, parsed: dict[str, Any], merge_commit: Any) -> str | None:
    """Return the protected ref the run's own sweep is proven on, or None.

    The bytes of an invalid state are claims, not proof, and a reachable commit
    alone could be any merged commit. What makes a new session safe is that this
    run's swept blocks left the inbox, so it cannot re-file them. So the recorded
    merge commit must be reachable from the protected ref and change the friction
    log, and every block the run filed or archived must be absent from the
    current inbox and present in the archive.
    """
    swept = _swept_blocks(parsed)
    if swept is None or not isinstance(merge_commit, str) or not OID_RE.fullmatch(merge_commit):
        return None
    repo = str(settings.paths.repo)
    ref = f"refs/remotes/origin/{settings.protected_branch}"
    reachable = subprocess.run(
        ["git", "-C", repo, "merge-base", "--is-ancestor", merge_commit, ref],
        check=False, capture_output=True,
    )
    changed = subprocess.run(
        ["git", "-C", repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", merge_commit],
        check=False, capture_output=True,
    )
    log_path = settings.paths.friction_log.relative_to(settings.paths.repo).as_posix()
    if reachable.returncode or changed.returncode or log_path not in changed.stdout.decode("utf-8", "replace").split("\0"):
        return None
    try:
        inbox = settings.paths.friction_log.read_text(encoding="utf-8")
        archive = settings.paths.archive.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if any(text in inbox or text not in archive for text in swept.values()):
        return None
    return ref


def state_action_plan(store: ArtifactStore, settings: Settings, bundle: dict[str, Any]) -> dict[str, Any]:
    core = bundle.get("capture_core")
    if not isinstance(core, dict) or digest(core) != bundle.get("capture_core_digest"):
        raise TriageError("state capture digest mismatch", outcome="operator-held")
    state_raw = decode_bytes(core["state_bytes"])
    valid = False
    try:
        canonical_state(state_raw, settings=settings, mode=store.mode)
        valid = True
    except TriageError:
        pass
    if valid:
        action = "preserve-valid-state-and-quarantine-old-gate"
    else:
        try:
            parsed = loads_exact(state_raw)
        except Exception:
            parsed = None
        evidence_names = ("attempts", "verified_tracker_identifiers", "repository_evidence", "pull_request_evidence")
        abandonable = (
            isinstance(parsed, dict)
            and set(parsed) == BASE_KEYS
            and parsed.get("kind") == "triage-run-state"
            and parsed.get("schema_version") == 1
            and isinstance(parsed.get("phase"), str)
            and parsed.get("phase") not in {
                "reserved", "propose", "notification-delivery", "awaiting-approval",
                "tracker-write", "forge-finalize", "archive-sweep", "completed",
            }
            and all(parsed.get(name) == [] for name in evidence_names)
        )
        terminal_evidence = None if abandonable else _terminal_evidence(parsed)
        if terminal_evidence is not None:
            landed = _sweep_landed(settings, parsed, terminal_evidence["merge_commit"])
            terminal_evidence = {
                **terminal_evidence,
                "merge_commit_reachable_from": landed,
                "swept_candidates": sorted(_swept_blocks(parsed) or {}),
            } if landed else None
        if not abandonable and terminal_evidence is None:
            held = {**bundle, "kind": "state-present-held", "terminal_classification": "external-attempt-absence-unproven"}
            return {"held": held}
        action = "abandon-invalid-state" if abandonable else "retire-terminal-invalid-state"
    quarantine_path = str(store.state_path) + f".quarantine-{core['state_digest'][:16]}"
    moves_state = action in {"abandon-invalid-state", "retire-terminal-invalid-state"}
    receipt_core = {
        "kind": "test-recovered-safe-to-restart" if store.mode == "test" else "recovered-safe-to-restart",
        "mode": store.mode,
        "old_gate_digest": core["old_gate_digest"],
        "configured_bundle_path": core["configured_bundle_path"],
        "capture_core_digest": bundle["capture_core_digest"],
        "quarantine_path": quarantine_path,
    }
    action_core = {
        "capture_core_digest": bundle["capture_core_digest"],
        "old_gate_digest": core["old_gate_digest"],
        "action": action,
        "quarantine_path": quarantine_path if moves_state else None,
        "receipt_core": receipt_core if moves_state else None,
    }
    if action == "retire-terminal-invalid-state":
        # Bound into the digest the operator approves, so the approval names
        # the external writes the retired bytes record as finished.
        action_core["terminal_evidence"] = terminal_evidence
    return {"action_core": action_core, "action_core_digest": digest(action_core), "held": None}


def resume_state_action(store: ArtifactStore, prepared: dict[str, Any]) -> dict[str, Any]:
    core = prepared["capture_core"]
    action = prepared["action_core"]
    if digest(core) != prepared.get("capture_core_digest") or digest(action) != prepared.get("action_core_digest"):
        raise TriageError("prepared state action digest mismatch", outcome="operator-held")
    state_raw = decode_bytes(core["state_bytes"])
    state_observation = Observation(**core["state_observation"])
    gate_raw = decode_bytes(core["old_gate_bytes"])
    if action["action"] == "preserve-valid-state-and-quarantine-old-gate":
        _quarantine(store.gate_path, store.gate_path.with_name(store.gate_path.name + f".quarantine-{core['old_gate_digest'][:16]}"), Observation(**core["old_gate_observation"]), gate_raw)
        return {"result": "resume", "state_digest": core["state_digest"]}
    target = Path(action["quarantine_path"])
    current_state_observation, current_state_raw = observe(store.state_path)
    if current_state_raw == state_raw:
        target_observation = _quarantine(store.state_path, target, state_observation, state_raw)
        current_state_raw = None
    elif current_state_raw is None:
        target_observation, target_raw = observe(target)
        if target_raw != state_raw:
            raise TriageError("prepared state quarantine is missing", outcome="operator-held")
        target_observation = target_observation.as_dict()
    else:
        target_observation, target_raw = observe(target)
        if target_raw != state_raw:
            raise TriageError("state changed outside prepared recovery", outcome="operator-held")
        target_observation = target_observation.as_dict()
    envelope_digest = digest_bytes(dumps(prepared))
    receipt = {**action["receipt_core"], "schema_version": 1, "prepared_envelope_digest": envelope_digest, "quarantine_observation": target_observation}
    if current_state_raw is None:
        exclusive_create(store.state_path, dumps(receipt))
    elif current_state_raw != dumps(receipt):
        raise TriageError("state path contains neither source nor exact receipt", outcome="operator-held")
    gate_observation = Observation(**core["old_gate_observation"])
    if store.gate_path.exists():
        _quarantine(store.gate_path, store.gate_path.with_name(store.gate_path.name + f".quarantine-{core['old_gate_digest'][:16]}"), gate_observation, gate_raw)
    return receipt
