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
        "guideline_citation": guideline_citation(body, citation_paths),
        "text": text,
        "text_truncated": truncated,
        "url": comment.get("url"),
    }


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
    return findings


def _rank_key(entry: dict[str, Any]) -> tuple[int, int, int, int]:
    return (-RANK[entry["max_severity"]], -entry["unaddressed_count"], -entry["finding_count"], entry["number"])


def derived(count: int, settings: Settings) -> dict[str, Any]:
    return {
        "findings_pr_count": count,
        "single_pass_recommended": count <= settings.single_pass_max_prs,
        "n_batches": math.ceil(count / settings.batch_size) if count else 0,
    }


def build(raw: dict[str, Any], settings: Settings, citation_paths: list[str]) -> dict[str, Any]:
    run_id = raw["run_identity"]
    candidates = []
    for pr in raw.get("prs") or []:
        findings = pr_findings(pr, settings, citation_paths)
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
        "prs": kept,
    }


# What --verify recomputes. Finding text is excluded on purpose: an agent-built
# digest may clean text differently, but it may not choose different evidence.
VERIFIED_FIELDS = (
    "run_identity_digest", "window", "forge_repo", "protected_branch_head", "config_fingerprint",
    "batching", "input_cap", "findings_pr_count", "single_pass_recommended", "n_batches",
)


def verify(candidate: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    identity.check_header(candidate, kind=identity.DIGEST_KIND, path=path)
    problems = [name for name in VERIFIED_FIELDS if candidate.get(name) != expected.get(name)]
    prs = candidate.get("prs")
    numbers = [p.get("number") for p in prs] if isinstance(prs, list) and all(isinstance(p, dict) for p in prs) else None
    if numbers != [p["number"] for p in expected["prs"]]:
        problems.append("prs[] (ordered capped identities)")
    if problems:
        raise SystemizeError(f"{path}: digest disagrees with its raw bundle on: {', '.join(problems)}")
