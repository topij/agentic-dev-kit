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
repository there holding only the case's own history, detached at the case head (so the
fix commits and this case file are not reachable from it), renders the lens prompt with ``panel_prompt.py`` (the
same prompt a real round gets, with ``--preflight-rev`` set to this checkout's
``HEAD``, because a historical head predates the preflight checker), runs
``--lens-command`` in that tree with the prompt on stdin, keeps its stdout as the
report, and retires the round.

**The lens command is what applies the compute**, exactly as in a real round: the
prompt's ``Run at:`` line only restates it. The command is recorded verbatim in the
result, so a score always names what produced it. Tests pass a stub, so ``make test``
never calls a model.

**A hit is a citation, not a judgment.** A bug case counts as caught when the report
cites ``path:line`` (or ``path:start-end``, at most ``HIT_SPAN`` lines wide) overlapping
one of the case's known findings. That is a proxy: a report can cite the right lines for the wrong reason, or
describe the bug without a citation. The result keeps every matched citation, and a
clean case's findings are candidate false alarms, so the operator reads both before a
score is recorded.

Exit 0 prints the result JSON (and writes it with ``--out``); exit 1 is a case that
could not be run, and ``--out`` then holds the partial result, ``complete: false``;
exit 2 is a rejected invocation, case file, or a kit checkout with uncommitted changes.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
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
_CITATION = re.compile(r"(?<![\w./-])((?:[\w.-]+/)*[\w.-]+\.\w+):[ ]?L?(\d+)(?:[-–]L?(\d+))?")
# A finding opens its own line: `F3 HIGH`, `**F3.`, `### F3 —`, `- F3:`, `1. **F3**`.
_FINDING_NUMBER = re.compile(r"^[ \t#>*_-]*(?:\d{1,3}[.)][ \t]+[*_]*)?F(\d+)\b", re.MULTILINE)
# The lens contract's own sections cite what was checked, not what is wrong. A
# heading names one when its title opens with that name as a word; a bold lead-in
# followed by more text names one only when the label is that name, with at most an
# `and ...` tail, a parenthetical and a colon, so `**Executed path skips guard** a.py:2`
# is a finding. A title opening with `F<n>` is a finding either way.
_SECTION_NAMES = (r"(?:verified clean|what i (?:reviewed|executed|checked)|execut(?:ed|ion)|attestation|"
                  r"scratch attestation|mutation(?:[ -]testing)?|earlier dispositions|disposition check|"
                  r"routes|reviewed)")
_SECTION_HEADING = re.compile(rf"[*_ ]*{_SECTION_NAMES}\b", re.IGNORECASE)
_SECTION_LABEL = re.compile(rf"{_SECTION_NAMES}(?:[ \t]+and[ \t]+[\w ]+)?(?:[ \t]*\([^)]*\))?[ \t]*[:.]?",
                            re.IGNORECASE)
# A heading is an ATX heading or a line that is bold from end to end; a bold label
# may sit after a list or quote marker. A bold lead-in followed by more text is body.
_LEAD = r"[ ]{0,3}(?:[-*+>][ \t]+|\d{1,3}[.)][ \t]+)?(?P<mark>\*\*|__)(?P<bold>.+?)(?P=mark)"
_ATX = re.compile(r"[ ]{0,3}#{1,6}(?:[ \t]+(?P<atx>.*))?")
_BOLD_LINE = re.compile(rf"{_LEAD}[:]?")
_BOLD_LEAD = re.compile(_LEAD)
_REPO_LINE = re.compile(r"^(- \*\*Repo:\*\* ).*$", re.MULTILINE)
_FENCE = re.compile(r"[ ]{0,3}(`{3,}|~{3,})")
# The widest citation that still counts as a hit: wider is a file, not a finding.
HIT_SPAN = 40
# What the lens sees as the branch: the same for every case, so the name says
# nothing about the case or its kind.
BRANCH = "review-eval/case"


class EvalError(Exception):
    """A case or invocation the runner refuses (exit 2)."""


class RunError(Exception):
    """A case that could not be run (exit 1)."""


class LensEscaped(Exception):
    """A process the lens started left its group and still holds the lens's output."""


# How long the runner waits for the lens's output to close once its group is killed.
DRAIN_SECONDS = 10


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


