"""Fetch the merged-PR population for a window into the raw bundle."""

from __future__ import annotations

import re
from datetime import date as Date
from datetime import datetime, time, timedelta, timezone
from typing import Any

from triage.canonical import CanonicalError, dumps

from . import artifacts, identity
from .config import Settings
from .errors import SystemizeError
from .forge import GitHubReader


def window_bounds(date: str, window_days: int) -> tuple[datetime, datetime]:
    """``window_days`` whole UTC days ending with ``date``, end-exclusive."""
    end = datetime.combine(Date.fromisoformat(date) + timedelta(days=1), time(0), tzinfo=timezone.utc)
    return end - timedelta(days=window_days), end


def _iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _login(node: dict[str, Any]) -> str | None:
    author = node.get("author")
    login = author.get("login") if isinstance(author, dict) else None
    return login if isinstance(login, str) else None


def _comment(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node.get("databaseId"),
        "author": _login(node),
        "body": node.get("body") or "",
        "url": node.get("url"),
        "created_at": node.get("createdAt"),
    }


def tracker_refs(repo: str, body: str, closing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: dict[tuple[str, int], dict[str, Any]] = {}
    for node in closing:
        owner = ((node.get("repository") or {}).get("nameWithOwner")) or repo
        number = node.get("number")
        if isinstance(number, int):
            refs[(owner, number)] = {"repo": owner, "number": number, "source": "closing-reference"}
    mentions = re.findall(r"(?<![\w/])#(\d+)\b", body)
    mentions += re.findall(rf"https://github\.com/{re.escape(repo)}/issues/(\d+)\b", body)
    for text in mentions:
        key = (repo, int(text))
        refs.setdefault(key, {"repo": repo, "number": int(text), "source": "body-mention"})
    return [refs[key] for key in sorted(refs)]


def collect_pr(reader: GitHubReader, repo: str, node: dict[str, Any]) -> dict[str, Any]:
    number = node.get("number")
    if not isinstance(number, int):
        raise SystemizeError("forge returned a merged pull request without a number")
    threads = []
    for thread in reader.pr_connection(repo, number, "reviewThreads"):
        threads.append({
            "id": thread.get("id"),
            "is_resolved": thread.get("isResolved"),
            "is_outdated": thread.get("isOutdated"),
            "path": thread.get("path"),
            "line": thread.get("line"),
            "comments": [_comment(c) for c in reader.thread_comments(thread)],
        })
    reviews = [
        {**_comment(r), "created_at": r.get("submittedAt"), "state": r.get("state")}
        for r in reader.pr_connection(repo, number, "reviews")
    ]
    body = node.get("body") or ""
    closing = reader.pr_connection(repo, number, "closingIssuesReferences")
    return {
        "number": number,
        "title": node.get("title"),
        "url": node.get("url"),
        "body": body,
        "author": _login(node),
        "base_ref": node.get("baseRefName"),
        "merged_at": node.get("mergedAt"),
        "merge_commit": (node.get("mergeCommit") or {}).get("oid"),
        "tracker_refs": tracker_refs(repo, body, closing),
        "files": sorted({f.get("path") for f in reader.pr_connection(repo, number, "files") if f.get("path")}),
        "reviews": reviews,
        "review_threads": threads,
        "issue_comments": [_comment(c) for c in reader.pr_connection(repo, number, "comments")],
    }


def run(settings: Settings, reader: GitHubReader, *, mode: str, window_days: int, date: str) -> dict[str, Any]:
    window_days = settings.window_days_for(window_days)
    # Resolve and check every canonical target before the forge is touched, so a
    # refused destination costs no network and writes nothing.
    raw_target = artifacts.state_write_target(
        settings, "cache", artifacts.render(settings.cache_pattern, date=date, window_days=window_days, mode=mode)
    )
    targets = all_targets(settings, date=date, window_days=window_days, mode=mode)
    artifacts.check_targets(settings, targets)

    repo = reader.repository()
    head = reader.branch_head(repo, settings.protected_branch)
    run_id = identity.run_identity(
        forge_repo=repo, window_days=window_days, head=head, fingerprint=settings.fingerprint, mode=mode
    )
    artifacts.require_replaceable(raw_target, kind=identity.RAW_KIND, identity=run_id)

    start, end = window_bounds(date, window_days)
    nodes, scanned = reader.merged_prs(repo, start, end)
    prs = sorted((collect_pr(reader, repo, n) for n in nodes), key=lambda p: p["number"])
    bundle = {
        **identity.header(identity.RAW_KIND, run_id),
        "window": {"days": window_days, "date": date, "start": _iso(start), "end": _iso(end)},
        "fetched_at": _iso(datetime.now(timezone.utc)),
        "population": {"merged_in_window": len(prs), "scanned": scanned},
        "prs": prs,
    }
    try:
        data = dumps(bundle)
    except CanonicalError as exc:
        raise SystemizeError(f"raw bundle is not canonical JSON: {exc}") from exc
    artifacts.check_targets(settings, targets)
    artifacts.publish(raw_target, data)
    return {
        "engine": "fetch",
        "cache_path": str(raw_target.path),
        "run_identity_digest": bundle["run_identity_digest"],
        "merged_in_window": len(prs),
    }


def all_targets(settings: Settings, *, date: str, window_days: int, mode: str) -> list[artifacts.Target]:
    """Every canonical artifact of the run, for collision and alias checks."""
    def logical(pattern: str) -> str:
        return artifacts.render(pattern, date=date, window_days=window_days, mode=mode)

    targets = [
        artifacts.state_write_target(settings, "cache", logical(settings.cache_pattern)),
        artifacts.state_write_target(settings, "digest", logical(settings.digest_pattern)),
        artifacts.report_target(settings, logical(settings.report_pattern)),
    ]
    if settings.heartbeat_pattern is not None:
        targets.append(artifacts.state_write_target(settings, "heartbeat", logical(settings.heartbeat_pattern)))
    return targets
