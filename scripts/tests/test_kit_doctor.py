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


@pytest.mark.parametrize("marker_line", [2, 3])
def test_marker_below_line_one_is_in_use_not_an_unrendered_template(tmp_path, marker_line):
    """The doctor reads LINE 1 only, matching init.sh's seed guard. Reverting it
    to a whole-file match left the entire suite green except the manifest-hash
    gate — which is discharged by regenerating the manifest, so it pins nothing
    (panel round 3). A doc that merely quotes the marker is in use; reporting it
    as an unrendered template prescribes a remedy that provably does nothing.

    LINE 2 is parametrized, not just line 3: with the marker only on line 3, a
    doctor reading the first TWO lines passed the whole suite while disagreeing
    with init.sh about a doc whose line 2 quotes the marker — the round-2 defect
    reopened one line lower, invisible to the tests (panel round 4)."""
    root = _fake_repo(tmp_path)
    body = ["# A real plan", "", "still a real plan", ""]
    body[marker_line - 1] = "We mark skeletons with `devkit-template: unrendered`."
    # Positive control: True is also _fake_repo's default state, so a fixture
    # that lost the marker — a typo, or an off-by-one in the index arithmetic
    # above — would pass vacuously and stop killing the mutant this test exists
    # for (panel round 5).
    assert "devkit-template: unrendered" in body[marker_line - 1]
    assert not any("devkit-template" in line for i, line in enumerate(body) if i != marker_line - 1)
    (root / "docs" / "handoff.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    report = kit_doctor.inspect(root, _manifest({}), config)

    assert report.narrative_rendered["docs/handoff.md"] is True


def test_marker_on_a_cr_delimited_first_line_is_still_detected(tmp_path):
    """`head -n 1` ends at LF only, so on a CR-delimited file its "first line" is
    the whole file. Path.read_text() applies universal-newline translation and
    would end the line at the first CR instead — reporting "in use" for a file
    init.sh will seed straight over (panel round 3). Reading bytes keeps the two
    predicates on the same text."""
    root = _fake_repo(tmp_path)
    (root / "docs" / "handoff.md").write_bytes(
        b"# Title\r<!-- devkit-template: unrendered -->\rbody\r"
    )
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    report = kit_doctor.inspect(root, _manifest({}), config)

    assert report.narrative_rendered["docs/handoff.md"] is False


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


@pytest.mark.driftcheck
def test_kit_repo_self_check_is_clean():
    """The kit's own checkout must report zero drift against its own manifest —
    otherwise the manifest is stale and every adopter report is wrong.

    Marked `driftcheck` because this test compares BYTES, not behaviour: any
    edit to a kit-owned file fails it, including a deliberate mutation. Left in
    a mutation run it reports a kill for every mutant while nothing behavioural
    caught anything (#33 — one lens once reported 17/17 killed, and 7 had
    survived when it was excluded; attested by that lens, not measured here). Regenerating the manifest instead makes it
    pass and contributes nothing, which is how a gate that is not coverage came
    to be read as coverage (#112).
    """
    manifest = json.loads((REPO_ROOT / kit_doctor.MANIFEST_NAME).read_text(encoding="utf-8"))
    config = kit_doctor.load_config(REPO_ROOT / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(REPO_ROOT, manifest, config)
    assert report.drifted == [], (
        "kit-owned files differ from kit-manifest.json: "
        + str([f"{f.path}: {f.state}" for f in report.drifted])
        + ". This compares bytes, not behaviour: it fails for ANY edit to a "
        "kit-owned file. If you are MUTATION-TESTING, this failure on its own "
        "is NOT evidence your mutation was caught — re-run with "
        "`-m 'not driftcheck'` (or `make mutation-test`) and check whether a "
        "test asserting behaviour also failed. If you are not mutating, the "
        "manifest is stale: run `kit_doctor.py --generate-manifest` and commit "
        "it with your change."
    )


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


# ------------------------------------------------------------------ issue #59


def test_engine_probe_derivation_applies_its_role_and_prefix_rules():
    """Driven with a SYNTHETIC KIT_OWNED rather than the real one.

    The earlier version of this test re-derived its expectation from the real
    KIT_OWNED with the prefix filter left out — so deleting that filter from the
    implementation left the whole suite green (mutation-confirmed). Restating
    the implementation cannot pin the implementation; feeding it inputs the real
    table does not contain can."""
    synthetic = (
        ("scripts/pr_watch.py", "engine"),
        ("scripts/lib/kitconfig.py", "engine"),
        ("scripts/hooks/pre-push", "hook"),  # not an engine
        ("tools/vendored_engine.py", "engine"),  # engine, but outside the prefix
        ("docs/agentic-dev-kit/workflows/wrap-up.md", "workflow"),
    )
    assert kit_doctor._derive_engine_names(synthetic) == ("pr_watch.py", "lib/kitconfig.py")


def test_engine_probe_names_cover_the_real_kit_owned_engines():
    """The probe must not be a third hand-maintained list of kit files (after
    KIT_OWNED and kit-manifest.json): adding an engine to KIT_OWNED has to
    extend it automatically."""
    engines = [rel for rel, role in kit_doctor.KIT_OWNED if role == "engine"]
    assert engines, "KIT_OWNED lists no engines — the probe would be empty"
    for rel in engines:
        assert rel[len(kit_doctor.KIT_ENGINE_PREFIX) + 1 :] in kit_doctor._ENGINE_NAMES
    assert "kit_doctor.py" in kit_doctor._ENGINE_NAMES
    assert "lib/kitconfig.py" in kit_doctor._ENGINE_NAMES
    # The hook is not an engine and does not live under paths.engines as one.
    assert "hooks/pre-push" not in kit_doctor._ENGINE_NAMES


def test_sized_down_install_of_two_engines_is_not_reported_engineless(tmp_path):
    """Issue #59, reproduced: the exact cs-toolkit Phase 1 shape — only
    kit_doctor.py and lib/kitconfig.py under `paths.engines`. The old probe
    named three other files, so this reported '✗ contains no kit engine' while
    executing from that very directory.

    (The issue's report also showed `2 unchanged` beside that ✗. This fixture
    passes an empty manifest, so those two files land in `unknown-version`
    instead — the contradiction being pinned here is the ✗ itself, not the
    count.)"""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    (root / "scripts" / "devkit" / "check_doc_budget.py").unlink()
    _write(root / "scripts" / "devkit" / "kit_doctor.py", "print('doctor')\n")
    _write(root / "scripts" / "devkit" / "lib" / "kitconfig.py", "print('config')\n")

    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}), config)
    assert report.engines_dir_ok is True
    rendered = kit_doctor.render(report)
    assert "contains no kit engine" not in rendered
    assert "✓ paths.engines: scripts/devkit" in rendered


