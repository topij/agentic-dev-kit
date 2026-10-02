"""The on-demand runtime smoke runner (#879), without starting a real client.

The runner exists to start real clients; this suite never does. The unit tests pin
how a row reads runtime artifacts: which message roles count as injected context,
what must match byte for byte, and where a pin is compared. The end-to-end tests
drive the public CLI against a temporary commit of the kit whose lane commands name
fake `codex` and `claude` scripts, so the harness check, the fixture build, the lane
launcher and the record all run for real while every "client" is a script in the
test's temporary directory. The fakes run the fixture's own hook registrations and
engines, so a hook row passes only if the shipped command lines produce the text the
runner expects.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
RUNNER = ENGINE_DIR / "runtime_smoke.py"

sys.path.insert(0, str(ENGINE_DIR))
import runtime_smoke as rs  # noqa: E402

FAKE_VERSION = "9.9.9"
# The kit's working records and evidence trees, which neither the runner nor the
# fixture's engines read.
NOT_COPIED = ("saved_plans/",)


def _message(index: int, role: str, text: str) -> dict:
    return {"index": index, "role": role, "text": text}


def _view(**parts) -> dict:
    view = {"meta": {}, "turns": [], "messages": [], "calls": [], "outputs": [], "events": [], "world_states": []}
    view.update(parts)
    return view


# ------------------------------------------------------------------- AGENTS.md


def _agents_block(directory: Path, body: str) -> str:
    return f"# AGENTS.md instructions for {directory}\n\n<INSTRUCTIONS>\n{body}\n</INSTRUCTIONS>"


def test_the_agents_block_must_name_the_fixture_and_equal_its_file(tmp_path):
    body = "# AGENTS.md\n\nThe contract.\n"
    view = _view(messages=[_message(3, "user", _agents_block(tmp_path, body))])
    ok, evidence = rs.check_agents_block(view, tmp_path, body.encode())
    assert ok
    assert evidence["blocks"] == [
        {
            "index": 3,
            "shape": "user message",
            "dir": str(tmp_path),
            "dir_is_fixture": True,
            "body_sha256": rs.sha256_bytes(body.encode()),
            "body_equals_fixture": True,
        }
    ]


def test_one_byte_of_difference_fails_the_agents_block(tmp_path):
    body = "# AGENTS.md\n\nThe contract.\n"
    view = _view(messages=[_message(3, "user", _agents_block(tmp_path, body.replace("contract", "Contract")))])
    ok, evidence = rs.check_agents_block(view, tmp_path, body.encode())
    assert not ok
    assert evidence["blocks"][0]["body_equals_fixture"] is False


def test_an_agents_block_for_another_directory_does_not_count(tmp_path):
    body = "# AGENTS.md\n"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    view = _view(messages=[_message(3, "user", _agents_block(elsewhere, body))])
    ok, evidence = rs.check_agents_block(view, tmp_path, body.encode())
    assert not ok
    assert evidence["blocks"][0]["dir_is_fixture"] is False


def _world_state(index: int, directory: Path, text: str) -> dict:
    return {"index": index, "state": {"agents_md": {"directory": str(directory), "text": text}}}


def test_a_world_state_snapshot_carries_agents_md_too(tmp_path):
    body = "# AGENTS.md\n\n— the contract.\n"
    ok, evidence = rs.check_agents_block(_view(world_states=[_world_state(6, tmp_path, body)]), tmp_path, body.encode())
    assert ok
    assert evidence["blocks"][0]["shape"] == "world_state.agents_md"
    ok, _ = rs.check_agents_block(_view(world_states=[_world_state(6, tmp_path, body + " ")]), tmp_path, body.encode())
    assert not ok


def test_a_world_state_snapshot_for_another_directory_does_not_count(tmp_path):
    body = "# AGENTS.md\n"
    ok, evidence = rs.check_agents_block(
        _view(world_states=[_world_state(6, tmp_path / "elsewhere", body)]), tmp_path, body.encode()
    )
    assert not ok
    assert (evidence["blocks"][0]["dir_is_fixture"], evidence["blocks"][0]["body_equals_fixture"]) == (False, True)


def test_world_state_entries_reach_the_view():
    entries = [
        {"type": "world_state", "payload": {"full": True, "state": {"agents_md": {"directory": "/r", "text": "x"}}}},
        {"type": "world_state", "payload": {"full": False}},
    ]
    assert rs.rollout_view(entries)["world_states"] == [
        {"index": 0, "state": {"agents_md": {"directory": "/r", "text": "x"}}}
    ]


@pytest.mark.parametrize("role", ["assistant", "developer"])
def test_only_a_user_message_carries_the_agents_block(tmp_path, role):
    body = "# AGENTS.md\n"
    view = _view(messages=[_message(3, role, _agents_block(tmp_path, body))])
    ok, evidence = rs.check_agents_block(view, tmp_path, body.encode())
    assert not ok
    assert evidence["blocks"] == []


# ---------------------------------------------------------------------- skills


SKILLS_TEXT = """<skills_instructions>
## Skills
### Skill roots
- `r0` = `{root}`
- `r1` = `/elsewhere/skills`
### Available skills
- adopt: Adopt the kit. (file: r0/adopt/SKILL.md)
- other: Another root's skill. (file: r1/other/SKILL.md)
- direct: An absolute entry. (file: {root}/direct/SKILL.md)
</skills_instructions>"""


def test_skills_resolve_through_their_root_alias(tmp_path):
    files = rs.listed_skill_files(SKILLS_TEXT.format(root=tmp_path))
    assert files == {
        rs.realpath(tmp_path / "adopt" / "SKILL.md"),
        rs.realpath("/elsewhere/skills/other/SKILL.md"),
        rs.realpath(tmp_path / "direct" / "SKILL.md"),
    }


def test_a_declared_skill_missing_from_the_list_fails_and_is_named(tmp_path):
    text = SKILLS_TEXT.format(root=tmp_path)
    expected = [rs.realpath(tmp_path / "adopt" / "SKILL.md"), rs.realpath(tmp_path / "wrap-up" / "SKILL.md")]
    ok, evidence = rs.check_skills(_view(messages=[_message(2, "developer", text)]), expected)
    assert not ok
    assert evidence["missing"] == [rs.realpath(tmp_path / "wrap-up" / "SKILL.md")]


def test_an_empty_declaration_proves_no_skill_discovery(tmp_path):
    ok, _ = rs.check_skills(_view(messages=[_message(2, "developer", SKILLS_TEXT.format(root=tmp_path))]), [])
    assert not ok


def test_a_skills_list_the_model_wrote_does_not_count(tmp_path):
    expected = [rs.realpath(tmp_path / "adopt" / "SKILL.md")]
    ok, evidence = rs.check_skills(
        _view(messages=[_message(2, "assistant", SKILLS_TEXT.format(root=tmp_path))]), expected
    )
    assert not ok
    assert evidence["skills_blocks"] == 0


# -------------------------------------------------------------- injected context


def test_injected_text_never_counts_from_the_model():
    view = _view(messages=[_message(5, "assistant", "⚠ marker"), _message(9, "developer", "⚠ marker")])
    assert rs.find_injected(view, "⚠ marker") == {"index": 9, "role": "developer"}
    assert rs.find_injected(_view(messages=[_message(5, "assistant", "⚠ marker")]), "⚠ marker") is None


def test_hook_context_must_follow_the_call_it_answers():
    view = _view(messages=[_message(4, "developer", "warning"), _message(12, "developer", "warning")])
    assert rs.find_injected(view, "warning", after=8) == {"index": 12, "role": "developer"}
    assert rs.find_injected(view, "warning", after=12) is None


def test_the_hook_answer_is_ordered_after_its_call_not_its_output():
    url = "https://github.com/adk-smoke/fixture-abc/pull/7"
    entries = [
        {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"text": "warning"}]}},
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "c1"}},
        {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"text": "warning"}]}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c1", "output": url}},
    ]
    view = rs.rollout_view(entries)
    output_index = rs.first_output_with(view, url)
    assert (output_index, rs.call_answered_by(view, output_index)) == (3, 1)
    assert rs.find_injected(view, "warning", after=rs.call_answered_by(view, output_index)) == {"index": 2, "role": "developer"}
    unlinked = rs.rollout_view(entries[:1] + [entries[3]])
    assert rs.call_answered_by(unlinked, rs.first_output_with(unlinked, url)) is None


def test_the_call_is_the_one_whose_id_the_output_carries():
    url = "https://github.com/adk-smoke/fixture-abc/pull/7"
    entries = [
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "c0"}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c0", "output": "a listing"}},
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "c1"}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c1", "output": url}},
    ]
    view = rs.rollout_view(entries)
    assert rs.call_answered_by(view, rs.first_output_with(view, url)) == 2


def test_the_nonce_url_is_found_only_in_tool_output():
    url = "https://github.com/adk-smoke/fixture-abc/pull/7"
    view = _view(
        outputs=[{"index": 11, "text": json.dumps(f"{url}\n")}],
        events=[{"index": 6, "type": "agent_message", "text": url}],
    )
    assert rs.first_output_with(view, url) == 11
    assert rs.first_output_with(_view(events=[{"index": 6, "type": "agent_message", "text": url}]), url) is None


# ----------------------------------------------------------- sessions and pins


def test_the_pin_is_compared_with_the_executing_runtime():
    entries = [
        {"type": "session_meta", "payload": {"id": "t1", "cli_version": "0.153.4", "originator": "Codex Desktop", "source": "exec", "cwd": "/w"}},
        {"type": "turn_context", "payload": {"model": "m", "effort": "low", "sandbox_policy": {"type": "read-only"}}},
    ]
    session = rs.codex_session(rs.rollout_view(entries))
    assert session["executing_version"] == "0.153.4"
    assert session["sandbox"] == "read-only"
    assert rs.pin_mismatch(session, "0.153.4") is None
    assert rs.pin_mismatch(session, "0.159.2") == "the executing runtime reported '0.153.4', not the pinned '0.159.2'"
    assert rs.pin_mismatch({"executing_version": None}, "0.153.4") is not None


def test_claude_reads_version_model_and_effort_from_the_transcript():
    transcript = [
        {"type": "user", "version": "2.1.287", "cwd": "/w"},
        {"type": "assistant", "version": "2.1.287", "effort": "high", "message": {"model": "claude-sonnet-5"}},
        {"type": "assistant", "version": "2.1.287", "effort": "high", "message": {"model": "<synthetic>"}},
    ]
    session = rs.claude_session({"session_id": "s", "model": "claude-sonnet-5"}, transcript)
    assert session["executing_version"] == "2.1.287"
    assert session["transcript_models"] == ["claude-sonnet-5"]
    assert session["transcript_efforts"] == ["high"]
    mixed = transcript + [{"type": "assistant", "version": "2.1.288", "message": {"model": "x"}}]
    assert rs.claude_session({}, mixed)["executing_version"] == ["2.1.287", "2.1.288"]


@pytest.mark.parametrize("tail", ["last line\n", "last line"])
def test_padding_lands_on_the_count_the_budget_engine_will_report(tmp_path, tail):
    document = tmp_path / "friction.md"
    document.write_text(f"# Friction\n\n{tail}", encoding="utf-8")
    target = rs.pad_over_budget(document, budget=150)
    assert 157 <= target <= 247
    with document.open("r", encoding="utf-8") as handle:
        assert sum(1 for _ in handle) == target


def test_hook_output_is_matched_through_its_json_layers():
    stdout = json.dumps({"hookSpecificOutput": {"additionalContext": "⚠ docs/x.md is 9 lines"}})
    events = [{"type": "system", "subtype": "hook_response", "hook_event": "PostToolUse", "output": stdout}]
    [event] = rs.claude_hook_events(events, "PostToolUse")
    assert rs.mentions(event, "⚠ docs/x.md is 9 lines")
    assert not rs.mentions(event, "docs/y.md")


def _tool_use(use_id: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": use_id, "name": "Bash"}]}}


def _tool_result(use_id: str, text: str) -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": use_id, "content": text}]}}


def test_only_a_tool_result_carries_the_nonce_url_and_its_id_finds_the_call():
    url = "https://github.com/adk-smoke/fixture-abc/pull/7"
    prompt = {"type": "user", "message": {"content": [{"type": "text", "text": f"printf {url}"}]}}
    echoed = {"type": "assistant", "message": {"content": [{"type": "text", "text": url}]}}
    assert rs.claude_tool_call_for([prompt, echoed], url) == (None, None)
    events = [prompt, _tool_use("t1"), {"type": "system", "subtype": "hook_response"}, _tool_result("t1", f"{url}\n")]
    assert rs.claude_tool_call_for(events, url) == (1, 3)
    unlinked = [prompt, _tool_use("t0"), _tool_result("t1", url)]
    assert rs.claude_tool_call_for(unlinked, url) == (None, 2)
    another_part = {"type": "user", "message": {"content": [{"type": "document", "content": url}]}}
    assert rs.claude_tool_call_for([prompt, _tool_use("t1"), another_part], url) == (None, None)


def test_the_hooks_json_comparison_reads_the_revisions_bytes(tmp_path):
    env = _git_env(tmp_path)
    kit = tmp_path / "kit"
    (kit / ".codex").mkdir(parents=True)
    (kit / ".codex" / "hooks.json").write_text('{"hooks": {}}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=kit, env=env, check=True)
    sha = _commit_all(kit, env, "hooks")
    fixture = tmp_path / "fixture"
    (fixture / ".codex").mkdir(parents=True)
    (fixture / ".codex" / "hooks.json").write_text('{"hooks": {}}\n', encoding="utf-8")
    with pytest.MonkeyPatch.context() as patch:
        for key, value in env.items():
            patch.setenv(key, value)
        assert rs.hooks_json_differs(fixture, kit, sha) is False
        (fixture / ".codex" / "hooks.json").write_text('{"hooks": {"x": []}}\n', encoding="utf-8")
        assert rs.hooks_json_differs(fixture, kit, sha) is True
        (fixture / ".codex" / "hooks.json").unlink()
        assert rs.hooks_json_differs(fixture, kit, sha) is True
        assert rs.hooks_json_differs(kit, kit, "no-such-revision") is True


@pytest.mark.parametrize("bypass, project_trust", [(True, True), (True, False), (False, True)])
def test_a_differing_registration_gets_no_trust_whatever_was_authorized(bypass, project_trust):
    assert rs.codex_hook_route(True, bypass=bypass, project_trust=project_trust) == {
        "project_trust": "none",
        "hook_trust": "none",
        "hooks_json_differs": True,
    }
    route = rs.codex_hook_route(False, bypass=bypass, project_trust=project_trust)
    assert route["project_trust"] == ("per-invocation override" if project_trust else "none")
    assert route["hook_trust"] == ("per-invocation bypass" if bypass else "none")


def test_a_moved_injection_shape_leaves_its_heads_in_the_evidence(tmp_path):
    view = _view(messages=[_message(1, "user", "<environment_context>\n<cwd>/x</cwd>"), _message(2, "developer", "## Skills\n")])
    ok, evidence = rs.check_agents_block(view, tmp_path, b"# AGENTS.md\n")
    assert not ok and evidence["user_message_heads"] == ["<environment_context>"]
    ok, evidence = rs.check_skills(view, [rs.realpath(tmp_path / "adopt" / "SKILL.md")])
    assert not ok and evidence["developer_message_heads"] == ["## Skills"]


def test_the_reviewer_is_the_review_child_session_in_the_fixture(tmp_path):
    day = tmp_path / "home" / "sessions" / "2026" / "10" / "02"
    day.mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()

    def rollout(name, source, cwd):
        (day / f"rollout-{name}.jsonl").write_text(
            json.dumps({"type": "session_meta", "payload": {"source": source, "cwd": str(cwd)}}) + "\n",
            encoding="utf-8",
        )

    rollout("parent", "exec", repo)
    rollout("child", {"subagent": "review"}, repo)
    rollout("elsewhere", {"subagent": "review"}, tmp_path)
    found = rs.review_child_sessions(tmp_path / "home", cwd=repo, since=0)
    assert [path.name for path in found] == ["rollout-child.jsonl"]
    assert rs.review_child_sessions(tmp_path / "home", cwd=repo, since=time.time() + 60) == []


def test_review_mode_is_read_from_completed_item_types():
    entries = [
        {"type": "event_msg", "payload": {"type": "item_completed", "item": {"type": "EnteredReviewMode"}}},
        {"type": "event_msg", "payload": {"type": "task_started"}},
        {"type": "event_msg", "payload": {"type": "item_completed", "item": {"type": "ExitedReviewMode"}}},
    ]
    assert rs.review_markers(rs.rollout_view(entries)) == ["EnteredReviewMode", "ExitedReviewMode"]
    assert rs.review_markers(rs.rollout_view(entries[1:2])) == []


def _route(project="none", hook="none", differs=False):
    return {"project_trust": project, "hook_trust": hook, "hooks_json_differs": differs}


def test_the_missing_trust_layer_is_named_project_first():
    assert rs.hook_trust_reason(_route()).startswith("project trust not established")
    assert rs.hook_trust_reason(_route(hook="per-invocation bypass")).startswith("project trust not established")
    assert rs.hook_trust_reason(_route(project="per-invocation override")).startswith("hook trust not established")
    assert rs.hook_trust_reason(_route("per-invocation override", "per-invocation bypass")) is None
    assert rs.hook_trust_reason(_route("per-invocation override", "per-invocation bypass", True)).startswith(
        "hook trust refused"
    )


def test_the_project_trust_override_is_one_toml_table_keyed_by_the_whole_path(tmp_path):
    repo = tmp_path / "a.b" / 'odd"name'
    repo.mkdir(parents=True)
    flag, value = rs.codex_project_trust_override(repo)
    assert flag == "-c"
    assert rs.tomllib.loads(value) == {"projects": {rs.realpath(repo): {"trust_level": "trusted"}}}


def test_subagents_are_read_with_their_agent_type_and_summarised_without_text(tmp_path):
    transcript = tmp_path / "session-1.jsonl"
    transcript.write_text("", encoding="utf-8")
    folder = tmp_path / "session-1" / "subagents"
    folder.mkdir(parents=True)
    (folder / "agent-1.meta.json").write_text(json.dumps({"agentType": "adversarial"}), encoding="utf-8")
    (folder / "agent-1.jsonl").write_text(
        "\n".join(
            json.dumps(entry)
            for entry in (
                {"type": "user", "version": "2.1.287", "message": {"content": "the rendered prompt"}},
                {"type": "assistant", "version": "2.1.287", "effort": "high",
                 "message": {"model": "claude-sonnet-5", "content": [{"type": "text", "text": "Reviewed abc1234."}]}},
            )
        ),
        encoding="utf-8",
    )
    [agent] = rs.claude_subagents(transcript)
    assert (agent["agent_type"], agent["models"], agent["efforts"]) == ("adversarial", ["claude-sonnet-5"], ["high"])
    assert (agent["first_prompt"], agent["last_text"]) == ("the rendered prompt", "Reviewed abc1234.")
    summary = rs.summarise_subagent(agent)
    assert summary["prompt_sha256"] == rs.sha256_bytes(b"the rendered prompt")
    assert "the rendered prompt" not in json.dumps(summary) and "Reviewed" not in json.dumps(summary)
    assert rs.claude_subagents(None) == []


def test_hook_events_are_selected_by_event_name():
    events = [
        {"type": "system", "subtype": "init"},
        {"type": "system", "subtype": "hook_started", "hook_event": "SessionStart"},
        {"type": "system", "subtype": "hook_response", "hook_event": "PostToolUse", "output": "x"},
        {"type": "assistant", "subtype": "hook_response", "hook_event": "SessionStart"},
    ]
    assert [event["index"] for event in rs.claude_hook_events(events, "SessionStart")] == [1]
    assert [event["index"] for event in rs.claude_hook_events(events, "PostToolUse")] == [2]


# ------------------------------------------------------------- record and exits


def test_redaction_replaces_every_form_of_a_path_longest_first(tmp_path):
    run = tmp_path / "work" / "adk-smoke-x"
    run.mkdir(parents=True)
    table = rs.placeholders([(tmp_path / "work", "<work-root>"), (run, "<run>"), (None, "<absent>")])
    record = {f"{run}/logs": [f"cd {rs.realpath(run)}/repo", f"{tmp_path}/work/other"]}
    assert rs.redact(record, table) == {"<run>/logs": ["cd <run>/repo", "<work-root>/other"]}


def test_strings_are_bounded_only_after_redaction(tmp_path):
    run = tmp_path / "work" / "adk-smoke-x"
    run.mkdir(parents=True)
    table = rs.placeholders([(run, "<run>")])
    tail = "/repo/.claude.json"
    # Exactly the limit once redacted, so a cut made before redaction lands inside the path.
    padding = "p" * (rs.RECORD_STRING_LIMIT - len("<run>") - len(tail))
    long = "x" * (rs.RECORD_STRING_LIMIT + 1)
    record = rs.finalize_record({"stderr_head": padding + str(run) + tail, "long": long}, table)
    assert record["stderr_head"] == padding + "<run>" + tail
    assert record["long"] == long[: rs.RECORD_STRING_LIMIT - 1] + "…"


def test_a_path_reached_through_a_link_is_redacted_in_both_spellings(tmp_path):
    real = tmp_path / "real" / "run"
    real.mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    table = rs.placeholders([(link, "<run>")])
    assert rs.redact(f"{link}/repo and {real}/repo", table) == "<run>/repo and <run>/repo"


def test_the_encoded_spelling_of_a_path_is_redacted_too(tmp_path):
    home = tmp_path / "Users" / "someone"
    encoded = "-".join(str(home).split("/"))
    table = rs.placeholders([(home, "~"), (encoded, "~")])
    assert rs.redact(f"projects/-private{encoded}-Coding-repo/x.jsonl", table) == "projects/-private~-Coding-repo/x.jsonl"


@pytest.mark.parametrize(
    "statuses, expected",
    [
        (["passed", "passed"], rs.EXIT_PASSED),
        (["passed", "not-run"], rs.EXIT_INCOMPLETE),
        (["not-run", "failed"], rs.EXIT_FAILED),
    ],
)
def test_a_failed_row_outranks_one_that_did_not_run(statuses, expected):
    rows = {str(index): rs.Row(str(index), "codex", "check", status=status) for index, status in enumerate(statuses)}
    assert rs.summarise(rows)[1] == expected


def test_trust_entries_are_read_from_the_isolated_home(tmp_path):
    (tmp_path / "config.toml").write_text(
        '[projects."/fixture/repo"]\ntrust_level = "trusted"\n\n'
        '[hooks.state."/fixture/repo/.codex/hooks.json:session_start:0:0"]\ntrusted_hash = "sha256:00"\n',
        encoding="utf-8",
    )
    assert rs.config_trust_entries(tmp_path) == {
        "projects": ["/fixture/repo (trusted)"],
        "hooks_state": ["/fixture/repo/.codex/hooks.json:session_start:0:0"],
    }
    assert rs.config_trust_entries(tmp_path / "absent") == {"projects": [], "hooks_state": []}


# --------------------------------------------------------- row judgements

GOOD_CODEX_SESSION = {"model": "m", "effort": "medium", "executing_version": "1.0"}


def _codex_lens(**changes):
    arguments = dict(failure=None, session=dict(GOOD_CODEX_SESSION), missing="", report="Reviewed abc1234def.",
                     model="m", effort="medium", head="abc1234def", pin="1.0")
    arguments.update(changes)
    return rs.codex_lens_problems("lens", **arguments)


@pytest.mark.parametrize(
    "changes, problem",
    [
        ({"failure": "exited 1"}, "lens: exited 1"),
        ({"session": None, "missing": "0 rollouts"}, "lens: no rollout (0 rollouts)"),
        ({"session": {**GOOD_CODEX_SESSION, "model": "other"}}, "lens: applied model 'other', configured 'm'"),
        ({"session": {**GOOD_CODEX_SESSION, "effort": "low"}}, "lens: applied effort 'low', configured 'medium'"),
        ({"report": "Reviewed something else."}, "lens: the report does not name the review head"),
        ({"session": {**GOOD_CODEX_SESSION, "executing_version": "0.9"}}, "not the pinned '1.0'"),
    ],
)
def test_each_codex_lens_guard_fails_the_lens_alone(changes, problem):
    assert _codex_lens() == []
    problems = _codex_lens(**changes)
    assert len(problems) == 1 and problem in problems[0], problems


GOOD_AGENT = {"agent_type": "lens", "models": ["claude-sonnet-5"], "efforts": ["high"], "executing_version": "1.0",
              "first_prompt": "the rendered prompt\n", "last_text": "Reviewed abc1234def."}


def _claude_lens(**changes):
    arguments = dict(failure=None, agent=dict(GOOD_AGENT), prompt="the rendered prompt", model="sonnet",
                     effort="high", head="abc1234def", pin="1.0")
    arguments.update(changes)
    return rs.claude_lens_problems("lens", **arguments)


@pytest.mark.parametrize(
    "changes, problem",
    [
        ({"failure": "exited 1"}, "lens: exited 1"),
        ({"agent": None}, "lens: the parent session launched no `lens` agent"),
        ({"agent": {**GOOD_AGENT, "first_prompt": "a paraphrase"}}, "the agent's prompt is not the one panel_prompt.py rendered"),
        ({"agent": {**GOOD_AGENT, "models": ["claude-opus-5"]}}, "applied models ['claude-opus-5'], configured 'sonnet'"),
        ({"agent": {**GOOD_AGENT, "models": []}}, "applied models [], configured 'sonnet'"),
        ({"agent": {**GOOD_AGENT, "models": ["claude-sonnet-5", "claude-opus-5"]}},
         "applied models ['claude-sonnet-5', 'claude-opus-5'], configured 'sonnet'"),
        ({"agent": {**GOOD_AGENT, "efforts": ["medium"]}}, "applied efforts ['medium'], configured 'high'"),
        ({"agent": {**GOOD_AGENT, "last_text": "Could not diff."}}, "the report does not name the review head"),
        ({"agent": {**GOOD_AGENT, "executing_version": "0.9"}}, "not the pinned '1.0'"),
    ],
)
def test_each_claude_lens_guard_fails_the_lens_alone(changes, problem):
    assert _claude_lens() == []
    problems = _claude_lens(**changes)
    assert len(problems) == 1 and problem in problems[0], problems


def test_the_lens_agent_is_chosen_by_its_agent_type():
    other = {**GOOD_AGENT, "agent_type": "general-purpose"}
    assert rs.lens_agent([other, GOOD_AGENT], "lens") is GOOD_AGENT
    assert rs.lens_agent([other], "lens") is None


def _lane(tmp_path, **changes):
    text = b"LANE-abc dev/smoke-codex"
    arguments = dict(
        launch_failure=None,
        receipt={"status": "completed", "terminal": {"final_text_sha256": rs.sha256_bytes(text)}},
        text_bytes=text, token="LANE-abc",
        session={"cwd": str(tmp_path), "executing_version": "1.0"}, worktree=tmp_path, pin="1.0",
    )
    arguments.update(changes)
    return rs.lane_problems(**arguments)


@pytest.mark.parametrize(
    "changes, problem",
    [
        ({"launch_failure": "exited 70"}, "launch_lane.py exited 70"),
        ({"receipt": {"status": "failed", "terminal": {"final_text_sha256": rs.sha256_bytes(b"LANE-abc dev/smoke-codex")}}},
         "receipt status 'failed'"),
        ({"receipt": {"status": "completed", "terminal": {"final_text_sha256": "0" * 64}}},
         "the final text is not the one the receipt binds"),
        ({"token": "LANE-other"}, "the final text does not carry the task token"),
        ({"session": {"cwd": "/elsewhere", "executing_version": "1.0"}}, "the lane session ran outside the descriptor worktree"),
        ({"session": {"cwd": None}}, "no lane session artifact recorded an executing version"),
        ({"session": {"executing_version": "0.9"}}, "not the pinned '1.0'"),
    ],
)
def test_each_lane_guard_fails_the_lane_alone(tmp_path, changes, problem):
    assert _lane(tmp_path) == []
    problems = _lane(tmp_path, **changes)
    assert len(problems) == 1 and problem in problems[0], problems


def test_the_lane_text_is_what_each_transport_digests():
    assert rs.lane_final_text("codex", b"raw bytes\n") == (b"raw bytes\n", None)
    result = json.dumps({"type": "result", "result": "LANE-x b", "session_id": "s1"}).encode()
    assert rs.lane_final_text("claude", result) == (b"LANE-x b", "s1")
    assert rs.lane_final_text("claude", b"[1, 2]") == (b"", None)
    assert rs.lane_final_text("claude", b"not json") == (b"", None)


def test_agents_md_must_load_as_the_claude_md_import(tmp_path):
    claude_md = {"file_path": str(tmp_path / "CLAUDE.md"), "load_reason": "session_start"}
    imported = {"file_path": str(tmp_path / "AGENTS.md"), "load_reason": "include",
                "parent_file_path": str(tmp_path / "CLAUDE.md")}
    assert rs.claude_instructions_ok([claude_md, imported], tmp_path)
    for agents_md in (
        {**imported, "load_reason": "session_start"},
        {**imported, "parent_file_path": str(tmp_path / "docs" / "other.md")},
        {key: value for key, value in imported.items() if key != "parent_file_path"},
    ):
        assert not rs.claude_instructions_ok([claude_md, agents_md], tmp_path), agents_md
    assert not rs.claude_instructions_ok([imported], tmp_path)
    assert not rs.claude_instructions_ok([claude_md], tmp_path)


def test_the_commands_row_needs_something_to_look_for():
    assert rs.claude_commands_ok(["pr-watch"], ["adversarial"], [], [])
    for arguments in (
        ([], ["adversarial"], [], []),
        (["pr-watch"], [], [], []),
        (["pr-watch"], ["adversarial"], ["pr-watch"], []),
        (["pr-watch"], ["adversarial"], [], ["adversarial"]),
    ):
        assert not rs.claude_commands_ok(*arguments), arguments


def test_a_passing_row_whose_runtime_is_not_the_pin_fails():
    mismatch = "the executing runtime reported '0.9', not the pinned '1.0'"
    rows = [rs.Row(str(index), "codex", "check") for index in range(3)]
    rs._finish(rows[0], True, mismatch, {"seen": 1}, "it passed", "it failed")
    rs._finish(rows[1], True, None, {}, "it passed", "it failed")
    rs._finish(rows[2], False, mismatch, {}, "it passed", "it failed")
    assert [(row.status, row.reason) for row in rows] == [
        ("failed", f"it passed, but {mismatch}"), ("passed", "it passed"), ("failed", "it failed"),
    ]
    assert rows[0].evidence == {"seen": 1}


def test_two_candidates_for_one_session_fail_closed(tmp_path):
    day = tmp_path / "codex" / "sessions" / "2026" / "10" / "02"
    day.mkdir(parents=True)
    meta = json.dumps({"type": "session_meta", "payload": {"cwd": str(tmp_path / "repo")}}) + "\n"
    (day / "rollout-a-t1.jsonl").write_text(meta, encoding="utf-8")
    for thread in ("t1", None):
        assert rs.locate_rollout(tmp_path / "codex", thread_id=thread, cwd=tmp_path / "repo", since=0)[0] is not None
    (day / "rollout-b-t1.jsonl").write_text(meta, encoding="utf-8")
    for thread in ("t1", None):
        assert rs.locate_rollout(tmp_path / "codex", thread_id=thread, cwd=tmp_path / "repo", since=0)[0] is None
    projects = tmp_path / "claude" / "projects"
    (projects / "p1").mkdir(parents=True)
    (projects / "p1" / "s1.jsonl").write_text("{}\n", encoding="utf-8")
    assert rs.find_claude_transcript(tmp_path / "claude", "s1") == projects / "p1" / "s1.jsonl"
    (projects / "p2").mkdir()
    (projects / "p2" / "s1.jsonl").write_text("{}\n", encoding="utf-8")
    assert rs.find_claude_transcript(tmp_path / "claude", "s1") is None


def test_missing_commands_and_lens_agents_are_named():
    init = {"slash_commands": ["/wrap-up", "pr-watch"], "agents": ["adversarial"]}
    assert rs.claude_missing(init, ["pr-watch", "wrap-up"], ["adversarial"]) == ([], [])
    assert rs.claude_missing(init, ["pr-watch", "parallel"], ["adversarial", "correctness"]) == (["parallel"], ["correctness"])


@pytest.mark.parametrize(
    "changes",
    [
        {"problem": "exited 1"},
        {"listed": False},
        {"invoked": False},
        {"result": {"is_error": True, "result": "a review"}},
        {"result": {"is_error": False, "result": "  "}},
        {"result": {"result": "a review"}},
        {"result": {}},
    ],
)
def test_each_claude_review_condition_is_required(changes):
    arguments = dict(problem=None, listed=True, invoked=True, result={"is_error": False, "result": "a review"})
    assert rs.claude_review_ok(**arguments)
    arguments.update(changes)
    assert not rs.claude_review_ok(**arguments)


def test_ls_remote_is_not_a_lens_git_allowance():
    # `git ls-remote --upload-pack=<command>` runs <command>.
    assert rs.CLAUDE_LENS_GIT and not [rule for rule in rs.CLAUDE_LENS_GIT if "ls-remote" in rule]


def test_fixture_children_inherit_no_lane_identity_or_home(monkeypatch):
    scrubbed = {"DEVKIT_STATE_ROOT", "GIT_DIR", "GIT_CONFIG_GLOBAL", "GH_REPO", "JOB_NAME", "FORCE_COLOR",
                "CODEX_HOME", "CLAUDE_CONFIG_DIR", "PWD", "OLDPWD"}
    for key in scrubbed:
        monkeypatch.setenv(key, "inherited")
    monkeypatch.setenv("SMOKE_KEPT", "kept")
    env = rs.scrubbed_environment()
    assert env["SMOKE_KEPT"] == "kept"
    assert not scrubbed & set(env)


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("hangs_on, reason", [("--version", "<--version failed"), ("status", "did not answer")])
def test_a_client_that_does_not_answer_its_preflight_is_a_reason_not_a_crash(tmp_path, monkeypatch, runtime, hangs_on, reason):
    monkeypatch.setattr(rs, "PREFLIGHT_TIMEOUT", 1)
    preflight, version = {
        "codex": (rs.codex_preflight, f"codex-cli {FAKE_VERSION}"),
        "claude": (rs.claude_preflight, f"{FAKE_VERSION} (Claude Code)"),
    }[runtime]
    client = tmp_path / runtime
    client.write_text(
        f'#!/bin/sh\ncase " $* " in *" {hangs_on} "*) exec sleep 30;; esac\necho "{version}"\n', encoding="utf-8"
    )
    client.chmod(0o755)
    _facts, problem = preflight(client, FAKE_VERSION, tmp_path, dict(os.environ))
    assert problem and reason in problem, problem


@pytest.mark.parametrize("expectation", ["budget", "followup"])
def test_an_engine_that_does_not_finish_refuses_the_run(tmp_path, monkeypatch, expectation):
    def hang(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(rs.subprocess, "run", hang)
    fixture = types.SimpleNamespace(engines=tmp_path, repo=tmp_path, friction_rel="docs/log.md", friction_lines=120)
    with pytest.raises(rs.Refusal, match="did not finish"):
        if expectation == "budget":
            rs.expected_budget_line(fixture, {})
        else:
            rs.expected_followup_marker(fixture, "codex", "printf x", "https://x.invalid/pull/1", {})


@pytest.mark.parametrize(
    "raised, message",
    [
        (KeyboardInterrupt(), "interrupted; every client process group it was running is stopped; no record was written to --out"),
        (RuntimeError("boom"), "failed: RuntimeError: boom; every client process group it was running is stopped; no record"),
    ],
    ids=["interrupt", "exception"],
)
def test_a_run_that_cannot_finish_stops_its_clients_and_exits_aborted(tmp_path, monkeypatch, capsys, raised, message):
    monkeypatch.setattr(rs, "_INTERRUPTED", False)
    monkeypatch.setattr(rs, "_STOPPING", False)
    before = {signum: signal.getsignal(signum) for signum in rs.INTERRUPT_SIGNALS}
    stopped = []

    def fail(*_args):
        for signum, handler in before.items():
            assert signal.getsignal(signum) is (signal.SIG_IGN if handler is signal.SIG_IGN else rs._interrupt), signum
        raise raised

    monkeypatch.setattr(rs, "resolve_revision", lambda _root, _revision: "0" * 40)
    monkeypatch.setattr(rs, "verify_harness", lambda _root, _revision: {})
    monkeypatch.setattr(rs, "stop_live_children", lambda: stopped.append(True) or [])
    monkeypatch.setattr(rs, "run", fail)
    assert rs.main(["--work-root", str(tmp_path), "--out", str(tmp_path / "out")]) == rs.EXIT_ABORTED
    assert message in capsys.readouterr().err
    assert stopped == [True]
    assert {signum: signal.getsignal(signum) for signum in rs.INTERRUPT_SIGNALS} == before


@pytest.mark.parametrize(
    "raised, account",
    [
        (RuntimeError("boom"), "failed: RuntimeError: boom; every client process group it was running is stopped"),
        # Raised as no handler of the runner's would: the latch is still unset.
        (KeyboardInterrupt(), "interrupted; every client process group it was running is stopped"),
    ],
    ids=["failure", "interrupt"],
)
def test_a_signal_during_an_abort_stop_does_not_cut_it_short(tmp_path, monkeypatch, capsys, raised, account):
    monkeypatch.setattr(rs, "_INTERRUPTED", False)
    monkeypatch.setattr(rs, "_STOPPING", False)
    monkeypatch.setattr(rs, "resolve_revision", lambda _root, _revision: "0" * 40)
    monkeypatch.setattr(rs, "verify_harness", lambda _root, _revision: {})
    stops = []

    def fail(*_args):
        raise raised

    def stop_while_signalled():
        assert signal.getsignal(signal.SIGTERM) is rs._interrupt
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(0.3)  # the handler runs here
        stops.append(True)
        return []

    monkeypatch.setattr(rs, "run", fail)
    monkeypatch.setattr(rs, "stop_live_children", stop_while_signalled)
    try:
        code = rs.main(["--work-root", str(tmp_path), "--out", str(tmp_path / "out")])
    except KeyboardInterrupt:
        pytest.fail("a signal during the abort's stop escaped main")
    assert code == rs.EXIT_ABORTED and stops == [True]
    assert account in capsys.readouterr().err


def _gone(pid: int, wait: float = 15.0) -> bool:
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError):
            return True
        # A zombie has exited; only its reaping is outstanding, which an orphan
        # waits on from whichever process adopted it.
        try:
            state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            state = ""
        if state.strip().startswith("Z"):
            return True
        time.sleep(0.1)
    return False


def test_an_interrupt_raises_once(monkeypatch):
    monkeypatch.setattr(rs, "_INTERRUPTED", False)
    with pytest.raises(KeyboardInterrupt):
        rs._interrupt(signal.SIGTERM, None)
    try:
        repeated = rs._interrupt(signal.SIGTERM, None)
    except KeyboardInterrupt:
        pytest.fail("a repeated interrupt raised again")
    assert repeated is None


def test_a_signal_inherited_ignored_stays_ignored(monkeypatch):
    monkeypatch.setattr(rs, "_INTERRUPTED", False)
    monkeypatch.setattr(rs, "_STOPPING", False)
    before = {signum: signal.getsignal(signum) for signum in rs.INTERRUPT_SIGNALS}
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        previous = rs.install_interrupts()
        assert signal.getsignal(signal.SIGHUP) is signal.SIG_IGN and signal.SIGHUP not in previous
        assert previous and all(signal.getsignal(signum) is rs._interrupt for signum in previous)
    finally:
        for signum, handler in before.items():
            signal.signal(signum, signal.SIG_DFL if handler is None else handler)


def test_no_client_starts_once_the_stop_has_begun(tmp_path, monkeypatch):
    monkeypatch.setattr(rs, "_STOPPING", False)
    monkeypatch.setattr(rs, "_LIVE_GROUPS", set())
    rs.stop_live_children()
    assert rs._STOPPING
    marker = tmp_path / "started"
    invocation = rs.run_child(
        ["touch", str(marker)], cwd=tmp_path, env=dict(os.environ), stdin_text="", timeout=10, log_dir=tmp_path,
        name="late",
    )
    assert rs.invocation_ok(invocation) == "not started: the run is stopping"
    assert not marker.exists()


def test_a_client_an_interrupt_catches_mid_stop_stays_registered_until_stopped(tmp_path, monkeypatch):
    """A timeout's stop waits out its grace for a descendant that ignores SIGTERM after
    its leader has died; an interrupt in that wait must leave the group, which still has
    a member, for `stop_live_children`."""
    monkeypatch.setattr(rs, "_LIVE_GROUPS", set())
    monkeypatch.setattr(rs, "_STOPPING", False)
    leader, descendant = tmp_path / "leader", tmp_path / "descendant"

    def interrupt(_signum, _frame):
        raise KeyboardInterrupt("an interrupt during the stop")

    previous = signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, 3)
    try:
        with pytest.raises(KeyboardInterrupt):
            rs.run_child(
                ["bash", "-c", f"echo $$ > {leader}; (trap '' TERM; sleep 300 & echo $! > {descendant}; wait) & wait"],
                cwd=tmp_path, env=dict(os.environ), stdin_text="", timeout=1, log_dir=tmp_path, name="stubborn",
            )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    assert _gone(int(leader.read_text(encoding="utf-8")))
    assert len(rs._LIVE_GROUPS) == 1
    assert rs.stop_live_children() == []
    assert _gone(int(descendant.read_text(encoding="utf-8")))


def test_a_group_that_outlives_the_stop_is_named(monkeypatch):
    monkeypatch.setattr(rs, "_STOPPING", False)
    monkeypatch.setattr(rs, "_LIVE_GROUPS", {424242})
    monkeypatch.setattr(rs.os, "killpg", lambda _group, _signum: None)
    monkeypatch.setattr(rs, "_group_alive", lambda _group: True)
    survivors = rs.stop_live_children(grace=0.2)
    assert survivors == [424242]
    assert rs.stopped(survivors) == "client process groups that outlived the stop: 424242"
    assert rs.stopped([]) == "every client process group it was running is stopped"


def test_what_a_stopped_run_left_at_out_is_read_from_the_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(rs, "_RUN_ID", "adk-smoke-this")
    assert rs.left_at(tmp_path / "absent") == "no record was written to --out"
    for written in ("not json", json.dumps({"run_id": "adk-smoke-another"})):
        (tmp_path / "record.json").write_text(written, encoding="utf-8")
        assert rs.left_at(tmp_path) == "no record was written to --out", written
    (tmp_path / "record.json").write_text(json.dumps({"run_id": "adk-smoke-this"}), encoding="utf-8")
    assert rs.left_at(tmp_path) == "the record at --out was complete before the run stopped"
    # Before a run has its id, nothing at --out is its record, not even one without an id.
    monkeypatch.setattr(rs, "_RUN_ID", None)
    (tmp_path / "record.json").write_text("{}", encoding="utf-8")
    assert rs.left_at(tmp_path) == "no record was written to --out"


def test_a_group_that_refuses_its_signal_counts_as_stopped(monkeypatch):
    """macOS refuses a signal to a group whose only member is an unreaped zombie."""
    def refuse(_group, _signum):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(rs.os, "killpg", refuse)
    rs._stop_group(types.SimpleNamespace(pid=424242, poll=lambda: 0), grace=0.1)


class _GoneStream:
    """A stderr whose terminal has closed."""

    def write(self, _text):
        raise OSError(5, "Input/output error")

    def flush(self):
        raise OSError(5, "Input/output error")


@pytest.mark.parametrize(
    "raised, code",
    [
        (KeyboardInterrupt(), rs.EXIT_ABORTED),
        (RuntimeError("boom"), rs.EXIT_ABORTED),
        (rs.Refusal("no"), rs.EXIT_REFUSED),
    ],
    ids=["interrupt", "failure", "refusal"],
)
def test_the_exit_status_survives_a_stderr_that_is_gone(tmp_path, monkeypatch, raised, code):
    monkeypatch.setattr(rs, "_INTERRUPTED", False)
    monkeypatch.setattr(rs, "_STOPPING", False)
    monkeypatch.setattr(rs, "resolve_revision", lambda _root, _revision: "0" * 40)
    monkeypatch.setattr(rs, "verify_harness", lambda _root, _revision: {})
    monkeypatch.setattr(rs, "stop_live_children", lambda: [])

    def fail(*_args):
        raise raised

    monkeypatch.setattr(rs, "run", fail)
    monkeypatch.setattr(sys, "stderr", _GoneStream())
    assert rs.main(["--work-root", str(tmp_path), "--out", str(tmp_path / "out")]) == code


def test_a_new_run_starts_unstopped_and_its_handlers_come_back(monkeypatch):
    for name, value in (("_INTERRUPTED", True), ("_STOPPING", True), ("_RUN_ID", "adk-smoke-old")):
        monkeypatch.setattr(rs, name, value)
    before = {signum: signal.getsignal(signum) for signum in rs.INTERRUPT_SIGNALS}
    try:
        previous = rs.install_interrupts()
        assert (rs._INTERRUPTED, rs._STOPPING, rs._RUN_ID) == (False, False, None)
        rs.restore_interrupts(previous)
        assert {signum: signal.getsignal(signum) for signum in rs.INTERRUPT_SIGNALS} == before
        # A handler installed outside Python comes back from `signal.signal` as None.
        rs.restore_interrupts({signal.SIGHUP: None})
        assert signal.getsignal(signal.SIGHUP) is signal.SIG_DFL
    finally:
        rs.restore_interrupts(before)


def test_a_home_or_binary_that_is_not_what_it_claims_is_refused(tmp_path):
    with pytest.raises(rs.Refusal, match="is not an existing directory"):
        rs.check_isolated_home(
            tmp_path / "missing", flag="--codex-home", env_key="CODEX_HOME", fallback=".codex", kit_root=tmp_path / "kit"
        )
    with pytest.raises(rs.Refusal, match="must be an absolute path"):
        rs.check_binary(Path("codex"), "--codex-bin")
    plain = tmp_path / "plain"
    plain.write_text("", encoding="utf-8")
    plain.chmod(0o644)
    with pytest.raises(rs.Refusal, match="is not an executable file"):
        rs.check_binary(plain, "--codex-bin")


def _quick_stops(monkeypatch):
    """The runner's own stop, with a one-second grace for the unit tests."""
    stop_group = rs._stop_group
    monkeypatch.setattr(rs, "_stop_group", lambda process: stop_group(process, grace=1))


