"""`kit_doctor.py --upgrade-lite`: the lite upgrade as one engine operation (#1406).

Every test runs the engine from a kit *clone*, as upgrade.md's lite section runs it:
a fixture kit repository holds an old lite kit at its first commit and the current
one at its second, a bare repository stands in for the kit's URL, and each test
clones it. The adopter is installed from the old commit and recorded, then upgraded.
The environment holds no `REPO`, `KIT` or `LITE_*` variable: every input is an
argument on the call, which is the fresh-shell case #1410 is about.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(engine_dir(Path(__file__)))
MANIFEST = json.loads((REPO_ROOT / "kit-manifest.json").read_text(encoding="utf-8"))
LITE_SOURCES: list[str] = list(MANIFEST["profiles"]["lite"])
SKILL_DIRS = {"claude": ".claude/skills", "codex": ".agents/skills"}
FRAGMENT = "changelog.d/lite-fixture.md"
FRAGMENT_TEXT = "## The fixture kit's newer lite copies\n\nTake them.\n"
OLD_LINE = b"\nAn older kit's line.\n"
# What the kit clone needs to run the engine and to be read by it.
KIT_PARTS = (
    ".gitignore",
    "kit-manifest.json",
    "scripts/kit_doctor.py",
    "scripts/lib",
    "docs/agentic-dev-kit/lite",
    "docs/agentic-dev-kit/workflows/adopt.md",
)


def _installed(rel: str) -> str:
    parts = rel.split("/")
    if "adapters" in parts:
        return f"{SKILL_DIRS[parts[-3]]}/{parts[-2]}/SKILL.md"
    return rel


INSTALLED = {_installed(rel): rel for rel in LITE_SOURCES}
DOCS = sorted(p for p in INSTALLED if p.startswith("docs/"))
SKILLS = sorted(p for p in INSTALLED if not p.startswith("docs/"))


def _env(home: Path) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("GIT_", "LITE_")) and k not in ("REPO", "KIT")
    }
    env.update(
        HOME=str(home),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
        PYTHONDONTWRITEBYTECODE="1",
    )
    return env


def _git(cwd: Path, env: dict[str, str], *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def kit_upstream(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """A kit repository with an old lite kit at commit A and the current kit at B,
    and a bare clone of it standing in for the kit's URL."""
    base = tmp_path_factory.mktemp("kit")
    env = _env(base)
    src = base / "src"
    src.mkdir()
    for part in KIT_PARTS:
        origin = REPO_ROOT / part
        if origin.is_dir():
            shutil.copytree(origin, src / part, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            (src / part).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, src / part)
    # Commit A: every lite file one line longer, the manifest recording those copies,
    # and adopt.md's lite section as it was before #1401 added its upgrade sentence.
    old = json.loads(json.dumps(MANIFEST))
    for rel in LITE_SOURCES:
        target = src / rel
        target.write_bytes((REPO_ROOT / rel).read_bytes() + OLD_LINE)
        old["files"][rel]["sha256"] = _sha(target)
    (src / "kit-manifest.json").write_text(json.dumps(old, indent=2), encoding="utf-8")
    adopt = src / "docs/agentic-dev-kit/workflows/adopt.md"
    current_adopt = adopt.read_text(encoding="utf-8")
    added = (
        " To take a newer kit, follow the *Lite profile* section\n"
        "  of `docs/agentic-dev-kit/workflows/upgrade.md` in the kit,\n"
        "  https://github.com/topij/agentic-dev-kit (or the fork this repository adopted from)."
    )
    assert added in current_adopt
    adopt.write_text(current_adopt.replace(added, ""), encoding="utf-8")
    _git(src, env, "-c", "init.defaultBranch=main", "init", "-q")
    _git(src, env, "add", "-A")
    _git(src, env, "commit", "-qm", "old kit")
    old_commit = _git(src, env, "rev-parse", "HEAD")
    old_kit = base / "old-kit"
    _git(base, env, "clone", "-q", str(src), str(old_kit))
    # Commit B: the current kit, with a changelog fragment.
    for rel in LITE_SOURCES:
        shutil.copy2(REPO_ROOT / rel, src / rel)
    shutil.copy2(REPO_ROOT / "kit-manifest.json", src / "kit-manifest.json")
    adopt.write_text(current_adopt, encoding="utf-8")
    (src / "changelog.d").mkdir()
    (src / FRAGMENT).write_text(FRAGMENT_TEXT, encoding="utf-8")
    _git(src, env, "add", "-A")
    _git(src, env, "commit", "-qm", "new kit")
    bare = base / "upstream.git"
    _git(base, env, "clone", "-q", "--bare", str(src), str(bare))
    return {"bare": bare, "old_kit": old_kit, "old_commit": old_commit, "head": _git(src, env, "rev-parse", "HEAD")}


@pytest.fixture
def kit(tmp_path: Path, kit_upstream: dict) -> Path:
    clone = tmp_path / "kit"
    _git(tmp_path, _env(tmp_path), "clone", "-q", str(kit_upstream["bare"]), str(clone))
    return clone


