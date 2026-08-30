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
from datetime import datetime, timedelta, timezone
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
    "review_repository": "https://github.com/example/review",
    "reviewed_head": REVIEWED,
    "redaction_reviewer": "fixture-reviewer",
    "runtime": "codex",
    "client_version": "codex-cli example",
    "session_persistence": "persistent",
}
FIXTURE_EXPECTED_COMPUTE = {
    "model": "gpt-example",
    "effort": "max",
    "cwd": "/private/tmp/synthetic/repo",
    "session_id": "session-example",
    "attestation": "artifacts/runtime-attestation.json",
}
CODEX_WRITING_HISTORICAL_COMPUTE = {
    "model": "gpt-5.6-sol",
    "effort": "max",
    "cwd": "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
    "session_id": "01a04fb1-0b63-7921-982b-23ff66c200be",
    "attestation": "artifacts/runtime-attestation.json",
}
DEFAULT_EXPECTED_COMPUTE = object()
CODEX_WRITING_SOURCE_PATHS = (
    "config/dev-model.yaml",
    "scripts/dev_session.sh",
    "scripts/launch_lane.py",
    "scripts/lib/kitconfig.py",
    "scripts/lib/repo_root.sh",
)
CODEX_WRITING_SOURCE_EVIDENCE = [
    f"artifacts/source/{path}" for path in CODEX_WRITING_SOURCE_PATHS
]
CODEX_WRITING_EXECUTION_SOURCE_EVIDENCE = [
    "artifacts/execution-source-digests.txt",
    "artifacts/fixture/config/dev-model.yaml",
    *CODEX_WRITING_SOURCE_EVIDENCE,
]
FIXTURE_EXPECTED_CLAIMS = [
    {
        "id": "applied-compute-and-reviewed-head",
        "evidence": [
            "artifacts/runtime-attestation.json",
            "artifacts/forge-readback.json",
        ],
        "requires_applied_compute": True,
    }
]
CODEX_WRITING_EXPECTED_CLAIMS = [
    {
        "evidence": [
            "artifacts/descriptor.json",
            "artifacts/launcher-receipt.json",
            "artifacts/filesystem-readback.txt",
            "artifacts/git-readback.txt",
            "artifacts/source-digests.txt",
            *CODEX_WRITING_EXECUTION_SOURCE_EVIDENCE,
        ],
        "id": "codex-writing-lane-scoped-write-and-state",
        "requires_applied_compute": False,
    },
    {
        "evidence": [
            "artifacts/descriptor.json",
            "artifacts/launcher-receipt.json",
            "artifacts/final-message.txt",
            "artifacts/forge-readback.json",
            "artifacts/git-readback.txt",
            "artifacts/source-digests.txt",
            *CODEX_WRITING_EXECUTION_SOURCE_EVIDENCE,
        ],
        "id": "codex-writing-lane-ready-private-pr",
        "requires_applied_compute": False,
    },
    {
        "evidence": [
            "artifacts/forge-readback.json",
            "artifacts/review-receipt.json",
        ],
        "id": "codex-writing-lane-exact-head-review-receipt",
        "requires_applied_compute": False,
    },
]
CODEX_WRITING_EXPECTED_ARTIFACT_BINDINGS = {
    "artifacts/client-version.txt": (
        "command-capture",
        "codex-cli",
        "/opt/homebrew/bin/codex --version",
    ),
    "artifacts/descriptor.json": (
        "descriptor",
        "dev-session-durable-descriptor",
        "scripts/dev_session.sh new write --headless --runtime codex --merge-class operator",
    ),
    "artifacts/execution-source-digests.txt": (
        "source-digest",
        "synthetic-git-object-readback",
        "git object readback and SHA-256 of each execution source path enumerated in "
        "artifacts/execution-source-digests.txt at "
        "83d3b623305a691dd874df44ca92270daa62ade9",
    ),
    "artifacts/filesystem-readback.txt": (
        "filesystem-readback",
        "cockpit-filesystem-readback",
        "cockpit filesystem readback of descriptor-bound worktree and state root",
    ),
    "artifacts/final-message.txt": (
        "final-message",
        "codex-last-message-file",
        "scripts/launch_lane.py final-message readback for descriptor "
        "ec07f5b3-14fb-4203-8e82-9ef62bfde785",
    ),
    "artifacts/forge-readback.json": (
        "forge-readback",
        "github-api",
        "gh repo view topij/adk-codex-writing-evidence-20260830 --json "
        "name,url,visibility,isPrivate,defaultBranchRef; gh pr view 1 --repo "
        "topij/adk-codex-writing-evidence-20260830 --json "
        "number,url,state,isDraft,mergeStateStatus,headRefName,headRefOid,baseRefName,"
        "commits,files",
    ),
    "artifacts/git-readback.txt": (
        "git-readback",
        "git-remote-and-object-readback",
        "git ls-remote origin refs/heads/dev/write; git diff-tree --no-commit-id "
        "--name-status -r 83d3b623305a691dd874df44ca92270daa62ade9.."
        "5c4006d18e65e0443dc7b22f48c099ad07ce1da9; git show "
        "5c4006d18e65e0443dc7b22f48c099ad07ce1da9:notes/codex-writing-lane.md",
    ),
    "artifacts/launcher-receipt.json": (
        "launcher-receipt",
        "launch-lane-receipt",
        "launch_lane receipt readback for descriptor "
        "ec07f5b3-14fb-4203-8e82-9ef62bfde785",
    ),
    "artifacts/review-receipt.json": (
        "review-receipt",
        "pr-watch-state-and-forge-readback",
        "uv run scripts/pr_watch.py 1 --json",
    ),
    "artifacts/runtime-attestation.json": (
        "runtime-attestation",
        "runtime-session-context",
        "runtime session turn_context readback for 01a04fb1-0b63-7921-982b-23ff66c200be",
    ),
    "artifacts/source-digests.txt": (
        "source-digest",
        "git-object-source-readback",
        "git object readback and SHA-256 of each source path enumerated in "
        "artifacts/source-digests.txt at bdfd6ee702a630f0575f0c186f51b3bbbcd1810a",
    ),
    "artifacts/fixture/config/dev-model.yaml": (
        "source-file",
        "retained-synthetic-git-object-bytes",
        "git show 83d3b623305a691dd874df44ca92270daa62ade9:config/dev-model.yaml",
    ),
    **{
        f"artifacts/source/{path}": (
            "source-file",
            "retained-git-object-bytes",
            f"git show bdfd6ee702a630f0575f0c186f51b3bbbcd1810a:{path}",
        )
        for path in CODEX_WRITING_SOURCE_PATHS
    },
}
CODEX_WRITING_EXPECTED_ARTIFACT_SHA256 = {
    "artifacts/client-version.txt": "ca4fe30a68dd82c6a7af75eeb683f763cfb6554840590a9e345692269ae744f0",
    "artifacts/descriptor.json": "d57a3eeaeef0dd01e208735e71b2c672f409b03ffec06347408864de396691cf",
    "artifacts/execution-source-digests.txt": "c2344c3db6b50233d96faecc02d2559c07406878e851174c3edfa6074f7f7911",
    "artifacts/filesystem-readback.txt": "ae6b54246ec52ac4dfd8079ea44a19499f5966887f5c0673084cf8e6df38dbf0",
    "artifacts/final-message.txt": "56c7748b3099da9282dde6c13e202b529740274577aa44ba4baaea8440051ca0",
    "artifacts/fixture/config/dev-model.yaml": "d4cb774d636655c2c572aed4341c773ae057d09f444494f4b54a56a513035393",
    "artifacts/forge-readback.json": "d6fb6505b19a522d9cc6718d7c09a4510b3e96bbf0ef554a8fa9f63d5910a6c6",
    "artifacts/git-readback.txt": "7767f7e2a40d17c61ec34ce205943a8414eb07810be28414bd50c35f68b47029",
    "artifacts/launcher-receipt.json": "06be15394a823fedf6abee96cd38746f8a6c1f951abbef7a9b4f8f2b92e839cc",
    "artifacts/review-receipt.json": "e71819c7a767c94adcee86c67f683045d7547af3a7a1f96792c8ae645f8c76b4",
    "artifacts/runtime-attestation.json": "95271b822394dd24e9f5d2fdb2ae3c3b5a380a74f0c49bbefd71d8f59fd2deaa",
    "artifacts/source-digests.txt": "079c325ee9f2c80222d4441826f1f19c0509d5d2a4c1f3b5f1af8541bbb166ad",
    "artifacts/source/config/dev-model.yaml": "32d9e7b285a54438975c2aa2d9813adc5d017cef077b6df71564b1ae418a6d92",
    "artifacts/source/scripts/dev_session.sh": "2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba",
    "artifacts/source/scripts/launch_lane.py": "7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6",
    "artifacts/source/scripts/lib/kitconfig.py": "4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6",
    "artifacts/source/scripts/lib/repo_root.sh": "980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555",
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
        "review": {
            "repository": "https://github.com/example/review",
            "head": REVIEWED,
            "observer": "forge-pr-readback",
        },
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
                "capture_request": "runtime session turn_context readback for session-example",
                "captured_on": "2026-08-30",
                "path": "artifacts/runtime-attestation.json",
                "sha256": _sha(attestation_path),
                "kind": "runtime-attestation",
                "observer": "runtime-session-context",
            },
            {
                "capture_request": "gh pr view 1 --json headRefOid,state,isDraft",
                "captured_on": "2026-08-30",
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
        "review_repository": "https://github.com/example/review",
        "reviewed_head": REVIEWED,
        "redaction_reviewer": "fixture-reviewer",
        "runtime": {
            "name": "codex",
            "client_version": "codex-cli example",
            "session_persistence": "persistent",
            "applied_compute": FIXTURE_EXPECTED_COMPUTE,
        },
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
    expected_claims: list[dict[str, object]] | None = None,
    expected_compute: dict[str, object] | None | object = DEFAULT_EXPECTED_COMPUTE,
    env: dict[str, str] | None = None,
    timeout: float = 10,
) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(ENGINE), str(manifest), "--json"]
    if promotion is not None:
        argv.extend(["--promotion", str(promotion)])
        bindings = FIXTURE_EXPECTATIONS if expectations is None else expectations
        for field, value in bindings.items():
            argv.extend([f"--expect-{field.replace('_', '-')}", value])
        claims = FIXTURE_EXPECTED_CLAIMS if expected_claims is None else expected_claims
        for claim in claims:
            argv.extend(["--expect-claim", json.dumps(claim, separators=(",", ":"))])
        compute = (
            FIXTURE_EXPECTED_COMPUTE
            if expected_compute is DEFAULT_EXPECTED_COMPUTE
            else expected_compute
        )
        if compute is not None:
            argv.extend(
                ["--expect-applied-compute", json.dumps(compute, separators=(",", ":"))]
            )
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=timeout,
    )


