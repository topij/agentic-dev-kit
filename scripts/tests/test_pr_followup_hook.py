"""Tests for scripts/hooks/pr_followup_hook.py — the PostToolUse PR follow-through nag.

Covers the contract the hook must hold regardless of config state: it only fires on
`gh pr create` / `gh pr ready`, never in a cron/CI context (`JOB_NAME` set), and it
always exits 0 — a malformed stdin payload must never fail the hosting session.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType

import pytest
import yaml

ENGINE_DIR = Path(__file__).resolve().parent.parent
HOOK_PATH = ENGINE_DIR / "hooks" / "pr_followup_hook.py"


def _find_repo_root(start: Path) -> Path:
    """Walk up for the `.git` marker rather than counting `parents[N]`.

    Depth arithmetic breaks in the `scripts/devkit/` layout `/adopt` defaults to
    (#134); the marker walk is the same approach `kitconfig.repo_root` takes and
    the sibling suite already uses.
    """
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no repository root above {start}")


REPO_ROOT = _find_repo_root(ENGINE_DIR)


def _load_hook() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pr_followup_hook_under_test", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(module: ModuleType, monkeypatch, capsys, stdin_text: str) -> tuple[int, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    exit_code = module.main()
    captured = capsys.readouterr()
    return exit_code, captured.out


def _payload(command: str) -> str:
    """No `tool_response` — the shape every pre-#302 test used, and the one that
    still fires unconditionally because nothing readable settles it."""
    return json.dumps({"tool_input": {"command": command}})


def _payload_with(command: str, stdout: str = "", stderr: str = "") -> str:
    """The real PostToolUse shape: what the tool reported alongside the command."""
    return json.dumps(
        {
            "tool_input": {"command": command},
            "tool_response": {"stdout": stdout, "stderr": stderr, "interrupted": False},
        }
    )


@pytest.fixture(autouse=True)
def _no_job_name(monkeypatch):
    """Every test runs outside cron/CI unless it explicitly sets JOB_NAME."""
    monkeypatch.delenv("JOB_NAME", raising=False)


def test_triggers_on_gh_pr_create(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr create --draft --title x",
            stdout="https://github.com/owner/repo/pull/42\n",
        ),
    )
    assert exit_code == 0
    body = json.loads(out)
    assert body["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    context = body["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context
    assert "Do not start review polling or the watch-and-fix loop yet" in context
    assert context.index("--assert-draft") < context.index("gh pr ready")
    assert context.index("gh pr ready") < context.index("--assert-ready")


@pytest.mark.parametrize(
    "draft_flag",
    ("-d", "-df", "-dFbody.md", "-dBmain", "--draft", "--draft=true"),
)
def test_supported_draft_flags_take_draft_lifecycle(
    monkeypatch, capsys, draft_flag
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            f"gh pr create {draft_flag} --fill",
            stdout="https://github.com/owner/repo/pull/42\n",
        ),
    )
    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context


def test_ready_create_asserts_ready_before_watch(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr create --fill",
            stdout="https://github.com/owner/repo/pull/42\n",
        ),
    )
    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" not in context
    assert context.index("--assert-ready") < context.index("watch-and-fix loop")


def test_triggers_on_gh_pr_ready(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr ready 42",
            stderr='Pull request owner/repo#42 is marked as "ready for review"\n',
        ),
    )
    assert exit_code == 0
    body = json.loads(out)
    assert body["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    context = body["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" not in context
    assert context.index("--assert-ready") < context.index("watch-and-fix loop")


def test_compound_draft_create_and_ready_takes_ready_route(monkeypatch, capsys):
    hook = _load_hook()
    command = "gh pr create --draft --fill && gh pr ready 42"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            command,
            stdout="https://github.com/owner/repo/pull/42\n",
            stderr='Pull request owner/repo#42 is marked as "ready for review"\n',
        ),
    )
    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" not in context
    assert context.index("--assert-ready") < context.index("watch-and-fix loop")


def test_ready_ack_for_another_pr_never_settles_the_created_pr(monkeypatch, capsys):
    hook = _load_hook()
    command = "gh pr ready 7; gh pr create --draft --fill"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            command,
            stdout="https://github.com/owner/repo/pull/42\n",
            stderr='Pull request owner/repo#7 is marked as "ready for review"\n',
        ),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert hook._pr_lifecycle(
        command,
        "https://github.com/owner/repo/pull/42\n"
        'Pull request owner/repo#7 is marked as "ready for review"\n',
    ) == "unknown"
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context


def test_ready_ack_only_settles_a_parsed_ready_invocation(monkeypatch, capsys):
    """Output text cannot turn a draft create into an executed ready transition."""
    hook = _load_hook()
    command = "gh pr create --draft --fill && echo 'is marked as ready for review'"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            command,
            stdout=(
                "https://github.com/owner/repo/pull/42\n"
                'is marked as "ready for review"\n'
            ),
        ),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "--assert-ready` before review polling" not in context


def test_compound_draft_create_with_echoed_ready_requires_live_state():
    hook = _load_hook()
    command = "gh pr create --draft --fill && echo gh pr ready"
    response = "https://github.com/owner/repo/pull/42\n"
    assert hook._pr_lifecycle(command, response) == "unknown"


@pytest.mark.parametrize(
    "command,stderr",
    (
        ("gh pr create --draft --fill || gh pr ready 42", ""),
        (
            "gh pr create --draft --fill && run-required-validation && gh pr ready 42",
            "run-required-validation: failed\n",
        ),
    ),
)
def test_distinct_unsettled_lifecycle_invocations_require_live_state(
    monkeypatch, capsys, command, stderr
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            command,
            stdout="https://github.com/owner/repo/pull/42\n",
            stderr=stderr,
        ),
    )
    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context


@pytest.mark.parametrize(
    "command",
    (
        "gh -R owner/repo pr create --draft --fill",
        "gh --repo=owner/repo pr create --draft --fill",
        "/usr/local/bin/gh -Rowner/repo pr create --draft --fill",
    ),
)
def test_global_repo_flag_and_gh_path_still_trigger_draft_lifecycle(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )
    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context


@pytest.mark.parametrize(
    "inherited",
    ("-R owner/repo", "-Rowner/repo", "--repo owner/repo", "--repo=owner/repo"),
)
@pytest.mark.parametrize(
    "action,stdout,stderr,assertion",
    (
        (
            "create --draft --fill",
            "https://github.com/owner/repo/pull/42\n",
            "",
            "--assert-draft",
        ),
        (
            "new --draft --fill",
            "https://github.com/owner/repo/pull/42\n",
            "",
            "--assert-draft",
        ),
        (
            "ready 42",
            "",
            'Pull request owner/repo#42 is marked as "ready for review"\n',
            "--assert-ready",
        ),
    ),
)
def test_inherited_repo_flags_after_pr_reach_each_lifecycle_action(
    monkeypatch, capsys, inherited, action, stdout, stderr, assertion
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(f"gh pr {inherited} {action}", stdout=stdout, stderr=stderr),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert assertion in context


@pytest.mark.parametrize(
    "command",
    (
        "{ gh pr create --draft --fill; }",
        "if gh pr create --draft --fill; then echo opened; fi",
        "exec gh pr create --draft --fill",
        ">pr.log gh pr create --draft --fill",
        "! gh pr create --draft --fill",
        "GH_HOST=github.example gh pr create --draft --fill",
        "command -- gh pr create --draft --fill",
        "env GH_HOST=github.example gh pr create --draft --fill",
        "env -u GH_TOKEN -- gh pr create --draft --fill",
    ),
)
def test_shell_prefixes_and_wrappers_reach_the_shared_lifecycle_hook(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context


@pytest.mark.parametrize(
    "command",
    (
        "time gh pr create --draft --fill",
        "sh -c 'gh pr create --draft --fill'",
        "bash -lc 'gh pr create --draft --fill'",
        "created=`gh pr create --draft --fill`",
        "created=$(gh pr create --draft --fill)",
        'created="it\'s $(gh pr create --draft --fill)"',
    ),
)
def test_executing_wrappers_and_substitutions_reach_the_lifecycle_hook(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert "--assert-draft" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


@pytest.mark.parametrize(
    "command",
    (
        "eval 'gh pr create --draft --fill'",
        "bash <<'EOF'\ngh pr create --draft --fill\nEOF",
        "bash -s positional <<'EOF'\ngh pr create --draft --fill\nEOF",
        "env GH_HOST=github.example sh <<\\EOF\ngh pr create --draft --fill\nEOF",
    ),
)
def test_literal_executed_source_with_success_evidence_requires_live_state(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is True
    assert hook._pr_lifecycle(command, response) == "unknown"
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context


@pytest.mark.parametrize(
    "command",
    (
        (
            "cat <<CAT; bash <<SHELL\n"
            "gh pr create --draft --fill\n"
            "https://github.com/owner/repo/pull/42\n"
            "CAT\n:\nSHELL"
        ),
        (
            "bash <<FIRST <<SECOND\n"
            "gh pr create --draft --fill\n"
            "FIRST\n:\nSECOND"
        ),
    ),
)
def test_only_the_effective_shell_stdin_heredoc_is_treated_as_program(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    response = (
        "gh pr create --draft --fill\n"
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is False
    assert out == ""


@pytest.mark.parametrize(
    "command",
    (
        "gh pr create \\\n  --draft \\\n  --fill",
        "gh pr \\\n  create --draft --fill",
    ),
)
def test_line_continuations_preserve_draft_lifecycle(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert hook._pr_lifecycle(
        command, "https://github.com/owner/repo/pull/42\n"
    ) == "draft"
    assert "--assert-draft" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


@pytest.mark.parametrize(
    "command",
    (
        "DRAFT=--draft; gh pr create $DRAFT --fill",
        "flags=--draft; gh pr create ${flags} --fill",
        'open_pr(){ gh pr create "$@"; }; open_pr --draft',
        'set -- --draft; gh pr create "$@"',
        "gh pr create $(printf %s --draft) --fill",
        "GH=gh; $GH pr create --draft --fill",
    ),
)
def test_dynamic_create_arguments_require_live_state(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook._pr_lifecycle(command, response) == "unknown"
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context


def test_dynamic_ready_executable_with_acknowledgement_requires_live_state(
    monkeypatch, capsys
):
    hook = _load_hook()
    command = "GH=gh; $GH pr ready 42"
    response = 'Pull request owner/repo#42 is marked as "ready for review"\n'
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stderr=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is True
    assert hook._pr_lifecycle(command, response) == "unknown"
    assert "ambiguous lifecycle evidence" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


def test_assignment_fed_create_with_success_evidence_cannot_fail_open(
    monkeypatch, capsys
):
    hook = _load_hook()
    command = 'open_pr="gh pr create --draft"; $open_pr'
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is True
    assert hook._pr_lifecycle(command, response) == "unknown"
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "actually created or readied" in context


@pytest.mark.parametrize(
    "command",
    (
        "command -p gh pr create --draft --fill",
        "env -S gh pr create --draft --fill",
        "env --split-string=gh pr create --draft --fill",
        "nohup gh pr create --draft --fill",
    ),
)
def test_supported_execution_wrappers_preserve_draft_lifecycle(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert "--assert-draft" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


@pytest.mark.parametrize(
    "command",
    (
        "timeout 30 gh pr create --fill",
        "/usr/bin/time -o timing gh pr create --fill",
    ),
)
def test_unmodelled_wrapper_with_success_evidence_requires_live_state(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook._pr_lifecycle(command, response) == "unknown"
    assert "ambiguous lifecycle evidence" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


@pytest.mark.parametrize(
    "command",
    (
        "echo '$(gh pr create --draft --fill)'",
        "echo '`gh pr create --draft --fill`'",
    ),
)
def test_single_quoted_substitution_text_stays_inert(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert out == ""


@pytest.mark.parametrize(
    "command",
    (
        "open_pr(){ gh pr create --draft --fill; }",
        "function open_pr { gh pr create --draft --fill; }",
        "open_pr() { gh pr create --draft --fill; }; echo defined",
    ),
)
def test_nonexecuting_function_definition_stays_silent(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command),
    )

    assert exit_code == 0
    assert out == ""


@pytest.mark.parametrize(
    "command",
    (
        "helper(){ :; }; gh pr create --draft --fill",
        "helper(){ gh pr create --draft --fill; }; helper",
        'helper(){ printf "%s\\n" "}"; gh pr create --draft --fill; }; helper',
    ),
)
def test_executed_commands_are_not_hidden_by_function_definitions(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert "--assert-draft" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


def test_gh_pr_new_alias_reaches_the_create_lifecycle(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr new --draft --fill",
            stdout="https://github.com/owner/repo/pull/42\n",
        ),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context


@pytest.mark.parametrize(
    "command",
    (
        "gh pr create --fill --body 'example: --draft'",
        "gh pr create --fill --body 'run gh pr ready later'",
        "gh pr create --body -d --fill",
        "gh pr create --draft=false --fill",
        "gh pr create -d=false --fill",
        "gh pr create -Fd --fill",
        "gh pr create -t-d --fill",
    ),
)
def test_quoted_or_false_draft_text_does_not_change_ready_lifecycle(command):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"
    assert hook._pr_lifecycle(command, response) == "ready"


@pytest.mark.parametrize(
    "command,expected",
    (
        ("gh pr create --draft --draft=false --fill", "ready"),
        ("gh pr create --draft=false --draft --fill", "draft"),
        ("gh pr create -d --draft=false --fill", "ready"),
        ("gh pr create --draft=false -d --fill", "draft"),
    ),
)
def test_repeated_draft_flags_follow_the_cli_last_value(command, expected):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"

    assert hook._pr_lifecycle(command, response) == expected


@pytest.mark.parametrize(
    "arguments,can_complete",
    (
        (["--dry-run", "--dry-run=false", "--fill"], True),
        (["--dry-run=false", "--dry-run", "--fill"], False),
        (["--web", "--web=false", "--fill"], True),
        (["--web=false", "--web", "--fill"], False),
    ),
)
def test_repeated_noncreating_flags_follow_the_cli_last_value(
    arguments, can_complete
):
    hook = _load_hook()

    assert hook._create_can_complete(arguments) is can_complete


def test_mixed_create_branches_inspect_live_state_before_any_correction(
    monkeypatch, capsys
):
    hook = _load_hook()
    command = "gh pr create --fill || gh pr create --draft --fill"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert hook._pr_lifecycle(command) == "unknown"
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context
    assert "only when that field is true" in context
    assert "Start the watch-and-fix loop only after the ready assertion passes" in context


@pytest.mark.parametrize(
    "command",
    (
        "false && gh pr create --draft --fill; "
        "gh pr view 42 --json url --jq .url",
        "if false; then gh pr create --draft --fill; fi; "
        "gh pr view 42 --json url --jq .url",
    ),
)
def test_unexecuted_create_cannot_borrow_a_later_view_url(
    monkeypatch, capsys, command
):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is True
    assert hook._pr_lifecycle(command, response) == "unknown"
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "ambiguous lifecycle evidence" in context
    assert "a URL printed by another command is not proof" in context
    assert "A draft pull request was just opened" not in context


def test_existing_pr_error_url_is_not_successful_creation(monkeypatch, capsys):
    hook = _load_hook()
    response = (
        'a pull request for branch "topic" into branch "main" already exists:\n'
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with("gh pr create --draft --fill", stderr=response),
    )

    assert exit_code == 0
    assert out == ""


def test_failed_create_cannot_borrow_a_later_view_url(monkeypatch, capsys):
    hook = _load_hook()
    command = "gh pr create --draft --fill || gh pr view --json url --jq .url"
    response = (
        'a pull request for branch "topic" into branch "main" already exists:\n'
        "https://github.com/owner/repo/pull/42\n"
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stderr=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is False
    assert out == ""


@pytest.mark.parametrize(
    "response",
    (
        (
            "https://github.com/owner/repo/pull/42\n"
            'a pull request for branch "other" into branch "main" already exists:\n'
            "https://github.com/owner/repo/pull/9\n"
        ),
        (
            'a pull request for branch "other" into branch "main" already exists:\n'
            "https://github.com/owner/repo/pull/9\n"
            "https://github.com/owner/repo/pull/42\n"
        ),
    ),
)
def test_existing_pr_diagnostic_does_not_hide_a_separate_success(
    monkeypatch, capsys, response
):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr create --fill; gh pr create --fill",
            stdout=response,
        ),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "MANDATORY" in context
    assert "ambiguous lifecycle evidence" in context


def test_heredoc_body_is_not_treated_as_executed_shell(monkeypatch, capsys):
    hook = _load_hook()
    command = (
        "cat <<'EOF'\n"
        "gh pr create --draft --fill\n"
        "https://github.com/owner/repo/pull/42\n"
        "EOF"
    )
    response = (
        "gh pr create --draft --fill\n"
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is False
    assert out == ""


def test_heredoc_body_cannot_forge_a_ready_transition(monkeypatch, capsys):
    hook = _load_hook()
    command = (
        "gh pr create --draft --body-file - <<EOF\n"
        "Do not run && gh pr ready yet\n"
        "EOF"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-draft" in context
    assert "ambiguous lifecycle evidence" not in context


@pytest.mark.parametrize("opener", (r"<<\EOF", "<<'E'O\"F\""))
def test_quote_removed_heredoc_delimiter_does_not_hide_later_create(
    monkeypatch, capsys, opener
):
    hook = _load_hook()
    command = f"cat {opener}\nbody\nEOF\ngh pr create --draft --fill"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout="https://github.com/owner/repo/pull/42\n"),
    )

    assert exit_code == 0
    assert "--assert-draft" in json.loads(out)["hookSpecificOutput"][
        "additionalContext"
    ]


def test_shell_comment_cannot_borrow_an_unrelated_pr_url(monkeypatch, capsys):
    hook = _load_hook()
    command = (
        'printf "https://github.com/owner/repo/pull/42\\n" '
        "# ; gh pr create --draft --fill"
    )
    response = "https://github.com/owner/repo/pull/42\n"
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is False
    assert out == ""


def test_dry_run_body_url_is_not_creation_evidence(monkeypatch, capsys):
    hook = _load_hook()
    dry_run_output = (
        "Would have created a Pull Request with:\n"
        "title: Example\n"
        "draft: false\n"
        "base: main\n"
        "head: topic\n"
        "maintainerCanModify: true\n"
        "body:\n"
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr create --dry-run --body https://github.com/owner/repo/pull/42",
            stdout=dry_run_output,
        ),
    )

    assert exit_code == 0
    assert out == ""


@pytest.mark.parametrize("web_flag", ("--web", "-w", "-dw"))
def test_browser_handoff_is_not_completed_creation(
    monkeypatch, capsys, web_flag
):
    hook = _load_hook()
    command = f"gh pr create {web_flag}"
    exit_code, out = _run(hook, monkeypatch, capsys, _payload(command))

    assert exit_code == 0
    assert hook.should_fire(command, None) is False
    assert out == ""


def test_dry_run_and_real_create_require_live_state(monkeypatch, capsys):
    hook = _load_hook()
    command = "gh pr create --dry-run --fill; gh pr create --fill"
    response = (
        "Would have created a Pull Request with:\n"
        "body:\n"
        "https://github.com/owner/repo/pull/7\n"
        "https://github.com/owner/repo/pull/42\n"
    )
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stdout=response),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert hook._pr_lifecycle(command, response) == "unknown"
    assert "ambiguous lifecycle evidence" in context
    assert "gh pr view <PR#> --json isDraft" in context


@pytest.mark.parametrize(
    "command",
    (
        "gh pr ready --undo 42 >/dev/null 2>&1",
        "gh pr ready 42 --undo >/dev/null 2>&1",
    ),
)
@pytest.mark.parametrize("tool_response", ({"stdout": "", "stderr": ""}, ""))
def test_ready_undo_never_injects_a_ready_assertion(
    monkeypatch, capsys, command, tool_response
):
    hook = _load_hook()
    payload = json.dumps(
        {"tool_input": {"command": command}, "tool_response": tool_response}
    )
    exit_code, out = _run(hook, monkeypatch, capsys, payload)

    assert exit_code == 0
    assert out == ""


def test_ready_undo_false_remains_a_ready_transition(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr ready 42 --undo=false",
            stderr='Pull request owner/repo#42 is marked as "ready for review"\n',
        ),
    )

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "--assert-ready" in context


@pytest.mark.parametrize(
    "command,should_fire",
    (
        ("gh pr ready 42 --undo --undo=false", True),
        ("gh pr ready 42 --undo=false --undo", False),
    ),
)
def test_repeated_ready_undo_flags_follow_the_cli_last_value(
    monkeypatch, capsys, command, should_fire
):
    hook = _load_hook()
    response = 'Pull request owner/repo#42 is marked as "ready for review"\n'
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(command, stderr=response),
    )

    assert exit_code == 0
    assert hook.should_fire(command, response) is should_fire
    assert bool(out) is should_fire


def test_does_not_trigger_on_gh_pr_view(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, _payload("gh pr view 42"))
    assert exit_code == 0
    assert out == ""


def test_does_not_trigger_on_unrelated_bash_command(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, _payload("ls -la"))
    assert exit_code == 0
    assert out == ""


def test_noops_when_job_name_is_set(monkeypatch, capsys):
    hook = _load_hook()
    monkeypatch.setenv("JOB_NAME", "nightly-triage")
    exit_code, out = _run(hook, monkeypatch, capsys, _payload("gh pr create --draft"))
    assert exit_code == 0
    assert out == ""


@pytest.mark.parametrize(
    "stdin_text",
    [
        "not json at all",
        "",
        "[]",
        "null",
        '"just a string"',
        '{"tool_input": "not-a-dict"}',
        '{"tool_input": {"command": 123}}',
    ],
)
def test_exits_zero_on_malformed_or_unexpected_stdin(monkeypatch, capsys, stdin_text):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, stdin_text)
    assert exit_code == 0
    assert out == ""


def test_reminder_names_configured_bots_not_a_hardcoded_bot(monkeypatch):
    """The reminder must be sourced from config (review.bots / fallback_panel),
    never a hardcoded bot literal — this is the whole point of generalizing the
    reference implementation (Principle #10, "No hardcoding").

    The bot name is INJECTED rather than read from the ambient repo, for two
    reasons:

    1. Reading it made this test depend on the surrounding repo configuring a
       review bot — an adopter setting the truthful ``review.bots: []`` turned
       it red on a property that has nothing to do with their config.
    2. More importantly, asserting ``"coderabbit" in reminder`` while the repo's
       own config says ``coderabbit`` **cannot fail for the reason the test
       names**: a hard-coded literal in ``build_reminder`` would satisfy it just
       as well as a config read. It claimed to pin "not hardcoded" and pinned
       nothing. A bot name that appears in no config and no source file
       distinguishes the two.
    """
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        # Shape matches `_load_review_config`'s declared contract
        # (tuple[list[str], str, str, list[str], str, str]) rather than being
        # merely duck-compatible: `panel_source` in particular is guarded twice and
        # defaulted on the except path, so `None` is not a value the real
        # function can return, and a mock that returns one could mask a
        # type-shape bug instead of exposing it.
        lambda *_a, **_k: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            [],
            "fallback:test-panel",
            "",
        ),
    )

    reminder = hook.build_reminder()

    assert "zzz-sentinel-bot" in reminder
    assert "coderabbit" not in reminder.lower()
    assert "bugbot" not in reminder.lower()


def test_reminder_names_configured_bots_on_the_panel_branch_too(monkeypatch):
    """The bot name must come from config on BOTH fallback branches.

    The sibling test above supplies no lenses, which routes
    `_fallback_instruction` to the DEGRADED wording — so on its own it leaves
    the PANEL wording uncovered, and a bot literal hardcoded into that branch
    survives the whole suite. Found by an adversarial review of the commit that
    added the sentinel, which is a fair reminder that "the mock is minimal" and
    "the mock exercises the path you care about" are different properties.
    """
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        lambda *_a, **_k: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            ["zzz-lens-one", "zzz-lens-two"],
            "fallback:test-panel",
            "",
        ),
    )

    reminder = hook.build_reminder()

    assert "PANEL" in reminder  # the panel branch really is the one rendered
    assert "zzz-sentinel-bot" in reminder
    assert "coderabbit" not in reminder.lower()
    assert "bugbot" not in reminder.lower()


def test_reminder_points_at_the_panel_not_the_degraded_one_lens_mode(monkeypatch):
    """This hook fires on every `gh pr create`/`ready`, so it is the most-read
    statement of the fallback policy in the kit.

    Pointing it at `fallback_commands` — a single command in the author's own
    context — taught the wrong habit every time it fired, against
    `safety-critical-changes.md` rule 2. With a panel configured it must name
    the panel and its lenses.

    The panel is INJECTED rather than read from the ambient repo: this asserts
    an engine property ("a configured panel is advertised over the degraded
    command"), and reading it from config made the test require the surrounding
    repo to configure a panel — it went red when `review.fallback_panel` was
    removed, which is a legitimate adopter state the hook explicitly handles and
    which has its own test below.
    """
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        lambda *_a, **_k: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            ["zzz-lens-one", "zzz-lens-two"],
            "fallback:test-panel",
            "",
        ),
    )

    reminder = hook.build_reminder()

    assert "PANEL" in reminder
    assert "zzz-lens-one" in reminder and "zzz-lens-two" in reminder
    assert "fallback-review-panel.md" in reminder
    assert "--lenses" in reminder
    # …and it must NOT advertise the degraded command as the thing to run.
    assert "/code-review" not in reminder


def test_the_reminder_reads_the_receipt_source_from_config(monkeypatch):
    """`review.fallback_panel.receipt_source` exists so an adopter can rename it.

    Driven through `load_config`, not through a positional argument: passing the
    value in only proves the formatter interpolates it. A mutation that made the
    loader ignore config entirely and return the default survived the whole
    suite — which is adding a config key and then not reading it (Principle #10),
    the exact failure the docstring claims to guard.
    """
    hook = _load_hook()
    hook._load_review_config()  # prime the kitconfig import
    import kitconfig  # noqa: PLC0415

    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *a, **k: {
            "review": {
                "bots": ["somebot"],
                "fallback_panel": {
                    "receipt_source": "fallback:my-panel",
                    "lenses": [{"name": "adversarial"}, {"name": "correctness"}],
                },
            }
        },
    )

    reminder = hook.build_reminder()

    assert '"fallback:my-panel"' in reminder
    assert "fallback:panel" not in reminder


def test_a_one_lens_panel_config_degrades_instead_of_advertising_a_refusal(
    monkeypatch,
):
    """Two distinct lenses is the panel's floor, and `record_review` enforces it.

    An adopter who configures one lens would otherwise be told to run "the
    PANEL" and record it with a command the engine refuses every single time.
    """
    hook = _load_hook()
    hook._load_review_config()
    import kitconfig  # noqa: PLC0415

    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *a, **k: {
            "review": {
                "bots": ["somebot"],
                "fallback_commands": {"claude": "/solo-review"},
                "fallback_panel": {"lenses": [{"name": "adversarial"}]},
            }
        },
    )

    reminder = hook.build_reminder()

    assert "PANEL" not in reminder
    assert "/solo-review" in reminder
    assert "review waiver" in reminder


def test_blank_lens_names_are_discarded_and_never_advertised(monkeypatch):
    """A whitespace-only `name` would have the hook advertise a panel with an
    unnameable lens — worse than advertising no panel at all."""
    hook = _load_hook()
    hook._load_review_config()
    import kitconfig  # noqa: PLC0415

    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *a, **k: {
            "review": {
                "bots": ["somebot"],
                "fallback_panel": {
                    "lenses": [{"name": "  "}, {"name": "adversarial"}, {"name": ""}]
                },
            }
        },
    )

    _bots, _fb, _eng, lenses, _src, _compute = hook._load_review_config()

    assert lenses == ["adversarial"]
    # "never advertised" was the half the name promised and the body skipped:
    # one usable lens is below the panel floor, so the reminder must not name
    # a panel at all.
    assert "PANEL" not in hook.build_reminder()


def test_reminder_falls_back_to_the_single_command_with_no_panel_configured():
    """An adopter who has not configured a panel — or a runtime that cannot
    isolate a reviewer — must still get actionable wording, not a dangling
    reference to lenses that do not exist."""
    hook = _load_hook()

    degraded = hook._fallback_instruction("/my-review", [])
    panel = hook._fallback_instruction("/my-review", ["adversarial", "correctness"])

    assert "`/my-review`" in degraded
    assert "PANEL" not in degraded
    assert "review waiver" in degraded  # the invariant survives either way
    assert "/my-review" not in panel


def test_load_review_config_degrades_gracefully_when_config_unreadable(monkeypatch):
    """A missing/unreadable config must never raise — the hook falls back to
    generic wording rather than failing the session."""
    hook = _load_hook()
    hook._load_review_config()  # prime the import so `kitconfig` lands in sys.modules
    import kitconfig  # noqa: PLC0415

    def _boom(*_args, **_kwargs):
        raise FileNotFoundError("no config here")

    monkeypatch.setattr(kitconfig, "load_config", _boom)
    bots, fallback, engines, lenses, panel_source, lens_compute = hook._load_review_config()
    assert bots == []
    assert fallback == "/code-review"
    assert engines == "scripts"
    # No panel known → the reminder degrades to the single command rather than
    # naming lenses that were never read.
    assert lenses == []
    assert panel_source == "fallback:panel"
    assert "PANEL" not in hook._fallback_instruction(
        fallback, lenses, panel_source, engines
    )


def test_an_unreadable_config_never_advertises_a_panel(monkeypatch):
    """This path means nothing confirmed a panel exists.

    A default lens roster here would have the hook advertise a panel — and a
    `--record-review` command the engine then refuses — on the strength of a
    config it had just failed to read.
    """
    hook = _load_hook()
    hook._load_review_config()
    import kitconfig  # noqa: PLC0415

    def _boom(*_a, **_k):
        raise FileNotFoundError("no config")

    monkeypatch.setattr(kitconfig, "load_config", _boom)

    reminder = hook.build_reminder()

    assert "PANEL" not in reminder
    assert "/code-review" in reminder  # the compatible single-command wording
    assert "review waiver" in reminder


def test_lens_compute_renders_both_controls_from_config(monkeypatch):
    """`model` and `effort` are independent knobs and both must reach the agent.

    The hook is the most-read statement of the fallback policy in the kit, so a
    lens-compute setting that never renders is a setting that silently does
    nothing — the `#145` failure mode (a config key read by no code) reintroduced
    one level down.
    """
    hook = _load_hook()

    class _Cfg:
        @staticmethod
        def get(config, path, default=None):
            if path == "review.fallback_panel.lens_compute.claude":
                return {"model": "zzz-model", "effort": "zzz-effort"}
            return default

    phrase = hook._lens_compute_phrase({}, _Cfg)

    assert "zzz-model" in phrase
    assert "zzz-effort" in phrase
    assert "review.fallback_panel.lens_compute" in phrase, (
        "name the key, or an operator cannot find what produced the instruction"
    )


def test_lens_compute_renders_a_lone_control(monkeypatch):
    """A runtime exposing only one control sets only that key.

    `codex` in the shipped config carries `effort` and no `model`, so a renderer
    that required both would emit nothing for it while the config plainly asks
    for something.
    """
    hook = _load_hook()

    class _Cfg:
        @staticmethod
        def get(config, path, default=None):
            if path == "review.fallback_panel.lens_compute.claude":
                return {"effort": "zzz-effort"}
            return default

    phrase = hook._lens_compute_phrase({}, _Cfg)

    assert "zzz-effort" in phrase
    assert "model" not in phrase, "must not invent a model the config did not name"


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        "sonnet",                      # scalar where a map belongs
        {"model": None},               # present-but-null
        {"model": "   "},              # blank after strip
        {"nonsense": "x"},             # unknown keys only
        # kitconfig's YAML subset has no block scalars, so `model: |` reaches us
        # as the literal "|" instead of raising. Non-blank, so a strip()-only
        # guard rendered `model |` into the instruction. Found by an adversarial
        # review that drove the real hook end-to-end against a mutated config.
        {"model": "|"},
        {"model": ">", "effort": "-"},
    ],
)
def test_lens_compute_is_silent_rather_than_wrong(value):
    """Unset or unusable must render NOTHING, never a malformed directive.

    Empty means "inherit the cockpit's compute" — the behaviour before this key
    existed and the default for any adopter who never sets it. Rendering
    `model: None` into the reminder would have the agent try to honour a model
    that does not exist, which is worse than saying nothing at all.
    """
    hook = _load_hook()

    class _Cfg:
        @staticmethod
        def get(config, path, default=None):
            if path == "review.fallback_panel.lens_compute.claude":
                return value
            return default

    assert hook._lens_compute_phrase({}, _Cfg) == ""


def test_lens_compute_never_reaches_the_degraded_one_lens_branch(monkeypatch):
    """The degraded fallback runs in the cockpit's OWN context.

    There is no separate lens process to give a model or effort level to, so
    appending the directive there would tell the operator to set compute for
    something that is not a delegated reviewer at all.
    """
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        lambda *_a, **_k: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            [],  # fewer than two lenses -> degraded branch
            "fallback:test-panel",
            " Run each lens at model zzz-model, per review.fallback_panel.lens_compute.",
        ),
    )

    reminder = hook.build_reminder()

    assert "PANEL" not in reminder, "guard: this must be the degraded branch"
    assert "zzz-model" not in reminder


def test_shipped_config_pins_the_lens_compute_the_panel_measurement_chose():
    """A silent revert of this key is a silent cost/quality change.

    Nothing else in the suite would notice `lens_compute` disappearing from the
    shipped config, and the hook fails soft by design — so the panel would
    quietly go back to inheriting the cockpit's compute with no signal.
    """
    shipped = yaml.safe_load(
        (REPO_ROOT / "config" / "dev-model.yaml").read_text(encoding="utf-8")
    )
    compute = shipped["review"]["fallback_panel"]["lens_compute"]

    assert compute["claude"]["model"] == "sonnet"
    assert compute["claude"]["effort"] == "high"
    # codex exposes effort only; asserting no `model` keeps the "a runtime may
    # carry one control" case represented in the shipped file, which is what the
    # lone-control renderer test above is written against.
    assert "model" not in compute["codex"]


def test_lens_compute_actually_reaches_the_panel_instruction(monkeypatch):
    """The positive path the whole key exists for.

    Its sibling below pins that the clause must NOT reach the degraded branch,
    and the renderer tests pin that the clause is built correctly — but until
    this test existed, deleting the `+ lens_compute` append from
    `_fallback_instruction` entirely left the whole suite green. The claim "this
    key is load-bearing" rested on wiring that no mutant could kill. Found by an
    adversarial review that deleted exactly that line.
    """
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        lambda *_a, **_k: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            ["zzz-lens-one", "zzz-lens-two"],  # two lenses -> PANEL branch
            "fallback:test-panel",
            " Run each lens at model zzz-model and effort zzz-effort.",
        ),
    )

    reminder = hook.build_reminder()

    assert "PANEL" in reminder, "guard: this must be the panel branch"
    assert "zzz-model" in reminder
    assert "zzz-effort" in reminder


def test_a_fault_confined_to_lens_compute_does_not_drop_the_panel(monkeypatch):
    """A failure reading the least important field must not empty `lenses`.

    All six fields once shared one `try`, so a raise from the lens_compute read
    returned the whole default tuple — including `lenses == []`, which routes
    `_fallback_instruction` to the DEGRADED single-lens wording. The panel would
    stop being advertised for a reason having nothing to do with the panel.
    Not reachable through any config shape found by fuzzing, which is exactly
    why it needs a test rather than a comment.
    """
    hook = _load_hook()

    def _boom(*_args, **_kwargs):
        raise RuntimeError("lens_compute read exploded")

    monkeypatch.setattr(hook, "_lens_compute_phrase", _boom)

    bots, _fb, _eng, lenses, panel_source, lens_compute = hook._load_review_config()

    assert lens_compute == "", "the failed field itself degrades to silence"
    assert lenses, "a lens_compute fault must NOT empty the lens roster"
    assert panel_source == "fallback:panel"
    assert "PANEL" in hook._fallback_instruction(
        "/code-review", lenses, panel_source, "scripts", lens_compute
    )

# ── #301: the runtime is a parameter, not a hardcoded key ────────────────────


def test_runtime_from_argv_reads_both_spellings():
    module = _load_hook()
    assert module._runtime_from_argv(["--runtime", "codex"]) == "codex"
    assert module._runtime_from_argv(["--runtime=codex"]) == "codex"


def test_runtime_defaults_to_claude_so_a_pre_301_registration_still_works():
    """`.claude/settings.json` passed no argument before #301; an engine refresh
    must not silence the hook for an adopter who has not updated their settings."""
    module = _load_hook()
    assert module._runtime_from_argv([]) == "claude"


def test_an_unknown_runtime_falls_back_rather_than_reading_a_missing_key():
    """A typo would otherwise resolve `review.fallback_commands.<typo>` to the
    generic default and degrade the reminder silently."""
    module = _load_hook()
    assert module._runtime_from_argv(["--runtime", "emacs"]) == "claude"


def test_each_runtime_gets_its_own_fallback_command(monkeypatch):
    """The defect #301 exists to fix: registering this hook on Codex while it
    hardcoded `.claude` told a Codex session to run Claude's review command."""
    hook = _load_hook()
    seen = {}

    def _fake(runtime="claude"):
        seen["runtime"] = runtime
        return (["somebot"], f"/{runtime}-only", "scripts", [], "fallback:panel", "")

    monkeypatch.setattr(hook, "_load_review_config", _fake)

    claude = hook.build_reminder("claude")
    assert seen["runtime"] == "claude"
    assert "/claude-only" in claude and "/codex-only" not in claude

    codex = hook.build_reminder("codex")
    assert seen["runtime"] == "codex"
    assert "/codex-only" in codex and "/claude-only" not in codex


def test_lens_compute_never_leaks_across_runtimes():
    """An absent key for this runtime yields no clause — it must not fall back to
    the other runtime's model/effort."""
    module = _load_hook()

    class _Kit:
        @staticmethod
        def get(config, path, default=None):
            return {"model": "sonnet"} if path.endswith(".claude") else default

    assert module._lens_compute_phrase({}, _Kit, "claude") != ""
    assert module._lens_compute_phrase({}, _Kit, "codex") == ""

# ── the two mutation survivors the #303 panel found ─────────────────────────
# Both are on the exact lines this change exists to fix, and both survived the
# whole suite: the pieces were tested, the WIRING was not.


def test_main_threads_the_parsed_runtime_all_the_way_to_the_reminder(monkeypatch, capsys):
    """Kills: `build_reminder(runtime)` reverted to `build_reminder()` in main().

    Every other test either calls `main()` without touching argv, or calls
    `build_reminder(runtime)` directly — so `--runtime` could be parsed and then
    silently dropped, and nothing noticed."""
    hook = _load_hook()
    monkeypatch.setattr(
        hook,
        "_load_review_config",
        lambda runtime="claude": ([], f"/{runtime}-sentinel", "scripts", [], "src", ""),
    )
    monkeypatch.setattr("sys.argv", ["pr_followup_hook.py", "--runtime", "codex"])
    monkeypatch.setattr("sys.stdin", io.StringIO(_payload("gh pr create")))

    assert hook.main() == 0
    emitted = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
    assert "/codex-sentinel" in emitted
    assert "/claude-sentinel" not in emitted


def test_load_review_config_reads_the_key_for_the_runtime_it_was_given(monkeypatch, tmp_path):
    """Kills: the f-string reverted to the literal `review.fallback_commands.claude`.

    The sibling runtime test monkeypatches `_load_review_config` away, so the real
    function body — the thing that was hardcoded before #301 — had no coverage."""
    hook = _load_hook()
    hook._load_review_config()  # prime the kitconfig import
    import kitconfig  # noqa: PLC0415

    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *_a, **_k: {
            "review": {
                "bots": ["b"],
                "fallback_commands": {"claude": "/claude-cmd", "codex": "/codex-cmd"},
            }
        },
    )
    assert hook._load_review_config("codex")[1] == "/codex-cmd"
    assert hook._load_review_config("claude")[1] == "/claude-cmd"


@pytest.mark.parametrize(
    "argv",
    [
        ["--runtime"],                      # trailing flag, no value
        ["--runtime="],                     # empty value
        ["--runtime", "--codex"],           # value is itself a flag
        ["--runtime", "c\u00f6dex"],         # unicode near-miss
        ["--runtime", "fallback_commands"], # a real config key, wrong slot
    ],
)
def test_malformed_runtime_degrades_to_the_default_rather_than_a_missing_key(argv):
    """Every malformed shape resolves to the default. That is the documented
    choice — but it means a malformed CODEX invocation renders CLAUDE's values,
    the leakage class #301 exists to close, reached through a different door.
    Pinned here so a future change to that trade-off is deliberate."""
    module = _load_hook()
    assert module._runtime_from_argv(argv) == "claude"


def test_first_runtime_flag_wins_when_repeated():
    module = _load_hook()
    assert module._runtime_from_argv(["--runtime", "codex", "--runtime", "claude"]) == "codex"

def test_load_review_config_threads_the_runtime_into_lens_compute_too(monkeypatch):
    """Kills: `_lens_compute_phrase(config, kitconfig, runtime)` losing its third
    argument and silently defaulting to claude.

    The sibling leak test exercises `_lens_compute_phrase` DIRECTLY with an
    explicit runtime, so it cannot see that call site drop the argument. That is
    the same shape as the two survivors the previous round found: the piece was
    tested, the wiring was not. Against this repo's own config the mutation is
    live, not theoretical — a Codex reminder would say "model sonnet", which is
    Claude's model."""
    hook = _load_hook()
    hook._load_review_config()  # prime the kitconfig import
    import kitconfig  # noqa: PLC0415

    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *_a, **_k: {
            "review": {
                "bots": ["b"],
                "fallback_panel": {
                    "lenses": [{"name": "one"}, {"name": "two"}],
                    "lens_compute": {
                        "claude": {"model": "claude-sentinel-model"},
                        "codex": {"effort": "codex-sentinel-effort"},
                    },
                },
            }
        },
    )

    codex_clause = hook._load_review_config("codex")[5]
    assert "codex-sentinel-effort" in codex_clause
    assert "claude-sentinel-model" not in codex_clause

    claude_clause = hook._load_review_config("claude")[5]
    assert "claude-sentinel-model" in claude_clause
    assert "codex-sentinel-effort" not in claude_clause


# ── #302: the command selects candidates, the response decides ───────────────
# Every shape below was observed live, firing a MANDATORY watch-loop mandate
# with zero open PRs. Two are self-referential: one is the commit that documented
# the bug, the other is a review lens that had never heard of it.

_MENTIONS = [
    pytest.param(
        'python3 -c \'print("run gh pr create when ready")\'',
        "run gh pr create when ready\n",
        id="echoes_the_phrase",
    ),
    pytest.param(
        "grep -rn 'gh pr create' scripts/",
        "scripts/hooks/pr_followup_hook.py:58:  gh pr create\n",
        id="greps_for_the_phrase",
    ),
    pytest.param(
        "uv run pytest -k 'gh pr ready' -q",
        "1 passed in 0.4s\n",
        id="a_test_selector_naming_it",
    ),
    pytest.param(
        'git commit -m "note that gh pr create fires this hook"',
        "[main abc1234] note that gh pr create fires this hook\n",
        id="a_commit_message_documenting_it",
    ),
    pytest.param(
        "gh pr create --help",
        "Create a pull request on GitHub.\nUSAGE\n  gh pr create [flags]\n",
        id="reading_its_own_help",
    ),
]


@pytest.mark.parametrize("command,stdout", _MENTIONS)
def test_a_command_that_merely_mentions_the_phrase_stays_silent(
    monkeypatch, capsys, command, stdout
):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, _payload_with(command, stdout=stdout))

    assert exit_code == 0
    assert out == "", f"spurious mandate for a command that only mentions it: {command}"


def test_a_real_pr_create_still_fires_on_the_url_it_printed(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(
        hook,
        monkeypatch,
        capsys,
        _payload_with(
            "gh pr create --title x --body y",
            stdout="https://github.com/topij/agentic-dev-kit/pull/306\n",
        ),
    )

    assert exit_code == 0
    assert "MANDATORY" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize(
    "stderr",
    [
        'Pull request topij/agentic-dev-kit#306 is marked as "ready for review"\n',
        # idempotent re-run: a real PR still exists, so the reminder is still owed
        'Pull request topij/agentic-dev-kit#306 is already "ready for review"\n',
    ],
    ids=["marked_ready", "already_ready"],
)
def test_pr_ready_fires_on_its_stderr_ack_since_it_prints_no_url(monkeypatch, capsys, stderr):
    """`gh pr ready` emits no URL — established from `gh`'s source, not assumed.
    Its confirmation goes to stderr, so the URL check alone would miss it."""
    hook = _load_hook()
    exit_code, out = _run(
        hook, monkeypatch, capsys, _payload_with("gh pr ready 306", stderr=stderr)
    )

    assert exit_code == 0
    assert "MANDATORY" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(None, id="absent"),
        pytest.param({}, id="empty_dict"),
        pytest.param("", id="empty_string"),
        pytest.param({"stdout": "", "stderr": ""}, id="captured_nothing"),
    ],
)
@pytest.mark.parametrize(
    "command",
    ("gh pr create --fill", "gh pr create --draft --fill", "gh pr ready 42"),
)
def test_an_unreadable_response_fires_rather_than_risking_a_missed_reminder(
    monkeypatch, capsys, response, command
):
    """The direction stays fail-loud where the payload cannot settle it.

    `captured_nothing` is the load-bearing case: a runtime that does not capture
    stderr makes a real `gh pr ready` look exactly like a command that printed
    nothing, and a missed reminder costs the follow-through this hook exists to
    guarantee.
    """
    hook = _load_hook()
    payload = {"tool_input": {"command": command}}
    if response is not None:
        payload["tool_response"] = response

    exit_code, out = _run(hook, monkeypatch, capsys, json.dumps(payload))

    assert exit_code == 0
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "MANDATORY" in context
    assert "ambiguous lifecycle evidence" in context
    assert "resolve the exact pull-request identity" in context
    assert "if none exists, stop without changing any pull request" in context
    assert hook._pr_lifecycle(command, None) == "unknown"


