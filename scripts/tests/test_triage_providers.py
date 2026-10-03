from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from datetime import date  # noqa: E402

from triage.canonical import digest  # noqa: E402
from triage.model import TriageError  # noqa: E402
from triage.providers import GitHubForge, GitHubIssues, LinearIssues  # noqa: E402

DESTINATION = {"backend": "github-issues", "host": "github.com", "repository": "owner/repo", "project": "owner/repo"}
MARKER = "<!-- triage-payload:session:TRI-01:" + "a" * 64 + " -->"

LINEAR_DESTINATION = {"backend": "linear", "host": "linear.app", "repository": "Adopter",
                      "project": "Adopter", "team_id": "team", "project_id": "project", "label_name": "bug"}


class LinearTransport:
    def __init__(self):
        self.calls = []
        self.issues = []
        self.labels = [{"id": "label", "name": "bug", "isGroup": False, "team": {"id": "team"}}]
        self.fault = None
        self.lag = 0

    def page(self, nodes, variables):
        start = int(variables.get("cursor") or 0)
        # A deliberately short page with hasNextPage exercises cursor authority.
        more = start + 1 < len(nodes)
        return {"nodes": nodes[start:start + 1],
                "pageInfo": {"hasNextPage": more, "endCursor": str(start + 1) if more else None}}

    def __call__(self, query, variables):
        self.calls.append((query, variables))
        if "TriageProjectTeams(" in query:
            result = {"project": {"teams": self.page([{"id": "other"}, {"id": "team"}], variables)}}
        elif "TriageProject(" in query:
            result = {"project": {"id": "project", "name": "Adopter"}}
        elif "TriageLabels(" in query:
            result = {"issueLabels": self.page(self.labels, variables)}
        elif "TriageIssueLabels(" in query:
            issue = next(i for i in self.issues if i["id"] == variables["id"])
            labels = [{"id": label["id"], "name": label["name"]} for label in issue["labels"]
                      if not label.get("archived") or "includeArchived: true" in query]
            result = {"issue": {"labels": self.page(labels, variables)}}
        elif "TriageIssue(" in query:
            result = {"issue": {k: v for k, v in next(i for i in self.issues if i["id"] == variables["id"]).items() if k != "labels"}}
        elif "TriageIssues(" in query:
            assert "includeArchived: true" in query
            nodes = [{"id": i["id"], "description": i["description"]} for i in self.issues]
            if self.lag:
                self.lag -= 1
                nodes = []
            result = {"issues": self.page(nodes, variables)}
        elif "TriageCreate(" in query:
            item = variables["input"]
            assert item["teamId"] == "team" and item["projectId"] == "project"
            assert item["labelIds"] == ["label"]
            self.issues.append({"id": "issue", "identifier": "ADO-17", "url": "https://linear.app/w/issue/ADO-17",
                                "title": item["title"], "description": item["description"],
                                "team": {"id": item["teamId"]}, "project": {"id": item["projectId"], "name": "Adopter"},
                                "labels": [{"id": "label", "name": "bug"}]})
            if self.fault == "timeout":
                raise TimeoutError("create response lost")
            if self.fault == "duplicate":
                self.issues.append({**self.issues[-1], "id": "duplicate", "identifier": "ADO-18"})
            result = {"issueCreate": {"success": True, "issue": {"id": "issue", "identifier": "ADO-17"}}}
        else:
            raise AssertionError(query)
        return {"data": result}


def linear_payload():
    return {"title": "title", "body": "body\n" + MARKER, "project": "Adopter", "labels": ["bug"]}


def test_linear_create_readback_paginates_team_labels_and_issues():
    transport = LinearTransport()
    transport.labels.insert(0, {"id": "unrelated", "name": "other", "isGroup": False, "team": None})
    transport.issues.append({"id": "old", "description": "unrelated"})
    slept = []
    tracker = LinearIssues(transport=transport, sleep=slept.append)
    observed = tracker.create(LINEAR_DESTINATION, linear_payload())
    assert observed.status == "verified"
    assert observed.verified_route == "created-and-read-back"
    assert observed.read_back["payload"] == linear_payload()
    assert observed.read_back["identifier"] == "ADO-17"
    assert any("TriageLabels(" in q and v["cursor"] == "1" for q, v in transport.calls)
    assert any("TriageIssues(" in q and v["cursor"] == "1" for q, v in transport.calls)
    assert slept == []
    before = sum("TriageCreate(" in q for q, _ in transport.calls)
    assert tracker.create(LINEAR_DESTINATION, linear_payload()).verified_route == "pre-existing-exact-match"
    assert sum("TriageCreate(" in q for q, _ in transport.calls) == before