def test_a_child_that_outlives_its_timeout_is_stopped_with_what_it_started(tmp_path, monkeypatch):
    """The leader dies on SIGTERM; a descendant ignores it. The stop waits for the
    group, not its leader, so only its SIGKILL ends the descendant."""
    _quick_stops(monkeypatch)
    leader, descendant = tmp_path / "leader", tmp_path / "descendant"
    invocation = rs.run_child(
        ["bash", "-c", f"echo $$ > {leader}; (trap '' TERM; sleep 300 & echo $! > {descendant}; wait) & wait"],
        cwd=tmp_path, env=dict(os.environ), stdin_text="", timeout=2, log_dir=tmp_path, name="hang",
    )
    assert rs.invocation_ok(invocation) == "timed out after 2s"
    started = [int(path.read_text(encoding="utf-8")) for path in (leader, descendant)]
    assert all(_gone(pid) for pid in started)
    assert not rs._LIVE_GROUPS


def test_what_a_client_leaves_in_its_group_goes_with_it(tmp_path, monkeypatch):
    _quick_stops(monkeypatch)
    descendant = tmp_path / "descendant"
    invocation = rs.run_child(
        ["bash", "-c", f"(trap '' TERM; sleep 300 & echo $! > {descendant}; wait) & sleep 0.5; exit 0"],
        cwd=tmp_path, env=dict(os.environ), stdin_text="", timeout=30, log_dir=tmp_path, name="leaves",
    )
    assert rs.invocation_ok(invocation) is None and invocation["group_outlived_client"]
    assert _gone(int(descendant.read_text(encoding="utf-8")))
    assert not rs._LIVE_GROUPS


