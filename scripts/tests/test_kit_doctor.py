"""Tests for the installation-drift report (scripts/kit_doctor.py).

The behaviors pinned here are the ones that made the surveyed adopters
diagnosable at all:

- `paths.engines` remapping, so a repo that vendored engines under
  `scripts/devkit/` is compared against the right files rather than reported as
  a wholesale `missing`.
- the `engines_dir_ok` probe, which is what catches a configured engines
  directory containing no engine — the silent breakage where every workflow's
  `<engine-dir>/…` reference resolves to nothing.
- `differs` never asserting a *cause* **without a trusted baseline**. A hash
  mismatch alone cannot tell an older kit version from a hand-edit, and claiming
  "locally modified" sends someone hunting for edits they never made. With a
  baseline recording what this repo actually installed (`--record-install`,
  #51), the cause stops being an inference: the mismatch splits into `stale` /
  `locally-edited` / `stale-and-edited`, each a fact. The no-cause rule still
  governs every report without one, which is every repo adopted before that
  field existed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

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
    assert (
        kit_doctor._remap("scripts/pr_watch.py", "scripts/devkit") == "scripts/devkit/pr_watch.py"
    )
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
    a mutation run it reports a kill for every mutation to a KIT_OWNED file — the
    paths in kit-manifest.json, not the whole repo — while nothing behavioural
    caught anything (#33 — one lens once reported 17/17 killed, and 7 had
    survived when it was excluded; attested by that lens, not measured here).
    Regenerating the manifest instead makes it
    pass and contributes nothing, which is how a gate that is not coverage came
    to be read as coverage (#112).
    """
    manifest = json.loads((REPO_ROOT / kit_doctor.MANIFEST_NAME).read_text(encoding="utf-8"))
    config = kit_doctor.load_config(REPO_ROOT / "config" / "dev-model.yaml", overlay=False)
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
    assert (
        f"manifest kit_version is {shown} — cannot tell whether this config is behind" in rendered
    )
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
    assert (
        kit_doctor._remap("scripts/pr_watch.py", "scripts/devkit/") == "scripts/devkit/pr_watch.py"
    )


# --- the required-by axis (#41) -------------------------------------------
#
# The bug these pin: `missing` filed a hard dependency under "sized-down
# adoption, or incomplete", and /upgrade tells the operator that such a piece
# may be a deliberate omission and to ask before installing it. So the
# documented path invited someone to decline `lib/kitconfig.py`, which every
# Python engine imports.


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        _write(tmp_path / rel, text)
    return tmp_path


@pytest.mark.kit_repo_only("scripts/kit_doctor.py")
def test_dependency_graph_of_the_real_kit_names_kitconfigs_importers():
    """Measured against the kit's own tree, not a fixture.

    What this pins that a fixture cannot: `scripts/hooks/pre-push` is BASH, and
    its kitconfig import lives inside a `python3 - <<'PY'` heredoc, so an
    ast-only scan drops it; and the equality assertion below fails on any NEW
    importer the derivation misses, which is the staleness the whole axis exists
    to prevent.

    **What it does NOT pin, corrected from an earlier version of this docstring
    that claimed otherwise.** The `devmodel_config.py` assertion looks like it
    proves `ast` beats a text scan on a docstring usage example — that module's
    docstring opens with the literal line `from devmodel_config import get,
    load_config, resolve_path`. It does not: that example names the module's own
    file, so `derive_dependencies`'s `candidate != rel` self-loop guard drops it
    whether ast or the regex produced the match. Forcing the regex branch leaves
    this test GREEN. The ast-vs-prose property is real and IS pinned — by
    `test_a_docstring_usage_example_is_not_an_import`, whose fixture names a
    DIFFERENT module and so is not rescued by the self-loop guard. The assertion
    is kept here as a cheap regression check on the graph's shape, not as
    evidence of the mechanism. Found by the correctness lens on PR #225.
    """
    graph = kit_doctor.derive_dependencies(REPO_ROOT)
    importers = set(graph.get("scripts/lib/kitconfig.py", []))
    assert "scripts/hooks/pre-push" in importers, "the bash heredoc import was dropped"
    assert "scripts/pr_watch.py" in importers, "a function-level import was dropped"
    assert "scripts/lib/devmodel_config.py" not in graph, "a docstring example became an edge"
    # Every engine that imports it, by the kit's own grep. Equality, not a
    # subset: a NEW importer that this misses is exactly the staleness the
    # derivation exists to prevent.
    assert importers == {
        "scripts/archive_plan_sessions.py",
        "scripts/check_doc_budget.py",
        "scripts/check_memory_budget.py",
        "scripts/hooks/pr_followup_hook.py",
        "scripts/hooks/pre-push",
        "scripts/kit_doctor.py",
        "scripts/panel_prompt.py",
        "scripts/pr_watch.py",
    }


