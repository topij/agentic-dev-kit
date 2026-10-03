from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

from test_triage_providers import LINEAR_DESTINATION, LinearIssues, LinearTransport  # noqa: E402
from triage import engine as triage_engine  # noqa: E402
from triage.approval import ApprovalContext  # noqa: E402
from triage.canonical import decode_bytes, digest, dumps, encode_bytes, loads_exact  # noqa: E402
from triage.engine import _inline_literal, _report_text, _source_literal, run  # noqa: E402
from triage.finalize import sweep_ids  # noqa: E402
from triage.inbox import parse  # noqa: E402
from triage.model import (  # noqa: E402
    BASE_KEYS,
    CAPABILITIES,
    TriageError,
    canonical_state,
    load_settings,
)
from triage.providers import FakeForge, FakeTracker, ProviderObservation  # noqa: E402


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def repository(tmp_path: Path, *, config_text: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    if config_text is None:
        shutil.copy2(REPO_ROOT / "config/dev-model.yaml", root / "config/dev-model.yaml")
    else:
        (root / "config/dev-model.yaml").write_text(config_text, encoding="utf-8")
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("  engines: scripts/devkit\n", "  engines: scripts\n"), encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/kit-friction-log.md").write_bytes(b"# Log\n\n## 2026-01-02\n\n- **Active defect.** details.\n")
    (root / "docs/kit-friction-log-archive.md").write_text("# Archive\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/triage_friction_log.py").write_text("# engine\n", encoding="utf-8")
    (root / "scripts/finalize_triage.py").write_text("# engine\n", encoding="utf-8")
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")
    git(root, "remote", "add", "origin", "https://github.com/example/project.git")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def request(root: Path) -> dict:
    candidate = parse((root / "docs/kit-friction-log.md").read_bytes())[0]
    return {
        "operator_identity": "operator",
        "proposals": [{
            "candidate_id": candidate.candidate_id,
            "source_block_digest": candidate.digest,
            "title": "Active defect",
            "body_without_marker": "Observed details.",
            "project": "topij/agentic-dev-kit",
            "labels": ["bug"],
        }],
    }


def approval_for(state: dict, command: str = "approve all") -> dict:
    proposal_set_digest = digest(state["proposal_payload_digests"])
    return {
        "command": command,
        "proposal_set_digest": proposal_set_digest,
    }


@pytest.mark.parametrize("adopter_host", [False, True])
def test_linear_approval_and_uncertain_create_resume_keep_frozen_authority(tmp_path, monkeypatch, adopter_host):
    from http.client import IncompleteRead

    if adopter_host:
        host = tmp_path / "adopter"
        (host / "config").mkdir(parents=True)
        (host / "config/dev-model.yaml").write_text(
            'tracker:\n  backend: linear\n  project_name: "Other adopter"\n'
            'review:\n  bots: ["adopter-bot"]\nsystemize:\n  operator_logins: ["adopter-operator"]\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", host)
    # Controlled kit fixture data is installed with these tests; adopter policy
    # is intentionally not a source for the approval and recovery scenario.
    fixture = Path(__file__).parent / "fixtures/init-config.json"
    config_text = "\n".join(json.loads(fixture.read_text(encoding="utf-8"))) + "\n"
    root = repository(tmp_path, config_text=config_text)
    config = root / "config/dev-model.yaml"
    text = config.read_text(encoding="utf-8")
    for old, new in (
        ("backend: github-issues", "backend: linear"),
        ('project_name: "topij/agentic-dev-kit"', 'project_name: "Adopter"'),
        ('url: "https://github.com/topij/agentic-dev-kit/issues"', 'url: "https://linear.app/w/project/p"'),
        ('team_id: ""', 'team_id: "team"'), ('project_id: ""', 'project_id: "project"'),
        ('label_name: ""', 'label_name: "bug"'),
    ):
        assert old in text
        text = text.replace(old, new, 1)
    config.write_text(text, encoding="utf-8")
    git(root, "add", "config/dev-model.yaml")
    git(root, "commit", "-m", "Linear fixture policy")
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    supplied = request(root)
    supplied["proposals"][0]["project"] = "Adopter"
    transport = LinearTransport()
    malformed = {"parent": "teams"}
    def lost_create(query, variables):
        if malformed["parent"] == "protocol":
            raise IncompleteRead(b"partial", 10)
        if "TriageProjectTeams(" in query and malformed["parent"] == "teams":
            return {"data": {"project": ["bad"]}}
        if "TriageIssueLabels(" in query and malformed["parent"] == "labels":
            return {"data": {"issue": ["bad"]}}
        if "TriageCreate(" in query:
            transport.calls.append((query, variables))
            raise IncompleteRead(b"partial", 10)
        return transport(query, variables)
    tracker = LinearIssues(transport=lost_create, sleep=lambda _: None)
    drafted = run("new", context="interactive", request=supplied, start=root, tracker=tracker)
    assert drafted["outcome"] == "operator-held"
    assert transport.calls == []
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    frozen_path = Path(drafted["frozen_snapshot"])
    frozen_bytes = frozen_path.read_bytes()
    refused = run("resume", context="interactive", request={"approval": approval_for(presented)}, start=root,
                  tracker=tracker, approval_context=approval_context(presented, operator="foreign"), head_authority=FakeForge([]))
    assert refused["outcome"] == "operator-held"
    assert transport.calls == []
    malformed_held = run("resume", context="interactive", request={"approval": approval_for(presented)}, start=root,
                         tracker=tracker, approval_context=approval_context(presented), head_authority=FakeForge([]))
    assert malformed_held["outcome"] == "operator-held"
    assert "Linear connection is missing" in malformed_held["detail"]
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert not any("TriageCreate(" in query for query, _ in transport.calls)
    malformed["parent"] = "protocol"
    protocol_held = run("resume", context="interactive", request={}, start=root,
                        tracker=tracker, head_authority=FakeForge([]))
    assert protocol_held["outcome"] == "operator-held"
    assert "Linear API response is unavailable or incomplete" in protocol_held["detail"]
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert not any("TriageCreate(" in query for query, _ in transport.calls)
    malformed["parent"] = None
    held = run("resume", context="interactive", request={}, start=root,
               tracker=tracker, head_authority=FakeForge([]))
    assert held["outcome"] == "operator-held"
    retained = loads_exact(state_path.read_bytes())
    assert retained["operations"][0]["status"] == "ambiguous"
    assert retained["operations"][0]["destination"] == LINEAR_DESTINATION
    creates = sum("TriageCreate(" in q for q, _ in transport.calls)
    run("resume", context="interactive", request={}, start=root, tracker=tracker, head_authority=FakeForge([]))
    assert sum("TriageCreate(" in q for q, _ in transport.calls) == creates
    payload = retained["proposal_payloads"][0]["payload"]
    transport.issues.append({"id": "issue", "identifier": "ADO-17", "url": "https://linear.app/w/issue/ADO-17",
                            "title": payload["title"], "description": payload["body"], "team": {"id": "team"},
                            "project": {"id": "project", "name": "Adopter"}, "labels": [{"id": "label", "name": "bug"}]})
    malformed["parent"] = "labels"
    malformed_held = run("resume", context="interactive", request={}, start=root, tracker=tracker, head_authority=FakeForge([]))
    assert malformed_held["outcome"] == "operator-held"
    assert "Linear connection is missing" in malformed_held["detail"]
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    assert sum("TriageCreate(" in q for q, _ in transport.calls) == creates
    malformed["parent"] = None
    resumed = run("resume", context="interactive", request={}, start=root, tracker=tracker, head_authority=FakeForge([]))
    assert resumed["verified_tracker_identifiers"] == ["ADO-17"]
    assert sum("TriageCreate(" in q for q, _ in transport.calls) == creates
    assert frozen_path.read_bytes() == frozen_bytes
    assert loads_exact(state_path.read_bytes())["proposal_payloads"] == presented["proposal_payloads"]


def approval_context(state: dict, command: str = "approve all", operator: str = "operator") -> ApprovalContext:
    proposal_set_digest = digest(state["proposal_payload_digests"])
    return ApprovalContext(
        "current-session",
        operator,
        {
            "approver_identity": "operator",
            "text": command,
            "proposal_set_digest": proposal_set_digest,
            "payload_digests": state["proposal_payload_digests"],
        },
    )


def plan_in_own_process(root: Path, entry: str = "recover") -> dict:
    """Run an ungated planning call as the CLI does: in its own process.

    Its capture stays bound to that process's gate, and a later approval may act on it
    only once that owner is proven dead (#863). Planning in-process would leave the
    live test process as the owner.
    """
    child = (
        "import sys\nfrom pathlib import Path\nfrom triage.canonical import dumps\n"
        "from triage.engine import run\n"
        "print(dumps(run(sys.argv[2], context='interactive', request={}, start=Path(sys.argv[1]))).decode(), flush=True)\n"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    completed = subprocess.run([sys.executable, "-c", child, str(root), entry], check=True, capture_output=True, text=True, env=environment)
    return loads_exact(completed.stdout.strip().encode())


def recover_dead_valid_gate(root: Path) -> None:
    planned = run("recover", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    core_digest = plan["action_core_digest"]
    supplied = {
        "decision": "approve", "source": "current-session",
        "approver_identity": "operator", "core_digest": core_digest,
    }
    context = ApprovalContext("current-session", "operator", {
        "decision": "approve", "approver_identity": "operator",
        "core_digest": core_digest,
    })
    recovered = run(
        "recover", context="interactive",
        request={"recovery_approval": supplied}, start=root,
        approval_context=context,
    )
    assert recovered["outcome"] == "operator-held"
    assert recovered["detail"] == "resume"


def test_test_mode_completes_without_external_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    inbox_before = (root / "docs/kit-friction-log.md").read_bytes()
    archive_before = (root / "docs/kit-friction-log-archive.md").read_bytes()
    drafted = run("test", context="interactive", request=request(root), start=root)
    assert drafted["outcome"] == "operator-held"
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_test.json"
    presented = loads_exact(state_path.read_bytes())
    result = run("test", context="interactive", request={"approval": approval_for(presented)}, start=root, approval_context=approval_context(presented), head_authority=FakeForge([]))
    assert result["outcome"] == "degraded-success"
    assert result["verified_tracker_identifiers"] == []
    state = loads_exact(state_path.read_bytes())
    assert state["phase"] == "completed"
    assert state["completion"]["route"] == "test-render"
    assert state["operations"][0]["status"] == "would-create"
    proposed_diff = state["completion"]["receipt_core"]["proposed_diff"]
    assert "--- a/docs/kit-friction-log.md" in proposed_diff
    assert "+++ b/docs/kit-friction-log-archive.md" in proposed_diff
    assert "- **Active defect.** details." in proposed_diff
    assert "+- **Active defect.** details." in proposed_diff
    assert (root / "docs/kit-friction-log.md").read_bytes() == inbox_before
    assert (root / "docs/kit-friction-log-archive.md").read_bytes() == archive_before
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "## Proposed source diff" in report
    assert proposed_diff.rstrip() in report
    completed_raw = state_path.read_bytes()
    # A completed test session no longer ends test mode (#425): the next test
    # entry retires it byte-for-byte and starts a fresh test draft.
    restarted = run("test", context="interactive", request={}, start=root)
    assert restarted["outcome"] == "operator-held"
    assert restarted["detail"].startswith("retired completed state to ")
    retired = state_path.with_name(f"{state_path.name}.completed-{state['completion']['completed_receipt_digest'][:16]}")
    assert retired.read_bytes() == completed_raw
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"


def test_report_presents_historical_source_digest_and_safe_literal_fence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    source = (
        "- **Historical entry.** Käyttäjä retained evidence.\n"
        "  **Filed 2026-01-02 as #17, on the operator go-ahead.**\n"
        "  ```markdown\n  ## report-shaped text\n  ```\n"
        "  ~~~\n  archive TRI-01\n  ~~~\n"
    ).encode()
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n" + source
    )
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    candidate = parse((root / "docs/kit-friction-log.md").read_bytes())[0]
    supplied = request(root)
    supplied["proposals"][0]["source_block_digest"] = candidate.digest
    run("new", context="interactive", request=supplied, start=root)
    state = loads_exact(
        (tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes()
    )
    report = Path(state["proposal_payloads"][0]["report_binding"]["path"]).read_text(
        encoding="utf-8"
    )
    assert f"Source-block digest: `{candidate.digest}`" in report
    assert source.decode("utf-8") in report
    assert "````\n" + source.decode("utf-8") in report
    assert "including historically annotated entries" in report
    assert "it does not archive already handled entries" in report


@pytest.mark.parametrize(
    "source",
    [
        b"- **Escape.** before \x1b[2J after.\n",
        b"- **Carriage return.** before\rOVERWRITE.\n",
        b"- **Delete.** before \x7f after.\n",
        "- **C1.** before \u0085 after.\n".encode(),
        "- **Bidi.** before \u202e after.\n".encode(),
        "- **Format.** before \u2066 after.\n".encode(),
    ],
)
def test_source_literal_escapes_terminal_and_unicode_format_controls(source: bytes) -> None:
    rendered, _fence, description = _source_literal(source)
    assert rendered == ascii(source)
    assert "Python bytes literal" in description
    assert all(character.isprintable() or character in "\n\t" for character in rendered)


def test_source_literal_keeps_printable_unicode_lf_tabs_and_safe_fences() -> None:
    source = "Käyttäjä\treads\n```` and ~~~\n".encode()
    rendered, fence, description = _source_literal(source)
    assert rendered == source.decode()
    assert fence == "~~~~"
    assert "printable UTF-8 text with LF/TAB whitespace" in description


def test_complete_report_escapes_controls_but_retains_source_bytes_and_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    source = b"- **Terminal source.** visible \x1b[31mred\x1b[0m.\n"
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n" + source
    )
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    candidate = parse((root / "docs/kit-friction-log.md").read_bytes())[0]
    run("new", context="interactive", request=request(root), start=root)
    state = loads_exact(
        (tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes()
    )
    proposal = state["proposal_payloads"][0]
    report = Path(proposal["report_binding"]["path"]).read_text(encoding="utf-8")
    assert "\x1b" not in report
    assert ascii(source) in report
    assert f"Source-block digest: `{candidate.digest}`" in report
    assert decode_bytes(proposal["source_block"]["source_block"]) == source
    assert proposal["source_block_digest"] == candidate.digest


def test_report_uses_unambiguous_bytes_literal_for_non_utf8_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    source = b"- **Byte entry.** literal \\x41 and invalid \xff.\n"
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n" + source
    )
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("new", context="interactive", request=request(root), start=root)
    state = loads_exact(
        (tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes()
    )
    report = Path(state["proposal_payloads"][0]["report_binding"]["path"]).read_text(
        encoding="utf-8"
    )
    assert "Python bytes literal" in report
    assert ascii(source) in report


CANARY = "FORGED-CANARY"
CONTROL_HOSTILE = f"x\x1b[2J‮ `` ```\n## {CANARY} heading\n<!-- {CANARY} -->\r"
PRINTABLE_HOSTILE = f"`` a`b <!-- {CANARY} --> ## {CANARY} *em* [link](https://example.invalid)"
PRINTABLE_BLOCK_HOSTILE = f"```\n## {CANARY} heading\n<!-- {CANARY} -->\n ```\n~~~~ tail"
REPORT_HEADINGS = [
    "# Triage friction log report",
    "## Capabilities",
    "## Exact proposal payloads",
    "## Tracker operations",
    "## Finalization operations",
    "## Proposed source diff",
]


def hostile_report_state(line: str, block: str) -> dict:
    """Synthetic state whose every report-read string carries ``line`` or ``block``."""
    return {
        "mode": line,
        "engine_mode": line,
        "run_identity": {"session": line, "repository_identity": {"remote": line}},
        "frozen_inbox_digest": line,
        "proposal_payloads": [{
            "candidate_id": line,
            "source_block": {"source_block": encode_bytes(block.encode("utf-8"))},
            "source_block_digest": line,
            "payload_digest": line,
            "payload": {"title": line, "body": block, "project": line, "labels": [line, line + "2"]},
        }],
        "operations": [{"candidate_id": line, "status": line, "returned_identifier": line}],
        "finalization_operations": [
            {
                "kind": "pull-request", "status": "verified",
                "intent": {"base_branch": line, "head": line},
                "read_back": {"baseRefName": line, "headRefOid": line, "url": line},
            },
            {
                "kind": "pr-watch", "status": "verified",
                "intent": {"pr": line, "base_branch": line, "head": line},
                "read_back": {"url": line, "baseRefName": line, "headRefOid": line, "reviewed_head": line, "receipt": {"x": 1}},
            },
        ],
        "completion": {"receipt_core": {"proposed_diff": block}},
    }


def fenced_blocks(report: str) -> tuple[list[str], list[str]]:
    """Split by CommonMark fence rules into (fenced contents, lines outside fences)."""
    blocks: list[str] = []
    outside: list[str] = []
    fence: tuple[str, int] | None = None
    content: list[str] = []
    for line in report.split("\n"):
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.lstrip(" ") if indent <= 3 else ""
        run_char = stripped[:1]
        run_length = len(stripped) - len(stripped.lstrip(run_char)) if run_char in ("`", "~") else 0
        if fence is None:
            if run_length >= 3 and not (run_char == "`" and "`" in stripped[run_length:]):
                fence = (run_char, run_length)
                content = []
            else:
                outside.append(line)
        elif run_char == fence[0] and run_length >= fence[1] and not stripped[run_length:].strip(" \t"):
            blocks.append("\n".join(content))
            fence = None
        else:
            content.append(line)
    assert fence is None, "a fence opened in the report is never closed"
    return blocks, outside


def without_code_spans(line: str) -> str:
    """Remove CommonMark code spans (matching backtick runs) from one line."""
    kept = []
    index = 0
    while index < len(line):
        if line[index] != "`":
            kept.append(line[index])
            index += 1
            continue
        length = len(line[index:]) - len(line[index:].lstrip("`"))
        search = index + length
        closing = -1
        while search < len(line):
            if line[search] != "`":
                search += 1
                continue
            run_length = len(line[search:]) - len(line[search:].lstrip("`"))
            if run_length == length:
                closing = search
                break
            search += run_length
        if closing < 0:
            kept.append(line[index:index + length])
            index += length
        else:
            kept.append("<span>")
            index = closing + length
    return "".join(kept)


@pytest.mark.parametrize(
    ("line", "block"),
    [(CONTROL_HOSTILE, CONTROL_HOSTILE), (PRINTABLE_HOSTILE, PRINTABLE_BLOCK_HOSTILE)],
    ids=["control-bearing", "printable-markup"],
)
def test_report_renders_every_state_value_as_literal_content(line: str, block: str) -> None:
    state = hostile_report_state(line, block)
    capabilities = {name: {"status": line, "mechanism": line} for name in CAPABILITIES}
    report = _report_text(state, capabilities, line).decode("utf-8")

    assert all(character.isprintable() or character == "\n" for character in report)
    blocks, outside = fenced_blocks(report)
    assert blocks == [_source_literal(block.encode("utf-8"))[0]] * 2 + [
        _source_literal(block.rstrip().encode("utf-8"))[0]
    ]
    assert [item for item in outside if item.startswith("#")] == [
        *REPORT_HEADINGS[:3], f"### {_inline_literal(line)}", *REPORT_HEADINGS[3:]
    ]
    assert all(CANARY not in without_code_spans(item) for item in outside)
    assert not any(item.lstrip().startswith("<") for item in outside)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain", "`plain`"),
        ("Käyttäjä", "`Käyttäjä`"),
        ("<!-- c -->", "`<!-- c -->`"),
        ("a`b", "``a`b``"),
        ("`lead", "`` `lead ``"),
        ("trail`", "`` trail` ``"),
        (None, "`None`"),
        (" edge", "`' edge'` (escaped Python string literal)"),
        ("   ", "`'   '` (escaped Python string literal)"),
        ("", "`''` (escaped Python string literal)"),
        (" nbsp", "`'\\xa0nbsp'` (escaped Python string literal)"),
        ("x\ny", "`'x\\ny'` (escaped Python string literal)"),
        ("\x1b[2K`", "``'\\x1b[2K`'`` (escaped Python string literal)"),
    ],
)
def test_inline_literal_is_verbatim_only_for_safe_printable_text(value: object, expected: str) -> None:
    assert _inline_literal(value) == expected


def test_report_shows_payload_body_verbatim_in_a_fence_and_keeps_stored_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    supplied = request(root)
    supplied["proposals"][0]["body_without_marker"] = "Summary.\n\n<!-- hidden? -->\n\n## Not a heading\n```\ncode\n```"
    run("new", context="interactive", request=supplied, start=root)
    state = loads_exact((tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes())
    proposal = state["proposal_payloads"][0]
    body = proposal["payload"]["body"]
    assert body == supplied["proposals"][0]["body_without_marker"] + "\n\n" + proposal["marker"]
    report = Path(proposal["report_binding"]["path"]).read_text(encoding="utf-8")
    fence = _source_literal(body.encode("utf-8"))[1]
    assert "Body (printable UTF-8 text with LF/TAB whitespace;" in report
    assert f"\n{fence}\n{body}\n{fence}\n" in report
    assert "\n## Not a heading" not in report.replace(f"{fence}\n{body}\n{fence}", "")


def test_report_escapes_a_control_bearing_payload_body_but_stores_it_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    supplied = request(root)
    supplied["proposals"][0]["body_without_marker"] = "ok \x1b[8mhidden\x1b[0m\x1b[2K\x1b[1AFAKE"
    supplied["proposals"][0]["title"] = "ok \x1b[8mhidden\x1b[0m"
    run("new", context="interactive", request=supplied, start=root)
    state = loads_exact((tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes())
    proposal = state["proposal_payloads"][0]
    assert proposal["payload"]["title"] == "ok \x1b[8mhidden\x1b[0m"
    assert proposal["payload"]["body"].startswith("ok \x1b[8mhidden\x1b[0m\x1b[2K\x1b[1AFAKE\n\n")
    report = Path(proposal["report_binding"]["path"]).read_text(encoding="utf-8")
    assert "\x1b" not in report
    assert ascii(proposal["payload"]["body"].encode("utf-8")) in report
    assert f"Title: {_inline_literal(proposal['payload']['title'])}" in report
    assert f"Payload digest: `{proposal['payload_digest']}`" in report


def test_proposed_diff_fence_outlasts_a_fence_shaped_context_line() -> None:
    diff = "--- a/log\n+++ b/log\n@@ -1,3 +1,2 @@\n ```\n-- **Entry.**\n ```\n"
    state = {**hostile_report_state("plain", "plain"), "completion": {"receipt_core": {"proposed_diff": diff}}}
    capabilities = {name: {"status": "ready", "mechanism": "fixture"} for name in CAPABILITIES}
    report = _report_text(state, capabilities, "operator-held").decode("utf-8")
    fence = _source_literal(diff.rstrip().encode("utf-8"))[1]
    assert f"\n{fence}diff\n{diff.rstrip()}\n{fence}\n" in report
    assert fenced_blocks(report)[0][-1] == diff.rstrip()


def test_control_bearing_proposed_diff_is_a_literal_without_diff_highlighting() -> None:
    diff = "--- a/log\n+++ b/log\n@@ -1 +0,0 @@\n-- **Entry.** \x1b[2Jhidden\n"
    state = {**hostile_report_state("plain", "plain"), "completion": {"receipt_core": {"proposed_diff": diff}}}
    capabilities = {name: {"status": "ready", "mechanism": "fixture"} for name in CAPABILITIES}
    report = _report_text(state, capabilities, "operator-held").decode("utf-8")
    assert "\x1b" not in report
    assert f"\n```\n{ascii(diff.rstrip().encode('utf-8'))}\n```\n" in report
    assert "```diff" not in report


def presented_live_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, dict]:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    return root, state_path, loads_exact(state_path.read_bytes())


def test_archive_only_approval_without_tracker_reports_tracker_not_triggered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, presented = presented_live_state(tmp_path, monkeypatch)
    command = "archive TRI-01"
    approved = run(
        "resume", context="interactive",
        request={"approval": approval_for(presented, command)}, start=root,
        approval_context=approval_context(presented, command),
    )
    expected = {"status": "not-triggered", "mechanism": "archive-only approval files no tracker payload; continue with finalize"}
    assert approved["outcome"] == "operator-held"
    assert approved["capabilities"]["tracker-write-readback"] == expected
    assert loads_exact(state_path.read_bytes())["phase"] == "tracker-write"
    resumed = run("resume", context="interactive", request={}, start=root)
    assert resumed["outcome"] == "operator-held"
    assert resumed["capabilities"]["tracker-write-readback"] == expected
    report = Path(approved["report"]).read_text(encoding="utf-8")
    assert "archive-only approval files no tracker payload" in report
    assert "requires tracker provider" not in report


def test_filing_approval_without_tracker_still_holds_for_the_tracker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _state_path, presented = presented_live_state(tmp_path, monkeypatch)
    approved = run(
        "resume", context="interactive",
        request={"approval": approval_for(presented)}, start=root,
        approval_context=approval_context(presented),
    )
    assert approved["outcome"] == "operator-held"
    assert approved["capabilities"]["tracker-write-readback"] == {
        "status": "operator-held", "mechanism": "approved payload requires tracker provider",
    }
    resumed = run("resume", context="interactive", request={}, start=root)
    assert resumed["capabilities"]["tracker-write-readback"] == {
        "status": "operator-held", "mechanism": "retained tracker batch requires a read-back provider",
    }


def test_explicit_archive_dispatches_no_tracker_and_implicitly_parks_other_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n"
        b"- **Handled.** details. **Filed 2026-01-02 as #17.**\n"
        b"- **Explicit park.** details.\n"
        b"- **Unmentioned.** details.\n"
    )
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    candidates = parse((root / "docs/kit-friction-log.md").read_bytes())
    supplied = {
        "proposals": [
            {
                "candidate_id": candidate.candidate_id,
                "source_block_digest": candidate.digest,
                "title": f"Candidate {candidate.candidate_id}",
                "body_without_marker": "Observed details.",
                "project": "topij/agentic-dev-kit",
                "labels": ["bug"],
            }
            for candidate in candidates
        ]
    }
    run("new", context="interactive", request=supplied, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    tracker = FakeTracker()
    command = "archive TRI-01"
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(presented, command)},
        start=root,
        tracker=tracker,
        approval_context=approval_context(presented, command),
        head_authority=FakeForge([]),
    )
    assert result["outcome"] == "operator-held"
    assert tracker.calls == []
    retained = loads_exact(state_path.read_bytes())
    assert retained["operations"] == []
    assert [(item["candidate_id"], item["decision"]) for item in retained["decisions"]] == [
        ("TRI-01", "archive"),
        ("TRI-02", "park"),
        ("TRI-03", "park"),
    ]


def test_completed_no_op_cannot_contradict_nonempty_frozen_candidate_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("test", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_test.json"
    reserved = loads_exact(state_path.read_bytes())
    receipt_core = {
        "route": "no-op", "outcome": "successful-completion",
        "run_identity": reserved["run_identity"],
        "frozen_inbox_digest": reserved["frozen_inbox_digest"],
        "candidate_index": [],
    }
    forged = {key: reserved[key] for key in BASE_KEYS}
    forged.update({
        "phase": "completed",
        "completion": {
            "route": "no-op", "outcome": "successful-completion",
            "receipt_core": receipt_core,
            "completed_receipt_digest": digest(receipt_core),
        },
    })
    forged_raw = dumps(forged)
    state_path.write_bytes(forged_raw)
    result = run("test", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "external-attempt-absence-unproven"
    assert state_path.read_bytes() == forged_raw


def test_decision_only_completion_is_durable_without_tracker_or_forge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("new", context="interactive", request=request(root), start=root)
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(presented, "park TRI-01")},
        start=root,
        approval_context=approval_context(presented, "park TRI-01"),
    )
    assert result["outcome"] == "degraded-success"
    retained = loads_exact(state_path.read_bytes())
    assert retained["phase"] == "completed"
    assert retained["completion"]["route"] == "decision-only"
    assert retained["completion"]["receipt_core"]["operations"] == []
    terminal_raw = state_path.read_bytes()
    # A sweep-cleanup record belongs to an archive-sweep completion only (#807).
    tampered = {**retained, "completion": {**retained["completion"], "sweep_cleanup": {
        name: {"result": "absent", "reason": None} for name in ("worktree", "local_branch", "remote_branch")
    }}}
    with pytest.raises(TriageError, match="outside an archive-sweep completion"):
        canonical_state(dumps(tampered), settings=load_settings(root), mode="live")
    resumed = run("resume", context="interactive", request={}, start=root)
    assert resumed["outcome"] == "degraded-success"
    assert resumed["detail"] == "completed/decision-only"
    assert state_path.read_bytes() == terminal_raw
    implicit = run(None, context="interactive", request={}, start=root)
    assert implicit["outcome"] == "operator-held"
    assert implicit["detail"].startswith("retired completed state to ")
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"


def test_one_approval_files_one_candidate_and_archives_another(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#820: a reply carrying both `approve` and `archive` records both decisions, files
    only the approved payload, and leaves the unmentioned entry parked."""
    root = repository(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n"
        b"- **To file.** details.\n"
        b"- **Handled.** details. **Filed 2026-01-02 as #17.**\n"
        b"- **Unmentioned.** details.\n"
    )
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    candidates = parse((root / "docs/kit-friction-log.md").read_bytes())
    supplied = {
        "proposals": [
            {
                "candidate_id": candidate.candidate_id,
                "source_block_digest": candidate.digest,
                "title": f"Candidate {candidate.candidate_id}",
                "body_without_marker": "Observed details.",
                "project": "topij/agentic-dev-kit",
                "labels": ["bug"],
            }
            for candidate in candidates
        ]
    }
    run("new", context="interactive", request=supplied, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    proposal = presented["proposal_payloads"][0]
    assert proposal["candidate_id"] == "TRI-01"
    destination = {"backend": "github-issues", "host": "github.com", "repository": "topij/agentic-dev-kit", "project": "topij/agentic-dev-kit"}
    observed = {"identifier": "40", "payload": proposal["payload"], "payload_digest": proposal["payload_digest"], "marker": proposal["marker"], "destination": destination}
    tracker = FakeTracker([], ProviderObservation("verified", {"number": 40}, observed, "created-and-read-back"))
    command = "approve TRI-01\narchive TRI-02"
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(presented, command)},
        start=root,
        tracker=tracker,
        approval_context=approval_context(presented, command),
        head_authority=FakeForge([]),
    )
    assert result["verified_tracker_identifiers"] == ["40"]
    assert [call[0] for call in tracker.calls] == ["search", "create"]
    assert tracker.calls[1][1]["payload"] == proposal["payload"]
    retained = loads_exact(state_path.read_bytes())
    assert [(item["candidate_id"], item["decision"]) for item in retained["decisions"]] == [
        ("TRI-01", "file"),
        ("TRI-02", "archive"),
        ("TRI-03", "park"),
    ]
    assert retained["approval"]["source_read_back"]["text"] == command
    assert [(item["candidate_id"], item["status"]) for item in retained["operations"]] == [("TRI-01", "verified")]
    assert sweep_ids(retained) == {"TRI-01", "TRI-02"}


def test_live_attempt_is_persisted_before_fake_create(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    read_back = {
        "identifier": "17",
        "payload_digest": "placeholder",
        "marker": "placeholder",
        "destination": {"backend": "github-issues", "host": "github.com", "repository": "topij/agentic-dev-kit", "project": "topij/agentic-dev-kit"},
    }

    class InspectingTracker(FakeTracker):
        def create(self, destination, payload):
            state = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
            assert state["operations"][-1]["status"] == "attempting"
            proposal = state["proposal_payloads"][0]
            observed = {
                **read_back,
                "payload": payload,
                "payload_digest": proposal["payload_digest"],
                "marker": proposal["marker"],
            }
            self.create_observation = ProviderObservation("verified", {"number": 17}, observed, "created-and-read-back")
            return super().create(destination, payload)

    tracker = InspectingTracker()
    run("new", context="interactive", request=request(root), start=root, tracker=tracker)
    assert tracker.calls == []
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    result = run("resume", context="interactive", request={"approval": approval_for(presented)}, start=root, tracker=tracker, approval_context=approval_context(presented), head_authority=FakeForge([]))
    assert result["outcome"] == "operator-held"
    assert result["verified_tracker_identifiers"] == ["17"]
    assert [call[0] for call in tracker.calls] == ["search", "create"]


def test_labels_are_canonical_before_approval_and_changed_readback_cannot_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    supplied = request(root)
    supplied["proposals"][0]["labels"] = ["zeta", "alpha"]
    run("new", context="interactive", request=supplied, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    proposal = presented["proposal_payloads"][0]
    assert proposal["payload"]["labels"] == ["alpha", "zeta"]

    first = FakeTracker([], ProviderObservation("ambiguous", {"accepted": True}, {"effect": "unknown"}))
    run(
        "resume",
        context="interactive",
        request={"approval": approval_for(presented)},
        start=root,
        tracker=first,
        approval_context=approval_context(presented),
        head_authority=FakeForge([]),
    )
    retained = loads_exact(state_path.read_bytes())
    destination = retained["operations"][0]["destination"]
    changed_payload = {**proposal["payload"], "labels": ["alpha", "changed"]}
    changed = {
        "identifier": "17",
        "payload": changed_payload,
        "payload_digest": digest(changed_payload),
        "marker": proposal["marker"],
        "destination": destination,
    }
    refused = run(
        "resume",
        context="interactive",
        request={},
        start=root,
        tracker=FakeTracker([changed]),
        head_authority=FakeForge([]),
    )
    assert refused["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["operations"][0]["status"] == "ambiguous"
    exact = {
        "identifier": "17",
        "payload": proposal["payload"],
        "payload_digest": proposal["payload_digest"],
        "marker": proposal["marker"],
        "destination": destination,
    }
    resumed = run(
        "resume",
        context="interactive",
        request={},
        start=root,
        tracker=FakeTracker([exact]),
        head_authority=FakeForge([]),
    )
    assert resumed["verified_tracker_identifiers"] == ["17"]


def test_unknown_entry_stops_before_repository_probe(tmp_path: Path) -> None:
    result = run("resume new", context="interactive", start=tmp_path)
    assert result["outcome"] == "hard-stop"
    assert result["capabilities"]["repository-config-read"]["status"] == "not-triggered"


@pytest.mark.parametrize(
    ("entry", "context"),
    [([], "interactive"), ("new", []), ({"entry": "new"}, "interactive")],
)
def test_non_string_entry_and_context_enums_hard_stop_before_probe(entry, context) -> None:
    result = run(entry, context=context)
    assert result["outcome"] == "hard-stop"
    assert result["capabilities"]["repository-config-read"]["status"] == "not-triggered"


def test_gate_is_acquired_before_state_or_inbox_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import triage.engine as engine

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    gate_path = state_root / "triage/triage-pipeline-gate_live.lock"
    original_observe = engine.observe
    observed: list[Path] = []

    def observe_after_gate(path: Path, **kwargs):
        assert gate_path.exists()
        observed.append(path)
        return original_observe(path, **kwargs)

    monkeypatch.setattr(engine, "observe", observe_after_gate)
    result = run("new", context="interactive", request=request(root), start=root)
    assert result["outcome"] == "operator-held"
    assert observed[0] == state_root / "triage/triage-pipeline-state_live.json"
    assert root / "docs/kit-friction-log.md" in observed


def test_new_refuses_active_state_and_resume_rebinds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    first = run("test", context="interactive", request=request(root), start=root)
    assert first["outcome"] == "operator-held"
    refused = run("new", context="interactive", request={}, start=root)
    # new is live-isolated and therefore starts a separate live draft rather
    # than observing the existing test session.
    assert refused["outcome"] in {"operator-held", "hard-stop"}
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_test.json"
    presented = loads_exact(state_path.read_bytes())
    resumed = run("test", context="interactive", request={"approval": approval_for(presented)}, start=root, approval_context=approval_context(presented))
    assert resumed["outcome"] == "degraded-success"


def test_new_refuses_live_active_state_without_changing_approval_bound_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    before = state_path.read_bytes()
    refused = run("new", context="interactive", request={}, start=root)
    assert refused["outcome"] == "operator-held"
    assert refused["detail"] == "new refuses to overwrite active state"
    retained = loads_exact(before)
    assert refused["report"] == retained["proposal_payloads"][0]["report_binding"]["path"]
    assert refused["frozen_snapshot"]
    assert state_path.read_bytes() == before


@pytest.mark.parametrize("mutation", ["missing", "malformed", "foreign"])
def test_resume_refuses_invalid_published_frozen_artifact_before_tracker_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    drafted = run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    state_raw = state_path.read_bytes()
    state = loads_exact(state_raw)
    frozen_path = Path(drafted["frozen_snapshot"])
    if mutation == "missing":
        frozen_path.unlink()
    elif mutation == "malformed":
        frozen_path.write_bytes(b"not-json")
    else:
        artifact = loads_exact(frozen_path.read_bytes())
        artifact["run_identity"] = {**artifact["run_identity"], "session": "foreign-session"}
        frozen_path.write_bytes(dumps(artifact))
    tracker = FakeTracker()
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(state)},
        start=root,
        tracker=tracker,
        approval_context=approval_context(state),
        head_authority=FakeForge([]),
    )
    assert result["outcome"] == "hard-stop"
    assert "frozen snapshot artifact" in result["detail"]
    assert tracker.calls == []
    assert state_path.read_bytes() == state_raw


def test_tampered_report_path_cannot_overwrite_unrelated_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    state = loads_exact(state_path.read_bytes())
    victim = tmp_path / "owned-victim.txt"
    victim.write_bytes(b"preserve me")
    binding = {**state["proposal_payloads"][0]["report_binding"], "path": str(victim)}
    state["proposal_payloads"] = [
        {**proposal, "report_binding": binding}
        for proposal in state["proposal_payloads"]
    ]
    tampered_raw = dumps(state)
    state_path.write_bytes(tampered_raw)
    tracker = FakeTracker()
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(state)},
        start=root,
        tracker=tracker,
        approval_context=approval_context(state),
        head_authority=FakeForge([]),
    )
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "proposal report binding mismatch"
    assert victim.read_bytes() == b"preserve me"
    assert tracker.calls == []
    assert state_path.read_bytes() == tampered_raw


@pytest.mark.parametrize("mutation", ["missing-proposal", "forged-marker"])
def test_resume_refuses_incomplete_or_derived_proposal_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    state = loads_exact(state_path.read_bytes())
    if mutation == "missing-proposal":
        state["proposal_payloads"] = []
        state["proposal_payload_digests"] = []
    else:
        proposal = state["proposal_payloads"][0]
        forged_marker = "<!-- triage-payload:foreign:TRI-01:" + proposal["payload_core_digest"] + " -->"
        forged_payload = {**proposal["payload"], "body": proposal["payload_core"]["body_without_marker"] + "\n\n" + forged_marker}
        state["proposal_payloads"] = [{
            **proposal,
            "marker": forged_marker,
            "payload": forged_payload,
            "payload_digest": digest(forged_payload),
        }]
        state["proposal_payload_digests"] = [digest(forged_payload)]
    tampered_raw = dumps(state)
    state_path.write_bytes(tampered_raw)
    tracker = FakeTracker()
    result = run("resume", context="interactive", request={}, start=root, tracker=tracker)
    assert result["outcome"] == "operator-held"
    assert tracker.calls == []
    assert state_path.read_bytes() == tampered_raw


def test_recover_refuses_valid_ungated_state_without_changing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    before = state_path.read_bytes()
    result = run("recover", context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "captured state is valid; recovery refused"
    assert state_path.read_bytes() == before


def test_resume_records_fast_forward_protected_head_without_changing_draft_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    before = loads_exact(state_path.read_bytes())
    (root / "advance").write_text("descendant\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "advance"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "advance"], check=True, capture_output=True)
    current = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "-C", str(root), "update-ref", "refs/remotes/origin/main", current], check=True)
    authority = FakeForge([])
    authority.authority = lambda action, supplied: {
        "draft_head": supplied["draft_head"],
        "observed_head": current,
        "descends_from_draft": True,
    }
    resumed = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(before, "park TRI-01")},
        start=root,
        tracker=FakeTracker(),
        approval_context=approval_context(before, "park TRI-01"),
        head_authority=authority,
    )
    assert resumed["outcome"] == "degraded-success"
    assert resumed["observed_protected_head"] == current
    retained = loads_exact(state_path.read_bytes())
    assert retained["run_identity"]["protected_branch_head"] == before["run_identity"]["protected_branch_head"]
    assert retained["repository_evidence"] == []


@pytest.mark.parametrize("transition", ["divergent", "missing"])
def test_resume_hard_stops_unverifiable_protected_head_before_tracker_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, transition: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    before = state_path.read_bytes()
    presented = loads_exact(before)
    authority = FakeForge([])
    authority.authority = lambda _action, supplied: (
        {"draft_head": supplied["draft_head"], "observed_head": "f" * 40, "descends_from_draft": False}
        if transition == "divergent"
        else {"draft_head": supplied["draft_head"], "observed_head": None, "descends_from_draft": False}
    )
    tracker = FakeTracker()
    result = run(
        "resume",
        context="interactive",
        request={"approval": approval_for(presented)},
        start=root,
        tracker=tracker,
        approval_context=approval_context(presented),
        head_authority=authority,
    )
    assert result["outcome"] == "hard-stop"
    assert tracker.calls == []
    retained = loads_exact(state_path.read_bytes())
    assert retained["phase"] == presented["phase"]
    assert retained["approval"] is None
    assert retained["decisions"] == []
    assert retained["repository_evidence"] == []
    assert retained["pull_request_evidence"] == []


def test_same_call_blanket_approval_cannot_authorize_fresh_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    tracker = FakeTracker()
    unsafe = {**request(root), "approval": {"command": "approve all", "proposal_set_digest": "0" * 64}}
    result = run("new", context="interactive", request=unsafe, start=root, tracker=tracker)
    assert result["outcome"] == "operator-held"
    assert tracker.calls == []


def test_cli_analysis_handoff_freezes_before_runtime_proposals_and_refuses_same_resume_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    drafted = run("new", context="interactive", request={}, start=root)
    assert drafted["outcome"] == "operator-held"
    assert drafted["candidate_index"]
    assert drafted["frozen_snapshot"]
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_live.json"
    reserved = loads_exact(state_path.read_bytes())
    assert reserved["phase"] == "reserved"
    supplied = request(root)
    supplied["approval"] = {"command": "approve all", "proposal_set_digest": "0" * 64}
    resumed = run("resume", context="interactive", request=supplied, start=root)
    assert resumed["outcome"] == "operator-held"
    presented = loads_exact(state_path.read_bytes())
    assert presented["phase"] == "awaiting-approval"
    assert presented["approval"] is None


def test_stale_display_digest_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("test", context="interactive", request=request(root), start=root)
    stale = {"command": "approve all", "proposal_set_digest": "0" * 64}
    state = loads_exact((tmp_path / "state-root/triage/triage-pipeline-state_test.json").read_bytes())
    result = run("test", context="interactive", request={"approval": stale}, start=root, approval_context=approval_context(state))
    assert result["outcome"] == "operator-held"
    assert "not bound" in result["detail"]
    assert result["engine_mode"] == state["engine_mode"]
    assert result["frozen_snapshot"]
    assert result["report"] == state["proposal_payloads"][0]["report_binding"]["path"]


def test_modify_replaces_payload_digest_and_requires_later_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("test", context="interactive", request=request(root), start=root)
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_test.json"
    presented = loads_exact(state_path.read_bytes())
    old_digest = presented["proposal_payload_digests"][0]
    command = "modify TRI-01: replacement, with exact comma"
    result = run(
        "test",
        context="interactive",
        request={"approval": approval_for(presented, command)},
        start=root,
        approval_context=approval_context(presented, command),
    )
    assert result["outcome"] == "operator-held"
    represented = loads_exact(state_path.read_bytes())
    assert represented["phase"] == "awaiting-approval"
    assert represented["approval"] is None
    assert represented["proposal_payload_digests"][0] != old_digest
    assert represented["proposal_payloads"][0]["payload_core"]["body_without_marker"] == "replacement, with exact comma"


@pytest.mark.parametrize("mutation", ["foreign-source", "foreign-operator", "mismatched-text", "malformed-operator"])
def test_modify_requires_trusted_exact_readback_before_state_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("test", context="interactive", request=request(root), start=root)
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_test.json"
    presented_raw = state_path.read_bytes()
    presented = loads_exact(presented_raw)
    command = "modify TRI-01: replacement"
    trusted = approval_context(presented, command)
    if mutation == "foreign-source":
        context = ApprovalContext("foreign", trusted.operator_identity, trusted.source_read_back)
    elif mutation == "foreign-operator":
        context = ApprovalContext(trusted.source, "foreign", trusted.source_read_back)
    elif mutation == "mismatched-text":
        context = ApprovalContext(
            trusted.source,
            trusted.operator_identity,
            {**trusted.source_read_back, "text": "approve all"},
        )
    else:
        context = ApprovalContext(trusted.source, [], trusted.source_read_back)
    result = run(
        "test",
        context="interactive",
        request={"approval": approval_for(presented, command)},
        start=root,
        approval_context=context,
    )
    assert result["outcome"] == "operator-held"
    assert state_path.read_bytes() == presented_raw


def test_request_identity_cannot_replace_trusted_approval_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("test", context="interactive", request=request(root), start=root)
    state = loads_exact((tmp_path / "state-root/triage/triage-pipeline-state_test.json").read_bytes())
    supplied = {"approval": approval_for(state), "operator_identity": "operator", "source": "current-session"}
    foreign = approval_context(state, operator="foreign")
    result = run("test", context="interactive", request=supplied, start=root, approval_context=foreign)
    assert result["outcome"] == "operator-held"
    assert "read-back" in result["detail"]


def test_interactive_recover_routes_gate_only_plan_then_exact_approved_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    child = r'''
import sys, time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings, repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1]))
store=ArtifactStore(settings,'live')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True)
time.sleep(300)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen(
        [sys.executable, "-c", child, str(root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)

    planned = run("recover", context="interactive", request={}, start=root)
    assert planned["outcome"] == "operator-held"
    plan = planned["recovery_plan"]
    assert plan["prepared_core_digest"] == digest(plan["prepared_core"])
    core_digest = plan["prepared_core_digest"]
    recovery_approval = {
        "decision": "approve",
        "source": "current-session",
        "approver_identity": "operator",
        "core_digest": core_digest,
    }
    context = ApprovalContext("current-session", "operator", {
        "decision": "approve",
        "approver_identity": "operator",
        "core_digest": core_digest,
    })
    recovered = run(
        "recover",
        context="interactive",
        request={"recovery_approval": recovery_approval},
        start=root,
        approval_context=context,
    )
    assert recovered["outcome"] == "operator-held"
    held = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert held["kind"] == "gate-only-operator-held"
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()


def test_unattended_initial_and_single_reminder_require_provider_readback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace('user_key: ""', 'user_key: "operator"'), encoding="utf-8")
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))

    class Notification:
        def __init__(self) -> None:
            self.calls = []

        def send_and_read_back(self, target, rendered, marker):
            self.calls.append((target, rendered, marker))
            return ProviderObservation("verified", {"sent": True}, {
                "thread_reference": "thread-17", "marker": marker, "target": target,
                "rendered_payload": rendered, "rendered_payload_digest": digest(rendered),
                "match_count": 1,
            })

    notification = Notification()
    drafted = run("new", context="unattended", request=request(root), start=root, notification=notification)
    assert drafted["outcome"] == "operator-held"
    assert len(notification.calls) == 1
    reminded = run("resume", context="unattended", request={}, start=root, notification=notification)
    assert reminded["outcome"] == "operator-held"
    assert len(notification.calls) == 2
    retained = loads_exact((tmp_path / "state-root/triage/triage-pipeline-state_live.json").read_bytes())
    assert [operation["kind"] for operation in retained["notification_operations"]] == ["initial", "reminder"]
    run("resume", context="unattended", request={}, start=root, notification=notification)
    assert len(notification.calls) == 2


def test_retained_notification_delivery_resumes_by_readback_without_resend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace('user_key: ""', 'user_key: "operator"'), encoding="utf-8")
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))

    class Notification:
        def __init__(self) -> None:
            self.sends = 0
            self.reads = 0

        def send_and_read_back(self, target, rendered, marker):
            self.sends += 1
            return ProviderObservation("ambiguous", {"accepted": True}, {"effect": "unknown"})

        def read_back(self, target, rendered, marker):
            self.reads += 1
            return ProviderObservation("verified", None, {
                "thread_reference": "thread-17", "marker": marker, "target": target,
                "rendered_payload": rendered, "rendered_payload_digest": digest(rendered),
                "match_count": 1,
            })

    notification = Notification()
    first = run("new", context="unattended", request=request(root), start=root, notification=notification)
    assert first["outcome"] == "operator-held"
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    assert loads_exact(state_path.read_bytes())["phase"] == "notification-delivery"
    resumed = run("resume", context="interactive", request={}, start=root, notification=notification)
    assert resumed["outcome"] == "operator-held"
    assert notification.sends == 1 and notification.reads == 1
    assert loads_exact(state_path.read_bytes())["phase"] == "awaiting-approval"


@pytest.mark.parametrize("mutation", ["target", "rendered-payload"])
def test_notification_verified_claim_requires_exact_visible_message_and_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    root = repository(tmp_path)
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace('user_key: ""', 'user_key: "operator"'), encoding="utf-8")
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))

    class Notification:
        @staticmethod
        def send_and_read_back(target, rendered, marker):
            observed_target = "foreign" if mutation == "target" else target
            observed_rendered = "changed" if mutation == "rendered-payload" else rendered
            return ProviderObservation("verified", {"sent": True}, {
                "thread_reference": "thread-17", "marker": marker,
                "target": observed_target, "rendered_payload": observed_rendered,
                "rendered_payload_digest": digest(observed_rendered), "match_count": 1,
            })

    result = run("new", context="unattended", request=request(root), start=root, notification=Notification())
    assert result["outcome"] == "operator-held"
    retained = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert retained["phase"] == "notification-delivery"
    assert retained["notification_operations"][0]["status"] == "ambiguous"


def test_notification_dispatch_process_loss_recovers_gate_and_reconciles_without_resend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace('user_key: ""', 'user_key: "operator"'), encoding="utf-8")
    state_root = tmp_path / "state-root"
    destination = tmp_path / "notification-destination.json"
    marker_path = tmp_path / "notification-dispatched"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    child = r'''
import os,sys,time
from pathlib import Path
from triage.canonical import digest,dumps
from triage.engine import run
class Notification:
 def send_and_read_back(self,target,rendered,marker):
  record={"thread_reference":"thread-17","marker":marker,"target":target,"rendered_payload":rendered,"rendered_payload_digest":digest(rendered),"match_count":1}
  path=Path(sys.argv[2]); path.write_bytes(dumps([record]));
  with path.open('rb') as stream: os.fsync(stream.fileno())
  Path(sys.argv[3]).write_text('ready'); time.sleep(300)
run('new',context='unattended',request={"proposals":[{"candidate_id":"TRI-01","source_block_digest":__import__('triage.inbox',fromlist=['parse']).parse((Path(sys.argv[1])/'docs/kit-friction-log.md').read_bytes())[0].digest,"title":"Active defect","body_without_marker":"Observed details.","project":"topij/agentic-dev-kit","labels":["bug"]}]},start=Path(sys.argv[1]),notification=Notification())
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen(
        [sys.executable, "-c", child, str(root), str(destination), str(marker_path)],
        env=environment,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker_path.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    crashed = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    notification_operation = crashed["notification_operations"][0]
    assert notification_operation["status"] == "attempting"
    assert notification_operation["attempts"][-1]["status"] == "attempting"
    recover_dead_valid_gate(root)

    restart_child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps,loads_exact
from triage.engine import run
from triage.providers import ProviderObservation
class Notification:
 def send_and_read_back(self,*_args): raise AssertionError('reconciliation must not resend')
 def read_back(self,*_args):
  records=loads_exact(Path(sys.argv[2]).read_bytes()); assert len(records)==1
  return ProviderObservation('verified',None,records[0])
print(dumps(run('resume',context='interactive',request={},start=Path(sys.argv[1]),notification=Notification())).decode(),flush=True)
'''
    restarted = subprocess.run(
        [sys.executable, "-c", restart_child, str(root), str(destination)],
        check=True, capture_output=True, text=True, env=environment,
    )
    resumed = loads_exact(restarted.stdout.strip().encode())
    assert resumed["outcome"] == "operator-held"
    assert len(loads_exact(destination.read_bytes())) == 1
    retained = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert retained["phase"] == "awaiting-approval"


def test_retained_tracker_prefix_reconciles_and_continues_without_reset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    (root / "docs/kit-friction-log.md").write_bytes(
        b"# Log\n\n## 2026-01-02\n\n- **First.** one.\n\n- **Second.** two.\n\n- **Third.** three.\n"
    )
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    candidates = parse((root / "docs/kit-friction-log.md").read_bytes())
    supplied = {
        "proposals": [{
            "candidate_id": candidate.candidate_id,
            "source_block_digest": candidate.digest,
            "title": candidate.title,
            "body_without_marker": candidate.raw.decode(),
            "project": "topij/agentic-dev-kit",
            "labels": ["bug"],
        } for candidate in candidates]
    }

    class FirstTracker:
        def __init__(self) -> None:
            self.creates = 0

        def search(self, destination, marker):
            return []

        def create(self, destination, payload):
            self.creates += 1
            marker = next(line for line in payload["body"].splitlines() if "triage-payload:" in line)
            read_back = {"identifier": str(self.creates), "payload": payload, "payload_digest": digest(payload), "marker": marker, "destination": destination}
            return ProviderObservation("verified" if self.creates == 1 else "ambiguous", {"number": self.creates} if self.creates == 1 else None, read_back if self.creates == 1 else {"effect": "unknown"}, "created-and-read-back" if self.creates == 1 else None)

    run("new", context="interactive", request=supplied, start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    first_tracker = FirstTracker()
    run("resume", context="interactive", request={"approval": approval_for(presented)}, start=root, tracker=first_tracker, approval_context=approval_context(presented), head_authority=FakeForge([]))
    partial = loads_exact(state_path.read_bytes())
    assert [item["status"] for item in partial["operations"]] == ["verified", "ambiguous"]

    class ResumeTracker:
        def __init__(self) -> None:
            self.searches = 0
            self.creates = 0

        @staticmethod
        def exact(destination, proposal, identifier):
            return {"identifier": identifier, "payload": proposal["payload"], "payload_digest": proposal["payload_digest"], "marker": proposal["marker"], "destination": destination}

        def search(self, destination, marker):
            self.searches += 1
            if self.searches == 1:
                proposal = partial["proposal_payloads"][1]
                return [self.exact(destination, proposal, "2")]
            return []

        def create(self, destination, payload):
            self.creates += 1
            proposal = partial["proposal_payloads"][2]
            return ProviderObservation("verified", {"number": 3}, self.exact(destination, proposal, "3"), "created-and-read-back")

    resumed_tracker = ResumeTracker()
    resumed = run("resume", context="interactive", request={}, start=root, tracker=resumed_tracker, head_authority=FakeForge([]))
    assert resumed["outcome"] == "operator-held"
    completed_prefix = loads_exact(state_path.read_bytes())
    assert [item["returned_identifier"] for item in completed_prefix["operations"]] == ["1", "2", "3"]
    assert resumed_tracker.searches == 2 and resumed_tracker.creates == 1


def test_tracker_dispatch_process_loss_recovers_gate_and_reconciles_without_duplicate_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    destination = tmp_path / "tracker-destination.json"
    marker_path = tmp_path / "tracker-dispatched"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    child = r'''
import os,sys,time
from pathlib import Path
from triage.approval import ApprovalContext
from triage.canonical import digest,dumps,loads_exact
from triage.engine import run
state=loads_exact((Path(os.environ['DEVKIT_STATE_ROOT'])/'triage/triage-pipeline-state_live.json').read_bytes())
set_digest=digest(state['proposal_payload_digests'])
approval={"command":"approve all","proposal_set_digest":set_digest}
context=ApprovalContext('current-session','operator',{"approver_identity":"operator","text":"approve all","proposal_set_digest":set_digest,"payload_digests":state['proposal_payload_digests']})
class Head:
 def authority(self,action,request): return {"draft_head":request['draft_head'],"observed_head":request['draft_head'],"descends_from_draft":True}
class Tracker:
 def search(self,destination,marker): return []
 def create(self,destination,payload):
  marker=next(line for line in payload['body'].splitlines() if 'triage-payload:' in line)
  record={"identifier":"17","payload":payload,"payload_digest":digest(payload),"marker":marker,"destination":destination}
  path=Path(sys.argv[2]); path.write_bytes(dumps([record]));
  with path.open('rb') as stream: os.fsync(stream.fileno())
  Path(sys.argv[3]).write_text('ready'); time.sleep(300)
run('resume',context='interactive',request={"approval":approval},start=Path(sys.argv[1]),tracker=Tracker(),approval_context=context,head_authority=Head())
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen(
        [sys.executable, "-c", child, str(root), str(destination), str(marker_path)],
        env=environment,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker_path.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    crashed = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert crashed["operations"][0]["status"] == "attempting"
    assert crashed["attempts"][-1]["status"] == "attempting"
    recover_dead_valid_gate(root)

    restart_child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps,loads_exact
from triage.engine import run
class Head:
 def authority(self,action,request): return {"draft_head":request['draft_head'],"observed_head":request['draft_head'],"descends_from_draft":True}
class Tracker:
 def search(self,_destination,_marker):
  records=loads_exact(Path(sys.argv[2]).read_bytes()); assert len(records)==1; return records
 def create(self,*_args): raise AssertionError('reconciliation must not create again')
print(dumps(run('resume',context='interactive',request={},start=Path(sys.argv[1]),tracker=Tracker(),head_authority=Head())).decode(),flush=True)
'''
    restarted = subprocess.run(
        [sys.executable, "-c", restart_child, str(root), str(destination)],
        check=True, capture_output=True, text=True, env=environment,
    )
    resumed = loads_exact(restarted.stdout.strip().encode())
    assert resumed["outcome"] == "operator-held"
    assert len(loads_exact(destination.read_bytes())) == 1
    retained = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert retained["operations"][0]["status"] == "verified"
    assert retained["operations"][0]["verified_route"] == "ambiguous-response-then-exact-read-back"


def test_invalid_ungated_test_state_uses_exact_interactive_recovery_and_unattended_preserves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    test_state = state_root / "triage/triage-pipeline-state_test.json"
    run("test", context="interactive", request={}, start=root)
    abandonable = loads_exact(test_state.read_bytes())
    abandonable["phase"] = "unknown-phase"
    invalid = dumps(abandonable)
    test_state.write_bytes(invalid)
    unattended = run("test", context="unattended", request={}, start=root)
    assert unattended["outcome"] == "operator-held"
    assert test_state.read_bytes() == invalid
    child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps
from triage.engine import run
print(dumps(run('test',context='interactive',request={},start=Path(sys.argv[1]))).decode(),flush=True)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    planned_process = subprocess.run(
        [sys.executable, "-c", child, str(root)], check=True,
        capture_output=True, text=True, env=environment,
    )
    planned = loads_exact(planned_process.stdout.strip().encode())
    core_digest = planned["recovery_plan"]["action_core_digest"]
    supplied = {
        "decision": "approve", "source": "current-session",
        "approver_identity": "operator", "core_digest": core_digest,
    }
    context = ApprovalContext("current-session", "operator", {
        "decision": "approve", "approver_identity": "operator", "core_digest": core_digest,
    })
    recovered = run(
        "test", context="interactive", request={"recovery_approval": supplied},
        start=root, approval_context=context,
    )
    assert recovered["outcome"] == "operator-held"
    receipt = loads_exact(test_state.read_bytes())
    assert receipt["kind"] == "test-recovered-safe-to-restart"
    assert not (state_root / "triage/triage-pipeline-state_live.json").exists()
    malformed_receipt = {**receipt, "old_gate_digest": []}
    malformed_raw = dumps(malformed_receipt)
    test_state.write_bytes(malformed_raw)
    malformed_result = run("test", context="interactive", request={}, start=root)
    assert malformed_result["outcome"] == "operator-held"
    assert malformed_result["detail"] == "safe-restart receipt has malformed fields"
    assert test_state.read_bytes() == malformed_raw
    test_state.write_bytes(dumps(receipt))
    restarted = run("test", context="interactive", request={}, start=root)
    assert restarted["outcome"] == "operator-held"
    restarted_state = loads_exact(test_state.read_bytes())
    assert restarted_state["phase"] == "reserved"
    assert restarted_state["state_claim"]["reason"] == "test-receipt-restart"


def test_non_string_persisted_phase_is_held_without_uncaught_type_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("test", context="interactive", request={}, start=root)
    state_path = state_root / "triage/triage-pipeline-state_test.json"
    malformed = loads_exact(state_path.read_bytes())
    malformed["phase"] = ["reserved"]
    malformed_raw = dumps(malformed)
    state_path.write_bytes(malformed_raw)
    result = run("test", context="unattended", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"] == "invalid test state preserved without unattended recovery"
    assert state_path.read_bytes() == malformed_raw


@pytest.mark.parametrize("state_kind", ["malformed", "valid", "safe-restart-receipt"])
def test_blocking_test_gate_with_state_publishes_only_approved_terminal_held_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state_kind: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    state = state_root / "triage/triage-pipeline-state_test.json"
    if state_kind == "valid":
        run("test", context="interactive", request=request(root), start=root)
        artifact = state.read_bytes()
    elif state_kind == "safe-restart-receipt":
        run("test", context="interactive", request={}, start=root)
        invalid = loads_exact(state.read_bytes())
        invalid["phase"] = "unknown-phase"
        state.write_bytes(dumps(invalid))
        recovery_plan = plan_in_own_process(root, "test")["recovery_plan"]
        recovery_digest = recovery_plan["action_core_digest"]
        supplied_recovery = {
            "decision": "approve",
            "source": "current-session",
            "approver_identity": "operator",
            "core_digest": recovery_digest,
        }
        recovery_context = ApprovalContext(
            "current-session",
            "operator",
            {
                "decision": "approve",
                "approver_identity": "operator",
                "core_digest": recovery_digest,
            },
        )
        recovered = run(
            "test",
            context="interactive",
            request={"recovery_approval": supplied_recovery},
            start=root,
            approval_context=recovery_context,
        )
        assert recovered["detail"] == "test-recovered-safe-to-restart"
        artifact = state.read_bytes()
    else:
        artifact = b'{"malformed":"but preserved"}'
    child = r'''
import sys, time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings, repository_identity
from triage.storage import ArtifactStore, exclusive_create
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'test')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
if not store.state_path.exists(): exclusive_create(store.state_path,bytes.fromhex(sys.argv[2]))
print('ready',flush=True); time.sleep(300)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen([sys.executable, "-c", child, str(root), artifact.hex()], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
    try:
        assert process.stdout is not None and process.stdout.readline().strip() == "ready"
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    gate = state_root / "triage/triage-pipeline-gate_test.lock"
    gate_before, state_before = gate.read_bytes(), state.read_bytes()

    planned = run("test", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    assert plan["capture_core_digest"] == digest(plan["capture_core"])
    assert gate.read_bytes() == gate_before and state.read_bytes() == state_before
    core_digest = plan["capture_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = ApprovalContext("current-session", "operator", {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest})
    held = run("test", context="interactive", request={"recovery_approval": supplied}, start=root, approval_context=context)
    assert held["outcome"] == "operator-held"
    assert gate.read_bytes() == gate_before and state.read_bytes() == state_before
    bundles = list((state_root / "triage").glob("recovery-bundle_test_*.json"))
    held_bundles = [
        bundle
        for bundle in bundles
        if loads_exact(bundle.read_bytes())["kind"] == "state-present-test-gate-held"
    ]
    assert len(held_bundles) == 1


def test_blocking_test_gate_with_absent_state_resumes_exact_approved_gate_only_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    child = r'''
import sys,time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings,repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'test')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True); time.sleep(300)
'''
    owner = subprocess.Popen(
        [sys.executable, "-c", child, str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment,
    )
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if owner.poll() is None:
            owner.terminate()
        owner.wait(timeout=10)
    planned = run("test", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    core_digest = plan["prepared_core_digest"]
    supplied = {
        "decision": "approve", "source": "current-session",
        "approver_identity": "operator", "core_digest": core_digest,
    }
    context = ApprovalContext("current-session", "operator", {
        "decision": "approve", "approver_identity": "operator", "core_digest": core_digest,
    })
    held = run(
        "test", context="interactive", request={"recovery_approval": supplied},
        start=root, approval_context=context,
    )
    assert held["outcome"] == "operator-held"
    receipt = loads_exact(
        (state_root / "triage/triage-pipeline-state_test.json").read_bytes()
    )
    assert receipt["kind"] == "gate-only-operator-held"
    assert not (state_root / "triage/triage-pipeline-gate_test.lock").exists()


@pytest.mark.parametrize(
    "cutpoint",
    ["prepared", "intent", "old-quarantine", "replacement-gate", "held-receipt", "released"],
)
def test_gate_only_transition_restarts_from_each_durable_cutpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cutpoint: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    owner_child = r'''
import sys,time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings,repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'live')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True); time.sleep(300)
'''
    owner = subprocess.Popen(
        [sys.executable, "-c", owner_child, str(root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if owner.poll() is None:
            owner.terminate()
        owner.wait(timeout=10)

    planned = run("recover", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    core_digest = plan["prepared_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context_value = {
        "source": "current-session",
        "operator_identity": "operator",
        "source_read_back": {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest},
    }
    marker = tmp_path / f"gate-only-{cutpoint}"
    transition_child = r'''
import sys,time
from pathlib import Path
import triage.gate as gate
import triage.recovery as recovery
from triage.approval import ApprovalContext
from triage.canonical import loads_exact
from triage.engine import run
root=Path(sys.argv[1]); marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
request=loads_exact(bytes.fromhex(sys.argv[4])); context=ApprovalContext(**loads_exact(bytes.fromhex(sys.argv[5])))
def stop(name):
    if cutpoint == name:
        marker.write_text(name); time.sleep(300)
original_create=recovery.exclusive_create
def controlled_create(path,raw):
    result=original_create(path,raw)
    if b'"kind":"gate-only-prepared"' in raw: stop('prepared')
    if path.name == 'triage-pipeline-state_live.json' and b'"kind":"gate-only-recovery-intent"' in raw: stop('intent')
    return result
recovery.exclusive_create=controlled_create
original_quarantine=recovery._quarantine_group
def controlled_quarantine(*args,**kwargs):
    result=original_quarantine(*args,**kwargs); stop('old-quarantine'); return result
recovery._quarantine_group=controlled_quarantine
original_acquire=recovery.acquire
def controlled_acquire(*args,**kwargs):
    result=original_acquire(*args,**kwargs); stop('replacement-gate'); return result
recovery.acquire=controlled_acquire
original_replace=recovery.atomic_replace
def controlled_replace(path,raw,**kwargs):
    result=original_replace(path,raw,**kwargs)
    if b'"kind":"gate-only-operator-held"' in raw: stop('held-receipt')
    return result
recovery.atomic_replace=controlled_replace
original_release=gate.GateLease.release
def controlled_release(self):
    result=original_release(self); stop('released'); return result
gate.GateLease.release=controlled_release
run('recover',context='interactive',request=request,start=root,approval_context=context)
'''
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            transition_child,
            str(root),
            str(marker),
            cutpoint,
            dumps({"recovery_approval": supplied}).hex(),
            dumps(context_value).hex(),
        ],
        env=environment,
    )
    import time

    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    gate_path = state_root / "triage/triage-pipeline-gate_live.lock"
    stale_gate = gate_path.read_bytes() if gate_path.exists() else None

    if cutpoint == "intent":
        state_path = state_root / "triage/triage-pipeline-state_live.json"
        intent_before = state_path.read_bytes()
        assert stale_gate is not None
        ordinary = run("resume", context="interactive", request={}, start=root)
        assert ordinary["outcome"] == "operator-held"
        assert state_path.read_bytes() == intent_before
        assert gate_path.read_bytes() == stale_gate
        unattended = run(None, context="unattended", request={}, start=root)
        assert unattended["outcome"] == "operator-held"
        assert state_path.read_bytes() == intent_before
        assert gate_path.read_bytes() == stale_gate

    restart_child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps
from triage.engine import run
print(dumps(run('recover',context='interactive',request={},start=Path(sys.argv[1]))).decode(),flush=True)
'''
    restarted_process = subprocess.run(
        [sys.executable, "-c", restart_child, str(root)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    restarted = loads_exact(restarted_process.stdout.strip().encode())
    assert restarted["outcome"] == "operator-held"
    receipt = loads_exact((state_root / "triage/triage-pipeline-state_live.json").read_bytes())
    assert receipt["kind"] == "gate-only-operator-held"
    if cutpoint == "held-receipt":
        assert stale_gate is not None and gate_path.read_bytes() == stale_gate
    else:
        assert not gate_path.exists()


def test_test_mode_gate_only_intent_blocks_unattended_work_then_resumes_interactively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    owner_child = r'''
import sys,time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings,repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'test')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True); time.sleep(300)
'''
    owner = subprocess.Popen(
        [sys.executable, "-c", owner_child, str(root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if owner.poll() is None:
            owner.terminate()
        owner.wait(timeout=10)
    planned = run("test", context="interactive", request={}, start=root)
    core_digest = planned["recovery_plan"]["prepared_core_digest"]
    supplied = {
        "decision": "approve",
        "source": "current-session",
        "approver_identity": "operator",
        "core_digest": core_digest,
    }
    context_value = {
        "source": "current-session",
        "operator_identity": "operator",
        "source_read_back": {
            "decision": "approve",
            "approver_identity": "operator",
            "core_digest": core_digest,
        },
    }
    marker = tmp_path / "test-intent"
    transition_child = r'''
import sys,time
from pathlib import Path
import triage.recovery as recovery
from triage.approval import ApprovalContext
from triage.canonical import loads_exact
from triage.engine import run
root=Path(sys.argv[1]); marker=Path(sys.argv[2])
request=loads_exact(bytes.fromhex(sys.argv[3])); context=ApprovalContext(**loads_exact(bytes.fromhex(sys.argv[4])))
original=recovery.exclusive_create
def controlled(path,raw):
 result=original(path,raw)
 if path.name == 'triage-pipeline-state_test.json' and b'"kind":"test-gate-recovery-intent"' in raw:
  marker.write_text('intent'); time.sleep(300)
 return result
recovery.exclusive_create=controlled
run('test',context='interactive',request=request,start=root,approval_context=context)
'''
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            transition_child,
            str(root),
            str(marker),
            dumps({"recovery_approval": supplied}).hex(),
            dumps(context_value).hex(),
        ],
        env=environment,
    )
    import time

    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    gate_path = state_root / "triage/triage-pipeline-gate_test.lock"
    state_path = state_root / "triage/triage-pipeline-state_test.json"
    gate_before, state_before = gate_path.read_bytes(), state_path.read_bytes()
    unattended = run("test", context="unattended", request={}, start=root)
    assert unattended["outcome"] == "operator-held"
    assert gate_path.read_bytes() == gate_before
    assert state_path.read_bytes() == state_before
    resumed = run("test", context="interactive", request={}, start=root)
    assert resumed["outcome"] == "operator-held"
    assert resumed["detail"] == "gate-only-operator-held"
    assert not gate_path.exists()


@pytest.mark.parametrize("cutpoint", ["before-rebind", "after-rebind"])
def test_fresh_process_restart_across_normal_resume_rebind_cutpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cutpoint: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    old_raw = state_path.read_bytes()
    marker = tmp_path / "rebind-cutpoint"
    child = r'''
import sys, time
from pathlib import Path
import triage.engine as engine
original=engine.atomic_replace; marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
def controlled(path, raw, **kwargs):
    is_rebind=b'"reason":"normal-resume"' in raw
    if is_rebind and cutpoint=='before-rebind': marker.write_text('ready'); time.sleep(300)
    result=original(path,raw,**kwargs)
    if is_rebind and cutpoint=='after-rebind': marker.write_text('ready'); time.sleep(300)
    return result
engine.atomic_replace=controlled
engine.run('resume',context='interactive',request={},start=Path(sys.argv[1]))
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen([sys.executable, "-c", child, str(root), str(marker), cutpoint], env=environment)
    import time

    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    if cutpoint == "before-rebind":
        assert state_path.read_bytes() == old_raw
    else:
        assert loads_exact(state_path.read_bytes())["state_claim"]["reason"] == "normal-resume"

    planned = run("recover", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    assert plan["action_core"]["action"] == "preserve-valid-state-and-quarantine-old-gate"
    core_digest = plan["action_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = ApprovalContext("current-session", "operator", {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest})
    released = run("recover", context="interactive", request={"recovery_approval": supplied}, start=root, approval_context=context)
    assert released["outcome"] == "operator-held"
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    resumed = run("resume", context="interactive", request={}, start=root)
    assert resumed["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["phase"] == "awaiting-approval"


def test_invalid_state_recovery_and_receipt_restart_cross_fresh_processes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from triage.model import load_settings, new_run_identity, state_base
    from triage.storage import ArtifactStore, exclusive_create

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    configured = load_settings(root)
    store = ArtifactStore(configured, "live")
    identity = new_run_identity(configured, "live", session="invalid-recovery-session")
    binding = {"gate_path": str(store.gate_path), "owner_token": "old-owner", "owner_run_identity": None, "gate_claim_core_digest": "4" * 64}
    invalid = state_base(identity, binding, {
        "reason": "initial-reservation",
        "previous_gate_binding": None,
        "current_gate_binding": binding,
        "captured_state_digest": None,
        "recovery_bundle_digest": None,
        "approval_digest": None,
    }, "5" * 64, {}, "engine-backed")
    invalid["phase"] = "unknown"
    exclusive_create(store.state_path, dumps(invalid))
    child = r'''
import sys
from pathlib import Path
from triage.approval import ApprovalContext
from triage.canonical import dumps, loads_exact
from triage.engine import run
request=loads_exact(bytes.fromhex(sys.argv[3]))
context_value=loads_exact(bytes.fromhex(sys.argv[4])) if sys.argv[4] != '-' else None
context=ApprovalContext(**context_value) if context_value is not None else None
print(dumps(run(sys.argv[2],context='interactive',request=request,start=Path(sys.argv[1]),approval_context=context)).decode(),flush=True)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)

    def invoke(entry: str, supplied: dict, context: dict | None = None) -> dict:
        result = subprocess.run(
            [sys.executable, "-c", child, str(root), entry, dumps(supplied).hex(), dumps(context).hex() if context else "-"],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return loads_exact(result.stdout.strip().encode())

    planned = invoke("recover", {})
    plan = planned["recovery_plan"]
    assert plan["action_core"]["action"] == "abandon-invalid-state"
    core_digest = plan["action_core_digest"]
    approval = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = {"source": "current-session", "operator_identity": "operator", "source_read_back": {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest}}
    recovered = invoke("recover", {"recovery_approval": approval}, context)
    assert recovered["outcome"] == "operator-held"
    receipt = loads_exact(store.state_path.read_bytes())
    assert receipt["kind"] == "recovered-safe-to-restart"
    restarted = invoke("new", request(root))
    assert restarted["outcome"] == "operator-held"
    assert loads_exact(store.state_path.read_bytes())["phase"] == "awaiting-approval"


@pytest.mark.parametrize("cutpoint", ["prepared", "state-quarantine", "receipt", "gate-quarantine"])
def test_invalid_state_recovery_restarts_at_internal_durable_cutpoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cutpoint: str
) -> None:
    from triage.model import load_settings, new_run_identity, state_base
    from triage.storage import ArtifactStore, exclusive_create

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    configured = load_settings(root)
    store = ArtifactStore(configured, "live")
    identity = new_run_identity(configured, "live", session="invalid-cutpoint-session")
    binding = {"gate_path": str(store.gate_path), "owner_token": "old-owner", "owner_run_identity": None, "gate_claim_core_digest": "4" * 64}
    invalid = state_base(identity, binding, {
        "reason": "initial-reservation",
        "previous_gate_binding": None,
        "current_gate_binding": binding,
        "captured_state_digest": None,
        "recovery_bundle_digest": None,
        "approval_digest": None,
    }, "5" * 64, {}, "engine-backed")
    invalid["phase"] = "unknown"
    exclusive_create(store.state_path, dumps(invalid))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    owner_child = r'''
import sys,time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings,repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'live')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True); time.sleep(300)
'''
    owner = subprocess.Popen([sys.executable, "-c", owner_child, str(root)], stdout=subprocess.PIPE, text=True, env=environment)
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if owner.poll() is None:
            owner.terminate()
        owner.wait(timeout=10)
    planned = run("recover", context="interactive", request={}, start=root)
    plan = planned["recovery_plan"]
    core_digest = plan["action_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context_value = {"source": "current-session", "operator_identity": "operator", "source_read_back": {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest}}
    marker = tmp_path / cutpoint
    child = r'''
import sys,time
from pathlib import Path
import triage.recovery as recovery
from triage.approval import ApprovalContext
from triage.canonical import loads_exact
from triage.engine import run
root=Path(sys.argv[1]); marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
request=loads_exact(bytes.fromhex(sys.argv[4])); context=ApprovalContext(**loads_exact(bytes.fromhex(sys.argv[5])))
def stop(name):
    if cutpoint == name: marker.write_text(name); time.sleep(300)
original_replace=recovery.atomic_replace
def controlled_replace(path,raw,**kwargs):
    result=original_replace(path,raw,**kwargs)
    if b'"kind":"state-present-prepared"' in raw: stop('prepared')
    return result
recovery.atomic_replace=controlled_replace
original_quarantine=recovery._quarantine
def controlled_quarantine(path,*args,**kwargs):
    result=original_quarantine(path,*args,**kwargs)
    stop('state-quarantine' if 'state_' in path.name else 'gate-quarantine')
    return result
recovery._quarantine=controlled_quarantine
original_create=recovery.exclusive_create
def controlled_create(path,raw,*args,**kwargs):
    result=original_create(path,raw,*args,**kwargs)
    if b'"kind":"recovered-safe-to-restart"' in raw: stop('receipt')
    return result
recovery.exclusive_create=controlled_create
run('recover',context='interactive',request=request,start=root,approval_context=context)
'''
    process = subprocess.Popen([
        sys.executable, "-c", child, str(root), str(marker), cutpoint,
        dumps({"recovery_approval": supplied}).hex(), dumps(context_value).hex(),
    ], env=environment)
    import time

    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    restart_child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps
from triage.engine import run
print(dumps(run('recover',context='interactive',request={},start=Path(sys.argv[1]))).decode(),flush=True)
'''
    restarted = subprocess.run([sys.executable, "-c", restart_child, str(root)], check=True, capture_output=True, text=True, env=environment)
    result = loads_exact(restarted.stdout.strip().encode())
    assert result["outcome"] == "operator-held"
    assert loads_exact(store.state_path.read_bytes())["kind"] == "recovered-safe-to-restart"
    assert not store.gate_path.exists()


@pytest.mark.parametrize("cutpoint", ["prepared", "gate-release"])
def test_valid_state_recovery_restarts_at_release_cutpoints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cutpoint: str
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    original_state = loads_exact(state_path.read_bytes())
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    owner_child = r'''
import sys,time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings,repository_identity
from triage.storage import ArtifactStore
settings=load_settings(Path(sys.argv[1])); store=ArtifactStore(settings,'live')
acquire(store,repository_identity=repository_identity(settings),config_fingerprint=settings.fingerprint,run_identity=None)
print('ready',flush=True); time.sleep(300)
'''
    owner = subprocess.Popen(
        [sys.executable, "-c", owner_child, str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment,
    )
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if owner.poll() is None:
            owner.terminate()
        owner.wait(timeout=10)
    planned = run("recover", context="interactive", request={}, start=root)
    core_digest = planned["recovery_plan"]["action_core_digest"]
    supplied = {
        "decision": "approve", "source": "current-session",
        "approver_identity": "operator", "core_digest": core_digest,
    }
    context_value = {
        "source": "current-session", "operator_identity": "operator",
        "source_read_back": {
            "decision": "approve", "approver_identity": "operator",
            "core_digest": core_digest,
        },
    }
    marker = tmp_path / f"valid-state-{cutpoint}"
    transition_child = r'''
import sys,time
from pathlib import Path
import triage.recovery as recovery
from triage.approval import ApprovalContext
from triage.canonical import loads_exact
from triage.engine import run
root=Path(sys.argv[1]); marker=Path(sys.argv[2]); cutpoint=sys.argv[3]
request=loads_exact(bytes.fromhex(sys.argv[4])); context=ApprovalContext(**loads_exact(bytes.fromhex(sys.argv[5])))
def stop(name):
 if cutpoint == name: marker.write_text(name); time.sleep(300)
original_replace=recovery.atomic_replace
def controlled_replace(path,raw,**kwargs):
 result=original_replace(path,raw,**kwargs)
 if b'"kind":"state-present-prepared"' in raw: stop('prepared')
 return result
recovery.atomic_replace=controlled_replace
original_quarantine=recovery._quarantine
def controlled_quarantine(*args,**kwargs):
 result=original_quarantine(*args,**kwargs); stop('gate-release'); return result
recovery._quarantine=controlled_quarantine
run('recover',context='interactive',request=request,start=root,approval_context=context)
'''
    process = subprocess.Popen([
        sys.executable, "-c", transition_child, str(root), str(marker), cutpoint,
        dumps({"recovery_approval": supplied}).hex(), dumps(context_value).hex(),
    ], env=environment)
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    restart_child = r'''
import sys
from pathlib import Path
from triage.canonical import dumps
from triage.engine import run
print(dumps(run(sys.argv[2],context='interactive',request={},start=Path(sys.argv[1]))).decode(),flush=True)
'''

    def invoke(entry: str) -> dict:
        completed = subprocess.run(
            [sys.executable, "-c", restart_child, str(root), entry],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        return loads_exact(completed.stdout.strip().encode())

    assert state_path.read_bytes() == dumps(original_state)
    recovered = invoke("recover")
    assert recovered["outcome"] == "operator-held"
    if cutpoint == "prepared":
        assert recovered["detail"] == "resume"
    else:
        assert recovered["detail"] == "captured state is valid; recovery refused"
    assert state_path.read_bytes() == dumps(original_state)
    resumed = invoke("resume")
    assert resumed["outcome"] == "operator-held"
    retained = loads_exact(state_path.read_bytes())
    assert retained["phase"] == original_state["phase"]
    assert retained["proposal_payload_digests"] == original_state["proposal_payload_digests"]


# --- Completed-state retirement (#425) --------------------------------------
# Before this route, a valid ``completed`` state ended its mode: ``new`` refused
# it, every other entry replayed its receipt, and nothing removed it.

LIVE_STATE = "triage/triage-pipeline-state_live.json"



def completed_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, bytes, Path]:
    """Drive a live session to a decision-only completion; return root, state, bytes, retired path."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / LIVE_STATE
    presented = loads_exact(state_path.read_bytes())
    completed = run(
        "resume", context="interactive",
        request={"approval": approval_for(presented, "park TRI-01")}, start=root,
        approval_context=approval_context(presented, "park TRI-01"),
    )
    assert completed["outcome"] == "degraded-success"
    raw = state_path.read_bytes()
    receipt = loads_exact(raw)["completion"]["completed_receipt_digest"]
    return root, state_path, raw, state_path.with_name(f"{state_path.name}.completed-{receipt[:16]}")


@pytest.mark.parametrize("entry", [None, "new"])
def test_session_starting_entry_retires_completed_live_state_and_drafts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str | None
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    previous_session = loads_exact(completed_raw)["run_identity"]["session"]
    result = run(entry, context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert result["detail"].startswith(f"retired completed state to {retired} ")
    assert retired.read_bytes() == completed_raw
    fresh = loads_exact(state_path.read_bytes())
    assert fresh["phase"] == "reserved"
    assert fresh["run_identity"]["session"] != previous_session


def change_config(root: Path) -> None:
    """Change a configuration value the triage run does not read, as a later
    PR does to `config/dev-model.yaml`: the effective config fingerprint moves."""
    config = root / "config/dev-model.yaml"
    before = config.read_text(encoding="utf-8")
    after = before.replace('systemize_branch_pattern: "chore/systemize-{date}"', 'systemize_branch_pattern: "chore/systemize-{date}-later"')
    assert after != before
    config.write_text(after, encoding="utf-8")


@pytest.mark.parametrize("entry", [None, "new"])
def test_a_completed_state_retires_after_the_configuration_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str | None
) -> None:
    """A config change after a run finished held every later session-starting
    run on `configuration identity mismatch`, because retirement validated the
    completed state against the current fingerprint."""
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    before = load_settings(root).fingerprint
    change_config(root)
    assert load_settings(root).fingerprint != before
    with pytest.raises(TriageError, match="configuration identity mismatch"):
        canonical_state(completed_raw, settings=load_settings(root), mode="live")
    result = run(entry, context="interactive", request={}, start=root)
    assert result["detail"].startswith(f"retired completed state to {retired} ")
    assert retired.read_bytes() == completed_raw
    fresh = loads_exact(state_path.read_bytes())
    assert fresh["phase"] == "reserved"
    assert fresh["config_fingerprint"] == load_settings(root).fingerprint


def test_resume_of_a_completed_state_stays_bound_to_the_current_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    change_config(root)
    held = run("resume", context="interactive", request={}, start=root)
    assert held["outcome"] == "operator-held"
    assert held["detail"] == "configuration identity mismatch"
    assert state_path.read_bytes() == completed_raw
    assert not retired.exists()


def test_an_active_state_stays_bound_to_the_current_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / LIVE_STATE
    awaiting = state_path.read_bytes()
    assert loads_exact(awaiting)["phase"] == "awaiting-approval"
    change_config(root)
    for entry in (None, "new"):
        held = run(entry, context="interactive", request={}, start=root)
        assert held["outcome"] == "operator-held"
        assert held["detail"] == "configuration identity mismatch"
    assert state_path.read_bytes() == awaiting


def with_recorded_fingerprint(state: dict, fingerprint: str) -> dict:
    """Record `fingerprint` in both of a completed decision-only state's fields and
    recompute every digest that embeds its run identity, so that only the
    fingerprint check can refuse the result."""
    state["config_fingerprint"] = state["run_identity"]["config_fingerprint"] = fingerprint
    for proposal in state["proposal_payloads"]:
        binding = proposal["report_binding"]
        binding["report_core"]["run_identity"] = state["run_identity"]
        binding["report_core_digest"] = digest(binding["report_core"])
    core = state["completion"]["receipt_core"]
    core["run_identity"] = state["run_identity"]
    core["proposal_payloads"] = state["proposal_payloads"]
    state["completion"]["completed_receipt_digest"] = digest(core)
    return state


def test_a_completed_state_that_disagrees_with_itself_is_not_retired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _state_path, completed_raw, _retired = completed_live(tmp_path, monkeypatch)
    change_config(root)
    settings = load_settings(root)
    split = loads_exact(completed_raw)
    split["config_fingerprint"] = "f" * 64
    with pytest.raises(TriageError, match="configuration identity mismatch"):
        canonical_state(dumps(split), settings=settings, mode="live", retiring=True)
    # Every identity-bound digest is recomputed, so a well-formed recorded
    # fingerprint validates and only the digest-format check refuses a malformed one.
    reshaped = with_recorded_fingerprint(loads_exact(completed_raw), "e" * 64)
    assert canonical_state(dumps(reshaped), settings=settings, mode="live", retiring=True)["phase"] == "completed"
    malformed = with_recorded_fingerprint(loads_exact(completed_raw), "not-a-digest")
    with pytest.raises(TriageError, match="configuration identity mismatch"):
        canonical_state(dumps(malformed), settings=settings, mode="live", retiring=True)
    assert canonical_state(completed_raw, settings=settings, mode="live", retiring=True)["phase"] == "completed"


def test_a_completed_test_state_retires_after_the_configuration_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repository(tmp_path)
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "state-root"))
    run("test", context="interactive", request=request(root), start=root)
    state_path = tmp_path / "state-root/triage/triage-pipeline-state_test.json"
    presented = loads_exact(state_path.read_bytes())
    finished = run("test", context="interactive", request={"approval": approval_for(presented)}, start=root, approval_context=approval_context(presented), head_authority=FakeForge([]))
    assert finished["outcome"] == "degraded-success"
    completed_raw = state_path.read_bytes()
    change_config(root)
    restarted = run("test", context="interactive", request={}, start=root)
    assert restarted["detail"].startswith("retired completed state to ")
    receipt = loads_exact(completed_raw)["completion"]["completed_receipt_digest"]
    assert state_path.with_name(f"{state_path.name}.completed-{receipt[:16]}").read_bytes() == completed_raw
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"


