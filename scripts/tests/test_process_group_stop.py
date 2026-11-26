"""lib/subprocess_runner.py's process-group stop, and the engines held to it (#1508).

A group's id is its leader's pid, safe to signal or probe only while the leader is
unreaped. The real-process tests below hold a leader unreaped the way the engines do
and check the stop against real signals; the rest pin the EPERM rule, the two
member readers, and that no moved engine calls `os.killpg` itself.
"""

from __future__ import annotations

import ast
import errno
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

import subprocess_runner as sr  # noqa: E402

# The engines moved onto the shared stop. #1508's second pull request adds
# `launch_lane.py`, and `reconcile_sessions.sh`'s embedded Python, to this list.
MOVED_SITES = ("runtime_smoke.py", "review_eval.py")


def _listed(pid: int) -> bool:
    """Whether `ps` lists `pid`; it lists a zombie until it is reaped."""
    out = subprocess.run(["ps", "-o", "pid=", "-p", str(pid)], capture_output=True, text=True).stdout
    return out.strip() == str(pid)


def _state(pid: int) -> str:
    return subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()


def _gone(pid: int, wait: float = 15.0) -> bool:
    """Exited: no such process, or a zombie only its new parent's reap is owed."""
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if not _listed(pid) or _state(pid).startswith("Z"):
            return True
        time.sleep(0.1)
    return False


def _start(script: str) -> subprocess.Popen:
    return subprocess.Popen(["bash", "-c", script], start_new_session=True)


def _await_exit(process: subprocess.Popen) -> None:
    assert sr.exited_unreaped(process.pid, 15)
    assert _listed(process.pid)  # observed, not reaped


# ------------------------------------------------------------ real processes


def test_a_held_zombie_leader_alone_is_no_live_member(tmp_path) -> None:
    leader = _start("exit 0")
    try:
        _await_exit(leader)
        assert sr.group_has_live_member(leader.pid) is False
    finally:
        leader.wait()


def test_a_member_the_exited_leader_left_behind_is_live(tmp_path) -> None:
    pid_file = tmp_path / "member"
    leader = _start(f"sleep 300 & echo $! > {pid_file}; exit 0")
    try:
        _await_exit(leader)
        assert sr.group_has_live_member(leader.pid) is True
        assert sr.signal_group(leader.pid, signal.SIGKILL) == sr.GROUP_SIGNALLED
        assert sr.wait_group_empty(leader.pid, 15)
        assert _gone(int(pid_file.read_text()))
    finally:
        leader.wait()


def test_the_stop_waits_for_the_group_not_its_leader(tmp_path) -> None:
    """The leader dies on SIGTERM; a descendant ignores it, so only SIGKILL ends it.
    The leader stays unreaped through the stop, and is reaped by the caller after."""
    pid_file = tmp_path / "descendant"
    leader = _start(f"(trap '' TERM; sleep 300 & echo $! > {pid_file}; wait) & wait")
    try:
        deadline = time.monotonic() + 15
        while not pid_file.exists() or not pid_file.read_text().strip():
            assert time.monotonic() < deadline
            time.sleep(0.05)
        started = time.monotonic()
        result = sr.stop_group(leader.pid, grace=1)
        assert result == sr.GroupStop(stopped=True)
        assert time.monotonic() - started >= 1  # SIGTERM's grace ran out first
        assert _listed(leader.pid)
        assert _gone(int(pid_file.read_text()))
    finally:
        leader.wait()
    assert leader.returncode == -signal.SIGTERM


def test_a_group_that_empties_on_sigterm_gets_no_sigkill(tmp_path, monkeypatch) -> None:
    sent: list[int] = []
    killpg = os.killpg

    def recording(pgid: int, signum: int) -> None:
        sent.append(signum)
        killpg(pgid, signum)

    leader = _start("sleep 300")
    monkeypatch.setattr(os, "killpg", recording)
    try:
        assert sr.stop_group(leader.pid, grace=10) == sr.GroupStop(stopped=True)
    finally:
        leader.wait()
    assert signal.SIGKILL not in sent and sent[0] == signal.SIGTERM


# ------------------------------------------------------------ the EPERM rule


def _killpg_answering(monkeypatch, error: type[OSError] | None) -> list[int]:
    sent: list[int] = []

    def answer(_pgid: int, signum: int) -> None:
        sent.append(signum)
        if error is not None:
            raise error(errno.EPERM if error is PermissionError else errno.ESRCH, "refused")

    monkeypatch.setattr(os, "killpg", answer)
    return sent


@pytest.mark.parametrize(("error", "outcome"), [(None, sr.GROUP_SIGNALLED),
                                                (ProcessLookupError, sr.GROUP_GONE),
                                                (PermissionError, sr.GROUP_DENIED)])
def test_signal_group_names_each_answer(monkeypatch, error, outcome) -> None:
    _killpg_answering(monkeypatch, error)
    assert sr.signal_group(424242, signal.SIGTERM) == outcome


def test_a_refusal_with_no_live_member_is_a_stopped_group(monkeypatch) -> None:
    """macOS refuses a group of zombies alone (#1238): nothing is left, and no escalation."""
    sent = _killpg_answering(monkeypatch, PermissionError)
    monkeypatch.setattr(sr, "group_has_live_member", lambda _pgid: False)
    assert sr.stop_group(424242, grace=0.1) == sr.GroupStop(stopped=True)
    assert sent == [signal.SIGTERM]


def test_a_refusal_with_a_live_member_ends_the_stop_denied(monkeypatch) -> None:
    """A member of another owner: the stop does not claim it, and the caller decides."""
    sent = _killpg_answering(monkeypatch, PermissionError)
    monkeypatch.setattr(sr, "group_has_live_member", lambda _pgid: True)
    assert sr.stop_group(424242, grace=0.1) == sr.GroupStop(stopped=False, denied=True)
    assert sent == [signal.SIGTERM]


