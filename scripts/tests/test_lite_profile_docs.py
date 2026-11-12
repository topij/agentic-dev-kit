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
It also runs the lite session-start's *Backlog* block against fixture backlogs and
configs: the declared form of the key, the plain-path rules, Markdown the block must
read or skip, and the stories it reports, blocks and picks. Last, `adopt.md`'s lite
copy block installs into a fresh repository, and `kit_doctor.py` records and reports
that install as intact, with or without a `backlog` key it does not read.
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


# The lite session-start's *Backlog* block (#1399), run against a backlog in the
# format of the bama `user-stories` skill, the one TGuitar's docs/STORIES.md uses.

BACKLOG = """\
# App stories

Intro text, and an example that is not a story:

```markdown
### S-999 An example
Status: todo
```

## M0 Spikes

### S-001 Clicks stay on time
As the developer, I run a tempo ramp.
Status: done (2026-11-08; the recorded run was dropped)

### S-002 Slow-down sounds good
Status: done (2026-11-08, Signalsmith won 9 of 15)

## M1 Drill

### S-010 Start and stop the metronome
Depends: S-001
Acceptance:
- [unit] Clicks are scheduled at sample time.
Status: done (2026-11-08; unit 23/23)

### S-011 Change the tempo by hand
Depends: S-010, S-099
Status: todo

### S-012 Choose the meter
Depends: S-010
Status: todo

### S-013 Ramp the tempo
Depends: S-011 S-012
Status: todo

## Later

### S-070 Tuner
Status: todo (later)

## Dropped

### S-080 Share to a friend
Status: dropped (2026-11-09; not wanted)
"""


def _backlog_block() -> str:
    (block,) = _sh_blocks("lite-session-start.md", "config=config/dev-model.yaml")
    return block


def _config(repo: Path, backlog: str) -> None:
    (repo / "config").mkdir(exist_ok=True)
    (repo / "config/dev-model.yaml").write_text(
        "profile: lite\npaths:\n  handoff: docs/plan.md\n  friction_log: docs/friction-log.md\n" + backlog,
        encoding="utf-8",
    )


def _backlog(tmp_path: Path, text: str, rel: str = "docs/STORIES.md") -> tuple[Path, dict[str, str]]:
    repo, env = _repo(tmp_path, "backlog")
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(text, encoding="utf-8")
    _config(repo, f"backlog:\n  path: {rel}\n")
    return repo, env


def _read_backlog(shell: str, repo: Path, env: dict[str, str], where: str = "."):
    result = _run(shell, _backlog_block(), repo / where, env)
    lines = result.stdout.splitlines()
    return result, [ln for ln in lines if ln.startswith("story ")], [
        ln for ln in lines if ln.startswith("problem ")
    ], [ln for ln in lines if ln.startswith("next ")]


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("where", [".", "docs"])
def test_backlog_block_reads_every_story_and_picks_the_first_ready_todo(
    tmp_path: Path, shell: str, where: str
) -> None:
    """S-011 waits on an unknown id, so S-012 is next; the fenced example is not a story."""
    repo, env = _backlog(tmp_path, BACKLOG)
    result, stories, problems, nexts = _read_backlog(shell, repo, env, where)
    assert result.returncode == 0, result.stderr
    assert stories == [
        "story S-001 done -",
        "story S-002 done -",
        "story S-010 done S-001",
        "story S-011 todo S-010,S-099",
        "story S-012 todo S-010",
        "story S-013 todo S-011,S-012",
        "story S-070 todo -",
        "story S-080 dropped -",
    ]
    assert problems == ["problem S-011 depends on unknown S-099"]
    # S-013 waits on S-011, which cannot be read, so it can never become ready as written.
    assert [ln.split()[:2] for ln in result.stdout.splitlines() if ln.startswith("blocked ")] == [
        ["blocked", "S-013"]
    ]
    assert nexts == ["next S-012"]


def test_backlog_block_prefers_a_ready_doing_story_over_an_earlier_todo(tmp_path: Path) -> None:
    text = BACKLOG.replace("### S-013 Ramp the tempo\nDepends: S-011 S-012\nStatus: todo", "### S-013 Ramp\nStatus: doing")
    repo, env = _backlog(tmp_path, text)
    result, _, _, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    assert nexts == ["next S-013"]


def test_backlog_block_skips_a_todo_whose_dependency_is_not_done(tmp_path: Path) -> None:
    """S-012 waits on S-010, now `doing`, which is picked instead as the doing story."""
    text = BACKLOG.replace("Status: done (2026-11-08; unit 23/23)", "Status: doing")
    repo, env = _backlog(tmp_path, text)
    result, _, problems, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    assert nexts == ["next S-010"]
    text = text.replace("### S-010 Start and stop the metronome\nDepends: S-001", "### S-010 Start\nDepends: S-002, S-080")
    (repo / "docs/STORIES.md").write_text(text, encoding="utf-8")
    result, _, problems, nexts = _read_backlog("sh", repo, env)
    # S-010 is doing but waits on the dropped S-080, and every todo waits on S-010.
    assert nexts == ["next S-070"], result.stdout


