"""Complete-record exclusive single-writer gate."""

from __future__ import annotations

import ctypes
import os
import platform
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import CanonicalError, digest, digest_bytes, dumps, loads_exact
from .model import TOKEN_RE, TriageError
from .storage import ArtifactStore, exclusive_create, observe, unlink_inode

GATE_CORE_KEYS = {
    "repository_identity", "config_fingerprint", "owner_token",
    "owner_run_identity", "host", "process_id", "process_start", "created_at_ns",
}


def validate_record(
    record: Any,
    *,
    repository_identity: dict[str, Any] | None = None,
    config_fingerprint: str | None = None,
) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != {"kind", "schema_version", "gate_claim_core", "gate_claim_core_digest", *GATE_CORE_KEYS}:
        raise TriageError("gate owner record has the wrong shape", outcome="operator-held")
    core = record.get("gate_claim_core")
    if (
        record.get("kind") != "triage-gate"
        or isinstance(record.get("schema_version"), bool)
        or record.get("schema_version") != 1
        or not isinstance(core, dict)
        or set(core) != GATE_CORE_KEYS
    ):
        raise TriageError("gate owner record has the wrong shape", outcome="operator-held")
    if digest(core) != record.get("gate_claim_core_digest") or any(record.get(name) != core.get(name) for name in GATE_CORE_KEYS):
        raise TriageError("gate owner record core binding mismatch", outcome="operator-held")
    pid = core["process_id"]
    start = core["process_start"]
    if not isinstance(core["owner_token"], str) or not TOKEN_RE.fullmatch(core["owner_token"]) or isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise TriageError("gate owner identity is malformed", outcome="operator-held")
    if not isinstance(start, str) or not start.startswith(("linux-proc-ticks:", "darwin-bsd-time:", "ps-lstart:")):
        raise TriageError("gate process-start identity is malformed", outcome="operator-held")
    if not isinstance(core["host"], str) or not core["host"] or not isinstance(core["created_at_ns"], str) or not core["created_at_ns"].isdigit():
        raise TriageError("gate owner metadata is malformed", outcome="operator-held")
    if core["owner_run_identity"] is not None and not isinstance(core["owner_run_identity"], dict):
        raise TriageError("gate run identity is malformed", outcome="operator-held")
    if repository_identity is not None and core["repository_identity"] != repository_identity:
        raise TriageError("gate repository identity is foreign", outcome="operator-held")
    if config_fingerprint is not None and core["config_fingerprint"] != config_fingerprint:
        raise TriageError("gate configuration identity is foreign", outcome="operator-held")
    return record


