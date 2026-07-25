#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Poll a PR's CI checks + new review comments — the engine for the watch-and-fix loop.

The shared `pr-watch` workflow (and the "PR follow-through" policy in your project's
agent instructions)
call this once per round: it asks `gh` for the PR's check rollup + every
comment surface (issue comments, review submissions, inline review comments),
filters out known auto-noise (while surfacing reviewer-unavailability notices),
diffs against a per-PR seen-set so only *new actionable* comments surface, and
reports two distinct predicates:

- `converged` — checks green, nothing new to act on, not mid-settle. The
  WATCH-LOOP predicate: "is there more for me to fix?"
- `mergeable` — `converged` AND no deterministic merge blocker AND an
  independent-review receipt bound to the current head. The MERGE-GATE
  predicate, re-checked by `dev_session.sh merge` at act time.

A `converged` PR is not necessarily `mergeable`. Keeping them separate is what
lets a caller watch to convergence without being forced to record a review
receipt just to terminate the loop (see `decide_converged`).

It also resolves each configured review bot (`review.bots`) to *unavailable* or
*pending* (`summarize_review_bots`). A bot's own status check is excluded from
the blocking tally so a bot that never reports cannot wedge the loop — but that
exclusion used to make an outage indistinguishable from a clean review, and a
merely-queued bot indistinguishable from a finished one. Both signals now feed
the MERGE GATE only, never `converged`, so the anti-wedge property is untouched.

`done` is a LEGACY alias, always equal to `mergeable`. Its meaning is unchanged
and must stay that way: engine upgrades are per-file, so a new `pr_watch.py` can
run against an older `dev_session.sh` that gates merges on `done` — repurposing
the key would silently authorize merges on unreviewed PRs.

The caller loops: run this -> if not converged, fix the failures / address or
reply to the new comments -> `--mark-seen` -> wait -> run again. `converged`
flips true once CI is green and every finding has been handled; `mergeable`
additionally waits on `--record-review`.

`--mark-seen` NEVER re-polls `gh`. Every plain poll (any invocation without
`--mark-seen`) persists the exact ``all_seen_keys`` it just reported into a
per-PR "pending" slot (`state["pending_seen"]`). `--mark-seen` promotes THAT
stored set into `seen` and clears the slot — it does not re-derive the ack set
from a fresh fetch. This closes the ordering hazard where a comment posted
after the caller's read-poll but before `--mark-seen` would otherwise be
silently absorbed into a fresh re-poll's superset and never surface: since
`--mark-seen` no longer talks to `gh` at all, a comment that isn't in the last
reported poll's set structurally can't be acked — it stays unseen and surfaces
on the next poll. Calling `--mark-seen` cold (no prior poll reported since the
last ack) acks nothing and says so via `report["note"]`.

The `gh` shelling is a thin layer; the classification + diff + done logic are pure
functions (tested). Stdlib only.

Usage:
    uv run scripts/pr_watch.py                 # current branch's PR, human summary
    uv run scripts/pr_watch.py 916 --json       # explicit PR, machine-readable
    uv run scripts/pr_watch.py --mark-seen      # ack exactly what the last poll reported
    uv run scripts/pr_watch.py 916 --record-review "fallback:codex" --head <polled-sha>
    uv run scripts/pr_watch.py 916 --assert-draft  # correct a drifted draft bit after `gh pr create --draft`
    uv run scripts/pr_watch.py 916 --assert-ready  # correct a drifted draft bit before `gh pr merge`

`gh`'s draft bit is flaky in both directions (observed on gh 2.89.0): a
`--draft` create can silently land non-draft (a review bot auto-reviews and
burns rate-limit budget before the lane can re-draft), and a ready PR can
silently revert to draft (a later `gh pr merge` fails with "Pull Request is
still a draft"). `--assert-draft` / `--assert-ready` read `isDraft` and issue
the one corrective `gh pr ready [--undo]` call if it drifted, then re-read to
confirm — call the former right after `gh pr create --draft`, the latter
right before `gh pr merge`.

Exit codes:
    0 — reported (regardless of the verdict; check `converged` / `mergeable` in
        the output), or the draft-bit assertion held/was corrected successfully
    2 — usage error (no PR found, gh failure), or a draft-bit assertion that
        failed to correct (`ok: false`)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple


def _find_repo_root(start: Path) -> Path:
    """Nearest ancestor with a ``.git`` marker (so this keeps working when the kit
    is vendored under a nested dir, e.g. scripts/devkit/); falls back to the
    script's grandparent if no marker is found. Inlined — pr_watch stays stdlib-only."""
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start.parent.parent


REPO_ROOT = _find_repo_root(Path(__file__).resolve())

# Sticky on-disk sandbox marker, written at the worktree root by a headless-lane
# launcher (see scripts/lib/state_paths/). Same name/semantics as state_paths —
# the two must agree or a lane's state splits in half (see below).
STATE_ROOT_MARKER = ".devkit_state_root"


def _marker_state_root(start: Path) -> Path | None:
    """Sandbox root from a ``.devkit_state_root`` marker, walked up from ``start``.

    Mirrors ``state_paths.resolver._marker_state_root``: walk up checking for the
    marker, ceilinged at the first directory carrying a ``.git`` entry (checked
    *after* the marker, so a marker sitting beside ``.git`` is still found), and
    accept only an absolute path from inside it.

    Deliberate divergence: state_paths *raises* on a relative/garbage marker,
    while this returns ``None`` and lets the caller fall back. pr_watch runs in
    the hot watch-and-fix loop, where the file's standing rule is "never crash
    the loop" — the same reason a relative ``DEVKIT_STATE_ROOT`` falls back here
    instead of raising.

    ``start`` is this engine file's own directory rather than ``Path.cwd()``
    (which is what state_paths uses): the marker lives at the worktree root and
    the engine file lives *inside* that worktree, whereas the caller's cwd is
    arbitrary — ``dev_session.sh`` invokes this engine from wherever the operator
    happened to be.
    """
    for candidate in (start, *start.parents):
        marker = candidate / STATE_ROOT_MARKER
        try:
            if marker.is_file():
                raw = marker.read_text(encoding="utf-8").strip()
                # Empty or relative -> ignore (fall back), never a silent redirect.
                return Path(raw) if raw and os.path.isabs(raw) else None
        except OSError:
            return None  # unreadable marker -> fall back rather than crash
        if (candidate / ".git").exists():
            break  # worktree root: don't climb into an unintended ancestor
    return None


def _resolve_state_root(start: Path, repo_root: Path, state_root_env: str | None) -> Path:
    """Absolute dir this engine's per-PR watch state lives under.

    ``$DEVKIT_STATE_ROOT`` -> ``.devkit_state_root`` marker -> ``<repo>/state``,
    the same precedence (and the same marker-only-when-the-env-var-is-unset rule)
    as ``state_paths.resolver.state_root``. Honoring the marker is what keeps
    ``dev_session.sh pr-watch <scope>`` — which exports the env var — and a bare
    ``uv run pr_watch.py`` inside a marker-driven headless lane reading the SAME
    per-PR file: while only the env var was honored, the two used different state,
    so a ``--mark-seen`` through one path was invisible to the other and the merge
    gate could re-surface already-acked findings.

    Inlined rather than importing state_paths on purpose: pr_watch is deliberately
    stdlib-only (``dependencies = []``) for the hot loop. Own-dir state, so no
    read-cascade is needed — only the write root.
    """
    if state_root_env:
        # A relative override falls back to the repo-root default rather than
        # raising (never crash the loop), and does NOT consult the marker — an
        # explicit env var, even a bad one, means the caller chose the root.
        return (
            Path(state_root_env)
            if os.path.isabs(state_root_env)
            else repo_root / "state"
        )
    marker = _marker_state_root(start)
    return marker if marker is not None else repo_root / "state"


_STATE_ROOT = _resolve_state_root(
    Path(__file__).resolve().parent, REPO_ROOT, os.environ.get("DEVKIT_STATE_ROOT")
)
STATE_DIR = _STATE_ROOT / "pr-watch"

# ------------------------------------------------------- review-bot knowledge
#
# Which comment bodies are auto-noise, which signal a *down* reviewer, and which
# status checks are advisory is **adopter knowledge, not engine logic** — it
# depends entirely on the review-bot mix a given org runs. It therefore lives in
# `config/dev-model.yaml` under `review.*`; the tuples below are only the
# fallbacks used when that config is missing or unreadable.
#
# This is the difference between an engine you can update and one you can't: the
# previous version told adopters to edit these literals in place, which forks the
# engine and makes every later kit update a merge conflict (Principle #10).
#
# Read via `scripts/lib/kitconfig.py` — the kit's stdlib-only config reader —
# specifically so this module keeps `dependencies = []` and never drags PyYAML
# into the hot watch-and-fix loop.

# Keep this list tight — over-filtering would hide a real review. Defaults target
# a GitHub + CodeRabbit + Bugbot setup.
_DEFAULT_NOISE_MARKERS = (
    "bugbot needs on-demand usage enabled",  # Cursor billing notice
    "<!-- this is an auto-generated comment: summarize by coderabbit",  # walkthrough
    "<!-- this is an auto-generated comment: review in progress",  # CodeRabbit "processing…" placeholder
    "<!-- walkthrough_start -->",
    "actionable comments posted: 0",  # CodeRabbit "nothing to change" review
    "review skipped",  # CodeRabbit draft-detected / skip notices
    "<!-- linear-linkback -->",  # a tracker's auto issue-mirror comment (not a finding)
)

# Review unavailability is actionable even when the surrounding comment also
# carries a generic walkthrough/noise marker. Surfacing it is what triggers the
# configured independent fallback; hiding it would turn a down reviewer into a
# silent review waiver.
_DEFAULT_REVIEW_UNAVAILABLE_MARKERS = (
    "bugbot needs on-demand usage enabled",
    "review limit reached",
    "rate limited by coderabbit",
    "couldn't start this review",
    "review skipped",
    "no review credits",
    # The status-check phrasing of the same outage. Same bot, same rate limit, an
    # hour apart on #22 vs #24, but a different wording on a different surface —
    # the comment said "review limit reached", the check description said "Review
    # rate limited". Matching only the comment wording is what made detection
    # depend on which surface the bot happened to use (#23).
    "review rate limited",
)

# Status contexts that are advisory only — they must NEVER block "done". A
# review-bot status check can sit PENDING indefinitely after a trivial
# follow-up commit (it never auto-incrementally-reviews it), which would
# otherwise wedge the loop forever even though every real CI job is green. Its
# actual findings surface as review comments (which DO block via
# new_comments). Matched case-insensitively against the check name/context.
_DEFAULT_INFORMATIONAL_CHECK_NAMES = ("coderabbit",)

# The configured independent review bots (`review.bots`). Distinct in PURPOSE
# from `_DEFAULT_INFORMATIONAL_CHECK_NAMES` even though the shipped values
# coincide: that list is a *blocking policy* ("this check never blocks"), this
# one is an *identity* ("these checks belong to a reviewer whose state we care
# about"). Keeping them separate is what lets a bot's check stay non-blocking
# for `converged` while its state still informs the merge gate — the exact
# split issues #19 and #23 need. Matched as a case-insensitive SUBSTRING of a
# check name, and as a case-insensitive PREFIX of a comment author (that input
# is not the repo's to control) — so `coderabbit` covers the check `CodeRabbit`
# and the author `coderabbitai`. Keep entries specific enough not to collide
# with a CI job name.
_DEFAULT_REVIEW_BOTS = ("coderabbit",)

# How long a configured review bot's own check may sit non-terminal before the
# merge gate stops waiting for it. Below the bound, a pending bot is "a review
# is coming" and blocks `mergeable` (issue #19 — a receipt recorded against a
# merely *slow* bot let four post-merge findings through). Above it, the bot is
# treated as never going to report and stops blocking — which is what preserves
# the anti-wedge property that `_DEFAULT_INFORMATIONAL_CHECK_NAMES` exists for.
_DEFAULT_BOT_PENDING_GRACE_MINUTES = 15.0

# Whether a PR must carry at least one real (non-informational) check before it
# can read as green. True is the safe default — see :func:`summarize_checks`.
_DEFAULT_REQUIRE_CI = True

# Same pattern as check_doc_budget.py: the reader ships beside the engines, so
# deriving its directory from THIS file keeps working when the kit is vendored
# under a nested dir (scripts/devkit/).
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))


