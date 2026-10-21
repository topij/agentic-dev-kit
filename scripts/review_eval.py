#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Score the fallback panel's lenses against a case set of known review misses (#1156).

The kit changes its reviewer often — a lens's ``focus``, ``lens_compute``'s model and
effort, ``panel_prompt.py`` — and had no way to tell whether a change made review
better or worse. This runs every lens over every case in
``docs/agentic-dev-kit/review-eval/cases.yaml`` and reports, per lens, how many bug
cases it caught and how many findings it raised on the clean ones.

For each case and lens it allocates a review round with ``sweep_scratch.py``, builds a
detached tree at the case head, renders the lens prompt with ``panel_prompt.py`` (the
same prompt a real round gets, with ``--preflight-rev`` set to this checkout's
``HEAD``, because a historical head predates the preflight checker), runs
``--lens-command`` in that tree with the prompt on stdin, keeps its stdout as the
report, and retires the round.

**The lens command is what applies the compute**, exactly as in a real round: the
prompt's ``Run at:`` line only restates it. The command is recorded verbatim in the
result, so a score always names what produced it. Tests pass a stub, so ``make test``
never calls a model.

**A hit is a citation, not a judgment.** A bug case counts as caught when the report
cites ``path:line`` (or ``path:start-end``) overlapping one of the case's known
findings. That is a proxy: a report can cite the right lines for the wrong reason, or
describe the bug without a citation. The result keeps every matched citation, and a
clean case's findings are candidate false alarms, so the operator reads both before a
score is recorded.

Exit 0 prints the result JSON (and writes it with ``--out``); exit 1 is a case that
could not be run; exit 2 is a rejected invocation or case file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR / "lib"))

sys.path.insert(0, str(ENGINE_DIR))

import sweep_scratch  # noqa: E402
from kitconfig import load_config  # noqa: E402

CASES = Path("docs/agentic-dev-kit/review-eval/cases.yaml")
CASES_SCHEMA = "review-eval-cases-v1"
RESULT_SCHEMA = "review-eval-result-v1"
RUNTIMES = ("claude", "codex")
_SHA = re.compile(r"[0-9a-f]{40}")
_CASE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
# `path:line` or `path:start-end`, the citation form the lens contract asks for.
_CITATION = re.compile(r"(?<![\w./-])((?:[\w.-]+/)*[\w.-]+\.\w+):(\d+)(?:[-–](\d+))?")
_FINDING_NUMBER = re.compile(r"\bF(\d+)\b")


class EvalError(Exception):
    """A case or invocation the runner refuses (exit 2)."""


class RunError(Exception):
    """A case that could not be run (exit 1)."""


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RunError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _commit_exists(root: Path, sha: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=root, capture_output=True, check=False
    ).returncode == 0


def _lines(value: Any, where: str) -> tuple[int, int]:
    if (not isinstance(value, list) or len(value) != 2
            or not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in value)
            or value[0] > value[1]):
        raise EvalError(f"{where}: lines must be [start, end] with 0 < start <= end")
    return value[0], value[1]


