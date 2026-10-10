#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown-it-py==4.0.0"]
# ///
"""Read-only preflight for changes confined to configured narrative paths.

Run with uv so the declared CommonMark parser is available. Git objects, not the
working tree, supply the input. This is an adjunct to an independent full review:
it does not classify prose as inert, authorize a receipt, or prove a run happened.

Exit 0: the implemented checks passed, or the change is explicitly not applicable.
Exit 1: a deterministic check found a defect.
Exit 2: input, applicability, a dependency, or a required read is unavailable.
"""

from __future__ import annotations

import argparse
import datetime
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, loads, repo_root  # noqa: E402

NARRATIVE_KEYS = ("handoff", "handoff_history", "friction_log", "friction_log_archive")
LIMITS = [
    "Only destinations parsed as CommonMark links or images are checked; unresolved reference text is not a parsed link.",
    "Links and stamps are checked in changed Markdown blocks; a changed reference definition also rechecks document links.",
    "External URLs, fragment identifiers, and raw HTML destinations are not verified.",
    "A stamp's commit and date can be checked; its command's execution and claimed result cannot.",
    "A historical stamp need not name the candidate head; the reviewer must judge its stated scope.",
    "Every changed narrative file and commit message remains in full independent-review scope.",
]
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_STAMP = re.compile(
    r"`(?P<command>[^`\n]+)`\s+at\s+`(?P<sha>[^`\n]+)`"
    r"(?:,?\s+in\s+`[^`]+`,?)?\s+on\s+(?P<date>\d{4}-\d{2}-\d{2})"
)
# Scan raw added text, including quotes, code and negation: those do not prevent
# forge automation acting on commit/PR text, nor satisfy the author's intent rule.
_CLOSING = re.compile(
    r"\b(?:close[sd]?|closing|fix(?:es|ed|ing)?|resolve[sd]?|resolving)"
    r"[\s:*`]*?(?P<ref>(?:[\w.-]+/[\w.-]+)?#\d+|"
    r"https://github\.com/[\w.-]+/[\w.-]+/issues/\d+)\b", re.IGNORECASE
)


class CheckError(Exception):
    """A read could not establish the required input."""


class NotApplicable(CheckError):
    """The comparison is outside the declared narrative-path scope."""


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "--literal-pathspecs", *args], cwd=root, capture_output=True,
            text=True, encoding="utf-8", timeout=30, check=False,
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise CheckError(str(exc)) from exc
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {args[0]} failed")
    return result.stdout