class ReviewConfig(NamedTuple):
    """The resolved ``review.*`` knobs.

    A NamedTuple rather than a bare tuple because this shape GREW — it carried
    four fields until #19/#23 needed the reviewer's identity and a pending
    bound. Positional unpacking makes every future addition a breaking change
    for every reader; named fields make it additive, which is the same property
    the report schema is held to.
    """

    noise_markers: tuple[str, ...]
    unavailable_markers: tuple[str, ...]
    informational_checks: frozenset[str]
    require_ci: bool
    bots: tuple[str, ...]
    bot_pending_grace_minutes: float


def _load_review_config(config_path: str | Path | None = None) -> ReviewConfig:
    """Resolve the ``review.*`` knobs from config, falling back to the defaults.

    ``config_path`` overrides the default ``config/dev-model.yaml`` lookup (used
    by the tests to exercise a real adopter config without touching this repo's).

    Returns a :class:`ReviewConfig`. Marker strings are lower-cased here because
    every call site matches them case-insensitively against a lower-cased
    body/name — so a config author may write them in any case.

    **Never raises.** A missing config file, an absent ``scripts/lib/``, a
    parse failure, a wrong-typed value: all fall back to the in-module defaults,
    because a config problem must not wedge or crash the watch loop. A config
    that *exists* but could not be read warns on stderr, so a silently-ignored
    config is still visible; a merely absent one is normal (the engine runs
    standalone) and stays quiet.

    Distinctions worth knowing:

    - key absent / ``key:`` with no value -> the default list applies.
    - key set to an explicit empty list (``noise_markers: []``) -> honored as
      "filter nothing". Deliberate: an adopter with no review bots wants no
      filtering, and over-filtering hides real findings.
    - ``require_ci`` accepts only a real boolean; anything else (a stray
      ``yes``, a typo) keeps the default. The unsafe direction here is reading
      as *False* by accident, which would let a zero-check PR report green.
    - ``bot_pending_grace_minutes`` accepts a non-negative number (``bool`` is
      rejected despite being an ``int`` subclass; anything non-numeric keeps the
      default). Both directions are reachable and only one is dangerous: a large
      value makes a dead bot hold the merge gate for hours — annoying, but
      fail-*closed* — while **``0`` disables the guard outright**, since the
      bound is ``age >= grace``. That is a legitimate setting for a repo that
      wants the #23 outage signal without the #19 wait, but it is opt-out of a
      safety check, so set it deliberately rather than as a way to quiet a slow
      bot.
    """
    defaults = ReviewConfig(
        noise_markers=_DEFAULT_NOISE_MARKERS,
        unavailable_markers=_DEFAULT_REVIEW_UNAVAILABLE_MARKERS,
        informational_checks=frozenset(_DEFAULT_INFORMATIONAL_CHECK_NAMES),
        require_ci=_DEFAULT_REQUIRE_CI,
        bots=_DEFAULT_REVIEW_BOTS,
        bot_pending_grace_minutes=_DEFAULT_BOT_PENDING_GRACE_MINUTES,
    )
    try:
        from kitconfig import get, get_str_list, load_config

        config = load_config() if config_path is None else load_config(config_path)
        noise = get_str_list(config, "review.noise_markers", list(_DEFAULT_NOISE_MARKERS))
        unavailable = get_str_list(
            config,
            "review.unavailable_markers",
            list(_DEFAULT_REVIEW_UNAVAILABLE_MARKERS),
        )
        informational = get_str_list(
            config,
            "review.informational_checks",
            list(_DEFAULT_INFORMATIONAL_CHECK_NAMES),
        )
        bots = get_str_list(config, "review.bots", list(_DEFAULT_REVIEW_BOTS))
        require_ci = get(config, "review.require_ci", _DEFAULT_REQUIRE_CI)
        if not isinstance(require_ci, bool):
            require_ci = _DEFAULT_REQUIRE_CI
        grace = get(
            config,
            "review.bot_pending_grace_minutes",
            _DEFAULT_BOT_PENDING_GRACE_MINUTES,
        )
        if isinstance(grace, bool) or not isinstance(grace, (int, float)) or grace < 0:
            grace = _DEFAULT_BOT_PENDING_GRACE_MINUTES
    except FileNotFoundError:
        # `load_config` raises this for an absent config file — a standalone
        # engine run. Defaults are exactly right; stay quiet.
        return defaults
    except Exception as exc:  # noqa: BLE001 — a config read must never break the loop
        # Anything else means the config (or the reader beside it) IS there and
        # could not be used: an unreadable file, a construct the parser rejects,
        # a vendored copy missing scripts/lib/. Fall back, but say so — a
        # silently-ignored config is how an adopter's settings become a no-op.
        print(
            f"warning: could not read review config ({exc}); "
            "using pr_watch's built-in defaults",
            file=sys.stderr,
        )
        return defaults
    return ReviewConfig(
        noise_markers=tuple(marker.lower() for marker in noise),
        unavailable_markers=tuple(marker.lower() for marker in unavailable),
        informational_checks=frozenset(
            name.strip().lower() for name in informational if name.strip()
        ),
        require_ci=require_ci,
        bots=tuple(bot.strip().lower() for bot in bots if bot.strip()),
        bot_pending_grace_minutes=float(grace),
    )


_REVIEW_CONFIG = _load_review_config()
_NOISE_MARKERS = _REVIEW_CONFIG.noise_markers
_REVIEW_UNAVAILABLE_MARKERS = _REVIEW_CONFIG.unavailable_markers
_INFORMATIONAL_CHECK_NAMES = _REVIEW_CONFIG.informational_checks
_REQUIRE_CI = _REVIEW_CONFIG.require_ci
_REVIEW_BOTS = _REVIEW_CONFIG.bots
_BOT_PENDING_GRACE_MINUTES = _REVIEW_CONFIG.bot_pending_grace_minutes


# --------------------------------------------------------------------------- gh


def _gh(args: list[str], *, timeout: int = 60) -> str:
    cmd = ["gh", *args]
    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        # A hung gh call must not wedge the watch loop — surface it as an error
        # the caller already handles (main catches RuntimeError → exit 2).
        raise RuntimeError(f"gh {' '.join(args)} timed out after {timeout}s") from exc
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def _gh_json(args: list[str]):
    return json.loads(_gh(args))


_bot_signal_warned = False


def _warn_bot_signal_lost(reason: str) -> None:
    """Say once, on stderr, that the review-bot guards are running blind.

    Once per process, not per poll: a watch loop calls this every round, and a
    warning repeated forty times is skimmed past exactly like silence.
    """
    global _bot_signal_warned
    if _bot_signal_warned:
        return
    _bot_signal_warned = True
    print(
        f"warning: could not read check details ({' '.join(reason.split())[:160]}); "
        "review-bot pending/outage state is unavailable, so a queued or "
        "rate-limited reviewer will not be detected",
        file=sys.stderr,
    )


class CheckDetails(NamedTuple):
    """``gh pr checks`` rows plus whether they could be read at all.

    The signal is the point: an empty ``rows`` from a failed fetch is otherwise
    byte-identical to an empty one from a genuinely quiet bot, and both #19's and
    #23's guards go silently dead in the first case.
    """

    rows: list[dict]
    signal: str  # "ok" | "skipped" | "unavailable"