def test_importing_a_package_by_name_resolves_to_its_init(tmp_path):
    """The `<pkg>/__init__.py` candidate in `_module_targets`. Nothing in the kit
    imports a KIT_OWNED package by bare name today, so deleting that candidate
    left the whole suite green — flagged by the adversarial lens on PR #225 as
    an untested resolution rule, and pinned here rather than left to a future
    engine to discover."""
    root = _tree(
        tmp_path,
        {
            "scripts/engine.py": "import pkg\n",
            "scripts/lib/pkg/__init__.py": "value = 1\n",
        },
    )
    owned = (("scripts/engine.py", "engine"), ("scripts/lib/pkg/__init__.py", "engine"))
    assert kit_doctor.derive_dependencies(root, owned) == {
        "scripts/lib/pkg/__init__.py": ["scripts/engine.py"]
    }


@pytest.mark.kit_repo_only("scripts/kit_doctor.py")
def test_the_shell_source_dependency_is_a_KNOWN_GAP_not_an_oversight():
    """`dev_session.sh` and `reconcile_sessions.sh` both
    `source "$SCRIPT_DIR/lib/repo_root.sh"`, and that edge is deliberately NOT
    in the graph. Asserted so the gap stays stated.

    A scanner for it was built and withdrawn across three review rounds. Both
    directions failed: preventing FALSE edges needs every real heredoc opener
    recognised (`cmd <<A <<B`, `<<123`, `<<'MULTI WORD'` all defeated the last
    version, letting a printed heredoc body become a dependency), and
    preventing MISSED edges needs to know whether a `source` is in command
    position (`echo "run this; source lib/dep.sh"` became a real edge). Both are
    tokenizer problems. A false edge tells an adopter their working install is
    broken, so shipping the Python-only graph with this hole documented beats
    shipping a mechanism that can manufacture one. #228 carries it.

    If a future change adds shell scanning, this test fails — which is correct:
    it must arrive with a real parser and this test rewritten, not as an
    incidental loosening.
    """
    graph = kit_doctor.derive_dependencies(REPO_ROOT)
    assert "scripts/lib/repo_root.sh" not in graph
    # The whole graph, so a false edge from ANY future non-Python source — a
    # heredoc body, a doc code fence — fails here in the kit's own repo, which
    # is where such a file would be authored. This is the guard that replaced
    # the withdrawn scanner, and it costs five lines instead of thirty-five.
    assert set(graph) == {
        "scripts/lib/atomic_write.py",
        "scripts/lib/kitconfig.py",
        "scripts/lib/state_paths/paths.py",
        "scripts/lib/state_paths/repo_root.py",
        "scripts/lib/state_paths/resolver.py",
    }


@pytest.mark.kit_repo_only("scripts/kit_doctor.py")
def test_shipped_manifest_required_by_matches_a_fresh_derivation():
    """A stale `required_by` is a silent downgrade: the file stops being called
    required and the report goes back to inviting an operator to decline it.

    This is the guard the KIT_OWNED comments say does not exist for the
    tracked/untracked pairing (#216) — it is affordable here only because the
    axis is derived rather than hand-written.
    """
    manifest = json.loads((REPO_ROOT / kit_doctor.MANIFEST_NAME).read_text(encoding="utf-8"))
    shipped = {
        rel: entry["required_by"]
        for rel, entry in manifest["files"].items()
        if entry.get("required_by")
    }
    assert shipped == kit_doctor.derive_dependencies(REPO_ROOT), (
        "kit-manifest.json's required_by is stale: run "
        "`uv run scripts/kit_doctor.py --generate-manifest` and commit it."
    )


def test_a_docstring_usage_example_is_not_an_import(tmp_path):
    root = _tree(
        tmp_path,
        {
            "scripts/lib/thing.py": '"""Use it:\n\n    from other import go\n"""\n',
            "scripts/lib/other.py": "def go(): ...\n",
        },
    )
    owned = (("scripts/lib/thing.py", "engine"), ("scripts/lib/other.py", "engine"))
    assert kit_doctor.derive_dependencies(root, owned) == {}


def test_relative_imports_inside_a_package_are_edges(tmp_path):
    root = _tree(
        tmp_path,
        {
            "scripts/lib/pkg/__init__.py": "from .inner import thing\nfrom . import sibling\n",
            "scripts/lib/pkg/inner.py": "thing = 1\n",
            "scripts/lib/pkg/sibling.py": "other = 2\n",
        },
    )
    owned = (
        ("scripts/lib/pkg/__init__.py", "engine"),
        ("scripts/lib/pkg/inner.py", "engine"),
        ("scripts/lib/pkg/sibling.py", "engine"),
    )
    assert kit_doctor.derive_dependencies(root, owned) == {
        "scripts/lib/pkg/inner.py": ["scripts/lib/pkg/__init__.py"],
        "scripts/lib/pkg/sibling.py": ["scripts/lib/pkg/__init__.py"],
    }


