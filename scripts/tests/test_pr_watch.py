from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import find_repo_root  # noqa: E402

ENGINE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = find_repo_root(ENGINE_DIR)


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
    module._COMMENT_VERDICT_MARKERS = defaults.comment_verdict_markers
    module._INFORMATIONAL_CHECK_NAMES = defaults.informational_checks
    module._REQUIRE_CI = defaults.require_ci
    module._REVIEW_BOTS = defaults.bots
    module._REVIEW_BOT_AUTHOR_ALIASES = defaults.bot_author_aliases
    module._REVIEW_BOT_APP_SLUGS = defaults.bot_app_slugs
    module._BOT_PENDING_GRACE_MINUTES = defaults.bot_pending_grace_minutes
    module._SETTLE_GRACE_MINUTES = defaults.settle_grace_minutes


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


def _ago_iso(minutes: float) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes)
    ).isoformat().replace("+00:00", "Z")


def _settled(view: dict, minutes: float = 30.0, *, now: datetime | None = None) -> dict:
    """The prior-state kwargs a real SECOND poll carries for ``view``.

    `build_report` defaults `prior_settle_since` to None — "no baseline for this
    head" — and the merge gate reads that as NOT settled. That default is
    deliberate and must stay: reading an absent baseline as a satisfied one is
    the fail-open #190 and #39 are about, and is exactly how
    `comparable_max_total` failed.

    So a test that wants a *mergeable* report has to say the rollup was already
    this size on the previous poll,
    which takes all three of these together. The stamp alone is not enough: a
    `prior_max_total` left at its 0 default reads as "the rollup just grew from
    nothing", which restarts the clock — correctly, since that IS a first poll.
    Tests exercising the guard itself build their own state instead of calling
    this.

    ``now`` must be passed by any test that pins `build_report`'s clock, and the
    failure if it is not is silent in the dangerous direction: a real-time stamp
    against the suite's fixed ``NOW`` lands weeks in the FUTURE, which
    `_age_minutes` reports as unusable, which reads as not-settled. That fails
    closed here — but it would make such a test pass for a reason it does not
    state.
    """
    reference = now or datetime.now(timezone.utc)
    return {
        "prior_head": view.get("headRefOid"),
        "prior_max_total": len(view.get("statusCheckRollup") or []),
        "prior_settle_since": (
            (reference - timedelta(minutes=minutes))
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "prior_settle_total": len(view.get("statusCheckRollup") or []),
    }


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


def test_workflow_routes_check_only_review_outages_to_the_fallback_panel() -> None:
    workflow = (
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows" / "pr-watch.md"
    ).read_text(encoding="utf-8")

    start = workflow.index("If `review_bots.unavailable` contains an entry")
    end = workflow.index("\n1. **If `converged`", start)
    fallback_rule = " ".join(workflow[start:end].split())
    condition = fallback_rule.split(":**", 1)[0]

    assert "`surface` is `check`" in condition
    assert "`review_bots.blockers` is empty" in condition
    assert "current head has no valid `review_evidence`" in condition
    assert "`new_comments[]` contains no outage notice" in fallback_rule
    assert "run `review.fallback_panel`" in fallback_rule
    assert "report's exact `head`" in fallback_rule
    assert "historical comment-only" in fallback_rule
    assert "must not preempt a live pending" in fallback_rule
    assert "another configured reviewer is still pending" in fallback_rule
    assert "`--record-review` would refuse" in fallback_rule
    assert "do not rerun the panel" in fallback_rule
    # #518 — the branch's receipt is a substitute review and not a request, said
    # inside the branch itself. Stated here because this is where an agent is
    # standing when it decides the review question is settled.
    assert "substitute review, not a request" in fallback_rule
    assert "never the reason to skip the request" in fallback_rule

    comment_start = workflow.index("- **Reviewer unavailable**")
    comment_end = workflow.index("- **Real finding**", comment_start)
    comment_rule = " ".join(workflow[comment_start:comment_end].split())
    comment_condition = comment_rule.split(":", 1)[0]
    assert "current-head `review_evidence` is invalid" in comment_condition
    assert "`review_bots.blockers` is empty" in comment_condition
    assert "do not rerun the panel" in comment_rule
    assert "another reviewer is pending" in comment_rule
    assert "blocker must clear before the panel runs" in comment_rule


def test_the_converged_step_settles_the_review_request_before_reading_mergeable() -> None:
    """#518 — the exit ramp `#516` took out of the loop, closed in the prose.

    The two review-bot-facing steps read as sequential and are independent. The
    panel branch can fire on the first poll and make `mergeable` true before the
    loop converges; the converged step then said "if `mergeable` is already true,
    say so", which is a finish line. The Converged stop condition's request bullet
    is unconditional on coverage, but nothing sent you back to it — so on `#516`
    it was never revisited and the configured reviewer never saw the diff.

    Pinned as prose because the fix is prose: the engine's `⚠ review owed` line
    reports the state, and this step is what acts on it.
    """
    workflow = (
        REPO_ROOT / "docs" / "agentic-dev-kit" / "workflows" / "pr-watch.md"
    ).read_text(encoding="utf-8")

    start = workflow.index("1. **If `converged`:**")
    end = workflow.index("\n1. **If checks are still", start)
    rule = " ".join(workflow[start:end].split())

    # The request is settled BEFORE the receipt, not after it.
    assert "before anything else, settle the review request" in rule
    assert rule.index("settle the review request") < rule.index(
        "record the independent review"
    )
    # Key off the PRINTED line, not a hand-rebuilt coverage check: the engine
    # weighs three more things, so a condition re-derived from coverage alone
    # asks for reviews it already knows are unnecessary.
    assert "⚠ review owed" in rule
    assert "rather than re-deriving it from" in rule
    # And the specific misreading that produced #516.
    assert "does not discharge that request" in rule
    assert "do not read it as the end of this step" in rule

    # The Converged stop condition's own paragraph describes the same line, and
    # was pinned by nothing — so a future edit could drift it away from the
    # engine silently. Its four terms are the engine's four.
    stop = workflow[workflow.index("Nothing in `pr_watch.py` performs the request") :]
    stop = " ".join(stop[: stop.index("And note")].split())
    assert "name who owes it" in stop
    assert "no review covering the head" in stop
    assert "no comment-borne verdict" in stop
    assert "no review in flight" in stop
    assert "only when the reviewer read succeeded" in stop
    assert "gates nothing" in stop




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

    view = _green_view()
    converged = pr_watch.render(pr_watch.build_report(view, [], set()))
    authorized = pr_watch.render(
        pr_watch.build_report(
            view,
            [],
            set(),
            review_receipt=receipt,
            **_settled(view),
        )
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

    informational_view = _green_view(
        mergeStateStatus="UNSTABLE",
        statusCheckRollup=[
            {"name": "tests", "conclusion": "SUCCESS"},
            coderabbit_pending,
        ],
    )
    unstable_view = _green_view(mergeStateStatus="UNSTABLE")
    successful_view = _green_view(
        mergeStateStatus="UNSTABLE",
        statusCheckRollup=[
            {"name": "tests", "conclusion": "SUCCESS"},
            {"context": "CodeRabbit", "state": "SUCCESS"},
        ],
    )

    informational_only = pr_watch.build_report(
        informational_view,
        [],
        set(),
        review_receipt=receipt,
        **_settled(informational_view),
    )
    unexplained_unstable = pr_watch.build_report(
        unstable_view,
        [],
        set(),
        review_receipt=receipt,
        **_settled(unstable_view),
    )
    successful_informational = pr_watch.build_report(
        successful_view,
        [],
        set(),
        review_receipt=receipt,
        **_settled(successful_view),
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
        comments=[{"id": "notice-1", "author": {"login": "coderabbitai"}, "body": body}],
        reviews=[
            {"id": "notice-2", "author": {"login": "coderabbitai[bot]"}, "body": body}
        ],
    )
    inline = [
        {"id": "notice-3", "author": {"login": "coderabbitai[bot]"}, "body": body}
    ]

    report = pr_watch.build_report(
        view,
        inline,
        set(),
        review_receipt={"head": "abc123", "source": "coderabbit"},
    )

    assert report["done"] is False
    assert len(report["new_comments"]) == 3
    assert {
        comment["kind"]: comment["review_unavailable_reason"]
        for comment in report["new_comments"]
    } == {
        "issue": "review limit reached",
        "review": "review limit reached",
        "inline": "review limit reached",
    }


def test_non_reviewer_quoting_an_outage_message_remains_noise() -> None:
    """Tracker mirrors can quote the ticket's outage evidence verbatim.

    The marker only proves unavailability when a configured reviewer says it;
    otherwise a known-noise mirror becomes a false fallback-review signal.
    """
    pr_watch = _load_pr_watch()
    body = """<!-- linear-linkback -->
The incident report says: Review limit reached. We couldn't start this review.
"""
    view = _green_view(
        comments=[{"id": "mirror-1", "author": {"login": "linear-code"}, "body": body}],
        reviews=[
            {"id": "mirror-2", "author": {"login": "review-reporter"}, "body": body}
        ],
    )
    inline = [
        {"id": "mirror-3", "author": {"login": "review-reporter"}, "body": body}
    ]

    report = pr_watch.build_report(
        view,
        inline,
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )

    assert report["new_comments"] == []
    assert report["review_bots"]["unavailable"] == []
    assert report["mergeable"] is True


def test_custom_reviewer_aliases_cover_every_comment_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REVIEW_BOTS", ("otherbot",))
    monkeypatch.setattr(
        pr_watch,
        "_REVIEW_BOT_AUTHOR_ALIASES",
        {"otherbot": frozenset({"otherbotai[bot]"})},
    )
    monkeypatch.setattr(pr_watch, "_REVIEW_UNAVAILABLE_MARKERS", ("review offline",))
    monkeypatch.setattr(pr_watch, "_NOISE_MARKERS", ("generated summary",))
    body = "generated summary — review offline"
    raw = {"author": {"login": "OtherBotAI[bot]"}, "body": body}
    view = _green_view(
        comments=[{"id": "custom-1", **raw}],
        reviews=[{"id": "custom-2", **raw}],
    )
    inline = [{"id": "custom-3", **raw}]

    report = pr_watch.build_report(view, inline, set())

    assert {comment["kind"] for comment in report["new_comments"]} == {
        "issue",
        "review",
        "inline",
    }
    assert all(
        comment["review_unavailable_reason"] == "review offline"
        for comment in report["new_comments"]
    )
    assert {entry["bot"] for entry in report["review_bots"]["unavailable"]} == {
        "otherbot"
    }


def test_legacy_prefix_outage_is_visible_but_not_authenticated() -> None:
    pr_watch = _load_pr_watch()
    body = "<!-- walkthrough_start --> Review skipped — Draft detected."
    raw = {"author": {"login": "coderabbit-impersonator"}, "body": body}
    view = _green_view(
        comments=[{"id": "candidate-1", **raw}],
        reviews=[{"id": "candidate-2", **raw}],
    )
    inline = [{"id": "candidate-3", **raw}]

    report = pr_watch.build_report(view, inline, set())

    assert report["review_bots"]["unavailable"] == []
    assert {comment["kind"] for comment in report["new_comments"]} == {
        "issue",
        "review",
        "inline",
    }
    assert all(
        comment["review_unavailable_reason"] is None
        and comment["untrusted_review_unavailable_candidate"] == "review skipped"
        for comment in report["new_comments"]
    )
    assert "untrusted reviewer-outage candidate" in pr_watch.render(report)
    assert "review.bot_author_aliases" in pr_watch.render(report)

    seen = {
        key
        for comment in pr_watch.collect_comments(view, inline)
        for key in (comment["key"], comment["content_key"])
    }
    acknowledged = pr_watch.build_report(
        view,
        inline,
        seen,
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )
    assert acknowledged["new_comments"] == []
    assert acknowledged["mergeable"] is True


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
        **_settled(view),
    )

    # All three are green and comment-clean, so the watch loop has converged for
    # each; only the receipt bound to the CURRENT head authorizes the merge.
    for report in (missing, stale, current):
        assert report["converged"] is True

    assert missing["mergeable"] is False
    assert stale["mergeable"] is False
    assert current["mergeable"] is True
    # Exact-equality on purpose: this is the payload `dev_session.sh merge` and
    # any other consumer reads, so a key appearing or vanishing should break a
    # test rather than surprise an adopter. `route`/`bots` arrived with #350.
    assert current["review_evidence"] == {
        "lenses": [],
        "override": None,
        "bot_signal": None,
        "valid": True,
        "route": "receipt",
        "bots": [],
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


def test_state_dir_is_the_pr_watch_subdir_of_the_resolved_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the wiring: whatever the root resolves to, state lands in pr-watch/.

    #428's suite-wide `_hermetic_state_root` autouse fixture (in this
    directory's ``conftest.py``) sets ``$DEVKIT_STATE_ROOT`` before every
    test body runs, including this one — so without the ``delenv`` below,
    ``pr_watch._STATE_ROOT`` would resolve to that fixture's tmp sandbox
    rather than this repo's real default, and the two assertions that used
    to close this test (``STATE_DIR == _STATE_ROOT / "pr-watch"`` and
    ``is_absolute()``) would keep passing for a reason no longer stated:
    they would hold no matter what `_resolve_state_root` computed, since a
    pytest tmp dir is absolute by construction. That is not this test lying,
    but it is testing less than its name claims.

    ``delenv`` restores this ONE test to what it always was: the module
    computing its OWN real derivation, with no override in effect — so the
    root assertion below is a genuine pin of the production rule, not a
    tautology reachable no matter what the wiring does. Still never touches
    disk: only `Path` objects are inspected here, `STATE_DIR.mkdir()` is
    never called.

    That rule is TWO-armed, and asserting only the second arm
    (``REPO_ROOT / "state"``) would pass here and fail in a headless lane.
    With the env var gone, `_resolve_state_root` consults the
    ``.devkit_state_root`` marker BEFORE falling back to the repo default —
    and `dev_session.sh new --headless` writes exactly that marker into
    every lane worktree, so a lane running `make test` resolves to its own
    sandbox and is right to. Pinning one arm would have put this test in the
    same class as the `state_paths` tests that `upgrade.md`'s "Known gotcha"
    (kit issue #10) already tells you to run from the main checkout. So the
    expectation is derived the way production derives it, and holds in both
    a plain checkout and a lane.
    """
    monkeypatch.delenv("DEVKIT_STATE_ROOT", raising=False)
    pr_watch = _load_pr_watch()

    engine_dir = Path(pr_watch.__file__).resolve().parent
    marker = pr_watch._marker_state_root(engine_dir)
    expected_root = marker if marker is not None else pr_watch.REPO_ROOT / "state"

    assert expected_root == pr_watch._STATE_ROOT
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
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:codex"},
        **_settled(view),
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
    """One `gh pr checks --json` row for the configured review bot.

    ``identity`` defaults to the REAL reviewer's creator identity, so a test
    whose subject is outage *semantics* keeps testing that and not #95's trust
    boundary. It is the identity GitHub actually reports for this repo's
    CodeRabbit status contexts (`creator.login: coderabbitai[bot]`).

    A test whose subject IS the trust boundary must set ``identity`` explicitly —
    to a forged value, or to ``""`` for the unresolvable case. Both directions are
    pinned in ``test_a_forged_check_cannot_cancel_a_pending_reviewer`` and
    ``test_an_unresolvable_identity_cannot_cancel_but_costs_only_the_grace``; if
    this default ever silently became the *only* thing keeping the outage path
    alive, those two would fail.
    """
    detail = {
        "name": "CodeRabbit",
        "state": "SUCCESS",
        "bucket": "pass",
        "description": "",
        "startedAt": "2026-07-25T11:50:00Z",
        "identity": "coderabbitai[bot]",
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


def test_a_forged_check_cannot_cancel_a_pending_reviewer() -> None:
    """#95: the demonstration from the issue, as a regression.

    A same-repo PR's own workflow holds `checks: write`, so the PR under review
    can create a check named anything with any description. Named
    `coderabbit-shim` and described `Review rate limited`, it used to be read as
    the configured reviewer announcing an outage — which cancelled the REAL
    reviewer's pending block and opened the merge gate mid-review.

    The forged row is still REPORTED (an operator wants to see it) but may not
    cancel, because its creator is `github-actions`: a workflow's GITHUB_TOKEN
    cannot authenticate as the reviewer's app.
    """
    pr_watch = _load_pr_watch()
    real_pending = _bot_check(
        name="CodeRabbit", state="PENDING", bucket="pending", startedAt=_minutes_ago(1)
    )
    forged = _bot_check(
        name="coderabbit-shim",
        description="Review rate limited",
        # What GitHub records for any check a workflow creates — verified on this
        # repo, whose Actions check carries `app.slug: github-actions`.
        identity="github-actions",
    )

    forged_poll = pr_watch.summarize_review_bots([real_pending, forged], [], now=NOW)

    assert forged_poll["blockers"] != [], "a forged check reopened #95"
    assert forged_poll["pending"][0]["cancelled_by"] is None
    reported = [e for e in forged_poll["unavailable"] if e["surface"] == "check"]
    assert reported[0]["where"] == "coderabbit-shim"
    assert reported[0]["trusted"] is False
    assert reported[0]["identity"] == "github-actions"

    # THE POSITIVE CONTROL. Identical fixture, real creator identity — the cancel
    # still works, so the assertions above are evidence about the trust boundary
    # and not about a fixture that could never cancel anything. Deleting the
    # identity gate makes this pass and the block above fail; breaking the outage
    # path entirely makes this fail.
    genuine_poll = pr_watch.summarize_review_bots(
        [real_pending, _bot_check(name="CodeRabbit / stale", description="Review rate limited")],
        [],
        now=NOW,
    )
    assert genuine_poll["blockers"] == []
    assert genuine_poll["pending"][0]["cancelled_by"] == "outage"
    assert [e for e in genuine_poll["unavailable"] if e["surface"] == "check"][0][
        "trusted"
    ] is True


def test_an_unresolvable_identity_cannot_cancel_but_costs_only_the_grace() -> None:
    """An empty identity is untrusted, and the cost of that is BOUNDED (#95).

    This is the case that decides whether requiring identity is safe as a
    default: an old `gh` without `--slurp`, a missing token, a rate-limited API
    call. All of them resolve no identity, and the answer must not be a wedge.

    Two shapes, both bounded — which is the argument for shipping the gate on by
    default rather than behind an opt-in:

    - a TERMINAL outage row (#23's own case, an outage on an otherwise SUCCESS
      context) creates no pending entry at all, so an unresolved identity costs
      exactly nothing.
    - a NON-TERMINAL one blocks, then ages out at the grace bound like any other
      pending check. It cannot block forever.
    """
    pr_watch = _load_pr_watch()

    # #23's shape: the outage is the bot's ONLY row, and it is terminal.
    terminal = pr_watch.summarize_review_bots(
        [_bot_check(description="Review rate limited", identity="")], [], now=NOW
    )
    assert terminal["blockers"] == []
    assert terminal["pending"] == []
    assert terminal["unavailable"][0]["trusted"] is False

    # A pending row with no resolvable identity blocks while young…
    young = pr_watch.summarize_review_bots(
        [
            _bot_check(
                state="PENDING",
                bucket="pending",
                description="Review rate limited",
                startedAt=_minutes_ago(1),
                identity="",
            )
        ],
        [],
        now=NOW,
    )
    assert young["blockers"] != []

    # …and ages out on its own once past the grace bound, so the worst an
    # unresolvable identity can do is delay a merge by the grace window.
    aged = pr_watch.summarize_review_bots(
        [
            _bot_check(
                state="PENDING",
                bucket="pending",
                description="Review rate limited",
                startedAt=_minutes_ago(1),
                identity="",
            )
        ],
        [],
        now=NOW,
        grace_minutes=15.0,
        pending_since={"coderabbit": _minutes_ago(45)},
    )
    assert aged["blockers"] == []
    assert aged["pending"][0]["cancelled_by"] == "grace"


def test_a_trusted_identity_is_matched_exactly_never_by_prefix() -> None:
    """The #95 fix must not re-import the defect one namespace over.

    A substring/prefix rule on the identity would let `coderabbitai-evil` speak
    for CodeRabbit, which is precisely what an unanchored check-NAME match let
    `coderabbit-shim` do.
    """
    pr_watch = _load_pr_watch()
    bots = ("coderabbit",)

    # Both namespaces the real reviewer can appear under: an app slug on a check
    # run, a `[bot]` login on a status context.
    assert pr_watch._match_bot_identity("coderabbitai", bots) == "coderabbit"
    assert pr_watch._match_bot_identity("coderabbitai[bot]", bots) == "coderabbit"
    assert pr_watch._match_bot_identity("CodeRabbitAI[bot]", bots) == "coderabbit"
    assert pr_watch._match_bot_identity("coderabbit", bots) == "coderabbit"

    for forged in (
        "coderabbitai-evil",
        "coderabbit-shim",
        "xcoderabbitai",
        "github-actions",
        "",
        "[bot]",
    ):
        assert pr_watch._match_bot_identity(forged, bots) is None, forged

    # An extra slug reaches matching only when configured — never inferred.
    assert pr_watch._match_bot_identity("reviewer-app", bots) is None
    assert (
        pr_watch._match_bot_identity(
            "reviewer-app", bots, app_slugs={"coderabbit": frozenset({"reviewer-app"})}
        )
        == "coderabbit"
    )


def test_a_bot_listed_only_by_its_bot_login_is_still_trusted_as_an_app_slug() -> None:
    """The two identity namespaces spell the same service differently (#95).

    A status context reports `creator.login: coderabbitai[bot]`; the same service
    is `coderabbitai` as a check run's `app.slug`. An adopter who enumerated only
    the login form must not silently lose outage detection on the check-run
    surface — so `_trusted_bot_identities` admits each configured entry in its
    `[bot]`-stripped spelling too.

    This is invisible under the SHIPPED config, which happens to list both forms,
    and it was a mutation survivor for exactly that reason: the property was real,
    the default config made it redundant, and no test reached the case where it
    matters.
    """
    pr_watch = _load_pr_watch()
    bots = ("coderabbit",)
    # An adopter who wrote only the `[bot]` login.
    login_only = {"coderabbit": frozenset({"somereviewer[bot]"})}

    assert {"coderabbit", "somereviewer", "somereviewer[bot]"} <= pr_watch._trusted_bot_identities(
        "coderabbit", aliases=login_only, app_slugs={}
    )
    # The app-slug spelling of the login they DID write is trusted…
    assert (
        pr_watch._match_bot_identity("somereviewer", bots, aliases=login_only, app_slugs={})
        == "coderabbit"
    )
    # …and stripping never invents an identity they did not write.
    assert (
        pr_watch._match_bot_identity("somereviewer-evil", bots, aliases=login_only, app_slugs={})
        is None
    )
    assert (
        pr_watch._match_bot_identity("otherreviewer", bots, aliases=login_only, app_slugs={})
        is None
    )


def test_the_render_says_an_untrusted_outage_did_not_cancel_anything() -> None:
    """A reported-but-untrusted outage must not read like a normal one (#95).

    Both entries carry the same `reason`, so without this the operator sees the
    identical "review unavailable" line whether the outage cancelled the pending
    block or was ignored — and the difference is the whole point of the gate.
    """
    pr_watch = _load_pr_watch()
    forged = pr_watch.build_report(
        _green_view(),
        [],
        set(),
        check_details=[
            _bot_check(name="CodeRabbit", state="PENDING", bucket="pending", startedAt=_minutes_ago(1)),
            _bot_check(
                name="coderabbit-shim",
                description="Review rate limited",
                identity="github-actions",
            ),
        ],
        now=NOW,
    )
    forged_text = pr_watch.render(forged)

    assert "does NOT cancel a pending review (#95)" in forged_text
    assert "github-actions" in forged_text
    assert "review.bot_app_slugs" in forged_text

    # The positive control: a genuine outage keeps the plain wording, so the
    # assertions above are about trust and not about any outage line at all.
    genuine = pr_watch.render(
        pr_watch.build_report(
            _green_view(),
            [],
            set(),
            check_details=[_bot_check(description="Review rate limited")],
            now=NOW,
        )
    )
    assert "review unavailable" in genuine
    assert "does NOT cancel" not in genuine


def test_the_newest_posting_owns_a_status_context_identity() -> None:
    """`/commits/{sha}/statuses` returns history, and only the latest row counts.

    A context can be posted to repeatedly — this repo's own head carries three
    `CodeRabbit` rows. If an older row could supply the identity, a forged latest
    posting would inherit the real reviewer's identity from history and its
    description would cancel under a trusted name. That is the fail-open
    direction, so newest wins, computed from `created_at` rather than assumed
    from response order.
    """
    pr_watch = _load_pr_watch()
    # Deliberately NOT newest-first, to prove ordering is computed.
    history = [
        {
            "context": "CodeRabbit",
            "created_at": "2026-08-10T11:00:00Z",
            "id": 1,
            "creator": {"login": "coderabbitai[bot]"},
        },
        {
            "context": "CodeRabbit",
            "created_at": "2026-08-10T12:00:00Z",
            "id": 3,
            "creator": {"login": "github-actions[bot]"},
        },
        {
            "context": "CodeRabbit",
            "created_at": "2026-08-10T11:30:00Z",
            "id": 2,
            "creator": {"login": "coderabbitai[bot]"},
        },
    ]

    assert pr_watch._newest_status_creators(history) == {"CodeRabbit": "github-actions[bot]"}

    # Reversing the input cannot change the answer.
    assert pr_watch._newest_status_creators(list(reversed(history))) == {
        "CodeRabbit": "github-actions[bot]"
    }

    # Same second: the monotonic id breaks the tie. The two rows are ordered
    # OPPOSITELY by id and by login on purpose — higher id is "a", higher login is
    # "b" — so only an implementation that really consults the id can return "a".
    # An earlier version of this fixture had id and login agreeing ("b" both
    # ways), which meant replacing the id with a constant passed the whole suite:
    # the property was named in the comment above and pinned by nothing.
    same_second = [
        {"context": "c", "created_at": "2026-08-10T12:00:00Z", "id": 9, "creator": {"login": "a"}},
        {"context": "c", "created_at": "2026-08-10T12:00:00Z", "id": 4, "creator": {"login": "b"}},
    ]
    assert pr_watch._newest_status_creators(same_second) == {"c": "a"}

    # A malformed row cannot crash the resolver.
    assert pr_watch._newest_status_creators(
        ["not-a-dict", {"context": ""}, {"context": "c", "creator": "nope"}]
    ) == {"c": ""}

    # A NEWER malformed row does replace an older good identity, and that is the
    # intended direction: eviction here can only downgrade a context to
    # untrusted, never forge a trusted one. Stated as a test rather than a
    # comment because the safety of the whole helper rests on which way this
    # goes — resolving to the older row's identity is the fail-open shape
    # `_newest_status_creators` exists to prevent.
    assert pr_watch._newest_status_creators(
        [
            {
                "context": "c",
                "created_at": "2026-08-10T11:00:00Z",
                "id": 1,
                "creator": {"login": "coderabbitai[bot]"},
            },
            {"context": "c", "created_at": "2026-08-10T12:00:00Z", "id": 2, "creator": "nope"},
        ]
    ) == {"c": ""}


def test_a_status_rows_identity_comes_from_the_creator_join() -> None:
    """The combined-status endpoint has no `creator`, so identity is joined in.

    Verified against this repo: `/commits/{sha}/status` returns only
    `avatar_url, context, created_at, description, id, node_id, state,
    target_url, updated_at, url` — no creator anywhere. A check RUN needs no join
    because it carries its own `app`.
    """
    pr_watch = _load_pr_watch()
    check_runs = [
        {
            "name": "toolkit",
            "status": "completed",
            "conclusion": "success",
            "app": {"slug": "github-actions"},
        }
    ]
    statuses = [{"context": "CodeRabbit", "state": "success", "description": "Review completed"}]

    joined = pr_watch._rest_check_rows(
        check_runs, statuses, status_creators={"CodeRabbit": "coderabbitai[bot]"}
    )
    assert joined[0]["identity"] == "github-actions"
    assert joined[1]["identity"] == "coderabbitai[bot]"

    # No join performed (the identity read was skipped or failed) -> untrusted,
    # never a silent trust.
    unjoined = pr_watch._rest_check_rows(check_runs, statuses)
    assert unjoined[1]["identity"] == ""
    # …but the check run's own identity does not depend on the join at all.
    assert unjoined[0]["identity"] == "github-actions"


def test_an_ambiguous_check_name_resolves_to_no_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two check runs sharing a name must collapse to no identity (#95).

    `gh pr checks` rows carry nothing to tell same-named runs apart, so the join
    is by name. Picking the trusted one would be the fail-open guess: a forged
    run named exactly `CodeRabbit` would lend its description the real app's
    identity. An attacker can always force this state, so it has to be the
    harmless one.
    """
    pr_watch = _load_pr_watch()

    def fake_pages(path: str):
        if "check-runs" in path:
            return [
                {
                    "check_runs": [
                        {"name": "CodeRabbit", "app": {"slug": "coderabbitai"}},
                        {"name": "CodeRabbit", "app": {"slug": "github-actions"}},
                        {"name": "toolkit", "app": {"slug": "github-actions"}},
                    ]
                }
            ]
        return [[]]

    monkeypatch.setattr(pr_watch, "_gh_api_pages", fake_pages)

    resolved = pr_watch._gh_identity_map("deadbeef")

    assert "CodeRabbit" not in resolved
    # An unambiguous name in the same payload still resolves — otherwise this
    # test would pass against a function that returned {} unconditionally.
    assert resolved["toolkit"] == "github-actions"


def test_a_gh_spawn_failure_in_the_identity_read_cannot_crash_the_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_gh` translates only TimeoutExpired, so the identity read must catch more.

    `fetch_check_details` is documented as never raising and `main` calls it
    OUTSIDE its try deliberately. An `OSError` or a non-timeout
    `SubprocessError` escaping the identity read would therefore crash the poll
    *before* `persist_poll` — no state written, and every later poll repeating it.
    A wedge from one failed subprocess spawn.

    Each raiser below escapes `_gh` untranslated today, which is what makes this
    a real path rather than a defensive nicety.
    """
    pr_watch = _load_pr_watch()

    for raiser in (
        FileNotFoundError("gh: No such file or directory"),
        OSError(12, "Cannot allocate memory"),
        subprocess.SubprocessError("spawn failed"),
        subprocess.CalledProcessError(1, "gh"),
    ):

        def boom(*args, _exc=raiser, **kwargs):
            raise _exc

        monkeypatch.setattr(pr_watch, "_gh", boom)

        # Degrades to no pages, so no identity — never a raise.
        assert pr_watch._gh_api_pages("repos/x/y/commits/abc/check-runs") == []
        assert pr_watch._gh_identity_map("abc") == {}

    # A positive control: with `_gh` working, pages really do come back — so the
    # assertions above are about the guard and not about a function that returns
    # {} regardless.
    monkeypatch.setattr(
        pr_watch,
        "_gh",
        lambda *a, **k: '[{"check_runs": [{"name": "toolkit", "app": {"slug": "github-actions"}}]}]',
    )
    assert pr_watch._gh_identity_map("abc") == {"toolkit": "github-actions"}

    # The SECOND `_gh` call on this path: resolving the head sha when the caller
    # supplied none. It goes through `_gh_json`, whose own except clause needs the
    # same class — reached end-to-end through `fetch_check_details` rather than by
    # calling the helper, because that is the contract that must not raise.
    class _Result:
        def __init__(self) -> None:
            # A bot-named row WITH an outage marker, so `_outage_row_present` is
            # true and the identity read is actually attempted.
            self.stdout = (
                '[{"name":"CodeRabbit","state":"SUCCESS","bucket":"pass",'
                '"description":"Review rate limited"}]'
            )
            self.returncode = 0
            self.stderr = ""

    monkeypatch.setattr(pr_watch.subprocess, "run", lambda *a, **k: _Result())

    def _gh_boom(*a, **k):
        raise OSError("gh vanished between backend resolution and this call")

    monkeypatch.setattr(pr_watch, "_gh", _gh_boom)

    # No `head_sha=`, so the sha fallback runs and raises inside `_gh_json`.
    details = pr_watch.fetch_check_details(1)

    assert details.signal == "ok"
    assert details.rows[0]["identity"] == ""
    # …and the unresolved identity means the outage cannot cancel anything.
    assert (
        pr_watch.summarize_review_bots(details.rows, [], now=NOW)["unavailable"][0]["trusted"]
        is False
    )


def test_a_failed_identity_read_keeps_the_rows_it_already_had(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient failure in the identity read must not blank the bot signal.

    The rows are already fetched and already carry the outage marker by the time
    the identity read runs. If a 403 or a network blip on that third call
    discarded them, #19's and #23's guards would go dark for the whole poll — the
    same "silent bypass" shape as the wrong-reader defect, reached by ordinary
    flakiness rather than by a bug. Degrading to no-identity keeps every row and
    costs at most the grace window.

    Also the transport-parity check: `_gh_api_pages` already swallows these
    classes and returns `{}` while keeping its rows, and this file's own doctrine
    says the REST path's job is parity with `gh`.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    calls: list[str] = []

    def _get(url: str, token: str, **_kw):
        calls.append(url)
        if "/statuses?" in url:
            # Transient, and specifically NOT a shape problem — the failure the
            # wrong-reader fix cannot help with.
            raise RuntimeError("GitHub API GET … returned 403 (secondary rate limit)")
        if "check-runs" in url:
            return {"total_count": 0, "check_runs": []}, None
        if "/status?" in url:
            return {
                "state": "success",
                "statuses": [
                    {
                        "context": "CodeRabbit",
                        "state": "success",
                        "description": "Review rate limited",
                    }
                ],
            }, None
        if "pulls/5" in url:
            return {"head": {"sha": "abc123"}}, None
        raise AssertionError(f"unrouted GET {url}")

    monkeypatch.setattr(pr_watch, "_http_get", _get)

    details = pr_watch.fetch_check_details(5, bots=("coderabbit",))

    # The identity read was attempted and failed…
    assert any("/statuses?" in url for url in calls), calls
    # …and the row survived it, rather than the signal going dark.
    assert details.signal == "ok"
    assert [row["name"] for row in details.rows] == ["CodeRabbit"]
    assert details.rows[0]["description"] == "Review rate limited"

    # The outage is still REPORTED, just not trusted — so the panel signal
    # survives while the cancel does not.
    bots = pr_watch.summarize_review_bots(
        details.rows, [], now=NOW, bots=("coderabbit",), signal=details.signal
    )
    assert bots["unavailable"][0]["trusted"] is False
    assert bots["unavailable"][0]["identity"] == ""


def test_the_real_gh_head_sha_drives_the_head_move_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise `_gh_head_sha` ITSELF, not a stand-in for it.

    The head-move guard's other test patches `_gh_head_sha` to canned strings, so
    hardwiring its real body to a constant left the entire suite green. That is the
    same "mocked the helper under test" shape that made the wrong-reader CRITICAL
    invisible while 500+ new test lines were already in the diff — so the guard
    against a bypass had an illusory safety net of exactly the kind this loop keeps
    finding.

    Here only `subprocess.run` is stubbed, at the process boundary. `_gh`,
    `_gh_json` and `_gh_head_sha` all run for real, and both guard directions are
    driven end-to-end through `fetch_check_details`.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_resolve_backend", lambda: ("gh", None))
    monkeypatch.setattr(
        pr_watch, "_gh_identity_map", lambda _sha: {"CodeRabbit": "coderabbitai[bot]"}
    )

    class _Result:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.returncode = 0
            self.stderr = ""

    head = {"sha": "abc123"}
    seen: list[list[str]] = []

    def _run(cmd, **_kwargs):
        seen.append(list(cmd))
        if "checks" in cmd:
            return _Result(
                '[{"name":"CodeRabbit","state":"SUCCESS","bucket":"pass",'
                '"description":"Review rate limited"}]'
            )
        if "view" in cmd:
            return _Result(json.dumps({"headRefOid": head["sha"]}))
        raise AssertionError(f"unexpected gh call: {cmd}")

    monkeypatch.setattr(pr_watch.subprocess, "run", _run)

    # The real helper parses `headRefOid` — the success path nothing reached.
    assert pr_watch._gh_head_sha(5) == "abc123"

    # Head STEADY: the real helper agrees with the supplied sha, identity stands.
    steady = pr_watch.fetch_check_details(5, bots=("coderabbit",), head_sha="abc123")
    assert steady.rows[0]["identity"] == "coderabbitai[bot]"
    assert any("view" in cmd for cmd in seen), seen

    # Head MOVED: the real helper reports a different sha, identity is dropped.
    head["sha"] = "def456"
    moved = pr_watch.fetch_check_details(5, bots=("coderabbit",), head_sha="abc123")
    assert moved.rows[0]["identity"] == ""

    # And with no `head_sha` supplied, the real helper is what resolves it, so a
    # steady head still resolves identity through two live reads of the same sha.
    resolved = pr_watch.fetch_check_details(5, bots=("coderabbit",))
    assert resolved.rows[0]["identity"] == "coderabbitai[bot]"


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("gh failed"),
        OSError("gh is not installed"),
        subprocess.SubprocessError("spawn failed"),
        json.JSONDecodeError("bad", "doc", 0),
        AttributeError("None has no attribute get"),
    ],
)
def test_gh_head_sha_swallows_every_class_it_declares(
    monkeypatch: pytest.MonkeyPatch, exc: Exception
) -> None:
    """Each class in `_gh_head_sha`'s except tuple must actually be exercised.

    Trimming that tuple to `OSError` alone left the suite green, so the breadth was
    documented and unverified. It matters because this helper is reached from
    `fetch_check_details`, which is documented as never raising and whose caller in
    `main` sits outside the try — an escaping class crashes the poll before
    `persist_poll` and wedges every later poll.
    """
    pr_watch = _load_pr_watch()

    def _boom(*_a, **_k):
        raise exc

    monkeypatch.setattr(pr_watch, "_gh", _boom)

    assert pr_watch._gh_head_sha(5) == ""


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("returned list, expected a JSON object"),
        OSError("connection reset"),
        KeyError("statuses"),
        ValueError("bad json"),
        AttributeError("NoneType has no attribute get"),
        TypeError("string indices must be integers"),
    ],
)
def test_the_rest_identity_read_swallows_every_class_it_declares(
    monkeypatch: pytest.MonkeyPatch, exc: Exception
) -> None:
    """Same for the REST inner try: trimming it to `RuntimeError` stayed green.

    Every class here must leave the already-fetched rows intact rather than
    blanking the bot signal, which is the whole point of that inner try.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)

    def _get(url: str, token: str, **_kw):
        if "/statuses?" in url:
            raise exc
        if "check-runs" in url:
            return {"total_count": 0, "check_runs": []}, None
        if "/status?" in url:
            return {
                "state": "success",
                "statuses": [
                    {
                        "context": "CodeRabbit",
                        "state": "success",
                        "description": "Review rate limited",
                    }
                ],
            }, None
        if "pulls/5" in url:
            return {"head": {"sha": "abc123"}}, None
        raise AssertionError(f"unrouted GET {url}")

    monkeypatch.setattr(pr_watch, "_http_get", _get)

    details = pr_watch.fetch_check_details(5, bots=("coderabbit",))

    assert details.signal == "ok"
    assert [row["name"] for row in details.rows] == ["CodeRabbit"]
    assert details.rows[0]["identity"] == ""


def test_a_head_move_during_the_gh_identity_read_drops_every_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`gh pr checks` reports the CURRENT head and carries no sha (#95 TOCTOU).

    Identities are resolved for a specific sha, so a push landing between the two
    calls leaves rows from one commit joined BY NAME to identities from another. A
    same-repo PR can push — the capability #95 already assumes — so a forged row
    on the new commit could otherwise inherit the real reviewer's identity from a
    same-named check on the old one, bypassing this PR's own guard.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_resolve_backend", lambda: ("gh", None))

    class _Result:
        def __init__(self) -> None:
            self.stdout = (
                '[{"name":"CodeRabbit","state":"SUCCESS","bucket":"pass",'
                '"description":"Review rate limited"}]'
            )
            self.returncode = 0
            self.stderr = ""

    monkeypatch.setattr(pr_watch.subprocess, "run", lambda *a, **k: _Result())
    monkeypatch.setattr(
        pr_watch,
        "_gh_identity_map",
        lambda _sha: {"CodeRabbit": "coderabbitai[bot]"},
    )

    # Head UNCHANGED: the identity stands and the genuine outage can cancel.
    monkeypatch.setattr(pr_watch, "_gh_head_sha", lambda _pr: "abc123")
    steady = pr_watch.fetch_check_details(5, bots=("coderabbit",), head_sha="abc123")
    assert steady.rows[0]["identity"] == "coderabbitai[bot]"

    # Head MOVED between the rows read and the identity read: every identity is
    # dropped, so nothing can cancel on a cross-commit name join.
    monkeypatch.setattr(pr_watch, "_gh_head_sha", lambda _pr: "def456")
    moved = pr_watch.fetch_check_details(5, bots=("coderabbit",), head_sha="abc123")
    assert moved.rows[0]["identity"] == ""
    assert (
        pr_watch.summarize_review_bots(
            moved.rows, [], now=NOW, bots=("coderabbit",)
        )["unavailable"][0]["trusted"]
        is False
    )


def test_the_gh_backend_resolves_a_status_contexts_creator_across_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `gh` backend's STATUS-context identity path, which is the one that
    matters most on this repo and was pinned by nothing.

    CodeRabbit posts a status context here, not a check run — verified against
    this repo's own PR heads. So on the default backend the reviewer's identity
    arrives exclusively through the plural-statuses read and its page-list
    flattening. Emptying that flattening left the whole suite green while every
    genuine outage silently became untrusted: fail-closed, so bounded, but it
    disables #23's acceleration for the primary reviewer on the default backend.

    The two endpoints' `--paginate --slurp` shapes differ and both are exercised
    here: check-runs yields page OBJECTS, statuses yields page LISTS. Two status
    pages, so a flattening that only reads the first is caught too.
    """
    pr_watch = _load_pr_watch()

    def fake_pages(path: str):
        if "check-runs" in path:
            return [{"check_runs": [{"name": "toolkit", "app": {"slug": "github-actions"}}]}]
        return [
            [
                {
                    "context": "CodeRabbit",
                    "created_at": "2026-08-10T11:00:00Z",
                    "id": 1,
                    "creator": {"login": "coderabbitai[bot]"},
                }
            ],
            [
                {
                    "context": "legacy/ci",
                    "created_at": "2026-08-10T11:30:00Z",
                    "id": 2,
                    "creator": {"login": "some-ci[bot]"},
                }
            ],
        ]

    monkeypatch.setattr(pr_watch, "_gh_api_pages", fake_pages)

    resolved = pr_watch._gh_identity_map("abc")

    assert resolved["CodeRabbit"] == "coderabbitai[bot]"
    # From the SECOND page, so a first-page-only flattening fails here.
    assert resolved["legacy/ci"] == "some-ci[bot]"
    # The check-run surface still resolves in the same call.
    assert resolved["toolkit"] == "github-actions"

    # End to end: that identity is what lets the real reviewer's outage cancel.
    outage = pr_watch.summarize_review_bots(
        [
            _bot_check(
                name="CodeRabbit",
                description="Review rate limited",
                identity=resolved["CodeRabbit"],
            )
        ],
        [],
        now=NOW,
    )
    assert outage["unavailable"][0]["trusted"] is True


def test_identity_is_read_only_when_a_row_could_cancel_something() -> None:
    """The lazy precondition: a healthy poll must not pay for the identity read.

    Also the guard against the read being skipped when it DOES matter — the two
    directions are one predicate, so they are pinned together.
    """
    pr_watch = _load_pr_watch()
    bots = ("coderabbit",)

    # Healthy reviewer, nothing to cancel.
    assert not pr_watch._outage_row_present([_bot_check()], bots)
    assert not pr_watch._outage_row_present(
        [_bot_check(state="PENDING", bucket="pending")], bots
    )
    # A non-bot check carrying outage-shaped text is not the reviewer's outage.
    assert not pr_watch._outage_row_present(
        [{"name": "toolkit", "description": "Review rate limited"}], bots
    )
    # A bot-named row with an outage marker is exactly the case that needs it —
    # including the forged name, which is the whole point: the fetch must happen
    # so the identity can be judged.
    assert pr_watch._outage_row_present(
        [_bot_check(description="Review rate limited")], bots
    )
    assert pr_watch._outage_row_present(
        [{"name": "coderabbit-shim", "description": "Review rate limited"}], bots
    )


def test_configured_bot_app_slugs_reach_runtime_matching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`review.bot_app_slugs` must reach the outage decision, not just parse."""
    _load_pr_watch()
    kitconfig = sys.modules["kitconfig"]
    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *args, **kwargs: {
            "review": {
                "bots": ["otherbot"],
                "bot_app_slugs": {"otherbot": ["otherbot-review-app"]},
                "unavailable_markers": ["review offline"],
            }
        },
    )

    runtime = _load_pr_watch(pin_defaults=False)

    assert {"otherbot": frozenset({"otherbot-review-app"})} == runtime._REVIEW_BOT_APP_SLUGS
    outage = runtime.summarize_review_bots(
        [
            {
                "name": "otherbot",
                "state": "PENDING",
                "bucket": "pending",
                "description": "review offline",
                "identity": "otherbot-review-app",
                "startedAt": _minutes_ago(1),
            }
        ],
        [],
        now=NOW,
    )
    assert outage["unavailable"][0]["trusted"] is True
    assert outage["blockers"] == []


def test_a_non_reviewer_commenter_cannot_speak_for_the_bot() -> None:
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
    assert pr_watch._match_bot("coderabbit-impersonator", bots, anchored=True) is None

    # …and quoted outage text from a non-reviewer never becomes an outage signal.
    comments = pr_watch.collect_comments(
        {
            "comments": [
                {
                    "id": "lookalike-1",
                    "author": {"login": "xcoderabbit"},
                    "body": "Review skipped — Draft detected.",
                }
            ]
        },
        [],
    )
    assert comments[0]["review_unavailable_reason"] is None
    status = pr_watch.summarize_review_bots(
        [_bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(1))],
        comments,
        now=NOW,
    )
    assert status["unavailable"] == []
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
    # `identity` is present on every row even on a healthy poll where the #95
    # identity read never ran — the key's presence must not depend on that, or a
    # caller indexing it raises on the common path.
    assert pr_watch.fetch_check_details(1) == (
        [{"name": "CodeRabbit", "state": "PENDING", "identity": ""}],
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
    view = _green_view()
    args = dict(
        review_receipt={"head": "abc123", "source": "coderabbit"},
        now=NOW,
        **_settled(view, now=NOW),
    )

    without = pr_watch.build_report(view, [], set(), **args)
    with_pending = pr_watch.build_report(
        view,
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
  bot_author_aliases:
    OtherBot: [OtherBotAI, "OtherBotAI[bot]"]
  noise_markers:
    - "<!-- Generated by OtherBot -->"
    - "NOTHING TO REPORT"
  unavailable_markers:
    - "OtherBot Is Out Of Credits"
  comment_verdict_markers:
    - "OtherBot Found Nothing"
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
    assert resolved.comment_verdict_markers == ("otherbot found nothing",)
    assert resolved.informational_checks == frozenset({"otherbot", "advisory"})
    assert resolved.require_ci is False
    assert resolved.bots == ("otherbot",)
    assert resolved.bot_author_aliases == {
        "otherbot": frozenset({"otherbotai", "otherbotai[bot]"})
    }
    assert resolved.bot_pending_grace_minutes == 30
    # None of the kit's own default markers leak in — config replaces, not extends.
    assert "<!-- walkthrough_start -->" not in resolved.noise_markers


@pytest.mark.parametrize(
    "alias_block",
    [
        "coderabbit: 42",
        "coderabbit: []",
    ],
    ids=["wrong-value-type", "empty-alias-list"],
)
def test_malformed_bot_author_aliases_warn_and_fall_back(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], alias_block: str
) -> None:
    pr_watch = _load_pr_watch()
    path = _write_config(
        tmp_path,
        f"review:\n  bot_author_aliases:\n    {alias_block}\n",
    )

    resolved = pr_watch._load_review_config(path)

    assert resolved.bot_author_aliases == pr_watch._DEFAULT_REVIEW_BOT_AUTHOR_ALIASES
    assert "bot_author_aliases must map bot names" in capsys.readouterr().err


def test_non_string_bot_key_is_rejected() -> None:
    pr_watch = _load_pr_watch()

    assert pr_watch._normalize_bot_author_aliases({42: ["coderabbitai"]}) is None


def test_omitted_bot_author_aliases_use_defaults_without_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pr_watch = _load_pr_watch()
    resolved = pr_watch._load_review_config(
        _write_config(tmp_path, "review:\n  bots: [otherbot]\n")
    )

    assert resolved.bot_author_aliases == pr_watch._DEFAULT_REVIEW_BOT_AUTHOR_ALIASES
    assert capsys.readouterr().err == ""


def test_configured_aliases_reach_runtime_matching(monkeypatch: pytest.MonkeyPatch) -> None:
    _load_pr_watch()  # ensure the shared top-level kitconfig module is imported
    kitconfig = sys.modules["kitconfig"]
    monkeypatch.setattr(
        kitconfig,
        "load_config",
        lambda *args, **kwargs: {
            "review": {
                "bots": ["otherbot"],
                "bot_author_aliases": {"otherbot": ["otherbotai[bot]"]},
                "noise_markers": ["generated summary"],
                "unavailable_markers": ["review offline"],
            }
        },
    )

    runtime = _load_pr_watch(pin_defaults=False)

    assert {
        "otherbot": frozenset({"otherbotai[bot]"})
    } == runtime._REVIEW_BOT_AUTHOR_ALIASES
    assert (
        runtime.review_unavailable_reason(
            "generated summary — review offline", author="OtherBotAI[bot]"
        )
        == "review offline"
    )


def test_missing_config_falls_back_to_defaults_silently(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A standalone engine run (no config at all) must behave exactly as before."""
    pr_watch = _load_pr_watch()

    resolved = pr_watch._load_review_config(tmp_path / "absent.yaml")

    assert resolved == (
        pr_watch._DEFAULT_NOISE_MARKERS,
        pr_watch._DEFAULT_REVIEW_UNAVAILABLE_MARKERS,
        pr_watch._DEFAULT_COMMENT_VERDICT_MARKERS,
        frozenset(pr_watch._DEFAULT_INFORMATIONAL_CHECK_NAMES),
        True,
        pr_watch._DEFAULT_REVIEW_BOTS,
        pr_watch._DEFAULT_REVIEW_BOT_AUTHOR_ALIASES,
        pr_watch._DEFAULT_REVIEW_BOT_APP_SLUGS,
        pr_watch._DEFAULT_BOT_PENDING_GRACE_MINUTES,
        pr_watch._DEFAULT_SETTLE_GRACE_MINUTES,
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
        "_COMMENT_VERDICT_MARKERS": (("zzz-sentinel-verdict",), "comment_verdict_markers"),
        "_INFORMATIONAL_CHECK_NAMES": (frozenset({"zzz-sentinel-check"}), "informational_checks"),
        "_REQUIRE_CI": ("zzz-sentinel-require-ci", "require_ci"),
        "_REVIEW_BOTS": (("zzz-sentinel-bot",), "bots"),
        "_REVIEW_BOT_AUTHOR_ALIASES": (
            {"zzz-sentinel-bot": frozenset({"zzz-sentinel-alias"})},
            "bot_author_aliases",
        ),
        "_REVIEW_BOT_APP_SLUGS": (
            {"zzz-sentinel-bot": frozenset({"zzz-sentinel-slug"})},
            "bot_app_slugs",
        ),
        "_BOT_PENDING_GRACE_MINUTES": (-99999.0, "bot_pending_grace_minutes"),
        "_SETTLE_GRACE_MINUTES": (-99998.0, "settle_grace_minutes"),
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


# --------------------------------------------------------------------------- #
# noise markers vs. the wording a bot actually emits (issue #468)
# --------------------------------------------------------------------------- #
#
# The three bodies below are CAPTURED, not invented — each is the opening of a
# real comment on this repo, quoted verbatim and truncated. That is the whole
# point: the marker these tests replaced was pinned by a hand-written string no
# bot had ever produced, so the pin held while the marker matched nothing.
#
# Read `docs/kit-friction-log-archive.md` (2026-08-13) and #468 for the finding.

# CodeRabbit's clean verdict, from its summary comment on PR #462 (2026-08-13).
# Truncated after the verdict sentence; the real comment continues into a
# walkthrough section that carries `<!-- walkthrough_start -->` as well. Stopping
# short of it is deliberate — the summary comment is emitted WITHOUT a walkthrough
# often enough (PRs #443, #444, #445, #451, #459 among others) that the opening
# marker is the one doing the filtering in those cases, and this fixture asserts
# against that weaker case rather than the doubly-marked one.
CLEAN_VERDICT_COMMENT = (
    "<!-- This is an auto-generated comment: summarize by coderabbit.ai -->\n"
    "<!-- review_stack_entry_start -->\n\n"
    "[![Review Change Stack](https://storage.googleapis.com/coderabbit_public_assets"
    "/review-stack-in-coderabbit-ui.svg)](https://app.coderabbit.ai/change-stack"
    "/topij/agentic-dev-kit/pull/462)\n\n"
    "<!-- review_stack_entry_end -->\n"
    "<!-- recent_review_start -->\n\n"
    "No actionable comments were generated in the recent review. 🎉\n"
)

# The operator's own review-record comment on PR #43 (2026-07-26), which quotes
# CodeRabbit's clean verdict as evidence. No configured marker matches it, and
# none may: it is a human explaining why the review receipt reads `coderabbit`
# rather than `fallback:panel`, i.e. exactly the kind of comment the gate exists
# to make someone acknowledge.
HUMAN_COMMENT_QUOTING_THE_CLEAN_VERDICT = (
    "## Review record\n\n"
    "**CodeRabbit reviewed this and found nothing** — plan Pro Plus, profile "
    "CHILL, `Configuration used: defaults`:\n\n"
    "> No actionable comments were generated in the recent review. 🎉\n\n"
    "## Why the receipt says `coderabbit` and not `fallback:panel`\n\n"
    "**No panel ran on this PR.** The receipt names the review that actually "
    "happened.\n"
)

# CodeRabbit's review submission when it DOES have findings, from PR #411. This
# is the only surface and the only shape in which "Actionable comments posted:"
# has ever appeared on this repo — always with a count of one or more.
REVIEW_WITH_FINDINGS = (
    "**Actionable comments posted: 5**\n\n"
    "<details>\n"
    "<summary>🤖 Prompt for all review comments with AI agents</summary>\n"
)


# Each of the three below runs twice: once against the ENGINE defaults (the
# kit-owned literals an adopter without the key falls back to) and once against
# whatever `config/dev-model.yaml` this checkout ships. Both are real answers to
# "would the live loop filter this?", and #468 was a drift between exactly those
# two copies of the same list.
@pytest.mark.parametrize("source", ["engine-defaults", "shipped-config"])
def test_the_clean_verdict_is_filtered_by_a_structural_marker(source: str) -> None:
    """A clean CodeRabbit review must not block the loop as an unacknowledged
    comment — and the marker that filters it must be the container's HTML
    marker, not the verdict sentence.

    WHAT THIS DOES NOT CATCH, stated plainly: the fixture is frozen at
    CodeRabbit's 2026-08 output. If the bot renames
    `<!-- This is an auto-generated comment: summarize by coderabbit.ai -->`
    tomorrow, this test keeps passing against the stale copy and the live loop
    starts surfacing clean reviews as findings. Nothing in this repo can detect
    that; only re-reading the forge can, which is what #468 did by hand. What the
    test DOES catch is the reverse direction — a change to the marker list that
    stops filtering the wording we have actually observed.
    """
    pr_watch = _load_pr_watch(pin_defaults=source == "engine-defaults")
    if source == "shipped-config" and not pr_watch._NOISE_MARKERS:
        pytest.skip(
            "ambient config empties noise_markers — a supported adopter state "
            "(`_load_review_config` documents it) in which nothing is filtered"
        )

    assert pr_watch.is_noise(CLEAN_VERDICT_COMMENT) is True
    # ...and specifically because of the container marker. Deleting the verdict
    # sentence must not change the verdict.
    without_the_sentence = CLEAN_VERDICT_COMMENT.replace(
        "No actionable comments were generated in the recent review. 🎉\n", ""
    )
    assert without_the_sentence != CLEAN_VERDICT_COMMENT
    assert pr_watch.is_noise(without_the_sentence) is True


@pytest.mark.parametrize("source", ["engine-defaults", "shipped-config"])
def test_a_human_quoting_the_clean_verdict_is_not_noise(source: str) -> None:
    """The tripwire against the tempting fix for #468.

    `is_noise` matches the BODY with no author check, so adding CodeRabbit's
    verdict sentence to `noise_markers` — the obvious repair for a drifted
    marker — would also discard the comment below, which is a human's review
    record quoting that sentence. On this repo that comment is not hypothetical:
    it is PR #43, the one place the phrase has ever appeared outside a bot
    comment, and it carried the reasoning behind a hand-recorded review receipt.

    Be clear about why this passes TODAY: trivially, because no configured marker
    appears anywhere in the body. Its job is to start failing the day someone
    adds the sentence — a change that would otherwise look green and would let
    `converged` flip past an unacknowledged human comment. That is the fail-open
    direction, so it gets a test even though it asserts a negative.
    """
    pr_watch = _load_pr_watch(pin_defaults=source == "engine-defaults")

    assert pr_watch.is_noise(HUMAN_COMMENT_QUOTING_THE_CLEAN_VERDICT) is False
    assert (
        pr_watch.is_noise(HUMAN_COMMENT_QUOTING_THE_CLEAN_VERDICT, author="topij")
        is False
    )


@pytest.mark.parametrize("source", ["engine-defaults", "shipped-config"])
def test_a_review_carrying_findings_is_never_noise(source: str) -> None:
    """The other tempting repair, and the more dangerous one.

    Broadening the retired marker to the prefix `"actionable comments posted:"`
    would match every CodeRabbit review that HAS findings — the body below and
    the inline comments it introduces — and silently drop the entire review out
    of `new_comments`. A gate that filters real findings is worse than one that
    filters nothing, so pin it from both sides: the count-phrased review body
    must stay visible whatever else the marker list does.
    """
    pr_watch = _load_pr_watch(pin_defaults=source == "engine-defaults")

    assert pr_watch.is_noise(REVIEW_WITH_FINDINGS) is False
    assert pr_watch.is_noise(REVIEW_WITH_FINDINGS, author="coderabbitai") is False


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
    # This line used to read `is_noise("Actionable comments posted: 0") is True`.
    # It was green from the day it was written while the marker behind it matched
    # nothing on any real comment (#468): the string was invented here, so the
    # assertion proved the config still listed the marker, not that any bot ever
    # emitted it. A captured body is the falsifiable form of the same claim.
    assert pr_watch.is_noise(CLEAN_VERDICT_COMMENT) is True
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
        **_settled(view),
    )

    assert report["new_comments"] == []
    assert report["done"] is True


# --------------------------------------------------------------------------- #
# review coverage: which commit the bot's last review actually saw (issue #27)
# --------------------------------------------------------------------------- #


def _review(login: str, sha: str, at: str, state: str = "COMMENTED") -> dict:
    # `COMMENTED` by default because that is what the configured bot's reviews
    # actually carry on this repo — including its clean ones, verified against
    # PR #484's live review list. A default of `APPROVED` would make the suite
    # exercise a state the real reviewer rarely emits.
    return {
        "author": {"login": login},
        "commit": {"oid": sha},
        "submittedAt": at,
        "state": state,
    }


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


def test_review_coverage_behind_the_head_does_not_gate() -> None:
    """Deliberately the cheap half of #27. Invalidating a receipt when the diff
    changes *shape* is the faithful fix, but it risks becoming a wedge on a repo
    whose bot is permanently unavailable — so this only makes the gap visible at
    merge time instead of reconstructible from the PR thread afterwards.

    This test was named ``..._and_never_gates`` until #350 direction 1, when
    coverage AT the head became one of the merge gate's two evidence routes.
    What it actually pins is unchanged and still true: coverage *behind* the
    head gates nothing, and the merge here rides on the receipt alone.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )

    assert report["review_bots"]["coverage"][0]["covers_head"] is False
    assert "review coverage" in pr_watch.render(report)
    assert "0ldc0de" in pr_watch.render(report)
    # …and the merge gate is untouched by it.
    assert report["mergeable"] is True
    assert report["merge_blockers"] == []


def test_bot_coverage_at_the_head_is_evidence_with_no_receipt() -> None:
    """#350 direction 1, and the whole point of it.

    Before this, `mergeable` required a `--record-review` receipt whose entire
    vocabulary names FALLBACK passes. When the configured bot itself reviewed
    the head there was no literal that described what happened, so an honest
    agent recorded nothing and the gate was unreachable — wedged precisely when
    review had gone well, and hardest on an autonomous lane, whose
    `dev_session.sh merge` reads `mergeable` and nothing else.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(view, [], set(), **_settled(view))

    assert report["review_evidence"]["valid"] is True
    assert report["review_evidence"]["route"] == "bot-coverage"
    assert report["review_evidence"]["bots"] == ["coderabbit"]
    assert report["mergeable"] is True
    assert report["merge_blockers"] == []
    # The receipt-describing keys stay receipt-only, so nothing about this
    # report can be misread as a recorded pass that never ran.
    assert report["review_evidence"]["source"] is None
    assert report["review_evidence"]["lenses"] == []
    # And the render says which reviewer the merge rests on, rather than
    # printing "no lenses recorded" at a real review.
    rendered = pr_watch.render(report)
    assert "coderabbit" in rendered
    assert "no lenses recorded" not in rendered


def test_coverage_of_a_different_sha_never_reaches_the_gate() -> None:
    """`covers_head` is DERIVED, so the gate re-checks the identity it is about
    to authorize against rather than trusting a boolean computed elsewhere in
    the call. A coverage entry naming another commit is not evidence for this
    one, however that entry came to exist."""
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "0ldc0de", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(view, [], set(), **_settled(view))

    assert report["review_evidence"]["valid"] is False
    assert report["review_evidence"]["route"] is None
    assert report["review_evidence"]["bots"] == []
    assert report["mergeable"] is False
    assert (
        "independent review evidence is missing for current head"
        in report["merge_blockers"]
    )


def test_only_a_standing_verdict_is_evidence_not_merely_a_review_at_the_head() -> None:
    """Found by the adversarial lens on `#484`, extended by two more the author
    measured. The gate accepted a review that was attributed to the bot and
    bound to the head and NOT a standing verdict.

    Each excluded state is a different way that can happen:

    - ``DISMISSED`` — a maintainer said explicitly that this review does not
      count. `_rest_review_decision` already honours dismissal for the
      `CHANGES_REQUESTED` blocker, so accepting it here made the gate disagree
      with its own sibling one function away.
    - ``PENDING`` — never submitted. A draft, not a verdict.
    - ``CHANGES_REQUESTED`` — an unresolved objection, not caught by the separate
      `reviewDecision` blocker **on the `gh` transport**, where that field is
      GitHub's own and reflects required-reviewer rules that a bot is typically
      outside. On the REST fallback the blocker does fire, because
      `_rest_review_decision` aggregates every reviewer with no such notion. The
      evidence rule has to hold on both, so it does not defer to that blocker.
      Exercised below with `reviewDecision` empty, which is the `gh`-shaped case
      — and note what that pins and what it does not: `_green_view` sets that
      field independently of its `reviews` list, so this fixes the INPUT the gate
      sees rather than demonstrating how GitHub would populate it.
    - an unknown or missing state — GitHub may add one tomorrow, and a gate that
      accepts what it does not recognize is not a gate.
    """
    pr_watch = _load_pr_watch()

    for state in ("APPROVED", "COMMENTED"):
        view = _green_view(
            reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z", state)]
        )
        report = pr_watch.build_report(view, [], set(), **_settled(view))
        assert report["review_evidence"]["route"] == "bot-coverage", state
        assert report["mergeable"] is True, state

    for state in ("DISMISSED", "PENDING", "CHANGES_REQUESTED", "", "SOME_FUTURE_STATE"):
        view = _green_view(
            reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z", state)]
        )
        # `reviewDecision` stays empty — the `gh`-shaped case for a non-required
        # bot reviewer. Asserted to document the fixture, NOT as evidence about
        # GitHub: `_green_view` sets this field independently of `reviews`, so it
        # pins what the gate is handed, not how the forge would fill it in.
        assert view["reviewDecision"] == ""
        report = pr_watch.build_report(view, [], set(), **_settled(view))

        assert report["review_evidence"]["valid"] is False, state
        assert report["review_evidence"]["route"] is None, state
        assert report["review_evidence"]["bots"] == [], state
        assert report["mergeable"] is False, state
        assert (
            "independent review evidence is missing for current head"
            in report["merge_blockers"]
        ), state

    # A review with NO state key at all — the shape a `gh` too old to emit it,
    # or a REST payload shaped differently, would produce. Fails closed.
    stateless = _review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")
    stateless.pop("state")
    view = _green_view(reviews=[stateless])
    report = pr_watch.build_report(view, [], set(), **_settled(view))
    assert report["review_evidence"]["valid"] is False
    # …and it is still REPORTED as coverage, because the advisory display is not
    # the gate: a reader should still see which commit the bot last looked at.
    assert report["review_bots"]["coverage"][0]["covers_head"] is True
    assert report["review_bots"]["coverage"][0]["state"] == ""


def test_an_inconsistent_coverage_entry_is_refused_by_the_sha_recheck() -> None:
    """Pins the redundant `sha == head` check in `qualifying_bot_coverage`.

    Written as a direct unit call because the inconsistency is NOT reachable
    through `bot_review_coverage` today: that function derives `covers_head` as
    `sha == head`, so the two can never disagree, and an end-to-end test of a
    different sha is rejected by the `covers_head` check before the sha check is
    consulted. Deleting the sha check therefore passes the whole end-to-end
    suite — verified by mutation — which is precisely the unpinned-guard shape
    of #447.

    The guard is kept rather than removed because it defends the merge gate
    against a FUTURE `bot_review_coverage` that computes `covers_head` from
    something other than sha identity (a range, a merge-base, a normalized
    short sha). This test is what makes that defence real instead of decorative:
    it fails if the recheck is dropped, and it documents what the recheck is
    for so a later reader does not delete it as obviously redundant.
    """
    pr_watch = _load_pr_watch()
    inconsistent = {
        "signal": "ok",
        "coverage": [
            {
                "bot": "coderabbit",
                "sha": "0ldc0de",
                "covers_head": True,  # disagrees with `sha`
                "submitted_at": "2026-07-25T12:00:00Z",
                "state": "COMMENTED",  # qualifying, so `sha` is what is tested
            }
        ],
    }

    assert pr_watch.qualifying_bot_coverage(inconsistent, "abc123") == []
    # …and the same entry qualifies once the two agree, so the test is pinning
    # the recheck rather than a blanket refusal.
    consistent = {
        "signal": "ok",
        "coverage": [dict(inconsistent["coverage"][0], sha="abc123")],
    }
    assert pr_watch.qualifying_bot_coverage(consistent, "abc123") == ["coderabbit"]

    # THE MIRROR DIRECTION, and it was unpinned until a lens mutation-tested it:
    # dropping the `covers_head is True` clause while keeping `sha == head`
    # survived the whole suite. Both halves of an `and` need their own failing
    # case, or half the guard is decorative — #447's shape, one clause over from
    # where the neighbouring docstring already warns about it.
    disagreeing_the_other_way = {
        "signal": "ok",
        "coverage": [dict(consistent["coverage"][0], covers_head=False)],
    }
    assert pr_watch.qualifying_bot_coverage(disagreeing_the_other_way, "abc123") == []
    # A missing `covers_head` is refused too. Note what this case does and does
    # NOT pin (#486): `None` is falsy, so it is refused under plain truthiness as
    # well, and an earlier comment here credited the refusal to `is True` — naming
    # a property as the reason for a result that holds either way, which is
    # exactly what would let someone weaken the guard believing it was covered.
    absent = {"signal": "ok", "coverage": [dict(consistent["coverage"][0])]}
    absent["coverage"][0].pop("covers_head")
    assert pr_watch.qualifying_bot_coverage(absent, "abc123") == []

    # THIS is the case that pins `is True` rather than truthiness, and nothing in
    # the suite carried it before (#486): a value that is truthy but not `True`.
    # Mutating the guard to `if entry.get("covers_head"):` left every case above
    # green — verified by mutation — so the identity check was unpinned in the
    # same #447 shape as the clause beside it.
    #
    # Not reachable through `bot_review_coverage` today, whose `sha == head` is
    # always a real `bool`; the guard is forward-defence against a future writer
    # that computes the field from something else, and this is what makes that
    # defence testable instead of decorative.
    for truthy_not_true in (1, "yes", {"covered": True}):
        surrogate = {
            "signal": "ok",
            "coverage": [dict(consistent["coverage"][0], covers_head=truthy_not_true)],
        }
        assert pr_watch.qualifying_bot_coverage(surrogate, "abc123") == [], (
            truthy_not_true
        )


def test_a_receipt_cannot_authorize_a_merge_over_a_standing_bot_objection() -> None:
    """Issue #485, reproduced as filed and then closed.

    Found by the adversarial lens on `#484`'s round-3 panel and confirmed
    PRE-EXISTING there — the same probe against that branch's base gave the same
    result — so it was filed rather than fixed in that PR.

    The shape: a configured bot's live `CHANGES_REQUESTED` on the exact current
    head, with a `fallback:panel` receipt also at that head. Before this guard
    the gate returned `mergeable: True` with an EMPTY blocker list, and the
    receipt carried none of the engine's "this is less than it looks" markers —
    no `override`, no `bot_signal`, no `bots_behind_head`. It read completely
    clean. `dev_session.sh merge` reads `mergeable` and nothing else, so this was
    reachable on the real autonomous-merge path, not only in the JSON report.

    `reviewDecision` stays empty throughout: that is the `gh` shape for a
    non-required bot reviewer, and `gh` is the only transport `--record-review`
    runs on (`require_gh_backend`). So the aggregate blocker cannot be what
    catches this.
    """
    pr_watch = _load_pr_watch()
    receipt = {"head": "abc123", "source": "fallback:panel"}
    view = _green_view(
        reviews=[
            _review("coderabbitai", "abc123", "2026-07-25T12:00:00Z", "CHANGES_REQUESTED")
        ]
    )
    assert view["reviewDecision"] == ""  # documents the fixture; see the docstring

    report = pr_watch.build_report(
        view, [], set(), review_receipt=receipt, **_settled(view)
    )

    assert report["mergeable"] is False
    assert report["done"] is False  # the legacy alias tightens in lockstep
    assert (
        "configured review bot requested changes on current head: coderabbit"
        in report["merge_blockers"]
    )
    # The receipt itself is still VALID and still says so — the objection
    # outranks it rather than invalidating it. Reporting it as missing evidence
    # would misdescribe why the merge is refused.
    assert report["review_evidence"]["valid"] is True
    assert report["review_evidence"]["route"] == "receipt"

    # The no-receipt case was already refused by `qualifying_bot_coverage`, but
    # for the WRONG REASON — "evidence is missing" rather than "the reviewer
    # objected". Both blockers now stand, so the report names the objection
    # whether or not a receipt exists.
    no_receipt = pr_watch.build_report(view, [], set(), **_settled(view))
    assert no_receipt["mergeable"] is False
    assert (
        "configured review bot requested changes on current head: coderabbit"
        in no_receipt["merge_blockers"]
    )
    assert (
        "independent review evidence is missing for current head"
        in no_receipt["merge_blockers"]
    )


def test_a_bots_own_later_non_verdict_review_cannot_clear_its_objection() -> None:
    """Issue #494 — the third clearance route, which was neither fix nor dismissal.

    Found by an adversarial fallback-panel lens during an adopter `/upgrade`, then
    reproduced at the cockpit before being acted on.

    The shape the suite had never built: **two reviews from one bot at one head.**
    Every other `objecting_bot_coverage` / `qualifying_bot_coverage` test builds a
    single coverage entry or a single review, so the displacement path was
    asserted in prose and pinned by nothing.

    What it did. `bot_review_coverage` reduces to one entry per bot,
    latest-timestamp-wins *regardless of state*, and the objection read was
    computed from that survivor — so an ordinary follow-up `COMMENTED` at the same
    head did not outrank the earlier `CHANGES_REQUESTED`, it removed it from the
    structure the blocker was computed from. Two blockers became zero. Worse, since
    `COMMENTED` is evidential, that same review then *supplied* the
    independent-review evidence, so the gate went from refusing twice to
    authorizing.

    Why it mattered more than the state it replaced: #488 ships with no override
    flag, justified by its only two escape routes — push a fix, or have a
    maintainer dismiss — both leaving a forge audit trail. This third route leaves
    none, requires no human act, and the bot walks into it by itself. It was also a
    regression against the pre-#484 world on that path, where merging over a
    standing objection took a deliberate `--record-review`.
    """
    pr_watch = _load_pr_watch()
    objection = _review(
        "coderabbitai", "abc123", "2026-07-25T12:00:00Z", "CHANGES_REQUESTED"
    )

    # The bypass, as filed: same bot, same head, later timestamp, no verdict.
    view = _green_view(
        reviews=[
            objection,
            _review("coderabbitai", "abc123", "2026-07-25T12:30:00Z", "COMMENTED"),
        ]
    )
    report = pr_watch.build_report(view, [], set(), **_settled(view))

    assert report["mergeable"] is False
    assert (
        "configured review bot requested changes on current head: coderabbit"
        in report["merge_blockers"]
    )
    # `PENDING` is the other non-verdict state, and an unrecognized one stands in
    # for anything GitHub adds later — the reason `_VERDICT_REVIEW_STATES` is an
    # allowlist rather than a denylist of the two states known today.
    for benign in ("PENDING", "COMMENTED", "", "WAT"):
        moved = _green_view(
            reviews=[
                objection,
                _review("coderabbitai", "abc123", "2026-07-25T12:30:00Z", benign),
            ]
        )
        assert pr_watch.objecting_bot_coverage(
            pr_watch.build_report(moved, [], set(), **_settled(moved))["review_bots"],
            "abc123",
        ) == ["coderabbit"], benign

    # The release valves that MUST still clear it, or the fix is a wedge. Both
    # leave the forge audit trail #488's no-override-flag argument rests on.
    #
    # They clear the OBJECTION identically and land differently, which is the
    # distinction worth pinning rather than smoothing over: `APPROVED` is also
    # evidence, `DISMISSED` is deliberately not (it is absent from
    # `_EVIDENTIAL_REVIEW_STATES`), so a dismissal withdraws the refusal without
    # supplying a review. That leaves the ordinary receipt requirement standing,
    # which is the correct outcome and not a residue of this fix.
    for verdict, still_blocked in (("APPROVED", False), ("DISMISSED", True)):
        cleared = _green_view(
            reviews=[
                objection,
                _review("coderabbitai", "abc123", "2026-07-25T12:30:00Z", verdict),
            ]
        )
        cleared_report = pr_watch.build_report(cleared, [], set(), **_settled(cleared))
        assert (
            "configured review bot requested changes on current head: coderabbit"
            not in cleared_report["merge_blockers"]
        ), verdict
        assert cleared_report["mergeable"] is not still_blocked, verdict
        assert (
            "independent review evidence is missing for current head"
            in cleared_report["merge_blockers"]
        ) is still_blocked, verdict

    # And the evidence route is untouched: a bot's ordinary clean review is
    # `COMMENTED`, so a rule that let a verdict outrank it *for coverage* would
    # have broken #350 in its commonest shape. `coverage` still reports the
    # newest review whatever it says; only `objections` filters.
    assert report["review_bots"]["coverage"][0]["state"] == "COMMENTED"
    assert report["review_bots"]["objections"][0]["state"] == "CHANGES_REQUESTED"
    assert report["review_evidence"]["route"] == "bot-coverage"


def test_a_comment_borne_verdict_is_reported_and_never_becomes_evidence() -> None:
    """Issue #44, ruled 2026-08-17: report it, never gate on it.

    A reviewer that delivers a clean verdict as an issue comment creates no
    review object, so `coverage` is empty and a reviewed PR looks exactly like an
    unreviewed one. This surfaces that as `comment_verdicts` — and the assertion
    that matters most is the NEGATIVE one: `mergeable` stays false and
    `review_evidence` stays invalid. If a future change wires this into the
    gate, the prose match starts deciding merges, which `bot_review_coverage`'s
    docstring is the standing argument against.
    """
    pr_watch = _load_pr_watch()
    head = "abc123"
    verdict = {
        "author": {"login": "coderabbitai"},
        "body": (
            "**Actionable comments posted: 0**\n\n"
            "No actionable comments were generated in the recent review.\n\n"
            f"Reviewing files that changed between 0ldbase and {head}."
        ),
    }
    view = _green_view(comments=[verdict])
    report = pr_watch.build_report(view, [], set(), **_settled(view))

    assert report["review_bots"]["comment_verdicts"] == [
        {"bot": "coderabbit", "sha": head}
    ]
    # The whole ruling: reported above, and gating on nothing below.
    assert report["review_evidence"]["valid"] is False
    assert report["review_evidence"]["route"] is None
    assert report["mergeable"] is False
    assert (
        "independent review evidence is missing for current head"
        in report["merge_blockers"]
    )

    # The line a human actually reads — this feature's entire user-visible
    # output, and the reason it exists at all. Asserted on `render`, not just on
    # the report dict: deleting the whole render block passed all 252 tests,
    # which made "the operator is told" a claim the suite did not check. It also
    # pins the remedy text, because a report that names the state without naming
    # the next command is the half of this that is not useful.
    rendered = pr_watch.render(report)
    assert "review reported" in rendered
    assert head[:7] in rendered
    assert 'coderabbit:comment-verdict' in rendered

    # …and the suppression branch: once the bot's own review OBJECT covers this
    # head, the comment adds nothing and the line would be noise on every poll.
    # Its own case, because an inverted `covered` check still passes everything
    # above.
    with_object = _green_view(
        comments=[verdict],
        reviews=[_review("coderabbitai", head, "2026-07-25T12:00:00Z")],
    )
    covered_report = pr_watch.build_report(
        with_object, [], set(), **_settled(with_object)
    )
    assert covered_report["review_bots"]["comment_verdicts"] == [
        {"bot": "coderabbit", "sha": head}
    ]
    assert "review reported" not in pr_watch.render(covered_report)


def test_a_converged_head_with_no_reviewer_coverage_says_the_review_is_owed(
    monkeypatch,
) -> None:
    """#518 — the state `#516` merged in, on the surface that is actually read.

    On `#516` the check-surface panel branch fired on the first poll, its
    receipt made `mergeable` true before the loop had converged, and the
    Converged step's unconditional "request a review" bullet was never
    revisited: the PR merged with `gh pr view 516 --json reviews` returning
    `[]`. Every value in that report was correct, which is the point — a report
    says what happened, and nothing in it said the reviewer had never been
    asked.

    The assertion that matters most is the RECEIPT one. A valid `fallback:panel`
    receipt satisfies `mergeable`, and silencing this line there would reproduce
    `#516` exactly, one layer down: the substitute standing in for having asked.
    """
    pr_watch = _load_pr_watch()
    view = _green_view()

    report = pr_watch.build_report(view, [], set(), **_settled(view))
    assert report["converged"] is True
    assert report["review_bots"]["coverage"] == []
    rendered = pr_watch.render(report)
    assert "review owed" in rendered
    # It names WHICH reviewer is owed. A reader who has to work that out is
    # being handed the question rather than the answer.
    assert "coderabbit has not reviewed it" in rendered

    # #516's own state, and the reason the line exists at all.
    receipt = {"head": "abc123", "source": "fallback:panel"}
    with_receipt = pr_watch.build_report(
        view, [], set(), review_receipt=receipt, **_settled(view)
    )
    assert with_receipt["mergeable"] is True, "the panel receipt still authorizes"
    assert "review owed" in pr_watch.render(with_receipt)

    # Suppression 1 — the bot's own review of this head. It looked.
    covered_view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )
    covered = pr_watch.build_report(
        covered_view, [], set(), **_settled(covered_view)
    )
    assert "review owed" not in pr_watch.render(covered)

    # Suppression 2 — a head that is still moving. Convergence is when the
    # merge head stops moving and the request becomes worth spending; before it
    # this would fire on every poll of the healthy window and be skimmed past,
    # which is how a warning stops working.
    failing = _green_view(
        statusCheckRollup=[
            {"name": "tests", "status": "COMPLETED", "conclusion": "FAILURE"}
        ]
    )
    not_converged = pr_watch.build_report(failing, [], set(), **_settled(failing))
    assert not_converged["converged"] is False
    assert "review owed" not in pr_watch.render(not_converged)

    # Suppression 3 — the reviewer answered in a COMMENT and created no review
    # object (#44). It looked; the `ⓘ review reported:` line above already
    # carries that state and its own remedy, and saying "nobody reviewed this"
    # over the top of it would be false.
    #
    # The comment has to be ACKED for this report to converge at all — an
    # unseen comment is un-clean by definition. That is not fixture ceremony:
    # it is why this case cannot live in the comment-verdict test next door,
    # whose reports are both unconverged and where an assertion about this line
    # would pass no matter what the guard did.
    verdict = {
        "id": "IC_verdict",
        "author": {"login": "coderabbitai"},
        "body": (
            "**Actionable comments posted: 0**\n\n"
            "No actionable comments were generated in the recent review.\n\n"
            "Reviewing files that changed between 0ldbase and abc123."
        ),
    }
    verdict_view = _green_view(comments=[verdict])
    unacked = pr_watch.build_report(
        verdict_view, [], set(), **_settled(verdict_view)
    )
    acked = pr_watch.build_report(
        verdict_view,
        [],
        set(unacked["all_comment_keys"]),
        **_settled(verdict_view),
    )
    assert acked["converged"] is True
    assert acked["review_bots"]["comment_verdicts"] == [
        {"bot": "coderabbit", "sha": "abc123"}
    ]
    assert "review reported" in pr_watch.render(acked)
    assert "review owed" not in pr_watch.render(acked)

    # Suppression 4 — a bot MID-REVIEW. A verdict is coming; "request one now"
    # would spend a second unit on a review already in flight.
    reviewing_view = _green_view()
    reviewing = pr_watch.build_report(
        reviewing_view,
        [],
        set(),
        check_details=pr_watch.CheckDetails(
            [
                _bot_check(
                    state="PENDING", bucket="pending", startedAt=_minutes_ago(2)
                )
            ],
            "ok",
        ),
        now=NOW,
        **_settled(reviewing_view, now=NOW),
    )
    assert [e for e in reviewing["review_bots"]["pending"] if e["blocking"]]
    assert "review owed" not in pr_watch.render(reviewing)

    # Suppression 5 — the review-bot READ failed. The hedge line above already
    # says reviewer state could not be read this poll; an absolute underneath it
    # retracts that hedge instead of qualifying it.
    unread_view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T11:30:00Z", "APPROVED")]
    )
    unread = pr_watch.build_report(
        unread_view,
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "unavailable"),
        **_settled(unread_view),
    )
    assert unread["review_bots"]["signal"] == "unavailable"
    assert "could not be read" in pr_watch.render(unread)
    assert "review owed" not in pr_watch.render(unread)

    # Suppression 6 — a standing `CHANGES_REQUESTED` on this exact head. The
    # reviewer plainly reviewed; `qualifying_bot_coverage` excludes this state
    # DELIBERATELY, for the gate. Reading the gate predicate here made the line
    # claim nobody had reviewed the diff, printed directly beside the engine's
    # own `requested changes on current head` blocker — and prescribed
    # requesting a review when addressing the objection is the next step.
    objected_view = _green_view(
        reviews=[
            _review(
                "coderabbitai", "abc123", "2026-07-25T11:30:00Z", "CHANGES_REQUESTED"
            )
        ]
    )
    objected = pr_watch.build_report(
        objected_view, [], set(), **_settled(objected_view)
    )
    assert pr_watch.qualifying_bot_coverage(
        objected["review_bots"], objected["head"]
    ) == [], "the gate predicate still refuses it — that part is correct"
    assert objected["review_bots"]["coverage"][0]["covers_head"] is True
    assert "review owed" not in pr_watch.render(objected)

    # …and the positive case that separates "nobody looked" from "the gate
    # cannot vouch for it": a bot BEHIND the head genuinely has not reviewed
    # this diff, so the line still fires.
    behind_view = _green_view(
        reviews=[_review("coderabbitai", "0ldsha", "2026-07-25T11:30:00Z", "APPROVED")]
    )
    behind = pr_watch.build_report(behind_view, [], set(), **_settled(behind_view))
    assert behind["review_bots"]["coverage"][0]["covers_head"] is False
    assert "review owed" in pr_watch.render(behind)

    # Suppression 7 — the read failed AND nothing is known. This is the case
    # that isolates the `signal` term: every other suppression here also has
    # coverage, so `unreviewed` would empty first and the term would be pinned
    # by nothing. (It survived a mutation sweep for exactly that reason.)
    blind_view = _green_view()
    blind = pr_watch.build_report(
        blind_view,
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "unavailable"),
        **_settled(blind_view),
    )
    assert blind["review_bots"]["signal"] == "unavailable"
    assert blind["review_bots"]["coverage"] == [], "nothing is known either way"
    assert "could not be read" in pr_watch.render(blind)
    assert "review owed" not in pr_watch.render(blind)

    # Suppression 8 — TWO bots configured, one of which answered. A blanket
    # "some verdict exists" test let the answering bot speak for the silent one,
    # which is this line's own failure mode one bot over. The line must still
    # fire, and must name the bot that was never asked.
    monkeypatch.setattr(pr_watch, "_REVIEW_BOTS", ("coderabbit", "otherbot"))
    two_bot_view = _green_view(
        comments=[
            {
                "id": "IC_two_bot",
                "author": {"login": "coderabbitai"},
                "body": (
                    "**Actionable comments posted: 0**\n\n"
                    "No actionable comments were generated in the recent "
                    "review.\n\nReviewing files that changed between 0ldbase "
                    "and abc123."
                ),
            }
        ]
    )
    two_bot_first = pr_watch.build_report(
        two_bot_view, [], set(), **_settled(two_bot_view)
    )
    two_bot = pr_watch.build_report(
        two_bot_view,
        [],
        set(two_bot_first["all_comment_keys"]),
        **_settled(two_bot_view),
    )
    assert two_bot["converged"] is True
    assert [e["bot"] for e in two_bot["review_bots"]["comment_verdicts"]] == [
        "coderabbit"
    ]
    two_bot_rendered = pr_watch.render(two_bot)
    assert "review owed" in two_bot_rendered
    assert "otherbot has not reviewed it" in two_bot_rendered
    assert "coderabbit has not" not in two_bot_rendered, "it answered; do not name it"

    # Suppression 9 — no reviewer configured. `signal: skipped` means there is
    # nobody to ask, so the line would name an action that does not exist.
    monkeypatch.setattr(pr_watch, "_REVIEW_BOTS", ())
    unconfigured = pr_watch.build_report(view, [], set(), **_settled(view))
    assert unconfigured["review_bots"]["signal"] == "skipped"
    assert "review owed" not in pr_watch.render(unconfigured)


def test_a_rate_limited_bot_naming_the_range_it_would_have_reviewed_is_not_a_verdict() -> None:
    """The #263 fail-open, which is why the read is a conjunction.

    A rate-limited CodeRabbit posted ONE comment carrying both "Review limit
    reached … we couldn't start this review" and the `Reviewing files that
    changed between <base> and <head>` line — the range it *would have* covered.
    `GET /pulls/263/reviews` was empty; no review happened. A rule keyed on the
    SHA and a completion marker without the unavailable term would manufacture a
    verdict there, which is worse than reporting nothing.

    Also pins the other two terms, neither of which has a failing case otherwise:
    a lookalike login cannot announce that the reviewer passed, and a comment
    that never names this head is not about this head.
    """
    pr_watch = _load_pr_watch()
    head = "abc123"

    rate_limited = {
        "author": {"login": "coderabbitai"},
        "body": (
            "**Review limit reached**\n\n"
            "@topij, you've reached your PR review limit, so we couldn't start "
            "this review.\n\n"
            "Actionable comments posted: 0\n"
            f"Reviewing files that changed between 0ldbase and {head}."
        ),
    }
    assert pr_watch.bot_comment_verdicts([rate_limited], head) == []

    clean_body = (
        f"No actionable comments were generated in the recent review. {head}"
    )
    # A lookalike login — the anchored match, same reason `bot_review_coverage`
    # anchors: a comment author is not the repo's to control.
    assert (
        pr_watch.bot_comment_verdicts(
            [{"author": {"login": "xcoderabbit"}, "body": clean_body}], head
        )
        == []
    )
    # A verdict that never names this head. The containment test is what makes
    # this fail toward silence rather than toward a wrong sha.
    assert (
        pr_watch.bot_comment_verdicts(
            [
                {
                    "author": {"login": "coderabbitai"},
                    "body": "No actionable comments were generated in the recent review.",
                }
            ],
            head,
        )
        == []
    )
    # A bot comment that names this head but announces no completed review.
    # This is the term the other refusals do NOT reach: each of them fails on a
    # different clause, so without this case dropping the completion check
    # entirely passed the whole suite — every comment a bot ever posts about
    # this head would have become a verdict, including a walkthrough or a
    # progress note. Found by mutation, not by reading.
    assert (
        pr_watch.bot_comment_verdicts(
            [
                {
                    "author": {"login": "coderabbitai"},
                    "body": f"Walkthrough\n\nReviewing files that changed between 0ldbase and {head}.",
                }
            ],
            head,
        )
        == []
    )
    # …and the positive control, so the refusals above are readable as
    # refusals rather than as a function that never returns anything.
    assert pr_watch.bot_comment_verdicts(
        [{"author": {"login": "coderabbitai"}, "body": clean_body}], head
    ) == [{"bot": "coderabbit", "sha": head}]
    # No head to bind to, and a non-configured bot.
    assert pr_watch.bot_comment_verdicts([{"author": {"login": "coderabbitai"}, "body": clean_body}], "") == []
    assert (
        pr_watch.bot_comment_verdicts(
            [{"author": {"login": "coderabbitai"}, "body": clean_body}],
            head,
            bots=("otherbot",),
        )
        == []
    )


def test_a_bot_objection_clears_by_pushing_a_fix_rather_than_wedging() -> None:
    """The anti-wedge property of #485's blocker, which is the whole reason it
    can ship without an override flag.

    The blocker is bound to `head`. The ordinary remediation for "changes
    requested" is to push the fix — which moves the head, leaves the objection
    covering an older commit, and clears the blocker with no flag, no dismissal,
    and no special case. A blocker that did NOT clear this way would be the wedge
    this engine's design refuses, and would have forced an escape hatch on the
    merge gate to compensate.

    The first half is also the state the ordering a record-time refusal would
    miss (#485 direction 1) resolves to: a receipt taken while the bot was
    rate-limited, then the bot recovering and objecting at that same head. Note
    what this does and does NOT establish — `build_report` reads the final state
    and has no view of arrival order, so no test here can replay the sequence.
    What it pins is that the gate's answer does not DEPEND on the ordering, which
    is the property that makes a merge-time check cover both and a record-time
    one cover only the objection-first case.
    """
    pr_watch = _load_pr_watch()

    # The bot objected at `abc123`, and the receipt was taken there too.
    objection = _review(
        "coderabbitai", "abc123", "2026-07-25T12:00:00Z", "CHANGES_REQUESTED"
    )
    blocked = _green_view(reviews=[objection])
    report = pr_watch.build_report(
        blocked,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(blocked),
    )
    assert report["mergeable"] is False

    # Push the fix: the head moves, and a fresh receipt is taken against it. The
    # objection now covers an older commit, so it no longer speaks for this one.
    pushed = _green_view(headRefOid="d3adb33f", reviews=[objection])
    after = pr_watch.build_report(
        pushed,
        [],
        set(),
        review_receipt={"head": "d3adb33f", "source": "fallback:panel"},
        **_settled(pushed),
    )
    assert after["mergeable"] is True
    assert after["merge_blockers"] == []
    # …and the stale objection is still REPORTED as coverage of the older commit,
    # so nothing is hidden by the blocker clearing.
    assert after["review_bots"]["coverage"][0]["covers_head"] is False
    assert after["review_bots"]["coverage"][0]["sha"] == "abc123"


def test_only_a_real_objection_blocks_not_every_non_evidential_state() -> None:
    """The set of objecting states is explicit, NOT the complement of the
    evidential one — and this is what pins that they are built differently.

    `_EVIDENTIAL_REVIEW_STATES` is an allowlist so an unknown state cannot open
    the gate. `_OBJECTING_REVIEW_STATES` is an explicit set so an unknown state
    cannot *close* it. Inverting the second into "everything that is not
    evidence" would raise a permanent blocker for `PENDING` (a draft the bot has
    not submitted), for `""` (a `gh` too old to emit the field), and for any
    state GitHub adds later — none of which is anyone objecting, and none of
    which clears without a push.

    So each state below is checked for the ABSENCE of the objection blocker
    while a valid receipt carries the merge. `DISMISSED` is the case that matters
    most: it is how a maintainer retracts an objection, and a gate that kept
    blocking after a dismissal would disagree with `_rest_review_decision`, which
    already honours dismissal one function away.
    """
    pr_watch = _load_pr_watch()

    for state in ("DISMISSED", "PENDING", "", "SOME_FUTURE_STATE"):
        view = _green_view(
            reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z", state)]
        )
        report = pr_watch.build_report(
            view,
            [],
            set(),
            review_receipt={"head": "abc123", "source": "fallback:panel"},
            **_settled(view),
        )
        assert not [
            b for b in report["merge_blockers"] if "requested changes" in b
        ], state
        # None of these is evidence either — the receipt is what carries the
        # merge here, which is the pre-#485 behaviour left deliberately intact.
        assert report["review_evidence"]["route"] == "receipt", state
        assert report["mergeable"] is True, state

    # A review with no `state` key at all, the shape an older `gh` would emit.
    stateless = _review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")
    stateless.pop("state")
    view = _green_view(reviews=[stateless])
    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )
    assert report["mergeable"] is True
    assert report["merge_blockers"] == []


def test_the_objection_read_pins_both_clauses_and_ignores_a_failed_check_read() -> None:
    """Direct unit calls on `objecting_bot_coverage`, for the three properties an
    end-to-end test cannot reach.

    1. The `covers_head is True` / `sha == head` pair, both clauses. Same #447
       shape as its sibling: `bot_review_coverage` derives one from the other, so
       neither clause can fail end-to-end and dropping either survives the rest
       of the suite. A truthy-non-`True` value is what distinguishes identity
       from truthiness (#486, pinned for this copy at the moment it is written
       rather than left for a later ticket).

    2. That the blocker does NOT gate on `signal`, where `qualifying_bot_coverage`
       does. The asymmetry is deliberate and fails closed on each side: `signal`
       describes the CHECK read, while this coverage comes from the `pr view`
       review objects, which are there whether or not that read succeeded.
       Declining to raise a blocker because a different read failed is the
       fail-open — so an `unavailable` signal must still block.

    3. That a lookalike login cannot manufacture an objection either. The
       matching is `_reduce_latest_bot_reviews`'s anchored one, so this is
       inherited rather than added — but the gate now has a second reason to
       care: a false objection is a denial-of-merge, the mirror of #350's false
       evidence.

    Reads `review_bots["objections"]`, not `["coverage"]` (#494). The clause
    structure below is byte-for-byte the property set it pinned against coverage;
    only the reduction it is applied to changed, which is exactly the fix.
    """
    pr_watch = _load_pr_watch()
    objection = {
        "bot": "coderabbit",
        "sha": "abc123",
        "covers_head": True,
        "submitted_at": "2026-07-25T12:00:00Z",
        "state": "CHANGES_REQUESTED",
    }

    assert pr_watch.objecting_bot_coverage(
        {"signal": "ok", "objections": [objection]}, "abc123"
    ) == ["coderabbit"]

    # Clause 1a — `sha` disagrees with the head being authorized.
    assert (
        pr_watch.objecting_bot_coverage(
            {"signal": "ok", "objections": [dict(objection, sha="0ldc0de")]}, "abc123"
        )
        == []
    )
    # Clause 1b — `covers_head` false, and the truthy-non-`True` values that
    # separate `is True` from a bare truthiness test.
    for bad in (False, 1, "yes", {"covered": True}):
        assert (
            pr_watch.objecting_bot_coverage(
                {"signal": "ok", "objections": [dict(objection, covers_head=bad)]},
                "abc123",
            )
            == []
        ), bad
    absent = {"signal": "ok", "objections": [dict(objection)]}
    absent["objections"][0].pop("covers_head")
    assert pr_watch.objecting_bot_coverage(absent, "abc123") == []

    # 2 — a failed or skipped CHECK read does not suppress the objection.
    for signal in ("unavailable", "skipped", "ok"):
        assert pr_watch.objecting_bot_coverage(
            {"signal": signal, "objections": [objection]}, "abc123"
        ) == ["coderabbit"], signal

    # …and with no head to bind to there is nothing to object to.
    assert pr_watch.objecting_bot_coverage({"signal": "ok", "objections": [objection]}, "") == []
    assert (
        pr_watch.objecting_bot_coverage({"signal": "ok", "objections": [objection]}, None)
        == []
    )

    # 3 — end-to-end, an impostor's CHANGES_REQUESTED reaches neither the
    # coverage list nor the blocker.
    view = _green_view(
        reviews=[
            _review(
                "coderabbit-shim", "abc123", "2026-07-25T12:00:00Z", "CHANGES_REQUESTED"
            )
        ]
    )
    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )
    assert report["review_bots"]["coverage"] == []
    assert report["merge_blockers"] == []
    assert report["mergeable"] is True


def test_a_lookalike_login_cannot_manufacture_merge_evidence() -> None:
    """The trust boundary direction 1 now rests on, pinned at the gate.

    On a public repo any account may open a PR and review it. Coverage matching
    is ANCHORED (`_match_bot(..., anchored=True)`: exact normalized login, its
    `[bot]` form, or an explicitly enumerated alias) — the rule #95 established
    for author-controlled input, precisely so a lookalike cannot speak for the
    reviewer.

    That was already true, and was already load-bearing for comment authorship.
    #350 makes it load-bearing for the MERGE GATE too, so it gets a test that
    fails at the gate rather than only at the matcher: a substring impostor must
    not be able to authorize its own merge.
    """
    pr_watch = _load_pr_watch()
    for impostor in ("coderabbitai-impostor", "not-coderabbit", "coderabbit-shim"):
        view = _green_view(
            reviews=[_review(impostor, "abc123", "2026-07-25T12:00:00Z")]
        )
        report = pr_watch.build_report(view, [], set(), **_settled(view))

        assert report["review_bots"]["coverage"] == [], impostor
        assert report["review_evidence"]["valid"] is False, impostor
        assert report["review_evidence"]["bots"] == [], impostor
        assert report["mergeable"] is False, impostor

    # …and the real identity, plus its conventional `[bot]` spelling, do qualify —
    # so this pins anchoring, not a blanket refusal.
    for genuine in ("coderabbitai", "coderabbitai[bot]"):
        view = _green_view(
            reviews=[_review(genuine, "abc123", "2026-07-25T12:00:00Z")]
        )
        report = pr_watch.build_report(view, [], set(), **_settled(view))
        assert report["review_evidence"]["route"] == "bot-coverage", genuine
        assert report["mergeable"] is True, genuine


def test_an_unreadable_bot_signal_never_opens_the_gate() -> None:
    """The fail-closed case, and the one worth being loudest about.

    On `signal == "unavailable"` the bot-state read FAILED, so both of
    `summarize_review_bots`'s guards are already off. A failed read must not
    also be allowed to authorize a merge — that is the shape of #23, where a
    rate-limited bot read as a clean one, arriving at the gate that decides a PR
    is safe to merge.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "unavailable"),
        **_settled(view),
    )

    # The review objects say the head WAS reviewed, and the gate still refuses,
    # because the state that would qualify it could not be read.
    assert report["review_bots"]["signal"] == "unavailable"
    assert report["review_evidence"]["valid"] is False
    assert report["review_evidence"]["route"] is None
    assert report["mergeable"] is False


def test_with_no_configured_bots_the_receipt_is_the_only_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An adopter running `review.bots: []` is unaffected by direction 1: there
    is no reviewer whose coverage could stand in, so the receipt requirement is
    exactly what it was, and the fallback panel is simply their reviewer."""
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REVIEW_BOTS", ())
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )

    without = pr_watch.build_report(view, [], set(), **_settled(view))
    assert without["review_bots"]["signal"] == "skipped"
    assert without["review_evidence"]["valid"] is False
    assert without["mergeable"] is False

    with_receipt = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        **_settled(view),
    )
    assert with_receipt["review_evidence"]["route"] == "receipt"
    assert with_receipt["mergeable"] is True


def test_the_receipt_is_labelled_when_both_routes_hold() -> None:
    """`route` names the claim someone actively MADE, but the coverage is the
    sturdier of the two and is not hidden by that precedence — a reader weighing
    a one-lens receipt deserves to know the bot saw this exact head too."""
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={
            "head": "abc123",
            "source": "fallback:panel",
            "lenses": ["adversarial"],
        },
        **_settled(view),
    )

    assert report["review_evidence"]["route"] == "receipt"
    assert report["review_evidence"]["source"] == "fallback:panel"
    assert report["review_evidence"]["bots"] == ["coderabbit"]
    rendered = pr_watch.render(report)
    assert "ONE lens claimed" in rendered  # the receipt caveat still fires
    assert "also reviewed this head" in rendered


def test_a_pending_bot_still_blocks_a_merge_its_coverage_would_allow() -> None:
    """Direction 1 can only ever ADD evidence to a PR that is otherwise already
    clear. It deliberately does not re-check what blocks on its own path — a
    second copy of a rule is a second thing to go stale — so #19's grace window
    keeps its authority over a bot that has coverage AND a pending check."""
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )

    report = pr_watch.build_report(
        view,
        [],
        set(),
        check_details=[
            {"name": "CodeRabbit", "status": "IN_PROGRESS", "conclusion": ""}
        ],
        **_settled(view),
    )

    # The evidence route is satisfied…
    assert report["review_evidence"]["route"] == "bot-coverage"
    # …and the merge is still refused, by the pending bot's own blocker.
    assert report["mergeable"] is False
    assert any("has not reported yet" in b for b in report["merge_blockers"])


def test_the_merge_wrapper_reads_a_coverage_route_report_as_mergeable() -> None:
    """`safety-critical-changes.md` rule 4, applied to a merge gate.

    Unit tests on `decide_mergeable` are insufficient by that rule: the thing
    that actually authorizes a merge is `dev_session.sh merge`, which shells out
    to `pr_watch.py --json` and tests the parsed value with an IDENTITY check
    (`d.get("mergeable") is True`). A truthy non-bool would fail that check
    closed but confusingly, and nothing at the Python level would notice —
    `decide_mergeable`'s own docstring names this hazard.

    So this exercises the real path: the report is serialized exactly as
    `--json` emits it, and the extraction is READ OUT OF `dev_session.sh` rather
    than restated here, so a change to the wrapper's parsing cannot drift away
    from this test silently.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(
        reviews=[_review("coderabbitai", "abc123", "2026-07-25T12:00:00Z")]
    )
    report = pr_watch.build_report(view, [], set(), **_settled(view))
    assert report["review_evidence"]["route"] == "bot-coverage"

    wrapper = (REPO_ROOT / "scripts" / "dev_session.sh").read_text()
    # Selected by CONTENT, not position: `dev_session.sh` embeds several
    # `python3 -c` blocks and the merge gate's is not the first. Indexing them
    # would silently re-point this test at another block the day one is added
    # above it — which is how a gate test starts asserting about `nameWithOwner`.
    blocks = [
        block
        for block in re.findall(r"python3 -c '\n(import json, sys\n.*?)'", wrapper, re.S)
        if "mergeable" in block
    ]
    assert len(blocks) == 1, (
        "expected exactly one merge-gate extraction in dev_session.sh, "
        f"found {len(blocks)} — re-point this test"
    )

    proc = subprocess.run(
        [sys.executable, "-c", blocks[0]],
        input=json.dumps(report),
        capture_output=True,
        text=True,
        check=True,
    )
    mergeable, validated_pr, validated_base, validated_head = proc.stdout.rstrip(
        "\n"
    ).split("\t")

    # The literal the wrapper compares against, and the identity check behind it.
    assert mergeable == "true"
    assert validated_pr == "7"
    assert validated_base == "trunk"
    assert validated_head == "abc123"


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
    scoped and unscoped are identical.

    **Covers `objections` as well as `coverage`, and that is the point** (#494).
    This test pinned only `coverage` when it was written, so the identical
    threading on the `objections` field added beside it was again correct and
    pinned by nothing: mutating it to `bots=None` passed all 250 tests. That is
    the `#447` shape the `_reduce_latest_bot_reviews` docstring names — a pinned
    copy of a reduction beside an unpinned one — recurring in the field whose
    read is the merge gate's refusal side. Assert on both, or the next field
    added here inherits the same gap.
    """
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

    # The `objections` half needs its own fixture rather than reusing the one
    # above, and the reason is the property under test one layer down: `_review`
    # defaults to `COMMENTED`, which is not a verdict, so the reviews above
    # produce an EMPTY objections list whatever `bots` is — scoped and unscoped
    # alike. Asserting on that would have looked like a scoping pin while
    # actually pinning the verdict filter, and would have passed with the
    # threading dropped.
    verdicts = [
        _review("otherbot", "0ldc0de", "2026-07-25T12:00:00Z", "CHANGES_REQUESTED"),
        _review("coderabbitai", "abc123", "2026-07-25T13:00:00Z", "CHANGES_REQUESTED"),
    ]
    scoped_verdicts = pr_watch.summarize_review_bots(
        [], [], now=NOW, bots=("otherbot",), reviews=verdicts, head="abc123"
    )
    assert [e["bot"] for e in scoped_verdicts["objections"]] == ["otherbot"]
    assert scoped_verdicts["objections"][0]["covers_head"] is False

    # …and a repo with no bots configured gets neither list populated. The
    # objections half matters most: an unconfigured bot's stray
    # CHANGES_REQUESTED reaching this list is a denial-of-merge, the mirror of
    # #350's false evidence.
    assert (
        pr_watch.summarize_review_bots(
            [], [], now=NOW, bots=(), reviews=reviews, head="abc123"
        )["coverage"]
        == []
    )
    assert (
        pr_watch.summarize_review_bots(
            [], [], now=NOW, bots=(), reviews=verdicts, head="abc123"
        )["objections"]
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
        # No `app` on the input run, so no identity to carry — untrusted, which is
        # the fail-closed direction (#95).
        "identity": "",
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


def test_the_rest_identity_read_uses_the_bare_array_reader_for_plural_statuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The #95 identity read must survive the shape of the endpoint it calls.

    Two endpoints one character apart, with different shapes:

      ``commits/{sha}/status``   -> ``{"state": …, "statuses": [...]}``  wrapped
      ``commits/{sha}/statuses`` -> ``[ … ]``                            bare array

    Reading the plural one with `_http_get_all_wrapped` raises ("returned list,
    expected a JSON object"), which `fetch_check_details`'s own handler degrades to
    ``([], "unavailable")`` — **discarding every row**, not just the identities.
    That switches #19's and #23's guards off in precisely the case they exist
    for, an outage-marked row, and `record_review` names that state as the silent
    bypass: no rows means no blockers means no refusal.

    Driven through the real `_http_get` boundary on purpose. The sibling test
    below mocks `_http_get_all_wrapped` itself, so it exercises the reader's
    caller and can never see a shape mismatch — which is why this defect reached
    review with 500+ new test lines already in the diff.
    """
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    # Fragments chosen not to overlap: "/status?" cannot match "/statuses?...",
    # because the plural has an "e" where the singular has "?".
    seen = _route_http(
        pr_watch,
        monkeypatch,
        {
            "check-runs": {
                "total_count": 1,
                "check_runs": [
                    {
                        "name": "toolkit",
                        "status": "completed",
                        "conclusion": "success",
                        "app": {"slug": "github-actions"},
                    }
                ],
            },
            # The #23 shape: the outage announced only as a status description.
            "/status?": {
                "state": "success",
                "statuses": [
                    {
                        "context": "CodeRabbit",
                        "state": "success",
                        "description": "Review rate limited",
                    }
                ],
            },
            # The plural endpoint — a BARE ARRAY, and the only source of `creator`.
            "/statuses?": [
                {
                    "context": "CodeRabbit",
                    "state": "success",
                    "description": "Review rate limited",
                    "created_at": "2026-08-10T12:15:00Z",
                    "id": 51945692384,
                    "creator": {"login": "coderabbitai[bot]", "type": "Bot"},
                }
            ],
            "pulls/5": {"head": {"sha": "abc123"}},
        },
    )

    details = pr_watch.fetch_check_details(5, bots=("coderabbit",))

    # The rows survive at all — this is what the wrong reader destroyed.
    assert details.signal == "ok"
    assert [row["name"] for row in details.rows] == ["toolkit", "CodeRabbit"]
    assert any("/statuses?per_page=100" in url for url in seen), seen

    # …and the genuine outage resolves to the real reviewer, so it still cancels.
    bots = pr_watch.summarize_review_bots(
        details.rows, [], now=NOW, bots=("coderabbit",), signal=details.signal
    )
    outage = [e for e in bots["unavailable"] if e["surface"] == "check"]
    assert outage[0]["identity"] == "coderabbitai[bot]"
    assert outage[0]["trusted"] is True


def test_fetch_check_details_on_rest_returns_rows_with_a_real_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pr_watch = _load_pr_watch()
    _no_gh(pr_watch, monkeypatch)
    _route_http(
        pr_watch,
        monkeypatch,
        {
            # ORDER MATTERS: `_route_http` returns the first fragment that is a
            # substring of the URL, and "commits/abc123/status" is a substring of
            # ".../statuses?per_page=100" too. The plural route must come first or
            # it never wins. This row's check carries an outage marker, so the #95
            # identity read fires and really does request the plural endpoint —
            # which needs its own BARE ARRAY body.
            "commits/abc123/statuses": [],
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


def test_truncation_is_reported_in_the_json_and_the_render(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The adversarial lens: truncation warned on stderr only, so a partial read
    reached `dev_session.sh merge` as `converged: true` with no trace.
    Note what this does NOT claim: `dev_session.sh merge` reads only
    `mergeable`/`pr`/`base`/`head`, so nothing in the repo consumes this key. It is
    in the JSON for a caller that wants it and printed by `render` for a human;
    the earlier name of this test asserted a merge-gate consumer that does not
    exist.

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

    view = _green_view(headRefOid="abc123")
    report = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel", "lenses": ["adversarial", "correctness"]},
        check_details=pr_watch.CheckDetails([], "skipped"),
        **_settled(view),
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

    message = pr_watch._REST_POLL_ONLY_BLOCKER
    # "polls only", not "read-only": the engine does write its own watch state, so
    # the stronger word was inaccurate on the surface an operator reads.
    assert "polls only" in message
    assert "read-only" not in message
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

    # An ABSENT key is rejected: GitHub always returns the wrapper key, so its
    # absence means an error payload with a 200 status. Treating it as "no checks"
    # dropped a whole surface — a real failing status context vanished and
    # `all_green` went true, with no warning at all.
    monkeypatch.setattr(pr_watch, "_http_get", lambda url, token, **_kw: ({"message": "Bad credentials"}, None))
    with pytest.raises(RuntimeError, match="returned no 'check_runs' key"):
        pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs")
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"check_runs": None}, None)
    )
    with pytest.raises(RuntimeError, match="expected a JSON array"):
        pr_watch._http_get_all_wrapped("https://api.github.com/cr", "t", "check_runs")

    # An empty LIST is legal — a commit with no checks is a real state.
    monkeypatch.setattr(
        pr_watch, "_http_get", lambda url, token, **_kw: ({"total_count": 0, "check_runs": []}, None)
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

    message = pr_watch._REST_POLL_ONLY_BLOCKER
    assert "GraphQL" not in message
    assert "read-only" not in message

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


def test_the_false_settle_guard_is_not_disabled_by_a_missing_state_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replaces a test that pinned a fail-open of my own making.

    A previous round added `comparable_max_total`, which reset `prior_max_total`
    to 0 whenever the state file had no recorded backend — true of every file the
    shipped engine has ever written. That looks conservative and is not: with
    `prior_max_total=0`, `max_total` becomes `checks["total"]`, so
    `checks["total"] < max_total` can never hold. Resetting the baseline can only
    ever REMOVE `settling`, never add it — so upgrading disabled the false-settle
    guard for every existing PR on the DEFAULT `gh` backend and flipped
    `mergeable` from false to true. The mechanism is deleted; this pins the
    property it broke.

    Driven through `main`, deliberately. The deleted test called the helper itself
    and handed the result to `build_report`, so reverting the fix in `main` — the
    only production call site — left the suite green. Third occurrence of that
    shape on this branch.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "resolve_pr", lambda explicit: 9)
    monkeypatch.setattr(
        pr_watch,
        "fetch_pr_view",
        lambda pr: (_green_view(headRefOid="abc123"), []),
    )
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "skipped")
    )
    # A state file exactly as the shipped engine writes it: a baseline, no backend.
    monkeypatch.setattr(
        pr_watch,
        "load_state",
        lambda pr: {"head": "abc123", "max_total": 6, "seen": [], "review_receipt": {
            "head": "abc123", "source": "fallback:panel", "lenses": ["adversarial", "correctness"]}},
    )
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: None)

    captured: list[dict] = []
    real_build = pr_watch.build_report
    monkeypatch.setattr(
        pr_watch,
        "build_report",
        lambda *a, **kw: captured.append(real_build(*a, **kw)) or captured[-1],
    )

    assert pr_watch.main(["9", "--json"]) == 0
    report = captured[0]
    # The rollup has 1 check against a stored baseline of 6, so this poll has NOT
    # seen every check yet — the guard must hold.
    assert report["settling"] is True, "the false-settle guard was disabled"
    assert report["converged"] is False
    assert report["mergeable"] is False


# ------------------------------------------------- the settle baseline (#190/#39)
#
# One guard, two holes. `settling` answers "did the rollup shrink or the head
# move on THIS poll" — a single-poll question, and both issues are about what it
# cannot see. The gate these pin is `merge_blockers`, deliberately: `converged`
# is the watch-loop predicate and blocking it would wedge the loop.


def _settle_state(**overrides) -> dict:
    """A state file mid-watch, with an established settle baseline."""
    state = {
        "head": "abc123",
        "max_total": 1,
        "seen": [],
        "settle_since": {"head": "abc123", "at": _ago_iso(30.0), "total": 1},
        "review_receipt": {
            "head": "abc123",
            "source": "fallback:panel",
            "lenses": ["adversarial", "correctness"],
        },
    }
    state.update(overrides)
    return state


def _poll_via_main(monkeypatch: pytest.MonkeyPatch, pr_watch, state: dict, view: dict):
    """Drive a real `main` poll against `state`, returning the built report.

    Through `main`, not `build_report`: the deleted `comparable_max_total` test
    called its helper directly and stayed green when the production call site was
    reverted. Same shape, third occurrence — so these go through the call site.
    """
    monkeypatch.setattr(pr_watch, "resolve_pr", lambda explicit: 9)
    monkeypatch.setattr(pr_watch, "fetch_pr_view", lambda pr: (view, []))
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails([], "skipped"),
    )
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: dict(state))
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, s: None)

    captured: list[dict] = []
    real_build = pr_watch.build_report
    monkeypatch.setattr(
        pr_watch,
        "build_report",
        lambda *a, **kw: captured.append(real_build(*a, **kw)) or captured[-1],
    )
    assert pr_watch.main(["9", "--json"]) == 0
    return captured[0]