def fetch_check_details(pr: int, *, bots: tuple[str, ...] | None = None) -> CheckDetails:
    """Per-check ``{name, state, bucket, description, startedAt}`` for one PR.

    A SECOND ``gh`` call, and deliberately so. ``gh pr view --json
    statusCheckRollup`` — the source :func:`summarize_checks` reads — returns a
    fixed sub-shape with **no description field** on either a ``CheckRun`` or a
    ``StatusContext``. That omission is the whole of issue #23: CodeRabbit
    reported its rate limit *only* as a check description ("Review rate
    limited") on an otherwise-``SUCCESS`` context, so nothing pr_watch could see
    carried the outage. ``gh pr checks --json`` normalizes both check kinds and
    does expose ``description``.

    The two sources are kept in their own lanes on purpose: this one feeds ONLY
    :func:`summarize_review_bots` (reviewer identity + state), never the
    blocking tally. Letting a second fetch influence ``all_green`` would mean two
    views of CI that can disagree between calls.

    **Never raises, and never blocks the loop.** ``gh pr checks`` exits non-zero
    for perfectly normal states (8 = some check pending, 1 = some check failing)
    and errors outright on a PR with no checks at all, so the exit code is
    ignored and only parseable JSON on stdout is used. Any failure degrades to
    ``[]`` — which reads as "no bot signal", the same fail-open direction the
    informational-check exclusion already takes.

    **But it says so, once.** Degrading silently would disable both #19's and
    #23's guards without a trace — an older ``gh`` that rejects one of these
    ``--json`` fields fails exactly this way, and "checked and clean" would be
    indistinguishable from "never checked". Warned once per process rather than
    per poll, so a watch loop does not turn one real problem into a wall.

    Skips the call entirely when no review bots are configured: with nothing to
    match, the result could only ever be discarded.
    """
    if bots is None:
        bots = _REVIEW_BOTS
    if not bots:
        return CheckDetails([], "skipped")
    cmd = [
        "gh",
        "pr",
        "checks",
        str(pr),
        "--json",
        "name,state,bucket,description,startedAt",
    ]
    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _warn_bot_signal_lost(str(exc))
        return CheckDetails([], "unavailable")
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        # stdout wasn't JSON, so the exit code IS the story here — an older `gh`
        # rejecting one of these fields, or a PR with no checks at all.
        _warn_bot_signal_lost(result.stderr or f"gh exited {result.returncode}")
        return CheckDetails([], "unavailable")
    if not isinstance(parsed, list):
        _warn_bot_signal_lost("gh pr checks returned an unexpected shape")
        return CheckDetails([], "unavailable")
    return CheckDetails([item for item in parsed if isinstance(item, dict)], "ok")


def resolve_pr(explicit: int | None) -> int:
    """Return the PR number — explicit, or the current branch's open PR."""
    if explicit is not None:
        return explicit
    data = _gh_json(["pr", "view", "--json", "number"])
    return int(data["number"])


def _read_is_draft(pr: int) -> bool:
    """Read the PR's current isDraft bit via gh (coerced to bool)."""
    return bool(_gh_json(["pr", "view", str(pr), "--json", "isDraft"])["isDraft"])


# Bounded settle-retry for the post-correction confirm read. gh's draft bit is
# eventually-consistent (the exact flakiness this guard exists for — see the
# module docstring), so an immediate read right after `gh pr ready [--undo]` can
# still return the pre-mutation value; a single trusting read would then report
# a correction that actually succeeded as a failure (ok=False → exit 2), falsely
# blocking the very merge/draft flow the feature protects. Re-read a few times,
# accepting as soon as the bit reflects the wanted state.
_CONFIRM_RETRIES = 3
_CONFIRM_DELAY_S = 1.0


def assert_draft_state(
    pr: int,
    *,
    want_draft: bool,
    confirm_retries: int = _CONFIRM_RETRIES,
    confirm_delay_s: float = _CONFIRM_DELAY_S,
) -> dict:
    """Ensure PR `pr` has isDraft == want_draft, correcting a drifted bit once.

    Reads isDraft; if it already matches, returns without a correction. If it
    drifted, issues the corrective gh command (`gh pr ready --undo <pr>` to make
    it a draft, `gh pr ready <pr>` to make it ready) — which is idempotent, so a
    stale initial read that drove a redundant call is harmless — then re-reads to
    confirm with a bounded settle-retry (gh's draft bit can lag the mutation).
    Returns a report dict: {pr, want_draft, initial_draft, corrected: bool,
    final_draft, ok: bool}. `ok` is True iff final_draft == want_draft.
    """
    initial_draft = _read_is_draft(pr)
    corrected = initial_draft != want_draft
    final_draft = initial_draft
    if corrected:
        if want_draft:
            _gh(["pr", "ready", str(pr), "--undo"])
        else:
            _gh(["pr", "ready", str(pr)])
        # Confirm with a bounded settle-retry rather than one trusting read.
        for attempt in range(confirm_retries):
            final_draft = _read_is_draft(pr)
            if final_draft == want_draft:
                break
            if attempt < confirm_retries - 1:
                time.sleep(confirm_delay_s)
    return {
        "pr": pr,
        "want_draft": want_draft,
        "initial_draft": initial_draft,
        "corrected": corrected,
        "final_draft": final_draft,
        "ok": final_draft == want_draft,
    }


# ------------------------------------------------------------------- pure logic


def summarize_checks(rollup: list[dict], *, require_ci: bool | None = None) -> dict:
    """Collapse a statusCheckRollup into counts + the list of failing checks.

    Informational status contexts (``_INFORMATIONAL_CHECK_NAMES``, e.g.
    CodeRabbit) are excluded from the blocking tally — they never count toward
    ``pending`` / ``failing``.

    ``require_ci`` (default: ``review.require_ci`` from config, itself default
    ``True``) decides whether ``all_green`` additionally demands at least one
    real, non-informational check:

    - ``True`` — a PR with zero blocking checks is **not** green. This is the
      safe default: it stops an autonomous merge on a PR whose CI never ran.
    - ``False`` — a zero-check PR can be green. Needed for a repo with no CI at
      all, where the ``blocking_total > 0`` clause otherwise makes ``converged``
      unreachable forever, so the watch loop never terminates and
      ``dev_session.sh merge`` always refuses.

    ``False`` does not remove the quality gate: :func:`decide_mergeable`
    separately requires an independent-review receipt bound to the *current*
    head, so on a CI-less repo that receipt becomes the only gate — which is why
    the flag is opt-in per repo rather than inferred from an empty rollup.
    """
    if require_ci is None:
        require_ci = _REQUIRE_CI
    terminal_ok = {"SUCCESS", "NEUTRAL", "SKIPPED"}
    bad = {
        "FAILURE",
        "ERROR",
        "CANCELLED",
        "TIMED_OUT",
        "ACTION_REQUIRED",
        "STARTUP_FAILURE",
    }
    success = pending = informational = informational_non_green = 0
    failing: list[dict] = []
    for c in rollup:
        status = (c.get("conclusion") or c.get("state") or "").upper()
        name = c.get("name") or c.get("context") or "check"
        if name.strip().lower() in _INFORMATIONAL_CHECK_NAMES:
            informational += 1
            if status not in terminal_ok:
                informational_non_green += 1
            continue  # advisory only — never blocks "done"
        if status in terminal_ok:
            success += 1
        elif status in bad:
            failing.append({"name": name, "status": status})
        else:  # "", PENDING, QUEUED, IN_PROGRESS, EXPECTED, …
            pending += 1
    blocking_total = len(rollup) - informational
    return {
        "total": len(rollup),
        "success": success,
        "pending": pending,
        "informational": informational,
        "informational_non_green": informational_non_green,
        "failing": failing,
        "all_green": (
            not failing
            and pending == 0
            and (blocking_total > 0 or not require_ci)
        ),
    }


def _comment_key(kind: str, raw: dict) -> str:
    """Stable id for a comment across rounds. Prefer the platform id; else hash."""
    ident = raw.get("id")
    if ident in (None, ""):
        basis = f"{raw.get('createdAt') or raw.get('created_at')}|{_author(raw)}|{(raw.get('body') or '')[:80]}"
        # usedforsecurity=False: this is a dedup key, not a security hash (satisfies bandit B324 + ruff S324)
        ident = hashlib.sha1(basis.encode(), usedforsecurity=False).hexdigest()[:12]
    return f"{kind}:{ident}"


def _content_key(kind: str, author: str, body: str) -> str:
    """Content-addressed dedup key — survives an id/updated_at change on the same finding.

    A review bot may re-review after every fix push: it edits the inline
    comment (which bumps ``updated_at`` and can re-home the line) or posts a
    fresh review submission, so the *platform id* changes while the finding
    text is unchanged — and an id-keyed seen-set would report it as new again
    (each finding read twice). Keying additionally on the normalized body
    (case- and whitespace-folded, line number deliberately excluded — that's
    metadata, not content) lets :func:`new_actionable` treat a byte-identical
    re-post as already handled. A *materially* changed body (e.g. the bot
    marking it addressed) hashes differently and correctly re-surfaces.
    """
    normalized = " ".join((body or "").split()).lower()
    basis = f"{kind}|{author}|{normalized}"
    # usedforsecurity=False: dedup key, not a security hash (bandit B324 + ruff S324)
    return f"content:{hashlib.sha1(basis.encode(), usedforsecurity=False).hexdigest()[:16]}"


def _author(raw: dict) -> str:
    a = raw.get("author") or raw.get("user") or {}
    if isinstance(a, dict):
        return a.get("login") or a.get("name") or "?"
    return str(a)


def review_unavailable_reason(body: str) -> str | None:
    low = (body or "").lower()
    return next(
        (marker for marker in _REVIEW_UNAVAILABLE_MARKERS if marker in low), None
    )


def is_noise(body: str) -> bool:
    low = (body or "").lower()
    if review_unavailable_reason(body) is not None:
        return False
    return any(marker in low for marker in _NOISE_MARKERS)