def _install(
    tmp_path: Path,
    kit_upstream: dict,
    *,
    keep: tuple[str, ...] = (),
    without: tuple[str, ...] = (),
    protected: str | None = None,
    record_commit: bool = True,
) -> tuple[Path, dict[str, str]]:
    """A lite repository installed from the old kit and recorded, as adopt.md's lite
    profile leaves one: committed on `main`."""
    env = _env(tmp_path)
    repo = tmp_path / "adopter"
    repo.mkdir()
    _git(repo, env, "-c", "init.defaultBranch=main", "init", "-q")
    old_kit: Path = kit_upstream["old_kit"]
    for path, rel in INSTALLED.items():
        if path in without:
            continue
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if path in keep:
            target.write_text("---\nname: ours\ndescription: Ours.\n---\n\nOur skill.\n", encoding="utf-8")
        else:
            shutil.copy2(old_kit / rel, target)
    (repo / "config").mkdir()
    config = (
        "profile: lite\nkit:\n  version: 2\npaths:\n  handoff: docs/plan.md\n"
        "  friction_log: docs/friction-log.md\n"
    )
    if protected:
        config += f"vcs:\n  protected_branch: {protected}\n"
    (repo / "config/dev-model.yaml").write_text(config, encoding="utf-8")
    (repo / "docs/plan.md").write_text("# Plan\n\n## Workstreams\n", encoding="utf-8")
    (repo / "docs/friction-log.md").write_text("# Friction log\n", encoding="utf-8")
    adopt = (old_kit / "docs/agentic-dev-kit/workflows/adopt.md").read_text(encoding="utf-8")
    section = adopt.split("```markdown\n", 1)[1].split("```", 1)[0]
    (repo / "AGENTS.md").write_text(
        "# Agents\n\n" + section + "\n### session-start\n\n- Our deploy check.\n", encoding="utf-8"
    )
    keep_args = [arg for path in keep for arg in ("--keep", path)]
    record = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/kit_doctor.py"), "--record-install",
         "--from-kit", str(old_kit), "--root", str(repo), *keep_args],
        env=env, capture_output=True, text=True, timeout=120,
    )
    assert record.returncode == 0, record.stderr
    if not record_commit:
        baseline = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
        baseline["kit_commit"] = None
        (repo / "kit-manifest.json").write_text(json.dumps(baseline), encoding="utf-8")
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-qm", "lite install")
    return repo, env


def _doctor(kit: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(kit / "scripts/kit_doctor.py"), *args],
        env=env, capture_output=True, text=True, timeout=300,
    )


def _read(kit: Path, repo: Path, env: dict[str, str], branch: str = "main", *, json_out: bool = True):
    args = ["--upgrade-lite", "--root", str(repo), "--branch", branch]
    done = _doctor(kit, env, *args, *(["--json"] if json_out else []))
    return done


def _plan(kit: Path, repo: Path, env: dict[str, str], branch: str = "main") -> dict:
    done = _read(kit, repo, env, branch)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout)


def _apply(kit: Path, repo: Path, env: dict[str, str], *flags: str, branch: str = "main", commit: str | None = None):
    head = commit or _git(kit, env, "rev-parse", "HEAD")
    return _doctor(
        kit, env, "--upgrade-lite", "--root", str(repo), "--branch", branch, "--apply",
        "--kit-commit", head, *flags,
    )


def _report(kit: Path, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return _doctor(kit, env, "--root", str(repo), "--manifest", str(kit / "kit-manifest.json"))


def _has_line(done: subprocess.CompletedProcess[str], prefix: str) -> bool:
    return any(line.startswith(prefix) for line in done.stdout.splitlines())


def _snapshot(repo: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(repo)): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if ".git" not in p.relative_to(repo).parts and p.is_file() and not p.is_symlink()
    }


# --- The end-to-end path ---------------------------------------------------------