# ------------------------------------------------------------ refusals


def test_the_operators_own_homes_are_refused(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    exported = tmp_path / "exported-codex-home"
    exported.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(exported))
    kit = tmp_path / "kit"
    (kit / "inside").mkdir(parents=True)
    isolated = tmp_path / "isolated"
    isolated.mkdir()

    def check(path):
        return rs.check_isolated_home(path, flag="--codex-home", env_key="CODEX_HOME", fallback=".codex", kit_root=kit)

    for refused in (home / ".codex", exported, kit / "inside"):
        with pytest.raises(rs.Refusal):
            check(refused)
    with pytest.raises(rs.Refusal):
        check(Path("relative"))
    assert check(isolated) == Path(rs.realpath(isolated))


def _git_env(base: Path) -> dict[str, str]:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CEILING_DIRECTORIES=str(base))
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    return env


def _commit_all(root: Path, env: dict[str, str], message: str) -> str:
    identity = ["-c", "user.name=smoke test", "-c", "user.email=smoke@test.invalid"]
    subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True, capture_output=True)
    subprocess.run(["git", *identity, "commit", "-q", "-m", message], cwd=root, env=env, check=True, capture_output=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, env=env, check=True, capture_output=True, text=True).stdout.strip()


def test_the_harness_must_be_the_revisions_own_bytes(tmp_path, monkeypatch):
    env = _git_env(tmp_path)
    kit = tmp_path / "kit"
    (kit / "scripts" / "lib").mkdir(parents=True)
    script = kit / "scripts" / "runtime_smoke.py"
    shutil.copy2(RUNNER, script)
    shutil.copy2(ENGINE_DIR / "lib" / "kitconfig.py", kit / "scripts" / "lib" / "kitconfig.py")
    subprocess.run(["git", "init", "-q"], cwd=kit, env=env, check=True)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sha = _commit_all(kit, env, "harness")
    monkeypatch.setattr(rs, "SCRIPT_PATH", script.resolve())

    digests = rs.verify_harness(kit.resolve(), sha)
    assert set(digests) == {"scripts/runtime_smoke.py", "scripts/lib/kitconfig.py"}

    (kit / "scripts" / "lib" / "kitconfig.py").write_text("# edited after the commit\n", encoding="utf-8")
    with pytest.raises(rs.Refusal, match="kitconfig.py differs"):
        rs.verify_harness(kit.resolve(), sha)


