#!/usr/bin/env python3
"""Launch one headless lane (Codex or Claude) from a one-shot dev-session descriptor.

The public path validates the durable descriptor, scrubs inherited lane and
repository identity, starts a child observer in the intended worktree, and does
not acknowledge a successful launch until the child's independent observation is
durably bound to the descriptor and process.  The observer then ``exec``s the
runtime's config-selected headless command without changing PID.

The descriptor's ``runtime`` selects a config-owned template under ``parallel``:
``<runtime>_headless_command`` plus three declared transports.  The engine owns the
transport vocabulary and the argv each one produces; a declaration the runtime does
not implement refuses before launch, so config cannot make Claude read its prompt
from an argument or make Codex report through stdout.
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
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, BinaryIO

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
        "PWD",
        "OLDPWD",
    }
)
PROCESS_LINEAGE_ENV = "ADK_LAUNCH_PROCESS_NONCE"
# The runtimes this bounded mechanism supports, and the transports each one
# implements. Config DECLARES a transport per runtime (`parallel.<runtime>_*`); the
# engine validates the declaration against this table and assembles the argv. The
# Codex triple reproduces the #609 argv byte for byte; the Claude triple is what
# `claude -p` documents: cwd from the process, prompt on stdin, one JSON result
# object on stdout under `--output-format json`.
SUPPORTED_RUNTIMES = ("codex", "claude")
RUNTIME_TRANSPORTS: dict[str, dict[str, tuple[str, ...]]] = {
    "codex": {
        "worktree": ("cd-flag",),
        "prompt": ("stdin-dash",),
        "final_text": ("last-message-file",),
    },
    "claude": {
        "worktree": ("process-cwd",),
        "prompt": ("stdin",),
        "final_text": ("json-stdout",),
    },
}
TRANSPORT_KINDS = ("worktree", "prompt", "final_text")
# Approval/sandbox policy: config DECLARES `parallel.<runtime>_approval_policy` from
# this engine-owned vocabulary and the engine emits the argv contribution. Every
# unrestricted spelling (bypassPermissions, danger-full-access, the dangerously-*
# flags, auto, manual, plan) is a deliberate non-member: no config value makes the
# wrapper widen a lane to unrestricted. The Codex contribution is validated and
# passed; its behaviour is unclaimed until a Codex writing-lane record exists.
RUNTIME_APPROVAL_POLICIES: dict[str, dict[str, tuple[str, ...]]] = {
    "codex": {
        "read-only": ("--sandbox", "read-only"),
        "workspace-write": ("--sandbox", "workspace-write"),
    },
    "claude": {
        "dont-ask": ("--permission-mode", "dontAsk"),
        "accept-edits": ("--permission-mode", "acceptEdits"),
    },
}
# The Claude trust route (design matrix, 2026-08-27): an unattended lane worktree
# is an untrusted workspace, so the branch's project settings never supply policy
# and the operator's user settings must not either. `--setting-sources ""` loads
# neither; the cockpit-owned profile passed with `--settings` is the one source.
CLAUDE_SETTING_SOURCES_ARGS = ("--setting-sources", "")
# A `Bash` allow entry is bounded only by the literal command prefix its pattern
# starts with. The validator refuses an entry with no such prefix by structure
# rather than by enumerating spellings — an enumeration is a blocklist, and the
# panel found `Bash(**)` unrestricted live at Claude Code 2.1.247 while an
# enumeration missed it. The pattern is read literally, as the runtime's own
# matcher reads it: only the entry's leading and trailing whitespace is ignored,
# and inside the parentheses a space is a character like any other. The head of
# the pattern is everything before the first wildcard, `:`, or whitespace; it must
# begin with a letter, a digit, or a path character AND contain a letter or digit,
# so a lone path character in front of a wildcard (`Bash(/*)`, which matches every
# absolute-path command, `Bash(.*)`, `Bash(~*)`, `Bash(. rm*)`) is refused along
# with `Bash`, `Bash()`, `Bash(*)`, `Bash(**)`, `Bash(?*)`, `Bash(:*)`, and
# `Bash( * )`. After `Bash`, only a letter or digit (another tool's name, such as
# `BashOutput`) or a well-formed `(...)` is a rule shape this guard can read;
# anything else — `Bash (*)`, `Bash:*`, `Bash*`, `Bash{` — is refused as
# malformed rather than read as harmless. What the guard does NOT judge is the command the
# prefix names: `Bash(sh:*)` or `Bash(python3 -c:*)` is a literal prefix an
# adopter declared, and declaring it is their policy decision, not a widening
# this check claims to catch.
LITERAL_COMMAND_LEAD = frozenset("/._~")
PATTERN_HEAD_TERMINATORS = frozenset("*?:")
# File editing is bounded only by a path pattern the runtime resolves relative to
# the worktree root, and at Claude Code 2.1.247 the `Edit(<pattern>)` rule is the
# one that governs every file-editing tool: `Edit(**)` alone let a Write land
# inside the worktree and refused `../x` and `/abs/x`, `Edit(notes/**)` confined
# it to `notes/`, and `Write(**)` alone granted nothing (all observed live by the
# panel). A bare `Edit` edits anywhere. So a bare entry for any of the four names,
# a pattern rooted outside the worktree by its lead (`//…` filesystem-absolute,
# `~…` home), or a `..` segment anywhere is a declared escape refused by that
# structure — for `Write`/`MultiEdit`/`NotebookEdit` as well, because an entry the
# client ignores today may be honoured by another. A single leading `/` anchors a
# pattern at the worktree root (`Edit(/notes/**)`) and is accepted; what a
# pattern's text does not show — a symlink inside the worktree pointing out, say —
# is the runtime's own path resolution, which the panel observed refusing such
# writes live. Today this guard is a backstop behind that resolution, not the only
# boundary.
EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
# `//` filesystem-absolute, `~` home, and a backslash lead (`\\server\\share`,
# the UNC spelling of absolute on the platform that uses it; a literal
# character on this POSIX-only kit, refused rather than left unscoped).
OUTSIDE_WORKTREE_PATTERN_LEADS = ("//", "~", "\\")
# The only keys a lane profile's `permissions` object may carry: the three rule
# lists the validator inspects. The order is the order the refusal names them in.
# Anything else is refused rather than passed through — `defaultMode` would be a
# second authority for the config-declared mode, `additionalDirectories` (the
# settings form of `--add-dir`) widens tool access beyond the worktree with no
# rule in any list, and a key this client ignores may be honoured by another.
# Structural again: a closed set of accepted keys, not a list of known-widening
# spellings (panel round 14, adversarial lens).
PERMISSION_RULE_LISTS = ("allow", "deny", "ask")


def _edit_allow_escapes_the_worktree(entry: str) -> bool:
    """True when a `permissions.allow` entry grants an edit tool beyond the worktree."""
    spelling = entry.strip()
    if spelling in EDIT_TOOLS:
        return True
    for tool in EDIT_TOOLS:
        if spelling.startswith(tool) and not spelling[len(tool) :][:1].isalnum():
            rest = spelling[len(tool) :]
            if not (rest.startswith("(") and rest.endswith(")")):
                return True
            pattern = rest[1:-1].strip()
            if pattern == "" or pattern.startswith(OUTSIDE_WORKTREE_PATTERN_LEADS):
                return True
            # A drive-letter lead (`C:/…`, `C:\…`) is absolute on the one platform
            # that spells it so; this kit is POSIX-only, and the shape is refused
            # rather than left to a claim the comment never scoped (panel round 10).
            if pattern[:1].isalpha() and pattern[1:2] == ":" and pattern[2:3] in "/\\":
                return True
            return any(segment == ".." for segment in pattern.replace("\\", "/").split("/"))
    return False


def _bash_allow_has_no_literal_prefix(entry: str) -> bool:
    """True when a `permissions.allow` entry grants Bash without a command prefix."""
    spelling = entry.strip()
    if spelling == "Bash":
        return True
    if not spelling.startswith("Bash"):
        return False
    rest = spelling[len("Bash") :]
    if not (rest.startswith("(") and rest.endswith(")")):
        # `BashOutput` is another tool's name and outside this guard's claim;
        # `Bash (*)`, `Bash:*`, `Bash*`, `Bash{`, `Bash(` are Bash rule shapes the
        # runtime would not parse, refused rather than read as harmless.
        return not rest[:1].isalnum()
    pattern = rest[1:-1]
    lead = pattern[:1]
    if not (lead.isalnum() or lead in LITERAL_COMMAND_LEAD):
        return True
    head = ""
    for character in pattern:
        if character in PATTERN_HEAD_TERMINATORS or character.isspace():
            break
        head += character
    return not any(character.isalnum() for character in head)
SAFE_EXECUTABLE_PATH = os.pathsep.join(
    (*os.defpath.split(os.pathsep), "/opt/homebrew/bin", "/usr/local/bin", "/opt/local/bin")
)
TRUSTED_GIT = shutil.which("git", path=os.defpath)
TRUSTED_BASH = shutil.which("bash", path=os.defpath)
TRUSTED_PS = shutil.which("ps", path=os.defpath)


def _is_repository_override_key(key: str) -> bool:
    return key in REPOSITORY_OVERRIDE_KEYS or key.startswith("GIT_")


class LaunchError(RuntimeError):
    """A fail-closed launcher refusal."""


class RuntimeProfile:
    """One runtime's config-owned headless template, validated and resolved."""

    def __init__(
        self,
        runtime: str,
        command: list[str],
        transports: dict[str, str],
        approval: dict[str, Any],
    ) -> None:
        self.runtime = runtime
        self.command = command
        self.transports = transports
        # {"declared", "argv", "settings_profile_path", "settings_profile_sha256"}:
        # the declared policy, the exact argv it produces, and the trust-route
        # profile the argv names (Claude) — bound into the request by both sides.
        self.approval = approval

    def child_argv(self, worktree: str, final_message: str) -> list[str]:
        # Fixed order: command prefix, approval contribution, worktree, final text,
        # prompt. For Codex this is the #609 argv with `--sandbox <policy>` in the
        # second slot; for Claude it is `claude -p --setting-sources "" --permission-mode
        # <mode> --settings <profile> --output-format json`.
        approval_args = list(self.approval["argv"])
        worktree_args = (
            ["--cd", worktree] if self.transports["worktree"] == "cd-flag" else []
        )
        if self.transports["final_text"] == "last-message-file":
            final_args = ["--output-last-message", final_message]
        else:
            final_args = ["--output-format", "json"]
        prompt_args = ["-"] if self.transports["prompt"] == "stdin-dash" else []
        return [*self.command, *approval_args, *worktree_args, *final_args, *prompt_args]