def test_doctrine_prose_quoting_an_import_is_not_scanned(tmp_path):
    """Roles other than engine/hook are skipped, and this is why: the fallback
    text scan cannot tell a code fence from code, and kit doctrine quotes engine
    imports when explaining them."""
    root = _tree(
        tmp_path,
        {
            "docs/kit/explainer.md": "The engines do:\n\n```python\nfrom kitconfig import get\n```\n",
            "scripts/lib/kitconfig.py": "def get(): ...\n",
        },
    )
    owned = (("docs/kit/explainer.md", "doctrine"), ("scripts/lib/kitconfig.py", "engine"))
    assert kit_doctor.derive_dependencies(root, owned) == {}


def test_a_missing_library_an_installed_engine_imports_is_broken_not_sized_down(tmp_path):
    root = _fake_repo(tmp_path)  # installs scripts/check_doc_budget.py, no lib/
    manifest = _manifest({"scripts/check_doc_budget.py": None, "scripts/lib/kitconfig.py": None})
    manifest["files"]["scripts/lib/kitconfig.py"]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/lib/kitconfig.py"] == "missing-required"
    assert [f.path for f in report.broken] == ["scripts/lib/kitconfig.py"]
    detail = next(f.detail for f in report.files if f.path == "scripts/lib/kitconfig.py")
    assert detail == "needed by check_doc_budget.py"


def test_a_missing_library_nothing_installed_imports_stays_an_ordinary_omission(tmp_path):
    """The pair, not the file, is what makes a dependency required. A repo that
    installed no engine is a supported sized-down adoption and must not be told
    its absent library breaks it."""
    root = _fake_repo(tmp_path)
    (root / "scripts" / "check_doc_budget.py").unlink()
    manifest = _manifest({"scripts/check_doc_budget.py": None, "scripts/lib/kitconfig.py": None})
    manifest["files"]["scripts/lib/kitconfig.py"]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/lib/kitconfig.py"] == "missing"
    assert report.broken == []


def test_the_dependent_is_looked_up_through_the_engines_remap(tmp_path):
    """`required_by` records kit-layout paths; whether the dependent is INSTALLED
    is a question about the adopter's layout. Without the remap, a repo that
    vendored engines under `scripts/devkit/` looks like it installed nothing and
    a genuinely broken install reports as sized-down."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    manifest = _manifest({"scripts/check_doc_budget.py": None, "scripts/lib/kitconfig.py": None})
    manifest["files"]["scripts/lib/kitconfig.py"]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/devkit/lib/kitconfig.py"] == "missing-required"


def test_a_manifest_without_the_field_degrades_to_the_old_report(tmp_path):
    """An adopter comparing against a kit release older than this field gets the
    previous behaviour, not a crash and not a false all-clear."""
    root = _fake_repo(tmp_path)
    manifest = _manifest({"scripts/check_doc_budget.py": None, "scripts/lib/kitconfig.py": None})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/lib/kitconfig.py"] == "missing"
    assert report.broken == []


def test_a_broken_install_is_not_a_green_exit(tmp_path, capsys):
    """The dependent is given its REAL hash, so it lands `unchanged` and
    `report.drifted` is empty — otherwise the exit code proves nothing.

    The first version of this test used `_manifest`'s default `None` hash. That
    makes the *present* dependent `unknown-version`, which is already counted in
    `drifted`, so `assert code == 1` passed for a reason unrelated to the
    mechanism under test: deleting `report.broken` from the exit expression
    entirely left all 72 tests green. Found by the adversarial lens on PR #225 —
    the doctrine's "named by a test and pinned by nothing" case, in a test
    written to pin exactly that.
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    manifest = _manifest(
        {
            "scripts/check_doc_budget.py": kit_doctor.sha256_of(target),
            "scripts/lib/kitconfig.py": None,
        }
    )
    manifest["files"]["scripts/lib/kitconfig.py"]["required_by"] = ["scripts/check_doc_budget.py"]
    manifest_path = root / "kit-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    # Positive control on the fixture itself: if a future edit reintroduces an
    # unrelated drifted entry, this fails rather than silently restoring the
    # confound the assertion below is meant to be free of.
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    assert report.drifted == [], f"fixture is confounded: {[f.path for f in report.drifted]}"
    assert [f.path for f in report.broken] == ["scripts/lib/kitconfig.py"]

    code = kit_doctor.main(["--root", str(root), "--manifest", str(manifest_path)])
    out = capsys.readouterr().out
    assert code == 1, "a tree whose engines cannot import their own library exited green"
    assert "this install is broken, not sized down" in out
    assert "1 required by an installed engine" in out