@pytest.mark.parametrize(
    ("entry", "detail"),
    [("resume", "completed/decision-only"), ("recover", "captured state is valid; recovery refused")],
)
def test_resume_and_recover_leave_completed_state_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str, detail: str
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    result = run(entry, context="interactive", request={}, start=root)
    assert result["detail"] == detail
    assert state_path.read_bytes() == completed_raw
    assert not retired.exists()


def test_non_completed_state_is_never_retired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / LIVE_STATE
    awaiting = state_path.read_bytes()
    assert loads_exact(awaiting)["phase"] == "awaiting-approval"
    refused = run("new", context="interactive", request={}, start=root)
    assert refused["detail"] == "new refuses to overwrite active state"
    resumed = run(None, context="interactive", request={}, start=root)
    assert resumed["detail"] == "active session resumed"
    assert loads_exact(state_path.read_bytes())["phase"] == "awaiting-approval"
    assert [path.name for path in state_path.parent.iterdir() if ".completed-" in path.name] == []


def test_foreign_bytes_at_retired_path_hold_without_changing_either_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    retired.write_bytes(b"foreign\n")
    result = run(None, context="interactive", request={}, start=root)
    assert result["outcome"] == "operator-held"
    assert state_path.read_bytes() == completed_raw
    assert retired.read_bytes() == b"foreign\n"


