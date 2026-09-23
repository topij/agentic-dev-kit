"""Artifact target safety: every refusal writes nothing and preserves what exists."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))
from systemize import artifacts, identity  # noqa: E402
from systemize.config import load_settings  # noqa: E402
from systemize.errors import SystemizeError  # noqa: E402
from systemize.fetch import all_targets  # noqa: E402
from test_systemize_support import DATE, HEAD, make_repo  # noqa: E402


@pytest.fixture
def ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = make_repo(tmp_path)
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(sandbox))
    monkeypatch.setenv("DEVKIT_ROOT", str(root))
    settings = load_settings(root)
    targets = all_targets(settings, date=DATE, window_days=7, mode="test")
    return settings, targets, sandbox, root


def _target(targets, label):
    return next(t for t in targets if t.label == label)


def _run_id(settings, head=HEAD):
    return identity.run_identity(forge_repo="o/r", window_days=7, head=head,
                                 fingerprint=settings.fingerprint, mode="test")


def test_state_targets_land_in_the_sandbox_and_nothing_is_created(ctx) -> None:
    settings, targets, sandbox, root = ctx
    cache = _target(targets, "cache")
    assert cache.path == sandbox / "cache" / f"merged-prs_7d_test_{DATE}.json"
    assert _target(targets, "report").path == root / "reports" / f"post-merge-systemize_7d_test_{DATE}.md"
    artifacts.check_targets(settings, targets)
    assert not sandbox.exists()


def test_the_read_cascade_selects_the_newer_copy_in_both_directions(ctx) -> None:
    settings, _, sandbox, root = ctx
    logical = f"state/cache/merged-prs_7d_test_{DATE}.json"
    sandbox_copy = sandbox / "cache" / f"merged-prs_7d_test_{DATE}.json"
    prod_copy = root / "state" / "cache" / f"merged-prs_7d_test_{DATE}.json"
    for path in (sandbox_copy, prod_copy):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    os.utime(prod_copy, (1, 1))
    assert artifacts.state_read_path(settings, logical) == sandbox_copy
    os.utime(prod_copy, (4_000_000_000, 4_000_000_000))
    assert artifacts.state_read_path(settings, logical) == prod_copy


def test_a_symlinked_target_is_refused_not_followed(ctx, tmp_path: Path) -> None:
    settings, targets, sandbox, _ = ctx
    cache = _target(targets, "cache")
    cache.path.parent.mkdir(parents=True)
    inside = sandbox / "elsewhere.json"
    inside.write_text("keep")
    cache.path.symlink_to(inside)
    with pytest.raises(SystemizeError, match="not a regular file"):
        artifacts.check_targets(settings, targets)
    assert inside.read_text() == "keep"


def test_a_parent_symlink_escaping_the_root_is_refused(ctx, tmp_path: Path) -> None:
    settings, targets, sandbox, _ = ctx
    outside = tmp_path / "outside"
    outside.mkdir()
    sandbox.mkdir()
    (sandbox / "cache").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SystemizeError, match="symlink escaping"):
        artifacts.check_targets(settings, targets)
    assert list(outside.iterdir()) == []


def test_a_hardlinked_target_is_refused(ctx, tmp_path: Path) -> None:
    settings, targets, _, _ = ctx
    cache = _target(targets, "cache")
    cache.path.parent.mkdir(parents=True)
    other = tmp_path / "other.json"
    other.write_text("x")
    os.link(other, cache.path)
    with pytest.raises(SystemizeError, match="2 links"):
        artifacts.check_targets(settings, targets)


def test_a_non_regular_target_is_refused(ctx) -> None:
    settings, targets, _, _ = ctx
    cache = _target(targets, "cache")
    cache.path.mkdir(parents=True)
    with pytest.raises(SystemizeError, match="not a regular file"):
        artifacts.check_targets(settings, targets)


def test_colliding_targets_are_refused(ctx) -> None:
    settings, targets, _, _ = ctx
    duplicate = artifacts.Target("digest", _target(targets, "cache").path, _target(targets, "cache").allowed_root)
    with pytest.raises(SystemizeError, match="collide"):
        artifacts.check_targets(settings, [*targets, duplicate])


def test_a_tracked_report_target_is_refused(ctx) -> None:
    settings, targets, _, root = ctx
    report = _target(targets, "report")
    report.path.parent.mkdir(parents=True)
    report.path.write_text("tracked")
    subprocess.run(["git", "-C", str(root), "add", "-f", str(report.path)], check=True)
    with pytest.raises(SystemizeError, match="tracked by Git"):
        artifacts.check_targets(settings, targets)


def test_a_control_input_target_is_refused(ctx) -> None:
    settings, _, _, root = ctx
    control = artifacts.Target("report", root / "AGENTS.md", root)
    with pytest.raises(SystemizeError, match="control input"):
        artifacts.check_targets(settings, [control])


def test_an_alias_of_a_control_input_is_refused(ctx) -> None:
    settings, targets, _, root = ctx
    report = _target(targets, "report")
    report.path.parent.mkdir(parents=True)
    os.link(root / "AGENTS.md", report.path)
    with pytest.raises(SystemizeError):
        artifacts.check_targets(settings, targets)
    assert (root / "AGENTS.md").read_text() == "# rules\n"


def test_a_report_root_escaping_the_repository_is_refused(ctx, tmp_path: Path) -> None:
    settings, targets, _, root = ctx
    outside = tmp_path / "outside-reports"
    outside.mkdir()
    (root / "reports").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SystemizeError, match="outside the repository"):
        artifacts.check_targets(settings, targets)


@pytest.mark.parametrize(
    "content, message",
    [
        (b"not json", "unreadable artifact"),
        (b"[]", "not a JSON object"),
        (b'{"artifact_kind": "post-merge-systemize-digest"}', "foreign artifact kind"),
        (b'{"artifact_kind": "post-merge-systemize-raw", "schema_version": 2}', "schema_version"),
        (b'{"artifact_kind": "post-merge-systemize-raw", "schema_version": 1}', "missing run_identity"),
    ],
)
def test_an_unusable_existing_artifact_is_preserved(ctx, content: bytes, message: str) -> None:
    settings, targets, _, _ = ctx
    cache = _target(targets, "cache")
    cache.path.parent.mkdir(parents=True)
    cache.path.write_bytes(content)
    with pytest.raises(SystemizeError, match=message):
        artifacts.require_replaceable(cache, kind=identity.RAW_KIND, identity=_run_id(settings))
    assert cache.path.read_bytes() == content


def test_only_the_same_run_may_be_replaced(ctx) -> None:
    settings, targets, _, _ = ctx
    cache = _target(targets, "cache")
    old = identity.header(identity.RAW_KIND, _run_id(settings, head="b" * 40))
    artifacts.publish(cache, json.dumps(old).encode())
    with pytest.raises(SystemizeError, match="different run"):
        artifacts.require_replaceable(cache, kind=identity.RAW_KIND, identity=_run_id(settings))
    tampered = {**old, "run_identity_digest": "sha256:" + "0" * 64}
    cache.path.write_text(json.dumps(tampered))
    with pytest.raises(SystemizeError, match="does not match the recorded identity"):
        artifacts.require_replaceable(cache, kind=identity.RAW_KIND, identity=_run_id(settings, head="b" * 40))
    same = identity.header(identity.RAW_KIND, _run_id(settings))
    cache.path.write_text(json.dumps(same))
    artifacts.require_replaceable(cache, kind=identity.RAW_KIND, identity=_run_id(settings))
    artifacts.publish(cache, b"{}")
    assert cache.path.read_bytes() == b"{}"
    assert [p.name for p in cache.path.parent.iterdir()] == [cache.path.name]


def test_a_run_identity_is_the_canonical_digest() -> None:
    run_id = identity.run_identity(forge_repo="o/r", window_days=7, head=HEAD, fingerprint="sha256:x", mode="live")
    canonical = ('{"config_fingerprint":"sha256:x","execution_mode":"live","forge_repo":"o/r",'
                 f'"protected_branch_head":"{HEAD}","schema":"post-merge-systemize-run-v1","window_days":7}}')
    assert identity.identity_digest(run_id) == "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