def test_a_healthy_report_does_not_grow_the_parenthetical(tmp_path, capsys):
    """The count line's new clause is conditional; a report with no breakage
    must read exactly as it did."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    manifest = _manifest({"scripts/check_doc_budget.py": kit_doctor.sha256_of(target)})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    print(kit_doctor.render(kit_doctor.inspect(root, manifest, config)))
    out = capsys.readouterr().out
    line = next(ln for ln in out.splitlines() if ln.startswith("  files:"))
    # Everything but check_doc_budget.py is absent here, so the count is large —
    # the property under test is that none of it is called REQUIRED, because
    # nothing that imports it is installed either.
    # Derived, not literal: a new KIT_OWNED entry would otherwise fail this test
    # for a reason unrelated to the property under test, which is only that the
    # parenthetical is absent. (CodeRabbit, PR #225.)
    absent = len(kit_doctor.KIT_OWNED) - 1
    assert line == f"  files: 1 unchanged, 0 differ, {absent} missing, 0 unknown"
    assert "required by an installed engine" not in out
    assert "this install is broken" not in out


# --- the install baseline and the three-way drift split (#51) ---------------
#
# `differs` used to guess its cause from `kit.version`, which tracks the CONFIG
# SCHEMA and therefore does not move when kit FILES change. Every doc, engine
# and doctrine fix between schema bumps landed in the "same schema version, so
# these are likely LOCAL EDITS" branch — wrong for the commonest case, and
# worst for a freshly-upgraded adopter, who is the most likely to be one commit
# behind and the least deserving of being sent hunting for edits they never
# made.
#
# The fix is a baseline, not better wording: a second manifest recording what
# this repo actually installed. A file matching it cannot be a local edit
# however far upstream has moved, which turns the guess into arithmetic.
#
# These tests pin the truth table, and — as importantly — the two ways it may
# NOT be applied: without a trustworthy baseline (below), and to a file the
# baseline has no entry for.


def _sha(text: str) -> str:
    """The sha a file with this content would hash to, without writing one."""
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest()


def _baseline(entries: dict[str, str], kit_commit: str | None = None) -> dict:
    """A manifest carrying the `kit_commit` KEY, which is the trust signal."""
    return {
        "kit_version": 2,
        "kit_commit": kit_commit,
        "files": {p: {"sha256": h, "role": "engine"} for p, h in entries.items()},
    }


def _split_case(tmp_path, *, installed: str, ships: str, recorded: str | None):
    """Drive one row of the table: what the file says, what the kit ships, what
    the baseline recorded. Returns `(that file's FileStatus, the whole Report)` —
    the report so a caller can also assert on `baseline_trusted` or the counts."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", installed)
    rel = "scripts/check_doc_budget.py"
    baseline = _baseline({rel: _sha(recorded)}) if recorded is not None else _baseline({})
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({rel: _sha(ships)}), config, baseline)
    return next(f for f in report.files if f.path == rel), report


def test_the_kit_release_manifest_carries_no_commit_and_is_not_a_baseline(tmp_path):
    """`--record-install` is the ONLY writer of `kit_commit`, which is what lets
    its presence mean "a kit recorded an install here".

    The hazard this closes: the `cp -r` quickstart (#18) copies the kit's
    manifest into an adopter verbatim. If the release manifest carried the
    field, that copy would be trusted as a record of an install it knows nothing
    about, and every file installed at an older kit version would read as a
    local edit — #51 reproduced by the fix for #51.

    Also pins byte-determinism, which the CI manifest gate depends on: a HEAD
    sha here would change the file on every commit."""
    root = _fake_repo(tmp_path)
    manifest = kit_doctor.generate_manifest(root, 2)
    assert "kit_commit" not in manifest
    assert not kit_doctor._baseline_trusted(manifest), "a release manifest is not a baseline"
    assert kit_doctor.generate_manifest(root, 2) == manifest