def test_interrupted_claim_after_retirement_starts_fresh_on_the_next_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    original = triage_engine._new_draft

    def interrupted(*args, **kwargs):
        raise TriageError("simulated interruption after retirement")

    monkeypatch.setattr(triage_engine, "_new_draft", interrupted)
    failed = run(None, context="interactive", request={}, start=root)
    assert failed["outcome"] == "hard-stop"
    assert failed["detail"].startswith(f"retired completed state to {retired} ")
    assert "the next run starts fresh" in failed["detail"]
    # The retired session is not reported as retained evidence of the failed run.
    assert (failed["report"], failed["frozen_snapshot"], failed["candidate_index"]) == (None, None, [])
    assert not state_path.exists()
    assert retired.read_bytes() == completed_raw
    monkeypatch.setattr(triage_engine, "_new_draft", original)
    fresh = run(None, context="interactive", request={}, start=root)
    assert fresh["detail"] == "durable triage state retained"
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"
    assert retired.read_bytes() == completed_raw


def test_unattended_retirement_then_holds_for_notification_like_a_fresh_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, completed_raw, retired = completed_live(tmp_path, monkeypatch)
    result = run(None, context="unattended", request={}, start=root)
    assert retired.read_bytes() == completed_raw
    assert not state_path.exists()
    assert (result["report"], result["frozen_snapshot"], result["candidate_index"]) == (None, None, [])
    fresh_root = repository(tmp_path / "fresh")
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(tmp_path / "fresh-state-root"))
    baseline = run(None, context="unattended", request={}, start=fresh_root)
    assert result["outcome"] == baseline["outcome"]
    assert result["detail"].endswith(baseline["detail"])


