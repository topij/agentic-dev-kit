#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""CLI for deterministic draft, resume, approval, accounting, and recovery."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from triage.approval import ApprovalContext  # noqa: E402
from triage.canonical import CanonicalError, dumps, loads_exact  # noqa: E402
from triage.engine import run  # noqa: E402
from triage.model import (
    CAPABILITIES,  # noqa: E402
    TriageError,  # noqa: E402
    load_settings,  # noqa: E402
)
from triage.outcome import (  # noqa: E402
    check_receipt,
    claim_receipt,
    disposition_fields,
    receipt_path_error,
    write_receipt,
)
from triage.providers import GitHubForge, GitHubIssues, LinearIssues  # noqa: E402
from triage.storage import observe  # noqa: E402


class CanonicalArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise TriageError(f"invalid CLI arguments: {message}", outcome="hard-stop")


def parser() -> argparse.ArgumentParser:
    result = CanonicalArgumentParser(description=__doc__)
    result.add_argument("entry", nargs="?", choices=("resume", "new", "recover", "test"))
    result.add_argument("--context", choices=("interactive", "unattended"), default="interactive")
    result.add_argument("--request", type=Path, help="RFC 8785 canonical request JSON")
    result.add_argument("--approval-context", type=Path, help="runtime-attested canonical approval identity/read-back")
    trackers = result.add_mutually_exclusive_group()
    trackers.add_argument("--enable-github-tracker", action="store_true", help="allow an approved live GitHub tracker transition through gh")
    trackers.add_argument("--enable-tracker", action="store_true", help="select the approved tracker adapter from merged configuration")
    result.add_argument("--enable-github-forge", action="store_true", help="allow an approved finalization transition through git and gh")
    result.add_argument("--outcome-receipt", type=Path, help=f"absolute path for this invocation's outcome receipt (default ${RECEIPT_ENV})")
    result.add_argument("--invocation-id", help=f"caller-chosen id the receipt is bound to (default ${INVOCATION_ENV})")
    result.add_argument("--check-outcome-receipt", type=Path, help="classify an outcome receipt for --invocation-id and exit")
    result.add_argument("--expect-context", choices=("interactive", "unattended"), help="with --check-outcome-receipt: the context the caller invoked")
    result.add_argument("--expect-mode", choices=("live", "test"), help="with --check-outcome-receipt: the mode the caller invoked")
    return result


# An outer wrapper that cannot pass flags through (a scheduled agent run invokes
# the CLI itself) exports these instead; a flag wins over its variable.
RECEIPT_ENV = "DEVKIT_TRIAGE_OUTCOME_RECEIPT"
# Receipt paths this process already cleared, with the sequence each call takes.
_CLAIMED: dict[Path, int] = {}
INVOCATION_ENV = "DEVKIT_TRIAGE_INVOCATION_ID"
# Exit statuses of --check-outcome-receipt, by verdict.
CHECK_EXIT = {"completed": 0, "waiting": 0, "refused": 1}


def hard_stop(detail: str, code: str = "invalid-invocation") -> dict:
    return {
        "capabilities": {
            name: {"status": "not-triggered", "mechanism": "CLI input validation stopped before engine invocation"}
            for name in CAPABILITIES
        },
        "outcome": "hard-stop",
        **disposition_fields("hard-stop", refusal_code=code),
        "execution_mode": "unknown",
        "engine_mode": None,
        "report": None,
        "frozen_snapshot": None,
        "verified_tracker_identifiers": [],
        "resume_action": "correct the CLI input and retry",
        "detail": detail,
        "recovery_plan": None,
        "candidate_index": [],
        "pull_request_url": None,
        "observed_pr_head": None,
        "reviewed_head": None,
        "observed_protected_head": None,
    }


def _receipt_target(args: argparse.Namespace | None) -> tuple[Path | None, str | None]:
    path = args.outcome_receipt if args is not None else None
    invocation_id = args.invocation_id if args is not None else None
    return _with_environment(path, invocation_id)


def _with_environment(path: Path | None, invocation_id: str | None) -> tuple[Path | None, str | None]:
    if path is None and os.environ.get(RECEIPT_ENV):
        path = Path(os.environ[RECEIPT_ENV])
    if invocation_id is None and os.environ.get(INVOCATION_ENV):
        invocation_id = os.environ[INVOCATION_ENV]
    return path, invocation_id


def _check(args: argparse.Namespace) -> int:
    run_flags = (args.entry, args.request, args.approval_context, args.outcome_receipt)
    if any(flag is not None for flag in run_flags) or args.enable_github_tracker or args.enable_tracker or args.enable_github_forge:
        print(dumps(hard_stop("--check-outcome-receipt takes only --invocation-id, --expect-context and --expect-mode")).decode())
        return 2
    invocation_id = args.invocation_id if args.invocation_id is not None else os.environ.get(INVOCATION_ENV)
    try:
        if not args.check_outcome_receipt.is_absolute():
            raise TriageError("outcome receipt path must be absolute", code="invalid-invocation")
        verdict = check_receipt(
            args.check_outcome_receipt,
            invocation_id=invocation_id,
            context=args.expect_context,
            mode=args.expect_mode,
        )
    except TriageError as exc:
        print(dumps(hard_stop(str(exc), exc.code)).decode())
        return 2
    print(dumps(verdict).decode())
    return CHECK_EXIT.get(verdict["verdict"], 2)


