"""Raw bundle → capped, ranked review-finding digest, and its independent check.

Every rule here is the shared workflow's Step 1 made executable: the trusted
source set, the canonical severity table, the ranking and cap, and the derived
batching fields. ``verify`` recomputes the evidence selection from the raw bundle
so a digest — engine-built or agent-built — cannot select its own working set.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from . import identity
from .config import CANONICAL_SEVERITIES, Settings, normalize_login
from .errors import SystemizeError

SEVERITY_TABLE = {
    **dict.fromkeys(("low", "minor", "info", "informational"), "low"),
    **dict.fromkeys(("medium", "moderate", "normal", "warning"), "normal"),
    **dict.fromkeys(("high", "major"), "high"),
    **dict.fromkeys(("critical", "blocker"), "critical"),
}
RANK = {name: index for index, name in enumerate(CANONICAL_SEVERITIES)}

# Where a source states its own severity. Only the label text is extracted; the
# table above is the only mapping, so an emoji or a custom scale never gets one.
_LABEL_PATTERNS = (
    re.compile(r"[\U0001F534\U0001F7E0\U0001F7E1\U0001F7E2\U0001F535⚪]\s*[_*]*\s*([A-Za-z]+)"),
    re.compile(r"\*\*\s*([A-Za-z]+)\s+Severity\s*\*\*", re.IGNORECASE),
    re.compile(r"(?im)^[\s>*_-]*severity[\s*_]*[:：][\s*_]*([A-Za-z0-9_-]+)"),
    re.compile(r"!\[(P\d)\s+Badge\]"),
)
_GUIDELINE_MARKERS = re.compile(r"as per coding guidelines|based on learnings", re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# Collapsible markup is dropped but its content kept: reviewers put real
# findings (nitpicks, outside-diff comments) inside <details> blocks.
_MARKUP = re.compile(r"</?(?:details|summary|blockquote)\b[^>]*>", re.IGNORECASE)
TEXT_LIMIT = 4000


def source_label(body: str) -> str | None:
    best: tuple[int, str] | None = None
    for pattern in _LABEL_PATTERNS:
        match = pattern.search(body)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), match.group(1))
    return best[1] if best else None


def normalize_severity(label: str | None) -> tuple[str, bool]:
    """Return ``(normalized, mapped)``; ``mapped`` is false for an unmapped label."""
    if label is None:
        return "normal", True
    key = label.strip().lower()
    if key in SEVERITY_TABLE:
        return SEVERITY_TABLE[key], True
    return "normal", False


def clean_text(body: str) -> tuple[str, bool]:
    text = _MARKUP.sub("", _HTML_COMMENT.sub("", body))
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(line.rstrip() for line in text.splitlines())).strip()
    if len(text) > TEXT_LIMIT:
        return text[:TEXT_LIMIT], True
    return text, False


def instruction_paths(root: Path) -> list[str]:
    """The active instruction and shared-workflow set a finding may cite."""
    found = [name for name in ("AGENTS.md", "CLAUDE.md") if (root / name).is_file()]
    for base in ("docs/agentic-dev-kit", ".claude/rules"):
        directory = root / base
        if directory.is_dir():
            found += sorted(str(p.relative_to(root)) for p in directory.rglob("*.md") if p.is_file())
    return sorted(set(found))


def guideline_citation(body: str, paths: list[str]) -> dict[str, Any]:
    evidence = [p for p in paths if p in body]
    evidence += sorted({m.group(0).lower() for m in _GUIDELINE_MARKERS.finditer(body)})
    return {"state": "cited" if evidence else "none", "evidence": evidence}


def _source(login: str | None, settings: Settings) -> dict[str, str] | None:
    if not isinstance(login, str):
        return None
    normalized = normalize_login(login)
    if normalized in settings.operator_logins:
        return {"kind": "operator", "login": login}
    if normalized in settings.reviewer_logins:
        return {"kind": "configured-reviewer", "login": login}
    return None


def thread_addressed(thread: dict[str, Any]) -> str:
    """Forge thread resolution is the evidence; reply text is not (#748)."""
    if thread.get("is_resolved") is True:
        return "addressed"
    if thread.get("is_outdated") is True:
        return "outdated"
    return "unaddressed"


def _finding(kind: str, comment: dict[str, Any], source: dict[str, str], *, path: Any, line: Any,
             addressed: str, citation_paths: list[str]) -> dict[str, Any]:
    body = comment.get("body") or ""
    label = source_label(body)
    severity, mapped = normalize_severity(label)
    text, truncated = clean_text(body)
    return {
        "id": f"{kind}:{comment.get('id')}",
        "source": source,
        "path": path,
        "line": line,
        "source_severity": label,
        "severity": severity,
        "severity_mapped": mapped,
        "addressed": addressed,
        "stance": None,
        "reviewed_head": None,
        "guideline_citation": guideline_citation(body, citation_paths),
        "text": text,
        "text_truncated": truncated,
        "url": comment.get("url"),
    }


# The fallback panel reaches a pull request only as the comment
# `pr_watch.py --record-review --disposition` posts (#772). Its first lines are
# fixed by that engine; the rest is the cockpit's prose, in which each finding is
# one typed line (fallback-review-panel.md *Typed dispositions*). Only that line
# grammar is read, only after the engine's header, and only from a trusted
# author: neither the marker nor the prose makes a comment evidence by itself.
_DISPOSITION_HEADER = re.compile(
    r"<!-- pr-watch:disposition head=(?P<head>[0-9a-f]{7,40}) -->\n"
    r"## Review disposition — [^\n]*\n"
    r"\n"
    r"- reviewed head: `(?P<reviewed>[0-9a-f]{7,40})`\n"
    r"- review source: `(?P<source>[^`\n]*)`\n"
    r"- lenses: (?P<lenses>[^\n]*)\n"
)
_DISPOSITION_LINE = re.compile(
    r"^[ \t]*(?:[-*][ \t]+)?`?(?P<lens>[A-Za-z0-9_.-]+) F(?P<n>[1-9][0-9]*)"
    r"(?: (?P<severity>[A-Za-z]+))?: (?P<stance>accept|dispute-evidence|dispute-concern)"
    r"(?=[ :—`]|$)[^\n]*$",
    re.MULTILINE,
)
STANCES = ("accept", "dispute-evidence", "dispute-concern")


def disposition_header(body: str) -> dict[str, Any] | None:
    """The engine-written header of a disposition comment, or ``None``."""
    match = _DISPOSITION_HEADER.match(body.replace("\r\n", "\n"))
    if match is None or match.group("head") != match.group("reviewed"):
        return None
    lenses = [name.strip() for name in match.group("lenses").split(",") if name.strip()]
    return {
        "head": match.group("head"),
        "review_source": match.group("source"),
        "lenses": lenses,
        "prose": body.replace("\r\n", "\n")[match.end():],
    }


def stance_addressed(stance: str, severity: str) -> str:
    """A typed disposition is the panel's addressed-state evidence (#772, #748).

    Every stance answers the finding on the pull request, except that a HIGH or
    CRITICAL finding is never closed by ``dispute-concern``
    (fallback-review-panel.md *Typed dispositions*), so that one stays unaddressed.
    """
    if stance == "dispute-concern" and RANK[severity] >= RANK["high"]:
        return "unaddressed"
    return "addressed"


def disposition_findings(comment: dict[str, Any], source: dict[str, str],
                         citation_paths: list[str]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """``(header, findings)`` for one trusted comment; ``(None, [])`` if it is not one.

    A line inside a blockquote is a quotation, not this round's disposition, and
    a line naming a lens the header does not list is not this round's finding.
    A repeated ``<lens> F<n>`` in one comment counts once, first line first.
    """
    header = disposition_header(comment.get("body") or "")
    if header is None:
        return None, []
    findings: dict[tuple[str, str], dict[str, Any]] = {}
    for match in _DISPOSITION_LINE.finditer(header["prose"]):
        lens, number = match.group("lens"), match.group("n")
        if lens not in header["lenses"] or (lens, number) in findings:
            continue
        label = match.group("severity")
        severity, mapped = normalize_severity(label)
        line = match.group(0)
        text, truncated = clean_text(line)
        findings[(lens, number)] = {
            "id": f"disposition:{comment.get('id')}:{lens}:F{number}",
            "source": {**source, "lens": lens, "review_source": header["review_source"]},
            "path": None,
            "line": None,
            "source_severity": label,
            "severity": severity,
            "severity_mapped": mapped,
            "addressed": stance_addressed(match.group("stance"), severity),
            "stance": match.group("stance"),
            "reviewed_head": header["head"],
            "guideline_citation": guideline_citation(line, citation_paths),
            "text": text,
            "text_truncated": truncated,
            "url": comment.get("url"),
        }
    return header, list(findings.values())


def pr_findings(pr: dict[str, Any], settings: Settings, citation_paths: list[str]) -> list[dict[str, Any]]:
    findings = []
    for thread in pr.get("review_threads") or []:
        comments = thread.get("comments") or []
        if not comments:
            continue
        root = comments[0]
        source = _source(root.get("author"), settings)
        if source is not None:
            findings.append(_finding(
                "thread", root, source, path=thread.get("path"), line=thread.get("line"),
                addressed=thread_addressed(thread), citation_paths=citation_paths,
            ))
    for review in pr.get("reviews") or []:
        source = _source(review.get("author"), settings)
        if source is not None and (review.get("body") or "").strip():
            findings.append(_finding(
                "review", review, source, path=None, line=None,
                addressed="unevidenced", citation_paths=citation_paths,
            ))
    findings.extend(panel_findings(pr, settings, citation_paths)[1])
    return findings


def panel_findings(pr: dict[str, Any], settings: Settings,
                   citation_paths: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
    """``(reviewed heads, findings)`` from the PR's trusted disposition comments.

    The heads are distinct and in comment order: one per recorded round. A later
    comment at the same head replaces an earlier one's findings for the same
    ``<lens> F<n>``, because a correction is posted after what it corrects.
    """
    heads: list[str] = []
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for comment in pr.get("issue_comments") or []:
        source = _source(comment.get("author"), settings)
        if source is None:
            continue
        header, findings = disposition_findings(comment, source, citation_paths)
        if header is None:
            continue
        if header["head"] not in heads:
            heads.append(header["head"])
        for finding in findings:
            key = (header["head"], finding["id"].split(":", 2)[2])
            found.pop(key, None)
            found[key] = finding
    return heads, list(found.values())


def _rank_key(entry: dict[str, Any]) -> tuple[int, int, int, int]:
    return (-RANK[entry["max_severity"]], -entry["unaddressed_count"], -entry["finding_count"], entry["number"])


def derived(count: int, settings: Settings) -> dict[str, Any]:
    return {
        "findings_pr_count": count,
        "single_pass_recommended": count <= settings.single_pass_max_prs,
        "n_batches": math.ceil(count / settings.batch_size) if count else 0,
    }


ADDRESSED_STATES = ("addressed", "outdated", "unaddressed", "unevidenced")


def _tally_key(finding: dict[str, Any]) -> str:
    source = finding["source"]
    if "lens" in source:
        return f"lens:{source['lens']}"
    return f"{source['kind']}:{normalize_login(source['login'])}"


def reviewer_tally(findings: list[dict[str, Any]], rounds: list[dict[str, int]],
                   settings: Settings) -> dict[str, Any]:
    """Per-source precision and per-PR rounds over the whole window (#1157).

    A lens finding carries a typed stance; a thread or review finding carries
    only its addressed state, so its ``by_stance`` and ``refuted`` are null.
    ``refuted`` counts ``dispute-evidence``: the author showed the finding wrong.
    The flag is a report line and nothing more; no gate reads it.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        grouped.setdefault(_tally_key(finding), []).append(finding)
    sources = []
    for key in sorted(grouped):
        group = grouped[key]
        typed = key.startswith("lens:")
        by_stance = {s: sum(1 for f in group if f["stance"] == s) for s in STANCES} if typed else None
        refuted = by_stance["dispute-evidence"] if by_stance is not None else None
        sources.append({
            "source": key,
            "findings": len(group),
            "by_addressed": {state: sum(1 for f in group if f["addressed"] == state) for state in ADDRESSED_STATES},
            "by_stance": by_stance,
            "refuted": refuted,
            "refuted_flag": refuted is not None
            and len(group) >= settings.refuted_flag_min_findings
            and refuted * 100 >= settings.refuted_flag_percent * len(group),
        })
    return {
        "refuted_flag_min_findings": settings.refuted_flag_min_findings,
        "refuted_flag_percent": settings.refuted_flag_percent,
        "sources": sources,
        "rounds": rounds,
    }


def build(raw: dict[str, Any], settings: Settings, citation_paths: list[str]) -> dict[str, Any]:
    run_id = raw["run_identity"]
    candidates = []
    every_finding: list[dict[str, Any]] = []
    rounds: list[dict[str, int]] = []
    for pr in raw.get("prs") or []:
        heads, _ = panel_findings(pr, settings, citation_paths)
        if heads:
            rounds.append({"pr": pr["number"], "rounds": len(heads)})
        findings = pr_findings(pr, settings, citation_paths)
        every_finding.extend(findings)
        if not findings:
            continue
        candidates.append({
            "number": pr["number"],
            "title": pr.get("title"),
            "url": pr.get("url"),
            "tracker_refs": pr.get("tracker_refs") or [],
            "max_severity": max((f["severity"] for f in findings), key=RANK.__getitem__),
            "unaddressed_count": sum(1 for f in findings if f["addressed"] != "addressed"),
            "finding_count": len(findings),
            "findings": findings,
        })
    candidates.sort(key=_rank_key)
    kept = candidates[: settings.max_findings_prs_per_run]
    omitted = [c["number"] for c in candidates[settings.max_findings_prs_per_run:]]
    limitations = [
        {"pr": c["number"], "finding": f["id"], "source_severity": f["source_severity"]}
        for c in kept for f in c["findings"] if not f["severity_mapped"]
    ]
    window = raw.get("window") or {}
    return {
        **identity.header(identity.DIGEST_KIND, run_id),
        "window": f"{run_id['window_days']}d",
        "window_start": window.get("start"),
        "window_end": window.get("end"),
        "forge_repo": run_id["forge_repo"],
        "protected_branch_head": run_id["protected_branch_head"],
        "config_fingerprint": run_id["config_fingerprint"],
        "batching": {
            "batch_size": settings.batch_size,
            "single_pass_max_prs": settings.single_pass_max_prs,
            "max_findings_prs_per_run": settings.max_findings_prs_per_run,
        },
        "input_cap": {
            "applied": bool(omitted),
            "uncapped_findings_pr_count": len(candidates),
            "omitted_prs": omitted,
        },
        **derived(len(kept), settings),
        "severity_limitations": limitations,
        "reviewer_tally": reviewer_tally(every_finding, sorted(rounds, key=lambda r: r["pr"]), settings),
        "prs": kept,
    }


# What --verify recomputes. Finding text is excluded on purpose: an agent-built
# digest may clean text differently, but it may not choose different evidence.
VERIFIED_FIELDS = (
    "run_identity_digest", "window", "forge_repo", "protected_branch_head", "config_fingerprint",
    "batching", "input_cap", "findings_pr_count", "single_pass_recommended", "n_batches",
    "window_start", "window_end", "severity_limitations", "reviewer_tally",
)


def _evidence(prs: Any) -> Any:
    if not isinstance(prs, list):
        return None
    evidence = []
    for pr in prs:
        if not isinstance(pr, dict) or not isinstance(pr.get("findings"), list):
            return None
        findings = []
        for finding in pr["findings"]:
            if not isinstance(finding, dict) or not isinstance(finding.get("text"), str):
                return None
            if not isinstance(finding.get("text_truncated"), bool):
                return None
            # Text cleaning may differ, but every evidence field remains exact.
            findings.append({k: v for k, v in finding.items() if k not in ("text", "text_truncated")})
        evidence.append({**pr, "findings": findings})
    return evidence


def _same(actual: Any, expected: Any) -> bool:
    # Python considers True equal to 1; evidence and counts retain JSON types.
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(_same(a, e) for a, e in zip(actual, expected, strict=True))
    return actual == expected


def verify(candidate: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    identity.check_header(candidate, kind=identity.DIGEST_KIND, path=path)
    problems = [name for name in VERIFIED_FIELDS if name not in candidate or not _same(candidate[name], expected.get(name))]
    prs = candidate.get("prs")
    if not _same(_evidence(prs), _evidence(expected["prs"])):
        problems.append("prs[] (ordered capped finding evidence)")
    if problems:
        raise SystemizeError(f"{path}: digest disagrees with its raw bundle on: {', '.join(problems)}")
