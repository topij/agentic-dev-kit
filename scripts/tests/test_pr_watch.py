from __future__ import annotations

import importlib.util
import json
import shutil
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _pin_engine_defaults(module: ModuleType) -> None:
    """Detach the loaded engine from whatever config happens to be on disk.

    ``pr_watch`` resolves its review config at IMPORT time into module-level
    constants, so a module loaded here inherits the *ambient repo's*
    ``config/dev-model.yaml``. These tests exercise the ENGINE, not an
    adopter's configuration — so without this, they carry an undeclared
    precondition that the surrounding repo happens to configure a review bot.

    That is not hypothetical. A real adopter (OpenKitchen) set the truthful
    ``review.bots: []`` — it has CodeRabbit installed but on a plan where it
    never returns a verdict — and **32 of these tests failed**, on assertions
    about engine behaviour that have nothing to do with config. Same tree, one
    config value: ``[]`` -> 32 failed, ``[coderabbit]`` -> all passed. The kit's
    own invariant is that config is adopter-owned and engines are kit-owned;
    a legitimate adopter value must never break a kit-owned test.

    Passing a path that cannot exist takes ``_load_review_config``'s
    ``FileNotFoundError`` branch, which returns the engine defaults and stays
    deliberately quiet — the same state as a standalone engine run.

    A test that genuinely wants the AMBIENT config — this repo's own
    ``config/dev-model.yaml`` — must ask for it with
    ``_load_pr_watch(pin_defaults=False)``. Pinning by default and opting out
    is deliberate: the failure mode of a test that silently reads ambient
    config is invisible here and only shows up in somebody else's repo, so the
    safe state is the default and wanting otherwise has to be written down.
    """
    defaults = module._load_review_config(ENGINE_DIR / "does-not-exist" / "dev-model.yaml")
    module._REVIEW_CONFIG = defaults
    module._NOISE_MARKERS = defaults.noise_markers
    module._REVIEW_UNAVAILABLE_MARKERS = defaults.unavailable_markers
    module._INFORMATIONAL_CHECK_NAMES = defaults.informational_checks
    module._REQUIRE_CI = defaults.require_ci
    module._REVIEW_BOTS = defaults.bots
    module._BOT_PENDING_GRACE_MINUTES = defaults.bot_pending_grace_minutes


def _pin_engine_backend(module: ModuleType) -> None:
    """Detach the loaded engine from whether this MACHINE happens to have `gh`.

    The transport picks its backend from ``shutil.which("gh")`` on every call.
    That is right for production and wrong for a test suite: a number of these
    tests mock ``_gh_json`` and nothing else, so on a machine with no `gh` on PATH
    they resolve to REST, the mock is never consulted, and they fail — on
    assertions about receipts and merge blockers that have nothing to do with
    transport. The count is not quoted here on purpose; it changes as tests are
    added, and an out-of-date figure in a docstring is worse than none.

    The invariant, stated instead of a count: without the pin, removing `gh` from
    PATH turns a passing suite into a failing one. No figure is quoted — the count
    is environment-dependent AND changes as tests are added, so it would be
    claim-drift bait rather than evidence. `make test`
    is green here and on GitHub-hosted runners only because both ship `gh`, which
    is exactly the ambient-state coupling the config half of this file already
    exists to prevent. A kit-owned test must not depend on the host.

    Swaps in a per-module stand-in rather than patching the real ``shutil``,
    which is shared process-wide. A test whose SUBJECT is backend selection
    overrides ``module.shutil.which`` itself (see ``_no_gh``), and because each
    test loads the engine fresh, that override cannot leak into another test.
    """

    class _ShutilPinnedToGh:
        @staticmethod
        def which(name: str) -> str | None:
            if name == "gh":
                return "/pinned/by/tests/gh"
            return shutil.which(name)

    module.shutil = _ShutilPinnedToGh


def _load_pr_watch(*, pin_defaults: bool = True) -> ModuleType:
    """Load the engine fresh.

    ``pin_defaults=False`` leaves the module bound to whatever
    ``config/dev-model.yaml`` the surrounding repo has — correct only for a
    test whose SUBJECT is that config. The BACKEND pin is unconditional: no
    test should depend on whether the host has `gh`, including the ones that
    deliberately read ambient config.
    """
    spec = importlib.util.spec_from_file_location(
        "pr_watch_under_test", ENGINE_DIR / "pr_watch.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if pin_defaults:
        _pin_engine_defaults(module)
    _pin_engine_backend(module)
    return module


def _green_view(**overrides):
    view = {
        "number": 7,
        "url": "https://example.test/pr/7",
        "state": "OPEN",
        "isDraft": False,
        "baseRefName": "trunk",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "headRefOid": "abc123",
        "statusCheckRollup": [
            {"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS"}
        ],
        "comments": [],
        "reviews": [],
    }
    view.update(overrides)
    return view


def test_done_keeps_its_original_merge_authorization_semantics() -> None:
    """`done` must still mean exactly what it meant before `converged` existed.

    This is the safety property that makes the schema change purely ADDITIVE.
    Engine upgrades are per-file, so a new `pr_watch.py` can run against an older
    `dev_session.sh` whose merge gate reads `done`. If `done` were repurposed to
    mean watch-convergence, that pairing would authorize merges on PRs carrying
    no review receipt at all — a silent fail-open on the merge gate.

    Pinned over the whole boolean input space, not just a happy path.
    """
    pr_watch = _load_pr_watch()

    def original_done(checks, new_items, merge_blockers, review_evidence, settling):
        return (
            checks["all_green"]
            and not new_items
            and not merge_blockers
            and review_evidence
            and not settling
        )

    comment = {"kind": "issue", "author": "a", "path": None, "line": None, "body": "x"}
    for all_green in (True, False):
        for new_items in ([], [comment]):
            for blockers in ([], ["merge state is BLOCKED"]):
                for evidence in (True, False):
                    for settling in (True, False):
                        checks = {"all_green": all_green}
                        expected = original_done(
                            checks, new_items, blockers, evidence, settling
                        )
                        assert (
                            pr_watch.decide_done(
                                checks,
                                new_items,
                                merge_blockers=blockers,
                                review_evidence=evidence,
                                settling=settling,
                            )
                            is expected
                        )
                        # ...and `mergeable` is that same predicate under its
                        # clearer name, composed from `converged`.
                        assert (
                            pr_watch.decide_mergeable(
                                pr_watch.decide_converged(
                                    checks, new_items, settling=settling
                                ),
                                merge_blockers=blockers,
                                review_evidence=evidence,
                            )
                            is expected
                        )


def test_report_done_is_always_identical_to_mergeable() -> None:
    """The alias must never drift from the field it aliases.

    The report **key** — not :func:`decide_done`, which has no in-engine caller —
    is what keeps an older `dev_session.sh` gating on merge authorization. So it
    is the key that needs the coverage: walk a matrix of report shapes spanning
    converged/not, blocked/clean, and receipt/none, rather than a few examples.
    """
    pr_watch = _load_pr_watch()
    current = {"head": "abc123", "source": "fallback:codex"}
    stale = {"head": "older", "source": "fallback:codex"}
    comment = {"id": "c1", "author": {"login": "someone"}, "body": "please fix"}

    views = (
        _green_view(),
        _green_view(isDraft=True),
        _green_view(state="MERGED"),
        _green_view(mergeStateStatus="BLOCKED"),
        _green_view(reviewDecision="CHANGES_REQUESTED"),
        _green_view(statusCheckRollup=[{"name": "t", "conclusion": "FAILURE"}]),
        _green_view(statusCheckRollup=[]),
        _green_view(comments=[comment]),
    )
    for view in views:
        for receipt in (None, current, stale):
            report = pr_watch.build_report(view, [], set(), review_receipt=receipt)
            assert report["done"] is report["mergeable"], (view, receipt)


def test_predicates_are_strictly_bool_typed() -> None:
    """`dev_session.sh merge` tests the JSON value with `is True`.

    A bare `and` chain returns its LAST operand, so a truthy non-bool reaching
    the predicate would land a non-bool in the report. That fails the gate's
    identity check — closed, but confusingly, and it would serialize as e.g.
    `"mergeable": 1`. Pin the type rather than trusting every caller.
    """
    pr_watch = _load_pr_watch()

    assert (
        pr_watch.decide_mergeable(
            True, merge_blockers=[], review_evidence=1  # truthy non-bool
        )
        is True
    )
    report = pr_watch.build_report(
        _green_view(), [], set(), review_receipt={"head": "abc123", "source": "x"}
    )
    for key in ("converged", "mergeable", "done"):
        assert isinstance(report[key], bool), key


def test_converged_is_watch_progress_and_ignores_merge_authorization() -> None:
    """The whole point of the split: a converged loop is not a merge clearance.

    A green, comment-clean PR with NO review receipt is `converged` (nothing left
    for the loop to fix) and NOT `mergeable`. Before `converged` existed a caller
    had only `done`, so it kept looping — and the operator was pressured into
    recording a receipt early just to terminate it (issue #19).
    """
    pr_watch = _load_pr_watch()

    report = pr_watch.build_report(_green_view(), [], set())

    assert report["converged"] is True
    assert report["mergeable"] is False
    assert report["done"] is False
    assert (
        "independent review evidence is missing for current head"
        in report["merge_blockers"]
    )


def test_render_never_lets_convergence_read_as_merge_clearance() -> None:
    pr_watch = _load_pr_watch()
    receipt = {"head": "abc123", "source": "fallback:codex"}

    converged = pr_watch.render(pr_watch.build_report(_green_view(), [], set()))
    authorized = pr_watch.render(
        pr_watch.build_report(_green_view(), [], set(), review_receipt=receipt)
    )

    assert "NOT mergeable" in converged
    assert "DONE" not in converged
    assert "DONE" in authorized and "NOT mergeable" not in authorized


def test_changes_requested_and_blocked_merge_state_never_settle_done() -> None:
    pr_watch = _load_pr_watch()
    review = {
        "id": "review-1",
        "author": {"login": "reviewer"},
        "body": "Please fix the unsafe branch deletion.",
    }
    view = _green_view(
        mergeStateStatus="BLOCKED",
        reviewDecision="CHANGES_REQUESTED",
        reviews=[review],
    )
    comments = pr_watch.collect_comments(view, [])
    seen = {
        key for comment in comments for key in (comment["key"], comment["content_key"])
    }

    report = pr_watch.build_report(view, [], seen)

    assert report["new_comments"] == []
    # The findings were acked and CI is green, so the WATCH loop has converged...
    assert report["converged"] is True
    # ...but the merge is still refused: blockers are a merge-gate concern.
    assert report["mergeable"] is False
    assert "merge state is BLOCKED" in report["merge_blockers"]
    assert "review decision is CHANGES_REQUESTED" in report["merge_blockers"]


def test_unknown_or_non_open_pr_state_never_settles_done() -> None:
    pr_watch = _load_pr_watch()

    unknown = pr_watch.build_report(_green_view(mergeStateStatus="UNKNOWN"), [], set())
    merged = pr_watch.build_report(
        _green_view(state="MERGED", mergeStateStatus="UNKNOWN"), [], set()
    )

    # Both are green and comment-clean, so the watch loop converged; only the
    # merge is refused. Asserting `converged` here too keeps the two predicates
    # independently pinned, so a regression that re-couples them fails.
    assert unknown["converged"] is True
    assert unknown["mergeable"] is False
    assert "merge state is UNKNOWN" in unknown["merge_blockers"]
    assert merged["converged"] is True
    assert merged["mergeable"] is False
    assert "PR state is MERGED" in merged["merge_blockers"]


def test_unstable_is_allowed_only_when_remaining_check_is_informational() -> None:
    pr_watch = _load_pr_watch()
    receipt = {"head": "abc123", "source": "fallback:codex"}
    coderabbit_pending = {
        "context": "CodeRabbit",
        "state": "PENDING",
    }

    informational_only = pr_watch.build_report(
        _green_view(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {"name": "tests", "conclusion": "SUCCESS"},
                coderabbit_pending,
            ],
        ),
        [],
        set(),
        review_receipt=receipt,
    )
    unexplained_unstable = pr_watch.build_report(
        _green_view(mergeStateStatus="UNSTABLE"),
        [],
        set(),
        review_receipt=receipt,
    )
    successful_informational = pr_watch.build_report(
        _green_view(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {"name": "tests", "conclusion": "SUCCESS"},
                {"context": "CodeRabbit", "state": "SUCCESS"},
            ],
        ),
        [],
        set(),
        review_receipt=receipt,
    )

    # All three converged — an informational check never blocks the watch loop.
    # Only mergeability varies, and only on the merge-state blocker.
    for report in (informational_only, unexplained_unstable, successful_informational):
        assert report["converged"] is True

    assert informational_only["mergeable"] is True
    assert "merge state is UNSTABLE" not in informational_only["merge_blockers"]
    assert unexplained_unstable["mergeable"] is False
    assert "merge state is UNSTABLE" in unexplained_unstable["merge_blockers"]
    assert successful_informational["mergeable"] is False
    assert "merge state is UNSTABLE" in successful_informational["merge_blockers"]


def test_review_unavailable_overrides_coderabbit_summary_noise() -> None:
    pr_watch = _load_pr_watch()
    body = """<!-- This is an auto-generated comment: summarize by coderabbit.ai -->
Review limit reached. We couldn't start this review.
"""
    view = _green_view(
        comments=[{"id": "notice-1", "author": {"login": "coderabbitai"}, "body": body}]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "coderabbit"},
    )

    assert report["done"] is False
    assert len(report["new_comments"]) == 1
    assert (
        report["new_comments"][0]["review_unavailable_reason"] == "review limit reached"
    )


def test_acknowledged_unavailable_notice_still_needs_review_evidence() -> None:
    pr_watch = _load_pr_watch()
    body = "Review limit reached. We couldn't start this review."
    view = _green_view(
        reviewDecision="",
        comments=[
            {"id": "notice-1", "author": {"login": "coderabbitai"}, "body": body}
        ],
    )
    comments = pr_watch.collect_comments(view, [])
    seen = {
        key for comment in comments for key in (comment["key"], comment["content_key"])
    }

    report = pr_watch.build_report(view, [], seen)

    assert report["new_comments"] == []
    # Acking the unavailability notice ends the watch loop — there is genuinely
    # nothing left to fix — but it must NOT buy merge clearance.
    assert report["converged"] is True
    assert report["mergeable"] is False
    assert (
        "independent review evidence is missing for current head"
        in report["merge_blockers"]
    )


def test_review_receipt_must_match_current_head() -> None:
    pr_watch = _load_pr_watch()
    view = _green_view(reviewDecision="")

    missing = pr_watch.build_report(view, [], set())
    stale = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "older", "source": "fallback:codex"},
    )
    current = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
    )

    # All three are green and comment-clean, so the watch loop has converged for
    # each; only the receipt bound to the CURRENT head authorizes the merge.
    for report in (missing, stale, current):
        assert report["converged"] is True

    assert missing["mergeable"] is False
    assert stale["mergeable"] is False
    assert current["mergeable"] is True
    assert current["review_evidence"] == {
        "lenses": [],
        "override": None,
        "bot_signal": None,
        "valid": True,
        "source": "fallback:codex",
        "head": "abc123",
    }


def test_record_review_refuses_push_between_review_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda _args: {"number": 7, "headRefOid": "new-unreviewed-head"},
    )

    with pytest.raises(ValueError, match="head changed during review"):
        pr_watch.record_review(7, "fallback:codex", "reviewed-head")

    assert not (tmp_path / "7.json").exists()


def test_record_review_persists_only_expected_current_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda _args: {"number": 7, "headRefOid": "reviewed-head"},
    )

    report = pr_watch.record_review(7, "fallback:codex", "reviewed-head")

    assert report["review_receipt"]["head"] == "reviewed-head"
    assert pr_watch.load_state(7)["review_receipt"]["source"] == "fallback:codex"


# --------------------------------------------------------------------------- #
# state root resolution: env -> .devkit_state_root marker -> repo-root default
# --------------------------------------------------------------------------- #


def _lane_worktree(tmp_path: Path, *, marker: str | None) -> Path:
    """A linked worktree (``.git`` is a FILE, as `git worktree add` writes) with
    an engine dir inside it, optionally carrying a sandbox marker at its root."""
    wt = tmp_path / "wt"
    (wt / "scripts").mkdir(parents=True)
    (wt / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n", encoding="utf-8")
    if marker is not None:
        (wt / ".devkit_state_root").write_text(marker, encoding="utf-8")
    return wt


def test_marker_sandbox_is_honored_when_env_is_unset(tmp_path: Path) -> None:
    """The headless-lane mechanism: a background agent's Bash calls don't share a
    shell, so an exported env var doesn't survive — the marker file is all that
    does. Without this, `dev_session.sh pr-watch <scope>` (env) and a bare
    `uv run pr_watch.py` (no env) in the same lane read DIFFERENT state files, so
    a --mark-seen through one is invisible to the other."""
    pr_watch = _load_pr_watch()
    sandbox = tmp_path / "sandbox-state"
    wt = _lane_worktree(tmp_path, marker=f"{sandbox}\n")

    resolved = pr_watch._resolve_state_root(wt / "scripts", wt, None)

    assert resolved == sandbox


def test_env_sandbox_still_wins_over_the_marker(tmp_path: Path) -> None:
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=str(tmp_path / "from-marker"))
    explicit = tmp_path / "from-env"

    assert pr_watch._resolve_state_root(wt / "scripts", wt, str(explicit)) == explicit


def test_relative_env_override_falls_back_and_ignores_the_marker(
    tmp_path: Path,
) -> None:
    """Mirrors state_paths' "marker only when the env var is unset" precedence,
    but falls back instead of raising — this engine must never crash the loop."""
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=str(tmp_path / "from-marker"))

    assert pr_watch._resolve_state_root(wt / "scripts", wt, "relative/state") == (
        wt / "state"
    )


def test_no_marker_keeps_the_repo_root_default(tmp_path: Path) -> None:
    """Cron/CI and normal checkouts carry no marker — byte-identical to before."""
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=None)

    assert pr_watch._resolve_state_root(wt / "scripts", wt, None) == wt / "state"


@pytest.mark.parametrize("content", ["", "   \n", "relative/state", "~/state"])
def test_unusable_marker_content_falls_back_instead_of_raising(
    tmp_path: Path, content: str
) -> None:
    """Empty, blank, relative, or unexpanded — never a silent redirect, never a
    crash. state_paths raises here; pr_watch deliberately falls back."""
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=content)

    assert pr_watch._resolve_state_root(wt / "scripts", wt, None) == wt / "state"


def test_unreadable_marker_falls_back_instead_of_raising(tmp_path: Path) -> None:
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=str(tmp_path / "sandbox"))
    marker = wt / ".devkit_state_root"
    marker.chmod(0o000)
    try:
        marker.read_text(encoding="utf-8")
    except OSError:
        pass
    else:  # pragma: no cover - only when tests run as root
        pytest.skip("cannot make a file unreadable (running as root?)")

    assert pr_watch._resolve_state_root(wt / "scripts", wt, None) == wt / "state"


def test_marker_walk_is_ceilinged_at_the_worktree_root(tmp_path: Path) -> None:
    """A stray marker ABOVE the .git level must not redirect this checkout — the
    walk stops at the worktree root, same ceiling as state_paths."""
    pr_watch = _load_pr_watch()
    wt = _lane_worktree(tmp_path, marker=None)
    (tmp_path / ".devkit_state_root").write_text(
        str(tmp_path / "stray"), encoding="utf-8"
    )

    assert pr_watch._resolve_state_root(wt / "scripts", wt, None) == wt / "state"


