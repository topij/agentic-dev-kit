"""Run a command with a timeout and translate failures for engine CLI callers.

``run_stdout`` returns text stdout and raises for a non-zero exit. ``run_result``
(text) and ``run_bytes`` (bytes) return the exit code with the output instead, for
a caller whose answer is the exit code or whose content is bytes.

Every failure is a ``CommandError`` (a ``RuntimeError``), so a caller that only
needs "it did not work" catches one type. A caller that must treat the cases
differently catches the subclass: ``CommandTimedOut``, ``CommandUnavailable``
(the process could not start) or ``CommandFailed`` (it ran and exited non-zero;
raised by ``run_stdout`` only). A caller's own argument errors (a NUL byte in argv,
an empty argv, the wrong stdin type) are not translated, and ``run_stdout`` decodes as
it always has, so output in another encoding raises ``UnicodeDecodeError`` there.

The process-group functions at the end (``signal_group``, ``stop_group``,
``group_has_live_member``, ``exited_unreaped``) are how an engine stops a child it
started in a session of its own; their section says what the caller must hold.
"""

from __future__ import annotations

import errno
import os
import select
import signal
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class CommandError(RuntimeError):
    """A command did not produce its output."""


class CommandTimedOut(CommandError):
    """The command ran past its timeout and was killed."""


class CommandUnavailable(CommandError):
    """The command could not be started."""


class CommandFailed(CommandError):
    """The command ran and exited non-zero."""

    def __init__(self, message: str, *, returncode: int, stderr: str) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


