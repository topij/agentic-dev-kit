#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Poll a PR's CI checks + new review comments — the engine for the watch-and-fix loop.

The shared `pr-watch` workflow (and the "PR follow-through" policy in your project's
agent instructions)
call this once per round: it asks GitHub for the PR's check rollup + every
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

The transport is a thin layer; the classification + diff + done logic are pure
functions (tested). Stdlib only.

**Two backends, with different authority.** `gh` is the default whenever the
binary is on PATH, and its behaviour is unchanged. When `gh` is absent — cloud and
container sessions with no binary and no way to run an interactive
`gh auth login` — the same fields are read from the GitHub REST API using
`GH_TOKEN`/`GITHUB_TOKEN`. With neither, the engine exits 2 with an actionable
message rather than a `FileNotFoundError` traceback. Selection is per call, never
memoized: see `_resolve_backend`.

**On REST this engine POLLS ONLY.** `mergeable` is false by construction, and
`--record-review` / `--assert-draft` / `--assert-ready` refuse. It does still
write its own per-PR watch state (the seen-set, the settle baseline, the grace
clock) — "polls only" means it never authorizes a merge and never mutates the PR,
not that it touches no disk. Calling that "read-only" was imprecise. So the watch loop works without `gh`, and merge authorization still
requires it — which costs nothing, because `dev_session.sh merge` needs `gh`
anyway. See `rest_cannot_authorize_merge` for why this is a structural bound
rather than validation at each boundary, and issue #94 for lifting it. It polls
only; it is not read-only — it still writes its own per-PR watch state.

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
right before `gh pr merge`. Both REFUSE on the REST backend: they mutate the PR,
and REST is read-only here (see `require_gh_backend`).

Exit codes:
    0 — reported (regardless of the verdict; check `converged` / `mergeable` in
        the output), or the draft-bit assertion held/was corrected successfully
    2 — usage error (no PR found, transport failure, no usable backend), or a
        draft-bit assertion that failed to correct (`ok: false`)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple


def _find_repo_root(start: Path) -> Path:
    """Nearest ancestor with a ``.git`` marker (so this keeps working when the kit
    is vendored under a nested dir, e.g. scripts/devkit/). Inlined — pr_watch
    stays stdlib-only.

    The ``.git`` walk handles any depth. The FALLBACK does not, and that is a
    known limitation rather than an oversight: ``parent.parent`` is calibrated
    for ``scripts/pr_watch.py`` and returns ``<repo>/scripts`` from the vendored
    ``scripts/devkit/`` layout named right above (issue #60, still open). A
    config-marker probe was tried here and removed — see
    ``lib/kitconfig.py:repo_root`` for why a depth bound cannot fix it. It
    matters most here: ``REPO_ROOT`` is the ``cwd=`` for every ``gh``/``git``
    subprocess and the base for the state root, so a probe that escapes points
    a merge-gate engine at a different repository. Failing loudly inside the
    right tree beats resolving quietly into the wrong one."""
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
#
# `is_noise` matches these against the body ALONE, with no author check, so an
# entry here silences the text wherever it appears — including in a human's
# comment quoting the bot. Structural markers (the HTML comments a bot writes into
# its own container) carry that property safely; the bot's *prose* does not, which
# is why the clean-verdict sentence "No actionable comments were generated in the
# recent review." is deliberately absent. `#468`.
_DEFAULT_NOISE_MARKERS = (
    "bugbot needs on-demand usage enabled",  # Cursor billing notice
    "<!-- this is an auto-generated comment: summarize by coderabbit",  # walkthrough
    "<!-- this is an auto-generated comment: review in progress",  # CodeRabbit "processing…" placeholder
    "<!-- walkthrough_start -->",
    "review skipped",  # CodeRabbit draft-detected / skip notices
    "<!-- linear-linkback -->",  # a tracker's auto issue-mirror comment (not a finding)
)

# Review unavailability is actionable even when the surrounding comment also
# carries a generic walkthrough/noise marker. Surfacing it is what triggers the
# configured independent fallback; hiding it would turn a down reviewer into a
# silent review waiver.
# Comment text announcing a review that COMPLETED (#44). Reported only — see
# `bot_comment_verdicts` for why this may never reach the merge gate, and
# `review.comment_verdict_markers` in config/dev-model.yaml for the full account.
_DEFAULT_COMMENT_VERDICT_MARKERS = (
    "no actionable comments were generated",
    "actionable comments posted:",
)

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
# check name, and by exact normalized identity for a comment author (that input
# is not the repo's to control). Known service aliases are enumerated below;
# accepting prefixes would let `coderabbit-impersonator` speak for CodeRabbit.
# Keep entries specific enough not to collide with a CI job name.
_DEFAULT_REVIEW_BOTS = ("coderabbit",)

_DEFAULT_REVIEW_BOT_AUTHOR_ALIASES = {
    "coderabbit": frozenset({"coderabbitai", "coderabbitai[bot]"}),
}

# Extra CREATOR identities trusted to announce an outage for a bot, for the case
# where an app's slug differs from the login it comments under (#95). Ordinarily
# empty: `_trusted_bot_identities` already derives the common case from the
# author-alias table above, since a GitHub App's slug and its `<slug>[bot]` login
# are conventionally the same string — verified on this repo, where the real
# reviewer's status contexts carry `creator.login: coderabbitai[bot]` while
# `bot_author_aliases` already enumerates `coderabbitai`.
#
# Derived, never inferred from the bot key alone: an app slug is an
# attacker-relevant identity, so it comes from a table an adopter curates. Same
# "enumerate, never infer" discipline as the aliases — a prefix rule here would
# let `coderabbit-impersonator` announce CodeRabbit's outage, which is the whole
# of #95 one namespace over.
_DEFAULT_REVIEW_BOT_APP_SLUGS: dict[str, frozenset[str]] = {}

# How long a configured review bot's own check may sit non-terminal before the
# merge gate stops waiting for it. Below the bound, a pending bot is "a review
# is coming" and blocks `mergeable` (issue #19 — a receipt recorded against a
# merely *slow* bot let four post-merge findings through). Above it, the bot is
# treated as never going to report and stops blocking — which is what preserves
# the anti-wedge property that `_DEFAULT_INFORMATIONAL_CHECK_NAMES` exists for.
_DEFAULT_BOT_PENDING_GRACE_MINUTES = 15.0

# How long the check rollup must go without changing size, for the current head,
# before the merge gate believes it is COMPLETE. See the settle-baseline block in
# :func:`build_report` for what this is protecting and why a count alone cannot.
#
# NOT A MEASURED VALUE ON THIS REPO, and saying so is the honest form: the kit's
# own CI registers exactly one check
# (`gh api repos/topij/agentic-dev-kit/commits/<sha>/check-runs`), so there is no
# registration *spread* here to measure. What the number has to exceed is the gap
# between a head's first and last check appearing, which is a property of the
# adopter's CI, not of this engine — so re-measure it against your own repo before
# treating this default as tuned for you.
#
# What makes 3 safe to ship without that measurement is the shape of the cost
# rather than the size of the number. The clock runs from when the rollup last
# GREW, which is seconds after a push — concurrently with CI, not after it — so on
# any repo whose checks take longer than the grace to finish, the added merge
# latency is zero. Being too large is fail-CLOSED (a slower merge); the only
# fail-open setting is 0, and that is opt-out, not tuning.
_DEFAULT_SETTLE_GRACE_MINUTES = 3.0


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
    comment_verdict_markers: tuple[str, ...]
    informational_checks: frozenset[str]
    require_ci: bool
    bots: tuple[str, ...]
    bot_author_aliases: dict[str, frozenset[str]]
    bot_app_slugs: dict[str, frozenset[str]]
    bot_pending_grace_minutes: float
    settle_grace_minutes: float