def _process_start(pid: int) -> str | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        # The comm field is parenthesized and may contain spaces. Fields after
        # its final ')' begin at process-stat field 3; starttime is field 22.
        remainder = raw[raw.rfind(")") + 2 :].split()
        return f"linux-proc-ticks:{remainder[19]}"
    except (OSError, IndexError, UnicodeError):
        pass
    if platform.system() == "Darwin":
        class ProcBSDInfo(ctypes.Structure):
            _fields_ = [
                ("flags", ctypes.c_uint32), ("status", ctypes.c_uint32),
                ("xstatus", ctypes.c_uint32), ("pid", ctypes.c_uint32),
                ("ppid", ctypes.c_uint32), ("uid", ctypes.c_uint32),
                ("gid", ctypes.c_uint32), ("ruid", ctypes.c_uint32),
                ("rgid", ctypes.c_uint32), ("svuid", ctypes.c_uint32),
                ("svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32),
                ("nfiles", ctypes.c_uint32), ("pgid", ctypes.c_uint32),
                ("pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                ("e_tpgid", ctypes.c_uint32), ("nice", ctypes.c_int32),
                ("start_tvsec", ctypes.c_uint64), ("start_tvusec", ctypes.c_uint64),
            ]

        info = ProcBSDInfo()
        try:
            read = ctypes.CDLL("/usr/lib/libproc.dylib").proc_pidinfo(
                pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info)
            )
        except (OSError, AttributeError):
            read = 0
        if read == ctypes.sizeof(info) and info.start_tvsec:
            return f"darwin-bsd-time:{info.start_tvsec}:{info.start_tvusec}"
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    observed = result.stdout.strip()
    return f"ps-lstart:{observed}" if result.returncode == 0 and observed else None


def _cleanup_orphaned_temporaries(
    store: ArtifactStore,
    *,
    repository_identity: dict[str, Any],
    config_fingerprint: str,
) -> None:
    gate = store.gate_path
    _, published = observe(gate, allow_links=True)
    if published is not None:
        return
    prefix = f".{gate.name}."
    suffix = ".tmp"
    for candidate in gate.parent.iterdir():
        if not candidate.name.startswith(prefix) or not candidate.name.endswith(suffix):
            continue
        token = candidate.name[len(prefix) : -len(suffix)]
        observation, raw = observe(candidate, allow_links=True)
        if raw is None:
            continue
        try:
            record = loads_exact(raw)
        except CanonicalError as exc:
            raise TriageError("orphaned gate temporary is malformed", outcome="operator-held") from exc
        validate_record(
            record,
            repository_identity=repository_identity,
            config_fingerprint=config_fingerprint,
        )
        if record.get("owner_token") != token or observation.links != 1:
            raise TriageError("orphaned gate temporary identity is ambiguous", outcome="operator-held")
        if owner_status(record) != "terminated":
            raise TriageError("gate publication is active or uncertain", outcome="operator-held")
        unlink_inode(candidate, observation, raw, allow_links=True)


@dataclass
class GateLease:
    store: ArtifactStore
    owner_token: str
    record: dict[str, Any]
    binding: dict[str, Any]
    gate_digest: str
    held: bool = True

    def verify(self) -> bytes:
        observation, raw = observe(self.store.gate_path, allow_links=True)
        if raw is None:
            raise TriageError("owned gate disappeared", outcome="operator-held")
        try:
            parsed = loads_exact(raw)
        except CanonicalError as exc:
            raise TriageError("owned gate changed", outcome="operator-held") from exc
        validate_record(parsed)
        if parsed != self.record or parsed.get("owner_token") != self.owner_token:
            raise TriageError("owned gate changed", outcome="operator-held")
        if observation.digest != self.gate_digest:
            raise TriageError("gate digest mismatch", outcome="operator-held")
        return raw

    def release(self) -> None:
        raw = self.verify()
        observation, repeated = observe(self.store.gate_path)
        if repeated != raw:
            raise TriageError("owned gate changed before release", outcome="operator-held")
        unlink_inode(self.store.gate_path, observation, raw)
        self.held = False


def acquire(store: ArtifactStore, *, repository_identity: dict[str, Any], config_fingerprint: str, run_identity: dict[str, Any] | None) -> GateLease:
    gate = store.gate_path
    gate.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_orphaned_temporaries(
        store,
        repository_identity=repository_identity,
        config_fingerprint=config_fingerprint,
    )
    token = uuid.uuid4().hex
    if not TOKEN_RE.fullmatch(token):
        raise AssertionError("generated owner token violated grammar")
    process_start = _process_start(os.getpid())
    if process_start is None:
        raise TriageError("current process start identity is unavailable", outcome="operator-held")
    core = {
        "repository_identity": repository_identity,
        "config_fingerprint": config_fingerprint,
        "owner_token": token,
        "owner_run_identity": run_identity,
        "host": socket.gethostname(),
        "process_id": os.getpid(),
        "process_start": process_start,
        "created_at_ns": str(time.time_ns()),
    }
    record = {"kind": "triage-gate", "schema_version": 1, "gate_claim_core": core, "gate_claim_core_digest": digest(core), **core}
    raw = dumps(record)
    try:
        exclusive_create(gate, raw, temporary_name=f".{gate.name}.{token}.tmp")
    except FileExistsError as exc:
        raise TriageError("single-writer gate is already held", outcome="operator-held") from exc
    binding = {
        "gate_path": str(gate),
        "owner_token": token,
        "owner_run_identity": run_identity,
        "gate_claim_core_digest": record["gate_claim_core_digest"],
    }
    return GateLease(store, token, record, binding, digest_bytes(raw))


def owner_status(record: dict[str, Any]) -> str:
    if record.get("host") != socket.gethostname():
        return "uncertain"
    pid = record.get("process_id")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return "uncertain"
    recorded_start = record.get("process_start")
    if not isinstance(recorded_start, str) or not recorded_start:
        return "uncertain"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "terminated"
    except PermissionError:
        return "uncertain"
    current_start = _process_start(pid)
    if current_start is None or recorded_start != current_start:
        return "uncertain"
    return "active"
