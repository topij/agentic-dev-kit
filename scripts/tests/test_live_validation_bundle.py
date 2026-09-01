"""Behavioral and hostile coverage for retained live-validation evidence.

The dangerous false-success is a plausible narrative or digest surviving after the
bytes it names disappeared. These tests therefore drive the public CLI against real
files. Deterministic mutation tests invoke the same CLI entry point in an isolated
subprocess and supply only its explicit snapshot observer or directory-scan factory;
they do not replace Python startup behavior or validate an internal helper in place of
the promotion path.
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


def _git_oid(kind: str, data: bytes) -> str:
    return hashlib.sha1(
        f"{kind} {len(data)}\0".encode() + data,
        usedforsecurity=False,
    ).hexdigest()


TEST_SOURCE_BYTES = b"print('retained source')\n"
TEST_SOURCE_BLOB = _git_oid("blob", TEST_SOURCE_BYTES)
TEST_SCRIPTS_TREE_ENTRIES = [
    {"mode": "100644", "name": "example.py", "oid": TEST_SOURCE_BLOB},
]
TEST_SCRIPTS_TREE_BYTES = (
    b"100644 example.py\0" + bytes.fromhex(TEST_SOURCE_BLOB)
)
TEST_SCRIPTS_TREE = _git_oid("tree", TEST_SCRIPTS_TREE_BYTES)
TEST_ROOT_TREE_ENTRIES = [
    {"mode": "40000", "name": "scripts", "oid": TEST_SCRIPTS_TREE},
]
TEST_ROOT_TREE_BYTES = b"40000 scripts\0" + bytes.fromhex(TEST_SCRIPTS_TREE)
TEST_ROOT_TREE = _git_oid("tree", TEST_ROOT_TREE_BYTES)
TEST_COMMIT_LINES = [
    f"tree {TEST_ROOT_TREE}",
    "author Evidence Fixture <evidence@example.invalid> 0 +0000",
    "committer Evidence Fixture <evidence@example.invalid> 0 +0000",
    "",
    "retained source fixture",
]
TEST_COMMIT_BYTES = ("\n".join(TEST_COMMIT_LINES) + "\n").encode()
SOURCE = _git_oid("commit", TEST_COMMIT_BYTES)
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
    "artifacts/source-proof.json",
    "artifacts/fixture-proof.json",
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
            "artifacts/final-message.txt",
            "artifacts/filesystem-readback.txt",
            "artifacts/git-readback.txt",
            "artifacts/source-digests.txt",
            *CODEX_WRITING_EXECUTION_SOURCE_EVIDENCE,
        ],
        "id": "codex-writing-lane-observed-write-and-state",
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
        "id": "codex-writing-lane-open-nondraft-clean-private-pr",
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
    "artifacts/fixture-proof.json": (
        "source-git-proof",
        "synthetic-git-object-readback",
        "git cat-file commit and tree-object readback for "
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
    "artifacts/source-proof.json": (
        "source-git-proof",
        "git-object-source-readback",
        "git cat-file commit and tree-object readback for "
        "bdfd6ee702a630f0575f0c186f51b3bbbcd1810a",
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
    "artifacts/execution-source-digests.txt": "5d2696ba86165f940cf5ab4e5426bbd7f05ad75e2efe9e92ef432903e7ca78ef",
    "artifacts/filesystem-readback.txt": "ae6b54246ec52ac4dfd8079ea44a19499f5966887f5c0673084cf8e6df38dbf0",
    "artifacts/final-message.txt": "56c7748b3099da9282dde6c13e202b529740274577aa44ba4baaea8440051ca0",
    "artifacts/fixture-proof.json": "a9be47ffe03aa319dc059fd9df1b210ef6d1ae684eeea460c021695d8e45e7ed",
    "artifacts/fixture/config/dev-model.yaml": "d4cb774d636655c2c572aed4341c773ae057d09f444494f4b54a56a513035393",
    "artifacts/forge-readback.json": "d6fb6505b19a522d9cc6718d7c09a4510b3e96bbf0ef554a8fa9f63d5910a6c6",
    "artifacts/git-readback.txt": "7767f7e2a40d17c61ec34ce205943a8414eb07810be28414bd50c35f68b47029",
    "artifacts/launcher-receipt.json": "06be15394a823fedf6abee96cd38746f8a6c1f951abbef7a9b4f8f2b92e839cc",
    "artifacts/review-receipt.json": "e71819c7a767c94adcee86c67f683045d7547af3a7a1f96792c8ae645f8c76b4",
    "artifacts/runtime-attestation.json": "95271b822394dd24e9f5d2fdb2ae3c3b5a380a74f0c49bbefd71d8f59fd2deaa",
    "artifacts/source-digests.txt": "5859493e48386ebb12e382b3b743ee5b00c7c9d6a93c31c8dbed2faae93f7c19",
    "artifacts/source-proof.json": "5c605d93a352f9cf1f2bf6f067d6abcff923cbcaf03101d60fa398f3334abc3c",
    "artifacts/source/config/dev-model.yaml": "32d9e7b285a54438975c2aa2d9813adc5d017cef077b6df71564b1ae418a6d92",
    "artifacts/source/scripts/dev_session.sh": "2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba",
    "artifacts/source/scripts/launch_lane.py": "7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6",
    "artifacts/source/scripts/lib/kitconfig.py": "4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6",
    "artifacts/source/scripts/lib/repo_root.sh": "980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_sha(root: Path) -> str:
    digest = hashlib.sha256(b"live-validation-snapshot-v1\0")
    directories = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_dir()
    }
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    for directory in sorted(directories):
        encoded = directory.encode("utf-8")
        digest.update(b"d")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    for relative, raw in sorted(files.items()):
        encoded = relative.encode("utf-8")
        digest.update(b"f")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


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


def _argv(
    manifest: Path,
    promotion: Path | None = None,
    *,
    expectations: dict[str, object] | None = None,
    expected_claims: list[dict[str, object]] | None = None,
    expected_compute: dict[str, object] | None | object = DEFAULT_EXPECTED_COMPUTE,
) -> list[str]:
    argv = [str(manifest), "--json"]
    if promotion is not None:
        argv.extend(["--promotion", str(promotion)])
        bindings = FIXTURE_EXPECTATIONS if expectations is None else expectations
        for field, value in bindings.items():
            flag = f"--expect-{field.replace('_', '-')}"
            if field == "reviewed_head" and isinstance(value, list):
                for head in value:
                    argv.extend([flag, str(head)])
            else:
                argv.extend([flag, str(value)])
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
    return argv


def _run(
    manifest: Path,
    promotion: Path | None = None,
    *,
    expectations: dict[str, object] | None = None,
    expected_claims: list[dict[str, object]] | None = None,
    expected_compute: dict[str, object] | None | object = DEFAULT_EXPECTED_COMPUTE,
    env: dict[str, str] | None = None,
    timeout: float = 10,
) -> subprocess.CompletedProcess[str]:
    argv = _argv(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
        expected_compute=expected_compute,
    )
    return subprocess.run(
        [sys.executable, str(ENGINE), *argv],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=timeout,
    )


def _run_observed(
    manifest: Path,
    promotion: Path | None,
    observer_source: str,
    *,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    argv = _argv(manifest, promotion)
    runner = f"""\
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("live_validation_verifier", {str(ENGINE)!r})
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
{observer_source}
raise SystemExit(module.main(
    sys.argv[1:],
    snapshot_observer=observer,
    **globals().get("_main_kwargs", {{}}),
))
"""
    return subprocess.run(
        [sys.executable, "-c", runner, *argv],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=10,
    )


BOUNDED_SCANDIR_SOURCE = """\
import os

class _BoundedScandir:
    def __init__(self, context, limit):
        self._context = context
        self._limit = limit
        self._iterator = None
        self._seen = 0

    def __enter__(self):
        self._iterator = iter(self._context.__enter__())
        return self

    def __exit__(self, *args):
        return self._context.__exit__(*args)

    def __iter__(self):
        return self

    def __next__(self):
        if self._seen >= self._limit:
            raise AssertionError("SCANDIR_CONSUMED_PAST_BOUND")
        self._seen += 1
        return next(self._iterator)

_scan_call = 0
_target_call = int(os.environ["LIVE_EVIDENCE_SCANDIR_TARGET_CALL"])
_limit = int(os.environ["LIVE_EVIDENCE_SCANDIR_LIMIT"])

def _scandir_factory(descriptor):
    global _scan_call
    _scan_call += 1
    context = os.scandir(descriptor)
    if _scan_call == _target_call:
        return _BoundedScandir(context, _limit)
    return context