def without_git_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return ``environ`` (default: this process's) with every ``GIT_*`` variable dropped.

    A ``GIT_DIR``, ``GIT_WORK_TREE``, ``GIT_INDEX_FILE`` or ``GIT_OBJECT_DIRECTORY``
    inherited from a hook or a calling Git would point ``git -C <path>`` at another
    repository than the one named, so a caller that names its repository by path
    runs Git without them.
    """
    source = os.environ if environ is None else environ
    return {key: value for key, value in source.items() if not key.startswith("GIT_")}


@dataclass(frozen=True)
class Completed:
    """A command that ran to its exit, whatever its exit code.

    ``stdout`` is ``str`` from ``run_result`` and ``bytes`` from ``run_bytes``;
    ``stderr`` is always text, decoded as UTF-8 with replacement. ``returncode`` is
    negative when a signal ended the command (``-9`` for ``SIGKILL``), so a caller
    whose answer is the exit code compares it with the codes it expects rather than
    treating every value but one as the other answer.
    """

    returncode: int
    stdout: str | bytes
    stderr: str


def _run(argv: list[str], *, cwd: Path | None, timeout: int, stdin: str | bytes | None,
         env: Mapping[str, str] | None, text: bool,
         encoding: str | None = None, errors: str | None = None) -> subprocess.CompletedProcess:
    """One ``subprocess.run`` call; a timeout or a failure to start becomes a CommandError.

    On a timeout ``subprocess.run`` kills the direct child and waits for it, as
    before. A process that child started keeps running, in the same process group
    or another; this runner does not reach it.
    """
    command = " ".join(argv)
    # Only a caller that names an encoding passes one, so run_stdout's call stays the
    # base's exactly (callers' tests stub subprocess.run with its keyword arguments).
    decoding = {} if encoding is None else {"encoding": encoding, "errors": errors}
    try:
        return subprocess.run(  # noqa: S603
            argv, cwd=None if cwd is None else str(cwd), timeout=timeout, input=stdin,
            env=None if env is None else dict(env), capture_output=True, text=text,
            check=False, **decoding,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(f"{command} timed out after {timeout}s") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise CommandUnavailable(f"{command} could not run: {exc}") from exc


def run_result(argv: list[str], *, cwd: Path | None, timeout: int, stdin_text: str | None = None,
               env: Mapping[str, str] | None = None) -> Completed:
    """Run a command with text in and out, and return its exit code, stdout and stderr.

    For a caller whose answer is the exit code (``git merge-base --is-ancestor``,
    ``git ls-files --error-unmatch``). A non-zero exit is returned, not raised. Both
    streams are UTF-8, and bytes that do not decode are replaced, so the exit code is
    always returned. A caller that needs the exact bytes uses ``run_bytes``. A timeout
    raises ``CommandTimedOut`` and a command that cannot start raises
    ``CommandUnavailable``. ``cwd`` and ``env`` are as for ``run_stdout``.
    """
    result = _run(argv, cwd=cwd, timeout=timeout, stdin=stdin_text, env=env, text=True,
                  encoding="utf-8", errors="replace")
    return Completed(result.returncode, result.stdout, result.stderr)


def run_bytes(argv: list[str], *, cwd: Path | None, timeout: int, stdin_bytes: bytes | None = None,
              env: Mapping[str, str] | None = None) -> Completed:
    """Run a command with bytes in and out, and return its exit code and output.

    For a caller that reads or writes content Git stores as bytes (``git show``,
    ``git cat-file blob``, ``git hash-object --stdin``). Exit codes and errors are as
    for ``run_result``; ``stdout`` is the raw bytes and ``stderr`` is decoded as UTF-8
    with replacement, for messages only.
    """
    result = _run(argv, cwd=cwd, timeout=timeout, stdin=stdin_bytes, env=env, text=False)
    return Completed(result.returncode, result.stdout, result.stderr.decode("utf-8", "replace"))


def run_stdout(argv: list[str], *, cwd: Path | None, timeout: int, stdin_text: str | None = None,
               env: Mapping[str, str] | None = None) -> str:
    """Return stdout verbatim, or raise a CommandError naming the command and cause.

    The call is the one this function has always made: text mode in the locale's
    encoding, strict, so output that does not decode raises ``UnicodeDecodeError`` (a
    ``ValueError``) as before, and a caller expecting such output uses ``run_bytes``.
    A non-zero exit, including one a signal caused, raises ``CommandFailed``.
    ``cwd=None`` runs in the current directory; ``env=None`` inherits this process's
    environment.
    """
    result = _run(argv, cwd=cwd, timeout=timeout, stdin=stdin_text, env=env, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise CommandFailed(f"{' '.join(argv)} failed (exit {result.returncode}): {stderr}",
                            returncode=result.returncode, stderr=stderr)
    return result.stdout


# ---------------------------------------------------------------- process groups
#
# A child started with ``start_new_session=True`` leads a process group whose id is
# its pid. That id is only safe to signal, or to probe, while the pid cannot be
# reused, which is while the leader is unreaped: once it is reaped and the group's
# other members have exited, an unrelated process can take the pid and become a
# group of the same id (#1172, #1508). So every function below that names a group
# requires the caller to hold its leader unreaped until the call returns, and to reap
# it (``Popen.wait()``, which keeps ``returncode`` right) only after its last call.
# ``Popen.poll()``, ``communicate()``, ``send_signal()`` and ``kill()`` all reap a
# leader that has exited, so none of them may run first.
#
# ``signal_group`` is the one place ``os.killpg`` is called; the engines that stop a
# group call these functions rather than ``os.killpg`` (a test holds them to it).


class GroupObserverUnavailable(CommandError):
    """This platform offers no way to answer what was asked of a process or group."""


# How often a wait below looks again.
GROUP_POLL_SECONDS = 0.05
# Asked which members a group has where there is no /proc. Absolute, so PATH
# cannot choose it.
PS = "/bin/ps"
PS_TIMEOUT = 10

GROUP_SIGNALLED = "signalled"
GROUP_GONE = "gone"
GROUP_DENIED = "denied"


def signal_group(pgid: int, signum: int) -> str:
    """Send ``signum`` (0 probes) to group ``pgid``: ``signalled``, ``gone`` or ``denied``.

    ``gone`` is ``ESRCH``: no process is in the group. ``denied`` is ``EPERM``, which
    names no single cause, so the caller asks ``group_has_live_member`` before acting
    on it. Every input that answers ``EPERM`` while the caller holds the leader:
    - macOS, every member a zombie, the held leader included (#1238): nothing is
      left to stop;
    - a live member this process may not signal (another owner): something is left;
    - Linux never answers ``EPERM`` for a zombie, which it signals as a no-op.
    """
    try:
        os.killpg(pgid, signum)
    except ProcessLookupError:
        return GROUP_GONE
    except PermissionError:
        return GROUP_DENIED
    return GROUP_SIGNALLED


def group_has_live_member(pgid: int) -> bool:
    """Whether group ``pgid`` has a member that is not a zombie.

    A zombie has exited, and the held leader is one once it exits, so it does not
    count. Linux signals a zombie without complaint, so there a probe cannot tell
    a held leader from a live member, and this reads each process's state and group
    from ``/proc``. Elsewhere a probe answers first: macOS signals a group with any
    live member and refuses one of zombies alone (``signal_group``); only that
    refusal, which a live member of another owner gives too, is settled by listing
    the group with ``ps``. Raises ``GroupObserverUnavailable`` when neither can be
    read, rather than report a group empty that may not be.

    A ``/proc`` mounted with ``hidepid`` hides other owners' processes, so there a
    member of another owner is not seen.
    """
    proc = Path("/proc")
    if (proc / "self" / "stat").is_file():
        return any(True for _ in _proc_live_members(proc, pgid))
    outcome = signal_group(pgid, 0)
    if outcome == GROUP_GONE:
        return False
    if outcome == GROUP_SIGNALLED:
        return True
    return _ps_has_live_member(pgid)


def _proc_live_members(proc: Path, pgid: int):
    for entry in proc.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            stat = (entry / "stat").read_bytes()
        except OSError:  # it exited while the listing ran, or is not ours to read
            continue
        # The command name is in parentheses and may hold any byte, ')' and spaces
        # included, so the fields are counted from its last ')'.
        fields = stat.rpartition(b")")[2].split()
        if len(fields) < 3:
            continue
        state, group = fields[0], fields[2]
        if group == str(pgid).encode() and state not in (b"Z", b"X"):
            yield int(entry.name)


def _ps_has_live_member(pgid: int) -> bool:
    try:
        listed = run_result([PS, "-axo", "pid=,pgid=,stat="], cwd=None, timeout=PS_TIMEOUT)
    except CommandError as exc:
        raise GroupObserverUnavailable(f"cannot list process group {pgid}: {exc}") from exc
    if listed.returncode != 0:
        raise GroupObserverUnavailable(
            f"cannot list process group {pgid}: {PS} exited {listed.returncode}: {listed.stderr.strip()}")
    for line in listed.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[1] == str(pgid) and not fields[2].startswith("Z"):
            return True
    return False


def wait_group_empty(pgid: int, timeout: float) -> bool:
    """Whether group ``pgid`` has no live member within ``timeout`` seconds."""
    deadline = time.monotonic() + timeout
    while group_has_live_member(pgid):
        if time.monotonic() >= deadline:
            return False
        time.sleep(GROUP_POLL_SECONDS)
    return True


@dataclass(frozen=True)
class GroupStop:
    """What ``stop_group`` found. ``stopped``: no live member is left.

    ``denied``: a signal was refused while a live member remained, so the stop
    ended without escalating; the caller decides whether that is a refusal.
    """

    stopped: bool
    denied: bool = False


def stop_group(pgid: int, *, grace: float) -> GroupStop:
    """Stop group ``pgid``: ``SIGTERM``, up to ``grace`` for it to empty, then the same with ``SIGKILL``.

    The group is stopped when no live member is left, not when its leader exits: a
    descendant that ignores ``SIGTERM`` outlives a leader that does not. The caller
    holds the leader unreaped for the whole call (see above) and reaps it after.
    """
    for signum in (signal.SIGTERM, signal.SIGKILL):
        outcome = signal_group(pgid, signum)
        if outcome == GROUP_GONE:
            return GroupStop(stopped=True)
        if outcome == GROUP_DENIED:
            if group_has_live_member(pgid):
                return GroupStop(stopped=False, denied=True)
            return GroupStop(stopped=True)
        if wait_group_empty(pgid, grace):
            return GroupStop(stopped=True)
    return GroupStop(stopped=False)


def exited_unreaped(pid: int, timeout: float) -> bool:
    """Whether the child ``pid`` exits within ``timeout``, leaving it unreaped.

    ``os.waitid`` with ``WNOWAIT`` where Python has it. macOS lacks it before Python
    3.13, which the engines' floor admits, so there a kqueue ``NOTE_EXIT`` watch. A
    child that already exited, a zombie, cannot be watched: kqueue answers with an
    ``EV_ERROR`` event carrying ``ESRCH``, which is read as the exit. Any other
    error raises ``GroupObserverUnavailable`` rather than pass for one.
    """
    if hasattr(os, "waitid"):
        deadline = time.monotonic() + timeout
        while os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT | os.WNOHANG) is None:
            if time.monotonic() >= deadline:
                return False
            time.sleep(GROUP_POLL_SECONDS)
        return True
    if hasattr(select, "kqueue"):
        queue = select.kqueue()
        try:
            watch = select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                  flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                  fflags=select.KQ_NOTE_EXIT)
            events = queue.control([watch], 1, timeout)
        finally:
            queue.close()
        if not events:
            return False
        if events[0].flags & select.KQ_EV_ERROR:
            if events[0].data == errno.ESRCH:
                return True
            raise GroupObserverUnavailable(
                f"kqueue could not watch process {pid}'s exit: {os.strerror(events[0].data)}")
        return True  # the watch asks for NOTE_EXIT alone, so any other event is that
    raise GroupObserverUnavailable("this platform offers no way to observe an exit without reaping it")
