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


@pytest.fixture(autouse=True)
def _mtime_only(request, monkeypatch):
    """Fixtures backdate with ``os.utime``, which sets every ctime to now, so the
    engine's ``max(mtime, ctime)`` would read every fixture as fresh. Age is judged
    by mtime alone here; a test whose name holds ``ctime`` keeps the real stamp."""
    if "ctime" not in request.node.name:
        monkeypatch.setattr(sweep, "_stamp", lambda st: st.st_mtime)


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
    # The fake registration is not a repository, so its git dir cannot be read.
    monkeypatch.setattr(sweep, "repository_stores", lambda *a, **k: [])
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [(o.action, o.reason.startswith("now live-worktree")) for o in outcomes] == [("kept", True)]
    assert entry.is_dir()


def test_git_file_naming_an_impossible_path_keeps_the_entry_and_the_sweep_runs(root: Path, repo: Path):
    poisoned = root / "poisoned"
    poisoned.mkdir()
    (poisoned / ".git").write_bytes(b"gitdir: /tmp/a\x00b\n")
    _set_age(poisoned, OLD)
    stale = _tree(root / "stale")
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"poisoned": sweep.LIVE, "stale": sweep.STALE}
    assert [(os.path.basename(o.path), o.action) for o in outcomes] == [("stale", "removed")]
    assert poisoned.is_dir() and not stale.exists()


def test_fifo_worktree_record_keeps_the_entry_without_blocking(root: Path, repo: Path, base: Path):
    records = root / "fifo" / ".git" / "worktrees" / "x"
    records.mkdir(parents=True)
    os.mkfifo(records / "gitdir")
    _set_age(root / "fifo", OLD)
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=[str(repo)])
    # In a child with a deadline: opening the FIFO would block forever, and a hung
    # test is a worse signal than a failed one.
    done = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--config", str(cfg), "--json"],
        capture_output=True, text=True, timeout=60, cwd=REPO_ROOT,
    )
    assert done.returncode == 0, done.stderr
    owners = {os.path.basename(e["path"]): e["owner"] for e in json.loads(done.stdout)["roots"][0]["entries"]}
    assert owners == {"fifo": sweep.LIVE}


def test_bare_repository_with_an_outside_worktree_is_kept(root: Path, repo: Path, base: Path):
    bare = root / "barerepo.git"
    _git(base, "clone", "-q", "--bare", str(repo), str(bare))
    _git(bare, "worktree", "add", "-q", "--detach", str(base / "outside-wt"))
    _set_age(bare, OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"barerepo.git": sweep.LIVE}
    assert outcomes == []
    assert bare.is_dir()


def test_registration_of_a_worktree_path_holding_a_newline_is_read_whole(root: Path, repo: Path):
    odd = root / "we ird\nnl"
    _git(repo, "worktree", "add", "-q", "--detach", str(odd))
    assert str(odd) in sweep.registered_worktrees([repo])


def test_linked_worktree_whose_git_dir_cannot_be_statted_is_kept(base: Path, repo: Path):
    roots, entry = _linked_worktree_of_unconfigured_repo(base, repo)
    other = base / "other-repo"
    other.chmod(0)
    try:
        reports, outcomes = _run(roots, repo, older_than=0)
    finally:
        other.chmod(0o755)
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert "cannot stat" in reports[0].entries[0].reason
    assert outcomes == []
    assert entry.is_dir()


def test_failed_worktree_reread_during_apply_keeps_the_entry(root: Path, repo: Path, monkeypatch):
    entry = _tree(root / "entry")
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.STALE}

    def fail(repos):
        raise sweep.ConfigError("git worktree list failed")

    monkeypatch.setattr(sweep, "registered_worktrees", fail)
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [o.action for o in outcomes] == ["kept"]
    assert entry.is_dir()


def test_entry_touched_after_the_report_is_rechecked_against_older_than(root: Path, repo: Path):
    entry = _tree(root / "entry", age=30 * DAY)
    settings = _settings([root], repo, grace=60)
    reports = sweep.survey(settings, root=repo, now=time.time())
    _set_age(entry, 2 * DAY)  # still past the grace window, now younger than --older-than
    outcomes = sweep.apply(reports, settings, older_than=7 * DAY)
    assert [o.action for o in outcomes] == ["kept"]
    assert entry.is_dir()