def test_a_response_that_cannot_be_serialised_is_treated_as_unreadable(monkeypatch, capsys):
    hook = _load_hook()
    # a dict pytest can build but json cannot render — unreadable, so fail loud
    assert hook.should_fire("gh pr create", None) is True
    assert hook._response_text({"tool_response": {"k": {1, 2}}}) is None


def test_should_fire_needs_the_command_first_whatever_the_response_says(monkeypatch, capsys):
    """A PR URL in the output of an unrelated command must not fire it."""
    hook = _load_hook()
    assert (
        hook.should_fire(
            "gh pr view 306", "https://github.com/topij/agentic-dev-kit/pull/306"
        )
        is False
    )
    assert hook.should_fire(None, "https://github.com/x/y/pull/1") is False


@pytest.mark.parametrize(
    "command",
    (
        'gh pr view "$PR" --json url --jq .url',
        'printf "%s\\n" "$NOTE"; gh pr view 42 --json url --jq .url',
    ),
)
def test_unrelated_shell_expansion_cannot_turn_a_view_into_a_lifecycle_event(command):
    hook = _load_hook()
    response = "https://github.com/owner/repo/pull/42\n"

    assert hook.should_fire(command, response) is False


def test_lifecycle_words_in_argument_position_cannot_borrow_a_later_view_url():
    hook = _load_hook()
    command = (
        "printf '%s\\n' 'gh pr create --draft'; "
        "gh pr view 42 --json url --jq .url"
    )
    response = "https://github.com/owner/repo/pull/42\n"

    assert hook.should_fire(command, response) is False