def _early_receipt_target(argv: list[str]) -> tuple[Path | None, str | None, bool]:
    """The receipt path and id as given, read before the full parse, and whether
    the call is a receipt check. A call that then fails to parse, or whose id is
    malformed, has still cleared the path, so the caller's check finds no receipt
    rather than an earlier call's outcome under the same id."""
    early = argparse.ArgumentParser(add_help=False)
    early.add_argument("--outcome-receipt", type=Path)
    early.add_argument("--invocation-id")
    early.add_argument("--check-outcome-receipt")
    try:
        known, _ = early.parse_known_args(argv)
    except SystemExit:
        return (*_with_environment(None, None), False)
    return (*_with_environment(known.outcome_receipt, known.invocation_id), known.check_outcome_receipt is not None)


def main(argv: list[str] | None = None) -> int:
    _CLAIMED.clear()
    path, invocation_id, checking = _early_receipt_target(sys.argv[1:] if argv is None else list(argv))
    if not checking and path is not None and path.is_absolute():
        try:
            _CLAIMED[path] = claim_receipt(path, invocation_id=invocation_id)
        except (OSError, TriageError) as exc:
            code = exc.code if isinstance(exc, TriageError) else "invalid-invocation"
            print(dumps(hard_stop(f"outcome receipt path cannot be claimed: {exc}", code)).decode())
            return 2
    try:
        args = parser().parse_args(argv)
    except TriageError as exc:
        return _finish(hard_stop(str(exc)), None, entry=None, context=None, status=2, target=(path, invocation_id))
    if args.check_outcome_receipt is not None:
        return _check(args)
    if args.expect_context is not None or args.expect_mode is not None:
        return _finish(hard_stop("--expect-context and --expect-mode need --check-outcome-receipt"), args, entry=args.entry, context=args.context, status=2)
    receipt_error = receipt_path_error(*_receipt_target(args))
    if receipt_error is not None:
        # No receipt can be bound, so none is written, and an absolute path was
        # cleared above: the caller's check finds it missing or stale, never a
        # success.
        print(dumps(hard_stop(receipt_error)).decode())
        return 2
    request = {}
    if args.request is not None:
        try:
            _, request_raw = observe(args.request)
            if request_raw is None:
                raise CanonicalError("request file is missing")
            request = loads_exact(request_raw)
            if not isinstance(request, dict):
                raise CanonicalError("request root must be an object")
        except (OSError, CanonicalError, TriageError) as exc:
            return _finish(hard_stop(str(exc)), args, entry=args.entry, context=args.context, status=2)
    tracker = None
    approval_context = None
    if args.approval_context is not None:
        try:
            _, context_raw = observe(args.approval_context)
            if context_raw is None:
                raise CanonicalError("approval context file is missing")
            raw_context = loads_exact(context_raw)
            if not isinstance(raw_context, dict) or set(raw_context) != {"source", "operator_identity", "source_read_back"}:
                raise CanonicalError("approval context has the wrong shape")
            approval_context = ApprovalContext(**raw_context)
        except (OSError, CanonicalError, TriageError, TypeError) as exc:
            return _finish(hard_stop(str(exc)), args, entry=args.entry, context=args.context, status=2)
    try:
        configured = load_settings(Path(__file__)) if args.enable_github_forge or args.enable_github_tracker or args.enable_tracker else None
        if args.enable_github_tracker or args.enable_tracker:
            backend = configured.tracker.get("backend")
            if backend == "github-issues":
                tracker = GitHubIssues()
            elif backend == "linear" and args.enable_tracker:
                tracker = LinearIssues()
            else:
                raise TriageError(f"unsupported selected tracker backend: {backend}")
    except (OSError, TriageError, TypeError, ValueError) as exc:
        code = exc.code if isinstance(exc, TriageError) else "unclassified"
        return _finish(hard_stop(str(exc), code), args, entry=args.entry, context=args.context, status=2)
    authority = GitHubForge(configured.paths.repo, pr_watch=configured.paths.engine_dir / "pr_watch.py") if configured is not None else None
    forge = authority if args.enable_github_forge else None
    result = run(args.entry, context=args.context, request=request, start=Path(__file__), tracker=tracker, approval_context=approval_context, forge=forge, head_authority=authority)
    status = 0 if result["outcome"] in {"successful-completion", "degraded-success", "operator-held"} else 2
    return _finish(result, args, entry=args.entry, context=args.context, status=status)


def _finish(
    result: dict,
    args: argparse.Namespace | None,
    *,
    entry: str | None,
    context: str | None,
    status: int,
    target: tuple[Path | None, str | None] | None = None,
) -> int:
    """Print the result and, when a receipt was asked for, publish it.

    The result is printed whatever happens to the receipt: the engine may
    already have acted, and its result is the only report of that. A receipt
    that cannot be written makes the exit status 2, and the caller's check finds
    no receipt for its invocation."""
    print(dumps(result).decode())
    path, invocation_id = target if target is not None else _receipt_target(args)
    if receipt_path_error(path, invocation_id) is not None or path is None or invocation_id is None:
        return status
    try:
        sequence = _CLAIMED.pop(path) if path in _CLAIMED else claim_receipt(path, invocation_id=invocation_id)
        write_receipt(path, result, invocation_id=invocation_id, entry=entry, context=context, sequence=sequence)
    except (OSError, TriageError) as exc:
        print(f"outcome receipt not written: {exc}", file=sys.stderr)
        return 2
    return status


if __name__ == "__main__":
    raise SystemExit(main())
