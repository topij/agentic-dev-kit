#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Verify a retained, redacted live-validation evidence bundle.

The bundle contract lives in ``docs/agentic-dev-kit/live-validation-evidence.md``.
This engine gives its load-bearing parts teeth: artifact presence and digests,
source/review/runtime binding, claim-to-evidence links, a separate promotion
receipt, and the persistent runtime attestation required for applied-compute
claims. It deliberately does not pretend that a token-pattern scan proves a
redaction safe; a named human/agent review remains part of the manifest.

Usage:
    uv run <engine-dir>/verify_live_validation_bundle.py \
      saved_plans/example-evidence/bundle.json

    uv run <engine-dir>/verify_live_validation_bundle.py \
      saved_plans/example-evidence/bundle.json \
      --promotion saved_plans/example-evidence/promotion.json \
      --expect-authority docs/agentic-dev-kit/runtime-parity.md \
      --expect-source-repository https://github.com/example/source \
      --expect-source-revision <full-source-sha> \
      --expect-review-repository https://github.com/example/review \
      --expect-reviewed-head <full-reviewed-head-sha> \
      --expect-redaction-reviewer <independent-reviewer> \
      --expect-runtime codex \
      --expect-client-version "codex-cli <version>" \
      --expect-applied-compute '<exact-applied-compute-json>' \
      --expect-claim '<exact-claim-json>'

The command exits 0 only when every requested check passes and exits 2 for an
invalid bundle, promotion receipt, or invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
MAX_ARTIFACT_BYTES = 1_048_576
MAX_BUNDLE_BYTES = 8_388_608
MAX_ARTIFACT_COUNT = 256
MAX_ARTIFACT_TREE_ENTRIES = 512
MAX_JSON_INTEGER_DIGITS = 4_300

ALLOWED_ARTIFACT_KINDS = frozenset(
    {
        "command-capture",
        "descriptor",
        "filesystem-readback",
        "final-message",
        "forge-readback",
        "git-readback",
        "launcher-receipt",
        "review-receipt",
        "runtime-attestation",
        "source-digest",
        "source-file",
    }
)
ALLOWED_SUFFIXES = frozenset(
    {".diff", ".json", ".md", ".patch", ".py", ".sh", ".txt", ".yaml", ".yml"}
)
REQUIRED_EXCLUSIONS = frozenset(
    {
        "authentication-material",
        "credentials",
        "tokens",
        "unrelated-user-data",
        "unrelated-workspace-data",
    }
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_CAPTURE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FORBIDDEN_JSON_KEY = re.compile(
    r"(?:^|_)(?:(?:api|access|private)_?keys?|auths?|authentications?|"
    r"authorizations?|bearers?|cookies?|credentials?|pass_?phrases?|passwords?|"
    r"secrets?|tokens?)(?:$|_)",
    re.IGNORECASE,
)
_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}=*", re.IGNORECASE),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bAuthorization\s*:\s*Basic\s+[A-Za-z0-9+/]{8,}=*", re.IGNORECASE),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(
        r"\b(?:aws_?secret_?access_?key|password|pass_?phrase|api_?key|"
        r"access_?token|secret|token)\s*[:=]\s*(?:"
        r'"[^"\r\n]{6,}"|\'[^\'\r\n]{6,}\'|[^\s\"\']{6,})',
        re.IGNORECASE,
    ),
)


