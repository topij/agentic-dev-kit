"""Behavioral and hostile coverage for retained live-validation evidence.

The dangerous false-success is a plausible narrative or digest surviving after the
bytes it names disappeared. These tests therefore drive the public CLI against real
files. They do not import an internal helper and conclude that the helper agrees with
itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE = engine_dir(Path(__file__).resolve()) / "verify_live_validation_bundle.py"
SOURCE = "1" * 40
REVIEWED = "2" * 40
FIXTURE_EXPECTATIONS = {
    "authority": "docs/agentic-dev-kit/runtime-parity.md",
    "source_repository": "https://github.com/example/source",
    "source_revision": SOURCE,
    "reviewed_head": REVIEWED,
    "runtime": "codex",
    "client_version": "codex-cli example",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "evidence"
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True)
    attestation_path = artifacts / "runtime-attestation.json"
    forge_path = artifacts / "forge-readback.json"
    _write_json(
        attestation_path,
        {
            "session_id": "session-example",
            "turn_context": {
                "cwd": "/private/tmp/synthetic/repo",
                "effort": "max",
                "model": "gpt-example",
            },
        },
    )
    _write_json(
        forge_path,
        {"head": REVIEWED, "state": "OPEN", "visibility": "PRIVATE"},
    )
    manifest = {
        "schema_version": 1,
        "bundle_id": "example-live-validation",
        "source": {
            "repository": "https://github.com/example/source",
            "revision": SOURCE,
        },
        "review": {"head": REVIEWED, "observer": "forge-pr-readback"},
        "runtime": {
            "name": "codex",
            "client_version": "codex-cli example",
            "session_persistence": "persistent",
            "applied_compute": {
                "model": "gpt-example",
                "effort": "max",
                "cwd": "/private/tmp/synthetic/repo",
                "session_id": "session-example",
                "attestation": "artifacts/runtime-attestation.json",
            },
        },
        "redaction": {
            "reviewed": True,
            "reviewer": "fixture-reviewer",
            "excluded": [
                "authentication-material",
                "credentials",
                "tokens",
                "unrelated-user-data",
                "unrelated-workspace-data",
            ],
        },
        "artifacts": [
            {
                "path": "artifacts/runtime-attestation.json",
                "sha256": _sha(attestation_path),
                "kind": "runtime-attestation",
                "observer": "runtime-session-context",
            },
            {
                "path": "artifacts/forge-readback.json",
                "sha256": _sha(forge_path),
                "kind": "forge-readback",
                "observer": "github-api",
            },
        ],
        "claims": [
            {
                "id": "applied-compute-and-reviewed-head",
                "evidence": [
                    "artifacts/runtime-attestation.json",
                    "artifacts/forge-readback.json",
                ],
                "requires_applied_compute": True,
            }
        ],
    }
    manifest_path = root / "bundle.json"
    _write_json(manifest_path, manifest)
    promotion = {
        "schema_version": 1,
        "manifest": "bundle.json",
        "manifest_sha256": _sha(manifest_path),
        "authority": "docs/agentic-dev-kit/runtime-parity.md",
        "source_revision": SOURCE,
        "reviewed_head": REVIEWED,
        "runtime": {"name": "codex", "client_version": "codex-cli example"},
        "claims": ["applied-compute-and-reviewed-head"],
    }
    promotion_path = root / "promotion.json"
    _write_json(promotion_path, promotion)
    return manifest_path, promotion_path


def _run(
    manifest: Path,
    promotion: Path | None = None,
    *,
    expectations: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(ENGINE), str(manifest), "--json"]
    if promotion is not None:
        argv.extend(["--promotion", str(promotion)])
        bindings = FIXTURE_EXPECTATIONS if expectations is None else expectations
        for field, value in bindings.items():
            argv.extend([f"--expect-{field.replace('_', '-')}", value])
    return subprocess.run(argv, capture_output=True, text=True, check=False)


def _refresh_promotion_digest(manifest: Path, promotion: Path) -> None:
    value = json.loads(promotion.read_text(encoding="utf-8"))
    value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, value)


def test_a_complete_bundle_and_promotion_receipt_verify(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    result = _run(manifest, promotion)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "bundle_id": "example-live-validation",
        "claims": ["applied-compute-and-reviewed-head"],
        "promotion": True,
        "status": "verified",
    }


@pytest.mark.parametrize("mutation", ["absent", "altered"])
def test_prose_or_a_digest_cannot_outlive_the_artifact(tmp_path: Path, mutation: str) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    if mutation == "absent":
        artifact.unlink()
    else:
        artifact.write_text('{"head":"foreign"}\n', encoding="utf-8")
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "absent" in result.stderr or "digest mismatch" in result.stderr


def test_a_self_consistent_bundle_for_the_wrong_revision_cannot_promote(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = "3" * 40
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = "3" * 40
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "source revision does not match the independent expectation" in result.stderr


@pytest.mark.parametrize(
    "field",
    ["source_revision", "reviewed_head", "runtime", "client_version"],
)
def test_promotion_receipt_repeated_fields_must_match_the_manifest(
    tmp_path: Path,
    field: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    if field == "source_revision":
        promotion_value["source_revision"] = "3" * 40
    elif field == "reviewed_head":
        promotion_value["reviewed_head"] = "4" * 40
    elif field == "runtime":
        promotion_value["runtime"]["name"] = "claude"
    else:
        promotion_value["runtime"]["client_version"] = "codex-cli fabricated"
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "does not match the bundle" in result.stderr


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("authority", "docs/foreign-authority.md"),
        ("source_repository", "https://github.com/example/foreign"),
        ("reviewed_head", "4" * 40),
        ("runtime", "claude"),
        ("client_version", "codex-cli fabricated"),
    ],
)
def test_other_self_consistent_promotion_relabeling_is_refused(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    if field == "authority":
        promotion_value["authority"] = replacement
    elif field == "source_repository":
        manifest_value["source"]["repository"] = replacement
    elif field == "reviewed_head":
        manifest_value["review"]["head"] = replacement
        promotion_value["reviewed_head"] = replacement
    elif field == "runtime":
        manifest_value["runtime"]["name"] = replacement
        promotion_value["runtime"]["name"] = replacement
    else:
        manifest_value["runtime"]["client_version"] = replacement
        promotion_value["runtime"]["client_version"] = replacement
    _write_json(manifest, manifest_value)
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert f"promotion {field.replace('_', ' ')}" in result.stderr
    assert "independent expectation" in result.stderr


def test_a_promotion_without_independent_expected_bindings_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            str(manifest),
            "--promotion",
            str(promotion),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "promotion requires independent expected bindings" in result.stderr


def test_extreme_json_nesting_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    manifest = tmp_path / "bundle.json"
    manifest.write_text("[" * 200_000 + '"value"' + "]" * 200_000, encoding="utf-8")

    result = _run(manifest)

    assert result.returncode == 2
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("field", ["excluded", "evidence", "promoted_claims"])
def test_malformed_nested_values_use_the_documented_refusal_exit(
    tmp_path: Path,
    field: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    if field == "excluded":
        manifest_value["redaction"]["excluded"] = [{}]
    elif field == "evidence":
        manifest_value["claims"][0]["evidence"] = [{}]
    else:
        promotion_value["claims"] = [{}]
    _write_json(manifest, manifest_value)
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "must be a non-empty string" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("target", ["manifest", "attestation", "promotion"])
def test_duplicate_json_members_are_refused(tmp_path: Path, target: str) -> None:
    manifest, promotion = _fixture(tmp_path)
    if target == "manifest":
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(
            text.replace('{\n  "artifacts"', '{\n  "bundle_id": "decoy",\n  "artifacts"', 1),
            encoding="utf-8",
        )
    elif target == "attestation":
        artifact = manifest.parent / "artifacts" / "runtime-attestation.json"
        text = artifact.read_text(encoding="utf-8")
        artifact.write_text(
            text.replace(
                '    "model": "gpt-example"',
                '    "model": "decoy",\n    "model": "gpt-example"',
                1,
            ),
            encoding="utf-8",
        )
        value = json.loads(manifest.read_text(encoding="utf-8"))
        value["artifacts"][0]["sha256"] = _sha(artifact)
        _write_json(manifest, value)
        _refresh_promotion_digest(manifest, promotion)
    else:
        text = promotion.read_text(encoding="utf-8")
        promotion.write_text(
            text.replace(
                '{\n  "authority"',
                '{\n  "authority": "docs/decoy.md",\n  "authority"',
                1,
            ),
            encoding="utf-8",
        )

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "duplicate JSON key" in result.stderr
    assert "Traceback" not in result.stderr


def test_non_finite_json_values_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.write_text('{"measurement": NaN}\n', encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "non-finite JSON value" in result.stderr


def test_credential_pattern_in_manifest_metadata_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["repository"] = (
        "https://ghp_abcdefghijklmnop@github.com/example/source"
    )
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "bundle manifest contains credential-like content" in result.stderr


@pytest.mark.parametrize(
    "credential_key",
    [
        "api-key",
        "apiKey",
        "access-key",
        "private_key",
        "credentials",
        "tokens",
        "passwords",
        "secrets",
    ],
)
def test_credential_key_variants_are_refused(
    tmp_path: Path,
    credential_key: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    _write_json(
        artifact,
        {credential_key: "credential-material-not-matching-a-token-pattern"},
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "credential-like key" in result.stderr


def test_boolean_schema_version_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    manifest_value["schema_version"] = True
    _write_json(manifest, manifest_value)
    promotion_value["schema_version"] = True
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "schema_version" in result.stderr


def test_invalid_utf8_manifest_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    manifest = tmp_path / "bundle.json"
    manifest.write_bytes(b"\xff")

    result = _run(manifest)

    assert result.returncode == 2
    assert "unreadable" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("invalid_value", [[], {}], ids=["array", "object"])
def test_session_persistence_shape_uses_the_documented_refusal_exit(
    tmp_path: Path,
    invalid_value: object,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["runtime"]["session_persistence"] = invalid_value
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "runtime.session_persistence must be a non-empty string" in result.stderr
    assert "Traceback" not in result.stderr


def test_an_ephemeral_carrier_cannot_support_applied_compute(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["runtime"]["session_persistence"] = "ephemeral"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "ephemeral carrier" in result.stderr


def test_compute_claim_must_name_the_minimal_attestation(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["claims"][0]["evidence"] = ["artifacts/forge-readback.json"]
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "omits its attestation" in result.stderr


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("model", "gpt-fabricated"),
        ("effort", "low"),
        ("cwd", "/private/tmp/foreign/repo"),
        ("session_id", "session-foreign"),
    ],
)
def test_runtime_attestation_must_match_every_applied_compute_binding(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    attestation = manifest.parent / "artifacts" / "runtime-attestation.json"
    attestation_value = json.loads(attestation.read_text(encoding="utf-8"))
    if field == "session_id":
        attestation_value[field] = replacement
    else:
        attestation_value["turn_context"][field] = replacement
    _write_json(attestation, attestation_value)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["artifacts"][0]["sha256"] = _sha(attestation)
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "runtime attestation disagrees" in result.stderr


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="chmod cannot make a file unreadable for this process",
)
def test_an_unreadable_artifact_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.chmod(0o000)
    try:
        result = _run(manifest, promotion)
    finally:
        artifact.chmod(0o644)

    assert result.returncode == 2
    assert "unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_an_undeclared_artifact_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    (manifest.parent / "artifacts" / "forgotten.txt").write_text("raw capture\n")
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "undeclared" in result.stderr


def test_an_undeclared_bundle_root_capture_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    synthetic_credential_marker = "ghp_" + ("a" * 16)
    (manifest.parent / "raw-capture.txt").write_text(
        synthetic_credential_marker + "\n",
        encoding="utf-8",
    )

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "bundle root contains an undeclared entry" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO is a POSIX artifact shape")
def test_a_special_artifact_neighbor_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    os.mkfifo(manifest.parent / "artifacts" / "undeclared.fifo")

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "non-regular entry" in result.stderr
    assert "Traceback" not in result.stderr


def test_an_undeclared_artifact_directory_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    (manifest.parent / "artifacts" / "undeclared").mkdir()

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "artifact directory inventory differs" in result.stderr


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="chmod cannot make a directory unreadable for this process",
)
def test_an_unreadable_artifact_subtree_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    directory = manifest.parent / "artifacts" / "opaque"
    directory.mkdir()
    (directory / "undeclared.txt").write_text("hidden capture\n", encoding="utf-8")
    directory.chmod(0o000)
    try:
        result = _run(manifest, promotion)
    finally:
        directory.chmod(0o755)

    assert result.returncode == 2
    assert "artifact directory is unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_control_characters_in_artifact_paths_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][0]["path"] = "artifacts/nul\u0000.txt"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "must not contain control characters" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_credential_like_json_field_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    _write_json(artifact, {"access_token": "redacted-but-still-the-wrong-artifact"})
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "credential-like key" in result.stderr


def test_the_promotion_receipt_is_bound_to_the_manifest_bytes(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["review"]["observer"] = "a-different-observer"
    _write_json(manifest, value)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "manifest digest does not match" in result.stderr


@pytest.mark.kit_repo_only(
    "saved_plans/codex-writing-lane-evidence_2026-08-30/bundle.json",
    "saved_plans/codex-writing-lane-evidence_2026-08-30/promotion.json",
)
def test_the_promoted_codex_writing_lane_bundle_remains_recomputable() -> None:
    root = find_repo_root(ENGINE)
    bundle = root / "saved_plans/codex-writing-lane-evidence_2026-08-30"
    result = _run(
        bundle / "bundle.json",
        bundle / "promotion.json",
        expectations={
            "authority": "docs/agentic-dev-kit/runtime-parity.md",
            "source_repository": "https://github.com/topij/agentic-dev-kit",
            "source_revision": "bdfd6ee702a630f0575f0c186f51b3bbbcd1810a",
            "reviewed_head": "5c4006d18e65e0443dc7b22f48c099ad07ce1da9",
            "runtime": "codex",
            "client_version": "codex-cli 0.149.1",
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "bundle_id": "codex-writing-lane-2026-08-30",
        "claims": [
            "codex-writing-lane-scoped-write-and-state",
            "codex-writing-lane-ready-private-pr",
            "codex-writing-lane-exact-head-review-receipt",
            "codex-writing-lane-applied-compute",
        ],
        "promotion": True,
        "status": "verified",
    }