def test_an_install_of_only_kitconfig_still_counts_as_an_engines_dir(tmp_path):
    """A NESTED engine path (`lib/kitconfig.py`) must probe as well as a
    top-level one: the probe joins the derived relative path onto the configured
    engines dir, so a name containing `/` has to survive that join."""
    root = _fake_repo(tmp_path, engines="tools/devkit")
    (root / "tools" / "devkit" / "check_doc_budget.py").unlink()
    _write(root / "tools" / "devkit" / "lib" / "kitconfig.py", "print('config')\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    assert kit_doctor.inspect(root, _manifest({}), config).engines_dir_ok is True


# ------------------------------------------------------------------ issue #61.1


@pytest.mark.parametrize("written", ['"2"', "'2'", '" 2 "'])
def test_a_quoted_kit_version_reports_instead_of_crashing(tmp_path, written):
    """`kitconfig` coerces unquoted integers only (PyYAML parity), so a quoted
    version stayed a str and `cfg_v < man_v` raised TypeError — a traceback out
    of the read-only diagnostic an adopter reaches for when something looks
    wrong.

    Every case here must be genuinely QUOTED. An earlier bare ` 2 ` was not:
    kitconfig strips whitespace and coerces it to an int before `_as_version`
    ever sees it, so that case passed on the unfixed code too and pinned
    nothing about the bug."""
    root = _fake_repo(tmp_path, version=written)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}, version=2), config)
    assert report.kit_version_config == 2
    assert "✓ config schema: v2" in kit_doctor.render(report)


def test_a_quoted_manifest_version_is_coerced_too(tmp_path):
    """Both sides of the comparison, not just the config side."""
    root = _fake_repo(tmp_path, version="1")
    manifest = _manifest({})
    manifest["kit_version"] = "2"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    assert report.kit_version_manifest == 2
    assert "v1, kit ships v2" in kit_doctor.render(report)


