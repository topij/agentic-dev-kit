"""The reviewer eval runner (#1156), driven by stub lenses so no model is called."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
ENGINE = ENGINE_DIR / "review_eval.py"
DOCTRINE = "docs/agentic-dev-kit/fallback-review-panel.md"
sys.path.insert(0, str(ENGINE_DIR))

import review_eval  # noqa: E402


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def _commit(root: Path, name: str, text: str) -> str:
    (root / name).write_text(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", name)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> dict:
    """A fixture repository: a bug commit, a clean commit, and the real doctrine."""
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "docs/agentic-dev-kit").mkdir(parents=True)
    (root / "scripts/lib").mkdir(parents=True)
    (root / "scripts/check_record_prose.py").write_text(
        '# /// script\n# requires-python = ">=3.12"\n# dependencies = []\n# ///\n')
    (root / "scripts/lib/kitconfig.py").write_text("# fixture parser\n")
    (root / DOCTRINE).write_text((REPO_ROOT / DOCTRINE).read_text(encoding="utf-8"))
    scratch = tmp_path / "scratch-root"
    scratch.mkdir()
    (root / "config/dev-model.yaml").write_text(
        f"scratch:\n  roots: [{str(scratch)!r}]\n  grace_window: 24h\n  worktree_repos: [{str(root)!r}]\n"
        "vcs:\n  protected_branch: main\n"
        "review:\n  fallback_panel:\n    lenses:\n"
        "      - name: adversarial\n        focus: prove it wrong\n"
        "      - name: correctness\n        focus: ask what it says\n"
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "remote.origin.url", "https://github.com/o/r.git")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    base = _git(root, "rev-parse", "HEAD")
    bug = _commit(root, "bug.py", "def f(x):\n    return x / 0\n    # unreachable\n")
    clean = _commit(root, "notes.md", "a note\n")
    cases = tmp_path / "cases.yaml"
    cases.write_text(
        "schema: review-eval-cases-v1\n"
        "bug_cases:\n"
        f"  - id: divide-by-zero\n    base: {base}\n    head: {bug}\n    source: \"#1\"\n"
        "    findings:\n      - path: bug.py\n        lines: [2, 2]\n        description: divides by zero\n"
        "    confirmed: \"fixture\"\n"
        f"  - id: unconfirmed-case\n    base: {base}\n    head: {bug}\n    source: \"#2\"\n"
        "    findings:\n      - path: bug.py\n        lines: [3, 3]\n        description: dead code\n"
        "    confirmed: \"\"\n"
        "clean_cases:\n"
        f"  - id: a-clean-note\n    base: {bug}\n    head: {clean}\n    source: \"#3\"\n    confirmed: \"\"\n"
    )
    return {"root": root, "cases": cases, "scratch": scratch, "base": base, "bug": bug, "clean": clean}


def _stub(tmp_path: Path, body: str, name: str = "lens.py") -> str:
    """A lens that records where it ran and what it was told, then prints ``body``."""
    path = tmp_path / name
    log = tmp_path / f"{name}.log"
    path.write_text(
        "import subprocess, sys\n"
        "prompt = sys.stdin.read()\n"
        "head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()\n"
        f"open({str(log)!r}, 'a').write(head + ' ' + str('## Your lens' in prompt or 'adversarial' in prompt) + '\\n')\n"
        f"sys.stdout.write({body!r})\n"
    )
    return f"{sys.executable} {path}"


def _run(repo: dict, command: str, *extra: str, out: Path | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(ENGINE), "--root", str(repo["root"]), "--cases", str(repo["cases"]),
            "--runtime", "claude", "--lens-command", command, "--scratch-root", str(repo["scratch"]), *extra]
    if out is not None:
        args += ["--out", str(out)]
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_a_cited_bug_is_a_hit_and_clean_findings_are_candidate_false_alarms(repo, tmp_path) -> None:
    command = _stub(tmp_path, "F1 HIGH: bug.py:2 divides by zero\nF2 LOW: notes.md:1 typo\n")
    out = tmp_path / "out"
    proc = _run(repo, command, "--lens", "adversarial", out=out)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert json.loads((out / "result.json").read_text()) == result
    assert result["schema"] == "review-eval-result-v1" and result["runtime"] == "claude"
    assert result["complete"] is True and result["failure"] is None
    assert result["lens_command"] == command
    assert result["kit_revision"] == repo["clean"]
    by_case = {r["case"]: r for r in result["results"]}
    assert by_case["divide-by-zero"]["hit"] is True
    assert by_case["divide-by-zero"]["matched_citations"] == [{"finding": 0, "path": "bug.py", "lines": [2, 2]}]
    assert by_case["unconfirmed-case"]["hit"] is False
    assert by_case["a-clean-note"]["candidate_false_alarms"] == 2
    assert result["summary"] == {"adversarial": {
        "confirmed_bug_cases": 1, "confirmed_hits": 1, "unconfirmed_bug_cases": 1,
        "unconfirmed_hits": 0, "clean_cases": 1, "candidate_false_alarms": 2}}
    assert (out / "divide-by-zero-adversarial.md").read_text().startswith("F1 HIGH")
    # The lens ran in a tree at each case head, with the rendered prompt on stdin.
    log = (tmp_path / "lens.py.log").read_text().split("\n")
    assert [line.split()[0] for line in log if line] == [repo["bug"], repo["bug"], repo["clean"]]
    assert all(line.endswith("True") for line in log if line)


def test_every_round_is_retired_and_every_tree_removed(repo, tmp_path) -> None:
    proc = _run(repo, _stub(tmp_path, "nothing found\n"))
    assert proc.returncode == 0, proc.stderr
    assert list(repo["scratch"].iterdir()) == []
    assert _git(repo["root"], "worktree", "list").count("\n") == 0
    summary = json.loads(proc.stdout)["summary"]
    assert set(summary) == {"adversarial", "correctness"}
    assert summary["correctness"]["confirmed_hits"] == 0


def test_a_failing_lens_command_is_exit_1_and_still_cleans_up(repo, tmp_path) -> None:
    script = tmp_path / "fail.py"
    script.write_text("import sys\nsys.stdin.read()\nsys.exit(3)\n")
    proc = _run(repo, f"{sys.executable} {script}", "--case", "divide-by-zero", "--lens", "adversarial")
    assert proc.returncode == 1
    assert "exited 3" in proc.stderr
    assert list(repo["scratch"].iterdir()) == []
    assert _git(repo["root"], "worktree", "list").count("\n") == 0


def test_an_empty_report_is_a_failed_case_not_a_clean_one(repo, tmp_path) -> None:
    script = tmp_path / "silent.py"
    script.write_text("import sys\nsys.stdin.read()\nsys.stdout.write('  \\n')\n")
    proc = _run(repo, f"{sys.executable} {script}", "--case", "a-clean-note", "--lens", "adversarial")
    assert proc.returncode == 1 and "printed no report" in proc.stderr
    assert list(repo["scratch"].iterdir()) == []


@pytest.mark.parametrize("edit, message", [
    (lambda t, r: t.replace(r["bug"], r["bug"][:12], 1), "full 40-hex sha"),
    (lambda t, r: t.replace(r["bug"], "f" * 40, 1), "is not a commit"),
    (lambda t, r: t.replace("id: unconfirmed-case", "id: divide-by-zero"), "unique"),
    (lambda t, r: t.replace("lines: [2, 2]", "lines: [3, 2]"), "start <= end"),
    (lambda t, r: t.replace("review-eval-cases-v1", "v0"), "schema"),
])
def test_a_malformed_case_file_is_refused(repo, tmp_path, edit, message) -> None:
    repo["cases"].write_text(edit(repo["cases"].read_text(), repo))
    proc = _run(repo, _stub(tmp_path, ""))
    assert proc.returncode == 2 and message in proc.stderr
    assert list(repo["scratch"].iterdir()) == []


def test_unknown_lenses_and_cases_are_refused(repo, tmp_path) -> None:
    assert "security" in _run(repo, _stub(tmp_path, ""), "--lens", "security").stderr
    assert "no such case" in _run(repo, _stub(tmp_path, ""), "--case", "nope").stderr


def test_the_lens_tree_holds_only_the_case_history_and_a_neutral_branch(repo, tmp_path) -> None:
    """The fix, the clean commit after the bug and the case file are not reachable."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import subprocess, sys\n"
        "prompt = sys.stdin.read()\n"
        "def git(*a):\n"
        "    return subprocess.run(['git', *a], capture_output=True, text=True)\n"
        f"later = git('cat-file', '-e', {repo['clean']!r}).returncode == 0\n"
        "refs = git('for-each-ref').stdout.strip()\n"
        "fetched = git('rev-parse', '-q', '--verify', 'FETCH_HEAD').returncode == 0\n"
        "branch = [l for l in prompt.splitlines() if 'Branch:' in l][0]\n"
        "print(f'later={later} refs={refs!r} fetched={fetched} {branch}')\n"
    )
    proc = _run(repo, f"{sys.executable} {probe}", "--lens", "adversarial", out=tmp_path / "out")
    assert proc.returncode == 0, proc.stderr
    report = (tmp_path / "out" / "divide-by-zero-adversarial.md").read_text()
    assert report.startswith("later=False refs='' fetched=False"), report
    assert "review-eval/case" in report and "divide-by-zero" not in report
    clean = (tmp_path / "out" / "a-clean-note-adversarial.md").read_text()
    assert "review-eval/case" in clean