def test_a_copied_release_manifest_does_not_impersonate_a_baseline(tmp_path):
    """The `cp -r` path, end to end: an adopter whose only manifest is the kit's
    own must still get the hedge, not a confident local-edit claim about files
    it merely installed at an older version."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed at an older kit")
    rel = "scripts/check_doc_budget.py"
    released = kit_doctor.generate_manifest(root, 2)
    released["files"][rel] = {"sha256": _sha("what the kit ships now"), "role": "engine"}
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, released, config, released)
    assert not report.baseline_trusted
    assert next(f for f in report.files if f.path == rel).state == "differs"


def test_an_untouched_file_the_kit_moved_past_is_stale_not_edited(tmp_path):
    """The #51 headline, and the case measured live on a real adopter: installed
    unmodified, upstream changed, previously reported as a likely LOCAL EDIT."""
    status, _ = _split_case(tmp_path, installed="v1", ships="v2", recorded="v1")
    assert status.state == "stale"
    assert "installed" in status.detail and "kit ships" in status.detail


def test_a_changed_file_the_kit_left_alone_is_locally_edited(tmp_path):
    """The other direction. Without this the check is not discriminating — a
    split that answered STALE for everything would pass the test above."""
    status, _ = _split_case(tmp_path, installed="mine", ships="v1", recorded="v1")
    assert status.state == "locally-edited"


def test_a_file_changed_on_both_sides_says_so(tmp_path):
    """The only state that can lose work, so it must not collapse into either
    single-sided one."""
    status, _ = _split_case(tmp_path, installed="mine", ships="v2", recorded="v1")
    assert status.state == "stale-and-edited"


def test_a_file_edited_into_agreement_with_the_kit_is_unchanged(tmp_path):
    """Edited, but edited to exactly what the kit ships. `unchanged` is defined
    against the COMPARISON manifest alone because the instruction — do nothing —
    follows from that and not from the baseline, which is merely out of date."""
    status, _ = _split_case(tmp_path, installed="v2", ships="v2", recorded="v1")
    assert status.state == "unchanged"


def test_a_file_absent_from_the_baseline_is_not_judged(tmp_path):
    """Installed after the baseline was recorded. The baseline is trustworthy
    and still has nothing to say about THIS file, so the report must fall back
    to the undifferentiated state rather than reading a missing entry as
    evidence of anything."""
    status, _ = _split_case(tmp_path, installed="mine", ships="v1", recorded=None)
    assert status.state == "differs"
    assert "not in baseline" in status.detail


def test_a_baseline_predating_the_field_is_distrusted(tmp_path):
    """Every adopter installed before this change has a manifest with no
    `kit_commit` key, and — measured on a real one — a baseline nineteen days
    older than the files beside it. Trusting it would re-file every stale file
    as an edit, which is #51 reproduced in a new place. The report degrades to
    the pre-#51 wording instead."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    _write(target, "installed")
    rel = "scripts/check_doc_budget.py"
    old_style = _manifest({rel: _sha("upstream")})  # no kit_commit key
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, old_style, config, old_style)
    assert not report.baseline_trusted
    assert next(f for f in report.files if f.path == rel).state == "differs"


def test_the_trust_signal_is_the_key_not_its_value():
    """An install recorded retroactively knows its hashes but not its origin, so
    `kit_commit: null` is a legitimate recorded baseline. Reading the VALUE as
    the signal would throw that case away."""
    assert kit_doctor._baseline_trusted({"kit_commit": None, "files": {}})
    assert kit_doctor._baseline_trusted({"kit_commit": "a" * 40, "files": {}})
    assert not kit_doctor._baseline_trusted({"files": {}})
    assert not kit_doctor._baseline_trusted(None)


def _states_drift_state_can_return() -> set[str]:
    """Every state `_drift_state` actually produces, derived by driving it over
    the truth table rather than restated as a literal.

    The point is the derivation. A hardcoded list cannot fail when a fourth
    state is added to `_drift_state` and forgotten in `drifted` — which is
    precisely the regression the test below exists to catch, and an earlier
    version of it claimed to catch while pinning nothing (CodeRabbit, PR #278).
    """
    a, b, c = "a" * 64, "b" * 64, "c" * 64
    return {
        kit_doctor._drift_state(actual, expected, recorded)[0]
        # actual != expected always (a matching pair never reaches _drift_state),
        # so this covers: untouched-but-behind, edited-with-kit-still,
        # edited-and-kit-moved, and no-baseline-entry.
        for actual, expected, recorded in ((a, b, a), (a, b, b), (a, b, c), (a, b, None))
    }


def test_no_split_state_can_escape_the_drift_tally():
    """Derived from `_drift_state` itself: whatever causes it can name, `drifted`
    must count. Adding a fifth row to the table without adding its state to
    `drifted` fails here, which the parametrized list below could not do."""
    missing = _states_drift_state_can_return() - {
        f.state
        for f in kit_doctor.Report(
            kit_version_config=2,
            kit_version_manifest=2,
            engines_dir="scripts",
            engines_dir_ok=True,
            hooks_installed=True,
            narrative_rendered={},
            files=[
                kit_doctor.FileStatus(s, "engine", s) for s in _states_drift_state_can_return()
            ],
        ).drifted
    }
    assert not missing, f"states _drift_state can return that `drifted` does not count: {missing}"


@pytest.mark.parametrize("state", ["stale", "locally-edited", "stale-and-edited"])
def test_every_split_state_still_counts_as_drift(state):
    """The split states are refinements of `differs`, not lesser categories.
    Dropping one from `drifted` would remove it from the exit code AND from the
    CI manifest gate — so naming a drift precisely would be what made it stop
    being reported.

    This list is a literal on purpose — it names the three states this PR
    introduced, so a rename shows up as a failure here. The test above is the
    one that catches a NEW state going uncounted; this one does not claim to."""
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        files=[kit_doctor.FileStatus("x", "engine", state)],
    )
    assert [f.state for f in report.drifted] == [state]