def observer(event, path):
    pass

_main_kwargs = {"scandir_factory": _scandir_factory}
"""


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
    source_bytes: bytes = TEST_SOURCE_BYTES,
) -> list[dict[str, object]]:
    artifacts = manifest.parent / "artifacts"
    source_file = artifacts / "source" / "scripts" / "example.py"
    source_blob = _git_oid("blob", source_bytes)
    scripts_tree_entries = [
        {"mode": "100644", "name": "example.py", "oid": source_blob},
    ]
    scripts_tree_bytes = b"100644 example.py\0" + bytes.fromhex(source_blob)
    scripts_tree = _git_oid("tree", scripts_tree_bytes)
    root_tree_entries = [
        {"mode": "40000", "name": "scripts", "oid": scripts_tree},
    ]
    root_tree_bytes = b"40000 scripts\0" + bytes.fromhex(scripts_tree)
    root_tree = _git_oid("tree", root_tree_bytes)
    commit_lines = [
        f"tree {root_tree}",
        "author Evidence Fixture <evidence@example.invalid> 0 +0000",
        "committer Evidence Fixture <evidence@example.invalid> 0 +0000",
        "",
        "retained source fixture",
    ]
    source_revision = _git_oid(
        "commit", ("\n".join(commit_lines) + "\n").encode()
    )
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    source_proof = artifacts / "source-proof.json"
    _write_json(
        source_proof,
        {
            "schema_version": 1,
            "namespace": "source",
            "revision": source_revision,
            "commit_lines": commit_lines,
            "trees": [
                {"oid": root_tree, "entries": root_tree_entries},
                {"oid": scripts_tree, "entries": scripts_tree_entries},
            ],
        },
    )
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        f"source revision: {source_revision}\n"
        "source proof: artifacts/source-proof.json\n"
        f"{source_digest if ledger_digest is None else ledger_digest}  "
        "source/scripts/example.py  "
        f"git-blob:{source_blob if ledger_git_blob is None else ledger_git_blob}\n",
        encoding="utf-8",
    )
    if include_source_file:
        source_file.parent.mkdir(parents=True)
        source_file.write_bytes(source_bytes)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["source"]["revision"] = source_revision
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
    value["artifacts"].append(
        {
                "capture_request": f"git cat-file commit/tree proof for {source_revision}",
            "captured_on": "2026-08-30",
            "path": "artifacts/source-proof.json",
            "sha256": _sha(source_proof),
            "kind": "source-git-proof",
            "observer": "git-object-source-readback",
        }
    )
    value["claims"][0]["evidence"].append("artifacts/source-digests.txt")
    if include_source_file:
        value["artifacts"].append(
            {
                "capture_request": f"git show {source_revision}:scripts/example.py",
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
            value["claims"][0]["evidence"].append("artifacts/source-proof.json")
    _write_json(manifest, value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = source_revision
    _write_json(promotion, promotion_value)
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
        "snapshot_sha256": _snapshot_sha(manifest.parent),
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


def test_git_bound_python_source_may_carry_a_runtime_token_value(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    source_bytes = b"def _github_token():\n    return None\n\ntoken = _github_token()\n"
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=source_bytes,
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 0, result.stderr


def test_git_bound_python_source_may_read_a_runtime_token_from_the_environment(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'import os\n\ntoken = os.getenv("GITHUB_TOKEN")\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 0, result.stderr


def test_git_bound_python_source_refuses_a_static_credential_assignment(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'token = "hunter2-secret"\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_git_bound_python_source_refuses_a_static_credential_alias(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'LONG_VALUE = "hunter2-secret"\ntoken = LONG_VALUE\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


@pytest.mark.parametrize(
    "source_bytes",
    [
        b"token = 123456\n",
        b"password = 123456.0\n",
        b"secret = 123456j\n",
        b'token = next(value for value in ["hunter2-secret"])\n',
        b"token = helper(123456)\n",
        b'token = f"{123456}"\n',
        b"token = next(value for value in [123456])\n",
        b'authorization = f"Bearer {123456}"\n',
        b'authorization = f"Basic {helper(123456)}"\n',
        b'authorization = f"Bearer {("hunter2-secret")}"\n',
    ],
    ids=[
        "integer",
        "float",
        "complex",
        "string-comprehension",
        "numeric-call",
        "numeric-formatted-value",
        "numeric-comprehension",
        "authorization-numeric-field",
        "authorization-nested-numeric-call",
        "authorization-static-string-field",
    ],
)
def test_git_bound_python_source_refuses_a_newly_traversed_static_credential(
    tmp_path: Path,
    source_bytes: bytes,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=source_bytes,
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_git_bound_python_source_refuses_a_credential_literal_in_an_expression(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'token = "hunter2" + suffix\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_git_bound_python_source_refuses_a_subscripted_credential_literal(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'token = "hunter2-secret"[::-1]\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_git_bound_python_source_refuses_a_credential_literal_in_a_callable(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=b'token = (lambda: "hunter2-secret")()\n',
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


@pytest.mark.parametrize(
    "source_bytes",
    [
        b'import os\n\ntoken = os.getenv("TOKEN", "HUNTERSECRET")\n',
        b'import os\n\ntoken = os.getenv("TOKEN", default="HUNTERSECRET")\n',
    ],
    ids=["positional-default", "keyword-default"],
)
def test_git_bound_python_source_refuses_an_environment_credential_default(
    tmp_path: Path,
    source_bytes: bytes,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=source_bytes,
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


@pytest.mark.parametrize(
    "source_bytes",
    [
        b'def f(token="hunter2-secret"):\n    pass\n',
        b'def f(*, token="hunter2-secret"):\n    pass\n',
        b'f = lambda token="hunter2-secret": None\n',
        b'def f(token=(lambda: "hunter2-secret")()):\n    pass\n',
    ],
    ids=["positional", "keyword-only", "lambda", "callable"],
)
def test_git_bound_python_source_refuses_a_credential_parameter_default(
    tmp_path: Path,
    source_bytes: bytes,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
        source_bytes=source_bytes,
    )
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = json.loads(
        manifest.read_text(encoding="utf-8")
    )["source"]["revision"]

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_a_fixture_proof_must_bind_retained_execution_sources(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    artifacts = manifest.parent / "artifacts"
    fixture_bytes = b"parallel:\n  fixture: true\n"
    fixture_file = artifacts / "fixture/config/dev-model.yaml"
    fixture_file.parent.mkdir(parents=True)
    fixture_file.write_bytes(fixture_bytes)
    fixture_blob = _git_oid("blob", fixture_bytes)
    config_tree_entries = [
        {"mode": "100644", "name": "dev-model.yaml", "oid": fixture_blob},
    ]
    config_tree_bytes = b"100644 dev-model.yaml\0" + bytes.fromhex(fixture_blob)
    config_tree = _git_oid("tree", config_tree_bytes)
    wrong_scripts_tree = "9" * 40
    root_tree_entries = [
        {"mode": "40000", "name": "config", "oid": config_tree},
        {"mode": "40000", "name": "scripts", "oid": wrong_scripts_tree},
    ]
    root_tree_bytes = (
        b"40000 config\0"
        + bytes.fromhex(config_tree)
        + b"40000 scripts\0"
        + bytes.fromhex(wrong_scripts_tree)
    )
    root_tree = _git_oid("tree", root_tree_bytes)
    fixture_commit_lines = [
        f"tree {root_tree}",
        f"parent {SOURCE}",
        "author Evidence Fixture <evidence@example.invalid> 1 +0000",
        "committer Evidence Fixture <evidence@example.invalid> 1 +0000",
        "",
        "changed fixture config",
    ]
    fixture_revision = _git_oid(
        "commit",
        ("\n".join(fixture_commit_lines) + "\n").encode(),
    )
    fixture_proof = artifacts / "fixture-proof.json"
    _write_json(
        fixture_proof,
        {
            "schema_version": 1,
            "namespace": "fixture",
            "revision": fixture_revision,
            "commit_lines": fixture_commit_lines,
            "trees": [
                {"oid": root_tree, "entries": root_tree_entries},
                {"oid": config_tree, "entries": config_tree_entries},
            ],
        },
    )
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(
            "source proof: artifacts/source-proof.json\n",
            "source proof: artifacts/source-proof.json\n"
            f"fixture base revision: {fixture_revision}\n"
            "fixture proof: artifacts/fixture-proof.json\n",
        )
        + f"{hashlib.sha256(fixture_bytes).hexdigest()}  "
        f"fixture/config/dev-model.yaml  git-blob:{fixture_blob}\n",
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in manifest_value["artifacts"]
        if artifact["path"] == "artifacts/source-digests.txt"
    )["sha256"] = _sha(ledger)
    manifest_value["artifacts"].extend(
        [
            {
                "capture_request": f"git cat-file commit/tree proof for {fixture_revision}",
                "captured_on": "2026-08-30",
                "path": "artifacts/fixture-proof.json",
                "sha256": _sha(fixture_proof),
                "kind": "source-git-proof",
                "observer": "git-object-source-readback",
            },
            {
                "capture_request": (
                    f"git show {fixture_revision}:config/dev-model.yaml"
                ),
                "captured_on": "2026-08-30",
                "path": "artifacts/fixture/config/dev-model.yaml",
                "sha256": hashlib.sha256(fixture_bytes).hexdigest(),
                "kind": "source-file",
                "observer": "retained-git-object-bytes",
            },
        ]
    )
    manifest_value["claims"][0]["evidence"].extend(
        [
            "artifacts/fixture-proof.json",
            "artifacts/fixture/config/dev-model.yaml",
        ]
    )
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=manifest_value["claims"],
    )

    assert result.returncode == 2
    assert "omits tree" in result.stderr
    assert "fixture/scripts/example.py" in result.stderr


def test_a_source_ledger_capture_date_must_match_its_artifact_record(
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
            "source proof: artifacts/source-proof.json\n",
            "source proof: artifacts/source-proof.json\ncaptured on: 2026-08-29\n",
        ),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in manifest_value["artifacts"]
        if artifact["path"] == "artifacts/source-digests.txt"
    )["sha256"] = _sha(ledger)
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "capture date differs from its artifact record" in result.stderr


def test_manifest_claim_count_is_bounded_before_claim_validation(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["claims"].extend(
        {
            "id": f"bounded-claim-{index}",
            "evidence": ["artifacts/forge-readback.json"],
            "requires_applied_compute": False,
        }
        for index in range(256)
    )
    manifest_value["claims"][0] = {"password": "hunter2-secret"}
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "claims exceeds the claim-count limit" in result.stderr


def test_a_self_consistently_relabelled_source_revision_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    fabricated_revision = "3" * 40
    ledger = manifest.parent / "artifacts/source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(SOURCE, fabricated_revision),
        encoding="utf-8",
    )
    proof = manifest.parent / "artifacts/source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["revision"] = fabricated_revision
    _write_json(proof, proof_value)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = fabricated_revision
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source-proof.json":
            artifact["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = fabricated_revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = fabricated_revision

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "commit does not match its revision" in result.stderr


@pytest.mark.parametrize("revision", ["not-a-git-object-id", "4" * 64])
def test_only_full_git_sha1_source_revision_ids_can_promote(
    tmp_path: Path,
    revision: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = revision
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = revision

    result = _run(manifest, promotion, expectations=expectations)

    assert result.returncode == 2
    assert "must be a full lowercase Git SHA-1 object id" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("revision", ["not-a-git-object-id", "4" * 64])
def test_only_full_git_sha1_reviewed_heads_validate_structurally(
    tmp_path: Path,
    revision: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion.unlink()
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["review"]["head"] = revision
    _write_json(manifest, manifest_value)

    result = _run(manifest)

    assert result.returncode == 2
    assert "must be a full lowercase Git SHA-1 object id" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_multi_head_promotion_requires_the_complete_independent_head_set(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    second_head = "3" * 40
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["review"].pop("head")
    manifest_value["review"]["heads"] = [REVIEWED, second_head]
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value.pop("reviewed_head")
    promotion_value["reviewed_heads"] = [REVIEWED, second_head]
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["reviewed_head"] = [REVIEWED, second_head]

    result = _run(manifest, promotion, expectations=expectations)
    assert result.returncode == 0, result.stderr

    expectations["reviewed_head"] = [REVIEWED]
    result = _run(manifest, promotion, expectations=expectations)
    assert result.returncode == 2
    assert "reviewed-head shape does not match" in result.stderr

    expectations["reviewed_head"] = [REVIEWED, "4" * 40]
    result = _run(manifest, promotion, expectations=expectations)
    assert result.returncode == 2
    assert "reviewed heads does not match" in result.stderr


def test_a_source_proof_commit_without_a_header_boundary_is_refused_cleanly(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    commit_lines = [
        f"tree {TEST_ROOT_TREE}",
        "author Evidence Fixture <evidence@example.invalid> 0 +0000",
        "committer Evidence Fixture <evidence@example.invalid> 0 +0000",
        "retained source fixture without a header boundary",
    ]
    revision = _git_oid("commit", ("\n".join(commit_lines) + "\n").encode())
    artifacts = manifest.parent / "artifacts"
    proof = artifacts / "source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["revision"] = revision
    proof_value["commit_lines"] = commit_lines
    _write_json(proof, proof_value)
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(SOURCE, revision),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = revision
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source-proof.json":
            artifact["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = revision

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "source Git proof commit has no header boundary" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_source_proof_preserves_a_commit_without_a_trailing_newline(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    revision = _git_oid("commit", "\n".join(TEST_COMMIT_LINES).encode())
    artifacts = manifest.parent / "artifacts"
    proof = artifacts / "source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["revision"] = revision
    proof_value["commit_trailing_newline"] = False
    _write_json(proof, proof_value)
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(SOURCE, revision),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = revision
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source-proof.json":
            artifact["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = revision

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 0, result.stderr


def test_a_source_proof_rejects_a_non_boolean_commit_eof_field(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    revision = _git_oid("commit", "\n".join(TEST_COMMIT_LINES).encode())
    artifacts = manifest.parent / "artifacts"
    proof = artifacts / "source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["revision"] = revision
    proof_value["commit_trailing_newline"] = None
    _write_json(proof, proof_value)
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(SOURCE, revision),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = revision
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source-proof.json":
            artifact["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = revision

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "commit_trailing_newline must be a boolean" in result.stderr


def test_retained_source_bytes_absent_from_the_revision_tree_are_refused(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    artifacts = manifest.parent / "artifacts"
    original = artifacts / "source/scripts/example.py"
    foreign = artifacts / "source/scripts/foreign.py"
    original.rename(foreign)
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(
            "source/scripts/example.py",
            "source/scripts/foreign.py",
        ),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source/scripts/example.py":
            artifact["path"] = "artifacts/source/scripts/foreign.py"
            artifact["capture_request"] = f"git show {SOURCE}:scripts/foreign.py"
    manifest_value["claims"][0]["evidence"] = [
        "artifacts/source/scripts/foreign.py"
        if path == "artifacts/source/scripts/example.py"
        else path
        for path in manifest_value["claims"][0]["evidence"]
    ]
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=manifest_value["claims"],
    )

    assert result.returncode == 2
    assert "does not contain source/scripts/foreign.py" in result.stderr


def test_an_altered_source_tree_object_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    proof = manifest.parent / "artifacts/source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["trees"][0]["entries"].append(
        {"mode": "100644", "name": "unrelated.txt", "oid": "9" * 40}
    )
    _write_json(proof, proof_value)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in manifest_value["artifacts"]
        if artifact["path"] == "artifacts/source-proof.json"
    )["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "tree content does not match its oid" in result.stderr


def test_an_unneeded_source_proof_tree_is_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    proof = manifest.parent / "artifacts/source-proof.json"
    proof_value = json.loads(proof.read_text(encoding="utf-8"))
    proof_value["trees"].append(
        {"oid": _git_oid("tree", b""), "entries": []}
    )
    _write_json(proof, proof_value)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    next(
        artifact
        for artifact in manifest_value["artifacts"]
        if artifact["path"] == "artifacts/source-proof.json"
    )["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "contains unneeded tree objects" in result.stderr


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


def test_fixture_only_bytes_cannot_replace_source_revision_evidence(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    artifacts = manifest.parent / "artifacts"
    source_file = artifacts / "source/scripts/example.py"
    fixture_file = artifacts / "fixture/scripts/example.py"
    fixture_file.parent.mkdir(parents=True)
    source_file.rename(fixture_file)
    source_file.parent.rmdir()
    source_file.parent.parent.rmdir()

    source_proof = artifacts / "source-proof.json"
    fixture_proof = artifacts / "fixture-proof.json"
    proof_value = json.loads(source_proof.read_text(encoding="utf-8"))
    proof_value["namespace"] = "fixture"
    _write_json(fixture_proof, proof_value)
    source_proof.unlink()

    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8")
        .replace(
            "source proof: artifacts/source-proof.json",
            f"fixture base revision: {SOURCE}\nfixture proof: artifacts/fixture-proof.json",
        )
        .replace("source/scripts/example.py", "fixture/scripts/example.py"),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    for artifact in manifest_value["artifacts"]:
        path = artifact["path"]
        if path == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif path == "artifacts/source-proof.json":
            artifact["path"] = "artifacts/fixture-proof.json"
            artifact["sha256"] = _sha(fixture_proof)
        elif path == "artifacts/source/scripts/example.py":
            artifact["path"] = "artifacts/fixture/scripts/example.py"
    manifest_value["claims"][0]["evidence"] = [
        path.replace("artifacts/source-proof.json", "artifacts/fixture-proof.json").replace(
            "artifacts/source/scripts/example.py",
            "artifacts/fixture/scripts/example.py",
        )
        for path in manifest_value["claims"][0]["evidence"]
    ]
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=manifest_value["claims"],
    )

    assert result.returncode == 2
    assert "must retain source-revision bytes" in result.stderr


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


def test_a_valid_source_proof_tree_must_point_to_the_ledger_blob(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    foreign_blob = _git_oid("blob", b"print('foreign source')\n")
    scripts_entries = [
        {"mode": "100644", "name": "example.py", "oid": foreign_blob},
    ]
    scripts_bytes = b"100644 example.py\0" + bytes.fromhex(foreign_blob)
    scripts_tree = _git_oid("tree", scripts_bytes)
    root_entries = [{"mode": "40000", "name": "scripts", "oid": scripts_tree}]
    root_bytes = b"40000 scripts\0" + bytes.fromhex(scripts_tree)
    root_tree = _git_oid("tree", root_bytes)
    commit_lines = [
        f"tree {root_tree}",
        "author Evidence Fixture <evidence@example.invalid> 0 +0000",
        "committer Evidence Fixture <evidence@example.invalid> 0 +0000",
        "",
        "foreign source fixture",
    ]
    revision = _git_oid("commit", ("\n".join(commit_lines) + "\n").encode())
    artifacts = manifest.parent / "artifacts"
    proof = artifacts / "source-proof.json"
    _write_json(
        proof,
        {
            "schema_version": 1,
            "namespace": "source",
            "revision": revision,
            "commit_lines": commit_lines,
            "trees": [
                {"oid": root_tree, "entries": root_entries},
                {"oid": scripts_tree, "entries": scripts_entries},
            ],
        },
    )
    ledger = artifacts / "source-digests.txt"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(SOURCE, revision),
        encoding="utf-8",
    )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_value["source"]["revision"] = revision
    for artifact in manifest_value["artifacts"]:
        if artifact["path"] == "artifacts/source-digests.txt":
            artifact["sha256"] = _sha(ledger)
        elif artifact["path"] == "artifacts/source-proof.json":
            artifact["sha256"] = _sha(proof)
    _write_json(manifest, manifest_value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["source_revision"] = revision
    promotion_value["manifest_sha256"] = _sha(manifest)
    _write_json(promotion, promotion_value)
    expectations = dict(FIXTURE_EXPECTATIONS)
    expectations["source_revision"] = revision

    result = _run(
        manifest,
        promotion,
        expectations=expectations,
        expected_claims=expected_claims,
    )

    assert result.returncode == 2
    assert "source Git proof blob differs" in result.stderr


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
    assert "incomplete source-evidence closure" in result.stderr


def test_a_source_file_claim_must_link_its_ledger_and_proof(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    _add_source_ledger(
        manifest,
        promotion,
        include_source_file=True,
        claim_source_file=True,
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["claims"][0]["evidence"] = [
        path
        for path in value["claims"][0]["evidence"]
        if path
        not in {
            "artifacts/source-digests.txt",
            "artifacts/source-proof.json",
        }
    ]
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=value["claims"],
    )

    assert result.returncode == 2
    assert "incomplete source-evidence closure" in result.stderr


def test_a_bundle_without_a_promotion_receipt_verifies_structurally(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    promotion.unlink()

    result = _run(manifest)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["promotion"] is False


def test_a_non_compute_claim_cannot_promote_an_open_runtime_attestation(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    claim = value["claims"][0]
    claim["id"] = "reviewed-head-with-retained-session-context"
    claim["evidence"] = [
        "artifacts/runtime-attestation.json",
        "artifacts/forge-readback.json",
    ]
    claim["requires_applied_compute"] = False
    value["runtime"]["applied_compute"] = None
    attestation = manifest.parent / "artifacts/runtime-attestation.json"
    _write_json(attestation, {"unimplemented_assertion": "accepted"})
    value["artifacts"][0]["sha256"] = _sha(attestation)
    _write_json(manifest, value)
    promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
    promotion_value["claims"] = [claim["id"]]
    promotion_value["runtime"]["applied_compute"] = None
    _write_json(promotion, promotion_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=[claim],
        expected_compute=None,
    )

    assert result.returncode == 2
    assert "runtime attestation keys differ" in result.stderr


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


@pytest.mark.parametrize("target", ["manifest", "artifact"])
def test_a_file_changed_during_its_descriptor_read_is_refused(
    tmp_path: Path,
    target: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    race_target = (
        manifest
        if target == "manifest"
        else manifest.parent / "artifacts/forge-readback.json"
    )
    result = _run_observed(
        manifest,
        promotion,
        """\