def test_the_prompt_pins_the_preflight_checker_at_the_kit_revision(repo, tmp_path) -> None:
    """A historical head predates the checker, so the eval always names its own revision."""
    case = {"base": repo["base"], "head": repo["bug"], "id": "divide-by-zero"}
    args = review_eval.prompt_args(repo["root"], case, "adversarial", "claude", tmp_path, "c" * 40)
    assert args[args.index("--preflight-rev") + 1] == "c" * 40
    assert args[args.index("--branch") + 1] == review_eval.BRANCH


def test_the_prompt_withholds_the_kit_checkout(repo, tmp_path) -> None:
    """A local origin would name the checkout holding the fix commits and the case file."""
    _git(repo["root"], "config", "remote.origin.url", str(repo["root"]))
    probe = tmp_path / "probe.py"
    probe.write_text("import sys\nsys.stdout.write(sys.stdin.read())\n")
    proc = _run(repo, f"{sys.executable} {probe}", "--lens", "adversarial", "--case", "divide-by-zero",
                out=tmp_path / "out")
    assert proc.returncode == 0, proc.stderr
    prompt = (tmp_path / "out" / "divide-by-zero-adversarial.md").read_text()
    assert "- **Repo:** withheld by the reviewer eval" in prompt
    assert str(repo["root"]) not in prompt