# ------------------------------------------------------------ fake clients

FAKE_CODEX = r'''#!{python}
"""A stand-in `codex` for the smoke runner's tests. Never a real client."""
import json, os, re, subprocess, sys, uuid
from pathlib import Path

VERSION = "{version}"
args = sys.argv[1:]
if args == ["--version"]:
    print(f"codex-cli {{VERSION}}")
    sys.exit(0)
if args[:2] == ["login", "status"]:
    if os.environ.get("FAKE_CODEX_LOGGED_OUT") == "1":
        print("Not logged in")
        sys.exit(1)
    print("Logged in using a fake credential")
    sys.exit(0)
if not args or args[0] != "exec":
    sys.exit(64)
args = args[1:]
review = bool(args) and args[0] == "review"
if review:
    args = args[1:]
values = {{"-C": None, "--cd": None, "-o": None, "--output-last-message": None, "-m": None, "-s": None,
          "--sandbox": None, "--base": None}}
configs, flags, read_stdin, i = [], set(), False, 0
while i < len(args):
    arg = args[i]
    if arg in values:
        values[arg] = args[i + 1]
        i += 2
    elif arg in ("-c", "--config"):
        configs.append(args[i + 1])
        i += 2
    elif arg == "-":
        read_stdin = True
        i += 1
    else:
        flags.add(arg)
        i += 1
prompt = sys.stdin.read() if read_stdin else ""
cwd = Path(values["-C"] or values["--cd"] or os.getcwd())
last = values["-o"] or values["--output-last-message"]
effort = next((item.split("=", 1)[1] for item in configs if item.startswith("model_reasoning_effort=")), "medium")
thread = str(uuid.uuid4())
day = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "10" / "02"
day.mkdir(parents=True, exist_ok=True)
entries = []

def add(kind, payload):
    entries.append({{"type": kind, "payload": payload}})

def message(role, text):
    add("response_item", {{"type": "message", "role": role, "content": [{{"type": "input_text", "text": text}}]}})

add("session_meta", {{"id": thread, "cli_version": VERSION, "originator": "codex_exec", "source": "exec", "cwd": str(cwd)}})
# Only the panel lenses pass -m, so this misapplies a lens's model and nothing else.
applied_model = (os.environ.get("FAKE_CODEX_LENS_MODEL") or values["-m"]) if values["-m"] else "fake-default"
add("turn_context", {{"model": applied_model, "effort": effort, "approval_policy": "never",
                      "sandbox_policy": {{"type": values["-s"] or values["--sandbox"] or "read-only"}}, "cwd": str(cwd)}})
if (cwd / "AGENTS.md").is_file():
    # The shape the live 0.153.4 client wrote under an isolated home.
    add("world_state", {{"full": True, "state": {{"agents_md": {{
        "directory": str(cwd), "text": (cwd / "AGENTS.md").read_text(encoding="utf-8")}}}}}})
skills = cwd / ".agents" / "skills"
if skills.is_dir():
    lines = ["<skills_instructions>", "## Skills", "### Skill roots", f"- `r0` = `{{skills}}`", "### Available skills"]
    lines += [f"- {{s.parent.name}}: fake. (file: r0/{{s.parent.name}}/SKILL.md)" for s in sorted(skills.glob("*/SKILL.md"))]
    lines.append("</skills_instructions>")
    message("developer", "\n".join(lines))

# A project's hooks load only for a trusted project, and run only with their
# definitions trusted: the two layers the live client showed.
project_trusted = any(item.startswith("projects=") and json.dumps(os.path.realpath(cwd)) in item
                      and 'trust_level="trusted"' in item for item in configs)
hooks = {{}}
if project_trusted and "--dangerously-bypass-hook-trust" in flags and (cwd / ".codex" / "hooks.json").is_file():
    hooks = json.loads((cwd / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]

def run_hooks(event, payload):
    texts = []
    for group in hooks.get(event, []):
        if group.get("matcher") and not re.search(group["matcher"], "Bash"):
            continue
        for hook in group["hooks"]:
            done = subprocess.run(["bash", "-c", hook["command"]], cwd=cwd, input=json.dumps(payload),
                                  capture_output=True, text=True, timeout=hook.get("timeout", 30))
            texts.append(done.stdout)
    return texts

for text in run_hooks("SessionStart", {{"hook_event_name": "SessionStart", "source": "startup", "cwd": str(cwd)}}):
    if text.strip():
        message("developer", text)

def hang(step):
    # Stands still in a process group with a child of its own, both ignoring SIGTERM, so
    # only a stop's SIGKILL escalation ends them; for the interrupt tests.
    if os.environ.get("FAKE_CODEX_HANG") != step:
        return
    import signal, time
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child = subprocess.Popen(["sleep", "300"])
    pids = Path(os.environ["FAKE_PID_DIR"]) / f"{{uuid.uuid4()}}.pid"
    pids.write_text(f"{{os.getpid()}} {{child.pid}}\n", encoding="utf-8")
    time.sleep(300)

if "SMOKE-DONE-" in prompt:
    hang("probe")
    if os.environ.get("FAKE_CODEX_WRITES_TRUST") == "1":
        # What #802 saw a client write into the home it ran under.
        with (Path(os.environ["CODEX_HOME"]) / "config.toml").open("a", encoding="utf-8") as handle:
            handle.write(f"\n[projects.{{json.dumps(str(cwd))}}]\ntrust_level = \"trusted\"\n")
    command = re.search(r"^(printf .+)$", prompt, re.M).group(1)
    output = subprocess.run(["bash", "-c", command], capture_output=True, text=True).stdout
    payload = {{"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {{"command": command}},
               "tool_response": {{"stdout": output, "stderr": "", "exit_code": 0}}, "cwd": str(cwd)}}
    answers = [json.loads(text)["hookSpecificOutput"]["additionalContext"]
               for text in run_hooks("PostToolUse", payload) if text.strip()]
    early = os.environ.get("FAKE_CODEX_HOOK_BEFORE_CALL") == "1"
    for answer in answers if early else []:
        message("developer", answer)
    add("response_item", {{"type": "function_call", "name": "shell", "call_id": "c1", "arguments": json.dumps({{"command": command}})}})
    # The live client wrote the hook's context between the call and its output.
    for answer in [] if early else answers:
        message("developer", answer)
    add("response_item", {{"type": "function_call_output", "call_id": "c1", "output": output}})
    final = re.search(r"SMOKE-DONE-[0-9a-f]+", prompt).group(0)
elif review:
    if os.environ.get("FAKE_CODEX_REVIEW_NO_MARKERS") != "1":
        add("event_msg", {{"type": "item_completed", "item": {{"type": "EnteredReviewMode"}}}})
        add("event_msg", {{"type": "item_completed", "item": {{"type": "ExitedReviewMode"}}}})
    # The reviewer runs as a child session of its own, as the live client's did.
    child = str(uuid.uuid4())
    (day / f"rollout-2026-10-02T00-00-01-{{child}}.jsonl").write_text("".join(json.dumps(entry) + "\n" for entry in (
        {{"type": "session_meta", "payload": {{"id": child, "cli_version": VERSION, "source": {{"subagent": "review"}}, "cwd": str(cwd)}}}},
        {{"type": "turn_context", "payload": {{"model": "fake-reviewer", "effort": effort}}}},
    )), encoding="utf-8")
    final = "" if os.environ.get("FAKE_CODEX_REVIEW_SILENT") == "1" else "Fake review: one finding in docs/smoke-review-target.md."
elif "LANE-" in prompt:
    hang("lane")
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    token = "" if os.environ.get("FAKE_CODEX_LANE_NO_TOKEN") == "1" else re.search(r"LANE-[0-9a-f]+", prompt).group(0)
    final = f"{{token}} {{branch}}".strip()
else:
    hang("lens")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    final = f"Reviewed {{head}}."
message("assistant", final)
(day / f"rollout-2026-10-02T00-00-00-{{thread}}.jsonl").write_text(
    "".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
if last:
    Path(last).write_text(final, encoding="utf-8")
if "--json" in flags:
    print(json.dumps({{"type": "thread.started", "thread_id": thread}}))
if review and os.environ.get("FAKE_CODEX_REVIEW_EXIT") == "1":
    sys.exit(1)
'''

