"""Provider protocols and independently observed GitHub/git operations."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.client import HTTPException
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .canonical import decode_bytes, digest, digest_bytes
from .model import TriageError, terminal_pr_watch_receipt, worktree_conflicts_with_checkout


@dataclass(frozen=True)
class ProviderObservation:
    status: str
    response: Any
    read_back: Any
    verified_route: str | None = None


class TrackerProvider(Protocol):
    def search(self, destination: dict[str, Any], marker: str) -> list[dict[str, Any]]: ...
    def create(self, destination: dict[str, Any], payload: dict[str, Any]) -> ProviderObservation: ...


class NotificationProvider(Protocol):
    def send_and_read_back(self, target: str, rendered: str, marker: str) -> ProviderObservation: ...
    def read_back(self, target: str, rendered: str, marker: str) -> ProviderObservation: ...


class ForgeProvider(Protocol):
    def authority(self, action: str, request: dict[str, Any]) -> dict[str, Any]: ...
    def perform(self, action: str, intent: dict[str, Any]) -> ProviderObservation: ...


Runner = Callable[[list[str], Path | None], subprocess.CompletedProcess[str]]


def subprocess_runner(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, check=False, capture_output=True, text=True)


class GitHubIssues:
    """GitHub Issues adapter. Tests inject a runner; live use invokes `gh api`."""

    # GitHub's issue list lags a fresh create (#808). After a successful
    # create, the listing is re-read on this schedule, in seconds, until it
    # shows the returned issue; uniqueness is then judged exactly as before.
    CREATE_LISTING_RETRY_DELAYS = (1.0, 2.0, 4.0, 8.0)

    def __init__(
        self,
        runner: Runner = subprocess_runner,
        *,
        sleep: Callable[[float], None] = time.sleep,
        create_listing_retry_delays: tuple[float, ...] = CREATE_LISTING_RETRY_DELAYS,
    ) -> None:
        self.runner = runner
        self.sleep = sleep
        self.create_listing_retry_delays = create_listing_retry_delays

    def _json(self, argv: list[str]) -> Any:
        result = self.runner(argv, None)
        if result.returncode:
            raise TriageError(f"provider command failed: {result.stderr.strip()}", outcome="operator-held")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise TriageError("provider returned invalid JSON", outcome="operator-held") from exc

    @staticmethod
    def _repository(destination: dict[str, Any]) -> tuple[str, str]:
        if destination.get("backend") != "github-issues":
            raise TriageError("unsupported tracker backend for GitHub adapter", outcome="operator-held")
        repository = destination.get("repository")
        if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise TriageError("invalid GitHub repository destination", outcome="operator-held")
        host = destination.get("host")
        if not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9.-]+", host):
            raise TriageError("invalid GitHub host destination", outcome="operator-held")
        return repository, host

    def search(self, destination: dict[str, Any], marker: str) -> list[dict[str, Any]]:
        repository, host = self._repository(destination)
        if not isinstance(marker, str) or not marker or marker.count("triage-payload:") != 1:
            raise TriageError("invalid tracker marker", outcome="operator-held")
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            data = self._json(["gh", "api", "--hostname", host, f"repos/{repository}/issues?state=all&per_page=100&page={page}"])
            if not isinstance(data, list):
                raise TriageError("tracker issue-list read-back is incomplete", outcome="operator-held")
            if any(not isinstance(item, dict) for item in data):
                raise TriageError("tracker issue-list contains a malformed item", outcome="operator-held")
            items.extend(data)
            if len(data) < 100:
                break
            page += 1
        observed = []
        for item in items:
            if "pull_request" in item:
                continue
            body = item.get("body")
            if isinstance(body, str) and marker in body and body.count(marker) != 1:
                raise TriageError("tracker marker multiplicity is ambiguous", outcome="operator-held")
            if not isinstance(body, str) or marker not in body:
                continue
            number = item.get("number")
            issue = self._json(["gh", "api", "--hostname", host, f"repos/{repository}/issues/{number}"])
            if not isinstance(issue, dict) or issue.get("number") != number or "pull_request" in issue:
                raise TriageError("tracker issue read-back identity mismatch", outcome="operator-held")
            issue_body = issue.get("body")
            if not isinstance(issue_body, str) or issue_body.count(marker) != 1:
                raise TriageError("tracker marker changed during read-back", outcome="operator-held")
            repository_url = issue.get("repository_url")
            observed_repository = repository_url.rsplit("/repos/", 1)[-1] if isinstance(repository_url, str) and "/repos/" in repository_url else None
            observed_host = urlparse(repository_url).hostname if isinstance(repository_url, str) else None
            expected_api_host = "api.github.com" if host == "github.com" else host
            if observed_repository != repository or destination.get("project") != observed_repository or observed_host != expected_api_host:
                raise TriageError("tracker destination read-back mismatch", outcome="operator-held")
            labels = issue.get("labels")
            if (
                not isinstance(labels, list)
                or any(
                    not isinstance(label, dict)
                    or not isinstance(label.get("name"), str)
                    or not label["name"]
                    for label in labels
                )
            ):
                raise TriageError("tracker label read-back is malformed", outcome="operator-held")
            label_names = [label["name"] for label in labels]
            if len(label_names) != len(set(label_names)):
                raise TriageError("tracker label read-back is ambiguous", outcome="operator-held")
            payload = {
                "title": issue.get("title"),
                "body": issue_body,
                "project": observed_repository,
                "labels": sorted(label_names),
            }
            observed.append({"identifier": str(number), "payload": payload, "payload_digest": digest(payload), "marker": marker, "destination": destination})
        return observed

    def create(self, destination: dict[str, Any], payload: dict[str, Any]) -> ProviderObservation:
        repository, host = self._repository(destination)
        fields = ["-f", f"title={payload['title']}", "-f", f"body={payload['body']}"]
        for label in payload["labels"]:
            fields.extend(["-f", f"labels[]={label}"])
        result = self.runner(["gh", "api", "--hostname", host, f"repos/{repository}/issues", "--method", "POST", *fields], None)
        response: Any
        try:
            response = json.loads(result.stdout) if result.stdout else None
        except json.JSONDecodeError:
            response = {"raw": result.stdout}
        marker = next((line for line in payload["body"].splitlines() if "triage-payload:" in line), "")
        matches = self.search(destination, marker) if marker else []
        response_identifier = response.get("number") if isinstance(response, dict) else None
        if (
            result.returncode == 0
            and marker
            and isinstance(response_identifier, int)
            and not isinstance(response_identifier, bool)
            and response_identifier > 0
        ):
            # Wait, bounded, for a listing that shows the issue this create
            # returned (#808). Such a listing is at least as fresh as the
            # create, so an earlier issue carrying the same marker shows in it
            # too and still makes the result ambiguous below. A listing that
            # never catches up leaves the result ambiguous, as before.
            for delay in self.create_listing_retry_delays:
                if any(item["identifier"] == str(response_identifier) for item in matches):
                    break
                self.sleep(delay)
                matches = self.search(destination, marker)
        exact = [item for item in matches if item["payload_digest"] == digest(payload)]
        if len(exact) == 1 and len(matches) == 1:
            if result.returncode == 0 and response_identifier is not None and str(response_identifier) != exact[0]["identifier"]:
                return ProviderObservation("ambiguous", response, {"matches": matches})
            if result.returncode != 0:
                route = "failed-response-then-exact-read-back"
            elif response_identifier is None:
                route = "ambiguous-response-then-exact-read-back"
            else:
                route = "created-and-read-back"
            return ProviderObservation("verified", response, exact[0], route)
        if result.returncode and not matches:
            return ProviderObservation("failed", response, {"matches": []})
        return ProviderObservation("ambiguous", response, {"matches": matches})


class LinearIssues:
    """Linear GraphQL adapter; mutations are never retried without reconciliation."""

    ENDPOINT = "https://api.linear.app/graphql"
    READ_RETRY_DELAYS = (1.0, 2.0, 4.0)
    CREATE_LISTING_RETRY_DELAYS = (1.0, 2.0, 4.0, 8.0)
    PAGE_INFO = "pageInfo { hasNextPage endCursor }"
    ISSUE_FIELDS = "id identifier url title description team { id } project { id name }"

    def __init__(self, *, transport=None, sleep=time.sleep, api_key=None) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("LINEAR_API_KEY")
        self.transport = transport if transport is not None else self._http
        self.sleep = sleep

    def _http(self, query: str, variables: dict[str, Any]) -> Any:
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise TriageError("set LINEAR_API_KEY for the selected Linear tracker", outcome="operator-held")
        request = Request(self.ENDPOINT, data=json.dumps({"query": query, "variables": variables}).encode(),
                          headers={"Authorization": self.api_key, "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    @staticmethod
    def _rate_limited(value: Any) -> bool:
        errors = value.get("errors") if isinstance(value, dict) else None
        return isinstance(errors, list) and bool(errors) and all(
            isinstance(e, dict) and isinstance(e.get("extensions"), dict)
            and e["extensions"].get("code") == "RATELIMITED"
            for e in errors
        )

    def _query(self, query: str, variables: dict[str, Any], *, mutation: bool = False) -> dict:
        delays = () if mutation else self.READ_RETRY_DELAYS
        for attempt in range(len(delays) + 1):
            retryable = False
            try:
                value = self.transport(query, variables)
                if isinstance(value, dict) and not value.get("errors") and isinstance(value.get("data"), dict):
                    return value["data"]
                retryable = self._rate_limited(value)
            except HTTPError as exc:
                # Linear documents GraphQL rate limiting as HTTP 400 with a
                # RATELIMITED body. Other bad requests remain permanent errors.
                with exc:
                    retryable = exc.code == 429 or 500 <= exc.code < 600
                    if exc.code == 400:
                        try:
                            retryable = self._rate_limited(json.load(exc))
                        except (HTTPException, OSError):
                            retryable = True
                        except (ValueError, TypeError):
                            retryable = False
            except (URLError, TimeoutError, OSError, HTTPException):
                retryable = True
            except (ValueError, TypeError):
                pass
            if not retryable or attempt == len(delays):
                # Transport bodies and exception text may carry credentials or
                # private response content; durable state gets only this verdict.
                raise TriageError("Linear API response is unavailable or incomplete", outcome="operator-held")
            self.sleep(delays[attempt])
        raise AssertionError("unreachable retry state")

    def _pages(self, query: str, variables: dict, select) -> list[dict]:
        items = []
        cursor = None
        seen = set()
        ids = set()
        while True:
            connection = select(self._query(query, {**variables, "cursor": cursor}))
            if not isinstance(connection, dict):
                raise TriageError("Linear connection is missing", outcome="operator-held")
            info, nodes = connection.get("pageInfo"), connection.get("nodes")
            if not isinstance(info, dict) or not isinstance(info.get("hasNextPage"), bool) or not isinstance(nodes, list):
                raise TriageError("Linear pagination is incomplete", outcome="operator-held")
            for node in nodes:
                if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"] or node["id"] in ids:
                    raise TriageError("Linear page identity is malformed or repeated", outcome="operator-held")
                ids.add(node["id"])
                items.append(node)
            if not info["hasNextPage"]:
                return items
            cursor = info.get("endCursor")
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise TriageError("Linear pagination cursor is missing or repeated", outcome="operator-held")
            seen.add(cursor)

    @staticmethod
    def _destination(destination: dict) -> None:
        if destination.get("backend") != "linear" or destination.get("host") != "linear.app":
            raise TriageError("unsupported Linear destination", outcome="operator-held")
        for name in ("team_id", "project_id", "project"):
            if not isinstance(destination.get(name), str) or not destination[name].strip():
                raise TriageError(f"Linear destination lacks {name}", outcome="operator-held")
        if not isinstance(destination.get("label_name"), str):
            raise TriageError("Linear label policy is invalid", outcome="operator-held")

    def _project(self, destination: dict) -> None:
        self._destination(destination)
        query = "query TriageProject($id: String!) { project(id: $id) { id name } }"
        project = self._query(query, {"id": destination["project_id"]}).get("project")
        if project != {"id": destination["project_id"], "name": destination["project"]}:
            raise TriageError("Linear project read-back mismatch", outcome="operator-held")
        query = ("query TriageProjectTeams($id: String!, $cursor: String) { project(id: $id) { "
                 f"teams(first: 100, after: $cursor) {{ {self.PAGE_INFO} nodes {{ id }} }} }} }}")
        teams = self._pages(query, {"id": destination["project_id"]}, lambda d: d["project"].get("teams") if isinstance(d.get("project"), dict) else None)
        if destination["team_id"] not in [t["id"] for t in teams]:
            raise TriageError("Linear project is outside the configured team", outcome="operator-held")

    def list_labels(self, destination: dict) -> list[dict]:
        self._destination(destination)
        query = ("query TriageLabels($filter: IssueLabelFilter, $cursor: String) { "
                 f"issueLabels(filter: $filter, first: 100, after: $cursor) {{ {self.PAGE_INFO} "
                 "nodes { id name isGroup team { id } } } }")
        variables = {"filter": {"or": [{"team": {"id": {"eq": destination["team_id"]}}}, {"team": {"null": True}}]}}
        labels = self._pages(query, variables, lambda d: d.get("issueLabels"))
        for label in labels:
            team = label.get("team")
            if (not isinstance(label.get("name"), str) or not label["name"]
                    or not isinstance(label.get("isGroup"), bool)
                    or (team is not None and team != {"id": destination["team_id"]})):
                raise TriageError("Linear label read-back mismatch", outcome="operator-held")
        return labels

    def _read_issue(self, destination: dict, iid: str, marker: str) -> dict:
        query = f"query TriageIssue($id: String!) {{ issue(id: $id) {{ {self.ISSUE_FIELDS} }} }}"
        issue = self._query(query, {"id": iid}).get("issue")
        url = issue.get("url") if isinstance(issue, dict) else None
        try:
            link = urlparse(url) if isinstance(url, str) else None
            valid_link = link is not None and link.hostname == "linear.app" and link.scheme == "https"
        except ValueError:
            valid_link = False
        if (not isinstance(issue, dict) or issue.get("id") != iid
                or issue.get("team") != {"id": destination["team_id"]}
                or issue.get("project") != {"id": destination["project_id"], "name": destination["project"]}
                or not isinstance(issue.get("identifier"), str) or not issue["identifier"]
                or not valid_link
                or not isinstance(issue.get("title"), str)
                or not isinstance(issue.get("description"), str) or issue["description"].count(marker) != 1):
            raise TriageError("Linear issue identity, marker or destination read-back mismatch", outcome="operator-held")
        # Archived labels are still payload evidence; hiding one could verify
        # an issue carrying an extra label the operator never approved.
        query = ("query TriageIssueLabels($id: String!, $cursor: String) { issue(id: $id) { "
                 f"labels(includeArchived: true, first: 100, after: $cursor) {{ {self.PAGE_INFO} nodes {{ id name }} }} }} }}")
        labels = self._pages(query, {"id": iid}, lambda d: d["issue"].get("labels") if isinstance(d.get("issue"), dict) else None)
        names = [label.get("name") for label in labels]
        if any(not isinstance(n, str) or not n for n in names) or len(names) != len(set(names)):
            raise TriageError("Linear issue label read-back is ambiguous", outcome="operator-held")
        payload = {"title": issue["title"], "body": issue["description"], "project": issue["project"]["name"], "labels": sorted(names)}
        return {"id": iid, "identifier": issue["identifier"], "url": issue["url"], "payload": payload,
                "payload_digest": digest(payload), "marker": marker, "destination": destination}

    def search(self, destination: dict, marker: str) -> list[dict]:
        self._project(destination)
        if not isinstance(marker, str) or not marker or marker.count("triage-payload:") != 1:
            raise TriageError("invalid tracker marker", outcome="operator-held")
        # Include archived issues so a past issue cannot disappear from dedup.
        query = ("query TriageIssues($filter: IssueFilter, $cursor: String) { "
                 f"issues(filter: $filter, includeArchived: true, first: 100, after: $cursor) {{ {self.PAGE_INFO} "
                 "nodes { id description } } }")
        issues = self._pages(query, {"filter": {"project": {"id": {"eq": destination["project_id"]}}}}, lambda d: d.get("issues"))
        matches = []
        for issue in issues:
            body = issue.get("description")
            if body is not None and not isinstance(body, str):
                raise TriageError("Linear issue listing is malformed", outcome="operator-held")
            if isinstance(body, str) and marker in body:
                matches.append(self._read_issue(destination, issue["id"], marker))
        return matches

    def create(self, destination: dict, payload: dict) -> ProviderObservation:
        self._project(destination)
        if payload.get("project") != destination["project"]:
            raise TriageError("approved Linear project differs from configured destination", outcome="operator-held")
        label_names = payload.get("labels")
        required = destination["label_name"]
        if (not isinstance(label_names, list) or any(not isinstance(n, str) or not n for n in label_names)
                or len(label_names) != len(set(label_names)) or (required and required not in label_names)):
            raise TriageError("approved Linear labels do not satisfy configured policy", outcome="operator-held")
        labels = self.list_labels(destination)
        label_ids = []
        for name in label_names:
            choices = [label for label in labels if label["name"] == name and not label["isGroup"]]
            if len(choices) != 1:
                raise TriageError("approved Linear label is missing or ambiguous", outcome="operator-held")
            label_ids.append(choices[0]["id"])
        body = payload.get("body")
        markers = [line for line in body.splitlines() if "triage-payload:" in line] if isinstance(body, str) else []
        if len(markers) != 1 or body.count(markers[0]) != 1:
            raise TriageError("approved Linear marker is missing or ambiguous", outcome="operator-held")
        marker = markers[0]
        prior = self.search(destination, marker)
        if prior:
            exact = len(prior) == 1 and prior[0]["payload_digest"] == digest(payload)
            return ProviderObservation("verified" if exact else "ambiguous", None,
                                       prior[0] if exact else {"matches": prior}, "pre-existing-exact-match" if exact else None)
        query = "mutation TriageCreate($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id identifier } } }"
        inputs = {"teamId": destination["team_id"], "projectId": destination["project_id"],
                  "title": payload["title"], "description": body, "labelIds": label_ids}
        response = None
        failed = False
        try:
            response = self._query(query, {"input": inputs}, mutation=True).get("issueCreate")
        except TriageError:
            failed = True
            response = {"error": "create outcome unknown"}
        returned_issue = response.get("issue") if isinstance(response, dict) else None
        returned = returned_issue.get("identifier") if isinstance(returned_issue, dict) else None
        returned_id = returned_issue.get("id") if isinstance(returned_issue, dict) else None
        success = isinstance(response, dict) and response.get("success") is True
        matches = self.search(destination, marker)
        for delay in self.CREATE_LISTING_RETRY_DELAYS:
            visible = any(m["identifier"] == returned for m in matches) if returned else bool(matches)
            if visible:
                break
            self.sleep(delay)
            matches = self.search(destination, marker)
        exact = [m for m in matches if m["payload_digest"] == digest(payload)]
        if (len(matches) == 1 and len(exact) == 1
                and (returned is None or returned == exact[0]["identifier"])
                and (returned_id is None or returned_id == exact[0]["id"])):
            route = "failed-response-then-exact-read-back" if failed else "created-and-read-back" if success and returned else "ambiguous-response-then-exact-read-back"
            return ProviderObservation("verified", response, exact[0], route)
        return ProviderObservation("ambiguous", response, {"matches": matches})


class FakeTracker:
    """Owned synthetic provider for tests; never invokes a subprocess."""

    def __init__(self, matches: list[dict[str, Any]] | None = None, create_observation: ProviderObservation | None = None) -> None:
        self.matches = list(matches or [])
        self.create_observation = create_observation
        self.calls: list[tuple[str, Any]] = []

    def search(self, destination: dict[str, Any], marker: str) -> list[dict[str, Any]]:
        self.calls.append(("search", {"destination": destination, "marker": marker}))
        return list(self.matches)

    def create(self, destination: dict[str, Any], payload: dict[str, Any]) -> ProviderObservation:
        self.calls.append(("create", {"destination": destination, "payload": payload}))
        if self.create_observation is None:
            raise AssertionError("fake tracker create observation was not configured")
        return self.create_observation


class FakeForge:
    def __init__(self, observations: list[ProviderObservation]) -> None:
        self.observations = list(observations)
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.branch_create_absence = {"local_branch_absent": True, "worktree_absent": True, "remote_branch_absent": True}

    def authority(self, action: str, request: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((f"authority:{action}", request))
        if action == "protected-head":
            return {
                "draft_head": request["draft_head"],
                "observed_head": request["draft_head"],
                "descends_from_draft": True,
            }
        if action == "branch-create-absent":
            return dict(self.branch_create_absence)
        if not self.observations or not isinstance(self.observations[0].read_back, dict):
            raise AssertionError(f"no fake forge authority source configured for {action}")
        read_back = self.observations[0].read_back
        if action == "branch-create":
            return {"finalize_base_head": read_back["base"], "descends_from_draft": True}
        if action == "commit":
            return {"paths": request["paths"], "staged_tree": read_back["tree"], "clean_before_stage": True}
        if action == "worktree-clean":
            return {"clean": True}
        raise AssertionError(f"unsupported fake forge authority action {action}")

    def perform(self, action: str, intent: dict[str, Any]) -> ProviderObservation:
        self.calls.append((action, intent))
        if not self.observations:
            raise AssertionError(f"no fake forge observation configured for {action}")
        return self.observations.pop(0)


class GitHubForge:
    """Explicitly enabled git/GitHub provider. It never issues a merge."""

    def __init__(self, repo: Path, runner: Runner = subprocess_runner, *, pr_watch: Path | None = None) -> None:
        self.repo = repo.resolve()
        self.runner = runner
        self.pr_watch = (pr_watch or (self.repo / "scripts/pr_watch.py")).resolve()

    def _run(self, argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return self.runner(argv, cwd or self.repo)

    def _git(self, cwd: Path, *args: str) -> str:
        result = self._run(["git", *args], cwd)
        if result.returncode:
            raise TriageError(f"git {' '.join(args)} failed: {result.stderr.strip()}", outcome="operator-held")
        return result.stdout.strip()

    def _gh_json(self, repository: str, pr: str, host: str) -> dict[str, Any]:
        result = self._run(["gh", "pr", "view", pr, "--repo", f"{host}/{repository}", "--json", "url,baseRefName,headRefName,headRefOid,isDraft,mergedAt,files"])
        if result.returncode:
            raise TriageError("pull-request read-back failed", outcome="operator-held")
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise TriageError("pull-request read-back returned invalid JSON", outcome="operator-held") from exc
        if not isinstance(value, dict):
            raise TriageError("pull-request read-back is malformed", outcome="operator-held")
        url = value.get("url")
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is None or parsed.hostname != host or not parsed.path.startswith(f"/{repository}/pull/"):
            raise TriageError("pull-request read-back destination mismatch", outcome="operator-held")
        files = value.get("files")
        if not isinstance(files, list) or any(not isinstance(item, dict) or not isinstance(item.get("path"), str) for item in files):
            raise TriageError("pull-request file read-back is malformed", outcome="operator-held")
        value = {**value, "files": [item["path"] for item in files]}
        return value

    @staticmethod
    def _commit_updates(request: dict[str, Any]) -> list[tuple[str, bytes]]:
        updates = request.get("updates")
        paths = request.get("paths")
        if (
            not isinstance(updates, list)
            or not isinstance(paths, list)
            or any(not isinstance(path, str) for path in paths)
            or any(
                not isinstance(update, dict)
                or set(update) != {
                    "path", "previous_content", "previous_digest", "content", "content_digest",
                }
                or not isinstance(update.get("path"), str)
                or not isinstance(update.get("previous_digest"), str)
                or not isinstance(update.get("previous_content"), str)
                or not isinstance(update.get("content"), str)
                or not isinstance(update.get("content_digest"), str)
                for update in updates
            )
            or [update["path"] for update in updates] != paths
            or any(
                Path(path).is_absolute() or ".." in Path(path).parts
                for path in paths
            )
        ):
            raise TriageError("commit update authority is malformed", outcome="operator-held")
        decoded: list[tuple[str, bytes]] = []
        for update in updates:
            try:
                raw = decode_bytes(update["content"])
                previous = decode_bytes(update["previous_content"])
            except (TypeError, ValueError) as exc:
                raise TriageError("commit update content is malformed", outcome="operator-held") from exc
            if (
                digest_bytes(raw) != update["content_digest"]
                or digest_bytes(previous) != update["previous_digest"]
            ):
                raise TriageError("commit update content digest mismatch", outcome="operator-held")
            decoded.append((update["path"], raw))
        return decoded

    @staticmethod
    def _pr_number(url: Any, *, host: str, repository: str) -> str:
        if not isinstance(url, str):
            raise TriageError("pull-request identity is not a URL", outcome="operator-held")
        parsed = urlparse(url)
        expected_path = f"/{repository}/pull/"
        if (
            parsed.scheme != "https"
            or parsed.hostname != host
            or parsed.params
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith(expected_path)
        ):
            raise TriageError("pull-request identity does not match the forge destination", outcome="operator-held")
        number = parsed.path[len(expected_path):]
        if not number.isdigit() or not number or "/" in number or int(number) <= 0:
            raise TriageError("pull-request URL lacks a numeric identity", outcome="operator-held")
        return number

    def authority(self, action: str, request: dict[str, Any]) -> dict[str, Any]:
        if action == "protected-head":
            branch_ref = f"refs/heads/{request['protected_branch']}"
            result = self._run(["git", "ls-remote", "origin", branch_ref], self.repo)
            if result.returncode or not result.stdout.strip():
                raise TriageError("protected branch authority read-back failed", outcome="hard-stop")
            observed = result.stdout.split()[0]
            exists = self._run(["git", "cat-file", "-e", f"{observed}^{{commit}}"], self.repo)
            if exists.returncode:
                fetched = self._run(["git", "fetch", "--no-write-fetch-head", "origin", observed], self.repo)
                if fetched.returncode:
                    raise TriageError("protected branch object refresh failed", outcome="hard-stop")
            ancestor = self._run(["git", "merge-base", "--is-ancestor", request["draft_head"], observed], self.repo)
            return {
                "draft_head": request["draft_head"],
                "observed_head": observed,
                "descends_from_draft": ancestor.returncode == 0,
            }
        if action == "branch-create-absent":
            # What a failed branch-create could have left behind: the local
            # branch, the worktree directory, or a remote branch of that name.
            branch = request["branch"]
            local = self._run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], self.repo)
            remote = self._run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], self.repo)
            # rev-parse --verify --quiet exits 1 only for a missing ref; any other
            # failure means the refs could not be read, which proves nothing.
            if local.returncode not in (0, 1):
                raise TriageError("local branch read-back failed", outcome="operator-held")
            if remote.returncode:
                raise TriageError("remote branch read-back failed", outcome="operator-held")
            return {
                "local_branch_absent": local.returncode == 1,
                "worktree_absent": not Path(request["worktree"]).exists(),
                "remote_branch_absent": not remote.stdout.strip(),
            }
        if action == "branch-create":
            branch_ref = f"refs/heads/{request['protected_branch']}"
            result = self._run(["git", "ls-remote", "origin", branch_ref], self.repo)
            if result.returncode or not result.stdout.strip():
                raise TriageError("protected branch authority read-back failed", outcome="operator-held")
            base = result.stdout.split()[0]
            exists = self._run(["git", "cat-file", "-e", f"{base}^{{commit}}"], self.repo)
            if exists.returncode:
                fetched = self._run(["git", "fetch", "--no-write-fetch-head", "origin", base], self.repo)
                if fetched.returncode:
                    raise TriageError("finalize base object fetch failed", outcome="operator-held")
            ancestor = self._run(["git", "merge-base", "--is-ancestor", request["draft_head"], base], self.repo)
            return {"finalize_base_head": base, "descends_from_draft": ancestor.returncode == 0}
        if action == "worktree-clean":
            worktree = Path(request["worktree"]).resolve()
            return {"clean": self._git(worktree, "status", "--porcelain") == ""}
        if action == "commit":
            worktree = Path(request["worktree"]).resolve()
            import tempfile

            updates = self._commit_updates(request)
            with tempfile.NamedTemporaryFile(prefix="triage-index-", dir=worktree, delete=True) as index:
                env = {**os.environ, "GIT_INDEX_FILE": index.name}
                seed = subprocess.run(["git", "read-tree", "HEAD"], cwd=worktree, env=env, check=False, capture_output=True, text=True)
                update_results = []
                for (path, raw), update in zip(updates, request["updates"], strict=True):
                    if digest_bytes((worktree / path).read_bytes()) != update["previous_digest"]:
                        raise TriageError("commit update source changed before authority", outcome="operator-held")
                    mode = subprocess.run(
                        ["git", "ls-files", "-s", "--", path], cwd=worktree,
                        check=False, capture_output=True, text=True,
                    )
                    fields = mode.stdout.split()
                    if mode.returncode or len(fields) < 4:
                        raise TriageError("commit update path is not tracked", outcome="operator-held")
                    blob = subprocess.run(
                        ["git", "hash-object", "-w", "--stdin"], cwd=worktree,
                        env=env, input=raw, check=False, capture_output=True,
                    )
                    if blob.returncode:
                        raise TriageError("commit update blob authority failed", outcome="operator-held")
                    update_results.append(subprocess.run(
                        ["git", "update-index", "--add", "--cacheinfo", fields[0], blob.stdout.decode().strip(), path],
                        cwd=worktree, env=env, check=False, capture_output=True, text=True,
                    ))
                names = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=worktree, env=env, check=False, capture_output=True, text=True)
                tree = subprocess.run(["git", "write-tree"], cwd=worktree, env=env, check=False, capture_output=True, text=True)
                if any(item.returncode for item in (seed, *update_results, names, tree)):
                    raise TriageError("staged-tree authority read-back failed", outcome="operator-held")
                return {"paths": names.stdout.strip().splitlines(), "staged_tree": tree.stdout.strip()}
        raise TriageError(f"unsupported forge authority action {action}", outcome="operator-held")

    def perform(self, action: str, intent: dict[str, Any]) -> ProviderObservation:
        if action == "branch-create":
            branch = intent["branch"]
            worktree = Path(intent["worktree"]).resolve()
            if worktree.exists():
                return ProviderObservation("ambiguous", None, {"reason": "worktree target exists"})
            base = intent["finalize_base_head"]
            created = self._run(["git", "worktree", "add", "-b", branch, str(worktree), base], self.repo)
            if created.returncode:
                return ProviderObservation("failed", {"stderr": created.stderr}, {"effect": "unverified"})
            read_back = {"repository": intent["repository"], "base": base, "branch": branch, "worktree": str(worktree), "head": self._git(worktree, "rev-parse", "HEAD"), "tree": self._git(worktree, "rev-parse", "HEAD^{tree}")}
            return ProviderObservation("verified", {"stdout": created.stdout}, read_back)
        worktree = Path(intent["worktree"]).resolve() if intent.get("worktree") else self.repo
        if action == "commit":
            paths = intent["paths"]
            updates = self._commit_updates(intent)
            if any(
                digest_bytes((worktree / path).read_bytes()) != digest_bytes(raw)
                for path, raw in updates
            ):
                return ProviderObservation("ambiguous", None, {"reason": "commit update bytes changed"})
            add = self._run(["git", "add", "--", *paths], worktree)
            if add.returncode:
                return ProviderObservation("failed", {"stderr": add.stderr}, {"effect": "unverified"})
            staged = self._git(worktree, "diff", "--cached", "--name-only").splitlines()
            staged_tree = self._git(worktree, "write-tree")
            if staged != paths or staged_tree != intent["authority_read_back"]["staged_tree"]:
                return ProviderObservation("ambiguous", None, {"staged_paths": staged, "staged_tree": staged_tree})
            committed = self._run(["git", "commit", "-m", intent["subject"]], worktree)
            if committed.returncode:
                return ProviderObservation("failed", {"stderr": committed.stderr}, {"effect": "unverified"})
            read_back = {"commit": self._git(worktree, "rev-parse", "HEAD"), "tree": self._git(worktree, "rev-parse", "HEAD^{tree}"), "subject": self._git(worktree, "show", "-s", "--format=%s", "HEAD"), "paths": self._git(worktree, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines(), "worktree": str(worktree), "branch": intent["branch"], "repository": intent["repository"], "base": intent["base"]}
            return ProviderObservation("verified", {"stdout": committed.stdout}, read_back)
        if action == "push":
            pushed = self._run(["git", "push", "-u", "origin", intent["branch"]], worktree)
            if pushed.returncode:
                return ProviderObservation("failed", {"stderr": pushed.stderr}, {"effect": "unverified"})
            remote = self._git(worktree, "ls-remote", "origin", f"refs/heads/{intent['branch']}").split()[0]
            status = "verified" if remote == intent["commit"] else "ambiguous"
            return ProviderObservation(status, {"stdout": pushed.stdout}, {"remote_head": remote, "tree": intent["tree"], "branch": intent["branch"], "worktree": str(worktree), "repository": intent["repository"], "base": intent["base"]})
        if action == "pull-request":
            created = self._run(["gh", "pr", "create", "--repo", f"{intent['host']}/{intent['repository']}", "--base", intent["base_branch"], "--head", intent["branch"], "--title", intent["title"], "--body", intent["body"]], worktree)
            response = {"stdout": created.stdout, "stderr": created.stderr, "returncode": created.returncode}
            pr_ref = created.stdout.strip() if created.stdout.strip() else intent["branch"]
            try:
                read_back = self._gh_json(intent["repository"], pr_ref, intent["host"])
            except TriageError:
                return ProviderObservation("ambiguous", response, None)
            exact = read_back.get("baseRefName") == intent["base_branch"] and read_back.get("headRefOid") == intent["head"] and read_back.get("isDraft") is False
            return ProviderObservation("verified" if exact else "ambiguous", response, read_back)
        if action == "pr-watch":
            pr_number = self._pr_number(
                intent.get("pr"), host=intent["host"], repository=intent["repository"]
            )
            asserted = self._run(["uv", "run", str(self.pr_watch), pr_number, "--assert-ready"], self.repo)
            if asserted.returncode:
                return ProviderObservation("failed", {"stderr": asserted.stderr}, self._gh_json(intent["repository"], str(intent["pr"]), intent["host"]))
            watched = self._run(["uv", "run", str(self.pr_watch), pr_number, "--json"], self.repo)
            read_back = self._gh_json(intent["repository"], str(intent["pr"]), intent["host"])
            if watched.returncode:
                return ProviderObservation("unsettled", {"stdout": watched.stdout, "stderr": watched.stderr}, read_back)
            try:
                receipt = json.loads(watched.stdout)
            except json.JSONDecodeError:
                return ProviderObservation("ambiguous", {"raw": watched.stdout}, read_back)
            terminal = terminal_pr_watch_receipt(
                receipt, head=intent["head"], url=intent["pr"]
            )
            if read_back.get("headRefOid") != intent["head"]:
                return ProviderObservation("ambiguous", receipt, read_back)
            if not terminal:
                return ProviderObservation("unsettled", receipt, read_back)
            return ProviderObservation("verified", receipt, {**read_back, "reviewed_head": intent["head"], "receipt": receipt})
        if action == "merge-read-back":
            read_back = self._gh_json(intent["repository"], str(intent["pr"]), intent["host"])
            merged = bool(read_back.get("mergedAt"))
            exact = read_back.get("headRefOid") == intent["reviewed_head"]
            return ProviderObservation("verified" if merged and exact else "unsettled" if not merged and exact else "ambiguous", None, {**read_back, "merged": merged})
        if action == "sweep-cleanup":
            return ProviderObservation("verified", None, self._sweep_cleanup(intent))
        raise TriageError(f"unsupported forge action {action}", outcome="operator-held")

    def _sweep_cleanup(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Retire this sweep's own worktree, local branch, and remote branch
        after its merge read-back verified (#807). Each artifact is guarded and
        idempotent, so a rerun after a partial cleanup reads the rest back as
        `absent` or `removed` rather than failing: never `--force`, never `-D`,
        and the remote branch only when its head still equals the exact commit
        this run pushed (a compare-and-delete, so a later push by someone else
        is never deleted)."""
        worktree = Path(intent["worktree"]).resolve()
        branch = intent["branch"]
        pushed_head = intent["pushed_head"]
        if worktree_conflicts_with_checkout(worktree, self.repo):
            reason = "sweep-cleanup worktree conflicts with the caller checkout"
            return {name: {"result": "kept", "reason": reason} for name in ("worktree", "local_branch", "remote_branch")}
        if not worktree.exists():
            worktree_result: dict[str, Any] = {"result": "absent", "reason": None}
        else:
            removed = self._run(["git", "worktree", "remove", str(worktree)], self.repo)
            if removed.returncode:
                worktree_result = {"result": "kept", "reason": f"git worktree remove refused: {removed.stderr.strip()}"}
            else:
                worktree_result = {"result": "removed", "reason": None}
        local = self._run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], self.repo)
        if local.returncode:
            local_result: dict[str, Any] = {"result": "absent", "reason": None}
        else:
            deleted = self._run(["git", "branch", "-d", branch], self.repo)
            if deleted.returncode:
                local_result = {"result": "kept", "reason": f"git branch -d refused: {deleted.stderr.strip()}"}
            else:
                local_result = {"result": "removed", "reason": None}
        remote = self._run(["git", "ls-remote", "origin", f"refs/heads/{branch}"], self.repo)
        if remote.returncode:
            remote_result: dict[str, Any] = {"result": "kept", "reason": f"remote branch read-back failed: {remote.stderr.strip()}"}
        elif not remote.stdout.strip():
            remote_result = {"result": "absent", "reason": None}
        else:
            remote_head = remote.stdout.split()[0]
            if remote_head != pushed_head:
                remote_result = {"result": "kept", "reason": "remote branch head moved since this run pushed it"}
            else:
                lease = f"refs/heads/{branch}:{remote_head}"
                deleted = self._run(["git", "push", f"--force-with-lease={lease}", "origin", f":refs/heads/{branch}"], self.repo)
                if deleted.returncode:
                    remote_result = {"result": "kept", "reason": f"compare-and-delete push refused: {deleted.stderr.strip()}"}
                else:
                    remote_result = {"result": "removed", "reason": None}
        return {"worktree": worktree_result, "local_branch": local_result, "remote_branch": remote_result}