def test_a_lost_state_file_cannot_authorize_a_merge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#190. `load_state` returns {} for a missing, empty OR corrupt file — and a
    FRESH CLONE reaches that with no failed write anywhere, so this is the first
    run, not an error path.

    That drops `head`/`max_total`, and the guard collapses: `head_changed` is
    False (no `prior_head` to differ from), `max_total` becomes `checks["total"]`,
    so `checks["total"] < max_total` can never hold. `settling` is False and a
    partial rollup reads as complete.

    The receipt goes with the same file, so the gate does hold — until the next
    `--record-review`, which merges a receipt back in while `head`/`max_total`
    stay absent. That is the state driven here, and it is row 3 of #190's
    measured table: identical PR, head and rollup to row 1, differing ONLY in
    whether the state file survived, and disagreeing about whether the PR may
    merge with most of its checks unregistered.
    """
    pr_watch = _load_pr_watch()
    report = _poll_via_main(
        monkeypatch,
        pr_watch,
        # Exactly what `--record-review` leaves behind on an emptied file: a
        # receipt for the current head, and no settle baseline of any kind.
        {
            "review_receipt": {
                "head": "abc123",
                "source": "fallback:panel",
                "lenses": ["adversarial", "correctness"],
            }
        },
        _green_view(headRefOid="abc123"),
    )

    assert report["review_evidence"]["valid"] is True, "the receipt is for this head"
    assert report["mergeable"] is False, "a lost baseline authorized a merge (#190)"
    assert report["done"] is False, "the legacy alias fell open"
    assert any(
        "settle" in blocker for blocker in report["merge_blockers"]
    ), report["merge_blockers"]


def test_an_upgrade_from_a_state_file_with_no_settle_stamp_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The upgrade path, and the direction is the whole point.

    Every state file the shipped engine has written carries `head`/`max_total`
    and NO settle stamp. Reading that absence as "settled long ago" would flip
    the gate open for every in-flight PR at the moment of upgrade — which is
    precisely how `comparable_max_total` failed, and it was deleted for it under
    `safety-critical-changes.md` rule 1. Absent must mean "not established yet":
    fail-closed, and self-clearing on the next poll.
    """
    pr_watch = _load_pr_watch()
    state = _settle_state()
    del state["settle_since"]

    report = _poll_via_main(
        monkeypatch, pr_watch, state, _green_view(headRefOid="abc123")
    )

    assert report["mergeable"] is False, "an upgrade opened the gate (comparable_max_total's failure)"
    assert report["done"] is False