FAKE_CLAUDE = r'''#!{python}
"""A stand-in `claude` for the smoke runner's tests. Never a real client."""
import hashlib, json, os, re, subprocess, sys, uuid
from pathlib import Path

VERSION = "{version}"
args = sys.argv[1:]
if args == ["--version"]:
    print(f"{{VERSION}} (Claude Code)")
    sys.exit(0)
if args[:2] == ["auth", "status"]:
    logged_in = os.environ.get("FAKE_CLAUDE_LOGGED_OUT") != "1"
    print(json.dumps({{"loggedIn": logged_in, "authMethod": "fake" if logged_in else "none"}}))
    sys.exit(0 if logged_in else 1)
values = {{"--output-format": "text", "--setting-sources": "user,project,local", "--permission-mode": None,
          "--settings": None, "--model": None, "--agent": None}}
allowed, positional, i = [], [], 0
while i < len(args):
    arg = args[i]
    if arg in values:
        values[arg] = args[i + 1]
        i += 2
    elif arg in ("--allowedTools", "--allowed-tools"):
        i += 1
        while i < len(args) and not args[i].startswith("-"):
            allowed += [item for item in args[i].split(",") if item]
            i += 1
    elif arg == "--":
        positional += args[i + 1:]
        break
    elif arg.startswith("-"):
        i += 1
    else:
        positional.append(arg)
        i += 1
prompt = " ".join(positional) if positional else sys.stdin.read()
cwd = Path.cwd()
config = Path(os.environ["CLAUDE_CONFIG_DIR"])
session = str(uuid.uuid4())
project = "project" in values["--setting-sources"].split(",")
settings = {{}}
if values["--settings"]:
    raw = values["--settings"]
    settings = json.loads(raw if raw.lstrip().startswith("{{") else Path(raw).read_text(encoding="utf-8"))
project_settings = json.loads((cwd / ".claude" / "settings.json").read_text(encoding="utf-8")) if project else {{}}
model, effort = values["--model"] or "default", "medium"
if values["--agent"]:
    front = (cwd / ".claude" / "agents" / f"{{values['--agent']}}.md").read_text(encoding="utf-8").split("---")[1]
    model = re.search(r'^model:\s*"?([^"\n]+)"?', front, re.M).group(1)
    effort = re.search(r"^effort:\s*(\S+)", front, re.M).group(1)
model_id = f"claude-{{model}}-fake"
events, transcript = [], []
commands = sorted(p.stem for p in (cwd / ".claude" / "commands").glob("*.md")) if project else []
agents = sorted(p.stem for p in (cwd / ".claude" / "agents").glob("*.md")) if project else []
omitted = os.environ.get("FAKE_CLAUDE_INIT_OMIT")
commands, agents = [name for name in commands if name != omitted], [name for name in agents if name != omitted]
if not (os.environ.get("FAKE_CLAUDE_NO_INIT") == "1" and "SMOKE-DONE-" in prompt):
    events.append({{"type": "system", "subtype": "init", "session_id": session, "cwd": str(cwd), "model": model_id,
                    "claude_code_version": VERSION, "slash_commands": commands + ["code-review"], "agents": agents,
                    "permissionMode": values["--permission-mode"], "apiKeySource": "none"}})
env = dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd))

def run(command, payload):
    return subprocess.run(["bash", "-c", command], cwd=cwd, env=env, input=json.dumps(payload),
                          capture_output=True, text=True, timeout=60).stdout

for group in settings.get("hooks", {{}}).get("InstructionsLoaded", []):
    for hook in group["hooks"]:
        for name, reason in (("CLAUDE.md", "session_start"), ("AGENTS.md", "include")):
            if project and (cwd / name).is_file():
                payload = {{"hook_event_name": "InstructionsLoaded", "file_path": str(cwd / name),
                           "memory_type": "Project", "load_reason": reason}}
                if reason == "include":
                    # 2.1.287 names the file that imported it.
                    payload["parent_file_path"] = str(cwd / "CLAUDE.md")
                run(hook["command"], payload)

def hook_events(event, payload, tool="Bash"):
    outputs = []
    for group in project_settings.get("hooks", {{}}).get(event, []):
        if group.get("matcher") and not re.search(group["matcher"], tool):
            continue
        for hook in group["hooks"]:
            out = run(hook["command"], payload)
            if os.environ.get("FAKE_CLAUDE_SILENT_HOOK") == event:
                out = ""
            outputs.append(out)
            events.append({{"type": "system", "subtype": "hook_response", "hook_event": event, "output": out, "stdout": out}})
    return outputs

hook_events("SessionStart", {{"hook_event_name": "SessionStart", "source": "startup"}})
encoded = re.sub(r"[/.]", "-", str(cwd))
# Kept under a directory name's length limit, so a long temporary path cannot fail the
# fake; the runner finds a transcript by its session id, never by this name.
if len(encoded) > 200:
    encoded = encoded[:160] + "-" + hashlib.sha256(encoded.encode()).hexdigest()[:16]
folder = config / "projects" / encoded
folder.mkdir(parents=True, exist_ok=True)

def frontmatter(agent):
    front = (cwd / ".claude" / "agents" / f"{{agent}}.md").read_text(encoding="utf-8").split("---")[1]
    return (re.search(r'^model:\s*"?([^"\n]+)"?', front, re.M).group(1), re.search(r"^effort:\s*(\S+)", front, re.M).group(1))

def subagent(agent_type, prompt_text, sub_model_id, sub_effort, text):
    # Where 2.1.287 keeps a subagent: beside the session transcript, with a .meta.json.
    sub = folder / session / "subagents"
    sub.mkdir(parents=True, exist_ok=True)
    name = "agent-" + uuid.uuid4().hex[:16]
    (sub / f"{{name}}.meta.json").write_text(json.dumps({{"agentType": agent_type, "requestShape": "foreground"}}), encoding="utf-8")
    entries = [
        {{"type": "user", "isSidechain": True, "version": VERSION, "message": {{"role": "user", "content": prompt_text}}}},
        {{"type": "assistant", "isSidechain": True, "version": VERSION, "effort": sub_effort,
          "message": {{"model": sub_model_id, "content": [{{"type": "text", "text": text}}]}}}},
    ]
    (sub / f"{{name}}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")

transcript.append({{"type": "user", "version": VERSION, "cwd": str(cwd), "sessionId": session,
                   "message": {{"role": "user", "content": prompt.strip() if prompt.startswith("/") else prompt}}}})
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
if "SMOKE-DONE-" in prompt:
    command = re.search(r"^(printf .+)$", prompt, re.M).group(1)
    if "Bash(printf:*)" in allowed:
        output = subprocess.run(["bash", "-c", command], capture_output=True, text=True).stdout
        post = {{"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {{"command": command}},
                "tool_response": {{"stdout": output, "stderr": "", "interrupted": False}}}}
        hooked = os.environ.get("FAKE_CLAUDE_NO_POSTTOOL_HOOK") != "1"
        early = os.environ.get("FAKE_CLAUDE_HOOK_BEFORE_CALL") == "1"
        if hooked and early:
            hook_events("PostToolUse", post)
        events.append({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "id": "t1", "name": "Bash", "input": {{"command": command}}}}]}}}})
        # The live client streamed the hook's events between the call and its result.
        if hooked and not early:
            hook_events("PostToolUse", post)
        if os.environ.get("FAKE_CLAUDE_NO_TOOL_RESULT") != "1":
            events.append({{"type": "user", "message": {{"content": [{{"type": "tool_result", "tool_use_id": "t1", "content": output}}]}}}})
    result = re.search(r"SMOKE-DONE-[0-9a-f]+", prompt).group(0)
elif prompt.startswith("/"):
    # 2.1.287 records a command as its literal text, then a local_command entry.
    result = "Fake review: one finding."
    subagent("general-purpose", "Review the diff.", "claude-opus-fake", "medium", result)
    if os.environ.get("FAKE_CLAUDE_REVIEW_UNRECORDED") == "1":
        transcript[-1]["message"]["content"] = "a review, described in prose"
    else:
        transcript.append({{"type": "system", "subtype": "local_command",
                           "content": f"<local-command-stdout>{{result}}</local-command-stdout>"}})
elif "-----BEGIN LENS PROMPT-----" in prompt:
    lens = re.search(r"Launch the `([^`]+)` agent", prompt).group(1)
    lens_prompt = prompt.split("-----BEGIN LENS PROMPT-----\n", 1)[1].rsplit("\n-----END LENS PROMPT-----", 1)[0]
    lens_model, lens_effort = frontmatter(lens)
    lens_effort = os.environ.get("FAKE_CLAUDE_LENS_EFFORT") or lens_effort
    subagent(lens, lens_prompt, f"claude-{{lens_model}}-fake", lens_effort, f"Reviewed {{head}}.")
    result = "LENS-DONE"
elif "LANE-" in prompt:
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    token = "" if os.environ.get("FAKE_CLAUDE_LANE_NO_TOKEN") == "1" else re.search(r"LANE-[0-9a-f]+", prompt).group(0)
    result = f"{{token}} {{branch}}".strip()
else:
    result = f"Reviewed {{head}}."
transcript.append({{"type": "assistant", "version": VERSION, "cwd": str(cwd), "effort": effort, "message": {{"model": model_id}}}})
final = {{"type": "result", "subtype": "success", "is_error": False, "result": result, "session_id": session,
         "permission_denials": []}}
events.append(final)
(folder / f"{{session}}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in transcript), encoding="utf-8")
if values["--output-format"] == "stream-json":
    for event in events:
        print(json.dumps(event))
else:
    print(json.dumps(final))
'''