def test_section_matching_stays_linear_on_long_whitespace() -> None:
    import time
    start = time.monotonic()
    review_eval.findings_text("## executed" + " " * 200_000 + "x\n" + "**a" + " " * 200_000 + "\n")
    assert time.monotonic() - start < 5


def test_a_hit_on_an_unconfirmed_case_is_not_a_confirmed_hit(repo, tmp_path) -> None:
    proc = _run(repo, _stub(tmp_path, "F1 LOW: bug.py:3 dead code\n"), "--lens", "adversarial")
    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)["summary"]["adversarial"]
    assert (summary["confirmed_hits"], summary["unconfirmed_hits"]) == (0, 1)


def test_a_repeated_lens_runs_once(repo, tmp_path) -> None:
    proc = _run(repo, _stub(tmp_path, "nothing\n"), "--lens", "adversarial", "--lens", "adversarial",
                "--case", "divide-by-zero")
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)["results"]) == 1


def test_nothing_the_lens_started_outlives_it(repo, tmp_path) -> None:
    marker = tmp_path / "late"
    script = tmp_path / "spawn.py"
    script.write_text(
        "import subprocess, sys\nsys.stdin.read()\n"
        f"subprocess.Popen(['sh', '-c', 'sleep 1; touch {marker}'], stdin=subprocess.DEVNULL,\n"
        "                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\nprint('done')\n")
    proc = _run(repo, f"{sys.executable} {script}", "--lens", "adversarial", "--case", "divide-by-zero")
    assert proc.returncode == 0, proc.stderr
    subprocess.run(["sleep", "2"], check=True)
    assert not marker.exists()


