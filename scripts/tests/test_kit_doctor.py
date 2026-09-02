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

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest
from _repo_layout import engine_dir, find_repo_root

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

import kit_doctor  # noqa: E402
import panel_prompt  # noqa: E402
import run_installed_tests  # noqa: E402
import runtime_adapters  # noqa: E402

LEGACY_CODEX_SHA256 = {
    "adopt": "fee749f57477fc21ced59027209d48eac22fafc44b15307bfff209028897def9",
    "parallel": "c5e34023e188965187727caa77939edbfe71cf762247e27afc0b7b6b9aa58882",
    "pr-watch": "549e0d08f78c6ed5814f2504451d7a11c0a8bc593dc9420ccec9b07d784973f8",
    "upgrade": "b667fea4d997d0e4126518501bb8deac276aba42fcf26e2f80a7ddd26f9fba54",
}


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


def _lens_repo(tmp_path: Path, *, engines: str = "scripts") -> Path:
    root = _fake_repo(tmp_path, engines=engines)
    _write(
        root / "config" / "dev-model.yaml",
        f"""kit:
  version: 2
paths:
  handoff: docs/handoff.md
  friction_log: docs/friction-log.md
  engines: {engines}
review:
  fallback_panel:
    lenses:
      - name: adversarial
        focus: Try to prove the change wrong.
    lens_compute:
      claude:
        model: sonnet
        effort: high
""",
    )
    engine = root / engines
    shutil.copy2(ENGINE_DIR / "panel_prompt.py", engine / "panel_prompt.py")
    shutil.copy2(ENGINE_DIR / "kit_doctor.py", engine / "kit_doctor.py")
    shutil.copytree(ENGINE_DIR / "lib", engine / "lib")
    return root


@pytest.mark.parametrize("engines", ["scripts", "scripts/devkit", "scr&ipts"])
def test_lens_definition_inspection_reports_missing_current_and_stale(tmp_path, engines):
    root = _lens_repo(tmp_path, engines=engines)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    missing = kit_doctor.inspect_lens_definitions(root, config, engines)
    assert [(item.lens, item.state) for item in missing] == [("adversarial", "missing")]
    missing_rendered = kit_doctor.render(
        kit_doctor.Report(
            kit_version_config=2,
            kit_version_manifest=2,
            engines_dir=engines,
            engines_dir_ok=True,
            hooks_installed=True,
            narrative_rendered={},
            inspection_root=root,
            lens_definitions=missing,
        )
    )
    assert "⚠ .claude/agents/adversarial.md [claude lens=adversarial]" in missing_rendered
    assert "not present — generate it before the next session" in missing_rendered

    definition = root / ".claude" / "agents" / "adversarial.md"
    remedy_template = kit_doctor._lens_definition_regeneration_command(root, engines)
    assert remedy_template in missing_rendered
    remedy = remedy_template.replace("<name>", "adversarial")
    uv_stub = tmp_path / "bin" / "uv"
    _write(
        uv_stub,
        "#!/bin/sh\n"
        '[ "$1" = run ] || exit 64\n'
        "shift\n"
        f"exec {shlex.quote(sys.executable)} \"$@\"\n",
    )
    uv_stub.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{uv_stub.parent}{os.pathsep}{env.get('PATH', '')}"
    caller = root / "docs" / "probe"
    caller.mkdir(parents=True)
    regenerated = subprocess.run(
        ["sh", "-c", remedy],
        cwd=caller,
        env=env,
        capture_output=True,
        check=False,
    )
    assert regenerated.returncode == 0, regenerated.stderr.decode("utf-8", "replace")
    current = kit_doctor.inspect_lens_definitions(root, config, engines)
    assert [(item.lens, item.state) for item in current] == [("adversarial", "current")]

    definition.write_text(
        definition.read_text(encoding="utf-8") + "Hand edit.\n", encoding="utf-8"
    )
    stale = kit_doctor.inspect_lens_definitions(root, config, engines)
    assert [(item.lens, item.state) for item in stale] == [("adversarial", "stale")]
    rendered = kit_doctor.render(
        kit_doctor.Report(
            kit_version_config=2,
            kit_version_manifest=2,
            engines_dir=engines,
            engines_dir_ok=True,
            hooks_installed=True,
            narrative_rendered={},
            inspection_root=root,
            lens_definitions=stale,
        )
    )
    assert "inspect and regenerate it" in rendered
    assert "this check never executes the command or writes the definitions" in rendered
    assert kit_doctor._lens_definition_regeneration_command(root, engines) in rendered

    with definition.open("wb") as output:
        regenerated = subprocess.run(
            [
                sys.executable,
                str(root / engines / "panel_prompt.py"),
                "--root",
                str(root),
                "--lens",
                "adversarial",
                "--agent-definition",
            ],
            cwd=root,
            stdout=output,
            stderr=subprocess.PIPE,
            check=False,
        )
    assert regenerated.returncode == 0, regenerated.stderr.decode("utf-8", "replace")
    refreshed = kit_doctor.inspect_lens_definitions(root, config, engines)
    assert [(item.lens, item.state) for item in refreshed] == [
        ("adversarial", "current")
    ]


def test_the_lens_remedy_does_not_prescribe_an_engine_this_tree_lacks(tmp_path):
    """#661's second occurrence: the remedy was printed unconditionally, against
    the KIT's dependency graph rather than the adopter's installed surface. One
    surveyed repo had no `panel_prompt.py` anywhere and was told to run it.

    The VERDICT is untouched — the definitions really are missing, and this
    tests only which remedy is named. The alternative has to be runnable, so it
    is asserted as such rather than as the absence of the first one: an
    empty parenthetical would pass a `not in` check while telling the operator
    nothing.
    """
    root = _lens_repo(tmp_path)
    (root / "scripts" / "panel_prompt.py").unlink()
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")
    assert [(item.lens, item.state) for item in statuses] == [("adversarial", "missing")]

    rendered = kit_doctor.render(
        kit_doctor.Report(
            kit_version_config=2,
            kit_version_manifest=2,
            engines_dir="scripts",
            engines_dir_ok=True,
            hooks_installed=True,
            narrative_rendered={},
            inspection_root=root,
            lens_definitions=statuses,
        )
    )

    assert kit_doctor._lens_definition_regeneration_command(root, "scripts") not in rendered
    assert "scripts/panel_prompt.py — is NOT installed here" in rendered
    assert "<kit checkout>/scripts/panel_prompt.py --root . --lens <name>" in rendered
    # The invariant holds on both branches: naming a command is not running one.
    assert "this check never executes the command or writes the definitions" in rendered


def test_a_configured_compute_change_makes_the_definition_stale(tmp_path):
    root = _lens_repo(tmp_path)
    definition = root / ".claude" / "agents" / "adversarial.md"
    _write(definition, panel_prompt.agent_definition(root, "adversarial", "claude"))
    config_path = root / "config" / "dev-model.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace("model: sonnet", "model: opus"),
        encoding="utf-8",
    )
    config = kit_doctor.load_config(config_path)

    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")

    assert [(item.lens, item.state) for item in statuses] == [("adversarial", "stale")]


def test_lens_inspection_does_not_execute_the_adopter_generator(tmp_path):
    root = _lens_repo(tmp_path)
    sentinel = root / "doctor-executed-generator"
    _write(
        root / "scripts" / "panel_prompt.py",
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('ran')\n",
    )
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")

    assert [(item.lens, item.state) for item in statuses] == [
        ("adversarial", "missing")
    ]
    assert not sentinel.exists()


def test_a_malformed_lens_roster_is_unverifiable(tmp_path):
    root = _lens_repo(tmp_path)
    config_path = root / "config" / "dev-model.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "    lenses:\n"
            "      - name: adversarial\n"
            "        focus: Try to prove the change wrong.\n",
            "    lenses: malformed\n",
        ),
        encoding="utf-8",
    )
    config = kit_doctor.load_config(config_path)

    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")

    assert [(item.lens, item.state) for item in statuses] == [("", "unverifiable")]
    assert "roster is not a list" in statuses[0].detail


def test_a_malformed_lens_roster_entry_is_unverifiable(tmp_path):
    root = _lens_repo(tmp_path)
    config_path = root / "config" / "dev-model.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "      - name: adversarial\n        focus: Try to prove the change wrong.\n",
            "      - focus: Try to prove the change wrong.\n",
        ),
        encoding="utf-8",
    )
    config = kit_doctor.load_config(config_path)

    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")

    assert [(item.lens, item.state) for item in statuses] == [("", "unverifiable")]
    assert "entry has no string name" in statuses[0].detail


def test_an_unreadable_lens_definition_is_reported_and_rendered(
    tmp_path, monkeypatch
):
    root = _lens_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    definition = root / ".claude" / "agents" / "adversarial.md"
    _write(definition, panel_prompt.agent_definition(root, "adversarial", "claude"))
    original_read_bytes = Path.read_bytes

    def fail_target_read(path):
        if path == definition:
            raise PermissionError("definition denied")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_target_read)
    statuses = kit_doctor.inspect_lens_definitions(root, config, "scripts")

    assert [(item.lens, item.state) for item in statuses] == [
        ("adversarial", "unreadable")
    ]
    rendered = kit_doctor.render(
        kit_doctor.Report(
            kit_version_config=2,
            kit_version_manifest=2,
            engines_dir="scripts",
            engines_dir_ok=True,
            hooks_installed=True,
            narrative_rendered={},
            lens_definitions=statuses,
        )
    )
    assert "⚠ .claude/agents/adversarial.md [claude lens=adversarial]" in rendered
    assert "unreadable — definition denied" in rendered


def test_regeneration_imports_the_sibling_doctor_before_a_lib_shadow(tmp_path):
    root = _lens_repo(tmp_path)
    sentinel = root / "shadow-doctor-executed"
    _write(
        root / "scripts" / "lib" / "kit_doctor.py",
        f"""from pathlib import Path
Path({str(sentinel)!r}).write_text("ran")
AGENT_DEFINITION_RUNTIME = "claude"
class LensDefinitionError(ValueError):
    pass
def render_agent_definition(*_args):
    return "shadow output"
""",
    )

    generated = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "panel_prompt.py"),
            "--root",
            str(root),
            "--lens",
            "adversarial",
            "--agent-definition",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert generated.returncode == 0, generated.stderr
    assert generated.stdout == panel_prompt.agent_definition(
        root, "adversarial", "claude"
    )
    assert not sentinel.exists()