class _ForkedChild:
    """Minimal wait/poll surface for the fork-only observer process."""

    def __init__(self, pid: int, stdin: BinaryIO) -> None:
        self.pid = pid
        self.stdin = stdin
        self.returncode: int | None = None

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode
        waited, status = os.waitpid(self.pid, os.WNOHANG)
        if waited == self.pid:
            self.returncode = os.waitstatus_to_exitcode(status)
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(["forked lane observer"], timeout)
            time.sleep(0.02)
        assert self.returncode is not None
        return self.returncode


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


def _reserve_empty_regular_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
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
    if descriptor.get("runtime") not in SUPPORTED_RUNTIMES:
        raise LaunchError("descriptor runtime is not a supported headless runtime")
    expected_env = {
        "DEVKIT_STATE_ROOT": descriptor.get("state_root"),
        "DEVKIT_ROOT": descriptor.get("repo_root"),
        "DEVKIT_REFUSE_UNSANDBOXED_STATE": "1",
    }
    if env != expected_env:
        raise LaunchError("descriptor environment disagrees with lane identity")
    authority_path = session_dir / "launch-authority.json"
    authority_raw = _read_stable_regular_file(authority_path)
    try:
        authority = json.loads(authority_raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LaunchError("launch authority is not valid JSON") from exc
    if not isinstance(authority, dict) or _canonical_json(authority) != authority_raw:
        raise LaunchError("launch authority is not canonical")
    if authority != {
        "schema_version": SCHEMA_VERSION,
        "descriptor_id": descriptor_id,
        "descriptor_sha256": _sha256(raw),
    }:
        raise LaunchError("descriptor disagrees with issuer-created launch authority")
    return descriptor, raw


def _config_for_launcher(runtime: str) -> tuple[RuntimeProfile, int, int, int, Path]:
    if runtime not in SUPPORTED_RUNTIMES:
        raise LaunchError("descriptor runtime is not a supported headless runtime")
    root = repo_root(SCRIPT_DIR)
    config = load_config(root / "config" / "dev-model.yaml")
    command = get(config, f"parallel.{runtime}_headless_command", None)
    timeout = get(config, "parallel.observation_timeout_seconds", None)
    lifetime = get(config, "parallel.descriptor_ttl_seconds", None)
    termination_grace = get(config, "parallel.termination_grace_seconds", None)
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        raise LaunchError(
            f"config parallel.{runtime}_headless_command must be a non-empty argv sequence"
        )
    transports: dict[str, str] = {}
    for kind in TRANSPORT_KINDS:
        key = f"parallel.{runtime}_{kind}_transport"
        declared = get(config, key, None)
        if not isinstance(declared, str) or declared not in RUNTIME_TRANSPORTS[runtime][kind]:
            raise LaunchError(
                f"config {key} must declare one of "
                f"{', '.join(RUNTIME_TRANSPORTS[runtime][kind])}"
            )
        transports[kind] = declared
    approval = _approval_for_runtime(runtime, config, root)
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
    executable = command[0]
    resolved_executable = (
        str(Path(executable).resolve())
        if Path(executable).is_absolute()
        else shutil.which(executable, path=SAFE_EXECUTABLE_PATH)
    )
    if not resolved_executable or not os.access(resolved_executable, os.X_OK):
        raise LaunchError(
            f"configured {runtime} launcher is unavailable on the trusted path"
        )
    return (
        RuntimeProfile(runtime, [resolved_executable, *command[1:]], transports, approval),
        timeout,
        lifetime,
        termination_grace,
        root.resolve(),
    )


def _validate_settings_profile(raw: bytes, path: Path) -> None:
    """Refuse a lane settings profile whose `permissions` object is not bounded.

    The `permissions` object carries the three rule lists (`allow`, `deny`,
    `ask`) and nothing else. The mode is config-declared and passed as
    `--permission-mode`, so a profile carrying `permissions.defaultMode` would be
    a second authority for the same decision; `permissions.additionalDirectories`
    is the settings form of `--add-dir` and widens tool access beyond the worktree
    with no rule in any list; and a key the wrapper does not recognise is refused
    rather than passed through, because an entry this client ignores may be
    honoured by another (panel round 14, adversarial lens). A `Bash` entry in
    `permissions.allow` with no literal command prefix would widen the lane to
    unrestricted shell without any declaration. All of these refuse before an
    attempt record exists. Only `allow` is inspected for widening among the lists:
    a `deny` entry narrows, and an `ask` entry cannot widen an unattended `-p`
    lane, where a call that would prompt is a denial the wrapper reads back from
    `permission_denials`. An edit-tool entry (`Edit`, `Write`, `MultiEdit`,
    `NotebookEdit`) must carry a path pattern relative to the worktree root; a
    bare tool name writes anywhere and a pattern rooted outside the worktree is a
    declared escape, both refused. The checks are structural (see
    `_bash_allow_has_no_literal_prefix` and `_edit_allow_escapes_the_worktree`),
    not lists of known-bad spellings, and they judge the shape of a prefix or
    pattern, never the command it names. Other top-level
    keys (`hooks`, `env`, …) are the profile owner's and pass through: the profile
    is cockpit-owned by design, and its hooks are meant to run in the lane.
    """
    try:
        profile = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LaunchError(f"lane settings profile {path} is not valid JSON") from exc
    if not isinstance(profile, dict):
        raise LaunchError(f"lane settings profile {path} must be one JSON object")
    permissions = profile.get("permissions")
    if not isinstance(permissions, dict):
        raise LaunchError(f"lane settings profile {path} must declare a permissions object")
    if "defaultMode" in permissions:
        raise LaunchError(
            f"lane settings profile {path} must not declare permissions.defaultMode; "
            "the mode is config-declared through parallel.claude_approval_policy"
        )
    for key in permissions:
        if key not in PERMISSION_RULE_LISTS:
            raise LaunchError(
                f"lane settings profile {path} must not declare permissions.{key}; "
                f"a lane profile's permissions object carries only "
                f"{', '.join(PERMISSION_RULE_LISTS)} (additionalDirectories widens "
                "tool access beyond the worktree, and an unrecognised key is refused "
                "rather than passed through)"
            )
    for key in PERMISSION_RULE_LISTS:
        entries = permissions.get(key, [])
        if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
            raise LaunchError(f"lane settings profile {path} permissions.{key} must be a list of strings")
    for entry in permissions.get("allow", []):
        if _bash_allow_has_no_literal_prefix(entry):
            raise LaunchError(
                f"lane settings profile {path} widens Bash to unrestricted ({entry!r}: "
                "no literal command prefix); declare each command prefix instead"
            )
        if _edit_allow_escapes_the_worktree(entry):
            raise LaunchError(
                f"lane settings profile {path} grants an edit tool beyond the worktree "
                f"({entry!r}); scope it with a pattern relative to the worktree root, "
                "such as Write(**)"
            )


def _approval_for_runtime(runtime: str, config: dict[str, Any], root: Path) -> dict[str, Any]:
    key = f"parallel.{runtime}_approval_policy"
    declared = get(config, key, None)
    vocabulary = RUNTIME_APPROVAL_POLICIES[runtime]
    if not isinstance(declared, str) or declared not in vocabulary:
        raise LaunchError(f"config {key} must declare one of {', '.join(vocabulary)}")
    contribution = list(vocabulary[declared])
    profile_path: str | None = None
    profile_sha256: str | None = None
    if runtime == "claude":
        profile_key = "parallel.claude_settings_profile"
        configured = get(config, profile_key, None)
        if not isinstance(configured, str) or not configured:
            raise LaunchError(f"config {profile_key} must name the lane settings profile")
        candidate = Path(configured)
        if not candidate.is_absolute():
            candidate = root / candidate
        if candidate.is_symlink() or not candidate.is_file():
            raise LaunchError(f"lane settings profile {candidate} is not a regular file")
        raw = _read_stable_regular_file(candidate)
        _validate_settings_profile(raw, candidate)
        profile_path = str(candidate.resolve())
        profile_sha256 = _sha256(raw)
        contribution = [*CLAUDE_SETTING_SOURCES_ARGS, *contribution, "--settings", profile_path]
    return {
        "declared": declared,
        "argv": contribution,
        "settings_profile_path": profile_path,
        "settings_profile_sha256": profile_sha256,
    }


def _git(cwd: Path, *args: str) -> str:
    if TRUSTED_GIT is None:
        raise LaunchError("trusted system Git is unavailable")
    try:
        result = subprocess.run(
            [TRUSTED_GIT, *args], cwd=cwd, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LaunchError(f"git observation failed for {' '.join(args)}") from exc
    return result.stdout.strip()


def _validate_descriptor_contract(descriptor: dict[str, Any], config_root: Path) -> None:
    if TRUSTED_BASH is None:
        raise LaunchError("trusted system Bash is unavailable")
    issuer = SCRIPT_DIR / "dev_session.sh"
    _read_stable_regular_file(issuer)
    try:
        result = subprocess.run(
            [TRUSTED_BASH, str(issuer), "print-contract"],
            cwd=config_root,
            env={
                **{
                    key: value
                    for key, value in os.environ.items()
                    if not key.startswith("DEVKIT_")
                    and not _is_repository_override_key(key)
                    and key != "PATH"
                },
                "PATH": SAFE_EXECUTABLE_PATH,
            },
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LaunchError("cannot derive the canonical lane contract from the issuer") from exc
    canonical = result.stdout.rstrip("\n")
    if not canonical or descriptor.get("prompt_preamble") != canonical:
        raise LaunchError("descriptor prompt preamble disagrees with the canonical issuer")


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


def _processes_with_launch_nonce(process_nonce: str) -> dict[int, str]:
    marker = f"{PROCESS_LINEAGE_ENV}={process_nonce}"
    matches: dict[int, str] = {}
    proc_root = Path("/proc")
    if proc_root.is_dir():
        for candidate in proc_root.iterdir():
            if not candidate.name.isdecimal():
                continue
            try:
                environment = (candidate / "environ").read_bytes().split(b"\0")
            except (OSError, PermissionError):
                continue
            if marker.encode() not in environment:
                continue
            pid = int(candidate.name)
            fingerprint = _process_start_fingerprint(pid)
            if fingerprint is None:
                raise LaunchError("cannot bind a launch-lineage process identity")
            matches[pid] = fingerprint
        return matches
    if TRUSTED_PS is None:
        raise LaunchError("trusted process observer is unavailable")
    try:
        result = subprocess.run(
            [TRUSTED_PS, "eww", "-axo", "pid=,command="],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LaunchError("cannot observe the launch process lineage") from exc
    for line in result.stdout.splitlines():
        pid_text, separator, payload = line.lstrip().partition(" ")
        if not separator or marker not in payload:
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        fingerprint = _process_start_fingerprint(pid)
        if fingerprint is None:
            raise LaunchError("cannot bind a launch-lineage process identity")
        matches[pid] = fingerprint
    return matches


def _close_nonstandard_descriptors() -> None:
    for descriptor_root in (Path("/proc/self/fd"), Path("/dev/fd")):
        if not descriptor_root.is_dir():
            continue
        try:
            descriptors = [
                int(candidate.name)
                for candidate in descriptor_root.iterdir()
                if candidate.name.isdecimal() and int(candidate.name) > 2
            ]
        except OSError:
            continue
        for descriptor in descriptors:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        return
    raise LaunchError("cannot enumerate inherited file descriptors before runtime exec")


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
        "origin_push_url": _git(cwd, "remote", "get-url", "--push", "origin"),
        "branch": branch,
        "persisted_branch": persisted_branch,
        "base": persisted_base,
        "base_oid": base_oid,
        "lane_oid": lane_oid,
        "merge_class": merge_class,
        "environment": devkit_env,
        "pwd_environment": os.environ.get("PWD"),
        "repository_overrides_present": sorted(
            key
            for key in os.environ
            if key != "PWD" and _is_repository_override_key(key)
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
            "origin_push_url",
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
        "origin_push_url",
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


def _request_binding(
    descriptor_raw: bytes,
    *,
    task_sha256: str,
    combined_prompt_sha256: str,
    profile: RuntimeProfile,
    process_nonce: str,
) -> dict[str, Any]:
    # Computed identically by parent and child; the child refuses when its own
    # config resolves to a different runtime, command, transport set, or approval
    # policy — including a settings profile whose bytes changed between the two
    # reads, since the digest is part of the binding.
    return {
        "descriptor_sha256": _sha256(descriptor_raw),
        "task_sha256": task_sha256,
        "combined_prompt_sha256": combined_prompt_sha256,
        "configured_command": list(profile.command),
        "runtime": profile.runtime,
        "transports": dict(profile.transports),
        "approval_policy": {
            "declared": profile.approval["declared"],
            "argv": list(profile.approval["argv"]),
            "settings_profile_path": profile.approval["settings_profile_path"],
            "settings_profile_sha256": profile.approval["settings_profile_sha256"],
        },
        "process_nonce_sha256": _sha256(process_nonce.encode()),
    }


def _extract_final_text(transport: str, final_bytes: bytes) -> bytes:
    """Return the runtime's final text from the reserved evidence file, or refuse."""
    return _extract_final_result(transport, final_bytes)[0]


def _extract_final_result(
    transport: str, final_bytes: bytes
) -> tuple[bytes, list[Any] | None]:
    """Return (final text, permission denials) from the reserved evidence file.

    The denial list is what makes a refused write visible: Claude's envelope stays
    `subtype=success` / `is_error=false` when a tool call is denied, and only
    `permission_denials` says so. `None` means the transport cannot observe it
    (`last-message-file`); it is never reported as an empty list.
    """
    if transport == "last-message-file":
        if not final_bytes:
            raise LaunchError("child returned success without final-message evidence")
        return final_bytes, None
    if not final_bytes:
        raise LaunchError("runtime produced no JSON result on stdout")
    try:
        text = final_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LaunchError("runtime stdout is not UTF-8 JSON") from exc
    stripped = text.strip()
    try:
        value, end = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError as exc:
        raise LaunchError(
            f"runtime stdout is not one complete JSON object: {exc.msg}"
        ) from exc
    if stripped[end:].strip():
        raise LaunchError("runtime stdout holds more than one JSON value")
    if not isinstance(value, dict):
        raise LaunchError("runtime JSON result is not an object")
    if value.get("type") != "result":
        raise LaunchError("runtime JSON is not a result object")
    if value.get("is_error") is not False or value.get("subtype") != "success":
        raise LaunchError("runtime reported an unsuccessful result")
    result = value.get("result")
    if not isinstance(result, str) or not result:
        raise LaunchError("runtime result text is missing or empty")
    denials = value.get("permission_denials")
    if not isinstance(denials, list):
        raise LaunchError("runtime result carries no permission_denials list")
    return result.encode("utf-8"), denials


def _redirect_stdout_to_reserved_final(final_message: Path) -> None:
    """Point fd 1 at the parent-reserved, still-empty final-message file."""
    flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(final_message, flags)
    except OSError as exc:
        raise LaunchError(f"cannot open reserved final-message evidence: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size != 0 or info.st_nlink != 1:
            raise LaunchError("reserved final-message evidence is not an empty regular file")
        sys.stdout.flush()
        os.dup2(descriptor, 1)
    finally:
        os.close(descriptor)


def _validate_child_authority(
    arguments: argparse.Namespace,
    descriptor: dict[str, Any],
    descriptor_raw: bytes,
    profile: RuntimeProfile,
) -> str:
    if arguments.descriptor_id != descriptor["descriptor_id"]:
        raise LaunchError("child descriptor identity disagrees with the descriptor")
    expected_attempt_path = Path(descriptor["session_dir"]) / "launch-attempt.json"
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
    expected_request = _request_binding(
        descriptor_raw,
        task_sha256=arguments.task_sha256,
        combined_prompt_sha256=arguments.combined_prompt_sha256,
        profile=profile,
        process_nonce=process_nonce,
    )
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
        profile, _timeout, _lifetime, _termination_grace, config_root = (
            _config_for_launcher(descriptor["runtime"])
        )
        if Path(descriptor["repo_root"]).resolve() != config_root:
            raise LaunchError("descriptor repository is foreign to the launcher configuration")
        _validate_descriptor_contract(descriptor, config_root)
        process_nonce = _validate_child_authority(arguments, descriptor, raw, profile)
        expected = _expected_identity(descriptor)
        observed = _observed_identity(process_nonce)
        _validate_observation(expected, observed)
        final_message = Path(arguments.final_message)
        argv = profile.child_argv(expected["worktree"], str(final_message))
        # The exact argv this observer will exec, including the approval
        # contribution, is durable before the ready signal; the parent compares it
        # against its own expectation, so a child that drops the policy or the
        # trust step cannot be acknowledged.
        observed["argv"] = list(argv)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "status": "observed",
            "descriptor_id": descriptor["descriptor_id"],
            "request": _request_binding(
                raw,
                task_sha256=arguments.task_sha256,
                combined_prompt_sha256=arguments.combined_prompt_sha256,
                profile=profile,
                process_nonce=process_nonce,
            ),
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
        os.environ[PROCESS_LINEAGE_ENV] = process_nonce
        if profile.transports["final_text"] == "json-stdout":
            # Immediately before exec, so nothing the wrapper prints can precede
            # the runtime's own JSON on the evidence file.
            _redirect_stdout_to_reserved_final(final_message)
        _close_nonstandard_descriptors()
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
        print(f"[lane-launcher] child refused: {exc}", file=sys.stderr)
        return 70


def _scrubbed_environment(descriptor: dict[str, Any]) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("DEVKIT_") and not _is_repository_override_key(key)
    }
    environment.update(descriptor["env"])
    environment["PATH"] = SAFE_EXECUTABLE_PATH
    environment["PWD"] = descriptor["worktree"]
    return environment


def _fork_observer_child(
    arguments: argparse.Namespace,
    *,
    worktree: str,
    environment: dict[str, str],
    ready_read: int,
    ack_write: int,
    authority_write: int,
) -> _ForkedChild:
    prompt_read, prompt_write = os.pipe()
    try:
        pid = os.fork()
    except OSError:
        os.close(prompt_read)
        os.close(prompt_write)
        raise
    if pid == 0:
        returncode = 70
        try:
            os.setsid()
            for signum in (signal.SIGINT, signal.SIGTERM):
                signal.signal(signum, signal.SIG_DFL)
            os.chdir(worktree)
            os.environ.clear()
            os.environ.update(environment)
            for descriptor in (ready_read, ack_write, authority_write, prompt_write):
                with contextlib.suppress(OSError):
                    os.close(descriptor)
            os.dup2(prompt_read, 0)
            os.close(prompt_read)
            returncode = _child_main(arguments)
        except BaseException as exc:  # child must terminalize without re-entering parent
            print(f"[lane-launcher] forked child failed: {exc}", file=sys.stderr)
        finally:
            with contextlib.suppress(Exception):
                sys.stdout.flush()
                sys.stderr.flush()
        os._exit(returncode)
    os.close(prompt_read)
    return _ForkedChild(pid, os.fdopen(prompt_write, "wb", buffering=0))


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
    expected_argv: list[str],
) -> None:
    observed_process = receipt.get("observed", {}).get("process", {})
    if (
        receipt.get("status") != "observed"
        or receipt.get("descriptor_id") != descriptor_id
        or receipt.get("request") != request
        or receipt.get("observed", {}).get("argv") != expected_argv
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
    final_text_transport: str,
    final_text: bytes | None,
    permission_denials: list[Any] | None,
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
        "final_text_transport": final_text_transport,
        "final_text_sha256": _sha256(final_text) if final_text else None,
        # A list is the runtime's own denial record (empty when nothing was
        # refused); None means the outcome was not observed — the transport
        # cannot expose it (`last-message-file`), or the result could not be
        # extracted at all. Never spelled `[]` in either case.
        "permission_denials": permission_denials,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_atomic(receipt_path, receipt)


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_process_group_exit(
    process: _ForkedChild, deadline: float
) -> int | None:
    while time.monotonic() < deadline:
        process.poll()
        if not _process_group_exists(process.pid):
            if process.returncode is None:
                remaining = max(0.0, deadline - time.monotonic())
                try:
                    return process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    return None
            return process.returncode
        time.sleep(0.05)
    return None


def _terminate_process_group(
    process: _ForkedChild, grace_seconds: int
) -> int:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise LaunchError("cannot signal the child process group") from exc
    returncode = _wait_for_process_group_exit(
        process, time.monotonic() + grace_seconds
    )
    if returncode is not None:
        return returncode
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise LaunchError("cannot force-stop the child process group") from exc
    returncode = _wait_for_process_group_exit(
        process, time.monotonic() + grace_seconds
    )
    if returncode is None:
        raise LaunchError("child process group survived forced termination")
    return returncode


def _terminate_launch_lineage(process_nonce: str, grace_seconds: int) -> None:
    def signal_current_lineage(signum: int, error: str) -> dict[int, str]:
        tracked = _processes_with_launch_nonce(process_nonce)
        for pid, fingerprint in tracked.items():
            current = _processes_with_launch_nonce(process_nonce)
            if (
                current.get(pid) != fingerprint
                or _process_start_fingerprint(pid) != fingerprint
            ):
                continue
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                pass
            except PermissionError as exc:
                raise LaunchError(error) from exc
        return tracked

    tracked = signal_current_lineage(
        signal.SIGTERM, "cannot signal a launch-lineage process"
    )
    deadline = time.monotonic() + grace_seconds
    while tracked and time.monotonic() < deadline:
        tracked = _processes_with_launch_nonce(process_nonce)
        if tracked:
            time.sleep(0.05)
    tracked = signal_current_lineage(
        signal.SIGKILL, "cannot force-stop a launch-lineage process"
    )
    deadline = time.monotonic() + grace_seconds
    while tracked and time.monotonic() < deadline:
        tracked = _processes_with_launch_nonce(process_nonce)
        if tracked:
            time.sleep(0.05)
    if _processes_with_launch_nonce(process_nonce):
        raise LaunchError("launch-lineage process survived forced termination")


def _wait_for_process_or_signal(
    process: _ForkedChild, caught: list[int]
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
        profile,
        observation_timeout,
        configured_lifetime,
        termination_grace,
        config_root,
    ) = _config_for_launcher(descriptor["runtime"])
    final_text_transport = profile.transports["final_text"]
    if Path(descriptor["repo_root"]).resolve() != config_root:
        raise LaunchError("descriptor repository is foreign to the launcher configuration")
    _validate_descriptor_contract(descriptor, config_root)
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
    attempt_path = session_dir / "launch-attempt.json"
    receipt_path = session_dir / f"launch-receipt-{descriptor_id}.json"
    final_message = session_dir / f"launch-final-{descriptor_id}.txt"
    request = _request_binding(
        descriptor_raw,
        task_sha256=_sha256(task),
        combined_prompt_sha256=_sha256(combined),
        profile=profile,
        process_nonce=process_nonce,
    )
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
    try:
        _reserve_empty_regular_file(final_message)
    except OSError as exc:
        _terminal_receipt(
            receipt_path,
            attempt,
            status="failed",
            returncode=None,
            caught_signal=None,
            final_message=final_message,
            error=f"cannot reserve empty final-message evidence: {exc}",
            final_text_transport=final_text_transport,
            final_text=None,
            permission_denials=None,
        )
        return 70

    ready_read, ready_write = os.pipe()
    ack_read, ack_write = os.pipe()
    authority_read, authority_write = os.pipe()
    child_arguments = argparse.Namespace(
        descriptor=str(descriptor_path),
        attempt=str(attempt_path),
        receipt=str(receipt_path),
        final_message=str(final_message),
        descriptor_id=descriptor_id,
        task_sha256=request["task_sha256"],
        combined_prompt_sha256=request["combined_prompt_sha256"],
        authority_fd=authority_read,
        ready_fd=ready_write,
        ack_fd=ack_read,
    )
    process: _ForkedChild | None = None
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
        process = _fork_observer_child(
            child_arguments,
            worktree=descriptor["worktree"],
            environment=_scrubbed_environment(descriptor),
            ready_read=ready_read,
            ack_write=ack_write,
            authority_write=authority_write,
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
                        expected_argv=profile.child_argv(
                            descriptor["worktree"], str(final_message)
                        ),
                    )
                except LaunchError:
                    error = "durable child observation or process identity is invalid"
                if error is None:
                    bound_receipt_sha256 = _sha256(_canonical_json(receipt))
                    os.write(ack_write, b"1")
                    os.close(ack_write)
                    ack_write = -1
                    process.stdin.write(combined)
                    process.stdin.close()
        returncode = None if error else _wait_for_process_or_signal(process, caught)
        if returncode is not None and _process_group_exists(process.pid):
            error = "child exited while its process group remained active"
        if (
            returncode is not None
            and error is None
            and _processes_with_launch_nonce(process_nonce)
        ):
            error = "child exited while detached launch-lineage processes remained active"
        if caught or error:
            returncode = _terminate_process_group(process, termination_grace)
            _terminate_launch_lineage(process_nonce, termination_grace)
        assert returncode is not None
        final_bytes = b""
        if final_message.is_file() and not final_message.is_symlink():
            final_bytes = _read_stable_regular_file(final_message)
        final_text: bytes | None = None
        final_text_error: str | None = None
        permission_denials: list[Any] | None = None
        try:
            final_text, permission_denials = _extract_final_result(
                final_text_transport, final_bytes
            )
        except LaunchError as exc:
            final_text_error = str(exc)
        if caught:
            _terminal_receipt(
                receipt_path,
                attempt,
                status="interrupted",
                returncode=returncode,
                caught_signal=caught[0],
                final_message=final_message,
                error="launcher interrupted",
                final_text_transport=final_text_transport,
                final_text=final_text,
                permission_denials=permission_denials,
            )
            return 128 + caught[0]
        # A denied tool call does not fail the runtime's envelope (Claude reports
        # `success` with the refusal only in `permission_denials`), so the approval
        # transition is read here, before any success is acknowledged: a lane that
        # was refused a write under the declared policy is `failed`, not `completed`.
        if error is None and returncode == 0 and final_text_error is None and permission_denials:
            error = (
                "runtime reported permission denials under declared policy "
                f"{profile.approval['declared']}"
            )
        if error is not None or returncode != 0 or final_text_error is not None:
            if error is None:
                error = (
                    f"child exited with status {returncode}"
                    if returncode != 0
                    else final_text_error
                )
            _terminal_receipt(
                receipt_path,
                attempt,
                status="failed",
                returncode=returncode,
                caught_signal=None,
                final_message=final_message,
                error=error,
                final_text_transport=final_text_transport,
                final_text=None,
                permission_denials=permission_denials,
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
            final_text_transport=final_text_transport,
            final_text=final_text,
            permission_denials=permission_denials,
            required_observed_sha256=bound_receipt_sha256,
        )
        print(f"[lane-launcher] receipt: {receipt_path}", file=sys.stderr)
        return 0
    except (LaunchError, OSError) as exc:
        returncode: int | None = process.poll() if process is not None else None
        if process is not None and _process_group_exists(process.pid):
            try:
                returncode = _terminate_process_group(process, termination_grace)
            except LaunchError as termination_error:
                exc = LaunchError(f"{exc}; {termination_error}")
        try:
            _terminate_launch_lineage(process_nonce, termination_grace)
        except LaunchError as termination_error:
            exc = LaunchError(f"{exc}; {termination_error}")
        _terminal_receipt(
            receipt_path,
            attempt,
            status="interrupted" if caught else "failed",
            returncode=returncode,
            caught_signal=caught[0] if caught else None,
            final_message=final_message,
            error="launcher interrupted" if caught else str(exc),
            final_text_transport=final_text_transport,
            final_text=None,
            permission_denials=None,
        )
        return 128 + caught[0] if caught else 70
    finally:
        if process is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
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
    parser.add_argument("--descriptor")
    parser.add_argument("--prompt-file")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if not arguments.descriptor or not arguments.prompt_file:
            raise LaunchError("--descriptor and --prompt-file are required")
        return launch(Path(arguments.descriptor), Path(arguments.prompt_file))
    except LaunchError as exc:
        print(f"[lane-launcher] error: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
