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

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _repo_layout import engine_dir, find_repo_root

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
RUNNER = ENGINE_DIR / "runtime_smoke.py"

sys.path.insert(0, str(ENGINE_DIR))
import runtime_smoke as rs  # noqa: E402

FAKE_VERSION = "9.9.9"
# The kit's working records and evidence trees: most of the tracked bytes, and
# nothing the runner or the fixture's engines read.
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


def test_the_nonce_url_counts_only_from_a_tool_result():
    url = "https://github.com/adk-smoke/fixture-abc/pull/7"
    prompt = {"type": "user", "message": {"content": [{"type": "text", "text": f"printf {url}"}]}}
    echoed = {"type": "assistant", "message": {"content": [{"type": "text", "text": url}]}}
    result = {"type": "user", "message": {"content": [{"type": "tool_result", "content": f"{url}\n"}]}}
    assert not rs.tool_results_with([prompt, echoed], url)
    assert rs.tool_results_with([prompt, echoed, result], url)


def test_a_moved_injection_shape_leaves_its_heads_in_the_evidence(tmp_path):
    view = _view(messages=[_message(1, "user", "<environment_context>\n<cwd>/x</cwd>"), _message(2, "developer", "## Skills\n")])
    ok, evidence = rs.check_agents_block(view, tmp_path, b"# AGENTS.md\n")
    assert not ok and evidence["user_message_heads"] == ["<environment_context>"]
    ok, evidence = rs.check_skills(view, [rs.realpath(tmp_path / "adopt" / "SKILL.md")])
    assert not ok and evidence["developer_message_heads"] == ["## Skills"]


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
    notice = "Ignoring entries: " + "padding " * 40 + f"set projects[{run}/repo] in {run}/cfg.json"
    bounded = rs.bound_strings(rs.redact({"stderr_head": notice}, table), limit=120)
    assert str(tmp_path) not in json.dumps(bounded) and rs.realpath(tmp_path) not in json.dumps(bounded)
    assert bounded["stderr_head"].endswith("…") and len(bounded["stderr_head"]) == 120


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
add("turn_context", {{"model": values["-m"] or "fake-default", "effort": effort, "approval_policy": "never",
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

if "SMOKE-DONE-" in prompt:
    command = re.search(r"^(printf .+)$", prompt, re.M).group(1)
    output = subprocess.run(["bash", "-c", command], capture_output=True, text=True).stdout
    add("response_item", {{"type": "function_call", "name": "shell", "call_id": "c1", "arguments": json.dumps({{"command": command}})}})
    payload = {{"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {{"command": command}},
               "tool_response": {{"stdout": output, "stderr": "", "exit_code": 0}}, "cwd": str(cwd)}}
    # The live client wrote the hook's context between the call and its output.
    for text in run_hooks("PostToolUse", payload):
        if text.strip():
            message("developer", json.loads(text)["hookSpecificOutput"]["additionalContext"])
    add("response_item", {{"type": "function_call_output", "call_id": "c1", "output": output}})
    final = re.search(r"SMOKE-DONE-[0-9a-f]+", prompt).group(0)
elif review:
    add("event_msg", {{"type": "item_completed", "item": {{"type": "EnteredReviewMode"}}}})
    add("event_msg", {{"type": "item_completed", "item": {{"type": "ExitedReviewMode"}}}})
    final = "Fake review: one finding in docs/smoke-review-target.md."
elif "LANE-" in prompt:
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    final = f"{{re.search(r'LANE-[0-9a-f]+', prompt).group(0)}} {{branch}}"
else:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    final = f"Reviewed {{head}}."
message("assistant", final)
(day / f"rollout-2026-10-02T00-00-00-{{thread}}.jsonl").write_text(
    "".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
if last:
    Path(last).write_text(final, encoding="utf-8")
if "--json" in flags:
    print(json.dumps({{"type": "thread.started", "thread_id": thread}}))
'''

FAKE_CLAUDE = r'''#!{python}
"""A stand-in `claude` for the smoke runner's tests. Never a real client."""
import json, os, re, subprocess, sys, uuid
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
                run(hook["command"], {{"hook_event_name": "InstructionsLoaded", "file_path": str(cwd / name),
                                      "memory_type": "Project", "load_reason": reason}})

def hook_events(event, payload, tool="Bash"):
    outputs = []
    for group in project_settings.get("hooks", {{}}).get(event, []):
        if group.get("matcher") and not re.search(group["matcher"], tool):
            continue
        for hook in group["hooks"]:
            out = run(hook["command"], payload)
            outputs.append(out)
            events.append({{"type": "system", "subtype": "hook_response", "hook_event": event, "output": out, "stdout": out}})
    return outputs

hook_events("SessionStart", {{"hook_event_name": "SessionStart", "source": "startup"}})
folder = config / "projects" / re.sub(r"[/.]", "-", str(cwd))
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
        events.append({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "id": "t1", "name": "Bash", "input": {{"command": command}}}}]}}}})
        events.append({{"type": "user", "message": {{"content": [{{"type": "tool_result", "tool_use_id": "t1", "content": output}}]}}}})
        hook_events("PostToolUse", {{"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {{"command": command}},
                                    "tool_response": {{"stdout": output, "stderr": "", "interrupted": False}}}})
    result = re.search(r"SMOKE-DONE-[0-9a-f]+", prompt).group(0)
