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


ENGINE_DIR = Path(__file__).resolve().parent.parent
HOOK_PATH = ENGINE_DIR / "hooks" / "pr_followup_hook.py"


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
    return json.dumps({"tool_input": {"command": command}})


@pytest.fixture(autouse=True)
def _no_job_name(monkeypatch):
    """Every test runs outside cron/CI unless it explicitly sets JOB_NAME."""
    monkeypatch.delenv("JOB_NAME", raising=False)


def test_triggers_on_gh_pr_create(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, _payload("gh pr create --draft --title x"))
    assert exit_code == 0
    body = json.loads(out)
    assert body["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "additionalContext" in body["hookSpecificOutput"]
    assert "pr-watch" in body["hookSpecificOutput"]["additionalContext"]


def test_triggers_on_gh_pr_ready(monkeypatch, capsys):
    hook = _load_hook()
    exit_code, out = _run(hook, monkeypatch, capsys, _payload("gh pr ready 42"))
    assert exit_code == 0
    body = json.loads(out)
    assert body["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


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


def test_reminder_names_configured_bots_and_fallback_not_a_hardcoded_bot(monkeypatch):
    """The reminder must be sourced from config (review.bots / fallback_commands),
    never a hardcoded bot literal — this is the whole point of generalizing the
    reference implementation (Principle #10, "No hardcoding")."""
    hook = _load_hook()
    reminder = hook.build_reminder()
    assert "coderabbit" in reminder  # from this repo's config/dev-model.yaml review.bots
    assert "/code-review" in reminder  # review.fallback_commands.claude
    assert "codex" not in reminder.lower()
    assert "bugbot" not in reminder.lower()


def test_load_review_config_degrades_gracefully_when_config_unreadable(monkeypatch):
    """A missing/unreadable config must never raise — the hook falls back to
    generic wording rather than failing the session."""
    hook = _load_hook()
    hook._load_review_config()  # prime the import so `kitconfig` lands in sys.modules
    import kitconfig  # noqa: PLC0415

    def _boom(*_args, **_kwargs):
        raise FileNotFoundError("no config here")

    monkeypatch.setattr(kitconfig, "load_config", _boom)
    bots, fallback, engines = hook._load_review_config()
    assert bots == []
    assert fallback == "/code-review"
    assert engines == "scripts"