# --- Retiring a finished run whose state no longer validates -----------------
# An invalid state that records external writes is held, because nothing proves
# none is in flight. A run whose own bytes record every write verified and a
# verified merge of the reviewed head has nothing in flight, and is retired.

REVIEWED = "a" * 40
SWEPT_BLOCK = "- **Swept defect.** filed by the old run."


def terminal_invalid_state() -> dict:
    return {
        "kind": "triage-run-state",
        "schema_version": 1,
        "phase": "completed",
        "schema_deviations": [{"id": "hand-recorded"}],
        "run_identity": {"session": "old-llm-only-session"},
        "reviewed_head": REVIEWED,
        "verified_tracker_identifiers": ["https://github.com/example/project/issues/9"],
        "operations": [{"candidate_id": "TRI-01", "status": "verified"}],
        "attempts": [{"status": "verified"}],
        "notification_operations": [],
        "finalization_operations": [
            {"kind": "commit", "status": "verified", "attempts": [{"status": "verified"}]},
            {"kind": "pr-watch", "status": "unsettled", "attempts": [{"status": "unsettled"}]},
            {"kind": "pr-watch", "status": "verified", "attempts": [{"status": "verified"}]},
            {"kind": "merge-read-back", "status": "verified", "attempts": [{"status": "verified"}]},
        ],
        "completion": {
            "route": "archive-sweep",
            "merge_read_back": {"merged": True, "final_head": REVIEWED, "pull_request": "10", "merge_commit": "b" * 40},
        },
        "frozen_snapshot": {"content": {"blocks": [
            {"candidate_id": "TRI-01", "source_block": SWEPT_BLOCK},
            {"candidate_id": "TRI-02", "source_block": "- **Parked defect.** still active."},
        ]}},
        "decisions": [
            {"candidate_id": "TRI-01", "decision": "file"},
            {"candidate_id": "TRI-02", "decision": "park"},
        ],
    }


