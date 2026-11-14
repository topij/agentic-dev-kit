"""The one merge predicate over a parsed ``pr_watch.py --json`` report.

Three callers decide whether a pull request may merge, or is finished and only
waiting for the operator, from the same report:

- ``dev_session.sh merge`` (a ``self`` lane merging its own pull request),
- ``reconcile_sessions.sh``'s ``_held_check`` (is this lane ``held``?),
- ``lib/triage/model.py``'s ``terminal_pr_watch_receipt``.

Each used to spell the field reads itself, and each had a check the others
lacked. This module holds the reads once. It requires everything any one of the
three required, so no caller got looser by moving here.

Stdlib only: the shell engines run this file with a bare ``python3`` from hooks
and scheduled jobs, where nothing else is installed.

Every read fails closed. An absent key, a wrong type or an unexpected value
reads as "not ready" or "not standard"; no read has a permissive default. The
verdict flags are read, never re-derived: ``pr_watch.py`` computes
``mergeable``, and a second derivation here could drift from the engine's.

The shell callers run this file as a command (see ``main``) and act on one
exact token or an exit code. They compare nothing in the report themselves.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# Readiness verdicts, in the order `readiness` checks them.
READY = "ready"
MALFORMED = "malformed"
NOT_MERGEABLE = "not-mergeable"
WRONG_PR = "wrong-pr"
WRONG_URL = "wrong-url"
WRONG_BASE = "wrong-base"
NO_HEAD = "no-head"
HEAD_CHANGED = "head-changed"

# Review-class verdicts.
CLASS_STANDARD = "standard"
CLASS_MISSING = "missing"
CLASS_UNCLASSIFIED = "unclassified"
CLASS_NOT_STANDARD = "not-standard"

# The keys `pr_watch.pr_review_class` always emits. A `review_class` lacking
# one of them was not written by that function, so it is read as missing
# rather than judged on the keys it happens to carry (#1371).
REVIEW_CLASS_KEYS = ("class", "matched_paths", "changes_config", "unclassified")

HELD = "held"
NOT_HELD = "not-held"
UNKNOWN = "unknown"

CONFIG_CHANGE = "the config that declares review.safety_critical_paths"


def scrub(value: Any) -> str:
    """`value` as one printable line: each control character becomes a space.

    The shell callers read this module's output with a tab-splitting `read` and
    print the detail in a refusal message, so report text must not carry a tab,
    a newline or a NUL into either. A space replaces the character rather than
    deleting it: deleting would fuse the text around it into a different value.
    Nothing scrubbed is ever compared. Identity is compared on the raw values in
    `readiness`, where `"tr\\tunk"` simply does not equal `"trunk"`."""
    return "".join(" " if ch < "\x20" or ch == "\x7f" else ch for ch in str(value))


def _expected(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def readiness(
    report: Any,
    *,
    head: Any,
    pr: Any = None,
    base: Any = None,
    url: Any = None,
) -> tuple[str, str]:
    """Is `report` a merge-ready verdict for exactly this pull request?

    Returns `(verdict, detail)`. `verdict` is `READY` or the first check that
    failed; `detail` is the reported value for the identity mismatches, scrubbed
    for printing, and empty otherwise.

    The caller names the identity it holds. `head` is always required, and so
    is at least one of `pr` (the number, as a string) and `url`, because a
    report bound to no pull request must never read as ready. `base` is checked
    when given. A given identity that is not a non-empty string is refused, so
    a caller that lost a value cannot match a report that also lacks it.

    What each of the three earlier copies required, and this requires all of:

    - `mergeable is True` (all three);
    - `converged is True` (the reconciler and triage; not the merge wrapper);
    - `done is True` (triage only);
    - `merge_blockers == []` (the reconciler and triage; not the merge wrapper);
    - `truncated_reads == []` (triage only);
    - `review_evidence.valid is True` (triage only);
    - the reported `head` equal to the expected one (all three), and non-empty
      (the merge wrapper only);
    - the reported `pr` and `base` (the merge wrapper and the reconciler);
    - the reported `url` (triage only).

    `MALFORMED` is kept apart from `NOT_MERGEABLE` because the reconciler
    reports a report it could not read differently from one that said no."""
    if not isinstance(report, dict) or not isinstance(report.get("merge_blockers"), list):
        return MALFORMED, ""
    evidence = report.get("review_evidence")
    if not (
        report.get("mergeable") is True
        and report.get("converged") is True
        and report.get("done") is True
        and report["merge_blockers"] == []
        and report.get("truncated_reads") == []
        and isinstance(evidence, dict)
        and evidence.get("valid") is True
    ):
        return NOT_MERGEABLE, ""
    if pr is None and url is None:
        return WRONG_PR, ""
    if pr is not None:
        reported = report.get("pr")
        # A bool is an int in Python and `str(True)` is not a number, but say so
        # here instead of relying on it.
        if not _expected(pr) or isinstance(reported, bool) or str(reported) != pr:
            return WRONG_PR, scrub("" if reported is None else reported)
    if url is not None:
        reported = report.get("url")
        if not _expected(url) or reported != url:
            return WRONG_URL, scrub("" if reported is None else reported)
    if base is not None:
        reported = report.get("base")
        if not _expected(base) or reported != base:
            return WRONG_BASE, scrub("" if reported is None else reported)
    reported = report.get("head")
    if not isinstance(reported, str) or reported == "":
        return NO_HEAD, ""
    if not _expected(head) or reported != head:
        return HEAD_CHANGED, scrub(reported)
    return READY, ""


def review_class(report: Any) -> tuple[str, str]:
    """The report's review class as one exact token, with a printable reason.

    Only a report that says `standard`, with nothing unclassified, no matched
    path and no config change, reads as `CLASS_STANDARD` (#1357). Everything
    else is one of three refusals, and they differ in what the reader does next:

    - `CLASS_MISSING`: no `review_class` object, or one lacking a key
      `pr_watch` always writes (`{"class": "standard"}` alone is not a class).
      An older or foreign `pr_watch`; the remedy is an upgrade.
    - `CLASS_UNCLASSIFIED`: `unclassified` holds anything but `None`, a falsy
      reason included. Most often a base or head commit the clone lacks.
    - `CLASS_NOT_STANDARD`: the pull request is operator-merge. This includes a
      class string other than exactly `standard`, and a `standard` that is
      inconsistent with its own fields: a `matched_paths` that is not an empty
      list (a non-list of any value counts, and is printed as given), or a
      `changes_config` that is anything other than `False`.

    The reason is scrubbed and only ever printed."""
    rc = report.get("review_class") if isinstance(report, dict) else None
    if not isinstance(rc, dict):
        return CLASS_MISSING, "the pr-watch report has no review_class"
    absent = [key for key in REVIEW_CLASS_KEYS if key not in rc]
    if absent:
        return CLASS_MISSING, scrub(
            "the pr-watch report has no review_class that names " + ", ".join(absent)
        )
    if rc["unclassified"] is not None:
        return CLASS_UNCLASSIFIED, scrub(rc["unclassified"])
    raw = rc["matched_paths"]
    matched = [str(item) for item in raw] if isinstance(raw, list) else [str(raw)]
    paths_clear = isinstance(raw, list) and not raw
    if rc["changes_config"] is not False:
        matched.append(CONFIG_CHANGE)
    if rc["class"] == "standard" and paths_clear and rc["changes_config"] is False:
        return CLASS_STANDARD, ""
    why = "class " + str(rc["class"])
    if matched:
        why += "; matched: " + ", ".join(matched)
    return CLASS_NOT_STANDARD, scrub(why)


def merge_gate(report: Any, *, pr: Any, base: Any, head: Any) -> tuple[str, str]:
    """May a `self` lane merge this pull request itself?

    `(READY, "")` only when the report is merge-ready for exactly this pull
    request, base and head and is classed standard. Otherwise the first failing
    readiness verdict, or `class-<review class verdict>` with its reason."""
    if not (_expected(pr) and _expected(base)):
        return WRONG_PR if not _expected(pr) else WRONG_BASE, ""
    verdict, detail = readiness(report, pr=pr, base=base, head=head)
    if verdict != READY:
        return verdict, detail
    klass, why = review_class(report)
    if klass != CLASS_STANDARD:
        return "class-" + klass, why
    return READY, ""


def held(report: Any, *, merge_class: Any, pr: Any, base: Any, head: Any) -> str:
    """Is this lane finished, with only the operator's merge left?

    `HELD` when the report is merge-ready for exactly this pull request and
    either the lane's persisted merge class is `operator`, or it is `self` and
    the review class is `CLASS_NOT_STANDARD`: the one verdict on which
    `merge_gate` tells the lane the operator lands it (#1370).

    `held` is a terminal claim, so the safe direction here is the opposite of
    the merge gate's: anything unclear must NOT widen it. Each input that could
    reach the `self` branch, and what it gets:

    - merge class neither `operator` nor `self` (absent, empty, misspelt):
      `NOT_HELD`. Unknown lane metadata never claims a terminal state.
    - a report that is not merge-ready: `NOT_HELD`, whatever its class.
    - a report that could not be read (`MALFORMED`): `UNKNOWN`.
    - `self`, ready, `CLASS_STANDARD`: `NOT_HELD`. The lane merges itself.
    - `self`, ready, `CLASS_MISSING` or `CLASS_UNCLASSIFIED`: `UNKNOWN`. The
      wrapper refuses this merge too, but its remedy is an upgrade or a fetch,
      not an operator merge, so the lane is not finished. The caller reports it
      `open` and says it could not be evaluated."""
    if merge_class not in ("operator", "self"):
        return NOT_HELD
    if not (_expected(pr) and _expected(base)):
        return NOT_HELD
    verdict, _detail = readiness(report, pr=pr, base=base, head=head)
    if verdict == MALFORMED:
        return UNKNOWN
    if verdict != READY:
        return NOT_HELD
    if merge_class == "operator":
        return HELD
    klass, _why = review_class(report)
    if klass == CLASS_NOT_STANDARD:
        return HELD
    if klass == CLASS_STANDARD:
        return NOT_HELD
    return UNKNOWN


def _load(stream: Any) -> Any:
    try:
        return json.load(stream)
    except (ValueError, RecursionError):
        # Not a dict, so every predicate reads it as malformed.
        return None


def main(argv: list[str] | None = None) -> int:
    """The shell callers' interface. The report is read from stdin.

    `merge --pr P --base B --head H` prints `<verdict><TAB><detail>` and exits
    0 only for `ready`. `dev_session.sh merge` requires both.

    `held --merge-class C --pr P --base B --head H` prints `held`, `not-held`
    or `unknown` and exits 0, 1 or 2 to match. `_held_check` reads the printed
    answer, and takes `held` only with exit 0.

    A run that fails (a usage error, an exception, this file missing or not
    parsing) prints no verdict, and a bare Python traceback exits 1. That is why
    both callers act on the printed token and treat anything else as "refuse"
    and "could not tell": an exit status of 1 alone would read as a clean "not
    held"."""
    parser = argparse.ArgumentParser(prog="merge_predicate.py")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("merge", "held"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--pr", required=True)
        cmd.add_argument("--base", required=True)
        cmd.add_argument("--head", required=True)
        if name == "held":
            cmd.add_argument("--merge-class", required=True)
    args = parser.parse_args(argv)
    try:
        report = _load(sys.stdin)
        if args.command == "merge":
            verdict, detail = merge_gate(report, pr=args.pr, base=args.base, head=args.head)
            print(verdict + "\t" + detail)
            return 0 if verdict == READY else 1
        answer = held(
            report, merge_class=args.merge_class, pr=args.pr, base=args.base, head=args.head
        )
        print(answer)
        return {HELD: 0, NOT_HELD: 1}.get(answer, 2)
    except Exception:
        # Whatever failed, no verdict was printed, and the status is neither 0
        # nor 1.
        return 2


if __name__ == "__main__":
    sys.exit(main())
