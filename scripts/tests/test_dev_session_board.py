"""dev_session.sh: where the sessions container resolves, and the board's RUN and
OVERLAP columns.

The sessions container must resolve to the same directory from the primary
checkout, a linked cockpit worktree and a lane worktree (#479). The board reads
each lane's headless-wrapper evidence for RUN and its changed files for OVERLAP;
both are read-only displays.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@dataclass
class Repo:
    root: Path
    sessions: Path
    env: dict[str, str]

    def engine(self, checkout: Path) -> Path:
        return checkout / "scripts" / "devkit" / "dev_session.sh"

    def run(self, checkout: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.engine(checkout)), *args],
            cwd=checkout,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
        )


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q", "-b", "trunk")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "shared.txt").write_text("seed\n", encoding="utf-8")
    (root / "other.txt").write_text("seed\n", encoding="utf-8")
    (root / ".gitignore").write_text("state/\n.devkit_state_root\n", encoding="utf-8")
    engine = root / "scripts" / "devkit"
    (engine / "lib").mkdir(parents=True)
    shutil.copy2(ENGINE_DIR / "dev_session.sh", engine / "dev_session.sh")
    shutil.copy2(ENGINE_DIR / "lib" / "repo_root.sh", engine / "lib" / "repo_root.sh")
    (root / "config").mkdir()
    (root / "config" / "dev-model.yaml").write_text(
        "paths:\n"
        "  handoff: handoff.md\n"
        "  friction_log: friction-log.md\n"
        "vcs:\n"
        "  protected_branch: trunk\n"
        "  dev_branch_prefix: lane\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "-u", "origin", "trunk")
    # A `gh` that always fails keeps the board offline: PR and CI read `—`.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_gh.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DEVKIT_", "GIT_"))}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return Repo(root=root, sessions=tmp_path / "dev-model-sessions", env=env)


def _new(repo: Repo, scope: str) -> Path:
    created = repo.run(repo.root, "new", scope)
    assert created.returncode == 0, created.stderr
    worktree = repo.sessions / scope / "wt"
    assert worktree.is_dir()
    return worktree


def _board(repo: Repo, checkout: Path | None = None) -> dict[str, list[str]]:
    listed = repo.run(checkout or repo.root, "list")
    assert listed.returncode == 0, listed.stderr
    lines = listed.stdout.splitlines()
    assert lines[0].split() == [
        "SCOPE", "BRANCH", "PR", "CI", "DIRTY", "RUN", "OVERLAP", "SANDBOX"
    ]
    return {line.split()[0]: line.split() for line in lines[2:]}


def test_the_sessions_dir_is_the_same_from_primary_linked_and_lane_checkouts(
    repo: Repo,
) -> None:
    lane = _new(repo, "alpha")
    cockpit = repo.root / ".claude" / "worktrees" / "cockpit"
    _git(repo.root, "worktree", "add", "-q", "-b", "cockpit", str(cockpit), "trunk")
    expected = str(lane)
    for checkout in (repo.root, cockpit, lane):
        resolved = repo.run(checkout, "path", "alpha")
        assert resolved.returncode == 0, (checkout, resolved.stderr)
        assert resolved.stdout.strip() == expected, checkout


def test_an_explicit_sessions_dir_still_wins(repo: Repo, tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    repo.env["DEVKIT_SESSIONS_DIR"] = str(elsewhere)
    created = repo.run(repo.root, "new", "beta")
    assert created.returncode == 0, created.stderr
    assert (elsewhere / "beta" / "wt").is_dir()
    assert not (repo.sessions / "beta").exists()


def test_overlap_names_lanes_that_change_the_same_file(repo: Repo) -> None:
    alpha, beta, gamma = (_new(repo, s) for s in ("alpha", "beta", "gamma"))
    # alpha commits to shared.txt, beta leaves it uncommitted, gamma only adds a
    # new untracked file: each kind of change counts toward a footprint.
    (alpha / "shared.txt").write_text("alpha\n", encoding="utf-8")
    _git(alpha, "commit", "-q", "-am", "alpha")
    (beta / "shared.txt").write_text("beta\n", encoding="utf-8")
    (gamma / "new.txt").write_text("gamma\n", encoding="utf-8")
    board = _board(repo)
    assert board["alpha"][6] == "beta"
    assert board["beta"][6] == "alpha"
    assert board["gamma"][6] == "—"
    (gamma / "other.txt").write_text("gamma\n", encoding="utf-8")
    (alpha / "other.txt").write_text("alpha\n", encoding="utf-8")
    board = _board(repo)
    assert board["alpha"][6] == "beta,gamma"
    assert board["gamma"][6] == "alpha"


def _attempt(session: Path, *, pid: int, descriptor_id: str = "d1") -> None:
    (session / "launch-attempt.json").write_text(
        json.dumps(
            {"status": "starting", "descriptor_id": descriptor_id,
             "parent_process": {"pid": pid}}
        ),
        encoding="utf-8",
    )


def _receipt(session: Path, status: str, descriptor_id: str = "d1") -> None:
    (session / f"launch-receipt-{descriptor_id}.json").write_text(
        json.dumps({"status": status, "descriptor_id": descriptor_id}),
        encoding="utf-8",
    )


def _dead_pid() -> int:
    child = subprocess.Popen(["true"])
    child.wait()
    return child.pid


def test_run_reports_the_headless_wrappers_own_evidence(repo: Repo) -> None:
    scopes = ("plain", "starting", "running", "lost", "done", "broken")
    for scope in scopes:
        _new(repo, scope)
    s = repo.sessions
    _attempt(s / "starting", pid=os.getpid())
    _attempt(s / "running", pid=os.getpid())
    _receipt(s / "running", "observed")
    _attempt(s / "lost", pid=_dead_pid())
    _receipt(s / "lost", "observed")
    _attempt(s / "done", pid=_dead_pid())
    _receipt(s / "done", "completed")
    (s / "broken" / "launch-attempt.json").write_text("{not json", encoding="utf-8")
    board = _board(repo)
    assert {scope: board[scope][5] for scope in scopes} == {
        "plain": "—",
        "starting": "starting",
        "running": "running",
        "lost": "lost",
        "done": "completed",
        "broken": "?",
    }


def test_a_receipt_status_is_shown_only_when_it_is_a_plain_word(repo: Repo) -> None:
    _new(repo, "odd")
    _attempt(repo.sessions / "odd", pid=_dead_pid())
    _receipt(repo.sessions / "odd", "done\tforged")
    assert _board(repo)["odd"][5] == "?"


def test_the_watch_board_carries_the_same_columns(repo: Repo) -> None:
    _new(repo, "alpha")
    _attempt(repo.sessions / "alpha", pid=os.getpid())
    watched = repo.run(repo.root, "list", "--watch", "1", "--max-iters", "1")
    assert watched.returncode == 0, watched.stderr
    rows = [line.split() for line in watched.stdout.splitlines() if line.strip()]
    header = next(row for row in rows if "SCOPE" in row)
    assert header == ["SCOPE", "BRANCH", "PR", "CI", "DIRTY", "RUN", "OVERLAP", "SANDBOX"]
    alpha = next(row for row in rows if row and row[0] == "alpha")
    assert alpha[5:] == ["starting", "—", "alpha/state"]


def _pr_watch_mark_seen(repo: Repo, checkout: Path, pr: int, **extra: str):
    engine = checkout / "scripts" / "devkit" / "pr_watch.py"
    if not engine.exists():
        shutil.copy2(ENGINE_DIR / "pr_watch.py", engine)
    return subprocess.run(
        ["python3", str(engine), str(pr), "--mark-seen"],
        cwd=checkout,
        env={**repo.env, **extra},
        check=False,
        capture_output=True,
        text=True,
    )


def test_a_cockpit_poll_names_the_lane_that_holds_the_prs_watch_state(
    repo: Repo,
) -> None:
    _new(repo, "alpha")
    lane_state = repo.sessions / "alpha" / "state" / "pr-watch"
    lane_state.mkdir(parents=True)
    (lane_state / "41.json").write_text("{}", encoding="utf-8")
    hinted = _pr_watch_mark_seen(repo, repo.root, 41)
    assert hinted.returncode == 0, hinted.stderr
    assert "lane session(s) alpha" in hinted.stderr
    assert "dev_session.sh pr-watch <scope>" in hinted.stderr
    # Another PR number, or a run that chose its own state root, gets no hint.
    assert "lane session" not in _pr_watch_mark_seen(repo, repo.root, 42).stderr
    chosen = _pr_watch_mark_seen(
        repo, repo.root, 41, DEVKIT_STATE_ROOT=str(repo.sessions / "alpha" / "state")
    )
    assert "lane session" not in chosen.stderr


def _sessions_dir_from(repo_root: Path, env: dict[str, str]) -> str:
    return subprocess.run(
        ["bash", "-c", f'source "{ENGINE_DIR / "lib" / "repo_root.sh"}"; '
         f'devkit_default_sessions_dir "{repo_root}"'],
        env=env, check=True, capture_output=True, text=True,
    ).stdout.strip()


def test_a_bare_primary_keeps_the_invoking_checkouts_sibling(tmp_path: Path) -> None:
    bare = tmp_path / "bare.git"
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "trunk")
    _git(seed, "-c", "user.email=t@e", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "s")
    subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(bare)], check=True)
    linked = tmp_path / "nested" / "wt"
    _git(bare, "worktree", "add", "-q", str(linked), "trunk")
    resolved = _sessions_dir_from(linked, dict(os.environ))
    assert resolved == str(tmp_path / "nested" / "dev-model-sessions")


def test_a_primary_that_is_not_a_directory_falls_back(tmp_path: Path) -> None:
    # A git that names a primary which no longer exists on disk.
    shim = tmp_path / "bin"
    shim.mkdir()
    fake = shim / "git"
    fake.write_text(
        "#!/bin/sh\nprintf 'worktree %s\\0HEAD 0\\0\\0' "
        f"'{tmp_path / 'gone' / 'primary'}'\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    checkout = tmp_path / "here" / "checkout"
    checkout.mkdir(parents=True)
    env = {**os.environ, "PATH": f"{shim}{os.pathsep}{os.environ['PATH']}"}
    assert _sessions_dir_from(checkout, env) == str(tmp_path / "here" / "dev-model-sessions")


def test_untracked_files_alone_make_two_lanes_overlap(repo: Repo) -> None:
    alpha, beta = (_new(repo, s) for s in ("alpha", "beta"))
    (alpha / "new.txt").write_text("a\n", encoding="utf-8")
    (beta / "new.txt").write_text("b\n", encoding="utf-8")
    board = _board(repo)
    assert board["alpha"][6] == "beta"
    assert board["beta"][6] == "alpha"


def test_a_base_that_reads_as_an_option_is_not_passed_to_git(repo: Repo) -> None:
    _new(repo, "alpha")
    (repo.sessions / "alpha" / "base").write_text(
        f"--output={repo.root.parent / 'injected'}\n", encoding="utf-8"
    )
    assert _board(repo)["alpha"][6] == "?"
    assert not list(repo.root.parent.glob("injected*"))


def test_a_wrapper_that_died_before_any_receipt_is_lost(repo: Repo) -> None:
    _new(repo, "alpha")
    _attempt(repo.sessions / "alpha", pid=_dead_pid())
    assert _board(repo)["alpha"][5] == "lost"


def test_the_watch_board_marks_a_row_whose_run_state_changed(repo: Repo) -> None:
    _new(repo, "alpha")
    session = repo.sessions / "alpha"
    _attempt(session, pid=os.getpid())
    sigfile = repo.root.parent / "sigfile"
    sigfile.write_text("", encoding="utf-8")

    def frame() -> list[str]:
        rendered = subprocess.run(
            ["bash", "-c", f'source "{repo.engine(repo.root)}"; _list_render "{sigfile}"'],
            cwd=repo.root, env=repo.env, check=True, capture_output=True, text=True,
        ).stdout
        return next(line.split() for line in rendered.splitlines() if "alpha" in line.split()[:2])

    assert frame()[0] == "alpha"  # baseline: nothing marked
    assert frame()[0] == "alpha"  # unchanged: nothing marked
    _receipt(session, "observed")
    row = frame()
    assert row[:2] == ["*", "alpha"]
    assert row[6] == "running"