def test_terminal_evidence_summarises_a_finished_run() -> None:
    from triage.recovery import _terminal_evidence

    assert _terminal_evidence(terminal_invalid_state()) == {
        "session": "old-llm-only-session",
        "verified_tracker_identifiers": ["https://github.com/example/project/issues/9"],
        "pull_request": "10",
        "merge_commit": "b" * 40,
        "final_head": REVIEWED,
    }


def _unfinished(change: str) -> dict:
    state = terminal_invalid_state()
    if change == "phase":
        state["phase"] = "forge-finalize"
    elif change == "route":
        state["completion"]["route"] = "decision-only"
    elif change == "unmerged":
        state["completion"]["merge_read_back"]["merged"] = False
    elif change == "other-head":
        state["completion"]["merge_read_back"]["final_head"] = "c" * 40
    elif change == "tracker-attempting":
        state["operations"][0]["status"] = "attempting"
    elif change == "attempt-ambiguous":
        state["attempts"][0]["status"] = "ambiguous"
    elif change == "nested-failed":
        state["finalization_operations"][0]["attempts"][0]["status"] = "failed"
    elif change == "unsettled-write":
        state["finalization_operations"][0]["status"] = "unsettled"
    elif change == "no-merge-read-back-last":
        state["finalization_operations"].pop()
    elif change == "no-forge":
        state["finalization_operations"] = []
    elif change == "notification-attempting":
        state["notification_operations"] = [{"status": "attempting"}]
    elif change == "identifier-type":
        state["verified_tracker_identifiers"] = [9]
    elif change == "schema-bool":
        state["schema_version"] = True
    elif change == "no-merge-commit":
        del state["completion"]["merge_read_back"]["merge_commit"]
    elif change == "null-merge-commit":
        state["completion"]["merge_read_back"]["merge_commit"] = None
    return state