def test_json_reports_missing_lens_definitions_as_advisory(tmp_path, capsys):
    root = _lens_repo(tmp_path)
    manifest_path = tmp_path / "comparison.json"
    manifest_path.write_text(
        json.dumps(kit_doctor.generate_manifest(root, 2)), encoding="utf-8"
    )

    code = kit_doctor.main(
        ["--json", "--root", str(root), "--manifest", str(manifest_path)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["lens_definitions"] == [
        {
            "runtime": "claude",
            "lens": "adversarial",
            "surface": ".claude/agents/adversarial.md",
            "state": "missing",
            "detail": "not present",
        }
    ]


def test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes():
    statuses = runtime_adapters.compare_adapters(REPO_ROOT, REPO_ROOT)
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for pattern in (".claude/commands/*.md", ".agents/skills/*/SKILL.md")
        for path in REPO_ROOT.glob(pattern)
    }

    assert statuses
    assert {status.runtime for status in statuses} == {"claude", "codex"}
    assert {status.state for status in statuses} == {"kit-current"}
    assert {status.path for status in statuses} == actual_paths
    parity = (REPO_ROOT / "docs" / "agentic-dev-kit" / "runtime-parity.md").read_text(
        encoding="utf-8"
    )
    assert "fetched kit's adapter renderer" in parity
    assert "authored command preserved" in parity
    assert "authored skill preserved" in parity
    assert not {
        path
        for path, _role in kit_doctor.KIT_OWNED
        if path.startswith((".claude/", ".agents/"))
    }


@pytest.mark.parametrize("slug", ["adopt", "parallel", "pr-watch", "upgrade"])
def test_previous_generated_codex_adapter_is_refreshable_not_adopter_owned(tmp_path, slug):
    source = REPO_ROOT
    adopter = tmp_path / "adopter"
    rel = f".agents/skills/{slug}/SKILL.md"
    source_text = (source / rel).read_text(encoding="utf-8")
    description = runtime_adapters._frontmatter(source_text)["description"]
    legacy = runtime_adapters.render_adapter(
        "codex",
        slug,
        description,
        f"docs/agentic-dev-kit/workflows/{slug}.md",
        template_version=1,
    )
    assert hashlib.sha256(legacy.encode()).hexdigest() == LEGACY_CODEX_SHA256[slug]
    assert legacy == runtime_adapters.render_adapter(
        "codex",
        slug,
        f"{description} Future wording.",
        f"docs/agentic-dev-kit/workflows/{slug}.md",
        template_version=1,
    )
    _write(adopter / rel, legacy)

    statuses = runtime_adapters.compare_adapters(source, adopter)
    status = next(item for item in statuses if item.path == rel)

    assert status.state == "kit-stale"
    assert "refresh freely" in status.detail


def test_authored_adapter_change_is_reported_and_preserved_for_each_runtime(tmp_path):
    adopter = tmp_path / "adopter"
    shutil.copytree(REPO_ROOT / ".claude", adopter / ".claude")
    shutil.copytree(REPO_ROOT / ".agents", adopter / ".agents")
    changed = {
        ".claude/commands/adopt.md",
        ".agents/skills/adopt/SKILL.md",
    }
    for rel in changed:
        path = adopter / rel
        path.write_text(
            path.read_text(encoding="utf-8") + "\nKeep this adopter policy.\n",
            encoding="utf-8",
        )
    before = {rel: (adopter / rel).read_bytes() for rel in changed}

    statuses = runtime_adapters.compare_adapters(REPO_ROOT, adopter)
    by_path = {status.path: status for status in statuses}

    for rel in changed:
        assert by_path[rel].state == "adopter-owned"
        assert "leave unchanged" in by_path[rel].detail
        assert (adopter / rel).read_bytes() == before[rel]


@pytest.mark.parametrize(
    "runtime, rel",
    [
        ("claude", ".claude/commands/adopt.md"),
        ("codex", ".agents/skills/adopt/SKILL.md"),
    ],
)
def test_adapter_report_preserves_a_symlink_path_as_adopter_owned(tmp_path, runtime, rel):
    adopter = tmp_path / "adopter"
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    path = adopter / rel
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    statuses = runtime_adapters.compare_adapters(REPO_ROOT, adopter)
    status = next(item for item in statuses if item.runtime == runtime and item.path == rel)

    assert status.state == "adopter-owned"
    assert "symlink" in status.detail
    assert path.is_symlink()
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_adapter_report_preserves_a_symlinked_ancestor_as_adopter_owned(tmp_path):
    adopter = tmp_path / "adopter"
    outside = tmp_path / "outside-agents"
    outside.mkdir()
    adopter.mkdir()
    (adopter / ".agents").symlink_to(outside, target_is_directory=True)

    statuses = runtime_adapters.compare_adapters(REPO_ROOT, adopter)
    status = next(
        item
        for item in statuses
        if item.runtime == "codex" and item.path == ".agents/skills/adopt/SKILL.md"
    )

    assert status.state == "adopter-owned"
    assert "symlink at .agents" in status.detail
    assert list(outside.iterdir()) == []


def test_adapter_report_preserves_a_hardlinked_path_as_adopter_owned(tmp_path):
    adopter = tmp_path / "adopter"
    outside = tmp_path / "outside.md"
    outside.write_text(
        (REPO_ROOT / ".agents/skills/adopt/SKILL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = adopter / ".agents/skills/adopt/SKILL.md"
    path.parent.mkdir(parents=True)
    path.hardlink_to(outside)
    before = outside.read_bytes()

    statuses = runtime_adapters.compare_adapters(REPO_ROOT, adopter)
    status = next(item for item in statuses if item.path == ".agents/skills/adopt/SKILL.md")

    assert status.state == "adopter-owned"
    assert "multiply-linked" in status.detail
    assert path.stat().st_ino == outside.stat().st_ino
    assert path.read_bytes() == before
    assert outside.read_bytes() == before


def test_installed_test_targets_use_manifest_not_directory_contents(tmp_path):
    root = tmp_path / "adopter"
    declared = root / "scripts" / "devkit" / "tests" / "test_declared.py"
    undeclared = root / "scripts" / "devkit" / "tests" / "test_undeclared.py"
    state_paths = (
        root
        / "scripts"
        / "devkit"
        / "lib"
        / "state_paths"
        / "tests"
        / "test_state_paths.py"
    )
    _write(declared, "def test_declared(): pass\n")
    _write(undeclared, "raise AssertionError('must not run')\n")
    _write(state_paths, "def test_state_paths(): pass\n")
    manifest = root / "kit-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": {
                    "scripts/tests/test_declared.py": {"role": "test"},
                    "scripts/lib/state_paths/tests/test_state_paths.py": {
                        "role": "test"
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assert run_installed_tests.installed_test_targets(
        root, manifest, "scripts/devkit"
    ) == [state_paths, declared]


def test_installed_test_main_invokes_pytest_and_propagates_failure(
    tmp_path, monkeypatch
):
    root = tmp_path / "adopter"
    runner = root / "scripts" / "devkit" / "run_installed_tests.py"
    target = root / "scripts" / "devkit" / "tests" / "test_declared.py"
    _write(runner, "# installed runner location\n")
    _write(target, "def test_declared(): pass\n")
    (root / "kit-manifest.json").write_text(
        json.dumps({"files": {"scripts/tests/test_declared.py": {"role": "test"}}}),
        encoding="utf-8",
    )
    calls = []

    def fake_pytest_main(args):
        calls.append(args)
        return 7

    monkeypatch.setattr(run_installed_tests, "__file__", str(runner))
    monkeypatch.setattr(run_installed_tests.pytest, "main", fake_pytest_main)

    assert run_installed_tests.main(["--root", str(root)]) == 7
    assert calls == [[str(target), "-q"]]


def test_installed_test_main_reports_a_successful_empty_suite(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "adopter"
    runner = root / "scripts" / "devkit" / "run_installed_tests.py"
    _write(runner, "# installed runner location\n")
    (root / "kit-manifest.json").write_text(
        json.dumps({"files": {}}), encoding="utf-8"
    )
    monkeypatch.setattr(run_installed_tests, "__file__", str(runner))
    monkeypatch.setattr(
        run_installed_tests.pytest,
        "main",
        lambda _args: pytest.fail("pytest must not run for an empty declared suite"),
    )

    assert run_installed_tests.main(["--root", str(root)]) == 0
    assert "none declared installed — suite skipped" in capsys.readouterr().out


def test_installed_test_targets_and_main_refuse_a_declared_missing_module(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "adopter"
    runner = root / "scripts" / "devkit" / "run_installed_tests.py"
    _write(runner, "# installed runner location\n")
    manifest = root / "kit-manifest.json"
    manifest.write_text(
        json.dumps({"files": {"scripts/tests/test_missing.py": {"role": "test"}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing or not regular"):
        run_installed_tests.installed_test_targets(root, manifest, "scripts/devkit")

    monkeypatch.setattr(run_installed_tests, "__file__", str(runner))
    with pytest.raises(SystemExit) as exc_info:
        run_installed_tests.main(["--root", str(root)])

    assert exc_info.value.code == 2
    assert "missing or not regular" in capsys.readouterr().err


def test_installed_test_targets_skip_a_declined_missing_test_root(tmp_path):
    manifest = tmp_path / "kit-manifest.json"
    manifest.write_text(json.dumps({"files": {}}), encoding="utf-8")

    assert run_installed_tests.installed_test_targets(tmp_path, manifest, "scripts") == []


def test_doctor_default_report_starts_without_the_adapter_renderer(tmp_path):
    root = _fake_repo(tmp_path / "adopter", engines="scripts/devkit")
    engine = root / "scripts" / "devkit"
    shutil.copy2(ENGINE_DIR / "kit_doctor.py", engine / "kit_doctor.py")
    shutil.copytree(
        ENGINE_DIR / "lib",
        engine / "lib",
        ignore=shutil.ignore_patterns("runtime_adapters.py"),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(engine / "kit_doctor.py"),
            "--root",
            str(root),
            "--manifest",
            str(REPO_ROOT / "kit-manifest.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ModuleNotFoundError" not in result.stderr
    assert "runtime_adapters" not in result.stderr


def test_installed_test_targets_refuse_declared_symlink(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("def test_outside(): pass\n", encoding="utf-8")
    target = tmp_path / "scripts" / "tests" / "test_link.py"
    target.parent.mkdir(parents=True)
    target.symlink_to(outside)
    manifest = tmp_path / "kit-manifest.json"
    manifest.write_text(
        json.dumps({"files": {"scripts/tests/test_link.py": {"role": "test"}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="crosses a symlink"):
        run_installed_tests.installed_test_targets(tmp_path, manifest, "scripts")


def test_installed_test_targets_refuse_declared_symlinked_ancestor(tmp_path):
    outside = tmp_path / "outside-tests"
    outside.mkdir()
    (outside / "test_link.py").write_text("def test_outside(): pass\n", encoding="utf-8")
    engine = tmp_path / "scripts"
    engine.mkdir()
    test_root = engine / "tests"
    test_root.symlink_to(outside, target_is_directory=True)
    before = (outside / "test_link.py").read_bytes()
    manifest = tmp_path / "kit-manifest.json"
    manifest.write_text(
        json.dumps({"files": {"scripts/tests/test_link.py": {"role": "test"}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="crosses a symlink"):
        run_installed_tests.installed_test_targets(tmp_path, manifest, "scripts")
    assert test_root.is_symlink()
    assert (outside / "test_link.py").read_bytes() == before


def test_adapter_report_refuses_a_source_adapter_the_renderer_does_not_own(
    tmp_path, capsys
):
    source = tmp_path / "source"
    shutil.copytree(REPO_ROOT / ".claude", source / ".claude")
    shutil.copytree(REPO_ROOT / ".agents", source / ".agents")
    shutil.copytree(
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows",
        source / "docs" / "agentic-dev-kit" / "workflows",
    )
    path = source / ".claude" / "commands" / "adopt.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nSource drift.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not equal the current rendered form"):
        runtime_adapters.compare_adapters(source, REPO_ROOT)

    code = kit_doctor.main(
        [
            "--root",
            str(REPO_ROOT),
            "--adapter-report",
            "--adapter-source",
            str(source),
        ]
    )

    assert code == 2
    assert "does not equal the current rendered form" in capsys.readouterr().err


def test_adapter_report_cli_is_read_only_and_does_not_require_adopter_config(
    tmp_path, capsys
):
    code = kit_doctor.main(
        [
            "--root",
            str(tmp_path),
            "--adapter-report",
            "--adapter-source",
            str(REPO_ROOT),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["adapters"]
    assert {item["state"] for item in payload["adapters"]} == {"missing"}
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "extra",
    [
        ["--generate-manifest"],
        ["--record-install"],
        ["--from-kit", "source"],
        ["--manifest", "comparison.json"],
        ["--baseline", "baseline.json"],
    ],
)
def test_adapter_report_refuses_drift_and_write_options(tmp_path, capsys, extra):
    with pytest.raises(SystemExit) as exc:
        kit_doctor.main(
            [
                "--root",
                str(tmp_path),
                "--adapter-report",
                "--adapter-source",
                str(REPO_ROOT),
                *extra,
            ]
        )

    assert exc.value.code == 2
    assert "separate informational mode" in capsys.readouterr().err


def test_adapter_source_requires_adapter_report(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        kit_doctor.main(["--root", str(tmp_path), "--adapter-source", str(REPO_ROOT)])

    assert exc.value.code == 2
    assert "requires --adapter-report" in capsys.readouterr().err


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
    # The fixture changed when init.sh's guard was anchored to the OPENING of
    # line 1 (panel round 6). The old one — `# Title\r<!-- marker -->` — no
    # longer discriminates: both predicates now correctly call it in use, since
    # line 1 does not open with the marker comment under either reader.
    #
    # This one does. read_bytes ends line 1 at LF, as `head -n 1` does, so the
    # whole file is line 1 and the CR after `<!--` is stripped as a blank,
    # leaving the marker first — a skeleton. read_text translates the CR to a
    # newline, ending line 1 at `<!--` alone, and reports the file in use while
    # init.sh seeds straight over it.
    (root / "docs" / "handoff.md").write_bytes(
        b"<!--\rdevkit-template: unrendered -->\rbody\r"
    )
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    report = kit_doctor.inspect(root, _manifest({}), config)

    assert report.narrative_rendered["docs/handoff.md"] is False


@pytest.mark.parametrize(
    ("skeleton", "first_line"),
    [
        # The two shipped shapes.
        (True, "<!-- devkit-template: unrendered — ./init.sh renders this. -->"),
        (True, "<!-- devkit-source: kit-own — the kit's own entry point. -->"),
        (True, "<!--   devkit-template: unrendered   -->"),
        # No blank between the marker and `-->` — BOTH predicates reject this,
        # verified against the shell rather than assumed. The shipped markers
        # always carry a space, and the boundary that stops `kit-ownership`
        # cannot also admit `kit-own-->`. Conservative direction: a hand-written
        # tight marker is left alone rather than overwritten.
        (False, "<!--devkit-source: kit-own-->"),
        (True, "<!-- devkit-source: kit-own"),
        # A CR after the marker is a blank to `sed` and the shell glob, so it
        # must be one here. `" \t"` alone made the two disagree on a
        # CR-delimited file.
        (True, "<!-- devkit-source: kit-own\r-->"),
        # Mentions, not markers — line 1 must OPEN with the marker comment.
        (False, "Note: the kit marks its files `devkit-source: kit-own` on line 1."),
        (False, "<!-- see the kit's devkit-source: kit-own convention -->"),
        (False, "<!-- migration note: we dropped the devkit-template: unrendered line -->"),
        # Prefix collision — the boundary after the marker is what stops it.
        (False, "<!-- devkit-source: kit-ownership notes, ours -->"),
        (False, "# CLAUDE.md — mine"),
        (False, ""),
        (False, "<!--"),
    ],
)
def test_still_a_skeleton_matches_init_sh_s_rule(skeleton, first_line):
    """The Python half of a predicate whose two halves have diverged three times:
    round 2 anchored `init.sh` to line 1 and left this reading the whole file;
    round 6 anchored `init.sh` to the opening comment and left this a bare
    substring; the first fix for THAT compared the boundary with `" \\t"` while
    `sed` uses `[[:space:]]`, which includes CR.

    A disagreement is never cosmetic here — the doctor prescribes `run ./init.sh`
    for a file `init.sh` will refuse to touch, or stays silent about one it will
    overwrite. These shapes mirror `test_a_marker_quoted_in_prose_on_line_1_is_not_seedable`
    on the shell side deliberately, so the two suites pin the same boundary."""
    assert kit_doctor._still_a_skeleton(first_line) is skeleton


@pytest.mark.parametrize("entry_point", ["AGENTS.md", "CLAUDE.md"])
def test_a_kit_own_entry_point_is_reported_as_unrendered(tmp_path, entry_point):
    """The round-6 HIGH: `/upgrade` Step 1 promises this check and `inspect()`
    did not implement it, so a `cp -r` adopter whose `./init.sh` never completed
    got a CLEAN report while both entry points still carried the kit's contract.

    Mutation-checked rather than assumed — deleting the entry points from
    `inspect()`'s target list left the whole suite green (panel round 7,
    correctness), which is how the gap survived the round that fixed it."""
    root = _fake_repo(tmp_path)
    _write(root / entry_point, "<!-- devkit-source: kit-own — the kit's own -->\n# kit\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    report = kit_doctor.inspect(root, _manifest({}), config)

    assert entry_point in report.narrative_rendered, (
        f"{entry_point} is not even checked — `/upgrade` Step 1 says it is"
    )
    assert report.narrative_rendered[entry_point] is False


@pytest.mark.parametrize("entry_point", ["AGENTS.md", "CLAUDE.md"])
def test_an_adopters_own_entry_point_is_reported_in_use(tmp_path, entry_point):
    """The control. Without it, a check that always reported False would satisfy
    the test above while telling every adopter to re-run ./init.sh forever."""
    root = _fake_repo(tmp_path)
    _write(root / entry_point, "# ours, hand written\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    report = kit_doctor.inspect(root, _manifest({}), config)

    assert report.narrative_rendered[entry_point] is True


@pytest.mark.parametrize("shape", ["directory", "broken symlink", "unreadable"])
def test_a_target_init_sh_will_not_touch_is_not_reported_as_unrendered(tmp_path, shape):
    """`doc.is_file()` alone conflated three things with "missing", and only
    missing warrants `run ./init.sh`.

    A directory named AGENTS.md and a dangling symlink are both left alone by
    `_seedable`, so telling the operator to run the command that will refuse them
    is the no-op remedy round 2 removed. An unreadable file raised OSError out of
    `read_bytes()` and aborted the ENTIRE report — thirty-two other files
    undiagnosed because of one. Both found by the review bot on PR #289."""
    root = _fake_repo(tmp_path)
    target = root / "AGENTS.md"
    if shape == "directory":
        target.mkdir()
    elif shape == "broken symlink":
        target.symlink_to("no-such-file-9f2a.md")
    else:
        _write(target, "<!-- devkit-source: kit-own -->\n")
        target.chmod(0o000)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")

    try:
        report = kit_doctor.inspect(root, _manifest({}), config)
    finally:
        if shape == "unreadable":
            target.chmod(0o644)

    assert report.narrative_rendered["AGENTS.md"] is True
    # The report still covers everything else — the point of not aborting.
    assert "docs/handoff.md" in report.narrative_rendered


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


def test_the_installer_is_tracked():
    """`init.sh` must stay in KIT_OWNED (#360).

    It was absent from both KIT_OWNED and the manifest, which made the file that
    PERFORMS every install the one file this report structurally could not range
    over. cs-toolkit's copy stood 852 differing lines out while its doctor
    reported `13 unchanged, 0 differ, 0 missing` and exited 0.

    Asserted against KIT_OWNED rather than only the manifest because the manifest
    is GENERATED from it: a check that read the manifest alone would pass on a
    stale artifact and miss the removal it exists to catch. Manifest sync itself
    is `test_shipped_manifest_covers_every_kit_owned_file`.
    """
    owned = dict(kit_doctor.KIT_OWNED)
    assert "init.sh" in owned, "init.sh dropped out of KIT_OWNED — see #360"
    assert owned["init.sh"] == "installer", (
        "init.sh's role drives two mechanisms, so changing it is not cosmetic: "
        "`engine` would feed it to _ENGINE_NAMES and to the _TEXT_IMPORT_RE "
        "dependency scan, neither of which applies to a root-level shell script "
        "that declares no non-stdlib dependency."
    )


# The premise that makes a plain KIT_OWNED entry for init.sh correct — that an
# adopter's copy is NOT expected to diverge — is pinned BEHAVIOURALLY, by running
# the installer and comparing its own bytes, in
# test_init_sh.py::test_running_the_installer_does_not_modify_the_installer.
#
# It lived here first as a regex over init.sh's source, looking for `> $0`,
# `sed -i … init.sh` and similar. An adversarial lens killed that version by
# inserting a self-overwrite the pattern could not see:
#
#     SELF_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
#     cp "/tmp/newer-init.sh" "$SELF_PATH"
#
# `sh -n` accepted it, the guard passed, and that indirect shape is the one a
# real "self-updating installer" change would take — nobody truncates a
# 1500-line script in place. Two further reasons a textual guard was the wrong
# instrument, both found while repairing it: the write verb is open-ended
# (`cp`/`mv`/`install`/`dd`/a downloader), and init.sh contains 14 `$0`
# occurrences that are all AWK's current-record variable, so anchoring on `$0`
# at all starts from 14 false positives. Observing the outcome has none of these
# problems and needs no list of verbs.


def test_the_installers_premise_is_pinned_in_test_init_sh():
    """A pointer test, so the cross-file dependency is not only a comment.

    Named for the one thing it checks. It was
    `test_the_installer_is_tracked_and_its_premise_is_pinned_elsewhere`, a
    compound name whose first clause this body never checked — that is
    `test_the_installer_is_tracked` above. A correctness lens flagged it; the
    cheaper fix is the honest name, not a second assertion duplicating a sibling.

    If the behavioural guard named below is renamed or deleted, this fails and
    says why it mattered — otherwise the #360 decision would keep its rationale
    and quietly lose its evidence.
    """
    guard = "test_running_the_installer_does_not_modify_the_installer"
    text = (Path(__file__).parent / "test_init_sh.py").read_text(encoding="utf-8")
    # `def <guard>(` — the trailing paren is load-bearing. Matching `def <guard>`
    # alone is a SUBSTRING check, so renaming the guard to
    # `<guard>_RENAMED` left the old name as a prefix and this test kept passing.
    # An adversarial lens found that by doing exactly that rename.
    assert f"def {guard}(" in text, (
        f"{guard} is gone from test_init_sh.py. It is the only thing pinning "
        "the premise behind init.sh's KIT_OWNED entry: that an adopter's copy is "
        "not expected to diverge, so `stale` rather than `locally-edited` is the "
        "state they land in. Restore it or re-open the #360 design question."
    )


def test_an_unedited_installer_behind_the_kit_reports_stale_not_locally_edited(tmp_path):
    """The behaviour the #360 decision turns on, driven through `inspect`.

    An adopter that has never touched `init.sh` but is behind the kit must land in
    `stale` — true, actionable, and it clears when they update — and must NOT land
    in `locally-edited`, which would be a permanent red on a file the adopter never
    edited and the objection that made #360 look like a design choice.

    Driven through `inspect` with `rel="init.sh"` rather than by calling
    `_drift_state` with synthetic hashes. An earlier version of this test did the
    latter and an adversarial lens killed it: it passed with `init.sh` removed
    from `KIT_OWNED` entirely, because nothing in it referred to the installer at
    all. `_drift_state`'s own table is covered by the sibling `_split_case` tests;
    what needs pinning here is that *this path*, with *this role*, reaches those
    states — which is why the `role` assertion is not decoration.

    Verified against the real adopter 2026-08-08: cs-toolkit reported `differs …
    not in baseline`, then `stale … installed 01f7ea7ea604, kit ships
    2b3372375106` against a re-recorded baseline.
    """
    older, current = "an older installer", "the installer the kit ships now"

    status, _ = _split_case(
        tmp_path, rel="init.sh", installed=older, ships=current, recorded=older
    )
    assert status.state == "stale", f"unedited-but-behind must be stale, got {status.state}"
    assert status.role == "installer", f"role regressed to {status.role}"
    assert "installed" in status.detail and "kit ships" in status.detail

    # The migration case: present locally, absent from a baseline recorded before
    # init.sh was tracked. `new-upstream` covers only files that are ABSENT, so
    # this is `differs` and exits 1 until the adopter re-records.
    status, _ = _split_case(
        tmp_path, rel="init.sh", installed=older, ships=current, recorded=None
    )
    assert status.state == "differs", f"absent from baseline must be differs, got {status.state}"

    # Control: the state that WOULD have been the objection to tracking, reached
    # only by an adopter who really did edit their installer.
    status, _ = _split_case(
        tmp_path, rel="init.sh", installed="edited by the adopter", ships=current, recorded=current
    )
    assert status.state == "locally-edited"


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
    # Same for the test suite (#493): `scripts/tests/` sits under the prefix an
    # adopter's `paths.engines` remaps, but role `test` is not role `engine`, so
    # none of it should be swept into the engines-dir probe. A vendored test
    # suite would otherwise make a sized-down install (kit_doctor.py + kitconfig
    # only, no tests) look like it "contains no kit engine" is the wrong verdict
    # for the WRONG reason — #59's bug reopened via the new role instead of the
    # old hand-written list.
    tests = [rel for rel, role in kit_doctor.KIT_OWNED if role == "test"]
    assert tests, "KIT_OWNED lists no tests — #493 regressed"
    for rel in tests:
        assert rel[len(kit_doctor.KIT_ENGINE_PREFIX) + 1 :] not in kit_doctor._ENGINE_NAMES


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


def test_generate_manifest_status_line_stays_off_stdout(tmp_path, capsys):
    """#464: the obvious invocation is `kit_doctor.py --generate-manifest >
    kit-manifest.json`. `manifest_path.write_text` puts the real JSON on disk
    through its own descriptor, unaffected by the redirect — so a `wrote ...`
    status line printed to STDOUT was the only thing that could go wrong, and
    it did: on the shell's redirect descriptor, still sitting at offset 0, it
    overwrote the opening bytes of the file just written in full, splicing the
    status message onto the tail of the JSON underneath. The fix is to keep
    this line off stdout entirely, so a redirect captures nothing and the two
    writers never compete for the same descriptor. See
    `test_a_shell_redirect_to_the_default_output_path_does_not_splice_the_manifest`
    below for the real OS-level reproduction this unit test cannot exercise —
    `capsys` intercepts the `sys.stdout` object, not the file descriptor a
    shell redirect rebinds."""
    root = _fake_repo(tmp_path)
    manifest_path = tmp_path / "kit-manifest.json"
    code = kit_doctor.main(
        ["--generate-manifest", "--root", str(root), "--manifest", str(manifest_path)]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"wrote {manifest_path}" in captured.err
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["kit_version"] == 2


def test_a_shell_redirect_to_the_default_output_path_does_not_splice_the_manifest(tmp_path):
    """The literal reproduction from #464: `kit_doctor.py --generate-manifest >
    kit-manifest.json`, with NO `--manifest` flag, so the redirect target and
    the tool's own write both name `<root>/kit-manifest.json` — the exact
    collision the bug depended on. The shell opens (and truncates) that path
    for its own fd 1 before exec; a real subprocess is what gives this test
    that fd, which an in-process `capsys` run does not have. Before the fix
    this reproduced with `json.load` raising `JSONDecodeError: Expecting
    value: line 1 column 1 (char 0)` on the result — the status line had
    overwritten the opening brace.

    Also the ONE test in this file where stderr is redirected (via
    `subprocess.PIPE`) but does NOT alias `manifest_path` — `stdout=` is the
    only thing bound to it here — so this is the case `_stream_aliases_path`
    must NOT suppress. The round-4 full-panel correctness lens found that
    nothing asserted on `result.stderr` anywhere in this file, so a mutant
    that always suppresses (equivalent to an inverted `if not
    _stream_aliases_path(...)`) passed the entire suite undetected — this
    assertion is the kill for that mutant."""
    root = _fake_repo(tmp_path)
    manifest_path = root / kit_doctor.MANIFEST_NAME
    script = ENGINE_DIR / "kit_doctor.py"
    with manifest_path.open("w", encoding="utf-8") as redirected_stdout:
        result = subprocess.run(
            [sys.executable, str(script), "--generate-manifest", "--root", str(root)],
            stdout=redirected_stdout,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    assert result.returncode == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["kit_version"] == 2
    assert "check_doc_budget.py" in json.dumps(manifest["files"])
    assert f"wrote {manifest_path}" in result.stderr


def test_a_merged_stream_redirect_does_not_splice_the_manifest(tmp_path):
    """The gap the fallback panel's adversarial lens found reviewing the fix
    above: routing the status line to stderr alone closes `>
    kit-manifest.json`, but `> kit-manifest.json 2>&1` (or `&>`) merges
    stderr onto the SAME descriptor the redirect opened, and the identical
    splice recurs on a stream this module had already "fixed" — reproduced
    live with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`,
    the exact #464 symptom, on a head that had already fixed the plain-stdout
    case. `stderr=subprocess.STDOUT` is the Python equivalent of the shell's
    `2>&1`: it tells the child to write its stderr to the same file object
    already bound to `stdout=`, which is this test's `manifest_path` handle —
    the real fd-level collision, not a simulation of it."""
    root = _fake_repo(tmp_path)
    manifest_path = root / kit_doctor.MANIFEST_NAME
    script = ENGINE_DIR / "kit_doctor.py"
    with manifest_path.open("w", encoding="utf-8") as redirected_stdout:
        result = subprocess.run(
            [sys.executable, str(script), "--generate-manifest", "--root", str(root)],
            stdout=redirected_stdout,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    assert result.returncode == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["kit_version"] == 2
    assert "check_doc_budget.py" in json.dumps(manifest["files"])


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
        "scripts/launch_lane.py",
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
        "scripts/kit_doctor.py",
        "scripts/lib/runtime_adapters.py",
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
    """The dependent carries its REAL hash, which is what makes it the version
    the edge was derived from. `_manifest`'s default `None` used to stand here
    and the assertion passed on presence alone — the confound #661 is about."""
    root = _fake_repo(tmp_path)  # installs scripts/check_doc_budget.py, no lib/
    target = root / "scripts" / "check_doc_budget.py"
    manifest = _manifest(
        {
            "scripts/check_doc_budget.py": kit_doctor.sha256_of(target),
            "scripts/lib/kitconfig.py": None,
        }
    )
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
    target = root / "scripts" / "devkit" / "check_doc_budget.py"
    manifest = _manifest(
        {
            "scripts/check_doc_budget.py": kit_doctor.sha256_of(target),
            "scripts/lib/kitconfig.py": None,
        }
    )
    manifest["files"]["scripts/lib/kitconfig.py"]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}
    assert states["scripts/devkit/lib/kitconfig.py"] == "missing-required"
    # The version check reads the dependent through the SAME remap. Comparing
    # the vendored copy against `scripts/check_doc_budget.py` in the kit's own
    # layout would find no file and drop the edge, restoring the sized-down
    # misreading this test exists to catch, one lookup over.
    assert [f.path for f in report.broken] == ["scripts/devkit/lib/kitconfig.py"]


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


def test_a_dependent_at_another_sha_does_not_make_a_new_dependency_broken(tmp_path):
    """#661's mechanism at its smallest. The edge is derived from the KIT's
    imports, so it describes the version the kit ships; the installed dependent
    is at a different sha and its imports are therefore unknown. Presence alone
    used to carry the edge across that gap and print "this install is broken,
    not sized down" over a library nothing installed here imports.

    The second half is what makes the narrowing safe rather than merely quieter:
    the dependent whose version could not be confirmed is reported as drift by
    the same run, so the report stops naming a remedy it cannot justify without
    going silent about the tree.
    """
    root = _fake_repo(tmp_path)
    lib = "scripts/lib/kitconfig.py"
    manifest = _manifest({"scripts/check_doc_budget.py": _sha("what the kit ships"), lib: None})
    manifest["files"][lib]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}

    assert states[lib] == "missing"
    assert report.broken == []
    assert states["scripts/check_doc_budget.py"] == "differs"
    assert [f.path for f in report.drifted] == ["scripts/check_doc_budget.py"]


def test_a_dependent_the_manifest_cannot_hash_drops_the_edge(tmp_path):
    """The third answer to "is this dependent the version the edge describes" is
    "unknown", and unknown resolves to NO edge — `derive_dependencies` states
    that asymmetry and this is the version axis obeying it.

    A manifest with no hash for the dependent is a manifest that cannot answer
    the question at all. It also cannot judge that dependent's drift, which is
    why the file lands `unknown-version` and the run still exits 1.
    """
    root = _fake_repo(tmp_path)
    lib = "scripts/lib/kitconfig.py"
    manifest = _manifest({"scripts/check_doc_budget.py": None, lib: None})
    manifest["files"][lib]["required_by"] = ["scripts/check_doc_budget.py"]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config)
    states = {f.path: f.state for f in report.files}

    assert states[lib] == "missing"
    assert report.broken == []
    assert states["scripts/check_doc_budget.py"] == "unknown-version"
    assert [f.path for f in report.drifted] == ["scripts/check_doc_budget.py"]


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


def _split_case(
    tmp_path,
    *,
    installed: str,
    ships: str,
    recorded: str | None,
    rel: str = "scripts/check_doc_budget.py",
):
    """Drive one row of the table: what the file says, what the kit ships, what
    the baseline recorded. Returns `(that file's FileStatus, the whole Report)` —
    the report so a caller can also assert on `baseline_trusted` or the counts.

    `rel` defaults to the engine every row of the original table used. It is a
    parameter so a caller can drive the SAME table for another kit-owned path
    without restating the machinery — `init.sh` does, since #360's decision is a
    claim about which of these states its adopters land in.
    """
    root = _fake_repo(tmp_path)
    _write(root / rel, installed)
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


def test_record_install_status_line_stays_off_stdout(tmp_path, capsys):
    """The sibling of `test_generate_manifest_status_line_stays_off_stdout`.
    `--record-install`'s default baseline path is the SAME `kit-manifest.json`
    `--generate-manifest` defaults to, and its own `wrote ...` line had the
    identical unfixed shape — found live by both the fallback panel's
    adversarial and correctness lenses, independently, while reviewing
    #464's `--generate-manifest` fix: `--record-install --from-kit <kit> >
    kit-manifest.json` reproduced the exact same splice, unfixed, in the
    very flag every `/adopt` and `/upgrade` actually runs."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    code = kit_doctor.main(["--record-install", "--root", str(root)])
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"wrote {root / kit_doctor.MANIFEST_NAME}" in captured.err


def test_a_shell_redirect_does_not_splice_the_record_install_baseline(tmp_path):
    """The `--record-install` counterpart to
    `test_a_shell_redirect_to_the_default_output_path_does_not_splice_the_manifest`:
    a real subprocess, `stdout` bound to an open handle on the same path the
    tool defaults to (`root/kit-manifest.json`, no `--baseline` override) —
    the literal collision. Before this fix this reproduced with `json.load`
    raising the same `JSONDecodeError: Expecting value: line 1 column 1
    (char 0)` `--generate-manifest` did.

    Same dual purpose as its sibling: stderr here is piped but does NOT
    alias `baseline_path`, so this is also the "must still print" case —
    see that test's docstring for why the assertion on `result.stderr`
    matters (round-4 full-panel correctness lens)."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    baseline_path = root / kit_doctor.MANIFEST_NAME
    script = ENGINE_DIR / "kit_doctor.py"
    with baseline_path.open("w", encoding="utf-8") as redirected_stdout:
        result = subprocess.run(
            [sys.executable, str(script), "--record-install", "--root", str(root)],
            stdout=redirected_stdout,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    assert result.returncode == 0
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert "scripts/check_doc_budget.py" in baseline["files"]
    assert f"wrote {baseline_path}" in result.stderr


def test_a_merged_stream_redirect_does_not_splice_the_record_install_baseline(tmp_path):
    """The `--record-install` counterpart to
    `test_a_merged_stream_redirect_does_not_splice_the_manifest`: `stdout`
    bound to `baseline_path`, `stderr=subprocess.STDOUT` merging the child's
    stderr onto that same handle — the real fd-level equivalent of `>
    kit-manifest.json 2>&1`. Before the alias check this reproduced the same
    `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` on a head
    that had already fixed the plain-stdout case."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    baseline_path = root / kit_doctor.MANIFEST_NAME
    script = ENGINE_DIR / "kit_doctor.py"
    with baseline_path.open("w", encoding="utf-8") as redirected_stdout:
        result = subprocess.run(
            [sys.executable, str(script), "--record-install", "--root", str(root)],
            stdout=redirected_stdout,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    assert result.returncode == 0
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert "scripts/check_doc_budget.py" in baseline["files"]


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
    class Done:
        returncode = 0
        stdout = "b" * 64 + "\n"

    monkeypatch.setattr(kit_doctor.subprocess, "run", lambda *a, **k: Done())
    assert kit_doctor._git_head(tmp_path) == "b" * 64


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


def test_an_unreadable_source_manifest_refuses_rather_than_recording_everything(
    tmp_path, capsys, monkeypatch
):
    """Falling back to the permissive mode here would silently re-open the
    retained-file hole: the check that keeps an adopter's own file out of the
    baseline is exactly the one that needs this manifest."""
    root = _fake_repo(tmp_path)
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / ".git").mkdir()
    _write(kit / "kit-manifest.json", "{ not json")
    monkeypatch.setattr(kit_doctor, "_git_head", lambda p: "c" * 40)
    code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
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
    _write(root / "kit-manifest.json", json.dumps(release))
    before = (root / "kit-manifest.json").read_text()
    code = kit_doctor.main(["--record-install", "--root", str(root)])
    assert code == 2
    assert "not written by --record-install" in capsys.readouterr().err
    assert (root / "kit-manifest.json").read_text() == before, "refused, and wrote nothing"


def test_the_refusal_does_not_depend_on_required_by_existing(tmp_path, capsys):
    """The guard's first version needed a `required_by` edge to recognise a
    release manifest — but that is an emergent fact about today's import graph
    (most files have no dependent), not something `generate_manifest`
    guarantees. Stripping those keys — which a kit losing its last shared
    library would do on its own — made the guard silently stop firing and
    reproduced the original destructive overwrite at exit 0 (panel, adversarial
    lens).

    A guard resting on an incidental property of the current codebase is not a
    guard, so the signal is now the one thing that is exact: `--record-install`
    always writes `kit_commit`, `generate_manifest` never does."""
    root = _fake_repo(tmp_path)
    release = kit_doctor.generate_manifest(REPO_ROOT, 2)
    for entry in release["files"].values():
        entry.pop("required_by", None)
    assert not any(e.get("required_by") for e in release["files"].values())
    _write(root / "kit-manifest.json", json.dumps(release))
    before = (root / "kit-manifest.json").read_text()
    assert kit_doctor.main(["--record-install", "--root", str(root)]) == 2
    assert "not written by --record-install" in capsys.readouterr().err
    assert (root / "kit-manifest.json").read_text() == before


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


def test_a_partial_record_exits_nonzero_and_names_what_it_left_out(tmp_path, capsys, monkeypatch):
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
    monkeypatch.setattr(kit_doctor, "_git_head", lambda p: "d" * 40)
    code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
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


@pytest.mark.parametrize("body", ['["a", "list"]', '"a string"', "null", '{"files": ["oops"]}'])
def test_a_structurally_malformed_source_manifest_degrades_rather_than_tracebacking(
    tmp_path, capsys, monkeypatch, body
):
    """Syntactically valid JSON of the wrong SHAPE at `--from-kit`. The read was
    guarded for JSONDecodeError/OSError but not for "parsed fine, isn't a dict",
    so `.get` raised AttributeError and escaped — the one malformed-input path
    in this file that tracebacked instead of degrading, in code this PR adds
    (CodeRabbit, PR #278).

    The safe degrade is an empty source: it matches nothing, so every present
    file lands in `unverified` and none is blessed as kit-installed."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "installed")
    kit = tmp_path / "kit"
    (kit / ".git").mkdir(parents=True)
    _write(kit / "kit-manifest.json", body)
    monkeypatch.setattr(kit_doctor, "_git_head", lambda p: "e" * 40)
    code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
    assert code == 1, "nothing could be verified, so the record is partial"
    assert "scripts/check_doc_budget.py" in capsys.readouterr().err
    recorded = json.loads((root / "kit-manifest.json").read_text())
    assert recorded["files"] == {}, "nothing may be recorded as installed from an unusable source"


@pytest.mark.parametrize(
    "trusted,commit,differ,expect",
    [
        (True, "a" * 40, True, "installed from kit aaaaaaaaaaaa"),
        (True, "a" * 40, False, "installed from kit aaaaaaaaaaaa"),
        (True, None, True, "recorded, install provenance unknown"),
        (True, None, False, "recorded, install provenance unknown"),
        (False, None, True, "none recorded"),
        (False, None, False, "none recorded"),
    ],
)
def test_the_baseline_line_is_emitted_in_every_combination(
    tmp_path, capsys, trusted, commit, differ, expect
):
    """Both skill docs tell the operator to read this line to confirm
    `--record-install` ran, phrased as a two-way check. Two combinations printed
    NOTHING — untrusted with zero mismatches, and trusted-without-provenance
    with zero mismatches — so the documented check had a silent third outcome,
    in exactly the case someone runs it (a clean install). And no test asserted
    on the line at all: deleting the whole render block left the suite green
    (panel, correctness lens)."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "on disk")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    ships = _sha("kit") if differ else _sha("on disk")
    baseline = (
        _baseline({rel: _sha("on disk")}, kit_commit=commit)
        if trusted
        else _manifest({rel: _sha("on disk")})
    )
    print(kit_doctor.render(kit_doctor.inspect(root, _manifest({rel: ships}), config, baseline)))
    out = capsys.readouterr().out
    line = [ln for ln in out.splitlines() if ln.startswith("  baseline:")]
    assert line, "the documented signal must never be silently absent"
    assert expect in line[0]


def test_a_self_comparison_run_does_not_claim_the_kit_is_unchanged(tmp_path, capsys):
    """The bare invocation resolves baseline and comparison to the same file, so
    `recorded == expected` holds by construction and every mismatch is
    `locally-edited` — which is CORRECT, since the baseline is what you
    installed. What is not correct is the label's second clause, "and the kit's
    version is unchanged": this run has no upstream in it at all and knows
    nothing about the kit's copy (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "edited after recording")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    same = _baseline({rel: _sha("as recorded")}, kit_commit="b" * 40)
    report = kit_doctor.inspect(root, same, config, same, baseline_is_comparison=True)
    assert next(f for f in report.files if f.path == rel).state == "locally-edited"
    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    assert "changed here since it was recorded" in out
    assert "the kit's version is unchanged" not in out, "no upstream was consulted"
    assert "compared against ITSELF" in out


def test_an_upstream_comparison_still_claims_the_kit_is_unchanged(tmp_path, capsys):
    """The discriminating half: when a real upstream manifest IS supplied, the
    stronger claim is earned and must still be made."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "edited")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root,
        _manifest({rel: _sha("kit")}),
        config,
        _baseline({rel: _sha("kit")}, kit_commit="c" * 40),
    )
    assert next(f for f in report.files if f.path == rel).state == "locally-edited"
    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    assert "the kit's version is unchanged" in out
    assert "compared against ITSELF" not in out


def _recorded_adopter(tmp_path: Path) -> tuple[Path, str]:
    """An adopter with a real recorded baseline on disk, via the CLI."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "installed")
    assert kit_doctor.main(["--record-install", "--root", str(root)]) == 0
    return root, rel


def test_main_derives_self_comparison_from_the_resolved_paths(tmp_path, capsys):
    """`main`'s `baseline_path.resolve() == manifest_path.resolve()` was the real
    signal and nothing exercised it: every test hand-passed the boolean to
    `inspect`, so hardcoding the line to False left the suite green — found
    independently by BOTH lenses (panel round 5).

    Drives the bare CLI, which is the invocation the module docstring lists
    first."""
    root, rel = _recorded_adopter(tmp_path)
    _write(root / rel, "edited after recording")
    assert kit_doctor.main(["--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "compared against ITSELF" in out
    assert "changed here since it was recorded" in out
    assert "the kit's version is unchanged" not in out


def test_main_does_not_claim_self_comparison_against_a_separate_manifest(tmp_path, capsys):
    """The discriminating half, also through the CLI: a real upstream manifest
    at a different path must NOT be reported as a self-comparison."""
    root, rel = _recorded_adopter(tmp_path)
    _write(root / rel, "edited after recording")
    upstream = tmp_path / "kit" / "kit-manifest.json"
    _write(upstream, json.dumps(_manifest({rel: _sha("what the kit ships")})))
    assert kit_doctor.main(["--root", str(root), "--manifest", str(upstream)]) == 1
    out = capsys.readouterr().out
    assert "compared against ITSELF" not in out
    assert "STALE **and** LOCALLY EDITED" in out


def test_main_sees_through_a_symlinked_manifest_path(tmp_path, capsys):
    """`resolve()` follows symlinks, so the same file reached by two names is
    still one document. Pins the resolution, not just the equality.

    The symlink is on `--manifest`; `--baseline` is left to default. The
    comparison is symmetric, so this exercises the same resolution either way —
    but the name said `baseline` and the body passed `--manifest`, which is the
    name-promises-more shape this file exists to catch (panel round 6)."""
    root, rel = _recorded_adopter(tmp_path)
    _write(root / rel, "edited")
    link = tmp_path / "alias.json"
    link.symlink_to(root / "kit-manifest.json")
    assert kit_doctor.main(["--root", str(root), "--manifest", str(link)]) == 1
    assert "compared against ITSELF" in capsys.readouterr().out


def test_self_comparison_is_dropped_when_the_two_documents_actually_differ(tmp_path):
    """`inspect` verifies the caller's assertion instead of believing it. Called
    with `baseline_is_comparison=True` but genuinely different documents, the
    report used to say "no upstream was consulted" in the summary and "changed
    upstream" one line below (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "on disk")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root,
        _manifest({rel: _sha("upstream")}),
        config,
        _baseline({rel: _sha("recorded")}, kit_commit="f" * 40),
        baseline_is_comparison=True,
    )
    assert not report.baseline_is_comparison, "the claim contradicted the documents"
    assert next(f for f in report.files if f.path == rel).state == "stale-and-edited"


def test_an_untrusted_self_comparison_is_not_reported_as_one(tmp_path):
    """The `and trusted` half, which was also unpinned: a bare run in a repo
    whose only manifest is a release manifest consulted no baseline for a cause,
    so "compared against itself" describes nothing that happened. Only visible
    in --json, where the two fields would otherwise contradict each other."""
    root = _fake_repo(tmp_path)
    rel = "scripts/check_doc_budget.py"
    _write(root / rel, "on disk")
    release = _manifest({rel: _sha("on disk")})  # no kit_commit
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, release, config, release, baseline_is_comparison=True)
    assert not report.baseline_trusted
    assert not report.baseline_is_comparison, "a field pair that must never contradict"


@pytest.mark.parametrize(
    "body",
    [
        '{"kit_version": 2}',  # dict, no files key
        '{"kit_version": 2, "files": null}',  # explicit null
        '{"kit_version": 2, "files": ["a"]}',  # present but not a dict
        '{"kit_version": 2, "files": "nope"}',
        '["a", "list"]',  # top level not a dict at all
        '"a string"',
        "null",
    ],
)
def test_from_kit_never_falls_back_to_recording_everything(tmp_path, capsys, monkeypatch, body):
    """`--from-kit` means "these came from that kit" and must be CHECKED. The
    check reads the source manifest's `files`; downstream, `None` is the
    sentinel for "no --from-kit given", which turns verification off.

    **Exactly two of the seven bodies below reproduced that**, and the other
    five were already safe by TWO DIFFERENT routes — worth separating, because
    an earlier version of this docstring credited one route for all five:

    - `{"kit_version": 2}` and `"files": null` yield None. These were the bug.
    - `"files": ["a"]` / `"files": "nope"` pass that list or string straight
      through, and `record_install_manifest`'s own `isinstance(source_files,
      dict)` refuses it.
    - A non-dict TOP level never calls `.get` at all: the pre-fix line's own
      `else {}` had already produced a real empty dict, so the check above
      trivially passes and safety comes from the per-key lookup finding nothing.

    They are parametrized together anyway, as a boundary: the fix normalizes all
    seven to `{}`, and the five that were already safe are what keeps a future
    edit from re-splitting them. But the coverage claim is "two reproduce, five
    bound them", not "every shape reaches the sentinel" — an earlier version of
    this docstring said the latter, which is the same overstated-coverage class
    that let the bug survive four rounds in the first place (panel, both lenses
    converged on it)."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "the adopter's own file, never installed")
    kit = tmp_path / "kit"
    (kit / ".git").mkdir(parents=True)
    _write(kit / "kit-manifest.json", body)
    monkeypatch.setattr(kit_doctor, "_git_head", lambda p: "a" * 40)
    code = kit_doctor.main(["--record-install", "--root", str(root), "--from-kit", str(kit)])
    recorded = json.loads((root / "kit-manifest.json").read_text())
    assert recorded["files"] == {}, "an unusable source must bless nothing"
    assert code == 1, "and the partial record must not report success"
    assert "scripts/check_doc_budget.py" in capsys.readouterr().err


# --- #285: the Usage block hardcoded `scripts/kit_doctor.py`, so every printed
# example failed the moment an adopter vendored engines anywhere else (which
# `paths.engines` exists to allow, and which docs/agentic-dev-kit/
# adopting-into-a-linted-repo.md recommends). Fixed by writing
# `<engine-dir>/kit_doctor.py` the way every workflow doc already does.
#
# `re.escape` even though KIT_ENGINE_PREFIX has no regex metacharacters today
# — reading it from kit_doctor rather than writing "scripts" here means this
# regex tracks the constant if it ever changes, instead of silently checking a
# prefix the kit no longer uses.
_BARE_ENGINE_PATH_RE = re.compile(
    r"^\s*(?:#\s*)?(?:uv run\s+|python3?\s+|bash\s+|sh\s+)?"
    rf"{re.escape(kit_doctor.KIT_ENGINE_PREFIX)}/\S+\.(?:py|sh)\b(?!:)"
)


def _bare_engine_path_lines(text: str) -> list[str]:
    """Lines that hardcode `<KIT_ENGINE_PREFIX>/<name>.py` (or `.sh`) as if
    that were the only place an adopter could have it installed — #285's bug
    class, generalized past the one file it was found in.

    Anchored to catch a command example (with or without a runner keyword,
    with or without a leading `#`) while leaving incidental prose alone:

    - The `scripts/...` token must OPEN the line (after stripping a comment
      marker and an optional runner word). "... while `bash scripts/foo.sh`
      dies on its ``source`` line" does not open its line, so a past-tense bug
      account is never mistaken for an instruction to run something —
      `kit_doctor.py` itself has two of these, describing #228 and #41.
    - A colon immediately after the extension is excluded:
      `scripts/pr_watch.py:summarize_checks` (a cross-reference to a specific
      function, in `dev_session.sh`) and `scripts/kit_doctor.py:101` (a line
      citation, in a handoff doc) name a location in the kit's OWN tree for a
      reader already there — correct regardless of where the file is later
      vendored, unlike a copy-paste command.

    Deliberately NOT special-cased: KIT_OWNED's own `("scripts/…", role)`
    tuple entries. They never match anyway — a line opening with `(` cannot
    match a pattern anchored on `scripts/` — so the one place a literal
    `scripts/` prefix is correct (the layout `_remap` reads) needs no carve-out.
    """
    return [line.strip() for line in text.splitlines() if _BARE_ENGINE_PATH_RE.match(line)]


@pytest.mark.parametrize(
    "line",
    [
        "    as an ordinary `missing` while `bash scripts/dev_session.sh` dies on its",
        "# `bash scripts/dev_session.sh` died on line 63. The Python-only version",
        "See `scripts/kit_doctor.py:101` for the signal.",
        "    # scripts/pr_watch.py:summarize_checks (the other cockpit CI surface)",
        '    ("scripts/pr_watch.py", "engine"),',
    ],
)
def test_the_detector_leaves_layout_specific_prose_alone(line):
    """The two carve-outs `_bare_engine_path_lines` documents, each pinned to
    the real line shape that motivated it (kit_doctor.py's own #228/#41 prose,
    a handoff-doc line citation, dev_session.sh's cross-reference to a
    `pr_watch.py` function, and a KIT_OWNED tuple entry)."""
    assert _bare_engine_path_lines(line) == []


@pytest.mark.parametrize(
    "line",
    [
        "    uv run scripts/kit_doctor.py --json             # machine-readable",
        "    python3 scripts/check_doc_budget.py            # report every tracked doc",
        "#   scripts/dev_session.sh list [--watch [interval]]",
    ],
)
def test_the_detector_catches_every_shape_the_kit_actually_used(line):
    """The three shapes #285's sweep actually found: a `uv run` Python
    example, a `python3` example, and a shell script's bare comment-block
    usage line with no runner keyword at all."""
    assert _bare_engine_path_lines(line) == [line.strip()]


def test_kit_doctor_source_has_no_hardcoded_engine_prefix():
    """Scans the file's own source text, not just the docstring's Usage
    block: #285 named two more candidates for the same literal — the
    `--help` text and the `hint:` lines in `main()` — and a whole-file scan
    catches any of the three without needing to know which one moved.

    Reached through `ENGINE_DIR`, not `REPO_ROOT / "scripts"` (#534). A test
    that exists to forbid a hardcoded `scripts/` engine prefix cannot hardcode
    the engine prefix to find the file it scans — under
    `paths.engines: scripts/devkit` it read a path that does not exist, so the
    one guard against this literal was the one guard that could not run in the
    layout it protects. The sibling at `ENGINE_DIR / "kit_doctor.py"` above had
    it right already."""
    text = (ENGINE_DIR / "kit_doctor.py").read_text(encoding="utf-8")
    assert _bare_engine_path_lines(text) == []


def test_help_output_has_no_hardcoded_engine_prefix(capsys):
    """The rendered `--help` text is argparse's own composition of
    `description` and each flag's `help=` — not the module docstring, so the
    source-text scan above cannot see it. Run for real rather than inferred:
    a static check of the `help=` string literals would miss a value built by
    string concatenation or an f-string."""
    with pytest.raises(SystemExit) as exc:
        kit_doctor.main(["--help"])
    assert exc.value.code == 0
    assert _bare_engine_path_lines(capsys.readouterr().out) == []


# Pre-existing instances of the SAME bug, in kit-owned engines #285 did not
# scope its fix to. Found while building the general test below — that test
# is what the issue calls "the only form that stops the next copied line", and
# proving it actually catches something is what surfaced these. Each is a
# Usage-block command example exactly like kit_doctor.py's former five lines,
# now hardcoding `scripts/<name>` in a file this fix's footprint does not
# cover; they need their own follow-up rather than a silent fix here.
#
# Pinned by EXACT line text rather than skipped, so the test keeps two
# properties: a NEW hardcoded line anywhere in any kit-owned file still fails
# immediately (the found set stops matching this one), and fixing one of
# these seven files ALSO fails immediately (same reason) — which is the
# prompt to delete that entry, not a false alarm. See
# `test_shipped_manifest_required_by_matches_a_fresh_derivation` above for the
# same self-obsoleting shape.
_KNOWN_PRE_EXISTING_HARDCODED_ENGINE_PATHS: dict[str, list[str]] = {
    "scripts/pr_watch.py": [
        r"uv run scripts/pr_watch.py                 # current branch's PR, human summary",
        r"uv run scripts/pr_watch.py 916 --json       # explicit PR, machine-readable",
        r"uv run scripts/pr_watch.py --mark-seen      # ack exactly what the last poll reported",
        r'uv run scripts/pr_watch.py 916 --record-review "fallback:codex" --head <polled-sha>',
        r"uv run scripts/pr_watch.py 916 --assert-draft  # correct a drifted draft bit after `gh pr create --draft`",
        r"uv run scripts/pr_watch.py 916 --assert-ready  # correct after ready creation/transition, and before merge",
    ],
    "scripts/check_doc_budget.py": [
        r"python3 scripts/check_doc_budget.py            # report every tracked doc",
        r"python3 scripts/check_doc_budget.py --quiet     # print only when over budget",
        r"python3 scripts/check_doc_budget.py --strict    # exit 1 when over budget",
        r"python3 scripts/check_doc_budget.py --json       # machine-readable",
    ],
    "scripts/archive_plan_sessions.py": [
        r"uv run scripts/archive_plan_sessions.py                  # keep 6, apply",
        r"uv run scripts/archive_plan_sessions.py --keep 5",
        r"uv run scripts/archive_plan_sessions.py --target-lines <budget>  # sweep to a line budget",
        r"uv run scripts/archive_plan_sessions.py --dry-run         # report only",
        r"uv run scripts/archive_plan_sessions.py --plan docs/handoff.md --history docs/handoff-history.md",
    ],
    "scripts/panel_prompt.py": [
        r"uv run scripts/panel_prompt.py --lens adversarial --head <sha>",
        r"uv run scripts/panel_prompt.py --lens correctness --head <sha> \\",
    ],
    "scripts/check_memory_budget.py": [
        r"python3 scripts/check_memory_budget.py            # report",
        r"python3 scripts/check_memory_budget.py --quiet     # print only when over budget (the hook)",
        r"python3 scripts/check_memory_budget.py --strict    # exit 1 when over budget",
        r"python3 scripts/check_memory_budget.py --json       # machine-readable",
    ],
    "scripts/dev_session.sh": [
        r"#   scripts/dev_session.sh new <scope> [--base <protected>] [--prefix <configured>]"
        r" [--branch <full>] [--merge-class self|operator] [--force] [--headless]"
        r" [--runtime <name>] [--launcher <command>]",
        r"#   scripts/dev_session.sh list [--watch [interval]]",
        r"#   scripts/dev_session.sh path <scope>",
        r"#   scripts/dev_session.sh pr-watch <scope> [pr-watch options]",
        r"#   scripts/dev_session.sh merge <scope>",
        r"#   scripts/dev_session.sh rm <scope> [--force] [--keep-branch]",
        r"#   scripts/dev_session.sh print-contract",
    ],
    "scripts/reconcile_sessions.sh": [
        r"#   scripts/reconcile_sessions.sh <scope|branch> [...] [--prefix <configured>] [--base <configured>]",
        r"#   scripts/reconcile_sessions.sh --match '<glob>' [--match '<glob>'] ...",
        r"#   scripts/reconcile_sessions.sh                      # discover in-flight lanes",
    ],
}


def test_no_shipped_kit_owned_file_hardcodes_a_bare_engine_path():
    """#285's general form: the invariant its fix restored for
    `kit_doctor.py` alone must hold across every file in `KIT_OWNED` — the
    manifest-tracked, `/upgrade`-refreshed population `kit_doctor.py` itself
    treats as "the kit" — and keep holding.

    **Scope, precisely, because "kit-wide" overstates it.** `KIT_OWNED` is
    engines, hooks and the shared `docs/agentic-dev-kit/` workflow/doctrine
    docs — NOT `.claude/commands/*.md` or `.agents/skills/*/SKILL.md`, which
    are runtime-specific bindings this test never reads. Found by the panel's
    adversarial lens on this PR: two files there (`triage-friction-log.md`,
    `post-merge-systemize.md`) already carry the identical hardcoded-`scripts/`
    shape, naming engines that don't exist yet (#6, #7) — so nothing breaks
    today, but nothing here would catch it if one of those files' scripts
    landed, or if a currently-clean command/skill doc regressed. That gap is
    real and is not this test's job to close; it needs its own coverage.

    `kit_doctor.py` is deliberately ABSENT from
    `_KNOWN_PRE_EXISTING_HARDCODED_ENGINE_PATHS`: this file's fix must hold
    with no exception, which an entry here would quietly grant it.
    """
    found = {
        rel: _bare_engine_path_lines((REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace"))
        for rel, _role in kit_doctor.KIT_OWNED
        if (REPO_ROOT / rel).is_file()
    }
    found = {rel: lines for rel, lines in found.items() if lines}
    assert found == _KNOWN_PRE_EXISTING_HARDCODED_ENGINE_PATHS, (
        "a kit-owned file's set of hardcoded-`scripts/`-path lines changed since "
        "this test was written. If this is a NEW violation: fix it — write "
        "`<engine-dir>/<name>` the way every workflow doc does (see "
        "kit_doctor.py's own Usage block), or render it from paths.engines at "
        "run time. If a KNOWN one from "
        "_KNOWN_PRE_EXISTING_HARDCODED_ENGINE_PATHS was just fixed: delete its "
        "entry above — do not widen the pin to make this pass."
    )


# --- the declared install set (#286) ----------------------------------------
#
# `missing` answered two questions with one number: "deliberately sized down"
# and "broken" were reported in the same words, forever. The cost was not the
# ambiguity itself but its permanence — an adopter with 21 deliberate omissions
# read the same line every run, and a deletion moving it to 25 said nothing.
#
# The split is DERIVED, not declared: `--record-install` already walks every
# kit-owned path and already knows which were absent. Recording that is the
# whole mechanism. These tests pin the three absent states it produces, the
# two ways it must refuse to apply (no key, no trust), and — the property that
# makes it worth having — that a deletion is now audible.


def _scoped_baseline(
    installed: dict[str, str],
    *,
    unrecorded: tuple[str, ...] = (),
    kit_commit: str = "d3faafb",
) -> dict:
    """A baseline carrying `not_installed`, derived from the real KIT_OWNED.

    `installed` maps a kit-layout path to its recorded sha. `unrecorded` names
    paths left out of BOTH maps, which is how a file the kit gained after this
    baseline was written looks from here — the case no declared set can
    anticipate and the reason `new-upstream` exists.
    """
    every = {rel for rel, _role in kit_doctor.KIT_OWNED}
    absent = sorted(every - set(installed) - set(unrecorded))
    return {
        "kit_version": 2,
        "kit_commit": kit_commit,
        "files": {p: {"sha256": h, "role": "engine"} for p, h in installed.items()},
        "not_installed": absent,
    }


def _states(report) -> dict[str, str]:
    return {f.path: f.state for f in report.files}


def _inspect(root, manifest_entries, baseline):
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    return kit_doctor.inspect(root, _manifest(manifest_entries), config, baseline)


ENGINE = "scripts/check_doc_budget.py"


def test_record_install_records_what_was_absent_not_only_what_was_there(tmp_path):
    """The declared set is a by-product of a walk `--record-install` already
    does. Before #286 the absent branch was a bare `continue`."""
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    written, unverified = kit_doctor.record_install_manifest(root, config, 2, "abc123")

    assert unverified == []
    assert set(written["files"]) == {ENGINE}
    every = {rel for rel, _role in kit_doctor.KIT_OWNED}
    # Derived from KIT_OWNED rather than listed: a new kit file must not fail
    # this test, whose property is only that the two maps partition the set.
    assert set(written["not_installed"]) == every - {ENGINE}
    assert set(written["files"]).isdisjoint(written["not_installed"])


def test_a_present_but_unverified_file_is_not_recorded_as_not_installed(tmp_path):
    """`--from-kit` drops a file that does not match the source kit — it is
    UNJUDGEABLE, not absent. Calling it "not installed" would be a plain
    falsehood, and would later read as a deliberate omission of a file that is
    sitting right there.
    """
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    # The adopter's own pre-existing file at a kit-owned path: present, and not
    # what the kit ships.
    written, unverified = kit_doctor.record_install_manifest(
        root, config, 2, "abc123", source_files={ENGINE: {"sha256": _sha("something else")}}
    )

    assert unverified == [ENGINE]
    assert ENGINE not in written["files"]
    # Not merely absent from the list — the whole key is suppressed, because an
    # unverified path makes the record partial. That stronger property, and the
    # misclassification it prevents, are pinned by
    # `test_an_unverified_path_suppresses_the_declared_set_entirely` and
    # `test_a_deleted_unverified_path_is_not_reported_as_a_new_kit_file`. Here
    # the point is only that a file sitting on disk is never called "not
    # installed", which holds under either shape.
    assert ENGINE not in written.get("not_installed", []), (
        "a file that is present on disk was recorded as not installed"
    )


def test_an_absence_the_baseline_declared_is_not_a_finding(tmp_path):
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, baseline)

    assert report.declared_scope_known
    assert _states(report)["scripts/pr_watch.py"] == "declined"
    assert report.broken == []
    assert [f.path for f in report.files if f.state == "missing"] == [], (
        "an absence stayed ambiguous while a declared set was available"
    )


def test_a_file_the_baseline_recorded_as_installed_and_is_now_gone_is_a_finding(tmp_path):
    """#286's actual bug, stated as a test: under one undifferentiated count,
    deleting an installed engine moved a number nobody reads."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    target.unlink()

    report = _inspect(root, {ENGINE: recorded}, baseline)
    status = _states(report)[ENGINE]
    assert status == "removed", status
    assert [f.path for f in report.broken] == [ENGINE]


def test_a_file_the_kit_added_after_the_baseline_is_neither_declined_nor_broken(tmp_path):
    """The case no declared set can contain, and the one that is live in the
    kit's own adopter today: a path in neither map is one the operator was
    never offered."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    newcomer = "docs/templates/CLAUDE.md.tmpl"
    baseline = _scoped_baseline(
        {ENGINE: kit_doctor.sha256_of(target)}, unrecorded=(newcomer,)
    )

    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, baseline)
    assert _states(report)[newcomer] == "new-upstream"
    assert [f.path for f in report.new_upstream] == [newcomer]
    assert report.broken == [], "a file that was never offered was called broken"


def test_runtime_parity_contract_is_tracked_and_new_to_an_older_baseline(tmp_path):
    runtime_parity = "docs/agentic-dev-kit/runtime-parity.md"
    assert dict(kit_doctor.KIT_OWNED).get(runtime_parity) == "doctrine"
    root = _fake_repo(tmp_path)
    engine_hash = kit_doctor.sha256_of(root / ENGINE)
    baseline = _scoped_baseline(
        {ENGINE: engine_hash},
        unrecorded=(runtime_parity,),
    )

    report = _inspect(
        root,
        {ENGINE: engine_hash, runtime_parity: "newer-doctrine"},
        baseline,
    )

    assert _states(report)[runtime_parity] == "new-upstream"
    assert runtime_parity in [status.path for status in report.new_upstream]


def test_a_baseline_without_the_key_gets_the_old_report_not_an_inferred_one(tmp_path):
    """Every baseline written before #286 lacks `not_installed`. Inferring
    "declined" from its silence would assert an intent nobody expressed — and
    would swallow `new-upstream`, which is absent from a pre-#286 baseline in
    exactly the same way."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    legacy = _baseline({ENGINE: kit_doctor.sha256_of(target)}, kit_commit="d3faafb")
    assert "not_installed" not in legacy

    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, legacy)
    assert report.baseline_trusted, "fixture is confounded: the trust gate, not the key, applied"
    assert not report.declared_scope_known
    assert _states(report)["scripts/pr_watch.py"] == "missing"
    assert report.declined == [] and report.new_upstream == []


def test_an_untrusted_baseline_carrying_the_key_still_cannot_declare_scope(tmp_path):
    """`declined` is a claim about what happened after the baseline was
    written, so it needs the same trust `locally-edited` needs. A hand-written
    `not_installed` in a manifest no kit recorded must not silence anything."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    forged = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    del forged["kit_commit"]

    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, forged)
    assert not report.declared_scope_known
    assert _states(report)["scripts/pr_watch.py"] == "missing"


@pytest.mark.parametrize(
    "value", [None, "scripts/pr_watch.py", {"scripts/pr_watch.py": True}, 7]
)
def test_a_malformed_declared_set_degrades_instead_of_aborting_the_report(tmp_path, value):
    """Same degrade-don't-abort rule the `files` handling follows: this is a
    read-only diagnostic, and a malformed key in one axis must not take the
    whole report down. A truthy non-list is the hazard — `or []` passes it
    through and `in` then means something else entirely."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    baseline["not_installed"] = value

    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, baseline)
    assert not report.declared_scope_known
    assert _states(report)["scripts/pr_watch.py"] == "missing"


def test_a_declared_absence_an_installed_engine_needs_is_still_broken(tmp_path):
    """A path recorded as declined AND required by something installed is a
    contradiction. The safe reading of a contradiction is the loud one."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    lib = "scripts/lib/kitconfig.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    assert lib in baseline["not_installed"], "fixture is confounded: the lib was not declined"

    manifest = _manifest({ENGINE: kit_doctor.sha256_of(target), lib: None})
    manifest["files"][lib]["required_by"] = [ENGINE]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config, baseline)

    assert _states(report)[lib] == "missing-required"
    assert [f.path for f in report.broken] == [lib]


def test_a_dependency_the_kit_gained_after_this_baseline_is_never_offered_not_broken(
    tmp_path, capsys
):
    """#661's reproduction, in the shape the adopter hit it. The dependent is
    installed and STALE — exactly what it hashes to in that repo's own baseline,
    and not what the kit now ships — and the kit gained the library it imports
    after the baseline was written, so the baseline mentions it in neither map.

    The old filter read the stale dependent as agreement with the current import
    graph and printed the hard verdict, directly above the `/upgrade` line that
    is the real remedy. Both halves are pinned: the state, and the words an
    operator actually reads.
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    lib = "scripts/lib/kitconfig.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)}, unrecorded=(lib,))
    assert lib not in baseline["not_installed"], "fixture is confounded: the lib was declined"

    # The kit has moved the dependent on since this baseline; the library is one
    # the moved version imports and the installed version does not.
    manifest = _manifest({ENGINE: _sha("the kit's newer engine"), lib: None})
    manifest["files"][lib]["required_by"] = [ENGINE]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config, baseline)

    assert _states(report)[lib] == "new-upstream"
    assert report.broken == []
    assert [f.path for f in report.new_upstream] == [lib]
    # The dependent is not excused: it is stale against the kit and says so.
    assert _states(report)[ENGINE] == "stale"

    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    assert "this install is broken, not sized down" not in out
    assert "✓ intact for this adoption" in out or "⚠ intact for this adoption" in out
    assert "Run /upgrade to accept or decline them." in out


def test_dropping_a_version_gap_edge_still_reports_a_deletion(tmp_path):
    """The narrowing must not buy silence anywhere it applies. Same stale
    dependent as above, but this baseline records the library AS installed — so
    the absence is a deletion, and the fall-through the dropped edge exposes is
    what has to say so. `missing-required` is checked FIRST, ahead of the
    declared set, so dropping it is exactly where a real finding could be lost.
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    lib = "scripts/lib/kitconfig.py"
    baseline = _scoped_baseline(
        {ENGINE: kit_doctor.sha256_of(target), lib: _sha("the library, when it was installed")}
    )
    manifest = _manifest({ENGINE: _sha("the kit's newer engine"), lib: None})
    manifest["files"][lib]["required_by"] = [ENGINE]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, manifest, config, baseline)

    assert _states(report)[lib] == "removed"
    assert [f.path for f in report.broken] == [lib]


def test_a_deletion_changes_the_exit_code_a_declined_file_does_not(tmp_path):
    """The pair that makes the split worth having, and the reason it is a
    controlled comparison rather than two scenarios: BOTH trees are missing the
    same file, from the same fixture. The ONLY difference is what the baseline
    recorded about it — installed, or never installed. Before #286 both exited
    0, because nothing distinguished them."""

    def run(*, was_installed: bool) -> int:
        root = _fake_repo(tmp_path / ("gone" if was_installed else "declined"))
        target = root / "scripts" / "check_doc_budget.py"
        recorded = kit_doctor.sha256_of(target)
        baseline = (
            _scoped_baseline({ENGINE: recorded}) if was_installed else _scoped_baseline({})
        )
        target.unlink()
        (root / "kit-manifest.json").write_text(
            json.dumps(_manifest({ENGINE: recorded})), encoding="utf-8"
        )
        (root / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
        return kit_doctor.main(
            [
                "--root",
                str(root),
                "--manifest",
                str(root / "kit-manifest.json"),
                "--baseline",
                str(root / "baseline.json"),
            ]
        )

    assert run(was_installed=True) == 1, "a deleted engine exited green"
    assert run(was_installed=False) == 0, "a deliberately sized-down adoption failed its own gate"


def test_the_report_says_intact_and_stops_repeating_the_count(tmp_path, capsys):
    """The line #286 asked for. The declined files must NOT be itemised — a
    per-file list of 21 deliberate omissions is the noise being removed."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, baseline)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    line = next(ln for ln in out.splitlines() if ln.startswith("  files:"))
    assert line == "  files: 1 unchanged, 0 differ, 0 missing, 0 unknown"
    assert f"✓ intact for this adoption — {len(kit_doctor.KIT_OWNED) - 1} file(s) declined" in out
    assert "sized-down adoption, or incomplete" not in out
    assert "scripts/pr_watch.py" not in out, "declined files were itemised"


def test_the_report_names_new_upstream_files_and_does_not_count_them_missing(tmp_path, capsys):
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    newcomer = "docs/templates/CLAUDE.md.tmpl"
    baseline = _scoped_baseline(
        {ENGINE: kit_doctor.sha256_of(target)}, unrecorded=(newcomer,)
    )
    print(kit_doctor.render(_inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, baseline)))
    out = capsys.readouterr().out

    line = next(ln for ln in out.splitlines() if ln.startswith("  files:"))
    assert line == "  files: 1 unchanged, 0 differ, 0 missing, 0 unknown"
    assert "1 file(s) this baseline does not mention either way" in out
    # Named, because "which" is always the next question.
    assert newcomer in out
    assert "/upgrade" in out


def test_a_legacy_baseline_is_told_what_would_split_its_count(tmp_path, capsys):
    """The nudge is the whole migration path for existing adopters, so it must
    appear — and name the command."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    legacy = _baseline({ENGINE: kit_doctor.sha256_of(target)}, kit_commit="d3faafb")
    print(kit_doctor.render(_inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, legacy)))
    out = capsys.readouterr().out

    assert "declares no install set" in out
    assert "Commonly it predates the declared" in out
    assert "--record-install" in out
    assert "intact for this adoption" not in out, (
        "a report that cannot judge scope claimed the install was intact"
    )


def test_a_full_install_with_nothing_declined_does_not_carry_the_nudge(tmp_path, capsys):
    """The nudge is gated on there being an ambiguous absence to explain.
    Reproducing #286's own noise in the fix's advice line would be its own
    joke."""
    root = _fake_repo(tmp_path)
    every = {rel for rel, _role in kit_doctor.KIT_OWNED}
    for rel in every - {ENGINE}:
        _write(root / rel, f"content of {rel}\n")
    installed = {rel: kit_doctor.sha256_of(root / rel) for rel in every}
    legacy = _baseline(installed, kit_commit="d3faafb")
    print(kit_doctor.render(_inspect(root, installed, legacy)))
    out = capsys.readouterr().out

    line = next(ln for ln in out.splitlines() if ln.startswith("  files:"))
    assert line == f"  files: {len(every)} unchanged, 0 differ, 0 missing, 0 unknown"
    assert "predates the declared install set" not in out


def test_json_exposes_whether_the_scope_was_judgeable(tmp_path, capsys):
    """Not derivable from `files`: a report with no absent file at all looks
    identical either way."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    (root / "kit-manifest.json").write_text(
        json.dumps(_manifest({ENGINE: kit_doctor.sha256_of(target)})), encoding="utf-8"
    )
    (root / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    kit_doctor.main(
        [
            "--root",
            str(root),
            "--json",
            "--manifest",
            str(root / "kit-manifest.json"),
            "--baseline",
            str(root / "baseline.json"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["declared_scope_known"] is True
    assert {f["state"] for f in payload["files"]} == {"unchanged", "declined"}


def test_the_not_intact_line_does_not_claim_a_provenance_it_lacks(tmp_path, capsys):
    """`broken` holds two states with DIFFERENT sources: `removed` comes from
    the baseline's record of an install, `missing-required` from the import
    graph. A file can be `missing-required` while the baseline records it as
    DECLINED — absent, needed, and on record as the opposite of installed.

    An earlier draft of the summary line read "absent that this repo has on
    record", which is false for exactly that file. Pinned because it is the
    overstatement class #54 tracks, and nothing else here would catch it: the
    per-file sections are correct, only the line above them was not.
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    lib = "scripts/lib/kitconfig.py"
    baseline = _scoped_baseline({ENGINE: kit_doctor.sha256_of(target)})
    assert lib in baseline["not_installed"], "fixture is confounded: the lib was not declined"

    manifest = _manifest({ENGINE: kit_doctor.sha256_of(target), lib: None})
    manifest["files"][lib]["required_by"] = [ENGINE]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    print(kit_doctor.render(kit_doctor.inspect(root, manifest, config, baseline)))
    out = capsys.readouterr().out

    assert "✗ NOT intact for this adoption" in out
    assert "has on record" not in out, (
        "the summary claimed a declined file was recorded as installed here"
    )
    # The accurate claim, which holds for both states in `broken`.
    assert "absent that should be installed" in out


# --- the declared set must not outlive the record's completeness (#322 review) ---


def test_an_unverified_path_suppresses_the_declared_set_entirely(tmp_path):
    """A present-but-unmatched path is in neither map BY DESIGN, so the record
    is partial and cannot carry a scope claim.

    Writing `not_installed` anyway was sound only at record time: the path is
    present, so nothing asks about it. Delete it later and `inspect` finds it
    absent and in neither map — which is the `new-upstream` signature.
    """
    root = _fake_repo(tmp_path)
    written, unverified = kit_doctor.record_install_manifest(
        root,
        kit_doctor.load_config(root / "config" / "dev-model.yaml"),
        2,
        "abc123",
        source_files={ENGINE: {"sha256": _sha("a different kit's copy")}},
    )
    assert unverified == [ENGINE], "fixture is confounded: nothing was unverified"
    assert "not_installed" not in written, (
        "a partial record claimed a complete declared install set"
    )


def test_a_deleted_unverified_path_is_not_reported_as_a_new_kit_file(tmp_path):
    """The failure the suppression above prevents, driven end to end: the
    adopter's OWN file, recorded as unjudgeable, then deleted."""
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    written, _ = kit_doctor.record_install_manifest(
        root, config, 2, "abc123", source_files={ENGINE: {"sha256": _sha("elsewhere")}}
    )
    (root / "scripts" / "check_doc_budget.py").unlink()

    report = kit_doctor.inspect(root, _manifest({ENGINE: _sha("whatever")}), config, written)
    state = _states(report)[ENGINE]
    assert state != "new-upstream", (
        "a deleted adopter-owned file was reported as a file the kit added since the baseline"
    )
    assert state == "missing", state
    assert not report.declared_scope_known


def test_a_malformed_files_map_cannot_be_read_as_a_declared_scope(tmp_path):
    """The two halves are one record. `inspect` degrades a non-dict `files` to
    `{}`, so a sound `not_installed` beside a malformed `files` would classify
    every absent-but-installed file as `declined`/`new-upstream` — the
    malformed half deciding the answer for the sound one."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    baseline["files"] = ["not", "a", "dict"]
    target.unlink()

    report = _inspect(root, {ENGINE: recorded}, baseline)
    assert not report.declared_scope_known
    # `missing`, not `declined` and not `new-upstream`: nothing is known here.
    assert _states(report)[ENGINE] == "missing"
    assert report.declined == [] and report.new_upstream == []


# --- render-layer coverage for the split (fallback panel, adversarial lens) ---
#
# The state layer was pinned; the RENDER layer was not, and that is where #286's
# own bug can reappear. `render` gates its headline verdict on `report.broken`,
# so a gate narrowed to `missing-required` alone prints "✓ intact" directly above
# an itemised deletion warning — the same "deleting engines said nothing" failure,
# one layer up. The whole suite passed under that mutation before these tests.


def test_a_deletion_alone_makes_the_report_say_NOT_intact(tmp_path, capsys):
    """`removed` with no `missing-required` anywhere — the state that reaches
    the headline verdict only through `broken`'s second member."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    target.unlink()

    report = _inspect(root, {ENGINE: recorded}, baseline)
    assert [f.state for f in report.broken] == ["removed"], (
        "fixture is confounded: something other than `removed` reached the verdict"
    )
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "✗ NOT intact for this adoption" in out
    assert "✓ intact for this adoption" not in out, (
        "the report called an adoption intact while itemising a deleted file below it"
    )
    # The itemised warning and the headline must agree — the contradiction is
    # the actual defect, so pin that both halves are present together.
    assert "deleted since" in out


def test_removed_beats_declined_when_a_baseline_lists_a_path_in_both(tmp_path):
    """The precedence the code comments call load-bearing, pinned. Only a
    hand-edited baseline reaches it — an honest `record_install_manifest` run
    partitions every path into exactly one map — but it is a documented safety
    property, and swapping the two branches passed the whole suite before this.
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    baseline["not_installed"] = sorted({*baseline["not_installed"], ENGINE})
    target.unlink()

    report = _inspect(root, {ENGINE: recorded}, baseline)
    assert ENGINE in baseline["files"] and ENGINE in baseline["not_installed"], (
        "fixture is confounded: the path is not in both maps"
    )
    assert _states(report)[ENGINE] == "removed", (
        "a contradictory baseline resolved to silence rather than to the finding"
    )
    assert [f.path for f in report.broken] == [ENGINE]


def test_an_empty_adoption_is_not_called_intact(tmp_path, capsys):
    """An install set with nothing in it has nothing to be intact. Recording a
    tree where no kit file was ever copied yields a well-formed baseline
    declining all of KIT_OWNED — which printed the same confident ✓ as a
    healthy sized-down adoption, underneath a `✗ paths.engines` line saying
    every workflow reference resolves to nothing."""
    root = tmp_path
    _write(
        root / "config" / "dev-model.yaml",
        "kit:\n  version: 2\npaths:\n  handoff: docs/handoff.md\n"
        "  friction_log: docs/friction-log.md\n  engines: scripts\n",
    )
    _write(root / "docs" / "handoff.md", "# real handoff\n")
    _write(root / "docs" / "friction-log.md", "# real inbox\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    written, unverified = kit_doctor.record_install_manifest(root, config, 2, "abc123")
    assert written["files"] == {} and unverified == [], "fixture is confounded"

    report = kit_doctor.inspect(root, _manifest({}), config, written)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "✓ intact for this adoption" not in out, (
        "a tree with nothing installed was reported as an intact adoption"
    )
    assert "nothing is installed here" in out
    assert "empty adoption rather than an intact one" in out


def test_a_removed_file_is_counted_and_named_on_the_summary_line(tmp_path, capsys):
    """The summary line's `removed` contribution, pinned. Deleting both the
    parenthetical and `n_removed`'s term in `n_absent` left the whole suite
    green: a deleted file would then read `0 missing` on the count line while
    the section below itemised it — the same headline/detail contradiction the
    intact verdict had. (Fallback panel, correctness lens.)
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    target.unlink()

    print(kit_doctor.render(_inspect(root, {ENGINE: recorded}, baseline)))
    out = capsys.readouterr().out
    line = next(ln for ln in out.splitlines() if ln.startswith("  files:"))

    # Both halves: the file is COUNTED, and the count says which kind it is.
    assert line == "  files: 0 unchanged, 0 differ, 1 missing (1 recorded as installed here), 0 unknown", line


# --- `unknown-version` is a PRESENT file (fallback panel, correctness lens r2) ---
#
# It means "this file is here and its drift cannot be judged" — an absence of
# information, not of a file. The verdict block read it as neither, so a tree
# holding only unjudgeable files reported "nothing is installed here", and a
# full install reported a bare ✓ three lines above "drift cannot be judged".


def _unjudgeable_case(tmp_path, *, also_installed: bool):
    """One present file the COMPARISON manifest has no entry for. With
    `also_installed`, a second file is present and recorded, so the tree is a
    normal install rather than an otherwise-empty one."""
    root = _fake_repo(tmp_path)
    other = "scripts/lib/kitconfig.py"
    if also_installed:
        _write(root / other, "recorded and matching\n")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    installed = {other: kit_doctor.sha256_of(root / other)} if also_installed else {}
    baseline = _scoped_baseline(installed)
    # ENGINE is present on disk but in neither map and absent from the
    # comparison manifest, which is what makes it `unknown-version`.
    baseline["not_installed"] = [p for p in baseline["not_installed"] if p != ENGINE]
    report = kit_doctor.inspect(root, _manifest(installed), config, baseline)
    assert _states(report)[ENGINE] == "unknown-version", _states(report)[ENGINE]
    return report


def test_a_tree_holding_only_unjudgeable_files_is_not_called_empty(tmp_path, capsys):
    """`scripts/check_doc_budget.py` is on disk. Saying "nothing is installed
    here" is a plain falsehood, not an imprecision."""
    report = _unjudgeable_case(tmp_path, also_installed=False)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "nothing is installed here" not in out, (
        "a tree with a file on disk was reported as an empty adoption"
    )
    assert "drift unjudgeable for 1 present file(s)" in out


def test_the_intact_verdict_carries_the_unjudgeable_caveat(tmp_path, capsys):
    """Both skill docs tell an operator to skim for this line, so it must not
    read as an all-clear while the section below says a file cannot be judged."""
    report = _unjudgeable_case(tmp_path, also_installed=True)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    verdict = next(ln for ln in out.splitlines() if "intact for this adoption" in ln)
    assert "drift unjudgeable for 1 present file(s), listed below" in verdict, verdict
    assert not verdict.lstrip().startswith("✓"), (
        f"a bare ✓ stood above an unjudgeable file: {verdict}"
    )
    # The caveat must point at something real.
    assert "drift cannot be judged" in out


def test_an_empty_adoption_does_not_say_all_declined_when_some_were_never_offered(
    tmp_path, capsys
):
    """"all N declined" is only true when `declined` accounts for every absence.
    At 0 declined and 33 new-upstream it read "all 0 kit-owned file(s) are
    declined" directly above the itemised 33-file list contradicting it —
    the headline/detail contradiction this PR closed twice for `removed`,
    reintroduced in the adjacent branch. (Panel, adversarial lens, round 2.)
    """
    root = _fake_repo(tmp_path)
    (root / "scripts" / "check_doc_budget.py").unlink()
    every = [rel for rel, _role in kit_doctor.KIT_OWNED]
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    # Nothing installed, nothing declined, everything unmentioned.
    baseline = {"kit_version": 2, "kit_commit": "abc", "files": {}, "not_installed": []}
    print(kit_doctor.render(kit_doctor.inspect(root, _manifest({}), config, baseline)))
    out = capsys.readouterr().out

    assert "all 0 kit-owned file(s)" not in out, "the verdict claimed 'all 0 ... declined'"
    assert f"0 declined and {len(every)} never offered" in out
    assert "nothing is installed here" in out


def test_the_unmentioned_state_does_not_assert_what_only_an_intact_record_supports(
    tmp_path, capsys
):
    """One deleted key turns a `removed` finding into this line at exit 0, for a
    file that WAS installed and then deleted. The baseline is the trust root and
    is not integrity-protected, so the two are indistinguishable here — which
    means the wording must not claim the kit did anything."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    written, _ = kit_doctor.record_install_manifest(root, config, 2, "abc123")
    recorded = written["files"][ENGINE]["sha256"]
    target.unlink()
    del written["files"][ENGINE]  # the single edit that flips the verdict

    report = kit_doctor.inspect(root, _manifest({ENGINE: recorded}), config, written)
    assert _states(report)[ENGINE] == "new-upstream", "fixture is confounded"
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "the kit added since your baseline" not in out, (
        "the report asserted the kit added a file, which only an intact baseline could support"
    )
    assert "this baseline does not mention either way" in out
    # The likely cause is still named — hedged, not deleted.
    assert "most likely added to the kit since it was recorded" in out


# --- the verdict caveats, pinned on EVERY branch (panel round 3) -------------
#
# `n_differ` reached none of the verdict branches: injecting `n_differ = 0`
# before the whole block left all 196 tests green, while a STALE or LOCALLY
# EDITED file sat under a bare `✓ intact for this adoption` at exit 1. And two
# of the four branches carrying the caveat were themselves unpinned — the
# "full install" ternary and the "NOT intact" f-string both survived removal.


def _drifted_case(tmp_path, *, declined: bool):
    """A present file whose hash matches neither the baseline nor the kit, so it
    lands in the `differs` family — judged, actionable drift."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    other = "scripts/lib/kitconfig.py"
    installed = {ENGINE: _sha("what was installed here")}
    if not declined:
        # Leave nothing declined, so the "full install" branch is the one hit.
        _write(root / other, "second file\n")
        installed[other] = kit_doctor.sha256_of(root / other)
    baseline = _scoped_baseline(installed)
    if not declined:
        baseline["not_installed"] = []
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root, _manifest({**installed, ENGINE: _sha("what the kit ships")}), config, baseline
    )
    assert _states(report)[str(target.relative_to(root))] in (
        "stale",
        "locally-edited",
        "stale-and-edited",
        "differs",
    ), _states(report)[str(target.relative_to(root))]
    return report


def test_judged_drift_stops_the_verdict_reading_as_an_all_clear(tmp_path, capsys):
    """The HIGH from round 3: `unknown-version` got the caveat and `differs` did
    not — the weaker case caveated, the stronger one bare."""
    report = _drifted_case(tmp_path, declined=True)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    verdict = next(ln for ln in out.splitlines() if "intact for this adoption" in ln)
    assert not verdict.lstrip().startswith("✓"), (
        f"a bare ✓ stood above judged, actionable drift: {verdict}"
    )
    assert "1 present file(s) differ from the kit" in verdict, verdict


def test_the_full_install_verdict_carries_the_caveat_too(tmp_path, capsys):
    """The `else:` branch — nothing declined — was one of the two whose caveat
    survived removal with the suite green."""
    report = _drifted_case(tmp_path, declined=False)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    verdict = next(ln for ln in out.splitlines() if "intact for this adoption" in ln)
    assert "full install, nothing declined" in verdict, verdict
    assert not verdict.lstrip().startswith("✓"), verdict
    assert "differ from the kit" in verdict, verdict


def test_the_not_intact_verdict_carries_the_caveat_too(tmp_path, capsys):
    """The `broken` branch — the other unpinned one. A tree can be both missing
    a file it recorded AND holding one whose drift cannot be judged."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    gone = "scripts/lib/kitconfig.py"
    _write(root / gone, "recorded, and about to vanish\n")
    installed = {
        ENGINE: kit_doctor.sha256_of(target),
        gone: kit_doctor.sha256_of(root / gone),
    }
    baseline = _scoped_baseline(installed)
    (root / gone).unlink()
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    # ENGINE present with no manifest entry -> unknown-version, beside the removal.
    report = kit_doctor.inspect(root, _manifest({}), config, baseline)
    assert [f.state for f in report.broken] == ["removed"], [f.state for f in report.broken]

    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    verdict = next(ln for ln in out.splitlines() if "intact for this adoption" in ln)
    assert verdict.lstrip().startswith("✗"), verdict
    assert "drift unjudgeable for 1 present file(s)" in verdict, verdict


def test_a_brand_new_partial_baseline_is_not_called_old(tmp_path, capsys):
    """A baseline written SECONDS AGO by a current kit lands on the same branch
    as a genuinely old one: an unverified path suppresses `not_installed` while
    `kit_commit` is written anyway, so the record is trusted, scope-less, and
    new. The note used to assert it "predates the declared install set" — false,
    and it points the operator away from the reconcile step they actually need.
    (Panel, adversarial lens, round 4.)
    """
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    written, unverified = kit_doctor.record_install_manifest(
        root, config, 2, "b" * 40, source_files={ENGINE: {"sha256": "0" * 64}}
    )
    assert unverified == [ENGINE] and "not_installed" not in written, "fixture is confounded"

    report = kit_doctor.inspect(root, _manifest({}), config, written)
    assert report.baseline_trusted and not report.declared_scope_known
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "This baseline predates the declared install set" not in out, (
        "a baseline written this run was reported as predating the feature"
    )
    assert "declares no install set" in out
    # Both causes named, and the unverified one carries its own next step.
    assert "did not match the source kit" in out
    assert "reconcile those first" in out


@pytest.mark.parametrize(
    "key,value",
    [("not_installed", "a string, not a list"), ("files", ["a list, not a dict"])],
)
def test_a_malformed_baseline_reaches_the_same_note_and_it_does_not_claim_two_causes(
    tmp_path, capsys, key, value
):
    """A third route to the scope-less state, and the reason the note stopped
    saying "Either … or": `_declared_scope` declines to read a scope out of a
    malformed `files` OR `not_installed`, so a corrupt baseline lands on the
    same branch as an old one and a partial one. Two causes presented as
    exhaustive is the error this note was fixed for one round earlier — it must
    not be reintroduced by naming two of three. (CodeRabbit, PR #322.)
    """
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    baseline[key] = value

    report = _inspect(root, {ENGINE: recorded}, baseline)
    assert not report.declared_scope_known
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert "declares no install set" in out
    assert "Either it predates" not in out, "two causes were presented as exhaustive"
    assert "malformed" in out, "the malformed route is not named at all"


# --- the registrations the hook depends on (#379), and a declined hook (#381) --
#
# Both are the same shape as #360: a fact the doctor's verdict depends on, that
# the doctor could not see. #360 was the file that PERFORMS the install; #379 is
# the pair of files that decide whether the kit's one mandatory mechanism fires.
# The measured occasion: an adopter reporting `16 unchanged, 0 differ, 0 missing`
# and exit 0, over zero registration state.


def _registration(root: Path, surface: str, command: str) -> None:
    matcher = "^Bash$" if surface == ".codex/hooks.json" else "Bash"
    _write(
        root / surface,
        json.dumps({"hooks": {"PostToolUse": [{"matcher": matcher, "hooks": [
            {"type": "command", "command": command, "timeout": 10}
        ]}]}}),
    )


HOOK_REL = "scripts/hooks/pr_followup_hook.py"


def test_a_registration_naming_a_path_that_exists_resolves(tmp_path):
    """The Claude shape as `init.sh` prints it, placeholder and all."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude',
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    claude = [s for s in statuses if s.surface == ".claude/settings.json"]

    assert [(s.state, s.detail) for s in claude] == [("resolves", HOOK_REL)]


def test_a_registration_naming_a_path_that_moved_is_reported_dead(tmp_path):
    """#368's shape: the engines were vendored to `scripts/devkit/`, the
    registration still names the old `scripts/hooks/` path. The operator's
    observable is a hook that silently stopped firing — a PostToolUse failure
    does not halt a session — so nothing else in the kit reports it."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "hooks" / "pr_followup_hook.py", "print('hook')\n")
    _registration(
        root, ".codex/hooks.json",
        'root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        f'[ -n "$root" ] || exit 0; exec python3 "$root/{HOOK_REL}" --runtime codex',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    dead = report.dead_registrations

    assert [(s.runtime, s.detail) for s in dead] == [("codex", HOOK_REL)]
    assert "NO SUCH FILE" in kit_doctor.render(report)


def test_a_dead_registration_makes_the_run_non_green(tmp_path, capsys, monkeypatch):
    """The property the issue was filed for. Without it the adopter's report
    was `0 differ, 0 missing`, exit 0, with a dead hook — which is the same
    clean bill of health a working install gets."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    _write(root / "kit-manifest.json", json.dumps(_manifest({ENGINE: kit_doctor.sha256_of(target)})))
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude',
    )
    monkeypatch.chdir(root)

    # Nothing on the FILE axis reaches the exit code here — no drift, nothing
    # broken — so a 1 can only have come from the registration. Asserted on the
    # report rather than on the rendered counts, which also carry the plain
    # `missing` entries a minimal fixture always has and which are not findings.
    quiet = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, None)
    assert (quiet.drifted, quiet.broken) == ([], [])

    assert kit_doctor.main(["--root", str(root)]) == 1
    assert "NO SUCH FILE" in capsys.readouterr().out


def test_an_unwired_runtime_is_not_an_error(tmp_path):
    """`init.sh` PRINTS both registration blocks and writes neither (#303), so
    an adopter who has not wired one is in a supported state. Failing it would
    be #286's bug in a third place: a healthy adoption failing its own gate
    forever, which is exactly what #381 is about on the sibling check."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert report.dead_registrations == []
    assert {s.state for s in report.registrations} == {"absent"}
    assert "`/hooks` in a session is the authority" in kit_doctor.render(report)


def test_a_registration_this_check_cannot_resolve_is_not_called_broken(tmp_path):
    """An expansion the kit does not know is a limit of the CHECK, not a
    finding about the repo. Reporting it as broken would assert a file is
    missing from a path that was never resolved."""
    root = _fake_repo(tmp_path)
    _registration(
        root, ".claude/settings.json", f'python3 "$MY_OWN_ROOT/{HOOK_REL}" --runtime claude'
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    claude = [s for s in statuses if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["unresolvable"]


def test_a_malformed_registration_degrades_instead_of_aborting_the_report(tmp_path):
    """Same rule the baseline read follows: a diagnostic that dies on one
    unparseable file tells the adopter nothing about the other thirty-six."""
    root = _fake_repo(tmp_path)
    _write(root / ".codex" / "hooks.json", "{not json at all")

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert [s.state for s in statuses if s.surface == ".codex/hooks.json"] == ["unreadable"]


def test_a_malformed_codex_project_config_degrades_instead_of_aborting(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / ".codex" / "config.toml", "[hooks\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert [s.state for s in statuses if s.surface == ".codex/config.toml"] == [
        "unreadable"
    ]


def test_a_session_start_registration_is_checked_too(tmp_path):
    """The walk is over every `command` in the document, not a lookup into the
    events the kit ships today — `SessionStart` is already a second one, and a
    lookup would go blind the day a third arrives."""
    root = _fake_repo(tmp_path)
    _write(
        root / ".claude" / "settings.json",
        json.dumps({"hooks": {"SessionStart": [{"matcher": "startup", "hooks": [
            {"type": "command",
             "command": '[ -z "$JOB_NAME" ] && cd "$CLAUDE_PROJECT_DIR" '
                        "&& uv run --script scripts/check_memory_budget.py --quiet || true"}
        ]}]}}),
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    claude = [s for s in statuses if s.surface == ".claude/settings.json"]

    # check_memory_budget.py is not in this fixture — only check_doc_budget.py is.
    assert [(s.state, s.detail) for s in claude] == [
        ("broken", "scripts/check_memory_budget.py")
    ]


def _valid_codex_lifecycle_document() -> dict:
    return {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'root="$(git rev-parse --show-toplevel 2>/dev/null)" '
                            '|| exit 0; [ -n "$root" ] || exit 0; '
                            '[ -z "${JOB_NAME:-}" ] || exit 0; '
                            'uv run --script "$root/scripts/check_doc_budget.py" '
                            "--quiet || true",
                            "timeout": 15,
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "^Bash$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'root="$(git rev-parse --show-toplevel 2>/dev/null)" '
                            '|| exit 0; [ -n "$root" ] || exit 0; '
                            'exec python3 "$root/scripts/hooks/pr_followup_hook.py" '
                            "--runtime codex",
                            "timeout": 10,
                        }
                    ],
                }
            ],
        }
    }


def _write_codex_lifecycle_fixture(root: Path, document: dict) -> None:
    _write(root / HOOK_REL, "print('hook')\n")
    _write(root / ".codex" / "hooks.json", json.dumps(document))


def _valid_codex_inline_posttooluse() -> str:
    return """\
[[hooks.PostToolUse]]
matcher = "^Bash$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = 'root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; [ -n "$root" ] || exit 0; exec python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
timeout = 10
"""


def _has_verified_lifecycle(statuses, name: str) -> bool:
    return any(
        status.state == "verified" and status.detail.startswith(name)
        for status in statuses
    )


def test_codex_lifecycle_semantics_accept_the_shipped_contract(tmp_path):
    root = _fake_repo(tmp_path)
    shipped = json.loads(
        (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8")
    )
    _write_codex_lifecycle_fixture(root, shipped)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    codex = [s for s in statuses if s.runtime == "codex"]

    assert not [s for s in codex if s.state == "misconfigured"]
    assert {s.detail for s in codex if s.state == "resolves"} == {
        "scripts/check_doc_budget.py",
        HOOK_REL,
    }
    assert {s.detail for s in codex if s.state == "verified"} == {
        "check_doc_budget.py canonical lifecycle form verified",
        "pr_followup_hook.py canonical lifecycle form verified",
    }


@pytest.mark.parametrize("matcher", ["", "*"])
def test_codex_lifecycle_semantics_verify_explicit_match_all_session_matchers(
    tmp_path, matcher
):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    document["hooks"]["SessionStart"][0]["matcher"] = matcher
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    doc = [s for s in statuses if s.detail.startswith("check_doc_budget.py")]

    assert [(s.state, s.detail) for s in doc] == [
        ("verified", "check_doc_budget.py supported match-all lifecycle form verified")
    ]


def test_codex_lifecycle_semantics_accept_inline_project_config(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _write(root / ".codex" / "config.toml", _valid_codex_inline_posttooluse())

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    codex = [s for s in statuses if s.runtime == "codex"]

    assert not [s for s in codex if s.state == "misconfigured"]
    assert any(s.state == "resolves" and s.detail == HOOK_REL for s in codex)
    assert any(
        s.state == "verified"
        and s.detail == "pr_followup_hook.py canonical lifecycle form verified"
        for s in codex
    )


def test_nested_hooks_metadata_is_not_an_inline_codex_registration(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    command = _valid_codex_lifecycle_document()["hooks"]["PostToolUse"][0]["hooks"][
        0
    ]["command"]
    _write(
        root / ".codex" / "config.toml",
        f"[metadata.hooks]\ncommand = {json.dumps(command)}\n",
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    inline = [s for s in statuses if s.surface == ".codex/config.toml"]

    assert inline == []


def test_codex_lifecycle_semantics_detect_cross_source_duplicate(tmp_path):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(root / ".codex" / "config.toml", _valid_codex_inline_posttooluse())

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert any("pr_followup_hook.py has a duplicate" in detail for detail in details)


def test_duplicate_is_attributed_to_the_source_that_contains_it(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    document["hooks"]["SessionStart"].append(
        json.loads(json.dumps(document["hooks"]["SessionStart"][0]))
    )
    _write_codex_lifecycle_fixture(root, document)
    _write(root / ".codex" / "config.toml", "[features]\nhooks = true\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    duplicates = [
        s for s in statuses if s.state == "misconfigured" and "duplicate" in s.detail
    ]

    assert [(s.surface, s.detail) for s in duplicates] == [
        (".codex/hooks.json", "check_doc_budget.py has a duplicate Codex registration")
    ]


@pytest.mark.parametrize("feature", ["hooks", "codex_hooks"])
def test_codex_lifecycle_semantics_detect_project_feature_disable(tmp_path, feature):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(root / ".codex" / "config.toml", f"[features]\n{feature} = false\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert "Codex lifecycle hooks are disabled by the project config" in details


def test_codex_lifecycle_semantics_validates_each_present_feature_alias(tmp_path):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(
        root / ".codex" / "config.toml",
        "[features]\nhooks = true\ncodex_hooks = 0\n",
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert "Codex project feature codex_hooks must be a boolean" in details


def test_invalid_feature_alias_does_not_claim_an_effective_disable(tmp_path):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(
        root / ".codex" / "config.toml",
        "[features]\nhooks = false\ncodex_hooks = 0\n",
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert details == ["Codex project feature codex_hooks must be a boolean"]


@pytest.mark.parametrize(
    ("canonical", "deprecated", "disabled"),
    [
        (True, False, False),
        (False, True, True),
    ],
)
def test_canonical_codex_feature_key_takes_precedence(
    tmp_path, canonical, deprecated, disabled
):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(
        root / ".codex" / "config.toml",
        "[features]\n"
        f"hooks = {str(canonical).lower()}\n"
        f"codex_hooks = {str(deprecated).lower()}\n",
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert (
        "Codex lifecycle hooks are disabled by the project config" in details
    ) is disabled


@pytest.mark.parametrize(
    ("feature", "value"),
    [
        ("hooks", "0"),
        ("hooks", "0.0"),
        ("hooks", '"false"'),
        ("codex_hooks", "0"),
    ],
)
def test_codex_lifecycle_semantics_reject_nonboolean_project_feature(
    tmp_path, feature, value
):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(root / ".codex" / "config.toml", f"[features]\n{feature} = {value}\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert f"Codex project feature {feature} must be a boolean" in details


def test_codex_lifecycle_semantics_reject_nontable_project_features(tmp_path):
    root = _fake_repo(tmp_path)
    _write_codex_lifecycle_fixture(root, _valid_codex_lifecycle_document())
    _write(root / ".codex" / "config.toml", "features = 0\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert "Codex project features must be a table" in details


@pytest.mark.parametrize(
    "config",
    [
        "features = 0\n",
        '[features]\nhooks = "false"\n',
    ],
)
def test_unrelated_codex_feature_shape_is_ignored_without_identified_lifecycle_commands(
    tmp_path, config
):
    root = _fake_repo(tmp_path)
    _write(root / ".codex" / "config.toml", config)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not [status for status in statuses if status.state == "misconfigured"]


def test_codex_lifecycle_semantics_reject_float_inline_timeout(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    invalid = _valid_codex_inline_posttooluse().replace("timeout = 10", "timeout = 10.0")
    _write(root / ".codex" / "config.toml", invalid)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert "pr_followup_hook.py timeout must be 10 seconds" in details


def test_inline_codex_config_is_explicitly_unreadable_without_tomllib(
    tmp_path, monkeypatch
):
    root = _fake_repo(tmp_path)
    _write(root / ".codex" / "config.toml", _valid_codex_inline_posttooluse())
    monkeypatch.setattr(kit_doctor, "tomllib", None)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert [
        (status.state, status.detail)
        for status in statuses
        if status.surface == ".codex/config.toml"
    ] == [("unreadable", "TOML parser unavailable; run kit_doctor through uv")]


def test_codex_lifecycle_semantics_validate_inline_project_config(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    invalid = _valid_codex_inline_posttooluse().replace(
        "--runtime codex", "--runtime claude"
    )
    _write(root / ".codex" / "config.toml", invalid)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


# Frozen from the fallback-panel probes accumulated on PR #590. These cases are
# a hostile corpus, not a grammar specification: each mutation must fail to
# receive the positive ``verified`` result, but the checker does not explain its
# shell behavior. Altered command strings receive no lifecycle classification;
# the generic path axis remains independent.
@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("doc-matcher", "for open-ended match-all coverage"),
        ("doc-matcher-container", "for open-ended match-all coverage"),
        ("doc-matcher-null", "for open-ended match-all coverage"),
        ("doc-timeout", "check_doc_budget.py timeout must be 15 seconds"),
        ("doc-timeout-float", "check_doc_budget.py timeout must be 15 seconds"),
        ("doc-job-skip", "must use the shipped scheduled-run guard"),
        ("doc-job-reversed", "must use the shipped scheduled-run guard"),
        ("doc-job-comment", "must use the shipped scheduled-run guard"),
        ("doc-job-literal", "must use the shipped scheduled-run guard"),
        ("doc-job-fragmented", "must use the shipped scheduled-run guard"),
        ("doc-job-escaped", "must use the shipped scheduled-run guard"),
        ("doc-job-late", "must use the shipped scheduled-run guard"),
        ("doc-job-echo", "must use the shipped scheduled-run guard"),
        ("doc-job-disabled", "must use the shipped scheduled-run guard"),
        ("doc-job-reassigned", "must use the shipped scheduled-run guard"),
        ("doc-read-job", "must use the shipped Git-root"),
        ("doc-root-guard-missing", "must use the shipped Git-root"),
        ("doc-quiet", "must run in quiet mode"),
        ("doc-quiet-comment", "must run in quiet mode"),
        ("doc-quiet-unbound", "must run in quiet mode"),
        ("doc-quiet-json", "quiet mode must not be overridden"),
        ("doc-quiet-json-equals", "quiet mode must not be overridden"),
        ("doc-root-option", "must use repository-resolved root and config"),
        ("doc-config-option", "must use repository-resolved root and config"),
        ("doc-uv-help", "must use the shipped uv run --script launcher"),
        ("doc-exec", "must use the shipped uv run --script launcher"),
        ("doc-root-stderr", "must use the shipped Git-root"),
        ("doc-stray-argument", "must use only the shipped --quiet argument"),
        ("doc-redirection", "must not use shell redirection"),
        ("pr-event", "must be registered under PostToolUse"),
        ("pr-matcher", 'matcher must be "^Bash$"'),
        ("pr-timeout", "pr_followup_hook.py timeout must be 10 seconds"),
        ("pr-timeout-float", "pr_followup_hook.py timeout must be 10 seconds"),
        ("pr-runtime", "must pass --runtime codex"),
        ("pr-runtime-comment", "must pass --runtime codex"),
        ("pr-runtime-unbound", "must pass --runtime codex"),
        ("pr-runtime-shadowed", "must pass --runtime codex"),
        ("pr-runtime-expanded", "must pass --runtime codex"),
        ("pr-runtime-crlf", "must pass --runtime codex"),
        ("pr-leading-operator", "command must use valid shell syntax"),
        ("pr-consecutive-operator", "command must use valid shell syntax"),
        ("pr-nul-sentinel", "command must use valid shell syntax"),
        ("pr-leading-comment", "must pass --runtime codex"),
        ("pr-absolute-launcher", "must use the shipped python3 launcher"),
        ("pr-escaped-space-comment", "must use supported shell control flow"),
        ("pr-runtime-midword-hash", "must pass --runtime codex"),
        ("pr-echo-argument", "path must be invoked as the configured kit engine"),
        ("pr-python-data", "path must be invoked as the configured kit engine"),
        ("pr-disabled-invocation", "must use supported shell control flow"),
        ("pr-or-invocation", "must use supported shell control flow"),
        ("pr-piped-invocation", "must use supported shell control flow"),
        ("pr-background-invocation", "must use supported shell control flow"),
        ("pr-exit-before-invocation", "must use supported shell control flow"),
        ("pr-redirection", "must not use shell redirection"),
        ("pr-dup-redirection", "must not use shell redirection"),
        ("pr-group-exit", "must not use compound shell syntax"),
        ("pr-conditional", "must not use compound shell syntax"),
        ("pr-heredoc", "path must be invoked as the configured kit engine"),
        ("pr-command-substitution", "must not use compound shell syntax"),
        ("pr-inline-root", "must not use compound shell syntax"),
        ("pr-read-root", "must use the shipped Git-root"),
        ("pr-root-guard-missing", "must use the shipped Git-root"),
        ("absolute-dead-prefix", "must use the shipped Git-root"),
        ("relative-path", "path must not depend on the session working directory"),
        ("pwd-path", "path must not depend on the session working directory"),
        ("pwd-command-path", "path must not depend on the session working directory"),
        ("pwd-parameter-path", "path must not depend on the session working directory"),
        ("root-pwd-default-path", "path must not depend on the session working directory"),
        ("root-parameter-path", "path must not depend on the session working directory"),
        ("root-traversal-path", "path must resolve to the configured kit engine"),
        ("root-nested-path", "path must resolve to the configured kit engine"),
        ("disabled-root-path", "path must not depend on the session working directory"),
        ("dead-root-chain", "path must not depend on the session working directory"),
        ("root-pwd-alias", "path must not depend on the session working directory"),
        ("root-overwritten", "path must not depend on the session working directory"),
        ("root-unquoted-guard", "must use the shipped Git-root"),
        ("root-single-quoted-path", "path must not depend on the session working directory"),
        ("root-fragmented-path", "path must not depend on the session working directory"),
        ("handler-type", "must use a command handler"),
        ("invalid-shell", "command must use valid shell syntax"),
    ],
)
def test_codex_lifecycle_hostile_corpus_is_never_verified(
    tmp_path, mutation, expected
):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    session = document["hooks"]["SessionStart"][0]
    session_hook = session["hooks"][0]
    post = document["hooks"]["PostToolUse"][0]
    post_hook = post["hooks"][0]

    if mutation == "doc-matcher":
        session["matcher"] = "^startup$"
    elif mutation == "doc-matcher-container":
        session["matcher"] = ["startup"]
    elif mutation == "doc-matcher-null":
        session["matcher"] = None
    elif mutation == "doc-timeout":
        session_hook["timeout"] = 14
    elif mutation == "doc-timeout-float":
        session_hook["timeout"] = 15.0
    elif mutation == "doc-job-skip":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ] || exit 0; ', ""
        )
    elif mutation == "doc-job-reversed":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ]', '[ -n "${JOB_NAME:-}" ]'
        )
    elif mutation == "doc-job-comment":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ] || exit 0; ', ""
        ) + ' # [ -z "${JOB_NAME:-}" ] || exit 0'
    elif mutation == "doc-job-literal":
        session_hook["command"] = session_hook["command"].replace(
            '"${JOB_NAME:-}"', "'${JOB_NAME:-}'"
        )
    elif mutation == "doc-job-fragmented":
        session_hook["command"] = session_hook["command"].replace(
            '"${JOB_NAME:-}"', '"$"\'JOB_NAME\''
        )
    elif mutation == "doc-job-escaped":
        session_hook["command"] = session_hook["command"].replace(
            '"${JOB_NAME:-}"', r"\${JOB_NAME:-}"
        )
    elif mutation == "doc-job-late":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ] || exit 0; ', ""
        ) + '; [ -z "${JOB_NAME:-}" ] || exit 0'
    elif mutation == "doc-job-echo":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ]', 'echo [ -z "${JOB_NAME:-}" ]'
        )
    elif mutation == "doc-job-disabled":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ]', 'false && [ -z "${JOB_NAME:-}" ]'
        )
    elif mutation == "doc-job-reassigned":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ]', 'JOB_NAME=; [ -z "${JOB_NAME:-}" ]'
        )
    elif mutation == "doc-read-job":
        session_hook["command"] = session_hook["command"].replace(
            '[ -z "${JOB_NAME:-}" ]', 'read JOB_NAME; [ -z "${JOB_NAME:-}" ]'
        )
    elif mutation == "doc-root-guard-missing":
        session_hook["command"] = session_hook["command"].replace(
            ' || exit 0; [ -n "$root" ] || exit 0;', ";"
        )
    elif mutation == "doc-quiet":
        session_hook["command"] = session_hook["command"].replace(" --quiet", "")
    elif mutation == "doc-quiet-comment":
        session_hook["command"] = session_hook["command"].replace(
            " --quiet", ""
        ) + " # --quiet"
    elif mutation == "doc-quiet-unbound":
        session_hook["command"] = session_hook["command"].replace(
            " --quiet", ""
        ) + "; echo --quiet"
    elif mutation == "doc-quiet-json":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", "--quiet --json"
        )
    elif mutation == "doc-quiet-json-equals":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", "--quiet --json=true"
        )
    elif mutation == "doc-root-option":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", '--quiet --root "$PWD"'
        )
    elif mutation == "doc-config-option":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", "--quiet --config=config/dev-model.yaml"
        )
    elif mutation == "doc-uv-help":
        session_hook["command"] = session_hook["command"].replace(
            "uv run --script", "uv run --help --script"
        )
    elif mutation == "doc-exec":
        session_hook["command"] = session_hook["command"].replace(
            "uv run --script", "exec uv run --script"
        )
    elif mutation == "doc-root-stderr":
        session_hook["command"] = session_hook["command"].replace(
            " --show-toplevel 2>/dev/null", " --show-toplevel"
        )
    elif mutation == "doc-stray-argument":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", "--quiet stray-argument"
        )
    elif mutation == "doc-redirection":
        session_hook["command"] = session_hook["command"].replace(
            "--quiet", "> --quiet"
        )
    elif mutation == "pr-event":
        document["hooks"]["SessionStart"].append(post)
        document["hooks"]["PostToolUse"] = []
    elif mutation == "pr-matcher":
        post["matcher"] = "Bash"
    elif mutation == "pr-timeout":
        post_hook["timeout"] = 11
    elif mutation == "pr-timeout-float":
        post_hook["timeout"] = 10.0
    elif mutation == "pr-runtime":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "--runtime claude"
        )
    elif mutation == "pr-runtime-comment":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "--runtime claude # --runtime codex"
        )
    elif mutation == "pr-runtime-unbound":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "--runtime claude; echo --runtime codex"
        )
    elif mutation == "pr-runtime-shadowed":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "--runtime claude --runtime codex"
        )
    elif mutation == "pr-runtime-expanded":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", '"$RUNTIME_ARG" --runtime codex'
        )
    elif mutation == "pr-runtime-crlf":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", '--runtime "co\\\r\ndex"'
        )
    elif mutation == "pr-leading-operator":
        post_hook["command"] = "&& " + post_hook["command"]
    elif mutation == "pr-consecutive-operator":
        post_hook["command"] = post_hook["command"].replace(
            " || exit 0", " || || exit 0", 1
        )
    elif mutation == "pr-nul-sentinel":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"\x00devkit-root\x00/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-leading-comment":
        post_hook["command"] = "# explanation\n" + post_hook["command"].replace(
            "--runtime codex", "--runtime claude"
        )
    elif mutation == "pr-absolute-launcher":
        post_hook["command"] = post_hook["command"].replace(
            "exec python3", "exec /definitely/not-installed/python3"
        )
    elif mutation == "pr-escaped-space-comment":
        post_hook["command"] += r" harmless\ #; false"
    elif mutation == "pr-runtime-midword-hash":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "--runtime codex#typo"
        )
    elif mutation == "pr-echo-argument":
        post_hook["command"] = (
            'root="$(git rev-parse --show-toplevel)"; '
            'echo "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "pr-python-data":
        post_hook["command"] = (
            'root="$(git rev-parse --show-toplevel)"; '
            'python3 -c pass "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "pr-disabled-invocation":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
            'false && exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-or-invocation":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
            'true || exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-piped-invocation":
        post_hook["command"] += " | true"
    elif mutation == "pr-background-invocation":
        post_hook["command"] += " &"
    elif mutation == "pr-exit-before-invocation":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
            'exit 0; exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-redirection":
        post_hook["command"] = post_hook["command"].replace(
            "--runtime codex", "> --runtime codex"
        )
    elif mutation == "pr-dup-redirection":
        post_hook["command"] += " 1>&2"
    elif mutation == "pr-group-exit":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
            '{ exit 0; }; exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-conditional":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex',
            'if false; then :; exec python3 '
            '"$root/scripts/hooks/pr_followup_hook.py" --runtime codex; fi',
        )
    elif mutation == "pr-heredoc":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex',
            'cat <<EOF\nexec python3 "$root/scripts/hooks/pr_followup_hook.py" '
            '--runtime codex\nEOF',
        )
    elif mutation == "pr-command-substitution":
        post_hook["command"] += (
            ' "$(python3 "$root/scripts/hooks/pr_followup_hook.py" '
            '--runtime claude)"'
        )
    elif mutation == "pr-inline-root":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"$(git rev-parse --show-toplevel)/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-read-root":
        post_hook["command"] = post_hook["command"].replace(
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
            'read root; exec python3 "$root/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "pr-root-guard-missing":
        post_hook["command"] = post_hook["command"].replace(
            ' || exit 0; [ -n "$root" ] || exit 0;', ";"
        )
    elif mutation == "absolute-dead-prefix":
        post_hook["command"] = (
            f'set -e; false; exec python3 "{root / HOOK_REL}" --runtime codex'
        )
    elif mutation == "relative-path":
        post_hook["command"] = (
            "python3 scripts/hooks/pr_followup_hook.py --runtime codex"
        )
    elif mutation == "pwd-path":
        post_hook["command"] = (
            'python3 "$PWD/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "pwd-command-path":
        post_hook["command"] = (
            'python3 "$(pwd)/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "pwd-parameter-path":
        post_hook["command"] = (
            'python3 "${PWD:+$PWD}/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "root-pwd-default-path":
        post_hook["command"] = (
            'python3 "${root:-$PWD}/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "root-parameter-path":
        post_hook["command"] = (
            'python3 "${root:+/definitely/not-the-repo}/scripts/hooks/'
            'pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "root-traversal-path":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"$root/../../sibling/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "root-nested-path":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"$root/decoy/scripts/hooks/pr_followup_hook.py"',
        )
    elif mutation == "disabled-root-path":
        post_hook["command"] = (
            'root="$(git rev-parse --show-toplevel)"; false && cd "$root"; '
            "python3 scripts/hooks/pr_followup_hook.py --runtime codex"
        )
    elif mutation == "dead-root-chain":
        post_hook["command"] = (
            'root="$(git rev-parse --show-toplevel)"; false && cd "$root" && '
            "python3 scripts/hooks/pr_followup_hook.py --runtime codex"
        )
    elif mutation == "root-pwd-alias":
        post_hook["command"] = (
            'root=$PWD; exec python3 "$root/scripts/hooks/pr_followup_hook.py" '
            "--runtime codex"
        )
    elif mutation == "root-overwritten":
        post_hook["command"] = (
            'root="$(git rev-parse --show-toplevel)"; root=$PWD; '
            'exec python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
        )
    elif mutation == "root-unquoted-guard":
        post_hook["command"] = post_hook["command"].replace(
            '[ -n "$root" ]', "[ -n $root ]"
        )
    elif mutation == "root-single-quoted-path":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            "'$root/scripts/hooks/pr_followup_hook.py'",
        )
    elif mutation == "root-fragmented-path":
        post_hook["command"] = post_hook["command"].replace(
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"$"\'root/scripts/hooks/pr_followup_hook.py\'',
        )
    elif mutation == "handler-type":
        post_hook["type"] = "prompt"
    elif mutation == "invalid-shell":
        post_hook["command"] += ' "'

    _write_codex_lifecycle_fixture(root, document)
    statuses = kit_doctor.inspect_registrations(root, "scripts")
    target = "check_doc_budget.py" if mutation.startswith("doc-") else "pr_followup_hook.py"
    assert not [
        status
        for status in statuses
        if status.state == "verified" and status.detail.startswith(target)
    ]
    rejected = [
        s
        for s in statuses
        if s.state in ("misconfigured", "unverifiable") and target in s.detail
    ]
    structurally_invalid = {
        "doc-matcher",
        "doc-matcher-container",
        "doc-matcher-null",
        "doc-timeout",
        "doc-timeout-float",
        "pr-event",
        "pr-matcher",
        "pr-timeout",
        "pr-timeout-float",
        "handler-type",
    }
    if mutation in structurally_invalid:
        assert rejected, f"{mutation} was neither misconfigured nor unverifiable"

    if rejected:
        assert any(
            expected in status.detail or status.state == "unverifiable"
            for status in rejected
        ), [(status.state, status.detail) for status in rejected]


@pytest.mark.parametrize("runtime_arg", ["--runtime codex", "--runtime=codex"])
@pytest.mark.parametrize("cd_command", ['cd "$root"', 'cd -P "$root"', 'cd -- "$root"'])
def test_noncanonical_root_anchored_relative_paths_are_not_verified(
    tmp_path, runtime_arg, cd_command
):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = (
        'root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        f'[ -n "$root" ] || exit 0; {cd_command} || exit 0; '
        f"python3 scripts/hooks/pr_followup_hook.py {runtime_arg}"
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


@pytest.mark.parametrize(
    "runtime_args", ["--runtime= --runtime codex", '--runtime "" --runtime=codex']
)
def test_noncanonical_repeated_runtime_options_are_not_verified(runtime_args, tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = post_hook["command"].replace("--runtime codex", runtime_args)
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


def test_adjacent_shell_operators_are_not_verified(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = post_hook["command"].replace(
        "--runtime codex", "--runtime claude&&echo ignored"
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


@pytest.mark.parametrize(
    "container",
    ["document", "events", "groups", "group-entry", "handlers", "handler-entry", "command"],
)
def test_codex_semantics_reject_malformed_lifecycle_containers(tmp_path, container):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post = document["hooks"]["PostToolUse"][0]
    post_hook = post["hooks"][0]
    if container == "document":
        document = [document]
    elif container == "events":
        document["hooks"] = [document["hooks"]]
    elif container == "groups":
        document["hooks"]["PostToolUse"] = post
    elif container == "group-entry":
        document["hooks"]["PostToolUse"] = [[post]]
    elif container == "handler-entry":
        post["hooks"] = [[post_hook]]
    elif container == "command":
        post_hook["command"] = [post_hook["command"]]
    else:
        post["hooks"] = post_hook
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert any("must be" in detail for detail in details), details


def test_codex_semantics_reject_a_nested_command_without_a_handler_command(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["metadata"] = {"command": post_hook.pop("command")}
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    details = [s.detail for s in statuses if s.state == "misconfigured"]

    assert any("command must be a string" in detail for detail in details), details


def test_script_word_scan_preserves_equals_options_as_arguments():
    lexed, words = kit_doctor._script_words(
        "echo --script=pr_followup_hook.py --runtime=codex"
    )

    assert lexed
    assert "--script=pr_followup_hook.py" in words
    assert "--runtime=codex" in words
    assert kit_doctor._match_word(words, "pr_followup_hook.py") is None


def test_codex_misconfiguration_renders_as_a_failure(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    document["hooks"]["PostToolUse"][0]["matcher"] = "Bash"
    _write_codex_lifecycle_fixture(root, document)

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    rendered = kit_doctor.render(report)

    assert "✗ .codex/hooks.json [codex]" in rendered
    assert "lifecycle wiring does not match" in rendered


def test_exact_codex_command_with_unsupported_keys_is_an_unverifiable_failure(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    hook["async"] = False
    _write_codex_lifecycle_fixture(root, document)

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    rendered = kit_doctor.render(report)

    assert any(s.state == "unverifiable" for s in report.dead_registrations)
    assert "✗ .codex/hooks.json [codex]" in rendered
    assert "installer-emitted key set was verified" in rendered


@pytest.mark.parametrize(
    ("container", "key", "value"),
    [
        ("handler", "async", False),
        ("group", "description", "extra metadata"),
    ],
)
def test_unsupported_codex_object_keys_are_unverifiable(
    tmp_path, container, key, value
):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    group = document["hooks"]["PostToolUse"][0]
    target = group["hooks"][0] if container == "handler" else group
    target[key] = value
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert any(s.state == "unverifiable" for s in statuses)
    assert not [
        s
        for s in statuses
        if s.state == "verified"
        and s.detail.startswith("pr_followup_hook.py")
    ]


def test_codex_rejects_the_claude_only_memory_tripwire(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    document["hooks"]["SessionStart"][0]["hooks"].append(
        {
            "type": "command",
            "command": (
                'root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
                '[ -n "$root" ] || exit 0; [ -z "${JOB_NAME:-}" ] || exit 0; '
                'uv run --script "$root/scripts/check_memory_budget.py" '
                "--quiet || true"
            ),
            "timeout": 15,
        }
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert any(
        s.state == "misconfigured" and "Claude-only" in s.detail for s in statuses
    )


def test_duplicate_codex_lifecycle_registration_is_a_finding(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    document["hooks"]["SessionStart"].append(
        json.loads(json.dumps(document["hooks"]["SessionStart"][0]))
    )
    _write_codex_lifecycle_fixture(root, document)

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert any(
        s.state == "misconfigured" and "duplicate" in s.detail
        for s in report.dead_registrations
    )


def test_multiple_invocations_inside_one_command_are_not_verified(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    hook["command"] = hook["command"].replace("exec python3", "python3")
    hook["command"] += (
        '; python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
    )
    _write_codex_lifecycle_fixture(root, document)

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert not _has_verified_lifecycle(report.registrations, "pr_followup_hook.py")
    assert not [s for s in report.dead_registrations if "duplicate" in s.detail]


def test_command_after_engine_exec_is_not_assigned_lifecycle_semantics(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    hook["command"] += (
        '; python3 "$root/scripts/hooks/pr_followup_hook.py" --runtime codex'
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")
    assert not [s for s in statuses if "duplicate" in s.detail]


def test_a_declined_pre_push_is_reported_as_declined_not_as_missing(tmp_path, capsys):
    """#381. cs-toolkit declines the kit's `pre-push` on principle (#46, still
    open — its own hook carries two guards no config key expresses), so the
    `run ./init.sh` advice could never be taken and never be cleared. A
    permanent warning is how the next real one gets skimmed past."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    assert kit_doctor.PRE_PUSH_REL in baseline["not_installed"], "fixture no longer declines it"

    report = _inspect(root, {ENGINE: recorded}, baseline)
    print(kit_doctor.render(report))
    out = capsys.readouterr().out

    assert report.hooks_state == "declined"
    assert "pre-push hook: declined" in out
    # The WHOLE line, not a window around it: an earlier form of this assertion
    # looked only before the word "declined", so appending the advice after it
    # survived (panel, correctness lens, round 7) — which is precisely where a
    # regression would land.
    hook_lines = [line for line in out.splitlines() if "pre-push hook" in line]
    assert hook_lines and all("init.sh" not in line for line in hook_lines), hook_lines


def test_an_undeclared_absent_pre_push_still_says_run_init(tmp_path, capsys):
    """The other direction, so the test above cannot pass by the warning simply
    being deleted: an adopter who never declared a decline gets the original
    advice, because for them it is still correct."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    report = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, None)
    print(kit_doctor.render(report))

    assert report.hooks_state == "not-installed"
    assert "NOT installed — run ./init.sh" in capsys.readouterr().out


def test_json_carries_the_hook_state_and_the_registrations(tmp_path, capsys, monkeypatch):
    """Both are invisible to a `--json` consumer otherwise: `hooks_installed`
    is a bool with no room for "declined", and the two registration surfaces
    are in neither KIT_OWNED nor any manifest."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    _write(root / "kit-manifest.json", json.dumps(_manifest({ENGINE: kit_doctor.sha256_of(target)})))
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".codex/hooks.json", f'exec python3 "$root/{HOOK_REL}" --runtime codex'
    )
    monkeypatch.chdir(root)

    kit_doctor.main(["--root", str(root), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["hooks_installed"] is False
    assert payload["hooks_state"] == "not-installed"
    assert {"runtime": "codex", "surface": ".codex/hooks.json", "state": "resolves",
            "detail": HOOK_REL} in payload["registrations"]


def test_a_hook_renamed_out_of_rotation_is_reported_dead_not_resolved(tmp_path):
    """The most ordinary way anyone disables a hook is renaming the file, and
    the first version of this check reported that as `✓ resolves`.

    The path scan stopped at the kit's own filename, so
    `…/pr_followup_hook.py.disabled` was truncated back to
    `…/pr_followup_hook.py` — which exists — and the registration invoking an
    absent file passed clean. That is #379's own failure mode manufactured by
    #379's fix, and worse than the silence it replaced: it asserts a specific
    falsehood confidently (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")  # the real file, still present
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}.disabled" --runtime claude',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert [(s.state, s.detail) for s in report.dead_registrations] == [
        ("broken", f"{HOOK_REL}.disabled")
    ]


def test_a_degenerately_nested_registration_does_not_abort_the_report(tmp_path):
    """Valid JSON, absurd shape. The parse is guarded and says so ("a diagnostic
    that dies on one malformed file tells the adopter nothing about the other
    thirty-six"); the walk after it recursed without a cap and raised
    `RecursionError` straight out of `inspect()` (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    payload = "[" * 10000 + "]" * 10000
    _write(root / ".codex" / "hooks.json", f'{{"hooks": {{"PostToolUse": {payload}}}}}')

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    # `unreadable`, not `unregistered`: the stack ran out inside `json.loads`
    # before the walk was reached, and reporting "no kit hook registered" for a
    # file this run could not read would be a claim it did not establish.
    assert [s.state for s in statuses if s.surface == ".codex/hooks.json"] == [
        "unreadable"
    ]


def test_an_installed_hook_beats_a_baseline_that_declares_it_declined(tmp_path):
    """Evidence order, not declaration order — the property the comment claims
    and nothing checked. A baseline is a record of a past decision; the file on
    disk is the current fact, and a stale declaration must not hide a working
    install (panel, correctness lens)."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "hooks" / "pre-push", "#!/bin/sh\n")
    _write(root / ".git" / "hooks" / "pre-push", "#!/bin/sh\n")
    target = root / "scripts" / "check_doc_budget.py"
    recorded = kit_doctor.sha256_of(target)
    baseline = _scoped_baseline({ENGINE: recorded})
    assert kit_doctor.PRE_PUSH_REL in baseline["not_installed"]

    report = _inspect(root, {ENGINE: recorded}, baseline)

    assert report.hooks_installed is True
    assert report.hooks_state == "installed"


def test_the_optional_overlay_is_silent_when_absent_and_read_when_present(tmp_path):
    """`.claude/settings.local.json` is optional by design, so its absence says
    nothing and must produce no line — while a registration written there is
    still the adopter's live registration and gets the same check. Both
    directions, because either alone passes with the surface deleted (panel,
    correctness lens)."""
    root = _fake_repo(tmp_path)
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude',
    )
    _write(root / HOOK_REL, "print('hook')\n")

    silent = kit_doctor.inspect_registrations(root, "scripts")
    assert [s for s in silent if s.surface == ".claude/settings.local.json"] == []

    _registration(
        root, ".claude/settings.local.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}.disabled" --runtime claude',
    )

    read = kit_doctor.inspect_registrations(root, "scripts")
    overlay = [s for s in read if s.surface == ".claude/settings.local.json"]
    assert [(s.state, s.detail) for s in overlay] == [("broken", f"{HOOK_REL}.disabled")]


def test_the_depth_cap_is_what_stops_a_deep_walk_not_the_json_parser(tmp_path):
    """The cap, exercised where it is actually reachable.

    A 10,000-deep document is stopped by `json.loads` exhausting its own
    recursion budget, so the test written for the cap passed with the cap
    REMOVED — the property was named by a test and pinned by nothing (panel,
    adversarial lens, delta round). At a depth the parser handles comfortably
    and the cap does not, the cap is the thing under test: without it the
    registration below is found and reported, with it the surface is reported
    `unreadable`, because a document this check declined to walk to the bottom
    was not measured."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    depth = kit_doctor._MAX_REGISTRATION_DEPTH * 3
    buried = json.dumps(
        {"type": "command", "command": f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}"'}
    )
    payload = "[" * depth + buried + "]" * depth
    _write(root / ".codex" / "hooks.json", f'{{"hooks": {{"PostToolUse": {payload}}}}}')

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    codex = [s for s in statuses if s.surface == ".codex/hooks.json"]

    assert [s.state for s in codex] == ["unreadable"]
    assert "nesting deeper than" in codex[0].detail


def test_an_adopters_own_script_is_not_judged_as_a_kit_hook(tmp_path):
    """`env_paths.py` ends in `paths.py`, which `KIT_OWNED` carries as a library
    module. A substring match over every kit-owned filename claimed it, so an
    adopter renaming *their own* unrelated tool got
    `✗ … NO SUCH FILE` and exit 1 — permanently, with nothing telling them why
    (panel, adversarial lens, delta round).

    Two independent fixes, both needed: library modules are not invocable and
    are out of the candidate set, and a name matches only at a path boundary."""
    root = _fake_repo(tmp_path)
    _registration(
        root, ".claude/settings.json",
        'python3 "$CLAUDE_PROJECT_DIR/scripts/my_hooks/env_paths.py" --their-flag',
    )
    # A second shape, and the one that pins the BOUNDARY half specifically: this
    # basename ends with a name the narrowed set still contains, so only the
    # boundary check keeps an adopter's derived hook from being judged as the
    # kit's. (A repo that forked the hook and kept a related name is the
    # ordinary way to end up here.)
    _registration(
        root, ".codex/hooks.json",
        'exec python3 "$root/scripts/my_pr_followup_hook.py" --runtime codex',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    codex = [s for s in report.registrations if s.surface == ".codex/hooks.json"]
    assert [s.state for s in codex] == ["unregistered"], (
        "a name matched mid-token: " f"{[(s.state, s.detail) for s in codex]}"
    )
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["unregistered"], (
        "an adopter's own script was judged as a kit hook: "
        f"{[(s.state, s.detail) for s in claude]}"
    )
    assert report.dead_registrations == []


def test_a_variable_that_merely_starts_with_root_is_not_expanded(tmp_path):
    """`$rootcause_dir` is one shell identifier — a shell resolves the longest
    name and never `$root` plus a literal remainder. A plain `str.replace`
    rewrote it to `<root>cause_dir` and then reported a hook that is right there
    as `broken` at a path nothing would ever build (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".codex/hooks.json",
        f'exec python3 "$rootcause_dir/{HOOK_REL}" --runtime codex',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    codex = [s for s in report.registrations if s.surface == ".codex/hooks.json"]

    assert any(s.state == "unresolvable" for s in codex)


def test_only_invocable_scripts_are_candidates_for_a_registration_match(tmp_path):
    """The candidate set, pinned directly — the adopter-script test above passes
    on the boundary check alone, so this half would otherwise be unpinned
    (checked by mutation: widening the set with the boundary check in place
    changes nothing). A library module is imported by an engine, never named in
    a hook command, so it has no business being matchable."""
    candidates = kit_doctor._invocable_kit_scripts()

    assert {"pr_followup_hook.py", "check_doc_budget.py"} <= candidates
    for library in ("kitconfig.py", "paths.py", "resolver.py", "__init__.py"):
        assert library not in candidates, f"{library} is imported, not invoked"


def test_role_test_basenames_are_not_candidates_for_a_registration_match():
    """#527's regression, reproduced and pinned: adding `scripts/tests/` to
    `KIT_OWNED` under role `test` (#493) leaked its 15 basenames unique to that
    role straight into `_invocable_kit_scripts()`, because the filter only
    excluded role `template`. A pytest module is collected and run by pytest,
    never named in a hook registration — so an adopter's OWN unrelated script
    sharing one of these names (`scripts/my_hooks/test_kit_doctor.py`, say)
    would have been misjudged as a kit file: `broken`, in
    `dead_registrations`, exit code 0->1 on an otherwise healthy install. This
    is `test_an_adopters_own_script_is_not_judged_as_a_kit_hook`'s class,
    reopened by the new role.

    Deliberately NOT asserting `conftest.py` here: that basename is ALSO
    contributed by `scripts/conftest.py` (role `engine`, tracked long before
    #493), so it remains a candidate regardless of this fix — asserting its
    absence would be a false pin.
    """
    candidates = kit_doctor._invocable_kit_scripts()
    test_only_basenames = {
        rel: PurePosixPath(rel).name
        for rel, role in kit_doctor.KIT_OWNED
        if role == "test" and "/lib/" not in rel
    }
    assert test_only_basenames, "no role-`test` KIT_OWNED entries — #493 regressed"
    for rel, name in test_only_basenames.items():
        if name == "conftest.py":
            continue
        assert name not in candidates, f"{rel}'s basename {name!r} leaked back into the candidate set"


def test_an_unparseable_registration_file_makes_the_run_non_green(tmp_path, capsys, monkeypatch):
    """A file that does not parse is worse than one broken path: EVERY
    registration in it is unmeasurable, and the runtime that must read the same
    JSON is no better placed than this check was.

    Reported `⚠` and exited 0 — a clean bill of health over a file nobody can
    account for, which is #379's own shape one level up (panel, correctness
    lens, delta round 2)."""
    root = _fake_repo(tmp_path)
    target = root / "scripts" / "check_doc_budget.py"
    _write(root / "kit-manifest.json", json.dumps(_manifest({ENGINE: kit_doctor.sha256_of(target)})))
    _write(root / ".claude" / "settings.json", "{not json at all")
    monkeypatch.chdir(root)

    # The file axis is clean, so a 1 can only have come from the registration.
    quiet = _inspect(root, {ENGINE: kit_doctor.sha256_of(target)}, None)
    assert (quiet.drifted, quiet.broken) == ([], [])

    assert kit_doctor.main(["--root", str(root)]) == 1
    assert "unreadable" in capsys.readouterr().out


def test_an_unwired_runtime_names_the_engines_dir_it_looked_under(tmp_path, capsys):
    """The `unregistered` detail was computed and reached `--json` only. It is
    the useful half of that line: an operator who sees no registration wants to
    know which engines path the check resolved before going to look."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / ".codex" / "hooks.json", json.dumps({"hooks": {}}))

    report = _inspect(root, {}, None)
    print(kit_doctor.render(report))

    assert "no kit hook registered (engines: scripts/devkit)" in capsys.readouterr().out


def test_a_repo_root_containing_a_space_does_not_break_the_path_scan(tmp_path):
    """A present, working hook reported `✗ NO SUCH FILE` with exit 1, for every
    checkout under a directory with a space in its name — `~/My Project`, a
    `OneDrive - Company` sync folder, a home directory built from a full name.

    The path scan ends a word at whitespace, so substituting the real root into
    the command BEFORE the split truncated the word at the root's own space. The kit's own quoting cannot help: the scan
    is a delimiter walk, not a shell parser. The root is now marked with a
    sentinel that survives tokenising and resolved afterwards (panel,
    adversarial lens, delta round 3)."""
    root = _fake_repo(tmp_path / "My Project")
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [(s.state, s.detail) for s in claude] == [("resolves", HOOK_REL)]
    assert report.dead_registrations == []


def test_inline_rev_parse_resolves_without_getting_lifecycle_semantics(tmp_path):
    """Path discovery can resolve this form without making it safe lifecycle
    wiring: a non-repository cwd turns the substitution into an empty root."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".codex/hooks.json",
        f'exec python3 "$(git rev-parse --show-toplevel)/{HOOK_REL}" --runtime codex',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    codex = [s for s in report.registrations if s.surface == ".codex/hooks.json"]

    assert [(s.state, s.detail) for s in codex] == [("resolves", HOOK_REL)]


@pytest.mark.parametrize(
    "label,command",
    [
        # The shape `init.sh` prints: the whole path inside one pair of quotes.
        ("fully quoted", 'python3 "$CLAUDE_PROJECT_DIR/{rel}" --runtime claude'),
        # Standard POSIX shell: quote only what needs it. Shell-identical to the
        # form above, and the delimiter walk cut it at the closing quote — the
        # remainder began with `/`, so it was read as an ABSOLUTE path, checked
        # at the filesystem root and reported NO SUCH FILE with exit 1 on a
        # healthy install (panel, adversarial lens, delta round 4).
        ("variable quoted, suffix bare", 'python3 "$CLAUDE_PROJECT_DIR"/{rel} --runtime claude'),
        # No quoting at all.
        ("unquoted", "python3 $CLAUDE_PROJECT_DIR/{rel} --runtime claude"),
        # Assignment form: the word is `HOOK=<path>`, and the path is what is
        # being asked about.
        ("assigned to a variable", 'HOOK="$CLAUDE_PROJECT_DIR/{rel}"; exec python3 "$HOOK"'),
    ],
)
def test_every_shell_quoting_of_the_same_path_reads_the_same(tmp_path, label, command):
    """Four spellings a shell treats identically. A check that disagrees with
    the shell about which characters bound a path will report a working hook as
    dead, and this one did — twice, at opposite ends of the token."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(root, ".claude/settings.json", command.format(rel=HOOK_REL))

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["resolves"], f"{label}: {claude}"


def test_a_quoted_absolute_path_containing_a_space_is_one_path(tmp_path):
    """The other half of the same lexing question, and not covered by the
    sentinel: an adopter who hardcoded an absolute path rather than using the
    runtime's placeholder. `shlex` keeps the quoted word whole; a walk that
    stops at any space cuts it."""
    root = _fake_repo(tmp_path / "My Project")
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".codex/hooks.json", f'exec python3 "{root}/{HOOK_REL}" --runtime codex'
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    codex = [s for s in report.registrations if s.surface == ".codex/hooks.json"]

    assert any(s.state == "resolves" and s.detail == HOOK_REL for s in codex)


def test_an_external_same_basename_hook_is_not_kit_lifecycle_wiring(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    external = tmp_path / "external" / "pr_followup_hook.py"
    _write(external, "print('adopter hook')\n")
    _registration(
        root,
        ".codex/hooks.json",
        f'exec python3 "{external}" --runtime codex',
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    codex = [s for s in statuses if s.surface == ".codex/hooks.json"]

    assert [(s.state, s.detail) for s in codex] == [("resolves", str(external))]


def test_leading_assignment_keeps_an_altered_lifecycle_string_unidentified(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    external = tmp_path / "external" / "pr_followup_hook.py"
    _write(external, "print('adopter hook')\n")
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = post_hook["command"].replace(
        "--runtime codex", "--runtime claude"
    )
    post_hook["command"] = f'DECOY="{external}"; ' + post_hook["command"]
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    assert not [
        s
        for s in statuses
        if s.state == "verified" and s.detail.startswith("pr_followup_hook.py")
    ]


def test_an_inert_kit_path_does_not_bless_an_external_invocation(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    external = tmp_path / "external" / "pr_followup_hook.py"
    _write(external, "print('adopter hook')\n")
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = (
        f'python3 "{external}" --runtime codex '
        f'"{root / HOOK_REL}"'
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    assert not [
        s
        for s in statuses
        if s.state == "verified" and s.detail.startswith("pr_followup_hook.py")
    ]


@pytest.mark.parametrize(
    ("event", "from_path", "to_path"),
    [
        (
            "SessionStart",
            '"$root/scripts/check_doc_budget.py"',
            '"$root/../../sibling/scripts/check_doc_budget.py"',
        ),
        (
            "PostToolUse",
            '"$root/scripts/hooks/pr_followup_hook.py"',
            '"$root/../../sibling/scripts/hooks/pr_followup_hook.py"',
        ),
    ],
)
def test_codex_lifecycle_paths_cannot_traverse_outside_the_repo(
    tmp_path, event, from_path, to_path
):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    handler = document["hooks"][event][0]["hooks"][0]
    handler["command"] = handler["command"].replace(from_path, to_path)
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    target = "check_doc_budget.py" if event == "SessionStart" else "pr_followup_hook.py"
    assert not [
        s
        for s in statuses
        if s.state == "verified" and s.detail.startswith(target)
    ]


def test_an_unbalanced_quote_is_reported_as_unjudged_not_as_absent(tmp_path):
    """A quote that never closes is a line a shell would refuse too, so the hook
    cannot fire — but this check has not established WHERE it points, so it says
    that rather than guessing. `unregistered` would be wrong (a registration is
    plainly there) and `broken` would claim a measurement never made; the run
    stays green and the operator gets a ⚠ naming the line.

    The rule is the module's own, shared with the parse guard and the depth cap:
    degrade, never abort."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json", f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL} --runtime claude'
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [(s.state, s.detail) for s in claude] == [
        ("unresolvable", "unbalanced quote — not lexable")
    ]
    assert report.dead_registrations == []


def test_a_single_quoted_placeholder_is_not_expanded(tmp_path):
    """Single quotes suppress expansion, so `'$CLAUDE_PROJECT_DIR/hook.py'` is a
    literal path containing a `$` — a registration that can never fire. Marking
    the root there anyway reported that dead hook as `resolves`, exit 0: the
    exact failure #379 exists to catch, produced by #379's own check (panel,
    adversarial lens).

    It reports `unresolvable` rather than `broken` because the `$` that remains
    is literal, and this check does not claim to know what a literal `$` path
    means to the adopter — but it is a ⚠ the operator can see, not a ✓."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json",
        f"python3 '$CLAUDE_PROJECT_DIR/{HOOK_REL}' --runtime claude",
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["unresolvable"]


def test_a_command_string_outside_a_hooks_block_is_not_a_registration(tmp_path):
    """`.claude/settings.json` carries `command` strings that are not hooks —
    `statusLine.command` is one. Judging those reported a repo with NO kit hook
    registered as having a BROKEN one, exit 1, and suppressed the line that
    would have said none was registered (panel, adversarial lens)."""
    root = _fake_repo(tmp_path)
    # The path is spelled EXACTLY as a kit script, so only the hooks-subtree
    # scoping can exclude it. An earlier version of this test used a
    # `.py.txt` log name, which the suffix allowlist added two rounds later
    # excluded on its own — so the test kept passing while pinning nothing, and
    # removing the scoping left the whole suite green (panel, adversarial lens,
    # round 8). That is this session's own pattern, in the test written to
    # prevent it.
    _write(
        root / ".claude" / "settings.json",
        json.dumps({"statusLine": {"type": "command",
                                   "command": "bash statusline.sh --budget scripts/check_doc_budget.py"}}),
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["unregistered"]
    assert report.dead_registrations == []


@pytest.mark.parametrize("log_name", ["pr_followup_hook.py.out.log", "pr_followup_hook.py.log"])
def test_an_argument_that_merely_contains_a_kit_script_name_is_not_the_hook(tmp_path, log_name):
    """A log path passed to an unrelated hook. The first spelling was excluded
    by a "one extra extension, no further dot" rule — which admitted the second,
    the commoner spelling of the same thing, and reported `✗ NO SUCH FILE` with
    exit 1 for a repo that had registered no kit hook at all (panel, adversarial
    lens, rounds 6 and 7). Both are somebody else's file."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "hooks" / "other.py", "print('theirs')\n")
    _registration(
        root, ".claude/settings.json",
        'python3 "$CLAUDE_PROJECT_DIR/scripts/hooks/other.py" ' f"--log-file /tmp/{log_name}",
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert report.dead_registrations == []


def test_a_hook_taken_out_of_rotation_is_still_reported_dead(tmp_path):
    """The other direction, so the exclusion above cannot pass by the check
    simply going blind to suffixes: a NAMED out-of-rotation suffix is still a
    registration pointing at a file that is not there."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}.disabled" --runtime claude',
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)

    assert [(s.state, s.detail) for s in report.dead_registrations] == [
        ("broken", f"{HOOK_REL}.disabled")
    ]


def test_a_name_mentioned_in_a_shell_comment_is_not_an_invocation(tmp_path):
    """A shell never runs what follows an unquoted `#` at a word start. The scan
    did, so a script named in an explanatory comment beside a hook line was read
    as an invocation — a phantom registration when the file exists, a dead one
    when it does not (panel, adversarial lens, round 7)."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _registration(
        root, ".claude/settings.json",
        f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude  '
        "# see also scripts/kit_doctor.py",
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [(s.state, s.detail) for s in claude] == [("resolves", HOOK_REL)]


@pytest.mark.parametrize(
    "target",
    [
        "scripts/check_doc_budget.py",
        "scripts/hooks/pr_followup_hook.py",
        "scripts/check_memory_budget.py",
    ],
)
@pytest.mark.parametrize(
    "prefix",
    [
        "echo ok # ",
        'root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
        '[ -n "$root" ] || exit 0; echo ok # ',
    ],
)
def test_codex_lifecycle_name_in_an_unrelated_comment_is_not_a_candidate(
    tmp_path, target, prefix
):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    document = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "^Bash$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{prefix}{target}",
                            "timeout": 10,
                        }
                    ],
                }
            ]
        }
    }
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    target_name = PurePosixPath(target).name
    semantic_failures = [
        s
        for s in statuses
        if s.state in ("misconfigured", "unverifiable")
        and target_name in s.detail
    ]

    assert semantic_failures == []


def test_inert_prefix_keeps_an_altered_lifecycle_string_on_the_path_axis(tmp_path):
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    document = _valid_codex_lifecycle_document()
    hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    hook["command"] = "exit 0; " + hook["command"]
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    semantic = [
        status
        for status in statuses
        if status.state in ("verified", "misconfigured", "unverifiable")
        and status.detail.startswith("pr_followup_hook.py")
    ]

    assert semantic == []
    assert any(status.state == "resolves" and status.detail == HOOK_REL for status in statuses)


def test_an_escaped_space_keeps_a_path_whole(tmp_path):
    """`\\ ` is how a shell carries a space without quotes. A split that ignores
    the escape cuts the path in half, which is the same defect as the two the
    quoting cases cover, by a third route."""
    root = _fake_repo(tmp_path / "My Project")
    _write(root / HOOK_REL, "print('hook')\n")
    escaped = str(root).replace(" ", "\\ ")
    _registration(
        root, ".codex/hooks.json", f"exec python3 {escaped}/{HOOK_REL} --runtime codex"
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    codex = [s for s in report.registrations if s.surface == ".codex/hooks.json"]

    assert any(s.state == "resolves" and s.detail == HOOK_REL for s in codex)


def test_a_shell_line_continuation_is_not_verified(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] = post_hook["command"].replace(
        "--runtime codex", "--runtime \\\n codex"
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


def test_adjacent_path_fragments_are_not_verified(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    session_hook = document["hooks"]["SessionStart"][0]["hooks"][0]
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    session_hook["command"] = session_hook["command"].replace(
        '"$root/scripts/check_doc_budget.py"', '"$root"/scripts/check_doc_budget.py'
    )
    post_hook["command"] = post_hook["command"].replace(
        '"$root/scripts/hooks/pr_followup_hook.py"',
        '"$root"/scripts/hooks/pr_followup_hook.py',
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "check_doc_budget.py")
    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


def test_an_escaped_literal_dollar_path_is_not_verified(tmp_path):
    root = _fake_repo(tmp_path / "$repo")
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    escaped_hook = str(root / HOOK_REL).replace("$", r"\$")
    post_hook["command"] = post_hook["command"].replace(
        '"$root/scripts/hooks/pr_followup_hook.py"', f'"{escaped_hook}"'
    )
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


def test_comment_text_makes_the_command_not_exact(tmp_path):
    root = _fake_repo(tmp_path)
    document = _valid_codex_lifecycle_document()
    post_hook = document["hooks"]["PostToolUse"][0]["hooks"][0]
    post_hook["command"] += " # explanatory $(inactive)"
    _write_codex_lifecycle_fixture(root, document)

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert not _has_verified_lifecycle(statuses, "pr_followup_hook.py")


def test_the_optional_overlay_is_silent_when_it_registers_nothing_too(tmp_path):
    """The `report_absent` flag gates two cases, not one: the overlay being
    absent, and the overlay being present with no kit hook in it. Both say
    nothing about the install, and only the first was described (panel,
    correctness lens) or tested."""
    root = _fake_repo(tmp_path)
    _write(
        root / ".claude" / "settings.local.json",
        json.dumps({"hooks": {"PostToolUse": [{"hooks": [
            {"type": "command", "command": "echo hi"}
        ]}]}}),
    )

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert [s for s in statuses if s.surface == ".claude/settings.local.json"] == []
    # The required surface with the same content is NOT silent, so this pins the
    # flag rather than a general rule about empty hook blocks.
    _write(
        root / ".claude" / "settings.json",
        json.dumps({"hooks": {"PostToolUse": [{"hooks": [
            {"type": "command", "command": "echo hi"}
        ]}]}}),
    )
    again = kit_doctor.inspect_registrations(root, "scripts")
    assert [s.state for s in again if s.surface == ".claude/settings.json"] == ["unregistered"]


def test_deep_nesting_outside_a_hooks_block_does_not_condemn_the_file(tmp_path):
    """The depth budget counted every node in the document, so an unrelated deep
    blob elsewhere in `.claude/settings.json` reported the whole surface
    `unreadable` — exit 1 — while the install's actual hook sat shallow and
    resolvable right beside it (panel, adversarial lens, round 8).

    The cap is a stack guard, not a verdict on material this check does not
    read: outside a `hooks` subtree it stops descending and says nothing."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    depth = kit_doctor._MAX_REGISTRATION_DEPTH + 1
    document = {
        "someAdopterKey": json.loads("[" * depth + "1" + "]" * depth),
        "hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command",
             "command": f'python3 "$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude'}
        ]}]},
    }
    _write(root / ".claude" / "settings.json", json.dumps(document))

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [(s.state, s.detail) for s in claude] == [("resolves", HOOK_REL)]
    assert report.dead_registrations == []


def test_an_escaped_dollar_is_a_literal_not_a_placeholder(tmp_path):
    """`\\$CLAUDE_PROJECT_DIR` is literal — a shell never expands it — so that
    registration looks for a directory named `$CLAUDE_PROJECT_DIR` and can only
    fail. Marking it anyway reported a dead hook as `resolves`, exit 0, which is
    #379's own failure asserted by #379's check (panel, adversarial lens).

    The word is tokenised before it is marked, and the escape was being consumed
    in between — so the marker never saw that the `$` was literal."""
    root = _fake_repo(tmp_path)
    _write(root / HOOK_REL, "print('hook')\n")
    _write(
        root / ".claude" / "settings.json",
        json.dumps({"hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command",
             "command": f'python3 "\\$CLAUDE_PROJECT_DIR/{HOOK_REL}" --runtime claude'}
        ]}]}}),
    )

    report = _inspect(root, {ENGINE: _sha("x")}, None)
    claude = [s for s in report.registrations if s.surface == ".claude/settings.json"]

    assert [s.state for s in claude] == ["unresolvable"], (
        f"an escaped placeholder was expanded: {[(s.state, s.detail) for s in claude]}"
    )


# ── The upgrade-workflow bootstrap block (#577) ──────────────────────────────
#
# The gap this pins: an upgrade executes Steps 2-3 from the copy of `upgrade.md`
# on disk and replaces that copy only in Step 4, so a drifted copy drives the
# whole run — and the paragraph telling the operator to check for that is inside
# the copy they do not have yet. `render` hoists this one file out of the drift
# list so the machinery does the reminding. Every assertion below is on the
# HOISTED block, never on the drift list, which carries the file either way.

_BOOTSTRAP_MARK = "THE UPGRADE WORKFLOW ITSELF HAS DRIFTED"
_UPGRADE_REL = "docs/agentic-dev-kit/workflows/upgrade.md"


def test_the_upgrade_workflow_constant_names_a_real_kit_owned_entry():
    """Derived from KIT_OWNED rather than spelled again, so a moved path cannot
    silently stop matching — the failure PRE_PUSH_REL's comment describes. An
    empty constant would make the block below unreachable while every
    `not in` assertion still passed, so the identity is pinned here."""
    assert kit_doctor.UPGRADE_WORKFLOW_REL == _UPGRADE_REL
    assert (_UPGRADE_REL, "workflow") in kit_doctor.KIT_OWNED


@pytest.mark.parametrize(
    "installed, recorded",
    [
        # STALE — installed matches the baseline, kit has moved on.
        ("installed", "installed"),
        # LOCALLY EDITED — installed matches neither; baseline says kit's copy.
        ("edited here", "kit"),
    ],
)
def test_a_drifted_upgrade_workflow_gets_its_own_block_above_the_drift_list(
    tmp_path, capsys, installed, recorded
):
    """Both split states, because the block must not be a STALE-only nicety:
    an adopter whose copy is LOCALLY EDITED is running the wrong prose just as
    surely, and #560 is about that state being the one this file's advice
    handles worst."""
    root = _fake_repo(tmp_path)
    _write(root / _UPGRADE_REL, installed)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root,
        _manifest({_UPGRADE_REL: _sha("kit")}),
        config,
        _baseline({_UPGRADE_REL: _sha(recorded)}),
    )
    assert next(f for f in report.files if f.path == _UPGRADE_REL).state in (
        "stale",
        "locally-edited",
    )
    print(kit_doctor.render(report))
    out = capsys.readouterr().out
    assert _BOOTSTRAP_MARK in out
    # Above the drift list, not inside it. The whole finding is that saying it
    # among the other drifted files is saying it where it does not help — so
    # position is the assertion, not mere presence.
    assert out.index(_BOOTSTRAP_MARK) < out.index("  files:")
    assert out.index(_BOOTSTRAP_MARK) < out.index(f"    · {_UPGRADE_REL}")


def test_the_block_does_not_prescribe_replacing_the_file():
    """#560's finding, kept out of the engine. `LOCALLY EDITED` is the state
    that can lose work, and a blanket "take the kit's copy" is wrong for it —
    so the block prescribes READING the fetched copy, which is safe in every
    state it fires on, and leaves the keep/replace question to the drift list."""
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        files=[
            kit_doctor.FileStatus(
                path=_UPGRADE_REL, role="workflow", state="locally-edited", detail=""
            )
        ],
    )
    # Scoped to the block itself — the rest of the report says "replace them"
    # about the drift list, which is correct there and would mask this.
    rendered = kit_doctor.render(report).splitlines()
    start = next(i for i, ln in enumerate(rendered) if _BOOTSTRAP_MARK in ln)
    end = next(i for i in range(start + 1, len(rendered)) if not rendered[i].strip())
    text = " ".join(rendered[start:end])
    # The one imperative the block issues, and it is safe in every state it
    # fires on.
    assert "Read the fetched kit's copy" in text
    # ...and the keep/replace decision is deferred rather than answered.
    assert "the drift list answers" in text
    # The prescriptive forms, none of which may appear. `replaces` on its own is
    # not among them: the block uses it to DESCRIBE what an upgrade does to this
    # file, which is the fact the warning rests on. An earlier version of this
    # test banned the substring and failed on that sentence — the ban has to be
    # on the instruction, not on the word.
    for prescription in (
        "take the kit's copy",
        "replace it",
        "replace them",
        "replace yours",
        "replace this file",
    ):
        assert prescription not in text, prescription


def test_an_unchanged_upgrade_workflow_renders_no_block(tmp_path, capsys):
    """The discriminating half. A block that fired unconditionally would satisfy
    every assertion above while pinning nothing — the shape the kit-bug nudge's
    pair of tests exists to rule out."""
    root = _fake_repo(tmp_path)
    _write(root / _UPGRADE_REL, "kit")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    target = root / _UPGRADE_REL
    report = kit_doctor.inspect(
        root, _manifest({_UPGRADE_REL: kit_doctor.sha256_of(target)}), config
    )
    assert next(f for f in report.files if f.path == _UPGRADE_REL).state == "unchanged"
    print(kit_doctor.render(report))
    assert _BOOTSTRAP_MARK not in capsys.readouterr().out


def test_another_drifted_file_does_not_raise_the_block(tmp_path, capsys):
    """The second discriminator, and the one that catches a block keyed on
    `report.drifted` being non-empty rather than on this file being in it."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "check_doc_budget.py", "edited here")
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(
        root, _manifest({"scripts/check_doc_budget.py": _sha("kit")}), config
    )
    assert report.drifted
    print(kit_doctor.render(report))
    assert _BOOTSTRAP_MARK not in capsys.readouterr().out


def test_an_absent_upgrade_workflow_renders_no_block(tmp_path, capsys):
    """A repo with no installed copy has nothing to be misled BY — it is reading
    the kit's copy already, so the warning would be false. `drifted` excludes
    every absent state, and this pins that the block inherits that boundary
    rather than re-deriving one."""
    root = _fake_repo(tmp_path)
    config = kit_doctor.load_config(root / "config" / "dev-model.yaml")
    report = kit_doctor.inspect(root, _manifest({_UPGRADE_REL: _sha("kit")}), config)
    assert next(f for f in report.files if f.path == _UPGRADE_REL).state in (
        "missing",
        "declined",
        "missing-required",
    )
    print(kit_doctor.render(report))
    assert _BOOTSTRAP_MARK not in capsys.readouterr().out


# ── cockpit command permissions (#606) ───────────────────────────────────
# `.claude/settings.json`'s `permissions` block had no test of any kind, which
# is half of what #606 reports: `kit_doctor` walked only the `hooks` subtrees,
# so an allow rule naming an engine path the adopter does not have was invisible
# to every check the kit runs.


def _settings_with_allow(root: Path, allow: list, *, surface: str = "settings.json") -> None:
    _write(root / ".claude" / surface, json.dumps({"permissions": {"allow": allow}}))


def _ungranted(statuses) -> list[tuple[str, str]]:
    return [(s.surface, s.detail) for s in statuses if s.state == "ungranted"]


def test_an_allow_rule_naming_the_wrong_engine_dir_is_reported_ungranted(tmp_path):
    """#606's reported case, end to end.

    The adopter vendored under `scripts/devkit/` and copied the kit's literal
    entry. The rule parses, it is well-formed, and it grants nothing — the path
    it names is not in this tree, so every `pr-watch` poll prompts.
    """
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py:*)"])

    statuses = kit_doctor.inspect_registrations(root, "scripts/devkit")

    assert _ungranted(statuses) == [(".claude/settings.json", "scripts/devkit/pr_watch.py")]


def test_an_allow_rule_at_the_configured_engine_dir_is_not_reported(tmp_path):
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/devkit/pr_watch.py:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts/devkit")) == []


def test_both_engine_spellings_together_are_not_reported(tmp_path):
    """The shape `init.sh` itself seeds into `config/claude-lane-settings.json`.

    That profile carries BOTH spellings deliberately, because `paths.engines` is
    the adopter's, so in every repo one of the two names a path that is not
    there. An adopter mirroring that shape in their cockpit settings must not be
    told something is wrong: one rule reaches the engine, which is the whole
    question. A check keyed on "does every rule resolve" would fail this, and
    would be #286's bug reopened against a healthy install.
    """
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(
        root,
        [
            "Bash(uv run scripts/pr_watch.py:*)",
            "Bash(uv run scripts/devkit/pr_watch.py:*)",
        ],
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts/devkit")) == []


def test_a_grant_in_the_local_overlay_covers_the_tracked_settings(tmp_path):
    """The overlay is a real place to put a grant — an adopter who keeps it out
    of version control is covered, and reporting the tracked file ungranted
    would be a falsehood about a repo whose prompts are already gone."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(gh pr view:*)"])
    _settings_with_allow(
        root, ["Bash(uv run scripts/pr_watch.py:*)"], surface="settings.local.json"
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_a_declined_engine_is_not_reported_ungranted(tmp_path):
    """Not installed is not ungranted. Telling an adopter who declined
    `pr_watch.py` to add a rule for it is advice to grant a command they do not
    have."""
    root = _fake_repo(tmp_path)
    _settings_with_allow(root, ["Bash(gh pr view:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_a_single_quoted_project_dir_does_not_count_as_a_grant(tmp_path):
    """Single quotes suppress expansion, so this rule names a LITERAL path with
    a dollar sign in it — the same dead-registration shape `_script_words`
    exists to keep visible. Counting it as a grant was this check's first bug:
    a tail comparison matched it (the string does end in the engine's path) and
    silenced the line for a rule no ordinary invocation reaches. What rejects it
    now is the equality comparison in `_granted_engine_names`, so this test is
    the one that keeps that comparison from being loosened back."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(
        root, ["Bash(uv run '$CLAUDE_PROJECT_DIR/scripts/pr_watch.py':*)"]
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


def test_a_double_quoted_project_dir_is_a_grant(tmp_path):
    """The other half of the pair above, so the single-quote test is pinning
    quoting semantics rather than merely a `$`."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(
        root, ['Bash(uv run "$CLAUDE_PROJECT_DIR/scripts/pr_watch.py":*)']
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


@pytest.mark.parametrize("rule", ["Bash", "Bash(*)"])
def test_a_whole_tool_bash_grant_covers_every_engine(tmp_path, rule):
    """Both spellings were measured against the client rather than assumed —
    `_bash_allow_prefixes` names the run. `Bash(:*)` used to be a third case
    here; it moved to the ungranted test below when the same run showed it
    grants nothing."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [rule])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_a_non_covering_rule_does_not_suppress_a_covering_one(tmp_path):
    """`Bash(:*)` reaches `_granted_engine_names` as the empty prefix rather than
    being dropped earlier, so it is evaluated beside its siblings.

    What this pins is that a prefix contributing nothing does not short-circuit
    the prefixes after it. Mutating the loop in `_granted_engine_names` to return
    early on a prefix that lexes to no words fails this test and no other
    behavioural one.

    **It does not pin the other direction**, and an earlier draft of this
    docstring claimed it did. Loosening `_grants_invocation`'s empty-words guard
    into a match-anything leaves this test passing, because the covering rule
    beside it grants the engine either way; the single-rule case
    `test_a_rule_that_does_not_reach_the_engine_leaves_it_ungranted[Bash(:*)]` is
    what catches that. Both readings were measured by mutation rather than
    argued — the wrong one survived a round of review as prose beside a passing
    test, which is how this file's own claims go stale."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(:*)", "Bash(uv run scripts/pr_watch.py:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


@pytest.mark.parametrize(
    "rule",
    [
        "Bash(uv run scripts/my_pr_watch.py:*)",  # an adopter's own longer name
        "Read(scripts/pr_watch.py)",  # a different tool entirely
        "Bash(uv run scripts/pr_watch.py:*",  # unbalanced — no shell would run it
        # Reads like a whole-tool grant and measurably is not: under this rule
        # the client refused a command no other rule named. It reaches here by
        # contributing an empty prefix, which lexes to no words.
        "Bash(:*)",
    ],
)
def test_a_rule_that_does_not_reach_the_engine_leaves_it_ungranted(tmp_path, rule):
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [rule])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"permissions": None},
        {"permissions": {}},
        {"permissions": {"allow": "Bash(uv run scripts/pr_watch.py:*)"}},
        {"permissions": {"allow": [None, 3, {"nested": "object"}]}},
        [1, 2, 3],
        "a bare string",
    ],
)
def test_a_malformed_permissions_block_degrades_instead_of_aborting(tmp_path, document):
    """Same rule the parse and the hook walk follow: adopter-supplied JSON that
    does not have the expected shape is reported, never raised."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _write(root / ".claude" / "settings.json", json.dumps(document))

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert _ungranted(statuses) == [(".claude/settings.json", "scripts/pr_watch.py")]


def test_permissions_are_judged_even_when_the_hooks_subtree_is_unreadable(tmp_path):
    """The permissions read happens before the hook walk's `continue` paths, so
    a document whose `hooks` subtree defeats the walk still gets its allow-list
    judged. Without that ordering the two checks share a failure they do not
    share a cause for."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    deep = {"permissions": {"allow": ["Bash(uv run scripts/pr_watch.py:*)"]}}
    node = deep
    for _ in range(kit_doctor._MAX_REGISTRATION_DEPTH + 5):
        node["hooks"] = {}
        node = node["hooks"]
    _write(root / ".claude" / "settings.json", json.dumps(deep))

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert "unreadable" in [s.state for s in statuses if s.surface == ".claude/settings.json"]
    assert _ungranted(statuses) == []


def test_no_claude_surface_at_all_reports_no_permission_finding(tmp_path):
    """A repo with no `.claude/` is not a Claude adoption. Reporting a missing
    grant there is the same over-claim as reporting a missing hook: the `absent`
    line already says the only true thing available."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")

    statuses = kit_doctor.inspect_registrations(root, "scripts")

    assert _ungranted(statuses) == []
    assert ("claude", ".claude/settings.json", "absent") in [
        (s.runtime, s.surface, s.state) for s in statuses
    ]


def test_an_ungranted_permission_does_not_fail_the_run(tmp_path):
    """A choice, not a defect. An operator who prefers to approve each poll is
    in a supported state, so this must stay out of `dead_registrations` and out
    of the exit code — the distinction #286 and #527 were both filed about."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(gh pr view:*)"])

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        registrations=statuses,
    )

    assert [s.state for s in statuses if s.state == "ungranted"]
    # The three properties `main` builds its exit code from. Asserting them
    # rather than calling `main` keeps this a statement about the CLASSIFICATION
    # — which is where a future state could wrongly join the gate — instead of
    # about a process exit that a dozen unrelated things also decide.
    assert report.dead_registrations == []
    assert report.drifted == []
    assert report.broken == []


def test_the_ungranted_line_names_the_path_a_rule_would_have_to_name(tmp_path):
    """The detail is the configured path rather than the basename, because that
    is the whole content of the advice: an adopter under `scripts/devkit/` who
    is shown `pr_watch.py` learns nothing they did not know."""
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [])

    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts/devkit",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        registrations=kit_doctor.inspect_registrations(root, "scripts/devkit"),
    )
    rendered = kit_doctor.render(report)

    assert "scripts/devkit/pr_watch.py" in rendered
    assert "nothing pre-approves it" in rendered
    # NOT "each invocation prompts", which the earlier wording said. A review
    # lens caught it: an engine named only in `deny` also gets this line, and
    # there the invocation is refused rather than prompted. What the check
    # actually established is that no allow rule reaches the path; what the
    # client does next depends on the rest of the config and the permission
    # mode, neither of which this check reads.
    assert "prompts" not in rendered


def test_an_exact_rule_without_the_wildcard_is_not_a_grant(tmp_path):
    """A `Bash(...)` rule without the `:*` suffix is an EXACT command match, so
    it pre-approves one argument-less invocation and not the poll shape.

    Measured at Claude Code 2.1.251 against the deny matcher, which shares this
    grammar: under `Bash(git status)`, `git status` was refused and
    `git status --short` was not. `pr-watch` polls with a PR number and flags
    that vary per call, so an exact rule leaves every poll stopping for
    approval — while the check, before this, reported the engine as covered.

    Raised by a review lens. The author's own earlier probe had asserted the
    opposite by testing THIS MODULE rather than the client.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


def test_the_prefix_form_of_the_same_rule_is_a_grant(tmp_path):
    """The pair to the test above, so it pins the `:*` suffix specifically
    rather than merely rejecting that rule text."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


@pytest.mark.parametrize("withholding", ["deny", "ask"])
def test_a_deny_or_ask_rule_is_not_read_as_a_grant(tmp_path, withholding):
    """This check answers whether an allow rule pre-approves the engine. `ask`
    withholds that approval and `deny` refuses it, so folding either in would
    make a rule that withholds permission read as one that confers it — and
    would silence the line for the adopter who most needs it, the one who denied
    the command on purpose.

    Note the reported line says "nothing pre-approves it" rather than naming a
    consequence: this fixture is exactly the case where the invocation is
    refused rather than prompted, so a line promising a prompt would be false
    here."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _write(
        root / ".claude" / "settings.json",
        json.dumps(
            {"permissions": {withholding: ["Bash(uv run scripts/pr_watch.py:*)"]}}
        ),
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


def test_a_deny_rule_does_not_cancel_an_allow_rule_in_this_report(tmp_path):
    """The other direction, stated so the pair above is not read as this check
    modelling precedence. It does not: it reports whether an allow rule REACHES
    the engine, and what a deny rule then does to that grant at runtime is the
    client's to decide and `/permissions` to show. Reporting `ungranted` here
    would be a claim about precedence this check has not measured."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _write(
        root / ".claude" / "settings.json",
        json.dumps(
            {
                "permissions": {
                    "allow": ["Bash(uv run scripts/pr_watch.py:*)"],
                    "deny": ["Bash(uv run scripts/pr_watch.py:*)"],
                }
            }
        ),
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_an_overlay_that_grants_nothing_does_not_erase_the_tracked_grant(tmp_path):
    """The other direction from the overlay test above, and the only one that
    actually pins the union.

    `REGISTRATION_SURFACES` walks `.claude/settings.json` before
    `.claude/settings.local.json`, so a grant found in the LATER surface
    survives even a plain assignment — that test passes either way, by
    coincidence of ordering. This is the shape that distinguishes them: the
    tracked file grants the engine, the overlay exists and contributes nothing,
    and only accumulating across surfaces keeps the earlier grant.

    Found by a review lens mutating `|=` to `=` and watching the suite stay
    green. Under that mutation an adopter whose tracked settings already grant
    the engine is told every poll will prompt, which is false and unactionable —
    the rule they would be told to add is the one they have.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py:*)"])
    _settings_with_allow(
        root, ["Bash(gh pr view:*)"], surface="settings.local.json"
    )

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_an_empty_overlay_does_not_erase_the_tracked_grant(tmp_path):
    """The degenerate form of the same shape: an overlay present but carrying no
    `permissions` block at all, which is what most adopters' overlays look
    like."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py:*)"])
    _write(root / ".claude" / "settings.local.json", json.dumps({}))

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_an_ungranted_line_carries_its_own_hand_written_footer(tmp_path):
    """The `ungranted` line states a gap in a file this check never writes, so
    it owes the reader where the fix comes from.

    Found by a review lens: the line could render alone — hooks fully wired,
    only the permission rule wrong — with no note that `init.sh` prints the
    corrected rule. The lens proposed adding `ungranted` to the existing
    registration footer's condition; that footer names `/hooks` as the
    authority and is about hook registrations, so this asserts the separate
    wording instead, and asserts the hook footer is NOT what appears.
    """
    root = _fake_repo(tmp_path, engines="scripts/devkit")
    _write(root / "scripts" / "devkit" / "pr_watch.py", "print('engine')\n")
    # BOTH runtimes wired, because the hook footer fires on `absent` too and
    # `.codex/hooks.json` missing is an `absent`. The first version of this test
    # wired only Claude and failed on exactly that — which is the point: without
    # a codex registration there is no fixture in which the `ungranted` footer
    # renders alone, and the negative assertion below would have been vacuous.
    _write(
        root / ".codex" / "hooks.json",
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": 'root="$(git rev-parse --show-toplevel 2>/dev/null)" '
                                    '|| exit 0; [ -n "$root" ] || exit 0; '
                                    '[ -z "${JOB_NAME:-}" ] || exit 0; '
                                    'uv run --script "$root/scripts/devkit/check_doc_budget.py" '
                                    "--quiet || true",
                                    "timeout": 15,
                                }
                            ]
                        }
                    ]
                }
            }
        ),
    )
    _write(
        root / ".claude" / "settings.json",
        json.dumps(
            {
                "permissions": {"allow": []},
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "uv run --script scripts/devkit/check_doc_budget.py --quiet",
                                }
                            ]
                        }
                    ]
                },
            }
        ),
    )
    statuses = kit_doctor.inspect_registrations(root, "scripts/devkit")
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts/devkit",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        registrations=statuses,
    )

    rendered = kit_doctor.render(report)

    assert "ungranted" in [s.state for s in statuses]
    assert "the cockpit allow-list is hand-written" in rendered
    assert "./init.sh prints the rule for your engines dir" in rendered
    assert "`/hooks` in a session is the authority" not in rendered


