"""Fresh-repository adoption fixtures: what a new adopter receives (#878).

Phase 6 item 6. Each adopter below takes the supported fresh-install path — the kit's
tracked files copied into a new repository, then `./init.sh` — and the resulting
install is checked against `docs/agentic-dev-kit/runtime-parity.md`: its workflow
inventory, its `adoption` block, and the adapters `scripts/lib/runtime_adapters.py`
renders from `scripts/lib/adapter_templates/`.

The three adopters differ in the runtime they answer for `runtime.default` and in the
runtime files they already keep before the kit arrives:

- **codex-only** answers `codex` and keeps its own Codex project config and a skill;
- **claude-only** answers `claude` and keeps its own local Claude settings and a command;
- **dual-runtime** answers `claude` and keeps both.

Those own files are ones the kit does not ship. A repository that already holds its own
copy of a file the kit ships is the case `/adopt` exists for: the template route
overwrites it, as the README warns.

`other_runtime: installed` in the declaration is #878 step 3's answer, decided by the
operator on 2026-10-01: an adopter receives both runtimes' files whatever
`runtime.default` names. So the expected footprint here never depends on the adopter's
runtime, and an install that left out the runtime an adopter does not run fails that
adopter's fixture.

Kit source only: the install is built from the kit's own tracked files, which an
adopter's tree is not.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest
import yaml
from _repo_layout import engine_dir, find_repo_root
from conftest import require_kit_source

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)

PARITY_DOC = "docs/agentic-dev-kit/runtime-parity.md"
CONFIG = "config/dev-model.yaml"

pytestmark = pytest.mark.kit_repo_only("init.sh", PARITY_DOC, "docs/templates/AGENTS.md.tmpl")

sys.path.insert(0, str(ENGINE_DIR / "lib"))
import runtime_adapters  # noqa: E402

RUNTIMES = runtime_adapters.RUNTIMES

# The kit's own working records and retained evidence trees: most of the tracked
# bytes, and neither a runtime surface nor anything `init.sh` reads.
NOT_COPIED = ("saved_plans/",)

# The directories an install may hold only declared files in, as the parity doc's
# *Adoption footprint* names them. Fixed rather than derived from the declaration: once
# a runtime's last declared surface was removed, a derived set dropped that directory
# from the scan, and only the negative control below noticed (#919).
RUNTIME_DIRS = (".claude", ".agents", ".codex")

# How `init.sh`'s closing line tells each runtime to start, per the README's adapter
# table.
SESSION_START = {"claude": "/session-start", "codex": "$session-start"}


@dataclass(frozen=True)
class Adopter:
    name: str
    runtime: str
    # Files the repository already holds when the kit arrives, by path.
    own: dict[str, str]


CODEX_OWN = {
    ".codex/config.toml": "# This repository's own Codex project config.\n[features]\nhooks = true\n",
    ".agents/skills/release/SKILL.md": (
        "---\nname: release\ndescription: Cut a release of this project.\n---\n\n"
        "Tag the release and publish it.\n"
    ),
}
CLAUDE_OWN = {
    ".claude/settings.local.json": '{"permissions": {"allow": ["Bash(make release)"]}}\n',
    ".claude/commands/release.md": (
        "---\ndescription: Cut a release of this project.\n---\n\n"
        "Tag the release and publish it.\n"
    ),
}
ADOPTERS = (
    Adopter("codex-only", "codex", CODEX_OWN),
    Adopter("claude-only", "claude", CLAUDE_OWN),
    Adopter("dual-runtime", "claude", {**CODEX_OWN, **CLAUDE_OWN}),
)


@dataclass(frozen=True)
class Install:
    adopter: Adopter
    root: Path
    stdout: str


def _declaration() -> dict:
    text = (REPO_ROOT / PARITY_DOC).read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{PARITY_DOC} has no front matter"
    _, frontmatter, _ = text.split("---", 2)
    return yaml.safe_load(frontmatter)


def _kit_files() -> list[str]:
    """The kit's tracked files: what the template route hands a new repository.

    `cp -r` from a checkout would also carry `.git/`, the state sandbox and whatever
    is untracked, none of which a new repository is meant to receive.
    """
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return [
        rel
        for rel in listed.split("\0")
        if rel and not rel.startswith(NOT_COPIED) and (REPO_ROOT / rel).is_file()
    ]


def _env(ceiling: Path) -> dict[str, str]:
    # Isolated from the developer's git configuration, and from any repository
    # enclosing the temporary directory, as `test_init_sh.py`'s `_env` explains.
    env = dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_CEILING_DIRECTORIES=str(ceiling),
    )
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _install(base: Path, adopter: Adopter, kit_files: list[str]) -> Install:
    root = base / adopter.name
    env = _env(base)
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env, capture_output=True)
    for rel, body in adopter.own.items():
        assert rel not in kit_files, f"{adopter.name}: own file {rel} is a kit path the copy would overwrite"
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding="utf-8")

    for rel in kit_files:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, root / rel)

    # The adopter's answer to `init.sh`'s runtime prompt. With no terminal attached
    # `init.sh` keeps each current value and stamps it back, so the answer is set in
    # the config it will show as the default.
    config = root / CONFIG
    text, answered = re.subn(
        r"(?m)^(  default: )claude\b", rf"\g<1>{adopter.runtime}", config.read_text(encoding="utf-8")
    )
    assert answered == 1, f"{CONFIG} no longer carries one runtime.default to answer"
    config.write_text(text, encoding="utf-8")

    result = subprocess.run(
        ["sh", "init.sh"],
        cwd=root,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        env=env,
    )
    assert result.returncode == 0, f"{adopter.name}: init.sh failed\n{result.stdout}\n{result.stderr}"
    return Install(adopter, root, result.stdout)


@pytest.fixture(scope="module")
def installs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Install]:
    require_kit_source()
    base = tmp_path_factory.mktemp("adoption")
    kit_files = _kit_files()
    return {adopter.name: _install(base, adopter, kit_files) for adopter in ADOPTERS}


def _interfaces(declaration: dict) -> set[str]:
    """Each Codex skill's interface file, beside the SKILL.md the inventory names."""
    return {
        str(PurePosixPath(entry["codex"]).parent / "agents" / "openai.yaml")
        for entry in declaration["workflow_contract"]
        if entry["codex"]
    }


