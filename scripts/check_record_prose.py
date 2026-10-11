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
import io
import json
import os
import posixpath
import re
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

# The generated invocation must stay read-only even in a fresh handed tree.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, loads, repo_root  # noqa: E402

NARRATIVE_KEYS = ("handoff", "handoff_history", "friction_log", "friction_log_archive")
LIMITS = [
    "Only destinations parsed as CommonMark links or images are checked; unresolved reference text is not a parsed link.",
    "Links and stamps are checked in changed Markdown blocks, including newly active blocks after deletions; a changed reference definition also rechecks document links.",
    "External URLs, fragment identifiers, and raw HTML destinations are not verified.",
    "A stamp's commit and date can be checked; its command's execution and claimed result cannot.",
    "A historical stamp need not name the candidate head; the reviewer must judge its stated scope.",
    "Stamp fields use code spans and the connectors at, optional in, and on; raw HTML and unrelated connector wording are outside this scan.",
    "Closing keywords pair conservatively with the next issue reference across intervening text and markup; declare each intended reference exactly.",
    "Every changed narrative file and commit message remains in full independent-review scope.",
]
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
# The archived heading/list incident paired a negated keyword with a reference
# across markup. Tokenize raw text and pair each keyword with the next reference,
# rather than guessing which separators the forge permits. References are whole
# tokens so a repository name containing a keyword cannot become that keyword.
_CLOSING_TOKEN = re.compile(
    r"(?P<ref>https://github\.com/[\w.-]+/[\w.-]+/issues/\d+|"
    r"(?:[\w.-]+/[\w.-]+)?#\d+)\b|"
    r"\b(?P<keyword>close[sd]?|closing|fix(?:es|ed|ing)?|resolve[sd]?|resolving)\b",
    re.IGNORECASE,
)


class CheckError(Exception):
    """A read could not establish the required input."""