elif prompt.startswith("/"):
    # 2.1.287 records a command as its literal text, then a local_command entry.
    result = "Fake review: one finding."
    subagent("general-purpose", "Review the diff.", "claude-opus-fake", "medium", result)
    transcript.append({{"type": "system", "subtype": "local_command",
                       "content": f"<local-command-stdout>{{result}}</local-command-stdout>"}})
elif "-----BEGIN LENS PROMPT-----" in prompt:
    lens = re.search(r"Launch the `([^`]+)` agent", prompt).group(1)
    lens_prompt = prompt.split("-----BEGIN LENS PROMPT-----\n", 1)[1].rsplit("\n-----END LENS PROMPT-----", 1)[0]
    lens_model, lens_effort = frontmatter(lens)
    subagent(lens, lens_prompt, f"claude-{{lens_model}}-fake", lens_effort, f"Reviewed {{head}}.")
    result = "LENS-DONE"
elif "LANE-" in prompt:
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    result = f"{{re.search(r'LANE-[0-9a-f]+', prompt).group(0)}} {{branch}}"
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


def _smoke(smoke_kit, name: str, *extra: str, codex_version: str = FAKE_VERSION, env_extra=None):
    base = smoke_kit["base"]
    work = base / f"work-{name}"
    work.mkdir()
    out = base / f"out-{name}"
    argv = [
        sys.executable, str(smoke_kit["kit"] / "scripts" / "runtime_smoke.py"),
        "--work-root", str(work), "--out", str(out), "--timeout", "180",
        "--codex-bin", str(smoke_kit["fakes"]["codex"]), "--codex-version", codex_version,
        "--codex-home", str(smoke_kit["homes"]["codex"]),
        "--claude-bin", str(smoke_kit["fakes"]["claude"]), "--claude-version", FAKE_VERSION,
        "--claude-config-dir", str(smoke_kit["homes"]["claude"]),
        *extra,
    ]
    env = {key: value for key, value in smoke_kit["env"].items() if key not in rs.CLAUDE_CREDENTIAL_ENV}
    env.update(env_extra or {})
    result = subprocess.run(argv, cwd=base, env=env, capture_output=True, text=True, timeout=900)
    record = json.loads((out / "record.json").read_text(encoding="utf-8")) if (out / "record.json").is_file() else None
    return result, record, out


def _rows(record) -> dict[str, dict]:
    return {row["id"]: row for row in record["rows"]}


def test_every_row_passes_against_clients_that_behave(smoke_kit):
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


def test_an_unauthenticated_claude_home_names_the_credential_it_lacked(smoke_kit):
    result, record, _ = _smoke(smoke_kit, "logged-out", "--runtime", "claude", env_extra={"FAKE_CLAUDE_LOGGED_OUT": "1"})
    for row in record["rows"]:
        if row["runtime"] == "claude":
            assert row["status"] == "not-run"
            assert "CLAUDE_CODE_OAUTH_TOKEN" in row["reason"] and "ANTHROPIC_API_KEY" in row["reason"]
    assert result.returncode == rs.EXIT_INCOMPLETE


def _rollouts(home: Path) -> set[Path]:
    return set((home / "sessions").rglob("rollout-*.jsonl"))


def test_a_shell_cli_that_is_not_the_pin_runs_nothing(smoke_kit):
    before = _rollouts(smoke_kit["homes"]["codex"])
    result, record, _ = _smoke(smoke_kit, "pin", "--runtime", "codex", codex_version="0.0.1")
    for row in record["rows"]:
        if row["runtime"] == "codex":
            assert row["status"] == "not-run"
            assert f"codex-cli {FAKE_VERSION}" in row["reason"] and "codex-cli 0.0.1" in row["reason"]
    assert _rollouts(smoke_kit["homes"]["codex"]) == before
    assert result.returncode == rs.EXIT_INCOMPLETE


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