def test_each_action_is_matched_against_its_own_evidence(monkeypatch, capsys):
    """CodeRabbit on `#306`: accepting either signal for either action let a
    command merely mentioning `gh pr ready` fire on any PR URL in its output."""
    hook = _load_hook()
    url = "https://github.com/topij/agentic-dev-kit/pull/306"
    ack = 'Pull request topij/agentic-dev-kit#306 is marked as "ready for review"'

    # mismatched pairs stay silent
    assert hook.should_fire("echo 'next: gh pr ready 306'", url) is False
    assert hook.should_fire("echo 'next: gh pr create'", ack) is False
    # matched pairs fire
    assert hook.should_fire("gh pr create --fill", url) is True
    assert hook.should_fire("gh pr ready 306", ack) is True


def test_one_command_doing_both_fires_on_either_signal_alone(monkeypatch, capsys):
    """`gh pr create --draft && gh pr ready` is one command with two actions.

    ANY, not ALL: a runtime that drops stderr carries only the URL, and
    requiring both would go silent on a PR that was genuinely just opened.
    """
    hook = _load_hook()
    both = "gh pr create --draft --fill && gh pr ready"

    assert hook.should_fire(both, "https://github.com/topij/agentic-dev-kit/pull/306") is True
    assert hook.should_fire(both, 'Pull request x/y#1 is marked as "ready for review"') is True
    assert hook.should_fire(both, "nothing relevant here") is False


