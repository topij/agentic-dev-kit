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
        # (tuple[list[str], str, str, list[str], str]) rather than being merely
        # duck-compatible: `panel_source` in particular is guarded twice and
        # defaulted on the except path, so `None` is not a value the real
        # function can return, and a mock that returns one could mask a
        # type-shape bug instead of exposing it.
        lambda: (["zzz-sentinel-bot"], "/code-review", "scripts", [], "fallback:test-panel"),
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
        lambda: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            ["zzz-lens-one", "zzz-lens-two"],
            "fallback:test-panel",
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
        lambda: (
            ["zzz-sentinel-bot"],
            "/code-review",
            "scripts",
            ["zzz-lens-one", "zzz-lens-two"],
            "fallback:test-panel",
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

    _bots, _fb, _eng, lenses, _src = hook._load_review_config()

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
    bots, fallback, engines, lenses, panel_source = hook._load_review_config()
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