def test_relative_worktree_repo_resolves_against_the_repo_root(base: Path, repo: Path, root: Path):
    cfg = _config(base / "dev-model.yaml", roots=[str(root)], repos=["."])
    assert sweep.load_settings(cfg, root=repo).repos == [repo]


def test_a_refused_root_is_still_protected_as_an_entry_of_another(root: Path, repo: Path):
    inner = root / "file.txt"
    inner.write_text("x\n", encoding="utf-8")
    _set_age(inner, OLD)
    reports, outcomes = _run([root, inner], repo, older_than=0)
    assert [r.status for r in reports] == ["ok", "refused"]
    assert _owners(reports) == {"file.txt": sweep.UNCLASSIFIED}
    assert outcomes == []
    assert inner.exists()


def test_an_entry_holding_a_deeper_configured_root_is_kept(root: Path, repo: Path):
    deeper = root / "a" / "b"
    deeper.mkdir(parents=True)
    _set_age(root / "a", OLD)
    reports, outcomes = _run([root, deeper], repo, older_than=0)
    first = next(r for r in reports if r.root == str(root))
    assert {os.path.basename(e.path): e.owner for e in first.entries} == {"a": sweep.UNCLASSIFIED}
    assert deeper.is_dir()


def test_entry_replaced_after_the_report_is_kept(root: Path, repo: Path):
    entry = _tree(root / "entry")
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.STALE}
    holder = root.parent / "holder"
    entry.rename(holder)  # keeps the old inode alive, so the new one cannot reuse it
    _tree(root / "entry")
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [(o.action, o.reason) for o in outcomes] == [("kept", "replaced since it was classified")]
    assert (root / "entry").is_dir()


@pytest.mark.parametrize("raw", ["/tmp/{uid.real}", "/tmp/{repo_slug!r}", "/tmp/{uid:>9}", "/tmp/{home}"])
def test_placeholders_other_than_the_two_plain_ones_are_refused(raw: str, base: Path):
    with pytest.raises(ValueError):
        sweep.expand_root(raw, root=base)


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


# --------------------------------------------------------------------------- #
# roots over a home or a worktree repo; inherited GIT_* variables
# --------------------------------------------------------------------------- #


def _home_under_root(base: Path, repo: Path, monkeypatch, source: str) -> Path:
    parent = base / "parent"
    home = parent / "home"
    home.mkdir(parents=True)
    if source == "env":
        monkeypatch.setenv("HOME", str(home))
    else:
        monkeypatch.delenv("HOME", raising=False)
        monkeypatch.setattr(
            sweep.pwd, "getpwuid", lambda uid: type("pw", (), {"pw_dir": str(home)})()
        )
    return parent


@pytest.mark.parametrize("neutralised", [False, True], ids=["guarded", "neutralised"])
@pytest.mark.parametrize(
    "make_root",
    [
        pytest.param(lambda base, repo, mp: _home_under_root(base, repo, mp, "env"), id="holds-HOME"),
        pytest.param(lambda base, repo, mp: _home_under_root(base, repo, mp, "pwd"), id="holds-pw-home"),
        pytest.param(lambda base, repo, mp: base, id="holds-worktree-repo"),
    ],
)
def test_root_holding_a_home_or_worktree_repo_is_refused(
    make_root, neutralised: bool, base: Path, repo: Path, monkeypatch
):
    parent = make_root(base, repo, monkeypatch)
    sibling = _tree(parent / "sibling-repo")
    if neutralised:
        monkeypatch.setattr(sweep, "guarded_paths", lambda repos: [])

    reports, _ = _run([parent], repo, older_than=0)

    assert (reports[0].status == "refused") is not neutralised
    assert sibling.exists() is not neutralised


def test_root_equal_to_the_worktree_repo_is_refused(repo: Path):
    reports, outcomes = _run([repo], repo, older_than=0)
    assert reports[0].status == "refused"
    assert "worktree repository" in reports[0].reason
    assert outcomes == []