def test_a_pr_url_buried_in_other_output_is_not_a_pr_being_opened(monkeypatch, capsys):
    """Found live while this PR was open, by this PR's own hook.

    Replying to a review comment with `gh api …/comments/N/replies` fired the
    mandate: the command text quoted the trigger phrase (it was explaining the
    fix) and the API's JSON response carried
    `https://github.com/…/pull/306#discussion_r…`. Command matched, URL matched,
    no PR opened.

    `gh pr create` prints the URL alone on its line and nothing else, so
    anchoring costs no real invocation.
    """
    hook = _load_hook()
    quoting = "gh api repos/o/r/pulls/306/comments/1/replies -f body='use gh pr create'"

    assert (
        hook.should_fire(
            quoting,
            '{"html_url": "https://github.com/topij/agentic-dev-kit/pull/306#discussion_r37"}',
        )
        is False
    )
    # a URL mentioned mid-sentence is not one either
    assert hook.should_fire("gh pr create --fill", "see https://x/pull/1 for details") is False
    # but the real thing, alone on its line, still fires — with or without noise around it
    assert hook.should_fire("gh pr create --fill", "https://github.com/o/r/pull/306\n") is True
    assert (
        hook.should_fire(
            "gh pr create --fill",
            "Warning: 3 uncommitted changes\nhttps://github.com/o/r/pull/306\n",
        )
        is True
    )