def test_the_count_line_totals_every_mismatch_state(tmp_path, capsys):
    """`N differ` must keep meaning "how many kit files are not what the kit
    ships" once the causes are split out, or a fully-split report reads as
    `0 differ` with its files listed underneath.

    **All four mismatch states are present at once, on purpose.** An earlier
    version built ONE file in ONE state and asserted `1 differ` — which cannot
    detect a bug in the summation it is named for: dropping `stale-and-edited`
    from `render`'s total left the whole suite green (panel, correctness lens,
    mutation-confirmed). A total is only pinned by a case where the states it
    sums are distinguishable from each other."""
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    # Four kit-owned engines, one per mismatch state. Real KIT_OWNED paths so
    # the remap and manifest lookup behave as in a live report.
    cases = {
        "scripts/check_doc_budget.py": ("here", _sha("kit"), _sha("here")),  # stale
        "scripts/pr_watch.py": ("here", _sha("kit"), _sha("kit")),  # locally-edited
        "scripts/dev_session.sh": ("here", _sha("kit"), _sha("third")),  # stale-and-edited
        "scripts/panel_prompt.py": ("here", _sha("kit"), None),  # differs (not in baseline)
    }
    for rel, (content, _, _) in cases.items():
        _write(root / rel, content)
    report = kit_doctor.inspect(
        root,
        _manifest({rel: ships for rel, (_, ships, _) in cases.items()}),
        config,
        _baseline({rel: rec for rel, (_, _, rec) in cases.items() if rec is not None}),
    )
    states = {f.path: f.state for f in report.files}
    assert states["scripts/check_doc_budget.py"] == "stale"
    assert states["scripts/pr_watch.py"] == "locally-edited"
    assert states["scripts/dev_session.sh"] == "stale-and-edited"
    assert states["scripts/panel_prompt.py"] == "differs"
    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    # The property: the total equals the number of mismatches, across all four
    # states. Dropping any one from `render`'s sum makes this 3.
    assert next(ln for ln in out.splitlines() if ln.startswith("  files:")).count("4 differ") == 1
    assert len(report.drifted) == 4
    for label in ("STALE", "LOCALLY EDITED", "STALE **and** LOCALLY EDITED"):
        assert label in out


def test_record_install_hashes_the_installed_files_not_the_kit(tmp_path):
    """The distinction the whole fix rests on. Copying the kit's hashes would
    assert "these came from kit HEAD" — false for any install that is merely
    old, and it would re-file every stale file as an edit."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "what is actually here")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    recorded, _ = kit_doctor.record_install_manifest(root, config, 2, None)
    entry = recorded["files"]["scripts/check_doc_budget.py"]
    assert entry["sha256"] == _sha("what is actually here")
    # Only what is installed: absent files get no entry at all, so a later
    # install of one is `differs`/unjudgeable rather than a false edit.
    assert "scripts/pr_watch.py" not in recorded["files"]


def test_record_install_keys_by_kit_layout_under_a_vendored_engines_dir(tmp_path):
    """Both manifests must be keyed identically or `inspect` looks the baseline
    up under a path it was never written under — which would silently make every
    vendored-engine adopter unjudgeable, i.e. exactly the repos this is for."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "check_doc_budget.py", "vendored")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    recorded, _ = kit_doctor.record_install_manifest(root, config, 2, None)
    assert "scripts/check_doc_budget.py" in recorded["files"]
    assert "scripts/devkit/check_doc_budget.py" not in recorded["files"]


def test_record_install_refuses_a_from_kit_that_is_not_a_checkout(tmp_path, capsys):
    """Naming a checkout is asking the provenance question explicitly. Answering
    it with null — the value that means "nobody asked" — would be silent."""
    root = _fake_repo(tmp_path)
    code = kit_doctor.main(
        ["--record-install", "--root", str(root), "--from-kit", str(tmp_path / "not-a-repo")]
    )
    assert code == 2
    assert "cannot resolve HEAD" in capsys.readouterr().err
    assert not (root / "kit-manifest.json").exists()


def test_record_install_without_a_kit_still_splits_drift(tmp_path, capsys):
    """Provenance is optional and the edit axis does not depend on it: the
    hashes were taken from the files. Only "how far behind upstream" needs the
    commit, and that is a separate question."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    assert kit_doctor.main(["--record-install", "--root", str(root)]) == 0
    assert "provenance is unrecorded" in capsys.readouterr().err
    baseline = json.loads((root / "kit-manifest.json").read_text())
    assert baseline["kit_commit"] is None
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root,
        _manifest({"scripts/check_doc_budget.py": _sha("upstream moved")}),
        config,
        baseline,
    )
    assert report.baseline_trusted
    assert [f.state for f in report.drifted] == ["stale"]


def test_an_unreadable_baseline_degrades_instead_of_aborting(tmp_path, capsys):
    """A read-only diagnostic must not withhold the whole report because a
    supplementary file is malformed — but the degrade has to be visible."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    kit_manifest = tmp_path / "kit" / "kit-manifest.json"
    _write(
        kit_manifest,
        json.dumps(_baseline({"scripts/check_doc_budget.py": _sha("upstream")})),
    )
    _write(root / "kit-manifest.json", "{ this is not json")
    code = kit_doctor.main(["--root", str(root), "--manifest", str(kit_manifest)])
    captured = capsys.readouterr()
    assert code == 1, "drift still reported"
    assert "unreadable baseline" in captured.err
    assert "differ" in captured.out