@pytest.mark.parametrize("change", [
    "phase", "route", "unmerged", "other-head", "tracker-attempting", "attempt-ambiguous",
    "nested-failed", "unsettled-write", "no-merge-read-back-last", "no-forge",
    "notification-attempting", "identifier-type", "schema-bool",
    "no-merge-commit", "null-merge-commit",
])
def test_terminal_evidence_refuses_anything_unfinished(change: str) -> None:
    from triage.recovery import _terminal_evidence

    assert _terminal_evidence(_unfinished(change)) is None


@pytest.mark.parametrize(("entries", "settled"), [
    ([], True),
    ([{"status": "verified"}], True),
    ([{"status": "attempting", "intent_digest": "d1"}, {"status": "verified", "intent_digest": "d1"}], True),
    ([{"status": "attempting", "intent_digest": "d1"}], False),
    ([{"status": "attempting", "intent_digest": "d1"}, {"status": "verified", "intent_digest": "d2"}], False),
    ([{"status": "attempting", "intent_digest": "d1"}, {"status": "failed", "intent_digest": "d1"}], False),
    ([{"status": "attempting"}, {"status": "verified"}], False),
    ([{"status": "attempting", "intent_digest": "d1"}, {"status": "attempting", "intent_digest": "d1"}, {"status": "verified", "intent_digest": "d1"}], False),
    ([{"status": "ambiguous", "intent_digest": "d1"}, {"status": "verified", "intent_digest": "d1"}], False),
    ("not-a-list", False),
])
def test_attempt_log_is_settled_only_when_each_attempting_entry_is_answered(entries, settled: bool) -> None:
    """#833: the engine writes `attempting` before each external call and the
    outcome after it; only an exactly paired answer settles it."""
    from triage.recovery import _SETTLED, _attempt_log_settled

    assert _attempt_log_settled(entries, _SETTLED) is settled


