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
    disposition_fields,
    preflight_receipt,
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
    result.add_argument("--context", choices=("interactive", "unattended"), default=None)
    result.add_argument("--request", type=Path, help="RFC 8785 canonical request JSON")
    result.add_argument("--approval-context", type=Path, help="runtime-attested canonical approval identity/read-back")
    trackers = result.add_mutually_exclusive_group()
    trackers.add_argument("--enable-github-tracker", action="store_true", help="allow an approved live GitHub tracker transition through gh")
    trackers.add_argument("--enable-tracker", action="store_true", help="select the approved tracker adapter from merged configuration")
    result.add_argument("--enable-github-forge", action="store_true", help="allow an approved finalization transition through git and gh")
    result.add_argument("--outcome-receipt", type=Path, help="fresh absolute receipt path (or DEVKIT_TRIAGE_OUTCOME_RECEIPT)")
    result.add_argument("--invocation-id", help="fresh per-call caller id (or DEVKIT_TRIAGE_INVOCATION_ID)")
    result.add_argument("--check-outcome-receipt", type=Path, help="read-only receipt classification; requires invocation expectations")
    result.add_argument("--expect-entry", choices=("auto", "resume", "new", "recover", "test"))
    result.add_argument("--expect-context", choices=("interactive", "unattended"))
    result.add_argument("--expect-mode", choices=("live", "test"))
    return result


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


def main(argv: list[str] | None = None, *, default_entry: str | None = None) -> int:
    try:
        args = parser().parse_args(argv)
    except TriageError as exc:
        print(dumps(hard_stop(str(exc))).decode())
        return 2
    invocation_id = args.invocation_id if args.invocation_id is not None else os.environ.get("DEVKIT_TRIAGE_INVOCATION_ID")
    if args.check_outcome_receipt is not None:
        # Checking never dispatches through the publishing path, even if the
        # environment contains a receipt destination. Parse errors and --help
        # also return before any receipt I/O.
        run_flags = (args.entry, args.context, args.request, args.approval_context, args.outcome_receipt)
        if (any(value is not None for value in run_flags)
                or args.enable_github_tracker or args.enable_tracker or args.enable_github_forge
                or args.expect_entry is None or args.expect_context is None or args.expect_mode is None):
            print(dumps(hard_stop("receipt checks require --expect-entry, --expect-context and --expect-mode, and accept no execution flags")).decode())
            return 2
        try:
            checked = check_receipt(args.check_outcome_receipt, invocation_id=invocation_id,
                                    entry=None if args.expect_entry == "auto" else args.expect_entry,
                                    context=args.expect_context, mode=args.expect_mode)
        except TriageError as exc:
            print(dumps(hard_stop(str(exc), exc.code)).decode())
            return 2
        print(dumps(checked).decode())
        return {"completed": 0, "waiting": 0, "refused": 1}.get(checked["verdict"], 2)
    if any(value is not None for value in (args.expect_entry, args.expect_context, args.expect_mode)):
        print(dumps(hard_stop("invocation expectations require --check-outcome-receipt")).decode())
        return 2
    args.entry = args.entry if args.entry is not None else default_entry
    args.context = args.context or "interactive"
    receipt_path = args.outcome_receipt
    if receipt_path is None and "DEVKIT_TRIAGE_OUTCOME_RECEIPT" in os.environ:
        receipt_path = Path(os.environ["DEVKIT_TRIAGE_OUTCOME_RECEIPT"])
    if receipt_path is not None or invocation_id is not None:
        try:
            if receipt_path is None or invocation_id is None:
                raise TriageError("an outcome receipt needs both a path and an invocation id", code="invalid-invocation")
            preflight_receipt(receipt_path, invocation_id)
        except (OSError, TriageError) as exc:
            print(dumps(hard_stop(f"outcome receipt unavailable: {exc}")).decode())
            return 2

    def finish(result: dict, status: int) -> int:
        # Preserve the engine result even when publication fails after it acted.
        print(dumps(result).decode())
        if receipt_path is not None:
            try:
                write_receipt(receipt_path, result, invocation_id=invocation_id, entry=args.entry, context=args.context)
            except (OSError, TriageError) as exc:
                print(f"outcome receipt not written: {exc}", file=sys.stderr)
                return 2
        return status

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
            return finish(hard_stop(str(exc)), 2)
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
            return finish(hard_stop(str(exc)), 2)
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
        return finish(hard_stop(str(exc), code), 2)
    authority = GitHubForge(configured.paths.repo, pr_watch=configured.paths.engine_dir / "pr_watch.py") if configured is not None else None
    forge = authority if args.enable_github_forge else None
    result = run(args.entry, context=args.context, request=request, start=Path(__file__), tracker=tracker, approval_context=approval_context, forge=forge, head_authority=authority)
    return finish(result, 0 if result["outcome"] in {"successful-completion", "degraded-success", "operator-held"} else 2)


if __name__ == "__main__":
    raise SystemExit(main())