class BundleError(ValueError):
    """A condition that makes retained evidence or promotion unsafe to trust."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BundleError(f"evidence bytes are unreadable: {path}: {exc}") from exc
    return digest.hexdigest()


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BundleError(f"{label} must be a JSON object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise BundleError(f"{label} must be a JSON array")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BundleError(f"{label} must be a non-empty string")
    return value


def _string_without_controls(value: Any, label: str) -> str:
    text = _string(value, label)
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        raise BundleError(f"{label} must not contain control characters")
    return text


def _string_list(value: Any, label: str) -> list[str]:
    items = _list(value, label)
    return [_string(item, f"{label}[{index}]") for index, item in enumerate(items)]


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise BundleError(f"{label} keys differ: missing={missing}, extra={extra}")


def _file_size(path: Path, label: str, *, limit: int) -> int:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BundleError(f"{label} cannot be inspected: {path}: {exc}") from exc
    if size > limit:
        raise BundleError(f"{label} exceeds its byte limit: {path}")
    return size


def _read_json(
    path: Path,
    label: str,
    *,
    limit: int = MAX_BUNDLE_BYTES,
) -> dict[str, Any]:
    _file_size(path, label, limit=limit)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BundleError(f"{label} is unreadable: {path}: {exc}") from exc
    _reject_credential_like_text(raw, label, path)
    return _object(_parse_json(raw, label, path), label)


def _reject_credential_like_text(text: str, label: str, path: Path) -> None:
    for pattern in _FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(text):
            raise BundleError(f"{label} contains credential-like content: {path}")


def _parse_json(raw: str, label: str, path: Path) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, child in pairs:
            if key in value:
                raise BundleError(f"{label} contains duplicate JSON key {key!r}: {path}")
            value[key] = child
        return value

    def finite_number(constant: str) -> None:
        raise BundleError(f"{label} contains non-finite JSON value {constant!r}: {path}")

    def finite_float(number: str) -> float:
        value = float(number)
        if not math.isfinite(value):
            finite_number(number)
        return value

    def bounded_integer(number: str) -> int:
        if len(number.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
            raise BundleError(f"{label} contains an unsupported JSON integer: {path}")
        return int(number)

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=finite_number,
            parse_float=finite_float,
            parse_int=bounded_integer,
        )
    except BundleError:
        raise
    except json.JSONDecodeError as exc:
        raise BundleError(f"{label} is not valid JSON: {path}: {exc}") from exc
    except ValueError as exc:
        raise BundleError(f"{label} contains an unsupported JSON number: {path}") from exc
    except RecursionError as exc:
        raise BundleError(f"{label} exceeds the supported JSON nesting depth: {path}") from exc
    try:
        _scan_json_content(value, label, path)
    except RecursionError as exc:
        raise BundleError(f"{label} exceeds the supported JSON nesting depth: {path}") from exc
    return value


def _safe_relative_path(value: Any, label: str, *, beneath: str | None = None) -> str:
    text = _string_without_controls(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or path.as_posix() != text or ".." in path.parts or "." in path.parts:
        raise BundleError(f"{label} must be a canonical relative path: {text}")
    if any(part.startswith(".") for part in path.parts):
        raise BundleError(f"{label} must not contain hidden path components: {text}")
    if beneath is not None and (not path.parts or path.parts[0] != beneath):
        raise BundleError(f"{label} must be beneath {beneath}/: {text}")
    return text


def _validate_bundle_root(manifest_path: Path) -> None:
    if manifest_path.name != "bundle.json":
        raise BundleError("bundle manifest must be named bundle.json")
    if manifest_path.parent.is_symlink():
        raise BundleError("bundle root must be a retained directory, not a symlink")
    allowed = {"artifacts", "bundle.json", "promotion.json"}
    seen: set[str] = set()
    try:
        with os.scandir(manifest_path.parent) as entries:
            for entry in entries:
                seen.add(entry.name)
                if entry.name not in allowed:
                    raise BundleError(f"bundle root contains an undeclared entry: {entry.name}")
                if entry.is_symlink():
                    raise BundleError(f"bundle root contains a symlink: {entry.name}")
                if entry.name == "artifacts":
                    if not entry.is_dir(follow_symlinks=False):
                        raise BundleError("bundle root artifacts entry must be a directory")
                elif not entry.is_file(follow_symlinks=False):
                    raise BundleError(f"bundle root entry must be a regular file: {entry.name}")
    except OSError as exc:
        raise BundleError(f"bundle root is unreadable: {manifest_path.parent}: {exc}") from exc
    missing = {"artifacts", "bundle.json"} - seen
    if missing:
        raise BundleError(f"bundle root is missing required entries: {sorted(missing)}")


def _reject_symlink_traversal(path: Path, label: str) -> None:
    lexical = Path(os.path.abspath(path))
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BundleError(f"{label} is unreadable: {path}: {exc}") from exc
    if lexical != resolved:
        raise BundleError(f"{label} path must not traverse a symlink: {path}")


def _artifact_inventory(
    artifact_root: Path,
    bundle_root: Path,
) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories = {artifact_root.relative_to(bundle_root).as_posix()}
    pending = [artifact_root]
    observed_entries = 0
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    observed_entries += 1
                    if observed_entries > MAX_ARTIFACT_TREE_ENTRIES:
                        raise BundleError("artifact tree exceeds the entry-count limit")
                    path = Path(entry.path)
                    relative = path.relative_to(bundle_root).as_posix()
                    if entry.name.startswith("."):
                        raise BundleError(f"artifact tree contains a hidden entry: {relative}")
                    if entry.is_symlink():
                        raise BundleError(f"artifact tree contains a symlink: {relative}")
                    if entry.is_dir(follow_symlinks=False):
                        directories.add(relative)
                        pending.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        files.add(relative)
                    else:
                        raise BundleError(f"artifact tree contains a non-regular entry: {relative}")
        except OSError as exc:
            relative = current.relative_to(bundle_root).as_posix()
            raise BundleError(f"artifact directory is unreadable: {relative}: {exc}") from exc
    return files, directories


def _scan_json_content(value: Any, label: str, path: Path) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_credential_like_text(str(key), label, path)
            key_text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", str(key))
            key_text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key_text)
            normalized_key = re.sub(r"[^A-Za-z0-9]+", "_", key_text)
            if _FORBIDDEN_JSON_KEY.search(normalized_key):
                raise BundleError(f"{label} contains forbidden credential-like key {key!r}")
            _scan_json_content(child, label, path)
    elif isinstance(value, list):
        for child in value:
            _scan_json_content(child, label, path)
    elif isinstance(value, str):
        _reject_credential_like_text(value, label, path)


def _scan_artifact(path: Path, label: str) -> int:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BundleError(f"{label} cannot be inspected: {path}: {exc}") from exc
    if size > MAX_ARTIFACT_BYTES:
        raise BundleError(f"{label} exceeds the per-artifact byte limit: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BundleError(f"{label} must be readable UTF-8 text: {path}: {exc}") from exc
    _reject_credential_like_text(text, label, path)
    if path.suffix == ".json":
        _parse_json(text, label, path)
    return size


def _validate_revision(value: Any, label: str) -> str:
    revision = _string(value, label)
    if not _GIT_SHA.fullmatch(revision):
        raise BundleError(f"{label} must be a full lowercase Git sha")
    return revision


def _validate_attestation(
    *,
    bundle_root: Path,
    runtime: dict[str, Any],
    artifact_by_path: dict[str, dict[str, Any]],
    compute_claims: list[dict[str, Any]],
) -> None:
    persistence = runtime["session_persistence"]
    compute = runtime["applied_compute"]
    if not compute_claims:
        if compute is not None:
            raise BundleError("runtime.applied_compute must be null when no claim depends on it")
        return
    if persistence != "persistent":
        raise BundleError(
            "applied-compute claims require session_persistence=persistent; "
            "an ephemeral carrier cannot support them"
        )
    compute = _object(compute, "runtime.applied_compute")
    _exact_keys(
        compute,
        {"model", "effort", "cwd", "session_id", "attestation"},
        "runtime.applied_compute",
    )
    for key in ("model", "effort", "cwd", "session_id"):
        _string_without_controls(compute[key], f"runtime.applied_compute.{key}")
    attestation_path = _safe_relative_path(
        compute["attestation"], "runtime.applied_compute.attestation", beneath="artifacts"
    )
    record = artifact_by_path.get(attestation_path)
    if record is None:
        raise BundleError("runtime.applied_compute.attestation is not a declared artifact")
    if record["kind"] != "runtime-attestation":
        raise BundleError("applied-compute attestation must have kind runtime-attestation")
    if record["observer"] != "runtime-session-context":
        raise BundleError("applied-compute attestation observer must be runtime-session-context")
    for claim in compute_claims:
        if attestation_path not in claim["evidence"]:
            raise BundleError(
                f"claim {claim['id']} depends on applied compute but omits its attestation"
            )
    attestation = _read_json(bundle_root / attestation_path, "runtime attestation")
    _exact_keys(attestation, {"session_id", "turn_context"}, "runtime attestation")
    context = _object(attestation["turn_context"], "runtime attestation.turn_context")
    _exact_keys(context, {"model", "effort", "cwd"}, "runtime attestation.turn_context")
    expected = {
        "session_id": compute["session_id"],
        "turn_context": {
            "model": compute["model"],
            "effort": compute["effort"],
            "cwd": compute["cwd"],
        },
    }
    if attestation != expected:
        raise BundleError("runtime attestation disagrees with runtime.applied_compute")


def validate_bundle(manifest_path: Path) -> dict[str, Any]:
    """Return the parsed manifest only after its complete bundle validates."""

    _reject_symlink_traversal(manifest_path, "bundle manifest")
    if manifest_path.parent.is_symlink():
        raise BundleError("bundle root must be a retained directory, not a symlink")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BundleError(f"bundle manifest must be a regular file, not a symlink: {manifest_path}")
    manifest = _read_json(manifest_path, "bundle manifest")
    _validate_bundle_root(manifest_path)
    _exact_keys(
        manifest,
        {
            "schema_version",
            "bundle_id",
            "source",
            "review",
            "runtime",
            "redaction",
            "artifacts",
            "claims",
        },
        "bundle manifest",
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise BundleError(f"unsupported schema_version: {manifest['schema_version']!r}")
    bundle_id = _string(manifest["bundle_id"], "bundle_id")
    if not _SLUG.fullmatch(bundle_id):
        raise BundleError("bundle_id must be a lowercase slug")

    source = _object(manifest["source"], "source")
    _exact_keys(source, {"repository", "revision"}, "source")
    _string(source["repository"], "source.repository")
    _validate_revision(source["revision"], "source.revision")

    review = _object(manifest["review"], "review")
    _exact_keys(review, {"repository", "head", "observer"}, "review")
    _string(review["repository"], "review.repository")
    _validate_revision(review["head"], "review.head")
    _string(review["observer"], "review.observer")

    runtime = _object(manifest["runtime"], "runtime")
    _exact_keys(
        runtime,
        {"name", "client_version", "session_persistence", "applied_compute"},
        "runtime",
    )
    if not _SLUG.fullmatch(_string(runtime["name"], "runtime.name")):
        raise BundleError("runtime.name must be a lowercase slug")
    _string(runtime["client_version"], "runtime.client_version")
    persistence = _string(runtime["session_persistence"], "runtime.session_persistence")
    if persistence not in {"persistent", "not-applicable", "ephemeral"}:
        raise BundleError("runtime.session_persistence has an unsupported value")

    redaction = _object(manifest["redaction"], "redaction")
    _exact_keys(redaction, {"reviewed", "reviewer", "excluded"}, "redaction")
    if redaction["reviewed"] is not True:
        raise BundleError("redaction.reviewed must be true before verification")
    _string(redaction["reviewer"], "redaction.reviewer")
    excluded = _string_list(redaction["excluded"], "redaction.excluded")
    if set(excluded) != REQUIRED_EXCLUSIONS or len(excluded) != len(REQUIRED_EXCLUSIONS):
        raise BundleError(
            "redaction.excluded must enumerate every forbidden data category exactly once"
        )

    bundle_root = manifest_path.parent
    artifacts = _list(manifest["artifacts"], "artifacts")
    if not artifacts:
        raise BundleError("artifacts must not be empty")
    if len(artifacts) > MAX_ARTIFACT_COUNT:
        raise BundleError("artifacts exceeds the artifact-count limit")
    artifact_by_path: dict[str, dict[str, Any]] = {}
    total_bytes = _file_size(manifest_path, "bundle manifest", limit=MAX_BUNDLE_BYTES)
    for index, item in enumerate(artifacts):
        label = f"artifacts[{index}]"
        record = _object(item, label)
        _exact_keys(
            record,
            {"path", "sha256", "kind", "observer", "capture_request", "captured_on"},
            label,
        )
        rel = _safe_relative_path(record["path"], f"{label}.path", beneath="artifacts")
        if rel in artifact_by_path:
            raise BundleError(f"duplicate artifact path: {rel}")
        if PurePosixPath(rel).suffix not in ALLOWED_SUFFIXES:
            raise BundleError(f"artifact has an unsupported suffix: {rel}")
        digest = _string(record["sha256"], f"{label}.sha256")
        if not _SHA256.fullmatch(digest):
            raise BundleError(f"{label}.sha256 must be lowercase sha256")
        kind = _string(record["kind"], f"{label}.kind")
        if kind not in ALLOWED_ARTIFACT_KINDS:
            raise BundleError(f"unsupported artifact kind: {kind}")
        _string(record["observer"], f"{label}.observer")
        _string_without_controls(record["capture_request"], f"{label}.capture_request")
        captured_on = _string(record["captured_on"], f"{label}.captured_on")
        if not _CAPTURE_DATE.fullmatch(captured_on):
            raise BundleError(f"{label}.captured_on must use YYYY-MM-DD")
        try:
            capture_date = date.fromisoformat(captured_on)
        except ValueError as exc:
            raise BundleError(f"{label}.captured_on must be a calendar date") from exc
        if capture_date > date.today():
            raise BundleError(f"{label}.captured_on must not be in the future")
        path = bundle_root / rel
        _reject_symlink_traversal(path, label)
        if path.is_symlink() or not path.is_file():
            raise BundleError(f"declared artifact is absent or not a regular file: {rel}")
        total_bytes += _file_size(path, label, limit=MAX_ARTIFACT_BYTES)
        if total_bytes > MAX_BUNDLE_BYTES:
            raise BundleError("bundle envelope exceeds the bundle byte limit")
        if _sha256(path) != digest:
            raise BundleError(f"artifact digest mismatch: {rel}")
        _scan_artifact(path, label)
        artifact_by_path[rel] = record

    artifact_root = bundle_root / "artifacts"
    if artifact_root.is_symlink() or not artifact_root.is_dir():
        raise BundleError("bundle must contain a regular artifacts/ directory")
    actual_paths, actual_directories = _artifact_inventory(artifact_root, bundle_root)
    declared_paths = set(artifact_by_path)
    if actual_paths != declared_paths:
        raise BundleError(
            "artifact inventory differs: "
            f"undeclared={sorted(actual_paths - declared_paths)}, "
            f"missing={sorted(declared_paths - actual_paths)}"
        )
    declared_directories = {"artifacts"}
    for rel in declared_paths:
        parent = PurePosixPath(rel).parent
        while parent != PurePosixPath("."):
            declared_directories.add(parent.as_posix())
            parent = parent.parent
    if actual_directories != declared_directories:
        raise BundleError(
            "artifact directory inventory differs: "
            f"undeclared={sorted(actual_directories - declared_directories)}, "
            f"missing={sorted(declared_directories - actual_directories)}"
        )

    claims = _list(manifest["claims"], "claims")
    if not claims:
        raise BundleError("claims must not be empty")
    claim_ids: set[str] = set()
    compute_claims: list[dict[str, Any]] = []
    for index, item in enumerate(claims):
        label = f"claims[{index}]"
        claim = _object(item, label)
        _exact_keys(claim, {"id", "evidence", "requires_applied_compute"}, label)
        claim_id = _string(claim["id"], f"{label}.id")
        if not _SLUG.fullmatch(claim_id) or claim_id in claim_ids:
            raise BundleError(f"{label}.id must be a unique lowercase slug")
        claim_ids.add(claim_id)
        evidence = _string_list(claim["evidence"], f"{label}.evidence")
        if not evidence or len(set(evidence)) != len(evidence):
            raise BundleError(f"{label}.evidence must contain unique artifact paths")
        for path in evidence:
            rel = _safe_relative_path(path, f"{label}.evidence", beneath="artifacts")
            if rel not in artifact_by_path:
                raise BundleError(f"{label} names undeclared evidence: {rel}")
        if not isinstance(claim["requires_applied_compute"], bool):
            raise BundleError(f"{label}.requires_applied_compute must be boolean")
        if claim["requires_applied_compute"]:
            compute_claims.append(claim)

    _validate_attestation(
        bundle_root=bundle_root,
        runtime=runtime,
        artifact_by_path=artifact_by_path,
        compute_claims=compute_claims,
    )
    return manifest


def validate_promotion(
    promotion_path: Path,
    manifest_path: Path,
    *,
    expected: dict[str, str],
    expected_claims: list[dict[str, Any]],
    expected_applied_compute: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate a capability-promotion receipt against a valid bundle."""

    _reject_symlink_traversal(promotion_path, "promotion receipt")
    if promotion_path.is_symlink() or not promotion_path.is_file():
        raise BundleError(
            f"promotion receipt must be a regular file, not a symlink: {promotion_path}"
        )
    if promotion_path.name != "promotion.json" or (
        promotion_path.parent.resolve() != manifest_path.parent.resolve()
    ):
        raise BundleError("promotion receipt must be the bundle's own promotion.json")
    promotion_bytes = _file_size(
        promotion_path,
        "promotion receipt",
        limit=MAX_BUNDLE_BYTES,
    )
    promotion = _read_json(promotion_path, "promotion receipt")
    _exact_keys(
        promotion,
        {
            "schema_version",
            "manifest",
            "manifest_sha256",
            "authority",
            "source_revision",
            "review_repository",
            "reviewed_head",
            "redaction_reviewer",
            "runtime",
            "claims",
        },
        "promotion receipt",
    )
    if (
        type(promotion["schema_version"]) is not int
        or promotion["schema_version"] != SCHEMA_VERSION
    ):
        raise BundleError("promotion schema_version differs from the bundle contract")
    rel_manifest = _safe_relative_path(promotion["manifest"], "promotion.manifest")
    if rel_manifest != "bundle.json":
        raise BundleError("promotion receipt must name bundle.json in its own directory")
    resolved_manifest = (promotion_path.parent / rel_manifest).resolve()
    if resolved_manifest != manifest_path.resolve():
        raise BundleError("promotion receipt names a different bundle manifest")
    expected_manifest_digest = _string(promotion["manifest_sha256"], "promotion.manifest_sha256")
    if not _SHA256.fullmatch(expected_manifest_digest):
        raise BundleError("promotion.manifest_sha256 must be lowercase sha256")
    if _sha256(manifest_path) != expected_manifest_digest:
        raise BundleError("promotion receipt's manifest digest does not match")

    manifest = validate_bundle(manifest_path)
    envelope_bytes = promotion_bytes + _file_size(
        manifest_path,
        "bundle manifest",
        limit=MAX_BUNDLE_BYTES,
    )
    for artifact in manifest["artifacts"]:
        envelope_bytes += _file_size(
            manifest_path.parent / artifact["path"],
            f"artifact {artifact['path']}",
            limit=MAX_ARTIFACT_BYTES,
        )
        if envelope_bytes > MAX_BUNDLE_BYTES:
            raise BundleError("bundle envelope exceeds the bundle byte limit")
    _safe_relative_path(promotion["authority"], "promotion.authority")
    if promotion["source_revision"] != manifest["source"]["revision"]:
        raise BundleError("promotion source revision does not match the bundle")
    if promotion["review_repository"] != manifest["review"]["repository"]:
        raise BundleError("promotion review repository does not match the bundle")
    if promotion["reviewed_head"] != manifest["review"]["head"]:
        raise BundleError("promotion reviewed head does not match the bundle")
    if promotion["redaction_reviewer"] != manifest["redaction"]["reviewer"]:
        raise BundleError("promotion redaction reviewer does not match the bundle")
    runtime = _object(promotion["runtime"], "promotion.runtime")
    _exact_keys(
        runtime,
        {"name", "client_version", "applied_compute"},
        "promotion.runtime",
    )
    expected_runtime = {
        "name": manifest["runtime"]["name"],
        "client_version": manifest["runtime"]["client_version"],
        "applied_compute": manifest["runtime"]["applied_compute"],
    }
    if runtime != expected_runtime:
        raise BundleError("promotion runtime does not match the bundle")
    promoted_claims = _string_list(promotion["claims"], "promotion.claims")
    if not promoted_claims or len(set(promoted_claims)) != len(promoted_claims):
        raise BundleError("promotion.claims must contain unique claim ids")
    available = {claim["id"] for claim in manifest["claims"]}
    unknown = sorted(set(promoted_claims) - available)
    if unknown:
        raise BundleError(f"promotion names claims absent from the bundle: {unknown}")
    if manifest["claims"] != expected_claims:
        raise BundleError("bundle claims do not match the independent expectation")
    if promoted_claims != [claim["id"] for claim in expected_claims]:
        raise BundleError("promotion claims do not match the independent expectation")
    compute_required = any(
        claim["requires_applied_compute"] for claim in expected_claims
    )
    if compute_required and expected_applied_compute is None:
        raise BundleError(
            "applied-compute claims require an independent applied-compute expectation"
        )
    if not compute_required and expected_applied_compute is not None:
        raise BundleError(
            "an applied-compute expectation requires an applied-compute claim"
        )
    if runtime["applied_compute"] != expected_applied_compute:
        raise BundleError(
            "promotion applied compute does not match the independent expectation"
        )

    actual_binding = {
        "authority": promotion["authority"],
        "source_repository": manifest["source"]["repository"],
        "source_revision": promotion["source_revision"],
        "review_repository": promotion["review_repository"],
        "reviewed_head": promotion["reviewed_head"],
        "redaction_reviewer": promotion["redaction_reviewer"],
        "runtime": runtime["name"],
        "client_version": runtime["client_version"],
    }
    for field, expected_value in expected.items():
        if actual_binding[field] != expected_value:
            raise BundleError(
                f"promotion {field.replace('_', ' ')} does not match the independent expectation"
            )
    return promotion


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to bundle.json")
    parser.add_argument("--promotion", type=Path, help="promotion receipt to bind and verify")
    parser.add_argument(
        "--expect-authority",
        help="independently selected capability-authority repository path",
    )
    parser.add_argument(
        "--expect-source-repository",
        help="independently observed source repository identity",
    )
    parser.add_argument(
        "--expect-source-revision",
        help="independently observed full source Git sha",
    )
    parser.add_argument(
        "--expect-reviewed-head",
        help="independently observed full reviewed-head Git sha",
    )
    parser.add_argument(
        "--expect-review-repository",
        help="independently observed repository containing the reviewed head",
    )
    parser.add_argument(
        "--expect-redaction-reviewer",
        help="independently selected redaction reviewer identity",
    )
    parser.add_argument("--expect-runtime", help="independently observed runtime name")
    parser.add_argument(
        "--expect-client-version",
        help="independently observed exact runtime client version",
    )
    parser.add_argument(
        "--expect-applied-compute",
        help=(
            "compact JSON object fixing model, effort, cwd, session_id, and attestation "
            "for promoted claims that depend on applied compute"
        ),
    )
    parser.add_argument(
        "--expect-claim",
        action="append",
        default=[],
        help=(
            "repeatable compact JSON object fixing one promoted claim's id, evidence, "
            "and requires_applied_compute value independently of the bundle"
        ),
    )
    parser.add_argument("--json", action="store_true", help="print the verification result as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = validate_bundle(args.manifest)
        promoted = None
        expected = {
            "authority": args.expect_authority,
            "source_repository": args.expect_source_repository,
            "source_revision": args.expect_source_revision,
            "review_repository": args.expect_review_repository,
            "reviewed_head": args.expect_reviewed_head,
            "redaction_reviewer": args.expect_redaction_reviewer,
            "runtime": args.expect_runtime,
            "client_version": args.expect_client_version,
        }
        if args.promotion is not None:
            missing = sorted(field for field, value in expected.items() if value is None)
            if not args.expect_claim:
                missing.append("claims")
            if missing:
                raise BundleError(
                    "promotion requires independent expected bindings: " + ", ".join(missing)
                )
            expected_values = {
                field: _string(value, f"expected {field}") for field, value in expected.items()
            }
            _safe_relative_path(expected_values["authority"], "expected authority")
            _validate_revision(expected_values["source_revision"], "expected source revision")
            _validate_revision(expected_values["reviewed_head"], "expected reviewed head")
            if len(args.expect_claim) > MAX_ARTIFACT_COUNT:
                raise BundleError("expected claims exceeds the claim-count limit")
            expected_claims: list[dict[str, Any]] = []
            expected_claim_ids: set[str] = set()
            for index, raw_claim in enumerate(args.expect_claim):
                label = f"expected claims[{index}]"
                if len(raw_claim.encode("utf-8")) > MAX_ARTIFACT_BYTES:
                    raise BundleError(f"{label} exceeds the byte limit")
                claim = _object(
                    _parse_json(raw_claim, label, Path("<command-line>")),
                    label,
                )
                _exact_keys(claim, {"id", "evidence", "requires_applied_compute"}, label)
                claim_id = _string(claim["id"], f"{label}.id")
                if not _SLUG.fullmatch(claim_id) or claim_id in expected_claim_ids:
                    raise BundleError(f"{label}.id must be a unique lowercase slug")
                expected_claim_ids.add(claim_id)
                evidence = _string_list(claim["evidence"], f"{label}.evidence")
                if not evidence or len(evidence) != len(set(evidence)):
                    raise BundleError(f"{label}.evidence must contain unique artifact paths")
                for path in evidence:
                    _safe_relative_path(path, f"{label}.evidence", beneath="artifacts")
                if not isinstance(claim["requires_applied_compute"], bool):
                    raise BundleError(f"{label}.requires_applied_compute must be boolean")
                expected_claims.append(claim)
            compute_required = any(
                claim["requires_applied_compute"] for claim in expected_claims
            )
            expected_applied_compute = None
            if args.expect_applied_compute is not None:
                label = "expected applied compute"
                if len(args.expect_applied_compute.encode("utf-8")) > MAX_ARTIFACT_BYTES:
                    raise BundleError(f"{label} exceeds the byte limit")
                expected_applied_compute = _object(
                    _parse_json(
                        args.expect_applied_compute,
                        label,
                        Path("<command-line>"),
                    ),
                    label,
                )
                _exact_keys(
                    expected_applied_compute,
                    {"model", "effort", "cwd", "session_id", "attestation"},
                    label,
                )
                for key in ("model", "effort", "cwd", "session_id"):
                    _string_without_controls(
                        expected_applied_compute[key],
                        f"{label}.{key}",
                    )
                _safe_relative_path(
                    expected_applied_compute["attestation"],
                    f"{label}.attestation",
                    beneath="artifacts",
                )
            if compute_required and expected_applied_compute is None:
                raise BundleError(
                    "promotion requires independent expected bindings: applied_compute"
                )
            if not compute_required and expected_applied_compute is not None:
                raise BundleError(
                    "an applied-compute expectation requires an applied-compute claim"
                )
            promoted = validate_promotion(
                args.promotion,
                args.manifest,
                expected=expected_values,
                expected_claims=expected_claims,
                expected_applied_compute=expected_applied_compute,
            )
        elif (args.manifest.parent / "promotion.json").exists():
            raise BundleError(
                "a retained promotion.json requires --promotion and independent expected bindings"
            )
        elif (
            any(value is not None for value in expected.values())
            or args.expect_claim
            or args.expect_applied_compute is not None
        ):
            raise BundleError("expected promotion bindings require --promotion")
    except BundleError as exc:
        print(f"live-validation evidence refused: {exc}", file=sys.stderr)
        return 2
    result = {
        "status": "verified",
        "bundle_id": manifest["bundle_id"],
        "promotion": promoted is not None,
        "claims": promoted["claims"] if promoted is not None else [],
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        suffix = " with promotion receipt" if promoted is not None else ""
        print(f"verified live-validation bundle {manifest['bundle_id']}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