@pytest.mark.parametrize("fault, status", [("timeout", "verified"), ("duplicate", "ambiguous")])
def test_linear_uncertain_create_never_retries_mutation(fault, status):
    transport = LinearTransport()
    transport.fault = fault
    observed = LinearIssues(transport=transport, sleep=lambda _: None).create(LINEAR_DESTINATION, linear_payload())
    assert observed.status == status
    assert sum("TriageCreate(" in q for q, _ in transport.calls) == 1
    if fault == "timeout":
        assert observed.verified_route == "failed-response-then-exact-read-back"


@pytest.mark.parametrize("timing", ["existing", "created"])
def test_linear_archived_extra_label_cannot_verify_approved_payload(timing):
    transport = LinearTransport()
    tracker = LinearIssues(transport=transport, sleep=lambda _: None)
    extra = {"id": "hidden", "name": "unapproved-archived", "archived": True}
    if timing == "existing":
        assert tracker.create(LINEAR_DESTINATION, linear_payload()).status == "verified"
        transport.issues[0]["labels"].append(extra)
        observed = tracker.create(LINEAR_DESTINATION, linear_payload())
    else:
        def altered(query, variables):
            result = transport(query, variables)
            if "TriageCreate(" in query:
                transport.issues[0]["labels"].append(extra)
            return result
        observed = LinearIssues(transport=altered, sleep=lambda _: None).create(LINEAR_DESTINATION, linear_payload())
    assert observed.status == "ambiguous"
    assert observed.verified_route is None
    assert observed.read_back["matches"][0]["payload"]["labels"] == ["bug", "unapproved-archived"]
    assert sum("TriageCreate(" in query for query, _ in transport.calls) == 1


def test_linear_create_waits_for_listing_visibility():
    transport = LinearTransport()
    original = transport.__call__
    def lagged(query, variables):
        result = original(query, variables)
        if "TriageCreate(" in query:
            transport.lag = 2
        return result
    slept = []
    observed = LinearIssues(transport=lagged, sleep=slept.append).create(LINEAR_DESTINATION, linear_payload())
    assert observed.status == "verified"
    assert slept == [1.0, 2.0]


@pytest.mark.parametrize("fault", ["cursor", "pageinfo", "team", "labels", "marker", "project", "url"])
def test_linear_incomplete_or_wrong_readback_fails_closed(fault):
    transport = LinearTransport()
    tracker = LinearIssues(transport=transport, sleep=lambda _: None)
    tracker.create(LINEAR_DESTINATION, linear_payload())
    original = transport.__call__
    def altered(query, variables):
        value = original(query, variables)
        if "TriageIssues(" in query and fault in {"cursor", "pageinfo"}:
            connection = value["data"]["issues"]
            connection["pageInfo"] = {"hasNextPage": True, "endCursor": None} if fault == "cursor" else {}
        if "TriageIssue(" in query:
            issue = value["data"]["issue"]
            if fault == "team":
                issue["team"] = {"id": "foreign"}
            elif fault == "project":
                issue["project"] = {"id": "foreign", "name": "Adopter"}
            elif fault == "marker":
                issue["description"] += "\n" + MARKER
            elif fault == "url":
                issue["url"] = "https://["
        if "TriageIssueLabels(" in query and fault == "labels":
            value["data"]["issue"]["labels"]["nodes"] = [{"id": "label", "name": None}]
        return value
    with pytest.raises(TriageError):
        LinearIssues(transport=altered).search(LINEAR_DESTINATION, MARKER)


@pytest.mark.parametrize("operation, parent", [("TriageProjectTeams(", "project"), ("TriageIssueLabels(", "issue")])
@pytest.mark.parametrize("malformed", [["bad"], "bad", True, 7])
def test_linear_malformed_nested_connection_is_controlled(operation, parent, malformed):
    transport = LinearTransport()
    assert LinearIssues(transport=transport, sleep=lambda _: None).create(LINEAR_DESTINATION, linear_payload()).status == "verified"
    def altered(query, variables):
        if operation in query:
            return {"data": {parent: malformed}}
        return transport(query, variables)
    with pytest.raises(TriageError, match="Linear connection is missing"):
        LinearIssues(transport=altered, sleep=lambda _: None).search(LINEAR_DESTINATION, MARKER)
    assert sum("TriageCreate(" in query for query, _ in transport.calls) == 1


def test_linear_create_refuses_mismatched_response_uuid():
    transport = LinearTransport()
    def altered(query, variables):
        value = transport(query, variables)
        if "TriageCreate(" in query:
            value["data"]["issueCreate"]["issue"]["id"] = "foreign-uuid"
        return value
    observed = LinearIssues(transport=altered, sleep=lambda _: None).create(LINEAR_DESTINATION, linear_payload())
    assert observed.status == "ambiguous"
    assert observed.verified_route is None
    assert observed.read_back["matches"][0]["id"] == "issue"
    assert observed.response["issue"]["id"] == "foreign-uuid"