def test_a_lens_that_overruns_its_timeout_is_stopped_and_cleaned_up(repo, tmp_path) -> None:
    script = tmp_path / "slow.py"
    # Its child holds the lens's output too, and goes with the group.
    script.write_text("import subprocess, sys, time\nsys.stdin.read()\n"
                      "subprocess.Popen(['sleep', '60'])\ntime.sleep(60)\n")
    proc = _run(repo, f"{sys.executable} {script}", "--lens", "adversarial", "--case", "divide-by-zero",
                "--timeout", "1")
    assert proc.returncode == 1 and "timed out" in proc.stderr and "left its group" not in proc.stderr
    assert list(repo["scratch"].iterdir()) == []


def test_a_lens_that_escapes_its_group_leaves_the_round_unretired(repo, tmp_path, monkeypatch, capsys) -> None:
    """A process that left the group cannot be killed with it: the round is not called finished."""
    script = tmp_path / "escape.py"
    script.write_text(
        "import subprocess, sys, time\nsys.stdin.read()\n"
        "child = subprocess.Popen(['sleep', '60'], start_new_session=True)\n"
        f"open({str(tmp_path / 'escaped.pid')!r}, 'w').write(str(child.pid))\ntime.sleep(60)\n")
    monkeypatch.setattr(review_eval, "DRAIN_SECONDS", 1)
    try:
        code = review_eval.main([
            "--root", str(repo["root"]), "--cases", str(repo["cases"]), "--runtime", "claude",
            "--lens-command", f"{sys.executable} {script}", "--scratch-root", str(repo["scratch"]),
            "--lens", "adversarial", "--case", "divide-by-zero", "--timeout", "1"])
    finally:
        pid = tmp_path / "escaped.pid"
        if pid.exists():
            with contextlib.suppress(ProcessLookupError):
                os.kill(int(pid.read_text()), signal.SIGKILL)
    assert code == 1
    assert "left its group" in capsys.readouterr().err
    assert len(list(repo["scratch"].iterdir())) == 1


@pytest.mark.parametrize("path", ["notes.md", "scripts/untracked.py"])
def test_a_dirty_kit_checkout_is_refused(repo, tmp_path, path) -> None:
    """kit_revision must name what produced the score, and a lens's focus is read from the tree."""
    (repo["root"] / path).write_text("an uncommitted edit\n")
    out = tmp_path / "out"
    out.mkdir()
    (out / "result.json").write_text('{"complete": true}\n')  # an earlier run's
    proc = _run(repo, _stub(tmp_path, ""), out=out)
    assert proc.returncode == 2 and "uncommitted" in proc.stderr
    assert list(repo["scratch"].iterdir()) == []
    assert not (out / "result.json").exists()


def test_engines_run_from_another_checkout_are_recorded(repo, tmp_path) -> None:
    proc = _run(repo, _stub(tmp_path, "nothing\n"), "--lens", "adversarial", "--case", "divide-by-zero")
    assert proc.returncode == 0, proc.stderr
    engine = json.loads(proc.stdout)["engine_checkout"]
    assert engine["revision"] == _git(REPO_ROOT, "rev-parse", "HEAD")
    assert isinstance(engine["dirty"], bool)


