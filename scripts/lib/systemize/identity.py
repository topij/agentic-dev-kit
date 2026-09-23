"""Run identities and the identity header every JSON artifact carries."""

from __future__ import annotations

import json
from typing import Any

from triage.canonical import CanonicalError, digest

from .errors import SystemizeError

RUN_SCHEMA = "post-merge-systemize-run-v1"
# The heartbeat starts before the forge read supplies the protected-branch head,
# so it binds this pre-forge identity and records the run identity once known.
HEARTBEAT_SCHEMA = "post-merge-systemize-heartbeat-v1"
RAW_KIND = "post-merge-systemize-raw"
DIGEST_KIND = "post-merge-systemize-digest"
HEARTBEAT_KIND = "post-merge-systemize-heartbeat"
SCHEMA_VERSION = 1


def identity_digest(identity: dict[str, Any]) -> str:
    try:
        return "sha256:" + digest(identity)
    except CanonicalError as exc:
        raise SystemizeError(f"identity is not canonical JSON: {exc}") from exc


def run_identity(
    *, forge_repo: str, window_days: int, head: str, fingerprint: str, mode: str
) -> dict[str, Any]:
    return {
        "schema": RUN_SCHEMA,
        "forge_repo": forge_repo,
        "window_days": window_days,
        "protected_branch_head": head,
        "config_fingerprint": fingerprint,
        "execution_mode": mode,
    }


def heartbeat_identity(
    *, job: str, window_days: int, date: str, fingerprint: str, mode: str
) -> dict[str, Any]:
    return {
        "schema": HEARTBEAT_SCHEMA,
        "job": job,
        "window_days": window_days,
        "date": date,
        "config_fingerprint": fingerprint,
        "execution_mode": mode,
    }


def header(kind: str, identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_kind": kind,
        "schema_version": SCHEMA_VERSION,
        "run_identity": identity,
        "run_identity_digest": identity_digest(identity),
    }


def parse_artifact(raw: bytes, path: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemizeError(f"{path}: unreadable artifact ({exc}); inspect and move it") from exc
    if not isinstance(value, dict):
        raise SystemizeError(f"{path}: artifact is not a JSON object; inspect and move it")
    return value


def check_header(value: dict[str, Any], *, kind: str, path: str) -> dict[str, Any]:
    """Validate kind, schema and the recorded digest; return the recorded identity."""
    if value.get("artifact_kind") != kind:
        raise SystemizeError(
            f"{path}: foreign artifact kind {value.get('artifact_kind')!r} (expected {kind}); "
            "inspect and move it or select a different configured pattern"
        )
    if value.get("schema_version") != SCHEMA_VERSION or isinstance(value.get("schema_version"), bool):
        raise SystemizeError(f"{path}: unsupported schema_version {value.get('schema_version')!r}")
    identity = value.get("run_identity")
    if not isinstance(identity, dict):
        raise SystemizeError(f"{path}: missing run_identity")
    if value.get("run_identity_digest") != identity_digest(identity):
        raise SystemizeError(f"{path}: run_identity_digest does not match the recorded identity")
    return identity


def require_same_run(raw: bytes, *, kind: str, identity: dict[str, Any], path: str) -> None:
    """An existing target may be replaced only when it is this run's own artifact."""
    recorded = check_header(parse_artifact(raw, path), kind=kind, path=path)
    if identity_digest(recorded) != identity_digest(identity):
        raise SystemizeError(
            f"{path}: existing artifact belongs to a different run; inspect and move it "
            "or select a different configured pattern"
        )
