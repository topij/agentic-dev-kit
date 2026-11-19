"""Claude lane's direct GitHub, PR assertion and commit-message permissions."""

from __future__ import annotations

import json
import os
import re
import shlex
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class Refused(ValueError):
    pass


def message_file(name: str):
    """Open from the actual lane cwd, rejecting links throughout the path."""
    path = Path(name)
    if path.is_absolute():
        path = path.relative_to(Path.cwd())
    if not path.parts or ".." in path.parts or name == "-":
        raise Refused("expected a message file inside the lane")
    directory = os.open(".", os.O_DIRECTORY)
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    finally:
        os.close(directory)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise Refused("expected a regular message file with one link")
    return os.fdopen(fd, "rb")


def own_pr(repo: str, branch: str, base: str) -> str:
    result = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--head", branch, "--base", base, "--state", "open",
         "--limit", "2", "--json", "number,headRefName,baseRefName,isCrossRepository"],
        check=True, capture_output=True, timeout=30,
    )
    rows = json.loads(result.stdout)
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise Refused("expected one open lane PR")
    row = rows[0]
    if (row.get("headRefName") != branch or row.get("baseRefName") != base
            or row.get("isCrossRepository") is not False
            or type(row.get("number")) is not int or row["number"] < 1):
        raise Refused("PR identity differs from the issued lane")
    return str(row["number"])


def json_fields(args: list[str]) -> bool:
    return not args or (len(args) == 2 and args[0] == "--json"
                        and re.fullmatch(r"[a-zA-Z]+(?:,[a-zA-Z]+)*", args[1]) is not None)


@dataclass
class Request:
    argv: list[str]
    filename: str | None = None
    needs_pr: bool = False
    selector: str | None = None


def creation(args: list[str], repo: str, branch: str, base: str) -> Request:
    options = {}
    while args:
        key, *args = args
        if key not in {"--body-file", "--title", "--base", "--head", "--draft"} or key in options:
            raise Refused("unsupported or duplicate PR creation option")
        if key == "--draft":
            options[key] = True
        elif args and args[0] and not args[0].startswith("-"):
            options[key], *args = args
        else:
            raise Refused(f"missing value for {key}")
    if options.get("--base", base) != base or options.get("--head", branch) != branch:
        raise Refused("PR creation requires the issued base and head")
    if "--body-file" not in options:
        raise Refused("PR creation requires --body-file")
    command = ["gh", "pr", "create", "--repo", repo, "--base", base, "--head", branch, "--body-file", "-"]
    command.extend(["--title", options["--title"]] if "--title" in options else ["--fill"])
    if "--draft" in options:
        command.append("--draft")
    return Request(command, filename=options["--body-file"])


WATCHERS = {"scripts/pr_watch.py", "scripts/devkit/pr_watch.py"}


def request(words: list[str], repo: str, branch: str, base: str) -> Request:
    if words[:2] == ["git", "commit"]:
        if len(words) == 4 and words[2] == "-F":
            return Request(["git", "commit", "-F", "-"], filename=words[3])
        if len(words) == 4 and words[2] == "-m":
            return Request(words)
        raise Refused("use git commit -F <lane-file> or -m <message>")
    if not repo:
        raise Refused("expected a forge origin with an owner and repository")
    args = words[3:]
    if words[:3] == ["gh", "pr", "create"]:
        return creation(args, repo, branch, base)
    if words[:3] == ["gh", "repo", "view"] and json_fields(args):
        return Request(["gh", "repo", "view", repo, *args])
    if words[:2] == ["uv", "run"] and words[2] in WATCHERS:
        if len(args) != 2 or args[1] not in {"--assert-draft", "--assert-ready"}:
            raise Refused("use the lane watcher for draft and ready assertions")
        script = Path(__file__).resolve().parents[1] / "pr_watch.py"
        return Request([sys.executable, "-I", str(script), args[1]], needs_pr=True, selector=args[0])
    if words[:2] != ["gh", "pr"] or words[2:3] not in (["checks"], ["view"], ["ready"], ["list"]):
        raise Refused("unsupported lane command")
    selector = args.pop(0) if args and not args[0].startswith("-") else None
    if not (json_fields(args) if words[2] in {"checks", "view"} else not args):
        raise Refused("unsupported PR option")
    if words[2] == "list":
        return Request([], needs_pr=True, selector=selector)
    return Request(["gh", "pr", words[2], "--repo", repo, *args], needs_pr=True, selector=selector)


def run(words: list[str], root: str, repo: str, branch: str, base: str) -> int:
    if os.getcwd() != root or not branch or not base:
        raise Refused("command requires the issued lane root, branch and base")
    operation = request(words, repo, branch, base)
    if repo:
        os.environ.update(GH_REPO=repo, GH_HOST=repo.split("/")[0], GH_PROMPT_DISABLED="1", GH_PAGER="cat")
    if operation.needs_pr:
        number = own_pr(repo, branch, base)
        if operation.selector not in {None, number, branch}:
            raise Refused("requested PR differs from the issued lane")
        if not operation.argv:
            print(number)
            return 0
        operation.argv.append(number)
    if operation.filename is not None:
        with message_file(operation.filename) as message:
            return subprocess.run(operation.argv, stdin=message).returncode
    return subprocess.run(operation.argv, stdin=subprocess.DEVNULL).returncode


def hook(event: dict) -> dict:
    tool = event.get("tool_input")
    if (event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash"
            or not isinstance(tool, dict) or not isinstance(tool.get("command"), str)
            or tool.keys() - {"command", "description", "timeout"}):
        return {}
    try:
        words = shlex.split(tool["command"])
    except ValueError:
        return {}
    if not (words[:1] == ["gh"] or words[:2] == ["git", "commit"]
            or (words[:2] == ["uv", "run"] and words[2:3] and words[2] in WATCHERS)):
        return {}
    keys = ("ADK_LANE_WORKTREE", "ADK_LANE_REPO", "ADK_LANE_BRANCH", "ADK_LANE_BASE")
    binding = [os.environ.get(key, "") for key in keys]
    if not binding[0] or binding[0] != event.get("cwd") or not all(binding[2:]):
        return {}
    try:
        request(words, *binding[1:])
    except Refused as error:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": str(error)}}
    # Rebuild a standalone argv. Neither the original shell expression nor its
    # environment can choose the executor, authority or additional tool options.
    command = shlex.join([sys.executable, "-I", str(Path(__file__).resolve()), *binding, *words])
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                   "updatedInput": {"command": command}}}


if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            print(json.dumps(hook(json.load(sys.stdin))))
        else:
            sys.exit(run(sys.argv[5:], *sys.argv[1:5]))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(f"lane command refused: {error}")