# ── the response shape is not ours to guess (#306, round-1 lens) ─────────────
# Codex's PostToolUse schema types `tool_response` as `true` — any value, no
# promised structure. An earlier version read six hardcoded keys and serialised
# anything else with `json.dumps`, which escapes newlines, so the line-anchored
# URL match could never fire on a serialised payload: a genuine `gh pr create`
# under an unrecognised shape went SILENT. Every shape below carries the same
# real PR URL and every one must fire.

_URL = "https://github.com/topij/agentic-dev-kit/pull/306"

_SHAPES = [
    pytest.param({"stdout": _URL + "\n", "stderr": ""}, id="flat_stdout_stderr"),
    pytest.param(_URL + "\n", id="plain_string"),
    pytest.param({"output": {"stdout": _URL + "\n", "stderr": ""}, "exit_code": 0}, id="nested_output"),
    pytest.param({"exec_output": _URL + "\n", "exit_code": 0}, id="unknown_key_name"),
    pytest.param({"chunks": [{"type": "text", "text": _URL + "\n"}]}, id="list_of_content_blocks"),
    pytest.param([{"text": _URL + "\n"}], id="top_level_list"),
]


@pytest.mark.parametrize("response", _SHAPES)
def test_a_real_pr_create_fires_whatever_shape_the_runtime_reports_it_in(
    monkeypatch, capsys, response
):
    hook = _load_hook()
    payload = json.dumps(
        {"tool_input": {"command": "gh pr create --fill"}, "tool_response": response}
    )

    exit_code, out = _run(hook, monkeypatch, capsys, payload)

    assert exit_code == 0
    assert out != "", "a real PR was opened and the reminder was silently dropped"
    # …and it fired because the URL was FOUND, not because the payload was
    # unreadable and fail-loud caught it. A round-2 lens showed this test passed
    # either way: cutting the depth bound to 1, and deleting list handling
    # outright, both left the whole suite green because `out != ""` cannot tell
    # a successful walk from a total miss.
    assert _URL in (hook._response_text({"tool_response": response}) or "")