def test_a_group_that_outlives_sigkill_is_not_stopped(monkeypatch) -> None:
    sent = _killpg_answering(monkeypatch, None)
    monkeypatch.setattr(sr, "group_has_live_member", lambda _pgid: True)
    assert sr.stop_group(424242, grace=0.1) == sr.GroupStop(stopped=False)
    assert sent == [signal.SIGTERM, signal.SIGKILL]


# ------------------------------------------------------------ member readers


def _fake_proc(root: Path, rows: dict[int, bytes]) -> Path:
    (root / "self").mkdir(parents=True)
    (root / "self" / "stat").write_bytes(b"1 (self) S 0 1 1")
    (root / "sys").mkdir()
    for pid, stat in rows.items():
        (root / str(pid)).mkdir()
        (root / str(pid) / "stat").write_bytes(stat)
    return root


def test_the_proc_reader_counts_live_members_of_the_group_only(tmp_path) -> None:
    proc = _fake_proc(tmp_path / "proc", {
        700: b"700 (leader) Z 1 700 700 0",
        701: b"701 (a ) S 700 (x) R 700 700 700 0",  # a name holding ") " and spaces
        702: b"702 (dead) X 700 700 700 0",
        703: b"703 (other) S 1 703 703 0",
    })
    assert list(sr._proc_live_members(proc, 700)) == [701]
    assert list(sr._proc_live_members(proc, 703)) == [703]
    assert list(sr._proc_live_members(proc, 999)) == []


def _ps_listing(monkeypatch, stdout: str, returncode: int = 0) -> None:
    monkeypatch.setattr(sr, "run_result", lambda argv, **_kw: sr.Completed(returncode, stdout, "ps: no"))


@pytest.mark.parametrize(("listing", "live"), [
    ("  700   700 Z\n  701   700 Z+\n  800   800 S\n", False),
    ("  700   700 Z\n  701   700 S+\n", True),
    ("  7000  7000 S\n  700  7001 S\n", False),  # neither row is group 700
])
def test_the_ps_reader_counts_non_zombie_rows_of_the_group(monkeypatch, listing, live) -> None:
    _ps_listing(monkeypatch, listing)
    assert sr._ps_has_live_member(700) is live


def test_a_ps_that_fails_is_unavailable_not_empty(monkeypatch) -> None:
    _ps_listing(monkeypatch, "", returncode=1)
    with pytest.raises(sr.GroupObserverUnavailable):
        sr._ps_has_live_member(700)


@pytest.mark.skipif(Path("/proc/self/stat").is_file(), reason="Linux reads /proc, not the probe")
def test_without_proc_only_a_refused_probe_asks_ps(monkeypatch) -> None:
    asked: list[int] = []
    monkeypatch.setattr(sr, "_ps_has_live_member", lambda pgid: asked.append(pgid) or True)
    for error, live in ((None, True), (ProcessLookupError, False)):
        _killpg_answering(monkeypatch, error)
        assert sr.group_has_live_member(700) is live
    assert asked == []
    _killpg_answering(monkeypatch, PermissionError)
    assert sr.group_has_live_member(700) is True and asked == [700]


# ------------------------------------------------------------ exit observer


@pytest.mark.skipif(not hasattr(select, "kqueue"), reason="no kqueue here")
@pytest.mark.parametrize(("code", "outcome"), [(errno.ESRCH, True), (errno.EPERM, sr.GroupObserverUnavailable)])
def test_a_kqueue_error_event_is_an_exit_only_when_it_says_no_such_process(monkeypatch, code, outcome) -> None:
    class Event:
        flags, data, fflags = select.KQ_EV_ERROR, code, 0

    class Queue:
        def control(self, changes, max_events, timeout):
            return [Event()]

        def close(self):
            pass

    monkeypatch.delattr(os, "waitid", raising=False)
    monkeypatch.setattr(select, "kqueue", Queue)
    if outcome is True:
        assert sr.exited_unreaped(os.getpid(), 1) is True
    else:
        with pytest.raises(outcome):
            sr.exited_unreaped(os.getpid(), 1)


# ------------------------------------------------------------ the one killpg


def _killpg_references(tree: ast.AST) -> list[int]:
    """Lines naming `killpg` in any form: `os.killpg`, an alias of it, or an import."""
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "killpg" or isinstance(node, ast.Name) and node.id == "killpg" or isinstance(node, ast.ImportFrom) and any(alias.name == "killpg" for alias in node.names):
            lines.append(node.lineno)
    return lines


@pytest.mark.parametrize("site", MOVED_SITES)
def test_a_moved_engine_never_calls_killpg_itself(site) -> None:
    tree = ast.parse((ENGINE_DIR / site).read_text(encoding="utf-8"))
    assert _killpg_references(tree) == [], f"{site} names killpg; stop a group through subprocess_runner"


def test_the_runner_calls_killpg_in_signal_group_alone() -> None:
    tree = ast.parse((ENGINE_DIR / "lib" / "subprocess_runner.py").read_text(encoding="utf-8"))
    owners = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
              and _killpg_references(node)]
    assert owners == ["signal_group"]
    assert len(_killpg_references(tree)) == 1


def test_the_guard_sees_each_spelling_of_killpg() -> None:
    for source in ("import os\nos.killpg(1, 9)\n", "from os import killpg\nkillpg(1, 9)\n",
                   "import os\nk = os.killpg\nk(1, 9)\n"):
        assert _killpg_references(ast.parse(source)), source