def test_reads_the_plan_then_takes_every_stale_file_and_records_an_intact_install(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    kept = (".claude/skills/review/SKILL.md", ".agents/skills/wrap-up/SKILL.md")
    repo, env = _install(tmp_path, kit_upstream, keep=kept)
    plan = _plan(kit, repo, env)
    actions = {row["path"]: (row["state"], row["action"]) for row in plan["files"]}
    assert {actions[p] for p in kept} == {("declined", "keep")}
    assert {actions[p] for p in INSTALLED if p not in kept} == {("stale", "take")}
    assert plan["record"] == "owed" and plan["kept"] == sorted(kept)
    assert plan["kit"]["commit"] == kit_upstream["head"]
    assert plan["baseline"]["kit_commit"] == kit_upstream["old_commit"]

    done = _apply(kit, repo, env)
    assert done.returncode == 0, done.stdout + done.stderr
    took = [line.removeprefix("took: ") for line in done.stdout.splitlines() if line.startswith("took: ")]
    assert sorted(took) == sorted(p for p in INSTALLED if p not in kept)
    assert sorted(line.removeprefix("kept: ") for line in done.stdout.splitlines() if line.startswith("kept: ")) == sorted(kept)
    assert f"recorded: kit-manifest.json for kit {kit_upstream['head'][:12]}" in done.stdout
    staged = [line.removeprefix("stage: ") for line in done.stdout.splitlines() if line.startswith("stage: ")]
    assert sorted(staged) == sorted([*took, "kit-manifest.json"])
    for path in kept:
        assert (repo / path).read_text(encoding="utf-8").endswith("Our skill.\n")

    report = _report(kit, repo, env)
    assert report.returncode == 0, report.stdout + report.stderr
    assert "intact for this adoption — lite install, 2 file(s) declined" in report.stdout
    # U6: the read mode now says the record waits only on the commit, then nothing.
    assert _plan(kit, repo, env)["record"] == "recorded-uncommitted"
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-qm", "upgrade")
    after = _plan(kit, repo, env)
    assert after["record"] == "not-owed" and after["kept"] == sorted(kept)
    again = _apply(kit, repo, env)
    assert again.returncode == 0 and again.stdout.startswith("nothing to do"), again.stdout


def test_the_text_report_names_each_row_and_the_apply_command(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    edited = repo / DOCS[0]
    edited.write_text(edited.read_text(encoding="utf-8") + "Our edit.\n", encoding="utf-8")
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 0, done.stdout + done.stderr
    head = kit_upstream["head"]
    assert f"kit: {kit} at {head[:12]}" in done.stdout
    assert "no protected branch named — direct commits" in done.stdout
    assert f"record: owed — the committed baseline names {kit_upstream['old_commit'][:12]}" in done.stdout
    assert f"stale-and-edited  {DOCS[0]} → decide (edited here): --take {DOCS[0]}" in done.stdout
    assert f"--apply --kit-commit {head} [--take {DOCS[0]}]" in done.stdout


# --- The record and the kept list ------------------------------------------------


def test_a_failed_record_leaves_the_old_baseline_and_a_rerun_still_carries_kept(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    """The record goes through `record_install_manifest`; a present lite file that is
    not the kit's copy and was not kept makes it partial, and the old baseline stays."""
    kept = (".claude/skills/review/SKILL.md",)
    repo, env = _install(tmp_path, kit_upstream, keep=kept)
    before = (repo / "kit-manifest.json").read_bytes()
    # A full-profile file the repository has at a kit path: present, not the kit's copy.
    stray = repo / "docs/agentic-dev-kit/workflows/wrap-up.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("ours\n", encoding="utf-8")
    failed = _apply(kit, repo, env)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert "refused: docs/agentic-dev-kit/workflows/wrap-up.md is not the kit's copy" in failed.stdout
    assert "not recorded: kit-manifest.json is unchanged" in failed.stdout
    assert (repo / "kit-manifest.json").read_bytes() == before
    stray.unlink()
    retried = _apply(kit, repo, env)
    assert retried.returncode == 0, retried.stdout + retried.stderr
    assert f"kept: {kept[0]}" in retried.stdout
    recorded = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    assert recorded["kept"] == [INSTALLED[kept[0]]]


def test_a_working_tree_record_left_by_an_abandoned_attempt_is_not_read(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    kept = (".agents/skills/review/SKILL.md",)
    repo, env = _install(tmp_path, kit_upstream, keep=kept)
    # What a record that exited 1 leaves: a manifest without `kept` or `not_installed`.
    (repo / "kit-manifest.json").write_text(json.dumps({"kit_commit": None, "files": {}}), encoding="utf-8")
    plan = _plan(kit, repo, env)
    assert plan["baseline"]["working_tree_differs"] is True
    assert plan["kept"] == list(kept) and plan["record"] == "owed"
    done = _apply(kit, repo, env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"kept: {kept[0]}" in done.stdout


def test_owes_the_record_until_the_committed_baseline_names_the_kit(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    """A session that copied by hand and stopped: every file reads unchanged, and
    the record is still owed until a baseline naming the kit is committed."""
    repo, env = _install(tmp_path, kit_upstream)
    for path, rel in INSTALLED.items():
        shutil.copy2(kit / rel, repo / path)
    plan = _plan(kit, repo, env)
    assert {row["state"] for row in plan["files"]} == {"unchanged"}
    assert plan["record"] == "owed"
    done = _apply(kit, repo, env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert not _has_line(done, "took: ") and _has_line(done, "recorded: ")
    assert _plan(kit, repo, env)["record"] == "recorded-uncommitted"


def test_a_baseline_with_no_provenance_is_named_and_owes_the_record(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream, record_commit=False)
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "baseline (committed): recorded, install provenance unknown" in done.stdout
    assert "record: owed" in done.stdout


def test_no_committed_baseline_stops(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    _git(repo, env, "rm", "-q", "--cached", "kit-manifest.json")
    _git(repo, env, "commit", "-qm", "untrack the baseline")
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1
    assert "refused: no committed kit-manifest.json written by --record-install" in done.stdout


# --- Decisions --------------------------------------------------------------------


def test_an_edited_file_waits_for_a_decision_then_take_or_keep_settles_it(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    doc, skill = repo / DOCS[1], repo / SKILLS[0]
    for edited in (doc, skill):
        edited.write_text(edited.read_text(encoding="utf-8") + "Our edit.\n", encoding="utf-8")
    plan = {row["path"]: row for row in _plan(kit, repo, env)["files"]}
    assert plan[DOCS[1]]["action"] == "decide" and plan[DOCS[1]]["options"] == [f"--take {DOCS[1]}"]
    assert plan[SKILLS[0]]["options"] == [f"--take {SKILLS[0]}", f"--keep {SKILLS[0]}"]

    before = _snapshot(repo)
    undecided = _apply(kit, repo, env)
    assert undecided.returncode == 1
    assert f"refused: {DOCS[1]} is stale-and-edited" in undecided.stdout
    assert f"refused: {SKILLS[0]} is stale-and-edited" in undecided.stdout
    assert _snapshot(repo) == before

    doc_kept = _apply(kit, repo, env, "--keep", DOCS[1], "--take", SKILLS[0])
    assert doc_kept.returncode == 2 and "is a doc, which cannot be kept" in doc_kept.stderr
    assert _snapshot(repo) == before

    done = _apply(kit, repo, env, "--take", DOCS[1], "--keep", SKILLS[0])
    assert done.returncode == 0, done.stdout + done.stderr
    assert doc.read_bytes() == (kit / INSTALLED[DOCS[1]]).read_bytes()
    assert skill.read_text(encoding="utf-8").endswith("Our edit.\n")
    assert f"kept: {SKILLS[0]}" in done.stdout
    assert "intact for this adoption" in _report(kit, repo, env).stdout


@pytest.mark.parametrize("decision", ["--take", "--leave-absent"])
def test_a_removed_file_and_a_kept_skill_gone_from_disk_are_decided(
    tmp_path: Path, kit_upstream: dict, kit: Path, decision: str
) -> None:
    kept = SKILLS[1]
    repo, env = _install(tmp_path, kit_upstream, keep=(kept,))
    (repo / DOCS[2]).unlink()
    (repo / kept).unlink()
    _git(repo, env, "commit", "-qam", "lose two")
    plan = {row["path"]: row for row in _plan(kit, repo, env)["files"]}
    assert (plan[DOCS[2]]["state"], plan[DOCS[2]]["action"]) == ("removed", "decide")
    assert (plan[kept]["state"], plan[kept]["action"]) == ("declined", "decide")
    assert _apply(kit, repo, env).returncode == 1

    done = _apply(kit, repo, env, decision, DOCS[2], decision, kept)
    assert done.returncode == 0, done.stdout + done.stderr
    if decision == "--take":
        assert (repo / DOCS[2]).is_file() and (repo / kept).is_file()
    else:
        assert not (repo / DOCS[2]).exists() and not (repo / kept).exists()
        assert f"left absent: {kept}" in done.stdout
    recorded = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    assert recorded["kept"] == []


def test_leave_absent_refuses_a_file_that_is_there(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    done = _apply(kit, repo, env, "--leave-absent", DOCS[0])
    assert done.returncode == 2 and f"--leave-absent names {DOCS[0]}, which is there" in done.stderr


def test_installs_a_doc_the_kit_added_since_the_baseline(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    added = DOCS[2]
    repo, env = _install(tmp_path, kit_upstream, without=(added,))
    # A baseline recorded by an older kit_doctor, which did not know the path at all.
    baseline = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    baseline["not_installed"].remove(INSTALLED[added])
    (repo / "kit-manifest.json").write_text(json.dumps(baseline), encoding="utf-8")
    _git(repo, env, "commit", "-qam", "baseline from an older kit_doctor")
    plan = {row["path"]: row for row in _plan(kit, repo, env)["files"]}
    assert (plan[added]["state"], plan[added]["action"]) == ("new-upstream", "take")
    done = _apply(kit, repo, env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert (repo / added).read_bytes() == (kit / added).read_bytes()


@pytest.mark.parametrize(
    "entry",
    [
        "./docs/agentic-dev-kit/lite/lite-review.md",
        "x/docs/agentic-dev-kit/lite/lite-review.md.bak",
        "docs/agentic-dev-kit/lite/lite-review",
        "README.md",
    ],
)
@pytest.mark.parametrize("flag", ["--take", "--keep", "--leave-absent"])
def test_a_flag_naming_a_path_that_is_not_a_lite_path_changes_nothing(
    tmp_path: Path, kit_upstream: dict, kit: Path, entry: str, flag: str
) -> None:
    """A near miss is refused, never skipped: skipped, a `new-upstream` doc would be
    recorded as declined and never offered again."""
    repo, env = _install(tmp_path, kit_upstream)
    before = _snapshot(repo)
    done = _apply(kit, repo, env, flag, entry)
    assert done.returncode == 2, done.stdout + done.stderr
    assert f"{flag} {entry!r} is not a lite path" in done.stderr
    assert _snapshot(repo) == before


def test_every_lite_path_is_one_a_flag_takes(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    assert len(INSTALLED) == 9, INSTALLED
    repo, env = _install(tmp_path, kit_upstream)
    flags = [arg for path in INSTALLED for arg in ("--take", path)]
    done = _apply(kit, repo, env, *flags)
    assert done.returncode == 0, done.stdout + done.stderr
    took = sorted(line.removeprefix("took: ") for line in done.stdout.splitlines() if line.startswith("took: "))
    assert took == sorted(INSTALLED)


def test_a_path_in_two_decision_flags_is_refused(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    done = _apply(kit, repo, env, "--take", SKILLS[0], "--keep", SKILLS[0])
    assert done.returncode == 2 and "more than one decision flag" in done.stderr


# --- The copy guards ---------------------------------------------------------------


def _all_or_nothing(repo: Path, kit: Path, env: dict[str, str], *flags: str) -> subprocess.CompletedProcess[str]:
    before = _snapshot(repo)
    manifest = (repo / "kit-manifest.json").read_bytes()
    done = _apply(kit, repo, env, *flags)
    assert done.returncode == 1, done.stdout + done.stderr
    assert not _has_line(done, "took: ") and not _has_line(done, "recorded: ")
    assert "nothing taken, nothing recorded" in done.stdout
    assert _snapshot(repo) == before
    assert (repo / "kit-manifest.json").read_bytes() == manifest
    return done


@pytest.mark.parametrize("dangling", [False, True])
def test_refuses_a_symlinked_file_and_takes_nothing(
    tmp_path: Path, kit_upstream: dict, kit: Path, dangling: bool
) -> None:
    """Every other row is a plain `stale` take, and none of them is taken either."""
    repo, env = _install(tmp_path, kit_upstream)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = repo / DOCS[0]
    if not dangling:
        shutil.copy2(link, outside / "doc.md")
    link.unlink()
    link.symlink_to(outside / "doc.md")
    flags = ("--take", DOCS[0]) if dangling else ()
    if dangling:
        _git(repo, env, "add", "-A")
        _git(repo, env, "commit", "-qm", "dangle")
        flags = ("--take", DOCS[0])
    done = _all_or_nothing(repo, kit, env, *flags)
    assert f"refused: {link} is a symlink" in done.stdout
    assert dangling == (not (outside / "doc.md").exists())


def test_refuses_a_skill_under_a_symlinked_directory(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream, without=tuple(p for p in SKILLS if p.startswith(".agents")))
    baseline = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / ".agents").mkdir()
    (repo / ".agents/skills").symlink_to(outside)
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-qm", "link")
    target = ".agents/skills/review/SKILL.md"
    assert INSTALLED[target] in baseline["not_installed"]
    done = _all_or_nothing(repo, kit, env, "--take", target)
    assert f"refused: a directory on the path of {repo / target} is a symlink" in done.stdout
    assert list(outside.iterdir()) == []


def test_refuses_a_directory_where_a_file_belongs(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    (repo / DOCS[1]).unlink()
    (repo / DOCS[1]).mkdir()
    (repo / DOCS[1] / "keep").write_text("x\n", encoding="utf-8")
    done = _all_or_nothing(repo, kit, env, "--take", DOCS[1])
    assert f"refused: {repo / DOCS[1]} is a directory" in done.stdout


@pytest.mark.parametrize("dangling", [False, True])
def test_refuses_a_claude_skill_a_command_would_be_shadowed_by(
    tmp_path: Path, kit_upstream: dict, kit: Path, dangling: bool
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    command = repo / ".claude/commands/review.md"
    command.parent.mkdir(parents=True)
    if dangling:
        command.symlink_to(tmp_path / "nowhere.md")
    else:
        command.write_text("our command\n", encoding="utf-8")
    done = _all_or_nothing(repo, kit, env)
    assert f"refused: {command} would be shadowed by {repo / '.claude/skills/review/SKILL.md'}" in done.stdout
    assert done.stdout.count("refused: ") == 1, done.stdout


def test_a_command_does_not_refuse_the_codex_skill_of_its_name(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    """Only the Claude runtime has commands: the Codex skill is taken (R3 F5)."""
    repo, env = _install(tmp_path, kit_upstream, keep=(".claude/skills/review/SKILL.md",))
    command = repo / ".claude/commands/review.md"
    command.parent.mkdir(parents=True)
    command.write_text("our command\n", encoding="utf-8")
    done = _apply(kit, repo, env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "took: .agents/skills/review/SKILL.md" in done.stdout


def test_refuses_a_path_whose_parent_is_a_file(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream, without=tuple(p for p in SKILLS if p.startswith(".agents")))
    (repo / ".agents").write_text("a file where a directory belongs\n", encoding="utf-8")
    done = _all_or_nothing(repo, kit, env, "--take", ".agents/skills/review/SKILL.md")
    assert f"refused: {repo / '.agents'} is not a directory" in done.stdout


def test_refuses_a_hardlinked_target(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    """A rename would leave the other name holding the old copy."""
    repo, env = _install(tmp_path, kit_upstream)
    os.link(repo / DOCS[0], tmp_path / "alias.md")
    done = _all_or_nothing(repo, kit, env)
    assert f"refused: {repo / DOCS[0]} is hardlinked" in done.stdout


def test_refuses_a_baseline_that_is_a_symlink(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    outside = tmp_path / "baseline.json"
    shutil.copy2(repo / "kit-manifest.json", outside)
    (repo / "kit-manifest.json").unlink()
    (repo / "kit-manifest.json").symlink_to(outside)
    before = outside.read_bytes()
    done = _apply(kit, repo, env)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "kit-manifest.json is not a regular file" in done.stdout
    assert not _has_line(done, "took: ") and outside.read_bytes() == before


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root writes a read-only directory")
def test_a_failed_copy_stops_before_the_record(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    manifest = (repo / "kit-manifest.json").read_bytes()
    lite = repo / "docs/agentic-dev-kit/lite"
    lite.chmod(0o500)
    try:
        done = _apply(kit, repo, env)
    finally:
        lite.chmod(0o700)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "stopped: cannot write" in done.stdout and "nothing recorded" in done.stdout
    assert not _has_line(done, "recorded: ")
    assert (repo / "kit-manifest.json").read_bytes() == manifest
    retried = _apply(kit, repo, env)
    assert retried.returncode == 0, retried.stdout + retried.stderr


def test_takes_a_root_with_a_trailing_slash_under_a_symlinked_ancestor(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    repo, env = _install(real, kit_upstream)
    linked = tmp_path / "linked"
    linked.symlink_to(real)
    head = _git(kit, env, "rev-parse", "HEAD")
    done = _doctor(kit, env, "--upgrade-lite", "--root", f"{linked}/adopter/", "--branch", "main",
                   "--apply", "--kit-commit", head)
    assert done.returncode == 0, done.stdout + done.stderr
    assert (repo / DOCS[0]).read_bytes() == (kit / DOCS[0]).read_bytes()


# --- The write target ----------------------------------------------------------------


def _wrong_target(repo: Path, env: dict[str, str], how: str) -> tuple[Path, str]:
    """A target and branch the check must refuse."""
    if how == "other-branch":
        return repo, "feat/upgrade"
    if how == "detached":
        _git(repo, env, "checkout", "-q", "--detach")
        return repo, "main"
    if how == "subdirectory":
        return repo / "docs", "main"
    if how == "not-a-checkout":
        plain = repo.parent / "plain"
        plain.mkdir()
        return plain, "main"
    if how in ("protected-committed", "protected-staged", "protected-working"):
        config = repo / "config/dev-model.yaml"
        text = config.read_text(encoding="utf-8") + "vcs:\n  protected_branch: main\n"
        if how == "protected-committed":
            config.write_text(text, encoding="utf-8")
            _git(repo, env, "commit", "-qam", "protect main")
        elif how == "protected-staged":
            original = config.read_text(encoding="utf-8")
            config.write_text(text, encoding="utf-8")
            _git(repo, env, "add", "config/dev-model.yaml")
            config.write_text(original, encoding="utf-8")
        else:
            config.write_text(text, encoding="utf-8")
        return repo, "main"
    if how == "unusable-protected":
        config = repo / "config/dev-model.yaml"
        config.write_text(config.read_text(encoding="utf-8") + "vcs:\n  protected_branch:\n", encoding="utf-8")
        return repo, "main"
    if how == "unparseable-config":
        config = repo / "config/dev-model.yaml"
        config.write_text(config.read_text(encoding="utf-8") + "vcs: [\n", encoding="utf-8")
        return repo, "main"
    raise AssertionError(how)


# Each wrong target and the refusal that must name it, so a guard removed from the
# check cannot hide behind a later one that happens to refuse the same tree.
WRONG_TARGETS = {
    "other-branch": "is on main, not feat/upgrade",
    "detached": "is not on a branch",
    "subdirectory": "is not the top of a checkout",
    "not-a-checkout": "is not the top of a checkout",
    "protected-committed": "refused: main is the protected branch (vcs.protected_branch in the committed",
    "protected-staged": "refused: main is the protected branch (vcs.protected_branch in the staged config)",
    "protected-working": "refused: main is the protected branch (vcs.protected_branch in the working tree config)",
    "unusable-protected": "vcs.protected_branch in the working tree config/dev-model.yaml is None",
    "unparseable-config": "the working tree config/dev-model.yaml does not parse",
}


@pytest.mark.parametrize("mode", ["read", "apply"])
@pytest.mark.parametrize("how", WRONG_TARGETS)
def test_a_wrong_target_is_refused_and_nothing_is_written(
    tmp_path: Path, kit_upstream: dict, kit: Path, how: str, mode: str
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    target, branch = _wrong_target(repo, env, how)
    before = _snapshot(repo)
    if mode == "read":
        done = _read(kit, target, env, branch, json_out=False)
    else:
        done = _apply(kit, target, env, branch=branch)
    assert done.returncode == 1, done.stdout + done.stderr
    assert WRONG_TARGETS[how] in done.stdout, done.stdout
    assert "took: " not in done.stdout
    assert _snapshot(repo) == before


def test_a_task_branch_of_a_protected_repository_is_the_target(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream, protected="main")
    _git(repo, env, "switch", "-qc", "chore/kit-upgrade")
    done = _read(kit, repo, env, "chore/kit-upgrade", json_out=False)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "protected branch main (committed, staged, working tree)" in done.stdout
    applied = _apply(kit, repo, env, branch="chore/kit-upgrade")
    assert applied.returncode == 0, applied.stdout + applied.stderr


@pytest.mark.parametrize(
    "args",
    [
        ["--upgrade-lite", "--root", "{repo}"],
        ["--upgrade-lite", "--branch", "main"],
        ["--upgrade-lite", "--root", "{repo}", "--branch", "main", "--apply"],
        ["--upgrade-lite", "--root", "{repo}", "--branch", "main", "--take", DOCS[0]],
        ["--upgrade-lite", "--root", "{repo}", "--branch", "main", "--record-install"],
        ["--root", "{repo}", "--branch", "main"],
        ["--upgrade-lite", "--root", ".", "--branch", "main"],
    ],
)
def test_usage_errors_exit_2_and_write_nothing(
    tmp_path: Path, kit_upstream: dict, kit: Path, args: list[str]
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    before = _snapshot(repo)
    done = _doctor(kit, env, *[a.replace("{repo}", str(repo)) for a in args])
    assert done.returncode == 2, done.stdout + done.stderr
    assert _snapshot(repo) == before


# --- The kit clone (#1405, #1410) -------------------------------------------------------


def _advance(tmp_path: Path, bare: Path, env: dict[str, str]) -> str:
    work = tmp_path / "advance"
    _git(tmp_path, env, "clone", "-q", str(bare), str(work))
    (work / "changelog.d/later.md").write_text("## Later\n", encoding="utf-8")
    _git(work, env, "add", "-A")
    _git(work, env, "commit", "-qm", "later")
    _git(work, env, "push", "-q", "origin", "HEAD")
    return _git(work, env, "rev-parse", "HEAD")


def test_a_stale_clone_is_refused_naming_both_commits(tmp_path: Path, kit_upstream: dict) -> None:
    env = _env(tmp_path)
    bare = tmp_path / "upstream.git"
    _git(tmp_path, env, "clone", "-q", "--bare", str(kit_upstream["bare"]), str(bare))
    kit = tmp_path / "kit"
    _git(tmp_path, env, "clone", "-q", str(bare), str(kit))
    repo, env = _install(tmp_path, kit_upstream)
    assert _read(kit, repo, env).returncode == 0
    later = _advance(tmp_path, bare, env)
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1
    assert f"is at {kit_upstream['head'][:12]} and its origin at {later[:12]}" in done.stdout
    # Apply pins the commit U3 approved, and names the newer origin without refusing.
    applied = _apply(kit, repo, env)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert f"note: the kit's origin has moved to {later[:12]}" in applied.stdout


def test_a_dirty_clone_is_refused(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    (kit / DOCS[0]).write_text("tampered\n", encoding="utf-8")
    for mode in ("read", "apply"):
        done = _read(kit, repo, env, json_out=False) if mode == "read" else _apply(kit, repo, env)
        assert done.returncode == 1 and f"the kit clone {kit} is not clean" in done.stdout


def test_an_untracked_file_in_the_clone_is_refused(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    (kit / "stray.md").write_text("x\n", encoding="utf-8")
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1 and "is not clean" in done.stdout


def test_another_clone_at_another_commit_is_refused_by_kit_commit(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    """#1410: a second clone made after U3, at a newer commit, is not the kit U3 approved."""
    repo, env = _install(tmp_path, kit_upstream)
    before = _snapshot(repo)
    done = _apply(kit, repo, env, commit=kit_upstream["old_commit"])
    assert done.returncode == 1
    assert f"is at {kit_upstream['head'][:12]}, not --kit-commit {kit_upstream['old_commit']}" in done.stdout
    assert _snapshot(repo) == before


def test_an_unreachable_origin_refuses_the_read(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    _git(kit, env, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1 and "cannot read the HEAD of" in done.stdout
    applied = _apply(kit, repo, env)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert "note: cannot read the HEAD of" in applied.stdout


# --- The AGENTS.md section (#1409) and the changelog (#1408) -----------------------------


def test_the_agents_section_reports_the_sentence_1401_added_then_matches(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream)
    section = _plan(kit, repo, env)["agents_section"]
    assert section["status"] == "differs" and section["file"] == "AGENTS.md"
    assert "To take a newer kit, follow the *Lite profile* section" in section["diff"]
    assert "Our deploy check" not in section["diff"]

    agents = repo / "AGENTS.md"
    adopt = (kit / "docs/agentic-dev-kit/workflows/adopt.md").read_text(encoding="utf-8")
    current = adopt.split("```markdown\n", 1)[1].split("```", 1)[0]
    # Rewrapped: the comparison is by bullet, so line breaks are not a difference.
    agents.write_text("# Agents\n\n" + current.replace("\n  ", " ") + "\n### session-start\n\n- Our deploy check.\n",
                      encoding="utf-8")
    assert _plan(kit, repo, env)["agents_section"] == {"status": "match", "file": "AGENTS.md", "diff": ""}
    agents.unlink()
    assert _plan(kit, repo, env)["agents_section"]["status"] == "missing"


def test_the_changelog_prints_the_fragments_written_after_the_baseline(
    tmp_path: Path, kit_upstream: dict
) -> None:
    env = _env(tmp_path)
    kit = tmp_path / "kit"
    # A `--depth 1` clone, as the kit block makes: the engine deepens it.
    _git(tmp_path, env, "clone", "-q", "--depth", "1", f"file://{kit_upstream['bare']}", str(kit))
    repo, env = _install(tmp_path, kit_upstream)
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"── {FRAGMENT} (" in done.stdout and FRAGMENT_TEXT.rstrip() in done.stdout
    assert _git(kit, env, "rev-parse", "--is-shallow-repository") == "false"
    changelog = _plan(kit, repo, env)["changelog"]
    assert changelog["bound"] == "baseline" and changelog["base"] == kit_upstream["old_commit"]
    assert [e["path"] for e in changelog["entries"]] == [FRAGMENT]


def test_the_changelog_of_a_baseline_with_no_provenance_starts_at_the_lite_profile(
    tmp_path: Path, kit_upstream: dict, kit: Path
) -> None:
    repo, env = _install(tmp_path, kit_upstream, record_commit=False)
    changelog = _plan(kit, repo, env)["changelog"]
    assert changelog["bound"] == "lite-profile" and changelog["base"] == kit_upstream["old_commit"]
    assert [e["path"] for e in changelog["entries"]] == [FRAGMENT]
    assert any("names no kit commit" in w for w in changelog["warnings"])


@pytest.mark.parametrize("version", ["1", "x"])
def test_a_config_schema_that_is_not_the_kits_stops(
    tmp_path: Path, kit_upstream: dict, kit: Path, version: str
) -> None:
    """No lite config migration is written: a `kit.version` behind the kit's, or one
    that is not a number, stops both modes."""
    repo, env = _install(tmp_path, kit_upstream)
    config = repo / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("version: 2", f"version: {version}"), encoding="utf-8")
    _git(repo, env, "commit", "-qam", "another schema")
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1 and "stop: config schema:" in done.stdout, done.stdout
    before = _snapshot(repo)
    applied = _apply(kit, repo, env)
    assert applied.returncode == 1 and "refused: config schema:" in applied.stdout, applied.stdout
    assert _snapshot(repo) == before


def test_an_unknown_state_stops_the_read_and_the_apply(tmp_path: Path, kit_upstream: dict, kit: Path) -> None:
    """A baseline that does not describe the tree (a lite file with no entry in it)
    stops: the states cannot be trusted."""
    repo, env = _install(tmp_path, kit_upstream)
    baseline = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    del baseline["not_installed"]
    (repo / "kit-manifest.json").write_text(json.dumps(baseline), encoding="utf-8")
    (repo / DOCS[0]).unlink()
    _git(repo, env, "commit", "-qam", "a baseline with no declared set, and a doc gone")
    done = _read(kit, repo, env, json_out=False)
    assert done.returncode == 1 and f"stop: {DOCS[0]} is missing" in done.stdout
    applied = _apply(kit, repo, env, "--take", DOCS[0])
    assert applied.returncode == 1 and f"refused: {DOCS[0]} is missing" in applied.stdout


# --- upgrade.md's lite section calls the engine ----------------------------------------

UPGRADE = REPO_ROOT / "docs/agentic-dev-kit/workflows/upgrade.md"


def _lite_section() -> str:
    text = UPGRADE.read_text(encoding="utf-8")
    return text[text.index("\n## Lite profile\n") :]


def test_the_lite_section_runs_the_engine_with_every_input_on_the_command() -> None:
    """No block carries a shell variable to a later one (#1410), and each command
    names the target on the call."""
    import re

    section = _lite_section()
    blocks = re.findall(r"^```bash\n(.*?)^```", section, re.MULTILINE | re.DOTALL)
    assert len(blocks) == 2, blocks
    for block in blocks:
        assert "$" not in block, block
        assert block.startswith("uv run <kit>/scripts/kit_doctor.py --upgrade-lite --root <root> --branch <branch>")
    assert "--apply --kit-commit <sha>" in blocks[1]
    assert "LITE_" not in section


def test_every_flag_the_lite_section_names_is_one_the_engine_takes(tmp_path: Path) -> None:
    import re

    flags = set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", _lite_section()))
    assert {"--upgrade-lite", "--apply", "--kit-commit", "--take", "--keep", "--leave-absent"} <= flags
    usage = _doctor(REPO_ROOT, _env(tmp_path), "--help").stdout
    for flag in flags - {"--depth"}:
        assert flag in usage, flag


@pytest.mark.parametrize(
    "phrase",
    [
        "record: recorded in the working tree",
        "apply (U4):",
        "nothing taken, nothing recorded",
        "not recorded",
        "recorded, install provenance unknown",
        "kept skills",
        "AGENTS.md section:",
        "baseline (committed):",
    ],
)
def test_each_output_the_lite_section_quotes_is_one_the_engine_prints(phrase: str) -> None:
    assert phrase in _lite_section()
    assert phrase in (REPO_ROOT / "scripts/kit_doctor.py").read_text(encoding="utf-8")