@pytest.mark.parametrize(
    "response",
    [
        pytest.param({"stdout": None, "stderr": None}, id="known_keys_but_null"),
        pytest.param({"exit_code": 0, "duration_ms": 12}, id="no_strings_at_all"),
        pytest.param({"k": {1, 2}}, id="unserialisable"),
        pytest.param([], id="empty_list"),
    ],
)
def test_a_payload_carrying_no_readable_text_still_fails_loud(monkeypatch, capsys, response):
    """These used to reach `json.dumps` and be read as evidence of nothing.
    A payload with no strings cannot settle whether a PR was opened."""
    hook = _load_hook()
    assert hook._response_text({"tool_response": response}) is None
    payload = json.dumps({"tool_input": {"command": "gh pr create --fill"}})
    exit_code, out = _run(hook, monkeypatch, capsys, payload)
    assert exit_code == 0 and out != ""


def test_a_payload_too_deep_for_json_load_still_exits_zero(monkeypatch, capsys):
    """`json.load` raises RecursionError before this module sees the payload.

    A lens ran the real script on a 200k-deep array and got exit 1, against a
    docstring promising a hook never fails a session. `_iter_strings`'s depth
    bound cannot help — the parse never completes. Pre-existing, and the
    previous version of this test asserted the property in its docstring while
    exercising a path `json.load` can never reach.
    """
    hook = _load_hook()
    text = '{"tool_input": {"command": "gh pr create"}, "tool_response": '
    text += "[" * 200_000 + '"x"' + "]" * 200_000 + "}"

    exit_code, out = _run(hook, monkeypatch, capsys, text)

    assert exit_code == 0
    assert out == ""