def test_the_ungranted_footer_is_not_printed_without_an_ungranted_line(tmp_path):
    """The footer follows the finding. Printed unconditionally it would tell an
    adopter whose allow-list is correct to go re-read `init.sh`."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py:*)"])
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        registrations=kit_doctor.inspect_registrations(root, "scripts"),
    )

    rendered = kit_doctor.render(report)

    assert "ungranted" not in [s.state for s in report.registrations]
    assert "the cockpit allow-list is hand-written" not in rendered


def test_dead_registrations_docstring_accounts_for_every_state_it_omits(tmp_path):
    """That docstring's stated purpose is enumerating its omissions ("The
    omissions are the point"), so a state it never names is a silent one.

    `ungranted` was missing for a round and a review lens caught it. This pins
    the property rather than the sentence: every state the module can put in a
    `RegistrationStatus` and that `dead_registrations` filters OUT must appear
    somewhere in that docstring.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(gh pr view:*)"])
    _write(root / ".codex" / "hooks.json", "{not json at all")

    statuses = kit_doctor.inspect_registrations(root, "scripts")
    report = kit_doctor.Report(
        kit_version_config=2,
        kit_version_manifest=2,
        engines_dir="scripts",
        engines_dir_ok=True,
        hooks_installed=True,
        narrative_rendered={},
        registrations=statuses,
    )
    docstring = type(report).dead_registrations.__doc__
    failing = {r.state for r in report.dead_registrations}
    omitted = {r.state for r in statuses} - failing

    assert omitted, "fixture produced no omitted state, so this asserts nothing"
    for state in sorted(omitted):
        assert state in docstring, (
            f"dead_registrations omits {state!r} without saying why; that "
            "docstring's whole point is enumerating its omissions"
        )