def commit(root: Path, value: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
        raise CheckError("base and head must be commit hex shas, not moving refs")
    return git(root, "rev-parse", "--verify", f"{value}^{{commit}}").strip()


def blob(root: Path, revision: str, path: str) -> str:
    entry = git(root, "ls-tree", "-z", revision, "--", path)
    if not entry or entry.split(" ", 1)[0] not in ("100644", "100755"):
        raise CheckError(f"{revision}:{path} is absent or is not a regular file")
    return git(root, "show", f"{revision}:{path}")


def path_value(value: object) -> str:
    if not isinstance(value, str) or not value or "\0" in value:
        raise CheckError("a narrative path is missing or invalid in the base config")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or p.as_posix() != value:
        raise CheckError(f"a configured path is not a normalized repository path: {value!r}")
    return value


def scope(root: Path, base: str, head: str) -> tuple[dict, str, list[str]]:
    config = loads(blob(root, base, "config/dev-model.yaml"))
    declared = {path_value(get(config, f"paths.{key}", None)) for key in NARRATIVE_KEYS}
    boundaries = git(root, "merge-base", "--all", base, head).splitlines()
    if len(boundaries) != 1:
        raise CheckError("the comparison has no unique merge base")
    boundary = boundaries[0]
    paths = git(root, "diff", "--name-only", "-z", "--no-renames", boundary, head).split("\0")
    changed = [p for p in paths if p]
    if not changed or not set(changed) <= declared:
        raise NotApplicable("the change is not confined to the configured narrative paths")
    return config, boundary, changed


def changed_lines(root: Path, boundary: str, head: str, path: str) -> set[int]:
    patch = git(root, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                "--unified=0", boundary, head, "--", path)
    lines: set[int] = set()
    for line in patch.splitlines():
        match = _HUNK.match(line)
        if match:
            start = int(match[1])
            count = int(match[2]) if match[2] is not None else 1
            lines.update(range(start, start + count))
    return lines


def local_target(source: str, target: str) -> str | None:
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    if path.startswith("/"):
        raise CheckError(f"absolute filesystem destination is not repository-verifiable: {target}")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    if resolved == ".." or resolved.startswith("../") or "\0" in resolved:
        raise CheckError(f"destination leaves the repository: {target}")
    return resolved


def check(root: Path, base: str, head: str, allowed: set[str]) -> dict:
    from markdown_it import MarkdownIt

    if Path(git(root, "rev-parse", "--show-toplevel").strip()).resolve() != root:
        raise CheckError("--root must name the repository root, not a subdirectory")
    base, head = commit(root, base), commit(root, head)
    config, boundary, paths = scope(root, base, head)
    report = {"base": base, "head": head, "merge_base": boundary, "paths": paths,
              "findings": [], "unavailable": [], "stamps": [], "limits": LIMITS}

    def finding(kind: str, source: str, line: int, detail: str) -> None:
        report["findings"].append({"check": kind, "source": source, "line": line,
                                   "detail": detail})

    def closings(text: str, source: str, added: set[int] | None = None) -> None:
        for match in _CLOSING.finditer(text):
            ref = match["ref"]
            line = text.count("\n", 0, match.start()) + 1
            end = text.count("\n", 0, match.end()) + 1
            if added is not None and not added.intersection(range(line, end + 1)):
                continue
            if ref not in allowed:
                finding("closing-keywords", source, line,
                        f"closing reference {ref}: explicitly declare --allow-close {ref} only if intended")

    budgets = get(config, "doc_budgets", None)
    if not isinstance(budgets, list):
        raise CheckError("doc_budgets is absent or malformed in the base config")
    for entry in budgets:
        if not isinstance(entry, dict) or not isinstance(entry.get("budget"), int) or isinstance(entry.get("budget"), bool) or entry["budget"] < 0:
            raise CheckError("a doc_budgets entry is malformed")
        path = path_value(entry.get("path"))
        if path in paths:
            text = blob(root, head, path)
            if len(text.splitlines()) > entry["budget"]:
                finding("budgets", path, 1, "candidate exceeds its configured line budget")

    parser = MarkdownIt("commonmark")
    for path in paths:
        # A deleted archive has no added blocks. Required budgeted inputs above
        # still must exist; deletion remains in the full review's diff.
        if not git(root, "ls-tree", "-z", head, "--", path):
            continue
        text = blob(root, head, path)
        lines = text.splitlines(keepends=True)
        added = changed_lines(root, boundary, head, path)
        closings(text, path, added)
        # Parse the entire document so reference definitions and code fences keep
        # their CommonMark meaning; select changed blocks only after parsing.
        environment: dict = {}
        tokens = parser.parse(text, environment)
        changed_reference = any(
            added.intersection(range(ref["map"][0] + 1, ref["map"][1] + 1))
            for ref in environment.get("references", {}).values() if "map" in ref
        )
        for token in tokens:
            if not token.map:
                continue
            start, end = token.map
            touched = bool(added.intersection(range(start + 1, end + 1)))
            if not touched and not changed_reference:
                continue
            if token.type == "inline":
                for child in token.children or []:
                    target = child.attrGet("href") if child.type == "link_open" else child.attrGet("src") if child.type == "image" else None
                    if target is None:
                        continue
                    try:
                        destination = local_target(path, target)
                        if destination not in (None, ".") and not git(root, "ls-tree", "-z", head, "--", destination):
                            finding("links", path, start + 1, f"destination absent from candidate: {target}")
                    except (CheckError, ValueError) as exc:
                        report["unavailable"].append({"check": "links", "source": path,
                                                      "line": start + 1, "detail": str(exc)})
            # Stamps in code examples are not claims about a run. Only prose
            # blocks participate; inline backticks carry the declared stamp form.
            if token.type != "inline" or not touched:
                continue
            block = "".join(lines[start:end])
            for match in _STAMP.finditer(block):
                line = start + block.count("\n", 0, match.start()) + 1
                if not re.fullmatch(r"[0-9a-fA-F]{7,40}", match["sha"]):
                    finding("stamps", path, line, "verification stamp names a moving or invalid revision")
                    continue
                try:
                    datetime.date.fromisoformat(match["date"])
                except ValueError:
                    finding("stamps", path, line, "verification stamp has an invalid calendar date")
                    continue
                try:
                    observed = commit(root, match["sha"])
                except CheckError as exc:
                    report["unavailable"].append({"check": "stamps", "source": path,
                                                  "line": line, "detail": str(exc)})
                    continue
                report["stamps"].append({"source": path, "line": line, "command": match["command"],
                                         "revision": observed, "date": match["date"],
                                         "names_head": observed == head})
    for sha in git(root, "rev-list", "--reverse", f"{boundary}..{head}").splitlines():
        closings(git(root, "show", "-s", "--format=%B", sha), f"commit:{sha}")
    report["status"] = "unavailable" if report["unavailable"] else "failed" if report["findings"] else "passed"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    parser.add_argument("--base", required=True, help="base commit hex sha")
    parser.add_argument("--head", required=True, help="candidate commit hex sha")
    parser.add_argument("--allow-close", action="append", default=[], help="exact intended closing reference; repeat as needed")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.root is not None and not args.root.strip():
            raise CheckError("--root must not be empty or whitespace")
        if any(not re.fullmatch(r"(?:[\w.-]+/[\w.-]+)?#\d+|https://github\.com/[\w.-]+/[\w.-]+/issues/\d+", ref) for ref in args.allow_close):
            raise CheckError("--allow-close takes an exact issue reference, such as '#123'")
        root = Path(args.root).resolve() if args.root is not None else repo_root()
        report = check(root, args.base, args.head, set(args.allow_close))
    except NotApplicable as exc:
        report = {"status": "not-applicable", "reason": str(exc), "limits": LIMITS}
    except (CheckError, ImportError, KeyError, OSError, UnicodeError, ValueError) as exc:
        report = {"status": "unavailable", "error": str(exc), "limits": LIMITS}
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(f"Record preflight: {report['status']}")
        if "error" in report:
            print(report["error"])
        if "reason" in report:
            print(report["reason"])
        for item in [*report.get("findings", []), *report.get("unavailable", [])]:
            print(f"{item['source']}:{item['line']}: {item['check']}: {item['detail']}")
        for stamp in report.get("stamps", []):
            print(f"{stamp['source']}:{stamp['line']}: stamp {stamp['revision']} (names candidate head: {stamp['names_head']})")
        for limit in LIMITS:
            print(f"Limit: {limit}")
    return {"passed": 0, "not-applicable": 0, "failed": 1, "unavailable": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