def test_linear_read_retries_are_bounded_and_partial_data_is_refused():
    calls = []
    slept = []
    def timed_out(query, variables):
        calls.append(query)
        raise TimeoutError("unavailable")
    tracker = LinearIssues(transport=timed_out, sleep=slept.append)
    with pytest.raises(TriageError):
        tracker.search(LINEAR_DESTINATION, MARKER)
    assert slept == list(tracker.READ_RETRY_DELAYS)
    assert len(calls) == len(slept) + 1
    tracker = LinearIssues(transport=lambda *_: {"data": {"project": {}}, "errors": [{"message": "partial"}]})
    with pytest.raises(TriageError):
        tracker.search(LINEAR_DESTINATION, MARKER)


@pytest.mark.parametrize("labels", [[], ["missing"], ["bug", "bug"]])
def test_linear_label_policy_never_changes_approved_payload(labels):
    transport = LinearTransport()
    payload = {**linear_payload(), "labels": labels}
    with pytest.raises(TriageError):
        LinearIssues(transport=transport).create(LINEAR_DESTINATION, payload)
    assert not any("TriageCreate(" in q for q, _ in transport.calls)
    assert payload["labels"] == labels


def test_linear_missing_credential_and_http_timeout(monkeypatch):
    import triage.providers as providers
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with pytest.raises(TriageError, match="LINEAR_API_KEY"):
        LinearIssues()._http("query", {})
    captured = []
    def timed_out(request, *, timeout):
        captured.append((request, timeout))
        raise TimeoutError("read timed out")
    monkeypatch.setattr(providers, "urlopen", timed_out)
    slept = []
    tracker = LinearIssues(api_key="private-key", sleep=slept.append)
    with pytest.raises(TriageError) as error:
        tracker.search(LINEAR_DESTINATION, MARKER)
    assert "private-key" not in str(error.value)
    assert all(timeout == 30 for _, timeout in captured)
    assert captured[0][0].get_header("Authorization") == "private-key"
    assert json.loads(captured[0][0].data)["variables"] == {"id": "project"}
    assert slept == list(tracker.READ_RETRY_DELAYS)


def test_linear_rate_limit_retry_then_success():
    transport = LinearTransport()
    slept = []
    calls = []
    def throttled(query, variables):
        calls.append(query)
        if len(calls) == 1:
            return {"data": {}, "errors": [{"extensions": {"code": "RATELIMITED"}}]}
        return transport(query, variables)
    assert LinearIssues(transport=throttled, sleep=slept.append).search(LINEAR_DESTINATION, MARKER) == []
    assert slept == [1.0]


@pytest.mark.parametrize("status", [400, 429, 503])
@pytest.mark.parametrize("exhausted", [False, True])
def test_linear_http_rate_limit_retries_reads(monkeypatch, exhausted, status):
    from io import BytesIO
    from urllib.error import HTTPError

    from triage import providers

    calls, slept = [], []
    def request(req, timeout):
        calls.append(req)
        if exhausted or len(calls) == 1:
            body = {"errors": [{"message": "private-key", "extensions": {"code": "RATELIMITED"}}]}
            raise HTTPError(req.full_url, status, "rate limited", {}, BytesIO(json.dumps(body).encode()))
        return BytesIO(json.dumps({"data": {"project": {"id": "project"}}}).encode())
    monkeypatch.setattr(providers, "urlopen", request)
    tracker = LinearIssues(api_key="private-key", sleep=slept.append)
    if exhausted:
        with pytest.raises(TriageError, match="unavailable or incomplete") as error:
            tracker._query("query Project { project { id } }", {})
        assert "private-key" not in str(error.value)
        assert len(calls) == len(tracker.READ_RETRY_DELAYS) + 1
        assert slept == list(tracker.READ_RETRY_DELAYS)
    else:
        assert tracker._query("query Project { project { id } }", {}) == {"project": {"id": "project"}}
        assert len(calls) == 2 and slept == [1.0]


@pytest.mark.parametrize("body", [b"not JSON", b'{"errors": []}',
    b'{"errors": [{"extensions": {"code": "AUTHENTICATION_ERROR"}}]}',
    b'{"errors": [{"extensions": {"code": "RATELIMITED"}}, {"extensions": {"code": "FORBIDDEN"}}]}'])
def test_linear_http400_permanent_errors_do_not_retry(monkeypatch, body):
    from io import BytesIO
    from urllib.error import HTTPError

    from triage import providers

    calls, slept = [], []
    def request(req, timeout):
        calls.append(req)
        raise HTTPError(req.full_url, 400, "bad request", {}, BytesIO(body))
    monkeypatch.setattr(providers, "urlopen", request)
    with pytest.raises(TriageError, match="unavailable or incomplete"):
        LinearIssues(api_key="key", sleep=slept.append)._query("query Project { project { id } }", {})
    assert len(calls) == 1 and slept == []


