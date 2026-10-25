"""dev_session.sh: where the sessions container resolves, the board's RUN and
OVERLAP columns, and the read-only help surface.

The sessions container must resolve to the same directory from the primary
checkout, a linked cockpit worktree and a lane worktree (#479). The board reads
each lane's headless-wrapper evidence for RUN and its changed files for OVERLAP;
both are read-only displays. `<subcommand> --help` prints that subcommand's usage
and touches nothing (#454).
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
        # pr_watch.py's mirror, behind its lane-state hint, agrees.
        assert _python_sessions_dir(checkout, repo.env) == str(repo.sessions), checkout


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


def _attempt(session: Path, *, pid: object, descriptor_id: str = "d1") -> None:
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


def test_a_stalled_lane_is_shown_as_stalled(repo: Repo) -> None:
    # launch_lane.py's status for a lane that ended without naming a terminal state.
    _new(repo, "stuck")
    _attempt(repo.sessions / "stuck", pid=_dead_pid())
    _receipt(repo.sessions / "stuck", "stalled")
    assert _board(repo)["stuck"][5] == "stalled"


def test_a_receipt_status_is_shown_only_when_it_is_a_plain_word(repo: Repo) -> None:
    _new(repo, "odd")
    _attempt(repo.sessions / "odd", pid=_dead_pid())
    _receipt(repo.sessions / "odd", "done\tforged")
    assert _board(repo)["odd"][5] == "?"


@pytest.mark.parametrize("status", ["a" * 17, "Completed", "complété"], ids=["long", "upper", "non-ascii"])
def test_a_receipt_status_the_launcher_would_not_write_is_unknown(repo: Repo, status: str) -> None:
    _new(repo, "odd")
    _attempt(repo.sessions / "odd", pid=_dead_pid())
    _receipt(repo.sessions / "odd", status)
    assert _board(repo)["odd"][5] == "?"


def test_an_oversized_session_file_is_unknown(repo: Repo) -> None:
    _new(repo, "alpha")
    session = repo.sessions / "alpha"
    _attempt(session, pid=_dead_pid())
    (session / "launch-receipt-d1.json").write_text(
        # Valid JSON then padding: the first MiB alone still parses, so only
        # the explicit size check refuses it.
        json.dumps({"status": "completed"}) + " " * (1 << 20), encoding="utf-8"
    )
    assert _board(repo)["alpha"][5] == "?"


@pytest.mark.parametrize("name", ["launch-attempt.json", "launch-receipt-d1.json"])
def test_a_dangling_session_file_link_is_unknown(repo: Repo, name: str) -> None:
    # A dangling link is a file that exists but cannot be read, not an absent one.
    _new(repo, "alpha")
    session = repo.sessions / "alpha"
    _attempt(session, pid=os.getpid())
    (session / name).unlink(missing_ok=True)
    (session / name).symlink_to(session / "nowhere.json")
    assert _board(repo)["alpha"][5] == "?"


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
    # A root chosen by a marker, with no env var, gets none either.
    marked = repo.root.parent / "marked-state"
    marked.mkdir()
    (repo.root / ".devkit_state_root").write_text(f"{marked}\n", encoding="utf-8")
    by_marker = _pr_watch_mark_seen(repo, repo.root, 41)
    assert by_marker.returncode == 0, by_marker.stderr
    assert "lane session" not in by_marker.stderr


def _shell_sessions_dir(repo_root: Path, env: dict[str, str]) -> str:
    return subprocess.run(
        ["bash", "-c", f'source "{ENGINE_DIR / "lib" / "repo_root.sh"}"; '
         f'devkit_default_sessions_dir "{repo_root}"'],
        env=env, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _python_sessions_dir(repo_root: Path, env: dict[str, str]) -> str:
    # pr_watch.py's mirror of the shell resolver, which its lane-state hint uses.
    return subprocess.run(
        ["python3", "-c",
         "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
         "import pr_watch; print(pr_watch._default_sessions_dir(Path(sys.argv[2])))",
         str(ENGINE_DIR), str(repo_root)],
        env=env, cwd=repo_root, check=True, capture_output=True, text=True,
    ).stdout.strip()


SESSIONS_DIR_RESOLVERS = pytest.mark.parametrize(
    "_sessions_dir_from", [_shell_sessions_dir, _python_sessions_dir], ids=["shell", "python"]
)


@SESSIONS_DIR_RESOLVERS
def test_a_bare_primary_keeps_the_invoking_checkouts_sibling(tmp_path: Path, _sessions_dir_from) -> None:
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


@SESSIONS_DIR_RESOLVERS
def test_a_separate_git_dir_keeps_the_checkouts_sibling(tmp_path: Path, _sessions_dir_from) -> None:
    # git lists the separate git dir itself as the first worktree.
    checkout = tmp_path / "here" / "checkout"
    checkout.parent.mkdir()
    (tmp_path / "gits").mkdir()
    subprocess.run(
        ["git", "init", "-q", "--separate-git-dir", str(tmp_path / "gits" / "x.git"), str(checkout)],
        check=True,
    )
    resolved = _sessions_dir_from(checkout, dict(os.environ))
    assert resolved == str(tmp_path / "here" / "dev-model-sessions")


@SESSIONS_DIR_RESOLVERS
def test_a_submodule_keeps_its_own_checkouts_sibling(tmp_path: Path, _sessions_dir_from) -> None:
    # git lists <super>/.git/modules/<name> as a submodule's first worktree.
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "trunk")
    _git(seed, "-c", "user.email=t@e", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "s")
    sup = tmp_path / "super"
    sup.mkdir()
    _git(sup, "init", "-q", "-b", "trunk")
    _git(sup, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(seed), "kit")
    resolved = _sessions_dir_from(sup / "kit", dict(os.environ))
    assert resolved == str(sup / "dev-model-sessions")


@SESSIONS_DIR_RESOLVERS
def test_a_primary_that_is_not_a_directory_falls_back(tmp_path: Path, _sessions_dir_from) -> None:
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


@pytest.mark.parametrize(
    "pid",
    [0, -1, 2**31, 2**64, "123", 1.5, True],
    ids=["zero", "group", "int32", "huge", "string", "float", "bool"],
)
def test_a_pid_that_names_no_single_process_is_not_read_as_alive(repo: Repo, pid: object) -> None:
    # 0 and negative pids address process groups, so os.kill succeeds on them;
    # pids past the C int range make os.kill raise instead.
    _new(repo, "alpha")
    _new(repo, "beta")
    _attempt(repo.sessions / "alpha", pid=pid)
    board = _board(repo)
    assert board["alpha"][5] == "?"
    assert board["beta"][5] == "—"  # read without raising, so the board survives


def test_a_live_pid_owned_by_someone_else_still_counts_as_alive(repo: Repo) -> None:
    if os.getuid() == 0:
        pytest.skip("root may signal every process, so no pid answers EPERM")
    _new(repo, "alpha")
    _attempt(repo.sessions / "alpha", pid=1)
    assert _board(repo)["alpha"][5] == "starting"


@pytest.mark.parametrize("status", [None, 5, ["completed"]], ids=["null", "number", "list"])
def test_a_receipt_without_a_plain_word_status_is_unknown(repo: Repo, status: object) -> None:
    _new(repo, "alpha")
    _new(repo, "beta")
    session = repo.sessions / "alpha"
    _attempt(session, pid=os.getpid())
    (session / "launch-receipt-d1.json").write_text(
        json.dumps({"status": status, "descriptor_id": "d1"}), encoding="utf-8"
    )
    board = _board(repo)
    assert board["alpha"][5] == "?"
    assert board["beta"][5] == "—"


def test_a_session_file_that_is_not_a_regular_file_never_blocks_the_board(repo: Repo) -> None:
    _new(repo, "alpha")
    _new(repo, "beta")
    os.mkfifo(repo.sessions / "alpha" / "launch-attempt.json")
    listed = subprocess.run(
        ["bash", str(repo.engine(repo.root)), "list"],
        cwd=repo.root, env=repo.env, capture_output=True, text=True, timeout=60,
    )
    assert listed.returncode == 0, listed.stderr
    rows = {line.split()[0]: line.split() for line in listed.stdout.splitlines()[1:]}
    assert rows["alpha"][5] == "?"
    assert rows["beta"][5] == "—"


def test_one_malformed_attempt_file_costs_only_its_own_row(repo: Repo) -> None:
    alpha, beta = (_new(repo, s) for s in ("alpha", "beta"))
    (alpha / "shared.txt").write_text("a\n", encoding="utf-8")
    (beta / "shared.txt").write_text("b\n", encoding="utf-8")
    (repo.sessions / "alpha" / "launch-attempt.json").write_text(
        json.dumps({"descriptor_id": "d1", "parent_process": "not-a-map"}), encoding="utf-8"
    )
    board = _board(repo)
    assert board["alpha"][5] == "?"
    assert board["beta"][5] == "—"
    assert (board["alpha"][6], board["beta"][6]) == ("beta", "alpha")


def test_the_watch_board_marks_a_row_whose_run_or_overlap_changed(repo: Repo) -> None:
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
    assert frame()[0] == "alpha"  # settled again
    # alpha dirties a file (its DIRTY moves), then a new peer touches the same
    # file, which changes only alpha's OVERLAP cell.
    (repo.sessions / "alpha" / "wt" / "shared.txt").write_text("a\n", encoding="utf-8")
    assert frame()[:2] == ["*", "alpha"]
    beta = _new(repo, "beta")
    (beta / "shared.txt").write_text("b\n", encoding="utf-8")
    row = frame()
    assert row[:2] == ["*", "alpha"]
    assert row[7] == "beta"


HELP_SUBCOMMANDS = {
    "new": "new",
    "list": "list",
    "ls": "list",
    "path": "path",
    "pr-watch": "pr-watch",
    "merge": "merge",
    "rm": "rm",
    "remove": "rm",
    "print-contract": "print-contract",
}


def _repository_snapshot(repo: Repo) -> tuple[str, str, str, list[str]]:
    return (
        _git(repo.root, "branch", "--list"),
        _git(repo.root, "worktree", "list", "--porcelain"),
        _git(repo.root, "status", "--porcelain", "--ignored"),
        sorted(path.name for path in repo.root.parent.iterdir()),
    )


@pytest.mark.parametrize("flag", ["--help", "-h"])
@pytest.mark.parametrize("subcommand", sorted(HELP_SUBCOMMANDS))
def test_subcommand_help_prints_its_usage_and_changes_nothing(
    repo: Repo, subcommand: str, flag: str
) -> None:
    before = _repository_snapshot(repo)

    result = repo.run(repo.root, subcommand, flag)

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(
        f"usage: scripts/dev_session.sh {HELP_SUBCOMMANDS[subcommand]}"
    ), result.stdout
    assert len(result.stdout.splitlines()) == 1
    assert _repository_snapshot(repo) == before
    assert not repo.sessions.exists()


def test_new_help_names_every_flag_new_accepts(repo: Repo) -> None:
    usage = repo.run(repo.root, "new", "--help").stdout
    source = repo.engine(repo.root).read_text(encoding="utf-8")
    start = source.index("cmd_new() {")
    body = source[start : source.index("\n}\n", start)]
    accepted = {
        line.strip().split(")")[0]
        for line in body.splitlines()
        if line.strip().startswith("--") and ")" in line
    }
    assert accepted
    for flag in accepted:
        assert f"[{flag}" in usage, flag


def test_top_level_help_prints_the_whole_header_and_nothing_past_it(repo: Repo) -> None:
    # Both help paths print a fixed line range of the header; a header edit that
    # moves its end must move that range too. The header's help text ends with the
    # blank comment line after the print-contract paragraph.
    printed = repo.run(repo.root, "help")
    assert printed.returncode == 0, printed.stderr
    header = []
    for line in repo.engine(repo.root).read_text(encoding="utf-8").splitlines()[1:]:
        if not line.startswith("#"):
            break
        header.append(line)
    end = next(
        index
        for index, line in enumerate(header)
        if line.rstrip() == "#" and index > 0 and "eyeballing" in header[index - 1]
    )
    expected = [line[2:] if line.startswith("# ") else line[1:] for line in header[: end + 1]]
    assert printed.stdout.splitlines() == expected
