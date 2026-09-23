"""Read-only GitHub access through ``gh``, with every connection paged to completion.

The runner is injectable so tests can serve pages without a network. Any page
that fails, lacks ``pageInfo``, claims more pages without a cursor, or repeats a
cursor is a hard stop: a truncated fetch must never pass for a complete window.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import SystemizeError

Runner = Callable[[list[str], Path | None], subprocess.CompletedProcess[str]]


def subprocess_runner(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, cwd=cwd, check=False, capture_output=True, text=True)
    except OSError as exc:
        raise SystemizeError(f"forge read unavailable: cannot run {argv[0]}: {exc}") from exc


_ACTOR = "author { login }"
_COMMENT = f"databaseId {_ACTOR} body url createdAt"

MERGED_PRS = f"""query MergedPRs($owner: String!, $name: String!, $cursor: String) {{
  repository(owner: $owner, name: $name) {{
    pullRequests(states: MERGED, first: 50, after: $cursor, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{ number title url body mergedAt updatedAt baseRefName {_ACTOR} mergeCommit {{ oid }} }}
    }}
  }}
}}"""

# One query per pull-request connection, each paged independently.
PR_CONNECTIONS = {
    "reviews": f"databaseId {_ACTOR} body state submittedAt url",
    "reviewThreads": (
        "id isResolved isOutdated path line "
        f"comments(first: 100) {{ pageInfo {{ hasNextPage endCursor }} nodes {{ {_COMMENT} }} }}"
    ),
    "comments": _COMMENT,
    "files": "path",
    "closingIssuesReferences": "number url repository { nameWithOwner }",
}


def _connection_query(connection: str) -> str:
    return (
        f"query PR_{connection}($owner: String!, $name: String!, $number: Int!, $cursor: String) {{\n"
        f"  repository(owner: $owner, name: $name) {{ pullRequest(number: $number) {{\n"
        f"    {connection}(first: 100, after: $cursor) {{ pageInfo {{ hasNextPage endCursor }} "
        f"nodes {{ {PR_CONNECTIONS[connection]} }} }}\n"
        f"  }} }}\n}}"
    )


THREAD_COMMENTS = f"""query ThreadComments($id: ID!, $cursor: String) {{
  node(id: $id) {{ ... on PullRequestReviewThread {{
    comments(first: 100, after: $cursor) {{ pageInfo {{ hasNextPage endCursor }} nodes {{ {_COMMENT} }} }}
  }} }}
}}"""


def parse_time(value: Any, what: str) -> datetime:
    if not isinstance(value, str):
        raise SystemizeError(f"forge returned no {what} timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemizeError(f"forge returned an unparseable {what} timestamp {value!r}") from exc


class GitHubReader:
    def __init__(self, root: Path, runner: Runner = subprocess_runner) -> None:
        self.root = root
        self.runner = runner

    def _json(self, argv: list[str], what: str) -> Any:
        result = self.runner(argv, self.root)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            raise SystemizeError(f"forge read failed ({what}): {detail[0] if detail else 'no output'}")
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise SystemizeError(f"forge read returned invalid JSON ({what})") from exc
        if isinstance(value, dict) and value.get("errors"):
            raise SystemizeError(f"forge read returned errors ({what}): {value['errors']!r:.200}")
        return value

    def repository(self) -> str:
        value = self._json(["gh", "repo", "view", "--json", "nameWithOwner"], "repository")
        name = value.get("nameWithOwner") if isinstance(value, dict) else None
        if not isinstance(name, str) or name.count("/") != 1:
            raise SystemizeError("forge read returned no repository identity")
        return name

    def branch_head(self, repo: str, branch: str) -> str:
        value = self._json(["gh", "api", f"repos/{repo}/branches/{branch}"], "protected branch")
        sha = (value.get("commit") or {}).get("sha") if isinstance(value, dict) else None
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise SystemizeError(f"forge read returned no head for protected branch {branch}")
        return sha

    def _graphql(self, query: str, variables: dict[str, Any], what: str) -> Any:
        argv = ["gh", "api", "graphql", "-f", f"query={query}"]
        for key, value in variables.items():
            if value is None:
                continue
            argv += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
        value = self._json(argv, what)
        if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
            raise SystemizeError(f"forge read returned no data ({what})")
        return value["data"]

    @staticmethod
    def _page(connection: Any, what: str, seen: set[str]) -> tuple[list[Any], str | None]:
        if not isinstance(connection, dict):
            raise SystemizeError(f"forge read returned no connection ({what})")
        info = connection.get("pageInfo")
        nodes = connection.get("nodes")
        if not isinstance(info, dict) or not isinstance(info.get("hasNextPage"), bool) or not isinstance(nodes, list):
            raise SystemizeError(f"forge page is missing pageInfo or nodes ({what}); refusing a possibly truncated read")
        if not info["hasNextPage"]:
            return nodes, None
        cursor = info.get("endCursor")
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            raise SystemizeError(f"forge page claims more results without a usable cursor ({what})")
        seen.add(cursor)
        return nodes, cursor

    def _paged(self, fetch: Callable[[str | None], Any], what: str) -> list[Any]:
        items: list[Any] = []
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            nodes, cursor = self._page(fetch(cursor), what, seen)
            items.extend(nodes)
            if cursor is None:
                return items

    def merged_prs(self, repo: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], int]:
        """Merged PRs with ``start <= mergedAt < end``, and how many were scanned."""
        owner, name = repo.split("/")
        found: list[dict[str, Any]] = []
        scanned = 0
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            data = self._graphql(MERGED_PRS, {"owner": owner, "name": name, "cursor": cursor}, "merged pull requests")
            connection = ((data.get("repository") or {}).get("pullRequests"))
            nodes, cursor = self._page(connection, "merged pull requests", seen)
            older = False
            for node in nodes:
                scanned += 1
                merged = parse_time(node.get("mergedAt"), "mergedAt")
                if start <= merged < end:
                    found.append(node)
                # updatedAt >= mergedAt, so once a page reaches updatedAt < start
                # every later page (ordered by updatedAt descending) is older too.
                if parse_time(node.get("updatedAt"), "updatedAt") < start:
                    older = True
            if cursor is None or older:
                return found, scanned

    def pr_connection(self, repo: str, number: int, connection: str) -> list[Any]:
        owner, name = repo.split("/")
        query = _connection_query(connection)
        what = f"PR #{number} {connection}"

        def fetch(cursor: str | None) -> Any:
            data = self._graphql(query, {"owner": owner, "name": name, "number": number, "cursor": cursor}, what)
            return (((data.get("repository") or {}).get("pullRequest")) or {}).get(connection)

        return self._paged(fetch, what)

    def thread_comments(self, thread: dict[str, Any]) -> list[Any]:
        """A thread's comments, paging beyond the first batch embedded in the thread page."""
        what = f"review thread {thread.get('id')} comments"
        first = thread.get("comments")
        seen: set[str] = set()
        nodes, cursor = self._page(first, what, seen)
        comments = list(nodes)
        while cursor is not None:
            data = self._graphql(THREAD_COMMENTS, {"id": thread.get("id"), "cursor": cursor}, what)
            nodes, cursor = self._page((data.get("node") or {}).get("comments"), what, seen)
            comments.extend(nodes)
        return comments