def _normalize_bot_author_aliases(value: Any) -> dict[str, frozenset[str]] | None:
    """Normalize a ``{bot: [identity, …]}`` config mapping, or reject all of it.

    Serves both ``review.bot_author_aliases`` and ``review.bot_app_slugs`` — the
    two have identical shape and identical trust semantics (an enumerated set of
    identities allowed to speak for a bot), so they share one normalizer rather
    than two that can drift apart.

    Partial acceptance is unsafe: one malformed entry among several would make
    that reviewer silently lose outage detection while the rest appeared to
    work. ``None`` tells the caller to warn and use the complete built-in
    default instead.
    """
    if not isinstance(value, dict):
        return None
    normalized: dict[str, frozenset[str]] = {}
    for raw_bot, raw_aliases in value.items():
        if not isinstance(raw_bot, str):
            return None
        bot = raw_bot.strip().lower()
        aliases = [raw_aliases] if isinstance(raw_aliases, str) else raw_aliases
        if isinstance(aliases, (tuple, set, frozenset)):
            aliases = list(aliases)
        if not bot or not isinstance(aliases, list) or not aliases or not all(
            isinstance(alias, str) and alias.strip() for alias in aliases
        ):
            return None
        normalized[bot] = frozenset(alias.strip().lower() for alias in aliases)
    return normalized


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
    - ``settle_grace_minutes`` validates identically, and its ``0`` is narrower
      than the one above: it drops the *time* requirement but NOT the
      requirement that a baseline exist at all, so a fresh clone still blocks
      for the one poll it takes to record one (#190 is not a timing bug and is
      not opted out of here). Setting it high is fail-closed.
    """
    defaults = ReviewConfig(
        noise_markers=_DEFAULT_NOISE_MARKERS,
        unavailable_markers=_DEFAULT_REVIEW_UNAVAILABLE_MARKERS,
        comment_verdict_markers=_DEFAULT_COMMENT_VERDICT_MARKERS,
        informational_checks=frozenset(_DEFAULT_INFORMATIONAL_CHECK_NAMES),
        require_ci=_DEFAULT_REQUIRE_CI,
        bots=_DEFAULT_REVIEW_BOTS,
        bot_author_aliases=dict(_DEFAULT_REVIEW_BOT_AUTHOR_ALIASES),
        bot_app_slugs=dict(_DEFAULT_REVIEW_BOT_APP_SLUGS),
        bot_pending_grace_minutes=_DEFAULT_BOT_PENDING_GRACE_MINUTES,
        settle_grace_minutes=_DEFAULT_SETTLE_GRACE_MINUTES,
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
        verdict_markers = get_str_list(
            config,
            "review.comment_verdict_markers",
            list(_DEFAULT_COMMENT_VERDICT_MARKERS),
        )
        informational = get_str_list(
            config,
            "review.informational_checks",
            list(_DEFAULT_INFORMATIONAL_CHECK_NAMES),
        )
        bots = get_str_list(config, "review.bots", list(_DEFAULT_REVIEW_BOTS))
        raw_aliases = get(
            config,
            "review.bot_author_aliases",
            _DEFAULT_REVIEW_BOT_AUTHOR_ALIASES,
        )
        aliases = _normalize_bot_author_aliases(raw_aliases)
        if aliases is None:
            print(
                "warning: review.bot_author_aliases must map bot names to non-empty string lists; "
                "using pr_watch's built-in aliases",
                file=sys.stderr,
            )
            aliases = dict(_DEFAULT_REVIEW_BOT_AUTHOR_ALIASES)
        raw_slugs = get(config, "review.bot_app_slugs", _DEFAULT_REVIEW_BOT_APP_SLUGS)
        # An EMPTY mapping is the default and must stay valid, so the reject
        # sentinel is distinguished from a legitimately empty result rather than
        # by truthiness — `if not slugs` would treat `{}` as malformed and warn on
        # every poll of every repo that never sets the key.
        app_slugs = _normalize_bot_author_aliases(raw_slugs) if raw_slugs else {}
        if app_slugs is None:
            print(
                "warning: review.bot_app_slugs must map bot names to non-empty string lists; "
                "using pr_watch's built-in app slugs",
                file=sys.stderr,
            )
            app_slugs = dict(_DEFAULT_REVIEW_BOT_APP_SLUGS)
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
        settle_grace = get(
            config,
            "review.settle_grace_minutes",
            _DEFAULT_SETTLE_GRACE_MINUTES,
        )
        if (
            isinstance(settle_grace, bool)
            or not isinstance(settle_grace, (int, float))
            or settle_grace < 0
        ):
            settle_grace = _DEFAULT_SETTLE_GRACE_MINUTES
    except FileNotFoundError:
        # `load_config` raises this for an absent config file — a standalone
        # engine run. Defaults are exactly right; stay quiet.
        return defaults
    except ValueError as exc:
        # An unusable local config overlay. This branch used to `raise` — but
        # `_load_review_config()` runs at MODULE IMPORT, so that killed even
        # `--help` with a raw traceback, and contradicted kit_doctor's handler in
        # the same change ("a config error reports cleanly"). Both panel lenses
        # caught it. Warn distinctly instead: the overlay is operator-fixable and
        # names itself, unlike the read failures below. It cannot narrow the review
        # gate either — `review.*` is not overlayable.
        print(f"warning: {exc}", file=sys.stderr)
        print("warning: using pr_watch's built-in review defaults", file=sys.stderr)
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
        comment_verdict_markers=tuple(marker.lower() for marker in verdict_markers),
        informational_checks=frozenset(
            name.strip().lower() for name in informational if name.strip()
        ),
        require_ci=require_ci,
        bots=tuple(bot.strip().lower() for bot in bots if bot.strip()),
        bot_author_aliases=aliases,
        bot_app_slugs=app_slugs,
        bot_pending_grace_minutes=float(grace),
        settle_grace_minutes=float(settle_grace),
    )


_REVIEW_CONFIG = _load_review_config()
_NOISE_MARKERS = _REVIEW_CONFIG.noise_markers
_REVIEW_UNAVAILABLE_MARKERS = _REVIEW_CONFIG.unavailable_markers
_COMMENT_VERDICT_MARKERS = _REVIEW_CONFIG.comment_verdict_markers
_INFORMATIONAL_CHECK_NAMES = _REVIEW_CONFIG.informational_checks
_REQUIRE_CI = _REVIEW_CONFIG.require_ci
_REVIEW_BOTS = _REVIEW_CONFIG.bots
_REVIEW_BOT_AUTHOR_ALIASES = _REVIEW_CONFIG.bot_author_aliases
_REVIEW_BOT_APP_SLUGS = _REVIEW_CONFIG.bot_app_slugs
_BOT_PENDING_GRACE_MINUTES = _REVIEW_CONFIG.bot_pending_grace_minutes
_SETTLE_GRACE_MINUTES = _REVIEW_CONFIG.settle_grace_minutes


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


# --------------------------------------------------------------- rest transport
#
# `gh` stays the default backend and its path is unchanged. Some cloud and
# container sessions have no `gh` binary and no way to run an interactive
# `gh auth login`; there, this backend re-derives the same fields from the
# GitHub REST API over `urllib` (stdlib only — this engine must stay
# dependency-free so it can run from a git hook), authenticating with
# GH_TOKEN/GITHUB_TOKEN.
#
# Dispatch is SEMANTIC, not a generic `gh --json` emulator: each of the six
# things this engine actually asks GitHub for has its own pair of
# implementations. Emulating arbitrary `--json` field sets would be a fake
# abstraction that silently returns the wrong shape the first time a caller
# asks for a field the emulator never mapped.
#
# `_http_get` / `_http_get_all` / `_http_get_all_wrapped` are the HTTP boundary.
# Most tests mock these helpers directly, which is fine for logic above them.
# Anything testing a guard INSIDE `_http_get` — the host check, the redirect
# check — must mock the opener below it instead (`_fake_urlopen` in the tests):
# a mock placed above `_check_api_url` can only ever verify its own scaffolding,
# which is how the host guard came to be untested on #91.


def _github_token() -> str | None:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _resolve_backend() -> tuple[str, str | None]:
    """Pick ``"gh"`` or ``"rest"``, or raise a clear, actionable RuntimeError.

    Resolved **lazily on every call**, never memoized at import time. Issue #48
    is the standing lesson: `pr_watch` resolving config at import time silently
    coupled ~32 kit tests to ambient repo state. A cached backend would do the
    same thing with ambient PATH — the first test to import the module would
    pin the backend for every test after it, and which backend that is would
    depend on whether the machine running CI happens to have `gh`.
    ``shutil.which`` is a cheap filesystem stat, so there is nothing to cache.

    Never lets a missing `gh` reach the operator as a raw ``FileNotFoundError``
    traceback — that is the bug this fallback exists to fix. Callers in
    :func:`main` already catch ``RuntimeError`` and print ``error: …`` + exit 2.
    """
    if shutil.which("gh") is not None:
        return "gh", None
    token = _github_token()
    if not token:
        raise RuntimeError(
            "`gh` CLI not found on PATH and no GitHub token in the environment — "
            "the watch engine needs one or the other. Install and authenticate "
            "`gh`, or set GH_TOKEN or GITHUB_TOKEN to a token with `repo` scope "
            "for the REST fallback, which POLLS ONLY: `--record-review`, "
            "`--assert-draft` and `--assert-ready` need `gh` either way (issue "
            "#94)."
        )
    return "rest", token


# ─── the one place the REST backend's authority is bounded ────────────────────
#
# On the REST backend this engine POLLS ONLY: it never authorizes a merge and
# never mutates the PR. It does write its own watch state (seen-set, settle
# baseline, grace clock), so "read-only" would be the wrong word. Both halves of
# what IS forbidden are enforced here — `mergeable` via :func:`rest_cannot_authorize_merge` in `build_report`,
# and the write paths via :func:`require_gh_backend`.
#
# Why a structural bound rather than validation at each boundary: PR #91 tried
# the latter. Three review rounds found HIGH fail-opens each time (2, 2, then
# ~7), severity INCREASING, because every round hardened one more boundary and
# the next round found the next one. `safety-critical-changes.md` rule 1 names
# that pattern — a leaky gate yields a new hole per round rather than closing the
# class — and prescribes a deterministic artifact instead. This is it: no
# malformed, truncated, stale or hostile response can make REST permissive,
# because REST does not get to say "mergeable" at all.
#
# It costs nothing today. `dev_session.sh cmd_merge` shells out to `gh repo view`
# + `gh pr list` (via `_resolve_lane_pr`) BEFORE it reads `mergeable`, and
# finishes with `gh pr merge` — so with no `gh` there is no merge path to feed.
# The bound turns that accident into an invariant.
#
# Broadening this is issue #94, and its acceptance bar is the fail-open
# enumeration recorded there. Keep the bound in these two functions so that
# broadening stays a deletion rather than a rewrite.

_REST_POLL_ONLY_BLOCKER = (
    "the REST backend cannot authorize a merge — it polls only (issue #94); "
    "run the merge from a session with `gh` available"
)


def _active_backend_name() -> str:
    """``"gh"`` / ``"rest"`` / ``"unknown"`` — never raises.

    Reporting-only, so an unresolvable backend must not turn a poll into an
    error; ``"unknown"`` is also correctly unequal to any recorded backend, which
    is the safe direction for :func:`comparable_max_total`.
    """
    try:
        return _resolve_backend()[0]
    except RuntimeError:
        return "unknown"


def rest_cannot_authorize_merge(backend: str | None = None) -> str | None:
    """The merge blocker to add when the report's data came from REST, else None.

    ``backend`` must be the backend that ACTUALLY PERFORMED THE READS, threaded in
    by the caller. Re-resolving it here was a race: `_resolve_backend` re-reads
    PATH on every call by design, so a `gh` that appeared during the poll's network
    phase — several round trips at a 30s timeout each — made this return None for a
    report built entirely from REST data. Measured: `mergeable: true` with
    `_gh_json` never called.

    Resolving once per poll and threading it satisfies the #48 lesson (no
    import-time memoization) without letting the bound drift from the data.

    Deliberately NOT conditioned on anything observed about the PR: the whole
    point is that no remote response participates in this decision.
    """
    if backend is None:
        try:
            backend, _ = _resolve_backend()
        except RuntimeError:
            # No usable backend at all. A missing backend must never read as
            # "gh, therefore permitted".
            return _REST_POLL_ONLY_BLOCKER
    return _REST_POLL_ONLY_BLOCKER if backend == "rest" else None


def require_gh_backend(operation: str) -> None:
    """Refuse a merge-authorizing or mutating operation on the REST backend.

    `--record-review` writes a receipt that outlives the process and is what
    flips `mergeable` on a later poll; `--assert-draft`/`--assert-ready` mutate
    the PR. Each carried its own fail-open on #91 — a receipt written from a
    truncated read recorded no `bot_signal`, and `--assert-ready` reported
    success from a body that never contained a draft bit. Rather than validate
    those paths, REST does not get them.
    """
    backend, _ = _resolve_backend()
    if backend == "rest":
        raise RuntimeError(
            f"{operation} needs the `gh` backend: the REST fallback polls only "
            "(issue #94). Install and authenticate `gh`, or run this from a "
            "session that has it."
        )


def _http_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agentic-dev-kit-pr-watch",
    }


_API_HOST = "api.github.com"


def _check_api_url(url: str) -> str:
    """Refuse to send the token anywhere but the GitHub API over TLS.

    Not defensive boilerplate: `_http_get_all` follows a `Link: rel="next"` URL
    that comes from the RESPONSE, so the destination of every page after the
    first is server-supplied. Validating inside the HTTP boundary covers the
    initial URL and every followed page with one check.

    ``GH_REPO`` is unhandled, and that matters more than it looks:
    ``dev_session.sh`` puts ``GH_REPO="$repo_nwo"`` in this engine's environment.
    ``gh`` honours it; the REST path resolves the repository from
    ``git remote get-url origin``, so the two backends can silently target
    different repositories. Keep `gh` on PATH wherever ``GH_REPO`` is set.

    Only github.com is supported: there is no `GH_HOST`/`GITHUB_HOST` handling
    anywhere in this engine, so a GitHub Enterprise origin parses to a valid
    owner/repo and is then queried against api.github.com. That is normally a 404,
    but if the same owner/repo exists publicly it would report a DIFFERENT
    repository's state as this PR's. Enterprise users should keep `gh` on PATH.

    Redirects go through the same check. urllib carries ``headers=`` across a
    3xx, so without this a redirect to another host would re-send the bearer
    token — and calling that "pre-existing urllib behaviour" (as an earlier
    version of this docstring did) was wrong: before this transport existed no
    GitHub token ever left the process, because `gh` owned its own auth. The
    exposure is this transport's to close, and :class:`_ApiOnlyRedirectHandler`
    closes it.

    The port is checked too: a server-supplied ``Link`` naming
    ``api.github.com:8443`` is not the GitHub API.
    """
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != _API_HOST
        or parsed.port not in (None, 443)
    ):
        raise RuntimeError(
            f"refusing to send a GitHub token to {url!r} — only https://{_API_HOST} is allowed"
        )
    return url


class _ApiOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-check the destination of every redirect before following it.

    ``urlopen`` follows 3xx internally, so :func:`_check_api_url` on the URL the
    engine *chose* proves nothing about where the token actually goes.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        _check_api_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_ApiOnlyRedirectHandler)


def _http_get(url: str, token: str, *, timeout: int = 30) -> tuple[Any, str | None]:
    """GET ``url``, returning (parsed JSON, the raw ``Link`` header or None)."""
    req = urllib.request.Request(_check_api_url(url), headers=_http_headers(token))  # noqa: S310
    try:
        with _opener.open(req, timeout=timeout) as resp:  # noqa: S310 — host-checked
            body = resp.read()
            link = resp.headers.get("Link")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"GitHub API GET {url} failed ({exc.code} {exc.reason})"
            + (
                " — the token may lack `repo` scope or have expired"
                if exc.code in (401, 403)
                else ""
            )
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API GET {url} failed: {exc.reason}") from exc
    try:
        return json.loads(body), link
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub API GET {url} returned non-JSON body") from exc


def _next_link(link_header: str | None) -> str | None:
    """The ``rel="next"`` URL from a GitHub ``Link`` pagination header, if any."""
    if not link_header:
        return None
    for part in link_header.split(","):
        section = [p.strip() for p in part.split(";")]
        # Scan EVERY parameter, not just the second, and accept an unquoted
        # value. `<url>; type="text/html"; rel="next"` and `rel=next` are both
        # legal per RFC 8288, and reading only `section[1] == 'rel="next"'`
        # returned None for each — a silent truncation with no warning, because
        # to the caller it is indistinguishable from "no next page".
        for param in section[1:]:
            name, _, value = param.partition("=")
            # Both sides lowered: RFC 8288 relation types are case-insensitive,
            # so `rel="NEXT"` is the same link as `rel="next"`.
            if name.strip().lower() == "rel" and value.strip().strip('"\'').lower() == "next":
                return section[0].strip("<>")
    return None


# Page ceiling for every paginated REST read. Bounded so a malformed or cyclic
# `Link` header cannot spin a watch loop forever; 20 pages at per_page=100 is
# 2000 items, far past any real PR.
_REST_MAX_PAGES = 20

_truncation_warned: set[str] = set()

# URLs truncated by the page ceiling during THIS process, in order. Surfaced two
# ways so the claim matches reality: in the JSON, and printed by `render`.
#
# The JSON alone was not enough, and saying it was is a mistake this engine has
# now made twice. `summarize_review_bots.signal` is the precedent worth copying —
# but the reason it works is that `render` BRANCHES on it and
# `workflows/pr-watch.md` documents it. A field with neither is read by nobody:
# `dev_session.sh merge` extracts only `mergeable`/`pr`/`base`/`head`.
#
# It gates nothing on purpose (REST cannot authorize a merge, and blocking
# `converged` would wedge the watch loop), so the render line is the whole
# mechanism: REST list endpoints return oldest-first, which means the ceiling
# drops the NEWEST comments — where fresh findings live — and an agent reading
# "converged" needs to see that its comment read was incomplete.
_truncated_reads: list[str] = []


def _warn_pagination_truncated(url: str, max_pages: int) -> None:
    """Record and announce that the page ceiling — not the data — ended a read.

    A partial list is byte-identical to a complete one, which is the same
    "truncated reads as absent rather than unread" direction the ceiling exists
    to bound. Deliberately NOT ``_warn_bot_signal_lost``: that warning makes a
    specific claim about the review-bot guards, and reusing it here would say
    something false about which guard is blind.

    The stderr line is deduped per URL within one process, which is one poll —
    the engine is invoked fresh per round. What that collapses is the check-runs
    URL being read twice in a single poll (`rest_pr_view`, then
    `fetch_check_details`).

    ``_truncated_reads`` itself is NOT deduped: both reads are real events.
    :func:`render` is what collapses them for display; ``build_report`` copies the
    list through unchanged and raises no blocker from it.
    """
    _truncated_reads.append(url)
    if url in _truncation_warned:
        return
    _truncation_warned.add(url)
    print(
        f"warning: paginated GitHub read stopped at the {max_pages}-page ceiling "
        f"({url}) — the result is TRUNCATED, not complete; checks or comments "
        "beyond that point were not read",
        file=sys.stderr,
    )


def _http_get_all(url: str, token: str, *, max_pages: int = _REST_MAX_PAGES) -> list:
    """GET ``url`` following ``Link: rel="next"``, for endpoints whose body IS
    the JSON array (reviews, issue comments, inline comments).

    A page that is not a list RAISES rather than contributing nothing. Skipping
    it silently was a fail-open straight through the merge gate, and the same one
    `_rest_object` exists to close for the object reads: a 200 with a `null` body
    on `pulls/{n}/reviews` made `review_decision` empty, which removed the
    CHANGES_REQUESTED blocker and flipped `mergeable` from false to TRUE. On the
    comment surfaces it made every unread finding read as "no findings".
    """
    items: list = []
    next_url: str | None = url
    pages = 0
    while next_url and pages < max_pages:
        data, link = _http_get(next_url, token)
        if not isinstance(data, list):
            raise RuntimeError(
                f"GitHub API GET {next_url} returned {type(data).__name__}, expected a JSON array"
            )
        items.extend(data)
        next_url = _next_link(link)
        pages += 1
    if next_url:
        _warn_pagination_truncated(url, max_pages)
    return items


def _http_get_all_wrapped(
    url: str, token: str, key: str, *, max_pages: int = _REST_MAX_PAGES
) -> list:
    """Same as :func:`_http_get_all` for an endpoint that wraps its array in an
    object — the Checks API's ``{"total_count": …, "check_runs": [...]}``.

    Pagination here is load-bearing, not defensive. The Checks API defaults to
    ``per_page=30``; cs-toolkit shipped a false green from a single unpaginated
    GET against ~49 real check runs, which truncated the rollup so the missing
    checks read as "not present" rather than "not yet read". Callers must pass
    ``per_page=100`` on ``url`` as well, to keep the page count low.
    """
    items: list = []
    next_url: str | None = url
    pages = 0
    while next_url and pages < max_pages:
        data, link = _http_get(next_url, token)
        if not isinstance(data, dict):
            raise RuntimeError(
                f"GitHub API GET {next_url} returned {type(data).__name__}, expected a JSON object"
            )
        # The extracted value needs its own check, not just the page. `or []`
        # only rescued a falsy value: a STRING extends character by character, a
        # dict extends its keys, and `_rest_check_rows` then filters the garbage
        # out so the whole check surface reads as empty.
        #
        # An ABSENT key is also rejected, which an earlier version of this allowed
        # by conflating "empty list" with "no key". GitHub always returns the
        # wrapper key — `{"total_count": 0, "check_runs": []}` for a commit with no
        # checks — so its absence means the body is not this endpoint's shape,
        # typically a 200 carrying an error payload. Treating that as "this surface
        # has no checks" dropped a whole surface silently: a real FAILING status
        # context vanished and `all_green` went true, with no warning and no
        # `truncated_reads` entry. An empty LIST is still legal.
        if key not in data:
            raise RuntimeError(
                f"GitHub API GET {next_url} returned no {key!r} key — not this "
                "endpoint's shape (usually an error payload with a 200 status)"
            )
        page = data.get(key)
        if not isinstance(page, list):
            raise RuntimeError(
                f"GitHub API GET {next_url} returned {type(page).__name__} for "
                f"{key!r}, expected a JSON array"
            )
        items.extend(page)
        next_url = _next_link(link)
        pages += 1
    if next_url:
        _warn_pagination_truncated(url, max_pages)
    return items


def _git_out(args: list[str], *, what: str) -> str:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607 — git resolved from PATH, fixed argv
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"could not {what}: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError(f"could not {what}: {result.stderr.strip()}")
    return result.stdout.strip()


def _rest_repo_slug() -> tuple[str, str]:
    """``(owner, repo)`` parsed from the ``origin`` remote URL.

    Only reached on the gh-less REST path, which always runs from a checkout —
    so a git-less environment is not a case worth defending further.
    """
    url = _git_out(
        ["remote", "get-url", "origin"], what="read the `origin` remote URL"
    )
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        raise RuntimeError(f"could not parse owner/repo from origin remote URL: {url!r}")
    return match.group(1), match.group(2)


def _rest_api(path: str, slug: tuple[str, str] | None = None) -> str:
    """Build an API URL. Pass ``slug`` when building several in one operation.

    Not cached at module scope, deliberately — that is the shape
    :func:`_resolve_backend` documents as the #48 hazard, and a cached slug goes
    stale the moment a caller changes repository (which the test suite does).
    Threading it through instead gets the same one-lookup-per-operation saving
    with no process-lifetime state: :func:`rest_pr_view` builds six URLs from
    one ``git remote`` call.
    """
    owner, repo = slug if slug is not None else _rest_repo_slug()
    return f"https://api.github.com/repos/{owner}/{repo}/{path}"


def rest_resolve_pr(explicit: int | None, *, token: str) -> int:
    """REST equivalent of :func:`resolve_pr`.

    Known limitation, stated rather than silently wrong: the head filter reuses
    the `origin` owner, so on a FORK checkout this queries the fork while the PR
    lives upstream (`gh` resolves that correctly). The kit's own model is
    same-repo `dev/<scope>` branches — `dev_session.sh` assumes it too — so a
    fork workflow is already outside what this engine supports. Pass an explicit
    PR number there.
    """
    if explicit is not None:
        return explicit
    slug = _rest_repo_slug()
    branch = _git_out(
        ["rev-parse", "--abbrev-ref", "HEAD"], what="determine the current branch"
    )
    # quote(): a branch is not the repo's to sanitize, and an unencoded `&` or
    # `?` in one silently rewrites the query — `dev/x&state=closed` produced
    # `…&state=closed&state=open`, i.e. a filter the caller never asked for.
    head = urllib.parse.quote(f"{slug[0]}:{branch}", safe="")
    data, _ = _http_get(
        _rest_api(f"pulls?head={head}&state=open&per_page=100", slug), token
    )
    # A non-list body would make `data[0]` a TypeError, which `main`'s handler
    # does not catch — so it would escape as a traceback rather than `error: …`.
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"no open PR found for branch {branch!r}")
    return int(data[0]["number"])


# REST conclusion/status -> the bucket `gh pr checks` would report. Kept as an
# explicit table rather than derived, because `_check_is_pending` treats a row
# with NO bucket and no recognized state as pending (fail-closed) — so a wrong
# bucket here is the one direction that could wave a bot through.
_REST_BUCKETS = {
    "SUCCESS": "pass",
    "NEUTRAL": "skipping",
    "SKIPPED": "skipping",
    # STALE is deliberately ABSENT, so it falls through to "pending" below.
    # `summarize_checks` treats it as neither terminal-ok nor bad, i.e. pending,
    # and `_TERMINAL_CHECK_STATES` omits it too. Mapping it to "skipping" here
    # made the two lanes disagree about the same row: finished to the bot lane
    # (`_check_is_pending` trusts the bucket) and pending to the blocking tally.
    # The bot-lane side of that split is the fail-open direction.
    "CANCELLED": "cancel",
    "FAILURE": "fail",
    "ERROR": "fail",
    "TIMED_OUT": "fail",
    "ACTION_REQUIRED": "fail",
    "STARTUP_FAILURE": "fail",
}


def _rest_str(value: object) -> str:
    """Coerce a remote scalar to ``str``, mapping anything else to ``""``.

    The `gh` path never needed this: the CLI applies a schema, so every string
    field arrives as a string. REST hands raw JSON straight to
    :func:`summarize_checks` and :func:`summarize_review_bots`, which call
    ``.strip()`` / ``.lower()`` on these fields — so a dict-valued ``name`` or
    ``output.title`` raised AttributeError out of `build_report`, which runs
    OUTSIDE `main`'s try.

    That is worse than a bad message: the raise precedes :func:`persist_poll`, so
    no state is written and every subsequent poll repeats it. The PR's watch loop
    is stuck with no ageing-out and no override — a wedge, from one malformed
    field. ``str()`` is deliberately not used: it would turn ``{"a": 1}`` into the
    string ``"{'a': 1}"`` and feed that to the outage matchers as if it were a
    real description.
    """
    return value if isinstance(value, str) else ""


def _rest_check_rows(
    check_runs: list[dict],
    statuses: list[dict],
    *,
    status_creators: dict[str, str] | None = None,
) -> list[dict]:
    """Shape REST check runs + legacy status contexts into ``gh pr checks`` rows.

    Carries ``description`` and ``startedAt``, which is the whole point: the
    GraphQL rollup `gh pr view` returns has neither, and without them #23's
    outage guard and #19's queued-bot grace window have nothing to read. On the
    REST path this shaping is the ONLY source of both.

    Also carries ``identity`` — the creator the outage path must trust (#95) —
    and it comes from a different place per surface, which is why this is not one
    expression:

    - a **check run** carries its own ``app.slug`` on the object, so the identity
      is exact and needs no join.
    - a **status context** does not: the combined-status endpoint this reads
      (``/commits/{sha}/status``) omits ``creator`` entirely — verified against
      this repo, whose real CodeRabbit context returns only
      ``avatar_url, context, created_at, description, id, node_id, state,
      target_url, updated_at, url``. So its identity arrives via
      ``status_creators``, keyed by context name, from the sibling
      ``/commits/{sha}/statuses`` endpoint that does carry it.

    ``status_creators=None`` (the identity read was not performed or failed)
    leaves every status row's ``identity`` empty, which reads as untrusted.
    """
    rows: list[dict] = []
    for run in check_runs:
        if not isinstance(run, dict):
            continue
        completed = run.get("status") == "completed"
        state = _rest_str(
            run.get("conclusion") if completed else run.get("status")
        ).upper()
        rows.append(
            {
                "name": _rest_str(run.get("name")) or "check",
                "state": state,
                "bucket": _REST_BUCKETS.get(state, "pending"),
                # `output.title` is what gh surfaces as a CheckRun's description
                # — the field that carried CodeRabbit's rate limit on #22.
                # isinstance, not `or {}`: a STRING `output` passes the
                # truthiness test and then raises AttributeError on `.get`. The
                # identical expression is reached from `fetch_check_details`,
                # whose handler catches AttributeError because it runs outside
                # `main`'s try — and from `rest_pr_view`, which does not. Guarded
                # here so both callers are safe rather than one.
                "description": (
                    _rest_str((run.get("output") or {}).get("title"))
                    if isinstance(run.get("output"), dict)
                    else ""
                ),
                "startedAt": _rest_str(run.get("started_at")),
                # The app that authenticated the check-run creation. A PR
                # workflow's GITHUB_TOKEN always resolves to `github-actions`, so
                # a forged check cannot claim a reviewer's app here — verified on
                # this repo, where the Actions check carries
                # `app.slug: github-actions` while the real reviewer's identity is
                # `coderabbitai[bot]`.
                # The `isinstance` check is the whole guard: a missing, null or
                # string `app` yields `""`. No `or {}` — it was dead, since
                # `isinstance` has already established a dict by then.
                "identity": (
                    _rest_str(run["app"].get("slug"))
                    if isinstance(run.get("app"), dict)
                    else ""
                ),
            }
        )
    creators = status_creators or {}
    for status in statuses:
        if not isinstance(status, dict):
            continue
        state = _rest_str(status.get("state")).upper()
        rows.append(
            {
                "name": _rest_str(status.get("context")) or "status",
                "state": state,
                "bucket": _REST_BUCKETS.get(state, "pending"),
                "description": _rest_str(status.get("description")),
                # Deliberately EMPTY, matching what the `gh` path effectively
                # provides: gh reports a StatusContext's startedAt as the zero
                # time, which `_age_minutes` rejects, so the grace clock falls
                # back to when THIS ENGINE first saw the bot pending — which is
                # what #19's guard specifies ("a queued bot is slow, not
                # unavailable", measured from our own first sighting).
                #
                # An earlier version passed REST's real `created_at` through here
                # on the theory that a true stamp beats no stamp. That inverted
                # the guard: a bot queued 45 minutes ago got ZERO grace instead of
                # a full window, and because the persisted `bot_pending_since` is
                # only written when our own clock is used, every later poll
                # re-read the same expired age. `gh` refused the identical live
                # state. The transport's job is parity with `gh`, not improving
                # on it.
                "startedAt": "",
                "identity": _rest_str(creators.get(_rest_str(status.get("context")))),
            }
        )
    return rows


def _newest_status_creators(statuses: list[dict]) -> dict[str, str]:
    """``{context: creator.login}`` for the NEWEST status per context (#95).

    ``/commits/{sha}/statuses`` returns the full history, so one context appears
    once per posting — this repo's own PR head carries three ``CodeRabbit`` rows
    (two ``pending``, then ``success``). Only the newest matters, and taking any
    other row would be the fail-open direction: a context whose latest posting
    came from a forged writer would still resolve to the real reviewer's identity
    from an older row, and the forged description would then cancel the block
    under a trusted name.

    Newest is computed, not assumed from response order. GitHub happens to return
    these newest-first, but ordering is not part of the contract this engine can
    rely on, and the consequence of being wrong is a security decision rather than
    a display nit. ``created_at`` is the key, with the monotonic ``id`` as the
    tie-break for two postings in the same second.

    **The ``created_at`` compare is lexicographic, and that is correct only
    because GitHub emits fixed-width Z-suffixed UTC timestamps** — the same
    assumption ``bot_review_coverage`` states about its own recency compare. It is
    safe *here* for a stronger reason than shape: both ``created_at`` and
    ``creator`` on this endpoint are **server-assigned**, so neither is
    attacker-suppliable, and a malformed value is therefore not a live route. A
    non-ISO string would nevertheless sort above a real timestamp and win the
    identity pick — the fail-open shape this function exists to prevent. So if
    this helper is ever pointed at a less-trusted source, the compare needs
    hardening first; the guarantee is about the source, not about the parse.
    """
    newest: dict[str, tuple[str, int, str]] = {}
    for status in statuses:
        if not isinstance(status, dict):
            continue
        context = _rest_str(status.get("context"))
        if not context:
            continue
        creator = status.get("creator")
        login = _rest_str(creator.get("login")) if isinstance(creator, dict) else ""
        raw_id = status.get("id")
        # bool is an int subclass and `True` would sort as 1; a non-numeric id
        # sorts as 0 rather than raising, since the timestamp is the primary key
        # and this only breaks ties.
        status_id = raw_id if isinstance(raw_id, int) and not isinstance(raw_id, bool) else 0
        key = (_rest_str(status.get("created_at")), status_id, login)
        if context not in newest or key > newest[context]:
            newest[context] = key
    return {context: key[2] for context, key in newest.items()}


def _rest_object(data: Any, what: str) -> dict:
    """Return ``data`` as a dict, or raise the error ``main`` knows how to print.

    Every REST read of an OBJECT passes through this; the list reads raise their
    own equivalent inside ``_http_get_all`` / ``_http_get_all_wrapped``. (An
    earlier version of this docstring claimed "every REST read", while the four
    list reads silently dropped a wrong-typed page — the fail-open that claim
    concealed.) ``main`` catches
    ``(RuntimeError, KeyError, ValueError)``, so a ``null`` or list body reaching
    ``.get`` raises ``AttributeError`` and escapes as a traceback instead of
    ``error: …`` + exit 2. GitHub really does return a bare ``null`` body, and an
    error payload for these endpoints is a dict with no expected keys, so this is
    the ordinary failure path rather than a defensive nicety.
    """
    if not isinstance(data, dict):
        raise RuntimeError(f"{what} response was not a JSON object")
    return data


def _coerce_review_timestamp(raw: dict) -> str:
    """The review's submission time, or `""` when it is unusable.

    Extracted so the property the comment in `bot_review_coverage` argues for is
    reachable by a focused test, and so the two spellings live in one place.

    A clarity change only. An earlier version of this docstring justified the
    extraction by claiming the property had been unpinned; a review checked and
    found both mutation forms — `str(x)` and `str(x) if x is not None else ""` —
    already killed on both trees. It keeps the two spellings in one place; it did
    not close a coverage gap.
    """
    submitted = raw.get("submittedAt")
    if not isinstance(submitted, str):
        submitted = raw.get("submitted_at")  # REST's spelling
    return submitted if isinstance(submitted, str) else ""


def _rest_review_decision(reviews: list[dict]) -> str | None:
    """Derive GraphQL's ``reviewDecision`` from a REST reviews list.

    Load-bearing, not cosmetic. :func:`build_report` raises a merge blocker on
    ``CHANGES_REQUESTED``; leaving this ``None`` on the REST path meant an
    explicit "request changes" produced NO blocker there while blocking on `gh`
    — a fail-open in the merge gate, and the one direction this transport must
    never introduce.

    Only each reviewer's LATEST verdict counts: a CHANGES_REQUESTED that the
    same reviewer later replaced with an APPROVED must not keep blocking.
    ``COMMENTED`` and ``PENDING`` submissions carry no verdict and are skipped,
    so they cannot displace an earlier one. REST returns reviews oldest-first.

    Dismissals ARE handled: dismissing a review rewrites its ``state`` to
    ``DISMISSED``, so it counts as that reviewer's latest verdict and clears an
    earlier block. An earlier version of this docstring claimed REST does not
    expose them and that a dismissal therefore produced a spurious blocker —
    both false, and the code already disagreed with it.

    Still an approximation of GraphQL's field, in one direction that is worth
    naming: it does not know about required-reviewer rules, so where GraphQL
    would say ``REVIEW_REQUIRED`` this returns ``None``. That yields no blocker
    where GraphQL also raises none from this field, so nothing is lost — the
    merge gate's own review-receipt requirement is what covers that case.
    """
    latest: dict[str, str] = {}
    for review in reviews or []:
        if not isinstance(review, dict):
            continue
        verdict = str(review.get("state") or "").upper()
        if verdict not in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            continue
        user = review.get("user")
        # isinstance, not `or {}`: a STRING `user` passes the truthiness test and
        # then raises AttributeError on `.get`, which `main` does not catch — so
        # an ordinary poll would end in a traceback instead of `error: …`.
        # (`user: null` is real — GitHub returns it for deleted accounts.)
        author = (user.get("login") if isinstance(user, dict) else None) or "?"
        latest[author] = verdict
    verdicts = set(latest.values())
    if "CHANGES_REQUESTED" in verdicts:
        return "CHANGES_REQUESTED"
    if "APPROVED" in verdicts:
        return "APPROVED"
    return None


def _rest_fetch_checks(
    sha: str, *, token: str, slug: tuple[str, str] | None = None
) -> tuple[list[dict], list[dict]]:
    """Both check surfaces for one commit: Checks API runs + combined statuses."""
    slug = slug if slug is not None else _rest_repo_slug()
    check_runs = _http_get_all_wrapped(
        _rest_api(f"commits/{sha}/check-runs?per_page=100", slug), token, "check_runs"
    )
    # Paginated for the same reason check-runs is, and it was not: this is the
    # StatusContext surface, which is the one #23 is actually about — a
    # rate-limited CodeRabbit announced its outage ONLY as the description on an
    # otherwise-SUCCESS status context. A single unpaginated GET here dropped the
    # `Link` header, so past 100 contexts the missing ones read as "not present"
    # rather than "not yet read" — the exact false green the sibling read's
    # docstring cites, in the same function.
    statuses = _http_get_all_wrapped(
        _rest_api(f"commits/{sha}/status?per_page=100", slug), token, "statuses"
    )
    return check_runs, statuses


def rest_pr_view(pr: int, *, token: str) -> tuple[dict, list[dict]]:
    """REST equivalent of the ``gh pr view`` + inline-comments fetch in :func:`main`.

    Returns ``(view, inline)`` in the shape :func:`build_report` consumes. REST
    spells a comment's author ``user`` where GraphQL spells it ``author``, which
    :func:`_author` already handles, so no renaming is needed.
    """
    slug = _rest_repo_slug()
    pr_data = _rest_object(_http_get(_rest_api(f"pulls/{pr}", slug), token)[0], f"PR #{pr}")
    head = pr_data.get("head")
    sha = head.get("sha") if isinstance(head, dict) else None
    if not sha:
        raise RuntimeError(f"PR #{pr} response carried no usable head SHA")
    check_runs, statuses = _rest_fetch_checks(sha, token=token, slug=slug)
    reviews = _http_get_all(_rest_api(f"pulls/{pr}/reviews?per_page=100", slug), token)
    view = {
        "number": pr_data.get("number"),
        "title": pr_data.get("title"),
        "url": pr_data.get("html_url"),
        # REST spells a merged PR `state: "closed"` + `merged: true`, where
        # GraphQL says `MERGED`. `build_report` blocks on any non-OPEN state
        # either way, so this is about the blocker naming the right reason
        # rather than about whether one fires.
        "state": (
            "MERGED"
            if pr_data.get("merged")
            else str(pr_data.get("state") or "").upper()
        ),
        "isDraft": bool(pr_data.get("draft")),
        "baseRefName": (pr_data.get("base") or {}).get("ref"),
        # REST's `mergeable_state` (clean/dirty/blocked/behind/unstable/…) is a
        # different enum than GraphQL's `mergeStateStatus`, passed through
        # upper-cased. This DOES feed a merge blocker: `build_report` branches on
        # `UNSTABLE` and on anything outside {CLEAN, HAS_HOOKS}. The two enums
        # happen to overlap on the values that matter, but the mapping is
        # approximate and #94 should verify it rather than inherit it.
        "mergeStateStatus": (str(pr_data.get("mergeable_state") or "").upper() or None),
        "reviewDecision": _rest_review_decision(reviews),
        "headRefOid": sha,
        "statusCheckRollup": _rest_check_rows(check_runs, statuses),
        "reviews": reviews,
        "comments": _http_get_all(
            _rest_api(f"issues/{pr}/comments?per_page=100", slug), token
        ),
    }
    inline = _http_get_all(_rest_api(f"pulls/{pr}/comments?per_page=100", slug), token)
    return view, inline


_bot_signal_warned = False


def _warn_bot_signal_lost(reason: str) -> None:
    """Say once, on stderr, that the review-bot guards are running blind.

    Once per process. The engine runs as a fresh process per round, so that is
    also once per poll — loud rather than silent, which is the point: a lost bot
    signal must not be mistakable for a clean one.
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


def _outage_row_present(rows: list[dict], bots: tuple[str, ...]) -> bool:
    """Whether any row could cancel a pending block — i.e. whether identity matters.

    The precondition for the whole #95 identity read. A poll with no
    bot-named, outage-marked row has no fail-open decision to make, so resolving
    identities would cost a round trip (two, on the `gh` backend) to change
    nothing. This is the overwhelmingly common case: a healthy reviewer never
    matches it.

    Deliberately evaluated over the SAME predicates
    :func:`summarize_review_bots` uses — an unanchored name match and
    :func:`review_unavailable_reason` — so the two cannot disagree about whether
    a row is interesting. A narrower test here would skip the fetch for a row the
    consumer then judges on an empty identity, which reads as untrusted and would
    silently disable the outage path.
    """
    for row in rows:
        name = str(row.get("name") or row.get("context") or "")
        if not _match_bot(name, bots):
            continue
        if review_unavailable_reason(str(row.get("description") or "")):
            return True
    return False


def _gh_api_pages(path: str) -> list:
    """``gh api --paginate --slurp`` for one path — the list of PAGES, or ``[]``.

    ``--slurp`` is what makes ``--paginate`` usable here: without it, gh
    concatenates one JSON document per page, which is not parseable as a single
    value for the object-shaped ``check-runs`` endpoint. With it, both endpoints
    return a list whose elements are pages — page objects for ``check-runs``,
    page lists for ``statuses``. Verified on gh 2.96.0.

    Never raises. Every failure — an old gh without ``--slurp``, no auth, a
    network error — degrades to ``[]``, which resolves no identities and so reads
    as untrusted. See :func:`summarize_review_bots` for why that direction is
    bounded rather than a wedge.

    **``OSError``/``SubprocessError`` are caught here, not left to ``_gh``.**
    ``_gh`` translates only ``TimeoutExpired`` into ``RuntimeError``; a missing
    binary, a spawn failure (ENOMEM, EAGAIN, too many open files) or any other
    ``SubprocessError`` escapes it raw. :func:`fetch_check_details` is documented
    as never raising and its caller in ``main`` sits **outside** the try
    deliberately, so one of those would crash the poll *before* ``persist_poll``
    — no state written, every later poll repeating it. That is the wedge shape
    ``_rest_str`` documents, reached from a different direction. ``gh`` existing
    at backend-resolution time does not settle it: resolution and this call are
    not the same moment, and fork can fail for reasons unrelated to the binary.
    The `gh` branch of :func:`fetch_check_details` already catches this exact
    class around its own ``subprocess.run``; this keeps the new call sites
    consistent with it rather than a narrower rule three lines away.
    """
    try:
        raw = _gh(["api", "--paginate", "--slurp", path])
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _gh_head_sha(pr: int) -> str:
    """The PR's current head sha via ``gh``, or ``""`` when it cannot be read.

    Never raises, for the same reason :func:`_gh_api_pages` does not: it is
    reached from :func:`fetch_check_details`, which is documented as
    never-raising and whose caller in ``main`` sits outside the try. ``_gh``
    translates only ``TimeoutExpired``, so the process-level classes are caught
    here explicitly.
    """
    try:
        data = _gh_json(["pr", "view", str(pr), "--json", "headRefOid"]) or {}
        return str(data.get("headRefOid") or "")
    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        AttributeError,
    ):
        return ""


def _gh_identity_map(sha: str) -> dict[str, str]:
    """``{check name: creator identity}`` for one commit, via ``gh api`` (#95).

    ``gh pr checks --json`` exposes no creator on either surface — its full field
    set is ``bucket, completedAt, description, event, link, name, startedAt,
    state, workflow``, verified by probing an invalid field on gh 2.96.0 — so the
    `gh` backend has to ask REST for identity even though its rows come from the
    CLI. The rows are then joined by NAME, which the REST backend does not need
    to do: there, each check run carries its own ``app``.

    **A name that resolves to more than one distinct identity resolves to none.**
    Two check runs may share a name, and gh's rows carry nothing to tell them
    apart — so if the real reviewer's check and a forged one are both called
    ``CodeRabbit``, picking either is a guess. Picking the trusted one is the
    fail-OPEN guess: it would let the forged row's description cancel the block
    under the real app's identity. Collapsing to no identity instead costs the
    grace window and cannot be gamed, and an attacker can force this state
    anyway — which is exactly why it must be the harmless one.

    The join is keyed by name across **both** surfaces, so a status context and a
    check run sharing one name string collapse together before the ambiguity test
    runs, and a resolvable identity can read as ambiguous. Left as is: the effect
    is the fail-closed one above — extra waiting, never a bypass — and separating
    the namespaces would mean carrying a surface tag through rows that
    `gh pr checks` returns without one.
    """
    identities: dict[str, set[str]] = {}

    def record(name: str, identity: str) -> None:
        if name:
            identities.setdefault(name, set()).add(identity)

    for page in _gh_api_pages(f"repos/{{owner}}/{{repo}}/commits/{sha}/check-runs?per_page=100"):
        runs = page.get("check_runs") if isinstance(page, dict) else None
        for run in runs or []:
            if not isinstance(run, dict):
                continue
            app = run.get("app")
            record(
                _rest_str(run.get("name")),
                _rest_str(app.get("slug")) if isinstance(app, dict) else "",
            )
    status_pages = _gh_api_pages(
        f"repos/{{owner}}/{{repo}}/commits/{sha}/statuses?per_page=100"
    )
    flat_statuses = [
        status for page in status_pages if isinstance(page, list) for status in page
    ]
    for context, login in _newest_status_creators(flat_statuses).items():
        record(context, login)
    return {
        name: next(iter(found))
        for name, found in identities.items()
        if len(found) == 1 and next(iter(found))
    }


def fetch_check_details(
    pr: int, *, bots: tuple[str, ...] | None = None, head_sha: str | None = None
) -> CheckDetails:
    """Per-check ``{name, state, bucket, description, startedAt, identity}`` for one PR.

    ``identity`` is the #95 addition: the creator a check is attributable to,
    which the outage path requires before letting a description cancel a pending
    reviewer. It is resolved **lazily** — only when :func:`_outage_row_present`
    finds a row that could cancel something — so a healthy poll pays nothing.
    Every row carries the key on **both** backends whether or not that read ran;
    an unresolved one is ``""``, which reads as untrusted. Consumers still use
    ``.get`` — the uniform key exists so a future reader who indexes it is not
    punished on the common path, not as a licence to drop the default.

    ``head_sha`` is an optimisation for the `gh` backend only. That backend needs
    a commit SHA to reach the REST identity endpoints and has none to hand, so
    without this it spends a ``gh pr view`` to find one. Both call sites already
    hold the head from their own snapshot. The REST backend ignores it and keeps
    deriving the SHA from its own ``pulls/{pr}`` read, so the identity it resolves
    can never be for a different commit than the rows it shaped.

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

    **On the REST backend this is not optional plumbing.** Leaving it shelling
    out to a `gh` that is not installed would degrade to ``([], "unavailable")``
    on *every* poll. The warning is once-per-process, and since this engine runs
    as a fresh process per round that is also once per poll — so it is loud rather
    than silent, but both guards are dead while the loop keeps reporting. A rate-limited reviewer would read as a
    clean one, in the engine that decides a PR is safe to merge. So the REST
    path supplies the same three fields from the Checks API and the combined
    status API — see :func:`_rest_check_rows`.
    """
    if bots is None:
        bots = _REVIEW_BOTS
    if not bots:
        return CheckDetails([], "skipped")
    try:
        backend, token = _resolve_backend()
    except RuntimeError as exc:
        # No usable backend at all. Reached only if some caller invokes this
        # before `main`'s own fetch has raised; degrade the same way as any
        # other failed read rather than raising out of a never-raises function.
        _warn_bot_signal_lost(str(exc))
        return CheckDetails([], "unavailable")
    if backend == "rest":
        try:
            slug = _rest_repo_slug()
            pr_data = _rest_object(
                _http_get(_rest_api(f"pulls/{pr}", slug), token)[0], f"PR #{pr}"
            )
            sha = (pr_data.get("head") or {}).get("sha")
            if not sha:
                raise RuntimeError(f"PR #{pr} response carried no head SHA")
            check_runs, statuses = _rest_fetch_checks(sha, token=token, slug=slug)
            rows = _rest_check_rows(check_runs, statuses)
            # The #95 identity read, only when a row could actually cancel a
            # pending block. Check runs already carry `app.slug` from the fetch
            # above; it is the STATUS surface that needs a second endpoint,
            # because the combined-status read has no `creator`.
            if _outage_row_present(rows, bots):
                # ITS OWN try, inside the outer one. `rows` above is already read
                # and already carries the outage marker; letting a failure in this
                # third call discard it would take #19's and #23's guards dark for
                # the whole poll over a transient 403 or a network blip — the same
                # "silent bypass, and the worse of the two" shape as the
                # wrong-reader bug, reached by ordinary flakiness instead of by a
                # defect. Degrading to no-identity keeps every row and costs at
                # most the grace window, and it is what the `gh` backend already
                # does (`_gh_api_pages` swallows the same classes and returns
                # `{}`), so this is the transport parity this file's own doctrine
                # asks for rather than a new policy.
                #
                # Not silent: an unresolved identity renders as the explicit
                # "creator is unattributable … does NOT cancel a pending review"
                # line, so the operator sees the degradation at merge time.
                try:
                    # `_http_get_all`, NOT `_http_get_all_wrapped`. The PLURAL
                    # `/commits/{sha}/statuses` endpoint's body IS the array;
                    # only the SINGULAR combined `/status` wraps it in
                    # `{"state": …, "statuses": [...]}`. The two differ by one
                    # character in the URL and by their whole shape, and
                    # `_rest_fetch_checks` above reads the singular one with the
                    # wrapped reader and the key `"statuses"` — so reusing that
                    # call's shape here raised `RuntimeError` ("returned list,
                    # expected a JSON object"), which this function's handler then
                    # degraded to `([], "unavailable")`, discarding EVERY row
                    # rather than just the identities. That switched #19's and
                    # #23's guards off in exactly the case they exist for — an
                    # outage-marked row — and `record_review` names that state as
                    # "the SILENT bypass, and the worse of the two", because no
                    # blockers means no refusal.
                    creators = _newest_status_creators(
                        _http_get_all(
                            _rest_api(f"commits/{sha}/statuses?per_page=100", slug),
                            token,
                        )
                    )
                except (
                    RuntimeError,
                    OSError,
                    KeyError,
                    ValueError,
                    AttributeError,
                    TypeError,
                ):
                    creators = None
                # `is not None`, not a truthy test, so "the read returned no
                # creators" and "the read failed" stay distinguishable at the type
                # level. Be honest about what that buys TODAY: nothing
                # behavioural — `_rest_check_rows` normalizes `status_creators or
                # {}`, so recomputing with `{}` and leaving `rows` as first built
                # produce identical output, and a truthy test here passes every
                # test. It is written this way so the distinction survives if that
                # normalization ever stops, not because it currently decides
                # anything.
                if creators is not None:
                    rows = _rest_check_rows(
                        check_runs, statuses, status_creators=creators
                    )
        # AttributeError/TypeError included on purpose: this function is called
        # OUTSIDE `main`'s try, so anything escaping here crashes the whole poll
        # rather than degrading. A `null` or list body would otherwise raise
        # AttributeError from `.get`, which no handler upstream catches.
        except (RuntimeError, OSError, KeyError, ValueError, AttributeError, TypeError) as exc:
            _warn_bot_signal_lost(str(exc))
            return CheckDetails([], "unavailable")
        return CheckDetails(rows, "ok")
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
    rows = [item for item in parsed if isinstance(item, dict)]
    # Unconditionally, so the key's presence does not depend on whether the
    # identity read ran. `summarize_review_bots` uses `.get`, so this changes no
    # behaviour today — it keeps the docstring's "every row gets the key" true on
    # this backend as well as REST, and stops a future reader's `row["identity"]`
    # from raising on the common (healthy) poll.
    for row in rows:
        row.setdefault("identity", "")
    # The #95 identity read on the `gh` backend. Same precondition as the REST
    # branch, but both surfaces need the extra call here, since `gh pr checks`
    # carries no creator on either.
    if _outage_row_present(rows, bots):
        sha = head_sha or _gh_head_sha(pr)
        identities = _gh_identity_map(sha) if sha else {}
        # Fail closed if the head moved across this read. `gh pr checks` always
        # reports the PR's CURRENT head and carries no sha, while identities are
        # resolved for `sha` — so a push landing between the two calls leaves rows
        # from one commit joined, BY NAME, to identities from another. A same-repo
        # PR can push, which is the capability #95 already assumes, so a forged
        # row on the new commit could inherit the real reviewer's identity from a
        # same-named check on the old one — a bypass of this very guard.
        #
        # `record_review`'s `current_head != expected_head` check does not cover
        # it: that compares the caller's `--head` against its snapshot, not the
        # snapshot against this function's own later reads.
        #
        # Dropping every identity on any movement is the cheap fail-closed
        # answer, and it costs only the grace window. The REST branch needs none
        # of this: it derives one sha and reads both surfaces for it.
        #
        # **This fires on two different conditions and cannot tell them apart**,
        # so do not read a drop here as evidence a push happened. `_gh_head_sha`
        # returns `""` when it merely FAILS — a network blip, a `gh` hiccup — and
        # `"" != sha` is indistinguishable from a real move. Both are treated the
        # same on purpose: identity we cannot confirm for this exact commit is
        # identity we will not trust, and a transient failure is not a licence to
        # keep the previous answer. The cost is the same bounded one either way.
        #
        # A narrower residual window stays open and is not closed by this: a
        # double push that moves the head away and back to the SAME sha between
        # the two reads passes the comparison. These are two point-in-time reads,
        # not one joint fetch, and `gh pr checks` exposes no sha to make it one.
        if identities and sha and _gh_head_sha(pr) != sha:
            identities = {}
        for row in rows:
            row["identity"] = identities.get(str(row.get("name") or ""), "")
    return CheckDetails(rows, "ok")


def resolve_pr(explicit: int | None) -> int:
    """Return the PR number — explicit, or the current branch's open PR."""
    if explicit is not None:
        return explicit
    backend, token = _resolve_backend()
    if backend == "rest":
        return rest_resolve_pr(None, token=token)
    data = _gh_json(["pr", "view", "--json", "number"])
    return int(data["number"])


def fetch_pr_view(pr: int) -> tuple[dict, list[dict]]:
    """The PR snapshot + its inline review comments, from either backend.

    One function rather than two call sites so the `gh` and REST paths cannot
    drift into returning different field sets.
    """
    backend, token = _resolve_backend()
    if backend == "rest":
        return rest_pr_view(pr, token=token)
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
    return view, inline


def fetch_review_snapshot(pr: int) -> dict:
    """``number``/``headRefOid``/``reviews`` for one PR. ``gh`` only.

    No REST branch on purpose: its only caller is :func:`record_review`, which
    writes a receipt that authorizes a merge, and :func:`require_gh_backend`
    refuses that on REST before this is reached.
    """
    return _gh_json(["pr", "view", str(pr), "--json", "number,headRefOid,reviews"])


def _read_is_draft(pr: int) -> bool:
    """Read the PR's current isDraft bit (coerced to bool). ``gh`` only.

    No REST branch: the only caller is :func:`assert_draft_state`, which runs
    :func:`require_gh_backend` first. A REST branch here would be unreachable
    code whose only test justified itself by naming flags that cannot reach it.
    """
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
    drifted, issues the corrective `gh pr ready [--undo] <pr>` — idempotent, so a
    stale initial read that drove a redundant call is harmless — then re-reads to
    confirm with a bounded settle-retry (gh's draft bit can lag the mutation).

    ``gh`` only: this MUTATES the PR, and :func:`require_gh_backend` refuses it on
    the REST backend before this is reached.
    Returns a report dict: {pr, want_draft, initial_draft, corrected: bool,
    final_draft, ok: bool}. `ok` is True iff final_draft == want_draft.
    """
    require_gh_backend("--assert-draft/--assert-ready")
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
    separately requires current-head independent-review evidence — either a
    ``--record-review`` receipt or a configured bot's own review of that head
    (:func:`qualifying_bot_coverage`) — so on a CI-less repo that evidence
    becomes the only gate, which is why the flag is opt-in per repo rather than
    inferred from an empty rollup.
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


def review_unavailable_reason(body: str, *, author: str | None = None) -> str | None:
    low = (body or "").lower()
    reason = next(
        (marker for marker in _REVIEW_UNAVAILABLE_MARKERS if marker in low), None
    )
    if reason is None:
        return None
    # Comment bodies are untrusted prose: tracker mirrors and humans can quote
    # an outage message without being the reviewer that emitted it. Only a
    # configured review-bot author may turn such text into an action signal.
    # ``author=None`` is reserved for trusted check descriptions and direct
    # marker classification, whose identity is scoped by the caller.
    if author is not None and _match_bot(author, _REVIEW_BOTS, anchored=True) is None:
        return None
    return reason


def untrusted_review_unavailable_candidate(
    body: str, *, author: str | None = None
) -> str | None:
    """Legacy-prefix outage text that needs explicit alias configuration.

    This is deliberately not reviewer evidence. It only keeps a formerly
    accepted custom-bot notice visible instead of letting an overlapping noise
    marker hide the migration gap.
    """
    if author is None:
        return None
    reason = review_unavailable_reason(body)
    if reason is None or review_unavailable_reason(body, author=author) is not None:
        return None
    low_author = str(author).strip().lower()
    return next((reason for bot in _REVIEW_BOTS if low_author.startswith(bot)), None)


def is_noise(body: str, *, author: str | None = None) -> bool:
    low = (body or "").lower()
    if review_unavailable_reason(body, author=author) is not None:
        return False
    if untrusted_review_unavailable_candidate(body, author=author) is not None:
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
        # Elements, not just the page: `_http_get_all` proves the RESPONSE is a
        # list; a hostile or malformed element inside it still reaches `.get`
        # here, and `build_report` runs outside `main`'s try, so an
        # AttributeError from a string element exits 1 with a traceback rather
        # than `error: …`. Same for the two surfaces below.
        if not isinstance(raw, dict):
            continue
        body = raw.get("body") or ""
        author = _author(raw)
        unavailable = review_unavailable_reason(body, author=author)
        untrusted = untrusted_review_unavailable_candidate(body, author=author)
        out.append(
            {
                "key": _comment_key("issue", raw),
                "content_key": _content_key("issue", author, body),
                "kind": "issue",
                "author": author,
                "path": None,
                "line": None,
                "body": body,
                "review_unavailable_reason": unavailable,
                "untrusted_review_unavailable_candidate": untrusted,
            }
        )
    for raw in view.get("reviews") or []:
        if not isinstance(raw, dict):
            continue
        body = raw.get("body") or ""
        if not body.strip():  # an approve/comment with no text carries no finding
            continue
        author = _author(raw)
        out.append(
            {
                "key": _comment_key("review", raw),
                "content_key": _content_key("review", author, body),
                "kind": "review",
                "author": author,
                "path": None,
                "line": None,
                "body": body,
                "review_unavailable_reason": review_unavailable_reason(body, author=author),
                "untrusted_review_unavailable_candidate": untrusted_review_unavailable_candidate(
                    body, author=author
                ),
            }
        )
    for raw in inline or []:
        if not isinstance(raw, dict):
            continue
        body = raw.get("body") or ""
        author = _author(raw)
        out.append(
            {
                "key": _comment_key("inline", raw),
                "content_key": _content_key("inline", author, body),
                "kind": "inline",
                "author": author,
                "path": raw.get("path"),
                "line": raw.get("line") or raw.get("original_line"),
                "body": body,
                "review_unavailable_reason": review_unavailable_reason(body, author=author),
                "untrusted_review_unavailable_candidate": untrusted_review_unavailable_candidate(
                    body, author=author
                ),
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
        and not is_noise(c["body"], author=c["author"])
    ]


def _match_bot(text: str, bots: tuple[str, ...], *, anchored: bool = False) -> str | None:
    """The configured review bot named in ``text``, if any. Case-insensitive.

    Substring matching is only for check names: one bot key (``coderabbit``)
    has to cover both ``CodeRabbit`` and a namespaced variant such as ``Review /
    CodeRabbit``.

    ``anchored`` selects exact normalized author matching and is used for
    comment authors because that input is not the repo's to control: on a public
    repo any account may comment. Each configured bot trusts its exact key, its
    conventional ``[bot]`` form, and explicitly enumerated service aliases.

    **A check NAME is not a trust boundary either, and the unanchored branch is
    no longer relied on as one** (#95). An earlier version of this docstring said
    check names "come from the repo's own CI and bot configuration" — which is
    false for a pull request, because a same-repo PR's own workflow runs with
    ``checks: write`` and can create a check named anything. The looseness here is
    kept, because it is what lets one key cover ``CodeRabbit`` and ``Review /
    CodeRabbit``, and because everything it now decides is fail-CLOSED: a forged
    name can only *add* a pending entry that blocks the PR that forged it. The
    one decision that was fail-open — a check description cancelling the pending
    block — moved to :func:`_match_bot_identity` over an unforgeable creator
    identity. Different rules because the inputs have different trust; the
    correction is about which decisions may rest on which input.
    """
    low = str(text or "").strip().lower()
    if not low:
        return None
    if anchored:
        for bot in bots:
            trusted = {bot, f"{bot}[bot]", *_REVIEW_BOT_AUTHOR_ALIASES.get(bot, ())}
            if low in trusted:
                return bot
        return None
    return next((bot for bot in bots if bot in low), None)


def _trusted_bot_identities(
    bot: str,
    *,
    aliases: dict[str, frozenset[str]] | None = None,
    app_slugs: dict[str, frozenset[str]] | None = None,
) -> frozenset[str]:
    """The creator identities allowed to announce an outage for ``bot`` (#95).

    Two namespaces reach this, and both are normalized to the same set because a
    row carries one or the other, never both:

    - a **check run**'s ``app.slug`` (``coderabbitai``, ``github-actions``)
    - a **status context**'s ``creator.login`` (``coderabbitai[bot]``)

    Derived from the tables an adopter already curates — the bot key, its
    conventional ``[bot]`` form, its enumerated author aliases, and any extra
    ``bot_app_slugs`` — with each entry also admitted in its ``[bot]``-stripped
    form, because the same service appears as ``coderabbitai[bot]`` on a status
    and ``coderabbitai`` as an app slug. That stripping is a namespace
    normalization, not a widening: it never introduces a string the adopter did
    not write, only the other spelling of one they did.

    **Why derivation rather than a new mandatory key.** Requiring every adopter
    to enumerate app slugs before outage detection worked again would silently
    change behaviour on upgrade for every repo that already has a bot configured
    by name. Deriving from ``bot_author_aliases`` keeps those repos working,
    because a GitHub App's slug and its bot login are conventionally the same
    string. ``bot_app_slugs`` exists for the repos where they are not.
    """
    if aliases is None:
        aliases = _REVIEW_BOT_AUTHOR_ALIASES
    if app_slugs is None:
        app_slugs = _REVIEW_BOT_APP_SLUGS
    named = {bot, f"{bot}[bot]", *aliases.get(bot, ()), *app_slugs.get(bot, ())}
    stripped = {
        name[: -len("[bot]")] for name in named if name.endswith("[bot]") and name != "[bot]"
    }
    return frozenset(
        identity for identity in (named | stripped) if identity and identity != "[bot]"
    )


def _match_bot_identity(
    identity: str,
    bots: tuple[str, ...],
    *,
    aliases: dict[str, frozenset[str]] | None = None,
    app_slugs: dict[str, frozenset[str]] | None = None,
) -> str | None:
    """The bot that ``identity`` is trusted to speak for, or ``None`` (#95).

    Exact normalized match against :func:`_trusted_bot_identities`, never a
    substring or prefix one. Deliberately the same discipline as the anchored
    author branch of :func:`_match_bot`, for the same reason: a substring rule
    would let ``coderabbit-shim`` speak for ``coderabbit``, which is the defect
    this function exists to close.

    An empty ``identity`` — the row's creator could not be resolved — returns
    ``None`` and is therefore untrusted. That is the fail-closed direction and
    its cost is bounded; see :func:`summarize_review_bots`.
    """
    low = str(identity or "").strip().lower()
    if not low:
        return None
    for bot in bots:
        if low in _trusted_bot_identities(bot, aliases=aliases, app_slugs=app_slugs):
            return bot
    return None


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

    Written as observation only, and no longer that: since #350 this output is
    read by :func:`qualifying_bot_coverage`, which lets a bot's own review of
    the current head satisfy the merge gate with no receipt. It still makes the
    gap *visible at merge time* instead of reconstructible only by reading the
    PR thread afterwards — deliberately the cheap half of issue #27, because the
    expensive half (invalidating a receipt when the diff changes shape) risks
    becoming a wedge on a repo whose bot is permanently unavailable.

    **The under-reporting bias below is now load-bearing.** It was a reporting
    preference when nothing gated on it; it is the reason the gate fails closed
    now. A change that made this function report coverage it is less sure of —
    inferring a SHA, treating a comment-shaped verdict as a review (#44) — would
    not merely over-report a warning, it would authorize merges. Widen what
    counts as coverage only with that in view.

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
    return _reduce_latest_bot_reviews(reviews, head, bots)


def _reduce_latest_bot_reviews(
    reviews: list[dict],
    head: str | None,
    bots: tuple[str, ...] | None,
    *,
    states: frozenset[str] | None = None,
) -> list[dict]:
    """Each configured bot's latest review, as the coverage entry shape.

    The shared core of :func:`bot_review_coverage` and
    :func:`bot_head_objections`. They ask different questions of the same review
    list and differ in exactly one parameter, so they are one walk rather than
    two: ``#447`` is this repo's standing account of what happens when a pinned
    copy of a reduction sits beside an unpinned one, and the extraction is here
    so that ``#494``'s fix cannot drift away from the read it corrects.

    ``states`` is the displacement policy, and it is the whole difference:

    - ``None`` — every review participates, so the newest one wins whatever it
      says. That is "which commit did this bot last *look at*", which is what
      coverage reports and what ``#350``'s evidence route needs: a clean review
      is ordinarily ``COMMENTED``, and a rule that let it be outranked would
      leave the ordinary clean review unable to supply evidence.
    - a state set — only those states may displace an earlier entry. That is
      "what is this bot's latest *verdict*", where a non-verdict submission must
      not be able to erase one (``#494``).

    Neither is a safe default for the other question, which is why this takes no
    default: coverage answered the verdict question for one release and a bot's
    own follow-up ``COMMENTED`` at the same head silently cleared its standing
    objection.
    """
    if bots is None:
        bots = _REVIEW_BOTS
    latest: dict[str, dict] = {}
    for raw in reviews or []:
        # Anchored: a comment author is not the repo's to control, so a
        # lookalike login (`xcoderabbit`) must not be able to claim that the
        # reviewer covered this head — nor, since #494 routes the objection read
        # through here too, manufacture an objection, which is the same defect
        # pointed the other way (a denial-of-merge).
        bot = _match_bot(_author(raw), bots, anchored=True)
        if not bot:
            continue
        # BOTH spellings, for the same reason `_author` takes both: GraphQL
        # nests the sha as `commit.oid` and REST returns a bare `commit_id`.
        # Reading only the GraphQL pair made this whole function dead code on
        # the REST backend — every review `continue`d, so `coverage` was always
        # `[]`, the #22/#25 "last review was of <sha>, not the current head"
        # warning never rendered, and `bots_behind_head` was never written to a
        # receipt. Silently, and specifically on the gate this guard protects.
        commit = raw.get("commit")
        sha = commit.get("oid") if isinstance(commit, dict) else raw.get("commit_id")
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
        submitted = _coerce_review_timestamp(raw)
        # The review's own verdict, carried so the merge gate can refuse the
        # ones that are not evidence (see `qualifying_bot_coverage`). Normalized
        # to an upper-case string; a missing or non-string value becomes `""`,
        # which no allowlist matches — the fail-closed direction, and the same
        # under-reporting bias the rest of this function takes.
        state = raw.get("state")
        state = state.strip().upper() if isinstance(state, str) else ""
        # The displacement policy, applied BEFORE the recency compare so a
        # skipped review cannot win on its timestamp. `continue`, not a
        # fall-through: a non-participating review must leave any earlier entry
        # exactly as it stood.
        if states is not None and state not in states:
            continue
        if bot not in latest or submitted >= latest[bot]["submitted_at"]:
            latest[bot] = {
                "bot": bot,
                "sha": sha,
                "submitted_at": submitted,
                "covers_head": sha == head,
                "state": state,
            }
    return sorted(latest.values(), key=lambda e: e["submitted_at"], reverse=True)


def bot_comment_verdicts(
    comments: list[dict],
    head: str | None,
    *,
    bots: tuple[str, ...] | None = None,
) -> list[dict]:
    """Configured bots that announced a COMPLETED review of ``head`` in a comment.

    **Reported, never evidence.** This is the whole of the #44 ruling
    (2026-08-17): a comment-borne verdict is surfaced so a reader can see that
    the reviewer did run, and the receipt stays the act that authorizes the
    merge. Nothing here reaches :func:`qualifying_bot_coverage`,
    ``review_evidence``, or ``merge_blockers``.

    That division is the point rather than a limitation. #44 asks for the other
    thing — parse the comment into ``coverage`` so the gate clears itself — and
    :func:`bot_review_coverage`'s docstring is the standing argument against it:
    *"treating a comment-shaped verdict as a review (#44) would not merely
    over-report a warning, it would authorize merges."* Keying the gate on prose
    means an upstream wording change silently decides merges. Keying a *report*
    on prose means an upstream wording change silently drops a line, and the
    receipt requirement — which was already there — catches it.

    **The problem it reports.** Some reviewers deliver a clean verdict as an
    issue comment and create no review object, so ``coverage`` sees nothing and
    a reviewed PR is indistinguishable from an unreviewed one. Measured on this
    repo (#168): whether a review object exists tracks whether the review *found
    anything* — so the clean pass is exactly the one the gate cannot see. Do not
    reach for "explicitly re-request it and you will get a review object": that
    heuristic held on #87 and failed on #498, where an explicit
    ``@coderabbitai full review`` returned a comment-only verdict.

    **A conjunction, and every term earns its place:**

    1. the author is a configured bot, matched ANCHORED — a comment author is
       not the repo's to control, so a lookalike login must not be able to
       announce that the reviewer passed;
    2. the body matches a ``comment_verdict_markers`` entry — the review
       completed;
    3. the body matches NO ``unavailable_markers`` entry — on #263 a
       rate-limited bot posted a comment naming the commit range it *would have*
       reviewed, so terms 1, 2 and 4 without this one manufacture a verdict for
       a review that never ran;
    4. the body contains ``head`` itself, as a full 40-character SHA.

    **Term 4 is a containment test rather than a parse, deliberately.** The SHA
    sits in an English sentence the bot composes, and two wordings have already
    been observed ("changed between X and Y", "changed from the base of the PR
    and between X and Y"). Matching the sentence would make this depend on
    which one it used; asking whether the head appears at all does not, and it
    answers the only question worth asking here. The cost is that this cannot
    report a verdict for an *older* head — that case reads as no verdict, which
    is the direction that fails toward silence.

    Returns ``[{bot, sha}]``, sorted by bot. ``sha`` is always ``head`` by
    construction — carried anyway because it is the value a reader pastes into
    ``--record-review --head``, and a report field that makes the next command
    obvious is worth one redundant key.
    """
    if not head:
        return []
    bots = _REVIEW_BOTS if bots is None else bots
    found: dict[str, dict] = {}
    for comment in comments or []:
        if not isinstance(comment, dict):
            continue
        bot = _match_bot(_author(comment), bots, anchored=True)
        if not bot:
            continue
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        low = body.lower()
        if not any(marker in low for marker in _COMMENT_VERDICT_MARKERS):
            continue
        # Term 3. Read from the body directly rather than from the comment's
        # precomputed `review_unavailable_reason`: that field is author-scoped
        # for its own purposes, and this is a refusal, so it must not depend on
        # an upstream trust decision made for a different question.
        if any(marker in low for marker in _REVIEW_UNAVAILABLE_MARKERS):
            continue
        if head.lower() not in low:
            continue
        found[bot] = {"bot": bot, "sha": head}
    return [found[bot] for bot in sorted(found)]


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

    - **unavailable** — an ``unavailable_markers`` hit on either trusted surface:
      a comment authored by a configured review bot *or* that bot's check
      description (#23, the surface that was invisible). Never blocks anything.
      It is an action signal: run the fallback review panel
      (docs/agentic-dev-kit/fallback-review-panel.md).

      Only a **check**-surface hit **from a trusted creator** suppresses the
      pending block below. The trust half is #95: a check name is chosen by
      whoever created the check, and on a same-repo PR that can be the PR's own
      workflow — so a check called ``coderabbit-shim`` carrying an outage marker
      used to cancel the real reviewer's pending block and open the merge gate
      mid-review. The cancel now requires the row's creator identity
      (``app.slug`` / ``creator.login``) to match the bot, which a workflow
      cannot forge; the *report* still does not, so the signal to run the panel
      never goes missing. Entries carry ``identity`` and ``trusted`` so the
      difference is visible rather than inferred from whether a block vanished.

      A check describes the bot's state now; a comment describes the past, and
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
    # Bot-attributed comments are reported, but NOT counted toward
    # `unavailable_bots`. `collect_comments` returns the whole PR history,
    # unscoped by head or age, so an outage comment from
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
            # #95: the CANCEL requires an unforgeable identity, the REPORT does
            # not. A same-repo PR's own workflow runs with `checks: write` and
            # `statuses: write`, so it can post a check named `coderabbit-shim`
            # whose description matches an outage marker — and cancelling the
            # pending block is the one thing that opened the merge gate while the
            # real reviewer was mid-review. The row's creator (`app.slug` on a
            # check run, `creator.login` on a status context) is not the PR's to
            # choose: a workflow's GITHUB_TOKEN authenticates as
            # `github-actions`, never as the reviewer's app.
            identity = str(detail.get("identity") or "")
            trusted = _match_bot_identity(identity, bots) == bot
            unavailable.append(
                {
                    "bot": bot,
                    "surface": "check",
                    "where": name,
                    "reason": reason,
                    "identity": identity,
                    "trusted": trusted,
                }
            )
            if trusted:
                unavailable_bots.add(bot)
                continue
            # Untrusted: reported (so the panel signal never regresses), and then
            # this row falls through to the ordinary pending logic below instead
            # of cancelling anything. What that costs depends on the row, and both
            # cases are bounded:
            #
            #   - a TERMINAL row (#23's own case — an outage on an otherwise
            #     SUCCESS context) adds no pending entry at all, so an
            #     unresolvable identity costs exactly nothing here.
            #   - a NON-TERMINAL row becomes a pending entry, which blocks until
            #     `grace_minutes` and then ages out by itself.
            #
            # Neither can wedge the merge gate, which is what makes requiring
            # identity safe as the default rather than an opt-in. The worst an
            # unresolvable identity can do is delay a merge by the grace window —
            # the same bound a bot that never reports already has.
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
        # subject is what a receipt covers. Reported — and, since #350, GATING:
        # `qualifying_bot_coverage` reads this to satisfy the merge gate's
        # independent-review requirement without a receipt.
        "coverage": bot_review_coverage(reviews or [], head, bots=bots),
        # The verdict-only reduction over the SAME reviews, read by
        # `objecting_bot_coverage` (#494). Computed here for the reason coverage
        # is — so the `record_review` path gets it too — and reported rather than
        # kept internal, because the merge gate's refusal side should be as
        # inspectable in `--json` as its evidence side. The two lists differ only
        # where a bot's latest review carries no verdict, which is precisely the
        # case that used to be invisible.
        "objections": bot_head_objections(reviews or [], head, bots=bots),
        # Comment-borne clean verdicts for this head (#44). REPORTED ONLY — no
        # gate reads this, by ruling. See `bot_comment_verdicts`. Empty on the
        # `record_review` path, which passes no comments; that path does not
        # read this field either.
        "comment_verdicts": bot_comment_verdicts(comments or [], head, bots=bots),
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


# Review states that are EVIDENCE of a completed, standing review. An
# allowlist, never a denylist, for the reason every identity rule in this file
# is an allowlist: an unrecognized value must fail closed, and GitHub is free to
# add a state tomorrow that this file has never heard of.
#
# Each exclusion is a case the merge gate was measured to accept before this
# existed (#484's adversarial panel round, plus two the author found extending
# it), and each is one where a merge would rest on something that is not a
# standing verdict:
#
#   DISMISSED         a maintainer said explicitly "this review does not count".
#                     `_rest_review_decision` already honours dismissal for the
#                     CHANGES_REQUESTED blocker; the gate must not disagree with
#                     it one function away.
#   PENDING           not submitted. There is no verdict yet, only a draft.
#   CHANGES_REQUESTED an unresolved objection, and not reliably covered by the
#                     separate `reviewDecision` blocker — reliably meaning
#                     ACROSS TRANSPORTS, which is the whole of the argument:
#                     on the REST path `_rest_review_decision` aggregates every
#                     reviewer's latest verdict with no required-reviewer
#                     notion (its own docstring says so), so a bot's
#                     CHANGES_REQUESTED DOES raise that blocker there. On the
#                     `gh` path the field is GitHub's own, which does reflect
#                     required-reviewer rules, and a bot is typically not a
#                     required reviewer. A guard that holds on one transport
#                     and not the other is not a guard, so this list does not
#                     lean on it either way. Measured on the `gh` shape at the
#                     time of #484: with `reviewDecision: ""`, the gate returned
#                     mergeable with no blockers at all. Re-measuring that today
#                     gives a different answer, and the exclusion is not why —
#                     `objecting_bot_coverage` now raises a blocker of its own
#                     for this state (#485). The dating matters: the figure is
#                     kept as the observation that motivated the exclusion, not
#                     as a claim about current behaviour.
#
# APPROVED and COMMENTED both qualify. COMMENTED is not a weaker signal here —
# it is the state CodeRabbit's own reviews actually carry on this repo,
# including its clean ones (verified against PR #484's live review list), so
# excluding it would leave the coverage route dead for the reviewer it was
# written for.
_EVIDENTIAL_REVIEW_STATES = frozenset({"APPROVED", "COMMENTED"})


def qualifying_bot_coverage(review_bots: dict, head: str | None) -> list[str]:
    """Configured bots whose OWN review covers ``head`` well enough to gate on.

    The second route to :func:`decide_mergeable`'s independent-review
    requirement, beside a ``--record-review`` receipt (issue #350, direction 1).

    **Why a second route exists at all.** The receipt vocabulary is three
    literals and every one names a *fallback* pass. When the configured bot
    itself reviewed the head, recording any of them asserts a pass that did not
    run — so the honest agent recorded nothing and ``mergeable`` was
    unreachable. That wedged the merge gate precisely when review had gone
    *well*, and it wedged it hardest on an autonomous lane, whose
    ``dev_session.sh merge`` reads ``mergeable`` and nothing else.

    **Why this route is safe where a fourth receipt literal would not have
    been.** Every receipt is SELF-REPORTED: the agent that wants the merge
    writes it, and nothing binds it to a review that happened. A ``bot:<name>``
    literal would have put that assertion on the merge gate's critical path,
    which is the fabricated-receipt threat the #428 state guard exists to catch.
    What this function reads instead is not a claim by the agent — it is
    :func:`bot_review_coverage` over review objects GitHub attributes to the
    bot's own identity.

    **It fails closed by construction, and that is a property inherited rather
    than added.** :func:`bot_review_coverage` already under-reports on purpose
    (a bot whose reviews carry no usable commit SHA is indistinguishable there
    from one that never reviewed). Under-reporting is the correct bias for a
    gate: anything the coverage read cannot see yields no entry here, hence no
    evidence, hence the receipt requirement stands exactly as it did before.
    Issue #44 — a clean review that arrives only as a comment, invisible to
    coverage — is therefore a case this route simply does not cover, never one
    it gets wrong. **Do not "improve" the coverage read by trading that bias for
    completeness**; the gate now rests on it.

    Requires ALL of:

    - a real ``head`` to bind to;
    - ``signal == "ok"`` — the bot-state read actually ran. On ``"unavailable"``
      both of :func:`summarize_review_bots`'s guards are already off and the
      read FAILED, so it must not also open the gate; on ``"skipped"`` no bots
      are configured and this route does not exist.
    - a coverage entry with ``covers_head`` true **and** a ``sha`` equal to
      ``head``. The redundancy is deliberate: ``covers_head`` is derived, and a
      merge gate should re-check the identity it is about to authorize against
      rather than trust a boolean computed elsewhere in the call.
    - a ``state`` in :data:`_EVIDENTIAL_REVIEW_STATES`. **That a review exists
      at the head is not the same as a standing verdict** — a dismissed, still-
      pending, or changes-requesting review is all three of "attributed to the
      bot", "bound to this head", and "not evidence". The gate accepted all
      three before this check existed.

    Deliberately does NOT re-check what already blocks on its own path, because
    a second copy of a rule is a second thing to go stale: a *pending* bot
    contributes its own ``merge_blockers`` entry (issue #19's grace window) and
    an unacknowledged outage comment blocks ``converged``.
    :func:`decide_mergeable` requires ``converged`` and an empty blocker list
    regardless of this function, so THIS route can only ever *add* evidence to a
    PR that is otherwise already clear.

    **Read that last sentence as scoped to this route, because the receipt route
    beside it does not share the property.** A bot's live ``CHANGES_REQUESTED``
    on the current head does not stop :func:`record_review` — its only refusal
    reads the bot's *check-row pending state*, never the submitted verdict — and
    the aggregate ``review_decision`` blocker does not catch it either on the
    ``gh`` transport, which is the only transport ``--record-review`` runs on.
    A receipt could therefore authorize a merge over a standing objection, which
    is why ``CHANGES_REQUESTED`` is excluded from
    :data:`_EVIDENTIAL_REVIEW_STATES` rather than delegated to that blocker:
    delegating would have inherited the hole.

    **That receipt hole was #485 and is now closed** —
    :func:`objecting_bot_coverage` raises its own ``merge_blockers`` entry from
    the same coverage read, which no receipt satisfies. The exclusion above still
    stands on its own reasoning and is NOT now redundant: it keeps this route
    from *supplying* evidence, while that blocker independently *refuses* the
    merge. Two mechanisms, because the two questions differ — and because a guard
    that delegates is a guard that fails when its delegate's conditions change.

    Returns the sorted distinct bot names whose coverage qualifies — a list
    rather than a bool so the report can name them and a reader can tell which
    reviewer the merge actually rests on.
    """
    if not head:
        return []
    if review_bots.get("signal") != "ok":
        return []
    qualifying = {
        entry.get("bot")
        for entry in review_bots.get("coverage") or []
        if entry.get("covers_head") is True
        and entry.get("sha") == head
        and entry.get("state") in _EVIDENTIAL_REVIEW_STATES
        and entry.get("bot")
    }
    return sorted(qualifying)


# Review states that are a STANDING OBJECTION at the head — the mirror of
# :data:`_EVIDENTIAL_REVIEW_STATES`, and deliberately not its complement.
#
# Note the two sets are built the opposite way round, which looks like an
# inconsistency and is the point: they fail closed in opposite directions, so
# they must. Evidence is an ALLOWLIST because an unrecognized state must not
# open the gate. An objection is an explicit SET because an unrecognized state
# must not *close* it — "everything that is not evidence" would raise a blocker
# for `PENDING` (a draft the bot has not submitted) and for `""` (a `gh` too old
# to emit the field, or a REST payload shaped differently), neither of which is
# anyone objecting. That blocker would never clear without a push, which is the
# wedge this engine's design refuses. Do not "harmonize" these two definitions.
#
# KNOWN BOUND, in the fail-open direction: a future GitHub objection state this
# set has never heard of raises no blocker. It would also not be evidence, so
# the *coverage* route still refuses it — but a receipt would carry the merge,
# which is exactly the #485 shape one state over. `CHANGES_REQUESTED` is the
# only objection state GitHub defines today; add to this set rather than
# inverting it.
_OBJECTING_REVIEW_STATES = frozenset({"CHANGES_REQUESTED"})

# Review states that CARRY A VERDICT, and so may displace a bot's earlier one
# when it reviews the same head again (#494). An ALLOWLIST, deliberately, rather
# than a denylist of `COMMENTED`/`PENDING`: an unrecognized state — a new one
# GitHub adds, a typo'd fixture, a transport that spells them differently — must
# not be able to clear a standing objection. A denylist grants displacement to
# everything it does not name, which is the fail-open direction on this gate.
#
# Same membership as the allowlist inside `_rest_review_decision`, and same
# reasoning; kept as its own name because the two are read by different gates
# and coupling them would make one's tightening silently retune the other.
_VERDICT_REVIEW_STATES = frozenset({"APPROVED", "CHANGES_REQUESTED", "DISMISSED"})


def bot_head_objections(
    reviews: list[dict],
    head: str | None,
    *,
    bots: tuple[str, ...] | None = None,
) -> list[dict]:
    """Each configured bot's latest VERDICT, in the coverage entry shape (#494).

    The sibling of :func:`bot_review_coverage`, and the reason the objection read
    is no longer computed from it. Coverage reduces to one entry per bot,
    newest-wins **regardless of state**, because its question is which commit the
    bot last looked at. Asking the objection question of that answer meant a
    bot's own follow-up ``COMMENTED`` at the same head did not merely outrank its
    earlier ``CHANGES_REQUESTED`` — it removed it from the structure the blocker
    was computed from. Two blockers became zero with no commit pushed, no head
    change, and nothing dismissed on the forge; and because ``COMMENTED`` is in
    :data:`_EVIDENTIAL_REVIEW_STATES`, that same review then *supplied* the
    independent-review evidence.

    That was a regression against the pre-#484 world on one path: merging over a
    standing objection previously took a deliberate ``--record-review``, and had
    become something an ordinary follow-up review did by itself, with no human
    act and no forge audit trail — while #488's stated contract offers only two
    routes out, fixing the finding or a maintainer dismissal, both of which leave
    one.

    Only :data:`_VERDICT_REVIEW_STATES` participate, so a non-verdict submission
    leaves an earlier verdict standing. Every other release valve is unchanged
    and still reachable, which is what keeps this from wedging: an ``APPROVED``
    at the same head displaces the objection, a ``DISMISSED`` does (dismissal
    rewrites the review's own state), and pushing a fix moves the head so the
    objection covers an older commit.
    """
    return _reduce_latest_bot_reviews(
        reviews, head, bots, states=_VERDICT_REVIEW_STATES
    )


def objecting_bot_coverage(review_bots: dict, head: str | None) -> list[str]:
    """Configured bots with a standing objection to ``head`` itself (issue #485).

    The gate's refusal side, and the reason it is a separate read from
    :func:`qualifying_bot_coverage` rather than one more excluded state there:
    that function decides whether a bot's review can *supply* the
    independent-review requirement, so everything it declines merely falls back
    to needing a receipt. A receipt is exactly what #485 showed does not
    dispose of an objection. A bot saying "changes requested" has to raise its
    own ``merge_blockers`` entry, which no receipt can satisfy, or it is not a
    refusal at all.

    **Why this lives at the gate and not in :func:`record_review`.** Refusing to
    *record* a receipt over a live objection closes only the ordering where the
    objection arrives first. The realistic sequence is the other one — the bot is
    rate-limited, a fallback panel runs, a receipt is taken, and the bot then
    recovers and objects at that same head. The receipt is already written and
    still binds, so a record-time refusal never runs. Evaluating the objection at
    merge time catches both orderings, and covers the no-receipt case besides.

    **It cannot wedge, and that is a property of the head binding rather than an
    escape hatch.** The blocker is bound to ``head``, so the ordinary remediation
    — push a fix — moves the head, leaves the objection covering an older commit,
    and clears it. A maintainer dismissing the review (``DISMISSED``) clears it
    too, and so does the reviewer's own ``APPROVED`` at this same head — that
    last one being a reviewer withdrawing its objection rather than an author
    routing around it. **All three**, which is why this ships with no override
    flag: each leaves the forge showing why the objection no longer applies — a
    superseding commit, a dismissal, or a later approving verdict — and
    ``--allow-pending-bot-review`` exists because a *silent* bot can genuinely
    never arrive, whereas an objection is a reviewer who has already spoken and
    can unsay it the same way.

    **Deliberately does NOT gate on** ``signal == "ok"``, where its sibling does.
    That asymmetry is the fail-closed direction on each side: ``signal``
    describes the CHECK read (:func:`fetch_check_details`), while the coverage
    this reads comes from the ``pr view`` review objects, which are present
    whether or not that read succeeded. Declining to raise a blocker because a
    *different* read failed is the fail-open. ``"skipped"`` needs no special case
    — with no bots configured :func:`bot_review_coverage` matches nothing and the
    coverage list is empty on its own.

    Returns the sorted distinct bot names, so the blocker can say who objected
    rather than leaving a reader to open the PR to find out.
    """
    if not head:
        return []
    objecting = {
        entry.get("bot")
        # `objections`, NOT `coverage` (#494). Coverage is newest-wins over every
        # state, so a bot's own later non-verdict review at this same head
        # deleted its objection from the list before this ever read it. Same
        # entry shape, so every clause below is unchanged — the fix is which
        # reduction the clauses are applied to.
        for entry in review_bots.get("objections") or []
        # `covers_head is True` AND `sha == head`: identity, not truthiness, and
        # the same deliberate redundancy `qualifying_bot_coverage` carries. A
        # gate should re-check the identity it is about to act on rather than
        # trust a boolean computed elsewhere in the call — and here the cost of a
        # derived `covers_head` going wrong is a blocker that outlives the commit
        # it objected to, i.e. the wedge.
        if entry.get("covers_head") is True
        and entry.get("sha") == head
        and entry.get("state") in _OBJECTING_REVIEW_STATES
        and entry.get("bot")
    }
    return sorted(objecting)


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

    ``settling`` is set when the PR head SHA moved, or the rollup is smaller than
    the largest seen for this head, so a poll can't false-settle on the *stale
    pre-push* rollup (an all-green old commit) before the new commit's CI even
    starts.

    **It is one poll wide, and that is deliberate here.** The baseline resets to
    the new commit's partial count, so the next poll compares that count against
    itself and settles (#39). Widening it would hold ``converged`` false while
    checks register, wedging the watch loop this predicate exists to keep
    runnable. The merge gate carries the wider guard instead — see
    ``rollup_settled`` in :func:`build_report`.
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
    non-open, blocked merge state, changes requested) and independent-review
    evidence bound to the *current* head.

    ``review_evidence`` here is the caller's already-resolved boolean, and it has
    **two** routes behind it (#350): a ``--record-review`` receipt, or a
    configured review bot's own review of that head
    (:func:`qualifying_bot_coverage`). This function does not care which — the
    resolution is :func:`build_report`'s, and the report says which route
    answered so a reader is never left to infer it.

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


def read_settle_since(state: dict, head: str | None) -> tuple[str | None, int | None]:
    """The persisted settle stamp and the check count it was taken at.

    Head-scoped and self-describing (``{"head": sha, "at": iso, "total": n}``)
    for the same reason :func:`read_pending_since` is: a push means the rollup is
    being rebuilt from nothing, so a clock from the previous head is DISCARDED
    rather than aged. Carrying it forward would let a long-settled prior head
    satisfy the gate for a commit pushed seconds ago — the exact substitution the
    guard exists to refuse.

    ``total`` rides along because the clock's meaning is "the rollup has been
    THIS size since then". Comparing against the *previous poll's* count rather
    than against ``max_total`` is what keeps the guard from wedging: ``max_total``
    is a one-way ratchet, so a check that permanently disappears leaves
    ``total < max_total`` true forever.

    ``(None, None)`` means "no baseline for this head", which the merge gate
    reads as not-settled. That is the whole of #190: absent must never be
    equivalent to satisfied.
    """
    stored = state.get("settle_since")
    if not isinstance(stored, dict) or not head or stored.get("head") != head:
        return None, None
    at = stored.get("at")
    total = stored.get("total")
    if not isinstance(at, str) or not at.strip():
        return None, None
    # A stamp with no usable count cannot say what it is a baseline FOR, so it
    # is not one. Fail closed rather than pairing a real timestamp with an
    # unknown size — that would settle on the next poll whatever the rollup did.
    if isinstance(total, bool) or not isinstance(total, int):
        return None, None
    return at, total


def write_pending_since(state: dict, head: str | None, bots: dict) -> dict:
    """Set the head-scoped grace clock on ``state`` (dropping an empty one)."""
    if bots and head:
        state["bot_pending_since"] = {"head": head, "bots": bots}
    else:
        state.pop("bot_pending_since", None)
    return state


def load_state(pr: int) -> dict:
    """Full per-PR watch state (missing/corrupt → {}).

    **Returning {} here is a fail-open route into the merge gate, not merely a
    lost cache** — it drops ``head``/``max_total`` and, before #190, left nothing
    to distinguish "never observed this head settling" from "this head has
    settled". ``settle_since`` is what closes that: absent means not-established,
    and :func:`read_settle_since` never invents one.

    Keys: ``seen`` (acked comment keys), ``head`` / ``max_total`` (false-settle
    guard, see :func:`build_report`), ``settle_since`` (the head-scoped settle
    baseline the merge gate reads, see :func:`read_settle_since`),
    ``bot_pending_since`` (the head-scoped
    fallback grace clock for a review bot whose check carries no usable
    timestamp, see :func:`read_pending_since`), ``pending_seen`` — the ``all_seen_keys``
    of the most recently *reported* plain poll, present only between a poll and
    the ``--mark-seen`` that consumes it (see :func:`mark_seen`) — and
    ``review_receipt`` — independent-review evidence **stamped with the head it
    was taken at**, written by :func:`record_review` and carried forward by
    :func:`persist_poll`. Its presence is not evidence for the current head:
    :func:`build_report` decides that at read time by comparing
    ``receipt["head"]`` against the polled head, and a push invalidates it.
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
    # Truncating write, deliberately: #174 carries the decision, the measurements
    # and the objections. Not restated here — every review round so far has found
    # a defect in some version of the argument kept at this site.
    #
    # Two local facts, each established by execution, because a reader who has
    # only one of them will reach the wrong conclusion.
    #
    # Why not convert: nothing enforces this file's properties between runs — the
    # `mkdir` below tolerates a pre-existing STATE_DIR whose mode it never checks,
    # and `_seen_path(pr)` outlives the run that made it — so rename-publishing
    # could refuse (hardlink, non-regular, un-carryable ownership, non-writable
    # parent). A poll that cannot record state at all is the worse failure.
    #
    # Why not relax: losing this file is NOT safe, and two earlier drafts of this
    # comment claimed it was. `load_state` returns {} for a missing, empty or
    # corrupt file, dropping `head`/`max_total` and disabling the false-settle
    # guard; a receipt recorded afterwards makes `mergeable` true while checks are
    # still registering and green, and `seen` is gone so every acknowledgement
    # resurfaces. That is #190 — a merge-gate defect this call can neither complete
    # alone (the fail-open needs the later `--record-review`) nor prevent (a fresh
    # clone reaches `load_state() == {}` with no failed write anywhere).
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
    lenses: str | None = None,
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
    cannot see. It is recorded on the receipt as ``override``, as is a failed
    check read (``bot_signal``; but not "no bots configured" — nothing was
    unreadable in that case) and any bot whose last review predates this head
    (``bots_behind_head``). All three say what the receipt does NOT stand for.

    ``lenses`` names the review lenses that actually ran (see
    ``docs/agentic-dev-kit/fallback-review-panel.md``). Recorded verbatim so a
    one-lens pass is distinguishable from a panel in the audit trail: the
    doctrine holds that a single-lens verdict is not a green light, and without
    this a degraded `fallback:` receipt reads exactly like a full one.
    """
    require_gh_backend("--record-review")
    source = source.strip()
    if not source:
        raise ValueError("review source must not be empty")
    expected_head = expected_head.strip()
    if not expected_head:
        raise ValueError("expected reviewed head must not be empty")
    snapshot = fetch_review_snapshot(pr)
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
        details = fetch_check_details(pr, head_sha=current_head)
        bot_status = summarize_review_bots(
            details.rows,
            [],
            now=now,
            pending_since=read_pending_since(state, current_head),
            signal=details.signal,
            # No `reviews=`/`head=`: coverage is computed directly above, for
            # every path including the override. Passing them here too would
            # compute it twice from two different bot lists — identical today,
            # silently divergent the moment this function takes a `bots` arg.
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
    named_lenses = [part.strip() for part in (lenses or "").split(",") if part.strip()]
    if named_lenses:
        receipt["lenses"] = named_lenses
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
        # receipt does NOT stand for. The poll render warns that a receipt taken
        # now would not stand for the bot's review of this design — and that was
        # printing everywhere except where a receipt is actually taken.
        receipt["bots_behind_head"] = {e["bot"]: e["sha"] for e in behind}
    state["review_receipt"] = receipt
    save_state(pr, state)
    return {"pr": pr, "recorded_review": True, "review_receipt": receipt}


# ----------------------------------------------------------------------- main


# A lens NAME, not a sentence: letters, digits, and the usual separators.
# `--lenses` splits on `,`, which is also ordinary punctuation — so
# "adversarial, focused on the new merge gate" arrived as two entries and
# rendered as a two-lens panel, suppressing the one-lens warning that is the
# whole remaining value of the field. That is an HONEST input misreported, not
# only a forgery. Counting only entries that look like names fixes both without
# a roster and without a gate: prose is still recorded verbatim, it just does
# not count toward "how many lenses ran".
_LENS_NAME_RE = re.compile(r"^[\w.+-]{1,40}$")


def _countable_lenses(names: list[str]) -> set[str]:
    """Case-folded lens names from ``names``, ignoring prose."""
    return {n.casefold() for n in names if _LENS_NAME_RE.match(n)}


def _flat(text: object, n: int = 120) -> str:
    """One line, bounded. For any receipt/config value entering a render.

    Both `source` and the lens names are free text chosen by whoever ran
    `--record-review`. Interpolated raw, a single newline splits the coverage
    line in two and leaves the first half reading as a completed panel:

        review evidence: fallback:panel — 2 lenses claimed (adversarial,
        correctness) (recorded) — ⚠ ONE lens claimed …

    `_excerpt` already established this convention for comment bodies; the
    receipt fields skipped it.
    """
    # Strip C0/C1 control characters BEFORE collapsing whitespace. `split()`
    # normalizes whitespace but `\x1b` is not whitespace, so ANSI cursor
    # control survived — and that is strictly worse than the newline this
    # function was written for: `\x1b[1A\x1b[2K` *erases* lines that exist
    # rather than appending ones that don't, so a receipt could delete the
    # merge blockers printed above it.
    cleaned = "".join(" " if unicodedata.category(c) == "Cc" else c for c in str(text))
    flat = " ".join(cleaned.split())
    return flat if len(flat) <= n else flat[: n - 1] + "…"


def _excerpt(body: str, n: int = 140) -> str:
    # Same control-character strip as :func:`_flat`, and for a stronger reason:
    # this renders a COMMENT BODY, which on a public repo any account can write.
    # It also renders last, so cursor-up sequences here walk over every merge
    # blocker above them. Pre-existing on main; fixed here because `_flat`'s
    # docstring cites this function as the convention it copies, and copying a
    # defect forward is how the convention stops being one.
    flat = " ".join(
        "".join(
            " " if unicodedata.category(c) == "Cc" else c for c in (body or "")
        ).split()
    )
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
    prior_settle_since: str | None = None,  # already head-scoped by the caller
    prior_settle_total: int | None = None,  # the count that stamp was taken at
    # The backend that PERFORMED THE READS in `view`/`inline`. Threaded rather
    # than re-resolved so the REST bound cannot drift from the data it is bounding
    # — see :func:`rest_cannot_authorize_merge`. None means "resolve it", which is
    # right for a caller that did no I/O of its own (tests, `--mark-seen`).
    backend: str | None = None,
) -> dict:
    """Assemble the JSON-serializable watch report for one PR snapshot.

    Returns a dict with:

    - ``pr`` / ``url`` / ``state`` / ``is_draft`` / ``base`` / ``merge_state`` /
      ``review_decision`` — PR identity + merge/review state.
    - ``head`` — the PR head SHA (``headRefOid``); ``head_changed`` — true when it
      moved since ``prior_head``; ``max_total`` — the largest check count seen for
      this head (persisted across runs); ``settling`` — true when the head moved
      or the rollup shrank *on this poll* (forces ``converged`` false). See
      :func:`decide_converged`.

      ``settling`` used to be documented here as "true while a just-pushed
      commit's checks are still registering". It is not, and #39 is the issue
      that measured it: the baseline resets to the new commit's partial count, so
      it is true only on the poll that OBSERVES the change. The property that
      sentence promised is now carried by ``rollup_settled`` below, on the merge
      gate.
    - ``settle_since`` / ``settle_age_minutes`` / ``rollup_settled`` — the settle
      baseline (#190/#39): how long the rollup has gone without changing size
      for this head, and
      whether that is long enough for the merge gate to believe it is complete.
      ``settle_age_minutes`` is ``None`` when there is no usable baseline, which
      is NOT the same as zero and never reads as settled.
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
    - ``review_evidence`` — whether current-head independent-review evidence
      exists, by either route (#350): a persisted receipt bound to this exact
      head SHA, or a configured bot's own review of it. ``route`` names which
      (``receipt`` / ``bot-coverage`` / null) and ``bots`` names the covering
      bots; the receipt-describing keys (``source``, ``lenses``, ``override``,
      ``bot_signal``) stay receipt-only and are empty on the coverage route.
    - ``review_bots`` — :func:`summarize_review_bots`: each configured review
      bot resolved to *unavailable* (an outage announced on either the comment
      or the check-description surface — an action signal, never a blocker) or
      *pending* (a verdict still coming, which blocks the merge gate until it
      ages past the grace window). Also carries ``coverage`` (which commit each
      bot's last review saw), ``objections`` (the same reduction over verdict
      states only, so a non-verdict review cannot displace one — #494), and
      ``signal`` (whether that state could be read at all). Advisory to
      ``converged`` by construction — but **no longer non-gating**: since #350
      ``coverage`` and ``signal`` are what :func:`qualifying_bot_coverage` reads
      to satisfy the merge gate's independent-review requirement without a
      receipt, and ``objections`` is what :func:`objecting_bot_coverage` reads to
      refuse it.
    - ``merge_blockers`` — deterministic reasons the PR is not currently safe to
      merge (draft, blocked/unknown merge state, requested changes, non-open PR,
      missing current-head review evidence, a configured review bot whose own
      verdict has not landed yet, or a configured review bot whose latest
      *verdict* at the current head is ``CHANGES_REQUESTED`` — latest verdict
      rather than latest review, which is #494's correction — see
      :func:`objecting_bot_coverage`, and note that no receipt satisfies that
      one).
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
    now_dt = now or datetime.now(timezone.utc)
    review_bots = summarize_review_bots(
        details.rows,
        comments,
        now=now_dt,
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

    # ------------------------------------------------ the settle baseline (#190/#39)
    #
    # `settling` above is a SINGLE-POLL question — did the head move, or did the
    # rollup shrink, between the last poll and this one. Both merge-gate holes it
    # leaves open are about what one poll cannot see, and they are the same hole
    # from two directions:
    #
    #   #190  With no state file, `prior_head` is None, so `head_changed` is
    #         False and `max_total` collapses to `checks["total"]` — making
    #         `checks["total"] < max_total` unsatisfiable. The guard is not
    #         merely absent, it is unfalsifiable. A FRESH CLONE reaches this with
    #         no failed write anywhere, so it is the first run, not an error path.
    #   #39   On a head change the baseline resets to the new commit's PARTIAL
    #         count, so the very next poll compares that count against itself and
    #         settles — while most of the commit's checks have not registered.
    #
    # No count can close either, because the rollup never says how many checks
    # are still coming: 2 of 5 and 2 of 2 are the same number. The only fact that
    # separates them is that the rollup stopped MOVING and stayed stopped, and
    # that needs a clock plus a persisted baseline.
    #
    # ONE KNOWN COST, decided rather than inherited. A `require_ci: false` repo's
    # rollup is permanently empty, so nothing can be mid-registration there and
    # this guard buys it nothing — but it still charges it one extra poll plus
    # the grace. Short-circuiting on an empty rollup was considered and REFUSED:
    # a first poll's rollup is also empty when the checks merely have not
    # registered yet, so the short-circuit is #39 again for any adopter who set
    # the flag while still having intermittent CI. `safety-critical-changes.md`
    # rule 3 names that trade — a fail-CLOSED limitation swapped for a fail-OPEN
    # mechanism — so the latency stands and is documented instead.
    # `test_a_ci_less_repo_still_waits_for_the_settle_baseline` pins it.
    #
    # NOT A SECURITY BOUNDARY, and it should not be read as one. The baseline
    # lives in the per-PR state file, so anyone who can run this engine can
    # backdate the stamp and satisfy the gate — the same standing of
    # `bot_pending_since`, whose forgeability #95 records. This guards a race
    # (a rollup read mid-registration), not an adversary.
    #
    # It gates `merge_blockers` and NOT `settling`, deliberately, because those
    # feed different predicates. `converged` answers "is there more for me to
    # fix?" and must stay answerable — blocking it would wedge the watch loop,
    # which is the one thing the converged/mergeable split exists to prevent.
    # Both issues' own suggested directions land here too (#190: "decide_mergeable
    # refusing a receipt when no max_total was ever recorded"; #39: "time-based
    # from the observed head change"). Additive to the merge gate is also what
    # keeps `done` — its alias — tightening rather than loosening.
    # A stamp carries forward only while the rollup is the SAME SIZE it was when
    # the stamp was taken. Any movement restarts it — a check appearing, a check
    # disappearing, a push.
    #
    # Anchored on the PREVIOUS POLL'S count, not on `max_total`, and the two
    # earlier versions of this line are why. Resetting only on growth
    # (`head_changed or rollup_grew`) let a stamp survive a dip and credited the
    # span either side of it: a rollup that dropped and returned to its old count
    # settled having been stable for seconds. Resetting on `settling or
    # rollup_grew` closed that and opened something worse — `max_total` is a
    # one-way ratchet, so a check that disappears for good leaves
    # `total < max_total` true on every future poll, the clock re-stamps forever
    # and the gate never opens for that head. Measured: stable at 4 checks for
    # five hours, never settled, with `settle_grace_minutes: 0` no escape because
    # the age stays None. A wedge, which is the one thing this engine's design
    # refuses.
    #
    # Comparing to the previous count has neither failure: a dip is movement, and
    # so is the recovery; a rollup that settles at a permanently lower count is
    # unchanged from the poll after the drop onward, so it ages normally.
    #
    # KNOWN BOUND: this is a count, so a same-size SWAP — one check vanishing as
    # another appears between two polls — reads as no movement. That is the same
    # bound the whole mechanism has always had (`max_total`, `settling` and #39
    # are all counts); closing it needs check identities, which is a bigger change
    # than this guard.
    rollup_moved = checks["total"] != prior_settle_total
    carried_stamp = (
        None if (head_changed or rollup_moved) else (prior_settle_since or None)
    )
    settle_age_minutes = _age_minutes(carried_stamp, now_dt)
    # `_age_minutes` returns None for a stamp it cannot use — unparseable, the
    # zero time, or meaningfully in the future (a state file copied between
    # machines, a clock NTP-corrected backwards). Unknown is not settled; and
    # re-stamping rather than keeping it is what stops a future stamp pinning the
    # gate closed until real time catches up, the failure its own docstring warns
    # about.
    settle_since = (
        carried_stamp
        if settle_age_minutes is not None
        else now_dt.isoformat().replace("+00:00", "Z")
    )
    rollup_settled = (
        settle_age_minutes is not None and settle_age_minutes >= _SETTLE_GRACE_MINUTES
    )

    pr_state = (view.get("state") or "UNKNOWN").upper()
    base = view.get("baseRefName")
    merge_state = (view.get("mergeStateStatus") or "UNKNOWN").upper()
    review_decision = (view.get("reviewDecision") or "").upper()
    receipt_head = (
        review_receipt.get("head") if isinstance(review_receipt, dict) else None
    )
    receipt_valid = bool(head) and receipt_head == head
    # The second route to the same requirement (#350, direction 1). See
    # `qualifying_bot_coverage` for why reading the bot's own review objects is
    # safe where a fourth self-reported receipt literal would not have been, and
    # why every case it cannot see degrades to the receipt requirement rather
    # than opening the gate.
    coverage_bots = qualifying_bot_coverage(review_bots, head)
    # The refusal side of the same read (#485). Resolved here beside the evidence
    # routes because it OUTRANKS both: a receipt is self-reported, and a standing
    # objection from the configured reviewer is not something the agent seeking
    # the merge gets to answer for itself.
    objecting_bots = objecting_bot_coverage(review_bots, head)
    review_evidence = {
        "valid": receipt_valid or bool(coverage_bots),
        # WHICH route satisfied the gate. Without this a coverage-backed merge
        # and a receipt-backed one are indistinguishable in the audit trail,
        # which is the distinction #350 is about — so it is reported, not
        # inferred from `source` being null. `receipt` wins the label when both
        # hold: it is the claim someone actively made, and `bots` below still
        # names the coverage, so nothing is hidden by the precedence.
        "route": (
            "receipt" if receipt_valid else ("bot-coverage" if coverage_bots else None)
        ),
        # Populated whenever coverage qualifies, INCLUDING when a receipt also
        # exists — a reader deciding whether to trust a merge wants both facts.
        "bots": coverage_bots,
        "source": (
            review_receipt.get("source")
            if isinstance(review_receipt, dict) and receipt_head == head
            else None
        ),
        "head": receipt_head,
        # Carried into the report so the poll render can state what the receipt
        # stands for. Previously the one-lens warning printed exactly once — on
        # the stdout of the `--record-review` call the agent itself chose to
        # make — and never again at the moment a merge is authorized.
        # `isinstance(..., list)` first: a bare string is iterable, so a
        # hand-edited `"lenses": "adversarial"` would otherwise be read as
        # eleven single-character lenses and render as ample coverage.
        "lenses": (
            [
                lens
                for lens in review_receipt["lenses"]
                if isinstance(lens, str) and lens.strip()
            ]
            if isinstance(review_receipt, dict)
            and receipt_head == head
            and isinstance(review_receipt.get("lenses"), list)
            else []
        ),
        "override": (
            review_receipt.get("override")
            if isinstance(review_receipt, dict) and receipt_head == head
            else None
        ),
        "bot_signal": (
            review_receipt.get("bot_signal")
            if isinstance(review_receipt, dict) and receipt_head == head
            else None
        ),
    }
    merge_blockers: list[str] = []
    rest_blocker = rest_cannot_authorize_merge(backend)
    if rest_blocker:
        merge_blockers.append(rest_blocker)
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
    if objecting_bots:
        # Worded to name the bot, and kept DISTINCT from the aggregate blocker
        # above rather than folded into it. On the REST transport both fire for
        # the same objection (`_rest_review_decision` aggregates every reviewer
        # with no required-reviewer notion), and that duplication is worth its
        # line: two mechanisms agreeing reads differently from one speaking. On
        # the `gh` transport — the only one `--record-review` runs on, which is
        # what made #485 reachable — the aggregate is empty and this is the sole
        # blocker.
        merge_blockers.append(
            "configured review bot requested changes on current head: "
            + ", ".join(objecting_bots)
        )
    if not review_evidence["valid"]:
        merge_blockers.append("independent review evidence is missing for current head")
    if not rollup_settled:
        # One prefix, two wordings, because a reader who cannot tell them apart
        # cannot act: "no baseline" means no clock is running, "stable Nm of Mm"
        # means one is. NEITHER is a promise about when. Both end when the rollup
        # has gone the grace without changing size, and "no baseline" RECURS on every poll
        # that restarts the clock rather than appearing once — this comment said
        # it "clears on the next poll" for four commits, which is false in
        # exactly the case the guard exists for.
        merge_blockers.append(
            "check rollup has not settled for current head "
            + (
                f"(stable {settle_age_minutes:.1f}m of {_SETTLE_GRACE_MINUTES:g}m)"
                if settle_age_minutes is not None
                else "(no settle baseline recorded)"
            )
        )
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
        # The settle baseline in force for THIS head, and what it is worth.
        # `settle_since` is written back by `persist_poll`, so it must be the
        # stamp the next poll should carry — the carried one while the rollup
        # is the same size it was, a fresh one the moment it changes either way
        # or the stamp goes unusable.
        "settle_since": settle_since,
        "settle_age_minutes": settle_age_minutes,
        "rollup_settled": rollup_settled,
        "checks": checks,
        # Reported, and gating nothing. It does not need to gate: REST cannot
        # authorize a merge at all, so the only thing truncation can still
        # mislead is `converged` — and blocking THAT would wedge the watch loop,
        # which is the one thing these two predicates exist to keep separate.
        # An earlier design made it a merge blocker and that was worse than
        # useless: a persistent pagination anomaly closed the gate for a PR
        # forever, with no ageing-out and no override, unlike every sibling
        # environment-caused blocker. Empty on the `gh` backend, which paginates
        # through `gh` itself.
        "truncated_reads": list(_truncated_reads),
        # Which transport produced this report. Needed by `persist_poll` so the
        # false-settle baseline is never compared across two backends that count
        # checks differently (see :func:`comparable_max_total`), and useful in the
        # JSON for anyone debugging why a gh-less poll behaves differently.
        "backend": backend if backend is not None else _active_backend_name(),
        "new_comments": [
            {
                "kind": c["kind"],
                "author": c["author"],
                "path": c["path"],
                "line": c["line"],
                "excerpt": _excerpt(c["body"]),
                "review_unavailable_reason": c.get("review_unavailable_reason"),
                "untrusted_review_unavailable_candidate": c.get(
                    "untrusted_review_unavailable_candidate"
                ),
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
    # Truncation, on the surface a human or agent actually reads. It gates
    # nothing — REST cannot authorize a merge, and blocking `converged` would
    # wedge the loop — so this line is the entire mechanism. Deduplicated because
    # one poll legitimately reads the check-runs URL twice.
    for truncated in dict.fromkeys(report.get("truncated_reads") or []):
        lines.append(
            f"  ⚠ a paginated read was TRUNCATED at the page ceiling ({truncated}) "
            "— this poll did NOT see every check/comment, so `converged` may be "
            "premature"
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
    # `.get` here, direct indexing below: an entry missing `blocking` falls out
    # of `reviewing` and the warning FIRES, which is the safe direction.
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
    # #44, reported so the reader is not left inferring it from two empty lists.
    # Fires only where it is informative: the bot announced a completed review of
    # THIS head in a comment, and its review objects do not cover this head — the
    # state where `coverage: []` and `unavailable: []` together look exactly like
    # "nobody reviewed" and actually mean "reviewed, on a surface the gate cannot
    # read". Says what to do, because the remedy is not guessable from the fact.
    covered = {e["bot"] for e in bots.get("coverage") or [] if e.get("covers_head")}
    for entry in bots.get("comment_verdicts") or []:
        if entry["bot"] in covered:
            continue
        lines.append(
            f"  ⓘ review reported: {entry['bot']} announced a completed review of "
            f"{entry['sha'][:7]} in a COMMENT, creating no review object — so the "
            "merge gate cannot see it and this is not evidence. If that verdict is "
            "what you are merging on, record it: --record-review "
            f"\"{entry['bot']}:comment-verdict\" --head {entry['sha']}"
        )
    for entry in bots.get("unavailable") or []:
        # `.get`, not indexing: only the check surface carries the #95 trust
        # fields, and a comment-surface entry legitimately has neither. Indexing
        # would KeyError on every rate-limit comment.
        if entry["surface"] == "check" and not entry.get("trusted", True):
            identity = entry.get("identity") or "unattributable"
            lines.append(
                f"  ⚠ review unavailable [{entry['surface']}] {entry['where']}: "
                f"{entry['reason']} — but its creator is {identity}, not "
                f"{entry['bot']}, so it does NOT cancel a pending review (#95). "
                "Run the fallback review panel "
                "(docs/agentic-dev-kit/fallback-review-panel.md); if this is the "
                "real reviewer under an identity the config does not know, add it "
                "to review.bot_app_slugs"
            )
            continue
        lines.append(
            f"  ⚠ review unavailable [{entry['surface']}] {entry['where']}: "
            f"{entry['reason']} — run the fallback review panel (docs/agentic-dev-kit/fallback-review-panel.md)"
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
                "treated as not coming; run the fallback review panel (docs/agentic-dev-kit/fallback-review-panel.md)"
            )
    # What the current-head receipt actually stands for. The gate cannot judge
    # this — `source` is free text an agent chooses — so the honest move is to
    # SHOW it at the moment a merge is considered, rather than to pattern-match
    # a label and hope. A relabelled one-lens receipt now reads as one lens
    # regardless of what it is called.
    evidence = report.get("review_evidence") or {}
    if evidence.get("valid") and evidence.get("route") == "bot-coverage":
        # The one kind of review evidence this engine did NOT take on trust: it
        # comes from review objects the forge attributes to the bot's own
        # identity, not from a label an agent typed. Rendered on its own branch
        # because every caveat in the receipt branch below — lens counts, an
        # override, an unreadable bot state — is a property of a RECEIPT. Run
        # through that branch, a real bot review would print "no lenses
        # recorded", reading as a deficiency rather than as different (and
        # harder to forge) evidence.
        who = ", ".join(_flat(bot) for bot in evidence.get("bots") or [])
        lines.append(
            f"  review evidence: the configured review bot reviewed this head ({who})"
            " — no receipt needed"
        )
    elif evidence.get("valid"):
        # SELF-REPORTED, and labelled as such. Whoever ran `--record-review`
        # wrote both the source and the lens names in one invocation, with
        # nothing binding either to a review that happened — so this engine
        # cannot verify coverage, and four rounds of trying to (matching the
        # source, then the lens names, then a configured roster) produced a
        # check defeated by one extra character while the render affirmed the
        # forgery. `safety-critical-changes.md` rule 1: treat "we tightened the
        # matcher" as a stopgap, not a fix. So: report the claim, name it a
        # claim, and let a reader judge it. Verifying it needs each lens to
        # record its own receipt from its own context — see issue #32.
        named = [_flat(lens, 40) for lens in evidence.get("lenses") or []]
        distinct = len(_countable_lenses(named))
        source = _flat(evidence.get("source"))
        if distinct >= 2:
            detail = f"{distinct} lenses claimed ({', '.join(named)})"
        elif named:
            detail = f"⚠ ONE lens claimed ({named[0]}) — not a dual-lens pass"
        else:
            detail = "no lenses recorded"
        lines.append(f"  review evidence: {source} — {detail}")
        # Both routes hold. `route` says `receipt` because that is the claim
        # someone actively made, but the coverage is the sturdier of the two and
        # a reader weighing a one-lens receipt deserves to know the bot also saw
        # this exact head.
        if evidence.get("bots"):
            lines.append(
                "    + the configured review bot also reviewed this head "
                f"({', '.join(_flat(bot) for bot in evidence['bots'])})"
            )
        # The same argument that moved `lenses` to the poll render applies to
        # its siblings: a caveat printed only on the stdout of the
        # `--record-review` call the agent itself made is not visible at the
        # moment a merge is considered.
        if evidence.get("override"):
            lines.append(
                f"    ⚠ recorded over an active override ({_flat(evidence['override'])})"
            )
        if evidence.get("bot_signal"):
            lines.append(
                f"    ⚠ review-bot state was unreadable ({_flat(evidence['bot_signal'])}) "
                "when this receipt was taken"
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
                    f"{c['review_unavailable_reason']} — run the fallback review panel (docs/agentic-dev-kit/fallback-review-panel.md)"
                )
            elif c.get("untrusted_review_unavailable_candidate"):
                lines.append(
                    f"  • [untrusted reviewer-outage candidate] @{c['author']}{loc}: "
                    f"{c['untrusted_review_unavailable_candidate']} — add the exact login under "
                    "review.bot_author_aliases before treating it as reviewer evidence"
                )
            else:
                lines.append(f"  • [{c['kind']}] @{c['author']}{loc}: {c['excerpt']}")
    return "\n".join(lines)


def render_record_review(report: dict) -> str:
    receipt = report["review_receipt"]
    lines = [
        f"PR #{report['pr']} — recorded independent review from "
        f"{_flat(receipt['source'])} for head {_flat(receipt['head'], 60)}"
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
    # Type-guarded like the sibling receipt fields: the state file is plain
    # JSON on disk and anything that can run this engine can edit it, so a
    # non-list or a list of non-strings must not crash the render.
    raw_lenses = receipt.get("lenses")
    named = (
        [lens for lens in raw_lenses if isinstance(lens, str) and lens.strip()]
        if isinstance(raw_lenses, list)
        else []
    )
    named = [_flat(lens, 40) for lens in named]
    if len(_countable_lenses(named)) == 1:
        lines.append(
            f"  ⚠ one lens only ({named[0]}) — `safety-critical-changes.md` rule 2 "
            "holds that a single-lens verdict is not a green light"
        )
    elif named:
        lines.append(f"  lenses: {', '.join(named)}")
    behind_map = receipt.get("bots_behind_head")
    for bot, sha in (behind_map if isinstance(behind_map, dict) else {}).items():
        lines.append(
            f"  ⚠ {bot}'s last review was of {_flat(sha, 12)}, not this head — this receipt "
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
      :func:`build_report`), plus ``max_total_backend`` so the guard is not
      compared across two transports that count checks differently.
    - ``pending_seen`` is THIS poll's ``all_seen_keys`` — the only thing a
      subsequent ``--mark-seen`` may promote into ``seen``. It overwrites any
      prior unconsumed pending set: the contract is "ack what the *last
      reported* poll showed."
    - ``seen`` itself only grows via :func:`mark_seen`, never here.
    - ``bot_pending_since`` is set here too, via :func:`write_pending_since`.
    - ``review_receipt`` is **carried forward**, not created: an existing dict is
      copied onto the new state so a poll never drops the evidence, and only
      :func:`record_review` ever originates one. It is not head-checked here —
      :func:`build_report` compares its stamped head against the polled head, so
      a receipt surviving a push is expected and is invalidated at read time.
    """
    new_state = {
        "seen": sorted(seen),
        "head": report["head"],
        "max_total": report["max_total"],
        # WHICH backend produced that count — recorded for diagnosis only.
        # NOTHING reads it, deliberately.
        #
        # There is a real cross-backend wedge here: the two transports read
        # different check surfaces (REST paginates `commits/{sha}/check-runs`
        # fully; `gh pr view --json statusCheckRollup` requests
        # `contexts(first: 100)` unpaginated), so on a PR with more contexts than
        # that, REST reports MORE than `gh`. One monotone `max_total` shared
        # across both then strands the lower-reporting backend in `settling` until
        # the next push.
        #
        # The obvious fix — reset the baseline when the backend changes — was
        # built here and REMOVED under `safety-critical-changes.md` rule 1,
        # because it fails open and does so on the DEFAULT backend. Resetting
        # `prior_max_total` to 0 makes `max_total = checks["total"]`, so
        # `checks["total"] < max_total` can never be true: the reset can only ever
        # REMOVE `settling`, never add it. Every state file written before the key
        # existed read as "not comparable", so upgrading turned the false-settle
        # guard off for every existing PR on `gh` and flipped `mergeable` from
        # false to TRUE. Measured, not theorised.
        #
        # So the wedge stays, as a fail-CLOSED known limitation (it refuses to
        # merge; a push clears it), rather than being traded for a fail-open on the
        # path everyone uses. Fixing it properly needs the two backends to count
        # the same checks, which is #94 territory.
        "max_total_backend": report.get("backend"),
        "pending_seen": report["all_seen_keys"],
        # The settle baseline (#190/#39), head-scoped like `bot_pending_since`.
        # It MUST ride every poll: a gate whose baseline is never persisted finds
        # no baseline on every poll, re-stamps it, and blocks forever — a wedge,
        # not a guard.
        "settle_since": {
            "head": report["head"],
            "at": report["settle_since"],
            # The count the stamp stands for. Without it the next poll cannot
            # tell whether the rollup moved, and a stamp that cannot say what
            # it is a baseline FOR is not one.
            "total": report["checks"]["total"],
        },
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
        "--no-persist",
        action="store_true",
        help=(
            "with a plain poll: report current PR state without rewriting the "
            "per-PR seen, pending, check-baseline, or bot-clock state; use for "
            "an act-time authorization check after the interactive watch loop"
        ),
    )
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
    parser.add_argument(
        "--lenses",
        metavar="NAMES",
        help=(
            "with --record-review: comma-separated review lenses that actually ran "
            "(e.g. adversarial,correctness). Recorded on the receipt so a one-lens "
            "pass is distinguishable from a panel — see "
            "docs/agentic-dev-kit/fallback-review-panel.md"
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
    if args.lenses and args.record_review is None:
        parser.error("--lenses is only valid with --record-review")
    if args.no_persist and (
        args.mark_seen
        or args.record_review is not None
        or args.assert_draft
        or args.assert_ready
    ):
        parser.error("--no-persist is only valid with a plain poll")

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
                lenses=args.lenses,
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

    # Resolved ONCE, before the first read, and threaded from here on. Not a
    # cache: it is re-resolved on the next invocation (a fresh process per poll),
    # which is what the #48 lesson actually requires. What it prevents is the
    # backend changing DURING one poll's multi-round-trip network phase and the
    # REST bound then being evaluated against the wrong transport.
    backend_name = _active_backend_name()
    try:
        view, inline = fetch_pr_view(pr)
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    # Deliberately outside the try: this call never raises and never blocks the
    # loop — see :func:`fetch_check_details`.
    check_details = fetch_check_details(pr, head_sha=view.get("headRefOid"))

    state = load_state(pr)
    seen = set(state.get("seen", []))
    settle_since, settle_total = read_settle_since(state, view.get("headRefOid"))
    report = build_report(
        view,
        inline,
        seen,
        prior_head=state.get("head"),
        prior_max_total=int(state.get("max_total") or 0),
        review_receipt=state.get("review_receipt"),
        check_details=check_details,
        prior_pending_since=read_pending_since(state, view.get("headRefOid")),
        prior_settle_since=settle_since,
        prior_settle_total=settle_total,
        backend=backend_name,
    )

    if not args.no_persist:
        persist_poll(pr, report, seen)

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
