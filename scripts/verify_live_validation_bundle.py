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
      --expect-session-persistence persistent \
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
import unicodedata
from datetime import date, datetime, timezone
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
        "source-git-proof",
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
_SOURCE_LEDGER_REVISION = re.compile(r"^source revision: (?P<revision>[0-9a-f]{40})$")
_SOURCE_LEDGER_FIXTURE = re.compile(
    r"^fixture base revision: (?P<revision>[0-9a-f]{40})$"
)
_SOURCE_LEDGER_SOURCE_PROOF = re.compile(
    r"^source proof: (?P<path>artifacts/[A-Za-z0-9][A-Za-z0-9._/-]*\.json)$"
)
_SOURCE_LEDGER_FIXTURE_PROOF = re.compile(
    r"^fixture proof: (?P<path>artifacts/[A-Za-z0-9][A-Za-z0-9._/-]*\.json)$"
)
_SOURCE_LEDGER_CAPTURE = re.compile(r"^captured on: (?P<captured_on>\d{4}-\d{2}-\d{2})$")
_SOURCE_LEDGER_ROW = re.compile(
    r"^(?P<sha256>[0-9a-f]{64})  "
    r"(?P<path>[A-Za-z0-9][A-Za-z0-9._/-]*)"
    r"  git-blob:(?P<git_blob>[0-9a-f]{40})$"
)
_GIT_TREE_MODE = re.compile(r"^(?:40000|100644|100755|120000|160000)$")
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
        r"\b(?:aws_?secret_?access_?key|client_?secret|auth_?token|password|"
        r"pass_?phrase|api_?key|access_?token|secret|token)\s*[:=]\s*(?:"
        r'\$?"(?:[^"\r\n]|\\\r?\n){6,}"|'
        r"\$?'(?:[^'\r\n]|\\\r?\n){6,}'|[^\s\"\']{6,})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:aws_?secret_?access_?key|client_?secret|auth_?token|password|"
        r"pass_?phrase|api_?key|access_?token|secret|token)\s*:\s*"
        r"[|>][0-9+-]{0,2}[^\r\n]*\r?\n[ \t]+[^\r\n]{6,}",
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