def test_an_unreadable_version_is_distinguished_from_an_unversioned_one(tmp_path):
    """`version: v2` is a typo, not a pre-v2 config. Rendering it as
    'UNVERSIONED — run ./init.sh to migrate' sends the adopter into a migration
    for a one-character fix."""
    root = _fake_repo(tmp_path, version="v2")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({}), config)
    assert report.kit_version_config is None
    assert report.kit_version_config_raw == "v2"
    rendered = kit_doctor.render(report)
    assert "UNREADABLE" in rendered
    assert "UNVERSIONED" not in rendered


def test_an_unreadable_version_does_not_attribute_differs_to_an_older_kit(tmp_path):
    """`differs` must not claim a cause the version cannot establish — the same
    rule the OLDER-version and LOCAL-EDITS branches already follow."""
    root = _fake_repo(tmp_path, version="v2")
    manifest = _manifest({"scripts/check_doc_budget.py": "0" * 64})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    rendered = kit_doctor.render(kit_doctor.inspect(root, manifest, config))
    assert "cannot narrow" in rendered
    assert "OLDER version" not in rendered
    assert "LOCAL EDITS" not in rendered
    assert "that is a kit bug" not in rendered


@pytest.mark.parametrize(
    "manifest_version, shown",
    [
        ("v3", "'v3'"),  # present but unparseable
        (None, "absent"),  # explicit JSON null
        ("__omit__", "absent"),  # key not in the manifest at all
    ],
)
def test_a_manifest_without_a_usable_version_is_not_a_silent_checkmark(
    tmp_path, manifest_version, shown
):
    """A manifest that cannot serve as a comparison point must say so.

    All three spellings leave `kit_version_manifest` at None, and all three used
    to fall through to a bare `✓ config schema: vN` — a checkmark for a
    comparison that was never performed — and then let `differs` assert LOCAL
    EDITS and tell the adopter to report a kit bug, off that same
    non-comparison. The absent case survived mutation before this test existed."""
    root = _fake_repo(tmp_path, version="2")
    manifest = _manifest({"scripts/check_doc_budget.py": "0" * 64})
    if manifest_version == "__omit__":
        del manifest["kit_version"]
    else:
        manifest["kit_version"] = manifest_version

    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    assert report.kit_version_manifest is None
    rendered = kit_doctor.render(report)
    assert f"manifest kit_version is {shown} — cannot tell whether this config is behind" in rendered
    assert "cannot narrow this" in rendered
    assert "LOCAL EDITS" not in rendered
    assert "OLDER version" not in rendered
    assert "that is a kit bug" not in rendered


def test_a_config_side_problem_does_not_swallow_the_manifest_side_one(tmp_path):
    """Both lines, not whichever the `elif` chain reached first — a packaging
    fault in the manifest must still be named when the config is also wrong."""
    root = _fake_repo(tmp_path, version="v2")
    manifest = _manifest({})
    manifest["kit_version"] = "v3"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    rendered = kit_doctor.render(kit_doctor.inspect(root, manifest, config))
    assert "config schema: UNREADABLE" in rendered
    assert "manifest kit_version is 'v3'" in rendered


def test_json_reports_both_raw_versions(tmp_path, capsys):
    """A consumer cannot tell "no version" from "unreadable version" without
    these, which is the whole reason they exist."""
    root = _fake_repo(tmp_path, version="v2")
    manifest_path = tmp_path / "kit-manifest.json"
    manifest_path.write_text(json.dumps(_manifest({})), encoding="utf-8")
    kit_doctor.main(["--json", "--root", str(root), "--manifest", str(manifest_path)])
    payload = json.loads(capsys.readouterr().out)
    assert payload["kit_version_config"] is None
    assert payload["kit_version_config_raw"] == "v2"
    assert payload["kit_version_manifest"] == 2
    assert payload["kit_version_manifest_raw"] == 2