def collect_comments(view: dict, inline: list[dict]) -> list[dict]:
    """Union issue comments + review submissions + inline review comments.

    Each returned dict: ``{key, kind, author, path, line, body}``. The three
    surfaces use different id namespaces, so keying by ``kind:id`` is what stops
    an inline finding from being mistaken for an already-seen issue comment.
    """
    out: list[dict] = []
    for raw in view.get("comments") or []:
        body = raw.get("body") or ""
        unavailable = review_unavailable_reason(body)
        out.append(
            {
                "key": _comment_key("issue", raw),
                "content_key": _content_key("issue", _author(raw), body),
                "kind": "issue",
                "author": _author(raw),
                "path": None,
                "line": None,
                "body": body,
                "review_unavailable_reason": unavailable,
            }
        )
    for raw in view.get("reviews") or []:
        body = raw.get("body") or ""
        if not body.strip():  # an approve/comment with no text carries no finding
            continue
        out.append(
            {
                "key": _comment_key("review", raw),
                "content_key": _content_key("review", _author(raw), body),
                "kind": "review",
                "author": _author(raw),
                "path": None,
                "line": None,
                "body": body,
                "review_unavailable_reason": review_unavailable_reason(body),
            }
        )
    for raw in inline or []:
        body = raw.get("body") or ""
        out.append(
            {
                "key": _comment_key("inline", raw),
                "content_key": _content_key("inline", _author(raw), body),
                "kind": "inline",
                "author": _author(raw),
                "path": raw.get("path"),
                "line": raw.get("line") or raw.get("original_line"),
                "body": body,
                "review_unavailable_reason": review_unavailable_reason(body),
            }
        )
    return out


def new_actionable(comments: list[dict], seen: set[str]) -> list[dict]:
    """Comments that are new and not auto-noise.

    A comment is "new" only when BOTH its platform-id key and its content key are
    absent from ``seen`` — so a review bot's re-review that re-posts the same
    finding under a fresh id (or an edit that bumps ``updated_at`` / re-homes
    the line) is recognized as already handled instead of read twice.
    """
    return [
        c
        for c in comments
        if c["key"] not in seen
        and c["content_key"] not in seen
        and not is_noise(c["body"])
    ]


def _match_bot(text: str, bots: tuple[str, ...], *, anchored: bool = False) -> str | None:
    """The configured review bot named in ``text``, if any. Case-insensitive.

    Substring by default: one bot key (``coderabbit``) has to cover the check
    name GitHub shows (``CodeRabbit``), a namespaced variant (``Review /
    CodeRabbit``), and the comment author (``coderabbitai``), which no exact
    match spans.

    ``anchored`` requires the text to START with the bot key, and is used for
    comment authors because that input is not the repo's to control: on a public
    repo any account may comment, and an unrelated login merely *containing*
    ``coderabbit`` (``xcoderabbit``) should not be read as the reviewer. Check
    names come from the repo's own CI and bot configuration, so the looser match
    is appropriate there. Different rules because the inputs have different
    trust, not by oversight.
    """
    low = str(text or "").strip().lower()
    if not low:
        return None
    if anchored:
        return next((bot for bot in bots if low.startswith(bot)), None)
    return next((bot for bot in bots if bot in low), None)


# Check states that mean the reviewer has finished — anything else (PENDING,
# QUEUED, IN_PROGRESS, EXPECTED, "") means a verdict may still be coming.
_TERMINAL_CHECK_STATES = {
    "SUCCESS",
    "NEUTRAL",
    "SKIPPED",
    "FAILURE",
    "ERROR",
    "CANCELLED",
    "TIMED_OUT",
    "ACTION_REQUIRED",
    "STARTUP_FAILURE",
}


def _check_is_pending(detail: dict) -> bool:
    """Whether one ``gh pr checks`` row is still awaiting a verdict.

    Prefers gh's own ``bucket`` (its normalization across ``CheckRun`` and
    ``StatusContext``); falls back to the raw state when a gh version omits it.
    A row carrying *neither* reads as pending — fail-closed, so a truncated row
    whose name matches a bot holds the merge gate for the grace window rather
    than waving it through.
    """
    bucket = (detail.get("bucket") or "").strip().lower()
    if bucket:
        return bucket == "pending"
    return (detail.get("state") or "").strip().upper() not in _TERMINAL_CHECK_STATES


# How far ahead of `now` a timestamp may sit and still be believed. Small skew
# between GitHub's clock and ours is normal on a just-created check; a value
# genuinely in the future is not a clock, it is corruption — and one that
# `max(0.0, …)` would clamp to age 0 forever while re-persisting itself.
_FUTURE_SKEW_TOLERANCE_MINUTES = 2.0


def _age_minutes(timestamp: str | None, now: datetime) -> float | None:
    """Minutes between ``timestamp`` (ISO 8601) and ``now``; ``None`` if unusable.

    GitHub stamps an unstarted check with the zero time (``0001-01-01T…``), which
    parses fine but means "no time recorded" — treated as unknown, not as an age
    of two millennia. That is not an edge case: CodeRabbit's pending status
    context reports exactly that, so the caller must always have a fallback
    clock (see ``pending_since`` in :func:`summarize_review_bots`).
    """
    if not timestamp:
        return None
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed.year < 2000:
        return None
    age = (now - parsed).total_seconds() / 60.0
    if age < -_FUTURE_SKEW_TOLERANCE_MINUTES:
        # Meaningfully in the future: unusable, NOT age 0. Clamping it would pin
        # the grace clock at its most-blocking value while the caller re-persists
        # the same future stamp every poll — the block would then last until real
        # time caught up with it. Reachable from a state file copied between
        # machines, or a VM clock that ran ahead and was then NTP-corrected.
        return None
    return max(0.0, age)


def bot_review_coverage(
    reviews: list[dict],
    head: str | None,
    *,
    bots: tuple[str, ...] | None = None,
) -> list[dict]:
    """Which commit each configured bot's LAST review actually covered.

    A receipt binds to the current head and a push invalidates it, which answers
    "was this exact code reviewed" — but not "by whom, and how much of it did
    they see". A bot can review commit 1, go rate-limited through a material
    redesign, and the merge still proceed on a fallback receipt taken at commit
    5. That happened on #22 (a fail-open rework the primary reviewer never saw)
    and again, smaller, on #25.

    This does not gate anything. It makes the gap *visible at merge time*
    instead of reconstructible only by reading the PR thread afterwards —
    deliberately the cheap half of issue #27, because the expensive half
    (invalidating a receipt when the diff changes shape) risks becoming a wedge
    on a repo whose bot is permanently unavailable.

    Returns one entry per bot with at least one review carrying a usable commit
    SHA, newest first: ``{bot, sha, submitted_at, covers_head}``. A bot whose
    reviews all lack one is indistinguishable here from a bot that never
    reviewed — the under-reporting direction, chosen because claiming coverage
    of an unknown commit would be worse than claiming none.

    Recency is a lexicographic compare on GitHub's ISO timestamps, which is
    correct only because ``gh`` emits fixed-width ``Z``-suffixed UTC with no
    fractional seconds (``2026-07-25T12:29:16Z``). An offset form or a
    fractional second would sort wrong; neither is reachable from ``gh``. Ties
    resolve to the later array element, matching gh's ascending submission
    order — and an undated review can never displace a dated one, which is the
    direction that matters: an undated review sitting at the head would
    otherwise set ``covers_head`` and suppress the warning.
    """
    if bots is None:
        bots = _REVIEW_BOTS
    latest: dict[str, dict] = {}
    for raw in reviews or []:
        # Anchored: a comment author is not the repo's to control, so a
        # lookalike login (`xcoderabbit`) must not be able to claim that the
        # reviewer covered this head.
        bot = _match_bot(_author(raw), bots, anchored=True)
        if not bot:
            continue
        commit = raw.get("commit")
        sha = commit.get("oid") if isinstance(commit, dict) else None
        # Type-checked, not just truthy: a non-string `oid` survives an
        # `isinstance(commit, dict)` guard and then kills `render` on
        # `sha[:7]` — on the ordinary poll path, for a field this is supposed
        # to be tolerant of.
        if not isinstance(sha, str) or not sha:
            continue
        # Type-checked, NOT coerced. `str(...)` is equally crash-proof and
        # actively wrong: it renders garbage as a string that sorts ABOVE every
        # real timestamp (`"20260725" > "2026-07-25T…"`, `"{'x': 1}" >`
        # anything), so a malformed review at the head displaces the real dated
        # one and sets `covers_head` — suppressing the very warning this exists
        # to raise. Unusable timestamps must sort to the BOTTOM, exactly like
        # the missing ones below.
        submitted = raw.get("submittedAt")
        submitted = submitted if isinstance(submitted, str) else ""
        if bot not in latest or submitted >= latest[bot]["submitted_at"]:
            latest[bot] = {
                "bot": bot,
                "sha": sha,
                "submitted_at": submitted,
                "covers_head": sha == head,
            }
    return sorted(latest.values(), key=lambda e: e["submitted_at"], reverse=True)