def test_walking_for_strings_is_depth_bounded(monkeypatch, capsys):
    """The walk's own bound, distinct from the parser's above."""
    hook = _load_hook()
    deep: object = "https://github.com/o/r/pull/1"
    for _ in range(60):
        deep = {"nested": deep}

    assert hook._response_text({"tool_response": deep}) is None  # past the bound
    assert hook.should_fire("gh pr create", None) is True


def test_shallow_noise_beside_deep_evidence_does_not_buy_silence(monkeypatch, capsys):
    """The regression a round-2 lens proved, as a fixture.

    Fail-loud triggers only when a payload yields NOTHING readable. So a payload
    with an irrelevant shallow string beside evidence nested past the bound used
    to read as "readable, and the evidence is not in it" — silence, on a PR that
    really was readied. The bound now raises instead of truncating, so a payload
    that cannot be walked in full settles nothing and fires.
    """
    hook = _load_hook()
    ack = 'Pull request o/r#1 is marked as "ready for review"'
    buried: object = ack
    for _ in range(hook._MAX_DEPTH + 2):
        buried = {"nested": buried}

    payload = {"noise": "duration_ms=12", "buried": buried}
    assert hook._response_text({"tool_response": payload}) is None
    assert hook.should_fire("gh pr ready 1", hook._response_text({"tool_response": payload}))

    # and the same shape inside the bound is walked rather than abandoned
    shallow: object = ack
    for _ in range(hook._MAX_DEPTH - 2):
        shallow = {"nested": shallow}
    assert ack in (hook._response_text({"tool_response": {"n": "x", "b": shallow}}) or "")


def test_a_list_in_the_payload_is_actually_walked(monkeypatch, capsys):
    """Deleting `_iter_strings`'s list branch left the whole suite green, because
    every list fixture still fired — via fail-loud, not via being read."""
    hook = _load_hook()
    found = hook._response_text({"tool_response": [{"text": "https://x/pull/9\n"}]})
    assert found is not None and "https://x/pull/9" in found


def test_content_in_a_key_is_not_treated_as_tool_output(monkeypatch, capsys):
    """Values only. Walking keys would let an arbitrary label pose as output."""
    hook = _load_hook()
    assert hook._response_text({"tool_response": {"https://x/pull/9": None}}) is None