@pytest.mark.parametrize("landed", [False, True])
def test_linear_http400_mutation_reconciles_without_retry(monkeypatch, landed):
    from io import BytesIO
    from urllib.error import HTTPError

    from triage import providers

    transport = LinearTransport()
    creates = []
    def request(req, timeout):
        value = json.loads(req.data)
        query, variables = value["query"], value["variables"]
        if "TriageCreate(" in query:
            creates.append(value)
            if landed:
                transport(query, variables)
            body = {"errors": [{"extensions": {"code": "RATELIMITED"}}]}
            raise HTTPError(req.full_url, 400, "rate limited", {}, BytesIO(json.dumps(body).encode()))
        return BytesIO(json.dumps(transport(query, variables)).encode())
    monkeypatch.setattr(providers, "urlopen", request)
    observed = LinearIssues(api_key="key", sleep=lambda _: None).create(LINEAR_DESTINATION, linear_payload())
    assert len(creates) == 1
    assert observed.status == ("verified" if landed else "ambiguous")
    assert observed.verified_route == ("failed-response-then-exact-read-back" if landed else None)


@pytest.mark.parametrize("backend, flag, expected", [
    ("linear", "--enable-tracker", LinearIssues),
    ("github-issues", "--enable-tracker", GitHubIssues),
    ("github-issues", "--enable-github-tracker", GitHubIssues),
])
def test_cli_selects_tracker_from_merged_settings(monkeypatch, tmp_path, backend, flag, expected):
    spec = importlib.util.spec_from_file_location("triage_cli_selection", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    settings = SimpleNamespace(tracker={"backend": backend}, paths=SimpleNamespace(repo=tmp_path, engine_dir=ENGINE_DIR))
    monkeypatch.setattr(cli, "load_settings", lambda _: settings)
    observed = []
    def run(*args, **kwargs):
        observed.append(kwargs["tracker"])
        return {"outcome": "operator-held"}
    monkeypatch.setattr(cli, "run", run)
    assert cli.main(["resume", flag]) == 0
    assert isinstance(observed[0], expected)


def test_cli_rejects_conflicting_tracker_flags():
    spec = importlib.util.spec_from_file_location("triage_cli_flags", ENGINE_DIR / "triage_friction_log.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.main(["--enable-tracker", "--enable-github-tracker"]) == 2


class Runner:
    def __init__(self, responses: list[tuple[int, object]]) -> None:
        self.responses = list(responses)
        self.argv: list[list[str]] = []

    def __call__(self, argv: list[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        self.argv.append(argv)
        code, body = self.responses.pop(0)
        stdout = body if isinstance(body, str) else json.dumps(body)
        return subprocess.CompletedProcess(argv, code, stdout=stdout, stderr="failure" if code else "")


def issue(number: int, payload: dict, *, pull_request: bool = False) -> dict:
    value = {
        "number": number,
        "title": payload["title"],
        "body": payload["body"],
        "labels": [{"name": label} for label in payload["labels"]],
        "repository_url": "https://api.github.com/repos/owner/repo",
    }
    if pull_request:
        value["pull_request"] = {"url": "example"}
    return value


def test_search_paginates_full_issue_listing_and_filters_pull_requests() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    first_page = [{"number": number, "body": "unrelated"} for number in range(100)]
    second_page = [{"number": 101, "body": payload["body"]}, {"number": 102, "body": payload["body"], "pull_request": {}}]
    runner = Runner([(0, first_page), (0, second_page), (0, issue(101, payload))])
    observed = GitHubIssues(runner).search(DESTINATION, MARKER)
    assert observed == [{"identifier": "101", "payload": payload, "payload_digest": digest(payload), "marker": MARKER, "destination": DESTINATION}]
    assert "page=1" in runner.argv[0][-1]
    assert "page=2" in runner.argv[1][-1]


def adapter(runner: Runner, delays: tuple[float, ...] = (1.0,)) -> tuple[GitHubIssues, list[float]]:
    """A GitHub adapter whose post-create listing retries record their delays
    instead of sleeping."""
    slept: list[float] = []
    return GitHubIssues(runner, sleep=slept.append, create_listing_retry_delays=delays), slept


def test_create_refuses_success_identifier_that_differs_from_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (0, {"number": 99}),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    tracker, slept = adapter(runner)
    observed = tracker.create(DESTINATION, payload)
    assert observed.status == "ambiguous"
    assert slept == [1.0]  # waited for #99 to appear; it never did


def test_create_waits_for_a_lagging_listing_to_show_the_created_issue() -> None:
    """#808: GitHub's issue list lags a fresh create. The listing is re-read
    until it shows the returned issue, and only then judged."""
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (0, {"number": 101}),
        (0, []),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    tracker, slept = adapter(runner, (1.0, 2.0))
    observed = tracker.create(DESTINATION, payload)
    assert observed.status == "verified"
    assert observed.verified_route == "created-and-read-back"
    assert observed.read_back["identifier"] == "101"
    assert slept == [1.0]


def test_create_listing_that_already_shows_the_issue_does_not_wait() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (0, {"number": 101}),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    tracker, slept = adapter(runner, (1.0, 2.0))
    assert tracker.create(DESTINATION, payload).status == "verified"
    assert slept == []


def test_create_listing_that_never_shows_the_issue_stays_ambiguous() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([(0, {"number": 101}), (0, []), (0, []), (0, [])])
    tracker, slept = adapter(runner, (1.0, 2.0))
    observed = tracker.create(DESTINATION, payload)
    assert observed.status == "ambiguous"
    assert observed.read_back == {"matches": []}
    assert slept == [1.0, 2.0]
    assert len(runner.argv) == 4  # the create and one listing per wait, bounded


def test_create_whose_caught_up_listing_shows_a_duplicate_stays_ambiguous() -> None:
    """A listing fresh enough to show the created issue also shows an earlier
    issue carrying the same marker — for example one a failed-looking create
    actually made — so the duplicate is not hidden behind the lag."""
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (0, {"number": 101}),
        (0, []),
        (0, [{"number": 55, "body": payload["body"]}, {"number": 101, "body": payload["body"]}]),
        (0, issue(55, payload)),
        (0, issue(101, payload)),
    ])
    tracker, slept = adapter(runner)
    observed = tracker.create(DESTINATION, payload)
    assert observed.status == "ambiguous"
    assert [item["identifier"] for item in observed.read_back["matches"]] == ["55", "101"]
    assert slept == [1.0]


@pytest.mark.parametrize("returned", [{}, {"number": True}, {"number": "101"}, {"number": 0}, None])
def test_create_without_a_usable_returned_number_does_not_wait(returned: object) -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([(0, returned if returned is not None else ""), (0, [])])
    tracker, slept = adapter(runner)
    assert tracker.create(DESTINATION, payload).status == "ambiguous"
    assert slept == []
    assert len(runner.argv) == 2


def test_failed_create_does_not_wait_for_the_listing() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([(1, {"number": 101}), (0, [])])
    tracker, slept = adapter(runner)
    assert tracker.create(DESTINATION, payload).status == "failed"
    assert slept == []


def test_failed_response_can_verify_only_through_exact_independent_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    runner = Runner([
        (1, "gateway failed"),
        (0, [{"number": 101, "body": payload["body"]}]),
        (0, issue(101, payload)),
    ])
    observed = GitHubIssues(runner).create(DESTINATION, payload)
    assert observed.status == "verified"
    assert observed.verified_route == "failed-response-then-exact-read-back"


def test_destination_is_derived_from_authoritative_issue_repository() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": []}
    foreign = issue(101, payload)
    foreign["repository_url"] = "https://api.github.com/repos/other/repo"
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, foreign)])
    with pytest.raises(TriageError, match="destination"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_destination_host_is_bound_to_authoritative_issue_readback() -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": []}
    foreign = issue(101, payload)
    foreign["repository_url"] = "https://github.example.invalid/repos/owner/repo"
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, foreign)])
    with pytest.raises(TriageError, match="destination"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_duplicate_marker_is_ambiguous_not_authoritative_absence() -> None:
    runner = Runner([(0, [{"number": 101, "body": MARKER + "\n" + MARKER}])])
    with pytest.raises(TriageError, match="multiplicity"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_malformed_list_item_invalidates_absence_readback() -> None:
    runner = Runner([(0, [None])])
    with pytest.raises(TriageError, match="malformed"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


def test_unsorted_authoritative_labels_reconcile_to_canonical_payload_order() -> None:
    payload = {
        "title": "title",
        "body": "body\n" + MARKER,
        "project": "owner/repo",
        "labels": ["alpha", "zeta"],
    }
    read_back = issue(101, payload)
    read_back["labels"] = [{"name": "zeta"}, {"name": "alpha"}]
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, read_back)])
    observed = GitHubIssues(runner).search(DESTINATION, MARKER)
    assert observed[0]["payload"] == payload
    assert observed[0]["payload_digest"] == digest(payload)


