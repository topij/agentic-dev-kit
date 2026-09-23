"""Shared fixtures for the systemize engine tests (collected, but holds no tests).

``make_repo`` builds a throwaway git repository carrying the shipped config and
the real engine set, so every test runs the installed layout rather than the kit
checkout. ``FAKE_GH`` is a stand-in ``gh`` that serves paged GraphQL from a JSON
fixture; it runs as a real subprocess both on ``PATH`` and behind the in-process
runner, so pagination is exercised through the same argv the engines emit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
sys.path.insert(0, str(ENGINE_DIR / "lib"))

ENGINES = ("fetch_merged_prs.py", "digest_merged_prs.py", "heartbeat_cli.py")
LIB_FILES = ("kitconfig.py", "triage/__init__.py", "triage/canonical.py")
LIB_DIRS = ("state_paths", "systemize")
HEAD = "a" * 40
DATE = "2026-09-23"

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys

fixture = json.load(open(os.environ["FAKE_GH_FIXTURE"]))
args = sys.argv[1:]
log = os.environ.get("FAKE_GH_LOG")
if log:
    with open(log, "a") as stream:
        stream.write(json.dumps(args) + "\n")


def out(value):
    print(json.dumps(value))
    sys.exit(0)


def page(items, cursor, op):
    size = fixture.get("page_size", 2)
    start = int(cursor) if cursor else 0
    chunk = items[start:start + size]
    more = start + size < len(items)
    fault = fixture.get("fault", {})
    if fault.get("op") == op:
        if fault.get("kind") == "error":
            sys.stderr.write("HTTP 502: fake failure\n")
            sys.exit(1)
        if fault.get("kind") == "no_pageinfo":
            return {"nodes": chunk}
        if fault.get("kind") == "no_cursor" and more:
            return {"pageInfo": {"hasNextPage": True, "endCursor": None}, "nodes": chunk}
    return {"pageInfo": {"hasNextPage": more, "endCursor": str(start + size) if more else None}, "nodes": chunk}


if args[:2] == ["repo", "view"]:
    out({"nameWithOwner": fixture["repo"]})
if args[0] == "api" and args[1].startswith("repos/") and "/branches/" in args[1]:
    if fixture.get("fault", {}).get("op") == "branch":
        sys.stderr.write("HTTP 404: Branch not found\n")
        sys.exit(1)
    out({"commit": {"sha": fixture["head"]}})
if args[:2] != ["api", "graphql"]:
    sys.stderr.write("fake gh: unsupported " + " ".join(args) + "\n")
    sys.exit(2)

variables = {}
query = ""
rest = args[2:]
for flag, value in zip(rest[::2], rest[1::2]):
    key, _, text = value.partition("=")
    if key == "query":
        query = text
    else:
        variables[key] = int(text) if flag == "-F" else text
op = query.split()[1].split("(")[0]
cursor = variables.get("cursor")
prs = fixture["prs"]
if op == "MergedPRs":
    ordered = sorted(prs, key=lambda p: p["updatedAt"], reverse=True)
    nodes = [{k: v for k, v in p.items() if k in (
        "number", "title", "url", "body", "mergedAt", "updatedAt", "baseRefName", "author", "mergeCommit")}
        for p in ordered]
    out({"data": {"repository": {"pullRequests": page(nodes, cursor, op)}}})
if op == "ThreadComments":
    for pr in prs:
        for thread in pr.get("reviewThreads", []):
            if thread["id"] == variables["id"]:
                out({"data": {"node": {"comments": page(thread["comments"], cursor, op)}}})
    sys.exit(3)
connection = op[len("PR_"):]
pr = next(p for p in prs if p["number"] == variables["number"])
items = pr.get(connection, [])
if connection == "reviewThreads":
    items = [{**t, "comments": page(t["comments"], None, "embedded")} for t in items]
out({"data": {"repository": {"pullRequest": {connection: page(items, cursor, op)}}}})
'''


def make_repo(tmp_path: Path, *, engines: tuple[str, ...] = ENGINES, config_edit=None) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    text = (REPO_ROOT / "config/dev-model.yaml").read_text(encoding="utf-8")
    if config_edit is not None:
        text = config_edit(text)
    (root / "config/dev-model.yaml").write_text(text, encoding="utf-8")
    scripts = root / "scripts"
    for name in LIB_FILES:
        (scripts / "lib" / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ENGINE_DIR / "lib" / name, scripts / "lib" / name)
    for name in LIB_DIRS:
        shutil.copytree(ENGINE_DIR / "lib" / name, scripts / "lib" / name,
                        ignore=shutil.ignore_patterns("__pycache__", "tests"))
    for name in engines:
        shutil.copy2(ENGINE_DIR / name, scripts / name)
    (root / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"],
        check=True,
    )
    return root


def comment(cid: int, login: str, body: str) -> dict[str, Any]:
    return {"databaseId": cid, "author": {"login": login}, "body": body,
            "url": f"https://example.test/c/{cid}", "createdAt": "2026-09-20T10:00:00Z"}


def pr(number: int, merged: str, *, threads=(), reviews=(), updated: str | None = None,
       body: str = "", closing=()) -> dict[str, Any]:
    return {
        "number": number, "title": f"PR {number}", "url": f"https://example.test/pull/{number}",
        "body": body, "mergedAt": merged, "updatedAt": updated or merged, "baseRefName": "main",
        "author": {"login": "someone"}, "mergeCommit": {"oid": f"{number:040x}"},
        "reviews": [{**r, "state": "COMMENTED", "submittedAt": "2026-09-20T10:00:00Z"} for r in reviews],
        "reviewThreads": list(threads), "comments": [], "files": [{"path": "scripts/x.py"}],
        "closingIssuesReferences": list(closing),
    }


def thread(tid: str, comments, *, resolved=False, outdated=False, path="scripts/x.py") -> dict[str, Any]:
    return {"id": tid, "isResolved": resolved, "isOutdated": outdated, "path": path, "line": 3,
            "comments": list(comments)}


def fake_env(tmp_path: Path, fixture: dict[str, Any], root: Path, state: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(FAKE_GH.replace("#!/usr/bin/env python3", f"#!{sys.executable}"), encoding="utf-8")
    gh.chmod(0o755)
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps({"repo": "o/r", "head": HEAD, **fixture}), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("DEVKIT_")}
    env.update(PATH=f"{bin_dir}{os.pathsep}{env.get('PATH', '')}", FAKE_GH_FIXTURE=str(fixture_path),
               FAKE_GH_LOG=str(tmp_path / "gh.log"), DEVKIT_STATE_ROOT=str(state), DEVKIT_ROOT=str(root))
    return env


def run_engine(root: Path, name: str, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(root / "scripts" / name), *args], cwd=root, env=env,
                          capture_output=True, text=True, check=False)


def run_args(mode: str = "test", window: int = 7, date: str = DATE) -> list[str]:
    return ["--mode", mode, "--window-days", str(window), "--date", date]