def test_registrations_ignore_an_inherited_git_dir(base: Path, repo: Path, monkeypatch):
    other = base / "other"
    other.mkdir()
    _git(other, "init", "-q")
    _git(other, "-c", "user.email=t@e", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "s")
    _git(other, "worktree", "add", "-q", str(base / "other-wt"))
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))

    found = sweep.registered_worktrees([repo])

    assert found == [str(repo)]


# --------------------------------------------------------------------------- #
# git dirs a repository outside the entry may depend on
# --------------------------------------------------------------------------- #


def _seeded(path: Path, *extra: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", *extra)
    _git(path, "-c", "user.email=t@e", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "s")
    return path


def test_separate_git_dir_target_inside_an_entry_is_kept(root: Path, repo: Path, base: Path):
    (root / "entry").mkdir()
    _seeded(base / "outside-main", f"--separate-git-dir={root / 'entry' / 'gd'}")
    _set_age(root / "entry", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert "--separate-git-dir" in reports[0].entries[0].reason
    assert outcomes == []
    assert (root / "entry" / "gd" / "HEAD").is_file()


def test_entry_that_is_a_bare_repository_is_kept(root: Path, repo: Path, base: Path):
    _git(base, "clone", "-q", "--bare", str(repo), str(root / "bare.git"))
    _set_age(root / "bare.git", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"bare.git": sweep.LIVE}
    assert outcomes == []


def test_ordinary_clone_with_submodule_git_dirs_is_still_removed(root: Path, repo: Path, base: Path):
    clone = root / "entry" / "clone"
    _git(base, "clone", "-q", str(repo), str(clone))
    sub = clone / ".git" / "modules" / "sub"
    (sub / "objects").mkdir(parents=True)
    (sub / "refs").mkdir()
    (sub / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    _set_age(root / "entry", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"entry": sweep.STALE}
    assert [o.action for o in outcomes] == ["removed"]


def test_configured_repo_borrowing_objects_from_an_entry_keeps_it(root: Path, repo: Path, base: Path):
    src = _seeded(root / "entry" / "src")
    (repo / ".git" / "objects" / "info" / "alternates").write_text(
        f"{src / '.git' / 'objects'}\n", encoding="utf-8"
    )
    _set_age(root / "entry", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert "object store" in reports[0].entries[0].reason
    assert outcomes == []
    assert src.is_dir()


def test_alternates_are_followed_through_a_chain_and_relative_paths(root: Path, repo: Path, base: Path):
    middle = _seeded(base / "middle")
    src = _seeded(root / "entry" / "src")
    (repo / ".git" / "objects" / "info" / "alternates").write_text(
        f"# a comment\n\n{middle / '.git' / 'objects'}\n", encoding="utf-8"
    )
    relative = os.path.relpath(src / ".git" / "objects", middle / ".git" / "objects")
    (middle / ".git" / "objects" / "info" / "alternates").write_text(f"{relative}\n", encoding="utf-8")
    _set_age(root / "entry", OLD)
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert outcomes == []


def test_configured_repo_whose_git_dir_sits_in_an_entry_keeps_it(root: Path, repo: Path, base: Path):
    # Named `.git`, so only the configured repository's own git dir protects it.
    gitdir = root / "entry" / "x" / ".git"
    gitdir.parent.mkdir(parents=True)
    other = _seeded(base / "other-main", f"--separate-git-dir={gitdir}")
    _set_age(root / "entry", OLD)
    settings = sweep.Settings(roots=[str(root)], grace_seconds=GRACE, repos=[repo, other])
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.LIVE}
    assert sweep.apply(reports, settings, older_than=0) == []
    assert (gitdir / "HEAD").is_file()


def test_quoted_alternates_path_refuses_the_survey(root: Path, repo: Path):
    (repo / ".git" / "objects" / "info" / "alternates").write_text('"/q\\tuoted"\n', encoding="utf-8")
    with pytest.raises(sweep.ConfigError, match="quoted"):
        _run([root], repo, older_than=None)


def test_failed_store_reread_during_apply_keeps_the_entry(root: Path, repo: Path, monkeypatch):
    entry = _tree(root / "entry")
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.STALE}

    def fail(worktrees):
        raise sweep.ConfigError("boom")

    monkeypatch.setattr(sweep, "repository_stores", fail)
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [(o.action, o.reason) for o in outcomes] == [("kept", "boom")]
    assert entry.is_dir()


def test_store_read_names_a_configured_repos_separated_git_dir(base: Path):
    gitdir = base / "elsewhere" / "gd"
    gitdir.parent.mkdir()
    other = _seeded(base / "other-main", f"--separate-git-dir={gitdir}")
    assert str(gitdir) in sweep.repository_stores([str(other)])



def test_objects_borrowed_after_the_report_are_rechecked_before_removal(root: Path, repo: Path):
    src = _seeded(root / "entry" / "src")
    _set_age(root / "entry", OLD)
    settings = _settings([root], repo)
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"entry": sweep.STALE}
    (repo / ".git" / "objects" / "info" / "alternates").write_text(
        f"{src / '.git' / 'objects'}\n", encoding="utf-8"
    )
    outcomes = sweep.apply(reports, settings, older_than=0)
    assert [(o.action, o.reason.startswith("now live-worktree")) for o in outcomes] == [("kept", True)]
    assert src.is_dir()


def test_a_prunable_worktree_registration_does_not_wedge_the_sweep(root: Path, repo: Path):
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "lens1"))
    (root / "lens1" / ".git").unlink()
    (root / "lens1").rmdir()  # deleted without `git worktree prune`
    junk = _tree(root / "junk")
    reports, outcomes = _run([root], repo, older_than=0)
    assert _owners(reports) == {"junk": sweep.STALE}
    assert [o.action for o in outcomes] == ["removed"]
    assert not junk.exists()