def load_cases(path: Path, root: Path) -> dict[str, list[dict[str, Any]]]:
    """Read and validate the case file; every sha must name a commit in ``root``."""
    try:
        data = load_config(path)
    except (OSError, ValueError) as exc:
        raise EvalError(f"{path}: unreadable case file: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != CASES_SCHEMA:
        raise EvalError(f"{path}: schema must be {CASES_SCHEMA}")
    seen: set[str] = set()
    cases: dict[str, list[dict[str, Any]]] = {}
    for kind in ("bug_cases", "clean_cases"):
        entries = data.get(kind)
        if not isinstance(entries, list):
            raise EvalError(f"{path}: {kind} must be a list")
        cases[kind] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise EvalError(f"{path}: every {kind} entry must be a mapping")
            case_id = entry.get("id")
            if not isinstance(case_id, str) or not _CASE_ID.fullmatch(case_id) or case_id in seen:
                raise EvalError(f"{path}: case id {case_id!r} must be unique lower-case [a-z0-9-]")
            seen.add(case_id)
            where = f"{path}: {case_id}"
            for key in ("base", "head"):
                sha = entry.get(key)
                if not isinstance(sha, str) or not _SHA.fullmatch(sha):
                    raise EvalError(f"{where}: {key} must be a full 40-hex sha")
                if not _commit_exists(root, sha):
                    raise EvalError(f"{where}: {key} {sha} is not a commit in {root}; fetch full history")
            if entry["base"] == entry["head"]:
                raise EvalError(f"{where}: base and head are the same commit")
            confirmed = entry.get("confirmed", "")
            if not isinstance(confirmed, str):
                raise EvalError(f"{where}: confirmed must be a string")
            case = {"id": case_id, "base": entry["base"], "head": entry["head"],
                    "source": entry.get("source"), "confirmed": bool(confirmed.strip())}
            if kind == "bug_cases":
                findings = entry.get("findings")
                if not isinstance(findings, list) or not findings:
                    raise EvalError(f"{where}: a bug case needs at least one finding")
                case["findings"] = []
                for finding in findings:
                    if not isinstance(finding, dict) or not isinstance(finding.get("path"), str):
                        raise EvalError(f"{where}: every finding needs a path")
                    start, end = _lines(finding.get("lines"), where)
                    case["findings"].append({"path": finding["path"], "lines": [start, end]})
            cases[kind].append(case)
    if not cases["bug_cases"]:
        raise EvalError(f"{path}: the case set has no bug case")
    return cases


def citations(report: str) -> list[dict[str, Any]]:
    found = []
    for match in _CITATION.finditer(report):
        start = int(match.group(2))
        end = int(match.group(3)) if match.group(3) else start
        found.append({"path": match.group(1), "lines": [start, max(start, end)]})
    return found


def _same_path(cited: str, known: str) -> bool:
    return cited == known or cited.endswith("/" + known) or known.endswith("/" + cited)


def score_bug(report: str, case: dict[str, Any]) -> dict[str, Any]:
    matched = []
    for cited in citations(report):
        for index, known in enumerate(case["findings"]):
            if (_same_path(cited["path"], known["path"])
                    and cited["lines"][0] <= known["lines"][1] and known["lines"][0] <= cited["lines"][1]):
                matched.append({"finding": index, **cited})
    return {"hit": bool(matched), "matched_citations": matched}


def score_clean(report: str) -> dict[str, Any]:
    numbers = sorted({int(n) for n in _FINDING_NUMBER.findall(report)})
    return {"candidate_false_alarms": len(numbers), "citations": citations(report)}


def _run_engine(name: str, args: list[str], root: Path) -> str:
    proc = subprocess.run([sys.executable, str(ENGINE_DIR / name), *args],
                          cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RunError(f"{name} {' '.join(args[:2])} failed: {proc.stderr.strip()[:500]}")
    return proc.stdout


def run_case(root: Path, case: dict[str, Any], lens: str, *, runtime: str, command: list[str],
             scratch_root: str, kit_rev: str, work: Path, timeout: int) -> str:
    """One lens over one case; returns the report. The round is retired either way.

    The round goes through ``sweep_scratch``'s own allocation and retirement, as a
    real round does, with the allocation receipt kept outside the round.
    """
    try:
        settings = sweep_scratch.load_settings(root / "config" / "dev-model.yaml", root=root)
        record = sweep_scratch.create_review_round(scratch_root, case["head"], settings, root)
    except (sweep_scratch.ConfigError, OSError, ValueError) as exc:
        raise RunError(f"{case['id']} {lens}: cannot allocate a review round: {exc}") from exc
    (work / f"{case['id']}-{lens}.round.json").write_text(json.dumps(record, sort_keys=True))
    tree = Path(record["path"]) / f"lens-{lens}-{case['head'][:7]}"
    try:
        _git(root, "worktree", "add", "-q", "--detach", str(tree), case["head"])
        prompt = _run_engine("panel_prompt.py", [
            "--root", str(root), "--lens", lens, "--head", case["head"], "--base", case["base"],
            "--branch", f"review-eval/{case['id']}", "--scratch", str(tree), "--runtime", runtime,
            "--preflight-rev", kit_rev,
        ], root)
        try:
            proc = subprocess.run(command, cwd=tree, input=prompt, capture_output=True,
                                  text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RunError(f"{case['id']} {lens}: lens command timed out after {timeout}s") from exc
        except OSError as exc:
            raise RunError(f"{case['id']} {lens}: cannot run lens command: {exc}") from exc
        if proc.returncode != 0:
            raise RunError(f"{case['id']} {lens}: lens command exited {proc.returncode}: "
                           f"{proc.stderr.strip()[:500]}")
        return proc.stdout
    finally:
        if tree.exists():
            _git(root, "worktree", "remove", "--force", str(tree))
        try:
            outcome = sweep_scratch.finish_review_round(record, settings, root, apply=True,
                                                        reviewers_finished=True)
        except (sweep_scratch.ConfigError, sweep_scratch.Refused, OSError, ValueError) as exc:
            raise RunError(f"{case['id']} {lens}: review round not retired: {exc}") from exc
        if outcome.action == "kept":
            raise RunError(f"{case['id']} {lens}: review round kept at {outcome.path}: {outcome.reason}")


def summarize(results: list[dict[str, Any]], lenses: list[str]) -> dict[str, Any]:
    summary = {}
    for lens in lenses:
        mine = [r for r in results if r["lens"] == lens]
        bugs = [r for r in mine if r["kind"] == "bug"]
        clean = [r for r in mine if r["kind"] == "clean"]
        summary[lens] = {
            "confirmed_bug_cases": sum(1 for r in bugs if r["confirmed"]),
            "confirmed_hits": sum(1 for r in bugs if r["confirmed"] and r["hit"]),
            "unconfirmed_bug_cases": sum(1 for r in bugs if not r["confirmed"]),
            "unconfirmed_hits": sum(1 for r in bugs if not r["confirmed"] and r["hit"]),
            "clean_cases": len(clean),
            "candidate_false_alarms": sum(r["candidate_false_alarms"] for r in clean),
        }
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=None, help="the kit checkout holding the case history (default: this one)")
    parser.add_argument("--cases", default=None, help=f"case file (default: <root>/{CASES})")
    parser.add_argument("--runtime", required=True, choices=RUNTIMES,
                        help="the runtime the lens command runs under; the score is per runtime")
    parser.add_argument("--lens-command", required=True,
                        help="shell-quoted command run in the lens tree with the prompt on stdin; "
                        "its stdout is the report, and it applies the compute")
    parser.add_argument("--scratch-root", required=True,
                        help="an expanded scratch.roots entry to allocate review rounds under")
    parser.add_argument("--lens", action="append", default=None,
                        help="score only this lens (repeatable; default: every configured lens)")
    parser.add_argument("--case", action="append", default=None,
                        help="score only this case id (repeatable; default: all)")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per lens run (default 1800)")
    parser.add_argument("--out", default=None, help="directory for the reports and result.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.root).resolve() if args.root else ENGINE_DIR.parent
        command = shlex.split(args.lens_command)
        if not command:
            raise EvalError("--lens-command is empty")
        if args.timeout < 1:
            raise EvalError("--timeout must be positive")
        cases_path = Path(args.cases) if args.cases else root / CASES
        cases = load_cases(cases_path, root)
        config = load_config(root / "config" / "dev-model.yaml")
        roster = [lens.get("name") for lens in
                  (((config.get("review") or {}).get("fallback_panel") or {}).get("lenses") or [])
                  if isinstance(lens, dict) and isinstance(lens.get("name"), str)]
        lenses = args.lens or roster
        unknown = sorted(set(lenses) - set(roster))
        if not lenses or unknown:
            raise EvalError(f"lens(es) not in review.fallback_panel.lenses: {', '.join(unknown) or '(none configured)'}")
        selected = [("bug", c) for c in cases["bug_cases"]] + [("clean", c) for c in cases["clean_cases"]]
        if args.case:
            missing = sorted(set(args.case) - {c["id"] for _, c in selected})
            if missing:
                raise EvalError(f"no such case: {', '.join(missing)}")
            selected = [(k, c) for k, c in selected if c["id"] in args.case]
    except EvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = Path(args.out).resolve() if args.out else None
    work = out or Path(_git(root, "rev-parse", "--absolute-git-dir")) / "review-eval"
    work.mkdir(parents=True, exist_ok=True)
    kit_rev = _git(root, "rev-parse", "HEAD")
    results = []
    try:
        for kind, case in selected:
            for lens in lenses:
                report = run_case(root, case, lens, runtime=args.runtime, command=command,
                                  scratch_root=args.scratch_root, kit_rev=kit_rev, work=work,
                                  timeout=args.timeout)
                if out is not None:
                    (out / f"{case['id']}-{lens}.md").write_text(report)
                entry = {"case": case["id"], "kind": kind, "lens": lens,
                         "source": case["source"], "confirmed": case["confirmed"]}
                entry.update(score_bug(report, case) if kind == "bug" else score_clean(report))
                results.append(entry)
    except RunError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = {
        "schema": RESULT_SCHEMA,
        "runtime": args.runtime,
        "lens_command": args.lens_command,
        "kit_revision": kit_rev,
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "summary": summarize(results, lenses),
        "results": results,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out is not None:
        (out / "result.json").write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