def test_marker_is_found_from_a_vendored_engine_dir(tmp_path: Path) -> None:
    """The walk starts at the engine file's own dir, so a kit vendored at
    scripts/devkit/ still finds the marker at the worktree root."""
    pr_watch = _load_pr_watch()
    sandbox = tmp_path / "sandbox-state"
    wt = _lane_worktree(tmp_path, marker=str(sandbox))
    vendored = wt / "scripts" / "devkit"
    vendored.mkdir()

    assert pr_watch._resolve_state_root(vendored, wt, None) == sandbox


def test_state_dir_is_the_pr_watch_subdir_of_the_resolved_root() -> None:
    """Pin the wiring: whatever the root resolves to, state lands in pr-watch/."""
    pr_watch = _load_pr_watch()

    assert pr_watch.STATE_DIR == pr_watch._STATE_ROOT / "pr-watch"
    assert pr_watch.STATE_DIR.is_absolute()


# --------------------------------------------------------------------------- #
# review.require_ci — convergence on a repo with no CI
# --------------------------------------------------------------------------- #


def test_zero_check_pr_can_never_be_green_while_require_ci_holds() -> None:
    """The safe default: no real check ran, so nothing may report green — this is
    what stops an autonomous merge on a PR whose CI never started."""
    pr_watch = _load_pr_watch()

    assert pr_watch.summarize_checks([], require_ci=True)["all_green"] is False
    # An informational-only rollup has no *blocking* check either.
    informational_only = pr_watch.summarize_checks(
        [{"context": "CodeRabbit", "state": "PENDING"}], require_ci=True
    )
    assert informational_only["all_green"] is False
    assert informational_only["informational"] == 1


def test_zero_check_pr_is_green_when_require_ci_is_false() -> None:
    """A repo with no CI at all: without this, `blocking_total > 0` makes `done`
    unreachable forever — the watch loop never terminates and merge always refuses."""
    pr_watch = _load_pr_watch()

    assert pr_watch.summarize_checks([], require_ci=False)["all_green"] is True
    assert (
        pr_watch.summarize_checks(
            [{"context": "CodeRabbit", "state": "PENDING"}], require_ci=False
        )["all_green"]
        is True
    )


def test_require_ci_is_honoured_by_summarize_checks() -> None:
    # RENAMED from `test_require_ci_defaults_to_the_configured_value`: the body
    # no longer checks a configured VALUE, and a review lens rightly called the
    # old name a promise the body did not keep. What it checks is the wiring —
    # whatever `review.require_ci` is set to, an empty check list is non-green
    # exactly when CI is required.
    #
    # `pin_defaults=False` because the ambient value is the input under test.
    # The old `is True` literal made a legitimate `require_ci: false` fail a kit
    # test, which is the same bug this module's loader change exists to remove.
    # That the value is READ from config at all is pinned separately by
    # `test_review_knowledge_is_read_from_config_not_engine_literals`.
    pr_watch = _load_pr_watch(pin_defaults=False)

    assert isinstance(pr_watch._REQUIRE_CI, bool)
    assert pr_watch.summarize_checks([])["all_green"] is (not pr_watch._REQUIRE_CI)


@pytest.mark.parametrize("require_ci", [True, False])
def test_real_checks_are_classified_identically_under_both_settings(
    require_ci: bool,
) -> None:
    """`require_ci` may ONLY change the zero-blocking-check verdict. With real
    checks present, every tally and verdict is byte-identical to today."""
    pr_watch = _load_pr_watch()
    green = [{"name": "tests", "conclusion": "SUCCESS"}]
    pending = [{"name": "tests", "conclusion": None, "status": "IN_PROGRESS"}]
    failing = [{"name": "tests", "conclusion": "FAILURE"}]
    mixed = [
        {"name": "tests", "conclusion": "SUCCESS"},
        {"name": "lint", "conclusion": "ERROR"},
        {"context": "CodeRabbit", "state": "PENDING"},
    ]

    assert pr_watch.summarize_checks(green, require_ci=require_ci) == {
        "total": 1,
        "success": 1,
        "pending": 0,
        "informational": 0,
        "informational_non_green": 0,
        "failing": [],
        "all_green": True,
    }
    assert pr_watch.summarize_checks(pending, require_ci=require_ci)["all_green"] is False
    assert pr_watch.summarize_checks(failing, require_ci=require_ci)["all_green"] is False
    mixed_summary = pr_watch.summarize_checks(mixed, require_ci=require_ci)
    assert mixed_summary["all_green"] is False
    assert mixed_summary["failing"] == [{"name": "lint", "status": "ERROR"}]
    assert mixed_summary["informational"] == 1
    assert mixed_summary["informational_non_green"] == 1


def test_zero_check_pr_still_needs_current_head_review_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`require_ci: false` is not a merge waiver — the receipt becomes THE gate."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REQUIRE_CI", False)
    view = _green_view(statusCheckRollup=[])

    without_receipt = pr_watch.build_report(view, [], set())
    stale_receipt = pr_watch.build_report(
        view, [], set(), review_receipt={"head": "older", "source": "fallback:codex"}
    )
    with_receipt = pr_watch.build_report(
        view, [], set(), review_receipt={"head": "abc123", "source": "fallback:codex"}
    )

    assert without_receipt["checks"]["all_green"] is True
    # With require_ci false a zero-check PR converges; the receipt is then the
    # ONLY thing standing between convergence and merge authorization.
    for report in (without_receipt, stale_receipt, with_receipt):
        assert report["converged"] is True

    assert without_receipt["mergeable"] is False
    assert (
        "independent review evidence is missing for current head"
        in without_receipt["merge_blockers"]
    )
    assert stale_receipt["mergeable"] is False
    assert with_receipt["mergeable"] is True


def test_zero_check_pr_never_settles_done_while_require_ci_holds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REQUIRE_CI", True)

    report = pr_watch.build_report(
        _green_view(statusCheckRollup=[]),
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
    )

    assert report["checks"]["all_green"] is False
    assert report["done"] is False


# --------------------------------------------------------------------------- #
# review-bot state: queued vs. unavailable (issues #19 + #23)
# --------------------------------------------------------------------------- #

NOW = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def _bot_check(**overrides):
    """One `gh pr checks --json` row for the configured review bot."""
    detail = {
        "name": "CodeRabbit",
        "state": "SUCCESS",
        "bucket": "pass",
        "description": "",
        "startedAt": "2026-07-25T11:50:00Z",
    }
    detail.update(overrides)
    return detail