import os

_target = os.environ["LIVE_EVIDENCE_RACE_TARGET"]
_triggered = False

def observer(event, path):
    global _triggered
    if event == "file-read" and os.fspath(path) == _target and not _triggered:
        _triggered = True
        with open(_target, "ab") as stream:
            stream.write(b" ")
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_RACE_TARGET": str(race_target),
        },
    )

    assert result.returncode == 2
    assert "changed while it was being read" in result.stderr
    assert "Traceback" not in result.stderr


def test_an_earlier_artifact_changed_while_a_later_artifact_is_captured_binds_the_snapshot(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifacts = manifest.parent / "artifacts"
    earlier = artifacts / "forge-readback.json"
    later = artifacts / "runtime-attestation.json"
    captured_snapshot = _snapshot_sha(manifest.parent)
    result = _run_observed(
        manifest,
        promotion,
        """\
import os

_earlier = os.environ["LIVE_EVIDENCE_EARLIER"]
_later = os.environ["LIVE_EVIDENCE_LATER"]
_triggered = False

def observer(event, path):
    global _triggered
    if event == "before-file-read" and os.fspath(path) == _later and not _triggered:
        _triggered = True
        with open(_earlier, "ab") as stream:
            stream.write(b" ")
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_EARLIER": str(earlier),
            "LIVE_EVIDENCE_LATER": str(later),
        },
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["snapshot_sha256"] == captured_snapshot
    assert _snapshot_sha(manifest.parent) != captured_snapshot
    recomputed = _run(manifest, promotion)
    assert recomputed.returncode == 2
    assert "artifact digest mismatch" in recomputed.stderr


def test_an_undeclared_artifact_added_during_snapshot_capture_is_refused(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifacts = manifest.parent / "artifacts"
    trigger = artifacts / "runtime-attestation.json"
    added = artifacts / "late-undeclared.txt"
    result = _run_observed(
        manifest,
        promotion,
        """\
import os

_trigger = os.environ["LIVE_EVIDENCE_TRIGGER"]
_added = os.environ["LIVE_EVIDENCE_ADDED"]
_triggered = False

def observer(event, path):
    global _triggered
    if event == "before-file-read" and os.fspath(path) == _trigger and not _triggered:
        _triggered = True
        with open(_added, "w", encoding="utf-8") as stream:
            stream.write("late undeclared bytes\\n")
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_TRIGGER": str(trigger),
            "LIVE_EVIDENCE_ADDED": str(added),
        },
    )

    assert added.is_file()
    assert result.returncode == 2
    assert "artifact directory changed during snapshot capture" in result.stderr
    assert "Traceback" not in result.stderr


