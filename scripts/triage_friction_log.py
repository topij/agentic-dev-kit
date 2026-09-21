#!/usr/bin/env python3
"""CLI for deterministic draft, resume, approval, accounting, and recovery."""

from __future__ import annotations

import argparse
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
from triage.providers import GitHubForge, GitHubIssues  # noqa: E402
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
    result.add_argument("--enable-github-tracker", action="store_true", help="allow an approved live tracker transition through gh")
    result.add_argument("--enable-github-forge", action="store_true", help="allow an approved finalization transition through git and gh")
    return result


def hard_stop(detail: str) -> dict:
    return {
        "capabilities": {
            name: {"status": "not-triggered", "mechanism": "CLI input validation stopped before engine invocation"}
            for name in CAPABILITIES
        },
        "outcome": "hard-stop",
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


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
    except TriageError as exc:
        print(dumps(hard_stop(str(exc))).decode())
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
            print(dumps(hard_stop(str(exc))).decode())
            return 2
    tracker = GitHubIssues() if args.enable_github_tracker else None
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
            print(dumps(hard_stop(str(exc))).decode())
            return 2
    try:
        configured = load_settings(Path(__file__)) if args.enable_github_forge or args.enable_github_tracker else None
    except (OSError, TriageError, TypeError, ValueError) as exc:
        print(dumps(hard_stop(str(exc))).decode())
        return 2
    authority = GitHubForge(configured.paths.repo, pr_watch=configured.paths.engine_dir / "pr_watch.py") if configured is not None else None
    forge = authority if args.enable_github_forge else None
    result = run(args.entry, context=args.context, request=request, start=Path(__file__), tracker=tracker, approval_context=approval_context, forge=forge, head_authority=authority)
    print(dumps(result).decode())
    return 0 if result["outcome"] in {"successful-completion", "degraded-success", "operator-held"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