@pytest.mark.parametrize(
    "spelling",
    [
        "scripts/pr_watch.py",
        "./scripts/pr_watch.py",
        "scripts//pr_watch.py",
        "./scripts/./pr_watch.py",
        "scripts/../scripts/pr_watch.py",
    ],
)
def test_an_equivalent_spelling_of_the_engine_path_is_still_a_grant(tmp_path, spelling):
    """A rule that names the engine by any equivalent path grants it.

    Raised by a review bot against the `./` form, which does not actually
    reproduce — `pathlib` folds `./` and doubled slashes away at parse time, so
    those three were already granted before `_same_path` existed. `..` is the
    one that was not: it stayed lexically unequal and reported a false
    `ungranted` at a path that does run the engine. The parametrization keeps
    all five, so the already-working forms cannot silently regress while the
    fixed one is watched.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [f"Bash(uv run {spelling}:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_a_path_that_merely_ends_in_the_engine_name_is_not_a_grant(tmp_path):
    """Normalization must not become a suffix match. `_same_path` resolves both
    sides, and a resolved path under a different tree still differs — the
    property the equality comparison was chosen for in the first place."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run /elsewhere/scripts/pr_watch.py:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


def test_a_symlink_loop_in_the_named_path_yields_no_grant_and_no_crash(tmp_path):
    """A rule whose path runs through a symlink loop reports `ungranted` and
    does not bring the run down.

    **Which code path this takes depends on the Python running it, and that is
    the point rather than a caveat.** At Python 3.14.6 `resolve()` returns a loop
    path unresolved, so this exercises the ordinary not-equal comparison. At
    Python 3.12 — what CI runs — the same call raises `RuntimeError` through
    `pathlib.check_eloop`, so it exercises `_same_path`'s `except` clause
    instead. This test went red on CI while passing locally for exactly that
    reason, and it is what established that the clause is reachable at all after
    a local-only measurement had concluded it was not.

    The assertion is the same either way, which is what makes it worth keeping:
    whatever `resolve()` does with a pathological path, the operator sees no
    grant and no traceback.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    loop = root / "loop"
    loop.symlink_to(root / "loop2")
    (root / "loop2").symlink_to(loop)
    _settings_with_allow(root, ["Bash(uv run loop/pr_watch.py:*)"])

    # The assertion is that this returns at all, with the honest answer.
    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


@pytest.mark.parametrize(
    "rule",
    [
        "Bash(cat scripts/pr_watch.py:*)",
        "Bash(ruff check scripts/pr_watch.py:*)",
        "Bash(rm scripts/pr_watch.py:*)",
        "Bash(wc -l scripts/pr_watch.py:*)",
    ],
)
def test_a_rule_that_names_the_engine_without_running_it_is_not_a_grant(tmp_path, rule):
    """Naming the engine is not pre-approving it.

    Found by a review lens: the check asked whether ANY word in the rule
    resolved to the engine's path, so a rule that merely mentions the file —
    linting it, reading it, deleting it — reported the engine as covered while
    every poll would still stop for approval. False reassurance from the one
    check built to surface that friction, which is the dangerous direction.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [rule])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