@pytest.mark.parametrize(
    "labels",
    [
        {"name": "bug"},
        [{"name": "bug"}, {"color": "red"}],
        [{"name": "bug"}, {"name": "bug"}],
    ],
)
def test_malformed_or_ambiguous_label_readback_is_held(labels: object) -> None:
    payload = {"title": "title", "body": "body\n" + MARKER, "project": "owner/repo", "labels": ["bug"]}
    read_back = issue(101, payload)
    read_back["labels"] = labels
    runner = Runner([(0, [{"number": 101, "body": payload["body"]}]), (0, read_back)])
    with pytest.raises(TriageError, match="label read-back"):
        GitHubIssues(runner).search(DESTINATION, MARKER)


@pytest.mark.parametrize("backend", [None, "linear", "jira"])
def test_github_adapter_refuses_foreign_tracker_backend_before_provider_call(backend: str | None) -> None:
    runner = Runner([])
    with pytest.raises(TriageError, match="unsupported tracker backend"):
        GitHubIssues(runner).search({**DESTINATION, "backend": backend}, MARKER)
    assert runner.argv == []


def pr_view(head: str) -> dict:
    return {
        "url": "https://github.com/owner/repo/pull/17",
        "baseRefName": "main",
        "headRefName": "chore/triage",
        "headRefOid": head,
        "isDraft": False,
        "mergedAt": None,
        "files": [{"path": "docs/kit-friction-log.md"}],
    }