def test_backlog_block_never_counts_a_dropped_story_as_done(tmp_path: Path) -> None:
    text = BACKLOG.replace("### S-070 Tuner\nStatus: todo (later)", "### S-070 Tuner\nDepends: S-080\nStatus: todo")
    text = text.replace("Depends: S-010, S-099\n", "").replace("Depends: S-010\nStatus: todo", "Depends: S-099\nStatus: todo")
    repo, env = _backlog(tmp_path, text)
    result, _, _, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    # S-011 is ready; with it done, S-013 still waits on S-012 (which waits on an unknown
    # id), and S-070 on the dropped S-080.
    assert nexts == ["next S-011"]
    text = text.replace("### S-011 Change the tempo by hand\nStatus: todo", "### S-011 Change\nStatus: done")
    (repo / "docs/STORIES.md").write_text(text, encoding="utf-8")
    result, _, _, nexts = _read_backlog("sh", repo, env)
    assert nexts == ["next none"], result.stdout


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        ("Status: todo\n\n### S-013", "\n\n### S-013", "problem S-012 no Status line"),
        ("Status: todo\n\n### S-013", "Status: todo\nStatus: doing\n\n### S-013", "problem S-012 more than one Status line"),
        ("Status: todo\n\n### S-013", "Status: Todo\n\n### S-013", 'problem S-012 unknown status "Todo"'),
        ("Status: todo\n\n### S-013", "Status: finished\n\n### S-013", 'problem S-012 unknown status "finished"'),
        ("Status: todo\n\n### S-013", "Status:\n\n### S-013", 'problem S-012 unknown status ""'),
        ("Depends: S-010\nStatus: todo", "Depends: S-010\nDepends: S-001\nStatus: todo", "problem S-012 more than one Depends line"),
        ("### S-012 Choose the meter", "### S-002 Choose the meter", "problem S-002 duplicate id"),
    ],
)
def test_backlog_block_reports_a_story_it_cannot_read_and_never_picks_it(
    tmp_path: Path, old: str, new: str, problem: str
) -> None:
    text = BACKLOG.replace("Depends: S-010, S-099\n", "")  # make S-011 ready, ahead of S-012
    text = text.replace("### S-011 Change the tempo by hand\nStatus: todo", "### S-011 Change\nStatus: done")
    assert text.count(old) == 1, old
    repo, env = _backlog(tmp_path, text.replace(old, new))
    result, _, problems, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    assert problem in problems, result.stdout
    # S-012 is unreadable or ambiguous, so neither it nor S-013, which waits on it, is next.
    assert nexts == ["next S-070"], result.stdout


def test_backlog_block_does_not_count_a_duplicated_done_id_as_done(tmp_path: Path) -> None:
    text = BACKLOG.replace("Depends: S-010, S-099", "Depends: S-010").replace("### S-002 Slow-down", "### S-010 Slow-down")
    repo, env = _backlog(tmp_path, text)
    result, _, problems, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    assert problems == ["problem S-010 duplicate id", "problem S-010 duplicate id"]
    # Every story waiting on the ambiguous S-010 is reported as unable to become ready.
    assert {ln.split()[1] for ln in result.stdout.splitlines() if ln.startswith("blocked ")} == {
        "S-011", "S-012", "S-013"
    }
    assert nexts == ["next S-070"], result.stdout