def _git_blob_id(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BundleError(f"source-file bytes are unreadable: {path}: {exc}") from exc
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def _git_object_id(kind: str, data: bytes) -> str:
    payload = f"{kind} {len(data)}\0".encode() + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


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
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        raise BundleError(f"{label} must not contain control characters")
    return value


def _git_text_line(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise BundleError(f"{label} must be a string")
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        raise BundleError(f"{label} must not contain control characters")
    return value


def _string_without_controls(value: Any, label: str) -> str:
    return _string(value, label)


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


def _validate_git_source_proof(
    *,
    bundle_root: Path,
    proof_path: str,
    artifact_by_path: dict[str, dict[str, Any]],
    namespace: str,
    revision: str,
    expected_blobs: dict[str, str],
) -> None:
    record = artifact_by_path.get(proof_path)
    if record is None or record["kind"] != "source-git-proof":
        raise BundleError(f"source ledger names an absent source-git-proof: {proof_path}")
    proof = _read_json(
        bundle_root / proof_path,
        f"source Git proof {proof_path}",
        limit=MAX_ARTIFACT_BYTES,
    )
    _exact_keys(
        proof,
        {"schema_version", "namespace", "revision", "commit_lines", "trees"},
        f"source Git proof {proof_path}",
    )
    if type(proof["schema_version"]) is not int or proof["schema_version"] != SCHEMA_VERSION:
        raise BundleError(f"source Git proof has an unsupported schema version: {proof_path}")
    if _string(proof["namespace"], f"source Git proof {proof_path}.namespace") != namespace:
        raise BundleError(f"source Git proof namespace differs from its ledger: {proof_path}")
    proof_revision = _validate_revision(
        proof["revision"], f"source Git proof {proof_path}.revision"
    )
    if proof_revision != revision:
        raise BundleError(f"source Git proof revision differs from its ledger: {proof_path}")

    commit_lines = _list(proof["commit_lines"], f"source Git proof {proof_path}.commit_lines")
    if not commit_lines:
        raise BundleError(f"source Git proof must retain commit content: {proof_path}")
    normalized_lines = [
        _git_text_line(line, f"source Git proof {proof_path}.commit_lines[{index}]")
        for index, line in enumerate(commit_lines)
    ]
    commit_bytes = ("\n".join(normalized_lines) + "\n").encode("utf-8")
    if _git_object_id("commit", commit_bytes) != revision:
        raise BundleError(f"source Git proof commit does not match its revision: {proof_path}")
    try:
        header_end = normalized_lines.index("")
    except ValueError as exc:
        raise BundleError(f"source Git proof commit has no header boundary: {proof_path}") from exc
    tree_headers = [
        line.removeprefix("tree ")
        for line in normalized_lines[:header_end]
        if line.startswith("tree ")
    ]
    if len(tree_headers) != 1 or not _GIT_SHA.fullmatch(tree_headers[0]):
        raise BundleError(f"source Git proof commit must name exactly one root tree: {proof_path}")
    root_tree = tree_headers[0]

    tree_values = _list(proof["trees"], f"source Git proof {proof_path}.trees")
    if not tree_values:
        raise BundleError(f"source Git proof must retain tree objects: {proof_path}")
    trees: dict[str, dict[str, tuple[str, str]]] = {}
    for tree_index, tree_value in enumerate(tree_values):
        tree_label = f"source Git proof {proof_path}.trees[{tree_index}]"
        tree = _object(tree_value, tree_label)
        _exact_keys(tree, {"oid", "entries"}, tree_label)
        oid = _validate_revision(tree["oid"], f"{tree_label}.oid")
        if oid in trees:
            raise BundleError(f"source Git proof repeats a tree object: {oid}")
        entry_values = _list(tree["entries"], f"{tree_label}.entries")
        entries: dict[str, tuple[str, str]] = {}
        raw = bytearray()
        for entry_index, entry_value in enumerate(entry_values):
            entry_label = f"{tree_label}.entries[{entry_index}]"
            entry = _object(entry_value, entry_label)
            _exact_keys(entry, {"mode", "name", "oid"}, entry_label)
            mode = _string(entry["mode"], f"{entry_label}.mode")
            if not _GIT_TREE_MODE.fullmatch(mode):
                raise BundleError(f"{entry_label}.mode is unsupported")
            name = _string(entry["name"], f"{entry_label}.name")
            if name in {".", ".."} or "/" in name or name in entries:
                raise BundleError(f"{entry_label}.name is not a unique Git tree entry")
            child_oid = _validate_revision(entry["oid"], f"{entry_label}.oid")
            entries[name] = (mode, child_oid)
            raw.extend(mode.encode("ascii") + b" " + name.encode("utf-8") + b"\0")
            raw.extend(bytes.fromhex(child_oid))
        if _git_object_id("tree", bytes(raw)) != oid:
            raise BundleError(f"source Git proof tree content does not match its oid: {oid}")
        trees[oid] = entries

    visited_trees: set[str] = set()
    for git_path, expected_blob in sorted(expected_blobs.items()):
        canonical = _safe_relative_path(git_path, f"source Git proof path {git_path}")
        parts = PurePosixPath(canonical).parts
        tree_oid = root_tree
        for index, part in enumerate(parts):
            entries = trees.get(tree_oid)
            if entries is None:
                raise BundleError(
                    f"source Git proof omits tree {tree_oid} needed for {namespace}/{git_path}"
                )
            visited_trees.add(tree_oid)
            entry = entries.get(part)
            if entry is None:
                raise BundleError(
                    f"source Git proof does not contain {namespace}/{git_path} at {revision}"
                )
            mode, child_oid = entry
            if index < len(parts) - 1:
                if mode != "40000":
                    raise BundleError(
                        f"source Git proof path crosses a non-tree entry: {namespace}/{git_path}"
                    )
                tree_oid = child_oid
            elif mode not in {"100644", "100755"} or child_oid != expected_blob:
                raise BundleError(
                    f"source Git proof blob differs for {namespace}/{git_path} at {revision}"
                )
    unused_trees = sorted(set(trees) - visited_trees)
    if unused_trees:
        raise BundleError(f"source Git proof contains unneeded tree objects: {unused_trees}")


def _validate_source_evidence(
    *,
    bundle_root: Path,
    source_revision: str,
    artifact_by_path: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    source_files = {
        path for path, record in artifact_by_path.items() if record["kind"] == "source-file"
    }
    ledgers = {
        path for path, record in artifact_by_path.items() if record["kind"] == "source-digest"
    }
    proof_files = {
        path
        for path, record in artifact_by_path.items()
        if record["kind"] == "source-git-proof"
    }
    named_source_files: set[str] = set()
    named_proof_files: set[str] = set()
    source_files_by_ledger: dict[str, set[str]] = {}
    proof_requirements: dict[str, tuple[str, str, dict[str, str]]] = {}
    for ledger_path in sorted(ledgers):
        record = artifact_by_path[ledger_path]
        try:
            lines = (bundle_root / ledger_path).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise BundleError(f"source-digest ledger is unreadable: {ledger_path}: {exc}") from exc
        if not lines or _SOURCE_LEDGER_REVISION.fullmatch(lines[0]) is None:
            raise BundleError(
                f"source-digest ledger must begin with source revision: {ledger_path}"
            )
        revision_headers = 0
        fixture_headers = 0
        source_proof_headers = 0
        fixture_proof_headers = 0
        capture_headers = 0
        row_count = 0
        ledger_paths: set[str] = set()
        ledger_proofs: set[str] = set()
        source_proof_path: str | None = None
        fixture_proof_path: str | None = None
        fixture_revision: str | None = None
        ledger_rows: list[tuple[str, str, str]] = []
        for line_number, line in enumerate(lines, start=1):
            revision_match = _SOURCE_LEDGER_REVISION.fullmatch(line)
            if revision_match:
                revision_headers += 1
                if revision_match.group("revision") != source_revision:
                    raise BundleError(
                        "source-digest ledger source revision differs from the bundle: "
                        f"{ledger_path}:{line_number}"
                    )
                continue
            fixture_match = _SOURCE_LEDGER_FIXTURE.fullmatch(line)
            if fixture_match:
                fixture_headers += 1
                fixture_revision = fixture_match.group("revision")
                continue
            source_proof_match = _SOURCE_LEDGER_SOURCE_PROOF.fullmatch(line)
            if source_proof_match:
                source_proof_headers += 1
                source_proof_path = _safe_relative_path(
                    source_proof_match.group("path"),
                    f"source-digest ledger {ledger_path}:{line_number}",
                    beneath="artifacts",
                )
                continue
            fixture_proof_match = _SOURCE_LEDGER_FIXTURE_PROOF.fullmatch(line)
            if fixture_proof_match:
                fixture_proof_headers += 1
                fixture_proof_path = _safe_relative_path(
                    fixture_proof_match.group("path"),
                    f"source-digest ledger {ledger_path}:{line_number}",
                    beneath="artifacts",
                )
                continue
            capture_match = _SOURCE_LEDGER_CAPTURE.fullmatch(line)
            if capture_match:
                capture_headers += 1
                if capture_match.group("captured_on") != record["captured_on"]:
                    raise BundleError(
                        "source-digest ledger capture date differs from its artifact record: "
                        f"{ledger_path}:{line_number}"
                    )
                continue
            row = _SOURCE_LEDGER_ROW.fullmatch(line)
            if row is None:
                raise BundleError(
                    "source-digest ledger has an unsupported line: "
                    f"{ledger_path}:{line_number}"
                )
            row_count += 1
            row_path = row.group("path")
            namespace, separator, git_path = row_path.partition("/")
            if separator != "/" or namespace not in {"source", "fixture"} or not git_path:
                raise BundleError(
                    "source-digest ledger rows must use source/ or fixture/ namespaces: "
                    f"{ledger_path}:{line_number}"
                )
            source_file = _safe_relative_path(
                f"artifacts/{row_path}",
                f"source-digest ledger {ledger_path}:{line_number}",
                beneath="artifacts",
            )
            if source_file in ledger_paths:
                raise BundleError(
                    f"source-digest ledger repeats a source-file path: {source_file}"
                )
            ledger_paths.add(source_file)
            source_record = artifact_by_path.get(source_file)
            if source_record is None or source_record["kind"] != "source-file":
                raise BundleError(
                    "source-digest ledger names bytes without a declared source-file: "
                    f"{source_file}"
                )
            if source_record["sha256"] != row.group("sha256"):
                raise BundleError(
                    "source-digest ledger does not match its source-file digest: "
                    f"{source_file}"
                )
            expected_git_blob = row.group("git_blob")
            if _git_blob_id(bundle_root / source_file) != expected_git_blob:
                raise BundleError(
                    "source-digest ledger does not match its source-file Git blob: "
                    f"{source_file}"
                )
            ledger_rows.append((namespace, git_path, expected_git_blob))
        if revision_headers != 1:
            raise BundleError(
                f"source-digest ledger must contain exactly one revision header: {ledger_path}"
            )
        if fixture_headers > 1:
            raise BundleError(
                f"source-digest ledger repeats its fixture-base header: {ledger_path}"
            )
        if source_proof_headers > 1 or fixture_proof_headers > 1:
            raise BundleError(f"source-digest ledger repeats a Git proof header: {ledger_path}")
        if capture_headers > 1:
            raise BundleError(
                f"source-digest ledger repeats its capture-date header: {ledger_path}"
            )
        if row_count == 0:
            raise BundleError(f"source-digest ledger must name source-file bytes: {ledger_path}")
        namespaces = {namespace for namespace, _, _ in ledger_rows}
        if source_proof_headers != (1 if "source" in namespaces else 0):
            raise BundleError(
                f"source-digest ledger has an invalid source proof header: {ledger_path}"
            )
        fixture_expected = "fixture" in namespaces
        if fixture_headers != (1 if fixture_expected else 0) or fixture_proof_headers != (
            1 if fixture_expected else 0
        ):
            raise BundleError(
                f"source-digest ledger has an invalid fixture proof binding: {ledger_path}"
            )
        for namespace, git_path, expected_blob in ledger_rows:
            if namespace == "source":
                proof_path = source_proof_path
                proof_revision = source_revision
            else:
                proof_path = fixture_proof_path
                proof_revision = fixture_revision
            if proof_path is None or proof_revision is None:
                raise BundleError(
                    f"source-digest ledger omits the {namespace} Git proof binding: {ledger_path}"
                )
            ledger_proofs.add(proof_path)
            existing = proof_requirements.get(proof_path)
            if existing is None:
                required_blobs: dict[str, str] = {}
                proof_requirements[proof_path] = (namespace, proof_revision, required_blobs)
            else:
                existing_namespace, existing_revision, required_blobs = existing
                if existing_namespace != namespace or existing_revision != proof_revision:
                    raise BundleError(f"source Git proof has conflicting ledger bindings: {proof_path}")
            previous_blob = required_blobs.get(git_path)
            if previous_blob is not None and previous_blob != expected_blob:
                raise BundleError(
                    f"source Git proof path has conflicting blob bindings: {namespace}/{git_path}"
                )
            required_blobs[git_path] = expected_blob
        named_source_files.update(ledger_paths)
        named_proof_files.update(ledger_proofs)
        source_files_by_ledger[ledger_path] = ledger_paths | ledger_proofs
    if source_files != named_source_files:
        raise BundleError(
            "source-file inventory differs from the source-digest ledgers: "
            f"unlisted={sorted(source_files - named_source_files)}, "
            f"missing={sorted(named_source_files - source_files)}"
        )
    if proof_files != named_proof_files:
        raise BundleError(
            "source-git-proof inventory differs from the source-digest ledgers: "
            f"unlisted={sorted(proof_files - named_proof_files)}, "
            f"missing={sorted(named_proof_files - proof_files)}"
        )
    for proof_path, (namespace, revision, expected_blobs) in proof_requirements.items():
        _validate_git_source_proof(
            bundle_root=bundle_root,
            proof_path=proof_path,
            artifact_by_path=artifact_by_path,
            namespace=namespace,
            revision=revision,
            expected_blobs=expected_blobs,
        )
    return source_files_by_ledger


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
        if capture_date > datetime.now(timezone.utc).date():
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

    source_files_by_ledger = _validate_source_evidence(
        bundle_root=bundle_root,
        source_revision=source["revision"],
        artifact_by_path=artifact_by_path,
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
        evidence_paths = set(evidence)
        for path in evidence:
            rel = _safe_relative_path(path, f"{label}.evidence", beneath="artifacts")
            if rel not in artifact_by_path:
                raise BundleError(f"{label} names undeclared evidence: {rel}")
        for ledger_path, source_paths in source_files_by_ledger.items():
            if ledger_path in evidence_paths and not source_paths.issubset(evidence_paths):
                raise BundleError(
                    f"{label} names a source-digest ledger without all of its source "
                    f"evidence: {sorted(source_paths - evidence_paths)}"
                )
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
        {"name", "client_version", "session_persistence", "applied_compute"},
        "promotion.runtime",
    )
    expected_runtime = {
        "name": manifest["runtime"]["name"],
        "client_version": manifest["runtime"]["client_version"],
        "session_persistence": manifest["runtime"]["session_persistence"],
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
    claims_by_id = {claim["id"]: claim for claim in manifest["claims"]}
    selected_claims = [claims_by_id[claim_id] for claim_id in promoted_claims]
    if selected_claims != expected_claims:
        raise BundleError("promoted claims do not match the independent expectation")
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
    if compute_required and runtime["applied_compute"] != expected_applied_compute:
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
        "session_persistence": runtime["session_persistence"],
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
        "--expect-session-persistence",
        choices=("persistent", "not-applicable", "ephemeral"),
        help="independently observed runtime session-persistence carrier",
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
            "session_persistence": args.expect_session_persistence,
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