def test_a_run_that_stops_keeps_what_it_scored(repo, tmp_path) -> None:
    script = tmp_path / "late-fail.py"
    script.write_text(
        "import subprocess, sys\nsys.stdin.read()\n"
        "head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()\n"
        f"print('nothing found')\nsys.exit(3 if head == {repo['clean']!r} else 0)\n")
    out = tmp_path / "out"
    proc = _run(repo, f"{sys.executable} {script}", "--lens", "adversarial", out=out)
    assert proc.returncode == 1 and proc.stdout == ""
    result = json.loads((out / "result.json").read_text())
    assert result["complete"] is False and "exited 3" in result["failure"]
    assert [r["case"] for r in result["results"]] == ["divide-by-zero", "unconfirmed-case"]


def test_a_refused_invocation_still_drops_a_stale_result(repo, tmp_path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "result.json").write_text('{"complete": true}\n')
    proc = _run(repo, _stub(tmp_path, ""), "--lens", "nosuch", out=out)
    assert proc.returncode == 2 and not (out / "result.json").exists()


def test_a_lens_writing_bytes_that_are_not_utf8_is_still_scored(repo, tmp_path) -> None:
    script = tmp_path / "bytes.py"
    script.write_text("import sys\nsys.stdin.read()\nsys.stdout.buffer.write(b'F1 LOW: bug.py:2 \\xff\\xfe\\n')\n")
    proc = _run(repo, f"{sys.executable} {script}", "--lens", "adversarial", "--case", "divide-by-zero")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["results"][0]["hit"] is True


def test_any_error_keeps_what_was_scored(repo, tmp_path, monkeypatch) -> None:
    calls = []
    real = review_eval._isolated_tree

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise OSError("disk full")
        return real(*args, **kwargs)

    monkeypatch.setattr(review_eval, "_isolated_tree", flaky)
    out = tmp_path / "out"
    code = review_eval.main([
        "--root", str(repo["root"]), "--cases", str(repo["cases"]), "--runtime", "claude",
        "--lens-command", _stub(tmp_path, "nothing\n"), "--scratch-root", str(repo["scratch"]),
        "--lens", "adversarial", "--out", str(out)])
    assert code == 1
    result = json.loads((out / "result.json").read_text())
    assert result["complete"] is False and "disk full" in result["failure"]
    assert [r["case"] for r in result["results"]] == ["divide-by-zero"]