def _refresh_promotion_digest(manifest: Path, promotion: Path) -> None:
    value = json.loads(promotion.read_text(encoding="utf-8"))
    value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, value)


def _add_source_ledger(
    manifest: Path,
    promotion: Path,
    *,
    include_source_file: bool,
    claim_source_file: bool,
    ledger_digest: str | None = None,
    ledger_git_blob: str | None = None,
) -> list[dict[str, object]]:
    artifacts = manifest.parent / "artifacts"
    source_file = artifacts / "source" / "scripts" / "example.py"
    source_bytes = b"print('retained source')\n"
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        f"source revision: {SOURCE}\n"
        f"{source_digest if ledger_digest is None else ledger_digest}  "
        "source/scripts/example.py"
        f"{'  git-blob:' + ledger_git_blob if ledger_git_blob is not None else ''}\n",
        encoding="utf-8",
    )
    if include_source_file:
        source_file.parent.mkdir(parents=True)
        source_file.write_bytes(source_bytes)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"].append(
        {
            "capture_request": "git object readback and SHA-256 ledger",
            "captured_on": "2026-08-30",
            "path": "artifacts/source-digests.txt",
            "sha256": _sha(ledger),
            "kind": "source-digest",
            "observer": "git-object-source-readback",
        }
    )
    value["claims"][0]["evidence"].append("artifacts/source-digests.txt")
    if include_source_file:
        value["artifacts"].append(
            {
                "capture_request": f"git show {SOURCE}:scripts/example.py",
                "captured_on": "2026-08-30",
                "path": "artifacts/source/scripts/example.py",
                "sha256": source_digest,
                "kind": "source-file",
                "observer": "retained-git-object-bytes",
            }
        )
        if claim_source_file:
            value["claims"][0]["evidence"].append(
                "artifacts/source/scripts/example.py"
            )
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    return json.loads(json.dumps(value["claims"]))


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


