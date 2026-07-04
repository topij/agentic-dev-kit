#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Poll a PR's CI checks + new review comments — the engine for the watch-and-fix loop.

`/pr-watch` (and the "PR follow-through" policy in your project's CLAUDE.md)
call this once per round: it asks `gh` for the PR's check rollup + every
comment surface (issue comments, review submissions, inline review comments),
filters out known auto-noise (a review bot's billing notice, its walkthrough /
pre-merge-check summaries), diffs against a per-PR seen-set so only *new
actionable* comments surface, and reports whether the PR is `done` (all checks
green AND nothing new to address).

The caller loops: run this -> if not done, fix the failures / address or reply
to the new comments -> `--mark-seen` -> wait -> run again. `done` flips true
once CI is green and every review-bot finding has been handled.

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
    0 — reported (regardless of done/not-done; check `done` in the output),
        or the draft-bit assertion held/was corrected successfully
    2 — usage error (no PR found, gh failure), or a draft-bit assertion that
        failed to correct (`ok: false`)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Nearest ancestor with a ``.git`` marker (so this keeps working when the kit
    is vendored under a nested dir, e.g. scripts/devkit/); falls back to the
    script's grandparent if no marker is found. Inlined — pr_watch stays stdlib-only."""
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start.parent.parent


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
# Honor the DEVKIT_STATE_ROOT sandbox (parallel dev sessions — see
# scripts/dev_session.sh) so a session's per-PR seen-set doesn't land in the
# main checkout's state/. Inlined rather than via a shared state-paths helper
# on purpose: pr_watch is deliberately stdlib-only (dependencies = []) for the
# hot watch-and-fix loop. Own-dir state => no read-cascade; an absolute env
# override else repo-root state/ (a relative override falls back rather than
# raising — never crash the loop).
_STATE_ENV = os.environ.get("DEVKIT_STATE_ROOT")
_STATE_ROOT = Path(_STATE_ENV) if _STATE_ENV and os.path.isabs(_STATE_ENV) else REPO_ROOT / "state"
STATE_DIR = _STATE_ROOT / "pr-watch"

# A comment is auto-noise (not a finding to act on) if its body matches any of
# these. Keep this list tight — over-filtering would hide a real review.
#
# These defaults target a GitHub + CodeRabbit + Bugbot review setup — edit this
# tuple to match whatever review-bot mix your own repo runs (a different org's
# bot(s) will emit different marker strings).
_NOISE_MARKERS = (
    "bugbot needs on-demand usage enabled",  # Cursor billing notice
    "<!-- this is an auto-generated comment: summarize by coderabbit",  # walkthrough
    "<!-- this is an auto-generated comment: review in progress",  # CodeRabbit "processing…" placeholder
    "<!-- walkthrough_start -->",
    "actionable comments posted: 0",  # CodeRabbit "nothing to change" review
    "review skipped",  # CodeRabbit draft-detected / skip notices
    "<!-- linear-linkback -->",  # a tracker's auto issue-mirror comment (not a finding)
)

# Status contexts that are advisory only — they must NEVER block "done". A
# review-bot status check can sit PENDING indefinitely after a trivial
# follow-up commit (it never auto-incrementally-reviews it), which would
# otherwise wedge the loop forever even though every real CI job is green. Its
# actual findings surface as review comments (which DO block via
# new_comments). Matched case-insensitively against the check name/context.
#
# Default targets CodeRabbit's status-check name — edit for your own
# review-bot mix.
_INFORMATIONAL_CHECK_NAMES = frozenset({"coderabbit"})


# --------------------------------------------------------------------------- gh


def _gh(args: list[str], *, timeout: int = 60) -> str:
    cmd = ["gh", *args]
    try:
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, check=False, cwd=str(REPO_ROOT), timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        # A hung gh call must not wedge the watch loop — surface it as an error
        # the caller already handles (main catches RuntimeError → exit 2).
        raise RuntimeError(f"gh {' '.join(args)} timed out after {timeout}s") from exc
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def _gh_json(args: list[str]):
    return json.loads(_gh(args))


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


def summarize_checks(rollup: list[dict]) -> dict:
    """Collapse a statusCheckRollup into counts + the list of failing checks.

    Informational status contexts (``_INFORMATIONAL_CHECK_NAMES``, e.g.
    CodeRabbit) are excluded from the blocking tally — they never count toward
    ``pending`` / ``failing`` and ``all_green`` requires at least one real
    (non-informational) check.
    """
    terminal_ok = {"SUCCESS", "NEUTRAL", "SKIPPED"}
    bad = {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
    success = pending = informational = 0
    failing: list[dict] = []
    for c in rollup:
        status = (c.get("conclusion") or c.get("state") or "").upper()
        name = c.get("name") or c.get("context") or "check"
        if name.strip().lower() in _INFORMATIONAL_CHECK_NAMES:
            informational += 1
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
        "failing": failing,
        "all_green": not failing and pending == 0 and blocking_total > 0,
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


def is_noise(body: str) -> bool:
    low = (body or "").lower()
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
        out.append(
            {
                "key": _comment_key("issue", raw),
                "content_key": _content_key("issue", _author(raw), body),
                "kind": "issue",
                "author": _author(raw),
                "path": None,
                "line": None,
                "body": body,
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
    return [c for c in comments if c["key"] not in seen and c["content_key"] not in seen and not is_noise(c["body"])]


def decide_done(checks: dict, new_items: list[dict], *, settling: bool = False) -> bool:
    """Done = checks all green AND nothing new to act on AND not mid-settle.

    ``settling`` is set right after a push (the PR head SHA moved, or the rollup
    is smaller than the largest seen for this head — new checks not yet
    registered), so a poll can't false-settle on the *stale pre-push* rollup
    (an all-green old commit) before the new commit's CI even starts.
    """
    return checks["all_green"] and not new_items and not settling


# ------------------------------------------------------------------ state I/O


def _seen_path(pr: int) -> Path:
    return STATE_DIR / f"{pr}.json"


def load_state(pr: int) -> dict:
    """Full per-PR watch state (missing/corrupt → {}).

    Keys: ``seen`` (acked comment keys), ``head`` / ``max_total`` (false-settle
    guard, see :func:`build_report`), and ``pending_seen`` — the ``all_seen_keys``
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
    _seen_path(pr).write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")


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
) -> dict:
    """Assemble the JSON-serializable watch report for one PR snapshot.

    Returns a dict with:

    - ``pr`` / ``url`` / ``is_draft`` / ``merge_state`` — PR identity + state.
    - ``head`` — the PR head SHA (``headRefOid``); ``head_changed`` — true when it
      moved since ``prior_head``; ``max_total`` — the largest check count seen for
      this head (persisted across runs); ``settling`` — true while a just-pushed
      commit's checks are still registering (the false-settle guard; forces
      ``done`` false). See :func:`decide_done`.
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
    - ``done`` — :func:`decide_done`: all checks green AND no fresh comments AND
      not ``settling``.
    """
    checks = summarize_checks(view.get("statusCheckRollup") or [])
    comments = collect_comments(view, inline)
    fresh = new_actionable(comments, seen)

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
    max_total = checks["total"] if head_changed else max(prior_max_total, checks["total"])
    settling = head_changed or checks["total"] < max_total

    return {
        "pr": view.get("number"),
        "url": view.get("url"),
        "is_draft": view.get("isDraft"),
        "merge_state": view.get("mergeStateStatus"),
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
                # Full body too: handling a finding no longer needs a second
                # `gh api .../pulls/N/comments` fetch for the suggested diff.
                "body": c["body"],
            }
            for c in fresh
        ],
        "all_comment_keys": [c["key"] for c in comments],
        # Persistence set for --mark-seen: BOTH id and content keys, so a later
        # re-post under a new id is matched on content and stays handled.
        "all_seen_keys": sorted({k for c in comments for k in (c["key"], c["content_key"])}),
        "done": decide_done(checks, fresh, settling=settling),
    }


def render(report: dict) -> str:
    ck = report["checks"]
    lines = [f"PR #{report['pr']} — {report['url']}"]
    state = "✅ DONE — green + clean" if report["done"] else "⏳ not done"
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
    if report["new_comments"]:
        lines.append(f"new comments to address ({len(report['new_comments'])}):")
        for c in report["new_comments"]:
            loc = f" {c['path']}:{c['line']}" if c["path"] else ""
            lines.append(f"  • [{c['kind']}] @{c['author']}{loc}: {c['excerpt']}")
    return "\n".join(lines)


def render_mark_seen(report: dict) -> str:
    pr = report.get("pr")
    keys = report.get("marked_seen_keys") or []
    if keys:
        return f"PR #{pr} — acked {len(keys)} comment key(s) from the last reported poll"
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
    save_state(pr, new_state)
    return new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", nargs="?", type=int, default=None, help="PR number (default: current branch's PR)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
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
                "number,title,url,isDraft,mergeStateStatus,headRefOid,statusCheckRollup,reviews,comments",
            ]
        )
        inline = _gh_json(["api", f"repos/{{owner}}/{{repo}}/pulls/{pr}/comments", "--paginate"])
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    state = load_state(pr)
    seen = set(state.get("seen", []))
    report = build_report(
        view, inline, seen, prior_head=state.get("head"), prior_max_total=int(state.get("max_total") or 0)
    )

    persist_poll(pr, report, seen)

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