def test_a_retained_adopter_file_is_left_out_of_the_baseline(tmp_path):
    """`/adopt` copies only where the target does not already exist, so a file
    the adopter already had at a kit-owned path is RETAINED, not installed.
    Recording it would make the next upgrade call it `STALE` — "replace them,
    nothing local is lost" — about a file that is entirely theirs, and the
    operator would be instructed to overwrite it (CodeRabbit, PR #278).

    `--from-kit` is the assertion "these came from that kit", so it is checked
    rather than believed."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "the adopter's own file, kept")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    source = {rel: {"sha256": _sha("what the kit actually ships"), "role": "engine"}}
    recorded, unverified = kit_doctor.record_install_manifest(root, config, 2, "a" * 40, source)
    assert rel not in recorded["files"], "a retained file must not be recorded as installed"
    assert unverified == [rel], "and it must be named, not silently dropped"
    # The consequence that matters: it stays unjudgeable rather than STALE.
    report = kit_doctor.inspect(root, _manifest(dict.fromkeys([rel], _sha("kit"))), config, recorded)
    assert next(f for f in report.files if f.path == rel).state == "differs"


def test_a_genuinely_installed_file_is_recorded(tmp_path):
    """The other direction — without it the check above is satisfied by a
    `--from-kit` mode that records nothing at all."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "straight from the kit")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    source = {rel: {"sha256": _sha("straight from the kit"), "role": "engine"}}
    recorded, unverified = kit_doctor.record_install_manifest(root, config, 2, "a" * 40, source)
    assert recorded["files"][rel]["sha256"] == _sha("straight from the kit")
    assert unverified == []


def test_retro_recording_without_a_kit_records_everything(tmp_path):
    """The mode the live acceptance test uses: an existing install, nothing
    matching current HEAD by construction, operator taking the files as found."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed long ago")
    recorded, unverified = kit_doctor.record_install_manifest(
        root, kit_doctor.load_config(root / "config" / "dev-model.yaml"), 2, None
    )
    assert "scripts/check_doc_budget.py" in recorded["files"]
    assert unverified == []


def test_a_sha256_object_format_head_is_accepted(monkeypatch, tmp_path):
    """`git rev-parse HEAD` prints 64 hex in a repo created with
    `--object-format=sha256`. Matching only 40 refused a valid checkout and
    reported it as "not a git checkout" (CodeRabbit, PR #278)."""
    import subprocess as sp

    class Done:
        returncode = 0
        stdout = "b" * 64 + "\n"

    monkeypatch.setattr(kit_doctor.subprocess, "run", lambda *a, **k: Done())
    assert kit_doctor._git_head(tmp_path) == "b" * 64
    _ = sp  # imported to make the monkeypatched target explicit


def test_a_non_string_kit_commit_does_not_abort_the_report(tmp_path, capsys):
    """Trust keys on the KEY's presence, so a hand-edited baseline can carry any
    JSON type. `render` slices this value; a number or list raised TypeError and
    took the whole read-only diagnostic with it, contradicting the
    degrade-don't-abort rule (CodeRabbit, PR #278)."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    rel = "scripts/check_doc_budget.py"
    baseline = _baseline({rel: _sha("installed")})
    baseline["kit_commit"] = 12345  # not a string
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({rel: _sha("kit moved")}), config, baseline)
    assert report.baseline_trusted, "the hashes are still good"
    assert report.baseline_kit_commit is None, "but the value is unusable as provenance"
    print(kit_doctor.render(report))  # must not raise
    assert "STALE" in capsys.readouterr().out


def test_an_unwritable_baseline_path_exits_two_rather_than_tracebacking(tmp_path, capsys):
    """The module's convention for an operator-facing failure (CodeRabbit, PR #278)."""
    root = _fake_repo(tmp_path)
    code = kit_doctor.main(
        ["--record-install", "--root", str(root), "--baseline", str(tmp_path / "nodir" / "m.json")]
    )
    assert code == 2
    assert "cannot write baseline" in capsys.readouterr().err


def test_an_unreadable_source_manifest_refuses_rather_than_recording_everything(tmp_path, capsys):
    """Falling back to the permissive mode here would silently re-open the
    retained-file hole: the check that keeps an adopter's own file out of the
    baseline is exactly the one that needs this manifest."""
    root = _fake_repo(tmp_path)
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / ".git").mkdir()
    _write(kit / "kit-manifest.json", "{ not json")
    monkey = kit_doctor._git_head
    kit_doctor._git_head = lambda p: "c" * 40
    try:
        code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
    finally:
        kit_doctor._git_head = monkey
    assert code == 2
    assert "cannot read" in capsys.readouterr().err
    assert not (root / "kit-manifest.json").exists()


# --- what the fallback review panel found on PR #278 -----------------------