def test_a_source_digest_and_its_named_source_file_can_promote(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 0, result.stderr


def test_a_fixture_header_cannot_replace_the_bundle_source_revision(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    ledger = manifest.parent / "artifacts/source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(
            f"source revision: {SOURCE}",
            f"fixture base revision: {'9' * 40}",
        ),
        encoding="utf-8",
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in value["artifacts"]
        if artifact["path"] == "artifacts/source-digests.txt"
    )["sha256"] = _sha(ledger)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "must begin with source revision" in result.stderr


def test_a_source_digest_must_begin_with_the_bundle_source_revision(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    ledger = manifest.parent / "artifacts/source-digests.txt"
    ledger.write_text(
        f"fixture base revision: {'9' * 40}\n" + ledger.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in value["artifacts"]
        if artifact["path"] == "artifacts/source-digests.txt"
    )["sha256"] = _sha(ledger)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "must begin with source revision" in result.stderr


def test_a_source_digest_without_its_named_source_file_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=False,
        claim_source_file=False,
    )

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "source-file" in result.stderr


def test_a_source_digest_must_match_its_named_source_file(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        ledger_digest="0" * 64,
    )

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "does not match its source-file digest" in result.stderr


def test_a_source_digest_git_blob_must_match_its_named_source_file(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        ledger_git_blob="0" * 40,
    )

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "does not match its source-file Git blob" in result.stderr


def test_a_source_digest_claim_must_link_every_named_source_file(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=False,
    )

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "without all of its source-file evidence" in result.stderr