def watch_intent(head: str) -> dict:
    return {
        "host": "github.com",
        "repository": "owner/repo",
        "pr": "https://github.com/owner/repo/pull/17",
        "base_branch": "main",
        "head": head,
        "tree": "b" * 40,
    }


@pytest.mark.parametrize(
    "receipt",
    [
        {"converged": False, "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
        {"converged": True, "head": "c" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
        {"converged": True, "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": False}},
        {"converged": True, "mergeable": False, "done": False, "merge_blockers": ["review pending"], "head": "a" * 40, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}},
    ],
)
def test_pr_watch_exit_zero_without_complete_exact_head_review_is_unsettled(tmp_path: Path, receipt: dict) -> None:
    head = "a" * 40
    runner = Runner([(0, ""), (0, receipt), (0, pr_view(head))])
    observed = GitHubForge(tmp_path, runner, pr_watch=tmp_path / "configured-pr-watch.py").perform("pr-watch", watch_intent(head))
    assert observed.status == "unsettled"
    assert str(tmp_path / "configured-pr-watch.py") in runner.argv[0]
    assert runner.argv[0][-2:] == ["17", "--assert-ready"]
    assert runner.argv[1][-2:] == ["17", "--json"]


def test_pr_watch_moved_head_is_ambiguous(tmp_path: Path) -> None:
    head = "a" * 40
    receipt = {"converged": True, "head": head, "url": "https://github.com/owner/repo/pull/17", "truncated_reads": [], "review_evidence": {"valid": True}}
    runner = Runner([(0, ""), (0, receipt), (0, pr_view("c" * 40))])
    assert GitHubForge(tmp_path, runner).perform("pr-watch", watch_intent(head)).status == "ambiguous"


def test_pr_watch_terminal_native_receipt_verifies_exact_head(tmp_path: Path) -> None:
    head = "a" * 40
    receipt = {
        "converged": True,
        "mergeable": True,
        "done": True,
        "merge_blockers": [],
        "head": head,
        "url": "https://github.com/owner/repo/pull/17",
        "truncated_reads": [],
        "review_evidence": {"valid": True},
    }
    runner = Runner([(0, ""), (0, receipt), (0, pr_view(head))])
    observed = GitHubForge(tmp_path, runner).perform("pr-watch", watch_intent(head))
    assert observed.status == "verified"
    assert observed.read_back["reviewed_head"] == head


