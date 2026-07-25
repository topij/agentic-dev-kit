"""Tests for the installation-drift report (scripts/kit_doctor.py).

The behaviors pinned here are the ones that made the surveyed adopters
diagnosable at all:

- `paths.engines` remapping, so a repo that vendored engines under
  `scripts/devkit/` is compared against the right files rather than reported as
  a wholesale `missing`.
- the `engines_dir_ok` probe, which is what catches a configured engines
  directory containing no engine — the silent breakage where every workflow's
  `<engine-dir>/…` reference resolves to nothing.
- `differs` never asserting a *cause*. A hash mismatch cannot tell an older kit
  version from a hand-edit, and claiming "locally modified" sends someone
  hunting for edits they never made.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import kit_doctor  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fake_repo(tmp_path: Path, *, engines: str = "scripts", version: str = "2") -> Path:
    """A minimal adopter tree: a config, and one engine at the configured dir."""
    _write(
        tmp_path / "config" / "dev-model.yaml",
        f"kit:\n  version: {version}\npaths:\n  handoff: docs/handoff.md\n"
        f"  friction_log: docs/friction-log.md\n  engines: {engines}\n",
    )
    _write(tmp_path / engines / "check_doc_budget.py", "print('engine')\n")
    _write(tmp_path / "docs" / "handoff.md", "# real handoff\n")
    _write(tmp_path / "docs" / "friction-log.md", "# real inbox\n")
    return tmp_path


def _manifest(entries: dict[str, str | None], version: int = 2) -> dict:
    return {
        "kit_version": version,
        "files": {p: {"sha256": h, "role": "engine"} for p, h in entries.items()},
    }


def test_remap_follows_configured_engines_dir():
    assert kit_doctor._remap("scripts/pr_watch.py", "scripts") == "scripts/pr_watch.py"
    assert kit_doctor._remap("scripts/pr_watch.py", "scripts/devkit") == "scripts/devkit/pr_watch.py"
    assert (
        kit_doctor._remap("scripts/lib/state_paths/resolver.py", "tools/devkit")
        == "tools/devkit/lib/state_paths/resolver.py"
    )
    # Non-engine paths are untouched by the remap.
    assert (
        kit_doctor._remap("docs/agentic-dev-kit/workflows/parallel.md", "scripts/devkit")
        == "docs/agentic-dev-kit/workflows/parallel.md"
    )


def test_unchanged_file_is_recognized(tmp_path):
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    manifest = _manifest({"scripts/check_doc_budget.py": kit_doctor.sha256_of(target)})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/check_doc_budget.py"] == "unchanged"
    assert report.drifted == []


def test_hash_mismatch_reports_differs_without_claiming_a_cause(tmp_path):
    root = _fake_repo(tmp_path)
    manifest = _manifest({"scripts/check_doc_budget.py": "0" * 64})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    match = next(f for f in report.files if f.path == "scripts/check_doc_budget.py")
    assert match.state == "differs"
    rendered = kit_doctor.render(report)
    # Must not assert a cause it cannot know.
    assert "locally-modified" not in rendered
    assert "LOCAL EDITS" in rendered  # same schema version ⇒ edits are the likelier cause


def test_older_schema_attributes_differences_to_version_not_edits(tmp_path):
    root = _fake_repo(tmp_path, version="1")
    manifest = _manifest({"scripts/check_doc_budget.py": "0" * 64}, version=2)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    rendered = kit_doctor.render(kit_doctor.inspect(root, manifest, config))
    assert "OLDER version" in rendered
    assert "LOCAL EDITS" not in rendered


def test_namespaced_engines_are_found_not_reported_missing(tmp_path):
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    target = root / "scripts" / "devkit" / "check_doc_budget.py"
    manifest = _manifest({"scripts/check_doc_budget.py": kit_doctor.sha256_of(target)})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    match = next(f for f in report.files if f.path.endswith("check_doc_budget.py"))
    assert match.path == "scripts/devkit/check_doc_budget.py"
    assert match.state == "unchanged"
    assert report.engines_dir_ok is True


def test_engines_dir_containing_no_engine_is_flagged(tmp_path):
    """The live breakage: a config whose paths.engines points at a directory with
    no engine in it, so every workflow's <engine-dir>/… reference resolves to
    nothing — silently, because nothing validated the value."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    # Config says scripts/devkit, but move the engine somewhere else entirely.
    (root / "scripts" / "devkit" / "check_doc_budget.py").unlink()
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}), config)
    assert report.engines_dir_ok is False
    assert "contains no kit engine" in kit_doctor.render(report)