def summarize_review_bots(
    check_details: list[dict],
    comments: list[dict],
    *,
    now: datetime,
    bots: tuple[str, ...] | None = None,
    grace_minutes: float | None = None,
    pending_since: dict | None = None,
    signal: str = "ok",
    reviews: list[dict] | None = None,
    head: str | None = None,
) -> dict:
    """Resolve each configured review bot to *unavailable*, *pending*, or neither.

    This is the single predicate issues #19 and #23 both needed. They are two
    branches of one question — "has the independent reviewer had its say?" — and
    the reason neither could be fixed alone is that the obvious local fix for
    each ("let the bot's check block") is the one move the design forbids: that
    check is excluded from the blocking tally precisely so a bot which never
    reports cannot wedge the watch loop forever.

    The way out is that **nothing here touches** :func:`decide_converged`. The
    anti-wedge property lives entirely in that predicate, and it is left alone.
    Everything below feeds only the merge gate, which already requires someone to
    explicitly record a review receipt — so tightening it can delay a merge but
    can never stall the poll/fix/ack loop.

    The three outcomes:

    - **unavailable** — an ``unavailable_markers`` hit on either surface: a
      comment body (already detected today) *or* a bot check's description (#23,
      the surface that was invisible). Never blocks anything. It is an action
      signal: run the configured fallback review.

      Only a **check**-surface hit suppresses the pending block below. A check
      describes the bot's state now; a comment describes the past, and
      ``collect_comments`` returns the entire PR history unscoped by head or
      age — so letting a comment cancel would mean one transient rate limit on
      commit 1 waves through every queued review for the rest of the PR. Since
      rate limits are transient by construction, that is the ordinary case, not
      a corner one. A comment-surface outage is reported and nothing more; the
      bot's check is what says whether it is still working.
    - **pending** — the bot's own check is non-terminal and no unavailability was
      announced. A verdict is genuinely coming, so a receipt recorded now would
      be premature (#19: exactly this, on #16, let four valid findings land after
      the merge). Blocks the merge gate — but only while the check is younger
      than ``grace_minutes``, so a permanently-stuck check ages out instead of
      wedging.
    - **neither** — terminal and unmarked: the bot reviewed. Nothing to add.

    **The grace clock cannot come from the check alone.** CodeRabbit's pending
    status context reports ``startedAt: 0001-01-01T00:00:00Z`` — the zero time,
    i.e. no timestamp — so an implementation that only reads the check has no
    age to compare and quietly stops guarding the one bot it was written for.
    (Observed on this very PR: the first cut of this function printed "age
    unmeasurable, NOT blocking" against a live CodeRabbit review-in-progress.)

    ``pending_since`` is the fallback clock: a ``{bot: iso8601}`` map of when
    THIS engine first saw that bot pending at the current head, threaded through
    per-PR state by the caller. An unseen bot is recorded at ``now`` and so
    starts at age 0 — blocking, and ageing normally from there. Because the
    clock is ours and only ever advances, every pending bot reaches the grace
    bound and stops blocking; there is no unmeasurable case left to fail open on.
    The map is scoped to a head: a push means a fresh review, so the caller
    resets it.

    Returns ``{grace_minutes, signal, coverage, unavailable, pending, blockers,
    pending_since}``. ``coverage`` is :func:`bot_review_coverage` over
    ``reviews``/``head`` — which commit each bot's last review actually saw.
    ``blockers`` are ready-made ``merge_blockers`` strings; ``pending_since`` is
    the updated map for the caller to persist.

    ``unavailable[].bot`` is ``None`` when a comment matched a marker but its
    author matches no configured bot — a human writing "review skipped" in a PR
    comment. Reported (the operator should see it) and attributed to nobody, so
    it can never suppress anything.

    ``signal`` distinguishes three states a bare empty result cannot: ``"ok"``
    (checks were read), ``"skipped"`` (no bots configured — nothing to read),
    and ``"unavailable"`` (the read failed, so both guards are off). Without it
    a failed fetch is byte-identical to a genuinely clean bot, and the merge gate
    consumes JSON on stdout — a stderr warning is not readable by
    ``dev_session.sh merge``.
    """
    if bots is None:
        bots = _REVIEW_BOTS
    if grace_minutes is None:
        grace_minutes = _BOT_PENDING_GRACE_MINUTES
    observed: dict[str, str] = dict(pending_since or {})

    unavailable: list[dict] = []
    unavailable_bots: set[str] = set()

    # Surface 1 — comment bodies. Already detected today, but only ever per
    # comment: once acked it vanished from `new_comments` and with it the fact
    # that the primary reviewer never ran. Aggregating it here keeps the gap
    # visible at merge time.
    #
    # Reported, NOT counted toward `unavailable_bots`. `collect_comments` returns
    # the whole PR history, unscoped by head or age, so an outage comment from
    # commit 1 would otherwise cancel the pending block on commit 5 — and rate
    # limits are transient by construction, which makes "this bot was
    # rate-limited earlier on this PR" the *normal* state of a later poll. That
    # would be issue #19 walking back in through the door built to close it.
    # A check is a statement about the bot's state NOW; a comment is a statement
    # about the past. Only the former may cancel (surface 2 below).
    for comment in comments or []:
        reason = comment.get("review_unavailable_reason")
        if not reason:
            continue
        author = comment.get("author") or "?"
        unavailable.append(
            {
                "bot": _match_bot(author, bots, anchored=True),
                "surface": "comment",
                "where": f"@{author}",
                "reason": reason,
            }
        )

    # Surface 2 — the bot's own check description. Issue #23: on PR #22 this was
    # the ONLY place the rate limit appeared, and it read as a clean review.
    pending: list[dict] = []
    exact_ages: list[float] = []
    for detail in check_details or []:
        name = str(detail.get("name") or detail.get("context") or "")
        bot = _match_bot(name, bots)
        if not bot:
            continue
        reason = review_unavailable_reason(detail.get("description") or "")
        if reason:
            unavailable.append(
                {
                    "bot": bot,
                    "surface": "check",
                    "where": name,
                    "reason": reason,
                }
            )
            unavailable_bots.add(bot)
            continue
        if not _check_is_pending(detail):
            continue
        # Our own clock wins whenever we already have one. Preferring the
        # check's stamp would let the age REGRESS: a stamp a few minutes ahead of
        # our clock reads as unusable at first (so we start observing), then
        # slides inside the skew tolerance a few minutes later and reads as age
        # 0 — restarting the window after it had already aged out, and making
        # `merge_blockers` non-monotonic in wall-clock time.
        age = _age_minutes(observed.get(bot), now)
        since = observed.get(bot)
        source = "observed"
        if age is None:
            age = _age_minutes(detail.get("startedAt"), now)
            since = detail.get("startedAt")
            source = "check"
        if age is None:
            # Neither usable — start our own clock now. A stored value that will
            # not parse is REPLACED, not coerced to age 0: `age = parse(x) or
            # 0.0` would pin it at the maximally-blocking age *and* write it
            # back, so every later poll re-read the same poison and the gate
            # blocked forever. Same for a value dated in the future, which is
            # parseable and would otherwise block until real time caught up.
            since = now.isoformat()
            age = 0.0
            source = "observed"
        if source == "observed":
            observed[bot] = since
        pending.append(
            {
                "bot": bot,
                "check": name,
                "state": (detail.get("state") or "").upper(),
                "since": since,
                "age_source": source,
                # Rounded for display only — the grace comparison below uses the
                # exact value, so a 14.96m check does not round its way past a
                # 15m bound.
                "age_minutes": round(age, 1),
                "blocking": False,
                "cancelled_by": None,
            }
        )
        exact_ages.append(age)

    blockers: list[str] = []
    # strict=True: the two lists are appended in lockstep in the loop above, and
    # a future edit that adds a `continue` between them would otherwise pair
    # each entry with the WRONG age — silently, and only for a bot with more
    # than one pending check.
    for entry, exact_age in zip(pending, exact_ages, strict=True):
        if entry["bot"] in unavailable_bots:
            # This bot's own CHECK announced an outage: it is not going to move
            # off pending, so waiting on it is a wedge with extra steps.
            entry["cancelled_by"] = "outage"
            continue
        if exact_age >= grace_minutes:
            entry["cancelled_by"] = "grace"
            continue
        entry["blocking"] = True
        blockers.append(
            f"review bot {entry['bot']} has not reported yet "
            # The exact age, not the display-rounded one: `pending 15.0m < 15m
            # grace` is a true statement rendered as a self-contradiction.
            f"(check {entry['check']} pending {exact_age:.2f}m "
            f"< {grace_minutes:g}m grace)"
        )

    return {
        "grace_minutes": grace_minutes,
        "signal": "skipped" if not bots else signal,
        # Per-bot last-reviewed SHA — see :func:`bot_review_coverage`. Computed
        # here rather than passed in, so every caller gets it: as a parameter it
        # arrived EMPTY on the `record_review` path, where "no data" and "every
        # bot is current" were indistinguishable — on the one path whose whole
        # subject is what a receipt covers. Reported, never gating.
        "coverage": bot_review_coverage(reviews or [], head, bots=bots),
        "unavailable": unavailable,
        "pending": pending,
        "blockers": blockers,
        # Only the bots still pending: an entry for a bot that has since
        # reported would otherwise keep a stale clock alive across polls, and a
        # later re-review would inherit an already-expired window.
        "pending_since": {
            bot: at
            for bot, at in observed.items()
            if bot in {entry["bot"] for entry in pending}
        },
    }


def decide_converged(
    checks: dict,
    new_items: list[dict],
    *,
    settling: bool = False,
) -> bool:
    """Converged = green, nothing left to act on, and not mid-settle.

    The **watch-loop** predicate: it answers "is there more for me to fix?",
    which is the only question the poll/fix/mark-seen loop needs. It deliberately
    does NOT mean "safe to merge" — see :func:`decide_mergeable`.

    This exists because merge authorization used to be the *only* thing a caller
    could ask for. A loop that has genuinely finished still reported not-done
    until someone recorded a review receipt, which (a) wedges any caller that
    watches to convergence without recording one, and (b) pressures the operator
    into recording a receipt early just to terminate the loop — exactly the
    premature-receipt failure tracked in issue #19.

    ``settling`` is set right after a push (the PR head SHA moved, or the rollup
    is smaller than the largest seen for this head — new checks not yet
    registered), so a poll can't false-settle on the *stale pre-push* rollup
    (an all-green old commit) before the new commit's CI even starts.
    """
    return checks["all_green"] and not new_items and not settling


def decide_mergeable(
    converged: bool,
    *,
    merge_blockers: list[str] | None = None,
    review_evidence: bool = False,
) -> bool:
    """Mergeable = the watch loop converged AND the merge is authorized.

    Strictly stronger than :func:`decide_converged`: a PR must first have nothing
    left to act on, and additionally carry no deterministic merge blocker (draft,
    non-open, blocked merge state, changes requested) and an independent-review
    receipt bound to the *current* head.

    This is what an autonomous self-merge gates on (``dev_session.sh merge``).

    The result is coerced to ``bool`` deliberately: a bare ``and`` chain returns
    its last operand, so a truthy non-bool ``review_evidence`` would propagate
    into the report — and ``dev_session.sh merge`` tests the JSON value with an
    identity check (``is True``), which such a value fails *closed* but
    confusingly. A safety gate should not depend on every caller passing a real
    bool.
    """
    return bool(converged and not merge_blockers and review_evidence)


