"""The lite profile's workflow docs: shared clauses pinned, shell blocks executed (#1320).

The lite docs under `docs/agentic-dev-kit/lite/` are separate files so a
lite adopter can read them without the full kit's machinery. The clauses both
profiles keep are wrapped in `<!-- lite:begin <id> -->` / `<!-- lite:end <id> -->`
markers in both files, and these tests fail when the two copies differ, so a change
to one cannot silently leave the other behind (the drift #243 and #273 describe).
Whitespace is collapsed before comparing, so indentation and line wrapping may
differ between the two files; the words may not. The lite review's two lens stances
are pinned to `review.fallback_panel.lenses` in `config/dev-model.yaml` the same way.

The second half runs the lite docs' shell blocks, taken from the docs as written,
against fixture repositories: the `base` blocks on a readable and an unreadable
`HEAD`, the wrap-up's commit-split check, and the risk tier's declared-path check.
Last, `adopt.md`'s lite copy block installs into a fresh repository, and
`kit_doctor.py` records and reports that install as intact.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))
WORKFLOWS = REPO_ROOT / "docs/agentic-dev-kit/workflows"
LITE = REPO_ROOT / "docs/agentic-dev-kit/lite"

# Each lite doc, the full doc whose marked clauses it must carry, and the ids both
# must mark. The ids are pinned here, not read from the docs, so removing a marker
# pair from both files fails rather than quietly shrinking what is guarded.
PAIRS = {
    "lite-session-start.md": ("session-start.md", {"source-failure", "dont-invent-work"}),
    "lite-wrap-up.md": (
        "wrap-up.md",
        {
            "handoff-content",
            "record-prose",
            "park-conditions",
            "stage-by-name",
            "completion-inference",
            "no-working-detail",
        },
    ),
}

MARKER = re.compile(r"<!-- lite:(begin|end) ([a-z0-9-]+) -->")


def _blocks(path: Path) -> dict[str, str]:
    """Return each marked block's text, refusing malformed, nested or repeated markers."""
    text = path.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    open_id: str | None = None
    start = 0
    for m in MARKER.finditer(text):
        kind, block_id = m.groups()
        if kind == "begin":
            assert open_id is None, f"{path}: {block_id!r} begins inside {open_id!r}"
            assert block_id not in blocks, f"{path}: {block_id!r} is marked twice"
            open_id, start = block_id, m.end()
        else:
            assert open_id == block_id, f"{path}: end {block_id!r} does not close {open_id!r}"
            blocks[block_id] = text[start : m.start()]
            open_id = None
    assert open_id is None, f"{path}: {open_id!r} is never closed"
    return blocks


def _normalise(text: str) -> str:
    return " ".join(text.split())


def _compare(full_path: Path, lite_path: Path, expected: set[str]) -> None:
    """Fail unless both docs mark exactly `expected` and every marked clause matches."""
    full = _blocks(full_path)
    lite = _blocks(lite_path)
    assert set(full) == expected, f"{full_path.name} marks {sorted(full)}, expected {sorted(expected)}"
    assert set(lite) == expected, f"{lite_path.name} marks {sorted(lite)}, expected {sorted(expected)}"
    for block_id in sorted(expected):
        assert _normalise(lite[block_id]) == _normalise(full[block_id]), (
            f"{lite_path.name}: clause {block_id!r} differs from {full_path.name}"
        )


@pytest.mark.parametrize("lite_name", sorted(PAIRS))
def test_lite_doc_carries_every_marked_full_clause_unchanged(lite_name: str) -> None:
    full_name, expected = PAIRS[lite_name]
    _compare(WORKFLOWS / full_name, LITE / lite_name, expected)


def test_lite_review_marks_exactly_the_two_lens_stances() -> None:
    assert set(_blocks(LITE / "lite-review.md")) == {"correctness-focus", "adversarial-focus"}


