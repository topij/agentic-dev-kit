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
      --expect-reviewed-head <full-reviewed-head-sha> \
      --expect-runtime codex \
      --expect-client-version "codex-cli <version>"

The command exits 0 only when every requested check passes and exits 2 for an
invalid bundle, promotion receipt, or invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
MAX_ARTIFACT_BYTES = 1_048_576
MAX_BUNDLE_BYTES = 8_388_608

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
    }
)
ALLOWED_SUFFIXES = frozenset({".diff", ".json", ".md", ".patch", ".txt"})
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
_FORBIDDEN_JSON_KEY = re.compile(
    r"(?:^|_)(?:api_?key|auth|authorization|bearer|credential|password|secret|token)(?:$|_)",
    re.IGNORECASE,
)
_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}=*", re.IGNORECASE),
)


class BundleError(ValueError):
    """A condition that makes retained evidence or promotion unsafe to trust."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
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


def _string_list(value: Any, label: str) -> list[str]:
    items = _list(value, label)
    return [_string(item, f"{label}[{index}]") for index, item in enumerate(items)]


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise BundleError(f"{label} keys differ: missing={missing}, extra={extra}")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BundleError(f"{label} is unreadable: {path}: {exc}") from exc
    for pattern in _FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(raw):
            raise BundleError(f"{label} contains credential-like content: {path}")
    try:
        value = _object(json.loads(raw), label)
    except json.JSONDecodeError as exc:
        raise BundleError(f"{label} is not valid JSON: {path}: {exc}") from exc
    except RecursionError as exc:
        raise BundleError(f"{label} exceeds the supported JSON nesting depth: {path}") from exc
    try:
        _scan_json_keys(value, label)
    except RecursionError as exc:
        raise BundleError(f"{label} exceeds the supported JSON nesting depth: {path}") from exc
    return value


def _safe_relative_path(value: Any, label: str, *, beneath: str | None = None) -> str:
    text = _string(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise BundleError(f"{label} must be a canonical relative path: {text}")
    if any(part.startswith(".") for part in path.parts):
        raise BundleError(f"{label} must not contain hidden path components: {text}")
    if beneath is not None and (not path.parts or path.parts[0] != beneath):
        raise BundleError(f"{label} must be beneath {beneath}/: {text}")
    return text


def _scan_json_keys(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _FORBIDDEN_JSON_KEY.search(str(key)):
                raise BundleError(f"{label} contains forbidden credential-like key {key!r}")
            _scan_json_keys(child, label)
    elif isinstance(value, list):
        for child in value:
            _scan_json_keys(child, label)


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
    for pattern in _FORBIDDEN_VALUE_PATTERNS:
        if pattern.search(text):
            raise BundleError(f"{label} contains credential-like content: {path}")
    if path.suffix == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise BundleError(f"{label} is not valid JSON: {path}: {exc}") from exc
        except RecursionError as exc:
            raise BundleError(
                f"{label} exceeds the supported JSON nesting depth: {path}"
            ) from exc
        try:
            _scan_json_keys(value, label)
        except RecursionError as exc:
            raise BundleError(
                f"{label} exceeds the supported JSON nesting depth: {path}"
            ) from exc
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
        _string(compute[key], f"runtime.applied_compute.{key}")
    attestation_path = _safe_relative_path(
        compute["attestation"], "runtime.applied_compute.attestation", beneath="artifacts"
    )
    record = artifact_by_path.get(attestation_path)
    if record is None:
        raise BundleError("runtime.applied_compute.attestation is not a declared artifact")
    if record["kind"] != "runtime-attestation":
        raise BundleError("applied-compute attestation must have kind runtime-attestation")
    if record["observer"] != "runtime-session-context":
        raise BundleError(
            "applied-compute attestation observer must be runtime-session-context"
        )
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

    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BundleError(f"bundle manifest must be a regular file, not a symlink: {manifest_path}")
    manifest = _read_json(manifest_path, "bundle manifest")
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
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise BundleError(f"unsupported schema_version: {manifest['schema_version']!r}")
    bundle_id = _string(manifest["bundle_id"], "bundle_id")
    if not _SLUG.fullmatch(bundle_id):
        raise BundleError("bundle_id must be a lowercase slug")

    source = _object(manifest["source"], "source")
    _exact_keys(source, {"repository", "revision"}, "source")
    _string(source["repository"], "source.repository")
    _validate_revision(source["revision"], "source.revision")

    review = _object(manifest["review"], "review")
    _exact_keys(review, {"head", "observer"}, "review")
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
    if runtime["session_persistence"] not in {"persistent", "not-applicable", "ephemeral"}:
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
    artifact_by_path: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for index, item in enumerate(artifacts):
        label = f"artifacts[{index}]"
        record = _object(item, label)
        _exact_keys(record, {"path", "sha256", "kind", "observer"}, label)
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
        path = bundle_root / rel
        if path.is_symlink() or not path.is_file():
            raise BundleError(f"declared artifact is absent or not a regular file: {rel}")
        if _sha256(path) != digest:
            raise BundleError(f"artifact digest mismatch: {rel}")
        total_bytes += _scan_artifact(path, label)
        artifact_by_path[rel] = record
    if total_bytes > MAX_BUNDLE_BYTES:
        raise BundleError("declared artifacts exceed the bundle byte limit")

    artifact_root = bundle_root / "artifacts"
    if artifact_root.is_symlink() or not artifact_root.is_dir():
        raise BundleError("bundle must contain a regular artifacts/ directory")
    actual_paths: set[str] = set()
    for path in artifact_root.rglob("*"):
        if path.is_symlink():
            raise BundleError(f"artifact tree contains a symlink: {path.relative_to(bundle_root)}")
        if path.is_file():
            actual_paths.add(path.relative_to(bundle_root).as_posix())
    declared_paths = set(artifact_by_path)
    if actual_paths != declared_paths:
        raise BundleError(
            "artifact inventory differs: "
            f"undeclared={sorted(actual_paths - declared_paths)}, "
            f"missing={sorted(declared_paths - actual_paths)}"
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
) -> dict[str, Any]:
    """Validate a capability-promotion receipt against a valid bundle."""

    if promotion_path.is_symlink() or not promotion_path.is_file():
        raise BundleError(
            f"promotion receipt must be a regular file, not a symlink: {promotion_path}"
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
            "reviewed_head",
            "runtime",
            "claims",
        },
        "promotion receipt",
    )
    if promotion["schema_version"] != SCHEMA_VERSION:
        raise BundleError("promotion schema_version differs from the bundle contract")
    rel_manifest = _safe_relative_path(promotion["manifest"], "promotion.manifest")
    resolved_manifest = (promotion_path.parent / rel_manifest).resolve()
    if resolved_manifest != manifest_path.resolve():
        raise BundleError("promotion receipt names a different bundle manifest")
    expected_manifest_digest = _string(
        promotion["manifest_sha256"], "promotion.manifest_sha256"
    )
    if not _SHA256.fullmatch(expected_manifest_digest):
        raise BundleError("promotion.manifest_sha256 must be lowercase sha256")
    if _sha256(manifest_path) != expected_manifest_digest:
        raise BundleError("promotion receipt's manifest digest does not match")

    manifest = validate_bundle(manifest_path)
    _safe_relative_path(promotion["authority"], "promotion.authority")
    if promotion["source_revision"] != manifest["source"]["revision"]:
        raise BundleError("promotion source revision does not match the bundle")
    if promotion["reviewed_head"] != manifest["review"]["head"]:
        raise BundleError("promotion reviewed head does not match the bundle")
    runtime = _object(promotion["runtime"], "promotion.runtime")
    _exact_keys(runtime, {"name", "client_version"}, "promotion.runtime")
    expected_runtime = {
        "name": manifest["runtime"]["name"],
        "client_version": manifest["runtime"]["client_version"],
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

    actual_binding = {
        "authority": promotion["authority"],
        "source_repository": manifest["source"]["repository"],
        "source_revision": promotion["source_revision"],
        "reviewed_head": promotion["reviewed_head"],
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
    parser.add_argument("--expect-runtime", help="independently observed runtime name")
    parser.add_argument(
        "--expect-client-version",
        help="independently observed exact runtime client version",
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
            "reviewed_head": args.expect_reviewed_head,
            "runtime": args.expect_runtime,
            "client_version": args.expect_client_version,
        }
        if args.promotion is not None:
            missing = sorted(field for field, value in expected.items() if value is None)
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
            promoted = validate_promotion(
                args.promotion,
                args.manifest,
                expected=expected_values,
            )
        elif any(value is not None for value in expected.values()):
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
