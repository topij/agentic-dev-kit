#!/usr/bin/env python3
"""PostToolUse hook: after a PR is opened / marked ready, mandate the watch-fix loop.

Wired in `.claude/settings.json` under `hooks.PostToolUse` with matcher `Bash` and
`if: "Bash(gh pr *)"`. The `if` pre-filters to `gh pr …` commands; this script
further narrows to `gh pr create` / `gh pr ready` (the moments a PR goes live for
review) and injects an `additionalContext` instruction so the session runs the
kit's PR follow-through loop (Principle #5 in `PRINCIPLES.md`) without being asked.
This closes the gap where the kit only had prose asking the agent to run `/pr-watch`
unasked (Principle #8: "a rule that lives only in a doc is a wish").

Generalized from a project-specific version: the reminder names whichever review
bot(s) and the fallback PANEL (or, with none configured, the single fallback
command) this repo actually configures, read from
`config/dev-model.yaml` via `scripts/lib/kitconfig.py` — never a hardcoded bot name
(Principle #10, "No hardcoding"). `paths.engines` resolves where `pr_watch.py` lives
so the reminder's poll command is correct even when the kit is vendored under a
nested engines dir. If config can't be read (missing file, kitconfig import
failure, or this script's own repo-root walk fails), the reminder still fires with
generic, runtime-agnostic wording rather than skipping the nag entirely — a
degraded reminder is better than a silently missing one.

Cron-safe: a no-op when `JOB_NAME` is set (the kit's own cron/CI signal — see
`scripts/lib/state_paths/resolver.py`), so a scheduled workflow's own PR-opens never
trigger it. Always exits 0 — a hook must never fail a session.

Reads the PostToolUse JSON on stdin; the bash command is at `.tool_input.command`.
To inject context from a PostToolUse hook you print
`{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": …}}`
(plain stdout is not surfaced for PostToolUse).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_TRIGGER = re.compile(r"\bgh\s+pr\s+(create|ready)\b")

_DEFAULT_FALLBACK_COMMAND = "/code-review"
_DEFAULT_ENGINES_DIR = "scripts"
_DEFAULT_LENSES: list[str] = []
_DEFAULT_PANEL_RECEIPT_SOURCE = "fallback:panel"


def _load_review_config() -> tuple[list[str], str, str, list[str], str]:
    """Read ``(review.bots, review.fallback_commands.claude, paths.engines,
    review.fallback_panel lens names, review.fallback_panel.receipt_source)``.

    Best-effort: any failure (missing config, kitconfig unimportable, malformed
    values) falls back to generic defaults rather than raising — this hook must
    never fail a session over a config read.
    """
    try:
        here = Path(__file__).resolve()
        lib_dir = here.parent.parent / "lib"
        sys.path.insert(0, str(lib_dir))
        import kitconfig  # noqa: PLC0415

        config = kitconfig.load_config()
        bots = kitconfig.get_str_list(config, "review.bots", [])
        fallback = kitconfig.get(config, "review.fallback_commands.claude", _DEFAULT_FALLBACK_COMMAND)
        engines = kitconfig.get(config, "paths.engines", _DEFAULT_ENGINES_DIR)
        if not isinstance(fallback, str) or not fallback:
            fallback = _DEFAULT_FALLBACK_COMMAND
        if not isinstance(engines, str) or not engines:
            engines = _DEFAULT_ENGINES_DIR
        panel = kitconfig.get(config, "review.fallback_panel.lenses", [])
        lenses = (
            [
                lens["name"].strip()
                for lens in panel
                if isinstance(lens, dict)
                and isinstance(lens.get("name"), str)
                # A blank name would have the hook advertise a panel with an
                # unnameable lens — worse than advertising no panel at all.
                and lens["name"].strip()
            ]
            if isinstance(panel, list)
            else []
        )
        panel_source = kitconfig.get(
            config, "review.fallback_panel.receipt_source", _DEFAULT_PANEL_RECEIPT_SOURCE
        )
        if not isinstance(panel_source, str) or not panel_source.strip():
            panel_source = _DEFAULT_PANEL_RECEIPT_SOURCE
        return bots, fallback, engines, lenses, panel_source.strip()
    except Exception:
        return (
            [],
            _DEFAULT_FALLBACK_COMMAND,
            _DEFAULT_ENGINES_DIR,
            list(_DEFAULT_LENSES),
            _DEFAULT_PANEL_RECEIPT_SOURCE,
        )


def _bot_description(bots: list[str]) -> str:
    if not bots:
        return "the configured review bot(s)"
    names = [b.strip() for b in bots if isinstance(b, str) and b.strip()]
    if not names:
        return "the configured review bot(s)"
    return " / ".join(names)


def _fallback_instruction(
    fallback_command: str,
    lenses: list[str],
    panel_source: str = _DEFAULT_PANEL_RECEIPT_SOURCE,
    engines_dir: str = _DEFAULT_ENGINES_DIR,
) -> str:
    """What to run when a bot is unavailable.

    Names the PANEL when one is configured, because a single command in this
    session's own context is the author reviewing their own diff — which
    `safety-critical-changes.md` rule 2 says is not a green light. This hook
    fires on every `gh pr create`/`ready`, so it is the most-read statement of
    the fallback policy in the kit; pointing it at the degraded mode taught the
    wrong habit every time.
    """
    # Two DISTINCT lenses is the panel's floor (see fallback-review-panel.md).
    # A one-lens `fallback_panel` would otherwise have this hook advertise a
    # command that `record_review` refuses every single time — so a sub-floor
    # config degrades to the single-command wording instead.
    if len({lens.casefold() for lens in lenses}) >= 2:
        return (
            "If a review bot is unavailable, run the fallback review PANEL — one "
            f"isolated, fresh-context reviewer per lens ({', '.join(lenses)}), per "
            "docs/agentic-dev-kit/fallback-review-panel.md — and record it with "
            f"`uv run {engines_dir}/pr_watch.py <PR#> "
            f'--record-review "{panel_source}" --lenses <names> --head <polled-sha>`. '
            "Never treat the outage as a review waiver."
        )
    return (
        f"If a review bot is unavailable, run the configured fallback "
        f"(`{fallback_command}`) instead of treating the outage as a review waiver."
    )


def build_reminder() -> str:
    bots, fallback_command, engines_dir, lenses, panel_source = _load_review_config()
    bot_desc = _bot_description(bots)
    return (
        "A pull request was just opened or marked ready for review. Per the kit's "
        '"PR follow-through" policy (PRINCIPLES.md #5/#8) this step is MANDATORY and '
        "you should start it now without being asked: run the watch-and-fix loop for "
        "this PR — invoke `/pr-watch` (or poll "
        f"`uv run {engines_dir}/pr_watch.py <PR#> --json`) and do NOT yield this turn "
        f"until CI is fully green AND every {bot_desc} finding is fixed or "
        "replied-to with a reason. Fix real findings, reply-with-reason to nitpicks "
        "you disagree with, `--mark-seen` each handled round, and keep polling (CI "
        "can take 20-30 min). "
        + _fallback_instruction(fallback_command, lenses, panel_source, engines_dir)
        + " Only stop early if you hit something that genuinely needs an "
        "operator decision."
    )


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return 0  # malformed payload — never block the session

    if os.environ.get("JOB_NAME"):
        return 0  # cron/CI context — don't nag

    if not isinstance(data, dict):
        return 0

    tool_input = data.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if isinstance(command, str) and _TRIGGER.search(command):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": build_reminder(),
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