def test_the_kept_reason_names_the_git_dir_that_kept_it(root: Path, repo: Path, base: Path):
    _git(base, "clone", "-q", "--bare", str(repo), str(root / "entry" / "fixture" / "origin.git"))
    _set_age(root / "entry", OLD)
    reports, _ = _run([root], repo, older_than=None)
    assert str(root / "entry" / "fixture" / "origin.git") in reports[0].entries[0].reason


def test_an_extracted_copy_with_old_mtimes_is_judged_by_its_ctime(root: Path, repo: Path, base: Path):
    src = _tree(base / "src")
    subprocess.run(["cp", "-Rp", str(src), str(root / "copy")], check=True)
    assert (root / "copy" / "sub" / "file.txt").stat().st_mtime < time.time() - OLD + DAY
    reports, outcomes = _run([root], repo, older_than=7 * DAY)
    assert _owners(reports) == {"copy": sweep.GRACE}
    assert outcomes == []
    assert (root / "copy").is_dir()


def test_a_worktree_registration_whose_git_file_is_gone_refuses_the_survey(root: Path, repo: Path):
    _git(repo, "worktree", "add", "-q", "--detach", str(root / "lens1"))
    (root / "lens1" / ".git").unlink()  # the directory stays; git calls it prunable
    _tree(root / "junk")
    with pytest.raises(sweep.ConfigError, match="git worktree prune"):
        _run([root], repo, older_than=0)


def test_a_bare_configured_repos_borrowed_object_store_is_kept(root: Path, repo: Path, base: Path):
    bare = base / "configured.git"
    _git(base, "clone", "-q", "--bare", str(repo), str(bare))
    store = _seeded(root / "objstore") / ".git" / "objects"
    (bare / "objects" / "info" / "alternates").write_text(f"{store}\n", encoding="utf-8")
    _set_age(root / "objstore", OLD)
    settings = sweep.Settings(roots=[str(root)], grace_seconds=GRACE, repos=[repo, bare])
    reports = sweep.survey(settings, root=repo, now=time.time())
    assert _owners(reports) == {"objstore": sweep.LIVE}
    assert sweep.apply(reports, settings, older_than=0) == []
    assert store.is_dir()