def decide_done(
    checks: dict,
    new_items: list[dict],
    *,
    merge_blockers: list[str] | None = None,
    review_evidence: bool = False,
    settling: bool = False,
) -> bool:
    """Legacy name for :func:`decide_mergeable`. Semantics UNCHANGED.

    ``done`` predates the split of the watch-loop predicate from the merge-gate
    predicate, and has always meant "green, independently reviewed, merge-ready,
    and not mid-settle". This function keeps that meaning exactly, for any Python
    caller that imported it.

    **Do not read a compatibility guarantee into this function.** The thing that
    protects an older ``dev_session.sh`` is the report's ``done`` **key** (see
    the assignment in :func:`build_report`), because that gate shells out to
    ``pr_watch.py --json`` and never imports this module. This function has no
    in-engine caller. Deleting the key while keeping this function would remove
    the protection entirely.

    Prefer :func:`decide_converged` / :func:`decide_mergeable` in new code.
    """
    return decide_mergeable(
        decide_converged(checks, new_items, settling=settling),
        merge_blockers=merge_blockers,
        review_evidence=review_evidence,
    )


# ------------------------------------------------------------------ state I/O


def _seen_path(pr: int) -> Path:
    return STATE_DIR / f"{pr}.json"


def read_pending_since(state: dict, head: str | None) -> dict:
    """The persisted grace clock, but only if it belongs to ``head``.

    Stored as ``{"head": sha, "bots": {bot: iso}}`` — self-describing rather than
    scoped by the sibling ``state["head"]``. That field is the false-settle
    guard's input, written by :func:`persist_poll` on every poll; making a second
    writer (:func:`record_review`) maintain it just to scope this clock would put
    two different intents on one key, and the guard it feeds decides whether a
    just-pushed commit can settle. A push means a fresh review, so a clock from
    another head is discarded, not aged.
    """
    stored = state.get("bot_pending_since")
    if not isinstance(stored, dict) or not head or stored.get("head") != head:
        return {}
    bots = stored.get("bots")
    return bots if isinstance(bots, dict) else {}


def write_pending_since(state: dict, head: str | None, bots: dict) -> dict:
    """Set the head-scoped grace clock on ``state`` (dropping an empty one)."""
    if bots and head:
        state["bot_pending_since"] = {"head": head, "bots": bots}
    else:
        state.pop("bot_pending_since", None)
    return state