def _kit_files() -> list[str]:
    listed = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "-z"], check=True, capture_output=True).stdout
    files = {rel for rel in listed.decode("utf-8").split("\0") if rel and not rel.startswith(NOT_COPIED)}
    # Present before its first commit too, while it is being written.
    files.add(RUNNER.relative_to(REPO_ROOT).as_posix())
    return sorted(rel for rel in files if (REPO_ROOT / rel).is_file())


UV_SHIM = """#!/bin/sh
# Stands in for `uv run --script <engine> <args>`, the one form the shipped hook
# registrations use, so these tests need no uv on the machine (CI has none).
if [ "$1" = run ] && [ "$2" = --script ]; then shift 2; exec "{python}" "$@"; fi
echo "test uv shim: unsupported: $*" >&2
exit 2
"""


@pytest.fixture(scope="module")
def smoke_kit(tmp_path_factory):
    """A committed copy of the kit whose lane commands name the fake clients."""
    base = tmp_path_factory.mktemp("smoke")
    shims = base / "shims"
    shims.mkdir()
    (shims / "uv").write_text(UV_SHIM.format(python=sys.executable), encoding="utf-8")
    (shims / "uv").chmod(0o755)
    env = _git_env(base)
    bin_dir = base / "bin"
    bin_dir.mkdir()
    fakes = {}
    for name, template in (("codex", FAKE_CODEX), ("claude", FAKE_CLAUDE)):
        path = bin_dir / name
        path.write_text(template.format(python=sys.executable, version=FAKE_VERSION), encoding="utf-8")
        path.chmod(0o755)
        fakes[name] = path
    kit = base / "kit"
    for rel in _kit_files():
        (kit / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, kit / rel)
    config = kit / "config" / "dev-model.yaml"
    text = config.read_text(encoding="utf-8")
    for runtime, flag in (("codex", "exec"), ("claude", "-p")):
        line = f"  {runtime}_headless_command: [{runtime}, {flag}]"
        assert line in text, f"the shipped config no longer spells {line.strip()!r}"
        text = text.replace(line, f"  {runtime}_headless_command: [{json.dumps(str(fakes[runtime]))}, {flag}]")
    config.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=kit, env=env, check=True)
    revision = _commit_all(kit, env, "kit under test, lane commands naming the fakes")
    homes = {"codex": base / "codex-home", "claude": base / "claude-config"}
    for home in homes.values():
        home.mkdir()
    env["PATH"] = f"{shims}{os.pathsep}{env.get('PATH', '')}"
    return {"base": base, "kit": kit, "revision": revision, "fakes": fakes, "homes": homes, "env": env}