def _engine_finished(change: str | None = None) -> dict:
    """The engine's finished layout: reviewed head under `archive_sweep`, the
    merge read-back as the last finalization operation, and no merge commit."""
    pair = [{"status": "attempting", "intent_digest": "i"}, {"status": "verified", "intent_digest": "i"}]
    state = {
        "kind": "triage-run-state", "schema_version": 1, "phase": "completed",
        "run_identity": {"session": "engine-session"},
        "verified_tracker_identifiers": [],
        "operations": [], "attempts": [], "notification_operations": [],
        "archive_sweep": {"reviewed_head": REVIEWED},
        "finalization_operations": [
            {"kind": "pr-watch", "status": "verified", "attempts": list(pair)},
            {"kind": "merge-read-back", "status": "verified", "attempts": list(pair), "read_back": {
                "url": "https://github.com/example/project/pull/10", "headRefOid": REVIEWED, "merged": True,
            }},
        ],
        "completion": {"route": "archive-sweep", "outcome": "degraded-success", "receipt_core": {}, "completed_receipt_digest": "x"},
    }
    read_back = state["finalization_operations"][-1]["read_back"]
    if change == "unmerged":
        read_back["merged"] = False
    elif change == "other-head":
        read_back["headRefOid"] = "c" * 40
    elif change == "no-reviewed-head":
        state["archive_sweep"] = {}
    elif change == "short-reviewed-head":
        state["archive_sweep"]["reviewed_head"] = "abc"
        read_back["headRefOid"] = "abc"
    elif change == "unanswered-attempt":
        state["finalization_operations"][0]["attempts"].pop()
    return state


def test_terminal_evidence_reads_the_engine_finished_layout() -> None:
    from triage.recovery import _terminal_evidence

    assert _terminal_evidence(_engine_finished()) == {
        "session": "engine-session",
        "verified_tracker_identifiers": [],
        "pull_request": "https://github.com/example/project/pull/10",
        "merge_commit": None,
        "final_head": REVIEWED,
    }


@pytest.mark.parametrize("change", ["unmerged", "other-head", "no-reviewed-head", "short-reviewed-head", "unanswered-attempt"])
def test_terminal_evidence_refuses_an_unfinished_engine_layout(change: str) -> None:
    from triage.recovery import _terminal_evidence

    assert _terminal_evidence(_engine_finished(change)) is None


