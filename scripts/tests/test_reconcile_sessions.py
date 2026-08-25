"""`reconcile_sessions.sh`'s lane classification — with `held` as the subject.

Why this file exists at all: the reconciler had no test module before #465, and
#465 adds a fourth state — `held`, terminal, alongside `merged` and `parked`;
`open` is the one that is not — plus a new exit code. A new state with no
failing case behind it is the pattern #417 and #447 are filed about, so every
assertion here is written to die under a specific mutation of the branch it
covers: `_held_check`'s three outcomes (held / not held / could not tell), the
branch → session-dir resolution (identity AND its ambiguity refusal), the
environment the probe is handed, how often the forge repo is resolved, the tally
composition, and the three-way exit.

Most of that list is there because review put it there. The first version of
this file pinned the rest and let two resolution mutants through — one lens made
the lookup ignore its argument, the other made two session dirs claiming one
branch resolve by glob order; both survived all 19 tests then present. Later
rounds found the probe's forge-repo pin unasserted, then its single-resolution
claim untrue and unmeasured, then the pin failing OPEN to an ambient `$GH_REPO`
when resolution itself failed. Each test says in place which mutant it exists
for.

**Everything runs the real script.** `gh`, `uv` and the session directory are
faked, but `reconcile_sessions.sh` itself is executed unmodified through `bash`,
against a real git repository with a real remote — so the classification, the
tally line and the exit code are observed, never reconstructed. Both stubs
RECORD what they were called with — the `uv` one its argv, `$DEVKIT_STATE_ROOT`
and `$GH_REPO`; the `gh` one its whole argv — which is what pins the properties
no output could show: that the probe reads the LANE's state sandbox rather than
the caller's, that it is aimed at the repository the run already resolved, that
that repository is resolved once per run, and that it passes `--no-persist` so
reconciling never mutates a lane's seen-set, settle baseline or receipt.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import time
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no repository root above {start}")


REPO_ROOT = _find_repo_root(ENGINE_DIR)

_CONFIG = """paths:
  handoff: handoff.md
  friction_log: friction-log.md
runtime:
  default: codex
  launchers:
    claude: claude
    codex: codex
vcs:
  protected_branch: trunk
  dev_branch_prefix: lane
"""

# `gh pr list --head <branch> …` reaches this; nothing else here shells out to
# the forge. Branch names contain `/`, which cannot be a filename component, so
# the fixture file is keyed on the slash-flattened name.
_FAKE_GH = """#!/bin/sh
printf '%s\\n' "$*" >> "$GH_ARGV_LOG"
if [ "$1" = "repo" ] && [ "$2" = "view" ]; then
  # $GH_NWO_FAIL_FIRST failures before the first success, so a TRANSIENT blip on
  # this one call can be told apart from a `gh` outage.
  n=0
  [ -f "$GH_ARGV_LOG.nwofail" ] && n=$(cat "$GH_ARGV_LOG.nwofail")
  if [ "$n" -lt "${GH_NWO_FAIL_FIRST:-0}" ]; then
    printf '%s\\n' "$((n + 1))" > "$GH_ARGV_LOG.nwofail"
    exit 1
  fi
  printf '%s\\n' "${GH_FAKE_NWO:-}"
  exit 0
fi
if [ "${GH_PR_LIST_FAIL:-0}" = "1" ]; then exit 17; fi
head=""
prev=""
for a in "$@"; do
  if [ "$prev" = "--head" ]; then head="$a"; fi
  prev="$a"
done
f="$GH_PRS/$(printf '%s' "$head" | tr '/' '_').json"
if [ -f "$f" ]; then cat "$f"; else printf '[]\\n'; fi
"""

# Stands in for `uv run <engine>/pr_watch.py <pr> --json --no-persist`. Records
# the state root it was handed plus its whole argv, then replies with the canned
# report for that PR — or exits non-zero when there is none, which is how the
# "probe could not run" path is reached without having to uninstall anything.
_FAKE_UV = """#!/bin/sh
# `${VAR-default}`, NOT `${VAR:-default}`: the colon form returns the default for
# an empty string too, so it cannot tell "GH_REPO was never exported" from
# "GH_REPO was exported empty" — which is exactly the distinction one of these
# tests exists to pin. Two round-3 lenses found that independently.
printf '%s\\t%s\\t%s\\n' "${DEVKIT_STATE_ROOT-<unset>}" "${GH_REPO-<unset>}" "$*" \
  >> "$UV_ARGV_LOG"
for a in "$@"; do
  case "$a" in
    ''|*[!0-9]*) ;;
    *)
      if [ -f "$UV_REPORTS/$a.json" ]; then cat "$UV_REPORTS/$a.json"; exit 0; fi
      exit 2 ;;
  esac
done
exit 2
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