def _runtime_files(declaration: dict) -> dict[str, set[str]]:
    """Every file the declaration assigns to each runtime: adapters and surfaces."""
    files: dict[str, set[str]] = {runtime: set() for runtime in RUNTIMES}
    for entry in declaration["workflow_contract"]:
        for runtime in RUNTIMES:
            if entry[runtime]:
                files[runtime].add(entry[runtime])
    files["codex"].update(_interfaces(declaration))
    for runtime in RUNTIMES:
        files[runtime].update(declaration["adoption"]["surfaces"][runtime])
    return files


def _runtime_config(text: str) -> dict[str, dict[tuple[str, ...], str]]:
    """Each registered runtime's config leaves, by path, with their values.

    A leaf is the runtime's when its path passes through a key named for the
    runtime, as in `review.fallback_commands.codex`, or one prefixed with it, as in
    `parallel.codex_headless_command`.
    """
    config = yaml.load(text, Loader=yaml.BaseLoader)
    runtimes = set(config["runtime"]["launchers"])
    leaves: dict[str, dict[tuple[str, ...], str]] = {runtime: {} for runtime in runtimes}

    def walk(node: object, path: tuple[str, ...]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, (*path, key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, (*path, str(index)))
        else:
            for runtime in runtimes:
                if any(key == runtime or key.startswith(f"{runtime}_") for key in path):
                    leaves[runtime][path] = node

    walk(config, ())
    return leaves


def _assert_install_matches_declaration(install: Install, declaration: dict) -> None:
    adopter, root = install.adopter, install.root
    adoption = declaration["adoption"]
    assert adoption["other_runtime"] == "installed", (
        f"{PARITY_DOC} records other_runtime: {adoption['other_runtime']!r}. These fixtures "
        "pin `installed`, #878 step 3's answer; a different answer needs fixtures that "
        "pin it, in the same change."
    )

    # Step 3's answer: the footprint is both runtimes' whatever runtime.default names.
    runtime_files = _runtime_files(declaration)
    footprint = set().union(*runtime_files.values())
    shared = set(adoption["surfaces"]["shared"]) | {
        entry["shared"] for entry in declaration["workflow_contract"]
    }
    for rel in sorted(footprint | shared):
        assert (root / rel).is_file(), f"{adopter.name}: declared {rel} is missing from the install"

    # Nothing undeclared lands in a runtime's own directory.
    present = {
        path.relative_to(root).as_posix()
        for top in RUNTIME_DIRS
        for path in (root / top).rglob("*")
        if not path.is_dir()
    }
    expected = {
        rel for rel in footprint | set(adopter.own) if PurePosixPath(rel).parts[0] in RUNTIME_DIRS
    }
    assert present == expected, (
        f"{adopter.name}: runtime directories hold undeclared {sorted(present - expected)} "
        f"and lack {sorted(expected - present)}"
    )

    # Each adapter is its rendered template, framed with the kit's own metadata.
    for entry in declaration["workflow_contract"]:
        for runtime in RUNTIMES:
            rel = entry[runtime]
            if not rel:
                continue
            metadata = runtime_adapters._frontmatter((REPO_ROOT / rel).read_text(encoding="utf-8"))
            rendered = runtime_adapters.render_adapter(
                runtime, entry["name"], metadata["description"], entry["shared"]
            )
            assert (root / rel).read_text(encoding="utf-8") == rendered, (
                f"{adopter.name}: {rel} is not the adapter rendered from its template"
            )

    # Entry points are rendered from their templates. Every other surface, and each
    # skill's interface file, arrives unchanged by the install. That compares the
    # install with the tree it was copied from, so it catches `init.sh` altering a
    # surface, not a change to the kit's own copy: each surface's content is pinned by
    # the tests of the file itself, such as the shipped-registration references.
    templates = REPO_ROOT / "docs" / "templates"
    surfaces = {rel for paths in adoption["surfaces"].values() for rel in paths}
    for rel in sorted(surfaces | _interfaces(declaration)):
        if (templates / f"{rel}.tmpl").is_file():
            text = (root / rel).read_text(encoding="utf-8")
            assert text.startswith(f"<!-- Rendered from docs/templates/{rel}.tmpl"), (
                f"{adopter.name}: {rel} was not rendered from its template"
            )
            assert "{{" not in text, f"{adopter.name}: {rel} keeps an unrendered template token"
        else:
            assert (root / rel).read_bytes() == (REPO_ROOT / rel).read_bytes(), (
                f"{adopter.name}: {rel} differs from the kit's"
            )
    # The matrix's *Repository instructions* row: Claude reads the shared contract
    # through CLAUDE.md's import.
    claude_md = (root / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert "@AGENTS.md" in claude_md, f"{adopter.name}: CLAUDE.md does not import AGENTS.md"

    for rel, body in adopter.own.items():
        assert (root / rel).read_text(encoding="utf-8") == body, (
            f"{adopter.name}: the install changed the adopter's own {rel}"
        )

    # Config: the adopter's answer, and both runtimes' keys as the kit ships them.
    installed = (root / CONFIG).read_text(encoding="utf-8")
    assert yaml.safe_load(installed)["runtime"]["default"] == adopter.runtime
    shipped = _runtime_config((REPO_ROOT / CONFIG).read_text(encoding="utf-8"))
    received = _runtime_config(installed)
    assert set(shipped) >= set(RUNTIMES)
    for runtime in RUNTIMES:
        assert shipped[runtime], f"the kit ships no {runtime} config keys to compare"
        got = received.get(runtime, {})
        changed = sorted(
            path for path in set(shipped[runtime]) | set(got) if shipped[runtime].get(path) != got.get(path)
        )
        assert not changed, f"{adopter.name}: {runtime} config differs from the kit's at {changed}"

    # `init.sh` tells every adopter both registrations, and how to start its runtime.
    for runtime in RUNTIMES:
        assert f'pr_followup_hook.py" --runtime {runtime}' in install.stdout, (
            f"{adopter.name}: init.sh did not print the {runtime} PR follow-through registration"
        )
    closing = install.stdout.rstrip().splitlines()[-1]
    assert SESSION_START[adopter.runtime] in closing, (
        f"{adopter.name}: init.sh closed with {closing!r}"
    )
    for runtime, invocation in SESSION_START.items():
        if runtime != adopter.runtime:
            assert invocation not in closing, f"{adopter.name}: init.sh closed with {closing!r}"


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_a_fresh_install_receives_the_declared_footprint(installs, name):
    _assert_install_matches_declaration(installs[name], _declaration())


def test_the_declaration_names_every_runtime_and_real_files():
    require_kit_source()
    declaration = _declaration()
    surfaces = declaration["adoption"]["surfaces"]
    assert set(surfaces) == {"shared", *RUNTIMES}
    declared = [rel for paths in surfaces.values() for rel in paths]
    assert len(declared) == len(set(declared)), "a surface is declared twice"
    tracked = set(_kit_files())
    assert set(declared) <= tracked, f"declared but not shipped: {sorted(set(declared) - tracked)}"
    inventory = {
        entry[key]
        for entry in declaration["workflow_contract"]
        for key in ("shared", *RUNTIMES)
        if entry[key]
    }
    assert not set(declared) & inventory, "a surface repeats the workflow inventory"


# The acceptance half of #878: each of these must fail the check above.


@contextmanager
def _replaced(path: Path, content: bytes | None) -> Iterator[None]:
    """Replace or remove one file for the duration, then put the original back."""
    original = path.read_bytes() if path.is_file() else None
    try:
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        yield
    finally:
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)


def _copy(install: Install, tmp_path: Path) -> Install:
    root = tmp_path / install.adopter.name
    shutil.copytree(install.root, root, symlinks=True)
    return Install(install.adopter, root, install.stdout)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_removing_any_declared_file_fails(installs, name, tmp_path):
    install = _copy(installs[name], tmp_path)
    declaration = _declaration()
    footprint = set().union(*_runtime_files(declaration).values())
    shared = set(declaration["adoption"]["surfaces"]["shared"]) | {
        entry["shared"] for entry in declaration["workflow_contract"]
    }
    _assert_install_matches_declaration(install, declaration)
    for rel in sorted(footprint | shared):
        with _replaced(install.root / rel, None), pytest.raises(AssertionError, match="missing"):
            _assert_install_matches_declaration(install, declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_an_undeclared_runtime_file_fails(installs, name, tmp_path):
    install = _copy(installs[name], tmp_path)
    declaration = _declaration()
    for rel in (
        ".claude/commands/undeclared.md",
        ".claude/rules/undeclared.md",
        ".agents/skills/undeclared/SKILL.md",
        ".codex/undeclared.json",
    ):
        with _replaced(install.root / rel, b"undeclared\n"), pytest.raises(
            AssertionError, match="undeclared"
        ):
            _assert_install_matches_declaration(install, declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_a_runtime_directory_stays_scanned_once_its_last_surface_is_undeclared(installs, name):
    declaration = _declaration()
    assert declaration["adoption"]["surfaces"]["codex"] == [".codex/hooks.json"], (
        "this test removes Codex's only declared surface; re-pick the surface if that changed"
    )
    declaration["adoption"]["surfaces"]["codex"] = []
    with pytest.raises(AssertionError, match=r"undeclared \['\.codex/hooks\.json'\]"):
        _assert_install_matches_declaration(installs[name], declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_an_adapter_that_is_not_its_rendered_template_fails(installs, name, tmp_path):
    install = _copy(installs[name], tmp_path)
    declaration = _declaration()
    for entry in declaration["workflow_contract"]:
        for runtime in RUNTIMES:
            if not entry[runtime]:
                continue
            path = install.root / entry[runtime]
            appended = path.read_bytes() + b"\nThe shared workflow is optional advice.\n"
            with _replaced(path, appended), pytest.raises(AssertionError, match="rendered"):
                _assert_install_matches_declaration(install, declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_a_changed_surface_or_own_file_fails(installs, name, tmp_path):
    install = _copy(installs[name], tmp_path)
    declaration = _declaration()
    surfaces = {rel for paths in declaration["adoption"]["surfaces"].values() for rel in paths}
    rendered = {rel for rel in surfaces if (REPO_ROOT / "docs" / "templates" / f"{rel}.tmpl").is_file()}
    assert rendered, "no declared surface is rendered from a template"
    for rel in sorted((surfaces - rendered) | _interfaces(declaration)):
        path = install.root / rel
        with _replaced(path, path.read_bytes() + b"\n"), pytest.raises(
            AssertionError, match="differs from the kit's"
        ):
            _assert_install_matches_declaration(install, declaration)
    for rel in sorted(rendered):
        # Left as the kit's own copy, which is what `init.sh` renders over.
        with _replaced(install.root / rel, (REPO_ROOT / rel).read_bytes()), pytest.raises(
            AssertionError, match="rendered"
        ):
            _assert_install_matches_declaration(install, declaration)
        # Rendered, but with a token left in.
        path = install.root / rel
        with _replaced(path, path.read_bytes() + b"\n{{PROJECT_NAME}}\n"), pytest.raises(
            AssertionError, match="unrendered template token"
        ):
            _assert_install_matches_declaration(install, declaration)
    for rel in install.adopter.own:
        path = install.root / rel
        with _replaced(path, path.read_bytes() + b"\n"), pytest.raises(
            AssertionError, match="adopter's own"
        ):
            _assert_install_matches_declaration(install, declaration)
    claude_md = install.root / "CLAUDE.md"
    without_import = claude_md.read_text(encoding="utf-8").replace("@AGENTS.md\n", "")
    with _replaced(claude_md, without_import.encode("utf-8")), pytest.raises(
        AssertionError, match="import"
    ):
        _assert_install_matches_declaration(install, declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_a_dropped_or_changed_runtime_config_key_fails(installs, name, tmp_path):
    install = _copy(installs[name], tmp_path)
    declaration = _declaration()
    config = install.root / CONFIG
    text = config.read_text(encoding="utf-8")
    for runtime in RUNTIMES:
        for pattern in (
            # A map keyed by the runtime, and a flat key prefixed with it.
            rf'(?m)^    {runtime}: "/[a-z-]*review"\n',
            rf"(?m)^  {runtime}_headless_command: .*\n",
        ):
            dropped, count = re.subn(pattern, "", text)
            assert count == 1, f"{CONFIG} no longer matches {pattern!r} once"
            with _replaced(config, dropped.encode("utf-8")), pytest.raises(
                AssertionError, match=f"{runtime} config differs"
            ):
                _assert_install_matches_declaration(install, declaration)
        # The key kept, its value changed: the same leaves, so only the values differ.
        changed, count = re.subn(
            rf"(?m)^(  {runtime}_headless_command: \[{runtime}, )[^\],]+\]$", r"\g<1>changed]", text
        )
        assert count == 1, f"{CONFIG} no longer carries one {runtime}_headless_command list"
        with _replaced(config, changed.encode("utf-8")), pytest.raises(
            AssertionError, match=f"{runtime} config differs"
        ):
            _assert_install_matches_declaration(install, declaration)
    answered = re.sub(r"(?m)^(  default: )\w+", r"\g<1>none", text, count=1)
    with _replaced(config, answered.encode("utf-8")), pytest.raises(AssertionError):
        _assert_install_matches_declaration(install, declaration)


@pytest.mark.parametrize("name", [adopter.name for adopter in ADOPTERS])
def test_init_output_without_a_registration_or_with_the_wrong_invocation_fails(installs, name):
    install = installs[name]
    declaration = _declaration()
    for runtime in RUNTIMES:
        line = f'pr_followup_hook.py" --runtime {runtime}'
        silent = Install(install.adopter, install.root, install.stdout.replace(line, ""))
        with pytest.raises(AssertionError, match=f"{runtime} PR follow-through"):
            _assert_install_matches_declaration(silent, declaration)
    for runtime, invocation in SESSION_START.items():
        if runtime == install.adopter.runtime:
            continue
        wrong = Install(
            install.adopter,
            install.root,
            install.stdout.rstrip() + f"\nYou're set — {invocation} next.\n",
        )
        with pytest.raises(AssertionError, match="closed with"):
            _assert_install_matches_declaration(wrong, declaration)


def test_a_different_step_3_answer_needs_its_own_fixtures(installs):
    declaration = _declaration()
    declaration["adoption"]["other_runtime"] = "omitted"
    with pytest.raises(AssertionError, match="pin `installed`"):
        _assert_install_matches_declaration(installs["codex-only"], declaration)