def _write_live_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: dict, history: str = "landed"
) -> tuple[Path, Path, bytes]:
    """Write `state` as live state after building the repository `history` it claims.

    `landed` commits the swept block into the inbox, then a sweep commit moving it
    to the archive, and records that sweep as the merge. The other histories each
    break one thing the retirement check relies on.
    """
    root = repository(tmp_path)
    inbox = root / "docs/kit-friction-log.md"
    archive = root / "docs/kit-friction-log-archive.md"

    def commit(message: str) -> str:
        git(root, "add", "-A")
        git(root, "commit", "-q", "--allow-empty", "-m", message)
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
        return git(root, "rev-parse", "HEAD")

    inbox.write_text(inbox.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
    entry_added = commit("add the entry the old run will sweep")
    if history == "uncommitted-local-sweep":
        # The working tree says the block moved, but no commit did.
        inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", ""), encoding="utf-8")
        archive.write_text(archive.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
        merge_commit = entry_added
    elif history == "side-branch-sweep":
        # A complete sweep on a branch that never merged, while main swept the
        # block separately: only reachability tells the cited commit apart.
        git(root, "checkout", "-q", "-b", "side")
        inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", ""), encoding="utf-8")
        archive.write_text(archive.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "unmerged sweep")
        merge_commit = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", "main")
        inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", "\n- **Other.** edit.\n"), encoding="utf-8")
        archive.write_text(archive.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n\n", encoding="utf-8")
        commit("main's own sweep")
    elif history == "archived-after-removal":
        # The block left the inbox in one commit and reached the archive in a
        # later one; the cited later commit did not take it out of the inbox.
        inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", ""), encoding="utf-8")
        commit("drop the block")
        archive.write_text(archive.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
        merge_commit = commit("archive it later")
    elif history == "unrelated-reachable":
        # Reachable and it changes the friction log, but it is not this run's
        # sweep: the block is still in the inbox and not in the archive.
        merge_commit = entry_added
    elif history == "unmerged-branch":
        git(root, "checkout", "-q", "-b", "side")
        git(root, "commit", "-q", "--allow-empty", "-m", "never merged")
        merge_commit = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", "main")
    elif history in {"f" * 40, "f" * 64, "not-a-sha"}:
        merge_commit = history
    else:
        if history != "archive-only-commit":
            inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", ""), encoding="utf-8")
        if history != "missing-from-archive":
            archive.write_text(archive.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
        merge_commit = commit("docs(triage): graduate friction-log entries")
        if history == "archive-only-commit":
            # The block is archived, but the commit never touched the inbox; a
            # later commit removes it there.
            inbox.write_text(inbox.read_text(encoding="utf-8").replace("\n" + SWEPT_BLOCK + "\n", ""), encoding="utf-8")
            commit("later inbox edit")
        elif history == "decoy-commit":
            # The real sweep landed, but the state cites a different commit.
            merge_commit = entry_added
        elif history == "claims-unmerged-sweep":
            # The real sweep is on main, but the recorded merge is a side-branch
            # commit that also touches the friction log and never merged: only
            # the reachability check can tell.
            git(root, "checkout", "-q", "-b", "side")
            inbox.write_text(inbox.read_text(encoding="utf-8") + "side\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "unmerged friction-log edit")
            merge_commit = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "-q", "main")
        elif history == "still-in-inbox":
            inbox.write_text(inbox.read_text(encoding="utf-8") + "\n" + SWEPT_BLOCK + "\n", encoding="utf-8")
            commit("block re-added to the inbox")
    state["completion"]["merge_read_back"]["merge_commit"] = merge_commit
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    state_path.parent.mkdir(parents=True)
    raw = dumps(state)
    state_path.write_bytes(raw)
    return root, state_path, raw


def test_recover_retires_a_terminal_invalid_state_on_exact_approval_then_new_drafts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, raw = _write_live_state(tmp_path, monkeypatch, terminal_invalid_state())
    blocked = run("new", context="interactive", request={}, start=root)
    assert blocked["outcome"] in {"operator-held", "hard-stop"}
    planned = plan_in_own_process(root)
    plan = planned["recovery_plan"]
    assert plan["action_core"]["action"] == "retire-terminal-invalid-state"
    evidence = plan["action_core"]["terminal_evidence"]
    assert evidence["verified_tracker_identifiers"] == ["https://github.com/example/project/issues/9"]
    assert evidence["merge_commit_reachable_from"] == "refs/remotes/origin/main"
    assert evidence["merge_commit_source"] == "recorded"
    assert evidence["swept_candidates"] == ["TRI-01"]
    assert state_path.read_bytes() == raw
    core_digest = plan["action_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = ApprovalContext("current-session", "operator", {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest})
    recovered = run("recover", context="interactive", request={"recovery_approval": supplied}, start=root, approval_context=context)
    assert recovered["outcome"] == "operator-held"
    assert loads_exact(state_path.read_bytes())["kind"] == "recovered-safe-to-restart"
    retained = Path(plan["action_core"]["quarantine_path"])
    assert retained.read_bytes() == raw
    restarted = run("new", context="interactive", request={}, start=root)
    assert restarted["detail"] == "verified recovery receipt replaced by reserved new state"
    assert loads_exact(state_path.read_bytes())["phase"] == "reserved"
    assert retained.read_bytes() == raw


def test_recover_still_holds_an_invalid_state_with_an_unfinished_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, state_path, raw = _write_live_state(tmp_path, monkeypatch, _unfinished("tracker-attempting"))
    held = run("recover", context="interactive", request={}, start=root)
    assert held["outcome"] == "operator-held"
    assert held["detail"] == "external-attempt-absence-unproven"
    assert state_path.read_bytes() == raw


@pytest.mark.parametrize("history", [
    "f" * 40, "f" * 64, "not-a-sha", "unmerged-branch", "unrelated-reachable",
    "still-in-inbox", "missing-from-archive", "archive-only-commit", "claims-unmerged-sweep",
    "uncommitted-local-sweep", "decoy-commit", "side-branch-sweep", "archived-after-removal",
])
def test_recover_holds_a_finished_looking_state_whose_sweep_is_not_proven(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, history: str
) -> None:
    """The file's own claims are not enough, and neither is any merged commit: this
    run's sweep must be on the protected ref and its swept blocks out of the inbox."""
    root, state_path, raw = _write_live_state(tmp_path, monkeypatch, terminal_invalid_state(), history)
    held = run("recover", context="interactive", request={}, start=root)
    assert held["outcome"] == "operator-held"
    assert held["detail"] == "external-attempt-absence-unproven"
    assert state_path.read_bytes() == raw


# A gate owner in its own process, for the recovery routes that must prove the owner
# dead (#863), quarantine every same-inode gate name (#862), and report a released
# gate-only receipt as itself (#864). `alias` links the name a kill between the gate's
# link and its temporary's unlink leaves; `capture` and `prepared` publish the
# state-present bundle an ungated `recover` leaves bound to its own gate.
GATE_OWNER_CHILD = r'''
import os, sys, time
from pathlib import Path
from triage.gate import acquire
from triage.model import load_settings, repository_identity
from triage.recovery import capture_state_present, prepare_state_action, state_action_plan
from triage.storage import ArtifactStore
root = Path(sys.argv[1]); mode = sys.argv[2]; options = set(sys.argv[3:])
settings = load_settings(root); store = ArtifactStore(settings, mode)
lease = acquire(store, repository_identity=repository_identity(settings), config_fingerprint=settings.fingerprint, run_identity=None)
if "alias" in options:
    os.link(store.gate_path, store.gate_path.with_name("." + store.gate_path.name + "." + lease.owner_token + ".tmp"))
if "capture" in options or "prepared" in options:
    bundle = capture_state_present(store, settings, require_terminated=False, publish=True)
    if "prepared" in options:
        plan = state_action_plan(store, settings, bundle)
        prepare_state_action(store, settings, bundle, approval={"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": plan["action_core_digest"]}, operator="operator")
print("ready", flush=True)
time.sleep(300)
'''


def _gate_owner(root: Path, *, mode: str = "live", options: tuple[str, ...] = (), hold: bool = False) -> subprocess.Popen[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    owner = subprocess.Popen(
        [sys.executable, "-c", GATE_OWNER_CHILD, str(root), mode, *options],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment,
    )
    try:
        assert owner.stdout is not None and owner.stdout.readline().strip() == "ready"
    finally:
        if not hold or owner.poll() is not None:
            owner.terminate()
            owner.wait(timeout=10)
    return owner


def _approve_recovery(root: Path, core_digest: str, entry: str = "recover") -> dict:
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context = ApprovalContext("current-session", "operator", {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest})
    return run(entry, context="interactive", request={"recovery_approval": supplied}, start=root, approval_context=context)


def _abandonable(state_path: Path) -> None:
    state = loads_exact(state_path.read_bytes())
    kept = {key: state[key] for key in BASE_KEYS}
    kept["phase"] = "synthetic-unknown-phase"
    state_path.write_bytes(dumps(kept))


def _triage_files(state_root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.name: (path.read_bytes(), path.lstat().st_ino, path.lstat().st_nlink)
        for path in (state_root / "triage").iterdir()
    }


@pytest.mark.parametrize("state_shape", ["valid", "abandonable"])
def test_state_present_recovery_quarantines_every_same_inode_gate_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state_shape: str
) -> None:
    """A gate killed between its link and its temporary's unlink has two names. Recovery
    must move both, or the survivor blocks every later acquisition (#862)."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    if state_shape == "abandonable":
        _abandonable(state_path)
    _gate_owner(root, options=("alias",))
    planned = run("recover", context="interactive", request={}, start=root)
    expected_action = "preserve-valid-state-and-quarantine-old-gate" if state_shape == "valid" else "abandon-invalid-state"
    assert planned["recovery_plan"]["action_core"]["action"] == expected_action
    recovered = _approve_recovery(root, planned["recovery_plan"]["action_core_digest"])
    assert recovered["detail"] == ("resume" if state_shape == "valid" else "recovered-safe-to-restart")
    names = sorted(path.name for path in (state_root / "triage").iterdir())
    assert not [name for name in names if name.endswith(".tmp")]
    assert not (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    quarantined = [state_root / "triage" / name for name in names if name.startswith((".triage-pipeline-gate_live.lock.", "triage-pipeline-gate_live.lock.quarantine-"))]
    assert len(quarantined) == 2
    assert len({path.lstat().st_ino for path in quarantined}) == 1
    after = run("resume" if state_shape == "valid" else "new", context="interactive", request={}, start=root)
    assert after["detail"] == ("active session resumed" if state_shape == "valid" else "verified recovery receipt replaced by reserved new state")


@pytest.mark.parametrize("bundle_kind", ["capture", "prepared"])
def test_recover_holds_a_state_present_bundle_while_its_gate_owner_lives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bundle_kind: str
) -> None:
    """An ungated `recover` leaves its capture bound to its own gate. While that owner
    lives, no other invocation may plan from the bundle or act on it (#863)."""
    from triage.recovery import state_action_plan
    from triage.storage import ArtifactStore

    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    _abandonable(state_root / "triage/triage-pipeline-state_live.json")
    owner = _gate_owner(root, options=(bundle_kind,), hold=True)
    try:
        before = _triage_files(state_root)
        planned = run("recover", context="interactive", request={}, start=root)
        assert planned["outcome"] == "operator-held"
        assert planned["detail"] == "blocking gate owner is active or uncertain"
        assert planned["recovery_plan"] is None
        bundle_path = next((state_root / "triage").glob("recovery-bundle_live_*.json"))
        bundle = loads_exact(bundle_path.read_bytes())
        store = ArtifactStore(load_settings(root), "live")
        capture = bundle if bundle["kind"] == "state-present-capture" else {
            "kind": "state-present-capture", "schema_version": 1,
            "capture_core": bundle["capture_core"], "capture_core_digest": bundle["capture_core_digest"],
        }
        core_digest = state_action_plan(store, load_settings(root), capture)["action_core_digest"]
        approved = _approve_recovery(root, core_digest)
        assert approved["outcome"] == "operator-held"
        assert approved["detail"] == "blocking gate owner is active or uncertain"
        assert _triage_files(state_root) == before
        assert owner.poll() is None
    finally:
        owner.terminate()
        owner.wait(timeout=10)
    if bundle_kind == "capture":
        planned = run("recover", context="interactive", request={}, start=root)
        assert planned["recovery_plan"]["action_core"]["action"] == "abandon-invalid-state"
        recovered = _approve_recovery(root, planned["recovery_plan"]["action_core_digest"])
    else:
        recovered = run("recover", context="interactive", request={}, start=root)
    assert recovered["detail"] == "recovered-safe-to-restart"


@pytest.mark.parametrize("mode", ["live", "test"])
def test_a_released_gate_only_receipt_reports_itself_to_every_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """The entry's own freshly acquired gate is not a changed replacement gate (#864)."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    _gate_owner(root, mode=mode)
    entry = "recover" if mode == "live" else "test"
    planned = run(entry, context="interactive", request={}, start=root)
    assert planned["detail"] == "gate-only recovery capture awaits exact approval"
    assert _approve_recovery(root, planned["recovery_plan"]["prepared_core_digest"], entry)["detail"] == "gate-only-operator-held"
    before = _triage_files(state_root)
    for later in ([None, "new", "resume", "recover"] if mode == "live" else ["test"]):
        reported = run(later, context="interactive", request={}, start=root)
        assert reported["outcome"] == "operator-held"
        assert reported["detail"] == "gate-only-operator-held"
        assert reported["resume_action"] == "preserve the terminal gate-only evidence"
        assert _triage_files(state_root) == before


@pytest.mark.parametrize("route", ["gate-only", "valid-state"])
def test_a_stop_between_gate_name_moves_leaves_recovery_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str
) -> None:
    """Recovery moves a gate's alias before the gate itself. A stop between the two
    leaves the gate blocking, so `recover` resumes the move; the other order would
    leave only the alias, which acquisition refuses and `recover` cannot find (#862)."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    if route == "valid-state":
        run("new", context="interactive", request=request(root), start=root)
    _gate_owner(root, options=("alias",))
    planned = run("recover", context="interactive", request={}, start=root)
    core_digest = planned["recovery_plan"]["prepared_core_digest" if route == "gate-only" else "action_core_digest"]
    supplied = {"decision": "approve", "source": "current-session", "approver_identity": "operator", "core_digest": core_digest}
    context_value = {"source": "current-session", "operator_identity": "operator", "source_read_back": {"decision": "approve", "approver_identity": "operator", "core_digest": core_digest}}
    marker = tmp_path / "first-gate-name-moved"
    child = r'''
import sys, time
from pathlib import Path
import triage.recovery as recovery
from triage.approval import ApprovalContext
from triage.canonical import loads_exact
from triage.engine import run
root = Path(sys.argv[1]); marker = Path(sys.argv[2])
request = loads_exact(bytes.fromhex(sys.argv[3])); context = ApprovalContext(**loads_exact(bytes.fromhex(sys.argv[4])))
original = recovery._quarantine
def stop_after_first(path, *args, **kwargs):
    result = original(path, *args, **kwargs)
    if "gate_live.lock" in path.name:
        marker.write_text(path.name); time.sleep(300)
    return result
recovery._quarantine = stop_after_first
run("recover", context="interactive", request=request, start=root, approval_context=context)
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen([
        sys.executable, "-c", child, str(root), str(marker),
        dumps({"recovery_approval": supplied}).hex(), dumps(context_value).hex(),
    ], env=environment)
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)
    assert marker.read_text().startswith(".triage-pipeline-gate_live.lock.")
    assert (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    restarted = run("recover", context="interactive", request={}, start=root)
    assert restarted["detail"] == ("gate-only-operator-held" if route == "gate-only" else "resume")
    assert not [path for path in (state_root / "triage").iterdir() if path.name.endswith(".tmp")]
    after = run("new" if route == "gate-only" else "resume", context="interactive", request={}, start=root)
    assert after["detail"] == ("gate-only-operator-held" if route == "gate-only" else "active session resumed")


@pytest.mark.parametrize("bundle_kind", ["capture", "prepared"])
def test_a_state_present_bundle_resumes_after_a_configuration_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bundle_kind: str
) -> None:
    """The owner proof checks liveness, not the current configuration: the bundle is
    bound to its gate's exact bytes, so an approved transition still completes after
    an unrelated configuration change (#863)."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    _abandonable(state_root / "triage/triage-pipeline-state_live.json")
    _gate_owner(root, options=(bundle_kind,))
    config = root / "config/dev-model.yaml"
    config.write_text(config.read_text(encoding="utf-8") + "synthetic_configuration_change: true\n", encoding="utf-8")
    if bundle_kind == "capture":
        planned = run("recover", context="interactive", request={}, start=root)
        assert planned["recovery_plan"]["action_core"]["action"] == "abandon-invalid-state"
        recovered = _approve_recovery(root, planned["recovery_plan"]["action_core_digest"])
    else:
        recovered = run("recover", context="interactive", request={}, start=root)
    assert recovered["detail"] == "recovered-safe-to-restart"


def test_an_uncertain_state_present_bundle_owner_holds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only a proven-dead owner releases the bundle: `uncertain` (a foreign host, a
    reused process id, an unreadable start time) holds like a live owner (#863)."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    _abandonable(state_root / "triage/triage-pipeline-state_live.json")
    _gate_owner(root, options=("capture",))
    monkeypatch.setattr(triage_engine, "owner_status", lambda record: "uncertain")
    before = _triage_files(state_root)
    held = run("recover", context="interactive", request={}, start=root)
    assert held["outcome"] == "operator-held"
    assert held["detail"] == "blocking gate owner is active or uncertain"
    assert _triage_files(state_root) == before


# A `new` that stops for good at one of completed-state retirement's cutpoints. It
# wraps the link and unlink `quarantine_inode` makes on the state and the claim that
# follows, writes the marker at the named cut and waits there to be killed, still
# holding the gate it acquired.
RETIREMENT_CUT_CHILD = r'''
import os, sys, time
from pathlib import Path
import triage.engine as engine
root = Path(sys.argv[1]); marker = Path(sys.argv[2]); cut = sys.argv[3]
state_name = "triage-pipeline-state_live.json"
def stop():
    marker.write_text(cut); time.sleep(300)
real_link, real_unlink, real_new_draft = os.link, os.unlink, engine._new_draft
def link(source, target, *args, **kwargs):
    retiring = str(target).startswith(state_name + ".completed-")
    if retiring and cut == "before-link":
        stop()
    result = real_link(source, target, *args, **kwargs)
    if retiring and cut == "after-link":
        stop()
    return result
def unlink(path, *args, **kwargs):
    result = real_unlink(path, *args, **kwargs)
    if str(path) == state_name and cut == "after-unlink":
        stop()
    return result
def new_draft(*args, **kwargs):
    if cut == "before-claim":
        stop()
    return real_new_draft(*args, **kwargs)
os.link, os.unlink, engine._new_draft = link, unlink, new_draft
engine.run("new", context="interactive", request={}, start=root)
'''


@pytest.mark.parametrize("cut", ["before-link", "after-link", "after-unlink", "before-claim"])
def test_a_kill_during_completed_state_retirement_holds_rather_than_starting_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cut: str
) -> None:
    """Retirement runs under the held gate, so a kill anywhere in it leaves that gate
    with a dead owner. The interactive no-argument, `new` and `resume` entries each hold,
    and none starts fresh (#874). What `recover` can do next depends on where the kill
    landed: the state still whole, the state and its retired name sharing one inode, or
    the state gone with only the retired name."""
    root = repository(tmp_path)
    state_root = tmp_path / "state-root"
    monkeypatch.setenv("DEVKIT_STATE_ROOT", str(state_root))
    run("new", context="interactive", request=request(root), start=root)
    state_path = state_root / "triage/triage-pipeline-state_live.json"
    presented = loads_exact(state_path.read_bytes())
    completed = run(
        "resume", context="interactive",
        request={"approval": approval_for(presented, "park TRI-01")}, start=root,
        approval_context=approval_context(presented, "park TRI-01"),
    )
    assert completed["outcome"] == "degraded-success"
    completed_raw = state_path.read_bytes()
    assert loads_exact(completed_raw)["phase"] == "completed"
    receipt_digest = loads_exact(completed_raw)["completion"]["completed_receipt_digest"]
    retired = state_path.with_name(f"{state_path.name}.completed-{receipt_digest[:16]}")
    marker = tmp_path / "retirement-cut"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ENGINE_DIR / "lib") + os.pathsep + str(ENGINE_DIR)
    process = subprocess.Popen([sys.executable, "-c", RETIREMENT_CUT_CHILD, str(root), str(marker), cut], env=environment)
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists()
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
    assert (state_root / "triage/triage-pipeline-gate_live.lock").exists()
    if cut == "before-link":
        assert state_path.read_bytes() == completed_raw
        assert state_path.lstat().st_nlink == 1
        assert not retired.exists()
    elif cut == "after-link":
        assert state_path.read_bytes() == completed_raw
        assert state_path.lstat().st_ino == retired.lstat().st_ino
        assert state_path.lstat().st_nlink == 2
    else:
        assert not state_path.exists()
        assert retired.read_bytes() == completed_raw
        assert retired.lstat().st_nlink == 1
    before = _triage_files(state_root)
    for entry in (None, "new", "resume"):
        held = run(entry, context="interactive", request={}, start=root)
        assert (held["outcome"], held["detail"]) == ("operator-held", "single-writer gate is already held")
        assert _triage_files(state_root) == before
    if cut == "after-link":
        # Neither name can be read while the inode has two links, so no engine route
        # clears it and the workflow leaves it to the operator. Were the retired name
        # removed, the same bytes would stay at the state path, and the engine's own
        # routes then treat it as the before-link case.
        held = run("recover", context="interactive", request={}, start=root)
        assert held["outcome"] == "operator-held"
        assert held["detail"].startswith("unsafe artifact at held parent: ")
        assert held["detail"].endswith(f"/{state_path.name}")
        assert _triage_files(state_root) == before
        retired.unlink()
    if cut in {"before-link", "after-link"}:
        planned = run("recover", context="interactive", request={}, start=root)
        assert planned["detail"] == "state-present recovery action awaits exact approval"
        assert planned["recovery_plan"]["action_core"]["action"] == "preserve-valid-state-and-quarantine-old-gate"
        assert _approve_recovery(root, planned["recovery_plan"]["action_core_digest"])["detail"] == "resume"
        restarted = run("new", context="interactive", request={}, start=root)
        assert restarted["detail"].startswith("retired completed state to ")
        assert retired.name in restarted["detail"]
        assert retired.read_bytes() == completed_raw
        assert loads_exact(state_path.read_bytes())["phase"] == "reserved"
        return
    # The state is gone, so this is the gate-only route. Its receipt is terminal:
    # every entry reports it, and none starts a new draft.
    planned = run("recover", context="interactive", request={}, start=root)
    assert planned["detail"] == "gate-only recovery capture awaits exact approval"
    assert _approve_recovery(root, planned["recovery_plan"]["prepared_core_digest"])["detail"] == "gate-only-operator-held"
    for entry in (None, "new", "resume", "recover"):
        assert run(entry, context="interactive", request={}, start=root)["detail"] == "gate-only-operator-held"
    assert retired.read_bytes() == completed_raw