def test_unrendered_narrative_doc_is_flagged(tmp_path):
    root = _fake_repo(tmp_path)
    (root / "docs" / "handoff.md").write_text(
        "<!-- devkit-template: unrendered -->\n# x\n", encoding="utf-8"
    )
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}), config)
    assert report.narrative_rendered["docs/handoff.md"] is False
    assert report.narrative_rendered["docs/friction-log.md"] is True


def test_missing_manifest_entry_is_unknown_not_unchanged(tmp_path):
    root = _fake_repo(tmp_path)
    manifest = _manifest({"scripts/check_doc_budget.py": None})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    match = next(f for f in report.files if f.path == "scripts/check_doc_budget.py")
    assert match.state == "unknown-version"
    assert report.drifted  # unknown must not silently pass


def test_unversioned_config_is_called_out(tmp_path):
    root = tmp_path
    _write(
        root / "config" / "dev-model.yaml",
        "paths:\n  handoff: docs/handoff.md\n  friction_log: docs/friction-log.md\n",
    )
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}), config)
    assert report.kit_version_config is None
    assert "UNVERSIONED" in kit_doctor.render(report)


def test_shipped_manifest_covers_every_kit_owned_file():
    """A KIT_OWNED entry with no manifest hash degrades silently to
    `unknown-version` for every adopter, so the manifest must be regenerated
    whenever the list changes."""
    manifest_path = REPO_ROOT / kit_doctor.MANIFEST_NAME
    assert manifest_path.is_file(), "run kit_doctor.py --generate-manifest"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = set(manifest["files"])
    owned = {rel for rel, _ in kit_doctor.KIT_OWNED}
    assert owned == listed, f"manifest out of sync: {owned ^ listed}"
    holes = [p for p, e in manifest["files"].items() if e["sha256"] is None]
    assert not holes, f"manifest has null hashes (files absent at generation): {holes}"


def test_kit_repo_self_check_is_clean():
    """The kit's own checkout must report zero drift against its own manifest —
    otherwise the manifest is stale and every adopter report is wrong."""
    manifest = json.loads((REPO_ROOT / kit_doctor.MANIFEST_NAME).read_text(encoding="utf-8"))
    config = kit_doctor.load_config(REPO_ROOT / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(REPO_ROOT, manifest, config)
    assert report.drifted == [], [f"{f.path}: {f.state}" for f in report.drifted]


@pytest.mark.parametrize("adopter_path", kit_doctor.ADOPTER_OWNED)
def test_adopter_owned_paths_are_never_compared(adopter_path):
    assert adopter_path not in {rel for rel, _ in kit_doctor.KIT_OWNED}


def test_hook_detection_honors_core_hookspath(tmp_path):
    """`.git/hooks` is not the only place git reads hooks from — core.hooksPath
    overrides it (pre-commit and several monorepo layouts set it). Checking only
    `.git/hooks` reports a correctly-installed hook as missing, which is the same
    mistake init.sh made when WRITING the shim: it would tell an adopter to
    re-run an install that had already worked."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "hooks" / "pre-push", "#!/bin/sh\nexit 0\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    # No hook installed anywhere yet.
    assert kit_doctor.inspect(root, _manifest({}), config).hooks_installed is False

    # Installed at a core.hooksPath location, NOT .git/hooks.
    _write(root / ".git" / "config", "[core]\n\thooksPath = .githooks\n")
    _write(root / ".githooks" / "pre-push", "#!/bin/sh\nexit 0\n")
    assert kit_doctor.inspect(root, _manifest({}), config).hooks_installed is True


def test_hook_detection_falls_back_to_git_hooks(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "hooks" / "pre-push", "#!/bin/sh\nexit 0\n")
    _write(root / ".git" / "hooks" / "pre-push", "#!/bin/sh\nexit 0\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    assert kit_doctor.inspect(root, _manifest({}), config).hooks_installed is True


def test_remap_tolerates_a_trailing_slash():
    assert kit_doctor._remap("scripts/pr_watch.py", "scripts/devkit/") == "scripts/devkit/pr_watch.py"
