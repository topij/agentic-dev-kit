"""Behavioral and hostile coverage for retained live-validation evidence.

The dangerous false-success is a plausible narrative or digest surviving after the
bytes it names disappeared. These tests therefore drive the public CLI against real
files. They do not import an internal helper and conclude that the helper agrees with
itself.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE = engine_dir(Path(__file__).resolve()) / "verify_live_validation_bundle.py"
SOURCE = "1" * 40
REVIEWED = "2" * 40


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


def _run(manifest: Path, promotion: Path | None = None) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(ENGINE), str(manifest), "--json"]
    if promotion is not None:
        argv.extend(["--promotion", str(promotion)])
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
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = "3" * 40
    _write_json(promotion, promotion_value)
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "source revision does not match" in result.stderr


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


def test_an_undeclared_artifact_refuses_the_bundle(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    (manifest.parent / "artifacts" / "forgotten.txt").write_text("raw capture\n")
    result = _run(manifest, promotion)
    assert result.returncode == 2
    assert "undeclared" in result.stderr


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
    result = _run(bundle / "bundle.json", bundle / "promotion.json")
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
