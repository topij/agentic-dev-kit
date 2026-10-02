#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run the kit's on-demand runtime smoke tests and write a stamped record (#879).

Phase 6 items 7 and 8 of the parity plan. Repository checks prove what the kit's
files declare; they cannot prove that a client discovered, trusted or executed them.
This runner starts the real clients against a disposable copy of the kit and records
what each runtime did, so a parity observation can be repeated against a newer client
instead of aging with the one it was first made on.

It is kept out of pull-request CI on purpose: it starts real clients, spends real
model calls, and needs credentials CI does not hold. Run it on demand from a checkout
of the kit whose copy of this file is committed at the revision under test:

    uv run <engine-dir>/runtime_smoke.py --work-root <dir> --out <new dir> \\
        [--revision <commit>] [--runtime codex|claude] \\
        --codex-bin <absolute path> --codex-version <version> --codex-home <dir> \\
        [--claude-bin <absolute path> --claude-version <version> \\
         --claude-config-dir <dir>] [--allow-codex-project-trust] \\
        [--allow-codex-hook-trust-bypass] [--timeout <s>]

One row per check per runtime:

    codex.instructions    AGENTS.md reaches the session
    codex.skills          every declared Codex skill is discovered
    codex.session_start   the SessionStart hook runs and its output reaches the session
    codex.post_tool_use   the PostToolUse hook runs after a shell call and reaches it
    codex.review          native review (`codex exec review`) runs
    codex.panel           the configured fallback panel runs at its configured compute
    codex.lane            one parallel lane runs through the kit's lane launcher
    claude.instructions   CLAUDE.md and the AGENTS.md it imports are loaded
    claude.commands       every declared command and every configured lens agent loads
    claude.session_start  as for Codex
    claude.post_tool_use  as for Codex
    claude.review         the configured review command (`review.fallback_commands`)
    claude.panel          as for Codex, each lens launched as its agent definition
    claude.lane           as for Codex

**What a runtime did is read from its own artifacts, never from what a model says.**
Codex rows read the session rollout under the isolated `CODEX_HOME`; Claude rows read
the stream-json events and the session transcript under the isolated config
directory; lane rows also read the launcher's terminal receipt. Model-written text
serves only as a liveness check: a review that returned something, a lens report that
names the review head, a lane's final text that carries its task token. The executing
client version and the applied model and effort come from those artifacts too (rollout
`session_meta` and `turn_context`, transcript `version`, `message.model` and `effort`),
so a shell CLI that differs from the runtime that executed a check shows as a pin
mismatch on the row instead of a wrong stamp on the record.

The SessionStart engine, `check_doc_budget.py --quiet`, prints nothing on a healthy
tree, so silence proves neither execution nor failure. The fixture therefore commits
its friction log a random number of lines over budget, and the row passes only when
the tripwire line naming that number appears in context the runtime injected. The
PostToolUse probe prints a pull-request URL carrying a per-run nonce, and the row
passes only when the follow-up hook's warning appears in the session after that call.
Both expected texts are produced by running the fixture's own engines before any
client starts, not restated here.

**Isolation and trust.** Each runtime runs under a home the operator provisions and
logs in to once: `--codex-home` becomes `CODEX_HOME` and `--claude-config-dir` becomes
`CLAUDE_CONFIG_DIR`. The runner refuses the default homes, so no client it starts uses
the operator's own Codex home or Claude configuration directory. #802 observed
`codex exec` writing a trusted-project entry for its working directory into the home
it ran under; the record lists every project and hook-state entry a run adds to the
isolated home's `config.toml`, so that side effect is observed rather than assumed. The runner grants
no trust itself. Codex trusts a project's hooks at two layers, the project and each
definition, and a fresh fixture holds neither, so the two Codex hook rows record
`not-run`, naming the missing layer, unless the operator authorizes both for the hook
probe alone: `--allow-codex-project-trust` adds a per-invocation `-c` override trusting
the fixture path, and `--allow-codex-hook-trust-bypass` adds the client's
`--dangerously-bypass-hook-trust`. Neither is written anywhere, and both apply only
after the runner has checked that the fixture's hook registration is the revision's
own bytes. That check binds the authorization to the revision's registration; vetting
the revision itself is the operator's choice of `--revision`.

**The fixture** is `git archive` of the kit revision: tracked files only, so no local
config overlay, `state/`, or operator note reaches a client. It is committed as a fresh
repository with a local bare `origin`, then one controls commit and one review-target
branch. Nothing is deleted: each run creates a new directory under `--work-root` and
leaves it there, with the fixture, the lens clones, the lane worktrees and the logs,
for the operator to remove.

**The record** is `record.json` and `record.md` under `--out`. It is stamped with the
kit revision, the date, the invocation with operator paths replaced by placeholders,
each client's shell `--version`, and the executing version each row's artifacts
report. No raw rollout or transcript is retained in it; logs stay in the run directory.
The record is written aside and moved into place whole as the run's last step, so a run
that is interrupted, or that fails on its own account, leaves no record at `--out`; it
stops every client it started, says what it left at `--out`, and leaves its run
directory as it stood.

Exit status: 0 every row passed; 1 a row failed; 3 no row failed and at least one did
not run; 2 refused before any client started; 4 interrupted, or failed on its own
account, with every client it had started stopped and stderr saying whether a record
reached `--out`.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import io
import itertools
import json
import os
import re
import secrets
import shlex
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT_PATH.parent / "lib"))

from kitconfig import get, load_config, loads, repo_root  # noqa: E402

SCHEMA = "adk-runtime-smoke/1"
PARITY_DOC = "docs/agentic-dev-kit/runtime-parity.md"
CODEX_HOOKS = ".codex/hooks.json"
# Engine paths relative to the fixture's own `paths.engines`.
HOOK_ENGINE = "hooks/pr_followup_hook.py"
BUDGET_ENGINE = "check_doc_budget.py"
REVIEW_BRANCH = "smoke-review"
REVIEW_TARGET = "docs/smoke-review-target.md"

ROWS: tuple[tuple[str, str, str], ...] = (
    ("codex.instructions", "codex", "AGENTS.md discovery"),
    ("codex.skills", "codex", "repository skill discovery"),
    ("codex.session_start", "codex", "SessionStart hook"),
    ("codex.post_tool_use", "codex", "PostToolUse hook"),
    ("codex.review", "codex", "native review (`codex exec review`)"),
    ("codex.panel", "codex", "configured fallback panel"),
    ("codex.lane", "codex", "parallel lane through `launch_lane.py`"),
    ("claude.instructions", "claude", "CLAUDE.md and its AGENTS.md import"),
    ("claude.commands", "claude", "command and lens-agent discovery"),
    ("claude.session_start", "claude", "SessionStart hook"),
    ("claude.post_tool_use", "claude", "PostToolUse hook"),
    ("claude.review", "claude", "configured review command"),
    ("claude.panel", "claude", "configured fallback panel"),
    ("claude.lane", "claude", "parallel lane through `launch_lane.py`"),
)
RUNTIMES = ("codex", "claude")

EXIT_PASSED, EXIT_FAILED, EXIT_REFUSED, EXIT_INCOMPLETE, EXIT_ABORTED = 0, 1, 2, 3, 4
# Client probes that answer at once (`--version`, a login status) get this long.
PREFLIGHT_TIMEOUT = 60
# The process groups of the clients running now. An interrupt stops every one: a
# client the runner abandoned would keep spending, perhaps under a trust bypass,
# until its own timeout.
_LIVE_GROUPS: set[int] = set()
_LIVE_LOCK = threading.Lock()

# What a fixture child never inherits. Lane and repository identity would point the
# fixture's engines at the operator's tree (the launcher strips the same set), a set
# `JOB_NAME` silences both hooks by design, `FORCE_COLOR` colourises engine output
# (#884), and each runtime's home is assigned explicitly or not at all.
SCRUBBED_PREFIXES = ("DEVKIT_", "GIT_")
SCRUBBED_KEYS = frozenset(
    {"GH_REPO", "JOB_NAME", "FORCE_COLOR", "PWD", "OLDPWD", "CODEX_HOME", "CLAUDE_CONFIG_DIR"}
)
CLAUDE_CREDENTIAL_ENV = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")
# A lens reads the diff with git; the kit's project settings allow none of these, and
# `dontAsk` would turn the first read into a denial. Passed per invocation, so nothing
# under `.claude/` changes.
CLAUDE_READ_ONLY_GIT = (
    "Bash(git diff:*)",
    "Bash(git show:*)",
    "Bash(git log:*)",
    "Bash(git status:*)",
    "Bash(git rev-parse:*)",
    "Bash(git ls-remote:*)",
)
EXCERPT_LIMIT = 240
# Strings in the record are bounded only after redaction: an excerpt cut first can end
# inside an operator path, leaving a prefix no placeholder matches.
RECORD_STRING_LIMIT = 600
LANE_SCOPES = {"codex": "smoke-codex", "claude": "smoke-claude"}

# The injected-context shapes Codex writes into a rollout. AGENTS.md has arrived two
# ways from the same 0.153.4 client: as a user message (the operator's desktop-launched
# sessions) and as `state.agents_md` in a `world_state` snapshot (a fresh `codex exec`
# under an isolated home, the first live run of this runner). The skills list arrives as
# a developer message whose entries name their file through a root alias. Matching fails
# closed: a shape this does not recognise leaves the row failed, with the first line of
# each candidate message in its evidence so the changed shape can be read from the record.
AGENTS_BLOCK = re.compile(
    r"\A# AGENTS\.md instructions for (?P<dir>[^\n]+)\n\n<INSTRUCTIONS>\n(?P<body>.*)\n"
    r"</INSTRUCTIONS>\s*\Z",
    re.S,
)
SKILL_ROOT = re.compile(r"^- `(?P<alias>[^`]+)` = `(?P<path>[^`]+)`\s*$", re.M)
SKILL_FILE = re.compile(r"\(file: (?P<file>[^)\n]+)\)\s*$", re.M)


class Refusal(Exception):
    """A precondition failed before any client started (exit 2)."""


@dataclass
class Row:
    id: str
    runtime: str
    check: str
    status: str = "not-run"
    reason: str = "not attempted"
    evidence: dict[str, Any] = field(default_factory=dict)
    session: dict[str, Any] = field(default_factory=dict)
    invocations: list[dict[str, Any]] = field(default_factory=list)

    def set(self, status: str, reason: str, **evidence: Any) -> None:
        self.status = status
        self.reason = reason
        self.evidence.update(evidence)


@dataclass
class Fixture:
    repo: Path
    engines: Path
    origin: Path
    main_head: str
    review_head: str
    friction_rel: str
    friction_lines: int
    friction_budget: int
    agents_md: bytes


@dataclass
class Context:
    kit_root: Path
    revision: str
    run_dir: Path
    log_dir: Path
    fixture: Fixture
    config: dict[str, Any]
    timeout: int
    nonce: str
    pr_number: int
    budget_line: str
    followup_markers: dict[str, str]
    base_env: dict[str, str]


# --------------------------------------------------------------------------- helpers


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def flatten(text: str) -> str:
    """One line, whitespace collapsed, nothing cut: captured text waits for redaction."""
    return " ".join(text.split())


def excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def realpath(path: Path | str) -> str:
    return os.path.realpath(str(path))


def scrubbed_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(SCRUBBED_PREFIXES) and key not in SCRUBBED_KEYS
    }


def fixture_git_env(base: dict[str, str]) -> dict[str, str]:
    """Git for the runner's own fixture commits: no operator config, signing or hooks."""
    return {
        **base,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "adk runtime smoke",
        "GIT_AUTHOR_EMAIL": "smoke@fixture.invalid",
        "GIT_COMMITTER_NAME": "adk runtime smoke",
        "GIT_COMMITTER_EMAIL": "smoke@fixture.invalid",
    }