def test_a_round_sweep_keeps_is_a_failed_run(repo, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(review_eval.sweep_scratch, "finish_review_round",
                        lambda record, *a, **k: review_eval.sweep_scratch.Outcome(record["path"], "kept", "held"))
    code = review_eval.main([
        "--root", str(repo["root"]), "--cases", str(repo["cases"]), "--runtime", "claude",
        "--lens-command", _stub(tmp_path, "nothing\n"), "--scratch-root", str(repo["scratch"]),
        "--lens", "adversarial", "--case", "divide-by-zero"])
    assert code == 1 and "review round kept" in capsys.readouterr().err


@pytest.mark.parametrize("report, count", [
    ("F1 LOW: a.py:1 x\nF2 LOW: b.py:2 y\n", 2),
    # An unnumbered report is counted by its distinct citations, not read as silent.
    ("Finding: x.py:3 bad\n2. y.py:4 bad\nagain x.py:3\n", 2),
    ("nothing found\n", 0),
    # Only a line that opens with F<n> numbers a finding.
    ("F1 LOW: a.py:1 x\nas F1 says, and F2 of the contract\n", 1),
    ("F1 LOW: a.py:1 x\n## Verified clean\nF2 checked b.py:2\n", 1),
])
def test_clean_case_findings_are_counted_even_unnumbered(report, count) -> None:
    assert review_eval.score_clean(report)["candidate_false_alarms"] == count


@pytest.mark.parametrize("report, hit", [
    ("see bug.py:1-2", True),
    # A citation as wide as a file is not a finding.
    ("see bug.py:1-99999", False),
    ("see src/bug.py:2", True),
    ("see bug.py:3", False),
    ("see other.py:2", False),
    ("bug.py line 2, no citation", False),
    ("see bug.py:L2", True),
    # Codex cites a file in its tree by absolute path, often as a link target.
    ("[guard](/private/tmp/claude-502/-Users-x-kit/review-1/lens-adversarial-abc1234/bug.py:2) fails", True),
    ("see /tmp/r/lens-x/other.py:2", False),
    # A line the lens checked and cleared is not a finding.
    ("## Verified clean\n- bug.py:2 reviewed, no issue\n\nNo findings.", False),
    ("**What I reviewed**\nbug.py:2\n**F1 (HIGH): divides by zero**\nbug.py:2", True),
    # A finding whose title names a report section is still a finding.
    ("### F1 (LOW): a mutation survives\nbug.py:2", True),
    ("### Finding 1 — Executed check ignored\nbug.py:2", True),
    # A finding listed after the contract's opening section needs no heading of its own.
    ("## What I reviewed\n- bug.py:2 read\n\nF1 HIGH bug.py:2 divides by zero", True),
    ("## What I reviewed\n- bug.py:2 read\n\n- F1: bug.py:2 divides by zero", True),
    ("## What I reviewed\n- bug.py:2 read\n\n1. **F1** bug.py:2 divides by zero", True),
    # A bold lead-in is body text, and a comment in fenced code is not a heading.
    ("**bug.py:2** — divides by zero, executed on every call", True),
    ("**Verified clean:** bug.py:2 cleared", False),
    ("**Executed** pytest at bug.py:2 passes", False),
    ("- **Verified clean:** bug.py:2 cleared", False),
    ("> **Verified clean:** bug.py:2 cleared", False),
    ("__Verified clean:__ bug.py:2 cleared", False),
    ("## Verified clean (what I executed)\n- bug.py:2 fine", False),
    ("### Mutation and verification\n- deleting bug.py:2 fails a test", False),
    # A section name opening a finding's title does not make it a section.
    ("**Mutation of shared state in bug.py:2** — aliasing", True),
    ("**Executed path skips guard** bug.py:2 divides by zero", True),
    # A heading opening with a section name is that section, whatever follows the name.
    ("## Mutation test\n- bug.py:2 cleared", False),
    ("## Executed commands\n- bug.py:2 cleared", False),
    ("## Routes allowed and refused\n- bug.py:2 cleared", False),
    ("**Verified clean — what I checked**\n- bug.py:2 cleared", False),
    # An evidence label inside a finding drops its own line, not the finding.
    ("F1 HIGH divides by zero\n**Executed:** ran it\nbug.py:2 raises ZeroDivisionError", True),
    ("**Verified clean:** a.py:1\n\n**bug.py:2** — divides by zero", True),
    ("### F1\nother.py:1\n```sh\n# mutation executed here\n```\nbug.py:2 divides by zero", True),
])
def test_a_hit_needs_an_overlapping_citation(report, hit) -> None:
    case = {"findings": [{"path": "bug.py", "lines": [2, 2]}]}
    assert review_eval.score_bug(report, case)["hit"] is hit


def test_the_shipped_case_set_names_the_issues_the_ticket_requires() -> None:
    """#1156's acceptance: at least #19, #23 and #95, each with a confirmation."""
    data = review_eval.load_config(REPO_ROOT / review_eval.CASES)
    sources = {case["source"]: case for case in data["bug_cases"]}
    for issue in ("#19", "#23", "#95"):
        assert issue in sources and sources[issue]["confirmed"].strip(), issue
        for finding in sources[issue]["findings"]:
            assert finding["path"] and finding["lines"][0] <= finding["lines"][1]