def findings_text(report: str) -> str:
    """``report`` without what the lens records having checked.

    A heading that names one of the contract's report sections drops the lines after
    it until the next heading or the next paragraph that opens with a numbered
    finding; a bold lead-in that names one (``**Executed:** ran it``) drops only its
    own line. A cited line the lens cleared is then neither a hit nor a false alarm,
    and a finding listed after such a section without a heading of its own is kept.
    Fenced code is never a heading.
    """
    kept, cut, fence, blank = [], False, None, True
    for line in report.splitlines(keepends=True):
        text = line.rstrip("\r\n")
        drop = False
        if fence is not None:
            closer = _FENCE.match(text)
            if closer and closer.group(1)[0] == fence[0] and len(closer.group(1)) >= len(fence) \
                    and not text[closer.end():].strip():
                fence = None
        elif (opener := _FENCE.match(text)) is not None:
            fence = opener.group(1)
        elif (heading := _ATX.fullmatch(text) or _BOLD_LINE.fullmatch(text.rstrip())) is not None:
            title = heading.group("atx") if "atx" in heading.re.groupindex else heading.group("bold")
            cut = bool(_SECTION_HEADING.match(title or "")) and not re.match(r"[*_ ]*F\d+\b", title)
        elif (lead := _BOLD_LEAD.match(text)) is not None and _SECTION_LABEL.fullmatch(lead.group("bold").strip()):
            drop = True
        elif blank and _FINDING_NUMBER.match(text):
            cut = False
        blank = fence is None and not text.strip()
        if not (cut or drop):
            kept.append(line)
    return "".join(kept)


def citations(report: str) -> list[dict[str, Any]]:
    found = []
    for match in _CITATION.finditer(findings_text(report)):
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
            if (cited["lines"][1] - cited["lines"][0] < HIT_SPAN
                    and _same_path(cited["path"], known["path"])
                    and cited["lines"][0] <= known["lines"][1] and known["lines"][0] <= cited["lines"][1]):
                matched.append({"finding": index, **cited})
    return {"hit": bool(matched), "matched_citations": matched}


def score_clean(report: str) -> dict[str, Any]:
    """A clean case's findings: its ``F<n>`` numbers, or, in a report that numbers
    none, each distinct citation, so an unnumbered report is not read as silent."""
    numbers = {int(n) for n in _FINDING_NUMBER.findall(findings_text(report))}
    cited = citations(report)
    count = len(numbers) or len({(c["path"], *c["lines"]) for c in cited})
    return {"candidate_false_alarms": count, "citations": cited}


def _run_engine(name: str, args: list[str], root: Path) -> str:
    proc = subprocess.run([sys.executable, str(ENGINE_DIR / name), *args],
                          cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RunError(f"{name} {' '.join(args[:2])} failed: {proc.stderr.strip()[:500]}")
    return proc.stdout


def _isolated_tree(root: Path, tree: Path, case: dict[str, Any], kit_rev: str) -> None:
    """A fresh repository at ``tree`` holding only the case's base and head history.

    A linked worktree would share ``root``'s refs and objects, and with them the fix
    commits, this case file and the issue references a lens could search for the
    answer. Only the two shas are fetched, so nothing later than the case head is
    reachable. The preflight checker's two blobs at ``kit_rev`` are written in by
    content, unreferenced, because the prompt pins them there.
    """
    tree.mkdir()
    _git(tree, "init", "-q")
    _git(tree, "fetch", "-q", "--no-tags", "--upload-pack",
         "git -c uploadpack.allowAnySHA1InWant=true upload-pack", str(root), case["base"], case["head"])
    (Path(_git(tree, "rev-parse", "--absolute-git-dir")) / "FETCH_HEAD").unlink(missing_ok=True)
    _git(tree, "-c", "advice.detachedHead=false", "checkout", "-q", "--detach", case["head"])
    engines = ((load_config(root / "config" / "dev-model.yaml").get("paths") or {}).get("engines")
               or "scripts").rstrip("/")
    for path in (f"{engines}/lib/kitconfig.py", f"{engines}/check_record_prose.py"):
        blob = subprocess.run(["git", "cat-file", "blob", f"{kit_rev}:{path}"], cwd=root,
                              capture_output=True, check=False)
        if blob.returncode != 0:
            raise RunError(f"{path} at {kit_rev[:12]}: {blob.stderr.decode().strip()}")
        subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=tree, input=blob.stdout,
                       capture_output=True, check=True)


def _run_lens(command: list[str], tree: Path, prompt: str, timeout: int) -> subprocess.CompletedProcess:
    """Run the lens in its own process group, and end the group before returning.

    The round is retired as finished once this returns, so the group is killed
    whether the lens exited or timed out. A process that left the group (``setsid``)
    is out of reach of that kill; if one still holds the lens's output after the
    kill, this raises ``LensEscaped`` rather than wait on it or call the round
    finished. One that left and closed its output is not seen at all.
    """
    proc = subprocess.Popen(command, cwd=tree, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, errors="replace", start_new_session=True)
    try:
        stdout, stderr = proc.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc.pid)
        try:
            proc.communicate(timeout=DRAIN_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise LensEscaped from exc
        raise
    finally:
        _kill_group(proc.pid)
    return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)


def _kill_group(pgid: int) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pgid, signal.SIGKILL)


def prompt_args(root: Path, case: dict[str, Any], lens: str, runtime: str, tree: Path,
                kit_rev: str) -> list[str]:
    """``panel_prompt.py``'s arguments for one lens on one case.

    ``--preflight-rev`` is required, not optional: a historical head predates the
    preflight checker, so without it every real case fails to render.
    """
    return ["--root", str(root), "--lens", lens, "--head", case["head"], "--base", case["base"],
            "--branch", BRANCH, "--scratch", str(tree), "--runtime", runtime,
            "--preflight-rev", kit_rev]