def test_record_install_refuses_to_overwrite_a_release_manifest(tmp_path, capsys):
    """`--record-install --root <the kit's own checkout>` is a natural
    invocation, and it silently destroyed the committed release manifest: every
    `required_by` edge gone (the basis of the `missing-required` axis), plus a
    `kit_commit` key whose ABSENCE from a release manifest is what stops a
    copied one being trusted as a baseline. The mode defeated that invariant
    from the opposite side, printed a success line, and only the suite caught it
    (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    release = kit_doctor.generate_manifest(REPO_ROOT, 2)
    assert any(e.get("required_by") for e in release["files"].values()), "fixture precondition"
    _write(root / "kit-manifest.json", json.dumps(release))
    before = (root / "kit-manifest.json").read_text()
    code = kit_doctor.main(["--record-install", "--root", str(root)])
    assert code == 2
    assert "RELEASE manifest" in capsys.readouterr().err
    assert (root / "kit-manifest.json").read_text() == before, "refused, and wrote nothing"


def test_a_real_baseline_is_still_overwritable(tmp_path):
    """The other direction: re-recording over a previous baseline is the
    supported path and must not be caught by the guard above."""
    root = _fake_repo(tmp_path)
    _write(root / "kit-manifest.json", json.dumps(_baseline({"scripts/pr_watch.py": _sha("x")})))
    assert kit_doctor.main(["--record-install", "--root", str(root)]) == 0
    assert json.loads((root / "kit-manifest.json").read_text())["kit_commit"] is None


@pytest.mark.parametrize("bad_files", [["oops"], "oops", 7])
def test_a_baseline_whose_files_is_not_a_dict_degrades(tmp_path, bad_files, capsys):
    """Trust keys on `kit_commit`'s presence, so the minimal hand-edit that
    turns the split ON is also what made this path reachable — and it raised
    AttributeError, aborting the whole read-only diagnostic. Same
    degrade-don't-abort rule the `kit_commit` normalization already obeyed,
    reached through the same gate (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root, _manifest({rel: _sha("kit")}), config, {"kit_commit": None, "files": bad_files}
    )
    assert next(f for f in report.files if f.path == rel).state == "differs"
    print(kit_doctor.render(report))  # must not raise
    assert "differ" in capsys.readouterr().out


def test_a_baseline_entry_that_is_not_a_dict_degrades(tmp_path):
    """Same hazard one level down: `files` is a dict but an entry is not."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root,
        _manifest({rel: _sha("kit")}),
        config,
        {"kit_commit": None, "files": {rel: "not-a-dict"}},
    )
    assert next(f for f in report.files if f.path == rel).state == "differs"


def test_a_partial_record_exits_nonzero_and_names_what_it_left_out(tmp_path, capsys):
    """The stderr warning had zero coverage through `main`, and the mode exited
    0 regardless — so an agent-driven /adopt or /upgrade reading only the status
    code would treat a partial record as complete (panel, adversarial lens)."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "check_doc_budget.py", "the adopter's own file")
    kit = tmp_path / "kit"
    (kit / ".git").mkdir(parents=True)
    _write(
        kit / "kit-manifest.json",
        json.dumps({"files": {"scripts/check_doc_budget.py": {"sha256": _sha("the kit's")}}}),
    )
    real_head = kit_doctor._git_head
    kit_doctor._git_head = lambda p: "d" * 40
    try:
        code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
    finally:
        kit_doctor._git_head = real_head
    err = capsys.readouterr().err
    assert code == 1, "a partial record must not report success"
    # Named by its LOCAL path, which is what the operator has to go look at —
    # the kit-layout key would send them to a directory that does not exist here.
    assert "scripts/devkit/check_doc_budget.py" in err
    assert "scripts/check_doc_budget.py\n" not in err


def test_the_kit_bug_nudge_fires_on_a_trusted_local_edit(tmp_path, capsys):
    """`show_nudge`'s trusted branch was unpinned: hardcoding it False left the
    suite green (panel, adversarial lens). The nudge is the only place the
    report tells an adopter that editing an engine is a kit bug worth
    reporting."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "edited here")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    edited = kit_doctor.inspect(
        root, _manifest({rel: _sha("kit")}), config, _baseline({rel: _sha("kit")})
    )
    assert next(f for f in edited.files if f.path == rel).state == "locally-edited"
    print(kit_doctor.render(edited))
    assert "Engines are kit-owned" in capsys.readouterr().out


def test_the_kit_bug_nudge_stays_silent_when_the_file_is_only_stale(tmp_path, capsys):
    """The discriminating half. A stale file is not an edit, so telling its
    owner they may have found a kit bug is noise — and a nudge that fired on
    everything would satisfy the test above without pinning anything."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    rel = "scripts/check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    stale = kit_doctor.inspect(
        root, _manifest({rel: _sha("kit")}), config, _baseline({rel: _sha("installed")})
    )
    assert next(f for f in stale.files if f.path == rel).state == "stale"
    print(kit_doctor.render(stale))
    assert "Engines are kit-owned" not in capsys.readouterr().out
