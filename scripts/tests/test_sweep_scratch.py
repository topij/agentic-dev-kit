"""Tests for scripts/sweep_scratch.py — the scratch report and guarded removal (#900).

Every fixture lives under pytest's ``tmp_path``; nothing here points the engine at
a real scratch directory. The engine deletes files, so the refusals listed in
``test_each_refusal_is_what_keeps_its_fixture`` each have a fixture that survives
``--apply`` and a twin that neutralises the guard and asserts the same fixture is
then removed — proof the first test discriminates. The mount-point refusals are
not pinned here: building a mount needs privileges a test run does not have.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest
from conftest import REPO_ROOT, require_kit_source

ENGINE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ENGINE_DIR / "sweep_scratch.py"

DAY = 86400
OLD = 30 * DAY
GRACE = 3600


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sweep_scratch_under_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


sweep = _load()


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _set_age(path: Path, seconds: int) -> None:
    """Backdate ``path`` and everything under it, bottom-up, never following a symlink."""
    stamp = time.time() - seconds
    lutime = os.utime in os.supports_follow_symlinks
    targets: list[str] = []
    if path.is_dir() and not path.is_symlink():
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            targets.extend(os.path.join(dirpath, n) for n in filenames + dirnames)
    targets.append(str(path))
    for target in targets:
        if os.path.islink(target):
            if lutime:
                os.utime(target, (stamp, stamp), follow_symlinks=False)
        else:
            os.utime(target, (stamp, stamp))


def _tree(path: Path, *, age: int = OLD) -> Path:
    (path / "sub").mkdir(parents=True)
    (path / "sub" / "file.txt").write_text("scratch\n", encoding="utf-8")
    _set_age(path, age)
    return path


@pytest.fixture
def base(tmp_path: Path) -> Path:
    # Resolved: the engine refuses a root with a symlink in its path, and macOS
    # temp dirs sit under /var -> /private/var.
    return Path(os.path.realpath(tmp_path))


@pytest.fixture
def repo(base: Path) -> Path:
    path = base / "repo"
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    _git(path, "commit", "-q", "--allow-empty", "-m", "seed")
    return path


@pytest.fixture
def root(base: Path) -> Path:
    path = base / "scratch"
    path.mkdir()
    return path


def _settings(roots: list[Path | str], repo: Path, grace: int = GRACE):
    return sweep.Settings(roots=[str(r) for r in roots], grace_seconds=grace, repos=[repo])


def _run(roots, repo: Path, *, older_than: int | None, grace: int = GRACE):
    settings = _settings(roots, repo, grace)
    reports = sweep.survey(settings, root=repo, now=time.time())
    outcomes = None if older_than is None else sweep.apply(reports, settings, older_than=older_than)
    return reports, outcomes


def _owners(reports) -> dict[str, str]:
    return {os.path.basename(e.path): e.owner for r in reports for e in r.entries}


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #


def test_report_classifies_every_owner_and_changes_nothing(root: Path, repo: Path, base: Path):
    _tree(root / "old-session")
    _tree(root / "fresh-session", age=60)
    (root / "old-file.log").write_text("x\n", encoding="utf-8")
    _set_age(root / "old-file.log", OLD)
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "lane-wt"))
    _set_age(root / "lane-wt", OLD)
    outside = _tree(base / "outside")
    (root / "escape").symlink_to(outside)

    before = sorted(p.name for p in root.iterdir())
    reports, _ = _run([root], repo, older_than=None)

    assert _owners(reports) == {
        "old-session": sweep.STALE,
        "fresh-session": sweep.GRACE,
        "old-file.log": sweep.STALE,
        "lane-wt": sweep.LIVE,
        "escape": sweep.UNCLASSIFIED,
    }
    assert sorted(p.name for p in root.iterdir()) == before
    stale = next(e for e in reports[0].entries if e.path.endswith("old-session"))
    assert stale.size_bytes > 0
    assert stale.age_seconds is not None and stale.age_seconds >= OLD - 60


def test_absent_root_is_reported_not_refused(base: Path, repo: Path):
    reports, outcomes = _run([base / "never-made"], repo, older_than=0)
    assert reports[0].status == "absent"
    assert outcomes == []


# --------------------------------------------------------------------------- #
# apply
# --------------------------------------------------------------------------- #


def test_apply_removes_only_stale_entries(root: Path, repo: Path, base: Path):
    _tree(root / "old-session")
    (root / "old-file.log").write_text("x\n", encoding="utf-8")
    _set_age(root / "old-file.log", OLD)
    _tree(root / "fresh-session", age=60)
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "lane-wt"))
    _set_age(root / "lane-wt", OLD)

    _, outcomes = _run([root], repo, older_than=7 * DAY)

    assert sorted(p.name for p in root.iterdir()) == ["fresh-session", "lane-wt"]
    removed = sorted(os.path.basename(o.path) for o in outcomes if o.action == "removed")
    assert removed == ["old-file.log", "old-session"]
    assert root.is_dir()


def test_older_than_spares_a_stale_entry_younger_than_it(root: Path, repo: Path):
    _tree(root / "two-days", age=2 * DAY)
    reports, outcomes = _run([root], repo, older_than=7 * DAY)
    assert _owners(reports) == {"two-days": sweep.STALE}
    assert outcomes == []
    assert (root / "two-days").is_dir()


def test_grace_is_judged_by_the_newest_mtime_anywhere_inside(root: Path, repo: Path):
    entry = _tree(root / "deep")
    deep = entry / "sub" / "a" / "b"
    deep.mkdir(parents=True)
    (deep / "live.txt").write_text("being written\n", encoding="utf-8")
    # The top directory and its first level stay old; only the deep file is new.
    for p in (entry, entry / "sub"):
        os.utime(p, (time.time() - OLD, time.time() - OLD))

    reports, outcomes = _run([root], repo, older_than=0)

    assert _owners(reports) == {"deep": sweep.GRACE}
    assert outcomes == []
    assert (deep / "live.txt").is_file()


def test_registered_worktree_is_kept(root: Path, repo: Path):
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "lane-wt"))
    _set_age(root / "lane-wt", OLD)
    _, outcomes = _run([root], repo, older_than=0)
    assert outcomes == []
    assert (root / "lane-wt" / ".git").is_file()


def test_entry_holding_a_registered_worktree_is_kept(root: Path, repo: Path):
    (root / "session").mkdir()
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "session" / "deep" / "wt"))
    _set_age(root / "session", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"session": sweep.LIVE}
    assert outcomes == []


def test_symlink_entry_out_of_the_root_is_never_followed(root: Path, repo: Path, base: Path):
    outside = _tree(base / "outside")
    (root / "escape").symlink_to(outside)
    _set_age(root / "escape", OLD)

    reports, outcomes = _run([root], repo, older_than=0)

    assert _owners(reports) == {"escape": sweep.UNCLASSIFIED}
    assert outcomes == []
    assert (root / "escape").is_symlink()
    assert (outside / "sub" / "file.txt").is_file()


def test_symlink_inside_a_stale_entry_is_removed_without_following(
    root: Path, repo: Path, base: Path
):
    outside = _tree(base / "outside")
    entry = _tree(root / "old-session")
    (entry / "sub" / "link").symlink_to(outside)
    _set_age(entry, OLD)

    _, outcomes = _run([root], repo, older_than=0)

    assert [o.action for o in outcomes] == ["removed"]
    assert not entry.exists()
    assert (outside / "sub" / "file.txt").is_file()


@pytest.mark.parametrize(
    "make_root",
    [
        pytest.param(lambda base: "/", id="filesystem-root"),
        pytest.param(lambda base: "relative/scratch", id="relative"),
        pytest.param(lambda base: f"{base}/scratch/../scratch", id="dotdot"),
        pytest.param(lambda base: f"{base}/link-root", id="root-is-symlink"),
        pytest.param(lambda base: f"{base}/link-parent/scratch", id="symlink-in-path"),
        pytest.param(lambda base: f"{base}/scratch/file.txt", id="not-a-directory"),
        pytest.param(lambda base: f"{base}/scratch/{{nope}}", id="unknown-placeholder"),
    ],
)
def test_refused_root_is_never_swept(make_root, root: Path, repo: Path, base: Path):
    _tree(root / "old-session")
    (root / "file.txt").write_text("x\n", encoding="utf-8")
    (base / "link-root").symlink_to(root)
    (base / "link-parent").symlink_to(base)

    reports, outcomes = _run([make_root(base)], repo, older_than=0)

    assert reports[0].status == "refused"
    assert outcomes == []
    assert (root / "old-session" / "sub" / "file.txt").is_file()


def test_nested_root_is_never_removed_but_its_entries_are_swept(root: Path, repo: Path):
    inner = root / "inner-root"
    _tree(inner / "old-session")
    _set_age(inner, OLD)

    reports, outcomes = _run([root, inner], repo, older_than=0)

    assert reports[0].entries[0].owner == sweep.UNCLASSIFIED
    assert inner.is_dir()
    assert not (inner / "old-session").exists()
    assert [os.path.basename(o.path) for o in outcomes] == ["old-session"]


def test_unreadable_path_inside_an_entry_keeps_the_entry(root: Path, repo: Path):
    if os.geteuid() == 0:
        pytest.skip("root reads through a 000 directory")
    entry = _tree(root / "old-session")
    locked = entry / "locked"
    locked.mkdir()
    _set_age(entry, OLD)
    locked.chmod(0)
    try:
        reports, outcomes = _run([root], repo, older_than=0)
    finally:
        locked.chmod(0o700)
    assert _owners(reports) == {"old-session": sweep.UNCLASSIFIED}
    assert outcomes == []
    assert entry.is_dir()


def test_entry_changed_after_the_report_is_rechecked_before_removal(root: Path, repo: Path):
    entry = _tree(root / "old-session")
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    (entry / "sub" / "new.txt").write_text("written after the report\n", encoding="utf-8")

    outcomes = sweep.apply(reports, settings, older_than=0)

    assert [o.action for o in outcomes] == ["kept"]
    assert (entry / "sub" / "new.txt").is_file()


# --------------------------------------------------------------------------- #
# the removal primitive refuses on its own, whatever the report said
# --------------------------------------------------------------------------- #


def _identity(path: Path) -> tuple[int, int]:
    st = os.lstat(path)
    return (st.st_dev, st.st_ino)


def test_remove_entry_refuses_the_root_itself(root: Path):
    with pytest.raises(sweep.Refused):
        sweep.remove_entry(str(root), str(root), _identity(root))
    assert root.is_dir()


def test_remove_entry_refuses_a_symlink(root: Path, base: Path):
    outside = _tree(base / "outside")
    (root / "escape").symlink_to(outside)
    with pytest.raises(sweep.Refused):
        sweep.remove_entry(str(root / "escape"), str(root), _identity(root / "escape"))
    assert (outside / "sub" / "file.txt").is_file()


def test_remove_entry_refuses_a_path_outside_the_root(root: Path, base: Path):
    outside = _tree(base / "outside")
    with pytest.raises(sweep.Refused):
        sweep.remove_entry(str(outside), str(root), _identity(outside))
    assert outside.is_dir()


def test_remove_entry_refuses_a_grandchild(root: Path):
    entry = _tree(root / "old-session")
    with pytest.raises(sweep.Refused):
        sweep.remove_entry(str(entry / "sub"), str(root), _identity(entry / "sub"))
    assert (entry / "sub").is_dir()


def test_remove_entry_refuses_a_replaced_entry(root: Path):
    entry = _tree(root / "old-session")
    with pytest.raises(sweep.Refused):
        sweep.remove_entry(str(entry), str(root), (0, 0))
    assert entry.is_dir()


# --------------------------------------------------------------------------- #
# each sole guard discriminates: neutralised, the same fixture is removed
# --------------------------------------------------------------------------- #


def _root_inside_worktree(base: Path, repo: Path) -> tuple[list[Path], Path]:
    scratch = repo / "scratch"
    _tree(scratch / "entry")
    return [scratch], scratch / "entry"


def _linked_worktree_of_unconfigured_repo(base: Path, repo: Path) -> tuple[list[Path], Path]:
    other = base / "other-repo"
    other.mkdir()
    _git(other, "init", "-q")
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    _git(other, "commit", "-q", "--allow-empty", "-m", "seed")
    scratch = base / "scratch"
    scratch.mkdir()
    _git(other, "worktree", "add", "-q", "--detach", str(scratch / "entry"))
    _set_age(scratch / "entry", OLD)
    return [scratch], scratch / "entry"


def _main_repo_with_outside_worktree(base: Path, repo: Path) -> tuple[list[Path], Path]:
    scratch = base / "scratch"
    clone = scratch / "entry" / "clone"
    clone.mkdir(parents=True)
    _git(clone, "init", "-q")
    _git(clone, "config", "user.email", "test@example.com")
    _git(clone, "config", "user.name", "Test")
    _git(clone, "commit", "-q", "--allow-empty", "-m", "seed")
    _git(clone, "worktree", "add", "-q", "--detach", str(base / "outside-wt"))
    _set_age(scratch / "entry", OLD)
    return [scratch], scratch / "entry"


def _fresh_entry(base: Path, repo: Path) -> tuple[list[Path], Path]:
    scratch = base / "scratch"
    _tree(scratch / "entry", age=60)
    return [scratch], scratch / "entry"


def _entry_is_another_root(base: Path, repo: Path) -> tuple[list[Path], Path]:
    scratch = base / "scratch"
    inner = scratch / "entry"
    inner.mkdir(parents=True)
    _set_age(inner, OLD)
    return [scratch, inner], inner


@pytest.mark.parametrize(
    "build, guard",
    [
        pytest.param(_root_inside_worktree, "live_worktree_reason", id="registered-worktree"),
        pytest.param(
            _linked_worktree_of_unconfigured_repo, "_linked_gitdir_reason", id="linked-worktree"
        ),
        pytest.param(
            _main_repo_with_outside_worktree, "_main_repo_reason", id="outside-worktree"
        ),
        pytest.param(_fresh_entry, "grace_reason", id="grace-window"),
        pytest.param(_entry_is_another_root, "configured_root_reason", id="configured-root"),
    ],
)
@pytest.mark.parametrize("neutralised", [False, True])
def test_each_refusal_is_what_keeps_its_fixture(
    build, guard: str, neutralised: bool, base: Path, repo: Path, monkeypatch
):
    roots, entry = build(base, repo)
    if neutralised:
        monkeypatch.setattr(sweep, guard, lambda *a, **k: None)

    _run(roots, repo, older_than=0)

    assert entry.exists() is not neutralised


def test_unparseable_git_file_keeps_the_entry(root: Path, repo: Path):
    entry = root / "entry"
    entry.mkdir()
    (entry / ".git").write_text("garbage\n", encoding="utf-8")
    _set_age(entry, OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert "unparseable .git file" in reports[0].entries[0].reason
    assert outcomes == []
    assert entry.is_dir()


def test_worktree_registered_after_the_report_is_rechecked_before_removal(
    root: Path, repo: Path, monkeypatch
):
    entry = _tree(root / "entry")
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.STALE}
    monkeypatch.setattr(sweep, "registered_worktrees", lambda repos: [str(entry)])
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [(o.action, o.reason.startswith("now live-worktree")) for o in outcomes] == [("kept", True)]
    assert entry.is_dir()


def test_cli_failed_removal_exits_one(root: Path, repo: Path, base: Path, monkeypatch, capsys):
    _tree(root / "old-session")
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(repo)])

    def fail(entry: str, root_path: str, identity) -> None:
        raise OSError(13, "Permission denied", entry)

    monkeypatch.setattr(sweep, "remove_entry", fail)
    assert sweep.main(["--config", str(cfg), "--apply", "--older-than", "1d"]) == 1
    assert "failed" in capsys.readouterr().out


def test_empty_worktree_repos_is_a_config_error(root: Path, base: Path, capsys):
    cfg = base / "dev-model.yaml"
    cfg.write_text(
        f'scratch:\n  roots:\n    - "{root}"\n  grace_window: 1h\n  worktree_repos: []\n',
        encoding="utf-8",
    )
    assert sweep.main(["--config", str(cfg)]) == 2
    assert "worktree_repos is empty" in capsys.readouterr().err


def test_grace_reason_never_prints_a_negative_age():
    assert "-" not in sweep.grace_reason(-5000.0, 3600)


# --------------------------------------------------------------------------- #
# CLI and config
# --------------------------------------------------------------------------- #


def _config(
    path: Path, *, roots: list[str], repos: list[str], grace: str = "1h", omit: str = ""
) -> Path:
    lines = ["scratch:"]
    if omit != "roots":
        lines += ["  roots:", *[f'    - "{r}"' for r in roots]]
    if omit != "grace_window":
        lines += [f"  grace_window: {grace}"]
    if omit != "worktree_repos":
        lines += ["  worktree_repos:", *[f'    - "{r}"' for r in repos]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_cli_report_then_apply(root: Path, repo: Path, base: Path, capsys):
    _tree(root / "old-session")
    _tree(root / "fresh-session", age=60)
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(repo)])

    assert sweep.main(["--config", str(cfg), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    owners = {os.path.basename(e["path"]): e["owner"] for e in payload["roots"][0]["entries"]}
    assert owners == {"old-session": "stale", "fresh-session": "in-grace"}
    assert "outcomes" not in payload
    assert (root / "old-session").is_dir()

    assert sweep.main(["--config", str(cfg), "--apply", "--older-than", "7d"]) == 0
    out = capsys.readouterr().out
    assert f"removed {root / 'old-session'}" in out
    assert sorted(p.name for p in root.iterdir()) == ["fresh-session"]


def test_cli_refused_root_exits_one(base: Path, repo: Path, capsys):
    cfg = _config(base / "dev-model.yaml", roots=["/"], repos=[str(repo)])
    assert sweep.main(["--config", str(cfg), "--apply", "--older-than", "1d"]) == 1
    assert "the filesystem root" in capsys.readouterr().out


def test_cli_unreadable_worktree_registrations_refuse_everything(root: Path, base: Path, capsys):
    _tree(root / "old-session")
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(base / "not-a-repo")])
    (base / "not-a-repo").mkdir()
    assert sweep.main(["--config", str(cfg), "--apply", "--older-than", "1d"]) == 2
    assert "git worktree list failed" in capsys.readouterr().err
    assert (root / "old-session").is_dir()


@pytest.mark.parametrize(
    "argv",
    [["--apply"], ["--older-than", "7d"], ["--apply", "--older-than", "7"]],
    ids=["apply-without-age", "age-without-apply", "unitless-age"],
)
def test_cli_usage_errors_exit_two(argv: list[str], root: Path, repo: Path, base: Path):
    _tree(root / "old-session")
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(repo)])
    try:
        code = sweep.main(["--config", str(cfg), *argv])
    except SystemExit as exc:
        code = exc.code
    assert code == 2
    assert (root / "old-session").is_dir()


@pytest.mark.parametrize("missing", ["roots", "grace_window", "worktree_repos"])
def test_missing_config_key_exits_two(missing: str, root: Path, repo: Path, base: Path, capsys):
    _tree(root / "old-session")
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(repo)], omit=missing)
    assert sweep.main(["--config", str(cfg), "--apply", "--older-than", "1d"]) == 2
    assert f"scratch.{missing}" in capsys.readouterr().err
    assert (root / "old-session").is_dir()


def test_placeholders_expand_to_uid_and_repo_slug(base: Path):
    expanded = sweep.expand_root("/private/tmp/claude-{uid}/{repo_slug}", root=Path("/a/b.c"))
    assert expanded == f"/private/tmp/claude-{os.getuid()}/-a-b-c"


def test_shipped_config_declares_the_scratch_block():
    require_kit_source()
    settings = sweep.load_settings(REPO_ROOT / "config" / "dev-model.yaml")
    assert settings.roots, "scratch.roots is empty"
    assert settings.grace_seconds > 0
    assert settings.repos