def git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=300
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal(f"git {' '.join(args)} could not run in {cwd}: {exc}") from exc
    if result.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout.strip()


def run_child(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdin_text: str,
    timeout: int,
    log_dir: Path,
    name: str,
) -> dict[str, Any]:
    """Run one client with a finite timeout; record exit status and timeout together.

    The child gets its own session so a timeout can stop everything it started, and
    the outcome is returned rather than raised: a hung or failed client is a row result,
    not a harness crash.
    """
    stdout_path = log_dir / f"{name}.stdout"
    stderr_path = log_dir / f"{name}.stderr"
    started = time.monotonic()
    timed_out = False
    returncode: int | None = None
    error: str | None = None
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
        except OSError as exc:
            error = f"could not start: {exc}"
        else:
            with _LIVE_LOCK:
                _LIVE_GROUPS.add(process.pid)
            try:
                process.communicate(stdin_text.encode(), timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                _stop_group(process)
            except BaseException:
                _stop_group(process)
                raise
            finally:
                with _LIVE_LOCK:
                    _LIVE_GROUPS.discard(process.pid)
            returncode = process.returncode
    stderr_lines = [line for line in _read_text(stderr_path).splitlines() if line.strip()]
    return {
        "name": name,
        "argv": list(argv),
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "duration_seconds": round(time.monotonic() - started, 1),
        "error": error,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        # A client's own notice lands here — Claude's note that an untrusted project's
        # allow list was ignored, say — so the first line is kept in the record.
        "stderr_head": flatten(stderr_lines[0]) if stderr_lines else "",
    }


def _stop_group(process: subprocess.Popen) -> None:
    for sig, grace in ((signal.SIGTERM, 10), (signal.SIGKILL, 10)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        try:
            process.wait(timeout=grace)
            break
        except subprocess.TimeoutExpired:
            continue


def stop_live_children() -> None:
    """Stop every client group still running: SIGTERM, a short grace, then SIGKILL.

    Called when the run is interrupted or fails. A client launched from a worker
    thread is not reached by the main thread's exception, so the registry is how
    the main thread finds it.
    """
    with _LIVE_LOCK:
        groups = sorted(_LIVE_GROUPS)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        alive = []
        for group in groups:
            try:
                os.killpg(group, sig)
                alive.append(group)
            except (ProcessLookupError, PermissionError):
                continue
        deadline = time.monotonic() + 5
        while alive and time.monotonic() < deadline:
            alive = [group for group in alive if _group_alive(group)]
            time.sleep(0.1)
        groups = alive


def _group_alive(group: int) -> bool:
    try:
        os.killpg(group, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _interrupt(signum: int, _frame: Any) -> None:
    raise KeyboardInterrupt(f"signal {signum}")


def invocation_ok(invocation: dict[str, Any]) -> str | None:
    """None when the child exited 0 in time, otherwise the reason it did not."""
    if invocation["error"]:
        return invocation["error"]
    if invocation["timed_out"]:
        return f"timed out after {invocation['timeout_seconds']}s"
    if invocation["returncode"] != 0:
        return f"exited {invocation['returncode']}"
    return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return entries
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            entries.append(value)
    return entries


# --------------------------------------------------------------- harness and inputs


def resolve_revision(kit_root: Path, revision: str) -> str:
    return git(kit_root, "rev-parse", "--verify", f"{revision}^{{commit}}")


def verify_harness(kit_root: Path, revision: str) -> dict[str, str]:
    """Refuse unless this file and the helper it imports are the revision's own bytes.

    A record says which kit revision produced it; a runner edited after that commit
    would stamp a revision it is not. The fixture's engines need no such check: they
    are extracted from the revision itself.
    """
    digests: dict[str, str] = {}
    for path in (SCRIPT_PATH, SCRIPT_PATH.parent / "lib" / "kitconfig.py"):
        rel = path.relative_to(kit_root).as_posix()
        committed = subprocess.run(
            ["git", "show", f"{revision}:{rel}"], cwd=kit_root, capture_output=True
        )
        if committed.returncode != 0:
            raise Refusal(f"{rel} is not in revision {revision}; commit the runner first")
        current = path.read_bytes()
        if committed.stdout != current:
            raise Refusal(
                f"{rel} differs from revision {revision}; the record would stamp a "
                "revision the harness is not. Commit it, or run from a clean checkout."
            )
        digests[rel] = sha256_bytes(current)
    return digests


def default_home(env_key: str, fallback: str) -> str:
    value = os.environ.get(env_key)
    return realpath(value) if value else realpath(Path.home() / fallback)


def check_isolated_home(path: Path, *, flag: str, env_key: str, fallback: str, kit_root: Path) -> Path:
    if not path.is_absolute():
        raise Refusal(f"{flag} must be an absolute path")
    if not path.is_dir():
        raise Refusal(f"{flag} {path} is not an existing directory")
    resolved = realpath(path)
    if resolved in {default_home(env_key, fallback), realpath(Path.home() / fallback)}:
        raise Refusal(
            f"{flag} is the operator's own home; the runner only uses an isolated one "
            "so that no trust entry or session lands in the operator's settings (#802)"
        )
    if Path(resolved).is_relative_to(realpath(kit_root)):
        raise Refusal(f"{flag} must not be inside the kit checkout")
    return Path(resolved)


def check_binary(path: Path, flag: str) -> Path:
    if not path.is_absolute():
        raise Refusal(f"{flag} must be an absolute path, so the record names one binary")
    if not (path.is_file() and os.access(path, os.X_OK)):
        raise Refusal(f"{flag} {path} is not an executable file")
    return path


def parity_declaration(repo: Path) -> dict[str, Any]:
    text = (repo / PARITY_DOC).read_text(encoding="utf-8")
    _, front_matter, _ = text.split("---", 2)
    return loads(front_matter)


def expected_codex_skills(repo: Path) -> list[str]:
    return sorted(
        realpath(repo / entry["codex"])
        for entry in parity_declaration(repo)["workflow_contract"]
        if entry.get("codex")
    )


def expected_claude_commands(repo: Path) -> list[str]:
    return sorted(
        Path(entry["claude"]).stem
        for entry in parity_declaration(repo)["workflow_contract"]
        if entry.get("claude")
    )


def lens_roster(config: dict[str, Any]) -> list[str]:
    return [entry["name"] for entry in get(config, "review.fallback_panel.lenses", []) or []]


# ------------------------------------------------------------------------ fixture


def build_fixture(kit_root: Path, revision: str, run_dir: Path, base_env: dict[str, str]) -> Fixture:
    """Extract the revision's tracked tree into a fresh repository with a bare origin."""
    repo = run_dir / "repo"
    origin = run_dir / "origin.git"
    repo.mkdir()
    archive = subprocess.run(
        ["git", "archive", "--format=tar", revision], cwd=kit_root, capture_output=True
    )
    if archive.returncode != 0:
        raise Refusal(f"git archive {revision} failed: {archive.stderr.decode(errors='replace')}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(repo, filter="data")
    env = fixture_git_env(base_env)
    git(repo, "init", "-q", "-b", "main", env=env)
    git(repo, "add", "-A", env=env)
    git(repo, "commit", "-q", "-m", f"fixture: agentic-dev-kit tree at {revision}", env=env)

    config = load_config(repo / "config" / "dev-model.yaml", overlay=False)
    friction_rel = get(config, "paths.friction_log")
    budgets = {entry["path"]: int(entry["budget"]) for entry in get(config, "doc_budgets", []) or []}
    if friction_rel not in budgets:
        raise Refusal(f"doc_budgets has no entry for paths.friction_log ({friction_rel})")
    target = pad_over_budget(repo / friction_rel, budgets[friction_rel])
    git(repo, "add", friction_rel, env=env)
    git(repo, "commit", "-q", "-m", "fixture: smoke controls", env=env)
    main_head = git(repo, "rev-parse", "HEAD", env=env)

    git(run_dir, "init", "-q", "--bare", str(origin), env=env)
    git(repo, "remote", "add", "origin", str(origin), env=env)
    git(repo, "push", "-q", "origin", "main", env=env)

    git(repo, "switch", "-q", "-c", REVIEW_BRANCH, env=env)
    (repo / REVIEW_TARGET).write_text(
        "# Smoke review target\n\n"
        "This page exists only in the runtime smoke fixture. `check_doc_budget.py` exits\n"
        "1 whenever a tracked document is over its budget, so a SessionStart hook that\n"
        "runs it blocks the session until the document is swept.\n",
        encoding="utf-8",
    )
    git(repo, "add", REVIEW_TARGET, env=env)
    git(repo, "commit", "-q", "-m", "fixture: review target", env=env)
    git(repo, "push", "-q", "-u", "origin", REVIEW_BRANCH, env=env)
    review_head = git(repo, "rev-parse", "HEAD", env=env)
    return Fixture(
        repo=repo,
        engines=repo / get(config, "paths.engines", "scripts"),
        origin=origin,
        main_head=main_head,
        review_head=review_head,
        friction_rel=friction_rel,
        friction_lines=target,
        friction_budget=budgets[friction_rel],
        agents_md=(repo / "AGENTS.md").read_bytes(),
    )


def pad_over_budget(path: Path, budget: int) -> int:
    """Append control lines until `path` is 7 to 97 lines over `budget`, chosen at random.

    Returns the count the budget engine will report, which counts lines the same way.
    """
    with path.open("r", encoding="utf-8") as handle:
        current = sum(1 for _ in handle)
    target = max(current, budget) + secrets.randbelow(91) + 7
    unterminated = path.read_bytes()[-1:] not in (b"", b"\n")
    with path.open("a", encoding="utf-8") as handle:
        # Terminate an unterminated last line first, or the first control line would
        # join it and the engine would count one line fewer than the record states.
        if unterminated:
            handle.write("\n")
        for index in range(target - current):
            handle.write(f"<!-- runtime smoke control line {index} -->\n")
    return target


def expected_budget_line(fixture: Fixture, env: dict[str, str]) -> str:
    """The tripwire line the fixture's own engine prints for the over-budget control."""
    try:
        result = subprocess.run(
            [sys.executable, str(fixture.engines / BUDGET_ENGINE), "--quiet"],
            cwd=fixture.repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal(f"the fixture's budget engine did not finish: {exc}") from exc
    needle = f"{fixture.friction_rel} is {fixture.friction_lines} lines"
    for line in result.stdout.splitlines():
        if needle in line:
            return line.strip()
    raise Refusal(
        f"the fixture's budget engine did not report {needle!r}; the SessionStart control "
        f"is broken (exit {result.returncode}, stdout {excerpt(result.stdout)!r})"
    )


def probe_command(nonce: str, pr_number: int) -> tuple[str, str]:
    url = f"https://github.com/adk-smoke/fixture-{nonce}/pull/{pr_number}"
    return f"printf '%s\\n' '{url}'", url


def expected_followup_marker(fixture: Fixture, runtime: str, command: str, url: str, env: dict[str, str]) -> str:
    """The first sentence the fixture's own follow-up hook emits for the probe's output."""
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {"stdout": f"{url}\n", "stderr": "", "exit_code": 0},
        "cwd": str(fixture.repo),
    }
    try:
        result = subprocess.run(
            [sys.executable, str(fixture.engines / HOOK_ENGINE), "--runtime", runtime],
            cwd=fixture.repo,
            env=env,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal(f"the fixture's follow-up hook did not finish: {exc}") from exc
    try:
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise Refusal(
            f"the fixture's follow-up hook emitted no context for the probe's output under "
            f"--runtime {runtime}; the PostToolUse control is broken"
        ) from exc
    first, _, _ = context.partition(". ")
    return first if first.endswith(".") else first + "."


# ------------------------------------------------------------------ codex artifacts


def codex_thread_id(stdout_path: Path) -> str | None:
    for event in read_jsonl(stdout_path):
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            return event["thread_id"]
    return None


def rollout_cwd(path: Path) -> str | None:
    return session_meta(path).get("cwd")


def locate_rollout(home: Path, *, thread_id: str | None, cwd: Path, since: float) -> tuple[Path | None, str]:
    sessions = home / "sessions"
    if thread_id:
        matches = sorted(sessions.rglob(f"rollout-*{thread_id}.jsonl"))
        if len(matches) == 1:
            return matches[0], f"thread {thread_id}"
        return None, f"{len(matches)} rollouts for thread {thread_id} under the isolated home"
    candidates = [
        path
        for path in sessions.rglob("rollout-*.jsonl")
        if path.stat().st_mtime >= since and rollout_cwd(path) in {str(cwd), realpath(cwd)}
    ]
    if len(candidates) == 1:
        return candidates[0], "the one rollout started in the expected directory during the run"
    return None, f"{len(candidates)} rollouts started in the expected directory during the run"


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for part in content or []:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            parts.append(part["text"])
    return "\n".join(parts)


def rollout_view(entries: list[dict[str, Any]]) -> dict[str, Any]:
    meta: dict[str, Any] | None = None
    turns: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    world_states: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        kind = entry.get("type")
        payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
        item = payload.get("type")
        if kind == "session_meta" and meta is None:
            meta = payload
        elif kind == "turn_context":
            turns.append(payload)
        elif kind == "response_item" and item == "message":
            messages.append(
                {"index": index, "role": payload.get("role"), "text": _message_text(payload.get("content"))}
            )
        elif kind == "response_item" and item in ("function_call", "custom_tool_call", "local_shell_call"):
            calls.append({"index": index, "call_id": payload.get("call_id")})
        elif kind == "response_item" and item in ("function_call_output", "custom_tool_call_output"):
            outputs.append(
                {"index": index, "call_id": payload.get("call_id"), "text": json.dumps(payload.get("output"), sort_keys=True)}
            )
        elif kind == "event_msg":
            completed = payload.get("item") if isinstance(payload.get("item"), dict) else {}
            events.append(
                {"index": index, "type": item, "item_type": completed.get("type"), "text": json.dumps(payload, sort_keys=True)}
            )
        elif kind == "world_state" and isinstance(payload.get("state"), dict):
            world_states.append({"index": index, "state": payload["state"]})
    return {
        "meta": meta or {},
        "turns": turns,
        "messages": messages,
        "calls": calls,
        "outputs": outputs,
        "events": events,
        "world_states": world_states,
    }


def codex_session(view: dict[str, Any]) -> dict[str, Any]:
    meta = view["meta"]
    turn = view["turns"][0] if view["turns"] else {}
    sandbox = turn.get("sandbox_policy")
    if isinstance(sandbox, dict):
        sandbox = sandbox.get("type") or sandbox.get("mode")
    return {
        "observer": "rollout session_meta and first turn_context",
        "session_id": meta.get("id"),
        "executing_version": meta.get("cli_version"),
        "originator": meta.get("originator"),
        "source": meta.get("source"),
        "cwd": meta.get("cwd"),
        "model": turn.get("model"),
        "effort": turn.get("effort"),
        "approval_policy": turn.get("approval_policy"),
        "sandbox": sandbox,
    }


def check_agents_block(view: dict[str, Any], repo: Path, agents_md: bytes) -> tuple[bool, dict[str, Any]]:
    blocks = []
    for message in view["messages"]:
        if message["role"] != "user":
            continue
        match = AGENTS_BLOCK.match(message["text"])
        if not match:
            continue
        body = match.group("body").encode()
        blocks.append(
            {
                "index": message["index"],
                "shape": "user message",
                "dir": match.group("dir"),
                "dir_is_fixture": realpath(match.group("dir")) == realpath(repo),
                "body_sha256": sha256_bytes(body),
                "body_equals_fixture": body == agents_md,
            }
        )
    for snapshot in view.get("world_states", []):
        injected = snapshot["state"].get("agents_md")
        if not isinstance(injected, dict) or not isinstance(injected.get("text"), str):
            continue
        body = injected["text"].encode()
        directory = str(injected.get("directory"))
        blocks.append(
            {
                "index": snapshot["index"],
                "shape": "world_state.agents_md",
                "dir": directory,
                "dir_is_fixture": realpath(directory) == realpath(repo),
                "body_sha256": sha256_bytes(body),
                "body_equals_fixture": body == agents_md,
            }
        )
    ok = any(block["dir_is_fixture"] and block["body_equals_fixture"] for block in blocks)
    evidence: dict[str, Any] = {
        "observer": "rollout `world_state` state.agents_md, or a user message `# AGENTS.md instructions for` block",
        "fixture_agents_md_sha256": sha256_bytes(agents_md),
        "blocks": blocks,
    }
    if not ok:
        evidence["user_message_heads"] = message_heads(view, "user")
    return ok, evidence


def listed_skill_files(text: str) -> set[str]:
    roots = {match.group("alias"): match.group("path") for match in SKILL_ROOT.finditer(text)}
    files: set[str] = set()
    for match in SKILL_FILE.finditer(text):
        name = match.group("file").strip()
        alias, _, rest = name.partition("/")
        if alias in roots and rest:
            files.add(realpath(Path(roots[alias]) / rest))
        elif name.startswith("/"):
            files.add(realpath(name))
    return files


def check_skills(view: dict[str, Any], expected: list[str]) -> tuple[bool, dict[str, Any]]:
    listed: set[str] = set()
    blocks = 0
    for message in view["messages"]:
        if message["role"] == "developer" and "<skills_instructions>" in message["text"]:
            blocks += 1
            listed |= listed_skill_files(message["text"])
    missing = [path for path in expected if path not in listed]
    ok = bool(expected) and not missing
    evidence: dict[str, Any] = {
        "observer": "rollout response_item message, role developer, `<skills_instructions>` block",
        "skills_blocks": blocks,
        "expected": expected,
        "missing": missing,
    }
    if not blocks:
        evidence["developer_message_heads"] = message_heads(view, "developer")
    return ok, evidence


def message_heads(view: dict[str, Any], role: str) -> list[str]:
    """The first line of each message in a role, bounded: what to read when a shape moves."""
    heads = []
    for message in view["messages"]:
        if message["role"] == role:
            first = message["text"].strip().splitlines()[0] if message["text"].strip() else ""
            heads.append(flatten(first))
    return heads


def review_child_sessions(home: Path, *, cwd: Path, since: float) -> list[Path]:
    """Rollouts of `codex exec review`'s reviewer: `source` `{"subagent": "review"}`."""
    children = []
    for path in sorted((home / "sessions").rglob("rollout-*.jsonl")):
        if path.stat().st_mtime < since:
            continue
        meta = session_meta(path)
        if meta.get("source") == {"subagent": "review"} and realpath(str(meta.get("cwd"))) == realpath(cwd):
            children.append(path)
    return children


def session_meta(path: Path) -> dict[str, Any]:
    """A rollout's `session_meta` payload, read from its opening lines alone."""
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in itertools.islice(handle, 5):
                entry = _json_or_none(line)
                if isinstance(entry, dict) and entry.get("type") == "session_meta" and isinstance(entry.get("payload"), dict):
                    return entry["payload"]
    except OSError:
        pass
    return {}


def review_markers(view: dict[str, Any]) -> list[str]:
    """Review-mode names from event types and completed-item types.

    0.153.4 records `codex exec review` as `item_completed` events whose items are
    `EnteredReviewMode` and `ExitedReviewMode`, not as event types of their own.
    """
    return sorted(
        {
            str(name)
            for event in view["events"]
            for name in (event["type"], event.get("item_type"))
            if name and "review" in str(name).lower()
        }
    )


def find_injected(view: dict[str, Any], needle: str, *, after: int = -1) -> dict[str, Any] | None:
    """The first non-assistant message after `after` that carries `needle` verbatim.

    Assistant messages are excluded: a model repeating the text proves nothing about
    the hook that was supposed to produce it.
    """
    for message in view["messages"]:
        if message["index"] > after and message["role"] != "assistant" and needle in message["text"]:
            return {"index": message["index"], "role": message["role"]}
    return None


def first_output_with(view: dict[str, Any], needle: str) -> int | None:
    """Index of the first tool output carrying `needle` — never a model-authored event."""
    indices = [item["index"] for item in view["outputs"] if needle in item["text"]]
    return min(indices) if indices else None


def call_answered_by(view: dict[str, Any], output_index: int) -> int | None:
    """Index of the tool call whose output sits at `output_index`, matched by call id.

    0.153.4 writes PostToolUse context between a call and its output, so a hook's
    answer is ordered after the call, not after the output.
    """
    output = next((item for item in view["outputs"] if item["index"] == output_index), None)
    if output is None or not output.get("call_id"):
        return None
    calls = [call["index"] for call in view["calls"] if call["call_id"] == output["call_id"]]
    return min(calls) if calls else None


def config_trust_entries(home: Path) -> dict[str, list[str]]:
    path = home / "config.toml"
    if not path.is_file():
        return {"projects": [], "hooks_state": []}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {"projects": ["<unreadable config.toml>"], "hooks_state": []}
    projects = data.get("projects") or {}
    hooks = (data.get("hooks") or {}).get("state") or {}
    return {
        "projects": sorted(
            f"{name} ({entry.get('trust_level')})" for name, entry in projects.items() if isinstance(entry, dict)
        ),
        "hooks_state": sorted(hooks),
    }


# ----------------------------------------------------------------- claude artifacts


def claude_init(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            return event
    return {}


def claude_result(events: list[dict[str, Any]]) -> dict[str, Any]:
    results = [event for event in events if event.get("type") == "result"]
    return results[-1] if results else {}


def claude_hook_events(events: list[dict[str, Any]], hook_event: str) -> list[dict[str, Any]]:
    found = []
    for index, event in enumerate(events):
        if event.get("type") != "system" or "hook" not in str(event.get("subtype", "")):
            continue
        name = event.get("hook_event") or event.get("hook_event_name") or event.get("event")
        if name == hook_event:
            found.append({"index": index, "subtype": event.get("subtype"), "strings": list(string_values(event))})
    return found


def string_values(value: Any) -> Any:
    """Every string inside `value`, and inside any string that is itself JSON.

    A hook's stdout can arrive as a JSON document inside a JSON event; matching on the
    decoded strings keeps an escape layer from hiding the text a row looks for.
    """
    if isinstance(value, str):
        yield value
        if value.lstrip().startswith(("{", "[")):
            yield from string_values(_json_or_none(value))
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from string_values(item)


def _json_or_none(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def mentions(event: dict[str, Any], needle: str) -> bool:
    return any(needle in text for text in event["strings"])


def claude_tool_call_for(events: list[dict[str, Any]], needle: str) -> tuple[int | None, int | None]:
    """(tool_use index, tool_result index) of the first tool result carrying `needle`.

    Only a `tool_result` counts — never the prompt or the model's own text. 2.1.287
    streams a PostToolUse hook's events between a `tool_use` and its `tool_result`,
    so a hook's answer is ordered after the call, which the result names by
    `tool_use_id`. The call index is None when no `tool_use` carries that id.
    """
    for result_index, event in enumerate(events):
        if event.get("type") != "user" or not isinstance(event.get("message"), dict):
            continue
        for part in event["message"].get("content") or []:
            if not (isinstance(part, dict) and part.get("type") == "tool_result"):
                continue
            if not any(needle in text for text in string_values(part.get("content"))):
                continue
            use_id = part.get("tool_use_id")
            for use_index, candidate in enumerate(events[:result_index]):
                message = candidate.get("message")
                if candidate.get("type") != "assistant" or not isinstance(message, dict):
                    continue
                for item in message.get("content") or []:
                    if isinstance(item, dict) and item.get("type") == "tool_use" and use_id and item.get("id") == use_id:
                        return use_index, result_index
            return None, result_index
    return None, None


def find_claude_transcript(config_dir: Path, session_id: str | None) -> Path | None:
    if not session_id:
        return None
    matches = sorted((config_dir / "projects").glob(f"*/{session_id}.jsonl"))
    return matches[0] if len(matches) == 1 else None


def claude_session(init: dict[str, Any], transcript: list[dict[str, Any]]) -> dict[str, Any]:
    versions = sorted({entry["version"] for entry in transcript if isinstance(entry.get("version"), str)})
    models = sorted(
        {
            entry["message"]["model"]
            for entry in transcript
            if entry.get("type") == "assistant"
            and isinstance(entry.get("message"), dict)
            and isinstance(entry["message"].get("model"), str)
            and not entry["message"]["model"].startswith("<")
        }
    )
    efforts = sorted(
        {
            str(entry["effort"])
            for entry in transcript
            if entry.get("type") == "assistant" and entry.get("effort") is not None
        }
    )
    return {
        "observer": "stream-json system/init and the session transcript",
        "session_id": init.get("session_id"),
        "executing_version": versions[0] if len(versions) == 1 else (versions or None),
        "init_version": init.get("claude_code_version"),
        "cwd": init.get("cwd"),
        "model": init.get("model"),
        "transcript_models": models,
        "transcript_efforts": efforts,
        "permission_mode": init.get("permissionMode"),
        "api_key_source": init.get("apiKeySource"),
    }


def entry_text(entry: dict[str, Any]) -> str:
    """The text of a transcript entry's message, whether a string or a list of parts."""
    message = entry.get("message")
    if not isinstance(message, dict):
        return ""
    return _message_text(message.get("content"))


def claude_subagents(transcript_path: Path | None) -> list[dict[str, Any]]:
    """Each subagent a session ran, read from its own transcript beside the session's.

    2.1.287 keeps them at `<session>/subagents/agent-<id>.jsonl`, each with a
    `.meta.json` naming its `agentType` — the agent definition it ran as.
    """
    if transcript_path is None:
        return []
    agents = []
    for path in sorted((transcript_path.parent / transcript_path.stem / "subagents").glob("agent-*.jsonl")):
        meta = _json_or_none(_read_text(path.with_name(path.name.removesuffix(".jsonl") + ".meta.json")))
        entries = read_jsonl(path)
        session = claude_session({}, entries)
        texts = [entry_text(entry) for entry in entries if entry.get("type") == "assistant"]
        agents.append(
            {
                "agent_type": meta.get("agentType") if isinstance(meta, dict) else None,
                "models": session["transcript_models"],
                "efforts": session["transcript_efforts"],
                "executing_version": session["executing_version"],
                "first_prompt": next((entry_text(e) for e in entries if e.get("type") == "user"), ""),
                "last_text": next((text for text in reversed(texts) if text.strip()), ""),
            }
        )
    return agents


def summarise_subagent(agent: dict[str, Any]) -> dict[str, Any]:
    """What the record keeps of a subagent: no prompt or report text, only their digests."""
    return {
        "agent_type": agent["agent_type"],
        "applied_models": agent["models"],
        "applied_efforts": agent["efforts"],
        "executing_version": agent["executing_version"],
        "prompt_sha256": sha256_bytes(agent["first_prompt"].encode()),
        "report_chars": len(agent["last_text"]),
    }


def pin_mismatch(session: dict[str, Any], pin: str) -> str | None:
    version = session.get("executing_version")
    if version == pin:
        return None
    return f"the executing runtime reported {version!r}, not the pinned {pin!r}"


# -------------------------------------------------------------------- preflight


def shell_version(binary: Path, env: dict[str, str]) -> str:
    """What the binary on disk says it is — the shell CLI, not the executing runtime."""
    try:
        result = subprocess.run(
            [str(binary), "--version"], env=env, capture_output=True, text=True, timeout=PREFLIGHT_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"<--version failed: {exc}>"
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0].strip() if lines else ""


def codex_preflight(binary: Path, pin: str, home: Path, env: dict[str, str]) -> tuple[dict[str, Any], str | None]:
    version = shell_version(binary, env)
    facts: dict[str, Any] = {"bin": str(binary), "realpath": realpath(binary), "shell_version": version, "pin": pin}
    if version != f"codex-cli {pin}":
        return facts, f"the shell CLI reports {version!r}, not the pinned `codex-cli {pin}`"
    try:
        status = subprocess.run(
            [str(binary), "login", "status"], env={**env, "CODEX_HOME": str(home)},
            capture_output=True, text=True, timeout=PREFLIGHT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return facts, f"`codex login status` under the isolated CODEX_HOME did not answer: {exc}"
    facts["logged_in"] = status.returncode == 0
    if status.returncode != 0:
        return facts, (
            "no credential: `codex login status` under the isolated CODEX_HOME reports not "
            "logged in; log in once with `CODEX_HOME=<codex-home> codex login`"
        )
    return facts, None


def claude_preflight(binary: Path, pin: str, config_dir: Path, env: dict[str, str]) -> tuple[dict[str, Any], str | None]:
    version = shell_version(binary, env)
    present = [key for key in CLAUDE_CREDENTIAL_ENV if os.environ.get(key)]
    facts: dict[str, Any] = {
        "bin": str(binary),
        "realpath": realpath(binary),
        "shell_version": version,
        "pin": pin,
        "credential_env_present": present,
    }
    if version != f"{pin} (Claude Code)":
        return facts, f"the shell CLI reports {version!r}, not the pinned `{pin} (Claude Code)`"
    try:
        status = subprocess.run(
            [str(binary), "auth", "status", "--json"],
            env={**env, "CLAUDE_CONFIG_DIR": str(config_dir)},
            capture_output=True,
            text=True,
            timeout=PREFLIGHT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return facts, f"`claude auth status` under the isolated CLAUDE_CONFIG_DIR did not answer: {exc}"
    report = _json_or_none(status.stdout)
    report = report if isinstance(report, dict) else {}
    facts["logged_in"] = bool(report.get("loggedIn"))
    facts["auth_method"] = report.get("authMethod")
    if not report.get("loggedIn"):
        if present:
            credential = f"{' and '.join(present)} {'is' if len(present) == 1 else 'are'} set but not accepted"
        else:
            credential = f"neither {' nor '.join(CLAUDE_CREDENTIAL_ENV)} is set in the runner's environment"
        return facts, (
            "no credential: `claude auth status` under the isolated CLAUDE_CONFIG_DIR reports "
            f"loggedIn false, and {credential}; log in once with "
            "`CLAUDE_CONFIG_DIR=<claude-config> claude auth login`, or supply one of those variables"
        )
    return facts, None


# -------------------------------------------------------------------- codex checks


def codex_exec_session(
    ctx: Context, binary: Path, home: Path, argv_tail: list[str], *, cwd: Path, prompt: str, name: str
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    """Run one `codex exec` child and return its invocation, rollout view and locator note."""
    env = {**ctx.base_env, "CODEX_HOME": str(home)}
    since = time.time() - 1
    invocation = run_child(
        [str(binary), *argv_tail], cwd=cwd, env=env, stdin_text=prompt, timeout=ctx.timeout,
        log_dir=ctx.log_dir, name=name,
    )
    rollout, note = locate_rollout(
        home, thread_id=codex_thread_id(Path(invocation["stdout"])), cwd=cwd, since=since
    )
    if rollout is None:
        return invocation, None, note
    return invocation, rollout_view(read_jsonl(rollout)), note


def codex_project_trust_override(repo: Path) -> list[str]:
    """A `-c` pair that trusts `repo` as a project for one invocation; nothing is written.

    An inline table rather than a dotted key, so a path holding a dot cannot be split
    into key segments.
    """
    return ["-c", f'projects={{{json.dumps(realpath(repo))}={{trust_level="trusted"}}}}']


def hooks_json_differs(repo: Path, kit_root: Path, revision: str) -> bool:
    """Whether the fixture's hook registration is anything but the revision's bytes."""
    committed = subprocess.run(["git", "show", f"{revision}:{CODEX_HOOKS}"], cwd=kit_root, capture_output=True)
    path = repo / CODEX_HOOKS
    return committed.returncode != 0 or not path.is_file() or path.read_bytes() != committed.stdout


def codex_hook_route(differs: bool, *, bypass: bool, project_trust: bool) -> dict[str, Any]:
    """The trust the hook probe runs under: none at all when the registration differs."""
    return {
        "project_trust": "per-invocation override" if project_trust and not differs else "none",
        "hook_trust": "per-invocation bypass" if bypass and not differs else "none",
        "hooks_json_differs": differs,
    }


def hook_trust_reason(route: dict[str, Any]) -> str | None:
    """Why the hook rows could not run under `route`, or None when both layers held.

    Codex trusts a hook at two layers: the project, whose `.codex/` it loads only once
    the path is trusted (#802 describes a trusted path loading a project's config and
    hooks), and each definition, which `--dangerously-bypass-hook-trust` waives for one
    invocation. The first live run passed the bypass without project trust and recorded
    no output from either hook.
    """
    if route["hooks_json_differs"]:
        return "hook trust refused: the fixture's .codex/hooks.json differs from the revision's bytes"
    if route["project_trust"] == "none":
        return (
            "project trust not established: the fixture is a new path to the isolated home and "
            "the runner grants no project trust; pass --allow-codex-project-trust for the hook probe"
        )
    if route["hook_trust"] == "none":
        return (
            "hook trust not established: the fixture's hook definitions are new to the isolated "
            "home and the runner grants no trust; pass --allow-codex-hook-trust-bypass for the hook probe"
        )
    return None


def run_codex(
    ctx: Context, rows: dict[str, Row], binary: Path, home: Path, pin: str, *, bypass: bool, project_trust: bool
) -> dict[str, Any]:
    trust_before = config_trust_entries(home)
    cheap = get(ctx.config, "models.runtime_mappings.codex.cheap")
    effort = ["-c", f"model_reasoning_effort={cheap}"] if cheap else []
    fixture = ctx.fixture
    command, url = probe_command(ctx.nonce, ctx.pr_number)

    # Hook probe: one session evidences instructions, skills and both hooks.
    # Equal by construction on the CLI path, since the fixture is extracted from the
    # revision; checked anyway, because the trust a route grants is to these bytes.
    route = codex_hook_route(
        hooks_json_differs(fixture.repo, ctx.kit_root, ctx.revision), bypass=bypass, project_trust=project_trust
    )
    trust_reason = hook_trust_reason(route)
    probe_argv = [
        "exec", "--json", "-C", str(fixture.repo), "-s", "read-only", *effort,
        "-o", str(ctx.log_dir / "codex-probe.last"),
        *(codex_project_trust_override(fixture.repo) if route["project_trust"] != "none" else []),
        *(["--dangerously-bypass-hook-trust"] if route["hook_trust"] != "none" else []), "-",
    ]
    invocation, view, note = codex_exec_session(
        ctx, binary, home, probe_argv, cwd=fixture.repo, prompt=probe_prompt(ctx, command), name="codex-probe"
    )
    probe_rows = [rows[key] for key in ("codex.instructions", "codex.skills", "codex.session_start", "codex.post_tool_use")]
    for row in probe_rows:
        row.invocations.append(invocation)
    if view is None:
        for row in probe_rows:
            row.set("failed", f"no rollout to read: {note} ({invocation_ok(invocation) or 'exit 0'})")
    else:
        session = codex_session(view)
        mismatch = pin_mismatch(session, pin)
        for row in probe_rows:
            row.session = session

        ok, evidence = check_agents_block(view, fixture.repo, fixture.agents_md)
        _finish(rows["codex.instructions"], ok, mismatch, evidence,
                "the injected AGENTS.md block names the fixture and equals its AGENTS.md byte for byte",
                "no injected AGENTS.md block both named the fixture and equalled its AGENTS.md")

        ok, evidence = check_skills(view, expected_codex_skills(fixture.repo))
        _finish(rows["codex.skills"], ok, mismatch, evidence,
                "every skill the parity declaration binds for Codex is listed in the injected skills block",
                "a declared Codex skill was not listed in the injected skills block")

        found = find_injected(view, ctx.budget_line)
        evidence = {
            "observer": "rollout response_item message carrying the budget tripwire line",
            "hook_trust_route": route,
            "expected_line": ctx.budget_line,
            "found": found,
        }
        if found:
            _finish(rows["codex.session_start"], True, mismatch, evidence,
                    "the tripwire line naming this run's over-budget count reached the session", "")
        elif trust_reason:
            rows["codex.session_start"].set("not-run", trust_reason, **evidence)
        else:
            rows["codex.session_start"].set(
                "failed", "both trust layers held for the probe, and the tripwire line never reached the session", **evidence
            )

        output_index = first_output_with(view, url)
        call_index = call_answered_by(view, output_index) if output_index is not None else None
        marker = ctx.followup_markers["codex"]
        # After the call when its id links it to the nonce output; after the output itself
        # otherwise, which is stricter and never earlier than the call.
        anchor = call_index if call_index is not None else output_index
        found = find_injected(view, marker, after=anchor) if anchor is not None else None
        evidence = {
            "observer": "rollout tool call whose output carries the nonce URL, then a context message with the hook's warning",
            "hook_trust_route": route,
            "nonce_url_output_index": output_index,
            "nonce_url_call_index": call_index,
            "expected_marker": marker,
            "found": found,
        }
        if found:
            _finish(rows["codex.post_tool_use"], True, mismatch, evidence,
                    "the follow-up hook's warning reached the session after the shell call that printed the nonce URL", "")
        elif trust_reason:
            rows["codex.post_tool_use"].set("not-run", trust_reason, **evidence)
        elif output_index is None:
            rows["codex.post_tool_use"].set("failed", "the session recorded no shell output carrying the nonce URL", **evidence)
        else:
            rows["codex.post_tool_use"].set(
                "failed", "both trust layers held for the probe, the shell call ran, and the hook's warning never reached the session", **evidence
            )

    # Native review, on the review branch against the protected branch.
    base = get(ctx.config, "vcs.protected_branch", "main")
    review_argv = ["exec", "review", "--json", "--base", base, *effort, "-o", str(ctx.log_dir / "codex-review.last")]
    review_since = time.time() - 1
    invocation, view, note = codex_exec_session(
        ctx, binary, home, review_argv, cwd=fixture.repo, prompt="", name="codex-review"
    )
    row = rows["codex.review"]
    row.invocations.append(invocation)
    last = _read_text(ctx.log_dir / "codex-review.last")
    if view is None:
        row.set("failed", f"no rollout to read: {note} ({invocation_ok(invocation) or 'exit 0'})")
    else:
        row.session = codex_session(view)
        # The reviewer's compute lives in the review's own child session; the parent
        # that carries the review-mode items records no turn context of its own.
        children = review_child_sessions(home, cwd=fixture.repo, since=review_since)
        row.session["reviewer"] = (
            codex_session(rollout_view(read_jsonl(children[0])))
            if len(children) == 1
            else {"note": f"{len(children)} review child sessions started in the fixture during the review"}
        )
        markers = review_markers(view)
        problem = invocation_ok(invocation)
        evidence = {
            "observer": "rollout event_msg and completed-item types naming review mode, and the last-message file",
            "review_events": markers,
            "reviewer_model": row.session["reviewer"].get("model"),
            "reviewer_effort": row.session["reviewer"].get("effort"),
            "last_message_chars": len(last),
            "last_message_first_line": flatten(last.strip().splitlines()[0]) if last.strip() else "",
        }
        ok = not problem and markers and last.strip()
        _finish(row, bool(ok), pin_mismatch(row.session, pin), evidence,
                "the rollout recorded review mode and the review returned its output",
                problem or ("the rollout recorded no review-mode event" if not markers else "the review returned no output"))

    run_codex_panel(ctx, rows["codex.panel"], binary, home, pin)
    run_lane(ctx, rows["codex.lane"], "codex", pin, {"CODEX_HOME": str(home)}, home=home)

    trust_after = config_trust_entries(home)
    return {
        "hook_trust_route": route,
        "projects_added": sorted(set(trust_after["projects"]) - set(trust_before["projects"])),
        "hooks_state_added": sorted(set(trust_after["hooks_state"]) - set(trust_before["hooks_state"])),
    }


def probe_prompt(ctx: Context, command: str) -> str:
    return (
        "This is an automated smoke test of the client, not a task. Run exactly one shell "
        "command, exactly as written, and nothing else:\n\n"
        f"{command}\n\n"
        "The URL it prints is a test string: do not open, query or act on it, and do not "
        "run any other command. After the command runs, reply with exactly "
        f"SMOKE-DONE-{ctx.nonce} and stop.\n"
    )


def _finish(row: Row, ok: bool, mismatch: str | None, evidence: dict[str, Any], passed: str, failed: str) -> None:
    if ok and mismatch:
        row.set("failed", f"{passed}, but {mismatch}", **evidence)
    elif ok:
        row.set("passed", passed, **evidence)
    else:
        row.set("failed", failed, **evidence)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def lens_tree(ctx: Context, name: str) -> Path:
    """A private clone at the review head, so no lens is handed a tree another uses."""
    tree = ctx.run_dir / name
    env = fixture_git_env(ctx.base_env)
    git(ctx.run_dir, "clone", "-q", "--no-hardlinks", str(ctx.fixture.origin), str(tree), env=env)
    git(tree, "checkout", "-q", "--detach", ctx.fixture.review_head, env=env)
    return tree


def panel_prompt(ctx: Context, tree: Path, lens: str, runtime: str) -> str:
    result = subprocess.run(
        [
            sys.executable, str(tree / ctx.fixture.engines.relative_to(ctx.fixture.repo) / "panel_prompt.py"), "--root", str(tree),
            "--lens", lens, "--head", ctx.fixture.review_head, "--branch", REVIEW_BRANCH,
            "--scratch", str(tree), "--runtime", runtime,
        ],
        cwd=tree,
        env=ctx.base_env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"panel_prompt.py exited {result.returncode}: {flatten(result.stderr)}")
    return result.stdout


def run_codex_panel(ctx: Context, row: Row, binary: Path, home: Path, pin: str) -> None:
    lenses = lens_roster(ctx.config)
    compute = get(ctx.config, "review.fallback_panel.lens_compute.codex", {}) or {}
    model, effort = compute.get("model"), compute.get("effort")
    if not lenses:
        row.set("failed", "review.fallback_panel.lenses is empty")
        return
    jobs = []
    for lens in lenses:
        try:
            tree = lens_tree(ctx, f"panel-codex-{lens}")
            prompt = panel_prompt(ctx, tree, lens, "codex")
        except (Refusal, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            row.set("failed", f"the {lens} prompt could not be assembled: {exc}")
            return
        argv = [
            "exec", "--json", "-C", str(tree), "-s", "read-only",
            *(["-m", model] if model else []),
            *(["-c", f"model_reasoning_effort={effort}"] if effort else []),
            "-o", str(ctx.log_dir / f"codex-lens-{lens}.last"), "-",
        ]
        jobs.append((lens, tree, argv, prompt))
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {
            lens: pool.submit(codex_exec_session, ctx, binary, home, argv, cwd=tree, prompt=prompt, name=f"codex-lens-{lens}")
            for lens, tree, argv, prompt in jobs
        }
    per_lens = []
    problems: list[str] = []
    for lens, *_ in jobs:
        invocation, view, note = futures[lens].result()
        row.invocations.append(invocation)
        report = _read_text(ctx.log_dir / f"codex-lens-{lens}.last")
        session = codex_session(view) if view is not None else None
        entry: dict[str, Any] = {
            "lens": lens,
            "configured_model": model,
            "configured_effort": effort,
            "report_chars": len(report),
            "report_names_review_head": ctx.fixture.review_head[:7] in report,
        }
        if session is not None:
            entry.update(
                applied_model=session["model"], applied_effort=session["effort"],
                executing_version=session["executing_version"],
            )
        per_lens.append(entry)
        problems += codex_lens_problems(
            lens, failure=invocation_ok(invocation), session=session, missing=note, report=report,
            model=model, effort=effort, head=ctx.fixture.review_head, pin=pin,
        )
    row.session = {"observer": "each lens's rollout turn_context", "lenses": per_lens}
    evidence = {"observer": "each lens's rollout turn_context and last-message file", "lenses": per_lens}
    if problems:
        row.set("failed", "; ".join(problems), **evidence)
    else:
        row.set(
            "passed",
            "every configured lens ran at its configured compute and returned a report naming the review head",
            **evidence,
        )


def codex_lens_problems(
    lens: str,
    *,
    failure: str | None,
    session: dict[str, Any] | None,
    missing: str,
    report: str,
    model: str | None,
    effort: str | None,
    head: str,
    pin: str,
) -> list[str]:
    """Why one Codex lens fails the panel row; empty when it passes.

    The head check is a liveness check: the rendered prompt carries the sha, so a
    report naming it shows the lens worked from this run's prompt, not that it read
    the diff.
    """
    problems = [f"{lens}: {failure}"] if failure else []
    if session is None:
        return [*problems, f"{lens}: no rollout ({missing})"]
    if model and session.get("model") != model:
        problems.append(f"{lens}: applied model {session.get('model')!r}, configured {model!r}")
    if effort and session.get("effort") != effort:
        problems.append(f"{lens}: applied effort {session.get('effort')!r}, configured {effort!r}")
    if head[:7] not in report:
        problems.append(f"{lens}: the report does not name the review head")
    if (mismatch := pin_mismatch(session, pin)):
        problems.append(f"{lens}: {mismatch}")
    return problems


# ---------------------------------------------------------------------------- lanes


def run_lane(ctx: Context, row: Row, runtime: str, pin: str, runtime_env: dict[str, str], *, home: Path) -> None:
    fixture = ctx.fixture
    sessions = ctx.run_dir / "sessions"
    sessions.mkdir(exist_ok=True)
    env = {**ctx.base_env, **runtime_env, "DEVKIT_SESSIONS_DIR": str(sessions)}
    scope = LANE_SCOPES[runtime]
    issue = run_child(
        ["bash", str(fixture.engines / "dev_session.sh"), "new", "--headless", scope,
         "--merge-class", "operator", "--runtime", runtime],
        cwd=fixture.repo, env=env, stdin_text="", timeout=300, log_dir=ctx.log_dir, name=f"{runtime}-lane-issue",
    )
    row.invocations.append(issue)
    if (problem := invocation_ok(issue)):
        row.set("failed", f"dev_session.sh new --headless {problem}")
        return
    try:
        descriptor = json.loads(Path(issue["stdout"]).read_text(encoding="utf-8"))
        session_dir = Path(descriptor["session_dir"])
        worktree = Path(descriptor["worktree"])
        descriptor_id = descriptor["descriptor_id"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        row.set("failed", f"dev_session.sh printed no usable descriptor: {exc}")
        return
    token = f"LANE-{ctx.nonce}"
    prompt_file = ctx.run_dir / f"{runtime}-lane-task.txt"
    prompt_file.write_text(
        "This is an automated read-only smoke task. Do not edit any file, commit, push, "
        "or open a pull request. Run `git rev-parse --abbrev-ref HEAD` once, then reply "
        f"with exactly one line: {token} followed by a space and the branch it printed.\n",
        encoding="utf-8",
    )
    since = time.time() - 1
    launch = run_child(
        [sys.executable, str(fixture.engines / "launch_lane.py"), "--descriptor",
         str(session_dir / "launch-descriptor.json"), "--prompt-file", str(prompt_file)],
        cwd=fixture.repo, env=env, stdin_text="", timeout=ctx.timeout, log_dir=ctx.log_dir, name=f"{runtime}-lane-launch",
    )
    row.invocations.append(launch)
    receipt_path = session_dir / f"launch-receipt-{descriptor_id}.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        receipt = {}
    terminal = receipt.get("terminal") or {}
    final_bytes = b""
    final_path = Path(terminal.get("final_message_path") or session_dir / f"launch-final-{descriptor_id}.txt")
    if final_path.is_file():
        final_bytes = final_path.read_bytes()
    text_bytes, claude_session_id = lane_final_text(runtime, final_bytes)
    final_digest = sha256_bytes(text_bytes) if text_bytes else None
    configured = (receipt.get("request") or {}).get("configured_command")
    evidence = {
        "observer": "launcher terminal receipt, its final message, and the lane's own session artifact",
        "receipt_status": receipt.get("status"),
        "receipt_returncode": terminal.get("returncode"),
        "receipt_final_text_sha256_matches": bool(final_digest) and final_digest == terminal.get("final_text_sha256"),
        "configured_command": configured,
        # The launcher resolves its command on its own trusted path, which need not be
        # the pinned binary's path; this is the file it ran.
        "configured_command_realpath": realpath(configured[0]) if isinstance(configured, list) and configured else None,
        "final_text_names_token": token in text_bytes.decode("utf-8", errors="replace"),
        "permission_denials": terminal.get("permission_denials"),
        "worktree": str(worktree),
    }
    if runtime == "codex":
        rollout, note = locate_rollout(home, thread_id=None, cwd=worktree, since=since)
        session = codex_session(rollout_view(read_jsonl(rollout))) if rollout else {"note": note}
    else:
        transcript = find_claude_transcript(home, claude_session_id)
        entries = read_jsonl(transcript) if transcript else []
        session = claude_session({"session_id": claude_session_id}, entries)
        session["cwd"] = next((entry.get("cwd") for entry in entries if entry.get("cwd")), None)
    row.session = session
    problems = lane_problems(
        launch_failure=invocation_ok(launch), receipt=receipt, text_bytes=text_bytes, token=token,
        session=session, worktree=worktree, pin=pin,
    )
    if problems:
        row.set("failed", "; ".join(problems), **evidence)
    else:
        row.set("passed", "the launcher completed the lane in its worktree and bound the final text", **evidence)


def lane_final_text(runtime: str, final_bytes: bytes) -> tuple[bytes, str | None]:
    """The text a lane's receipt digests, as the launcher extracts it, and Claude's session.

    The last-message file's raw bytes for Codex; for Claude, the `result` string of the
    one JSON object `--output-format json` printed, encoded as UTF-8.
    """
    if runtime != "claude":
        return final_bytes, None
    final_object = _json_or_none(final_bytes.decode("utf-8", errors="replace").strip())
    if not isinstance(final_object, dict):
        return b"", None
    session_id = final_object.get("session_id")
    return str(final_object.get("result", "")).encode("utf-8"), session_id if isinstance(session_id, str) else None


def lane_problems(
    *,
    launch_failure: str | None,
    receipt: dict[str, Any],
    text_bytes: bytes,
    token: str,
    session: dict[str, Any],
    worktree: Path,
    pin: str,
) -> list[str]:
    """Why a lane fails its row; empty when it passes."""
    terminal = receipt.get("terminal") or {}
    problems = [f"launch_lane.py {launch_failure}"] if launch_failure else []
    if receipt.get("status") != "completed":
        problems.append(f"receipt status {receipt.get('status')!r}")
    if not text_bytes or sha256_bytes(text_bytes) != terminal.get("final_text_sha256"):
        problems.append("the final text is not the one the receipt binds")
    if token not in text_bytes.decode("utf-8", errors="replace"):
        problems.append("the final text does not carry the task token")
    if session.get("cwd") and realpath(session["cwd"]) != realpath(worktree):
        problems.append("the lane session ran outside the descriptor worktree")
    if not session.get("executing_version"):
        problems.append("no lane session artifact recorded an executing version")
    elif (mismatch := pin_mismatch(session, pin)):
        problems.append(mismatch)
    return problems


# ------------------------------------------------------------------- claude checks


def claude_stream_session(
    ctx: Context, binary: Path, config_dir: Path, argv_tail: list[str], *, cwd: Path, prompt: str, name: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], Path | None]:
    env = {**ctx.base_env, "CLAUDE_CONFIG_DIR": str(config_dir)}
    invocation = run_child(
        [str(binary), *argv_tail], cwd=cwd, env=env, stdin_text=prompt, timeout=ctx.timeout,
        log_dir=ctx.log_dir, name=name,
    )
    events = read_jsonl(Path(invocation["stdout"]))
    session_id = claude_init(events).get("session_id") or claude_result(events).get("session_id")
    transcript = find_claude_transcript(config_dir, session_id)
    return invocation, events, read_jsonl(transcript) if transcript else [], transcript


def run_claude(ctx: Context, rows: dict[str, Row], binary: Path, config_dir: Path, pin: str) -> None:
    fixture = ctx.fixture
    command, url = probe_command(ctx.nonce, ctx.pr_number)
    cheap = get(ctx.config, "models.runtime_mappings.claude.cheap")
    observer_log = ctx.run_dir / "claude-instructions-loaded.jsonl"
    observer = {
        "hooks": {
            "InstructionsLoaded": [
                {"hooks": [{"type": "command", "command": f"{{ cat; printf '\\n'; }} >> {shlex.quote(str(observer_log))}", "timeout": 10}]}
            ]
        }
    }
    probe_argv = [
        "-p", "--output-format", "stream-json", "--verbose", "--include-hook-events",
        "--setting-sources", "project", "--permission-mode", "dontAsk",
        "--settings", json.dumps(observer), *(["--model", cheap] if cheap else []),
        "--allowedTools", "Bash(printf:*)",
    ]
    invocation, events, transcript, _ = claude_stream_session(
        ctx, binary, config_dir, probe_argv, cwd=fixture.repo, prompt=probe_prompt(ctx, command), name="claude-probe"
    )
    init = claude_init(events)
    session = claude_session(init, transcript)
    mismatch = pin_mismatch(session, pin)
    probe_rows = [rows[key] for key in ("claude.instructions", "claude.commands", "claude.session_start", "claude.post_tool_use")]
    for row in probe_rows:
        row.invocations.append(invocation)
        row.session = session
    if not init:
        for row in probe_rows:
            row.set("failed", f"the session emitted no init event ({invocation_ok(invocation) or 'exit 0'})")
    else:
        loaded = [entry for entry in read_jsonl(observer_log) if entry.get("hook_event_name") == "InstructionsLoaded"]
        wanted = [realpath(fixture.repo / "CLAUDE.md"), realpath(fixture.repo / "AGENTS.md")]
        evidence = {
            "observer": "an InstructionsLoaded hook passed with --settings, recording the runtime's own hook input",
            "expected": wanted,
            "loaded": [
                {"file_path": entry.get("file_path"), "memory_type": entry.get("memory_type"), "load_reason": entry.get("load_reason")}
                for entry in loaded
            ],
        }
        _finish(rows["claude.instructions"], claude_instructions_ok(loaded, fixture.repo), mismatch, evidence,
                "the runtime loaded the fixture's CLAUDE.md, and AGENTS.md as its import",
                "the runtime did not report loading the fixture's CLAUDE.md, and AGENTS.md as its import")

        expected_commands = expected_claude_commands(fixture.repo)
        expected_agents = lens_roster(ctx.config)
        missing_commands, missing_agents = claude_missing(init, expected_commands, expected_agents)
        evidence = {
            "observer": "stream-json system/init slash_commands and agents",
            "missing_commands": missing_commands,
            "missing_agents": missing_agents,
            "expected_commands": expected_commands,
            "expected_agents": expected_agents,
        }
        _finish(rows["claude.commands"], not evidence["missing_commands"] and not evidence["missing_agents"], mismatch, evidence,
                "every declared command and every configured lens agent was loaded",
                "a declared command or a configured lens agent was not loaded")

        starts = claude_hook_events(events, "SessionStart")
        hit = next((event for event in starts if mentions(event, ctx.budget_line)), None)
        evidence = {
            "observer": "stream-json hook events (--include-hook-events) for SessionStart",
            "session_start_events": [{"index": event["index"], "subtype": event["subtype"]} for event in starts],
            "expected_line": ctx.budget_line,
            "found": {"index": hit["index"], "subtype": hit["subtype"]} if hit else None,
        }
        _finish(rows["claude.session_start"], hit is not None, mismatch, evidence,
                "the tripwire line naming this run's over-budget count was the SessionStart hook's output",
                "no SessionStart hook event carried the tripwire line" if starts else "no SessionStart hook event was emitted")

        marker = ctx.followup_markers["claude"]
        posts = claude_hook_events(events, "PostToolUse")
        use_index, result_index = claude_tool_call_for(events, url)
        # After the call when the result names it; after the result itself otherwise,
        # which is stricter and never earlier than the call.
        anchor = use_index if use_index is not None else result_index
        hit = next(
            (event for event in posts if anchor is not None and event["index"] > anchor and mentions(event, marker)),
            None,
        )
        evidence = {
            "observer": "stream-json tool_use and the tool_result carrying the nonce URL, then PostToolUse hook events",
            "nonce_url_tool_use_index": use_index,
            "nonce_url_tool_result_index": result_index,
            "post_tool_use_events": [{"index": event["index"], "subtype": event["subtype"]} for event in posts],
            "expected_marker": marker,
            "found": {"index": hit["index"], "subtype": hit["subtype"]} if hit else None,
        }
        _finish(rows["claude.post_tool_use"], hit is not None, mismatch, evidence,
                "a PostToolUse hook event after the shell call that printed the nonce URL carried the hook's warning",
                "no tool result carried the nonce URL" if result_index is None
                else "no PostToolUse hook event after that shell call carried the hook's warning")

    # The configured review command, on the review branch.
    review_command = get(ctx.config, "review.fallback_commands.claude")
    row = rows["claude.review"]
    if not review_command:
        row.set("not-run", "review.fallback_commands.claude is not configured")
    else:
        argv = [
            "-p", "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
            "--permission-mode", "dontAsk", "--allowedTools", ",".join(CLAUDE_READ_ONLY_GIT), "--", review_command,
        ]
        invocation, events, transcript, transcript_path = claude_stream_session(
            ctx, binary, config_dir, argv, cwd=fixture.repo, prompt="", name="claude-review"
        )
        row.invocations.append(invocation)
        init = claude_init(events)
        row.session = claude_session(init, transcript)
        result = claude_result(events)
        name = review_command.lstrip("/").split()[0]
        listed = name in {str(item).lstrip("/") for item in init.get("slash_commands") or []}
        # 2.1.287 records a command as the user's literal text followed by a
        # `local_command` system entry; an older client wrapped it in `<command-name>`.
        invoked = any(
            (entry.get("type") == "user" and entry_text(entry).strip() == review_command.strip())
            or f"<command-name>/{name}</command-name>" in json.dumps(entry)
            for entry in transcript
        )
        local = [entry for entry in transcript if entry.get("type") == "system" and entry.get("subtype") == "local_command"]
        subagents = claude_subagents(transcript_path)
        row.session["subagents"] = [summarise_subagent(agent) for agent in subagents]
        text = str(result.get("result") or "")
        evidence = {
            "observer": "stream-json init and result, and the transcript's record of the invocation and its subagents",
            "command": review_command,
            "listed_in_init": listed,
            "invocation_in_transcript": invoked,
            "local_command_recorded": bool(local),
            "result_is_error": result.get("is_error"),
            "result_chars": len(text),
            "subagents": row.session["subagents"],
        }
        problem = invocation_ok(invocation)
        ok = claude_review_ok(problem=problem, listed=listed, invoked=invoked, result=result)
        _finish(row, ok, pin_mismatch(row.session, pin), evidence,
                "the configured review command was invoked, by the transcript's record, and returned a non-error result",
                problem or "the configured review command was not listed, not invoked, or returned no non-error result")

    run_claude_panel(ctx, rows["claude.panel"], binary, config_dir, pin)
    run_lane(ctx, rows["claude.lane"], "claude", pin, {"CLAUDE_CONFIG_DIR": str(config_dir)}, home=config_dir)


def claude_instructions_ok(loaded: list[dict[str, Any]], repo: Path) -> bool:
    """CLAUDE.md loaded, and AGENTS.md loaded as its import (`load_reason` `include`)."""
    claude_md, agents_md = realpath(repo / "CLAUDE.md"), realpath(repo / "AGENTS.md")
    paths = {
        (realpath(entry["file_path"]), entry.get("load_reason"))
        for entry in loaded
        if isinstance(entry.get("file_path"), str)
    }
    return any(path == claude_md for path, _ in paths) and (agents_md, "include") in paths


def claude_missing(
    init: dict[str, Any], expected_commands: list[str], expected_agents: list[str]
) -> tuple[list[str], list[str]]:
    """The declared commands and configured lens agents the init event does not list."""
    commands = {str(name).lstrip("/") for name in init.get("slash_commands") or []}
    agents = {str(name) for name in init.get("agents") or []}
    return (
        [name for name in expected_commands if name not in commands],
        [name for name in expected_agents if name not in agents],
    )


def claude_review_ok(*, problem: str | None, listed: bool, invoked: bool, result: dict[str, Any]) -> bool:
    """The command exited cleanly, was listed and invoked, and returned non-error text."""
    text = str(result.get("result") or "")
    return problem is None and listed and invoked and result.get("is_error") is False and bool(text.strip())


LENS_BEGIN = "-----BEGIN LENS PROMPT-----"
LENS_END = "-----END LENS PROMPT-----"


def delegation_prompt(lens: str, prompt: str) -> str:
    """The cockpit's half of the documented Claude route: launch the lens as its agent.

    `fallback-review-panel.md` makes `lens_compute.claude` mechanical only through the
    agent definition, applied when the cockpit delegates to the agent named after the
    lens; a session started with `--agent` is a different mechanism. So a parent
    session delegates, and the row reads the subagent's own transcript.
    """
    return (
        f"Launch the `{lens}` agent with your Agent tool. Give it, as its prompt, the text "
        "between the two marker lines below, exactly and in full, without the marker lines. "
        "Do not review anything yourself. When the agent returns, reply with exactly "
        f"LENS-DONE and nothing else.\n{LENS_BEGIN}\n{prompt}\n{LENS_END}\n"
    )


def run_claude_panel(ctx: Context, row: Row, binary: Path, config_dir: Path, pin: str) -> None:
    lenses = lens_roster(ctx.config)
    compute = get(ctx.config, "review.fallback_panel.lens_compute.claude", {}) or {}
    model, effort = compute.get("model"), compute.get("effort")
    if not lenses:
        row.set("failed", "review.fallback_panel.lenses is empty")
        return
    jobs = []
    for lens in lenses:
        try:
            tree = lens_tree(ctx, f"panel-claude-{lens}")
            prompt = panel_prompt(ctx, tree, lens, "claude")
        except (Refusal, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            row.set("failed", f"the {lens} prompt could not be assembled: {exc}")
            return
        argv = [
            "-p", "--output-format", "stream-json", "--verbose",
            "--setting-sources", "project", "--permission-mode", "dontAsk",
            "--allowedTools", ",".join(CLAUDE_READ_ONLY_GIT),
        ]
        jobs.append((lens, tree, argv, prompt))
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {
            lens: pool.submit(
                claude_stream_session, ctx, binary, config_dir, argv, cwd=tree,
                prompt=delegation_prompt(lens, prompt), name=f"claude-lens-{lens}",
            )
            for lens, tree, argv, prompt in jobs
        }
    per_lens = []
    problems: list[str] = []
    for lens, _tree, _argv, prompt in jobs:
        invocation, events, transcript, transcript_path = futures[lens].result()
        row.invocations.append(invocation)
        parent = claude_session(claude_init(events), transcript)
        agent = lens_agent(claude_subagents(transcript_path), lens)
        entry: dict[str, Any] = {
            "lens": lens,
            "configured_model": model,
            "configured_effort": effort,
            "parent_executing_version": parent["executing_version"],
            "lens_agent_launched": agent is not None,
        }
        if agent is not None:
            entry.update(summarise_subagent(agent))
            entry["prompt_verbatim"] = agent["first_prompt"].strip() == prompt.strip()
            entry["report_names_review_head"] = ctx.fixture.review_head[:7] in agent["last_text"]
        per_lens.append(entry)
        problems += claude_lens_problems(
            lens, failure=invocation_ok(invocation), agent=agent, prompt=prompt,
            model=model, effort=effort, head=ctx.fixture.review_head, pin=pin,
        )
    row.session = {"observer": "each lens agent's own subagent transcript", "lenses": per_lens}
    evidence = {
        "observer": "each lens agent's subagent transcript and its .meta.json agent type",
        "lenses": per_lens,
    }
    if problems:
        row.set("failed", "; ".join(problems), **evidence)
    else:
        row.set(
            "passed",
            "each configured lens ran as its agent definition, on the rendered prompt, at its configured "
            "compute, and returned a report naming the review head",
            **evidence,
        )


def lens_agent(agents: list[dict[str, Any]], lens: str) -> dict[str, Any] | None:
    """The subagent that ran as the lens's own definition, by its `.meta.json` agent type."""
    return next((agent for agent in agents if agent["agent_type"] == lens), None)


def claude_lens_problems(
    lens: str,
    *,
    failure: str | None,
    agent: dict[str, Any] | None,
    prompt: str,
    model: str | None,
    effort: str | None,
    head: str,
    pin: str,
) -> list[str]:
    """Why one Claude lens fails the panel row; empty when it passes.

    The configured model is an alias, so the check is that every applied model id
    names that family; the record keeps the resolved ids. The head check is the same
    liveness check as the Codex panel's.
    """
    problems = [f"{lens}: {failure}"] if failure else []
    if agent is None:
        return [*problems, f"{lens}: the parent session launched no `{lens}` agent"]
    if agent["first_prompt"].strip() != prompt.strip():
        problems.append(f"{lens}: the agent's prompt is not the one panel_prompt.py rendered")
    if model and not (agent["models"] and all(model in applied for applied in agent["models"])):
        problems.append(f"{lens}: applied models {agent['models']!r}, configured {model!r}")
    if effort and agent["efforts"] != [str(effort)]:
        problems.append(f"{lens}: applied efforts {agent['efforts']!r}, configured {effort!r}")
    if head[:7] not in agent["last_text"]:
        problems.append(f"{lens}: the report does not name the review head")
    if (mismatch := pin_mismatch(agent, pin)):
        problems.append(f"{lens}: {mismatch}")
    return problems


# ------------------------------------------------------------------------ record


def placeholders(pairs: list[tuple[Path | str | None, str]]) -> list[tuple[str, str]]:
    table: dict[str, str] = {}
    for path, token in pairs:
        if not path:
            continue
        for form in {str(path), realpath(path)}:
            table.setdefault(form.rstrip("/"), token)
    return sorted(table.items(), key=lambda item: len(item[0]), reverse=True)


def redact(value: Any, table: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        for prefix, token in table:
            value = value.replace(prefix, token)
        return value
    if isinstance(value, list):
        return [redact(item, table) for item in value]
    if isinstance(value, dict):
        return {redact(key, table): redact(item, table) for key, item in value.items()}
    return value


def finalize_record(record: dict[str, Any], table: list[tuple[str, str]]) -> dict[str, Any]:
    """Redact, then bound: a string cut before redaction can end inside a private path."""
    return bound_strings(redact(record, table))


def bound_strings(value: Any, limit: int = RECORD_STRING_LIMIT) -> Any:
    """Cut every string in `value` to `limit`; run it on a record already redacted."""
    if isinstance(value, str):
        return value if len(value) <= limit else value[: limit - 1] + "…"
    if isinstance(value, list):
        return [bound_strings(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: bound_strings(item, limit) for key, item in value.items()}
    return value


def summarise(rows: dict[str, Row]) -> tuple[dict[str, list[str]], int]:
    summary = {status: [row.id for row in rows.values() if row.status == status] for status in ("passed", "failed", "not-run")}
    if summary["failed"]:
        return summary, EXIT_FAILED
    if summary["not-run"]:
        return summary, EXIT_INCOMPLETE
    return summary, EXIT_PASSED


def render_markdown(record: dict[str, Any]) -> str:
    kit = record["kit"]
    lines = [
        f"# Runtime smoke record — {record['started_at'][:10]}",
        "",
        f"Written by `{kit['harness']}` at kit revision `{kit['revision']}`, run `{record['run_id']}`, "
        f"started {record['started_at']} and finished {record['finished_at']} (UTC). "
        "Every row below is an observation at the clients and revision named here.",
        "",
        f"Invocation, as the runner's arguments, under `{record.get('interpreter', '—')}`:",
        "",
        "```text",
        " ".join(shlex.quote(part) for part in record["invocation"]),
        "```",
        "",
        "## Clients",
        "",
        "| Runtime | Binary | Shell `--version` | Pin | Executing runtime, per row | Preflight |",
        "|---|---|---|---|---|---|",
    ]
    for runtime in RUNTIMES:
        client = record["clients"].get(runtime) or {}
        executing = sorted(
            {
                str(row["session"].get("executing_version"))
                for row in record["rows"]
                if row["runtime"] == runtime and row["session"].get("executing_version")
            }
        )
        lines.append(
            f"| {runtime} | `{client.get('realpath', '—')}` | `{client.get('shell_version', '—')}` | "
            f"`{client.get('pin', '—')}` | {', '.join(f'`{item}`' for item in executing) or '—'} | "
            f"{client.get('preflight', '—')} |"
        )
    lines += ["", "## Results", "", "| Row | Check | Result | Evidence or reason |", "|---|---|---|---|"]
    for row in record["rows"]:
        lines.append(f"| `{row['id']}` | {row['check']} | **{row['status']}** | {row['reason'].replace('|', '/')} |")
    observations = record["observations"]
    lines += [
        "",
        "## Fixture and observations",
        "",
        f"- Fixture: `{record['fixture']['main_head']}` (the revision's tree plus the controls commit), "
        f"review head `{record['fixture']['review_head']}` on `{REVIEW_BRANCH}`.",
        f"- SessionStart control: `{record['fixture']['friction_log']}` committed at "
        f"{record['fixture']['friction_lines']} lines against a budget of {record['fixture']['friction_budget']}.",
        f"- Codex hook probe trust: {render_route(observations.get('codex', {}).get('hook_trust_route'))}.",
        f"- Trusted-project entries the run added to the isolated Codex home (#802): "
        f"{', '.join(f'`{item}`' for item in observations.get('codex', {}).get('projects_added', [])) or 'none'}.",
        f"- Hook-state entries the run added to the isolated Codex home: "
        f"{', '.join(f'`{item}`' for item in observations.get('codex', {}).get('hooks_state_added', [])) or 'none'}.",
        f"- Instruction files above the fixture, which a client walking upward could also load: "
        f"{', '.join(f'`{item}`' for item in observations.get('ancestor_instruction_files', [])) or 'none'}.",
        "",
        "`record.json` beside this file carries each row's evidence fields, the session fields read "
        "from the runtime's artifacts, and every invocation with its exit status and timeout.",
        "",
    ]
    return "\n".join(lines)


def render_route(route: Any) -> str:
    if not isinstance(route, dict):
        return "—"
    return f"project trust {route.get('project_trust')}; definition trust {route.get('hook_trust')}"


def ancestor_instruction_files(start: Path) -> list[str]:
    found = []
    for parent in Path(realpath(start)).parents:
        for name in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "CLAUDE.local.md"):
            if (parent / name).is_file():
                found.append(str(parent / name))
    return found


# --------------------------------------------------------------------------- main


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the kit's on-demand runtime smoke tests (#879).")
    parser.add_argument("--work-root", required=True, type=Path, help="existing directory; each run creates a new directory in it")
    parser.add_argument("--out", required=True, type=Path, help="new or empty directory for record.json and record.md")
    parser.add_argument("--revision", default="HEAD", help="kit revision to test (default: HEAD)")
    parser.add_argument("--runtime", action="append", choices=RUNTIMES, help="limit to one runtime (repeatable; default both)")
    parser.add_argument("--codex-bin", type=Path, help="absolute path of the pinned Codex binary")
    parser.add_argument("--codex-version", help="the pin: the exact version `--version` must report")
    parser.add_argument("--codex-home", type=Path, help="isolated CODEX_HOME, provisioned and logged in by the operator")
    parser.add_argument("--allow-codex-project-trust", action="store_true",
                        help="operator authorization to trust the fixture path for the hook probe alone (-c override)")
    parser.add_argument("--allow-codex-hook-trust-bypass", action="store_true",
                        help="operator authorization to pass --dangerously-bypass-hook-trust to the hook probe")
    parser.add_argument("--claude-bin", type=Path, help="absolute path of the pinned Claude Code binary")
    parser.add_argument("--claude-version", help="the pin: the exact version `--version` must report")
    parser.add_argument("--claude-config-dir", type=Path, help="isolated CLAUDE_CONFIG_DIR, provisioned by the operator")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds each client child may run (default 1800)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)
    started_at = utc_now()
    previous = signal.signal(signal.SIGTERM, _interrupt)
    try:
        kit_root = repo_root(SCRIPT_PATH)
        revision = resolve_revision(kit_root, args.revision)
        harness = verify_harness(kit_root, revision)
        record = run(args, kit_root, revision, harness, started_at, raw_argv)
    except Refusal as exc:
        print(f"runtime_smoke: refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except KeyboardInterrupt:
        stop_live_children()
        print(f"runtime_smoke: interrupted; every client it started is stopped; {left_at(args.out)}", file=sys.stderr)
        return EXIT_ABORTED
    except Exception as exc:  # the runner's own failure is never a row result
        stop_live_children()
        print(f"runtime_smoke: failed: {type(exc).__name__}: {exc}; {left_at(args.out)}", file=sys.stderr)
        return EXIT_ABORTED
    finally:
        signal.signal(signal.SIGTERM, previous)
    summary = record["summary"]
    for status in ("passed", "failed", "not-run"):
        print(f"{status}: {', '.join(summary[status]) or '-'}")
    print(f"record: {args.out / 'record.md'}")
    return record["exit_status"]


def left_at(out: Path) -> str:
    """What a run that stopped left at `--out`, read from the disk rather than assumed."""
    if (out / "record.json").is_file():
        return "the record at --out was complete before the run stopped"
    return "no record was written to --out"


def run(
    args: argparse.Namespace,
    kit_root: Path,
    revision: str,
    harness: dict[str, str],
    started_at: str,
    raw_argv: list[str],
) -> dict[str, Any]:
    if args.timeout <= 0:
        raise Refusal("--timeout must be positive")
    work_root = args.work_root
    if not (work_root.is_absolute() and work_root.is_dir()):
        raise Refusal("--work-root must be an existing absolute directory")
    if Path(realpath(work_root)).is_relative_to(realpath(kit_root)):
        raise Refusal("--work-root must be outside the kit checkout, or Claude would also load the kit's CLAUDE.md")
    out = args.out
    if not out.is_absolute():
        raise Refusal("--out must be an absolute path")
    if not out.parent.is_dir():
        raise Refusal("--out must be in an existing directory")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refusal("--out must be a new or empty directory; the runner overwrites no record")
    selected = args.runtime or list(RUNTIMES)

    clients: dict[str, dict[str, Any]] = {}
    blocked: dict[str, str] = {}
    base_env = scrubbed_environment()
    homes: dict[str, Path] = {}
    pins: dict[str, str] = {}
    binaries: dict[str, Path] = {}
    for runtime in RUNTIMES:
        binary, pin, home = (
            (args.codex_bin, args.codex_version, args.codex_home)
            if runtime == "codex"
            else (args.claude_bin, args.claude_version, args.claude_config_dir)
        )
        if runtime not in selected:
            blocked[runtime] = "not selected for this run (--runtime)"
            continue
        if not (binary and pin and home):
            blocked[runtime] = f"not requested: --{runtime}-bin, --{runtime}-version and the isolated home were not all given"
            continue
        binaries[runtime] = check_binary(binary, f"--{runtime}-bin")
        homes[runtime] = (
            check_isolated_home(home, flag="--codex-home", env_key="CODEX_HOME", fallback=".codex", kit_root=kit_root)
            if runtime == "codex"
            else check_isolated_home(home, flag="--claude-config-dir", env_key="CLAUDE_CONFIG_DIR", fallback=".claude", kit_root=kit_root)
        )
        pins[runtime] = pin
    if (args.allow_codex_hook_trust_bypass or args.allow_codex_project_trust) and "codex" not in homes:
        raise Refusal("the Codex trust authorizations need a Codex run to apply to")

    run_dir = Path(realpath(tempfile.mkdtemp(prefix="adk-smoke-", dir=work_root)))
    log_dir = run_dir / "logs"
    log_dir.mkdir()
    fixture = build_fixture(kit_root, revision, run_dir, base_env)
    config = load_config(fixture.repo / "config" / "dev-model.yaml", overlay=False)
    nonce = secrets.token_hex(6)
    pr_number = 1000 + secrets.randbelow(9000)
    command, url = probe_command(nonce, pr_number)
    ctx = Context(
        kit_root=kit_root,
        revision=revision,
        run_dir=run_dir,
        log_dir=log_dir,
        fixture=fixture,
        config=config,
        timeout=args.timeout,
        nonce=nonce,
        pr_number=pr_number,
        budget_line=expected_budget_line(fixture, base_env),
        followup_markers={
            runtime: expected_followup_marker(fixture, runtime, command, url, base_env) for runtime in RUNTIMES
        },
        base_env=base_env,
    )

    rows = {row_id: Row(row_id, runtime, check) for row_id, runtime, check in ROWS}
    for runtime in homes:
        facts, reason = (
            codex_preflight(binaries[runtime], pins[runtime], homes[runtime], base_env)
            if runtime == "codex"
            else claude_preflight(binaries[runtime], pins[runtime], homes[runtime], base_env)
        )
        clients[runtime] = facts
        if reason:
            blocked[runtime] = reason
    for runtime, reason in blocked.items():
        clients.setdefault(runtime, {})["preflight"] = reason
        for row in rows.values():
            if row.runtime == runtime:
                row.set("not-run", reason)

    observations: dict[str, Any] = {"ancestor_instruction_files": ancestor_instruction_files(fixture.repo)}
    if "codex" in homes and "codex" not in blocked:
        clients["codex"]["preflight"] = "ready"
        observations["codex"] = run_codex(
            ctx, rows, binaries["codex"], homes["codex"], pins["codex"],
            bypass=args.allow_codex_hook_trust_bypass, project_trust=args.allow_codex_project_trust,
        )
    if "claude" in homes and "claude" not in blocked:
        clients["claude"]["preflight"] = "ready"
        run_claude(ctx, rows, binaries["claude"], homes["claude"], pins["claude"])

    summary, exit_status = summarise(rows)
    table = placeholders(
        [
            (run_dir, "<run>"),
            (homes.get("codex"), "<codex-home>"),
            (homes.get("claude"), "<claude-config>"),
            (kit_root, "<kit>"),
            (work_root, "<work-root>"),
            (out, "<out>"),
            (Path.home(), "~"),
            # Claude names a project's transcript directory by its path with `/` and
            # `.` turned into `-`; that spelling carries the account name too.
            (re.sub(r"[/.]", "-", str(Path.home())), "~"),
        ]
    )
    record = finalize_record(
        {
            "schema": SCHEMA,
            "run_id": run_dir.name,
            "started_at": started_at,
            "finished_at": utc_now(),
            "kit": {"revision": revision, "harness": SCRIPT_PATH.relative_to(kit_root).as_posix(), "harness_sha256": harness},
            # The arguments as given, and the interpreter that ran them. How the runner was
            # started (`uv run`, `python3`) is not observable from inside it.
            "invocation": [SCRIPT_PATH.relative_to(kit_root).as_posix(), *raw_argv],
            "interpreter": sys.executable,
            "clients": clients,
            "fixture": {
                "main_head": fixture.main_head,
                "review_head": fixture.review_head,
                "friction_log": fixture.friction_rel,
                "friction_lines": fixture.friction_lines,
                "friction_budget": fixture.friction_budget,
                "nonce": nonce,
            },
            "observations": observations,
            "rows": [
                {
                    "id": row.id,
                    "runtime": row.runtime,
                    "check": row.check,
                    "status": row.status,
                    "reason": row.reason,
                    "evidence": row.evidence,
                    "session": row.session,
                    "invocations": row.invocations,
                }
                for row in rows.values()
            ],
            "summary": summary,
            "exit_status": exit_status,
        },
        table,
    )
    payload = json.dumps(record, indent=2, sort_keys=False) + "\n"
    markdown = render_markdown(record)
    # Written aside and renamed into place, so the record appears whole or not at all.
    # The rename replaces `out` only if it is still an empty directory.
    staging = Path(tempfile.mkdtemp(prefix=f".{out.name}.", dir=out.parent))
    (staging / "record.json").write_text(payload, encoding="utf-8")
    (staging / "record.md").write_text(markdown, encoding="utf-8")
    try:
        os.rename(staging, out)
    except OSError as exc:
        raise RuntimeError(f"--out could not take the record ({exc}); it is complete at {staging}") from exc
    return record


if __name__ == "__main__":
    sys.exit(main())