def test_the_settle_guard_is_wider_than_the_poll_that_observes_the_push(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#39. The reproduced sequence, re-derived rather than trusted.

    `max_total` resets to the NEW commit's partial count on a head change, so on
    the very next poll `checks["total"] < max_total` is false and `settling`
    drops — while most of the commit's checks have not registered. #39's table
    has poll 2 authorizing the merge at 2 of 5 checks, and poll 3 showing one of
    the missing three would have failed.

    Poll 2 is the row under test: same head as poll 1, same partial count, and
    seconds later.

    The stamp age is varied against a control, because the earlier version of
    this test was blocked for the wrong reason: its stamp carried no `total`, so
    it was rejected as malformed and the assertion below held whatever the age
    was — a stamp 10,000 minutes old passed it just the same.
    """
    pr_watch = _load_pr_watch()
    partial = _green_view(
        headRefOid="newsha",
        statusCheckRollup=[
            {"name": "a", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "b", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    )

    def _poll(stamp_age_minutes: float) -> dict:
        return _poll_via_main(
            monkeypatch,
            pr_watch,
            _settle_state(
                head="newsha",
                max_total=2,
                settle_since={
                    "head": "newsha",
                    "at": _ago_iso(stamp_age_minutes),
                    "total": 2,
                },
                review_receipt={
                    "head": "newsha",
                    "source": "fallback:panel",
                    "lenses": ["adversarial", "correctness"],
                },
            ),
            partial,
        )

    # Poll 1 observed the push 30 seconds ago and recorded 2 of the 5 checks.
    report = _poll(0.5)

    assert report["checks"]["all_green"] is True, "the partial rollup reads green"
    assert report["settling"] is False, (
        "this pins #39's precondition: the one-poll guard has already dropped"
    )
    assert report["mergeable"] is False, "poll 2 authorized a partial rollup (#39)"
    assert report["done"] is False

    # Control: the ONLY thing holding the gate above is the grace, so the same
    # state with an aged stamp must merge. Without this, the assertions above
    # pass for any reason at all.
    assert _poll(pr_watch._SETTLE_GRACE_MINUTES + 5)["mergeable"] is True


def test_the_settle_clock_restarts_when_more_checks_register(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rollup that is still GROWING is not stable, however long ago the head
    was first seen. Without this the clock would age out during registration and
    authorize the merge at the moment the count was still climbing."""
    pr_watch = _load_pr_watch()
    grown = _green_view(
        headRefOid="abc123",
        statusCheckRollup=[
            {"name": "a", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "b", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "c", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    )
    # Baseline is old enough to have aged out, but only 1 check was in it.
    report = _poll_via_main(
        monkeypatch, pr_watch, _settle_state(max_total=1), grown
    )

    assert report["mergeable"] is False, "the gate opened while checks were still arriving"
    assert report["done"] is False


def test_a_stable_rollup_past_the_grace_still_merges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The anti-wedge half, and it is not optional.

    A guard that only ever blocks is a wedge, and this repo has deleted a
    mechanism for being one. The normal path must still authorize: same head,
    same count, stamp older than the grace.
    """
    pr_watch = _load_pr_watch()
    report = _poll_via_main(
        monkeypatch, pr_watch, _settle_state(), _green_view(headRefOid="abc123")
    )

    assert report["converged"] is True
    assert report["mergeable"] is True, "the settle guard wedged a clean PR"
    assert report["done"] is True
    assert report["merge_blockers"] == []


def test_the_settle_guard_never_blocks_the_watch_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`converged` answers "is there more for me to fix?" and must stay
    answerable while the merge gate waits. Blocking it would wedge exactly the
    loop the converged/mergeable split exists to keep runnable — so the guard is
    additive to `merge_blockers` ONLY.
    """
    pr_watch = _load_pr_watch()
    report = _poll_via_main(
        monkeypatch,
        pr_watch,
        # No baseline at all: the most-blocking state the gate has.
        {"review_receipt": {"head": "abc123", "source": "fallback:panel"}},
        _green_view(headRefOid="abc123"),
    )

    assert report["converged"] is True, "the settle guard wedged the watch loop"
    assert report["mergeable"] is False


def test_the_settle_baseline_is_written_to_the_state_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The stamp has to be PERSISTED or the gate can never clear: every poll
    would find no baseline, re-stamp it, and block forever.

    Scoped to the WRITER: that `persist_poll` puts a head-scoped stamp on disk
    and `load_state` reads it back. It was called `..._rides_every_poll`, which
    promised more than one round-trip can show — a lens said so, and the repo has
    a documented pattern of exactly that shape. Whether the value being written
    is the right ANCHOR across polls is
    `test_the_anchor_survives_a_real_poll_sequence`, and the distinction is the
    whole of round 2's HIGH.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)

    report = pr_watch.build_report(
        _green_view(headRefOid="abc123"),
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    state = pr_watch.persist_poll(9, report, set())

    assert state["settle_since"]["head"] == "abc123"
    assert state["settle_since"]["at"], "no stamp was written"
    # And it round-trips through the file, not just the return value.
    assert pr_watch.load_state(9)["settle_since"] == state["settle_since"]


def test_the_anchor_survives_a_real_poll_sequence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The clock must ACCUMULATE across polls, and start when the head was first
    seen — not be re-minted each poll, and not be born already aged.

    Two chained polls through the real `build_report` -> `persist_poll` ->
    `load_state` -> `read_settle_since` path, because that loop is where the
    value's meaning lives and no fixture-injected stamp exercises it. A review
    lens found the whole ternary that decides the persisted anchor survives the
    entire suite mutated in EITHER direction:

    - always re-stamping with `now` makes the age never exceed one poll interval,
      so the gate never opens — the permanent wedge `persist_poll`'s own comment
      warns about, and nothing failed.
    - minting the fresh stamp already backdated by the grace makes poll 2 settle
      30 seconds after a push, which is #39 reopened, and nothing failed.

    `test_the_settle_baseline_is_written_to_the_state_file` does not cover this: it asserts a
    stamp round-trips through the file unchanged, which is a fact about the
    writer, not about whether the value handed to it is the right anchor.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    view = _green_view(headRefOid="abc123")
    receipt = {"head": "abc123", "source": "fallback:panel"}
    first_seen = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    grace = pr_watch._SETTLE_GRACE_MINUTES

    def _poll(now: datetime) -> tuple[dict, dict]:
        state = pr_watch.load_state(9)
        _since, _total = pr_watch.read_settle_since(state, view["headRefOid"])
        report = pr_watch.build_report(
            view,
            [],
            set(),
            review_receipt=receipt,
            check_details=pr_watch.CheckDetails([], "skipped"),
            now=now,
            prior_head=state.get("head"),
            prior_max_total=int(state.get("max_total") or 0),
            prior_settle_since=_since,
            prior_settle_total=_total,
        )
        return report, pr_watch.persist_poll(9, report, set())

    # Poll 1 — nothing on disk. The anchor is minted HERE, at `now`, un-aged.
    first, state1 = _poll(first_seen)
    assert first["mergeable"] is False, "a first poll has no baseline yet"
    assert state1["settle_since"]["at"] == first_seen.isoformat().replace(
        "+00:00", "Z"
    ), "the fresh anchor was not stamped at the moment the head was first seen"

    # Poll 2 — same head, same rollup, past the grace. The anchor must not move.
    later = first_seen + timedelta(minutes=grace + 5)
    second, state2 = _poll(later)
    assert state2["settle_since"] == state1["settle_since"], (
        "the anchor was re-minted, so the clock can never accumulate"
    )
    assert second["settle_age_minutes"] == pytest.approx(grace + 5), (
        "age is measured from the first sighting, not from this poll"
    )
    assert second["rollup_settled"] is True
    assert second["mergeable"] is True, "a genuinely settled rollup must merge"


def test_a_rollup_that_settles_at_a_lower_count_still_opens_the_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The anti-wedge half of the dip fix, and it is not hypothetical.

    A check can disappear for good — a superseded rerun, a
    `concurrency: cancel-in-progress` consolidation, a bot retracting its check
    after an outage. `max_total` is a one-way ratchet, so an earlier version of
    this guard anchored on it and left `total < max_total` true on every future
    poll: the clock re-stamped forever and the gate never opened for that head
    again. A lens measured it stable at 4 checks for five hours, still refusing,
    with `settle_grace_minutes: 0` no escape because the age stays None.

    Anchoring on the PREVIOUS POLL's count instead has no such state: once the
    rollup stops moving at its new size it ages normally, whatever its old
    maximum was.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    grace = pr_watch._SETTLE_GRACE_MINUTES
    receipt = {"head": "abc123", "source": "fallback:panel"}

    def _view(n: int) -> dict:
        return _green_view(
            headRefOid="abc123",
            statusCheckRollup=[
                {"name": f"c{i}", "status": "COMPLETED", "conclusion": "SUCCESS"}
                for i in range(n)
            ],
        )

    def _poll(view: dict, now: datetime) -> dict:
        state = pr_watch.load_state(9)
        _since, _total = pr_watch.read_settle_since(state, "abc123")
        report = pr_watch.build_report(
            view,
            [],
            set(),
            review_receipt=receipt,
            check_details=pr_watch.CheckDetails([], "skipped"),
            now=now,
            prior_head=state.get("head"),
            prior_max_total=int(state.get("max_total") or 0),
            prior_settle_since=_since,
            prior_settle_total=_total,
        )
        pr_watch.persist_poll(9, report, set())
        return report

    t0 = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    _poll(_view(5), t0)                                   # five checks seen
    _poll(_view(4), t0 + timedelta(seconds=30))           # one gone, for good
    # It never comes back. The count is now stable, but permanently below the
    # maximum this head ever recorded.
    for minutes in (1, 2, grace + 1):
        report = _poll(_view(4), t0 + timedelta(minutes=minutes))

    assert report["checks"]["total"] < report["max_total"], (
        "precondition: the count really is below the head's recorded maximum"
    )
    assert report["rollup_settled"] is True, "the settle clock wedged permanently"

    # …and the PR is still blocked, by the OLDER guard, which this change does
    # not touch. `settling` is `total < max_total` against a ratcheting
    # `max_total`, so a permanently-dropped check holds `converged` false for
    # this head forever. That is #333, it predates this branch, and pinning the
    # boundary here is deliberate: without it a later reader would credit this
    # change with a wedge it does not cause, or "fix" #333 by loosening the
    # settle clock, which is the direction that reopens #39.
    assert report["settling"] is True, "#333's wedge is unchanged by this guard"
    assert report["converged"] is False
    assert report["mergeable"] is False


def test_a_dip_and_recovery_does_not_credit_the_time_before_the_dip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The recovery poll is the one that matters, and it is not the shrink poll.

    A rollup that drops and returns to its old count is, at the moment of
    return, indistinguishable from one that never moved — unless the baseline
    remembers what size it was taken at. It does: the stamp carries its `total`,
    and any difference restarts the clock, so both the drop and the return are
    movement.

    Two earlier anchors failed here, in opposite directions, and this test exists
    because of the first: resetting only on growth past `max_total` let the stamp
    survive the whole excursion and credited the span either side of the dip —
    measured by a review lens at `mergeable: true` after 2m45s of real stability
    against a 3m grace. (The second anchor, `settling or rollup_grew`, closed
    that and wedged the gate forever on a permanently-dropped check; that one is
    pinned by `test_a_rollup_that_settles_at_a_lower_count_still_opens_the_gate`.)

    Three real polls through `build_report` -> `persist_poll` -> `load_state`,
    because the defect lives in what one poll persists for the next and no
    single-poll assertion can see it.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "STATE_DIR", tmp_path)
    grace = pr_watch._SETTLE_GRACE_MINUTES
    receipt = {"head": "abc123", "source": "fallback:panel"}

    def _view(n: int) -> dict:
        return _green_view(
            headRefOid="abc123",
            statusCheckRollup=[
                {"name": f"c{i}", "status": "COMPLETED", "conclusion": "SUCCESS"}
                for i in range(n)
            ],
        )

    def _poll(view: dict, now: datetime) -> dict:
        state = pr_watch.load_state(9)
        _since, _total = pr_watch.read_settle_since(state, "abc123")
        report = pr_watch.build_report(
            view,
            [],
            set(),
            review_receipt=receipt,
            check_details=pr_watch.CheckDetails([], "skipped"),
            now=now,
            prior_head=state.get("head"),
            prior_max_total=int(state.get("max_total") or 0),
            prior_settle_since=_since,
            prior_settle_total=_total,
        )
        pr_watch.persist_poll(9, report, set())
        return report

    t0 = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    _poll(_view(5), t0)                                     # five checks, clock starts
    dip = _poll(_view(3), t0 + timedelta(seconds=30))       # one drops out
    assert dip["settling"] is True, "the dip itself is caught by settling"

    # Back to exactly five, comfortably past the grace measured from t0 — but
    # only seconds past it measured from when the rollup actually recovered.
    recovered = _poll(_view(5), t0 + timedelta(minutes=grace + 0.25))
    assert recovered["settling"] is False, "at the max again, so settling has lapsed"
    assert recovered["rollup_settled"] is False, (
        "the gate credited the span either side of the dip"
    )
    assert recovered["mergeable"] is False
    assert recovered["done"] is False

    # And it still clears once the recovered rollup has genuinely held.
    settled = _poll(_view(5), t0 + timedelta(minutes=2 * grace + 1))
    assert settled["rollup_settled"] is True, "a real wait must still open the gate"
    assert settled["mergeable"] is True


def test_a_settle_stamp_from_another_head_is_discarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Head-scoped like `bot_pending_since`, and for the same reason: a push
    means the rollup is being rebuilt, so a clock from the previous head is
    discarded rather than aged. Carrying it forward would let a long-settled
    prior head satisfy the gate for a commit pushed seconds ago.

    **Written with a positive control, because the earlier version of this test
    was hollowed out by an unrelated change and nobody noticed.** When
    `settle_since` grew a `total` field, this fixture kept omitting it — so the
    stamp was rejected for having no usable count, head-scoping was never
    reached, and deleting the head check entirely still passed. The test went on
    reporting a property it had stopped exercising. Varying ONLY the head, with
    the matching case asserted to settle, is what makes that impossible: if the
    stamp is rejected for any other reason the control fails first and says so.
    """
    pr_watch = _load_pr_watch()

    def _poll(stamp_head: str) -> dict:
        return _poll_via_main(
            monkeypatch,
            pr_watch,
            _settle_state(
                head="newsha",
                max_total=1,
                # Identical in every respect except whose head it was taken at.
                settle_since={
                    "head": stamp_head,
                    "at": _ago_iso(600.0),
                    "total": 1,
                },
                review_receipt={"head": "newsha", "source": "fallback:panel"},
            ),
            _green_view(headRefOid="newsha"),
        )

    control = _poll("newsha")
    assert control["mergeable"] is True, (
        "positive control: this stamp must otherwise satisfy the gate, or the "
        "negative case below proves nothing about head-scoping"
    )

    stale = _poll("oldsha")
    assert stale["mergeable"] is False, "a stale head's clock satisfied the gate"
    assert stale["settle_age_minutes"] is None, "the stamp was aged, not discarded"


@pytest.mark.parametrize(
    "stored_total",
    [None, "3", 1.0, True],
    ids=["absent", "string", "float", "bool"],
)
def test_a_stamp_that_cannot_say_its_count_is_not_a_baseline(
    stored_total, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The timestamp alone is not a baseline — it has to say what size rollup it
    stands for, or the next poll cannot tell whether anything moved.

    Fail closed rather than pairing a real timestamp with an unknown size: a
    stamp accepted without its count would settle on the very next poll whatever
    the rollup did, which is #190 wearing a timestamp. `True` is in the cases
    because `bool` is an `int` subclass and would otherwise slip through as the
    count 1 — the same trap `bot_pending_grace_minutes` validation already
    guards.

    **Two of these four cases carry the type guard; the other two would pass
    without it**, and saying so keeps the case list honest. Deleting the guard
    kills only `bool` and `float`, because `True == 1` and `1.0 == 1` compare
    equal to a one-check rollup and would be accepted as its count. `absent` and
    `string` fail closed anyway — `None` and `"3"` never equal an int, so the
    movement check rejects them a line later. They stay because they pin the
    intended behaviour at the boundary, not because they pin the guard.
    """
    pr_watch = _load_pr_watch()
    stamp = {"head": "abc123", "at": _ago_iso(600.0)}
    if stored_total is not None:
        stamp["total"] = stored_total

    report = _poll_via_main(
        monkeypatch,
        pr_watch,
        _settle_state(settle_since=stamp),
        _green_view(headRefOid="abc123"),
    )

    assert report["settle_age_minutes"] is None, f"a {stored_total!r} count was used"
    assert report["rollup_settled"] is False
    assert report["mergeable"] is False


def test_an_unusable_settle_stamp_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_age_minutes` returns None for a stamp it cannot use — unparseable, the
    zero time, or meaningfully in the future (a state file copied between
    machines, or a clock that ran ahead and was then NTP-corrected). None means
    "unknown", and unknown must not read as settled.

    Every stamp carries a valid `total`, and the control below asserts a well
    formed one settles. Both matter: without them this test stopped exercising
    `_age_minutes` entirely the moment `total` became required — the stamps were
    rejected as malformed one branch earlier, and disabling all three of
    `_age_minutes`'s validation branches left it green. A lens caught that; it
    had been passing for the wrong reason since the field was added.
    """
    pr_watch = _load_pr_watch()
    view = _green_view(headRefOid="abc123")

    def _poll(stamp: str) -> dict:
        return _poll_via_main(
            monkeypatch,
            pr_watch,
            _settle_state(
                settle_since={"head": "abc123", "at": stamp, "total": 1},
            ),
            view,
        )

    assert _poll(_ago_iso(600.0))["mergeable"] is True, (
        "control: a usable stamp of this exact shape must settle, or the cases "
        "below prove nothing about `_age_minutes`"
    )

    for stamp in ("not-a-timestamp", "0001-01-01T00:00:00Z", _ago_iso(-600.0)):
        report = _poll(stamp)
        assert report["settle_age_minutes"] is None, f"an unusable stamp was aged: {stamp}"
        assert report["mergeable"] is False, f"an unusable stamp opened the gate: {stamp}"


def test_the_settle_grace_is_configurable_and_rejects_nonsense(
    tmp_path: Path,
) -> None:
    """Same validation shape as `bot_pending_grace_minutes`, and the same
    asymmetry: a large value is fail-closed (a slow merge), while 0 disables the
    guard outright, so a typo must never land on 0."""
    pr_watch = _load_pr_watch()
    default = pr_watch._DEFAULT_SETTLE_GRACE_MINUTES

    def _grace(body: str) -> float:
        path = tmp_path / f"cfg{abs(hash(body))}.yaml"
        path.write_text(body, encoding="utf-8")
        return pr_watch._load_review_config(path).settle_grace_minutes

    assert _grace("review:\n  settle_grace_minutes: 7\n") == 7.0
    assert _grace("review:\n  settle_grace_minutes: 0\n") == 0.0, "0 is a legitimate opt-out"
    for nonsense in ("'soon'", "-1", "true"):
        assert _grace(f"review:\n  settle_grace_minutes: {nonsense}\n") == default, nonsense


def test_a_ci_less_repo_still_waits_for_the_settle_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `require_ci: false` interaction, decided rather than inherited.

    A CI-less repo's rollup is permanently empty, so nothing can "still be
    registering" and the ambiguity this guard resolves cannot arise there. The
    guard applies anyway, and that costs such a repo one extra poll plus the
    grace before it can merge. Found by a review lens, by execution.

    **The short-circuit was considered and refused.** Skipping the gate when the
    rollup is empty would authorize a merge on a first poll whose rollup is empty
    *because the checks have not registered yet* — which is #39 exactly, for any
    adopter who set `require_ci: false` while still having intermittent CI.
    `safety-critical-changes.md` rule 3 names that trade: the harm is swapping a
    fail-CLOSED limitation for a fail-OPEN mechanism. So the latency stands as a
    known cost, and this test is here so it is a decision somebody made rather
    than a default nobody examined.
    """
    pr_watch = _load_pr_watch()
    monkeypatch.setattr(pr_watch, "_REQUIRE_CI", False)
    view = _green_view(statusCheckRollup=[], mergeStateStatus="CLEAN")
    receipt = {"head": "abc123", "source": "fallback:panel"}

    first_poll = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt=receipt,
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert first_poll["checks"]["all_green"] is True, "a zero-check PR reads green here"
    assert first_poll["converged"] is True, "the watch loop is not blocked"
    assert first_poll["mergeable"] is False, "the documented cost is one extra poll"

    settled = pr_watch.build_report(
        view,
        [],
        set(),
        review_receipt=receipt,
        check_details=pr_watch.CheckDetails([], "skipped"),
        **_settled(view),
    )
    assert settled["mergeable"] is True, "and it clears — a cost, not a wedge"


def test_a_head_change_drops_the_stamp_even_if_the_caller_did_not() -> None:
    """Belt-and-braces, pinned at the level where it is reachable.

    Through `main` this is redundant: `read_settle_since` head-scopes before
    `build_report` ever sees the stamp, so a mismatched pair cannot occur — which
    is why mutating it survives the suite, as a lens found. It still guards a
    direct caller (a test, an embedder) that threads state itself, and the
    assertion is on `rollup_settled` rather than `mergeable` because
    `head_changed` independently forces `settling`, which would mask it.
    """
    pr_watch = _load_pr_watch()
    report = pr_watch.build_report(
        _green_view(headRefOid="newsha"),
        [],
        set(),
        check_details=pr_watch.CheckDetails([], "skipped"),
        prior_head="oldsha",
        prior_max_total=1,
        # Inconsistent on purpose: a long-settled stamp handed alongside a
        # DIFFERENT prior head. `main` cannot produce this pair.
        prior_settle_since=_ago_iso(600.0),
        prior_settle_total=1,
    )
    assert report["head_changed"] is True
    assert report["rollup_settled"] is False, "a push inherited the old head's clock"


def test_the_grace_boundary_is_inclusive() -> None:
    """`>=`, not `>`. Flipping it survives every other test, because the fixtures
    sit far past the grace and nothing lands on the boundary itself."""
    pr_watch = _load_pr_watch()
    view = _green_view()
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    grace = pr_watch._SETTLE_GRACE_MINUTES

    def _at(minutes: float) -> bool:
        return pr_watch.build_report(
            view,
            [],
            set(),
            check_details=pr_watch.CheckDetails([], "skipped"),
            now=now,
            prior_head=view["headRefOid"],
            prior_max_total=len(view["statusCheckRollup"]),
            prior_settle_since=(
                (now - timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
            ),
            prior_settle_total=len(view["statusCheckRollup"]),
        )["rollup_settled"]

    assert _at(grace) is True, "exactly at the grace must settle (>= not >)"
    assert _at(grace - 0.01) is False, "a hair under must not"


def test_the_settle_blocker_is_reported_to_the_operator() -> None:
    """A blocker nobody prints is a blocker nobody can act on — the PR just
    refuses to merge with no stated reason."""
    pr_watch = _load_pr_watch()
    report = pr_watch.build_report(
        _green_view(headRefOid="abc123"),
        [],
        set(),
        review_receipt={"head": "abc123", "source": "fallback:panel"},
        check_details=pr_watch.CheckDetails([], "skipped"),
    )
    assert report["mergeable"] is False
    assert "settle" in pr_watch.render(report).lower()


def test_the_rest_bound_uses_the_backend_that_did_the_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_resolve_backend` re-reads PATH on every call by design, so re-resolving
    the backend inside `build_report` was a race: a `gh` appearing during the
    poll's network phase (several round trips at 30s each) made the bound evaluate
    against a transport that fetched nothing, and a report built entirely from REST
    data came back `mergeable: true`.

    Fixed by resolving once in `main`, before the first read, and threading it.
    """
    pr_watch = _load_pr_watch()

    view = _green_view(headRefOid="abc123")
    receipt = {"head": "abc123", "source": "fallback:panel", "lenses": ["a", "b"]}

    # Data came from REST: the bound must fire even though PATH now says `gh`.
    rest = pr_watch.build_report(
        view, [], set(), review_receipt=receipt,
        check_details=pr_watch.CheckDetails([], "skipped"), backend="rest",
    )
    assert rest["mergeable"] is False
    assert any("cannot authorize a merge" in b for b in rest["merge_blockers"])
    assert rest["backend"] == "rest"

    # And the reverse: a gh-fetched report is not bounded by a PATH that lost gh.
    monkeypatch.setattr(pr_watch.shutil, "which", lambda _n: None)
    monkeypatch.setenv("GH_TOKEN", "t0ken")
    gh = pr_watch.build_report(
        view, [], set(), review_receipt=receipt,
        check_details=pr_watch.CheckDetails([], "skipped"), backend="gh",
        **_settled(view),
    )
    assert gh["mergeable"] is True
    assert gh["backend"] == "gh"


def test_main_resolves_the_backend_before_it_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The threading has to happen in `main`, which is the only production caller —
    asserting it on `build_report` alone would leave the wiring unpinned, which is
    exactly how the previous round's fix survived deletion."""
    pr_watch = _load_pr_watch()
    order: list[str] = []

    monkeypatch.setattr(pr_watch, "resolve_pr", lambda explicit: 9)
    monkeypatch.setattr(
        pr_watch, "_active_backend_name", lambda: (order.append("resolve"), "rest")[1]
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_pr_view",
        lambda pr: (order.append("read"), (_green_view(headRefOid="abc123"), []))[1],
    )
    monkeypatch.setattr(
        pr_watch, "fetch_check_details", lambda pr, **kw: pr_watch.CheckDetails([], "skipped")
    )
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: {})
    monkeypatch.setattr(pr_watch, "save_state", lambda pr, state: None)

    seen_backend: list[str | None] = []
    real_build = pr_watch.build_report

    def _build(*a, **kw):
        seen_backend.append(kw.get("backend"))
        return real_build(*a, **kw)

    monkeypatch.setattr(pr_watch, "build_report", _build)
    assert pr_watch.main(["9", "--json"]) == 0

    assert order[:2] == ["resolve", "read"], f"resolved after reading: {order}"
    assert seen_backend == ["rest"], "main did not thread the backend it resolved"


def test_no_persist_builds_the_report_without_rewriting_watch_state(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The final authorization probe must not acknowledge an unread comment.

    Patching ``persist_poll`` itself pins the production call site: an
    implementation that merely avoids ``save_state`` through another path would
    still fail this test if ``main`` accidentally invokes the state transition.
    """
    pr_watch = _load_pr_watch()
    original_state = {
        "head": "abc123",
        "max_total": 1,
        "seen": ["issue:already-read"],
        "pending_seen": ["issue:operator-has-not-read"],
    }

    monkeypatch.setattr(pr_watch, "resolve_pr", lambda explicit: 9)
    monkeypatch.setattr(
        pr_watch,
        "fetch_pr_view",
        lambda pr: (_green_view(headRefOid="abc123"), []),
    )
    monkeypatch.setattr(
        pr_watch,
        "fetch_check_details",
        lambda pr, **kw: pr_watch.CheckDetails([], "skipped"),
    )
    monkeypatch.setattr(pr_watch, "load_state", lambda pr: original_state.copy())

    def _must_not_persist(*_args, **_kwargs):
        pytest.fail("--no-persist invoked persist_poll")

    monkeypatch.setattr(pr_watch, "persist_poll", _must_not_persist)

    assert pr_watch.main(["9", "--json", "--no-persist"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["head"] == "abc123"


@pytest.mark.parametrize(
    "mode",
    ["--mark-seen", "--record-review", "--assert-draft", "--assert-ready"],
)
def test_no_persist_refuses_state_changing_modes(
    mode: str, capsys: pytest.CaptureFixture[str]
) -> None:
    pr_watch = _load_pr_watch()
    argv = ["9", "--no-persist", mode]
    if mode == "--record-review":
        argv.extend(["fallback:panel", "--head", "abc123"])

    with pytest.raises(SystemExit, match="2"):
        pr_watch.main(argv)
    assert "--no-persist is only valid with a plain poll" in capsys.readouterr().err

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


def test_a_malformed_check_field_cannot_wedge_the_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `gh` CLI applies a schema, so these fields always arrive as strings.
    REST hands raw JSON to `summarize_checks`/`summarize_review_bots`, which call
    `.strip()` and `.lower()` on them — so a dict-valued `name` or `output.title`
    raised AttributeError out of `build_report`, which runs OUTSIDE `main`'s try.

    The wedge is the point: the raise precedes `persist_poll`, so no state is
    written and every later poll repeats it. One malformed field, and that PR's
    watch loop is stuck with no ageing-out and no override.
    """
    pr_watch = _load_pr_watch()

    rows = pr_watch._rest_check_rows(
        [
            {
                "name": {"a": 1},
                "status": "completed",
                "conclusion": ["success"],
                "output": {"title": {"nested": "Review rate limited"}},
                "started_at": {"t": 1},
            }
        ],
        [{"context": 42, "state": {"s": 1}, "description": ["x"], "created_at": ""}],
    )

    # Every field a downstream pure function will call a string method on.
    for row in rows:
        for field in ("name", "state", "bucket", "description", "startedAt"):
            assert isinstance(row[field], str), (field, row)

    # And end to end: the two consumers must not raise.
    assert pr_watch.summarize_checks(rows)["all_green"] is False
    pr_watch.summarize_review_bots(rows, [], now=NOW)

    # A dict description must NOT be stringified into the outage matchers — that
    # would let `{'nested': 'Review rate limited'}` read as a real rate-limit.
    assert rows[0]["description"] == ""

    report = pr_watch.build_report(
        {
            "number": 9, "state": "OPEN", "headRefOid": "h",
            "statusCheckRollup": rows, "reviews": [], "comments": [],
        },
        [], set(), check_details=pr_watch.CheckDetails(rows, "ok"),
    )
    assert report["merge_blockers"] is not None  # it got this far without raising


def test_our_own_clock_wins_over_the_checks_stamp() -> None:
    """A 13-line comment argues for this precedence and nothing tested it; a review
    lens inverted it and the whole suite stayed green.

    Demonstrated permissive when inverted: an observed clock 1 minute old plus a
    bot check started 45m ago gives `blocking: True` with our clock and
    `cancelled_by: grace` with the check's — #19's merge blocker gone. Preferring
    the check's stamp also lets the age REGRESS, which makes `merge_blockers`
    non-monotonic in wall-clock time.
    """
    pr_watch = _load_pr_watch()

    detail = _bot_check(state="PENDING", bucket="pending", startedAt=_minutes_ago(45))
    result = pr_watch.summarize_review_bots(
        [detail], [], now=NOW, pending_since={"coderabbit": _minutes_ago(1)}
    )
    assert result["pending"], "the bot should still be pending"
    entry = result["pending"][0]
    assert entry["age_source"] == "observed", "the check's stamp displaced our clock"
    assert entry["age_minutes"] == 1.0
    assert entry["blocking"] is True
    assert result["blockers"] != []


def test_a_check_row_carrying_neither_bucket_nor_state_reads_as_pending() -> None:
    """`_check_is_pending`'s docstring calls this fail-closed and deliberate — "a
    truncated row whose name matches a bot holds the merge gate for the grace
    window rather than waving it through" — and replacing it with `return False`
    passed the suite."""
    pr_watch = _load_pr_watch()

    assert pr_watch._check_is_pending({"name": "CodeRabbit"}) is True
    assert pr_watch._check_is_pending({"name": "CodeRabbit", "bucket": ""}) is True
    assert pr_watch._check_is_pending({"name": "CodeRabbit", "state": ""}) is True
    # And a genuinely terminal row still reads as finished.
    assert pr_watch._check_is_pending({"name": "CodeRabbit", "state": "SUCCESS"}) is False
    assert pr_watch._check_is_pending({"name": "CodeRabbit", "bucket": "pass"}) is False