def test_pr_watch_transport_matches_numeric_shared_cli_contract(tmp_path: Path) -> None:
    parser_probe = subprocess.run(
        [sys.executable, str(ENGINE_DIR / "pr_watch.py"), "https://github.com/owner/repo/pull/17", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert parser_probe.returncode == 2
    assert "invalid int value" in parser_probe.stderr

    with pytest.raises(TriageError, match="forge destination"):
        GitHubForge(tmp_path, Runner([])).perform(
            "pr-watch",
            {**watch_intent("a" * 40), "pr": "https://example.com/owner/repo/pull/17"},
        )


def test_malformed_successful_pull_request_json_is_a_canonical_provider_hold(tmp_path: Path) -> None:
    intent = {
        "host": "github.com",
        "repository": "owner/repo",
        "pr": "https://github.com/owner/repo/pull/17",
        "base": "main",
        "reviewed_head": "a" * 40,
    }
    with pytest.raises(TriageError, match="invalid JSON"):
        GitHubForge(tmp_path, Runner([(0, "not-json")])).perform("merge-read-back", intent)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize("leftover", [None, "local-branch", "worktree", "remote-branch"])
def test_branch_create_absence_reads_the_real_repository(tmp_path: Path, leftover: str | None) -> None:
    """Each thing a failed branch-create could have left is read from git and the filesystem."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    branch, worktree = "chore/triage-2099-01-01", tmp_path / "sweep"
    if leftover == "local-branch":
        _git(repo, "branch", branch)
    elif leftover == "worktree":
        worktree.mkdir()
    elif leftover == "remote-branch":
        _git(repo, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
    absence = GitHubForge(repo).authority("branch-create-absent", {"branch": branch, "worktree": str(worktree)})
    expected = {"local_branch_absent": True, "worktree_absent": True, "remote_branch_absent": True}
    if leftover is not None:
        expected[{"local-branch": "local_branch_absent", "worktree": "worktree_absent", "remote-branch": "remote_branch_absent"}[leftover]] = False
    assert absence == expected


def test_branch_create_absence_holds_when_the_remote_cannot_be_read(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "remote", "add", "origin", str(tmp_path / "missing.git"))
    with pytest.raises(TriageError, match="remote branch read-back failed"):
        GitHubForge(repo).authority("branch-create-absent", {"branch": "b", "worktree": str(tmp_path / "w")})


def test_branch_create_absence_holds_when_local_refs_cannot_be_read(tmp_path: Path) -> None:
    """An unreadable ref store is not proof the branch is absent."""
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "branch", "chore/triage-2099-01-01")
    _git(repo, "pack-refs", "--all")
    (repo / ".git/packed-refs").write_text("garbage that is not a packed ref\n", encoding="utf-8")
    with pytest.raises(TriageError, match="local branch read-back failed"):
        GitHubForge(repo).authority("branch-create-absent", {"branch": "chore/triage-2099-01-01", "worktree": str(tmp_path / "w")})


def test_two_same_day_branch_creates_bound_to_distinct_sessions_do_not_collide(tmp_path: Path) -> None:
    """#807: the shipped default binds the branch to `{session}`, so two
    finalizations on the same day create distinct branches and neither
    fails; the exact same branch twice still collides, which is the failure
    `{session}` exists to avoid."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    base = _git(repo, "rev-parse", "HEAD")
    day = date.today().isoformat()
    pattern = "chore/triage-{date}-{session}"
    branch_a = pattern.replace("{date}", day).replace("{session}", "a" * 8)
    branch_b = pattern.replace("{date}", day).replace("{session}", "b" * 8)
    assert branch_a != branch_b
    forge = GitHubForge(repo)
    session_a = forge.perform("branch-create", {
        "repository": "owner/repo", "branch": branch_a,
        "worktree": str(tmp_path / "sweep-a"), "finalize_base_head": base,
    })
    session_b = forge.perform("branch-create", {
        "repository": "owner/repo", "branch": branch_b,
        "worktree": str(tmp_path / "sweep-b"), "finalize_base_head": base,
    })
    assert session_a.status == "verified"
    assert session_b.status == "verified"
    # The failure #807 reports: the same branch name, twice on the same day, collides.
    collision = forge.perform("branch-create", {
        "repository": "owner/repo", "branch": branch_a,
        "worktree": str(tmp_path / "sweep-a-again"), "finalize_base_head": base,
    })
    assert collision.status == "failed"


def _pushed_sweep_branch(tmp_path: Path) -> tuple[Path, Path, str, str]:
    """A repo with a triage-style branch pushed from its own isolated
    worktree, as branch-create, commit, and push leave it before its PR
    merges — the state `_sweep_cleanup` retires (#807)."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    _git(repo, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    base = _git(repo, "rev-parse", "HEAD")
    branch = "chore/triage-2099-01-01-deadbeef"
    worktree = tmp_path / "sweep"
    _git(repo, "worktree", "add", "-q", "-b", branch, str(worktree), base)
    _git(worktree, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-q", "--allow-empty", "-m", "sweep")
    pushed_head = _git(worktree, "rev-parse", "HEAD")
    _git(worktree, "push", "-q", "-u", "origin", branch)
    return repo, worktree, branch, pushed_head


def _cleanup_intent(worktree: Path, branch: str, pushed_head: str) -> dict:
    return {"repository": "owner/repo", "branch": branch, "worktree": str(worktree), "base": "main", "pushed_head": pushed_head}


def test_sweep_cleanup_removes_clean_worktree_merged_branch_and_unchanged_remote(tmp_path: Path) -> None:
    repo, worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(worktree, branch, pushed_head))
    assert observed.status == "verified"
    assert observed.read_back == {
        "worktree": {"result": "removed", "reason": None},
        "local_branch": {"result": "removed", "reason": None},
        "remote_branch": {"result": "removed", "reason": None},
    }
    assert not worktree.exists()
    local = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], capture_output=True, text=True)
    assert local.returncode != 0
    remote = _git(repo, "ls-remote", "origin", f"refs/heads/{branch}")
    assert remote == ""


def test_sweep_cleanup_keeps_a_dirty_worktree_and_its_checked_out_branch(tmp_path: Path) -> None:
    repo, worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    (worktree / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(worktree, branch, pushed_head))
    result = observed.read_back
    assert result["worktree"]["result"] == "kept"
    assert isinstance(result["worktree"]["reason"], str) and result["worktree"]["reason"]
    # The branch is still checked out at the kept worktree, so its own safe
    # delete is refused too -- never removed while something still uses it.
    assert result["local_branch"]["result"] == "kept"
    assert result["remote_branch"]["result"] == "removed"
    assert worktree.exists()
    local = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], capture_output=True, text=True)
    assert local.returncode == 0


def test_sweep_cleanup_keeps_a_remote_branch_whose_head_moved(tmp_path: Path) -> None:
    repo, worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    intruder = tmp_path / "intruder"
    subprocess.run(["git", "clone", "-q", "--branch", branch, str(tmp_path / "origin.git"), str(intruder)], check=True)
    _git(intruder, "-c", "user.email=x@example.invalid", "-c", "user.name=X", "commit", "-q", "--allow-empty", "-m", "someone else's push")
    _git(intruder, "push", "-q", "origin", branch)
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(worktree, branch, pushed_head))
    result = observed.read_back
    assert result["worktree"]["result"] == "removed"
    assert result["local_branch"]["result"] == "removed"
    assert result["remote_branch"]["result"] == "kept"
    assert "moved" in result["remote_branch"]["reason"]
    remote = _git(repo, "ls-remote", "origin", f"refs/heads/{branch}")
    assert remote.split()[0] != pushed_head


def test_sweep_cleanup_is_idempotent_on_rerun(tmp_path: Path) -> None:
    repo, worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    intent = _cleanup_intent(worktree, branch, pushed_head)
    forge = GitHubForge(repo)
    first = forge.perform("sweep-cleanup", intent)
    assert {entry["result"] for entry in first.read_back.values()} == {"removed"}
    second = forge.perform("sweep-cleanup", intent)
    assert second.status == "verified"
    assert {entry["result"] for entry in second.read_back.values()} == {"absent"}
    assert all(entry["reason"] is None for entry in second.read_back.values())


def test_sweep_cleanup_never_touches_the_caller_checkout(tmp_path: Path) -> None:
    repo, _worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(repo, branch, pushed_head))
    result = observed.read_back
    assert all(entry["result"] == "kept" for entry in result.values())
    assert all("caller checkout" in entry["reason"] for entry in result.values())
    # Nothing was touched: the branch this run pushed is still there, checked
    # out at the caller's own checkout.
    local = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], capture_output=True, text=True)
    assert local.returncode == 0
    # The provider's own guard also refuses a path inside the caller's
    # checkout, and one that contains it, without reaching git.
    for conflicting in (repo / "nested", repo.parent):
        observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(conflicting, branch, pushed_head))
        assert all("caller checkout" in entry["reason"] for entry in observed.read_back.values())
    assert subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], capture_output=True, text=True).returncode == 0


def _skip_unless_case_insensitive(directory: Path) -> None:
    probe = directory / "case-probe"
    probe.write_bytes(b"")
    folded = (directory / "CASE-PROBE").exists()
    probe.unlink()
    if not folded:
        pytest.skip("filesystem is case-sensitive; a case-variant path names a different directory")


@pytest.mark.parametrize("placement", ["same", "inside", "containing"])
def test_sweep_cleanup_keeps_a_case_variant_of_the_caller_checkout(tmp_path: Path, placement: str) -> None:
    """`resolve()` keeps the spelling it was given, so the provider's guard decides
    containment by filesystem identity, as the engine's guards do (#891)."""
    _skip_unless_case_insensitive(tmp_path)
    repo, _worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    variant = repo.with_name(repo.name.swapcase())
    conflicting = {
        "same": variant,
        "inside": variant / "nested",
        "containing": repo.parent.with_name(repo.parent.name.swapcase()),
    }[placement]
    assert conflicting != repo and not conflicting.is_relative_to(repo) and not repo.is_relative_to(conflicting)
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(conflicting, branch, pushed_head))
    assert {entry["result"] for entry in observed.read_back.values()} == {"kept"}
    assert all("caller checkout" in entry["reason"] for entry in observed.read_back.values())
    # Nothing was touched: the branch this run pushed is still there, locally and on the remote.
    assert _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
    assert _git(repo, "ls-remote", "origin", f"refs/heads/{branch}").split()[0] == pushed_head


def test_sweep_cleanup_guard_asks_the_predicate_the_engine_shares(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The case-variant test above skips on a case-sensitive filesystem, which is
    what CI runs on. This pins, on any filesystem, that the provider and the engine
    hold the same predicate function, and that the provider's guard asks it. The
    predicate's identity branches are pinned by `test_finalize_triage.py`, with a
    case-folding `Path.stat`, and the engine's call sites by its guard tests (#891)."""
    import triage.engine
    import triage.model
    import triage.providers

    shared = triage.model.worktree_conflicts_with_checkout
    assert triage.providers.worktree_conflicts_with_checkout is shared
    assert triage.engine._worktree_conflicts_with_checkout is shared

    repo, worktree, branch, pushed_head = _pushed_sweep_branch(tmp_path)
    asked: list[tuple[Path, Path]] = []

    def conflicts(candidate: Path, checkout: Path) -> bool:
        asked.append((candidate, checkout))
        return True

    monkeypatch.setattr(triage.providers, "worktree_conflicts_with_checkout", conflicts)
    observed = GitHubForge(repo).perform("sweep-cleanup", _cleanup_intent(worktree, branch, pushed_head))
    assert asked == [(worktree.resolve(), repo.resolve())]
    assert {entry["result"] for entry in observed.read_back.values()} == {"kept"}
    assert worktree.exists()