def _smoke_command(smoke_kit, name: str, *extra: str, codex_version: str = FAKE_VERSION,
                   claude_version: str = FAKE_VERSION, env_extra=None):
    base = smoke_kit["base"]
    work = base / f"work-{name}"
    work.mkdir()
    out = base / f"out-{name}"
    argv = [
        sys.executable, str(smoke_kit["kit"] / "scripts" / "runtime_smoke.py"),
        "--work-root", str(work), "--out", str(out), "--timeout", "180",
        "--codex-bin", str(smoke_kit["fakes"]["codex"]), "--codex-version", codex_version,
        "--codex-home", str(smoke_kit["homes"]["codex"]),
        "--claude-bin", str(smoke_kit["fakes"]["claude"]), "--claude-version", claude_version,
        "--claude-config-dir", str(smoke_kit["homes"]["claude"]),
        *extra,
    ]
    env = {key: value for key, value in smoke_kit["env"].items() if key not in rs.CLAUDE_CREDENTIAL_ENV}
    env.update(env_extra or {})
    return argv, env, out


def _smoke(smoke_kit, name: str, *extra: str, **options):
    argv, env, out = _smoke_command(smoke_kit, name, *extra, **options)
    result = subprocess.run(argv, cwd=smoke_kit["base"], env=env, capture_output=True, text=True, timeout=900)
    record = json.loads((out / "record.json").read_text(encoding="utf-8")) if (out / "record.json").is_file() else None
    return result, record, out


def _rows(record) -> dict[str, dict]:
    return {row["id"]: row for row in record["rows"]}


def test_every_row_passes_against_clients_that_behave(smoke_kit):
    # An empty --out is taken over whole; a missing one is created by the same rename.
    (smoke_kit["base"] / "out-all").mkdir()
    result, record, out = _smoke(smoke_kit, "all", "--allow-codex-project-trust", "--allow-codex-hook-trust-bypass")
    rows = _rows(record)
    assert {row_id: row["status"] for row_id, row in rows.items()} == {row_id: "passed" for row_id, _, _ in rs.ROWS}, (
        json.dumps({row_id: row["reason"] for row_id, row in rows.items()}, indent=1) + result.stderr
    )
    assert result.returncode == rs.EXIT_PASSED
    assert record["kit"]["revision"] == smoke_kit["revision"]
    assert record["observations"]["codex"]["hook_trust_route"] == {
        "project_trust": "per-invocation override",
        "hook_trust": "per-invocation bypass",
        "hooks_json_differs": False,
    }
    assert (rows["codex.review"]["evidence"]["reviewer_model"], rows["codex.review"]["evidence"]["reviewer_effort"]) == (
        "fake-reviewer", "low"
    )
    for row_id in ("codex.lane", "claude.lane"):
        assert rows[row_id]["evidence"]["receipt_status"] == "completed"
        assert rows[row_id]["session"]["executing_version"] == FAKE_VERSION
    markdown = (out / "record.md").read_text(encoding="utf-8")
    assert smoke_kit["revision"] in markdown
    published = markdown + (out / "record.json").read_text(encoding="utf-8")
    for private in (smoke_kit["kit"], smoke_kit["homes"]["codex"], smoke_kit["homes"]["claude"], smoke_kit["base"] / "work-all"):
        assert str(private) not in published and rs.realpath(private) not in published


@pytest.mark.parametrize(
    "flags, missing",
    [
        ((), "project trust not established"),
        (("--allow-codex-hook-trust-bypass",), "project trust not established"),
        (("--allow-codex-project-trust",), "hook trust not established"),
    ],
    ids=["neither", "bypass-only", "project-only"],
)
def test_the_codex_hook_rows_name_the_trust_layer_that_is_missing(smoke_kit, flags, missing):
    result, record, _ = _smoke(smoke_kit, f"trust-{len(flags)}-{'-'.join(flags)}", "--runtime", "codex", *flags)
    rows = _rows(record)
    for row_id in ("codex.session_start", "codex.post_tool_use"):
        assert rows[row_id]["status"] == "not-run"
        assert rows[row_id]["reason"].startswith(missing)
    for row_id in ("codex.instructions", "codex.skills", "codex.review", "codex.panel", "codex.lane"):
        assert rows[row_id]["status"] == "passed", rows[row_id]["reason"]
    assert rows["claude.lane"]["reason"] == "not selected for this run (--runtime)"
    assert result.returncode == rs.EXIT_INCOMPLETE


@pytest.mark.parametrize(
    "switches, runtime, broken",
    [
        (
            {
                "FAKE_CODEX_REVIEW_EXIT": "1",
                "FAKE_CODEX_HOOK_BEFORE_CALL": "1",
                "FAKE_CODEX_LENS_MODEL": "wrong-model",
                "FAKE_CLAUDE_NO_TOOL_RESULT": "1",
                "FAKE_CLAUDE_REVIEW_UNRECORDED": "1",
                "FAKE_CLAUDE_SILENT_HOOK": "SessionStart",
                "FAKE_CLAUDE_LANE_NO_TOKEN": "1",
            },
            None,
            {
                "codex.review": "exited 1",
                "codex.post_tool_use": "the hook's warning never reached the session",
                "codex.panel": "applied model 'wrong-model'",
                "claude.post_tool_use": "no tool result carried the nonce URL",
                "claude.review": "not listed, not invoked, or returned no non-error result",
                "claude.session_start": "no SessionStart hook event carried the tripwire line",
                "claude.lane": "the final text does not carry the task token",
            },
        ),
        (
            {
                "FAKE_CODEX_REVIEW_NO_MARKERS": "1",
                "FAKE_CODEX_LANE_NO_TOKEN": "1",
                "FAKE_CLAUDE_NO_POSTTOOL_HOOK": "1",
                "FAKE_CLAUDE_LENS_EFFORT": "low",
            },
            None,
            {
                "codex.review": "the rollout recorded no review-mode event",
                "codex.lane": "the final text does not carry the task token",
                "claude.post_tool_use": "no PostToolUse hook event after that shell call",
                "claude.panel": "applied efforts ['low']",
            },
        ),
        (
            {"FAKE_CLAUDE_HOOK_BEFORE_CALL": "1", "FAKE_CLAUDE_INIT_OMIT": "pr-watch"},
            "claude",
            {
                "claude.post_tool_use": "no PostToolUse hook event after that shell call",
                "claude.commands": "a declared command or a configured lens agent was not loaded",
            },
        ),
        (
            {"FAKE_CLAUDE_SILENT_HOOK": "PostToolUse", "FAKE_CLAUDE_INIT_OMIT": "adversarial"},
            "claude",
            {
                "claude.post_tool_use": "no PostToolUse hook event after that shell call carried the hook's warning",
                "claude.commands": "a declared command or a configured lens agent was not loaded",
            },
        ),
        ({"FAKE_CODEX_REVIEW_SILENT": "1"}, "codex", {"codex.review": "the review returned no output"}),
        (
            {"FAKE_CLAUDE_NO_INIT": "1"},
            "claude",
            {
                row_id: "the session emitted no init event"
                for row_id in ("claude.instructions", "claude.commands", "claude.session_start", "claude.post_tool_use")
            },
        ),
    ],
    ids=["exit-order-omission", "no-markers-no-hook", "hook-before-call", "silent-hook", "review-silent", "no-init"],
)
def test_a_client_that_misbehaves_fails_exactly_the_rows_it_breaks(smoke_kit, request, switches, runtime, broken):
    name = f"misbehave-{request.node.callspec.id}"
    extra = ["--allow-codex-project-trust", "--allow-codex-hook-trust-bypass"] if runtime != "claude" else []
    result, record, _ = _smoke(smoke_kit, name, *(["--runtime", runtime] if runtime else []), *extra, env_extra=switches)
    rows = _rows(record)
    for row_id, reason in broken.items():
        assert rows[row_id]["status"] == "failed", (row_id, rows[row_id]["reason"])
        assert reason in rows[row_id]["reason"], (row_id, rows[row_id]["reason"])
    selected = {row["id"] for row in record["rows"] if runtime in (None, row["runtime"])}
    assert {row_id for row_id in selected if rows[row_id]["status"] != "passed"} == set(broken)
    assert result.returncode == rs.EXIT_FAILED


def _in_process_context(smoke_kit, tmp_path, monkeypatch):
    """A run's context built in process, for the guards the CLI cannot reach."""
    for key, value in smoke_kit["env"].items():
        monkeypatch.setenv(key, value)
    run_dir = tmp_path / "run"
    (run_dir / "logs").mkdir(parents=True)
    base_env = rs.scrubbed_environment()
    fixture = rs.build_fixture(smoke_kit["kit"], smoke_kit["revision"], run_dir, base_env)
    ctx = rs.Context(
        kit_root=smoke_kit["kit"], revision=smoke_kit["revision"], run_dir=run_dir, log_dir=run_dir / "logs",
        fixture=fixture, config=rs.load_config(fixture.repo / "config" / "dev-model.yaml", overlay=False),
        timeout=180, nonce="0123456789ab", pr_number=1000, budget_line="⚠ unused", base_env=base_env,
        followup_markers={"codex": "unused.", "claude": "unused."},
    )
    return ctx, {row_id: rs.Row(row_id, runtime, check) for row_id, runtime, check in rs.ROWS}


def test_the_commands_row_fails_with_no_lens_agent_to_look_for(smoke_kit, tmp_path, monkeypatch):
    for name in ("run_claude_panel", "run_lane"):
        monkeypatch.setattr(rs, name, lambda *_args, **_kwargs: None)
    ctx, rows = _in_process_context(smoke_kit, tmp_path, monkeypatch)
    ctx.config["review"]["fallback_panel"]["lenses"] = []
    rs.run_claude(ctx, rows, smoke_kit["fakes"]["claude"], smoke_kit["homes"]["claude"], FAKE_VERSION)
    assert (rows["claude.commands"].status, rows["claude.commands"].reason) == (
        "failed", "no declared command or no configured lens agent to look for",
    )