@pytest.mark.parametrize(
    "written, expected",
    [
        ('"1_0"', None),  # bare int() accepts Python underscore separators → 10
        ('"２"', None),  # bare int() accepts Unicode decimal digits → 2
        ('"0x2"', None),
        ("2.0", 2),  # integral float worked before the fix; must keep working
        ("2.5", None),
        # Quoted and unquoted spellings of the same value must agree, because
        # the UNREADABLE message tells adopters they are equivalent.
        ('"-1"', -1),
        ("-1", -1),
        ('"+2"', 2),
        ("+2", 2),
        ('"-"', None),
        ('""', None),
    ],
)
def test_quoted_version_parsing_is_stricter_than_bare_int(tmp_path, written, expected):
    """Scoped to QUOTED values, which is all this guard covers.

    An unquoted `1_0` is resolved to 10 by kitconfig — and by PyYAML, since YAML
    1.1 permits underscore separators — so it never reaches the str branch.
    `test_unquoted_versions_are_left_to_the_yaml_parser` pins that boundary."""
    root = _fake_repo(tmp_path, version=written)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    assert kit_doctor.inspect(root, _manifest({}), config).kit_version_config == expected


def test_unquoted_versions_are_left_to_the_yaml_parser(tmp_path):
    """The boundary of the guard above, stated so it is not mistaken for a hole.

    `version: 1_0` is the int 10 under YAML 1.1 and PyYAML agrees, so kit_doctor
    reports v10 rather than second-guessing a value the parser resolved."""
    root = _fake_repo(tmp_path, version="1_0")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    assert kit_doctor.inspect(root, _manifest({}), config).kit_version_config == 10


def test_an_unreadable_version_fails_rather_than_warning_green(tmp_path, capsys):
    """CI gates on this exit code, so a config the report itself calls
    UNREADABLE must not pass. Exit 2 is the documented "unreadable input"."""
    root = _fake_repo(tmp_path, version="v2")
    manifest_path = tmp_path / "kit-manifest.json"
    manifest_path.write_text(json.dumps(_manifest({})), encoding="utf-8")
    code = kit_doctor.main(["--root", str(root), "--manifest", str(manifest_path)])
    assert "UNREADABLE" in capsys.readouterr().out
    assert code == 2


@pytest.mark.parametrize(
    "kit_block",
    [
        "",  # kit.version absent entirely
        "kit:\n  version:\n",  # present and explicitly null
        "kit:\n  version: ~\n",  # the other YAML spelling of null
    ],
    ids=["absent", "null", "tilde"],
)
def test_generate_manifest_defaults_a_versionless_config_rather_than_erroring(tmp_path, kit_block):
    """No usable version means "take the documented default", for every spelling
    of "no usable version".

    Defaulting BEFORE parsing made these diverge: an absent key silently stamped
    2 while an explicit null hit the refusal and printed "kit.version is None" —
    naming, as the error, the one case that was not an error. The absent case
    alone cannot catch that, which is why all three spellings are here."""
    root = _fake_repo(tmp_path)
    (root / "config" / "dev-model.yaml").write_text(
        kit_block + "paths:\n  handoff: docs/handoff.md\n"
        "  friction_log: docs/friction-log.md\n  engines: scripts\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "kit-manifest.json"
    code = kit_doctor.main(
        ["--generate-manifest", "--root", str(root), "--manifest", str(manifest_path)]
    )
    assert code == 0
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["kit_version"] == 2


def test_a_boolean_version_is_not_read_as_schema_v1():
    """`bool` is an `int` subclass, so `int(True)` is 1 and the
    `isinstance(value, int)` branch would read `version: true` as schema v1.
    The explicit bool rejection ahead of it is what prevents that."""
    assert kit_doctor._as_version(True) is None
    assert kit_doctor._as_version(False) is None
    assert kit_doctor._as_version(None) is None
    assert kit_doctor._as_version("2") == 2
    assert kit_doctor._as_version(2) == 2
    # A quoted float is a string, and strings must be plain decimal digits.
    assert kit_doctor._as_version("2.0") is None
    assert kit_doctor._as_version([2]) is None


def test_generate_manifest_refuses_an_unreadable_version(tmp_path, capsys):
    """Stamping a guessed kit_version would misreport drift for every adopter
    that reads the manifest, so this exits rather than picking a number."""
    root = _fake_repo(tmp_path, version="v2")
    manifest_path = tmp_path / "kit-manifest.json"
    code = kit_doctor.main(
        ["--generate-manifest", "--root", str(root), "--manifest", str(manifest_path)]
    )
    assert code == 2
    assert not manifest_path.exists()
    assert "refusing to stamp" in capsys.readouterr().err


def test_remap_tolerates_a_trailing_slash():
    assert kit_doctor._remap("scripts/pr_watch.py", "scripts/devkit/") == "scripts/devkit/pr_watch.py"