@pytest.mark.parametrize("lens", ["correctness", "adversarial"])
def test_lite_review_carries_the_configured_lens_focus(lens: str) -> None:
    """The same-context review takes the correctness stance and the risk tier the adversarial one."""
    config = yaml.safe_load((REPO_ROOT / "config/dev-model.yaml").read_text(encoding="utf-8"))
    lenses = config["review"]["fallback_panel"]["lenses"]
    (focus,) = [entry["focus"] for entry in lenses if entry["name"] == lens]
    assert _normalise(_blocks(LITE / "lite-review.md")[f"{lens}-focus"]) == _normalise(focus)


# The guard's own branches, against fixtures, so each refusal is shown to fire.


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_compare_rejects_a_clause_that_differs(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep this\n<!-- lite:end x -->\n")
    lite = _write(tmp_path / "lite.md", "<!-- lite:begin x -->\n  keep   that\n<!-- lite:end x -->\n")
    with pytest.raises(AssertionError, match="clause 'x' differs"):
        _compare(full, lite, {"x"})
    _write(lite, "<!-- lite:begin x -->\n  keep\n   this\n<!-- lite:end x -->\n")
    _compare(full, lite, {"x"})


def test_compare_rejects_a_marker_pair_removed_from_both_docs(tmp_path: Path) -> None:
    both = "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n"
    full = _write(tmp_path / "full.md", both)
    lite = _write(tmp_path / "lite.md", both)
    with pytest.raises(AssertionError, match="expected"):
        _compare(full, lite, {"x", "y"})


def test_compare_rejects_a_clause_only_the_lite_doc_marks(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n")
    lite = _write(
        tmp_path / "lite.md",
        "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n<!-- lite:begin y -->\nmore\n<!-- lite:end y -->\n",
    )
    with pytest.raises(AssertionError, match="full.md marks"):
        _compare(full, lite, {"x", "y"})


def test_compare_rejects_a_clause_marked_in_one_doc_only(tmp_path: Path) -> None:
    full = _write(tmp_path / "full.md", "<!-- lite:begin x -->\nkeep\n<!-- lite:end x -->\n")
    lite = _write(tmp_path / "lite.md", "keep\n")
    with pytest.raises(AssertionError, match="lite.md marks"):
        _compare(full, lite, {"x"})


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("<!-- lite:begin x -->\ntext\n", "never closed"),
        ("<!-- lite:begin x -->\n<!-- lite:begin y -->\n", "begins inside"),
        ("<!-- lite:begin x -->\na\n<!-- lite:end x -->\n<!-- lite:begin x -->\nb\n<!-- lite:end x -->\n", "marked twice"),
        ("<!-- lite:begin x -->\ntext\n<!-- lite:end y -->\n", "does not close"),
        ("<!-- lite:end x -->\n", "does not close"),
    ],
)
def test_blocks_rejects_malformed_markers(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _blocks(_write(tmp_path / "a.md", text))


# The lite docs' shell blocks, executed. Each test takes its block from the doc as
# written, so a change to the doc's command changes what is run here.

SH_FENCE = re.compile(r"^[ \t]*```sh\n(.*?)^[ \t]*```", re.MULTILINE | re.DOTALL)
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
SHELLS = [name for name in ("sh", "bash", "zsh") if shutil.which(name)]


def _sh_blocks(doc: str, needle: str) -> list[str]:
    """Every ```sh block in a lite doc that contains `needle`, dedented."""
    text = (LITE / doc).read_text(encoding="utf-8")
    return [textwrap.dedent(m.group(1)) for m in SH_FENCE.finditer(text) if needle in m.group(1)]


def _git_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        HOME=str(home),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    return env


def _git(repo: Path, env: dict[str, str], *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def _repo(tmp_path: Path, name: str, *, commit: bool = True) -> tuple[Path, dict[str, str]]:
    env = _git_env(tmp_path)
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, env, "-c", "init.defaultBranch=main", "init", "-q")
    if commit:
        (repo / "f").write_text("a\n", encoding="utf-8")
        _git(repo, env, "add", "f")
        _git(repo, env, "commit", "-qm", "init")
    return repo, env


def _run(shell: str, script: str, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [shell, "-c", script], cwd=repo, env=env, capture_output=True, text=True, timeout=60
    )


BASE_BLOCKS = {"lite-review.md": 1, "lite-wrap-up.md": 2}


def _base_blocks() -> list[tuple[str, int, str]]:
    found = []
    for doc, expected in sorted(BASE_BLOCKS.items()):
        blocks = _sh_blocks(doc, "base=")
        # Pinned, so a block dropped from a doc fails here instead of shrinking the test.
        assert len(blocks) == expected, f"{doc}: {len(blocks)} base blocks, expected {expected}"
        found += [(doc, i, block) for i, block in enumerate(blocks)]
    return found


def _break(repo: Path, how: str) -> None:
    """Leave HEAD naming a ref or commit that cannot be read."""
    git_dir = repo / ".git"
    missing = "1" * 40
    if how == "garbage-ref":
        (git_dir / "refs/heads/main").write_text("not-a-sha\n", encoding="utf-8")
    elif how == "ref-to-missing-object":
        (git_dir / "refs/heads/main").write_text(f"{missing}\n", encoding="utf-8")
    elif how == "detached-at-missing-object":
        (git_dir / "HEAD").write_text(f"{missing}\n", encoding="utf-8")
    elif how == "corrupt-packed-refs":
        env = _git_env(repo.parent)
        _git(repo, env, "pack-refs", "--all")
        with (git_dir / "packed-refs").open("a", encoding="utf-8") as handle:
            handle.write("bogus\n")
    else:  # pragma: no cover - a typo in the parametrize list
        raise AssertionError(how)


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(("commit", "expected"), [(True, "HEAD"), (False, EMPTY_TREE)])
def test_base_blocks_resolve_a_readable_head(tmp_path: Path, shell: str, commit: bool, expected: str) -> None:
    """A branch with a commit diffs against HEAD; an unborn one against the empty tree."""
    for doc, index, block in _base_blocks():
        repo, env = _repo(tmp_path, f"{doc}-{index}-{commit}", commit=commit)
        (repo / "new").write_text("b\n", encoding="utf-8")
        (repo / "sub").mkdir()
        (repo / "sub/keep").write_text("k\n", encoding="utf-8")
        _git(repo, env, "add", "sub/keep")
        result = _run(shell, f"set -e\n{block}\nprintf 'BASE=%s\\n' \"$base\"\n", repo / "sub", env)
        where = f"{doc} block {index} under {shell}: {result.stderr}"
        assert result.returncode == 0, where
        assert "stop:" not in result.stderr, where
        assert f"BASE={expected}" in result.stdout.splitlines(), where
        if "ls-files" in block:
            # Untracked files are listed from the repository root, not the shell's directory.
            assert "../new" in result.stdout.splitlines(), where


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(
    "how", ["garbage-ref", "ref-to-missing-object", "detached-at-missing-object", "corrupt-packed-refs"]
)
def test_base_blocks_fail_visibly_on_an_unreadable_head(tmp_path: Path, shell: str, how: str) -> None:
    """The docs promise `stop:` or a failing command; under `set -e` either one exits non-zero.

    The failure this guards against is the unborn-branch branch claiming a broken ref:
    `base` would be the empty tree, every command would succeed, and the whole tree
    would read as the change.
    """
    for doc, index, block in _base_blocks():
        repo, env = _repo(tmp_path, f"{doc}-{index}-{how}")
        _break(repo, how)
        result = _run(shell, f"set -e\n{block}\nprintf 'BASE=%s\\n' \"$base\"\n", repo, env)
        where = f"{doc} block {index} under {shell}: rc={result.returncode} {result.stdout!r} {result.stderr!r}"
        assert result.returncode != 0, where
        assert f"BASE={EMPTY_TREE}" not in result.stdout, where


HANDOFF, FRICTION = "docs/plan.md", "docs/friction.md"


def _commit_split_block() -> str:
    (block,) = _sh_blocks("lite-wrap-up.md", 'echo "record: $?"')
    return block.replace("<handoff>", HANDOFF).replace("<friction-log>", FRICTION)


@pytest.mark.parametrize(
    ("staged", "record", "other"),
    [
        ((), "0", "0"),
        (("f",), "0", "1"),
        ((HANDOFF,), "1", "0"),
        ((FRICTION, "f"), "1", "1"),
    ],
)
def test_commit_split_check_reports_which_parts_are_staged(
    tmp_path: Path, staged: tuple[str, ...], record: str, other: str
) -> None:
    """Two commits only when both the record files and something else are staged."""
    repo, env = _repo(tmp_path, "split")
    (repo / "docs").mkdir()
    for rel in (HANDOFF, FRICTION):
        (repo / rel).write_text("x\n", encoding="utf-8")
    _git(repo, env, "add", HANDOFF, FRICTION)
    _git(repo, env, "commit", "-qm", "docs")
    for rel in (HANDOFF, FRICTION, "f"):
        (repo / rel).write_text("changed\n", encoding="utf-8")
    for rel in staged:
        _git(repo, env, "add", rel)
    for where in (repo, repo / "docs"):
        result = _run("sh", _commit_split_block(), where, env)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [f"record: {record}", f"other: {other}"], where


def _risk_tier_block(*entries: str) -> str:
    """The doc's check with its entries filled in, keeping whatever pathspec magic it writes."""
    (block,) = _sh_blocks("lite-review.md", "<entry 1>")
    match = re.search(r"'([^'<]*)<entry 1>' '\1<entry 2>'", block)
    assert match, block
    prefix = match.group(1)
    return block.replace(match.group(0), " ".join(f"'{prefix}{entry}'" for entry in entries))


def _risk_fixture(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    repo, env = _repo(tmp_path, "risk")
    for rel in ("deploy/x.conf", "docs/deploy.md", "docs/other.md", "deployment.md"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("x\n", encoding="utf-8")
    _git(repo, env, "add", ".")
    _git(repo, env, "commit", "-qm", "base")
    return repo, env


@pytest.mark.parametrize("where", [".", "docs", "deploy/a"])
@pytest.mark.parametrize("entries", [("deploy/**", "docs/deploy.md"), ("DEPLOY/*", "Docs/Deploy.md")])
def test_risk_tier_check_lists_staged_paths_under_declared_entries(
    tmp_path: Path, where: str, entries: tuple[str, str]
) -> None:
    """From any directory, case-insensitively, with `*` crossing `/` as `pr_watch`'s fnmatch does."""
    repo, env = _risk_fixture(tmp_path)
    (repo / "deploy/a/b").mkdir(parents=True)
    (repo / "deploy/a/b/new.sh").write_text("y\n", encoding="utf-8")
    (repo / "docs/deploy.md").write_text("changed\n", encoding="utf-8")
    (repo / "docs/other.md").write_text("changed\n", encoding="utf-8")
    (repo / "deployment.md").write_text("changed\n", encoding="utf-8")
    _git(repo, env, "add", "deploy/a/b/new.sh", "docs/deploy.md", "docs/other.md", "deployment.md")
    result = _run("sh", _risk_tier_block(*entries), repo / where, env)
    assert result.returncode == 0, result.stderr
    assert sorted(result.stdout.split()) == ["deploy/a/b/new.sh", "docs/deploy.md"]


def test_risk_tier_check_matches_like_fnmatch_with_a_directory_entry_covering_its_tree(
    tmp_path: Path,
) -> None:
    repo, env = _risk_fixture(tmp_path)
    (repo / "deploy/a").mkdir(parents=True)
    for rel in ("deploy/a/run.sh", "top.sh", "deployment.md"):
        (repo / rel).write_text("y\n", encoding="utf-8")
    _git(repo, env, "add", "deploy/a/run.sh", "top.sh", "deployment.md")
    star = _run("sh", _risk_tier_block("*.sh", "nothing"), repo / "docs", env)
    assert sorted(star.stdout.split()) == ["deploy/a/run.sh", "top.sh"], star.stderr
    directory = _run("sh", _risk_tier_block("deploy", "nothing"), repo, env)
    assert directory.stdout.split() == ["deploy/a/run.sh"], directory.stderr


@pytest.mark.parametrize(
    ("source", "destination", "listed"),
    [
        ("deploy/x.conf", "elsewhere/x.conf", "deploy/x.conf"),
        ("docs/other.md", "deploy/other.md", "deploy/other.md"),
    ],
)
def test_risk_tier_check_lists_a_file_moved_across_a_declared_boundary(
    tmp_path: Path, source: str, destination: str, listed: str
) -> None:
    """Git narrows to the pathspec before rename detection, so either side of a move is seen."""
    repo, env = _risk_fixture(tmp_path)
    (repo / destination).parent.mkdir(exist_ok=True)
    _git(repo, env, "mv", source, destination)
    result = _run("sh", _risk_tier_block("deploy/**", "docs/deploy.md"), repo, env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [listed]


def test_risk_tier_check_prints_nothing_for_an_undeclared_change(tmp_path: Path) -> None:
    repo, env = _risk_fixture(tmp_path)
    (repo / "docs/other.md").write_text("changed\n", encoding="utf-8")
    _git(repo, env, "add", "docs/other.md")
    result = _run("sh", _risk_tier_block("deploy/**", "docs/deploy.md"), repo, env)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("where", [".", "docs"])
def test_risk_tier_check_lists_a_change_to_the_config_that_declares_the_list(
    tmp_path: Path, where: str
) -> None:
    """Shortening the list is a change to the config, and the check itself must catch it."""
    repo, env = _risk_fixture(tmp_path)
    (repo / "config").mkdir()
    (repo / "config/dev-model.yaml").write_text("profile: lite\n", encoding="utf-8")
    _git(repo, env, "add", "config/dev-model.yaml")
    result = _run("sh", _risk_tier_block("deploy/**", "docs/deploy.md"), repo / where, env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["config/dev-model.yaml"]


# adopt.md's *Lite profile*, run end to end from the doc's own copy block.

ADOPT = REPO_ROOT / "docs/agentic-dev-kit/workflows/adopt.md"
KIT_DOCTOR = engine_dir(Path(__file__)) / "kit_doctor.py"


def _adopt_copy_block() -> str:
    text = ADOPT.read_text(encoding="utf-8")
    blocks = [
        textwrap.dedent(m.group(1))
        for m in re.finditer(r"^```bash\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
        if "for doc in lite-session-start lite-wrap-up lite-review" in m.group(1)
    ]
    assert len(blocks) == 1, "adopt.md's lite copy block is missing or repeated"
    return blocks[0]


def _doctor(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(KIT_DOCTOR), *args], env=env, capture_output=True, text=True, timeout=120
    )


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_never_writes_through_a_dangling_symlink(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    outside = tmp_path / "outside"
    outside.mkdir()
    links = {
        repo / ".claude/skills/review/SKILL.md": outside / "skill.md",
        repo / "docs/agentic-dev-kit/lite/lite-wrap-up.md": outside / "wrap-up.md",
    }
    for link, target in links.items():
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    result = _run(shell, _adopt_copy_block(), repo, env)
    assert result.returncode == 0, result.stderr
    for link, target in links.items():
        assert f"kept: {link}" in result.stdout
        assert link.is_symlink() and not target.exists()
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
# The target's own directory first: a guard that starts one level up skips it (#1360).
@pytest.mark.parametrize(
    "linked",
    [".claude/skills/review", "docs/agentic-dev-kit/lite", ".claude/skills", ".claude", "docs/agentic-dev-kit"],
)
def test_adopt_lite_copy_block_skips_a_target_under_a_symlinked_directory(
    tmp_path: Path, shell: str, linked: str
) -> None:
    repo, env = _repo(tmp_path, "adopter")
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / linked).parent.mkdir(parents=True, exist_ok=True)
    (repo / linked).symlink_to(outside)
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    result = _run(shell, _adopt_copy_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert "skipped, a directory on its path is a symlink" in result.stdout
    assert list(outside.iterdir()) == []
    assert (repo / ".agents/skills/review/SKILL.md").is_file()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
@pytest.mark.parametrize("dangling", [False, True])
def test_adopt_lite_copy_block_skips_a_claude_skill_a_command_would_be_shadowed_by(
    tmp_path: Path, shell: str, dangling: bool
) -> None:
    repo, env = _repo(tmp_path, "adopter")
    command = repo / ".claude/commands/session-start.md"
    command.parent.mkdir(parents=True)
    if dangling:
        command.symlink_to(tmp_path / "nowhere.md")
    else:
        command.write_text("Our session start.\n", encoding="utf-8")
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    result = _run(shell, _adopt_copy_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert f"collision: {command}" in result.stdout
    assert not (repo / ".claude/skills/session-start").exists()
    # Codex reads no `.claude/commands/`, so its binding still installs, as do the other slugs.
    assert (repo / ".agents/skills/session-start/SKILL.md").is_file()
    assert (repo / ".claude/skills/wrap-up/SKILL.md").is_file()
    assert command.is_symlink() if dangling else command.read_text(encoding="utf-8") == "Our session start.\n"


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
@pytest.mark.parametrize("slashes", ["/", "//", "///"])
def test_adopt_lite_copy_block_takes_a_repo_with_a_trailing_slash_under_a_symlinked_ancestor(
    tmp_path: Path, shell: str, slashes: str
) -> None:
    repo, env = _repo(tmp_path, "adopter")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path)
    env = {**env, "REPO": f"{alias / 'adopter'}{slashes}", "KIT": str(REPO_ROOT)}

    result = _run(shell, _adopt_copy_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert "skipped" not in result.stdout
    assert (repo / "docs/agentic-dev-kit/lite/lite-review.md").is_file()
    assert (repo / ".claude/skills/review/SKILL.md").is_file()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_installs_a_profile_kit_doctor_reports_intact(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    kept_skill = repo / ".claude/skills/review/SKILL.md"
    kept_skill.parent.mkdir(parents=True)
    kept_skill.write_text("---\nname: review\ndescription: Ours.\n---\n\nOur review.\n", encoding="utf-8")
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    result = _run(shell, _adopt_copy_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert f"kept: {kept_skill}" in result.stdout
    assert kept_skill.read_text(encoding="utf-8").endswith("Our review.\n")
    again = _run(shell, _adopt_copy_block(), repo, env)
    assert again.returncode == 0 and again.stdout.count("kept: ") == 9, again.stdout

    (repo / "config").mkdir()
    (repo / "config/dev-model.yaml").write_text(
        "profile: lite\nkit:\n  version: 2\npaths:\n  handoff: docs/plan.md\n"
        "  friction_log: docs/friction-log.md\n",
        encoding="utf-8",
    )
    (repo / "docs/plan.md").write_text("# Plan\n\n## Workstreams\n", encoding="utf-8")
    (repo / "docs/friction-log.md").write_text("# Friction log\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")

    record = _doctor("--record-install", "--from-kit", str(REPO_ROOT), "--root", str(repo), env=env)
    assert record.returncode == 0, record.stderr
    report = _doctor("--root", str(repo), "--manifest", str(REPO_ROOT / "kit-manifest.json"), env=env)
    assert report.returncode == 0, report.stdout + report.stderr
    assert "· profile: lite" in report.stdout
    assert "intact for this adoption — lite install, nothing declined" in report.stdout
    assert "files: 3 unchanged, 0 differ, 0 missing, 0 unknown" in report.stdout

    adapters = _doctor(
        "--adapter-report", "--adapter-source", str(REPO_ROOT), "--root", str(repo), "--json", env=env
    )
    assert adapters.returncode == 0, adapters.stderr
    rows = {row["path"]: row["state"] for row in json.loads(adapters.stdout)["adapters"]}
    assert rows[".claude/skills/review/SKILL.md"] == "adopter-owned"
    for path in (".claude/skills/session-start/SKILL.md", ".agents/skills/review/SKILL.md"):
        assert rows[path] == "kit-current"
    assert rows[".claude/skills/pr-watch/SKILL.md"] == "outside-profile"