def test_a_bundle_without_a_promotion_receipt_verifies_structurally(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion.unlink()

    result = _run(manifest)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["promotion"] is False


def test_promotion_can_select_a_compute_claim_from_retained_claims(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["claims"].append(
        {
            "id": "retained-but-not-promoted",
            "evidence": ["artifacts/forge-readback.json"],
            "requires_applied_compute": False,
        }
    )
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 0, result.stderr


def test_promotion_can_select_a_non_compute_claim_while_retaining_compute(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    non_compute = {
        "id": "retained-observation",
        "evidence": ["artifacts/forge-readback.json"],
        "requires_applied_compute": False,
    }
    value["claims"].append(non_compute)
    _write_json(manifest, value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["claims"] = [non_compute["id"]]
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(
        manifest,
        promotion,
        expected_claims=[non_compute],
        expected_compute=None,
    )

    assert result.returncode == 0, result.stderr


def test_a_present_promotion_receipt_cannot_be_skipped(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion.write_text("{not-json\n", encoding="utf-8")

    result = _run(manifest)

    assert result.returncode == 2
    assert "requires --promotion" in result.stderr


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
    assert any(
        marker in result.stderr for marker in ("absent", "unreadable", "digest mismatch")
    )


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


@pytest.mark.parametrize("mutation", ["rename", "thin-evidence"])
def test_self_consistent_claim_relabeling_cannot_promote(
    tmp_path: Path,
    mutation: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    if mutation == "rename":
        manifest_value["claims"][0]["id"] = "unrestricted-write-and-merge"
        promotion_value["claims"][0] = "unrestricted-write-and-merge"
    else:
        manifest_value["claims"][0]["evidence"] = [
            "artifacts/runtime-attestation.json"
        ]
    _write_json(manifest, manifest_value)
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "claims do not match the independent expectation" in result.stderr


@pytest.mark.parametrize(
    "field",
    [
        "source_revision",
        "review_repository",
        "reviewed_head",
        "redaction_reviewer",
        "runtime",
        "client_version",
        "session_persistence",
        "applied_compute",
    ],
)
def test_promotion_receipt_repeated_fields_must_match_the_manifest(
    tmp_path: Path,
    field: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    if field == "source_revision":
        promotion_value["source_revision"] = "3" * 40
    elif field == "review_repository":
        promotion_value["review_repository"] = "https://github.com/example/foreign"
    elif field == "reviewed_head":
        promotion_value["reviewed_head"] = "4" * 40
    elif field == "redaction_reviewer":
        promotion_value["redaction_reviewer"] = "self-asserted-reviewer"
    elif field == "runtime":
        promotion_value["runtime"]["name"] = "claude"
    elif field == "session_persistence":
        promotion_value["runtime"]["session_persistence"] = "ephemeral"
    elif field == "applied_compute":
        promotion_value["runtime"]["applied_compute"]["model"] = "gpt-fabricated"
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
        ("review_repository", "https://github.com/example/foreign-review"),
        ("reviewed_head", "4" * 40),
        ("redaction_reviewer", "self-asserted-reviewer"),
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
    elif field == "review_repository":
        manifest_value["review"]["repository"] = replacement
        promotion_value["review_repository"] = replacement
    elif field == "reviewed_head":
        manifest_value["review"]["head"] = replacement
        promotion_value["reviewed_head"] = replacement
    elif field == "redaction_reviewer":
        manifest_value["redaction"]["reviewer"] = replacement
        promotion_value["redaction_reviewer"] = replacement
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


def test_self_consistent_session_persistence_relabeling_is_refused(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    attestation = manifest.parent / "artifacts" / "runtime-attestation.json"
    attestation.unlink()
    manifest_value["runtime"]["session_persistence"] = "ephemeral"
    manifest_value["runtime"]["applied_compute"] = None
    manifest_value["artifacts"] = [manifest_value["artifacts"][1]]
    claim = {
        "id": "reviewed-head",
        "evidence": ["artifacts/forge-readback.json"],
        "requires_applied_compute": False,
    }
    manifest_value["claims"] = [claim]
    promotion_value["runtime"]["session_persistence"] = "ephemeral"
    promotion_value["runtime"]["applied_compute"] = None
    promotion_value["claims"] = ["reviewed-head"]
    _write_json(manifest, manifest_value)
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(
        manifest,
        promotion,
        expected_claims=[claim],
        expected_compute=None,
    )

    assert result.returncode == 2
    assert "session persistence does not match the independent expectation" in result.stderr


def test_self_consistent_applied_compute_relabeling_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    attestation = manifest.parent / "artifacts" / "runtime-attestation.json"
    fabricated = {
        "model": "gpt-fabricated",
        "effort": "low",
        "cwd": "/private/tmp/fabricated/repo",
        "session_id": "session-fabricated",
        "attestation": "artifacts/runtime-attestation.json",
    }
    _write_json(
        attestation,
        {
            "session_id": fabricated["session_id"],
            "turn_context": {
                "model": fabricated["model"],
                "effort": fabricated["effort"],
                "cwd": fabricated["cwd"],
            },
        },
    )
    manifest_value["runtime"]["applied_compute"] = fabricated
    manifest_value["artifacts"][0]["sha256"] = _sha(attestation)
    promotion_value["runtime"]["applied_compute"] = fabricated
    _write_json(manifest, manifest_value)
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "applied compute does not match the independent expectation" in result.stderr


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


def test_an_applied_compute_claim_requires_an_independent_compute_expectation(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)

    result = _run(manifest, promotion, expected_compute=None)

    assert result.returncode == 2
    assert "independent expected bindings: applied_compute" in result.stderr


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


def test_duplicate_artifact_paths_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"].append(dict(value["artifacts"][0]))
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "duplicate artifact path" in result.stderr


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("capture_request", "", "capture_request must be a non-empty string"),
        ("captured_on", "2026/08/30", "captured_on must use YYYY-MM-DD"),
        ("captured_on", "2026-99-99", "captured_on must be a calendar date"),
        ("captured_on", "2999-01-01", "captured_on must not be in the future"),
    ],
)
def test_artifact_measurement_stamps_are_required(
    tmp_path: Path,
    field: str,
    replacement: str,
    message: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][0][field] = replacement
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert message in result.stderr


@pytest.mark.parametrize("zone", ["Etc/GMT+12", "Pacific/Kiritimati"])
@pytest.mark.parametrize(("day_offset", "expected_status"), [(0, 0), (1, 2)])
def test_capture_date_future_check_uses_utc(
    tmp_path: Path,
    zone: str,
    day_offset: int,
    expected_status: int,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    captured_on = (
        datetime.now(timezone.utc).date() + timedelta(days=day_offset)
    ).isoformat()
    value = json.loads(manifest.read_text(encoding="utf-8"))
    for artifact in value["artifacts"]:
        artifact["captured_on"] = captured_on
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        env={**os.environ, "TZ": zone},
    )

    assert result.returncode == expected_status, result.stderr


@pytest.mark.parametrize("number", ["NaN", "1e9999"])
def test_non_finite_json_values_are_refused(tmp_path: Path, number: str) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.write_text(f'{{"measurement": {number}}}\n', encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "non-finite JSON value" in result.stderr


def test_huge_json_integer_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.write_text(
        '{"measurement":' + ("1" * 5_000) + "}\n",
        encoding="utf-8",
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "unsupported JSON integer" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("target", ["manifest", "promotion", "artifact"])
def test_json_escaping_cannot_hide_a_credential_value(
    tmp_path: Path,
    target: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    escaped_marker = r"\u0067hp_abcdefghijklmnop"
    if target == "manifest":
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(
            text.replace(
                "https://github.com/example/source",
                f"https://{escaped_marker}@github.com/example/source",
            ),
            encoding="utf-8",
        )
        _refresh_promotion_digest(manifest, promotion)
    elif target == "promotion":
        text = promotion.read_text(encoding="utf-8")
        promotion.write_text(
            text.replace(
                "docs/agentic-dev-kit/runtime-parity.md",
                f"docs/{escaped_marker}.md",
            ),
            encoding="utf-8",
        )
    else:
        artifact = manifest.parent / "artifacts" / "forge-readback.json"
        artifact.write_text(f'{{"note":"{escaped_marker}"}}\n', encoding="utf-8")
        value = json.loads(manifest.read_text(encoding="utf-8"))
        value["artifacts"][1]["sha256"] = _sha(artifact)
        _write_json(manifest, value)
        _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


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
        "sessionCookies",
        "passphrase",
        "pass_phrase",
        "AWSAccessKeyId",
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


def test_common_aws_access_key_value_shape_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    _write_json(artifact, {"identifier": "AKIAIOSFODNN7EXAMPLE"})
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


@pytest.mark.parametrize(
    "credential_text",
    [
        "Authorization: Basic dXNlcjpwYXNzd29yZA==",
        "password=hunter2",
        'password="hunter2"',
        "password='hunter2'",
        'password=$"hunter2"',
        "password=$'hunter2'",
        'password="hunter' + "\\\n" + '2"',
        "client_secret: supersecretvalue",
        "auth_token=supersecretvalue",
        "password: |\n  supersecretvalue",
        "xoxb-" + "123456789012-123456789012-abcdefghijklmnopqrstuvwx",
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    ],
)
def test_common_credential_text_shapes_are_refused(
    tmp_path: Path,
    credential_text: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.write_text(credential_text + "\n", encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


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


@pytest.mark.parametrize(
    "control",
    ["\u0000", "\u007f", "\u0085"],
    ids=["nul", "del", "nel"],
)
def test_control_characters_in_artifact_paths_are_refused(
    tmp_path: Path,
    control: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][0]["path"] = f"artifacts/control{control}.txt"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "must not contain control characters" in result.stderr
    assert "Traceback" not in result.stderr


def test_control_characters_in_identity_fields_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    controlled_repository = "https://github.com/example/source\u0085suffix"
    value["source"]["repository"] = controlled_repository
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_repository"] = controlled_repository

    result = _run(manifest, promotion, expectations=expectations)

    assert result.returncode == 2
    assert "must not contain control characters" in result.stderr


def test_control_characters_in_applied_compute_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["runtime"]["applied_compute"]["cwd"] = "/synthetic/impossible\u0000cwd"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "runtime.applied_compute.cwd must not contain control characters" in result.stderr


def test_bundle_directory_itself_cannot_be_a_symlink(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "source")
    retained = tmp_path / "retained-evidence"
    retained.symlink_to(manifest.parent, target_is_directory=True)

    result = _run(retained / "bundle.json", retained / "promotion.json")

    assert result.returncode == 2
    assert "bundle manifest path" in result.stderr
    assert "symlink" in result.stderr


def test_a_bundle_path_cannot_traverse_an_ancestor_symlink(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "source")
    manifest.unlink()
    os.mkfifo(manifest)
    alias = tmp_path / "alias"
    alias.symlink_to(manifest.parent.parent, target_is_directory=True)

    result = _run(alias / "evidence" / "bundle.json", alias / "evidence" / "promotion.json")

    assert result.returncode == 2
    assert "must not traverse a symlink" in result.stderr


def test_an_artifact_path_cannot_traverse_an_ancestor_symlink(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path / "source")
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_artifact = outside / "forge-readback.json"
    os.mkfifo(outside_artifact)
    escape = manifest.parent / "artifacts" / "escape"
    escape.symlink_to(outside, target_is_directory=True)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["path"] = "artifacts/escape/forge-readback.json"
    value["claims"][0]["evidence"][1] = "artifacts/escape/forge-readback.json"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "must not traverse a symlink" in result.stderr


def test_a_promotion_path_cannot_traverse_an_ancestor_symlink(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path / "source")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "promotion.json").write_bytes(promotion.read_bytes())
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)

    result = _run(manifest, alias / "promotion.json")

    assert result.returncode == 2
    assert "must not traverse a symlink" in result.stderr


def test_a_symlink_loop_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    loop = tmp_path / "loop"
    loop.symlink_to("loop", target_is_directory=True)

    result = _run(loop / "bundle.json", loop / "promotion.json")

    assert result.returncode == 2
    assert "unreadable" in result.stderr
    assert "Traceback" not in result.stderr


def test_manifest_envelope_bytes_are_bounded_before_parsing(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["redaction"]["reviewer"] = "r" * 8_500_000
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    manifest.chmod(0)
    try:
        result = _run(manifest, promotion)
    finally:
        manifest.chmod(0o600)

    assert result.returncode == 2
    assert "bundle manifest exceeds its byte limit" in result.stderr


def test_artifact_bytes_are_bounded_before_hashing_or_scanning(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact.write_text("x" * 1_100_000, encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    artifact.chmod(0)
    try:
        result = _run(manifest, promotion)
    finally:
        artifact.chmod(0o600)

    assert result.returncode == 2
    assert "artifacts[1] exceeds its byte limit" in result.stderr
    assert "unreadable" not in result.stderr


def test_promotion_bytes_are_bounded_before_parsing(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(promotion.read_text(encoding="utf-8"))
    value["authority"] = "r" * 8_500_000
    _write_json(promotion, value)
    promotion.chmod(0)
    try:
        result = _run(manifest, promotion)
    finally:
        promotion.chmod(0o600)

    assert result.returncode == 2
    assert "promotion receipt exceeds its byte limit" in result.stderr
    assert "unreadable" not in result.stderr


def test_bundle_only_artifact_bytes_are_bounded_by_the_bundle_envelope(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    artifacts = manifest.parent / "artifacts"
    payload = "x" * 1_000_000
    for index in range(9):
        path = artifacts / f"aggregate-{index}.txt"
        artifact_payload = payload
        if index == 8:
            artifact_payload = 'password="hunter2"\n' + payload
        path.write_text(artifact_payload, encoding="utf-8")
        value["artifacts"].append(
            {
                "capture_request": f"synthetic aggregate envelope probe {index}",
                "captured_on": "2026-08-30",
                "path": f"artifacts/{path.name}",
                "sha256": _sha(path),
                "kind": "command-capture",
                "observer": "hostile-envelope-probe",
            }
        )
    _write_json(manifest, value)
    promotion.unlink()

    result = _run(manifest)

    assert result.returncode == 2
    assert "bundle envelope exceeds the bundle byte limit" in result.stderr


def test_promotion_bytes_are_bounded_by_the_bundle_envelope(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    artifacts = manifest.parent / "artifacts"
    sizes = [1_000_000] * 8 + [350_000]
    for index, size in enumerate(sizes):
        path = artifacts / f"promotion-envelope-{index}.txt"
        path.write_text("x" * size, encoding="utf-8")
        value["artifacts"].append(
            {
                "capture_request": f"synthetic promotion envelope probe {index}",
                "captured_on": "2026-08-30",
                "path": f"artifacts/{path.name}",
                "sha256": _sha(path),
                "kind": "command-capture",
                "observer": "hostile-envelope-probe",
            }
        )
    _write_json(manifest, value)
    last = artifacts / "promotion-envelope-8.txt"
    bundle_bytes = manifest.stat().st_size + sum(
        (manifest.parent / artifact["path"]).stat().st_size
        for artifact in value["artifacts"]
    )
    adjusted_size = last.stat().st_size + (8_388_608 - 100 - bundle_bytes)
    assert 0 < adjusted_size <= 1_048_576
    last.write_text("x" * adjusted_size, encoding="utf-8")
    value["artifacts"][-1]["sha256"] = _sha(last)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "bundle envelope exceeds the bundle byte limit" in result.stderr


def test_artifact_count_is_bounded_before_artifact_io(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    template = dict(value["artifacts"][0])
    value["artifacts"] = [
        {**template, "path": f"artifacts/absent-{index}.json"} for index in range(257)
    ]
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "artifact-count limit" in result.stderr


def test_undeclared_artifact_tree_entries_are_bounded(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifacts = manifest.parent / "artifacts"
    for index in range(513):
        (artifacts / f"undeclared-{index}.txt").write_text(
            "capture\n",
            encoding="utf-8",
        )

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "entry-count limit" in result.stderr


def test_promotion_manifest_path_must_be_lexically_canonical(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(promotion.read_text(encoding="utf-8"))
    value["manifest"] = "./bundle.json"
    _write_json(promotion, value)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "canonical relative path" in result.stderr


def test_an_external_promotion_receipt_cannot_replace_the_bundle_receipt(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    external = manifest.parent.parent / "promotion.json"
    value = json.loads(promotion.read_text(encoding="utf-8"))
    value["manifest"] = "evidence/bundle.json"
    _write_json(external, value)

    result = _run(manifest, external)

    assert result.returncode == 2
    assert "bundle's own promotion.json" in result.stderr


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
def test_the_promoted_codex_writing_lane_bundle_remains_structurally_verifiable() -> None:
    root = find_repo_root(ENGINE.parent)
    bundle = root / "saved_plans/codex-writing-lane-evidence_2026-08-30"
    result = _run(
        bundle / "bundle.json",
        bundle / "promotion.json",
        expectations={
            "authority": "docs/agentic-dev-kit/runtime-parity.md",
            "source_repository": "https://github.com/topij/agentic-dev-kit",
            "source_revision": "bdfd6ee702a630f0575f0c186f51b3bbbcd1810a",
            "review_repository": (
                "https://github.com/topij/adk-codex-writing-evidence-20260830"
            ),
            "reviewed_head": "5c4006d18e65e0443dc7b22f48c099ad07ce1da9",
            "redaction_reviewer": "codex-cockpit-gpt-5-6-sol-max",
            "runtime": "codex",
            "client_version": "codex-cli 0.149.1",
            "session_persistence": "persistent",
        },
        expected_claims=CODEX_WRITING_EXPECTED_CLAIMS,
        expected_compute=None,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "bundle_id": "codex-writing-lane-2026-08-30",
        "claims": [
            "codex-writing-lane-scoped-write-and-state",
            "codex-writing-lane-ready-private-pr",
            "codex-writing-lane-exact-head-review-receipt",
        ],
        "promotion": True,
        "status": "verified",
    }


@pytest.mark.kit_repo_only(
    "saved_plans/codex-writing-lane-evidence_2026-08-30/bundle.json",
    "saved_plans/codex-writing-lane-evidence_2026-08-30/promotion.json",
)
def test_the_promoted_codex_writing_lane_claims_remain_independently_recomputable() -> None:
    root = find_repo_root(ENGINE.parent)
    bundle = root / "saved_plans/codex-writing-lane-evidence_2026-08-30"
    manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    promotion = json.loads((bundle / "promotion.json").read_text(encoding="utf-8"))
    artifacts = bundle / "artifacts"
    descriptor = json.loads((artifacts / "descriptor.json").read_text(encoding="utf-8"))
    launcher = json.loads((artifacts / "launcher-receipt.json").read_text(encoding="utf-8"))
    forge = json.loads((artifacts / "forge-readback.json").read_text(encoding="utf-8"))
    review = json.loads((artifacts / "review-receipt.json").read_text(encoding="utf-8"))
    attestation = json.loads((artifacts / "runtime-attestation.json").read_text(encoding="utf-8"))

    reviewed_head = manifest["review"]["head"]
    assert manifest["source"] == {
        "repository": "https://github.com/topij/agentic-dev-kit",
        "revision": "bdfd6ee702a630f0575f0c186f51b3bbbcd1810a",
    }
    assert manifest["review"] == {
        "head": "5c4006d18e65e0443dc7b22f48c099ad07ce1da9",
        "observer": "github-pr-readback-and-pr-watch-receipt",
        "repository": "https://github.com/topij/adk-codex-writing-evidence-20260830",
    }
    assert manifest["redaction"] == {
        "excluded": [
            "authentication-material",
            "credentials",
            "tokens",
            "unrelated-user-data",
            "unrelated-workspace-data",
        ],
        "reviewed": True,
        "reviewer": "codex-cockpit-gpt-5-6-sol-max",
    }
    assert manifest["runtime"] == {
        "applied_compute": None,
        "client_version": "codex-cli 0.149.1",
        "name": "codex",
        "session_persistence": "persistent",
    }
    assert promotion["runtime"] == manifest["runtime"]
    assert manifest["claims"] == CODEX_WRITING_EXPECTED_CLAIMS
    assert {
        artifact["path"]: (
            artifact["kind"],
            artifact["observer"],
            artifact["capture_request"],
        )
        for artifact in manifest["artifacts"]
    } == CODEX_WRITING_EXPECTED_ARTIFACT_BINDINGS
    assert {
        artifact["path"]: artifact["sha256"] for artifact in manifest["artifacts"]
    } == CODEX_WRITING_EXPECTED_ARTIFACT_SHA256
    assert {
        path: _sha(bundle / path)
        for path in CODEX_WRITING_EXPECTED_ARTIFACT_SHA256
    } == CODEX_WRITING_EXPECTED_ARTIFACT_SHA256
    assert {artifact["captured_on"] for artifact in manifest["artifacts"]} == {
        "2026-08-30"
    }
    assert (artifacts / "client-version.txt").read_text(encoding="utf-8") == (
        manifest["runtime"]["client_version"] + "\n"
    )
    assert descriptor == {
        "base": "main",
        "base_oid": "83d3b623305a691dd874df44ca92270daa62ade9",
        "branch": "dev/write",
        "descriptor_id": "ec07f5b3-14fb-4203-8e82-9ef62bfde785",
        "expires_at": "2026-08-29T22:57:27.674451Z",
        "issued_at": "2026-08-29T22:42:27.674451Z",
        "lane_oid": "83d3b623305a691dd874df44ca92270daa62ade9",
        "merge_class": "operator",
        "origin_url": "git@github.com:topij/adk-codex-writing-evidence-20260830.git",
        "repo_root": "/private/tmp/adk-codex-writing-20260830/repo",
        "runtime": "codex",
        "schema_version": 1,
        "scope": "write",
        "state_root": "/private/tmp/adk-codex-writing-20260830/sessions/write/state",
        "worktree": "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
    }
    assert descriptor["scope"] == "write"
    assert descriptor["runtime"] == "codex"
    assert descriptor["merge_class"] == "operator"
    assert descriptor["branch"] == "dev/write"
    assert descriptor["origin_url"] == (
        "git@github.com:topij/adk-codex-writing-evidence-20260830.git"
    )
    assert descriptor["worktree"] == launcher["observed"]["worktree"]
    assert descriptor["state_root"] == launcher["observed"]["state_root"]
    assert descriptor["descriptor_id"] == launcher["descriptor_id"]
    assert launcher["request"]["runtime"] == "codex"
    assert launcher["request"]["configured_command"] == [
        "/opt/homebrew/bin/codex",
        "exec",
    ]
    assert launcher["observed"] == {
        "argv": [
            "/opt/homebrew/bin/codex",
            "exec",
            "--sandbox",
            "workspace-write",
            "--cd",
            "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
            "--output-last-message",
            "/private/tmp/adk-codex-writing-20260830/sessions/write/launch-final-ec07f5b3-14fb-4203-8e82-9ef62bfde785.txt",
            "-",
        ],
        "base": "main",
        "base_oid": "83d3b623305a691dd874df44ca92270daa62ade9",
        "branch": "dev/write",
        "git_top": "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
        "lane_oid": "83d3b623305a691dd874df44ca92270daa62ade9",
        "merge_class": "operator",
        "origin_url": "git@github.com:topij/adk-codex-writing-evidence-20260830.git",
        "repo_root": "/private/tmp/adk-codex-writing-20260830/repo",
        "repository_overrides_present": [],
        "scope": "write",
        "state_root": "/private/tmp/adk-codex-writing-20260830/sessions/write/state",
        "worktree": "/private/tmp/adk-codex-writing-20260830/sessions/write/wt",
    }
    assert launcher["observed"]["argv"][0] == launcher["request"]["configured_command"][0]
    assert launcher["observed"]["origin_url"] == descriptor["origin_url"]
    assert launcher["observed"]["base_oid"] == descriptor["base_oid"]
    assert launcher["status"] == "completed"
    assert launcher["observed"]["branch"] == "dev/write"
    assert launcher["terminal"]["returncode"] == 0
    assert launcher["terminal"]["final_text_sha256"] == _sha(artifacts / "final-message.txt")
    assert forge["repository"]["is_private"] is True
    assert forge["repository"]["visibility"] == "PRIVATE"
    assert forge["repository"]["name"] == "topij/adk-codex-writing-evidence-20260830"
    assert forge["repository"]["url"] == (
        "https://github.com/topij/adk-codex-writing-evidence-20260830"
    )
    assert descriptor["origin_url"] == (
        forge["repository"]["url"].replace("https://github.com/", "git@github.com:")
        + ".git"
    )
    assert forge["pull_request"]["state"] == "OPEN"
    assert forge["pull_request"]["is_draft"] is False
    assert forge["pull_request"]["head_oid"] == reviewed_head
    assert forge["pull_request"]["head"] == descriptor["branch"]
    assert forge["pull_request"]["base"] == descriptor["base"]
    assert forge["pull_request"]["number"] == 1
    assert forge["pull_request"]["url"] == (
        "https://github.com/topij/adk-codex-writing-evidence-20260830/pull/1"
    )
    assert forge["pull_request"]["files"] == [
        {
            "additions": 2,
            "change_type": "ADDED",
            "deletions": 0,
            "path": "notes/codex-writing-lane.md",
        }
    ]
    assert review["receipt"]["head"] == reviewed_head
    assert review["poll"]["head"] == reviewed_head
    assert review["poll"]["pr"] == forge["pull_request"]["number"]
    assert review["poll"]["url"] == forge["pull_request"]["url"]
    assert review["poll"]["review_evidence"] == {
        "head": reviewed_head,
        "lenses": ["correctness"],
        "route": "receipt",
        "source": "fallback:codex",
        "valid": True,
    }
    final_message = (artifacts / "final-message.txt").read_text(encoding="utf-8")
    assert f"- Branch: `{descriptor['branch']}`" in final_message
    assert f"- Commit: `{reviewed_head}`" in final_message
    assert f"- PR: {forge['pull_request']['url']} — open and ready" in final_message
    assert "- Changed path: `notes/codex-writing-lane.md`" in final_message
    assert attestation == {
        "session_id": CODEX_WRITING_HISTORICAL_COMPUTE["session_id"],
        "turn_context": {
            "cwd": CODEX_WRITING_HISTORICAL_COMPUTE["cwd"],
            "effort": CODEX_WRITING_HISTORICAL_COMPUTE["effort"],
            "model": CODEX_WRITING_HISTORICAL_COMPUTE["model"],
        },
    }
    assert attestation["turn_context"]["cwd"] == descriptor["worktree"]
    filesystem_readback = (artifacts / "filesystem-readback.txt").read_text(encoding="utf-8")
    assert descriptor["worktree"] in filesystem_readback
    assert descriptor["state_root"] in filesystem_readback
    assert "Codex writing lane\ndurable evidence validation" in filesystem_readback
    assert "durable evidence state" in filesystem_readback
    git_readback = (artifacts / "git-readback.txt").read_text(encoding="utf-8")
    assert reviewed_head in git_readback
    assert descriptor["base_oid"] in git_readback
    assert "A  notes/codex-writing-lane.md" in git_readback
    assert "Codex writing lane\ndurable evidence validation" in git_readback
    source_digests = (artifacts / "source-digests.txt").read_text(encoding="utf-8")
    assert source_digests == """source revision: bdfd6ee702a630f0575f0c186f51b3bbbcd1810a
7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6  source/scripts/launch_lane.py
2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba  source/scripts/dev_session.sh
4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6  source/scripts/lib/kitconfig.py
980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555  source/scripts/lib/repo_root.sh
32d9e7b285a54438975c2aa2d9813adc5d017cef077b6df71564b1ae418a6d92  source/config/dev-model.yaml
"""
    retained_source_digests = {
        path: digest
        for digest, path in (
            line.split("  ", 1) for line in source_digests.splitlines()[1:]
        )
    }
    assert set(retained_source_digests) == {
        f"source/{path}" for path in CODEX_WRITING_SOURCE_PATHS
    }
    for path, digest in retained_source_digests.items():
        assert _sha(artifacts / path) == digest
    execution_source_digests = (artifacts / "execution-source-digests.txt").read_text(
        encoding="utf-8"
    )
    assert execution_source_digests == """source revision: bdfd6ee702a630f0575f0c186f51b3bbbcd1810a
fixture base revision: 83d3b623305a691dd874df44ca92270daa62ade9
captured on: 2026-08-30
d4cb774d636655c2c572aed4341c773ae057d09f444494f4b54a56a513035393  fixture/config/dev-model.yaml  git-blob:e6829036c661e3535dcf24a574575cb866896258
2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba  source/scripts/dev_session.sh  git-blob:011a6a1102705f2c9255a086d9b78a8def341964
7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6  source/scripts/launch_lane.py  git-blob:43f71791b519ac3d479f74099769f893a50fb585
4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6  source/scripts/lib/kitconfig.py  git-blob:499ddcd2f7be6b3d78ef9dab1a108fb0ffbf5cf1
980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555  source/scripts/lib/repo_root.sh  git-blob:ba0c2e0f2a1b99de58872f4fdd6cc7f2a2279063
"""
    fixture_config = (artifacts / "fixture/config/dev-model.yaml").read_text(
        encoding="utf-8"
    )
    upstream_config = (artifacts / "source/config/dev-model.yaml").read_text(
        encoding="utf-8"
    )
    expected_fixture_config = upstream_config.replace(
        "  codex_approval_policy: read-only\n",
        "  codex_approval_policy: workspace-write\n",
    ).replace(
        "  bots: [coderabbit]\n",
        "  bots: []\n",
    ).replace(
        "  require_ci: true\n",
        "  require_ci: false\n",
    )
    assert fixture_config == expected_fixture_config