class Harness:
    """A repo, its engines, a sessions dir, and the two stubbed binaries."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        remote = tmp_path / "origin.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True
        )
        self.repo = tmp_path / "project"
        self.repo.mkdir()
        _git(self.repo, "init", "-b", "trunk")
        _git(self.repo, "config", "user.email", "test@example.com")
        _git(self.repo, "config", "user.name", "Test")
        (self.repo / "README.md").write_text("seed\n", encoding="utf-8")
        _git(self.repo, "add", "README.md")
        _git(self.repo, "commit", "-m", "seed")
        _git(self.repo, "remote", "add", "origin", str(remote))
        _git(self.repo, "push", "-u", "origin", "trunk")

        self.engine_dir = self.repo / "scripts"
        (self.engine_dir / "lib").mkdir(parents=True)
        shutil.copy2(
            ENGINE_DIR / "reconcile_sessions.sh", self.engine_dir / "reconcile_sessions.sh"
        )
        shutil.copy2(ENGINE_DIR / "lib" / "repo_root.sh", self.engine_dir / "lib" / "repo_root.sh")
        shutil.copy2(ENGINE_DIR / "pr_watch.py", self.engine_dir / "pr_watch.py")
        (self.repo / "config").mkdir()
        (self.repo / "config" / "dev-model.yaml").write_text(_CONFIG, encoding="utf-8")

        self.sessions = tmp_path / "sessions"
        self.sessions.mkdir()
        self.gh_prs = tmp_path / "gh-prs"
        self.gh_prs.mkdir()
        self.uv_reports = tmp_path / "uv-reports"
        self.uv_reports.mkdir()
        self.uv_argv_log = tmp_path / "uv-argv.log"
        self.uv_argv_log.write_text("", encoding="utf-8")
        self.gh_argv_log = tmp_path / "gh-argv.log"
        self.gh_argv_log.write_text("", encoding="utf-8")
        self.pr_heads: dict[int, str] = {}

        self.bin = tmp_path / "fake-bin"
        self.bin.mkdir()
        for name, body in (("gh", _FAKE_GH), ("uv", _FAKE_UV)):
            path = self.bin / name
            path.write_text(body, encoding="utf-8")
            path.chmod(0o755)

    # ---------------------------------------------------------------- fixtures

    def branch(self, name: str, *, commits: int = 1, push: bool = True) -> None:
        _git(self.repo, "checkout", "-b", name, "trunk")
        for n in range(commits):
            # Only the one file, never `add -A`: the engines and the config live
            # untracked in this tree, and sweeping them into a lane commit would
            # delete them again on the checkout back to trunk.
            leaf = f"{name.replace('/', '_')}-{n}.txt"
            (self.repo / leaf).write_text("x\n", encoding="utf-8")
            _git(self.repo, "add", leaf)
            _git(self.repo, "commit", "-m", f"{name} {n}")
        if push:
            _git(self.repo, "push", "-u", "origin", name)
        _git(self.repo, "checkout", "trunk")

    def pr(
        self,
        branch: str,
        number: int,
        state: str,
        title: str = "some work",
        *,
        base: str = "trunk",
        owner: str = "acme",
        cross_repository: bool = False,
        head: str | None = None,
    ) -> None:
        head = head or _git(self.repo, "rev-parse", branch)
        self.pr_heads[number] = head
        (self.gh_prs / f"{branch.replace('/', '_')}.json").write_text(
            json.dumps(
                [
                    {
                        "number": number,
                        "title": title,
                        "state": state,
                        "baseRefName": base,
                        "headRefName": branch,
                        "headRefOid": head,
                        "headRepositoryOwner": {"login": owner},
                        "isCrossRepository": cross_repository,
                    }
                ]
            ),
            encoding="utf-8",
        )

    def pr_payload(self, branch: str, payload: str) -> None:
        (self.gh_prs / f"{branch.replace('/', '_')}.json").write_text(
            payload, encoding="utf-8"
        )

    def advance_branch(self, branch: str) -> str:
        _git(self.repo, "checkout", branch)
        leaf = f"{branch.replace('/', '_')}-later.txt"
        (self.repo / leaf).write_text("later\n", encoding="utf-8")
        _git(self.repo, "add", leaf)
        _git(self.repo, "commit", "-m", f"advance {branch}")
        _git(self.repo, "push", "origin", branch)
        head = _git(self.repo, "rev-parse", "HEAD")
        _git(self.repo, "checkout", "trunk")
        return head

    def session(self, scope: str, branch: str, merge_class: str | None) -> Path:
        d = self.sessions / scope
        (d / "wt").mkdir(parents=True)
        (d / "state").mkdir()
        (d / "branch").write_text(f"{branch}\n", encoding="utf-8")
        (d / "base").write_text("trunk\n", encoding="utf-8")
        if merge_class is not None:
            (d / "merge_class").write_text(f"{merge_class}\n", encoding="utf-8")
        return d

    def watch_report(self, number: int, **fields: object) -> None:
        report = {
            "pr": number,
            "base": "trunk",
            "head": self.pr_heads[number],
            "merge_blockers": [],
            **fields,
        }
        if fields.get("mergeable") is True:
            report.setdefault("converged", True)
        (self.uv_reports / f"{number}.json").write_text(json.dumps(report), encoding="utf-8")

    # ------------------------------------------------------------------ runner

    def run(self, *args: str, nwo: str = "acme/widgets", **extra: str) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "DEVKIT_SESSIONS_DIR": str(self.sessions),
            "GH_PRS": str(self.gh_prs),
            "GH_FAKE_NWO": nwo,
            "UV_REPORTS": str(self.uv_reports),
            "UV_ARGV_LOG": str(self.uv_argv_log),
            "GH_ARGV_LOG": str(self.gh_argv_log),
        }
        # The runner's own ambient GH_REPO must not decide what these tests see.
        env.pop("GH_REPO", None)
        env.update(extra)
        return subprocess.run(
            ["bash", str(self.engine_dir / "reconcile_sessions.sh"), *args],
            cwd=self.repo,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    def gh_repo_view_calls(self) -> int:
        return sum(
            1
            for line in self.gh_argv_log.read_text(encoding="utf-8").splitlines()
            if line.startswith("repo view")
        )

    def uv_calls(self) -> list[tuple[str, str, str]]:
        """One (state_root, gh_repo, argv) triple per recorded probe."""
        lines = self.uv_argv_log.read_text(encoding="utf-8").splitlines()
        return [tuple(line.split("\t", 2)) for line in lines if line]  # type: ignore[misc]


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    return Harness(tmp_path)


def _status_of(stdout: str, lane: str) -> str:
    for line in stdout.splitlines():
        if line.startswith(f"{lane} ") or line == lane:
            return line.split()[1]
    raise AssertionError(f"no table row for {lane!r} in:\n{stdout}")


def _tally(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("launched "):
            return line
    raise AssertionError(f"no tally line in:\n{stdout}")


def _bounded_run_helper_source() -> str:
    script = (ENGINE_DIR / "reconcile_sessions.sh").read_text(encoding="utf-8")
    start = script.index("_bounded_run() {")
    end = script.index("\n}\n", start) + len("\n}\n")
    return script[start:end]


# --------------------------------------------------------------------------- #
# the state itself
# --------------------------------------------------------------------------- #


def test_operator_lane_with_a_mergeable_open_pr_is_held_not_open(harness: Harness) -> None:
    """The whole point of #465: an operator lane that is finished — green,
    review-clean, receipt bound to head — reported `open`, indistinguishable
    from one still working."""
    harness.branch("lane/alpha")
    harness.pr("lane/alpha", 501, "OPEN")
    harness.session("alpha", "lane/alpha", "operator")
    harness.watch_report(501, mergeable=True, converged=True)

    result = harness.run("alpha")

    assert _status_of(result.stdout, "alpha") == "held"
    assert "awaiting operator merge" in result.stdout
    assert result.returncode == 4


def test_self_merge_lane_with_the_same_mergeable_pr_stays_open(harness: Harness) -> None:
    """A `self` lane in this exact condition is not held — it is supposed to
    merge itself. Only the PERSISTED class distinguishes the two, so this is the
    case that dies if `_held_check` stops reading `merge_class`."""
    harness.branch("lane/beta")
    harness.pr("lane/beta", 502, "OPEN")
    harness.session("beta", "lane/beta", "self")
    harness.watch_report(502, mergeable=True, converged=True)

    result = harness.run("beta")

    assert _status_of(result.stdout, "beta") == "open"
    assert result.returncode == 3
    assert harness.uv_calls() == [], "a self-class lane must not even be probed"


def test_absent_merge_class_metadata_is_not_held(harness: Harness) -> None:
    """`dev_session.sh merge` defaults MISSING metadata to `operator` because
    that refuses a merge. Defaulting the same way here would WIDEN `held`, so
    the reconciler must default the other way."""
    harness.branch("lane/gamma")
    harness.pr("lane/gamma", 503, "OPEN")
    harness.session("gamma", "lane/gamma", None)
    harness.watch_report(503, mergeable=True, converged=True)

    result = harness.run("gamma")

    assert _status_of(result.stdout, "gamma") == "open"
    assert result.returncode == 3


def test_a_branch_with_no_session_dir_at_all_is_not_held(harness: Harness) -> None:
    """A bare branch or a torn-down lane has no persisted class and no state
    sandbox. It stays `open` — reconciliation never invents evidence."""
    harness.branch("feat/loose")
    harness.pr("feat/loose", 504, "OPEN")
    harness.watch_report(504, mergeable=True, converged=True)

    result = harness.run("feat/loose")

    assert _status_of(result.stdout, "feat/loose") == "open"
    assert result.returncode == 3
    # "no evidence" is an answer, not a failed probe: nothing to warn about, and
    # nothing was probed.
    assert "could not evaluate" not in result.stderr
    assert harness.uv_calls() == []


def test_converged_but_not_mergeable_is_open_not_held(harness: Harness) -> None:
    """`converged` is deliberately true on a green, comment-clean PR carrying NO
    review receipt. Reading it here would call an unreviewed lane finished — the
    single most dangerous mutation of `_held_check`."""
    harness.branch("lane/delta")
    harness.pr("lane/delta", 505, "OPEN")
    harness.session("delta", "lane/delta", "operator")
    harness.watch_report(505, mergeable=False, converged=True, done=False)

    result = harness.run("delta")

    assert _status_of(result.stdout, "delta") == "open"
    assert result.returncode == 3


def test_a_report_without_a_mergeable_key_fails_closed(harness: Harness) -> None:
    """Absent means not-mergeable, never "assume yes"."""
    harness.branch("lane/epsilon")
    harness.pr("lane/epsilon", 506, "OPEN")
    harness.session("epsilon", "lane/epsilon", "operator")
    harness.watch_report(506, converged=True)

    result = harness.run("epsilon")

    assert _status_of(result.stdout, "epsilon") == "open"
    assert result.returncode == 3


def test_a_probe_that_could_not_run_reports_open_and_says_so_on_stderr(
    harness: Harness,
) -> None:
    """No `uv`, no engine, a timeout, a transport failure — all the same rc 2.
    The lane is reported `open`, but a probe that never ran must not read as one
    that ran and said no."""
    harness.branch("lane/zeta")
    harness.pr("lane/zeta", 507, "OPEN")
    harness.session("zeta", "lane/zeta", "operator")
    # deliberately no watch_report → the uv stub exits 2

    result = harness.run("zeta")

    assert _status_of(result.stdout, "zeta") == "open"
    assert result.returncode == 3
    assert "could not evaluate for 'held'" in result.stderr
    assert "PR #507" in result.stderr


def test_an_ordinary_not_held_answer_is_silent(harness: Harness) -> None:
    """The counterpart to the test above: rc 1 must NOT produce the stderr note,
    or the note becomes noise on every in-flight batch and stops being read."""
    harness.branch("lane/eta")
    harness.pr("lane/eta", 508, "OPEN")
    harness.session("eta", "lane/eta", "operator")
    harness.watch_report(508, mergeable=False)

    result = harness.run("eta")

    assert _status_of(result.stdout, "eta") == "open"
    assert "could not evaluate" not in result.stderr


# --------------------------------------------------------------------------- #
# the probe is read-only and lane-scoped
# --------------------------------------------------------------------------- #


def test_the_probe_reads_the_lanes_own_sandbox_and_never_persists(harness: Harness) -> None:
    """Two properties of the invocation that no output could show: the state root
    it is handed, and the flags it carries.

    The receipt and seen-set live in the LANE's sandbox, so a probe against the
    caller's state root would answer for the wrong lane. And reconciliation is a
    report, so it must ask for no persistence — a settle baseline written or a
    pending seen-set consumed on the way past would be a mutation of lane state.

    Precisely, because a round-8 lens found the earlier wording overclaiming:
    this asserts that `--no-persist` is PASSED. That `pr_watch.py` honours it is
    that engine's contract and is tested in `test_pr_watch.py`; nothing here
    could establish it, since the probe is stubbed."""
    harness.branch("lane/theta")
    harness.pr("lane/theta", 509, "OPEN")
    session = harness.session("theta", "lane/theta", "operator")
    harness.watch_report(509, mergeable=True)

    result = harness.run("theta")

    assert result.returncode == 4
    assert len(harness.uv_calls()) == 1
    state_root, _gh_repo, argv = harness.uv_calls()[0]
    assert os.path.realpath(state_root) == os.path.realpath(session / "state")
    assert os.path.isabs(state_root)
    assert "--no-persist" in argv
    assert "--json" in argv
    assert " 509 " in f" {argv} "
    assert argv.split()[0] == "run"
    assert argv.split()[1].endswith("pr_watch.py")


def test_the_probe_is_pinned_to_the_repo_the_run_already_resolved(harness: Harness) -> None:
    """The panel's adversarial lens, round 2. `gh pr list` resolves the forge repo
    from the caller's cwd and any ambient `$GH_REPO`; `pr_watch.py` pins its own
    cwd to the repo root and separately honours `$GH_REPO`. Unpinned, the PR
    number can come from one repository and the merge-readiness verdict from
    another — and a same-numbered green PR elsewhere would report `held` about a
    PR nobody looked at. The probe must carry the repo this run already
    resolved."""
    harness.branch("lane/psi")
    harness.pr("lane/psi", 540, "OPEN")
    harness.session("psi", "lane/psi", "operator")
    harness.watch_report(540, mergeable=True)

    # An ambient GH_REPO for some OTHER repo is exactly the hazard. Whatever the
    # run resolves through `gh` is what the probe must be handed — the property
    # is that the two agree, not which one wins.
    result = harness.run("psi", nwo="acme/widgets", GH_REPO="someone/else")

    assert result.returncode == 4
    assert [gh_repo for _root, gh_repo, _argv in harness.uv_calls()] == ["acme/widgets"]


def test_a_relative_sessions_dir_still_yields_an_absolute_state_root(
    harness: Harness,
) -> None:
    """Also the panel's adversarial lens, round 2. `pr_watch.py` treats a RELATIVE
    `$DEVKIT_STATE_ROOT` as "ignore this, use `<repo>/state`" rather than as an
    error — deliberately, so its loop never crashes. A relative
    `$DEVKIT_SESSIONS_DIR` would therefore silently aim the probe at the MAIN
    checkout's per-PR file, which can hold real unrelated history for the same PR
    number, with no failure visible anywhere. The index normalizes instead."""
    harness.branch("lane/chi")
    harness.pr("lane/chi", 542, "OPEN")
    session = harness.session("chi", "lane/chi", "operator")
    harness.watch_report(542, mergeable=True)

    relative = os.path.relpath(harness.sessions, harness.repo)
    assert not os.path.isabs(relative)
    result = harness.run("chi", DEVKIT_SESSIONS_DIR=relative)

    assert result.returncode == 4
    state_root, _nwo, _argv = harness.uv_calls()[0]
    assert os.path.isabs(state_root), state_root
    assert os.path.realpath(state_root) == os.path.realpath(session / "state")


def test_the_forge_repo_is_resolved_once_per_run_not_once_per_lane(
    harness: Harness,
) -> None:
    """Round 3 — the correctness lens and the review bot found this one from
    opposite ends. `nwo="$(_repo_nwo)"` evaluated the memo in a COMMAND
    SUBSTITUTION, i.e. a subshell, so the flag it set died with that subshell and
    every operator lane paid another `gh repo view` round trip behind its own
    timeout. The code said "resolved once" and did not do it. Counting the calls
    is the only way that claim is worth anything."""
    for scope, pr in (("alpha", 550), ("beta", 551)):
        harness.branch(f"lane/{scope}")
        harness.pr(f"lane/{scope}", pr, "OPEN")
        harness.session(scope, f"lane/{scope}", "operator")
        harness.watch_report(pr, mergeable=True)

    result = harness.run("alpha", "beta")

    assert result.returncode == 4
    assert len(harness.uv_calls()) == 2, "both lanes must actually be probed"
    assert harness.gh_repo_view_calls() == 1


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param(" ", id="a-single-space"),
        pytest.param("", id="empty"),
        pytest.param("/", id="both-segments-empty"),
        pytest.param("acme/", id="empty-repo-segment"),
        pytest.param("/widgets", id="empty-owner-segment"),
        pytest.param("a/b/c", id="three-segments"),
        pytest.param("acme/wid gets", id="whitespace-inside-a-segment"),
        pytest.param("acmewidgets", id="no-separator"),
    ],
)
def test_a_malformed_repo_reply_stops_reconciliation(
    harness: Harness, reply: str
) -> None:
    """A malformed repository identity cannot produce a partial lane board."""
    for scope, pr in (("m1", 570), ("m2", 571)):
        harness.branch(f"lane/{scope}")
        harness.pr(f"lane/{scope}", pr, "OPEN")
        harness.session(scope, f"lane/{scope}", "operator")
        harness.watch_report(pr, mergeable=True)

    result = harness.run("m1", "m2", nwo=reply)

    assert result.returncode == 64
    assert "invalid repository identity" in result.stderr
    assert "launched " not in result.stdout
    assert harness.uv_calls() == []
    assert harness.gh_repo_view_calls() == 1


def test_an_unresolvable_repo_stops_before_classification(
    harness: Harness,
) -> None:
    """Repository resolution is a batch precondition, not a parked lane."""
    harness.branch("lane/omega")
    harness.pr("lane/omega", 541, "OPEN")
    harness.session("omega", "lane/omega", "operator")
    harness.watch_report(541, mergeable=True)

    result = harness.run("omega", nwo="", GH_REPO="someone-else/unrelated")

    assert result.returncode == 64
    assert "invalid repository identity" in result.stderr
    assert "launched " not in result.stdout
    assert harness.uv_calls() == []


def test_a_transient_repo_resolution_failure_stops_the_batch(
    harness: Harness,
) -> None:
    """A failed repository read cannot yield a mixed authoritative/unknown board."""
    for scope, pr in (("aa", 560), ("zz", 561)):
        harness.branch(f"lane/{scope}")
        harness.pr(f"lane/{scope}", pr, "OPEN")
        harness.session(scope, f"lane/{scope}", "operator")
        harness.watch_report(pr, mergeable=True)

    result = harness.run("aa", "zz", GH_NWO_FAIL_FIRST="1")

    assert result.returncode == 64
    assert "could not resolve the GitHub repository" in result.stderr
    assert "launched " not in result.stdout
    assert harness.gh_repo_view_calls() == 1


def test_the_forge_repo_is_resolved_before_any_lane_classification(
    harness: Harness,
) -> None:
    """Self-class lanes still need authoritative PR state for reconciliation."""
    harness.branch("lane/sigma2")
    harness.pr("lane/sigma2", 543, "OPEN")
    harness.session("sigma2", "lane/sigma2", "self")

    result = harness.run("sigma2")

    assert _status_of(result.stdout, "sigma2") == "open"
    assert harness.gh_repo_view_calls() == 1


def test_a_failed_pr_list_stops_without_rendering_a_partial_board(harness: Harness) -> None:
    harness.branch("lane/forge-fail")
    harness.session("forge-fail", "lane/forge-fail", "operator")

    result = harness.run("forge-fail", GH_PR_LIST_FAIL="1")

    assert result.returncode == 64
    assert "could not resolve PR state" in result.stderr
    assert "launched " not in result.stdout
    assert "EMPTY" not in result.stdout


@pytest.mark.parametrize("payload", ["not-json", "{}", '[{"number":"8"}]'])
def test_a_malformed_pr_list_stops_instead_of_becoming_no_pr(
    harness: Harness, payload: str
) -> None:
    harness.branch("lane/malformed")
    harness.session("malformed", "lane/malformed", "operator")
    harness.pr_payload("lane/malformed", payload)

    result = harness.run("malformed")

    assert result.returncode == 64
    assert "invalid PR state" in result.stderr
    assert "launched " not in result.stdout


def test_a_later_malformed_pr_discards_every_preceding_lane_row(harness: Harness) -> None:
    harness.branch("lane/valid-first")
    harness.pr("lane/valid-first", 584, "MERGED")
    harness.session("valid-first", "lane/valid-first", "operator")
    harness.branch("lane/malformed-later")
    harness.session("malformed-later", "lane/malformed-later", "operator")
    harness.pr_payload("lane/malformed-later", "not-json")

    result = harness.run("valid-first", "malformed-later")

    assert result.returncode == 64
    assert "invalid PR state" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("pr_kwargs", "label"),
    [
        ({"cross_repository": True}, "fork"),
        ({"base": "other"}, "wrong-base"),
        ({"owner": "someone-else"}, "foreign-owner"),
    ],
)
def test_foreign_pr_identity_cannot_terminalize_a_lane(
    harness: Harness, pr_kwargs: dict[str, object], label: str
) -> None:
    harness.branch("lane/foreign")
    harness.pr("lane/foreign", 580, "MERGED", **pr_kwargs)  # type: ignore[arg-type]
    harness.session("foreign", "lane/foreign", "operator")

    result = harness.run("foreign")

    assert result.returncode == 3, label
    assert _status_of(result.stdout, "foreign") == "parked", label
    assert "merged" not in _status_of(result.stdout, "foreign"), label


def test_newer_wrong_base_reuse_cannot_expose_an_older_matching_merge(
    harness: Harness,
) -> None:
    branch = "lane/base-reused"
    harness.branch(branch)
    head = _git(harness.repo, "rev-parse", branch)
    harness.session("base-reused", branch, "operator")
    harness.pr_payload(
        branch,
        json.dumps(
            [
                {
                    "number": 500,
                    "title": "older trunk work",
                    "state": "MERGED",
                    "baseRefName": "trunk",
                    "headRefName": branch,
                    "headRefOid": head,
                    "headRepositoryOwner": {"login": "acme"},
                    "isCrossRepository": False,
                },
                {
                    "number": 501,
                    "title": "newer release reuse",
                    "state": "MERGED",
                    "baseRefName": "release",
                    "headRefName": branch,
                    "headRefOid": head,
                    "headRepositoryOwner": {"login": "acme"},
                    "isCrossRepository": False,
                },
            ]
        ),
    )
    _git(harness.repo, "push", "origin", "--delete", branch)
    _git(harness.repo, "branch", "-D", branch)

    result = harness.run("base-reused")

    assert result.returncode == 3
    assert _status_of(result.stdout, "base-reused") == "parked"
    assert "older trunk work" not in result.stdout


@pytest.mark.parametrize(
    "report_changes",
    [
        {"pr": 999},
        {"base": "other"},
        {"head": "f" * 40},
        {"converged": False},
        {"merge_blockers": ["pending review"]},
    ],
)
def test_held_requires_the_exact_pr_base_head_and_clean_report(
    harness: Harness, report_changes: dict[str, object]
) -> None:
    harness.branch("lane/exact-report")
    harness.pr("lane/exact-report", 581, "OPEN")
    harness.session("exact-report", "lane/exact-report", "operator")
    harness.watch_report(581, mergeable=True, **report_changes)

    result = harness.run("exact-report")

    assert result.returncode == 3
    assert _status_of(result.stdout, "exact-report") == "open"


def test_recorded_lane_base_overrides_the_reconcile_default(harness: Harness) -> None:
    _git(harness.repo, "branch", "release", "trunk")
    _git(harness.repo, "push", "origin", "release")
    harness.branch("lane/release-base")
    harness.pr("lane/release-base", 582, "OPEN", base="release")
    session = harness.session("release-base", "lane/release-base", "operator")
    (session / "base").write_text("release\n", encoding="utf-8")
    harness.watch_report(582, mergeable=True, base="release")

    result = harness.run("release-base")

    assert result.returncode == 4
    assert _status_of(result.stdout, "release-base") == "held"


def test_newer_surviving_branch_tip_keeps_an_older_merged_pr_open(harness: Harness) -> None:
    harness.branch("lane/reused")
    old_head = _git(harness.repo, "rev-parse", "lane/reused")
    harness.pr("lane/reused", 583, "MERGED", head=old_head)
    harness.session("reused", "lane/reused", "operator")
    new_head = harness.advance_branch("lane/reused")
    assert new_head != old_head

    result = harness.run("reused")

    assert result.returncode == 3
    assert _status_of(result.stdout, "reused") == "open"
    assert "tip differs from PR head" in result.stdout


def test_newer_remote_tip_is_not_hidden_by_a_stale_matching_local_tip(
    harness: Harness,
) -> None:
    harness.branch("lane/remote-reused")
    old_head = _git(harness.repo, "rev-parse", "lane/remote-reused")
    harness.pr("lane/remote-reused", 585, "MERGED", head=old_head)
    harness.session("remote-reused", "lane/remote-reused", "operator")
    new_head = harness.advance_branch("lane/remote-reused")
    _git(harness.repo, "update-ref", "refs/heads/lane/remote-reused", old_head)
    assert _git(harness.repo, "rev-parse", "refs/heads/lane/remote-reused") == old_head
    assert (
        _git(harness.repo, "rev-parse", "refs/remotes/origin/lane/remote-reused")
        == new_head
    )

    result = harness.run("remote-reused")

    assert result.returncode == 3
    assert _status_of(result.stdout, "remote-reused") == "open"
    assert "remote-tracking tip differs from PR head" in result.stdout


def test_newer_live_origin_tip_is_not_hidden_by_stale_local_caches(
    harness: Harness,
) -> None:
    harness.branch("lane/live-origin")
    old_head = _git(harness.repo, "rev-parse", "lane/live-origin")
    harness.pr("lane/live-origin", 587, "MERGED", head=old_head)
    harness.session("live-origin", "lane/live-origin", "operator")
    new_head = harness.advance_branch("lane/live-origin")
    _git(harness.repo, "update-ref", "refs/heads/lane/live-origin", old_head)
    _git(
        harness.repo,
        "update-ref",
        "refs/remotes/origin/lane/live-origin",
        old_head,
    )
    assert _git(
        harness.repo, "ls-remote", "origin", "refs/heads/lane/live-origin"
    ).startswith(new_head)

    result = harness.run("live-origin")

    assert result.returncode == 3
    assert _status_of(result.stdout, "live-origin") == "open"
    assert "origin tip differs from PR head" in result.stdout


@pytest.mark.parametrize("mode", ["failure", "malformed"])
def test_unknown_live_origin_state_stops_without_a_lane_board(
    harness: Harness, mode: str
) -> None:
    branch = "lane/live-origin-read"
    harness.branch(branch)
    head = _git(harness.repo, "rev-parse", branch)
    harness.pr(branch, 588, "MERGED", head=head)
    harness.session("live-origin-read", branch, "operator")
    real_git = shutil.which("git")
    assert real_git is not None
    fake_git = harness.bin / "git"
    response = "exit 17" if mode == "failure" else "printf 'malformed\\n'"
    fake_git.write_text(
        "#!/bin/sh\n"
        f"if [ \"$1\" = \"-C\" ] && [ \"$3\" = \"ls-remote\" ] && "
        f"[ \"$6\" = \"refs/heads/{branch}\" ]; then {response}; fi\n"
        f"exec \"{real_git}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)

    result = harness.run("live-origin-read")

    assert result.returncode == 64
    assert "could not resolve surviving branch tips" in result.stderr
    assert result.stdout == ""


def test_live_origin_reads_use_the_portable_bounded_runner(harness: Harness) -> None:
    branch = "lane/live-origin-timeout"
    harness.branch(branch)
    head = _git(harness.repo, "rev-parse", branch)
    harness.pr(branch, 590, "MERGED", head=head)
    harness.session("live-origin-timeout", branch, "operator")
    timeout_log = harness.tmp / "timeout-argv.log"
    real_python = shutil.which("python3")
    assert real_python is not None
    fake_python = harness.bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ] && [ \"$4\" = \"git\" ] && "
        "[ \"$7\" = \"ls-remote\" ]; then\n"
        "  shift 2\n"
        f"  printf '%s\\n' \"$*\" >> \"{timeout_log}\"\n"
        "  exit 124\n"
        "fi\n"
        f"exec \"{real_python}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    result = harness.run("live-origin-timeout")

    assert result.returncode == 64
    assert "could not resolve surviving branch tips" in result.stderr
    assert result.stdout == ""
    logged = timeout_log.read_text(encoding="utf-8")
    assert logged.startswith(f"10 git -C {harness.repo} ls-remote --heads origin ")
    assert logged.rstrip().endswith(f"refs/heads/{branch}")


def test_forge_reads_use_the_portable_bounded_runner(harness: Harness) -> None:
    branch = "lane/forge-timeout"
    harness.branch(branch)
    harness.pr(branch, 591, "OPEN")
    harness.session("forge-timeout", branch, "operator")
    timeout_log = harness.tmp / "forge-timeout-argv.log"
    real_python = shutil.which("python3")
    assert real_python is not None
    fake_python = harness.bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ] && [ \"$3\" = \"10\" ] && "
        "[ \"$4\" = \"gh\" ]; then\n"
        "  shift 2\n"
        f"  printf '%s\\n' \"$*\" >> \"{timeout_log}\"\n"
        "  exit 124\n"
        "fi\n"
        f"exec \"{real_python}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    result = harness.run("forge-timeout")

    assert result.returncode == 64
    assert "could not resolve the GitHub repository" in result.stderr
    assert result.stdout == ""
    assert timeout_log.read_text(encoding="utf-8").startswith("10 gh repo view ")


def test_held_probe_uses_the_portable_bounded_runner(harness: Harness) -> None:
    branch = "lane/held-timeout"
    harness.branch(branch)
    harness.pr(branch, 592, "OPEN")
    harness.session("held-timeout", branch, "operator")
    harness.watch_report(592, mergeable=True, converged=True)
    timeout_log = harness.tmp / "held-timeout-argv.log"
    real_python = shutil.which("python3")
    assert real_python is not None
    fake_python = harness.bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-c\" ] && [ \"$3\" = \"60\" ] && "
        "[ \"$4\" = \"env\" ]; then\n"
        "  shift 2\n"
        f"  printf '%s\\n' \"$*\" >> \"{timeout_log}\"\n"
        "  exit 124\n"
        "fi\n"
        f"exec \"{real_python}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    result = harness.run("held-timeout")

    assert result.returncode == 3
    assert _status_of(result.stdout, "held-timeout") == "open"
    assert "could not evaluate for 'held'" in result.stderr
    logged = timeout_log.read_text(encoding="utf-8")
    assert logged.startswith("60 env DEVKIT_STATE_ROOT=")
    assert " uv run " in f" {logged} "
    assert " --json --no-persist" in logged


def test_portable_bounded_runner_reaps_term_ignoring_descendants(
    tmp_path: Path,
) -> None:
    helper = _bounded_run_helper_source()
    hostile = tmp_path / "term-ignoring-descendant.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        "trap 'exit 0' TERM\n"
        "sh -c 'trap \"\" TERM; while :; do sleep 1; done' &\n"
        "wait\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    command = f"{helper}\n_bounded_run 0.1 {shlex.quote(str(hostile))}\n"

    started = time.monotonic()
    result = subprocess.run(
        ["bash", "-c", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    )

    elapsed = time.monotonic() - started
    assert result.returncode == 124
    assert 1 <= elapsed < 2.5


def test_portable_bounded_runner_delivers_term_during_grace(tmp_path: Path) -> None:
    helper = _bounded_run_helper_source()
    marker = tmp_path / "term-delivered"
    command = tmp_path / "term-observer.sh"
    command.write_text(
        "#!/bin/sh\n"
        f"marker={shlex.quote(str(marker))}\n"
        "trap 'printf delivered > \"$marker\"; exit 0' TERM\n"
        "printf started > \"$marker\"\n"
        "while :; do sleep 1; done\n",
        encoding="utf-8",
    )
    command.chmod(0o755)
    invocation = f"{helper}\n_bounded_run 30 {shlex.quote(str(command))}\n"
    runner = subprocess.Popen(
        ["bash", "-c", invocation],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    deadline = time.monotonic() + 3
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert marker.read_text(encoding="utf-8") == "started"
    os.killpg(runner.pid, signal.SIGTERM)
    runner.communicate(timeout=3)

    assert runner.returncode in {-signal.SIGTERM, 128 + signal.SIGTERM}
    assert marker.read_text(encoding="utf-8") == "delivered"


def test_portable_bounded_runner_reaps_descendants_after_launcher_success(
    tmp_path: Path,
) -> None:
    helper = _bounded_run_helper_source()
    hostile = tmp_path / "successful-launcher-with-descendant.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        "sh -c 'trap \"\" HUP INT TERM; while :; do sleep 1; done' &\n"
        "exit 0\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    command = f"{helper}\n_bounded_run 30 {shlex.quote(str(hostile))}\n"

    result = subprocess.run(
        ["bash", "-c", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    )

    assert result.returncode == 0


def test_portable_bounded_runner_reaps_on_operator_interrupt(tmp_path: Path) -> None:
    helper = _bounded_run_helper_source()
    hostile = tmp_path / "signal-ignoring-descendant.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        "trap 'exit 0' HUP INT TERM\n"
        "sh -c 'trap \"\" HUP INT TERM; while :; do sleep 1; done' &\n"
        "wait\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    command = f"{helper}\n_bounded_run 30 {shlex.quote(str(hostile))}\n"
    runner = subprocess.Popen(
        ["bash", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    time.sleep(0.2)
    os.killpg(runner.pid, signal.SIGINT)
    runner.communicate(timeout=3)

    assert runner.returncode in {-signal.SIGINT, 128 + signal.SIGINT}


def test_portable_bounded_runner_reaps_on_startup_interrupt(tmp_path: Path) -> None:
    marker = tmp_path / "shim-started"
    install_handlers = (
        "for handled_signal in handled_signals:\n"
        "    signal.signal(handled_signal, cancel)"
    )
    helper = _bounded_run_helper_source().replace(
        install_handlers,
        f"open({json.dumps(str(marker))}, \"w\").close()\n"
        "time.sleep(0.5)\n"
        f"{install_handlers}",
    )
    assert str(marker) in helper
    hostile = tmp_path / "startup-signal-descendant.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        "sh -c 'trap \"\" HUP INT TERM; while :; do sleep 1; done' &\n"
        "wait\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    command = f"{helper}\n_bounded_run 30 {shlex.quote(str(hostile))}\n"
    runner = subprocess.Popen(
        ["bash", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    deadline = time.monotonic() + 3
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert marker.exists()
    os.killpg(runner.pid, signal.SIGINT)
    runner.communicate(timeout=3)

    assert runner.returncode in {-signal.SIGINT, 128 + signal.SIGINT}


def test_portable_bounded_runner_reaps_on_post_result_interrupt(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "result-ready"
    helper = _bounded_run_helper_source().replace(
        "    reply = os.read(result_fd, 64)",
        f"    open({json.dumps(str(marker))}, \"w\").close()\n"
        "    time.sleep(30)\n"
        "    reply = os.read(result_fd, 64)",
    )
    assert str(marker) in helper
    hostile = tmp_path / "successful-launcher-with-retained-pipe.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        "sh -c 'trap \"\" HUP INT TERM; while :; do sleep 1; done' &\n"
        "exit 0\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    command = f"{helper}\n_bounded_run 30 {shlex.quote(str(hostile))}\n"
    runner = subprocess.Popen(
        ["bash", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    deadline = time.monotonic() + 3
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert marker.exists()
    os.killpg(runner.pid, signal.SIGINT)
    runner.communicate(timeout=3)

    assert runner.returncode in {-signal.SIGINT, 128 + signal.SIGINT}


def test_portable_bounded_runner_reaps_after_repeated_operator_signals(
    tmp_path: Path,
) -> None:
    ready_marker = tmp_path / "command-ready"
    catch_marker = tmp_path / "cancel-caught"
    helper = _bounded_run_helper_source().replace(
        "except Cancelled as exc:\n    stop_group(exc.signum)",
        "except Cancelled as exc:\n"
        f"    open({json.dumps(str(catch_marker))}, \"w\").close()\n"
        "    time.sleep(0.5)\n"
        "    stop_group(exc.signum)",
    )
    assert str(catch_marker) in helper
    hostile = tmp_path / "repeated-signal-descendant.sh"
    hostile.write_text(
        "#!/bin/sh\n"
        f"printf ready > {shlex.quote(str(ready_marker))}\n"
        "sh -c 'trap \"\" HUP INT TERM; while :; do sleep 1; done' &\n"
        "wait\n",
        encoding="utf-8",
    )
    hostile.chmod(0o755)
    invocation = f"{helper}\n_bounded_run 30 {shlex.quote(str(hostile))}\n"
    runner = subprocess.Popen(
        ["bash", "-c", invocation],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    deadline = time.monotonic() + 3
    while not ready_marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready_marker.exists()
    os.killpg(runner.pid, signal.SIGINT)
    while not catch_marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert catch_marker.exists()
    os.killpg(runner.pid, signal.SIGTERM)
    runner.communicate(timeout=3)

    assert runner.returncode in {
        -signal.SIGINT,
        128 + signal.SIGINT,
        -signal.SIGTERM,
        128 + signal.SIGTERM,
    }


@pytest.mark.parametrize("direction", ["expected-to-new", "new-to-expected"])
def test_live_origin_movement_between_snapshot_reads_cannot_terminalize(
    harness: Harness, direction: str
) -> None:
    branch = "lane/live-origin-race"
    harness.branch(branch)
    old_head = _git(harness.repo, "rev-parse", branch)
    harness.pr(branch, 589, "MERGED", head=old_head)
    harness.session("live-origin-race", branch, "operator")
    new_head = harness.advance_branch(branch)
    _git(harness.repo, "update-ref", f"refs/heads/{branch}", old_head)
    _git(harness.repo, "update-ref", f"refs/remotes/origin/{branch}", old_head)
    _git(harness.repo, "push", "--force", "origin", f"{old_head}:refs/heads/{branch}")
    first, second = (
        (old_head, new_head)
        if direction == "expected-to-new"
        else (new_head, old_head)
    )
    real_git = shutil.which("git")
    assert real_git is not None
    marker = harness.tmp / "live-origin-read-once"
    fake_git = harness.bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        f"if [ \"$1\" = \"-C\" ] && [ \"$3\" = \"ls-remote\" ] && "
        f"[ \"$6\" = \"refs/heads/{branch}\" ]; then\n"
        f"  if [ ! -e \"{marker}\" ]; then printf '%s\\t%s\\n' {first} refs/heads/{branch}; "
        f": > \"{marker}\"; else printf '%s\\t%s\\n' {second} refs/heads/{branch}; fi\n"
        "  exit 0\n"
        "fi\n"
        f"exec \"{real_git}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)

    result = harness.run("live-origin-race")

    assert result.returncode == 3
    assert _status_of(result.stdout, "live-origin-race") == "open"
    assert "origin tip moved during reconciliation" in result.stdout


def test_a_tip_that_moves_between_snapshot_reads_cannot_terminalize(
    harness: Harness,
) -> None:
    harness.branch("lane/race")
    old_head = _git(harness.repo, "rev-parse", "lane/race")
    harness.pr("lane/race", 586, "MERGED", head=old_head)
    harness.session("race", "lane/race", "operator")
    new_head = harness.advance_branch("lane/race")
    _git(harness.repo, "update-ref", "refs/heads/lane/race", new_head)
    _git(harness.repo, "update-ref", "-d", "refs/remotes/origin/lane/race")
    _git(harness.repo, "push", "origin", "--delete", "lane/race")

    real_git = shutil.which("git")
    assert real_git is not None
    marker = harness.tmp / "moved-tip"
    fake_git = harness.bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        f"if [ \"$1\" = \"-C\" ] && [ \"$3\" = \"rev-parse\" ] && "
        "[ \"$4\" = \"--verify\" ] && "
        "[ \"$5\" = \"refs/heads/lane/race^{commit}\" ] && "
        f"[ ! -e \"{marker}\" ]; then\n"
        f"  \"{real_git}\" -C \"$2\" rev-parse --verify \"$5\"\n"
        f"  \"{real_git}\" -C \"$2\" update-ref refs/heads/lane/race {old_head}\n"
        f"  : > \"{marker}\"\n"
        "  exit 0\n"
        "fi\n"
        f"exec \"{real_git}\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)

    result = harness.run("race")

    assert result.returncode == 3
    assert _status_of(result.stdout, "race") == "open"
    assert "local tip moved during reconciliation" in result.stdout


def test_a_lane_reached_by_branch_name_still_resolves_its_session(harness: Harness) -> None:
    """Lanes are keyed on BRANCH but the evidence is keyed on SCOPE. A lane that
    surfaced as a full branch (a `--match` glob, a worktree, an explicit branch
    arg) must still find its session dir, or `held` would only ever work for the
    one selection path that happens to pass a scope."""
    harness.branch("feat/custom-name")
    harness.pr("feat/custom-name", 510, "OPEN")
    harness.session("iota", "feat/custom-name", "operator")
    harness.watch_report(510, mergeable=True)

    result = harness.run("--match", "feat/custom-*")

    assert _status_of(result.stdout, "feat/custom-name") == "held"
    assert result.returncode == 4


def test_the_index_matches_on_branch_identity_not_on_position(harness: Harness) -> None:
    """The panel's correctness lens killed the first version of this file with a
    mutant no test caught: make `_session_dir_for_branch` ignore its argument and
    return the first indexed session. Every other multi-session test here survives
    it, because the `uv` stub answers by PR number and never notices it was handed
    the wrong sandbox. So this one pins identity BOTH ways, with two sessions whose
    merge classes disagree and whose glob order is fixed by their names.

    `aaa` sorts first, so first-match resolves everything to it."""
    harness.branch("lane/aaa")
    harness.pr("lane/aaa", 530, "OPEN")
    aaa = harness.session("aaa", "lane/aaa", "operator")
    harness.watch_report(530, mergeable=True)

    harness.branch("lane/zzz")
    harness.pr("lane/zzz", 531, "OPEN")
    harness.session("zzz", "lane/zzz", "self")
    harness.watch_report(531, mergeable=True)

    # The self-class lane must NOT borrow the operator class of the first entry.
    only_zzz = harness.run("zzz")
    assert _status_of(only_zzz.stdout, "zzz") == "open"
    assert harness.uv_calls() == []

    # And the operator lane must be probed against ITS OWN sandbox, which is what
    # dies if resolution ever answers with a different session's directory.
    only_aaa = harness.run("aaa")
    assert _status_of(only_aaa.stdout, "aaa") == "held"
    assert [os.path.realpath(r) for r, _n, _a in harness.uv_calls()] == [
        os.path.realpath(aaa / "state")
    ]


def test_the_index_matches_on_branch_identity_in_the_other_direction(
    harness: Harness,
) -> None:
    """The mirror of the test above, with the classes swapped and both lanes
    queried in ONE invocation — the arrangement the real wrap-up uses, where the
    index is consulted twice against a shared roster rather than once.

    A round-2 lens checked whether this test is what kills a resolve-to-the-LAST
    match mutant and found the test above already does; the docstring here used
    to claim otherwise, and no longer does. What it adds is the multi-lane
    invocation and the opposite class arrangement, not a mutant of its own."""
    harness.branch("lane/aaa")
    harness.pr("lane/aaa", 532, "OPEN")
    harness.session("aaa", "lane/aaa", "self")
    harness.watch_report(532, mergeable=True)

    harness.branch("lane/zzz")
    harness.pr("lane/zzz", 533, "OPEN")
    zzz = harness.session("zzz", "lane/zzz", "operator")
    harness.watch_report(533, mergeable=True)

    result = harness.run("aaa", "zzz")

    assert _status_of(result.stdout, "aaa") == "open"
    assert _status_of(result.stdout, "zzz") == "held"
    assert [os.path.realpath(r) for r, _n, _a in harness.uv_calls()] == [
        os.path.realpath(zzz / "state")
    ]
    assert result.returncode == 3


def test_two_sessions_claiming_one_branch_are_refused_not_ranked(harness: Harness) -> None:
    """The panel's adversarial lens executed this: with two session dirs recording
    the same branch, first-match made `held` vs `open` depend on nothing but the
    alphabetical order of the directory names — swapping only the merge-class
    values flipped the verdict and the exit code. Ambiguity is now refused in both
    arrangements, which is what makes the outcome independent of that order."""
    harness.branch("lane/dup")
    harness.pr("lane/dup", 534, "OPEN")
    harness.watch_report(534, mergeable=True)

    for first, second in (("operator", "self"), ("self", "operator")):
        shutil.rmtree(harness.sessions, ignore_errors=True)
        harness.sessions.mkdir()
        harness.uv_argv_log.write_text("", encoding="utf-8")
        harness.session("aaa_old", "lane/dup", first)
        harness.session("zzz_new", "lane/dup", second)

        result = harness.run("lane/dup")

        assert _status_of(result.stdout, "lane/dup") == "open", (first, second)
        assert result.returncode == 3, (first, second)
        assert "two sessions record branch 'lane/dup'" in result.stderr
        assert harness.uv_calls() == [], "an ambiguous branch must not be probed"


def test_a_pre_metadata_session_resolves_through_the_prefix(harness: Harness) -> None:
    """A session dir written before `new` recorded its branch has no `branch`
    file. The index reconstructs `<prefix>/<scope>` for it, exactly as the
    no-arg discovery pass does, so the two agree on one lane."""
    harness.branch("lane/upsilon")
    harness.pr("lane/upsilon", 520, "OPEN")
    session = harness.session("upsilon", "lane/upsilon", "operator")
    (session / "branch").unlink()
    harness.watch_report(520, mergeable=True)

    result = harness.run("upsilon")

    assert _status_of(result.stdout, "upsilon") == "held"
    assert result.returncode == 4


def test_no_arg_discovery_reaches_the_same_held_verdict(harness: Harness) -> None:
    """The wrap-up path. Discovery unions session dirs and live worktrees; a
    lane found that way must classify identically to one named explicitly."""
    harness.branch("lane/phi")
    harness.pr("lane/phi", 521, "OPEN")
    harness.session("phi", "lane/phi", "operator")
    harness.watch_report(521, mergeable=True)

    result = harness.run()

    assert _status_of(result.stdout, "phi") == "held"
    assert result.returncode == 4


# --------------------------------------------------------------------------- #
# tally line and exit code
# --------------------------------------------------------------------------- #


def test_the_tally_grows_a_held_term_only_when_a_lane_is_held(harness: Harness) -> None:
    """The `held H` term is additive: a batch with none prints the line it has
    always printed, so nothing pinned to today's shape moves until a held lane
    actually exists."""
    harness.branch("lane/kappa")
    harness.pr("lane/kappa", 511, "MERGED")
    harness.session("kappa", "lane/kappa", "operator")

    merged_only = harness.run("kappa")
    assert _tally(merged_only.stdout) == "launched 1, merged 1, parked 0"
    assert merged_only.returncode == 0

    harness.branch("lane/lambda")
    harness.pr("lane/lambda", 512, "OPEN")
    harness.session("lambda", "lane/lambda", "operator")
    harness.watch_report(512, mergeable=True)

    with_held = harness.run("kappa", "lambda")
    assert _tally(with_held.stdout) == "launched 2, merged 1, parked 0, held 1"
    assert with_held.returncode == 4


def test_held_and_open_both_appear_with_held_first(harness: Harness) -> None:
    harness.branch("lane/mu")
    harness.pr("lane/mu", 513, "OPEN")
    harness.session("mu", "lane/mu", "operator")
    harness.watch_report(513, mergeable=True)

    harness.branch("lane/nu")
    harness.pr("lane/nu", 514, "OPEN")
    harness.session("nu", "lane/nu", "operator")
    harness.watch_report(514, mergeable=False)

    result = harness.run("mu", "nu")

    # The row label as well as the tally: a round-8 lens mutated `status="held"`
    # to `status="open"` while leaving the counter alone, and this test — the one
    # named for the distinction — passed. The tally and the row can disagree.
    assert _status_of(result.stdout, "mu") == "held"
    assert _status_of(result.stdout, "nu") == "open"
    assert _tally(result.stdout) == "launched 2, merged 0, parked 0, held 1, open 1"
    assert result.returncode == 3


def test_all_merged_still_exits_zero_and_prints_no_held_block(harness: Harness) -> None:
    harness.branch("lane/xi")
    harness.pr("lane/xi", 515, "MERGED")
    harness.session("xi", "lane/xi", "operator")

    result = harness.run("xi")

    assert result.returncode == 0
    assert "held" not in result.stdout


def test_a_parked_lane_outranks_a_held_one(harness: Harness) -> None:
    """A dead lane still needs naming. It must never hide behind a batch that is
    otherwise handed to the operator, so parked keeps the batch at 3."""
    harness.branch("lane/omicron")
    harness.pr("lane/omicron", 516, "OPEN")
    harness.session("omicron", "lane/omicron", "operator")
    harness.watch_report(516, mergeable=True)

    harness.branch("lane/pi", commits=0, push=False)
    harness.session("pi", "lane/pi", "operator")

    result = harness.run("omicron", "pi")

    assert _status_of(result.stdout, "omicron") == "held"
    assert _status_of(result.stdout, "pi") == "parked"
    assert _tally(result.stdout) == "launched 2, merged 0, parked 1, held 1"
    assert result.returncode == 3


def test_an_open_lane_outranks_a_held_one(harness: Harness) -> None:
    """Symmetric to the parked case, and the reason `held` cannot simply be
    folded into "not open"."""
    harness.branch("lane/rho")
    harness.pr("lane/rho", 517, "OPEN")
    harness.session("rho", "lane/rho", "operator")
    harness.watch_report(517, mergeable=True)

    harness.branch("lane/sigma")
    harness.pr("lane/sigma", 518, "OPEN")
    harness.session("sigma", "lane/sigma", "self")

    result = harness.run("rho", "sigma")

    assert _status_of(result.stdout, "rho") == "held"
    assert _status_of(result.stdout, "sigma") == "open"
    assert result.returncode == 3
    assert "still OPEN" in result.stdout


def test_the_held_block_names_every_held_lane_with_its_pr(harness: Harness) -> None:
    """The operator's to-do list. An exit code alone does not say which PRs are
    waiting, and the batch's wrap-up block has to name them."""
    harness.branch("lane/tau")
    harness.pr("lane/tau", 519, "OPEN", title="tighten the guard")
    harness.session("tau", "lane/tau", "operator")
    harness.watch_report(519, mergeable=True)

    result = harness.run("tau")

    assert "held for operator sign-off" in result.stdout
    assert "• tau: PR #519 — tighten the guard" in result.stdout


# --------------------------------------------------------------------------- #
# the contract as documented
# --------------------------------------------------------------------------- #


def test_help_prints_the_whole_header_including_the_exit_contract() -> None:
    """`--help` used to stop at a hardcoded line number that had already fallen
    short of the header. Growing the header — which this change does — would
    otherwise have hidden the new exit code from the only place a user reads it."""
    result = subprocess.run(
        ["bash", str(ENGINE_DIR / "reconcile_sessions.sh"), "--help"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "held" in result.stdout
    assert "4 = every launched lane merged or held" in result.stdout
    # The last line of the header comment, i.e. nothing was truncated.
    assert result.stdout.rstrip().endswith("rationale at the return statements.")
    assert "set -euo pipefail" not in result.stdout