@pytest.mark.parametrize("rule", ["Bash(uv:*)", "Bash(uv run:*)"])
def test_a_broader_rule_that_still_opens_the_invocation_is_a_grant(tmp_path, rule):
    """The other direction the old test got wrong, and the one that shows the
    error was the question rather than a missing case.

    `Bash(uv run:*)` pre-approves every poll and does not contain the engine's
    path at all, so a check that could only find grants NAMING the engine
    reported `ungranted` — telling an adopter to add a rule they already had in
    a broader form.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [rule])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == []


def test_a_rule_longer_than_the_invocation_is_not_a_general_grant(tmp_path):
    """`uv run <engine> --json` pre-approves some polls and not others —
    `--mark-seen` would still prompt — so reporting it as covering the workflow
    would be the same false reassurance in a smaller way."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv run scripts/pr_watch.py --json:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


def test_a_truncated_runner_token_is_not_a_grant(tmp_path):
    """Claude Code matches a Bash rule on argv TOKEN boundaries, so `uv r` is
    not a prefix of `uv run` — it is a different second token. The comparison
    here is token-wise for that reason rather than string-wise."""
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, ["Bash(uv r scripts/pr_watch.py:*)"])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]


@pytest.mark.parametrize(
    "rule",
    [
        "Bash( :*)",  # whitespace only
        "Bash(# uv run scripts/pr_watch.py:*)",  # a shell comment runs nothing
    ],
)
def test_a_rule_whose_prefix_lexes_to_nothing_is_not_a_grant(tmp_path, rule):
    """An empty token list is vacuously a prefix of anything, so without an
    explicit guard a rule carrying no command at all would grant every engine.

    Reachable rather than theoretical: whitespace survives the `:*` split, and
    `_script_words` drops everything after an unquoted `#` at a word start
    because no shell would run it. Found by mutation — removing the guard left
    the whole permissions suite green.
    """
    root = _fake_repo(tmp_path)
    _write(root / "scripts" / "pr_watch.py", "print('engine')\n")
    _settings_with_allow(root, [rule])

    assert _ungranted(kit_doctor.inspect_registrations(root, "scripts")) == [
        (".claude/settings.json", "scripts/pr_watch.py")
    ]