def test_a_file_entry_restored_with_an_old_mtime_is_judged_by_its_ctime(root: Path, repo: Path, base: Path):
    old = base / "old.txt"
    old.write_text("x\n", encoding="utf-8")
    _set_age(old, OLD)
    subprocess.run(["cp", "-p", str(old), str(root / "restored.txt")], check=True)
    reports, outcomes = _run([root], repo, older_than=7 * DAY)
    assert _owners(reports) == {"restored.txt": sweep.GRACE}
    assert outcomes == []


def test_a_copy_into_an_existing_subdirectory_is_judged_by_its_ctime(root: Path, repo: Path, base: Path):
    # The entry's own timestamps are older than the grace window; only the
    # copied children's ctimes are fresh.
    deep = root / "entry" / "deep"
    deep.mkdir(parents=True)
    time.sleep(2.5)
    src = _tree(base / "src")
    subprocess.run(["cp", "-Rp", str(src), str(deep / "copy")], check=True)
    stamp = time.time() - OLD
    os.utime(deep, (stamp, stamp))
    reports, outcomes = _run([root], repo, older_than=0, grace=2)
    assert _owners(reports) == {"entry": sweep.GRACE}
    assert outcomes == []


def test_a_moved_worktree_git_dir_names_git_worktree_repair(root: Path, repo: Path, base: Path, monkeypatch):
    wt = base / "wt"
    _git(repo, "worktree", "add", "-q", "--detach", str(wt))
    (wt / ".git").write_text("gitdir: /nonexistent/elsewhere\n", encoding="utf-8")
    with pytest.raises(sweep.ConfigError, match="git worktree repair"):
        sweep.repository_stores([str(wt)])


# --------------------------------------------------------------------------- #
# containment by filesystem identity, not by path string (#1000)
# --------------------------------------------------------------------------- #


def _string_only_holds(outer: str, inner: str) -> bool:
    return outer == inner or inner.startswith(outer + os.sep)


def _require_case_insensitive(base: Path) -> None:
    (base / "CaseProbe").mkdir()
    if not (base / "caseprobe").exists():
        pytest.skip("the filesystem under tmp_path is case-sensitive; no case-variant spelling exists")


@pytest.mark.parametrize("neutralised", [False, True], ids=["identity", "string-only"])
def test_case_variant_root_holding_a_worktree_repo_is_refused(
    neutralised: bool, base: Path, monkeypatch
):
    _require_case_insensitive(base)
    repo = _seeded(base / "Box" / "Repo")
    _set_age(base / "Box", OLD)
    if neutralised:
        monkeypatch.setattr(sweep, "_holds", _string_only_holds)
    settings = sweep.Settings(roots=[str(base / "box")], grace_seconds=0, repos=[repo])

    reports = sweep.survey(settings, root=repo, now=time.time())
    sweep.apply(reports, settings, older_than=0)

    assert (reports[0].status == "refused") is not neutralised
    assert (repo / ".git").is_dir() is not neutralised


@pytest.mark.parametrize("reason", ["live_worktree_reason", "repository_store_reason"])
def test_case_variant_entry_overlapping_a_registration_is_kept(reason: str, base: Path):
    _require_case_insensitive(base)
    (base / "Box" / "wt" / "deep").mkdir(parents=True)
    held = [str(base / "Box" / "wt")]
    check = getattr(sweep, reason)
    assert check(str(base / "box" / "wt"), held) is not None  # the same directory
    assert check(str(base / "box"), held) is not None  # the entry holds it
    assert check(str(base / "box" / "wt" / "deep"), held) is not None  # it holds the entry


def _aliased(base: Path) -> tuple[Path, Path]:
    """A real directory and a symlink spelling of it: two strings, one inode, on any
    filesystem. Guarded paths and registrations are realpaths, so the engine never
    meets this spelling itself; it stands in for a case variant on Linux CI."""
    real = base / "real"
    (real / "inner" / "deep").mkdir(parents=True)
    (base / "alias").symlink_to(real)
    return real, base / "alias"


