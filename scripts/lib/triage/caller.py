"""Scheduled caller bookkeeping inside a trusted launcher/filesystem boundary.

The launcher owns allocation, process status and final inspection. The CLI claims
an attempt before dispatch. This is not authentication against a process that can
rewrite the ledger, environment or engine; runtime containment remains upstream
of this protocol. No operation here changes retained triage workflow state.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from .canonical import dumps, loads_exact
from .model import TOKEN_RE, TriageError
from .outcome import ENTRIES, check_receipt, preflight_receipt
from .storage import exclusive_create, observe

RUN_ENV = "DEVKIT_TRIAGE_CALLER_RUN"
ATTEMPT_ENV = "DEVKIT_TRIAGE_CALLER_ATTEMPT"
# Transport markers supplied by scheduled launchers, not job-name allowlists.
SCHEDULED_ENV = (RUN_ENV, ATTEMPT_ENV, "JOB_NAME", "AUTOMATION_RUN_ID")
RUN_KIND = "triage-caller-run"
ATTEMPT_KIND = "triage-caller-attempt"


def _refuse(detail: str) -> None:
    raise TriageError(detail, code="invalid-invocation")


def _absolute(path: Path) -> None:
    if not path.is_absolute() or ".." in path.parts:
        _refuse("caller artifact path must be absolute without '..'")


def _read(path: Path) -> dict:
    _absolute(path)
    _, raw = observe(path)
    if raw is None:
        _refuse(f"caller evidence missing: {path}")
    value = loads_exact(raw)
    if not isinstance(value, dict):
        _refuse(f"caller evidence must be an object: {path}")
    return value


def _write(path: Path, value: dict) -> None:
    exclusive_create(path, dumps(value), temporary_name=f".{path.name}.{uuid.uuid4().hex}.tmp")


def _run(root: Path) -> dict:
    value = _read(root / "run.json")
    if (set(value) != {"kind", "schema_version", "run_id"} or value["kind"] != RUN_KIND
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or not isinstance(value["run_id"], str) or not TOKEN_RE.fullmatch(value["run_id"])):
        _refuse("invalid caller run")
    return value


def create_run(root: Path) -> None:
    """Launcher: exclusively allocate a private run before starting the agent."""
    _absolute(root)
    # Probe ancestors with the same no-alias reader used for receipts before mkdir.
    observe(root / "run.json", read=False)
    root.mkdir(mode=0o700)
    _write(root / "run.json", {"kind": RUN_KIND, "schema_version": 1, "run_id": uuid.uuid4().hex})


def prepare_attempt(root: Path, *, entry: str | None, mode: str = "live") -> Path:
    """Launcher: allocate before dispatch; retries always get a new attempt."""
    run = _run(root)
    if entry not in ENTRIES or mode not in ("live", "test"):
        _refuse("invalid caller invocation expectation")
    invocation_id = uuid.uuid4().hex
    call = root / f"call-{invocation_id}"
    call.mkdir(mode=0o700)
    attempt = call / "attempt.json"
    _write(attempt, {"kind": ATTEMPT_KIND, "schema_version": 1, "run_id": run["run_id"],
                     "invocation_id": invocation_id, "entry": entry, "context": "unattended",
                     "mode": mode, "outcome_receipt": str(call / "outcome.json")})
    return attempt


def read_attempt(root: Path, attempt: Path) -> dict:
    """Read a caller expectation without accepting a foreign run or path."""
    run = _run(root)
    value = _read(attempt)
    if (set(value) != {"kind", "schema_version", "run_id", "invocation_id", "entry", "context", "mode", "outcome_receipt"}
            or value["kind"] != ATTEMPT_KIND or type(value["schema_version"]) is not int
            or value["schema_version"] != 1 or value["run_id"] != run["run_id"]
            or not isinstance(value["invocation_id"], str) or not TOKEN_RE.fullmatch(value["invocation_id"])
            or value["entry"] not in ENTRIES or value["context"] != "unattended"
            or value["mode"] not in ("live", "test")):
        _refuse("invalid caller attempt")
    call = root / f"call-{value['invocation_id']}"
    if attempt != call / "attempt.json" or value["outcome_receipt"] != str(call / "outcome.json"):
        _refuse("caller attempt does not belong to this run/path")
    return value


def enforce_attempt(*, attempt: Path | None, receipt: Path | None, invocation_id: str | None,
                    entry: str | None, context: str) -> None:
    """CLI: consume a matching caller attempt before any engine transition."""
    if context != "unattended" and attempt is None and not any(key in os.environ for key in SCHEDULED_ENV):
        return
    root_text = os.environ.get(RUN_ENV)
    if not root_text or attempt is None:
        _refuse("scheduled triage requires a caller run and a fresh caller attempt; use the scheduled launcher")
    root = Path(root_text)
    expected = read_attempt(root, attempt)
    if (receipt is None or str(receipt) != expected["outcome_receipt"]
            or invocation_id != expected["invocation_id"] or entry != expected["entry"]
            or context != expected["context"]):
        _refuse("scheduled invocation differs from the caller's expectation")
    preflight_receipt(receipt, invocation_id)
    # Exclusive creation is the consumption gate: replays and concurrent claims
    # cannot dispatch again, even if the first process died before its receipt.
    _write(attempt.parent / "claimed.json", expected)


def record_rejection(detail: str) -> None:
    """CLI: retain refused direct/malformed calls so later success cannot hide them.

    Without a valid run the CLI still refuses. The launcher must treat a missing
    or inaccessible run as failure, and preserve its marker for every child.
    """
    root_text = os.environ.get(RUN_ENV)
    if root_text:
        root = Path(root_text)
        _run(root)
        _write(root / f"rejected-{uuid.uuid4().hex}.json", {"detail": detail})


def record_exit(root: Path, attempt: Path, returncode: int | None) -> None:
    """Launcher: retain the actual process exit; None means it did not finish."""
    read_attempt(root, attempt)
    if returncode is not None and type(returncode) is not int:
        _refuse("caller process status must be an integer or null")
    _write(attempt.parent / "process.json", {"returncode": returncode})


def check_run(root: Path) -> list[dict]:
    """Launcher: after all children exit, verify coverage; raise on any failure.

    The returned checks are not ordered transitions or a job-completion verdict.
    The caller retains dispatch order, agent exit status and its final-result
    policy (including approval waits and reconciliation), in addition to this gate.
    """
    _run(root)
    calls = []
    for path in sorted(root.iterdir()):
        if path.name == "run.json":
            continue
        if not path.name.startswith("call-"):
            _refuse(f"caller run contains rejected or incomplete evidence: {path.name}")
        expected = read_attempt(root, path / "attempt.json")
        if _read(path / "claimed.json") != expected:
            _refuse("caller claim differs from its expectation")
        process = _read(path / "process.json")
        if set(process) != {"returncode"} or type(process["returncode"]) is not int or process["returncode"] != 0:
            _refuse("scheduled engine process failed or was interrupted")
        checked = check_receipt(Path(expected["outcome_receipt"]), invocation_id=expected["invocation_id"],
                                entry=expected["entry"], context=expected["context"], mode=expected["mode"])
        if checked["verdict"] not in ("completed", "waiting"):
            _refuse(f"scheduled engine outcome failed verification: {checked['verdict']}")
        calls.append(checked)
    if not calls:
        _refuse("scheduled caller made no engine calls")
    return calls