def _withhold_repo(prompt: str) -> str:
    """``prompt`` with its ``**Repo:**`` line emptied.

    The line names ``--root``'s origin, which is a filesystem path to the kit
    checkout, with the fix commits and the case file, when that origin is local. A
    lens reviewing a case has no pull request to look up, so it loses nothing.
    """
    return _REPO_LINE.sub(r"\g<1>withheld by the reviewer eval", prompt)


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
    tree = Path(record["path"]) / f"lens-{lens}-{case['head'][:7]}"
    escaped = False
    try:
        (work / f"{case['id']}-{lens}.round.json").write_text(json.dumps(record, sort_keys=True))
        _isolated_tree(root, tree, case, kit_rev)
        prompt = _withhold_repo(
            _run_engine("panel_prompt.py", prompt_args(root, case, lens, runtime, tree, kit_rev), root))
        try:
            proc = _run_lens(command, tree, prompt, timeout)
        except LensEscaped as exc:
            escaped = True
            raise RunError(f"{case['id']} {lens}: lens command timed out after {timeout}s and a process it "
                           f"started left its group and still holds its output; the round is left at "
                           f"{record['path']} to retire once that process ends") from exc
        except subprocess.TimeoutExpired as exc:
            raise RunError(f"{case['id']} {lens}: lens command timed out after {timeout}s") from exc
        except OSError as exc:
            raise RunError(f"{case['id']} {lens}: cannot run lens command: {exc}") from exc
        if proc.returncode != 0:
            raise RunError(f"{case['id']} {lens}: lens command exited {proc.returncode}: "
                           f"{proc.stderr.strip()[:500]}")
        return proc.stdout
    finally:
        # A process that escaped the lens's group may still be working in the tree,
        # so that round is neither removed nor called finished.
        if not escaped:
            _retire(root, record, settings, tree, f"{case['id']} {lens}")


def _retire(root: Path, record: dict[str, Any], settings: Any, tree: Path, label: str) -> None:
    shutil.rmtree(tree, ignore_errors=True)
    try:
        outcome = sweep_scratch.finish_review_round(record, settings, root, apply=True,
                                                    reviewers_finished=True)
    except (sweep_scratch.ConfigError, sweep_scratch.Refused, OSError, ValueError) as exc:
        raise RunError(f"{label}: review round not retired: {exc}") from exc
    if outcome.action == "kept":
        raise RunError(f"{label}: review round kept at {outcome.path}: {outcome.reason}")


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
    out = Path(args.out).resolve() if args.out else None
    if out is not None:
        # A result left by an earlier run must not read as this one's, whatever this
        # run's exit.
        (out / "result.json").unlink(missing_ok=True)
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
        lenses = list(dict.fromkeys(args.lens or roster))
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


    # The score is stamped with the kit's HEAD, so HEAD must be what produced it: a
    # lens's focus is read from --root's working tree, an untracked module included.
    dirty = _git(root, "status", "--porcelain")
    if dirty:
        print("error: the kit checkout has uncommitted changes, so kit_revision would not name "
              "what produced the score; commit them first:\n" + dirty, file=sys.stderr)
        return 2
    # The engines run from this script's own checkout. When that is not --root, its
    # revision and state are recorded beside the score rather than refused, so the
    # runner's tests can point it at a fixture from a checkout under edit.
    engine_root = ENGINE_DIR.parent
    engine = None
    if engine_root.resolve() != root.resolve():
        engine = {"revision": _git(engine_root, "rev-parse", "HEAD"),
                  "dirty": bool(_git(engine_root, "status", "--porcelain"))}
    work = out or Path(_git(root, "rev-parse", "--absolute-git-dir")) / "review-eval"
    work.mkdir(parents=True, exist_ok=True)
    kit_rev = _git(root, "rev-parse", "HEAD")
    cases_sha256 = hashlib.sha256(cases_path.read_bytes()).hexdigest()
    results = []
    failure = None
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
        failure = str(exc)
        print(f"error: {exc}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 - keep the cases already scored, then report
        failure = f"{type(exc).__name__}: {exc}"
        print(f"error: {failure}", file=sys.stderr)

    result = {
        "schema": RESULT_SCHEMA,
        "runtime": args.runtime,
        "lens_command": args.lens_command,
        "kit_revision": kit_rev,
        # null when the engines ran from --root itself, which is then clean.
        "engine_checkout": engine,
        "cases_sha256": cases_sha256,
        # A run that stopped on a case keeps what it scored before it, marked partial.
        "complete": failure is None,
        "failure": failure,
        "summary": summarize(results, lenses),
        "results": results,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if out is not None:
        (out / "result.json").write_text(text)
    if failure is not None:
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
