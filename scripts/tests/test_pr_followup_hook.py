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
    """The reminder must be sourced from config (review.bots / fallback_panel),
    never a hardcoded bot literal — this is the whole point of generalizing the
    reference implementation (Principle #10, "No hardcoding")."""
    hook = _load_hook()
    reminder = hook.build_reminder()
    assert "coderabbit" in reminder  # from this repo's config/dev-model.yaml review.bots
    assert "bugbot" not in reminder.lower()


def test_reminder_points_at_the_panel_not_the_degraded_one_lens_mode(monkeypatch):
    """This hook fires on every `gh pr create`/`ready`, so it is the most-read
    statement of the fallback policy in the kit.

    Pointing it at `fallback_commands` — a single command in the author's own
    context — taught the wrong habit every time it fired, against
    `safety-critical-changes.md` rule 2. With a panel configured it must name
    the panel and its lenses.
    """
    hook = _load_hook()

    reminder = hook.build_reminder()

    assert "PANEL" in reminder
    assert "adversarial" in reminder and "correctness" in reminder
    assert "fallback-review-panel.md" in reminder
    assert "--lenses" in reminder
    # …and it must NOT advertise the degraded command as the thing to run.
    assert "/code-review" not in reminder


def test_the_reminder_uses_the_configured_receipt_source_not_a_literal():
    """`review.fallback_panel.receipt_source` exists so an adopter can rename it.

    Prescribing the literal in the instruction would hand them a command that
    writes a differently-labelled receipt than their own config declares —
    adding a config key and then ignoring it (Principle #10).
    """
    hook = _load_hook()

    renamed = hook._fallback_instruction(
        "/x", ["adversarial", "correctness"], "fallback:my-panel"
    )

    assert '"fallback:my-panel"' in renamed
    assert "fallback:panel" not in renamed


def test_blank_lens_names_are_discarded_rather_than_advertised(monkeypatch):
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

    _bots, _fb, _eng, lenses, _src = hook._load_review_config()

    assert lenses == ["adversarial"]


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
    bots, fallback, engines, lenses, panel_source = hook._load_review_config()
    assert bots == []
    assert fallback == "/code-review"
    assert engines == "scripts"
    # No panel known → the reminder degrades to the single command rather than
    # naming lenses that were never read.
    assert lenses == []
    assert panel_source == "fallback:panel"
    assert "PANEL" not in hook._fallback_instruction(fallback, lenses, panel_source)