@pytest.mark.parametrize("runtime", ["codex", "claude"])
def test_unset_optional_settings_are_reasons_not_crashes(smoke_kit, tmp_path, monkeypatch, runtime):
    """A setting the runner treats as optional, absent from the config, must not abort a
    run whose other runtime's clients have already run."""
    for name in ("run_codex_panel", "run_claude_panel", "run_lane"):
        monkeypatch.setattr(rs, name, lambda *_args, **_kwargs: None)
    ctx, rows = _in_process_context(smoke_kit, tmp_path, monkeypatch)
    ctx.config["models"]["runtime_mappings"][runtime].pop("cheap")
    if runtime == "codex":
        rs.run_codex(ctx, rows, smoke_kit["fakes"]["codex"], smoke_kit["homes"]["codex"], FAKE_VERSION,
                     bypass=False, project_trust=False)
        assert not any("model_reasoning_effort" in arg for arg in rows["codex.instructions"].invocations[0]["argv"])
        return
    ctx.config["review"]["fallback_commands"].pop("claude")
    rs.run_claude(ctx, rows, smoke_kit["fakes"]["claude"], smoke_kit["homes"]["claude"], FAKE_VERSION)
    assert "--model" not in rows["claude.instructions"].invocations[0]["argv"]
    assert (rows["claude.review"].status, rows["claude.review"].reason) == (
        "not-run", "review.fallback_commands.claude is not configured",
    )


def test_a_tampered_hook_registration_is_trusted_by_no_route(smoke_kit, tmp_path, monkeypatch):
    """The guard the CLI cannot reach: its fixture is the revision's own bytes."""
    ctx, rows = _in_process_context(smoke_kit, tmp_path, monkeypatch)
    (ctx.fixture.repo / rs.CODEX_HOOKS).write_text('{"hooks": {}}\n', encoding="utf-8")
    observed = rs.run_codex(
        ctx, rows, smoke_kit["fakes"]["codex"], smoke_kit["homes"]["codex"], FAKE_VERSION,
        bypass=True, project_trust=True,
    )
    assert observed["hook_trust_route"] == {"project_trust": "none", "hook_trust": "none", "hooks_json_differs": True}
    for row_id in ("codex.session_start", "codex.post_tool_use"):
        assert rows[row_id].status == "not-run"
        assert rows[row_id].reason.startswith("hook trust refused")


def test_a_record_is_published_whole_or_not_at_all(smoke_kit, tmp_path, monkeypatch, capsys):
    """Something wrote into --out while the run went on: the rename into place fails,
    and the complete record waits beside --out instead of merging into it."""
    for key, value in smoke_kit["env"].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(rs, "SCRIPT_PATH", (smoke_kit["kit"] / "scripts" / "runtime_smoke.py").resolve())
    work = tmp_path / "work"
    work.mkdir()
    out = tmp_path / "out"
    render = rs.render_markdown

    def intrude(record):
        out.mkdir()
        (out / "record.json").write_text(json.dumps({"run_id": "adk-smoke-another"}), encoding="utf-8")
        return render(record)

    monkeypatch.setattr(rs, "render_markdown", intrude)
    monkeypatch.setattr(rs, "_RUN_ID", None)
    assert rs.main(["--work-root", str(work), "--out", str(out)]) == rs.EXIT_ABORTED
    err = capsys.readouterr().err
    assert "--out could not take the record" in err and "no record was written to --out" in err
    assert [path.name for path in out.iterdir()] == ["record.json"]
    assert json.loads((out / "record.json").read_text(encoding="utf-8")) == {"run_id": "adk-smoke-another"}
    [staging] = tmp_path.glob(".out.*")
    assert sorted(path.name for path in staging.iterdir()) == ["record.json", "record.md"]
    # What `left_at` compares a record at --out with: this run's own id.
    assert json.loads((staging / "record.json").read_text(encoding="utf-8"))["run_id"] == rs._RUN_ID


def test_a_record_that_cannot_be_rendered_leaves_nothing_at_out(smoke_kit, tmp_path, monkeypatch, capsys):
    """Run in process, so the renderer can fail after every row is judged."""
    for key, value in smoke_kit["env"].items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(rs, "SCRIPT_PATH", (smoke_kit["kit"] / "scripts" / "runtime_smoke.py").resolve())

    def unrenderable(_record):
        raise KeyError("a shape the renderer does not know")

    monkeypatch.setattr(rs, "render_markdown", unrenderable)
    work = tmp_path / "work"
    work.mkdir()
    out = tmp_path / "out"
    assert rs.main(["--work-root", str(work), "--out", str(out)]) == rs.EXIT_ABORTED
    assert "failed: KeyError" in capsys.readouterr().err
    assert not out.exists() and not list(tmp_path.glob(".out.*"))


@pytest.mark.parametrize(
    "runtime, switch, named",
    [
        ("claude", "FAKE_CLAUDE_LOGGED_OUT", ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")),
        ("codex", "FAKE_CODEX_LOGGED_OUT", ("`codex login status`", "CODEX_HOME=<codex-home> codex login")),
    ],
)
def test_an_unauthenticated_home_names_the_credential_it_lacked(smoke_kit, runtime, switch, named):
    result, record, _ = _smoke(smoke_kit, f"logged-out-{runtime}", "--runtime", runtime, env_extra={switch: "1"})
    for row in record["rows"]:
        if row["runtime"] == runtime:
            assert row["status"] == "not-run"
            assert all(text in row["reason"] for text in named), row["reason"]
    assert result.returncode == rs.EXIT_INCOMPLETE


def test_the_record_lists_only_the_trust_entries_the_run_added(smoke_kit, tmp_path):
    home = tmp_path / "codex-home"
    home.mkdir()
    (home / "config.toml").write_text('[projects."/already/trusted"]\ntrust_level = "trusted"\n', encoding="utf-8")
    result, record, _ = _smoke(
        smoke_kit, "trust-written", "--runtime", "codex", "--codex-home", str(home),
        env_extra={"FAKE_CODEX_WRITES_TRUST": "1"},
    )
    assert record["observations"]["codex"]["projects_added"] == ["<run>/repo (trusted)"], result.stderr


def _sessions(home: Path) -> set[Path]:
    """Every rollout or transcript a client wrote under its home."""
    return set(home.rglob("*.jsonl"))


@pytest.mark.parametrize(
    "runtime, reported, pinned",
    [
        ("codex", f"codex-cli {FAKE_VERSION}", "codex-cli 0.0.1"),
        ("claude", f"{FAKE_VERSION} (Claude Code)", "0.0.1 (Claude Code)"),
    ],
)
def test_a_shell_cli_that_is_not_the_pin_runs_nothing(smoke_kit, runtime, reported, pinned):
    home = smoke_kit["homes"][runtime]
    before = _sessions(home)
    result, record, _ = _smoke(smoke_kit, f"pin-{runtime}", "--runtime", runtime, **{f"{runtime}_version": "0.0.1"})
    for row in record["rows"]:
        if row["runtime"] == runtime:
            assert row["status"] == "not-run"
            assert reported in row["reason"] and pinned in row["reason"], row["reason"]
    assert _sessions(home) == before
    assert result.returncode == rs.EXIT_INCOMPLETE


@pytest.mark.parametrize(
    "extra, refusal",
    [
        (("--timeout", "0"), "--timeout must be positive"),
        (("--work-root", "relative"), "--work-root must be an existing absolute directory"),
        (("--work-root", "<kit>/scripts"), "--work-root must be outside the kit checkout"),
        (("--out", "relative-out"), "--out must be an absolute path"),
        (("--out", "<occupied>/missing/out"), "--out must be in an existing directory"),
        (("--out", "<occupied>"), "--out must be a new or empty directory"),
        (("--runtime", "claude", "--allow-codex-project-trust"), "the Codex trust authorizations need a Codex run"),
        (("--runtime", "claude", "--allow-codex-hook-trust-bypass"), "the Codex trust authorizations need a Codex run"),
    ],
    ids=["timeout", "relative-work-root", "work-root-in-kit", "relative-out", "out-without-parent", "occupied-out",
         "project-trust", "bypass"],
)
def test_arguments_that_cannot_be_honoured_are_refused_before_anything_runs(smoke_kit, request, extra, refusal):
    name = request.node.callspec.id
    occupied = smoke_kit["base"] / f"occupied-{name}"
    occupied.mkdir()
    (occupied / "record.json").write_text("{}\n", encoding="utf-8")
    extra = [arg.replace("<kit>", str(smoke_kit["kit"])).replace("<occupied>", str(occupied)) for arg in extra]
    before = {runtime: _sessions(home) for runtime, home in smoke_kit["homes"].items()}
    result, record, out = _smoke(smoke_kit, f"refused-{name}", *extra)
    assert result.returncode == rs.EXIT_REFUSED, result.stderr
    assert refusal in result.stderr
    assert record is None and not out.exists()
    assert (occupied / "record.json").read_text(encoding="utf-8") == "{}\n"
    assert {runtime: _sessions(home) for runtime, home in smoke_kit["homes"].items()} == before


def _interrupts_at_default():
    # A job a shell starts in the background inherits SIGINT ignored, and the runner leaves
    # a signal it inherited ignored alone; start it as a terminal would.
    for signum in rs.INTERRUPT_SIGNALS:
        signal.signal(signum, signal.SIG_DFL)


@pytest.mark.parametrize(
    "step, signals",
    [
        ("probe", (signal.SIGHUP,)),
        ("probe", (signal.SIGTERM, signal.SIGTERM)),
        ("lens", (signal.SIGINT,)),
        ("lane", (signal.SIGTERM,)),
    ],
    ids=["probe-sighup", "probe-repeated-sigterm", "lens-sigint", "lane-sigterm"],
)
def test_an_interrupted_run_stops_every_client_and_writes_no_record(smoke_kit, tmp_path, step, signals):
    """The probe and the lane's launcher run on the main thread, the lenses on worker
    threads, and a lane's client behind the launcher's own relay. Every hanging fake
    ignores SIGTERM, so each case also needs the stop's SIGKILL escalation."""
    pid_dir = tmp_path / "pids"
    pid_dir.mkdir()
    argv, env, out = _smoke_command(
        smoke_kit, f"interrupt-{step}-{len(signals)}", "--runtime", "codex", "--allow-codex-project-trust",
        "--allow-codex-hook-trust-bypass", env_extra={"FAKE_CODEX_HANG": step, "FAKE_PID_DIR": str(pid_dir)},
    )
    config = rs.load_config(smoke_kit["kit"] / "config" / "dev-model.yaml", overlay=False)
    hanging = len(rs.lens_roster(config)) if step == "lens" else 1
    runner = subprocess.Popen(
        argv, cwd=smoke_kit["base"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        preexec_fn=_interrupts_at_default,
    )
    try:
        deadline = time.monotonic() + 300
        while len(list(pid_dir.glob("*.pid"))) < hanging:
            assert runner.poll() is None, runner.communicate()
            assert time.monotonic() < deadline, "no fake client reached its hang"
            time.sleep(0.2)
        time.sleep(0.5)
        for index, signum in enumerate(signals):
            if index:
                time.sleep(1)  # inside the grace of the stop the first signal began
            runner.send_signal(signum)
        _stdout, stderr = runner.communicate(timeout=120)
    finally:
        if runner.poll() is None:
            runner.kill()
            runner.wait()
        # Each hanging fake wrote its own pid and its child's.
        pids = [int(pid) for path in pid_dir.glob("*.pid") for pid in path.read_text(encoding="utf-8").split()]
        survivors = [pid for pid in pids if not _gone(pid)]
        for pid in survivors:
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
    assert runner.returncode == rs.EXIT_ABORTED, stderr
    assert "interrupted; every client process group it was running is stopped; no record was written to --out" in stderr
    assert len(pids) == 2 * hanging and not survivors, survivors
    assert not (out / "record.json").exists()


def test_the_runner_refuses_a_dirty_harness(smoke_kit):
    script = smoke_kit["kit"] / "scripts" / "runtime_smoke.py"
    original = script.read_bytes()
    script.write_bytes(original + b"\n# edited after the commit\n")
    try:
        result, record, out = _smoke(smoke_kit, "dirty")
    finally:
        script.write_bytes(original)
    assert result.returncode == rs.EXIT_REFUSED
    assert "differs from revision" in result.stderr
    assert record is None and not out.exists()
