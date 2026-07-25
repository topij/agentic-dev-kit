from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


ENGINE_DIR = Path(__file__).resolve().parent.parent


def _load_pr_watch() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pr_watch_under_test", ENGINE_DIR / "pr_watch.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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
    """The alias must never drift from the field it aliases."""
    pr_watch = _load_pr_watch()
    receipt = {"head": "abc123", "source": "fallback:codex"}

    for report in (
        pr_watch.build_report(_green_view(), [], set()),
        pr_watch.build_report(_green_view(), [], set(), review_receipt=receipt),
        pr_watch.build_report(_green_view(isDraft=True), [], set()),
        pr_watch.build_report(_green_view(state="MERGED"), [], set()),
    ):
        assert report["done"] is report["mergeable"]


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


def test_require_ci_defaults_to_the_configured_value() -> None:
    pr_watch = _load_pr_watch()

    assert pr_watch._REQUIRE_CI is True  # this repo's config
    assert pr_watch.summarize_checks([])["all_green"] is False


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
# review-bot knowledge comes from config, not from engine literals
# --------------------------------------------------------------------------- #


ADOPTER_CONFIG = """review:
  noise_markers:
    - "<!-- Generated by OtherBot -->"
    - "NOTHING TO REPORT"
  unavailable_markers:
    - "OtherBot Is Out Of Credits"
  informational_checks: [OtherBot, " Advisory "]
  require_ci: false
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

    noise, unavailable, informational, require_ci = pr_watch._load_review_config(
        _write_config(tmp_path, ADOPTER_CONFIG)
    )

    # Lower-cased/stripped at load so every call site can keep matching
    # case-insensitively against a folded body / check name.
    assert noise == ("<!-- generated by otherbot -->", "nothing to report")
    assert unavailable == ("otherbot is out of credits",)
    assert informational == frozenset({"otherbot", "advisory"})
    assert require_ci is False
    # None of the kit's own default markers leak in — config replaces, not extends.
    assert "<!-- walkthrough_start -->" not in noise


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

    assert resolved[3] is True  # NOT the config's require_ci: false
    assert resolved[0] == pr_watch._DEFAULT_NOISE_MARKERS
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

    assert empty[0] == ()
    assert absent[0] == pr_watch._DEFAULT_NOISE_MARKERS


def test_non_boolean_require_ci_keeps_the_safe_default(tmp_path: Path) -> None:
    """Only a real boolean flips the CI requirement — a stray `yes` must not
    silently let a zero-check PR read as green."""
    pr_watch = _load_pr_watch()

    for value in ("yes", "0", '"false"'):
        _, _, _, require_ci = pr_watch._load_review_config(
            _write_config(tmp_path, f"review:\n  require_ci: {value}\n")
        )
        assert require_ci is True, value


def test_configured_unavailable_marker_still_beats_configured_noise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The "a down reviewer is never auto-noise" invariant is a property of the
    engine, not of which list a marker happens to sit on in config."""
    pr_watch = _load_pr_watch()
    noise, unavailable, _, _ = pr_watch._load_review_config(
        _write_config(
            tmp_path,
            'review:\n  noise_markers: ["OtherBot Is Out Of Credits"]\n'
            '  unavailable_markers: ["OtherBot Is Out Of Credits"]\n',
        )
    )
    monkeypatch.setattr(pr_watch, "_NOISE_MARKERS", noise)
    monkeypatch.setattr(pr_watch, "_REVIEW_UNAVAILABLE_MARKERS", unavailable)

    body = "OtherBot is out of credits for this repo."

    assert pr_watch.review_unavailable_reason(body) == "otherbot is out of credits"
    assert pr_watch.is_noise(body) is False


def test_shipped_config_preserves_the_engine_defaults_behavior() -> None:
    """This repo's own config/dev-model.yaml must classify exactly as the
    literals it replaced — the behavior-preservation argument for BUG 3."""
    pr_watch = _load_pr_watch()

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
    assert pr_watch._INFORMATIONAL_CHECK_NAMES == frozenset({"coderabbit"})
    assert pr_watch._REQUIRE_CI is True


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