def _minutes_ago(minutes: float) -> str:
    return (NOW - timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def test_rate_limit_in_a_check_description_is_detected() -> None:
    """Issue #23, the exact repro: PR #22 head 32f3e4f.

    CodeRabbit was rate-limited and said so ONLY in its status-check
    description, on a check whose conclusion was `SUCCESS` and whose name is
    classified informational. Both mechanisms missed it — `unavailable_markers`
    read comment bodies and there was no comment; the check that carried the
    reason was excluded from the blocking tally. A rate-limited bot rendered
    identically to one that reviewed and found nothing.
    """
    pr_watch = _load_pr_watch()

    status = pr_watch.summarize_review_bots(
        [
            _bot_check(description="Review rate limited"),
            {"name": "toolkit", "state": "SUCCESS", "bucket": "pass", "description": ""},
        ],
        [],
        now=NOW,
    )

    assert [(e["bot"], e["surface"]) for e in status["unavailable"]] == [
        ("coderabbit", "check")
    ]
    assert status["unavailable"][0]["reason"] == "review rate limited"
    # An outage is an ACTION signal, never a gate: making it block would need the
    # informational-check exclusion inverted, and that exclusion is what stops a
    # bot which never reports from wedging the loop.
    assert status["blockers"] == []


def test_the_unavailable_marker_matches_both_surface_wordings() -> None:
    """Same bot, same rate limit, ~1h apart on #22 vs #24 — different wording per
    surface. Matching only the comment phrasing is what made detection depend on
    which surface the bot happened to use that time.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch.review_unavailable_reason("Review rate limited") is not None
    assert pr_watch.review_unavailable_reason("review limit reached") is not None


def test_a_queued_bot_blocks_the_merge_gate_but_never_convergence() -> None:
    """Issue #19: on #16 a receipt was recorded while CodeRabbit's check read
    `PENDING — Review queued`; the merge fired and its four valid findings landed
    minutes later.

    The fix has to hold BOTH halves at once, which is why #19 and #23 could not be
    solved separately: the gate must wait for a queued bot, and the watch loop
    must still be able to terminate while it waits.
    """
    pr_watch = _load_pr_watch()

    report = pr_watch.build_report(
        _green_view(),
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
        check_details=[
            _bot_check(
                state="PENDING",
                bucket="pending",
                description="Review queued",
                startedAt=_minutes_ago(3),
            )
        ],
        now=NOW,
    )

    assert report["converged"] is True  # the loop can finish — no wedge
    assert report["mergeable"] is False  # but the merge waits for the reviewer
    assert report["done"] is report["mergeable"]  # legacy alias stays in lockstep
    assert any("has not reported yet" in b for b in report["merge_blockers"])


def test_a_pending_bot_past_the_grace_window_stops_blocking() -> None:
    """The anti-wedge bound. A review bot's check can sit pending forever after a
    trivial follow-up commit — the documented reason its check is informational
    in the first place. Without a bound, the #19 fix would reintroduce exactly
    the wedge that exclusion exists to prevent, at the merge gate instead of the
    watch loop.
    """
    pr_watch = _load_pr_watch()

    status = pr_watch.summarize_review_bots(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(120))],
        [],
        now=NOW,
        grace_minutes=15,
    )

    assert status["blockers"] == []
    assert status["pending"][0]["blocking"] is False


def test_only_a_check_surface_outage_cancels_the_pending_block() -> None:
    """A check says what the bot is doing NOW; a comment says what it once did.

    `collect_comments` returns the whole PR history, unscoped by head or age. If
    a comment could cancel, one transient rate limit on commit 1 would wave
    through every queued review for the rest of the PR — and since rate limits
    are transient by construction, "this bot was rate-limited earlier" is the
    ordinary state of a later poll, not a corner case. That is issue #19 walking
    back in through the door built to close it.
    """
    pr_watch = _load_pr_watch()
    stuck = [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))]
    stale_outage = [
        {"author": "coderabbitai", "review_unavailable_reason": "review limit reached"}
    ]

    assert pr_watch.summarize_review_bots(stuck, [], now=NOW)["blockers"] != []

    # The historical comment is REPORTED (the operator still needs to see that
    # the primary reviewer had an outage) but does not cancel the live block.
    via_comment = pr_watch.summarize_review_bots(stuck, stale_outage, now=NOW)
    assert via_comment["blockers"] != []
    assert via_comment["unavailable"][0]["surface"] == "comment"

    # The bot's own check saying so DOES cancel. A check whose description
    # carries the outage is classified unavailable outright and never counted as
    # pending at all…
    via_check = pr_watch.summarize_review_bots(
        [
            _bot_check(
                state="PENDING",
                bucket="pending",
                description="Review rate limited",
                startedAt=_minutes_ago(1),
            )
        ],
        [],
        now=NOW,
    )
    assert via_check["blockers"] == []
    assert via_check["pending"] == []
    assert via_check["unavailable"][0]["surface"] == "check"

    # …and it also cancels a SECOND, separately-pending check from the same bot,
    # which is the only way a pending entry can survive to be cancelled.
    two_checks = pr_watch.summarize_review_bots(
        [
            _bot_check(description="Review rate limited"),
            _bot_check(
                name="CodeRabbit / incremental",
                state="PENDING",
                bucket="pending",
                startedAt=_minutes_ago(1),
            ),
        ],
        [],
        now=NOW,
    )
    assert two_checks["blockers"] == []
    assert two_checks["pending"][0]["cancelled_by"] == "outage"


def test_a_lookalike_commenter_cannot_speak_for_the_bot() -> None:
    """Comment authors are attacker-controlled on a public repo; check names are
    the repo's own. Matching them by the same loose rule is what would let
    `xcoderabbit` posting "review skipped" impersonate the reviewer.
    """
    pr_watch = _load_pr_watch()
    bots = ("coderabbit",)

    assert pr_watch._match_bot("CodeRabbit", bots) == "coderabbit"
    assert pr_watch._match_bot("Review / CodeRabbit", bots) == "coderabbit"
    # Authors are anchored: the real bot logins match, a lookalike does not.
    assert pr_watch._match_bot("coderabbitai", bots, anchored=True) == "coderabbit"
    assert pr_watch._match_bot("coderabbitai[bot]", bots, anchored=True) == "coderabbit"
    assert pr_watch._match_bot("xcoderabbit", bots, anchored=True) is None

    # …and an unattributed outage comment is reported with bot None, so it can
    # never suppress anything even if the wording matches.
    status = pr_watch.summarize_review_bots(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))],
        [{"author": "xcoderabbit", "review_unavailable_reason": "review skipped"}],
        now=NOW,
    )
    assert status["unavailable"][0]["bot"] is None
    assert status["blockers"] != []


def test_a_corrupt_or_foreign_clock_value_is_replaced_not_trusted() -> None:
    """`age = parse(stored) or 0.0` would pin an unreadable value at the
    maximally-blocking age AND write it straight back, so every later poll
    re-reads the same poison and the gate blocks forever — a wedge dressed as a
    guard.

    Anything unreadable is treated as "no clock yet" and restamped, whatever
    wrote it: a corrupt file, an older engine, a richer future format.
    """
    pr_watch = _load_pr_watch()
    zero_time = [
        _bot_check(state="PENDING", bucket="pending", startedAt="0001-01-01T00:00:00Z")
    ]

    for poison in (12345, {"at": "2026-07-25T11:00:00Z"}, "0001-01-01T00:00:00+00:00", ""):
        status = pr_watch.summarize_review_bots(
            zero_time, [], now=NOW, pending_since={"coderabbit": poison}
        )
        # Blocks now (age 0 is a real first sighting)…
        assert status["blockers"] != [], poison
        # …but the poison is GONE, replaced by a timestamp that will age out.
        assert status["pending_since"]["coderabbit"] == NOW.isoformat(), poison
        later = pr_watch.summarize_review_bots(
            zero_time,
            [],
            now=NOW + timedelta(minutes=20),
            pending_since=status["pending_since"],
        )
        assert later["blockers"] == [], poison


def test_a_check_with_no_usable_timestamp_falls_back_to_an_observed_clock() -> None:
    """The grace clock cannot come from the check alone — found by running this.

    CodeRabbit's pending status context reports `startedAt: 0001-01-01T00:00:00Z`
    (the zero time). An implementation that reads only the check therefore has no
    age for the one bot the guard exists for, and quietly stops guarding it. The
    first cut of this feature did exactly that, and printed "age unmeasurable,
    NOT blocking" against a live review-in-progress on PR #25.
    """
    pr_watch = _load_pr_watch()
    zero_time = [
        _bot_check(state="PENDING", bucket="pending", startedAt="0001-01-01T00:00:00Z")
    ]

    first = pr_watch.summarize_review_bots(zero_time, [], now=NOW)

    assert first["blockers"] != []  # unseen ⇒ age 0 ⇒ blocking, not waved through
    assert first["pending"][0]["age_source"] == "observed"
    assert first["pending_since"] == {"coderabbit": NOW.isoformat()}

    # …and OUR clock advances, so it always reaches the bound. This is what makes
    # the fallback safe: the block expires on its own, with no wedge to escape.
    later = pr_watch.summarize_review_bots(
        zero_time,
        [],
        now=NOW + timedelta(minutes=20),
        pending_since=first["pending_since"],
    )
    assert later["blockers"] == []
    assert later["pending"][0]["age_minutes"] == 20.0


def test_the_observed_clock_is_head_scoped_and_self_describing() -> None:
    """A clock that restarts every poll never advances, and a guard that never
    advances is a permanent block rather than a bounded one.

    It is stored as `{"head": sha, "bots": {...}}` rather than scoped by the
    sibling `state["head"]` — that field is the false-settle guard's input, and
    putting two intents on one key would mean a second writer maintaining the
    field that decides whether a just-pushed commit may settle.
    """
    pr_watch = _load_pr_watch()
    clock = {"coderabbit": NOW.isoformat()}
    state = pr_watch.write_pending_since({}, "abc123", clock)

    assert state["bot_pending_since"] == {"head": "abc123", "bots": clock}
    assert pr_watch.read_pending_since(state, "abc123") == clock
    # A push means a fresh review: the clock is discarded, not aged.
    assert pr_watch.read_pending_since(state, "def456") == {}
    # Corrupt / legacy / absent state degrades to "no clock", never to a crash.
    for bad in ({}, {"bot_pending_since": "nonsense"}, {"bot_pending_since": {}}):
        assert pr_watch.read_pending_since(bad, "abc123") == {}
    # An empty clock is dropped rather than persisted as a husk.
    assert "bot_pending_since" not in pr_watch.write_pending_since({}, "abc123", {})


def test_persist_poll_carries_the_clock_so_a_later_poll_can_age_it_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The round trip through the REAL persistence writer.

    `persist_poll` is the single source of truth for what a poll stores. A test
    that rebuilt that shape by hand could pass while the engine silently dropped
    the clock — and a dropped clock reads as "first sighting" forever, which is a
    permanent block rather than a bounded one.
    """
    pr_watch = _load_pr_watch()
    zero_time = [
        _bot_check(state="PENDING", bucket="pending", startedAt="0001-01-01T00:00:00Z")
    ]
    store: dict = {}
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: store.update(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: dict(store))

    first = pr_watch.build_report(
        _green_view(), [], set(), check_details=zero_time, now=NOW
    )
    pr_watch.persist_poll(7, first, set())

    assert store["bot_pending_since"] == {
        "head": "abc123",
        "bots": {"coderabbit": NOW.isoformat()},
    }
    assert first["review_bots"]["blockers"] != []

    aged = pr_watch.build_report(
        _green_view(),
        [],
        set(),
        check_details=zero_time,
        now=NOW + timedelta(minutes=20),
        prior_head=store["head"],
        prior_pending_since=pr_watch.read_pending_since(store, "abc123"),
    )
    assert aged["review_bots"]["blockers"] == []


def test_a_reported_bot_drops_out_of_the_persisted_clock() -> None:
    """Otherwise a stale entry outlives the pending state it timed, and a later
    re-review inherits an already-expired clock instead of a fresh window."""
    pr_watch = _load_pr_watch()

    status = pr_watch.summarize_review_bots(
        [_bot_check()],  # terminal — the bot reported
        [],
        now=NOW,
        pending_since={"coderabbit": (NOW - timedelta(minutes=5)).isoformat()},
    )

    assert status["pending"] == []
    assert status["pending_since"] == {}


def test_an_outage_stays_visible_after_the_notice_comment_is_acked() -> None:
    """The comment surface used to be the ONLY record that the primary reviewer
    never ran — and `--mark-seen` erases it from `new_comments`. Aggregating the
    outage separately is what keeps the gap readable at merge time rather than
    reconstructible only from the PR thread.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        comments=[
            {
                "id": "c1",
                "author": {"login": "coderabbitai"},
                "body": "Review limit reached — try again later.",
            }
        ]
    )

    report = pr_watch.build_report(
        view,
        [],
        # Every key of that comment already acked: it is gone from new_comments.
        set(pr_watch.build_report(view, [], set(), now=NOW)["all_seen_keys"]),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
        now=NOW,
    )

    assert report["new_comments"] == []
    assert report["review_bots"]["unavailable"][0]["reason"] == "review limit reached"
    assert "review unavailable" in pr_watch.render(report)


def test_a_bot_that_never_posts_a_check_blocks_nothing() -> None:
    """The repo with no review bot, and the bot that simply does not run on this
    PR. Absent is not pending: an empty rollup must add no blocker at all.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch.summarize_review_bots([], [], now=NOW)["blockers"] == []
    assert (
        pr_watch.summarize_review_bots(
            [{"name": "toolkit", "state": "PENDING", "bucket": "pending"}], [], now=NOW
        )["blockers"]
        == []
    )
    assert (
        pr_watch.summarize_review_bots(
            [_bot_check(state="PENDING", bucket="pending")], [], now=NOW, bots=()
        )["blockers"]
        == []
    )


def test_check_detail_fetch_never_raises_and_degrades_to_no_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`gh pr checks` exits non-zero for ordinary states (8 = something pending,
    1 = something failing) and errors outright on a PR with no checks. Trusting
    the exit code would drop the bot signal on the most common polls; raising
    would wedge the loop on a PR that has none.
    """
    pr_watch = _load_pr_watch()

    class _Result:
        def __init__(self, stdout: str, returncode: int) -> None:
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = ""

    monkeypatch.setattr(
        pr_watch.subprocess,
        "run",
        lambda *a, **k: _Result('[{"name":"CodeRabbit","state":"PENDING"}]', 8),
    )
    assert pr_watch.fetch_check_details(1) == (
        [{"name": "CodeRabbit", "state": "PENDING"}],
        "ok",
    )

    monkeypatch.setattr(
        pr_watch.subprocess, "run", lambda *a, **k: _Result("no checks reported", 1)
    )
    assert pr_watch.fetch_check_details(1) == ([], "unavailable")

    def _boom(*a, **k):
        raise OSError("gh is not installed")

    monkeypatch.setattr(pr_watch.subprocess, "run", _boom)
    assert pr_watch.fetch_check_details(1) == ([], "unavailable")

    # No bots configured is a THIRD state: nothing to read, not a failed read.
    assert pr_watch.fetch_check_details(1, bots=()) == ([], "skipped")


def test_losing_the_bot_signal_warns_once_rather_than_degrading_silently(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both new guards depend on this fetch, so a silent `[]` disables them
    without a trace.

    An older `gh` that rejects one of the requested `--json` fields fails exactly
    this way, and "checked and clean" would be indistinguishable from "never
    checked" — the failure mode that cost this repo three silent-no-op bugs in
    one session. Once per process, not per poll: a warning repeated every round
    of a watch loop is skimmed past exactly like silence.
    """
    pr_watch = _load_pr_watch()

    class _Result:
        stdout = ""
        stderr = 'unknown JSON field: "startedAt"'
        returncode = 1

    monkeypatch.setattr(pr_watch.subprocess, "run", lambda *a, **k: _Result())

    assert pr_watch.fetch_check_details(1).rows == []
    first = capsys.readouterr().err
    assert "unknown JSON field" in first
    assert "will not be detected" in first

    assert pr_watch.fetch_check_details(1).rows == []
    assert capsys.readouterr().err == ""  # not once per poll


def test_record_review_refuses_while_the_bot_is_still_queued(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The #16 sequence, mechanized at the moment the judgment is made.

    Every input `decide_done` could see was correct at that instant — CI green,
    no unacked comments, a receipt bound to the exact head. The one thing that
    was wrong was the reviewer's own state, which nothing consulted.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda args: {"number": 16, "headRefOid": "abc123"},
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails(
            [
                _bot_check(
                    state="PENDING",
                    bucket="pending",
                    description="Review queued",
                    startedAt=_minutes_ago(2),
                )
            ],
            "ok",
        ),
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    with pytest.raises(ValueError, match="has not reported yet"):
        pr_watch.record_review(16, "fallback:codex", "abc123", now=NOW)
    # No receipt was persisted. The grace clock IS written on the refusal path —
    # without it a cold `--record-review` restarts the clock at zero on every
    # retry, so the refusal could never expire.
    assert all("review_receipt" not in state for state in recorded)

    # The documented override is the only way past it, and it is explicit.
    pr_watch.record_review(
        16, "fallback:codex", "abc123", allow_pending_bot=True, now=NOW
    )
    assert recorded[-1]["review_receipt"]["source"] == "fallback:codex"


def test_a_cold_record_review_refusal_expires_instead_of_wedging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--record-review` outside a poll loop must still see a clock that advances.

    The bot here reports no usable timestamp (CodeRabbit's real behaviour), so
    the clock is the engine's own first sighting. If the refusal path did not
    persist it, every retry would restart at zero and the only way past would be
    the override — a wedge dressed as a guard.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda args: {"number": 16, "headRefOid": "abc123"},
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails(
            [
                _bot_check(
                    state="PENDING", bucket="pending", startedAt="0001-01-01T00:00:00Z"
                )
            ],
            "ok",
        ),
    )
    store: dict = {}
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: store.update(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: dict(store))

    with pytest.raises(ValueError, match="has not reported yet"):
        pr_watch.record_review(16, "fallback:codex", "abc123", now=NOW)
    assert store["bot_pending_since"] == {
        "head": "abc123",
        "bots": {"coderabbit": NOW.isoformat()},
    }

    # Retrying still refuses, and — the point — does NOT reset the clock.
    with pytest.raises(ValueError, match="has not reported yet"):
        pr_watch.record_review(
            16, "fallback:codex", "abc123", now=NOW + timedelta(minutes=1)
        )
    assert store["bot_pending_since"]["bots"] == {"coderabbit": NOW.isoformat()}

    # …so past the grace window it goes through on its own, with no override.
    pr_watch.record_review(
        16, "fallback:codex", "abc123", now=NOW + timedelta(minutes=20)
    )
    assert store["review_receipt"]["source"] == "fallback:codex"


def test_record_review_allows_the_fallback_when_the_bot_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal must not block the path it exists to protect.

    "A blocked bot is an action signal, run the fallback" is the doctrine — so
    once the bot's own check reports the outage, the fallback receipt goes
    through immediately rather than waiting out the grace window.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 22, "headRefOid": "32f3e4f"}
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails(
            [
                _bot_check(
                    state="PENDING",
                    bucket="pending",
                    description="Review rate limited",
                    startedAt=_minutes_ago(1),
                )
            ],
            "ok",
        ),
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    pr_watch.record_review(22, "fallback:codex", "32f3e4f", now=NOW)

    assert recorded[0]["review_receipt"]["source"] == "fallback:codex"
    assert "override" not in recorded[0]["review_receipt"]


def test_a_future_dated_clock_is_replaced_rather_than_clamped() -> None:
    """The incomplete half of the poison-clock fix.

    An unparseable value is replaced, but a future-dated one is perfectly
    *parseable* — so it survived, got clamped to age 0 by `max(0.0, …)`, and was
    re-persisted verbatim. The block then lasted until real time caught up with
    the stamp: a state file copied between machines, or a VM clock that ran ahead
    and was NTP-corrected back, could hold the merge gate for days.
    """
    pr_watch = _load_pr_watch()
    zero_time = [
        _bot_check(state="PENDING", bucket="pending", startedAt="0001-01-01T00:00:00Z")
    ]
    far_future = (NOW + timedelta(days=30)).isoformat()

    status = pr_watch.summarize_review_bots(
        zero_time, [], now=NOW, pending_since={"coderabbit": far_future}
    )

    assert status["pending_since"]["coderabbit"] == NOW.isoformat()
    assert status["blockers"] != []
    # …and it ages out on our clock, in minutes rather than in a month.
    later = pr_watch.summarize_review_bots(
        zero_time,
        [],
        now=NOW + timedelta(minutes=20),
        pending_since=status["pending_since"],
    )
    assert later["blockers"] == []

    # Small skew stays tolerated — a check GitHub stamped a few seconds ahead of
    # our clock is normal and must not be thrown away as corruption.
    skewed = (NOW + timedelta(seconds=30)).isoformat()
    assert pr_watch._age_minutes(skewed, NOW) == 0.0


def test_a_failed_check_read_is_recorded_on_the_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The silent bypass, and the worse of the two.

    When the check read fails there are no blockers to raise, so the receipt is
    taken with the #19 guard simply switched off. Recording the deliberate
    override but not this would leave the intentional escape auditable and the
    accidental one invisible.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 9, "headRefOid": "abc123"}
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails([], "unavailable"),
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    report = pr_watch.record_review(9, "fallback:codex", "abc123", now=NOW)

    assert recorded[0]["review_receipt"]["bot_signal"] == "unavailable"
    assert "guard did not run" in pr_watch.render_record_review(report)


def test_the_override_is_recorded_on_the_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The escape hatch on a safety gate is the one thing that must leave a
    trace — otherwise a receipt taken over an active override reads exactly like
    one taken after a clean bot verdict."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 9, "headRefOid": "abc123"}
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    pr_watch.record_review(
        9, "fallback:codex", "abc123", allow_pending_bot=True, now=NOW
    )

    assert recorded[0]["review_receipt"]["override"] == "pending-bot"


def test_an_unreadable_bot_signal_is_machine_readable_not_just_a_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`dev_session.sh merge` consumes the JSON on stdout; stderr scrolls past on
    an autonomous run.

    A failed fetch produces a `review_bots` block otherwise byte-identical to a
    genuinely clean bot, so without this field "both guards are off" and "the
    bot is fine" are the same report.
    """
    pr_watch = _load_pr_watch()

    clean = pr_watch.build_report(
        _green_view(), [], set(), check_details=[_bot_check()], now=NOW
    )
    blind = pr_watch.build_report(
        _green_view(),
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "unavailable"),
        now=NOW,
    )

    assert clean["review_bots"]["signal"] == "ok"
    assert blind["review_bots"]["signal"] == "unavailable"
    assert "could not be read" in pr_watch.render(blind)
    assert "could not be read" not in pr_watch.render(clean)
    # Still fail-open on the gate — an old `gh` is an environment problem, and
    # blocking on it would turn that into a wedge. Visible, not blocking.
    assert blind["review_bots"]["blockers"] == []


def test_a_cancelled_pending_check_is_not_reported_as_aged_out() -> None:
    """The single `not blocking` branch printed "past the 15m grace" for a
    check cancelled by an outage — which is a 1-minute-old check being given a
    reason that is simply false, in exactly the #22/#24 scenario this PR is
    built on."""
    pr_watch = _load_pr_watch()

    cancelled = pr_watch.summarize_review_bots(
        [
            _bot_check(description="Review rate limited"),
            _bot_check(
                name="CodeRabbit / incremental",
                state="PENDING",
                bucket="pending",
                startedAt=_minutes_ago(1),
            ),
        ],
        [],
        now=NOW,
    )
    assert cancelled["pending"][0]["cancelled_by"] == "outage"
    aged = pr_watch.summarize_review_bots(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(120))],
        [],
        now=NOW,
    )

    def _render(status):
        return pr_watch.render(
            {
                "pr": 1, "url": "u", "converged": True, "mergeable": False,
                "checks": {"success": 1, "total": 1, "pending": 0, "failing": []},
                "new_comments": [], "merge_blockers": [], "review_bots": status,
            }
        )

    assert "past the" not in _render(cancelled)
    assert "review unavailable [check]" in _render(cancelled)
    assert "past the 15m grace" in _render(aged)


def test_the_grace_bound_uses_the_exact_age_not_the_rounded_one() -> None:
    """`age_minutes` is rounded to one decimal for display. Comparing the
    rounded value lets a 14.96m check round its way past a 15m bound."""
    pr_watch = _load_pr_watch()

    status = pr_watch.summarize_review_bots(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(14.96))],
        [],
        now=NOW,
        grace_minutes=15,
    )

    assert status["pending"][0]["age_minutes"] == 15.0  # display rounds up
    assert status["blockers"] != []  # …the bound does not


def test_bot_state_never_reaches_the_watch_loop_predicate() -> None:
    """The load-bearing invariant, pinned directly rather than inferred.

    Everything in this section feeds the merge gate. If any of it ever reached
    `decide_converged`, a bot that never reports would wedge the poll/fix/ack
    loop forever — the failure the informational-check exclusion exists to
    prevent, and the constraint that made #19 and #23 unfixable in isolation.
    """
    pr_watch = _load_pr_watch()
    view = _green_view()

    baseline = pr_watch.build_report(view, [], set(), now=NOW)
    for details in (
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))],
        [_bot_check(description="Review rate limited")],
        [_bot_check(state="PENDING", bucket="pending", startedAt=None)],
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(999))],
    ):
        report = pr_watch.build_report(
            view, [], set(), check_details=details, now=NOW
        )
        assert report["converged"] is baseline["converged"] is True, details
        assert report["checks"] == baseline["checks"], details


def test_bot_blockers_only_ever_tighten_the_merge_gate() -> None:
    """The skew direction that makes this safe to ship per-file.

    Engine upgrades are per-file, so a new `pr_watch.py` can run against an older
    `dev_session.sh` whose gate reads `done`. Adding a blocker can only make
    `done` false where it was true — merges wait, never fire early. The reverse
    would be a silent fail-open on an unreviewed PR.
    """
    pr_watch = _load_pr_watch()
    args = dict(review_receipt={"head": "abc123", "source": "coderabbit"}, now=NOW)

    without = pr_watch.build_report(_green_view(), [], set(), **args)
    with_pending = pr_watch.build_report(
        _green_view(),
        [],
        set(),
        check_details=[
            _bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))
        ],
        **args,
    )

    assert without["done"] is True
    assert with_pending["done"] is False
    # Strictly a superset — no pre-existing blocker was dropped to make room.
    assert set(without["merge_blockers"]) <= set(with_pending["merge_blockers"])


# --------------------------------------------------------------------------- #
# review-bot knowledge comes from config, not from engine literals
# --------------------------------------------------------------------------- #


ADOPTER_CONFIG = """review:
  bots: [OtherBot]
  noise_markers:
    - "<!-- Generated by OtherBot -->"
    - "NOTHING TO REPORT"
  unavailable_markers:
    - "OtherBot Is Out Of Credits"
  informational_checks: [OtherBot, " Advisory "]
  require_ci: false
  bot_pending_grace_minutes: 30
"""


def _write_config(tmp_path: Path, body: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "dev-model.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_review_knowledge_is_read_from_config_not_engine_literals(
    tmp_path: Path,
) -> None:
    pr_watch = _load_pr_watch()

    resolved = pr_watch._load_review_config(_write_config(tmp_path, ADOPTER_CONFIG))

    # Lower-cased/stripped at load so every call site can keep matching
    # case-insensitively against a folded body / check name.
    assert resolved.noise_markers == (
        "<!-- generated by otherbot -->",
        "nothing to report",
    )
    assert resolved.unavailable_markers == ("otherbot is out of credits",)
    assert resolved.informational_checks == frozenset({"otherbot", "advisory"})
    assert resolved.require_ci is False
    assert resolved.bots == ("otherbot",)
    assert resolved.bot_pending_grace_minutes == 30
    # None of the kit's own default markers leak in — config replaces, not extends.
    assert "<!-- walkthrough_start -->" not in resolved.noise_markers


def test_missing_config_falls_back_to_defaults_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A standalone engine run (no config at all) must behave exactly as before."""
    pr_watch = _load_pr_watch()

    resolved = pr_watch._load_review_config(tmp_path / "absent.yaml")

    assert resolved == (
        pr_watch._DEFAULT_NOISE_MARKERS,
        pr_watch._DEFAULT_REVIEW_UNAVAILABLE_MARKERS,
        frozenset(pr_watch._DEFAULT_INFORMATIONAL_CHECK_NAMES),
        True,
        pr_watch._DEFAULT_REVIEW_BOTS,
        pr_watch._DEFAULT_BOT_PENDING_GRACE_MINUTES,
    )
    assert capsys.readouterr().err == ""


def test_unreadable_config_warns_and_falls_back_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A config that exists but can't be read must never wedge the watch loop —
    fall back to defaults, but say so, so an ignored config stays visible."""
    pr_watch = _load_pr_watch()
    path = _write_config(tmp_path, ADOPTER_CONFIG)
    path.chmod(0o000)
    if path.is_file():
        try:
            path.read_text(encoding="utf-8")
        except OSError:
            pass
        else:  # pragma: no cover - only when tests run as root
            pytest.skip("cannot make a file unreadable (running as root?)")

    resolved = pr_watch._load_review_config(path)

    assert resolved.require_ci is True  # NOT the config's require_ci: false
    assert resolved.noise_markers == pr_watch._DEFAULT_NOISE_MARKERS
    assert "could not read review config" in capsys.readouterr().err


def test_explicit_empty_noise_list_is_honored_but_absent_key_is_not(
    tmp_path: Path,
) -> None:
    """`noise_markers: []` means "filter nothing" (an adopter with no bots);
    an absent key means "use the kit's defaults". The two must not collapse."""
    pr_watch = _load_pr_watch()

    empty = pr_watch._load_review_config(
        _write_config(tmp_path / "a", "review:\n  noise_markers: []\n")
    )
    absent = pr_watch._load_review_config(
        _write_config(tmp_path / "b", "review:\n  bots: [coderabbit]\n")
    )

    assert empty.noise_markers == ()
    assert absent.noise_markers == pr_watch._DEFAULT_NOISE_MARKERS


def test_non_boolean_require_ci_keeps_the_safe_default(tmp_path: Path) -> None:
    """Only a real boolean flips the CI requirement — a stray `yes` must not
    silently let a zero-check PR read as green."""
    pr_watch = _load_pr_watch()

    for value in ("yes", "0", '"false"'):
        resolved = pr_watch._load_review_config(
            _write_config(tmp_path, f"review:\n  require_ci: {value}\n")
        )
        assert resolved.require_ci is True, value


def test_non_numeric_or_negative_grace_keeps_the_default(tmp_path: Path) -> None:
    """The pending-bot bound must survive a typo.

    `true` is the interesting one: `bool` is an `int` subclass, so a naive
    isinstance check would read it as a grace of 1 minute — turning the #19
    guard off for every bot that takes longer than a minute to review, which is
    all of them.
    """
    pr_watch = _load_pr_watch()

    for value in ("soon", "true", "-5", '"15"'):
        resolved = pr_watch._load_review_config(
            _write_config(tmp_path, f"review:\n  bot_pending_grace_minutes: {value}\n")
        )
        assert (
            resolved.bot_pending_grace_minutes
            == pr_watch._DEFAULT_BOT_PENDING_GRACE_MINUTES
        ), value

    # …but a real number, including 0 ("never wait"), is honored.
    for value, expected in (("0", 0.0), ("2.5", 2.5), ("60", 60.0)):
        resolved = pr_watch._load_review_config(
            _write_config(tmp_path, f"review:\n  bot_pending_grace_minutes: {value}\n")
        )
        assert resolved.bot_pending_grace_minutes == expected, value


def test_configured_unavailable_marker_still_beats_configured_noise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The "a down reviewer is never auto-noise" invariant is a property of the
    engine, not of which list a marker happens to sit on in config."""
    pr_watch = _load_pr_watch()
    resolved = pr_watch._load_review_config(
        _write_config(
            tmp_path,
            'review:\n  noise_markers: ["OtherBot Is Out Of Credits"]\n'
            '  unavailable_markers: ["OtherBot Is Out Of Credits"]\n',
        )
    )
    monkeypatch.setattr(pr_watch, "_NOISE_MARKERS", resolved.noise_markers)
    monkeypatch.setattr(
        pr_watch, "_REVIEW_UNAVAILABLE_MARKERS", resolved.unavailable_markers
    )

    body = "OtherBot is out of credits for this repo."

    assert pr_watch.review_unavailable_reason(body) == "otherbot is out of credits"
    assert pr_watch.is_noise(body) is False


def test_every_config_derived_global_is_pinned() -> None:
    """``_pin_engine_defaults`` must overwrite EVERY config-derived global.

    Guarding this by loading normally and comparing against the defaults does
    not work, and the first version of this test made exactly that mistake: for
    any field where this repo's config happens to AGREE with the engine default
    the comparison passes whether or not the pin ran. A per-line mutation sweep
    showed 5 of the 7 pins were unguarded that way — including ``_REVIEW_BOTS``,
    the one field whose ambient value caused the bug this all exists to fix.
    Deleting its pin left the suite green here while restoring the entire
    failure for an adopter with ``review.bots: []``.

    So seed every global with a sentinel the defaults cannot equal, then pin.
    Each assertion below fails if — and only if — its own line is missing from
    ``_pin_engine_defaults``, whatever the ambient config says.

    The field list is DERIVED from ``ReviewConfig`` rather than hand-written: a
    hand-written list makes "EVERY" a promise the body cannot keep, and an
    adversarial pass proved it by adding an 8th config-derived global and
    watching this test pass. The mapping below must therefore stay exhaustive
    over ``ReviewConfig._fields``, which the first assertion enforces.
    """
    pr_watch = _load_pr_watch(pin_defaults=False)

    # global name -> (sentinel, ReviewConfig field it must be re-derived from)
    pinned_globals = {
        "_NOISE_MARKERS": (("zzz-sentinel-noise",), "noise_markers"),
        "_REVIEW_UNAVAILABLE_MARKERS": (("zzz-sentinel-unavail",), "unavailable_markers"),
        "_INFORMATIONAL_CHECK_NAMES": (frozenset({"zzz-sentinel-check"}), "informational_checks"),
        "_REQUIRE_CI": ("zzz-sentinel-require-ci", "require_ci"),
        "_REVIEW_BOTS": (("zzz-sentinel-bot",), "bots"),
        "_BOT_PENDING_GRACE_MINUTES": (-99999.0, "bot_pending_grace_minutes"),
    }

    # If someone adds a field to ReviewConfig, this fails until they extend the
    # map above — which is what makes the test's name honest.
    assert set(pr_watch.ReviewConfig._fields) == {
        field for _, field in pinned_globals.values()
    }

    expected = pr_watch._load_review_config(ENGINE_DIR / "nope" / "dev-model.yaml")
    for name, (sentinel, _field) in pinned_globals.items():
        setattr(pr_watch, name, sentinel)
    pr_watch._REVIEW_CONFIG = "zzz-sentinel-config"

    _pin_engine_defaults(pr_watch)

    assert expected == pr_watch._REVIEW_CONFIG
    for name, (sentinel, field) in pinned_globals.items():
        actual = getattr(pr_watch, name)
        assert actual != sentinel, f"{name} was not re-pinned"
        assert actual == getattr(expected, field), f"{name} != defaults.{field}"


def test_the_default_loader_pins_but_the_opt_out_does_not() -> None:
    """The pinning must be wired into ``_load_pr_watch``, and
    ``pin_defaults=False`` must genuinely leave the ambient config in place —
    otherwise the shipped-config tests below assert about defaults.

    The discriminator is computed WITHOUT ``_load_pr_watch``, deliberately. An
    earlier cut derived the skip condition from the very function under test,
    so "the opt-out is broken" and "this repo's config equals the defaults"
    were indistinguishable — and it resolved that ambiguity toward *skip*. An
    adversarial pass then showed two one-line regressions it silently
    permitted, including the exact one this test exists to prevent. Reading the
    config independently means a broken opt-out FAILS and only a genuinely
    indistinguishable config skips.
    """
    fresh = _load_pr_watch(pin_defaults=False)
    ambient_config = fresh._load_review_config()
    defaults = fresh._load_review_config(ENGINE_DIR / "nope" / "dev-model.yaml")
    if ambient_config.noise_markers == defaults.noise_markers:
        pytest.skip(
            "ambient config's noise_markers equal the engine defaults — no "
            "discriminator exists in this repo, so pinned and unpinned are "
            "indistinguishable by construction"
        )

    pinned = _load_pr_watch()
    unpinned = _load_pr_watch(pin_defaults=False)

    assert defaults.noise_markers == pinned._NOISE_MARKERS
    assert ambient_config.noise_markers == unpinned._NOISE_MARKERS
    assert defaults.noise_markers != unpinned._NOISE_MARKERS


def test_shipped_config_preserves_the_engine_defaults_behavior() -> None:
    """This repo's own config/dev-model.yaml must classify exactly as the
    literals it replaced — the behavior-preservation argument for BUG 3.

    ``pin_defaults=False`` is load-bearing: THIS repo's config is the subject.
    Loading the pinned module here would assert that the defaults classify like
    the defaults — a tautology that stays green no matter what the shipped
    config says. Not hypothetical: the first cut of the pinning change left this
    test on the pinned loader, and corrupting ``review.noise_markers`` then went
    from "this test fails" to "the whole suite is green".

    It SKIPS for an adopter who has deliberately emptied the marker lists.
    ``_load_review_config``'s own docstring documents ``noise_markers: []`` as
    supported ("an adopter with no review bots wants no filtering"), so a repo
    in that state must not get a red kit suite — that is the same bug this
    module's loader change exists to remove, one field over. ``adopt.md`` tells
    adopters to run this suite against their own config, so it has to hold for
    a legitimately-configured adopter, not just for this repo.
    """
    pr_watch = _load_pr_watch(pin_defaults=False)

    if not pr_watch._NOISE_MARKERS or not pr_watch._REVIEW_UNAVAILABLE_MARKERS:
        pytest.skip(
            "ambient config empties a marker list — a supported adopter state "
            "in which this repo's classification claims do not apply"
        )

    walkthrough = (
        "<!-- This is an auto-generated comment: summarize by coderabbit.ai -->\n"
        "<!-- walkthrough_start -->\nSummary only.\n"
    )
    assert pr_watch.is_noise(walkthrough) is True
    assert pr_watch.is_noise("Actionable comments posted: 0") is True
    # Unavailability notices: surfaced, never noise (either list, either case).
    for body in (
        "Bugbot needs on-demand usage enabled",
        "Review skipped",
        "Review limit reached",
        "No review credits",
    ):
        assert pr_watch.review_unavailable_reason(body) is not None, body
        assert pr_watch.is_noise(body) is False, body
    # `require_ci` is ADOPTER-owned, so assert the wiring rather than this
    # repo's literal: a repo that legitimately sets `require_ci: false`
    # (documented for a repo with no CI at all) must not fail a kit test.
    #
    # There is deliberately no assertion on `_INFORMATIONAL_CHECK_NAMES` here.
    # An earlier cut asserted every name was lowercase, which BOTH review lenses
    # flagged as unfalsifiable: `_load_review_config` lowercases by construction
    # and the set is empty (so vacuously true) under `informational_checks: []`.
    # It replaced a falsifiable literal with nothing. The `.lower()` behaviour it
    # appeared to cover is genuinely pinned by
    # `test_review_knowledge_is_read_from_config_not_engine_literals`.
    assert pr_watch.summarize_checks([])["all_green"] is (not pr_watch._REQUIRE_CI)


def test_normal_coderabbit_walkthrough_remains_noise() -> None:
    pr_watch = _load_pr_watch()
    body = """<!-- This is an auto-generated comment: summarize by coderabbit.ai -->
<!-- walkthrough_start -->
Summary only.
"""
    view = _green_view(
        comments=[
            {"id": "summary-1", "author": {"login": "coderabbitai"}, "body": body}
        ]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "coderabbit"},
    )

    assert report["new_comments"] == []
    assert report["done"] is True


# --------------------------------------------------------------------------- #
# review coverage: which commit the bot's last review actually saw (issue #27)
# --------------------------------------------------------------------------- #


def _review(login: str, sha: str, at: str) -> dict:
    return {"author": {"login": login}, "commit": {"oid": sha}, "submittedAt": at}


def test_a_bot_whose_last_review_predates_the_head_is_surfaced() -> None:
    """The #22 shape, and #25's smaller repeat.

    A receipt binds to the head and a push invalidates it — which answers "was
    this exact code reviewed", not "by whom, and how much of it did they see".
    A bot can review commit 1, go rate-limited through a material redesign, and
    the merge proceeds on a fallback receipt taken at commit 5. Nothing said so.
    """
    pr_watch = _load_pr_watch()
    reviews = [
        _review("coderabbitai", "aaaaaaa1", "2026-07-25T12:00:00Z"),
        _review("coderabbitai", "bbbbbbb2", "2026-07-25T13:00:00Z"),  # newest
        _review("topij", "ccccccc3", "2026-07-25T14:00:00Z"),  # not a bot
    ]

    behind = pr_watch.bot_review_coverage(reviews, "zzzzzzz9")
    current = pr_watch.bot_review_coverage(reviews, "bbbbbbb2")

    # Newest review per bot wins, and a human's review is not a bot's coverage.
    assert [e["bot"] for e in behind] == ["coderabbit"]
    assert behind[0]["sha"] == "bbbbbbb2"
    assert behind[0]["covers_head"] is False
    assert current[0]["covers_head"] is True


def test_review_coverage_is_reported_and_never_gates() -> None:
    """Deliberately the cheap half of #27. Invalidating a receipt when the diff
    changes *shape* is the faithful fix, but it risks becoming a wedge on a repo
    whose bot is permanently unavailable — so this only makes the gap visible at
    merge time instead of reconstructible from the PR thread afterwards.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(
        view, [], set(), review_receipt={"head": "abc123", "source": "fallback:panel"}
    )

    assert report["review_bots"]["coverage"][0]["covers_head"] is False
    assert "review coverage" in pr_watch.render(report)
    assert "0ldc0de" in pr_watch.render(report)
    # …and the merge gate is untouched by it.
    assert report["mergeable"] is True
    assert report["merge_blockers"] == []


def test_coverage_tolerates_a_missing_or_malformed_commit_field() -> None:
    """`gh` shapes drift and a review can predate the field. Anything unusable
    is dropped rather than reported as coverage of an unknown commit — and it
    must never raise, since this feeds the ordinary poll path."""
    pr_watch = _load_pr_watch()

    assert pr_watch.bot_review_coverage([], "abc") == []
    assert pr_watch.bot_review_coverage(None, "abc") == []
    assert (
        pr_watch.bot_review_coverage(
            [
                {"author": {"login": "coderabbitai"}, "submittedAt": "x"},  # no commit
                {"author": {"login": "coderabbitai"}, "commit": "oops"},  # not a dict
                {"author": {"login": "coderabbitai"}, "commit": {}},  # no oid
            ],
            "abc",
        )
        == []
    )
    # No head to compare against: reported, but never claimed to cover it.
    orphan = pr_watch.bot_review_coverage(
        [_review("coderabbitai", "aaa", "2026-07-25T12:00:00Z")], None
    )
    assert orphan[0]["covers_head"] is False


def test_the_coverage_warning_is_silent_when_the_bot_is_current() -> None:
    """Selectivity is the entire value of this warning, and it was the one thing
    left unpinned after a dedicated mutation pass.

    Two mutants survived on the same hole: rendering the line unconditionally,
    and wiring the WRONG head into the coverage call. Both are invisible unless
    a test drives `build_report` -> `render` with a bot whose last review IS at
    the head and asserts silence — unit-level `covers_head is True` does not.
    """
    pr_watch = _load_pr_watch()
    at_head = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )
    behind = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )

    assert "review coverage" not in pr_watch.render(
        pr_watch.build_report(at_head, [], set())
    )
    assert "review coverage" in pr_watch.render(
        pr_watch.build_report(behind, [], set())
    )


def test_the_coverage_warning_defers_to_a_bot_that_is_mid_review() -> None:
    """A bot reviewing a just-pushed head is behind it by construction.

    The pending line already says a verdict is coming, so warning as well would
    fire on every poll of the healthy window — training the operator to skim
    past the case this exists for, a reviewer that went away commits ago.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )
    mid_review = [
        _bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))
    ]

    quiet = pr_watch.render(
        pr_watch.build_report(view, [], set(), check_details=mid_review, now=NOW)
    )
    loud = pr_watch.render(pr_watch.build_report(view, [], set(), now=NOW))

    assert "review coverage" not in quiet
    assert "has not reported yet" in quiet  # the pending line still says it
    assert "review coverage" in loud


def test_a_receipt_records_which_bots_were_behind_the_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The message says "a receipt taken now does not mean it saw this design" —
    and it was printing everywhere except where a receipt is taken.

    `override` and `bot_signal` both record what a receipt does NOT stand for.
    This is their sibling, and it was absent from the one path whose entire
    subject is what the receipt covers.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda args: {
            "number": 9,
            "headRefOid": "abc123",
            "reviews": [_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")],
        },
    )
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "ok")
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    report = pr_watch.record_review(9, "fallback:codex", "abc123", now=NOW)

    assert recorded[0]["review_receipt"]["bots_behind_head"] == {"coderabbit": "0ldc0de"}
    assert "does not stand for its review" in pr_watch.render_record_review(report)


def test_the_override_path_still_records_which_bots_were_behind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--allow-pending-bot-review` IS the #22/#25 scenario.

    A bot queued or rate-limited through a redesign, merged on a fallback
    receipt — the exact case this feature was written for. Computing `behind`
    inside `if not allow_pending_bot` made the receipt silent precisely there,
    and combined with the pending-deference below it was a total blind spot:
    neither the poll nor the receipt said the reviewer's last review was old.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_gh_json",
        lambda args: {
            "number": 9,
            "headRefOid": "abc123",
            "reviews": [_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")],
        },
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    report = pr_watch.record_review(
        9, "fallback:codex", "abc123", allow_pending_bot=True, now=NOW
    )
    receipt = recorded[0]["review_receipt"]

    assert receipt["override"] == "pending-bot"
    assert receipt["bots_behind_head"] == {"coderabbit": "0ldc0de"}
    rendered = pr_watch.render_record_review(report)
    assert "recorded over an active override" in rendered
    assert "does not stand for its review" in rendered


def test_only_a_blocking_pending_bot_silences_the_coverage_warning() -> None:
    """The deference must not swallow the case it claims to protect.

    A pending check that has aged past the grace window, or been cancelled by an
    announced outage, is the engine saying "this verdict is not coming" — the
    reviewer-went-away case. Deferring to *any* pending entry suppressed the
    coverage warning in exactly that situation, reachable after ~15 minutes of
    polling any stuck bot, and on the #22 two-check outage shape.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )

    def _render(details):
        return pr_watch.render(
            pr_watch.build_report(view, [], set(), check_details=details, now=NOW)
        )

    # Actively blocking (mid-review) — deferred, as designed.
    assert "review coverage" not in _render(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))]
    )
    # Aged past grace — "treated as not coming", so coverage MUST speak up.
    assert "review coverage" in _render(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(600))]
    )
    # Cancelled by an announced outage — the #22 shape. Same.
    assert "review coverage" in _render(
        [
            _bot_check(description="Review rate limited"),
            _bot_check(
                name="CodeRabbit / incremental",
                state="PENDING",
                bucket="pending",
                startedAt=_minutes_ago(1),
            ),
        ]
    )


def test_coverage_honours_a_non_default_review_bots_list() -> None:
    """`bots=bots` threading was correct and pinned by nothing — dropping it
    passed the whole suite, because every other test uses the default list where
    scoped and unscoped are identical."""
    pr_watch = _load_pr_watch()
    reviews = [
        _review("otherbot", "0ldc0de", "2026-07-25T12:00:00Z"),
        _review("coderabbitai", "abc123", "2026-07-25T13:00:00Z"),
    ]

    scoped = pr_watch.summarize_review_bots(
        [], [], now=NOW, bots=("otherbot",), reviews=reviews, head="abc123"
    )

    assert [e["bot"] for e in scoped["coverage"]] == ["otherbot"]
    assert scoped["coverage"][0]["covers_head"] is False
    # …and a repo with no bots configured gets no coverage at all.
    assert (
        pr_watch.summarize_review_bots(
            [], [], now=NOW, bots=(), reviews=reviews, head="abc123"
        )["coverage"]
        == []
    )


def test_an_unusable_timestamp_sorts_to_the_bottom_not_the_top() -> None:
    """`str()` coercion is crash-proof and actively wrong.

    It renders garbage as a string sorting ABOVE every real timestamp
    (`"20260725" > "2026-07-25T…"`), so a malformed review at the head displaces
    the real dated one and sets `covers_head` — suppressing the warning. The
    neighbouring crash test fed exactly this input and asserted only that it did
    not raise, walking straight over the hole.
    """
    pr_watch = _load_pr_watch()
    dated = _review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")

    for junk in (20260725, {"x": 1}, ["a"], 3.5):
        at_head = {
            "author": {"login": "coderabbitai"},
            "commit": {"oid": "current"},
            "submittedAt": junk,
        }
        covered = pr_watch.bot_review_coverage([dated, at_head], "current")
        assert covered[0]["sha"] == "0ldc0de", junk
        assert covered[0]["covers_head"] is False, junk


def test_a_lookalike_login_cannot_claim_the_bot_reviewed_this_head() -> None:
    """The one property here with an actual adversary.

    On a public repo any account can open a review, so `xcoderabbit` reviewing
    the current head must not read as CodeRabbit having covered it — that would
    suppress the very warning this feature exists to raise. Anchored matching
    gives that; without a test, flipping `anchored=True` to `False` passes the
    whole suite (verified by mutation).
    """
    pr_watch = _load_pr_watch()

    for impostor in ("xcoderabbit", "my-coderabbit-fan", "notcoderabbit"):
        assert (
            pr_watch.bot_review_coverage(
                [_review(impostor, "abc123", "2026-07-25T12:00:00Z")], "abc123"
            )
            == []
        ), impostor

    # The real logins still count, in both spellings GitHub uses.
    for real in ("coderabbitai", "coderabbitai[bot]"):
        covered = pr_watch.bot_review_coverage(
            [_review(real, "abc123", "2026-07-25T12:00:00Z")], "abc123"
        )
        assert covered and covered[0]["covers_head"] is True, real


def test_the_newest_review_wins_regardless_of_array_order() -> None:
    """Pinned independently of array order.

    The other fixture happens to list its reviews ascending, so "newest by
    timestamp" and "last in the array" are indistinguishable there — replacing
    the whole comparison with `if True:` passes the suite (verified by
    mutation). This one lists them descending, so only the timestamp can be
    right.
    """
    pr_watch = _load_pr_watch()
    descending = [
        _review("coderabbitai", "newest0", "2026-07-25T18:00:00Z"),
        _review("coderabbitai", "middle0", "2026-07-25T15:00:00Z"),
        _review("coderabbitai", "oldest0", "2026-07-25T12:00:00Z"),
    ]

    assert pr_watch.bot_review_coverage(descending, "zzz")[0]["sha"] == "newest0"
    # …and the same set shuffled resolves identically.
    shuffled = [descending[1], descending[2], descending[0]]
    assert pr_watch.bot_review_coverage(shuffled, "zzz")[0]["sha"] == "newest0"


def test_an_undated_review_never_displaces_a_dated_one() -> None:
    """The safety-relevant direction of the tie-break.

    An undated review that happened to sit at the head would otherwise set
    `covers_head` and suppress the warning — reporting coverage the reviewer
    never gave. Asserted in both array orders, since the comparison is
    order-sensitive by construction.
    """
    pr_watch = _load_pr_watch()
    dated = _review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")
    undated = {"author": {"login": "coderabbitai"}, "commit": {"oid": "current"}}

    for order in ([dated, undated], [undated, dated]):
        covered = pr_watch.bot_review_coverage(order, "current")
        assert covered[0]["sha"] == "0ldc0de", order
        assert covered[0]["covers_head"] is False, order


def test_a_non_string_sha_or_timestamp_cannot_break_the_poll() -> None:
    """`isinstance(commit, dict)` validates the container, not the value.

    A non-string `oid` passes that guard and then kills `render` on `sha[:7]` —
    on the ordinary poll path, in the function whose stated job is tolerating
    malformed input. A non-string timestamp raises TypeError against a sibling
    review's string.
    """
    pr_watch = _load_pr_watch()

    assert (
        pr_watch.bot_review_coverage(
            [{"author": {"login": "coderabbitai"}, "commit": {"oid": 12345}}], "abc"
        )
        == []
    )
    mixed = [
        _review("coderabbitai", "aaaaaaa", "2026-07-25T12:00:00Z"),
        {
            "author": {"login": "coderabbitai"},
            "commit": {"oid": "bbbbbbb"},
            "submittedAt": 20260725,  # not a string
        },
    ]
    assert pr_watch.bot_review_coverage(mixed, "zzz")  # does not raise

    # …and the render survives whatever survives the filter.
    report = pr_watch.build_report(
        _green_view(reviews=[{"author": {"login": "coderabbitai"}, "commit": {"oid": 1}}]),
        [],
        set(),
    )
    assert report["review_bots"]["coverage"] == []
    pr_watch.render(report)  # would raise on `sha[:7]` without the type check


# --------------------------------------------------------------------------- #
# the fallback review panel: a receipt must not claim more than it stands for
# --------------------------------------------------------------------------- #


def _record(monkeypatch, pr_watch, **kwargs) -> tuple[dict, dict]:
    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 9, "headRefOid": "abc123"}
    )
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "ok")
    )
    recorded: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: recorded.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})
    source = kwargs.pop("source", "fallback:panel")
    report = pr_watch.record_review(9, source, "abc123", now=NOW, **kwargs)
    return recorded[0]["review_receipt"], report


def test_a_single_lens_receipt_does_not_read_like_a_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`safety-critical-changes.md` rule 2: a single-lens verdict is not a green
    light.

    Without this, a degraded one-lens fallback and a full panel produce
    byte-identical receipts — so the audit trail cannot show which one a merge
    actually rested on, which is the whole reason the panel exists.
    """
    pr_watch = _load_pr_watch()

    receipt, report = _record(
        monkeypatch, pr_watch, source="fallback:codex", lenses="correctness"
    )

    assert receipt["lenses"] == ["correctness"]
    rendered = pr_watch.render_record_review(report)
    assert "one lens only (correctness)" in rendered
    assert "not a green light" in rendered


def test_a_panel_receipt_names_every_lens_that_ran(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()

    receipt, report = _record(
        monkeypatch, pr_watch, lenses="adversarial, correctness"
    )

    assert receipt["lenses"] == ["adversarial", "correctness"]
    rendered = pr_watch.render_record_review(report)
    assert "lenses: adversarial, correctness" in rendered
    assert "one lens only" not in rendered
def test_the_poll_render_surfaces_override_and_unreadable_bot_state() -> None:
    """Same argument that moved `lenses` to the poll render applies to its
    siblings: a caveat printed only at record time is not visible when a merge
    is considered. `lenses` was the only one of the family that had moved."""
    pr_watch = _load_pr_watch()

    report = pr_watch.build_report(
        _green_view(), [], set(),
        review_receipt={"head": "abc123", "source": "fallback:codex",
                        "lenses": ["correctness"], "override": "pending-bot",
                        "bot_signal": "unavailable"},
    )
    rendered = pr_watch.render(report)

    assert "recorded over an active override (pending-bot)" in rendered
    assert "review-bot state was unreadable (unavailable)" in rendered


def test_a_hand_edited_bots_behind_head_cannot_break_the_receipt_render() -> None:
    """The commit that added the `lenses` guard claimed parity with "the sibling
    receipt fields" — which were not guarded. This one raised AttributeError on
    a string or a list."""
    pr_watch = _load_pr_watch()

    for junk in ("coderabbit", ["coderabbit"], 5, None):
        pr_watch.render_record_review(
            {"pr": 9, "review_receipt": {"head": "abc", "source": "s",
                                         "bots_behind_head": junk}}
        )


def test_every_unavailability_line_points_at_the_panel_not_the_degraded_mode() -> None:
    """This PR redefines `review.fallback_commands` as the DEGRADED mode, so
    "the configured fallback" now names the wrong thing.

    The strings were changed at two of three sites and pinned by none — the
    existing assertions matched the `review unavailable` prefix, never the
    pointer, so reverting the change passed the whole suite. That is the
    "named by a test and pinned by nothing" class this PR ships doctrine about.
    """
    pr_watch = _load_pr_watch()

    outage_comment = pr_watch.build_report(
        _green_view(
            comments=[{"id": "c1", "author": {"login": "coderabbitai"},
                       "body": "Review limit reached."}]
        ),
        [], set(), now=NOW,
    )
    outage_check = pr_watch.build_report(
        _green_view(), [], set(),
        check_details=[_bot_check(description="Review rate limited")], now=NOW,
    )
    aged_out = pr_watch.build_report(
        _green_view(), [], set(),
        check_details=[
            _bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(600))
        ],
        now=NOW,
    )

    for label, report in (
        ("comment surface", outage_comment),
        ("check surface", outage_check),
        ("grace-cancelled", aged_out),
    ):
        rendered = pr_watch.render(report)
        assert "fallback review panel" in rendered, label
        assert "configured fallback review" not in rendered, label


def test_the_poll_render_reports_the_receipt_as_a_CLAIM_not_a_verdict() -> None:
    """Coverage is self-reported and the render says so.

    Whoever ran `--record-review` wrote both the source and the lens names in
    one invocation, with nothing binding either to a review that happened. Four
    rounds went into trying to verify it from here — matching the source, then
    the lens names, then a configured roster — and each was defeated: the last
    by a single extra character in the source, after which the render *affirmed*
    the forgery. Rule 1 calls that a stopgap, not a fix.

    So the render states what the receipt claims, labelled as a claim. That is
    honest and still useful: a one-lens receipt is visible at merge time.
    Verifying it needs each lens to record its own receipt (issue #32).
    """
    pr_watch = _load_pr_watch()

    def _line(receipt):
        report = pr_watch.build_report(_green_view(), [], set(), review_receipt=receipt)
        # Prefix match: the merge-blocker line legitimately contains the same
        # phrase, so a substring test picks it up when no receipt exists.
        return next(
            (ln.strip() for ln in pr_watch.render(report).splitlines()
             if ln.strip().startswith("review evidence:")),
            "",
        )

    two = _line({"head": "abc123", "source": "fallback:panel",
                 "lenses": ["adversarial", "correctness"]})
    one = _line({"head": "abc123", "source": "fallback:codex",
                 "lenses": ["correctness"]})
    none = _line({"head": "abc123", "source": "coderabbit"})

    assert "2 lenses claimed (adversarial, correctness)" in two
    assert "ONE lens claimed (correctness)" in one
    assert "no lenses recorded" in none
    # No line at all without a current-head receipt.
    assert _line({"head": "0ldc0de", "source": "fallback:panel"}) == ""


def test_the_render_cannot_be_forged_into_extra_lines_or_extra_lenses() -> None:
    """It reports a claim, but it must report it accurately.

    A newline in `source` split the line and left the first half reading as a
    completed panel; a comma inside a lens description counted as two lenses;
    duplicates counted twice.
    """
    pr_watch = _load_pr_watch()

    def _render(receipt):
        return pr_watch.render(
            pr_watch.build_report(_green_view(), [], set(), review_receipt=receipt)
        )

    forged = _render({
        "head": "abc123",
        "source": "fallback:panel — 2 lenses (adversarial, correctness)\n  (recorded)",
    })
    assert len([ln for ln in forged.splitlines()
                if ln.strip().startswith("review evidence:")]) == 1
    assert not any(ln.strip().startswith("(recorded)") for ln in forged.splitlines())

    duped = _render({"head": "abc123", "source": "fallback:codex",
                     "lenses": ["adversarial", "Adversarial"]})
    assert "ONE lens claimed" in duped


def test_a_receipt_records_lenses_without_the_engine_judging_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--record-review` no longer refuses anything on lens grounds.

    The refusal was a matcher over caller-supplied text in the same invocation
    as the claim it checked. Removing it is the honest state: the receipt is an
    audit trail, and nothing here pretends otherwise.
    """
    pr_watch = _load_pr_watch()

    for lenses in ("adversarial", "adversarial,correctness", "a,b,c", None):
        receipt, _ = _record(monkeypatch, pr_watch, lenses=lenses)
        expected = [p.strip() for p in (lenses or "").split(",") if p.strip()]
        assert receipt.get("lenses", []) == expected, lenses


def test_a_lens_described_in_prose_counts_as_one_lens() -> None:
    """`--lenses` splits on `,`, which is also ordinary punctuation.

    "adversarial, focused on the new merge gate" is an HONEST way to record one
    lens, and it arrived as two entries and rendered as a two-lens panel —
    suppressing the one-lens warning that is the whole remaining value of the
    field. Deleting the roster check (which had caught this class) reintroduced
    it. Counting only entries that look like NAMES fixes the honest case and the
    forgery together, without a roster and without a gate.
    """
    pr_watch = _load_pr_watch()

    def _line(lenses):
        report = pr_watch.build_report(
            _green_view(), [], set(),
            review_receipt={"head": "abc123", "source": "fallback:codex",
                            "lenses": lenses},
        )
        return next(ln.strip() for ln in pr_watch.render(report).splitlines()
                    if ln.strip().startswith("review evidence:"))

    assert "ONE lens claimed" in _line(["adversarial", " focused on the merge gate"])
    assert "ONE lens claimed" in _line(["correctness", " i.e. does it do what it says"])
    # Real names still count, including the shapes an adopter would use.
    assert "2 lenses claimed" in _line(["adversarial", "correctness"])
    assert "2 lenses claimed" in _line(["data-migration", "perf"])
    assert "2 lenses claimed" in _line(["lens.one", "lens_two"])
    # Prose is still RECORDED verbatim on the receipt — it just does not count
    # toward "how many lenses ran", and the render names the countable one.
    report = pr_watch.build_report(
        _green_view(), [], set(),
        review_receipt={"head": "abc123", "source": "fallback:codex",
                        "lenses": ["adversarial", " focused on the merge gate"]},
    )
    assert report["review_evidence"]["lenses"] == [
        "adversarial", " focused on the merge gate"
    ]


def test_control_characters_cannot_rewrite_the_rendered_report() -> None:
    """`_flat` collapsed whitespace, and `\\x1b` is not whitespace.

    ANSI cursor control is strictly worse than the newline `_flat` was written
    for: `\\x1b[1A\\x1b[2K` *erases* lines that already exist, so a receipt could
    delete the merge blockers printed above it. `_excerpt` renders a comment
    body — which on a public repo anyone can write — and renders last, so the
    same sequence there walks over the entire report.
    """
    pr_watch = _load_pr_watch()
    erase = "\x1b[1A\x1b[2K" * 3

    assert "\x1b" not in pr_watch._flat(f"a{erase}b")
    assert "\x1b" not in pr_watch._excerpt(f"{erase}LGTM")

    report = pr_watch.build_report(
        _green_view(
            mergeStateStatus="DIRTY",
            comments=[{"id": "c1", "author": {"login": "drive-by"},
                       "body": f"{erase}LGTM"}],
        ),
        [], set(),
        review_receipt={"head": "abc123", "source": f"fallback:{erase}panel",
                        "lenses": [f"{erase}adversarial"]},
    )
    rendered = pr_watch.render(report)

    assert "\x1b" not in rendered
    # …and the blocker it tried to erase is still there.
    assert "merge state is DIRTY" in rendered


def test_receipt_fields_are_flattened_and_type_guarded_in_both_renders() -> None:
    """Three guards whose reverts passed the whole suite.

    Each is cited by a comment or commit message as deliberate: `_flat` on lens
    names (not only on `source`), the list check on `lenses` (a bare string is
    iterable, so "adversarial" read as eleven single-character lenses), and
    `_flat` on the SHA in `bots_behind_head` (a non-string value crashed
    `sha[:7]` — the case the existing test's name promised and its body missed).
    """
    pr_watch = _load_pr_watch()

    # A newline in a LENS NAME must not forge a line.
    report = pr_watch.build_report(
        _green_view(), [], set(),
        review_receipt={"head": "abc123", "source": "fallback:codex",
                        "lenses": ["adversarial\n  review evidence: forged"]},
    )
    assert len([ln for ln in pr_watch.render(report).splitlines()
                if ln.strip().startswith("review evidence:")]) == 1

    # A bare string is iterable — it must not become one lens per character.
    stringy = pr_watch.build_report(
        _green_view(), [], set(),
        review_receipt={"head": "abc123", "source": "s", "lenses": "adversarial"},
    )
    assert stringy["review_evidence"]["lenses"] == []

    # A non-string SHA must not crash the receipt render.
    pr_watch.render_record_review(
        {"pr": 9, "review_receipt": {"head": "abc", "source": "s",
                                     "bots_behind_head": {"coderabbit": 12345}}}
    )


def test_the_cli_threads_lenses_through_to_the_receipt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The seam, not just the unit — restored after being deleted with the gate.

    This test never covered the gate; it covered the CLI wiring, and removing it
    left `--lenses` — this change's entire engine surface — unpinned end to end.
    Measured: `lenses=args.lenses` → `lenses=None` in `main()` passed all 314
    tests, and so did deleting the usage guard.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "resolve_pr", lambda explicit: 9)
    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 9, "headRefOid": "abc123"}
    )
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "ok")
    )
    saved: list[dict] = []
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: saved.append(state))
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})

    assert pr_watch.main(
        ["9", "--record-review", "fallback:panel",
         "--lenses", "adversarial,correctness", "--head", "abc123"]
    ) == 0
    assert saved[0]["review_receipt"]["lenses"] == ["adversarial", "correctness"]

    with pytest.raises(SystemExit):
        pr_watch.main(["9", "--lenses", "adversarial"])
    assert "--lenses is only valid with --record-review" in capsys.readouterr().err


def test_a_hand_edited_receipt_cannot_break_or_inflate_either_render() -> None:
    """Restored: this pinned three live type-guards, not the deleted gate.

    Each could be removed with the whole suite passing. They are load-bearing —
    without the `isinstance(..., list)` check a hand-edited `"lenses":
    "adversarial"` renders as `8 lenses claimed (a, d, v, e, r, s, a, r, i, a,
    l)`, which is the forgery the guard was added for.
    """
    pr_watch = _load_pr_watch()

    for junk in ("adversarial", 5, {"a": 1}, [None], [""], [1, 2], None):
        receipt = {"head": "abc123", "source": "fallback:panel", "lenses": junk}
        report = pr_watch.build_report(
            _green_view(), [], set(), review_receipt=receipt
        )
        assert report["review_evidence"]["lenses"] == [], junk
        assert "lenses claimed" not in pr_watch.render(report), junk
        pr_watch.render_record_review({"pr": 9, "review_receipt": receipt})

    # …and the sibling field, at the VALUE level — the case the previous test's
    # name promised and its body missed, and the one that actually crashed.
    for bad_map in ("coderabbit", ["coderabbit"], 5, None, {"coderabbit": 12345}):
        pr_watch.render_record_review(
            {"pr": 9, "review_receipt": {"head": "abc", "source": "s",
                                         "bots_behind_head": bad_map}}
        )


def test_a_stale_receipt_exposes_no_lenses_in_the_report_json() -> None:
    """Restored at REPORT level, not just render level.

    `review_evidence` is in the `--json` payload, so a consumer could read
    lenses off a receipt bound to an older head. The render-level replacement
    did not cover that.
    """
    pr_watch = _load_pr_watch()

    stale = pr_watch.build_report(
        _green_view(), [], set(),
        review_receipt={"head": "0ldc0de", "source": "fallback:panel",
                        "lenses": ["adversarial", "correctness"]},
    )

    assert stale["review_evidence"]["valid"] is False
    assert stale["review_evidence"]["lenses"] == []
    assert stale["review_evidence"]["source"] is None
    assert stale["mergeable"] is False


# ---------------------------------------------------------------------------
# transport backends (#90) — `gh` by default, REST when `gh` is absent.
#
# The point of most of these is NOT that REST returns data: it is that the two
# guards which depend on check DESCRIPTIONS (#23's outage guard) and check
# TIMESTAMPS (#19's queued-bot grace) still fire on the REST path. A port that
# moved only `_gh_json` would leave `fetch_check_details` shelling out to a `gh`
# that is not installed, degrading to no-signal on every poll — so a
# rate-limited reviewer would read as a clean one, in the engine that decides a
# PR is safe to merge.


def _no_gh(module: ModuleType, monkeypatch: pytest.MonkeyPatch, *, token: str | None = "t0ken") -> None:
    """Put the module on the REST path: no `gh` binary, a token, a known slug."""
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    if token is not None:
        monkeypatch.setenv("GH_TOKEN", token)
    monkeypatch.setattr(module, "_rest_repo_slug", lambda: ("owner", "repo"))


def _route_http(module: ModuleType, monkeypatch: pytest.MonkeyPatch, routes: dict) -> list[str]:
    """Mock the HTTP boundary, dispatching on a substring of the URL.

    Returns the list of requested URLs so a test can assert on what was asked
    for. `routes` values are the parsed JSON body; a missing route is an
    explicit failure rather than a silent empty result.
    """
    seen: list[str] = []

    def _get(url: str, token: str, **_kw):
        seen.append(url)
        for fragment, payload in routes.items():
            if fragment in url:
                return payload, None
        raise AssertionError(f"unrouted GET {url}")

    monkeypatch.setattr(module, "_http_get", _get)
    return seen


def test_backend_prefers_gh_and_is_never_memoized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selection must be per call. A cached backend would let the first test (or
    the first poll) pin it for the whole process, making which backend runs
    depend on whether the machine happens to have `gh` — the #48 failure mode,
    with ambient PATH in place of ambient config.
    """
    pr_watch = _load_pr_watch()

    monkeypatch.setattr(pr_watch.shutil, "which", lambda _name: "/usr/bin/gh")
    assert pr_watch._resolve_backend() == ("gh", None)

    # Same process, same module object: PATH changes and the answer must change.
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _name: None)
    monkeypatch.setenv("GH_TOKEN", "t0ken")
    assert pr_watch._resolve_backend() == ("rest", "t0ken")

    monkeypatch.setattr(pr_watch.shutil, "which", lambda _name: "/usr/bin/gh")
    assert pr_watch._resolve_backend() == ("gh", None)


def test_no_gh_and_no_token_is_actionable_not_a_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bug the fallback exists to fix: a missing `gh` reaching the operator
    as a raw FileNotFoundError out of subprocess.run."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch, token=None)

    with pytest.raises(RuntimeError) as excinfo:
        pr_watch.resolve_pr(None)
    message = str(excinfo.value)
    assert "not found on PATH" in message
    assert "GH_TOKEN" in message  # names the way out, not just the problem


def test_gh_present_still_takes_the_gh_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default backend is unchanged — REST must be unreachable with `gh` on PATH."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _name: "/usr/bin/gh")

    calls: list[list[str]] = []
    monkeypatch.setattr(pr_watch, "_gh_json", lambda args: (calls.append(args), {"number": 7})[1])

    def _no_http(*_a, **_k):
        raise AssertionError("REST must not be reached while `gh` is on PATH")

    monkeypatch.setattr(pr_watch, "_http_get", _no_http)

    assert pr_watch.resolve_pr(None) == 7
    assert calls == [["pr", "view", "--json", "number"]]


def test_rest_pr_view_assembles_the_same_shape_build_report_consumes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    _route_http(
        pr_watch,
        monkeypatch,
        {
            "commits/deadbee/status": {"statuses": [{"context": "legacy", "state": "success", "description": "", "created_at": "2026-07-25T11:00:00Z"}]},
            "pulls/9": {
                "number": 9,
                "title": "a title",
                "html_url": "https://github.com/owner/repo/pull/9",
                "state": "open",
                "draft": False,
                "base": {"ref": "main"},
                "mergeable_state": "clean",
                "head": {"sha": "deadbee"},
                "node_id": "PR_node",
            },
        },
    )
    # Keyed on `key`, deliberately: both check surfaces now go through this one
    # function, so a mock that ignores `key` would serve check-runs for the
    # statuses read too — hiding which surface each row actually came from.
    def _get_all_wrapped(url, token, key, **_kw):
        if key == "check_runs":
            return [
                {"name": "Test", "status": "completed", "conclusion": "success", "output": {"title": ""}, "started_at": "2026-07-25T11:00:00Z"}
            ]
        if key == "statuses":
            return [
                {"context": "legacy", "state": "success", "description": "", "created_at": "2026-07-25T11:00:00Z"}
            ]
        raise AssertionError(f"unexpected wrapped-list key {key!r}")

    monkeypatch.setattr(pr_watch, "_http_get_all_wrapped", _get_all_wrapped)

    def _get_all(url, token, **_kw):
        if "pulls/9/reviews" in url:
            return [{"user": {"login": "coderabbitai"}, "body": "looks fine", "commit_id": "deadbee"}]
        if "issues/9/comments" in url:
            return [{"id": 1, "user": {"login": "human"}, "body": "a comment"}]
        if "pulls/9/comments" in url:
            return [{"id": 2, "user": {"login": "human"}, "body": "inline", "path": "a.py", "line": 3}]
        raise AssertionError(f"unrouted GET-all {url}")

    monkeypatch.setattr(pr_watch, "_http_get_all", _get_all)

    view, inline = pr_watch.fetch_pr_view(9)

    assert view["number"] == 9
    assert view["headRefOid"] == "deadbee"
    assert view["isDraft"] is False
    assert view["baseRefName"] == "main"
    assert [c["body"] for c in view["comments"]] == ["a comment"]
    assert [r["body"] for r in view["reviews"]] == ["looks fine"]
    assert [c["body"] for c in inline] == ["inline"]
    # The rollup carries both check surfaces, in the shape summarize_checks reads.
    assert pr_watch.summarize_checks(view["statusCheckRollup"])["all_green"] is True
    # REST spells the author `user`; `_author` must still resolve it.
    assert pr_watch._author(view["comments"][0]) == "human"


def test_rest_check_rows_carry_the_fields_both_guards_read() -> None:
    """`description` and `startedAt` are the whole reason this shaping exists —
    the GraphQL rollup `gh pr view` returns has neither."""
    pr_watch = _load_pr_watch()

    rows = pr_watch._rest_check_rows(
        [
            {
                "name": "CodeRabbit",
                "status": "completed",
                "conclusion": "success",
                "output": {"title": "Review rate limited"},
                "started_at": "2026-07-25T11:50:00Z",
            }
        ],
        [
            {
                "context": "legacy/ci",
                "state": "pending",
                "description": "queued",
                "created_at": "2026-07-25T11:55:00Z",
            }
        ],
    )

    assert rows[0] == {
        "name": "CodeRabbit",
        "state": "SUCCESS",
        "bucket": "pass",
        "description": "Review rate limited",
        "startedAt": "2026-07-25T11:50:00Z",
    }
    # A StatusContext gets NO timestamp, matching what the `gh` path effectively
    # provides (gh reports the zero time, which `_age_minutes` rejects). Passing
    # REST's real `created_at` through here inverted #19's guard: a bot queued
    # longer than the grace window got zero grace instead of a full one, and it
    # could never recover, because `bot_pending_since` is persisted only when the
    # engine's own clock is used. Parity with `gh` is the contract.
    assert rows[1]["startedAt"] == ""
    assert rows[1]["bucket"] == "pending"


def test_rest_outage_guard_fires_on_a_check_description() -> None:
    """#23 end to end on REST rows: the rate limit appears ONLY as the check
    description, on an otherwise-SUCCESS check."""
    pr_watch = _load_pr_watch()

    rows = pr_watch._rest_check_rows(
        [
            {
                "name": "CodeRabbit",
                "status": "completed",
                "conclusion": "success",
                "output": {"title": "Review rate limited"},
                "started_at": "2026-07-25T11:50:00Z",
            }
        ],
        [],
    )
    result = pr_watch.summarize_review_bots(rows, [], now=NOW)

    assert [u["reason"] for u in result["unavailable"]] == ["review rate limited"]
    assert result["unavailable"][0]["surface"] == "check"


def test_rest_pending_guard_fires_and_uses_the_checks_own_clock() -> None:
    """#19 on REST rows: an in-progress run is pending, and its `started_at`
    feeds the grace window."""
    pr_watch = _load_pr_watch()

    rows = pr_watch._rest_check_rows(
        [
            {
                "name": "CodeRabbit",
                "status": "in_progress",
                "conclusion": None,
                "output": {"title": ""},
                "started_at": _minutes_ago(5),
            }
        ],
        [],
    )
    assert rows[0]["bucket"] == "pending"
    assert rows[0]["state"] == "IN_PROGRESS"

    result = pr_watch.summarize_review_bots(rows, [], now=NOW)
    assert [p["bot"] for p in result["pending"]] == ["coderabbit"]
    assert result["pending"][0]["age_source"] == "check"
    assert result["pending"][0]["age_minutes"] == 5.0
    # Inside the grace window, a pending bot blocks the MERGE gate.
    assert result["blockers"] != []


def test_rest_bucket_is_fail_closed_for_an_unrecognized_conclusion() -> None:
    """`_check_is_pending` trusts `bucket` when present, so a wrong bucket here
    is the one direction that could wave a bot through. An unknown conclusion
    must read as pending (hold the gate), never as pass.
    """
    pr_watch = _load_pr_watch()

    rows = pr_watch._rest_check_rows(
        [{"name": "CodeRabbit", "status": "completed", "conclusion": "some_new_github_state", "output": {}, "started_at": ""}],
        [{"context": "CodeRabbit", "state": "brand_new", "description": "", "created_at": ""}],
    )
    assert [r["bucket"] for r in rows] == ["pending", "pending"]
    assert all(pr_watch._check_is_pending(r) for r in rows)


def test_rest_check_pagination_is_followed_then_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Checks API defaults to per_page=30. cs-toolkit shipped a false green
    from a single unpaginated GET against 48 real check runs: the truncated
    checks read as absent rather than unread. Follow `Link`, and bound it so a
    malformed header cannot spin the loop forever.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    pages = {
        "page=1": ({"check_runs": [{"name": "one"}]}, '<https://api.github.com/x?page=2>; rel="next"'),
        "page=2": ({"check_runs": [{"name": "two"}]}, None),
    }

    def _get(url: str, token: str, **_kw):
        for fragment, payload in pages.items():
            if fragment in url:
                return payload
        return ({"check_runs": [{"name": "first"}]}, '<https://api.github.com/x?page=1>; rel="next"')

    monkeypatch.setattr(pr_watch, "_http_get", _get)
    got = pr_watch._http_get_all_wrapped("https://api.github.com/x", "t", "check_runs")
    assert [r["name"] for r in got] == ["first", "one", "two"]

    # A cyclic Link header must stop, not spin.
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ({"check_runs": [{"name": "loop"}]}, '<https://api.github.com/same>; rel="next"'),
    )
    bounded = pr_watch._http_get_all_wrapped("https://api.github.com/same", "t", "check_runs", max_pages=4)
    assert len(bounded) == 4


def test_next_link_ignores_other_rels() -> None:
    pr_watch = _load_pr_watch()
    header = '<https://api.github.com/a?page=3>; rel="prev", <https://api.github.com/a?page=5>; rel="next", <https://api.github.com/a?page=9>; rel="last"'
    assert pr_watch._next_link(header) == "https://api.github.com/a?page=5"
    assert pr_watch._next_link(None) is None
    assert pr_watch._next_link('<https://x>; rel="last"') is None


def test_fetch_check_details_on_rest_never_raises_and_says_so_once(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Same never-raises contract as the `gh` path, and the same audible
    degrade: a silent `[]` would disable both guards without a trace."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    def _boom(*_a, **_k):
        raise RuntimeError("GitHub API GET … failed (403 Forbidden)")

    monkeypatch.setattr(pr_watch, "_http_get", _boom)

    assert pr_watch.fetch_check_details(1) == ([], "unavailable")
    err = capsys.readouterr().err
    assert "403" in err
    assert "will not be detected" in err

    assert pr_watch.fetch_check_details(1) == ([], "unavailable")
    assert capsys.readouterr().err == ""  # once per process, not per poll

    # And with no backend at all it still degrades rather than raising.
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert pr_watch.fetch_check_details(1) == ([], "unavailable")


def test_fetch_check_details_on_rest_returns_rows_with_a_real_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    _route_http(
        pr_watch,
        monkeypatch,
        {
            "commits/abc123/status": {"statuses": []},
            "pulls/5": {"head": {"sha": "abc123"}},
        },
    )
    monkeypatch.setattr(
        pr_watch,
        "_http_get_all_wrapped",
        lambda url, token, key, **kw: [
            {"name": "CodeRabbit", "status": "completed", "conclusion": "success", "output": {"title": "Review limit reached"}, "started_at": "2026-07-25T11:50:00Z"}
        ],
    )

    details = pr_watch.fetch_check_details(5)
    assert details.signal == "ok"
    assert details.rows[0]["description"] == "Review limit reached"
    # per_page=100 on the checks fetch is not decoration — see the pagination test.
    assert pr_watch.summarize_review_bots(details.rows, [], now=NOW)["unavailable"] != []


# --- round 2: what CodeRabbit's review of #91 found -------------------------


def test_rest_view_raises_the_changes_requested_merge_blocker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Major finding on #91, pinned. `build_report` blocks on
    `reviewDecision == CHANGES_REQUESTED`; the first cut of the REST view hard-coded
    that field to None, so an explicit "request changes" produced NO blocker on
    REST while blocking on `gh` — a fail-open in the merge gate.

    Deliberately routed through `fetch_pr_view` rather than a hand-built view.
    An earlier version of this test called `_rest_review_decision` directly and
    assembled the view itself — so reverting the WIRING left it green, and it
    pinned nothing about the defect it is named for. Mutation testing caught
    that; the fetch is what makes it load-bearing.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: (
            {"number": 1, "state": "open", "head": {"sha": "h"}, "statuses": []},
            None,
        ),
    )
    monkeypatch.setattr(
        pr_watch,
        "_http_get_all",
        lambda url, token, **_kw: (
            [{"user": {"login": "rev"}, "state": "CHANGES_REQUESTED"}]
            if "reviews" in url
            else []
        ),
    )
    monkeypatch.setattr(
        pr_watch,
        "_http_get_all_wrapped",
        lambda url, token, key, **_kw: [
            {"name": "ci", "status": "completed", "conclusion": "success", "output": {}, "started_at": ""}
        ],
    )

    view, inline = pr_watch.fetch_pr_view(1)
    assert view["reviewDecision"] == "CHANGES_REQUESTED"

    report = pr_watch.build_report(
        view, inline, set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert "review decision is CHANGES_REQUESTED" in report["merge_blockers"]
    assert report["mergeable"] is False


def test_rest_review_decision_counts_only_each_reviewers_latest_verdict() -> None:
    """A CHANGES_REQUESTED the same reviewer later replaced with an APPROVED must
    stop blocking — otherwise the gate wedges on a resolved review. And a later
    COMMENTED carries no verdict, so it must not displace a standing one.
    """
    pr_watch = _load_pr_watch()
    decision = pr_watch._rest_review_decision

    assert decision([
        {"user": {"login": "a"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "a"}, "state": "APPROVED"},
    ]) == "APPROVED"

    # A different reviewer's block still stands.
    assert decision([
        {"user": {"login": "a"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "b"}, "state": "APPROVED"},
    ]) == "CHANGES_REQUESTED"

    # COMMENTED / PENDING carry no verdict and cannot clear one.
    assert decision([
        {"user": {"login": "a"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "a"}, "state": "COMMENTED"},
    ]) == "CHANGES_REQUESTED"

    assert decision([]) is None
    assert decision([{"user": {"login": "a"}, "state": "COMMENTED"}]) is None
    assert decision(["not a dict"]) is None


def test_rest_view_names_a_merged_pr_merged(monkeypatch: pytest.MonkeyPatch) -> None:
    """REST says `state: closed` + `merged: true` where GraphQL says MERGED. The
    blocker fires either way; this is about it naming the real reason.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: (
            {"number": 1, "state": "closed", "merged": True, "head": {"sha": "s"}, "statuses": []},
            None,
        ),
    )
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])
    monkeypatch.setattr(pr_watch, "_http_get_all_wrapped", lambda url, token, key, **_kw: [])

    view, _ = pr_watch.fetch_pr_view(1)
    assert view["state"] == "MERGED"

    report = pr_watch.build_report(
        view, [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert "PR state is MERGED" in report["merge_blockers"]


def test_pagination_ceiling_says_the_result_is_truncated(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Stopping at the ceiling returns a partial list byte-identical to a
    complete one — the same "truncated reads as absent, not unread" direction
    the bound exists to prevent. It must be audible.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ([{"id": 1}], '<https://api.github.com/next>; rel="next"'),
    )

    pr_watch._http_get_all("https://api.github.com/a", "t", max_pages=2)
    err = capsys.readouterr().err
    assert "TRUNCATED" in err
    assert "2-page ceiling" in err

    # Once per URL, not once per page.
    pr_watch._http_get_all("https://api.github.com/a", "t", max_pages=2)
    assert capsys.readouterr().err == ""

    # A read that ends because the DATA ended says nothing.
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: ([{"id": 1}], None))
    pr_watch._http_get_all("https://api.github.com/b", "t", max_pages=2)
    assert capsys.readouterr().err == ""


def test_the_token_only_ever_goes_to_the_github_api() -> None:
    """`_http_get_all` follows a `Link` URL that comes from the RESPONSE, so
    every page after the first is a server-supplied destination for a request
    carrying a bearer token.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch._check_api_url("https://api.github.com/repos/o/r/pulls/1").endswith("/pulls/1")
    for hostile in (
        "http://api.github.com/repos/o/r",           # downgraded to plaintext
        "https://evil.example.com/repos/o/r",        # another host
        "https://api.github.com.evil.example.com/x",  # suffix trick
        "file:///etc/passwd",
    ):
        with pytest.raises(RuntimeError, match="refusing to send a GitHub token"):
            pr_watch._check_api_url(hostile)


def _fake_urlopen(monkeypatch: pytest.MonkeyPatch, module: ModuleType, pages: dict) -> list[str]:
    """Mock the socket, not the transport.

    Patching `_http_get` would put the mock ABOVE `_check_api_url`, so a test
    could only ever verify its own scaffolding. Everything from the guard
    downwards has to be real code for these assertions to mean anything.

    Deliberately does NOT call `_check_api_url` itself. `_http_get` calls it
    before building the Request, so the production call site is what these tests
    exercise; a mock that re-ran the guard would be satisfied by its own
    scaffolding, which is the defect that let the host guard go untested on #91.

    Patches the engine's own opener (`pr_watch._opener`), not
    `urllib.request.urlopen`. That is per-module rather than process-global — the
    same reason `_pin_engine_backend` swaps a per-module stand-in for `shutil` —
    so it cannot leak into another test even in principle. It also keeps the real
    `_ApiOnlyRedirectHandler` out of the way; that handler has its own test.
    """
    attempted: list[str] = []

    class _Resp:
        def __init__(self, body: bytes, link: str | None) -> None:
            self._body = body
            self.headers = {"Link": link} if link else {}

        def read(self) -> bytes:
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    def _urlopen(req, timeout=None):
        url = req.full_url
        attempted.append(url)
        for fragment, (body, link) in pages.items():
            if fragment in url:
                return _Resp(json.dumps(body).encode(), link)
        return _Resp(b"[]", None)

    class _Opener:
        @staticmethod
        def open(req, timeout=None):
            return _urlopen(req, timeout=timeout)

    monkeypatch.setattr(module, "_opener", _Opener)
    return attempted


def test_the_host_guard_is_actually_wired_into_the_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `Link` header pointing off-host must abort the read, and the abort must
    come from production code.

    The first version of this test replaced `_http_get` — the function that
    CONTAINS the guard — with a mock that called `_check_api_url` itself, so
    `pytest.raises` was satisfied by the scaffolding. Deleting the guard call
    from `_http_get` left it green. Mutation testing caught that; this version
    mocks `urlopen`, below the guard, so the call site is load-bearing.
    """
    pr_watch = _load_pr_watch()
    attempted = _fake_urlopen(
        monkeypatch,
        pr_watch,
        {
            "api.github.com/first": ([{"id": 1}], '<https://evil.example.com/steal>; rel="next"'),
        },
    )

    with pytest.raises(RuntimeError, match="refusing to send a GitHub token"):
        pr_watch._http_get_all("https://api.github.com/first", "t0ken")

    # The decisive assertion: the off-host URL was never requested at all.
    assert any("api.github.com/first" in u for u in attempted)
    assert not any("evil.example.com" in u for u in attempted)


def test_the_token_header_is_attached_only_after_the_url_is_approved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ordering matters, not just the outcome: the guard must run before the
    request carrying Authorization is built."""
    pr_watch = _load_pr_watch()
    built: list[dict] = []
    real_request = pr_watch.urllib.request.Request

    def _request(url, **kw):
        built.append({"url": url, "headers": kw.get("headers") or {}})
        return real_request(url, **kw)

    monkeypatch.setattr(pr_watch.urllib.request, "Request", _request)
    _fake_urlopen(monkeypatch, pr_watch, {})

    with pytest.raises(RuntimeError, match="refusing to send a GitHub token"):
        pr_watch._http_get("https://evil.example.com/x", "t0ken")
    assert built == []  # no Request object was ever constructed for that host


def test_fetch_check_details_survives_a_non_object_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It is called OUTSIDE `main`'s try, so anything escaping crashes the poll
    instead of degrading.

    Two layers, and from HERE they are indistinguishable — both produce
    `([], "unavailable")`. An earlier version of this docstring claimed they were
    "tested separately because they fail differently", which was backwards, and
    claimed the risk was an untested except tuple, which was also backwards:
    mutation testing showed the tuple IS pinned and the `_rest_object` call site
    is the one of five that nothing kills, because the tuple absorbs exactly what
    the guard was added to prevent.

    So this test pins the OBSERVABLE contract — never raises, always degrades —
    and `test_the_guard_not_the_tuple_reports_a_malformed_body` pins which layer
    produced it, by reading the warning text only the guard can produce.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    # Layer 1 — malformed bodies.
    for body in (None, [], "a string"):
        monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, _b=body, **_kw: (_b, None))
        assert pr_watch.fetch_check_details(1) == ([], "unavailable")

    # Layer 2 — the except tuple itself.
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"head": {"sha": "s"}}, None)
    )
    for error in (AttributeError("no .get on None"), TypeError("not subscriptable")):
        def _raise(*_a, _e=error, **_k):
            raise _e

        monkeypatch.setattr(pr_watch, "_rest_fetch_checks", _raise)
        assert pr_watch.fetch_check_details(1) == ([], "unavailable")


def test_rest_resolve_pr_rejects_a_non_list_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """`data[0]` on a dict body is a TypeError, which `main`'s handler does not
    catch — so it would escape as a traceback rather than `error: …`."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_git_out", lambda args, what: "dev/x")
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"message": "Not Found"}, None)
    )

    with pytest.raises(RuntimeError, match="no open PR found"):
        pr_watch.resolve_pr(None)


def test_rest_pr_view_makes_one_git_call_for_six_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    """The slug is threaded, not re-derived per URL — and not cached at module
    scope either, which would go stale across repositories."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _n: None)
    monkeypatch.setenv("GH_TOKEN", "t0ken")

    slug_calls = []

    def _slug():
        slug_calls.append(1)
        return ("owner", "repo")

    monkeypatch.setattr(pr_watch, "_rest_repo_slug", _slug)
    built_urls: list[str] = []
    real_api = pr_watch._rest_api
    monkeypatch.setattr(
        pr_watch, "_rest_api", lambda path, slug=None: built_urls.append(real_api(path, slug)) or built_urls[-1]
    )
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ({"number": 1, "head": {"sha": "s"}, "statuses": []}, None),
    )
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])
    monkeypatch.setattr(pr_watch, "_http_get_all_wrapped", lambda url, token, key, **_kw: [])

    pr_watch.fetch_pr_view(1)
    assert len(slug_calls) == 1
    # Count the URLs too — the name says "six" and nothing checked it, so adding
    # or dropping a read was invisible.
    assert len(built_urls) == 6, built_urls

    # A second call re-derives it: no process-lifetime state to go stale.
    pr_watch.fetch_pr_view(1)
    assert len(slug_calls) == 2


# --- round 2: what the two-lens panel found ---------------------------------


def test_coverage_reads_rests_review_spellings() -> None:
    """The adversarial lens's HIGH. `bot_review_coverage` read only GraphQL's
    `commit.oid` / `submittedAt`; REST spells them `commit_id` (a bare string)
    and `submitted_at`. Every REST review was skipped, so `coverage` was always
    empty — the #22/#25 "last review was of <sha>, not the current head" warning
    could never render on this backend and `bots_behind_head` was never written
    to a receipt. Dead code, on the guard the merge gate leans on hardest.
    """
    pr_watch = _load_pr_watch()

    rest_reviews = [
        {
            "user": {"login": "coderabbitai"},
            "state": "COMMENTED",
            "commit_id": "0ldc0mm1t",
            "submitted_at": "2026-07-25T10:00:00Z",
        }
    ]
    coverage = pr_watch.bot_review_coverage(rest_reviews, "newhead")
    assert [(e["bot"], e["sha"], e["covers_head"]) for e in coverage] == [
        ("coderabbit", "0ldc0mm1t", False)
    ]

    # And it must reach the render, which is where a human sees it.
    report = pr_watch.build_report(
        _green_view(headRefOid="newhead", reviews=rest_reviews),
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert "not the current head" in pr_watch.render(report)


def test_coverage_still_prefers_the_graphql_spelling_when_both_are_present() -> None:
    """Accepting REST's names must not let them shadow gh's — a payload carrying
    both must resolve the same as it did before this transport existed."""
    pr_watch = _load_pr_watch()

    both = [
        {
            "user": {"login": "coderabbitai"},
            "commit": {"oid": "graphqlsha"},
            "commit_id": "restsha",
            "submittedAt": "2026-07-25T10:00:00Z",
            "submitted_at": "2026-07-01T10:00:00Z",
        }
    ]
    entry = pr_watch.bot_review_coverage(both, "graphqlsha")[0]
    assert entry["sha"] == "graphqlsha"
    assert entry["submitted_at"] == "2026-07-25T10:00:00Z"
    assert entry["covers_head"] is True


def test_the_status_surface_is_paginated_like_check_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both lenses found this independently. The combined-status read was a
    single unpaginated GET that discarded the `Link` header — on the
    StatusContext surface #23 is actually about, in the same function whose
    sibling read carries the docstring about a false green from exactly this.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    pages = {
        "check-runs": ({"check_runs": []}, None),
        "status?per_page=100&page=2": (
            {"statuses": [{"context": "late", "state": "pending", "description": "", "created_at": ""}]},
            None,
        ),
        "status?per_page=100": (
            {"statuses": [{"context": "early", "state": "success", "description": "", "created_at": ""}]},
            '<https://api.github.com/repos/owner/repo/commits/s/status?per_page=100&page=2>; rel="next"',
        ),
    }
    _fake_urlopen(monkeypatch, pr_watch, pages)

    _, statuses = pr_watch._rest_fetch_checks("s", token="t0ken")
    names = [s["context"] for s in statuses]
    assert names == ["early", "late"], "page 2 of the status surface was dropped"

    # And the dropped one was blocking, so truncating it is a false green.
    rows = pr_watch._rest_check_rows([], statuses)
    assert pr_watch.summarize_checks(rows)["all_green"] is False


def test_the_checks_fetch_asks_for_a_full_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """`per_page=100` was asserted by a comment and by
    `_http_get_all_wrapped`'s docstring, and checked by nothing — dropping it
    survived every test. At the API default of 30 this is the truncation the
    pagination bound exists to make survivable, on every poll.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    attempted = _fake_urlopen(
        monkeypatch, pr_watch, {"check-runs": ({"check_runs": []}, None), "status": ({"statuses": []}, None)}
    )

    pr_watch._rest_fetch_checks("sha1", token="t0ken")
    checks_urls = [u for u in attempted if "check-runs" in u or "/status" in u]
    assert checks_urls, "no check URL was requested"
    for url in checks_urls:
        assert "per_page=100" in url, f"{url} would truncate at the API default of 30"


def test_truncation_reaches_the_json_the_merge_gate_reads(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The adversarial lens: truncation warned on stderr only, so a partial read
    reached `dev_session.sh merge` as `converged: true` with no trace.
    `summarize_review_bots.signal` exists for exactly this reason — a stderr
    warning is not readable by the thing that decides a merge.

    REST list endpoints return oldest-first, so the ceiling drops the NEWEST
    comments, which is where fresh findings are.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ([{"id": 1}], '<https://api.github.com/n>; rel="next"'),
    )

    pr_watch._http_get_all("https://api.github.com/issues/9/comments", "t", max_pages=2)
    capsys.readouterr()

    report = pr_watch.build_report(
        _green_view(), [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert report["truncated_reads"] == ["https://api.github.com/issues/9/comments"]

    # Reported, never gating — an environment problem must not become a wedge.
    assert report["converged"] is True


def test_both_reads_of_one_url_in_a_poll_are_recorded(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One poll reads the check-runs URL twice — `rest_pr_view`, then
    `fetch_check_details`. The stderr line is deduped so a watch loop is not a
    wall of warnings; the recorded LIST must not be, or the second truncation
    vanishes."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ([{"id": 1}], '<https://api.github.com/n>; rel="next"'),
    )

    for _ in range(2):
        pr_watch._http_get_all("https://api.github.com/same", "t", max_pages=1)

    assert pr_watch._truncated_reads == [
        "https://api.github.com/same",
        "https://api.github.com/same",
    ]
    assert capsys.readouterr().err.count("TRUNCATED") == 1


def test_a_dismissal_clears_a_standing_block() -> None:
    """REST rewrites a dismissed review's `state` to DISMISSED, so it is that
    reviewer's latest verdict. Removing DISMISSED from the accepted set survived
    every test, and no test mentioned it — while the docstring simultaneously
    claimed REST does not expose dismissals at all.
    """
    pr_watch = _load_pr_watch()
    decision = pr_watch._rest_review_decision

    assert decision([{"user": {"login": "a"}, "state": "CHANGES_REQUESTED"}]) == "CHANGES_REQUESTED"
    assert decision([
        {"user": {"login": "a"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "a"}, "state": "DISMISSED"},
    ]) is None
    assert decision([
        {"user": {"login": "a"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "a"}, "state": "DISMISSED"},
        {"user": {"login": "b"}, "state": "APPROVED"},
    ]) == "APPROVED"


def test_review_decision_survives_a_non_dict_user() -> None:
    """`(review.get("user") or {})` passes a STRING through and then raises
    AttributeError on `.get`, which `main` does not catch — a traceback on an
    ordinary poll. `user: null` is real: GitHub returns it for deleted accounts.
    """
    pr_watch = _load_pr_watch()
    assert pr_watch._rest_review_decision([{"user": "a-string", "state": "APPROVED"}]) == "APPROVED"
    assert pr_watch._rest_review_decision([{"user": None, "state": "APPROVED"}]) == "APPROVED"


def test_every_rest_entry_point_degrades_to_an_error_not_a_traceback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`main` catches (RuntimeError, KeyError, ValueError). A `null` body reaching
    `.get` raises AttributeError and escapes as a traceback — and the invariant
    was applied to 2 of 5 entry points, so `--record-review`, `--assert-draft`
    and `--assert-ready` all still crashed.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: (None, None))
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])

    # Only the read paths that remain on REST. `fetch_review_snapshot` and the
    # draft mutation are gh-only now, so calling them here would shell out to a
    # real `gh` and hit the network.
    # `rest_pr_view` is the only REST entry point left: `fetch_review_snapshot`
    # and the draft read are gh-only now, refused by `require_gh_backend` before
    # any REST call, so there is no REST path through them to degrade.
    for label, call in (("rest_pr_view", lambda: pr_watch.fetch_pr_view(1)),):
        with pytest.raises(RuntimeError) as excinfo:
            call()
        assert "not a JSON object" in str(excinfo.value), label


def test_a_pr_with_no_head_sha_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    """Removing this raise survived, degrading to a 404 on `commits/None/...`."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: ({"number": 1}, None))
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])

    with pytest.raises(RuntimeError, match="no usable head SHA"):
        pr_watch.fetch_pr_view(1)


def test_next_link_handles_the_legal_forms_github_could_send() -> None:
    """Two RFC 8288-legal forms returned None — a silent truncation with no
    warning, because to the caller it is identical to "no next page"."""
    pr_watch = _load_pr_watch()
    nxt = pr_watch._next_link

    assert nxt('<https://a/2>; type="text/html"; rel="next"') == "https://a/2"
    assert nxt("<https://a/2>; rel=next") == "https://a/2"
    assert nxt('<https://a/2>; rel="NEXT"') == "https://a/2"
    assert nxt('<https://a/1>; rel="prev", <https://a/3>; rel="next"') == "https://a/3"
    assert nxt('<https://a/9>; rel="last"') is None


def test_a_stale_check_reads_the_same_way_in_both_lanes() -> None:
    """`_REST_BUCKETS["STALE"] = "skipping"` made the two lanes disagree about
    one row: finished to the bot lane (which trusts `bucket`) and pending to the
    blocking tally. The bot-lane side was the fail-open direction."""
    pr_watch = _load_pr_watch()

    row = pr_watch._rest_check_rows(
        [{"name": "CodeRabbit", "status": "completed", "conclusion": "stale", "output": {}, "started_at": ""}],
        [],
    )[0]
    assert pr_watch._check_is_pending(row) is True
    assert pr_watch.summarize_checks([row])["all_green"] is False


def test_a_branch_name_cannot_rewrite_the_resolve_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unencoded `&` in a branch name injected a query parameter the caller
    never asked for — `dev/x&state=closed` produced `&state=closed&state=open`."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_git_out", lambda args, what: "dev/x&state=closed")
    attempted = _fake_urlopen(monkeypatch, pr_watch, {"pulls?head=": ([{"number": 5}], None)})

    assert pr_watch.resolve_pr(None) == 5
    url = attempted[0]
    # Assert the encoding directly. The previous form was `A or B`, which passes
    # when either holds and so could not distinguish "encoded" from "the branch
    # name happened not to appear".
    assert "%26" in url, f"the branch name's & was not percent-encoded: {url}"
    assert url.count("state=") == 1, f"branch name injected a parameter: {url}"


def test_coverage_orders_rest_reviews_by_rests_timestamp() -> None:
    """The `submitted_at` fallback is only load-bearing when ONE bot has several
    reviews: with a single review the bot is added regardless of its timestamp,
    so a test with one review pins the sha spelling and nothing about the date.
    Mutation testing showed exactly that — dropping the REST spelling survived.

    Ordering is what decides which sha `coverage` reports, and therefore whether
    the "not the current head" warning fires. An undated review must never
    displace a dated one.
    """
    pr_watch = _load_pr_watch()

    reviews = [
        {
            "user": {"login": "coderabbitai"},
            "commit_id": "newer",
            "submitted_at": "2026-07-25T12:00:00Z",
        },
        {
            "user": {"login": "coderabbitai"},
            "commit_id": "older",
            "submitted_at": "2026-07-25T09:00:00Z",
        },
    ]
    entry = pr_watch.bot_review_coverage(reviews, "head")[0]
    assert entry["sha"] == "newer", "REST's submitted_at was not used to order"
    assert entry["submitted_at"] == "2026-07-25T12:00:00Z"

    # Reversed input order must give the same answer — it is the timestamp that
    # decides, not the position in the list.
    assert pr_watch.bot_review_coverage(list(reversed(reviews)), "head")[0]["sha"] == "newer"

    # An undated REST review cannot displace a dated one.
    undated = [
        {"user": {"login": "coderabbitai"}, "commit_id": "dated", "submitted_at": "2026-07-25T09:00:00Z"},
        {"user": {"login": "coderabbitai"}, "commit_id": "undated"},
    ]
    assert pr_watch.bot_review_coverage(undated, "head")[0]["sha"] == "dated"


def test_the_loader_detaches_the_engine_from_ambient_path() -> None:
    """The suite must not depend on whether this MACHINE has `gh`.

    Asserted on the pin itself rather than on its effect, deliberately: on a host
    that HAS `gh`, removing the pin changes no outcome, so a test written against
    the effect passes on the very machines where the coupling is invisible — and
    fails only in someone else's environment. That is the failure mode the
    config half of this file already exists to prevent (a legitimate ambient
    difference breaking a kit-owned test). Asserted on the pin, not on a failure
    count: the count varies by environment.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch.shutil.which("gh") == "/pinned/by/tests/gh"
    assert pr_watch._resolve_backend() == ("gh", None)
    # Non-`gh` lookups still reach the real shutil, so nothing else is masked.
    assert pr_watch.shutil.which("definitely-not-a-real-binary-xyz") is None


# --- round 2: the adversarial lens's two HIGH fail-opens --------------------


def test_a_malformed_list_body_cannot_flip_the_merge_gate_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The round-2 HIGH. `_http_get_all` skipped a non-list page silently, so a
    200 with a `null` body on `pulls/{n}/reviews` produced an empty
    `review_decision` — which removed the CHANGES_REQUESTED blocker and flipped
    `mergeable` from false to TRUE. The same fail-open `e3586b2` closed, through
    a different door: unreadable read to authorized merge.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    for body in (None, {"message": "Bad credentials"}, "a string"):
        monkeypatch.setattr(
            pr_watch, "_http_get", lambda url, token, _b=body, **_kw: (_b, None)
        )
        with pytest.raises(RuntimeError, match="expected a JSON array"):
            pr_watch._http_get_all("https://api.github.com/repos/o/r/pulls/9/reviews", "t")

    # And the wrapped variant, which feeds the check surfaces.
    for body in (None, [], "a string"):
        monkeypatch.setattr(
            pr_watch, "_http_get", lambda url, token, _b=body, **_kw: (_b, None)
        )
        with pytest.raises(RuntimeError, match="expected a JSON object"):
            pr_watch._http_get_all_wrapped(
                "https://api.github.com/repos/o/r/commits/s/check-runs", "t", "check_runs"
            )


def test_an_unreadable_review_surface_does_not_read_as_no_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End to end through the poll, which is where it mattered: the failure has to
    reach `main` as an error, not as a clean report."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: (
            ({"number": 9, "state": "open", "head": {"sha": "h"}}, None)
            if "pulls/9" in url and "reviews" not in url and "comments" not in url
            else (None, None)  # every list surface answers 200 + null
        ),
    )
    with pytest.raises(RuntimeError, match="expected a JSON"):
        pr_watch.fetch_pr_view(9)


def test_a_truncated_read_is_reported_but_does_not_gate(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Truncation is loud and recorded, and gates nothing.

    An earlier design made it a merge blocker. That is unnecessary here — REST
    cannot authorize a merge at all — and it was actively harmful: a persistent
    pagination anomaly closed the merge gate for a PR forever, with no ageing-out
    and no override, unlike every sibling environment-caused blocker.

    What remains is what a human or agent actually reads: a stderr warning and a
    `truncated_reads` field. Truncation CAN still mislead `converged` (an unread
    comment page reads as no new comments), which is why it must stay visible —
    but blocking `converged` would wedge the watch loop, which is the one thing
    the two predicates exist to keep separate.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ([{"id": 1}], '<https://api.github.com/n>; rel="next"'),
    )
    pr_watch._http_get_all("https://api.github.com/issues/9/comments", "t", max_pages=1)
    assert "TRUNCATED" in capsys.readouterr().err

    report = pr_watch.build_report(
        _green_view(), [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert report["truncated_reads"] == ["https://api.github.com/issues/9/comments"]
    assert report["converged"] is True
    assert not any("TRUNCATED" in b for b in report["merge_blockers"])


def test_the_wrapped_helper_reports_its_own_truncation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deleting the truncation call from `_http_get_all_wrapped` alone survived
    the whole suite: every truncation test drove the PLAIN helper, so the surface
    where truncation causes the documented false green was the untested one."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: (
            {"check_runs": [{"name": "c"}]},
            '<https://api.github.com/n>; rel="next"',
        ),
    )
    pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs", max_pages=1)
    assert pr_watch._truncated_reads == ["https://api.github.com/cr"]


def test_the_guard_not_the_tuple_reports_a_malformed_body(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`fetch_check_details`'s `_rest_object` call was the 1 of 5 sites no test
    killed: the widened except tuple absorbs the AttributeError the guard exists
    to prevent, so both layers look identical from the caller. Distinguished by
    the warning text, which only the guard produces.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: (None, None))

    assert pr_watch.fetch_check_details(1) == ([], "unavailable")
    assert "not a JSON object" in capsys.readouterr().err


def test_github_token_is_accepted_not_just_gh_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`GITHUB_TOKEN` is what GitHub Actions injects — the cloud-session case this
    whole backend exists for — and dropping it from `_github_token` survived every
    test, because `_no_gh` only ever sets `GH_TOKEN`."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _n: None)

    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "actions-token")
    assert pr_watch._resolve_backend() == ("rest", "actions-token")

    # GH_TOKEN wins when both are set, matching gh's own precedence.
    monkeypatch.setenv("GH_TOKEN", "explicit")
    assert pr_watch._resolve_backend() == ("rest", "explicit")


def test_the_origin_url_parse_is_covered_at_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_rest_repo_slug` was stubbed by every test, so the only thing between the
    REST backend and a 404 on every call had zero coverage — swapping owner/repo
    or dropping the `.git` strip both survived the suite.

    Calls the real function with only `git` stubbed. A first attempt at this test
    re-derived the regex in the test body instead, which would have pinned nothing
    about the engine — the same defect class this test exists to close. `ruff`'s
    unused-variable warning is what caught it.
    """
    pr_watch = _load_pr_watch()

    cases = {
        "git@github.com:topij/agentic-dev-kit.git": ("topij", "agentic-dev-kit"),
        "https://github.com/topij/agentic-dev-kit.git": ("topij", "agentic-dev-kit"),
        "https://github.com/topij/agentic-dev-kit": ("topij", "agentic-dev-kit"),
        "ssh://git@github.com:22/topij/agentic-dev-kit.git": ("topij", "agentic-dev-kit"),
        "https://x-access-token:tok@github.com/topij/agentic-dev-kit.git": ("topij", "agentic-dev-kit"),
        "https://github.com/topij/agentic-dev-kit/": ("topij", "agentic-dev-kit"),
        "git://github.com/topij/agentic-dev-kit.git": ("topij", "agentic-dev-kit"),
    }
    for url, expected in cases.items():
        monkeypatch.setattr(pr_watch, "_git_out", lambda args, what, _u=url: _u)
        # Order matters: owner first. A swap is a total failure (every call 404s).
        assert pr_watch._rest_repo_slug() == expected, url

    # An origin that is not a parseable remote must say so, not synthesize a slug.
    monkeypatch.setattr(pr_watch, "_git_out", lambda args, what: "not-a-url")
    with pytest.raises(RuntimeError, match="could not parse owner/repo"):
        pr_watch._rest_repo_slug()


def test_a_terminal_status_context_is_not_read_as_pending() -> None:
    """REST returns lowercase status states. Dropping the `.upper()` made every
    status context miss the uppercase bucket table and read as pending, while
    `summarize_checks` (which upper-cases independently) saw SUCCESS — the same
    two-lane split this round removed for STALE, in the wedge direction: a bot's
    terminal check would block the merge gate for the whole grace window.
    """
    pr_watch = _load_pr_watch()

    row = pr_watch._rest_check_rows(
        [], [{"context": "CodeRabbit", "state": "success", "description": "", "created_at": ""}]
    )[0]
    assert row["state"] == "SUCCESS"
    assert row["bucket"] == "pass"
    assert pr_watch._check_is_pending(row) is False
    assert pr_watch.summarize_review_bots([row], [], now=NOW)["pending"] == []


def test_an_approved_host_actually_receives_the_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three tests pinned that a REJECTED host gets no request; none pinned that
    an approved one gets the Authorization header. Deleting it from
    `_http_headers` survived — at runtime that is the anonymous 60/hr limit and a
    404 on any private repo."""
    pr_watch = _load_pr_watch()
    built: list[dict] = []
    real_request = pr_watch.urllib.request.Request

    def _request(url, **kw):
        built.append(kw.get("headers") or {})
        return real_request(url, **kw)

    monkeypatch.setattr(pr_watch.urllib.request, "Request", _request)
    _fake_urlopen(monkeypatch, pr_watch, {"api.github.com": ([], None)})

    pr_watch._http_get("https://api.github.com/repos/o/r/pulls/1", "s3cret")
    assert built and built[0].get("Authorization") == "Bearer s3cret"


def test_an_unusable_review_timestamp_sorts_below_a_real_one() -> None:
    """The comment above this line argues at length that `str(...)` would be
    "actively wrong" because garbage sorts ABOVE a real timestamp and so
    suppresses the coverage warning — and mutating it to exactly that survived.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch._coerce_review_timestamp({"submittedAt": "2026-07-25T10:00:00Z"}) == "2026-07-25T10:00:00Z"
    assert pr_watch._coerce_review_timestamp({"submitted_at": "2026-07-25T10:00:00Z"}) == "2026-07-25T10:00:00Z"
    # The mutation the comment warns about returns "20260725" instead of "".
    # It must be garbage in REST's `submitted_at`: garbage in `submittedAt` is
    # already wiped to None by the first isinstance, so `str(None if …)` yields
    # "" either way and the input cannot distinguish the two. A first version of
    # this test used only that input and the mutant survived.
    for garbage in (
        {"submitted_at": 20260725},
        {"submitted_at": {"x": 1}},
        {"submittedAt": 20260725},
        {},
    ):
        assert pr_watch._coerce_review_timestamp(garbage) == "", garbage

    # And end to end: a garbage-dated review must not displace the real one.
    reviews = [
        {"user": {"login": "coderabbitai"}, "commit_id": "real", "submitted_at": "2026-07-25T10:00:00Z"},
        {"user": {"login": "coderabbitai"}, "commit_id": "garbage", "submittedAt": 99999999},
    ]
    assert pr_watch.bot_review_coverage(reviews, "garbage")[0]["sha"] == "real"


def test_resolve_pr_asks_only_for_open_prs(monkeypatch: pytest.MonkeyPatch) -> None:
    """`state=all` survived: `data[0]` could then be a merged PR for the same
    branch name."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(pr_watch, "_git_out", lambda args, what: "dev/x")
    attempted = _fake_urlopen(monkeypatch, pr_watch, {"pulls?head=": ([{"number": 5}], None)})

    pr_watch.resolve_pr(None)
    assert "state=open" in attempted[0]




# --- the read-only bound: the reason this PR is shaped the way it is ---------


def test_rest_can_never_authorize_a_merge(monkeypatch: pytest.MonkeyPatch) -> None:
    """The central invariant. On REST, `mergeable` is false regardless of what the
    PR looks like — no remote response participates in the decision.

    PR #91 tried the alternative (validate every boundary) and three review rounds
    found HIGH fail-opens each time, severity increasing, because each round
    hardened one boundary and the next found the next. This asserts the property
    those rounds kept failing to reach.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    # A PR that is green, clean, reviewed and carrying a valid current-head
    # receipt — i.e. maximally mergeable by every other measure.
    view = _green_view(headRefOid="abc123")
    state = {"review_receipt": {"head": "abc123", "source": "fallback:panel", "lenses": ["adversarial", "correctness"]}}
    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt=state["review_receipt"],
        check_details=pr_watch.CheckDetails([], "skipped"),
    )

    assert report["converged"] is True, "the watch loop must still work on REST"
    assert report["mergeable"] is False
    assert report["done"] is False, "the legacy alias must not diverge from mergeable"
    assert any("cannot authorize a merge" in b for b in report["merge_blockers"])


def test_gh_is_still_allowed_to_authorize_a_merge() -> None:
    """The bound must be REST-specific — a blanket false would break the gh path
    and no test of the invariant above would notice."""
    pr_watch = _load_pr_watch()  # loader pins the backend to gh

    report = pr_watch.build_report(
        _green_view(headRefOid="abc123"),
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel", "lenses": ["adversarial", "correctness"]},
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert report["mergeable"] is True
    assert not any("cannot authorize" in b for b in report["merge_blockers"])


def test_no_backend_at_all_is_not_read_as_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`rest_cannot_authorize_merge` must not treat an unresolvable backend as
    "gh, therefore allowed" — the fail-closed direction on a guard whose whole
    job is to be unconditional."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _n: None)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    assert pr_watch.rest_cannot_authorize_merge() is not None


def test_the_write_paths_refuse_on_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    """`--record-review` writes durable evidence that flips `mergeable` on a later
    poll; the draft flags mutate the PR. Each carried its own fail-open on #91 —
    a receipt from a truncated read recorded no `bot_signal`, and `--assert-ready`
    reported success from a body with no draft bit. REST does not get them.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    with pytest.raises(RuntimeError, match="--record-review needs the `gh` backend"):
        pr_watch.record_review(1, source="fallback:panel", expected_head="abc123")

    with pytest.raises(RuntimeError, match="needs the `gh` backend"):
        pr_watch.assert_draft_state(1, want_draft=False)


def test_the_refusal_names_the_way_out() -> None:
    """A refusal an operator cannot act on is a wedge. It must say which backend
    is needed and point at the issue that tracks lifting the restriction."""
    pr_watch = _load_pr_watch()

    message = pr_watch._REST_READ_ONLY_BLOCKER
    assert "read-only" in message
    assert "#94" in message
    assert "gh" in message


def test_the_write_paths_still_work_on_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    """`require_gh_backend` must be a no-op on gh — otherwise the bound breaks the
    primary path and only the REST tests would pass."""
    pr_watch = _load_pr_watch()

    pr_watch.require_gh_backend("--record-review")  # must not raise

    monkeypatch.setattr(
        pr_watch, "_gh_json", lambda args: {"number": 1, "headRefOid": "abc123", "reviews": []}
    )
    # `record_review` also consults the bot signal, which shells out to `gh pr
    # checks`. Without this it reaches the REAL binary and the network — a test
    # whose behaviour depends on this machine's gh auth.
    #
    # Not pinned, and cannot be from here: `fetch_check_details` never raises, so
    # un-stubbing it changes no assertion on a machine where `gh` works — the same
    # "invisible exactly where it works" shape as the loader's backend pin. The
    # honest fix is a suite-wide guard that fails any test touching the network or
    # spawning a subprocess; tracked separately rather than approximated here.
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "skipped")
    )
    receipt = pr_watch.record_review(1, source="fallback:panel", expected_head="abc123")
    assert receipt["review_receipt"]["head"] == "abc123"


def test_a_non_list_value_under_the_expected_key_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CodeRabbit's Major on #96, and a genuine gap in my own fail-closed fix: the
    PAGE was validated but the value extracted from it was not.

    `data.get(key) or []` only rescues a falsy value. A string extends character
    by character, a dict extends its keys, and `_rest_check_rows` then filters the
    garbage out — so a whole check surface reads as empty and `summarize_checks`
    sees only the other one. That is the same fail-open the page check closes, one
    level down.
    """
    pr_watch = _load_pr_watch()

    for bad in ("truncated", {"a": 1}, 42):
        monkeypatch.setattr(
            pr_watch, "_http_get", lambda url, token, _b=bad, **_kw: ({"check_runs": _b}, None)
        )
        with pytest.raises(RuntimeError, match="expected a JSON array"):
            pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs")

    # A missing key is still legal — an empty rollup is a real state, not an error.
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: ({"total_count": 0}, None))
    assert pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs") == []
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"check_runs": None}, None)
    )
    assert pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs") == []


# --- panel round on #96: what the two lenses found --------------------------


def test_the_no_backend_message_does_not_promise_a_path_that_refuses() -> None:
    """The correctness lens's HIGH. The message an operator actually reads still
    said `--assert-draft`/`--assert-ready` "need it too, for the GraphQL draft
    mutation" — on a branch with no GraphQL path, where those flags refuse once a
    token IS set. Following the advice led straight to a flat refusal.

    The previous commit claimed to have fixed this and had fixed only the module
    docstring, which is the surface nobody reads.
    """
    pr_watch = _load_pr_watch()

    message = pr_watch._REST_READ_ONLY_BLOCKER
    assert "GraphQL" not in message

    import pytest as _pytest

    with _pytest.MonkeyPatch.context() as mp:
        mp.setattr(pr_watch.shutil, "which", lambda _n: None)
        mp.delenv("GH_TOKEN", raising=False)
        mp.delenv("GITHUB_TOKEN", raising=False)
        with _pytest.raises(RuntimeError) as excinfo:
            pr_watch._resolve_backend()

    advice = str(excinfo.value)
    assert "GraphQL" not in advice, "promises a path this engine does not have"
    # It must say the fallback polls only, so the operator is not sent down a
    # route that ends in `require_gh_backend`.
    assert "POLLS ONLY" in advice or "polls only" in advice
    for flag in ("--record-review", "--assert-draft", "--assert-ready"):
        assert flag in advice


def test_truncation_is_printed_where_a_human_reads_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The other HIGH: `truncated_reads` had no consumer at all, while the comment
    introducing it claimed it was "what makes the failure visible". `render` never
    printed it and `dev_session.sh merge` reads only `mergeable`.

    The precedent the comment cited — `review_bots.signal` — works precisely
    because `render` branches on it. So the render line IS the mechanism here.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: ([{"id": 1}], '<https://api.github.com/n>; rel="next"'),
    )
    pr_watch._http_get_all("https://api.github.com/issues/9/comments", "t", max_pages=1)

    report = pr_watch.build_report(
        _green_view(), [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    rendered = pr_watch.render(report)
    assert "truncat" in rendered.lower(), "a field nothing prints is read by nobody"
    assert "issues/9/comments" in rendered


def test_a_backend_switch_does_not_wedge_the_settle_guard() -> None:
    """The adversarial lens's wedge. REST paginates the Checks API fully; `gh pr
    view` requests `contexts(first: 100)` unpaginated — so on a PR with more
    contexts than that, REST reports MORE checks. Both backends share one state
    file and `max_total` is monotone per head, so a REST poll's higher count made
    every later `gh` poll report `settling: true` forever, with a new push as the
    only escape.
    """
    pr_watch = _load_pr_watch()

    rest_state = {"head": "abc123", "max_total": 5, "max_total_backend": "rest"}
    # Same backend: the baseline is real and must still be honoured.
    assert pr_watch.comparable_max_total(rest_state, "rest") == 5
    # Different backend: not comparable, so a fresh baseline rather than a wedge.
    assert pr_watch.comparable_max_total(rest_state, "gh") == 0
    # A state file predating the key reads as not comparable, which costs one
    # settling round rather than risking the wedge.
    assert pr_watch.comparable_max_total({"head": "abc123", "max_total": 5}, "gh") == 0

    # End to end: the gh poll that used to be stranded now settles.
    view = _green_view(headRefOid="abc123")
    stranded = pr_watch.build_report(
        view, [], set(), prior_head="abc123", prior_max_total=5,
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert stranded["settling"] is True, "precondition: a higher baseline strands it"

    healthy = pr_watch.build_report(
        view, [], set(), prior_head="abc123",
        prior_max_total=pr_watch.comparable_max_total(rest_state, "gh"),
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert healthy["settling"] is False
    assert healthy["converged"] is True


def test_the_report_names_which_backend_produced_it() -> None:
    """`persist_poll` needs it to scope the settle baseline, so it has to be in
    the report rather than recomputed at persist time."""
    pr_watch = _load_pr_watch()  # loader pins gh

    report = pr_watch.build_report(
        _green_view(), [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert report["backend"] == "gh"
    state = pr_watch.persist_poll(4242, report, set())
    assert state["max_total_backend"] == "gh"


def test_a_redirect_cannot_carry_the_token_off_host() -> None:
    """urllib follows 3xx internally and carries `headers=` across it, so
    validating the URL the engine CHOSE proves nothing about where the token
    lands. Verified against the stdlib: only content-length/content-type are
    stripped on redirect, so Authorization survives.

    Before this transport existed no GitHub token left the process at all — `gh`
    owned its auth — so this exposure is the transport's to close.
    """
    pr_watch = _load_pr_watch()
    handler = pr_watch._ApiOnlyRedirectHandler()

    with pytest.raises(RuntimeError, match="refusing to send a GitHub token"):
        handler.redirect_request(
            urllib.request.Request("https://api.github.com/repos/o/r/pulls/1"),
            None, 302, "Found", {}, "https://evil.example.com/steal",
        )

    # The opener the engine actually uses must have the handler installed.
    assert any(
        isinstance(h, pr_watch._ApiOnlyRedirectHandler) for h in pr_watch._opener.handlers
    ), "the checked handler is not wired into the opener `_http_get` uses"


def test_a_non_default_port_is_not_the_github_api() -> None:
    """A server-supplied `Link` naming api.github.com:8443 is not the API."""
    pr_watch = _load_pr_watch()

    assert pr_watch._check_api_url("https://api.github.com/x")
    assert pr_watch._check_api_url("https://api.github.com:443/x")
    with pytest.raises(RuntimeError, match="refusing to send a GitHub token"):
        pr_watch._check_api_url("https://api.github.com:8443/x")


def test_the_page_ceiling_itself_is_pinned() -> None:
    """The last remaining wedge bound, and nothing asserted it: every pagination
    test passes `max_pages=` explicitly, so raising the module constant left the
    suite green. Measured consequence of doing so on a cyclic `Link`: >500,000
    requests and still climbing.
    """
    pr_watch = _load_pr_watch()

    assert pr_watch._REST_MAX_PAGES == 20, (
        "the default page ceiling is the only bound on a cyclic Link header; "
        "changing it is a deliberate act that should fail this test"
    )


def test_malformed_list_elements_do_not_crash_the_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_http_get_all` proves the RESPONSE is a list; a hostile element inside it
    still reached `.get`. `build_report` runs outside `main`'s try, so that exits
    1 with a traceback rather than `error: …` — on the path that runs every round.
    """
    pr_watch = _load_pr_watch()

    view = {
        "number": 9,
        "state": "OPEN",
        "headRefOid": "h",
        "statusCheckRollup": [],
        "reviews": ["hostile-string", {"user": {"login": "x"}, "body": "real"}],
        "comments": [None, 42, {"id": 1, "user": {"login": "y"}, "body": "also real"}],
    }
    comments = pr_watch.collect_comments(view, ["a-string", {"id": 2, "body": "inline"}])
    bodies = sorted(c["body"] for c in comments)
    assert bodies == ["also real", "inline", "real"], bodies

    # And a non-dict `output` on a check run must not crash the row shaping.
    rows = pr_watch._rest_check_rows(
        [{"name": "c", "status": "completed", "conclusion": "success", "output": "rate limited"}], []
    )
    assert rows[0]["description"] == ""


def test_a_non_dict_head_is_rejected_not_dereferenced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`(pr_data.get("head") or {}).get("sha")` passes a STRING through the
    truthiness test and then raises AttributeError out of `rest_pr_view`."""
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"number": 9, "head": "deadbee"}, None)
    )
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])

    with pytest.raises(RuntimeError, match="no usable head SHA"):
        pr_watch.fetch_pr_view(9)