def test_an_ancestor_swap_after_its_descriptor_opens_cannot_redirect_the_snapshot(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path / "container")
    ancestor = manifest.parent.parent
    original = tmp_path / "container-original"
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    result = _run_observed(
        manifest,
        promotion,
        """\
import os

_ancestor = os.environ["LIVE_EVIDENCE_ANCESTOR"]
_original = os.environ["LIVE_EVIDENCE_ORIGINAL"]
_hostile = os.environ["LIVE_EVIDENCE_HOSTILE"]
_triggered = False

def observer(event, path):
    global _triggered
    if event == "directory-opened" and os.fspath(path) == _ancestor and not _triggered:
        _triggered = True
        os.rename(_ancestor, _original)
        os.symlink(_hostile, _ancestor)
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_ANCESTOR": str(ancestor),
            "LIVE_EVIDENCE_ORIGINAL": str(original),
            "LIVE_EVIDENCE_HOSTILE": str(hostile),
        },
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["snapshot_sha256"] == _snapshot_sha(original / "evidence")
    assert ancestor.is_symlink()


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


@pytest.mark.parametrize(
    "target",
    [
        "manifest",
        "source",
        "review",
        "runtime",
        "applied-compute",
        "redaction",
        "artifact",
        "claim",
        "promotion",
        "promotion-runtime",
        "attestation",
        "attestation-context",
        "source-proof",
        "source-proof-tree",
        "source-proof-entry",
        "expected-claim",
        "expected-compute",
    ],
)
def test_non_object_closed_schemas_use_the_documented_refusal_exit(
    tmp_path: Path,
    target: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims: list[dict[str, object]] | None = None
    if target == "manifest":
        _write_json(manifest, 1)
    elif target in {
        "source",
        "review",
        "runtime",
        "applied-compute",
        "redaction",
        "artifact",
        "claim",
    }:
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
        if target in {"source", "review", "runtime", "redaction"}:
            manifest_value[target] = 1
        elif target == "applied-compute":
            manifest_value["runtime"]["applied_compute"] = 1
        elif target == "artifact":
            manifest_value["artifacts"][0] = 1
        else:
            manifest_value["claims"][0] = 1
        _write_json(manifest, manifest_value)
        _refresh_promotion_digest(manifest, promotion)
    elif target in {"promotion", "promotion-runtime"}:
        if target == "promotion":
            _write_json(promotion, 1)
        else:
            promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
            promotion_value["runtime"] = 1
            _write_json(promotion, promotion_value)
    elif target in {"attestation", "attestation-context"}:
        artifact = manifest.parent / "artifacts/runtime-attestation.json"
        if target == "attestation":
            _write_json(artifact, 1)
        else:
            artifact_value = json.loads(artifact.read_text(encoding="utf-8"))
            artifact_value["turn_context"] = 1
            _write_json(artifact, artifact_value)
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
        manifest_value["artifacts"][0]["sha256"] = _sha(artifact)
        _write_json(manifest, manifest_value)
        _refresh_promotion_digest(manifest, promotion)
    elif target in {"source-proof", "source-proof-tree", "source-proof-entry"}:
        expected_claims = _add_source_ledger(
            manifest,
            promotion,
            include_source_file=True,
            claim_source_file=True,
        )
        proof = manifest.parent / "artifacts/source-proof.json"
        if target == "source-proof":
            proof_value: object = 1
        else:
            proof_value = json.loads(proof.read_text(encoding="utf-8"))
            if target == "source-proof-tree":
                proof_value["trees"][0] = 1
            else:
                proof_value["trees"][0]["entries"][0] = 1
        _write_json(proof, proof_value)
        manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
        next(
            artifact
            for artifact in manifest_value["artifacts"]
            if artifact["path"] == "artifacts/source-proof.json"
        )["sha256"] = _sha(proof)
        _write_json(manifest, manifest_value)
        _refresh_promotion_digest(manifest, promotion)

    if target == "expected-claim":
        result = _run(manifest, promotion, expected_claims=[1])  # type: ignore[list-item]
    elif target == "expected-compute":
        result = _run(manifest, promotion, expected_compute=1)  # type: ignore[arg-type]
    else:
        result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "must be a JSON object" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unreviewed", "redaction.reviewed must be true"),
        ("missing-exclusion", "must enumerate every forbidden data category"),
        ("duplicate-exclusion", "must enumerate every forbidden data category"),
    ],
)
def test_required_redaction_approval_and_exclusions_are_refused_when_incomplete(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    if mutation == "unreviewed":
        manifest_value["redaction"]["reviewed"] = False
    elif mutation == "missing-exclusion":
        manifest_value["redaction"]["excluded"].pop()
    else:
        manifest_value["redaction"]["excluded"].append(
            manifest_value["redaction"]["excluded"][0]
        )
    _write_json(manifest, manifest_value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert message in result.stderr


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
        ("observer", "", "observer must be a non-empty string"),
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


def test_an_ordinary_artifact_observer_is_required(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["observer"] = ""
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "observer must be a non-empty string" in result.stderr


def test_unknown_manifest_fields_are_refused(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["unreviewed_extension"] = "plausible"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "bundle manifest keys differ" in result.stderr


@pytest.mark.parametrize(
    "target",
    [
        "source",
        "review",
        "runtime",
        "applied-compute",
        "redaction",
        "artifact",
        "claim",
        "promotion",
        "promotion-runtime",
        "expected-claim",
        "expected-applied-compute",
        "attestation",
        "attestation-context",
        "proof",
        "tree",
        "tree-entry",
    ],
)
def test_unknown_nested_fields_are_refused(tmp_path: Path, target: str) -> None:
    manifest, promotion = _fixture(tmp_path)
    expected_claims = None
    expected_compute: dict[str, object] | None | object = DEFAULT_EXPECTED_COMPUTE
    if target in {"proof", "tree", "tree-entry"}:
        expected_claims = _add_source_ledger(
            manifest,
            promotion,
            include_source_file=True,
            claim_source_file=True,
        )
    manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
    if target == "source":
        manifest_value["source"]["unreviewed_extension"] = "plausible"
    elif target == "review":
        manifest_value["review"]["unreviewed_extension"] = "plausible"
    elif target == "runtime":
        manifest_value["runtime"]["unreviewed_extension"] = "plausible"
    elif target == "applied-compute":
        manifest_value["runtime"]["applied_compute"]["unreviewed_extension"] = "plausible"
    elif target == "redaction":
        manifest_value["redaction"]["unreviewed_extension"] = "plausible"
    elif target == "artifact":
        manifest_value["artifacts"][1]["unreviewed_extension"] = "plausible"
    elif target == "claim":
        manifest_value["claims"][0]["unreviewed_extension"] = "plausible"
    elif target == "promotion":
        promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
        promotion_value["unreviewed_extension"] = "plausible"
        _write_json(promotion, promotion_value)
    elif target == "promotion-runtime":
        promotion_value = json.loads(promotion.read_text(encoding="utf-8"))
        promotion_value["runtime"]["unreviewed_extension"] = "plausible"
        _write_json(promotion, promotion_value)
    elif target == "expected-claim":
        expected_claims = json.loads(json.dumps(FIXTURE_EXPECTED_CLAIMS))
        expected_claims[0]["unreviewed_extension"] = "plausible"
    elif target == "expected-applied-compute":
        expected_compute = dict(FIXTURE_EXPECTED_COMPUTE)
        expected_compute["unreviewed_extension"] = "plausible"
    elif target == "attestation":
        attestation = manifest.parent / "artifacts/runtime-attestation.json"
        artifact_value = json.loads(attestation.read_text(encoding="utf-8"))
        artifact_value["unreviewed_extension"] = "plausible"
        _write_json(attestation, artifact_value)
        manifest_value["artifacts"][0]["sha256"] = _sha(attestation)
    elif target == "attestation-context":
        attestation = manifest.parent / "artifacts/runtime-attestation.json"
        artifact_value = json.loads(attestation.read_text(encoding="utf-8"))
        artifact_value["turn_context"]["unreviewed_extension"] = "plausible"
        _write_json(attestation, artifact_value)
        manifest_value["artifacts"][0]["sha256"] = _sha(attestation)
    else:
        proof = manifest.parent / "artifacts/source-proof.json"
        proof_value = json.loads(proof.read_text(encoding="utf-8"))
        if target == "proof":
            proof_value["unreviewed_extension"] = "plausible"
        elif target == "tree":
            proof_value["trees"][0]["unreviewed_extension"] = "plausible"
        else:
            proof_value["trees"][0]["entries"][0]["unreviewed_extension"] = "plausible"
        _write_json(proof, proof_value)
        next(
            artifact
            for artifact in manifest_value["artifacts"]
            if artifact["path"] == "artifacts/source-proof.json"
        )["sha256"] = _sha(proof)
    if target not in {"promotion", "promotion-runtime"}:
        _write_json(manifest, manifest_value)
        _refresh_promotion_digest(manifest, promotion)

    result = _run(
        manifest,
        promotion,
        expected_claims=expected_claims,
        expected_compute=expected_compute,
    )

    assert result.returncode == 2
    assert "keys differ" in result.stderr


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


@pytest.mark.parametrize(
    "control",
    ["\u0085", "\u034f", "\u200b", "\u202e", "\ufe0f"],
    ids=[
        "nel",
        "combining-grapheme-joiner",
        "zero-width-space",
        "right-to-left-override",
        "variation-selector",
    ],
)
def test_unicode_controls_cannot_split_a_credential_marker(
    tmp_path: Path,
    control: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts/forge-readback.json"
    _write_json(artifact, {"note": f"api{control}_key=abcdefghijklmnop"})
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


def test_an_escaped_unicode_surrogate_is_refused_without_a_traceback(
    tmp_path: Path,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifact = manifest.parent / "artifacts/forge-readback.json"
    _write_json(artifact, {"note": "invalid-\ud800-scalar"})
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["sha256"] = _sha(artifact)
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)

    result = _run(manifest, promotion)

    assert result.returncode == 2
    assert "invalid Unicode surrogate" in result.stderr
    assert "Traceback" not in result.stderr


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
        "to\u200bken",
        "\uff50\uff41\uff53\uff53\uff57\uff4f\uff52\uff44",
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


@pytest.mark.parametrize(
    "credential_text",
    [
        "api key: hunter2-secret\n",
        "OPENAI_API_KEY=placeholder-credential-material\n",
        '"api_key": "hunter2-secret"\n',
        "'api_key': 'hunter2-secret'\n",
        '"password": |\n  hunter2-secret\n',
    ],
)
def test_non_json_credential_assignment_variants_are_refused(
    tmp_path: Path,
    credential_text: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    old_artifact = manifest.parent / "artifacts" / "forge-readback.json"
    artifact = manifest.parent / "artifacts" / "forge-readback.yaml"
    old_artifact.rename(artifact)
    artifact.write_text(credential_text, encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"][1]["path"] = "artifacts/forge-readback.yaml"
    value["artifacts"][1]["sha256"] = _sha(artifact)
    value["claims"][0]["evidence"][1] = "artifacts/forge-readback.yaml"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    expected_claims = json.loads(json.dumps(FIXTURE_EXPECTED_CLAIMS))
    expected_claims[0]["evidence"][1] = "artifacts/forge-readback.yaml"

    result = _run(manifest, promotion, expected_claims=expected_claims)

    assert result.returncode == 2
    assert "credential-like content" in result.stderr


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
        'password: !!str "hunter2-secret"',
        "password: !<tag:yaml.org,2002:str> hunter2-secret",
        'password=$"hunter2"',
        "password=$'hunter2'",
        'password="hunter' + "\\\n" + '2"',
        "client_secret: supersecretvalue",
        "api-key: hunter2-secret",
        "auth_token=supersecretvalue",
        "password: |\n  supersecretvalue",
        "password: |\n\n  supersecretvalue",
        "password: !!str |\n  supersecretvalue",
        "xoxb-" + "123456789012-123456789012-abcdefghijklmnopqrstuvwx",
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "AWS-SECRET-ACCESS-KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
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
    assert "live-validation evidence refused" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="raw POSIX argv bytes are required")
@pytest.mark.parametrize(
    "raw_option",
    ["--expect-claim", "--expect-applied-compute"],
)
def test_invalid_utf8_json_expectation_uses_the_documented_refusal_exit(
    tmp_path: Path,
    raw_option: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    argv = [
        os.fsencode(sys.executable),
        os.fsencode(ENGINE),
        os.fsencode(manifest),
        b"--promotion",
        os.fsencode(promotion),
    ]
    for field, value in FIXTURE_EXPECTATIONS.items():
        argv.extend(
            [
                os.fsencode("--expect-" + field.replace("_", "-")),
                os.fsencode(value),
            ]
        )
    if raw_option == "--expect-applied-compute":
        for claim in FIXTURE_EXPECTED_CLAIMS:
            argv.extend(
                [
                    b"--expect-claim",
                    json.dumps(claim, separators=(",", ":")).encode(),
                ]
            )
    argv.extend([os.fsencode(raw_option), b"\xff"])

    result = subprocess.run(argv, capture_output=True, check=False)

    assert result.returncode == 2
    assert b"must not contain Unicode surrogates" in result.stderr
    assert b"Traceback" not in result.stderr


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
    ("field", "replacement", "message"),
    [
        ("kind", "forge-readback", "must have kind runtime-attestation"),
        ("observer", "generic-runtime-readback", "must be runtime-session-context"),
    ],
)
def test_applied_compute_attestation_metadata_is_required(
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


@pytest.mark.parametrize(
    "control",
    ["\u0085", "\u202e", "\u200b"],
    ids=["nel", "right-to-left-override", "zero-width-space"],
)
def test_control_characters_in_identity_fields_are_refused(
    tmp_path: Path,
    control: str,
) -> None:
    manifest, promotion = _fixture(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    controlled_repository = f"https://github.com/example/source{control}suffix"
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
    assert "bundle root path must contain only retained directories" in result.stderr
    assert "symlink" in result.stderr


def test_a_bundle_path_cannot_traverse_an_ancestor_symlink(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "source")
    manifest.unlink()
    os.mkfifo(manifest)
    alias = tmp_path / "alias"
    alias.symlink_to(manifest.parent.parent, target_is_directory=True)

    result = _run(alias / "evidence" / "bundle.json", alias / "evidence" / "promotion.json")

    assert result.returncode == 2
    assert "bundle root path must contain only retained directories" in result.stderr


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
    assert "artifact tree contains a symlink" in result.stderr


def test_a_promotion_path_cannot_traverse_an_ancestor_symlink(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path / "source")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "promotion.json").write_bytes(promotion.read_bytes())
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)

    result = _run(manifest, alias / "promotion.json")

    assert result.returncode == 2
    assert "must be the bundle's own promotion.json" in result.stderr


def test_a_symlink_loop_uses_the_documented_refusal_exit(tmp_path: Path) -> None:
    loop = tmp_path / "loop"
    loop.symlink_to("loop", target_is_directory=True)

    result = _run(loop / "bundle.json", loop / "promotion.json")

    assert result.returncode == 2
    assert "bundle root path must contain only retained directories" in result.stderr
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
    assert "artifact artifacts/forge-readback.json exceeds its byte limit" in result.stderr
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


def test_bundle_only_artifact_bytes_are_bounded_before_artifact_io(
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
    artifact_io_marker = tmp_path / "artifact-io-observed"

    result = _run_observed(
        manifest,
        None,
        """\
import os
from pathlib import Path

_marker = os.environ["LIVE_EVIDENCE_ARTIFACT_IO_MARKER"]

def observer(event, path):
    if event == "before-file-read" and "artifacts" in Path(path).parts:
        with open(_marker, "w", encoding="utf-8") as stream:
            stream.write(os.fspath(path))
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_ARTIFACT_IO_MARKER": str(artifact_io_marker),
        },
    )

    assert result.returncode == 2
    assert "bundle envelope exceeds the bundle byte limit" in result.stderr
    assert not artifact_io_marker.exists()


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
    value["artifacts"][0] = "invalid-before-count-limit"
    _write_json(manifest, value)
    _refresh_promotion_digest(manifest, promotion)
    artifact_io_marker = tmp_path / "artifact-io-observed"

    result = _run_observed(
        manifest,
        promotion,
        """\
import os
from pathlib import Path

_marker = os.environ["LIVE_EVIDENCE_ARTIFACT_IO_MARKER"]

def observer(event, path):
    if event == "before-file-read" and "artifacts" in Path(path).parts:
        with open(_marker, "w", encoding="utf-8") as stream:
            stream.write(os.fspath(path))
""",
        env={
            **os.environ,
            "LIVE_EVIDENCE_ARTIFACT_IO_MARKER": str(artifact_io_marker),
        },
    )

    assert result.returncode == 2
    assert "artifact-count limit" in result.stderr
    assert not artifact_io_marker.exists()


