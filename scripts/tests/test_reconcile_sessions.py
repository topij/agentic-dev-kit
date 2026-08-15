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
import shutil
import subprocess
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
  printf '%s\\n' "${GH_FAKE_NWO:-}"
  exit 0
fi
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


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


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

    def pr(self, branch: str, number: int, state: str, title: str = "some work") -> None:
        (self.gh_prs / f"{branch.replace('/', '_')}.json").write_text(
            json.dumps([{"number": number, "title": title, "state": state}]),
            encoding="utf-8",
        )

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
        report = {"pr": number, "base": "trunk", "head": "deadbeef", **fields}
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
    """Two properties no output could show. The receipt and seen-set live in the
    LANE's sandbox, so a probe against the caller's state root would answer for
    the wrong lane; and reconciliation is a report, so it must not write a
    settle baseline or consume a pending seen-set on the way past."""
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


def test_an_unresolvable_repo_refuses_to_classify_rather_than_probing(
    harness: Harness,
) -> None:
    """Round 4's HIGH, and the reason resolution is a precondition rather than an
    optimisation. The first version simply omitted the pin when `gh repo view`
    failed — but `env` only ADDS to the environment, so the probe then inherited
    whatever `$GH_REPO` the operator's shell already had. The lens executed that:
    resolution failing plus a stale ambient `$GH_REPO` produced `held` on a probe
    that ran against an unrelated repository, silently, because rc 0 from the
    wrong repo looks exactly like rc 0 from the right one.

    So an unresolvable repo must not probe at all. It is rc 2 — reported `open`,
    named on stderr — never a lane classified from a repository nobody
    identified."""
    harness.branch("lane/omega")
    harness.pr("lane/omega", 541, "OPEN")
    harness.session("omega", "lane/omega", "operator")
    harness.watch_report(541, mergeable=True)

    result = harness.run("omega", nwo="", GH_REPO="someone-else/unrelated")

    assert _status_of(result.stdout, "omega") == "open"
    assert result.returncode == 3
    assert harness.uv_calls() == [], "an unidentified repo must never be probed"
    assert "could not evaluate for 'held'" in result.stderr


def test_the_forge_repo_is_not_resolved_when_no_lane_reaches_the_probe(
    harness: Harness,
) -> None:
    """Round 4's LOW: resolution is lazy, sits behind the merge-class gate, and
    nothing pinned that. A lens moved the call in front of the gate and all 26
    tests stayed green — so a batch of `self`-class lanes would silently start
    paying a `gh repo view` round trip it never needs."""
    harness.branch("lane/sigma2")
    harness.pr("lane/sigma2", 543, "OPEN")
    harness.session("sigma2", "lane/sigma2", "self")

    result = harness.run("sigma2")

    assert _status_of(result.stdout, "sigma2") == "open"
    assert harness.gh_repo_view_calls() == 0


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
