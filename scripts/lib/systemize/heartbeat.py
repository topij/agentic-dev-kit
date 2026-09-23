"""Local heartbeat state for an engine-backed systemize run.

``start`` precedes the fetch, ``tick`` marks the durable digest and each
analysis slice, and ``complete`` is the run's final write. The state file is
bound to the pre-forge heartbeat identity (the run identity does not exist
until the fetch reads the protected-branch head); ``tick --run-identity-digest``
records the run identity once known and it may not change afterwards.

Each invocation is one locked read-modify-write. A concurrent writer is refused
rather than allowed to lose an update, and every out-of-order transition is a
hard stop so a caller can never mark an incomplete run complete by accident.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from triage.canonical import dumps

from . import artifacts, identity
from .config import Settings
from .errors import SystemizeError
from .fetch import all_targets

REASONS = ("complete", "error")
_STEP = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")
_SLICE = re.compile(r"([1-9][0-9]*)/([1-9][0-9]*)")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def _locked(target: artifacts.Target) -> Iterator[None]:
    lock = lock_path(target)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    except FileExistsError as exc:
        raise SystemizeError(
            f"heartbeat lock {lock} is held: another writer is running, or one died mid-write; "
            "confirm no systemize process is running, then remove the lock"
        ) from exc
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        with suppress(FileNotFoundError):
            os.unlink(lock)


class Heartbeat:
    def __init__(self, settings: Settings, *, mode: str, window_days: int, date: str) -> None:
        if settings.engine_mode != "engine-backed" or settings.heartbeat_pattern is None:
            raise SystemizeError("heartbeat requires the complete engine set and systemize.heartbeat_pattern")
        window_days = settings.window_days_for(window_days)
        self.settings = settings
        self.identity = identity.heartbeat_identity(
            job=settings.heartbeat_job or "", window_days=window_days, date=date,
            fingerprint=settings.fingerprint, mode=mode,
        )
        self.targets = all_targets(settings, date=date, window_days=window_days, mode=mode)
        self.target = next(t for t in self.targets if t.label == "heartbeat")

    def _read(self) -> dict[str, Any] | None:
        if not os.path.lexists(self.target.path):
            return None
        raw = artifacts.read_regular(self.target.path, "heartbeat")
        identity.require_same_run(raw, kind=identity.HEARTBEAT_KIND, identity=self.identity, path=str(self.target.path))
        return identity.parse_artifact(raw, str(self.target.path))

    def _write(self, state: dict[str, Any]) -> dict[str, Any]:
        artifacts.check_targets(self.settings, self.targets)
        artifacts.publish(self.target, dumps(state))
        return {"engine": "heartbeat", "heartbeat_path": str(self.target.path), "status": state["status"],
                "current_step": state["current_step"]}

    def _running(self) -> dict[str, Any]:
        state = self._read()
        if state is None:
            raise SystemizeError(f"no heartbeat started at {self.target.path}; run `start` first")
        if state.get("status") != "running":
            raise SystemizeError(f"heartbeat at {self.target.path} is already {state.get('status')}; no further ticks")
        return state

    def start(self) -> dict[str, Any]:
        artifacts.check_targets(self.settings, self.targets)
        with _locked(self.target):
            previous = self._read()
            now = _now()
            state = {
                **identity.header(identity.HEARTBEAT_KIND, self.identity),
                "job": self.settings.heartbeat_job,
                "status": "running",
                "exit_reason": None,
                "started_at": now,
                "updated_at": now,
                "restarts": 0 if previous is None else int(previous.get("restarts") or 0) + 1,
                "systemize_run_identity_digest": None,
                "current_step": "start",
                "slice": None,
                "steps": [{"step": "start", "slice": None, "at": now}],
            }
            return self._write(state)

    def tick(self, step: str, slice_text: str | None, run_digest: str | None) -> dict[str, Any]:
        if not _STEP.fullmatch(step or ""):
            raise SystemizeError(f"invalid heartbeat step {step!r}")
        current: dict[str, int] | None = None
        if slice_text is not None:
            match = _SLICE.fullmatch(slice_text)
            if not match or int(match.group(1)) > int(match.group(2)):
                raise SystemizeError(f"invalid --slice {slice_text!r}; expected i/n with 1 <= i <= n")
            current = {"index": int(match.group(1)), "total": int(match.group(2))}
        if run_digest is not None and not _DIGEST.fullmatch(run_digest):
            raise SystemizeError(f"invalid --run-identity-digest {run_digest!r}")
        artifacts.check_targets(self.settings, self.targets)
        with _locked(self.target):
            state = self._running()
            prior = state.get("slice")
            if current is not None and isinstance(prior, dict):
                if prior.get("total") != current["total"]:
                    raise SystemizeError(f"slice total changed from {prior.get('total')} to {current['total']}")
                if current["index"] < prior.get("index", 0):
                    raise SystemizeError(f"slice regressed from {prior.get('index')} to {current['index']}")
            recorded = state.get("systemize_run_identity_digest")
            if run_digest is not None:
                if recorded not in (None, run_digest):
                    raise SystemizeError("run identity digest differs from the one this heartbeat already recorded")
                state["systemize_run_identity_digest"] = run_digest
            now = _now()
            state["current_step"] = step
            if current is not None:
                state["slice"] = current
            state["updated_at"] = now
            state["steps"] = [*state.get("steps", []), {"step": step, "slice": current, "at": now}]
            return self._write(state)

    def complete(self, reason: str) -> dict[str, Any]:
        if reason not in REASONS:
            raise SystemizeError(f"invalid completion reason {reason!r}")
        artifacts.check_targets(self.settings, self.targets)
        with _locked(self.target):
            state = self._read()
            if state is None:
                raise SystemizeError(f"no heartbeat started at {self.target.path}; nothing to complete")
            if state.get("status") == "complete":
                if state.get("exit_reason") == reason:
                    return {"engine": "heartbeat", "heartbeat_path": str(self.target.path),
                            "status": "complete", "current_step": state.get("current_step")}
                raise SystemizeError(
                    f"heartbeat already completed with reason {state.get('exit_reason')!r}; refusing {reason!r}"
                )
            now = _now()
            state.update(status="complete", exit_reason=reason, current_step="done", updated_at=now)
            state["steps"] = [*state.get("steps", []), {"step": "done", "slice": None, "at": now}]
            return self._write(state)


def lock_path(target: artifacts.Target) -> Path:
    return target.path.with_name(target.path.name + ".lock")