def test_undeclared_artifact_tree_entries_are_bounded(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    artifacts = manifest.parent / "artifacts"
    for index in range(513):
        (artifacts / f"undeclared-{index}.txt").write_text(
            "capture\n",
            encoding="utf-8",
        )

    result = _run_observed(
        manifest,
        promotion,
        BOUNDED_SCANDIR_SOURCE,
        env={
            **os.environ,
            "LIVE_EVIDENCE_SCANDIR_TARGET_CALL": "2",
            "LIVE_EVIDENCE_SCANDIR_LIMIT": "513",
        },
    )

    assert result.returncode == 2
    assert "entry-count limit" in result.stderr
    assert "SCANDIR_CONSUMED_PAST_BOUND" not in result.stderr
    assert "Traceback" not in result.stderr


def test_undeclared_bundle_root_entries_stop_enumeration(tmp_path: Path) -> None:
    manifest, promotion = _fixture(tmp_path)
    for index in range(8):
        (manifest.parent / f"undeclared-{index}.txt").write_text(
            "neighbor\n",
            encoding="utf-8",
        )

    result = _run_observed(
        manifest,
        promotion,
        BOUNDED_SCANDIR_SOURCE,
        env={
            **os.environ,
            "LIVE_EVIDENCE_SCANDIR_TARGET_CALL": "1",
            "LIVE_EVIDENCE_SCANDIR_LIMIT": "4",
        },
    )

    assert result.returncode == 2
    assert "bundle root contains an undeclared entry" in result.stderr
    assert "SCANDIR_CONSUMED_PAST_BOUND" not in result.stderr
    assert "Traceback" not in result.stderr


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
    "saved_plans/codex-parallel-batch-evidence_2026-09-01/bundle.json",
    "saved_plans/codex-parallel-batch-evidence_2026-09-01/promotion.json",
    "scripts/tests/fixtures/codex_parallel_batch_expected.json",
)
def test_the_promoted_codex_parallel_batch_remains_independently_recomputable() -> None:
    root = find_repo_root(ENGINE.parent)
    bundle = root / "saved_plans/codex-parallel-batch-evidence_2026-09-01"
    expected = json.loads(
        (root / "scripts/tests/fixtures/codex_parallel_batch_expected.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    promotion = json.loads((bundle / "promotion.json").read_text(encoding="utf-8"))
    result = _run(
        bundle / "bundle.json",
        bundle / "promotion.json",
        expectations={
            "authority": "docs/agentic-dev-kit/runtime-parity.md",
            "source_repository": expected["source"]["repository"],
            "source_revision": expected["source"]["revision"],
            "review_repository": expected["review"]["repository"],
            "reviewed_head": expected["review"]["heads"],
            "redaction_reviewer": expected["redaction"]["reviewer"],
            "runtime": expected["runtime"]["name"],
            "client_version": expected["runtime"]["client_version"],
            "session_persistence": expected["runtime"]["session_persistence"],
        },
        expected_claims=expected["claims"],
        expected_compute=None,
    )
    assert result.returncode == 0, result.stderr

    assert manifest["claims"] == expected["claims"]
    assert manifest["source"] == expected["source"]
    assert manifest["review"] == expected["review"]
    assert manifest["redaction"] == expected["redaction"]
    assert manifest["runtime"] == expected["runtime"]
    assert {
        artifact["path"]: {
            key: artifact[key]
            for key in ("kind", "observer", "capture_request", "sha256")
        }
        for artifact in manifest["artifacts"]
    } == expected["artifact_bindings"]
    assert {
        path: _sha(bundle / path) for path in expected["artifact_bindings"]
    } == {
        path: binding["sha256"]
        for path, binding in expected["artifact_bindings"].items()
    }

    artifacts = bundle / "artifacts"
    filesystem = json.loads((artifacts / "filesystem-readback.json").read_text())
    forge = json.loads((artifacts / "forge-readback.json").read_text())
    git_readback = json.loads((artifacts / "git-readback.json").read_text())
    reconciliation = json.loads((artifacts / "reconciliation.json").read_text())
    fixture_base = "f13b3e995558ee2f14b656bba2e1a0f74d2254c2"
    lane_heads = {
        "alpha": "59ad80980fb3c9d609c41c6ffc7f7fed0e12db97",
        "beta": "57e4209a79080d7605cd8e42cb53fe8bdc5d3f38",
    }
    reviewed_heads = [lane_heads[lane] for lane in ("alpha", "beta")]
    assert manifest["review"]["heads"] == reviewed_heads
    assert promotion["reviewed_heads"] == reviewed_heads
    assert git_readback["fixture_base"] == fixture_base
    assert git_readback["remote_refs"] == {
        "refs/heads/dev/parallel-alpha": lane_heads["alpha"],
        "refs/heads/dev/parallel-beta": lane_heads["beta"],
        "refs/heads/main": fixture_base,
    }
    scopes = {"alpha": "parallel-alpha", "beta": "parallel-beta"}
    pull_requests = {"alpha": 2, "beta": 1}
    identities: dict[str, tuple[str, str]] = {}
    for lane in ("alpha", "beta"):
        lane_root = artifacts / "lanes" / lane
        descriptor = json.loads((lane_root / "descriptor.json").read_text())
        authority = json.loads((lane_root / "launch-authority.json").read_text())
        attempt = json.loads((lane_root / "launch-attempt.json").read_text())
        launcher = json.loads((lane_root / "launcher-receipt.json").read_text())
        session_metadata = json.loads((lane_root / "session-metadata.json").read_text())
        review = json.loads((lane_root / "review-receipt.json").read_text())
        refusal = json.loads((lane_root / "merge-refusal.json").read_text())
        pr = forge["pull_requests"][lane]
        git_lane = git_readback["lanes"][lane]
        observed = filesystem["lanes"][lane]

        assert descriptor["scope"] == scopes[lane]
        assert descriptor["runtime"] == "codex"
        assert descriptor["merge_class"] == "operator"
        assert descriptor["base_oid"] == descriptor["lane_oid"] == fixture_base
        assert authority == {
            "descriptor_id": descriptor["descriptor_id"],
            "descriptor_sha256": _sha(lane_root / "descriptor.json"),
            "schema_version": 1,
        }
        assert attempt["descriptor_id"] == descriptor["descriptor_id"]
        assert attempt["request"]["descriptor_sha256"] == authority["descriptor_sha256"]
        assert launcher["descriptor_id"] == descriptor["descriptor_id"]
        assert launcher["status"] == "completed"
        assert launcher["terminal"]["returncode"] == 0
        assert launcher["terminal"]["final_text_sha256"] == _sha(
            lane_root / "final-message.txt"
        )
        for key in ("scope", "branch", "base_oid", "lane_oid", "merge_class"):
            assert launcher["observed"][key] == descriptor[key]
        assert launcher["observed"]["worktree"] == descriptor["worktree"]
        assert launcher["observed"]["state_root"] == descriptor["state_root"]
        assert launcher["observed"]["marker_state_root"] == descriptor["state_root"]
        assert session_metadata == {
            "base": "main",
            "branch": descriptor["branch"],
            "merge_class": "operator",
            "scope": scopes[lane],
        }
        note_path = f"notes/parallel-{lane}.md"
        assert git_lane["branch"] == descriptor["branch"]
        assert git_lane["head"] == lane_heads[lane]
        assert git_lane["note_path"] == note_path
        assert git_lane["note_sha256"] == _sha(lane_root / "lane-output.md")
        assert git_lane["commit_lines"][1] == f"parent {fixture_base}"
        assert _git_oid(
            "commit", ("\n".join(git_lane["commit_lines"]) + "\n").encode()
        ) == lane_heads[lane]
        assert observed["descriptor_worktree"] == observed["git_top"] == (
            descriptor["worktree"]
        )
        assert observed["descriptor_state_root"] == observed["marker_state_root"] == (
            descriptor["state_root"]
        )
        assert observed["state_root_exists"] is True
        assert observed["status_short"] == []
        assert observed["head"] == lane_heads[lane]
        identities[lane] = (descriptor["worktree"], descriptor["state_root"])

        assert pr["number"] == pull_requests[lane]
        assert pr["head_oid"] == lane_heads[lane]
        assert pr["state"] == "OPEN"
        assert pr["is_draft"] is False
        assert pr["merge_commit"] is None
        assert review["receipt"] == {
            "head": lane_heads[lane],
            "lenses": ["adversarial", "correctness"],
            "recorded_at": review["receipt"]["recorded_at"],
            "source": "fallback:panel",
        }
        assert review["poll"]["head"] == lane_heads[lane]
        assert review["poll"]["pr"] == pull_requests[lane]
        assert review["poll"]["converged"] is True
        assert review["poll"]["mergeable"] is True
        assert refusal["exit_code"] == 1
        assert refusal["scope"] == scopes[lane]
        assert "autonomous merge refused" in refusal["stderr"]

        for lens in ("adversarial", "correctness"):
            review_root = artifacts / "reviews" / lane
            run_record = json.loads((review_root / f"{lens}-run.json").read_text())
            prompt = (review_root / f"{lens}-prompt.txt").read_text()
            report = (review_root / f"{lens}-report.md").read_text()
            assert run_record["lane"] == scopes[lane]
            assert run_record["lens"] == lens
            assert run_record["head"] == lane_heads[lane]
            assert run_record["exit_code"] == 0
            assert run_record["prompt_sha256"] == _sha(
                review_root / f"{lens}-prompt.txt"
            )
            assert run_record["report_sha256"] == _sha(
                review_root / f"{lens}-report.md"
            )
            assert f"**{lens}** —" in prompt
            assert run_record["codex_argv"][2:4] == ["-C", run_record["worktree"]]
            assert f"{lane}-{lens}-" in Path(run_record["worktree"]).name
            assert f"**Branch:** {descriptor['branch']}" in prompt
            assert f"**PR:** #{pull_requests[lane]}" in prompt
            assert f"**Head sha under review:** `{lane_heads[lane]}`" in prompt
            assert f"**Base:** `{fixture_base}`" in prompt
            assert run_record["worktree"] in prompt
            assert lane_heads[lane] in report
            assert run_record["worktree"] in report

    assert identities["alpha"][0] != identities["beta"][0]
    assert identities["alpha"][1] != identities["beta"][1]
    assert filesystem["cross_lane"] == {
        "state_roots_distinct": True,
        "worktrees_distinct": True,
    }
    assert forge["repository"]["is_private"] is True
    assert forge["repository"]["visibility"] == "PRIVATE"
    assert "record-prose imprecision below HIGH" in (
        forge["pull_requests"]["alpha"]["comments"][0]["body"]
    )
    assert reconciliation["exit_code"] == 4
    assert "parallel-alpha               held" in reconciliation["stdout"]
    assert "parallel-beta                held" in reconciliation["stdout"]
    source_proof = json.loads((artifacts / "source-proof.json").read_text())
    assert source_proof["revision"] == expected["source"]["revision"]
    assert source_proof["commit_trailing_newline"] is False
    execution_source_digests = (
        artifacts / "execution-source-digests.txt"
    ).read_text(encoding="utf-8")
    assert "source/scripts/pr_watch.py" in execution_source_digests
    assert _sha(artifacts / "source/scripts/pr_watch.py") in execution_source_digests


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
            "codex-writing-lane-observed-write-and-state",
            "codex-writing-lane-open-nondraft-clean-private-pr",
            "codex-writing-lane-exact-head-review-receipt",
        ],
        "promotion": True,
        "snapshot_sha256": _snapshot_sha(bundle),
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
    source_proof = json.loads((artifacts / "source-proof.json").read_text(encoding="utf-8"))
    fixture_proof = json.loads((artifacts / "fixture-proof.json").read_text(encoding="utf-8"))

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
    captured_on_by_path = {
        artifact["path"]: artifact["captured_on"] for artifact in manifest["artifacts"]
    }
    assert captured_on_by_path == {
        "artifacts/client-version.txt": "2026-08-29",
        "artifacts/descriptor.json": "2026-08-29",
        "artifacts/filesystem-readback.txt": "2026-08-29",
        "artifacts/final-message.txt": "2026-08-29",
        "artifacts/forge-readback.json": "2026-08-29",
        "artifacts/git-readback.txt": "2026-08-29",
        "artifacts/launcher-receipt.json": "2026-08-29",
        "artifacts/review-receipt.json": "2026-08-29",
        "artifacts/runtime-attestation.json": "2026-08-29",
        "artifacts/source-digests.txt": "2026-08-30",
        "artifacts/source-proof.json": "2026-08-30",
        "artifacts/source/config/dev-model.yaml": "2026-08-30",
        "artifacts/source/scripts/dev_session.sh": "2026-08-30",
        "artifacts/source/scripts/launch_lane.py": "2026-08-30",
        "artifacts/execution-source-digests.txt": "2026-08-30",
        "artifacts/fixture-proof.json": "2026-08-30",
        "artifacts/fixture/config/dev-model.yaml": "2026-08-30",
        "artifacts/source/scripts/lib/kitconfig.py": "2026-08-30",
        "artifacts/source/scripts/lib/repo_root.sh": "2026-08-30",
    }
    assert captured_on_by_path["artifacts/descriptor.json"] == descriptor["issued_at"][:10]
    assert captured_on_by_path["artifacts/launcher-receipt.json"] == (
        launcher["terminal"]["finished_at"][:10]
    )
    assert captured_on_by_path["artifacts/review-receipt.json"] == (
        review["receipt"]["recorded_at"][:10]
    )
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
    assert forge["repository"]["default_branch"] == descriptor["base"]
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
    assert forge["pull_request"]["merge_state"] == "CLEAN"
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
    assert forge["pull_request"]["commits"] == [
        {
            "headline": "feat: add durable Codex writing-lane note",
            "oid": reviewed_head,
        }
    ]
    assert review["receipt"] == {
        "head": reviewed_head,
        "lenses": ["correctness"],
        "recorded_at": "2026-08-29T22:49:11.879292+00:00",
        "source": "fallback:codex",
    }
    assert review["poll"] == {
        "checks": {"all_green": True, "pending": 0, "total": 0},
        "converged": True,
        "head": reviewed_head,
        "is_draft": False,
        "merge_blockers": [],
        "merge_state": "CLEAN",
        "mergeable": True,
        "pr": forge["pull_request"]["number"],
        "review_evidence": {
            "head": reviewed_head,
            "lenses": ["correctness"],
            "route": "receipt",
            "source": "fallback:codex",
            "valid": True,
        },
        "state": "OPEN",
        "url": forge["pull_request"]["url"],
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
source proof: artifacts/source-proof.json
7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6  source/scripts/launch_lane.py  git-blob:43f71791b519ac3d479f74099769f893a50fb585
2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba  source/scripts/dev_session.sh  git-blob:011a6a1102705f2c9255a086d9b78a8def341964
4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6  source/scripts/lib/kitconfig.py  git-blob:499ddcd2f7be6b3d78ef9dab1a108fb0ffbf5cf1
980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555  source/scripts/lib/repo_root.sh  git-blob:ba0c2e0f2a1b99de58872f4fdd6cc7f2a2279063
32d9e7b285a54438975c2aa2d9813adc5d017cef077b6df71564b1ae418a6d92  source/config/dev-model.yaml  git-blob:6c4f4feaa870894537ba6173751a996c9a6716a7
"""
    retained_source_digests = {
        path: digest
        for digest, path, _blob in (
            line.split("  ", 2) for line in source_digests.splitlines()[2:]
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
source proof: artifacts/source-proof.json
fixture base revision: 83d3b623305a691dd874df44ca92270daa62ade9
fixture proof: artifacts/fixture-proof.json
captured on: 2026-08-30
d4cb774d636655c2c572aed4341c773ae057d09f444494f4b54a56a513035393  fixture/config/dev-model.yaml  git-blob:e6829036c661e3535dcf24a574575cb866896258
2ae9af83f182fa726bdc2102d65820242b873aa9d6749f9a450c4b1afd55e4ba  source/scripts/dev_session.sh  git-blob:011a6a1102705f2c9255a086d9b78a8def341964
7787079163e9d678284db5df15311f059a519a61db6301980784864ab02ad9e6  source/scripts/launch_lane.py  git-blob:43f71791b519ac3d479f74099769f893a50fb585
4ab496661883d8f4ad590a6612a48b31f8cbf770283bb09794096149276634e6  source/scripts/lib/kitconfig.py  git-blob:499ddcd2f7be6b3d78ef9dab1a108fb0ffbf5cf1
980cbf5596cea67033a5dd02d53630f2a92c24afd693ba7727d5fc50303ff555  source/scripts/lib/repo_root.sh  git-blob:ba0c2e0f2a1b99de58872f4fdd6cc7f2a2279063
"""
    assert source_proof["revision"] == manifest["source"]["revision"]
    assert fixture_proof["revision"] == descriptor["base_oid"]
    assert fixture_proof["revision"] == launcher["observed"]["base_oid"]
    assert fixture_proof["commit_lines"][1] == (
        f"parent {manifest['source']['revision']}"
    )
    source_root = {
        entry["name"]: (entry["mode"], entry["oid"])
        for entry in source_proof["trees"][0]["entries"]
    }
    fixture_root = {
        entry["name"]: (entry["mode"], entry["oid"])
        for entry in fixture_proof["trees"][0]["entries"]
    }
    assert fixture_root["scripts"] == source_root["scripts"]
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