def test_backlog_block_reports_a_file_with_no_story_heading_as_unavailable(tmp_path: Path) -> None:
    """A checkbox list or any other format reads as no stories; that is not an empty backlog."""
    repo, env = _backlog(tmp_path, "# Stories\n\n- [ ] Tuner\n- [x] Metronome\n")
    result, stories, problems, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 1, result.stdout
    assert "unavailable: no ### story heading" in result.stderr
    assert (stories, problems, nexts) == ([], [], [])


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("how", ["missing", "directory", "symlink", "symlinked-directory", "unreadable"])
def test_backlog_block_reports_an_unreadable_file_as_unavailable(tmp_path: Path, shell: str, how: str) -> None:
    repo, env = _repo(tmp_path, "backlog")
    _config(repo, "backlog:\n  path: docs/STORIES.md\n")
    if how == "directory":
        (repo / "docs/STORIES.md").mkdir(parents=True)
    elif how == "symlink":
        (repo / "docs").mkdir()
        (repo / "elsewhere.md").write_text("### S-1 a\nStatus: todo\n", encoding="utf-8")
        (repo / "docs/STORIES.md").symlink_to(repo / "elsewhere.md")
    elif how == "unreadable":
        if os.geteuid() == 0:
            pytest.skip("root reads a mode-000 file")
        (repo / "docs").mkdir()
        (repo / "docs/STORIES.md").write_text(BACKLOG, encoding="utf-8")
        (repo / "docs/STORIES.md").chmod(0)
    elif how == "symlinked-directory":
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "STORIES.md").write_text("### S-1 a\nStatus: todo\n", encoding="utf-8")
        (repo / "docs").symlink_to(outside)
    result, stories, _, nexts = _read_backlog(shell, repo, env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "unavailable: docs/STORIES.md" in result.stderr
    assert (stories, nexts) == ([], [])


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("locale", ["C.UTF-8", "en_US.UTF-8"])
def test_backlog_block_refuses_a_non_ascii_path_in_a_utf8_locale(tmp_path: Path, shell: str, locale: str) -> None:
    """A bracket range is locale-dependent; the block runs under LC_ALL=C so ASCII means ASCII."""
    probe = 'case "\u00e9" in *[!A-Za-z0-9._/-]*) echo refused;; *) echo passed;; esac'
    if _run(shell, probe, tmp_path, {**os.environ, "LC_ALL": locale, "LANG": locale}).stdout.strip() != "passed":
        pytest.skip(f"{shell} under {locale} already refuses it, so this case could not tell LC_ALL=C apart")
    repo, env = _backlog(tmp_path, BACKLOG, rel="docs/\u00e9.md")
    result = _run(shell, _backlog_block(), repo, {**env, "LC_ALL": locale, "LANG": locale})
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unusable: backlog.path" in result.stderr


def test_backlog_block_reports_a_missing_awk_as_unavailable_not_as_a_config_fault(tmp_path: Path) -> None:
    repo, env = _backlog(tmp_path, BACKLOG)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("git", "dirname", "cat"):
        (bin_dir / tool).symlink_to(shutil.which(tool))
    result = subprocess.run(
        ["/bin/sh", "-c", _backlog_block()], cwd=repo, env={**env, "PATH": str(bin_dir)},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "unavailable: awk could not read config/dev-model.yaml" in result.stderr


def test_backlog_block_stops_outside_a_git_work_tree(tmp_path: Path) -> None:
    repo, env = _backlog(tmp_path, BACKLOG)
    outside = tmp_path / "plain"
    (outside / "config").mkdir(parents=True)
    (outside / "config/dev-model.yaml").write_text("backlog:\n  path: S.md\n", encoding="utf-8")
    (outside / "S.md").write_text(BACKLOG, encoding="utf-8")
    result = _run("sh", _backlog_block(), outside, {**env, "GIT_CEILING_DIRECTORIES": str(tmp_path)})
    assert result.returncode == 1, result.stdout
    assert "next " not in result.stdout


@pytest.mark.parametrize(
    "backlog", ["", "backlog:\n", "backlog: null\n", "backlog: ~  # none\n", "backlog:  # none yet\n\nvcs:\n  protected_branch: main\n"]
)
def test_backlog_block_says_not_configured_without_a_path(tmp_path: Path, backlog: str) -> None:
    repo, env = _repo(tmp_path, "backlog")
    _config(repo, backlog)
    result = _run("sh", _backlog_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "backlog: not configured\n"


@pytest.mark.parametrize(
    "backlog",
    [
        "backlog:\n- path: docs/STORIES.md\n",
        "backlog:\npath: docs/STORIES.md\n",
        "backlog:\n? path\n: docs/STORIES.md\n",
    ],
)
def test_backlog_block_reads_an_unindented_line_under_backlog_as_not_configured(tmp_path: Path, backlog: str) -> None:
    """The gap *Backlog* names: a column-0 line ends the section. #1368's validator is to refuse these."""
    repo, env = _backlog(tmp_path, BACKLOG)
    _config(repo, backlog)
    result = _run("sh", _backlog_block(), repo, env)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "backlog: not configured\n"


@pytest.mark.parametrize(
    "backlog",
    [
        "backlog:\n  - path: docs/STORIES.md\n",
        "backlog:\n  ? path\n  : docs/STORIES.md\n",
        "backlog: docs/STORIES.md\n",
        "backlog:\n  path: docs/STORIES.md\n  extra: 1\n",
        "backlog:\n  path: docs/STORIES.md\n  path: docs/OTHER.md\n",
        "backlog:\n  path: docs/STORIES.md\nbacklog:\n  path: docs/OTHER.md\n",
        "backlog:\n  path:\n",
        "backlog:\n  path: null\n",
        "backlog: {}\n",
        "backlog: {path: docs/STORIES.md}\n",
        "\"backlog\":\n  path: docs/STORIES.md\n",
        "backlog :\n  path: docs/STORIES.md\n",
        "backlog:\n  path:docs/STORIES.md\n",
        "backlog:\n\tpath: docs/STORIES.md\n",
        "backlog:\n  path: docs/STORIES.md\nbacklog:\n",
        "backlog: null\n  path: docs/STORIES.md\n",
        "backlog:\tnull\n  path: docs/STORIES.md\n",
        "backlog: null#x\n",
        "backlog: ~#x\n",
        "backlog:#x\n",
        "backlog:null\n",
        "backlog:~\n",
    ],
)
def test_backlog_block_stops_on_a_backlog_that_is_not_a_mapping_with_one_path(tmp_path: Path, backlog: str) -> None:
    repo, env = _backlog(tmp_path, BACKLOG)
    _config(repo, backlog)
    result = _run("sh", _backlog_block(), repo, env)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unusable: backlog in config/dev-model.yaml" in result.stderr
    assert "next " not in result.stdout


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(
    "value",
    [
        "\"x'; touch INJECTED; echo '\"",
        "'$(touch INJECTED)'",
        "\"x\\\"; touch INJECTED; echo \\\"\"",
        "../STORIES.md",
        "/etc/hosts",
        "-STORIES.md",
        "\" docs/STORIES.md\"",
        "V=1.md",
        "docs/./STORIES.md",
        "docs//STORIES.md",
        "docs/",
        "<backlog path>",
        "-",
        "\"-\"",
    ],
)
def test_backlog_block_refuses_a_path_that_is_not_plain_and_runs_nothing_from_it(
    tmp_path: Path, shell: str, value: str
) -> None:
    """The block reads the value itself: nothing in it is ever run, and only a plain path passes."""
    repo, env = _backlog(tmp_path, BACKLOG)
    _config(repo, f"backlog:\n  path: {value}\n")
    result = _run(shell, _backlog_block(), repo, env)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unusable: backlog.path" in result.stderr
    assert not (repo / "INJECTED").exists()
    assert "next " not in result.stdout


@pytest.mark.parametrize("value", ["docs/STORIES.md", "'docs/STORIES.md'", '"docs/STORIES.md"  # ours'])
def test_backlog_block_reads_a_quoted_or_commented_path(tmp_path: Path, value: str) -> None:
    repo, env = _backlog(tmp_path, BACKLOG)
    _config(repo, f"backlog:  # see: next\n  # the stories\n\n  path: {value}\nvcs:\n  protected_branch: main\n")
    result, stories, _, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 0, result.stderr
    assert len(stories) == 8 and nexts == ["next S-012"]


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("# T\n\n### S-1 a\nStatus: todo\n```\n### S-2 b\nStatus: doing\n", "code fence opened at line 5"),
        ("# T\n\n### S-1 a\nStatus: todo\n~~~~\n### S-2 b\n~~~\nStatus: doing\n", "code fence opened at line 5"),
        ("# T\n\n<!-- hidden\n### S-2 b\nStatus: doing\n", "HTML comment opened at line 3"),
    ],
)
def test_backlog_block_reports_a_block_that_never_closes_as_unavailable(tmp_path: Path, text: str, kind: str) -> None:
    """Swallowing the rest of the file would read as a shorter backlog; it is the source failing instead."""
    repo, env = _backlog(tmp_path, text)
    result, stories, _, nexts = _read_backlog("sh", repo, env)
    assert result.returncode == 1, result.stdout
    assert f"unavailable: the {kind} never closes" in result.stderr
    assert (stories, nexts) == ([], [])


@pytest.mark.parametrize("shell", SHELLS)
def test_backlog_block_reads_what_markdown_shows_and_skips_what_it_hides(tmp_path: Path, shell: str) -> None:
    text = (
        "﻿### S-0 first, behind a byte-order mark\nStatus: done\n"
        "## M1\nStatus: doing\nDepends: S-9\n"
        "~~~markdown\n### S-8 a fenced example\nStatus: doing\n~~~\n"
        "  ```\n### S-7 an indented fence\nStatus: doing\n```\n"
        "<!--\n### S-6 commented out\nStatus: doing\n-->\n<!-- a one-line comment -->\n"
        "###\tS-1 a tab after the hashes\nDepends: none\nStatus: todo\n"
        "### S-2 waits on nothing\nDepends: -\nStatus: todo (later)\n"
        "### S-3 waits on itself\nDepends: S-3\nStatus: todo\n"
        "### S-4 one half of a cycle\nDepends: S-5\nStatus: todo\n"
        "### S-5 the other half\nDepends: S-4\nStatus: doing\n"
        "### S-6b an unknown word\nStatus: finished (yes)\n"
        "   ### S-7b indented three spaces\nStatus: done, shipped\n#### a sub-heading inside S-7b, not a story\n"
        "```x``` is inline code, not a fence\n### S-8b after inline code\nStatus: todo\n"
        "<!--> is an empty comment, closed on its own line\n### S-9b after an empty comment\nStatus: todo\n"
        "<!---> is empty too, closed on its own line\n### S-9c after the other empty comment\nStatus: todo\n"
        "~~~\n### S-0y inside\n```\n### S-0z still inside: a backtick line does not close a tilde fence\n~~~\n"
        "```\n### S-0v inside\n~~~\n### S-0w still inside: a tilde line does not close a backtick fence\n```\n"
        "```text\n### S-0x inside\n``` not a closer\n```\n"
    )
    repo, env = _backlog(tmp_path, text)
    result, stories, problems, nexts = _read_backlog(shell, repo, env)
    assert result.returncode == 0, result.stderr
    # The milestone's own Status and Depends lines belong to no story.
    assert stories == [
        "story S-0 done -",
        "story S-1 todo -",
        "story S-2 todo -",
        "story S-3 todo S-3",
        "story S-4 todo S-5",
        "story S-5 doing S-4",
        "story S-6b ? -",
        "story S-7b done -",
        "story S-8b todo -",
        "story S-9b todo -",
        "story S-9c todo -",
    ]
    assert problems == ["problem S-3 depends on itself", 'problem S-6b unknown status "finished"']
    assert [ln.split()[1] for ln in result.stdout.splitlines() if ln.startswith("blocked ")] == ["S-4", "S-5"]
    # S-5 is the only doing story and is in a cycle, so the first ready todo is picked.
    assert nexts == ["next S-1"]


def test_lite_backlog_key_is_in_the_wrap_up_schema_and_the_adopt_template() -> None:
    """The wrap-up refuses a key outside its schema list, so the key must be on it."""
    wrap_up = _normalise((LITE / "lite-wrap-up.md").read_text(encoding="utf-8"))
    assert "`vcs.protected_branch` and `backlog.path`." in wrap_up
    assert "The way out of the `vcs.protected_branch`, `backlog` and schema stops above" in wrap_up
    assert "`backlog` is held to the one form the lite `session-start`'s *Backlog* section declares" in wrap_up
    template = re.search(r"^```yaml\n(profile: lite\n.*?)^```", ADOPT.read_text(encoding="utf-8"), re.M | re.S)
    assert template, "adopt.md's lite config template is missing"
    assert "backlog:\n  path: <backlog path>" in template.group(1)


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


def _fill(text: str, root: str, kit: str) -> str:
    """The doc's `<root>` and `<kit>`, replaced as L1 says, by the paths written down."""
    return text.replace("<root>", root).replace("<kit>", kit)


def _fresh(env: dict[str, str]) -> dict[str, str]:
    """A shell that carries nothing from an earlier command (#1420)."""
    return {k: v for k, v in env.items() if k not in ("REPO", "KIT")}


def _adopt_run(shell: str, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """adopt.md L3's block, with the paths L1 wrote down, in a fresh shell."""
    block = _fill(_adopt_copy_block(), env["REPO"], env["KIT"])
    return _run(shell, block, repo, _fresh(env))


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

    result = _adopt_run(shell, repo, env)
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

    result = _adopt_run(shell, repo, env)
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

    result = _adopt_run(shell, repo, env)
    assert result.returncode == 0, result.stderr
    assert f"collision: {command}" in result.stdout
    assert not (repo / ".claude/skills/session-start").exists()
    # Codex reads no `.claude/commands/`, so its binding still installs, as do the other slugs.
    assert (repo / ".agents/skills/session-start/SKILL.md").is_file()
    assert (repo / ".claude/skills/wrap-up/SKILL.md").is_file()
    assert command.is_symlink() if dangling else command.read_text(encoding="utf-8") == "Our session start.\n"


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
# A name made only of newlines: a command substitution strips them, so `-z "$(ls -A ...)"` saw it as empty.
@pytest.mark.parametrize(
    "left", ["helper file", "hidden file", "newline-named file", "subdirectory", "plain file", "unreadable"]
)
def test_adopt_lite_copy_block_keeps_a_skill_directory_that_still_holds_something(
    tmp_path: Path, shell: str, left: str
) -> None:
    """A half-removed skill (its `SKILL.md` gone, a helper left) is not installed beside."""
    if left == "unreadable" and os.geteuid() == 0:
        pytest.skip("root lists an unreadable directory")
    repo, env = _repo(tmp_path, "adopter")
    skill = repo / ".claude/skills/review"
    skill.parent.mkdir(parents=True)
    if left == "plain file":
        skill.write_text("not a directory\n", encoding="utf-8")
    else:
        skill.mkdir()
        if left == "helper file":
            (skill / "helper.sh").write_text("echo ours\n", encoding="utf-8")
        elif left == "hidden file":
            (skill / ".notes").write_text("ours\n", encoding="utf-8")
        elif left == "newline-named file":
            (skill / "\n\n").write_text("ours\n", encoding="utf-8")
        elif left == "subdirectory":
            (skill / "scripts").mkdir()
        else:
            skill.chmod(0o000)
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    try:
        result = _adopt_run(shell, repo, env)
    finally:
        if left == "unreadable":
            skill.chmod(0o755)
    assert result.returncode == 0, result.stderr
    assert f"kept: {skill}" in result.stdout
    assert not (skill / "SKILL.md").exists()
    assert (repo / ".agents/skills/review/SKILL.md").is_file()
    assert (repo / ".claude/skills/wrap-up/SKILL.md").is_file()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_installs_into_an_empty_skill_directory(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    skill = repo / ".claude/skills/review"
    skill.mkdir(parents=True)
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}

    result = _adopt_run(shell, repo, env)
    assert result.returncode == 0, result.stderr
    assert "kept:" not in result.stdout
    assert (skill / "SKILL.md").is_file()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
@pytest.mark.parametrize("slashes", ["/", "//", "///"])
def test_adopt_lite_copy_block_takes_a_repo_with_a_trailing_slash_under_a_symlinked_ancestor(
    tmp_path: Path, shell: str, slashes: str
) -> None:
    repo, env = _repo(tmp_path, "adopter")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path)
    env = {**env, "REPO": f"{alias / 'adopter'}{slashes}", "KIT": str(REPO_ROOT)}

    result = _adopt_run(shell, repo, env)
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

    result = _adopt_run(shell, repo, env)
    assert result.returncode == 0, result.stderr
    assert f"kept: {kept_skill}" in result.stdout
    assert kept_skill.read_text(encoding="utf-8").endswith("Our review.\n")
    again = _adopt_run(shell, repo, env)
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

    # adopt.md L4, with `--keep` for the skill L2 kept.
    record = _doctor(
        "--record-install", "--from-kit", str(REPO_ROOT), "--root", str(repo),
        "--keep", ".claude/skills/review/SKILL.md", env=env,
    )
    assert record.returncode == 0, record.stderr
    # The kept skill is the repository's own: named, and left out of `files`.
    assert "recorded as the repository's own" in record.stderr
    assert "  · .claude/skills/review/SKILL.md" in record.stderr
    report = _doctor("--root", str(repo), "--manifest", str(REPO_ROOT / "kit-manifest.json"), env=env)
    assert report.returncode == 0, report.stdout + report.stderr
    assert "· profile: lite" in report.stdout
    assert "intact for this adoption — lite install, 1 file(s) declined" in report.stdout
    # The three docs and the five skills the block installed; the kept one is declined.
    assert "files: 8 unchanged, 0 differ, 0 missing, 0 unknown" in report.stdout
    assert "rests on the config alone" not in report.stdout

    adapters = _doctor(
        "--adapter-report", "--adapter-source", str(REPO_ROOT), "--root", str(repo), "--json", env=env
    )
    assert adapters.returncode == 0, adapters.stderr
    rows = {row["path"]: row["state"] for row in json.loads(adapters.stdout)["adapters"]}
    assert rows[".claude/skills/review/SKILL.md"] == "adopter-owned"
    for path in (".claude/skills/session-start/SKILL.md", ".agents/skills/review/SKILL.md"):
        assert rows[path] == "kit-current"
    assert rows[".claude/skills/pr-watch/SKILL.md"] == "outside-profile"

    # The main report covers the installed skills, not only the docs (#1365): a
    # deleted one and an edited one fail it, and the kept one stays declined.
    (repo / ".agents/skills/wrap-up/SKILL.md").unlink()
    edited = repo / ".claude/skills/session-start/SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "Our edit.\n", encoding="utf-8")
    broken = _doctor(
        "--root", str(repo), "--manifest", str(REPO_ROOT / "kit-manifest.json"), "--json", env=env
    )
    assert broken.returncode == 1, broken.stdout + broken.stderr
    states = {row["path"]: row["state"] for row in json.loads(broken.stdout)["files"]}
    assert states[".agents/skills/wrap-up/SKILL.md"] == "removed"
    assert states[".claude/skills/session-start/SKILL.md"] == "locally-edited"
    assert states[".claude/skills/review/SKILL.md"] == "declined"


def _lite_install(tmp_path: Path, shell: str, config_tail: str) -> tuple[Path, dict[str, str]]:
    repo, env = _repo(tmp_path, "adopter")
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}
    result = _adopt_run(shell, repo, env)
    assert result.returncode == 0, result.stderr
    (repo / "config").mkdir()
    (repo / "config/dev-model.yaml").write_text(
        "profile: lite\nkit:\n  version: 2\npaths:\n  handoff: docs/plan.md\n"
        "  friction_log: docs/friction-log.md\n" + config_tail,
        encoding="utf-8",
    )
    (repo / "docs/plan.md").write_text("# Plan\n\n## Workstreams\n", encoding="utf-8")
    (repo / "docs/friction-log.md").write_text("# Friction log\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    record = _doctor("--record-install", "--from-kit", str(REPO_ROOT), "--root", str(repo), env=env)
    assert record.returncode == 0, record.stderr
    return repo, env


@pytest.mark.parametrize(
    "config_tail",
    [
        "",
        "backlog:\n",
        "backlog:\n  path: docs/STORIES.md\n",
        "backlog:\n  path: docs/MISSING.md\n",
        "backlog:\n  path: ../STORIES.md\n",
        "backlog: {path: docs/STORIES.md}\n",
    ],
)
def test_kit_doctor_reports_a_lite_install_intact_with_or_without_a_backlog(tmp_path: Path, config_tail: str) -> None:
    """kit_doctor does not read the key (#1399): the *Backlog* block is its one reader, so
    whatever the key holds, the install reports intact and no backlog line appears."""
    repo, env = _lite_install(tmp_path, "sh", config_tail)
    (repo / "docs/STORIES.md").write_text(BACKLOG, encoding="utf-8")
    report = _doctor("--root", str(repo), "--manifest", str(REPO_ROOT / "kit-manifest.json"), env=env)
    assert report.returncode == 0, report.stdout + report.stderr
    assert "intact for this adoption — lite install" in report.stdout
    assert "backlog" not in report.stdout


# --- adopt.md's lite install carries no shell variable between commands (#1420) ---


def _adopt_lite_section() -> str:
    text = ADOPT.read_text(encoding="utf-8")
    # The last section: the `## ` heading inside it is the AGENTS.md template's.
    return text[text.index("\n## Lite profile\n") :]


def _adopt_lite_blocks() -> list[str]:
    return re.findall(r"^```bash\n(.*?)^```", _adopt_lite_section(), re.MULTILINE | re.DOTALL)


def test_no_adopt_lite_block_reads_a_variable_an_earlier_command_set() -> None:
    """Each block reads only the variables it assigns itself: an agent harness may
    start a fresh shell for every command, so one set by Step 0 is gone (#1420)."""
    blocks = _adopt_lite_blocks()
    # L3's copy block, L4 and L5: pinned, so a dropped block fails here.
    assert len(blocks) == 3, blocks
    for block in blocks:
        assigned = set(re.findall(r"(?:^|[\s;(])([A-Za-z_][A-Za-z0-9_]*)=", block, re.MULTILINE))
        assigned |= set(re.findall(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b", block))
        read = set(re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", block))
        assert read <= assigned, (sorted(read - assigned), block)
    section = _adopt_lite_section()
    assert "${KIT:?" not in section and "${REPO:?" not in section
    for block in blocks[1:]:
        assert "$" not in block, block
        # Quoted, so a path with a blank stays one word.
        assert block.startswith("uv run '<kit>/scripts/kit_doctor.py' "), block
    assert "--root '<root>'" in blocks[1] and "--from-kit '<kit>'" in blocks[1]
    assert blocks[2].strip() == (
        "uv run '<kit>/scripts/kit_doctor.py' --verify-lite --from-kit '<kit>' --root '<root>'"
    )
    assert re.search(r"<(?:kit|root)>", re.sub(r"'<(?:kit|root)>[^']*'", "", "".join(blocks[1:]))) is None


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_refuses_placeholders_left_in(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    result = _run(shell, _adopt_copy_block(), repo, _fresh(env))
    assert result.returncode == 1
    assert "replace <root> and <kit>" in result.stderr
    assert not (repo / "docs").exists()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_refuses_a_root_that_is_not_a_checkout_top(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    (repo / "sub").mkdir()
    result = _adopt_run(shell, repo, {**env, "REPO": str(repo / "sub"), "KIT": str(REPO_ROOT)})
    assert result.returncode == 1
    assert "is not the top of a checkout" in result.stderr
    assert not (repo / "sub/docs").exists()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_refuses_a_kit_path_that_is_not_the_kit(tmp_path: Path, shell: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    result = _adopt_run(shell, repo, {**env, "REPO": str(repo), "KIT": str(tmp_path)})
    assert result.returncode == 1
    assert "is not the kit clone" in result.stderr
    assert not (repo / "docs").exists()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
@pytest.mark.parametrize("only", ["scripts/kit_doctor.py", "docs/agentic-dev-kit/lite/adapters"])
def test_adopt_lite_copy_block_needs_both_halves_of_the_kit_check(tmp_path: Path, shell: str, only: str) -> None:
    """L3 takes a path as the kit only with the engine AND the lite adapters: each half
    alone is refused (adversarial, PR 1423 delta F3)."""
    repo, env = _repo(tmp_path, "adopter")
    fake = tmp_path / "fake-kit"
    if only.endswith(".py"):
        (fake / only).parent.mkdir(parents=True)
        (fake / only).write_text("", encoding="utf-8")
    else:
        (fake / only).mkdir(parents=True)
    result = _adopt_run(shell, repo, {**env, "REPO": str(repo), "KIT": str(fake)})
    assert result.returncode == 1
    assert "is not the kit clone" in result.stderr
    assert not (repo / "docs").exists()


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_copy_block_refuses_an_installed_adopter_as_the_kit(tmp_path: Path, shell: str) -> None:
    """An adopter carries `kit-manifest.json` after L4, so that is no sign of the kit
    clone: `<root>` and `<kit>` swapped is refused (adversarial, PR 1423 pass 2 F1)."""
    (tmp_path / "a").mkdir()
    adopter, env = _lite_installed(tmp_path / "a", shell)
    assert _l4(adopter, env).returncode == 0
    other, _ = _repo(tmp_path, "other")
    result = _adopt_run(shell, other, {**env, "REPO": str(other), "KIT": str(adopter)})
    assert result.returncode == 1
    assert "is not the kit clone" in result.stderr
    assert not (other / "docs").exists()


def test_verify_lite_refuses_a_kit_that_is_not_a_checkout(tmp_path: Path) -> None:
    repo, env = _lite_installed(tmp_path, "sh")
    assert _l4(repo, env).returncode == 0
    copy = tmp_path / "kit-copy"
    copy.mkdir()
    shutil.copy(REPO_ROOT / "kit-manifest.json", copy / "kit-manifest.json")
    verify = _doctor("--verify-lite", "--from-kit", str(copy), "--root", str(repo), env=env)
    assert verify.returncode == 1
    assert verify.stdout.startswith(f"refused: {copy} is not a git checkout")


def test_verify_lite_install_line_is_not_intact_when_any_stop_prints(tmp_path: Path) -> None:
    """A run that exits 1 never prints the phrase L5 tells the reader to expect
    (adversarial, PR 1423 pass 2 F3)."""
    repo, env = _lite_installed(tmp_path, "sh")
    assert _l4(repo, env).returncode == 0
    config = repo / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("version: 2", "version: 1"), encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1
    assert "intact for this adoption" not in verify.stdout
    assert "verify (L5): NOT intact" in verify.stdout


@pytest.mark.parametrize("replacement", ["directory", "dangling link"])
def test_verify_lite_stops_on_a_kept_skill_that_is_not_a_file(tmp_path: Path, replacement: str) -> None:
    repo, env = _repo(tmp_path, "adopter")
    kept = repo / ".claude/skills/review/SKILL.md"
    kept.parent.mkdir(parents=True)
    kept.write_text("---\nname: review\ndescription: Ours.\n---\n\nOur review.\n", encoding="utf-8")
    repo, env = _lite_installed_at(repo, env)
    assert _l4(repo, env, "--keep", ".claude/skills/review/SKILL.md").returncode == 0
    kept.unlink()
    if replacement == "directory":
        kept.mkdir()
    else:
        kept.symlink_to(tmp_path / "nowhere.md")
    verify = _l5(repo, env)
    assert verify.returncode == 1, verify.stdout
    assert ".claude/skills/review/SKILL.md is kept by the record but not a file on disk" in verify.stdout
    assert "intact for this adoption" not in verify.stdout


def _doc_command(block: str, root: Path) -> list[str]:
    """A one-line L4 or L5 command from the doc, filled in, run by this interpreter."""
    import shlex

    words = shlex.split(_fill(block.strip(), str(root), str(REPO_ROOT)))
    assert words[:2] == ["uv", "run"], words
    return [sys.executable, *words[2:]]


def _lite_installed(tmp_path: Path, shell: str) -> tuple[Path, dict[str, str]]:
    """L3 as the doc runs it, plus the config, plan, inbox and AGENTS.md L3 writes."""
    repo, env = _repo(tmp_path, "adopter")
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}
    result = _adopt_run(shell, repo, env)
    assert result.returncode == 0, result.stderr
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
    return repo, _fresh(env)


def _l4(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = _doc_command(_adopt_lite_blocks()[1], repo) + list(extra)
    return subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=120)


def _l5(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    cmd = _doc_command(_adopt_lite_blocks()[2], repo)
    return subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("shell", [s for s in ("sh", "bash") if shutil.which(s)])
def test_adopt_lite_l3_l4_l5_each_in_a_fresh_shell_end_intact(tmp_path: Path, shell: str) -> None:
    repo, env = _lite_installed(tmp_path, shell)
    record = _l4(repo, env)
    assert record.returncode == 0, record.stderr
    verify = _l5(repo, env)
    assert verify.returncode == 0, verify.stdout + verify.stderr
    lines = [line for line in verify.stdout.splitlines() if line.startswith("verify (L5):")]
    assert len(lines) == 2, verify.stdout
    assert "intact for this adoption — lite install" in lines[0]
    assert "as L5 expects" in lines[1]
    assert "stop:" not in verify.stdout


def test_verify_lite_passes_a_skill_kept_with_keep(tmp_path: Path) -> None:
    repo, env = _repo(tmp_path, "adopter")
    kept = repo / ".claude/skills/review/SKILL.md"
    kept.parent.mkdir(parents=True)
    kept.write_text("---\nname: review\ndescription: Ours.\n---\n\nOur review.\n", encoding="utf-8")
    repo, env = _lite_installed_at(repo, env)
    assert _l4(repo, env, "--keep", ".claude/skills/review/SKILL.md").returncode == 0
    verify = _l5(repo, env)
    assert verify.returncode == 0, verify.stdout
    assert "1 adopter-owned and kept" in verify.stdout


def _lite_installed_at(repo: Path, env: dict[str, str]) -> tuple[Path, dict[str, str]]:
    env = {**env, "REPO": str(repo), "KIT": str(REPO_ROOT)}
    result = _adopt_run("sh", repo, env)
    assert result.returncode == 0, result.stderr
    (repo / "config").mkdir()
    (repo / "config/dev-model.yaml").write_text(
        "profile: lite\nkit:\n  version: 2\npaths:\n  handoff: docs/plan.md\n"
        "  friction_log: docs/friction-log.md\n",
        encoding="utf-8",
    )
    (repo / "docs/plan.md").write_text("# Plan\n\n## Workstreams\n", encoding="utf-8")
    (repo / "docs/friction-log.md").write_text("# Friction log\n", encoding="utf-8")
    return repo, _fresh(env)


def test_verify_lite_passes_a_claude_skill_l3_skipped_for_a_kept_command(tmp_path: Path) -> None:
    repo, env = _repo(tmp_path, "adopter")
    command = repo / ".claude/commands/session-start.md"
    command.parent.mkdir(parents=True)
    command.write_text("Our session start.\n", encoding="utf-8")
    repo, env = _lite_installed_at(repo, env)
    assert not (repo / ".claude/skills/session-start").exists()
    assert _l4(repo, env).returncode == 0
    verify = _l5(repo, env)
    assert verify.returncode == 0, verify.stdout
    assert ".claude/skills/session-start/SKILL.md" in verify.stdout
    assert "as L5 expects" in verify.stdout


@pytest.mark.parametrize(
    "path", ["docs/agentic-dev-kit/lite/lite-review.md", ".agents/skills/wrap-up/SKILL.md", ".claude/skills/review/SKILL.md"]
)
def test_verify_lite_stops_on_a_lite_file_missing_at_install(tmp_path: Path, path: str) -> None:
    """At install nothing was left absent by a decision: a missing file is a stop,
    not a `declined` row read as accepted (the upgrade's `--leave-absent`)."""
    repo, env = _lite_installed(tmp_path, "sh")
    (repo / path).unlink()
    assert _l4(repo, env).returncode == 0
    verify = _l5(repo, env)
    assert verify.returncode == 1, verify.stdout
    assert f"stop: verify (L5): {path} is missing" in verify.stdout
    assert "NOT intact" in verify.stdout


def test_verify_lite_stops_on_a_skill_edited_after_l4(tmp_path: Path) -> None:
    repo, env = _lite_installed(tmp_path, "sh")
    assert _l4(repo, env).returncode == 0
    edited = repo / ".claude/skills/wrap-up/SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "Our edit.\n", encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1, verify.stdout
    assert "stop: verify (L5): .claude/skills/wrap-up/SKILL.md is" in verify.stdout


def test_verify_lite_refuses_without_a_record_l4_wrote_from_this_kit(tmp_path: Path) -> None:
    repo, env = _lite_installed(tmp_path, "sh")
    verify = _l5(repo, env)
    assert verify.returncode == 1
    assert verify.stdout.startswith("refused:") and "run L4" in verify.stdout
    assert _l4(repo, env).returncode == 0
    record = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    record["kit_commit"] = "0" * 40
    (repo / "kit-manifest.json").write_text(json.dumps(record), encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1 and "is not a record L4 wrote from the kit" in verify.stdout


@pytest.mark.parametrize(
    "args, message",
    [
        (["--verify-lite", "--root", "/abs"], "requires --from-kit and --root"),
        (["--verify-lite", "--from-kit", str(REPO_ROOT), "--root", "rel"], "absolute --root"),
        (["--verify-lite", "--from-kit", "rel", "--root", "/abs"], "absolute --from-kit"),
    ],
)
def test_verify_lite_usage(tmp_path: Path, args: list[str], message: str) -> None:
    result = _doctor(*args, env=_git_env(tmp_path))
    assert result.returncode == 2
    assert message in result.stderr


# Every other mode and option: --verify-lite combines with none of them, so none is
# silently ignored.
@pytest.mark.parametrize(
    "extra",
    [
        ["--json"],
        ["--generate-manifest"],
        ["--record-install"],
        ["--upgrade-lite"],
        ["--keep", ".claude/skills/review/SKILL.md"],
        ["--adapter-report"],
        ["--adapter-source", "/abs"],
        ["--manifest", "/abs/kit-manifest.json"],
        ["--baseline", "/abs/kit-manifest.json"],
        ["--branch", "main"],
        ["--apply"],
        ["--kit-commit", "abc1234"],
        ["--take", "docs/agentic-dev-kit/lite/lite-review.md"],
        ["--leave-absent", "docs/agentic-dev-kit/lite/lite-review.md"],
    ],
)
def test_verify_lite_combines_with_no_other_mode(tmp_path: Path, extra: list[str]) -> None:
    args = ["--verify-lite", "--from-kit", str(REPO_ROOT), "--root", "/abs", *extra]
    result = _doctor(*args, env=_git_env(tmp_path))
    assert result.returncode == 2
    assert f"--verify-lite cannot be combined with {extra[0]}" in result.stderr


def test_adopt_lite_l3_l4_l5_take_a_path_with_a_blank(tmp_path: Path) -> None:
    """Each placeholder sits inside single quotes, so a written-out path with a
    blank is one word (adversarial, PR 1423 F3)."""
    spaced = tmp_path / "sp ace"
    spaced.mkdir()
    repo, env = _lite_installed(spaced, "sh")
    record = subprocess.run(
        ["sh", "-c", _fill(_adopt_lite_blocks()[1].strip(), str(repo), str(REPO_ROOT)).replace(
            "uv run ", f"{sys.executable} ", 1
        )],
        cwd=repo, env=env, capture_output=True, text=True, timeout=120,
    )
    assert record.returncode == 0, record.stderr
    verify = subprocess.run(
        ["sh", "-c", _fill(_adopt_lite_blocks()[2].strip(), str(repo), str(REPO_ROOT)).replace(
            "uv run ", f"{sys.executable} ", 1
        )],
        cwd=repo, env=env, capture_output=True, text=True, timeout=120,
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert "as L5 expects" in verify.stdout


def test_verify_lite_names_the_install_not_the_upgrade(tmp_path: Path) -> None:
    """A config or record L3 or L4 got wrong points back at the install."""
    repo, env = _lite_installed(tmp_path, "sh")
    assert _l4(repo, env).returncode == 0
    config = repo / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("version: 2", "version: 1"), encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1
    assert "L3 writes the kit's kit_version" in verify.stdout
    assert "migration" not in verify.stdout and "U4" not in verify.stdout
    config.write_text(config.read_text(encoding="utf-8").replace("profile: lite", "profile: full"), encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1 and verify.stdout.startswith("refused: profile: full")
    assert "adopt.md L1" in verify.stdout and "upgrade.md" not in verify.stdout
    config.write_text(config.read_text(encoding="utf-8").replace("profile: full", "profile: lite"), encoding="utf-8")
    record = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    record["profile"] = "full"
    (repo / "kit-manifest.json").write_text(json.dumps(record), encoding="utf-8")
    verify = _l5(repo, env)
    assert verify.returncode == 1
    assert "the record L4 wrote reads" in verify.stdout and "U4" not in verify.stdout


@pytest.mark.parametrize(
    "phrase",
    ["verify (L5):", "intact for this adoption — lite install", "as L5 expects", "stop: verify (L5):", "refused:"],
)
def test_each_output_adopt_l5_quotes_is_one_the_engine_prints(phrase: str) -> None:
    assert phrase in _adopt_lite_section()
    assert phrase in KIT_DOCTOR.read_text(encoding="utf-8")
