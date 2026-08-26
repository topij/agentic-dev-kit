#!/usr/bin/env python3
"""Launch one Codex headless lane from a one-shot dev-session descriptor.

The public path validates the durable descriptor, scrubs inherited lane and
repository identity, starts a child observer in the intended worktree, and does
not acknowledge a successful launch until the child's independent observation is
durably bound to the descriptor and process.  The observer then ``exec``s the
config-selected Codex command without changing PID.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import secrets
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from kitconfig import get, load_config, repo_root  # noqa: E402

SCHEMA_VERSION = 1
DESCRIPTOR_NAME = "launch-descriptor.json"
REQUIRED_ENV_KEYS = frozenset(
    {
        "DEVKIT_STATE_ROOT",
        "DEVKIT_ROOT",
        "DEVKIT_REFUSE_UNSANDBOXED_STATE",
    }
)
REPOSITORY_OVERRIDE_KEYS = frozenset(
    {
        "GH_REPO",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "PWD",
        "OLDPWD",
    }
)


class LaunchError(RuntimeError):
    """A fail-closed launcher refusal."""


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_stable_regular_file(path: Path) -> bytes:
    try:
        before_path = path.lstat()
    except OSError as exc:
        raise LaunchError(f"cannot inspect {path}: {exc}") from exc
    if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
        raise LaunchError(f"refusing non-regular or symlinked file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LaunchError(f"cannot open {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise LaunchError(f"file disappeared while reading {path}: {exc}") from exc
    identity = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)  # noqa: E731
    if identity(before) != identity(after) or identity(after) != identity(after_path):
        raise LaunchError(f"file changed while reading: {path}")
    return b"".join(chunks)


def _write_atomic(path: Path, value: object, *, exclusive: bool = False) -> None:
    payload = _canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        descriptor = os.open(path, flags, 0o600)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    else:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _parse_timestamp(value: object, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LaunchError(f"descriptor {field} must be a UTC timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LaunchError(f"descriptor {field} is invalid") from exc
    return parsed


def _load_descriptor(path: Path, *, now: dt.datetime | None = None) -> tuple[dict[str, Any], bytes]:
    absolute = path.absolute()
    if absolute != path:
        raise LaunchError("descriptor path must be absolute")
    raw = _read_stable_regular_file(path)
    try:
        descriptor = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LaunchError(f"descriptor is not valid JSON: {exc}") from exc
    if not isinstance(descriptor, dict) or _canonical_json(descriptor) != raw:
        raise LaunchError("descriptor bytes are not canonical")
    if descriptor.get("schema_version") != SCHEMA_VERSION:
        raise LaunchError("unsupported descriptor schema")
    if descriptor.get("descriptor_path") != str(path):
        raise LaunchError("descriptor was moved or names another descriptor path")
    if path.name != DESCRIPTOR_NAME:
        raise LaunchError(f"descriptor must be named {DESCRIPTOR_NAME}")
    descriptor_id = descriptor.get("descriptor_id")
    if not isinstance(descriptor_id, str):
        raise LaunchError("descriptor id is missing")
    try:
        parsed_descriptor_id = uuid.UUID(descriptor_id)
    except ValueError as exc:
        raise LaunchError("descriptor id must be a canonical UUID4") from exc
    if str(parsed_descriptor_id) != descriptor_id or parsed_descriptor_id.version != 4:
        raise LaunchError("descriptor id must be a canonical UUID4")
    issued = _parse_timestamp(descriptor.get("issued_at"), "issued_at")
    expires = _parse_timestamp(descriptor.get("expires_at"), "expires_at")
    current = now or dt.datetime.now(dt.timezone.utc)
    if issued > current or expires <= issued or current > expires:
        raise LaunchError("descriptor is not within its issue/expiry window")
    session_dir = path.parent.resolve()
    expected_paths = {
        "session_dir": session_dir,
        "worktree": session_dir / "wt",
        "state_root": session_dir / "state",
    }
    for field, expected in expected_paths.items():
        value = descriptor.get(field)
        if not isinstance(value, str) or Path(value).resolve() != expected:
            raise LaunchError(f"descriptor {field} is foreign to its session directory")
    if descriptor.get("scope") != session_dir.name:
        raise LaunchError("descriptor scope does not match its session directory")
    env = descriptor.get("env")
    if not isinstance(env, dict) or set(env) != REQUIRED_ENV_KEYS:
        raise LaunchError("descriptor env must contain exactly the lane identity keys")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in env.items()):
        raise LaunchError("descriptor env keys and values must be strings")
    if descriptor.get("runtime") != "codex":
        raise LaunchError("descriptor runtime is not codex")
    return descriptor, raw


def _config_for_launcher() -> tuple[list[str], int, int, int, Path]:
    root = repo_root(SCRIPT_DIR)
    config = load_config(root / "config" / "dev-model.yaml")
    command = get(config, "parallel.codex_headless_command", None)
    timeout = get(config, "parallel.observation_timeout_seconds", None)
    lifetime = get(config, "parallel.descriptor_ttl_seconds", None)
    termination_grace = get(config, "parallel.termination_grace_seconds", None)
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        raise LaunchError("config parallel.codex_headless_command must be a non-empty argv sequence")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise LaunchError("config parallel.observation_timeout_seconds must be positive")
    if not isinstance(lifetime, int) or isinstance(lifetime, bool) or lifetime <= 0:
        raise LaunchError("config parallel.descriptor_ttl_seconds must be positive")
    if (
        not isinstance(termination_grace, int)
        or isinstance(termination_grace, bool)
        or termination_grace <= 0
    ):
        raise LaunchError("config parallel.termination_grace_seconds must be positive")
    return list(command), timeout, lifetime, termination_grace, root.resolve()


def _git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LaunchError(f"git observation failed for {' '.join(args)}") from exc
    return result.stdout.strip()


def _process_start_fingerprint(pid: int) -> str | None:
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.is_file():
        try:
            suffix = proc_stat.read_text(encoding="utf-8").rsplit(")", 1)[1].split()
            return f"proc:{suffix[19]}"
        except (OSError, IndexError, UnicodeDecodeError):
            return None
    ps = Path("/bin/ps")
    if not ps.is_file():
        return None
    try:
        result = subprocess.run(
            [str(ps), "-o", "lstart=", "-p", str(pid)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    if not value:
        return None
    return f"ps:{value}"


def _observed_identity(process_nonce: str) -> dict[str, Any]:
    cwd = Path.cwd().resolve()
    git_top = Path(_git(cwd, "rev-parse", "--show-toplevel")).resolve()
    common_raw = Path(_git(cwd, "rev-parse", "--git-common-dir"))
    common_dir = (cwd / common_raw).resolve() if not common_raw.is_absolute() else common_raw.resolve()
    if common_dir.name != ".git":
        raise LaunchError("Git common directory does not identify a repository root")
    repository = common_dir.parent.resolve()
    session_dir = cwd.parent.resolve()
    state_root = (session_dir / "state").resolve()
    marker = _read_stable_regular_file(cwd / ".devkit_state_root").decode().strip()
    marker_root = Path(marker).resolve()
    persisted_branch = _read_stable_regular_file(session_dir / "branch").decode().strip()
    persisted_base = _read_stable_regular_file(session_dir / "base").decode().strip()
    merge_class = _read_stable_regular_file(session_dir / "merge_class").decode().strip()
    branch = _git(cwd, "symbolic-ref", "--short", "HEAD")
    base_oid = _git(cwd, "rev-parse", f"refs/remotes/origin/{persisted_base}")
    lane_oid = _git(cwd, "rev-parse", "HEAD")
    devkit_env = {key: value for key, value in os.environ.items() if key.startswith("DEVKIT_")}
    process = {
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "session_id": os.getsid(0),
        "capability_nonce": process_nonce,
        "start_fingerprint": _process_start_fingerprint(os.getpid()),
    }
    return {
        "scope": session_dir.name,
        "worktree": str(cwd),
        "git_top": str(git_top),
        "session_dir": str(session_dir),
        "state_root": str(state_root),
        "marker_state_root": str(marker_root),
        "repo_root": str(repository),
        "origin_url": _git(cwd, "remote", "get-url", "origin"),
        "branch": branch,
        "persisted_branch": persisted_branch,
        "base": persisted_base,
        "base_oid": base_oid,
        "lane_oid": lane_oid,
        "merge_class": merge_class,
        "environment": devkit_env,
        "pwd_environment": os.environ.get("PWD"),
        "repository_overrides_present": sorted(
            key for key in REPOSITORY_OVERRIDE_KEYS - {"PWD"} if key in os.environ
        ),
        "process": process,
    }


def _expected_identity(descriptor: dict[str, Any]) -> dict[str, Any]:
    return {
        key: descriptor[key]
        for key in (
            "scope",
            "worktree",
            "session_dir",
            "state_root",
            "repo_root",
            "origin_url",
            "branch",
            "base",
            "base_oid",
            "lane_oid",
            "merge_class",
        )
    } | {"environment": dict(descriptor["env"])}


def _validate_observation(expected: dict[str, Any], observed: dict[str, Any]) -> None:
    direct = (
        "scope",
        "worktree",
        "session_dir",
        "state_root",
        "repo_root",
        "origin_url",
        "branch",
        "base",
        "base_oid",
        "lane_oid",
        "merge_class",
        "environment",
    )
    for key in direct:
        if observed.get(key) != expected.get(key):
            raise LaunchError(f"child observation disagrees on {key}")
    if observed.get("git_top") != expected["worktree"]:
        raise LaunchError("Git top-level is not the intended worktree")
    if observed.get("marker_state_root") != expected["state_root"]:
        raise LaunchError("state-root marker does not identify the intended sandbox")
    if observed.get("persisted_branch") != expected["branch"]:
        raise LaunchError("persisted branch disagrees with the intended branch")
    if observed.get("pwd_environment") != expected["worktree"]:
        raise LaunchError("child PWD does not identify the intended worktree")
    if observed.get("repository_overrides_present"):
        raise LaunchError("repository override variables survived environment scrubbing")


def _read_pipe_capability(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    try:
        try:
            while chunk := os.read(descriptor, 64):
                chunks.append(chunk)
        except OSError as exc:
            raise LaunchError("parent launch capability pipe is unavailable") from exc
    finally:
        with contextlib.suppress(OSError):
            os.close(descriptor)
    capability = b"".join(chunks)
    if len(capability) != 32:
        raise LaunchError("parent launch capability is missing or malformed")
    return capability


def _validate_child_authority(
    arguments: argparse.Namespace,
    descriptor: dict[str, Any],
    descriptor_raw: bytes,
    command: list[str],
) -> str:
    if arguments.descriptor_id != descriptor["descriptor_id"]:
        raise LaunchError("child descriptor identity disagrees with the descriptor")
    expected_attempt_path = Path(descriptor["session_dir"]) / (
        f"launch-attempt-{descriptor['descriptor_id']}.json"
    )
    expected_receipt_path = Path(descriptor["session_dir"]) / (
        f"launch-receipt-{descriptor['descriptor_id']}.json"
    )
    expected_final_path = Path(descriptor["session_dir"]) / (
        f"launch-final-{descriptor['descriptor_id']}.txt"
    )
    attempt_path = Path(arguments.attempt)
    if attempt_path != expected_attempt_path:
        raise LaunchError("child attempt path is foreign to the descriptor session")
    if Path(arguments.receipt) != expected_receipt_path:
        raise LaunchError("child receipt path is foreign to the descriptor session")
    if Path(arguments.final_message) != expected_final_path:
        raise LaunchError("child final-message path is foreign to the descriptor session")
    attempt_raw = _read_stable_regular_file(attempt_path)
    try:
        attempt = json.loads(attempt_raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LaunchError("launch attempt is not valid JSON") from exc
    if not isinstance(attempt, dict) or _canonical_json(attempt) != attempt_raw:
        raise LaunchError("launch attempt is not canonical")
    capability = _read_pipe_capability(arguments.authority_fd)
    process_nonce = capability.hex()
    expected_request = {
        "descriptor_sha256": _sha256(descriptor_raw),
        "task_sha256": arguments.task_sha256,
        "combined_prompt_sha256": arguments.combined_prompt_sha256,
        "configured_command": list(command),
        "process_nonce_sha256": _sha256(process_nonce.encode()),
    }
    if (
        attempt.get("status") != "starting"
        or attempt.get("descriptor_id") != descriptor["descriptor_id"]
        or attempt.get("request") != expected_request
        or attempt.get("parent_process", {}).get("pid") != os.getppid()
    ):
        raise LaunchError("child is not bound to the exclusive parent launch attempt")
    parent_fingerprint = attempt["parent_process"].get("start_fingerprint")
    if parent_fingerprint is not None and parent_fingerprint != _process_start_fingerprint(
        os.getppid()
    ):
        raise LaunchError("parent process identity changed before child observation")
    return process_nonce


def _child_main(arguments: argparse.Namespace) -> int:
    descriptor_path = Path(arguments.descriptor)
    receipt_path: Path | None = None
    try:
        descriptor, raw = _load_descriptor(descriptor_path)
        receipt_path = Path(descriptor["session_dir"]) / (
            f"launch-receipt-{descriptor['descriptor_id']}.json"
        )
        command, _timeout, _lifetime, _termination_grace, config_root = (
            _config_for_launcher()
        )
        if Path(descriptor["repo_root"]).resolve() != config_root:
            raise LaunchError("descriptor repository is foreign to the launcher configuration")
        process_nonce = _validate_child_authority(arguments, descriptor, raw, command)
        expected = _expected_identity(descriptor)
        observed = _observed_identity(process_nonce)
        _validate_observation(expected, observed)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "status": "observed",
            "descriptor_id": descriptor["descriptor_id"],
            "request": {
                "descriptor_sha256": _sha256(raw),
                "task_sha256": arguments.task_sha256,
                "combined_prompt_sha256": arguments.combined_prompt_sha256,
                "configured_command": list(command),
                "process_nonce_sha256": _sha256(process_nonce.encode()),
            },
            "expected": dict(expected),
            "observed": dict(observed),
            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        _write_atomic(receipt_path, receipt)
        os.write(arguments.ready_fd, b"READY\n")
        os.close(arguments.ready_fd)
        if os.read(arguments.ack_fd, 1) != b"1":
            raise LaunchError("parent did not acknowledge the durable observation")
        os.close(arguments.ack_fd)
        final_message = str(Path(arguments.final_message))
        argv = [*command, "--cd", expected["worktree"], "--output-last-message", final_message, "-"]
        os.execvpe(argv[0], argv, os.environ)
    except LaunchError as exc:
        rejected = {
            "schema_version": SCHEMA_VERSION,
            "status": "rejected",
            "descriptor_id": arguments.descriptor_id,
            "error": str(exc),
        }
        if receipt_path is not None:
            _write_atomic(receipt_path, rejected)
        with contextlib.suppress(OSError):
            os.write(arguments.ready_fd, b"REJECTED\n")
        print(f"[codex-lane-launcher] child refused: {exc}", file=sys.stderr)
        return 70


def _scrubbed_environment(descriptor: dict[str, Any]) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("DEVKIT_") and key not in REPOSITORY_OVERRIDE_KEYS
    }
    environment.update(descriptor["env"])
    environment["PWD"] = descriptor["worktree"]
    return environment


def _read_receipt(path: Path) -> dict[str, Any]:
    raw = _read_stable_regular_file(path)
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LaunchError("receipt is not valid JSON") from exc
    if not isinstance(value, dict) or _canonical_json(value) != raw:
        raise LaunchError("receipt is not a canonical object")
    return value


def _validate_parent_binding(
    receipt: dict[str, Any],
    *,
    descriptor_id: str,
    request: dict[str, Any],
    pid: int,
    process_nonce: str,
    live_start_fingerprint: str | None,
) -> None:
    observed_process = receipt.get("observed", {}).get("process", {})
    if (
        receipt.get("status") != "observed"
        or receipt.get("descriptor_id") != descriptor_id
        or receipt.get("request") != request
        or observed_process.get("pid") != pid
        or observed_process.get("capability_nonce") != process_nonce
        or (
            live_start_fingerprint is not None
            and observed_process.get("start_fingerprint") != live_start_fingerprint
        )
    ):
        raise LaunchError("durable child observation or process identity is invalid")


def _terminal_receipt(
    receipt_path: Path,
    attempt: dict[str, Any],
    *,
    status: str,
    returncode: int | None,
    caught_signal: int | None,
    final_message: Path,
    error: str | None,
    required_observed_sha256: str | None = None,
) -> None:
    try:
        receipt = _read_receipt(receipt_path)
    except LaunchError:
        if required_observed_sha256 is not None:
            raise
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "descriptor_id": attempt["descriptor_id"],
            "request": dict(attempt["request"]),
        }
    binding_matches = (
        receipt.get("descriptor_id") == attempt["descriptor_id"]
        and receipt.get("request") == attempt["request"]
    )
    if required_observed_sha256 is not None:
        if (
            not binding_matches
            or receipt.get("status") != "observed"
            or _sha256(_canonical_json(receipt)) != required_observed_sha256
        ):
            raise LaunchError("observed receipt changed before successful terminalization")
    elif not binding_matches:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "descriptor_id": attempt["descriptor_id"],
            "request": dict(attempt["request"]),
        }
    final_bytes = b""
    if final_message.is_file() and not final_message.is_symlink():
        final_bytes = _read_stable_regular_file(final_message)
    receipt["status"] = status
    receipt["terminal"] = {
        "returncode": returncode,
        "signal": caught_signal,
        "error": error,
        "final_message_path": str(final_message),
        "final_message_sha256": _sha256(final_bytes) if final_bytes else None,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_atomic(receipt_path, receipt)


def _terminate_process_group(
    process: subprocess.Popen[bytes], grace_seconds: int
) -> int:
    if process.poll() is not None:
        return process.returncode
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        return process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        try:
            return process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired as exc:
            raise LaunchError("child process group survived forced termination") from exc


def _wait_for_process_or_signal(
    process: subprocess.Popen[bytes], caught: list[int]
) -> int | None:
    while not caught:
        try:
            return process.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            continue
    return None


def launch(descriptor_path: Path, prompt_path: Path) -> int:
    descriptor, descriptor_raw = _load_descriptor(descriptor_path)
    (
        command,
        observation_timeout,
        configured_lifetime,
        termination_grace,
        config_root,
    ) = _config_for_launcher()
    if Path(descriptor["repo_root"]).resolve() != config_root:
        raise LaunchError("descriptor repository is foreign to the launcher configuration")
    issued = _parse_timestamp(descriptor["issued_at"], "issued_at")
    expires = _parse_timestamp(descriptor["expires_at"], "expires_at")
    if int((expires - issued).total_seconds()) != configured_lifetime:
        raise LaunchError("descriptor lifetime disagrees with merged configuration")
    task = _read_stable_regular_file(prompt_path)
    try:
        task_text = task.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LaunchError("task prompt must be UTF-8 text") from exc
    combined = (descriptor["prompt_preamble"] + "\n\n" + task_text).encode()
    descriptor_id = descriptor["descriptor_id"]
    launch_capability = secrets.token_bytes(32)
    process_nonce = launch_capability.hex()
    session_dir = Path(descriptor["session_dir"])
    attempt_path = session_dir / f"launch-attempt-{descriptor_id}.json"
    receipt_path = session_dir / f"launch-receipt-{descriptor_id}.json"
    final_message = session_dir / f"launch-final-{descriptor_id}.txt"
    request = {
        "descriptor_sha256": _sha256(descriptor_raw),
        "task_sha256": _sha256(task),
        "combined_prompt_sha256": _sha256(combined),
        "configured_command": list(command),
        "process_nonce_sha256": _sha256(process_nonce.encode()),
    }
    attempt = {
        "schema_version": SCHEMA_VERSION,
        "status": "starting",
        "descriptor_id": descriptor_id,
        "request": dict(request),
        "parent_process": {
            "pid": os.getpid(),
            "start_fingerprint": _process_start_fingerprint(os.getpid()),
        },
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    try:
        _write_atomic(attempt_path, attempt, exclusive=True)
    except FileExistsError as exc:
        raise LaunchError("descriptor already has a launch attempt and cannot be reused") from exc

    ready_read, ready_write = os.pipe()
    ack_read, ack_write = os.pipe()
    authority_read, authority_write = os.pipe()
    child_arguments = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_child",
        "--descriptor",
        str(descriptor_path),
        "--attempt",
        str(attempt_path),
        "--receipt",
        str(receipt_path),
        "--final-message",
        str(final_message),
        "--descriptor-id",
        descriptor_id,
        "--task-sha256",
        request["task_sha256"],
        "--combined-prompt-sha256",
        request["combined_prompt_sha256"],
        "--authority-fd",
        str(authority_read),
        "--ready-fd",
        str(ready_write),
        "--ack-fd",
        str(ack_read),
    ]
    process: subprocess.Popen[bytes] | None = None
    caught: list[int] = []

    def relay(signum: int, _frame: object) -> None:
        caught.append(signum)
        if process is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signum)

    previous_handlers = {
        signum: signal.signal(signum, relay) for signum in (signal.SIGINT, signal.SIGTERM)
    }
    error: str | None = None
    bound_receipt_sha256: str | None = None
    try:
        process = subprocess.Popen(
            child_arguments,
            cwd=descriptor["worktree"],
            env=_scrubbed_environment(descriptor),
            stdin=subprocess.PIPE,
            pass_fds=(ready_write, ack_read, authority_read),
            start_new_session=True,
        )
        os.close(ready_write)
        os.close(ack_read)
        os.close(authority_read)
        ready_write = ack_read = authority_read = -1
        os.write(authority_write, launch_capability)
        os.close(authority_write)
        authority_write = -1
        deadline = time.monotonic() + observation_timeout
        ready = b""
        while b"\n" not in ready and process.poll() is None and not caught:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                error = "child observation timed out"
                break
            readable, _, _ = select.select([ready_read], [], [], remaining)
            if readable:
                chunk = os.read(ready_read, 64)
                if not chunk:
                    break
                ready += chunk
        if not caught and error is None:
            if ready != b"READY\n":
                rejected = _read_receipt(receipt_path) if receipt_path.exists() else {}
                error = f"child did not produce an accepted observation: {rejected.get('error', 'missing receipt')}"
            else:
                receipt = _read_receipt(receipt_path)
                try:
                    _validate_parent_binding(
                        receipt,
                        descriptor_id=descriptor_id,
                        request=request,
                        pid=process.pid,
                        process_nonce=process_nonce,
                        live_start_fingerprint=_process_start_fingerprint(process.pid),
                    )
                except LaunchError:
                    error = "durable child observation or process identity is invalid"
                if error is None:
                    bound_receipt_sha256 = _sha256(_canonical_json(receipt))
                    os.write(ack_write, b"1")
                    os.close(ack_write)
                    ack_write = -1
                    assert process.stdin is not None
                    process.stdin.write(combined)
                    process.stdin.close()
        returncode = None if error else _wait_for_process_or_signal(process, caught)
        if caught or error:
            returncode = _terminate_process_group(process, termination_grace)
        assert returncode is not None
        final_bytes = b""
        if final_message.is_file() and not final_message.is_symlink():
            final_bytes = _read_stable_regular_file(final_message)
        if caught:
            _terminal_receipt(
                receipt_path,
                attempt,
                status="interrupted",
                returncode=returncode,
                caught_signal=caught[0],
                final_message=final_message,
                error="launcher interrupted",
            )
            return 128 + caught[0]
        if error is not None or returncode != 0 or not final_bytes:
            if error is None:
                error = (
                    f"child exited with status {returncode}"
                    if returncode != 0
                    else "child returned success without final-message evidence"
                )
            _terminal_receipt(
                receipt_path,
                attempt,
                status="failed",
                returncode=returncode,
                caught_signal=None,
                final_message=final_message,
                error=error,
            )
            return 70
        if bound_receipt_sha256 is None:
            raise LaunchError("successful child has no bound observed receipt")
        _terminal_receipt(
            receipt_path,
            attempt,
            status="completed",
            returncode=returncode,
            caught_signal=None,
            final_message=final_message,
            error=None,
            required_observed_sha256=bound_receipt_sha256,
        )
        print(f"[codex-lane-launcher] receipt: {receipt_path}", file=sys.stderr)
        return 0
    except (LaunchError, OSError) as exc:
        returncode: int | None = process.poll() if process is not None else None
        if process is not None and returncode is None:
            try:
                returncode = _terminate_process_group(process, termination_grace)
            except LaunchError as termination_error:
                exc = LaunchError(f"{exc}; {termination_error}")
        _terminal_receipt(
            receipt_path,
            attempt,
            status="failed",
            returncode=returncode,
            caught_signal=caught[0] if caught else None,
            final_message=final_message,
            error=str(exc),
        )
        return 70
    finally:
        for descriptor in (
            ready_read,
            ready_write,
            ack_read,
            ack_write,
            authority_read,
            authority_write,
        ):
            if descriptor >= 0:
                with contextlib.suppress(OSError):
                    os.close(descriptor)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="internal")
    child = subparsers.add_parser("_child", help=argparse.SUPPRESS)
    child.add_argument("--descriptor", required=True)
    child.add_argument("--attempt", required=True)
    child.add_argument("--receipt", required=True)
    child.add_argument("--final-message", required=True)
    child.add_argument("--descriptor-id", required=True)
    child.add_argument("--task-sha256", required=True)
    child.add_argument("--combined-prompt-sha256", required=True)
    child.add_argument("--authority-fd", required=True, type=int)
    child.add_argument("--ready-fd", required=True, type=int)
    child.add_argument("--ack-fd", required=True, type=int)
    parser.add_argument("--descriptor")
    parser.add_argument("--prompt-file")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.internal == "_child":
            return _child_main(arguments)
        if not arguments.descriptor or not arguments.prompt_file:
            raise LaunchError("--descriptor and --prompt-file are required")
        return launch(Path(arguments.descriptor), Path(arguments.prompt_file))
    except LaunchError as exc:
        print(f"[codex-lane-launcher] error: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