def load_state(pr: int) -> dict:
    """Full per-PR watch state (missing/corrupt → {}).

    Keys: ``seen`` (acked comment keys), ``head`` / ``max_total`` (false-settle
    guard, see :func:`build_report`), ``bot_pending_since`` (the head-scoped
    fallback grace clock for a review bot whose check carries no usable
    timestamp, see :func:`read_pending_since`), and ``pending_seen`` — the ``all_seen_keys``
    of the most recently *reported* plain poll, present only between a poll and
    the ``--mark-seen`` that consumes it (see :func:`mark_seen`).
    """
    path = _seen_path(pr)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(pr: int, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _seen_path(pr).write_text(
        json.dumps(state, indent=1, sort_keys=True), encoding="utf-8"
    )


def load_seen(pr: int) -> set[str]:
    return set(load_state(pr).get("seen", []))


def save_seen(pr: int, seen: set[str]) -> None:
    # Merge into the existing file so the head/max_total tracking survives.
    state = load_state(pr)
    state["seen"] = sorted(seen)
    save_state(pr, state)


def mark_seen(pr: int) -> dict:
    """Promote the PENDING set from the last *reported* poll into ``seen``.

    Deliberately does **not** talk to ``gh``. It reads ``state["pending_seen"]`` —
    the exact ``all_seen_keys`` a prior plain poll (any invocation without
    ``--mark-seen``) persisted — unions it into ``seen``, and clears the pending
    slot. A comment posted after that poll and before this call was never fetched
    into ``pending_seen``, so it structurally cannot be acked here: it stays
    unseen and re-surfaces on the next poll instead of being silently buried by
    a fresh re-poll's superset (the ordering hazard this replaces).

    If no poll has been reported since the last ack — ``pending_seen`` absent
    (a "cold" call, or state that was never a dict's list, e.g. corrupt) — acks
    nothing and returns a ``note`` explaining why, rather than re-deriving an ack
    set from a fresh fetch. Calling this twice in a row (no intervening poll) is
    a no-op the second time: idempotent, not an error.

    Returns ``{pr, marked_seen: True, marked_seen_keys, note?}``.
    """
    state = load_state(pr)
    pending = state.get("pending_seen")
    if not isinstance(pending, list):
        return {
            "pr": pr,
            "marked_seen": True,
            "marked_seen_keys": [],
            "note": "no pending poll to acknowledge — run a poll (without --mark-seen) first",
        }

    seen = set(state.get("seen", [])) | set(pending)
    state["seen"] = sorted(seen)
    state.pop("pending_seen", None)
    save_state(pr, state)
    return {"pr": pr, "marked_seen": True, "marked_seen_keys": sorted(pending)}


def record_review(
    pr: int,
    source: str,
    expected_head: str,
    *,
    allow_pending_bot: bool = False,
    now: datetime | None = None,
) -> dict:
    """Persist independent-review evidence bound to the PR's current head SHA.

    The caller runs this only after an independent reviewer (the configured bot,
    or the configured fallback when that bot is unavailable) has completed and
    every finding has been handled. A later push changes ``headRefOid`` and
    automatically invalidates the receipt.

    **Refuses while a configured review bot's own verdict is still coming.** This
    is the moment issue #19's failure happened: on #16 a fallback receipt was
    recorded while CodeRabbit's check read ``PENDING — Review queued``, the merge
    fired, and its four valid findings landed minutes later. Every input was
    correct at that instant; the missing one was the reviewer's own state. The
    judgment the doctrine asks for — *is this bot unavailable, or merely slow?* —
    is made right here, so this is where it gets mechanized.

    It refuses only for a bot that is genuinely mid-review. An outage announced
    on the bot's own **check** means "not coming" and goes straight through to
    the fallback; a check pending past the grace window ages out of blocking. An
    outage announced only in a *comment* does NOT clear the refusal — comments
    are unscoped PR history, so a stale one would wave through a live review (see
    :func:`summarize_review_bots`) — but the grace window bounds that wait to
    minutes. ``allow_pending_bot`` is the operator's documented override for the
    remaining case: evidence the queued review will never arrive that pr_watch
    cannot see. It is recorded on the receipt, as is a failed check read (but
    not "no bots configured" — nothing was unreadable in that case).
    """
    source = source.strip()
    if not source:
        raise ValueError("review source must not be empty")
    expected_head = expected_head.strip()
    if not expected_head:
        raise ValueError("expected reviewed head must not be empty")
    snapshot = _gh_json(
        ["pr", "view", str(pr), "--json", "number,headRefOid,reviews"]
    )
    current_head = snapshot.get("headRefOid")
    if not current_head:
        raise ValueError("PR has no headRefOid; cannot bind review evidence")
    if current_head != expected_head:
        raise ValueError(
            f"PR head changed during review (expected {expected_head}, current {current_head}); "
            "review the new head before recording evidence"
        )
    now = now or datetime.now(timezone.utc)
    state = load_state(pr)
    # Stays "ok" under an explicit override: `override` already records that the
    # bot state was deliberately not consulted, so a second key would be noise.
    bot_signal = "ok"
    # Computed BEFORE the override branch, and independently of the check fetch:
    # it comes from the `pr view` snapshot. Populating it inside
    # `if not allow_pending_bot` made the receipt silent on exactly the path this
    # exists for — the override IS the #22/#25 scenario, a bot queued or
    # rate-limited through a redesign and merged on a fallback receipt.
    behind = [
        e
        for e in bot_review_coverage(snapshot.get("reviews") or [], current_head)
        if not e["covers_head"]
    ]
    if not allow_pending_bot:
        # Checks only. Comments cannot cancel a pending block (see
        # :func:`summarize_review_bots`), so fetching them here would cost a
        # round trip to compute nothing — and would give this path a different
        # view of the same predicate than the poll has.
        details = fetch_check_details(pr)
        bot_status = summarize_review_bots(
            details.rows,
            [],
            now=now,
            pending_since=read_pending_since(state, current_head),
            signal=details.signal,
            reviews=snapshot.get("reviews") or [],
            head=current_head,
        )
        bot_signal = bot_status["signal"]
        if bot_status["blockers"]:
            # Persist the first sighting BEFORE refusing. Without this, a cold
            # `--record-review` (no poll loop running) restarts the grace clock
            # at zero on every retry, so the refusal could never expire and the
            # override would be the only way through — a wedge dressed as a guard.
            write_pending_since(state, current_head, bot_status["pending_since"])
            save_state(pr, state)
            raise ValueError(
                "; ".join(bot_status["blockers"])
                + ". A receipt recorded now would bind to a review that has not happened "
                "— wait for the bot, or pass --allow-pending-bot-review if you have "
                "evidence its verdict will never arrive"
            )
    receipt = {
        "head": expected_head,
        "source": source,
        "recorded_at": now.isoformat(),
    }
    if allow_pending_bot:
        # The escape hatch on a safety gate is the one thing that must leave a
        # trace. Without it, a receipt taken over an active override is
        # indistinguishable from one taken after a clean bot verdict.
        receipt["override"] = "pending-bot"
    if bot_signal == "unavailable":
        # The SILENT bypass, and the worse of the two: when the check read fails
        # there are no blockers to raise, so the receipt is taken with the #19
        # guard simply switched off. Recording an explicit override but not this
        # would leave the deliberate escape auditable and the accidental one
        # invisible. Not a refusal — a `gh` too old for these fields, or a PR
        # with no checks at all, is an environment problem, and refusing would
        # turn it into a wedge with no way out but the override flag.
        #
        # `"skipped"` (no bots configured) is deliberately NOT recorded: nothing
        # was unreadable and there was no guard to run, so flagging it would put
        # a permanent false warning on every receipt a bot-less adopter takes.
        receipt["bot_signal"] = bot_signal
    if behind:
        # The sibling of `override` and `bot_signal`: all three record what this
        # receipt does NOT stand for. Its own message says "a receipt taken now
        # does not mean it saw this design" — which was printing everywhere
        # except where a receipt is taken.
        receipt["bots_behind_head"] = {e["bot"]: e["sha"] for e in behind}
    state["review_receipt"] = receipt
    save_state(pr, state)
    return {"pr": pr, "recorded_review": True, "review_receipt": receipt}


# ----------------------------------------------------------------------- main


def _excerpt(body: str, n: int = 140) -> str:
    flat = " ".join((body or "").split())
    return flat if len(flat) <= n else flat[: n - 1] + "…"


def build_report(
    view: dict,
    inline: list[dict],
    seen: set[str],
    *,
    prior_head: str | None = None,
    prior_max_total: int = 0,
    review_receipt: dict | None = None,
    check_details: list[dict] | CheckDetails | None = None,
    now: datetime | None = None,
    prior_pending_since: dict | None = None,  # already head-scoped by the caller
) -> dict:
    """Assemble the JSON-serializable watch report for one PR snapshot.

    Returns a dict with:

    - ``pr`` / ``url`` / ``state`` / ``is_draft`` / ``base`` / ``merge_state`` /
      ``review_decision`` — PR identity + merge/review state.
    - ``head`` — the PR head SHA (``headRefOid``); ``head_changed`` — true when it
      moved since ``prior_head``; ``max_total`` — the largest check count seen for
      this head (persisted across runs); ``settling`` — true while a just-pushed
      commit's checks are still registering (the false-settle guard; forces
      ``converged`` false). See :func:`decide_converged`.
    - ``checks`` — the :func:`summarize_checks` rollup (``total`` / ``success`` /
      ``pending`` / ``informational`` / ``failing`` / ``all_green``).
    - ``new_comments`` — only the *fresh, actionable* comments (not in ``seen``,
      not auto-noise), each as
      ``{kind, author, path, line, excerpt, body}``. ``excerpt`` is the truncated
      one-liner for the human render; ``body`` is the FULL text so a caller never
      needs a second ``gh api`` fetch for the suggested diff.
    - ``all_comment_keys`` — every current comment's platform-id key (back-compat).
    - ``all_seen_keys`` — the persistence set ``--mark-seen`` writes: BOTH the
      id key AND the content key of every current comment, so a later re-post
      under a new id stays handled.
    - ``review_evidence`` — whether a persisted independent-review receipt is
      bound to this exact head SHA.
    - ``review_bots`` — :func:`summarize_review_bots`: each configured review
      bot resolved to *unavailable* (an outage announced on either the comment
      or the check-description surface — an action signal, never a blocker) or
      *pending* (a verdict still coming, which blocks the merge gate until it
      ages past the grace window). Also carries ``coverage`` (which commit each
      bot's last review saw) and ``signal`` (whether that state could be read at
      all) — both reported, neither gating. Advisory to ``converged`` by
      construction.
    - ``merge_blockers`` — deterministic reasons the PR is not currently safe to
      merge (draft, blocked/unknown merge state, requested changes, non-open PR,
      missing current-head review evidence, or a configured review bot whose own
      verdict has not landed yet).
    - ``converged`` — :func:`decide_converged`: all checks green, no fresh
      comments, and not ``settling``. The **watch-loop** predicate: "is there
      more to fix?" A converged PR is NOT necessarily safe to merge.
    - ``mergeable`` — :func:`decide_mergeable`: ``converged`` AND no
      ``merge_blockers`` AND current-head review evidence. The **merge-gate**
      predicate, and what ``dev_session.sh merge`` re-checks at act time.
    - ``done`` — legacy alias, always equal to ``mergeable``. Kept so an older
      ``dev_session.sh`` reading ``done`` still gates on merge authorization
      rather than falling open; see :func:`decide_done`.
    """
    checks = summarize_checks(view.get("statusCheckRollup") or [])
    comments = collect_comments(view, inline)
    fresh = new_actionable(comments, seen)
    # A plain list is accepted so a test (or an embedder) can pass rows directly;
    # only a CheckDetails carries the "could we read them at all" signal.
    details = (
        check_details
        if isinstance(check_details, CheckDetails)
        else CheckDetails(list(check_details or []), "ok")
    )
    review_bots = summarize_review_bots(
        details.rows,
        comments,
        now=now or datetime.now(timezone.utc),
        pending_since=prior_pending_since or {},
        signal=details.signal,
        reviews=view.get("reviews") or [],
        head=view.get("headRefOid"),
    )

    # False-settle guard: right after a push, `gh` can still report the OLD
    # commit's all-green rollup before the new commit's checks register — so a
    # naive `all_green` would settle on stale CI (and an autonomous self-merge
    # could fire before the new commit's CI even starts). Track the head SHA +
    # the largest check count seen for it; "settling" while the head just moved,
    # or the rollup is smaller than that max (checks not all registered yet).
    head = view.get("headRefOid")
    head_changed = bool(prior_head) and head is not None and head != prior_head
    # On a head change, reset the baseline to the new commit's current count;
    # otherwise remember the largest count ever seen for this head.
    max_total = (
        checks["total"] if head_changed else max(prior_max_total, checks["total"])
    )
    settling = head_changed or checks["total"] < max_total

    pr_state = (view.get("state") or "UNKNOWN").upper()
    base = view.get("baseRefName")
    merge_state = (view.get("mergeStateStatus") or "UNKNOWN").upper()
    review_decision = (view.get("reviewDecision") or "").upper()
    receipt_head = (
        review_receipt.get("head") if isinstance(review_receipt, dict) else None
    )
    review_evidence = {
        "valid": bool(head) and receipt_head == head,
        "source": (
            review_receipt.get("source")
            if isinstance(review_receipt, dict) and receipt_head == head
            else None
        ),
        "head": receipt_head,
    }
    merge_blockers: list[str] = []
    if pr_state != "OPEN":
        merge_blockers.append(f"PR state is {pr_state}")
    if bool(view.get("isDraft")):
        merge_blockers.append("PR is draft")
    informational_only_unstable = (
        merge_state == "UNSTABLE"
        and checks["all_green"]
        and checks["informational_non_green"] > 0
    )
    if merge_state not in {"CLEAN", "HAS_HOOKS"} and not informational_only_unstable:
        merge_blockers.append(f"merge state is {merge_state}")
    if review_decision == "CHANGES_REQUESTED":
        merge_blockers.append("review decision is CHANGES_REQUESTED")
    if not review_evidence["valid"]:
        merge_blockers.append("independent review evidence is missing for current head")
    # Additive to the merge gate only. `done` is an alias of `mergeable`, so
    # these tighten `done` too — the safe skew direction: an older
    # `dev_session.sh` reading `done` merges LESS, never more.
    merge_blockers.extend(review_bots["blockers"])

    report = {
        "pr": view.get("number"),
        "url": view.get("url"),
        "state": pr_state,
        "is_draft": view.get("isDraft"),
        "base": base,
        "merge_state": merge_state,
        "review_decision": review_decision,
        "review_evidence": review_evidence,
        "review_bots": review_bots,
        "merge_blockers": merge_blockers,
        "head": head,
        "head_changed": head_changed,
        "settling": settling,
        "max_total": max_total,
        "checks": checks,
        "new_comments": [
            {
                "kind": c["kind"],
                "author": c["author"],
                "path": c["path"],
                "line": c["line"],
                "excerpt": _excerpt(c["body"]),
                "review_unavailable_reason": c.get("review_unavailable_reason"),
                # Full body too: handling a finding no longer needs a second
                # `gh api .../pulls/N/comments` fetch for the suggested diff.
                "body": c["body"],
            }
            for c in fresh
        ],
        "all_comment_keys": [c["key"] for c in comments],
        # Persistence set for --mark-seen: BOTH id and content keys, so a later
        # re-post under a new id is matched on content and stays handled.
        "all_seen_keys": sorted(
            {k for c in comments for k in (c["key"], c["content_key"])}
        ),
    }
    report["converged"] = decide_converged(checks, fresh, settling=settling)
    report["mergeable"] = decide_mergeable(
        report["converged"],
        merge_blockers=merge_blockers,
        review_evidence=review_evidence["valid"],
    )
    # Legacy alias, identical to `mergeable` — see :func:`decide_done` for why
    # this key must never be repurposed to mean watch-convergence.
    report["done"] = report["mergeable"]
    return report


def render(report: dict) -> str:
    ck = report["checks"]
    lines = [f"PR #{report['pr']} — {report['url']}"]
    # `converged` answers "anything left to fix?"; `mergeable` answers "safe to
    # merge?". Naming the converged-but-unauthorized state explicitly is the
    # point: it is the normal end of a watch loop, not a failure, and it must not
    # read as merge clearance.
    if not report.get("converged"):
        state = "⏳ not converged"
    elif report.get("mergeable"):
        state = "✅ DONE — green, reviewed, merge-ready"
    else:
        state = "✅ converged — green + clean · NOT mergeable (see merge blockers below)"
    if report.get("settling"):
        state += " (settling — new commit pushed; waiting for its checks to register)"
    lines.append(state)
    lines.append(
        f"checks: {ck['success']}/{ck['total']} green"
        + (f", {ck['pending']} pending" if ck["pending"] else "")
        + (f", {ck['informational']} informational" if ck.get("informational") else "")
        + (f", {len(ck['failing'])} FAILING" if ck["failing"] else "")
    )
    for f in ck["failing"]:
        lines.append(f"  ✗ {f['name']} ({f['status']})")
    # The reviewer-outage action signal, hoisted out of the per-comment loop
    # below. It has to survive `--mark-seen`: acking the notice comment used to
    # be the last time anyone saw that the primary reviewer never ran, and the
    # check-description surface never produced a comment to ack in the first
    # place (#23). Printed even when the PR is otherwise clean — a clean report
    # that hides an outage is the exact failure being fixed.
    bots = report.get("review_bots") or {}
    if bots.get("signal") == "unavailable":
        lines.append(
            "  ⚠ review-bot state could not be read — a queued or rate-limited "
            "reviewer will NOT be detected on this poll (see stderr)"
        )
    # A bot mid-review of a just-pushed head is behind it BY CONSTRUCTION, and
    # the pending line above already says a verdict is coming. Warning there too
    # would fire on every poll of the healthy window and train the operator to
    # skim past the case this exists for.
    #
    # Only a BLOCKING pending entry defers, though. A pending check that has aged
    # past the grace window, or been cancelled by an announced outage, is the
    # engine saying "this verdict is not coming" — which is precisely the
    # reviewer-went-away case, so suppressing coverage there silenced the warning
    # in the one situation it was written for.
    reviewing = {e["bot"] for e in bots.get("pending") or [] if e.get("blocking")}
    for entry in bots.get("coverage") or []:
        if not entry["covers_head"] and entry["bot"] not in reviewing:
            # Direct indexing, not `.get`: bot_review_coverage always emits all
            # four keys, so a `.get` here would only imply a partial entry is
            # expected while the very next lookup would KeyError on one.
            lines.append(
                f"  ⚠ review coverage: {entry['bot']}'s last review was of "
                f"{entry['sha'][:7]}, not the current head — a receipt taken now "
                "would not stand for its review of this design; re-request it, or "
                "say so explicitly"
            )
    for entry in bots.get("unavailable") or []:
        lines.append(
            f"  ⚠ review unavailable [{entry['surface']}] {entry['where']}: "
            f"{entry['reason']} — run the configured fallback review"
        )
    grace = bots.get("grace_minutes")
    for entry in bots.get("pending") or []:
        # Only the aged-out reason is reported here. An entry cancelled by an
        # outage already has its own ⚠ line above, and printing "past the 15m
        # grace" for a 1-minute-old check — which the single `not blocking`
        # branch used to do — states a reason that is simply false.
        if entry.get("cancelled_by") == "grace":
            lines.append(
                f"  ⚠ review bot {entry['bot']} check {entry['check']} still pending after "
                f"{entry['age_minutes']}m (past the {grace:g}m grace) — "
                "treated as not coming; run the configured fallback review"
            )
    for blocker in report.get("merge_blockers") or []:
        lines.append(f"  ✗ merge blocker: {blocker}")
    if report["new_comments"]:
        lines.append(f"new comments to address ({len(report['new_comments'])}):")
        for c in report["new_comments"]:
            loc = f" {c['path']}:{c['line']}" if c["path"] else ""
            if c.get("review_unavailable_reason"):
                lines.append(
                    f"  • [review unavailable] @{c['author']}{loc}: "
                    f"{c['review_unavailable_reason']} — run the configured fallback review"
                )
            else:
                lines.append(f"  • [{c['kind']}] @{c['author']}{loc}: {c['excerpt']}")
    return "\n".join(lines)


def render_record_review(report: dict) -> str:
    receipt = report["review_receipt"]
    lines = [
        f"PR #{report['pr']} — recorded independent review from "
        f"{receipt['source']} for head {receipt['head']}"
    ]
    if receipt.get("override"):
        lines.append(
            f"  ⚠ recorded over an active override ({receipt['override']}) — a "
            "configured review bot had not reported yet"
        )
    if receipt.get("bot_signal"):
        lines.append(
            f"  ⚠ review-bot state was unreadable ({receipt['bot_signal']}) when this "
            "receipt was taken — the queued-reviewer guard did not run"
        )
    for bot, sha in (receipt.get("bots_behind_head") or {}).items():
        lines.append(
            f"  ⚠ {bot}'s last review was of {sha[:7]}, not this head — this receipt "
            "does not stand for its review of this design"
        )
    return "\n".join(lines)


def render_mark_seen(report: dict) -> str:
    pr = report.get("pr")
    keys = report.get("marked_seen_keys") or []
    if keys:
        return (
            f"PR #{pr} — acked {len(keys)} comment key(s) from the last reported poll"
        )
    return f"PR #{pr} — {report.get('note', 'nothing to acknowledge')}"


def render_assert_draft(report: dict) -> str:
    pr = report.get("pr")
    want = "draft" if report.get("want_draft") else "ready-for-review"
    if not report.get("corrected"):
        return f"PR #{pr} — already {want} (isDraft={report.get('initial_draft')})"
    if report.get("ok"):
        return f"PR #{pr} — drifted from {want}, corrected (isDraft={report.get('final_draft')})"
    return f"PR #{pr} — drifted from {want}, correction FAILED (isDraft={report.get('final_draft')})"


def persist_poll(pr: int, report: dict, seen: set[str]) -> dict:
    """Persist post-poll watch state and return it.

    Single source of truth for the persistence contract so a test helper can
    exercise the REAL shape instead of a copy that could silently drift:

    - ``head`` / ``max_total`` ride every run (the false-settle guard, see
      :func:`build_report`).
    - ``pending_seen`` is THIS poll's ``all_seen_keys`` — the only thing a
      subsequent ``--mark-seen`` may promote into ``seen``. It overwrites any
      prior unconsumed pending set: the contract is "ack what the *last
      reported* poll showed."
    - ``seen`` itself only grows via :func:`mark_seen`, never here.
    """
    new_state = {
        "seen": sorted(seen),
        "head": report["head"],
        "max_total": report["max_total"],
        "pending_seen": report["all_seen_keys"],
    }
    # The fallback grace clock for a bot whose check carries no usable timestamp.
    # Persisted rather than derived per poll, because a clock that restarts on
    # every poll never advances — and a guard that never advances is a permanent
    # block, the exact wedge this design avoids.
    write_pending_since(
        new_state, report["head"], report["review_bots"]["pending_since"]
    )
    previous = load_state(pr)
    if isinstance(previous.get("review_receipt"), dict):
        new_state["review_receipt"] = previous["review_receipt"]
    save_state(pr, new_state)
    return new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pr",
        nargs="?",
        type=int,
        default=None,
        help="PR number (default: current branch's PR)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--head",
        metavar="EXPECTED_SHA",
        help="exact head SHA reviewed; required with --record-review",
    )
    parser.add_argument(
        "--allow-pending-bot-review",
        action="store_true",
        help=(
            "with --record-review: record the receipt even though a configured review "
            "bot's own check is still pending. Only when you have evidence its verdict "
            "will never arrive — a queued bot is SLOW, not unavailable (issue #19)"
        ),
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--mark-seen",
        action="store_true",
        help=(
            "promote the PENDING set from the last reported poll into seen — acks exactly "
            "what that poll showed (no fresh gh re-poll); call after addressing a round"
        ),
    )
    mode_group.add_argument(
        "--record-review",
        metavar="SOURCE",
        help=(
            "after an independent review and all fixes, persist a receipt bound to "
            "the PR's current head (for example fallback:codex)"
        ),
    )
    mode_group.add_argument(
        "--assert-draft",
        action="store_true",
        help=(
            "assert the PR is a draft, correcting a drifted bit (gh 2.89.0 flakiness) — "
            "call right after `gh pr create --draft` to catch a create that silently landed ready"
        ),
    )
    mode_group.add_argument(
        "--assert-ready",
        action="store_true",
        help=(
            "assert the PR is ready-for-review, correcting a drifted bit — "
            "call right before `gh pr merge` to catch a ready PR that silently reverted to draft"
        ),
    )
    args = parser.parse_args(argv)
    if args.record_review is not None and not args.head:
        parser.error("--record-review requires --head <polled-sha>")
    if args.head and args.record_review is None:
        parser.error("--head is only valid with --record-review")
    if args.allow_pending_bot_review and args.record_review is None:
        parser.error("--allow-pending-bot-review is only valid with --record-review")

    try:
        pr = resolve_pr(args.pr)
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.mark_seen:
        # No `gh` call here on purpose: re-deriving the ack set from a fresh
        # poll is exactly the ordering hazard this replaces. Promote only
        # what the last *reported* poll already persisted as pending.
        mark_report = mark_seen(pr)
        if args.json:
            print(json.dumps(mark_report, ensure_ascii=False))
        else:
            print(render_mark_seen(mark_report))
        return 0

    if args.record_review is not None:
        try:
            review_report = record_review(
                pr,
                args.record_review,
                args.head,
                allow_pending_bot=args.allow_pending_bot_review,
            )
        except (RuntimeError, KeyError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(review_report, ensure_ascii=False))
        else:
            print(render_record_review(review_report))
        return 0

    if args.assert_draft or args.assert_ready:
        try:
            draft_report = assert_draft_state(pr, want_draft=args.assert_draft)
        except (RuntimeError, KeyError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(draft_report, ensure_ascii=False))
        else:
            print(render_assert_draft(draft_report))
        return 0 if draft_report["ok"] else 2

    try:
        view = _gh_json(
            [
                "pr",
                "view",
                str(pr),
                "--json",
                "number,title,url,state,isDraft,baseRefName,mergeStateStatus,reviewDecision,headRefOid,statusCheckRollup,reviews,comments",
            ]
        )
        inline = _gh_json(
            ["api", f"repos/{{owner}}/{{repo}}/pulls/{pr}/comments", "--paginate"]
        )
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    # Deliberately outside the try: this call never raises and never blocks the
    # loop — see :func:`fetch_check_details`.
    check_details = fetch_check_details(pr)

    state = load_state(pr)
    seen = set(state.get("seen", []))
    report = build_report(
        view,
        inline,
        seen,
        prior_head=state.get("head"),
        prior_max_total=int(state.get("max_total") or 0),
        review_receipt=state.get("review_receipt"),
        check_details=check_details,
        prior_pending_since=read_pending_since(state, view.get("headRefOid")),
    )

    persist_poll(pr, report, seen)

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
