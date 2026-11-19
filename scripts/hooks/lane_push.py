"""Grant the shipped Claude profile's standalone push from the issued lane."""

from __future__ import annotations

import json
import os
import shlex
import sys


def push_decision(event: dict, branch: str, worktree: str) -> dict:
    # The launcher supplies these values from the checked descriptor on launch
    # and resume. Neither the working branch nor a lane-writable file is authority.
    if not branch or not worktree or event.get("cwd") != worktree:
        return {}
    if event.get("tool_name") != "Bash" or event.get("hook_event_name") != "PreToolUse":
        return {}
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict) or tool_input.get("command") != (
        "git push -u origin " + shlex.quote(branch)
    ):
        return {}
    if tool_input.keys() - {"command", "description", "timeout"}:
        return {}
    # Grant only the command. Discard any tool options, including requests to
    # run outside the sandbox. Explicit heads avoid a configured default push
    # mapping, and --no-follow-tags keeps implicit tag pushes out of this grant.
    ref = "refs/heads/" + branch
    command = shlex.join(
        ["git", "push", "-u", "--no-follow-tags", "--recurse-submodules=no", "origin", f"{ref}:{ref}"]
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {"command": command},
        }
    }


if __name__ == "__main__":
    decision = push_decision(
        json.load(sys.stdin),
        os.environ.get("ADK_LANE_BRANCH", ""),
        os.environ.get("ADK_LANE_WORKTREE", ""),
    )
    print(json.dumps(decision))