class NotApplicable(CheckError):
    """The comparison is outside the declared narrative-path scope."""


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "--literal-pathspecs", *args],
            cwd=root, capture_output=True, timeout=30, check=False,
            # Replacement refs and grafts rewrite object/history reads without
            # changing the named SHA. Keep every read on the stored objects.
            env={**os.environ, "GIT_GRAFT_FILE": os.devnull},
        )
        output = result.stdout.decode("utf-8")
        error = result.stderr.decode("utf-8")
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise CheckError(str(exc)) from exc
    if result.returncode:
        raise CheckError(error.strip() or f"git {args[0]} failed")
    return output


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
    paths = git(root, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--name-only", "-z", "--no-renames", boundary, head).split("\0")
    changed = [p for p in paths if p]
    if not changed or not set(changed) <= declared:
        raise NotApplicable("the change is not confined to the configured narrative paths")
    return config, boundary, changed


def markdown_lines(text: str) -> list[str]:
    """Use text-stream newlines, as check_doc_budget and CommonMark do."""
    return list(io.StringIO(text, newline=None))


def changed_lines(root: Path, boundary: str, head: str, path: str,
                  text: str, before: str) -> tuple[set[int], dict[int, int], set[int]]:
    patch = git(root, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames",
                "--text", "--unified=0", boundary, head, "--", path)

    def records(value):
        physical = list(io.StringIO(value))
        spans, gaps = {}, {0: 0}
        cursor, offset = 1, 0
        for number, record in enumerate(physical, 1):
            logical = markdown_lines(record)
            spans[number] = range(cursor, cursor + len(logical))
            cursor += len(logical)
            offset += len("".join(logical))
            gaps[number] = offset
        return physical, spans, gaps

    old_records, old_spans, _ = records(before)
    new_records, new_spans, gaps = records(text)
    added, unchanged, deleted = set(), {}, set()
    old_cursor, new_cursor = 1, 1

    def preserve(old_end, new_end):
        for old, new in zip(range(old_cursor, old_end), range(new_cursor, new_end), strict=True):
            if old_records[old - 1] != new_records[new - 1]:
                raise CheckError("Git did not establish unchanged text coordinates")
            unchanged.update(zip(new_spans[new], old_spans[old], strict=True))

    # Git counts LF records; translate their exact correspondence to Markdown
    # lines and deletion cutpoints without matching equal text at other positions.
    for line in patch.split("\n"):
        match = _HUNK.match(line)
        if match:
            old_start, new_start = int(match[1]), int(match[3])
            old_count = int(match[2]) if match[2] is not None else 1
            new_count = int(match[4]) if match[4] is not None else 1
            preserve(old_start if old_count else old_start + 1,
                     new_start if new_count else new_start + 1)
            for number in range(new_start, new_start + new_count):
                added.update(new_spans[number])
            if old_count and not new_count:
                deleted.add(gaps[new_start])
            old_cursor = old_start + old_count if old_count else old_start + 1
            new_cursor = new_start + new_count if new_count else new_start + 1
    preserve(len(old_records) + 1, len(new_records) + 1)
    return added, unchanged, deleted


def changed_blocks(before: list, after: list, unchanged: dict[int, int]) -> set[int]:
    """Select candidate blocks whose parsed meaning changed, without line shifts."""
    def signature(token):
        return (token.type, token.tag, token.nesting, token.content,
                tuple((child.type, child.attrGet("href"), child.attrGet("src"))
                      for child in token.children or []))

    original = {(tuple(range(token.map[0] + 1, token.map[1] + 1)), signature(token))
                for token in before if token.map}
    affected: set[int] = set()
    for token in after:
        if not token.map:
            continue
        lines = range(token.map[0] + 1, token.map[1] + 1)
        prior = tuple(unchanged.get(line) for line in lines)
        if (prior, signature(token)) not in original:
            affected.update(lines)
    return affected


def verification_stamps(children: list):
    """Recognize stamp fields from CommonMark code spans, not raw delimiters."""
    def separator(char):
        return char.isspace() or unicodedata.category(char).startswith("P")

    def is_connector(text, word):
        visible = "".join(" " if separator(char) else char for char in text)
        return visible.casefold().split() == [word]

    def date_after_on(text):
        match = re.search(r"\bon\b", text, re.IGNORECASE)
        if not match or not all(separator(char) for char in text[:match.start()]):
            return None
        remainder = text[match.end():]
        position = 0
        while position < len(remainder) and separator(remainder[position]):
            position += 1
        return remainder[position:]

    parts = []
    for child in children:
        # Emphasis and links change presentation rather than visible field text.
        # Keep code spans distinct so enclosing inline examples cannot be claims.
        if child.nesting:
            continue
        kind = child.type
        content = child.content
        if kind in ("softbreak", "hardbreak"):
            kind, content = "text", "\n"
        if kind == "text" and parts and parts[-1][0] == "text":
            parts[-1] = (kind, parts[-1][1] + content)
        else:
            parts.append((kind, content))

    for index, (kind, command) in enumerate(parts):
        if kind != "code_inline" or not command or index + 3 >= len(parts):
            continue
        connector, revision, date_text = parts[index + 1:index + 4]
        if (connector[0] != "text" or not is_connector(connector[1], "at")
                or revision[0] != "code_inline" or date_text[0] != "text"):
            continue
        date_index = index + 3
        if is_connector(date_text[1], "in"):
            if index + 5 >= len(parts) or parts[index + 4][0] != "code_inline":
                continue
            date_index = index + 5
            date_text = parts[index + 5]
            if date_text[0] != "text":
                continue
        date = date_after_on(date_text[1])
        if date is None:
            continue
        if not date and date_index + 1 < len(parts) and parts[date_index + 1][0] == "code_inline":
            date = parts[date_index + 1][1]
        else:
            match = re.match(r"\S+", date)
            # Only trailing sentence punctuation and closing delimiters are
            # separators. Punctuation inside a token cannot hide a suffix;
            # slash, hyphen and underscore remain part of the date spelling.
            date = match[0].rstrip(".,;:!?…—)]}\"'»”’") if match else ""
        if date:
            yield {"command": command, "sha": revision[1], "date": date}


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

    def closings(text: str, source: str, added: set[int] | None = None,
                 deleted: set[int] | None = None) -> None:
        pending = []
        for token in _CLOSING_TOKEN.finditer(text):
            if token["keyword"]:
                pending.append(token)
                continue
            ref = token["ref"]
            for keyword in pending:
                line = text.count("\n", 0, keyword.start()) + 1
                end = text.count("\n", 0, token.end()) + 1
                if (added is not None and not added.intersection(range(line, end + 1))
                        and not any(keyword.start() < cut < token.end() for cut in deleted or ())):
                    continue
                if ref not in allowed:
                    finding("closing-keywords", source, line,
                            f"closing reference {ref}: explicitly declare --allow-close {ref} only if intended")
            pending.clear()

    budgets = get(config, "doc_budgets", None)
    if not isinstance(budgets, list) or not budgets:
        raise CheckError("doc_budgets is absent or malformed in the base config")
    for entry in budgets:
        if not isinstance(entry, dict) or not isinstance(entry.get("budget"), int) or isinstance(entry.get("budget"), bool) or entry["budget"] < 0:
            raise CheckError("a doc_budgets entry is malformed")
        path = path_value(entry.get("path"))
        if path in paths:
            text = blob(root, head, path)
            if len(markdown_lines(text)) > entry["budget"]:
                finding("budgets", path, 1, "candidate exceeds its configured line budget")

    parser = MarkdownIt("commonmark")
    for path in paths:
        # A deleted archive has no added blocks. Required budgeted inputs above
        # still must exist; deletion remains in the full review's diff.
        if not git(root, "ls-tree", "-z", head, "--", path):
            continue
        raw = blob(root, head, path)
        lines = markdown_lines(raw)
        text = "".join(lines)
        # Parse the entire document so reference definitions and code fences keep
        # their CommonMark meaning; select changed blocks only after parsing.
        environment: dict = {}
        tokens = parser.parse(text, environment)
        old = blob(root, boundary, path) if git(root, "ls-tree", "-z", boundary, "--", path) else ""
        before = "".join(markdown_lines(old))
        added, unchanged, deleted = changed_lines(root, boundary, head, path, raw, old)
        old_environment: dict = {}
        old_tokens = parser.parse(before, old_environment)
        affected = added | changed_blocks(old_tokens, tokens, unchanged)
        closings(text, path, added, deleted)

        def references(env):
            return {label: (ref.get("href"), ref.get("title"))
                    for label, ref in env.get("references", {}).items()}

        changed_reference = references(old_environment) != references(environment) or any(
            affected.intersection(range(ref["map"][0] + 1, ref["map"][1] + 1))
            for ref in environment.get("references", {}).values() if "map" in ref
        )
        for token in tokens:
            if not token.map:
                continue
            start, end = token.map
            touched = bool(affected.intersection(range(start + 1, end + 1)))
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
            # Code-span contents already have CommonMark's newline and padding
            # normalization. Their containing block supplies the source line,
            # as it does for parsed links; nested code examples stay literal.
            for match in verification_stamps(token.children or []):
                line = start + 1
                if not re.fullmatch(r"[0-9a-fA-F]{7,40}", match["sha"]):
                    finding("stamps", path, line, "verification stamp names a moving or invalid revision")
                    continue
                try:
                    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", match["date"]):
                        raise ValueError("stamp dates use YYYY-MM-DD")
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
        report = {"status": "unavailable", "error": str(exc), "limits": LIMITS,
                  "unavailable": [{"check": "input", "source": "input", "line": 0,
                                   "detail": str(exc)}]}
    report = {"findings": [], "unavailable": [], "stamps": [], **report}
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(f"Record preflight: {report['status']}")
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
