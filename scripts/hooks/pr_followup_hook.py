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
bot(s) and fallback command this repo actually configures, read from
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


def _load_review_config() -> tuple[list[str], str, str]:
    """Read ``(review.bots, review.fallback_commands.claude, paths.engines)``.

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
        return bots, fallback, engines
    except Exception:
        return [], _DEFAULT_FALLBACK_COMMAND, _DEFAULT_ENGINES_DIR


def _bot_description(bots: list[str]) -> str:
    if not bots:
        return "the configured review bot(s)"
    names = [b.strip() for b in bots if isinstance(b, str) and b.strip()]
    if not names:
        return "the configured review bot(s)"
    return " / ".join(names)


def build_reminder() -> str:
    bots, fallback_command, engines_dir = _load_review_config()
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
        "can take 20-30 min). If a review bot is unavailable, run the configured "
        f"fallback (`{fallback_command}`) instead of treating the outage as a review "
        "waiver. Only stop early if you hit something that genuinely needs an "
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