def test_root_holding_an_aliased_guarded_path_is_refused(base: Path):
    real, alias = _aliased(base)
    assert sweep.validate_root(str(real), [str(alias / "inner")])[0] == "refused"
    assert sweep.validate_root(str(real), [str(alias)])[0] == "refused"
    assert sweep.validate_root(str(real / "inner" / "deep"), [str(alias / "inner")]) == ("ok", None)


@pytest.mark.parametrize("reason", ["live_worktree_reason", "repository_store_reason"])
def test_entry_overlapping_an_aliased_registration_is_kept(reason: str, base: Path):
    real, alias = _aliased(base)
    check = getattr(sweep, reason)
    assert check(str(real / "inner"), [str(alias / "inner")]) is not None
    assert check(str(real), [str(alias / "inner")]) is not None
    assert check(str(real / "inner" / "deep"), [str(alias / "inner")]) is not None
    (base / "elsewhere").mkdir()
    assert check(str(real / "inner"), [str(base / "elsewhere")]) is None


def test_entry_that_is_an_aliased_configured_root_is_kept(base: Path):
    real, alias = _aliased(base)
    assert sweep.configured_root_reason(str(real / "inner"), [str(alias / "inner")]) is not None
    assert sweep.configured_root_reason(str(real), [str(alias / "inner" / "deep")]) is not None
    # One direction only: an entry inside another root is not kept for it.
    assert sweep.configured_root_reason(str(real / "inner" / "deep"), [str(alias / "inner")]) is None


def test_identity_compares_the_device_as_well_as_the_inode(base: Path, monkeypatch):
    """Two paths sharing an inode number on different devices are different paths."""
    outer, inner = base / "outer", base / "inner"
    outer.mkdir()
    inner.mkdir()
    real_stat = os.stat
    outer_st = real_stat(outer)

    def stat(path, *args, **kwargs):
        st = real_stat(path, *args, **kwargs)
        if os.fspath(path) == str(inner):
            fields = list(st)
            fields[1], fields[2] = outer_st.st_ino, outer_st.st_dev + 1
            return os.stat_result(fields)
        return st

    monkeypatch.setattr(sweep.os, "stat", stat)
    assert sweep._holds(str(outer), str(inner)) is False


def test_a_missing_guarded_path_does_not_refuse_the_root(root: Path, base: Path):
    assert sweep.validate_root(str(root), [str(base / "gone" / "home")]) == ("ok", None)


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(lambda path, held: sweep.validate_root(path, held)[0] == "refused", id="validate_root"),
        pytest.param(lambda path, held: sweep.live_worktree_reason(path, held) is not None, id="live_worktree_reason"),
        pytest.param(
            lambda path, held: sweep.repository_store_reason(path, held) is not None, id="repository_store_reason"
        ),
        pytest.param(
            lambda path, held: sweep.configured_root_reason(path, held) is not None, id="configured_root_reason"
        ),
    ],
)
def test_a_path_under_a_regular_file_fails_closed(check, root: Path, base: Path):
    """``NotADirectoryError`` is not "missing": a guarded path or store under a file
    (a bad ``alternates`` line, say) is unknown, so the root is refused or the entry kept."""
    blocker = base / "blocker"
    blocker.write_text("")
    assert check(str(root), [str(blocker / "repo")])


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(lambda path, held: sweep.validate_root(path, held)[0] == "refused", id="validate_root"),
        pytest.param(lambda path, held: sweep.live_worktree_reason(path, held) is not None, id="live_worktree_reason"),
        pytest.param(
            lambda path, held: sweep.repository_store_reason(path, held) is not None, id="repository_store_reason"
        ),
        pytest.param(
            lambda path, held: sweep.configured_root_reason(path, held) is not None, id="configured_root_reason"
        ),
    ],
)
def test_a_path_that_cannot_be_statted_fails_closed(check, root: Path, base: Path):
    if os.geteuid() == 0:
        pytest.skip("root stats through a 000 directory")
    locked = base / "locked"
    (locked / "repo").mkdir(parents=True)
    locked.chmod(0)
    try:
        assert check(str(root), [str(locked / "repo")])
    finally:
        locked.chmod(0o700)