def test_the_rest_field_mappings_that_feed_merge_blockers_are_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`isDraft`, `mergeStateStatus` and `baseRefName` each feed a merge blocker or
    a `dev_session.sh` cross-check, and all three were unpinned — inert only
    because the REST bound makes `mergeable` false regardless. Issue #94's plan to
    lift that bound would make three untested mappings load-bearing at once.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    monkeypatch.setattr(
        pr_watch,
        "_http_get",
        lambda url, token, **_kw: (
            {
                "number": 9,
                "state": "open",
                "draft": True,
                "base": {"ref": "release"},
                "mergeable_state": "blocked",
                "head": {"sha": "h"},
            },
            None,
        ),
    )
    monkeypatch.setattr(pr_watch, "_http_get_all", lambda url, token, **_kw: [])
    monkeypatch.setattr(pr_watch, "_http_get_all_wrapped", lambda url, token, key, **_kw: [])

    view, _ = pr_watch.fetch_pr_view(9)
    assert view["isDraft"] is True
    assert view["mergeStateStatus"] == "BLOCKED"
    assert view["baseRefName"] == "release"

    report = pr_watch.build_report(
        view, [], set(), check_details=pr_watch.CheckDetails([], "skipped")
    )
    assert any("draft" in b.lower() for b in report["merge_blockers"])
    assert any("BLOCKED" in b for b in report["merge_blockers"])
    assert report["base"] == "release"
